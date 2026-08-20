"""
bosses/level36.py - Semua boss Level 36

Berisi:
  - nyxallaria  (mini boss - RANGED abyssal sovereign, moonlit magic)
  - vhaerinth   (mini boss - RANGED inkweaver, ink magic)
  - xharokh     (mini boss - RANGED voidbinder, void staff)
  - kaerinya    (TRUE BOSS - MELEE sunfist, fiery golden fists)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _vha_ (vhaerinth), _xhr_ (xharokh) sudah unik.
  - _nyx_ (nyxallaria) di-rename -> _nxl_ (bentrok dengan nyxarath
    level 7 & nyxareva level 11), termasuk atribut _last_x/_last_y.
  - _kae_ (kaerinya) di-rename -> _kry_ (bentrok dengan level13 &
    kaervosth level 26), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# NYXALLARIA (ABYSSAL SOVEREIGN) - Mini Boss
# ====================================================================

class _NS_nyxallaria:
    """Namespace nyxallaria - Ocean Goddess boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Deep ocean blues (dress, main body)
        "ocean_darkest": (2, 8, 20),
        "ocean_dark": (8, 25, 55),
        "ocean_mid": (20, 60, 110),
        "ocean_light": (45, 110, 175),
        "ocean_bright": (90, 170, 220),
        "ocean_shine": (170, 230, 250),
        # Cyan/aqua water magic
        "aqua_darkest": (5, 30, 40),
        "aqua_dark": (15, 70, 95),
        "aqua_mid": (40, 150, 190),
        "aqua_light": (100, 220, 250),
        "aqua_hot": (180, 245, 255),
        "aqua_shine": (230, 255, 255),
        # Skin (goddess pale)
        "skin_shadow": (95, 70, 80),
        "skin_dark": (165, 130, 130),
        "skin_mid": (220, 185, 175),
        "skin_light": (245, 220, 210),
        "skin_shine": (255, 245, 235),
        # Hair (raven black-blue)
        "hair_darkest": (5, 5, 15),
        "hair_dark": (20, 20, 40),
        "hair_mid": (45, 45, 75),
        "hair_light": (80, 85, 120),
        "hair_shine": (140, 150, 190),
        # Gold armor/crown/trident
        "gold_dark": (85, 60, 15),
        "gold_mid": (180, 140, 45),
        "gold_light": (240, 205, 100),
        "gold_shine": (255, 240, 180),
        # Purple accents (dress sash, magical accents)
        "purple_dark": (35, 15, 60),
        "purple_mid": (85, 40, 130),
        "purple_light": (160, 100, 210),
        # Eye (glowing blue)
        "eye_socket": (10, 15, 25),
        "eye_dark": (20, 60, 100),
        "eye_mid": (60, 160, 220),
        "eye_light": (170, 230, 250),
        "eye_glow": (230, 250, 255),
        # Moonlight/ethereal
        "moon_dark": (60, 70, 100),
        "moon_mid": (180, 200, 230),
        "moon_light": (240, 245, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxallaria._clamp(color)
        if _NS_nyxallaria.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxallaria._clamp(color)
        if _NS_nyxallaria.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxallaria._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyxallaria(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxallaria._detect_moving(boss)
        _NS_nyxallaria._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nxl_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (large moonlit aura)
        _NS_nyxallaria._draw_moonlit_aura(surface, x, y, pulse)
        _NS_nyxallaria._draw_ground_ripples(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_nyxallaria._draw_spectral_tide_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxallaria._draw_maelstrom_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxallaria._draw_leviathan_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_nyxallaria._draw_nxl_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxallaria._draw_nxl_float_move(surface, boss, x, y)
        else:
            _NS_nyxallaria._draw_nxl_idle(surface, boss, x, y)
        # Spectral form overlay during W
        if active_skill == "w":
            _NS_nyxallaria._draw_spectral_overlay(surface, boss, x, y, skill_timer, pulse)
        # Foreground skill FX
        if active_skill == "q":
            _NS_nyxallaria._draw_abyssal_lance(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxallaria._draw_maelstrom_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxallaria._draw_leviathan_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nxl_previous_timer", 0))
        active = bool(getattr(boss, "_nxl_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nxl_attack_active = True
            boss._nxl_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nxl_attack_frame = int(getattr(boss, "_nxl_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nxl_attack_active = False
            boss._nxl_attack_frame = 0
            active = False
        boss._nxl_previous_timer = timer
        boss._nxl_attack_progress = (
            min(1.0, getattr(boss, "_nxl_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nxl_last_x"):
            boss._nxl_last_x = boss.x
            boss._nxl_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nxl_last_x)
        dy = abs(boss.y - boss._nxl_last_y)
        boss._nxl_last_x = boss.x
        boss._nxl_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_nxl_idle(surface, boss, x, y):
        # Slow floating bob
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_nyxallaria._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_nyxallaria._draw_water_swirls(surface, x, y + 40, boss.pulse)
        _NS_nyxallaria._draw_nxl_body(surface, x, y + bob,
                                       boss.direction, boss.pulse, "idle")
    def _draw_nxl_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_nyxallaria._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_nyxallaria._draw_water_swirls(surface, x + sway, y + 40, phase,
                                          trail=True, facing=boss.direction)
        _NS_nyxallaria._draw_nxl_body(surface, x + sway, y + bob,
                                       boss.direction, phase, "float")
    def _draw_nxl_attack(surface, boss, x, y):
        progress = getattr(boss, "_nxl_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Swing animation for melee-ish trident thrust
        if progress < 0.35:
            # Wind up (pull back)
            t = progress / 0.35
            thrust = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            # Forward thrust
            t = (progress - 0.35) / 0.25
            thrust = int((-5 + t * 16)) * boss.direction
            lift = int(4 - t * 6)
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            thrust = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_nyxallaria._draw_float_shadow(surface, x + thrust, y + 52, boss.pulse)
        _NS_nyxallaria._draw_water_swirls(surface, x + thrust, y + 40, boss.pulse,
                                          intense=True)
        _NS_nyxallaria._draw_nxl_body(surface, x + thrust, y - lift + bob,
                                       boss.direction, boss.pulse, "attack", progress)
        _NS_nyxallaria._draw_water_projectile(surface, boss, x + thrust,
                                              y - lift + bob, progress)
    # ============================================================
    # BODY - Goddess figure (crown, hair, dress, trident)
    # ============================================================
    def _draw_nxl_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw goddess: dress (bottom), torso, arms, head, hair, crown, trident."""
        # Flowing dress bottom (draws first, behind body)
        _NS_nyxallaria._draw_flowing_dress(surface, cx, cy, facing, phase)
        # Flowing hair back
        _NS_nyxallaria._draw_hair_back(surface, cx, cy - 22, facing, phase)
        # Torso/dress upper
        _NS_nyxallaria._draw_torso_armor(surface, cx, cy, facing, phase)
        # Back arm (holds trident)
        trident_thrust = 0
        if action == "attack":
            if attack_progress < 0.35:
                trident_thrust = -int(attack_progress / 0.35 * 4) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                trident_thrust = int((-4 + t * 14)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                trident_thrust = int(10 * (1 - t)) * facing
        # Front arm (extended magic hand)
        _NS_nyxallaria._draw_front_arm(surface, cx, cy - 4, facing, phase, action,
                                        attack_progress)
        # Head + face
        _NS_nyxallaria._draw_goddess_head(surface, cx, cy - 26, facing, phase)
        # Hair front (partial)
        _NS_nyxallaria._draw_hair_front(surface, cx, cy - 24, facing, phase)
        # Crown
        _NS_nyxallaria._draw_crown(surface, cx, cy - 34, facing, phase)
        # Trident (main weapon)
        _NS_nyxallaria._draw_trident(surface, cx - facing * 8 + trident_thrust,
                                      cy - 8, facing, phase, action, attack_progress)
    def _draw_flowing_dress(surface, cx, cy, facing, phase):
        """Long flowing dress from waist down, ethereal waves."""
        # Base dress silhouette (goes wider at bottom)
        wave1 = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 0.8 + 1) * 3
        # Main dress
        dress_pts = [
            (cx - 10, cy + 2),
            (cx + 10, cy + 2),
            (cx + 14, cy + 12),
            (cx + 18 + int(wave1), cy + 24),
            (cx + 22 + int(wave2), cy + 38),
            (cx + 16, cy + 48),
            (cx + 8, cy + 52),
            (cx - 8, cy + 52),
            (cx - 16, cy + 48),
            (cx - 22 + int(wave1), cy + 38),
            (cx - 18 + int(wave2), cy + 24),
            (cx - 14, cy + 12),
        ]
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in dress_pts])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_darkest"], dress_pts)
        # Dress midtone layer
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_dark"], [
            (cx - 9, cy + 4),
            (cx + 9, cy + 4),
            (cx + 12, cy + 14),
            (cx + 16 + int(wave1 * 0.7), cy + 26),
            (cx + 18 + int(wave2 * 0.7), cy + 38),
            (cx + 12, cy + 46),
            (cx - 12, cy + 46),
            (cx - 18 + int(wave1 * 0.7), cy + 38),
            (cx - 16 + int(wave2 * 0.7), cy + 26),
            (cx - 12, cy + 14),
        ])
        # Mid highlight
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_mid"], [
            (cx - 7, cy + 6),
            (cx + 7, cy + 6),
            (cx + 10, cy + 18),
            (cx + 12, cy + 32),
            (cx + 6, cy + 42),
            (cx - 6, cy + 42),
            (cx - 12, cy + 32),
            (cx - 10, cy + 18),
        ])
        # Light shimmer highlights (sheer fabric look)
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_light"], [
            (cx - 4, cy + 8),
            (cx + 2, cy + 8),
            (cx + 4, cy + 24),
            (cx + 2, cy + 36),
            (cx - 2, cy + 36),
            (cx - 6, cy + 24),
        ])
        # Purple/violet sash at hip (like reference)
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["purple_dark"], [
            (cx - 8, cy + 14),
            (cx + 8, cy + 14),
            (cx + 12, cy + 22),
            (cx + 8, cy + 26),
            (cx - 8, cy + 26),
            (cx - 12, cy + 22),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["purple_mid"], [
            (cx - 6, cy + 16),
            (cx + 6, cy + 16),
            (cx + 9, cy + 22),
            (cx + 6, cy + 24),
            (cx - 6, cy + 24),
            (cx - 9, cy + 22),
        ])
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["purple_light"],
                         (cx - 4, cy + 20), (cx + 4, cy + 20), 1)
        # Water sparkles on dress
        for i in range(6):
            spark_t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 10 + int((i % 3) * 8) + int(math.sin(phase + i) * 2)
            sy = cy + 14 + int(spark_t * 30)
            alpha = _NS_nyxallaria._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"], (sx, sy, 1, 1))
        # Gold trim at bottom
        for i in range(4):
            trim_x = cx - 14 + i * 9
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                             (trim_x, cy + 46, 3, 2))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_light"],
                             (trim_x + 1, cy + 46, 1, 1))
    def _draw_torso_armor(surface, cx, cy, facing, phase):
        """Upper torso with ornate armor/dress top."""
        # Torso base
        torso_pts = [
            (cx - 9, cy - 8),
            (cx + 9, cy - 8),
            (cx + 11, cy - 2),
            (cx + 10, cy + 4),
            (cx - 10, cy + 4),
            (cx - 11, cy - 2),
        ]
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_darkest"], torso_pts)
        # Bodice (dark ocean blue)
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_dark"], [
            (cx - 8, cy - 7),
            (cx + 8, cy - 7),
            (cx + 10, cy - 2),
            (cx + 9, cy + 3),
            (cx - 9, cy + 3),
            (cx - 10, cy - 2),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["ocean_mid"], [
            (cx - 7, cy - 5),
            (cx + 7, cy - 5),
            (cx + 8, cy),
            (cx + 6, cy + 2),
            (cx - 6, cy + 2),
            (cx - 8, cy),
        ])
        # Gold armor plating (shoulder + chest ornaments)
        # Shoulder pauldrons
        for side in (-1, 1):
            _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_dark"], [
                (cx + side * 7, cy - 9),
                (cx + side * 12, cy - 8),
                (cx + side * 13, cy - 4),
                (cx + side * 10, cy - 2),
                (cx + side * 7, cy - 4),
            ])
            _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_mid"], [
                (cx + side * 8, cy - 8),
                (cx + side * 11, cy - 7),
                (cx + side * 12, cy - 4),
                (cx + side * 9, cy - 3),
            ])
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_light"],
                             (cx + side * 10 - 1, cy - 6, 1, 1))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_shine"],
                             (cx + side * 10, cy - 6, 1, 1))
        # Chest gem (blue jewel)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                         (cx - 2, cy - 4, 4, 4))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_dark"],
                         (cx - 1, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_light"],
                         (cx - 1, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                         (cx - 1, cy - 3, 1, 1))
        # Cleavage line + collarbone
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["ocean_darkest"],
                         (cx, cy - 4), (cx, cy + 2), 1)
        # Skin (upper chest, neck)
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["skin_dark"], [
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["skin_mid"], [
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 2, cy - 8),
            (cx - 2, cy - 8),
        ])
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["skin_light"],
                         (cx - 1, cy - 9, 2, 1))
    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm extended, casting magic."""
        wave = math.sin(phase * 0.7) * 1
        # Arm extended forward
        shoulder_x = cx + facing * 8
        shoulder_y = cy - 2
        elbow_x = cx + facing * 14
        elbow_y = cy + 2 + int(wave)
        hand_x = cx + facing * 20
        hand_y = cy - 2 + int(wave)
        if action == "attack" and 0.35 < attack_progress < 0.6:
            # Reach further during attack
            hand_x += facing * 4
            hand_y -= 2
        # Upper arm
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1),
                               (elbow_x + 1, elbow_y + 1), 5)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["skin_shadow"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["skin_dark"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["skin_mid"],
                               (shoulder_x, shoulder_y - 1),
                               (elbow_x, elbow_y - 1), 2)
        # Gold armband on upper arm
        mid_up_x = (shoulder_x + elbow_x) // 2
        mid_up_y = (shoulder_y + elbow_y) // 2
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                         (mid_up_x - 2, mid_up_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                         (mid_up_x - 2, mid_up_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_light"],
                         (mid_up_x - 1, mid_up_y - 1, 2, 1))
        # Forearm
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                               (elbow_x + 1, elbow_y + 1),
                               (hand_x + 1, hand_y + 1), 5)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["skin_shadow"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["skin_dark"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["skin_mid"],
                               (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Gold bracelet on forearm
        mid_fore_x = (elbow_x + hand_x) // 2
        mid_fore_y = (elbow_y + hand_y) // 2
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                         (mid_fore_x - 2, mid_fore_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_light"],
                         (mid_fore_x - 1, mid_fore_y - 1, 2, 1))
        # Hand
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                                 (hand_x + 1, hand_y + 1), 3)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 3)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["skin_mid"],
                                 (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["skin_light"],
                         (hand_x, hand_y - 1, 1, 1))
        # Magic aura at hand
        aura_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_nyxallaria._alpha(120 * (6 - r) / 6 * aura_pulse)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                     (hand_x, hand_y), r)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_hot"],
                                 (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                         (hand_x, hand_y, 1, 1))
    def _draw_goddess_head(surface, cx, cy, facing, phase):
        """Beautiful goddess face."""
        # Face shape
        face_pts = [
            (cx - 5, cy - 5),
            (cx + 5, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
            (cx - 5, cy + 4),
            (cx - 6, cy - 1),
        ]
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in face_pts])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["skin_shadow"], face_pts)
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["skin_dark"], [
            (cx - 4, cy - 5),
            (cx + 4, cy - 5),
            (cx + 5, cy - 1),
            (cx + 4, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 3),
            (cx - 5, cy - 1),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["skin_mid"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
            (cx - 4, cy),
        ])
        # Highlight on cheek/forehead
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["skin_light"],
                         (cx - 1, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["skin_shine"],
                         (cx, cy - 3, 1, 1))
        # EYES (glowing blue)
        # Left eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for ex_off, side in [(-2, -1), (2, 1)]:
            ex = cx + ex_off
            ey = cy - 1
            # Socket shadow
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow around eye
            for r in range(3, 0, -1):
                alpha = _NS_nyxallaria._alpha(100 * (3 - r) / 3 * eye_pulse)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["eye_mid"], alpha),
                                         (ex, ey), r)
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
        # Eyebrows
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["hair_darkest"],
                         (cx - 3, cy - 3), (cx - 1, cy - 3), 1)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["hair_darkest"],
                         (cx + 1, cy - 3), (cx + 3, cy - 3), 1)
        # Nose (subtle)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["skin_shadow"],
                         (cx, cy + 1), (cx, cy + 3), 1)
        # Lips (small)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["eye_dark"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["purple_light"],
                         (cx, cy + 5, 1, 1))
        # Earrings (blue gems)
        for side in (-1, 1):
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                             (cx + side * 6, cy + 3, 1, 1))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_light"],
                             (cx + side * 6, cy + 5, 1, 2))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                             (cx + side * 6, cy + 5, 1, 1))
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long flowing hair behind body."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        wave3 = math.sin(phase * 0.6 + 3) * 2
        # Hair mass behind head/shoulders (long)
        hair_pts = [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 12, cy + 8),
            (cx + 14 + int(wave1), cy + 20),
            (cx + 12 + int(wave2), cy + 32),
            (cx + 8 + int(wave3), cy + 42),
            (cx + 2, cy + 46),
            (cx - 2, cy + 46),
            (cx - 8 + int(wave3), cy + 42),
            (cx - 12 + int(wave2), cy + 32),
            (cx - 14 + int(wave1), cy + 20),
            (cx - 12, cy + 8),
        ]
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in hair_pts])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["hair_darkest"], hair_pts)
        # Layered hair strands
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["hair_dark"], [
            (cx - 7, cy + 2),
            (cx + 7, cy + 2),
            (cx + 10, cy + 10),
            (cx + 11 + int(wave1 * 0.7), cy + 22),
            (cx + 9 + int(wave2 * 0.7), cy + 34),
            (cx + 4, cy + 42),
            (cx - 4, cy + 42),
            (cx - 9 + int(wave2 * 0.7), cy + 34),
            (cx - 11 + int(wave1 * 0.7), cy + 22),
            (cx - 10, cy + 10),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["hair_mid"], [
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 7, cy + 14),
            (cx + 6, cy + 26),
            (cx + 3, cy + 36),
            (cx - 3, cy + 36),
            (cx - 6, cy + 26),
            (cx - 7, cy + 14),
        ])
        # Hair strand highlights
        for i, x_off in enumerate((-6, -2, 4)):
            strand_x = cx + x_off + int(math.sin(phase * 0.7 + i) * 2)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["hair_light"],
                             (strand_x, cy + 6),
                             (strand_x + int(math.sin(phase + i)), cy + 30), 1)
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front hair strands falling over face."""
        # Bangs / side strands
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["hair_darkest"], [
            (cx - 6, cy),
            (cx + 6, cy),
            (cx + 5, cy + 3),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
            (cx - 5, cy + 3),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["hair_dark"], [
            (cx - 5, cy + 1),
            (cx + 5, cy + 1),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])
        # Side strand highlight
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["hair_light"],
                         (cx - 4, cy + 1), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["hair_light"],
                         (cx + 3, cy + 1), (cx + 4, cy + 3), 1)
    def _draw_crown(surface, cx, cy, facing, phase):
        """Gold crown with spikes and blue gem."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Base band
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             [(cx - 7, cy + 6), (cx + 7, cy + 6),
                              (cx + 7, cy + 9), (cx - 7, cy + 9)])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                             [(cx - 7, cy + 5), (cx + 7, cy + 5),
                              (cx + 7, cy + 8), (cx - 7, cy + 8)])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                             [(cx - 6, cy + 5), (cx + 6, cy + 5),
                              (cx + 6, cy + 7), (cx - 6, cy + 7)])
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_light"],
                         (cx - 5, cy + 5), (cx + 5, cy + 5), 1)
        # Center peak (tallest spike)
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["shadow_deep"], [
            (cx, cy - 3), (cx - 2, cy + 5), (cx + 2, cy + 5),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_dark"], [
            (cx, cy - 4), (cx - 2, cy + 5), (cx + 2, cy + 5),
        ])
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_mid"], [
            (cx, cy - 3), (cx - 1, cy + 5), (cx + 1, cy + 5),
        ])
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_light"],
                         (cx, cy - 3), (cx, cy + 4), 1)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_shine"],
                         (cx, cy - 2, 1, 1))
        # Side spikes
        for side in (-1, 1):
            for offset in (3, 6):
                sx = cx + side * offset
                _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_dark"], [
                    (sx, cy + 1), (sx - 1, cy + 5), (sx + 1, cy + 5),
                ])
                _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_mid"], [
                    (sx, cy + 2), (sx - 1, cy + 5), (sx + 1, cy + 5),  # ✅ 3 titik segitiga
                ])
                pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_light"],
                                 (sx, cy + 2, 1, 1))
        # Central blue gem
        for r in range(4, 0, -1):
            alpha = _NS_nyxallaria._alpha(150 * (4 - r) / 4 * pulse)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                     (cx, cy + 7), r)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_dark"],
                         (cx - 1, cy + 6, 3, 2))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_mid"],
                         (cx - 1, cy + 6, 2, 2))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_light"],
                         (cx, cy + 6, 1, 1))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                         (cx, cy + 6, 1, 1))
    def _draw_trident(surface, cx, cy, facing, phase, action, attack_progress):
        """Ornate golden trident weapon."""
        # Trident held behind, going up-left/right
        back = -facing
        # Shaft goes from bottom (near hip) up to above head
        shaft_bottom_x = cx + back * 2
        shaft_bottom_y = cy + 30
        shaft_top_x = cx + back * 6
        shaft_top_y = cy - 30
        # Shaft
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                               (shaft_bottom_x + 1, shaft_bottom_y + 1),
                               (shaft_top_x + 1, shaft_top_y + 1), 4)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                               (shaft_bottom_x, shaft_bottom_y),
                               (shaft_top_x, shaft_top_y), 3)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                               (shaft_bottom_x, shaft_bottom_y),
                               (shaft_top_x, shaft_top_y), 2)
        _NS_nyxallaria._aaline(surface, _NS_nyxallaria.PALETTE["gold_light"],
                               (shaft_bottom_x - 1, shaft_bottom_y),
                               (shaft_top_x - 1, shaft_top_y), 1)
        # Shaft decorations (rings)
        for i, t in enumerate((0.3, 0.55, 0.75)):
            ring_x = int(shaft_bottom_x + (shaft_top_x - shaft_bottom_x) * t)
            ring_y = int(shaft_bottom_y + (shaft_top_y - shaft_bottom_y) * t)
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                             (ring_x - 2, ring_y - 1, 5, 3))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_light"],
                             (ring_x - 1, ring_y - 1, 3, 1))
        # Trident head (3 prongs)
        head_x = shaft_top_x
        head_y = shaft_top_y
        # Center prong (longest)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                         (head_x + 1, head_y + 1), (head_x + 1, head_y - 12), 4)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                         (head_x, head_y), (head_x, head_y - 12), 3)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                         (head_x, head_y), (head_x, head_y - 12), 2)
        pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_light"],
                         (head_x, head_y), (head_x, head_y - 12), 1)
        # Sharp tip
        _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_light"], [
            (head_x, head_y - 14), (head_x - 2, head_y - 10),
            (head_x + 2, head_y - 10),
        ])
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_shine"],
                         (head_x, head_y - 13, 1, 1))
        # Side prongs (curved)
        for side in (-1, 1):
            # Prong base curves out then up
            base_out_x = head_x + side * 4
            base_out_y = head_y - 3
            tip_x = head_x + side * 5
            tip_y = head_y - 10
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             (head_x + 1, head_y + 1),
                             (base_out_x + 1, base_out_y + 1), 3)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                             (head_x, head_y), (base_out_x, base_out_y), 3)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                             (head_x, head_y), (base_out_x, base_out_y), 2)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["shadow_deep"],
                             (base_out_x + 1, base_out_y + 1),
                             (tip_x + 1, tip_y + 1), 3)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_dark"],
                             (base_out_x, base_out_y), (tip_x, tip_y), 3)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_mid"],
                             (base_out_x, base_out_y), (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["gold_light"],
                             (base_out_x, base_out_y), (tip_x, tip_y), 1)
            # Prong tip
            _NS_nyxallaria._poly(surface, _NS_nyxallaria.PALETTE["gold_light"], [
                (tip_x, tip_y - 2), (tip_x - 1, tip_y + 1),
                (tip_x + 1, tip_y + 1),
            ])
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["gold_shine"],
                             (tip_x, tip_y - 1, 1, 1))
        # Center blue gem at trident base
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_nyxallaria._alpha(180 * (5 - r) / 5 * gem_pulse)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                     (head_x, head_y - 1), r)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_dark"],
                         (head_x - 1, head_y - 2, 3, 3))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_mid"],
                         (head_x - 1, head_y - 2, 2, 2))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_light"],
                         (head_x, head_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                         (head_x, head_y - 2, 1, 1))
        # Energy sparks around trident head
        for i in range(4):
            angle = phase * 2 + i * math.pi / 2
            sx = head_x + int(math.cos(angle) * 8)
            sy = head_y - 4 + int(math.sin(angle) * 5)
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"], (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Elongated ellipse shadow (floating effect)."""
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = _NS_nyxallaria._alpha((12 - radius) * 15 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius // 2,
                 100 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (5, 10, 30, 150), (10, 8, 100, 10))
        pygame.draw.ellipse(shadow, (20, 60, 110, 100), (18, 10, 84, 6))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_water_swirls(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Water swirl/mist below floating goddess."""
        strength = 1.5 if intense else 1.0
        # Water swirl base
        mist = pygame.Surface((140, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_nyxallaria._alpha((30 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                    (70 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_nyxallaria._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                    (70 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising water droplets
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24, -30, 30)):
            t = (phase * 0.5 + i * 0.12) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 24)
            alpha = _NS_nyxallaria._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                     (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_nyxallaria.PALETTE["aqua_shine"], alpha),
                             (sx, sy - 1, 1, 1))
        # Water sparkles (bright)
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.11) % 1.0
            ex = cx - 30 + i * 7 + int(math.sin(phase + i) * 4)
            ey = cy + 2 - int(spark_t * 22)
            alpha = _NS_nyxallaria._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyxallaria.PALETTE["aqua_hot"], alpha),
                                 (ex, ey, 1, 1))
        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxallaria._alpha(150 - i * 22)
                if alpha <= 0:
                    continue
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_moonlit_aura(surface, x, y, phase):
        """Large moonlit blue aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_nyxallaria._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nyxallaria._aacircle(
                    aura, (*_NS_nyxallaria.PALETTE["ocean_dark"], alpha),
                    (110, 100), radius,
                )
        for radius in range(60, 5, -4):
            alpha = _NS_nyxallaria._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyxallaria._aacircle(
                    aura, (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                    (110, 100), radius,
                )
        for radius in range(35, 5, -3):
            alpha = _NS_nyxallaria._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyxallaria._aacircle(
                    aura, (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                    (110, 100), radius,
                )
        surface.blit(aura, (x - 110, y - 100))
        # Floating sparkles (moonlight)
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_nyxallaria.PALETTE["aqua_light"] if i % 2 == 0 \
                else _NS_nyxallaria.PALETTE["moon_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"], (sx, sy, 1, 1))
    def _draw_ground_ripples(surface, x, y, phase, skill):
        """Water ripples on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        # Multiple ripple rings
        for i, (radius_x, radius_y, alpha) in enumerate([
            (78, 22, 180), (65, 18, 200), (52, 14, 220), (40, 10, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                (85 - radius_x + offset, 27 - radius_y,
                                 radius_x * 2, radius_y * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                (85 - radius_x + offset + 1, 27 - radius_y + 1,
                                 radius_x * 2 - 2, radius_y * 2 - 2), 1)
        # Runes around
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 27 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 27 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_nyxallaria.PALETTE["aqua_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_nyxallaria.PALETTE["aqua_hot"],
                                 _NS_nyxallaria._alpha(150 * pulse)),
                                (15, 12, 140, 30), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # RANGED ATTACK - Water projectile
    # ============================================================
    def _draw_water_projectile(surface, boss, x, y, progress):
        """Water projectile from trident."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_nyxallaria._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxallaria._alpha(230 - i * 25)
            size = max(1, 6 - i)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                                     (px, py), size)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                     (px, py), max(1, size - 2))
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                     (px, py), max(1, size - 3))
        # Bright head
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_darkest"], (bx, by), 7)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_dark"], (bx, by), 5)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_mid"], (bx, by), 4)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_light"], (bx, by), 3)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_hot"], (bx, by), 2)
        _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["white"], (bx, by, 1, 1))
    # ============================================================
    # SKILL Q - ABYSSAL LANCE (energy beam projectile)
    # ============================================================
    def _draw_abyssal_lance(surface, boss, x, y, timer, phase):
        """Long piercing water beam."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxallaria._target_position(boss, x, y)
        if progress < 0.2:
            # Charge at hand
            t = progress / 0.2
            hand_x = x + facing * 24
            hand_y = y - 4
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_nyxallaria._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                                         (hand_x, hand_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_nyxallaria._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                         (hand_x, hand_y), r)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_mid"],
                                     (hand_x, hand_y), cr - 2)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_light"],
                                     (hand_x, hand_y), max(1, cr - 4))
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                                     (hand_x, hand_y), max(1, cr - 6))
            # Sparks
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 28
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Elongated shape (like a lance/beam)
            # Long trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_nyxallaria._alpha(240 - i * 20)
                size = max(1, 10 - i)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                                         (px, py), size)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                         (px, py), max(1, size - 1))
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                         (px, py), max(1, size - 2))
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                         (px, py), max(1, size - 3))
                if i < 6:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Big head
            for r in range(16, 3, -2):
                alpha = _NS_nyxallaria._alpha(100 * (16 - r) / 16)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                         (bx, by), r)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_darkest"], (bx, by), 11)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_dark"], (bx, by), 8)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_mid"], (bx, by), 6)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_light"], (bx, by), 4)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_hot"], (bx, by), 2)
            _NS_nyxallaria._aacircle(surface, _NS_nyxallaria.PALETTE["aqua_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["white"], (bx, by, 1, 1))
            # Impact splash on enemies
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(14 + st * 30)
                alpha = _NS_nyxallaria._alpha(240 * (1 - st))
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                                         (tx, ty), radius + 4, 3)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                         (tx, ty), radius, 3)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                         (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - SPECTRAL TIDE (water spirit form)
    # ============================================================
    def _draw_spectral_tide_ground(surface, boss, x, y, timer, phase):
        """Water wave trailing under spectral form."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_dark"], 180),
                                (x - r, y + 40 - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_mid"], 150),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_spectral_overlay(surface, boss, x, y, timer, phase):
        """Translucent water spirit overlay on body."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        overlay = pygame.Surface((80, 100), pygame.SRCALPHA)
        # Watery translucent silhouette
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(30, 5, -3):
            alpha = _NS_nyxallaria._alpha(80 * (30 - r) / 30 * pulse)
            _NS_nyxallaria._aacircle(overlay,
                                     (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                     (40, 50), r)
        # Rising water droplets on body
        for i in range(10):
            drop_t = (phase * 0.8 + i * 0.1) % 1.0
            dx = 15 + int((i % 5) * 10) + int(math.sin(phase + i) * 3)
            dy = 90 - int(drop_t * 80)
            alpha = _NS_nyxallaria._alpha(220 * (1 - drop_t))
            pygame.draw.rect(overlay,
                             (*_NS_nyxallaria.PALETTE["aqua_hot"], alpha),
                             (dx, dy, 1, 1))
            pygame.draw.rect(overlay,
                             (*_NS_nyxallaria.PALETTE["aqua_shine"], alpha),
                             (dx, dy, 1, 1))
        surface.blit(overlay, (x - 40, y - 40))
    # ============================================================
    # SKILL E - MAELSTROM (whirlpool)
    # ============================================================
    def _draw_maelstrom_ground(surface, boss, x, y, timer, phase):
        """Whirlpool base rings."""
        tx, ty = _NS_nyxallaria._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))
        if r > 3:
            # Multiple concentric ellipses forming vortex
            for i, (mult, alpha_val) in enumerate([
                (1.0, 220), (0.85, 200), (0.7, 180), (0.55, 160),
                (0.4, 140), (0.25, 120),
            ]):
                cur_r = int(r * mult)
                rot = phase * 2 + i * 0.5
                offset_x = int(math.cos(rot) * 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha_val),
                                    (tx - cur_r + offset_x, ty - cur_r // 3,
                                     cur_r * 2, cur_r * 2 // 3), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha_val),
                                    (tx - cur_r + offset_x + 1,
                                     ty - cur_r // 3 + 1,
                                     cur_r * 2 - 2, cur_r * 2 // 3 - 2), 1)
    def _draw_maelstrom_foreground(surface, boss, x, y, timer, phase):
        """Swirling water pull arrows and sparks."""
        tx, ty = _NS_nyxallaria._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))
        if r < 5:
            return
        # Rotating water sparks (spiral inward)
        for i in range(20):
            spiral_t = (phase * 1.5 + i * 0.1) % 1.0
            dist = r * (1 - spiral_t)
            angle = phase * 3 + i * math.pi / 10 + spiral_t * math.pi * 2
            sx = tx + int(math.cos(angle) * dist)
            sy = ty + int(math.sin(angle) * dist * 0.5)
            alpha = _NS_nyxallaria._alpha(230 * spiral_t)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                     (sx, sy), 3)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                     (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_nyxallaria.PALETTE["aqua_shine"], alpha),
                             (sx, sy, 1, 1))
        # Pull direction arrows around edge
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            arrow_x = tx + int(math.cos(angle) * r)
            arrow_y = ty + int(math.sin(angle) * r * 0.5)
            # Arrow points inward
            inner_x = tx + int(math.cos(angle) * (r - 8))
            inner_y = ty + int(math.sin(angle) * (r - 8) * 0.5)
            pygame.draw.line(surface, _NS_nyxallaria.PALETTE["aqua_light"],
                             (arrow_x, arrow_y), (inner_x, inner_y), 2)
            pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_hot"],
                             (inner_x, inner_y, 2, 2))
        # Center vortex glow
        for r_inner in range(8, 0, -1):
            alpha = _NS_nyxallaria._alpha(120 * (8 - r_inner) / 8)
            _NS_nyxallaria._aacircle(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                     (tx, ty), r_inner)
    # ============================================================
    # SKILL R - LEVIATHAN'S WRATH (massive wave)
    # ============================================================
    def _draw_leviathan_ground(surface, boss, x, y, timer, phase):
        """Massive wave circle."""
        tx, ty = _NS_nyxallaria._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning circle grows
            t = progress / 0.4
            r = int(65 * t)
            alpha = _NS_nyxallaria._alpha(180 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_light"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.4) / 0.6
            r = int(65 + t * 20)
            alpha = _NS_nyxallaria._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxallaria.PALETTE["aqua_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_leviathan_foreground(surface, boss, x, y, timer, phase):
        """Massive tidal wave rising."""
        tx, ty = _NS_nyxallaria._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Gathering water above
            t = progress / 0.4
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                gather_r = int(30 * (1 - t))
                gx = tx + int(math.cos(angle) * gather_r)
                gy = ty - 40 + int(math.sin(angle) * gather_r * 0.5)
                alpha = _NS_nyxallaria._alpha(200 * t)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                         (gx, gy), 3)
                _NS_nyxallaria._aacircle(surface,
                                         (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                         (gx, gy), 2)
        elif progress < 0.75:
            # Wave crashes down
            t = (progress - 0.4) / 0.35
            intensity = math.sin(t * math.pi)
            # Massive wave shape (crescent)
            wave_h = int(80 * intensity)
            for layer_i in range(5):
                layer_offset = layer_i * 3
                layer_alpha = _NS_nyxallaria._alpha(220 - layer_i * 30)
                colors = [
                    _NS_nyxallaria.PALETTE["aqua_darkest"],
                    _NS_nyxallaria.PALETTE["aqua_dark"],
                    _NS_nyxallaria.PALETTE["aqua_mid"],
                    _NS_nyxallaria.PALETTE["aqua_light"],
                    _NS_nyxallaria.PALETTE["aqua_hot"],
                ]
                # Wave crescent
                wave_pts = []
                for i in range(21):
                    a = i / 20 * math.pi
                    wave_x = tx + int(math.cos(a) * 70)
                    wave_y = ty - int(math.sin(a) * wave_h) - layer_offset
                    wave_pts.append((wave_x, wave_y))
                wave_pts.append((tx + 70, ty + 5))
                wave_pts.append((tx - 70, ty + 5))
                if len(wave_pts) >= 3:
                    _NS_nyxallaria._poly(surface,
                                         (*colors[layer_i], layer_alpha),
                                         wave_pts)
            # Foam/sparkles on top of wave
            for i in range(15):
                angle_top = i / 14 * math.pi
                foam_x = tx + int(math.cos(angle_top) * 70)
                foam_y = ty - int(math.sin(angle_top) * wave_h)
                pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["aqua_shine"],
                                 (foam_x, foam_y, 2, 2))
                pygame.draw.rect(surface, _NS_nyxallaria.PALETTE["white"],
                                 (foam_x, foam_y, 1, 1))
            # Sparks flying outward
            for i in range(20):
                spark_angle = i * math.pi / 10
                spark_r = int(wave_h * 0.7)
                sx = tx + int(math.cos(spark_angle) * spark_r * 1.2)
                sy = ty - wave_h // 2 + int(math.sin(spark_angle) * spark_r * 0.5)
                alpha = _NS_nyxallaria._alpha(240 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_nyxallaria.PALETTE["aqua_hot"], alpha),
                                 (sx, sy, 2, 2))
        else:
            # Aftermath: airborne effects (enemies knocked up)
            t = (progress - 0.75) / 0.25
            for i in range(10):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 40)
                alpha = _NS_nyxallaria._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_nyxallaria._aacircle(surface,
                                             (*_NS_nyxallaria.PALETTE["aqua_dark"], alpha),
                                             (rx, ry), 3)
                    _NS_nyxallaria._aacircle(surface,
                                             (*_NS_nyxallaria.PALETTE["aqua_light"], alpha),
                                             (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_nyxallaria.PALETTE["aqua_shine"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# VHAERINTH (INKWEAVER) - Mini Boss
# ====================================================================

class _NS_vhaerinth:
    """Namespace vhaerinth - ink sorcerer boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale, old wizard)
        "skin_darkest": (50, 30, 30),
        "skin_dark": (110, 80, 75),
        "skin_mid": (175, 145, 130),
        "skin_light": (225, 200, 185),
        "skin_shine": (250, 235, 220),
        # BEARD/HAIR (white/silver)
        "beard_darkest": (60, 55, 55),
        "beard_dark": (120, 115, 115),
        "beard_mid": (185, 180, 180),
        "beard_light": (230, 230, 230),
        "beard_shine": (255, 255, 255),
        # Robe main (dark crimson red)
        "robe_darkest": (18, 5, 5),
        "robe_dark": (60, 15, 15),
        "robe_mid": (130, 30, 30),
        "robe_light": (200, 55, 55),
        "robe_edge": (240, 100, 90),
        # Robe under (dark - inner cloth)
        "under_darkest": (5, 3, 5),
        "under_dark": (18, 12, 15),
        "under_mid": (40, 30, 35),
        "under_light": (75, 60, 65),
        # GOLD trim (ancient patterns)
        "gold_darkest": (35, 25, 5),
        "gold_dark": (95, 70, 15),
        "gold_mid": (195, 155, 45),
        "gold_light": (245, 215, 110),
        "gold_shine": (255, 245, 190),
        # Steel armor (pauldrons, plates)
        "steel_dark": (25, 25, 30),
        "steel_mid": (75, 78, 88),
        "steel_light": (150, 155, 170),
        "steel_shine": (215, 220, 235),
        # Horns (black-charcoal)
        "horn_darkest": (5, 3, 8),
        "horn_dark": (25, 18, 25),
        "horn_mid": (60, 50, 55),
        "horn_light": (110, 100, 105),
        # Skull (bone white on forehead)
        "skull_dark": (100, 90, 75),
        "skull_mid": (200, 190, 170),
        "skull_light": (245, 235, 215),
        # INK / BLOOD RED (signature magic)
        "ink_darkest": (35, 3, 5),
        "ink_dark": (95, 8, 15),
        "ink_mid": (200, 25, 35),
        "ink_light": (255, 80, 85),
        "ink_hot": (255, 160, 155),
        "ink_shine": (255, 230, 225),
        # Eye (red glow beneath skull)
        "eye_socket": (5, 0, 3),
        "eye_dark": (100, 8, 15),
        "eye_mid": (220, 40, 45),
        "eye_light": (255, 130, 130),
        # Brush handle (dark wood + gold caps)
        "wood_dark": (25, 12, 8),
        "wood_mid": (60, 30, 15),
        "wood_light": (110, 65, 30),
        # Lantern (gold cage + red glow inside)
        "lantern_glass_dark": (60, 8, 10),
        "lantern_glass_mid": (200, 25, 30),
        "lantern_glass_light": (255, 130, 100),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vhaerinth._clamp(color)
        if _NS_vhaerinth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vhaerinth._clamp(color)
        if _NS_vhaerinth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vhaerinth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vhaerinth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_vhaerinth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_vha_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_vhaerinth._draw_ink_aura(surface, x, y, pulse)
        _NS_vhaerinth._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Ink puddle beneath boss (signature).
        _NS_vhaerinth._draw_ink_puddle(surface, x, y + 44, pulse)
        # Skill ground FX.
        if active_skill == "q":
            _NS_vhaerinth._draw_inktrail_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhaerinth._draw_chaosstorm_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_vhaerinth._draw_vha_attack(surface, boss, x, y)
        else:
            _NS_vhaerinth._draw_vha_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_vhaerinth._draw_inktrail_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vhaerinth._draw_soulchain_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vhaerinth._draw_phantasmagoria_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhaerinth._draw_chaosstorm_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vha_previous_timer", 0))
        active = bool(getattr(boss, "_vha_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vha_attack_active = True
            boss._vha_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vha_attack_frame = int(getattr(boss, "_vha_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vha_attack_active = False
            boss._vha_attack_frame = 0
            active = False
        boss._vha_previous_timer = timer
        boss._vha_attack_progress = (
            min(1.0, getattr(boss, "_vha_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vha_float(surface, boss, x, y):
        """Idle: floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_vhaerinth._draw_shadow(surface, x, y + 52)
        _NS_vhaerinth._draw_ink_wisps(surface, x, y + 25, boss.pulse)
        _NS_vhaerinth._draw_vha_body(surface, x, y - 6 + hover,
                                     boss.direction, boss.pulse, "float", 0)
    def _draw_vha_attack(surface, boss, x, y):
        """Attack: raise brush, splash ink projectile."""
        progress = getattr(boss, "_vha_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.5) * 5)
        lean = 0
        lift = 0
        if progress < 0.35:
            t = progress / 0.35
            lean = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 8)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_vhaerinth._draw_shadow(surface, x + lean, y + 52)
        _NS_vhaerinth._draw_ink_wisps(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_vhaerinth._draw_vha_body(surface, x + lean, y - 6 + hover - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Ink projectile from brush tip.
        _NS_vhaerinth._draw_ink_projectile(surface, boss, x + lean, y - 6 + hover - lift,
                                           progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_vha_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_vhaerinth._draw_vha_body_to(surface, cx, cy, facing, phase, action,
                                        attack_progress, 1.0)
    def _draw_vha_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Ink sorcerer body — robe, arms holding brush & lantern, hooded skull head."""
        # Robe trailing bottom.
        _NS_vhaerinth._draw_robe_trail(surface, cx, cy + 14, facing, phase, alpha_scale)
        # Main robe body (crimson & gold).
        _NS_vhaerinth._draw_robe_body(surface, cx, cy, facing, phase, alpha_scale)
        # Shoulder pauldrons (silver metal).
        _NS_vhaerinth._draw_shoulder_pauldrons(surface, cx, cy - 8, facing, phase, alpha_scale)
        # Arms + brush + lantern.
        _NS_vhaerinth._draw_vha_arms(surface, cx, cy, facing, phase, action,
                                     attack_progress, alpha_scale)
        # Head with horns, skull mark, white beard.
        _NS_vhaerinth._draw_vha_head(surface, cx, cy - 22, facing, phase, alpha_scale)
    def _draw_robe_trail(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Trailing robe bottom with gold trim."""
        alpha_base = int(255 * alpha_scale)
        for i in range(5):
            t = i / 4
            wave = math.sin(phase * 0.9 + i * 0.5) * (3 + i)
            trail_x = cx + int(wave)
            trail_y = cy + int(i * 5)
            width = int(22 - i * 2)
            alpha = int(220 * alpha_scale) - i * 32
            if alpha <= 0:
                continue
            trail_surf = pygame.Surface((width * 2 + 4, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(trail_surf, (*_NS_vhaerinth.PALETTE["robe_darkest"], alpha),
                                (0, 0, width * 2, 8))
            pygame.draw.ellipse(trail_surf, (*_NS_vhaerinth.PALETTE["robe_dark"], alpha),
                                (2, 1, width * 2 - 4, 6))
            pygame.draw.ellipse(trail_surf, (*_NS_vhaerinth.PALETTE["robe_mid"], max(0, alpha - 40)),
                                (4, 2, width * 2 - 8, 4))
            # Gold trim strip.
            pygame.draw.ellipse(trail_surf, (*_NS_vhaerinth.PALETTE["gold_mid"], max(0, alpha - 40)),
                                (2, 0, width * 2 - 4, 1))
            surface.blit(trail_surf, (trail_x - width, trail_y))
        # Ink wisps rising below.
        for i in range(6):
            wisp_t = (phase * 0.5 + i * 0.16) % 1.0
            wx = cx + int(math.sin(phase + i) * 14)
            wy = cy + 4 + int(wisp_t * 26)
            alpha = _NS_vhaerinth._alpha(180 * (1 - wisp_t) * alpha_scale)
            if alpha > 0:
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                 (wx, wy, 1, 1))
    def _draw_robe_body(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Crimson robe torso with gold panels."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.7) * 1
        # Main robe shape.
        robe_pts = [
            (cx - 12, cy - 12),
            (cx - 14, cy - 4),
            (cx - 17, cy + 6),
            (cx - 22, cy + 16),
            (cx + 22, cy + 16),
            (cx + 17, cy + 6),
            (cx + 14, cy - 4),
            (cx + 12, cy - 12),
        ]
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"], robe_pts,
                                  alpha_base, offset=(2, 3))
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["robe_darkest"], robe_pts,
                                  alpha_base)
        # Robe mid.
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["robe_dark"], [
            (cx - 11, cy - 11),
            (cx - 13, cy - 3),
            (cx - 15, cy + 6),
            (cx - 19, cy + 14),
            (cx + 19, cy + 14),
            (cx + 15, cy + 6),
            (cx + 13, cy - 3),
            (cx + 11, cy - 11),
        ], alpha_base)
        # Middle robe panel (mid tone).
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["robe_mid"], [
            (cx - 8, cy - 10),
            (cx - 10, cy + 2),
            (cx - 13, cy + 12),
            (cx + 13, cy + 12),
            (cx + 10, cy + 2),
            (cx + 8, cy - 10),
        ], alpha_base)
        # UNDER cloth (dark under-layer showing on center).
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["under_dark"], [
            (cx - 4, cy - 10),
            (cx - 6, cy + 2),
            (cx - 8, cy + 12),
            (cx + 8, cy + 12),
            (cx + 6, cy + 2),
            (cx + 4, cy - 10),
        ], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["under_mid"], [
            (cx - 3, cy - 8),
            (cx - 5, cy + 2),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 5, cy + 2),
            (cx + 3, cy - 8),
        ], alpha_base)
        # Gold trim along robe center (vertical).
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                         (cx - 4, cy - 10), (cx - 8, cy + 12), 2)
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                         (cx - 4, cy - 10), (cx - 8, cy + 12), 1)
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                         (cx + 4, cy - 10), (cx + 8, cy + 12), 2)
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                         (cx + 4, cy - 10), (cx + 8, cy + 12), 1)
        # Gold trim horizontal (belt).
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                         (cx - 14, cy + 2), (cx + 14, cy + 2), 2)
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                         (cx - 14, cy + 2), (cx + 14, cy + 2), 1)
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                         (cx - 12, cy + 2), (cx + 12, cy + 2), 1)
        # Ornament / gold diamond on chest.
        diamond_y = cy - 4
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["gold_darkest"], [
            (cx, diamond_y - 3), (cx + 3, diamond_y),
            (cx, diamond_y + 3), (cx - 3, diamond_y),
        ], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["gold_mid"], [
            (cx, diamond_y - 2), (cx + 2, diamond_y),
            (cx, diamond_y + 2), (cx - 2, diamond_y),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                         (cx, diamond_y - 1, 1, 1))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_shine"], alpha_base),
                         (cx, diamond_y - 1, 1, 1))
        # Robe edge highlight.
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["robe_edge"], alpha_base),
                         (cx - 12, cy - 10), (cx - 20, cy + 14), 1)
        pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["robe_edge"], alpha_base),
                         (cx + 12, cy - 10), (cx + 20, cy + 14), 1)
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Silver metallic pauldrons with gold trim + red inner."""
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            base_x = cx + side * 11
            base_y = cy
            # Pauldron shape.
            pad_pts = [
                (base_x, base_y - 3),
                (base_x + side * 5, base_y - 5),
                (base_x + side * 9, base_y - 1),
                (base_x + side * 8, base_y + 5),
                (base_x + side * 2, base_y + 6),
            ]
            _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"], pad_pts,
                                      alpha_base, offset=(2, 2))
            _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["steel_dark"], pad_pts,
                                      alpha_base)
            _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["steel_mid"], [
                (base_x + side * 1, base_y - 2),
                (base_x + side * 4, base_y - 4),
                (base_x + side * 8, base_y),
                (base_x + side * 7, base_y + 4),
                (base_x + side * 2, base_y + 5),
            ], alpha_base)
            _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["steel_light"], [
                (base_x + side * 2, base_y - 1),
                (base_x + side * 4, base_y - 3),
                (base_x + side * 6, base_y),
                (base_x + side * 5, base_y + 2),
                (base_x + side * 3, base_y + 3),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["steel_shine"], alpha_base),
                             (base_x + side * 4, base_y - 3, 1, 1))
            # Gold trim edge.
            pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                             (base_x + side * 5, base_y - 5),
                             (base_x + side * 9, base_y - 1), 1)
            pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                             (base_x + side * 6, base_y - 4),
                             (base_x + side * 8, base_y - 2), 1)
            # Red inner cloth peeking below pauldron.
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["robe_mid"], alpha_base),
                             (base_x + side * 3, base_y + 5, 4, 2))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["robe_light"], alpha_base),
                             (base_x + side * 4, base_y + 5, 2, 1))
    def _draw_vha_arms(surface, cx, cy, facing, phase, action, attack_progress,
                       alpha_scale=1.0):
        """Two arms — front holds brush, other holds lantern chain."""
        alpha_base = int(255 * alpha_scale)
        # BRUSH arm (facing side).
        brush_side = facing
        arm_r_base_x = cx + brush_side * 10
        arm_r_base_y = cy - 6
        # Arm angle for brush during attack.
        raise_amount = 0
        if action == "attack":
            if attack_progress < 0.35:
                raise_amount = int(attack_progress / 0.35 * 10)
            elif attack_progress < 0.6:
                raise_amount = int(10 - (attack_progress - 0.35) / 0.25 * 15)
            else:
                raise_amount = int(-5 + (attack_progress - 0.6) / 0.4 * 5)
        hand_r_x = arm_r_base_x + brush_side * 4
        hand_r_y = arm_r_base_y + 8 - raise_amount
        elbow_r_x = arm_r_base_x + brush_side * 2
        elbow_r_y = arm_r_base_y + 3 - raise_amount // 2
        _NS_vhaerinth._draw_arm_segment(surface,
                                        (arm_r_base_x, arm_r_base_y),
                                        (elbow_r_x, elbow_r_y),
                                        (hand_r_x, hand_r_y), alpha_base)
        # LANTERN arm (opposite side).
        opp_side = -facing
        arm_l_base_x = cx + opp_side * 10
        arm_l_base_y = cy - 6
        sway = math.sin(phase * 0.6) * 1
        hand_l_x = arm_l_base_x + opp_side * 8 + int(sway)
        hand_l_y = arm_l_base_y + 6
        elbow_l_x = arm_l_base_x + opp_side * 4
        elbow_l_y = arm_l_base_y + 2
        _NS_vhaerinth._draw_arm_segment(surface,
                                        (arm_l_base_x, arm_l_base_y),
                                        (elbow_l_x, elbow_l_y),
                                        (hand_l_x, hand_l_y), alpha_base)
        # LANTERN dangling from left hand (via chain).
        _NS_vhaerinth._draw_lantern(surface, hand_l_x, hand_l_y, phase, alpha_base)
        # BRUSH held in right hand.
        _NS_vhaerinth._draw_ink_brush(surface, hand_r_x, hand_r_y, brush_side, phase,
                                      action, attack_progress, alpha_base)
    def _draw_arm_segment(surface, base, elbow, hand, alpha_base):
        """Robed arm segment."""
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                    (base[0] + 1, base[1] + 1),
                                    (elbow[0] + 1, elbow[1] + 1), 5, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["robe_darkest"],
                                    base, elbow, 4, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["robe_dark"],
                                    base, elbow, 3, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["robe_mid"],
                                    (base[0], base[1] - 1), (elbow[0], elbow[1] - 1), 1,
                                    alpha_base)
        # Gold cuff at elbow.
        _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                                (elbow[0], elbow[1]), 3)
        _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                                (elbow[0], elbow[1]), 2)
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                         (elbow[0], elbow[1] - 1, 1, 1))
        # Forearm.
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                    (elbow[0] + 1, elbow[1] + 1),
                                    (hand[0] + 1, hand[1] + 1), 5, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["robe_darkest"],
                                    elbow, hand, 4, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["robe_dark"],
                                    elbow, hand, 3, alpha_base)
        # Hand (skin, pale wrinkled).
        _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["skin_dark"], alpha_base),
                                (hand[0], hand[1]), 3)
        _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["skin_mid"], alpha_base),
                                (hand[0], hand[1]), 2)
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["skin_light"], alpha_base),
                         (hand[0], hand[1] - 1, 1, 1))
    def _draw_ink_brush(surface, hx, hy, side, phase, action, attack_progress, alpha_base):
        """Giant brush staff — handle + bristles at top with ink dripping."""
        # Brush extends up.
        brush_top_x = hx + side * 2
        brush_top_y = hy - 30
        brush_bot_x = hx - side * 1
        brush_bot_y = hy + 14
        # Shadow.
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                    (brush_top_x + 2, brush_top_y + 2),
                                    (brush_bot_x + 2, brush_bot_y + 2), 4, alpha_base)
        # Handle (dark wood).
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["wood_dark"],
                                    (brush_top_x, brush_top_y),
                                    (brush_bot_x, brush_bot_y), 3, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["wood_mid"],
                                    (brush_top_x, brush_top_y),
                                    (brush_bot_x, brush_bot_y), 2, alpha_base)
        _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["wood_light"],
                                    (brush_top_x - side, brush_top_y),
                                    (brush_bot_x - side, brush_bot_y), 1, alpha_base)
        # Gold rings along handle.
        for ring_i in range(3):
            ring_t = 0.25 + ring_i * 0.2
            rx = int(brush_top_x + (brush_bot_x - brush_top_x) * ring_t)
            ry = int(brush_top_y + (brush_bot_y - brush_top_y) * ring_t)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                             (rx - 2, ry - 1, 4, 2))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                             (rx - 2, ry - 1, 4, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                             (rx - 1, ry - 1, 2, 1))
        # BRUSH FERRULE (metal cap at top holding bristles).
        ferrule_x = brush_top_x
        ferrule_y = brush_top_y - 2
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["shadow_deep"], alpha_base),
                         (ferrule_x - 3, ferrule_y - 2, 6, 5))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                         (ferrule_x - 3, ferrule_y - 2, 6, 4))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                         (ferrule_x - 3, ferrule_y - 2, 6, 3))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                         (ferrule_x - 2, ferrule_y - 2, 4, 1))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_shine"], alpha_base),
                         (ferrule_x - 1, ferrule_y - 2, 2, 1))
        # BRISTLES (white with red ink-tips) - flowing/fanning shape.
        bristle_tip_x = ferrule_x + side * 4
        bristle_tip_y = ferrule_y - 10
        # Bristle base shape (fan).
        bristle_pts = [
            (ferrule_x - 3, ferrule_y - 2),
            (ferrule_x + 3, ferrule_y - 2),
            (bristle_tip_x + 4, bristle_tip_y),
            (bristle_tip_x, bristle_tip_y - 3),
            (bristle_tip_x - 5, bristle_tip_y + 2),
        ]
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                  [(p[0] + 1, p[1] + 1) for p in bristle_pts], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_darkest"], bristle_pts,
                                  alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_dark"], [
            (ferrule_x - 2, ferrule_y - 2),
            (ferrule_x + 2, ferrule_y - 2),
            (bristle_tip_x + 3, bristle_tip_y),
            (bristle_tip_x, bristle_tip_y - 2),
            (bristle_tip_x - 4, bristle_tip_y + 1),
        ], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_mid"], [
            (ferrule_x - 1, ferrule_y - 2),
            (ferrule_x + 1, ferrule_y - 2),
            (bristle_tip_x + 2, bristle_tip_y),
            (bristle_tip_x - 3, bristle_tip_y + 1),
        ], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_light"], [
            (ferrule_x, ferrule_y - 2),
            (ferrule_x + 1, ferrule_y - 2),
            (bristle_tip_x, bristle_tip_y - 1),
            (bristle_tip_x - 2, bristle_tip_y),
        ], alpha_base)
        # Individual bristle lines.
        for bristle_i in range(4):
            bt = bristle_i / 3
            bx = ferrule_x + int(-2 + bt * 6)
            by_start = ferrule_y - 2
            bx_end = bristle_tip_x + int(-4 + bt * 8)
            by_end = bristle_tip_y + int(2 - bt * 3)
            pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["beard_dark"], alpha_base),
                             (bx, by_start), (bx_end, by_end), 1)
        # RED INK on bristle tips (like dripping paint).
        ink_intensity = 1.5 if action == "attack" else 1.0
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Red-stained tips.
        ink_tips = [
            (bristle_tip_x - 4, bristle_tip_y + 2),
            (bristle_tip_x - 1, bristle_tip_y - 1),
            (bristle_tip_x + 2, bristle_tip_y),
            (bristle_tip_x + 4, bristle_tip_y + 1),
        ]
        for tip in ink_tips:
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha_base),
                                    tip, 2)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha_base),
                                    tip, 1)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha_base),
                             (tip[0], tip[1], 1, 1))
        # Glow at brush tip.
        for r in range(int(6 * ink_intensity), 0, -1):
            alpha = _NS_vhaerinth._alpha(120 * pulse * ink_intensity * (6 - r) / 6 * alpha_base / 255)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                    (bristle_tip_x, bristle_tip_y), r)
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha_base),
                         (bristle_tip_x, bristle_tip_y, 1, 1))
        # Ink drips falling.
        for drip_i in range(2):
            drip_t = (phase * 0.6 + drip_i * 0.3) % 1.0
            drip_x = ink_tips[drip_i % len(ink_tips)][0]
            drip_y = ink_tips[drip_i % len(ink_tips)][1] + int(drip_t * 12)
            drip_alpha = _NS_vhaerinth._alpha(200 * (1 - drip_t) * alpha_base / 255)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], drip_alpha),
                             (drip_x, drip_y, 1, 2))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], drip_alpha),
                             (drip_x, drip_y, 1, 1))
    def _draw_lantern(surface, hx, hy, phase, alpha_base):
        """Ornate gold lantern with red glow inside, dangling from chain."""
        # Chain from hand down.
        chain_len = 8
        chain_bot_x = hx
        chain_bot_y = hy + chain_len
        for chain_i in range(3):
            cy_pos = hy + chain_i * 3
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["shadow_deep"], alpha_base),
                             (hx - 1 + 1, cy_pos + 1, 2, 2))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["steel_dark"], alpha_base),
                             (hx - 1, cy_pos, 2, 2))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["steel_mid"], alpha_base),
                             (hx - 1, cy_pos, 2, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["steel_light"], alpha_base),
                             (hx, cy_pos, 1, 1))
        # Lantern top cap (gold).
        lx = chain_bot_x
        ly = chain_bot_y + 2
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["shadow_deep"], alpha_base),
                         (lx - 3, ly + 1, 6, 2))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                         (lx - 3, ly, 6, 2))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                         (lx - 3, ly, 6, 1))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_light"], alpha_base),
                         (lx - 2, ly, 4, 1))
        # Lantern body (red glass inside gold cage).
        body_y = ly + 2
        # Glow behind glass.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(9, 0, -1):
            alpha = _NS_vhaerinth._alpha(140 * pulse * (9 - r) / 9 * alpha_base / 255)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                    (lx, body_y + 3), r)
        # Glass body.
        glass_pts = [
            (lx - 4, body_y),
            (lx + 4, body_y),
            (lx + 4, body_y + 7),
            (lx - 4, body_y + 7),
        ]
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                  [(p[0] + 1, p[1] + 1) for p in glass_pts], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["lantern_glass_dark"], glass_pts,
                                  alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["lantern_glass_mid"], [
            (lx - 3, body_y + 1),
            (lx + 3, body_y + 1),
            (lx + 3, body_y + 6),
            (lx - 3, body_y + 6),
        ], alpha_base)
        # Bright core (flame inside).
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["lantern_glass_light"], alpha_base),
                         (lx - 1, body_y + 2, 2, 4))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha_base),
                         (lx, body_y + 3, 1, 2))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["white"], alpha_base),
                         (lx, body_y + 4, 1, 1))
        # Gold cage bars (vertical).
        for bar_x in (-3, 0, 3):
            pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                             (lx + bar_x, body_y), (lx + bar_x, body_y + 7), 1)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                             (lx + bar_x, body_y, 1, 1))
        # Lantern bottom cap.
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_dark"], alpha_base),
                         (lx - 3, body_y + 7, 6, 2))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["gold_mid"], alpha_base),
                         (lx - 3, body_y + 7, 6, 1))
        # Point bottom.
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["gold_dark"], [
            (lx - 2, body_y + 9), (lx + 2, body_y + 9), (lx, body_y + 11),
        ], alpha_base)
    def _draw_vha_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Head with horns, forehead skull mark, white beard."""
        alpha_base = int(255 * alpha_scale)
        # Skin face shape.
        head_pts = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 6, cy + 9),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 6, cy + 9),
            (cx + 7, cy + 4),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"], head_pts,
                                  alpha_base, offset=(2, 2))
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["skin_darkest"], head_pts,
                                  alpha_base)
        # Skin base.
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 5, cy + 8),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
        ], alpha_base)
        # Skin mid.
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["skin_mid"], [
            (cx - 4, cy + 2),
            (cx - 5, cy + 5),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 5, cy + 5),
            (cx + 4, cy + 2),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["skin_light"], alpha_base),
                         (cx - 1, cy + 3, 3, 1))
        # SKULL MARK ON FOREHEAD (small white skull symbol).
        skull_y = cy + 1
        # Skull main circle (bone white).
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["skull_dark"], alpha_base),
                         (cx - 3, skull_y - 1, 6, 4))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["skull_mid"], alpha_base),
                         (cx - 2, skull_y - 1, 4, 3))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["skull_light"], alpha_base),
                         (cx - 1, skull_y - 1, 2, 1))
        # Eye sockets (dark).
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["shadow_deep"], alpha_base),
                         (cx - 2, skull_y + 1, 1, 1))
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["shadow_deep"], alpha_base),
                         (cx + 1, skull_y + 1, 1, 1))
        # Skull red glow.
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha_base),
                         (cx, skull_y + 2, 1, 1))
        # BLACK HORNS (curved, from head sides).
        _NS_vhaerinth._draw_curved_horns(surface, cx, cy, phase, alpha_base)
        # RED EYES beneath skull mark.
        _NS_vhaerinth._draw_red_eyes(surface, cx, cy + 5, phase, alpha_scale)
        # LONG WHITE BEARD.
        _NS_vhaerinth._draw_white_beard(surface, cx, cy + 11, phase, alpha_base)
    def _draw_curved_horns(surface, cx, cy, phase, alpha_base):
        """Two black curved horns extending outward from head."""
        for side in (-1, 1):
            # Horn base at head side.
            base_x = cx + side * 5
            base_y = cy - 1
            # Horn extends up-out then curves inward at tip.
            mid_x = cx + side * 10
            mid_y = cy - 4
            tip_x = cx + side * 12
            tip_y = cy - 2  # curves back down slightly
            # Shadow.
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                        (base_x + 1, base_y + 1), (mid_x + 1, mid_y + 1),
                                        5, alpha_base)
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                        (mid_x + 1, mid_y + 1), (tip_x + 1, tip_y + 1),
                                        4, alpha_base)
            # Horn body.
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["horn_darkest"],
                                        (base_x, base_y), (mid_x, mid_y), 4, alpha_base)
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["horn_darkest"],
                                        (mid_x, mid_y), (tip_x, tip_y), 3, alpha_base)
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["horn_dark"],
                                        (base_x, base_y), (mid_x, mid_y), 3, alpha_base)
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["horn_dark"],
                                        (mid_x, mid_y), (tip_x, tip_y), 2, alpha_base)
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["horn_mid"],
                                        (base_x, base_y - 1), (mid_x, mid_y - 1), 1, alpha_base)
            _NS_vhaerinth._aaline_alpha(surface, _NS_vhaerinth.PALETTE["horn_mid"],
                                        (mid_x, mid_y - 1), (tip_x, tip_y - 1), 1, alpha_base)
            # Tip highlight.
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["horn_light"], alpha_base),
                             (tip_x, tip_y, 1, 1))
    def _draw_red_eyes(surface, cx, cy, phase, alpha_scale=1.0):
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            for r in range(4, 0, -1):
                a = _NS_vhaerinth._alpha(140 * (4 - r) / 4 * pulse * alpha_scale)
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["eye_mid"], a),
                                        (ex, ey), r)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["eye_mid"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["eye_light"], alpha_base),
                             (ex, ey, 1, 1))
    def _draw_white_beard(surface, cx, cy, phase, alpha_base):
        """Long flowing white beard from chin."""
        sway = math.sin(phase * 0.5) * 1
        # Beard main shape (long, tapering).
        beard_pts = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 3),
            (cx - 5 + int(sway), cy + 8),
            (cx - 3 + int(sway), cy + 13),
            (cx + int(sway * 1.5), cy + 16),
            (cx + 3 + int(sway), cy + 13),
            (cx + 5 + int(sway), cy + 8),
            (cx + 6, cy + 3),
            (cx + 5, cy - 1),
        ]
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                  [(p[0] + 1, p[1] + 2) for p in beard_pts], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_darkest"], beard_pts,
                                  alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 4),
            (cx - 4 + int(sway), cy + 8),
            (cx - 2 + int(sway), cy + 12),
            (cx + int(sway), cy + 14),
            (cx + 2 + int(sway), cy + 12),
            (cx + 4 + int(sway), cy + 8),
            (cx + 5, cy + 4),
            (cx + 4, cy),
        ], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_mid"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 5),
            (cx - 2, cy + 9),
            (cx, cy + 12),
            (cx + 2, cy + 9),
            (cx + 4, cy + 5),
            (cx + 3, cy + 1),
        ], alpha_base)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["beard_light"], [
            (cx - 2, cy + 2),
            (cx - 3, cy + 6),
            (cx, cy + 10),
            (cx + 3, cy + 6),
            (cx + 2, cy + 2),
        ], alpha_base)
        # Beard strand highlights.
        for strand_i in range(3):
            strand_x_off = -3 + strand_i * 3
            pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["beard_shine"], alpha_base),
                             (cx + strand_x_off, cy + 1),
                             (cx + strand_x_off + int(sway * 0.5), cy + 8), 1)
        # Beard tip.
        pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["beard_shine"], alpha_base),
                         (cx + int(sway * 1.5), cy + 15, 1, 1))
    # ============================================================
    # HELPERS
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_vhaerinth._poly(surface, color, points)
            return
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_vhaerinth._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_vhaerinth._aaline(surface, color, start, end, width)
            return
        c = _NS_vhaerinth._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 16 - radius, 126 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (12, 3, 3, 170), (5, 9, 140, 15))
        pygame.draw.ellipse(shadow, (100, 20, 25, 110), (12, 11, 126, 11))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_ink_puddle(surface, x, y, phase):
        """Signature red ink puddle on ground beneath boss."""
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        puddle_w = 90
        puddle_h = 24
        puddle_surf = pygame.Surface((puddle_w + 20, puddle_h + 10), pygame.SRCALPHA)
        # Main puddle body.
        pygame.draw.ellipse(puddle_surf, (*_NS_vhaerinth.PALETTE["shadow_deep"], 200),
                            (10, 5, puddle_w, puddle_h))
        pygame.draw.ellipse(puddle_surf, (*_NS_vhaerinth.PALETTE["ink_darkest"], 230),
                            (12, 6, puddle_w - 4, puddle_h - 2))
        pygame.draw.ellipse(puddle_surf, (*_NS_vhaerinth.PALETTE["ink_dark"], 210),
                            (16, 8, puddle_w - 12, puddle_h - 6))
        pygame.draw.ellipse(puddle_surf, (*_NS_vhaerinth.PALETTE["ink_mid"], _NS_vhaerinth._alpha(180 * pulse)),
                            (22, 10, puddle_w - 24, puddle_h - 10))
        # Highlight sheen.
        pygame.draw.ellipse(puddle_surf, (*_NS_vhaerinth.PALETTE["ink_light"], 150),
                            (28, 11, puddle_w - 36, 3))
        surface.blit(puddle_surf, (x - puddle_w // 2 - 10, y - puddle_h // 2 - 5))
        # Ink swirls / tendrils extending out from puddle.
        for i in range(4):
            swirl_angle = phase * 0.6 + i * (math.pi * 2 / 4)
            swirl_r = 55 + int(math.sin(phase * 1.5 + i) * 5)
            end_x = x + int(math.cos(swirl_angle) * swirl_r)
            end_y = y + int(math.sin(swirl_angle) * swirl_r * 0.35)
            # Curved tendril.
            segments = 6
            prev = (x, y)
            for k in range(1, segments + 1):
                t = k / segments
                curve = math.sin(t * math.pi) * 8
                perp = swirl_angle + math.pi / 2
                bx = int(x + (end_x - x) * t + math.cos(perp) * curve * math.sin(phase * 0.3 + i))
                by = int(y + (end_y - y) * t + math.sin(perp) * curve * math.sin(phase * 0.3 + i))
                thickness = max(1, 4 - k // 2)
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_darkest"],
                                 prev, (bx, by), thickness + 1)
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_dark"],
                                 prev, (bx, by), thickness)
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_mid"],
                                 prev, (bx, by), max(1, thickness - 1))
                prev = (bx, by)
            # Bright tip glow.
            pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_light"], (prev[0], prev[1], 1, 1))
    def _draw_ink_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_vhaerinth._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vhaerinth._aacircle(aura, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                        (120, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_vhaerinth._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vhaerinth._aacircle(aura, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                        (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_vhaerinth._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vhaerinth._aacircle(aura, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                        (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating red ink motes.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vhaerinth.PALETTE["ink_darkest"], 200),
                            (5, 19, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_vhaerinth.PALETTE["ink_dark"], 220),
                            (14, 21, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_vhaerinth.PALETTE["ink_mid"], 230),
                            (28, 23, 124, 20), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 32 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 32 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_vhaerinth.PALETTE["ink_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vhaerinth.PALETTE["ink_hot"],
                                       _NS_vhaerinth._alpha(150 * pulse)),
                                (15, 12, 150, 40), 1)
        surface.blit(ring, (x - 90, y - 28))
    def _draw_ink_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(40, 3, -3):
            alpha = _NS_vhaerinth._alpha((40 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(25, 3, -2):
            alpha = _NS_vhaerinth._alpha((25 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising ink motes.
        for i, offset in enumerate((-28, -20, -12, -4, 4, 12, 20, 28, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_vhaerinth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                    (sx, sy), 3)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha),
                             (sx, sy - 2, 1, 1))
    # ============================================================
    # RANGED ATTACK — INK PROJECTILE
    # ============================================================
    def _draw_ink_projectile(surface, boss, x, y, progress):
        """Ink blob projectile from brush tip."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_vhaerinth._target_position(boss, x, y)
        # Start from brush tip.
        start_x = x + facing * 16
        start_y = y - 30
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Ink comet trail (curving/flowing).
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            # Trail curves slightly with wave.
            wave = math.sin(t * 5 + i * 0.5) * 3
            perp_x = -(ty - start_y)
            perp_y = tx - start_x
            perp_len = max(1, math.hypot(perp_x, perp_y))
            perp_x /= perp_len
            perp_y /= perp_len
            px = int(start_x + (tx - start_x) * trail_t + perp_x * wave)
            py = int(start_y + (ty - start_y) * trail_t + perp_y * wave)
            alpha = _NS_vhaerinth._alpha(230 - i * 22)
            size = max(1, 7 - i)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                    (px, py), size)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha),
                                    (px, py), max(1, size - 3))
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Big ink blob head.
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_darkest"], (bx, by), 9)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_dark"], (bx, by), 7)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_mid"], (bx, by), 5)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_light"], (bx, by), 3)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_hot"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_shine"], (bx, by, 1, 1))
        # Radial glow.
        for r in range(13, 3, -2):
            alpha = _NS_vhaerinth._alpha(80 * (13 - r) / 13)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                    (bx, by), r)
        # Impact splash (splatter pattern).
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 22)
            alpha = _NS_vhaerinth._alpha(240 * (1 - st))
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                    (tx, ty), max(1, radius - 5), 2)
            # Splatter blobs radiating outward.
            for i in range(8):
                angle_s = i * math.pi / 4 + st * 2
                dist = int(radius * (0.8 + math.sin(i * 1.5) * 0.3))
                ex = tx + int(math.cos(angle_s) * dist)
                ey = ty + int(math.sin(angle_s) * dist * 0.7)
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                        (ex, ey), 3)
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                        (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SKILL: Q - INK TRAIL (ranged with damaging ground trail)
    # ============================================================
    def _draw_inktrail_ground(surface, boss, x, y, timer, phase):
        """Curving ink trail on ground."""
        tx, ty = _NS_vhaerinth._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.15:
            t = min(1.0, (progress - 0.15) / 0.85)
            # Trail flowing from boss to target with curve.
            segments = 16
            prev = (x, y + 44)
            for i in range(1, segments + 1):
                seg_t = min(t, i / segments)
                if seg_t <= 0:
                    break
                # Slight curve.
                curve = math.sin(seg_t * math.pi * 2 + phase) * 8
                perp_x = -(ty - y)
                perp_y = tx - x
                perp_len = max(1, math.hypot(perp_x, perp_y))
                perp_x /= perp_len
                perp_y /= perp_len
                bx = int(x + (tx - x) * seg_t + perp_x * curve)
                by = int(y + 30 + (ty - y) * seg_t + perp_y * curve)
                thickness = 6 - i // 4
                if thickness < 1:
                    thickness = 1
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                 (prev[0] + 1, prev[1] + 1),
                                 (bx + 1, by + 1), thickness + 1)
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_darkest"],
                                 prev, (bx, by), thickness)
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_dark"],
                                 prev, (bx, by), max(1, thickness - 1))
                pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_mid"],
                                 (prev[0], prev[1] - 1), (bx, by - 1), max(1, thickness - 2))
                prev = (bx, by)
    def _draw_inktrail_foreground(surface, boss, x, y, timer, phase):
        """Sparkles along ink trail path."""
        tx, ty = _NS_vhaerinth._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.2:
            t = min(1.0, (progress - 0.2) / 0.8)
            # Sparkles.
            for i in range(15):
                sp_t = (phase * 1.5 + i * 0.08) % 1.0
                if sp_t > t:
                    continue
                curve = math.sin(sp_t * math.pi * 2 + phase) * 8
                perp_x = -(ty - y)
                perp_y = tx - x
                perp_len = max(1, math.hypot(perp_x, perp_y))
                perp_x /= perp_len
                perp_y /= perp_len
                spx = int(x + (tx - x) * sp_t + perp_x * curve)
                spy = int(y + 30 + (ty - y) * sp_t + perp_y * curve)
                alpha = _NS_vhaerinth._alpha(220 * (1 - abs(t - sp_t) * 3))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha),
                                     (spx, spy - 3, 1, 1))
                    pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha),
                                     (spx, spy - 3, 1, 1))
    # ============================================================
    # SKILL: W - SOUL CHAIN (chain link to target)
    # ============================================================
    def _draw_soulchain_foreground(surface, boss, x, y, timer, phase):
        """Ink chain link from boss to target."""
        facing = boss.direction
        tx, ty = _NS_vhaerinth._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 5)
        if progress < 0.2:
            # Charge - lantern glow at hand.
            t = progress / 0.2
            hand_x = x - facing * 15
            hand_y = y - 6 + hover
            for r in range(int(10 * t), 0, -1):
                alpha = _NS_vhaerinth._alpha(200 * (10 - r) / 10 * t)
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                        (hand_x, hand_y), r)
        elif progress < 0.85:
            # Chain extending.
            t = (progress - 0.2) / 0.65
            start_x = x - facing * 15
            start_y = y - 6 + hover
            reach_x = int(start_x + (tx - start_x) * min(1.0, t * 1.5))
            reach_y = int(start_y + (ty - start_y) * min(1.0, t * 1.5))
            # Draw chain as segments.
            segments = 10
            for k in range(segments + 1):
                seg_t = k / segments
                sx = int(start_x + (reach_x - start_x) * seg_t)
                sy = int(start_y + (reach_y - start_y) * seg_t)
                # Chain link.
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["shadow_deep"],
                                 (sx - 2 + 1, sy - 2 + 1, 5, 5))
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_darkest"],
                                 (sx - 2, sy - 2, 5, 5))
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_dark"],
                                 (sx - 2, sy - 2, 5, 4))
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_mid"],
                                 (sx - 1, sy - 2, 3, 3))
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_light"],
                                 (sx - 1, sy - 2, 2, 1))
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_shine"],
                                 (sx, sy - 2, 1, 1))
            # Beam glow along chain.
            pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["ink_light"], 180),
                             (start_x, start_y), (reach_x, reach_y), 1)
            # Hook/claw at chain end.
            if t > 0.5:
                claw_x = reach_x
                claw_y = reach_y
                for r in range(8, 0, -1):
                    alpha = _NS_vhaerinth._alpha(180 * (8 - r) / 8)
                    _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                            (claw_x, claw_y), r)
                _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_mid"],
                                        (claw_x, claw_y), 4)
                _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_light"],
                                        (claw_x, claw_y), 2)
                pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_shine"],
                                 (claw_x, claw_y, 1, 1))
                # Claw spikes around impact.
                for i in range(4):
                    a = i * math.pi / 2 + phase
                    ex = claw_x + int(math.cos(a) * 8)
                    ey = claw_y + int(math.sin(a) * 8)
                    pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_dark"],
                                     (claw_x, claw_y), (ex, ey), 2)
                    pygame.draw.line(surface, _NS_vhaerinth.PALETTE["ink_light"],
                                     (claw_x, claw_y), (ex, ey), 1)
                    pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["ink_hot"], (ex, ey, 2, 2))
    # ============================================================
    # SKILL: E - PHANTASMAGORIA (summon ink illusions)
    # ============================================================
    def _draw_phantasmagoria_foreground(surface, boss, x, y, timer, phase):
        """3-4 ghostly ink illusions dancing around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 5)
        core_y = y - 4 + hover
        num_illusions = 4
        for i in range(num_illusions):
            spawn_delay = i * 0.08
            spawn_progress = max(0.0, progress - spawn_delay)
            if spawn_progress <= 0:
                continue
            rise_t = min(1.0, spawn_progress * 5)
            fade_out = min(1.0, (1 - progress) * 5)
            # Illusion orbits boss.
            orbit_angle = phase * 1.5 + i * (math.pi * 2 / num_illusions)
            orbit_r = 45
            ix = x + int(math.cos(orbit_angle) * orbit_r)
            iy_base = core_y + int(math.sin(orbit_angle) * orbit_r * 0.35)
            iy = iy_base - int(rise_t * 8)
            alpha_base = int(220 * rise_t * fade_out)
            if alpha_base <= 0:
                continue
            # Ghost body (crimson, translucent, wispy).
            _NS_vhaerinth._draw_ink_ghost(surface, ix, iy, phase + i, alpha_base)
    def _draw_ink_ghost(surface, cx, cy, phase, alpha_base):
        """Ghostly ink creature — wispy body with 2 arms/tendrils + eyes."""
        sway = math.sin(phase * 1.5) * 2
        # Body shape (wispy).
        body_pts = [
            (cx - 5, cy - 8),
            (cx - 7, cy - 4),
            (cx - 6, cy + 2),
            (cx - 8 + int(sway), cy + 8),
            (cx - 5 + int(sway), cy + 14),
            (cx + int(sway), cy + 16),
            (cx + 5 + int(sway), cy + 14),
            (cx + 8 - int(sway), cy + 8),
            (cx + 6, cy + 2),
            (cx + 7, cy - 4),
            (cx + 5, cy - 8),
            (cx + 2, cy - 10),
            (cx - 2, cy - 10),
        ]
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["ink_darkest"], body_pts,
                                  alpha_base // 2)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["ink_dark"], [
            (cx - 4, cy - 7),
            (cx - 6, cy - 3),
            (cx - 5, cy + 3),
            (cx - 6 + int(sway), cy + 9),
            (cx + int(sway), cy + 14),
            (cx + 6 - int(sway), cy + 9),
            (cx + 5, cy + 3),
            (cx + 6, cy - 3),
            (cx + 4, cy - 7),
            (cx + 1, cy - 9),
            (cx - 1, cy - 9),
        ], alpha_base * 3 // 4)
        _NS_vhaerinth._poly_alpha(surface, _NS_vhaerinth.PALETTE["ink_mid"], [
            (cx - 3, cy - 6),
            (cx - 4, cy),
            (cx - 3, cy + 5),
            (cx + int(sway), cy + 10),
            (cx + 3, cy + 5),
            (cx + 4, cy),
            (cx + 3, cy - 6),
        ], alpha_base // 2)
        # Bright core.
        _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha_base),
                                (cx, cy - 2), 3)
        _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha_base),
                                (cx, cy - 2), 2)
        # 2 tendril arms.
        for side in (-1, 1):
            arm_end_x = cx + side * 10 + int(sway * side)
            arm_end_y = cy + 4
            segments = 4
            prev = (cx + side * 4, cy - 2)
            for k in range(1, segments + 1):
                t = k / segments
                wave = math.sin(phase * 2 + k) * 2
                nx = prev[0] + side * 2 + int(wave)
                ny = prev[1] + 2
                thickness = max(1, 3 - k // 2)
                pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha_base),
                                 prev, (nx, ny), thickness)
                pygame.draw.line(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha_base),
                                 (prev[0], prev[1] - 1), (nx, ny - 1), max(1, thickness - 1))
                prev = (nx, ny)
            # Claw tip.
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha_base),
                             (prev[0], prev[1], 1, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha_base),
                             (prev[0], prev[1], 1, 1))
        # Glowing eyes.
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 4
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["shadow_deep"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_shine"], alpha_base),
                             (ex, ey, 1, 1))
        # Wispy tail dissolving at bottom.
        for i in range(3):
            wt = (phase * 2 + i * 0.3) % 1.0
            wx = cx + int(math.sin(phase + i) * 3)
            wy = cy + 16 + int(wt * 6)
            a = _NS_vhaerinth._alpha(alpha_base * (1 - wt))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], a), (wx, wy, 1, 1))
    # ============================================================
    # SKILL: R - CHAOS STORM (massive spiraling ink vortex)
    # ============================================================
    def _draw_chaosstorm_ground(surface, boss, x, y, timer, phase):
        """Concentric rings on ground."""
        tx, ty = _NS_vhaerinth._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r_max = 75
        r = int(r_max * min(1.0, progress * 3))
        if r > 5:
            for i in range(4):
                rr = r - i * 8
                if rr <= 3:
                    continue
                alpha = _NS_vhaerinth._alpha(230 - i * 45)
                pygame.draw.ellipse(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                    (tx - rr, ty - rr // 3, rr * 2, rr * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                    (tx - rr + 2, ty - rr // 3 + 1,
                                     rr * 2 - 4, rr * 2 // 3 - 2), 1)
    def _draw_chaosstorm_foreground(surface, boss, x, y, timer, phase):
        """Massive spiraling red ink vortex."""
        tx, ty = _NS_vhaerinth._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Vortex center.
        vx = tx
        vy = ty
        vortex_r = int(60 * min(1.0, progress * 3))
        if vortex_r < 5:
            return
        # Multiple spiral arms.
        num_arms = 5
        for arm_i in range(num_arms):
            arm_offset = arm_i * (math.pi * 2 / num_arms)
            for k in range(25):
                t = k / 25
                spiral_r = t * vortex_r
                spiral_angle = phase * 3 + arm_offset + t * 6
                sx = vx + int(math.cos(spiral_angle) * spiral_r)
                sy = vy + int(math.sin(spiral_angle) * spiral_r * 0.5)
                alpha = _NS_vhaerinth._alpha(240 * (1 - t * 0.5))
                size = max(1, 4 - k // 8)
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_darkest"], alpha),
                                        (sx, sy), size)
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                        (sx, sy), max(1, size - 1))
                _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_mid"], alpha),
                                        (sx, sy), max(1, size - 2))
                if k % 3 == 0:
                    pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_light"], alpha),
                                     (sx, sy, 1, 1))
                    pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha),
                                     (sx, sy, 1, 1))
        # Central bright core.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(int(15 * pulse), 0, -2):
            alpha = _NS_vhaerinth._alpha(200 * pulse * (15 - r) / 15)
            _NS_vhaerinth._aacircle(surface, (*_NS_vhaerinth.PALETTE["ink_dark"], alpha),
                                    (vx, vy), r)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_mid"], (vx, vy), 6)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_light"], (vx, vy), 4)
        _NS_vhaerinth._aacircle(surface, _NS_vhaerinth.PALETTE["ink_hot"], (vx, vy), 2)
        pygame.draw.rect(surface, _NS_vhaerinth.PALETTE["white"], (vx, vy, 1, 1))
        # Outer ring debris/sparkles.
        for i in range(20):
            angle = phase * 2 + i * math.pi / 10
            sr = vortex_r + int(math.sin(phase * 3 + i) * 5)
            sx = vx + int(math.cos(angle) * sr)
            sy = vy + int(math.sin(angle) * sr * 0.5)
            alpha = _NS_vhaerinth._alpha(220)
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_hot"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_vhaerinth.PALETTE["ink_shine"], alpha), (sx, sy, 1, 1))



# ====================================================================
# XHAROKH (VOIDBINDER) - Mini Boss
# ====================================================================

class _NS_xharokh:
    """Namespace xharokh - void warlock boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Armor / chitin (dark blue-purple with cool tint)
        "armor_darkest": (4, 3, 12),
        "armor_dark": (18, 15, 40),
        "armor_mid": (42, 35, 78),
        "armor_light": (85, 75, 135),
        "armor_edge": (140, 128, 190),
        "armor_shine": (200, 190, 235),
        # Chitin dark (like insect shell)
        "chitin_darkest": (8, 3, 20),
        "chitin_dark": (25, 12, 45),
        "chitin_mid": (55, 30, 90),
        "chitin_light": (110, 75, 155),
        # VOID PURPLE (signature magic)
        "void_darkest": (25, 3, 40),
        "void_dark": (80, 15, 110),
        "void_mid": (170, 45, 210),
        "void_light": (230, 130, 250),
        "void_hot": (250, 200, 255),
        "void_shine": (255, 240, 255),
        # Deep magenta accent
        "magenta_dark": (90, 10, 80),
        "magenta_mid": (200, 40, 175),
        "magenta_light": (255, 130, 225),
        # Skin/inner (ghostly pale void)
        "skin_dark": (35, 20, 55),
        "skin_mid": (80, 60, 110),
        "skin_light": (150, 130, 180),
        # Gold trim (subtle - ancient runes)
        "gold_dark": (55, 40, 15),
        "gold_mid": (140, 105, 40),
        "gold_light": (220, 190, 100),
        # Eye (bright magenta-white glow)
        "eye_socket": (5, 0, 8),
        "eye_dark": (100, 15, 130),
        "eye_mid": (220, 60, 240),
        "eye_light": (255, 180, 255),
        # Staff bone / handle
        "bone_dark": (40, 30, 50),
        "bone_mid": (100, 85, 120),
        "bone_light": (180, 165, 200),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xharokh._clamp(color)
        if _NS_xharokh.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xharokh._clamp(color)
        if _NS_xharokh.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xharokh._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xharokh(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_xharokh._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xhr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_xharokh._draw_void_aura(surface, x, y, pulse)
        _NS_xharokh._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "q":
            _NS_xharokh._draw_spawn_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xharokh._draw_shifting_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xharokh._draw_domain_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — special for E teleport.
        if active_skill == "e" and 15 < skill_timer < 55:
            _NS_xharokh._draw_xhr_shift_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_xharokh._draw_xhr_attack(surface, boss, x, y)
        else:
            _NS_xharokh._draw_xhr_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_xharokh._draw_spawn_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xharokh._draw_voidspines_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xharokh._draw_shifting_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xharokh._draw_domain_foreground(surface, boss, x, y, skill_timer, pulse)
        # Passive spore particles (always visible - signature).
        _NS_xharokh._draw_spore_particles(surface, x, y, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xhr_previous_timer", 0))
        active = bool(getattr(boss, "_xhr_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._xhr_attack_active = True
            boss._xhr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xhr_attack_frame = int(getattr(boss, "_xhr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._xhr_attack_active = False
            boss._xhr_attack_frame = 0
            active = False
        boss._xhr_previous_timer = timer
        boss._xhr_attack_progress = (
            min(1.0, getattr(boss, "_xhr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_xhr_float(surface, boss, x, y):
        """Idle: floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.5) * 6)
        _NS_xharokh._draw_shadow(surface, x, y + 54)
        _NS_xharokh._draw_void_wisps(surface, x, y + 25, boss.pulse)
        _NS_xharokh._draw_xhr_body(surface, x, y - 6 + hover,
                                   boss.direction, boss.pulse, "float", 0)
    def _draw_xhr_attack(surface, boss, x, y):
        """Attack: cast pose - raise staff, void bolt projectile."""
        progress = getattr(boss, "_xhr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.5) * 6)
        lean = 0
        lift = 0
        if progress < 0.35:
            t = progress / 0.35
            lean = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 8)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_xharokh._draw_shadow(surface, x + lean, y + 54)
        _NS_xharokh._draw_void_wisps(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_xharokh._draw_xhr_body(surface, x + lean, y - 6 + hover - lift,
                                   boss.direction, boss.pulse, "attack", progress)
        # Void bolt projectile from staff orb.
        _NS_xharokh._draw_void_bolt_projectile(surface, boss, x + lean, y - 6 + hover - lift,
                                               progress)
    def _draw_xhr_shift_body(surface, boss, x, y, skill_timer, pulse):
        """During E shift: boss vanishes into void, reappears at target."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.5) * 6)
        if progress < 0.35:
            # Fade out phase — dissolve into void portal.
            t = progress / 0.35
            alpha_scale = 1.0 - t
            _NS_xharokh._draw_shadow(surface, x, y + 54)
            # Ghost body.
            ghost_surf = pygame.Surface((130, 160), pygame.SRCALPHA)
            _NS_xharokh._draw_xhr_body_to(ghost_surf, 65, 80 + hover,
                                          boss.direction, pulse, "float", 0,
                                          alpha_scale)
            surface.blit(ghost_surf, (x - 65, y - 80))
        elif progress < 0.65:
            # In-void phase — no body, just portal effects (drawn by foreground FX).
            pass
        else:
            # Reappear at target.
            t = (progress - 0.65) / 0.35
            alpha_scale = t
            tx, ty = _NS_xharokh._target_position(boss, x, y)
            _NS_xharokh._draw_shadow(surface, tx, ty + 54)
            ghost_surf = pygame.Surface((130, 160), pygame.SRCALPHA)
            _NS_xharokh._draw_xhr_body_to(ghost_surf, 65, 80 + hover,
                                          -boss.direction, pulse, "float", 0,
                                          alpha_scale)
            surface.blit(ghost_surf, (tx - 65, ty - 80))
    # ============================================================
    # BODY
    # ============================================================
    def _draw_xhr_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_xharokh._draw_xhr_body_to(surface, cx, cy, facing, phase, action,
                                      attack_progress, 1.0)
    def _draw_xhr_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Void warlock body — chitinous armor, spiky crown, void staff."""
        # Robe/cape trail behind (chitinous flowing shards).
        _NS_xharokh._draw_shard_cape(surface, cx, cy + 6, facing, phase, alpha_scale)
        # Legs (chitinous armor legs).
        _NS_xharokh._draw_xhr_legs(surface, cx, cy + 12, facing, phase, alpha_scale)
        # Torso (armor plate).
        _NS_xharokh._draw_xhr_torso(surface, cx, cy, facing, phase, alpha_scale)
        # Shoulder chitin plates (big spikes).
        _NS_xharokh._draw_xhr_pauldrons(surface, cx, cy - 6, facing, phase, alpha_scale)
        # Arms + staff.
        _NS_xharokh._draw_xhr_arms(surface, cx, cy, facing, phase, action,
                                   attack_progress, alpha_scale)
        # Head + crown horns + face.
        _NS_xharokh._draw_xhr_head(surface, cx, cy - 24, facing, phase, alpha_scale)
    def _draw_shard_cape(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Trailing chitinous shards behind body (like ghost tail with sharp blades)."""
        alpha_base = int(255 * alpha_scale)
        # Multiple shard tails.
        num_shards = 5
        for i in range(num_shards):
            t = i / (num_shards - 1)
            sway = math.sin(phase * 0.9 + i * 0.4) * (2 + i * 0.5)
            offset_x = -8 + i * 4  # spread
            # Shard tip position.
            base_x = cx + offset_x
            base_y = cy + int(i * 3)
            tip_x = base_x + int(sway)
            tip_y = base_y + int(15 + i * 4)
            # Shard triangle shape.
            perp = math.pi / 2
            side_off = 3
            side_a = (base_x - int(math.cos(perp) * side_off),
                      base_y + int(math.sin(perp) * side_off))
            side_b = (base_x + int(math.cos(perp) * side_off),
                      base_y - int(math.sin(perp) * side_off))
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (side_a[0] + 1, side_a[1] + 1),
                (side_b[0] + 1, side_b[1] + 1),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"],
                                    [(tip_x, tip_y), side_a, side_b], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_dark"], [
                (tip_x, tip_y),
                (int((tip_x + side_a[0]) / 2), int((tip_y + side_a[1]) / 2)),
                (int((tip_x + side_b[0]) / 2), int((tip_y + side_b[1]) / 2)),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_mid"], [
                (tip_x, tip_y),
                (int((tip_x + side_a[0]) / 2 + 1), int((tip_y + side_a[1]) / 2)),
                (base_x, base_y),
            ], alpha_base)
            # Purple tip glow.
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                             (tip_x, tip_y, 1, 1))
    def _draw_xhr_legs(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Armored chitinous legs."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.6) * 1
        for side in (-1, 1):
            hip_x = cx + side * 6
            hip_y = cy
            knee_x = cx + side * 7 + int(sway * 0.5)
            knee_y = cy + 12
            foot_x = cx + side * 5 + int(sway)
            foot_y = cy + 22
            # Thigh (dark chitin).
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                      (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1),
                                      6, alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"],
                                      (hip_x, hip_y), (knee_x, knee_y), 5, alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_dark"],
                                      (hip_x, hip_y), (knee_x, knee_y), 4, alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_mid"],
                                      (hip_x, hip_y - 1), (knee_x, knee_y - 1), 2,
                                      alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_edge"],
                                      (hip_x - side, hip_y - 2), (knee_x - side, knee_y - 2),
                                      1, alpha_base)
            # Knee spike (chitin).
            spike_tip_x = knee_x + side * 4
            spike_tip_y = knee_y - 2
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                (spike_tip_x, spike_tip_y),
                (knee_x, knee_y - 2),
                (knee_x, knee_y + 2),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_mid"], [
                (spike_tip_x, spike_tip_y),
                (knee_x + side, knee_y - 1),
                (knee_x + side, knee_y + 1),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                             (spike_tip_x, spike_tip_y, 1, 1))
            # Shin (armored).
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                      (knee_x + 1, knee_y + 1), (foot_x + 1, foot_y + 1),
                                      5, alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"],
                                      (knee_x, knee_y), (foot_x, foot_y), 4, alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_dark"],
                                      (knee_x, knee_y), (foot_x, foot_y), 3, alpha_base)
            _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_mid"],
                                      (knee_x - side, knee_y), (foot_x - side, foot_y), 1,
                                      alpha_base)
            # Foot / boot claw (pointed).
            foot_pts = [
                (foot_x - 4, foot_y),
                (foot_x + 4, foot_y),
                (foot_x + 5, foot_y + 3),
                (foot_x - 5, foot_y + 3),
            ]
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                    [(p[0] + 1, p[1] + 1) for p in foot_pts], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], foot_pts,
                                    alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_dark"], [
                (foot_x - 3, foot_y + 1),
                (foot_x + 3, foot_y + 1),
                (foot_x + 4, foot_y + 2),
                (foot_x - 4, foot_y + 2),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                             (foot_x - 2, foot_y + 1, 4, 1))
            # Claw tips.
            for claw_off in (-4, 0, 4):
                pygame.draw.line(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                                 (foot_x + claw_off, foot_y + 3),
                                 (foot_x + claw_off, foot_y + 5), 1)
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha_base),
                                 (foot_x + claw_off, foot_y + 5, 1, 1))
    def _draw_xhr_torso(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Chitinous armor torso with void gem in center."""
        alpha_base = int(255 * alpha_scale)
        # Torso shape (V-shaped, muscular).
        torso_pts = [
            (cx - 11, cy - 10),
            (cx - 13, cy - 4),
            (cx - 10, cy + 2),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 10, cy + 2),
            (cx + 13, cy - 4),
            (cx + 11, cy - 10),
            (cx + 5, cy - 13),
            (cx - 5, cy - 13),
        ]
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], torso_pts,
                                alpha_base, offset=(2, 2))
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"], torso_pts,
                                alpha_base)
        # Armor mid tone.
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_dark"], [
            (cx - 10, cy - 9),
            (cx - 12, cy - 3),
            (cx - 9, cy + 2),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 9, cy + 2),
            (cx + 12, cy - 3),
            (cx + 10, cy - 9),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ], alpha_base)
        # Chitin plates (segmented).
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_dark"], [
            (cx - 8, cy - 8),
            (cx - 10, cy - 3),
            (cx - 7, cy + 2),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 2),
            (cx + 10, cy - 3),
            (cx + 8, cy - 8),
            (cx + 3, cy - 10),
            (cx - 3, cy - 10),
        ], alpha_base)
        # Segmented plate lines (chitinous ridge).
        for y_off, x_span in [(-6, 6), (-2, 7), (3, 6), (7, 4)]:
            py = cy + y_off
            pygame.draw.line(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                             (cx - x_span, py), (cx + x_span, py), 1)
            pygame.draw.line(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                             (cx - x_span + 1, py - 1), (cx + x_span - 1, py - 1), 1)
        # V-shape center chest ridge.
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_mid"], [
            (cx, cy - 10),
            (cx - 3, cy),
            (cx, cy + 5),
            (cx + 3, cy),
        ], alpha_base)
        # VOID GEM in center chest (large glowing).
        gem_y = cy - 2
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(8, 0, -1):
            alpha = _NS_xharokh._alpha(180 * (8 - r) / 8 * pulse * alpha_scale)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                  (cx, gem_y), r)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha_base),
                              (cx, gem_y), 4)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha_base),
                              (cx, gem_y), 3)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                              (cx, gem_y), 2)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_hot"], alpha_base),
                              (cx, gem_y), 1)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                         (cx, gem_y, 1, 1))
        # Highlight edges (armor light).
        pygame.draw.line(surface, (*_NS_xharokh.PALETTE["armor_light"], alpha_base),
                         (cx - 11, cy - 10), (cx - 13, cy - 4), 1)
        pygame.draw.line(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                         (cx + 11, cy - 10), (cx + 13, cy - 4), 1)
        # Ridge spikes on collarbone/chest edge.
        for spike_x in (-7, -3, 3, 7):
            sx = cx + spike_x
            sy_base = cy - 10
            sy_tip = sy_base - 2
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                (sx, sy_tip), (sx - 1, sy_base), (sx + 1, sy_base),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                             (sx, sy_tip, 1, 1))
    def _draw_xhr_pauldrons(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Big spiky chitin pauldrons with multiple spikes."""
        alpha_base = int(255 * alpha_scale)
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 12
            base_y = cy
            # Pauldron base shape.
            pad_pts = [
                (base_x, base_y - 4),
                (base_x + side * 6, base_y - 6),
                (base_x + side * 10, base_y - 2),
                (base_x + side * 11, base_y + 4),
                (base_x + side * 6, base_y + 7),
                (base_x + side * 1, base_y + 6),
            ]
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], pad_pts,
                                    alpha_base, offset=(2, 2))
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"], pad_pts,
                                    alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_dark"], [
                (base_x + side * 1, base_y - 3),
                (base_x + side * 5, base_y - 5),
                (base_x + side * 9, base_y - 1),
                (base_x + side * 10, base_y + 3),
                (base_x + side * 6, base_y + 6),
                (base_x + side * 2, base_y + 5),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_mid"], [
                (base_x + side * 2, base_y - 2),
                (base_x + side * 4, base_y - 4),
                (base_x + side * 7, base_y),
                (base_x + side * 6, base_y + 3),
                (base_x + side * 3, base_y + 4),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_light"], alpha_base),
                             (base_x + side * 3, base_y - 3, 2, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                             (base_x + side * 4, base_y - 4, 1, 1))
            # 2 SPIKES on top of pauldron (chitin).
            for spike_i, (spike_off_x, spike_tip_off_x, spike_tip_off_y) in enumerate([
                (3, 4, -9),
                (7, 8, -11),
            ]):
                spike_base_x = base_x + side * spike_off_x
                spike_base_y = base_y - 5
                spike_tip_x = base_x + side * spike_tip_off_x
                spike_tip_y = base_y + spike_tip_off_y
                _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], [
                    (spike_tip_x + 1, spike_tip_y + 1),
                    (spike_base_x - 2 + 1, spike_base_y + 1),
                    (spike_base_x + 2 + 1, spike_base_y + 1),
                ], alpha_base)
                _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x - 2, spike_base_y),
                    (spike_base_x + 2, spike_base_y),
                ], alpha_base)
                _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_dark"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x - 1, spike_base_y),
                    (spike_base_x + 1, spike_base_y),
                ], alpha_base)
                _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_mid"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x, spike_base_y - 1),
                    (spike_base_x + 1, spike_base_y),
                ], alpha_base)
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                                 (spike_tip_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                                 (spike_tip_x, spike_tip_y, 1, 1))
            # VOID GEM on pauldron.
            gem_x = base_x + side * 5
            gem_y = base_y + 2
            pulse = math.sin(phase * 2 + side_i) * 0.3 + 0.7
            for r in range(4, 0, -1):
                alpha = _NS_xharokh._alpha(150 * pulse * (4 - r) / 4 * alpha_scale)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (gem_x, gem_y), r)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha_base),
                             (gem_x - 1, gem_y - 1, 3, 2))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                             (gem_x, gem_y - 1, 2, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                             (gem_x, gem_y - 1, 1, 1))
    def _draw_xhr_arms(surface, cx, cy, facing, phase, action, attack_progress,
                       alpha_scale=1.0):
        """Two arms — front holds staff, other is claw."""
        alpha_base = int(255 * alpha_scale)
        # RIGHT arm (facing side) holds staff.
        staff_side = facing
        arm_r_base_x = cx + staff_side * 11
        arm_r_base_y = cy - 5
        # Arm angle changes in attack.
        raise_amount = 0
        if action == "attack":
            if attack_progress < 0.35:
                raise_amount = int(attack_progress / 0.35 * 10)
            elif attack_progress < 0.6:
                raise_amount = int(10 - (attack_progress - 0.35) / 0.25 * 15)
            else:
                raise_amount = int(-5 + (attack_progress - 0.6) / 0.4 * 5)
        hand_r_x = arm_r_base_x + staff_side * 4
        hand_r_y = arm_r_base_y + 8 - raise_amount
        elbow_r_x = arm_r_base_x + staff_side * 2
        elbow_r_y = arm_r_base_y + 3 - raise_amount // 2
        # Draw right arm (armored).
        _NS_xharokh._draw_arm_segment(surface,
                                      (arm_r_base_x, arm_r_base_y),
                                      (elbow_r_x, elbow_r_y),
                                      (hand_r_x, hand_r_y), alpha_base)
        # LEFT arm (opposite).
        opp_side = -facing
        arm_l_base_x = cx + opp_side * 11
        arm_l_base_y = cy - 5
        sway = math.sin(phase * 0.6) * 1
        hand_l_x = arm_l_base_x + opp_side * 7 + int(sway)
        hand_l_y = arm_l_base_y + 12
        elbow_l_x = arm_l_base_x + opp_side * 4
        elbow_l_y = arm_l_base_y + 6
        _NS_xharokh._draw_arm_segment(surface,
                                      (arm_l_base_x, arm_l_base_y),
                                      (elbow_l_x, elbow_l_y),
                                      (hand_l_x, hand_l_y), alpha_base)
        # Left hand claw with void energy.
        _NS_xharokh._draw_void_claw(surface, hand_l_x, hand_l_y, phase, alpha_base,
                                    intense=(action == "attack"))
        # STAFF held in right hand.
        _NS_xharokh._draw_void_staff(surface, hand_r_x, hand_r_y, staff_side, phase,
                                     action, attack_progress, alpha_base)
    def _draw_arm_segment(surface, base, elbow, hand, alpha_base):
        """Armored arm from shoulder to hand."""
        # Upper arm.
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                  (base[0] + 1, base[1] + 1),
                                  (elbow[0] + 1, elbow[1] + 1), 5, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"],
                                  base, elbow, 4, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_dark"],
                                  base, elbow, 3, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_mid"],
                                  (base[0], base[1] - 1), (elbow[0], elbow[1] - 1), 1,
                                  alpha_base)
        # Elbow joint (spiky armor).
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                              (elbow[0], elbow[1]), 3)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["chitin_dark"], alpha_base),
                              (elbow[0], elbow[1]), 2)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                         (elbow[0], elbow[1] - 1, 1, 1))
        # Forearm.
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                  (elbow[0] + 1, elbow[1] + 1),
                                  (hand[0] + 1, hand[1] + 1), 5, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"],
                                  elbow, hand, 4, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_dark"],
                                  elbow, hand, 3, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_mid"],
                                  (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 1,
                                  alpha_base)
    def _draw_void_claw(surface, hx, hy, phase, alpha_base, intense=False):
        """Claw hand with void energy."""
        # Hand base.
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["shadow_deep"], alpha_base),
                              (hx + 1, hy + 1), 3)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                              (hx, hy), 3)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["chitin_dark"], alpha_base),
                              (hx, hy), 2)
        # Claw fingers (3 short spikes).
        for finger_angle in (-0.6, 0, 0.6):
            fx = hx + int(math.cos(math.pi / 2 + finger_angle) * 4)
            fy = hy + int(math.sin(math.pi / 2 + finger_angle) * 4)
            pygame.draw.line(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                             (hx, hy), (fx, fy), 2)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["chitin_mid"], alpha_base),
                             (fx, fy, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                             (fx, fy, 1, 1))
        # Void energy in palm.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        strength = 1.5 if intense else 1.0
        for r in range(5, 0, -1):
            alpha = _NS_xharokh._alpha(140 * (5 - r) / 5 * pulse * strength * alpha_base / 255)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                  (hx, hy - 3), r)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha_base),
                              (hx, hy - 3), 2)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                         (hx, hy - 4, 1, 1))
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                         (hx, hy - 4, 1, 1))
    def _draw_void_staff(surface, hx, hy, side, phase, action, attack_progress, alpha_base):
        """Long ornate staff with void orb on top."""
        # Staff extends up.
        staff_top_x = hx + side * 2
        staff_top_y = hy - 30
        staff_bot_x = hx - side * 1
        staff_bot_y = hy + 12
        # Shadow.
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                  (staff_top_x + 2, staff_top_y + 2),
                                  (staff_bot_x + 2, staff_bot_y + 2), 4, alpha_base)
        # Staff shaft.
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["bone_dark"],
                                  (staff_top_x, staff_top_y),
                                  (staff_bot_x, staff_bot_y), 3, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"],
                                  (staff_top_x, staff_top_y),
                                  (staff_bot_x, staff_bot_y), 2, alpha_base)
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_dark"],
                                  (staff_top_x, staff_top_y),
                                  (staff_bot_x, staff_bot_y), 1, alpha_base)
        # Highlight.
        _NS_xharokh._aaline_alpha(surface, _NS_xharokh.PALETTE["armor_mid"],
                                  (staff_top_x - side, staff_top_y),
                                  (staff_bot_x - side, staff_bot_y), 1, alpha_base)
        # Chain wraps along staff (decorative).
        for wy in range(staff_top_y + 8, staff_bot_y - 2, 8):
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                             (staff_top_x - 2, wy, 4, 2))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["chitin_mid"], alpha_base),
                             (staff_top_x - 1, wy, 2, 1))
        # ORNATE TOP - void orb with pointed chitin cage.
        orb_x = staff_top_x
        orb_y = staff_top_y - 4
        # Void orb glow halo.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        strength = 1.6 if action == "attack" else 1.0
        for r in range(int(15 * strength), 0, -1):
            alpha = _NS_xharokh._alpha(150 * pulse * strength * (15 - r) / 15 * alpha_base / 255)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                  (orb_x, orb_y), r)
        # Chitin cage (2 curved spikes flanking orb).
        for cage_side in (-1, 1):
            cage_tip_x = orb_x + cage_side * 5
            cage_tip_y = orb_y - 5
            cage_base_x = orb_x + cage_side * 3
            cage_base_y = orb_y + 3
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], [
                (cage_tip_x + 1, cage_tip_y + 1),
                (cage_base_x + 1, cage_base_y + 1),
                (orb_x + 1, orb_y + 4),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                (cage_tip_x, cage_tip_y),
                (cage_base_x, cage_base_y),
                (orb_x, orb_y + 3),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_dark"], [
                (cage_tip_x, cage_tip_y),
                (int((cage_tip_x + cage_base_x) / 2), int((cage_tip_y + cage_base_y) / 2)),
                (orb_x, orb_y + 2),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["chitin_light"], alpha_base),
                             (cage_tip_x, cage_tip_y, 1, 1))
        # Central void orb.
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["shadow_deep"], alpha_base),
                              (orb_x, orb_y), 5)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha_base),
                              (orb_x, orb_y), 4)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha_base),
                              (orb_x, orb_y), 3)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha_base),
                              (orb_x, orb_y), 2)
        _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                              (orb_x, orb_y), 1)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                         (orb_x, orb_y, 1, 1))
        # Sparkles rising from orb.
        for i in range(3):
            sp_t = (phase * 1.5 + i * 0.3) % 1.0
            sx = orb_x + int(math.sin(phase * 3 + i) * 2)
            sy = orb_y - int(sp_t * 8)
            alpha = _NS_xharokh._alpha(200 * (1 - sp_t) * alpha_base / 255)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha),
                             (sx, sy, 1, 1))
        # Staff bottom cap (pointed).
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
            (staff_bot_x - 2, staff_bot_y - 2),
            (staff_bot_x + 2, staff_bot_y - 2),
            (staff_bot_x, staff_bot_y + 3),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["chitin_mid"], alpha_base),
                         (staff_bot_x, staff_bot_y - 1, 1, 1))
    def _draw_xhr_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Head with tall spiky crown horns + glowing purple eyes."""
        alpha_base = int(255 * alpha_scale)
        # Head shape (helmet-like, angular).
        head_pts = [
            (cx - 7, cy),
            (cx - 8, cy + 5),
            (cx - 7, cy + 10),
            (cx - 3, cy + 13),
            (cx + 3, cy + 13),
            (cx + 7, cy + 10),
            (cx + 8, cy + 5),
            (cx + 7, cy),
            (cx + 4, cy - 2),
            (cx - 4, cy - 2),
        ]
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], head_pts,
                                alpha_base, offset=(2, 2))
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_darkest"], head_pts,
                                alpha_base)
        # Helmet mid tone.
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["armor_dark"], [
            (cx - 6, cy + 1),
            (cx - 7, cy + 5),
            (cx - 6, cy + 9),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 6, cy + 9),
            (cx + 7, cy + 5),
            (cx + 6, cy + 1),
            (cx + 3, cy - 1),
            (cx - 3, cy - 1),
        ], alpha_base)
        # Face plate (chitin darker, showing "face").
        _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_dark"], [
            (cx - 4, cy + 3),
            (cx - 5, cy + 8),
            (cx - 2, cy + 12),
            (cx + 2, cy + 12),
            (cx + 5, cy + 8),
            (cx + 4, cy + 3),
        ], alpha_base)
        # Highlight on helmet top edges.
        pygame.draw.line(surface, (*_NS_xharokh.PALETTE["armor_light"], alpha_base),
                         (cx - 4, cy - 1), (cx + 4, cy - 1), 1)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                         (cx - 2, cy - 1, 4, 1))
        # Central helmet ridge.
        pygame.draw.line(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                         (cx, cy - 1), (cx, cy + 12), 1)
        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["armor_edge"], alpha_base),
                         (cx, cy + 5, 1, 1))
        # SPIKY CROWN HORNS (multiple tall spikes on head).
        _NS_xharokh._draw_crown_horns(surface, cx, cy - 2, phase, alpha_base)
        # GLOWING PURPLE EYES.
        _NS_xharokh._draw_void_eyes(surface, cx, cy + 6, phase, alpha_scale)
        # Chin plate detail.
        pygame.draw.line(surface, (*_NS_xharokh.PALETTE["chitin_darkest"], alpha_base),
                         (cx - 2, cy + 12), (cx + 2, cy + 12), 1)
    def _draw_crown_horns(surface, cx, cy, phase, alpha_base):
        """Tall spiky crown horns like reference image."""
        # Central big horn + 2 side horns + 2 outer horns.
        sway = math.sin(phase * 0.3) * 1
        horn_specs = [
            # (base_x_offset, tip_x_offset, tip_y_offset, width)
            (-8, -10, -8, 3),   # far left
            (-5, -6, -14, 3),   # left tall
            (-2, -2, -17, 3),   # inner left tallest
            (2, 2, -17, 3),     # inner right tallest
            (5, 6, -14, 3),     # right tall
            (8, 10, -8, 3),     # far right
        ]
        for spec_i, (base_off_x, tip_off_x, tip_off_y, width) in enumerate(horn_specs):
            base_x = cx + base_off_x
            base_y = cy
            tip_x = cx + tip_off_x + int(sway * (1 if base_off_x > 0 else -1))
            tip_y = cy + tip_off_y
            # Shadow.
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x - width + 1, base_y + 1),
                (base_x + width + 1, base_y + 1),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                (tip_x, tip_y),
                (base_x - width, base_y),
                (base_x + width, base_y),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_dark"], [
                (tip_x, tip_y),
                (base_x - width + 1, base_y),
                (base_x + width - 1, base_y),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_mid"], [
                (tip_x, tip_y),
                (base_x, base_y - 1),
                (base_x + width - 1, base_y),
            ], alpha_base)
            _NS_xharokh._poly_alpha(surface, _NS_xharokh.PALETTE["chitin_light"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x + 1, base_y - 1),
            ], alpha_base)
            # Bright tip glow.
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                             (tip_x, tip_y, 1, 1))
            # Small void glow at tip (halo).
            for r in range(3, 0, -1):
                alpha = _NS_xharokh._alpha(120 * (3 - r) / 3 * alpha_base / 255)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                      (tip_x, tip_y), r)
    def _draw_void_eyes(surface, cx, cy, phase, alpha_scale=1.0):
        """Bright glowing purple eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            # Halo.
            for r in range(6, 0, -1):
                a = _NS_xharokh._alpha(140 * (6 - r) / 6 * pulse * alpha_scale)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], a),
                                      (ex, ey), r)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha_base),
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha_base),
                             (ex, ey, 1, 1))
    # ============================================================
    # HELPERS
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_xharokh._poly(surface, color, points)
            return
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_xharokh._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_xharokh._aaline(surface, color, start, end, width)
            return
        c = _NS_xharokh._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 16 - radius, 126 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 12, 170), (5, 9, 140, 15))
        pygame.draw.ellipse(shadow, (60, 15, 90, 110), (12, 11, 126, 11))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_void_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_xharokh._alpha((100 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_xharokh._aacircle(aura, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                                      (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_xharokh._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xharokh._aacircle(aura, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_xharokh._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xharokh._aacircle(aura, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                      (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xharokh.PALETTE["void_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_xharokh.PALETTE["void_dark"], 220),
                            (16, 22, 158, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_xharokh.PALETTE["void_mid"], 230),
                            (30, 24, 130, 22), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 35 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_xharokh.PALETTE["void_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_xharokh.PALETTE["void_hot"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_xharokh.PALETTE["void_hot"],
                                       _NS_xharokh._alpha(150 * pulse)),
                                (16, 12, 158, 40), 1)
        surface.blit(ring, (x - 95, y - 30))
    def _draw_void_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(40, 3, -3):
            alpha = _NS_xharokh._alpha((40 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(25, 3, -2):
            alpha = _NS_xharokh._alpha((25 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising void motes.
        for i, offset in enumerate((-28, -20, -12, -4, 4, 12, 20, 28, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_xharokh._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                  (sx, sy), 3)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                  (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_hot"], alpha),
                             (sx, sy - 2, 1, 1))
    def _draw_spore_particles(surface, x, y, phase):
        """Passive spore particles orbiting boss (Spores of Destruction theme)."""
        for i in range(5):
            spore_angle = phase * 0.6 + i * (math.pi * 2 / 5)
            spore_r = 55 + int(math.sin(phase * 1.2 + i) * 8)
            sx = x + int(math.cos(spore_angle) * spore_r)
            sy = y - 10 + int(math.sin(spore_angle) * spore_r * 0.45)
            pulse = math.sin(phase * 3 + i) * 0.3 + 0.7
            # Spore body (small ball with glow).
            for r in range(4, 0, -1):
                alpha = _NS_xharokh._alpha(150 * pulse * (4 - r) / 4)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (sx, sy), r)
            _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_mid"], (sx, sy), 2)
            _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_light"], (sx, sy), 1)
            pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_shine"], (sx, sy, 1, 1))
    # ============================================================
    # RANGED ATTACK — VOID BOLT PROJECTILE
    # ============================================================
    def _draw_void_bolt_projectile(surface, boss, x, y, progress):
        """Purple void bolt from staff orb."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_xharokh._target_position(boss, x, y)
        # Start from staff top (approximate).
        start_x = x + facing * 15
        start_y = y - 24
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail.
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_xharokh._alpha(230 - i * 22)
            size = max(1, 7 - i)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                                  (px, py), size)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                  (px, py), max(1, size - 2))
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                  (px, py), max(1, size - 3))
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright bolt head.
        _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_darkest"], (bx, by), 8)
        _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_dark"], (bx, by), 6)
        _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_mid"], (bx, by), 4)
        _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_light"], (bx, by), 3)
        _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_hot"], (bx, by), 2)
        _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_xharokh.PALETTE["white"], (bx, by, 1, 1))
        # Radial glow.
        for r in range(12, 3, -2):
            alpha = _NS_xharokh._alpha(80 * (12 - r) / 12)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                  (bx, by), r)
        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 24)
            alpha = _NS_xharokh._alpha(240 * (1 - st))
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                                  (tx, ty), radius + 3, 3)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                  (tx, ty), max(1, radius - 4), 2)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                  (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SKILL: Q - NIGHTMARIC SPAWN (summon creature)
    # ============================================================
    def _draw_spawn_ground(surface, boss, x, y, timer, phase):
        """Purple summoning circle at target."""
        tx, ty = _NS_xharokh._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r_max = 30
        r = int(r_max * min(1.0, progress * 3))
        if r > 3:
            for i in range(3):
                rr = r - i * 4
                if rr <= 2:
                    continue
                alpha = _NS_xharokh._alpha(200 - i * 45)
                pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                                    (tx - rr, ty - rr // 3, rr * 2, rr * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                    (tx - rr + 2, ty - rr // 3 + 1,
                                     rr * 2 - 4, rr * 2 // 3 - 2), 1)
            # Runes.
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                rx = tx + int(math.cos(angle) * r)
                ry = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_hot"], (rx, ry, 2, 2))
    def _draw_spawn_foreground(surface, boss, x, y, timer, phase):
        """Nightmaric spawn creature rising from ground."""
        tx, ty = _NS_xharokh._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Portal charging.
            t = progress / 0.2
            for r in range(int(12 * t), 0, -2):
                alpha = _NS_xharokh._alpha(200 * (12 - r) / 12)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (tx, ty), r)
            _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_mid"], (tx, ty), 4)
            _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_light"], (tx, ty), 2)
        elif progress < 0.65:
            # Spawn creature rising up (small void beast).
            t = (progress - 0.2) / 0.45
            spawn_h = int(t * 20)
            spawn_y = ty - spawn_h
            spawn_x = tx
            # Body (small crescent shape with horns).
            body_pts = [
                (spawn_x - 5, spawn_y + 4),
                (spawn_x - 6, spawn_y),
                (spawn_x - 3, spawn_y - 3),
                (spawn_x + 3, spawn_y - 3),
                (spawn_x + 6, spawn_y),
                (spawn_x + 5, spawn_y + 4),
            ]
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in body_pts])
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_darkest"], body_pts)
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_dark"], [
                (spawn_x - 4, spawn_y + 3),
                (spawn_x - 5, spawn_y),
                (spawn_x - 2, spawn_y - 2),
                (spawn_x + 2, spawn_y - 2),
                (spawn_x + 5, spawn_y),
                (spawn_x + 4, spawn_y + 3),
            ])
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_mid"], [
                (spawn_x - 2, spawn_y - 1),
                (spawn_x + 2, spawn_y - 1),
                (spawn_x + 1, spawn_y + 1),
                (spawn_x - 1, spawn_y + 1),
            ])
            # 2 horn spikes on top.
            for side in (-1, 1):
                htip_x = spawn_x + side * 5
                htip_y = spawn_y - 6
                hbase_x = spawn_x + side * 2
                hbase_y = spawn_y - 3
                _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                    (htip_x, htip_y),
                    (hbase_x - 1, hbase_y),
                    (hbase_x + 1, hbase_y),
                ])
                pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_light"],
                                 (htip_x, htip_y, 1, 1))
            # Central eye (glowing purple).
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            for r in range(3, 0, -1):
                alpha = _NS_xharokh._alpha(200 * pulse * (3 - r) / 3)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                      (spawn_x, spawn_y), r)
            pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_light"], (spawn_x, spawn_y, 1, 1))
            pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_shine"], (spawn_x, spawn_y, 1, 1))
            # Rising portal energy.
            for i in range(6):
                sp_t = (phase * 1.5 + i * 0.17) % 1.0
                sx = tx + int(math.sin(phase * 3 + i) * 6)
                sy = ty - int(sp_t * 15)
                alpha = _NS_xharokh._alpha(200 * (1 - sp_t))
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                 (sx, sy, 1, 1))
        else:
            # Full spawn — stay + shoot small void bolt.
            t = (progress - 0.65) / 0.35
            spawn_y = ty - 20
            spawn_x = tx
            # Same body as before.
            body_pts = [
                (spawn_x - 5, spawn_y + 4),
                (spawn_x - 6, spawn_y),
                (spawn_x - 3, spawn_y - 3),
                (spawn_x + 3, spawn_y - 3),
                (spawn_x + 6, spawn_y),
                (spawn_x + 5, spawn_y + 4),
            ]
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_darkest"], body_pts)
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_dark"], [
                (spawn_x - 4, spawn_y + 3),
                (spawn_x - 5, spawn_y),
                (spawn_x - 2, spawn_y - 2),
                (spawn_x + 2, spawn_y - 2),
                (spawn_x + 5, spawn_y),
                (spawn_x + 4, spawn_y + 3),
            ])
            for side in (-1, 1):
                htip_x = spawn_x + side * 5
                htip_y = spawn_y - 6
                _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["chitin_darkest"], [
                    (htip_x, htip_y),
                    (spawn_x + side * 2 - 1, spawn_y - 3),
                    (spawn_x + side * 2 + 1, spawn_y - 3),
                ])
                pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_light"], (htip_x, htip_y, 1, 1))
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            for r in range(4, 0, -1):
                alpha = _NS_xharokh._alpha(220 * pulse * (4 - r) / 4)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                      (spawn_x, spawn_y), r)
            pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_shine"], (spawn_x, spawn_y, 1, 1))
    # ============================================================
    # SKILL: W - VOID SPINES (spread projectile)
    # ============================================================
    def _draw_voidspines_foreground(surface, boss, x, y, timer, phase):
        """Multiple purple energy spines fired forward in a spread pattern."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xharokh._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.5) * 6)
        if progress < 0.2:
            # Charge in front hand/staff.
            t = progress / 0.2
            hand_x = x + facing * 20
            hand_y = y - 24 + hover
            cr = int(4 + t * 6)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_xharokh._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_mid"], (hand_x, hand_y),
                                  cr - 2)
            _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_light"], (hand_x, hand_y),
                                  max(1, cr - 4))
        else:
            # 5 spines fired in spread pattern (fan).
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 22
            start_y = y - 20 + hover
            num_spines = 5
            base_angle = math.atan2(ty - start_y, tx - start_x)
            for spine_i in range(num_spines):
                # Spread angle (-30 to +30 degrees).
                spread_deg = -30 + spine_i * (60 / (num_spines - 1))
                spine_angle = base_angle + math.radians(spread_deg)
                spine_dist = 220
                # Spine tip position based on t.
                end_x = start_x + int(math.cos(spine_angle) * spine_dist)
                end_y = start_y + int(math.sin(spine_angle) * spine_dist)
                bx = int(start_x + (end_x - start_x) * t)
                by = int(start_y + (end_y - start_y) * t)
                # Trail behind each spine.
                for i in range(6):
                    trail_t = max(0.0, t - i * 0.06)
                    px = int(start_x + (end_x - start_x) * trail_t)
                    py = int(start_y + (end_y - start_y) * trail_t)
                    alpha = _NS_xharokh._alpha(220 - i * 30)
                    size = max(1, 4 - i)
                    _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                                          (px, py), size)
                    _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                          (px, py), max(1, size - 1))
                    _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                          (px, py), max(1, size - 2))
                # Spine head (elongated diamond shape).
                tip_forward = 8
                tip = (bx + int(math.cos(spine_angle) * tip_forward),
                       by + int(math.sin(spine_angle) * tip_forward))
                perp = spine_angle + math.pi / 2
                w = 3
                side_a = (bx + int(math.cos(perp) * w), by + int(math.sin(perp) * w))
                side_b = (bx - int(math.cos(perp) * w), by - int(math.sin(perp) * w))
                back = (bx - int(math.cos(spine_angle) * 5),
                        by - int(math.sin(spine_angle) * 5))
                _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["shadow_deep"],
                                  [(tip[0] + 1, tip[1] + 1),
                                   (side_a[0] + 1, side_a[1] + 1),
                                   (back[0] + 1, back[1] + 1),
                                   (side_b[0] + 1, side_b[1] + 1)])
                _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["void_darkest"],
                                  [tip, side_a, back, side_b])
                _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["void_dark"],
                                  [tip,
                                   (int((tip[0] + side_a[0]) / 2), int((tip[1] + side_a[1]) / 2)),
                                   (bx, by),
                                   (int((tip[0] + side_b[0]) / 2), int((tip[1] + side_b[1]) / 2))])
                _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["void_mid"],
                                  [tip, (bx, by),
                                   (int((tip[0] + side_a[0]) / 2), int((tip[1] + side_a[1]) / 2))])
                _NS_xharokh._aacircle(surface, _NS_xharokh.PALETTE["void_light"], tip, 1)
                pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_shine"], (tip[0], tip[1], 1, 1))
    # ============================================================
    # SKILL: E - SHIFTING SANDS (portal teleport)
    # ============================================================
    def _draw_shifting_ground(surface, boss, x, y, timer, phase):
        """Portal circles at boss & target."""
        tx, ty = _NS_xharokh._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Boss portal (fades).
        if progress < 0.5:
            fade = 1.0 - progress * 2
            for i in range(3):
                r = int(28 + i * 5)
                alpha = _NS_xharokh._alpha(220 * fade - i * 55)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (x, y + 46), r, 2)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                      (x, y + 46), r, 1)
        # Target portal (grows).
        if progress > 0.3:
            grow = min(1.0, (progress - 0.3) / 0.4)
            for i in range(3):
                r = int((28 + i * 5) * grow)
                alpha = _NS_xharokh._alpha(220 - i * 55)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                      (tx, ty + 26), r, 2)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                                      (tx, ty + 26), r, 1)
    def _draw_shifting_foreground(surface, boss, x, y, timer, phase):
        """Portal effects at both boss & target during shift."""
        tx, ty = _NS_xharokh._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 6)
        # Boss vanish portal.
        if progress < 0.5:
            fade = 1.0 - progress * 2
            portal_x = x
            portal_y = y - 6 + hover
            portal_r = int(20 + math.sin(phase * 3) * 3)
            # Portal ring (like O shape from ref image).
            for r in range(portal_r, portal_r - 6, -1):
                alpha = _NS_xharokh._alpha(220 * fade)
                pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                    (portal_x - r, portal_y - r // 2,
                                     r * 2, r), 2)
            pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_light"],
                                          _NS_xharokh._alpha(240 * fade)),
                                (portal_x - portal_r + 3, portal_y - portal_r // 2 + 1,
                                 portal_r * 2 - 6, portal_r - 2), 1)
            pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_shine"],
                                          _NS_xharokh._alpha(200 * fade)),
                                (portal_x - portal_r + 6, portal_y - portal_r // 2 + 2,
                                 portal_r * 2 - 12, portal_r - 4), 1)
            # Sparks orbiting portal.
            for i in range(8):
                angle = phase * 3 + i * math.pi / 4
                sx = portal_x + int(math.cos(angle) * portal_r)
                sy = portal_y + int(math.sin(angle) * portal_r * 0.5)
                pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_hot"],
                                           _NS_xharokh._alpha(240 * fade)), (sx, sy, 2, 2))
        # Target appear portal (grows then fades).
        if progress > 0.3:
            grow = min(1.0, (progress - 0.3) / 0.35)
            fade_in = grow if progress < 0.7 else max(0.0, 1.0 - (progress - 0.7) / 0.3)
            portal_x = tx
            portal_y = ty - 6 + hover
            portal_r = int(20 * grow + math.sin(phase * 3) * 2)
            if portal_r > 3:
                for r in range(portal_r, portal_r - 6, -1):
                    alpha = _NS_xharokh._alpha(220 * fade_in)
                    if alpha <= 0:
                        break
                    pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                        (portal_x - r, portal_y - r // 2,
                                         r * 2, r), 2)
                if portal_r > 6:
                    pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_light"],
                                                  _NS_xharokh._alpha(240 * fade_in)),
                                        (portal_x - portal_r + 3, portal_y - portal_r // 2 + 1,
                                         portal_r * 2 - 6, portal_r - 2), 1)
                # Sparks orbiting.
                for i in range(8):
                    angle = phase * 3 + i * math.pi / 4
                    sx = portal_x + int(math.cos(angle) * portal_r)
                    sy = portal_y + int(math.sin(angle) * portal_r * 0.5)
                    pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_hot"],
                                               _NS_xharokh._alpha(240 * fade_in)), (sx, sy, 2, 2))
                # AoE burst at appear moment.
                if 0.65 < progress < 0.85:
                    burst_t = (progress - 0.65) / 0.2
                    burst_r = int(15 + burst_t * 25)
                    burst_alpha = _NS_xharokh._alpha(240 * (1 - burst_t))
                    _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], burst_alpha),
                                          (tx, ty), burst_r, 2)
                    _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_light"], burst_alpha),
                                          (tx, ty), max(1, burst_r - 4), 1)
                    for i in range(10):
                        angle = i * math.pi / 5
                        ex = tx + int(math.cos(angle) * burst_r)
                        ey = ty + int(math.sin(angle) * burst_r * 0.7)
                        pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_hot"], burst_alpha),
                                         (ex, ey, 2, 2))
    # ============================================================
    # SKILL: R - DOMAIN OF DESTRUCTION (massive AoE dome)
    # ============================================================
    def _draw_domain_ground(surface, boss, x, y, timer, phase):
        """Large ground circle for the domain."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r_max = 80
        r = int(r_max * min(1.0, progress * 3))
        if r > 5:
            for i in range(5):
                rr = r - i * 6
                if rr <= 3:
                    continue
                alpha = _NS_xharokh._alpha(230 - i * 40)
                pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha),
                                    (x - rr, y + 48 - rr // 3, rr * 2, rr * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha),
                                    (x - rr + 2, y + 48 - rr // 3 + 1,
                                     rr * 2 - 4, rr * 2 // 3 - 2), 1)
            # Rune markers.
            for i in range(16):
                angle = phase * 0.5 + i * math.pi / 8
                mx = x + int(math.cos(angle) * r)
                my = y + 48 + int(math.sin(angle) * r * 0.35)
                pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_light"], (mx, my, 2, 2))
                pygame.draw.rect(surface, _NS_xharokh.PALETTE["void_shine"], (mx, my, 1, 1))
    def _draw_domain_foreground(surface, boss, x, y, timer, phase):
        """Massive purple dome + spikes rising + spore explosions."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 6)
        core_y = y - 6 + hover
        # DOME (translucent bubble - reference key visual).
        dome_r = int(80 * min(1.0, progress * 3))
        if dome_r > 10:
            dome_surf = pygame.Surface((dome_r * 2 + 20, dome_r + 20), pygame.SRCALPHA)
            dome_cx = dome_r + 10
            dome_cy = dome_r + 10
            # Multi-layer dome outline.
            for layer_i, (thickness, alpha_val) in enumerate([
                (3, 90), (2, 130), (1, 170),
            ]):
                pygame.draw.ellipse(dome_surf, (*_NS_xharokh.PALETTE["void_dark"], alpha_val),
                                    (10 - layer_i, 10 - layer_i,
                                     dome_r * 2 + layer_i * 2,
                                     dome_r + layer_i * 2), thickness)
            # Vertical & horizontal rune lines (dome grid).
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 6
                x1 = dome_cx + int(math.cos(angle) * dome_r)
                y1 = dome_cy + int(math.sin(angle) * dome_r * 0.5)
                pygame.draw.line(dome_surf, (*_NS_xharokh.PALETTE["void_mid"], 150),
                                 (dome_cx, dome_cy), (x1, y1), 1)
            # Sparkles orbiting dome.
            for i in range(16):
                angle = phase * 1.5 + i * math.pi / 8
                sx = dome_cx + int(math.cos(angle) * dome_r)
                sy = dome_cy + int(math.sin(angle) * dome_r * 0.5)
                pygame.draw.rect(dome_surf, (*_NS_xharokh.PALETTE["void_hot"], 220), (sx, sy, 2, 2))
                pygame.draw.rect(dome_surf, (*_NS_xharokh.PALETTE["void_shine"], 240), (sx, sy, 1, 1))
            # Peak crystal on top.
            peak_x = dome_cx
            peak_y = 10
            pygame.draw.line(dome_surf, (*_NS_xharokh.PALETTE["void_light"], 230),
                             (peak_x, peak_y - 5), (peak_x, peak_y + 3), 2)
            pygame.draw.rect(dome_surf, (*_NS_xharokh.PALETTE["void_shine"], 250),
                             (peak_x, peak_y - 5, 1, 1))
            surface.blit(dome_surf, (x - dome_r - 10, core_y - dome_r - 10))
        # Rising void spikes inside dome (like references show).
        num_spikes = 8
        for i in range(num_spikes):
            spike_angle = i * math.pi * 2 / num_spikes + phase * 0.2
            spike_r = int(dome_r * 0.6)
            spike_x = x + int(math.cos(spike_angle) * spike_r)
            spike_ground_y = y + 48 + int(math.sin(spike_angle) * spike_r * 0.4)
            spike_rise_t = (phase * 0.6 + i * 0.15) % 1.0
            spike_h = int(15 + spike_rise_t * 8)
            spike_tip_y = spike_ground_y - spike_h
            alpha = _NS_xharokh._alpha(220 * (1 - spike_rise_t * 0.3))
            # Draw spike as triangle.
            _NS_xharokh._poly(surface, _NS_xharokh.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 2 + 1, spike_ground_y + 1),
                (spike_x + 2 + 1, spike_ground_y + 1),
            ])
            _NS_xharokh._poly(surface, (*_NS_xharokh.PALETTE["void_darkest"], alpha), [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_ground_y),
                (spike_x + 2, spike_ground_y),
            ])
            _NS_xharokh._poly(surface, (*_NS_xharokh.PALETTE["void_dark"], alpha), [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_ground_y),
                (spike_x + 1, spike_ground_y),
            ])
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_light"], alpha),
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["void_shine"], alpha),
                             (spike_x, spike_tip_y, 1, 1))
        # Random spore explosions inside dome.
        for i in range(4):
            expl_t = (phase * 0.8 + i * 0.28) % 1.0
            if expl_t > 0.6:
                continue
            angle = i * math.pi / 2 + phase * 0.3
            ex_r = int(dome_r * 0.5)
            expl_x = x + int(math.cos(angle) * ex_r)
            expl_y = core_y + int(math.sin(angle) * ex_r * 0.4)
            expl_size = int(expl_t * 15)
            expl_alpha = _NS_xharokh._alpha(240 * (1 - expl_t / 0.6))
            for r in range(expl_size, 0, -2):
                alpha = _NS_xharokh._alpha(expl_alpha * (expl_size - r) / expl_size)
                _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_mid"], alpha),
                                      (expl_x, expl_y), r)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_hot"], expl_alpha),
                                  (expl_x, expl_y), 3)
            _NS_xharokh._aacircle(surface, (*_NS_xharokh.PALETTE["void_shine"], expl_alpha),
                                  (expl_x, expl_y), 1)
            pygame.draw.rect(surface, (*_NS_xharokh.PALETTE["white"], expl_alpha),
                             (expl_x, expl_y, 1, 1))



