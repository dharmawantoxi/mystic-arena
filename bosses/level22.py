"""
bosses/level22.py - Semua boss Level 22

Berisi:
  - grimstalker  (mini boss - MELEE toxic werewolf-cyborg)
  - kryvoxar     (mini boss - RANGED floating crystal wraith)
  - vargroth     (mini boss - MELEE bloodmoon alpha werewolf)
  - molgravar    (TRUE BOSS - MELEE stone golem dengan lava cracks)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _grm_ (grimstalker), _krv_ (kryvoxar), _var_ (vargroth),
    _mlg_ (molgravar) sudah unik. Nama fungsi namespace (_draw_*)
    TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# GRIMSTALKER (CHEMBEAST OF THE DEPTHS) - Mini Boss
# ====================================================================

class _NS_grimstalker:
    """Namespace grimstalker - mini boss werewolf-cyborg toxic."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Fur (dark grey-blue)
        "fur_darkest": (10, 15, 22),
        "fur_dark": (28, 38, 48),
        "fur_mid": (58, 72, 85),
        "fur_light": (105, 122, 138),
        "fur_shine": (165, 180, 195),
        # Skin/muzzle (dark grey)
        "skin_darkest": (12, 12, 16),
        "skin_dark": (32, 32, 40),
        "skin_mid": (68, 68, 78),
        "skin_light": (120, 120, 132),
        # Toxic green (canister glow, drool, aura)
        "toxic_darkest": (15, 30, 8),
        "toxic_dark": (45, 90, 20),
        "toxic_mid": (100, 180, 45),
        "toxic_light": (170, 240, 90),
        "toxic_hot": (220, 255, 140),
        "toxic_shine": (250, 255, 210),
        # Brass/copper machinery
        "brass_darkest": (25, 15, 8),
        "brass_dark": (75, 50, 20),
        "brass_mid": (145, 100, 45),
        "brass_light": (215, 170, 90),
        "brass_shine": (250, 220, 155),
        # Iron plate (dark metal)
        "iron_darkest": (12, 12, 15),
        "iron_dark": (35, 38, 45),
        "iron_mid": (75, 80, 90),
        "iron_light": (135, 140, 155),
        # Fang/claw (aged bone)
        "fang_dark": (60, 45, 25),
        "fang_mid": (150, 125, 80),
        "fang_light": (230, 210, 160),
        "fang_shine": (255, 245, 210),
        # Eye (glowing toxic green)
        "eye_socket": (5, 8, 3),
        "eye_dark": (25, 55, 10),
        "eye_mid": (110, 200, 50),
        "eye_light": (200, 255, 120),
        "eye_glow": (255, 255, 200),
        # Blood hunt eye (red variant when W active)
        "hunt_dark": (95, 15, 20),
        "hunt_mid": (200, 35, 40),
        "hunt_light": (255, 90, 80),
        # Mist
        "mist_dark": (18, 35, 12),
        "mist_mid": (70, 120, 30),
        "mist_light": (150, 200, 70),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 2),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grimstalker._clamp(color)
        if _NS_grimstalker.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_grimstalker._clamp(color)
        if _NS_grimstalker.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_grimstalker._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_grimstalker(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_grimstalker._update_grm_attack_anim(boss)
        attacking = (
            getattr(boss, "_grm_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_grimstalker._draw_toxic_aura(surface, x, y, pulse)
        _NS_grimstalker._draw_ground_ring(surface, x, y + 42, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_grimstalker._draw_howl_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grimstalker._draw_bloodhunt_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_grimstalker._draw_dupress_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_grimstalker._draw_jaws_ground(surface, boss, x, y, skill_timer, pulse)
        # Body - floating with vertical bob
        floating_bob = math.sin(pulse * 0.8) * 4
        if attacking:
            _NS_grimstalker._draw_grm_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_grimstalker._draw_grm_idle(surface, boss, x, y - floating_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_grimstalker._draw_jaws_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_grimstalker._draw_howl_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_grimstalker._draw_dupress_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grimstalker._draw_bloodhunt_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_grm_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_grm_previous_timer", 0))
        active = bool(getattr(boss, "_grm_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._grm_attack_active = True
            boss._grm_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._grm_attack_frame = int(getattr(boss, "_grm_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._grm_attack_active = False
            boss._grm_attack_frame = 0
            active = False
        boss._grm_previous_timer = timer
        boss._grm_attack_progress = (
            min(1.0, getattr(boss, "_grm_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_grm_idle(surface, boss, x, y):
        _NS_grimstalker._draw_shadow(surface, x, y + 46)
        _NS_grimstalker._draw_toxic_mist(surface, x, y + 30, boss.pulse)
        _NS_grimstalker._draw_grm_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_grm_attack(surface, boss, x, y):
        progress = getattr(boss, "_grm_attack_progress", 0.0)
        # Rear back → lunge forward → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 14)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(10 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_grimstalker._draw_shadow(surface, x + lunge, y + 46)
        _NS_grimstalker._draw_toxic_mist(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_grimstalker._draw_grm_body(surface, x + lunge, y - lift,
                                        boss.direction, boss.pulse, "attack", progress)
        _NS_grimstalker._draw_claw_slash(surface, x + lunge, y - lift,
                                          boss.direction, progress)
    # ============================================================
    # BODY (quadruped werewolf-cyborg)
    # ============================================================
    def _draw_grm_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw beast body: 4 legs, main body horizontal, head with muzzle."""
        # Order: tail → back legs → body → front legs → back canisters → head → shoulder canister
        _NS_grimstalker._draw_beast_tail(surface, cx, cy + 4, facing, phase, action)
        _NS_grimstalker._draw_beast_legs(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_grimstalker._draw_beast_body(surface, cx, cy, facing, phase)
        _NS_grimstalker._draw_back_canisters(surface, cx, cy - 4, facing, phase)
        # Head lunge offset during attack
        neck_lunge = 0
        head_dip = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                neck_lunge = -int(t * 3) * facing
                head_dip = -int(t * 3)
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                neck_lunge = int((-3 + t * 14)) * facing
                head_dip = int(-3 + t * 5)
            else:
                t = (attack_progress - 0.6) / 0.4
                neck_lunge = int(11 * (1 - t)) * facing
                head_dip = int(2 * (1 - t))
        _NS_grimstalker._draw_beast_head(surface, cx + facing * 20 + neck_lunge,
                                          cy - 10 + head_dip, facing, phase, action,
                                          attack_progress)
        _NS_grimstalker._draw_shoulder_canister(surface, cx, cy - 6, facing, phase)
    def _draw_beast_body(surface, cx, cy, facing, phase):
        """Main body: muscular quadruped chest+torso."""
        breath = math.sin(phase * 0.7) * 1
        # Body shape (elongated horizontal)
        body_shape = [
            (cx - 18, cy - 2),
            (cx - 20, cy - 6),
            (cx - 15, cy - 10),
            (cx - 5, cy - 12 - int(breath)),
            (cx + 8, cy - 12 - int(breath)),
            (cx + 16, cy - 9),
            (cx + 20, cy - 4),
            (cx + 18, cy + 2),
            (cx + 12, cy + 6),
            (cx - 4, cy + 8),
            (cx - 14, cy + 6),
            (cx - 20, cy + 2),
        ]
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                               [(px + 2, py + 3) for px, py in body_shape])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_darkest"], body_shape)
        # Fur top layer
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_dark"], [
            (cx - 18, cy - 3),
            (cx - 18, cy - 8),
            (cx - 13, cy - 11),
            (cx - 5, cy - 11),
            (cx + 8, cy - 11),
            (cx + 15, cy - 8),
            (cx + 18, cy - 4),
            (cx + 15, cy),
            (cx - 15, cy),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_mid"], [
            (cx - 14, cy - 4),
            (cx - 12, cy - 8),
            (cx - 4, cy - 10),
            (cx + 6, cy - 10),
            (cx + 12, cy - 7),
            (cx + 14, cy - 4),
            (cx + 10, cy - 2),
            (cx - 10, cy - 2),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_light"], [
            (cx - 6, cy - 7),
            (cx - 2, cy - 9),
            (cx + 5, cy - 8),
            (cx + 3, cy - 5),
            (cx - 4, cy - 5),
        ])
        # Belly (darker underside)
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_dark"], [
            (cx - 14, cy),
            (cx + 14, cy),
            (cx + 15, cy + 3),
            (cx + 8, cy + 7),
            (cx - 8, cy + 7),
            (cx - 15, cy + 3),
        ])
        # Fur texture (chevrons on back)
        for row in range(2):
            y_row = cy - 6 + row * 3
            for dx in (-12, -6, 0, 6, 12):
                offset = (row % 2) * 2 - 1
                pygame.draw.line(surface, _NS_grimstalker.PALETTE["fur_darkest"],
                                 (cx + dx + offset - 1, y_row),
                                 (cx + dx + offset, y_row - 1), 1)
                pygame.draw.line(surface, _NS_grimstalker.PALETTE["fur_darkest"],
                                 (cx + dx + offset, y_row - 1),
                                 (cx + dx + offset + 1, y_row), 1)
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fur_shine"],
                                 (cx + dx + offset, y_row - 1, 1, 1))
        # IRON CHEST PLATE (mech armor)
        plate = [
            (cx - 8, cy - 2),
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 8, cy - 2),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ]
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["iron_darkest"],
                               [(px + 1, py + 1) for px, py in plate])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["iron_dark"], plate)
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["iron_mid"], [
            (cx - 6, cy - 2),
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 6, cy - 2),
            (cx + 4, cy + 2),
            (cx - 4, cy + 2),
        ])
        # Center bolt
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"], (cx - 1, cy - 1, 3, 3))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_mid"], (cx, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_shine"], (cx, cy - 1, 1, 1))
        # Side bolts
        for bx in (-6, 6):
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"], (cx + bx - 1, cy, 2, 2))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_light"], (cx + bx, cy, 1, 1))
    def _draw_beast_legs(surface, cx, cy, facing, phase, action, attack_progress):
        """4 legs (2 front, 2 back). Front legs animate on attack."""
        # Leg positions
        # Back legs
        back_leg_sway = math.sin(phase * 1.0) * 1
        # Far back leg
        _NS_grimstalker._draw_beast_leg(
            surface, cx - 14, cy + 4, cx - 15, cy + 18, cx - 14, cy + 28,
            facing, dark=True)
        # Near back leg
        _NS_grimstalker._draw_beast_leg(
            surface, cx - 10, cy + 5, cx - 11 + int(back_leg_sway), cy + 19,
            cx - 10, cy + 30, facing, dark=False)
        # Front legs — animate on attack (claw swipe)
        if action == "attack":
            # Near front leg swings during attack
            if attack_progress < 0.35:
                # Rear back
                t = attack_progress / 0.35
                paw_x_off = -int(t * 5) * facing
                paw_y_off = -int(t * 6)
            elif attack_progress < 0.6:
                # Swipe forward+down
                t = (attack_progress - 0.35) / 0.25
                paw_x_off = int((-5 + t * 18)) * facing
                paw_y_off = int(-6 + t * 10)
            else:
                t = (attack_progress - 0.6) / 0.4
                paw_x_off = int(13 * (1 - t)) * facing
                paw_y_off = int(4 * (1 - t))
            # Far front leg (stable)
            _NS_grimstalker._draw_beast_leg(
                surface, cx + 12, cy + 3, cx + 13, cy + 16, cx + 12, cy + 28,
                facing, dark=True)
            # Near front leg (swinging - claw attack)
            shoulder = (cx + 14, cy + 4)
            elbow = (cx + 16 + paw_x_off // 2, cy + 14 + paw_y_off // 2)
            paw = (cx + 18 + paw_x_off, cy + 22 + paw_y_off)
            _NS_grimstalker._draw_beast_leg_custom(
                surface, shoulder, elbow, paw, facing, dark=False, claws_extended=True)
        else:
            front_leg_sway = math.sin(phase * 1.0 + math.pi) * 1
            # Far front leg
            _NS_grimstalker._draw_beast_leg(
                surface, cx + 12, cy + 3, cx + 13, cy + 16, cx + 12, cy + 28,
                facing, dark=True)
            # Near front leg
            _NS_grimstalker._draw_beast_leg(
                surface, cx + 15, cy + 4, cx + 16 + int(front_leg_sway), cy + 17,
                cx + 15, cy + 29, facing, dark=False)
    def _draw_beast_leg(surface, sx, sy, ex, ey, px, py, facing, dark=False):
        """Standard beast leg with paw."""
        shoulder = (sx, sy)
        elbow = (ex, ey)
        paw = (px, py)
        _NS_grimstalker._draw_beast_leg_custom(surface, shoulder, elbow, paw,
                                                facing, dark=dark, claws_extended=False)
    def _draw_beast_leg_custom(surface, shoulder, elbow, paw, facing,
                                dark=False, claws_extended=False):
        """Draw one beast leg with fur + brass mechanical joint."""
        fur_dark_c = _NS_grimstalker.PALETTE["fur_darkest"] if dark else _NS_grimstalker.PALETTE["fur_dark"]
        fur_mid_c = _NS_grimstalker.PALETTE["fur_dark"] if dark else _NS_grimstalker.PALETTE["fur_mid"]
        fur_light_c = _NS_grimstalker.PALETTE["fur_mid"] if dark else _NS_grimstalker.PALETTE["fur_light"]
        # Shadow
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                                 (shoulder[0] + 2, shoulder[1] + 2),
                                 (elbow[0] + 2, elbow[1] + 2), 7)
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                                 (elbow[0] + 2, elbow[1] + 2),
                                 (paw[0] + 2, paw[1] + 2), 5)
        # Upper leg (thigh)
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["fur_darkest"], shoulder, elbow, 8)
        _NS_grimstalker._aaline(surface, fur_dark_c, shoulder, elbow, 6)
        _NS_grimstalker._aaline(surface, fur_mid_c,
                                 (shoulder[0], shoulder[1] - 1), (elbow[0], elbow[1] - 1), 4)
        _NS_grimstalker._aaline(surface, fur_light_c,
                                 (shoulder[0], shoulder[1] - 1), (elbow[0], elbow[1] - 1), 1)
        # BRASS KNEE JOINT
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_darkest"],
                         (elbow[0] - 3, elbow[1] - 2, 6, 5))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"],
                         (elbow[0] - 3, elbow[1] - 2, 6, 4))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_mid"],
                         (elbow[0] - 2, elbow[1] - 1, 4, 2))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_light"],
                         (elbow[0] - 1, elbow[1] - 1, 2, 1))
        # Lower leg (shin) - iron/metal segment
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["iron_darkest"], elbow, paw, 6)
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["iron_dark"], elbow, paw, 4)
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["iron_mid"],
                                 (elbow[0], elbow[1] - 1), (paw[0], paw[1] - 1), 2)
        # PAW with CLAWS
        pw = paw[0]
        ph = paw[1]
        # Paw pad
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"], [
            (pw - 4 + 1, ph + 1), (pw + 5 + 1, ph + 1),
            (pw + 4 + 1, ph + 4 + 1), (pw - 3 + 1, ph + 4 + 1),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_darkest"], [
            (pw - 4, ph), (pw + 5, ph), (pw + 4, ph + 4), (pw - 3, ph + 4),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_dark"], [
            (pw - 3, ph + 1), (pw + 4, ph + 1), (pw + 3, ph + 3), (pw - 2, ph + 3),
        ])
        # Claws (3 sharp claws)
        claw_len = 4 if claws_extended else 3
        claw_glow = claws_extended
        for i, cx_off in enumerate((-3, 0, 3)):
            claw_tip_x = pw + cx_off + facing * 1
            claw_tip_y = ph + 4 + claw_len
            _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"], [
                (pw + cx_off - 1 + 1, ph + 3 + 1),
                (claw_tip_x + 1, claw_tip_y + 1),
                (pw + cx_off + 1 + 1, ph + 3 + 1),
            ])
            _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fang_dark"], [
                (pw + cx_off - 1, ph + 3),
                (claw_tip_x, claw_tip_y),
                (pw + cx_off + 1, ph + 3),
            ])
            _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fang_mid"], [
                (pw + cx_off, ph + 3),
                (claw_tip_x, claw_tip_y),
                (pw + cx_off + 1, ph + 3),
            ])
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fang_light"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            if claw_glow:
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_hot"],
                                 (claw_tip_x, claw_tip_y - 1, 1, 1))
    def _draw_beast_tail(surface, cx, cy, facing, phase, action):
        """Long bushy tail curling back."""
        back_dir = -facing
        base_x = cx + back_dir * 16
        base_y = cy
        # Tail sway
        tail_wave = math.sin(phase * 1.4) * 5
        if action == "attack":
            tail_wave += math.sin(phase * 3) * 3
        segments = 6
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (10 + t * 22))
            y_off = int(2 - t * 10)
            wave = math.sin(phase * 1.2 + t * math.pi) * (3 + t * 2)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))
        # Draw tail as tapered segments (bushy fur)
        for i in range(len(points) - 1):
            thickness = max(2, 9 - i)
            _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                                     (points[i][0] + 2, points[i][1] + 2),
                                     (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                     thickness + 1)
            _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["fur_darkest"],
                                     points[i], points[i + 1], thickness)
            _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["fur_dark"],
                                     points[i], points[i + 1], max(1, thickness - 2))
            _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["fur_mid"],
                                     (points[i][0], points[i][1] - 1),
                                     (points[i + 1][0], points[i + 1][1] - 1),
                                     max(1, thickness - 4))
        # Bushy fur tuft at end
        if len(points) >= 2:
            end = points[-1]
            for i in range(6):
                angle = math.pi * 2 * i / 6 + phase * 0.5
                fx = end[0] + int(math.cos(angle) * 3)
                fy = end[1] + int(math.sin(angle) * 3)
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fur_darkest"], (fx, fy, 2, 2))
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fur_mid"], (fx, fy, 1, 1))
            # Toxic tip glow
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_mid"],
                             (end[0], end[1], 2, 2))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_light"],
                             (end[0], end[1], 1, 1))
    def _draw_back_canisters(surface, cx, cy, facing, phase):
        """Toxic green canisters mounted on back (like Warwick's tubes)."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # 3 canisters on back
        positions = [(-6, -8), (0, -10), (6, -8)]
        for i, (dx, dy) in enumerate(positions):
            canx = cx + dx
            cany = cy + dy
            # Canister body (brass frame)
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                             (canx - 3 + 1, cany - 4 + 1, 6, 8))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_darkest"],
                             (canx - 3, cany - 4, 6, 8))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"],
                             (canx - 3, cany - 4, 6, 1))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"],
                             (canx - 3, cany + 3, 6, 1))
            # Glass part with toxic liquid
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_darkest"],
                             (canx - 2, cany - 3, 4, 6))
            liquid_level = int(5 * pulse)
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_dark"],
                             (canx - 2, cany - 3 + (5 - liquid_level), 4, liquid_level + 1))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_mid"],
                             (canx - 1, cany - 2 + (5 - liquid_level), 2, liquid_level))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_light"],
                             (canx - 1, cany, 1, 2))
            # Bubbles inside
            for b in range(2):
                bt = (phase * 0.8 + i * 0.3 + b * 0.5) % 1.0
                by = cany + 2 - int(bt * 4)
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_hot"], (canx, by, 1, 1))
            # Bright glow
            for r in range(4, 0, -1):
                alpha = _NS_grimstalker._alpha(80 * (4 - r) / 4 * pulse)
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                           (canx, cany), r)
            # Top valve/cap
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["iron_dark"],
                             (canx - 2, cany - 5, 4, 1))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["iron_mid"],
                             (canx - 1, cany - 5, 1, 1))
            # Steam vent (rising)
            for s in range(3):
                st = (phase * 0.6 + i * 0.4 + s * 0.35) % 1.0
                sx = canx + int(math.sin(phase + i + s) * 2)
                sy = cany - 6 - int(st * 8)
                alpha = _NS_grimstalker._alpha(180 * (1 - st))
                if alpha > 0:
                    _NS_grimstalker._aacircle(surface,
                                               (*_NS_grimstalker.PALETTE["toxic_mid"], alpha),
                                               (sx, sy), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_grimstalker.PALETTE["toxic_hot"], alpha),
                                     (sx, sy, 1, 1))
    def _draw_shoulder_canister(surface, cx, cy, facing, phase):
        """Big canister on shoulder/neck area (front-visible)."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        canx = cx + facing * 6
        cany = cy - 2
        # Frame
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                         (canx - 4 + 1, cany - 5 + 1, 8, 10))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_darkest"],
                         (canx - 4, cany - 5, 8, 10))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"],
                         (canx - 4, cany - 5, 8, 2))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_dark"],
                         (canx - 4, cany + 3, 8, 2))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_mid"],
                         (canx - 4, cany - 5, 1, 10))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_mid"],
                         (canx + 3, cany - 5, 1, 10))
        # Glass
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_darkest"],
                         (canx - 3, cany - 3, 6, 6))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_dark"],
                         (canx - 3, cany - 2, 6, 5))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_mid"],
                         (canx - 2, cany - 1, 4, 4))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_light"],
                         (canx - 1, cany, 3, 2))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_hot"],
                         (canx, cany, 1, 1))
        # Glow
        for r in range(6, 0, -1):
            alpha = _NS_grimstalker._alpha(100 * (6 - r) / 6 * pulse)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                       (canx, cany), r)
        # Bolts
        for by in (-4, 3):
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_darkest"],
                             (canx - 4, cany + by, 1, 1))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["brass_light"],
                             (canx + 3, cany + by, 1, 1))
        # Hose to head
        hose_end_x = cx + facing * 14
        hose_end_y = cy - 6
        for offset in range(3):
            _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["iron_darkest"],
                                     (canx + facing * 2, cany - 4),
                                     (hose_end_x, hose_end_y + offset), 2)
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["iron_dark"],
                                 (canx + facing * 2, cany - 4),
                                 (hose_end_x, hose_end_y), 2)
        _NS_grimstalker._aaline(surface, _NS_grimstalker.PALETTE["iron_mid"],
                                 (canx + facing * 2, cany - 5),
                                 (hose_end_x, hose_end_y - 1), 1)
    def _draw_beast_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Werewolf head: muzzle, ears, glowing eyes, toxic mouth."""
        # Main skull shape
        head_shape = [
            (cx - 7 * facing, cy + 5),   # jaw back
            (cx - 9 * facing, cy),        # cheek
            (cx - 8 * facing, cy - 6),    # crown back
            (cx - 3 * facing, cy - 8),    # top
            (cx + 3 * facing, cy - 7),    # brow
            (cx + 10 * facing, cy - 4),   # muzzle top
            (cx + 15 * facing, cy - 2),   # snout tip top
            (cx + 16 * facing, cy + 1),   # snout tip
            (cx + 14 * facing, cy + 4),   # snout bottom
            (cx + 10 * facing, cy + 5),   # under snout
            (cx + 3 * facing, cy + 7),    # jaw
            (cx - 3 * facing, cy + 7),
        ]
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                               [(px + 2, py + 2) for px, py in head_shape])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_darkest"], head_shape)
        # Fur top head
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_dark"], [
            (cx - 7 * facing, cy + 4),
            (cx - 8 * facing, cy - 1),
            (cx - 7 * facing, cy - 5),
            (cx - 3 * facing, cy - 7),
            (cx + 3 * facing, cy - 6),
            (cx + 9 * facing, cy - 3),
            (cx + 14 * facing, cy - 1),
            (cx + 15 * facing, cy + 1),
            (cx + 12 * facing, cy),
            (cx - 5 * facing, cy),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_mid"], [
            (cx - 5 * facing, cy - 1),
            (cx - 3 * facing, cy - 5),
            (cx + 3 * facing, cy - 5),
            (cx + 8 * facing, cy - 2),
            (cx + 12 * facing, cy),
            (cx + 5 * facing, cy - 1),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_light"], [
            (cx - 1 * facing, cy - 4),
            (cx + 2 * facing, cy - 5),
            (cx + 6 * facing, cy - 3),
            (cx + 4 * facing, cy - 2),
            (cx, cy - 2),
        ])
        # MUZZLE (darker snout)
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_darkest"], [
            (cx + 8 * facing, cy - 2),
            (cx + 15 * facing, cy - 1),
            (cx + 16 * facing, cy + 1),
            (cx + 14 * facing, cy + 4),
            (cx + 10 * facing, cy + 4),
            (cx + 8 * facing, cy + 2),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_dark"], [
            (cx + 10 * facing, cy - 1),
            (cx + 14 * facing, cy),
            (cx + 15 * facing, cy + 1),
            (cx + 13 * facing, cy + 3),
            (cx + 10 * facing, cy + 3),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_mid"], [
            (cx + 11 * facing, cy),
            (cx + 13 * facing, cy + 1),
            (cx + 12 * facing, cy + 2),
        ])
        # NOSE (black tip)
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                         (cx + 15 * facing, cy, 2, 2))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["skin_darkest"],
                         (cx + 15 * facing, cy, 1, 1))
        # EARS (pointed, pinned back)
        _NS_grimstalker._draw_beast_ears(surface, cx, cy, facing, phase)
        # EYE (glowing toxic or hunt-red based on blood hunt)
        blood_hunt = getattr(surface, '_blood_hunt_active', False)  # fallback
        _NS_grimstalker._draw_beast_eye(surface, cx + 2 * facing, cy - 3, facing, phase)
        # MOUTH with FANGS (opens on attack)
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 6)
        _NS_grimstalker._draw_beast_mouth(surface, cx, cy, facing, phase, mouth_open)
        # Toxic drool (idle)
        if action != "attack":
            for i in range(2):
                drip_t = (phase * 0.4 + i * 0.5) % 1.0
                dx = cx + 12 * facing + int(math.sin(phase + i) * 1)
                dy = cy + 5 + int(drip_t * 6)
                alpha = _NS_grimstalker._alpha(200 * (1 - drip_t))
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_mid"], alpha),
                                 (dx, dy, 1, 2))
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                 (dx, dy, 1, 1))
    def _draw_beast_ears(surface, cx, cy, facing, phase):
        """Wolf ears (pointed, twitching slightly)."""
        twitch = math.sin(phase * 0.8) * 1
        # Back ear
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"], [
            (cx - 4 * facing + 1, cy - 7 + 1),
            (cx - 6 * facing + 1, cy - 12 + int(twitch) + 1),
            (cx - 2 * facing + 1, cy - 8 + 1),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_darkest"], [
            (cx - 4 * facing, cy - 7),
            (cx - 6 * facing, cy - 12 + int(twitch)),
            (cx - 2 * facing, cy - 8),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_dark"], [
            (cx - 4 * facing, cy - 7),
            (cx - 5 * facing, cy - 11 + int(twitch)),
            (cx - 3 * facing, cy - 8),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_dark"], [
            (cx - 4 * facing, cy - 8),
            (cx - 5 * facing, cy - 10 + int(twitch)),
            (cx - 3 * facing, cy - 8),
        ])
        # Front ear
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"], [
            (cx + 2 * facing + 1, cy - 7 + 1),
            (cx + 4 * facing + 1, cy - 12 - int(twitch) + 1),
            (cx + 6 * facing + 1, cy - 6 + 1),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_darkest"], [
            (cx + 2 * facing, cy - 7),
            (cx + 4 * facing, cy - 12 - int(twitch)),
            (cx + 6 * facing, cy - 6),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["fur_dark"], [
            (cx + 3 * facing, cy - 7),
            (cx + 4 * facing, cy - 11 - int(twitch)),
            (cx + 5 * facing, cy - 6),
        ])
        _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["skin_dark"], [
            (cx + 3 * facing, cy - 8),
            (cx + 4 * facing, cy - 10 - int(twitch)),
            (cx + 5 * facing, cy - 7),
        ])
    def _draw_beast_eye(surface, ex, ey, facing, phase, is_hunt=False):
        """Glowing toxic-green eye (or red if blood hunt active)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Colors
        if is_hunt:
            dark_c = _NS_grimstalker.PALETTE["hunt_dark"]
            mid_c = _NS_grimstalker.PALETTE["hunt_mid"]
            light_c = _NS_grimstalker.PALETTE["hunt_light"]
        else:
            dark_c = _NS_grimstalker.PALETTE["eye_dark"]
            mid_c = _NS_grimstalker.PALETTE["eye_mid"]
            light_c = _NS_grimstalker.PALETTE["eye_light"]
        # Socket
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))
        # Halo
        for r in range(5, 0, -1):
            alpha = _NS_grimstalker._alpha(100 * (5 - r) / 5 * pulse)
            _NS_grimstalker._aacircle(surface, (*mid_c, alpha), (ex + 1, ey), r)
        # Core
        pygame.draw.rect(surface, dark_c, (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, mid_c, (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, light_c, (ex + 1, ey, 2, 1))
        pygame.draw.rect(surface, _NS_grimstalker.PALETTE["eye_glow"], (ex + 2, ey, 1, 1))
        # Pupil
        pygame.draw.line(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                         (ex + 1, ey - 1), (ex + 1, ey + 1), 1)
    def _draw_beast_mouth(surface, cx, cy, facing, phase, mouth_open):
        """Mouth with sharp fangs; opens on attack."""
        mouth_y = cy + 3
        mouth_x_start = cx + 4 * facing
        mouth_x_end = cx + 15 * facing
        if mouth_open > 0:
            # Open mouth cavity
            _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end, mouth_y + int(mouth_open)),
                (mouth_x_start, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_grimstalker._poly(surface, _NS_grimstalker.PALETTE["eye_socket"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing, mouth_y + int(mouth_open * 0.7) - 1),
            ])
            # Toxic green glow (venom brewing)
            glow_r = int(2 + mouth_open * 0.3)
            for r in range(glow_r + 2, 0, -1):
                alpha = _NS_grimstalker._alpha(180 * (glow_r + 2 - r) / (glow_r + 2))
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_dark"], alpha),
                                           (cx + 10 * facing, mouth_y + int(mouth_open * 0.5)), r)
            _NS_grimstalker._aacircle(surface, _NS_grimstalker.PALETTE["toxic_mid"],
                                       (cx + 10 * facing, mouth_y + int(mouth_open * 0.5)),
                                       max(1, glow_r - 1))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_light"],
                             (cx + 10 * facing, mouth_y + int(mouth_open * 0.5), 1, 1))
            # UPPER FANGS
            for x_off in (5, 9, 12):
                fang_x = cx + int(x_off * facing)
                fang_tip_y = mouth_y + int(mouth_open * 0.8)
                pygame.draw.line(surface, _NS_grimstalker.PALETTE["fang_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_grimstalker.PALETTE["fang_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
                # Toxic drip
                if mouth_open > 3:
                    drip_y = fang_tip_y + 2
                    pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_mid"],
                                     (fang_x, drip_y, 1, 2))
                    pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_light"],
                                     (fang_x, drip_y, 1, 1))
            # LOWER FANGS
            for x_off in (6, 10, 13):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 2
                pygame.draw.line(surface, _NS_grimstalker.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fang_mid"],
                                 (fang_x, fang_tip_y, 1, 1))
        else:
            # Closed mouth with visible fang tips
            pygame.draw.line(surface, _NS_grimstalker.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            for x_off in (6, 10, 13):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fang_mid"],
                                 (fang_x, mouth_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_grimstalker.PALETTE["fang_light"],
                                 (fang_x, mouth_y + 2, 1, 1))
    # ============================================================
    # CLAW SLASH (basic attack swing arc)
    # ============================================================
    def _draw_claw_slash(surface, cx, cy, facing, progress):
        """Toxic green claw slash arc."""
        if progress < 0.35 or progress > 0.75:
            return
        t = (progress - 0.35) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_grimstalker._alpha(255 * intensity)
        arc_cx = cx + facing * 18
        arc_cy = cy + 6
        arc_r = 22
        # 3 claw slash lines (parallel)
        for line_i, line_offset in enumerate((-4, 0, 4)):
            start_angle = math.radians(-75) if facing > 0 else math.radians(180 + 75)
            end_angle = math.radians(75) if facing > 0 else math.radians(180 - 75)
            sweep = start_angle + (end_angle - start_angle) * t
            trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
            prev_pt = None
            num_segments = 10
            for i in range(num_segments + 1):
                seg_t = i / num_segments
                angle = trail_start + (sweep - trail_start) * seg_t
                px = arc_cx + int(math.cos(angle) * (arc_r + line_offset))
                py = arc_cy + int(math.sin(angle) * (arc_r + line_offset))
                if prev_pt is not None:
                    for thickness, color in [
                        (4, (*_NS_grimstalker.PALETTE["toxic_darkest"], alpha // 3)),
                        (3, (*_NS_grimstalker.PALETTE["toxic_dark"], alpha // 2)),
                        (2, (*_NS_grimstalker.PALETTE["toxic_mid"], alpha)),
                        (1, (*_NS_grimstalker.PALETTE["toxic_light"], alpha)),
                    ]:
                        pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
                prev_pt = (px, py)
        # Sparks along arc
        for i in range(5):
            angle = math.radians(-75) + (math.radians(150)) * (i / 5)
            if facing < 0:
                angle = math.radians(180) - angle
            spark_r = arc_r + int(math.sin(i + progress * 10) * 3)
            sx = arc_cx + int(math.cos(angle) * spark_r)
            sy = arc_cy + int(math.sin(angle) * spark_r)
            pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_shine"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # TOXIC MIST (ambient)
    # ============================================================
    def _draw_toxic_mist(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_grimstalker._alpha((32 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_grimstalker.PALETTE["mist_dark"], alpha),
                                    (70 - radius * 2, 22 - radius // 3,
                                     radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_grimstalker._alpha((20 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_grimstalker.PALETTE["mist_mid"], alpha),
                                    (70 - radius, 22 - radius // 4,
                                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 70, cy - 8))
        # Rising toxic bubbles
        for i, offset in enumerate((-22, -14, -6, 2, 10, 18, 26)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 22)
            alpha = _NS_grimstalker._alpha(210 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["mist_dark"], alpha),
                                       (sx, sy), 2)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["mist_mid"], alpha),
                                       (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                             (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 28), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 17)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 14 - radius, 110 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 8, 3, 170), (5, 8, 120, 12))
        pygame.draw.ellipse(shadow, (30, 60, 15, 100), (12, 10, 106, 8))
        surface.blit(shadow, (x - 65, y - 14))
    def _draw_toxic_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_grimstalker._alpha((85 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_grimstalker._aacircle(aura, (*_NS_grimstalker.PALETTE["mist_dark"], alpha),
                                           (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_grimstalker._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_grimstalker._aacircle(aura, (*_NS_grimstalker.PALETTE["mist_mid"], alpha),
                                           (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))
        # Floating toxic embers
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_grimstalker.PALETTE["toxic_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_grimstalker.PALETTE["mist_dark"], 200),
                            (5, 15, 150, 25), 3)
        pygame.draw.ellipse(ring, (*_NS_grimstalker.PALETTE["toxic_darkest"], 220),
                            (12, 18, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_grimstalker.PALETTE["toxic_dark"], 230),
                            (22, 20, 116, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 65)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_grimstalker.PALETTE["toxic_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_grimstalker.PALETTE["toxic_hot"],
                                        _NS_grimstalker._alpha(150 * pulse)),
                                (12, 10, 136, 34), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - JAWS OF THE BEAST (melee lunge bite)
    # ============================================================
    def _draw_jaws_ground(surface, boss, x, y, timer, phase):
        """Lunge line indicator on ground."""
        tx, ty = _NS_grimstalker._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Warning line from boss to target
            alpha = _NS_grimstalker._alpha(200 * (progress / 0.3))
            for w, c in [(6, _NS_grimstalker.PALETTE["toxic_darkest"]),
                         (3, _NS_grimstalker.PALETTE["toxic_mid"]),
                         (1, _NS_grimstalker.PALETTE["toxic_light"])]:
                pygame.draw.line(surface, (*c, alpha), (x, y + 30), (tx, ty), w)
    def _draw_jaws_foreground(surface, boss, x, y, timer, phase):
        """Boss lunges forward with bite; leaves toxic trail."""
        tx, ty = _NS_grimstalker._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress > 0.3 and progress < 0.85:
            # Lunge trail (green streaks)
            t = (progress - 0.3) / 0.55
            for i in range(7):
                trail_t = max(0, t - i * 0.06)
                px = int(x + (tx - x) * trail_t)
                py = int(y - 5 + (ty - y - 5) * trail_t)
                alpha = _NS_grimstalker._alpha(220 - i * 25)
                size = max(1, 7 - i)
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_darkest"], alpha),
                                           (px, py), size)
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_mid"], alpha),
                                           (px, py), max(1, size - 2))
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                           (px, py), max(1, size - 4))
            # BITE burst at target
            if t > 0.7:
                bt = (t - 0.7) / 0.3
                intensity = math.sin(bt * math.pi)
                # Bite chomp visualization (2 fang arcs)
                for side_mult in (-1, 1):
                    for i in range(5):
                        fang_x = tx + i * 3 * facing
                        fang_y = ty + side_mult * (8 - int(bt * 6))
                        alpha = _NS_grimstalker._alpha(240 * intensity)
                        pygame.draw.line(surface, (*_NS_grimstalker.PALETTE["fang_light"], alpha),
                                         (fang_x, fang_y),
                                         (fang_x, fang_y + side_mult * 4), 2)
                # Blood splash
                for i in range(8):
                    angle = i * math.pi / 4
                    br = int(15 * intensity)
                    bx = tx + int(math.cos(angle) * br)
                    by = ty + int(math.sin(angle) * br)
                    alpha = _NS_grimstalker._alpha(200 * intensity)
                    pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                     (bx, by, 2, 2))
                    pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_light"], alpha),
                                     (bx, by, 1, 1))
    # ============================================================
    # SKILL W - BLOOD HUNT (buff + hunt indicator)
    # ============================================================
    def _draw_bloodhunt_ground(surface, boss, x, y, timer, phase):
        """Red hunt indicator ring around target."""
        tx, ty = _NS_grimstalker._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Rotating red circles around target
        for i in range(2):
            r = 25 + i * 5 + int(math.sin(phase * 3 + i) * 3)
            alpha = _NS_grimstalker._alpha(220 - i * 60)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                       (tx, ty), r, 2)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_light"], alpha),
                                       (tx, ty), r, 1)
        # Crosshair
        pygame.draw.line(surface, _NS_grimstalker.PALETTE["hunt_light"],
                         (tx - 10, ty), (tx - 4, ty), 2)
        pygame.draw.line(surface, _NS_grimstalker.PALETTE["hunt_light"],
                         (tx + 4, ty), (tx + 10, ty), 2)
        pygame.draw.line(surface, _NS_grimstalker.PALETTE["hunt_light"],
                         (tx, ty - 10), (tx, ty - 4), 2)
        pygame.draw.line(surface, _NS_grimstalker.PALETTE["hunt_light"],
                         (tx, ty + 4), (tx, ty + 10), 2)
    def _draw_bloodhunt_foreground(surface, boss, x, y, timer, phase):
        """Red aura around boss + hunt line to target."""
        tx, ty = _NS_grimstalker._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Red aura around boss
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(30, 5, -3):
            alpha = _NS_grimstalker._alpha(60 * (30 - r) / 30 * pulse)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                       (x, y), r)
        # Hunt trail (dotted line to target)
        num_dots = 12
        for i in range(num_dots):
            dot_t = i / num_dots
            dx = int(x + (tx - x) * dot_t)
            dy = int(y - 5 + (ty - y - 5) * dot_t)
            offset = math.sin(phase * 2 + i * 0.5) * 2
            alpha = _NS_grimstalker._alpha(180 * pulse)
            pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                             (dx, dy + int(offset), 2, 2))
            pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_light"], alpha),
                             (dx, dy + int(offset), 1, 1))
    # ============================================================
    # SKILL E - PRIMAL HOWL (AoE fear rings)
    # ============================================================
    def _draw_howl_ground(surface, boss, x, y, timer, phase):
        """Expanding green rings on ground."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for ring_i in range(3):
            ring_t = max(0, progress - ring_i * 0.15)
            r = int(75 * min(1.0, ring_t * 2))
            if r < 3:
                continue
            alpha = _NS_grimstalker._alpha(240 * (1 - ring_t))
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["toxic_darkest"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["toxic_mid"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                (x - r + 6, y + 40 - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_howl_foreground(surface, boss, x, y, timer, phase):
        """Sound wave rings + speech-like glow at mouth."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Mouth glow (howling)
        mouth_x = x + facing * 22
        mouth_y = y - 8
        if progress < 0.7:
            howl_intensity = math.sin(progress * math.pi * 1.5)
            for r in range(8, 0, -1):
                alpha = _NS_grimstalker._alpha(200 * (8 - r) / 8 * howl_intensity)
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                           (mouth_x, mouth_y), r)
            _NS_grimstalker._aacircle(surface, _NS_grimstalker.PALETTE["toxic_hot"],
                                       (mouth_x, mouth_y), 3)
            _NS_grimstalker._aacircle(surface, _NS_grimstalker.PALETTE["toxic_shine"],
                                       (mouth_x, mouth_y), 1)
        # Expanding sound wave rings (3D perspective)
        for ring_i in range(4):
            ring_t = max(0, progress - ring_i * 0.12)
            if ring_t <= 0:
                continue
            r_expand = int(90 * ring_t)
            alpha = _NS_grimstalker._alpha(200 * (1 - ring_t))
            # Wave ring in 3D perspective (ellipse tilted)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_mid"], alpha),
                                       (x, y), r_expand, 2)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["toxic_light"], alpha),
                                       (x, y), max(1, r_expand - 2), 1)
        # ! marks (fear indicators around expanding radius)
        r_current = int(70 * min(1.0, progress * 1.5))
        if r_current > 20:
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.2
                mx = x + int(math.cos(angle) * r_current)
                my = y + int(math.sin(angle) * r_current * 0.4)
                # ! mark
                alpha = _NS_grimstalker._alpha(255 * (1 - progress))
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_hot"], alpha),
                                 (mx, my - 5, 2, 3))
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_hot"], alpha),
                                 (mx, my - 1, 2, 2))
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["toxic_shine"], alpha),
                                 (mx, my - 5, 1, 3))
    # ============================================================
    # SKILL R - INFINITE DUPRESS (ultimate leap + suppress)
    # ============================================================
    def _draw_dupress_ground(surface, boss, x, y, timer, phase):
        """Red impact circle at target."""
        tx, ty = _NS_grimstalker._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning circle grows
            t = progress / 0.4
            r = int(40 * t)
            alpha = _NS_grimstalker._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["hunt_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            # Blood pool after impact
            t = (progress - 0.4) / 0.6
            r = int(45 * (1 - t * 0.3))
            alpha = _NS_grimstalker._alpha(230 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["hunt_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
    def _draw_dupress_foreground(surface, boss, x, y, timer, phase):
        """Boss leaps in arc to target; slams down; suppression FX."""
        tx, ty = _NS_grimstalker._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Leap phase: red comet trail from boss position to target arc
            t = progress / 0.4
            # Arc trajectory
            start_x, start_y = x, y
            arc_h = 60
            # Interpolate along arc
            for i in range(8):
                trail_t = max(0, t - i * 0.06)
                # Parabolic arc
                ax = start_x + (tx - start_x) * trail_t
                ay = start_y + (ty - start_y) * trail_t - math.sin(trail_t * math.pi) * arc_h
                alpha = _NS_grimstalker._alpha(230 - i * 25)
                size = max(1, 8 - i)
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_dark"], alpha),
                                           (int(ax), int(ay)), size)
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                           (int(ax), int(ay)), max(1, size - 2))
                _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_light"], alpha),
                                           (int(ax), int(ay)), max(1, size - 4))
        elif progress < 0.55:
            # IMPACT phase
            t = (progress - 0.4) / 0.15
            intensity = math.sin(t * math.pi)
            r = int(30 + t * 25)
            alpha = _NS_grimstalker._alpha(250 * intensity)
            # Big red shockwave
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_dark"], alpha),
                                       (tx, ty), r + 3, 3)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], alpha),
                                       (tx, ty), r, 3)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["hunt_light"], alpha),
                                       (tx, ty), max(1, r - 6), 2)
            _NS_grimstalker._aacircle(surface, (*_NS_grimstalker.PALETTE["white"], alpha),
                                       (tx, ty), max(1, r // 4))
            # Blood splashes radial
            for i in range(12):
                angle = i * math.pi / 6
                bx = tx + int(math.cos(angle) * r)
                by = ty + int(math.sin(angle) * r * 0.7)
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_light"], alpha),
                                 (bx, by, 3, 3))
                pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["white"], alpha),
                                 (bx, by, 1, 1))
        else:
            # SUPPRESS phase: claws pinning + blood particles
            t = (progress - 0.55) / 0.45
            # Pin claws (X marks around target)
            claw_alpha = _NS_grimstalker._alpha(200 * (1 - t))
            for angle_deg in (30, 150, 210, 330):
                angle = math.radians(angle_deg)
                dist = 12
                clx1 = tx + int(math.cos(angle) * dist)
                cly1 = ty + int(math.sin(angle) * dist)
                clx2 = tx + int(math.cos(angle) * (dist + 8))
                cly2 = ty + int(math.sin(angle) * (dist + 8))
                pygame.draw.line(surface, (*_NS_grimstalker.PALETTE["fang_dark"], claw_alpha),
                                 (clx1, cly1), (clx2, cly2), 2)
                pygame.draw.line(surface, (*_NS_grimstalker.PALETTE["fang_light"], claw_alpha),
                                 (clx1, cly1), (clx2, cly2), 1)
            # Blood particles rising
            for i in range(10):
                p_t = (phase * 0.8 + i * 0.1) % 1.0
                px_p = tx + int(math.sin(phase + i) * 15)
                py_p = ty - int(p_t * 20)
                p_alpha = _NS_grimstalker._alpha(220 * (1 - p_t) * (1 - t))
                if p_alpha > 0:
                    pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_mid"], p_alpha),
                                     (px_p, py_p, 2, 2))
                    pygame.draw.rect(surface, (*_NS_grimstalker.PALETTE["hunt_light"], p_alpha),
                                     (px_p, py_p, 1, 1))



# ====================================================================
# KRYVOXAR (CRYSTALBORNE WRAITH) - Mini Boss
# ====================================================================

class _NS_kryvoxar:
    """Namespace kryvoxar - mini boss kristal melayang."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Crystal cyan (main theme)
        "crystal_darkest": (5, 20, 30),
        "crystal_dark": (15, 55, 75),
        "crystal_mid": (40, 130, 165),
        "crystal_light": (95, 210, 240),
        "crystal_shine": (180, 245, 255),
        "crystal_hot": (230, 255, 255),
        # Skin (pale ghostly)
        "skin_darkest": (35, 30, 45),
        "skin_dark": (80, 75, 95),
        "skin_mid": (150, 145, 165),
        "skin_light": (210, 210, 225),
        "skin_shine": (240, 245, 250),
        # Hair (white-silver)
        "hair_dark": (60, 65, 80),
        "hair_mid": (140, 150, 170),
        "hair_light": (220, 225, 235),
        "hair_shine": (250, 252, 255),
        # Armor (dark stone with gold trim)
        "armor_darkest": (10, 10, 18),
        "armor_dark": (28, 30, 42),
        "armor_mid": (55, 60, 78),
        "armor_light": (100, 108, 130),
        "gold_dark": (95, 70, 20),
        "gold_mid": (185, 145, 55),
        "gold_light": (240, 210, 120),
        # Eye (glowing cyan)
        "eye_socket": (5, 8, 12),
        "eye_dark": (20, 60, 90),
        "eye_mid": (80, 180, 220),
        "eye_light": (180, 240, 255),
        "eye_glow": (255, 255, 255),
        # Ambient mist
        "mist_dark": (10, 30, 45),
        "mist_mid": (40, 90, 120),
        "mist_light": (120, 200, 230),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kryvoxar._clamp(color)
        if _NS_kryvoxar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kryvoxar._clamp(color)
        if _NS_kryvoxar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kryvoxar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kryvoxar(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_kryvoxar._update_krv_attack_anim(boss)
        attacking = (
            getattr(boss, "_krv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_kryvoxar._draw_crystal_aura(surface, x, y, pulse)
        _NS_kryvoxar._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_kryvoxar._draw_erosion_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kryvoxar._draw_bloodstone_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kryvoxar._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        # Body - always floating; attack triggers swing animation
        floating_bob = math.sin(pulse * 0.8) * 5
        if attacking:
            _NS_kryvoxar._draw_krv_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_kryvoxar._draw_krv_idle(surface, boss, x, y - floating_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_kryvoxar._draw_crystal_lance_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kryvoxar._draw_erosion_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kryvoxar._draw_bloodstone_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kryvoxar._draw_dash_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_krv_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_krv_previous_timer", 0))
        active = bool(getattr(boss, "_krv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._krv_attack_active = True
            boss._krv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._krv_attack_frame = int(getattr(boss, "_krv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._krv_attack_active = False
            boss._krv_attack_frame = 0
            active = False
        boss._krv_previous_timer = timer
        boss._krv_attack_progress = (
            min(1.0, getattr(boss, "_krv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_krv_idle(surface, boss, x, y):
        _NS_kryvoxar._draw_shadow(surface, x, y + 50)
        _NS_kryvoxar._draw_floating_particles(surface, x, y + 20, boss.pulse)
        _NS_kryvoxar._draw_krv_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_krv_attack(surface, boss, x, y):
        progress = getattr(boss, "_krv_attack_progress", 0.0)
        # Swing animation: wind-up → swing → recovery
        if progress < 0.35:
            t = progress / 0.35
            swing_offset = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            swing_offset = int((-3 + t * 10)) * boss.direction
            lift = int(2 - t * 3)
        else:
            t = (progress - 0.6) / 0.4
            swing_offset = int(7 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_kryvoxar._draw_shadow(surface, x + swing_offset, y + 50)
        _NS_kryvoxar._draw_floating_particles(surface, x + swing_offset, y + 20, boss.pulse, intense=True)
        _NS_kryvoxar._draw_krv_body(surface, x + swing_offset, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Swing slash arc
        _NS_kryvoxar._draw_swing_slash(surface, x + swing_offset, y - lift,
                                        boss.direction, progress)
    # ============================================================
    # BODY (humanoid wraith with crystals)
    # ============================================================
    def _draw_krv_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw floating wraith body with crystal armor."""
        # Order: cape/back-crystals → torso → arms → head → hair-crystals → floating shards
        _NS_kryvoxar._draw_back_crystals(surface, cx, cy - 8, facing, phase)
        _NS_kryvoxar._draw_lower_ghost_wisp(surface, cx, cy + 8, phase)  # replaces legs
        _NS_kryvoxar._draw_torso(surface, cx, cy, facing, phase)
        _NS_kryvoxar._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_kryvoxar._draw_head(surface, cx + facing * 2, cy - 22, facing, phase)
        _NS_kryvoxar._draw_shoulder_crystals(surface, cx, cy - 10, facing, phase)
    def _draw_lower_ghost_wisp(surface, cx, cy, phase):
        """Ghostly trailing lower body (no legs, floats)."""
        wisp_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pulse = math.sin(phase * 0.9) * 0.2 + 0.8
        # Layered translucent wisp shape
        for i, (w, h, alpha_v) in enumerate([
            (28, 40, 90), (22, 34, 130), (16, 28, 170), (10, 22, 210)
        ]):
            wobble = math.sin(phase * 1.2 + i) * 2
            pygame.draw.ellipse(
                wisp_surf,
                (*_NS_kryvoxar.PALETTE["armor_dark"], int(alpha_v * pulse)),
                (30 - w // 2 + int(wobble), 20, w, h),
            )
        for i, (w, h, alpha_v) in enumerate([
            (12, 22, 140), (8, 18, 180)
        ]):
            wobble = math.sin(phase * 1.5 + i) * 1
            pygame.draw.ellipse(
                wisp_surf,
                (*_NS_kryvoxar.PALETTE["crystal_dark"], int(alpha_v * pulse)),
                (30 - w // 2 + int(wobble), 24, w, h),
            )
        # Tail-like drip
        for i in range(5):
            drip_t = (phase * 0.4 + i * 0.2) % 1.0
            dy = 30 + int(drip_t * 25)
            dx = 30 + int(math.sin(phase + i) * 3)
            alpha = _NS_kryvoxar._alpha(200 * (1 - drip_t) * pulse)
            _NS_kryvoxar._aacircle(wisp_surf, (*_NS_kryvoxar.PALETTE["crystal_mid"], alpha), (dx, dy), 2)
            pygame.draw.rect(wisp_surf, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha), (dx, dy, 1, 1))
        surface.blit(wisp_surf, (cx - 30, cy - 10))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular bare torso with faint crystal veins."""
        breath = math.sin(phase * 0.7) * 1
        torso = [
            (cx - 10, cy - 10),
            (cx - 12, cy - 4),
            (cx - 10, cy + 6),
            (cx - 6, cy + 12),
            (cx + 6, cy + 12),
            (cx + 10, cy + 6),
            (cx + 12, cy - 4),
            (cx + 10, cy - 10),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ]
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso])
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_darkest"], torso)
        # Skin shading
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_dark"], [
            (cx - 10, cy - 8),
            (cx - 11, cy - 3),
            (cx - 9, cy + 5),
            (cx - 5, cy + 10),
            (cx + 5, cy + 10),
            (cx + 9, cy + 5),
            (cx + 11, cy - 3),
            (cx + 10, cy - 8),
            (cx + 3, cy - 10),
            (cx - 3, cy - 10),
        ])
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_mid"], [
            (cx - 7, cy - 6),
            (cx - 8, cy),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 8, cy),
            (cx + 7, cy - 6),
            (cx + 2, cy - 8),
            (cx - 2, cy - 8),
        ])
        # Chest highlight
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_light"], [
            (cx - 4, cy - 4),
            (cx - 5, cy),
            (cx - 2, cy + 3),
            (cx + 2, cy + 3),
            (cx + 5, cy),
            (cx + 4, cy - 4),
        ])
        # Abs line
        pygame.draw.line(surface, _NS_kryvoxar.PALETTE["skin_darkest"],
                         (cx, cy - 4), (cx, cy + 8), 1)
        pygame.draw.line(surface, _NS_kryvoxar.PALETTE["skin_darkest"],
                         (cx - 4, cy + 2), (cx + 4, cy + 2), 1)
        pygame.draw.line(surface, _NS_kryvoxar.PALETTE["skin_darkest"],
                         (cx - 4, cy + 6), (cx + 4, cy + 6), 1)
        # Crystal veins (pulsing cyan)
        vein_alpha = _NS_kryvoxar._alpha(180 + math.sin(phase * 2) * 60)
        for pts in [
            [(cx - 6, cy - 8), (cx - 4, cy - 4), (cx - 5, cy + 2)],
            [(cx + 6, cy - 8), (cx + 4, cy - 4), (cx + 5, cy + 2)],
        ]:
            for i in range(len(pts) - 1):
                _NS_kryvoxar._aaline(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], vein_alpha),
                                      pts[i], pts[i + 1], 1)
        # Gold belt
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["gold_dark"], (cx - 10, cy + 10, 20, 3))
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["gold_mid"], (cx - 9, cy + 11, 18, 1))
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["gold_light"], (cx - 2, cy + 11, 4, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two muscular arms with crystal gauntlets."""
        # Base arm angles
        idle_sway = math.sin(phase * 0.8) * 3
        # FAR ARM (behind body)
        far_shoulder = (cx - facing * 8, cy - 6)
        far_elbow = (cx - facing * 12, cy + 2)
        far_hand = (cx - facing * 14, cy + 10 + int(idle_sway * 0.3))
        _NS_kryvoxar._draw_arm_segment(surface, far_shoulder, far_elbow, far_hand,
                                        facing, dark=True)
        # NEAR ARM (front) — swings during attack
        if action == "attack":
            # Swing arc: wind-up back → forward slash
            if attack_progress < 0.35:
                # Wind-up: arm back and up
                t = attack_progress / 0.35
                angle = math.radians(-30 - t * 60) * facing
            elif attack_progress < 0.6:
                # Slash: arm swings forward
                t = (attack_progress - 0.35) / 0.25
                angle = math.radians(-90 + t * 140) * facing
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                angle = math.radians(50 - t * 50) * facing
            shoulder = (cx + facing * 8, cy - 6)
            arm_len = 14
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            hand = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_kryvoxar._draw_arm_segment(surface, shoulder, elbow, hand, facing, dark=False)
            # Big crystal fist/gauntlet at hand
            _NS_kryvoxar._draw_crystal_gauntlet(surface, hand, facing, phase, big=True)
        else:
            near_shoulder = (cx + facing * 8, cy - 6)
            near_elbow = (cx + facing * 12, cy + 3 + int(idle_sway * 0.3))
            near_hand = (cx + facing * 14, cy + 12 + int(idle_sway * 0.5))
            _NS_kryvoxar._draw_arm_segment(surface, near_shoulder, near_elbow, near_hand,
                                            facing, dark=False)
            _NS_kryvoxar._draw_crystal_gauntlet(surface, near_hand, facing, phase)
    def _draw_arm_segment(surface, shoulder, elbow, hand, facing, dark=False):
        """Muscular arm with 2 segments."""
        skin_dark_c = _NS_kryvoxar.PALETTE["skin_darkest"] if dark else _NS_kryvoxar.PALETTE["skin_dark"]
        skin_mid_c = _NS_kryvoxar.PALETTE["skin_dark"] if dark else _NS_kryvoxar.PALETTE["skin_mid"]
        skin_light_c = _NS_kryvoxar.PALETTE["skin_mid"] if dark else _NS_kryvoxar.PALETTE["skin_light"]
        # Shadow
        _NS_kryvoxar._aaline(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                              (shoulder[0] + 2, shoulder[1] + 2),
                              (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_kryvoxar._aaline(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                              (elbow[0] + 2, elbow[1] + 2),
                              (hand[0] + 2, hand[1] + 2), 5)
        # Upper arm
        _NS_kryvoxar._aaline(surface, _NS_kryvoxar.PALETTE["skin_darkest"], shoulder, elbow, 6)
        _NS_kryvoxar._aaline(surface, skin_dark_c, shoulder, elbow, 5)
        _NS_kryvoxar._aaline(surface, skin_mid_c,
                              (shoulder[0], shoulder[1] - 1), (elbow[0], elbow[1] - 1), 3)
        _NS_kryvoxar._aaline(surface, skin_light_c,
                              (shoulder[0], shoulder[1] - 1), (elbow[0], elbow[1] - 1), 1)
        # Forearm
        _NS_kryvoxar._aaline(surface, _NS_kryvoxar.PALETTE["skin_darkest"], elbow, hand, 5)
        _NS_kryvoxar._aaline(surface, skin_dark_c, elbow, hand, 4)
        _NS_kryvoxar._aaline(surface, skin_mid_c,
                              (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 2)
    def _draw_crystal_gauntlet(surface, hand, facing, phase, big=False):
        """Crystal shard cluster on hand."""
        size = 6 if big else 4
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Base
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                         (hand[0] - size, hand[1] - size, size * 2 + 1, size * 2 + 1))
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["armor_dark"],
                         (hand[0] - size, hand[1] - size, size * 2, size * 2))
        # Multiple crystal shards jutting out
        shards = [
            (hand[0], hand[1] - size - 3, hand[0] - 2, hand[1] - size + 1, hand[0] + 2, hand[1] - size + 1),
            (hand[0] - size - 2, hand[1], hand[0] - size + 1, hand[1] - 2, hand[0] - size + 1, hand[1] + 2),
            (hand[0] + size + 2, hand[1], hand[0] + size - 1, hand[1] - 2, hand[0] + size - 1, hand[1] + 2),
        ]
        if big:
            shards.append((hand[0] + facing * (size + 4), hand[1] - 2,
                           hand[0] + facing * size, hand[1] - 4,
                           hand[0] + facing * size, hand[1] + 1))
        for s in shards:
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                                [(s[0] + 1, s[1] + 1), (s[2] + 1, s[3] + 1), (s[4] + 1, s[5] + 1)])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"],
                                [(s[0], s[1]), (s[2], s[3]), (s[4], s[5])])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_dark"],
                                [(s[0], s[1]),
                                 (int((s[0] + s[2]) / 2), int((s[1] + s[3]) / 2)),
                                 (int((s[0] + s[4]) / 2), int((s[1] + s[5]) / 2))])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"],
                                [(s[0], s[1]),
                                 (int((s[0] + s[2]) / 2 + s[0]) / 2,
                                  int((s[1] + s[3]) / 2 + s[1]) / 2),
                                 (int((s[0] + s[4]) / 2 + s[0]) / 2,
                                  int((s[1] + s[5]) / 2 + s[1]) / 2)])
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_light"],
                             (s[0], s[1], 1, 1))
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"],
                             (s[0], s[1], 1, 1))
        # Glow aura around gauntlet
        glow_r = size + 4
        for r in range(glow_r, 0, -1):
            alpha = _NS_kryvoxar._alpha(60 * (glow_r - r) / glow_r * pulse)
            _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha), hand, r)
    def _draw_head(surface, cx, cy, facing, phase):
        """Head with pale skin, white hair, glowing cyan eyes."""
        # Skull shape
        head_shape = [
            (cx - 7, cy + 6), (cx - 8, cy + 2), (cx - 8, cy - 4),
            (cx - 5, cy - 8), (cx, cy - 9), (cx + 5, cy - 8),
            (cx + 8, cy - 4), (cx + 8, cy + 2), (cx + 7, cy + 6),
            (cx + 4, cy + 8), (cx - 4, cy + 8),
        ]
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in head_shape])
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_darkest"], head_shape)
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_dark"], [
            (cx - 7, cy + 5), (cx - 7, cy - 3), (cx - 4, cy - 7),
            (cx, cy - 8), (cx + 4, cy - 7), (cx + 7, cy - 3),
            (cx + 7, cy + 5), (cx + 3, cy + 7), (cx - 3, cy + 7),
        ])
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_mid"], [
            (cx - 5, cy + 3), (cx - 6, cy - 2), (cx - 3, cy - 6),
            (cx + 3, cy - 6), (cx + 6, cy - 2), (cx + 5, cy + 3),
        ])
        # Highlight cheek
        _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["skin_light"], [
            (cx + facing * 2, cy - 3),
            (cx + facing * 5, cy - 1),
            (cx + facing * 4, cy + 2),
            (cx + facing * 1, cy),
        ])
        # HAIR (spiky white, swept back)
        _NS_kryvoxar._draw_hair(surface, cx, cy, facing, phase)
        # Eyes (glowing cyan)
        _NS_kryvoxar._draw_glow_eye(surface, cx - 3, cy - 2, phase)
        _NS_kryvoxar._draw_glow_eye(surface, cx + 3, cy - 2, phase)
        # Nose shadow
        pygame.draw.line(surface, _NS_kryvoxar.PALETTE["skin_darkest"],
                         (cx, cy - 1), (cx, cy + 2), 1)
        # Mouth (stern)
        pygame.draw.line(surface, _NS_kryvoxar.PALETTE["skin_darkest"],
                         (cx - 2, cy + 4), (cx + 2, cy + 4), 1)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Spiky white hair with slight sway."""
        sway = math.sin(phase * 0.6) * 1
        # Back spikes
        for i, (bx, by, tx, ty) in enumerate([
            (-6, -6, -10 - facing, -12),
            (-3, -8, -6 - facing, -14),
            (0, -9, -2, -15),
            (3, -8, 4 + facing, -13),
            (6, -6, 9 + facing, -11),
        ]):
            spike_tip_y = cy + ty + int(sway)
            spike_tip_x = cx + tx
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"], [
                (cx + bx + 1, cy + by + 1),
                (spike_tip_x + 1, spike_tip_y + 1),
                (cx + bx + 3, cy + by + 1),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["hair_dark"], [
                (cx + bx, cy + by),
                (spike_tip_x, spike_tip_y),
                (cx + bx + 2, cy + by),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["hair_mid"], [
                (cx + bx, cy + by),
                (int((cx + bx + spike_tip_x) / 2), int((cy + by + spike_tip_y) / 2)),
                (cx + bx + 1, cy + by),
            ])
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["hair_light"],
                             (spike_tip_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["hair_shine"],
                             (spike_tip_x, spike_tip_y, 1, 1))
    def _draw_glow_eye(surface, ex, ey, phase):
        """Bright cyan glowing eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Socket
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["eye_socket"], (ex - 1, ey - 1, 3, 2))
        # Glow halo
        for r in range(4, 0, -1):
            alpha = _NS_kryvoxar._alpha(100 * (4 - r) / 4 * pulse)
            _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["eye_mid"], alpha), (ex, ey), r)
        # Core
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["eye_dark"], (ex - 1, ey - 1, 3, 2))
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["eye_mid"], (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["eye_light"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_back_crystals(surface, cx, cy, facing, phase):
        """Large crystal cluster growing from back (like wings)."""
        pulse = math.sin(phase * 0.5) * 0.2 + 0.8
        for side_mult in (-1, 1):
            base_x = cx + side_mult * 4
            base_y = cy
            # Multiple large shards
            for i, (dx, dy, length, width) in enumerate([
                (side_mult * 6, -4, 22, 5),
                (side_mult * 10, -2, 26, 4),
                (side_mult * 12, 4, 20, 4),
                (side_mult * 8, 8, 16, 3),
            ]):
                tip_x = base_x + dx + side_mult * length // 2
                tip_y = base_y + dy - length // 2
                bx = base_x + dx
                by = base_y + dy
                # Perpendicular for base width
                perp_x = -side_mult
                perp_y = 0
                a = (bx + perp_x * width, by + width)
                b = (bx - perp_x * width, by - width // 2)
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                                    [(tip_x + 2, tip_y + 2), (a[0] + 2, a[1] + 2),
                                     (b[0] + 2, b[1] + 2)])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"],
                                    [(tip_x, tip_y), a, b])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_dark"],
                                    [(tip_x, tip_y),
                                     (int((tip_x + a[0]) / 2), int((tip_y + a[1]) / 2)),
                                     (int((tip_x + b[0]) / 2), int((tip_y + b[1]) / 2))])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"], [
                    (tip_x, tip_y),
                    (int((tip_x * 3 + a[0]) / 4), int((tip_y * 3 + a[1]) / 4)),
                    (int((tip_x * 3 + b[0]) / 4), int((tip_y * 3 + b[1]) / 4)),
                ])
                # Highlight edge
                pygame.draw.line(surface, _NS_kryvoxar.PALETTE["crystal_light"],
                                 (tip_x, tip_y),
                                 (int((tip_x + b[0]) / 2), int((tip_y + b[1]) / 2)), 1)
                # Tip sparkle
                pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_shine"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"],
                                 (tip_x, tip_y, 1, 1))
    def _draw_shoulder_crystals(surface, cx, cy, facing, phase):
        """Sharp crystals jutting from shoulders."""
        for side in (-1, 1):
            base_x = cx + side * 9
            base_y = cy + 2
            tip_x = base_x + side * 3
            tip_y = base_y - 8
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x - 2 + 1, base_y + 1),
                (base_x + 3 + 1, base_y + 1),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"], [
                (tip_x, tip_y), (base_x - 2, base_y), (base_x + 3, base_y),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_dark"], [
                (tip_x, tip_y),
                (int((tip_x + base_x - 2) / 2), int((tip_y + base_y) / 2)),
                (int((tip_x + base_x + 3) / 2), int((tip_y + base_y) / 2)),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"], [
                (tip_x, tip_y),
                (int((tip_x * 3 + base_x - 2) / 4), int((tip_y * 3 + base_y) / 4)),
                (int((tip_x * 3 + base_x + 3) / 4), int((tip_y * 3 + base_y) / 4)),
            ])
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_light"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"], (tip_x, tip_y, 1, 1))
    # ============================================================
    # SWING SLASH (melee attack arc)
    # ============================================================
    def _draw_swing_slash(surface, cx, cy, facing, progress):
        """Cyan crescent slash arc during attack swing."""
        # Only visible during actual slash frames
        if progress < 0.35 or progress > 0.75:
            return
        # Slash intensity
        t = (progress - 0.35) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_kryvoxar._alpha(255 * intensity)
        # Arc center - in front of body
        arc_cx = cx + facing * 14
        arc_cy = cy + 4
        arc_r = 18
        # Draw slash arc as series of segments
        num_segments = 12
        start_angle = math.radians(-70) if facing > 0 else math.radians(180 + 70)
        end_angle = math.radians(70) if facing > 0 else math.radians(180 - 70)
        # Current sweep progress
        sweep = start_angle + (end_angle - start_angle) * t
        # Slash trail from start to current angle
        trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
        prev_pt = None
        for i in range(num_segments + 1):
            seg_t = i / num_segments
            angle = trail_start + (sweep - trail_start) * seg_t
            px = arc_cx + int(math.cos(angle) * arc_r)
            py = arc_cy + int(math.sin(angle) * arc_r)
            if prev_pt is not None:
                # Multi-layer slash line
                for thickness, color in [
                    (6, (*_NS_kryvoxar.PALETTE["crystal_darkest"], alpha // 3)),
                    (4, (*_NS_kryvoxar.PALETTE["crystal_dark"], alpha // 2)),
                    (3, (*_NS_kryvoxar.PALETTE["crystal_mid"], alpha)),
                    (2, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha)),
                    (1, (*_NS_kryvoxar.PALETTE["crystal_shine"], alpha)),
                ]:
                    pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
            prev_pt = (px, py)
        # Sparks along arc
        for i in range(6):
            angle = trail_start + (sweep - trail_start) * (i / 6)
            spark_r = arc_r + int(math.sin(i + progress * 10) * 3)
            sx = arc_cx + int(math.cos(angle) * spark_r)
            sy = arc_cy + int(math.sin(angle) * spark_r)
            pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["white"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # FLOATING PARTICLES (ambient below body)
    # ============================================================
    def _draw_floating_particles(surface, cx, cy, phase, intense=False):
        """Crystal shards floating around wraith."""
        strength = 1.4 if intense else 1.0
        for i in range(10):
            t = (phase * 0.35 + i * 0.11) % 1.0
            angle = i * math.pi / 5 + phase * 0.3
            radius = 30 + int(math.sin(phase + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy + int(math.sin(angle) * radius * 0.5) - int(t * 15)
            alpha = _NS_kryvoxar._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Small crystal shard (triangle)
            _NS_kryvoxar._poly(surface, (*_NS_kryvoxar.PALETTE["crystal_dark"], alpha),
                                [(px, py - 2), (px - 2, py + 1), (px + 2, py + 1)])
            _NS_kryvoxar._poly(surface, (*_NS_kryvoxar.PALETTE["crystal_mid"], alpha),
                                [(px, py - 2), (px - 1, py), (px + 1, py)])
            pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_shine"], alpha),
                             (px, py - 2, 1, 1))
        # Small sparks
        for i in range(6):
            spark_t = (phase * 0.6 + i * 0.17) % 1.0
            sx = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(spark_t * 20)
            alpha = _NS_kryvoxar._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_hot"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius, 80 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 8, 12, 170), (5, 7, 90, 10))
        surface.blit(shadow, (x - 50, y - 12))
    def _draw_crystal_aura(surface, x, y, phase):
        """Cyan aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_kryvoxar._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_kryvoxar._aacircle(aura, (*_NS_kryvoxar.PALETTE["mist_dark"], alpha),
                                        (100, 90), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_kryvoxar._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kryvoxar._aacircle(aura, (*_NS_kryvoxar.PALETTE["mist_mid"], alpha),
                                        (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Floating outer sparks
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 45 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring under floating boss."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kryvoxar.PALETTE["mist_dark"], 200),
                            (5, 15, 150, 25), 3)
        pygame.draw.ellipse(ring, (*_NS_kryvoxar.PALETTE["crystal_darkest"], 220),
                            (12, 18, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_kryvoxar.PALETTE["crystal_dark"], 230),
                            (22, 20, 116, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 65)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_kryvoxar.PALETTE["crystal_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kryvoxar.PALETTE["crystal_hot"],
                                        _NS_kryvoxar._alpha(150 * pulse)),
                                (12, 10, 136, 34), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - CRYSTAL LANCE (range projectile)
    # ============================================================
    def _draw_crystal_lance_skill(surface, boss, x, y, timer, phase):
        """Crystal spear projectile toward target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kryvoxar._target_position(boss, x, y)
        if progress < 0.25:
            # Charge in hand
            t = progress / 0.25
            hand_x = x + facing * 20
            hand_y = y + 8
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kryvoxar._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_kryvoxar._aacircle(surface, _NS_kryvoxar.PALETTE["crystal_mid"], (hand_x, hand_y), cr - 2)
            _NS_kryvoxar._aacircle(surface, _NS_kryvoxar.PALETTE["crystal_light"], (hand_x, hand_y),
                                    max(1, cr - 4))
            _NS_kryvoxar._aacircle(surface, _NS_kryvoxar.PALETTE["crystal_shine"], (hand_x, hand_y),
                                    max(1, cr - 6))
            # Sparks
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 2))
                sy = hand_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 24
            start_y = y + 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Lance direction
            dx = tx - start_x
            dy = ty - start_y
            length = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / length, dy / length
            perp_x, perp_y = -uy, ux
            # Lance body (elongated crystal shard)
            lance_len = 18
            tip = (bx + int(ux * lance_len // 2), by + int(uy * lance_len // 2))
            tail = (bx - int(ux * lance_len // 2), by - int(uy * lance_len // 2))
            side_a = (bx + int(perp_x * 3), by + int(perp_y * 3))
            side_b = (bx - int(perp_x * 3), by - int(perp_y * 3))
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                                [(tip[0] + 2, tip[1] + 2), (side_a[0] + 2, side_a[1] + 2),
                                 (tail[0] + 2, tail[1] + 2), (side_b[0] + 2, side_b[1] + 2)])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"],
                                [tip, side_a, tail, side_b])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_dark"],
                                [tip,
                                 (int((tip[0] + side_a[0]) / 2), int((tip[1] + side_a[1]) / 2)),
                                 (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)),
                                 (int((tip[0] + side_b[0]) / 2), int((tip[1] + side_b[1]) / 2))])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"], [
                tip,
                (int((tip[0] * 3 + side_a[0]) / 4), int((tip[1] * 3 + side_a[1]) / 4)),
                (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)),
                (int((tip[0] * 3 + side_b[0]) / 4), int((tip[1] * 3 + side_b[1]) / 4)),
            ])
            pygame.draw.line(surface, _NS_kryvoxar.PALETTE["crystal_light"],
                             tip, (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)), 1)
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"], (tip[0], tip[1], 1, 1))
            # Comet trail behind lance
            for i in range(1, 10):
                trail_t = max(0.0, t - i * 0.045)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kryvoxar._alpha(220 - i * 22)
                size = max(1, 6 - i)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_dark"], alpha),
                                        (px, py), size)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_mid"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha),
                                        (px, py), max(1, size - 2))
            # Big glow around lance head
            for r in range(12, 3, -2):
                alpha = _NS_kryvoxar._alpha(80 * (12 - r) / 12)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha),
                                        (bx, by), r)
            # Impact burst
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(10 + st * 25)
                alpha = _NS_kryvoxar._alpha(240 * (1 - st))
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha),
                                        (tx, ty), max(1, radius - 10), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["white"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - ENERGY EROSION (AoE ground slam + shield)
    # ============================================================
    def _draw_erosion_ground(surface, boss, x, y, timer, phase):
        """Crystal shards erupt from ground under boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_kryvoxar.PALETTE["crystal_darkest"], 200),
                                (x - r, y + 30 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kryvoxar.PALETTE["crystal_dark"], 180),
                                (x - r + 3, y + 30 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_kryvoxar.PALETTE["crystal_mid"], 130),
                                (x - r + 8, y + 30 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_erosion_foreground(surface, boss, x, y, timer, phase):
        """Crystal spikes rising from ground + shield forming."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Erupting crystal spikes around boss
        num_spikes = 8
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + phase * 0.1
            dist = 35 + int(math.sin(phase * 2 + i) * 5)
            sx = x + int(math.cos(angle) * dist)
            sy = y + 40 + int(math.sin(angle) * dist * 0.4)
            # Growth animation
            grow_t = min(1.0, progress * 2 - i * 0.05)
            if grow_t <= 0:
                continue
            spike_h = int(20 * grow_t)
            tip_y = sy - spike_h
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"], [
                (sx + 1, tip_y + 1), (sx - 4 + 1, sy + 1), (sx + 4 + 1, sy + 1),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"],
                                [(sx, tip_y), (sx - 4, sy), (sx + 4, sy)])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_dark"], [
                (sx, tip_y),
                (int((sx + sx - 4) / 2), int((tip_y + sy) / 2)),
                (int((sx + sx + 4) / 2), int((tip_y + sy) / 2)),
            ])
            _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"], [
                (sx, tip_y),
                (int((sx * 3 + sx - 4) / 4), int((tip_y * 3 + sy) / 4)),
                (int((sx * 3 + sx + 4) / 4), int((tip_y * 3 + sy) / 4)),
            ])
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_light"], (sx, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_shine"], (sx, tip_y, 1, 1))
        # Shield bubble forming around boss
        if progress > 0.3:
            shield_t = min(1.0, (progress - 0.3) / 0.7)
            shield_r = int(45 * shield_t)
            shield_alpha = _NS_kryvoxar._alpha(150 * shield_t)
            for i, thickness in enumerate((3, 2, 1)):
                _NS_kryvoxar._aacircle(surface,
                                        (*_NS_kryvoxar.PALETTE["crystal_mid"], shield_alpha - i * 30),
                                        (x, y), shield_r - i, thickness)
            # Rotating sparkles
            for i in range(12):
                angle = phase * 1.5 + i * math.pi / 6
                sx = x + int(math.cos(angle) * shield_r)
                sy = y + int(math.sin(angle) * shield_r)
                pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_hot"], shield_alpha),
                                 (sx, sy, 2, 2))
    # ============================================================
    # SKILL E - CRYSTAL DASH (blink with trail)
    # ============================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Rings on ground during dash."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(25 + i * 6 + progress * 20)
            alpha = _NS_kryvoxar._alpha(200 * (1 - progress) - i * 40)
            if alpha > 0:
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_mid"], alpha),
                                        (x, y + 40), r, 2)
    def _draw_dash_foreground(surface, boss, x, y, timer, phase):
        """Afterimage trail during dash."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # After-images stretching behind
        for i in range(6):
            offset = i * 12 * -facing
            alpha = _NS_kryvoxar._alpha(180 * (1 - progress) * (1 - i / 6))
            if alpha <= 0:
                continue
            # Ghost silhouette
            afterimage = pygame.Surface((30, 60), pygame.SRCALPHA)
            for r in range(15, 0, -2):
                _NS_kryvoxar._aacircle(afterimage,
                                        (*_NS_kryvoxar.PALETTE["crystal_light"],
                                         alpha * (15 - r) // 15),
                                        (15, 30), r)
            surface.blit(afterimage, (x + offset - 15, y - 30))
        # Dash streak lines
        for i in range(8):
            streak_y = y - 10 + i * 5
            streak_len = int(50 * (1 - progress))
            end_x = x - facing * streak_len
            alpha = _NS_kryvoxar._alpha(200 * (1 - progress) * (1 - i / 8))
            if alpha > 0:
                pygame.draw.line(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha),
                                 (x, streak_y), (end_x, streak_y), 2)
                pygame.draw.line(surface, (*_NS_kryvoxar.PALETTE["crystal_shine"], alpha),
                                 (x, streak_y), (end_x, streak_y), 1)
    # ============================================================
    # SKILL R - BLOOD AND STONE (ultimate: pull + eruption)
    # ============================================================
    def _draw_bloodstone_ground(surface, boss, x, y, timer, phase):
        """Large ground rune during ultimate."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 2))
        if r > 5:
            # Pulling vortex rings
            for i in range(4):
                ring_r = r - i * 10
                if ring_r <= 0:
                    continue
                alpha = _NS_kryvoxar._alpha(180 - i * 30)
                pygame.draw.ellipse(surface, (*_NS_kryvoxar.PALETTE["crystal_darkest"], alpha),
                                    (x - ring_r, y + 40 - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 2)
            # Inner glow
            pygame.draw.ellipse(surface, (*_NS_kryvoxar.PALETTE["crystal_dark"], 200),
                                (x - r + 10, y + 40 - r // 3 + 4,
                                 r * 2 - 20, r * 2 // 3 - 8))
            # Runes around edge
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.3
                rx = x + int(math.cos(angle) * r)
                ry = y + 40 + int(math.sin(angle) * r * 0.35)
                pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"], (rx, ry, 2, 2))
    def _draw_bloodstone_foreground(surface, boss, x, y, timer, phase):
        """Pulling vortex + eruption of giant crystals."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Phase 1: Pull vortex (spiraling energy)
            t = progress / 0.5
            for i in range(15):
                spiral_t = (phase * 0.5 + i * 0.08) % 1.0
                r = int(80 * (1 - spiral_t))
                angle = spiral_t * math.pi * 4 + i * math.pi / 7
                px = x + int(math.cos(angle) * r)
                py = y + int(math.sin(angle) * r * 0.5)
                alpha = _NS_kryvoxar._alpha(220 * (1 - spiral_t) * t)
                _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], alpha),
                                        (px, py), 3)
                pygame.draw.rect(surface, (*_NS_kryvoxar.PALETTE["crystal_hot"], alpha),
                                 (px, py, 1, 1))
        else:
            # Phase 2: Massive crystal eruption
            t = (progress - 0.5) / 0.5
            intensity = math.sin(t * math.pi)
            # Giant central crystal spike
            spike_h = int(60 * intensity)
            if spike_h > 5:
                tip = (x, y - spike_h)
                base_a = (x - 10, y + 20)
                base_b = (x + 10, y + 20)
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["shadow_deep"],
                                    [(tip[0] + 2, tip[1] + 2),
                                     (base_a[0] + 2, base_a[1] + 2),
                                     (base_b[0] + 2, base_b[1] + 2)])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"],
                                    [tip, base_a, base_b])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_dark"], [
                    tip,
                    (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
                    (int((tip[0] + base_b[0]) / 2), int((tip[1] + base_b[1]) / 2)),
                ])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"], [
                    tip,
                    (int((tip[0] * 3 + base_a[0]) / 4), int((tip[1] * 3 + base_a[1]) / 4)),
                    (int((tip[0] * 3 + base_b[0]) / 4), int((tip[1] * 3 + base_b[1]) / 4)),
                ])
                pygame.draw.line(surface, _NS_kryvoxar.PALETTE["crystal_light"],
                                 tip, (int((tip[0] + base_b[0]) / 2),
                                       int((tip[1] + base_b[1]) / 2)), 2)
                _NS_kryvoxar._aacircle(surface, _NS_kryvoxar.PALETTE["crystal_hot"], tip, 3)
                _NS_kryvoxar._aacircle(surface, _NS_kryvoxar.PALETTE["white"], tip, 1)
            # Surrounding smaller spikes
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.2
                dist = 40 + int(math.sin(phase + i) * 8)
                sx = x + int(math.cos(angle) * dist)
                sy = y + 30 + int(math.sin(angle) * dist * 0.4)
                mini_h = int(25 * intensity)
                if mini_h < 5:
                    continue
                tip_m = (sx, sy - mini_h)
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_darkest"], [
                    tip_m, (sx - 4, sy), (sx + 4, sy),
                ])
                _NS_kryvoxar._poly(surface, _NS_kryvoxar.PALETTE["crystal_mid"], [
                    tip_m,
                    (int((tip_m[0] + sx - 4) / 2), int((tip_m[1] + sy) / 2)),
                    (int((tip_m[0] + sx + 4) / 2), int((tip_m[1] + sy) / 2)),
                ])
                pygame.draw.rect(surface, _NS_kryvoxar.PALETTE["crystal_hot"],
                                 (tip_m[0], tip_m[1], 1, 1))
            # Shockwave
            shock_r = int(30 + t * 60)
            shock_alpha = _NS_kryvoxar._alpha(200 * (1 - t))
            _NS_kryvoxar._aacircle(surface, (*_NS_kryvoxar.PALETTE["crystal_light"], shock_alpha),
                                    (x, y + 20), shock_r, 2)



