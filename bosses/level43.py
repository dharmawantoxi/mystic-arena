"""
bosses/level43.py - Semua boss Level 43

Berisi:
  - nixweaver   (mini boss - RANGED woodland trickster)
  - nyxraal     (mini boss - MELEE abyssal prince)
  - xarnthuul   (mini boss - RANGED void sovereign)
  - zyvareth    (TRUE BOSS - RANGED stormherald, crystal-horned)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _xt_ (xarnthuul), _zy_ (zyvareth) sudah unik.
  - _nx_ (nixweaver) di-rename -> _nxw_ (bentrok dengan nyxharr
    level 30), termasuk atribut _last_x/_last_y.
  - _nx_ (nyxraal) di-rename -> _nxr_ (bentrok dengan nyxharr
    level 30 & nixweaver level ini), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# NIXWEAVER (WOODLAND TRICKSTER) - Mini Boss
# ====================================================================

class _NS_nixweaver:
    """Namespace nixweaver - Woodland Trickster boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Fur (brown squirrel/critter)
        "fur_darkest": (25, 15, 8),
        "fur_dark": (65, 40, 20),
        "fur_mid": (120, 80, 45),
        "fur_light": (180, 130, 80),
        "fur_shine": (230, 190, 140),
        # White belly fur
        "belly_dark": (140, 120, 100),
        "belly_mid": (200, 185, 165),
        "belly_light": (245, 235, 220),
        # Hood/cloak (forest green)
        "hood_darkest": (15, 30, 10),
        "hood_dark": (35, 60, 20),
        "hood_mid": (75, 115, 35),
        "hood_light": (130, 175, 65),
        "hood_shine": (185, 220, 110),
        # Gold trim
        "gold_dark": (90, 65, 15),
        "gold_mid": (185, 145, 45),
        "gold_light": (245, 215, 110),
        "gold_shine": (255, 240, 180),
        # Wood (crossbow, staff)
        "wood_dark": (45, 25, 12),
        "wood_mid": (95, 60, 28),
        "wood_light": (155, 105, 55),
        # Metal (bowstring, arrow tip)
        "metal_dark": (30, 30, 35),
        "metal_mid": (100, 100, 115),
        "metal_light": (180, 180, 195),
        # Amber/acorn ammo (glowing gold-green)
        "amber_darkest": (30, 20, 5),
        "amber_dark": (95, 65, 15),
        "amber_mid": (200, 155, 40),
        "amber_light": (250, 220, 100),
        "amber_hot": (255, 245, 170),
        "amber_shine": (255, 255, 220),
        # Leaf green (bushes, trails)
        "leaf_dark": (25, 60, 15),
        "leaf_mid": (70, 140, 40),
        "leaf_light": (140, 210, 80),
        "leaf_shine": (200, 245, 130),
        # Eye (curious dark eye)
        "eye_dark": (10, 5, 5),
        "eye_mid": (35, 20, 15),
        "eye_shine": (245, 235, 220),
        # Nose (pink)
        "nose_dark": (85, 40, 45),
        "nose_light": (185, 105, 110),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nixweaver._clamp(color)
        if _NS_nixweaver.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nixweaver._clamp(color)
        if _NS_nixweaver.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nixweaver._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nixweaver(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nixweaver._detect_moving(boss)
        _NS_nixweaver._update_attack_anim(boss)
        attacking = getattr(boss, "_nxw_attack_active", False)
        # Ambient behind
        _NS_nixweaver._draw_forest_aura(surface, x, y, pulse)
        _NS_nixweaver._draw_ground_ring(surface, x, y + 42, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_nixweaver._draw_thicket_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nixweaver._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if active_skill == "r":
            _NS_nixweaver._draw_channel_pose(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_nixweaver._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_nixweaver._draw_walk(surface, boss, x, y)
        else:
            _NS_nixweaver._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_nixweaver._draw_thornshot_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nixweaver._draw_thicket_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nixweaver._draw_dash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nixweaver._draw_piercebolt_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_nxw_attack_active", False))
        if not active and timer <= 2:
            boss._nxw_attack_active = True
            boss._nxw_attack_frame = 0
            active = True
        if active:
            boss._nxw_attack_frame = int(getattr(boss, "_nxw_attack_frame", 0)) + 1
            if boss._nxw_attack_frame >= cooldown:
                boss._nxw_attack_active = False
                boss._nxw_attack_frame = 0
                active = False
        boss._nxw_attack_progress = (
            min(1.0, getattr(boss, "_nxw_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nxw_last_x"):
            boss._nxw_last_x = boss.x
            boss._nxw_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nxw_last_x)
        dy = abs(boss.y - boss._nxw_last_y)
        boss._nxw_last_x = boss.x
        boss._nxw_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Small hop bob (alert critter)
        bob = int(math.sin(boss.pulse * 0.8) * 3)
        tail_wag = math.sin(boss.pulse * 1.2) * 4
        _NS_nixweaver._draw_shadow(surface, x, y + 44)
        _NS_nixweaver._draw_body(surface, x, y + bob,
                        boss.direction, boss.pulse, "idle", tail_wag=tail_wag)
    def _draw_walk(surface, boss, x, y):
        # Hopping motion
        phase = boss.pulse * 2.0
        hop = int(abs(math.sin(phase * 1.2)) * 6)
        sway = int(math.sin(phase * 0.6) * 2)
        tail_wag = math.sin(phase * 1.5) * 5
        _NS_nixweaver._draw_shadow(surface, x + sway, y + 44, squish=hop)
        _NS_nixweaver._draw_body(surface, x + sway, y - hop,
                        boss.direction, phase, "walk", tail_wag=tail_wag)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_nxw_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        # Aim → fire → recoil recovery
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        if progress < 0.4:
            # Aim (crossbow raise)
            t = progress / 0.4
            recoil = 0
            bob = int(bob - t * 1)
        elif progress < 0.5:
            # Fire (small recoil)
            t = (progress - 0.4) / 0.1
            recoil = -int(t * 3) * boss.direction
        else:
            # Recovery
            t = (progress - 0.5) / 0.5
            recoil = int(-3 * (1 - t)) * boss.direction
        tail_wag = math.sin(boss.pulse * 1.0) * 3
        _NS_nixweaver._draw_shadow(surface, x + recoil, y + 44)
        _NS_nixweaver._draw_body(surface, x + recoil, y + bob,
                        boss.direction, boss.pulse, "attack",
                        attack_progress=progress, tail_wag=tail_wag)
        _NS_nixweaver._draw_crossbow_bolt(surface, boss, x + recoil, y + bob, progress)
    def _draw_channel_pose(surface, boss, x, y, skill_timer, pulse):
        """Standing still, channeling R Piercebolt."""
        tail_wag = math.sin(pulse * 0.8) * 2
        _NS_nixweaver._draw_shadow(surface, x, y + 44)
        _NS_nixweaver._draw_body(surface, x, y, boss.direction, pulse, "attack",
                        attack_progress=0.35, tail_wag=tail_wag)
    # ============================================================
    # BODY - Small furry critter with hood + crossbow
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action,
                   attack_progress=0.0, tail_wag=0):
        """Draw body: tail behind, body, head+hood, arms holding crossbow."""
        # Big fluffy tail behind
        _NS_nixweaver._draw_fluffy_tail(surface, cx, cy, facing, phase, tail_wag)
        # Legs
        _NS_nixweaver._draw_legs(surface, cx, cy, facing, phase, action)
        # Torso with cloak
        _NS_nixweaver._draw_torso_cloak(surface, cx, cy, facing, phase)
        # Head with hood
        _NS_nixweaver._draw_head_hood(surface, cx, cy - 18, facing, phase, action)
        # Arms + crossbow
        _NS_nixweaver._draw_arms_crossbow(surface, cx, cy, facing, phase, action,
                                          attack_progress)
    def _draw_fluffy_tail(surface, cx, cy, facing, phase, wag):
        """Big fluffy squirrel tail curving up behind."""
        back = -facing
        base_x = cx + back * 8
        base_y = cy + 4
        # Tail curves up and forward (over head arc)
        # Use bezier-like path
        segments = 6
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            # Path: back → up → curl forward slightly
            angle_along = math.pi * 0.6 * t  # from 0 to 108deg
            radius = 16
            offset_x = int(back * (2 + t * 6))
            offset_y = -int(math.sin(angle_along) * radius) - int(t * 2)
            offset_x += int(wag * (1 - t) * 0.3)
            points.append((base_x + offset_x, base_y + offset_y))
        # Draw tail as puffy segments (thick)
        for i in range(len(points) - 1):
            thickness = max(6, 14 - i)
            # Shadow
            _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                    (points[i][0] + 2, points[i][1] + 2),
                    (points[i + 1][0] + 2, points[i + 1][1] + 2),
                    thickness + 1)
            # Base fur
            _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["fur_darkest"],
                    points[i], points[i + 1], thickness)
            _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["fur_dark"],
                    points[i], points[i + 1], max(1, thickness - 2))
            _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["fur_mid"],
                    (points[i][0] - 1, points[i][1] - 1),
                    (points[i + 1][0] - 1, points[i + 1][1] - 1),
                    max(1, thickness - 5))
            _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["fur_light"],
                    (points[i][0] - 2, points[i][1] - 2),
                    (points[i + 1][0] - 2, points[i + 1][1] - 2),
                    max(1, thickness - 8))
        # Puff tip (white/light)
        tip = points[-1]
        _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["fur_darkest"], (tip[0] + 2, tip[1] + 2), 7)
        _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["fur_dark"], tip, 7)
        _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["fur_mid"], tip, 5)
        _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["fur_light"], (tip[0] - 1, tip[1] - 1), 3)
        _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["fur_shine"], (tip[0] - 1, tip[1] - 2), 2)
        # Fur texture strokes on tail
        for i in range(3, len(points) - 1):
            p = points[i]
            for j in range(2):
                fx = p[0] + int(math.sin(phase + i + j) * 4)
                fy = p[1] + int(math.cos(phase + i + j) * 3) - 3
                pygame.draw.line(surface, _NS_nixweaver.PALETTE["fur_darkest"],
                                 (fx, fy), (fx + 1, fy - 2), 1)
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Small feet."""
        # Feet positions
        step_offset = 0
        if action == "walk":
            step_offset = math.sin(phase * 2) * 2
        # Back foot
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                            (cx - 6 - facing * 2 + 1, cy + 14 + 1, 8, 5))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["fur_darkest"],
                            (cx - 6 - facing * 2, cy + 14, 8, 5))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["fur_dark"],
                            (cx - 5 - facing * 2, cy + 14, 6, 3))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["fur_mid"],
                            (cx - 5 - facing * 2, cy + 14, 5, 2))
        # Front foot
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                            (cx - 2 + facing * 4 + 1, cy + 14 + int(step_offset) + 1, 8, 5))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["fur_darkest"],
                            (cx - 2 + facing * 4, cy + 14 + int(step_offset), 8, 5))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["fur_dark"],
                            (cx - 1 + facing * 4, cy + 14 + int(step_offset), 6, 3))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["fur_mid"],
                            (cx - 1 + facing * 4, cy + 14 + int(step_offset), 5, 2))
    def _draw_torso_cloak(surface, cx, cy, facing, phase):
        """Small torso covered by green cloak."""
        # Torso shape (small rounded)
        torso_shape = [
            (cx - 8, cy - 4),
            (cx - 10, cy),
            (cx - 9, cy + 8),
            (cx - 5, cy + 14),
            (cx + 5, cy + 14),
            (cx + 9, cy + 8),
            (cx + 10, cy),
            (cx + 8, cy - 4),
        ]
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_shape])
        # Fur base
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_darkest"], torso_shape)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_dark"], [
            (cx - 7, cy - 3), (cx - 9, cy),
            (cx - 8, cy + 7), (cx - 4, cy + 13),
            (cx + 4, cy + 13), (cx + 8, cy + 7),
            (cx + 9, cy), (cx + 7, cy - 3),
        ])
        # White belly (chest fluff)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["belly_dark"], [
            (cx - 4, cy + 2), (cx - 5, cy + 6),
            (cx - 3, cy + 12), (cx + 3, cy + 12),
            (cx + 5, cy + 6), (cx + 4, cy + 2),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["belly_mid"], [
            (cx - 3, cy + 3), (cx - 4, cy + 6),
            (cx - 2, cy + 11), (cx + 2, cy + 11),
            (cx + 4, cy + 6), (cx + 3, cy + 3),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["belly_light"], [
            (cx - 2, cy + 5), (cx - 2, cy + 9),
            (cx + 2, cy + 9), (cx + 2, cy + 5),
        ])
        # GREEN CLOAK (over shoulders, flowing back)
        cloak_sway = math.sin(phase * 0.6) * 2
        back = -facing
        # Cloak main body
        cloak_shape = [
            (cx - 10, cy - 3),
            (cx - 11, cy + 2),
            (cx - 10 + int(back * 3 + cloak_sway), cy + 8),
            (cx - 8 + int(back * 4 + cloak_sway), cy + 14),
            (cx - 5 + int(back * 3 + cloak_sway), cy + 16),
            (cx + 5, cy + 14),
            (cx + 10, cy + 4),
            (cx + 10, cy - 3),
            (cx + 6, cy - 5),
            (cx - 6, cy - 5),
        ]
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_darkest"], cloak_shape)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_dark"], [
            (cx - 9, cy - 2), (cx - 10, cy + 2),
            (cx - 9 + int(back * 2 + cloak_sway * 0.5), cy + 8),
            (cx - 7 + int(back * 3 + cloak_sway * 0.5), cy + 13),
            (cx + 5, cy + 13),
            (cx + 9, cy + 4),
            (cx + 9, cy - 2),
            (cx + 5, cy - 4),
            (cx - 5, cy - 4),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_mid"], [
            (cx - 8, cy - 1), (cx - 9, cy + 2),
            (cx - 8, cy + 8), (cx + 5, cy + 8),
            (cx + 8, cy + 3), (cx + 8, cy - 1),
            (cx + 4, cy - 3), (cx - 4, cy - 3),
        ])
        # Highlight on shoulder
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_light"], [
            (cx - 6, cy - 2), (cx + 6, cy - 2),
            (cx + 5, cy), (cx - 5, cy),
        ])
        # Gold belt/trim at waist
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["gold_dark"],
                         (cx - 8, cy + 10), (cx + 8, cy + 10), 2)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["gold_mid"],
                         (cx - 8, cy + 10), (cx + 8, cy + 10), 1)
        # Belt buckle
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["gold_dark"],
                         (cx - 2, cy + 9, 4, 3))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["gold_light"],
                         (cx - 1, cy + 10, 2, 1))
    def _draw_head_hood(surface, cx, cy, facing, phase, action):
        """Cute critter face inside green hood."""
        # HOOD (large peaked hood covering top of head)
        hood_shape = [
            (cx - 11, cy + 4),      # bottom left
            (cx - 12, cy - 2),
            (cx - 10, cy - 8),
            (cx - 5, cy - 12),
            (cx + facing * 3, cy - 14),   # peak (tilted forward)
            (cx + 8, cy - 10),
            (cx + 11, cy - 4),
            (cx + 12, cy + 2),
            (cx + 10, cy + 6),
        ]
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in hood_shape])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_darkest"], hood_shape)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_dark"], [
            (cx - 10, cy + 3), (cx - 11, cy - 2),
            (cx - 9, cy - 7), (cx - 4, cy - 11),
            (cx + facing * 3, cy - 13),
            (cx + 7, cy - 9), (cx + 10, cy - 4),
            (cx + 11, cy + 2), (cx + 9, cy + 5),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_mid"], [
            (cx - 9, cy + 1), (cx - 10, cy - 2),
            (cx - 8, cy - 6), (cx - 3, cy - 10),
            (cx + facing * 3, cy - 12),
            (cx + 6, cy - 8), (cx + 9, cy - 4),
            (cx + 10, cy + 1),
        ])
        # Hood highlight
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["hood_light"], [
            (cx - 6, cy - 8), (cx - 2, cy - 10),
            (cx + facing * 2, cy - 11), (cx + 3, cy - 9),
            (cx - 4, cy - 7),
        ])
        # Two feathers on hood (like reference)
        feather_sway = math.sin(phase * 0.5) * 2
        for i, (fx, fy, angle) in enumerate([
            (cx - 4 + facing * 2, cy - 12, -math.pi * 0.7),
            (cx - 2 + facing * 2, cy - 13, -math.pi * 0.55),
        ]):
            tip_x = fx + int(math.cos(angle) * 8) * facing
            tip_y = fy + int(math.sin(angle) * 8) + int(feather_sway)
            # Feather stem
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_dark"],
                             (fx, fy), (tip_x, tip_y), 1)
            # Feather body
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["belly_mid"],
                             (fx, fy), (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["belly_light"],
                             (fx, fy), (tip_x, tip_y), 1)
        # FACE inside hood
        # Face shape (round, fluffy fur)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_darkest"], [
            (cx - 8, cy + 4), (cx - 9, cy),
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 9, cy), (cx + 8, cy + 4),
            (cx + 5, cy + 7), (cx - 5, cy + 7),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_dark"], [
            (cx - 7, cy + 3), (cx - 8, cy),
            (cx - 5, cy - 3), (cx + 5, cy - 3),
            (cx + 8, cy), (cx + 7, cy + 3),
            (cx + 4, cy + 6), (cx - 4, cy + 6),
        ])
        # Face highlight (cheeks)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_mid"], [
            (cx - 5, cy - 1), (cx - 6, cy + 2),
            (cx - 3, cy + 5), (cx + 3, cy + 5),
            (cx + 6, cy + 2), (cx + 5, cy - 1),
        ])
        # White muzzle (bottom face)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["belly_dark"], [
            (cx - 3, cy + 3), (cx - 4, cy + 5),
            (cx - 2, cy + 7), (cx + 2, cy + 7),
            (cx + 4, cy + 5), (cx + 3, cy + 3),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["belly_light"], [
            (cx - 2, cy + 4), (cx - 3, cy + 5),
            (cx - 1, cy + 6), (cx + 1, cy + 6),
            (cx + 3, cy + 5), (cx + 2, cy + 4),
        ])
        # EARS peeking out of hood (small triangles)
        for side in (-1, 1):
            ear_x = cx + side * 7
            ear_y = cy - 5
            _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_darkest"], [
                (ear_x - 2, ear_y + 2),
                (ear_x + side, ear_y - 3),
                (ear_x + 2, ear_y + 2),
            ])
            _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["fur_dark"], [
                (ear_x - 1, ear_y + 1),
                (ear_x + side, ear_y - 2),
                (ear_x + 1, ear_y + 1),
            ])
            # Inner ear pink
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["nose_dark"],
                             (ear_x, ear_y - 1, 1, 2))
        # EYES (big black cute eyes)
        for eye_x in (cx - 3, cx + 3):
            # Eye base (large dark)
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                             (eye_x - 2, cy - 1, 4, 4))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["eye_mid"],
                             (eye_x - 1, cy + 1, 3, 1))
            # Shine
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["eye_shine"],
                             (eye_x, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["white"],
                             (eye_x, cy - 1, 1, 1))
        # NOSE (small pink)
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["nose_dark"],
                         (cx, cy + 3, 2, 1))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["nose_light"],
                         (cx, cy + 3, 1, 1))
        # Mouth (small smirk)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
        if action != "attack":
            # Small fang peeking
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["belly_light"],
                             (cx + 1, cy + 5, 1, 1))
    def _draw_arms_crossbow(surface, cx, cy, facing, phase, action, attack_progress):
        """Arms holding crossbow horizontally."""
        # Crossbow position depends on action
        if action == "attack":
            # Raised for aim
            if attack_progress < 0.4:
                # Raising
                t = attack_progress / 0.4
                bow_y_off = -int(t * 2)
                bow_forward = int(t * 2) * facing
            elif attack_progress < 0.5:
                # Fire recoil
                t = (attack_progress - 0.4) / 0.1
                bow_y_off = -2
                bow_forward = int(2 - t * 3) * facing
            else:
                # Recovery
                t = (attack_progress - 0.5) / 0.5
                bow_y_off = -int(2 * (1 - t))
                bow_forward = int(-1 + t * 1) * facing
        else:
            bow_y_off = 0
            bow_forward = 0
        # Body center for arms
        arm_center_x = cx
        arm_center_y = cy + 2 + bow_y_off
        # CROSSBOW body (horizontal wooden stock)
        bow_cx = arm_center_x + facing * 10 + bow_forward
        bow_cy = arm_center_y
        # Stock (main wooden body)
        _NS_nixweaver._draw_crossbow(surface, bow_cx, bow_cy, facing, phase, action,
                                     attack_progress)
        # ARMS holding crossbow
        # Back arm (holding grip)
        shoulder_back_x = cx - facing * 2
        shoulder_back_y = cy - 1
        grip_x = bow_cx - facing * 4
        grip_y = bow_cy + 1
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                (shoulder_back_x + 1, shoulder_back_y + 1),
                (grip_x + 1, grip_y + 1), 5)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["hood_darkest"],
                (shoulder_back_x, shoulder_back_y), (grip_x, grip_y), 4)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["hood_dark"],
                (shoulder_back_x, shoulder_back_y), (grip_x, grip_y), 2)
        # Paw at grip
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["fur_darkest"],
                         (grip_x - 2, grip_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["fur_mid"],
                         (grip_x - 1, grip_y - 1, 3, 2))
        # Front arm (support)
        shoulder_front_x = cx + facing * 4
        shoulder_front_y = cy - 1
        support_x = bow_cx + facing * 2
        support_y = bow_cy + 2
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                (shoulder_front_x + 1, shoulder_front_y + 1),
                (support_x + 1, support_y + 1), 5)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["hood_darkest"],
                (shoulder_front_x, shoulder_front_y), (support_x, support_y), 4)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["hood_dark"],
                (shoulder_front_x, shoulder_front_y), (support_x, support_y), 2)
        # Paw supporting
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["fur_darkest"],
                         (support_x - 2, support_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["fur_mid"],
                         (support_x - 1, support_y - 1, 3, 2))
    def _draw_crossbow(surface, cx, cy, facing, phase, action, attack_progress):
        """Wooden crossbow horizontal."""
        # STOCK (wooden main body)
        stock_len = 14
        stock_x1 = cx - facing * 4
        stock_x2 = cx + facing * stock_len
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                (stock_x1 + 1, cy + 2), (stock_x2 + 1, cy + 2), 5)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["wood_dark"],
                (stock_x1, cy + 1), (stock_x2, cy + 1), 4)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["wood_mid"],
                (stock_x1, cy), (stock_x2, cy), 2)
        _NS_nixweaver._aaline(surface, _NS_nixweaver.PALETTE["wood_light"],
                (stock_x1, cy - 1), (stock_x2, cy - 1), 1)
        # BOW LIMBS (curved on top of stock, vertical)
        bow_x = cx + facing * 8
        # Upper limb
        limb_upper = [
            (bow_x - 1, cy - 8),
            (bow_x + facing * 2, cy - 6),
            (bow_x + facing * 3, cy - 3),
            (bow_x, cy),
        ]
        for i in range(len(limb_upper) - 1):
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_dark"],
                             limb_upper[i], limb_upper[i + 1], 3)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_mid"],
                             limb_upper[i], limb_upper[i + 1], 2)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_light"],
                             (limb_upper[i][0] - 1, limb_upper[i][1] - 1),
                             (limb_upper[i + 1][0] - 1, limb_upper[i + 1][1] - 1), 1)
        # Lower limb (mirror)
        limb_lower = [
            (bow_x - 1, cy + 8),
            (bow_x + facing * 2, cy + 6),
            (bow_x + facing * 3, cy + 3),
            (bow_x, cy),
        ]
        for i in range(len(limb_lower) - 1):
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_dark"],
                             limb_lower[i], limb_lower[i + 1], 3)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_mid"],
                             limb_lower[i], limb_lower[i + 1], 2)
        # BOWSTRING (taut when aiming, slack after fire)
        string_tension = 1.0
        if action == "attack" and 0.4 < attack_progress < 0.55:
            # Just fired, string vibrates
            string_tension = 0.3
        string_top = (bow_x - 1, cy - 8)
        string_bot = (bow_x - 1, cy + 8)
        if string_tension < 1:
            # Vibrating (S-shape)
            wobble = math.sin(phase * 20) * 2
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["metal_light"],
                             string_top,
                             (bow_x - 1 - facing * 2 + int(wobble), cy), 1)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["metal_light"],
                             (bow_x - 1 - facing * 2 + int(wobble), cy),
                             string_bot, 1)
        else:
            # Straight taut string, pulled back
            pull_back = -facing * 3 if action == "attack" and attack_progress < 0.4 else 0
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["metal_dark"],
                             string_top,
                             (bow_x - 1 + pull_back, cy), 1)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["metal_light"],
                             (bow_x - 1 + pull_back, cy),
                             string_bot, 1)
        # LOADED BOLT (visible on top of stock when aiming)
        if action != "attack" or attack_progress < 0.4:
            bolt_x1 = cx + facing * 2
            bolt_x2 = cx + facing * 12
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_dark"],
                             (bolt_x1, cy - 2), (bolt_x2, cy - 2), 2)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_light"],
                             (bolt_x1, cy - 2), (bolt_x2, cy - 2), 1)
            # Bolt tip
            tip_x = bolt_x2 + facing * 2
            _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["metal_dark"], [
                (bolt_x2, cy - 3),
                (tip_x, cy - 2),
                (bolt_x2, cy - 1),
            ])
            _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["metal_light"], [
                (bolt_x2, cy - 3),
                (tip_x - facing, cy - 2),
                (bolt_x2, cy - 2),
            ])
            # Fletching
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["leaf_mid"],
                             (bolt_x1 - facing * 2, cy - 3, 2, 3))
        # Gold trigger/decoration on stock
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["gold_dark"],
                         (cx - facing * 2, cy + 2, 3, 2))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["gold_light"],
                         (cx - facing * 2, cy + 2, 2, 1))
    # ============================================================
    # AUTO-ATTACK - CROSSBOW BOLT PROJECTILE
    # ============================================================
    def _draw_crossbow_bolt(surface, boss, x, y, progress):
        """Bolt flying through the air."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_nixweaver._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y + 2
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Angle of bolt
        angle = math.atan2(ty - start_y, tx - start_x)
        bolt_len = 12
        # Bolt tail position
        tail_x = bx - int(math.cos(angle) * bolt_len)
        tail_y = by - int(math.sin(angle) * bolt_len)
        # Trail (motion blur behind)
        for i in range(6):
            trail_t = max(0.0, t - i * 0.05)
            tx_pos = int(start_x + (tx - start_x) * trail_t)
            ty_pos = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nixweaver._alpha(200 - i * 30)
            trail_tail_x = tx_pos - int(math.cos(angle) * bolt_len)
            trail_tail_y = ty_pos - int(math.sin(angle) * bolt_len)
            pygame.draw.line(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha),
                             (trail_tail_x, trail_tail_y), (tx_pos, ty_pos), 1)
        # Bolt shaft
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                         (tail_x + 1, tail_y + 1), (bx + 1, by + 1), 3)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_dark"],
                         (tail_x, tail_y), (bx, by), 2)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["wood_light"],
                         (tail_x, tail_y), (bx, by), 1)
        # Metal tip (with glow)
        for r in range(4, 0, -1):
            alpha = _NS_nixweaver._alpha(100 * (4 - r) / 4)
            _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha),
                                    (bx, by), r)
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["metal_dark"], [
            (bx - int(math.cos(angle - 0.5) * 3), by - int(math.sin(angle - 0.5) * 3)),
            (bx + int(math.cos(angle) * 3), by + int(math.sin(angle) * 3)),
            (bx - int(math.cos(angle + 0.5) * 3), by - int(math.sin(angle + 0.5) * 3)),
        ])
        _NS_nixweaver._poly(surface, _NS_nixweaver.PALETTE["metal_light"], [
            (bx - int(math.cos(angle - 0.5) * 2), by - int(math.sin(angle - 0.5) * 2)),
            (bx + int(math.cos(angle) * 2), by + int(math.sin(angle) * 2)),
            (bx - int(math.cos(angle + 0.5) * 2), by - int(math.sin(angle + 0.5) * 2)),
        ])
        # Fletching at tail (green feathers)
        perp = angle + math.pi / 2
        fl_a = (tail_x + int(math.cos(perp) * 2), tail_y + int(math.sin(perp) * 2))
        fl_b = (tail_x - int(math.cos(perp) * 2), tail_y - int(math.sin(perp) * 2))
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["leaf_dark"],
                         tail_x_pos_offset := (tail_x - int(math.cos(angle) * 2),
                                                tail_y - int(math.sin(angle) * 2)),
                         fl_a, 2)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["leaf_mid"],
                         tail_x_pos_offset, fl_a, 1)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["leaf_dark"],
                         tail_x_pos_offset, fl_b, 2)
        pygame.draw.line(surface, _NS_nixweaver.PALETTE["leaf_mid"],
                         tail_x_pos_offset, fl_b, 1)
        # Impact sparks
        if t > 0.9:
            st = (t - 0.9) / 0.1
            for i in range(8):
                spark_angle = i * math.pi / 4
                sr = int(6 + st * 12)
                sx = tx + int(math.cos(spark_angle) * sr)
                sy = ty + int(math.sin(spark_angle) * sr)
                alpha = _NS_nixweaver._alpha(240 * (1 - st))
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_shine"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, squish=0):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        w = 80 - squish
        h = max(2, 8 - squish // 2)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (5, 15, 5, 170), (10, 8, w, h))
        pygame.draw.ellipse(shadow, (20, 40, 15, 100), (14, 10, w - 8, max(2, h - 4)))
        surface.blit(shadow, (x - 50, y - 12))
    def _draw_forest_aura(surface, x, y, phase):
        """Soft green forest aura."""
        pulse = math.sin(phase * 0.4) * 0.2 + 0.8
        aura = pygame.Surface((180, 150), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = _NS_nixweaver._alpha((70 - radius) * 0.9 * pulse)
            if alpha > 0:
                _NS_nixweaver._aacircle(aura, (*_NS_nixweaver.PALETTE["leaf_dark"], alpha),
                                        (90, 75), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_nixweaver._alpha((45 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nixweaver._aacircle(aura, (*_NS_nixweaver.PALETTE["leaf_mid"], alpha),
                                        (90, 75), radius)
        surface.blit(aura, (x - 90, y - 75))
        # Floating leaves
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            radius = 40 + int(math.sin(phase + i) * 10)
            lx = x + int(math.cos(angle) * radius)
            ly = y - 5 + int(math.sin(angle) * radius * 0.4)
            # Leaf shape (small)
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["leaf_dark"], (lx, ly, 2, 1))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["leaf_mid"], (lx, ly, 1, 1))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["leaf_light"], (lx, ly, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.0) * 0.2 + 0.8
        ring = pygame.Surface((140, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nixweaver.PALETTE["leaf_dark"], 200),
                            (5, 12, 130, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_nixweaver.PALETTE["hood_dark"], 180),
                            (12, 14, 116, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_nixweaver.PALETTE["leaf_mid"], 150),
                            (22, 16, 96, 12), 1)
        # Small runes
        for i in range(8):
            angle = phase * 0.25 + i * math.pi / 4
            x1 = 70 + int(math.cos(angle) * 40)
            y1 = 22 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 58)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_nixweaver.PALETTE["leaf_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_nixweaver.PALETTE["amber_hot"],
                                       _NS_nixweaver._alpha(150 * pulse)),
                                (10, 8, 120, 28), 1)
        surface.blit(ring, (x - 70, y - 20))
    # ============================================================
    # SKILL Q - THORNSHOT (bouncing acorn)
    # ============================================================
    def _draw_thornshot_skill(surface, boss, x, y, timer, phase):
        """Big glowing acorn bouncing between targets."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nixweaver._target_position(boss, x, y)
        if progress < 0.2:
            # Charge on bolt tip
            t = progress / 0.2
            hand_x = x + facing * 22
            hand_y = y
            cr = int(3 + t * 5)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_nixweaver._alpha(180 * (cr + 4 - r) / (cr + 4))
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_mid"], (hand_x, hand_y), cr - 1)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_light"], (hand_x, hand_y), max(1, cr - 3))
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_shine"], (hand_x, hand_y), 1)
            return
        # Flight with bounce arc
        t = (progress - 0.2) / 0.8
        t = min(1.0, t)
        start_x = x + facing * 24
        start_y = y
        # Multiple bounces (3 arcs)
        num_bounces = 3
        bounce_t = t * num_bounces
        current_bounce = int(bounce_t)
        local_t = bounce_t - current_bounce
        # Interpolate through bounces
        # Bounce points: from start, alternating overshoot
        bounce_targets = [
            (tx, ty),
            (tx + 60, ty - 20),
            (tx + 30, ty + 20),
            (tx + 90, ty),
        ]
        if current_bounce >= len(bounce_targets) - 1:
            current_bounce = len(bounce_targets) - 2
            local_t = 1.0
        seg_start = (start_x, start_y) if current_bounce == 0 else bounce_targets[current_bounce - 1]
        seg_end = bounce_targets[current_bounce]
        # Arc trajectory
        bx = int(seg_start[0] + (seg_end[0] - seg_start[0]) * local_t)
        arc_height = 25
        by = int(seg_start[1] + (seg_end[1] - seg_start[1]) * local_t
                 - math.sin(local_t * math.pi) * arc_height)
        # Trail of small acorns
        for i in range(8):
            trail_t = max(0.0, t - i * 0.04)
            if trail_t <= 0:
                continue
            trail_bounce_t = trail_t * num_bounces
            trail_bounce = int(trail_bounce_t)
            trail_local = trail_bounce_t - trail_bounce
            if trail_bounce >= len(bounce_targets) - 1:
                continue
            ts = (start_x, start_y) if trail_bounce == 0 else bounce_targets[trail_bounce - 1]
            te = bounce_targets[trail_bounce]
            px = int(ts[0] + (te[0] - ts[0]) * trail_local)
            py = int(ts[1] + (te[1] - ts[1]) * trail_local
                     - math.sin(trail_local * math.pi) * arc_height)
            alpha = _NS_nixweaver._alpha(200 - i * 25)
            size = max(1, 6 - i)
            _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_dark"], alpha), (px, py), size)
            _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_mid"], alpha), (px, py), max(1, size - 1))
            _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha), (px, py), max(1, size - 3))
        # Big acorn projectile
        _NS_nixweaver._draw_acorn(surface, bx, by, phase)
    def _draw_acorn(surface, cx, cy, phase):
        """Glowing acorn (nut shape)."""
        # Glow halo
        for r in range(10, 3, -1):
            alpha = _NS_nixweaver._alpha(80 * (10 - r) / 10)
            _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha), (cx, cy), r)
        # Acorn nut body (oval)
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                            (cx - 4, cy - 3, 8, 8))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["amber_darkest"],
                            (cx - 4, cy - 4, 8, 8))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["amber_dark"],
                            (cx - 3, cy - 3, 6, 6))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["amber_mid"],
                            (cx - 3, cy - 3, 5, 5))
        pygame.draw.ellipse(surface, _NS_nixweaver.PALETTE["amber_light"],
                            (cx - 2, cy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["amber_shine"], (cx - 1, cy - 2, 1, 1))
        # Cap (top brown)
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["wood_dark"], (cx - 4, cy - 5, 8, 3))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["wood_mid"], (cx - 3, cy - 5, 6, 2))
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["wood_light"], (cx - 2, cy - 5, 4, 1))
        # Stem
        pygame.draw.rect(surface, _NS_nixweaver.PALETTE["wood_dark"], (cx, cy - 7, 1, 2))
    # ============================================================
    # SKILL W - THICKET SNARE (plant bush)
    # ============================================================
    def _draw_thicket_ground(surface, boss, x, y, timer, phase):
        """Ground planting circle."""
        tx, ty = _NS_nixweaver._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growing circle base
        r = int(30 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_nixweaver.PALETTE["leaf_dark"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_nixweaver.PALETTE["hood_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_thicket_foreground(surface, boss, x, y, timer, phase):
        """Bush growing at target."""
        tx, ty = _NS_nixweaver._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growth scale
        scale = min(1.0, progress * 2)
        # Central bush cluster
        # Multiple leaf clumps
        clump_positions = [
            (0, 0, 12),
            (-8, 2, 8), (8, 2, 8),
            (-4, -4, 9), (4, -4, 9),
            (-12, 4, 6), (12, 4, 6),
            (0, -8, 8),
        ]
        for i, (ox, oy, size) in enumerate(clump_positions):
            scaled_size = int(size * scale)
            if scaled_size < 2:
                continue
            sway = math.sin(phase * 0.8 + i) * 1
            bx = tx + ox + int(sway)
            by = ty + oy - int(scaled_size * 0.3)
            # Leaf clump (rounded)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["shadow_deep"],
                                    (bx + 1, by + 1), scaled_size)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["leaf_dark"], (bx, by), scaled_size)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["hood_dark"], (bx, by), max(1, scaled_size - 1))
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["leaf_mid"],
                                    (bx - 1, by - 1), max(1, scaled_size - 3))
            # Highlights
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["leaf_light"],
                                    (bx - 1, by - 2), max(1, scaled_size - 5))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["leaf_shine"], (bx - 1, by - 2, 1, 1))
        # Glowing amber berries hidden in bush
        if scale > 0.7:
            for i in range(5):
                angle = i * math.pi * 2 / 5 + phase * 0.3
                brry_x = tx + int(math.cos(angle) * 8)
                brry_y = ty + int(math.sin(angle) * 4) - 3
                _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_mid"], (brry_x, brry_y), 2)
                _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_light"], (brry_x, brry_y), 1)
                pygame.draw.rect(surface, _NS_nixweaver.PALETTE["amber_shine"], (brry_x, brry_y, 1, 1))
        # Silence sparkles rising
        for i in range(6):
            spk_t = (phase * 0.6 + i * 0.15) % 1.0
            sx = tx + int(math.sin(phase + i) * 12)
            sy = ty - int(spk_t * 20)
            alpha = _NS_nixweaver._alpha(200 * (1 - spk_t) * scale)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["leaf_light"], alpha), (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_shine"], alpha), (sx, sy - 1, 1, 1))
    # ============================================================
    # SKILL E - GROVE DASH (dash trail)
    # ============================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Paw prints trail."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Paw prints behind
        for i in range(6):
            dist = i * 18
            px = x - facing * dist
            py = y + 44
            alpha = _NS_nixweaver._alpha(200 * (1 - i / 6) * (1 - progress * 0.5))
            # Paw shape
            pygame.draw.ellipse(surface, (*_NS_nixweaver.PALETTE["leaf_dark"], alpha),
                                (px - 3, py - 1, 6, 4))
            pygame.draw.ellipse(surface, (*_NS_nixweaver.PALETTE["leaf_mid"], alpha),
                                (px - 2, py - 1, 4, 3))
            # Small toes
            for tox in (-2, 0, 2):
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["leaf_mid"], alpha),
                                 (px + tox, py - 2, 1, 1))
    def _draw_dash_foreground(surface, boss, x, y, timer, phase):
        """Leaf/wind trail behind boss."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Wind streaks behind
        for i in range(8):
            streak_x = x - facing * (10 + i * 12)
            streak_y = y + int(math.sin(phase * 4 + i) * 6)
            alpha = _NS_nixweaver._alpha(220 * (1 - i / 8))
            length = 12 - i
            pygame.draw.line(surface, (*_NS_nixweaver.PALETTE["leaf_light"], alpha),
                             (streak_x, streak_y),
                             (streak_x + facing * length, streak_y), 2)
            pygame.draw.line(surface, (*_NS_nixweaver.PALETTE["leaf_shine"], alpha),
                             (streak_x, streak_y),
                             (streak_x + facing * length, streak_y), 1)
        # Flying leaves
        for i in range(10):
            leaf_t = (phase * 1.5 + i * 0.1) % 1.0
            lx = x - facing * int(leaf_t * 80)
            ly = y - 5 + int(math.sin(phase * 3 + i) * 10)
            alpha = _NS_nixweaver._alpha(240 * (1 - leaf_t))
            pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["leaf_dark"], alpha), (lx, ly, 2, 2))
            pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["leaf_mid"], alpha), (lx, ly, 1, 1))
            pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["leaf_shine"], alpha), (lx, ly, 1, 1))
        # Speed lines
        for i in range(3):
            line_y = y - 4 + i * 6
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["leaf_light"],
                             (x - facing * 30, line_y),
                             (x - facing * 15, line_y), 1)
            pygame.draw.line(surface, _NS_nixweaver.PALETTE["leaf_shine"],
                             (x - facing * 25, line_y),
                             (x - facing * 18, line_y), 1)
    # ============================================================
    # SKILL R - PIERCEBOLT (massive channeled shot)
    # ============================================================
    def _draw_piercebolt_skill(surface, boss, x, y, timer, phase):
        """Massive charged shot from crossbow."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nixweaver._target_position(boss, x, y)
        if progress < 0.5:
            # CHANNELING phase - energy building on crossbow tip
            t = progress / 0.5
            tip_x = x + facing * 26
            tip_y = y
            # Growing energy orb
            cr = int(3 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_nixweaver._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_darkest"], alpha),
                                        (tip_x, tip_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_nixweaver._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_dark"], alpha),
                                        (tip_x, tip_y), r)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_mid"], (tip_x, tip_y), cr - 2)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_light"], (tip_x, tip_y), max(1, cr - 5))
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_shine"], (tip_x, tip_y), max(1, cr - 8))
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["white"], (tip_x, tip_y, 1, 1))
            # Energy particles being drawn in
            for i in range(10):
                pull_t = ((phase * 2 + i * 0.1) % 1.0)
                angle = i * math.pi * 2 / 10
                orbit_r = int(25 * (1 - pull_t))
                px = tip_x + int(math.cos(angle) * orbit_r)
                py = tip_y + int(math.sin(angle) * orbit_r)
                alpha = _NS_nixweaver._alpha(240 * (1 - pull_t * 0.5))
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_hot"], alpha), (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_shine"], alpha), (px, py, 1, 1))
            # Warning line to target (aim laser)
            if t > 0.3:
                laser_alpha = _NS_nixweaver._alpha(150 * (t - 0.3) / 0.7)
                pygame.draw.line(surface, (*_NS_nixweaver.PALETTE["amber_hot"], laser_alpha),
                                 (tip_x, tip_y), (tx, ty), 1)
                # Target reticle
                for r in range(8, 3, -1):
                    a = _NS_nixweaver._alpha(180 * (8 - r) / 8 * (t - 0.3) / 0.7)
                    _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_hot"], a),
                                            (tx, ty), r, 1)
        elif progress < 0.75:
            # FIRE phase - massive bolt flies
            t = (progress - 0.5) / 0.25
            start_x = x + facing * 26
            start_y = y
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            angle = math.atan2(ty - start_y, tx - start_x)
            # Massive beam trail (piercing effect)
            beam_width = int(6 * (1 - t * 0.5))
            for layer_i, (w, alpha_val) in enumerate([
                (beam_width + 6, 60),
                (beam_width + 4, 100),
                (beam_width + 2, 150),
                (beam_width, 200),
                (max(1, beam_width - 2), 240),
            ]):
                colors = [
                    _NS_nixweaver.PALETTE["amber_darkest"],
                    _NS_nixweaver.PALETTE["amber_dark"],
                    _NS_nixweaver.PALETTE["amber_mid"],
                    _NS_nixweaver.PALETTE["amber_light"],
                    _NS_nixweaver.PALETTE["amber_shine"],
                ]
                pygame.draw.line(surface, (*colors[min(layer_i, 4)], alpha_val),
                                 (start_x, start_y), (bx, by), w)
            # Huge bolt head
            for r in range(14, 3, -1):
                alpha = _NS_nixweaver._alpha(120 * (14 - r) / 14)
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha), (bx, by), r)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_darkest"], (bx, by), 10)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_dark"], (bx, by), 8)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_mid"], (bx, by), 5)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_light"], (bx, by), 3)
            _NS_nixweaver._aacircle(surface, _NS_nixweaver.PALETTE["amber_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_nixweaver.PALETTE["white"], (bx, by, 1, 1))
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 25)
                alpha = _NS_nixweaver._alpha(240 * (1 - st))
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_nixweaver._aacircle(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                # Big burst
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_nixweaver.PALETTE["amber_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_shine"], alpha),
                                     (ex, ey, 2, 2))
        else:
            # Aftermath sparkles
            t = (progress - 0.75) / 0.25
            for i in range(12):
                spark_t = (phase + i * 0.1) % 1.0
                sx = tx + int(math.sin(phase + i) * 20)
                sy = ty - int(spark_t * 25)
                alpha = _NS_nixweaver._alpha(200 * (1 - t) * (1 - spark_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_light"], alpha), (sx, sy, 1, 1))
                    pygame.draw.rect(surface, (*_NS_nixweaver.PALETTE["amber_shine"], alpha), (sx, sy, 1, 1))



# ====================================================================
# NYXRAAL (ABYSSAL PRINCE) - Mini Boss
# ====================================================================

class _NS_nyxraal:
    """Namespace nyxraal - abyssal prince boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale tan with dark tint)
        "skin_darkest": (45, 30, 40),
        "skin_dark": (105, 75, 90),
        "skin_mid": (170, 135, 145),
        "skin_light": (215, 185, 190),
        "skin_shine": (245, 220, 225),
        # White spiky hair (silver-white)
        "hair_darkest": (95, 90, 110),
        "hair_dark": (160, 155, 175),
        "hair_mid": (215, 210, 225),
        "hair_light": (245, 245, 250),
        "hair_shine": (255, 255, 255),
        # Dark armor (chest plates, shoulders)
        "armor_darkest": (12, 8, 20),
        "armor_dark": (35, 25, 55),
        "armor_mid": (75, 55, 105),
        "armor_light": (135, 105, 175),
        "armor_edge": (195, 165, 225),
        # Purple abyss (main FX color, energy, tattoos)
        "abyss_darkest": (20, 5, 40),
        "abyss_dark": (60, 15, 110),
        "abyss_mid": (135, 40, 200),
        "abyss_light": (200, 110, 250),
        "abyss_hot": (240, 190, 255),
        "abyss_shine": (255, 240, 255),
        # Purple eye (glowing)
        "eye_socket": (5, 2, 12),
        "eye_dark": (55, 15, 100),
        "eye_mid": (170, 60, 235),
        "eye_light": (235, 175, 255),
        "eye_glow": (255, 240, 255),
        # Steel sword blade
        "steel_darkest": (30, 30, 45),
        "steel_dark": (80, 78, 100),
        "steel_mid": (150, 145, 175),
        "steel_light": (215, 210, 230),
        "steel_shine": (250, 250, 255),
        # Chain (dark iron)
        "chain_darkest": (10, 8, 15),
        "chain_dark": (35, 30, 45),
        "chain_mid": (85, 78, 95),
        "chain_light": (155, 145, 170),
        # Belt/pants leather (dark violet)
        "leather_dark": (25, 15, 35),
        "leather_mid": (65, 40, 85),
        "leather_light": (110, 75, 135),
        # Mist purple
        "mist_dark": (30, 15, 55),
        "mist_mid": (85, 45, 135),
        "mist_light": (170, 110, 220),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxraal._clamp(color)
        if _NS_nyxraal.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxraal._clamp(color)
        if _NS_nyxraal.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxraal._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_nyxraal(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxraal._detect_moving(boss)
        _NS_nyxraal._update_nxr_attack_anim(boss)
        attacking = (
            getattr(boss, "_nxr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_nyxraal._draw_abyss_aura(surface, x, y, pulse)
        _NS_nyxraal._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Ambient chains (constant).
        _NS_nyxraal._draw_ambient_chains(surface, x, y, pulse)
        # Skill ground FX behind body.
        if active_skill == "e":
            _NS_nyxraal._draw_reaping_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxraal._draw_descent_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_nyxraal._draw_spectre_dash_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — during Q dash / R jump body position changes.
        q_dash_offset = 0
        r_jump_lift = 0
        body_visible = True
        if active_skill == "q":
            q_dur = 40
            q_prog = max(0.0, min(1.0, 1 - skill_timer / q_dur))
            # Dash forward and back to spawn point.
            if q_prog < 0.5:
                dash_t = q_prog / 0.5
                q_dash_offset = int(dash_t * 60) * boss.direction
        elif active_skill == "r":
            r_dur = 80
            r_prog = max(0.0, min(1.0, 1 - skill_timer / r_dur))
            # Jump up 0-0.5, slam down 0.5-0.7, land 0.7+.
            if r_prog < 0.5:
                jump_t = r_prog / 0.5
                r_jump_lift = int(math.sin(jump_t * math.pi) * 60)
            elif r_prog < 0.7:
                slam_t = (r_prog - 0.5) / 0.2
                r_jump_lift = int(60 * (1 - slam_t))
            else:
                r_jump_lift = 0
        if body_visible:
            if attacking:
                _NS_nyxraal._draw_nxr_attack(surface, boss, x + q_dash_offset, y - r_jump_lift)
            elif moving:
                _NS_nyxraal._draw_nxr_walk(surface, boss, x + q_dash_offset, y - r_jump_lift)
            else:
                _NS_nyxraal._draw_nxr_idle(surface, boss, x + q_dash_offset, y - r_jump_lift)
        # Foreground FX.
        if active_skill == "q":
            _NS_nyxraal._draw_spectre_step_trail(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxraal._draw_abyss_pull_chain(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxraal._draw_reaping_whirl(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxraal._draw_abyss_descent(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_nxr_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nxr_previous_timer", 0))
        active = bool(getattr(boss, "_nxr_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._nxr_attack_active = True
            boss._nxr_attack_frame = 0
            active = True
        elif active:
            boss._nxr_attack_frame = int(getattr(boss, "_nxr_attack_frame", 0)) + 1
            if boss._nxr_attack_frame >= cooldown:
                boss._nxr_attack_active = False
                boss._nxr_attack_frame = 0
                active = False
        boss._nxr_previous_timer = timer
        boss._nxr_attack_progress = (
            min(1.0, getattr(boss, "_nxr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nxr_last_x"):
            boss._nxr_last_x = boss.x
            boss._nxr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nxr_last_x)
        dy = abs(boss.y - boss._nxr_last_y)
        boss._nxr_last_x = boss.x
        boss._nxr_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_nxr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_nyxraal._draw_shadow(surface, x, y + 50)
        _NS_nyxraal._draw_hover_particles(surface, x, y + 44, boss.pulse)
        _NS_nyxraal._draw_nxr_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_nxr_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_nyxraal._draw_shadow(surface, x + sway, y + 50)
        _NS_nyxraal._draw_hover_particles(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_nyxraal._draw_nxr_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_nxr_attack(surface, boss, x, y):
        progress = getattr(boss, "_nxr_attack_progress", None)
        if progress is None or progress <= 0:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            lunge = int((-3 + t_eased * 12)) * boss.direction
            lift = int(3 - t_eased * 4)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_nyxraal._draw_shadow(surface, x + lunge, y + 50)
        _NS_nyxraal._draw_hover_particles(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_nyxraal._draw_nxr_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_nyxraal._draw_sword_swing(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_nxr_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cape/energy tendrils behind.
        _NS_nyxraal._draw_energy_cape(surface, cx, cy, facing, phase)
        # Back arm (with chain hanging).
        _NS_nyxraal._draw_back_arm(surface, cx, cy - 4, facing, phase, action)
        # Legs (dark leather with shin guards).
        _NS_nyxraal._draw_leg_armor(surface, cx, cy + 10, facing, phase, action)
        # Bare torso with tattoos.
        _NS_nyxraal._draw_bare_torso(surface, cx, cy, facing, phase)
        # Belt.
        _NS_nyxraal._draw_belt(surface, cx, cy + 8, facing, phase)
        # Shoulder pauldron.
        _NS_nyxraal._draw_shoulder_pauldron(surface, cx, cy - 10, facing, phase)
        # Head with spike hair.
        _NS_nyxraal._draw_prince_head(surface, cx, cy - 20, facing, phase, action)
        # Front arm with sword.
        _NS_nyxraal._draw_sword_arm(surface, cx, cy - 4, facing, phase, action, attack_progress)
    def _draw_energy_cape(surface, cx, cy, facing, phase):
        """Purple energy tendrils flowing behind."""
        wave = math.sin(phase * 1.0) * 3
        back_dir = -facing
        # 3 flowing tendrils.
        for tendril_i in range(3):
            tendril_offset = (tendril_i - 1) * 6
            base_x = cx + back_dir * 6 + int(tendril_offset * 0.3)
            base_y = cy - 8 + tendril_offset
            segments = 6
            prev = (base_x, base_y)
            for seg in range(1, segments + 1):
                t = seg / segments
                seg_wave = math.sin(phase * 1.2 + seg * 0.6 + tendril_i) * (3 + t * 2)
                bx = base_x + int(back_dir * (t * 18)) + int(seg_wave)
                by = base_y + int(t * 20) - int(seg_wave * 0.5)
                thickness = max(1, 4 - seg // 2)
                # Layer glow.
                for layer_thick, color in [
                    (thickness + 2, _NS_nyxraal.PALETTE["abyss_darkest"]),
                    (thickness + 1, _NS_nyxraal.PALETTE["abyss_dark"]),
                    (thickness, _NS_nyxraal.PALETTE["abyss_mid"]),
                    (max(1, thickness - 1), _NS_nyxraal.PALETTE["abyss_light"]),
                ]:
                    _NS_nyxraal._aaline(surface, color, prev, (bx, by), layer_thick)
                # Bright tip.
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (bx, by, 1, 1))
                prev = (bx, by)
            # End sparkle.
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["white"], (prev[0], prev[1], 1, 1))
    def _draw_leg_armor(surface, cx, cy, facing, phase, action):
        """Dark violet leather pants + shin guards."""
        leg_bob = math.sin(phase * 1.5) * 3 if action == "walk" \
            else math.sin(phase * 0.8) * 1
        # Pants shape (slim).
        pants_shape = [
            (cx - 11, cy - 4),
            (cx + 11, cy - 4),
            (cx + 13, cy + 4),
            (cx + 11, cy + 12),
            (cx + 6, cy + 16),
            (cx - 6, cy + 16),
            (cx - 11, cy + 12),
            (cx - 13, cy + 4),
        ]
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in pants_shape])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["leather_dark"], pants_shape)
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["leather_mid"], [
            (cx - 10, cy - 3),
            (cx + 10, cy - 3),
            (cx + 12, cy + 4),
            (cx + 9, cy + 11),
            (cx - 9, cy + 11),
            (cx - 12, cy + 4),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["leather_light"], [
            (cx - 7, cy - 2),
            (cx + 7, cy - 2),
            (cx + 9, cy + 4),
            (cx - 9, cy + 4),
        ])
        # Central seam.
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["leather_dark"],
                         (cx, cy - 4), (cx, cy + 14), 1)
        # Purple energy line down each thigh.
        for side in (-1, 1):
            thigh_x = cx + side * 6
            for band_y in (2, 6, 10):
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_mid"],
                                 (thigh_x - 1, cy + band_y, 2, 1))
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"],
                                 (thigh_x, cy + band_y, 1, 1))
        # Boots visible below.
        for side in (-1, 1):
            foot_x = cx + side * 6
            foot_y = cy + 16 + int(leg_bob * side * 0.3)
            # Armored boot.
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"], [
                (foot_x - 4 + 1, foot_y - 2 + 1),
                (foot_x + 4 + 1, foot_y - 2 + 1),
                (foot_x + 3 + 1, foot_y + 2 + 1),
                (foot_x - 3 + 1, foot_y + 2 + 1),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_darkest"], [
                (foot_x - 4, foot_y - 2),
                (foot_x + 4, foot_y - 2),
                (foot_x + 3, foot_y + 2),
                (foot_x - 3, foot_y + 2),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_dark"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_mid"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 2, foot_y - 1),
                (foot_x + 1, foot_y),
                (foot_x - 1, foot_y),
            ])
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_light"], (foot_x, foot_y - 1, 1, 1))
    def _draw_bare_torso(surface, cx, cy, facing, phase):
        """Bare pale muscular torso with dark abyss tattoos."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape.
        torso_shape = [
            (cx - 13, cy - 12),
            (cx - 15, cy - 4),
            (cx - 13, cy + 4),
            (cx - 10, cy + 12),
            (cx + 10, cy + 12),
            (cx + 13, cy + 4),
            (cx + 15, cy - 4),
            (cx + 13, cy - 12),
            (cx + 5, cy - 14),
            (cx - 5, cy - 14),
        ]
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in torso_shape])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_darkest"], torso_shape)
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_dark"], [
            (cx - 12, cy - 11),
            (cx - 14, cy - 3),
            (cx - 12, cy + 3),
            (cx - 9, cy + 11),
            (cx + 9, cy + 11),
            (cx + 12, cy + 3),
            (cx + 14, cy - 3),
            (cx + 12, cy - 11),
            (cx + 4, cy - 13),
            (cx - 4, cy - 13),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_mid"], [
            (cx - 10, cy - 9),
            (cx - 12, cy - 2),
            (cx - 9, cy + 4),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 9, cy + 4),
            (cx + 12, cy - 2),
            (cx + 10, cy - 9),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ])
        # PECTORALS (2 chest muscles).
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_light"], [
            (cx - 8, cy - 7),
            (cx - 1, cy - 9),
            (cx - 1, cy - 3),
            (cx - 6, cy - 2),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_light"], [
            (cx + 1, cy - 9),
            (cx + 8, cy - 7),
            (cx + 6, cy - 2),
            (cx + 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["skin_shine"], (cx - 5, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["skin_shine"], (cx + 3, cy - 8, 2, 1))
        # ABS.
        for row in range(3):
            ab_y = cy - 1 + row * 2
            pygame.draw.line(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                             (cx, ab_y - 1), (cx, ab_y + 1), 1)
            pygame.draw.line(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                             (cx - 4, ab_y), (cx + 4, ab_y), 1)
            pygame.draw.line(surface, _NS_nyxraal.PALETTE["skin_light"],
                             (cx - 3, ab_y - 1), (cx + 3, ab_y - 1), 1)
        # ABYSS TATTOOS on chest (dark curly lines).
        # Left pectoral tattoo.
        for pt in [(-6, -6), (-4, -5), (-3, -3), (-5, -2), (-6, -4)]:
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_darkest"],
                             (cx + pt[0], cy + pt[1], 1, 1))
        for pt in [(-5, -6), (-4, -4)]:
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_dark"],
                             (cx + pt[0], cy + pt[1], 1, 1))
        # Right pectoral tattoo.
        for pt in [(3, -6), (4, -5), (5, -3), (3, -2), (5, -4)]:
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_darkest"],
                             (cx + pt[0], cy + pt[1], 1, 1))
        for pt in [(4, -6), (3, -4)]:
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_dark"],
                             (cx + pt[0], cy + pt[1], 1, 1))
        # Small purple glow accents on tattoos.
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (cx - 5, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (cx + 4, cy - 5, 1, 1))
        # BICEPS.
        for side in (-1, 1):
            bicep_x = cx + side * 13
            bicep_y = cy - 4
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_dark"], (bicep_x, bicep_y), 4)
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_mid"], (bicep_x, bicep_y), 3)
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_light"], (bicep_x - 1, bicep_y - 1), 1)
    def _draw_shoulder_pauldron(surface, cx, cy, facing, phase):
        """Dark armored shoulder pieces with sharp spikes."""
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy
            # Base pauldron (curved sharp shape).
            paul_shape = [
                (sh_x - 4, sh_y - 2),
                (sh_x + 4, sh_y - 2),
                (sh_x + 6, sh_y + 3),
                (sh_x + 4, sh_y + 5),
                (sh_x - 4, sh_y + 5),
                (sh_x - 6, sh_y + 3),
            ]
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in paul_shape])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_darkest"], paul_shape)
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_dark"], [
                (sh_x - 3, sh_y - 1),
                (sh_x + 3, sh_y - 1),
                (sh_x + 5, sh_y + 3),
                (sh_x + 3, sh_y + 4),
                (sh_x - 3, sh_y + 4),
                (sh_x - 5, sh_y + 3),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_mid"], [
                (sh_x - 2, sh_y),
                (sh_x + 2, sh_y),
                (sh_x + 3, sh_y + 2),
                (sh_x - 3, sh_y + 2),
            ])
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["armor_edge"], (sh_x - 1, sh_y, 2, 1))
            # Sharp spike on top.
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_darkest"], [
                (sh_x - 2, sh_y - 2),
                (sh_x + 2, sh_y - 2),
                (sh_x + int(side), sh_y - 6),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_dark"], [
                (sh_x - 1, sh_y - 2),
                (sh_x + 1, sh_y - 2),
                (sh_x + int(side), sh_y - 5),
            ])
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (sh_x + int(side), sh_y - 6, 1, 1))
            # Purple gem in pauldron.
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["abyss_darkest"], (sh_x, sh_y + 2), 2)
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["abyss_mid"], (sh_x, sh_y + 2), 1)
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (sh_x, sh_y + 2, 1, 1))
    def _draw_belt(surface, cx, cy, facing, phase):
        """Slim dark belt."""
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"], [
            (cx - 13 + 1, cy - 2 + 1),
            (cx + 13 + 1, cy - 2 + 1),
            (cx + 13 + 1, cy + 2 + 1),
            (cx - 13 + 1, cy + 2 + 1),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["leather_dark"], [
            (cx - 13, cy - 2),
            (cx + 13, cy - 2),
            (cx + 13, cy + 2),
            (cx - 13, cy + 2),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["leather_mid"], [
            (cx - 12, cy - 1),
            (cx + 12, cy - 1),
            (cx + 12, cy + 1),
            (cx - 12, cy + 1),
        ])
        # Central buckle (dark armor with purple gem).
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_darkest"], (cx, cy), 3)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_dark"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_mid"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (cx, cy, 1, 1))
    def _draw_prince_head(surface, cx, cy, facing, phase, action):
        """Head with spiky white hair, pale skin, purple glowing eyes."""
        # Face (angular).
        head_shape = [
            (cx - 5, cy + 5),
            (cx - 6, cy),
            (cx - 5, cy - 5),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 5, cy - 5),
            (cx + 6, cy),
            (cx + 5, cy + 5),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_darkest"], head_shape)
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_dark"], [
            (cx - 4, cy + 4),
            (cx - 5, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 4),
            (cx + 1, cy + 7),
            (cx - 1, cy + 7),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_mid"], [
            (cx - 4, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 4, cy - 2),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["skin_shine"], (cx - 1, cy - 3, 1, 1))
        # SPIKY WHITE HAIR (multiple spikes going up + back).
        spike_wave = math.sin(phase * 0.5) * 1
        # Base hair mass.
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"], [
            (cx - 6 + 1, cy - 3 + 1),
            (cx - 7 + 1, cy - 6 + 1),
            (cx + 7 + 1, cy - 6 + 1),
            (cx + 6 + 1, cy - 3 + 1),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["hair_darkest"], [
            (cx - 6, cy - 3),
            (cx - 7, cy - 6),
            (cx + 7, cy - 6),
            (cx + 6, cy - 3),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["hair_dark"], [
            (cx - 5, cy - 3),
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 5, cy - 3),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["hair_mid"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        # SPIKES (multiple upward + backward).
        spikes = [
            (-6, -6, -8, -11, 1),   # left large
            (-3, -6, -4, -12, 2),   # left middle
            (0, -6, 0, -13, 2),     # center large
            (3, -6, 4, -12, 2),     # right middle
            (6, -6, 8, -11, 1),     # right large
            (-5, -6, -7, -9, 1),    # small left back
            (5, -6, 7, -9, 1),      # small right back
        ]
        for spike_i, (bx1, by1, tx1, ty1, mid_layer) in enumerate(spikes):
            sway = int(math.sin(phase * 0.4 + spike_i * 0.5) * 1)
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"], [
                (cx + bx1 - 1 + 1, cy + by1 + 1),
                (cx + bx1 + 1 + 1, cy + by1 + 1),
                (cx + tx1 + sway + 1, cy + ty1 + 1),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["hair_darkest"], [
                (cx + bx1 - 1, cy + by1),
                (cx + bx1 + 1, cy + by1),
                (cx + tx1 + sway, cy + ty1),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["hair_dark"], [
                (cx + bx1, cy + by1),
                (cx + int((bx1 + tx1) / 2) + sway, cy + int((by1 + ty1) / 2)),
                (cx + bx1 + int(0.5), cy + by1 - 1),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["hair_mid"], [
                (cx + tx1 + sway - 1, cy + ty1 + 2),
                (cx + tx1 + sway, cy + ty1),
                (cx + tx1 + sway + 1, cy + ty1 + 2),
            ])
            # Highlight tip.
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["hair_light"], (cx + tx1 + sway, cy + ty1, 1, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["hair_shine"], (cx + tx1 + sway, cy + ty1, 1, 1))
        # EYEBROWS.
        for eye_off in (-2, 2):
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["hair_darkest"], (cx + eye_off - 1, cy - 3, 2, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["hair_dark"], (cx + eye_off - 1, cy - 4, 2, 1))
        # GLOWING PURPLE EYES.
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy - 1
            for r in range(4, 0, -1):
                alpha = _NS_nyxraal._alpha(150 * (4 - r) / 4 * eye_pulse)
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["eye_mid"], alpha), (ex, ey), r)
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["eye_socket"], (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # NOSE.
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                         (cx, cy - 1), (cx, cy + 2), 1)
        # SMIRK (evil grin).
        if action == "attack":
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["shadow_deep"], (cx - 2, cy + 4, 5, 2))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_darkest"], (cx - 1, cy + 4, 3, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["white"], (cx - 1, cy + 4, 1, 1))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["white"], (cx + 1, cy + 4, 1, 1))
        else:
            # Confident smirk (curved up on one side).
            pygame.draw.line(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                             (cx - 2, cy + 4), (cx + 2, cy + 4), 1)
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["skin_darkest"], (cx + 2, cy + 3, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm hanging (with chain wrapped around wrist)."""
        back_dir = -facing
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx + back_dir * 10
        shoulder_y = cy - 4
        elbow_x = cx + back_dir * 14
        elbow_y = cy + 4 + int(sway)
        hand_x = cx + back_dir * 12
        hand_y = cy + 12 + int(sway * 0.5)
        # Upper arm (skin).
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_mid"],
                            (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)
        # Elbow.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_darkest"], (elbow_x, elbow_y), 3)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_mid"], (elbow_x, elbow_y), 2)
        # Forearm.
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Fist with dark gauntlet.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_darkest"], (hand_x, hand_y), 3)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_dark"], (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (hand_x, hand_y, 1, 1))
        # Chain wrapped around forearm (small links dangling down).
        for i in range(4):
            chain_y = hand_y + 4 + i * 3
            chain_x = hand_x + int(math.sin(phase + i * 0.5) * 2)
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_darkest"], (chain_x, chain_y), 2)
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_mid"], (chain_x, chain_y), 1)
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["chain_light"], (chain_x, chain_y, 1, 1))
    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with sword — swing animation."""
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                swing_angle = -math.pi * 0.15 - t * math.pi * 0.55
                arm_length = 22
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                t_eased = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.7 + t_eased * math.pi * 1.0
                arm_length = 22 + int(t_eased * 6)
            else:
                t = (attack_progress - 0.6) / 0.4
                swing_angle = math.pi * 0.3 - t * math.pi * 0.45
                arm_length = 28 - int(t * 6)
        else:
            swing_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.1
            arm_length = 22
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 6
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        elbow_x = (shoulder_x + hand_x) // 2 + facing * 2
        elbow_y = (shoulder_y + hand_y) // 2
        # Upper arm (skin, muscular).
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_mid"],
                            (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_light"],
                            (shoulder_x, shoulder_y - 2), (elbow_x, elbow_y - 2), 1)
        # Elbow.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_darkest"], (elbow_x, elbow_y), 4)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_dark"], (elbow_x, elbow_y), 3)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["skin_mid"], (elbow_x - 1, elbow_y - 1), 2)
        # Forearm.
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_nyxraal._aaline(surface, _NS_nyxraal.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Dark gauntlet on wrist.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_darkest"], (hand_x, hand_y), 4)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_dark"], (hand_x, hand_y), 3)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_mid"], (hand_x - 1, hand_y - 1), 2)
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (hand_x, hand_y, 1, 1))
        # ABYSS SWORD.
        _NS_nyxraal._draw_abyss_sword(surface, hand_x, hand_y, facing, phase, swing_angle)
    def _draw_abyss_sword(surface, hx, hy, facing, phase, angle):
        """Steel sword with purple abyss energy along blade."""
        blade_len = 32
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        # Handle behind hand.
        handle_x = hx - int(math.cos(angle) * 6) * facing
        handle_y = hy - int(math.sin(angle) * 6)
        perp = angle + math.pi / 2
        base_w = 3
        # Steel blade base.
        b1 = (hx + int(math.cos(perp) * base_w),
              hy + int(math.sin(perp) * base_w))
        b2 = (hx - int(math.cos(perp) * base_w),
              hy - int(math.sin(perp) * base_w))
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["shadow_deep"], [
            (b1[0] + 1, b1[1] + 1),
            (tip_x + 1, tip_y + 1),
            (b2[0] + 1, b2[1] + 1),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["steel_darkest"],
                          [b1, (tip_x, tip_y), b2])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["steel_dark"], [
            (b1[0] - int(math.cos(perp)), b1[1] - int(math.sin(perp))),
            (tip_x, tip_y),
            (b2[0] + int(math.cos(perp)), b2[1] + int(math.sin(perp))),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["steel_mid"], [
            (b1[0] - int(math.cos(perp) * 2), b1[1] - int(math.sin(perp) * 2)),
            (int((hx + tip_x) / 2), int((hy + tip_y) / 2)),
            (hx, hy),
        ])
        _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["steel_light"], [
            (hx, hy),
            (int((hx + tip_x) / 2), int((hy + tip_y) / 2)),
            (tip_x, tip_y),
        ])
        # PURPLE ABYSS ENERGY along blade edge.
        FX_W, FX_H = 100, 100
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        for glow_width, glow_alpha, glow_color in [
            (5, 100, _NS_nyxraal.PALETTE["abyss_dark"]),
            (3, 150, _NS_nyxraal.PALETTE["abyss_mid"]),
            (2, 200, _NS_nyxraal.PALETTE["abyss_light"]),
            (1, 240, _NS_nyxraal.PALETTE["abyss_hot"]),
        ]:
            tip_l = (ox + int(math.cos(angle) * blade_len) * facing,
                     oy + int(math.sin(angle) * blade_len))
            pygame.draw.line(fx_surf, (*glow_color, glow_alpha),
                             (ox, oy), tip_l, glow_width)
        surface.blit(fx_surf, (hx - ox, hy - oy))
        # Bright core.
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["white"], (hx, hy), (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Tip sparkle.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["abyss_hot"], (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Handle guard.
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["armor_darkest"],
                         (hx + int(math.cos(perp) * 5), hy + int(math.sin(perp) * 5)),
                         (hx - int(math.cos(perp) * 5), hy - int(math.sin(perp) * 5)), 3)
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["armor_dark"],
                         (hx + int(math.cos(perp) * 4), hy + int(math.sin(perp) * 4)),
                         (hx - int(math.cos(perp) * 4), hy - int(math.sin(perp) * 4)), 2)
        # Purple gem in guard.
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (hx, hy, 1, 1))
        # Handle grip.
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["armor_darkest"],
                         (handle_x, handle_y), (hx, hy), 4)
        pygame.draw.line(surface, _NS_nyxraal.PALETTE["armor_dark"],
                         (handle_x, handle_y), (hx, hy), 2)
        # Pommel.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_darkest"], (handle_x, handle_y), 2)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["abyss_dark"], (handle_x, handle_y), 1)
    # ================= MELEE SWING FX =================
    def _draw_sword_swing(surface, boss, x, y, progress):
        """Purple abyss slash arc."""
        if progress < 0.30 or progress > 0.80:
            return
        facing = boss.direction
        if progress < 0.6:
            swing_t = (progress - 0.30) / 0.30
        else:
            swing_t = 1.0 - (progress - 0.6) / 0.20
        swing_t = max(0.0, min(1.0, swing_t))
        alpha_base = _NS_nyxraal._alpha(255 * swing_t)
        if alpha_base <= 5:
            return
        cx_sh = x + facing * 12
        cy_sh = y - 6
        if progress < 0.35:
            current_angle = -math.pi * 0.7
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            current_angle = -math.pi * 0.7 + t_eased * math.pi * 1.0
        else:
            current_angle = math.pi * 0.3
        start_angle = -math.pi * 0.7
        arc_length = 34
        FX_W, FX_H = 240, 240
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        def to_fx(wx, wy):
            return (wx - cx_sh + ox, wy - cy_sh + oy)
        # ARC TRAIL (purple).
        for thickness, alpha_mult, color, radius_off in [
            (11, 0.30, _NS_nyxraal.PALETTE["abyss_darkest"], 4),
            (9, 0.50, _NS_nyxraal.PALETTE["abyss_dark"], 2),
            (7, 0.75, _NS_nyxraal.PALETTE["abyss_mid"], 1),
            (5, 0.95, _NS_nyxraal.PALETTE["abyss_light"], 0),
            (3, 1.00, _NS_nyxraal.PALETTE["abyss_hot"], 0),
            (1, 1.00, _NS_nyxraal.PALETTE["white"], 0),
        ]:
            steps = 26
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_nyxraal._alpha(alpha_base * alpha_mult * (0.2 + 0.8 * seg_t))
                if seg_alpha <= 0:
                    prev = None
                    continue
                a = start_angle + (current_angle - start_angle) * seg_t
                r = arc_length + radius_off
                wx = cx_sh + int(math.cos(a) * r) * facing
                wy = cy_sh + int(math.sin(a) * r)
                p = to_fx(wx, wy)
                if prev is not None:
                    pygame.draw.line(fx_surf, (*color, seg_alpha), prev, p, thickness)
                prev = p
        # LEADING EDGE FLASH.
        lead_wx = cx_sh + int(math.cos(current_angle) * (arc_length + 4)) * facing
        lead_wy = cy_sh + int(math.sin(current_angle) * (arc_length + 4))
        lfx, lfy = to_fx(lead_wx, lead_wy)
        for r in range(14, 0, -1):
            a = _NS_nyxraal._alpha(alpha_base * (14 - r) / 14 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_nyxraal.PALETTE["abyss_hot"], a), (lfx, lfy), r)
        pygame.draw.circle(fx_surf, (*_NS_nyxraal.PALETTE["abyss_shine"], alpha_base), (lfx, lfy), 3)
        pygame.draw.circle(fx_surf, (*_NS_nyxraal.PALETTE["white"], alpha_base), (lfx, lfy), 1)
        # SLASH LINES.
        for slash_i in range(3):
            slash_offset = (slash_i - 1) * 0.10
            slash_a = current_angle + slash_offset
            slash_alpha = _NS_nyxraal._alpha(alpha_base * (1 - abs(slash_offset) * 4))
            if slash_alpha <= 0:
                continue
            inner_r = arc_length - 12
            outer_r = arc_length + 14
            wx1 = cx_sh + int(math.cos(slash_a) * inner_r) * facing
            wy1 = cy_sh + int(math.sin(slash_a) * inner_r)
            wx2 = cx_sh + int(math.cos(slash_a) * outer_r) * facing
            wy2 = cy_sh + int(math.sin(slash_a) * outer_r)
            p1 = to_fx(wx1, wy1)
            p2 = to_fx(wx2, wy2)
            pygame.draw.line(fx_surf, (*_NS_nyxraal.PALETTE["white"], slash_alpha), p1, p2, 4 - slash_i)
            pygame.draw.line(fx_surf, (*_NS_nyxraal.PALETTE["abyss_shine"], slash_alpha), p1, p2, 1)
        # SPARKS.
        for i in range(16):
            spark_seed = i * 0.7 + progress * 4
            spark_a = current_angle + math.sin(spark_seed) * 0.5
            spark_r = arc_length + 6 + (i % 4) * 5 + int(swing_t * 10)
            wspx = cx_sh + int(math.cos(spark_a) * spark_r) * facing
            wspy = cy_sh + int(math.sin(spark_a) * spark_r)
            spx, spy = to_fx(wspx, wspy)
            spark_alpha = _NS_nyxraal._alpha(alpha_base * (0.7 + (i % 3) * 0.1))
            tail_wx = wspx - int(math.cos(spark_a) * 4) * facing
            tail_wy = wspy - int(math.sin(spark_a) * 4)
            tfx, tfy = to_fx(tail_wx, tail_wy)
            pygame.draw.line(fx_surf, (*_NS_nyxraal.PALETTE["abyss_mid"], spark_alpha), (tfx, tfy), (spx, spy), 2)
            pygame.draw.rect(fx_surf, (*_NS_nyxraal.PALETTE["abyss_hot"], spark_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_nyxraal.PALETTE["white"], spark_alpha), (spx, spy, 1, 1))
        # IMPACT BURST.
        if 0.55 < progress < 0.72:
            impact_t = (progress - 0.55) / 0.17
            impact_alpha = _NS_nyxraal._alpha(240 * (1 - impact_t))
            if impact_alpha > 0:
                impact_wx = cx_sh + int(math.cos(math.pi * 0.2) * (arc_length + 10)) * facing
                impact_wy = cy_sh + int(math.sin(math.pi * 0.2) * (arc_length + 10))
                ifx, ify = to_fx(impact_wx, impact_wy)
                for burst_r in range(int(8 + impact_t * 20), 0, -2):
                    a = _NS_nyxraal._alpha(impact_alpha * (22 - burst_r) / 22)
                    if a > 0:
                        pygame.draw.circle(fx_surf, (*_NS_nyxraal.PALETTE["abyss_light"], a), (ifx, ify), burst_r)
                for i in range(12):
                    a_burst = i * math.pi / 6
                    bx = ifx + int(math.cos(a_burst) * (10 + impact_t * 14))
                    by = ify + int(math.sin(a_burst) * (10 + impact_t * 14))
                    pygame.draw.line(fx_surf, (*_NS_nyxraal.PALETTE["abyss_hot"], impact_alpha), (ifx, ify), (bx, by), 2)
                    pygame.draw.rect(fx_surf, (*_NS_nyxraal.PALETTE["white"], impact_alpha), (bx, by, 2, 2))
        surface.blit(fx_surf, (cx_sh - ox, cy_sh - oy))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 3, 20, 180), (5, 9, 140, 14))
        pygame.draw.ellipse(shadow, (60, 15, 100, 130), (12, 11, 126, 10))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_abyss_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_nyxraal._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxraal._aacircle(aura, (*_NS_nyxraal.PALETTE["abyss_darkest"], alpha), (130, 110), radius)
        for radius in range(65, 5, -3):
            alpha = _NS_nyxraal._alpha((65 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_nyxraal._aacircle(aura, (*_NS_nyxraal.PALETTE["abyss_dark"], alpha), (130, 110), radius)
        for radius in range(35, 5, -2):
            alpha = _NS_nyxraal._alpha((35 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_nyxraal._aacircle(aura, (*_NS_nyxraal.PALETTE["abyss_mid"], alpha), (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Floating purple particles.
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 6 + i * 5) % 24)
            color = _NS_nyxraal.PALETTE["abyss_mid"] if i % 2 == 0 else _NS_nyxraal.PALETTE["abyss_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxraal.PALETTE["abyss_darkest"], 200), (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxraal.PALETTE["abyss_dark"], 220), (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxraal.PALETTE["abyss_mid"], 180), (25, 24, 140, 22), 1)
        # Rune markers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 95 + int(math.cos(angle) * 74)
            y1 = 35 + int(math.sin(angle) * 12)
            pygame.draw.rect(ring, _NS_nyxraal.PALETTE["abyss_hot"], (x1, y1, 2, 2))
            pygame.draw.rect(ring, _NS_nyxraal.PALETTE["white"], (x1, y1, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxraal.PALETTE["abyss_hot"], _NS_nyxraal._alpha(150 * pulse)),
                                (15, 14, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))
    def _draw_hover_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Purple abyss particles rising."""
        strength = 1.5 if intense else 1.0
        # Mist.
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_nyxraal._alpha((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_nyxraal.PALETTE["abyss_darkest"], alpha),
                                    (80 - radius * 2, 25 - radius // 3, radius * 4, max(3, radius // 2)))
        for radius in range(22, 3, -2):
            alpha = _NS_nyxraal._alpha((22 - radius) * 3.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_nyxraal.PALETTE["abyss_dark"], alpha),
                                    (80 - radius, 25 - radius // 4, radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising purple orbs.
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26, -32, 32)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_nyxraal._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], alpha), (sx, sy), 3)
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha), (sx, sy - 1, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxraal._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_mid"], alpha),
                                      (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha),
                                 (sx, sy - 1, 2, 1))
    def _draw_ambient_chains(surface, x, y, phase):
        """Dark chains hanging in air around boss."""
        for chain_i in range(3):
            base_offset_x = (chain_i - 1) * 35
            base_x = x + base_offset_x
            base_y = y - 55 + int(math.sin(phase + chain_i) * 3)
            # Chain link segments hanging.
            for link_i in range(6):
                link_y = base_y + link_i * 5
                link_x = base_x + int(math.sin(phase + chain_i + link_i * 0.3) * 2)
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_darkest"], (link_x, link_y), 3)
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_dark"], (link_x, link_y), 2)
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_mid"], (link_x - 1, link_y - 1), 1)
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["chain_light"], (link_x - 1, link_y - 1, 1, 1))
    # ================= SKILL Q — SPECTRE STEP (dash) =================
    def _draw_spectre_dash_ground(surface, boss, x, y, timer, phase):
        """Purple dash trail on ground."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            dash_t = progress / 0.5
            length = int(60 * dash_t)
            alpha = _NS_nyxraal._alpha(200)
            for i in range(4):
                pygame.draw.line(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], alpha - i * 40),
                                 (x, y + 40), (x + facing * length, y + 40), 4 - i)
    def _draw_spectre_step_trail(surface, boss, x, y, timer, phase):
        """Afterimages during dash."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            dash_t = progress / 0.5
            # Ghost trail behind boss.
            for i in range(1, 5):
                ghost_offset = -int(i * 12) * facing
                ghost_alpha = _NS_nyxraal._alpha(160 - i * 35)
                # Simple silhouette of boss body.
                ghost = pygame.Surface((60, 100), pygame.SRCALPHA)
                _NS_nyxraal._aacircle(ghost, (*_NS_nyxraal.PALETTE["abyss_mid"], ghost_alpha), (30, 30), 12)
                _NS_nyxraal._poly(ghost, (*_NS_nyxraal.PALETTE["abyss_dark"], ghost_alpha), [
                    (18, 40), (42, 40), (46, 70), (14, 70),
                ])
                _NS_nyxraal._poly(ghost, (*_NS_nyxraal.PALETTE["abyss_mid"], ghost_alpha), [
                    (22, 70), (38, 70), (36, 90), (24, 90),
                ])
                surface.blit(ghost, (x + ghost_offset - 30, y - 35))
            # Purple slash streaks.
            for i in range(6):
                streak_x = x - int(i * 15) * facing
                streak_alpha = _NS_nyxraal._alpha(220 - i * 30)
                pygame.draw.line(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], streak_alpha),
                                 (streak_x, y - 10 + int(math.sin(phase * 5 + i) * 4)),
                                 (streak_x + facing * 12, y + 10 + int(math.sin(phase * 5 + i) * 4)), 2)
    # ================= SKILL W — ABYSS PULL (chain grab) =================
    def _draw_abyss_pull_chain(surface, boss, x, y, timer, phase):
        """Purple chain flies to target and pulls."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxraal._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        if progress < 0.5:
            # Chain extends.
            t = progress / 0.5
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
        else:
            # Hold + pull.
            end_x = tx
            end_y = ty
        # Draw chain segments (purple glowing chain).
        segments = 14
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            wave = math.sin(phase * 4 + i * 0.5) * 3
            px1 = int(start_x + (end_x - start_x) * t1)
            py1 = int(start_y + (end_y - start_y) * t1 + wave)
            px2 = int(start_x + (end_x - start_x) * t2)
            py2 = int(start_y + (end_y - start_y) * t2 + math.sin(phase * 4 + (i + 1) * 0.5) * 3)
            # Chain link.
            mx = (px1 + px2) // 2
            my = (py1 + py2) // 2
            if i % 2 == 0:
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_darkest"], (mx, my), 3)
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_dark"], (mx, my), 2)
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["chain_light"], (mx, my, 1, 1))
            else:
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_dark"], (mx, my), 2)
                _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["chain_mid"], (mx, my), 1)
            # Purple energy along chain.
            pygame.draw.line(surface, _NS_nyxraal.PALETTE["abyss_mid"], (px1, py1), (px2, py2), 1)
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (mx, my - 2, 1, 1))
        # Claw/hook at end with purple energy.
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["shadow_deep"], (end_x + 1, end_y + 1), 5)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_darkest"], (end_x, end_y), 5)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["armor_dark"], (end_x, end_y), 4)
        _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["abyss_mid"], (end_x, end_y), 2)
        pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (end_x, end_y, 1, 1))
        # 3 claw prongs.
        dx = end_x - start_x
        dy = end_y - start_y
        claw_angle = math.atan2(dy, dx)
        for i in range(-1, 2):
            prong_angle = claw_angle + i * math.pi / 4
            px = end_x + int(math.cos(prong_angle) * 8)
            py = end_y + int(math.sin(prong_angle) * 8)
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_darkest"], [
                (end_x, end_y),
                (px, py),
                (end_x + int(math.cos(prong_angle + math.pi / 2) * 2),
                 end_y + int(math.sin(prong_angle + math.pi / 2) * 2)),
            ])
            _NS_nyxraal._poly(surface, _NS_nyxraal.PALETTE["armor_mid"], [
                (end_x, end_y),
                (int((end_x + px) / 2), int((end_y + py) / 2)),
                (end_x + int(math.cos(prong_angle + math.pi / 2) * 1),
                 end_y + int(math.sin(prong_angle + math.pi / 2) * 1)),
            ])
            pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (px, py, 1, 1))
        # Impact splash when hooked.
        if progress > 0.5:
            splash_t = (progress - 0.5) / 0.5
            for r in range(int(12 * (1 - splash_t)), 0, -2):
                alpha = _NS_nyxraal._alpha(220 * (1 - splash_t))
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_light"], alpha), (end_x, end_y), r, 1)
    # ================= SKILL E — REAPING WHIRL =================
    def _draw_reaping_ground(surface, boss, x, y, timer, phase):
        """Purple ring at feet."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r > 5:
            pygame.draw.ellipse(surface, (*_NS_nyxraal.PALETTE["abyss_darkest"], 220),
                                (x - r, y + 40 - r // 4, r * 2, r * 2 // 4))
            pygame.draw.ellipse(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], 200),
                                (x - r + 4, y + 40 - r // 4 + 2, r * 2 - 8, r * 2 // 4 - 4), 2)
    def _draw_reaping_whirl(surface, boss, x, y, timer, phase):
        """Purple sword whirl arcs around boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi) if progress < 0.85 else (1 - progress) / 0.15
        intensity = max(0, min(1, intensity))
        alpha_base = _NS_nyxraal._alpha(255 * intensity)
        cx_c = x
        cy_c = y - 6
        # Multiple orbit arcs going around body.
        for arc_i in range(3):
            rot_offset = phase * 5 + arc_i * math.pi * 2 / 3
            # Draw arc as many segments.
            num_seg = 20
            arc_r = 45 + arc_i * 4
            for s in range(num_seg):
                a1 = rot_offset + s * math.pi * 2 / num_seg
                a2 = rot_offset + (s + 1) * math.pi * 2 / num_seg
                # Fade tail — full arc.
                seg_alpha = _NS_nyxraal._alpha(alpha_base * 0.6)
                x1 = cx_c + int(math.cos(a1) * arc_r)
                y1 = cy_c + int(math.sin(a1) * arc_r * 0.6)
                x2 = cx_c + int(math.cos(a2) * arc_r)
                y2 = cy_c + int(math.sin(a2) * arc_r * 0.6)
                # Layers.
                for thick, color in [
                    (5, _NS_nyxraal.PALETTE["abyss_dark"]),
                    (3, _NS_nyxraal.PALETTE["abyss_mid"]),
                    (2, _NS_nyxraal.PALETTE["abyss_light"]),
                    (1, _NS_nyxraal.PALETTE["abyss_hot"]),
                ]:
                    pygame.draw.line(surface, color, (x1, y1), (x2, y2), thick)
        # Bright sword tip (rotating).
        for i in range(3):
            tip_a = phase * 5 + i * math.pi * 2 / 3
            tip_r = 50
            tx_ = cx_c + int(math.cos(tip_a) * tip_r)
            ty_ = cy_c + int(math.sin(tip_a) * tip_r * 0.6)
            # Bright flash.
            for r in range(6, 0, -1):
                a = _NS_nyxraal._alpha(alpha_base * (6 - r) / 6)
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], a), (tx_, ty_), r)
            _NS_nyxraal._aacircle(surface, _NS_nyxraal.PALETTE["white"], (tx_, ty_), 1)
        # Sparks flying outward.
        for i in range(14):
            spark_a = i * math.pi / 7 + phase * 2
            spark_r = 55 + (i % 3) * 4
            spx = cx_c + int(math.cos(spark_a) * spark_r)
            spy = cy_c + int(math.sin(spark_a) * spark_r * 0.6)
            sp_alpha = _NS_nyxraal._alpha(alpha_base * 0.8)
            pygame.draw.rect(surface, (*_NS_nyxraal.PALETTE["abyss_light"], sp_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(surface, (*_NS_nyxraal.PALETTE["white"], sp_alpha), (spx, spy, 1, 1))
    # ================= SKILL R — ABYSS DESCENT (jump + slam) =================
    def _draw_descent_ground(surface, boss, x, y, timer, phase):
        """Big impact ring on ground."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ring only shows after slam (progress > 0.7).
        if progress > 0.7:
            slam_t = (progress - 0.7) / 0.3
            r = int(80 * min(1.0, slam_t * 3))
            alpha = _NS_nyxraal._alpha(240 * (1 - slam_t))
            if r > 5:
                pygame.draw.ellipse(surface, (*_NS_nyxraal.PALETTE["abyss_darkest"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 4)
                pygame.draw.ellipse(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], alpha),
                                    (x - r + 4, y + 40 - r // 3 + 3, r * 2 - 8, r * 2 // 3 - 6), 3)
                pygame.draw.ellipse(surface, (*_NS_nyxraal.PALETTE["abyss_mid"], alpha),
                                    (x - r + 8, y + 40 - r // 3 + 6, r * 2 - 16, r * 2 // 3 - 12), 2)
                pygame.draw.ellipse(surface, (*_NS_nyxraal.PALETTE["abyss_light"], alpha),
                                    (x - r + 12, y + 40 - r // 3 + 9, r * 2 - 24, r * 2 // 3 - 18), 1)
    def _draw_abyss_descent(surface, boss, x, y, timer, phase):
        """Jump aura + slam explosion."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Jump aura (purple energy trail below boss going up).
            jump_t = progress / 0.5
            # Body offset (already handled in main).
            # Draw energy stream from ground to boss.
            for i in range(6):
                stream_t = (jump_t * 2 + i * 0.15) % 1.0
                stream_y = y + 40 - int(stream_t * 60)
                stream_alpha = _NS_nyxraal._alpha(200 * (1 - stream_t))
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], stream_alpha),
                                      (x + int(math.sin(phase * 3 + i) * 4), stream_y), 4)
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_mid"], stream_alpha),
                                      (x + int(math.sin(phase * 3 + i) * 4), stream_y - 1), 3)
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"],
                                 (x + int(math.sin(phase * 3 + i) * 4), stream_y - 1, 1, 1))
        elif progress < 0.7:
            # Falling — sword falling with target reticle on ground.
            fall_t = (progress - 0.5) / 0.2
            # Target reticle on ground.
            reticle_r = int(30 * fall_t)
            alpha = _NS_nyxraal._alpha(200)
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_light"], alpha),
                                  (x, y + 40), reticle_r, 2)
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha),
                                  (x, y + 40), reticle_r - 3, 1)
            # Crosshair.
            pygame.draw.line(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha),
                             (x - reticle_r, y + 40), (x + reticle_r, y + 40), 1)
            pygame.draw.line(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha),
                             (x, y + 40 - reticle_r // 2), (x, y + 40 + reticle_r // 2), 1)
        else:
            # SLAM burst! Purple explosion radiating outward.
            slam_t = (progress - 0.7) / 0.3
            burst_r = int(30 + slam_t * 60)
            alpha = _NS_nyxraal._alpha(255 * (1 - slam_t))
            # Big radial explosion.
            for r in range(burst_r, 0, -3):
                r_alpha = _NS_nyxraal._alpha(alpha * (burst_r - r) / burst_r)
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_darkest"], r_alpha), (x, y + 40), r)
            for r in range(burst_r - 5, 0, -3):
                r_alpha = _NS_nyxraal._alpha(alpha * (burst_r - r) / burst_r * 1.3)
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_dark"], r_alpha), (x, y + 40), r)
            for r in range(burst_r - 12, 0, -2):
                r_alpha = _NS_nyxraal._alpha(alpha * (burst_r - r) / burst_r * 1.5)
                _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_mid"], r_alpha), (x, y + 40), r)
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_light"], alpha), (x, y + 40),
                                  max(1, burst_r // 3))
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha), (x, y + 40),
                                  max(1, burst_r // 5))
            _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["white"], alpha), (x, y + 40),
                                  max(1, burst_r // 8))
            # Radial spikes shooting outward.
            for i in range(16):
                spike_a = i * math.pi / 8
                spike_r_end = burst_r + int(slam_t * 20)
                sp_x1 = x + int(math.cos(spike_a) * burst_r * 0.6)
                sp_y1 = y + 40 + int(math.sin(spike_a) * burst_r * 0.4)
                sp_x2 = x + int(math.cos(spike_a) * spike_r_end)
                sp_y2 = y + 40 + int(math.sin(spike_a) * spike_r_end * 0.6)
                pygame.draw.line(surface, (*_NS_nyxraal.PALETTE["abyss_hot"], alpha), (sp_x1, sp_y1), (sp_x2, sp_y2), 3)
                pygame.draw.line(surface, (*_NS_nyxraal.PALETTE["white"], alpha), (sp_x1, sp_y1), (sp_x2, sp_y2), 1)
                pygame.draw.rect(surface, _NS_nyxraal.PALETTE["white"], (sp_x2, sp_y2, 2, 2))
            # Rising smoke/energy pillars.
            for i in range(8):
                pillar_a = i * math.pi / 4 + phase
                pillar_r = int(burst_r * 0.7)
                px = x + int(math.cos(pillar_a) * pillar_r)
                py = y + 40 + int(math.sin(pillar_a) * pillar_r * 0.5)
                for layer in range(5):
                    layer_t = (phase + i * 0.2 + layer * 0.15) % 1.0
                    pill_y = py - int(layer_t * 30)
                    pill_alpha = _NS_nyxraal._alpha(200 * (1 - layer_t) * alpha / 255)
                    _NS_nyxraal._aacircle(surface, (*_NS_nyxraal.PALETTE["abyss_mid"], pill_alpha), (px, pill_y), 3)
                    pygame.draw.rect(surface, _NS_nyxraal.PALETTE["abyss_hot"], (px, pill_y - 1, 1, 1))



# ====================================================================
# XARNTHUUL (VOID SOVEREIGN) - Mini Boss
# ====================================================================

class _NS_xarnthuul:
    """Namespace xarnthuul - Void Sovereign boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Void body (deep purple to violet)
        "void_darkest": (8, 3, 18),
        "void_dark": (25, 12, 50),
        "void_mid": (55, 28, 95),
        "void_light": (110, 65, 170),
        "void_edge": (165, 115, 220),
        "void_shine": (215, 180, 245),
        # Cosmic energy (bright violet/magenta)
        "cosmic_darkest": (20, 5, 35),
        "cosmic_dark": (70, 20, 120),
        "cosmic_mid": (140, 55, 200),
        "cosmic_light": (200, 120, 245),
        "cosmic_hot": (235, 180, 255),
        "cosmic_shine": (250, 225, 255),
        # Star white (highlights, eyes)
        "star_dim": (180, 170, 220),
        "star_mid": (220, 210, 245),
        "star_bright": (250, 245, 255),
        # Eye (glowing white-violet)
        "eye_socket": (5, 2, 10),
        "eye_darkest": (30, 10, 55),
        "eye_dark": (90, 40, 150),
        "eye_mid": (180, 130, 230),
        "eye_light": (230, 200, 250),
        "eye_glow": (255, 240, 255),
        # Gauntlets/bracers (dark metal with gold)
        "metal_dark": (30, 25, 40),
        "metal_mid": (70, 60, 85),
        "metal_light": (130, 115, 150),
        "gold_dark": (90, 65, 20),
        "gold_mid": (180, 140, 55),
        "gold_light": (240, 210, 120),
        # Smoke/tail (dissipating body)
        "smoke_darkest": (10, 5, 20),
        "smoke_dark": (35, 20, 60),
        "smoke_mid": (75, 45, 115),
        "smoke_light": (140, 100, 180),
        # Black hole
        "hole_core": (0, 0, 0),
        "hole_ring": (15, 5, 30),
        "hole_glow": (80, 30, 140),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xarnthuul._clamp(color)
        if _NS_xarnthuul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xarnthuul._clamp(color)
        if _NS_xarnthuul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xarnthuul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xarnthuul(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xarnthuul._detect_moving(boss)
        _NS_xarnthuul._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_xarnthuul._draw_void_aura(surface, x, y, pulse)
        _NS_xarnthuul._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_xarnthuul._draw_spawn_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xarnthuul._draw_singularity_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xarnthuul._draw_eventhorizon_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_xarnthuul._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_xarnthuul._draw_walk(surface, boss, x, y)
        else:
            _NS_xarnthuul._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_xarnthuul._draw_voidlance_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xarnthuul._draw_spawn_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xarnthuul._draw_singularity_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xarnthuul._draw_eventhorizon_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        # Trigger attack when timer close to end of cooldown
        # Timer counts UP from 0 to cooldown
        active = bool(getattr(boss, "_xt_attack_active", False))
        # Start attack when timer resets to 0 (fresh cycle) or first frame
        if not active and timer <= 2:
            boss._xt_attack_active = True
            boss._xt_attack_frame = 0
            active = True
        if active:
            boss._xt_attack_frame = int(getattr(boss, "_xt_attack_frame", 0)) + 1
            # End attack when frames complete
            if boss._xt_attack_frame >= cooldown:
                boss._xt_attack_active = False
                boss._xt_attack_frame = 0
                active = False
        boss._xt_previous_timer = timer
        boss._xt_attack_progress = (
            min(1.0, getattr(boss, "_xt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_xt_last_x"):
            boss._xt_last_x = boss.x
            boss._xt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xt_last_x)
        dy = abs(boss.y - boss._xt_last_y)
        boss._xt_last_x = boss.x
        boss._xt_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Floating bob - more pronounced
        bob = int(math.sin(boss.pulse * 0.6) * 6)
        _NS_xarnthuul._draw_shadow(surface, x, y + 50)
        _NS_xarnthuul._draw_smoke_tail(surface, x, y + 20 + bob, boss.pulse, intense=False)
        _NS_xarnthuul._draw_body(surface, x, y + bob,
                        boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        # Floating drift - bob + slight sway
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_xarnthuul._draw_shadow(surface, x + sway, y + 50)
        _NS_xarnthuul._draw_smoke_tail(surface, x + sway, y + 20 + bob, phase,
                                       intense=True, facing=boss.direction, moving=True)
        _NS_xarnthuul._draw_body(surface, x + sway, y + bob,
                        boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_xt_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Charge arms back → thrust forward → recover (with float)
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3) + bob
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
            lift = int(3 - t * 4) + bob
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(7 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1) + bob
        _NS_xarnthuul._draw_shadow(surface, x + lunge, y + 50)
        _NS_xarnthuul._draw_smoke_tail(surface, x + lunge, y + 20 + lift, boss.pulse,
                                       intense=True)
        _NS_xarnthuul._draw_body(surface, x + lunge, y + lift,
                        boss.direction, boss.pulse, "attack", progress)
        # Ranged projectile (auto-attack)
        _NS_xarnthuul._draw_void_projectile(surface, boss, x + lunge, y + lift, progress)
    # ============================================================
    # BODY - Humanoid Void Being
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw humanoid void body: torso, arms, head, hood, no legs (smoke)."""
        # Torso first
        _NS_xarnthuul._draw_torso(surface, cx, cy, facing, phase)
        # Arms (behind torso for far, over torso for near)
        _NS_xarnthuul._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head + hood
        _NS_xarnthuul._draw_head(surface, cx, cy - 22, facing, phase)
        # Cosmic energy wisps around body
        _NS_xarnthuul._draw_body_wisps(surface, cx, cy, facing, phase)
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular void torso."""
        breath = math.sin(phase * 0.7) * 1
        # Main torso shape (broad shoulders, narrower waist)
        torso_shape = [
            (cx - 14, cy - 10),   # left shoulder
            (cx - 16, cy - 6),
            (cx - 15, cy),
            (cx - 13, cy + 8),
            (cx - 10, cy + 14),   # left waist
            (cx - 5, cy + 18),
            (cx + 5, cy + 18),
            (cx + 10, cy + 14),
            (cx + 13, cy + 8),
            (cx + 15, cy),
            (cx + 16, cy - 6),
            (cx + 14, cy - 10),   # right shoulder
            (cx + 8, cy - 13),
            (cx - 8, cy - 13),
        ]
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in torso_shape])
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_darkest"], torso_shape)
        # Dark void skin base
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_dark"], [
            (cx - 13, cy - 9),
            (cx - 15, cy - 5),
            (cx - 14, cy + 1),
            (cx - 12, cy + 8),
            (cx - 9, cy + 13),
            (cx - 4, cy + 16),
            (cx + 4, cy + 16),
            (cx + 9, cy + 13),
            (cx + 12, cy + 8),
            (cx + 14, cy + 1),
            (cx + 15, cy - 5),
            (cx + 13, cy - 9),
            (cx + 7, cy - 12),
            (cx - 7, cy - 12),
        ])
        # Mid tone (muscle definition)
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_mid"], [
            (cx - 11, cy - 7),
            (cx - 12, cy - 2),
            (cx - 10, cy + 5),
            (cx - 7, cy + 11),
            (cx + 7, cy + 11),
            (cx + 10, cy + 5),
            (cx + 12, cy - 2),
            (cx + 11, cy - 7),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ])
        # Chest muscle highlights
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_light"], [
            (cx - 8, cy - 6),
            (cx - 2, cy - 8),
            (cx - 1, cy - 3),
            (cx - 6, cy - 1),
        ])
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_light"], [
            (cx + 2, cy - 8),
            (cx + 8, cy - 6),
            (cx + 6, cy - 1),
            (cx + 1, cy - 3),
        ])
        # Abs
        for i, y_off in enumerate((2, 6, 10)):
            pygame.draw.line(surface, _NS_xarnthuul.PALETTE["void_darkest"],
                             (cx - 5 + i, cy + y_off),
                             (cx + 5 - i, cy + y_off), 1)
        # Center chest cosmic scar/glow
        glow_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_xarnthuul._alpha(200 * (5 - r) / 5 * glow_pulse)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_mid"], alpha),
                                    (cx, cy - 2), r)
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_light"], (cx, cy - 2), 2)
        pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (cx, cy - 2, 1, 1))
        # Cosmic runes/scars on torso
        for i, (rx, ry) in enumerate([(-6, 4), (5, 5), (-3, 9), (4, 10)]):
            alpha = _NS_xarnthuul._alpha(180 * glow_pulse)
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                             (cx + rx, cy + ry, 2, 1))
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                             (cx + rx, cy + ry, 1, 1))
        # Shoulder edges highlight
        pygame.draw.line(surface, _NS_xarnthuul.PALETTE["void_edge"],
                         (cx - 14, cy - 9), (cx - 15, cy - 5), 1)
        pygame.draw.line(surface, _NS_xarnthuul.PALETTE["void_edge"],
                         (cx + 14, cy - 9), (cx + 15, cy - 5), 1)
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms extending down, with gauntlets."""
        arm_sway = math.sin(phase * 0.5) * 2
        # Attack pose: arms forward
        if action == "attack":
            if attack_progress < 0.35:
                arm_forward = -int(attack_progress / 0.35 * 3) * facing
                arm_raise = int(attack_progress / 0.35 * 4)
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_forward = int((-3 + t * 14)) * facing
                arm_raise = int(4 - t * 5)
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_forward = int(11 * (1 - t)) * facing
                arm_raise = int(-1 + t * 1)
        else:
            arm_forward = 0
            arm_raise = int(arm_sway)
        # Both arms (far arm drawn first, near arm drawn on top)
        for side_i, side in enumerate([-1, 1]):
            is_far = (side == -facing) if action != "attack" else (side_i == 0)
            depth_shade = 0.75 if is_far else 1.0
            # Shoulder joint
            shoulder_x = cx + side * 13
            shoulder_y = cy - 8
            # Elbow (bent)
            if action == "attack" and side == facing:
                elbow_x = shoulder_x + side * 6 + arm_forward // 2
                elbow_y = shoulder_y + 4 - arm_raise
                hand_x = elbow_x + side * 8 + arm_forward // 2
                hand_y = elbow_y + 2 - arm_raise // 2
            else:
                elbow_x = shoulder_x + side * 4
                elbow_y = shoulder_y + 8 + int(arm_sway)
                hand_x = elbow_x + side * 3
                hand_y = elbow_y + 10
            # Upper arm
            _NS_xarnthuul._draw_arm_segment(
                surface, shoulder_x, shoulder_y, elbow_x, elbow_y,
                thickness=6, depth_shade=depth_shade
            )
            # Forearm
            _NS_xarnthuul._draw_arm_segment(
                surface, elbow_x, elbow_y, hand_x, hand_y,
                thickness=5, depth_shade=depth_shade
            )
            # Gauntlet at wrist
            _NS_xarnthuul._draw_gauntlet(surface, hand_x, hand_y, side, depth_shade)
            # Claw hand
            _NS_xarnthuul._draw_claw_hand(surface, hand_x, hand_y + 4, side,
                                          facing, phase, depth_shade)
    def _draw_arm_segment(surface, x1, y1, x2, y2, thickness, depth_shade=1.0):
        """Muscular arm segment."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Shadow
        _NS_xarnthuul._aaline(surface, _NS_xarnthuul.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), thickness + 1)
        # Base
        _NS_xarnthuul._aaline(surface, shade(_NS_xarnthuul.PALETTE["void_darkest"]),
                (x1, y1), (x2, y2), thickness)
        _NS_xarnthuul._aaline(surface, shade(_NS_xarnthuul.PALETTE["void_dark"]),
                (x1, y1), (x2, y2), max(1, thickness - 2))
        # Highlight
        _NS_xarnthuul._aaline(surface, shade(_NS_xarnthuul.PALETTE["void_mid"]),
                (x1, y1 - 1), (x2, y2 - 1), max(1, thickness - 4))
    def _draw_gauntlet(surface, cx, cy, side, depth_shade=1.0):
        """Gold-trimmed dark gauntlet at wrist."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Base gauntlet
        pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["metal_dark"]),
                         (cx - 4, cy - 2, 8, 6))
        pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["metal_mid"]),
                         (cx - 3, cy - 1, 6, 4))
        pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["metal_light"]),
                         (cx - 3, cy - 1, 6, 1))
        # Gold trim
        pygame.draw.line(surface, shade(_NS_xarnthuul.PALETTE["gold_dark"]),
                         (cx - 4, cy + 3), (cx + 4, cy + 3), 1)
        pygame.draw.line(surface, shade(_NS_xarnthuul.PALETTE["gold_mid"]),
                         (cx - 4, cy - 2), (cx + 4, cy - 2), 1)
        pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["gold_light"]),
                         (cx + side * 2, cy, 1, 1))
    def _draw_claw_hand(surface, cx, cy, side, facing, phase, depth_shade=1.0):
        """Clawed hand with cosmic energy."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Palm
        pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["void_darkest"]),
                         (cx - 3, cy - 2, 6, 5))
        pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["void_dark"]),
                         (cx - 2, cy - 1, 4, 4))
        # 3 claws
        for i, off in enumerate([-2, 0, 2]):
            claw_x = cx + off
            claw_tip_y = cy + 5
            pygame.draw.line(surface, shade(_NS_xarnthuul.PALETTE["void_darkest"]),
                             (claw_x, cy + 2), (claw_x, claw_tip_y), 2)
            pygame.draw.line(surface, shade(_NS_xarnthuul.PALETTE["void_light"]),
                             (claw_x, cy + 2), (claw_x, claw_tip_y), 1)
            pygame.draw.rect(surface, shade(_NS_xarnthuul.PALETTE["cosmic_light"]),
                             (claw_x, claw_tip_y, 1, 1))
        # Cosmic aura in palm
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        alpha = _NS_xarnthuul._alpha(180 * pulse)
        _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_mid"], alpha),
                                (cx, cy + 1), 2)
        pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (cx, cy + 1, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Hooded head with glowing eyes."""
        # Hood shape (larger than head, cowl-like)
        hood_shape = [
            (cx - 12, cy + 6),
            (cx - 13, cy + 2),
            (cx - 11, cy - 5),
            (cx - 6, cy - 10),
            (cx, cy - 12),
            (cx + 6, cy - 10),
            (cx + 11, cy - 5),
            (cx + 13, cy + 2),
            (cx + 12, cy + 6),
            (cx + 8, cy + 8),
            (cx - 8, cy + 8),
        ]
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in hood_shape])
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_darkest"], hood_shape)
        # Hood interior darker
        interior = [
            (cx - 9, cy + 5),
            (cx - 10, cy + 1),
            (cx - 8, cy - 4),
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 8, cy - 4),
            (cx + 10, cy + 1),
            (cx + 9, cy + 5),
        ]
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["shadow"], interior)
        # Hood edge highlight
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_dark"], [
            (cx - 12, cy + 6),
            (cx - 13, cy + 2),
            (cx - 11, cy - 5),
            (cx - 6, cy - 10),
            (cx, cy - 12),
            (cx - 2, cy - 10),
            (cx - 8, cy - 6),
            (cx - 10, cy - 1),
            (cx - 10, cy + 5),
        ])
        # Cosmic edge glow around hood
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for i, (px, py) in enumerate([(cx - 11, cy - 4), (cx - 5, cy - 9),
                                      (cx + 5, cy - 9), (cx + 11, cy - 4)]):
            alpha = _NS_xarnthuul._alpha(160 * pulse)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                    (px, py), 2)
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                             (px, py, 1, 1))
        # Head shape inside hood (barely visible)
        _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["void_darkest"], [
            (cx - 6, cy + 4),
            (cx - 7, cy - 2),
            (cx - 5, cy - 6),
            (cx + 5, cy - 6),
            (cx + 7, cy - 2),
            (cx + 6, cy + 4),
            (cx, cy + 6),
        ])
        # GLOWING EYES (2 bright void eyes)
        _NS_xarnthuul._draw_void_eyes(surface, cx, cy - 1, phase)
    def _draw_void_eyes(surface, cx, cy, phase):
        """Two glowing violet eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 3):
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_xarnthuul._alpha(100 * (5 - r) / 5 * pulse)
                _NS_xarnthuul._aacircle(surface,
                                        (*_NS_xarnthuul.PALETTE["cosmic_mid"], alpha),
                                        (eye_x, cy), r)
            # Bright eye
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 1, 2, 2))
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["eye_light"],
                             (eye_x - 1, cy - 1, 2, 1))
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["eye_glow"],
                             (eye_x, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["white"], (eye_x, cy - 1, 1, 1))
    def _draw_body_wisps(surface, cx, cy, facing, phase):
        """Cosmic energy wisps floating around body."""
        for i in range(6):
            wisp_t = (phase * 0.4 + i * 0.16) % 1.0
            angle = phase * 0.3 + i * math.pi / 3
            radius = 20 + int(wisp_t * 8)
            wx = cx + int(math.cos(angle) * radius)
            wy = cy - 5 + int(math.sin(angle) * radius * 0.6)
            alpha = _NS_xarnthuul._alpha(200 * (1 - wisp_t))
            if alpha > 0:
                _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_shine"], alpha),
                                 (wx, wy - 1, 1, 1))
    # ============================================================
    # SMOKE TAIL (floating body dissipating below)
    # ============================================================
    def _draw_smoke_tail(surface, cx, cy, phase, intense=False, facing=1, moving=False):
        """Smoke/cosmic energy where legs would be."""
        strength = 1.3 if intense else 1.0
        # Main smoke plume
        smoke = pygame.Surface((80, 60), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Layered smoke ellipses
        for radius in range(22, 3, -2):
            alpha = _NS_xarnthuul._alpha((22 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_xarnthuul.PALETTE["smoke_darkest"], alpha),
                    (40 - radius, 25 - radius // 2,
                     radius * 2, max(3, radius)),
                )
        for radius in range(16, 3, -2):
            alpha = _NS_xarnthuul._alpha((16 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_xarnthuul.PALETTE["smoke_dark"], alpha),
                    (40 - radius, 25 - radius // 2,
                     radius * 2, max(3, radius)),
                )
        for radius in range(10, 2, -1):
            alpha = _NS_xarnthuul._alpha((10 - radius) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_xarnthuul.PALETTE["smoke_mid"], alpha),
                    (40 - radius, 25 - radius // 2,
                     radius * 2, max(2, radius)),
                )
        surface.blit(smoke, (cx - 40, cy - 10))
        # Rising cosmic particles from smoke
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            px = cx - 20 + i * 4 + int(math.sin(phase + i) * 3)
            py = cy + 15 - int(t * 20)
            alpha = _NS_xarnthuul._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_mid"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                 (px, py, 1, 1))
        # Purple wisps swirling down
        for i in range(8):
            angle = phase * 0.6 + i * math.pi / 4
            radius = 12 + int(math.sin(phase + i) * 4)
            wx = cx + int(math.cos(angle) * radius)
            wy = cy + 15 + int(math.sin(angle) * radius * 0.3)
            alpha = _NS_xarnthuul._alpha(180 * strength)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["smoke_mid"], alpha),
                                    (wx, wy), 2)
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                             (wx, wy, 1, 1))
        # Trail when moving
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + 12 + int(math.sin(phase + i) * 2)
                alpha = _NS_xarnthuul._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["smoke_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["smoke_mid"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AUTO-ATTACK - VOID PROJECTILE (ranged)
    # ============================================================
    def _draw_void_projectile(surface, boss, x, y, progress):
        """Void energy orb projectile launched from hand."""
        # Charge phase (hand glows)
        facing = boss.direction
        hand_x = x + facing * 14
        hand_y = y - 2
        if progress < 0.35:
            # Charge glow in hand
            t = progress / 0.35
            cr = int(2 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_xarnthuul._alpha(180 * (cr + 3 - r) / (cr + 3) * t)
                _NS_xarnthuul._aacircle(surface,
                                        (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_mid"],
                                    (hand_x, hand_y), max(1, cr - 2))
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_light"],
                                    (hand_x, hand_y), max(1, cr - 4))
            # Sparks
            for i in range(4):
                angle = progress * 20 + i * math.pi / 2
                sx = hand_x + int(math.cos(angle) * (cr + 2))
                sy = hand_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_hot"], (sx, sy, 1, 1))
            return
        # Launch + travel phase
        if progress < 0.5:
            return
        tx, ty = _NS_xarnthuul._target_position(boss, x, y)
        start_x = x + facing * 18
        start_y = y - 2
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_xarnthuul._alpha(230 - i * 28)
            size = max(1, 6 - i)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_darkest"], alpha),
                                    (px, py), size)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                    (px, py), max(1, size - 3))
            # Sparks around trail
            if i < 3:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_xarnthuul.PALETTE["cosmic_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright bolt head
        for r in range(10, 3, -1):
            alpha = _NS_xarnthuul._alpha(80 * (10 - r) / 10)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                    (bx, by), r)
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_darkest"], (bx, by), 7)
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_dark"], (bx, by), 5)
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_mid"], (bx, by), 3)
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_light"], (bx, by), 2)
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["white"], (bx, by, 1, 1))
        # Impact splash
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(6 + st * 20)
            alpha = _NS_xarnthuul._alpha(240 * (1 - st))
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_mid"], alpha),
                                    (tx, ty), max(1, radius - 4), 2)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                    (tx, ty), max(1, radius - 8), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        """Ground shadow (blurry since boss is floating)."""
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 12)  # softer than grounded boss
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 15, 140), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (40, 20, 80, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_void_aura(surface, x, y, phase):
        """Large cosmic void aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        # Outer smoke
        for radius in range(100, 5, -5):
            alpha = _NS_xarnthuul._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_xarnthuul._aacircle(aura, (*_NS_xarnthuul.PALETTE["smoke_darkest"], alpha),
                                        (120, 100), radius)
        # Mid smoke
        for radius in range(70, 5, -4):
            alpha = _NS_xarnthuul._alpha((70 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xarnthuul._aacircle(aura, (*_NS_xarnthuul.PALETTE["void_dark"], alpha),
                                        (120, 100), radius)
        # Inner cosmic
        for radius in range(40, 5, -3):
            alpha = _NS_xarnthuul._alpha((40 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_xarnthuul._aacircle(aura, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                        (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating stars around
        for i in range(18):
            angle = phase * 0.25 + i * math.pi / 9
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            twinkle = math.sin(phase * 3 + i) * 0.5 + 0.5
            alpha = _NS_xarnthuul._alpha(220 * twinkle)
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["star_dim"], alpha),
                             (sx, sy, 1, 1))
            if twinkle > 0.7:
                pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["star_bright"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xarnthuul.PALETTE["void_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_xarnthuul.PALETTE["cosmic_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_xarnthuul.PALETTE["cosmic_mid"], 180),
                            (25, 24, 130, 20), 1)
        # Runes
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_xarnthuul.PALETTE["cosmic_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_xarnthuul.PALETTE["cosmic_hot"],
                                       _NS_xarnthuul._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q - VOIDLANCE (ranged beam projectile)
    # ============================================================
    def _draw_voidlance_skill(surface, boss, x, y, timer, phase):
        """Void energy beam draining life from target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xarnthuul._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in hand
            t = progress / 0.2
            hand_x = x + facing * 14
            hand_y = y - 2
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_xarnthuul._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_darkest"], alpha),
                                        (hand_x, hand_y), r)
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_mid"], (hand_x, hand_y), cr - 2)
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_light"], (hand_x, hand_y),
                      max(1, cr - 4))
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (hand_x, hand_y),
                      max(1, cr - 6))
            # Sparks
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_hot"], (sx, sy, 1, 1))
        else:
            # Continuous beam from hand to target
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 16
            start_y = y - 2
            # Multi-layered beam
            beam_wobble = math.sin(phase * 8) * 2
            for layer_i, (width, alpha_val) in enumerate([
                (8, 100), (6, 140), (4, 180), (2, 220), (1, 255)
            ]):
                actual_alpha = _NS_xarnthuul._alpha(alpha_val)
                colors = [
                    _NS_xarnthuul.PALETTE["cosmic_darkest"],
                    _NS_xarnthuul.PALETTE["cosmic_dark"],
                    _NS_xarnthuul.PALETTE["cosmic_mid"],
                    _NS_xarnthuul.PALETTE["cosmic_light"],
                    _NS_xarnthuul.PALETTE["cosmic_shine"],
                ]
                color = colors[min(layer_i, 4)]
                # Wobbled midpoint for organic beam
                mid_x = (start_x + tx) // 2
                mid_y = (start_y + ty) // 2 + int(beam_wobble)
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (mid_x, mid_y), width)
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (mid_x, mid_y), (tx, ty), width)
            # Energy particles flowing along beam TOWARD boss (draining)
            for i in range(8):
                flow_t = ((phase * 1.5 - i * 0.12) % 1.0)
                px = int(tx + (start_x - tx) * flow_t)
                py = int(ty + (start_y - ty) * flow_t)
                pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_hot"], (px, py, 2, 2))
                pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (px, py, 1, 1))
            # Impact glow at target
            impact_r = int(8 + math.sin(phase * 5) * 3)
            for r in range(impact_r + 3, 0, -1):
                alpha = _NS_xarnthuul._alpha(180 * (impact_r + 3 - r) / (impact_r + 3))
                _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], alpha),
                                        (tx, ty), r)
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_mid"], (tx, ty), impact_r - 2)
            _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["cosmic_light"], (tx, ty), impact_r - 4)
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (tx, ty, 1, 1))
            # Draining wisps rising from target
            for i in range(5):
                wisp_t = (phase * 0.8 + i * 0.2) % 1.0
                wx = tx + int(math.sin(phase + i) * 8)
                wy = ty - int(wisp_t * 15)
                alpha = _NS_xarnthuul._alpha(200 * (1 - wisp_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                                     (wx, wy, 1, 1))
    # ============================================================
    # SKILL W - ABYSSAL SPAWN (summon minions)
    # ============================================================
    def _draw_spawn_ground(surface, boss, x, y, timer, phase):
        """Portal circles on ground where minions spawn."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Spawn 3 minion portals in front of boss
        for i in range(3):
            offset_x = 40 + i * 30
            portal_x = x + offset_x * facing
            portal_y = y + 40
            # Growing portal
            r = int(15 * min(1.0, progress * 2))
            if r > 2:
                pygame.draw.ellipse(surface, _NS_xarnthuul.PALETTE["shadow"],
                                    (portal_x - r, portal_y - r // 3,
                                     r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, _NS_xarnthuul.PALETTE["cosmic_darkest"],
                                    (portal_x - r + 1, portal_y - r // 3 + 1,
                                     r * 2 - 2, r * 2 // 3 - 2))
                pygame.draw.ellipse(surface, _NS_xarnthuul.PALETTE["cosmic_dark"],
                                    (portal_x - r + 3, portal_y - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4))
                # Rotating rune
                for j in range(6):
                    angle = phase * 2 + j * math.pi / 3
                    px = portal_x + int(math.cos(angle) * r)
                    py = portal_y + int(math.sin(angle) * r * 0.4)
                    pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_light"], (px, py, 2, 2))
    def _draw_spawn_foreground(surface, boss, x, y, timer, phase):
        """Mini eidolons rising from portals."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.4:
            return
        # Rising minions
        rise_t = (progress - 0.4) / 0.6
        for i in range(3):
            offset_x = 40 + i * 30
            mx = x + offset_x * facing
            my = y + 40 - int(rise_t * 25)
            # Small void minion body
            _NS_xarnthuul._draw_mini_eidolon(surface, mx, my, phase, rise_t)
    def _draw_mini_eidolon(surface, cx, cy, phase, alpha_t):
        """Small version of void being."""
        alpha_mult = min(1.0, alpha_t * 2)
        base_alpha = _NS_xarnthuul._alpha(255 * alpha_mult)
        # Small torso
        _NS_xarnthuul._poly(surface, (*_NS_xarnthuul.PALETTE["void_darkest"], base_alpha), [
            (cx - 4, cy - 3), (cx - 5, cy),
            (cx - 3, cy + 5), (cx + 3, cy + 5),
            (cx + 5, cy), (cx + 4, cy - 3),
            (cx + 2, cy - 5), (cx - 2, cy - 5),
        ])
        _NS_xarnthuul._poly(surface, (*_NS_xarnthuul.PALETTE["void_dark"], base_alpha), [
            (cx - 3, cy - 2), (cx - 4, cy),
            (cx - 2, cy + 4), (cx + 2, cy + 4),
            (cx + 4, cy), (cx + 3, cy - 2),
            (cx + 1, cy - 4), (cx - 1, cy - 4),
        ])
        _NS_xarnthuul._poly(surface, (*_NS_xarnthuul.PALETTE["void_mid"], base_alpha), [
            (cx - 2, cy - 1), (cx - 2, cy + 2),
            (cx + 2, cy + 2), (cx + 2, cy - 1),
        ])
        # Small glowing eyes
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_alpha = _NS_xarnthuul._alpha(255 * alpha_mult * pulse)
        pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], eye_alpha),
                         (cx - 2, cy - 3, 1, 1))
        pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_shine"], eye_alpha),
                         (cx + 1, cy - 3, 1, 1))
        # Small smoke tail below
        for i in range(3):
            t = (phase * 0.6 + i * 0.2) % 1.0
            sy = cy + 6 + int(t * 6)
            alpha = _NS_xarnthuul._alpha(180 * (1 - t) * alpha_mult)
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["smoke_mid"], alpha),
                                    (cx, sy), 2)
    # ============================================================
    # SKILL E - SINGULARITY PULSE (AoE spikes)
    # ============================================================
    def _draw_singularity_ground(surface, boss, x, y, timer, phase):
        """Ground pulse rings."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse_r = int(60 * min(1.0, progress * 1.5))
        if pulse_r > 3:
            pygame.draw.ellipse(surface, (*_NS_xarnthuul.PALETTE["cosmic_darkest"], 180),
                                (x - pulse_r, y + 46 - pulse_r // 3,
                                 pulse_r * 2, pulse_r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_xarnthuul.PALETTE["cosmic_dark"], 200),
                                (x - pulse_r + 3, y + 46 - pulse_r // 3 + 2,
                                 pulse_r * 2 - 6, pulse_r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_xarnthuul.PALETTE["cosmic_mid"], 150),
                                (x - pulse_r + 8, y + 46 - pulse_r // 3 + 4,
                                 pulse_r * 2 - 16, pulse_r * 2 // 3 - 8), 1)
    def _draw_singularity_foreground(surface, boss, x, y, timer, phase):
        """Void spikes erupting from ground."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple spikes at various positions in ring
        num_spikes = 12
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + phase * 0.1
            spike_delay = (i / num_spikes) * 0.3
            spike_progress = max(0.0, (progress - spike_delay) / max(0.01, 1 - spike_delay))
            if spike_progress <= 0:
                continue
            radius = 40 + (i % 3) * 8
            base_x = x + int(math.cos(angle) * radius)
            base_y = y + 46 + int(math.sin(angle) * radius * 0.4)
            # Spike height (grows then shrinks)
            if spike_progress < 0.5:
                height = int(spike_progress * 2 * 25)
            else:
                height = int((1 - (spike_progress - 0.5) * 2) * 25)
            height = max(0, height)
            if height < 2:
                continue
            tip_y = base_y - height
            # Draw spike
            _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["shadow_deep"], [
                (base_x + 1, tip_y + 1),
                (base_x - 3, base_y + 1),
                (base_x + 3, base_y + 1),
            ])
            _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["cosmic_darkest"], [
                (base_x, tip_y),
                (base_x - 3, base_y),
                (base_x + 3, base_y),
            ])
            _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["cosmic_dark"], [
                (base_x, tip_y),
                (base_x - 2, base_y),
                (base_x + 2, base_y),
            ])
            _NS_xarnthuul._poly(surface, _NS_xarnthuul.PALETTE["cosmic_mid"], [
                (base_x, tip_y),
                (base_x - 1, base_y),
                (base_x + 1, base_y),
            ])
            # Bright tip
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_light"], (base_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["cosmic_shine"], (base_x, tip_y, 1, 1))
            # Glow at tip
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_hot"], 150),
                                    (base_x, tip_y), 2)
    # ============================================================
    # SKILL R - EVENT HORIZON (black hole)
    # ============================================================
    def _draw_eventhorizon_ground(surface, boss, x, y, timer, phase):
        """Growing dark void on ground."""
        tx, ty = _NS_xarnthuul._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, _NS_xarnthuul.PALETTE["shadow"],
                                (tx - r - 2, ty - r // 3 - 1,
                                 r * 2 + 4, r * 2 // 3 + 2))
            pygame.draw.ellipse(surface, _NS_xarnthuul.PALETTE["hole_ring"],
                                (tx - r, ty - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, _NS_xarnthuul.PALETTE["hole_core"],
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
    def _draw_eventhorizon_foreground(surface, boss, x, y, timer, phase):
        """Swirling black hole vortex."""
        tx, ty = _NS_xarnthuul._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 2))
        if r < 5:
            return
        # Swirling spiral arms
        num_arms = 4
        num_pts = 40
        for arm in range(num_arms):
            arm_offset = arm * math.pi * 2 / num_arms
            for i in range(num_pts):
                t = i / num_pts
                # Spiral equation
                spiral_r = r * (1 - t * 0.9)
                angle = arm_offset + t * math.pi * 3 + phase * 2
                px = tx + int(math.cos(angle) * spiral_r)
                py = ty + int(math.sin(angle) * spiral_r * 0.5)
                alpha = _NS_xarnthuul._alpha(220 * (1 - t))
                # Color varies from bright outer to dark inner
                if t < 0.3:
                    color = _NS_xarnthuul.PALETTE["cosmic_light"]
                elif t < 0.6:
                    color = _NS_xarnthuul.PALETTE["cosmic_mid"]
                elif t < 0.85:
                    color = _NS_xarnthuul.PALETTE["cosmic_dark"]
                else:
                    color = _NS_xarnthuul.PALETTE["hole_ring"]
                size = max(1, int(3 * (1 - t)))
                _NS_xarnthuul._aacircle(surface, (*color, alpha), (px, py), size)
        # Central black hole
        _NS_xarnthuul._aacircle(surface, _NS_xarnthuul.PALETTE["hole_core"], (tx, ty), r // 3)
        # Bright accretion ring at edge
        for ring_r in range(r - 2, r + 3):
            pulse = math.sin(phase * 4) * 0.3 + 0.7
            alpha = _NS_xarnthuul._alpha(200 * pulse * (1 - abs(ring_r - r) / 5))
            _NS_xarnthuul._aacircle(surface, (*_NS_xarnthuul.PALETTE["cosmic_hot"], alpha),
                                    (tx, ty), ring_r, 1)
        # Particles being sucked in
        for i in range(15):
            particle_t = ((phase * 1.2 + i * 0.07) % 1.0)
            particle_angle = i * math.pi * 2 / 15 + phase * 0.5
            particle_r = r * 1.5 * (1 - particle_t)
            px = tx + int(math.cos(particle_angle) * particle_r)
            py = ty + int(math.sin(particle_angle) * particle_r * 0.6)
            alpha = _NS_xarnthuul._alpha(240 * (1 - particle_t * 0.5))
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_light"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface, (*_NS_xarnthuul.PALETTE["cosmic_shine"], alpha),
                             (px, py, 1, 1))
        # Gravitational lensing sparkles at edge
        for i in range(10):
            angle = phase * 3 + i * math.pi / 5
            sx = tx + int(math.cos(angle) * (r + 4))
            sy = ty + int(math.sin(angle) * (r * 0.5 + 2))
            pygame.draw.rect(surface, _NS_xarnthuul.PALETTE["star_bright"], (sx, sy, 1, 1))



# ====================================================================
# ZYVARETH (STORMHERALD) - TRUE BOSS
# ====================================================================

class _NS_zyvareth:
    """Namespace zyvareth - crystal-horned lightning creature boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Teal/cyan body (main)
        "body_darkest": (5, 30, 40),
        "body_dark": (15, 75, 90),
        "body_mid": (40, 145, 165),
        "body_light": (100, 215, 225),
        "body_edge": (170, 245, 250),
        "body_shine": (230, 255, 255),
        # Belly / lighter underside
        "belly_dark": (30, 90, 105),
        "belly_mid": (85, 175, 190),
        "belly_light": (170, 235, 240),
        # Purple crystal horns/spikes (main FX)
        "crystal_darkest": (25, 5, 55),
        "crystal_dark": (75, 25, 130),
        "crystal_mid": (155, 60, 220),
        "crystal_light": (215, 130, 250),
        "crystal_hot": (245, 195, 255),
        "crystal_shine": (255, 240, 255),
        # Lightning purple (bolts, magic)
        "bolt_dark": (95, 30, 165),
        "bolt_mid": (185, 75, 245),
        "bolt_light": (230, 160, 255),
        "bolt_hot": (250, 220, 255),
        "bolt_shine": (255, 255, 255),
        # Gold saddle / ornaments
        "gold_dark": (95, 60, 15),
        "gold_mid": (185, 130, 40),
        "gold_light": (240, 195, 90),
        "gold_shine": (255, 235, 155),
        # Eye (purple glowing)
        "eye_socket": (5, 2, 15),
        "eye_dark": (55, 15, 105),
        "eye_mid": (180, 65, 240),
        "eye_light": (235, 175, 255),
        "eye_glow": (255, 255, 255),
        # Storm cloud (dark)
        "cloud_darkest": (12, 8, 25),
        "cloud_dark": (35, 25, 55),
        "cloud_mid": (75, 55, 110),
        "cloud_light": (135, 105, 180),
        # Hoof (dark grey)
        "hoof_dark": (15, 15, 25),
        "hoof_mid": (55, 55, 70),
        "hoof_light": (110, 110, 130),
        # Mist purple
        "mist_dark": (30, 15, 55),
        "mist_mid": (80, 40, 130),
        "mist_light": (165, 105, 215),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zyvareth._clamp(color)
        if _NS_zyvareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zyvareth._clamp(color)
        if _NS_zyvareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zyvareth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_zyvareth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zyvareth._detect_moving(boss)
        _NS_zyvareth._update_zy_attack_anim(boss)
        attacking = (
            getattr(boss, "_zy_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_zyvareth._draw_electric_aura(surface, x, y, pulse)
        _NS_zyvareth._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX behind body.
        if active_skill == "e":
            _NS_zyvareth._draw_stormfall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zyvareth._draw_crystal_nova_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_zyvareth._draw_zy_attack(surface, boss, x, y)
        elif moving:
            _NS_zyvareth._draw_zy_walk(surface, boss, x, y)
        else:
            _NS_zyvareth._draw_zy_idle(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_zyvareth._draw_splitbolt(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zyvareth._draw_soul_drain(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zyvareth._draw_stormfall(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zyvareth._draw_crystal_nova(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_zy_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zy_previous_timer", 0))
        active = bool(getattr(boss, "_zy_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._zy_attack_active = True
            boss._zy_attack_frame = 0
            active = True
        elif active:
            boss._zy_attack_frame = int(getattr(boss, "_zy_attack_frame", 0)) + 1
            if boss._zy_attack_frame >= cooldown:
                boss._zy_attack_active = False
                boss._zy_attack_frame = 0
                active = False
        boss._zy_previous_timer = timer
        boss._zy_attack_progress = (
            min(1.0, getattr(boss, "_zy_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zy_last_x"):
            boss._zy_last_x = boss.x
            boss._zy_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zy_last_x)
        dy = abs(boss.y - boss._zy_last_y)
        boss._zy_last_x = boss.x
        boss._zy_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_zy_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_zyvareth._draw_shadow(surface, x, y + 50)
        _NS_zyvareth._draw_electric_particles(surface, x, y + 44, boss.pulse)
        _NS_zyvareth._draw_zy_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_zy_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_zyvareth._draw_shadow(surface, x + sway, y + 50)
        _NS_zyvareth._draw_electric_particles(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_zyvareth._draw_zy_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_zy_attack(surface, boss, x, y):
        progress = getattr(boss, "_zy_attack_progress", None)
        if progress is None or progress <= 0:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Ranged cast pose: rear up slightly, cast forward.
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 5)
            lunge = 0
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            t_eased = 1 - (1 - t) ** 2
            lift = int(5 - t_eased * 3)
            lunge = int(t_eased * 4) * boss.direction
        else:
            t = (progress - 0.55) / 0.45
            lift = int(2 * (1 - t))
            lunge = int(4 * (1 - t)) * boss.direction
        _NS_zyvareth._draw_shadow(surface, x + lunge, y + 50)
        _NS_zyvareth._draw_electric_particles(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_zyvareth._draw_zy_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_zyvareth._draw_basic_bolt(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY (Quadruped) =================
    def _draw_zy_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Back legs (behind).
        _NS_zyvareth._draw_hooved_legs(surface, cx - facing * 12, cy + 12, facing, phase, action, back=True)
        # Tail behind body.
        _NS_zyvareth._draw_tuft_tail(surface, cx, cy + 4, facing, phase)
        # Main horizontal body (quadruped torso).
        _NS_zyvareth._draw_creature_body(surface, cx, cy, facing, phase)
        # Front legs.
        _NS_zyvareth._draw_hooved_legs(surface, cx + facing * 12, cy + 12, facing, phase, action, back=False)
        # Gold saddle / chest ornament.
        _NS_zyvareth._draw_gold_ornaments(surface, cx, cy - 2, facing, phase)
        # Neck (curved).
        _NS_zyvareth._draw_curved_neck(surface, cx + facing * 12, cy - 4, facing, phase, action, attack_progress)
        # Head with big crystal horns.
        _NS_zyvareth._draw_horned_head(surface, cx + facing * 22, cy - 12, facing, phase, action, attack_progress)
    def _draw_creature_body(surface, cx, cy, facing, phase):
        """Horizontal quadruped body (like a deer/gazelle)."""
        breath = math.sin(phase * 0.7) * 1
        # Body shape (elongated).
        body_shape = [
            (cx - 18, cy - 4),
            (cx - 20, cy),
            (cx - 18, cy + 6),
            (cx - 12, cy + 10),
            (cx + 12, cy + 10),
            (cx + 18, cy + 6),
            (cx + 20, cy),
            (cx + 18, cy - 4),
            (cx + 14, cy - 8),
            (cx - 14, cy - 8),
        ]
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in body_shape])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_darkest"], body_shape)
        # Dark base.
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_dark"], [
            (cx - 17, cy - 3),
            (cx - 19, cy),
            (cx - 17, cy + 5),
            (cx - 11, cy + 9),
            (cx + 11, cy + 9),
            (cx + 17, cy + 5),
            (cx + 19, cy),
            (cx + 17, cy - 3),
            (cx + 13, cy - 7),
            (cx - 13, cy - 7),
        ])
        # Mid teal.
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_mid"], [
            (cx - 14, cy - 4),
            (cx - 16, cy),
            (cx - 12, cy + 4),
            (cx + 12, cy + 4),
            (cx + 16, cy),
            (cx + 14, cy - 4),
            (cx + 10, cy - 6),
            (cx - 10, cy - 6),
        ])
        # Bright cyan highlights on top.
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_light"], [
            (cx - 10, cy - 5),
            (cx + 10, cy - 5),
            (cx + 8, cy - 3),
            (cx - 8, cy - 3),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_edge"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["body_shine"], (cx - 2, cy - 5, 4, 1))
        # Belly (lighter, bottom).
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["belly_dark"], [
            (cx - 12, cy + 5),
            (cx + 12, cy + 5),
            (cx + 10, cy + 9),
            (cx - 10, cy + 9),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["belly_mid"], [
            (cx - 10, cy + 6),
            (cx + 10, cy + 6),
            (cx + 8, cy + 8),
            (cx - 8, cy + 8),
        ])
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["belly_light"], (cx - 4, cy + 7, 8, 1))
        # SPINE CRYSTAL SPIKES along back (small purple crystals).
        for i, x_off in enumerate((-12, -6, 0, 6, 12)):
            spike_wave = math.sin(phase * 0.5 + i * 0.4) * 1
            spike_x = cx + x_off
            spike_h = 4 + i % 2
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"], [
                (spike_x - 2 + 1, cy - 8 + 1),
                (spike_x + 2 + 1, cy - 8 + 1),
                (spike_x + 1, cy - 8 - spike_h + 1 - int(spike_wave)),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_darkest"], [
                (spike_x - 2, cy - 8),
                (spike_x + 2, cy - 8),
                (spike_x, cy - 8 - spike_h - int(spike_wave)),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_dark"], [
                (spike_x - 1, cy - 8),
                (spike_x + 1, cy - 8),
                (spike_x, cy - 8 - spike_h + 1 - int(spike_wave)),
            ])
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_mid"],
                             (spike_x, cy - 8 - spike_h - int(spike_wave), 1, 1))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"],
                             (spike_x, cy - 8 - spike_h - int(spike_wave), 1, 1))
        # Scale texture (small spots on side).
        for i, (sx_off, sy_off) in enumerate([(-10, 0), (-6, 2), (-2, -1), (2, 1), (6, -1), (10, 2)]):
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["body_edge"], (cx + sx_off, cy + sy_off, 1, 1))
    def _draw_tuft_tail(surface, cx, cy, facing, phase):
        """Small tuft tail at back."""
        back_dir = -facing
        wave = math.sin(phase * 1.2) * 2
        base_x = cx + back_dir * 18
        base_y = cy + 2
        # Tail segments.
        segments = 3
        prev = (base_x, base_y)
        for seg in range(1, segments + 1):
            t = seg / segments
            bx = base_x + int(back_dir * t * 8)
            by = base_y + int(t * 3) + int(wave * t * 0.5)
            thickness = max(2, 5 - seg)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                                 (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), thickness + 1)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_darkest"],
                                 prev, (bx, by), thickness)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_dark"],
                                 prev, (bx, by), max(1, thickness - 1))
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_mid"],
                                 (prev[0], prev[1] - 1), (bx, by - 1), max(1, thickness - 2))
            prev = (bx, by)
        # Tuft at end (fluffy).
        tuft_x, tuft_y = prev
        for offset in [(-2, -1, 3), (2, -1, 3), (0, -2, 3), (0, 1, 2)]:
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["body_dark"],
                                   (tuft_x + offset[0], tuft_y + offset[1]), offset[2])
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["body_mid"],
                                   (tuft_x + offset[0], tuft_y + offset[1]), offset[2] - 1)
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["body_light"], (tuft_x, tuft_y - 1, 1, 1))
        # Small crystal at tail tip.
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_mid"], (tuft_x + 1, tuft_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"], (tuft_x + 1, tuft_y - 2, 1, 1))
    def _draw_hooved_legs(surface, cx, cy, facing, phase, action, back=True):
        """Two legs (front or back pair). cx = center between them."""
        leg_bob_offset = 0 if back else math.pi
        leg_bob = math.sin(phase * 1.5 + leg_bob_offset) * 4 if action == "walk" \
            else math.sin(phase * 0.8) * 1
        for side in (-1, 1):
            hip_x = cx + side * 2
            hip_y = cy - 4
            knee_x = cx + side * 3
            knee_y = cy + 2 + int(leg_bob * side * 0.5)
            hoof_x = cx + side * 2
            hoof_y = cy + 12 + int(leg_bob * side * 0.3)
            # Upper leg (thigh).
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                                 (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1), 5)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_darkest"],
                                 (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_dark"],
                                 (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_mid"],
                                 (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Knee joint.
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["body_darkest"], (knee_x, knee_y), 2)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["body_dark"], (knee_x, knee_y), 1)
            # Lower leg (shin, thinner).
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                                 (knee_x + 1, knee_y + 1), (hoof_x + 1, hoof_y + 1), 3)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_darkest"],
                                 (knee_x, knee_y), (hoof_x, hoof_y), 3)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_dark"],
                                 (knee_x, knee_y), (hoof_x, hoof_y), 2)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_mid"],
                                 (knee_x, knee_y - 1), (hoof_x, hoof_y - 1), 1)
            # Small purple lightning spark on knee.
            if action == "walk":
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["bolt_hot"], (knee_x, knee_y, 1, 1))
            # HOOF (dark, cloven).
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"], [
                (hoof_x - 3 + 1, hoof_y - 1 + 1),
                (hoof_x + 3 + 1, hoof_y - 1 + 1),
                (hoof_x + 2 + 1, hoof_y + 3 + 1),
                (hoof_x - 2 + 1, hoof_y + 3 + 1),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["hoof_dark"], [
                (hoof_x - 3, hoof_y - 1),
                (hoof_x + 3, hoof_y - 1),
                (hoof_x + 2, hoof_y + 3),
                (hoof_x - 2, hoof_y + 3),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["hoof_mid"], [
                (hoof_x - 2, hoof_y),
                (hoof_x + 2, hoof_y),
                (hoof_x + 1, hoof_y + 2),
                (hoof_x - 1, hoof_y + 2),
            ])
            # Central cloven split.
            pygame.draw.line(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                             (hoof_x, hoof_y - 1), (hoof_x, hoof_y + 3), 1)
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["hoof_light"], (hoof_x - 1, hoof_y, 1, 1))
            # Gold cuff at ankle.
            pygame.draw.line(surface, _NS_zyvareth.PALETTE["gold_dark"],
                             (hoof_x - 3, hoof_y - 2), (hoof_x + 3, hoof_y - 2), 1)
            pygame.draw.line(surface, _NS_zyvareth.PALETTE["gold_mid"],
                             (hoof_x - 3, hoof_y - 3), (hoof_x + 3, hoof_y - 3), 1)
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["gold_light"], (hoof_x - 1, hoof_y - 3, 2, 1))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["gold_shine"], (hoof_x, hoof_y - 3, 1, 1))
    def _draw_gold_ornaments(surface, cx, cy, facing, phase):
        """Gold saddle/breastplate with purple gem."""
        # Chest ornament (round with center gem).
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"], [
            (cx - 8 + 1, cy + 1),
            (cx + 8 + 1, cy + 1),
            (cx + 6 + 1, cy + 6 + 1),
            (cx - 6 + 1, cy + 6 + 1),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["gold_dark"], [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 6, cy + 6),
            (cx - 6, cy + 6),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["gold_mid"], [
            (cx - 7, cy + 1),
            (cx + 7, cy + 1),
            (cx + 5, cy + 5),
            (cx - 5, cy + 5),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["gold_light"], [
            (cx - 5, cy + 2),
            (cx + 5, cy + 2),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ])
        # Top rim highlight.
        pygame.draw.line(surface, _NS_zyvareth.PALETTE["gold_shine"],
                         (cx - 6, cy + 1), (cx + 6, cy + 1), 1)
        # Central purple gem.
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_zyvareth._alpha(160 * (6 - r) / 6 * gem_pulse)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha),
                                   (cx, cy + 3), r)
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_darkest"], [
            (cx, cy),
            (cx + 3, cy + 3),
            (cx, cy + 6),
            (cx - 3, cy + 3),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_dark"], [
            (cx, cy + 1),
            (cx + 2, cy + 3),
            (cx, cy + 5),
            (cx - 2, cy + 3),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_mid"], [
            (cx, cy + 2),
            (cx + 1, cy + 3),
            (cx, cy + 4),
            (cx - 1, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"], (cx, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["white"], (cx, cy + 3, 1, 1))
        # Side gold rings/chains.
        for side in (-1, 1):
            ring_x = cx + side * 10
            ring_y = cy + 4
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["gold_dark"], (ring_x, ring_y), 2)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["gold_mid"], (ring_x, ring_y), 1)
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["gold_light"], (ring_x, ring_y, 1, 1))
    def _draw_curved_neck(surface, cx, cy, facing, phase, action, attack_progress):
        """Curved neck from body to head."""
        neck_lift = 0
        if action == "attack" and attack_progress < 0.55:
            neck_lift = -int(attack_progress / 0.55 * 4)
        # Neck segments — curve up-forward.
        base_x = cx - facing * 2
        base_y = cy
        tip_x = cx + facing * 4
        tip_y = cy - 8 + neck_lift
        prev = (base_x, base_y)
        for step in range(1, 5):
            t = step / 4
            # Bezier curve.
            mid_x = base_x + int((tip_x - base_x) * 0.5) + facing * 2
            mid_y = base_y - int((base_y - tip_y) * 0.4) - 2
            bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y)
            thickness = 8 - step
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                                 (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), thickness + 1)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_darkest"],
                                 prev, (bx, by), thickness)
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_dark"],
                                 prev, (bx, by), max(1, thickness - 1))
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_mid"],
                                 (prev[0], prev[1] - 1), (bx, by - 1), max(1, thickness - 3))
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["body_light"],
                                 (prev[0], prev[1] - 2), (bx, by - 2), max(1, thickness - 5))
            # Belly on front side.
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["belly_dark"],
                                 (prev[0] + facing, prev[1] + 1), (bx + facing, by + 1),
                                 max(1, thickness - 3))
            _NS_zyvareth._aaline(surface, _NS_zyvareth.PALETTE["belly_mid"],
                                 (prev[0] + facing, prev[1] + 2), (bx + facing, by + 2),
                                 max(1, thickness - 5))
            # Small mane crystal spikes on top.
            if step % 2 == 0:
                spike_x = bx - facing * (thickness // 2)
                spike_y = by - thickness // 2 - 1
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_dark"],
                                 (spike_x, spike_y, 1, 2))
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"],
                                 (spike_x, spike_y - 1, 1, 1))
            prev = (bx, by)
    def _draw_horned_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Head with big branching crystal horns."""
        # Head shape (elongated snout).
        head_shape = [
            (cx - 6 * facing, cy + 4),
            (cx - 7 * facing, cy - 1),
            (cx - 4 * facing, cy - 6),
            (cx + 2 * facing, cy - 7),
            (cx + 8 * facing, cy - 5),
            (cx + 12 * facing, cy - 2),
            (cx + 13 * facing, cy + 1),
            (cx + 12 * facing, cy + 4),
            (cx + 6 * facing, cy + 6),
            (cx - 2 * facing, cy + 6),
        ]
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_darkest"], head_shape)
        # Top color.
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_dark"], [
            (cx - 6 * facing, cy + 3),
            (cx - 6 * facing, cy - 1),
            (cx - 3 * facing, cy - 5),
            (cx + 2 * facing, cy - 6),
            (cx + 7 * facing, cy - 4),
            (cx + 11 * facing, cy - 1),
            (cx + 12 * facing, cy + 1),
            (cx - 5 * facing, cy + 1),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_mid"], [
            (cx - 4 * facing, cy - 1),
            (cx - 2 * facing, cy - 4),
            (cx + 3 * facing, cy - 5),
            (cx + 8 * facing, cy - 3),
            (cx + 10 * facing, cy - 1),
            (cx, cy),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_light"], [
            (cx - 1 * facing, cy - 3),
            (cx + 4 * facing, cy - 4),
            (cx + 8 * facing, cy - 2),
            (cx + 4 * facing, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["body_edge"], (cx + 2 * facing, cy - 4, 1, 1))
        # Snout (belly light tint).
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["belly_dark"], [
            (cx + 8 * facing, cy + 1),
            (cx + 12 * facing, cy),
            (cx + 12 * facing, cy + 4),
            (cx + 8 * facing, cy + 5),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["belly_mid"], [
            (cx + 9 * facing, cy + 2),
            (cx + 11 * facing, cy + 2),
            (cx + 11 * facing, cy + 3),
            (cx + 9 * facing, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["belly_light"], (cx + 10 * facing, cy + 3, 1, 1))
        # Ear (behind horns).
        ear_x = cx - 3 * facing
        ear_y = cy - 5
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_darkest"], [
            (ear_x, ear_y),
            (ear_x - 2 * facing, ear_y - 3),
            (ear_x + 1 * facing, ear_y - 1),
        ])
        _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["body_mid"], [
            (ear_x, ear_y),
            (ear_x - 1 * facing, ear_y - 2),
            (ear_x + 1 * facing, ear_y - 1),
        ])
        # NOSTRIL.
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                         (cx + 10 * facing, cy + 1, 1, 1))
        # PURPLE EYE.
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        ex = cx + int(4 * facing)
        ey = cy - 2
        for r in range(4, 0, -1):
            alpha = _NS_zyvareth._alpha(140 * (4 - r) / 4 * eye_pulse)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["eye_mid"], alpha), (ex, ey), r)
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["eye_socket"], (ex - 1, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["eye_mid"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["eye_light"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_zyvareth.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # Small mouth.
        if action == "attack":
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                             (cx + 8 * facing, cy + 3, 3, 2))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_dark"],
                             (cx + 9 * facing, cy + 3, 2, 1))
        else:
            pygame.draw.line(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                             (cx + 8 * facing, cy + 4), (cx + 11 * facing, cy + 4), 1)
        # === BIG CRYSTAL HORNS (branching) ===
        _NS_zyvareth._draw_crystal_horns(surface, cx, cy - 4, facing, phase)
    def _draw_crystal_horns(surface, cx, cy, facing, phase):
        """Tall branching purple crystal horns."""
        # 2 sides.
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 2
            base_y = cy - 2
            sway = math.sin(phase * 0.4 + side) * 1
            # Main horn segments (branching upward).
            # Main stem.
            for seg in range(4):
                seg_h = 4
                seg_bot_y = base_y - seg * seg_h
                seg_top_y = seg_bot_y - seg_h
                seg_bot_w = 3 - seg // 2
                seg_top_w = 2 - seg // 2
                if seg_top_w < 1:
                    seg_top_w = 1
                sx_offset = int(side * seg * 1.2)
                # Horn segment shape.
                p1 = (base_x + sx_offset - seg_bot_w, seg_bot_y)
                p2 = (base_x + sx_offset + seg_bot_w, seg_bot_y)
                p3 = (base_x + sx_offset + side + seg_top_w, seg_top_y + int(sway * 0.3))
                p4 = (base_x + sx_offset + side - seg_top_w, seg_top_y + int(sway * 0.3))
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                                   [(p1[0] + 1, p1[1] + 1), (p2[0] + 1, p2[1] + 1),
                                    (p3[0] + 1, p3[1] + 1), (p4[0] + 1, p4[1] + 1)])
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_darkest"],
                                   [p1, p2, p3, p4])
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_dark"], [
                    (p1[0] + 1, p1[1] - 1),
                    (p2[0] - 1, p2[1] - 1),
                    (p3[0] - 1, p3[1] + 1),
                    (p4[0] + 1, p4[1] + 1),
                ])
                # Bright edge.
                pygame.draw.line(surface, _NS_zyvareth.PALETTE["crystal_mid"],
                                 (p4[0], p4[1]), (p1[0], p1[1]), 1)
                pygame.draw.line(surface, _NS_zyvareth.PALETTE["crystal_light"],
                                 (int((p4[0] + p1[0]) / 2), int((p4[1] + p1[1]) / 2)),
                                 (int((p3[0] + p2[0]) / 2), int((p3[1] + p2[1]) / 2)), 1)
            # Top spike tip (main horn).
            main_tip_y = base_y - 4 * 4 + int(sway)
            main_tip_x = base_x + int(side * 5)
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"], [
                (main_tip_x - 1 + 1, main_tip_y + 3 + 1),
                (main_tip_x + 1 + 1, main_tip_y + 3 + 1),
                (main_tip_x + 1, main_tip_y + 1),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_darkest"], [
                (main_tip_x - 1, main_tip_y + 3),
                (main_tip_x + 1, main_tip_y + 3),
                (main_tip_x, main_tip_y),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_dark"], [
                (main_tip_x, main_tip_y + 3),
                (main_tip_x + int(side * 0.5), main_tip_y + 1),
                (main_tip_x, main_tip_y),
            ])
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_mid"],
                             (main_tip_x, main_tip_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"],
                             (main_tip_x, main_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["white"],
                             (main_tip_x, main_tip_y, 1, 1))
            # Side branch (smaller horn).
            branch_base_x = base_x + int(side * 2)
            branch_base_y = base_y - 6
            branch_tip_x = base_x + int(side * 6)
            branch_tip_y = branch_base_y - 3 + int(sway * 0.5)
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"], [
                (branch_base_x + 1, branch_base_y + 1),
                (branch_base_x + int(side) + 1, branch_base_y + 1),
                (branch_tip_x + 1, branch_tip_y + 1),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_darkest"], [
                (branch_base_x, branch_base_y),
                (branch_base_x + int(side), branch_base_y),
                (branch_tip_x, branch_tip_y),
            ])
            _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_dark"], [
                (branch_base_x, branch_base_y),
                (int((branch_base_x + branch_tip_x) / 2), int((branch_base_y + branch_tip_y) / 2)),
                (branch_base_x, branch_base_y - 1),
            ])
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_mid"],
                             (branch_tip_x, branch_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"],
                             (branch_tip_x, branch_tip_y, 1, 1))
            # Second small branch (going down-back).
            b2_tip_x = base_x + int(side * 3)
            b2_tip_y = base_y - 10 + int(sway * 0.5)
            pygame.draw.line(surface, _NS_zyvareth.PALETTE["crystal_darkest"],
                             (base_x + int(side), base_y - 4),
                             (b2_tip_x, b2_tip_y), 2)
            pygame.draw.line(surface, _NS_zyvareth.PALETTE["crystal_dark"],
                             (base_x + int(side), base_y - 4),
                             (b2_tip_x, b2_tip_y), 1)
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"], (b2_tip_x, b2_tip_y, 1, 1))
        # Small electric sparks between horns.
        spark_pulse = math.sin(phase * 3) * 0.5 + 0.5
        if spark_pulse > 0.7:
            spark_x = cx + int(math.sin(phase * 5) * 3)
            spark_y = cy - 12
            for i in range(3):
                ang = i * math.pi / 3 + phase
                ex = spark_x + int(math.cos(ang) * 4)
                ey = spark_y + int(math.sin(ang) * 3)
                pygame.draw.line(surface, _NS_zyvareth.PALETTE["bolt_hot"],
                                 (spark_x, spark_y), (ex, ey), 1)
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["white"], (ex, ey, 1, 1))
    # ================= BASIC ATTACK — LIGHTNING BOLT =================
    def _draw_basic_bolt(surface, boss, x, y, progress):
        """Basic magic bolt projectile."""
        if progress < 0.4:
            # Charging at head.
            facing = boss.direction
            t = progress / 0.4
            head_x = x + facing * 30
            head_y = y - 20
            cr = int(2 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_zyvareth._alpha(180 * (cr + 4 - r) / (cr + 4))
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha),
                                       (head_x, head_y), r)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_mid"], (head_x, head_y), cr - 1)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_hot"], (head_x, head_y), max(1, cr - 2))
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (head_x, head_y), max(1, cr - 4))
            # Small electric sparks charging.
            for i in range(4):
                a = phase = boss.pulse * 4 + i * math.pi / 2
                sx = head_x + int(math.cos(a) * (cr + 3))
                sy = head_y + int(math.sin(a) * (cr + 3))
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["bolt_hot"], (sx, sy, 1, 1))
            return
        facing = boss.direction
        tx, ty = _NS_zyvareth._target_position(boss, x, y)
        start_x = x + facing * 32
        start_y = y - 18
        t = (progress - 0.4) / 0.6
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_zyvareth._alpha(220 - i * 25)
            size = max(1, 6 - i)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_darkest"], alpha), (px, py), size)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha), (px, py), max(1, size - 1))
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_mid"], alpha), (px, py), max(1, size - 2))
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha), (px, py), max(1, size - 3))
        # Head.
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_darkest"], (bx, by), 7)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_dark"], (bx, by), 5)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_mid"], (bx, by), 4)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_light"], (bx, by), 3)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_hot"], (bx, by), 2)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (bx, by), 1)
        # Impact.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 18)
            alpha = _NS_zyvareth._alpha(240 * (1 - st))
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha), (tx, ty), radius, 3)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_mid"], alpha), (tx, ty), max(1, radius - 4), 2)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha), (tx, ty), max(1, radius - 8), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha), (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["white"], alpha), (ex, ey, 1, 1))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((170, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius, 150 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 20, 180), (5, 9, 160, 14))
        pygame.draw.ellipse(shadow, (40, 15, 90, 130), (12, 11, 146, 10))
        surface.blit(shadow, (x - 85, y - 16))
    def _draw_electric_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_zyvareth._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_zyvareth._aacircle(aura, (*_NS_zyvareth.PALETTE["crystal_darkest"], alpha), (130, 110), radius)
        for radius in range(65, 5, -3):
            alpha = _NS_zyvareth._alpha((65 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_zyvareth._aacircle(aura, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha), (130, 110), radius)
        for radius in range(35, 5, -2):
            alpha = _NS_zyvareth._alpha((35 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_zyvareth._aacircle(aura, (*_NS_zyvareth.PALETTE["crystal_mid"], alpha), (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Random electric arcs around aura.
        for i in range(3):
            arc_t = (phase * 0.6 + i * 0.33) % 1.0
            if arc_t < 0.3:
                ang = (phase + i * 2) * math.pi
                ax1 = x + int(math.cos(ang) * 50)
                ay1 = y - 5 + int(math.sin(ang) * 25)
                ax2 = ax1 + int(math.cos(ang + math.pi / 4) * 10)
                ay2 = ay1 + int(math.sin(ang + math.pi / 4) * 10)
                pygame.draw.line(surface, _NS_zyvareth.PALETTE["bolt_light"], (ax1, ay1), (ax2, ay2), 1)
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["white"], (ax2, ay2, 1, 1))
        # Floating particles.
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 6 + i * 5) % 24)
            color = _NS_zyvareth.PALETTE["crystal_mid"] if i % 2 == 0 else _NS_zyvareth.PALETTE["bolt_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 62), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zyvareth.PALETTE["crystal_darkest"], 200), (5, 20, 190, 32), 3)
        pygame.draw.ellipse(ring, (*_NS_zyvareth.PALETTE["crystal_dark"], 220), (14, 22, 172, 28), 2)
        pygame.draw.ellipse(ring, (*_NS_zyvareth.PALETTE["crystal_mid"], 180), (25, 24, 150, 24), 1)
        # Rune sparks.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 82)
            y1 = 36 + int(math.sin(angle) * 14)
            pygame.draw.rect(ring, _NS_zyvareth.PALETTE["crystal_hot"], (x1, y1, 2, 2))
            pygame.draw.rect(ring, _NS_zyvareth.PALETTE["white"], (x1, y1, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zyvareth.PALETTE["crystal_hot"], _NS_zyvareth._alpha(150 * pulse)),
                                (15, 14, 170, 46), 1)
        surface.blit(ring, (x - 100, y - 31))
    def _draw_electric_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Purple electric particles floating below."""
        strength = 1.5 if intense else 1.0
        # Mist.
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_zyvareth._alpha((30 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_zyvareth.PALETTE["mist_dark"], alpha),
                                    (80 - radius * 2, 25 - radius // 3, radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_zyvareth._alpha((20 - radius) * 3.0 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_zyvareth.PALETTE["mist_mid"], alpha),
                                    (80 - radius, 25 - radius // 4, radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising sparks.
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26, -32, 32)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_zyvareth._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha), (sx, sy), 3)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha), (sx, sy - 1, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_zyvareth._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha),
                                 (sx, sy - 1, 2, 1))
    # ================= SKILL Q — SPLITBOLT =================
    def _draw_splitbolt(surface, boss, x, y, timer, phase):
        """Lightning bolt that splits into branches."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zyvareth._target_position(boss, x, y)
        head_x = x + facing * 30
        head_y = y - 20
        if progress < 0.2:
            # Charge at horn.
            t = progress / 0.2
            cr = int(3 + t * 10)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_zyvareth._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_dark"], alpha),
                                       (head_x, head_y), r)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_mid"], (head_x, head_y), cr - 2)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_light"], (head_x, head_y), max(1, cr - 4))
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_hot"], (head_x, head_y), max(1, cr - 6))
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (head_x, head_y), max(1, cr - 8))
        else:
            t = (progress - 0.2) / 0.8
            # Main jagged lightning bolt from head to target.
            _NS_zyvareth._draw_lightning_bolt(surface, head_x, head_y, tx, ty, phase, alpha=int(255 * min(1, t * 4)))
            # Split branches — smaller bolts branching from main.
            num_branches = 3
            for br_i in range(num_branches):
                mid_frac = 0.4 + br_i * 0.15
                mid_x = int(head_x + (tx - head_x) * mid_frac)
                mid_y = int(head_y + (ty - head_y) * mid_frac)
                # Branch direction perpendicular-ish.
                br_angle = math.atan2(ty - head_y, tx - head_x) + (br_i - 1) * math.pi / 3
                br_len = 40 + br_i * 5
                br_end_x = mid_x + int(math.cos(br_angle) * br_len)
                br_end_y = mid_y + int(math.sin(br_angle) * br_len)
                _NS_zyvareth._draw_lightning_bolt(surface, mid_x, mid_y, br_end_x, br_end_y, phase + br_i, alpha=180)
                # Small impact at each branch end.
                if t > 0.3:
                    _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_light"], (br_end_x, br_end_y), 5)
                    _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_hot"], (br_end_x, br_end_y), 3)
                    _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (br_end_x, br_end_y), 1)
            # Impact at main target.
            radius = int(12 + t * 20)
            alpha = _NS_zyvareth._alpha(240 * (1 - t) if t > 0.5 else 240)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_dark"], alpha), (tx, ty), radius, 3)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_mid"], alpha), (tx, ty), max(1, radius - 4), 2)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_light"], alpha), (tx, ty), max(1, radius - 8), 1)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_hot"], alpha), (tx, ty), 3)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["white"], alpha), (tx, ty), 1)
    def _draw_lightning_bolt(surface, x1, y1, x2, y2, phase, alpha=255):
        """Jagged lightning bolt between two points."""
        alpha = _NS_zyvareth._alpha(alpha)
        segments = 10
        # Jagged path.
        points = [(x1, y1)]
        for i in range(1, segments):
            t = i / segments
            base_x = x1 + (x2 - x1) * t
            base_y = y1 + (y2 - y1) * t
            # Random offset.
            offset = math.sin(phase * 8 + i * 2.3) * 6
            perp_x = -(y2 - y1)
            perp_y = (x2 - x1)
            length = math.hypot(perp_x, perp_y) or 1
            perp_x /= length
            perp_y /= length
            px = int(base_x + perp_x * offset)
            py = int(base_y + perp_y * offset)
            points.append((px, py))
        points.append((x2, y2))
        # Draw layered.
        for width, color in [
            (5, _NS_zyvareth.PALETTE["bolt_dark"]),
            (3, _NS_zyvareth.PALETTE["bolt_mid"]),
            (2, _NS_zyvareth.PALETTE["bolt_light"]),
            (1, _NS_zyvareth.PALETTE["bolt_hot"]),
        ]:
            for i in range(len(points) - 1):
                pygame.draw.line(surface, (*color, alpha), points[i], points[i + 1], width)
        # White core.
        for i in range(len(points) - 1):
            pygame.draw.line(surface, (*_NS_zyvareth.PALETTE["white"], alpha), points[i], points[i + 1], 1)
    # ================= SKILL W — SOUL DRAIN (beam) =================
    def _draw_soul_drain(surface, boss, x, y, timer, phase):
        """Continuous purple beam from head to target."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zyvareth._target_position(boss, x, y)
        head_x = x + facing * 30
        head_y = y - 20
        intensity = math.sin(progress * math.pi) if progress < 0.85 else (1 - progress) / 0.15
        intensity = max(0, min(1, intensity))
        alpha_base = _NS_zyvareth._alpha(255 * intensity)
        # Zigzag beam (like soul drain).
        segments = 12
        points = [(head_x, head_y)]
        for i in range(1, segments):
            t = i / segments
            base_x = head_x + (tx - head_x) * t
            base_y = head_y + (ty - head_y) * t
            offset = math.sin(phase * 5 + i * 1.5) * 4
            perp_x = -(ty - head_y)
            perp_y = (tx - head_x)
            length = math.hypot(perp_x, perp_y) or 1
            perp_x /= length
            perp_y /= length
            px = int(base_x + perp_x * offset)
            py = int(base_y + perp_y * offset)
            points.append((px, py))
        points.append((tx, ty))
        # Draw layered beam.
        for width, color in [
            (7, _NS_zyvareth.PALETTE["bolt_dark"]),
            (5, _NS_zyvareth.PALETTE["bolt_mid"]),
            (3, _NS_zyvareth.PALETTE["bolt_light"]),
            (2, _NS_zyvareth.PALETTE["bolt_hot"]),
            (1, _NS_zyvareth.PALETTE["white"]),
        ]:
            for i in range(len(points) - 1):
                pygame.draw.line(surface, (*color, alpha_base), points[i], points[i + 1], width)
        # Bright particles flowing along beam (soul being drained).
        for i in range(8):
            flow_t = (phase * 0.8 + i * 0.13) % 1.0
            flow_x = int(tx + (head_x - tx) * flow_t)
            flow_y = int(ty + (head_y - ty) * flow_t)
            # Add zigzag offset.
            offset = math.sin(phase * 5 + i * 1.5) * 3
            perp_x = -(ty - head_y)
            perp_y = (tx - head_x)
            length = math.hypot(perp_x, perp_y) or 1
            perp_x /= length
            perp_y /= length
            fpx = int(flow_x + perp_x * offset)
            fpy = int(flow_y + perp_y * offset)
            pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha_base), (fpx, fpy, 2, 2))
            pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["white"], alpha_base), (fpx, fpy, 1, 1))
        # Impact glow at target.
        for r in range(15, 0, -2):
            a = _NS_zyvareth._alpha(alpha_base * (15 - r) / 15)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_mid"], a), (tx, ty), r)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_hot"], (tx, ty), 4)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (tx, ty), 2)
        # Charge glow at head.
        for r in range(10, 0, -1):
            a = _NS_zyvareth._alpha(alpha_base * (10 - r) / 10)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_mid"], a), (head_x, head_y), r)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["bolt_hot"], (head_x, head_y), 3)
        _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (head_x, head_y), 1)
    # ================= SKILL E — STORM FALL =================
    def _draw_stormfall_ground(surface, boss, x, y, timer, phase):
        """Ground indicators for storm strikes."""
        tx, ty = _NS_zyvareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # AoE ground circle.
        r = int(70 * min(1.0, progress * 3))
        if r > 5:
            pygame.draw.ellipse(surface, (*_NS_zyvareth.PALETTE["bolt_dark"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_zyvareth.PALETTE["bolt_mid"], 150),
                                (tx - r + 4, ty - r // 3 + 2, r * 2 - 8, r * 2 // 3 - 4), 1)
    def _draw_stormfall(surface, boss, x, y, timer, phase):
        """Storm cloud + random lightning strikes."""
        tx, ty = _NS_zyvareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 3))
        # Storm cloud above area.
        cloud_y = ty - 80
        cloud_offsets = [
            (-30, 0, 12), (-15, -6, 14), (0, -8, 16), (15, -6, 14), (30, 0, 12),
            (-20, 4, 10), (20, 4, 10),
        ]
        for offset in cloud_offsets:
            cx_c = tx + offset[0]
            cy_c = cloud_y + offset[1]
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["cloud_darkest"], (cx_c + 1, cy_c + 1), offset[2])
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["cloud_dark"], (cx_c, cy_c), offset[2])
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["cloud_mid"], (cx_c - 1, cy_c - 1), offset[2] - 3)
            pygame.draw.rect(surface, _NS_zyvareth.PALETTE["cloud_light"], (cx_c - 2, cy_c - 3, 2, 1))
        # Multiple random lightning strikes.
        num_strikes = 5
        for strike_i in range(num_strikes):
            strike_t = (phase * 1.5 + strike_i * 0.6) % 1.5
            if strike_t < 0.4:  # bolt visible
                # Random position within AoE.
                offset_ang = strike_i * math.pi * 2 / num_strikes + phase * 0.3
                strike_x = tx + int(math.cos(offset_ang) * (r * 0.7))
                strike_y = ty + int(math.sin(offset_ang) * (r * 0.7) * 0.4)
                # Bolt from cloud to ground.
                bolt_start_x = strike_x + int(math.sin(strike_i) * 5)
                bolt_start_y = cloud_y + 10
                alpha = _NS_zyvareth._alpha(255 * (1 - strike_t / 0.4))
                _NS_zyvareth._draw_lightning_bolt(surface, bolt_start_x, bolt_start_y,
                                                  strike_x, strike_y, phase + strike_i, alpha=alpha)
                # Impact on ground.
                impact_r = int(10 + strike_t * 8)
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_light"], alpha),
                                       (strike_x, strike_y), impact_r, 1)
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["bolt_hot"], alpha),
                                       (strike_x, strike_y), impact_r // 2)
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["white"], alpha),
                                       (strike_x, strike_y), 2)
    # ================= SKILL R — CRYSTAL NOVA =================
    def _draw_crystal_nova_ground(surface, boss, x, y, timer, phase):
        """Nova ring on ground."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.2:
            nova_t = (progress - 0.2) / 0.8
            r = int(80 * min(1.0, nova_t * 2))
            alpha = _NS_zyvareth._alpha(220 * (1 - nova_t * 0.5))
            if r > 5:
                pygame.draw.ellipse(surface, (*_NS_zyvareth.PALETTE["crystal_darkest"], alpha),
                                    (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha),
                                    (x - r + 3, y + 42 - r // 3 + 2, r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface, (*_NS_zyvareth.PALETTE["crystal_mid"], alpha),
                                    (x - r + 6, y + 42 - r // 3 + 4, r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_crystal_nova(surface, boss, x, y, timer, phase):
        """Nova burst with crystal spikes erupting from ground."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Charge — pulse growing.
            t = progress / 0.2
            cr = int(6 + t * 18)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_zyvareth._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], alpha), (x, y), r)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_mid"], (x, y), cr - 3)
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["crystal_hot"], (x, y), max(1, cr - 6))
            _NS_zyvareth._aacircle(surface, _NS_zyvareth.PALETTE["white"], (x, y), max(1, cr - 10))
        else:
            t = (progress - 0.2) / 0.8
            intensity = math.sin(t * math.pi)
            # Expanding nova ring.
            nova_r = int(30 + t * 60)
            alpha_base = _NS_zyvareth._alpha(240 * (1 - t * 0.5))
            # Big center burst.
            for r in range(nova_r + 6, 0, -3):
                r_alpha = _NS_zyvareth._alpha(alpha_base * (nova_r + 6 - r) / (nova_r + 6))
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_darkest"], r_alpha), (x, y), r)
            for r in range(nova_r, 0, -3):
                r_alpha = _NS_zyvareth._alpha(alpha_base * (nova_r - r) / nova_r * 1.3)
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_dark"], r_alpha), (x, y), r)
            for r in range(nova_r - 8, 0, -2):
                r_alpha = _NS_zyvareth._alpha(alpha_base * (nova_r - r) / nova_r * 1.5)
                _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_mid"], r_alpha), (x, y), r)
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha_base), (x, y),
                                   max(1, nova_r // 3))
            _NS_zyvareth._aacircle(surface, (*_NS_zyvareth.PALETTE["white"], alpha_base), (x, y),
                                   max(1, nova_r // 5))
            # CRYSTAL SPIKES ERUPTING from ground in circle.
            num_spikes = 12
            for spike_i in range(num_spikes):
                spike_angle = spike_i * math.pi * 2 / num_spikes + phase * 0.2
                # Spikes grow from center outward.
                spike_dist_max = nova_r
                spike_dist = int(spike_dist_max * min(1.0, t * 2))
                spike_x = x + int(math.cos(spike_angle) * spike_dist)
                spike_y = y + 20 + int(math.sin(spike_angle) * spike_dist * 0.4)
                # Spike size varies.
                spike_h = 12 + spike_i % 3 * 4
                spike_w = 4
                # Growth animation.
                grow_t = min(1.0, (t * 2 - spike_i * 0.05) if t * 2 > spike_i * 0.05 else 0)
                if grow_t <= 0:
                    continue
                actual_h = int(spike_h * grow_t)
                actual_w = int(spike_w * grow_t)
                if actual_h < 2 or actual_w < 1:
                    continue
                # Crystal spike shape (pointed up).
                p_tip = (spike_x, spike_y - actual_h)
                p_bl = (spike_x - actual_w, spike_y)
                p_br = (spike_x + actual_w, spike_y)
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["shadow_deep"],
                                   [(p_tip[0] + 1, p_tip[1] + 1),
                                    (p_bl[0] + 1, p_bl[1] + 1),
                                    (p_br[0] + 1, p_br[1] + 1)])
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_darkest"], [p_tip, p_bl, p_br])
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_dark"], [
                    p_tip,
                    (int((p_tip[0] + p_bl[0]) / 2), int((p_tip[1] + p_bl[1]) / 2)),
                    (spike_x, spike_y),
                ])
                _NS_zyvareth._poly(surface, _NS_zyvareth.PALETTE["crystal_mid"], [
                    p_tip,
                    (spike_x - 1, int((p_tip[1] + spike_y) / 2)),
                    (spike_x, spike_y),
                ])
                # Bright edge.
                pygame.draw.line(surface, _NS_zyvareth.PALETTE["crystal_light"],
                                 p_tip, (spike_x, spike_y), 1)
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["crystal_hot"], (p_tip[0], p_tip[1], 1, 1))
                pygame.draw.rect(surface, _NS_zyvareth.PALETTE["white"], (p_tip[0], p_tip[1], 1, 1))
            # Radial lightning bolts shooting outward.
            for i in range(8):
                bolt_angle = i * math.pi / 4 + phase * 0.5
                bolt_end_x = x + int(math.cos(bolt_angle) * (nova_r + 12))
                bolt_end_y = y + int(math.sin(bolt_angle) * (nova_r + 12) * 0.6)
                _NS_zyvareth._draw_lightning_bolt(surface, x, y, bolt_end_x, bolt_end_y, phase + i, alpha=alpha_base)
            # Bright sparks all around.
            for i in range(16):
                spark_a = i * math.pi / 8 + phase * 0.8
                spark_r = nova_r + int(math.sin(phase + i) * 5)
                spx = x + int(math.cos(spark_a) * spark_r)
                spy = y + int(math.sin(spark_a) * spark_r * 0.6)
                pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["crystal_hot"], alpha_base), (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_zyvareth.PALETTE["white"], alpha_base), (spx, spy, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_nixweaver(surface, boss, x, y):
    """Entry point nixweaver."""
    return _NS_nixweaver.draw_nixweaver(surface, boss, x, y)


def draw_nyxraal(surface, boss, x, y):
    """Entry point nyxraal."""
    return _NS_nyxraal.draw_nyxraal(surface, boss, x, y)


def draw_xarnthuul(surface, boss, x, y):
    """Entry point xarnthuul."""
    return _NS_xarnthuul.draw_xarnthuul(surface, boss, x, y)


def draw_zyvareth(surface, boss, x, y):
    """Entry point zyvareth."""
    return _NS_zyvareth.draw_zyvareth(surface, boss, x, y)
