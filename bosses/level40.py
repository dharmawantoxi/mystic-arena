"""
bosses/level40.py - Semua boss Level 40

Berisi:
  - urgharun    (mini boss - MELEE feral wrath, beast rage)
  - yhoranth    (mini boss - RANGED unforgiven wraith)
  - zulkhaven   (mini boss - MELEE devourer, blood feast)
  - thalryndel  (TRUE BOSS - RANGED tempest weaver, storm/lightning)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _urg_ (urgharun), _yho_ (yhoranth), _zul_ (zulkhaven),
    _thal_ (thalryndel) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# URGHARUN (FERAL WRATH) - Mini Boss
# ====================================================================

class _NS_urgharun:
    """Namespace urgharun - Feral Wrath boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Fur (dark grey/black)
        "fur_darkest": (8, 8, 12),
        "fur_dark": (25, 25, 32),
        "fur_mid": (55, 55, 65),
        "fur_light": (95, 95, 105),
        "fur_edge": (140, 140, 150),
        "fur_shine": (180, 180, 190),
        # Belly/inner fur (lighter grey with brown)
        "belly_dark": (40, 32, 28),
        "belly_mid": (80, 68, 60),
        "belly_light": (135, 120, 105),
        # Leather straps (brown)
        "leather_dark": (35, 20, 10),
        "leather_mid": (85, 55, 30),
        "leather_light": (140, 100, 60),
        "leather_shine": (195, 155, 100),
        # Metal buckles/spikes
        "metal_dark": (30, 25, 25),
        "metal_mid": (75, 70, 70),
        "metal_light": (150, 145, 145),
        "metal_shine": (220, 215, 215),
        # Fury red (mouth, eyes, claws, cracks)
        "fury_darkest": (35, 3, 3),
        "fury_dark": (130, 15, 15),
        "fury_mid": (230, 40, 40),
        "fury_light": (255, 110, 90),
        "fury_hot": (255, 180, 140),
        "fury_shine": (255, 230, 200),
        # Claws/fangs (dark bone with red tint)
        "claw_dark": (25, 15, 12),
        "claw_mid": (85, 55, 45),
        "claw_light": (180, 140, 120),
        "claw_shine": (240, 210, 190),
        # Eye (fierce red)
        "eye_socket": (3, 1, 1),
        "eye_dark": (90, 10, 10),
        "eye_mid": (220, 40, 30),
        "eye_light": (255, 120, 80),
        "eye_glow": (255, 220, 160),
        # Blood/rage ground
        "blood_dark": (50, 8, 8),
        "blood_mid": (120, 20, 15),
        "blood_light": (200, 45, 30),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 1),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_urgharun._clamp(color)
        if _NS_urgharun.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_urgharun._clamp(color)
        if _NS_urgharun.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_urgharun._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_urgharun(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_urgharun._update_urg_attack_anim(boss)
        attacking = bool(getattr(boss, "_urg_attack_active", False))
        moving = _NS_urgharun._detect_moving(boss)
        # ===== LAYER 1: BACKGROUND =====
        _NS_urgharun._draw_fury_aura(surface, x, y, pulse,
                                      enraged=(active_skill == "r"))
        _NS_urgharun._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # ===== LAYER 2: SKILL GROUND FX (behind body) =====
        if active_skill == "q":
            _NS_urgharun._draw_earthshock_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_urgharun._draw_enrage_ground(surface, boss, x, y, skill_timer, pulse)
        # ===== LAYER 3: BODY =====
        if attacking:
            _NS_urgharun._draw_urg_attack(surface, boss, x, y, active_skill)
        elif moving:
            _NS_urgharun._draw_urg_walk(surface, boss, x, y, active_skill)
        else:
            _NS_urgharun._draw_urg_idle(surface, boss, x, y, active_skill)
        # ===== LAYER 4: FOREGROUND FX =====
        # Basic attack (claw slash)
        if attacking and not active_skill:
            _NS_urgharun._draw_basic_attack_fx(surface, boss, x, y)
        # Skill foreground
        if active_skill == "q":
            _NS_urgharun._draw_earthshock_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_urgharun._draw_overpower_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_urgharun._draw_furyswipes_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_urgharun._draw_enrage_fx(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_urg_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_urg_previous_timer", timer))
        active = bool(getattr(boss, "_urg_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._urg_attack_active = True
            boss._urg_attack_frame = 0
            active = True
        if active:
            boss._urg_attack_frame = int(getattr(boss, "_urg_attack_frame", 0)) + 1
            attack_duration = 28
            if boss._urg_attack_frame >= attack_duration:
                boss._urg_attack_active = False
                boss._urg_attack_frame = 0
                active = False
        boss._urg_previous_timer = timer
        if active:
            attack_duration = 28
            boss._urg_attack_progress = min(1.0,
                boss._urg_attack_frame / attack_duration)
        else:
            boss._urg_attack_progress = 0.0
    def _detect_moving(boss):
        if not hasattr(boss, "_urg_last_x"):
            boss._urg_last_x = boss.x
            boss._urg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._urg_last_x)
        dy = abs(boss.y - boss._urg_last_y)
        boss._urg_last_x = boss.x
        boss._urg_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_urg_idle(surface, boss, x, y, active_skill):
        breath = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_urgharun._draw_shadow(surface, x, y + 52)
        _NS_urgharun._draw_urg_body(surface, x, y + breath, boss.direction,
                                     boss.pulse, "idle", active_skill=active_skill)
    def _draw_urg_walk(surface, boss, x, y, active_skill):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.2) * 3)
        _NS_urgharun._draw_shadow(surface, x, y + 52)
        _NS_urgharun._draw_urg_body(surface, x, y + bob, boss.direction,
                                     phase, "walk", active_skill=active_skill)
    def _draw_urg_attack(surface, boss, x, y, active_skill):
        """Claw swing attack animation."""
        progress = getattr(boss, "_urg_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        # Rear back → swing forward → recover
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 5) * facing
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-5 + t * 20)) * facing
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(15 * (1 - t)) * facing
            lift = int(-2 + t * 2)
        _NS_urgharun._draw_shadow(surface, x + lunge, y + 52)
        _NS_urgharun._draw_urg_body(surface, x + lunge, y - lift, facing,
                                     boss.pulse, "attack", progress,
                                     active_skill=active_skill)
    # ============================================================
    # BODY (Bear quadruped)
    # ============================================================
    def _draw_urg_body(surface, cx, cy, facing, phase, action,
                        attack_progress=0, active_skill=None):
        """Full bear body: legs, torso, arms, head."""
        enraged = (active_skill == "r")
        # Tail (small)
        _NS_urgharun._draw_bear_tail(surface, cx, cy + 6, facing, phase)
        # Rear legs (partially hidden behind body)
        _NS_urgharun._draw_bear_legs(surface, cx - facing * 10, cy + 12,
                                      facing, phase, action, is_rear=True)
        # Main torso
        _NS_urgharun._draw_bear_torso(surface, cx, cy, facing, phase, enraged)
        # Straps and armor over torso
        _NS_urgharun._draw_leather_straps(surface, cx, cy, facing, phase)
        # Front arms with BIG CLAWS
        arm_swing = 0
        if action == "attack":
            arm_swing = int(math.sin(attack_progress * math.pi) * 8)
        _NS_urgharun._draw_bear_arms(surface, cx, cy, facing, phase, arm_swing,
                                      action, attack_progress, enraged)
        # Head
        head_lunge = 0
        head_lift = 0
        if action == "attack":
            if attack_progress < 0.3:
                head_lunge = -int(attack_progress / 0.3 * 3) * facing
                head_lift = -int(attack_progress / 0.3 * 2)
            elif attack_progress < 0.6:
                t = (attack_progress - 0.3) / 0.3
                head_lunge = int((-3 + t * 12)) * facing
                head_lift = int(-2 + t * 4)
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(9 * (1 - t)) * facing
                head_lift = int(2 - t * 2)
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 9)
        elif enraged:
            mouth_open = 4 + math.sin(phase * 2) * 2
        _NS_urgharun._draw_bear_head(surface, cx + facing * 16 + head_lunge,
                                      cy - 12 + head_lift, facing, phase,
                                      mouth_open, action, enraged)
    def _draw_bear_tail(surface, cx, cy, facing, phase):
        """Short stubby tail."""
        back_dir = -facing
        tx = cx + back_dir * 15
        ty = cy + 4
        _NS_urgharun._aacircle(surface, _NS_urgharun.PALETTE["shadow_deep"],
                                (tx + 1, ty + 1), 4)
        _NS_urgharun._aacircle(surface, _NS_urgharun.PALETTE["fur_darkest"],
                                (tx, ty), 4)
        _NS_urgharun._aacircle(surface, _NS_urgharun.PALETTE["fur_dark"],
                                (tx, ty), 3)
        _NS_urgharun._aacircle(surface, _NS_urgharun.PALETTE["fur_mid"],
                                (tx - 1, ty - 1), 2)
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["fur_edge"],
                         (tx - 1, ty - 1, 1, 1))
    def _draw_bear_legs(surface, cx, cy, facing, phase, action, is_rear=True):
        """Rear legs thick and short."""
        step_offset = 0
        if action == "walk":
            step_phase = phase + (0 if is_rear else math.pi)
            step_offset = int(math.sin(step_phase) * 3)
        for leg_i, (side, offset_x) in enumerate([(-1, -3), (1, 3)]):
            leg_offset = step_offset if leg_i == 0 else -step_offset
            leg_top_x = cx + offset_x
            leg_top_y = cy - 4
            leg_bot_x = leg_top_x + leg_offset // 2
            leg_bot_y = cy + 8
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["shadow_deep"],
                                  (leg_top_x + 2, leg_top_y + 2),
                                  (leg_bot_x + 2, leg_bot_y + 2), 8)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_darkest"],
                                  (leg_top_x, leg_top_y),
                                  (leg_bot_x, leg_bot_y), 7)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_dark"],
                                  (leg_top_x, leg_top_y),
                                  (leg_bot_x, leg_bot_y), 5)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_mid"],
                                  (leg_top_x - 1, leg_top_y),
                                  (leg_bot_x - 1, leg_bot_y), 2)
            # Paw
            paw_x = leg_bot_x
            paw_y = leg_bot_y
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"], [
                (paw_x - 5, paw_y + 1),
                (paw_x + 6, paw_y + 1),
                (paw_x + 5, paw_y + 5),
                (paw_x - 5, paw_y + 5),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"], [
                (paw_x - 5, paw_y),
                (paw_x + 6, paw_y),
                (paw_x + 5, paw_y + 4),
                (paw_x - 5, paw_y + 4),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_dark"], [
                (paw_x - 4, paw_y + 1),
                (paw_x + 5, paw_y + 1),
                (paw_x + 4, paw_y + 3),
                (paw_x - 4, paw_y + 3),
            ])
            # Small rear claws
            for cx_off in (-3, 0, 3):
                claw_x = paw_x + cx_off + facing
                claw_y = paw_y + 3
                _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["claw_dark"], [
                    (claw_x, claw_y),
                    (claw_x + facing, claw_y + 3),
                    (claw_x + facing * 2, claw_y),
                ])
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["claw_light"],
                                 (claw_x + facing, claw_y + 2, 1, 1))
    def _draw_bear_torso(surface, cx, cy, facing, phase, enraged):
        """Main body - bulky bear torso."""
        body_shape = [
            (cx - 18, cy + 2),
            (cx - 20, cy - 4),
            (cx - 16, cy - 12),
            (cx - 8, cy - 15),
            (cx + 6, cy - 15),
            (cx + 16, cy - 12),
            (cx + 20, cy - 4),
            (cx + 22, cy + 2),
            (cx + 20, cy + 8),
            (cx + 14, cy + 13),
            (cx + 4, cy + 14),
            (cx - 6, cy + 14),
            (cx - 14, cy + 13),
            (cx - 20, cy + 8),
        ]
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in body_shape])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"], body_shape)
        # Upper fur
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_dark"], [
            (cx - 18, cy),
            (cx - 15, cy - 11),
            (cx - 6, cy - 14),
            (cx + 6, cy - 14),
            (cx + 15, cy - 11),
            (cx + 19, cy - 4),
            (cx + 20, cy),
            (cx + 15, cy + 3),
            (cx - 15, cy + 3),
            (cx - 18, cy),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_mid"], [
            (cx - 14, cy - 3),
            (cx - 12, cy - 10),
            (cx - 4, cy - 12),
            (cx + 6, cy - 12),
            (cx + 12, cy - 10),
            (cx + 15, cy - 3),
            (cx + 13, cy),
            (cx - 10, cy),
        ])
        # Highlight streaks (fur direction)
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_light"], [
            (cx - 6, cy - 8),
            (cx + 2, cy - 10),
            (cx + 8, cy - 6),
            (cx + 6, cy - 3),
            (cx - 4, cy - 3),
        ])
        # Fur texture (small dark tufts)
        for row in range(3):
            y_row = cy - 8 + row * 4
            for dx in (-12, -7, -2, 3, 8, 13):
                offset_x = (row % 2) * 2 - 1
                # Small vertical dark line for fur
                pygame.draw.line(surface, _NS_urgharun.PALETTE["fur_darkest"],
                                 (cx + dx + offset_x, y_row),
                                 (cx + dx + offset_x, y_row + 2), 1)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["fur_edge"],
                                 (cx + dx + offset_x, y_row, 1, 1))
        # Belly (lighter fur)
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["belly_dark"], [
            (cx - 12, cy + 3),
            (cx + 12, cy + 3),
            (cx + 16, cy + 6),
            (cx + 12, cy + 12),
            (cx + 4, cy + 14),
            (cx - 6, cy + 14),
            (cx - 12, cy + 12),
            (cx - 16, cy + 6),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["belly_mid"], [
            (cx - 10, cy + 5),
            (cx + 10, cy + 5),
            (cx + 13, cy + 7),
            (cx + 8, cy + 12),
            (cx - 4, cy + 13),
            (cx - 10, cy + 11),
            (cx - 13, cy + 7),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["belly_light"], [
            (cx - 6, cy + 7),
            (cx + 6, cy + 7),
            (cx + 9, cy + 9),
            (cx + 4, cy + 11),
            (cx - 4, cy + 11),
            (cx - 8, cy + 9),
        ])
        # Fury cracks (red glow through fur) - stronger if enraged
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = 240 if enraged else 200
        for crack in [
            [(cx - 12, cy - 3), (cx - 8, cy), (cx - 5, cy + 3)],
            [(cx + 8, cy - 5), (cx + 12, cy - 2), (cx + 14, cy + 2)],
            [(cx - 3, cy + 8), (cx + 2, cy + 10)],
            [(cx - 15, cy + 5), (cx - 10, cy + 8)],
        ]:
            for i in range(len(crack) - 1):
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_dark"],
                                  _NS_urgharun._alpha(crack_alpha * pulse)),
                                 crack[i], crack[i + 1], 1)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_mid"],
                                  _NS_urgharun._alpha(180 * pulse)),
                                 crack[i], crack[i + 1], 1)
                pygame.draw.rect(surface,
                                 (*_NS_urgharun.PALETTE["fury_hot"],
                                  _NS_urgharun._alpha(240 * pulse)),
                                 (crack[i][0], crack[i][1], 1, 1))
    def _draw_leather_straps(surface, cx, cy, facing, phase):
        """Leather straps and buckles across body."""
        # Diagonal strap across chest
        strap_pts = [
            (cx - 12, cy - 8),
            (cx + 14, cy + 4),
        ]
        pygame.draw.line(surface, _NS_urgharun.PALETTE["shadow_deep"],
                         (strap_pts[0][0] + 1, strap_pts[0][1] + 1),
                         (strap_pts[1][0] + 1, strap_pts[1][1] + 1), 3)
        pygame.draw.line(surface, _NS_urgharun.PALETTE["leather_dark"],
                         strap_pts[0], strap_pts[1], 3)
        pygame.draw.line(surface, _NS_urgharun.PALETTE["leather_mid"],
                         strap_pts[0], strap_pts[1], 2)
        pygame.draw.line(surface, _NS_urgharun.PALETTE["leather_light"],
                         (strap_pts[0][0], strap_pts[0][1] - 1),
                         (strap_pts[1][0], strap_pts[1][1] - 1), 1)
        # Metal buckle in middle
        buckle_x = (strap_pts[0][0] + strap_pts[1][0]) // 2
        buckle_y = (strap_pts[0][1] + strap_pts[1][1]) // 2
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_dark"],
                         (buckle_x - 2, buckle_y - 2, 5, 4))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_mid"],
                         (buckle_x - 1, buckle_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_light"],
                         (buckle_x, buckle_y - 1, 2, 1))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_shine"],
                         (buckle_x, buckle_y - 1, 1, 1))
        # Second strap (belt at waist)
        for i in range(-15, 16, 2):
            belt_x = cx + i
            belt_y = cy + 8
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["leather_dark"],
                             (belt_x, belt_y, 2, 2))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["leather_mid"],
                             (belt_x, belt_y, 1, 1))
        # Central buckle
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_dark"],
                         (cx - 2, cy + 7, 5, 4))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_mid"],
                         (cx - 1, cy + 8, 3, 2))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_shine"],
                         (cx, cy + 8, 1, 1))
        # Small spikes on straps
        for sx_off, sy_off in [(-10, -5), (-3, -1), (8, 2)]:
            spike_x = cx + sx_off
            spike_y = cy + sy_off
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_dark"],
                             (spike_x, spike_y - 1, 2, 3))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_light"],
                             (spike_x, spike_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_shine"],
                             (spike_x, spike_y - 1, 1, 1))
    def _draw_bear_arms(surface, cx, cy, facing, phase, swing, action,
                         attack_progress, enraged):
        """Two front arms with MASSIVE CLAWS."""
        for side, x_base in [(-1, -12), (1, 14)]:
            base_x = cx + x_base
            base_y = cy - 8
            if action == "attack":
                # Reach forward
                hand_x = base_x + facing * (10 + swing)
                hand_y = base_y + 12 - swing // 2
            else:
                # Idle: hands down/forward
                hand_x = base_x + facing * int(4 + math.sin(phase * 0.5 + side) * 1)
                hand_y = base_y + 18
            # Elbow bend
            mx = int((base_x + hand_x) / 2) + side * 2
            my = int((base_y + hand_y) / 2) + 2
            # Upper arm (thick with fur)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["shadow_deep"],
                                  (base_x + 2, base_y + 2), (mx + 2, my + 2), 8)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_darkest"],
                                  (base_x, base_y), (mx, my), 7)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_dark"],
                                  (base_x, base_y), (mx, my), 5)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_mid"],
                                  (base_x - 1, base_y), (mx - 1, my), 3)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_light"],
                                  (base_x - 2, base_y), (mx - 2, my), 1)
            # Forearm
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["shadow_deep"],
                                  (mx + 2, my + 2),
                                  (hand_x + 2, hand_y + 2), 7)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_darkest"],
                                  (mx, my), (hand_x, hand_y), 6)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_dark"],
                                  (mx, my), (hand_x, hand_y), 4)
            _NS_urgharun._aaline(surface, _NS_urgharun.PALETTE["fur_mid"],
                                  (mx - 1, my), (hand_x - 1, hand_y), 2)
            # Leather strap on forearm
            wrist_x = int((mx + hand_x) / 2)
            wrist_y = int((my + hand_y) / 2)
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["leather_dark"],
                             (wrist_x - 3, wrist_y - 1, 6, 3))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["leather_mid"],
                             (wrist_x - 3, wrist_y - 1, 6, 2))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["metal_shine"],
                             (wrist_x, wrist_y - 1, 1, 1))
            # PAW WITH BIG CLAWS
            _NS_urgharun._draw_claw_paw(surface, hand_x, hand_y, facing, phase,
                                         side, action, enraged)
    def _draw_claw_paw(surface, hx, hy, facing, phase, side, action, enraged):
        """Big paw with 4-5 massive claws."""
        # Paw base
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"], [
            (hx - 5, hy - 2),
            (hx + 6, hy - 2),
            (hx + 6, hy + 5),
            (hx - 5, hy + 5),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"], [
            (hx - 5, hy - 3),
            (hx + 6, hy - 3),
            (hx + 6, hy + 4),
            (hx - 5, hy + 4),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_dark"], [
            (hx - 4, hy - 2),
            (hx + 5, hy - 2),
            (hx + 5, hy + 3),
            (hx - 4, hy + 3),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_mid"], [
            (hx - 3, hy - 1),
            (hx + 4, hy - 1),
            (hx + 4, hy + 2),
            (hx - 3, hy + 2),
        ])
        # BIG CLAWS (5 claws forward)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, cx_off in enumerate((-4, -2, 0, 2, 4)):
            claw_size = 8 if i in (1, 2, 3) else 7  # middle claws longer
            claw_x = hx + cx_off + facing * 3
            claw_base_y = hy + 3
            claw_tip_x = claw_x + facing * claw_size
            claw_tip_y = claw_base_y - 1
            # Shadow
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"], [
                (claw_x + 1, claw_base_y - 1),
                (claw_x + 1, claw_base_y + 2),
                (claw_tip_x + 1, claw_tip_y + 1),
            ])
            # Claw shape (curved talon)
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["claw_dark"], [
                (claw_x, claw_base_y - 1),
                (claw_x, claw_base_y + 2),
                (claw_tip_x, claw_tip_y),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["claw_mid"], [
                (claw_x + facing, claw_base_y - 1),
                (claw_x + facing, claw_base_y + 1),
                (claw_tip_x - facing, claw_tip_y),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["claw_light"], [
                (claw_x + facing * 2, claw_base_y),
                (claw_x + facing * 2, claw_base_y + 1),
                (claw_tip_x - facing * 2, claw_tip_y),
            ])
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["claw_shine"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            # Fury glow on claw tip (stronger if attacking or enraged)
            glow_intensity = pulse
            if action == "attack" or enraged:
                glow_intensity = min(1.0, pulse + 0.4)
            for r in range(3, 0, -1):
                alpha = _NS_urgharun._alpha(200 * (3 - r) / 3 * glow_intensity)
                _NS_urgharun._aacircle(surface,
                                       (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                       (claw_tip_x, claw_tip_y), r)
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_hot"],
                             (claw_tip_x, claw_tip_y, 1, 1))
    def _draw_bear_head(surface, cx, cy, facing, phase, mouth_open, action,
                         enraged):
        """Bear head with mane and open mouth."""
        # Mane (behind head - shaggy fur)
        mane_pts = [
            (cx - 12, cy + 5),
            (cx - 14, cy + 1),
            (cx - 13, cy - 4),
            (cx - 10, cy - 9),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 10, cy - 9),
            (cx + 13, cy - 4),
            (cx + 14, cy + 1),
            (cx + 12, cy + 5),
        ]
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in mane_pts])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"], mane_pts)
        # Shaggy mane fur (jagged spikes around head)
        for angle_deg in range(-90, 91, 20):
            angle = math.radians(angle_deg)
            mane_r = 13 + int(math.sin(phase + angle_deg * 0.1) * 1)
            mx1 = cx + int(math.cos(angle) * mane_r)
            my1 = cy - int(math.sin(angle) * mane_r) - 3
            mx2 = cx + int(math.cos(angle) * (mane_r + 3))
            my2 = cy - int(math.sin(angle) * (mane_r + 3)) - 3
            pygame.draw.line(surface, _NS_urgharun.PALETTE["fur_darkest"],
                             (mx1, my1), (mx2, my2), 2)
            pygame.draw.line(surface, _NS_urgharun.PALETTE["fur_dark"],
                             (mx1, my1), (mx2, my2), 1)
        # Head shape (bear muzzle - shorter than dragon)
        head_shape = [
            (cx - 9 * facing, cy + 4),
            (cx - 10 * facing, cy - 2),
            (cx - 7 * facing, cy - 8),
            (cx - 2 * facing, cy - 10),
            (cx + 5 * facing, cy - 9),
            (cx + 11 * facing, cy - 6),
            (cx + 15 * facing, cy - 2),
            (cx + 17 * facing, cy + 2),
            (cx + 15 * facing, cy + 6),
            (cx + 8 * facing, cy + 8),
            (cx + 1 * facing, cy + 9),
            (cx - 6 * facing, cy + 8),
        ]
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in head_shape])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"],
                            head_shape)
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_dark"], [
            (cx - 9 * facing, cy + 3),
            (cx - 9 * facing, cy - 1),
            (cx - 5 * facing, cy - 7),
            (cx + 4 * facing, cy - 8),
            (cx + 10 * facing, cy - 5),
            (cx + 14 * facing, cy - 1),
            (cx + 15 * facing, cy + 1),
            (cx + 10 * facing, cy + 1),
            (cx + 3 * facing, cy),
            (cx - 5 * facing, cy + 1),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_mid"], [
            (cx - 6 * facing, cy - 1),
            (cx - 3 * facing, cy - 6),
            (cx + 4 * facing, cy - 7),
            (cx + 10 * facing, cy - 3),
            (cx + 12 * facing, cy),
            (cx + 3 * facing, cy - 1),
        ])
        # Highlight on brow
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_light"], [
            (cx - 2 * facing, cy - 4),
            (cx + 3 * facing, cy - 6),
            (cx + 7 * facing, cy - 4),
            (cx + 4 * facing, cy - 2),
        ])
        # Snout (lighter fur)
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["belly_dark"], [
            (cx + 8 * facing, cy - 1),
            (cx + 14 * facing, cy - 1),
            (cx + 16 * facing, cy + 2),
            (cx + 14 * facing, cy + 5),
            (cx + 8 * facing, cy + 5),
        ])
        _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["belly_mid"], [
            (cx + 9 * facing, cy),
            (cx + 13 * facing, cy),
            (cx + 15 * facing, cy + 2),
            (cx + 13 * facing, cy + 4),
            (cx + 9 * facing, cy + 4),
        ])
        # Nose (dark)
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["shadow_deep"],
                         (cx + 14 * facing, cy + 1, 3, 3))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["fur_darkest"],
                         (cx + 15 * facing, cy + 1, 2, 2))
        pygame.draw.rect(surface, _NS_urgharun.PALETTE["fur_edge"],
                         (cx + 15 * facing, cy + 1, 1, 1))
        # Small ears (top of head)
        for side in (-1, 1):
            ear_x = cx + side * 6
            ear_y = cy - 9
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"], [
                (ear_x, ear_y),
                (ear_x - 2 * side, ear_y - 4),
                (ear_x + 2 * side, ear_y - 2),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_dark"], [
                (ear_x, ear_y),
                (ear_x - 1 * side, ear_y - 3),
                (ear_x + 1 * side, ear_y - 2),
            ])
            # Inner ear (dark)
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_dark"],
                             (ear_x, ear_y - 2, 1, 1))
        # Fierce glowing eyes
        _NS_urgharun._draw_bear_eyes(surface, cx, cy - 3, facing, phase, enraged)
        # Mouth
        _NS_urgharun._draw_bear_mouth(surface, cx, cy, facing, phase, mouth_open,
                                       action)
    def _draw_bear_eyes(surface, cx, cy, facing, phase, enraged):
        """Two fierce red glowing eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        if enraged:
            pulse = min(1.0, pulse + 0.3)
        for eye_side, eye_off_x in [(-1, -3), (1, 3)]:
            ex = cx + int(eye_off_x * facing)
            ey = cy
            # Socket
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["shadow_deep"],
                             (ex - 2, ey - 1, 5, 3))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 4, 3))
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_urgharun._alpha(120 * (5 - r) / 5 * pulse)
                _NS_urgharun._aacircle(surface,
                                       (*_NS_urgharun.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            # Iris
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["eye_dark"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["eye_mid"],
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
    def _draw_bear_mouth(surface, cx, cy, facing, phase, mouth_open, action):
        """Bear mouth with fangs."""
        mouth_y = cy + 5
        mouth_x_start = cx + 5 * facing
        mouth_x_end = cx + 15 * facing
        if mouth_open > 0:
            # Open mouth
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end - 2, mouth_y + int(mouth_open)),
                (mouth_x_start + 2, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fury_darkest"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing * 2, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing * 2, mouth_y + int(mouth_open * 0.7) - 1),
            ])
            # Red rage glow inside mouth
            glow_cx = cx + 10 * facing
            glow_cy = mouth_y + int(mouth_open * 0.5)
            glow_r = int(3 + mouth_open * 0.3)
            for r in range(glow_r + 3, 0, -1):
                alpha = _NS_urgharun._alpha(180 * (glow_r + 3 - r) / (glow_r + 3))
                _NS_urgharun._aacircle(surface,
                                       (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                       (glow_cx, glow_cy), r)
            _NS_urgharun._aacircle(surface, _NS_urgharun.PALETTE["fury_mid"],
                                    (glow_cx, glow_cy), max(1, glow_r - 1))
            _NS_urgharun._aacircle(surface, _NS_urgharun.PALETTE["fury_light"],
                                    (glow_cx, glow_cy), max(1, glow_r - 3))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                             (glow_cx, glow_cy, 1, 1))
            # Upper fangs (big canines)
            for i, x_off in enumerate((6, 9, 12, 14)):
                fang_x = cx + int(x_off * facing)
                fang_size = 4 if i in (0, 3) else 3  # canines bigger
                fang_tip_y = mouth_y + int(mouth_open * 0.75) + fang_size
                pygame.draw.line(surface, _NS_urgharun.PALETTE["claw_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_urgharun.PALETTE["claw_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["claw_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Lower fangs
            for i, x_off in enumerate((7, 10, 13)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 4
                pygame.draw.line(surface, _NS_urgharun.PALETTE["claw_dark"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_urgharun.PALETTE["claw_light"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["claw_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Drool
            if mouth_open > 5:
                for x_off in (7, 12):
                    drip_x = cx + int(x_off * facing)
                    drip_y = mouth_y + int(mouth_open) + 2
                    pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_dark"],
                                     (drip_x, drip_y, 1, 2))
                    pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_light"],
                                     (drip_x, drip_y, 1, 1))
        else:
            # Closed mouth
            pygame.draw.line(surface, _NS_urgharun.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            for x_off in (7, 10, 13):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["claw_mid"],
                                 (fang_x, mouth_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["claw_light"],
                                 (fang_x, mouth_y + 2, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 2, 2, 180), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_fury_aura(surface, x, y, phase, enraged=False):
        """Red fury aura - stronger when enraged."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if enraged else 1.0
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_urgharun._alpha((90 - radius) * 1.2 * pulse * strength)
            if alpha > 0:
                _NS_urgharun._aacircle(aura,
                                       (*_NS_urgharun.PALETTE["fury_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_urgharun._alpha((50 - radius) * 1.4 * pulse * strength)
            if alpha > 0:
                _NS_urgharun._aacircle(aura,
                                       (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Rage embers floating
        num_embers = 16 if enraged else 12
        for i in range(num_embers):
            angle = phase * 0.3 + i * math.pi / (num_embers / 2)
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.4)
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_urgharun.PALETTE["fury_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_urgharun.PALETTE["fur_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_urgharun.PALETTE["fury_dark"], 220),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_urgharun.PALETTE["fury_mid"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_urgharun.PALETTE["fury_hot"],
                                        _NS_urgharun._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - Claw Slash (MELEE)
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic melee attack: 3 parallel claw slashes arc + impact at target."""
        progress = getattr(boss, "_urg_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y
        # Limit to melee range
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist > 80:
            tx = x + int(dx / dist * 60)
            ty = y + int(dy / dist * 60)
        # PHASE 1: Wind-up (0-30%)
        if progress < 0.3:
            t = progress / 0.3
            # Small red glow at claws building up
            for side_i, x_off in enumerate((-8, 12)):
                claw_x = x + x_off * facing
                claw_y = y + 8
                for r in range(int(3 + t * 3), 0, -1):
                    alpha = _NS_urgharun._alpha(150 * t * r / 5)
                    _NS_urgharun._aacircle(surface,
                                           (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                           (claw_x, claw_y), r)
        # PHASE 2: SLASH ARC (30-70%)
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            # Big slash arc in front
            slash_cx = x + facing * 25
            slash_cy = y - 2
            arc_radius = 32
            start_angle = math.radians(-70) if facing == 1 else math.radians(-110)
            end_angle = math.radians(70) if facing == 1 else math.radians(250)
            current_angle = start_angle + (end_angle - start_angle) * t
            # 5 parallel claw marks (matching 5 claws)
            for line_i, offset in enumerate((-12, -6, 0, 6, 12)):
                num_pts = 10
                prev_pt = None
                for step in range(num_pts + 1):
                    step_t = step / num_pts
                    a = start_angle + (current_angle - start_angle) * step_t
                    r = arc_radius + offset
                    px = slash_cx + int(math.cos(a) * r) * facing
                    py = slash_cy + int(math.sin(a) * r)
                    if prev_pt is not None:
                        alpha = _NS_urgharun._alpha(230 * step_t
                                                    * (1 - t * 0.3))
                        pygame.draw.line(surface,
                                         (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                         prev_pt, (px, py), 3)
                        pygame.draw.line(surface,
                                         (*_NS_urgharun.PALETTE["fury_mid"], alpha),
                                         prev_pt, (px, py), 2)
                        pygame.draw.line(surface,
                                         (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                         prev_pt, (px, py), 1)
                        pygame.draw.line(surface,
                                         (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                                         prev_pt, (px, py), 1)
                    prev_pt = (px, py)
                # Bright tip
                tip_a = current_angle
                tip_r = arc_radius + offset
                tip_x = slash_cx + int(math.cos(tip_a) * tip_r) * facing
                tip_y = slash_cy + int(math.sin(tip_a) * tip_r)
                for r in range(4, 0, -1):
                    alpha = _NS_urgharun._alpha(240 * (4 - r) / 4)
                    _NS_urgharun._aacircle(surface,
                                           (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                                           (tip_x, tip_y), r)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["white"],
                                 (tip_x, tip_y, 1, 1))
            # Blood sparks
            for i in range(8):
                spark_angle = start_angle + (current_angle - start_angle) \
                              * (0.3 + (i % 5) * 0.15)
                spark_r = arc_radius + math.sin(boss.pulse * 3 + i) * 8
                sx = slash_cx + int(math.cos(spark_angle) * spark_r) * facing
                sy = slash_cy + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_hot"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                                 (sx, sy, 1, 1))
        # PHASE 3: IMPACT (70-100%)
        else:
            t = (progress - 0.7) / 0.3
            impact_r = int(8 + t * 22)
            alpha = _NS_urgharun._alpha(240 * (1 - t))
            # Impact rings
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                   (tx, ty), impact_r + 2, 3)
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_mid"], alpha),
                                   (tx, ty), impact_r, 2)
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                   (tx, ty), max(1, impact_r - 5), 1)
            # Core
            core_r = max(1, int(6 * (1 - t)))
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                                   (tx, ty), core_r + 2)
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                                   (tx, ty), max(1, core_r))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["white"],
                             (tx, ty, 1, 1))
            # 5 claw scratch marks
            scratch_len = int(16 * (1 - t * 0.3))
            for i, y_off in enumerate((-12, -6, 0, 6, 12)):
                start_sx = tx - scratch_len // 2 * facing
                end_sx = tx + scratch_len // 2 * facing
                sy_pos = ty + y_off + int(math.sin(i) * 2)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_darkest"], alpha),
                                 (start_sx, sy_pos - 1),
                                 (end_sx, sy_pos - 1), 2)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                 (start_sx, sy_pos),
                                 (end_sx, sy_pos), 1)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                                 (start_sx + 2, sy_pos),
                                 (end_sx - 2, sy_pos), 1)
            # Radial burst particles
            for i in range(10):
                angle_p = i * math.pi / 5
                pr = int(impact_r * (0.6 + (i % 3) * 0.2))
                px = tx + int(math.cos(angle_p) * pr)
                py = ty + int(math.sin(angle_p) * pr * 0.8)
                pygame.draw.rect(surface,
                                 (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                                 (px, py, 2, 2))
    # ============================================================
    # SKILL: Q - EARTHSHOCK (ground slam AoE)
    # ============================================================
    def _draw_earthshock_ground(surface, boss, x, y, timer, phase):
        """Ground shockwave at boss location."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Expanding rings on ground
        for i in range(3):
            ring_t = max(0.0, progress - i * 0.15)
            r = int(ring_t * 90)
            if r > 5:
                alpha = _NS_urgharun._alpha(220 * (1 - ring_t))
                pygame.draw.ellipse(surface,
                                    (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_urgharun.PALETTE["fury_mid"], alpha),
                                    (x - r + 3, y + 40 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                    (x - r + 6, y + 40 - r // 3 + 4,
                                     r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_earthshock_fx(surface, boss, x, y, timer, phase):
        """Rock/debris around boss (far from body to avoid coverage)."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Debris positions - far from body edges only
        debris_positions = [
            (-55, 42), (-45, 45), (-38, 40),
            (55, 42), (45, 45), (38, 40),
            (-30, 48), (30, 48),
        ]
        for i, (dx, dy) in enumerate(debris_positions):
            delay = i * 0.05
            local_t = max(0.0, min(1.0, (progress - delay) / (1 - delay)))
            if local_t <= 0:
                continue
            if local_t < 0.4:
                height = int((local_t / 0.4) * 22)
            else:
                height = int(22 * (1 - (local_t - 0.4) / 0.6))
            cx_r = x + dx
            cy_r = y + dy - height
            # Rock chunk
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["shadow_deep"], [
                (cx_r - 3, cy_r + 3),
                (cx_r + 4, cy_r + 3),
                (cx_r + 4, cy_r - 2),
                (cx_r - 3, cy_r - 2),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_darkest"], [
                (cx_r - 3, cy_r + 2),
                (cx_r + 4, cy_r + 2),
                (cx_r + 4, cy_r - 3),
                (cx_r - 3, cy_r - 3),
            ])
            _NS_urgharun._poly(surface, _NS_urgharun.PALETTE["fur_mid"], [
                (cx_r - 2, cy_r + 1),
                (cx_r + 3, cy_r + 1),
                (cx_r + 3, cy_r - 2),
                (cx_r - 2, cy_r - 2),
            ])
            # Fire glow beneath
            if local_t < 0.5:
                alpha = _NS_urgharun._alpha(200 * (1 - local_t * 2))
                pygame.draw.rect(surface,
                                 (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                                 (cx_r, y + dy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                                 (cx_r, y + dy, 1, 1))
        # Fire cracks radiating from center
        if progress < 0.5:
            for i in range(8):
                crack_angle = i * math.pi / 4
                crack_len = int(progress * 60)
                for step in range(3, crack_len, 3):
                    px = x + int(math.cos(crack_angle) * step)
                    py = y + 42 + int(math.sin(crack_angle) * step * 0.4)
                    alpha = _NS_urgharun._alpha(200 * (1 - progress))
                    pygame.draw.rect(surface,
                                     (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                                     (px, py, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                                     (px, py, 1, 1))
    # ============================================================
    # SKILL: W - OVERPOWER (attack speed buff - multi-slash effect)
    # ============================================================
    def _draw_overpower_fx(surface, boss, x, y, timer, phase):
        """Red slashes trailing around boss claws + speed lines."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Red claw trails around each hand (fast slashes)
        for side_i, (arm_side, arm_x) in enumerate([(-1, -8), (1, 10)]):
            claw_cx = x + arm_x * facing
            claw_cy = y + 8
            # 4 layered slash trails at different angles
            for trail_i in range(4):
                trail_t = (phase * 3 + trail_i * math.pi / 2 + side_i * math.pi / 3) \
                          % (math.pi * 2)
                # Curved trail
                trail_len = 12
                start_a = trail_t
                end_a = trail_t + math.pi / 2
                num_pts = 6
                prev_pt = None
                for step in range(num_pts + 1):
                    step_t = step / num_pts
                    a = start_a + (end_a - start_a) * step_t
                    px = claw_cx + int(math.cos(a) * trail_len)
                    py = claw_cy + int(math.sin(a) * trail_len)
                    if prev_pt is not None:
                        alpha = _NS_urgharun._alpha(200 * step_t)
                        pygame.draw.line(surface,
                                         (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                         prev_pt, (px, py), 2)
                        pygame.draw.line(surface,
                                         (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                         prev_pt, (px, py), 1)
                    prev_pt = (px, py)
                # Bright tip
                tip_a = end_a
                tx_p = claw_cx + int(math.cos(tip_a) * trail_len)
                ty_p = claw_cy + int(math.sin(tip_a) * trail_len)
                pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                                 (tx_p, ty_p, 1, 1))
        # Speed particles around body
        for i in range(12):
            angle = phase * 2 + i * math.pi / 6
            r = 30 + int(math.sin(phase * 3 + i) * 5)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_hot"],
                             (sx, sy, 1, 1))
        # Stars around head (stunning target indicator - just decoration)
        if progress > 0.5:
            target = getattr(boss, "target", None)
            if target:
                tx = int(target.x)
                ty = int(target.y) - 20
                for i in range(4):
                    star_angle = phase * 3 + i * math.pi / 2
                    star_r = 15
                    sx = tx + int(math.cos(star_angle) * star_r)
                    sy = ty + int(math.sin(star_angle) * star_r * 0.4)
                    # Star shape (small +)
                    pygame.draw.line(surface,
                                     _NS_urgharun.PALETTE["fury_hot"],
                                     (sx - 2, sy), (sx + 2, sy), 1)
                    pygame.draw.line(surface,
                                     _NS_urgharun.PALETTE["fury_hot"],
                                     (sx, sy - 2), (sx, sy + 2), 1)
                    pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                                     (sx, sy, 1, 1))
    # ============================================================
    # SKILL: E - FURY SWIPES (multi-swipe attack, visual only)
    # ============================================================
    def _draw_furyswipes_fx(surface, boss, x, y, timer, phase):
        """Multiple slash marks from boss to target (rapid claw attacks)."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 80
            ty = y
        # Limit to melee-ish range
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist > 100:
            tx = x + int(dx / dist * 80)
            ty = y + int(dy / dist * 80)
        # 5 rapid slashes appearing at different times
        num_slashes = 5
        for slash_i in range(num_slashes):
            slash_delay = slash_i * 0.15
            slash_t = max(0.0, (progress - slash_delay) / max(0.001, 0.3))
            if slash_t <= 0 or slash_t > 1.2:
                continue
            fade = min(1.0, slash_t * 2) * max(0.0, 1 - (slash_t - 0.5) * 2)
            alpha = _NS_urgharun._alpha(240 * fade)
            # Slash offset
            offset_angle = slash_i * math.pi / 3 + progress * 2
            offset_x = int(math.cos(offset_angle) * 10)
            offset_y = int(math.sin(offset_angle) * 8)
            slash_cx = tx + offset_x
            slash_cy = ty + offset_y
            # Slash mark (3 parallel lines)
            slash_len = 20
            slash_dir_x = facing
            slash_dir_y = -1 + slash_i * 0.4
            for line_off in (-4, 0, 4):
                perp_x = -slash_dir_y
                perp_y = slash_dir_x
                start_x = slash_cx - int(slash_dir_x * slash_len / 2) \
                          + int(perp_x * line_off)
                start_y = slash_cy - int(slash_dir_y * slash_len / 2) \
                          + int(perp_y * line_off)
                end_x = slash_cx + int(slash_dir_x * slash_len / 2) \
                        + int(perp_x * line_off)
                end_y = slash_cy + int(slash_dir_y * slash_len / 2) \
                        + int(perp_y * line_off)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_darkest"], alpha),
                                 (start_x, start_y), (end_x, end_y), 3)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                 (start_x, start_y), (end_x, end_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_mid"], alpha),
                                 (start_x, start_y), (end_x, end_y), 1)
                pygame.draw.line(surface,
                                 (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                 (start_x + 2, start_y), (end_x - 2, end_y), 1)
            # Bright tip
            pygame.draw.rect(surface, (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                             (slash_cx + facing * 8, slash_cy, 2, 2))
    # ============================================================
    # SKILL: R - ENRAGE (rage buff - aura around boss)
    # ============================================================
    def _draw_enrage_ground(surface, boss, x, y, timer, phase):
        """Ground rune circle indicating rage buff."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        # Pulsing ground rings
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_urgharun._alpha(220 * pulse - i * 40)
            pygame.draw.ellipse(surface,
                                (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_urgharun.PALETTE["fury_mid"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                (x - r + 6, y + 40 - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            rune_r = 38
            rx = x + int(math.cos(angle) * rune_r)
            ry = y + 42 + int(math.sin(angle) * rune_r * 0.4)
            pygame.draw.rect(surface,
                             (*_NS_urgharun.PALETTE["fury_hot"],
                              _NS_urgharun._alpha(240 * pulse)),
                             (rx, ry, 3, 3))
            pygame.draw.rect(surface, _NS_urgharun.PALETTE["fury_shine"],
                             (rx, ry, 1, 1))
    def _draw_enrage_fx(surface, boss, x, y, timer, pulse):
        """Rage flames rising around boss (edges only, not overlapping body)."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Rising flames around boss (edge only, radius >= 30 to avoid body)
        for i in range(10):
            angle = pulse * 0.5 + i * math.pi / 5
            base_r = 32
            flame_x = x + int(math.cos(angle) * base_r)
            flame_y_base = y + int(math.sin(angle) * base_r * 0.5)
            # Rising flame animation
            flame_t = (pulse * 0.6 + i * 0.15) % 1.0
            flame_y = flame_y_base - int(flame_t * 20)
            alpha = _NS_urgharun._alpha(220 * (1 - flame_t))
            flame_h = int(6 + flame_t * 4)
            # Flame teardrop shape
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_dark"], alpha),
                                   (flame_x, flame_y), 3)
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_mid"], alpha),
                                   (flame_x, flame_y - 1), 2)
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                   (flame_x, flame_y - 2), 1)
            pygame.draw.rect(surface,
                             (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                             (flame_x, flame_y - 3, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                             (flame_x, flame_y - 4, 1, 1))
        # Rage aura ring (edge only)
        aura_pulse = math.sin(pulse * 4) * 0.3 + 0.7
        for r in range(38, 32, -1):
            alpha = _NS_urgharun._alpha(180 * aura_pulse * (38 - r) / 6)
            _NS_urgharun._aacircle(surface,
                                   (*_NS_urgharun.PALETTE["fury_light"], alpha),
                                   (x, y), r, 1)
        # Fire embers rising (in front only, not overlapping)
        for i in range(6):
            ember_t = (pulse * 0.8 + i * 0.15) % 1.0
            ex = x + 35 + int(math.sin(pulse + i) * 15) if i % 2 == 0 \
                else x - 35 + int(math.sin(pulse + i) * 15)
            ey = y + 20 - int(ember_t * 40)
            alpha = _NS_urgharun._alpha(240 * (1 - ember_t))
            pygame.draw.rect(surface,
                             (*_NS_urgharun.PALETTE["fury_hot"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_urgharun.PALETTE["fury_shine"], alpha),
                             (ex, ey, 1, 1))



# ====================================================================
# YHORANTH (UNFORGIVEN WRAITH) - Mini Boss
# ====================================================================

class _NS_yhoranth:
    """Namespace yhoranth - Unforgiven Wraith boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale)
        "skin_darkest": (60, 45, 40),
        "skin_dark": (130, 100, 90),
        "skin_mid": (200, 170, 155),
        "skin_light": (240, 215, 200),
        "skin_shine": (255, 240, 230),
        # Hair (white/silver)
        "hair_darkest": (75, 80, 95),
        "hair_dark": (140, 145, 160),
        "hair_mid": (200, 205, 215),
        "hair_light": (240, 240, 245),
        "hair_shine": (255, 255, 255),
        # Hakama (dark blue-purple pants)
        "hakama_darkest": (10, 8, 25),
        "hakama_dark": (25, 20, 55),
        "hakama_mid": (55, 45, 95),
        "hakama_light": (95, 85, 145),
        "hakama_edge": (140, 130, 190),
        # Oni mask (red demon)
        "mask_darkest": (35, 3, 5),
        "mask_dark": (110, 15, 20),
        "mask_mid": (200, 40, 45),
        "mask_light": (255, 100, 90),
        "mask_hot": (255, 170, 140),
        "mask_shine": (255, 230, 210),
        # Mask stripes (white/pale)
        "mask_stripe": (240, 235, 220),
        # Sword blade (silver-red)
        "blade_dark": (35, 40, 55),
        "blade_mid": (110, 120, 140),
        "blade_light": (200, 210, 225),
        "blade_shine": (245, 250, 255),
        # Sword edge glow (crimson red)
        "edge_darkest": (40, 3, 8),
        "edge_dark": (140, 15, 30),
        "edge_mid": (230, 40, 60),
        "edge_light": (255, 100, 120),
        "edge_hot": (255, 170, 180),
        "edge_shine": (255, 225, 230),
        # Sword handle (dark wood/wrap)
        "handle_dark": (25, 15, 8),
        "handle_mid": (65, 40, 20),
        "handle_light": (120, 85, 45),
        # Guard/tsuba (gold-brass)
        "gold_dark": (75, 55, 15),
        "gold_mid": (160, 125, 40),
        "gold_light": (230, 195, 90),
        "gold_shine": (255, 240, 170),
        # Petals/particles (pink cherry blossom)
        "petal_dark": (100, 40, 60),
        "petal_mid": (200, 90, 130),
        "petal_light": (255, 180, 210),
        # Spirit blue (for E skill)
        "spirit_darkest": (5, 20, 40),
        "spirit_dark": (20, 70, 130),
        "spirit_mid": (60, 150, 230),
        "spirit_light": (140, 220, 255),
        "spirit_hot": (200, 245, 255),
        "spirit_shine": (240, 255, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_yhoranth._clamp(color)
        if _NS_yhoranth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_yhoranth._clamp(color)
        if _NS_yhoranth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_yhoranth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_yhoranth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_yhoranth._update_yho_attack_anim(boss)
        attacking = bool(getattr(boss, "_yho_attack_active", False))
        moving = _NS_yhoranth._detect_moving(boss)
        # ===== LAYER 1: BACKGROUND =====
        _NS_yhoranth._draw_wraith_aura(surface, x, y, pulse,
                                        spirit_mode=(active_skill == "e"))
        _NS_yhoranth._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # ===== LAYER 2: SKILL GROUND FX =====
        if active_skill == "r":
            _NS_yhoranth._draw_fatesealed_ground(surface, boss, x, y, skill_timer, pulse)
        # ===== LAYER 3: PETALS (cherry blossom - always) =====
        _NS_yhoranth._draw_falling_petals(surface, x, y, pulse)
        # ===== LAYER 4: BODY =====
        if attacking:
            _NS_yhoranth._draw_yho_attack(surface, boss, x, y, active_skill)
        elif moving:
            _NS_yhoranth._draw_yho_walk(surface, boss, x, y, active_skill)
        else:
            _NS_yhoranth._draw_yho_idle(surface, boss, x, y, active_skill)
        # ===== LAYER 5: FOREGROUND FX =====
        # Basic attack (katana slash arc)
        if attacking and not active_skill:
            _NS_yhoranth._draw_basic_attack_fx(surface, boss, x, y)
        # Skill FX foreground
        if active_skill == "q":
            _NS_yhoranth._draw_mortalsteel_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_yhoranth._draw_spiritcleave_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_yhoranth._draw_soulunbound_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_yhoranth._draw_fatesealed_fx(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_yho_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_yho_previous_timer", timer))
        active = bool(getattr(boss, "_yho_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._yho_attack_active = True
            boss._yho_attack_frame = 0
            active = True
        if active:
            boss._yho_attack_frame = int(getattr(boss, "_yho_attack_frame", 0)) + 1
            attack_duration = 28
            if boss._yho_attack_frame >= attack_duration:
                boss._yho_attack_active = False
                boss._yho_attack_frame = 0
                active = False
        boss._yho_previous_timer = timer
        if active:
            attack_duration = 28
            boss._yho_attack_progress = min(1.0,
                boss._yho_attack_frame / attack_duration)
        else:
            boss._yho_attack_progress = 0.0
    def _detect_moving(boss):
        if not hasattr(boss, "_yho_last_x"):
            boss._yho_last_x = boss.x
            boss._yho_last_y = boss.y
            return False
        dx = abs(boss.x - boss._yho_last_x)
        dy = abs(boss.y - boss._yho_last_y)
        boss._yho_last_x = boss.x
        boss._yho_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_yho_idle(surface, boss, x, y, active_skill):
        breath = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_yhoranth._draw_shadow(surface, x, y + 52)
        _NS_yhoranth._draw_yho_body(surface, x, y + breath, boss.direction,
                                     boss.pulse, "idle",
                                     active_skill=active_skill)
    def _draw_yho_walk(surface, boss, x, y, active_skill):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.2) * 3)
        _NS_yhoranth._draw_shadow(surface, x, y + 52)
        _NS_yhoranth._draw_yho_body(surface, x, y + bob, boss.direction,
                                     phase, "walk",
                                     active_skill=active_skill)
    def _draw_yho_attack(surface, boss, x, y, active_skill):
        """Katana slash animation."""
        progress = getattr(boss, "_yho_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        # Rear back → forward step → recover
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-4 + t * 16)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(12 * (1 - t)) * facing
            lift = int(-2 + t * 2)
        _NS_yhoranth._draw_shadow(surface, x + lunge, y + 52)
        _NS_yhoranth._draw_yho_body(surface, x + lunge, y - lift, facing,
                                     boss.pulse, "attack", progress,
                                     active_skill=active_skill)
    # ============================================================
    # BODY (Humanoid samurai)
    # ============================================================
    def _draw_yho_body(surface, cx, cy, facing, phase, action,
                        attack_progress=0, active_skill=None):
        """Full samurai body: hakama, torso, arms, head with mask."""
        spirit_mode = (active_skill == "e")
        # Hakama (pants - bottom)
        _NS_yhoranth._draw_hakama(surface, cx, cy + 8, facing, phase, action)
        # Torso (bare chest)
        _NS_yhoranth._draw_torso(surface, cx, cy - 4, facing, phase)
        # Left arm (holding second katana, mostly hidden)
        _NS_yhoranth._draw_left_arm(surface, cx, cy - 4, facing, phase, action,
                                     attack_progress)
        # Head (with oni mask + hair)
        _NS_yhoranth._draw_head(surface, cx, cy - 20, facing, phase)
        # Right arm with MAIN KATANA (front - most visible)
        _NS_yhoranth._draw_right_arm_with_katana(surface, cx, cy - 4, facing,
                                                   phase, action, attack_progress)
        # Spirit overlay if E is active
        if spirit_mode:
            _NS_yhoranth._draw_spirit_overlay(surface, cx, cy, facing, phase)
    def _draw_hakama(surface, cx, cy, facing, phase, action):
        """Wide samurai hakama pants."""
        sway = math.sin(phase * 0.6) * 2
        step_sway = 0
        if action == "walk":
            step_sway = int(math.sin(phase * 1.5) * 3)
        # Left leg hakama
        left_pts = [
            (cx - 8, cy - 4),
            (cx - 3, cy - 4),
            (cx - 2, cy + 8),
            (cx - 3 + step_sway, cy + 16),
            (cx - 10 + step_sway, cy + 18),
            (cx - 12, cy + 8),
        ]
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in left_pts])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hakama_darkest"], left_pts)
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hakama_dark"], [
            (cx - 7, cy - 3),
            (cx - 4, cy - 3),
            (cx - 3, cy + 7),
            (cx - 4 + step_sway, cy + 15),
            (cx - 9 + step_sway, cy + 16),
            (cx - 11, cy + 7),
        ])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hakama_mid"], [
            (cx - 6, cy - 2),
            (cx - 5, cy - 2),
            (cx - 4, cy + 6),
            (cx - 6 + step_sway, cy + 14),
            (cx - 8, cy + 6),
        ])
        # Right leg hakama
        right_pts = [
            (cx + 3, cy - 4),
            (cx + 8, cy - 4),
            (cx + 12, cy + 8),
            (cx + 10 - step_sway, cy + 18),
            (cx + 3 - step_sway, cy + 16),
            (cx + 2, cy + 8),
        ]
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in right_pts])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hakama_darkest"], right_pts)
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hakama_dark"], [
            (cx + 4, cy - 3),
            (cx + 7, cy - 3),
            (cx + 11, cy + 7),
            (cx + 9 - step_sway, cy + 16),
            (cx + 4 - step_sway, cy + 15),
            (cx + 3, cy + 7),
        ])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hakama_mid"], [
            (cx + 5, cy - 2),
            (cx + 6, cy - 2),
            (cx + 8, cy + 6),
            (cx + 6 - step_sway, cy + 14),
            (cx + 4, cy + 6),
        ])
        # Belt/obi (dark sash at waist)
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["hakama_darkest"],
                         (cx - 12, cy - 5, 24, 4))
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["hakama_dark"],
                         (cx - 11, cy - 5, 22, 3))
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["hakama_mid"],
                         (cx - 10, cy - 4, 20, 1))
        # Hakama pleats (vertical lines)
        for x_off in (-8, -5, 5, 8):
            pygame.draw.line(surface, _NS_yhoranth.PALETTE["hakama_darkest"],
                             (cx + x_off, cy - 1),
                             (cx + x_off, cy + 12), 1)
        # Feet peeking out (sandals)
        for side, foot_x in [(-1, -7), (1, 7)]:
            foot_offset = step_sway * side
            fx = cx + foot_x + foot_offset
            fy = cy + 18
            pygame.draw.ellipse(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                                (fx - 4, fy - 1, 8, 4))
            pygame.draw.ellipse(surface, _NS_yhoranth.PALETTE["handle_dark"],
                                (fx - 4, fy - 2, 8, 3))
            pygame.draw.ellipse(surface, _NS_yhoranth.PALETTE["handle_mid"],
                                (fx - 3, fy - 2, 6, 2))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Bare muscular chest."""
        torso_pts = [
            (cx - 9, cy - 4),
            (cx - 10, cy + 2),
            (cx - 8, cy + 10),
            (cx - 4, cy + 14),
            (cx + 4, cy + 14),
            (cx + 8, cy + 10),
            (cx + 10, cy + 2),
            (cx + 9, cy - 4),
        ]
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["skin_darkest"], torso_pts)
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["skin_dark"], [
            (cx - 8, cy - 3),
            (cx - 9, cy + 2),
            (cx - 7, cy + 9),
            (cx - 3, cy + 13),
            (cx + 3, cy + 13),
            (cx + 7, cy + 9),
            (cx + 9, cy + 2),
            (cx + 8, cy - 3),
        ])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["skin_mid"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 3),
            (cx - 5, cy + 8),
            (cx - 2, cy + 11),
            (cx + 2, cy + 11),
            (cx + 5, cy + 8),
            (cx + 7, cy + 3),
            (cx + 6, cy - 1),
        ])
        # Chest highlight (muscle)
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["skin_light"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 5),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 4, cy + 5),
            (cx + 3, cy + 1),
        ])
        # Abs/muscle definition lines
        pygame.draw.line(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                         (cx, cy + 4), (cx, cy + 12), 1)
        for y_off in (5, 8):
            pygame.draw.line(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                             (cx - 4, cy + y_off), (cx - 1, cy + y_off), 1)
            pygame.draw.line(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                             (cx + 1, cy + y_off), (cx + 4, cy + y_off), 1)
        # Shoulder highlight
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["skin_light"],
                         (cx - 8, cy - 2, 2, 3))
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["skin_shine"],
                         (cx - 8, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["skin_light"],
                         (cx + 6, cy - 2, 2, 3))
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["skin_shine"],
                         (cx + 7, cy - 2, 1, 1))
    def _draw_left_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Left arm - holding second katana (mostly behind)."""
        shoulder_x = cx - facing * 8
        shoulder_y = cy - 2
        # Hand rests near hip (idle) or moves during attack
        if action == "attack":
            hand_x = shoulder_x - facing * (2 + int(attack_progress * 4))
            hand_y = shoulder_y + 12 - int(attack_progress * 3)
        else:
            hand_x = shoulder_x - facing * 2 + int(math.sin(phase * 0.5) * 1)
            hand_y = shoulder_y + 14
        elbow_x = int((shoulder_x + hand_x) / 2) - facing * 2
        elbow_y = int((shoulder_y + hand_y) / 2)
        # Upper arm (skin)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_mid"],
                              (shoulder_x - 1, shoulder_y),
                              (elbow_x - 1, elbow_y), 1)
        # Forearm
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Hand
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                                (hand_x, hand_y), 2)
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)
    def _draw_right_arm_with_katana(surface, cx, cy, facing, phase, action,
                                     attack_progress):
        """Right arm holding main katana - VERY VISIBLE."""
        shoulder_x = cx + facing * 8
        shoulder_y = cy - 2
        # Idle: sword pointed down-forward
        # Attack: swings in arc
        if action == "attack":
            if attack_progress < 0.3:
                # Rear back
                t = attack_progress / 0.3
                sword_angle = math.radians(-140) if facing == 1 \
                              else math.radians(-40)
                sword_angle -= t * math.radians(30) * facing
            elif attack_progress < 0.6:
                # Swing forward
                t = (attack_progress - 0.3) / 0.3
                start_a = math.radians(-170) if facing == 1 else math.radians(-10)
                end_a = math.radians(-20) if facing == 1 else math.radians(-160)
                sword_angle = start_a + (end_a - start_a) * t
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                sword_angle = math.radians(-20) if facing == 1 else math.radians(-160)
                sword_angle += t * math.radians(20) * facing
        else:
            # Idle: sword down-forward
            sword_angle = math.radians(-30) if facing == 1 else math.radians(-150)
            sword_angle += math.sin(phase * 0.5) * math.radians(3)
        # Hand position based on sword angle
        hand_dist = 10
        hand_x = shoulder_x + int(math.cos(sword_angle) * hand_dist)
        hand_y = shoulder_y + int(math.sin(sword_angle) * hand_dist)
        # Elbow
        elbow_x = int((shoulder_x + hand_x) / 2) + facing * 2
        elbow_y = int((shoulder_y + hand_y) / 2)
        # Upper arm
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_mid"],
                              (shoulder_x - 1, shoulder_y),
                              (elbow_x - 1, elbow_y), 1)
        # Forearm
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # KATANA drawn from hand outward
        _NS_yhoranth._draw_katana(surface, hand_x, hand_y, sword_angle, facing,
                                    phase, action)
    def _draw_katana(surface, hand_x, hand_y, angle, facing, phase, action):
        """Long crimson katana blade."""
        # Direction perpendicular for width
        perp = angle + math.pi / 2
        # HANDLE (tsuka)
        handle_len = 6
        handle_end_x = hand_x - int(math.cos(angle) * handle_len)
        handle_end_y = hand_y - int(math.sin(angle) * handle_len)
        # Handle body
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1),
                              (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["handle_dark"],
                              (hand_x, hand_y), (handle_end_x, handle_end_y), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["handle_mid"],
                              (hand_x, hand_y), (handle_end_x, handle_end_y), 2)
        # Handle wrap lines
        for i in range(1, 5):
            wrap_t = i / 5
            wx = hand_x - int(math.cos(angle) * handle_len * wrap_t)
            wy = hand_y - int(math.sin(angle) * handle_len * wrap_t)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["handle_light"],
                             (wx, wy, 1, 1))
        # GUARD (tsuba) - small round disc at handle-blade meeting
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["gold_dark"],
                                (hand_x, hand_y), 3)
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["gold_mid"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["gold_light"],
                         (hand_x, hand_y, 1, 1))
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["gold_shine"],
                         (hand_x, hand_y - 1, 1, 1))
        # BLADE (long crimson katana)
        blade_len = 34
        tip_x = hand_x + int(math.cos(angle) * blade_len)
        tip_y = hand_y + int(math.sin(angle) * blade_len)
        # Blade shape with slight curve - draw as thick line + edge
        # Shadow
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                              (hand_x + 2, hand_y + 2),
                              (tip_x + 2, tip_y + 2), 4)
        # Blade body (silver)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["blade_dark"],
                              (hand_x, hand_y), (tip_x, tip_y), 4)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["blade_mid"],
                              (hand_x, hand_y), (tip_x, tip_y), 3)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["blade_light"],
                              (hand_x, hand_y), (tip_x, tip_y), 2)
        _NS_yhoranth._aaline(surface, _NS_yhoranth.PALETTE["blade_shine"],
                              (hand_x, hand_y), (tip_x, tip_y), 1)
        # CRIMSON EDGE GLOW along cutting edge
        edge_off_x = int(math.cos(perp) * 2)
        edge_off_y = int(math.sin(perp) * 2)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        edge_alpha = int(220 * pulse)
        # Glow along edge (outside blade)
        for glow_r in range(3, 0, -1):
            offx = int(math.cos(perp) * (2 + glow_r))
            offy = int(math.sin(perp) * (2 + glow_r))
            alpha = _NS_yhoranth._alpha(edge_alpha * (3 - glow_r) / 3)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                             (hand_x + offx, hand_y + offy),
                             (tip_x + offx, tip_y + offy), 2)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                             (hand_x + offx, hand_y + offy),
                             (tip_x + offx, tip_y + offy), 1)
        # Sharp bright edge line
        pygame.draw.line(surface, _NS_yhoranth.PALETTE["edge_mid"],
                         (hand_x + edge_off_x, hand_y + edge_off_y),
                         (tip_x + edge_off_x, tip_y + edge_off_y), 1)
        pygame.draw.line(surface, _NS_yhoranth.PALETTE["edge_light"],
                         (hand_x + int(edge_off_x * 0.7),
                          hand_y + int(edge_off_y * 0.7)),
                         (tip_x + int(edge_off_x * 0.7),
                          tip_y + int(edge_off_y * 0.7)), 1)
        # Blade tip sparkle
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["edge_hot"],
                                (tip_x, tip_y), 2)
        _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["edge_shine"],
                                (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Head with long white hair + oni mask."""
        # Long hair behind (flowing)
        hair_sway = math.sin(phase * 0.5) * 2
        # Back hair (long strands)
        hair_back_pts = [
            (cx - 7, cy + 2),
            (cx - 9, cy - 3),
            (cx - 8, cy - 8),
            (cx - 4, cy - 11),
            (cx + 4, cy - 11),
            (cx + 8, cy - 8),
            (cx + 9, cy - 3),
            (cx + 7, cy + 2),
            (cx + 8 + hair_sway, cy + 10),
            (cx + 6, cy + 16),
            (cx + 2, cy + 20),
            (cx - 2, cy + 20),
            (cx - 6, cy + 16),
            (cx - 8 - hair_sway, cy + 10),
        ]
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in hair_back_pts])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hair_darkest"],
                           hair_back_pts)
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hair_dark"], [
            (cx - 6, cy + 1),
            (cx - 8, cy - 3),
            (cx - 7, cy - 7),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 7, cy - 7),
            (cx + 8, cy - 3),
            (cx + 6, cy + 1),
            (cx + 7 + hair_sway, cy + 10),
            (cx + 5, cy + 15),
            (cx + 1, cy + 18),
            (cx - 1, cy + 18),
            (cx - 5, cy + 15),
            (cx - 7 - hair_sway, cy + 10),
        ])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["hair_mid"], [
            (cx - 5, cy),
            (cx - 6, cy - 4),
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 6, cy - 4),
            (cx + 5, cy),
            (cx + 5 + hair_sway, cy + 8),
            (cx + 3, cy + 13),
            (cx - 3, cy + 13),
            (cx - 5 - hair_sway, cy + 8),
        ])
        # Hair highlights (silver shine)
        for hair_x in (-3, 1, 4):
            pygame.draw.line(surface, _NS_yhoranth.PALETTE["hair_light"],
                             (cx + hair_x, cy - 6),
                             (cx + hair_x + hair_sway // 2, cy + 12), 1)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["hair_shine"],
                             (cx + hair_x, cy - 6, 1, 1))
        # ONI MASK (red demon face)
        _NS_yhoranth._draw_oni_mask(surface, cx, cy, facing, phase)
    def _draw_oni_mask(surface, cx, cy, facing, phase):
        """Red oni demon mask covering face."""
        # Mask shape (angular demon face)
        mask_pts = [
            (cx - 5, cy - 5),
            (cx - 6, cy - 2),
            (cx - 5, cy + 2),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 5, cy + 2),
            (cx + 6, cy - 2),
            (cx + 5, cy - 5),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ]
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                           [(px + 1, py + 1) for px, py in mask_pts])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["mask_darkest"], mask_pts)
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["mask_dark"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 1),
            (cx - 4, cy + 1),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
            (cx + 4, cy + 1),
            (cx + 5, cy - 1),
            (cx + 4, cy - 4),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["mask_mid"], [
            (cx - 3, cy - 3),
            (cx - 4, cy),
            (cx - 3, cy + 2),
            (cx - 1, cy + 3),
            (cx + 1, cy + 3),
            (cx + 3, cy + 2),
            (cx + 4, cy),
            (cx + 3, cy - 3),
        ])
        # Highlight
        _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["mask_light"], [
            (cx - 1, cy - 2),
            (cx + 2, cy - 3),
            (cx + 3, cy),
            (cx + 1, cy + 1),
        ])
        pygame.draw.rect(surface, _NS_yhoranth.PALETTE["mask_shine"],
                         (cx + 2, cy - 3, 1, 1))
        # White stripes (traditional oni marks)
        for stripe_y in (-3, 1):
            pygame.draw.line(surface, _NS_yhoranth.PALETTE["mask_stripe"],
                             (cx - 4, cy + stripe_y),
                             (cx + 4, cy + stripe_y), 1)
        # Small horns on top of mask
        for side in (-1, 1):
            horn_x = cx + side * 4
            horn_top_y = cy - 8
            _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["shadow_deep"], [
                (horn_x + 1, horn_top_y + 1),
                (horn_x - 1 + 1, cy - 5 + 1),
                (horn_x + 2 * side + 1, cy - 5 + 1),
            ])
            _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["mask_darkest"], [
                (horn_x, horn_top_y),
                (horn_x - 1, cy - 5),
                (horn_x + 2 * side, cy - 5),
            ])
            _NS_yhoranth._poly(surface, _NS_yhoranth.PALETTE["mask_dark"], [
                (horn_x, horn_top_y),
                (horn_x, cy - 5),
                (horn_x + 1 * side, cy - 5),
            ])
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["mask_shine"],
                             (horn_x, horn_top_y, 1, 1))
        # Fierce glowing eyes (through mask)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            # Eye socket in mask
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                             (eye_x - 1, cy - 2, 2, 2))
            for r in range(3, 0, -1):
                alpha = _NS_yhoranth._alpha(200 * (3 - r) / 3 * pulse)
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                                        (eye_x, cy - 1), r)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["edge_shine"],
                             (eye_x, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["white"],
                             (eye_x, cy - 1, 1, 1))
        # Mouth line (angry frown - down curve)
        pygame.draw.line(surface, _NS_yhoranth.PALETTE["shadow_deep"],
                         (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
    def _draw_spirit_overlay(surface, cx, cy, facing, phase):
        """Blue spirit ghost overlay for E skill."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        # Multiple layered spirit trails around body
        for r in range(20, 5, -3):
            alpha = _NS_yhoranth._alpha(60 * pulse * (20 - r) / 15)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["spirit_dark"], alpha),
                                    (cx, cy), r)
        for r in range(15, 3, -2):
            alpha = _NS_yhoranth._alpha(90 * pulse * (15 - r) / 12)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["spirit_mid"], alpha),
                                    (cx, cy), r)
        # Spirit wisps around
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            wisp_r = 25 + int(math.sin(phase * 3 + i) * 5)
            wx = cx + int(math.cos(angle) * wisp_r)
            wy = cy + int(math.sin(angle) * wisp_r * 0.6)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["spirit_light"],
                             (wx, wy, 2, 2))
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["spirit_shine"],
                             (wx, wy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius,
                                 80 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 1, 3, 180), (5, 6, 90, 10))
        surface.blit(shadow, (x - 50, y - 12))
    def _draw_wraith_aura(surface, x, y, phase, spirit_mode=False):
        """Wraith aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        # Base dark aura
        for radius in range(90, 5, -5):
            alpha = _NS_yhoranth._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_yhoranth._aacircle(aura,
                                        (*_NS_yhoranth.PALETTE["hakama_darkest"], alpha),
                                        (110, 100), radius)
        # Red inner aura
        aura_color = "spirit_dark" if spirit_mode else "edge_darkest"
        for radius in range(50, 5, -3):
            alpha = _NS_yhoranth._alpha((50 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_yhoranth._aacircle(aura,
                                        (*_NS_yhoranth.PALETTE[aura_color], alpha),
                                        (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating particles (red/spirit)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.4)
            color_key = "spirit_light" if spirit_mode else "edge_mid"
            hot_key = "spirit_hot" if spirit_mode else "edge_light"
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE[color_key],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE[hot_key],
                             (sx, sy, 1, 1))
    def _draw_falling_petals(surface, x, y, phase):
        """Cherry blossom petals falling around boss."""
        for i in range(12):
            t = (phase * 0.3 + i * 0.083) % 1.0
            drift_x = math.sin(phase * 0.8 + i * 0.5) * 40
            base_x = x + int(drift_x) + (i - 6) * 8
            base_y = y - 60 + int(t * 120)
            alpha = _NS_yhoranth._alpha(200 * (1 - abs(t - 0.5) * 0.8))
            # Petal shape (small diamond)
            pygame.draw.polygon(surface,
                                (*_NS_yhoranth.PALETTE["petal_dark"], alpha), [
                (base_x, base_y - 2),
                (base_x + 2, base_y),
                (base_x, base_y + 2),
                (base_x - 2, base_y),
            ])
            pygame.draw.polygon(surface,
                                (*_NS_yhoranth.PALETTE["petal_mid"], alpha), [
                (base_x, base_y - 1),
                (base_x + 1, base_y),
                (base_x, base_y + 1),
                (base_x - 1, base_y),
            ])
            pygame.draw.rect(surface,
                             (*_NS_yhoranth.PALETTE["petal_light"], alpha),
                             (base_x, base_y, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_yhoranth.PALETTE["edge_darkest"], 200),
                            (5, 14, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_yhoranth.PALETTE["hakama_darkest"], 220),
                            (14, 16, 122, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_yhoranth.PALETTE["edge_dark"], 220),
                            (25, 18, 100, 14), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 40)
            y1 = 25 + int(math.sin(angle) * 6)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 25 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_yhoranth.PALETTE["edge_mid"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_yhoranth.PALETTE["edge_hot"],
                                        _NS_yhoranth._alpha(150 * pulse)),
                                (15, 10, 120, 30), 1)
        surface.blit(ring, (x - 75, y - 23))
    # ============================================================
    # BASIC ATTACK - Katana Slash (MELEE)
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic melee: crimson katana slash arc + impact at target."""
        progress = getattr(boss, "_yho_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y
        # Limit to melee range
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist > 80:
            tx = x + int(dx / dist * 60)
            ty = y + int(dy / dist * 60)
        # PHASE 1: Wind-up (0-30%) - blade glow charging
        if progress < 0.3:
            t = progress / 0.3
            # Charge glow on blade (subtle)
            blade_x = x + facing * 15
            blade_y = y - 5
            for r in range(int(3 + t * 3), 0, -1):
                alpha = _NS_yhoranth._alpha(180 * t * r / 6)
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                                        (blade_x, blade_y), r)
        # PHASE 2: SLASH ARC (30-70%)
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            slash_cx = x + facing * 20
            slash_cy = y - 4
            arc_radius = 38
            start_angle = math.radians(-100) if facing == 1 \
                          else math.radians(-80)
            end_angle = math.radians(80) if facing == 1 \
                        else math.radians(260)
            current_angle = start_angle + (end_angle - start_angle) * t
            # Main slash arc (curved crimson trail)
            num_pts = 15
            prev_pt = None
            for step in range(num_pts + 1):
                step_t = step / num_pts
                a = start_angle + (current_angle - start_angle) * step_t
                px = slash_cx + int(math.cos(a) * arc_radius) * facing
                py = slash_cy + int(math.sin(a) * arc_radius)
                if prev_pt is not None:
                    alpha = _NS_yhoranth._alpha(240 * step_t * (1 - t * 0.3))
                    # Thick layered slash
                    pygame.draw.line(surface,
                                     (*_NS_yhoranth.PALETTE["edge_darkest"], alpha),
                                     prev_pt, (px, py), 6)
                    pygame.draw.line(surface,
                                     (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                                     prev_pt, (px, py), 5)
                    pygame.draw.line(surface,
                                     (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                                     prev_pt, (px, py), 3)
                    pygame.draw.line(surface,
                                     (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                                     prev_pt, (px, py), 2)
                    pygame.draw.line(surface,
                                     (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                                     prev_pt, (px, py), 1)
                prev_pt = (px, py)
            # Bright slash tip (current position)
            tip_a = current_angle
            tip_x = slash_cx + int(math.cos(tip_a) * arc_radius) * facing
            tip_y = slash_cy + int(math.sin(tip_a) * arc_radius)
            for r in range(6, 0, -1):
                alpha = _NS_yhoranth._alpha(240 * (6 - r) / 6)
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_hot"], alpha),
                                        (tip_x, tip_y), r)
            _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["edge_shine"],
                                    (tip_x, tip_y), 2)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))
            # Sparks flying from slash
            for i in range(6):
                spark_angle = start_angle + (current_angle - start_angle) \
                              * (0.4 + (i % 4) * 0.15)
                spark_r = arc_radius + math.sin(boss.pulse * 4 + i) * 8
                sx = slash_cx + int(math.cos(spark_angle) * spark_r) * facing
                sy = slash_cy + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface, _NS_yhoranth.PALETTE["edge_hot"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_yhoranth.PALETTE["edge_shine"],
                                 (sx, sy, 1, 1))
        # PHASE 3: IMPACT (70-100%)
        else:
            t = (progress - 0.7) / 0.3
            impact_r = int(8 + t * 22)
            alpha = _NS_yhoranth._alpha(240 * (1 - t))
            # Impact burst
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                                    (tx, ty), impact_r + 2, 3)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                                    (tx, ty), impact_r, 2)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                                    (tx, ty), max(1, impact_r - 5), 1)
            # Bright core
            core_r = max(1, int(6 * (1 - t)))
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["edge_hot"], alpha),
                                    (tx, ty), core_r + 2)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                                    (tx, ty), max(1, core_r))
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["white"], (tx, ty, 1, 1))
            # Single sharp slash line at target (katana cut)
            cut_len = int(20 * (1 - t * 0.3))
            cut_start = (tx - cut_len // 2 * facing, ty - cut_len // 3)
            cut_end = (tx + cut_len // 2 * facing, ty + cut_len // 3)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_darkest"], alpha),
                             cut_start, cut_end, 3)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                             cut_start, cut_end, 2)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                             cut_start, cut_end, 1)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                             (cut_start[0] + 3, cut_start[1] + 1),
                             (cut_end[0] - 3, cut_end[1] - 1), 1)
            # Radial sparks
            for i in range(10):
                angle_p = i * math.pi / 5
                pr = int(impact_r * (0.7 + (i % 3) * 0.15))
                px = tx + int(math.cos(angle_p) * pr)
                py = ty + int(math.sin(angle_p) * pr * 0.8)
                pygame.draw.rect(surface,
                                 (*_NS_yhoranth.PALETTE["edge_hot"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: Q - MORTAL STEEL (thrust + circle slash)
    # ============================================================
    def _draw_mortalsteel_fx(surface, boss, x, y, timer, phase):
        """Forward thrust + potential circle slash."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big circle slash around boss (phase 2 stack visualization)
        if progress > 0.4:
            t = (progress - 0.4) / 0.6
            radius = int(30 + t * 25)
            alpha = _NS_yhoranth._alpha(240 * (1 - t))
            # Full circle slash
            num_pts = 24
            circle_pts = []
            for i in range(num_pts + 1):
                a = (i / num_pts) * math.pi * 2 + phase * 0.5
                px = x + int(math.cos(a) * radius)
                py = y + int(math.sin(a) * radius * 0.7)
                circle_pts.append((px, py))
            # Draw circular arc trail
            for i in range(len(circle_pts) - 1):
                fade = min(1.0, (i / len(circle_pts)) * 2)
                arc_alpha = _NS_yhoranth._alpha(alpha * fade)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_darkest"], arc_alpha),
                                 circle_pts[i], circle_pts[i + 1], 5)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_dark"], arc_alpha),
                                 circle_pts[i], circle_pts[i + 1], 4)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_mid"], arc_alpha),
                                 circle_pts[i], circle_pts[i + 1], 2)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_light"], arc_alpha),
                                 circle_pts[i], circle_pts[i + 1], 1)
        # Thrust line forward (phase 1)
        else:
            t = progress / 0.4
            thrust_len = int(t * 60)
            thrust_start_x = x + facing * 25
            thrust_end_x = thrust_start_x + facing * thrust_len
            alpha = _NS_yhoranth._alpha(240 * (1 - t * 0.3))
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_darkest"], alpha),
                             (thrust_start_x, y - 4),
                             (thrust_end_x, y - 4), 6)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                             (thrust_start_x, y - 4),
                             (thrust_end_x, y - 4), 4)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                             (thrust_start_x, y - 4),
                             (thrust_end_x, y - 4), 2)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                             (thrust_start_x, y - 4),
                             (thrust_end_x, y - 4), 1)
            # Sharp tip
            for r in range(4, 0, -1):
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_hot"], alpha),
                                        (thrust_end_x, y - 4), r)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["white"],
                             (thrust_end_x, y - 4, 1, 1))
    # ============================================================
    # SKILL: W - SPIRIT CLEAVE (large crescent slash)
    # ============================================================
    def _draw_spiritcleave_fx(surface, boss, x, y, timer, phase):
        """Huge crescent moon slash forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big crescent moon shape
        crescent_cx = x + facing * 55
        crescent_cy = y - 4
        radius = int(45 * min(1.0, progress * 1.5))
        if radius < 5:
            return
        fade = 1.0
        if progress > 0.6:
            fade = 1.0 - (progress - 0.6) / 0.4
        alpha = _NS_yhoranth._alpha(240 * fade)
        # Crescent arc (draw as curve)
        start_angle = math.radians(-100) if facing == 1 else math.radians(-80)
        end_angle = math.radians(100) if facing == 1 else math.radians(260)
        num_pts = 20
        prev_pt = None
        for step in range(num_pts + 1):
            step_t = step / num_pts
            a = start_angle + (end_angle - start_angle) * step_t
            # Outer arc
            px = crescent_cx + int(math.cos(a) * radius) * facing
            py = crescent_cy + int(math.sin(a) * radius)
            if prev_pt is not None:
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_darkest"], alpha),
                                 prev_pt, (px, py), 8)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                                 prev_pt, (px, py), 6)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                                 prev_pt, (px, py), 4)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                                 prev_pt, (px, py), 2)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                                 prev_pt, (px, py), 1)
            prev_pt = (px, py)
        # Inner smaller arc (crescent shape)
        inner_r = int(radius * 0.75)
        prev_pt = None
        for step in range(num_pts + 1):
            step_t = step / num_pts
            a = start_angle + (end_angle - start_angle) * step_t
            px = crescent_cx + int(math.cos(a) * inner_r) * facing
            py = crescent_cy + int(math.sin(a) * inner_r)
            if prev_pt is not None:
                alpha_i = _NS_yhoranth._alpha(alpha * 0.5)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_dark"], alpha_i),
                                 prev_pt, (px, py), 3)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_light"], alpha_i),
                                 prev_pt, (px, py), 1)
            prev_pt = (px, py)
        # Sparks along crescent
        for i in range(10):
            spark_a = start_angle + (end_angle - start_angle) * (i / 10)
            sr = radius + int(math.sin(phase * 3 + i) * 5)
            sx = crescent_cx + int(math.cos(spark_a) * sr) * facing
            sy = crescent_cy + int(math.sin(spark_a) * sr)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["edge_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["edge_shine"],
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: E - SOUL UNBOUND (spirit dash effect)
    # ============================================================
    def _draw_soulunbound_fx(surface, boss, x, y, timer, phase):
        """Spirit dash - ghostly trails."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Speed lines / motion blur behind
        for i in range(8):
            trail_x = x - facing * (10 + i * 10)
            trail_y = y - 5 + int(math.sin(phase * 2 + i) * 2)
            alpha = _NS_yhoranth._alpha(180 * (1 - i / 8))
            # Ghostly blue trail
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["spirit_dark"], alpha),
                                    (trail_x, trail_y), 6)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["spirit_mid"], alpha),
                                    (trail_x, trail_y), 4)
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["spirit_light"], alpha),
                                    (trail_x, trail_y), 2)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["spirit_shine"],
                             (trail_x, trail_y, 1, 1))
        # Speed lines
        for i in range(6):
            line_y = y - 12 + i * 5
            line_start = x - facing * 40
            line_end = x - facing * 15
            alpha = _NS_yhoranth._alpha(200)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["spirit_light"], alpha),
                             (line_start, line_y), (line_end, line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["spirit_shine"], alpha),
                             (line_start, line_y), (line_end, line_y), 1)
        # Rising spirit wisps
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            wx = x - 30 + i * 6 + int(math.sin(phase + i) * 4)
            wy = y + 15 - int(t * 40)
            alpha = _NS_yhoranth._alpha(220 * (1 - t))
            _NS_yhoranth._aacircle(surface,
                                    (*_NS_yhoranth.PALETTE["spirit_mid"], alpha),
                                    (wx, wy), 2)
            pygame.draw.rect(surface, _NS_yhoranth.PALETTE["spirit_hot"],
                             (wx, wy, 1, 1))
    # ============================================================
    # SKILL: R - FATE SEALED (line strike + teleport)
    # ============================================================
    def _draw_fatesealed_ground(surface, boss, x, y, timer, phase):
        """Ground line marker toward target direction."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Line ground indicator
        alpha = _NS_yhoranth._alpha(180 * (1 - progress * 0.5))
        line_start_x = x + facing * 15
        line_end_x = x + facing * 150
        line_y = y + 42
        pygame.draw.line(surface,
                         (*_NS_yhoranth.PALETTE["edge_darkest"], alpha),
                         (line_start_x, line_y), (line_end_x, line_y), 8)
        pygame.draw.line(surface,
                         (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                         (line_start_x, line_y), (line_end_x, line_y), 6)
        pygame.draw.line(surface,
                         (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                         (line_start_x, line_y), (line_end_x, line_y), 3)
        pygame.draw.line(surface,
                         (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                         (line_start_x, line_y), (line_end_x, line_y), 1)
    def _draw_fatesealed_fx(surface, boss, x, y, timer, phase):
        """Massive line slash forward + teleport wisp."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        line_start_x = x + facing * 15
        line_end_x = x + facing * 150
        line_y = y - 4
        # Phase 1: Charge (0-30%)
        if progress < 0.3:
            t = progress / 0.3
            # Growing charge at boss's blade
            charge_x = x + facing * 22
            charge_y = y - 5
            for r in range(int(4 + t * 8), 0, -1):
                alpha = _NS_yhoranth._alpha(220 * t * r / 12)
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                                        (charge_x, charge_y), r)
            _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["edge_light"],
                                    (charge_x, charge_y), max(1, int(3 * t)))
            _NS_yhoranth._aacircle(surface, _NS_yhoranth.PALETTE["edge_shine"],
                                    (charge_x, charge_y), max(1, int(1 * t)))
        # Phase 2: STRIKE - massive line slash (30-70%)
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            fade = math.sin(t * math.pi)  # peaks then fades
            alpha = _NS_yhoranth._alpha(255 * fade)
            # Massive horizontal line slash
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_darkest"], alpha),
                             (line_start_x, line_y),
                             (line_end_x, line_y), 12)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                             (line_start_x, line_y),
                             (line_end_x, line_y), 10)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                             (line_start_x, line_y),
                             (line_end_x, line_y), 6)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                             (line_start_x, line_y),
                             (line_end_x, line_y), 3)
            pygame.draw.line(surface,
                             (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                             (line_start_x, line_y),
                             (line_end_x, line_y), 1)
            # Additional lines above and below for airborne effect
            for y_off in (-8, 8):
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_dark"],
                                  _NS_yhoranth._alpha(alpha * 0.6)),
                                 (line_start_x, line_y + y_off),
                                 (line_end_x, line_y + y_off), 4)
                pygame.draw.line(surface,
                                 (*_NS_yhoranth.PALETTE["edge_light"],
                                  _NS_yhoranth._alpha(alpha * 0.6)),
                                 (line_start_x, line_y + y_off),
                                 (line_end_x, line_y + y_off), 1)
            # Sparks along line
            for i in range(15):
                sx = line_start_x + facing * (i * 10) \
                     + int(math.sin(phase * 5 + i) * 3)
                sy = line_y + int(math.cos(phase * 5 + i) * 4)
                pygame.draw.rect(surface,
                                 (*_NS_yhoranth.PALETTE["edge_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Airborne indicator (up arrows at end)
            if fade > 0.5:
                for i in range(3):
                    arrow_x = line_end_x - i * 15 * facing
                    arrow_y_base = line_y - 12
                    for arrow_off in range(3):
                        pygame.draw.rect(surface,
                                         (*_NS_yhoranth.PALETTE["edge_shine"],
                                          alpha),
                                         (arrow_x, arrow_y_base - arrow_off, 1, 1))
        # Phase 3: Aftermath / teleport wisps (70-100%)
        else:
            t = (progress - 0.7) / 0.3
            # Wisps behind indicating teleport
            for i in range(8):
                wisp_x = line_end_x - facing * (i * 15)
                wisp_y = line_y + int(math.sin(phase * 3 + i) * 5)
                alpha = _NS_yhoranth._alpha(200 * (1 - t) * (1 - i / 8))
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_dark"], alpha),
                                        (wisp_x, wisp_y), 4)
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_mid"], alpha),
                                        (wisp_x, wisp_y), 3)
                _NS_yhoranth._aacircle(surface,
                                        (*_NS_yhoranth.PALETTE["edge_light"], alpha),
                                        (wisp_x, wisp_y), 2)
                pygame.draw.rect(surface,
                                 (*_NS_yhoranth.PALETTE["edge_shine"], alpha),
                                 (wisp_x, wisp_y, 1, 1))



# ====================================================================
# ZULKHAVEN (DEVOURER) - Mini Boss
# ====================================================================

class _NS_zulkhaven:
    """Namespace zulkhaven - The Devourer boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Flesh skin (pink-tan pucat)
        "flesh_darkest": (50, 30, 25),
        "flesh_dark": (110, 75, 60),
        "flesh_mid": (185, 140, 115),
        "flesh_light": (225, 180, 155),
        "flesh_edge": (245, 210, 190),
        "flesh_shine": (255, 235, 220),
        # Belly (paler yellow-tan)
        "belly_dark": (95, 75, 55),
        "belly_mid": (170, 145, 100),
        "belly_light": (220, 200, 145),
        # Blood red (mouth, cuts, mata)
        "blood_darkest": (30, 3, 3),
        "blood_dark": (110, 12, 12),
        "blood_mid": (200, 25, 25),
        "blood_light": (255, 70, 60),
        "blood_hot": (255, 130, 110),
        "blood_shine": (255, 210, 190),
        # Teeth/fangs (aged bone yellow)
        "fang_dark": (75, 55, 30),
        "fang_mid": (170, 140, 90),
        "fang_light": (240, 220, 170),
        "fang_shine": (255, 250, 220),
        # Metal shackles
        "metal_darkest": (12, 12, 15),
        "metal_dark": (35, 35, 40),
        "metal_mid": (75, 75, 85),
        "metal_light": (140, 140, 155),
        "metal_shine": (220, 220, 235),
        # Eye (small red)
        "eye_socket": (5, 1, 1),
        "eye_dark": (100, 15, 10),
        "eye_light": (255, 100, 80),
        "eye_glow": (255, 200, 160),
        # Sores/wounds
        "wound_dark": (60, 8, 8),
        "wound_mid": (130, 20, 20),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 1),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zulkhaven._clamp(color)
        if _NS_zulkhaven.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zulkhaven._clamp(color)
        if _NS_zulkhaven.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zulkhaven._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zulkhaven(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_zulkhaven._update_zul_attack_anim(boss)
        attacking = bool(getattr(boss, "_zul_attack_active", False))
        moving = _NS_zulkhaven._detect_moving(boss)
        # ===== LAYER 1: BACKGROUND =====
        _NS_zulkhaven._draw_blood_aura(surface, x, y, pulse,
                                        enraged=(active_skill in ("q", "r")))
        _NS_zulkhaven._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # ===== LAYER 2: SKILL GROUND FX =====
        if active_skill == "q":
            _NS_zulkhaven._draw_rage_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zulkhaven._draw_infest_ground(surface, boss, x, y, skill_timer, pulse)
        # ===== LAYER 3: BLOOD DRIPS (always ambient) =====
        _NS_zulkhaven._draw_blood_drips(surface, x, y, pulse)
        # ===== LAYER 4: BODY =====
        if attacking:
            _NS_zulkhaven._draw_zul_attack(surface, boss, x, y, active_skill)
        elif moving:
            _NS_zulkhaven._draw_zul_walk(surface, boss, x, y, active_skill)
        else:
            _NS_zulkhaven._draw_zul_idle(surface, boss, x, y, active_skill)
        # ===== LAYER 5: FOREGROUND FX =====
        if attacking and not active_skill:
            _NS_zulkhaven._draw_basic_attack_fx(surface, boss, x, y)
        if active_skill == "q":
            _NS_zulkhaven._draw_rage_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zulkhaven._draw_feed_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zulkhaven._draw_openwounds_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zulkhaven._draw_infest_fx(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_zul_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zul_previous_timer", timer))
        active = bool(getattr(boss, "_zul_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._zul_attack_active = True
            boss._zul_attack_frame = 0
            active = True
        if active:
            boss._zul_attack_frame = int(getattr(boss, "_zul_attack_frame", 0)) + 1
            attack_duration = 30
            if boss._zul_attack_frame >= attack_duration:
                boss._zul_attack_active = False
                boss._zul_attack_frame = 0
                active = False
        boss._zul_previous_timer = timer
        if active:
            attack_duration = 30
            boss._zul_attack_progress = min(1.0,
                boss._zul_attack_frame / attack_duration)
        else:
            boss._zul_attack_progress = 0.0
    def _detect_moving(boss):
        if not hasattr(boss, "_zul_last_x"):
            boss._zul_last_x = boss.x
            boss._zul_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zul_last_x)
        dy = abs(boss.y - boss._zul_last_y)
        boss._zul_last_x = boss.x
        boss._zul_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_zul_idle(surface, boss, x, y, active_skill):
        breath = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_zulkhaven._draw_shadow(surface, x, y + 52)
        _NS_zulkhaven._draw_zul_body(surface, x, y + breath, boss.direction,
                                      boss.pulse, "idle", active_skill=active_skill)
    def _draw_zul_walk(surface, boss, x, y, active_skill):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.5) * 4)  # jerky hunched walk
        _NS_zulkhaven._draw_shadow(surface, x, y + 52)
        _NS_zulkhaven._draw_zul_body(surface, x, y + bob, boss.direction,
                                      phase, "walk", active_skill=active_skill)
    def _draw_zul_attack(surface, boss, x, y, active_skill):
        """Bite/claw lunge animation."""
        progress = getattr(boss, "_zul_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        # Rear back → lunge with jaw open → recover
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 5) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-5 + t * 20)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(15 * (1 - t)) * facing
            lift = int(-2 + t * 2)
        _NS_zulkhaven._draw_shadow(surface, x + lunge, y + 52)
        _NS_zulkhaven._draw_zul_body(surface, x + lunge, y - lift, facing,
                                      boss.pulse, "attack", progress,
                                      active_skill=active_skill)
    # ============================================================
    # BODY (Hunched flesh monster with giant maw)
    # ============================================================
    def _draw_zul_body(surface, cx, cy, facing, phase, action,
                        attack_progress=0, active_skill=None):
        """Full body: legs, tail-like back, hunched torso, arms with claws, huge head."""
        enraged = (active_skill in ("q", "r"))
        # Rear legs (crouched)
        _NS_zulkhaven._draw_rear_legs(surface, cx - facing * 14, cy + 12,
                                       facing, phase, action)
        # Main hunched body
        _NS_zulkhaven._draw_hunched_body(surface, cx, cy, facing, phase, enraged)
        # Front arms with bloody claws
        arm_swing = 0
        if action == "attack":
            arm_swing = int(math.sin(attack_progress * math.pi) * 6)
        _NS_zulkhaven._draw_front_arms(surface, cx, cy, facing, phase, arm_swing,
                                        action, attack_progress, enraged)
        # Huge head with giant maw (front of body since hunched)
        head_lunge = 0
        head_lift = 0
        if action == "attack":
            if attack_progress < 0.3:
                head_lunge = -int(attack_progress / 0.3 * 4) * facing
                head_lift = -int(attack_progress / 0.3 * 2)
            elif attack_progress < 0.6:
                t = (attack_progress - 0.3) / 0.3
                head_lunge = int((-4 + t * 18)) * facing
                head_lift = int(-2 + t * 4)
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(14 * (1 - t)) * facing
                head_lift = int(2 - t * 2)
        mouth_open = 3
        if action == "attack":
            mouth_open = max(3, math.sin(attack_progress * math.pi) * 11)
        elif enraged:
            mouth_open = 5 + math.sin(phase * 3) * 2
        _NS_zulkhaven._draw_zul_head(surface, cx + facing * 16 + head_lunge,
                                      cy - 4 + head_lift, facing, phase,
                                      mouth_open, action, enraged)
    def _draw_rear_legs(surface, cx, cy, facing, phase, action):
        """Rear legs (crouched)."""
        step_offset = 0
        if action == "walk":
            step_offset = int(math.sin(phase * 1.5) * 3)
        for leg_i, (side, offset_x) in enumerate([(-1, -3), (1, 3)]):
            leg_offset = step_offset if leg_i == 0 else -step_offset
            leg_top_x = cx + offset_x
            leg_top_y = cy - 4
            leg_bot_x = leg_top_x + leg_offset // 2
            leg_bot_y = cy + 10
            # Thick fleshy leg
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                                   (leg_top_x + 2, leg_top_y + 2),
                                   (leg_bot_x + 2, leg_bot_y + 2), 7)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_darkest"],
                                   (leg_top_x, leg_top_y),
                                   (leg_bot_x, leg_bot_y), 6)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_dark"],
                                   (leg_top_x, leg_top_y),
                                   (leg_bot_x, leg_bot_y), 4)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_mid"],
                                   (leg_top_x - 1, leg_top_y),
                                   (leg_bot_x - 1, leg_bot_y), 2)
            # Paw with claws
            paw_x = leg_bot_x
            paw_y = leg_bot_y
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"], [
                (paw_x - 4, paw_y + 1),
                (paw_x + 5, paw_y + 1),
                (paw_x + 4, paw_y + 5),
                (paw_x - 4, paw_y + 5),
            ])
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_darkest"], [
                (paw_x - 4, paw_y),
                (paw_x + 5, paw_y),
                (paw_x + 4, paw_y + 4),
                (paw_x - 4, paw_y + 4),
            ])
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_dark"], [
                (paw_x - 3, paw_y + 1),
                (paw_x + 4, paw_y + 1),
                (paw_x + 3, paw_y + 3),
                (paw_x - 3, paw_y + 3),
            ])
            # Sharp bloody claws
            for cx_off in (-3, 0, 3):
                claw_x = paw_x + cx_off + facing
                claw_y = paw_y + 3
                _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["fang_dark"], [
                    (claw_x, claw_y),
                    (claw_x + facing, claw_y + 4),
                    (claw_x + facing * 2, claw_y),
                ])
                _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["fang_mid"], [
                    (claw_x, claw_y),
                    (claw_x + facing, claw_y + 3),
                    (claw_x + facing * 2, claw_y),
                ])
                # Blood drip on claw
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_dark"],
                                 (claw_x + facing, claw_y + 2, 1, 2))
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                                 (claw_x + facing, claw_y + 2, 1, 1))
    def _draw_hunched_body(surface, cx, cy, facing, phase, enraged):
        """Hunched torso - upper back exposed, belly hanging."""
        # Body shape (hunched over, elongated forward)
        body_shape = [
            (cx - 18, cy + 4),      # rear top
            (cx - 20, cy - 2),
            (cx - 15, cy - 10),     # arched back top
            (cx - 5, cy - 14),      # highest point
            (cx + 8, cy - 12),
            (cx + 16, cy - 8),      # slope to front
            (cx + 20, cy - 3),
            (cx + 22, cy + 3),
            (cx + 18, cy + 10),     # front bottom
            (cx + 10, cy + 14),
            (cx + 2, cy + 15),      # belly hanging
            (cx - 6, cy + 15),
            (cx - 14, cy + 13),
            (cx - 20, cy + 9),
        ]
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in body_shape])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_darkest"], body_shape)
        # Upper back (flesh)
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_dark"], [
            (cx - 18, cy + 2),
            (cx - 15, cy - 9),
            (cx - 4, cy - 13),
            (cx + 8, cy - 11),
            (cx + 16, cy - 7),
            (cx + 20, cy - 2),
            (cx + 20, cy + 3),
            (cx + 15, cy + 5),
            (cx - 15, cy + 5),
            (cx - 18, cy),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_mid"], [
            (cx - 14, cy - 3),
            (cx - 12, cy - 9),
            (cx - 2, cy - 11),
            (cx + 8, cy - 9),
            (cx + 14, cy - 5),
            (cx + 16, cy - 1),
            (cx + 13, cy + 1),
            (cx - 10, cy + 1),
        ])
        # Highlights on back
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_light"], [
            (cx - 4, cy - 7),
            (cx + 2, cy - 9),
            (cx + 8, cy - 7),
            (cx + 6, cy - 4),
            (cx - 2, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["flesh_edge"],
                         (cx + 2, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["flesh_shine"],
                         (cx + 3, cy - 8, 1, 1))
        # Belly (paler, hanging)
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["belly_dark"], [
            (cx - 14, cy + 5),
            (cx + 14, cy + 5),
            (cx + 18, cy + 8),
            (cx + 12, cy + 13),
            (cx + 2, cy + 15),
            (cx - 6, cy + 15),
            (cx - 14, cy + 13),
            (cx - 18, cy + 8),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["belly_mid"], [
            (cx - 12, cy + 7),
            (cx + 12, cy + 7),
            (cx + 15, cy + 9),
            (cx + 10, cy + 13),
            (cx + 2, cy + 14),
            (cx - 6, cy + 14),
            (cx - 10, cy + 13),
            (cx - 13, cy + 9),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["belly_light"], [
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 11, cy + 11),
            (cx + 6, cy + 12),
            (cx - 4, cy + 12),
            (cx - 10, cy + 11),
        ])
        # Ribs/muscle definition (dark lines)
        for i, y_off in enumerate((-4, -1, 3)):
            pygame.draw.line(surface, _NS_zulkhaven.PALETTE["flesh_darkest"],
                             (cx - 12 + i * 2, cy + y_off),
                             (cx + 12 - i * 2, cy + y_off), 1)
        # Wounds/sores on body (bloody spots)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        wound_alpha = 240 if enraged else 200
        for wx, wy, wr in [
            (cx - 8, cy - 6, 3), (cx + 10, cy - 4, 2),
            (cx - 4, cy + 3, 2), (cx + 6, cy + 6, 3),
            (cx - 12, cy + 1, 2),
        ]:
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["wound_dark"],
                                      _NS_zulkhaven._alpha(wound_alpha * pulse)),
                                     (wx, wy), wr)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_dark"],
                                      _NS_zulkhaven._alpha(200 * pulse)),
                                     (wx, wy), max(1, wr - 1))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                             (wx, wy, 1, 1))
        # Bloody streaks/dripping down
        for streak in [
            [(cx - 8, cy - 3), (cx - 8, cy + 4)],
            [(cx + 6, cy - 1), (cx + 6, cy + 8)],
            [(cx - 4, cy + 5), (cx - 4, cy + 12)],
        ]:
            pygame.draw.line(surface,
                             (*_NS_zulkhaven.PALETTE["blood_dark"],
                              _NS_zulkhaven._alpha(220 * pulse)),
                             streak[0], streak[1], 1)
            pygame.draw.line(surface,
                             (*_NS_zulkhaven.PALETTE["blood_mid"],
                              _NS_zulkhaven._alpha(180 * pulse)),
                             streak[0], streak[1], 1)
        # Small skin scars
        for scar in [
            [(cx - 10, cy + 8), (cx - 6, cy + 8)],
            [(cx + 4, cy - 2), (cx + 8, cy)],
        ]:
            pygame.draw.line(surface, _NS_zulkhaven.PALETTE["flesh_darkest"],
                             scar[0], scar[1], 1)
    def _draw_front_arms(surface, cx, cy, facing, phase, swing, action,
                          attack_progress, enraged):
        """Front arms with big bloody claws + shackles."""
        for side, x_base in [(-1, -8), (1, 12)]:
            base_x = cx + x_base
            base_y = cy + 2
            if action == "attack":
                hand_x = base_x + facing * (10 + swing)
                hand_y = base_y + 10 - swing // 2
            else:
                # Idle/walk: arms reach forward (hunched creature)
                hand_x = base_x + facing * int(6 + math.sin(phase * 0.7 + side) * 2)
                hand_y = base_y + 14
            # Elbow bend
            mx = int((base_x + hand_x) / 2) + side * 2
            my = int((base_y + hand_y) / 2) + 2
            # Upper arm (thick with flesh)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                                   (base_x + 2, base_y + 2), (mx + 2, my + 2), 7)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_darkest"],
                                   (base_x, base_y), (mx, my), 6)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_dark"],
                                   (base_x, base_y), (mx, my), 4)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_mid"],
                                   (base_x - 1, base_y), (mx - 1, my), 2)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_light"],
                                   (base_x - 2, base_y), (mx - 2, my), 1)
            # Forearm
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                                   (mx + 2, my + 2),
                                   (hand_x + 2, hand_y + 2), 6)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_darkest"],
                                   (mx, my), (hand_x, hand_y), 5)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_dark"],
                                   (mx, my), (hand_x, hand_y), 3)
            _NS_zulkhaven._aaline(surface, _NS_zulkhaven.PALETTE["flesh_mid"],
                                   (mx - 1, my), (hand_x - 1, hand_y), 1)
            # SHACKLE on forearm (broken chain)
            _NS_zulkhaven._draw_shackle(surface, int((mx + hand_x) / 2),
                                         int((my + hand_y) / 2), facing, phase)
            # Claw hand
            _NS_zulkhaven._draw_bloody_claw_hand(surface, hand_x, hand_y, facing,
                                                  phase, side, action, enraged)
    def _draw_shackle(surface, sx, sy, facing, phase):
        """Broken metal shackle around wrist."""
        # Shackle ring
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                         (sx - 4, sy - 2, 8, 5))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_darkest"],
                         (sx - 4, sy - 2, 8, 4))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_dark"],
                         (sx - 3, sy - 2, 6, 3))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_mid"],
                         (sx - 3, sy - 1, 6, 1))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_light"],
                         (sx - 2, sy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_shine"],
                         (sx - 2, sy - 1, 1, 1))
        # Broken chain link (2-3 links hanging)
        sway = math.sin(phase * 0.6) * 2
        for i in range(3):
            link_y = sy + 3 + i * 3
            link_x = sx + int(sway * (i + 1) / 3)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_darkest"],
                             (link_x - 1, link_y, 3, 2))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_dark"],
                             (link_x, link_y, 2, 2))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["metal_light"],
                             (link_x, link_y, 1, 1))
    def _draw_bloody_claw_hand(surface, hx, hy, facing, phase, side, action,
                                 enraged):
        """Big claw hand covered in blood."""
        # Paw base
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"], [
            (hx - 4, hy - 2),
            (hx + 5, hy - 2),
            (hx + 5, hy + 5),
            (hx - 4, hy + 5),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_darkest"], [
            (hx - 4, hy - 3),
            (hx + 5, hy - 3),
            (hx + 5, hy + 4),
            (hx - 4, hy + 4),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_dark"], [
            (hx - 3, hy - 2),
            (hx + 4, hy - 2),
            (hx + 4, hy + 3),
            (hx - 3, hy + 3),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_mid"], [
            (hx - 2, hy - 1),
            (hx + 3, hy - 1),
            (hx + 3, hy + 2),
            (hx - 2, hy + 2),
        ])
        # Blood covering hand
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        blood_alpha = 220 if enraged else 180
        pygame.draw.rect(surface,
                         (*_NS_zulkhaven.PALETTE["blood_dark"],
                          _NS_zulkhaven._alpha(blood_alpha * pulse)),
                         (hx - 2, hy, 5, 3))
        # Big sharp claws (5 claws forward with blood)
        for i, cx_off in enumerate((-3, -1, 1, 3, 5)):
            claw_size = 7 if i in (1, 2, 3) else 6
            claw_x = hx + cx_off + facing * 2
            claw_base_y = hy + 3
            claw_tip_x = claw_x + facing * claw_size
            claw_tip_y = claw_base_y - 1
            # Shadow
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"], [
                (claw_x + 1, claw_base_y - 1),
                (claw_x + 1, claw_base_y + 2),
                (claw_tip_x + 1, claw_tip_y + 1),
            ])
            # Claw
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["fang_dark"], [
                (claw_x, claw_base_y - 1),
                (claw_x, claw_base_y + 2),
                (claw_tip_x, claw_tip_y),
            ])
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["fang_mid"], [
                (claw_x + facing, claw_base_y - 1),
                (claw_x + facing, claw_base_y + 1),
                (claw_tip_x - facing, claw_tip_y),
            ])
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["fang_light"], [
                (claw_x + facing * 2, claw_base_y),
                (claw_x + facing * 2, claw_base_y + 1),
                (claw_tip_x - facing * 2, claw_tip_y),
            ])
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["fang_shine"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            # BLOOD on claw tip
            for r in range(3, 0, -1):
                alpha = _NS_zulkhaven._alpha(200 * (3 - r) / 3 * pulse)
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                         (claw_tip_x, claw_tip_y), r)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_light"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            # Blood dripping down
            if i in (1, 3):
                drip_y = claw_tip_y + 3
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_dark"],
                                 (claw_tip_x, drip_y, 1, 3))
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                                 (claw_tip_x, drip_y, 1, 2))
    def _draw_zul_head(surface, cx, cy, facing, phase, mouth_open, action,
                        enraged):
        """Huge head with GIANT MAW (mouth wider than face)."""
        # Head shape - very wide at mouth
        head_shape = [
            (cx - 12 * facing, cy + 8),   # jaw back
            (cx - 13 * facing, cy),
            (cx - 10 * facing, cy - 8),
            (cx - 4 * facing, cy - 12),
            (cx + 3 * facing, cy - 13),   # top
            (cx + 10 * facing, cy - 11),
            (cx + 16 * facing, cy - 6),
            (cx + 20 * facing, cy - 1),
            (cx + 22 * facing, cy + 5),   # snout tip
            (cx + 20 * facing, cy + 10),
            (cx + 12 * facing, cy + 12),
            (cx + 2 * facing, cy + 12),   # bottom jaw
            (cx - 8 * facing, cy + 11),
        ]
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_shape])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_darkest"], head_shape)
        # Upper head flesh
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_dark"], [
            (cx - 12 * facing, cy + 6),
            (cx - 12 * facing, cy),
            (cx - 8 * facing, cy - 7),
            (cx + 2 * facing, cy - 11),
            (cx + 9 * facing, cy - 10),
            (cx + 15 * facing, cy - 5),
            (cx + 19 * facing, cy),
            (cx + 20 * facing, cy + 4),
            (cx + 15 * facing, cy + 3),
            (cx + 3 * facing, cy),
            (cx - 8 * facing, cy + 1),
        ])
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_mid"], [
            (cx - 9 * facing, cy - 1),
            (cx - 5 * facing, cy - 8),
            (cx + 2 * facing, cy - 9),
            (cx + 9 * facing, cy - 7),
            (cx + 14 * facing, cy - 3),
            (cx + 16 * facing, cy),
            (cx + 3 * facing, cy - 2),
        ])
        # Highlights
        _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["flesh_light"], [
            (cx - 2 * facing, cy - 6),
            (cx + 5 * facing, cy - 8),
            (cx + 10 * facing, cy - 5),
            (cx + 6 * facing, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["flesh_shine"],
                         (cx + 5 * facing, cy - 7, 1, 1))
        # Wounds/sores on head
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for wx, wy, wr in [
            (cx - 4 * facing, cy - 8, 2),
            (cx + 6 * facing, cy - 8, 2),
            (cx - 8 * facing, cy - 3, 1),
        ]:
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["wound_dark"],
                                      _NS_zulkhaven._alpha(200 * pulse)),
                                     (wx, wy), wr)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                             (wx, wy, 1, 1))
        # Tiny red eyes (very small, hidden in wrinkles)
        _NS_zulkhaven._draw_tiny_eyes(surface, cx, cy - 6, facing, phase, enraged)
        # Nostril slits (2 small)
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                         (cx + 15 * facing, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                         (cx + 18 * facing, cy - 1, 1, 1))
        # GIANT MAW
        _NS_zulkhaven._draw_giant_maw(surface, cx, cy, facing, phase, mouth_open,
                                       action)
    def _draw_tiny_eyes(surface, cx, cy, facing, phase, enraged):
        """Tiny red glowing eyes (hidden in wrinkles)."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        if enraged:
            pulse = min(1.0, pulse + 0.3)
        for eye_x_off in (-2, 3):
            ex = cx + int(eye_x_off * facing)
            ey = cy
            # Wrinkle around eye
            pygame.draw.line(surface, _NS_zulkhaven.PALETTE["flesh_darkest"],
                             (ex - 2, ey - 1), (ex + 2, ey - 1), 1)
            # Tiny socket
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["eye_socket"],
                             (ex - 1, ey, 2, 2))
            # Small glow
            for r in range(2, 0, -1):
                alpha = _NS_zulkhaven._alpha(220 * pulse * r / 2)
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["eye_light"], alpha),
                                         (ex, ey), r)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                             (ex, ey, 1, 1))
    def _draw_giant_maw(surface, cx, cy, facing, phase, mouth_open, action):
        """MASSIVE mouth with tons of teeth."""
        mouth_y = cy + 3
        mouth_x_start = cx + 1 * facing
        mouth_x_end = cx + 20 * facing
        if mouth_open > 0:
            # Big open maw cavity
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end - 2, mouth_y + int(mouth_open)),
                (mouth_x_start + 2, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["blood_darkest"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing * 2, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing * 2, mouth_y + int(mouth_open * 0.7) - 1),
            ])
            # BLOODY inside (dark red glow)
            glow_cx = cx + 11 * facing
            glow_cy = mouth_y + int(mouth_open * 0.5)
            glow_r = int(3 + mouth_open * 0.4)
            for r in range(glow_r + 3, 0, -1):
                alpha = _NS_zulkhaven._alpha(200 * (glow_r + 3 - r) / (glow_r + 3))
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                         (glow_cx, glow_cy), r)
            _NS_zulkhaven._aacircle(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                                     (glow_cx, glow_cy), max(1, glow_r - 1))
            # UPPER FANGS (many rows of teeth)
            for i, x_off in enumerate((3, 6, 9, 12, 15, 18)):
                fang_x = cx + int(x_off * facing)
                fang_size = 5 if i in (1, 2, 3, 4) else 4
                fang_tip_y = mouth_y + int(mouth_open * 0.7) + fang_size
                pygame.draw.line(surface, _NS_zulkhaven.PALETTE["fang_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 3)
                pygame.draw.line(surface, _NS_zulkhaven.PALETTE["fang_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_zulkhaven.PALETTE["fang_light"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["fang_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
                # Blood on teeth
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_dark"],
                                 (fang_x, fang_tip_y - 1, 1, 1))
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                                 (fang_x, fang_tip_y - 1, 1, 1))
            # LOWER FANGS
            for i, x_off in enumerate((4, 7, 10, 13, 16)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_size = 4 if i in (1, 2, 3) else 3
                fang_tip_y = fang_top_y - fang_size
                pygame.draw.line(surface, _NS_zulkhaven.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_zulkhaven.PALETTE["fang_mid"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
            # BLOOD/DROOL dripping out of mouth
            if mouth_open > 5:
                for x_off in (5, 10, 15):
                    drip_x = cx + int(x_off * facing)
                    drip_y = mouth_y + int(mouth_open) + 3
                    pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_darkest"],
                                     (drip_x, drip_y, 1, 4))
                    pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_dark"],
                                     (drip_x, drip_y, 1, 3))
                    pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                                     (drip_x, drip_y, 1, 1))
        else:
            # Closed - still visible fangs
            pygame.draw.line(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            for x_off in (5, 9, 13, 17):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["fang_mid"],
                                 (fang_x, mouth_y + 1, 1, 3))
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["fang_light"],
                                 (fang_x, mouth_y + 3, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 1, 1, 180), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_blood_aura(surface, x, y, phase, enraged=False):
        """Blood aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.5 if enraged else 1.0
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_zulkhaven._alpha((90 - radius) * 1.2 * pulse * strength)
            if alpha > 0:
                _NS_zulkhaven._aacircle(aura,
                                         (*_NS_zulkhaven.PALETTE["blood_darkest"],
                                          alpha),
                                         (110, 90), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_zulkhaven._alpha((50 - radius) * 1.4 * pulse * strength)
            if alpha > 0:
                _NS_zulkhaven._aacircle(aura,
                                         (*_NS_zulkhaven.PALETTE["blood_dark"],
                                          alpha),
                                         (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Blood particles floating
        num = 14 if enraged else 10
        for i in range(num):
            angle = phase * 0.3 + i * math.pi / (num / 2)
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.4)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_dark"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                             (sx, sy, 1, 1))
    def _draw_blood_drips(surface, x, y, phase):
        """Blood drips falling from body constantly."""
        for i in range(8):
            t = (phase * 0.5 + i * 0.125) % 1.0
            drip_x = x - 20 + i * 5 + int(math.sin(phase + i) * 3)
            drip_y_start = y + 15
            drip_y = drip_y_start + int(t * 35)
            alpha = _NS_zulkhaven._alpha(200 * (1 - t))
            pygame.draw.rect(surface,
                             (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                             (drip_x, drip_y, 1, 3))
            pygame.draw.rect(surface,
                             (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                             (drip_x, drip_y, 1, 2))
            pygame.draw.rect(surface,
                             (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                             (drip_x, drip_y, 1, 1))
        # Blood puddle at ground
        pygame.draw.ellipse(surface, _NS_zulkhaven.PALETTE["blood_darkest"],
                            (x - 30, y + 48, 60, 8))
        pygame.draw.ellipse(surface, _NS_zulkhaven.PALETTE["blood_dark"],
                            (x - 25, y + 49, 50, 6))
        pygame.draw.ellipse(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                            (x - 15, y + 50, 30, 3))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zulkhaven.PALETTE["blood_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_zulkhaven.PALETTE["flesh_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_zulkhaven.PALETTE["blood_dark"], 220),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_zulkhaven.PALETTE["blood_mid"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zulkhaven.PALETTE["blood_hot"],
                                        _NS_zulkhaven._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - Claw slash + Bite (MELEE)
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic melee: 5 bloody claw slashes arc + bite impact."""
        progress = getattr(boss, "_zul_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist > 80:
            tx = x + int(dx / dist * 60)
            ty = y + int(dy / dist * 60)
        # PHASE 1: Wind-up
        if progress < 0.3:
            t = progress / 0.3
            mouth_x = x + facing * 22
            mouth_y = y - 4
            for r in range(int(3 + t * 3), 0, -1):
                alpha = _NS_zulkhaven._alpha(150 * t * r / 6)
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                         (mouth_x, mouth_y), r)
        # PHASE 2: SLASH
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            slash_cx = x + facing * 25
            slash_cy = y - 2
            arc_radius = 30
            start_angle = math.radians(-70) if facing == 1 \
                          else math.radians(-110)
            end_angle = math.radians(70) if facing == 1 \
                        else math.radians(250)
            current_angle = start_angle + (end_angle - start_angle) * t
            # 5 parallel claw slashes
            for line_i, offset in enumerate((-10, -5, 0, 5, 10)):
                num_pts = 10
                prev_pt = None
                for step in range(num_pts + 1):
                    step_t = step / num_pts
                    a = start_angle + (current_angle - start_angle) * step_t
                    r = arc_radius + offset
                    px = slash_cx + int(math.cos(a) * r) * facing
                    py = slash_cy + int(math.sin(a) * r)
                    if prev_pt is not None:
                        alpha = _NS_zulkhaven._alpha(230 * step_t * (1 - t * 0.3))
                        pygame.draw.line(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_darkest"],
                                          alpha),
                                         prev_pt, (px, py), 4)
                        pygame.draw.line(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_dark"],
                                          alpha),
                                         prev_pt, (px, py), 3)
                        pygame.draw.line(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_mid"],
                                          alpha),
                                         prev_pt, (px, py), 2)
                        pygame.draw.line(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_light"],
                                          alpha),
                                         prev_pt, (px, py), 1)
                    prev_pt = (px, py)
                # Bright tip
                tip_a = current_angle
                tip_r = arc_radius + offset
                tip_x = slash_cx + int(math.cos(tip_a) * tip_r) * facing
                tip_y = slash_cy + int(math.sin(tip_a) * tip_r)
                for r in range(4, 0, -1):
                    alpha = _NS_zulkhaven._alpha(240 * (4 - r) / 4)
                    _NS_zulkhaven._aacircle(surface,
                                             (*_NS_zulkhaven.PALETTE["blood_hot"],
                                              alpha),
                                             (tip_x, tip_y), r)
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                                 (tip_x, tip_y, 1, 1))
            # Blood droplets flying
            for i in range(10):
                spark_angle = start_angle + (current_angle - start_angle) \
                              * (0.3 + (i % 5) * 0.15)
                spark_r = arc_radius + math.sin(boss.pulse * 3 + i) * 8
                sx = slash_cx + int(math.cos(spark_angle) * spark_r) * facing
                sy = slash_cy + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_mid"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_light"],
                                 (sx, sy, 1, 1))
        # PHASE 3: IMPACT + BLOOD SPLASH
        else:
            t = (progress - 0.7) / 0.3
            impact_r = int(8 + t * 22)
            alpha = _NS_zulkhaven._alpha(240 * (1 - t))
            # Impact rings
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_darkest"], alpha),
                                     (tx, ty), impact_r + 2, 3)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                     (tx, ty), impact_r, 2)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                     (tx, ty), max(1, impact_r - 5), 1)
            # Core
            core_r = max(1, int(6 * (1 - t)))
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_hot"], alpha),
                                     (tx, ty), core_r + 2)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_shine"], alpha),
                                     (tx, ty), max(1, core_r))
            # 5 claw scratches
            scratch_len = int(15 * (1 - t * 0.3))
            for i, y_off in enumerate((-10, -5, 0, 5, 10)):
                start_sx = tx - scratch_len // 2 * facing
                end_sx = tx + scratch_len // 2 * facing
                sy_pos = ty + y_off + int(math.sin(i) * 2)
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_darkest"], alpha),
                                 (start_sx, sy_pos - 1),
                                 (end_sx, sy_pos - 1), 2)
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                 (start_sx, sy_pos),
                                 (end_sx, sy_pos), 1)
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                                 (start_sx + 2, sy_pos),
                                 (end_sx - 2, sy_pos), 1)
            # Blood splatter droplets
            for i in range(14):
                angle_p = i * math.pi / 7
                pr = int(impact_r * (0.7 + (i % 3) * 0.15))
                px = tx + int(math.cos(angle_p) * pr)
                py = ty + int(math.sin(angle_p) * pr * 0.8)
                pygame.draw.rect(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                 (px, py, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: Q - RAGE (self buff - red aura + speed lines)
    # ============================================================
    def _draw_rage_ground(surface, boss, x, y, timer, phase):
        """Ground pulsing red rings."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(38 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_zulkhaven._alpha(220 - i * 50)
            pygame.draw.ellipse(surface,
                                (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                                (x - r + 6, y + 40 - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_rage_fx(surface, boss, x, y, timer, phase):
        """Red flames rising + speed lines (edges only)."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Red flames rising around boss (edge only, radius >= 32)
        for i in range(10):
            angle = phase * 0.5 + i * math.pi / 5
            base_r = 34
            flame_x = x + int(math.cos(angle) * base_r)
            flame_y_base = y + int(math.sin(angle) * base_r * 0.5)
            flame_t = (phase * 0.6 + i * 0.15) % 1.0
            flame_y = flame_y_base - int(flame_t * 25)
            alpha = _NS_zulkhaven._alpha(230 * (1 - flame_t))
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                     (flame_x, flame_y), 3)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                     (flame_x, flame_y - 1), 2)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                                     (flame_x, flame_y - 2), 1)
            pygame.draw.rect(surface, (*_NS_zulkhaven.PALETTE["blood_hot"], alpha),
                             (flame_x, flame_y - 3, 1, 1))
            pygame.draw.rect(surface, (*_NS_zulkhaven.PALETTE["blood_shine"], alpha),
                             (flame_x, flame_y - 4, 1, 1))
        # Rage aura ring (edge only)
        aura_pulse = math.sin(phase * 4) * 0.3 + 0.7
        for r in range(38, 32, -1):
            alpha = _NS_zulkhaven._alpha(180 * aura_pulse * (38 - r) / 6)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                                     (x, y), r, 1)
        # Speed particles
        for i in range(12):
            angle = phase * 2 + i * math.pi / 6
            r_p = 40 + int(math.sin(phase * 3 + i) * 6)
            sx = x + int(math.cos(angle) * r_p)
            sy = y + int(math.sin(angle) * r_p * 0.5)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: W - FEED (bite + heal effect)
    # ============================================================
    def _draw_feed_fx(surface, boss, x, y, timer, phase):
        """Bite forward at target + green heal particles rising to boss."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y
        # Bite forward line
        if progress < 0.5:
            t = progress / 0.5
            bite_end_x = x + facing * int(t * 60)
            # Bite trail
            for i, y_off in enumerate((-8, 0, 8)):
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_darkest"], 220),
                                 (x + facing * 22, y - 4 + y_off),
                                 (bite_end_x, ty + y_off), 4)
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_dark"], 220),
                                 (x + facing * 22, y - 4 + y_off),
                                 (bite_end_x, ty + y_off), 3)
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_mid"], 220),
                                 (x + facing * 22, y - 4 + y_off),
                                 (bite_end_x, ty + y_off), 2)
                pygame.draw.line(surface,
                                 (*_NS_zulkhaven.PALETTE["blood_light"], 220),
                                 (x + facing * 22, y - 4 + y_off),
                                 (bite_end_x, ty + y_off), 1)
            # Bite impact tip
            if t > 0.5:
                for r in range(8, 0, -1):
                    alpha = _NS_zulkhaven._alpha(240 * (8 - r) / 8)
                    _NS_zulkhaven._aacircle(surface,
                                             (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                             (bite_end_x, ty), r)
        # Green heal particles rising from target back to boss
        if progress > 0.4:
            t = (progress - 0.4) / 0.6
            for i in range(10):
                particle_t = (t + i * 0.1) % 1.0
                px = int(tx + (x - tx) * particle_t)
                py = int(ty + (y - ty) * particle_t
                         - math.sin(particle_t * math.pi) * 20)
                alpha = _NS_zulkhaven._alpha(240 * (1 - particle_t * 0.5))
                # Green heal particle
                _NS_zulkhaven._aacircle(surface,
                                         (30, 130, 40, alpha),
                                         (px, py), 3)
                _NS_zulkhaven._aacircle(surface,
                                         (60, 200, 60, alpha),
                                         (px, py), 2)
                pygame.draw.rect(surface, (140, 255, 140, alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (220, 255, 220, alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: E - OPEN WOUNDS (bleed projectile)
    # ============================================================
    def _draw_openwounds_fx(surface, boss, x, y, timer, phase):
        """Blood spikes shooting to target - ranged bleeding."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 100
            ty = y
        start_x = x + facing * 22
        start_y = y - 2
        # Phase 1: Charge
        if progress < 0.3:
            t = progress / 0.3
            for r in range(int(3 + t * 5), 0, -1):
                alpha = _NS_zulkhaven._alpha(200 * t * r / 8)
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                         (start_x, start_y), r)
            _NS_zulkhaven._aacircle(surface, _NS_zulkhaven.PALETTE["blood_hot"],
                                     (start_x, start_y), max(1, int(3 * t)))
        # Phase 2: Multiple spikes shoot forward
        else:
            t = (progress - 0.3) / 0.7
            # 5-7 blood spikes at slight angles
            num_spikes = 7
            for spike_i in range(num_spikes):
                spike_delay = spike_i * 0.05
                spike_t = max(0.0, min(1.0, (t - spike_delay) / (1 - spike_delay)))
                if spike_t <= 0:
                    continue
                # Slight angle variation
                angle_offset = (spike_i - num_spikes // 2) * 0.05
                target_offset_y = (spike_i - num_spikes // 2) * 5
                bx = int(start_x + (tx - start_x) * spike_t)
                by = int(start_y + (ty + target_offset_y - start_y) * spike_t)
                # Spike direction
                angle = math.atan2(ty + target_offset_y - start_y, tx - start_x)
                # Draw elongated spike (line-like)
                spike_len = 12
                tip_x = bx + int(math.cos(angle) * spike_len / 2)
                tip_y = by + int(math.sin(angle) * spike_len / 2)
                back_x = bx - int(math.cos(angle) * spike_len / 2)
                back_y = by - int(math.sin(angle) * spike_len / 2)
                # Perpendicular
                perp_angle = angle + math.pi / 2
                perp_x = math.cos(perp_angle) * 2
                perp_y = math.sin(perp_angle) * 2
                # Trail
                for i in range(4):
                    trail_t = max(0.0, spike_t - i * 0.06)
                    tpx = int(start_x + (tx - start_x) * trail_t)
                    tpy = int(start_y + (ty + target_offset_y - start_y) * trail_t)
                    alpha = _NS_zulkhaven._alpha(200 - i * 40)
                    _NS_zulkhaven._aacircle(surface,
                                             (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                             (tpx, tpy), max(1, 4 - i))
                    _NS_zulkhaven._aacircle(surface,
                                             (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                             (tpx, tpy), max(1, 3 - i))
                # Spike shape
                spike_pts = [
                    (tip_x, tip_y),
                    (int(back_x + perp_x), int(back_y + perp_y)),
                    (int(back_x - perp_x), int(back_y - perp_y)),
                ]
                _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["shadow_deep"],
                                     [(p[0] + 1, p[1] + 1) for p in spike_pts])
                _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["blood_darkest"],
                                     spike_pts)
                _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["blood_dark"], [
                    (tip_x, tip_y),
                    (int(back_x + perp_x * 0.7), int(back_y + perp_y * 0.7)),
                    (int(back_x - perp_x * 0.7), int(back_y - perp_y * 0.7)),
                ])
                _NS_zulkhaven._poly(surface, _NS_zulkhaven.PALETTE["blood_mid"], [
                    (tip_x, tip_y),
                    (int(back_x + perp_x * 0.4), int(back_y + perp_y * 0.4)),
                    (int(back_x - perp_x * 0.4), int(back_y - perp_y * 0.4)),
                ])
                # Bright tip
                _NS_zulkhaven._aacircle(surface, _NS_zulkhaven.PALETTE["blood_hot"],
                                         (tip_x, tip_y), 2)
                pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                                 (tip_x, tip_y, 1, 1))
                # Impact
                if spike_t > 0.9:
                    st = (spike_t - 0.9) / 0.1
                    impact_r = int(4 + st * 8)
                    alpha = _NS_zulkhaven._alpha(240 * (1 - st))
                    impact_ty = ty + target_offset_y
                    _NS_zulkhaven._aacircle(surface,
                                             (*_NS_zulkhaven.PALETTE["blood_dark"],
                                              alpha),
                                             (tx, impact_ty), impact_r, 2)
                    _NS_zulkhaven._aacircle(surface,
                                             (*_NS_zulkhaven.PALETTE["blood_mid"],
                                              alpha),
                                             (tx, impact_ty), max(1, impact_r - 2))
                    pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                                     (tx, impact_ty, 1, 1))
    # ============================================================
    # SKILL: R - INFEST (dark self-buff with tentacles)
    # ============================================================
    def _draw_infest_ground(surface, boss, x, y, timer, phase):
        """Dark corrupt ground pattern."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 + math.sin(phase * 2) * 5)
        alpha_base = _NS_zulkhaven._alpha(200)
        pygame.draw.ellipse(surface,
                            (*_NS_zulkhaven.PALETTE["blood_darkest"], alpha_base),
                            (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_zulkhaven.PALETTE["blood_dark"], alpha_base),
                            (x - r + 3, y + 40 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface,
                            (*_NS_zulkhaven.PALETTE["blood_mid"], 160),
                            (x - r + 8, y + 40 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8))
        # Runes around
        for i in range(10):
            angle = phase * 0.5 + i * math.pi / 5
            rx = x + int(math.cos(angle) * r * 0.8)
            ry = y + 42 + int(math.sin(angle) * r * 0.8 * 0.4)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_hot"],
                             (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                             (rx, ry, 1, 1))
    def _draw_infest_fx(surface, boss, x, y, timer, phase):
        """Blood tentacles/wisps rising around boss (edges only)."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Curling tentacle wisps from ground around boss
        for i in range(8):
            base_angle = i * math.pi / 4 + phase * 0.3
            base_r = 40
            bx = x + int(math.cos(base_angle) * base_r)
            by = y + 42 + int(math.sin(base_angle) * base_r * 0.3)
            # Tentacle curls upward
            for step in range(8):
                t = step / 8
                curl = math.sin(t * math.pi * 2 + phase * 3 + i) * 4
                sx = bx + int(curl)
                sy = by - int(t * 25)
                alpha = _NS_zulkhaven._alpha(220 * (1 - t))
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_darkest"],
                                          alpha),
                                         (sx, sy), max(1, 4 - step // 2))
                _NS_zulkhaven._aacircle(surface,
                                         (*_NS_zulkhaven.PALETTE["blood_dark"],
                                          alpha),
                                         (sx, sy), max(1, 3 - step // 2))
                if step < 3:
                    pygame.draw.rect(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_mid"], alpha),
                                     (sx, sy, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_light"], alpha),
                                     (sx, sy, 1, 1))
        # Dark aura ring
        aura_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(42, 36, -1):
            alpha = _NS_zulkhaven._alpha(200 * aura_pulse * (42 - r) / 6)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_darkest"], alpha),
                                     (x, y), r, 1)
        for r in range(38, 33, -1):
            alpha = _NS_zulkhaven._alpha(150 * aura_pulse * (38 - r) / 5)
            _NS_zulkhaven._aacircle(surface,
                                     (*_NS_zulkhaven.PALETTE["blood_dark"], alpha),
                                     (x, y), r, 1)
        # Floating blood orbs
        for i in range(6):
            angle = phase * 0.7 + i * math.pi / 3
            orb_r = 45 + int(math.sin(phase * 2 + i) * 5)
            ox = x + int(math.cos(angle) * orb_r)
            oy = y + int(math.sin(angle) * orb_r * 0.4)
            _NS_zulkhaven._aacircle(surface,
                                     _NS_zulkhaven.PALETTE["blood_dark"],
                                     (ox, oy), 3)
            _NS_zulkhaven._aacircle(surface,
                                     _NS_zulkhaven.PALETTE["blood_mid"],
                                     (ox, oy), 2)
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_hot"],
                             (ox, oy, 1, 1))
            pygame.draw.rect(surface, _NS_zulkhaven.PALETTE["blood_shine"],
                             (ox, oy, 1, 1))



# ====================================================================
# THALRYNDEL (TEMPEST WEAVER) - TRUE BOSS
# ====================================================================

class _NS_thalryndel:
    """Namespace thalryndel - Tempest Weaver boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale blue elemental)
        "skin_darkest": (15, 30, 55),
        "skin_dark": (45, 85, 130),
        "skin_mid": (105, 165, 210),
        "skin_light": (170, 220, 245),
        "skin_shine": (220, 245, 255),
        # Beard/hair (blue elemental)
        "hair_darkest": (10, 25, 60),
        "hair_dark": (35, 75, 140),
        "hair_mid": (85, 145, 220),
        "hair_light": (160, 210, 255),
        "hair_shine": (220, 240, 255),
        # Robe dark blue (main)
        "robe_darkest": (5, 10, 30),
        "robe_dark": (15, 30, 75),
        "robe_mid": (40, 65, 130),
        "robe_light": (85, 120, 190),
        "robe_edge": (140, 175, 230),
        # Gold trim/accents
        "gold_darkest": (35, 25, 5),
        "gold_dark": (100, 70, 15),
        "gold_mid": (200, 155, 45),
        "gold_light": (245, 210, 100),
        "gold_shine": (255, 245, 180),
        # Hat (rice hat - dark blue with gold)
        "hat_dark": (15, 25, 55),
        "hat_mid": (35, 55, 100),
        "hat_light": (75, 105, 155),
        # Lightning blue (main effect color)
        "light_darkest": (5, 15, 50),
        "light_dark": (20, 60, 160),
        "light_mid": (60, 140, 240),
        "light_light": (140, 210, 255),
        "light_hot": (200, 240, 255),
        "light_shine": (240, 250, 255),
        # Yellow eyes
        "eye_socket": (5, 8, 15),
        "eye_glow": (255, 220, 100),
        "eye_bright": (255, 250, 200),
        # Red gem accents
        "gem_dark": (80, 15, 15),
        "gem_mid": (200, 40, 40),
        "gem_light": (255, 100, 100),
        "gem_shine": (255, 220, 200),
        # Storm cloud/aura
        "cloud_dark": (10, 20, 50),
        "cloud_mid": (35, 60, 120),
        "cloud_light": (95, 145, 210),
        "shadow": (0, 0, 0),
        "shadow_deep": (1, 3, 8),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thalryndel._clamp(color)
        if _NS_thalryndel.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_thalryndel._clamp(color)
        if _NS_thalryndel.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_thalryndel._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    def _lightning_line(surface, color, start, end, alpha=255, segments=8,
                        offset=3):
        """Draw jagged lightning bolt line."""
        pts = [start]
        for i in range(1, segments):
            t = i / segments
            mid_x = start[0] + (end[0] - start[0]) * t
            mid_y = start[1] + (end[1] - start[1]) * t
            jitter_x = (math.sin(i * 7.3) * offset)
            jitter_y = (math.cos(i * 5.7) * offset)
            pts.append((int(mid_x + jitter_x), int(mid_y + jitter_y)))
        pts.append(end)
        for i in range(len(pts) - 1):
            pygame.draw.line(surface, (*color, alpha), pts[i], pts[i + 1], 1)
        return pts
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thalryndel(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_thalryndel._update_thal_attack_anim(boss)
        attacking = bool(getattr(boss, "_thal_attack_active", False))
        # FLOATING bob
        float_bob = math.sin(pulse * 0.7) * 5
        y_floating = y - 8 + int(float_bob)
        # ===== LAYER 1: BACKGROUND =====
        _NS_thalryndel._draw_storm_aura(surface, x, y_floating, pulse)
        _NS_thalryndel._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # ===== LAYER 2: SKILL GROUND FX =====
        if active_skill == "w":
            _NS_thalryndel._draw_vortex_ground(surface, boss, x, y, skill_timer, pulse)
        # ===== LAYER 3: LIGHTNING ambient =====
        _NS_thalryndel._draw_ambient_lightning(surface, x, y_floating, pulse)
        # ===== LAYER 4: SHADOW + BODY =====
        _NS_thalryndel._draw_floating_shadow(surface, x, y + 52, pulse)
        _NS_thalryndel._draw_thal_body(surface, x, y_floating, boss.direction,
                                        pulse, "attack" if attacking else "idle",
                                        getattr(boss, "_thal_attack_progress", 0.0),
                                        active_skill)
        # ===== LAYER 5: FOREGROUND FX =====
        if attacking and not active_skill:
            _NS_thalryndel._draw_basic_attack_fx(surface, boss, x, y_floating)
        if active_skill == "q":
            _NS_thalryndel._draw_staticremnant_fx(surface, boss, x, y_floating,
                                                    skill_timer, pulse)
        elif active_skill == "w":
            _NS_thalryndel._draw_vortex_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thalryndel._draw_overload_fx(surface, boss, x, y_floating,
                                               skill_timer, pulse)
        elif active_skill == "r":
            _NS_thalryndel._draw_balllightning_fx(surface, boss, x, y_floating,
                                                    skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_thal_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_thal_previous_timer", timer))
        active = bool(getattr(boss, "_thal_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._thal_attack_active = True
            boss._thal_attack_frame = 0
            active = True
        if active:
            boss._thal_attack_frame = int(getattr(boss, "_thal_attack_frame", 0)) + 1
            attack_duration = 30
            if boss._thal_attack_frame >= attack_duration:
                boss._thal_attack_active = False
                boss._thal_attack_frame = 0
                active = False
        boss._thal_previous_timer = timer
        if active:
            attack_duration = 30
            boss._thal_attack_progress = min(1.0,
                boss._thal_attack_frame / attack_duration)
        else:
            boss._thal_attack_progress = 0.0
    # ============================================================
    # BODY (Humanoid elemental with rice hat)
    # ============================================================
    def _draw_thal_body(surface, cx, cy, facing, phase, action,
                         attack_progress, active_skill):
        """Full body: robe, torso, arms with orbs, head with hat."""
        # Robe bottom (flowing)
        _NS_thalryndel._draw_robe_bottom(surface, cx, cy + 10, facing, phase)
        # Torso
        _NS_thalryndel._draw_torso(surface, cx, cy - 2, facing, phase)
        # Sash/belt with red gem
        _NS_thalryndel._draw_sash(surface, cx, cy + 6, facing, phase)
        # Arms with lightning orbs
        arm_raise = 0
        if action == "attack":
            arm_raise = int(math.sin(attack_progress * math.pi) * 4)
        _NS_thalryndel._draw_arms_with_orbs(surface, cx, cy - 2, facing, phase,
                                              arm_raise, action, attack_progress)
        # Beard (flowing blue)
        _NS_thalryndel._draw_beard(surface, cx, cy - 12, facing, phase)
        # Head with skin
        _NS_thalryndel._draw_head(surface, cx, cy - 18, facing, phase)
        # RICE HAT on top (drawn last so it's on top)
        _NS_thalryndel._draw_rice_hat(surface, cx, cy - 22, facing, phase)
    def _draw_robe_bottom(surface, cx, cy, facing, phase):
        """Flowing blue robe bottom."""
        sway = math.sin(phase * 0.6) * 2
        robe_pts = [
            (cx - 11, cy - 8),
            (cx + 11, cy - 8),
            (cx + 15 + int(sway), cy + 4),
            (cx + 13, cy + 12),
            (cx + 6, cy + 16),
            (cx - 6, cy + 16),
            (cx - 13, cy + 12),
            (cx - 15 - int(sway), cy + 4),
        ]
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                              [(px + 2, py + 3) for px, py in robe_pts])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_darkest"], robe_pts)
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_dark"], [
            (cx - 10, cy - 7),
            (cx + 10, cy - 7),
            (cx + 13, cy + 3),
            (cx + 11, cy + 11),
            (cx + 5, cy + 14),
            (cx - 5, cy + 14),
            (cx - 11, cy + 11),
            (cx - 13, cy + 3),
        ])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_mid"], [
            (cx - 7, cy - 5),
            (cx + 7, cy - 5),
            (cx + 10, cy + 3),
            (cx + 7, cy + 10),
            (cx - 7, cy + 10),
            (cx - 10, cy + 3),
        ])
        # Center highlight
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_light"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 3, cy + 10),
            (cx - 3, cy + 10),
        ])
        # Gold trim along bottom edge
        for i in range(-14, 15, 2):
            trim_x = cx + i
            trim_y = cy + 14 + int(math.sin(i * 0.3) * 1)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_dark"],
                             (trim_x, trim_y, 2, 2))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_mid"],
                             (trim_x, trim_y, 1, 1))
        # Gold vertical stripe center
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["gold_dark"],
                         (cx, cy - 6), (cx, cy + 14), 2)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["gold_mid"],
                         (cx, cy - 6), (cx, cy + 14), 1)
        # Gold diamond patterns
        for oy in (-2, 3, 8):
            pygame.draw.polygon(surface, _NS_thalryndel.PALETTE["gold_light"], [
                (cx, cy + oy - 2), (cx + 2, cy + oy),
                (cx, cy + oy + 2), (cx - 2, cy + oy),
            ])
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_shine"],
                             (cx, cy + oy, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Upper body torso in robe."""
        torso_pts = [
            (cx - 9, cy - 4),
            (cx - 10, cy),
            (cx - 8, cy + 6),
            (cx - 3, cy + 10),
            (cx + 3, cy + 10),
            (cx + 8, cy + 6),
            (cx + 10, cy),
            (cx + 9, cy - 4),
        ]
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in torso_pts])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_darkest"],
                              torso_pts)
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_dark"], [
            (cx - 8, cy - 3),
            (cx - 9, cy),
            (cx - 7, cy + 5),
            (cx - 2, cy + 9),
            (cx + 2, cy + 9),
            (cx + 7, cy + 5),
            (cx + 9, cy),
            (cx + 8, cy - 3),
        ])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["robe_mid"], [
            (cx - 6, cy - 2),
            (cx - 7, cy + 1),
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 7, cy + 1),
            (cx + 6, cy - 2),
        ])
        # V-neck opening (dark blue skin visible)
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["skin_darkest"], [
            (cx - 2, cy - 3),
            (cx, cy),
            (cx + 2, cy - 3),
        ])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["skin_dark"], [
            (cx - 1, cy - 3),
            (cx, cy - 1),
            (cx + 1, cy - 3),
        ])
        # Shoulder highlights
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["robe_edge"],
                         (cx - 8, cy - 2, 2, 2))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["robe_edge"],
                         (cx + 6, cy - 2, 2, 2))
        # Gold trim on collar
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["gold_dark"],
                         (cx - 4, cy - 3), (cx - 1, cy), 1)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["gold_dark"],
                         (cx + 1, cy), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["gold_mid"],
                         (cx - 4, cy - 3), (cx - 1, cy), 1)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["gold_mid"],
                         (cx + 1, cy), (cx + 4, cy - 3), 1)
    def _draw_sash(surface, cx, cy, facing, phase):
        """Belt/sash with red gem."""
        # Belt
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_dark"],
                         (cx - 9, cy - 1, 18, 4))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_mid"],
                         (cx - 8, cy - 1, 16, 3))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_light"],
                         (cx - 8, cy - 1, 16, 1))
        # Red gem in center
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_thalryndel._alpha(180 * (4 - r) / 4 * pulse)
            _NS_thalryndel._aacircle(surface,
                                      (*_NS_thalryndel.PALETTE["gem_mid"], alpha),
                                      (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gem_dark"],
                         (cx - 2, cy, 4, 3))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gem_mid"],
                         (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gem_light"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gem_shine"],
                         (cx, cy, 1, 1))
    def _draw_arms_with_orbs(surface, cx, cy, facing, phase, raise_amount,
                              action, attack_progress):
        """Both arms extended with lightning orbs."""
        # Arms extend to sides with orbs in each hand
        for side, x_base in [(-1, -9), (1, 9)]:
            shoulder_x = cx + x_base
            shoulder_y = cy - 1
            # Hand position (extended outward, slightly forward)
            if action == "attack":
                # Reach forward
                hand_x = shoulder_x + facing * (6 + int(attack_progress * 4))
                hand_y = shoulder_y + 6 - raise_amount
            else:
                # Idle: arms out to sides with orb
                hand_x = shoulder_x + side * 6 + int(math.sin(phase * 0.6 + side) * 1)
                hand_y = shoulder_y + 4 + int(math.sin(phase * 0.5) * 1)
            # Elbow
            elbow_x = int((shoulder_x + hand_x) / 2) + side
            elbow_y = int((shoulder_y + hand_y) / 2) + 1
            # Upper arm (in robe sleeve)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                                    (shoulder_x + 1, shoulder_y + 1),
                                    (elbow_x + 1, elbow_y + 1), 5)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["robe_darkest"],
                                    (shoulder_x, shoulder_y),
                                    (elbow_x, elbow_y), 4)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["robe_dark"],
                                    (shoulder_x, shoulder_y),
                                    (elbow_x, elbow_y), 3)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["robe_mid"],
                                    (shoulder_x - 1, shoulder_y),
                                    (elbow_x - 1, elbow_y), 1)
            # Forearm (thinner - sleeve tapered)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                                    (elbow_x + 1, elbow_y + 1),
                                    (hand_x + 1, hand_y + 1), 4)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["robe_darkest"],
                                    (elbow_x, elbow_y), (hand_x, hand_y), 3)
            _NS_thalryndel._aaline(surface, _NS_thalryndel.PALETTE["robe_dark"],
                                    (elbow_x, elbow_y), (hand_x, hand_y), 2)
            # Gold cuff at wrist
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_dark"],
                             (hand_x - 2, hand_y - 1, 4, 3))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_mid"],
                             (hand_x - 2, hand_y - 1, 4, 2))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_shine"],
                             (hand_x, hand_y - 1, 1, 1))
            # Skin hand
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["skin_darkest"],
                                      (hand_x, hand_y + 1), 2)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["skin_mid"],
                                      (hand_x, hand_y + 1), 1)
            # LIGHTNING ORB in hand (always visible)
            _NS_thalryndel._draw_lightning_orb(surface, hand_x, hand_y + 3,
                                                phase + side * math.pi,
                                                action, attack_progress)
    def _draw_lightning_orb(surface, ox, oy, phase, action, attack_progress):
        """Floating lightning orb in hand."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        size_mult = 1.0
        if action == "attack":
            size_mult = 1.0 + attack_progress * 0.4
        base_r = int(4 * size_mult)
        # Outer glow halo
        for r in range(base_r + 4, 0, -1):
            alpha = _NS_thalryndel._alpha(150 * (base_r + 4 - r)
                                          / (base_r + 4) * pulse)
            _NS_thalryndel._aacircle(surface,
                                      (*_NS_thalryndel.PALETTE["light_light"],
                                       alpha),
                                      (ox, oy), r)
        # Orb layers
        _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_darkest"],
                                  (ox, oy), base_r)
        _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_dark"],
                                  (ox, oy), max(1, base_r - 1))
        _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_mid"],
                                  (ox, oy), max(1, base_r - 2))
        _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_hot"],
                                  (ox, oy), max(1, base_r - 3))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                         (ox, oy, 1, 1))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"], (ox, oy, 1, 1))
        # Small lightning arcs around orb
        for i in range(3):
            arc_a = phase * 4 + i * math.pi * 2 / 3
            arc_r = base_r + 2
            ax = ox + int(math.cos(arc_a) * arc_r)
            ay = oy + int(math.sin(arc_a) * arc_r)
            pygame.draw.line(surface,
                             (*_NS_thalryndel.PALETTE["light_hot"],
                              _NS_thalryndel._alpha(220 * pulse)),
                             (ox, oy), (ax, ay), 1)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                             (ax, ay, 1, 1))
    def _draw_beard(surface, cx, cy, facing, phase):
        """Long flowing blue beard."""
        sway = math.sin(phase * 0.5) * 2
        # Beard shape (flowing down)
        beard_pts = [
            (cx - 4, cy),
            (cx - 5 + int(sway), cy + 4),
            (cx - 6, cy + 8),
            (cx - 4, cy + 12),
            (cx - 2, cy + 15),
            (cx + 2, cy + 15),
            (cx + 4, cy + 12),
            (cx + 6, cy + 8),
            (cx + 5 - int(sway), cy + 4),
            (cx + 4, cy),
        ]
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                              [(px + 1, py + 1) for px, py in beard_pts])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["hair_darkest"], beard_pts)
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["hair_dark"], [
            (cx - 3, cy + 1),
            (cx - 4 + int(sway * 0.5), cy + 5),
            (cx - 5, cy + 8),
            (cx - 3, cy + 11),
            (cx - 1, cy + 14),
            (cx + 1, cy + 14),
            (cx + 3, cy + 11),
            (cx + 5, cy + 8),
            (cx + 4 - int(sway * 0.5), cy + 5),
            (cx + 3, cy + 1),
        ])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["hair_mid"], [
            (cx - 2, cy + 2),
            (cx - 3, cy + 6),
            (cx - 2, cy + 10),
            (cx, cy + 13),
            (cx + 2, cy + 10),
            (cx + 3, cy + 6),
            (cx + 2, cy + 2),
        ])
        # Highlights (strands)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["hair_light"],
                         (cx - 1, cy + 3), (cx - 1, cy + 12), 1)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["hair_light"],
                         (cx + 1, cy + 3), (cx + 1, cy + 12), 1)
    def _draw_head(surface, cx, cy, facing, phase):
        """Blue skinned head with glowing yellow eyes."""
        # Head shape
        head_pts = [
            (cx - 5, cy - 2),
            (cx - 6, cy + 1),
            (cx - 5, cy + 5),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 5, cy + 5),
            (cx + 6, cy + 1),
            (cx + 5, cy - 2),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                              [(px + 1, py + 1) for px, py in head_pts])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["skin_darkest"], head_pts)
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["skin_dark"], [
            (cx - 4, cy - 1),
            (cx - 5, cy + 1),
            (cx - 4, cy + 4),
            (cx - 1, cy + 6),
            (cx + 1, cy + 6),
            (cx + 4, cy + 4),
            (cx + 5, cy + 1),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 3, cy + 4),
            (cx - 1, cy + 5),
            (cx + 1, cy + 5),
            (cx + 3, cy + 4),
            (cx + 4, cy + 2),
            (cx + 3, cy),
        ])
        # Cheek highlights
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["skin_light"],
                         (cx - 2, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["skin_light"],
                         (cx + 1, cy + 3, 1, 1))
        # Yellow glowing eyes
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            # Socket
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["eye_socket"],
                             (eye_x - 1, cy, 2, 2))
            # Glow halo
            for r in range(3, 0, -1):
                alpha = _NS_thalryndel._alpha(200 * (3 - r) / 3 * pulse)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["eye_glow"],
                                           alpha),
                                          (eye_x, cy + 1), r)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["eye_bright"],
                             (eye_x, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (eye_x, cy + 1, 1, 1))
        # Mustache lines (angry look)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["hair_darkest"],
                         (cx - 3, cy + 4), (cx - 1, cy + 5), 1)
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["hair_darkest"],
                         (cx + 3, cy + 4), (cx + 1, cy + 5), 1)
    def _draw_rice_hat(surface, cx, cy, facing, phase):
        """Conical rice hat with gold crown."""
        # Hat shape (wide cone)
        hat_pts = [
            (cx - 14, cy + 4),   # left brim
            (cx - 8, cy - 2),
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 8, cy - 2),
            (cx + 14, cy + 4),   # right brim
            (cx + 12, cy + 6),   # underside
            (cx - 12, cy + 6),
        ]
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["shadow_deep"],
                              [(px + 1, py + 2) for px, py in hat_pts])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["hat_dark"], hat_pts)
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["hat_mid"], [
            (cx - 13, cy + 3),
            (cx - 7, cy - 1),
            (cx - 1, cy - 5),
            (cx + 1, cy - 5),
            (cx + 7, cy - 1),
            (cx + 13, cy + 3),
            (cx + 11, cy + 5),
            (cx - 11, cy + 5),
        ])
        _NS_thalryndel._poly(surface, _NS_thalryndel.PALETTE["hat_light"], [
            (cx - 8, cy),
            (cx - 1, cy - 4),
            (cx + 1, cy - 4),
            (cx + 8, cy),
            (cx + 6, cy + 2),
            (cx - 6, cy + 2),
        ])
        # Center highlight strand
        pygame.draw.line(surface, _NS_thalryndel.PALETTE["hat_light"],
                         (cx, cy - 5), (cx, cy + 5), 1)
        # Radial lines on hat (bamboo weave)
        for angle_deg in (-70, -40, 0, 40, 70):
            angle = math.radians(angle_deg)
            end_x = cx + int(math.cos(angle - math.pi / 2) * 13)
            end_y = cy + 5 + int(math.sin(angle - math.pi / 2) * 10)
            pygame.draw.line(surface, _NS_thalryndel.PALETTE["hat_dark"],
                             (cx, cy - 4), (end_x, end_y), 1)
        # GOLD CROWN on top of hat
        crown_y = cy - 6
        # Base
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_darkest"],
                         (cx - 3, crown_y - 2, 6, 3))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_dark"],
                         (cx - 3, crown_y - 2, 6, 2))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_mid"],
                         (cx - 2, crown_y - 2, 4, 1))
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_light"],
                         (cx - 1, crown_y - 2, 2, 1))
        # Small spike on top
        pygame.draw.polygon(surface, _NS_thalryndel.PALETTE["gold_dark"], [
            (cx - 1, crown_y - 2),
            (cx, crown_y - 5),
            (cx + 1, crown_y - 2),
        ])
        pygame.draw.polygon(surface, _NS_thalryndel.PALETTE["gold_mid"], [
            (cx, crown_y - 2),
            (cx, crown_y - 4),
            (cx + 1, crown_y - 2),
        ])
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gold_shine"],
                         (cx, crown_y - 4, 1, 1))
        # Small red gem on crown
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(2, 0, -1):
            alpha = _NS_thalryndel._alpha(200 * (2 - r) / 2 * pulse)
            _NS_thalryndel._aacircle(surface,
                                      (*_NS_thalryndel.PALETTE["gem_mid"], alpha),
                                      (cx, crown_y - 1), r)
        pygame.draw.rect(surface, _NS_thalryndel.PALETTE["gem_light"],
                         (cx, crown_y - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((120, 28), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, int((12 - radius) * 14 * pulse))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 14 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 5, 15, int(160 * pulse)),
                            (8, 8, 104, 12))
        surface.blit(shadow, (x - 60, y - 14))
    def _draw_storm_aura(surface, x, y, phase):
        """Storm cloud aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_thalryndel._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_thalryndel._aacircle(aura,
                                          (*_NS_thalryndel.PALETTE["cloud_dark"],
                                           alpha),
                                          (110, 100), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_thalryndel._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thalryndel._aacircle(aura,
                                          (*_NS_thalryndel.PALETTE["cloud_mid"],
                                           alpha),
                                          (110, 100), radius)
        # Inner blue lightning glow
        for radius in range(30, 5, -3):
            alpha = _NS_thalryndel._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thalryndel._aacircle(aura,
                                          (*_NS_thalryndel.PALETTE["light_dark"],
                                           alpha),
                                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating lightning particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_hot"],
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (sx, sy, 1, 1))
    def _draw_ambient_lightning(surface, x, y, phase):
        """Random small lightning arcs around boss."""
        for i in range(3):
            if (int(phase * 4) + i) % 3 == 0:
                angle = (phase * 2 + i * 2.1) % (math.pi * 2)
                radius = 30
                start_x = x + int(math.cos(angle) * radius)
                start_y = y + int(math.sin(angle) * radius * 0.5)
                end_x = x + int(math.cos(angle) * (radius + 12))
                end_y = y + int(math.sin(angle) * (radius + 12) * 0.5)
                # Jagged lightning bolt
                num_seg = 4
                lightning_pts = [(start_x, start_y)]
                for s in range(1, num_seg):
                    t = s / num_seg
                    mx = start_x + (end_x - start_x) * t
                    my = start_y + (end_y - start_y) * t
                    mx += math.sin(phase * 8 + s) * 2
                    my += math.cos(phase * 8 + s) * 2
                    lightning_pts.append((int(mx), int(my)))
                lightning_pts.append((end_x, end_y))
                for j in range(len(lightning_pts) - 1):
                    pygame.draw.line(surface,
                                     _NS_thalryndel.PALETTE["light_hot"],
                                     lightning_pts[j], lightning_pts[j + 1], 1)
                    # FIX: proper rect format (x, y, w, h)
                    px, py = lightning_pts[j]
                    pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                                     (px, py, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thalryndel.PALETTE["cloud_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_thalryndel.PALETTE["robe_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_thalryndel.PALETTE["light_dark"], 220),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_thalryndel.PALETTE["light_mid"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_thalryndel.PALETTE["light_hot"],
                                        _NS_thalryndel._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - Lightning Bolt Projectile
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic ranged: lightning bolt projectile from hand to target."""
        progress = getattr(boss, "_thal_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        tx, ty = _NS_thalryndel._target_position(boss, x, y)
        # Launch from front hand
        start_x = x + facing * 15
        start_y = y - 2
        # PHASE 1: Charge (0-35%)
        if progress < 0.35:
            t = progress / 0.35
            charge_r = int(3 + t * 6)
            for r in range(charge_r + 4, 0, -1):
                alpha = _NS_thalryndel._alpha(200 * (charge_r + 4 - r)
                                              / (charge_r + 4) * t)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_dark"],
                                           alpha),
                                          (start_x, start_y), r)
            _NS_thalryndel._aacircle(surface,
                                      (*_NS_thalryndel.PALETTE["light_mid"],
                                       _NS_thalryndel._alpha(220 * t)),
                                      (start_x, start_y), max(1, charge_r - 2))
            _NS_thalryndel._aacircle(surface,
                                      (*_NS_thalryndel.PALETTE["light_hot"],
                                       _NS_thalryndel._alpha(240 * t)),
                                      (start_x, start_y), max(1, charge_r - 4))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                             (start_x, start_y, 1, 1))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (start_x, start_y, 1, 1))
            # Orbiting sparks
            for i in range(5):
                a = boss.pulse * 8 + i * math.pi * 2 / 5
                sr = charge_r + 3
                sx = start_x + int(math.cos(a) * sr)
                sy = start_y + int(math.sin(a) * sr)
                pygame.draw.rect(surface,
                                 (*_NS_thalryndel.PALETTE["light_hot"],
                                  _NS_thalryndel._alpha(240 * t)),
                                 (sx, sy, 1, 1))
        # PHASE 2: Projectile flight (35-95%)
        else:
            t = min(1.0, (progress - 0.35) / 0.6)
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # LIGHTNING BOLT connecting to bolt head (jagged line)
            num_segments = 12
            bolt_pts = [(start_x, start_y)]
            for i in range(1, num_segments):
                seg_t = i / num_segments
                mx = start_x + (bx - start_x) * seg_t
                my = start_y + (by - start_y) * seg_t
                # Jitter
                mx += math.sin(i * 3.7 + boss.pulse * 10) * 4
                my += math.cos(i * 5.3 + boss.pulse * 10) * 4
                bolt_pts.append((int(mx), int(my)))
            bolt_pts.append((bx, by))
            # Draw jagged bolt (multiple layers for glow)
            for width, color_key, alpha in [
                (4, "light_darkest", 120),
                (3, "light_dark", 160),
                (2, "light_mid", 220),
                (1, "light_hot", 255),
                (1, "white", 255),
            ]:
                for i in range(len(bolt_pts) - 1):
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE[color_key], alpha),
                                     bolt_pts[i], bolt_pts[i + 1], width)
            # BRIGHT BOLT HEAD
            for r in range(12, 3, -2):
                alpha = _NS_thalryndel._alpha(90 * (12 - r) / 12)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_light"],
                                           alpha),
                                          (bx, by), r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_darkest"],
                                      (bx, by), 8)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_dark"],
                                      (bx, by), 6)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_mid"],
                                      (bx, by), 4)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_hot"],
                                      (bx, by), 2)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (bx, by), 1)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (bx, by, 1, 1))
            # Sparks around bolt head
            for i in range(6):
                spark_a = boss.pulse * 5 + i * math.pi / 3
                sx = bx + int(math.cos(spark_a) * 8)
                sy = by + int(math.sin(spark_a) * 8)
                pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                                 (sx, sy, 1, 1))
            # IMPACT SPLASH at target
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(8 + st * 22)
                alpha = _NS_thalryndel._alpha(240 * (1 - st))
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_darkest"],
                                           alpha),
                                          (tx, ty), radius + 3, 3)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_dark"],
                                           alpha),
                                          (tx, ty), radius, 3)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_mid"],
                                           alpha),
                                          (tx, ty), max(1, radius - 5), 2)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_hot"],
                                           alpha),
                                          (tx, ty), max(1, radius - 12), 1)
                core_r = max(1, int(6 * (1 - st)))
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_shine"],
                                           alpha),
                                          (tx, ty), core_r)
                pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                                 (tx, ty, 1, 1))
                # Radial lightning arcs
                for i in range(8):
                    arc_a = i * math.pi / 4
                    end_x = tx + int(math.cos(arc_a) * radius)
                    end_y = ty + int(math.sin(arc_a) * radius * 0.8)
                    # Jagged arc
                    mid_x = tx + int(math.cos(arc_a) * radius / 2) \
                             + int(math.sin(arc_a * 3) * 3)
                    mid_y = ty + int(math.sin(arc_a) * radius * 0.4) \
                             + int(math.cos(arc_a * 3) * 3)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_hot"], alpha),
                                     (tx, ty), (mid_x, mid_y), 2)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_hot"], alpha),
                                     (mid_x, mid_y), (end_x, end_y), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_thalryndel.PALETTE["light_shine"], alpha),
                                     (end_x, end_y, 2, 2))
    # ============================================================
    # SKILL: Q - STATIC REMNANT (clone summon)
    # ============================================================
    def _draw_staticremnant_fx(surface, boss, x, y, timer, phase):
        """Blue clone forming beside boss."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Clone position (behind boss)
        clone_x = x - facing * 40
        clone_y = y
        # Phase 1: forming (0-40%)
        if progress < 0.4:
            t = progress / 0.4
            # Growing lightning ball
            for r in range(int(15 * t), 0, -2):
                alpha = _NS_thalryndel._alpha(200 * t * (15 * t - r) / max(1, 15 * t))
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_dark"],
                                           alpha),
                                          (clone_x, clone_y), r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_mid"],
                                      (clone_x, clone_y), max(1, int(10 * t)))
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (clone_x, clone_y), max(1, int(6 * t)))
            # Lightning arcs converging
            for i in range(6):
                a = phase * 4 + i * math.pi / 3
                start_x_arc = clone_x + int(math.cos(a) * (30 - int(t * 20)))
                start_y_arc = clone_y + int(math.sin(a) * (30 - int(t * 20)))
                pygame.draw.line(surface,
                                 (*_NS_thalryndel.PALETTE["light_hot"], 240),
                                 (start_x_arc, start_y_arc), (clone_x, clone_y), 1)
                pygame.draw.line(surface,
                                 (*_NS_thalryndel.PALETTE["white"], 240),
                                 (start_x_arc, start_y_arc), (clone_x, clone_y), 1)
        # Phase 2: full clone visible (40-100%)
        else:
            pulse = math.sin(phase * 4) * 0.3 + 0.7
            # Draw blue silhouette clone (simplified body)
            # Clone head glow
            for r in range(10, 0, -1):
                alpha = _NS_thalryndel._alpha(120 * (10 - r) / 10 * pulse)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_light"],
                                           alpha),
                                          (clone_x, clone_y), r)
            # Body silhouette
            body_pts = [
                (clone_x - 8, clone_y + 12),
                (clone_x - 10, clone_y + 4),
                (clone_x - 8, clone_y - 4),
                (clone_x - 4, clone_y - 10),
                (clone_x + 4, clone_y - 10),
                (clone_x + 8, clone_y - 4),
                (clone_x + 10, clone_y + 4),
                (clone_x + 8, clone_y + 12),
                (clone_x + 4, clone_y + 16),
                (clone_x - 4, clone_y + 16),
            ]
            # Silhouette shadow
            _NS_thalryndel._poly(surface,
                                  (*_NS_thalryndel.PALETTE["light_dark"], 200),
                                  body_pts)
            _NS_thalryndel._poly(surface,
                                  (*_NS_thalryndel.PALETTE["light_mid"], 200),
                                  [(px, py + 1) for px, py in body_pts[:6]])
            # Rice hat silhouette
            _NS_thalryndel._poly(surface,
                                  (*_NS_thalryndel.PALETTE["light_dark"], 200), [
                (clone_x - 10, clone_y - 6),
                (clone_x, clone_y - 12),
                (clone_x + 10, clone_y - 6),
                (clone_x + 8, clone_y - 4),
                (clone_x - 8, clone_y - 4),
            ])
            # Bright eyes on clone
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                             (clone_x - 2, clone_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                             (clone_x + 2, clone_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (clone_x - 2, clone_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (clone_x + 2, clone_y - 2, 1, 1))
            # Lightning arcs emanating
            for i in range(4):
                arc_a = phase * 3 + i * math.pi / 2
                arc_end_x = clone_x + int(math.cos(arc_a) * 20)
                arc_end_y = clone_y + int(math.sin(arc_a) * 20)
                _NS_thalryndel._lightning_line(surface,
                                                _NS_thalryndel.PALETTE["light_hot"],
                                                (clone_x, clone_y),
                                                (arc_end_x, arc_end_y),
                                                alpha=200, segments=5, offset=3)
            # Connect boss and clone with lightning
            _NS_thalryndel._lightning_line(surface,
                                            _NS_thalryndel.PALETTE["light_hot"],
                                            (x - facing * 5, y),
                                            (clone_x + facing * 8, clone_y),
                                            alpha=180, segments=8, offset=4)
    # ============================================================
    # SKILL: W - ELECTRIC VORTEX (AoE pull)
    # ============================================================
    def _draw_vortex_ground(surface, boss, x, y, timer, phase):
        """Vortex ground - spinning pattern under target."""
        tx, ty = _NS_thalryndel._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 2))
        if r > 5:
            alpha = _NS_thalryndel._alpha(200)
            pygame.draw.ellipse(surface,
                                (*_NS_thalryndel.PALETTE["light_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_thalryndel.PALETTE["light_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_vortex_fx(surface, boss, x, y, timer, phase):
        """Electric vortex swirling."""
        tx, ty = _NS_thalryndel._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 2))
        if r < 5:
            return
        # Spinning lightning rings
        num_arcs = 5
        for arc_i in range(num_arcs):
            arc_start_a = phase * 3 + arc_i * math.pi * 2 / num_arcs
            arc_end_a = arc_start_a + math.pi / 3
            num_pts = 10
            prev_pt = None
            for step in range(num_pts + 1):
                step_t = step / num_pts
                a = arc_start_a + (arc_end_a - arc_start_a) * step_t
                # Elliptical
                px = tx + int(math.cos(a) * r)
                py = ty + int(math.sin(a) * r * 0.5)
                if prev_pt is not None:
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_dark"], 240),
                                     prev_pt, (px, py), 3)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_mid"], 240),
                                     prev_pt, (px, py), 2)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_hot"], 240),
                                     prev_pt, (px, py), 1)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["white"], 240),
                                     prev_pt, (px, py), 1)
                prev_pt = (px, py)
        # Inner smaller ring
        inner_r = r * 2 // 3
        for arc_i in range(num_arcs):
            arc_start_a = -phase * 4 + arc_i * math.pi * 2 / num_arcs
            arc_end_a = arc_start_a + math.pi / 3
            num_pts = 8
            prev_pt = None
            for step in range(num_pts + 1):
                step_t = step / num_pts
                a = arc_start_a + (arc_end_a - arc_start_a) * step_t
                px = tx + int(math.cos(a) * inner_r)
                py = ty + int(math.sin(a) * inner_r * 0.5)
                if prev_pt is not None:
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_mid"], 200),
                                     prev_pt, (px, py), 2)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_shine"], 200),
                                     prev_pt, (px, py), 1)
                prev_pt = (px, py)
        # Central bright core (pull point)
        pulse = math.sin(phase * 5) * 0.3 + 0.7
        for r_core in range(8, 0, -1):
            alpha = _NS_thalryndel._alpha(180 * (8 - r_core) / 8 * pulse)
            _NS_thalryndel._aacircle(surface,
                                      (*_NS_thalryndel.PALETTE["light_hot"], alpha),
                                      (tx, ty), r_core)
        _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                  (tx, ty), 3)
        _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["white"],
                                  (tx, ty), 1)
        # Lightning particles being sucked in
        for i in range(12):
            p_t = (phase * 0.8 + i * 0.08) % 1.0
            p_a = i * math.pi / 6
            p_r = int(r * (1 - p_t))
            px = tx + int(math.cos(p_a) * p_r)
            py = ty + int(math.sin(p_a) * p_r * 0.5)
            alpha = _NS_thalryndel._alpha(240 * (1 - p_t * 0.3))
            pygame.draw.rect(surface,
                             (*_NS_thalryndel.PALETTE["light_hot"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_thalryndel.PALETTE["white"], alpha),
                             (px, py, 1, 1))
    # ============================================================
    # SKILL: E - OVERLOAD (charge orb + lightning beam)
    # ============================================================
    def _draw_overload_fx(surface, boss, x, y, timer, phase):
        """Big lightning orb charge + beam to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_thalryndel._target_position(boss, x, y)
        # Big orb at boss's chest
        orb_x = x + facing * 8
        orb_y = y - 2
        # Phase 1: Charge (0-40%)
        if progress < 0.4:
            t = progress / 0.4
            orb_r = int(6 + t * 10)
            for r in range(orb_r + 5, 0, -1):
                alpha = _NS_thalryndel._alpha(180 * (orb_r + 5 - r)
                                              / (orb_r + 5) * t)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_dark"],
                                           alpha),
                                          (orb_x, orb_y), r)
            # Layered orb
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_darkest"],
                                      (orb_x, orb_y), orb_r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_dark"],
                                      (orb_x, orb_y), max(1, orb_r - 2))
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_mid"],
                                      (orb_x, orb_y), max(1, orb_r - 4))
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_hot"],
                                      (orb_x, orb_y), max(1, orb_r - 6))
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (orb_x, orb_y), max(1, orb_r - 8))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (orb_x, orb_y, 1, 1))
            # Radial lightning rays inside orb
            for i in range(8):
                ray_a = phase * 4 + i * math.pi / 4
                rx = orb_x + int(math.cos(ray_a) * (orb_r - 2))
                ry = orb_y + int(math.sin(ray_a) * (orb_r - 2))
                pygame.draw.line(surface, _NS_thalryndel.PALETTE["white"],
                                 (orb_x, orb_y), (rx, ry), 1)
        # Phase 2: BEAM to target (40-100%)
        else:
            t = (progress - 0.4) / 0.6
            fade = 1.0 if t < 0.7 else (1 - (t - 0.7) / 0.3)
            # Persistent orb
            orb_r = 10
            for r in range(orb_r + 4, 0, -1):
                alpha = _NS_thalryndel._alpha(150 * (orb_r + 4 - r)
                                              / (orb_r + 4) * fade)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_light"],
                                           alpha),
                                          (orb_x, orb_y), r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_darkest"],
                                      (orb_x, orb_y), orb_r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_mid"],
                                      (orb_x, orb_y), orb_r - 3)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (orb_x, orb_y), orb_r - 6)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (orb_x, orb_y, 1, 1))
            # LIGHTNING BEAM to target
            alpha = _NS_thalryndel._alpha(255 * fade)
            # Multi-segment jagged beam
            num_segments = 15
            bolt_pts = [(orb_x, orb_y)]
            for i in range(1, num_segments):
                seg_t = i / num_segments
                mx = orb_x + (tx - orb_x) * seg_t
                my = orb_y + (ty - orb_y) * seg_t
                mx += math.sin(i * 4.3 + phase * 12) * 5
                my += math.cos(i * 6.7 + phase * 12) * 5
                bolt_pts.append((int(mx), int(my)))
            bolt_pts.append((tx, ty))
            for width, color_key, alpha_m in [
                (5, "light_darkest", 100),
                (4, "light_dark", 140),
                (3, "light_mid", 200),
                (2, "light_hot", 240),
                (1, "light_shine", 255),
                (1, "white", 255),
            ]:
                for i in range(len(bolt_pts) - 1):
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE[color_key],
                                      _NS_thalryndel._alpha(alpha_m * fade)),
                                     bolt_pts[i], bolt_pts[i + 1], width)
            # Sparks along beam
            for i in range(15):
                sp_i = (i / 15) * len(bolt_pts)
                sp_idx = int(sp_i)
                if sp_idx < len(bolt_pts):
                    sp_x = bolt_pts[sp_idx][0] + int(math.sin(phase * 8 + i) * 4)
                    sp_y = bolt_pts[sp_idx][1] + int(math.cos(phase * 8 + i) * 4)
                    pygame.draw.rect(surface,
                                     (*_NS_thalryndel.PALETTE["light_shine"],
                                      alpha),
                                     (sp_x, sp_y, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_thalryndel.PALETTE["white"], alpha),
                                     (sp_x, sp_y, 1, 1))
            # Impact at target
            impact_r = int(10 + math.sin(phase * 10) * 3)
            for r in range(impact_r, 0, -2):
                a = _NS_thalryndel._alpha(180 * (impact_r - r) / impact_r * fade)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_hot"], a),
                                          (tx, ty), r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (tx, ty), 3)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["white"],
                                      (tx, ty), 1)
    # ============================================================
    # SKILL: R - BALL LIGHTNING (ranged dash effect)
    # ============================================================
    def _draw_balllightning_fx(surface, boss, x, y, timer, phase):
        """Massive lightning ball racing forward."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_thalryndel._target_position(boss, x, y)
        start_x = x + facing * 15
        start_y = y
        # Phase 1: Charge (0-25%)
        if progress < 0.25:
            t = progress / 0.25
            orb_r = int(8 + t * 12)
            for r in range(orb_r + 5, 0, -1):
                alpha = _NS_thalryndel._alpha(220 * t * (orb_r + 5 - r) / (orb_r + 5))
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_mid"],
                                           alpha),
                                          (start_x, start_y), r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_hot"],
                                      (start_x, start_y), max(1, orb_r - 3))
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (start_x, start_y), max(1, orb_r - 6))
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"],
                             (start_x, start_y, 1, 1))
        # Phase 2: Racing ball (25-90%)
        else:
            t = min(1.0, (progress - 0.25) / 0.65)
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # LONG lightning trail behind
            trail_length = 60
            angle = math.atan2(ty - start_y, tx - start_x)
            trail_end_x = bx - int(math.cos(angle) * trail_length)
            trail_end_y = by - int(math.sin(angle) * trail_length)
            # Jagged lightning trail
            num_seg = 12
            trail_pts = [(trail_end_x, trail_end_y)]
            for i in range(1, num_seg):
                seg_t = i / num_seg
                mx = trail_end_x + (bx - trail_end_x) * seg_t
                my = trail_end_y + (by - trail_end_y) * seg_t
                mx += math.sin(i * 4.3 + phase * 15) * 6
                my += math.cos(i * 5.7 + phase * 15) * 6
                trail_pts.append((int(mx), int(my)))
            trail_pts.append((bx, by))
            # Thick trail with fade
            for i in range(len(trail_pts) - 1):
                seg_fade = i / len(trail_pts)
                for width, color_key in [
                    (8, "light_darkest"),
                    (6, "light_dark"),
                    (4, "light_mid"),
                    (2, "light_hot"),
                    (1, "white"),
                ]:
                    alpha = _NS_thalryndel._alpha(200 * seg_fade)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE[color_key], alpha),
                                     trail_pts[i], trail_pts[i + 1], width)
            # BIG BALL LIGHTNING HEAD
            for r in range(20, 3, -2):
                alpha = _NS_thalryndel._alpha(120 * (20 - r) / 20)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_light"],
                                           alpha),
                                          (bx, by), r)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_darkest"],
                                      (bx, by), 14)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_dark"],
                                      (bx, by), 11)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_mid"],
                                      (bx, by), 8)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_hot"],
                                      (bx, by), 5)
            _NS_thalryndel._aacircle(surface, _NS_thalryndel.PALETTE["light_shine"],
                                      (bx, by), 3)
            pygame.draw.rect(surface, _NS_thalryndel.PALETTE["white"], (bx, by, 1, 1))
            # Lightning arcs shooting out of ball
            for i in range(8):
                arc_a = phase * 5 + i * math.pi / 4
                arc_len = 15 + int(math.sin(phase * 8 + i) * 5)
                arc_end_x = bx + int(math.cos(arc_a) * arc_len)
                arc_end_y = by + int(math.sin(arc_a) * arc_len)
                # Jagged arc
                mid_x = bx + int(math.cos(arc_a) * arc_len / 2) \
                         + int(math.sin(phase * 10 + i) * 3)
                mid_y = by + int(math.sin(arc_a) * arc_len / 2) \
                         + int(math.cos(phase * 10 + i) * 3)
                pygame.draw.line(surface,
                                 (*_NS_thalryndel.PALETTE["light_hot"], 240),
                                 (bx, by), (mid_x, mid_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_thalryndel.PALETTE["white"], 240),
                                 (bx, by), (mid_x, mid_y), 1)
                pygame.draw.line(surface,
                                 (*_NS_thalryndel.PALETTE["light_hot"], 240),
                                 (mid_x, mid_y), (arc_end_x, arc_end_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_thalryndel.PALETTE["white"], 240),
                                 (mid_x, mid_y), (arc_end_x, arc_end_y), 1)
                pygame.draw.rect(surface, _NS_thalryndel.PALETTE["light_shine"],
                                 (arc_end_x, arc_end_y, 2, 2))
            # Impact at destination
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_thalryndel._alpha(240 * (1 - st))
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_darkest"],
                                           alpha),
                                          (tx, ty), radius + 3, 3)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_dark"],
                                           alpha),
                                          (tx, ty), radius, 3)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_mid"],
                                           alpha),
                                          (tx, ty), max(1, radius - 6), 2)
                _NS_thalryndel._aacircle(surface,
                                          (*_NS_thalryndel.PALETTE["light_hot"],
                                           alpha),
                                          (tx, ty), max(1, radius - 14), 1)
                # Radial lightning burst
                for i in range(12):
                    angle_r = i * math.pi / 6
                    end_x = tx + int(math.cos(angle_r) * radius)
                    end_y = ty + int(math.sin(angle_r) * radius * 0.8)
                    pygame.draw.line(surface,
                                     (*_NS_thalryndel.PALETTE["light_hot"], alpha),
                                     (tx, ty), (end_x, end_y), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_thalryndel.PALETTE["white"], alpha),
                                     (end_x, end_y, 2, 2))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_urgharun(surface, boss, x, y):
    """Entry point urgharun."""
    return _NS_urgharun.draw_urgharun(surface, boss, x, y)


def draw_yhoranth(surface, boss, x, y):
    """Entry point yhoranth."""
    return _NS_yhoranth.draw_yhoranth(surface, boss, x, y)


def draw_zulkhaven(surface, boss, x, y):
    """Entry point zulkhaven."""
    return _NS_zulkhaven.draw_zulkhaven(surface, boss, x, y)


def draw_thalryndel(surface, boss, x, y):
    """Entry point thalryndel."""
    return _NS_thalryndel.draw_thalryndel(surface, boss, x, y)