# ====================================================================
# VARGROTH (BLOODMOON ALPHA) - Mini Boss
# ====================================================================

class _NS_vargroth:
    """Namespace vargroth - Mini boss werewolf/beastmaster."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (rugged tan)
        "skin_darkest": (40, 25, 20),
        "skin_dark": (95, 65, 50),
        "skin_mid": (155, 115, 90),
        "skin_light": (210, 170, 140),
        "skin_shine": (245, 215, 190),
        # Hair/beard (dark brown/black)
        "hair_darkest": (10, 8, 8),
        "hair_dark": (35, 25, 20),
        "hair_mid": (75, 55, 40),
        "hair_light": (130, 100, 75),
        # Fur (wolf gray-brown)
        "fur_darkest": (15, 12, 10),
        "fur_dark": (45, 35, 30),
        "fur_mid": (95, 80, 65),
        "fur_light": (155, 140, 115),
        "fur_edge": (200, 185, 155),
        # Leather armor (dark brown)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (55, 35, 20),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 105, 60),
        # Metal (iron rivets)
        "metal_dark": (30, 30, 35),
        "metal_mid": (80, 80, 90),
        "metal_light": (170, 170, 180),
        # BLOOD RED (signature - eyes, howl, ultimate)
        "blood_darkest": (25, 3, 5),
        "blood_dark": (75, 10, 15),
        "blood_mid": (170, 25, 35),
        "blood_light": (240, 60, 60),
        "blood_hot": (255, 130, 100),
        "blood_shine": (255, 210, 180),
        # Cape (dark red)
        "cape_darkest": (20, 5, 8),
        "cape_dark": (55, 15, 20),
        "cape_mid": (100, 30, 35),
        "cape_light": (160, 60, 60),
        # Fang / claw (bone/off-white)
        "fang_dark": (85, 75, 60),
        "fang_mid": (180, 165, 140),
        "fang_light": (240, 225, 200),
        # Moon glow (background accent)
        "moon_dark": (40, 20, 10),
        "moon_mid": (140, 60, 30),
        "moon_light": (240, 130, 80),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 3),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vargroth._clamp(color)
        if _NS_vargroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vargroth._clamp(color)
        if _NS_vargroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vargroth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vargroth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_vargroth._update_var_attack_anim(boss)
        attacking = (
            getattr(boss, "_var_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient background.
        _NS_vargroth._draw_blood_aura(surface, x, y, pulse, active_skill)
        _NS_vargroth._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_vargroth._draw_wolf_pack_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vargroth._draw_howl_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vargroth._draw_bloodmoon_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (transform state affects rendering).
        if attacking:
            _NS_vargroth._draw_var_attack(surface, boss, x, y)
        else:
            _NS_vargroth._draw_var_idle(surface, boss, x, y)
        # W buff aura (over body).
        if active_skill == "w":
            _NS_vargroth._draw_feral_rage_aura(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_vargroth._draw_wolf_pack_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vargroth._draw_howl_waves(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vargroth._draw_bloodmoon_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_var_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_var_previous_timer", 0))
        active = bool(getattr(boss, "_var_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._var_attack_active = True
            boss._var_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._var_attack_frame = int(getattr(boss, "_var_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._var_attack_active = False
            boss._var_attack_frame = 0
            active = False
        boss._var_previous_timer = timer
        boss._var_attack_progress = (
            min(1.0, getattr(boss, "_var_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_var_idle(surface, boss, x, y):
        """Floating idle - beast alpha stance."""
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        sway = int(math.sin(boss.pulse * 0.35) * 2)
        _NS_vargroth._draw_shadow(surface, x + sway, y + 50, phase=boss.pulse)
        _NS_vargroth._draw_bloodmist(surface, x + sway, y + 42, boss.pulse)
        _NS_vargroth._draw_var_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")
    def _draw_var_attack(surface, boss, x, y):
        progress = getattr(boss, "_var_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back → CLAW SWIPE → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_vargroth._draw_shadow(surface, x + lunge, y + 50, phase=boss.pulse)
        _NS_vargroth._draw_bloodmist(surface, x + lunge, y + 42, boss.pulse, intense=True)
        _NS_vargroth._draw_var_body(surface, x + lunge, y + bob - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Claw slash effect during swing.
        if 0.35 < progress < 0.75:
            _NS_vargroth._draw_claw_slash(surface, x + lunge, y + bob - lift,
                                          boss.direction, progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_var_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw floating werewolf beastman."""
        # Cape (dark red).
        _NS_vargroth._draw_wolf_cape(surface, cx, cy, facing, phase)
        # Legs (floating - dangling like Vorgath).
        _NS_vargroth._draw_beast_legs(surface, cx, cy + 12, facing, phase)
        # Torso (muscular bare chest with fur/leather).
        _NS_vargroth._draw_beast_torso(surface, cx, cy, facing, phase)
        # Back arm.
        _NS_vargroth._draw_back_claw_arm(surface, cx, cy, facing, phase)
        # Head with beard, wolf features.
        _NS_vargroth._draw_beast_head(surface, cx + facing * 2, cy - 20, facing, phase)
        # Front arm with claws (main attack).
        _NS_vargroth._draw_front_claw_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_wolf_cape(surface, cx, cy, facing, phase):
        """Dark red cape with fur trim."""
        sway = math.sin(phase * 0.7) * 3
        back = -facing
        cape_top = (cx + back * 5, cy - 15)
        cape_shoulder = (cx + back * 9, cy - 11)
        cape_mid = (cx + back * 15 + int(sway), cy + 2)
        cape_bot1 = (cx + back * 19 + int(sway * 1.5), cy + 15)
        cape_bot2 = (cx + back * 13 + int(sway), cy + 19)
        cape_bot3 = (cx + back * 5, cy + 17)
        cape_side = (cx + back * 3, cy - 9)
        pts = [cape_top, cape_shoulder, cape_mid, cape_bot1,
               cape_bot2, cape_bot3, cape_side]
        # Shadow.
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in pts])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["cape_darkest"], pts)
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["cape_dark"], [
            cape_top, cape_shoulder,
            (cape_mid[0] + facing * 2, cape_mid[1]),
            (cape_bot1[0] + facing * 2, cape_bot1[1] - 2),
            (cape_bot3[0] + facing * 2, cape_bot3[1] - 2),
            cape_side,
        ])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["cape_mid"], [
            (cape_top[0] + facing, cape_top[1] + 1),
            (cape_shoulder[0] + facing, cape_shoulder[1] + 1),
            (cape_mid[0] + facing * 4, cape_mid[1]),
            (cape_bot3[0] + facing * 3, cape_bot3[1] - 4),
            (cape_side[0] + facing, cape_side[1] + 1),
        ])
        # Cape edge highlights.
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["cape_light"],
                              cape_top, cape_shoulder, 1)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["cape_light"],
                              (cape_bot1[0], cape_bot1[1] - 1),
                              (cape_bot2[0], cape_bot2[1] - 1), 1)
        # Fur trim at top of cape (shoulder area).
        for i in range(4):
            fur_x = cx + back * (6 + i * 2)
            fur_y = cy - 12 + int(math.sin(phase + i) * 1)
            _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["fur_darkest"], (fur_x, fur_y), 3)
            _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["fur_dark"], (fur_x, fur_y), 2)
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["fur_light"], (fur_x, fur_y - 1, 1, 1))
    def _draw_beast_legs(surface, cx, cy, facing, phase):
        """Legs dangling with leather boots + fur."""
        sway = math.sin(phase * 0.6) * 2
        # Left leg.
        hip_a = (cx - 4, cy - 2)
        knee_a = (cx - 6 - facing, cy + 6 + int(sway))
        foot_a = (cx - 3 - facing, cy + 14 + int(sway))
        # Right leg.
        hip_b = (cx + 4, cy - 2)
        knee_b = (cx + 5 + facing, cy + 8 - int(sway))
        foot_b = (cx + 7 + facing, cy + 15 - int(sway))
        for hip, knee, foot in [(hip_a, knee_a, foot_a), (hip_b, knee_b, foot_b)]:
            # Shadow.
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["shadow_deep"],
                                  (hip[0] + 1, hip[1] + 1),
                                  (knee[0] + 1, knee[1] + 1), 6)
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["shadow_deep"],
                                  (knee[0] + 1, knee[1] + 1),
                                  (foot[0] + 1, foot[1] + 1), 5)
            # Thigh (leather pants).
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_darkest"], hip, knee, 6)
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_dark"], hip, knee, 4)
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_mid"],
                                  (hip[0] - 1, hip[1]), (knee[0] - 1, knee[1]), 2)
            # Shin.
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_darkest"], knee, foot, 5)
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_dark"], knee, foot, 3)
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_mid"],
                                  (knee[0] - 1, knee[1]), (foot[0] - 1, foot[1]), 1)
            # Knee - fur strap.
            _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["fur_dark"], knee, 3)
            _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["fur_mid"], knee, 2)
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["fur_light"], (knee[0], knee[1], 1, 1))
            # Boot (leather with fur).
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["leather_darkest"], [
                (foot[0] - 3, foot[1] - 1),
                (foot[0] + 4, foot[1] - 1),
                (foot[0] + 3, foot[1] + 3),
                (foot[0] - 2, foot[1] + 3),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["leather_dark"], [
                (foot[0] - 2, foot[1]),
                (foot[0] + 3, foot[1]),
                (foot[0] + 2, foot[1] + 2),
                (foot[0] - 1, foot[1] + 2),
            ])
            # Fur top of boot.
            for fx_off in (-2, 0, 2):
                pygame.draw.rect(surface, _NS_vargroth.PALETTE["fur_mid"],
                                 (foot[0] + fx_off, foot[1] - 2, 1, 1))
                pygame.draw.rect(surface, _NS_vargroth.PALETTE["fur_light"],
                                 (foot[0] + fx_off, foot[1] - 2, 1, 1))
    def _draw_beast_torso(surface, cx, cy, facing, phase):
        """Muscular bare chest with fur pauldrons + leather straps."""
        breath = math.sin(phase * 0.7) * 1
        # Main torso (V-shape muscular).
        torso = [
            (cx - 11, cy - 12),
            (cx - 13, cy - 4),
            (cx - 11, cy + 4),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 11, cy + 4),
            (cx + 13, cy - 4),
            (cx + 11, cy - 12),
            (cx + 4, cy - 14),
            (cx - 4, cy - 14),
        ]
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_darkest"], torso)
        # Skin base.
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_dark"], [
            (cx - 10, cy - 11), (cx - 12, cy - 4), (cx - 10, cy + 3),
            (cx - 5, cy + 9), (cx + 5, cy + 9), (cx + 10, cy + 3),
            (cx + 12, cy - 4), (cx + 10, cy - 11),
            (cx + 3, cy - 13), (cx - 3, cy - 13),
        ])
        # Muscle definition.
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_mid"], [
            (cx - 8, cy - 10), (cx - 10, cy - 4), (cx - 8, cy + 2),
            (cx - 4, cy + 7), (cx + 4, cy + 7), (cx + 8, cy + 2),
            (cx + 10, cy - 4), (cx + 8, cy - 10),
        ])
        # Highlight (pecs).
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_light"], [
            (cx - 5, cy - 8), (cx - 6, cy - 3), (cx - 2, cy - 1),
            (cx + 2, cy - 1), (cx + 6, cy - 3), (cx + 5, cy - 8),
            (cx + 2, cy - 9), (cx - 2, cy - 9),
        ])
        # Chest line.
        pygame.draw.line(surface, _NS_vargroth.PALETTE["skin_darkest"],
                         (cx, cy - 8), (cx, cy + 2), 1)
        # Ab lines.
        for ab_y in (0, 3, 6):
            pygame.draw.line(surface, _NS_vargroth.PALETTE["skin_darkest"],
                             (cx - 4, cy + ab_y), (cx + 4, cy + ab_y), 1)
        # LEATHER STRAP diagonal across chest.
        strap_start = (cx - 10, cy - 6)
        strap_end = (cx + 8, cy + 5)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_darkest"],
                              strap_start, strap_end, 3)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_dark"],
                              strap_start, strap_end, 2)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_mid"],
                              (strap_start[0], strap_start[1] - 1),
                              (strap_end[0], strap_end[1] - 1), 1)
        # Wolf skull emblem on strap (small).
        emblem_x = cx - 2
        emblem_y = cy - 1
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_dark"], (emblem_x, emblem_y), 3)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_mid"], (emblem_x, emblem_y), 2)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_light"], (emblem_x - 1, emblem_y - 1), 1)
        # Red gem center.
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_mid"], (emblem_x, emblem_y, 1, 1))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_light"], (emblem_x, emblem_y, 1, 1))
        # Belt (leather with metal buckle).
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["leather_darkest"],
                         (cx - 8, cy + 8, 16, 4))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["leather_dark"],
                         (cx - 7, cy + 9, 14, 2))
        # Buckle.
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["metal_dark"],
                         (cx - 3, cy + 8, 6, 4))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["metal_light"],
                         (cx - 2, cy + 9, 4, 2))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_mid"],
                         (cx, cy + 10, 1, 1))
        # FUR PAULDRONS (wolf fur on shoulders).
        _NS_vargroth._draw_fur_pauldrons(surface, cx, cy, facing, phase)
        # Blood scar on chest (3 claw marks - iconic).
        scar_x = cx - 8
        for i in range(3):
            pygame.draw.line(surface, _NS_vargroth.PALETTE["blood_dark"],
                             (scar_x + i * 3, cy - 8),
                             (scar_x + i * 3 + 4, cy - 3), 1)
            pygame.draw.line(surface, _NS_vargroth.PALETTE["blood_mid"],
                             (scar_x + i * 3, cy - 8),
                             (scar_x + i * 3 + 3, cy - 4), 1)
    def _draw_fur_pauldrons(surface, cx, cy, facing, phase):
        """Wolf fur pauldrons on shoulders."""
        for side in (-1, 1):
            sx = cx + side * 12
            sy = cy - 12
            # Base pauldron shape (fur mass).
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"], [
                (sx + side * 1, sy - 4),
                (sx + side * 6, sy - 2),
                (sx + side * 7, sy + 3),
                (sx + side * 2, sy + 6),
                (sx - side * 3, sy + 3),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fur_darkest"], [
                (sx, sy - 5),
                (sx + side * 5, sy - 2),
                (sx + side * 6, sy + 2),
                (sx + side * 1, sy + 5),
                (sx - side * 3, sy + 2),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fur_dark"], [
                (sx, sy - 4),
                (sx + side * 4, sy - 1),
                (sx + side * 5, sy + 1),
                (sx, sy + 4),
                (sx - side * 2, sy + 1),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fur_mid"], [
                (sx, sy - 3),
                (sx + side * 3, sy),
                (sx + side * 3, sy + 2),
                (sx, sy + 3),
                (sx - side * 1, sy),
            ])
            # Fur strands (spiky look).
            for i, (dx, dy) in enumerate([(-2, -4), (0, -5), (2, -4), (4, -2), (5, 0)]):
                wave = math.sin(phase + i) * 1
                strand_x = sx + int(dx * side)
                strand_y = sy + dy + int(wave)
                strand_tip_x = strand_x + int(side * 1)
                strand_tip_y = strand_y - 2
                pygame.draw.line(surface, _NS_vargroth.PALETTE["fur_darkest"],
                                 (strand_x, strand_y), (strand_tip_x, strand_tip_y), 1)
                pygame.draw.rect(surface, _NS_vargroth.PALETTE["fur_light"],
                                 (strand_tip_x, strand_tip_y, 1, 1))
    def _draw_back_claw_arm(surface, cx, cy, facing, phase):
        """Back arm with clawed hand."""
        back = -facing
        sway = math.sin(phase * 0.5) * 1
        shoulder = (cx + back * 9, cy - 10)
        elbow = (cx + back * 13, cy - 1 + int(sway))
        hand = (cx + back * 11, cy + 8 + int(sway))
        # Shadow.
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 4)
        # Upper arm (muscular skin).
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["skin_darkest"], shoulder, elbow, 5)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["skin_dark"], shoulder, elbow, 3)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["skin_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 1)
        # Forearm (with leather bracer).
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_darkest"], elbow, hand, 4)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_dark"], elbow, hand, 3)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_mid"],
                              (elbow[0] - 1, elbow[1]),
                              (hand[0] - 1, hand[1]), 1)
        # Bracer metal.
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_dark"], elbow, 2)
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["metal_light"], (elbow[0], elbow[1], 1, 1))
        # Clawed fist.
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["skin_darkest"], hand, 3)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["skin_dark"], hand, 2)
        # Small claws.
        for claw_off in (-2, 0, 2):
            pygame.draw.line(surface, _NS_vargroth.PALETTE["fang_dark"],
                             hand,
                             (hand[0] + claw_off - back, hand[1] + 3), 1)
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["fang_light"],
                             (hand[0] + claw_off - back, hand[1] + 3, 1, 1))
    def _draw_beast_head(surface, cx, cy, facing, phase):
        """Rugged warrior head with beard, wolf-like features."""
        # Head shape (wider jaw for beard).
        head = [
            (cx - 6, cy - 2),
            (cx - 7, cy - 6),
            (cx - 5, cy - 10),
            (cx - 1, cy - 12),
            (cx + 4, cy - 11),
            (cx + 7, cy - 8),
            (cx + 7, cy - 3),
            (cx + 6, cy + 3),
            (cx + 4, cy + 6),  # jaw
            (cx - 4, cy + 6),
            (cx - 6, cy + 3),
        ]
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in head])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_darkest"], head)
        # Skin base.
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_dark"], [
            (cx - 5, cy - 2), (cx - 6, cy - 6), (cx - 4, cy - 9),
            (cx - 1, cy - 11), (cx + 3, cy - 10), (cx + 6, cy - 7),
            (cx + 6, cy - 3), (cx + 5, cy + 2), (cx + 3, cy + 5),
            (cx - 3, cy + 5), (cx - 5, cy + 2),
        ])
        # Face mid.
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_mid"], [
            (cx - 3, cy - 4), (cx - 4, cy - 7), (cx, cy - 9),
            (cx + 3, cy - 8), (cx + 5, cy - 5), (cx + 4, cy - 1),
            (cx + 2, cy + 1), (cx - 2, cy + 1), (cx - 3, cy - 1),
        ])
        # Nose/cheek highlight.
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["skin_light"], [
            (cx, cy - 6), (cx + 3, cy - 5), (cx + 2, cy - 2), (cx, cy - 3),
        ])
        # HAIR (dark, wild, spiky).
        _NS_vargroth._draw_beast_hair(surface, cx, cy, facing, phase)
        # BEARD (thick dark).
        _NS_vargroth._draw_beard(surface, cx, cy, facing, phase)
        # EYES (RED - beast/bloodlust).
        _NS_vargroth._draw_beast_eyes(surface, cx, cy, facing, phase)
        # Nose.
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["skin_darkest"], (cx + 1, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["skin_light"], (cx + 2, cy - 3, 1, 1))
        # Fierce brow.
        pygame.draw.line(surface, _NS_vargroth.PALETTE["hair_darkest"],
                         (cx - 4, cy - 6), (cx - 2, cy - 5), 1)
        pygame.draw.line(surface, _NS_vargroth.PALETTE["hair_darkest"],
                         (cx + 2, cy - 5), (cx + 4, cy - 6), 1)
        # WOLF EARS (small pointed ears at top).
        _NS_vargroth._draw_wolf_ears(surface, cx, cy, facing, phase)
    def _draw_beast_hair(surface, cx, cy, facing, phase):
        """Wild dark hair swept back."""
        wave = math.sin(phase * 0.5) * 1
        hair_shape = [
            (cx - 6, cy - 5),
            (cx - 7, cy - 10),
            (cx - 4, cy - 13),
            (cx, cy - 14),
            (cx + 4, cy - 13),
            (cx + 7, cy - 11),
            (cx + 8, cy - 8),
            (cx + 6, cy - 5),
            (cx + 3, cy - 9),
            (cx - 3, cy - 9),
        ]
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in hair_shape])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["hair_darkest"], hair_shape)
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["hair_dark"], [
            (cx - 5, cy - 6), (cx - 6, cy - 10), (cx - 3, cy - 12),
            (cx, cy - 13), (cx + 3, cy - 12), (cx + 5, cy - 10),
            (cx + 6, cy - 8), (cx + 4, cy - 6), (cx, cy - 9),
            (cx - 3, cy - 9),
        ])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["hair_mid"], [
            (cx - 3, cy - 8), (cx - 4, cy - 11), (cx - 1, cy - 12),
            (cx + 2, cy - 11), (cx + 1, cy - 10), (cx - 1, cy - 10),
        ])
        # Hair spikes (wild).
        for i, (dx, dy, length) in enumerate([
            (-6, -8, 3), (-3, -12, 2), (2, -13, 2), (5, -11, 3), (7, -8, 3),
        ]):
            offset = int(wave) if i % 2 == 0 else -int(wave)
            spike_x = cx + dx
            spike_y = cy + dy + offset
            tip_x = spike_x - facing * length
            tip_y = spike_y - length
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["hair_darkest"],
                                  (spike_x, spike_y), (tip_x, tip_y), 2)
            _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["hair_dark"],
                                  (spike_x, spike_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["hair_light"], (tip_x, tip_y, 1, 1))
        # Streak of gray in hair (alpha wolf feature).
        pygame.draw.line(surface, _NS_vargroth.PALETTE["fur_edge"],
                         (cx - 2, cy - 11), (cx - 3, cy - 8), 1)
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["fur_light"], (cx - 2, cy - 11, 1, 1))
    def _draw_beard(surface, cx, cy, facing, phase):
        """Thick dark beard."""
        # Beard shape.
        beard = [
            (cx - 5, cy),
            (cx - 6, cy + 3),
            (cx - 5, cy + 7),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 7),
            (cx + 6, cy + 3),
            (cx + 5, cy),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ]
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"],
                            [(px, py + 1) for px, py in beard])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["hair_darkest"], beard)
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["hair_dark"], [
            (cx - 4, cy + 1),
            (cx - 5, cy + 4),
            (cx - 4, cy + 6),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 4, cy + 6),
            (cx + 5, cy + 4),
            (cx + 4, cy + 1),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["hair_mid"], [
            (cx - 3, cy + 4), (cx + 3, cy + 4),
            (cx + 2, cy + 6), (cx - 2, cy + 6),
        ])
        # Beard strands (rough texture).
        for x_off in (-4, -2, 0, 2, 4):
            pygame.draw.line(surface, _NS_vargroth.PALETTE["hair_darkest"],
                             (cx + x_off, cy + 3), (cx + x_off, cy + 7), 1)
        # Mustache lines above.
        pygame.draw.line(surface, _NS_vargroth.PALETTE["hair_darkest"],
                         (cx - 3, cy + 1), (cx - 1, cy + 2), 1)
        pygame.draw.line(surface, _NS_vargroth.PALETTE["hair_darkest"],
                         (cx + 1, cy + 2), (cx + 3, cy + 1), 1)
    def _draw_beast_eyes(surface, cx, cy, facing, phase):
        """Fierce red beast eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side, ex_off in [(-1, -2), (1, 3)]:
            ex = cx + ex_off
            ey = cy - 4
            # Socket.
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 2))
            # Red glow halo.
            for r in range(5, 0, -1):
                alpha = _NS_vargroth._alpha(120 * (5 - r) / 5 * pulse)
                _NS_vargroth._aacircle(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                        (ex, ey), r)
            # Eye core.
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_wolf_ears(surface, cx, cy, facing, phase):
        """Small pointed wolf ears on top of head."""
        wave = math.sin(phase * 0.6) * 1
        for side_i, (dx, dy) in enumerate([(-5, -11), (5, -11)]):
            ear_x = cx + dx
            ear_y = cy + dy + int(wave)
            side = -1 if side_i == 0 else 1
            # Ear triangle.
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"], [
                (ear_x + 1, ear_y + 1),
                (ear_x + side * 2 + 1, ear_y - 3 + 1),
                (ear_x + side * 3 + 1, ear_y + 1),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fur_darkest"], [
                (ear_x, ear_y),
                (ear_x + side * 2, ear_y - 3),
                (ear_x + side * 3, ear_y),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fur_dark"], [
                (ear_x + side, ear_y - 1),
                (ear_x + side * 2, ear_y - 2),
                (ear_x + side * 2, ear_y),
            ])
            # Inner ear (pink/red).
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_dark"],
                             (ear_x + side, ear_y - 1, 1, 1))
    def _draw_front_claw_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with big claws (main melee weapon)."""
        shoulder = (cx + facing * 12, cy - 10)
        # Arm angle based on attack.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise arm back over shoulder.
                t = attack_progress / 0.35
                arm_angle = -math.pi * (0.2 + t * 0.5)  # arm goes UP-BACK
                claw_extra = int(t * 3)
            elif attack_progress < 0.65:
                # SLASH FORWARD - horizontal claw swipe.
                t = (attack_progress - 0.35) / 0.3
                arm_angle = -math.pi * 0.7 + t * math.pi * 1.0  # sweep from up-back to down-forward
                claw_extra = int(3 + t * 2)
            else:
                # Recovery.
                t = (attack_progress - 0.65) / 0.35
                arm_angle = math.pi * (0.3 - t * 0.15)
                claw_extra = int(5 - t * 5)
        else:
            # Idle: arm hangs slightly forward.
            hover = math.sin(phase * 0.7) * 1
            arm_angle = math.pi * 0.15
            claw_extra = int(hover)
        # Calc elbow position.
        arm_len = 10
        elbow_x = shoulder[0] + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder[1] + int(math.sin(arm_angle) * arm_len)
        # Forearm.
        forearm_angle = arm_angle + math.pi * 0.1
        forearm_len = 10
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)
        # === DRAW ARM ===
        # Shadow.
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow_x + 1, elbow_y + 1), 7)
        # Upper arm (muscular skin).
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["skin_darkest"],
                              shoulder, (elbow_x, elbow_y), 6)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["skin_dark"],
                              shoulder, (elbow_x, elbow_y), 4)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["skin_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow_x, elbow_y - 1), 2)
        # Forearm with leather bracer.
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 6)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_vargroth._aaline(surface, _NS_vargroth.PALETTE["leather_mid"],
                              (elbow_x - 1, elbow_y),
                              (hand_x - 1, hand_y), 1)
        # Metal spikes on bracer.
        for spike_t in (0.3, 0.7):
            sx = int(elbow_x + (hand_x - elbow_x) * spike_t)
            sy = int(elbow_y + (hand_y - elbow_y) * spike_t)
            _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_dark"], (sx, sy - 1), 2)
            _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_light"], (sx, sy - 1), 1)
        # Elbow guard.
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_dark"], (elbow_x, elbow_y), 3)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_mid"], (elbow_x, elbow_y), 2)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["metal_light"],
                                (elbow_x - 1, elbow_y - 1), 1)
        # === CLAWED HAND ===
        _NS_vargroth._draw_claw_hand(surface, hand_x, hand_y,
                                      forearm_angle, facing, claw_extra, action, attack_progress)
    def _draw_claw_hand(surface, hx, hy, angle, facing, claw_extra, action, attack_progress):
        """Fist with 4 big sharp claws."""
        # Hand base.
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["shadow_deep"], (hx + 1, hy + 1), 5)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["skin_darkest"], (hx, hy), 5)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["skin_dark"], (hx, hy), 4)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["skin_mid"], (hx - 1, hy - 1), 2)
        # 4 CLAWS extending forward.
        claw_len = 6 + claw_extra
        for i, angle_off in enumerate([-0.4, -0.15, 0.1, 0.35]):
            claw_angle = angle + angle_off
            claw_start_x = hx + int(math.cos(claw_angle) * 4) * facing
            claw_start_y = hy + int(math.sin(claw_angle) * 4)
            claw_tip_x = hx + int(math.cos(claw_angle) * (4 + claw_len)) * facing
            claw_tip_y = hy + int(math.sin(claw_angle) * (4 + claw_len))
            # Claw shape (thicker at base, sharp tip).
            perp = claw_angle + math.pi / 2
            base_a = (claw_start_x + int(math.cos(perp) * 1),
                       claw_start_y + int(math.sin(perp) * 1))
            base_b = (claw_start_x - int(math.cos(perp) * 1),
                       claw_start_y - int(math.sin(perp) * 1))
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"], [
                (claw_tip_x + 1, claw_tip_y + 1),
                (base_a[0] + 1, base_a[1] + 1),
                (base_b[0] + 1, base_b[1] + 1),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fang_dark"],
                                [(claw_tip_x, claw_tip_y), base_a, base_b])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fang_mid"], [
                (claw_tip_x, claw_tip_y),
                (int((claw_tip_x + base_a[0]) / 2),
                 int((claw_tip_y + base_a[1]) / 2)),
                (claw_start_x, claw_start_y),
            ])
            _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["fang_light"], [
                (claw_tip_x, claw_tip_y),
                (int((claw_tip_x + claw_start_x) / 2),
                 int((claw_tip_y + claw_start_y) / 2)),
                (claw_start_x, claw_start_y),
            ])
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["white"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            # Blood drip during attack.
            if action == "attack" and 0.5 < attack_progress < 0.75:
                pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_dark"],
                                 (claw_tip_x, claw_tip_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_mid"],
                                 (claw_tip_x, claw_tip_y + 1, 1, 1))
    # ============================================================
    # CLAW SLASH EFFECT (during attack)
    # ============================================================
    def _draw_claw_slash(surface, cx, cy, facing, progress):
        """Big red claw slash marks in air during attack."""
        # Slash arcs from top-back to bottom-forward.
        t = (progress - 0.35) / 0.4
        t = min(1.0, t)
        alpha = _NS_vargroth._alpha(240 * (1 - t * 0.5))
        # 3 parallel claw marks (looks like 3 claws slashing).
        for i in range(3):
            offset = (i - 1) * 5
            # Arc from top-back to bottom-forward.
            arc_start_x = cx + facing * 5
            arc_start_y = cy - 12
            arc_end_x = cx + facing * 30
            arc_end_y = cy + 5
            # Interpolate current position with sweeping motion.
            sweep_t = t
            # Bezier-like arc.
            mid_x = int((arc_start_x + arc_end_x) / 2 + facing * 5)
            mid_y = cy - 5
            # Draw line at multiple points along the arc.
            num_pts = 10
            pts = []
            for j in range(num_pts + 1):
                jt = j / num_pts
                # Bezier curve.
                bx = int((1 - jt) ** 2 * arc_start_x + 2 * (1 - jt) * jt * mid_x
                          + jt ** 2 * arc_end_x)
                by = int((1 - jt) ** 2 * arc_start_y + 2 * (1 - jt) * jt * mid_y
                          + jt ** 2 * arc_end_y)
                # Perpendicular offset for 3 parallel lines.
                perp_angle = math.pi / 4  # diagonal
                bx += int(math.cos(perp_angle) * offset)
                by += int(math.sin(perp_angle) * offset)
                pts.append((bx, by))
            # Only draw the "revealed" portion up to progress.
            reveal_count = int(num_pts * sweep_t) + 1
            for j in range(min(reveal_count, len(pts) - 1)):
                pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha),
                                 (pts[j][0] + 1, pts[j][1] + 1),
                                 (pts[j + 1][0] + 1, pts[j + 1][1] + 1), 4)
                pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                                 pts[j], pts[j + 1], 3)
                pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                 pts[j], pts[j + 1], 2)
                pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_light"], alpha),
                                 pts[j], pts[j + 1], 1)
                # Sparkle on trail.
                if j % 2 == 0:
                    pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_hot"], alpha),
                                     (pts[j][0], pts[j][1], 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, phase=0):
        offset_y = int(math.sin(phase * 0.5) * 2)
        shadow = pygame.Surface((140, 28), pygame.SRCALPHA)
        max_alpha = 150
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * (max_alpha // 12))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 14 - radius // 2, 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (10, 3, 5, 170), (10, 10, 120, 10))
        surface.blit(shadow, (x - 70, y - 14 + offset_y))
    def _draw_bloodmist(surface, cx, cy, phase, intense=False):
        """Blood mist wisps rising."""
        strength = 1.4 if intense else 1.0
        for i in range(8):
            wisp_t = (phase * 0.5 + i * 0.14) % 1.0
            wx = cx - 16 + i * 4 + int(math.sin(phase + i) * 3)
            wy = cy + 10 - int(wisp_t * 22)
            alpha = _NS_vargroth._alpha(200 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_vargroth._aacircle(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha),
                                        (wx, wy), 3)
                _NS_vargroth._aacircle(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_light"], alpha),
                                 (wx, wy - 1, 1, 1))
        # Small blood droplets flying.
        for i in range(5):
            drop_t = (phase * 0.7 + i * 0.2) % 1.0
            dx = cx - 12 + i * 6 + int(math.sin(phase * 1.5 + i) * 3)
            dy = cy + 5 - int(drop_t * 18)
            alpha = _NS_vargroth._alpha(220 * (1 - drop_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha), (dx, dy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha), (dx, dy, 1, 1))
    def _draw_blood_aura(surface, x, y, phase, active_skill):
        """Red aura (bigger during R ultimate)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        scale = 1.3 if active_skill == "r" else 1.0
        aura = pygame.Surface((int(210 * scale), int(180 * scale)), pygame.SRCALPHA)
        cx_local = int(105 * scale)
        cy_local = int(90 * scale)
        max_r = int(90 * scale)
        for radius in range(max_r, 5, -5):
            alpha = _NS_vargroth._alpha((max_r - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_vargroth._aacircle(aura, (*_NS_vargroth.PALETTE["blood_darkest"], alpha),
                                        (cx_local, cy_local), radius)
        for radius in range(int(55 * scale), 5, -4):
            alpha = _NS_vargroth._alpha((int(55 * scale) - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_vargroth._aacircle(aura, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                                        (cx_local, cy_local), radius)
        for radius in range(int(35 * scale), 5, -3):
            alpha = _NS_vargroth._alpha((int(35 * scale) - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vargroth._aacircle(aura, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                        (cx_local, cy_local), radius)
        surface.blit(aura, (x - cx_local, y - cy_local))
        # Floating embers (blood sparks).
        num_embers = 16 if active_skill == "r" else 12
        for i in range(num_embers):
            angle = phase * 0.3 + i * math.pi / (num_embers // 2)
            radius = int(38 * scale) + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Red ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vargroth.PALETTE["blood_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_vargroth.PALETTE["blood_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_vargroth.PALETTE["blood_mid"], 230),
                            (25, 22, 120, 18), 1)
        # Wolf paw print runes.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            # Small paw shape (5 dots).
            pygame.draw.rect(ring, (*_NS_vargroth.PALETTE["blood_light"], 220), (x1, y1, 2, 2))
            for dot_off in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                pygame.draw.rect(ring, (*_NS_vargroth.PALETTE["blood_light"], 200),
                                 (x1 + dot_off[0], y1 + dot_off[1], 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vargroth.PALETTE["blood_hot"],
                                        _NS_vargroth._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: SUMMON PACK (3 wolf spirits)
    # ============================================================
    def _draw_wolf_pack_ground(surface, boss, x, y, timer, phase):
        """Ground paw prints appearing where wolves run."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vargroth._target_position(boss, x, y)
        # Paw prints along path from boss to target.
        num_prints = 8
        for i in range(num_prints):
            print_t = i / num_prints
            # Only show prints that "have been made" up to current progress.
            if print_t > progress * 1.5:
                continue
            px = int(x + (tx - x) * print_t)
            py = int(y + 44 + (ty - (y + 44)) * print_t + math.sin(i * 1.5) * 3)
            alpha = _NS_vargroth._alpha(180 * (1 - print_t * 0.5))
            # Paw print (5 dots).
            pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                             (px, py, 3, 3))
            for dot_off in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                 (px + dot_off[0], py + dot_off[1], 1, 1))
    def _draw_wolf_pack_foreground(surface, boss, x, y, timer, phase):
        """3 spectral wolves running from boss toward target."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vargroth._target_position(boss, x, y)
        # 3 wolves at different positions along path.
        for wolf_i in range(3):
            # Stagger start.
            wolf_start = wolf_i * 0.1
            wolf_t = max(0.0, min(1.0, (progress - wolf_start) * 1.3))
            if wolf_t <= 0:
                continue
            # Y offset per wolf.
            y_off = (wolf_i - 1) * 10
            wx = int(x + facing * 15 + (tx - x - facing * 15) * wolf_t)
            wy = int(y + 20 + y_off + (ty - y - 20 - y_off) * wolf_t
                      + math.sin(phase * 3 + wolf_i) * 2)
            # Fade in at start and fade out at end.
            if wolf_t < 0.1:
                fade = wolf_t / 0.1
            elif wolf_t > 0.85:
                fade = (1 - wolf_t) / 0.15
            else:
                fade = 1.0
            _NS_vargroth._draw_spectral_wolf(surface, wx, wy, facing, phase, fade)
    def _draw_spectral_wolf(surface, wx, wy, facing, phase, fade):
        """Small ghostly red wolf sprite (running left-to-right)."""
        alpha = _NS_vargroth._alpha(220 * fade)
        if alpha <= 0:
            return
        # Wolf body (elongated for running).
        # Body oval.
        body_shape = [
            (wx - 8 * facing, wy),
            (wx - 7 * facing, wy - 3),
            (wx + 4 * facing, wy - 4),
            (wx + 8 * facing, wy - 2),
            (wx + 9 * facing, wy + 1),
            (wx + 7 * facing, wy + 3),
            (wx - 5 * facing, wy + 3),
            (wx - 8 * facing, wy + 1),
        ]
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["shadow_deep"], alpha),
                            [(p[0] + 1, p[1] + 1) for p in body_shape])
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha), body_shape)
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha), [
            (wx - 7 * facing, wy),
            (wx - 6 * facing, wy - 2),
            (wx + 4 * facing, wy - 3),
            (wx + 7 * facing, wy - 1),
            (wx + 8 * facing, wy + 1),
            (wx + 6 * facing, wy + 2),
            (wx - 4 * facing, wy + 2),
            (wx - 7 * facing, wy + 1),
        ])
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha), [
            (wx - 5 * facing, wy - 1),
            (wx + 2 * facing, wy - 2),
            (wx + 5 * facing, wy - 1),
            (wx + 4 * facing, wy + 1),
            (wx - 3 * facing, wy + 1),
        ])
        # Wolf head (front).
        head_x = wx + 8 * facing
        head_y = wy - 2
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha), [
            (head_x, head_y - 2),
            (head_x + 4 * facing, head_y - 1),
            (head_x + 5 * facing, head_y + 2),
            (head_x + 2 * facing, head_y + 3),
            (head_x, head_y + 1),
        ])
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha), [
            (head_x + 1 * facing, head_y - 1),
            (head_x + 3 * facing, head_y),
            (head_x + 4 * facing, head_y + 2),
            (head_x + 1 * facing, head_y + 2),
        ])
        # Snout tip.
        pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_hot"], alpha),
                         (head_x + 5 * facing, head_y + 1, 1, 1))
        # Ears (2 small triangles on head).
        _NS_vargroth._poly(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha), [
            (head_x + 1 * facing, head_y - 2),
            (head_x + 2 * facing, head_y - 4),
            (head_x + 3 * facing, head_y - 1),
        ])
        # Glowing red eye.
        pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_hot"], alpha),
                         (head_x + 2 * facing, head_y, 1, 1))
        pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_shine"], alpha),
                         (head_x + 2 * facing, head_y, 1, 1))
        # Legs (4 running lines - alternating pose).
        leg_phase = phase * 6
        for leg_i in range(4):
            leg_x_off = -5 + leg_i * 4
            leg_bob = math.sin(leg_phase + leg_i * math.pi / 2) * 2
            leg_x = wx + leg_x_off * facing
            leg_top = wy + 3
            leg_bot = wy + 6 + int(leg_bob)
            pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha),
                             (leg_x, leg_top), (leg_x, leg_bot), 2)
            pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                             (leg_x, leg_bot, 1, 1))
        # Tail (flowing back).
        tail_wave = math.sin(phase * 2) * 2
        tail_start = (wx - 8 * facing, wy - 1)
        tail_mid = (wx - 11 * facing, wy - 3 + int(tail_wave))
        tail_tip = (wx - 14 * facing, wy - 1 + int(tail_wave))
        pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha),
                         tail_start, tail_mid, 3)
        pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                         tail_mid, tail_tip, 2)
        pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_light"], alpha),
                         (tail_tip[0], tail_tip[1], 1, 1))
        # Motion blur / spectral trail.
        for trail_i in range(3):
            offset = -(trail_i + 1) * 6 * facing
            trail_alpha = _NS_vargroth._alpha(alpha * (1 - trail_i / 3) * 0.4)
            _NS_vargroth._aacircle(surface,
                                    (*_NS_vargroth.PALETTE["blood_dark"], trail_alpha),
                                    (wx + offset, wy), 4)
    # ============================================================
    # SKILL W: FERAL RAGE (buff aura)
    # ============================================================
    def _draw_feral_rage_aura(surface, boss, x, y, timer, phase):
        """Red rage aura around boss (glow + sparks)."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Pulsing bubble.
        r = 55 + int(math.sin(phase * 2) * 4)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Aura ring layers.
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 150), (1, 200),
        ]):
            _NS_vargroth._aacircle(bubble, (*_NS_vargroth.PALETTE["blood_dark"], alpha_val),
                                    center, r - i, thickness)
            _NS_vargroth._aacircle(bubble, (*_NS_vargroth.PALETTE["blood_mid"], alpha_val),
                                    center, r - i - 1, 1)
        # Rotating claw marks on aura edge.
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            # Small claw slash mark (3 lines).
            for cl_i in range(3):
                cl_offset = (cl_i - 1) * 2
                cl_perp = angle + math.pi / 2
                clx1 = sx + int(math.cos(cl_perp) * cl_offset)
                cly1 = sy + int(math.sin(cl_perp) * cl_offset)
                pygame.draw.rect(bubble, (*_NS_vargroth.PALETTE["blood_hot"], 220),
                                 (clx1, cly1, 3, 1))
                pygame.draw.rect(bubble, (*_NS_vargroth.PALETTE["blood_shine"], 220),
                                 (clx1, cly1, 1, 1))
        # Fangs floating in aura (small red fangs).
        for i in range(8):
            angle = -phase * 0.8 + i * math.pi / 4
            inner_r = r - 12
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            # Fang shape.
            _NS_vargroth._poly(bubble, (*_NS_vargroth.PALETTE["fang_dark"], 220),
                                [(bx - 1, by), (bx + 1, by), (bx, by + 3)])
            pygame.draw.rect(bubble, (*_NS_vargroth.PALETTE["fang_light"], 220), (bx, by + 3, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Rising blood embers.
        for i in range(10):
            spark_t = (phase * 0.8 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.3
            spark_r = r + int(spark_t * 12)
            sx = x + int(math.cos(angle) * spark_r)
            sy = y + int(math.sin(angle) * spark_r) - int(spark_t * 10)
            alpha = _NS_vargroth._alpha(220 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_hot"], alpha), (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_shine"], alpha), (sx, sy, 1, 1))
    # ============================================================
    # SKILL E: BLOOD HOWL (expanding sound waves)
    # ============================================================
    def _draw_howl_ground(surface, boss, x, y, timer, phase):
        """Ground shake effect below boss."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(28 + i * 5 + math.sin(phase * 3) * 2)
            alpha = _NS_vargroth._alpha(180 - i * 45)
            _NS_vargroth._aacircle(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                    (x, y + 44), r, 2)
    def _draw_howl_waves(surface, boss, x, y, timer, phase):
        """Expanding red sound waves - Lycan howl signature."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple concentric wave arcs expanding outward.
        origin_x = x + facing * 12
        origin_y = y - 18  # from head
        # Number of wave rings.
        num_waves = 5
        for wave_i in range(num_waves):
            # Wave timing.
            wave_start = wave_i * 0.12
            wave_t = max(0.0, min(1.0, (progress - wave_start) * 1.8))
            if wave_t <= 0:
                continue
            # Expanding radius.
            max_radius = 90
            radius = int(15 + wave_t * max_radius)
            # Fade out.
            fade = 1 - wave_t
            alpha = _NS_vargroth._alpha(240 * fade)
            # Draw arc (crescent facing forward).
            # Arc from -60° to +60° (facing forward).
            angle_start = -math.pi * 0.4
            angle_end = math.pi * 0.4
            num_segs = 15
            prev_pt = None
            for seg in range(num_segs + 1):
                seg_t = seg / num_segs
                arc_angle = angle_start + (angle_end - angle_start) * seg_t
                px = origin_x + int(math.cos(arc_angle) * radius) * facing
                py = origin_y + int(math.sin(arc_angle) * radius)
                if prev_pt is not None:
                    # Draw wave arc line.
                    pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_darkest"], alpha),
                                     (prev_pt[0] + 1, prev_pt[1] + 1),
                                     (px + 1, py + 1), 4)
                    pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_dark"], alpha),
                                     prev_pt, (px, py), 3)
                    pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                     prev_pt, (px, py), 2)
                    pygame.draw.line(surface, (*_NS_vargroth.PALETTE["blood_light"], alpha),
                                     prev_pt, (px, py), 1)
                prev_pt = (px, py)
            # Sparks along wave.
            for i in range(8):
                sp_angle = angle_start + (angle_end - angle_start) * i / 7
                sx = origin_x + int(math.cos(sp_angle) * radius) * facing
                sy = origin_y + int(math.sin(sp_angle) * radius)
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_shine"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL R: BLOODMOON FORM (transform + eclipse)
    # ============================================================
    def _draw_bloodmoon_ground(surface, boss, x, y, timer, phase):
        """Big red circle marking transform area."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2))
        if r > 5:
            pygame.draw.ellipse(surface, (*_NS_vargroth.PALETTE["blood_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_vargroth.PALETTE["blood_dark"], 200),
                                (x - r + 4, y + 42 - r // 3,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_vargroth.PALETTE["blood_mid"], 150),
                                (x - r + 10, y + 44 - r // 3,
                                 r * 2 - 20, r * 2 // 3 - 10))
            # Wolf paw prints in a circle around boss.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.2
                px = x + int(math.cos(angle) * r * 0.85)
                py = y + 44 + int(math.sin(angle) * r * 0.32)
                pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_hot"], (px, py, 3, 3))
                for dot_off in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                    pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_light"],
                                     (px + dot_off[0], py + dot_off[1], 1, 1))
    def _draw_bloodmoon_foreground(surface, boss, x, y, timer, phase):
        """Big blood moon above boss + rising energy pillars."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # BLOOD MOON above boss.
        moon_x = x
        moon_y = y - 90
        moon_r = 24
        # Moon glow halo.
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for r in range(moon_r + 20, moon_r, -2):
            alpha = _NS_vargroth._alpha(80 * (moon_r + 20 - r) / 20 * pulse)
            _NS_vargroth._aacircle(surface, (*_NS_vargroth.PALETTE["blood_mid"], alpha),
                                    (moon_x, moon_y), r)
        # Moon body.
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["moon_dark"], (moon_x, moon_y), moon_r)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["blood_dark"], (moon_x, moon_y), moon_r - 2)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["blood_mid"], (moon_x, moon_y), moon_r - 5)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["moon_mid"],
                                (moon_x - 2, moon_y - 2), moon_r - 9)
        _NS_vargroth._aacircle(surface, _NS_vargroth.PALETTE["moon_light"],
                                (moon_x - 4, moon_y - 4), moon_r - 15)
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["blood_shine"],
                         (moon_x - 5, moon_y - 5, 2, 2))
        # Moon craters.
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["moon_dark"], (moon_x + 3, moon_y - 5, 3, 2))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["moon_dark"], (moon_x - 2, moon_y + 4, 2, 2))
        pygame.draw.rect(surface, _NS_vargroth.PALETTE["moon_dark"], (moon_x + 6, moon_y + 2, 2, 3))
        # Wolf silhouette on moon (howling).
        _NS_vargroth._draw_moon_wolf_silhouette(surface, moon_x, moon_y, moon_r)
        # Rising blood energy pillars around boss.
        r_ground = int(70 * min(1.0, progress * 2))
        num_pillars = 8
        for i in range(num_pillars):
            angle = i * math.pi / 4 + phase * 0.15
            px = x + int(math.cos(angle) * r_ground * 0.85)
            py_base = y + 44 + int(math.sin(angle) * r_ground * 0.3)
            for layer in range(6):
                layer_t = (phase * 0.7 + i * 0.3 + layer * 0.16) % 1.0
                py_layer = py_base - int(layer_t * 30)
                lalpha = _NS_vargroth._alpha(200 * (1 - layer_t))
                lw = int(4 + layer_t * 3)
                lh = int(2 + layer_t * 2)
                pygame.draw.ellipse(surface, (*_NS_vargroth.PALETTE["blood_dark"], lalpha),
                                    (px - lw, py_layer - lh, lw * 2, lh * 2))
                pygame.draw.ellipse(surface, (*_NS_vargroth.PALETTE["blood_mid"], lalpha),
                                    (px - lw + 1, py_layer - lh + 1,
                                     lw * 2 - 2, lh * 2 - 2))
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_light"], lalpha),
                                 (px, py_layer, 1, 1))
                pygame.draw.rect(surface, (*_NS_vargroth.PALETTE["blood_hot"], lalpha),
                                 (px, py_layer - 1, 1, 1))
    def _draw_moon_wolf_silhouette(surface, moon_x, moon_y, moon_r):
        """Small wolf silhouette on blood moon."""
        # Simple wolf howling shape.
        wolf_shape = [
            (moon_x - 3, moon_y + 3),
            (moon_x - 5, moon_y),
            (moon_x - 3, moon_y - 4),
            (moon_x, moon_y - 6),
            (moon_x + 2, moon_y - 8),
            (moon_x + 4, moon_y - 4),
            (moon_x + 5, moon_y),
            (moon_x + 3, moon_y + 3),
        ]
        _NS_vargroth._poly(surface, _NS_vargroth.PALETTE["shadow_deep"], wolf_shape)



