"""
bosses/level30.py - Semua boss Level 30

Berisi:
  - kaelvyrn   (mini boss - MELEE gilded marauder, gold raider)
  - thorvin    (mini boss - MELEE ironbound warden, spirit shield)
  - xaerissa   (mini boss - RANGED weaver of crimson silk, spider)
  - nyxharr    (TRUE BOSS - MELEE shadow of war, ghost rider)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kv_ (kaelvyrn), _tv_ (thorvin), _xae_ (xaerissa) sudah unik.
  - _nx_ (nyxharr) di-rename -> _nxh_ (bentrok dengan nyxara level 5),
    termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KAELVYRN (GILDED MARAUDER) - Mini Boss
# ====================================================================

class _NS_kaelvyrn:
    """Namespace kaelvyrn - Gilded Marauder mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tanned/bronze)
        "skin_darkest": (55, 30, 20),
        "skin_dark": (110, 70, 45),
        "skin_mid": (170, 115, 78),
        "skin_light": (215, 165, 120),
        "skin_shine": (245, 210, 170),
        # Hair (dark brown/black)
        "hair_darkest": (10, 8, 12),
        "hair_dark": (30, 22, 25),
        "hair_mid": (60, 45, 40),
        "hair_light": (100, 75, 60),
        # Cape/cloth (GOLD YELLOW — signature)
        "cape_darkest": (60, 40, 5),
        "cape_dark": (130, 90, 15),
        "cape_mid": (200, 155, 40),
        "cape_light": (245, 210, 90),
        "cape_shine": (255, 240, 160),
        "cape_edge": (255, 250, 200),
        # Leather armor (brown)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (55, 35, 18),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 110, 65),
        # Pants (dark blue-teal)
        "pants_dark": (15, 25, 35),
        "pants_mid": (35, 55, 70),
        "pants_light": (65, 90, 110),
        # Gold trim/metal
        "gold_dark": (90, 60, 10),
        "gold_mid": (180, 140, 30),
        "gold_light": (240, 200, 80),
        "gold_shine": (255, 240, 150),
        # Crossbow/weapon (dark metal + gold)
        "metal_dark": (20, 20, 25),
        "metal_mid": (60, 60, 70),
        "metal_light": (130, 130, 145),
        # Magic energy (cyan/teal - Akshan style)
        "magic_darkest": (5, 30, 40),
        "magic_dark": (15, 80, 105),
        "magic_mid": (40, 165, 205),
        "magic_light": (120, 230, 250),
        "magic_hot": (200, 250, 255),
        "magic_shine": (240, 255, 255),
        # Golden shot projectile
        "shot_dark": (100, 70, 5),
        "shot_mid": (220, 170, 30),
        "shot_light": (255, 230, 100),
        "shot_hot": (255, 250, 200),
        # Shadow/stealth purple
        "shadow_purple_dark": (20, 10, 35),
        "shadow_purple_mid": (55, 30, 85),
        "shadow_purple_light": (120, 80, 170),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaelvyrn._clamp(color)
        if _NS_kaelvyrn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaelvyrn._clamp(color)
        if _NS_kaelvyrn.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaelvyrn._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaelvyrn(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaelvyrn._detect_moving(boss)
        _NS_kaelvyrn._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_kaelvyrn._draw_gold_aura(surface, x, y, pulse)
        _NS_kaelvyrn._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_kaelvyrn._draw_stealth_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelvyrn._draw_reckoning_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelvyrn._draw_grapple_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — during stealth, semi-transparent
        stealth = (active_skill == "w")
        if attacking:
            _NS_kaelvyrn._draw_attack(surface, boss, x, y, stealth)
        elif moving:
            _NS_kaelvyrn._draw_walk(surface, boss, x, y, stealth)
        else:
            _NS_kaelvyrn._draw_idle(surface, boss, x, y, stealth)
        # Foreground skill FX
        if active_skill == "q":
            _NS_kaelvyrn._draw_golden_shot(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelvyrn._draw_stealth_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelvyrn._draw_grapple_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelvyrn._draw_reckoning_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kv_previous_timer", 0))
        active = bool(getattr(boss, "_kv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kv_attack_active = True
            boss._kv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kv_attack_frame = int(getattr(boss, "_kv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kv_attack_active = False
            boss._kv_attack_frame = 0
            active = False
        boss._kv_previous_timer = timer
        boss._kv_attack_progress = (
            min(1.0, getattr(boss, "_kv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kv_last_x"):
            boss._kv_last_x = boss.x
            boss._kv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kv_last_x)
        dy = abs(boss.y - boss._kv_last_y)
        boss._kv_last_x = boss.x
        boss._kv_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (all "floating" movement)
    # ============================================================
    def _draw_idle(surface, boss, x, y, stealth=False):
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        _NS_kaelvyrn._draw_shadow(surface, x, y + 50)
        _NS_kaelvyrn._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                 "idle", 0, stealth)
    def _draw_walk(surface, boss, x, y, stealth=False):
        # FLOATING movement — smooth bob and sway, no footsteps
        phase = boss.pulse * 1.8
        float_bob = int(math.sin(phase * 1.0) * 6)
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_kaelvyrn._draw_shadow(surface, x + sway, y + 50, faded=True)
        _NS_kaelvyrn._draw_float_wisps(surface, x + sway, y + 40, phase,
                                        boss.direction)
        _NS_kaelvyrn._draw_body(surface, x + sway, y + float_bob - 4,
                                 boss.direction, phase, "walk", 0, stealth)
    def _draw_attack(surface, boss, x, y, stealth=False):
        progress = getattr(boss, "_kv_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Ranged shot: aim → fire → recoil (crossbow shot)
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction  # slight rear
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            lunge = int((-3 + t * 8)) * boss.direction  # slight forward
            lift = int(3 - t * 2)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(5 * (1 - t)) * boss.direction
            lift = int(1 - t * 1)
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_kaelvyrn._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaelvyrn._draw_body(surface, x + lunge, y - lift + bob,
                                 boss.direction, boss.pulse, "attack",
                                 progress, stealth)
        _NS_kaelvyrn._draw_basic_shot(surface, boss, x + lunge, y - lift + bob,
                                       progress)
    # ============================================================
    # BODY (Humanoid rogue with crossbow)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                    stealth=False):
        """Layered humanoid body: cape → legs → torso → arms → head → weapon."""
        # Cape (behind body, flowing)
        _NS_kaelvyrn._draw_cape(surface, cx, cy, facing, phase, action)
        # Legs
        _NS_kaelvyrn._draw_legs(surface, cx, cy + 12, facing, phase, action)
        # Torso
        _NS_kaelvyrn._draw_torso(surface, cx, cy, facing, phase, action,
                                  attack_progress)
        # Off-arm (rear)
        _NS_kaelvyrn._draw_rear_arm(surface, cx, cy, facing, phase, action,
                                     attack_progress)
        # Head + hair
        _NS_kaelvyrn._draw_head(surface, cx + facing * 2, cy - 14, facing,
                                 phase, action)
        # Front arm + crossbow (weapon hand)
        _NS_kaelvyrn._draw_weapon_arm(surface, cx, cy, facing, phase, action,
                                       attack_progress)
        # Stealth fade overlay
        if stealth:
            _NS_kaelvyrn._apply_stealth_overlay(surface, cx, cy, phase)
    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Long flowing gold cape behind body."""
        wave = math.sin(phase * 1.2) * 4
        wave2 = math.sin(phase * 0.9 + 1) * 3
        back = -facing
        # Cape starts at shoulder, flows back & down
        base_top = (cx + back * 4, cy - 14)
        base_bot = (cx + back * 4, cy - 6)
        # Cape shape (flowing)
        cape_points = [
            base_top,
            (cx + back * 10, cy - 18 + int(wave)),
            (cx + back * 18, cy - 12 + int(wave2)),
            (cx + back * 24, cy - 4 + int(wave)),
            (cx + back * 26, cy + 6 + int(wave2)),
            (cx + back * 22, cy + 18 + int(wave)),
            (cx + back * 14, cy + 22 + int(wave2)),
            (cx + back * 6, cy + 20),
            (cx + back * 2, cy + 10),
            base_bot,
        ]
        # Shadow
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in cape_points])
        # Cape layers (darkest → lightest)
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["cape_darkest"],
                           cape_points)
        # Inner darker fold
        cx_c = sum(p[0] for p in cape_points) / len(cape_points)
        cy_c = sum(p[1] for p in cape_points) / len(cape_points)
        inner = [(int(p[0] * 0.85 + cx_c * 0.15),
                  int(p[1] * 0.85 + cy_c * 0.15)) for p in cape_points]
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["cape_dark"], inner)
        # Mid layer
        mid = [(int(p[0] * 0.7 + cx_c * 0.3),
                int(p[1] * 0.7 + cy_c * 0.3)) for p in cape_points]
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["cape_mid"], mid)
        # Highlights along edges (folds)
        for i in range(len(cape_points) - 1):
            p1 = cape_points[i]
            p2 = cape_points[i + 1]
            if i % 2 == 0:
                mid_pt = (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))
                inner_pt = (int(mid_pt[0] * 0.75 + cx_c * 0.25),
                            int(mid_pt[1] * 0.75 + cy_c * 0.25))
                _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["cape_light"],
                                     mid_pt, inner_pt, 2)
        # Bright edge trim (gold shine along outer)
        for i in range(len(cape_points) - 1):
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["cape_shine"],
                                 cape_points[i], cape_points[i + 1], 1)
        # Small gold ornament at cape shoulder clasp
        clasp_x = cx + back * 3
        clasp_y = cy - 12
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_dark"],
                                (clasp_x, clasp_y), 3)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                                (clasp_x, clasp_y), 2)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_shine"],
                                (clasp_x - 1, clasp_y - 1), 1)
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Floating legs — slight sway, no walk cycle (rogue floats)."""
        sway = math.sin(phase * 0.8) * 2
        for side_i, side in enumerate((-1, 1)):
            hip_x = cx + side * 3
            hip_y = cy - 4
            knee_x = hip_x + int(sway * side * 0.5)
            knee_y = hip_y + 8
            foot_x = knee_x - side * 1
            foot_y = knee_y + 8
            # Thigh
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                                 (hip_x + 1, hip_y + 1),
                                 (knee_x + 1, knee_y + 1), 6)
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["pants_dark"],
                                 (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["pants_mid"],
                                 (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["pants_light"],
                                 (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Shin
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                                 (knee_x + 1, knee_y + 1),
                                 (foot_x + 1, foot_y + 1), 5)
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["pants_dark"],
                                 (knee_x, knee_y), (foot_x, foot_y), 4)
            _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["pants_mid"],
                                 (knee_x, knee_y), (foot_x, foot_y), 2)
            # Boot
            boot_pts = [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 4, foot_y + 2),
                (foot_x + 2, foot_y + 3),
                (foot_x - 3, foot_y + 3),
                (foot_x - 4, foot_y + 1),
            ]
            _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["leather_darkest"],
                               [(p[0] + 1, p[1] + 1) for p in boot_pts])
            _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["leather_dark"],
                               boot_pts)
            _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["leather_mid"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 2, foot_y - 1),
                (foot_x + 3, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            # Gold buckle
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                             (foot_x - 1, foot_y, 2, 1))
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["gold_shine"],
                             (foot_x, foot_y, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase, action, attack_progress):
        """Torso: bare chest with leather straps + gold trim."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape (V-shape muscular)
        torso = [
            (cx - 7, cy - 8),
            (cx + 7, cy - 8),
            (cx + 9, cy - 2),
            (cx + 8, cy + 5),
            (cx + 5, cy + 12),
            (cx - 5, cy + 12),
            (cx - 8, cy + 5),
            (cx - 9, cy - 2),
        ]
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in torso])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_darkest"], torso)
        # Skin base
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_dark"], [
            (cx - 6, cy - 7), (cx + 6, cy - 7),
            (cx + 8, cy - 2), (cx + 7, cy + 4),
            (cx + 4, cy + 10), (cx - 4, cy + 10),
            (cx - 7, cy + 4), (cx - 8, cy - 2),
        ])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 6, cy - 1), (cx + 5, cy + 6),
            (cx + 3, cy + 9), (cx - 3, cy + 9),
            (cx - 5, cy + 6), (cx - 6, cy - 1),
        ])
        # Chest highlight
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_light"], [
            (cx - 3, cy - 4), (cx + 3, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Abs shadow
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                         (cx, cy - 2), (cx, cy + 8), 1)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                         (cx - 3, cy + 3), (cx + 3, cy + 3), 1)
        # Leather chest strap (diagonal)
        strap_pts = [
            (cx - 8, cy - 4),
            (cx + 8, cy + 2),
            (cx + 8, cy + 5),
            (cx - 8, cy - 1),
        ]
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["leather_darkest"],
                           strap_pts)
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["leather_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy + 3),
            (cx + 7, cy + 4),
            (cx - 7, cy - 2),
        ])
        # Gold trim on strap
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                         (cx - 7, cy - 3), (cx + 7, cy + 3), 1)
        # Gold medallion at center
        med_x = cx + 1
        med_y = cy + 1
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_dark"],
                                (med_x, med_y), 3)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                                (med_x, med_y), 2)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["magic_mid"],
                                (med_x, med_y), 1)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_hot"],
                         (med_x, med_y, 1, 1))
        # Belt
        belt_y = cy + 11
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["leather_darkest"],
                         (cx - 6, belt_y, 12, 3))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["leather_dark"],
                         (cx - 6, belt_y, 12, 2))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                         (cx - 1, belt_y, 3, 3))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["gold_shine"],
                         (cx, belt_y + 1, 1, 1))
    def _draw_rear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm (holds bolts / gestures)."""
        back = -facing
        shoulder = (cx + back * 5, cy - 6)
        # Rear arm swings during walk
        swing = math.sin(phase * 1.0) * 3 if action == "walk" else 0
        elbow = (shoulder[0] + back * 4, shoulder[1] + 6 + int(swing))
        hand = (elbow[0] + back * 2, elbow[1] + 6)
        # Upper arm
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                             shoulder, elbow, 4)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_dark"],
                             shoulder, elbow, 3)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 1)
        # Forearm
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                             elbow, hand, 3)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_dark"],
                             elbow, hand, 2)
        # Wrist wrap (leather)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["leather_dark"],
                         (hand[0] - 2, hand[1] - 1, 4, 2))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["leather_mid"],
                         (hand[0] - 2, hand[1] - 1, 4, 1))
        # Hand
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["skin_dark"], hand, 2)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["skin_mid"], hand, 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Handsome roguish face with wild hair."""
        # Head shape (slightly oval)
        head = [
            (cx - 5, cy - 2),
            (cx - 6, cy - 6),
            (cx - 4, cy - 9),
            (cx, cy - 10),
            (cx + 4, cy - 9),
            (cx + 6, cy - 6),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
            (cx - 5, cy + 3),
        ]
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_darkest"], head)
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_dark"], [
            (cx - 4, cy - 2), (cx - 5, cy - 5), (cx - 3, cy - 8),
            (cx, cy - 9), (cx + 3, cy - 8), (cx + 5, cy - 5),
            (cx + 5, cy - 1), (cx + 4, cy + 2), (cx + 1, cy + 4),
            (cx - 1, cy + 4), (cx - 4, cy + 2),
        ])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_mid"], [
            (cx - 3, cy - 3), (cx - 3, cy - 6), (cx, cy - 7),
            (cx + 3, cy - 6), (cx + 4, cy - 3),
            (cx + 3, cy + 1), (cx - 3, cy + 1),
        ])
        # Highlight
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["skin_light"], [
            (cx + 1 * facing, cy - 6),
            (cx + 3 * facing, cy - 5),
            (cx + 3 * facing, cy - 3),
            (cx + 1 * facing, cy - 3),
        ])
        # Hair (wild, wavy on top and back)
        hair_wave = math.sin(phase * 0.5) * 1
        hair_pts = [
            (cx - 6, cy - 5),
            (cx - 7, cy - 8),
            (cx - 5, cy - 11 + int(hair_wave)),
            (cx - 2, cy - 12 + int(hair_wave)),
            (cx + 1, cy - 13 + int(hair_wave)),
            (cx + 4, cy - 12 + int(hair_wave)),
            (cx + 6, cy - 10),
            (cx + 7, cy - 6),
            (cx + 6, cy - 4),
            (cx + 4, cy - 7),
            (cx + 1, cy - 8),
            (cx - 2, cy - 8),
            (cx - 4, cy - 6),
        ]
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["hair_darkest"],
                           hair_pts)
        # Hair highlights
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["hair_dark"], [
            (cx - 5, cy - 8),
            (cx - 3, cy - 11),
            (cx + 2, cy - 12),
            (cx + 5, cy - 10),
            (cx + 4, cy - 8),
            (cx, cy - 9),
            (cx - 3, cy - 9),
        ])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["hair_mid"], [
            (cx - 3, cy - 10),
            (cx, cy - 11),
            (cx + 3, cy - 10),
            (cx + 2, cy - 9),
            (cx - 2, cy - 9),
        ])
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["hair_light"],
                         (cx + facing, cy - 11, 1, 1))
        # Trailing hair strands at back
        back = -facing
        for i in range(3):
            strand_x = cx + back * (5 + i)
            strand_y = cy - 7 + i * 2 + int(math.sin(phase + i) * 1)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["hair_darkest"],
                             (strand_x, strand_y),
                             (strand_x + back * 2, strand_y + 2), 2)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["hair_dark"],
                             (strand_x, strand_y),
                             (strand_x + back * 2, strand_y + 2), 1)
        # EYES — cyan magic glow
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Eye socket shadow
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 3, 2))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 3, 2))
        # Whites of eyes
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["skin_shine"],
                         (cx - 3, cy - 5, 3, 2))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["skin_shine"],
                         (cx + 1, cy - 5, 3, 2))
        # Cyan pupils (magic infused)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_dark"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_dark"],
                         (cx + 2, cy - 5, 1, 2))
        # Glow
        for r in range(3, 0, -1):
            alpha = _NS_kaelvyrn._alpha(80 * (3 - r) / 3 * eye_pulse)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["magic_light"], alpha),
                                    (cx - 2, cy - 4), r)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["magic_light"], alpha),
                                    (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_hot"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_hot"],
                         (cx + 2, cy - 4, 1, 1))
        # Nose
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                         (cx, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["skin_light"],
                         (cx + facing, cy - 2, 1, 1))
        # Smirk (roguish)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                         (cx + 2 * facing, cy + 1, 1, 1))  # smirk upturn
        # Small stubble
        for sx in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["hair_dark"],
                             (cx + sx, cy + 4, 1, 1))
    def _draw_weapon_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding crossbow — aims and fires."""
        shoulder = (cx + facing * 4, cy - 6)
        # Arm angle based on action
        if action == "attack":
            if attack_progress < 0.35:
                # Aiming — arm raises forward
                t = attack_progress / 0.35
                elbow_off_x = facing * (5 + int(t * 3))
                elbow_off_y = -2 - int(t * 2)
            elif attack_progress < 0.55:
                # Fire — arm extends fully, recoil pull
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = facing * (8 - int(t * 2))
                elbow_off_y = -4 + int(t * 1)
            else:
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = facing * (6 + int(t * -2))
                elbow_off_y = -3 + int(t * 3)
        else:
            # Casual aim forward
            aim_bob = math.sin(phase * 0.7) * 1
            elbow_off_x = facing * 6
            elbow_off_y = -2 + int(aim_bob)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (elbow[0] + facing * 8, elbow[1] + 1)
        # Upper arm
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                             shoulder, elbow, 4)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_dark"],
                             shoulder, elbow, 3)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 1)
        # Forearm
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 4)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_darkest"],
                             elbow, hand, 3)
        _NS_kaelvyrn._aaline(surface, _NS_kaelvyrn.PALETTE["skin_dark"],
                             elbow, hand, 2)
        # Leather wrist guard
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["leather_darkest"],
                         (hand[0] - facing * 3, hand[1] - 2, 5, 4))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["leather_dark"],
                         (hand[0] - facing * 3, hand[1] - 2, 5, 3))
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                         (hand[0] - facing * 2, hand[1] - 1, 3, 1))
        # CROSSBOW (in hand)
        _NS_kaelvyrn._draw_crossbow(surface, hand[0], hand[1], facing, phase,
                                     action, attack_progress)
    def _draw_crossbow(surface, hx, hy, facing, phase, action, attack_progress):
        """Ornate golden crossbow with cyan magic core."""
        # Main stock (horizontal wooden/metal body)
        stock_x = hx + facing * 2
        stock_y = hy
        # Stock body
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["shadow_deep"], [
            (stock_x - facing * 4, stock_y - 1),
            (stock_x + facing * 10, stock_y - 2),
            (stock_x + facing * 12, stock_y),
            (stock_x + facing * 10, stock_y + 3),
            (stock_x - facing * 4, stock_y + 2),
        ])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["metal_dark"], [
            (stock_x - facing * 4, stock_y - 1),
            (stock_x + facing * 9, stock_y - 2),
            (stock_x + facing * 11, stock_y),
            (stock_x + facing * 9, stock_y + 2),
            (stock_x - facing * 4, stock_y + 1),
        ])
        _NS_kaelvyrn._poly(surface, _NS_kaelvyrn.PALETTE["metal_mid"], [
            (stock_x - facing * 3, stock_y),
            (stock_x + facing * 8, stock_y - 1),
            (stock_x + facing * 10, stock_y),
            (stock_x + facing * 8, stock_y + 1),
            (stock_x - facing * 3, stock_y),
        ])
        # Gold trim highlight
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                         (stock_x - facing * 3, stock_y - 1),
                         (stock_x + facing * 9, stock_y - 1), 1)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["gold_shine"],
                         (stock_x + facing * 4, stock_y - 1),
                         (stock_x + facing * 8, stock_y - 1), 1)
        # Bow arms (vertical curve at front)
        bow_front_x = stock_x + facing * 10
        for direction in (-1, 1):
            arm_tip_x = bow_front_x + facing * 3
            arm_tip_y = stock_y + direction * 7
            arm_mid_x = bow_front_x + facing * 1
            arm_mid_y = stock_y + direction * 4
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                             (bow_front_x + 1, stock_y + 1),
                             (arm_mid_x + 1, arm_mid_y + 1), 3)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["metal_dark"],
                             (bow_front_x, stock_y),
                             (arm_mid_x, arm_mid_y), 2)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["metal_dark"],
                             (arm_mid_x, arm_mid_y),
                             (arm_tip_x, arm_tip_y), 2)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                             (arm_mid_x, arm_mid_y),
                             (arm_tip_x, arm_tip_y), 1)
            # Tip caps
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_dark"],
                                    (arm_tip_x, arm_tip_y), 2)
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                                    (arm_tip_x, arm_tip_y), 1)
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["gold_shine"],
                             (arm_tip_x, arm_tip_y, 1, 1))
        # Bowstring (or magic energy string)
        string_top = (bow_front_x + facing * 3, stock_y - 7)
        string_bot = (bow_front_x + facing * 3, stock_y + 7)
        # Slight tension during fire
        if action == "attack" and 0.3 < attack_progress < 0.5:
            string_mid = (bow_front_x + facing * 1, stock_y)  # relaxed
        else:
            string_mid = (bow_front_x + facing * 2, stock_y)  # tensioned
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["magic_dark"],
                         string_top, string_mid, 1)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["magic_dark"],
                         string_mid, string_bot, 1)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["magic_light"],
                         string_top, string_mid, 1)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["magic_light"],
                         string_mid, string_bot, 1)
        # Magic core (center of crossbow — glowing cyan)
        core_x = stock_x + facing * 4
        core_y = stock_y
        core_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_kaelvyrn._alpha(150 * (4 - r) / 4 * core_pulse)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["magic_light"], alpha),
                                    (core_x, core_y), r)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["magic_mid"],
                                (core_x, core_y), 2)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["magic_hot"],
                                (core_x, core_y), 1)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_shine"],
                         (core_x, core_y, 1, 1))
        # Trigger + grip
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["metal_dark"],
                         (stock_x - facing * 1, stock_y + 2),
                         (stock_x - facing * 1, stock_y + 4), 1)
    def _apply_stealth_overlay(surface, cx, cy, phase):
        """Semi-transparent overlay when stealthed."""
        # Draw shimmer / distortion effect via overlay (approximation)
        overlay = pygame.Surface((80, 80), pygame.SRCALPHA)
        # Sparkle particles
        for i in range(12):
            sx = 40 + int(math.sin(phase * 2 + i) * 25)
            sy = 40 + int(math.cos(phase * 1.5 + i) * 30)
            alpha = _NS_kaelvyrn._alpha(150 + math.sin(phase * 3 + i) * 60)
            pygame.draw.rect(overlay,
                             (*_NS_kaelvyrn.PALETTE["shadow_purple_light"], alpha),
                             (sx, sy, 1, 1))
        surface.blit(overlay, (cx - 40, cy - 40))
    # ============================================================
    # BASIC ATTACK SHOT (small golden bolt)
    # ============================================================
    def _draw_basic_shot(surface, boss, x, y, progress):
        """Basic crossbow shot — golden bolt with trail."""
        if progress < 0.45:
            return
        facing = boss.direction
        tx, ty = _NS_kaelvyrn._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 6
        t = (progress - 0.45) / 0.55
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Bolt trail
        for i in range(6):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_kaelvyrn._alpha(220 - i * 30)
            size = max(1, 4 - i)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["shot_dark"], alpha),
                                    (px, py), size)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["shot_mid"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["shot_light"], alpha),
                                    (px, py), max(1, size - 2))
        # Bright head
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_dark"], (bx, by), 4)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_mid"], (bx, by), 3)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_light"], (bx, by), 2)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["white"], (bx, by, 1, 1))
        # Bolt streak line (arrow shape)
        streak_len = 6
        streak_x = bx - facing * streak_len
        streak_y = by
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["shot_mid"],
                         (streak_x, streak_y), (bx, by), 2)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["shot_light"],
                         (streak_x, streak_y), (bx, by), 1)
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        alpha_mult = 0.5 if faded else 1.0
        for radius in range(11, 0, -1):
            alpha = int(max(0, (11 - radius) * 18) * alpha_mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 12 - radius,
                                 84 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, int(160 * alpha_mult)),
                            (4, 6, 92, 12))
        surface.blit(shadow, (x - 50, y - 12))
    def _draw_gold_aura(surface, x, y, phase):
        """Warm gold aura + subtle cyan magic accents."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((180, 140), pygame.SRCALPHA)
        for radius in range(75, 5, -5):
            alpha = _NS_kaelvyrn._alpha((75 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_kaelvyrn._aacircle(aura,
                                        (*_NS_kaelvyrn.PALETTE["cape_dark"], alpha),
                                        (90, 70), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_kaelvyrn._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kaelvyrn._aacircle(aura,
                                        (*_NS_kaelvyrn.PALETTE["cape_mid"], alpha),
                                        (90, 70), radius)
        for radius in range(25, 5, -2):
            alpha = _NS_kaelvyrn._alpha((25 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_kaelvyrn._aacircle(aura,
                                        (*_NS_kaelvyrn.PALETTE["magic_dark"], alpha),
                                        (90, 70), radius)
        surface.blit(aura, (x - 90, y - 70))
        # Floating gold sparks
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_kaelvyrn.PALETTE["shot_mid"] if i % 3 != 0 \
                else _NS_kaelvyrn.PALETTE["magic_mid"]
            hot_color = _NS_kaelvyrn.PALETTE["shot_hot"] if i % 3 != 0 \
                else _NS_kaelvyrn.PALETTE["magic_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaelvyrn.PALETTE["cape_dark"], 180),
                            (5, 15, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_kaelvyrn.PALETTE["cape_mid"], 200),
                            (14, 17, 122, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_kaelvyrn.PALETTE["gold_mid"], 210),
                            (24, 19, 102, 14), 1)
        pygame.draw.ellipse(ring, (*_NS_kaelvyrn.PALETTE["magic_dark"], 160),
                            (35, 21, 80, 10), 1)
        # Runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 42)
            y1 = 26 + int(math.sin(angle) * 7)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 26 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_kaelvyrn.PALETTE["gold_shine"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaelvyrn.PALETTE["magic_hot"],
                                       _NS_kaelvyrn._alpha(140 * pulse)),
                                (15, 10, 120, 34), 1)
        surface.blit(ring, (x - 75, y - 23))
    def _draw_float_wisps(surface, cx, cy, phase, facing):
        """Wisps under body during floating movement."""
        for i in range(6):
            t = (phase * 0.5 + i * 0.15) % 1.0
            wx = cx + int(math.sin(phase + i) * 10) - facing * i * 2
            wy = cy + int(t * 8)
            alpha = _NS_kaelvyrn._alpha(180 * (1 - t))
            if alpha > 0:
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["cape_dark"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kaelvyrn.PALETTE["gold_mid"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # SKILL: Q - GOLDEN SHOT (long-range piercing bolt)
    # ============================================================
    def _draw_golden_shot(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaelvyrn._target_position(boss, x, y)
        if progress < 0.2:
            # Charge at crossbow core
            t = progress / 0.2
            mx = x + facing * 22
            my = y - 6
            cr = int(3 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kaelvyrn._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_dark"], alpha),
                                        (mx, my), r)
            for r in range(cr, 0, -1):
                alpha = _NS_kaelvyrn._alpha(220 * (cr - r) / max(1, cr))
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_mid"], alpha),
                                        (mx, my), r)
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_light"],
                                    (mx, my), max(1, cr - 2))
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_hot"],
                                    (mx, my), max(1, cr - 4))
            # Sparks
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = mx + int(math.cos(angle) * (cr + 3))
                sy = my + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["shot_hot"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 26
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Long piercing trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kaelvyrn._alpha(240 - i * 20)
                size = max(1, 8 - i)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_dark"], alpha),
                                        (px, py), size)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_mid"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_light"], alpha),
                                        (px, py), max(1, size - 2))
                if i < 5:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 1))
                        pygame.draw.rect(surface,
                                         (*_NS_kaelvyrn.PALETTE["shot_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Big head
            for r in range(12, 3, -2):
                alpha = _NS_kaelvyrn._alpha(100 * (12 - r) / 12)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_light"], alpha),
                                        (bx, by), r)
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_dark"],
                                    (bx, by), 6)
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_mid"],
                                    (bx, by), 4)
            _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_light"],
                                    (bx, by), 2)
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["white"], (bx, by, 1, 1))
            # Impact burst
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(10 + st * 22)
                alpha = _NS_kaelvyrn._alpha(240 * (1 - st))
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_dark"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_mid"], alpha),
                                        (tx, ty), radius, 2)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_light"], alpha),
                                        (tx, ty), max(1, radius - 6), 1)
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_kaelvyrn.PALETTE["shot_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: W - SHADOW VEIL (stealth)
    # ============================================================
    def _draw_stealth_ground(surface, boss, x, y, timer, phase):
        """Purple mist under boss during stealth."""
        for i in range(2):
            r = int(28 + i * 6 + math.sin(phase * 2) * 3)
            alpha = _NS_kaelvyrn._alpha(180 - i * 60)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["shadow_purple_mid"], alpha),
                                    (x, y + 40), r, 2)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["shadow_purple_light"], alpha),
                                    (x, y + 40), r, 1)
    def _draw_stealth_foreground(surface, boss, x, y, timer, phase):
        """Fading purple wisps rising."""
        for i in range(12):
            rise_t = (phase * 0.5 + i * 0.1) % 1.0
            rx = x + int(math.sin(phase + i) * 22)
            ry = y + 20 - int(rise_t * 40)
            alpha = _NS_kaelvyrn._alpha(200 * (1 - rise_t))
            if alpha > 0:
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shadow_purple_dark"], alpha),
                                        (rx, ry), 3)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shadow_purple_mid"], alpha),
                                        (rx, ry), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kaelvyrn.PALETTE["shadow_purple_light"], alpha),
                                 (rx, ry, 1, 1))
    # ============================================================
    # SKILL: E - GRAPPLE SWING (grappling hook + swing)
    # ============================================================
    def _draw_grapple_ground(surface, boss, x, y, timer, phase):
        """Ring shows launch point."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(20 + math.sin(phase * 3) * 3)
        alpha = _NS_kaelvyrn._alpha(220 * (1 - progress * 0.5))
        _NS_kaelvyrn._aacircle(surface,
                                (*_NS_kaelvyrn.PALETTE["magic_dark"], alpha),
                                (x, y + 40), r, 2)
        _NS_kaelvyrn._aacircle(surface,
                                (*_NS_kaelvyrn.PALETTE["magic_light"], alpha),
                                (x, y + 40), r - 3, 1)
    def _draw_grapple_foreground(surface, boss, x, y, timer, phase):
        """Grappling hook cable extending to sky anchor."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Anchor point (up and forward)
        anchor_x = x + facing * 60
        anchor_y = y - 80
        # Cable extend animation
        if progress < 0.3:
            t = progress / 0.3
            cur_x = int(x + facing * 22 + (anchor_x - x - facing * 22) * t)
            cur_y = int(y - 8 + (anchor_y - y + 8) * t)
        else:
            cur_x = anchor_x
            cur_y = anchor_y
        # Cable (glowing cyan)
        start_x = x + facing * 22
        start_y = y - 8
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["shadow_deep"],
                         (start_x + 1, start_y + 1),
                         (cur_x + 1, cur_y + 1), 3)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["magic_dark"],
                         (start_x, start_y), (cur_x, cur_y), 2)
        pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["magic_light"],
                         (start_x, start_y), (cur_x, cur_y), 1)
        # Hook at end
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["metal_dark"],
                                (cur_x, cur_y), 4)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                                (cur_x, cur_y), 3)
        _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["magic_hot"],
                                (cur_x, cur_y), 1)
        # Hook prongs
        for angle_off in (0, math.pi / 2, math.pi, math.pi * 1.5):
            px = cur_x + int(math.cos(angle_off) * 5)
            py = cur_y + int(math.sin(angle_off) * 5)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["metal_dark"],
                             (cur_x, cur_y), (px, py), 2)
            pygame.draw.line(surface, _NS_kaelvyrn.PALETTE["gold_mid"],
                             (cur_x, cur_y), (px, py), 1)
        # Impact sparkles at anchor
        if progress >= 0.3:
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                spark_r = 6 + int(math.sin(phase * 3 + i) * 3)
                sx = cur_x + int(math.cos(angle) * spark_r)
                sy = cur_y + int(math.sin(angle) * spark_r)
                pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_hot"],
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["magic_shine"],
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL: R - RECKONING (multi-shot barrage)
    # ============================================================
    def _draw_reckoning_ground(surface, boss, x, y, timer, phase):
        """Ground ring showing marked target zone."""
        tx, ty = _NS_kaelvyrn._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Rings expanding at target
        for i in range(3):
            ring_r = int(15 + i * 12 + progress * 20)
            alpha = _NS_kaelvyrn._alpha(200 - i * 50)
            pygame.draw.ellipse(surface,
                                (*_NS_kaelvyrn.PALETTE["shot_dark"], alpha),
                                (tx - ring_r, ty - ring_r // 3,
                                 ring_r * 2, ring_r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_kaelvyrn.PALETTE["shot_mid"], alpha),
                                (tx - ring_r + 2, ty - ring_r // 3 + 1,
                                 ring_r * 2 - 4, ring_r * 2 // 3 - 2), 1)
        # Rotating rune circle
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            r = 30
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["shot_light"],
                             (sx - 1, sy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["shot_hot"],
                             (sx, sy, 1, 1))
    def _draw_reckoning_foreground(surface, boss, x, y, timer, phase):
        """Multiple golden bolts converging on target."""
        facing = boss.direction
        tx, ty = _NS_kaelvyrn._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind-up — bolts gathering around boss
            t = progress / 0.3
            num_bolts = 8
            for i in range(num_bolts):
                angle = phase * 2 + i * math.pi * 2 / num_bolts
                orbit_r = int(35 * (1 - t) + 12 * t)
                bx = x + int(math.cos(angle) * orbit_r)
                by = y - 6 + int(math.sin(angle) * orbit_r * 0.6)
                _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_dark"],
                                        (bx, by), 3)
                _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_mid"],
                                        (bx, by), 2)
                _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_hot"],
                                        (bx, by), 1)
        elif progress < 0.75:
            # Fire barrage — bolts fly to target
            t = (progress - 0.3) / 0.45
            num_bolts = 8
            start_x = x + facing * 22
            start_y = y - 6
            for i in range(num_bolts):
                bolt_t = min(1.0, max(0.0, t - i * 0.05))
                if bolt_t <= 0:
                    continue
                # Slight fan pattern
                fan_off_y = int((i - num_bolts / 2) * 3)
                effective_ty = ty + fan_off_y
                bx = int(start_x + (tx - start_x) * bolt_t)
                by = int(start_y + (effective_ty - start_y) * bolt_t)
                # Trail
                for tr in range(4):
                    trail_t = max(0.0, bolt_t - tr * 0.08)
                    px = int(start_x + (tx - start_x) * trail_t)
                    py = int(start_y + (effective_ty - start_y) * trail_t)
                    alpha = _NS_kaelvyrn._alpha(220 - tr * 40)
                    _NS_kaelvyrn._aacircle(surface,
                                            (*_NS_kaelvyrn.PALETTE["shot_dark"], alpha),
                                            (px, py), max(1, 3 - tr))
                    _NS_kaelvyrn._aacircle(surface,
                                            (*_NS_kaelvyrn.PALETTE["shot_light"], alpha),
                                            (px, py), max(1, 2 - tr))
                # Head
                _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_dark"],
                                        (bx, by), 3)
                _NS_kaelvyrn._aacircle(surface, _NS_kaelvyrn.PALETTE["shot_light"],
                                        (bx, by), 2)
                pygame.draw.rect(surface, _NS_kaelvyrn.PALETTE["shot_hot"],
                                 (bx, by, 1, 1))
        else:
            # Impact aftermath
            t = (progress - 0.75) / 0.25
            radius = int(20 + t * 30)
            alpha = _NS_kaelvyrn._alpha(220 * (1 - t))
            for r in range(radius, 0, -4):
                a = _NS_kaelvyrn._alpha(alpha * r / radius)
                _NS_kaelvyrn._aacircle(surface,
                                        (*_NS_kaelvyrn.PALETTE["shot_mid"], a),
                                        (tx, ty), r, 2)
            _NS_kaelvyrn._aacircle(surface,
                                    (*_NS_kaelvyrn.PALETTE["shot_hot"], alpha),
                                    (tx, ty), max(1, radius // 3))
            for i in range(16):
                angle = i * math.pi / 8
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.6)
                pygame.draw.rect(surface,
                                 (*_NS_kaelvyrn.PALETTE["shot_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_kaelvyrn.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))



# ====================================================================
# THORVIN (IRONBOUND WARDEN) - Mini Boss
# ====================================================================

class _NS_thorvin:
    """Namespace thorvin - Ironbound Warden mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tanned/weathered old warrior)
        "skin_darkest": (50, 30, 22),
        "skin_dark": (105, 70, 50),
        "skin_mid": (165, 115, 82),
        "skin_light": (215, 165, 125),
        "skin_shine": (245, 210, 175),
        # Hair/beard (white/silver)
        "hair_darkest": (60, 60, 65),
        "hair_dark": (120, 120, 128),
        "hair_mid": (185, 185, 195),
        "hair_light": (230, 230, 240),
        "hair_shine": (255, 255, 255),
        # Shield (aged bronze/gold with dark iron)
        "shield_darkest": (25, 20, 15),
        "shield_dark": (60, 45, 25),
        "shield_mid": (120, 90, 45),
        "shield_light": (185, 145, 70),
        "shield_shine": (240, 200, 110),
        "shield_edge": (255, 235, 160),
        "shield_iron": (45, 40, 45),
        "shield_iron_light": (110, 100, 105),
        # Leather armor (deep brown)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (55, 35, 18),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 110, 65),
        # Pants/cloth (dark green-brown)
        "cloth_dark": (25, 30, 15),
        "cloth_mid": (60, 65, 35),
        "cloth_light": (100, 110, 60),
        # Gold ornaments
        "gold_dark": (90, 60, 10),
        "gold_mid": (180, 140, 30),
        "gold_light": (240, 200, 80),
        "gold_shine": (255, 240, 150),
        # Weapon (hammer - iron + gold trim)
        "metal_dark": (20, 20, 25),
        "metal_mid": (60, 60, 70),
        "metal_light": (130, 130, 145),
        "metal_shine": (200, 200, 215),
        # Spirit energy (orange/amber - Baxia signature)
        "spirit_darkest": (40, 15, 5),
        "spirit_dark": (110, 50, 10),
        "spirit_mid": (220, 120, 25),
        "spirit_light": (255, 180, 60),
        "spirit_hot": (255, 220, 130),
        "spirit_shine": (255, 245, 200),
        # Green shield energy (Tough passive)
        "guard_darkest": (5, 30, 15),
        "guard_dark": (20, 80, 35),
        "guard_mid": (55, 165, 80),
        "guard_light": (130, 230, 155),
        "guard_hot": (200, 255, 220),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thorvin._clamp(color)
        if _NS_thorvin.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_thorvin._clamp(color)
        if _NS_thorvin.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_thorvin._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thorvin(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thorvin._detect_moving(boss)
        _NS_thorvin._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_tv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_thorvin._draw_spirit_aura(surface, x, y, pulse)
        _NS_thorvin._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "r":
            _NS_thorvin._draw_avenging_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thorvin._draw_indestructible_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_thorvin._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_thorvin._draw_walk(surface, boss, x, y)
        else:
            _NS_thorvin._draw_idle(surface, boss, x, y)
        # Shield bubble (W)
        if active_skill == "w":
            _NS_thorvin._draw_indestructible_bubble(surface, boss, x, y, skill_timer, pulse)
        # Passive Tough shield
        if getattr(boss, "tough_shield_active", False):
            _NS_thorvin._draw_tough_shield(surface, boss, x, y, pulse)
        # Foreground skill FX
        if active_skill == "q":
            _NS_thorvin._draw_sacred_wheel(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorvin._draw_counter_assault(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorvin._draw_avenging_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_tv_previous_timer", 0))
        active = bool(getattr(boss, "_tv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._tv_attack_active = True
            boss._tv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._tv_attack_frame = int(getattr(boss, "_tv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._tv_attack_active = False
            boss._tv_attack_frame = 0
            active = False
        boss._tv_previous_timer = timer
        boss._tv_attack_progress = (
            min(1.0, getattr(boss, "_tv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_tv_last_x"):
            boss._tv_last_x = boss.x
            boss._tv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._tv_last_x)
        dy = abs(boss.y - boss._tv_last_y)
        boss._tv_last_x = boss.x
        boss._tv_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_thorvin._draw_shadow(surface, x, y + 50)
        _NS_thorvin._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Floating movement - smooth bob, no footsteps
        phase = boss.pulse * 1.6
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.6) * 2)
        _NS_thorvin._draw_shadow(surface, x + sway, y + 50, faded=True)
        _NS_thorvin._draw_float_wisps(surface, x + sway, y + 40, phase,
                                       boss.direction)
        _NS_thorvin._draw_body(surface, x + sway, y + float_bob - 3,
                                boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_tv_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Melee SWING: wind-up back → forward swing → follow-through
        if progress < 0.35:
            # Wind up (pull back)
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.55:
            # Strike (lunge forward)
            t = (progress - 0.35) / 0.20
            lunge = int((-5 + t * 18)) * boss.direction
            lift = int(4 - t * 6)
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            lunge = int(13 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_thorvin._draw_shadow(surface, x + lunge, y + 50)
        _NS_thorvin._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        # Swing trail
        _NS_thorvin._draw_swing_trail(surface, boss, x + lunge, y - lift,
                                       progress)
    # ============================================================
    # BODY (Humanoid warrior with shield + hammer)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered order: shield (back arm) -> legs -> torso -> rear arm -> head -> weapon arm."""
        # SHIELD is in the FRONT (facing side) — Baxia holds shield forward
        # But hammer arm swings from back to front during attack.
        # Layer: cape wisps behind → legs → torso → back arm (hammer) → head → shield arm (front)
        # Spirit wisps behind body (subtle)
        _NS_thorvin._draw_back_wisps(surface, cx, cy, facing, phase)
        # Legs
        _NS_thorvin._draw_legs(surface, cx, cy + 12, facing, phase, action)
        # Torso
        _NS_thorvin._draw_torso(surface, cx, cy, facing, phase, action,
                                 attack_progress)
        # Rear arm holds the HAMMER (swings during attack)
        _NS_thorvin._draw_hammer_arm(surface, cx, cy, facing, phase, action,
                                      attack_progress)
        # Head
        _NS_thorvin._draw_head(surface, cx + facing * 1, cy - 14, facing,
                                phase, action, attack_progress)
        # Front arm holds SHIELD
        _NS_thorvin._draw_shield_arm(surface, cx, cy, facing, phase, action,
                                      attack_progress)
    def _draw_back_wisps(surface, cx, cy, facing, phase):
        """Spirit wisps behind warrior (aura hint)."""
        back = -facing
        for i in range(4):
            t = (phase * 0.4 + i * 0.25) % 1.0
            wx = cx + back * (6 + i * 2) + int(math.sin(phase + i) * 2)
            wy = cy - 8 + i * 4 - int(t * 6)
            alpha = _NS_thorvin._alpha(140 * (1 - t))
            if alpha > 0:
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                       (wx, wy), 3)
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                 (wx, wy, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Floating legs — subtle sway."""
        sway = math.sin(phase * 0.7) * 2
        for side_i, side in enumerate((-1, 1)):
            hip_x = cx + side * 4
            hip_y = cy - 4
            knee_x = hip_x + int(sway * side * 0.4)
            knee_y = hip_y + 9
            foot_x = knee_x - side * 1
            foot_y = knee_y + 9
            # Thigh (thick, muscular)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                                 (hip_x + 1, hip_y + 1),
                                 (knee_x + 1, knee_y + 1), 8)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["cloth_dark"],
                                 (hip_x, hip_y), (knee_x, knee_y), 7)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["cloth_mid"],
                                 (hip_x, hip_y), (knee_x, knee_y), 4)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["cloth_light"],
                                 (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Leather wraps on thigh
            for wrap_y in (hip_y + 3, hip_y + 6):
                pygame.draw.line(surface, _NS_thorvin.PALETTE["leather_dark"],
                                 (hip_x - 4, wrap_y),
                                 (hip_x + 4, wrap_y), 2)
                pygame.draw.line(surface, _NS_thorvin.PALETTE["leather_mid"],
                                 (hip_x - 4, wrap_y),
                                 (hip_x + 4, wrap_y), 1)
            # Shin
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                                 (knee_x + 1, knee_y + 1),
                                 (foot_x + 1, foot_y + 1), 6)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["cloth_dark"],
                                 (knee_x, knee_y), (foot_x, foot_y), 5)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["cloth_mid"],
                                 (knee_x, knee_y), (foot_x, foot_y), 3)
            # Leather shin wraps
            for wrap_y in (knee_y + 3, knee_y + 6):
                pygame.draw.line(surface, _NS_thorvin.PALETTE["leather_dark"],
                                 (knee_x - 3, wrap_y),
                                 (knee_x + 3, wrap_y), 1)
            # Heavy boot
            boot_pts = [
                (foot_x - 4, foot_y - 1),
                (foot_x + 4, foot_y - 1),
                (foot_x + 5, foot_y + 2),
                (foot_x + 3, foot_y + 3),
                (foot_x - 4, foot_y + 3),
                (foot_x - 5, foot_y + 1),
            ]
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in boot_pts])
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_darkest"],
                              boot_pts)
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_dark"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 4, foot_y + 1),
                (foot_x - 3, foot_y + 1),
            ])
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_mid"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 2, foot_y - 1),
                (foot_x + 3, foot_y),
                (foot_x - 2, foot_y),
            ])
            # Gold buckle
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_mid"],
                             (foot_x - 1, foot_y, 3, 2))
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_shine"],
                             (foot_x, foot_y, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase, action, attack_progress):
        """Massive muscular torso with leather straps."""
        breath = math.sin(phase * 0.6) * 1
        # Torso shape (broad shoulders, big chest)
        torso = [
            (cx - 10, cy - 8),
            (cx + 10, cy - 8),
            (cx + 12, cy - 2),
            (cx + 11, cy + 5),
            (cx + 7, cy + 12),
            (cx - 7, cy + 12),
            (cx - 11, cy + 5),
            (cx - 12, cy - 2),
        ]
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in torso])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_darkest"], torso)
        # Skin base
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_dark"], [
            (cx - 9, cy - 7), (cx + 9, cy - 7),
            (cx + 11, cy - 2), (cx + 10, cy + 4),
            (cx + 6, cy + 10), (cx - 6, cy + 10),
            (cx - 10, cy + 4), (cx - 11, cy - 2),
        ])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 9, cy - 1), (cx + 8, cy + 6),
            (cx + 4, cy + 9), (cx - 4, cy + 9),
            (cx - 8, cy + 6), (cx - 9, cy - 1),
        ])
        # Pectoral highlights
        for side in (-1, 1):
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_light"], [
                (cx + side * 2, cy - 4),
                (cx + side * 6, cy - 4),
                (cx + side * 5, cy - 1),
                (cx + side * 3, cy - 1),
            ])
        # Center chest shadow (between pecs)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["skin_darkest"],
                         (cx, cy - 4), (cx, cy + 2), 1)
        # Abs
        pygame.draw.line(surface, _NS_thorvin.PALETTE["skin_darkest"],
                         (cx, cy + 2), (cx, cy + 10), 1)
        for ab_y in (cy + 4, cy + 7):
            pygame.draw.line(surface, _NS_thorvin.PALETTE["skin_darkest"],
                             (cx - 4, ab_y), (cx + 4, ab_y), 1)
        # Leather chest strap (X-cross for heavy warrior)
        strap1 = [
            (cx - 10, cy - 5),
            (cx + 10, cy + 4),
            (cx + 10, cy + 6),
            (cx - 10, cy - 3),
        ]
        strap2 = [
            (cx + 10, cy - 5),
            (cx - 10, cy + 4),
            (cx - 10, cy + 6),
            (cx + 10, cy - 3),
        ]
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_darkest"], strap1)
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_darkest"], strap2)
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_dark"], [
            (cx - 9, cy - 4), (cx + 9, cy + 5),
            (cx + 9, cy + 5), (cx - 9, cy - 3),
        ])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["leather_dark"], [
            (cx + 9, cy - 4), (cx - 9, cy + 5),
            (cx - 9, cy + 5), (cx + 9, cy - 3),
        ])
        # Gold trim on straps
        pygame.draw.line(surface, _NS_thorvin.PALETTE["gold_mid"],
                         (cx - 8, cy - 4), (cx + 8, cy + 4), 1)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["gold_mid"],
                         (cx + 8, cy - 4), (cx - 8, cy + 4), 1)
        # Central belt buckle (large ornate)
        buckle_x = cx
        buckle_y = cy + 1
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["gold_dark"], [
            (buckle_x - 4, buckle_y - 3),
            (buckle_x + 4, buckle_y - 3),
            (buckle_x + 5, buckle_y),
            (buckle_x + 4, buckle_y + 3),
            (buckle_x - 4, buckle_y + 3),
            (buckle_x - 5, buckle_y),
        ])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["gold_mid"], [
            (buckle_x - 3, buckle_y - 2),
            (buckle_x + 3, buckle_y - 2),
            (buckle_x + 4, buckle_y),
            (buckle_x + 3, buckle_y + 2),
            (buckle_x - 3, buckle_y + 2),
            (buckle_x - 4, buckle_y),
        ])
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["spirit_mid"],
                               (buckle_x, buckle_y), 2)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_hot"],
                         (buckle_x, buckle_y, 1, 1))
        # Belt line (below buckle)
        belt_y = cy + 11
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["leather_darkest"],
                         (cx - 8, belt_y, 16, 3))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["leather_dark"],
                         (cx - 8, belt_y, 16, 2))
        for i in range(4):
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_dark"],
                             (cx - 6 + i * 4, belt_y, 1, 2))
        # Shoulder pauldrons (metal armor on shoulders)
        for side in (-1, 1):
            paul_x = cx + side * 9
            paul_y = cy - 8
            paul_pts = [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 4, paul_y + 3),
                (paul_x + 2, paul_y + 5),
                (paul_x - 2, paul_y + 5),
                (paul_x - 4, paul_y + 3),
            ]
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in paul_pts])
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["metal_dark"],
                              paul_pts)
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["metal_mid"], [
                (paul_x - 2, paul_y + 1),
                (paul_x + 2, paul_y + 1),
                (paul_x + 3, paul_y + 3),
                (paul_x - 3, paul_y + 3),
            ])
            _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["metal_light"], [
                (paul_x - 1, paul_y + 1),
                (paul_x + 1, paul_y + 1),
                (paul_x + 1, paul_y + 2),
                (paul_x - 1, paul_y + 2),
            ])
            # Gold rivet
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_mid"],
                             (paul_x, paul_y + 3, 1, 1))
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_shine"],
                             (paul_x, paul_y + 3, 1, 1))
    def _draw_hammer_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm (BACK side) holds the warhammer — swings during attack."""
        back = -facing
        shoulder = (cx + back * 6, cy - 6)
        # Arm angle based on action
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up — raise hammer high back
                t = attack_progress / 0.35
                elbow_off_x = back * (5 + int(t * 3))
                elbow_off_y = -4 - int(t * 6)
                hand_off_x = back * (8 + int(t * 4))
                hand_off_y = -8 - int(t * 8)
            elif attack_progress < 0.55:
                # Strike — swing forward and down
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = int((back * 8) + (facing * 8 - back * 8) * t)
                elbow_off_y = int(-10 + t * 12)
                hand_off_x = int((back * 12) + (facing * 16 - back * 12) * t)
                hand_off_y = int(-16 + t * 20)
            else:
                # Recovery — bring back to guard
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = int(facing * 8 * (1 - t) + back * 3 * t)
                elbow_off_y = int(2 - t * 4)
                hand_off_x = int(facing * 16 * (1 - t) + back * 6 * t)
                hand_off_y = int(4 - t * 6)
        else:
            # Idle/walk — hammer rests
            sway = math.sin(phase * 0.7) * 1
            elbow_off_x = back * 3
            elbow_off_y = 2 + int(sway)
            hand_off_x = back * 6
            hand_off_y = 6
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # Upper arm (thick muscular)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_darkest"],
                             shoulder, elbow, 5)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_dark"],
                             shoulder, elbow, 4)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Forearm
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_darkest"],
                             elbow, hand, 4)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_dark"],
                             elbow, hand, 3)
        # Leather wrist wrap
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["leather_darkest"],
                         (hand[0] - 3, hand[1] - 2, 6, 4))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["leather_dark"],
                         (hand[0] - 3, hand[1] - 2, 6, 3))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_mid"],
                         (hand[0] - 2, hand[1] - 1, 4, 1))
        # WARHAMMER
        _NS_thorvin._draw_warhammer(surface, hand[0], hand[1], facing, phase,
                                     action, attack_progress)
    def _draw_warhammer(surface, hx, hy, facing, phase, action, attack_progress):
        """Big warhammer with gold + iron head."""
        # Hammer angle based on swing
        if action == "attack":
            if attack_progress < 0.35:
                # Windup — hammer up
                angle = -math.pi / 2 - (attack_progress / 0.35) * 0.5
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.2
                angle = -math.pi / 2 - 0.5 + t * (math.pi + 1.0)
            else:
                t = (attack_progress - 0.55) / 0.45
                angle = math.pi / 2 - t * math.pi
        else:
            # Rest — hammer down
            angle = math.pi / 2 + math.sin(phase * 0.5) * 0.05
        # Handle length + direction
        handle_len = 22
        head_x = hx + int(math.cos(angle) * handle_len) * facing
        head_y = hy + int(math.sin(angle) * handle_len)
        # Handle (wood + leather grip)
        # Shadow
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                             (hx + 1, hy + 1),
                             (head_x + 1, head_y + 1), 5)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["leather_darkest"],
                             (hx, hy), (head_x, head_y), 4)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["leather_dark"],
                             (hx, hy), (head_x, head_y), 3)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["leather_mid"],
                             (hx, hy), (head_x, head_y), 1)
        # Gold rings along handle
        for i in (0.3, 0.6):
            rx = int(hx + (head_x - hx) * i)
            ry = int(hy + (head_y - hy) * i)
            _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_dark"],
                                   (rx, ry), 2)
            _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_mid"],
                                   (rx, ry), 1)
        # HAMMER HEAD (big rectangular iron with gold trim)
        # Perpendicular to handle direction
        perp_x = -math.sin(angle) * facing
        perp_y = math.cos(angle)
        along_x = math.cos(angle) * facing
        along_y = math.sin(angle)
        # Head corners
        head_w = 9  # perp width
        head_l = 6  # along handle length
        c1 = (int(head_x + perp_x * head_w - along_x * head_l),
              int(head_y + perp_y * head_w - along_y * head_l))
        c2 = (int(head_x + perp_x * head_w + along_x * head_l),
              int(head_y + perp_y * head_w + along_y * head_l))
        c3 = (int(head_x - perp_x * head_w + along_x * head_l),
              int(head_y - perp_y * head_w + along_y * head_l))
        c4 = (int(head_x - perp_x * head_w - along_x * head_l),
              int(head_y - perp_y * head_w - along_y * head_l))
        # Shadow
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                          [(c1[0] + 2, c1[1] + 2), (c2[0] + 2, c2[1] + 2),
                           (c3[0] + 2, c3[1] + 2), (c4[0] + 2, c4[1] + 2)])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["metal_dark"],
                          [c1, c2, c3, c4])
        # Inner
        inner_pts = []
        hcx = (c1[0] + c2[0] + c3[0] + c4[0]) / 4
        hcy = (c1[1] + c2[1] + c3[1] + c4[1]) / 4
        for p in (c1, c2, c3, c4):
            inner_pts.append((int(p[0] * 0.75 + hcx * 0.25),
                              int(p[1] * 0.75 + hcy * 0.25)))
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["metal_mid"], inner_pts)
        # Highlight
        highlight_pts = []
        for p in (c1, c2, c3, c4):
            highlight_pts.append((int(p[0] * 0.55 + hcx * 0.45),
                                  int(p[1] * 0.55 + hcy * 0.45)))
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["metal_light"],
                          highlight_pts)
        # Gold trim edges
        for a, b in ((c1, c2), (c3, c4)):
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["gold_mid"],
                                 a, b, 2)
            _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["gold_shine"],
                                 a, b, 1)
        # Spirit glow rune on hammer head center
        rune_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_thorvin._alpha(160 * (4 - r) / 4 * rune_pulse)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                   (int(hcx), int(hcy)), r)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["spirit_hot"],
                               (int(hcx), int(hcy)), 2)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_shine"],
                         (int(hcx), int(hcy), 1, 1))
        # Spike caps at ends
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_dark"],
                               (int((c1[0] + c4[0]) / 2),
                                int((c1[1] + c4[1]) / 2)), 3)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_mid"],
                               (int((c1[0] + c4[0]) / 2),
                                int((c1[1] + c4[1]) / 2)), 2)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_dark"],
                               (int((c2[0] + c3[0]) / 2),
                                int((c2[1] + c3[1]) / 2)), 3)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_mid"],
                               (int((c2[0] + c3[0]) / 2),
                                int((c2[1] + c3[1]) / 2)), 2)
    def _draw_shield_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holds MASSIVE SHIELD."""
        shoulder = (cx + facing * 6, cy - 6)
        # Shield stays forward always (defensive)
        if action == "attack" and attack_progress < 0.35:
            # Shield slightly lower during windup
            elbow_off_x = facing * 4
            elbow_off_y = 2 + int(attack_progress / 0.35 * 2)
        elif action == "attack" and attack_progress < 0.55:
            # Shield pushes forward slightly during strike
            t = (attack_progress - 0.35) / 0.2
            elbow_off_x = facing * (4 + int(t * 3))
            elbow_off_y = 2 - int(t * 1)
        else:
            elbow_off_x = facing * 4
            elbow_off_y = 2 + int(math.sin(phase * 0.6) * 1)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (elbow[0] + facing * 5, elbow[1] + 2)
        # Upper arm
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_darkest"],
                             shoulder, elbow, 5)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_dark"],
                             shoulder, elbow, 4)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Forearm
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_darkest"],
                             elbow, hand, 4)
        _NS_thorvin._aaline(surface, _NS_thorvin.PALETTE["skin_dark"],
                             elbow, hand, 3)
        # SHIELD (huge circular)
        _NS_thorvin._draw_shield(surface, hand[0] + facing * 3, hand[1] - 2,
                                  facing, phase)
    def _draw_shield(surface, sx, sy, facing, phase):
        """Massive circular shield with gold rim and central boss."""
        # Shield radius
        r = 18
        # Slight sway/breathing
        sway = int(math.sin(phase * 0.5) * 1)
        sy += sway
        # Shadow
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shadow_deep"],
                               (sx + 2, sy + 3), r)
        # Outer rim (gold)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_dark"],
                               (sx, sy), r)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_mid"],
                               (sx, sy), r - 1)
        # Iron inner face
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_iron"],
                               (sx, sy), r - 3)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_iron_light"],
                               (sx, sy), r - 4)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_iron"],
                               (sx, sy), r - 5)
        # Inner gold ring
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_dark"],
                               (sx, sy), r - 6, 1)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_mid"],
                               (sx, sy), r - 7, 1)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shield_light"],
                               (sx, sy), r - 8, 1)
        # Central boss (spirit orb)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for cr in range(5, 0, -1):
            alpha = _NS_thorvin._alpha(180 * (5 - cr) / 5 * pulse)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                   (sx, sy), cr + 2)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_dark"],
                               (sx, sy), 4)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_mid"],
                               (sx, sy), 3)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["spirit_mid"],
                               (sx, sy), 2)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["spirit_hot"],
                               (sx, sy), 1)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_shine"],
                         (sx, sy, 1, 1))
        # Ornate spikes/studs around rim
        for i in range(6):
            angle = i * math.pi / 3 + math.pi / 6
            spike_x = sx + int(math.cos(angle) * (r - 2))
            spike_y = sy + int(math.sin(angle) * (r - 2))
            _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_dark"],
                                   (spike_x, spike_y), 2)
            _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_mid"],
                                   (spike_x, spike_y), 1)
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["gold_shine"],
                             (spike_x, spike_y, 1, 1))
        # Edge shine (top-left highlight)
        for i in range(3):
            angle = math.pi + math.pi / 4 + i * 0.2
            hx = sx + int(math.cos(angle) * (r - 1))
            hy = sy + int(math.sin(angle) * (r - 1))
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["shield_edge"],
                             (hx, hy, 2, 2))
    def _draw_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Old warrior head with big white beard and hair."""
        # Head shape
        head = [
            (cx - 5, cy - 2),
            (cx - 6, cy - 6),
            (cx - 4, cy - 9),
            (cx, cy - 10),
            (cx + 4, cy - 9),
            (cx + 6, cy - 6),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 5, cy + 3),
        ]
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_darkest"], head)
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_dark"], [
            (cx - 4, cy - 2), (cx - 5, cy - 5), (cx - 3, cy - 8),
            (cx, cy - 9), (cx + 3, cy - 8), (cx + 5, cy - 5),
            (cx + 5, cy - 1), (cx + 4, cy + 2),
            (cx + 2, cy + 5), (cx - 2, cy + 5), (cx - 4, cy + 2),
        ])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_mid"], [
            (cx - 3, cy - 3), (cx - 3, cy - 6), (cx, cy - 7),
            (cx + 3, cy - 6), (cx + 4, cy - 3),
        ])
        # Highlight side
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["skin_light"], [
            (cx + 1 * facing, cy - 5),
            (cx + 3 * facing, cy - 4),
            (cx + 3 * facing, cy - 2),
            (cx + 1 * facing, cy - 3),
        ])
        # HAIR - wild flowing back
        hair_wave = math.sin(phase * 0.4) * 1
        hair_pts = [
            (cx - 6, cy - 4),
            (cx - 8, cy - 8),
            (cx - 6, cy - 12 + int(hair_wave)),
            (cx - 2, cy - 13 + int(hair_wave)),
            (cx + 2, cy - 13 + int(hair_wave)),
            (cx + 6, cy - 12 + int(hair_wave)),
            (cx + 8, cy - 8),
            (cx + 7, cy - 5),
            (cx + 4, cy - 8),
            (cx, cy - 9),
            (cx - 4, cy - 8),
        ]
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["hair_darkest"], hair_pts)
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["hair_dark"], [
            (cx - 6, cy - 6),
            (cx - 5, cy - 11),
            (cx - 1, cy - 12),
            (cx + 3, cy - 12),
            (cx + 6, cy - 11),
            (cx + 6, cy - 7),
            (cx + 3, cy - 9),
            (cx, cy - 10),
            (cx - 3, cy - 9),
        ])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["hair_mid"], [
            (cx - 4, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 4, cy - 9),
            (cx + 3, cy - 8),
            (cx - 3, cy - 8),
        ])
        # Highlights
        for hx_off in (-2, 1):
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["hair_light"],
                             (cx + hx_off, cy - 11, 1, 1))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["hair_shine"],
                         (cx, cy - 12, 1, 1))
        # Long flowing hair strands at back
        back = -facing
        for i in range(4):
            strand_x = cx + back * (5 + i)
            strand_y = cy - 8 + i * 2 + int(math.sin(phase * 0.6 + i) * 1)
            end_x = strand_x + back * 3
            end_y = strand_y + 4
            pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_darkest"],
                             (strand_x, strand_y), (end_x, end_y), 2)
            pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_dark"],
                             (strand_x, strand_y), (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["hair_mid"],
                             (end_x, end_y, 1, 1))
        # EYES - fierce spirit orange
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Sockets (heavy brow)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 3, 2))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 3, 2))
        # Brow line (bushy white)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_darkest"],
                         (cx - 4, cy - 6), (cx - 1, cy - 6), 1)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_darkest"],
                         (cx + 1, cy - 6), (cx + 4, cy - 6), 1)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_light"],
                         (cx - 4, cy - 7), (cx - 1, cy - 7), 1)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_light"],
                         (cx + 1, cy - 7), (cx + 4, cy - 7), 1)
        # Whites
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["skin_shine"],
                         (cx - 2, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["skin_shine"],
                         (cx + 2, cy - 5, 2, 2))
        # Orange spirit pupils
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_dark"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_dark"],
                         (cx + 2, cy - 5, 1, 2))
        # Glow
        for r in range(3, 0, -1):
            alpha = _NS_thorvin._alpha(100 * (3 - r) / 3 * eye_pulse)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                   (cx - 2, cy - 4), r)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                   (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_shine"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_shine"],
                         (cx + 2, cy - 4, 1, 1))
        # Nose (big prominent)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["skin_darkest"],
                         (cx, cy - 2, 1, 3))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["skin_dark"],
                         (cx - 1, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["skin_light"],
                         (cx + facing, cy - 2, 1, 1))
        # BIG WHITE BEARD (covers mouth and lower face, flowing)
        beard_wave = math.sin(phase * 0.4) * 1
        beard_pts = [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 6, cy + 8 + int(beard_wave)),
            (cx - 4, cy + 12 + int(beard_wave)),
            (cx - 2, cy + 14 + int(beard_wave)),
            (cx, cy + 15 + int(beard_wave)),
            (cx + 2, cy + 14 + int(beard_wave)),
            (cx + 4, cy + 12 + int(beard_wave)),
            (cx + 6, cy + 8 + int(beard_wave)),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ]
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["hair_darkest"],
                          beard_pts)
        # Beard shading
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["hair_dark"], [
            (cx - 5, cy + 2),
            (cx - 5, cy + 7),
            (cx - 3, cy + 11),
            (cx, cy + 13),
            (cx + 3, cy + 11),
            (cx + 5, cy + 7),
            (cx + 5, cy + 2),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_thorvin._poly(surface, _NS_thorvin.PALETTE["hair_mid"], [
            (cx - 4, cy + 3),
            (cx - 4, cy + 6),
            (cx - 2, cy + 9),
            (cx, cy + 11),
            (cx + 2, cy + 9),
            (cx + 4, cy + 6),
            (cx + 4, cy + 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        # Beard highlight streaks
        for i, x_off in enumerate((-2, 0, 2)):
            pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_light"],
                             (cx + x_off, cy + 5 + i),
                             (cx + x_off, cy + 10 + i), 1)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["hair_shine"],
                         (cx, cy + 6, 1, 1))
        # Mustache (part of beard)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_dark"],
                         (cx - 3, cy + 1), (cx - 1, cy + 2), 2)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_dark"],
                         (cx + 3, cy + 1), (cx + 1, cy + 2), 2)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_mid"],
                         (cx - 3, cy + 1), (cx - 1, cy + 2), 1)
        pygame.draw.line(surface, _NS_thorvin.PALETTE["hair_mid"],
                         (cx + 3, cy + 1), (cx + 1, cy + 2), 1)
    # ============================================================
    # SWING TRAIL (during melee attack)
    # ============================================================
    def _draw_swing_trail(surface, boss, x, y, progress):
        """Arc-shaped swing trail for hammer strike."""
        if not (0.35 <= progress <= 0.7):
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.35
        # Arc from up-back to down-front
        arc_center = (x, y - 2)
        arc_r = 26
        # Draw arc segments
        num_segs = 12
        arc_start = -math.pi * 0.8
        arc_end = math.pi * 0.3
        # Full sweep progress: reveal segments as t increases
        max_seg = int(num_segs * min(1.0, t * 1.3))
        for i in range(max_seg):
            seg_t = i / num_segs
            angle = arc_start + (arc_end - arc_start) * seg_t
            px = arc_center[0] + int(math.cos(angle) * arc_r) * facing
            py = arc_center[1] + int(math.sin(angle) * arc_r)
            fade = (max_seg - i) / max(1, max_seg)
            alpha = _NS_thorvin._alpha(220 * fade)
            size = max(1, 4 - i // 3)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                   (px, py), size + 1)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                   (px, py), size)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_light"], alpha),
                                   (px, py), max(1, size - 1))
            pygame.draw.rect(surface,
                             (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                             (px, py, 1, 1))
        # Impact burst near strike apex
        if 0.5 < progress < 0.65:
            imp_t = (progress - 0.5) / 0.15
            imp_x = x + facing * 24
            imp_y = y + 4
            imp_r = int(4 + imp_t * 12)
            alpha = _NS_thorvin._alpha(240 * (1 - imp_t))
            for r in range(imp_r, 0, -2):
                a = _NS_thorvin._alpha(alpha * r / imp_r)
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_mid"], a),
                                       (imp_x, imp_y), r, 2)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                   (imp_x, imp_y), max(1, imp_r // 3))
            for i in range(8):
                angle = i * math.pi / 4
                ex = imp_x + int(math.cos(angle) * imp_r)
                ey = imp_y + int(math.sin(angle) * imp_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_thorvin.PALETTE["spirit_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(12, 0, -1):
            alpha = int(max(0, (12 - radius) * 18) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 13 - radius,
                                 104 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, int(160 * mult)),
                            (4, 6, 112, 14))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_spirit_aura(surface, x, y, phase):
        """Warm orange spirit aura."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_thorvin._alpha((85 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_thorvin._aacircle(aura,
                                       (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                       (100, 80), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_thorvin._alpha((50 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_thorvin._aacircle(aura,
                                       (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                       (100, 80), radius)
        for radius in range(25, 5, -2):
            alpha = _NS_thorvin._alpha((25 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_thorvin._aacircle(aura,
                                       (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                       (100, 80), radius)
        surface.blit(aura, (x - 100, y - 80))
        # Floating embers
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 36 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thorvin.PALETTE["spirit_dark"], 200),
                            (5, 18, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_thorvin.PALETTE["spirit_mid"], 210),
                            (14, 20, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_thorvin.PALETTE["spirit_light"], 220),
                            (24, 22, 112, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 44)
            y1 = 28 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 66)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_thorvin.PALETTE["spirit_hot"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_thorvin.PALETTE["spirit_shine"],
                                       _NS_thorvin._alpha(150 * pulse)),
                                (15, 12, 130, 36), 1)
        surface.blit(ring, (x - 80, y - 25))
    def _draw_float_wisps(surface, cx, cy, phase, facing):
        """Wisps under floating body."""
        for i in range(7):
            t = (phase * 0.5 + i * 0.14) % 1.0
            wx = cx + int(math.sin(phase + i) * 10) - facing * i * 2
            wy = cy + int(t * 10)
            alpha = _NS_thorvin._alpha(180 * (1 - t))
            if alpha > 0:
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                       (wx, wy), 3)
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # PASSIVE - TOUGH (green shield around boss when active)
    # ============================================================
    def _draw_tough_shield(surface, boss, x, y, phase):
        """Green translucent shield bubble."""
        r = 40
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Rings
        for i, (thick, alpha) in enumerate([(3, 100), (2, 140), (1, 180)]):
            a = _NS_thorvin._alpha(alpha * pulse)
            _NS_thorvin._aacircle(bubble,
                                   (*_NS_thorvin.PALETTE["guard_dark"], a),
                                   center, r - i, thick)
            _NS_thorvin._aacircle(bubble,
                                   (*_NS_thorvin.PALETTE["guard_mid"], a),
                                   center, r - i - 1, 1)
        # Sparkles along edge
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_thorvin.PALETTE["guard_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_thorvin.PALETTE["guard_hot"],
                             (sx, sy, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
    # ============================================================
    # SKILL: Q - SACRED WHEEL (spinning wheel that returns)
    # ============================================================
    def _draw_sacred_wheel(surface, boss, x, y, timer, phase):
        """Spinning gold wheel that flies out and returns (boomerang)."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_thorvin._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 2
        # Wheel travel: out (0 → 0.5) then return (0.5 → 1.0)
        if progress < 0.5:
            t = progress / 0.5
            wx = int(start_x + (tx - start_x) * t)
            wy = int(start_y + (ty - start_y) * t)
        else:
            t = (progress - 0.5) / 0.5
            wx = int(tx + (start_x - tx) * t)
            wy = int(ty + (start_y - ty) * t)
        # Spinning rotation
        spin = phase * 6
        # Motion trail (short arc trail)
        for i in range(6):
            trail_t = max(0.0, min(1.0, progress - i * 0.03))
            if trail_t < 0.5:
                tt = trail_t / 0.5
                px = int(start_x + (tx - start_x) * tt)
                py = int(start_y + (ty - start_y) * tt)
            else:
                tt = (trail_t - 0.5) / 0.5
                px = int(tx + (start_x - tx) * tt)
                py = int(ty + (start_y - ty) * tt)
            alpha = _NS_thorvin._alpha(180 - i * 25)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                   (px, py), max(2, 8 - i))
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                   (px, py), max(1, 6 - i))
        # Wheel itself
        r = 10
        # Outer ring
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shadow_deep"],
                               (wx + 1, wy + 1), r + 1)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_dark"],
                               (wx, wy), r)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_mid"],
                               (wx, wy), r - 1)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["gold_light"],
                               (wx, wy), r - 2, 1)
        # Inner hole
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["shadow_deep"],
                               (wx, wy), r - 4)
        # Spokes (rotating)
        for i in range(4):
            spoke_angle = spin + i * math.pi / 2
            x2 = wx + int(math.cos(spoke_angle) * (r - 1))
            y2 = wy + int(math.sin(spoke_angle) * (r - 1))
            pygame.draw.line(surface, _NS_thorvin.PALETTE["gold_dark"],
                             (wx, wy), (x2, y2), 2)
            pygame.draw.line(surface, _NS_thorvin.PALETTE["gold_shine"],
                             (wx, wy), (x2, y2), 1)
        # Central spirit orb
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        for cr in range(5, 0, -1):
            a = _NS_thorvin._alpha(180 * (5 - cr) / 5 * pulse)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_light"], a),
                                   (wx, wy), cr)
        _NS_thorvin._aacircle(surface, _NS_thorvin.PALETTE["spirit_hot"],
                               (wx, wy), 2)
        pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_shine"],
                         (wx, wy, 1, 1))
        # Motion sparks
        for i in range(4):
            angle = spin + i * math.pi / 2
            sx = wx + int(math.cos(angle) * (r + 3))
            sy = wy + int(math.sin(angle) * (r + 3))
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_hot"],
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: W - INDESTRUCTIBLE (bubble + speed)
    # ============================================================
    def _draw_indestructible_ground(surface, boss, x, y, timer, phase):
        """Ground rings when indestructible active."""
        for i in range(2):
            r = int(30 + i * 6 + math.sin(phase * 2) * 3)
            alpha = _NS_thorvin._alpha(200 - i * 60)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                   (x, y + 40), r, 2)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                   (x, y + 40), r, 1)
    def _draw_indestructible_bubble(surface, boss, x, y, timer, phase):
        """Bright orange bubble armor."""
        r = 42
        pulse = math.sin(phase * 2) * 0.25 + 0.75
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Rings
        for i, (thick, alpha) in enumerate([(4, 100), (3, 140), (2, 180), (1, 220)]):
            a = _NS_thorvin._alpha(alpha * pulse)
            _NS_thorvin._aacircle(bubble,
                                   (*_NS_thorvin.PALETTE["spirit_dark"], a),
                                   center, r - i, thick)
            _NS_thorvin._aacircle(bubble,
                                   (*_NS_thorvin.PALETTE["spirit_mid"], a),
                                   center, r - i - 1, 1)
        # Bright sparkles
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_thorvin.PALETTE["spirit_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_thorvin.PALETTE["spirit_hot"],
                             (sx, sy, 1, 1))
        # Inner glow orbs
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            inner_r = r - 8
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            _NS_thorvin._aacircle(bubble, _NS_thorvin.PALETTE["spirit_mid"],
                                   (bx, by), 3)
            _NS_thorvin._aacircle(bubble, _NS_thorvin.PALETTE["spirit_hot"],
                                   (bx, by), 1)
        surface.blit(bubble, (x - r - 10, y - r - 10))
    # ============================================================
    # SKILL: E - COUNTER ASSAULT (reflect bullets from shield)
    # ============================================================
    def _draw_counter_assault(surface, boss, x, y, timer, phase):
        """Shield glows brightly and shoots deflection sparks forward."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Position roughly at shield
        shield_x = x + facing * 18
        shield_y = y - 4
        # Big shield glow
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(24, 4, -3):
            alpha = _NS_thorvin._alpha(200 * (24 - r) / 24 * pulse)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_light"], alpha),
                                   (shield_x, shield_y), r)
        # Deflection sparks flying forward
        num_sparks = 6
        for i in range(num_sparks):
            spark_t = (phase * 0.8 + i * 0.15) % 1.0
            spark_dist = int(spark_t * 100)
            offset_y = int(math.sin(phase * 2 + i) * 20)
            sx = shield_x + facing * spark_dist
            sy = shield_y + offset_y - int(spark_dist * 0.1)
            alpha = _NS_thorvin._alpha(240 * (1 - spark_t))
            if alpha > 0:
                # Trail
                for tr in range(4):
                    tt = max(0, spark_dist - tr * 8)
                    tx_ = shield_x + facing * tt
                    ty_ = shield_y + offset_y - int(tt * 0.1)
                    ta = _NS_thorvin._alpha(alpha - tr * 40)
                    _NS_thorvin._aacircle(surface,
                                           (*_NS_thorvin.PALETTE["spirit_mid"], ta),
                                           (tx_, ty_), max(1, 3 - tr))
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                       (sx, sy), 3)
                _NS_thorvin._aacircle(surface,
                                       (*_NS_thorvin.PALETTE["spirit_shine"], alpha),
                                       (sx, sy), 1)
                # Streak
                pygame.draw.line(surface,
                                 (*_NS_thorvin.PALETTE["spirit_light"], alpha),
                                 (sx - facing * 4, sy),
                                 (sx, sy), 2)
    # ============================================================
    # SKILL: R - AVENGING WRATH (leap slam)
    # ============================================================
    def _draw_avenging_ground(surface, boss, x, y, timer, phase):
        """Big impact circle at target with runes."""
        tx, ty = _NS_thorvin._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growing warning ring
        if progress < 0.4:
            t = progress / 0.4
            r = int(50 * t)
        else:
            r = 50 + int(math.sin(phase * 2) * 4)
        alpha = _NS_thorvin._alpha(220 * min(1.0, progress * 2))
        # Multi-ring
        pygame.draw.ellipse(surface, (*_NS_thorvin.PALETTE["spirit_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 3)
        pygame.draw.ellipse(surface, (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                            (tx - r + 8, ty - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 2)
        pygame.draw.ellipse(surface, (*_NS_thorvin.PALETTE["spirit_light"], alpha),
                            (tx - r + 14, ty - r // 3 + 6,
                             r * 2 - 28, r * 2 // 3 - 12), 1)
        # Rotating runes
        for i in range(10):
            angle = phase * 1.5 + i * math.pi / 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_hot"],
                             (sx - 1, sy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_thorvin.PALETTE["spirit_shine"],
                             (sx, sy, 1, 1))
    def _draw_avenging_foreground(surface, boss, x, y, timer, phase):
        """Boss leaps and slams — rising ground pillars + impact."""
        tx, ty = _NS_thorvin._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Wind-up — energy gathers on boss
            t = progress / 0.4
            # Rising spirit tendrils around boss
            for i in range(8):
                angle = phase + i * math.pi / 4
                rise_t = (phase + i * 0.15) % 1.0
                rx = x + int(math.cos(angle) * 20)
                ry = y - int(rise_t * 30)
                alpha = _NS_thorvin._alpha(220 * t * (1 - rise_t))
                if alpha > 0:
                    _NS_thorvin._aacircle(surface,
                                           (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                           (rx, ry), 3)
                    _NS_thorvin._aacircle(surface,
                                           (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                           (rx, ry), 2)
        elif progress < 0.7:
            # Slam phase — massive impact
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)
            # Massive impact explosion
            imp_r = int(20 + t * 40)
            alpha = _NS_thorvin._alpha(240 * intensity)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_darkest"], alpha),
                                   (tx, ty), imp_r + 4, 4)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                   (tx, ty), imp_r, 3)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                   (tx, ty), max(1, imp_r - 8), 2)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_light"], alpha),
                                   (tx, ty), max(1, imp_r - 15), 1)
            _NS_thorvin._aacircle(surface,
                                   (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                   (tx, ty), max(1, imp_r // 4))
            # Radial ground shockwave
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * imp_r)
                ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                pygame.draw.line(surface,
                                 (*_NS_thorvin.PALETTE["spirit_light"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_thorvin.PALETTE["spirit_shine"], alpha),
                                 (ex, ey, 1, 1))
            # Ground pillars rising around impact
            for i in range(8):
                pillar_angle = i * math.pi / 4
                pillar_dist = int(imp_r * 0.8)
                px = tx + int(math.cos(pillar_angle) * pillar_dist)
                py = ty + int(math.sin(pillar_angle) * pillar_dist * 0.5)
                pillar_h = int(15 * intensity)
                for py_off in range(pillar_h):
                    py_off_alpha = _NS_thorvin._alpha(alpha * (pillar_h - py_off) / pillar_h)
                    pygame.draw.rect(surface,
                                     (*_NS_thorvin.PALETTE["spirit_mid"], py_off_alpha),
                                     (px - 2, py - py_off, 4, 1))
                    if py_off < 3:
                        pygame.draw.rect(surface,
                                         (*_NS_thorvin.PALETTE["spirit_hot"], py_off_alpha),
                                         (px - 1, py - py_off, 2, 1))
        else:
            # Aftermath — rising smoke/embers
            t = (progress - 0.7) / 0.3
            for i in range(12):
                rise_t = (phase * 0.7 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 35)
                alpha = _NS_thorvin._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_thorvin._aacircle(surface,
                                           (*_NS_thorvin.PALETTE["spirit_dark"], alpha),
                                           (rx, ry), 3)
                    _NS_thorvin._aacircle(surface,
                                           (*_NS_thorvin.PALETTE["spirit_mid"], alpha),
                                           (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_thorvin.PALETTE["spirit_hot"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# XAERISSA (WEAVER OF CRIMSON SILK) - Mini Boss
# ====================================================================

class _NS_xaerissa:
    """Namespace xaerissa - spider queen mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Deep crimson red (spider legs, chitin)
        "crimson_darkest": (30, 3, 8),
        "crimson_dark": (75, 10, 20),
        "crimson_mid": (150, 25, 45),
        "crimson_light": (210, 60, 85),
        "crimson_hot": (245, 110, 130),
        "crimson_shine": (255, 190, 200),
        # Black chitin/armor
        "chitin_darkest": (3, 3, 5),
        "chitin_dark": (12, 12, 18),
        "chitin_mid": (30, 28, 40),
        "chitin_light": (60, 55, 75),
        "chitin_edge": (100, 95, 120),
        # Magenta/purple magic (venom, magic aura)
        "venom_darkest": (30, 5, 40),
        "venom_dark": (75, 20, 100),
        "venom_mid": (150, 45, 190),
        "venom_light": (215, 100, 245),
        "venom_hot": (245, 155, 255),
        "venom_shine": (255, 220, 255),
        # Pale skin
        "skin_darkest": (85, 65, 75),
        "skin_dark": (145, 115, 125),
        "skin_mid": (200, 170, 180),
        "skin_light": (235, 210, 215),
        "skin_shine": (250, 235, 235),
        # Black hair
        "hair_darkest": (5, 3, 12),
        "hair_dark": (18, 10, 30),
        "hair_mid": (45, 30, 60),
        "hair_light": (80, 60, 100),
        "hair_shine": (125, 100, 145),
        # Bright red glowing eyes
        "eye_socket": (5, 2, 4),
        "eye_dark": (95, 5, 20),
        "eye_mid": (220, 25, 40),
        "eye_light": (255, 85, 90),
        "eye_glow": (255, 200, 180),
        # Gold accents
        "gold_dark": (75, 55, 15),
        "gold_mid": (155, 120, 40),
        "gold_light": (220, 185, 90),
        "gold_shine": (255, 235, 160),
        # Web / silk (white translucent)
        "web_dark": (100, 100, 115),
        "web_mid": (180, 180, 195),
        "web_light": (235, 235, 245),
        # Shadow mist
        "mist_dark": (25, 8, 35),
        "mist_mid": (75, 25, 100),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xaerissa._clamp(color)
        if _NS_xaerissa.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xaerissa._clamp(color)
        if _NS_xaerissa.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xaerissa._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xaerissa(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xaerissa._detect_moving(boss)
        _NS_xaerissa._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xae_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_xaerissa._draw_web_backdrop(surface, x, y, pulse)
        _NS_xaerissa._draw_crimson_aura(surface, x, y, pulse)
        _NS_xaerissa._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_xaerissa._draw_spiderling_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xaerissa._draw_arachnoid_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_xaerissa._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_xaerissa._draw_float_move(surface, boss, x, y)
        else:
            _NS_xaerissa._draw_float_idle(surface, boss, x, y)
        # Arachnoid form (transformation glow)
        if active_skill == "r":
            _NS_xaerissa._draw_arachnoid_aura(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_xaerissa._draw_neurotoxin_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xaerissa._draw_spiderling_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xaerissa._draw_cocoon_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xae_previous_timer", 0))
        active = bool(getattr(boss, "_xae_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._xae_attack_active = True
            boss._xae_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xae_attack_frame = int(getattr(boss, "_xae_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._xae_attack_active = False
            boss._xae_attack_frame = 0
            active = False
        boss._xae_previous_timer = timer
        boss._xae_attack_progress = (
            min(1.0, getattr(boss, "_xae_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_xae_last_x"):
            boss._xae_last_x = boss.x
            boss._xae_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xae_last_x)
        dy = abs(boss.y - boss._xae_last_y)
        boss._xae_last_x = boss.x
        boss._xae_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.7) * 5) - 10
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_xaerissa._draw_float_shadow(surface, x + sway, y + 52, boss.pulse)
        _NS_xaerissa._draw_venom_mist(surface, x + sway, y + 42, boss.pulse)
        _NS_xaerissa._draw_body(surface, x + sway, y + hover,
                                boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        hover = int(math.sin(phase * 0.9) * 6) - 11
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_xaerissa._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_xaerissa._draw_venom_mist(surface, x + sway, y + 42, phase,
                                      trail=True, facing=boss.direction)
        _NS_xaerissa._draw_body(surface, x + sway, y + hover,
                                boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Ranged bite - venom projectile from hand."""
        progress = getattr(boss, "_xae_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.4:
            t = progress / 0.4
            lean = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            lean = int((-3 + t * 8)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        hover = int(math.sin(boss.pulse * 0.7) * 3) - 8
        _NS_xaerissa._draw_float_shadow(surface, x + lean, y + 52, boss.pulse)
        _NS_xaerissa._draw_venom_mist(surface, x + lean, y + 42,
                                      boss.pulse, intense=True)
        _NS_xaerissa._draw_body(surface, x + lean, y + hover - lift,
                                boss.direction, boss.pulse,
                                "attack", progress)
        _NS_xaerissa._draw_venom_projectile(surface, boss, x + lean,
                                            y + hover - lift, progress)
    # ============================================================
    # BODY - Spider Queen
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # SPIDER LEGS FIRST (behind body, 8 legs - 4 pairs)
        _NS_xaerissa._draw_spider_legs(surface, cx, cy, facing, phase, action)
        # Torso
        _NS_xaerissa._draw_spider_torso(surface, cx, cy, facing, phase)
        # Skirt/lower body (dangling)
        _NS_xaerissa._draw_gothic_skirt(surface, cx, cy + 8, facing, phase, action)
        # Back arm
        _NS_xaerissa._draw_back_arm(surface, cx, cy - 2, facing, phase)
        # Head with crown + long black hair
        _NS_xaerissa._draw_queen_head(surface, cx, cy - 20, facing, phase,
                                      action, attack_progress)
        # Front arm (casting hand - LAST for priority)
        _NS_xaerissa._draw_casting_arm(surface, cx, cy - 2, facing, phase, action,
                                       attack_progress)
    def _draw_spider_legs(surface, cx, cy, facing, phase, action):
        """8 spider legs sprouting from her back/shoulders (like reference)."""
        # 8 legs total, 4 pairs on each side
        # Reference shows: 2 upper legs going up-outward, 2 lower legs going down-outward
        # Actually in reference: 4 pairs of legs visible
        for side in (-1, 1):
            for leg_i, (base_off_y, tip_angle_deg, tip_length, thickness) in enumerate([
                # (base_y_offset, angle_from_horizontal_deg, length, thickness)
                (-6, 70, 32, 5),    # topmost leg (highest)
                (-3, 40, 30, 5),    # upper leg
                (0, 5, 28, 4),      # middle leg
                (3, -30, 26, 4),    # lower leg
            ]):
                base_x = cx + side * 6
                base_y = cy + base_off_y
                # Animated leg (subtle wave)
                wave = math.sin(phase * 1.5 + leg_i * 0.5 + side * 0.3) * 2
                tip_angle = math.radians(tip_angle_deg + wave)
                # Joint (bent midway - spider legs are jointed)
                joint_x = base_x + int(math.cos(tip_angle) * tip_length * 0.5) * side
                joint_y = base_y - int(math.sin(tip_angle) * tip_length * 0.5)
                # Then curves down slightly for spider-leg look
                curve_angle = math.radians(tip_angle_deg - 30 + wave * 0.5)
                tip_x = joint_x + int(math.cos(curve_angle) * tip_length * 0.55) * side
                tip_y = joint_y - int(math.sin(curve_angle) * tip_length * 0.55) + int(tip_length * 0.15)
                # UPPER SEGMENT (base to joint)
                # Shadow
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                                 (base_x + 1, base_y + 1),
                                 (joint_x + 1, joint_y + 1), thickness + 1)
                # Dark chitin
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                                 (base_x, base_y),
                                 (joint_x, joint_y), thickness)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_dark"],
                                 (base_x, base_y),
                                 (joint_x, joint_y), thickness - 1)
                # RED CHITIN edge (crimson stripe along top)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                                 (base_x, base_y - 1),
                                 (joint_x, joint_y - 1), max(1, thickness - 2))
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                 (base_x, base_y - 1),
                                 (joint_x, joint_y - 1), max(1, thickness - 3))
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                                 (base_x, base_y - 2),
                                 (joint_x, joint_y - 2), 1)
                # Joint knuckle (small circle)
                _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                                       (joint_x, joint_y), thickness // 2 + 1)
                _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                                       (joint_x, joint_y), thickness // 2 + 1)
                _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                       (joint_x, joint_y), thickness // 2)
                _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                                       (joint_x, joint_y), max(1, thickness // 2 - 1))
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                                 (joint_x, joint_y, 1, 1))
                # LOWER SEGMENT (joint to tip) - thinner
                lower_thickness = max(2, thickness - 1)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                                 (joint_x + 1, joint_y + 1),
                                 (tip_x + 1, tip_y + 1), lower_thickness + 1)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                                 (joint_x, joint_y),
                                 (tip_x, tip_y), lower_thickness)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_dark"],
                                 (joint_x, joint_y),
                                 (tip_x, tip_y), lower_thickness - 1)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                                 (joint_x, joint_y - 1),
                                 (tip_x, tip_y - 1), max(1, lower_thickness - 2))
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                 (joint_x, joint_y - 1),
                                 (tip_x, tip_y - 1), max(1, lower_thickness - 3))
                # SHARP CLAW tip
                # Direction of tip
                claw_angle = math.atan2(tip_y - joint_y, (tip_x - joint_x) * side)
                claw_len = 4
                claw_end_x = tip_x + int(math.cos(claw_angle) * claw_len) * side
                claw_end_y = tip_y + int(math.sin(claw_angle) * claw_len)
                # Perpendicular for claw shape
                perp = claw_angle + math.pi / 2
                claw_a = (tip_x + int(math.cos(perp) * 2),
                          tip_y + int(math.sin(perp) * 2))
                claw_b = (tip_x - int(math.cos(perp) * 2),
                          tip_y - int(math.sin(perp) * 2))
                _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["shadow_deep"], [
                    (claw_end_x + 1, claw_end_y + 1),
                    (claw_a[0] + 1, claw_a[1] + 1),
                    (claw_b[0] + 1, claw_b[1] + 1),
                ])
                _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                                   [(claw_end_x, claw_end_y), claw_a, claw_b])
                _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                                   [(claw_end_x, claw_end_y),
                                    (int((claw_end_x + claw_a[0]) / 2),
                                     int((claw_end_y + claw_a[1]) / 2)),
                                    (tip_x, tip_y)])
                _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                   [(claw_end_x, claw_end_y),
                                    (int((claw_end_x + tip_x) / 2),
                                     int((claw_end_y + tip_y) / 2)),
                                    (tip_x, tip_y)])
                # Bright red claw tip
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                                 (claw_end_x, claw_end_y, 1, 1))
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_shine"],
                                 (claw_end_x, claw_end_y, 1, 1))
    def _draw_spider_torso(surface, cx, cy, facing, phase):
        """Feminine torso with black corset + red chitin details."""
        breath = math.sin(phase * 0.7) * 1
        torso_pts = [
            (cx - 8, cy - 5),
            (cx - 9, cy),
            (cx - 8, cy + 6),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 8, cy + 6),
            (cx + 9, cy),
            (cx + 8, cy - 5),
        ]
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        # Base skin (visible)
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_dark"], torso_pts)
        # Black corset
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_darkest"], [
            (cx - 8, cy - 3),
            (cx - 9, cy + 1),
            (cx - 8, cy + 6),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 8, cy + 6),
            (cx + 9, cy + 1),
            (cx + 8, cy - 3),
        ])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_dark"], [
            (cx - 7, cy - 2),
            (cx - 8, cy + 1),
            (cx - 7, cy + 5),
            (cx - 4, cy + 8),
            (cx + 4, cy + 8),
            (cx + 7, cy + 5),
            (cx + 8, cy + 1),
            (cx + 7, cy - 2),
        ])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_mid"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 1),
            (cx - 6, cy + 4),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 4),
            (cx + 7, cy + 1),
            (cx + 6, cy - 1),
        ])
        # Chitin edge highlights
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_edge"],
                         (cx - 5, cy), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_edge"],
                         (cx + 5, cy), (cx + 5, cy + 6), 1)
        # SKIN cleavage V-neck (pale)
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_mid"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_light"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 1, cy - 3),
            (cx - 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_shine"],
                         (cx, cy - 4, 1, 1))
        # CRIMSON GEM in center of chest (like spider abdomen jewel)
        gem_cx = cx
        gem_cy = cy + 3
        # Gem base (diamond shape)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (gem_cx - 2, gem_cy - 2, 4, 4))
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_darkest"], [
            (gem_cx, gem_cy - 2),
            (gem_cx + 2, gem_cy),
            (gem_cx, gem_cy + 2),
            (gem_cx - 2, gem_cy),
        ])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_dark"], [
            (gem_cx, gem_cy - 1),
            (gem_cx + 1, gem_cy),
            (gem_cx, gem_cy + 1),
            (gem_cx - 1, gem_cy),
        ])
        # Bright pulse
        pulse = math.sin(phase * 3) * 0.4 + 0.6
        for r in range(4, 0, -1):
            alpha = _NS_xaerissa._alpha(180 * (4 - r) / 4 * pulse)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["crimson_mid"], alpha),
                                   (gem_cx, gem_cy), r)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                         (gem_cx, gem_cy, 1, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_shine"],
                         (gem_cx, gem_cy, 1, 1))
        # Corset lacing (red X pattern)
        for i in range(3):
            ly = cy + 1 + i * 2
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                             (cx - 2, ly), (cx + 2, ly + 1), 1)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                             (cx - 2, ly + 1), (cx + 2, ly), 1)
        # BLACK BELT with red gem
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                         (cx - 7, cy + 8, 14, 2))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["chitin_dark"],
                         (cx - 7, cy + 8, 14, 1))
        # Red buckle
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                         (cx - 2, cy + 8, 5, 2))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                         (cx - 1, cy + 8, 3, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                         (cx, cy + 8, 1, 1))
        # CHITIN PLATING on chest (red plates like spider abdomen)
        # Small red chitin ridges on shoulders
        for side in (-1, 1):
            for cy_off in (-3, 0):
                plate_x = cx + side * 6
                plate_y = cy + cy_off
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                                 (plate_x - 1, plate_y, 2, 1))
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                 (plate_x - 1, plate_y, 2, 1))
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                                 (plate_x - 1, plate_y, 1, 1))
    def _draw_gothic_skirt(surface, cx, cy, facing, phase, action):
        """Dark gothic skirt dangling."""
        sway1 = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7) * 2
        skirt_pts = [
            (cx - 7, cy),
            (cx - 9 + int(sway1 * 0.3), cy + 7),
            (cx - 11 + int(sway1 * 0.6), cy + 15),
            (cx - 12 + int(sway1), cy + 22),
            (cx - 10 + int(sway1 * 0.9), cy + 27),
            (cx - 5 + int(sway2 * 0.5), cy + 30),
            (cx + int(sway2), cy + 32),
            (cx + 5 + int(sway2 * 0.5), cy + 30),
            (cx + 10 + int(sway1 * 0.9), cy + 27),
            (cx + 12 + int(sway1), cy + 22),
            (cx + 11 + int(sway1 * 0.6), cy + 15),
            (cx + 9 + int(sway1 * 0.3), cy + 7),
            (cx + 7, cy),
        ]
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in skirt_pts])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_darkest"], skirt_pts)
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_dark"], [
            (cx - 6, cy + 1),
            (cx - 8 + int(sway1 * 0.3), cy + 7),
            (cx - 10 + int(sway1 * 0.6), cy + 15),
            (cx - 10 + int(sway1), cy + 22),
            (cx - 8 + int(sway1 * 0.9), cy + 25),
            (cx - 4 + int(sway2 * 0.5), cy + 28),
            (cx + int(sway2), cy + 29),
            (cx + 4 + int(sway2 * 0.5), cy + 28),
            (cx + 8 + int(sway1 * 0.9), cy + 25),
            (cx + 10 + int(sway1), cy + 22),
            (cx + 10 + int(sway1 * 0.6), cy + 15),
            (cx + 8 + int(sway1 * 0.3), cy + 7),
            (cx + 6, cy + 1),
        ])
        # Vertical fold highlights
        for fold_x_off in (-6, -3, 0, 3, 6):
            fold_x_top = cx + fold_x_off
            fold_x_bot = cx + fold_x_off + int(sway1 * (abs(fold_x_off) / 6))
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_mid"],
                             (fold_x_top, cy + 3), (fold_x_bot, cy + 26), 1)
            if fold_x_off in (-3, 3):
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_light"],
                                 (fold_x_top, cy + 3),
                                 (fold_x_bot, cy + 22), 1)
        # RED CHITIN TRIM at bottom (like spider abdomen)
        for i, ex in enumerate(range(-10, 12, 3)):
            ex_x = cx + ex + int(sway1 * 0.7)
            ex_y = cy + 28
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                             (ex_x, ex_y, 2, 2))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                             (ex_x, ex_y, 2, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                             (ex_x, ex_y, 1, 1))
        # Magic glow at bottom edges (venom drip)
        for edge_x_off in (-10, -5, 0, 5, 10):
            edge_x = cx + edge_x_off + int(sway1 * 0.7)
            edge_y = cy + 30
            glow_alpha = _NS_xaerissa._alpha(120 + math.sin(phase * 2 + edge_x_off) * 40)
            pygame.draw.rect(surface,
                             (*_NS_xaerissa.PALETTE["venom_dark"], glow_alpha),
                             (edge_x, edge_y, 1, 2))
            pygame.draw.rect(surface,
                             (*_NS_xaerissa.PALETTE["venom_light"], glow_alpha),
                             (edge_x, edge_y + 1, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm hanging."""
        back_shoulder_x = cx - facing * 5
        back_shoulder_y = cy - 2
        arm_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.1
        arm_length = 12
        back_hand_x = back_shoulder_x - int(math.cos(arm_angle) * arm_length) * facing
        back_hand_y = back_shoulder_y + int(math.sin(arm_angle) * arm_length)
        elbow_x = back_shoulder_x - int(math.cos(arm_angle) * (arm_length * 0.5)) * facing
        elbow_y = back_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.5))
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 4)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_mid"],
                         (back_shoulder_x - 1, back_shoulder_y),
                         (elbow_x - 1, elbow_y), 1)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 4)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 2)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (back_hand_x - 1, back_hand_y), 1)
        # Small hand with claws
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_dark"],
                         (back_hand_x - 1, back_hand_y, 3, 3))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_mid"],
                         (back_hand_x - 1, back_hand_y, 2, 2))
        # Red claw fingernails
        for i in range(3):
            claw_x = back_hand_x - facing * i
            claw_y = back_hand_y + 3
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                             (claw_x, claw_y, 1, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                             (claw_x, claw_y, 1, 1))
    def _draw_casting_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm extended - casting venom bite."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 2
        if action == "attack":
            if attack_progress < 0.4:
                t = attack_progress / 0.4
                arm_angle = -math.pi * 0.15 * (1 - t) - math.pi * 0.3 * t
            elif attack_progress < 0.6:
                t = (attack_progress - 0.4) / 0.2
                arm_angle = -math.pi * 0.3 + math.pi * 0.4 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.1 * (1 - t)
        else:
            arm_angle = math.pi * 0.05 + math.sin(phase * 0.6) * 0.08
        arm_length = 14
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 2
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 1
        # Upper arm (skin - slender)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_mid"],
                         (shoulder_x - 1, shoulder_y), (elbow_x - 1, elbow_y), 2)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_light"],
                         (shoulder_x - 1, shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Forearm
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 5)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (hand_x - 1, hand_y), 2)
        # Palm (open with sharp red nails)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (hand_x - 2, hand_y - 1, 5, 5))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_darkest"],
                         (hand_x - 2, hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_dark"],
                         (hand_x - 2, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_mid"],
                         (hand_x - 1, hand_y - 1, 3, 2))
        # Sharp red-black claws (fingernails)
        for i in range(4):
            claw_angle = arm_angle + math.pi * 0.1 - i * math.pi * 0.07
            claw_len = 4
            claw_tip_x = hand_x + int(math.cos(claw_angle) * claw_len) * facing
            claw_tip_y = hand_y + int(math.sin(claw_angle) * claw_len) + 1
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                             (hand_x + 1, hand_y + 1),
                             (claw_tip_x + 1, claw_tip_y + 1), 2)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                             (hand_x, hand_y),
                             (claw_tip_x, claw_tip_y), 1)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                             (claw_tip_x, claw_tip_y, 1, 1))
        # VENOM ORB in palm (magenta)
        orb_x = hand_x + facing * 3
        orb_y = hand_y + 1
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        if action == "attack":
            orb_size = int(3 + math.sin(attack_progress * math.pi) * 4)
        else:
            orb_size = 3
        for r in range(orb_size + 5, 0, -1):
            alpha = _NS_xaerissa._alpha(150 * (orb_size + 5 - r) / (orb_size + 5) * pulse)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                   (orb_x, orb_y), r)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_darkest"],
                               (orb_x, orb_y), orb_size)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_dark"],
                               (orb_x, orb_y), orb_size - 1)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_mid"],
                               (orb_x, orb_y), max(1, orb_size - 2))
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_light"],
                               (orb_x, orb_y), max(1, orb_size - 3))
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_hot"],
                               (orb_x, orb_y), max(1, orb_size - 4))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["venom_shine"],
                         (orb_x, orb_y, 1, 1))
        # Sparks around orb
        for i in range(4):
            spark_angle = phase * 3 + i * math.pi / 2
            sx = orb_x + int(math.cos(spark_angle) * (orb_size + 3))
            sy = orb_y + int(math.sin(spark_angle) * (orb_size + 3))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["venom_hot"], (sx, sy, 1, 1))
    def _draw_queen_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Beautiful queen face with crown horns + long black hair + red eyes."""
        # Face oval
        head_pts = [
            (cx - 6, cy + 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 6),
            (cx - 2, cy - 9),
            (cx + 3, cy - 9),
            (cx + 6, cy - 6),
            (cx + 7, cy - 2),
            (cx + 6, cy + 3),
            (cx + 3, cy + 6),
            (cx - 2, cy + 6),
            (cx - 5, cy + 4),
        ]
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in head_pts])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_darkest"], head_pts)
        # Face base (pale)
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy - 1),
            (cx - 4, cy - 5),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 5, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 3, cy - 5),
            (cx, cy - 7),
            (cx + 3, cy - 7),
            (cx + 5, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx, cy + 4),
            (cx - 2, cy + 2),
        ])
        # Highlights (cheekbones)
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["skin_light"], [
            (cx + 1, cy - 5),
            (cx + 3, cy - 5),
            (cx + 4, cy - 3),
            (cx + 2, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_shine"],
                         (cx + facing * 2, cy - 4, 1, 1))
        # LONG BLACK HAIR (behind + around head)
        _NS_xaerissa._draw_black_hair(surface, cx, cy, facing, phase)
        # RED CROWN with horns/spikes
        _NS_xaerissa._draw_crown_horns(surface, cx, cy - 5, facing, phase)
        # BRIGHT RED GLOWING EYES
        _NS_xaerissa._draw_glowing_red_eyes(surface, cx, cy - 3, facing, phase, action)
        # Nose
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_darkest"],
                         (cx + facing, cy - 1, 1, 1))
        # DARK RED LIPS
        _NS_xaerissa._draw_dark_lips(surface, cx, cy + 3, facing, phase, action, attack_progress)
        # Small facial mark/tattoo on cheek (spider-like)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                         (cx - facing * 3, cy, 1, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                         (cx - facing * 3, cy, 1, 1))
    def _draw_black_hair(surface, cx, cy, facing, phase):
        """Long flowing black hair."""
        sway1 = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7) * 2
        # Hair bulk behind head
        hair_bulk = [
            (cx - 7, cy - 5),
            (cx - 10, cy - 3),
            (cx - 12, cy + 3),
            (cx - 13, cy + 10 + int(sway2 * 0.5)),
            (cx - 12, cy + 18 + int(sway2)),
            (cx - 9, cy + 22 + int(sway1)),
            (cx - 4, cy + 24 + int(sway1 * 0.8)),
            (cx + 2, cy + 22 + int(sway1 * 0.6)),
            (cx + 7, cy + 18 + int(sway1 * 0.5)),
            (cx + 10, cy + 12 + int(sway2 * 0.6)),
            (cx + 11, cy + 5),
            (cx + 8, cy),
            (cx + 7, cy - 4),
            (cx + 4, cy - 9),
            (cx - 2, cy - 10),
            (cx - 6, cy - 8),
        ]
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                           [(px + 1, py + 2) for px, py in hair_bulk])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["hair_darkest"], hair_bulk)
        # Hair mid tone
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["hair_dark"], [
            (cx - 6, cy - 4),
            (cx - 9, cy - 2),
            (cx - 11, cy + 3),
            (cx - 11, cy + 10 + int(sway2 * 0.4)),
            (cx - 10, cy + 18 + int(sway2 * 0.8)),
            (cx - 6, cy + 20 + int(sway1 * 0.8)),
            (cx + 2, cy + 18 + int(sway1 * 0.6)),
            (cx + 7, cy + 15 + int(sway2 * 0.6)),
            (cx + 9, cy + 8),
            (cx + 8, cy + 2),
            (cx + 6, cy - 5),
            (cx + 3, cy - 8),
            (cx - 2, cy - 9),
        ])
        _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["hair_mid"], [
            (cx - 4, cy - 3),
            (cx - 8, cy),
            (cx - 9, cy + 5),
            (cx - 8, cy + 12),
            (cx - 3, cy + 15 + int(sway1 * 0.5)),
            (cx + 2, cy + 12),
            (cx + 7, cy + 8),
            (cx + 6, cy),
            (cx + 4, cy - 5),
            (cx, cy - 6),
        ])
        # Highlight strands
        for i, (x_off, y_start, length) in enumerate([
            (-8, -2, 20), (-4, -4, 22), (2, -4, 20), (6, -2, 18),
        ]):
            for dy in range(length):
                if dy % 4 == 0:
                    hx = cx + x_off + int(math.sin(phase * 0.3 + i + dy * 0.2) * 0.5)
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_xaerissa.PALETTE["hair_light"],
                                     (hx, hy, 1, 1))
                elif dy % 7 == 0:
                    hx = cx + x_off
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_xaerissa.PALETTE["hair_shine"],
                                     (hx, hy, 1, 1))
        # Bangs falling over forehead
        for i in range(4):
            bx = cx - 3 + i * 2
            by_top = cy - 8
            by_bot = cy - 4 + (i % 2)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["hair_darkest"],
                             (bx, by_top), (bx, by_bot), 1)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["hair_dark"],
                             (bx + 1, by_top), (bx + 1, by_bot - 1), 1)
    def _draw_crown_horns(surface, cx, cy, facing, phase):
        """Red crown with spider-like horns (like Elise's headpiece)."""
        # Central taller horn + 2 side horns curving outward
        for i, (x_off, height, angle_off) in enumerate([
            (-5, 6, 0.4),    # left curve outward
            (-2, 8, 0.15),   # left tall
            (0, 9, 0),       # center tallest
            (2, 8, -0.15),   # right tall
            (5, 6, -0.4),    # right curve outward
        ]):
            sway = math.sin(phase * 0.4 + i * 0.3) * 0.5
            base_x = cx + x_off
            base_y = cy
            tip_x = cx + x_off + int(math.sin(angle_off) * height) + int(sway)
            tip_y = cy - height
            # Shadow
            _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x - 1, base_y + 1),
                (base_x + 2, base_y + 1),
            ])
            # Dark chitin
            _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["chitin_darkest"], [
                (tip_x, tip_y),
                (base_x - 1, base_y),
                (base_x + 1, base_y),
            ])
            # Red crimson layer
            _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_darkest"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_dark"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x + 1, base_y),
            ])
            _NS_xaerissa._poly(surface, _NS_xaerissa.PALETTE["crimson_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2 + 1), int((tip_y + base_y) / 2)),
                (base_x + 1, base_y),
            ])
            # Bright tip
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_shine"],
                             (tip_x, tip_y, 1, 1))
        # Central gem in crown (dark red)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                         (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                         (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                         (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_shine"],
                         (cx, cy, 1, 1))
    def _draw_glowing_red_eyes(surface, cx, cy, facing, phase, action):
        """Bright red glowing eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.5 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 2 + (1 if facing == 1 else -1)
            ey = cy
            # Deep socket
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Red glow halo
            for radius in range(5, 0, -1):
                alpha = _NS_xaerissa._alpha(120 * (5 - radius) / 5 * pulse * intensity)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["eye_mid"], alpha),
                                       (ex, ey), radius)
            # Eye core (bright red)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["white"],
                             (ex + 1, ey, 1, 1))
        # Dark eyeshadow makeup (accent)
        pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                         (cx - 3, cy - 2), (cx + 3, cy - 2), 1)
    def _draw_dark_lips(surface, cx, cy, facing, phase, action, attack_progress):
        """Dark red seductive lips."""
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 2)
        if mouth_open > 0:
            # Slightly parted (biting/casting)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                             (cx - 2, cy, 4, int(mouth_open) + 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                             (cx - 2, cy, 4, int(mouth_open)))
            # Small fang tips visible
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_light"],
                             (cx - 1, cy + int(mouth_open) - 1, 1, 1))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["skin_light"],
                             (cx + 1, cy + int(mouth_open) - 1, 1, 1))
        # Lips
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                         (cx - 2, cy - 1, 4, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"],
                         (cx - 1, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                         (cx, cy - 1, 1, 1))
    # ============================================================
    # RANGED ATTACK - VENOM PROJECTILE
    # ============================================================
    def _draw_venom_projectile(surface, boss, x, y, progress):
        """Magenta venom projectile from hand."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_xaerissa._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 4
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Venom trail
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_xaerissa._alpha(240 - i * 24)
            size = max(1, 8 - i)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_darkest"], alpha),
                                   (px, py), size)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                   (px, py), max(1, size - 3))
            # Sparks
            if i < 5:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_xaerissa.PALETTE["venom_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright head
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_darkest"],
                               (bx, by), 8)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_dark"],
                               (bx, by), 6)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_mid"],
                               (bx, by), 4)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_light"],
                               (bx, by), 3)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_hot"],
                               (bx, by), 2)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_shine"],
                               (bx, by), 1)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["white"], (bx, by, 1, 1))
        for r in range(12, 3, -2):
            alpha = _NS_xaerissa._alpha(80 * (12 - r) / 12)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                   (bx, by), r)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 22)
            alpha = _NS_xaerissa._alpha(240 * (1 - st))
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                   (tx, ty), max(1, radius - 5), 2)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                   (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["venom_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # VENOM MIST (ambient)
    # ============================================================
    def _draw_venom_mist(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 55), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_xaerissa._alpha((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xaerissa.PALETTE["mist_dark"], alpha),
                    (80 - radius * 2, 27 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_xaerissa._alpha((24 - radius) * 3.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xaerissa.PALETTE["mist_mid"], alpha),
                    (80 - radius, 27 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 12))
        # Rising venom bubbles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_xaerissa._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                   (sx, sy), 3)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xaerissa.PALETTE["venom_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Red sparks (blood-like)
        for i in range(6):
            spark_t = (phase * 0.7 + i * 0.15) % 1.0
            sx = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(spark_t * 24)
            alpha = _NS_xaerissa._alpha(220 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["crimson_mid"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["crimson_hot"], alpha),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_xaerissa._alpha(160 - i * 22)
                if alpha <= 0:
                    continue
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (10, 3, 8, 170), (10, 10, 130, 12))
        pygame.draw.ellipse(shadow, (35, 10, 25, 110), (18, 12, 114, 8))
        surface.blit(shadow, (x - 75, y - 15 + hover_offset))
    def _draw_crimson_aura(surface, x, y, phase):
        """Crimson-purple aura around spider queen."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_xaerissa._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_xaerissa._aacircle(aura,
                                       (*_NS_xaerissa.PALETTE["crimson_darkest"], alpha),
                                       (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_xaerissa._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_xaerissa._aacircle(aura,
                                       (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                       (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_xaerissa._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xaerissa._aacircle(aura,
                                       (*_NS_xaerissa.PALETTE["crimson_dark"], alpha),
                                       (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Small spider silhouettes crawling around (webby particles)
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_hot"], (sx, sy, 1, 1))
    def _draw_web_backdrop(surface, x, y, phase):
        """Subtle web pattern in the background."""
        # Small web strands crisscrossing (very subtle)
        web_surf = pygame.Surface((280, 200), pygame.SRCALPHA)
        cx_local, cy_local = 140, 100
        # Radial web lines
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.05
            end_x = cx_local + int(math.cos(angle) * 130)
            end_y = cy_local + int(math.sin(angle) * 90)
            pygame.draw.line(web_surf,
                             (*_NS_xaerissa.PALETTE["web_dark"], 40),
                             (cx_local, cy_local), (end_x, end_y), 1)
        # Concentric web rings
        for r in (40, 70, 100):
            pygame.draw.ellipse(web_surf,
                                (*_NS_xaerissa.PALETTE["web_dark"], 40),
                                (cx_local - r, cy_local - r // 2,
                                 r * 2, r), 1)
        surface.blit(web_surf, (x - 140, y - 100))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Crimson rune ring on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xaerissa.PALETTE["crimson_darkest"], 210),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_xaerissa.PALETTE["crimson_dark"], 230),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_xaerissa.PALETTE["venom_dark"], 200),
                            (25, 22, 120, 18), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_xaerissa.PALETTE["crimson_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_xaerissa.PALETTE["crimson_shine"],
                                 _NS_xaerissa._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: NEUROTOXIN BITE (enhanced venom projectile)
    # ============================================================
    def _draw_neurotoxin_foreground(surface, boss, x, y, timer, phase):
        """Enhanced neurotoxin bite - venom projectile."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xaerissa._target_position(boss, x, y)
        if progress < 0.25:
            # Charge venom in hand (spider fang icon glow)
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 4
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_xaerissa._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_darkest"], alpha),
                                       (hand_x, hand_y), r)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_dark"],
                                   (hand_x, hand_y), cr - 1)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_mid"],
                                   (hand_x, hand_y), max(1, cr - 3))
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_light"],
                                   (hand_x, hand_y), max(1, cr - 4))
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_shine"],
                                   (hand_x, hand_y), max(1, cr - 6))
            # Spider fang shape gathering (2 fangs)
            fang_len = int(6 * t)
            for side in (-1, 1):
                fang_x = hand_x + side * 2
                fang_tip_y = hand_y + fang_len
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["chitin_darkest"],
                                 (fang_x, hand_y - 2),
                                 (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                 (fang_x, hand_y - 2),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["venom_hot"],
                                 (fang_x, fang_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_xaerissa.PALETTE["venom_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
        else:
            # Projectile flies
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 26
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Extra bright venom trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xaerissa._alpha(250 - i * 20)
                size = max(1, 9 - i)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_darkest"], alpha),
                                       (px, py), size)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                       (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_xaerissa.PALETTE["venom_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Huge bright venom head
            for r in range(15, 3, -2):
                alpha = _NS_xaerissa._alpha(100 * (15 - r) / 15)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                       (bx, by), r)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_darkest"],
                                   (bx, by), 10)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_dark"],
                                   (bx, by), 8)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_mid"],
                                   (bx, by), 5)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_light"],
                                   (bx, by), 3)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["venom_shine"],
                                   (bx, by), 1)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["white"], (bx, by, 1, 1))
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 25)
                alpha = _NS_xaerissa._alpha(240 * (1 - st))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_darkest"], alpha),
                                       (tx, ty), radius + 4, 3)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 2)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                       (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_xaerissa.PALETTE["venom_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_xaerissa.PALETTE["venom_shine"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W: VOLATILE SPIDERLING (summon spider)
    # ============================================================
    def _draw_spiderling_ground(surface, boss, x, y, timer, phase):
        """Circle on ground where spiderling spawns."""
        # Spawns beside boss
        facing = boss.direction
        sp_x = x + facing * 40
        sp_y = y + 20
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(28 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_xaerissa.PALETTE["venom_darkest"], 200),
                                (sp_x - r, sp_y - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_xaerissa.PALETTE["venom_dark"], 180),
                                (sp_x - r + 3, sp_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_xaerissa.PALETTE["crimson_dark"], 150),
                                (sp_x - r + 8, sp_y - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_spiderling_foreground(surface, boss, x, y, timer, phase):
        """Spawn spiderling that moves toward target."""
        facing = boss.direction
        tx, ty = _NS_xaerissa._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Spawn position
        spawn_x = x + facing * 40
        spawn_y = y + 20
        if progress < 0.25:
            # Rising from ground with magic
            t = progress / 0.25
            _NS_xaerissa._draw_spiderling(surface, spawn_x,
                                          spawn_y - int(t * 10), phase, t, facing)
        elif progress < 0.75:
            # Moving toward target
            t = (progress - 0.25) / 0.5
            cur_x = int(spawn_x + (tx - spawn_x) * t)
            cur_y = int(spawn_y - 10 + (ty - (spawn_y - 10)) * t)
            _NS_xaerissa._draw_spiderling(surface, cur_x, cur_y, phase, 1.0, facing)
        else:
            # EXPLODE at target
            t = (progress - 0.75) / 0.25
            explode_r = int(15 + t * 30)
            alpha = _NS_xaerissa._alpha(240 * (1 - t))
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_darkest"], alpha),
                                   (tx, ty), explode_r + 3, 3)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_dark"], alpha),
                                   (tx, ty), explode_r, 3)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_mid"], alpha),
                                   (tx, ty), max(1, explode_r - 5), 2)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["venom_light"], alpha),
                                   (tx, ty), max(1, explode_r - 12), 1)
            # Explosion sparks
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * explode_r)
                ey = ty + int(math.sin(angle_s) * explode_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["venom_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["crimson_hot"], alpha),
                                 (ex, ey, 1, 1))
    def _draw_spiderling(surface, sx, sy, phase, form_progress, facing):
        """Small spider with 8 legs."""
        alpha_base = int(255 * min(1.0, form_progress * 1.5))
        # Body (round abdomen)
        body_r = 4
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["shadow_deep"], alpha_base),
                               (sx + 1, sy + 1), body_r + 1)
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["chitin_darkest"], alpha_base),
                               (sx, sy), body_r)
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["chitin_dark"], alpha_base),
                               (sx, sy), body_r - 1)
        # Red highlight on top
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["crimson_dark"], alpha_base),
                               (sx, sy - 1), 2)
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["crimson_mid"], alpha_base),
                               (sx, sy - 1), 1)
        pygame.draw.rect(surface,
                         (*_NS_xaerissa.PALETTE["crimson_hot"], alpha_base),
                         (sx, sy - 1, 1, 1))
        # Small head in front
        head_x = sx + facing * 3
        head_y = sy
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["chitin_darkest"], alpha_base),
                               (head_x, head_y), 2)
        _NS_xaerissa._aacircle(surface,
                               (*_NS_xaerissa.PALETTE["chitin_dark"], alpha_base),
                               (head_x, head_y), 1)
        # 8 legs (4 pairs) - animated wave
        for side in (-1, 1):
            for leg_i, (angle_deg, length) in enumerate([
                (60, 5), (25, 6), (-15, 6), (-50, 5),
            ]):
                wave = math.sin(phase * 4 + leg_i * 0.5 + side * 0.3) * 1
                angle = math.radians(angle_deg + wave * 5)
                end_x = sx + int(math.cos(angle) * length) * side
                end_y = sy - int(math.sin(angle) * length)
                pygame.draw.line(surface,
                                 (*_NS_xaerissa.PALETTE["chitin_darkest"], alpha_base),
                                 (sx, sy), (end_x, end_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_xaerissa.PALETTE["crimson_dark"], alpha_base),
                                 (sx, sy - 1), (end_x, end_y - 1), 1)
                pygame.draw.rect(surface,
                                 (*_NS_xaerissa.PALETTE["crimson_hot"], alpha_base),
                                 (end_x, end_y, 1, 1))
        # Small red glowing eyes
        pygame.draw.rect(surface,
                         (*_NS_xaerissa.PALETTE["eye_light"], alpha_base),
                         (head_x, head_y, 1, 1))
        pygame.draw.rect(surface,
                         (*_NS_xaerissa.PALETTE["white"], alpha_base),
                         (head_x, head_y, 1, 1))
        # Glow around spider (venom aura)
        if form_progress < 0.6:
            glow_alpha = _NS_xaerissa._alpha(150 * (1 - form_progress / 0.6))
            for r in range(10, 3, -2):
                a = _NS_xaerissa._alpha(glow_alpha * (10 - r) / 10)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["venom_hot"], a),
                                       (sx, sy), r)
    # ============================================================
    # SKILL E: COCOON (web trap projectile)
    # ============================================================
    def _draw_cocoon_foreground(surface, boss, x, y, timer, phase):
        """Web projectile that stuns target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xaerissa._target_position(boss, x, y)
        if progress < 0.25:
            # Charge web in hand
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 4
            # White web ball
            for r in range(int(6 * t), 0, -1):
                alpha = _NS_xaerissa._alpha(200 * (6 * t - r) / max(1, 6 * t))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["web_dark"], alpha),
                                       (hand_x, hand_y), r)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["web_mid"],
                                   (hand_x, hand_y), max(1, int(4 * t)))
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["web_light"],
                                   (hand_x, hand_y), max(1, int(2 * t)))
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["white"],
                             (hand_x, hand_y, 1, 1))
        elif progress < 0.6:
            # Web flying to target
            t = (progress - 0.25) / 0.35
            start_x = x + facing * 24
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Web ball with trail
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xaerissa._alpha(200 - i * 30)
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["web_dark"], alpha),
                                       (px, py), max(1, 5 - i))
                _NS_xaerissa._aacircle(surface,
                                       (*_NS_xaerissa.PALETTE["web_mid"], alpha),
                                       (px, py), max(1, 3 - i))
            # Web strands trailing (thin lines back to boss)
            for i in range(3):
                strand_offset = math.sin(phase * 3 + i) * 3
                pygame.draw.line(surface,
                                 (*_NS_xaerissa.PALETTE["web_dark"], 180),
                                 (start_x, start_y + int(strand_offset)),
                                 (bx, by), 1)
                pygame.draw.line(surface,
                                 (*_NS_xaerissa.PALETTE["web_mid"], 200),
                                 (start_x, start_y + int(strand_offset)),
                                 (bx, by), 1)
            # Main ball
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["web_dark"],
                                   (bx, by), 5)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["web_mid"],
                                   (bx, by), 4)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["web_light"],
                                   (bx, by), 2)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["white"], (bx, by, 1, 1))
        else:
            # COCOON at target (wrapped in web)
            t = (progress - 0.6) / 0.4
            # Cocoon body (vertical oval)
            cocoon_r = int(10 + t * 3)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["shadow_deep"],
                                   (tx, ty), cocoon_r + 2)
            # Draw as oval
            pygame.draw.ellipse(surface, _NS_xaerissa.PALETTE["web_dark"],
                                (tx - cocoon_r + 1, ty - cocoon_r * 1.5,
                                 cocoon_r * 2 - 2, cocoon_r * 3))
            pygame.draw.ellipse(surface, _NS_xaerissa.PALETTE["web_mid"],
                                (tx - cocoon_r + 2, ty - cocoon_r * 1.5 + 1,
                                 cocoon_r * 2 - 4, cocoon_r * 3 - 2))
            pygame.draw.ellipse(surface, _NS_xaerissa.PALETTE["web_light"],
                                (tx - cocoon_r + 3, ty - cocoon_r * 1.5 + 2,
                                 cocoon_r * 2 - 6, cocoon_r * 3 - 4))
            # Web wrapping lines (horizontal bands)
            for band_y_off in (-8, -4, 0, 4, 8):
                band_alpha = _NS_xaerissa._alpha(200)
                pygame.draw.line(surface,
                                 (*_NS_xaerissa.PALETTE["web_dark"], band_alpha),
                                 (tx - cocoon_r + 2, ty + band_y_off),
                                 (tx + cocoon_r - 2, ty + band_y_off), 1)
                pygame.draw.line(surface,
                                 (*_NS_xaerissa.PALETTE["white"], band_alpha),
                                 (tx - cocoon_r + 2, ty + band_y_off - 1),
                                 (tx + cocoon_r - 2, ty + band_y_off - 1), 1)
            # Web strand still connecting to boss
            if t < 0.7:
                start_x = x + facing * 24
                start_y = y - 4
                for strand_i in range(2):
                    strand_offset = math.sin(phase * 3 + strand_i) * 2
                    pygame.draw.line(surface,
                                     (*_NS_xaerissa.PALETTE["web_dark"], 150),
                                     (start_x, start_y + int(strand_offset)),
                                     (tx, ty), 1)
    # ============================================================
    # SKILL R: ARACHNOID FORM (transformation aura)
    # ============================================================
    def _draw_arachnoid_ground(surface, boss, x, y, timer, phase):
        """Web pattern on ground during transformation."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2))
        if r > 3:
            # Web-like ring
            pygame.draw.ellipse(surface,
                                (*_NS_xaerissa.PALETTE["crimson_darkest"], 230),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                                (*_NS_xaerissa.PALETTE["crimson_dark"], 210),
                                (x - r + 4, y + 40 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_xaerissa.PALETTE["venom_dark"], 220),
                                (x - r + 10, y + 40 - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 2)
            # Radial web lines from center
            for i in range(12):
                angle = phase * 0.3 + i * math.pi / 6
                x1 = x + int(math.cos(angle) * r)
                y1 = y + 40 + int(math.sin(angle) * r * 0.4)
                x2 = x + int(math.cos(angle) * 10)
                y2 = y + 40 + int(math.sin(angle) * 4)
                pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_arachnoid_aura(surface, boss, x, y, timer, phase):
        """Bright crimson aura + spider silhouettes around boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Body aura
        aura_r = 50 + int(math.sin(phase * 3) * 5)
        aura_surf = pygame.Surface((aura_r * 2 + 20, aura_r * 2 + 20), pygame.SRCALPHA)
        center = (aura_r + 10, aura_r + 10)
        for r in range(aura_r, 3, -3):
            alpha = _NS_xaerissa._alpha(120 * (aura_r - r) / aura_r)
            _NS_xaerissa._aacircle(aura_surf,
                                   (*_NS_xaerissa.PALETTE["crimson_dark"], alpha),
                                   center, r)
        surface.blit(aura_surf, (x - aura_r - 10, y - aura_r - 10 - 5))
        # Spider silhouettes orbiting
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            sx = x + int(math.cos(angle) * (aura_r + 5))
            sy = y + int(math.sin(angle) * (aura_r + 5)) - 5
            # Small spider body
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                                   (sx, sy), 3)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                   (sx, sy), 2)
            _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                                   (sx, sy), 1)
            # 4 tiny legs
            for leg_side in (-1, 1):
                for leg_i in range(2):
                    leg_angle = leg_side * (0.5 + leg_i * 0.5)
                    lex = sx + int(math.cos(angle + leg_angle) * 5)
                    ley = sy + int(math.sin(angle + leg_angle) * 5)
                    pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                                     (sx, sy), (lex, ley), 1)
        # Central bright spider emblem above boss
        sym_x = x
        sym_y = y - 45
        sym_pulse = math.sin(phase * 3) * 0.3 + 0.7
        # 8-point spider legs
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.3
            outer_r = 12
            outer_x = sym_x + int(math.cos(angle) * outer_r)
            outer_y = sym_y + int(math.sin(angle) * outer_r)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_darkest"],
                             (sym_x, sym_y), (outer_x, outer_y), 3)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_dark"],
                             (sym_x, sym_y), (outer_x, outer_y), 2)
            pygame.draw.line(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                             (sym_x, sym_y), (outer_x, outer_y), 1)
            pygame.draw.rect(surface, _NS_xaerissa.PALETTE["crimson_shine"],
                             (outer_x, outer_y, 1, 1))
        # Center spider body
        for r in range(6, 0, -1):
            alpha = _NS_xaerissa._alpha(220 * (6 - r) / 6 * sym_pulse)
            _NS_xaerissa._aacircle(surface,
                                   (*_NS_xaerissa.PALETTE["crimson_mid"], alpha),
                                   (sym_x, sym_y), r)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_hot"],
                               (sym_x, sym_y), 3)
        _NS_xaerissa._aacircle(surface, _NS_xaerissa.PALETTE["crimson_shine"],
                               (sym_x, sym_y), 2)
        pygame.draw.rect(surface, _NS_xaerissa.PALETTE["white"], (sym_x, sym_y, 1, 1))



# ====================================================================
# NYXHARR (SHADOW OF WAR) - TRUE BOSS
# ====================================================================

class _NS_nyxharr:
    """Namespace nyxharr - Shadow of War true boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark armor (deep black-teal)
        "armor_darkest": (5, 10, 12),
        "armor_dark": (15, 25, 30),
        "armor_mid": (35, 55, 65),
        "armor_light": (70, 100, 115),
        "armor_edge": (120, 155, 170),
        "armor_shine": (180, 215, 225),
        # Spirit cyan/teal (signature — Hecarim aura)
        "spirit_darkest": (2, 20, 25),
        "spirit_dark": (10, 65, 80),
        "spirit_mid": (30, 155, 180),
        "spirit_light": (90, 225, 245),
        "spirit_hot": (170, 250, 255),
        "spirit_shine": (230, 255, 255),
        # Ghost horse body (translucent teal-dark)
        "ghost_darkest": (5, 15, 20),
        "ghost_dark": (15, 45, 55),
        "ghost_mid": (35, 100, 120),
        "ghost_light": (80, 170, 190),
        "ghost_shine": (150, 230, 240),
        # Metal (weapon shaft, ornaments)
        "metal_darkest": (8, 8, 12),
        "metal_dark": (25, 25, 32),
        "metal_mid": (55, 60, 70),
        "metal_light": (110, 118, 130),
        "metal_shine": (190, 200, 210),
        # Blade (spirit-infused metal — dark base + cyan glow)
        "blade_dark": (12, 22, 28),
        "blade_mid": (40, 70, 85),
        "blade_light": (120, 175, 195),
        "blade_shine": (220, 245, 250),
        # Fire mane (spirit fire — cyan flame)
        "flame_dark": (10, 60, 80),
        "flame_mid": (40, 170, 200),
        "flame_light": (120, 235, 250),
        "flame_hot": (200, 255, 255),
        # Blood red eye (deep sockets in helm, glowing cyan)
        "eye_socket": (2, 5, 8),
        "eye_dark": (10, 60, 75),
        "eye_mid": (60, 200, 225),
        "eye_hot": (180, 255, 255),
        # Dark purple accent (nether corruption)
        "nether_dark": (20, 10, 40),
        "nether_mid": (60, 30, 100),
        "nether_light": (130, 80, 190),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxharr._clamp(color)
        if _NS_nyxharr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxharr._clamp(color)
        if _NS_nyxharr.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxharr._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyxharr(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxharr._detect_moving(boss)
        _NS_nyxharr._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nxh_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (BIG for TRUE BOSS)
        _NS_nyxharr._draw_shadow_aura(surface, x, y, pulse)
        _NS_nyxharr._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_nyxharr._draw_dread_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxharr._draw_charge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxharr._draw_onslaught_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_nyxharr._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxharr._draw_walk(surface, boss, x, y)
        else:
            _NS_nyxharr._draw_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_nyxharr._draw_rampage(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxharr._draw_dread_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxharr._draw_charge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxharr._draw_onslaught_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nxh_previous_timer", 0))
        active = bool(getattr(boss, "_nxh_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nxh_attack_active = True
            boss._nxh_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nxh_attack_frame = int(getattr(boss, "_nxh_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nxh_attack_active = False
            boss._nxh_attack_frame = 0
            active = False
        boss._nxh_previous_timer = timer
        boss._nxh_attack_progress = (
            min(1.0, getattr(boss, "_nxh_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nxh_last_x"):
            boss._nxh_last_x = boss.x
            boss._nxh_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nxh_last_x)
        dy = abs(boss.y - boss._nxh_last_y)
        boss._nxh_last_x = boss.x
        boss._nxh_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_nyxharr._draw_shadow(surface, x, y + 55)
        _NS_nyxharr._draw_ghost_trail(surface, x, y + 40, boss.pulse,
                                       boss.direction, intense=False)
        _NS_nyxharr._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Floating gallop — smooth bob + spectral trail
        phase = boss.pulse * 2.0
        float_bob = int(math.sin(phase * 1.1) * 5)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_nyxharr._draw_shadow(surface, x + sway, y + 55, faded=True)
        _NS_nyxharr._draw_ghost_trail(surface, x + sway, y + 40, phase,
                                       boss.direction, intense=True)
        _NS_nyxharr._draw_body(surface, x + sway, y + float_bob - 3,
                                boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_nxh_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # SWING glaive: rear-back → forward strike → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 5)
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            lunge = int((-5 + t * 20)) * boss.direction
            lift = int(5 - t * 7)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(15 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_nyxharr._draw_shadow(surface, x + lunge, y + 55)
        _NS_nyxharr._draw_ghost_trail(surface, x + lunge, y + 40, boss.pulse,
                                       boss.direction, intense=True)
        _NS_nyxharr._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_nyxharr._draw_swing_trail(surface, boss, x + lunge, y - lift,
                                       progress)
    # ============================================================
    # BODY (Centaur-like: horse body + armored rider torso)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered: tail/mane behind → horse body → rider torso → arms → head → glaive."""
        # Spectral tail (behind)
        _NS_nyxharr._draw_ghost_tail(surface, cx, cy, facing, phase)
        # Horse body (bottom half — spectral)
        _NS_nyxharr._draw_horse_body(surface, cx, cy + 8, facing, phase, action)
        # Rider torso (armored, upper half)
        _NS_nyxharr._draw_rider_torso(surface, cx, cy - 12, facing, phase,
                                       action, attack_progress)
        # Shoulder pauldrons
        _NS_nyxharr._draw_pauldrons(surface, cx, cy - 12, facing, phase)
        # Flame mane (above shoulders / helmet)
        _NS_nyxharr._draw_flame_mane(surface, cx, cy - 20, facing, phase)
        # Helm (head)
        _NS_nyxharr._draw_helm(surface, cx + facing * 1, cy - 22, facing,
                                phase, action, attack_progress)
        # Rear arm (holds glaive shaft near end)
        _NS_nyxharr._draw_rear_arm(surface, cx, cy - 12, facing, phase, action,
                                    attack_progress)
        # Front arm + GLAIVE (main weapon)
        _NS_nyxharr._draw_glaive_arm(surface, cx, cy - 12, facing, phase,
                                      action, attack_progress)
    def _draw_ghost_tail(surface, cx, cy, facing, phase):
        """Long spectral tail behind horse body."""
        back = -facing
        base_x = cx + back * 18
        base_y = cy + 10
        # Wispy tail flowing back
        segments = 8
        for seg_i in range(segments):
            t = seg_i / segments
            wave = math.sin(phase * 1.5 + t * math.pi) * (3 + t * 4)
            wx = base_x + back * int(6 + t * 20)
            wy = base_y + int(wave)
            alpha = _NS_nyxharr._alpha(220 * (1 - t * 0.6))
            size = max(2, 7 - seg_i)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["flame_dark"], alpha),
                                   (wx, wy), size + 1)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["flame_mid"], alpha),
                                   (wx, wy), size)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["flame_light"], alpha),
                                   (wx, wy), max(1, size - 2))
            if seg_i < 4:
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["flame_hot"], alpha),
                                 (wx, wy, 1, 1))
    def _draw_horse_body(surface, cx, cy, facing, phase, action):
        """Spectral horse body — 4 legs floating, muscular chest, hindquarters."""
        breath = math.sin(phase * 0.7) * 1
        gallop = math.sin(phase * 2) * 2 if action == "walk" else 0
        # Main horse body shape (elongated horizontal)
        body = [
            (cx - 20, cy - 2),
            (cx - 22, cy - 8),
            (cx - 18, cy - 12),
            (cx - 8, cy - 14),
            (cx + 4, cy - 14),
            (cx + 14, cy - 12),
            (cx + 20, cy - 8),
            (cx + 22, cy - 3),
            (cx + 20, cy + 4),
            (cx + 12, cy + 10),
            (cx + 2, cy + 12),
            (cx - 8, cy + 12),
            (cx - 16, cy + 10),
            (cx - 22, cy + 4),
        ]
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in body])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["ghost_darkest"], body)
        # Body shading (upper darker layer)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["ghost_dark"], [
            (cx - 20, cy - 4), (cx - 18, cy - 11),
            (cx - 8, cy - 13), (cx + 4, cy - 13),
            (cx + 14, cy - 11), (cx + 20, cy - 7),
            (cx + 20, cy + 3),
            (cx + 10, cy + 6), (cx - 16, cy + 6),
            (cx - 20, cy + 3),
        ])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["ghost_mid"], [
            (cx - 16, cy - 6), (cx - 12, cy - 10),
            (cx, cy - 12), (cx + 10, cy - 10),
            (cx + 15, cy - 6),
            (cx + 14, cy - 2), (cx - 12, cy - 2),
        ])
        # Highlight along top of back
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["ghost_light"], [
            (cx - 6, cy - 11),
            (cx + 2, cy - 12),
            (cx + 8, cy - 10),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ])
        # Belly darker underside
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["ghost_darkest"], [
            (cx - 14, cy + 8), (cx + 12, cy + 8),
            (cx + 10, cy + 12), (cx - 12, cy + 12),
        ])
        # Spectral wisps rising from body (ghostly aura)
        for i in range(6):
            wisp_t = (phase * 0.6 + i * 0.15) % 1.0
            wx = cx - 16 + i * 6 + int(math.sin(phase + i) * 3)
            wy = cy - 12 - int(wisp_t * 8)
            alpha = _NS_nyxharr._alpha(160 * (1 - wisp_t))
            if alpha > 0:
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["flame_mid"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["flame_hot"], alpha),
                                 (wx, wy, 1, 1))
        # LEGS (4 legs — front pair + rear pair, spectral)
        # Front legs
        for side_i, x_off in enumerate((-14, -10)):
            leg_phase = phase * 2 + side_i * math.pi
            lift = math.sin(leg_phase) * 3 if action == "walk" else 0
            _NS_nyxharr._draw_horse_leg(surface, cx + x_off, cy + 8, phase,
                                         int(lift), True)
        # Rear legs
        for side_i, x_off in enumerate((10, 16)):
            leg_phase = phase * 2 + side_i * math.pi + math.pi / 2
            lift = math.sin(leg_phase) * 3 if action == "walk" else 0
            _NS_nyxharr._draw_horse_leg(surface, cx + x_off, cy + 8, phase,
                                         int(lift), False)
        # Chest muscular armor plate
        chest_pts = [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 6, cy),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
            (cx - 6, cy),
        ]
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_dark"], chest_pts)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_mid"], [
            (cx - 3, cy - 3), (cx + 3, cy - 3),
            (cx + 5, cy), (cx + 3, cy + 3),
            (cx - 3, cy + 3), (cx - 5, cy),
        ])
        # Central glow rune on chest
        chest_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            a = _NS_nyxharr._alpha(180 * (4 - r) / 4 * chest_pulse)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_mid"], a),
                                   (cx, cy), r)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                               (cx, cy), 2)
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_shine"],
                         (cx, cy, 1, 1))
    def _draw_horse_leg(surface, hx, hy, phase, lift, front):
        """Spectral horse leg (translucent, wispy at bottom)."""
        knee_y = hy + 8 - lift
        hoof_y = knee_y + 10 - lift // 2
        # Upper leg
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                             (hx + 1, hy + 1), (hx + 1, knee_y + 1), 5)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["ghost_darkest"],
                             (hx, hy), (hx, knee_y), 4)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["ghost_dark"],
                             (hx, hy), (hx, knee_y), 3)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["ghost_mid"],
                             (hx - 1, hy), (hx - 1, knee_y), 1)
        # Lower leg (fetlock)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["ghost_darkest"],
                             (hx, knee_y), (hx, hoof_y), 3)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["ghost_dark"],
                             (hx, knee_y), (hx, hoof_y), 2)
        # Hoof (with flame)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["metal_darkest"],
                               (hx, hoof_y), 3)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["metal_dark"],
                               (hx, hoof_y), 2)
        # Flame under hoof
        pulse = math.sin(phase * 3 + hx * 0.1) * 0.3 + 0.7
        for r in range(4, 0, -1):
            a = _NS_nyxharr._alpha(160 * (4 - r) / 4 * pulse)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["flame_mid"], a),
                                   (hx, hoof_y + 2), r)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["flame_hot"],
                               (hx, hoof_y + 2), 1)
    def _draw_rider_torso(surface, cx, cy, facing, phase, action, attack_progress):
        """Armored rider torso (upper half of centaur)."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape (armored)
        torso = [
            (cx - 8, cy - 6),
            (cx + 8, cy - 6),
            (cx + 10, cy),
            (cx + 9, cy + 6),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 9, cy + 6),
            (cx - 10, cy),
        ]
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in torso])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_darkest"], torso)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_dark"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 9, cy), (cx + 8, cy + 5),
            (cx + 5, cy + 10), (cx - 5, cy + 10),
            (cx - 8, cy + 5), (cx - 9, cy),
        ])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_mid"], [
            (cx - 5, cy - 3), (cx + 5, cy - 3),
            (cx + 7, cy), (cx + 6, cy + 4),
            (cx + 3, cy + 8), (cx - 3, cy + 8),
            (cx - 6, cy + 4), (cx - 7, cy),
        ])
        # Highlight
        for side in (-1, 1):
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_light"], [
                (cx + side * 2, cy - 2),
                (cx + side * 4, cy - 1),
                (cx + side * 4, cy + 1),
                (cx + side * 2, cy),
            ])
        # Chest armor central glow (spirit runes)
        rune_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Big central rune
        for r in range(5, 0, -1):
            a = _NS_nyxharr._alpha(200 * (5 - r) / 5 * rune_pulse)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_mid"], a),
                                   (cx, cy + 2), r)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                               (cx, cy + 2), 2)
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_shine"],
                         (cx, cy + 2, 1, 1))
        # Armor plate lines (vertical ribs)
        for x_off in (-3, 3):
            pygame.draw.line(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                             (cx + x_off, cy - 4),
                             (cx + x_off, cy + 8), 1)
            pygame.draw.line(surface, _NS_nyxharr.PALETTE["armor_edge"],
                             (cx + x_off + 1, cy - 4),
                             (cx + x_off + 1, cy + 8), 1)
        # Small side runes
        for side in (-1, 1):
            rune_x = cx + side * 6
            rune_y = cy + 5
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_dark"],
                             (rune_x - 1, rune_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                             (rune_x, rune_y, 1, 1))
    def _draw_pauldrons(surface, cx, cy, facing, phase):
        """Heavy spiked shoulder armor."""
        for side in (-1, 1):
            px = cx + side * 8
            py = cy - 4
            # Pauldron base
            paul_pts = [
                (px - 4, py),
                (px + 4, py),
                (px + 5, py + 4),
                (px + 3, py + 6),
                (px - 3, py + 6),
                (px - 5, py + 4),
            ]
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in paul_pts])
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                              paul_pts)
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_dark"], [
                (px - 3, py + 1), (px + 3, py + 1),
                (px + 4, py + 3), (px + 2, py + 5),
                (px - 2, py + 5), (px - 4, py + 3),
            ])
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_mid"], [
                (px - 2, py + 2), (px + 2, py + 2),
                (px + 3, py + 3), (px - 3, py + 3),
            ])
            # Highlight
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["armor_edge"],
                             (px - 1, py + 2, 2, 1))
            # SPIKES on pauldron (2 curved spikes going up-back)
            for spike_i, spike_off_x in enumerate((-2, 2)):
                spike_base_x = px + spike_off_x
                spike_base_y = py + 1
                spike_tip_x = spike_base_x - facing * 2
                spike_tip_y = spike_base_y - 6 - spike_i
                _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"], [
                    (spike_tip_x + 1, spike_tip_y + 1),
                    (spike_base_x - 1, spike_base_y + 1),
                    (spike_base_x + 2, spike_base_y + 1),
                ])
                _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_darkest"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x - 1, spike_base_y),
                    (spike_base_x + 2, spike_base_y),
                ])
                _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_mid"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x, spike_base_y),
                    (spike_base_x + 1, spike_base_y),
                ])
                pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                                 (spike_tip_x, spike_tip_y, 1, 1))
    def _draw_flame_mane(surface, cx, cy, facing, phase):
        """Cyan flame mane rising from shoulders/back of helm."""
        flame_wave = math.sin(phase * 2) * 2
        # Multiple flame tongues
        for i, (base_off_x, base_off_y, tip_off_x, tip_off_y, size) in enumerate([
            (-6, 4, -8, -8, 4),
            (-3, 3, -5, -12, 5),
            (0, 2, 0, -14, 6),
            (3, 3, 5, -12, 5),
            (6, 4, 8, -8, 4),
        ]):
            wave_off = math.sin(phase * 2 + i * 0.5) * 2
            tip_x = cx + tip_off_x + int(wave_off)
            tip_y = cy + tip_off_y
            base_x = cx + base_off_x
            base_y = cy + base_off_y
            # Flame shape
            flame_pts = [
                (base_x - size, base_y),
                (base_x - size // 2, base_y - size),
                (tip_x - 1, tip_y + 2),
                (tip_x, tip_y),
                (tip_x + 1, tip_y + 2),
                (base_x + size // 2, base_y - size),
                (base_x + size, base_y),
            ]
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["flame_dark"],
                              flame_pts)
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["flame_mid"], [
                (base_x - size + 1, base_y),
                (tip_x - 1, tip_y + 3),
                (tip_x, tip_y + 1),
                (tip_x + 1, tip_y + 3),
                (base_x + size - 1, base_y),
            ])
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["flame_light"], [
                (base_x - size // 2, base_y - 1),
                (tip_x, tip_y + 2),
                (base_x + size // 2, base_y - 1),
            ])
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["flame_hot"],
                             (tip_x, tip_y, 1, 1))
        # Rising ember particles
        for i in range(8):
            ember_t = (phase * 1.2 + i * 0.15) % 1.0
            ex = cx - 8 + i * 2 + int(math.sin(phase * 2 + i) * 2)
            ey = cy - int(ember_t * 20)
            alpha = _NS_nyxharr._alpha(230 * (1 - ember_t))
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["flame_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["flame_hot"], alpha),
                                 (ex, ey, 1, 1))
    def _draw_helm(surface, cx, cy, facing, phase, action, attack_progress):
        """Dark spiky helm with glowing cyan eyes (no visible face)."""
        # Helm shape (tall, pointed)
        helm = [
            (cx - 5, cy + 2),
            (cx - 6, cy - 2),
            (cx - 5, cy - 6),
            (cx - 3, cy - 9),
            (cx, cy - 10),
            (cx + 3, cy - 9),
            (cx + 5, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 2),
            (cx + 4, cy + 5),
            (cx - 4, cy + 5),
        ]
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in helm])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_darkest"], helm)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_dark"], [
            (cx - 4, cy + 2), (cx - 5, cy - 1),
            (cx - 4, cy - 5), (cx - 2, cy - 8),
            (cx, cy - 9), (cx + 2, cy - 8),
            (cx + 4, cy - 5), (cx + 5, cy - 1),
            (cx + 4, cy + 2), (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_mid"], [
            (cx - 3, cy - 3), (cx - 3, cy - 5),
            (cx, cy - 7), (cx + 3, cy - 5),
            (cx + 3, cy - 3), (cx + 2, cy - 1),
            (cx - 2, cy - 1),
        ])
        # Side highlight
        pygame.draw.line(surface, _NS_nyxharr.PALETTE["armor_edge"],
                         (cx + facing * 3, cy - 6),
                         (cx + facing * 4, cy - 3), 1)
        # HORNS/SPIKES on top of helm (2 curving back)
        for i, (base_off_x, tip_off_x, tip_off_y) in enumerate([
            (-2, -6, -8),
            (2, 6, -8),
        ]):
            wave = math.sin(phase * 0.5 + i) * 1
            base_x = cx + base_off_x
            base_y = cy - 9
            tip_x = cx + tip_off_x
            tip_y = cy + tip_off_y + int(wave)
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x - 1, base_y + 1),
                (base_x + 2, base_y + 1),
            ])
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_darkest"], [
                (tip_x, tip_y),
                (base_x - 1, base_y),
                (base_x + 2, base_y),
            ])
            _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_dark"], [
                (tip_x, tip_y),
                (base_x, base_y),
                (base_x + 1, base_y),
            ])
            # Cyan tip
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                             (tip_x, tip_y, 1, 1))
        # CENTER TOP CROWN SPIKE (tallest)
        crown_wave = math.sin(phase * 0.6) * 1
        crown_tip_y = cy - 14 + int(crown_wave)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_darkest"], [
            (cx, crown_tip_y),
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
        ])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["armor_dark"], [
            (cx, crown_tip_y),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
        ])
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (cx, crown_tip_y, 1, 1))
        # DARK VOID INSIDE HELM (face area — no face, just void + glowing eyes)
        void_pts = [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 3, cy + 1),
            (cx - 3, cy + 1),
        ]
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"], void_pts)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["eye_socket"], [
            (cx - 2, cy - 2), (cx + 2, cy - 2),
            (cx + 2, cy), (cx - 2, cy),
        ])
        # GLOWING CYAN EYES (menyala terang)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Big glow halo
        for r in range(6, 0, -1):
            a = _NS_nyxharr._alpha(120 * (6 - r) / 6 * eye_pulse)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_mid"], a),
                                   (cx, cy - 1), r)
        # Eye slits
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["eye_dark"],
                         (cx - 2, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["eye_dark"],
                         (cx + 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["eye_mid"],
                         (cx - 2, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["eye_mid"],
                         (cx + 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["eye_hot"],
                         (cx - 2, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["eye_hot"],
                         (cx + 1, cy - 1, 1, 1))
        # Jaw guard (bottom of helm — small teeth/plate)
        for tooth_x in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["armor_edge"],
                             (cx + tooth_x, cy + 3, 1, 2))
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                             (cx + tooth_x, cy + 4, 1, 1))
    def _draw_rear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm (offhand) — supports weapon or rests."""
        back = -facing
        shoulder = (cx + back * 6, cy - 4)
        swing = math.sin(phase * 0.8) * 2 if action != "attack" else 0
        elbow = (shoulder[0] + back * 3, shoulder[1] + 5 + int(swing))
        hand = (elbow[0] + back * 2, elbow[1] + 5)
        # Upper arm (armored)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                             shoulder, elbow, 4)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_dark"],
                             shoulder, elbow, 3)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 1)
        # Forearm
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                             elbow, hand, 3)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_dark"],
                             elbow, hand, 2)
        # Gauntlet (spiked)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                               hand, 3)
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["armor_dark"],
                               hand, 2)
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (hand[0], hand[1], 1, 1))
    def _draw_glaive_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding massive glaive."""
        shoulder = (cx + facing * 6, cy - 4)
        # Arm angle based on action
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up — raise glaive high behind
                t = attack_progress / 0.35
                elbow_off_x = facing * (2 - int(t * 4))
                elbow_off_y = -2 - int(t * 6)
            elif attack_progress < 0.55:
                # Strike — swing forward
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = int((facing * -2) + (facing * 12) * t)
                elbow_off_y = int(-8 + t * 10)
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = int(facing * 10 * (1 - t) + facing * 4 * t)
                elbow_off_y = int(2 - t * 4)
        else:
            # Idle — glaive resting slightly forward
            sway = math.sin(phase * 0.7) * 1
            elbow_off_x = facing * 4
            elbow_off_y = -2 + int(sway)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (elbow[0] + facing * 6, elbow[1] + 2)
        # Upper arm
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                             shoulder, elbow, 5)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_dark"],
                             shoulder, elbow, 4)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Forearm
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                             elbow, hand, 4)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["armor_dark"],
                             elbow, hand, 3)
        # Gauntlet (grip)
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                         (hand[0] - 3, hand[1] - 2, 6, 5))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["armor_dark"],
                         (hand[0] - 3, hand[1] - 2, 6, 4))
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (hand[0], hand[1], 1, 1))
        # GLAIVE (massive)
        _NS_nyxharr._draw_glaive(surface, hand[0], hand[1], facing, phase,
                                  action, attack_progress)
    def _draw_glaive(surface, hx, hy, facing, phase, action, attack_progress):
        """Massive spirit glaive — long shaft + curved crescent blade."""
        # Glaive angle
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up: glaive raised high behind
                angle = -math.pi * 0.85 - (attack_progress / 0.35) * 0.2
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.2
                angle = -math.pi * 1.05 + t * math.pi * 1.3
            else:
                t = (attack_progress - 0.55) / 0.45
                angle = math.pi * 0.25 - t * math.pi * 0.5
        else:
            # Idle — glaive angled forward-down
            angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.05
        # Shaft length
        shaft_len = 34
        # Rear end (butt of shaft)
        butt_x = hx - int(math.cos(angle) * 8) * facing
        butt_y = hy - int(math.sin(angle) * 8)
        # Blade end
        blade_end_x = hx + int(math.cos(angle) * shaft_len) * facing
        blade_end_y = hy + int(math.sin(angle) * shaft_len)
        # Shaft (dark metal)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                             (butt_x + 1, butt_y + 1),
                             (blade_end_x + 1, blade_end_y + 1), 5)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["metal_darkest"],
                             (butt_x, butt_y), (blade_end_x, blade_end_y), 4)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["metal_dark"],
                             (butt_x, butt_y), (blade_end_x, blade_end_y), 3)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["metal_mid"],
                             (butt_x, butt_y), (blade_end_x, blade_end_y), 1)
        # Wrap details along shaft (ridges)
        for wrap_t in (0.25, 0.5, 0.75):
            wx = int(butt_x + (blade_end_x - butt_x) * wrap_t)
            wy = int(butt_y + (blade_end_y - butt_y) * wrap_t)
            _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["armor_darkest"],
                                   (wx, wy), 2)
            _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["armor_mid"],
                                   (wx, wy), 1)
        # BUTT SPIKE at rear end
        butt_tip_x = butt_x - int(math.cos(angle) * 5) * facing
        butt_tip_y = butt_y - int(math.sin(angle) * 5)
        perp_ang = angle + math.pi / 2
        pa_x = butt_x + int(math.cos(perp_ang) * 2) * facing
        pa_y = butt_y + int(math.sin(perp_ang) * 2)
        pb_x = butt_x - int(math.cos(perp_ang) * 2) * facing
        pb_y = butt_y - int(math.sin(perp_ang) * 2)
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["metal_darkest"],
                          [(butt_tip_x, butt_tip_y), (pa_x, pa_y), (pb_x, pb_y)])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["metal_dark"], [
            (butt_tip_x, butt_tip_y),
            (int((pa_x + butt_x) / 2), int((pa_y + butt_y) / 2)),
            (int((pb_x + butt_x) / 2), int((pb_y + butt_y) / 2)),
        ])
        # ============ BLADE (curved crescent) ============
        # Perpendicular to shaft direction
        perp_x = -math.sin(angle) * facing
        perp_y = math.cos(angle)
        along_x = math.cos(angle) * facing
        along_y = math.sin(angle)
        # Blade attachment point
        att_x = blade_end_x
        att_y = blade_end_y
        # Crescent blade: main curve
        # Tip (outer far)
        tip_x = int(att_x + along_x * 10 + perp_x * 14)
        tip_y = int(att_y + along_y * 10 + perp_y * 14)
        # Back curve
        back_x = int(att_x + along_x * 4 + perp_x * 6)
        back_y = int(att_y + along_y * 4 + perp_y * 6)
        # Inner back edge
        inner_back_x = int(att_x + perp_x * 3)
        inner_back_y = int(att_y + perp_y * 3)
        # Middle inner curve
        inner_mid_x = int(att_x + along_x * 5 + perp_x * 8)
        inner_mid_y = int(att_y + along_y * 5 + perp_y * 8)
        # Second spike (small on inner)
        inner_spike_x = int(att_x - along_x * 2 + perp_x * 5)
        inner_spike_y = int(att_y - along_y * 2 + perp_y * 5)
        # Blade shape (crescent)
        blade_pts = [
            (att_x, att_y),
            (back_x, back_y),
            (tip_x, tip_y),
            (inner_mid_x, inner_mid_y),
            (inner_back_x, inner_back_y),
        ]
        # Shadow
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in blade_pts])
        # Blade dark base
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["blade_dark"], blade_pts)
        # Blade mid
        bcx = sum(p[0] for p in blade_pts) / len(blade_pts)
        bcy = sum(p[1] for p in blade_pts) / len(blade_pts)
        mid_pts = [(int(p[0] * 0.75 + bcx * 0.25),
                    int(p[1] * 0.75 + bcy * 0.25)) for p in blade_pts]
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["blade_mid"], mid_pts)
        # Bright edge (outer curve) — cyan glow along edge
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["blade_light"],
                             (att_x, att_y), (back_x, back_y), 2)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["blade_light"],
                             (back_x, back_y), (tip_x, tip_y), 2)
        _NS_nyxharr._aaline(surface, _NS_nyxharr.PALETTE["spirit_light"],
                             (back_x, back_y), (tip_x, tip_y), 1)
        # Bright tip
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                               (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_shine"],
                         (tip_x, tip_y, 1, 1))
        # Inner spike on blade
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["blade_dark"], [
            (att_x, att_y),
            (inner_back_x, inner_back_y),
            (inner_spike_x, inner_spike_y),
        ])
        _NS_nyxharr._poly(surface, _NS_nyxharr.PALETTE["blade_light"], [
            (att_x, att_y),
            (int((inner_back_x + inner_spike_x) / 2),
             int((inner_back_y + inner_spike_y) / 2)),
            (inner_spike_x, inner_spike_y),
        ])
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (inner_spike_x, inner_spike_y, 1, 1))
        # Cyan glow around blade (aura)
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(8, 2, -2):
            a = _NS_nyxharr._alpha(100 * (8 - r) / 8 * glow_pulse)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_light"], a),
                                   (tip_x, tip_y), r)
        # Central rune on blade base
        _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                               (int(bcx), int(bcy)), 2)
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (int(bcx), int(bcy), 1, 1))
    # ============================================================
    # SWING TRAIL
    # ============================================================
    def _draw_swing_trail(surface, boss, x, y, progress):
        """Cyan arc swing trail during glaive strike."""
        if not (0.35 <= progress <= 0.7):
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.35
        arc_center = (x, y - 8)
        arc_r = 32
        num_segs = 14
        arc_start = -math.pi * 0.9
        arc_end = math.pi * 0.35
        max_seg = int(num_segs * min(1.0, t * 1.3))
        # Draw main arc trail
        for i in range(max_seg):
            seg_t = i / num_segs
            angle = arc_start + (arc_end - arc_start) * seg_t
            px = arc_center[0] + int(math.cos(angle) * arc_r) * facing
            py = arc_center[1] + int(math.sin(angle) * arc_r)
            fade = (max_seg - i) / max(1, max_seg)
            alpha = _NS_nyxharr._alpha(230 * fade)
            size = max(1, 5 - i // 3)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_darkest"], alpha),
                                   (px, py), size + 2)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                   (px, py), size + 1)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                   (px, py), size)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_light"], alpha),
                                   (px, py), max(1, size - 1))
            pygame.draw.rect(surface,
                             (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                             (px, py, 1, 1))
        # Impact burst near strike apex
        if 0.5 < progress < 0.65:
            imp_t = (progress - 0.5) / 0.15
            imp_x = x + facing * 30
            imp_y = y + 6
            imp_r = int(6 + imp_t * 16)
            alpha = _NS_nyxharr._alpha(240 * (1 - imp_t))
            for r in range(imp_r, 0, -2):
                a = _NS_nyxharr._alpha(alpha * r / imp_r)
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_mid"], a),
                                       (imp_x, imp_y), r, 2)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                                   (imp_x, imp_y), max(1, imp_r // 3))
            for i in range(10):
                angle = i * math.pi / 5
                ex = imp_x + int(math.cos(angle) * imp_r)
                ey = imp_y + int(math.sin(angle) * imp_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["spirit_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT / GROUND (BIG scale for TRUE BOSS)
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(15, 0, -1):
            alpha = int(max(0, (15 - radius) * 15) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius,
                                 140 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, int(170 * mult)),
                            (5, 8, 150, 16))
        pygame.draw.ellipse(shadow, (10, 40, 50, int(120 * mult)),
                            (12, 10, 136, 12))
        surface.blit(shadow, (x - 80, y - 16))
    def _draw_shadow_aura(surface, x, y, phase):
        """MASSIVE cyan-teal + purple aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        # Outer aura (very large)
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(115, 5, -6):
            alpha = _NS_nyxharr._alpha((115 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxharr._aacircle(aura,
                                       (*_NS_nyxharr.PALETTE["spirit_darkest"], alpha),
                                       (130, 110), radius)
        for radius in range(75, 5, -4):
            alpha = _NS_nyxharr._alpha((75 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nyxharr._aacircle(aura,
                                       (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                       (130, 110), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_nyxharr._alpha((45 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_nyxharr._aacircle(aura,
                                       (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                       (130, 110), radius)
        # Nether purple inner tint
        for radius in range(30, 5, -3):
            alpha = _NS_nyxharr._alpha((30 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_nyxharr._aacircle(aura,
                                       (*_NS_nyxharr.PALETTE["nether_mid"], alpha),
                                       (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Floating cyan+purple embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_nyxharr.PALETTE["spirit_mid"] if i % 3 != 0 \
                else _NS_nyxharr.PALETTE["nether_light"]
            hot_color = _NS_nyxharr.PALETTE["spirit_hot"] if i % 3 != 0 \
                else _NS_nyxharr.PALETTE["nether_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Big ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxharr.PALETTE["spirit_darkest"], 210),
                            (5, 22, 190, 30), 4)
        pygame.draw.ellipse(ring, (*_NS_nyxharr.PALETTE["spirit_dark"], 220),
                            (14, 24, 172, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxharr.PALETTE["spirit_mid"], 230),
                            (25, 26, 150, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxharr.PALETTE["nether_mid"], 180),
                            (42, 28, 116, 16), 1)
        # Runes
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 54)
            y1 = 34 + int(math.sin(angle) * 10)
            x2 = 100 + int(math.cos(angle) * 82)
            y2 = 34 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_nyxharr.PALETTE["spirit_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxharr.PALETTE["spirit_shine"],
                                       _NS_nyxharr._alpha(160 * pulse)),
                                (15, 14, 170, 44), 1)
        surface.blit(ring, (x - 100, y - 30))
    def _draw_ghost_trail(surface, cx, cy, phase, facing, intense=False):
        """Spectral trail behind ghost horse."""
        strength = 1.6 if intense else 1.0
        # Rising spirit wisps
        for i in range(10):
            t = (phase * 0.5 + i * 0.12) % 1.0
            wx = cx + int(math.sin(phase + i) * 12) - facing * i * 3
            wy = cy + int(t * 12) - int(math.sin(phase + i * 0.5) * 2)
            alpha = _NS_nyxharr._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_darkest"], alpha),
                                       (wx, wy), 4)
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                       (wx, wy), 3)
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                                 (wx, wy, 1, 1))
        # Extra flame trail behind (when moving/attacking)
        if intense:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxharr._alpha(180 - i * 25)
                if alpha <= 0:
                    continue
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["flame_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["flame_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["flame_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # SKILL: Q - RAMPAGE (multi-swing arc)
    # ============================================================
    def _draw_rampage(surface, boss, x, y, timer, phase):
        """3 slashing arcs in front (increasing damage)."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple arc slashes at different times
        for slash_i in range(3):
            slash_start = slash_i * 0.25
            slash_end = slash_start + 0.35
            if progress < slash_start or progress > slash_end:
                continue
            t = (progress - slash_start) / (slash_end - slash_start)
            arc_r = 40 + slash_i * 4
            arc_center = (x + facing * 8, y - 8)
            # Draw arc
            num_segs = 16
            arc_start_ang = -math.pi * 0.8
            arc_end_ang = math.pi * 0.35
            max_seg = int(num_segs * min(1.0, t * 1.4))
            for i in range(max_seg):
                seg_t = i / num_segs
                angle = arc_start_ang + (arc_end_ang - arc_start_ang) * seg_t
                px = arc_center[0] + int(math.cos(angle) * arc_r) * facing
                py = arc_center[1] + int(math.sin(angle) * arc_r)
                fade = (max_seg - i) / max(1, max_seg)
                alpha = _NS_nyxharr._alpha(240 * fade * (1 - t * 0.3))
                size = max(2, 6 - i // 3) + slash_i
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_darkest"], alpha),
                                       (px, py), size + 2)
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                       (px, py), size + 1)
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                       (px, py), size)
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["spirit_light"], alpha),
                                       (px, py), max(1, size - 2))
                if i % 2 == 0:
                    pygame.draw.rect(surface,
                                     (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                                     (px, py, 1, 1))
            # Sparks flying off arc tip
            if t > 0.6:
                for spark_i in range(6):
                    sp_angle = arc_end_ang - 0.2 + spark_i * 0.15
                    sp_r = arc_r + int((t - 0.6) * 20)
                    sx = arc_center[0] + int(math.cos(sp_angle) * sp_r) * facing
                    sy = arc_center[1] + int(math.sin(sp_angle) * sp_r)
                    sp_alpha = _NS_nyxharr._alpha(200 * (1 - (t - 0.6) / 0.4))
                    pygame.draw.rect(surface,
                                     (*_NS_nyxharr.PALETTE["spirit_hot"], sp_alpha),
                                     (sx, sy, 2, 2))
    # ============================================================
    # SKILL: W - SPIRIT OF DREAD (ghost horse projectile)
    # ============================================================
    def _draw_dread_ground(surface, boss, x, y, timer, phase):
        """Path ground effect."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ghost trail along path
        path_len = int(200 * min(1.0, progress * 2))
        for i in range(0, path_len, 8):
            px = x + facing * (30 + i)
            py = y + 45 + int(math.sin(phase + i * 0.1) * 2)
            alpha = _NS_nyxharr._alpha(180 * (1 - i / max(1, path_len)))
            if alpha > 0:
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                    (px - 6, py - 2, 12, 4))
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                                 (px, py, 1, 1))
    def _draw_dread_foreground(surface, boss, x, y, timer, phase):
        """Big spectral horse spirit charging forward."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxharr._target_position(boss, x, y)
        start_x = x + facing * 30
        start_y = y
        t = progress
        px = int(start_x + (tx - start_x) * t)
        py = int(start_y + (ty - start_y) * t)
        # Trail
        for tr in range(8):
            trail_t = max(0.0, t - tr * 0.05)
            trx = int(start_x + (tx - start_x) * trail_t)
            tr_y = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxharr._alpha(220 - tr * 25)
            size = max(2, 10 - tr)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                   (trx, tr_y), size + 2)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                   (trx, tr_y), size)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_light"], alpha),
                                   (trx, tr_y), max(1, size - 3))
        # SPIRIT HORSE SHAPE (silhouette)
        horse_scale = 1.0
        # Body (elongated)
        pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_dark"],
                            (px - int(18 * horse_scale),
                             py - int(6 * horse_scale),
                             int(36 * horse_scale),
                             int(12 * horse_scale)))
        pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                            (px - int(15 * horse_scale),
                             py - int(4 * horse_scale),
                             int(30 * horse_scale),
                             int(8 * horse_scale)))
        # Head (in front)
        head_x = px + facing * int(16 * horse_scale)
        head_y = py - int(4 * horse_scale)
        pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_dark"],
                            (head_x - 5, head_y - 3, 10, 8))
        pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                            (head_x - 4, head_y - 2, 8, 6))
        # Eyes
        pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (head_x + facing * 1, head_y, 2, 2))
        # Legs (streaks)
        for leg_x_off in (-10, -4, 4, 10):
            pygame.draw.line(surface, _NS_nyxharr.PALETTE["spirit_dark"],
                             (px + leg_x_off, py + 4),
                             (px + leg_x_off - facing * 2, py + 12), 3)
            pygame.draw.line(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                             (px + leg_x_off, py + 4),
                             (px + leg_x_off - facing * 2, py + 12), 2)
        # Flame mane on top
        for i in range(5):
            m_wave = math.sin(phase * 3 + i) * 2
            mx = px - 8 + i * 4
            my = py - 8 - i + int(m_wave)
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_light"],
                             (mx, my, 2, 4))
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                             (mx, my, 1, 1))
        # Tail flame
        pygame.draw.line(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                         (px - facing * 16, py),
                         (px - facing * 24, py - 4), 4)
        pygame.draw.line(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                         (px - facing * 16, py),
                         (px - facing * 24, py - 4), 2)
    # ============================================================
    # SKILL: E - DEVASTATING CHARGE (dash line)
    # ============================================================
    def _draw_charge_ground(surface, boss, x, y, timer, phase):
        """Charge path — long cyan streak on ground."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Path line from boss to charge end
        path_len = int(220 * min(1.0, progress * 2))
        for i in range(0, path_len, 4):
            px = x + facing * (25 + i)
            py = y + 45 + int(math.sin(phase * 2 + i * 0.2) * 2)
            fade = 1 - i / max(1, path_len)
            alpha = _NS_nyxharr._alpha(220 * fade)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxharr.PALETTE["spirit_darkest"], alpha),
                                (px - 5, py - 2, 10, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                (px - 4, py - 1, 8, 3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                (px - 3, py, 6, 2))
            if i % 8 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                                 (px, py, 2, 2))
    def _draw_charge_foreground(surface, boss, x, y, timer, phase):
        """Streaking motion blur/afterimages of the boss."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple afterimages trailing behind
        for i in range(4):
            offset = -(i + 1) * 18 * facing
            alpha = _NS_nyxharr._alpha(150 - i * 30)
            if alpha <= 0:
                continue
            # Simplified silhouette
            silh = pygame.Surface((60, 90), pygame.SRCALPHA)
            for r in range(15, 5, -3):
                a = _NS_nyxharr._alpha(alpha * (15 - r) / 15)
                _NS_nyxharr._aacircle(silh,
                                       (*_NS_nyxharr.PALETTE["spirit_mid"], a),
                                       (30, 45), r)
            surface.blit(silh, (x + offset - 30, y - 45))
        # Speed lines
        for i in range(10):
            line_y = y - 30 + i * 6
            line_alpha = _NS_nyxharr._alpha(180 - abs(5 - i) * 20)
            line_len = 30 + i * 3
            pygame.draw.line(surface,
                             (*_NS_nyxharr.PALETTE["spirit_light"], line_alpha),
                             (x - facing * 20, line_y),
                             (x - facing * (20 + line_len), line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_nyxharr.PALETTE["spirit_hot"], line_alpha),
                             (x - facing * 20, line_y),
                             (x - facing * (20 + line_len // 2), line_y), 1)
    # ============================================================
    # SKILL: R - ONSLAUGHT OF SHADOWS (multiple ghost horses)
    # ============================================================
    def _draw_onslaught_ground(surface, boss, x, y, timer, phase):
        """Massive ground effect with expanding rings."""
        tx, ty = _NS_nyxharr._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growing rings at target
        r = int(15 + progress * 60)
        alpha = _NS_nyxharr._alpha(220 * (1 - progress * 0.3))
        for ring_i in range(3):
            ring_r = r - ring_i * 8
            if ring_r <= 0:
                continue
            pygame.draw.ellipse(surface,
                                (*_NS_nyxharr.PALETTE["spirit_darkest"], alpha),
                                (tx - ring_r, ty - ring_r // 3,
                                 ring_r * 2, ring_r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                (tx - ring_r + 2, ty - ring_r // 3 + 1,
                                 ring_r * 2 - 4, ring_r * 2 // 3 - 2), 2)
        # Rotating rune circle
        for i in range(10):
            angle = phase * 1.5 + i * math.pi / 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                             (sx - 1, sy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_shine"],
                             (sx, sy, 1, 1))
    def _draw_onslaught_foreground(surface, boss, x, y, timer, phase):
        """Multiple ghost horses charging from boss to target in parallel lanes."""
        facing = boss.direction
        tx, ty = _NS_nyxharr._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Summoning — dark portal + gathering
            t = progress / 0.25
            portal_x = x + facing * 20
            portal_y = y - 4
            portal_r = int(6 + t * 20)
            # Portal ring
            for r in range(portal_r + 4, 0, -2):
                a = _NS_nyxharr._alpha(180 * (portal_r + 4 - r) / (portal_r + 4))
                _NS_nyxharr._aacircle(surface,
                                       (*_NS_nyxharr.PALETTE["nether_dark"], a),
                                       (portal_x, portal_y), r)
            _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["spirit_dark"],
                                   (portal_x, portal_y), max(1, portal_r - 4))
            _NS_nyxharr._aacircle(surface, _NS_nyxharr.PALETTE["shadow_deep"],
                                   (portal_x, portal_y), max(1, portal_r - 8))
            # Swirling wisps around portal
            for i in range(10):
                angle = phase * 3 + i * math.pi / 5
                wx = portal_x + int(math.cos(angle) * portal_r)
                wy = portal_y + int(math.sin(angle) * portal_r)
                pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                                 (wx, wy, 2, 2))
        elif progress < 0.85:
            # Charging horses
            t = (progress - 0.25) / 0.6
            start_x = x + facing * 20
            start_y = y
            # 4 ghost horses in staggered lanes
            for horse_i in range(4):
                horse_t = min(1.0, max(0.0, t * 1.3 - horse_i * 0.15))
                if horse_t <= 0:
                    continue
                lane_off = (horse_i - 1.5) * 14
                start_lane_y = start_y + int(lane_off)
                end_lane_y = ty + int(lane_off)
                hx = int(start_x + (tx - start_x) * horse_t)
                hy = int(start_lane_y + (end_lane_y - start_lane_y) * horse_t)
                # Trail
                for tr in range(6):
                    trail_t = max(0.0, horse_t - tr * 0.05)
                    trx = int(start_x + (tx - start_x) * trail_t)
                    try_ = int(start_lane_y + (end_lane_y - start_lane_y) * trail_t)
                    alpha = _NS_nyxharr._alpha(200 - tr * 30)
                    _NS_nyxharr._aacircle(surface,
                                           (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                           (trx, try_), max(2, 6 - tr))
                    _NS_nyxharr._aacircle(surface,
                                           (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                           (trx, try_), max(1, 4 - tr))
                # Simplified horse silhouette
                pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_dark"],
                                    (hx - 12, hy - 4, 24, 8))
                pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                                    (hx - 10, hy - 3, 20, 6))
                # Head
                pygame.draw.ellipse(surface, _NS_nyxharr.PALETTE["spirit_mid"],
                                    (hx + facing * 10 - 3, hy - 3, 6, 6))
                # Eyes
                pygame.draw.rect(surface, _NS_nyxharr.PALETTE["spirit_hot"],
                                 (hx + facing * 11, hy - 1, 1, 1))
                # Legs
                for leg_x_off in (-6, 0, 6):
                    pygame.draw.line(surface,
                                     _NS_nyxharr.PALETTE["spirit_mid"],
                                     (hx + leg_x_off, hy + 2),
                                     (hx + leg_x_off - facing, hy + 7), 2)
                # Mane
                for m_i in range(3):
                    mx = hx - 4 + m_i * 3
                    my = hy - 6 + int(math.sin(phase * 4 + m_i) * 1)
                    pygame.draw.rect(surface,
                                     _NS_nyxharr.PALETTE["spirit_hot"],
                                     (mx, my, 1, 3))
        else:
            # Aftermath — big impact + rising wisps at target
            t = (progress - 0.85) / 0.15
            imp_r = int(30 + t * 30)
            alpha = _NS_nyxharr._alpha(230 * (1 - t))
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_dark"], alpha),
                                   (tx, ty), imp_r, 3)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_mid"], alpha),
                                   (tx, ty), max(1, imp_r - 8), 2)
            _NS_nyxharr._aacircle(surface,
                                   (*_NS_nyxharr.PALETTE["spirit_hot"], alpha),
                                   (tx, ty), max(1, imp_r // 3))
            # Rising wisps at target
            for i in range(14):
                rise_t = (phase * 0.8 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 40)
                a = _NS_nyxharr._alpha(220 * (1 - rise_t))
                if a > 0:
                    _NS_nyxharr._aacircle(surface,
                                           (*_NS_nyxharr.PALETTE["spirit_dark"], a),
                                           (rx, ry), 3)
                    _NS_nyxharr._aacircle(surface,
                                           (*_NS_nyxharr.PALETTE["spirit_mid"], a),
                                           (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_nyxharr.PALETTE["spirit_hot"], a),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kaelvyrn(surface, boss, x, y):
    """Entry point kaelvyrn."""
    return _NS_kaelvyrn.draw_kaelvyrn(surface, boss, x, y)


def draw_thorvin(surface, boss, x, y):
    """Entry point thorvin."""
    return _NS_thorvin.draw_thorvin(surface, boss, x, y)


def draw_xaerissa(surface, boss, x, y):
    """Entry point xaerissa."""
    return _NS_xaerissa.draw_xaerissa(surface, boss, x, y)


def draw_nyxharr(surface, boss, x, y):
    """Entry point nyxharr."""
    return _NS_nyxharr.draw_nyxharr(surface, boss, x, y)
