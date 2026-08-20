"""
bosses/level52.py - Semua boss Level 52

Berisi:
  - garumenshi (mini boss - MELEE sage toad hermit, summoner)
  - thoraz     (mini boss - MELEE mountainbreaker, fighter/charger)
  - vhaerith   (mini boss - RANGED hollow reaper, magic)
  - nyxaris    (TRUE BOSS - RANGED lunar herald, marksman)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================================================
# GARUMENSHI - MINI BOSS
# ====================================================================================================

class _NS_garumenshi:
    """Namespace garumenshi - Sage Toad Hermit mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # White hair (spiky mane)
        "hair_darkest": (60, 55, 50),
        "hair_dark": (130, 125, 115),
        "hair_mid": (200, 195, 185),
        "hair_light": (240, 238, 230),
        "hair_shine": (255, 255, 250),

        # Skin (aged sage)
        "skin_darkest": (90, 55, 40),
        "skin_dark": (160, 110, 80),
        "skin_mid": (215, 165, 125),
        "skin_light": (245, 210, 170),
        "skin_shine": (255, 235, 200),

        # Red facial marks / eye marks
        "mark_dark": (110, 20, 20),
        "mark_mid": (200, 40, 40),
        "mark_light": (255, 90, 70),

        # Green haori/vest
        "cloth_darkest": (25, 35, 20),
        "cloth_dark": (55, 75, 40),
        "cloth_mid": (95, 120, 65),
        "cloth_light": (150, 175, 105),
        "cloth_shine": (200, 220, 155),

        # Red robe/scarf accents
        "robe_darkest": (60, 15, 15),
        "robe_dark": (120, 30, 30),
        "robe_mid": (185, 50, 45),
        "robe_light": (230, 90, 75),
        "robe_shine": (255, 150, 130),

        # Pants (grey-brown)
        "pants_dark": (55, 50, 40),
        "pants_mid": (100, 90, 70),
        "pants_light": (150, 135, 105),

        # Metal headband
        "metal_dark": (60, 55, 55),
        "metal_mid": (140, 135, 130),
        "metal_light": (210, 205, 200),
        "metal_shine": (250, 248, 245),

        # Rasengan blue chakra
        "chakra_darkest": (5, 20, 60),
        "chakra_dark": (20, 60, 140),
        "chakra_mid": (60, 130, 220),
        "chakra_light": (140, 200, 255),
        "chakra_hot": (200, 235, 255),
        "chakra_shine": (245, 252, 255),

        # Orange sage fire (oil/flames)
        "fire_darkest": (60, 15, 5),
        "fire_dark": (140, 45, 10),
        "fire_mid": (220, 100, 20),
        "fire_light": (255, 175, 50),
        "fire_hot": (255, 220, 120),
        "fire_shine": (255, 250, 200),

        # Sage red aura (mode)
        "sage_dark": (100, 15, 20),
        "sage_mid": (200, 30, 40),
        "sage_light": (255, 90, 90),
        "sage_glow": (255, 180, 170),

        # Toad brown-red
        "toad_darkest": (40, 20, 10),
        "toad_dark": (95, 45, 20),
        "toad_mid": (155, 80, 40),
        "toad_light": (210, 130, 70),
        "toad_belly": (240, 200, 140),

        # Eye
        "eye_dark": (30, 20, 15),
        "eye_white": (240, 235, 220),
        "eye_iris": (60, 40, 25),
        "eye_sage_iris": (220, 180, 40),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_garumenshi._clamp(color)
        if _NS_garumenshi.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_garumenshi._clamp(color)
        if _NS_garumenshi.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_garumenshi._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_garumenshi(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_garumenshi._detect_moving(boss)
        _NS_garumenshi._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_gm_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Sage mode aura (if R active) - behind everything
        sage_mode = (active_skill == "r")
        _NS_garumenshi._draw_shadow(surface, x, y + 46)

        if sage_mode:
            _NS_garumenshi._draw_sage_aura(surface, x, y, pulse)

        _NS_garumenshi._draw_ground_seal(surface, x, y + 42, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_garumenshi._draw_oil_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_garumenshi._draw_toad_ground(surface, boss, x, y, skill_timer, pulse)

        # W - Toad Summon (behind boss)
        if active_skill == "w":
            _NS_garumenshi._draw_gamabunta(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_garumenshi._draw_gm_attack(surface, boss, x, y, sage_mode)
        elif moving:
            _NS_garumenshi._draw_gm_walk(surface, boss, x, y, sage_mode)
        else:
            _NS_garumenshi._draw_gm_idle(surface, boss, x, y, sage_mode)

        # Foreground skill FX
        if active_skill == "q":
            _NS_garumenshi._draw_rasengan_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_garumenshi._draw_oil_shot_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_garumenshi._draw_maha_rasen_skill(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gm_previous_timer", 0))
        active = bool(getattr(boss, "_gm_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gm_attack_active = True
            boss._gm_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._gm_attack_frame = int(getattr(boss, "_gm_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._gm_attack_active = False
            boss._gm_attack_frame = 0
            active = False

        boss._gm_previous_timer = timer
        boss._gm_attack_progress = (
            min(1.0, getattr(boss, "_gm_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_gm_last_x"):
            boss._gm_last_x = boss.x
            boss._gm_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gm_last_x)
        dy = abs(boss.y - boss._gm_last_y)
        boss._gm_last_x = boss.x
        boss._gm_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_gm_idle(surface, boss, x, y, sage_mode):
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_garumenshi._draw_gm_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle",
                                     sage_mode=sage_mode)

    def _draw_gm_walk(surface, boss, x, y, sage_mode):
        phase = boss.pulse * 2.2
        bob = int(math.sin(phase * 1.8) * 3)
        sway = int(math.sin(phase * 0.9) * 2)
        _NS_garumenshi._draw_gm_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk",
                                     sage_mode=sage_mode)

    def _draw_gm_attack(surface, boss, x, y, sage_mode):
        progress = getattr(boss, "_gm_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Wind-up → throw
        if progress < 0.5:
            t = progress / 0.5
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        else:
            t = (progress - 0.5) / 0.5
            lunge = int(t * 6) * boss.direction
            lift = int(2 - t * 2)

        _NS_garumenshi._draw_gm_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack",
                                     progress, sage_mode=sage_mode)

        # Basic ranged attack: small rasengan projectile
        _NS_garumenshi._draw_basic_rasengan(surface, boss, x + lunge, y - lift,
                                             progress)

    # ============================================================
    # BODY - Humanoid Sage
    # ============================================================
    def _draw_gm_body(surface, cx, cy, facing, phase, action,
                     attack_progress=0, sage_mode=False):
        """Draw humanoid: legs, torso (haori), arms, head with white spiky hair."""
        # Legs
        _NS_garumenshi._draw_legs(surface, cx, cy + 22, facing, phase, action)

        # Robe/haori (behind torso trailing)
        _NS_garumenshi._draw_robe_back(surface, cx, cy + 4, facing, phase)

        # Torso
        _NS_garumenshi._draw_torso(surface, cx, cy + 4, facing, phase)

        # Arms (depending on action)
        _NS_garumenshi._draw_arms(surface, cx, cy + 6, facing, phase, action,
                                   attack_progress)

        # Head + hair
        _NS_garumenshi._draw_head(surface, cx, cy - 16, facing, phase, sage_mode)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Two legs with pants and sandals."""
        if action == "walk":
            leg_swing = math.sin(phase * 1.5) * 3
        elif action == "attack":
            leg_swing = 0
        else:
            leg_swing = 0

        # Left leg (back)
        lx = cx - 4
        ly = cy
        lx_end = int(lx - leg_swing)
        # Right leg (front)
        rx = cx + 4
        ry = cy
        rx_end = int(rx + leg_swing)

        for leg_x, leg_x_end, offset in [(lx, lx_end, 0), (rx, rx_end, 1)]:
            # Shadow
            _NS_garumenshi._aaline(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                                    (leg_x + 2, ly + 2), (leg_x_end + 2, ly + 14 + 2), 6)
            # Pants
            _NS_garumenshi._aaline(surface, _NS_garumenshi.PALETTE["pants_dark"],
                                    (leg_x, ly), (leg_x_end, ly + 14), 6)
            _NS_garumenshi._aaline(surface, _NS_garumenshi.PALETTE["pants_mid"],
                                    (leg_x, ly), (leg_x_end, ly + 14), 4)
            _NS_garumenshi._aaline(surface, _NS_garumenshi.PALETTE["pants_light"],
                                    (leg_x - 1, ly), (leg_x_end - 1, ly + 14), 2)

            # Sandal (foot)
            pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                                (leg_x_end - 4, ly + 13, 10, 4))
            pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["pants_dark"],
                                (leg_x_end - 4, ly + 12, 9, 3))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["skin_dark"],
                             (leg_x_end - 2, ly + 12, 6, 1))

    def _draw_robe_back(surface, cx, cy, facing, phase):
        """Trailing red haori/cape behind body."""
        sway = math.sin(phase * 0.7) * 2
        # Back cape shape trailing behind
        back_dir = -facing
        base_x = cx + back_dir * 6
        base_y = cy - 4

        cape_pts = [
            (base_x, base_y - 2),
            (base_x + back_dir * 4, base_y + 3),
            (base_x + back_dir * 8 + int(sway), base_y + 12),
            (base_x + back_dir * 10 + int(sway), base_y + 22),
            (base_x + back_dir * 6, base_y + 26),
            (base_x - back_dir * 2, base_y + 20),
            (base_x - back_dir * 3, base_y + 8),
        ]
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in cape_pts])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["robe_darkest"], cape_pts)

        # Inner darker
        inner_pts = [
            (base_x, base_y),
            (base_x + back_dir * 3, base_y + 4),
            (base_x + back_dir * 6 + int(sway), base_y + 12),
            (base_x + back_dir * 7 + int(sway), base_y + 20),
            (base_x + back_dir * 4, base_y + 22),
            (base_x - back_dir * 1, base_y + 16),
        ]
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["robe_dark"], inner_pts)

        # Red highlight
        highlight_pts = [
            (base_x + back_dir * 2, base_y + 3),
            (base_x + back_dir * 5 + int(sway), base_y + 12),
            (base_x + back_dir * 3, base_y + 18),
            (base_x, base_y + 12),
        ]
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["robe_mid"], highlight_pts)

    def _draw_torso(surface, cx, cy, facing, phase):
        """Green haori vest with red trim."""
        # Torso shape (chest)
        torso = [
            (cx - 8, cy - 4),
            (cx - 9, cy),
            (cx - 8, cy + 10),
            (cx - 5, cy + 18),
            (cx + 5, cy + 18),
            (cx + 8, cy + 10),
            (cx + 9, cy),
            (cx + 8, cy - 4),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ]
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in torso])

        # Green haori (main)
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["cloth_darkest"], torso)

        # Inner lighter
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["cloth_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy + 1),
            (cx - 7, cy + 9),
            (cx - 4, cy + 16),
            (cx + 4, cy + 16),
            (cx + 7, cy + 9),
            (cx + 8, cy + 1),
            (cx + 7, cy - 3),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["cloth_mid"], [
            (cx - 5, cy - 2),
            (cx - 6, cy + 2),
            (cx - 5, cy + 8),
            (cx - 2, cy + 14),
            (cx + 2, cy + 14),
            (cx + 5, cy + 8),
            (cx + 6, cy + 2),
            (cx + 5, cy - 2),
        ])
        # Highlight
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["cloth_light"], [
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 3, cy + 8),
            (cx + 1, cy + 12),
            (cx - 1, cy + 12),
            (cx - 3, cy + 8),
        ])

        # Red robe underneath (V-neck / collar)
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["robe_darkest"], [
            (cx - 4, cy - 5),
            (cx, cy),
            (cx + 4, cy - 5),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["robe_mid"], [
            (cx - 3, cy - 4),
            (cx, cy - 1),
            (cx + 3, cy - 4),
        ])

        # Belt/sash
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                         (cx - 7, cy + 12, 14, 4))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["robe_dark"],
                         (cx - 7, cy + 12, 14, 3))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["robe_mid"],
                         (cx - 7, cy + 13, 14, 1))

        # Scroll on back (visible from side)
        scroll_x = cx - facing * 6
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                            (scroll_x - 3, cy + 6, 7, 4))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_darkest"],
                            (scroll_x - 3, cy + 6, 6, 3))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_dark"],
                            (scroll_x - 2, cy + 6, 5, 2))

    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms with hands. Action changes pose."""
        # Back arm
        back_arm_x = cx - facing * 5
        # Front arm
        front_arm_x = cx + facing * 5

        if action == "attack":
            if attack_progress < 0.5:
                # Wind up - hands together forming rasengan
                t = attack_progress / 0.5
                # Front arm bends up
                elbow_fx = front_arm_x + facing * 3
                elbow_fy = cy + 4 - int(t * 3)
                hand_fx = cx + facing * (6 + int(t * 4))
                hand_fy = cy + 2 - int(t * 5)
                # Back arm supports
                elbow_bx = back_arm_x + facing * 2
                elbow_by = cy + 5
                hand_bx = cx + facing * (4 + int(t * 3))
                hand_by = cy + 3 - int(t * 3)
            else:
                # Throw forward
                t = (attack_progress - 0.5) / 0.5
                elbow_fx = front_arm_x + facing * (3 + int(t * 4))
                elbow_fy = cy + 4
                hand_fx = cx + facing * (10 + int(t * 8))
                hand_fy = cy - 3 + int(t * 2)
                elbow_bx = back_arm_x + facing * (2 - int(t * 2))
                elbow_by = cy + 8
                hand_bx = back_arm_x + facing * (1 - int(t * 3))
                hand_by = cy + 12
        elif action == "walk":
            swing = math.sin(phase * 1.5) * 3
            elbow_fx = front_arm_x + facing * 1
            elbow_fy = cy + 6 + int(swing)
            hand_fx = front_arm_x + facing * 2
            hand_fy = cy + 12 + int(swing)
            elbow_bx = back_arm_x - facing * 1
            elbow_by = cy + 6 - int(swing)
            hand_bx = back_arm_x - facing * 2
            hand_by = cy + 12 - int(swing)
        else:  # idle
            breath = math.sin(phase * 0.6) * 1
            elbow_fx = front_arm_x + facing * 2
            elbow_fy = cy + 6 + int(breath)
            hand_fx = front_arm_x + facing * 3
            hand_fy = cy + 13 + int(breath)
            elbow_bx = back_arm_x - facing * 1
            elbow_by = cy + 6
            hand_bx = back_arm_x - facing * 2
            hand_by = cy + 13

        # Draw back arm first (behind)
        _NS_garumenshi._draw_single_arm(surface,
                                         (back_arm_x, cy - 2),
                                         (elbow_bx, elbow_by),
                                         (hand_bx, hand_by), back=True)

        # Draw front arm
        _NS_garumenshi._draw_single_arm(surface,
                                         (front_arm_x, cy - 2),
                                         (elbow_fx, elbow_fy),
                                         (hand_fx, hand_fy), back=False)

    def _draw_single_arm(surface, shoulder, elbow, hand, back=False):
        """Draw one arm with shading."""
        # Shadow
        _NS_garumenshi._aaline(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                                (shoulder[0] + 2, shoulder[1] + 2),
                                (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_garumenshi._aaline(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                                (elbow[0] + 2, elbow[1] + 2),
                                (hand[0] + 2, hand[1] + 2), 5)

        # Upper arm (green cloth)
        cloth_dark = _NS_garumenshi.PALETTE["cloth_darkest" if back else "cloth_dark"]
        cloth_mid = _NS_garumenshi.PALETTE["cloth_dark" if back else "cloth_mid"]
        _NS_garumenshi._aaline(surface, cloth_dark, shoulder, elbow, 6)
        _NS_garumenshi._aaline(surface, cloth_mid, shoulder, elbow, 4)

        # Forearm (skin exposed / arm wraps)
        skin_dark = _NS_garumenshi.PALETTE["skin_darkest" if back else "skin_dark"]
        skin_mid = _NS_garumenshi.PALETTE["skin_dark" if back else "skin_mid"]
        _NS_garumenshi._aaline(surface, skin_dark, elbow, hand, 5)
        _NS_garumenshi._aaline(surface, skin_mid, elbow, hand, 3)

        # Hand
        _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                                  (hand[0] + 1, hand[1] + 1), 3)
        _NS_garumenshi._aacircle(surface, skin_dark, hand, 3)
        _NS_garumenshi._aacircle(surface, skin_mid, hand, 2)
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["skin_light"],
                         (hand[0] - 1, hand[1] - 1, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, sage_mode):
        """Jiraiya-style head: white spiky hair mane, headband, face."""
        # HAIR MANE (huge spiky white) - back layer
        _NS_garumenshi._draw_hair_mane(surface, cx, cy, facing, phase)

        # HEAD/FACE
        head_shape = [
            (cx - 6, cy - 4),
            (cx - 7, cy),
            (cx - 6, cy + 4),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6 + facing, cy + 5),
            (cx + 7 + facing, cy + 2),
            (cx + 7 + facing, cy - 1),
            (cx + 5, cy - 4),
        ]
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in head_shape])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["skin_darkest"], head_shape)
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["skin_dark"], [
            (cx - 5, cy - 3),
            (cx - 6, cy),
            (cx - 5, cy + 3),
            (cx - 2, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5 + facing, cy + 4),
            (cx + 6 + facing, cy + 1),
            (cx + 6 + facing, cy - 1),
            (cx + 4, cy - 3),
        ])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 4, cy + 1),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 4 + facing, cy + 3),
            (cx + 5 + facing, cy),
            (cx + 3, cy - 2),
        ])
        # Highlight cheek
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["skin_light"],
                         (cx + facing * 2, cy + 1, 2, 2))

        # Red facial marks (streaks below eyes)
        for line_x in (-3, 3):
            pygame.draw.line(surface, _NS_garumenshi.PALETTE["mark_dark"],
                             (cx + line_x, cy),
                             (cx + line_x, cy + 5), 1)
            pygame.draw.line(surface, _NS_garumenshi.PALETTE["mark_mid"],
                             (cx + line_x, cy + 1),
                             (cx + line_x, cy + 4), 1)

        # EYE
        eye_x = cx + facing * 2
        eye_y = cy - 1
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                         (eye_x - 1, eye_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["eye_white"],
                         (eye_x, eye_y, 3, 2))
        if sage_mode:
            # Sage mode - yellow toad eyes
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["eye_sage_iris"],
                             (eye_x + 1, eye_y, 2, 2))
            pygame.draw.line(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                             (eye_x + 1, eye_y), (eye_x + 1, eye_y + 1), 1)
            # Red around eyes
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["mark_mid"],
                             (eye_x - 1, eye_y - 2, 5, 1))
        else:
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["eye_iris"],
                             (eye_x + 1, eye_y, 2, 2))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["eye_dark"],
                             (eye_x + 1, eye_y, 1, 2))

        # Nose hint
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["skin_darkest"],
                         (cx + facing * 4, cy + 2, 1, 2))

        # Mouth
        pygame.draw.line(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                         (cx + facing * 2, cy + 5),
                         (cx + facing * 5, cy + 5), 1)

        # HEADBAND (metal plate)
        _NS_garumenshi._draw_headband(surface, cx, cy - 4, facing)

    def _draw_hair_mane(surface, cx, cy, facing, phase):
        """Long spiky white hair - massive mane behind body."""
        sway = math.sin(phase * 0.5) * 1

        # Big mane behind head
        mane_shape = [
            (cx - 10, cy - 6),
            (cx - 14, cy - 2),
            (cx - 18, cy + 4),
            (cx - 20, cy + 12),
            (cx - 18, cy + 22),
            (cx - 14, cy + 30),
            (cx - 8, cy + 34),
            (cx, cy + 32),
            (cx + 4, cy + 22),
            (cx + 2, cy + 10),
            (cx - 2, cy + 2),
            (cx - 4, cy - 4),
        ]
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in mane_shape])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_darkest"], mane_shape)

        # Mid layer
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_dark"], [
            (cx - 9, cy - 5),
            (cx - 13, cy - 1),
            (cx - 16, cy + 5),
            (cx - 18, cy + 12),
            (cx - 16, cy + 20),
            (cx - 12, cy + 26),
            (cx - 6, cy + 28),
            (cx - 2, cy + 22),
            (cx, cy + 12),
            (cx - 2, cy + 4),
            (cx - 4, cy - 3),
        ])
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_mid"], [
            (cx - 8, cy - 3),
            (cx - 11, cy + 2),
            (cx - 14, cy + 8),
            (cx - 15, cy + 15),
            (cx - 12, cy + 22),
            (cx - 6, cy + 22),
            (cx - 3, cy + 15),
            (cx - 4, cy + 6),
            (cx - 5, cy - 1),
        ])

        # Highlights
        _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_light"], [
            (cx - 9, cy + 4),
            (cx - 12, cy + 10),
            (cx - 11, cy + 18),
            (cx - 7, cy + 18),
            (cx - 6, cy + 10),
            (cx - 7, cy + 3),
        ])

        # Spiky tips - jagged edges (multiple triangle spikes)
        spike_positions = [
            (cx - 20, cy + 6, cx - 22, cy + 8, cx - 19, cy + 12),
            (cx - 20, cy + 16, cx - 22, cy + 20, cx - 18, cy + 22),
            (cx - 14, cy + 30, cx - 16, cy + 34, cx - 12, cy + 34),
            (cx - 6, cy + 34, cx - 4, cy + 38, cx - 2, cy + 34),
            (cx - 12, cy - 4, cx - 16, cy - 6, cx - 12, cy - 2),
            (cx - 6, cy - 6, cx - 8, cy - 10, cx - 3, cy - 6),
            (cx - 2, cy - 6, cx + 1, cy - 10, cx + 3, cy - 5),
        ]
        for pts in spike_positions:
            _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_darkest"], [
                (pts[0] + 1, pts[1] + 1),
                (pts[2] + 1, pts[3] + 1),
                (pts[4] + 1, pts[5] + 1),
            ])
            _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_dark"], [
                (pts[0], pts[1]),
                (pts[2], pts[3]),
                (pts[4], pts[5]),
            ])
            _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_mid"], [
                (int((pts[0] + pts[4]) / 2), int((pts[1] + pts[5]) / 2)),
                (pts[2], pts[3]),
                (pts[4], pts[5]),
            ])

        # Front top spikes on head
        for i, (dx, dy_off) in enumerate([(-5, -8), (-2, -10), (1, -9), (4, -7)]):
            spike_x = cx + dx
            spike_y = cy + dy_off
            _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_dark"], [
                (spike_x - 2, cy - 4),
                (spike_x, spike_y),
                (spike_x + 2, cy - 4),
            ])
            _NS_garumenshi._poly(surface, _NS_garumenshi.PALETTE["hair_mid"], [
                (spike_x - 1, cy - 4),
                (spike_x, spike_y + 1),
                (spike_x + 1, cy - 4),
            ])
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["hair_light"],
                             (spike_x, spike_y + 1, 1, 2))

    def _draw_headband(surface, cx, cy, facing):
        """Metal headband/forehead protector."""
        # Cloth band
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                         (cx - 7, cy + 1, 14, 4))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["cloth_darkest"],
                         (cx - 7, cy + 1, 13, 3))

        # Metal plate
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["metal_dark"],
                         (cx - 6, cy + 1, 11, 3))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["metal_mid"],
                         (cx - 6, cy + 1, 11, 2))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["metal_light"],
                         (cx - 5, cy + 1, 10, 1))
        # Symbol (dot in middle, resembling kanji)
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["metal_dark"],
                         (cx - 1, cy + 2, 3, 1))
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["shadow"],
                         (cx, cy + 2, 1, 1))

    # ============================================================
    # BASIC ATTACK - Small Rasengan projectile
    # ============================================================
    def _draw_basic_rasengan(surface, boss, x, y, progress):
        facing = boss.direction
        # Hand position (where rasengan forms/launches)
        hx = x + facing * (14 + int(progress * 6))
        hy = y - 2

        if progress < 0.45:
            # PHASE 1: Charge in hand (rasengan forming)
            t = progress / 0.45
            r = int(3 + t * 4)

            # Glow halo
            for radius in range(r + 4, 0, -1):
                alpha = _NS_garumenshi._alpha(180 * (r + 4 - radius) / (r + 4))
                _NS_garumenshi._aacircle(
                    surface,
                    (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                    (hx, hy), radius,
                )

            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_darkest"], (hx, hy), r + 1)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_dark"], (hx, hy), r)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_mid"], (hx, hy), max(1, r - 1))
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_light"], (hx, hy), max(1, r - 2))
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_shine"], (hx, hy), max(1, r - 3))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["white"], (hx, hy, 1, 1))

            # Spiraling energy sparks around
            for i in range(6):
                angle = boss.pulse * 6 + i * math.pi / 3
                sx = hx + int(math.cos(angle) * (r + 2))
                sy = hy + int(math.sin(angle) * (r + 2))
                pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_hot"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_shine"], (sx, sy, 1, 1))
            return

        # PHASE 2: Projectile flies to target
        tx, ty = _NS_garumenshi._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 2

        t = (progress - 0.45) / 0.55
        t = max(0.0, min(1.0, t))
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Comet trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_garumenshi._alpha(230 - i * 25)
            size = max(1, 7 - i)
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                      (px, py), size)
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                      (px, py), max(1, size - 1))
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_mid"], alpha),
                                      (px, py), max(1, size - 2))
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                      (px, py), max(1, size - 3))

            # Sparks around trail
            if i < 4:
                for s in range(2):
                    angle_s = boss.pulse * 5 + i + s * 2
                    spark_x = px + int(math.cos(angle_s) * (size + 1))
                    spark_y = py + int(math.sin(angle_s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_garumenshi.PALETTE["chakra_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright rasengan head with outer glow
        for r in range(11, 3, -2):
            alpha = _NS_garumenshi._alpha(100 * (11 - r) / 11)
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                      (bx, by), r)
        _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_darkest"], (bx, by), 7)
        _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_dark"], (bx, by), 6)
        _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_mid"], (bx, by), 4)
        _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_light"], (bx, by), 2)
        _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_garumenshi.PALETTE["white"], (bx, by, 1, 1))

        # Spinning spiral arms on projectile
        for i in range(4):
            angle = boss.pulse * 8 + i * math.pi / 2
            for r_step in (6, 8):
                sx = bx + int(math.cos(angle) * r_step)
                sy = by + int(math.sin(angle) * r_step)
                pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_hot"], (sx, sy, 1, 1))

        # Impact burst
        if t > 0.85:
            st = (t - 0.85) / 0.15
            radius = int(8 + st * 20)
            alpha = _NS_garumenshi._alpha(240 * (1 - st))
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                      (tx, ty), radius + 3, 3)
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                      (tx, ty), radius, 2)
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_mid"], alpha),
                                      (tx, ty), max(1, radius - 5), 2)
            _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                      (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["chakra_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["chakra_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius, 80 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 6, 90, 12))
        surface.blit(shadow, (x - 50, y - 12))

    def _draw_sage_aura(surface, x, y, phase):
        """Red sage mode aura."""
        pulse = math.sin(phase * 0.6) * 0.3 + 0.7
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_garumenshi._alpha((80 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_garumenshi._aacircle(aura, (*_NS_garumenshi.PALETTE["sage_dark"], alpha),
                                          (90, 80), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_garumenshi._alpha((50 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_garumenshi._aacircle(aura, (*_NS_garumenshi.PALETTE["sage_mid"], alpha),
                                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))

        # Red energy flames rising
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 35 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5) - 5
            flame_h = 5 + int(math.sin(phase * 3 + i) * 3)
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["sage_dark"],
                             (sx - 1, sy - flame_h, 2, flame_h))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["sage_mid"],
                             (sx, sy - flame_h + 1, 1, flame_h - 1))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["sage_light"],
                             (sx, sy - flame_h + 2, 1, 2))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["sage_glow"],
                             (sx, sy - flame_h + 1, 1, 1))

    def _draw_ground_seal(surface, x, y, phase, skill):
        """Ground seal circle beneath boss."""
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        ring = pygame.Surface((130, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_garumenshi.PALETTE["fire_dark"], 180),
                            (5, 12, 120, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_garumenshi.PALETTE["fire_mid"], 220),
                            (14, 14, 102, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_garumenshi.PALETTE["chakra_dark"], 180),
                            (28, 16, 74, 14), 1)

        # Seal marks
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 35)
            y1 = 22 + int(math.sin(angle) * 7)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_garumenshi.PALETTE["fire_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            color = _NS_garumenshi.PALETTE["chakra_hot"] if skill in ("q", "r") \
                else _NS_garumenshi.PALETTE["fire_hot"]
            pygame.draw.ellipse(ring, (*color, _NS_garumenshi._alpha(180 * pulse)),
                                (12, 8, 108, 30), 1)
        surface.blit(ring, (x - 65, y - 20))

    # ============================================================
    # SKILL Q - RASENGAN (big blue spiraling projectile)
    # ============================================================
    def _draw_rasengan_skill(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_garumenshi._target_position(boss, x, y)

        if progress < 0.3:
            # Big charging rasengan in hand
            t = progress / 0.3
            hx = x + facing * 16
            hy = y - 2
            cr = int(5 + t * 10)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_garumenshi._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                          (hx, hy), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_garumenshi._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                          (hx, hy), r)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_mid"], (hx, hy), cr - 2)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_light"], (hx, hy), max(1, cr - 4))
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_shine"], (hx, hy), max(1, cr - 6))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["white"], (hx, hy, 1, 1))

            # Spiraling arms
            for i in range(6):
                angle = phase * 6 + i * math.pi / 3
                for r_step in range(cr, cr + 4):
                    sx = hx + int(math.cos(angle) * r_step)
                    sy = hy + int(math.sin(angle) * r_step)
                    pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_hot"],
                                     (sx, sy, 1, 1))
        else:
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 22
            start_y = y - 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long spiral trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_garumenshi._alpha(240 - i * 22)
                size = max(1, 9 - i)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                          (px, py), size)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                          (px, py), max(1, size - 1))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_mid"], alpha),
                                          (px, py), max(1, size - 2))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                          (px, py), max(1, size - 3))
                # Sparks
                if i < 5:
                    for s in range(3):
                        angle_s = phase * 4 + i + s * 2
                        spark_x = px + int(math.cos(angle_s) * (size + 2))
                        spark_y = py + int(math.sin(angle_s) * (size + 2))
                        pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["chakra_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Bright core
            for r in range(14, 3, -2):
                alpha = _NS_garumenshi._alpha(100 * (14 - r) / 14)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                          (bx, by), r)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_darkest"], (bx, by), 10)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_dark"], (bx, by), 8)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_mid"], (bx, by), 5)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_light"], (bx, by), 3)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["white"], (bx, by, 1, 1))

            # Spiraling energy around the ball
            for i in range(8):
                angle = phase * 8 + i * math.pi / 4
                for r_step in (9, 11):
                    sx = bx + int(math.cos(angle) * r_step)
                    sy = by + int(math.sin(angle) * r_step)
                    pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_hot"], (sx, sy, 1, 1))

            # Big impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 28)
                alpha = _NS_garumenshi._alpha(240 * (1 - st))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                          (tx, ty), radius + 3, 3)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                          (tx, ty), radius, 3)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_mid"], alpha),
                                          (tx, ty), max(1, radius - 5), 2)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                          (tx, ty), max(1, radius - 12), 1)
                # Radial burst
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["chakra_hot"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL W - TOAD SUMMON (Gamabunta stomp)
    # ============================================================
    def _draw_toad_ground(surface, boss, x, y, timer, phase):
        """Ground crack/dust from toad slam."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Summon smoke ring
            t = progress / 0.3
            r = int(t * 40)
            alpha = _NS_garumenshi._alpha(200 * (1 - t))
            for i in range(3):
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["hair_dark"], alpha),
                                          (x, y + 42), r - i * 3, 3)
        else:
            # Dust rings after landing
            t = (progress - 0.3) / 0.7
            r = int(30 + t * 40)
            alpha = _NS_garumenshi._alpha(180 * (1 - t))
            pygame.draw.ellipse(surface, (*_NS_garumenshi.PALETTE["toad_darkest"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_garumenshi.PALETTE["toad_dark"], alpha),
                                (x - r + 4, y + 42 - r // 3, r * 2 - 8, r * 2 // 3 - 4), 2)

            # Ground cracks
            for i in range(6):
                angle = i * math.pi / 3
                sx = x + int(math.cos(angle) * r * 0.5)
                sy = y + 44 + int(math.sin(angle) * r * 0.25)
                ex = x + int(math.cos(angle) * r * 0.9)
                ey = y + 44 + int(math.sin(angle) * r * 0.45)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["shadow_deep"], alpha),
                                 (sx, sy), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["fire_dark"], alpha),
                                 (sx, sy), (ex, ey), 1)

    def _draw_gamabunta(surface, boss, x, y, timer, phase):
        """Big red toad Gamabunta appearing behind boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.2:
            # Summoning smoke only
            t = progress / 0.2
            for i in range(8):
                angle = i * math.pi / 4 + phase
                sr = int(30 * (1 - t))
                sx = x + int(math.cos(angle) * sr)
                sy = y + int(math.sin(angle) * sr * 0.4)
                _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["hair_dark"],
                                          (sx, sy), 8)
                _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["hair_mid"],
                                          (sx, sy), 6)
            return

        # Scale up toad
        scale = min(1.0, (progress - 0.2) / 0.3)
        if progress > 0.7:
            scale = 1.0 - (progress - 0.7) / 0.3 * 0.3

        # Toad body - big oval
        tx = x - boss.direction * 30
        ty = y + 10
        w = int(35 * scale)
        h = int(28 * scale)

        # Body
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                            (tx - w + 2, ty - h + 2, w * 2, h * 2))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_darkest"],
                            (tx - w, ty - h, w * 2, h * 2))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_dark"],
                            (tx - w + 2, ty - h + 2, w * 2 - 4, h * 2 - 4))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_mid"],
                            (tx - w + 4, ty - h + 4, w * 2 - 8, h * 2 - 8))

        # Belly
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_belly"],
                            (tx - w + 6, ty - h // 2, w * 2 - 12, h))

        # Toad head bulge on top
        hw = int(22 * scale)
        hh = int(15 * scale)
        htx = tx + int(boss.direction * 8 * scale)
        hty = ty - h + 4
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                            (htx - hw + 2, hty - hh + 2, hw * 2, hh * 2))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_darkest"],
                            (htx - hw, hty - hh, hw * 2, hh * 2))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_dark"],
                            (htx - hw + 2, hty - hh + 2, hw * 2 - 4, hh * 2 - 4))
        pygame.draw.ellipse(surface, _NS_garumenshi.PALETTE["toad_mid"],
                            (htx - hw + 4, hty - hh + 4, hw * 2 - 8, hh * 2 - 8))

        # Eyes bumps (2)
        for eye_off in (-8, 8):
            ex = htx + int(eye_off * scale)
            ey = hty - hh + int(2 * scale)
            er = int(5 * scale)
            if er < 2:
                continue
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                                      (ex + 1, ey + 1), er)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["toad_darkest"], (ex, ey), er)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["toad_mid"], (ex, ey), er - 1)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["toad_belly"], (ex, ey - 1), max(1, er - 2))
            # Pupil
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["eye_dark"],
                             (ex, ey, max(1, er - 3), max(1, er - 2)))

        # Big mouth line
        pygame.draw.line(surface, _NS_garumenshi.PALETTE["shadow_deep"],
                         (htx - hw + 4, hty + 3),
                         (htx + hw - 4, hty + 3), 2)
        pygame.draw.line(surface, _NS_garumenshi.PALETTE["toad_darkest"],
                         (htx - hw + 4, hty + 4),
                         (htx + hw - 4, hty + 4), 1)

        # Warts
        for wart_i in range(4):
            wx = tx + int((wart_i - 2) * 8 * scale)
            wy = ty - int(h * 0.6) + int((wart_i % 2) * 4 * scale)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["toad_darkest"], (wx, wy), 2)
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["toad_light"], (wx, wy - 1, 1, 1))

    # ============================================================
    # SKILL E - OIL SHOT (arcing fireball)
    # ============================================================
    def _draw_oil_ground(surface, boss, x, y, timer, phase):
        """Burning oil pool at target."""
        tx, ty = _NS_garumenshi._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Only show pool after impact (progress > 0.4)
        if progress < 0.4:
            return

        t = (progress - 0.4) / 0.6
        r = int(45 * min(1.0, t * 3))
        if r < 3:
            return

        pygame.draw.ellipse(surface, (*_NS_garumenshi.PALETTE["fire_darkest"], 220),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface, (*_NS_garumenshi.PALETTE["fire_dark"], 200),
                            (tx - r + 3, ty - r // 3 + 2, r * 2 - 6, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface, (*_NS_garumenshi.PALETTE["fire_mid"], 180),
                            (tx - r + 8, ty - r // 3 + 4, r * 2 - 16, r * 2 // 3 - 8))

    def _draw_oil_shot_skill(surface, boss, x, y, timer, phase):
        """Arcing oil ball projectile that explodes."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_garumenshi._target_position(boss, x, y)

        if progress < 0.2:
            # Wind-up (charging in mouth)
            t = progress / 0.2
            mx = x + facing * 12
            my = y - 14
            cr = int(2 + t * 4)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_garumenshi._alpha(180 * (cr + 3 - r) / (cr + 3))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["fire_dark"], alpha),
                                          (mx, my), r)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_mid"], (mx, my), cr - 1)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_light"], (mx, my), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["fire_hot"], (mx, my, 1, 1))
            return

        if progress < 0.4:
            # Arc projectile in flight
            t = (progress - 0.2) / 0.2
            start_x = x + facing * 16
            start_y = y - 14

            bx = int(start_x + (tx - start_x) * t)
            arc_y = int(start_y + (ty - start_y) * t)
            # Arc curve (parabolic)
            arc_h = int(-40 * math.sin(t * math.pi))
            by = arc_y + arc_h

            # Fire trail
            for i in range(6):
                trail_t = max(0.0, t - i * 0.07)
                px = int(start_x + (tx - start_x) * trail_t)
                py_base = int(start_y + (ty - start_y) * trail_t)
                py = py_base + int(-40 * math.sin(trail_t * math.pi))
                alpha = _NS_garumenshi._alpha(220 - i * 30)
                size = max(1, 5 - i)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["fire_dark"], alpha),
                                          (px, py), size)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["fire_mid"], alpha),
                                          (px, py), max(1, size - 1))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["fire_light"], alpha),
                                          (px, py), max(1, size - 2))

            # Head - oil ball with flame
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_darkest"], (bx, by), 5)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_dark"], (bx, by), 4)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_mid"], (bx, by), 3)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_light"], (bx, by), 2)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["fire_hot"], (bx, by), 1)
            # Flame tail
            for i in range(4):
                fy = by - i * 2 - 2
                fx = bx + int(math.sin(phase * 4 + i) * 1)
                pygame.draw.rect(surface, _NS_garumenshi.PALETTE["fire_light"], (fx, fy, 1, 2))
                pygame.draw.rect(surface, _NS_garumenshi.PALETTE["fire_hot"], (fx, fy, 1, 1))

        else:
            # Impact - flame burst + oil pool (pool drawn in ground)
            t = (progress - 0.4) / 0.6
            # Rising flames from pool
            for i in range(12):
                flame_x = tx + int((i - 6) * 6)
                flame_h = int(15 + math.sin(phase * 3 + i) * 5) - int(t * 8)
                if flame_h <= 0:
                    continue
                alpha = _NS_garumenshi._alpha(240 * (1 - t))
                # Flame shape (tall triangle)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["fire_darkest"], alpha),
                                 (flame_x, ty), (flame_x, ty - flame_h), 3)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["fire_dark"], alpha),
                                 (flame_x, ty), (flame_x, ty - flame_h + 1), 2)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["fire_mid"], alpha),
                                 (flame_x, ty - 1), (flame_x, ty - flame_h + 3), 1)
                # Hot tip
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["fire_light"], alpha),
                                 (flame_x, ty - flame_h + 1, 1, 3))
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["fire_hot"], alpha),
                                 (flame_x, ty - flame_h + 2, 1, 2))

            # Rising embers
            for i in range(10):
                ember_t = (phase * 0.5 + i * 0.1) % 1.0
                ex = tx + int((i - 5) * 5) + int(math.sin(phase + i) * 3)
                ey = ty - int(ember_t * 25)
                alpha = _NS_garumenshi._alpha(220 * (1 - ember_t) * (1 - t))
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["fire_hot"], alpha), (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["fire_shine"], alpha), (ex, ey, 1, 1))

    # ============================================================
    # SKILL R - SAGE ART: MAHA GAMA RASEN (giant rasengan)
    # ============================================================
    def _draw_maha_rasen_skill(surface, boss, x, y, timer, phase):
        """Massive spiraling rasengan super skill."""
        facing = boss.direction
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_garumenshi._target_position(boss, x, y)

        if progress < 0.4:
            # Charging - HUGE rasengan forming in hands
            t = progress / 0.4
            cx = x + facing * 20
            cy = y - 5
            cr = int(8 + t * 20)

            # Outer glow
            for r in range(cr + 12, 0, -3):
                alpha = _NS_garumenshi._alpha(160 * (cr + 12 - r) / (cr + 12))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                          (cx, cy), r)
            for r in range(cr + 6, 0, -2):
                alpha = _NS_garumenshi._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                          (cx, cy), r)

            # Core
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_dark"], (cx, cy), cr)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_mid"], (cx, cy), cr - 3)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_light"], (cx, cy), cr - 6)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_hot"], (cx, cy), max(1, cr - 10))
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_shine"], (cx, cy), max(1, cr - 14))
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["white"], (cx, cy, 2, 2))

            # Spiraling arms (multiple layers)
            for layer, thickness in [(0, 2), (1, 1)]:
                for i in range(8):
                    angle = phase * 8 + i * math.pi / 4 + layer * 0.2
                    for r_step in range(cr - 2, cr + 6):
                        sx = cx + int(math.cos(angle) * r_step)
                        sy = cy + int(math.sin(angle) * r_step)
                        color = _NS_garumenshi.PALETTE["chakra_hot"] if r_step % 2 == 0 \
                            else _NS_garumenshi.PALETTE["chakra_light"]
                        pygame.draw.rect(surface, color, (sx, sy, thickness, thickness))

            # Extra energy shockwaves
            for i in range(4):
                sw_r = cr + 15 + i * 5 + int(math.sin(phase * 2 + i) * 3)
                alpha = _NS_garumenshi._alpha(120 - i * 25)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                          (cx, cy), sw_r, 1)

        elif progress < 0.75:
            # Launch - massive rasengan flying
            t = (progress - 0.4) / 0.35
            start_x = x + facing * 30
            start_y = y - 5
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Massive trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_garumenshi._alpha(240 - i * 18)
                size = max(2, 18 - i * 2)

                for r_layer in [(size, "chakra_darkest"),
                                (size - 2, "chakra_dark"),
                                (size - 5, "chakra_mid"),
                                (size - 8, "chakra_light")]:
                    r, col = r_layer
                    if r > 0:
                        _NS_garumenshi._aacircle(surface,
                                                  (*_NS_garumenshi.PALETTE[col], alpha),
                                                  (px, py), r)

                # Trail sparkles
                if i < 6:
                    for s in range(4):
                        angle_s = phase * 5 + i + s * 2
                        spark_x = px + int(math.cos(angle_s) * (size + 3))
                        spark_y = py + int(math.sin(angle_s) * (size + 3))
                        pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["chakra_hot"], alpha),
                                         (spark_x, spark_y, 2, 2))

            # HUGE core ball
            for r in range(25, 3, -3):
                alpha = _NS_garumenshi._alpha(100 * (25 - r) / 25)
                _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                          (bx, by), r)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_darkest"], (bx, by), 20)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_dark"], (bx, by), 16)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_mid"], (bx, by), 11)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_light"], (bx, by), 6)
            _NS_garumenshi._aacircle(surface, _NS_garumenshi.PALETTE["chakra_shine"], (bx, by), 3)
            pygame.draw.rect(surface, _NS_garumenshi.PALETTE["white"], (bx - 1, by - 1, 3, 3))

            # Spinning spirals
            for layer in range(3):
                for i in range(10):
                    angle = phase * 8 + i * math.pi / 5 + layer * 0.3
                    r_step = 18 + layer * 2
                    sx = bx + int(math.cos(angle) * r_step)
                    sy = by + int(math.sin(angle) * r_step)
                    pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_hot"], (sx, sy, 2, 2))
                    pygame.draw.rect(surface, _NS_garumenshi.PALETTE["chakra_shine"], (sx, sy, 1, 1))

        else:
            # Massive impact explosion
            t = (progress - 0.75) / 0.25
            radius = int(30 + t * 60)
            alpha = _NS_garumenshi._alpha(240 * (1 - t))

            # Concentric shockwaves
            for i in range(4):
                r_ring = radius - i * 12
                if r_ring > 0:
                    _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_darkest"], alpha),
                                              (tx, ty), r_ring + 3, 3)
                    _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_dark"], alpha),
                                              (tx, ty), r_ring, 3)
                    _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_mid"], alpha),
                                              (tx, ty), max(1, r_ring - 5), 2)
                    _NS_garumenshi._aacircle(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                              (tx, ty), max(1, r_ring - 10), 1)

            # Radial burst rays
            for i in range(20):
                angle_s = i * math.pi / 10
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.8)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["chakra_light"], alpha),
                                 (tx, ty), (ex, ey), 3)
                pygame.draw.line(surface, (*_NS_garumenshi.PALETTE["chakra_hot"], alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_garumenshi.PALETTE["chakra_shine"], alpha),
                                 (ex - 1, ey - 1, 3, 3))


# ====================================================================================================
# THORAZ - MINI BOSS
# ====================================================================================================

class _NS_thoraz:
    """Namespace thoraz - HD rendering untuk mini boss Thoraz."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (weathered warrior)
        "skin_darkest": (55, 30, 20),
        "skin_dark": (110, 65, 45),
        "skin_mid": (170, 115, 85),
        "skin_light": (220, 170, 135),
        "skin_shine": (245, 205, 170),

        # Fiery red hair/beard
        "hair_darkest": (55, 15, 5),
        "hair_dark": (130, 40, 10),
        "hair_mid": (200, 75, 20),
        "hair_light": (240, 130, 40),
        "hair_shine": (255, 180, 80),

        # Leather armor (dark brown)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (55, 35, 20),
        "leather_mid": (100, 65, 35),
        "leather_light": (155, 105, 60),
        "leather_edge": (200, 145, 90),

        # Metal armor plate (dark iron with gold accents)
        "armor_darkest": (15, 15, 20),
        "armor_dark": (40, 40, 50),
        "armor_mid": (80, 78, 90),
        "armor_light": (150, 145, 160),
        "armor_shine": (215, 210, 225),

        # Gold armor trim
        "gold_dark": (85, 55, 15),
        "gold_mid": (175, 130, 40),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 170),

        # Stone hammer head (chunky rock)
        "stone_darkest": (25, 20, 18),
        "stone_dark": (55, 45, 40),
        "stone_mid": (95, 80, 70),
        "stone_light": (155, 135, 115),
        "stone_edge": (200, 180, 160),

        # Hammer handle (wood)
        "wood_dark": (30, 20, 12),
        "wood_mid": (75, 50, 25),
        "wood_light": (130, 90, 55),

        # Fire/flame (orange-yellow signature)
        "fire_darkest": (40, 10, 0),
        "fire_dark": (110, 30, 5),
        "fire_deep": (180, 65, 15),
        "fire_mid": (240, 130, 30),
        "fire_bright": (255, 175, 50),
        "fire_light": (255, 215, 90),
        "fire_hot": (255, 235, 140),
        "fire_shine": (255, 250, 200),
        "fire_white": (255, 255, 240),

        # Eyes (fierce yellow-white)
        "eye_dark": (60, 40, 5),
        "eye_mid": (200, 150, 30),
        "eye_light": (255, 220, 100),

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
        color = _NS_thoraz._clamp(color)
        if _NS_thoraz.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_thoraz._clamp(color)
        if _NS_thoraz.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_thoraz._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 130 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thoraz(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thoraz._detect_moving(boss)
        _NS_thoraz._update_attack_anim(boss)
        attacking = getattr(boss, "_th_attack_active", False)

        # Ambient
        _NS_thoraz._draw_shadow(surface, x, y + 52)
        _NS_thoraz._draw_fire_aura(surface, x, y, pulse)
        _NS_thoraz._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "q":
            _NS_thoraz._draw_shock_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thoraz._draw_swing_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thoraz._draw_wrath_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if active_skill == "w":
            _NS_thoraz._draw_charge_afterimages(surface, boss, x, y, skill_timer)

        if attacking:
            _NS_thoraz._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_thoraz._draw_body_walk(surface, boss, x, y)
        else:
            _NS_thoraz._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_thoraz._draw_shock_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thoraz._draw_charge_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thoraz._draw_swing_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thoraz._draw_wrath_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_th_attack_active", False))

        if not active:
            if timer >= cooldown - 28:
                boss._th_attack_active = True
                boss._th_attack_frame = 0
                active = True

        if active:
            boss._th_attack_frame = int(getattr(boss, "_th_attack_frame", 0)) + 1
            attack_duration = 32
            if boss._th_attack_frame >= attack_duration:
                boss._th_attack_active = False
                boss._th_attack_frame = 0
                active = False

        attack_duration = 32
        boss._th_attack_progress = (
            min(1.0, getattr(boss, "_th_attack_frame", 0) / attack_duration)
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
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_thoraz._draw_full_body(surface, x, y + bob,
                                   boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 0.9) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_thoraz._draw_full_body(surface, x + sway, y + bob,
                                   boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_th_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Heavy hammer swing
        if progress < 0.4:
            # Wind-up: raise hammer HIGH
            t = progress / 0.4
            lunge = -int(t * 6) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            # SMASH DOWNWARD
            t = (progress - 0.4) / 0.25
            ease = 1 - (1 - t) ** 2
            lunge = int((-6 + ease * 22)) * boss.direction
            lift = int(4 - ease * 6)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(16 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_thoraz._draw_full_body(surface, x + lunge, y - lift,
                                   boss.direction, boss.pulse, "attack", progress)
        # Hammer impact effect (ground shockwave when hammer hits)
        _NS_thoraz._draw_basic_hammer_impact(surface, boss, x + lunge,
                                              y - lift, progress)

    # ============================================================
    # FULL BODY (bulky warrior)
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Legs
        _NS_thoraz._draw_legs(surface, cx, cy, facing, phase, action)
        # 2. BACK arm (holds nothing / behind body)
        _NS_thoraz._draw_back_arm(surface, cx, cy, facing, phase, action)
        # 3. Torso
        _NS_thoraz._draw_torso(surface, cx, cy, facing, phase)
        # 4. BEARD (behind head area — hangs down)
        _NS_thoraz._draw_beard(surface, cx, cy - 12, facing, phase)
        # 5. Head + fiery hair
        _NS_thoraz._draw_head(surface, cx, cy - 22, facing, phase)
        # 6. FRONT arm + BIG HAMMER
        _NS_thoraz._draw_front_arm_with_hammer(surface, cx, cy, facing,
                                                phase, action, atk_prog)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Bulky armored legs with metal greaves."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        for leg_i, leg_x_off in enumerate((-5, 5)):
            leg_x = cx + leg_x_off
            leg_y_top = cy + 8
            leg_y_knee = cy + 24
            leg_y_bot = cy + 44 + int((-leg_sway if leg_i == 0 else leg_sway))

            # Thigh (leather pants)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                               (leg_x + 1, leg_y_top + 1),
                               (leg_x + 1, leg_y_knee + 1), 9)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_darkest"],
                               (leg_x, leg_y_top), (leg_x, leg_y_knee), 8)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_dark"],
                               (leg_x, leg_y_top), (leg_x, leg_y_knee), 6)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_mid"],
                               (leg_x - 1, leg_y_top), (leg_x - 1, leg_y_knee), 2)

            # Greaves (metal armor)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                               (leg_x + 1, leg_y_knee + 1),
                               (leg_x + 1, leg_y_bot + 1), 9)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_darkest"],
                               (leg_x, leg_y_knee), (leg_x, leg_y_bot), 8)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_dark"],
                               (leg_x, leg_y_knee), (leg_x, leg_y_bot), 6)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_mid"],
                               (leg_x - 1, leg_y_knee), (leg_x - 1, leg_y_bot), 3)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_light"],
                               (leg_x - 2, leg_y_knee + 2),
                               (leg_x - 2, leg_y_bot - 2), 1)

            # Knee cap (with gold trim)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["shadow_deep"],
                                 (leg_x, leg_y_knee), 5)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["armor_darkest"],
                                 (leg_x, leg_y_knee), 4)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["armor_dark"],
                                 (leg_x, leg_y_knee), 3)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["gold_dark"],
                                 (leg_x, leg_y_knee), 2, 1)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["gold_mid"],
                                 (leg_x, leg_y_knee), 2)
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_shine"],
                             (leg_x, leg_y_knee - 1, 1, 1))

        # Big armored boots (sabatons)
        for leg_i, leg_x_off in enumerate((-5, 5)):
            leg_x = cx + leg_x_off
            leg_y_bot = cy + 44 + int((-leg_sway if leg_i == 0 else leg_sway))

            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["shadow_deep"],
                                (leg_x - 6, leg_y_bot - 1, 14, 7))
            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["armor_darkest"],
                                (leg_x - 5, leg_y_bot, 12, 5))
            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["armor_dark"],
                                (leg_x - 5, leg_y_bot, 12, 4))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_mid"],
                             (leg_x - 3, leg_y_bot, 7, 1))
            # Gold spike on toe
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_dark"],
                             (leg_x + 4, leg_y_bot + 1, 3, 2))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_mid"],
                             (leg_x + 4, leg_y_bot + 1, 3, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Bulky armored torso."""
        breath = math.sin(phase * 0.6) * 1

        # Wider bulky shape
        torso_pts = [
            (cx - 15, cy - 8),
            (cx - 17, cy - 2),
            (cx - 16, cy + 6),
            (cx - 10, cy + 10),
            (cx + 10, cy + 10),
            (cx + 16, cy + 6),
            (cx + 17, cy - 2),
            (cx + 15, cy - 8),
            (cx + 7, cy - 12),
            (cx - 7, cy - 12),
        ]
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in torso_pts])
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["leather_darkest"], torso_pts)

        # Leather chest
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["leather_dark"], [
            (cx - 14, cy - 6),
            (cx - 16, cy - 1),
            (cx - 15, cy + 5),
            (cx - 9, cy + 9),
            (cx + 9, cy + 9),
            (cx + 15, cy + 5),
            (cx + 16, cy - 1),
            (cx + 14, cy - 6),
            (cx + 6, cy - 10),
            (cx - 6, cy - 10),
        ])
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["leather_mid"], [
            (cx - 12, cy - 4),
            (cx - 13, cy + 2),
            (cx - 8, cy + 7),
            (cx + 8, cy + 7),
            (cx + 13, cy + 2),
            (cx + 12, cy - 4),
            (cx + 5, cy - 9),
            (cx - 5, cy - 9),
        ])

        # METAL CHEST PLATE (front center)
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["shadow_deep"],
                         (cx - 7, cy - 5, 15, 10))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_darkest"],
                         (cx - 7, cy - 5, 14, 10))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_dark"],
                         (cx - 6, cy - 4, 13, 8))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_mid"],
                         (cx - 5, cy - 3, 11, 6))
        # Chest plate highlight
        pygame.draw.line(surface, _NS_thoraz.PALETTE["armor_light"],
                         (cx - 4, cy - 3), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["armor_shine"],
                         (cx - 3, cy - 3), (cx + 3, cy - 3), 1)

        # Gold plate detail (H-shape)
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_dark"],
                         (cx - 1, cy - 4, 2, 8))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_mid"],
                         (cx - 1, cy - 4, 2, 7))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_shine"],
                         (cx, cy - 3, 1, 5))

        # Chest bolts (rivets)
        for bolt_x, bolt_y in [(-5, -3), (5, -3), (-5, 3), (5, 3)]:
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_darkest"],
                             (cx + bolt_x, cy + bolt_y, 1, 1))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_light"],
                             (cx + bolt_x, cy + bolt_y, 1, 1))

        # LARGE SHOULDER PAULDRONS (armored spikes)
        for shoulder_x_off, shoulder_side in [(-14, -1), (14, 1)]:
            sx = cx + shoulder_x_off
            sy = cy - 8

            # Shadow
            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["shadow_deep"],
                                (sx - 6, sy - 5, 14, 12))
            # Base pauldron
            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["armor_darkest"],
                                (sx - 6, sy - 5, 13, 12))
            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["armor_dark"],
                                (sx - 5, sy - 4, 11, 10))
            pygame.draw.ellipse(surface, _NS_thoraz.PALETTE["armor_mid"],
                                (sx - 4, sy - 3, 9, 8))

            # SPIKES on top (3 short spikes)
            for spike_i in range(3):
                sp_off = (spike_i - 1) * 3 * shoulder_side
                sp_x = sx + sp_off
                sp_h = 5 + (1 if spike_i == 1 else 0)
                _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["shadow_deep"], [
                    (sp_x + 1, sy - 5 - sp_h + 1),
                    (sp_x - 1, sy - 5 + 1),
                    (sp_x + 2, sy - 5 + 1),
                ])
                _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["armor_darkest"], [
                    (sp_x, sy - 5 - sp_h),
                    (sp_x - 1, sy - 5),
                    (sp_x + 2, sy - 5),
                ])
                _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["armor_dark"], [
                    (sp_x, sy - 5 - sp_h),
                    (sp_x, sy - 5),
                    (sp_x + 1, sy - 5),
                ])
                pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_light"],
                                 (sp_x, sy - 5 - sp_h, 1, 1))
                pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_shine"],
                                 (sp_x, sy - 5 - sp_h, 1, 1))

            # Pauldron highlight
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_light"],
                             (sx - 2, sy - 2, 3, 1))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["armor_shine"],
                             (sx - 1, sy - 2, 2, 1))

        # BELT with buckle
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["shadow_deep"],
                         (cx - 16, cy + 7, 33, 6))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["leather_darkest"],
                         (cx - 15, cy + 8, 31, 5))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["leather_dark"],
                         (cx - 15, cy + 8, 31, 3))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["leather_mid"],
                         (cx - 15, cy + 8, 31, 1))

        # Big center gold buckle
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["shadow_deep"],
                         (cx - 5, cy + 7, 11, 7))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_dark"],
                         (cx - 4, cy + 8, 9, 5))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_mid"],
                         (cx - 3, cy + 8, 7, 4))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_light"],
                         (cx - 2, cy + 9, 5, 2))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_shine"],
                         (cx - 1, cy + 9, 3, 1))

    def _draw_beard(surface, cx, cy, facing, phase):
        """Big bushy red beard."""
        sway = math.sin(phase * 0.5) * 1

        # Beard shape (large triangular)
        beard_pts = [
            (cx - 6, cy - 2),
            (cx - 9, cy + 4),
            (cx - 10, cy + 10),
            (cx - 8, cy + 15),
            (cx - 4 + int(sway), cy + 18),
            (cx + int(sway), cy + 20),
            (cx + 4 - int(sway), cy + 18),
            (cx + 8, cy + 15),
            (cx + 10, cy + 10),
            (cx + 9, cy + 4),
            (cx + 6, cy - 2),
        ]
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["shadow_deep"],
                         [(px + 1, py + 2) for px, py in beard_pts])
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["hair_darkest"], beard_pts)

        # Beard mid layer
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx - 8, cy + 5),
            (cx - 8, cy + 12),
            (cx - 5 + int(sway), cy + 16),
            (cx + int(sway), cy + 18),
            (cx + 5 - int(sway), cy + 16),
            (cx + 8, cy + 12),
            (cx + 8, cy + 5),
            (cx + 5, cy - 1),
        ])
        # Bright red highlights
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["hair_mid"], [
            (cx - 4, cy + 2),
            (cx - 6, cy + 7),
            (cx - 5, cy + 13),
            (cx + int(sway), cy + 15),
            (cx + 5, cy + 13),
            (cx + 6, cy + 7),
            (cx + 4, cy + 2),
        ])
        # Bright center streaks
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_light"],
                         (cx - 2, cy + 4), (cx - 1 + int(sway), cy + 15), 1)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_light"],
                         (cx + 2, cy + 4), (cx + 1 + int(sway), cy + 15), 1)
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["hair_shine"],
                         (cx - 1, cy + 6, 2, 1))

        # Small braids/strands at bottom
        for braid_i in range(3):
            bx_off = (braid_i - 1) * 3
            braid_x = cx + bx_off + int(sway)
            braid_y_top = cy + 16
            braid_y_bot = cy + 20 + braid_i
            pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_dark"],
                             (braid_x, braid_y_top),
                             (braid_x + int(sway * 0.5), braid_y_bot), 2)
            pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_mid"],
                             (braid_x, braid_y_top),
                             (braid_x + int(sway * 0.5), braid_y_bot), 1)

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with WILD FIERY RED HAIR (mohawk-like)."""
        # ==== WILD FIERY HAIR (upward spikes like flames) ====
        # Multiple hair spikes rising up like flames
        hair_spikes = [
            (-6, -5, 8, 0.3),
            (-3, -8, 12, 0.5),
            (-1, -10, 14, 0.7),   # tallest
            (2, -9, 13, 0.4),
            (5, -6, 10, 0.6),
            (-8, -2, 6, 0.2),
            (7, -2, 6, 0.8),
        ]

        for base_off_x, base_off_y, spike_h, phase_off in hair_spikes:
            base_x = cx + base_off_x
            base_y = cy + base_off_y
            # Animate hair wobble
            wobble_x = math.sin(phase * 1.2 + phase_off * 3) * 1.5
            wobble_h = math.sin(phase * 0.8 + phase_off * 2) * 1.5
            tip_x = base_x + int(wobble_x)
            tip_y = base_y - spike_h - int(wobble_h)
            w = max(2, spike_h // 4)

            # Hair spike (flame-like shape)
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["hair_darkest"], [
                (base_x - w, base_y),
                (tip_x, tip_y),
                (base_x + w, base_y),
            ])
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["hair_dark"], [
                (base_x - w + 1, base_y),
                (tip_x, tip_y - 1),
                (base_x + w - 1, base_y),
            ])
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["hair_mid"], [
                (base_x - 1, base_y),
                (tip_x, tip_y - 2),
                (base_x + 1, base_y),
            ])
            # Bright tip
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["hair_light"],
                             (tip_x, tip_y - 2, 1, 2))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["hair_shine"],
                             (tip_x, tip_y - 2, 1, 1))

        # ==== FACE (weathered, angry) ====
        face_pts = [
            (cx - 6, cy + 5),
            (cx - 7, cy - 2),
            (cx - 5, cy - 6),
            (cx + 5, cy - 6),
            (cx + 7, cy - 2),
            (cx + 6, cy + 5),
        ]
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["skin_dark"], face_pts)
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["skin_mid"], [
            (cx - 5, cy + 4),
            (cx - 6, cy - 2),
            (cx - 4, cy - 5),
            (cx + 4, cy - 5),
            (cx + 6, cy - 2),
            (cx + 5, cy + 4),
        ])
        # Skin highlights (cheekbones)
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["skin_light"],
                         (cx - 4, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["skin_light"],
                         (cx + 2, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["skin_shine"],
                         (cx - 4, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["skin_shine"],
                         (cx + 3, cy - 2, 1, 1))

        # Angry FURROWED BROW (thick red eyebrows)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_darkest"],
                         (cx - 5, cy - 4), (cx - 2, cy - 5), 2)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_dark"],
                         (cx - 5, cy - 4), (cx - 2, cy - 5), 1)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_darkest"],
                         (cx + 2, cy - 5), (cx + 5, cy - 4), 2)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_dark"],
                         (cx + 2, cy - 5), (cx + 5, cy - 4), 1)

        # ==== EYES (fierce yellow, glowing) ====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            # Eye white
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["skin_shine"],
                             (ex - 1, ey, 2, 1))
            # Yellow iris
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["eye_dark"],
                             (ex, ey, 1, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_thoraz._alpha(90 * (3 - r) / 3 * eye_pulse)
                _NS_thoraz._aacircle(surface,
                                     (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                     (ex, ey), r)
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["white"],
                             (ex, ey, 1, 1))

        # NOSE (subtle line)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["skin_dark"],
                         (cx, cy - 2), (cx, cy + 1), 1)

        # MUSTACHE (part of beard, curved)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_darkest"],
                         (cx - 4, cy + 3), (cx + 4, cy + 3), 2)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_dark"],
                         (cx - 4, cy + 3), (cx + 4, cy + 3), 1)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["hair_mid"],
                         (cx - 3, cy + 3), (cx + 3, cy + 3), 1)

        # Rising ember sparks around head
        for i in range(4):
            e_t = (phase * 1.0 + i * 0.25) % 1.0
            e_angle = i * math.pi / 2 + phase * 0.3
            e_r = 12 + int(e_t * 6)
            ex = cx + int(math.cos(e_angle) * e_r)
            ey = cy - 8 - int(e_t * 10)
            alpha = _NS_thoraz._alpha(220 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                             (ex, ey, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm (hidden or free)."""
        sway = math.sin(phase * 0.9) * 1
        back_shoulder_x = cx - facing * 12
        back_shoulder_y = cy - 6
        back_hand_x = back_shoulder_x - facing * 4 + int(sway)
        back_hand_y = cy + 10

        # Upper arm (armored)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                           (back_shoulder_x + 1, back_shoulder_y + 1),
                           (back_hand_x + 1, back_hand_y + 1), 7)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_darkest"],
                           (back_shoulder_x, back_shoulder_y),
                           (back_hand_x, back_hand_y), 6)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_dark"],
                           (back_shoulder_x, back_shoulder_y),
                           (back_hand_x, back_hand_y), 4)
        # Fist (bare) - clenched
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["shadow_deep"],
                             (back_hand_x, back_hand_y), 4)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["leather_dark"],
                             (back_hand_x, back_hand_y), 3)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["skin_dark"],
                             (back_hand_x, back_hand_y), 2)

    def _draw_front_arm_with_hammer(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm holding the GIANT STONE HAMMER."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 12
        front_shoulder_y = cy - 6

        # Hammer angle
        if action == "attack":
            if atk_prog < 0.4:
                # Wind-up: hammer raised HIGH above head
                t = atk_prog / 0.4
                hammer_angle = -math.pi * 0.3 - t * math.pi * 0.85
                hand_off_x = facing * int(-8 - t * 4)
                hand_off_y = int(-8 - t * 10)
            elif atk_prog < 0.65:
                # SMASH DOWNWARD (heavy)
                t = (atk_prog - 0.4) / 0.25
                ease = 1 - (1 - t) ** 2
                hammer_angle = -math.pi * 1.15 + ease * math.pi * 1.25
                hand_off_x = facing * int(-12 + ease * 28)
                hand_off_y = int(-18 + ease * 22)
            else:
                # Recovery (hammer down)
                t = (atk_prog - 0.65) / 0.35
                hammer_angle = math.pi * 0.1 - t * math.pi * 0.1
                hand_off_x = facing * int(16 - t * 10)
                hand_off_y = int(4 - t * 4)
        elif action == "walk":
            # Hammer resting on shoulder
            hammer_angle = -math.pi * 0.4 + math.sin(phase) * 0.05
            hand_off_x = facing * 6
            hand_off_y = int(0 + sway)
        else:
            # IDLE: hammer resting on shoulder
            hammer_angle = -math.pi * 0.4 + math.sin(phase * 0.4) * 0.02
            hand_off_x = facing * 6
            hand_off_y = int(0 - sway)

        front_hand_x = front_shoulder_x + hand_off_x
        front_hand_y = front_shoulder_y + hand_off_y

        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 3
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # Upper arm (armored)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                           (front_shoulder_x + 1, front_shoulder_y + 1),
                           (elbow_x + 1, elbow_y + 1), 7)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_darkest"],
                           (front_shoulder_x, front_shoulder_y),
                           (elbow_x, elbow_y), 6)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_dark"],
                           (front_shoulder_x, front_shoulder_y),
                           (elbow_x, elbow_y), 4)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_mid"],
                           (front_shoulder_x - 1, front_shoulder_y - 1),
                           (elbow_x - 1, elbow_y - 1), 2)

        # Elbow armor
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["armor_darkest"],
                             (elbow_x, elbow_y), 4)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["armor_dark"],
                             (elbow_x, elbow_y), 3)
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_mid"],
                         (elbow_x, elbow_y, 1, 1))

        # Forearm (leather gauntlet)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                           (elbow_x + 1, elbow_y + 1),
                           (front_hand_x + 1, front_hand_y + 1), 6)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_darkest"],
                           (elbow_x, elbow_y),
                           (front_hand_x, front_hand_y), 5)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_dark"],
                           (elbow_x, elbow_y),
                           (front_hand_x, front_hand_y), 3)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_mid"],
                           (elbow_x - 1, elbow_y - 1),
                           (front_hand_x - 1, front_hand_y - 1), 1)

        # Fist (large, gripping hammer)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["shadow_deep"],
                             (front_hand_x, front_hand_y), 5)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["leather_darkest"],
                             (front_hand_x, front_hand_y), 4)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["leather_dark"],
                             (front_hand_x, front_hand_y), 3)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["leather_mid"],
                             (front_hand_x - 1, front_hand_y - 1), 2)

        # HAMMER
        _NS_thoraz._draw_giant_hammer(surface, front_hand_x, front_hand_y,
                                       hammer_angle, facing, phase, action)

    def _draw_giant_hammer(surface, hand_x, hand_y, angle, facing, phase, action):
        """MASSIVE stone hammer with wooden handle."""
        actual_angle = angle if facing > 0 else math.pi - angle

        # Hammer handle length (forward from hand)
        handle_len = 26
        # Head position (top end)
        head_x = hand_x + int(math.cos(actual_angle) * handle_len)
        head_y = hand_y + int(math.sin(actual_angle) * handle_len)

        # Handle bottom (behind hand)
        butt_len = 8
        butt_x = hand_x - int(math.cos(actual_angle) * butt_len)
        butt_y = hand_y - int(math.sin(actual_angle) * butt_len)

        perp_x = -math.sin(actual_angle)
        perp_y = math.cos(actual_angle)

        # WOODEN HANDLE
        # Shadow
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                           (butt_x + 2, butt_y + 2),
                           (head_x + 2, head_y + 2), 5)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["wood_dark"],
                           (butt_x, butt_y), (head_x, head_y), 5)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["wood_mid"],
                           (butt_x, butt_y), (head_x, head_y), 3)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["wood_light"],
                           (butt_x - int(perp_x), butt_y - int(perp_y)),
                           (head_x - int(perp_x), head_y - int(perp_y)), 1)

        # Leather wrapping on handle (multiple bands)
        for wrap_t in (0.15, 0.4, 0.65, 0.85):
            wx = int(butt_x + (head_x - butt_x) * wrap_t)
            wy = int(butt_y + (head_y - butt_y) * wrap_t)
            wa = (wx + int(perp_x * 3), wy + int(perp_y * 3))
            wb = (wx - int(perp_x * 3), wy - int(perp_y * 3))
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_darkest"],
                               wa, wb, 3)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_dark"],
                               wa, wb, 2)
            _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["leather_mid"],
                               wa, wb, 1)

        # HAMMER HEAD (giant stone block)
        head_size = 14
        # Perpendicular offsets for the head's rectangular shape
        head_perp = 8

        # Head positions (rectangular block perpendicular to handle)
        h1 = (head_x + int(perp_x * head_perp - math.cos(actual_angle) * head_size // 2),
              head_y + int(perp_y * head_perp - math.sin(actual_angle) * head_size // 2))
        h2 = (head_x + int(perp_x * head_perp + math.cos(actual_angle) * head_size // 2),
              head_y + int(perp_y * head_perp + math.sin(actual_angle) * head_size // 2))
        h3 = (head_x - int(perp_x * head_perp + math.cos(actual_angle) * -head_size // 2),
              head_y - int(perp_y * head_perp + math.sin(actual_angle) * -head_size // 2))
        h4 = (head_x - int(perp_x * head_perp - math.cos(actual_angle) * -head_size // 2),
              head_y - int(perp_y * head_perp - math.sin(actual_angle) * -head_size // 2))

        # Adjust to make a proper rectangular hammer head
        h1 = (head_x - int(math.cos(actual_angle) * head_size // 2) +
              int(perp_x * head_perp),
              head_y - int(math.sin(actual_angle) * head_size // 2) +
              int(perp_y * head_perp))
        h2 = (head_x + int(math.cos(actual_angle) * head_size // 2) +
              int(perp_x * head_perp),
              head_y + int(math.sin(actual_angle) * head_size // 2) +
              int(perp_y * head_perp))
        h3 = (head_x + int(math.cos(actual_angle) * head_size // 2) -
              int(perp_x * head_perp),
              head_y + int(math.sin(actual_angle) * head_size // 2) -
              int(perp_y * head_perp))
        h4 = (head_x - int(math.cos(actual_angle) * head_size // 2) -
              int(perp_x * head_perp),
              head_y - int(math.sin(actual_angle) * head_size // 2) -
              int(perp_y * head_perp))

        head_pts = [h1, h2, h3, h4]

        # Shadow of hammer head
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["shadow_deep"],
                         [(px + 3, py + 3) for px, py in head_pts])
        # Base stone
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["stone_darkest"], head_pts)

        # Inner shading (offset polygon)
        inner_pts = [
            (h1[0] + int(math.cos(actual_angle) * 2) - int(perp_x * 1),
             h1[1] + int(math.sin(actual_angle) * 2) - int(perp_y * 1)),
            (h2[0] - int(math.cos(actual_angle) * 2) - int(perp_x * 1),
             h2[1] - int(math.sin(actual_angle) * 2) - int(perp_y * 1)),
            (h3[0] - int(math.cos(actual_angle) * 2) + int(perp_x * 1),
             h3[1] - int(math.sin(actual_angle) * 2) + int(perp_y * 1)),
            (h4[0] + int(math.cos(actual_angle) * 2) + int(perp_x * 1),
             h4[1] + int(math.sin(actual_angle) * 2) + int(perp_y * 1)),
        ]
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["stone_dark"], inner_pts)
        # Mid stone
        _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["stone_mid"], [
            (int((h1[0] + inner_pts[0][0]) / 2), int((h1[1] + inner_pts[0][1]) / 2)),
            (int((h2[0] + inner_pts[1][0]) / 2), int((h2[1] + inner_pts[1][1]) / 2)),
            (int((h3[0] + inner_pts[2][0]) / 2), int((h3[1] + inner_pts[2][1]) / 2)),
            (int((h4[0] + inner_pts[3][0]) / 2), int((h4[1] + inner_pts[3][1]) / 2)),
        ])

        # Top edge highlight (bright side)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["stone_light"],
                         h1, h2, 1)
        pygame.draw.line(surface, _NS_thoraz.PALETTE["stone_edge"],
                         (int((h1[0] + h2[0]) / 2), int((h1[1] + h2[1]) / 2)),
                         h2, 1)

        # Cracks on hammer head (stone texture)
        crack_center = (int(sum(p[0] for p in head_pts) / 4),
                        int(sum(p[1] for p in head_pts) / 4))
        for crack_i in range(3):
            ca = crack_i * math.pi / 3 + actual_angle
            cx_end = crack_center[0] + int(math.cos(ca) * 4)
            cy_end = crack_center[1] + int(math.sin(ca) * 4)
            pygame.draw.line(surface, _NS_thoraz.PALETTE["stone_darkest"],
                             crack_center, (cx_end, cy_end), 1)

        # Metal band around handle where it meets hammer head
        band_x = head_x - int(math.cos(actual_angle) * 4)
        band_y = head_y - int(math.sin(actual_angle) * 4)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["shadow_deep"],
                           (band_x + int(perp_x * 4), band_y + int(perp_y * 4)),
                           (band_x - int(perp_x * 4), band_y - int(perp_y * 4)), 4)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["armor_darkest"],
                           (band_x + int(perp_x * 4), band_y + int(perp_y * 4)),
                           (band_x - int(perp_x * 4), band_y - int(perp_y * 4)), 3)
        _NS_thoraz._aaline(surface, _NS_thoraz.PALETTE["gold_mid"],
                           (band_x + int(perp_x * 4), band_y + int(perp_y * 4)),
                           (band_x - int(perp_x * 4), band_y - int(perp_y * 4)), 1)

        # GLOWING FIRE CRACKS on hammer head (like image)
        # Add fire-lit cracks that pulse
        pulse_intensity = math.sin(phase * 3) * 0.3 + 0.7
        for crack_i, (ca_off, cr_len) in enumerate([
            (0.3, 5), (-0.5, 4), (1.2, 3),
        ]):
            crack_a = actual_angle + math.pi / 2 + ca_off
            c_start = crack_center
            c_end = (crack_center[0] + int(math.cos(crack_a) * cr_len),
                     crack_center[1] + int(math.sin(crack_a) * cr_len))
            pygame.draw.line(surface,
                             (*_NS_thoraz.PALETTE["fire_deep"],
                              _NS_thoraz._alpha(220 * pulse_intensity)),
                             c_start, c_end, 2)
            pygame.draw.line(surface,
                             (*_NS_thoraz.PALETTE["fire_bright"],
                              _NS_thoraz._alpha(255 * pulse_intensity)),
                             c_start, c_end, 1)
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_hot"],
                             (c_end[0], c_end[1], 1, 1))

        # Small fire glow on hammer surface
        for r in range(5, 0, -1):
            alpha = _NS_thoraz._alpha(80 * (5 - r) / 5 * pulse_intensity)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                 crack_center, r)

        # Handle butt cap
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["armor_darkest"],
                             (butt_x, butt_y), 3)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["gold_mid"],
                             (butt_x, butt_y), 2)
        pygame.draw.rect(surface, _NS_thoraz.PALETTE["gold_shine"],
                         (butt_x, butt_y, 1, 1))

    # ============================================================
    # BASIC ATTACK — HAMMER IMPACT SHOCKWAVE
    # ============================================================
    def _draw_basic_hammer_impact(surface, boss, x, y, progress):
        """Fire shockwave when hammer smashes ground."""
        # Only during smash phase and after
        if progress < 0.6 or progress > 0.9:
            return

        facing = boss.direction
        if progress < 0.75:
            t = (progress - 0.6) / 0.15
        else:
            t = 1 - (progress - 0.75) / 0.15
        intensity = math.sin(t * math.pi)

        # Impact point (in front of boss where hammer lands)
        impact_x = x + facing * 30
        impact_y = y + 40

        # Expanding fire ring
        r = int(15 + t * 25)
        alpha = _NS_thoraz._alpha(240 * intensity)
        pygame.draw.ellipse(surface,
                            (*_NS_thoraz.PALETTE["fire_darkest"], alpha),
                            (impact_x - r, impact_y - r // 3,
                             r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface,
                            (*_NS_thoraz.PALETTE["fire_dark"], alpha),
                            (impact_x - r + 2, impact_y - r // 3 + 1,
                             r * 2 - 4, r * 2 // 3 - 2), 3)
        pygame.draw.ellipse(surface,
                            (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                            (impact_x - r + 5, impact_y - r // 3 + 3,
                             r * 2 - 10, r * 2 // 3 - 6), 2)
        pygame.draw.ellipse(surface,
                            (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                            (impact_x - r + 8, impact_y - r // 3 + 5,
                             r * 2 - 16, r * 2 // 3 - 10), 1)

        # Ground cracks radiating outward
        for i in range(6):
            crack_angle = i * math.pi / 3
            crack_end_x = impact_x + int(math.cos(crack_angle) * r * 0.8)
            crack_end_y = impact_y + int(math.sin(crack_angle) * r * 0.3)
            pygame.draw.line(surface,
                             (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                             (impact_x, impact_y), (crack_end_x, crack_end_y), 2)
            pygame.draw.line(surface,
                             (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                             (impact_x, impact_y), (crack_end_x, crack_end_y), 1)

        # Debris and sparks flying up
        for i in range(10):
            sp_angle = i * math.pi / 5
            sp_r = int(15 + t * 20)
            sp_x = impact_x + int(math.cos(sp_angle) * sp_r)
            sp_y = impact_y + int(math.sin(sp_angle) * sp_r) - int(t * 15)
            pygame.draw.rect(surface,
                             (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                             (sp_x, sp_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_thoraz.PALETTE["fire_shine"], alpha),
                             (sp_x, sp_y, 1, 1))

        # Bright center flash
        for lr in range(8, 0, -1):
            a = _NS_thoraz._alpha(200 * (8 - lr) / 8 * intensity)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_light"], a),
                                 (impact_x, impact_y), lr)

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 180), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_fire_aura(surface, x, y, phase):
        """Fiery aura."""
        pulse = math.sin(phase * 0.7) * 0.3 + 0.7

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_thoraz._alpha((85 - radius) * 0.9 * pulse)
            if alpha > 0:
                _NS_thoraz._aacircle(aura,
                                     (*_NS_thoraz.PALETTE["fire_dark"], alpha),
                                     (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_thoraz._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_thoraz._aacircle(aura,
                                     (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                                     (100, 85), radius)
        for radius in range(28, 5, -3):
            alpha = _NS_thoraz._alpha((28 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_thoraz._aacircle(aura,
                                     (*_NS_thoraz.PALETTE["fire_mid"], alpha),
                                     (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))

        # Rising embers
        for i in range(10):
            e_t = (phase * 0.5 + i * 0.1) % 1.0
            e_angle = i * math.pi / 5 + phase * 0.2
            e_r = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(e_angle) * e_r)
            sy = y + 5 - int(e_t * 40)
            alpha = _NS_thoraz._alpha(240 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fire ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thoraz.PALETTE["fire_darkest"], 220),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_thoraz.PALETTE["fire_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_thoraz.PALETTE["fire_deep"], 200),
                            (25, 21, 110, 16), 1)

        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_thoraz.PALETTE["fire_bright"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_thoraz.PALETTE["fire_hot"],
                                 _NS_thoraz._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — MOUNTAIN SHOCK (ground smash + shockwave)
    # ============================================================
    def _draw_shock_ground(surface, boss, x, y, timer, phase):
        """Cone-shaped shockwave forward from boss."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wave travels forward
        max_dist = 180
        current_dist = int(max_dist * min(1.0, progress * 1.5))

        # Cone of ground cracks
        base_x = x + facing * 30
        base_y = y + 44

        # Multiple cracks in cone shape
        for i in range(9):
            angle_off = (i - 4) * 0.15
            end_x = base_x + facing * int(math.cos(angle_off) * current_dist)
            end_y = base_y + int(math.sin(angle_off) * current_dist * 0.4)

            # Zigzag crack
            steps = 6
            prev = (base_x, base_y)
            for step in range(1, steps + 1):
                tt = step / steps
                sx = int(base_x + (end_x - base_x) * tt +
                         math.sin(phase * 2 + i + step) * 3)
                sy = int(base_y + (end_y - base_y) * tt)

                alpha = _NS_thoraz._alpha(230 * (1 - tt * 0.4))

                pygame.draw.line(surface,
                                 (*_NS_thoraz.PALETTE["fire_darkest"], alpha),
                                 prev, (sx, sy), 4)
                pygame.draw.line(surface,
                                 (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                                 prev, (sx, sy), 2)
                pygame.draw.line(surface,
                                 (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                 prev, (sx, sy), 1)
                prev = (sx, sy)

    def _draw_shock_fg(surface, boss, x, y, timer, phase):
        """Ground pillars and eruptions."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        max_dist = 180
        current_dist = int(max_dist * min(1.0, progress * 1.5))

        base_x = x + facing * 30
        base_y = y + 44

        # Rising rock pillars in cone
        for i in range(8):
            angle_off = (i - 3.5) * 0.15
            dist = 25 + i * 18
            if dist > current_dist:
                break

            px = base_x + facing * int(math.cos(angle_off) * dist)
            py_base = base_y + int(math.sin(angle_off) * dist * 0.4)

            # Rise animation
            rise_t = min(1.0, (current_dist - dist) / 30)
            pillar_h = int(15 * rise_t + math.sin(phase * 2 + i) * 2)

            if pillar_h < 3:
                continue

            # Rock pillar
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["shadow_deep"], [
                (px + 1, py_base - pillar_h + 1),
                (px - 4, py_base + 1),
                (px + 4, py_base + 1),
            ])
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["stone_darkest"], [
                (px, py_base - pillar_h),
                (px - 4, py_base),
                (px + 4, py_base),
            ])
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["stone_dark"], [
                (px, py_base - pillar_h),
                (px - 3, py_base),
                (px + 3, py_base),
            ])
            _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["stone_mid"], [
                (px, py_base - pillar_h),
                (px - 1, py_base),
                (px + 1, py_base),
            ])
            # Bright top
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["stone_edge"],
                             (px, py_base - pillar_h, 1, 1))

            # Fire glow at base
            for glow_r in range(4, 0, -1):
                alpha = _NS_thoraz._alpha(150 * (4 - glow_r) / 4)
                _NS_thoraz._aacircle(surface,
                                     (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                     (px, py_base), glow_r)

            # Fire tongue from pillar top
            if rise_t > 0.5:
                for f_i in range(2):
                    fw_x = int(math.sin(phase * 3 + i + f_i) * 2)
                    fw_h = int(4 + math.sin(phase * 2 + i) * 2)
                    _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["fire_deep"], [
                        (px - 1, py_base - pillar_h),
                        (px + fw_x, py_base - pillar_h - fw_h),
                        (px + 1, py_base - pillar_h),
                    ])
                    _NS_thoraz._poly(surface, _NS_thoraz.PALETTE["fire_bright"], [
                        (px, py_base - pillar_h),
                        (px + fw_x, py_base - pillar_h - fw_h + 1),
                        (px, py_base - pillar_h),
                    ])
                    pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_hot"],
                                     (px + fw_x, py_base - pillar_h - fw_h, 1, 1))

    # ============================================================
    # SKILL W — SEARING CHARGE (dash with fire trail)
    # ============================================================
    def _draw_charge_afterimages(surface, boss, x, y, timer):
        """Motion afterimages behind boss during charge."""
        facing = boss.direction
        for i in range(5):
            ghost_x = x - facing * (i + 1) * 14
            alpha = _NS_thoraz._alpha(120 - i * 20)

            # Ghost silhouette
            ghost_pts = [
                (ghost_x - 10, y - 10),
                (ghost_x - 12, y),
                (ghost_x - 10, y + 12),
                (ghost_x + 10, y + 12),
                (ghost_x + 12, y),
                (ghost_x + 10, y - 10),
            ]
            _NS_thoraz._poly(surface,
                             (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                             ghost_pts)
            _NS_thoraz._poly(surface,
                             (*_NS_thoraz.PALETTE["fire_bright"], alpha // 2),
                             [(p[0], p[1] + 1) for p in ghost_pts])

    def _draw_charge_fg(surface, boss, x, y, timer, phase):
        """Fire trail and dash lines forward."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Fire trail behind boss (comet-like)
        trail_length = 80
        for i in range(15):
            trail_t = i / 15
            trail_x = x - facing * int(trail_t * trail_length)
            trail_y = y + int(math.sin(phase * 3 + i) * 4)
            alpha = _NS_thoraz._alpha(230 * (1 - trail_t))
            size = max(1, 6 - i // 3)

            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                                 (trail_x, trail_y), size + 1)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                 (trail_x, trail_y), size)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                                 (trail_x, trail_y), max(1, size - 2))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_shine"],
                             (trail_x, trail_y, 1, 1))

        # Speed lines (horizontal streaks)
        for i in range(8):
            line_t = (phase * 3 + i * 0.13) % 1.0
            line_x = x - facing * int(line_t * trail_length)
            line_y = y - 8 + i * 3
            line_alpha = _NS_thoraz._alpha(240 * (1 - line_t))
            pygame.draw.line(surface,
                             (*_NS_thoraz.PALETTE["fire_bright"], line_alpha),
                             (line_x, line_y),
                             (line_x - facing * 8, line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_thoraz.PALETTE["fire_hot"], line_alpha),
                             (line_x, line_y),
                             (line_x - facing * 6, line_y), 1)

        # Ground fire trail at feet
        for i in range(10):
            trail_t = i / 10
            trail_x = x - facing * int(trail_t * trail_length)
            trail_y = y + 46
            alpha = _NS_thoraz._alpha(200 * (1 - trail_t))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                                (trail_x - 12, trail_y - 4, 24, 8))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                (trail_x - 8, trail_y - 3, 16, 6))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                                (trail_x - 4, trail_y - 2, 8, 4))

    # ============================================================
    # SKILL E — SWINGING SMASH (360° hammer swing)
    # ============================================================
    def _draw_swing_ground(surface, boss, x, y, timer, phase):
        """Circular ground crater."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_dark"], 200),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_deep"], 180),
                                (x - r + 8, y + 40 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_swing_fg(surface, boss, x, y, timer, phase):
        """360° hammer swing arc."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 50  # swing radius
        # Swing angle progresses full 360
        swing_angle_start = -math.pi
        swing_angle_end = math.pi
        current_swing_angle = swing_angle_start + progress * math.pi * 2

        # Draw the sweep arc (fire trail behind current hammer position)
        num_arcs = 24
        for i in range(num_arcs):
            arc_offset = (i / num_arcs) * math.pi * 0.8  # 144 degrees behind hammer
            arc_angle = current_swing_angle - arc_offset

            # Position of arc segment
            arc_x = x + int(math.cos(arc_angle) * r)
            arc_y = y + int(math.sin(arc_angle) * r * 0.5)  # perspective

            alpha_falloff = 1.0 - (i / num_arcs)
            alpha = _NS_thoraz._alpha(250 * alpha_falloff)

            # Fire arc segment
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_darkest"], alpha),
                                 (arc_x, arc_y), 6)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                                 (arc_x, arc_y), 5)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                 (arc_x, arc_y), 3)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                                 (arc_x, arc_y), 2)
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_shine"],
                             (arc_x, arc_y, 1, 1))

        # Head of the swing (bright)
        head_x = x + int(math.cos(current_swing_angle) * r)
        head_y = y + int(math.sin(current_swing_angle) * r * 0.5)
        for lr in range(10, 0, -1):
            alpha = _NS_thoraz._alpha(180 * (10 - lr) / 10)
            _NS_thoraz._aacircle(surface,
                                 (*_NS_thoraz.PALETTE["fire_light"], alpha),
                                 (head_x, head_y), lr)
        _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["fire_shine"],
                             (head_x, head_y), 3)

        # Sparks flying outward
        for i in range(12):
            sp_angle = i * math.pi / 6 + phase
            sp_r = r + int(10 + math.sin(phase * 3 + i) * 5)
            sx = x + int(math.cos(sp_angle) * sp_r)
            sy = y + int(math.sin(sp_angle) * sp_r * 0.5)
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_bright"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_shine"],
                             (sx, sy, 1, 1))

    # ============================================================
    # SKILL R — WRATH BURST (massive area eruption)
    # ============================================================
    def _draw_wrath_ground(surface, boss, x, y, timer, phase):
        """Warning circle then massive crater."""
        tx, ty = _NS_thoraz._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 65
        if progress < 0.3:
            # Warning circle
            t = progress / 0.3
            actual_r = int(r * t)
            alpha = _NS_thoraz._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_darkest"], alpha),
                                (tx - actual_r, ty - actual_r // 3,
                                 actual_r * 2, actual_r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                (tx - actual_r + 3, ty - actual_r // 3 + 2,
                                 actual_r * 2 - 6, actual_r * 2 // 3 - 4), 2)
            # Warning runes
            for i in range(8):
                angle = i * math.pi / 4 + phase
                sx = tx + int(math.cos(angle) * actual_r)
                sy = ty + int(math.sin(angle) * actual_r * 0.4)
                pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_hot"],
                                 (sx, sy, 2, 2))
        else:
            # Massive crater
            t = (progress - 0.3) / 0.7
            alpha = _NS_thoraz._alpha(240 * (1 - t * 0.4))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_dark"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_deep"], alpha),
                                (tx - r + 12, ty - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12))
            pygame.draw.ellipse(surface,
                                (*_NS_thoraz.PALETTE["fire_mid"], alpha),
                                (tx - r + 20, ty - r // 3 + 10,
                                 r * 2 - 40, r * 2 // 3 - 20))

    def _draw_wrath_fg(surface, boss, x, y, timer, phase):
        """Massive eruption of fire pillars + geyser."""
        tx, ty = _NS_thoraz._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up: gathering energy at target
            t = progress / 0.3
            gather_r = int(4 + t * 15)
            for r in range(gather_r + 5, 0, -1):
                alpha = _NS_thoraz._alpha(200 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_thoraz._aacircle(surface,
                                     (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                     (tx, ty), r)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["fire_hot"],
                                 (tx, ty), max(1, gather_r - 2))
        else:
            t = (progress - 0.3) / 0.7
            intensity = math.sin(min(1.0, t * 2) * math.pi * 0.7)

            # MASSIVE CENTRAL GEYSER
            geyser_h = int(100 * intensity)
            geyser_w = 20

            layers = [
                (geyser_w, 120, _NS_thoraz.PALETTE["fire_darkest"]),
                (geyser_w - 4, 180, _NS_thoraz.PALETTE["fire_deep"]),
                (geyser_w - 8, 220, _NS_thoraz.PALETTE["fire_bright"]),
                (geyser_w - 14, 255, _NS_thoraz.PALETTE["fire_hot"]),
                (geyser_w - 18, 255, _NS_thoraz.PALETTE["fire_shine"]),
            ]
            for (w, base_a, color) in layers:
                if w < 1:
                    continue
                actual_alpha = _NS_thoraz._alpha(base_a * intensity)
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - w // 2, ty - geyser_h, w, geyser_h))

            # Rushing motion lines
            for i in range(20):
                line_t = (phase * 4 + i * 0.1) % 1.0
                line_y = ty - int(line_t * geyser_h)
                line_x = tx + int(math.sin(phase * 5 + i) * 4)
                pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_shine"],
                                 (line_x - 4, line_y, 8, 1))
                pygame.draw.rect(surface, _NS_thoraz.PALETTE["fire_white"],
                                 (line_x, line_y, 2, 1))

            # Bright top explosion
            top_y = ty - geyser_h
            for r in range(20, 3, -2):
                alpha = _NS_thoraz._alpha(180 * (20 - r) / 20 * intensity)
                _NS_thoraz._aacircle(surface,
                                     (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                     (tx, top_y), r)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["fire_hot"],
                                 (tx, top_y), 6)
            _NS_thoraz._aacircle(surface, _NS_thoraz.PALETTE["fire_shine"],
                                 (tx, top_y), 3)

            # Surrounding fire pillars around geyser
            num_pillars = 8
            for i in range(num_pillars):
                p_angle = i * math.pi * 2 / num_pillars + phase * 0.2
                p_dist = int(30 + math.sin(phase + i) * 5)
                px = tx + int(math.cos(p_angle) * p_dist)
                py_base = ty + int(math.sin(p_angle) * p_dist * 0.4)

                pillar_h = int(35 * intensity + math.sin(phase * 2 + i) * 3)
                if pillar_h < 3:
                    continue

                for layer_i in range(5):
                    layer_t = layer_i / 5
                    layer_y = py_base - int(layer_t * pillar_h)
                    layer_w = int(5 - layer_t * 3)
                    layer_alpha = _NS_thoraz._alpha(220 * (1 - layer_t))
                    pygame.draw.ellipse(surface,
                                        (*_NS_thoraz.PALETTE["fire_darkest"], layer_alpha),
                                        (px - layer_w, layer_y - 2,
                                         layer_w * 2, 4))
                    pygame.draw.ellipse(surface,
                                        (*_NS_thoraz.PALETTE["fire_deep"], layer_alpha),
                                        (px - layer_w + 1, layer_y - 1,
                                         layer_w * 2 - 2, 3))
                    pygame.draw.ellipse(surface,
                                        (*_NS_thoraz.PALETTE["fire_bright"], layer_alpha),
                                        (px - layer_w + 1, layer_y - 1,
                                         layer_w * 2 - 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_thoraz.PALETTE["fire_hot"], layer_alpha),
                                     (px, layer_y, 1, 1))

            # Debris/rocks flying out
            for i in range(15):
                d_t = (phase * 1.2 + i * 0.08) % 1.0
                d_angle = i * math.pi / 7.5 + phase * 0.4
                d_r = 30 + int(d_t * 40)
                dx = tx + int(math.cos(d_angle) * d_r)
                dy = ty + int(math.sin(d_angle) * d_r * 0.6) - int(d_t * 20)
                alpha = _NS_thoraz._alpha(230 * (1 - d_t))
                # Rock debris
                pygame.draw.rect(surface,
                                 (*_NS_thoraz.PALETTE["stone_dark"], alpha),
                                 (dx, dy, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_thoraz.PALETTE["stone_mid"], alpha),
                                 (dx, dy, 2, 2))
                # Fire around rock
                pygame.draw.rect(surface,
                                 (*_NS_thoraz.PALETTE["fire_bright"], alpha),
                                 (dx + 1, dy + 1, 1, 1))

            # Ground splash (radial)
            for i in range(12):
                sp_angle = i * math.pi / 6
                sp_r = int(20 + t * 15)
                sx = tx + int(math.cos(sp_angle) * sp_r)
                sy = ty + int(math.sin(sp_angle) * sp_r * 0.4)
                alpha = _NS_thoraz._alpha(230 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_thoraz.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_thoraz.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))


# ====================================================================
# ALIAS
# ====================================================================
draw_thoraz = _NS_thoraz.draw_thoraz


# ====================================================================================================
# VHAERITH - MINI BOSS
# ====================================================================================================

class _NS_vhaerith:
    """Namespace vhaerith - HD rendering untuk mini boss Vhaerith."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Rotting sackcloth body
        "sack_darkest": (25, 20, 15),
        "sack_dark": (55, 45, 30),
        "sack_mid": (95, 80, 55),
        "sack_light": (140, 120, 85),
        "sack_edge": (180, 155, 115),

        # Dried blood/rot stains
        "rot_dark": (55, 15, 10),
        "rot_mid": (110, 30, 20),
        "rot_light": (160, 60, 35),

        # Dark cloth/rags
        "rag_darkest": (10, 8, 12),
        "rag_dark": (25, 20, 30),
        "rag_mid": (50, 40, 55),
        "rag_light": (85, 70, 90),

        # Bones (aged)
        "bone_dark": (65, 55, 40),
        "bone_mid": (130, 115, 85),
        "bone_light": (200, 185, 145),
        "bone_shine": (240, 225, 190),

        # Scythe blade (dark rusted metal)
        "scythe_darkest": (15, 12, 15),
        "scythe_dark": (35, 30, 40),
        "scythe_mid": (75, 65, 80),
        "scythe_light": (135, 120, 140),
        "scythe_shine": (200, 190, 210),
        "scythe_blood": (100, 20, 20),

        # Scythe shaft (dark wood)
        "shaft_dark": (20, 15, 12),
        "shaft_mid": (45, 35, 25),
        "shaft_light": (85, 65, 45),

        # PURPLE MAGIC (signature - dark magic/fear)
        "magic_darkest": (25, 5, 45),
        "magic_dark": (55, 15, 95),
        "magic_deep": (95, 30, 155),
        "magic_mid": (150, 60, 210),
        "magic_light": (200, 130, 240),
        "magic_hot": (230, 180, 250),
        "magic_shine": (250, 230, 255),

        # Glowing red eyes
        "eye_darkest": (30, 0, 0),
        "eye_dark": (100, 10, 5),
        "eye_mid": (200, 40, 30),
        "eye_bright": (255, 100, 60),
        "eye_shine": (255, 200, 150),

        # Crows (jet black + purple tint)
        "crow_darkest": (0, 0, 5),
        "crow_dark": (10, 8, 20),
        "crow_mid": (25, 20, 40),
        "crow_light": (55, 45, 75),
        "crow_purple": (80, 40, 130),

        # Fear mist (dark purple)
        "mist_dark": (30, 15, 60),
        "mist_mid": (65, 35, 110),
        "mist_light": (130, 90, 180),

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
        color = _NS_vhaerith._clamp(color)
        if _NS_vhaerith.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_vhaerith._clamp(color)
        if _NS_vhaerith.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vhaerith._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vhaerith(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vhaerith._detect_moving(boss)
        _NS_vhaerith._update_attack_anim(boss)
        attacking = getattr(boss, "_vh_attack_active", False)

        # Ambient
        _NS_vhaerith._draw_shadow(surface, x, y + 52)
        _NS_vhaerith._draw_dark_aura(surface, x, y, pulse)
        _NS_vhaerith._draw_fear_mist(surface, x, y + 30, pulse)
        _NS_vhaerith._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_vhaerith._draw_reap_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhaerith._draw_crowstorm_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_vhaerith._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_vhaerith._draw_body_walk(surface, boss, x, y)
        else:
            _NS_vhaerith._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_vhaerith._draw_raven_bolt_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vhaerith._draw_drain_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vhaerith._draw_reap_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhaerith._draw_crowstorm_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_vh_attack_active", False))

        if not active:
            if timer >= cooldown - 20:
                boss._vh_attack_active = True
                boss._vh_attack_frame = 0
                active = True

        if active:
            boss._vh_attack_frame = int(getattr(boss, "_vh_attack_frame", 0)) + 1
            attack_duration = 28
            if boss._vh_attack_frame >= attack_duration:
                boss._vh_attack_active = False
                boss._vh_attack_frame = 0
                active = False

        attack_duration = 28
        boss._vh_attack_progress = (
            min(1.0, getattr(boss, "_vh_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_vh_last_x"):
            boss._vh_last_x = boss.x
            boss._vh_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vh_last_x)
        dy = abs(boss.y - boss._vh_last_y)
        boss._vh_last_x = boss.x
        boss._vh_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_vhaerith._draw_full_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_vhaerith._draw_full_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_vh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Reach out with scythe arm
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            ease = 1 - (1 - t) ** 2
            lunge = int((-3 + ease * 12)) * boss.direction
            lift = int(3 - ease * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_vhaerith._draw_full_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Dark magic projectile
        _NS_vhaerith._draw_basic_dark_projectile(surface, boss, x + lunge,
                                                  y - lift, progress)

    # ============================================================
    # FULL BODY (scarecrow with 4 scythe arms)
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Back scythe arms (2 arms behind body, curved up-back)
        _NS_vhaerith._draw_back_scythe_arms(surface, cx, cy, facing, phase)
        # 2. Legs (thin, ragged)
        _NS_vhaerith._draw_legs(surface, cx, cy, facing, phase, action)
        # 3. Body (tattered sack torso)
        _NS_vhaerith._draw_torso(surface, cx, cy, facing, phase)
        # 4. Head (sack head with glowing eyes)
        _NS_vhaerith._draw_head(surface, cx, cy - 20, facing, phase)
        # 5. Front scythe arms (2 arms in front, one extends during attack)
        _NS_vhaerith._draw_front_scythe_arms(surface, cx, cy, facing,
                                              phase, action, atk_prog)

    def _draw_back_scythe_arms(surface, cx, cy, facing, phase):
        """Two long scythe arms curving up-back like spider legs."""
        # Arm 1: upper back (curving up)
        # Arm 2: lower back (curving out-back)

        for arm_i, (base_off_x, base_off_y, curve_dir, base_angle, arm_len) in enumerate([
            (0, -14, 1, -math.pi * 0.7, 42),      # top-back scythe
            (-4, -8, -1, math.pi * 0.9, 38),      # back-lower scythe
        ]):
            base_x = cx + int(base_off_x * -facing)
            base_y = cy + base_off_y

            # Sway/twitch animation
            twitch = math.sin(phase * 0.8 + arm_i * 2) * 0.15

            # Curved arm path (3 segments)
            angle = base_angle + twitch
            # Segment 1 (upper)
            seg1_len = arm_len * 0.4
            joint1_x = base_x + int(math.cos(angle) * seg1_len) * (-facing)
            joint1_y = base_y + int(math.sin(angle) * seg1_len)

            # Segment 2 (curves inward)
            angle2 = angle + math.pi * 0.3 * curve_dir
            seg2_len = arm_len * 0.35
            joint2_x = joint1_x + int(math.cos(angle2) * seg2_len) * (-facing)
            joint2_y = joint1_y + int(math.sin(angle2) * seg2_len)

            # Segment 3 (end/scythe base)
            angle3 = angle2 + math.pi * 0.2 * curve_dir
            seg3_len = arm_len * 0.25
            end_x = joint2_x + int(math.cos(angle3) * seg3_len) * (-facing)
            end_y = joint2_y + int(math.sin(angle3) * seg3_len)

            # Draw arm segments (bone-like, thin)
            _NS_vhaerith._draw_arm_segment(surface, (base_x, base_y),
                                            (joint1_x, joint1_y), 4)
            _NS_vhaerith._draw_arm_segment(surface, (joint1_x, joint1_y),
                                            (joint2_x, joint2_y), 3)
            _NS_vhaerith._draw_arm_segment(surface, (joint2_x, joint2_y),
                                            (end_x, end_y), 3)

            # Joint bumps
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                                   (joint1_x, joint1_y), 3)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["bone_dark"],
                                   (joint1_x, joint1_y), 2)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                                   (joint2_x, joint2_y), 3)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["bone_dark"],
                                   (joint2_x, joint2_y), 2)

            # SCYTHE BLADE at end
            _NS_vhaerith._draw_scythe_blade(surface, end_x, end_y,
                                             angle3 + math.pi * 0.4 * curve_dir,
                                             facing, size=1.0)

    def _draw_arm_segment(surface, start, end, thickness):
        """Bone/tendril arm segment with dark rag wrap."""
        # Shadow
        _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                             (start[0] + 1, start[1] + 1),
                             (end[0] + 1, end[1] + 1), thickness + 1)
        # Dark rag wrap
        _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["rag_darkest"],
                             start, end, thickness)
        # Mid rag
        _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["rag_dark"],
                             start, end, max(1, thickness - 1))
        # Bone highlight (thin)
        _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["bone_dark"],
                             (start[0], start[1] - 1), (end[0], end[1] - 1), 1)

    def _draw_scythe_blade(surface, hand_x, hand_y, angle, facing, size=1.0):
        """Curved sickle/scythe blade."""
        blade_length = int(20 * size)

        # Perp for width
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)

        # Curved scythe blade (crescent shape)
        # Blade tip (far end)
        tip_x = hand_x + int(math.cos(angle) * blade_length)
        tip_y = hand_y + int(math.sin(angle) * blade_length)

        # Blade curve peak (perpendicular to tip direction)
        curve_peak_x = hand_x + int(math.cos(angle) * blade_length * 0.6
                                     + perp_x * blade_length * 0.35)
        curve_peak_y = hand_y + int(math.sin(angle) * blade_length * 0.6
                                     + perp_y * blade_length * 0.35)

        # Blade back edge
        back_peak_x = hand_x + int(math.cos(angle) * blade_length * 0.5
                                    + perp_x * blade_length * 0.15)
        back_peak_y = hand_y + int(math.sin(angle) * blade_length * 0.5
                                    + perp_y * blade_length * 0.15)

        # Scythe outer curve (draw as filled polygon with segments)
        outer_pts = [(hand_x, hand_y)]
        segs = 8
        for i in range(1, segs + 1):
            t = i / segs
            # Quadratic bezier: hand -> curve_peak -> tip
            bx = int((1 - t) ** 2 * hand_x + 2 * (1 - t) * t * curve_peak_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * hand_y + 2 * (1 - t) * t * curve_peak_y
                     + t ** 2 * tip_y)
            outer_pts.append((bx, by))

        # Inner (back) curve
        inner_pts = []
        for i in range(segs, -1, -1):
            t = i / segs
            bx = int((1 - t) ** 2 * hand_x + 2 * (1 - t) * t * back_peak_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * hand_y + 2 * (1 - t) * t * back_peak_y
                     + t ** 2 * tip_y)
            inner_pts.append((bx, by))

        blade_polygon = outer_pts + inner_pts

        # Shadow
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in blade_polygon])
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["scythe_darkest"], blade_polygon)

        # Bright edge along outer curve
        for i in range(len(outer_pts) - 1):
            _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["scythe_mid"],
                                 outer_pts[i], outer_pts[i + 1], 2)
            _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["scythe_light"],
                                 outer_pts[i], outer_pts[i + 1], 1)

        # Dried blood on blade edge (near tip)
        blood_at = outer_pts[len(outer_pts) * 3 // 4]
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["scythe_blood"],
                         (blood_at[0], blood_at[1], 2, 1))

        # SHARP TIP
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["scythe_dark"],
                               (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["scythe_light"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["scythe_shine"],
                         (tip_x, tip_y, 1, 1))

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Thin ragged legs (scarecrow style)."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 2

        # Both legs thin, wrapped in rags
        for leg_i, leg_x_off in enumerate((-3, 3)):
            leg_x = cx + leg_x_off
            leg_y_top = cy + 8
            leg_y_bot = cy + 42 + int((-leg_sway if leg_i == 0 else leg_sway))

            # Thin bone legs wrapped in dark rags
            _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                                 (leg_x + 1, leg_y_top + 1),
                                 (leg_x + 1, leg_y_bot + 1), 5)
            _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["rag_darkest"],
                                 (leg_x, leg_y_top), (leg_x, leg_y_bot), 4)
            _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["rag_dark"],
                                 (leg_x, leg_y_top), (leg_x, leg_y_bot), 3)
            _NS_vhaerith._aaline(surface, _NS_vhaerith.PALETTE["sack_dark"],
                                 (leg_x - 1, leg_y_top), (leg_x - 1, leg_y_bot), 1)

            # Ragged strips at bottom (torn cloth)
            for strip_i in range(3):
                s_off_y = leg_y_bot - 4 + strip_i * 2
                s_off_x = int(math.sin(phase * 2 + strip_i) * 2)
                pygame.draw.line(surface, _NS_vhaerith.PALETTE["rag_dark"],
                                 (leg_x - 2, s_off_y),
                                 (leg_x - 2 + s_off_x, s_off_y + 3), 1)
                pygame.draw.line(surface, _NS_vhaerith.PALETTE["rag_mid"],
                                 (leg_x + 2, s_off_y),
                                 (leg_x + 2 - s_off_x, s_off_y + 3), 1)

            # Skeletal foot (small bone)
            pygame.draw.ellipse(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                                (leg_x - 4, leg_y_bot, 9, 4))
            pygame.draw.ellipse(surface, _NS_vhaerith.PALETTE["bone_dark"],
                                (leg_x - 3, leg_y_bot, 7, 3))
            pygame.draw.ellipse(surface, _NS_vhaerith.PALETTE["bone_mid"],
                                (leg_x - 3, leg_y_bot, 7, 2))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Tattered sackcloth torso with rot stains."""
        # Body shape (hunched, ragged)
        torso_pts = [
            (cx - 11, cy - 6),
            (cx - 13, cy - 2),
            (cx - 12, cy + 5),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 12, cy + 5),
            (cx + 13, cy - 2),
            (cx + 11, cy - 6),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ]
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_darkest"], torso_pts)
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_dark"], [
            (cx - 10, cy - 4),
            (cx - 12, cy - 1),
            (cx - 11, cy + 4),
            (cx - 7, cy + 8),
            (cx + 7, cy + 8),
            (cx + 11, cy + 4),
            (cx + 12, cy - 1),
            (cx + 10, cy - 4),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ])
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_mid"], [
            (cx - 8, cy - 2),
            (cx - 10, cy + 2),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 10, cy + 2),
            (cx + 8, cy - 2),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])

        # Sackcloth stitching (rough seams)
        for stitch_x in (-6, 0, 6):
            for stitch_y in (-2, 2, 6):
                pygame.draw.rect(surface, _NS_vhaerith.PALETTE["sack_darkest"],
                                 (cx + stitch_x - 1, cy + stitch_y, 3, 1))

        # Vertical stitch seam down middle
        pygame.draw.line(surface, _NS_vhaerith.PALETTE["sack_darkest"],
                         (cx, cy - 6), (cx, cy + 8), 1)
        for stitch_y in range(-6, 8, 2):
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                             (cx - 1, cy + stitch_y), (cx + 1, cy + stitch_y), 1)

        # BLOOD/ROT STAINS
        # Big stain on chest
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["rot_dark"], [
            (cx - 4, cy - 2),
            (cx - 5, cy + 2),
            (cx - 2, cy + 5),
            (cx + 3, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
        ])
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["rot_mid"], [
            (cx - 3, cy - 1),
            (cx - 4, cy + 2),
            (cx - 1, cy + 4),
            (cx + 2, cy + 3),
            (cx + 4, cy),
        ])
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["rot_light"],
                         (cx - 1, cy + 1, 2, 1))

        # Small tears at bottom edge (ragged)
        for tear_i, tx_off in enumerate((-9, -4, 2, 8)):
            tear_x = cx + tx_off
            tear_h = 2 + tear_i % 2
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                             (tear_x, cy + 9),
                             (tear_x + 1, cy + 9 + tear_h), 1)
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["sack_dark"],
                             (tear_x + 1, cy + 9),
                             (tear_x + 2, cy + 9 + tear_h), 1)

    def _draw_head(surface, cx, cy, facing, phase):
        """Sack head with glowing red eyes and stitched mouth."""
        # HEAD SHAPE (rounded sack, slightly tilted)
        head_pts = [
            (cx - 8, cy + 6),
            (cx - 10, cy + 1),
            (cx - 9, cy - 6),
            (cx - 6, cy - 10),
            (cx - 1, cy - 12),
            (cx + 5, cy - 11),
            (cx + 9, cy - 8),
            (cx + 10, cy - 2),
            (cx + 9, cy + 4),
            (cx + 7, cy + 8),
            (cx + 3, cy + 9),
            (cx - 3, cy + 9),
        ]
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in head_pts])
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_darkest"], head_pts)
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_dark"], [
            (cx - 7, cy + 5),
            (cx - 9, cy),
            (cx - 8, cy - 5),
            (cx - 5, cy - 9),
            (cx + 4, cy - 10),
            (cx + 8, cy - 7),
            (cx + 9, cy - 2),
            (cx + 8, cy + 3),
            (cx + 6, cy + 7),
            (cx - 2, cy + 8),
        ])
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_mid"], [
            (cx - 6, cy - 4),
            (cx - 4, cy - 8),
            (cx + 3, cy - 8),
            (cx + 7, cy - 4),
            (cx + 7, cy + 2),
            (cx + 4, cy + 5),
            (cx - 4, cy + 5),
        ])
        # Highlight
        _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["sack_light"], [
            (cx - 2, cy - 5),
            (cx + 2, cy - 6),
            (cx + 5, cy - 3),
            (cx + 3, cy),
            (cx - 3, cy),
        ])

        # STITCHES around head (rough hand-sewn look)
        # Top stitching (where sack is tied)
        for i, sx in enumerate((-4, -1, 2, 5)):
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                             (cx + sx, cy - 10), (cx + sx, cy - 11), 1)
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["rot_dark"],
                             (cx + sx - 1, cy - 10), (cx + sx + 1, cy - 10), 1)

        # Side seams
        for sy in range(-6, 6, 3):
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["sack_darkest"],
                             (cx - 9, cy + sy, 1, 2))
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["sack_darkest"],
                             (cx + 9, cy + sy, 1, 2))

        # DEEP EYE SOCKETS (dark holes with GLOWING RED EYES)
        eye_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for eye_x_off in (-3, 3):
            ex = cx + eye_x_off
            ey = cy - 3

            # Deep dark socket
            pygame.draw.ellipse(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                                (ex - 3, ey - 2, 6, 5))
            pygame.draw.ellipse(surface, _NS_vhaerith.PALETTE["eye_darkest"],
                                (ex - 2, ey - 2, 5, 4))

            # GLOWING RED EYES
            # Outer halo (large soft glow)
            for r in range(8, 0, -1):
                alpha = _NS_vhaerith._alpha(100 * (8 - r) / 8 * eye_pulse)
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)

            # Bright core
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["eye_dark"],
                                   (ex, ey), 3)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["eye_mid"],
                                   (ex, ey), 2)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["eye_bright"],
                                   (ex, ey), 1)
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["eye_shine"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["white"],
                             (ex, ey, 1, 1))

            # Dark tear/drip below eye (rot)
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["rot_dark"],
                             (ex, ey + 2), (ex, ey + 5), 1)

        # STITCHED MOUTH (X-shape stitches)
        # Mouth line
        pygame.draw.line(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                         (cx - 4, cy + 4), (cx + 4, cy + 4), 2)
        pygame.draw.line(surface, _NS_vhaerith.PALETTE["rot_dark"],
                         (cx - 3, cy + 4), (cx + 3, cy + 4), 1)

        # X-stitches across mouth
        for stitch_x in (-3, 0, 3):
            sx = cx + stitch_x
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                             (sx - 1, cy + 3), (sx + 1, cy + 5), 1)
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                             (sx - 1, cy + 5), (sx + 1, cy + 3), 1)

        # Small purple magic wisps rising from head (fear aura)
        for i in range(4):
            e_t = (phase * 0.8 + i * 0.25) % 1.0
            e_x = cx + int(math.sin(phase + i * 2) * 6)
            e_y = cy - 10 - int(e_t * 12)
            alpha = _NS_vhaerith._alpha(200 * (1 - e_t))
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                   (e_x, e_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                             (e_x, e_y, 1, 1))

    def _draw_front_scythe_arms(surface, cx, cy, facing, phase, action, atk_prog):
        """Two scythe arms in front — one extends during attack."""
        # Arm 1: main attack arm (front-side, extends during attack)
        # Arm 2: passive front-lower arm

        # === MAIN ATTACK ARM (extends during attack) ===
        base_x = cx + facing * 8
        base_y = cy - 4

        if action == "attack":
            if atk_prog < 0.35:
                # Wind-up: pull back
                t = atk_prog / 0.35
                arm_angle = -math.pi * 0.2 - t * math.pi * 0.4
                arm_len = 20
            elif atk_prog < 0.6:
                # THRUST forward
                t = (atk_prog - 0.35) / 0.25
                ease = 1 - (1 - t) ** 2
                arm_angle = -math.pi * 0.6 + ease * math.pi * 0.6
                arm_len = int(20 + ease * 20)
            else:
                # Recovery
                t = (atk_prog - 0.6) / 0.4
                arm_angle = -t * math.pi * 0.2
                arm_len = int(40 - t * 15)
        else:
            twitch = math.sin(phase * 0.7) * 0.1
            arm_angle = -math.pi * 0.15 + twitch
            arm_len = 22

        # 3-segment arm
        # Segment 1 (upper)
        seg1_len = int(arm_len * 0.4)
        joint1_x = base_x + int(math.cos(arm_angle) * seg1_len) * facing
        joint1_y = base_y + int(math.sin(arm_angle) * seg1_len)

        # Segment 2 (curves)
        angle2 = arm_angle - math.pi * 0.15
        seg2_len = int(arm_len * 0.35)
        joint2_x = joint1_x + int(math.cos(angle2) * seg2_len) * facing
        joint2_y = joint1_y + int(math.sin(angle2) * seg2_len)

        # Segment 3 (end)
        angle3 = angle2 + math.pi * 0.15
        seg3_len = int(arm_len * 0.25)
        end_x = joint2_x + int(math.cos(angle3) * seg3_len) * facing
        end_y = joint2_y + int(math.sin(angle3) * seg3_len)

        # Draw arm segments
        _NS_vhaerith._draw_arm_segment(surface, (base_x, base_y),
                                        (joint1_x, joint1_y), 4)
        _NS_vhaerith._draw_arm_segment(surface, (joint1_x, joint1_y),
                                        (joint2_x, joint2_y), 3)
        _NS_vhaerith._draw_arm_segment(surface, (joint2_x, joint2_y),
                                        (end_x, end_y), 3)

        # Joints
        for jp in ((joint1_x, joint1_y), (joint2_x, joint2_y)):
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                                   jp, 3)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["bone_dark"],
                                   jp, 2)

        # Purple magic charge at hand during attack
        if action == "attack" and atk_prog < 0.5:
            charge_intensity = math.sin((atk_prog / 0.5) * math.pi)
            for r in range(int(6 * charge_intensity) + 2, 0, -1):
                alpha = _NS_vhaerith._alpha(150 * charge_intensity *
                                             (8 - r) / 8)
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                       (end_x, end_y), r)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_light"],
                                   (end_x, end_y),
                                   max(1, int(charge_intensity * 3)))
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_shine"],
                             (end_x, end_y, 1, 1))

        # SCYTHE BLADE at end (larger for front)
        _NS_vhaerith._draw_scythe_blade(surface, end_x, end_y,
                                         angle3 - math.pi * 0.3 * facing,
                                         facing, size=1.1)

        # === SECONDARY FRONT ARM (passive) ===
        base2_x = cx + facing * 6
        base2_y = cy + 2
        twitch2 = math.sin(phase * 0.6 + 1.5) * 0.1
        angle_a = math.pi * 0.15 + twitch2

        # Simpler 2-segment
        j1_len = 14
        j1_x = base2_x + int(math.cos(angle_a) * j1_len) * facing
        j1_y = base2_y + int(math.sin(angle_a) * j1_len)

        angle_b = angle_a + math.pi * 0.2
        j2_len = 12
        j2_x = j1_x + int(math.cos(angle_b) * j2_len) * facing
        j2_y = j1_y + int(math.sin(angle_b) * j2_len)

        _NS_vhaerith._draw_arm_segment(surface, (base2_x, base2_y),
                                        (j1_x, j1_y), 3)
        _NS_vhaerith._draw_arm_segment(surface, (j1_x, j1_y),
                                        (j2_x, j2_y), 3)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                               (j1_x, j1_y), 3)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["bone_dark"],
                               (j1_x, j1_y), 2)

        _NS_vhaerith._draw_scythe_blade(surface, j2_x, j2_y,
                                         angle_b + math.pi * 0.4 * facing,
                                         facing, size=0.85)

    # ============================================================
    # BASIC RANGED ATTACK — DARK MAGIC PROJECTILE
    # ============================================================
    def _draw_basic_dark_projectile(surface, boss, x, y, progress):
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_vhaerith._target_position(boss, x, y)

        start_x = x + facing * 32
        start_y = y - 6

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail
        for i in range(7):
            trail_t = max(0.0, t - i * 0.07)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vhaerith._alpha(230 - i * 28)
            size = max(1, 6 - i)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                   (px, py), size)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                                   (px, py), max(1, size - 3))

        # Bright bolt head
        for r in range(8, 0, -1):
            alpha = _NS_vhaerith._alpha(100 * (8 - r) / 8)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                                   (bx, by), r)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_darkest"],
                               (bx, by), 5)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_dark"],
                               (bx, by), 4)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_deep"],
                               (bx, by), 3)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_mid"],
                               (bx, by), 2)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_hot"],
                               (bx, by), 1)
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_shine"],
                         (bx, by, 1, 1))

        # Impact splash
        if t > 0.9:
            st = (t - 0.9) / 0.1
            r = int(10 + st * 20)
            alpha = _NS_vhaerith._alpha(230 * (1 - st))
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_deep"], alpha),
                                   (tx, ty), r + 2, 3)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                   (tx, ty), r, 2)
            for i in range(8):
                a = i * math.pi / 4
                ex = tx + int(math.cos(a) * r)
                ey = ty + int(math.sin(a) * r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 20, 180), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_dark_aura(surface, x, y, phase):
        """Dark purple ominous aura."""
        pulse = math.sin(phase * 0.5) * 0.3 + 0.7

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_vhaerith._alpha((95 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_vhaerith._aacircle(aura,
                                       (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_vhaerith._alpha((60 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vhaerith._aacircle(aura,
                                       (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_vhaerith._alpha((35 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_vhaerith._aacircle(aura,
                                       (*_NS_vhaerith.PALETTE["magic_deep"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Floating dark particles
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 38 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_dark"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_light"], (sx, sy, 1, 1))

    def _draw_fear_mist(surface, cx, cy, phase):
        """Purple fear mist floating around."""
        mist = pygame.Surface((160, 60), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7

        for radius in range(40, 3, -3):
            alpha = _NS_vhaerith._alpha((40 - radius) * 2.5 * pulse)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                                    (*_NS_vhaerith.PALETTE["mist_dark"], alpha),
                                    (80 - radius * 2, 30 - radius // 3,
                                     radius * 4, max(3, radius // 2)))
        for radius in range(25, 3, -2):
            alpha = _NS_vhaerith._alpha((25 - radius) * 3.0 * pulse)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                                    (*_NS_vhaerith.PALETTE["mist_mid"], alpha),
                                    (80 - radius, 30 - radius // 4,
                                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 80, cy - 10))

        # Rising purple wisps
        for i in range(6):
            t = (phase * 0.4 + i * 0.16) % 1.0
            sx = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 20)
            alpha = _NS_vhaerith._alpha(200 * (1 - t))
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["mist_mid"], alpha),
                                   (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_vhaerith.PALETTE["mist_light"], alpha),
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Dark ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vhaerith.PALETTE["magic_darkest"], 220),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_vhaerith.PALETTE["magic_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_vhaerith.PALETTE["magic_deep"], 200),
                            (25, 21, 110, 16), 1)

        # Runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_vhaerith.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_vhaerith.PALETTE["magic_hot"],
                                 _NS_vhaerith._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — RAVEN BOLT (crow projectile bouncing)
    # ============================================================
    def _draw_raven_bolt_fx(surface, boss, x, y, timer, phase):
        """Crow-shaped magic projectile flying to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vhaerith._target_position(boss, x, y)

        start_x = x + facing * 32
        start_y = y - 6

        if progress < 0.15:
            # Charge crow forming
            t = progress / 0.15
            r = int(4 + t * 8)
            for lr in range(r + 4, 0, -1):
                alpha = _NS_vhaerith._alpha(180 * (r + 4 - lr) / (r + 4))
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                       (start_x, start_y), lr)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_deep"],
                                   (start_x, start_y), r - 2)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_light"],
                                   (start_x, start_y), max(1, r - 4))
        else:
            t = (progress - 0.15) / 0.85
            t = min(1.0, t)
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            angle = math.atan2(ty - start_y, tx - start_x)

            # Magic trail
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_vhaerith._alpha(230 - i * 25)
                size = max(1, 5 - i)
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                       (px, py), size)
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                                       (px, py), max(1, size - 2))

            # DRAW CROW SHAPE at bolt head
            _NS_vhaerith._draw_flying_crow(surface, bx, by, angle, facing,
                                            phase, size=1.2)

            # Bright magic aura around crow
            for r in range(8, 3, -1):
                alpha = _NS_vhaerith._alpha(120 * (8 - r) / 5)
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                                       (bx, by), r)

            # Impact
            if t > 0.9:
                st = (t - 0.9) / 0.1
                r = int(12 + st * 18)
                alpha = _NS_vhaerith._alpha(230 * (1 - st))
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_deep"], alpha),
                                       (tx, ty), r + 2, 3)
                _NS_vhaerith._aacircle(surface,
                                       (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                       (tx, ty), r, 2)
                for i in range(8):
                    a = i * math.pi / 4
                    ex = tx + int(math.cos(a) * r)
                    ey = ty + int(math.sin(a) * r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_vhaerith.PALETTE["magic_hot"], alpha),
                                     (ex, ey, 2, 2))

    def _draw_flying_crow(surface, cx, cy, angle, facing, phase, size=1.0):
        """A small crow shape mid-flight (wings spread)."""
        # Wing flap animation
        flap = math.sin(phase * 8) * 0.5 + 0.5  # 0 to 1

        body_w = int(6 * size)
        body_h = int(4 * size)

        # Body (elongated oval)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Body ellipse
        for i in range(-body_w // 2, body_w // 2 + 1, 1):
            w = max(1, body_h - abs(i) // 2)
            bx = cx + int(cos_a * i)
            by = cy + int(sin_a * i)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["crow_darkest"],
                                   (bx, by), w)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["crow_dark"],
                                   (bx, by), max(1, w - 1))

        # WINGS (spread perpendicular to flight direction)
        perp_x = -sin_a
        perp_y = cos_a
        wing_span = int((6 + flap * 4) * size)

        for wing_side in (-1, 1):
            wing_base_x = cx
            wing_base_y = cy
            wing_tip_x = cx + int(perp_x * wing_span * wing_side)
            wing_tip_y = cy + int(perp_y * wing_span * wing_side)
            # Wing shape (feathered)
            wing_mid_x = int((wing_base_x + wing_tip_x) / 2 - cos_a * 2)
            wing_mid_y = int((wing_base_y + wing_tip_y) / 2 - sin_a * 2)

            _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["crow_darkest"], [
                (wing_base_x + int(cos_a * 1), wing_base_y + int(sin_a * 1)),
                (wing_mid_x, wing_mid_y),
                (wing_tip_x, wing_tip_y),
                (int((wing_tip_x + wing_base_x) / 2), int((wing_tip_y + wing_base_y) / 2)),
                (wing_base_x - int(cos_a * 1), wing_base_y - int(sin_a * 1)),
            ])
            _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["crow_dark"], [
                (wing_base_x, wing_base_y),
                (wing_mid_x, wing_mid_y),
                (wing_tip_x, wing_tip_y),
                (wing_base_x, wing_base_y),
            ])
            # Purple tint highlight
            pygame.draw.line(surface, _NS_vhaerith.PALETTE["crow_purple"],
                             (wing_base_x, wing_base_y),
                             (wing_tip_x, wing_tip_y), 1)
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_light"],
                             (wing_tip_x, wing_tip_y, 1, 1))

        # BEAK (small triangle at head)
        head_x = cx + int(cos_a * (body_w // 2 + 1))
        head_y = cy + int(sin_a * (body_w // 2 + 1))
        beak_x = head_x + int(cos_a * 2)
        beak_y = head_y + int(sin_a * 2)
        pygame.draw.line(surface, _NS_vhaerith.PALETTE["bone_dark"],
                         (head_x, head_y), (beak_x, beak_y), 1)

        # RED EYE (small glowing dot on head)
        eye_x = head_x - int(cos_a) + int(perp_x)
        eye_y = head_y - int(sin_a) + int(perp_y)
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["eye_bright"],
                         (eye_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_vhaerith.PALETTE["eye_shine"],
                         (eye_x, eye_y, 1, 1))

    # ============================================================
    # SKILL W — SOUL DRAIN (purple beam)
    # ============================================================
    def _draw_drain_fx(surface, boss, x, y, timer, phase):
        """Continuous purple beam draining target."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vhaerith._target_position(boss, x, y)

        # Origin (boss hand)
        start_x = x + facing * 30
        start_y = y - 6

        # Beam intensity (pulsates while draining)
        intensity = 0.7 + math.sin(phase * 6) * 0.3

        # Draw beam with wavy energy
        segments = 20
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            x1 = int(start_x + (tx - start_x) * t1)
            y1 = int(start_y + (ty - start_y) * t1)
            x2 = int(start_x + (tx - start_x) * t2)
            y2 = int(start_y + (ty - start_y) * t2)

            # Wave perpendicular
            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            wave1 = math.sin(phase * 4 + t1 * math.pi * 6) * 4
            wave2 = math.sin(phase * 4 + t2 * math.pi * 6) * 4
            x1 += int(math.cos(perp_angle) * wave1)
            y1 += int(math.sin(perp_angle) * wave1)
            x2 += int(math.cos(perp_angle) * wave2)
            y2 += int(math.sin(perp_angle) * wave2)

            # Multi-layer beam
            alpha_outer = _NS_vhaerith._alpha(150 * intensity)
            alpha_core = _NS_vhaerith._alpha(255 * intensity)
            pygame.draw.line(surface,
                             (*_NS_vhaerith.PALETTE["magic_darkest"], alpha_outer),
                             (x1, y1), (x2, y2), 10)
            pygame.draw.line(surface,
                             (*_NS_vhaerith.PALETTE["magic_dark"], alpha_outer),
                             (x1, y1), (x2, y2), 7)
            pygame.draw.line(surface,
                             (*_NS_vhaerith.PALETTE["magic_deep"], alpha_core),
                             (x1, y1), (x2, y2), 5)
            pygame.draw.line(surface,
                             (*_NS_vhaerith.PALETTE["magic_mid"], alpha_core),
                             (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface,
                             (*_NS_vhaerith.PALETTE["magic_hot"], alpha_core),
                             (x1, y1), (x2, y2), 1)

        # Orb of energy flowing back to boss (soul particles)
        for i in range(8):
            flow_t = (phase * 2 + i * 0.12) % 1.0
            flow_t = 1.0 - flow_t  # flow from target to boss
            px = int(start_x + (tx - start_x) * flow_t)
            py = int(start_y + (ty - start_y) * flow_t)
            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            wave = math.sin(phase * 4 + i) * 3
            px += int(math.cos(perp_angle) * wave)
            py += int(math.sin(perp_angle) * wave)
            _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_hot"],
                                   (px, py), 2)
            pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_shine"],
                             (px, py, 1, 1))

        # Target extraction effect (particles being sucked out)
        for i in range(8):
            ext_t = (phase * 3 + i * 0.12) % 1.0
            ext_r = int(20 - ext_t * 18)
            ext_angle = i * math.pi / 4 + phase
            ex = tx + int(math.cos(ext_angle) * ext_r)
            ey = ty + int(math.sin(ext_angle) * ext_r)
            alpha = _NS_vhaerith._alpha(230 * (1 - ext_t))
            pygame.draw.rect(surface,
                             (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                             (ex, ey, 2, 2))

        # Beam origin glow (boss hand)
        for r in range(8, 0, -1):
            alpha = _NS_vhaerith._alpha(150 * (8 - r) / 8 * intensity)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                   (start_x, start_y), r)

        # Target glow
        for r in range(10, 0, -1):
            alpha = _NS_vhaerith._alpha(150 * (10 - r) / 10 * intensity)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_deep"], alpha),
                                   (tx, ty), r)

    # ============================================================
    # SKILL E — TERROR REAP (scythe slam + fear geyser)
    # ============================================================
    def _draw_reap_ground(surface, boss, x, y, timer, pulse):
        """Warning circle then eruption."""
        tx, ty = _NS_vhaerith._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            t = progress / 0.3
            r = int(15 + t * 15)
            alpha = _NS_vhaerith._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            t = (progress - 0.3) / 0.7
            r = int(35)
            alpha = _NS_vhaerith._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_deep"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_reap_fg(surface, boss, x, y, timer, phase):
        """Rising jagged spikes of dark energy + fear geyser."""
        tx, ty = _NS_vhaerith._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress >= 0.3:
            t = (progress - 0.3) / 0.7
            intensity = math.sin(min(1.0, t * 2) * math.pi * 0.7)

            # Multiple jagged energy spikes rising
            num_spikes = 12
            for i in range(num_spikes):
                s_angle = i * math.pi * 2 / num_spikes
                s_r = int(15 + math.sin(phase + i) * 5)
                sx = tx + int(math.cos(s_angle) * s_r)
                sy_base = ty + int(math.sin(s_angle) * s_r * 0.4)

                spike_h = int(30 * intensity + math.sin(phase * 3 + i) * 3)
                if spike_h < 3:
                    continue

                # Jagged spike (crystal shape)
                _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["shadow_deep"], [
                    (sx + 1, sy_base - spike_h + 1),
                    (sx - 4, sy_base + 1),
                    (sx + 4, sy_base + 1),
                ])
                _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["magic_darkest"], [
                    (sx, sy_base - spike_h),
                    (sx - 4, sy_base),
                    (sx + 4, sy_base),
                ])
                _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["magic_dark"], [
                    (sx, sy_base - spike_h),
                    (sx - 3, sy_base),
                    (sx + 3, sy_base),
                ])
                _NS_vhaerith._poly(surface, _NS_vhaerith.PALETTE["magic_deep"], [
                    (sx, sy_base - spike_h),
                    (sx - 2, sy_base),
                    (sx + 2, sy_base),
                ])
                # Bright edge
                pygame.draw.line(surface, _NS_vhaerith.PALETTE["magic_light"],
                                 (sx, sy_base - spike_h), (sx, sy_base), 1)
                # Bright tip
                pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_hot"],
                                 (sx, sy_base - spike_h, 1, 1))
                pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_shine"],
                                 (sx, sy_base - spike_h, 1, 1))

                # Base glow
                for glow_r in range(4, 0, -1):
                    alpha = _NS_vhaerith._alpha(100 * (4 - glow_r) / 4 * intensity)
                    _NS_vhaerith._aacircle(surface,
                                           (*_NS_vhaerith.PALETTE["magic_light"], alpha),
                                           (sx, sy_base), glow_r)

            # Central geyser column
            col_h = int(45 * intensity)
            for layer_i in range(5):
                lt = layer_i / 5
                ly = ty - int(lt * col_h)
                lw = int(8 - lt * 4)
                alpha = _NS_vhaerith._alpha(220 * (1 - lt) * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                 (tx - lw, ly - 2, lw * 2, 4))
                pygame.draw.rect(surface,
                                 (*_NS_vhaerith.PALETTE["magic_deep"], alpha),
                                 (tx - lw + 1, ly - 1, lw * 2 - 2, 3))
                pygame.draw.rect(surface,
                                 (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                 (tx - lw + 2, ly - 1, lw * 2 - 4, 2))
                pygame.draw.rect(surface,
                                 (*_NS_vhaerith.PALETTE["magic_hot"], alpha),
                                 (tx, ly, 1, 1))

            # Rising particles
            for i in range(12):
                p_t = (phase * 1.2 + i * 0.08) % 1.0
                p_x = tx + int(math.sin(phase * 3 + i) * 15)
                p_y = ty - int(p_t * 40)
                alpha = _NS_vhaerith._alpha(230 * (1 - p_t) * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_vhaerith.PALETTE["magic_hot"], alpha),
                                 (p_x, p_y, 2, 2))

    # ============================================================
    # SKILL R — CROWSTORM (swirling crows around target)
    # ============================================================
    def _draw_crowstorm_ground(surface, boss, x, y, timer, phase):
        """Massive dark ring on ground."""
        tx, ty = _NS_vhaerith._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_dark"], 200),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                                (*_NS_vhaerith.PALETTE["magic_deep"], 180),
                                (tx - r + 12, ty - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12))
            # Runes on ring
            for i in range(12):
                angle = phase * 0.5 + i * math.pi / 6
                rx = tx + int(math.cos(angle) * r * 0.85)
                ry = ty + int(math.sin(angle) * r * 0.3)
                pygame.draw.rect(surface, _NS_vhaerith.PALETTE["magic_light"],
                                 (rx, ry, 2, 2))

    def _draw_crowstorm_fg(surface, boss, x, y, timer, phase):
        """Massive swirling storm of crows around target."""
        tx, ty = _NS_vhaerith._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = 70

        # Spiraling dark magic tendrils
        num_arms = 4
        for arm_i in range(num_arms):
            arm_offset = arm_i * math.pi * 2 / num_arms
            prev = None
            for step in range(25):
                t = step / 25
                spiral_angle = phase * 2 + arm_offset + t * math.pi * 3
                sr = int(r * (1 - t * 0.3))
                sx = tx + int(math.cos(spiral_angle) * sr)
                sy = ty + int(math.sin(spiral_angle) * sr * 0.4)
                alpha = _NS_vhaerith._alpha(200 * (1 - t * 0.4))

                if prev is not None:
                    pygame.draw.line(surface,
                                     (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                     prev, (sx, sy), 5)
                    pygame.draw.line(surface,
                                     (*_NS_vhaerith.PALETTE["magic_dark"], alpha),
                                     prev, (sx, sy), 3)
                    pygame.draw.line(surface,
                                     (*_NS_vhaerith.PALETTE["magic_mid"], alpha),
                                     prev, (sx, sy), 1)
                prev = (sx, sy)

        # SWIRLING CROWS (multiple crows flying around)
        num_crows = 8
        for crow_i in range(num_crows):
            crow_angle = phase * 1.8 + crow_i * math.pi * 2 / num_crows
            crow_r = r * 0.7 + math.sin(phase * 2 + crow_i) * 8
            cx_pos = tx + int(math.cos(crow_angle) * crow_r)
            cy_pos = ty + int(math.sin(crow_angle) * crow_r * 0.4)
            # Crow flies in circular motion, so its facing changes
            crow_facing_angle = crow_angle + math.pi / 2
            _NS_vhaerith._draw_flying_crow(surface, cx_pos, cy_pos,
                                            crow_facing_angle, 1, phase * 4,
                                            size=1.0)

        # Additional smaller crows (further out)
        for crow_i in range(6):
            crow_angle = -phase * 1.5 + crow_i * math.pi * 2 / 6
            crow_r = r * 0.95 + math.sin(phase * 3 + crow_i) * 6
            cx_pos = tx + int(math.cos(crow_angle) * crow_r)
            cy_pos = ty + int(math.sin(crow_angle) * crow_r * 0.4)
            crow_facing_angle = crow_angle + math.pi / 2
            _NS_vhaerith._draw_flying_crow(surface, cx_pos, cy_pos,
                                            crow_facing_angle, 1, phase * 5,
                                            size=0.8)

        # Central dark vortex
        for r_v in range(15, 3, -2):
            alpha = _NS_vhaerith._alpha(150 * (15 - r_v) / 15)
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_darkest"], alpha),
                                   (tx, ty), r_v)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["shadow_deep"],
                               (tx, ty), 6)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_dark"],
                               (tx, ty), 4)
        _NS_vhaerith._aacircle(surface, _NS_vhaerith.PALETTE["magic_hot"],
                               (tx, ty), 1)

        # Purple feathers falling
        for feather_i in range(15):
            f_t = (phase * 0.6 + feather_i * 0.07) % 1.0
            f_angle = feather_i * math.pi / 7.5 + phase * 0.3
            f_r = int(r * (0.3 + f_t * 0.6))
            fx = tx + int(math.cos(f_angle) * f_r)
            fy = ty + int(math.sin(f_angle) * f_r * 0.4) + int(f_t * 20)
            alpha = _NS_vhaerith._alpha(220 * (1 - f_t))
            # Feather shape (small elongated)
            pygame.draw.rect(surface,
                             (*_NS_vhaerith.PALETTE["crow_darkest"], alpha),
                             (fx, fy, 2, 3))
            pygame.draw.rect(surface,
                             (*_NS_vhaerith.PALETTE["crow_purple"], alpha),
                             (fx, fy + 1, 1, 1))

        # Rising fear mist inside vortex
        for i in range(10):
            m_t = (phase * 1.5 + i * 0.1) % 1.0
            m_x = tx + int(math.sin(phase * 2 + i) * 20)
            m_y = ty - int(m_t * 30)
            alpha = _NS_vhaerith._alpha(200 * (1 - m_t))
            _NS_vhaerith._aacircle(surface,
                                   (*_NS_vhaerith.PALETTE["magic_hot"], alpha),
                                   (m_x, m_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_vhaerith.PALETTE["magic_shine"], alpha),
                             (m_x, m_y, 1, 1))