# ====================================================================
# MOLGRAVAR (COLOSSUS OF THE SUNDERED PEAK) - TRUE BOSS
# ====================================================================

class _NS_molgravar:
    """Namespace molgravar - TRUE BOSS golem batu dengan lava cracks."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Stone (main body)
        "stone_darkest": (18, 12, 8),
        "stone_dark": (48, 34, 22),
        "stone_mid": (95, 72, 48),
        "stone_light": (155, 122, 85),
        "stone_shine": (210, 180, 135),
        # Dark rock (crevices, shadow between plates)
        "rock_darkest": (8, 5, 3),
        "rock_dark": (25, 18, 12),
        "rock_mid": (55, 42, 28),
        # Lava/molten cracks (orange-gold glow)
        "lava_darkest": (35, 12, 3),
        "lava_dark": (95, 40, 8),
        "lava_mid": (200, 100, 25),
        "lava_light": (255, 180, 60),
        "lava_hot": (255, 230, 130),
        "lava_shine": (255, 250, 200),
        # Gold trim (accents)
        "gold_dark": (100, 65, 15),
        "gold_mid": (195, 145, 45),
        "gold_light": (250, 215, 120),
        # Crystal shards (pale bone-white top spikes)
        "shard_dark": (65, 55, 45),
        "shard_mid": (135, 120, 100),
        "shard_light": (215, 200, 175),
        "shard_shine": (250, 240, 220),
        # Eye (glowing green-yellow like Malphite)
        "eye_socket": (5, 8, 3),
        "eye_dark": (30, 60, 15),
        "eye_mid": (120, 200, 60),
        "eye_light": (200, 255, 130),
        "eye_glow": (250, 255, 210),
        # Ambient dust
        "dust_dark": (25, 18, 12),
        "dust_mid": (85, 60, 35),
        "dust_light": (170, 135, 90),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 1),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_molgravar._clamp(color)
        if _NS_molgravar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_molgravar._clamp(color)
        if _NS_molgravar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_molgravar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 250 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_molgravar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_molgravar._update_mlg_attack_anim(boss)
        attacking = (
            getattr(boss, "_mlg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (large for TRUE BOSS)
        _NS_molgravar._draw_lava_aura(surface, x, y, pulse)
        _NS_molgravar._draw_ground_ring(surface, x, y + 58, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_molgravar._draw_thunderclap_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_molgravar._draw_groundslam_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_molgravar._draw_unstoppable_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_molgravar._draw_shard_ground(surface, boss, x, y, skill_timer, pulse)
        # Body - floating with heavy slow bob
        floating_bob = math.sin(pulse * 0.5) * 4
        if attacking:
            _NS_molgravar._draw_mlg_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_molgravar._draw_mlg_idle(surface, boss, x, y - floating_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_molgravar._draw_shard_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_molgravar._draw_thunderclap_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_molgravar._draw_groundslam_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_molgravar._draw_unstoppable_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mlg_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 55)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mlg_previous_timer", 0))
        active = bool(getattr(boss, "_mlg_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._mlg_attack_active = True
            boss._mlg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mlg_attack_frame = int(getattr(boss, "_mlg_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mlg_attack_active = False
            boss._mlg_attack_frame = 0
            active = False
        boss._mlg_previous_timer = timer
        boss._mlg_attack_progress = (
            min(1.0, getattr(boss, "_mlg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_mlg_idle(surface, boss, x, y):
        _NS_molgravar._draw_shadow(surface, x, y + 62)
        _NS_molgravar._draw_orbiting_rocks(surface, x, y, boss.pulse)
        _NS_molgravar._draw_falling_dust(surface, x, y, boss.pulse)
        _NS_molgravar._draw_mlg_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_mlg_attack(surface, boss, x, y):
        progress = getattr(boss, "_mlg_attack_progress", 0.0)
        # Big golem punch: wind-up → slam → recovery
        if progress < 0.35:
            t = progress / 0.35
            swing_offset = -int(t * 4) * boss.direction
            lift = int(t * 6)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            swing_offset = int((-4 + t * 16)) * boss.direction
            lift = int(6 - t * 10)
        else:
            t = (progress - 0.6) / 0.4
            swing_offset = int(12 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4)
        _NS_molgravar._draw_shadow(surface, x + swing_offset, y + 62)
        _NS_molgravar._draw_orbiting_rocks(surface, x + swing_offset, y - lift,
                                           boss.pulse, intense=True)
        _NS_molgravar._draw_falling_dust(surface, x + swing_offset, y - lift,
                                          boss.pulse, intense=True)
        _NS_molgravar._draw_mlg_body(surface, x + swing_offset, y - lift,
                                      boss.direction, boss.pulse, "attack", progress)
        _NS_molgravar._draw_punch_impact(surface, x + swing_offset, y - lift,
                                          boss.direction, progress)
    # ============================================================
    # BODY (upright bipedal stone golem)
    # ============================================================
    def _draw_mlg_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw massive golem body: back spikes, torso, arms, head, shoulders."""
        # Order: back spikes → legs (short) → torso → arms → shoulder crystals → head → head crystals
        _NS_molgravar._draw_back_spikes(surface, cx, cy - 10, facing, phase)
        _NS_molgravar._draw_golem_lower(surface, cx, cy + 20, phase)  # stumpy leg base
        _NS_molgravar._draw_golem_torso(surface, cx, cy, facing, phase)
        _NS_molgravar._draw_golem_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_molgravar._draw_shoulder_spikes(surface, cx, cy - 8, facing, phase)
        # Head with dip/lift on attack
        head_dip = 0
        head_lunge = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                head_dip = -int(t * 2)
                head_lunge = -int(t * 2) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                head_dip = int(-2 + t * 5)
                head_lunge = int((-2 + t * 8)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                head_dip = int(3 * (1 - t))
                head_lunge = int(6 * (1 - t)) * facing
        _NS_molgravar._draw_golem_head(surface, cx + head_lunge, cy - 22 + head_dip,
                                        facing, phase, action)
        _NS_molgravar._draw_head_crown_spikes(surface, cx + head_lunge,
                                               cy - 30 + head_dip, facing, phase)
    def _draw_golem_lower(surface, cx, cy, phase):
        """Stumpy stone base (no legs, just cluster of rocks - floating golem)."""
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        # Base rock cluster (like feet/pedestal)
        # Big central rock
        base_pts = [
            (cx - 14, cy - 4), (cx - 18, cy + 2), (cx - 16, cy + 10),
            (cx - 8, cy + 14), (cx + 8, cy + 14), (cx + 16, cy + 10),
            (cx + 18, cy + 2), (cx + 14, cy - 4),
        ]
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in base_pts])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], base_pts)
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
            (cx - 12, cy - 3), (cx - 15, cy + 2), (cx - 13, cy + 8),
            (cx - 6, cy + 11), (cx + 6, cy + 11), (cx + 13, cy + 8),
            (cx + 15, cy + 2), (cx + 12, cy - 3),
        ])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
            (cx - 10, cy - 2), (cx - 12, cy + 4), (cx - 6, cy + 8),
            (cx + 6, cy + 8), (cx + 12, cy + 4), (cx + 10, cy - 2),
        ])
        # Rock plate lines (fracture texture)
        for pts in [
            [(cx - 8, cy - 2), (cx - 4, cy + 4), (cx - 6, cy + 8)],
            [(cx + 8, cy - 2), (cx + 4, cy + 4), (cx + 6, cy + 8)],
            [(cx, cy - 1), (cx - 2, cy + 5), (cx + 2, cy + 10)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, _NS_molgravar.PALETTE["rock_darkest"],
                                 pts[i], pts[i + 1], 1)
        # LAVA CRACKS glowing on base
        crack_alpha = _NS_molgravar._alpha(200 + math.sin(phase * 2) * 55)
        for pts in [
            [(cx - 8, cy + 2), (cx - 4, cy + 5), (cx - 6, cy + 9)],
            [(cx + 8, cy + 2), (cx + 4, cy + 5), (cx + 6, cy + 9)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                                 pts[i], pts[i + 1], 2)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_hot"], crack_alpha),
                                 pts[i], pts[i + 1], 1)
        # Small pebbles falling below
        for i in range(4):
            pt = (phase * 0.5 + i * 0.25) % 1.0
            px = cx - 12 + i * 8 + int(math.sin(phase + i) * 2)
            py = cy + 14 + int(pt * 12)
            alpha = _NS_molgravar._alpha(200 * (1 - pt))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_dark"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_mid"], alpha),
                             (px, py, 1, 1))
    def _draw_golem_torso(surface, cx, cy, facing, phase):
        """Massive stone torso with lava cracks."""
        breath = math.sin(phase * 0.6) * 1
        # Big blocky torso (wide shoulders, tapered waist)
        torso_shape = [
            (cx - 16, cy + 15),          # bottom left
            (cx - 20, cy + 6),           # waist left
            (cx - 22, cy - 4 - int(breath)),  # rib left
            (cx - 20, cy - 12),          # shoulder left
            (cx - 12, cy - 16),          # neck side left
            (cx - 6, cy - 18),           # neck base left
            (cx + 6, cy - 18),
            (cx + 12, cy - 16),
            (cx + 20, cy - 12),
            (cx + 22, cy - 4 - int(breath)),
            (cx + 20, cy + 6),
            (cx + 16, cy + 15),
            (cx + 8, cy + 18),
            (cx - 8, cy + 18),
        ]
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in torso_shape])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], torso_shape)
        # Stone layer (chunky plates)
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
            (cx - 15, cy + 14), (cx - 18, cy + 5), (cx - 20, cy - 4),
            (cx - 18, cy - 11), (cx - 10, cy - 15), (cx + 10, cy - 15),
            (cx + 18, cy - 11), (cx + 20, cy - 4), (cx + 18, cy + 5),
            (cx + 15, cy + 14), (cx + 7, cy + 16), (cx - 7, cy + 16),
        ])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
            (cx - 12, cy + 12), (cx - 15, cy + 4), (cx - 17, cy - 3),
            (cx - 14, cy - 10), (cx - 6, cy - 12), (cx + 6, cy - 12),
            (cx + 14, cy - 10), (cx + 17, cy - 3), (cx + 15, cy + 4),
            (cx + 12, cy + 12), (cx + 5, cy + 14), (cx - 5, cy + 14),
        ])
        # Chest highlight
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_light"], [
            (cx - 6, cy - 8), (cx + 6, cy - 8), (cx + 8, cy - 2),
            (cx + 4, cy + 5), (cx - 4, cy + 5), (cx - 8, cy - 2),
        ])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_shine"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6), (cx + 4, cy - 2),
            (cx + 2, cy + 2), (cx - 2, cy + 2), (cx - 4, cy - 2),
        ])
        # Rock plate fracture lines
        for pts in [
            [(cx - 14, cy - 8), (cx - 8, cy - 4), (cx - 12, cy + 4), (cx - 10, cy + 12)],
            [(cx + 14, cy - 8), (cx + 8, cy - 4), (cx + 12, cy + 4), (cx + 10, cy + 12)],
            [(cx, cy - 10), (cx - 3, cy - 2), (cx + 3, cy + 6), (cx, cy + 14)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, _NS_molgravar.PALETTE["rock_darkest"],
                                 pts[i], pts[i + 1], 1)
        # ✨ LAVA CRACKS (glowing orange veins on torso)
        crack_pulse = math.sin(phase * 1.5) * 0.4 + 0.6
        crack_alpha = _NS_molgravar._alpha(230 * crack_pulse)
        # Main chest lava veins
        for pts in [
            # Left chest crack
            [(cx - 10, cy - 10), (cx - 6, cy - 4), (cx - 8, cy + 3), (cx - 5, cy + 10)],
            # Right chest crack
            [(cx + 10, cy - 10), (cx + 6, cy - 4), (cx + 8, cy + 3), (cx + 5, cy + 10)],
            # Center vertical
            [(cx, cy - 12), (cx - 1, cy - 6), (cx + 1, cy), (cx, cy + 6), (cx - 1, cy + 12)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_dark"], crack_alpha),
                                 pts[i], pts[i + 1], 3)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                                 pts[i], pts[i + 1], 2)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_light"], crack_alpha),
                                 pts[i], pts[i + 1], 1)
        # Bright lava spots (glowing points)
        for spot in [(cx, cy - 6), (cx, cy + 2), (cx - 8, cy), (cx + 8, cy)]:
            _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_hot"], crack_alpha),
                                     spot, 2)
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_shine"], (spot[0], spot[1], 1, 1))
        # Gold trim on belt/waist
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["gold_dark"], (cx - 14, cy + 12, 28, 4))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["gold_mid"], (cx - 13, cy + 13, 26, 2))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["gold_light"], (cx - 2, cy + 13, 4, 1))
    def _draw_golem_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two massive stone arms."""
        idle_sway = math.sin(phase * 0.5) * 2
        # FAR ARM (behind body)
        far_shoulder = (cx - facing * 14, cy - 10)
        far_elbow = (cx - facing * 20, cy - 2)
        far_fist = (cx - facing * 22, cy + 12 + int(idle_sway * 0.3))
        _NS_molgravar._draw_stone_arm(surface, far_shoulder, far_elbow, far_fist,
                                       facing, phase, dark=True)
        # NEAR ARM (front) — SWING on attack
        if action == "attack":
            # Massive fist swing
            if attack_progress < 0.35:
                # Wind-up: arm back+up
                t = attack_progress / 0.35
                angle = math.radians(-40 - t * 70) * facing
                arm_len = 24
            elif attack_progress < 0.6:
                # SLAM: swing forward+down
                t = (attack_progress - 0.35) / 0.25
                angle = math.radians(-110 + t * 160) * facing
                arm_len = 26
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                angle = math.radians(50 - t * 60) * facing
                arm_len = 24
            shoulder = (cx + facing * 14, cy - 10)
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            fist = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_molgravar._draw_stone_arm(surface, shoulder, elbow, fist,
                                           facing, phase, dark=False, big_fist=True)
        else:
            near_shoulder = (cx + facing * 14, cy - 10)
            near_elbow = (cx + facing * 20, cy - 1 + int(idle_sway * 0.3))
            near_fist = (cx + facing * 22, cy + 14 + int(idle_sway * 0.5))
            _NS_molgravar._draw_stone_arm(surface, near_shoulder, near_elbow, near_fist,
                                           facing, phase, dark=False)
    def _draw_stone_arm(surface, shoulder, elbow, fist, facing, phase,
                        dark=False, big_fist=False):
        """Chunky stone arm with lava cracks."""
        stone_dark_c = _NS_molgravar.PALETTE["stone_darkest"] if dark else _NS_molgravar.PALETTE["stone_dark"]
        stone_mid_c = _NS_molgravar.PALETTE["stone_dark"] if dark else _NS_molgravar.PALETTE["stone_mid"]
        stone_light_c = _NS_molgravar.PALETTE["stone_mid"] if dark else _NS_molgravar.PALETTE["stone_light"]
        # Shadow
        _NS_molgravar._aaline(surface, _NS_molgravar.PALETTE["shadow_deep"],
                               (shoulder[0] + 2, shoulder[1] + 3),
                               (elbow[0] + 2, elbow[1] + 3), 10)
        _NS_molgravar._aaline(surface, _NS_molgravar.PALETTE["shadow_deep"],
                               (elbow[0] + 2, elbow[1] + 3),
                               (fist[0] + 2, fist[1] + 3), 9)
        # Upper arm (thick)
        _NS_molgravar._aaline(surface, _NS_molgravar.PALETTE["stone_darkest"], shoulder, elbow, 10)
        _NS_molgravar._aaline(surface, stone_dark_c, shoulder, elbow, 8)
        _NS_molgravar._aaline(surface, stone_mid_c,
                               (shoulder[0], shoulder[1] - 1),
                               (elbow[0], elbow[1] - 1), 5)
        _NS_molgravar._aaline(surface, stone_light_c,
                               (shoulder[0], shoulder[1] - 2),
                               (elbow[0], elbow[1] - 2), 2)
        # Lava crack along upper arm
        crack_alpha = _NS_molgravar._alpha(200 + math.sin(phase * 2) * 55)
        _NS_molgravar._aaline(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                               shoulder, elbow, 2)
        _NS_molgravar._aaline(surface, (*_NS_molgravar.PALETTE["lava_hot"], crack_alpha),
                               shoulder, elbow, 1)
        # Elbow joint (chunky rock)
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["stone_darkest"],
                         (elbow[0] - 4, elbow[1] - 4, 9, 9))
        pygame.draw.rect(surface, stone_dark_c, (elbow[0] - 4, elbow[1] - 4, 8, 8))
        pygame.draw.rect(surface, stone_mid_c, (elbow[0] - 3, elbow[1] - 3, 6, 6))
        pygame.draw.rect(surface, stone_light_c, (elbow[0] - 2, elbow[1] - 3, 3, 3))
        # Forearm
        _NS_molgravar._aaline(surface, _NS_molgravar.PALETTE["stone_darkest"], elbow, fist, 9)
        _NS_molgravar._aaline(surface, stone_dark_c, elbow, fist, 7)
        _NS_molgravar._aaline(surface, stone_mid_c,
                               (elbow[0], elbow[1] - 1), (fist[0], fist[1] - 1), 4)
        _NS_molgravar._aaline(surface, stone_light_c,
                               (elbow[0], elbow[1] - 2), (fist[0], fist[1] - 2), 1)
        # Massive stone FIST
        fist_size = 8 if big_fist else 6
        _NS_molgravar._draw_stone_fist(surface, fist, facing, phase, fist_size, dark=dark)
    def _draw_stone_fist(surface, fist, facing, phase, size, dark=False):
        """Boulder-sized fist with lava cracks."""
        stone_dark_c = _NS_molgravar.PALETTE["stone_darkest"] if dark else _NS_molgravar.PALETTE["stone_dark"]
        stone_mid_c = _NS_molgravar.PALETTE["stone_dark"] if dark else _NS_molgravar.PALETTE["stone_mid"]
        stone_light_c = _NS_molgravar.PALETTE["stone_mid"] if dark else _NS_molgravar.PALETTE["stone_light"]
        fx, fy = fist
        # Chunky fist shape (irregular hexagon)
        fist_pts = [
            (fx - size, fy - size + 1),
            (fx - size + 2, fy - size - 1),
            (fx + size - 2, fy - size - 1),
            (fx + size, fy - size + 2),
            (fx + size, fy + size - 1),
            (fx + size - 2, fy + size + 1),
            (fx - size + 2, fy + size + 1),
            (fx - size, fy + size - 1),
        ]
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in fist_pts])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], fist_pts)
        # Inner layers
        _NS_molgravar._poly(surface, stone_dark_c, [
            (fx - size + 1, fy - size + 1), (fx - size + 2, fy - size),
            (fx + size - 2, fy - size), (fx + size - 1, fy - size + 1),
            (fx + size - 1, fy + size - 1), (fx + size - 2, fy + size),
            (fx - size + 2, fy + size), (fx - size + 1, fy + size - 1),
        ])
        _NS_molgravar._poly(surface, stone_mid_c, [
            (fx - size + 2, fy - 2), (fx - size + 3, fy - size + 3),
            (fx + size - 3, fy - size + 3), (fx + size - 2, fy - 2),
            (fx + size - 3, fy + size - 3), (fx - size + 3, fy + size - 3),
        ])
        pygame.draw.rect(surface, stone_light_c, (fx - 2, fy - 3, 4, 3))
        # Lava crack across fist
        crack_alpha = _NS_molgravar._alpha(240 + math.sin(phase * 2) * 15)
        pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_dark"], crack_alpha),
                         (fx - size + 2, fy - 2), (fx + size - 2, fy + 1), 3)
        pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                         (fx - size + 2, fy - 2), (fx + size - 2, fy + 1), 2)
        pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_hot"], crack_alpha),
                         (fx - size + 2, fy - 2), (fx + size - 2, fy + 1), 1)
        # Central hot spot
        _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_hot"], crack_alpha),
                                 (fx, fy - 1), 2)
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_shine"], (fx, fy - 1, 1, 1))
        # Small spikes on knuckles (facing outward)
        for i, kx in enumerate((-4, 0, 4)):
            spike_x = fx + kx
            spike_top_y = fy - size - 2
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"], [
                (spike_x - 2 + 1, fy - size + 1),
                (spike_x + 1, spike_top_y + 1),
                (spike_x + 2 + 1, fy - size + 1),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shard_dark"], [
                (spike_x - 2, fy - size),
                (spike_x, spike_top_y),
                (spike_x + 2, fy - size),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shard_mid"], [
                (spike_x - 1, fy - size),
                (spike_x, spike_top_y),
                (spike_x + 1, fy - size),
            ])
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_shine"],
                             (spike_x, spike_top_y, 1, 1))
        # Glow around fist (indicating molten power)
        for r in range(size + 4, 0, -2):
            alpha = _NS_molgravar._alpha(40 * (size + 4 - r) / (size + 4) * crack_alpha / 255)
            _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha), fist, r)
    def _draw_back_spikes(surface, cx, cy, facing, phase):
        """Massive shard spikes growing from back (like Malphite's iconic back)."""
        pulse = math.sin(phase * 0.5) * 0.15 + 0.85
        # Multiple large stone shards behind body (2 rows for depth)
        for row_i, (side_range, size_mult) in enumerate([
            ((-1, 1), 1.0),   # back row (bigger)
        ]):
            for side_mult in side_range:
                base_x = cx + side_mult * 6
                base_y = cy
                # 3 shards per side going up
                for i, (dx, dy, length, width) in enumerate([
                    (side_mult * 4, -6, int(24 * size_mult), 5),
                    (side_mult * 10, -3, int(28 * size_mult), 5),
                    (side_mult * 14, 4, int(22 * size_mult), 4),
                ]):
                    tip_x = base_x + dx + side_mult * length // 3
                    tip_y = base_y + dy - length
                    bx = base_x + dx
                    by = base_y + dy
                    perp_x = -side_mult
                    a = (bx + perp_x * width, by + width)
                    b = (bx - perp_x * width, by - width // 2)
                    _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"],
                                         [(tip_x + 2, tip_y + 2),
                                          (a[0] + 2, a[1] + 2),
                                          (b[0] + 2, b[1] + 2)])
                    _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"],
                                         [(tip_x, tip_y), a, b])
                    _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
                        (tip_x, tip_y),
                        (int((tip_x + a[0]) / 2), int((tip_y + a[1]) / 2)),
                        (int((tip_x + b[0]) / 2), int((tip_y + b[1]) / 2)),
                    ])
                    _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
                        (tip_x, tip_y),
                        (int((tip_x * 3 + a[0]) / 4), int((tip_y * 3 + a[1]) / 4)),
                        (int((tip_x * 3 + b[0]) / 4), int((tip_y * 3 + b[1]) / 4)),
                    ])
                    # Highlight edge
                    pygame.draw.line(surface, _NS_molgravar.PALETTE["stone_light"],
                                     (tip_x, tip_y),
                                     (int((tip_x + b[0]) / 2), int((tip_y + b[1]) / 2)), 1)
                    # Sharp tip (shard_light)
                    pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_light"],
                                     (tip_x, tip_y, 1, 1))
                    pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_shine"],
                                     (tip_x, tip_y, 1, 1))
                    # Lava crack up shard
                    crack_alpha = _NS_molgravar._alpha(180 * pulse)
                    pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                                     (bx, by), (tip_x, tip_y), 1)
    def _draw_shoulder_spikes(surface, cx, cy, facing, phase):
        """Sharp shards on shoulders."""
        for side in (-1, 1):
            base_x = cx + side * 16
            base_y = cy - 2
            # Cluster of 2 spikes
            for spike_i, (dx, dy, length) in enumerate([
                (side * 2, -2, 10),
                (side * 5, 1, 8),
            ]):
                tip_x = base_x + dx + side * 3
                tip_y = base_y + dy - length
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (base_x - 2 + 1, base_y + 1),
                    (base_x + 3 + 1, base_y + 1),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], [
                    (tip_x, tip_y), (base_x - 2, base_y), (base_x + 3, base_y),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + base_x - 2) / 2), int((tip_y + base_y) / 2)),
                    (int((tip_x + base_x + 3) / 2), int((tip_y + base_y) / 2)),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
                    (tip_x, tip_y),
                    (int((tip_x * 3 + base_x - 2) / 4), int((tip_y * 3 + base_y) / 4)),
                    (int((tip_x * 3 + base_x + 3) / 4), int((tip_y * 3 + base_y) / 4)),
                ])
                pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_light"], (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_shine"], (tip_x, tip_y, 1, 1))
    def _draw_golem_head(surface, cx, cy, facing, phase, action):
        """Blocky stone head with glowing green eye."""
        # Head is chunky rock cluster
        head_shape = [
            (cx - 8, cy + 6), (cx - 10, cy + 2), (cx - 10, cy - 4),
            (cx - 7, cy - 8), (cx - 2, cy - 10), (cx + 4, cy - 10),
            (cx + 9, cy - 7), (cx + 11, cy - 2), (cx + 10, cy + 4),
            (cx + 7, cy + 7), (cx + 1, cy + 8), (cx - 5, cy + 7),
        ]
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_shape])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], head_shape)
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
            (cx - 8, cy + 5), (cx - 9, cy + 1), (cx - 9, cy - 3),
            (cx - 6, cy - 7), (cx - 2, cy - 9), (cx + 4, cy - 9),
            (cx + 8, cy - 6), (cx + 10, cy - 2), (cx + 9, cy + 3),
            (cx + 6, cy + 6), (cx + 1, cy + 7), (cx - 5, cy + 6),
        ])
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
            (cx - 6, cy + 3), (cx - 7, cy - 2), (cx - 4, cy - 6),
            (cx + 3, cy - 6), (cx + 7, cy - 2), (cx + 7, cy + 3),
            (cx + 4, cy + 5), (cx - 3, cy + 5),
        ])
        # Highlight
        _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_light"], [
            (cx + facing * 2, cy - 5),
            (cx + facing * 5, cy - 3),
            (cx + facing * 4, cy),
            (cx + facing, cy - 2),
        ])
        # LAVA CRACKS on head
        crack_alpha = _NS_molgravar._alpha(220 + math.sin(phase * 2) * 35)
        for pts in [
            [(cx - 6, cy - 4), (cx - 3, cy - 1), (cx - 5, cy + 3)],
            [(cx + 6, cy - 4), (cx + 3, cy - 1), (cx + 5, cy + 3)],
            [(cx - 2, cy - 8), (cx, cy - 4), (cx + 2, cy - 8)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_dark"], crack_alpha),
                                 pts[i], pts[i + 1], 2)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                                 pts[i], pts[i + 1], 1)
        # SINGLE BIG GLOWING EYE (Malphite has one prominent glowing eye area)
        _NS_molgravar._draw_golem_eye(surface, cx + facing * 1, cy - 2, facing, phase)
        # Fracture lines
        pygame.draw.line(surface, _NS_molgravar.PALETTE["rock_darkest"],
                         (cx - 7, cy - 5), (cx - 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_molgravar.PALETTE["rock_darkest"],
                         (cx + 7, cy - 5), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_molgravar.PALETTE["rock_darkest"],
                         (cx - 5, cy + 5), (cx + 5, cy + 4), 1)
        # "Mouth" — dark cavity/slit
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["shadow_deep"],
                         (cx - 3, cy + 3, 6, 2))
        # Lava glow in mouth
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_dark"], (cx - 2, cy + 3, 4, 1))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_mid"], (cx - 1, cy + 3, 2, 1))
    def _draw_golem_eye(surface, ex, ey, facing, phase):
        """Massive glowing green-yellow eye (like Malphite's shard eye)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Deep socket
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["shadow_deep"],
                         (ex - 3, ey - 2, 7, 5))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["eye_socket"],
                         (ex - 2, ey - 2, 6, 5))
        # Glow halo (large!)
        for r in range(8, 0, -1):
            alpha = _NS_molgravar._alpha(100 * (8 - r) / 8 * pulse)
            _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["eye_mid"], alpha),
                                     (ex + 1, ey), r)
        # Bright core
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["eye_dark"], (ex - 2, ey - 1, 6, 3))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["eye_mid"], (ex - 1, ey - 1, 5, 3))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["eye_light"], (ex, ey - 1, 4, 2))
        pygame.draw.rect(surface, _NS_molgravar.PALETTE["eye_glow"], (ex + 1, ey, 2, 1))
        # Vertical pupil slit
        pygame.draw.line(surface, _NS_molgravar.PALETTE["shadow_deep"],
                         (ex + 1, ey - 1), (ex + 1, ey + 1), 1)
    def _draw_head_crown_spikes(surface, cx, cy, facing, phase):
        """Small crown of spikes on top of head."""
        for i, (dx, height) in enumerate([
            (-5, 5), (-2, 7), (1, 8), (4, 6),
        ]):
            spike_x = cx + dx
            spike_tip_y = cy - height
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"], [
                (spike_x - 1 + 1, cy + 1),
                (spike_x + 1, spike_tip_y + 1),
                (spike_x + 1 + 1, cy + 1),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], [
                (spike_x - 1, cy), (spike_x, spike_tip_y), (spike_x + 1, cy),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
                (spike_x - 1, cy), (spike_x, spike_tip_y),
                (int((spike_x + spike_x + 1) / 2), int((spike_tip_y + cy) / 2)),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
                (spike_x, cy - 1), (spike_x, spike_tip_y),
                (int((spike_x * 3 + spike_x + 1) / 4),
                 int((spike_tip_y * 3 + cy) / 4)),
            ])
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_light"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["shard_shine"],
                             (spike_x, spike_tip_y, 1, 1))
    # ============================================================
    # PUNCH IMPACT SHOCKWAVE (basic attack)
    # ============================================================
    def _draw_punch_impact(surface, cx, cy, facing, progress):
        """Orange shockwave arc during punch."""
        if progress < 0.4 or progress > 0.8:
            return
        t = (progress - 0.4) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_molgravar._alpha(255 * intensity)
        # Impact point (in front of fist)
        impact_cx = cx + facing * 30
        impact_cy = cy + 8
        r = int(8 + t * 20)
        # Multi-layer shockwave arc
        for layer_i, (thickness, color) in enumerate([
            (4, (*_NS_molgravar.PALETTE["lava_darkest"], alpha // 2)),
            (3, (*_NS_molgravar.PALETTE["lava_dark"], alpha)),
            (2, (*_NS_molgravar.PALETTE["lava_mid"], alpha)),
            (1, (*_NS_molgravar.PALETTE["lava_light"], alpha)),
        ]):
            # Semicircle arc facing forward
            start_ang = math.radians(-90) if facing > 0 else math.radians(90)
            end_ang = math.radians(90) if facing > 0 else math.radians(270)
            steps = 12
            prev = None
            for i in range(steps + 1):
                st = i / steps
                a = start_ang + (end_ang - start_ang) * st
                px = impact_cx + int(math.cos(a) * r)
                py = impact_cy + int(math.sin(a) * r)
                if prev is not None:
                    pygame.draw.line(surface, color, prev, (px, py), thickness)
                prev = (px, py)
        # Radial sparks
        for i in range(8):
            ang = math.radians(-80 + i * 20) if facing > 0 else math.radians(100 + i * 20)
            spark_r = r + int(math.sin(i + progress * 10) * 4)
            sx = impact_cx + int(math.cos(ang) * spark_r)
            sy = impact_cy + int(math.sin(ang) * spark_r)
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_shine"], alpha), (sx, sy, 1, 1))
        # Small rock debris flying
        for i in range(5):
            ang = math.radians(-70 + i * 30) if facing > 0 else math.radians(110 + i * 30)
            debris_r = int(r * 0.7 + math.sin(progress * 5 + i) * 3)
            dx_pt = impact_cx + int(math.cos(ang) * debris_r)
            dy_pt = impact_cy + int(math.sin(ang) * debris_r)
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_dark"], alpha),
                             (dx_pt, dy_pt, 3, 3))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_mid"], alpha),
                             (dx_pt, dy_pt, 2, 2))
    # ============================================================
    # ORBITING ROCKS + FALLING DUST (ambient)
    # ============================================================
    def _draw_orbiting_rocks(surface, cx, cy, phase, intense=False):
        """Small rocks orbiting around boss."""
        strength = 1.3 if intense else 1.0
        for i in range(6):
            angle = phase * 0.4 + i * math.pi / 3
            radius = 45 + int(math.sin(phase + i) * 8)
            rx = cx + int(math.cos(angle) * radius)
            ry = cy + int(math.sin(angle) * radius * 0.5)
            size = 3 if i % 2 == 0 else 2
            # Shadow
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["shadow_deep"],
                             (rx + 1, ry + 1, size + 1, size + 1))
            # Rock chunk
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["stone_darkest"],
                             (rx, ry, size, size))
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["stone_dark"],
                             (rx, ry, size, size - 1))
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["stone_mid"],
                             (rx + 1, ry, size - 1, 1))
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["stone_shine"],
                             (rx + 1, ry, 1, 1))
            # Lava glow inside orbiting rock
            alpha = _NS_molgravar._alpha(150 * strength)
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                             (rx + size // 2, ry + size // 2, 1, 1))
    def _draw_falling_dust(surface, cx, cy, phase, intense=False):
        """Dust particles falling around boss."""
        strength = 1.4 if intense else 1.0
        for i in range(8):
            t = (phase * 0.6 + i * 0.13) % 1.0
            dx = cx - 30 + i * 8 + int(math.sin(phase + i) * 3)
            dy = cy - 25 + int(t * 60)
            alpha = _NS_molgravar._alpha(180 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["dust_mid"], alpha),
                                 (dx, dy, 2, 2))
                pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["dust_light"], alpha),
                                 (dx, dy, 1, 1))
        # Lava embers rising
        for i in range(6):
            t = (phase * 0.5 + i * 0.17) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 20 - int(t * 30)
            alpha = _NS_molgravar._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT / GROUND (TRUE BOSS scale)
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius, 140 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 3, 2, 180), (5, 10, 150, 14))
        pygame.draw.ellipse(shadow, (35, 20, 10, 120), (12, 12, 136, 10))
        surface.blit(shadow, (x - 80, y - 16))
    def _draw_lava_aura(surface, x, y, phase):
        """Large orange lava aura + heat haze (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        # Outer heat glow
        for radius in range(105, 5, -5):
            alpha = _NS_molgravar._alpha((105 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_molgravar._aacircle(aura, (*_NS_molgravar.PALETTE["dust_dark"], alpha),
                                         (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_molgravar._alpha((70 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_molgravar._aacircle(aura, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                         (120, 100), radius)
        # Lava orange inner
        for radius in range(40, 5, -3):
            alpha = _NS_molgravar._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_molgravar._aacircle(aura, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                         (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 55 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large ground ring with lava runes (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_molgravar.PALETTE["dust_dark"], 200),
                            (5, 22, 180, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_molgravar.PALETTE["lava_darkest"], 220),
                            (14, 24, 162, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_molgravar.PALETTE["lava_dark"], 230),
                            (25, 26, 140, 20), 1)
        pygame.draw.ellipse(ring, (*_NS_molgravar.PALETTE["lava_mid"], 180),
                            (40, 28, 110, 16), 1)
        # Runes
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 34 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_molgravar.PALETTE["lava_hot"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_molgravar.PALETTE["lava_hot"],
                                        _NS_molgravar._alpha(150 * pulse)),
                                (15, 14, 160, 42), 1)
        surface.blit(ring, (x - 95, y - 30))
    # ============================================================
    # SKILL Q - SEISMIC SHARD (range projectile)
    # ============================================================
    def _draw_shard_ground(surface, boss, x, y, timer, phase):
        """Small crack line under boss during charge."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            alpha = _NS_molgravar._alpha(180 * (progress / 0.3))
            for i in range(3):
                cx = x - 15 + i * 15
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                 (cx, y + 55), (cx + 5, y + 60), 2)
    def _draw_shard_foreground(surface, boss, x, y, timer, phase):
        """Rock shard projectile with orange trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_molgravar._target_position(boss, x, y)
        if progress < 0.3:
            # Charge in hand
            t = progress / 0.3
            hand_x = x + facing * 24
            hand_y = y + 10
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_molgravar._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                         (hand_x, hand_y), r)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_mid"], (hand_x, hand_y), cr - 2)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_hot"], (hand_x, hand_y),
                                     max(1, cr - 4))
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_shine"], (hand_x, hand_y),
                                     max(1, cr - 6))
            # Rock forming
            for a in range(4):
                ang = a * math.pi / 2 + phase * 2
                rx = hand_x + int(math.cos(ang) * (cr + 2))
                ry = hand_y + int(math.sin(ang) * (cr + 2))
                pygame.draw.rect(surface, _NS_molgravar.PALETTE["stone_mid"], (rx, ry, 2, 2))
        else:
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 26
            start_y = y + 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Lance direction
            dx = tx - start_x
            dy = ty - start_y
            length = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / length, dy / length
            perp_x, perp_y = -uy, ux
            # Rock shard shape (elongated diamond)
            lance_len = 16
            tip = (bx + int(ux * lance_len // 2), by + int(uy * lance_len // 2))
            tail = (bx - int(ux * lance_len // 2), by - int(uy * lance_len // 2))
            side_a = (bx + int(perp_x * 4), by + int(perp_y * 4))
            side_b = (bx - int(perp_x * 4), by - int(perp_y * 4))
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"], [
                (tip[0] + 2, tip[1] + 2), (side_a[0] + 2, side_a[1] + 2),
                (tail[0] + 2, tail[1] + 2), (side_b[0] + 2, side_b[1] + 2),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"],
                                 [tip, side_a, tail, side_b])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
                tip,
                (int((tip[0] + side_a[0]) / 2), int((tip[1] + side_a[1]) / 2)),
                (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)),
                (int((tip[0] + side_b[0]) / 2), int((tip[1] + side_b[1]) / 2)),
            ])
            _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
                tip,
                (int((tip[0] * 3 + side_a[0]) / 4), int((tip[1] * 3 + side_a[1]) / 4)),
                (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)),
                (int((tip[0] * 3 + side_b[0]) / 4), int((tip[1] * 3 + side_b[1]) / 4)),
            ])
            # Lava crack down center
            pygame.draw.line(surface, _NS_molgravar.PALETTE["lava_hot"], tip, tail, 1)
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_shine"], (tip[0], tip[1], 1, 1))
            # Orange comet trail behind shard
            for i in range(1, 10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_molgravar._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                         (px, py), size)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                         (px, py), max(1, size - 1))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                         (px, py), max(1, size - 2))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                         (px, py), max(1, size - 3))
                # Rock chunks in trail
                if i < 4:
                    for s in range(2):
                        rock_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                        rock_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                        pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_mid"], alpha),
                                         (rock_x, rock_y, 2, 2))
            # Glow around shard
            for r in range(11, 3, -2):
                alpha = _NS_molgravar._alpha(80 * (11 - r) / 11)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_light"], alpha),
                                         (bx, by), r)
            # Impact burst
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 28)
                alpha = _NS_molgravar._alpha(240 * (1 - st))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                         (tx, ty), radius + 3, 3)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                         (tx, ty), radius, 3)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                         (tx, ty), max(1, radius - 10), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_shine"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - THUNDERCLAP (AoE shockwave around self)
    # ============================================================
    def _draw_thunderclap_ground(surface, boss, x, y, timer, phase):
        """Expanding orange shockwave rings on ground."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for ring_i in range(3):
            ring_t = max(0, progress - ring_i * 0.13)
            r = int(90 * min(1.0, ring_t * 1.5))
            if r < 3:
                continue
            alpha = _NS_molgravar._alpha(230 * (1 - ring_t))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                (x - r, y + 55 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                (x - r + 3, y + 55 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                (x - r + 6, y + 55 - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 2)
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                (x - r + 10, y + 55 - r // 3 + 6,
                                 r * 2 - 20, r * 2 // 3 - 12), 1)
    def _draw_thunderclap_foreground(surface, boss, x, y, timer, phase):
        """Armor buff glow around body + rock chunks flying."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Armor glow (pulsing orange around body)
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(45, 5, -3):
            alpha = _NS_molgravar._alpha(80 * (45 - r) / 45 * pulse * (1 - progress * 0.5))
            _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                     (x, y), r)
        # Rock chunks flying outward
        num_chunks = 12
        for i in range(num_chunks):
            angle = i * math.pi * 2 / num_chunks
            chunk_r = int(50 + progress * 40)
            cx_chunk = x + int(math.cos(angle) * chunk_r)
            cy_chunk = y + int(math.sin(angle) * chunk_r * 0.6)
            alpha = _NS_molgravar._alpha(220 * (1 - progress))
            # Shadow
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["shadow_deep"], alpha),
                             (cx_chunk + 1, cy_chunk + 1, 4, 4))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_dark"], alpha),
                             (cx_chunk, cy_chunk, 4, 4))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_mid"], alpha),
                             (cx_chunk, cy_chunk, 3, 2))
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_light"], alpha),
                             (cx_chunk + 1, cy_chunk, 1, 1))
            # Lava glow on chunk
            pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                             (cx_chunk + 1, cy_chunk + 1, 1, 1))
        # Rising heat particles
        for i in range(10):
            t = (phase * 0.7 + i * 0.1) % 1.0
            hx = x - 30 + i * 6 + int(math.sin(phase + i) * 3)
            hy = y + 20 - int(t * 40)
            alpha = _NS_molgravar._alpha(220 * (1 - t) * (1 - progress * 0.3))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                 (hx, hy, 2, 2))
                pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                 (hx, hy, 1, 1))
    # ============================================================
    # SKILL E - GROUND SLAM (AoE at target: spike burst)
    # ============================================================
    def _draw_groundslam_ground(surface, boss, x, y, timer, phase):
        """Ground crack pattern at target."""
        tx, ty = _NS_molgravar._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2))
        if r > 3:
            # Base crack pool
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_dark"], 190),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_mid"], 150),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Cracks radiating out
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.1
                crack_start = (tx + int(math.cos(angle) * r * 0.4),
                                ty + int(math.sin(angle) * r * 0.4 * 0.6))
                crack_end = (tx + int(math.cos(angle) * r),
                              ty + int(math.sin(angle) * r * 0.6))
                pygame.draw.line(surface, _NS_molgravar.PALETTE["lava_hot"],
                                 crack_start, crack_end, 2)
                pygame.draw.line(surface, _NS_molgravar.PALETTE["lava_shine"],
                                 crack_start, crack_end, 1)
    def _draw_groundslam_foreground(surface, boss, x, y, timer, phase):
        """Stone spike erupts from ground at target."""
        tx, ty = _NS_molgravar._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind-up: warning
            t = progress / 0.3
            r = int(30 * t)
            alpha = _NS_molgravar._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
        elif progress < 0.7:
            # ERUPTION: giant spike shoots up
            t = (progress - 0.3) / 0.4
            spike_h = int(80 * math.sin(t * math.pi))
            if spike_h > 5:
                # Main giant spike
                tip = (tx, ty - spike_h)
                base_a = (tx - 14, ty + 5)
                base_b = (tx + 14, ty + 5)
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["shadow_deep"], [
                    (tip[0] + 2, tip[1] + 2),
                    (base_a[0] + 2, base_a[1] + 2),
                    (base_b[0] + 2, base_b[1] + 2),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"],
                                     [tip, base_a, base_b])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
                    tip,
                    (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
                    (int((tip[0] + base_b[0]) / 2), int((tip[1] + base_b[1]) / 2)),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
                    tip,
                    (int((tip[0] * 3 + base_a[0]) / 4), int((tip[1] * 3 + base_a[1]) / 4)),
                    (int((tip[0] * 3 + base_b[0]) / 4), int((tip[1] * 3 + base_b[1]) / 4)),
                ])
                # Highlight edge
                pygame.draw.line(surface, _NS_molgravar.PALETTE["stone_light"],
                                 tip, (int((tip[0] + base_b[0]) / 2),
                                       int((tip[1] + base_b[1]) / 2)), 2)
                # Lava crack up center
                crack_alpha = _NS_molgravar._alpha(240)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_dark"], crack_alpha),
                                 tip, ((base_a[0] + base_b[0]) // 2, base_a[1]), 3)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_mid"], crack_alpha),
                                 tip, ((base_a[0] + base_b[0]) // 2, base_a[1]), 2)
                pygame.draw.line(surface, (*_NS_molgravar.PALETTE["lava_hot"], crack_alpha),
                                 tip, ((base_a[0] + base_b[0]) // 2, base_a[1]), 1)
                # Bright glowing tip
                _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_hot"], tip, 3)
                _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_shine"], tip, 1)
            # Surrounding smaller spikes
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.15
                dist = 30 + int(math.sin(phase + i) * 6)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.6)
                mini_h = int(30 * math.sin(t * math.pi))
                if mini_h < 5:
                    continue
                tip_m = (sx, sy - mini_h)
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_darkest"], [
                    tip_m, (sx - 5, sy), (sx + 5, sy),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_dark"], [
                    tip_m,
                    (int((tip_m[0] + sx - 5) / 2), int((tip_m[1] + sy) / 2)),
                    (int((tip_m[0] + sx + 5) / 2), int((tip_m[1] + sy) / 2)),
                ])
                _NS_molgravar._poly(surface, _NS_molgravar.PALETTE["stone_mid"], [
                    tip_m,
                    (int((tip_m[0] * 3 + sx - 5) / 4), int((tip_m[1] * 3 + sy) / 4)),
                    (int((tip_m[0] * 3 + sx + 5) / 4), int((tip_m[1] * 3 + sy) / 4)),
                ])
                pygame.draw.rect(surface, _NS_molgravar.PALETTE["lava_hot"],
                                 (tip_m[0], tip_m[1], 1, 1))
            # AIRBORNE indicator (small "up" arrows)
            if progress > 0.4:
                for a_i in range(3):
                    ax = tx - 15 + a_i * 15
                    ay = ty - spike_h - 12 - int(math.sin(phase * 4 + a_i) * 3)
                    alpha = _NS_molgravar._alpha(220)
                    # Arrow up
                    pygame.draw.polygon(surface,
                                        (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                        [(ax, ay), (ax - 3, ay + 4), (ax + 3, ay + 4)])
        else:
            # Aftermath: crumbling debris
            t = (progress - 0.7) / 0.3
            for i in range(12):
                fall_t = (phase * 0.9 + i * 0.08) % 1.0
                fx = tx + int(math.sin(phase + i) * 30)
                fy = ty - 40 + int(fall_t * 50)
                alpha = _NS_molgravar._alpha(200 * (1 - t) * (1 - fall_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_dark"], alpha),
                                     (fx, fy, 3, 3))
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["stone_mid"], alpha),
                                     (fx, fy, 2, 2))
    # ============================================================
    # SKILL R - UNSTOPPABLE FORCE (ultimate dash meteor)
    # ============================================================
    def _draw_unstoppable_ground(surface, boss, x, y, timer, phase):
        """Big impact crater at target."""
        tx, ty = _NS_molgravar._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Wind-up: warning circle at target growing
            t = progress / 0.4
            r = int(50 * t)
            alpha = _NS_molgravar._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            # Post-impact: giant crater
            t = (progress - 0.4) / 0.6
            r = int(60 + t * 25)
            alpha = _NS_molgravar._alpha(240 * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["shadow_deep"], alpha),
                                (tx - r - 2, ty - r // 3 - 1, r * 2 + 4, r * 2 // 3 + 2))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10))
            pygame.draw.ellipse(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                (tx - r + 18, ty - r // 3 + 8,
                                 r * 2 - 36, r * 2 // 3 - 16))
    def _draw_unstoppable_foreground(surface, boss, x, y, timer, phase):
        """Boss transforms into meteor + dash + impact."""
        tx, ty = _NS_molgravar._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.4:
            # Wind-up: boss gathers energy (aura pulses)
            pass  # body still visible; ground shows warning
        elif progress < 0.75:
            # DASH: meteor form of boss trajectory
            t = (progress - 0.4) / 0.35
            # Parabolic arc dash
            start_x, start_y = x, y
            for i in range(10):
                trail_t = max(0, t - i * 0.05)
                ax = int(start_x + (tx - start_x) * trail_t)
                ay = int(start_y + (ty - start_y) * trail_t
                          - math.sin(trail_t * math.pi) * 40)
                alpha = _NS_molgravar._alpha(240 - i * 22)
                size = max(2, 10 - i)
                # Big meteor with fire trail
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                         (ax, ay), size + 2)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["stone_darkest"], alpha),
                                         (ax, ay), size)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["stone_dark"], alpha),
                                         (ax, ay), max(1, size - 1))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["stone_mid"], alpha),
                                         (ax, ay), max(1, size - 2))
                # Fire wrap
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                         (ax, ay), max(1, size - 3))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                         (ax, ay), max(1, size - 4))
                # Flames trailing behind
                for f in range(3):
                    flame_ang = trail_t * 10 + f * 2
                    fx = ax + int(math.sin(flame_ang) * (size + 2))
                    fy = ay + int(math.cos(flame_ang) * (size + 2))
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_shine"], alpha),
                                     (fx, fy, 1, 1))
            # Front meteor (bright head)
            bx = int(start_x + (tx - start_x) * t
                     - 0)  # linear travel
            by = int(start_y + (ty - start_y) * t
                     - math.sin(t * math.pi) * 40)
            for r in range(16, 3, -2):
                alpha = _NS_molgravar._alpha(120 * (16 - r) / 16)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_light"], alpha),
                                         (bx, by), r)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["stone_darkest"], (bx, by), 10)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["stone_dark"], (bx, by), 8)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_dark"], (bx, by), 6)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_mid"], (bx, by), 4)
            _NS_molgravar._aacircle(surface, _NS_molgravar.PALETTE["lava_hot"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_molgravar.PALETTE["white"], (bx, by, 1, 1))
            # IMPACT burst
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(20 + st * 40)
                alpha = _NS_molgravar._alpha(250 * (1 - st))
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_darkest"], alpha),
                                         (tx, ty), radius + 5, 4)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_dark"], alpha),
                                         (tx, ty), radius, 3)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_mid"], alpha),
                                         (tx, ty), max(1, radius - 8), 2)
                _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                         (tx, ty), max(1, radius - 16), 1)
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_shine"], alpha),
                                     (ex, ey, 3, 3))
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["white"], alpha),
                                     (ex, ey, 1, 1))
        else:
            # Aftermath: knock-up airborne indicators + smoke
            t = (progress - 0.75) / 0.25
            # Airborne enemies indicator
            for a_i in range(3):
                ax = tx - 25 + a_i * 20
                ay = ty - 25 - int(math.sin(phase * 3 + a_i) * 4) + int(t * 8)
                alpha = _NS_molgravar._alpha(230 * (1 - t))
                # Up arrow
                pygame.draw.polygon(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                    [(ax, ay), (ax - 4, ay + 5), (ax + 4, ay + 5)])
                pygame.draw.polygon(surface, (*_NS_molgravar.PALETTE["lava_shine"], alpha),
                                    [(ax, ay + 1), (ax - 2, ay + 4), (ax + 2, ay + 4)])
            # Rising smoke + embers
            for i in range(12):
                sm_t = (phase * 0.6 + i * 0.09) % 1.0
                sx = tx + int(math.sin(phase + i) * 25)
                sy = ty - int(sm_t * 40)
                alpha = _NS_molgravar._alpha(200 * (1 - t) * (1 - sm_t))
                if alpha > 0:
                    _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["dust_mid"], alpha),
                                             (sx, sy), 3)
                    _NS_molgravar._aacircle(surface, (*_NS_molgravar.PALETTE["dust_light"], alpha),
                                             (sx, sy), 2)
                    pygame.draw.rect(surface, (*_NS_molgravar.PALETTE["lava_hot"], alpha),
                                     (sx, sy, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_grimstalker(surface, boss, x, y):
    """Entry point grimstalker."""
    return _NS_grimstalker.draw_grimstalker(surface, boss, x, y)


def draw_kryvoxar(surface, boss, x, y):
    """Entry point kryvoxar."""
    return _NS_kryvoxar.draw_kryvoxar(surface, boss, x, y)


def draw_vargroth(surface, boss, x, y):
    """Entry point vargroth."""
    return _NS_vargroth.draw_vargroth(surface, boss, x, y)


def draw_molgravar(surface, boss, x, y):
    """Entry point molgravar."""
    return _NS_molgravar.draw_molgravar(surface, boss, x, y)