# ====================================================================
# KAERINYA (SUNFIST) - TRUE BOSS
# ====================================================================

class _NS_kaerinya:
    """Namespace kaerinya - fiery brawler boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (fair, warm tone)
        "skin_darkest": (60, 35, 30),
        "skin_dark": (130, 85, 68),
        "skin_mid": (195, 150, 120),
        "skin_light": (235, 205, 175),
        "skin_shine": (250, 230, 210),
        # HAIR (auburn/brown-red)
        "hair_darkest": (30, 15, 8),
        "hair_dark": (75, 40, 20),
        "hair_mid": (135, 85, 45),
        "hair_light": (200, 145, 85),
        "hair_shine": (240, 190, 130),
        # Cape/robe (deep blue)
        "cloth_darkest": (5, 10, 25),
        "cloth_dark": (18, 30, 55),
        "cloth_mid": (40, 65, 105),
        "cloth_light": (85, 120, 165),
        "cloth_edge": (140, 175, 210),
        # Leather (dark brown - bracers, boots, belt)
        "leather_dark": (25, 15, 8),
        "leather_mid": (60, 40, 22),
        "leather_light": (110, 78, 45),
        "leather_edge": (170, 130, 85),
        # GOLD (buckles, trim - and signature energy)
        "gold_darkest": (35, 25, 5),
        "gold_dark": (100, 70, 15),
        "gold_mid": (200, 155, 40),
        "gold_light": (250, 220, 110),
        "gold_shine": (255, 245, 190),
        # FIERY GOLDEN ENERGY (signature - fists, aura, projectiles)
        "fire_darkest": (55, 25, 3),
        "fire_dark": (140, 65, 8),
        "fire_mid": (240, 150, 25),
        "fire_light": (255, 210, 90),
        "fire_hot": (255, 240, 160),
        "fire_shine": (255, 255, 220),
        # Eye (bright amber)
        "eye_socket": (8, 4, 2),
        "eye_dark": (85, 45, 10),
        "eye_mid": (220, 155, 40),
        "eye_light": (255, 220, 130),
        # Pants (dark leather-tone)
        "pants_dark": (18, 12, 8),
        "pants_mid": (40, 28, 20),
        "pants_light": (75, 55, 40),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaerinya._clamp(color)
        if _NS_kaerinya.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaerinya._clamp(color)
        if _NS_kaerinya.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaerinya._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaerinya(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_kaerinya._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kry_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_kaerinya._draw_fire_aura(surface, x, y, pulse)
        _NS_kaerinya._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "e":
            _NS_kaerinya._draw_unleash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaerinya._draw_rebound_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaerinya._draw_sidekick_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — special handling for W (leap) & R (dash).
        if active_skill == "w" and 10 < skill_timer < 60:
            _NS_kaerinya._draw_kry_rebound_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r" and 10 < skill_timer < 55:
            _NS_kaerinya._draw_kry_sidekick_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_kaerinya._draw_kry_attack(surface, boss, x, y)
        else:
            _NS_kaerinya._draw_kry_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_kaerinya._draw_dispose_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaerinya._draw_rebound_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaerinya._draw_unleash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaerinya._draw_sidekick_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kry_previous_timer", 0))
        active = bool(getattr(boss, "_kry_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kry_attack_active = True
            boss._kry_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kry_attack_frame = int(getattr(boss, "_kry_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kry_attack_active = False
            boss._kry_attack_frame = 0
            active = False
        boss._kry_previous_timer = timer
        boss._kry_attack_progress = (
            min(1.0, getattr(boss, "_kry_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_kry_float(surface, boss, x, y):
        """Idle: floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_kaerinya._draw_shadow(surface, x, y + 52)
        _NS_kaerinya._draw_fire_sparks(surface, x, y + 25, boss.pulse)
        _NS_kaerinya._draw_kry_body(surface, x, y - 4 + hover,
                                    boss.direction, boss.pulse, "float", 0)
    def _draw_kry_attack(surface, boss, x, y):
        """Attack: fist punch forward."""
        progress = getattr(boss, "_kry_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        lean = 0
        if progress < 0.35:
            t = progress / 0.35
            lean = -int(t * 3) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 9)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lean = int(6 * (1 - t)) * boss.direction
        _NS_kaerinya._draw_shadow(surface, x + lean, y + 52)
        _NS_kaerinya._draw_fire_sparks(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_kaerinya._draw_kry_body(surface, x + lean, y - 4 + hover,
                                    boss.direction, boss.pulse, "attack", progress)
        # Punch impact energy at fist.
        _NS_kaerinya._draw_punch_energy(surface, boss, x + lean, y + hover, progress)
    def _draw_kry_rebound_body(surface, boss, x, y, skill_timer, pulse):
        """W skill: leap forward, arrive at target, dash back."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.6) * 5)
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        if progress < 0.4:
            # Leap forward with arc.
            t = progress / 0.4
            arc_h = -50  # jump height
            arc_offset = int(arc_h * 4 * t * (1 - t))
            leap_x = int(x + (tx - x) * t)
            leap_y = int(y + (ty - y) * t + arc_offset)
            _NS_kaerinya._draw_shadow(surface, leap_x, ty + 52)
            # Trailing golden streaks.
            for i in range(4):
                trail_t = max(0.0, t - i * 0.06)
                trail_arc = int(arc_h * 4 * trail_t * (1 - trail_t))
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t + trail_arc)
                alpha = _NS_kaerinya._alpha(200 - i * 40)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                       (px, py + 20), 4)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                                       (px, py + 20), 2)
            _NS_kaerinya._draw_kry_body(surface, leap_x, leap_y - 4 + hover,
                                        boss.direction, pulse, "attack", 0.5)
        elif progress < 0.55:
            # Arrival at target - striking pose.
            _NS_kaerinya._draw_shadow(surface, tx, ty + 52)
            _NS_kaerinya._draw_kry_body(surface, tx, ty - 4 + hover,
                                        boss.direction, pulse, "attack", 0.6)
        elif progress < 0.95:
            # Dash back to original position.
            t = (progress - 0.55) / 0.4
            arc_h = -30
            arc_offset = int(arc_h * 4 * t * (1 - t))
            back_x = int(tx + (x - tx) * t)
            back_y = int(ty + (y - ty) * t + arc_offset)
            _NS_kaerinya._draw_shadow(surface, back_x, y + 52)
            # Trailing back streaks.
            for i in range(4):
                trail_t = max(0.0, t - i * 0.06)
                trail_arc = int(arc_h * 4 * trail_t * (1 - trail_t))
                px = int(tx + (x - tx) * trail_t)
                py = int(ty + (y - ty) * trail_t + trail_arc)
                alpha = _NS_kaerinya._alpha(180 - i * 40)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                       (px, py + 20), 3)
            _NS_kaerinya._draw_kry_body(surface, back_x, back_y - 4 + hover,
                                        -boss.direction, pulse, "float", 0)
        else:
            # Back home.
            _NS_kaerinya._draw_shadow(surface, x, y + 52)
            _NS_kaerinya._draw_kry_body(surface, x, y - 4 + hover,
                                        boss.direction, pulse, "float", 0)
    def _draw_kry_sidekick_body(surface, boss, x, y, skill_timer, pulse):
        """R skill: dash forward through enemies multiple times."""
        duration = 65
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.6) * 5)
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        if progress < 0.85:
            # Dash phase.
            t = progress / 0.85
            dash_x = int(x + (tx - x) * t)
            dash_y = int(y + (ty - y) * t)
            _NS_kaerinya._draw_shadow(surface, dash_x, dash_y + 52)
            # Streaking afterimage trail.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.05)
                gx = int(x + (tx - x) * trail_t)
                gy = int(y + (ty - y) * trail_t)
                alpha_scale = (1.0 - i / 6) * 0.6
                ghost_surf = pygame.Surface((80, 100), pygame.SRCALPHA)
                _NS_kaerinya._draw_kry_body_to(ghost_surf, 40, 50 + hover,
                                               boss.direction, pulse, "attack", 0.6,
                                               alpha_scale)
                surface.blit(ghost_surf, (gx - 40, gy - 50))
            _NS_kaerinya._draw_kry_body(surface, dash_x, dash_y - 4 + hover,
                                        boss.direction, pulse, "attack", 0.6)
        else:
            # End pose.
            _NS_kaerinya._draw_shadow(surface, tx, ty + 52)
            _NS_kaerinya._draw_kry_body(surface, tx, ty - 4 + hover,
                                        boss.direction, pulse, "attack", 0.7)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_kry_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_kaerinya._draw_kry_body_to(surface, cx, cy, facing, phase, action,
                                       attack_progress, 1.0)
    def _draw_kry_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Brawler body — cape, tunic, arms with glowing fists, hair ponytail."""
        # Cape trail behind body.
        _NS_kaerinya._draw_cape_back(surface, cx, cy - 10, facing, phase, alpha_scale)
        # Legs.
        _NS_kaerinya._draw_kry_legs(surface, cx, cy + 8, facing, phase, alpha_scale)
        # Torso (tunic + cloth).
        _NS_kaerinya._draw_kry_torso(surface, cx, cy, facing, phase, alpha_scale)
        # Arms + fists.
        _NS_kaerinya._draw_kry_arms(surface, cx, cy, facing, phase, action,
                                    attack_progress, alpha_scale)
        # Head + ponytail hair + face.
        _NS_kaerinya._draw_kry_head(surface, cx, cy - 22, facing, phase, alpha_scale)
        # Ponytail (long swaying).
        _NS_kaerinya._draw_ponytail(surface, cx - facing * 4, cy - 22, facing, phase, alpha_scale)
    def _draw_cape_back(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Cape flowing behind (blue)."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.8) * 3
        # Cape shape (behind body).
        cape_pts = [
            (cx - 8, cy),
            (cx - 12 + int(sway), cy + 6),
            (cx - 14 + int(sway), cy + 16),
            (cx - 12 + int(sway), cy + 26),
            (cx - 8 + int(sway * 1.5), cy + 32),
            (cx - 2, cy + 34),
            (cx + 4, cy + 30),
            (cx + 8, cy + 20),
            (cx + 8, cy + 10),
            (cx + 6, cy + 2),
        ]
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"], cape_pts,
                                 alpha_base, offset=(2, 3))
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["cloth_darkest"], cape_pts,
                                 alpha_base)
        # Cape mid tone.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["cloth_dark"], [
            (cx - 7, cy + 1),
            (cx - 10 + int(sway), cy + 8),
            (cx - 12 + int(sway), cy + 18),
            (cx - 8 + int(sway), cy + 26),
            (cx - 2, cy + 30),
            (cx + 4, cy + 26),
            (cx + 6, cy + 16),
            (cx + 6, cy + 3),
        ], alpha_base)
        # Highlight fold.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["cloth_mid"], [
            (cx - 5, cy + 3),
            (cx - 7 + int(sway), cy + 10),
            (cx - 6 + int(sway), cy + 22),
            (cx + 2, cy + 24),
            (cx + 4, cy + 10),
        ], alpha_base)
        # Vertical folds.
        for x_off in (-8, -3, 3):
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["cloth_darkest"], alpha_base),
                             (cx + x_off, cy + 4),
                             (cx + x_off + int(sway * 0.5), cy + 26), 1)
        # Gold trim at cape edge.
        pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                         (cx - 12 + int(sway), cy + 16),
                         (cx - 8 + int(sway * 1.5), cy + 32), 1)
        pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["gold_light"], alpha_base),
                         (cx - 10 + int(sway), cy + 18),
                         (cx - 6 + int(sway), cy + 30), 1)
    def _draw_ponytail(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Long ponytail flowing back."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.9) * 4
        # Ponytail hangs down-back.
        back_dir = -facing
        segments = 5
        prev = (cx + back_dir * 3, cy - 4)
        for i in range(1, segments + 1):
            t = i / segments
            wave = math.sin(phase * 1.2 + i * 0.5) * (2 + t * 3)
            nx = prev[0] + back_dir * 3 + int(wave)
            ny = prev[1] + 4
            thickness = max(1, 5 - i)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"],
                                       (prev[0] + 1, prev[1] + 1),
                                       (nx + 1, ny + 1), thickness + 1, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["hair_darkest"],
                                       prev, (nx, ny), thickness, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["hair_dark"],
                                       prev, (nx, ny), max(1, thickness - 1), alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["hair_mid"],
                                       (prev[0], prev[1] - 1), (nx, ny - 1),
                                       max(1, thickness - 2), alpha_base)
            # Highlights.
            if i in (1, 3):
                pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["hair_light"], alpha_base),
                                 (nx, ny, 1, 1))
            prev = (nx, ny)
        # Tip.
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["hair_light"], alpha_base),
                         (prev[0], prev[1], 1, 1))
    def _draw_kry_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Head with brown hair front + amber eyes + young face."""
        alpha_base = int(255 * alpha_scale)
        # Head shape.
        head_pts = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 6, cy + 9),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 6, cy + 9),
            (cx + 7, cy + 4),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"], head_pts,
                                 alpha_base, offset=(2, 2))
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["skin_darkest"], head_pts,
                                 alpha_base)
        # Skin base.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 5, cy + 8),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
        ], alpha_base)
        # Cheek highlight.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["skin_mid"], [
            (cx - 3, cy + 2), (cx + 3, cy + 2),
            (cx + 4, cy + 5), (cx + 2, cy + 8),
            (cx - 2, cy + 8), (cx - 4, cy + 5),
        ], alpha_base)
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["skin_light"], [
            (cx - 1, cy + 3), (cx + 1, cy + 3),
            (cx + 1, cy + 5), (cx - 1, cy + 5),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["skin_shine"], alpha_base),
                         (cx, cy + 4, 1, 1))
        # HAIR (top + side fringes).
        # Hair top volume.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["hair_darkest"], [
            (cx - 7, cy - 2),
            (cx - 6, cy + 2),
            (cx - 4, cy + 1),
            (cx + 4, cy + 1),
            (cx + 6, cy + 2),
            (cx + 7, cy - 2),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ], alpha_base)
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["hair_dark"], [
            (cx - 6, cy - 1),
            (cx - 5, cy + 1),
            (cx + 5, cy + 1),
            (cx + 6, cy - 1),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ], alpha_base)
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["hair_mid"], [
            (cx - 4, cy - 2),
            (cx + 4, cy - 2),
            (cx + 3, cy),
            (cx - 3, cy),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["hair_light"], alpha_base),
                         (cx - 2, cy - 3, 4, 1))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["hair_shine"], alpha_base),
                         (cx - 1, cy - 3, 2, 1))
        # Side fringe (few strands hanging beside face).
        for side in (-1, 1):
            sx = cx + side * 6
            sy = cy + 2
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["hair_darkest"], alpha_base),
                             (sx, sy), (sx, sy + 4), 2)
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["hair_dark"], alpha_base),
                             (sx, sy), (sx, sy + 4), 1)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["hair_mid"], alpha_base),
                             (sx, sy + 3, 1, 1))
        # AMBER GLOWING EYES.
        _NS_kaerinya._draw_amber_eyes(surface, cx, cy + 5, phase, alpha_scale)
        # Small nose highlight.
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["skin_light"], alpha_base),
                         (cx, cy + 7, 1, 1))
        # Small mouth (determined expression - slight smile).
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["skin_darkest"], alpha_base),
                         (cx - 1, cy + 9, 3, 1))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["skin_dark"], alpha_base),
                         (cx, cy + 9, 2, 1))
    def _draw_amber_eyes(surface, cx, cy, phase, alpha_scale=1.0):
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            # Halo.
            for r in range(4, 0, -1):
                a = _NS_kaerinya._alpha(120 * (4 - r) / 4 * pulse * alpha_scale)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["eye_mid"], a),
                                       (ex, ey), r)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["eye_mid"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["eye_light"], alpha_base),
                             (ex, ey, 1, 1))
    def _draw_kry_torso(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Blue tunic torso with leather belt + gold buckle."""
        alpha_base = int(255 * alpha_scale)
        # Torso shape (V-shape, athletic).
        torso_pts = [
            (cx - 8, cy - 10),
            (cx - 10, cy - 4),
            (cx - 8, cy),
            (cx - 7, cy + 6),
            (cx - 9, cy + 10),
            (cx + 9, cy + 10),
            (cx + 7, cy + 6),
            (cx + 8, cy),
            (cx + 10, cy - 4),
            (cx + 8, cy - 10),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ]
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"], torso_pts,
                                 alpha_base, offset=(2, 2))
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["cloth_darkest"], torso_pts,
                                 alpha_base)
        # Cloth mid.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["cloth_dark"], [
            (cx - 7, cy - 9),
            (cx - 9, cy - 3),
            (cx - 7, cy),
            (cx - 6, cy + 6),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 6, cy + 6),
            (cx + 7, cy),
            (cx + 9, cy - 3),
            (cx + 7, cy - 9),
            (cx + 3, cy - 11),
            (cx - 3, cy - 11),
        ], alpha_base)
        # Cloth center highlight.
        _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["cloth_mid"], [
            (cx - 4, cy - 8),
            (cx - 6, cy - 2),
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 6, cy - 2),
            (cx + 4, cy - 8),
        ], alpha_base)
        # Highlight stripe (front lit).
        pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["cloth_light"], alpha_base),
                         (cx - 3, cy - 8), (cx - 3, cy + 4), 1)
        pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["cloth_edge"], alpha_base),
                         (cx + 3, cy - 8), (cx + 3, cy + 4), 1)
        # Gold trim on shoulders/neckline.
        pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                         (cx - 4, cy - 12), (cx + 4, cy - 12), 1)
        pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["gold_light"], alpha_base),
                         (cx - 3, cy - 12), (cx + 3, cy - 12), 1)
        # LEATHER BELT (waist).
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_dark"], alpha_base),
                         (cx - 9, cy + 5, 18, 3))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_mid"], alpha_base),
                         (cx - 9, cy + 5, 18, 2))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_light"], alpha_base),
                         (cx - 8, cy + 5, 16, 1))
        # GOLD BELT BUCKLE (center, embossed - like a fist or star).
        buckle_x = cx
        buckle_y = cy + 6
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_darkest"], alpha_base),
                         (buckle_x - 3, buckle_y - 1, 6, 4))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_dark"], alpha_base),
                         (buckle_x - 3, buckle_y - 1, 6, 3))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                         (buckle_x - 2, buckle_y, 4, 2))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_light"], alpha_base),
                         (buckle_x - 1, buckle_y, 2, 1))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_shine"], alpha_base),
                         (buckle_x - 1, buckle_y, 1, 1))
        # Emblem on chest (small fist symbol).
        emblem_y = cy - 3
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_dark"], alpha_base),
                         (cx - 2, emblem_y, 4, 3))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                         (cx - 1, emblem_y, 2, 2))
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_light"], alpha_base),
                         (cx - 1, emblem_y, 1, 1))
    def _draw_kry_arms(surface, cx, cy, facing, phase, action, attack_progress,
                       alpha_scale=1.0):
        """Two arms with bracer & glowing fists."""
        alpha_base = int(255 * alpha_scale)
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 8
            base_y = cy - 6
            is_punch_arm = (side == facing)
            # Determine hand position.
            if action == "attack" and is_punch_arm:
                # Wind-up → punch forward → recover.
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    angle_deg = 30 + t * 30  # pull back
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    angle_deg = 60 - t * 90  # punch straight out
                else:
                    t = (attack_progress - 0.6) / 0.4
                    angle_deg = -30 + t * 60  # recover
                arm_len = 16 if 0.35 <= attack_progress <= 0.6 else 12
            else:
                # Idle: fighting stance — arms up, fists ready.
                sway = math.sin(phase * 0.6 + side_i * 0.4) * 1
                angle_deg = -10 + int(sway * 3)
                arm_len = 12
            angle_rad = math.radians(angle_deg)
            hand_x = base_x + int(math.cos(angle_rad) * arm_len) * side
            hand_y = base_y + int(math.sin(angle_rad) * arm_len)
            elbow_x = base_x + int(math.cos(angle_rad + 0.3) * arm_len * 0.5) * side
            elbow_y = base_y + int(math.sin(angle_rad + 0.3) * arm_len * 0.5)
            # Upper arm (cloth sleeve - blue).
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"],
                                       (base_x + 1, base_y + 1),
                                       (elbow_x + 1, elbow_y + 1), 5, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["cloth_darkest"],
                                       (base_x, base_y), (elbow_x, elbow_y), 4, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["cloth_dark"],
                                       (base_x, base_y), (elbow_x, elbow_y), 3, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["cloth_mid"],
                                       (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1,
                                       alpha_base)
            # Forearm (bare skin).
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"],
                                       (elbow_x + 1, elbow_y + 1),
                                       (hand_x + 1, hand_y + 1), 4, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["skin_darkest"],
                                       (elbow_x, elbow_y), (hand_x, hand_y), 3, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["skin_dark"],
                                       (elbow_x, elbow_y), (hand_x, hand_y), 2, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["skin_mid"],
                                       (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1,
                                       alpha_base)
            # LEATHER BRACER at wrist.
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_dark"], alpha_base),
                             (hand_x - 2, hand_y - 1, 4, 3))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_mid"], alpha_base),
                             (hand_x - 2, hand_y - 1, 4, 2))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                             (hand_x - 1, hand_y, 2, 1))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_light"], alpha_base),
                             (hand_x, hand_y, 1, 1))
            # GLOWING FIST.
            _NS_kaerinya._draw_fiery_fist(surface, hand_x, hand_y + 2, phase, alpha_base,
                                          intense=(action == "attack" and is_punch_arm))
    def _draw_fiery_fist(surface, cx, cy, phase, alpha_base, intense=False):
        """Fist with golden fire aura."""
        # Fist base (skin knuckles).
        _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["shadow_deep"], alpha_base),
                               (cx + 1, cy + 1), 4)
        _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["skin_darkest"], alpha_base),
                               (cx, cy), 4)
        _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["skin_dark"], alpha_base),
                               (cx, cy), 3)
        _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["skin_mid"], alpha_base),
                               (cx - 1, cy - 1), 2)
        # Knuckle bumps.
        for k in range(3):
            kx = cx - 2 + k * 2
            ky = cy - 2
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["skin_light"], alpha_base),
                             (kx, ky, 1, 1))
        # FIERY GOLDEN AURA around fist.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        strength = 1.8 if intense else 1.0
        for r in range(int(10 * strength), 4, -1):
            alpha = _NS_kaerinya._alpha(140 * pulse * strength * (10 - r) / 10 * alpha_base / 255)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                   (cx, cy), r)
        for r in range(int(7 * strength), 3, -1):
            alpha = _NS_kaerinya._alpha(180 * pulse * strength * (7 - r) / 7 * alpha_base / 255)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                   (cx, cy), r)
        _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha_base),
                               (cx, cy), 3)
        _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha_base),
                               (cx, cy), 2)
        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha_base),
                         (cx, cy, 1, 1))
        # Flame flickers around fist.
        num_flames = 5 if intense else 3
        for i in range(num_flames):
            flame_angle = phase * 3 + i * (math.pi * 2 / num_flames)
            fr = 5 + int(math.sin(phase * 4 + i) * 2)
            fx = cx + int(math.cos(flame_angle) * fr)
            fy = cy + int(math.sin(flame_angle) * fr)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha_base),
                             (fx, fy, 1, 1))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha_base),
                             (fx, fy, 1, 1))
    def _draw_kry_legs(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Legs with pants + boots."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.8) * 2
        for side in (-1, 1):
            hip_x = cx + side * 4
            hip_y = cy
            knee_x = cx + side * 5 + int(sway * 0.5)
            knee_y = cy + 10
            foot_x = cx + side * 4 + int(sway)
            foot_y = cy + 20
            # Thigh (dark pants).
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"],
                                       (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1),
                                       5, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["pants_dark"],
                                       (hip_x, hip_y), (knee_x, knee_y), 4, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["pants_mid"],
                                       (hip_x, hip_y), (knee_x, knee_y), 3, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["pants_light"],
                                       (hip_x - side, hip_y - 1), (knee_x - side, knee_y - 1),
                                       1, alpha_base)
            # Shin/boot (leather).
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"],
                                       (knee_x + 1, knee_y + 1), (foot_x + 1, foot_y + 1),
                                       5, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["leather_dark"],
                                       (knee_x, knee_y), (foot_x, foot_y), 4, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["leather_mid"],
                                       (knee_x, knee_y), (foot_x, foot_y), 3, alpha_base)
            _NS_kaerinya._aaline_alpha(surface, _NS_kaerinya.PALETTE["leather_light"],
                                       (knee_x - side, knee_y), (foot_x - side, foot_y), 1,
                                       alpha_base)
            # Knee guard (small).
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_dark"], alpha_base),
                             (knee_x - 2, knee_y - 1, 4, 2))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_dark"], alpha_base),
                             (knee_x - 1, knee_y - 1, 2, 1))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                             (knee_x, knee_y - 1, 1, 1))
            # Boot base.
            foot_pts = [
                (foot_x - 4, foot_y),
                (foot_x + 4, foot_y),
                (foot_x + 5, foot_y + 3),
                (foot_x - 5, foot_y + 3),
            ]
            _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["shadow_deep"],
                                     [(p[0] + 1, p[1] + 1) for p in foot_pts], alpha_base)
            _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["leather_dark"], foot_pts,
                                     alpha_base)
            _NS_kaerinya._poly_alpha(surface, _NS_kaerinya.PALETTE["leather_mid"], [
                (foot_x - 3, foot_y + 1),
                (foot_x + 3, foot_y + 1),
                (foot_x + 4, foot_y + 2),
                (foot_x - 4, foot_y + 2),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["leather_edge"], alpha_base),
                             (foot_x - 2, foot_y + 1, 4, 1))
            # Gold buckle on boot.
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_dark"], alpha_base),
                             (foot_x - 1, foot_y - 2, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["gold_mid"], alpha_base),
                             (foot_x, foot_y - 2, 1, 1))
    # ============================================================
    # HELPERS
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_kaerinya._poly(surface, color, points)
            return
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_kaerinya._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_kaerinya._aaline(surface, color, start, end, width)
            return
        c = _NS_kaerinya._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (10, 5, 2, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (100, 60, 15, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_kaerinya._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kaerinya._aacircle(aura, (*_NS_kaerinya.PALETTE["fire_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_kaerinya._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaerinya._aacircle(aura, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kaerinya._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaerinya._aacircle(aura, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating gold sparks.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_kaerinya.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaerinya.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaerinya.PALETTE["fire_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_kaerinya.PALETTE["fire_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_kaerinya.PALETTE["fire_mid"], 230),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_kaerinya.PALETTE["fire_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaerinya.PALETTE["fire_hot"],
                                       _NS_kaerinya._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_fire_sparks(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_kaerinya._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaerinya.PALETTE["fire_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_kaerinya._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising fire embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_kaerinya._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                   (sx, sy), 3)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                             (sx, sy - 2, 1, 1))
    # ============================================================
    # PUNCH IMPACT (melee foreground)
    # ============================================================
    def _draw_punch_energy(surface, boss, x, y, progress):
        """Explosive golden burst at fist during punch peak."""
        if not (0.45 <= progress <= 0.7):
            return
        facing = boss.direction
        t = (progress - 0.45) / 0.25
        intensity = math.sin(t * math.pi)
        # Fist position (in front of body).
        fist_x = x + facing * 24
        fist_y = y - 6
        # Big golden burst at fist.
        burst_r = int(15 * intensity)
        for r in range(burst_r + 5, 0, -1):
            alpha = _NS_kaerinya._alpha(200 * intensity * (burst_r + 5 - r) / (burst_r + 5))
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                   (fist_x, fist_y), r)
        _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_mid"], (fist_x, fist_y),
                               max(1, burst_r - 3))
        _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_light"], (fist_x, fist_y),
                               max(1, burst_r - 6))
        _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_hot"], (fist_x, fist_y),
                               max(1, burst_r - 9))
        pygame.draw.rect(surface, _NS_kaerinya.PALETTE["fire_shine"], (fist_x, fist_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaerinya.PALETTE["white"], (fist_x, fist_y, 1, 1))
        # Radial rays.
        for i in range(8):
            a = i * math.pi / 4
            rx = fist_x + int(math.cos(a) * (burst_r + 8))
            ry = fist_y + int(math.sin(a) * (burst_r + 8))
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_light"],
                                       _NS_kaerinya._alpha(240 * intensity)),
                             (fist_x, fist_y), (rx, ry), 1)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"],
                                       _NS_kaerinya._alpha(240 * intensity)),
                             (rx, ry, 2, 2))
    # ============================================================
    # SKILL: Q - DISPOSE (ranged fist punch projectile)
    # ============================================================
    def _draw_dispose_foreground(surface, boss, x, y, timer, phase):
        """Ranged fist-shaped projectile flying forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.2:
            # Charge in fist.
            t = progress / 0.2
            fist_x = x + facing * 20
            fist_y = y - 4 + hover
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kaerinya._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                       (fist_x, fist_y), r)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_mid"], (fist_x, fist_y),
                                   cr - 2)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_light"], (fist_x, fist_y),
                                   max(1, cr - 4))
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_hot"], (fist_x, fist_y),
                                   max(1, cr - 6))
            pygame.draw.rect(surface, _NS_kaerinya.PALETTE["fire_shine"], (fist_x, fist_y, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 24
            start_y = y - 4 + hover
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Comet trail.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kaerinya._alpha(240 - i * 22)
                size = max(1, 8 - i)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_darkest"], alpha),
                                       (px, py), size)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                       (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                        pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # FIST-SHAPED head (rounded ball with 4 knuckle bumps).
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_darkest"], (bx, by), 10)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_dark"], (bx, by), 8)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_mid"], (bx, by), 6)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_light"], (bx, by), 4)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_hot"], (bx, by), 3)
            _NS_kaerinya._aacircle(surface, _NS_kaerinya.PALETTE["fire_shine"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_kaerinya.PALETTE["white"], (bx, by, 1, 1))
            # Knuckle bumps (small bright dots at front of fist).
            angle_to_target = math.atan2(ty - start_y, tx - start_x)
            for k in range(4):
                knuckle_off = -0.6 + k * 0.4
                kx = bx + int(math.cos(angle_to_target + knuckle_off) * 6)
                ky = by + int(math.sin(angle_to_target + knuckle_off) * 6)
                pygame.draw.rect(surface, _NS_kaerinya.PALETTE["fire_shine"], (kx, ky, 1, 1))
                pygame.draw.rect(surface, _NS_kaerinya.PALETTE["white"], (kx, ky, 1, 1))
            # Radial glow.
            for r in range(15, 5, -2):
                alpha = _NS_kaerinya._alpha(100 * (15 - r) / 15)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                       (bx, by), r)
            # Impact splash on target.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(15 + st * 30)
                alpha = _NS_kaerinya._alpha(240 * (1 - st))
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_darkest"], alpha),
                                       (tx, ty), radius + 4, 3)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 2)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                       (tx, ty), max(1, radius - 12), 1)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                       (tx, ty), max(1, radius // 4))
                # Radial rays (like burst).
                for i in range(12):
                    a = i * math.pi / 6
                    ex = tx + int(math.cos(a) * radius)
                    ey = ty + int(math.sin(a) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: W - REBOUND (leap + return)
    # ============================================================
    def _draw_rebound_ground(surface, boss, x, y, timer, phase):
        """Rings at boss start & target."""
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Start ring fade in as leaping.
        if progress < 0.5:
            fade = 1.0 - progress * 2
            for i in range(2):
                r = int(28 + i * 5)
                alpha = _NS_kaerinya._alpha(200 * fade - i * 50)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                       (x, y + 44), r, 2)
        # Target ring during arrival.
        if 0.3 < progress < 0.7:
            grow = min(1.0, (progress - 0.3) / 0.2) if progress < 0.5 else max(0.0, 1.0 - (progress - 0.5) / 0.2)
            for i in range(3):
                r = int((25 + i * 6) * grow)
                alpha = _NS_kaerinya._alpha(220 - i * 55)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                       (tx, ty + 20), r, 2)
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                       (tx, ty + 20), max(1, r - 3), 1)
    def _draw_rebound_foreground(surface, boss, x, y, timer, phase):
        """Impact burst at target."""
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if 0.4 < progress < 0.6:
            # Arrival explosion.
            t = (progress - 0.4) / 0.2
            intensity = math.sin(t * math.pi)
            radius = int(15 + t * 25)
            alpha = _NS_kaerinya._alpha(240 * intensity)
            # Big burst.
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_darkest"], alpha),
                                   (tx, ty), radius + 4, 3)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                   (tx, ty), max(1, radius - 5), 2)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                   (tx, ty), max(1, radius - 12), 1)
            # Stun stars circling above.
            for i in range(3):
                star_angle = phase * 3 + i * (math.pi * 2 / 3)
                sr = 20
                stx = tx + int(math.cos(star_angle) * sr)
                sty = ty - 15 + int(math.sin(star_angle) * 3)
                pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                 (stx - 1, sty, 3, 1))
                pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                 (stx, sty - 1, 1, 3))
                pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                 (stx, sty, 1, 1))
            # Radial rays.
            for i in range(10):
                a = i * math.pi / 5
                ex = tx + int(math.cos(a) * radius)
                ey = ty + int(math.sin(a) * radius * 0.7)
                pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL: E - UNLEASH (self buff aura - like sun radiance)
    # ============================================================
    def _draw_unleash_ground(surface, boss, x, y, timer, phase):
        """Golden circle around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_kaerinya._alpha(200 - i * 50)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                   (x, y + 44), r, 2)
            _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                   (x, y + 44), r, 1)
    def _draw_unleash_foreground(surface, boss, x, y, timer, phase):
        """Golden radiant ring around boss + sparkles + rays."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.6) * 5)
        core_y = y - 4 + hover
        # Big radiant ring around boss.
        ring_r = 35 + int(math.sin(phase * 2) * 3)
        # Draw multiple concentric rings.
        ring_surf = pygame.Surface((ring_r * 2 + 20, ring_r * 2 + 20), pygame.SRCALPHA)
        center = (ring_r + 10, ring_r + 10)
        for layer_i, (thickness, alpha_val) in enumerate([
            (2, 120), (1, 200),
        ]):
            _NS_kaerinya._aacircle(ring_surf, (*_NS_kaerinya.PALETTE["fire_mid"], alpha_val),
                                   center, ring_r - layer_i, thickness)
            _NS_kaerinya._aacircle(ring_surf, (*_NS_kaerinya.PALETTE["fire_light"], alpha_val),
                                   center, ring_r - layer_i - 1, 1)
        # 4 "cross" markers on ring (like ref image with +).
        for i in range(4):
            angle = phase * 0.3 + i * math.pi / 2
            mx = center[0] + int(math.cos(angle) * ring_r)
            my = center[1] + int(math.sin(angle) * ring_r)
            pygame.draw.rect(ring_surf, _NS_kaerinya.PALETTE["fire_hot"], (mx - 2, my, 5, 1))
            pygame.draw.rect(ring_surf, _NS_kaerinya.PALETTE["fire_hot"], (mx, my - 2, 1, 5))
            pygame.draw.rect(ring_surf, _NS_kaerinya.PALETTE["fire_shine"], (mx, my, 1, 1))
        # Small sparkles around ring.
        for i in range(20):
            sp_angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(sp_angle) * ring_r)
            sy = center[1] + int(math.sin(sp_angle) * ring_r)
            pygame.draw.rect(ring_surf, _NS_kaerinya.PALETTE["fire_light"], (sx, sy, 1, 1))
            pygame.draw.rect(ring_surf, _NS_kaerinya.PALETTE["fire_shine"], (sx, sy, 1, 1))
        surface.blit(ring_surf, (x - ring_r - 10, core_y - ring_r - 10))
        # Radial rays coming out of boss (like sun rays).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(12):
            ray_angle = phase * 0.5 + i * math.pi / 6
            ray_len = int(45 + math.sin(phase * 3 + i) * 5)
            rx1 = x + int(math.cos(ray_angle) * 20)
            ry1 = core_y + int(math.sin(ray_angle) * 20)
            rx2 = x + int(math.cos(ray_angle) * ray_len)
            ry2 = core_y + int(math.sin(ray_angle) * ray_len)
            alpha = _NS_kaerinya._alpha(180 * pulse)
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                             (rx1, ry1), (rx2, ry2), 1)
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                             (rx2, ry2, 1, 1))
        # Rising gold sparkles around body.
        for i in range(8):
            angle = i * math.pi / 4
            base_r = 30
            bx = x + int(math.cos(angle) * base_r)
            by_base = core_y + int(math.sin(angle) * base_r * 0.5)
            rise_t = (phase * 0.6 + i * 0.15) % 1.0
            by = by_base - int(rise_t * 25)
            alpha = _NS_kaerinya._alpha(220 * (1 - rise_t))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                             (bx, by, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                             (bx, by, 1, 1))
        # Body glow (empowered).
        for r in range(20, 0, -2):
            alpha = _NS_kaerinya._alpha(100 * pulse * (20 - r) / 20)
            if alpha > 0:
                _NS_kaerinya._aacircle(surface, (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                       (x, core_y), r)
    # ============================================================
    # SKILL: R - SIDEKICK (multi-hit dash strikes)
    # ============================================================
    def _draw_sidekick_ground(surface, boss, x, y, timer, phase):
        """Trail line on ground."""
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if 0.1 < progress < 0.9:
            # Ground streak line.
            t = min(1.0, (progress - 0.1) / 0.8)
            end_x = int(x + (tx - x) * t)
            end_y = int(y + (ty - y) * t)
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_darkest"], 220),
                             (x, y + 44), (end_x, end_y + 30), 5)
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_mid"], 240),
                             (x, y + 44), (end_x, end_y + 30), 3)
            pygame.draw.line(surface, (*_NS_kaerinya.PALETTE["fire_light"], 220),
                             (x, y + 44), (end_x, end_y + 30), 1)
    def _draw_sidekick_foreground(surface, boss, x, y, timer, phase):
        """Multiple strike bursts along dash path."""
        tx, ty = _NS_kaerinya._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.6) * 5)
        if 0.1 < progress < 0.85:
            # Multiple hit points along path (like multi-strike).
            t = (progress - 0.1) / 0.75
            # Show 4 strike positions along path.
            num_strikes = 4
            for i in range(num_strikes):
                strike_t = i / (num_strikes - 1) if num_strikes > 1 else 0
                strike_x = int(x + (tx - x) * strike_t)
                strike_y = int(y + (ty - y) * strike_t) - 4 + hover
                # Strike appears/disappears based on t.
                if t >= strike_t and t < strike_t + 0.3:
                    strike_progress = (t - strike_t) / 0.3
                    burst_r = int(12 * (1 - strike_progress))
                    alpha = _NS_kaerinya._alpha(240 * (1 - strike_progress))
                    _NS_kaerinya._aacircle(surface,
                                           (*_NS_kaerinya.PALETTE["fire_dark"], alpha),
                                           (strike_x, strike_y), burst_r + 2, 2)
                    _NS_kaerinya._aacircle(surface,
                                           (*_NS_kaerinya.PALETTE["fire_mid"], alpha),
                                           (strike_x, strike_y), max(1, burst_r), 2)
                    _NS_kaerinya._aacircle(surface,
                                           (*_NS_kaerinya.PALETTE["fire_light"], alpha),
                                           (strike_x, strike_y), max(1, burst_r - 3), 1)
                    _NS_kaerinya._aacircle(surface,
                                           (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                           (strike_x, strike_y), max(1, burst_r // 3))
                    # Radial rays.
                    for k in range(6):
                        a = k * math.pi / 3
                        ex = strike_x + int(math.cos(a) * (burst_r + 3))
                        ey = strike_y + int(math.sin(a) * (burst_r + 3))
                        pygame.draw.line(surface,
                                         (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                                         (strike_x, strike_y), (ex, ey), 1)
                        pygame.draw.rect(surface,
                                         (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                         (ex, ey, 1, 1))
        # Trailing golden sparkles along path.
        if 0.05 < progress < 0.9:
            t = (progress - 0.05) / 0.85
            for i in range(15):
                sp_t = (phase * 2 + i * 0.06) % 1.0
                if sp_t > t:
                    continue
                spx = int(x + (tx - x) * sp_t)
                spy = int(y + (ty - y) * sp_t) - 4 + hover
                spx += int(math.sin(phase * 4 + i) * 8)
                spy += int(math.cos(phase * 4 + i) * 4)
                alpha = _NS_kaerinya._alpha(220 * (1 - abs(t - sp_t) * 3))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_hot"], alpha),
                                     (spx, spy, 2, 2))
                    pygame.draw.rect(surface, (*_NS_kaerinya.PALETTE["fire_shine"], alpha),
                                     (spx, spy, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_nyxallaria(surface, boss, x, y):
    """Entry point nyxallaria."""
    return _NS_nyxallaria.draw_nyxallaria(surface, boss, x, y)


def draw_vhaerinth(surface, boss, x, y):
    """Entry point vhaerinth."""
    return _NS_vhaerinth.draw_vhaerinth(surface, boss, x, y)


def draw_xharokh(surface, boss, x, y):
    """Entry point xharokh."""
    return _NS_xharokh.draw_xharokh(surface, boss, x, y)


def draw_kaerinya(surface, boss, x, y):
    """Entry point kaerinya."""
    return _NS_kaerinya.draw_kaerinya(surface, boss, x, y)