# ====================================================================
# ALIAS
# ====================================================================
draw_vhaerith = _NS_vhaerith.draw_vhaerith


# ====================================================================================================
# NYXARIS - TRUE BOSS
# ====================================================================================================

class _NS_nyxaris:
    """Namespace nyxaris - HD rendering untuk mini boss Nyxaris."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Dark robe/coat (main)
        "coat_darkest": (10, 8, 15),
        "coat_dark": (25, 20, 35),
        "coat_mid": (55, 40, 65),
        "coat_light": (95, 75, 110),

        # Red/crimson collar & accents
        "crimson_darkest": (35, 8, 15),
        "crimson_dark": (85, 20, 30),
        "crimson_mid": (155, 40, 55),
        "crimson_light": (220, 80, 90),
        "crimson_shine": (250, 150, 150),

        # Armor plating (dark metal)
        "armor_darkest": (12, 12, 20),
        "armor_dark": (35, 35, 50),
        "armor_mid": (75, 75, 95),
        "armor_light": (140, 140, 170),
        "armor_shine": (200, 200, 230),

        # Skin (pale)
        "skin_dark": (110, 85, 75),
        "skin_mid": (175, 145, 130),
        "skin_light": (225, 195, 180),
        "skin_shine": (250, 230, 220),

        # Hair (dark blue-black)
        "hair_darkest": (8, 8, 20),
        "hair_dark": (25, 25, 45),
        "hair_mid": (55, 55, 85),
        "hair_light": (100, 100, 140),

        # LUNAR MAGIC (main - cyan/white moonlight)
        "moon_darkest": (20, 35, 60),
        "moon_dark": (50, 90, 140),
        "moon_mid": (120, 180, 230),
        "moon_light": (200, 235, 255),
        "moon_shine": (240, 250, 255),
        "moon_white": (255, 255, 255),

        # PURPLE MAGIC (Gravitum/Moonlight Vigil)
        "purple_darkest": (25, 5, 50),
        "purple_dark": (55, 20, 100),
        "purple_mid": (110, 55, 175),
        "purple_light": (180, 130, 230),
        "purple_hot": (220, 180, 250),
        "purple_shine": (245, 225, 255),

        # PRIESTESS SPIRIT (ghostly cyan-white)
        "spirit_darkest": (25, 45, 75),
        "spirit_dark": (60, 100, 145),
        "spirit_mid": (120, 180, 220),
        "spirit_light": (200, 230, 245),
        "spirit_hair": (180, 210, 235),

        # Weapon metal (silver + moon glow)
        "weapon_dark": (40, 50, 70),
        "weapon_mid": (110, 130, 160),
        "weapon_light": (200, 215, 240),
        "weapon_shine": (250, 253, 255),

        # Eyes (piercing cyan)
        "eye_dark": (10, 30, 60),
        "eye_mid": (60, 140, 220),
        "eye_light": (180, 230, 255),

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
        color = _NS_nyxaris._clamp(color)
        if _NS_nyxaris.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxaris._clamp(color)
        if _NS_nyxaris.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxaris._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyxaris(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxaris._detect_moving(boss)
        _NS_nyxaris._update_attack_anim(boss)
        attacking = getattr(boss, "_nx_attack_active", False)

        # Priestess spirit behind (always visible)
        _NS_nyxaris._draw_priestess_spirit(surface, boss, x, y, pulse)

        # Ambient
        _NS_nyxaris._draw_shadow(surface, x, y + 52)
        _NS_nyxaris._draw_lunar_aura(surface, x, y, pulse)
        _NS_nyxaris._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX
        if active_skill == "w":
            _NS_nyxaris._draw_moonlight_vigil_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxaris._draw_descent_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_nyxaris._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxaris._draw_body_walk(surface, boss, x, y)
        else:
            _NS_nyxaris._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_nyxaris._draw_phase_shot_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxaris._draw_moonlight_vigil_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxaris._draw_gravitum_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxaris._draw_descent_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_nx_attack_active", False))

        if not active:
            if timer >= cooldown - 20:
                boss._nx_attack_active = True
                boss._nx_attack_frame = 0
                active = True

        if active:
            boss._nx_attack_frame = int(getattr(boss, "_nx_attack_frame", 0)) + 1
            attack_duration = 25
            if boss._nx_attack_frame >= attack_duration:
                boss._nx_attack_active = False
                boss._nx_attack_frame = 0
                active = False

        attack_duration = 25
        boss._nx_attack_progress = (
            min(1.0, getattr(boss, "_nx_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_nx_last_x"):
            boss._nx_last_x = boss.x
            boss._nx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nx_last_x)
        dy = abs(boss.y - boss._nx_last_y)
        boss._nx_last_x = boss.x
        boss._nx_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.55) * 2)
        _NS_nyxaris._draw_full_body(surface, x, y + bob,
                                    boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_nyxaris._draw_full_body(surface, x + sway, y + bob,
                                    boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_nx_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Small recoil (ranged shooter)
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            ease = 1 - (1 - t) ** 2
            lunge = int((-3 + ease * 8)) * boss.direction
            lift = int(2 - ease * 3)
        else:
            t = (progress - 0.5) / 0.5
            lunge = int(5 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)

        _NS_nyxaris._draw_full_body(surface, x + lunge, y - lift,
                                    boss.direction, boss.pulse, "attack", progress)
        # Basic lunar bolt
        _NS_nyxaris._draw_basic_lunar_bolt(surface, boss, x + lunge,
                                            y - lift, progress)

    # ============================================================
    # FULL BODY
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Cape/coat back (flowing)
        _NS_nyxaris._draw_coat_back(surface, cx, cy, facing, phase)
        # 2. Legs
        _NS_nyxaris._draw_legs(surface, cx, cy, facing, phase, action)
        # 3. Coat front (lower)
        _NS_nyxaris._draw_coat_front(surface, cx, cy, facing, phase)
        # 4. Back arm holding OFF-HAND weapon
        _NS_nyxaris._draw_back_arm_offhand(surface, cx, cy, facing,
                                             phase, action, atk_prog)
        # 5. Torso
        _NS_nyxaris._draw_torso(surface, cx, cy, facing, phase)
        # 6. Head + hair
        _NS_nyxaris._draw_head(surface, cx, cy - 22, facing, phase)
        # 7. Front arm holding MAIN-HAND weapon
        _NS_nyxaris._draw_front_arm_mainhand(surface, cx, cy, facing,
                                              phase, action, atk_prog)

    def _draw_coat_back(surface, cx, cy, facing, phase):
        """Dark coat with crimson lining flowing behind."""
        sway = math.sin(phase * 0.4) * 3
        back_dir = -facing

        coat_pts = [
            (cx + back_dir * 4, cy - 8),
            (cx + back_dir * 10, cy - 4),
            (cx + back_dir * 15, cy + 4),
            (cx + back_dir * 18 + int(sway * back_dir), cy + 16),
            (cx + back_dir * 20 + int(sway * back_dir * 1.5), cy + 28),
            (cx + back_dir * 17 + int(sway * back_dir * 2), cy + 40),
            (cx + back_dir * 10, cy + 44),
            (cx + back_dir * 4, cy + 42),
            (cx, cy + 28),
            (cx + back_dir * 2, cy + 8),
            (cx + back_dir * 3, cy - 4),
        ]
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in coat_pts])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_darkest"], coat_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_dark"], [
            (cx + back_dir * 3, cy - 7),
            (cx + back_dir * 9, cy - 3),
            (cx + back_dir * 14, cy + 5),
            (cx + back_dir * 16 + int(sway * back_dir), cy + 16),
            (cx + back_dir * 18 + int(sway * back_dir * 1.5), cy + 28),
            (cx + back_dir * 14, cy + 40),
            (cx + back_dir * 8, cy + 42),
            (cx + back_dir * 3, cy + 40),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_mid"], [
            (cx + back_dir * 5, cy - 3),
            (cx + back_dir * 12, cy + 4),
            (cx + back_dir * 13 + int(sway * back_dir), cy + 18),
            (cx + back_dir * 10, cy + 30),
            (cx + back_dir * 4, cy + 30),
            (cx + back_dir * 3, cy + 8),
        ])

        # CRIMSON LINING on inner edge (visible when coat flares)
        pygame.draw.line(surface, _NS_nyxaris.PALETTE["crimson_dark"],
                         (cx + back_dir * 4, cy - 4),
                         (cx + back_dir * 6, cy + 30), 2)
        pygame.draw.line(surface, _NS_nyxaris.PALETTE["crimson_mid"],
                         (cx + back_dir * 4, cy - 4),
                         (cx + back_dir * 6, cy + 30), 1)

        # Crimson outer edge (bottom)
        for i in range(3):
            edge_pt = (cx + back_dir * (17 - i * 3) + int(sway * back_dir * 1.5),
                       cy + 40 - i * 4)
            end_pt = (cx + back_dir * (14 - i * 3) + int(sway * back_dir * 1.5),
                      cy + 42 - i * 4)
            pygame.draw.line(surface, _NS_nyxaris.PALETTE["crimson_dark"],
                             edge_pt, end_pt, 2)
            pygame.draw.line(surface, _NS_nyxaris.PALETTE["crimson_mid"],
                             edge_pt, end_pt, 1)

        # Small moon shards floating around cape
        for i in range(3):
            e_t = (phase * 0.4 + i * 0.33) % 1.0
            ex = cx + back_dir * (10 + int(math.sin(phase + i) * 5))
            ey = cy + 10 - int(e_t * 25)
            alpha = _NS_nyxaris._alpha(200 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_nyxaris.PALETTE["moon_shine"], alpha),
                             (ex, ey, 1, 1))

    def _draw_coat_front(surface, cx, cy, facing, phase):
        """Front hem of coat."""
        sway = math.sin(phase * 0.6) * 2
        front_dir = facing

        front_pts = [
            (cx + front_dir * 2, cy - 6),
            (cx + front_dir * 8, cy - 2),
            (cx + front_dir * 12, cy + 8),
            (cx + front_dir * 14, cy + 22),
            (cx + front_dir * 12 + int(sway * front_dir), cy + 34),
            (cx + front_dir * 6, cy + 40),
            (cx, cy + 36),
            (cx + front_dir * 3, cy + 12),
            (cx + front_dir * 2, cy - 2),
        ]
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in front_pts])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_darkest"], front_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_dark"], [
            (cx + front_dir * 3, cy - 4),
            (cx + front_dir * 7, cy - 1),
            (cx + front_dir * 11, cy + 8),
            (cx + front_dir * 13, cy + 22),
            (cx + front_dir * 10 + int(sway * front_dir), cy + 32),
            (cx + front_dir * 5, cy + 38),
            (cx + front_dir * 1, cy + 34),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_mid"], [
            (cx + front_dir * 5, cy),
            (cx + front_dir * 9, cy + 8),
            (cx + front_dir * 10, cy + 22),
            (cx + front_dir * 6, cy + 30),
            (cx + front_dir * 3, cy + 12),
        ])

        # Crimson trim on edge
        pygame.draw.line(surface, _NS_nyxaris.PALETTE["crimson_dark"],
                         (cx + front_dir * 14, cy + 22),
                         (cx + front_dir * 6, cy + 40), 2)
        pygame.draw.line(surface, _NS_nyxaris.PALETTE["crimson_mid"],
                         (cx + front_dir * 14, cy + 22),
                         (cx + front_dir * 6, cy + 40), 1)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Armored legs."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        for leg_i, leg_x_off in enumerate((-4, 4)):
            leg_x = cx + leg_x_off
            leg_y_top = cy + 8
            leg_y_knee = cy + 24
            leg_y_bot = cy + 42 + int((-leg_sway if leg_i == 0 else leg_sway))

            # Thigh
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                                (leg_x + 1, leg_y_top + 1),
                                (leg_x + 1, leg_y_knee + 1), 8)
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_darkest"],
                                (leg_x, leg_y_top), (leg_x, leg_y_knee), 7)
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_dark"],
                                (leg_x, leg_y_top), (leg_x, leg_y_knee), 5)
            # Greave (armor lower leg)
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                                (leg_x + 1, leg_y_knee + 1),
                                (leg_x + 1, leg_y_bot + 1), 8)
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                                (leg_x, leg_y_knee), (leg_x, leg_y_bot), 7)
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["armor_dark"],
                                (leg_x, leg_y_knee), (leg_x, leg_y_bot), 5)
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["armor_mid"],
                                (leg_x - 1, leg_y_knee), (leg_x - 1, leg_y_bot), 2)

            # Knee cap
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                                  (leg_x, leg_y_knee), 3)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_dark"],
                                  (leg_x, leg_y_knee), 2)
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_light"],
                             (leg_x, leg_y_knee - 1, 1, 1))

            # Boot
            pygame.draw.ellipse(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                                (leg_x - 5, leg_y_bot - 1, 12, 6))
            pygame.draw.ellipse(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                                (leg_x - 4, leg_y_bot, 10, 4))
            pygame.draw.ellipse(surface, _NS_nyxaris.PALETTE["armor_dark"],
                                (leg_x - 4, leg_y_bot, 10, 3))
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_mid"],
                             (leg_x - 2, leg_y_bot, 5, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Dark armored torso with crimson high collar."""
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
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_pts])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_darkest"], torso_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_dark"], [
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
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["coat_mid"], [
            (cx - 9, cy - 4),
            (cx - 10, cy + 2),
            (cx - 6, cy + 7),
            (cx + 6, cy + 7),
            (cx + 10, cy + 2),
            (cx + 9, cy - 4),
            (cx + 3, cy - 8),
            (cx - 3, cy - 8),
        ])

        # ARMOR PLATE on chest (dark metal)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                         (cx - 7, cy - 5, 14, 8))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_dark"],
                         (cx - 6, cy - 4, 12, 6))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_mid"],
                         (cx - 5, cy - 3, 10, 4))
        pygame.draw.line(surface, _NS_nyxaris.PALETTE["armor_light"],
                         (cx - 4, cy - 3), (cx + 4, cy - 3), 1)
        # Small moon emblem on chest
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_dark"],
                              (cx, cy), 2)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_light"],
                              (cx, cy), 1)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_shine"],
                         (cx, cy, 1, 1))

        # HIGH CRIMSON COLLAR (upright)
        collar_pts = [
            (cx - 6, cy - 12),
            (cx - 8, cy - 16),
            (cx - 7, cy - 18),
            (cx - 4, cy - 20),
            (cx + 4, cy - 20),
            (cx + 7, cy - 18),
            (cx + 8, cy - 16),
            (cx + 6, cy - 12),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ]
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in collar_pts])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["crimson_darkest"], collar_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["crimson_dark"], [
            (cx - 5, cy - 11),
            (cx - 7, cy - 15),
            (cx - 6, cy - 17),
            (cx - 3, cy - 19),
            (cx + 3, cy - 19),
            (cx + 6, cy - 17),
            (cx + 7, cy - 15),
            (cx + 5, cy - 11),
            (cx, cy - 10),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["crimson_mid"], [
            (cx - 3, cy - 12),
            (cx - 5, cy - 16),
            (cx - 2, cy - 18),
            (cx + 2, cy - 18),
            (cx + 5, cy - 16),
            (cx + 3, cy - 12),
        ])
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["crimson_light"],
                         (cx - 1, cy - 17, 2, 1))

        # Small belt/waist detail
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                         (cx - 13, cy + 7, 27, 4))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                         (cx - 12, cy + 8, 25, 3))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["armor_dark"],
                         (cx - 12, cy + 8, 25, 2))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["crimson_mid"],
                         (cx - 12, cy + 10, 25, 1))
        # Center moon buckle
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                              (cx, cy + 10), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_dark"],
                              (cx, cy + 10), 2)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_light"],
                         (cx, cy + 10, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with dark hair and piercing cyan eyes."""
        # HAIR back (short-medium dark)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"], [
            (cx - 7, cy + 6),
            (cx - 9, cy - 2),
            (cx - 8, cy - 9),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 8, cy - 9),
            (cx + 9, cy - 2),
            (cx + 7, cy + 6),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["hair_darkest"], [
            (cx - 6, cy + 5),
            (cx - 8, cy - 2),
            (cx - 7, cy - 8),
            (cx - 3, cy - 11),
            (cx + 3, cy - 11),
            (cx + 7, cy - 8),
            (cx + 8, cy - 2),
            (cx + 6, cy + 5),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["hair_dark"], [
            (cx - 5, cy - 5),
            (cx - 6, cy - 8),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 6, cy - 8),
            (cx + 5, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["hair_mid"],
                         (cx - 3, cy - 9, 6, 1))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["hair_light"],
                         (cx - 1, cy - 9, 2, 1))

        # FACE
        face_pts = [
            (cx - 5, cy + 5),
            (cx - 6, cy - 2),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 6, cy - 2),
            (cx + 5, cy + 5),
        ]
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["skin_dark"], face_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["skin_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 2),
            (cx + 4, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["skin_light"],
                         (cx - 3, cy - 3, 6, 1))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["skin_shine"],
                         (cx - 1, cy - 3, 2, 1))

        # Hair bangs (parted, falling on forehead)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["hair_darkest"], [
            (cx - 5, cy - 6),
            (cx - 4, cy - 8),
            (cx - 2, cy - 6),
            (cx + 1, cy - 8),
            (cx + 4, cy - 6),
            (cx + 5, cy - 4),
            (cx - 5, cy - 4),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["hair_dark"], [
            (cx - 4, cy - 5),
            (cx - 2, cy - 5),
            (cx + 1, cy - 6),
            (cx + 4, cy - 5),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])

        # EYES (piercing cyan/blue)
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            # Eye white
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["skin_shine"],
                             (ex - 1, ey, 2, 1))
            # Iris
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["eye_dark"],
                             (ex, ey, 1, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_nyxaris._alpha(80 * (3 - r) / 3 * eye_pulse)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["eye_mid"], alpha),
                                      (ex, ey), r)
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["eye_light"],
                             (ex, ey, 1, 1))

        # Serious mouth
        pygame.draw.line(surface, _NS_nyxaris.PALETTE["skin_dark"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

    # ============================================================
    # PRIESTESS SPIRIT (ghostly figure behind boss)
    # ============================================================
    def _draw_priestess_spirit(surface, boss, x, y, phase):
        """Ghostly moon priestess floating behind boss."""
        facing = boss.direction
        # Position: slightly behind and above boss
        back_dir = -facing
        sx = x + back_dir * 20
        sy = y - 25 + int(math.sin(phase * 0.6) * 3)  # gentle floating

        pulse = math.sin(phase * 0.8) * 0.25 + 0.75

        # Ghostly glow around spirit
        for r in range(35, 5, -3):
            alpha = _NS_nyxaris._alpha(50 * (35 - r) / 30 * pulse)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["spirit_dark"], alpha),
                                  (sx, sy), r)

        # Spirit body (ethereal, translucent)
        # Head (small)
        head_alpha = _NS_nyxaris._alpha(180 * pulse)
        head_surf = pygame.Surface((20, 24), pygame.SRCALPHA)

        # Face
        pygame.draw.ellipse(head_surf,
                            (*_NS_nyxaris.PALETTE["spirit_dark"], head_alpha),
                            (5, 3, 10, 12))
        pygame.draw.ellipse(head_surf,
                            (*_NS_nyxaris.PALETTE["spirit_mid"], head_alpha),
                            (6, 4, 8, 10))
        pygame.draw.ellipse(head_surf,
                            (*_NS_nyxaris.PALETTE["spirit_light"], head_alpha),
                            (7, 5, 6, 7))

        # Long flowing hair (ghostly)
        hair_pts = [
            (5, 6),
            (2, 12),
            (0, 20),
            (3, 24),
            (7, 22),
            (10, 16),
            (13, 22),
            (17, 24),
            (20, 20),
            (18, 12),
            (15, 6),
        ]
        pygame.draw.polygon(head_surf,
                            (*_NS_nyxaris.PALETTE["spirit_hair"], head_alpha - 30),
                            hair_pts)

        # Small eyes (glowing)
        pygame.draw.rect(head_surf,
                         (*_NS_nyxaris.PALETTE["spirit_light"], head_alpha),
                         (8, 8, 1, 1))
        pygame.draw.rect(head_surf,
                         (*_NS_nyxaris.PALETTE["spirit_light"], head_alpha),
                         (11, 8, 1, 1))

        surface.blit(head_surf, (sx - 10, sy - 12))

        # BODY (ethereal, tapering down)
        for i in range(20):
            body_t = i / 20
            body_y = sy + 5 + i * 2
            body_w = int(6 - body_t * 4)
            if body_w < 1:
                break
            body_alpha = _NS_nyxaris._alpha(150 * pulse * (1 - body_t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["spirit_dark"], body_alpha),
                                (sx - body_w, body_y, body_w * 2, 3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["spirit_mid"], body_alpha),
                                (sx - body_w + 1, body_y, body_w * 2 - 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_nyxaris.PALETTE["spirit_light"], body_alpha),
                             (sx, body_y, 1, 1))

        # Floating hair strands around
        for i in range(4):
            strand_t = (phase * 0.5 + i * 0.25) % 1.0
            strand_x_off = int(math.sin(phase + i * 2) * 8)
            strand_y_off = int(math.cos(phase + i * 2) * 4)
            strx = sx + strand_x_off
            stry = sy + strand_y_off
            alpha = _NS_nyxaris._alpha(180 * pulse * (1 - strand_t * 0.5))
            pygame.draw.rect(surface,
                             (*_NS_nyxaris.PALETTE["spirit_hair"], alpha),
                             (strx, stry, 1, 3))

        # Small moon over spirit's head
        moon_y = sy - 20 + int(math.sin(phase * 0.8) * 2)
        for r in range(6, 0, -1):
            alpha = _NS_nyxaris._alpha(120 * (6 - r) / 6 * pulse)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                  (sx, moon_y), r)
        # Crescent moon shape
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_dark"],
                              (sx, moon_y), 4)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_shine"],
                              (sx - 1, moon_y), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["spirit_dark"],
                              (sx + 1, moon_y), 3)  # crescent cutout
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_white"],
                         (sx - 2, moon_y - 1, 1, 1))

    # ============================================================
    # ARMS + WEAPONS
    # ============================================================
    def _draw_back_arm_offhand(surface, cx, cy, facing, phase, action, atk_prog):
        """Back arm holding OFF-HAND weapon (purple lunar orb)."""
        sway = math.sin(phase * 0.9) * 1
        back_shoulder_x = cx - facing * 10
        back_shoulder_y = cy - 6

        # Off-hand weapon held down at side
        weapon_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.05
        hand_off_x = -facing * 6
        hand_off_y = int(8 + sway)

        back_hand_x = back_shoulder_x + hand_off_x
        back_hand_y = back_shoulder_y + hand_off_y

        elbow_x = int((back_shoulder_x + back_hand_x) / 2) - facing * 2
        elbow_y = int((back_shoulder_y + back_hand_y) / 2) + 2

        # Arm (dark coat sleeve)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                            (back_shoulder_x + 1, back_shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_darkest"],
                            (back_shoulder_x, back_shoulder_y),
                            (elbow_x, elbow_y), 5)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_dark"],
                            (back_shoulder_x, back_shoulder_y),
                            (elbow_x, elbow_y), 3)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (back_hand_x + 1, back_hand_y + 1), 5)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_darkest"],
                            (elbow_x, elbow_y),
                            (back_hand_x, back_hand_y), 4)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_dark"],
                            (elbow_x, elbow_y),
                            (back_hand_x, back_hand_y), 2)

        # Gauntlet
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                              (back_hand_x, back_hand_y), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_dark"],
                              (back_hand_x, back_hand_y), 2)

        # OFF-HAND WEAPON (purple crescent orb — Gravitum style)
        _NS_nyxaris._draw_offhand_orb(surface, back_hand_x, back_hand_y,
                                       weapon_angle, facing, phase)

    def _draw_front_arm_mainhand(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm holding MAIN-HAND weapon (cyan pistol/scythe)."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 10
        front_shoulder_y = cy - 6

        # Weapon angle
        if action == "attack":
            if atk_prog < 0.3:
                # Aim
                t = atk_prog / 0.3
                weapon_angle = -math.pi * 0.05 - t * 0.05
                hand_off_x = facing * int(4 + t * 4)
                hand_off_y = int(0 - t * 2)
            elif atk_prog < 0.5:
                # Fire (recoil)
                t = (atk_prog - 0.3) / 0.2
                weapon_angle = -math.pi * 0.1 + t * 0.1
                hand_off_x = facing * int(8 - t * 2)
                hand_off_y = int(-2 + t * 1)
            else:
                # Reset
                t = (atk_prog - 0.5) / 0.5
                weapon_angle = 0
                hand_off_x = facing * int(6 - t * 2)
                hand_off_y = int(-1 + t * 1)
        elif action == "walk":
            weapon_angle = -math.pi * 0.1 + math.sin(phase) * 0.03
            hand_off_x = facing * 8
            hand_off_y = int(4 + sway)
        else:
            # Idle: weapon held ready horizontally
            weapon_angle = -math.pi * 0.1 + math.sin(phase * 0.5) * 0.02
            hand_off_x = facing * 8
            hand_off_y = int(4 - sway)

        front_hand_x = front_shoulder_x + hand_off_x
        front_hand_y = front_shoulder_y + hand_off_y

        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 2
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # Arm
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                            (front_shoulder_x + 1, front_shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_darkest"],
                            (front_shoulder_x, front_shoulder_y),
                            (elbow_x, elbow_y), 5)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_dark"],
                            (front_shoulder_x, front_shoulder_y),
                            (elbow_x, elbow_y), 3)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_mid"],
                            (front_shoulder_x - 1, front_shoulder_y - 1),
                            (elbow_x - 1, elbow_y - 1), 1)

        # Elbow
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                              (elbow_x, elbow_y), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_dark"],
                              (elbow_x, elbow_y), 2)

        # Forearm
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_darkest"],
                            (elbow_x, elbow_y),
                            (front_hand_x, front_hand_y), 4)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["coat_dark"],
                            (elbow_x, elbow_y),
                            (front_hand_x, front_hand_y), 2)

        # Hand/gauntlet
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_darkest"],
                              (front_hand_x, front_hand_y), 4)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_dark"],
                              (front_hand_x, front_hand_y), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["armor_mid"],
                              (front_hand_x, front_hand_y), 2)

        # MAIN-HAND WEAPON (cyan lunar rifle/scythe)
        _NS_nyxaris._draw_mainhand_weapon(surface, front_hand_x, front_hand_y,
                                           weapon_angle, facing, phase, action, atk_prog)

    def _draw_mainhand_weapon(surface, hand_x, hand_y, angle, facing, phase,
                               action, atk_prog):
        """Main-hand: elegant lunar rifle/gun with crescent blade."""
        actual_angle = angle if facing > 0 else math.pi - angle

        # Weapon dimensions
        barrel_len = 22
        # Barrel tip
        tip_x = hand_x + int(math.cos(actual_angle) * barrel_len)
        tip_y = hand_y + int(math.sin(actual_angle) * barrel_len)
        # Back of weapon (stock)
        back_x = hand_x - int(math.cos(actual_angle) * 8)
        back_y = hand_y - int(math.sin(actual_angle) * 8)

        perp_x = -math.sin(actual_angle)
        perp_y = math.cos(actual_angle)

        # MAIN BODY (rifle body — dark metal with cyan accents)
        body_pts = [
            (back_x + int(perp_x * 3), back_y + int(perp_y * 3)),
            (tip_x + int(perp_x * 2), tip_y + int(perp_y * 2)),
            (tip_x - int(perp_x * 2), tip_y - int(perp_y * 2)),
            (back_x - int(perp_x * 3), back_y - int(perp_y * 3)),
        ]
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in body_pts])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["weapon_dark"], body_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["weapon_mid"], [
            (back_x + int(perp_x * 2), back_y + int(perp_y * 2)),
            (tip_x + int(perp_x * 1), tip_y + int(perp_y * 1)),
            (tip_x - int(perp_x * 1), tip_y - int(perp_y * 1)),
            (back_x - int(perp_x * 2), back_y - int(perp_y * 2)),
        ])
        # Bright top edge
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["weapon_light"],
                            (back_x + int(perp_x * 2), back_y + int(perp_y * 2)),
                            (tip_x + int(perp_x * 1), tip_y + int(perp_y * 1)), 1)

        # Cyan energy line in center of weapon
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["moon_mid"],
                            (back_x, back_y), (tip_x, tip_y), 1)
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["moon_light"],
                            (int((back_x + tip_x) / 2 - perp_x),
                             int((back_y + tip_y) / 2 - perp_y)),
                            (tip_x, tip_y), 1)

        # CRESCENT BLADE on top (small)
        blade_base_x = tip_x - int(math.cos(actual_angle) * 3)
        blade_base_y = tip_y - int(math.sin(actual_angle) * 3)
        blade_tip_x = blade_base_x + int(perp_x * 6)
        blade_tip_y = blade_base_y + int(perp_y * 6)
        blade_curve_x = blade_base_x + int(perp_x * 4 + math.cos(actual_angle) * 3)
        blade_curve_y = blade_base_y + int(perp_y * 4 + math.sin(actual_angle) * 3)

        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"], [
            (blade_base_x + 1, blade_base_y + 1),
            (blade_curve_x + 1, blade_curve_y + 1),
            (blade_tip_x + 1, blade_tip_y + 1),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["weapon_dark"], [
            (blade_base_x, blade_base_y),
            (blade_curve_x, blade_curve_y),
            (blade_tip_x, blade_tip_y),
        ])
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["weapon_mid"], [
            (blade_base_x, blade_base_y),
            (blade_curve_x, blade_curve_y),
            (int((blade_curve_x + blade_tip_x) / 2),
             int((blade_curve_y + blade_tip_y) / 2)),
        ])
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["weapon_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))

        # BARREL TIP (glowing cyan)
        muzzle_glow = math.sin(phase * 3) * 0.3 + 0.7
        # Bright muzzle when firing
        if action == "attack" and 0.3 < atk_prog < 0.55:
            muzzle_glow = 1.0
            for r in range(8, 0, -1):
                alpha = _NS_nyxaris._alpha(200 * (8 - r) / 8)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                      (tip_x, tip_y), r)

        # Small muzzle glow
        for r in range(4, 0, -1):
            alpha = _NS_nyxaris._alpha(120 * (4 - r) / 4 * muzzle_glow)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                                  (tip_x, tip_y), r)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_light"],
                              (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_shine"],
                         (tip_x, tip_y, 1, 1))

        # Stock end (small back cap)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["weapon_dark"],
                              (back_x, back_y), 2)

    def _draw_offhand_orb(surface, hand_x, hand_y, angle, facing, phase):
        """Off-hand: floating purple crescent moon orb."""
        actual_angle = angle if facing > 0 else math.pi - angle

        # Orb hovers slightly off hand
        orb_dist = 6
        orb_x = hand_x + int(math.cos(actual_angle) * orb_dist)
        orb_y = hand_y + int(math.sin(actual_angle) * orb_dist)

        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Outer glow
        for r in range(10, 0, -1):
            alpha = _NS_nyxaris._alpha(100 * (10 - r) / 10 * pulse)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_light"], alpha),
                                  (orb_x, orb_y), r)

        # Crescent moon shape (purple)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_darkest"],
                              (orb_x, orb_y), 5)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_dark"],
                              (orb_x, orb_y), 4)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_mid"],
                              (orb_x, orb_y), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_light"],
                              (orb_x - 1, orb_y - 1), 2)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["purple_shine"],
                         (orb_x - 1, orb_y - 1, 1, 1))

        # Crescent cutout (darker inside)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["coat_darkest"],
                              (orb_x + 2, orb_y), 3)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_darkest"],
                              (orb_x + 2, orb_y), 2)

        # Connecting energy wisps between hand and orb
        for i in range(3):
            wisp_t = (phase * 3 + i * 0.3) % 1.0
            wx = int(hand_x + (orb_x - hand_x) * wisp_t)
            wy = int(hand_y + (orb_y - hand_y) * wisp_t)
            alpha = _NS_nyxaris._alpha(150 * (1 - wisp_t))
            pygame.draw.rect(surface,
                             (*_NS_nyxaris.PALETTE["purple_hot"], alpha),
                             (wx, wy, 1, 1))

    # ============================================================
    # BASIC ATTACK — LUNAR BOLT
    # ============================================================
    def _draw_basic_lunar_bolt(surface, boss, x, y, progress):
        """Cyan lunar bolt projectile."""
        if progress < 0.3:
            return
        facing = boss.direction
        tx, ty = _NS_nyxaris._target_position(boss, x, y)

        # Origin at gun muzzle
        start_x = x + facing * 28
        start_y = y - 6

        t = (progress - 0.3) / 0.7
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Elongated bolt (arrow-like)
        angle = math.atan2(ty - start_y, tx - start_x)
        bolt_len = 12
        tip_x = bx + int(math.cos(angle) * bolt_len)
        tip_y = by + int(math.sin(angle) * bolt_len)
        tail_x = bx - int(math.cos(angle) * bolt_len)
        tail_y = by - int(math.sin(angle) * bolt_len)

        # Trail
        for i in range(6):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxaris._alpha(220 - i * 30)
            size = max(1, 5 - i)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["moon_dark"], alpha),
                                  (px, py), size)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                  (px, py), max(1, size - 2))

        # Arrow head
        perp_x = -math.sin(angle) * 2
        perp_y = math.cos(angle) * 2
        arrow_pts = [
            (tip_x, tip_y),
            (bx + int(perp_x), by + int(perp_y)),
            (tail_x, tail_y),
            (bx - int(perp_x), by - int(perp_y)),
        ]
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_dark"], arrow_pts)
        _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_mid"], [
            (tip_x, tip_y),
            (bx + int(perp_x * 0.6), by + int(perp_y * 0.6)),
            (tail_x, tail_y),
            (bx - int(perp_x * 0.6), by - int(perp_y * 0.6)),
        ])
        _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["moon_light"],
                            (tail_x, tail_y), (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_white"],
                         (tip_x, tip_y, 1, 1))

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

    def _draw_lunar_aura(surface, x, y, phase):
        """Cool cyan/purple aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_nyxaris._alpha((80 - radius) * 0.8 * pulse)
            if alpha > 0:
                _NS_nyxaris._aacircle(aura,
                                      (*_NS_nyxaris.PALETTE["moon_darkest"], alpha),
                                      (100, 85), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_nyxaris._alpha((50 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_nyxaris._aacircle(aura,
                                      (*_NS_nyxaris.PALETTE["moon_dark"], alpha),
                                      (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))

        # Purple mix
        aura2 = pygame.Surface((160, 130), pygame.SRCALPHA)
        for radius in range(35, 5, -3):
            alpha = _NS_nyxaris._alpha((35 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxaris._aacircle(aura2,
                                      (*_NS_nyxaris.PALETTE["purple_dark"], alpha),
                                      (80, 65), radius)
        surface.blit(aura2, (x - 80, y - 65))

        # Floating moon particles (cyan + purple mix)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 36 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_nyxaris.PALETTE["moon_mid"] if i % 2 == 0 \
                else _NS_nyxaris.PALETTE["purple_mid"]
            highlight = _NS_nyxaris.PALETTE["moon_shine"] if i % 2 == 0 \
                else _NS_nyxaris.PALETTE["purple_shine"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, highlight, (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Lunar ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxaris.PALETTE["moon_darkest"], 200),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxaris.PALETTE["moon_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxaris.PALETTE["purple_dark"], 200),
                            (25, 21, 110, 16), 1)

        # Runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_nyxaris.PALETTE["moon_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_nyxaris.PALETTE["moon_shine"],
                                 _NS_nyxaris._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — PHASE SHOT (long-range piercing bolt)
    # ============================================================
    def _draw_phase_shot_fx(surface, boss, x, y, timer, phase):
        """Massive piercing cyan bolt."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxaris._target_position(boss, x, y)

        start_x = x + facing * 28
        start_y = y - 6

        if progress < 0.15:
            # Charge at barrel tip
            t = progress / 0.15
            r = int(4 + t * 10)
            for lr in range(r + 5, 0, -1):
                alpha = _NS_nyxaris._alpha(180 * (r + 5 - lr) / (r + 5))
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                                      (start_x, start_y), lr)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_darkest"],
                                  (start_x, start_y), r - 2)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_light"],
                                  (start_x, start_y), max(1, r - 4))
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_shine"],
                                  (start_x, start_y), max(1, r - 6))
        else:
            t = (progress - 0.15) / 0.85
            t = min(1.0, t)
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            angle = math.atan2(ty - start_y, tx - start_x)

            # HUGE piercing beam trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_nyxaris._alpha(240 - i * 22)
                size = max(1, 9 - i)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_darkest"], alpha),
                                      (px, py), size)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_dark"], alpha),
                                      (px, py), max(1, size - 1))
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                                      (px, py), max(1, size - 2))
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                      (px, py), max(1, size - 3))

                # Sparks around
                if i < 4:
                    for si in range(3):
                        sp_off = math.sin(t * 6 + i + si) * (size + 2)
                        sp_x = px + int(math.cos(angle + math.pi / 2) * sp_off)
                        sp_y = py + int(math.sin(angle + math.pi / 2) * sp_off)
                        pygame.draw.rect(surface,
                                         (*_NS_nyxaris.PALETTE["moon_shine"], alpha),
                                         (sp_x, sp_y, 1, 1))

            # BOLT HEAD (large elongated arrow)
            bolt_len = 20
            tip_x = bx + int(math.cos(angle) * bolt_len)
            tip_y = by + int(math.sin(angle) * bolt_len)
            perp_x = -math.sin(angle) * 4
            perp_y = math.cos(angle) * 4

            bolt_pts = [
                (tip_x, tip_y),
                (bx + int(perp_x), by + int(perp_y)),
                (bx - int(math.cos(angle) * 8), by - int(math.sin(angle) * 8)),
                (bx - int(perp_x), by - int(perp_y)),
            ]
            _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_darkest"], bolt_pts)
            _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_dark"], [
                (tip_x, tip_y),
                (bx + int(perp_x * 0.6), by + int(perp_y * 0.6)),
                (bx - int(math.cos(angle) * 6), by - int(math.sin(angle) * 6)),
                (bx - int(perp_x * 0.6), by - int(perp_y * 0.6)),
            ])
            _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_mid"], [
                (tip_x, tip_y),
                (bx + int(perp_x * 0.3), by + int(perp_y * 0.3)),
                (bx, by),
                (bx - int(perp_x * 0.3), by - int(perp_y * 0.3)),
            ])
            _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["moon_shine"],
                                (bx - int(math.cos(angle) * 6),
                                 by - int(math.sin(angle) * 6)),
                                (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_white"],
                             (tip_x, tip_y, 1, 1))

            # Bright glow around head
            for r in range(10, 3, -1):
                alpha = _NS_nyxaris._alpha(80 * (10 - r) / 10)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                      (bx, by), r)

            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                r = int(15 + st * 20)
                alpha = _NS_nyxaris._alpha(240 * (1 - st))
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_darkest"], alpha),
                                      (tx, ty), r + 3, 3)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_dark"], alpha),
                                      (tx, ty), r, 3)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                                      (tx, ty), max(1, r - 6), 2)
                for i in range(10):
                    a = i * math.pi / 5
                    ex = tx + int(math.cos(a) * r)
                    ey = ty + int(math.sin(a) * r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_nyxaris.PALETTE["moon_shine"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL W — MOONLIGHT VIGIL (purple AoE circle)
    # ============================================================
    def _draw_moonlight_vigil_ground(surface, boss, x, y, timer, phase):
        """Purple ground circle."""
        tx, ty = _NS_nyxaris._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["purple_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["purple_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["purple_mid"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_moonlight_vigil_fg(surface, boss, x, y, timer, phase):
        """Dome/bubble of purple energy at target."""
        tx, ty = _NS_nyxaris._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 45
        breath = math.sin(phase * 2) * 2
        actual_r = r + int(breath)

        # Dome
        dome = pygame.Surface((actual_r * 2 + 20, actual_r * 2 + 20), pygame.SRCALPHA)
        center = (actual_r + 10, actual_r + 10)

        # Layered rings
        for i, (thickness, alpha_val) in enumerate([
            (3, 140), (2, 180), (1, 220),
        ]):
            _NS_nyxaris._aacircle(dome,
                                  (*_NS_nyxaris.PALETTE["purple_dark"], alpha_val),
                                  center, actual_r - i, thickness)
            _NS_nyxaris._aacircle(dome,
                                  (*_NS_nyxaris.PALETTE["purple_mid"], alpha_val),
                                  center, actual_r - i - 1, 1)

        # Rotating sparkles on edge
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * actual_r)
            sy = center[1] + int(math.sin(angle) * actual_r)
            pygame.draw.rect(dome, _NS_nyxaris.PALETTE["purple_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(dome, _NS_nyxaris.PALETTE["purple_shine"],
                             (sx, sy, 1, 1))

        # Grid pattern inside dome (constellation lines)
        for i in range(6):
            a1 = i * math.pi / 3 + phase * 0.3
            a2 = (i + 2) * math.pi / 3 + phase * 0.3
            x1 = center[0] + int(math.cos(a1) * (actual_r - 5))
            y1 = center[1] + int(math.sin(a1) * (actual_r - 5))
            x2 = center[0] + int(math.cos(a2) * (actual_r - 5))
            y2 = center[1] + int(math.sin(a2) * (actual_r - 5))
            pygame.draw.line(dome,
                             (*_NS_nyxaris.PALETTE["purple_hot"], 100),
                             (x1, y1), (x2, y2), 1)

        surface.blit(dome, (tx - actual_r - 10, ty - actual_r - 10))

        # Inner particles
        for i in range(8):
            p_angle = phase * 0.5 + i * math.pi / 4
            p_r = actual_r - 12
            px = tx + int(math.cos(p_angle) * p_r)
            py = ty + int(math.sin(p_angle) * p_r)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_light"],
                                  (px, py), 2)
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["purple_shine"],
                             (px, py, 1, 1))

    # ============================================================
    # SKILL E — GRAVITUM FLUX (purple orb skillshot)
    # ============================================================
    def _draw_gravitum_fx(surface, boss, x, y, timer, phase):
        """Purple orb traveling to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxaris._target_position(boss, x, y)

        # Origin at off-hand
        start_x = x - facing * 6
        start_y = y + 4

        t = min(1.0, progress)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxaris._alpha(230 - i * 24)
            size = max(1, 7 - i)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_darkest"], alpha),
                                  (px, py), size)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_mid"], alpha),
                                  (px, py), max(1, size - 2))
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_light"], alpha),
                                  (px, py), max(1, size - 3))

        # Main orb (crescent moon)
        for r in range(12, 3, -1):
            alpha = _NS_nyxaris._alpha(100 * (12 - r) / 12)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_light"], alpha),
                                  (bx, by), r)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_darkest"],
                              (bx, by), 6)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_dark"],
                              (bx, by), 5)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_mid"],
                              (bx, by), 4)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_light"],
                              (bx - 1, by - 1), 2)
        pygame.draw.rect(surface, _NS_nyxaris.PALETTE["purple_shine"],
                         (bx - 1, by - 1, 1, 1))

        # Crescent cutout
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["shadow_deep"],
                              (bx + 3, by), 4)
        _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["purple_darkest"],
                              (bx + 3, by), 3)

        # Orbiting sparkles
        for i in range(6):
            orb_angle = phase * 4 + i * math.pi / 3
            orb_r = 10 + int(math.sin(phase * 2 + i) * 3)
            ox = bx + int(math.cos(orb_angle) * orb_r)
            oy = by + int(math.sin(orb_angle) * orb_r)
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["purple_hot"],
                             (ox, oy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["purple_shine"],
                             (ox, oy, 1, 1))

        # Impact
        if t > 0.92:
            st = (t - 0.92) / 0.08
            r = int(20 + st * 25)
            alpha = _NS_nyxaris._alpha(230 * (1 - st))
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_darkest"], alpha),
                                  (tx, ty), r + 2, 3)
            _NS_nyxaris._aacircle(surface,
                                  (*_NS_nyxaris.PALETTE["purple_mid"], alpha),
                                  (tx, ty), r, 2)
            for i in range(10):
                a = i * math.pi / 5
                ex = tx + int(math.cos(a) * r)
                ey = ty + int(math.sin(a) * r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_nyxaris.PALETTE["purple_hot"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL R — MOONLIGHT DESCENT (rain of bolts)
    # ============================================================
    def _draw_descent_ground(surface, boss, x, y, timer, phase):
        """Large ring at target."""
        tx, ty = _NS_nyxaris._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["moon_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["moon_dark"], 200),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxaris.PALETTE["moon_mid"], 180),
                                (tx - r + 12, ty - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12))
            # Sparkles
            for i in range(10):
                angle = phase * 0.5 + i * math.pi / 5
                sx = tx + int(math.cos(angle) * r * 0.85)
                sy = ty + int(math.sin(angle) * r * 0.3)
                pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_shine"],
                                 (sx, sy, 2, 2))

    def _draw_descent_fg(surface, boss, x, y, timer, phase):
        """Rain of moon bolts falling from sky at target."""
        tx, ty = _NS_nyxaris._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = 60

        # Charge up phase — big moon appears above target
        if progress < 0.25:
            t = progress / 0.25
            moon_y = ty - 120 + int(t * 30)
            moon_r = int(6 + t * 15)
            # Big moon
            for lr in range(moon_r + 10, 0, -1):
                alpha = _NS_nyxaris._alpha(150 * (moon_r + 10 - lr) / (moon_r + 10) * t)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                      (tx, moon_y), lr)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_dark"],
                                  (tx, moon_y), moon_r)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_mid"],
                                  (tx, moon_y), moon_r - 2)
            _NS_nyxaris._aacircle(surface, _NS_nyxaris.PALETTE["moon_light"],
                                  (tx - 2, moon_y - 2), moon_r - 5)
            pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_shine"],
                             (tx - 3, moon_y - 3, 2, 2))
        else:
            # RAIN OF BOLTS phase
            t = (progress - 0.25) / 0.75

            # Multiple bolts falling in the AoE area
            num_bolts = 12
            for bolt_i in range(num_bolts):
                # Bolt timing (staggered)
                bolt_delay = (bolt_i / num_bolts) * 0.7
                bolt_t = ((phase * 2 + bolt_i * 0.3) % 1.0)

                if bolt_t < 0.05:
                    continue

                # Random position within radius
                angle_off = (bolt_i * 2.3) % (math.pi * 2)
                dist = (bolt_i * 0.35 + t * 0.3) % 1.0
                bx = tx + int(math.cos(angle_off) * r * dist * 0.85)
                by = ty + int(math.sin(angle_off) * r * dist * 0.35)

                # Bolt falls from top
                fall_start_y = -50
                fall_end_y = by
                current_y = int(fall_start_y + (fall_end_y - fall_start_y) * bolt_t)

                # Bolt shape
                bolt_len = 14
                # Draw falling arrow
                tip_y = current_y + bolt_len
                perp = 2

                # Shadow
                _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["shadow_deep"], [
                    (bx + 1, tip_y + 1),
                    (bx + perp + 1, current_y + 5 + 1),
                    (bx + 1, current_y + 1),
                    (bx - perp + 1, current_y + 5 + 1),
                ])
                # Bolt
                _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_darkest"], [
                    (bx, tip_y),
                    (bx + perp, current_y + 5),
                    (bx, current_y),
                    (bx - perp, current_y + 5),
                ])
                _NS_nyxaris._poly(surface, _NS_nyxaris.PALETTE["moon_dark"], [
                    (bx, tip_y),
                    (bx + perp - 1, current_y + 6),
                    (bx, current_y + 1),
                    (bx - perp + 1, current_y + 6),
                ])
                _NS_nyxaris._aaline(surface, _NS_nyxaris.PALETTE["moon_light"],
                                    (bx, current_y), (bx, tip_y), 1)
                pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_shine"],
                                 (bx, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_nyxaris.PALETTE["moon_white"],
                                 (bx, tip_y, 1, 1))

                # Trail line (falling streak)
                for i in range(4):
                    trail_y = current_y - i * 6
                    if trail_y < 0:
                        break
                    alpha = _NS_nyxaris._alpha(200 - i * 40)
                    pygame.draw.line(surface,
                                     (*_NS_nyxaris.PALETTE["moon_mid"], alpha),
                                     (bx, trail_y), (bx, trail_y + 5), 2)
                    pygame.draw.line(surface,
                                     (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                     (bx, trail_y), (bx, trail_y + 5), 1)

                # Impact splash when reached
                if bolt_t > 0.85:
                    st = (bolt_t - 0.85) / 0.15
                    imp_r = int(6 + st * 12)
                    imp_alpha = _NS_nyxaris._alpha(230 * (1 - st))
                    _NS_nyxaris._aacircle(surface,
                                          (*_NS_nyxaris.PALETTE["moon_mid"], imp_alpha),
                                          (bx, by), imp_r, 2)
                    for si in range(6):
                        sa = si * math.pi / 3
                        sx = bx + int(math.cos(sa) * imp_r)
                        sy = by + int(math.sin(sa) * imp_r)
                        pygame.draw.rect(surface,
                                         (*_NS_nyxaris.PALETTE["moon_shine"], imp_alpha),
                                         (sx, sy, 2, 2))

            # Central bright glow
            central_pulse = math.sin(phase * 3) * 0.3 + 0.7
            for lr in range(20, 3, -2):
                alpha = _NS_nyxaris._alpha(80 * (20 - lr) / 20 * central_pulse)
                _NS_nyxaris._aacircle(surface,
                                      (*_NS_nyxaris.PALETTE["moon_light"], alpha),
                                      (tx, ty), lr)


# ====================================================================
# ALIAS
# ====================================================================
draw_nyxaris = _NS_nyxaris.draw_nyxaris


# ====================================================================================================
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ====================================================================================================
def draw_garumenshi(surface, boss, x, y):
    """Entry point garumenshi."""
    return _NS_garumenshi.draw_garumenshi(surface, boss, x, y)

def draw_thoraz(surface, boss, x, y):
    """Entry point thoraz."""
    return _NS_thoraz.draw_thoraz(surface, boss, x, y)

def draw_vhaerith(surface, boss, x, y):
    """Entry point vhaerith."""
    return _NS_vhaerith.draw_vhaerith(surface, boss, x, y)

def draw_nyxaris(surface, boss, x, y):
    """Entry point nyxaris."""
    return _NS_nyxaris.draw_nyxaris(surface, boss, x, y)
