"""
bosses/level34.py - Semua boss Level 34

Berisi:
  - infrakzaar  (mini boss - RANGED emberflesh pyromancer)
  - xarnathul   (mini boss - RANGED deathsinger, soul magic)
  - zhyrakaan   (mini boss - MELEE phantomweave lancer)
  - grondmauris (TRUE BOSS - MELEE earthborn colossus, earth golem)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _ik_ (infrakzaar), _xar_ (xarnathul), _zh_ (zhyrakaan),
    _grn_ (grondmauris) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# INFRAKZAAR (EMBERFLESH PYROMANCER) - Mini Boss
# ====================================================================

class _NS_infrakzaar:
    """Namespace infrakzaar - burning pyromancer mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Charred/obsidian skin (very dark base)
        "char_darkest": (5, 3, 3),
        "char_dark": (18, 12, 10),
        "char_mid": (40, 28, 22),
        "char_light": (70, 50, 42),
        "char_shine": (110, 85, 70),
        # Lava cracks (bright orange-red, glowing)
        "lava_darkest": (60, 12, 3),
        "lava_dark": (140, 35, 8),
        "lava_mid": (230, 90, 20),
        "lava_light": (255, 165, 50),
        "lava_hot": (255, 220, 130),
        "lava_shine": (255, 250, 210),
        # Fire (flames, projectiles)
        "fire_darkest": (55, 10, 5),
        "fire_dark": (130, 35, 10),
        "fire_mid": (220, 90, 25),
        "fire_light": (255, 155, 55),
        "fire_hot": (255, 215, 130),
        "fire_shine": (255, 250, 220),
        # Skull (exposed bone at head top)
        "bone_dark": (55, 40, 30),
        "bone_mid": (130, 105, 80),
        "bone_light": (200, 175, 145),
        "bone_shine": (240, 220, 190),
        # Glowing white-yellow eyes (empty burning sockets)
        "eye_socket": (5, 2, 0),
        "eye_dark": (85, 30, 5),
        "eye_mid": (240, 145, 30),
        "eye_light": (255, 230, 130),
        "eye_glow": (255, 255, 220),
        # Loincloth (torn dark fabric)
        "cloth_dark": (25, 15, 10),
        "cloth_mid": (55, 35, 22),
        "cloth_light": (95, 65, 40),
        # Ground molten (skill FX)
        "molten_dark": (85, 20, 5),
        "molten_mid": (200, 70, 15),
        "molten_light": (255, 150, 45),
        "molten_shine": (255, 245, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 1),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_infrakzaar._clamp(color)
        if _NS_infrakzaar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_infrakzaar._clamp(color)
        if _NS_infrakzaar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_infrakzaar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    def _arm_elbow(shoulder, hand, bend=4, bend_up=False):
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        if bend_up:
            if perp_y > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        else:
            if perp_y < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    def _fist_position(boss, x, y):
        """Position of front fist (source of projectiles)."""
        facing = boss.direction
        active = getattr(boss, "_ik_attack_active", False)
        progress = getattr(boss, "_ik_attack_progress", 0.0)
        if active:
            if progress < 0.35:
                t = progress / 0.35
                fx = x + facing * int(10 - t * 6)
                fy = y - 6
            elif progress < 0.55:
                t = (progress - 0.35) / 0.2
                fx = x + facing * int(4 + t * 26)
                fy = y - 6
            elif progress < 0.75:
                fx = x + facing * 30
                fy = y - 6
            else:
                t = (progress - 0.75) / 0.25
                fx = x + facing * int(30 - t * 20)
                fy = y - 6
        else:
            fx = x + facing * 14
            fy = y - 8
        return fx, fy
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_infrakzaar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_infrakzaar._update_attack_anim(boss)
        attack_progress = getattr(boss, "_ik_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_ik_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )
        # Ambient FX.
        _NS_infrakzaar._draw_ember_aura(surface, x, y, pulse)
        _NS_infrakzaar._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_infrakzaar._draw_pillar_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_infrakzaar._draw_conflagration_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_infrakzaar._draw_cataclysm_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body.
        float_bob = math.sin(pulse * 0.7) * 5
        body_y = y + int(float_bob)
        # Rising flame particles under body.
        _NS_infrakzaar._draw_rising_flames(surface, x, body_y + 40, pulse)
        # Body pose.
        if active_skill == "q":
            _NS_infrakzaar._draw_body_qcast(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif active_skill == "w":
            _NS_infrakzaar._draw_body_wcast(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif active_skill == "e":
            _NS_infrakzaar._draw_body_ecast(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif active_skill == "r":
            _NS_infrakzaar._draw_body_rcast(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif attacking:
            _NS_infrakzaar._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_infrakzaar._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX.
        if active_skill == "q":
            _NS_infrakzaar._draw_sear_projectile(surface, boss, x, body_y,
                                                  skill_timer, pulse)
        elif active_skill == "w":
            _NS_infrakzaar._draw_pillar_flame(surface, boss, x, body_y,
                                                skill_timer, pulse)
        elif active_skill == "e":
            _NS_infrakzaar._draw_conflagration_wave(surface, boss, x, body_y,
                                                     skill_timer, pulse)
        elif active_skill == "r":
            _NS_infrakzaar._draw_cataclysm_meteor(surface, boss, x, body_y,
                                                    skill_timer, pulse)
        else:
            if attacking and attack_progress > 0:
                _NS_infrakzaar._draw_basic_fireball(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_ik_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._ik_attack_active = True
            boss._ik_attack_frame = 0
            active = True
        elif active:
            boss._ik_attack_frame = int(getattr(boss, "_ik_attack_frame", 0)) + 1
            if boss._ik_attack_frame >= cooldown:
                boss._ik_attack_active = False
                boss._ik_attack_frame = 0
                active = False
        boss._ik_previous_timer = timer
        boss._ik_attack_progress = (
            min(1.0, getattr(boss, "_ik_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_infrakzaar._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_infrakzaar._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_ik_attack_progress", 0.0)
        _NS_infrakzaar._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_infrakzaar._draw_body(surface, boss, cx, cy, "throw", progress)
    def _draw_body_qcast(surface, boss, cx, cy, timer, phase):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_infrakzaar._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_infrakzaar._draw_body(surface, boss, cx, cy, "throw", progress)
    def _draw_body_wcast(surface, boss, cx, cy, timer, phase):
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_infrakzaar._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_infrakzaar._draw_body(surface, boss, cx, cy, "point_down", progress)
    def _draw_body_ecast(surface, boss, cx, cy, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_infrakzaar._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_infrakzaar._draw_body(surface, boss, cx, cy, "sweep", progress)
    def _draw_body_rcast(surface, boss, cx, cy, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_infrakzaar._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_infrakzaar._draw_body(surface, boss, cx, cy, "raise_up", progress)
    # ============================================================
    # MAIN BODY
    # ============================================================
    def _draw_body(surface, boss, cx, cy, action, progress):
        facing = boss.direction
        phase = boss.pulse
        # Body base (charred with lava cracks) - drawn from bottom up.
        # Loincloth/lower body.
        _NS_infrakzaar._draw_lower_body(surface, cx, cy, facing, phase)
        # Torso.
        _NS_infrakzaar._draw_torso(surface, cx, cy, facing, phase)
        # Head (skull + flames).
        _NS_infrakzaar._draw_head(surface, cx, cy - 24, facing, phase, action)
        # Arms with flaming fists.
        _NS_infrakzaar._draw_arms(surface, cx, cy, facing, phase, action, progress)
    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Legs + loincloth."""
        # Legs.
        for side in (-1, 1):
            leg_x = cx + side * 6
            # Thigh (charred with lava cracks).
            thigh_pts = [
                (leg_x - 4, cy + 8),
                (leg_x + 4, cy + 8),
                (leg_x + 5, cy + 18),
                (leg_x + 3, cy + 28),
                (leg_x - 3, cy + 28),
                (leg_x - 5, cy + 18),
            ]
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                                 [(p[0] + 1, p[1] + 2) for p in thigh_pts])
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_darkest"], thigh_pts)
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_dark"], [
                (leg_x - 3, cy + 9),
                (leg_x + 3, cy + 9),
                (leg_x + 4, cy + 18),
                (leg_x + 2, cy + 27),
                (leg_x - 2, cy + 27),
                (leg_x - 4, cy + 18),
            ])
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_mid"], [
                (leg_x - 2, cy + 10),
                (leg_x + 2, cy + 10),
                (leg_x + 3, cy + 18),
                (leg_x + 1, cy + 25),
                (leg_x - 1, cy + 25),
                (leg_x - 3, cy + 18),
            ])
            # Lava cracks on leg.
            crack_pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
            # Vertical crack.
            for i in range(3):
                cy_off = cy + 12 + i * 5
                pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_darkest"],
                                 (leg_x - 1, cy_off), (leg_x + 1, cy_off + 2), 1)
                pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_mid"],
                                 (leg_x, cy_off), (leg_x, cy_off + 2), 1)
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"],
                                 (leg_x, cy_off, 1, 1))
            # Foot (charred, lava tips).
            foot_pts = [
                (leg_x - 5, cy + 28),
                (leg_x + 5, cy + 28),
                (leg_x + 6, cy + 32),
                (leg_x - 5, cy + 32),
            ]
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                                 [(p[0] + 1, p[1] + 1) for p in foot_pts])
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_darkest"], foot_pts)
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_dark"], [
                (leg_x - 4, cy + 29),
                (leg_x + 4, cy + 29),
                (leg_x + 5, cy + 31),
                (leg_x - 4, cy + 31),
            ])
            # Glowing toe cracks.
            for i in range(3):
                toe_x = leg_x - 3 + i * 3
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_dark"],
                                 (toe_x, cy + 30, 1, 2))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_mid"],
                                 (toe_x, cy + 31, 1, 1))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"],
                                 (toe_x, cy + 31, 1, 1))
        # Loincloth (tattered cloth around waist).
        sway = math.sin(phase * 0.6) * 2
        cloth_pts = [
            (cx - 12, cy + 4),
            (cx - 14 + int(sway), cy + 8),
            (cx - 12 + int(sway), cy + 20),
            (cx - 6 + int(sway * 0.5), cy + 24),
            (cx, cy + 22),
            (cx + 6 - int(sway * 0.5), cy + 24),
            (cx + 12 - int(sway), cy + 20),
            (cx + 14 - int(sway), cy + 8),
            (cx + 12, cy + 4),
        ]
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in cloth_pts])
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["cloth_dark"], cloth_pts)
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["cloth_mid"], [
            (cx - 11, cy + 5),
            (cx - 13 + int(sway), cy + 8),
            (cx - 11 + int(sway), cy + 18),
            (cx - 5 + int(sway * 0.5), cy + 22),
            (cx, cy + 20),
            (cx + 5 - int(sway * 0.5), cy + 22),
            (cx + 11 - int(sway), cy + 18),
            (cx + 13 - int(sway), cy + 8),
            (cx + 11, cy + 5),
        ])
        # Highlights.
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["cloth_light"],
                         (cx - 12, cy + 6), (cx - 13 + int(sway), cy + 10), 1)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["cloth_light"],
                         (cx + 12, cy + 6), (cx + 13 - int(sway), cy + 10), 1)
        # Torn edges glowing.
        for x_off in (-8, -3, 3, 8):
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_dark"],
                             (cx + x_off + int(sway * 0.3), cy + 22, 1, 2))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular torso with lava cracks."""
        breath = math.sin(phase * 0.7) * 1
        torso_pts = [
            (cx - 12, cy - 14),
            (cx - 14, cy - 6),
            (cx - 12, cy + 4),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 12, cy + 4),
            (cx + 14, cy - 6),
            (cx + 12, cy - 14),
            (cx + 6, cy - 18),
            (cx - 6, cy - 18),
        ]
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_darkest"], torso_pts)
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_dark"], [
            (cx - 11, cy - 13),
            (cx - 13, cy - 6),
            (cx - 11, cy + 3),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 11, cy + 3),
            (cx + 13, cy - 6),
            (cx + 11, cy - 13),
            (cx + 5, cy - 17),
            (cx - 5, cy - 17),
        ])
        # Muscle midtones.
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_mid"], [
            (cx - 8, cy - 10),
            (cx - 10, cy - 4),
            (cx - 8, cy + 3),
            (cx + 8, cy + 3),
            (cx + 10, cy - 4),
            (cx + 8, cy - 10),
            (cx + 4, cy - 14),
            (cx - 4, cy - 14),
        ])
        # Pec highlights (charred).
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["char_light"], (cx - 6, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["char_light"], (cx + 4, cy - 8, 2, 1))
        # LAVA CRACKS across torso (SIGNATURE FEATURE).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Vertical crack down center of chest.
        crack_center = [
            (cx, cy - 16),
            (cx - 1, cy - 12),
            (cx + 1, cy - 8),
            (cx, cy - 4),
            (cx - 1, cy),
            (cx + 1, cy + 4),
            (cx, cy + 8),
        ]
        for i in range(len(crack_center) - 1):
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_darkest"],
                             crack_center[i], crack_center[i + 1], 2)
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_dark"],
                             crack_center[i], crack_center[i + 1], 1)
        # Glowing lava inside cracks.
        for p in crack_center:
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_mid"], (p[0], p[1], 1, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"], (p[0], p[1], 1, 1))
        # Side cracks (branching outward).
        for side in (-1, 1):
            branch_pts = [
                (cx + side * 2, cy - 10),
                (cx + side * 5, cy - 8),
                (cx + side * 7, cy - 4),
                (cx + side * 9, cy),
                (cx + side * 8, cy + 4),
                (cx + side * 5, cy + 6),
            ]
            for i in range(len(branch_pts) - 1):
                pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_darkest"],
                                 branch_pts[i], branch_pts[i + 1], 1)
                pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_mid"],
                                 branch_pts[i], branch_pts[i + 1], 1)
            # Bright spots along cracks.
            for p in branch_pts[::2]:
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"], (p[0], p[1], 1, 1))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_shine"], (p[0], p[1], 1, 1))
        # Small ember dots on torso (glowing points).
        for i, (px_o, py_o) in enumerate([(-9, -6), (7, -10), (-5, 2), (8, 4), (-8, -2)]):
            ember_pulse = math.sin(phase * 3 + i) * 0.4 + 0.6
            alpha_e = _NS_infrakzaar._alpha(240 * ember_pulse)
            pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["lava_mid"], alpha_e),
                             (cx + px_o, cy + py_o, 1, 1))
            pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["lava_hot"], alpha_e),
                             (cx + px_o, cy + py_o, 1, 1))
        # Small flame wisps rising from cracks.
        for i in range(4):
            wisp_t = ((phase * 0.6 + i * 0.25) % 1.0)
            wx = cx - 4 + i * 3
            wy = cy - 10 - int(wisp_t * 8)
            alpha_w = _NS_infrakzaar._alpha(200 * (1 - wisp_t))
            if alpha_w > 0:
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha_w),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha_w),
                                 (wx, wy - 1, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Charred head with EXPOSED SKULL TOP + flames erupting."""
        # Lower face (still fleshy but charred).
        face_pts = [
            (cx - 6, cy),
            (cx - 7, cy + 3),
            (cx - 5, cy + 7),
            (cx - 2, cy + 9),
            (cx + 2, cy + 9),
            (cx + 5, cy + 7),
            (cx + 7, cy + 3),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_darkest"], face_pts)
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 3),
            (cx - 4, cy + 6),
            (cx - 1, cy + 8),
            (cx + 1, cy + 8),
            (cx + 4, cy + 6),
            (cx + 6, cy + 3),
            (cx + 5, cy + 1),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["char_mid"], [
            (cx - 3, cy + 2),
            (cx - 4, cy + 4),
            (cx - 2, cy + 6),
            (cx + 2, cy + 6),
            (cx + 4, cy + 4),
            (cx + 3, cy + 2),
        ])
        # Cheek highlights.
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["char_light"], (cx - 3, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["char_light"], (cx + 2, cy + 3, 1, 1))
        # Lava crack down face.
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_darkest"],
                         (cx, cy), (cx, cy + 6), 2)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_mid"],
                         (cx, cy), (cx, cy + 6), 1)
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"], (cx, cy + 3, 1, 1))
        # EXPOSED SKULL TOP (bone visible where flesh burned away).
        skull_pts = [
            (cx - 6, cy),
            (cx - 5, cy - 4),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in skull_pts])
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["bone_dark"], skull_pts)
        _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["bone_mid"], [
            (cx - 5, cy - 1),
            (cx - 4, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 4, cy - 4),
            (cx + 5, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Bone highlight.
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["bone_light"], (cx - 1, cy - 5, 2, 1))
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["bone_shine"], (cx, cy - 5, 1, 1))
        # Skull sutures (bone lines).
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["bone_dark"],
                         (cx, cy - 8), (cx, cy - 3), 1)
        # BURNING EYES (empty sockets glowing).
        _NS_infrakzaar._draw_burning_eyes(surface, cx, cy, phase, action)
        # Mouth (fanged burning).
        _NS_infrakzaar._draw_burning_mouth(surface, cx, cy, phase, action)
        # FLAMES ERUPTING FROM SKULL TOP (main feature).
        _NS_infrakzaar._draw_head_flames(surface, cx, cy - 6, phase)
    def _draw_burning_eyes(surface, cx, cy, phase, action):
        """Empty eye sockets with intense fire glow."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.5 if action != "idle" else 1.0
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy + 1
            # Deep socket.
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Glow halo (BIG bright orange-yellow).
            for r in range(6, 0, -1):
                alpha = _NS_infrakzaar._alpha(150 * (6 - r) / 6 * pulse * intensity)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["eye_mid"], alpha),
                                         (ex, ey), r)
            # Empty glowing eye.
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["eye_glow"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (ex, ey, 1, 1))
            # Small fire wisp above eye.
            wisp_alpha = _NS_infrakzaar._alpha(200 * pulse * intensity)
            wy_off = int(math.sin(phase * 3 + side) * 1) - 2
            pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], wisp_alpha),
                             (ex, ey + wy_off, 1, 1))
    def _draw_burning_mouth(surface, cx, cy, phase, action):
        """Mouth with fangs and inner fire glow."""
        # Open mouth showing fire inside.
        if action in ("throw", "sweep", "point_down", "raise_up") and phase % 1 < 0.7:
            # Roaring open mouth.
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["shadow_deep"], [
                (cx - 3, cy + 5),
                (cx + 3, cy + 5),
                (cx + 2, cy + 8),
                (cx - 2, cy + 8),
            ])
            # Fire inside.
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["fire_darkest"], [
                (cx - 2, cy + 5),
                (cx + 2, cy + 5),
                (cx + 2, cy + 7),
                (cx - 2, cy + 7),
            ])
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["fire_mid"], [
                (cx - 1, cy + 5),
                (cx + 1, cy + 5),
                (cx + 1, cy + 7),
                (cx - 1, cy + 7),
            ])
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_hot"], (cx, cy + 6, 1, 1))
            # Fangs.
            for fx in (-2, 2):
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["bone_mid"], (cx + fx, cy + 5, 1, 2))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["bone_light"], (cx + fx, cy + 6, 1, 1))
        else:
            # Grim closed grin with fire seeping out.
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                             (cx - 3, cy + 6), (cx + 3, cy + 6), 1)
            # Fangs peek.
            for fx in (-2, 2):
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["bone_mid"], (cx + fx, cy + 6, 1, 1))
            # Fire glow between teeth.
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_hot"], (cx, cy + 6, 1, 1))
    def _draw_head_flames(surface, cx, cy, phase):
        """Big flames erupting from top of skull."""
        # Multi-layered flame going up.
        for flame_i in range(5):
            offset_x = (flame_i - 2) * 2
            flame_pulse = math.sin(phase * 3 + flame_i * 0.7) * 2
            # Flame height varies.
            flame_top_y = cy - 12 - int(flame_pulse) - flame_i
            flame_base_y = cy - 2
            base_x = cx + offset_x
            top_x = cx + offset_x + int(math.sin(phase * 2 + flame_i) * 1)
            # Flame shape (teardrop).
            flame_pts = [
                (base_x - 2, flame_base_y),
                (base_x + 2, flame_base_y),
                (top_x + 1, flame_top_y + 4),
                (top_x, flame_top_y),
                (top_x - 1, flame_top_y + 4),
            ]
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["fire_darkest"], flame_pts)
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["fire_dark"], [
                (base_x - 1, flame_base_y),
                (base_x + 1, flame_base_y),
                (top_x + 1, flame_top_y + 5),
                (top_x, flame_top_y + 1),
                (top_x - 1, flame_top_y + 5),
            ])
            _NS_infrakzaar._poly(surface, _NS_infrakzaar.PALETTE["fire_mid"], [
                (base_x, flame_base_y),
                (base_x + 1, flame_base_y - 2),
                (top_x, flame_top_y + 3),
                (top_x - 1, flame_top_y + 5),
                (base_x - 1, flame_base_y - 2),
            ])
            # Bright core.
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["fire_hot"],
                             (base_x, flame_base_y - 2), (top_x, flame_top_y + 3), 1)
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_shine"],
                             (top_x, flame_top_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"],
                             (top_x, flame_top_y, 1, 1))
        # Rising sparks.
        for i in range(6):
            spark_t = ((phase * 0.8 + i * 0.17) % 1.0)
            sx = cx + int(math.sin(phase + i) * 4) - 3 + i
            sy = cy - 4 - int(spark_t * 20)
            alpha = _NS_infrakzaar._alpha(240 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                 (sx, sy - 1, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress):
        """Two arms with flaming fists. Pose varies per action."""
        front_sh = (cx + facing * 12, cy - 12)
        back_sh = (cx - facing * 12, cy - 12)
        # Determine hand positions.
        if action == "throw":
            # Front hand throws fireball, back hand pulled back.
            if progress < 0.35:
                t = progress / 0.35
                front_hand_x = cx + facing * int(10 - t * 6)
                front_hand_y = cy - 8 - int(t * 4)
                back_hand_x = cx - facing * int(8 + t * 4)
                back_hand_y = cy - 4
            elif progress < 0.55:
                t = (progress - 0.35) / 0.2
                front_hand_x = cx + facing * int(4 + t * 26)
                front_hand_y = cy - 12 + int(t * 6)
                back_hand_x = cx - facing * int(12 - t * 6)
                back_hand_y = cy - 4
            elif progress < 0.75:
                front_hand_x = cx + facing * 30
                front_hand_y = cy - 6
                back_hand_x = cx - facing * 6
                back_hand_y = cy - 4
            else:
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(30 - t * 20)
                front_hand_y = cy - 6
                back_hand_x = cx - facing * int(6 + t * 4)
                back_hand_y = cy - 4
        elif action == "point_down":
            # W: Point down at target.
            if progress < 0.5:
                t = progress / 0.5
                front_hand_x = cx + facing * int(8 + t * 8)
                front_hand_y = cy - int(8 - t * 8)  # goes down
            else:
                t = (progress - 0.5) / 0.5
                front_hand_x = cx + facing * int(16 - t * 8)
                front_hand_y = cy + int(t * -4)  # returns up
            back_hand_x = cx - facing * 6
            back_hand_y = cy - 4
        elif action == "sweep":
            # E: Sweep sideways with wave.
            if progress < 0.35:
                t = progress / 0.35
                front_hand_x = cx + facing * int(6 - t * 10)
                front_hand_y = cy - 8
            elif progress < 0.6:
                t = (progress - 0.35) / 0.25
                front_hand_x = cx + facing * int(-4 + t * 30)
                front_hand_y = cy - 6
            else:
                t = (progress - 0.6) / 0.4
                front_hand_x = cx + facing * int(26 - t * 16)
                front_hand_y = cy - 6
            back_hand_x = cx - facing * 6
            back_hand_y = cy - 4
        elif action == "raise_up":
            # R: Both hands raised to sky (summon meteor).
            if progress < 0.5:
                t = progress / 0.5
                front_hand_x = cx + facing * int(6 + t * 4)
                front_hand_y = cy - int(8 + t * 18)
                back_hand_x = cx - facing * int(6 + t * 4)
                back_hand_y = cy - int(8 + t * 18)
            elif progress < 0.75:
                # Hold at top.
                front_hand_x = cx + facing * 10
                front_hand_y = cy - 26
                back_hand_x = cx - facing * 10
                back_hand_y = cy - 26
            else:
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(10 - t * 4)
                front_hand_y = cy - int(26 - t * 18)
                back_hand_x = cx - facing * int(10 - t * 4)
                back_hand_y = cy - int(26 - t * 18)
        else:
            # Idle: hands at sides with subtle bob.
            idle_sway = math.sin(phase * 0.8) * 1
            front_hand_x = cx + facing * 12
            front_hand_y = cy - 4 + int(idle_sway)
            back_hand_x = cx - facing * 10
            back_hand_y = cy - 2 + int(idle_sway)
        front_elbow = _NS_infrakzaar._arm_elbow(front_sh, (front_hand_x, front_hand_y), bend=4)
        back_elbow = _NS_infrakzaar._arm_elbow(back_sh, (back_hand_x, back_hand_y), bend=4)
        # Draw back arm.
        _NS_infrakzaar._draw_arm_segment(surface, back_sh, back_elbow,
                                          (back_hand_x, back_hand_y), phase,
                                          charging=(action == "raise_up"))
        # Front arm.
        _NS_infrakzaar._draw_arm_segment(surface, front_sh, front_elbow,
                                          (front_hand_x, front_hand_y), phase,
                                          charging=(action == "raise_up" or action == "point_down"))
    def _draw_arm_segment(surface, shoulder, elbow, hand, phase, charging=False):
        """Draw charred arm with lava cracks + flaming fist."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        # Upper arm.
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 6)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["char_darkest"],
                         (sx, sy), (ex, ey), 5)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["char_dark"],
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["char_mid"],
                         (sx, sy - 1), (ex, ey - 1), 2)
        # Lava crack along upper arm.
        mid_up_x = (sx + ex) // 2
        mid_up_y = (sy + ey) // 2
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_dark"],
                         (sx, sy), (ex, ey), 1)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_mid"],
                         (mid_up_x, mid_up_y - 1),
                         (mid_up_x + 1, mid_up_y + 1), 1)
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"], (mid_up_x, mid_up_y, 1, 1))
        # Forearm.
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 5)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["char_darkest"],
                         (ex, ey), (hx, hy), 4)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["char_dark"],
                         (ex, ey), (hx, hy), 3)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["char_mid"],
                         (ex, ey - 1), (hx, hy - 1), 1)
        # Lava crack along forearm.
        mid_fore_x = (ex + hx) // 2
        mid_fore_y = (ey + hy) // 2
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_dark"],
                         (ex, ey), (hx, hy), 1)
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"], (mid_fore_x, mid_fore_y, 1, 1))
        # FLAMING FIST.
        _NS_infrakzaar._draw_flaming_fist(surface, hx, hy, phase, charging)
    def _draw_flaming_fist(surface, fx, fy, phase, charging=False):
        """Fist wrapped in fire."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.6 if charging else 1.0
        # BIG fire aura around fist.
        aura_r = int((6 + math.sin(phase * 3) * 1) * intensity)
        for r in range(aura_r + 8, 0, -1):
            alpha = _NS_infrakzaar._alpha(70 * (aura_r + 8 - r) / (aura_r + 8) * pulse * intensity)
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                     (fx, fy), r)
        for r in range(aura_r + 4, 0, -1):
            alpha = _NS_infrakzaar._alpha(120 * (aura_r + 4 - r) / (aura_r + 4) * pulse * intensity)
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                     (fx, fy), r)
        # Fist (charred with lava).
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["shadow_deep"], (fx + 1, fy + 1), 4)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["char_darkest"], (fx, fy), 4)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["char_dark"], (fx, fy), 3)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["char_mid"], (fx, fy - 1), 2)
        # Lava cracks on fist.
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_dark"],
                         (fx - 2, fy - 1), (fx + 2, fy + 1), 1)
        pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_mid"],
                         (fx - 1, fy), (fx + 1, fy), 1)
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["lava_hot"], (fx, fy, 1, 1))
        # Flame tongues rising.
        for i in range(5):
            angle = i * math.pi / 4 - math.pi / 2
            flame_len = int((6 + math.sin(phase * 4 + i) * 2) * intensity)
            fx_end = fx + int(math.cos(angle) * flame_len)
            fy_end = fy + int(math.sin(angle) * flame_len)
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["fire_dark"],
                             (fx, fy), (fx_end, fy_end), 2)
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["fire_mid"],
                             (fx, fy), (fx_end, fy_end), 1)
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_hot"], (fx_end, fy_end, 1, 1))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_shine"], (fx_end, fy_end, 1, 1))
        # Sparks orbiting.
        for i in range(4):
            spark_t = (phase * 3 + i * 0.25) % 1.0
            spark_r = int(aura_r + 5 + spark_t * 3)
            angle = phase * 4 + i * math.pi / 2
            spx = fx + int(math.cos(angle) * spark_r)
            spy = fy + int(math.sin(angle) * spark_r)
            alpha = _NS_infrakzaar._alpha(240 * (1 - spark_t) * intensity)
            pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                             (spx, spy, 1, 1))
    # ============================================================
    # BASIC ATTACK: Fireball projectile
    # ============================================================
    def _draw_basic_fireball(surface, boss, x, y):
        """Small fireball throw."""
        progress = getattr(boss, "_ik_attack_progress", 0.0)
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        sx, sy = _NS_infrakzaar._fist_position(boss, x, y)
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(sx + (tx - sx) * t)
        by = int(sy + (ty - sy) * t)
        # Trail (fire streaks).
        for i in range(9):
            trail_t = max(0.0, t - i * 0.04)
            px = int(sx + (tx - sx) * trail_t)
            py = int(sy + (ty - sy) * trail_t)
            alpha = _NS_infrakzaar._alpha(230 - i * 22)
            size = max(1, 6 - i)
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_darkest"], alpha),
                                     (px, py), size + 1)
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                     (px, py), size)
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                     (px, py), max(1, size - 3))
            # Sparks.
            if i < 4:
                for s in range(2):
                    sp_angle = t * 6 + i + s * math.pi
                    sp_r = size + 2
                    spx = px + int(math.cos(sp_angle) * sp_r)
                    spy = py + int(math.sin(sp_angle) * sp_r)
                    pygame.draw.rect(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                     (spx, spy, 1, 1))
        # Bright fireball head.
        for r in range(10, 0, -1):
            alpha = _NS_infrakzaar._alpha(100 * (10 - r) / 10)
            _NS_infrakzaar._aacircle(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                     (bx, by), r)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_darkest"], (bx, by), 7)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_dark"], (bx, by), 5)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_mid"], (bx, by), 3)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_hot"], (bx, by), 2)
        _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (bx, by, 1, 1))
        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            imp_r = int(10 + st * 15)
            alpha = _NS_infrakzaar._alpha(240 * (1 - st))
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                     (tx, ty), imp_r + 2, 3)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                     (tx, ty), imp_r, 2)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                     (tx, ty), max(1, imp_r - 5), 1)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                     (tx, ty), max(1, imp_r // 3))
            for i in range(8):
                ang = i * math.pi / 4
                ex = tx + int(math.cos(ang) * imp_r)
                ey = ty + int(math.sin(ang) * imp_r * 0.7)
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha), (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        breath = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, int((12 - radius) * 15 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - radius, 13 - radius,
                                 106 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (20, 5, 3, int(170 * breath)),
                            (10, 8, 110, 10))
        surface.blit(shadow, (x - 65, y - 13))
    def _draw_rising_flames(surface, cx, cy, phase):
        """Small fire particles rising from ground under body."""
        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            dx = cx + int(math.sin(phase + i * 0.6) * 28) - 14 + i * 3
            dy = cy - int(t * 24)
            alpha = _NS_infrakzaar._alpha(230 * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                 (dx, dy, 2, 2))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                 (dx, dy, 1, 1))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                 (dx, dy - 1, 1, 1))
    def _draw_ember_aura(surface, x, y, phase):
        """Ember-orange aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_infrakzaar._alpha((95 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_infrakzaar._aacircle(aura,
                                         (*_NS_infrakzaar.PALETTE["fire_darkest"], alpha),
                                         (110, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_infrakzaar._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_infrakzaar._aacircle(aura,
                                         (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                         (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Ember particles.
        for i in range(16):
            angle = phase * 0.4 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_infrakzaar.PALETTE["fire_mid"] if i % 2 == 0 else _NS_infrakzaar.PALETTE["fire_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_infrakzaar.PALETTE["fire_darkest"], 200),
                            (5, 18, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_infrakzaar.PALETTE["fire_dark"], 220),
                            (14, 20, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_infrakzaar.PALETTE["fire_mid"], 180),
                            (25, 22, 130, 18), 1)
        # Rune spikes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_infrakzaar.PALETTE["fire_hot"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_infrakzaar.PALETTE["fire_shine"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_infrakzaar.PALETTE["fire_shine"],
                                        _NS_infrakzaar._alpha(160 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 28))
    # ============================================================
    # SKILL Q: SEAR (enhanced fireball)
    # ============================================================
    def _draw_sear_projectile(surface, boss, x, y, timer, phase):
        """Bigger fireball with more intense trail."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        sx, sy = _NS_infrakzaar._fist_position(boss, x, y)
        if progress < 0.35:
            # Charge at fist.
            t = progress / 0.35
            cr = int(5 + t * 8)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_infrakzaar._alpha(180 * (cr + 6 - r) / (cr + 6) * t)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                         (sx, sy), r)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_light"], (sx, sy), max(1, cr - 2))
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_hot"], (sx, sy), max(1, cr - 4))
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_shine"], (sx, sy), max(1, cr - 6))
        else:
            # Fireball flying.
            t = (progress - 0.35) / 0.65
            t = min(1.0, t)
            bx = int(sx + (tx - sx) * t)
            by = int(sy + (ty - sy) * t)
            # BIGGER trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(sx + (tx - sx) * trail_t)
                py = int(sy + (ty - sy) * trail_t)
                alpha = _NS_infrakzaar._alpha(240 - i * 18)
                size = max(1, 9 - i)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_darkest"], alpha),
                                         (px, py), size + 1)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                         (px, py), size)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                         (px, py), max(1, size - 2))
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                         (px, py), max(1, size - 4))
                # Extra sparks.
                if i < 6:
                    for s in range(3):
                        sp_ang = t * 8 + i + s * 2
                        sp_r = size + 2
                        spx = px + int(math.cos(sp_ang) * sp_r)
                        spy = py + int(math.sin(sp_ang) * sp_r)
                        pygame.draw.rect(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                         (spx, spy, 1, 1))
            # BIG fireball head with corona.
            for r in range(14, 3, -2):
                alpha = _NS_infrakzaar._alpha(100 * (14 - r) / 14)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_light"], alpha),
                                         (bx, by), r)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_darkest"], (bx, by), 9)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_dark"], (bx, by), 7)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_mid"], (bx, by), 5)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_hot"], (bx, by), 3)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_shine"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (bx, by, 1, 1))
            # Impact burst.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                imp_r = int(15 + st * 22)
                alpha = _NS_infrakzaar._alpha(255 * (1 - st))
                _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_darkest"], alpha),
                                         (tx, ty), imp_r + 3, 3)
                _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                         (tx, ty), imp_r, 3)
                _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                         (tx, ty), max(1, imp_r - 6), 2)
                _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                         (tx, ty), max(1, imp_r - 12), 1)
                _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                         (tx, ty), max(1, imp_r // 3))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
                # Radial rays.
                for i in range(10):
                    ang = i * math.pi / 5
                    ex = tx + int(math.cos(ang) * imp_r)
                    ey = ty + int(math.sin(ang) * imp_r * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W: PILLAR OF FLAME
    # ============================================================
    def _draw_pillar_ground(surface, boss, x, y, timer, phase):
        """Ground marker + crater at target."""
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Growing warning circle.
            t = progress / 0.3
            r = int(22 * t)
            alpha = _NS_infrakzaar._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_mid"], alpha),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 2)
            # Runes.
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_shine"], (sx, sy, 2, 2))
        else:
            # Crater during & after pillar.
            t = (progress - 0.3) / 0.7
            r = int(24 - t * 4)
            pulse_a = int(math.sin(phase * 3) * 30 + 200)
            alpha = _NS_infrakzaar._alpha(pulse_a * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_light"], alpha),
                                (tx - r + 7, ty - r // 3 + 4,
                                 r * 2 - 14, r * 2 // 3 - 8))
    def _draw_pillar_flame(surface, boss, x, y, timer, phase):
        """Vertical pillar of flame at target."""
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return  # only warning marker shows
        # PILLAR of flames.
        t = (progress - 0.3) / 0.4
        if t > 1.0:
            t = 1.0
        # Pillar height grows fast.
        pillar_h = int(t * 65) if progress < 0.7 else int(65 * (1 - (progress - 0.7) / 0.3))
        # Draw pillar from ground up.
        # Multi-layer teardrop shape.
        for layer_i, (width_scale, color) in enumerate([
            (1.2, _NS_infrakzaar.PALETTE["fire_darkest"]),
            (1.0, _NS_infrakzaar.PALETTE["fire_dark"]),
            (0.75, _NS_infrakzaar.PALETTE["fire_mid"]),
            (0.5, _NS_infrakzaar.PALETTE["fire_hot"]),
            (0.25, _NS_infrakzaar.PALETTE["fire_shine"]),
        ]):
            base_w = int(14 * width_scale)
            # Flickering.
            flicker = math.sin(phase * 4 + layer_i) * 2
            top_x = tx + int(flicker)
            # Teardrop shape.
            for seg in range(6):
                seg_t = seg / 5
                seg_y = ty - int(seg_t * pillar_h)
                # Width narrows toward top.
                w = int(base_w * (1 - seg_t * 0.7))
                if w < 1:
                    w = 1
                pygame.draw.rect(surface, color,
                                 (top_x - w // 2 + int(math.sin(phase * 3 + seg) * 1),
                                  seg_y - 4, w, 8))
        # Flame tongues at top.
        top_y = ty - pillar_h
        for i in range(3):
            angle = -math.pi / 2 + (i - 1) * 0.3
            f_len = 6 + int(math.sin(phase * 4 + i) * 2)
            fx = tx + int(math.cos(angle) * f_len)
            fy = top_y + int(math.sin(angle) * f_len)
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["fire_hot"],
                             (tx, top_y), (fx, fy), 2)
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_shine"], (fx, fy, 1, 1))
        # Rising sparks along pillar.
        for i in range(12):
            spark_t = ((phase * 2 + i * 0.1) % 1.0)
            sy_pos = ty - int(spark_t * pillar_h)
            sx_pos = tx + int(math.sin(phase * 5 + i) * 5)
            alpha = _NS_infrakzaar._alpha(240 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha), (sx_pos, sy_pos, 2, 2))
            pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha), (sx_pos, sy_pos, 1, 1))
        # Ground burst at base.
        if progress < 0.5:
            burst_t = (progress - 0.3) / 0.2
            burst_alpha = _NS_infrakzaar._alpha(240 * (1 - burst_t))
            burst_r = int(15 + burst_t * 12)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_dark"], burst_alpha),
                                     (tx, ty), burst_r + 2, 2)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], burst_alpha),
                                     (tx, ty), burst_r, 2)
            for i in range(10):
                ang = i * math.pi / 5
                ex = tx + int(math.cos(ang) * burst_r)
                ey = ty + int(math.sin(ang) * burst_r * 0.6)
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], burst_alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL E: CONFLAGRATION (wave of fire in front)
    # ============================================================
    def _draw_conflagration_ground(surface, boss, x, y, timer, phase):
        """Burning ground path from boss to target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        if 0.3 < progress < 0.85:
            t = (progress - 0.3) / 0.55
            start_x = x + facing * 20
            start_y = y + 44
            # Fire path glowing on ground.
            for i in range(15):
                path_t = i / 14
                # Only show up to current wave progress.
                if path_t > t + 0.1:
                    continue
                px = int(start_x + (tx - start_x) * path_t)
                py = int(start_y + (ty - start_y) * path_t * 0.3)
                alpha = _NS_infrakzaar._alpha(230 * (1 - (t - path_t)))
                pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_dark"], alpha),
                                    (px - 12, py - 3, 24, 6))
                pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_mid"], alpha),
                                    (px - 9, py - 2, 18, 4))
                pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_light"], alpha),
                                    (px - 6, py - 1, 12, 2))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["molten_shine"], alpha),
                                 (px, py, 1, 1))
    def _draw_conflagration_wave(surface, boss, x, y, timer, phase):
        """Wave of fire traveling forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        sx, sy = _NS_infrakzaar._fist_position(boss, x, y)
        if progress < 0.3:
            # Charge: flames gather at hand.
            t = progress / 0.3
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_infrakzaar._alpha(200 * (cr + 5 - r) / (cr + 5) * t)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                         (sx, sy), r)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_light"], (sx, sy), max(1, cr - 2))
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_hot"], (sx, sy), max(1, cr - 4))
        elif progress < 0.85:
            # WAVE traveling forward.
            t = (progress - 0.3) / 0.55
            intensity = math.sin(t * math.pi)
            # Position along path.
            cur_end_x = int(sx + (tx - sx) * t)
            cur_end_y = int(sy + (ty - sy) * t)
            # Direction & perpendicular.
            dx = tx - sx
            dy = ty - sy
            length = max(1, math.sqrt(dx * dx + dy * dy))
            dir_x = dx / length
            dir_y = dy / length
            perp_x = -dir_y
            perp_y = dir_x
            # Wave front (wider at head).
            wave_width = 20
            head_a = (cur_end_x + int(perp_x * wave_width),
                      cur_end_y + int(perp_y * wave_width))
            head_b = (cur_end_x - int(perp_x * wave_width),
                      cur_end_y - int(perp_y * wave_width))
            head_tip = (cur_end_x + int(dir_x * 10),
                        cur_end_y + int(dir_y * 10))
            # Draw wave shape (like arrow-head made of fire).
            alpha_w = _NS_infrakzaar._alpha(240 * intensity)
            _NS_infrakzaar._poly(surface, (*_NS_infrakzaar.PALETTE["fire_darkest"], alpha_w), [
                (sx, sy), head_a, head_tip, head_b,
            ])
            _NS_infrakzaar._poly(surface, (*_NS_infrakzaar.PALETTE["fire_dark"], alpha_w), [
                (sx + int(dir_x * 2), sy + int(dir_y * 2)),
                (head_a[0] - int(perp_x * 3), head_a[1] - int(perp_y * 3)),
                (head_tip[0] - int(dir_x * 2), head_tip[1] - int(dir_y * 2)),
                (head_b[0] + int(perp_x * 3), head_b[1] + int(perp_y * 3)),
            ])
            _NS_infrakzaar._poly(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha_w), [
                (sx + int(dir_x * 4), sy + int(dir_y * 4)),
                (head_a[0] - int(perp_x * 8), head_a[1] - int(perp_y * 8)),
                (head_tip[0] - int(dir_x * 4), head_tip[1] - int(dir_y * 4)),
                (head_b[0] + int(perp_x * 8), head_b[1] + int(perp_y * 8)),
            ])
            # Bright core line.
            pygame.draw.line(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha_w),
                             (sx, sy), head_tip, 3)
            pygame.draw.line(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha_w),
                             (sx, sy), head_tip, 1)
            # Sparks along wave.
            for i in range(12):
                sp_t = ((phase * 3 + i * 0.08) % 1.0)
                sp_pos_x = int(sx + (cur_end_x - sx) * sp_t)
                sp_pos_y = int(sy + (cur_end_y - sy) * sp_t)
                offset = math.sin(phase * 5 + i) * 8
                spx = sp_pos_x + int(perp_x * offset)
                spy = sp_pos_y + int(perp_y * offset)
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha_w),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha_w),
                                 (spx, spy, 1, 1))
        else:
            # Aftermath: burning residue.
            t = (progress - 0.85) / 0.15
            for i in range(8):
                rise_t = (phase * 0.7 + i * 0.12) % 1.0
                rx = int(sx + (tx - sx) * (i / 7)) + int(math.sin(phase + i) * 4)
                ry = int(sy + (ty - sy) * (i / 7)) - int(rise_t * 20)
                alpha = _NS_infrakzaar._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                     (rx, ry, 1, 1))
    # ============================================================
    # SKILL R: CATACLYSM (meteor from sky)
    # ============================================================
    def _draw_cataclysm_ground(surface, boss, x, y, timer, phase):
        """Ground marker + crater after meteor impact."""
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Warning: growing runic circle.
            t = progress / 0.5
            r = int(35 * t)
            alpha = _NS_infrakzaar._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_light"], 150 * t),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)
            # Runes rotating.
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["fire_shine"], (sx, sy, 1, 1))
        else:
            # Post-impact: massive crater.
            t = (progress - 0.5) / 0.5
            r = int(45 - t * 8)
            alpha = _NS_infrakzaar._alpha(240 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_mid"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_light"], alpha),
                                (tx - r + 12, ty - r // 3 + 5,
                                 r * 2 - 24, r * 2 // 3 - 10))
            pygame.draw.ellipse(surface, (*_NS_infrakzaar.PALETTE["molten_shine"], alpha),
                                (tx - r + 20, ty - r // 3 + 8,
                                 r * 2 - 40, r * 2 // 3 - 16))
    def _draw_cataclysm_meteor(surface, boss, x, y, timer, phase):
        """Massive meteor falling from sky onto target."""
        tx, ty = _NS_infrakzaar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Charge: fire orbs forming above boss's raised hands.
            t = progress / 0.5
            # Big charging orb above boss.
            orb_x = x
            orb_y = y - 30 - int(t * 8)
            cr = int(6 + t * 10)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_infrakzaar._alpha(160 * (cr + 8 - r) / (cr + 8) * t)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                         (orb_x, orb_y), r)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_light"], (orb_x, orb_y), max(1, cr - 2))
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_hot"], (orb_x, orb_y), max(1, cr - 4))
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_shine"], (orb_x, orb_y), max(1, cr - 6))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (orb_x, orb_y, 1, 1))
            # Sparks converging.
            for i in range(12):
                angle = phase * 3 + i * math.pi / 6
                spark_dist = int(25 * (1 - t))
                spx = orb_x + int(math.cos(angle) * spark_dist)
                spy = orb_y + int(math.sin(angle) * spark_dist)
                alpha_s = _NS_infrakzaar._alpha(240 * t)
                pygame.draw.line(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha_s),
                                 (spx, spy), (orb_x, orb_y), 1)
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha_s), (spx, spy, 1, 1))
        elif progress < 0.75:
            # METEOR FALLING from sky.
            t = (progress - 0.5) / 0.25
            # Starts high above screen, ends at target.
            meteor_start_y = max(0, ty - 300)
            meteor_x = tx
            meteor_y = int(meteor_start_y + (ty - meteor_start_y) * t)
            # Meteor size.
            meteor_r = int(12 + t * 6)
            # Fire tail behind meteor (going up).
            tail_len = 80
            for i in range(15):
                trail_t = i / 14
                trail_y = meteor_y - int(trail_t * tail_len)
                trail_x = meteor_x + int(math.sin(trail_t * 4) * 3)
                alpha = _NS_infrakzaar._alpha(240 * (1 - trail_t))
                size = max(1, meteor_r - int(trail_t * meteor_r))
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_darkest"], alpha),
                                         (trail_x, trail_y), size + 1)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_dark"], alpha),
                                         (trail_x, trail_y), size)
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                         (trail_x, trail_y), max(1, size - 2))
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                         (trail_x, trail_y), max(1, size - 4))
            # Sparks/embers scattering from tail.
            for i in range(10):
                em_t = ((phase * 3 + i * 0.1) % 1.0)
                em_y = meteor_y - int(em_t * tail_len)
                em_x = meteor_x + int(math.sin(phase * 5 + i) * 15)
                alpha = _NS_infrakzaar._alpha(240 * (1 - em_t))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                 (em_x, em_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                 (em_x, em_y, 1, 1))
            # BIG METEOR head.
            for r in range(meteor_r + 8, 0, -1):
                alpha = _NS_infrakzaar._alpha(140 * (meteor_r + 8 - r) / (meteor_r + 8))
                _NS_infrakzaar._aacircle(surface,
                                         (*_NS_infrakzaar.PALETTE["fire_light"], alpha),
                                         (meteor_x, meteor_y), r)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["char_darkest"], (meteor_x, meteor_y), meteor_r)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_darkest"], (meteor_x, meteor_y), meteor_r - 1)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_dark"], (meteor_x, meteor_y), meteor_r - 3)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_mid"], (meteor_x, meteor_y), meteor_r - 5)
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_hot"], (meteor_x, meteor_y), max(1, meteor_r - 7))
            _NS_infrakzaar._aacircle(surface, _NS_infrakzaar.PALETTE["fire_shine"], (meteor_x, meteor_y), max(1, meteor_r - 9))
            # Meteor cracks (lava inside).
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["lava_hot"],
                             (meteor_x - meteor_r + 2, meteor_y),
                             (meteor_x + meteor_r - 2, meteor_y), 2)
            pygame.draw.line(surface, _NS_infrakzaar.PALETTE["fire_shine"],
                             (meteor_x, meteor_y - meteor_r + 2),
                             (meteor_x, meteor_y + meteor_r - 2), 1)
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"],
                             (meteor_x - 1, meteor_y - 1, 2, 2))
        elif progress < 0.85:
            # MASSIVE EXPLOSION at target.
            t = (progress - 0.75) / 0.1
            intensity = math.sin(t * math.pi)
            impact_r = int(25 + t * 40)
            impact_alpha = _NS_infrakzaar._alpha(255 * intensity)
            # Multi-layer explosion.
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_darkest"], impact_alpha),
                                     (tx, ty), impact_r + 5, 4)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_dark"], impact_alpha),
                                     (tx, ty), impact_r, 3)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], impact_alpha),
                                     (tx, ty), max(1, impact_r - 8), 3)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], impact_alpha),
                                     (tx, ty), max(1, impact_r - 16), 2)
            _NS_infrakzaar._aacircle(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], impact_alpha),
                                     (tx, ty), max(1, impact_r - 24))
            pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (tx - 2, ty - 2, 4, 4))
            # Radial fire rays.
            for i in range(16):
                ang = i * math.pi / 8
                ex = tx + int(math.cos(ang) * impact_r)
                ey = ty + int(math.sin(ang) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], impact_alpha),
                                 (tx, ty), (ex, ey), 3)
                pygame.draw.line(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], impact_alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], impact_alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface, _NS_infrakzaar.PALETTE["white"], (ex, ey, 1, 1))
        else:
            # Aftermath: lingering fire + rising embers.
            t = (progress - 0.85) / 0.15
            for i in range(15):
                rise_t = (phase * 0.7 + i * 0.07) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 35)
                alpha = _NS_infrakzaar._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_hot"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface, (*_NS_infrakzaar.PALETTE["fire_shine"], alpha),
                                     (rx, ry - 1, 1, 1))



# ====================================================================
# XARNATHUL (DEATHSINGER) - Mini Boss
# ====================================================================

class _NS_xarnathul:
    """Namespace xarnathul - lich deathsinger."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Robe/cloth (dark obsidian black-blue)
        "robe_darkest": (2, 4, 8),
        "robe_dark": (10, 15, 25),
        "robe_mid": (25, 32, 48),
        "robe_light": (45, 58, 78),
        "robe_edge": (75, 90, 115),
        "robe_shine": (110, 130, 160),
        # Armor plates (dark tarnished metal)
        "armor_darkest": (8, 10, 14),
        "armor_dark": (28, 32, 40),
        "armor_mid": (60, 68, 80),
        "armor_light": (110, 120, 140),
        "armor_shine": (170, 180, 200),
        # Skull/bone (aged, grim)
        "bone_darkest": (25, 22, 15),
        "bone_dark": (70, 62, 48),
        "bone_mid": (140, 128, 100),
        "bone_light": (210, 195, 165),
        "bone_shine": (245, 235, 210),
        # SOUL CYAN (magic, glow, eyes) - signature color
        "soul_darkest": (5, 25, 30),
        "soul_dark": (15, 70, 85),
        "soul_mid": (40, 160, 180),
        "soul_light": (100, 230, 245),
        "soul_hot": (180, 250, 255),
        "soul_shine": (230, 255, 255),
        # Chain (rusted iron dangling)
        "chain_dark": (18, 18, 22),
        "chain_mid": (55, 55, 65),
        "chain_light": (100, 100, 115),
        # Wisp / ghost / spirit (translucent)
        "wisp_dark": (10, 40, 55),
        "wisp_mid": (50, 140, 170),
        "wisp_light": (140, 220, 240),
        # Death purple accent
        "death_dark": (20, 8, 30),
        "death_mid": (60, 30, 90),
        "death_light": (130, 90, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xarnathul._clamp(color)
        if _NS_xarnathul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xarnathul._clamp(color)
        if _NS_xarnathul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xarnathul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xarnathul(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_xarnathul._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xar_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (soul aura, ground rune).
        _NS_xarnathul._draw_soul_aura(surface, x, y, pulse)
        _NS_xarnathul._draw_ground_rune(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_xarnathul._draw_defile_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xarnathul._draw_wallofpain_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xarnathul._draw_requiem_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating - has hover bob).
        if attacking:
            _NS_xarnathul._draw_xar_attack(surface, boss, x, y)
        else:
            # No walk animation - lich floats.
            _NS_xarnathul._draw_xar_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_xarnathul._draw_laywaste_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xarnathul._draw_wallofpain_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xarnathul._draw_requiem_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xar_previous_timer", 0))
        active = bool(getattr(boss, "_xar_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._xar_attack_active = True
            boss._xar_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xar_attack_frame = int(getattr(boss, "_xar_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._xar_attack_active = False
            boss._xar_attack_frame = 0
            active = False
        boss._xar_previous_timer = timer
        boss._xar_attack_progress = (
            min(1.0, getattr(boss, "_xar_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_xar_float(surface, boss, x, y):
        """Idle & moving: always floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_xarnathul._draw_shadow(surface, x, y + 52)
        _NS_xarnathul._draw_soul_wisps(surface, x, y + 20, boss.pulse)
        _NS_xarnathul._draw_xar_body(surface, x, y - 6 + hover,
                                     boss.direction, boss.pulse, "float", 0)
    def _draw_xar_attack(surface, boss, x, y):
        """Attack: raise staff/arms, cast forward (range spell)."""
        progress = getattr(boss, "_xar_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up (raise arm) → cast forward → recover.
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        lift = 0
        if progress < 0.4:
            t = progress / 0.4
            lift = int(t * 3)
        elif progress < 0.7:
            t = (progress - 0.4) / 0.3
            lift = int(3 - t * 2)
        else:
            t = (progress - 0.7) / 0.3
            lift = int(1 - t)
        _NS_xarnathul._draw_shadow(surface, x, y + 52)
        _NS_xarnathul._draw_soul_wisps(surface, x, y + 20, boss.pulse, intense=True)
        _NS_xarnathul._draw_xar_body(surface, x, y - 6 + hover - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        _NS_xarnathul._draw_laywaste_projectile(surface, boss, x, y - 6 + hover - lift,
                                                progress)
    # ============================================================
    # BODY (Floating lich: robe, arms, staff, skull head, chains)
    # ============================================================
    def _draw_xar_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw lich body: cape/robe flowing, floating pose."""
        # Chains dangling below (behind robe).
        _NS_xarnathul._draw_hanging_chains(surface, cx, cy + 20, phase)
        # Trailing robe below (ethereal wisp legs).
        _NS_xarnathul._draw_robe_trail(surface, cx, cy + 14, facing, phase)
        # Main robe body.
        _NS_xarnathul._draw_robe_body(surface, cx, cy, facing, phase)
        # Shoulder pads / armor.
        _NS_xarnathul._draw_shoulder_armor(surface, cx, cy - 6, facing, phase)
        # Arms & staff.
        _NS_xarnathul._draw_lich_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Hood & skull head.
        _NS_xarnathul._draw_hooded_skull(surface, cx, cy - 20, facing, phase)
    def _draw_robe_trail(surface, cx, cy, facing, phase):
        """Ethereal trailing robe bottom (like ghost tail)."""
        # Wispy trail replacing legs.
        for i in range(5):
            t = i / 4
            wave = math.sin(phase * 1.0 + i * 0.5) * (3 + i)
            trail_x = cx + int(wave)
            trail_y = cy + int(i * 6)
            width = int(18 - i * 2)
            alpha = 220 - i * 35
            trail_surf = pygame.Surface((width * 2 + 4, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(trail_surf, (*_NS_xarnathul.PALETTE["robe_darkest"], alpha),
                                (0, 0, width * 2, 8))
            pygame.draw.ellipse(trail_surf, (*_NS_xarnathul.PALETTE["robe_dark"], alpha),
                                (2, 1, width * 2 - 4, 6))
            pygame.draw.ellipse(trail_surf, (*_NS_xarnathul.PALETTE["robe_mid"], alpha - 30),
                                (4, 2, width * 2 - 8, 4))
            # Cyan tint along edge.
            pygame.draw.ellipse(trail_surf, (*_NS_xarnathul.PALETTE["soul_dark"], alpha - 60),
                                (6, 3, width * 2 - 12, 2))
            surface.blit(trail_surf, (trail_x - width, trail_y))
        # Wisp tendrils.
        for i in range(6):
            wisp_t = (phase * 0.5 + i * 0.16) % 1.0
            wx = cx + int(math.sin(phase + i) * 12)
            wy = cy + 4 + int(wisp_t * 24)
            alpha = _NS_xarnathul._alpha(180 * (1 - wisp_t))
            if alpha > 0:
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                 (wx, wy, 1, 1))
    def _draw_robe_body(surface, cx, cy, facing, phase):
        """Main robe silhouette (upper body torso)."""
        sway = math.sin(phase * 0.7) * 1
        # Main robe shape (trapezoid, wider at bottom).
        robe_shape = [
            (cx - 10, cy - 12),
            (cx - 12, cy - 6),
            (cx - 14, cy),
            (cx - 16, cy + 8),
            (cx - 18, cy + 16),
            (cx + 18, cy + 16),
            (cx + 16, cy + 8),
            (cx + 14, cy),
            (cx + 12, cy - 6),
            (cx + 10, cy - 12),
        ]
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in robe_shape])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["robe_darkest"], robe_shape)
        # Inner robe (mid-tone).
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["robe_dark"], [
            (cx - 9, cy - 11),
            (cx - 12, cy),
            (cx - 15, cy + 14),
            (cx + 15, cy + 14),
            (cx + 12, cy),
            (cx + 9, cy - 11),
        ])
        # Inner shade (chest).
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["robe_mid"], [
            (cx - 6, cy - 8),
            (cx - 8, cy - 2),
            (cx - 10, cy + 8),
            (cx + 10, cy + 8),
            (cx + 8, cy - 2),
            (cx + 6, cy - 8),
        ])
        # Central glow (soul core in chest).
        core_y = cy - 2
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(8, 0, -1):
            alpha = _NS_xarnathul._alpha(180 * (8 - r) / 8 * pulse)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                    (cx, core_y), r)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_mid"], (cx, core_y), 3)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_light"], (cx, core_y), 2)
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"], (cx, core_y, 1, 1))
        # Cloth folds (vertical lines).
        for x_off in (-8, -4, 4, 8):
            pygame.draw.line(surface, _NS_xarnathul.PALETTE["robe_darkest"],
                             (cx + x_off, cy - 6),
                             (cx + x_off + int(sway), cy + 14), 1)
        # Robe edge highlights.
        pygame.draw.line(surface, _NS_xarnathul.PALETTE["robe_edge"],
                         (cx - 10, cy - 10), (cx - 16, cy + 14), 1)
        pygame.draw.line(surface, _NS_xarnathul.PALETTE["robe_light"],
                         (cx + 10, cy - 10), (cx + 16, cy + 14), 1)
        # Belt / sash across waist.
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["armor_darkest"],
                         (cx - 12, cy + 4, 24, 3))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["armor_dark"],
                         (cx - 11, cy + 4, 22, 2))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["armor_mid"],
                         (cx - 10, cy + 5, 20, 1))
        # Belt buckle (skull).
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["bone_dark"], (cx - 2, cy + 3, 4, 5))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["bone_mid"], (cx - 1, cy + 4, 2, 3))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_light"], (cx - 1, cy + 4, 1, 1))
    def _draw_shoulder_armor(surface, cx, cy, facing, phase):
        """Sharp shoulder pauldrons with spikes."""
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 11
            # Pauldron plate (angular).
            pad_shape = [
                (base_x, cy - 4),
                (base_x + side * 6, cy - 6),
                (base_x + side * 8, cy - 2),
                (base_x + side * 7, cy + 3),
                (base_x + side * 2, cy + 4),
            ]
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in pad_shape])
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["armor_darkest"], pad_shape)
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["armor_dark"], [
                (base_x + side * 1, cy - 3),
                (base_x + side * 5, cy - 5),
                (base_x + side * 7, cy - 1),
                (base_x + side * 6, cy + 2),
                (base_x + side * 2, cy + 3),
            ])
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["armor_mid"], [
                (base_x + side * 2, cy - 2),
                (base_x + side * 4, cy - 4),
                (base_x + side * 5, cy),
                (base_x + side * 3, cy + 1),
            ])
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["armor_light"],
                             (base_x + side * 3, cy - 2, 1, 1))
            # Spike on top of pauldron.
            spike_tip_x = base_x + side * 4
            spike_tip_y = cy - 9
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["shadow_deep"], [
                (spike_tip_x + 1, spike_tip_y + 1),
                (base_x + side * 2 + 1, cy - 5 + 1),
                (base_x + side * 6 + 1, cy - 5 + 1),
            ])
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_dark"], [
                (spike_tip_x, spike_tip_y),
                (base_x + side * 2, cy - 5),
                (base_x + side * 6, cy - 5),
            ])
            _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_mid"], [
                (spike_tip_x, spike_tip_y),
                (base_x + side * 3, cy - 5),
                (base_x + side * 5, cy - 5),
            ])
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["bone_light"],
                             (spike_tip_x, spike_tip_y, 1, 1))
    def _draw_lich_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms: one holds staff, other free (or raised in cast)."""
        # LEFT arm (holding staff on facing side).
        staff_side = facing
        arm_sway = math.sin(phase * 0.5) * 1
        # Staff arm base.
        arm_base_x = cx + staff_side * 12
        arm_base_y = cy - 3
        # Arm raise during attack.
        raise_amount = 0
        if action == "attack":
            if attack_progress < 0.4:
                raise_amount = int(attack_progress / 0.4 * 8)
            elif attack_progress < 0.7:
                raise_amount = int(8 - (attack_progress - 0.4) / 0.3 * 12)
            else:
                raise_amount = int(-4 + (attack_progress - 0.7) / 0.3 * 4)
        # Staff hand position.
        hand_x = arm_base_x + staff_side * 4
        hand_y = arm_base_y + 6 - raise_amount
        elbow_x = arm_base_x + staff_side * 2
        elbow_y = arm_base_y + 2 - raise_amount // 2
        # Draw arm (robed sleeve).
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                              (arm_base_x + 1, arm_base_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_darkest"],
                              (arm_base_x, arm_base_y), (elbow_x, elbow_y), 4)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_dark"],
                              (arm_base_x, arm_base_y), (elbow_x, elbow_y), 3)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_mid"],
                              (arm_base_x, arm_base_y - 1), (elbow_x, elbow_y - 1), 1)
        # Forearm.
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        # Bony hand.
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["bone_dark"], (hand_x, hand_y), 2)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["bone_mid"], (hand_x, hand_y), 1)
        # STAFF.
        _NS_xarnathul._draw_staff(surface, hand_x, hand_y, staff_side, phase, action, attack_progress)
        # RIGHT arm (opposite - shorter, held in front or raised in attack).
        other_side = -staff_side
        other_base_x = cx + other_side * 10
        other_base_y = cy - 2
        # In attack, raise this hand and glow soul energy.
        cast_raise = 0
        if action == "attack":
            if attack_progress < 0.4:
                cast_raise = int(attack_progress / 0.4 * 6)
            elif attack_progress < 0.7:
                cast_raise = int(6 - (attack_progress - 0.4) / 0.3 * 8)
        other_hand_x = other_base_x + other_side * 6
        other_hand_y = other_base_y + 4 - cast_raise
        other_elbow_x = other_base_x + other_side * 3
        other_elbow_y = other_base_y + 1 - cast_raise // 2
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                              (other_base_x + 1, other_base_y + 1),
                              (other_elbow_x + 1, other_elbow_y + 1), 4)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_darkest"],
                              (other_base_x, other_base_y), (other_elbow_x, other_elbow_y), 3)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_dark"],
                              (other_base_x, other_base_y), (other_elbow_x, other_elbow_y), 2)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_darkest"],
                              (other_elbow_x, other_elbow_y), (other_hand_x, other_hand_y), 3)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["robe_dark"],
                              (other_elbow_x, other_elbow_y), (other_hand_x, other_hand_y), 2)
        # Bony free hand.
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["bone_dark"],
                                (other_hand_x, other_hand_y), 2)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["bone_mid"],
                                (other_hand_x, other_hand_y), 1)
        # Soul flame in free hand (always glowing).
        flame_intensity = 1.5 if action == "attack" else 1.0
        pulse_flame = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_xarnathul._alpha(160 * (6 - r) / 6 * pulse_flame * flame_intensity)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                    (other_hand_x, other_hand_y - 2), r)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_mid"],
                                (other_hand_x, other_hand_y - 2), 2)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_light"],
                                (other_hand_x, other_hand_y - 3), 1)
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"],
                         (other_hand_x, other_hand_y - 3, 1, 1))
    def _draw_staff(surface, hand_x, hand_y, side, phase, action, attack_progress):
        """Long staff with skull top glowing cyan."""
        # Staff extends up and slightly outward.
        staff_top_x = hand_x + side * 2
        staff_top_y = hand_y - 26
        staff_bot_x = hand_x - side * 1
        staff_bot_y = hand_y + 8
        # Shadow.
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                              (staff_top_x + 2, staff_top_y + 2),
                              (staff_bot_x + 2, staff_bot_y + 2), 3)
        # Staff shaft.
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["bone_darkest"],
                              (staff_top_x, staff_top_y), (staff_bot_x, staff_bot_y), 3)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["bone_dark"],
                              (staff_top_x, staff_top_y), (staff_bot_x, staff_bot_y), 2)
        _NS_xarnathul._aaline(surface, _NS_xarnathul.PALETTE["bone_mid"],
                              (staff_top_x - side, staff_top_y),
                              (staff_bot_x - side, staff_bot_y), 1)
        # Wrap details (chain around staff).
        for wy in range(staff_top_y + 8, staff_bot_y - 2, 6):
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["chain_dark"],
                             (staff_top_x - 2, wy, 4, 1))
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["chain_mid"],
                             (staff_top_x - 1, wy, 2, 1))
        # SKULL top with cyan glow.
        skull_x = staff_top_x
        skull_y = staff_top_y - 4
        # Cyan halo behind skull.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        glow_intensity = 1.5 if action == "attack" else 1.0
        for r in range(12, 0, -1):
            alpha = _NS_xarnathul._alpha(140 * (12 - r) / 12 * pulse * glow_intensity)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                    (skull_x, skull_y), r)
        # Skull shape.
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["shadow_deep"], [
            (skull_x - 3 + 1, skull_y - 3 + 1),
            (skull_x + 3 + 1, skull_y - 3 + 1),
            (skull_x + 4 + 1, skull_y + 1),
            (skull_x + 2 + 1, skull_y + 4 + 1),
            (skull_x - 2 + 1, skull_y + 4 + 1),
            (skull_x - 4 + 1, skull_y + 1),
        ])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_darkest"], [
            (skull_x - 3, skull_y - 3),
            (skull_x + 3, skull_y - 3),
            (skull_x + 4, skull_y),
            (skull_x + 2, skull_y + 4),
            (skull_x - 2, skull_y + 4),
            (skull_x - 4, skull_y),
        ])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_dark"], [
            (skull_x - 3, skull_y - 2),
            (skull_x + 3, skull_y - 2),
            (skull_x + 3, skull_y + 1),
            (skull_x + 1, skull_y + 3),
            (skull_x - 1, skull_y + 3),
            (skull_x - 3, skull_y + 1),
        ])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_mid"], [
            (skull_x - 2, skull_y - 1),
            (skull_x + 2, skull_y - 1),
            (skull_x + 2, skull_y + 1),
            (skull_x, skull_y + 2),
            (skull_x - 2, skull_y + 1),
        ])
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["bone_light"],
                         (skull_x - 1, skull_y - 2, 3, 1))
        # Skull eye sockets (glowing cyan).
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                         (skull_x - 2, skull_y, 1, 2))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                         (skull_x + 1, skull_y, 1, 2))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_light"],
                         (skull_x - 2, skull_y, 1, 1))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_light"],
                         (skull_x + 1, skull_y, 1, 1))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"],
                         (skull_x - 2, skull_y, 1, 1))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"],
                         (skull_x + 1, skull_y, 1, 1))
        # Jaw line.
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                         (skull_x - 1, skull_y + 3, 3, 1))
        # Cyan flame rising from skull.
        for i in range(3):
            fx = skull_x + int(math.sin(phase * 3 + i) * 2)
            fy = skull_y - 5 - i * 2
            alpha = _NS_xarnathul._alpha(200 - i * 40)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                    (fx, fy), 2)
            pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                             (fx, fy, 1, 1))
    def _draw_hooded_skull(surface, cx, cy, facing, phase):
        """Skull face inside a dark hood."""
        # Hood outer shape.
        hood_shape = [
            (cx - 10, cy - 2),
            (cx - 12, cy + 4),
            (cx - 11, cy + 10),
            (cx - 6, cy + 12),
            (cx + 6, cy + 12),
            (cx + 11, cy + 10),
            (cx + 12, cy + 4),
            (cx + 10, cy - 2),
            (cx + 6, cy - 6),
            (cx - 6, cy - 6),
        ]
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in hood_shape])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["robe_darkest"], hood_shape)
        # Inner hood shadow.
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["shadow_deep"], [
            (cx - 8, cy),
            (cx - 9, cy + 6),
            (cx - 5, cy + 10),
            (cx + 5, cy + 10),
            (cx + 9, cy + 6),
            (cx + 8, cy),
        ])
        # Hood highlight (edge).
        pygame.draw.line(surface, _NS_xarnathul.PALETTE["robe_dark"],
                         (cx - 10, cy - 2), (cx - 12, cy + 4), 1)
        pygame.draw.line(surface, _NS_xarnathul.PALETTE["robe_mid"],
                         (cx - 6, cy - 6), (cx + 6, cy - 6), 1)
        pygame.draw.line(surface, _NS_xarnathul.PALETTE["robe_edge"],
                         (cx + 6, cy - 6), (cx + 10, cy - 2), 1)
        # SKULL FACE inside hood (partially visible).
        skull_y = cy + 4
        # Skull main shape.
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_darkest"], [
            (cx - 5, skull_y - 3),
            (cx + 5, skull_y - 3),
            (cx + 6, skull_y),
            (cx + 4, skull_y + 5),
            (cx - 4, skull_y + 5),
            (cx - 6, skull_y),
        ])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_dark"], [
            (cx - 4, skull_y - 2),
            (cx + 4, skull_y - 2),
            (cx + 5, skull_y),
            (cx + 3, skull_y + 4),
            (cx - 3, skull_y + 4),
            (cx - 5, skull_y),
        ])
        _NS_xarnathul._poly(surface, _NS_xarnathul.PALETTE["bone_mid"], [
            (cx - 3, skull_y - 1),
            (cx + 3, skull_y - 1),
            (cx + 3, skull_y + 1),
            (cx + 2, skull_y + 3),
            (cx - 2, skull_y + 3),
            (cx - 3, skull_y + 1),
        ])
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["bone_light"],
                         (cx - 1, skull_y - 1, 3, 1))
        # GLOWING CYAN EYE SOCKETS.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Eye holes.
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                         (cx - 3, skull_y, 2, 2))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                         (cx + 1, skull_y, 2, 2))
        # Glow behind eyes.
        for r in range(4, 0, -1):
            alpha = _NS_xarnathul._alpha(160 * (4 - r) / 4 * pulse)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                    (cx - 2, skull_y), r)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                    (cx + 2, skull_y), r)
        # Bright core eyes.
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_light"],
                         (cx - 3, skull_y, 2, 2))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_light"],
                         (cx + 1, skull_y, 2, 2))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"],
                         (cx - 2, skull_y, 1, 1))
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"],
                         (cx + 2, skull_y, 1, 1))
        # Cyan wisps rising from eyes.
        for i, ex in enumerate((cx - 2, cx + 2)):
            for k in range(3):
                wisp_t = (phase * 1.5 + i * 0.3 + k * 0.25) % 1.0
                wy = skull_y - int(wisp_t * 6)
                wx = ex + int(math.sin(phase * 2 + i + k) * 1)
                alpha = _NS_xarnathul._alpha(180 * (1 - wisp_t))
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_shine"], alpha),
                                 (wx, wy, 1, 1))
        # Nose hole.
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                         (cx, skull_y + 2, 1, 1))
        # Teeth (grim smile).
        for tx in range(cx - 2, cx + 3):
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                             (tx, skull_y + 4, 1, 1))
            if tx % 2 == 0:
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["bone_mid"],
                                 (tx, skull_y + 4, 1, 1))
    def _draw_hanging_chains(surface, cx, cy, phase):
        """Rusted chains dangling from robe."""
        for i, x_off in enumerate((-10, -4, 4, 10)):
            sway = math.sin(phase * 0.8 + i * 0.5) * 2
            chain_x = cx + x_off + int(sway)
            for link_i in range(4):
                link_y = cy + link_i * 4
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["shadow_deep"],
                                 (chain_x - 1 + 1, link_y + 1, 3, 3))
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["chain_dark"],
                                 (chain_x - 1, link_y, 3, 3))
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["chain_mid"],
                                 (chain_x - 1, link_y, 3, 1))
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["chain_light"],
                                 (chain_x, link_y, 1, 1))
    # ============================================================
    # RANGED ATTACK — LAY WASTE PROJECTILE (soul bolt)
    # ============================================================
    def _draw_laywaste_projectile(surface, boss, x, y, progress):
        """Cyan soul bolt fired from staff/hand."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_xarnathul._target_position(boss, x, y)
        start_x = x + facing * 18
        start_y = y - 8
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail.
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_xarnathul._alpha(230 - i * 22)
            size = max(1, 7 - i)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                    (px, py), size)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                    (px, py), max(1, size - 3))
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright bolt head (crystal-like arrow shape).
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_darkest"], (bx, by), 8)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_dark"], (bx, by), 6)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_mid"], (bx, by), 4)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_light"], (bx, by), 3)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_hot"], (bx, by), 2)
        _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_xarnathul.PALETTE["white"], (bx, by, 1, 1))
        # Crystal shard edges (radiating).
        angle_to_target = math.atan2(ty - start_y, tx - start_x)
        for i in range(4):
            spike_angle = angle_to_target + i * math.pi / 2
            ex = bx + int(math.cos(spike_angle) * 5)
            ey = by + int(math.sin(spike_angle) * 5)
            pygame.draw.line(surface, _NS_xarnathul.PALETTE["soul_light"],
                             (bx, by), (ex, ey), 1)
        # Radial glow.
        for r in range(12, 3, -2):
            alpha = _NS_xarnathul._alpha(80 * (12 - r) / 12)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                    (bx, by), r)
        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 24)
            alpha = _NS_xarnathul._alpha(240 * (1 - st))
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                    (tx, ty), max(1, radius - 4), 2)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                    (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SOUL WISPS (ambient)
    # ============================================================
    def _draw_soul_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        # Ethereal cyan cloud below.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_xarnathul._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xarnathul.PALETTE["wisp_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_xarnathul._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xarnathul.PALETTE["wisp_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising soul motes.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_xarnathul._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["wisp_dark"], alpha), (sx, sy), 3)
            _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["wisp_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Death purple accents.
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 20 + i * 10 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 20)
            alpha = _NS_xarnathul._alpha(180 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["death_dark"], alpha), (wx, wy), 2)
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["death_light"], (wx, wy, 1, 1))
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
        pygame.draw.ellipse(shadow, (3, 5, 8, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (15, 60, 70, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_soul_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_xarnathul._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_xarnathul._aacircle(aura, (*_NS_xarnathul.PALETTE["wisp_dark"], alpha), (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_xarnathul._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xarnathul._aacircle(aura, (*_NS_xarnathul.PALETTE["wisp_mid"], alpha), (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_xarnathul._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xarnathul._aacircle(aura, (*_NS_xarnathul.PALETTE["death_dark"], alpha), (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_xarnathul.PALETTE["soul_mid"] if i % 3 != 0 else _NS_xarnathul.PALETTE["death_mid"]
            hot_color = _NS_xarnathul.PALETTE["soul_hot"] if i % 3 != 0 \
                else _NS_xarnathul.PALETTE["death_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_rune(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xarnathul.PALETTE["wisp_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_xarnathul.PALETTE["soul_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_xarnathul.PALETTE["soul_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_xarnathul.PALETTE["death_dark"], 180),
                            (40, 24, 90, 14), 1)
        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_xarnathul.PALETTE["soul_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_xarnathul.PALETTE["soul_hot"], _NS_xarnathul._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL: Q - LAY WASTE (enhanced soul bolt)
    # ============================================================
    def _draw_laywaste_skill(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xarnathul._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.2:
            t = progress / 0.2
            hand_x = x + facing * 18
            hand_y = y - 8 + hover
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_xarnathul._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                        (hand_x, hand_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_xarnathul._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_mid"], (hand_x, hand_y), cr - 2)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_light"], (hand_x, hand_y),
                                    max(1, cr - 4))
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_shine"], (hand_x, hand_y),
                                    max(1, cr - 6))
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 22
            start_y = y - 8 + hover
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            for i in range(11):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xarnathul._alpha(240 - i * 22)
                size = max(1, 9 - i)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                        (px, py), size)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                        (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Bright crystal head.
            angle_to_target = math.atan2(ty - start_y, tx - start_x)
            for r in range(15, 3, -2):
                alpha = _NS_xarnathul._alpha(100 * (15 - r) / 15)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha), (bx, by), r)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_darkest"], (bx, by), 10)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_dark"], (bx, by), 8)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_mid"], (bx, by), 5)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_light"], (bx, by), 3)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["white"], (bx, by, 1, 1))
            # Crystal shard spikes.
            for i in range(4):
                spike_angle = angle_to_target + i * math.pi / 2
                ex = bx + int(math.cos(spike_angle) * 8)
                ey = by + int(math.sin(spike_angle) * 8)
                pygame.draw.line(surface, _NS_xarnathul.PALETTE["soul_light"],
                                 (bx, by), (ex, ey), 2)
                pygame.draw.line(surface, _NS_xarnathul.PALETTE["soul_shine"],
                                 (bx, by), (ex, ey), 1)
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 30)
                alpha = _NS_xarnathul._alpha(240 * (1 - st))
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                        (tx, ty), radius + 4, 3)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: W - WALL OF PAIN (row of ghost spirits)
    # ============================================================
    def _draw_wallofpain_ground(surface, boss, x, y, timer, phase):
        """Ground marker under wall of spirits."""
        tx, ty = _NS_xarnathul._target_position(boss, x, y)
        # Wall spans perpendicular to boss->target direction.
        facing = boss.direction
        wall_dir_x = 0
        wall_dir_y = 1  # vertical wall
        wall_len = 70
        # Wall center at target.
        wall_start = (tx - wall_dir_x * wall_len // 2, ty - wall_dir_y * wall_len // 2)
        wall_end = (tx + wall_dir_x * wall_len // 2, ty + wall_dir_y * wall_len // 2)
        # Ground line under wall.
        for offset in range(-2, 3):
            alpha = _NS_xarnathul._alpha(150 - abs(offset) * 30)
            pygame.draw.line(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                             (wall_start[0] + offset, wall_start[1]),
                             (wall_end[0] + offset, wall_end[1]), 1)
    def _draw_wallofpain_foreground(surface, boss, x, y, timer, phase):
        """Row of ghost spirits standing in a vertical line."""
        tx, ty = _NS_xarnathul._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Wall vertical: 5 ghost figures.
        num_ghosts = 5
        wall_len = 70
        wall_start_y = ty - wall_len // 2
        for i in range(num_ghosts):
            spawn_delay = i * 0.08
            spawn_progress = max(0.0, progress - spawn_delay)
            if spawn_progress <= 0:
                continue
            rise_t = min(1.0, spawn_progress * 5)  # rise-in animation
            gy = wall_start_y + int(i * wall_len / (num_ghosts - 1))
            gx = tx + int(math.sin(phase * 1.5 + i * 0.5) * 3)
            sway = math.sin(phase * 1.2 + i * 0.4) * 2
            # Fade in based on rise_t; fade out at end.
            fade_out = min(1.0, (1 - progress) * 4)
            alpha_base = _NS_xarnathul._alpha(220 * rise_t * fade_out)
            if alpha_base <= 0:
                continue
            # Ghost body rises from ground.
            ghost_h = int(24 * rise_t)
            ghost_y = gy - ghost_h + 10  # extend upward
            # Draw ghost silhouette (translucent).
            ghost_surf = pygame.Surface((24, ghost_h + 4), pygame.SRCALPHA)
            # Body (tapered wisp).
            body_pts = [
                (12, 0),                    # head top
                (16, 4),
                (18, 8),
                (16 + int(sway), ghost_h),  # bottom right
                (8 + int(sway), ghost_h),   # bottom left
                (6, 8),
                (8, 4),
            ]
            _NS_xarnathul._poly(ghost_surf, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha_base // 2),
                                body_pts)
            _NS_xarnathul._poly(ghost_surf, (*_NS_xarnathul.PALETTE["wisp_dark"], alpha_base),
                                body_pts)
            _NS_xarnathul._poly(ghost_surf, (*_NS_xarnathul.PALETTE["wisp_mid"], alpha_base * 3 // 4),
                                [(p[0], p[1] + 1) for p in body_pts[:-2]])
            # Bright core.
            _NS_xarnathul._aacircle(ghost_surf, (*_NS_xarnathul.PALETTE["soul_light"], alpha_base),
                                    (12, 6), 3)
            # Eye sockets.
            pygame.draw.rect(ghost_surf, (*_NS_xarnathul.PALETTE["shadow_deep"], alpha_base),
                             (9, 5, 2, 2))
            pygame.draw.rect(ghost_surf, (*_NS_xarnathul.PALETTE["shadow_deep"], alpha_base),
                             (13, 5, 2, 2))
            pygame.draw.rect(ghost_surf, (*_NS_xarnathul.PALETTE["soul_shine"], alpha_base),
                             (9, 5, 1, 1))
            pygame.draw.rect(ghost_surf, (*_NS_xarnathul.PALETTE["soul_shine"], alpha_base),
                             (14, 5, 1, 1))
            # Mouth (screaming).
            pygame.draw.ellipse(ghost_surf, (*_NS_xarnathul.PALETTE["shadow_deep"], alpha_base),
                                (10, 9, 4, 3))
            surface.blit(ghost_surf, (gx - 12, ghost_y))
            # Wisps rising above ghost head.
            for k in range(2):
                wisp_t = (phase * 1.5 + i * 0.3 + k * 0.3) % 1.0
                wy = ghost_y - int(wisp_t * 8)
                wx = gx + int(math.sin(phase * 2 + i + k) * 2)
                alpha_w = _NS_xarnathul._alpha(180 * (1 - wisp_t) * rise_t * fade_out)
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha_w),
                                 (wx, wy, 1, 1))
    # ============================================================
    # SKILL: E - DEFILE (ground DoT area)
    # ============================================================
    def _draw_defile_ground(surface, boss, x, y, timer, phase):
        """Cyan corruption rings on ground."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple concentric growing rings.
        for i in range(3):
            base_r = 25 + i * 12
            r = int(base_r + math.sin(phase * 2 + i) * 3)
            alpha = _NS_xarnathul._alpha(200 - i * 50)
            pygame.draw.ellipse(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                (x - r + 2, y + 40 - r // 3 + 1, r * 2 - 4, r * 2 // 3 - 2), 2)
            pygame.draw.ellipse(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                (x - r + 4, y + 40 - r // 3 + 2, r * 2 - 8, r * 2 // 3 - 4), 1)
        # Rune symbols on outer ring.
        outer_r = 45
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            rx = x + int(math.cos(angle) * outer_r)
            ry = y + 40 + int(math.sin(angle) * outer_r * 0.4)
            # Rune "X" or small cross.
            pygame.draw.line(surface, _NS_xarnathul.PALETTE["soul_light"],
                             (rx - 2, ry - 1), (rx + 2, ry + 1), 1)
            pygame.draw.line(surface, _NS_xarnathul.PALETTE["soul_light"],
                             (rx - 2, ry + 1), (rx + 2, ry - 1), 1)
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"], (rx, ry, 1, 1))
        # Wisps rising from ground.
        for i in range(10):
            wisp_t = (phase * 0.6 + i * 0.15) % 1.0
            angle = i * math.pi / 5
            sr = 20 + int((i % 3) * 8)
            wx = x + int(math.cos(angle) * sr)
            wy_base = y + 40 + int(math.sin(angle) * sr * 0.4)
            wy = wy_base - int(wisp_t * 20)
            alpha = _NS_xarnathul._alpha(200 * (1 - wisp_t))
            if alpha > 0:
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["wisp_dark"], alpha), (wx, wy), 2)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["wisp_mid"], alpha), (wx, wy - 1), 1)
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                 (wx, wy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                                 (wx, wy - 2, 1, 1))
    # ============================================================
    # SKILL: R - REQUIEM (global soul beams from sky)
    # ============================================================
    def _draw_requiem_ground(surface, boss, x, y, timer, phase):
        """Massive rune circle around boss during requiem cast."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Grand ritual circle.
        for i in range(4):
            base_r = 40 + i * 10
            r = int(base_r + math.sin(phase * 2 + i) * 3)
            alpha = _NS_xarnathul._alpha(230 - i * 40)
            pygame.draw.ellipse(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                (x - r + 2, y + 40 - r // 3 + 1, r * 2 - 4, r * 2 // 3 - 2), 1)
        # Ritual runes radiating outward.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            r1 = 50
            r2 = 75
            x1 = x + int(math.cos(angle) * r1)
            y1 = y + 40 + int(math.sin(angle) * r1 * 0.4)
            x2 = x + int(math.cos(angle) * r2)
            y2 = y + 40 + int(math.sin(angle) * r2 * 0.4)
            pygame.draw.line(surface, _NS_xarnathul.PALETTE["soul_light"], (x1, y1), (x2, y2), 2)
            pygame.draw.rect(surface, _NS_xarnathul.PALETTE["soul_shine"], (x2, y2, 2, 2))
    def _draw_requiem_foreground(surface, boss, x, y, timer, phase):
        """Massive soul beams raining down globally + upward blast at boss."""
        tx, ty = _NS_xarnathul._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.35:
            # Wind-up: boss glowing brighter, raising energy.
            t = progress / 0.35
            core_x = x
            core_y = y - 10 + hover
            # Growing corona.
            for r in range(int(20 + t * 15), 0, -2):
                alpha = _NS_xarnathul._alpha(150 * t * (30 - r) / 30)
                if alpha > 0:
                    _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                            (core_x, core_y), r)
            # Bright core.
            core_r = int(6 + t * 8)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_darkest"], (core_x, core_y), core_r)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_mid"], (core_x, core_y), core_r - 2)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_light"], (core_x, core_y), core_r - 4)
            _NS_xarnathul._aacircle(surface, _NS_xarnathul.PALETTE["soul_shine"], (core_x, core_y), max(1, core_r - 6))
            # Energy streams pulled inward.
            for i in range(12):
                stream_angle = phase * 2 + i * math.pi / 6
                stream_r = int(60 * (1 - t))
                sx = core_x + int(math.cos(stream_angle) * stream_r)
                sy = core_y + int(math.sin(stream_angle) * stream_r)
                alpha = _NS_xarnathul._alpha(200 * t)
                pygame.draw.line(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                 (sx, sy), (core_x, core_y), 1)
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_hot"], alpha),
                                 (sx, sy, 2, 2))
        elif progress < 0.75:
            # STRIKE: multiple soul beams raining down.
            t = (progress - 0.35) / 0.4
            intensity = math.sin(t * math.pi)
            # Central beam from boss upward (soul cannon).
            core_x = x
            core_y = y - 10 + hover
            beam_top_y = 0
            for layer_i, (width, alpha_val) in enumerate([
                (14, 100), (10, 140), (6, 180), (3, 220), (1, 255),
            ]):
                actual_alpha = _NS_xarnathul._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_xarnathul.PALETTE["soul_darkest"],
                    _NS_xarnathul.PALETTE["soul_dark"],
                    _NS_xarnathul.PALETTE["soul_mid"],
                    _NS_xarnathul.PALETTE["soul_light"],
                    _NS_xarnathul.PALETTE["soul_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (core_x - width // 2, beam_top_y,
                                  width, core_y - beam_top_y))
            # Multiple raining beams around target area (global damage).
            num_beams = 6
            for i in range(num_beams):
                beam_delay = i * 0.05
                beam_progress = max(0.0, t - beam_delay)
                if beam_progress <= 0:
                    continue
                beam_intensity = math.sin(min(1.0, beam_progress * 3) * math.pi)
                # Randomize positions around target area.
                bx_offset = int(math.sin(i * 1.7 + progress * 2) * 80)
                by_offset = int(math.cos(i * 2.3 + progress * 1.5) * 20)
                beam_x = tx + bx_offset
                beam_y = ty + by_offset
                # Beam from top.
                for layer_i, (width, alpha_val) in enumerate([
                    (10, 80), (6, 130), (3, 180), (1, 240),
                ]):
                    actual_alpha = _NS_xarnathul._alpha(alpha_val * beam_intensity)
                    if actual_alpha <= 0:
                        continue
                    colors = [
                        _NS_xarnathul.PALETTE["soul_dark"],
                        _NS_xarnathul.PALETTE["soul_mid"],
                        _NS_xarnathul.PALETTE["soul_light"],
                        _NS_xarnathul.PALETTE["soul_shine"],
                    ]
                    color = colors[min(layer_i, 3)]
                    pygame.draw.rect(surface, (*color, actual_alpha),
                                     (beam_x - width // 2, 0,
                                      width, beam_y))
                # Impact at beam ground.
                impact_r = int(6 + beam_progress * 15)
                impact_alpha = _NS_xarnathul._alpha(240 * beam_intensity)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_darkest"], impact_alpha),
                                        (beam_x, beam_y), impact_r + 2, 2)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], impact_alpha),
                                        (beam_x, beam_y), impact_r, 2)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_light"], impact_alpha),
                                        (beam_x, beam_y), max(1, impact_r - 4), 1)
                _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_shine"], impact_alpha),
                                        (beam_x, beam_y), max(1, impact_r // 3))
                # Skull symbol at impact.
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["shadow_deep"], impact_alpha),
                                 (beam_x - 1, beam_y - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["shadow_deep"], impact_alpha),
                                 (beam_x + 1, beam_y - 1, 1, 1))
        else:
            # Aftermath: dissipating wisps.
            t = (progress - 0.75) / 0.25
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                bx_off = int(math.sin(i * 1.7) * 100)
                by_off = int(math.cos(i * 2.3) * 30)
                rx = tx + bx_off + int(math.sin(phase + i) * 10)
                ry = ty + by_off - int(rise_t * 30)
                alpha = _NS_xarnathul._alpha(180 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_dark"], alpha),
                                            (rx, ry), 3)
                    _NS_xarnathul._aacircle(surface, (*_NS_xarnathul.PALETTE["soul_mid"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_xarnathul.PALETTE["soul_light"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# ZHYRAKAAN (PHANTOMWEAVE LANCER) - Mini Boss
# ====================================================================

class _NS_zhyrakaan:
    """Namespace zhyrakaan - phantom lancer mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Pale blue skin
        "skin_darkest": (15, 25, 45),
        "skin_dark": (45, 75, 110),
        "skin_mid": (95, 135, 175),
        "skin_light": (155, 195, 225),
        "skin_shine": (215, 240, 255),
        # White hair/beard
        "hair_darkest": (55, 65, 80),
        "hair_dark": (120, 130, 150),
        "hair_mid": (190, 200, 220),
        "hair_light": (235, 245, 255),
        "hair_shine": (255, 255, 255),
        # Dark blue armor/cloth
        "armor_darkest": (8, 15, 30),
        "armor_dark": (25, 40, 65),
        "armor_mid": (55, 85, 125),
        "armor_light": (110, 150, 195),
        "armor_shine": (185, 215, 245),
        # Gold trim/armor
        "gold_darkest": (55, 35, 8),
        "gold_dark": (110, 75, 20),
        "gold_mid": (200, 155, 45),
        "gold_light": (250, 220, 105),
        "gold_shine": (255, 245, 190),
        # Cape red (crimson)
        "cape_dark": (75, 15, 20),
        "cape_mid": (170, 35, 40),
        "cape_light": (225, 80, 70),
        # Blue crystal glow (lance tip, phantom)
        "crystal_darkest": (10, 30, 65),
        "crystal_dark": (25, 90, 165),
        "crystal_mid": (75, 175, 235),
        "crystal_light": (170, 230, 255),
        "crystal_hot": (220, 250, 255),
        "crystal_shine": (245, 255, 255),
        # Steel lance
        "steel_dark": (35, 45, 65),
        "steel_mid": (110, 125, 155),
        "steel_light": (200, 215, 240),
        # Phantom/ghost blue (illusions)
        "phantom_darkest": (5, 25, 55),
        "phantom_dark": (20, 70, 130),
        "phantom_mid": (60, 145, 210),
        "phantom_light": (140, 210, 250),
        # Glowing blue eyes
        "eye_socket": (5, 10, 20),
        "eye_dark": (20, 60, 130),
        "eye_mid": (70, 165, 245),
        "eye_light": (180, 230, 255),
        "eye_glow": (240, 250, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zhyrakaan._clamp(color)
        if _NS_zhyrakaan.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zhyrakaan._clamp(color)
        if _NS_zhyrakaan.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zhyrakaan._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    def _arm_elbow(shoulder, hand, bend=4, bend_up=False):
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        if bend_up:
            if perp_y > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        else:
            if perp_y < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    def _lance_tip_position(boss, x, y):
        """Position of lance tip during attack."""
        facing = boss.direction
        active = getattr(boss, "_zh_attack_active", False)
        progress = getattr(boss, "_zh_attack_progress", 0.0)
        if active:
            if progress < 0.3:
                # Wind back.
                t = progress / 0.3
                tx = x + facing * int(28 - t * 18)
                ty = y - 10 - int(t * 4)
            elif progress < 0.5:
                # Thrust forward.
                t = (progress - 0.3) / 0.2
                tx = x + facing * int(10 + t * 42)
                ty = y - 14 + int(t * 8)
            elif progress < 0.75:
                # Hold thrust.
                tx = x + facing * 52
                ty = y - 6
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                tx = x + facing * int(52 - t * 24)
                ty = y - 6 - int(t * 4)
        else:
            tx = x + facing * 30
            ty = y - 12
        return tx, ty
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zhyrakaan(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_zhyrakaan._update_attack_anim(boss)
        attack_progress = getattr(boss, "_zh_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_zh_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )
        # Ambient FX.
        _NS_zhyrakaan._draw_crystal_aura(surface, x, y, pulse)
        _NS_zhyrakaan._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_zhyrakaan._draw_juxtapose_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zhyrakaan._draw_doppelganger_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body.
        float_bob = math.sin(pulse * 0.7) * 5
        body_y = y + int(float_bob)
        # BACKGROUND phantom illusions (for W & R skills - drawn BEHIND main body).
        if active_skill == "w":
            _NS_zhyrakaan._draw_juxtapose_phantoms_back(surface, boss, x, body_y,
                                                         skill_timer, pulse)
        elif active_skill == "r":
            _NS_zhyrakaan._draw_doppelganger_phantoms_back(surface, boss, x, body_y,
                                                             skill_timer, pulse)
        # Main body pose.
        if active_skill == "q":
            _NS_zhyrakaan._draw_body_qthrow(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif active_skill == "e":
            _NS_zhyrakaan._draw_body_flurry(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif attacking:
            _NS_zhyrakaan._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_zhyrakaan._draw_body_idle(surface, boss, x, body_y)
        # FOREGROUND phantoms (in front of body for depth).
        if active_skill == "w":
            _NS_zhyrakaan._draw_juxtapose_phantoms_front(surface, boss, x, body_y,
                                                          skill_timer, pulse)
        elif active_skill == "r":
            _NS_zhyrakaan._draw_doppelganger_phantoms_front(surface, boss, x, body_y,
                                                              skill_timer, pulse)
        # Foreground effects.
        if active_skill == "q":
            _NS_zhyrakaan._draw_spirit_lance_projectile(surface, boss, x, body_y,
                                                         skill_timer, pulse)
        elif active_skill == "e":
            _NS_zhyrakaan._draw_phantom_edge_fx(surface, boss, x, body_y,
                                                 skill_timer, pulse)
        else:
            if attacking and attack_progress > 0:
                _NS_zhyrakaan._draw_basic_thrust_fx(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_zh_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._zh_attack_active = True
            boss._zh_attack_frame = 0
            active = True
        elif active:
            boss._zh_attack_frame = int(getattr(boss, "_zh_attack_frame", 0)) + 1
            if boss._zh_attack_frame >= cooldown:
                boss._zh_attack_active = False
                boss._zh_attack_frame = 0
                active = False
        boss._zh_previous_timer = timer
        boss._zh_attack_progress = (
            min(1.0, getattr(boss, "_zh_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_zhyrakaan._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_zhyrakaan._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_zh_attack_progress", 0.0)
        _NS_zhyrakaan._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_zhyrakaan._draw_body(surface, boss, cx, cy, "thrust", progress)
    def _draw_body_qthrow(surface, boss, cx, cy, timer, phase):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zhyrakaan._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_zhyrakaan._draw_body(surface, boss, cx, cy, "throw", progress)
    def _draw_body_flurry(surface, boss, cx, cy, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zhyrakaan._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_zhyrakaan._draw_body(surface, boss, cx, cy, "flurry", progress)
    # ============================================================
    # MAIN BODY
    # ============================================================
    def _draw_body(surface, boss, cx, cy, action, progress, alpha_mult=1.0):
        """Draw full body. alpha_mult used for phantoms (translucent copies)."""
        facing = boss.direction
        phase = boss.pulse
        # Cape backdrop.
        _NS_zhyrakaan._draw_cape(surface, cx, cy, facing, phase, alpha_mult)
        # Legs.
        _NS_zhyrakaan._draw_legs(surface, cx, cy, facing, phase, alpha_mult)
        # Torso.
        _NS_zhyrakaan._draw_torso(surface, cx, cy, facing, phase, alpha_mult)
        # Hair back.
        _NS_zhyrakaan._draw_hair_back(surface, cx, cy - 22, facing, phase, alpha_mult)
        # Head.
        _NS_zhyrakaan._draw_head(surface, cx, cy - 22, facing, phase, action, alpha_mult)
        # Arms with lance.
        _NS_zhyrakaan._draw_arms(surface, cx, cy, facing, phase, action, progress, alpha_mult)
    def _draw_cape(surface, cx, cy, facing, phase, alpha_mult=1.0):
        """Red cape flowing behind."""
        sway = math.sin(phase * 0.6) * 3
        cape_pts = [
            (cx - facing * 4, cy - 16),
            (cx - facing * 12 + int(sway), cy - 6),
            (cx - facing * 16 + int(sway), cy + 8),
            (cx - facing * 14 + int(sway * 1.2), cy + 22),
            (cx - facing * 8 + int(sway), cy + 30),
            (cx + facing * 2, cy + 26),
            (cx + facing * 2, cy - 12),
        ]
        if alpha_mult < 1.0:
            # Draw with alpha for phantoms.
            surf = pygame.Surface((100, 80), pygame.SRCALPHA)
            offset_x = cx - 50
            offset_y = cy - 20
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in cape_pts]
            a = _NS_zhyrakaan._alpha(200 * alpha_mult)
            _NS_zhyrakaan._poly(surf, (*_NS_zhyrakaan.PALETTE["cape_dark"], a), local_pts)
            surface.blit(surf, (offset_x, offset_y))
        else:
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in cape_pts])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["cape_dark"], cape_pts)
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["cape_mid"], [
                (cx - facing * 3, cy - 15),
                (cx - facing * 10 + int(sway), cy - 4),
                (cx - facing * 14 + int(sway), cy + 8),
                (cx - facing * 12 + int(sway * 1.2), cy + 20),
                (cx - facing * 6 + int(sway), cy + 26),
                (cx + facing * 1, cy + 22),
                (cx + facing * 1, cy - 10),
            ])
            # Highlight edge.
            pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["cape_light"],
                             (cx - facing * 4, cy - 16),
                             (cx - facing * 12 + int(sway), cy - 6), 1)
    def _draw_legs(surface, cx, cy, facing, phase, alpha_mult=1.0):
        """Two armored legs."""
        for side in (-1, 1):
            leg_x = cx + side * 6
            # Thigh.
            thigh_pts = [
                (leg_x - 4, cy + 8),
                (leg_x + 4, cy + 8),
                (leg_x + 5, cy + 18),
                (leg_x + 3, cy + 28),
                (leg_x - 3, cy + 28),
                (leg_x - 5, cy + 18),
            ]
            if alpha_mult < 1.0:
                surf = pygame.Surface((20, 25), pygame.SRCALPHA)
                offset_x = leg_x - 10
                offset_y = cy + 7
                local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in thigh_pts]
                a = _NS_zhyrakaan._alpha(200 * alpha_mult)
                _NS_zhyrakaan._poly(surf, (*_NS_zhyrakaan.PALETTE["armor_dark"], a), local_pts)
                surface.blit(surf, (offset_x, offset_y))
                continue
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in thigh_pts])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_darkest"], thigh_pts)
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_dark"], [
                (leg_x - 3, cy + 9),
                (leg_x + 3, cy + 9),
                (leg_x + 4, cy + 18),
                (leg_x + 2, cy + 27),
                (leg_x - 2, cy + 27),
                (leg_x - 4, cy + 18),
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_mid"], [
                (leg_x - 2, cy + 10),
                (leg_x + 2, cy + 10),
                (leg_x + 3, cy + 18),
                (leg_x + 1, cy + 25),
                (leg_x - 1, cy + 25),
                (leg_x - 3, cy + 18),
            ])
            pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_light"],
                             (leg_x - 2, cy + 12), (leg_x - 2, cy + 24), 1)
            # Gold knee guard.
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_dark"],
                             (leg_x - 4, cy + 17, 8, 3))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_mid"],
                             (leg_x - 3, cy + 17, 6, 2))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                             (leg_x - 2, cy + 18, 4, 1))
            # Boot.
            boot_pts = [
                (leg_x - 5, cy + 28),
                (leg_x + 5, cy + 28),
                (leg_x + 6, cy + 32),
                (leg_x + 4, cy + 34),
                (leg_x - 4, cy + 34),
                (leg_x - 6, cy + 32),
            ]
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in boot_pts])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_darkest"], boot_pts)
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_dark"], [
                (leg_x - 4, cy + 29),
                (leg_x + 4, cy + 29),
                (leg_x + 5, cy + 31),
                (leg_x + 3, cy + 33),
                (leg_x - 3, cy + 33),
                (leg_x - 5, cy + 31),
            ])
            # Gold boot trim.
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_dark"],
                             (leg_x - 5, cy + 28, 10, 2))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_mid"],
                             (leg_x - 4, cy + 28, 8, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                             (leg_x - 3, cy + 28, 6, 1))
    def _draw_torso(surface, cx, cy, facing, phase, alpha_mult=1.0):
        """Armored torso with gold plates."""
        breath = math.sin(phase * 0.6) * 1
        torso_pts = [
            (cx - 11, cy - 14),
            (cx - 13, cy - 6),
            (cx - 11, cy + 4),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 11, cy + 4),
            (cx + 13, cy - 6),
            (cx + 11, cy - 14),
            (cx + 5, cy - 18),
            (cx - 5, cy - 18),
        ]
        if alpha_mult < 1.0:
            surf = pygame.Surface((30, 32), pygame.SRCALPHA)
            offset_x = cx - 15
            offset_y = cy - 19
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in torso_pts]
            a = _NS_zhyrakaan._alpha(200 * alpha_mult)
            _NS_zhyrakaan._poly(surf, (*_NS_zhyrakaan.PALETTE["armor_dark"], a), local_pts)
            # Add gold accent.
            a2 = _NS_zhyrakaan._alpha(180 * alpha_mult)
            pygame.draw.rect(surf, (*_NS_zhyrakaan.PALETTE["gold_dark"], a2),
                             (5, 22, 20, 4))
            surface.blit(surf, (offset_x, offset_y))
            return
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_darkest"], torso_pts)
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_dark"], [
            (cx - 10, cy - 13),
            (cx - 12, cy - 6),
            (cx - 10, cy + 3),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 10, cy + 3),
            (cx + 12, cy - 6),
            (cx + 10, cy - 13),
            (cx + 4, cy - 17),
            (cx - 4, cy - 17),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["armor_mid"], [
            (cx - 8, cy - 10),
            (cx - 10, cy - 4),
            (cx - 6, cy + 4),
            (cx + 6, cy + 4),
            (cx + 10, cy - 4),
            (cx + 8, cy - 10),
            (cx + 4, cy - 14),
            (cx - 4, cy - 14),
        ])
        # Chest highlight.
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_light"],
                         (cx - 2, cy - 12), (cx + 2, cy - 12), 1)
        # GOLD CHEST PLATE.
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_darkest"], [
            (cx - 6, cy - 12),
            (cx + 6, cy - 12),
            (cx + 8, cy - 6),
            (cx + 6, cy),
            (cx - 6, cy),
            (cx - 8, cy - 6),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_dark"], [
            (cx - 5, cy - 11),
            (cx + 5, cy - 11),
            (cx + 7, cy - 6),
            (cx + 5, cy - 1),
            (cx - 5, cy - 1),
            (cx - 7, cy - 6),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_mid"], [
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 6, cy - 6),
            (cx + 4, cy - 2),
            (cx - 4, cy - 2),
            (cx - 6, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"], (cx - 2, cy - 9, 4, 1))
        # Central blue crystal gem on chest.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_zhyrakaan._alpha(140 * (4 - r) / 4 * pulse)
            _NS_zhyrakaan._aacircle(surface,
                                    (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                    (cx, cy - 6), r)
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_darkest"], [
            (cx, cy - 8),
            (cx - 2, cy - 6),
            (cx, cy - 4),
            (cx + 2, cy - 6),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_dark"], [
            (cx, cy - 7),
            (cx - 1, cy - 6),
            (cx, cy - 5),
            (cx + 1, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_light"], (cx, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_shine"], (cx, cy - 6, 1, 1))
        # Gold belt.
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_darkest"],
                         (cx - 10, cy + 6, 20, 5))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_dark"],
                         (cx - 9, cy + 6, 18, 4))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_mid"],
                         (cx - 8, cy + 7, 16, 3))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                         (cx - 7, cy + 8, 14, 1))
        # Shoulder pauldrons with spikes.
        for side in (-1, 1):
            base_x = cx + side * 11
            paul_pts = [
                (base_x - side, cy - 16),
                (base_x + side * 4, cy - 17),
                (base_x + side * 5, cy - 10),
                (base_x + side * 2, cy - 8),
                (base_x - side, cy - 10),
            ]
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_darkest"], paul_pts)
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_dark"], [
                (base_x, cy - 16),
                (base_x + side * 3, cy - 16),
                (base_x + side * 4, cy - 10),
                (base_x + side, cy - 9),
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_mid"], [
                (base_x + side, cy - 15),
                (base_x + side * 3, cy - 14),
                (base_x + side * 3, cy - 11),
                (base_x + side, cy - 10),
            ])
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                             (base_x + side * 2, cy - 14, 1, 1))
            # Spike.
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_dark"], [
                (base_x + side * 2, cy - 17),
                (base_x + side * 4, cy - 22),
                (base_x + side * 5, cy - 15),
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_mid"], [
                (base_x + side * 3, cy - 17),
                (base_x + side * 4, cy - 21),
                (base_x + side * 4, cy - 15),
            ])
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_shine"],
                             (base_x + side * 4, cy - 21, 1, 1))
    def _draw_hair_back(surface, cx, cy, facing, phase, alpha_mult=1.0):
        """Long white hair flowing back."""
        sway = math.sin(phase * 0.5) * 2
        if alpha_mult < 1.0:
            # Simplified for phantoms.
            surf = pygame.Surface((30, 40), pygame.SRCALPHA)
            offset_x = cx - 15
            offset_y = cy - 2
            a = _NS_zhyrakaan._alpha(200 * alpha_mult)
            pygame.draw.ellipse(surf, (*_NS_zhyrakaan.PALETTE["hair_dark"], a),
                                (2, 0, 26, 30))
            surface.blit(surf, (offset_x, offset_y))
            return
        hair_pts = [
            (cx - 7, cy),
            (cx - 10 + int(sway), cy + 5),
            (cx - 11 + int(sway), cy + 15),
            (cx - 9 + int(sway * 1.2), cy + 24),
            (cx - 5 + int(sway), cy + 30),
            (cx + 5 - int(sway), cy + 30),
            (cx + 9 - int(sway * 1.2), cy + 24),
            (cx + 11 - int(sway), cy + 15),
            (cx + 10 - int(sway), cy + 5),
            (cx + 7, cy),
        ]
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in hair_pts])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["hair_darkest"], hair_pts)
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["hair_dark"], [
            (cx - 6, cy),
            (cx - 9 + int(sway), cy + 5),
            (cx - 10 + int(sway), cy + 15),
            (cx - 8 + int(sway * 1.2), cy + 22),
            (cx - 4 + int(sway), cy + 28),
            (cx + 4 - int(sway), cy + 28),
            (cx + 8 - int(sway * 1.2), cy + 22),
            (cx + 10 - int(sway), cy + 15),
            (cx + 9 - int(sway), cy + 5),
            (cx + 6, cy),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["hair_mid"], [
            (cx - 5, cy + 2),
            (cx - 7 + int(sway), cy + 7),
            (cx - 7 + int(sway), cy + 18),
            (cx - 3 + int(sway), cy + 25),
            (cx + 3 - int(sway), cy + 25),
            (cx + 7 - int(sway), cy + 18),
            (cx + 7 - int(sway), cy + 7),
            (cx + 5, cy + 2),
        ])
        # Light strands.
        for i, x_off in enumerate((-6, -2, 2, 6)):
            strand_x = cx + x_off + int(sway * 0.5)
            pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["hair_light"],
                             (strand_x, cy + 3),
                             (strand_x + int(sway), cy + 24), 1)
        # Sheen.
        for x_off in (-3, 3):
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["hair_shine"],
                             (cx + x_off + int(sway * 0.3), cy + 6, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action, alpha_mult=1.0):
        """Blue skinned head with white beard, glowing eyes, horns/crown."""
        # Face.
        face_pts = [
            (cx - 7, cy - 2),
            (cx - 8, cy + 2),
            (cx - 7, cy + 6),
            (cx - 4, cy + 10),
            (cx + 4, cy + 10),
            (cx + 7, cy + 6),
            (cx + 8, cy + 2),
            (cx + 7, cy - 2),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ]
        if alpha_mult < 1.0:
            surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            offset_x = cx - 10
            offset_y = cy - 7
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in face_pts]
            a = _NS_zhyrakaan._alpha(200 * alpha_mult)
            _NS_zhyrakaan._poly(surf, (*_NS_zhyrakaan.PALETTE["skin_dark"], a), local_pts)
            # Glowing eye hint.
            a2 = _NS_zhyrakaan._alpha(220 * alpha_mult)
            pygame.draw.rect(surf, (*_NS_zhyrakaan.PALETTE["crystal_mid"], a2), (7, 6, 6, 2))
            surface.blit(surf, (offset_x, offset_y))
            return
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["skin_darkest"], face_pts)
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["skin_dark"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 6, cy + 5),
            (cx - 3, cy + 9),
            (cx + 3, cy + 9),
            (cx + 6, cy + 5),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 5, cy + 3),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5, cy + 3),
            (cx + 4, cy),
        ])
        # Cheek highlights.
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["skin_light"], (cx - 4, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["skin_light"], (cx + 3, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["skin_shine"], (cx - 4, cy + 1, 1, 1))
        # WHITE BEARD (long).
        _NS_zhyrakaan._draw_beard(surface, cx, cy + 8, facing, phase)
        # Glowing blue eyes.
        _NS_zhyrakaan._draw_glowing_eyes(surface, cx, cy, phase, action)
        # Nose.
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["skin_darkest"], (cx, cy + 3, 1, 2))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["skin_dark"], (cx, cy + 3, 1, 1))
        # Mouth (fierce).
        if action in ("thrust", "throw", "flurry") and phase % 1 < 0.6:
            # Battle cry.
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                             (cx - 2, cy + 6, 5, 2))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["skin_darkest"],
                             (cx - 1, cy + 6, 3, 1))
        else:
            pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                             (cx - 2, cy + 7), (cx + 2, cy + 7), 1)
        # HORNS/CROWN.
        _NS_zhyrakaan._draw_horns(surface, cx, cy - 4, facing, phase)
    def _draw_beard(surface, cx, cy, facing, phase):
        """Long white beard."""
        sway = math.sin(phase * 0.5) * 1
        beard_pts = [
            (cx - 5, cy - 2),
            (cx - 6 + int(sway), cy + 2),
            (cx - 5 + int(sway), cy + 8),
            (cx - 3 + int(sway * 1.2), cy + 14),
            (cx, cy + 16),
            (cx + 3 - int(sway * 1.2), cy + 14),
            (cx + 5 - int(sway), cy + 8),
            (cx + 6 - int(sway), cy + 2),
            (cx + 5, cy - 2),
        ]
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["hair_dark"], beard_pts)
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["hair_mid"], [
            (cx - 4, cy - 1),
            (cx - 5 + int(sway), cy + 2),
            (cx - 4 + int(sway), cy + 8),
            (cx - 2 + int(sway * 1.2), cy + 13),
            (cx, cy + 15),
            (cx + 2 - int(sway * 1.2), cy + 13),
            (cx + 4 - int(sway), cy + 8),
            (cx + 5 - int(sway), cy + 2),
            (cx + 4, cy - 1),
        ])
        # Light strands.
        for x_off in (-3, 0, 3):
            pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["hair_light"],
                             (cx + x_off, cy),
                             (cx + x_off + int(sway * 0.5), cy + 12), 1)
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["hair_shine"], (cx, cy + 14, 1, 1))
    def _draw_glowing_eyes(surface, cx, cy, phase, action):
        """Bright glowing blue eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.4 if action != "idle" else 1.0
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy + 1
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            for r in range(4, 0, -1):
                alpha = _NS_zhyrakaan._alpha(130 * (4 - r) / 4 * pulse * intensity)
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["eye_glow"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_horns(surface, cx, cy, facing, phase):
        """Gold ornate horns/crown going up and back."""
        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy
            tip_x = cx + side * 9
            tip_y = cy - 8
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"], [
                (base_x + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
                (base_x + side * 2 + 1, base_y - 1 + 1),
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_dark"], [
                (base_x, base_y),
                (tip_x, tip_y),
                (base_x + side * 2, base_y - 1),
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_mid"], [
                (base_x + side, base_y),
                (tip_x, tip_y),
                (base_x + side * 2, base_y - 1),
            ])
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_shine"], (tip_x, tip_y, 1, 1))
        # Center peak (short).
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_dark"], [
            (cx - 2, cy),
            (cx, cy - 4),
            (cx + 2, cy),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["gold_mid"], [
            (cx - 1, cy - 1),
            (cx, cy - 3),
            (cx + 1, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"], (cx, cy - 3, 1, 1))
        # Blue crystal center.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_zhyrakaan._alpha(140 * (3 - r) / 3 * pulse)
            _NS_zhyrakaan._aacircle(surface,
                                    (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                    (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_shine"], (cx, cy + 1, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress, alpha_mult=1.0):
        """Two arms. Both hold lance (2-handed grip)."""
        front_sh = (cx + facing * 11, cy - 12)
        back_sh = (cx - facing * 11, cy - 12)
        # Determine hand positions based on action.
        if action == "thrust":
            # Basic thrust: both hands push lance forward.
            if progress < 0.3:
                # Wind back.
                t = progress / 0.3
                front_hand_x = cx + facing * int(16 - t * 8)
                front_hand_y = cy - 8 - int(t * 3)
                back_hand_x = cx + facing * int(2 - t * 8)
                back_hand_y = cy - 4 - int(t * 3)
            elif progress < 0.5:
                # Thrust forward.
                t = (progress - 0.3) / 0.2
                front_hand_x = cx + facing * int(8 + t * 24)
                front_hand_y = cy - 11 + int(t * 5)
                back_hand_x = cx + facing * int(-6 + t * 24)
                back_hand_y = cy - 7 + int(t * 5)
            elif progress < 0.75:
                # Hold.
                front_hand_x = cx + facing * 32
                front_hand_y = cy - 6
                back_hand_x = cx + facing * 18
                back_hand_y = cy - 2
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(32 - t * 16)
                front_hand_y = cy - 6 - int(t * 2)
                back_hand_x = cx + facing * int(18 - t * 16)
                back_hand_y = cy - 2 - int(t * 2)
        elif action == "throw":
            # Q: Prepare to throw, then release.
            if progress < 0.3:
                # Wind up.
                t = progress / 0.3
                front_hand_x = cx + facing * int(16 - t * 20)
                front_hand_y = cy - 8 - int(t * 8)
                back_hand_x = cx + facing * int(2 - t * 14)
                back_hand_y = cy - 4 - int(t * 6)
            elif progress < 0.5:
                # Throw forward.
                t = (progress - 0.3) / 0.2
                front_hand_x = cx + facing * int(-4 + t * 32)
                front_hand_y = cy - 16 + int(t * 10)
                back_hand_x = cx + facing * int(-12 + t * 20)
                back_hand_y = cy - 10 + int(t * 8)
            else:
                # Recover.
                t = (progress - 0.5) / 0.5
                front_hand_x = cx + facing * int(28 - t * 16)
                front_hand_y = cy - 6 - int(t * 2)
                back_hand_x = cx + facing * int(8 - t * 6)
                back_hand_y = cy - 2 - int(t * 2)
        elif action == "flurry":
            # E: Rapid thrusts (multiple hits).
            hit_phase = (progress * 4) % 1.0  # 4 rapid thrusts
            if hit_phase < 0.5:
                t = hit_phase / 0.5
                front_hand_x = cx + facing * int(8 + t * 22)
                front_hand_y = cy - 8
                back_hand_x = cx + facing * int(-6 + t * 22)
                back_hand_y = cy - 4
            else:
                t = (hit_phase - 0.5) / 0.5
                front_hand_x = cx + facing * int(30 - t * 22)
                front_hand_y = cy - 8
                back_hand_x = cx + facing * int(16 - t * 22)
                back_hand_y = cy - 4
        else:
            # Idle: 2-handed grip at ready.
            idle_sway = math.sin(phase * 0.8) * 1
            front_hand_x = cx + facing * 16
            front_hand_y = cy - 8 + int(idle_sway)
            back_hand_x = cx + facing * 2
            back_hand_y = cy - 4 + int(idle_sway)
        # Compute elbows.
        front_elbow = _NS_zhyrakaan._arm_elbow(front_sh, (front_hand_x, front_hand_y), bend=4)
        back_elbow = _NS_zhyrakaan._arm_elbow(back_sh, (back_hand_x, back_hand_y), bend=4)
        # Draw back arm first.
        _NS_zhyrakaan._draw_arm_segment(surface, back_sh, back_elbow,
                                          (back_hand_x, back_hand_y), alpha_mult)
        # Front arm.
        _NS_zhyrakaan._draw_arm_segment(surface, front_sh, front_elbow,
                                          (front_hand_x, front_hand_y), alpha_mult)
        # DRAW LANCE (hidden during throw's flight phase).
        lance_hidden = (action == "throw" and 0.5 < progress < 0.9)
        if not lance_hidden:
            # Lance from back hand to front hand extended forward.
            _NS_zhyrakaan._draw_lance(surface, back_hand_x, back_hand_y,
                                        front_hand_x, front_hand_y, facing, phase,
                                        action, progress, alpha_mult)
    def _draw_arm_segment(surface, shoulder, elbow, hand, alpha_mult=1.0):
        """Draw armored arm."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        if alpha_mult < 1.0:
            a = _NS_zhyrakaan._alpha(200 * alpha_mult)
            pygame.draw.line(surface, (*_NS_zhyrakaan.PALETTE["armor_dark"], a),
                             (sx, sy), (ex, ey), 4)
            pygame.draw.line(surface, (*_NS_zhyrakaan.PALETTE["armor_dark"], a),
                             (ex, ey), (hx, hy), 3)
            return
        # Upper arm.
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 5)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_darkest"],
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_dark"],
                         (sx, sy), (ex, ey), 3)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_mid"],
                         (sx, sy - 1), (ex, ey - 1), 1)
        # Forearm.
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 4)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_darkest"],
                         (ex, ey), (hx, hy), 3)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["armor_dark"],
                         (ex, ey), (hx, hy), 2)
        # Gold bracer at wrist.
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_dark"],
                         (hx - 2, hy - 2, 4, 4))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_mid"],
                         (hx - 1, hy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                         (hx - 1, hy - 1, 2, 1))
    def _draw_lance(surface, bhx, bhy, fhx, fhy, facing, phase, action,
                     progress, alpha_mult=1.0):
        """Long lance from back hand extending past front hand."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Calculate lance direction (from back hand through front hand).
        dx = fhx - bhx
        dy = fhy - bhy
        length = max(1, math.sqrt(dx * dx + dy * dy))
        dir_x = dx / length
        dir_y = dy / length
        perp_x = -dir_y
        perp_y = dir_x
        # Lance total length.
        lance_len = 42
        # Butt end (behind back hand).
        butt_x = bhx - int(dir_x * 6)
        butt_y = bhy - int(dir_y * 6)
        # Tip end (extending past front hand).
        tip_x = fhx + int(dir_x * (lance_len - int(length)))
        tip_y = fhy + int(dir_y * (lance_len - int(length)))
        if alpha_mult < 1.0:
            # Simplified for phantoms.
            a = _NS_zhyrakaan._alpha(200 * alpha_mult)
            pygame.draw.line(surface, (*_NS_zhyrakaan.PALETTE["steel_dark"], a),
                             (butt_x, butt_y), (tip_x, tip_y), 3)
            a2 = _NS_zhyrakaan._alpha(220 * alpha_mult)
            _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_mid"], a2),
                                    (tip_x, tip_y), 4)
            return
        # SHAFT (wooden/steel).
        # Shadow.
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["shadow_deep"],
                         (butt_x + 1, butt_y + 1), (tip_x + 1, tip_y + 1), 4)
        # Body.
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["steel_dark"],
                         (butt_x, butt_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["steel_mid"],
                         (butt_x, butt_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["steel_light"],
                         (butt_x, butt_y - 1), (tip_x, tip_y - 1), 1)
        # Butt cap (gold).
        _NS_zhyrakaan._aacircle(surface, _NS_zhyrakaan.PALETTE["gold_dark"], (butt_x, butt_y), 3)
        _NS_zhyrakaan._aacircle(surface, _NS_zhyrakaan.PALETTE["gold_mid"], (butt_x, butt_y), 2)
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_shine"], (butt_x, butt_y, 1, 1))
        # Middle grip decorations (gold bands).
        for i in range(2):
            band_t = 0.35 + i * 0.15
            band_x = int(butt_x + (tip_x - butt_x) * band_t)
            band_y = int(butt_y + (tip_y - butt_y) * band_t)
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_dark"],
                             (band_x - 2, band_y - 1, 4, 3))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_mid"],
                             (band_x - 1, band_y, 2, 2))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                             (band_x, band_y, 1, 1))
        # LANCE HEAD (crystal spearpoint, larger).
        # Position: at 90% of shaft.
        head_base_x = int(butt_x + (tip_x - butt_x) * 0.88)
        head_base_y = int(butt_y + (tip_y - butt_y) * 0.88)
        # Head base guard (small crossguard).
        cg_a = (head_base_x + int(perp_x * 4), head_base_y + int(perp_y * 4))
        cg_b = (head_base_x - int(perp_x * 4), head_base_y - int(perp_y * 4))
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["gold_dark"],
                         cg_a, cg_b, 3)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["gold_mid"],
                         cg_a, cg_b, 2)
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["gold_light"],
                         cg_a, cg_b, 1)
        # CRYSTAL SPEARHEAD (long diamond shape with glow).
        head_side_a = (head_base_x + int(perp_x * 3), head_base_y + int(perp_y * 3))
        head_side_b = (head_base_x - int(perp_x * 3), head_base_y - int(perp_y * 3))
        # Aura around spearhead.
        for r in range(6, 0, -1):
            alpha = _NS_zhyrakaan._alpha(80 * (6 - r) / 6 * pulse)
            _NS_zhyrakaan._aacircle(surface,
                                    (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                    (tip_x, tip_y), r)
        # Spearhead shape (diamond).
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1),
            (head_side_a[0] + 1, head_side_a[1] + 1),
            (head_base_x + 1, head_base_y + 1),
            (head_side_b[0] + 1, head_side_b[1] + 1),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_darkest"], [
            (tip_x, tip_y),
            head_side_a,
            (head_base_x, head_base_y),
            head_side_b,
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_dark"], [
            (tip_x, tip_y),
            (int((tip_x + head_side_a[0]) / 2), int((tip_y + head_side_a[1]) / 2)),
            (head_base_x, head_base_y),
            (int((tip_x + head_side_b[0]) / 2), int((tip_y + head_side_b[1]) / 2)),
        ])
        _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_mid"], [
            (tip_x, tip_y),
            (int(head_base_x + (tip_x - head_base_x) * 0.5),
             int(head_base_y + (tip_y - head_base_y) * 0.5)),
            (head_base_x, head_base_y),
        ])
        pygame.draw.line(surface, _NS_zhyrakaan.PALETTE["crystal_light"],
                         (head_base_x, head_base_y), (tip_x, tip_y), 1)
        # Bright tip.
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_shine"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Sparkles orbiting spearhead.
        for i in range(4):
            angle = phase * 3 + i * math.pi / 2
            spark_r = 6
            spx = tip_x + int(math.cos(angle) * spark_r)
            spy = tip_y + int(math.sin(angle) * spark_r)
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_shine"], (spx, spy, 1, 1))
    # ============================================================
    # PHANTOMS (illusion copies for W & R)
    # ============================================================
    def _draw_juxtapose_phantoms_back(surface, boss, cx, cy, timer, phase):
        """W: 2 phantoms behind body (side positions)."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Fade in / out.
        if progress < 0.15:
            alpha_mult = progress / 0.15
        elif progress > 0.85:
            alpha_mult = (1 - progress) / 0.15
        else:
            alpha_mult = 1.0
        alpha_mult *= 0.7  # phantoms always somewhat translucent
        # Phantom positions (behind and side).
        phantom_offsets = [
            (-facing * 26, -6),  # far back
            (facing * 6, -12),   # slight forward, higher (behind main)
        ]
        for i, (ox, oy) in enumerate(phantom_offsets):
            phantom_cx = cx + ox
            phantom_cy = cy + oy
            # Phantom sway (slightly different from main).
            phantom_cy += int(math.sin(phase * 0.9 + i * 2) * 3)
            _NS_zhyrakaan._draw_body(surface, boss, phantom_cx, phantom_cy,
                                       "idle", 0, alpha_mult=alpha_mult)
    def _draw_juxtapose_phantoms_front(surface, boss, cx, cy, timer, phase):
        """W: 1 phantom in front of body."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.15:
            alpha_mult = progress / 0.15
        elif progress > 0.85:
            alpha_mult = (1 - progress) / 0.15
        else:
            alpha_mult = 1.0
        alpha_mult *= 0.5
        # Front phantom.
        phantom_cx = cx + facing * 20
        phantom_cy = cy + int(math.sin(phase * 0.9 + 3) * 3)
        _NS_zhyrakaan._draw_body(surface, boss, phantom_cx, phantom_cy,
                                   "idle", 0, alpha_mult=alpha_mult)
    def _draw_doppelganger_phantoms_back(surface, boss, cx, cy, timer, phase):
        """R: 3-4 phantoms in circle formation (behind)."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.2:
            alpha_mult = progress / 0.2
        elif progress > 0.85:
            alpha_mult = (1 - progress) / 0.15
        else:
            alpha_mult = 1.0
        alpha_mult *= 0.75
        # 3 phantoms in circle (back positions).
        phantom_offsets = [
            (-facing * 36, -4),   # far back left
            (-facing * 12, -18),  # back top
            (facing * 12, -18),   # front top
        ]
        for i, (ox, oy) in enumerate(phantom_offsets):
            phantom_cx = cx + ox
            phantom_cy = cy + oy
            phantom_cy += int(math.sin(phase * 0.7 + i * 1.5) * 4)
            _NS_zhyrakaan._draw_body(surface, boss, phantom_cx, phantom_cy,
                                       "idle", 0, alpha_mult=alpha_mult)
    def _draw_doppelganger_phantoms_front(surface, boss, cx, cy, timer, phase):
        """R: 2 phantoms in front."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.2:
            alpha_mult = progress / 0.2
        elif progress > 0.85:
            alpha_mult = (1 - progress) / 0.15
        else:
            alpha_mult = 1.0
        alpha_mult *= 0.5
        # 2 phantoms in front side.
        phantom_offsets = [
            (facing * 28, -2),  # far front right
            (facing * 40, -8),  # far far front
        ]
        for i, (ox, oy) in enumerate(phantom_offsets):
            phantom_cx = cx + ox
            phantom_cy = cy + oy
            phantom_cy += int(math.sin(phase * 0.8 + i * 2 + 5) * 4)
            _NS_zhyrakaan._draw_body(surface, boss, phantom_cx, phantom_cy,
                                       "idle", 0, alpha_mult=alpha_mult)
    # ============================================================
    # BASIC ATTACK: Lance thrust
    # ============================================================
    def _draw_basic_thrust_fx(surface, boss, x, y):
        """Blue crystal energy on lance tip during thrust."""
        progress = getattr(boss, "_zh_attack_progress", 0.0)
        if progress < 0.4 or progress > 0.8:
            return
        facing = boss.direction
        tx, ty = _NS_zhyrakaan._lance_tip_position(boss, x, y)
        t = (progress - 0.4) / 0.4
        intensity = math.sin(t * math.pi)
        # Energy trail from tip.
        for i in range(6):
            trail_dist = 4 + i * 2
            angle = 0
            px = tx - facing * trail_dist + int(math.sin(t * 5 + i) * 2)
            py = ty + int(math.cos(t * 5 + i) * 2)
            alpha = _NS_zhyrakaan._alpha(220 * intensity - i * 30)
            if alpha > 0:
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_dark"], alpha),
                                        (px, py), max(1, 4 - i))
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                        (px, py), max(1, 3 - i))
                pygame.draw.rect(surface,
                                 (*_NS_zhyrakaan.PALETTE["crystal_shine"], alpha),
                                 (px, py, 1, 1))
        # Bright glow at tip.
        for r in range(6, 0, -1):
            alpha = _NS_zhyrakaan._alpha(140 * (6 - r) / 6 * intensity)
            _NS_zhyrakaan._aacircle(surface,
                                    (*_NS_zhyrakaan.PALETTE["crystal_hot"], alpha),
                                    (tx, ty), r)
        pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["white"], (tx, ty, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        breath = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, int((12 - radius) * 15 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - radius, 13 - radius,
                                 106 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 10, 25, int(160 * breath)),
                            (10, 8, 110, 10))
        surface.blit(shadow, (x - 65, y - 13))
    def _draw_crystal_aura(surface, x, y, phase):
        """Blue crystal aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_zhyrakaan._alpha((95 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_zhyrakaan._aacircle(aura,
                                        (*_NS_zhyrakaan.PALETTE["crystal_darkest"], alpha),
                                        (110, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_zhyrakaan._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zhyrakaan._aacircle(aura,
                                        (*_NS_zhyrakaan.PALETTE["crystal_dark"], alpha),
                                        (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating crystal shards around body.
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 45 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            # Crystal shard shape.
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_dark"], [
                (sx, sy - 2),
                (sx - 1, sy),
                (sx, sy + 2),
                (sx + 1, sy),
            ])
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["crystal_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zhyrakaan.PALETTE["crystal_darkest"], 200),
                            (5, 18, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_zhyrakaan.PALETTE["crystal_dark"], 220),
                            (14, 20, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_zhyrakaan.PALETTE["crystal_mid"], 180),
                            (25, 22, 130, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_zhyrakaan.PALETTE["crystal_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_zhyrakaan.PALETTE["crystal_shine"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zhyrakaan.PALETTE["crystal_hot"],
                                       _NS_zhyrakaan._alpha(160 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 28))
    # ============================================================
    # SKILL Q: SPIRIT LANCE (throw magic lance)
    # ============================================================
    def _draw_spirit_lance_projectile(surface, boss, x, y, timer, phase):
        """Magical crystal lance projectile."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhyrakaan._target_position(boss, x, y)
        # Source: from hand extended position.
        sx = x + facing * 16
        sy = y - 10
        if progress < 0.3:
            # Wind up: charge on lance.
            t = progress / 0.3
            for r in range(int(10 + t * 6), 0, -1):
                alpha = _NS_zhyrakaan._alpha(150 * (int(10 + t * 6) - r) / (int(10 + t * 6)) * t)
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                        (sx + facing * 20, sy - 4), r)
        else:
            # Lance flying.
            t = (progress - 0.3) / 0.7
            t = min(1.0, t)
            dx = tx - sx
            dy = ty - sy
            length = max(1, math.sqrt(dx * dx + dy * dy))
            dir_x = dx / length
            dir_y = dy / length
            perp_x = -dir_y
            perp_y = dir_x
            bx = int(sx + dx * t)
            by = int(sy + dy * t)
            # Trail behind (crystal shards).
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(sx + dx * trail_t)
                py = int(sy + dy * trail_t)
                alpha = _NS_zhyrakaan._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_darkest"], alpha),
                                        (px, py), size + 1)
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_dark"], alpha),
                                        (px, py), size)
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_light"], alpha),
                                        (px, py), max(1, size - 3))
                # Sparks.
                if i < 5:
                    for s in range(2):
                        sp_ang = trail_t * 6 + i + s * math.pi
                        sp_r = size + 2
                        spx = px + int(math.cos(sp_ang) * sp_r)
                        spy = py + int(math.sin(sp_ang) * sp_r)
                        pygame.draw.rect(surface,
                                         (*_NS_zhyrakaan.PALETTE["crystal_shine"], alpha),
                                         (spx, spy, 1, 1))
            # LANCE shape (long thin projectile).
            lance_len = 22
            lance_back_x = bx - int(dir_x * lance_len)
            lance_back_y = by - int(dir_y * lance_len)
            # Shaft layers.
            for width, color in [
                (5, _NS_zhyrakaan.PALETTE["shadow_deep"]),
                (4, _NS_zhyrakaan.PALETTE["crystal_darkest"]),
                (3, _NS_zhyrakaan.PALETTE["crystal_dark"]),
                (2, _NS_zhyrakaan.PALETTE["crystal_mid"]),
                (1, _NS_zhyrakaan.PALETTE["crystal_light"]),
            ]:
                pygame.draw.line(surface, color,
                                 (lance_back_x, lance_back_y), (bx, by), width)
            # Spearhead at tip.
            head_len = 6
            head_tip_x = bx + int(dir_x * head_len)
            head_tip_y = by + int(dir_y * head_len)
            head_side_a = (bx + int(perp_x * 3), by + int(perp_y * 3))
            head_side_b = (bx - int(perp_x * 3), by - int(perp_y * 3))
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_darkest"], [
                (head_tip_x, head_tip_y), head_side_a, head_side_b,
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_dark"], [
                (head_tip_x, head_tip_y),
                (int((head_tip_x + head_side_a[0]) / 2), int((head_tip_y + head_side_a[1]) / 2)),
                (bx, by),
                (int((head_tip_x + head_side_b[0]) / 2), int((head_tip_y + head_side_b[1]) / 2)),
            ])
            _NS_zhyrakaan._poly(surface, _NS_zhyrakaan.PALETTE["crystal_mid"], [
                (head_tip_x, head_tip_y),
                (int(bx + (head_tip_x - bx) * 0.5),
                 int(by + (head_tip_y - by) * 0.5)),
                (bx, by),
            ])
            # Bright tip glow.
            for r in range(7, 0, -1):
                alpha = _NS_zhyrakaan._alpha(140 * (7 - r) / 7)
                _NS_zhyrakaan._aacircle(surface,
                                        (*_NS_zhyrakaan.PALETTE["crystal_hot"], alpha),
                                        (head_tip_x, head_tip_y), r)
            _NS_zhyrakaan._aacircle(surface, _NS_zhyrakaan.PALETTE["crystal_shine"],
                                    (head_tip_x, head_tip_y), 2)
            pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["white"],
                             (head_tip_x, head_tip_y, 1, 1))
            # Impact burst.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                imp_r = int(15 + st * 18)
                alpha = _NS_zhyrakaan._alpha(240 * (1 - st))
                _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_dark"], alpha),
                                        (tx, ty), imp_r + 3, 3)
                _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                        (tx, ty), imp_r, 3)
                _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_light"], alpha),
                                        (tx, ty), max(1, imp_r - 6), 2)
                _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_shine"], alpha),
                                        (tx, ty), max(1, imp_r // 3))
                pygame.draw.rect(surface, _NS_zhyrakaan.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
                # Radial crystal shards flying out.
                for i in range(10):
                    ang = i * math.pi / 5
                    ex = tx + int(math.cos(ang) * imp_r)
                    ey = ty + int(math.sin(ang) * imp_r * 0.7)
                    _NS_zhyrakaan._poly(surface, (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha), [
                        (ex, ey - 2), (ex - 1, ey), (ex, ey + 2), (ex + 1, ey),
                    ])
                    pygame.draw.rect(surface, (*_NS_zhyrakaan.PALETTE["crystal_shine"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W: JUXTAPOSE (spawn illusions)
    # ============================================================
    def _draw_juxtapose_ground(surface, boss, x, y, timer, phase):
        """Ground ring showing illusion spawn positions."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Rings at each phantom position.
        phantom_positions = [
            (x - facing * 26, y + 52),
            (x + facing * 6 - facing * 8, y + 42),
            (x + facing * 20, y + 52),
        ]
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i, (px, py) in enumerate(phantom_positions):
            r_max = 12
            if progress < 0.15:
                r = int(r_max * (progress / 0.15))
            elif progress > 0.85:
                r = int(r_max * ((1 - progress) / 0.15))
            else:
                r = r_max
            if r < 2:
                continue
            alpha = _NS_zhyrakaan._alpha(180 * pulse)
            pygame.draw.ellipse(surface, (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                (px - r, py - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_zhyrakaan.PALETTE["crystal_light"], alpha),
                                (px - r + 2, py - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)
    # ============================================================
    # SKILL E: PHANTOM EDGE (flurry with evasion)
    # ============================================================
    def _draw_phantom_edge_fx(surface, boss, x, y, timer, phase):
        """Multiple slash lines + evasion shimmer."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhyrakaan._target_position(boss, x, y)
        # Multiple lance thrust lines converging on target.
        num_thrusts = 6
        for i in range(num_thrusts):
            thrust_start = i * 0.12
            if progress < thrust_start:
                continue
            local_t = min(1.0, (progress - thrust_start) / 0.15)
            # Angle for this thrust (spread).
            angle = -math.pi / 3 + (i / (num_thrusts - 1)) * (math.pi * 2 / 3)
            angle *= facing
            # Start from body, end at target with slight offset.
            sx = x + facing * 20 + int(math.cos(angle) * 5)
            sy = y - 6 + int(math.sin(angle) * 5)
            offset_x = int(math.cos(angle) * 15)
            offset_y = int(math.sin(angle) * 15)
            end_x = tx + offset_x
            end_y = ty + offset_y
            # Line extending from body to end.
            cur_end_x = int(sx + (end_x - sx) * local_t)
            cur_end_y = int(sy + (end_y - sy) * local_t)
            alpha = _NS_zhyrakaan._alpha(230 * (1 - local_t * 0.5))
            # Slash lines with crystal glow.
            for width, color in [
                (4, _NS_zhyrakaan.PALETTE["crystal_dark"]),
                (2, _NS_zhyrakaan.PALETTE["crystal_mid"]),
                (1, _NS_zhyrakaan.PALETTE["crystal_light"]),
            ]:
                pygame.draw.line(surface, (*color, alpha),
                                 (sx, sy), (cur_end_x, cur_end_y), width)
            pygame.draw.line(surface, (*_NS_zhyrakaan.PALETTE["crystal_shine"], alpha),
                             (sx, sy), (cur_end_x, cur_end_y), 1)
            # Sparkle at tip.
            _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_hot"], alpha),
                                    (cur_end_x, cur_end_y), 3)
            _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_shine"], alpha),
                                    (cur_end_x, cur_end_y), 2)
            pygame.draw.rect(surface, (*_NS_zhyrakaan.PALETTE["white"], alpha),
                             (cur_end_x, cur_end_y, 1, 1))
        # Impact accumulation at target.
        if progress > 0.4:
            imp_alpha = _NS_zhyrakaan._alpha(200 * min(1.0, (progress - 0.4) / 0.3))
            imp_r = int(15 + math.sin(phase * 5) * 3)
            _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_dark"], imp_alpha),
                                    (tx, ty), imp_r + 2, 2)
            _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_mid"], imp_alpha),
                                    (tx, ty), imp_r, 2)
            _NS_zhyrakaan._aacircle(surface, (*_NS_zhyrakaan.PALETTE["crystal_shine"], imp_alpha),
                                    (tx, ty), max(1, imp_r // 3))
        # Body shimmer (evasion trail).
        for i in range(3):
            shimmer_alpha = _NS_zhyrakaan._alpha(80 - i * 20)
            offset = i * 3 * facing
            pygame.draw.rect(surface, (*_NS_zhyrakaan.PALETTE["crystal_light"], shimmer_alpha),
                             (x - offset - 10, y - 15, 20, 30), 1)
    def _draw_doppelganger_ground(surface, boss, x, y, timer, phase):
        """Ground rings at each phantom position."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Phantom ground positions.
        phantom_positions = [
            (x - facing * 36, y + 50),
            (x - facing * 12, y + 36),
            (x + facing * 12, y + 36),
            (x + facing * 28, y + 52),
            (x + facing * 40, y + 46),
        ]
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i, (px, py) in enumerate(phantom_positions):
            r_max = 14
            if progress < 0.2:
                r = int(r_max * (progress / 0.2))
            elif progress > 0.85:
                r = int(r_max * ((1 - progress) / 0.15))
            else:
                r = r_max
            if r < 2:
                continue
            alpha = _NS_zhyrakaan._alpha(180 * pulse)
            pygame.draw.ellipse(surface, (*_NS_zhyrakaan.PALETTE["crystal_mid"], alpha),
                                (px - r, py - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_zhyrakaan.PALETTE["crystal_light"], alpha),
                                (px - r + 2, py - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)
            # Small crystal shards floating up.
            for j in range(3):
                sh_t = (phase * 0.6 + j * 0.33 + i * 0.15) % 1.0
                sh_x = px + int(math.sin(phase + i + j) * 6)
                sh_y = py - int(sh_t * 20)
                sh_alpha = _NS_zhyrakaan._alpha(200 * (1 - sh_t))
                if sh_alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_zhyrakaan.PALETTE["crystal_mid"], sh_alpha),
                                     (sh_x, sh_y, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_zhyrakaan.PALETTE["crystal_shine"], sh_alpha),
                                     (sh_x, sh_y, 1, 1))



# ====================================================================
# GRONDMAURIS (EARTHBORN) - TRUE BOSS
# ====================================================================

class _NS_grondmauris:
    """Namespace grondmauris - TRUE BOSS stone titan."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Stone (main body)
        "stone_darkest": (25, 22, 20),
        "stone_dark": (58, 55, 50),
        "stone_mid": (105, 100, 92),
        "stone_light": (165, 158, 145),
        "stone_edge": (205, 198, 182),
        "stone_shine": (240, 235, 220),
        # Cracked stone (fissures, dark)
        "crack_dark": (10, 8, 6),
        "crack_mid": (35, 30, 25),
        # Moss / lichen (green growth)
        "moss_darkest": (15, 30, 10),
        "moss_dark": (35, 65, 20),
        "moss_mid": (75, 120, 40),
        "moss_light": (140, 190, 70),
        "moss_shine": (200, 240, 130),
        # Earth/dirt undertone
        "earth_dark": (45, 32, 20),
        "earth_mid": (95, 72, 45),
        "earth_light": (160, 130, 85),
        # GLOWING YELLOW-GOLD eyes (menyala)
        "eye_socket": (5, 3, 0),
        "eye_darkest": (55, 35, 5),
        "eye_dark": (130, 90, 15),
        "eye_mid": (220, 175, 40),
        "eye_light": (255, 225, 100),
        "eye_glow": (255, 250, 200),
        # Energy green (TRUE BOSS magic - grow, aura)
        "energy_darkest": (5, 30, 10),
        "energy_dark": (20, 80, 30),
        "energy_mid": (60, 170, 70),
        "energy_light": (140, 240, 130),
        "energy_hot": (200, 255, 180),
        "energy_shine": (240, 255, 220),
        # Ancient runes (glowing)
        "rune_dark": (40, 20, 5),
        "rune_mid": (180, 130, 40),
        "rune_light": (255, 220, 130),
        # Dust / debris
        "dust_dark": (60, 50, 40),
        "dust_mid": (130, 115, 90),
        "dust_light": (200, 185, 155),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grondmauris._clamp(color)
        if _NS_grondmauris.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_grondmauris._clamp(color)
        if _NS_grondmauris.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_grondmauris._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_grondmauris(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_grondmauris._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_grn_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Grow buff (from R skill).
        grow_scale = float(getattr(boss, "_grn_grow_scale", 1.0))
        # Ambient (aura, ground).
        _NS_grondmauris._draw_earth_aura(surface, x, y, pulse, grow_scale)
        _NS_grondmauris._draw_ground_ring(surface, x, y + 52, pulse, active_skill, grow_scale)
        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_grondmauris._draw_craggy_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_grondmauris._draw_grow_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_grondmauris._draw_avalanche_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_grondmauris._draw_grn_attack(surface, boss, x, y, grow_scale)
        else:
            _NS_grondmauris._draw_grn_float(surface, boss, x, y, grow_scale)
        # Foreground FX.
        if active_skill == "q":
            _NS_grondmauris._draw_avalanche_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grondmauris._draw_toss_foreground(surface, boss, x, y, skill_timer, pulse, grow_scale)
        elif active_skill == "e":
            _NS_grondmauris._draw_craggy_foreground(surface, boss, x, y, skill_timer, pulse, grow_scale)
        elif active_skill == "r":
            _NS_grondmauris._draw_grow_foreground(surface, boss, x, y, skill_timer, pulse, grow_scale)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_grn_previous_timer", 0))
        active = bool(getattr(boss, "_grn_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._grn_attack_active = True
            boss._grn_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._grn_attack_frame = int(getattr(boss, "_grn_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._grn_attack_active = False
            boss._grn_attack_frame = 0
            active = False
        boss._grn_previous_timer = timer
        boss._grn_attack_progress = (
            min(1.0, getattr(boss, "_grn_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
        # Handle grow scale (persist while R active, decay after).
        active_skill = getattr(boss, "active_skill", None)
        if active_skill == "r":
            skill_timer = int(getattr(boss, "active_skill_timer", 0))
            # Scale up during skill.
            t = 1.0 - min(1.0, skill_timer / 120)
            boss._grn_grow_scale = 1.0 + t * 0.35
        else:
            # Decay back to 1.0.
            cur = float(getattr(boss, "_grn_grow_scale", 1.0))
            boss._grn_grow_scale = max(1.0, cur - 0.005)
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_grn_float(surface, boss, x, y, grow_scale=1.0):
        """Idle/moving: floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.5) * 6)
        _NS_grondmauris._draw_shadow(surface, x, y + 54, grow_scale)
        _NS_grondmauris._draw_orbiting_shards(surface, x, y + 5, boss.pulse, grow_scale)
        _NS_grondmauris._draw_dust_particles(surface, x, y + 40, boss.pulse)
        _NS_grondmauris._draw_grn_body(surface, x, y - 4 + hover,
                                       boss.direction, boss.pulse, "float", 0, grow_scale)
    def _draw_grn_attack(surface, boss, x, y, grow_scale=1.0):
        """Attack: MELEE SWING with arm sweeping across."""
        progress = getattr(boss, "_grn_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.5) * 6)
        # Body lean-back → forward slam.
        lean = 0
        if progress < 0.4:
            t = progress / 0.4
            lean = -int(t * 5) * boss.direction  # lean back
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            lean = int((-5 + t * 12)) * boss.direction  # slam forward
        else:
            t = (progress - 0.6) / 0.4
            lean = int(7 * (1 - t)) * boss.direction
        _NS_grondmauris._draw_shadow(surface, x + lean, y + 54, grow_scale)
        _NS_grondmauris._draw_orbiting_shards(surface, x + lean, y + 5, boss.pulse, grow_scale, intense=True)
        _NS_grondmauris._draw_dust_particles(surface, x + lean, y + 40, boss.pulse, intense=True)
        _NS_grondmauris._draw_grn_body(surface, x + lean, y - 4 + hover,
                                       boss.direction, boss.pulse, "attack", progress, grow_scale)
        # Slam impact FX at end of swing.
        _NS_grondmauris._draw_slam_impact(surface, boss, x + lean, y + hover, progress, grow_scale)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_grn_body(surface, cx, cy, facing, phase, action, attack_progress, scale=1.0):
        """Massive stone golem body with moss."""
        # Scale-adjusted key coordinates.
        s = scale
        # Legs / lower stone base (crossed/sitting slightly).
        _NS_grondmauris._draw_stone_legs(surface, cx, cy, facing, phase, s)
        # Main torso (large rocky block).
        _NS_grondmauris._draw_stone_torso(surface, cx, cy, facing, phase, s)
        # Arms (giant boulder fists).
        _NS_grondmauris._draw_stone_arms(surface, cx, cy, facing, phase, action,
                                        attack_progress, s)
        # Head (rocky face with glowing eyes).
        _NS_grondmauris._draw_stone_head(surface, cx, cy - int(24 * s), facing, phase, s)
        # Ancient runes glowing on body.
        _NS_grondmauris._draw_body_runes(surface, cx, cy, facing, phase, s)
    def _draw_stone_legs(surface, cx, cy, facing, phase, s):
        """Chunky rock legs (or floating rock feet)."""
        # Legs are stubby rock chunks.
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + int(side * 8 * s)
            base_y = cy + int(14 * s)
            # Leg chunk (rocky).
            leg_pts = [
                (base_x - int(6 * s), base_y - int(2 * s)),
                (base_x + int(6 * s), base_y - int(2 * s)),
                (base_x + int(8 * s), base_y + int(4 * s)),
                (base_x + int(6 * s), base_y + int(10 * s)),
                (base_x - int(6 * s), base_y + int(10 * s)),
                (base_x - int(8 * s), base_y + int(4 * s)),
            ]
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                                  [(p[0] + 2, p[1] + 3) for p in leg_pts])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_darkest"], leg_pts)
            # Stone shading.
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_dark"], [
                (base_x - int(5 * s), base_y - int(1 * s)),
                (base_x + int(5 * s), base_y - int(1 * s)),
                (base_x + int(7 * s), base_y + int(4 * s)),
                (base_x + int(5 * s), base_y + int(9 * s)),
                (base_x - int(5 * s), base_y + int(9 * s)),
                (base_x - int(7 * s), base_y + int(4 * s)),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_mid"], [
                (base_x - int(3 * s), base_y),
                (base_x + int(3 * s), base_y),
                (base_x + int(5 * s), base_y + int(5 * s)),
                (base_x + int(2 * s), base_y + int(8 * s)),
                (base_x - int(2 * s), base_y + int(8 * s)),
                (base_x - int(5 * s), base_y + int(5 * s)),
            ])
            # Highlight.
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_light"], [
                (base_x - int(1 * s), base_y + int(1 * s)),
                (base_x + int(2 * s), base_y + int(1 * s)),
                (base_x + int(3 * s), base_y + int(4 * s)),
                (base_x, base_y + int(6 * s)),
                (base_x - int(2 * s), base_y + int(4 * s)),
            ])
            # Cracks.
            pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                             (base_x - int(3 * s), base_y + int(2 * s)),
                             (base_x + int(2 * s), base_y + int(7 * s)), 1)
            # Moss patches.
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_dark"], [
                (base_x - int(6 * s), base_y - int(1 * s)),
                (base_x - int(3 * s), base_y - int(2 * s)),
                (base_x - int(2 * s), base_y + int(1 * s)),
                (base_x - int(5 * s), base_y + int(2 * s)),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_mid"], [
                (base_x - int(5 * s), base_y - int(1 * s)),
                (base_x - int(3 * s), base_y - int(1 * s)),
                (base_x - int(3 * s), base_y + int(1 * s)),
                (base_x - int(4 * s), base_y + int(1 * s)),
            ])
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_light"],
                             (base_x - int(4 * s), base_y, 1, 1))
    def _draw_stone_torso(surface, cx, cy, facing, phase, s):
        """Massive rocky torso."""
        # Torso shape (wide, chunky).
        torso_pts = [
            (cx - int(18 * s), cy - int(10 * s)),
            (cx - int(20 * s), cy - int(4 * s)),
            (cx - int(19 * s), cy + int(6 * s)),
            (cx - int(16 * s), cy + int(14 * s)),
            (cx + int(16 * s), cy + int(14 * s)),
            (cx + int(19 * s), cy + int(6 * s)),
            (cx + int(20 * s), cy - int(4 * s)),
            (cx + int(18 * s), cy - int(10 * s)),
            (cx + int(10 * s), cy - int(14 * s)),
            (cx - int(10 * s), cy - int(14 * s)),
        ]
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                              [(p[0] + 3, p[1] + 3) for p in torso_pts])
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_darkest"], torso_pts)
        # Torso mid.
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_dark"], [
            (cx - int(16 * s), cy - int(9 * s)),
            (cx - int(18 * s), cy - int(3 * s)),
            (cx - int(17 * s), cy + int(5 * s)),
            (cx - int(14 * s), cy + int(12 * s)),
            (cx + int(14 * s), cy + int(12 * s)),
            (cx + int(17 * s), cy + int(5 * s)),
            (cx + int(18 * s), cy - int(3 * s)),
            (cx + int(16 * s), cy - int(9 * s)),
            (cx + int(9 * s), cy - int(12 * s)),
            (cx - int(9 * s), cy - int(12 * s)),
        ])
        # Torso rock chunks (visible facets).
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_mid"], [
            (cx - int(12 * s), cy - int(6 * s)),
            (cx - int(14 * s), cy - int(1 * s)),
            (cx - int(12 * s), cy + int(6 * s)),
            (cx - int(6 * s), cy + int(9 * s)),
            (cx + int(6 * s), cy + int(9 * s)),
            (cx + int(12 * s), cy + int(6 * s)),
            (cx + int(14 * s), cy - int(1 * s)),
            (cx + int(12 * s), cy - int(6 * s)),
            (cx, cy - int(9 * s)),
        ])
        # Highlights (top).
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_light"], [
            (cx - int(8 * s), cy - int(7 * s)),
            (cx + int(8 * s), cy - int(7 * s)),
            (cx + int(6 * s), cy - int(2 * s)),
            (cx - int(6 * s), cy - int(2 * s)),
        ])
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_edge"], [
            (cx - int(4 * s), cy - int(6 * s)),
            (cx + int(4 * s), cy - int(6 * s)),
            (cx + int(3 * s), cy - int(4 * s)),
            (cx - int(3 * s), cy - int(4 * s)),
        ])
        # Deep cracks on torso.
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx - int(10 * s), cy - int(4 * s)),
                         (cx - int(6 * s), cy + int(6 * s)), 2)
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_mid"],
                         (cx - int(10 * s), cy - int(4 * s)),
                         (cx - int(6 * s), cy + int(6 * s)), 1)
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx + int(4 * s), cy - int(8 * s)),
                         (cx + int(10 * s), cy + int(2 * s)), 2)
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx - int(2 * s), cy + int(4 * s)),
                         (cx + int(6 * s), cy + int(12 * s)), 1)
        # MOSS patches on shoulders / top.
        moss_patches = [
            [(cx - int(14 * s), cy - int(8 * s)),
             (cx - int(9 * s), cy - int(11 * s)),
             (cx - int(4 * s), cy - int(10 * s)),
             (cx - int(6 * s), cy - int(7 * s))],
            [(cx + int(4 * s), cy - int(10 * s)),
             (cx + int(10 * s), cy - int(11 * s)),
             (cx + int(14 * s), cy - int(8 * s)),
             (cx + int(8 * s), cy - int(6 * s))],
            [(cx - int(18 * s), cy - int(2 * s)),
             (cx - int(15 * s), cy - int(4 * s)),
             (cx - int(13 * s), cy),
             (cx - int(16 * s), cy + int(2 * s))],
        ]
        for patch in moss_patches:
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_darkest"], patch)
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_dark"],
                                  [(p[0] + 1, p[1] + 1) for p in patch[:3]])
            # Bright moss highlight.
            mid_x = sum(p[0] for p in patch) // len(patch)
            mid_y = sum(p[1] for p in patch) // len(patch)
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_mid"], [
                (mid_x - 2, mid_y - 1), (mid_x + 2, mid_y - 1),
                (mid_x + 1, mid_y + 1), (mid_x - 1, mid_y + 1),
            ])
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_light"],
                             (mid_x, mid_y, 1, 1))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_shine"],
                             (mid_x - 1, mid_y - 1, 1, 1))
        # Small hanging moss strands.
        for x_off in (-15, -8, 0, 7, 14):
            hang_x = cx + int(x_off * s)
            hang_y = cy - int(9 * s)
            pygame.draw.line(surface, _NS_grondmauris.PALETTE["moss_dark"],
                             (hang_x, hang_y), (hang_x, hang_y + int(3 * s)), 1)
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                             (hang_x, hang_y + int(2 * s), 1, 1))
    def _draw_stone_arms(surface, cx, cy, facing, phase, action, attack_progress, s):
        """Massive boulder-fist arms."""
        # Swing angle for attack.
        # Right arm (facing side) does the swing.
        swing_side = facing
        # LEFT arm (opposite side): mostly static, hanging down.
        opp_side = -facing
        arm_l_base_x = cx + int(opp_side * 14 * s)
        arm_l_base_y = cy - int(4 * s)
        # Small breath sway.
        sway = math.sin(phase * 0.7) * 1
        arm_l_hand_x = arm_l_base_x + int(opp_side * 6 * s) + int(sway)
        arm_l_hand_y = arm_l_base_y + int(16 * s)
        arm_l_elbow_x = arm_l_base_x + int(opp_side * 4 * s)
        arm_l_elbow_y = arm_l_base_y + int(8 * s)
        # Draw upper arm (shoulder to elbow).
        _NS_grondmauris._draw_stone_limb(surface,
                                         (arm_l_base_x, arm_l_base_y),
                                         (arm_l_elbow_x, arm_l_elbow_y),
                                         int(6 * s))
        # Forearm (elbow to hand).
        _NS_grondmauris._draw_stone_limb(surface,
                                         (arm_l_elbow_x, arm_l_elbow_y),
                                         (arm_l_hand_x, arm_l_hand_y),
                                         int(5 * s))
        # Fist.
        _NS_grondmauris._draw_boulder_fist(surface, arm_l_hand_x, arm_l_hand_y,
                                           int(8 * s), phase)
        # RIGHT arm (facing side): swings in attack.
        # Default rest position.
        arm_r_base_x = cx + int(swing_side * 14 * s)
        arm_r_base_y = cy - int(4 * s)
        if action == "attack":
            # Compute swing angle based on progress.
            if attack_progress < 0.4:
                # Wind-up: arm raises back and up.
                t = attack_progress / 0.4
                angle_deg = -60 + t * -70  # goes from -60 to -130 (back over head)
            elif attack_progress < 0.65:
                # Slam forward.
                t = (attack_progress - 0.4) / 0.25
                angle_deg = -130 + t * 200  # from -130 to +70 (arc slam)
            else:
                # Recovery.
                t = (attack_progress - 0.65) / 0.35
                angle_deg = 70 - t * 130  # back to -60
            angle_rad = math.radians(angle_deg)
            arm_len = int(16 * s)
            hand_off_x = int(math.cos(angle_rad) * arm_len) * swing_side
            hand_off_y = int(math.sin(angle_rad) * arm_len)
            arm_r_hand_x = arm_r_base_x + hand_off_x
            arm_r_hand_y = arm_r_base_y + hand_off_y
            # Elbow at midpoint with slight bend outward.
            elbow_angle = angle_rad + math.radians(15)
            arm_r_elbow_x = arm_r_base_x + int(math.cos(elbow_angle) * arm_len * 0.5) * swing_side
            arm_r_elbow_y = arm_r_base_y + int(math.sin(elbow_angle) * arm_len * 0.5)
        else:
            # Idle: arm hangs down.
            sway = math.sin(phase * 0.5 + 1) * 1
            arm_r_hand_x = arm_r_base_x + int(swing_side * 6 * s) + int(sway)
            arm_r_hand_y = arm_r_base_y + int(16 * s)
            arm_r_elbow_x = arm_r_base_x + int(swing_side * 4 * s)
            arm_r_elbow_y = arm_r_base_y + int(8 * s)
        # Motion blur effect during swing (fast phase only).
        if action == "attack" and 0.4 < attack_progress < 0.65:
            # Draw ghost arm at previous position.
            t_ghost = max(0.4, attack_progress - 0.08)
            ghost_t = (t_ghost - 0.4) / 0.25
            ghost_angle_deg = -130 + ghost_t * 200
            ghost_angle_rad = math.radians(ghost_angle_deg)
            ghost_hand_x = arm_r_base_x + int(math.cos(ghost_angle_rad) * int(16 * s)) * swing_side
            ghost_hand_y = arm_r_base_y + int(math.sin(ghost_angle_rad) * int(16 * s))
            # Draw motion arc (translucent).
            arc_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            _NS_grondmauris._aacircle(arc_surf, (*_NS_grondmauris.PALETTE["stone_mid"], 100),
                                      (60 + ghost_hand_x - arm_r_hand_x,
                                       60 + ghost_hand_y - arm_r_hand_y), int(6 * s))
            surface.blit(arc_surf, (arm_r_hand_x - 60, arm_r_hand_y - 60))
        # Draw upper arm.
        _NS_grondmauris._draw_stone_limb(surface,
                                         (arm_r_base_x, arm_r_base_y),
                                         (arm_r_elbow_x, arm_r_elbow_y),
                                         int(6 * s))
        # Forearm.
        _NS_grondmauris._draw_stone_limb(surface,
                                         (arm_r_elbow_x, arm_r_elbow_y),
                                         (arm_r_hand_x, arm_r_hand_y),
                                         int(5 * s))
        # BOULDER FIST (bigger for attack arm).
        _NS_grondmauris._draw_boulder_fist(surface, arm_r_hand_x, arm_r_hand_y,
                                           int(9 * s), phase)
    def _draw_stone_limb(surface, start, end, thickness):
        """Draw a rocky limb segment."""
        # Shadow.
        _NS_grondmauris._aaline(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                                (start[0] + 2, start[1] + 2),
                                (end[0] + 2, end[1] + 2), thickness + 2)
        # Base dark.
        _NS_grondmauris._aaline(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                                start, end, thickness + 1)
        _NS_grondmauris._aaline(surface, _NS_grondmauris.PALETTE["stone_dark"],
                                start, end, thickness)
        _NS_grondmauris._aaline(surface, _NS_grondmauris.PALETTE["stone_mid"],
                                start, end, max(1, thickness - 2))
        # Highlight on top edge.
        _NS_grondmauris._aaline(surface, _NS_grondmauris.PALETTE["stone_light"],
                                (start[0], start[1] - 1),
                                (end[0], end[1] - 1), max(1, thickness - 4))
        # Add moss speckle at midpoint.
        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_dark"],
                         (mid_x - 1, mid_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                         (mid_x, mid_y - 1, 1, 1))
    def _draw_boulder_fist(surface, cx, cy, radius, phase):
        """Big boulder fist."""
        # Shadow.
        _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                                  (cx + 2, cy + 2), radius + 1)
        # Rock layers.
        _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                                  (cx, cy), radius)
        _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_dark"],
                                  (cx, cy), radius - 1)
        _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_mid"],
                                  (cx - 1, cy - 1), radius - 2)
        # Highlight.
        _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_light"],
                                  (cx - 2, cy - 2), max(1, radius - 4))
        _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_edge"],
                                  (cx - 2, cy - 2), max(1, radius - 5))
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_shine"],
                         (cx - 2, cy - 3, 1, 1))
        # Angular facets (rock look).
        for i in range(4):
            angle = i * math.pi / 2 + math.pi / 4
            fx = cx + int(math.cos(angle) * (radius - 2))
            fy = cy + int(math.sin(angle) * (radius - 2))
            pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                             (cx, cy), (fx, fy), 1)
        # Knuckle bumps.
        for k in range(3):
            kx = cx - radius // 2 + k * (radius // 2)
            ky = cy - radius // 2
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_mid"], (kx, ky), 2)
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_edge"], (kx, ky - 1, 1, 1))
        # Moss patch.
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_dark"], [
            (cx - radius + 1, cy),
            (cx - radius + 3, cy - 1),
            (cx - radius + 3, cy + 2),
            (cx - radius + 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                         (cx - radius + 2, cy, 1, 1))
    def _draw_stone_head(surface, cx, cy, facing, phase, s):
        """Rocky face with glowing yellow eyes and stone brow."""
        # Head shape (chunky boulder).
        head_pts = [
            (cx - int(10 * s), cy),
            (cx - int(12 * s), cy + int(4 * s)),
            (cx - int(11 * s), cy + int(10 * s)),
            (cx - int(6 * s), cy + int(13 * s)),
            (cx + int(6 * s), cy + int(13 * s)),
            (cx + int(11 * s), cy + int(10 * s)),
            (cx + int(12 * s), cy + int(4 * s)),
            (cx + int(10 * s), cy),
            (cx + int(5 * s), cy - int(3 * s)),
            (cx - int(5 * s), cy - int(3 * s)),
        ]
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in head_pts])
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_darkest"], head_pts)
        # Mid.
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_dark"], [
            (cx - int(9 * s), cy + int(1 * s)),
            (cx - int(11 * s), cy + int(4 * s)),
            (cx - int(10 * s), cy + int(9 * s)),
            (cx - int(5 * s), cy + int(12 * s)),
            (cx + int(5 * s), cy + int(12 * s)),
            (cx + int(10 * s), cy + int(9 * s)),
            (cx + int(11 * s), cy + int(4 * s)),
            (cx + int(9 * s), cy + int(1 * s)),
            (cx + int(4 * s), cy - int(2 * s)),
            (cx - int(4 * s), cy - int(2 * s)),
        ])
        # Lighter face plane.
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_mid"], [
            (cx - int(7 * s), cy + int(3 * s)),
            (cx - int(8 * s), cy + int(6 * s)),
            (cx - int(5 * s), cy + int(11 * s)),
            (cx + int(5 * s), cy + int(11 * s)),
            (cx + int(8 * s), cy + int(6 * s)),
            (cx + int(7 * s), cy + int(3 * s)),
        ])
        # Highlight top of head.
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_light"], [
            (cx - int(4 * s), cy),
            (cx + int(4 * s), cy),
            (cx + int(3 * s), cy + int(2 * s)),
            (cx - int(3 * s), cy + int(2 * s)),
        ])
        # Highlight edge on cheek.
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["stone_edge"],
                         (cx - int(9 * s), cy + int(3 * s)),
                         (cx - int(8 * s), cy + int(6 * s)), 1)
        # BROW RIDGE (heavy stone ridge above eyes).
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_darkest"], [
            (cx - int(8 * s), cy + int(4 * s)),
            (cx - int(6 * s), cy + int(3 * s)),
            (cx - int(2 * s), cy + int(4 * s)),
            (cx + int(2 * s), cy + int(4 * s)),
            (cx + int(6 * s), cy + int(3 * s)),
            (cx + int(8 * s), cy + int(4 * s)),
            (cx + int(7 * s), cy + int(6 * s)),
            (cx - int(7 * s), cy + int(6 * s)),
        ])
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_dark"], [
            (cx - int(7 * s), cy + int(4 * s)),
            (cx + int(7 * s), cy + int(4 * s)),
            (cx + int(6 * s), cy + int(5 * s)),
            (cx - int(6 * s), cy + int(5 * s)),
        ])
        # GLOWING YELLOW EYES (deep sockets).
        _NS_grondmauris._draw_glowing_eyes(surface, cx, cy + int(7 * s), s, phase)
        # NOSE / snout crease.
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx, cy + int(8 * s)), (cx, cy + int(11 * s)), 1)
        # Nostril holes.
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx - int(2 * s), cy + int(10 * s), 1, 1))
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx + int(1 * s), cy + int(10 * s), 1, 1))
        # MOUTH (grim line).
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx - int(4 * s), cy + int(12 * s)),
                         (cx + int(4 * s), cy + int(12 * s)), 2)
        # Small tusk hint.
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_edge"],
                         (cx - int(3 * s), cy + int(12 * s), 1, 1))
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_edge"],
                         (cx + int(2 * s), cy + int(12 * s), 1, 1))
        # Moss on top of head.
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_darkest"], [
            (cx - int(8 * s), cy - int(1 * s)),
            (cx - int(3 * s), cy - int(3 * s)),
            (cx + int(3 * s), cy - int(3 * s)),
            (cx + int(8 * s), cy - int(1 * s)),
            (cx + int(6 * s), cy + int(1 * s)),
            (cx - int(6 * s), cy + int(1 * s)),
        ])
        _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_dark"], [
            (cx - int(6 * s), cy - int(1 * s)),
            (cx - int(2 * s), cy - int(2 * s)),
            (cx + int(2 * s), cy - int(2 * s)),
            (cx + int(6 * s), cy - int(1 * s)),
            (cx + int(4 * s), cy),
            (cx - int(4 * s), cy),
        ])
        # Moss highlights.
        for mx in (-4, 0, 4):
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                             (cx + int(mx * s), cy - int(2 * s), 1, 1))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_light"],
                             (cx + int(mx * s), cy - int(2 * s), 1, 1))
        # Head cracks.
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx - int(9 * s), cy + int(2 * s)),
                         (cx - int(7 * s), cy + int(9 * s)), 1)
        pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                         (cx + int(8 * s), cy + int(5 * s)),
                         (cx + int(10 * s), cy + int(11 * s)), 1)
    def _draw_glowing_eyes(surface, cx, cy, s, phase):
        """Bright yellow-gold glowing eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + int(side * 4 * s)
            ey = cy
            # Deep socket.
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                             (ex - 2, ey - 1, 4, 3))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_socket"],
                             (ex - 2, ey - 1, 4, 3))
            # Glow halo.
            for radius in range(6, 0, -1):
                alpha = _NS_grondmauris._alpha(120 * (6 - radius) / 6 * pulse)
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["eye_mid"], alpha),
                                          (ex, ey), radius)
            # Iris.
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_darkest"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
        # Between-eye glow (like a third eye hint).
        pygame.draw.rect(surface, _NS_grondmauris.PALETTE["eye_dark"], (cx, cy - 2, 1, 1))
    def _draw_body_runes(surface, cx, cy, facing, phase, s):
        """Ancient glowing runes on stone body."""
        pulse = math.sin(phase * 1.5) * 0.4 + 0.6
        # Runes on chest.
        rune_positions = [
            (cx - int(8 * s), cy - int(2 * s)),
            (cx + int(6 * s), cy + int(4 * s)),
            (cx - int(4 * s), cy + int(8 * s)),
        ]
        for i, (rx, ry) in enumerate(rune_positions):
            alpha = _NS_grondmauris._alpha(180 * pulse)
            # Small rune symbol (diamond or cross).
            if i % 2 == 0:
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["rune_mid"], alpha),
                                 (rx - 2, ry), (rx + 2, ry), 1)
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["rune_mid"], alpha),
                                 (rx, ry - 2), (rx, ry + 2), 1)
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["rune_light"],
                                 (rx, ry, 1, 1))
            else:
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["rune_mid"], alpha),
                                 (rx - 1, ry - 1), (rx + 1, ry + 1), 1)
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["rune_mid"], alpha),
                                 (rx - 1, ry + 1), (rx + 1, ry - 1), 1)
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["rune_light"],
                                 (rx, ry, 1, 1))
    # ============================================================
    # MELEE SLAM IMPACT
    # ============================================================
    def _draw_slam_impact(surface, boss, x, y, progress, scale=1.0):
        """Ground crack + dust burst when arm slams down."""
        if not (0.55 <= progress <= 0.85):
            return
        facing = boss.direction
        # Impact point (in front of boss on ground).
        ix = x + int(facing * 30 * scale)
        iy = y + int(50 * scale)
        t = (progress - 0.55) / 0.30
        radius = int(scale * (10 + t * 30))
        alpha = _NS_grondmauris._alpha(240 * (1 - t))
        # Ground shockwave (elliptical).
        pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["stone_darkest"], alpha),
                            (ix - radius, iy - radius // 3,
                             radius * 2, radius * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["dust_mid"], alpha),
                            (ix - radius + 3, iy - radius // 3 + 1,
                             radius * 2 - 6, radius * 2 // 3 - 2), 2)
        # Crack lines radiating.
        for i in range(8):
            angle = i * math.pi / 4
            cx1 = ix + int(math.cos(angle) * 5)
            cy1 = iy + int(math.sin(angle) * 3)
            cx2 = ix + int(math.cos(angle) * radius)
            cy2 = iy + int(math.sin(angle) * radius * 0.6)
            pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["crack_dark"], alpha),
                             (cx1, cy1), (cx2, cy2), 2)
        # Dust cloud rising.
        for i in range(8):
            angle = i * math.pi / 4 + phase_offset(boss)
            dust_r = int(radius * 0.7)
            dx = ix + int(math.cos(angle) * dust_r)
            dy = iy + int(math.sin(angle) * dust_r * 0.5) - int(t * 15)
            dust_alpha = _NS_grondmauris._alpha(200 * (1 - t))
            _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["dust_dark"], dust_alpha),
                                      (dx, dy), 4)
            _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["dust_mid"], dust_alpha),
                                      (dx, dy), 3)
            pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["dust_light"], dust_alpha),
                             (dx, dy, 1, 1))
        # Small rock chunks flying out.
        for i in range(6):
            angle = i * math.pi / 3 + t * 2
            chunk_dist = int(radius * (0.5 + t * 0.5))
            cx1 = ix + int(math.cos(angle) * chunk_dist)
            cy1 = iy + int(math.sin(angle) * chunk_dist * 0.5) - int(t * 10)
            _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["stone_dark"], alpha),
                                      (cx1, cy1), 3)
            _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["stone_mid"], alpha),
                                      (cx1, cy1), 2)
            pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["stone_light"], alpha),
                             (cx1, cy1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, scale=1.0):
        w = int(160 * scale)
        h = int(30 * scale)
        shadow = pygame.Surface((w + 20, h + 10), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, h // 2 - radius, w + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 2, 170),
                            (5, h // 2 - h // 4, w + 10, h // 2))
        pygame.draw.ellipse(shadow, (30, 40, 20, 110),
                            (12, h // 2 - h // 5, w - 4, h // 3))
        surface.blit(shadow, (x - (w + 20) // 2, y - h // 2))
    def _draw_earth_aura(surface, x, y, phase, scale=1.0):
        """Green earth energy aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        size = int(220 * scale)
        aura = pygame.Surface((size, int(size * 0.8)), pygame.SRCALPHA)
        center = (size // 2, int(size * 0.4))
        for radius in range(int(95 * scale), 5, -5):
            alpha = _NS_grondmauris._alpha((95 - radius / scale) * 1.3 * pulse)
            if alpha > 0:
                _NS_grondmauris._aacircle(aura, (*_NS_grondmauris.PALETTE["moss_darkest"], alpha),
                                          center, radius)
        for radius in range(int(60 * scale), 5, -4):
            alpha = _NS_grondmauris._alpha((60 - radius / scale) * 1.5 * pulse)
            if alpha > 0:
                _NS_grondmauris._aacircle(aura, (*_NS_grondmauris.PALETTE["energy_darkest"], alpha),
                                          center, radius)
        for radius in range(int(35 * scale), 5, -3):
            alpha = _NS_grondmauris._alpha((35 - radius / scale) * 1.5 * pulse)
            if alpha > 0:
                _NS_grondmauris._aacircle(aura, (*_NS_grondmauris.PALETTE["energy_dark"], alpha),
                                          center, radius)
        surface.blit(aura, (x - size // 2, y - int(size * 0.4)))
        # Floating earth motes.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = int((40 + math.sin(phase + i) * 12) * scale)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_grondmauris.PALETTE["energy_mid"] if i % 3 != 0 \
                else _NS_grondmauris.PALETTE["rune_mid"]
            hot_color = _NS_grondmauris.PALETTE["energy_light"] if i % 3 != 0 \
                else _NS_grondmauris.PALETTE["rune_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill, scale=1.0):
        """Rune ring on ground beneath boss."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        w = int(180 * scale)
        h = int(58 * scale)
        ring = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_grondmauris.PALETTE["moss_darkest"], 200),
                            (5, 18, w - 10, h - 26), 3)
        pygame.draw.ellipse(ring, (*_NS_grondmauris.PALETTE["energy_darkest"], 220),
                            (14, 20, w - 28, h - 30), 2)
        pygame.draw.ellipse(ring, (*_NS_grondmauris.PALETTE["energy_dark"], 230),
                            (25, 22, w - 50, h - 34), 1)
        pygame.draw.ellipse(ring, (*_NS_grondmauris.PALETTE["rune_dark"], 180),
                            (40, 24, w - 80, h - 38), 1)
        # Runes.
        cx_ring = w // 2
        cy_ring = h // 2
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = cx_ring + int(math.cos(angle) * (w // 3.5))
            y1 = cy_ring + int(math.sin(angle) * (h // 6))
            x2 = cx_ring + int(math.cos(angle) * (w // 2.5))
            y2 = cy_ring + int(math.sin(angle) * (h // 4))
            pygame.draw.line(ring, (*_NS_grondmauris.PALETTE["rune_mid"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_grondmauris.PALETTE["rune_light"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_grondmauris.PALETTE["energy_hot"],
                                       _NS_grondmauris._alpha(150 * pulse)),
                                (15, 12, w - 30, h - 16), 1)
        surface.blit(ring, (x - w // 2, y - h // 2))
    def _draw_orbiting_shards(surface, cx, cy, phase, scale=1.0, intense=False):
        """Rock shards orbiting boss (magical floating)."""
        num_shards = 8 if not intense else 12
        for i in range(num_shards):
            angle = phase * 0.6 + i * (math.pi * 2 / num_shards)
            orbit_r = int((45 + math.sin(phase + i) * 4) * scale)
            orbit_h = int(orbit_r * 0.35)  # ellipse height
            sx = cx + int(math.cos(angle) * orbit_r)
            sy = cy + int(math.sin(angle) * orbit_h)
            # Depth cue: shards behind boss are darker/smaller.
            is_behind = math.sin(angle) < 0
            shard_size = int(3 * scale) if not is_behind else int(2 * scale)
            base_color = _NS_grondmauris.PALETTE["stone_dark"] if is_behind \
                else _NS_grondmauris.PALETTE["stone_mid"]
            # Shadow.
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                             (sx - shard_size + 1, sy - shard_size + 1,
                              shard_size * 2, shard_size * 2))
            # Shard.
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                             (sx - shard_size, sy - shard_size,
                              shard_size * 2, shard_size * 2))
            pygame.draw.rect(surface, base_color,
                             (sx - shard_size + 1, sy - shard_size + 1,
                              shard_size * 2 - 1, shard_size * 2 - 1))
            if not is_behind:
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_light"],
                                 (sx - shard_size + 1, sy - shard_size + 1, 1, 1))
                # Small moss on shard.
                if i % 2 == 0:
                    pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                                     (sx + shard_size - 2, sy + shard_size - 2, 1, 1))
    def _draw_dust_particles(surface, cx, cy, phase, intense=False):
        """Dust particles floating around."""
        strength = 1.5 if intense else 1.0
        for i in range(8):
            t = (phase * 0.3 + i * 0.13) % 1.0
            sx = cx + int(math.sin(phase + i * 0.7) * (20 + i * 3))
            sy = cy + 4 - int(t * 20)
            alpha = _NS_grondmauris._alpha(180 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["dust_dark"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["dust_mid"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: Q - AVALANCHE (rocks fall from sky in target area)
    # ============================================================
    def _draw_avalanche_ground(surface, boss, x, y, timer, phase):
        """Target zone marker on ground."""
        tx, ty = _NS_grondmauris._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))
        if r > 3:
            # Warning zone (dark stone).
            pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["stone_darkest"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["stone_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Impact craters emerging.
            for i in range(5):
                crater_t = (phase * 0.5 + i * 0.2) % 1.0
                if crater_t > progress:
                    continue
                cangle = i * math.pi / 2.5
                cdist = int(r * 0.6)
                ccx = tx + int(math.cos(cangle) * cdist)
                ccy = ty + int(math.sin(cangle) * cdist * 0.5)
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["crack_dark"], 200),
                                          (ccx, ccy), 4)
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["stone_dark"], 220),
                                          (ccx, ccy), 3)
    def _draw_avalanche_foreground(surface, boss, x, y, timer, phase):
        """Rocks falling from sky."""
        tx, ty = _NS_grondmauris._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple rocks with staggered timing.
        num_rocks = 10
        for i in range(num_rocks):
            rock_delay = (i * 0.08) % 0.7
            rock_progress = ((progress + i * 0.13) * 1.5) % 1.0
            # Fall from top.
            fall_start_y = ty - 200
            rock_x_off = int(math.sin(i * 1.7) * 40)
            rock_y = fall_start_y + int(rock_progress * (ty - fall_start_y))
            rock_x = tx + rock_x_off
            if rock_progress < 1.0:
                # Falling rock.
                rock_size = 4 + (i % 3)
                # Motion streak.
                streak_len = 12
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["stone_light"], 150),
                                 (rock_x, rock_y - streak_len),
                                 (rock_x, rock_y), 2)
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["stone_edge"], 200),
                                 (rock_x, rock_y - streak_len + 2),
                                 (rock_x, rock_y), 1)
                # Rock body.
                _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                                          (rock_x + 1, rock_y + 1), rock_size + 1)
                _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                                          (rock_x, rock_y), rock_size)
                _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_dark"],
                                          (rock_x, rock_y), rock_size - 1)
                _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_mid"],
                                          (rock_x - 1, rock_y - 1), max(1, rock_size - 2))
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_light"],
                                 (rock_x - 1, rock_y - 1, 1, 1))
            else:
                # Impact dust.
                impact_t = (rock_progress - 1.0) * 5
                if impact_t < 1.0:
                    dust_r = int(6 + impact_t * 10)
                    alpha = _NS_grondmauris._alpha(200 * (1 - impact_t))
                    _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["dust_dark"], alpha),
                                              (rock_x, ty), dust_r, 2)
                    _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["dust_mid"], alpha),
                                              (rock_x, ty), max(1, dust_r - 3), 1)
                    for k in range(4):
                        spark_angle = k * math.pi / 2 + impact_t * 3
                        sx = rock_x + int(math.cos(spark_angle) * dust_r)
                        sy = ty + int(math.sin(spark_angle) * dust_r * 0.5)
                        pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["stone_edge"], alpha),
                                         (sx, sy, 1, 1))
        # Rising rock spikes from ground.
        for i in range(6):
            spike_t = (phase * 0.4 + i * 0.15) % 1.0
            if spike_t > progress * 1.5:
                continue
            sangle = i * math.pi / 3
            sdist = 30
            spike_x = tx + int(math.cos(sangle) * sdist)
            spike_base_y = ty + int(math.sin(sangle) * sdist * 0.5)
            spike_h = int(15 * spike_t)
            spike_tip_y = spike_base_y - spike_h
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 3 + 1, spike_base_y + 1),
                (spike_x + 3 + 1, spike_base_y + 1),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 3, spike_base_y),
                (spike_x + 3, spike_base_y),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_mid"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y - 2),
                (spike_x + 1, spike_base_y - 2),
            ])
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_edge"],
                             (spike_x, spike_tip_y, 1, 1))
    # ============================================================
    # SKILL: W - BOULDER TOSS (projectile)
    # ============================================================
    def _draw_toss_foreground(surface, boss, x, y, timer, phase, scale=1.0):
        """Big boulder hurled at target with green trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_grondmauris._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.5) * 6)
        if progress < 0.25:
            # Wind-up: boulder in hand.
            t = progress / 0.25
            hand_x = x + int(facing * 20 * scale)
            hand_y = y - int(4 * scale) + hover + int((1 - t) * 10)
            boulder_r = int(scale * (6 + t * 4))
            # Green energy gathering around boulder.
            for r in range(boulder_r + 6, 0, -1):
                alpha = _NS_grondmauris._alpha(160 * t * (boulder_r + 6 - r) / (boulder_r + 6))
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_dark"], alpha),
                                          (hand_x, hand_y), r)
            # Boulder.
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                                      (hand_x + 2, hand_y + 2), boulder_r + 1)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                                      (hand_x, hand_y), boulder_r)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_dark"],
                                      (hand_x, hand_y), boulder_r - 1)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_mid"],
                                      (hand_x - 1, hand_y - 1), boulder_r - 2)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_light"],
                                      (hand_x - 2, hand_y - 2), max(1, boulder_r - 4))
            # Moss on boulder.
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["moss_dark"], [
                (hand_x - boulder_r + 1, hand_y),
                (hand_x - boulder_r + 3, hand_y - 1),
                (hand_x - boulder_r + 3, hand_y + 2),
                (hand_x - boulder_r + 1, hand_y + 2),
            ])
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                             (hand_x - boulder_r + 2, hand_y, 1, 1))
        else:
            # Projectile flight (arc).
            t = (progress - 0.25) / 0.75
            t = min(1.0, t)
            start_x = x + int(facing * 24 * scale)
            start_y = y - int(4 * scale) + hover
            # Parabolic arc.
            arc_height = -60
            bx = int(start_x + (tx - start_x) * t)
            arc_offset = int(arc_height * 4 * t * (1 - t))  # peak at t=0.5
            by = int(start_y + (ty - start_y) * t + arc_offset)
            # Green energy trail (comet-like).
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                trail_arc = int(arc_height * 4 * trail_t * (1 - trail_t))
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t + trail_arc)
                alpha = _NS_grondmauris._alpha(220 - i * 25)
                size = max(1, 7 - i)
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_darkest"], alpha),
                                          (px, py), size)
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_dark"], alpha),
                                          (px, py), max(1, size - 1))
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_mid"], alpha),
                                          (px, py), max(1, size - 2))
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_light"], alpha),
                                          (px, py), max(1, size - 3))
                if i < 4:
                    for s_i in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s_i) * (size + 1))
                        spark_y = py + int(math.cos(t * 6 + i + s_i) * (size + 1))
                        pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["energy_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Boulder head (spinning).
            spin = int(phase * 3) % 4
            boulder_r = int(scale * 8)
            # Green magic glow around boulder.
            for r in range(boulder_r + 8, boulder_r, -1):
                alpha = _NS_grondmauris._alpha(150 * (boulder_r + 8 - r) / 8)
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_mid"], alpha),
                                          (bx, by), r)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["shadow_deep"],
                                      (bx + 2, by + 2), boulder_r + 1)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                                      (bx, by), boulder_r)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_dark"],
                                      (bx, by), boulder_r - 1)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_mid"],
                                      (bx - 1, by - 1), boulder_r - 2)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["stone_light"],
                                      (bx - 2, by - 2), max(1, boulder_r - 4))
            # Spinning facets.
            for i in range(4):
                fangle = i * math.pi / 2 + phase * 2
                fx = bx + int(math.cos(fangle) * (boulder_r - 2))
                fy = by + int(math.sin(fangle) * (boulder_r - 2))
                pygame.draw.line(surface, _NS_grondmauris.PALETTE["crack_dark"],
                                 (bx, by), (fx, fy), 1)
            # Moss chunks (spinning around).
            for i in range(3):
                mangle = i * math.pi * 2 / 3 + phase * 2
                mx = bx + int(math.cos(mangle) * (boulder_r - 1))
                my = by + int(math.sin(mangle) * (boulder_r - 1))
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_dark"], (mx - 1, my - 1, 2, 2))
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"], (mx, my, 1, 1))
            # Impact.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(15 + st * 30)
                alpha = _NS_grondmauris._alpha(240 * (1 - st))
                # Ground crack.
                pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["stone_darkest"], alpha),
                                    (tx - radius, ty - radius // 3,
                                     radius * 2, radius * 2 // 3), 3)
                pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["crack_dark"], alpha),
                                    (tx - radius + 4, ty - radius // 3 + 2,
                                     radius * 2 - 8, radius * 2 // 3 - 4), 2)
                # Dust burst.
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.5)
                    _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["dust_mid"], alpha),
                                              (ex, ey), 3)
                    pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["dust_light"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL: E - CRAGGY EXTERIOR (armor buff with rock spikes)
    # ============================================================
    def _draw_craggy_ground(surface, boss, x, y, timer, phase):
        """Circle of energy around boss during craggy exterior."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_grondmauris._alpha(180 - i * 50)
            pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["stone_edge"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["moss_mid"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 1, r * 2 - 6, r * 2 // 3 - 2), 1)
    def _draw_craggy_foreground(surface, boss, x, y, timer, phase, scale=1.0):
        """Rock spikes protruding from boss body + shield sparks."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 6)
        cy = y - 4 + hover
        # Rock spikes sticking out of body (defensive plates).
        num_spikes = 10
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + phase * 0.2
            spawn_t = min(1.0, progress * 2 - i * 0.03)
            if spawn_t <= 0:
                continue
            base_r = int(20 * scale * spawn_t)
            tip_r = int(28 * scale * spawn_t)
            base_x = x + int(math.cos(angle) * base_r)
            base_y = cy + int(math.sin(angle) * base_r * 0.7)
            tip_x = x + int(math.cos(angle) * tip_r)
            tip_y = cy + int(math.sin(angle) * tip_r * 0.7)
            perp = angle + math.pi / 2
            pa_x = base_x + int(math.cos(perp) * 3)
            pa_y = base_y + int(math.sin(perp) * 3)
            pb_x = base_x - int(math.cos(perp) * 3)
            pb_y = base_y - int(math.sin(perp) * 3)
            # Shadow.
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_darkest"],
                                  [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_dark"], [
                (tip_x, tip_y),
                (int((pa_x + base_x) / 2), int((pa_y + base_y) / 2)),
                (int((pb_x + base_x) / 2), int((pb_y + base_y) / 2)),
            ])
            _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["stone_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["stone_edge"], (tip_x, tip_y, 1, 1))
            # Moss on spike base.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_dark"],
                                 (base_x - 1, base_y - 1, 2, 2))
                pygame.draw.rect(surface, _NS_grondmauris.PALETTE["moss_mid"],
                                 (base_x, base_y, 1, 1))
        # Shield spark bursts (deflected attacks).
        for i in range(4):
            spark_t = (phase * 1.5 + i * 0.25) % 1.0
            if spark_t < 0.7:
                continue
            sangle = i * math.pi / 2 + phase
            sr = int(30 * scale)
            sx = x + int(math.cos(sangle) * sr)
            sy = cy + int(math.sin(sangle) * sr * 0.7)
            spark_alpha = _NS_grondmauris._alpha(240 * (1 - (spark_t - 0.7) / 0.3))
            _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["rune_mid"], spark_alpha),
                                      (sx, sy), 4)
            _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["rune_light"], spark_alpha),
                                      (sx, sy), 2)
            for k in range(4):
                sk_angle = k * math.pi / 2 + spark_t * 5
                skx = sx + int(math.cos(sk_angle) * 5)
                sky = sy + int(math.sin(sk_angle) * 5)
                pygame.draw.line(surface, (*_NS_grondmauris.PALETTE["rune_light"], spark_alpha),
                                 (sx, sy), (skx, sky), 1)
            pygame.draw.rect(surface, (*_NS_grondmauris.PALETTE["white"], spark_alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: R - GROW! (boss enlarges, green energy pillars)
    # ============================================================
    def _draw_grow_ground(surface, boss, x, y, timer, phase):
        """Energy circle expanding under boss."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Grand ritual circle (larger).
        for i in range(4):
            base_r = 45 + i * 10
            r = int(base_r + math.sin(phase * 2 + i) * 4)
            alpha = _NS_grondmauris._alpha(230 - i * 40)
            pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["energy_darkest"], alpha),
                                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_grondmauris.PALETTE["energy_dark"], alpha),
                                (x - r + 2, y + 42 - r // 3 + 1, r * 2 - 4, r * 2 // 3 - 2), 1)
        # Ground energy runes.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r1 = 55
            r2 = 80
            x1 = x + int(math.cos(angle) * r1)
            y1 = y + 42 + int(math.sin(angle) * r1 * 0.4)
            x2 = x + int(math.cos(angle) * r2)
            y2 = y + 42 + int(math.sin(angle) * r2 * 0.4)
            pygame.draw.line(surface, _NS_grondmauris.PALETTE["energy_light"], (x1, y1), (x2, y2), 2)
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["energy_shine"], (x2, y2, 2, 2))
    def _draw_grow_foreground(surface, boss, x, y, timer, phase, scale=1.0):
        """Vertical green energy pillars around boss."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 6)
        # Rising green energy pillars around boss.
        num_pillars = 8
        for i in range(num_pillars):
            pangle = i * math.pi * 2 / num_pillars + phase * 0.15
            pdist = int(50 * scale)
            px = x + int(math.cos(pangle) * pdist)
            py_ground = y + int(45 * scale) + int(math.sin(pangle) * pdist * 0.4)
            # Pillar rises with staggered timing.
            spawn_t = min(1.0, progress * 2 - i * 0.02)
            if spawn_t <= 0:
                continue
            pillar_h = int(60 * scale * spawn_t)
            pillar_top_y = py_ground - pillar_h
            # Draw pillar as tapered vertical energy column.
            for layer_i, (width, alpha_val) in enumerate([
                (8, 100), (5, 150), (3, 200), (1, 240),
            ]):
                colors = [
                    _NS_grondmauris.PALETTE["energy_darkest"],
                    _NS_grondmauris.PALETTE["energy_dark"],
                    _NS_grondmauris.PALETTE["energy_mid"],
                    _NS_grondmauris.PALETTE["energy_light"],
                ]
                color = colors[min(layer_i, 3)]
                pygame.draw.rect(surface, (*color, alpha_val),
                                 (px - width // 2, pillar_top_y,
                                  width, pillar_h))
            # Arrows/chevrons rising up the pillar.
            for arrow_i in range(3):
                arrow_t = (phase * 0.8 + arrow_i * 0.33 + i * 0.1) % 1.0
                ay = py_ground - int(arrow_t * pillar_h)
                # Up arrow shape.
                _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["energy_hot"], [
                    (px, ay - 3),
                    (px - 3, ay),
                    (px + 3, ay),
                ])
                _NS_grondmauris._poly(surface, _NS_grondmauris.PALETTE["energy_shine"], [
                    (px, ay - 2),
                    (px - 2, ay),
                    (px + 2, ay),
                ])
            # Sparkle at top of pillar.
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["energy_light"],
                                      (px, pillar_top_y), 3)
            _NS_grondmauris._aacircle(surface, _NS_grondmauris.PALETTE["energy_shine"],
                                      (px, pillar_top_y), 2)
            pygame.draw.rect(surface, _NS_grondmauris.PALETTE["white"], (px, pillar_top_y, 1, 1))
        # Boss glow (empowered aura).
        core_y = y - 8 + hover
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(int(30 * scale), 0, -3):
            alpha = _NS_grondmauris._alpha(140 * pulse * (30 - r / scale) / 30)
            if alpha > 0:
                _NS_grondmauris._aacircle(surface, (*_NS_grondmauris.PALETTE["energy_mid"], alpha),
                                          (x, core_y), r)
def phase_offset(boss):
    """Helper to get phase offset for dust animation."""
    return float(getattr(boss, "pulse", 0.0)) * 0.5

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_infrakzaar(surface, boss, x, y):
    """Entry point infrakzaar."""
    return _NS_infrakzaar.draw_infrakzaar(surface, boss, x, y)


def draw_xarnathul(surface, boss, x, y):
    """Entry point xarnathul."""
    return _NS_xarnathul.draw_xarnathul(surface, boss, x, y)


def draw_zhyrakaan(surface, boss, x, y):
    """Entry point zhyrakaan."""
    return _NS_zhyrakaan.draw_zhyrakaan(surface, boss, x, y)


def draw_grondmauris(surface, boss, x, y):
    """Entry point grondmauris."""
    return _NS_grondmauris.draw_grondmauris(surface, boss, x, y)
