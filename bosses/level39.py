"""
bosses/level39.py - Semua boss Level 39

Berisi:
  - bhorgathul  (mini boss - MELEE earth render)
  - morkhelvis  (mini boss - MELEE necrogargoyle, stone wings)
  - vorthakul   (mini boss - RANGED terror of the abyss)
  - xaelmoran   (TRUE BOSS - RANGED elemental weaver, quas/wex/exort)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _bho_ (bhorgathul) sudah unik.
  - _mor_ (morkhelvis) di-rename -> _mkh_ (bentrok dengan Morgath
    level 1), termasuk atribut _last_x/_last_y.
  - _vor_ (vorthakul) di-rename -> _vth_ (bentrok dengan vorenmarr
    level 7), termasuk atribut _last_x/_last_y.
  - _xae_ (xaelmoran) di-rename -> _xlm_ (bentrok dengan xaerissa
    level 30), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# BHORGATHUL (EARTH RENDER) - Mini Boss
# ====================================================================

class _NS_bhorgathul:
    """Namespace bhorgathul - Primal Beast boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Hide/skin (tan brown)
        "hide_darkest": (30, 18, 12),
        "hide_dark": (70, 45, 28),
        "hide_mid": (135, 90, 55),
        "hide_light": (195, 145, 95),
        "hide_edge": (230, 190, 140),
        "hide_shine": (250, 225, 180),
        # Belly (lighter tan/cream)
        "belly_darkest": (55, 35, 20),
        "belly_dark": (110, 80, 50),
        "belly_mid": (180, 140, 90),
        "belly_light": (230, 200, 145),
        "belly_shine": (255, 235, 190),
        # Rock spikes (grey-blue)
        "rock_darkest": (18, 20, 28),
        "rock_dark": (45, 50, 65),
        "rock_mid": (85, 92, 110),
        "rock_light": (140, 148, 168),
        "rock_edge": (200, 205, 220),
        "rock_shine": (240, 245, 255),
        # Fire/rage orange (mouth, eyes, cracks)
        "fire_darkest": (35, 10, 3),
        "fire_dark": (130, 45, 10),
        "fire_mid": (230, 110, 25),
        "fire_light": (255, 175, 65),
        "fire_hot": (255, 220, 130),
        "fire_shine": (255, 250, 210),
        # Fangs/claws (aged bone)
        "fang_dark": (65, 50, 30),
        "fang_mid": (160, 135, 90),
        "fang_light": (235, 215, 165),
        "fang_shine": (255, 245, 210),
        # Eye (glowing orange-red)
        "eye_socket": (5, 2, 2),
        "eye_dark": (100, 20, 10),
        "eye_mid": (220, 60, 20),
        "eye_light": (255, 140, 60),
        "eye_glow": (255, 220, 160),
        # Dust/dirt clouds
        "dust_dark": (55, 40, 25),
        "dust_mid": (120, 95, 65),
        "dust_light": (180, 155, 115),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 3),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_bhorgathul._clamp(color)
        if _NS_bhorgathul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_bhorgathul._clamp(color)
        if _NS_bhorgathul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_bhorgathul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_bhorgathul(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_bhorgathul._update_bho_attack_anim(boss)
        attacking = bool(getattr(boss, "_bho_attack_active", False))
        moving = _NS_bhorgathul._detect_moving(boss)
        # ===== LAYER 1: BACKGROUND (ambient, aura) =====
        _NS_bhorgathul._draw_rage_aura(surface, x, y, pulse)
        _NS_bhorgathul._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # ===== LAYER 2: SKILL GROUND FX (behind body) =====
        if active_skill == "w":
            _NS_bhorgathul._draw_thunderclap_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_bhorgathul._draw_trample_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_bhorgathul._draw_onslaught_ground(surface, boss, x, y, skill_timer, pulse)
        # ===== LAYER 3: BODY (drawn OVER background effects) =====
        if attacking:
            _NS_bhorgathul._draw_bho_attack(surface, boss, x, y)
        elif moving:
            _NS_bhorgathul._draw_bho_walk(surface, boss, x, y)
        else:
            _NS_bhorgathul._draw_bho_idle(surface, boss, x, y)
        # ===== LAYER 4: FOREGROUND FX (only in front/side, not overlapping body) =====
        # Basic attack
        if attacking and not active_skill:
            _NS_bhorgathul._draw_basic_attack_fx(surface, boss, x, y)
        # Skills (foreground - small/side effects only)
        if active_skill == "q":
            _NS_bhorgathul._draw_uproar_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_bhorgathul._draw_thunderclap_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_bhorgathul._draw_trample_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_bhorgathul._draw_onslaught_fx(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_bho_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_bho_previous_timer", timer))
        active = bool(getattr(boss, "_bho_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._bho_attack_active = True
            boss._bho_attack_frame = 0
            active = True
        if active:
            boss._bho_attack_frame = int(getattr(boss, "_bho_attack_frame", 0)) + 1
            attack_duration = 30
            if boss._bho_attack_frame >= attack_duration:
                boss._bho_attack_active = False
                boss._bho_attack_frame = 0
                active = False
        boss._bho_previous_timer = timer
        if active:
            attack_duration = 30
            boss._bho_attack_progress = min(1.0,
                boss._bho_attack_frame / attack_duration)
        else:
            boss._bho_attack_progress = 0.0
    def _detect_moving(boss):
        if not hasattr(boss, "_bho_last_x"):
            boss._bho_last_x = boss.x
            boss._bho_last_y = boss.y
            return False
        dx = abs(boss.x - boss._bho_last_x)
        dy = abs(boss.y - boss._bho_last_y)
        boss._bho_last_x = boss.x
        boss._bho_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_bho_idle(surface, boss, x, y):
        breath = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_bhorgathul._draw_shadow(surface, x, y + 52)
        _NS_bhorgathul._draw_bho_body(surface, x, y + breath, boss.direction,
                                       boss.pulse, "idle")
    def _draw_bho_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.2) * 3)
        _NS_bhorgathul._draw_shadow(surface, x, y + 52)
        _NS_bhorgathul._draw_dust_cloud(surface, x, y + 48, phase, boss.direction)
        _NS_bhorgathul._draw_bho_body(surface, x, y + bob, boss.direction,
                                       phase, "walk")
    def _draw_bho_attack(surface, boss, x, y):
        """Bite/lunge attack animation."""
        progress = getattr(boss, "_bho_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        # Bite lunge: rear back → lunge forward → recover
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 6) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-6 + t * 22)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(16 * (1 - t)) * facing
            lift = int(-2 + t * 2)
        _NS_bhorgathul._draw_shadow(surface, x + lunge, y + 52)
        _NS_bhorgathul._draw_dust_cloud(surface, x + lunge, y + 48, boss.pulse * 2,
                                        facing, intense=True)
        _NS_bhorgathul._draw_bho_body(surface, x + lunge, y - lift, facing,
                                       boss.pulse, "attack", progress)
    # ============================================================
    # BODY (Quadruped beast with big jaw)
    # ============================================================
    def _draw_bho_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Full beast body: legs, tail, torso, big head with jaw."""
        # Back rock spikes (behind body)
        _NS_bhorgathul._draw_back_spikes(surface, cx, cy - 10, facing, phase)
        # Tail
        _NS_bhorgathul._draw_beast_tail(surface, cx, cy + 6, facing, phase, action)
        # Rear legs
        _NS_bhorgathul._draw_beast_legs(surface, cx - facing * 12, cy + 10,
                                         facing, phase, action, is_rear=True)
        # Main body torso
        _NS_bhorgathul._draw_beast_torso(surface, cx, cy, facing, phase)
        # Front legs
        _NS_bhorgathul._draw_beast_legs(surface, cx + facing * 10, cy + 10,
                                         facing, phase, action, is_rear=False)
        # Head with big jaw
        head_lunge = 0
        head_lift = 0
        if action == "attack":
            if attack_progress < 0.3:
                head_lunge = -int(attack_progress / 0.3 * 5) * facing
                head_lift = -int(attack_progress / 0.3 * 3)
            elif attack_progress < 0.6:
                t = (attack_progress - 0.3) / 0.3
                head_lunge = int((-5 + t * 20)) * facing
                head_lift = int(-3 + t * 5)
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(15 * (1 - t)) * facing
                head_lift = int(2 - t * 2)
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 10)
        elif action == "walk":
            mouth_open = 2
        _NS_bhorgathul._draw_beast_head(surface, cx + facing * 20 + head_lunge,
                                         cy - 8 + head_lift, facing, phase,
                                         mouth_open, action)
    def _draw_back_spikes(surface, cx, cy, facing, phase):
        """Large rock crystal spikes on back."""
        spike_configs = [
            (-16, 4, 6),
            (-11, 1, 10),
            (-5, -2, 13),
            (1, -4, 15),   # tallest
            (7, -3, 13),
            (13, 0, 10),
            (18, 3, 7),
        ]
        for i, (x_off, y_off, h) in enumerate(spike_configs):
            sway = math.sin(phase * 0.3 + i * 0.4) * 1
            spike_x = cx + x_off
            base_y = cy + y_off
            tip_y = base_y - h + int(sway)
            # Wide base (rock chunk look)
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["shadow_deep"], [
                (spike_x + 2, tip_y + 2),
                (spike_x - 4, base_y + 2),
                (spike_x + 4, base_y + 2),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_darkest"], [
                (spike_x, tip_y),
                (spike_x - 4, base_y),
                (spike_x + 4, base_y),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_dark"], [
                (spike_x, tip_y),
                (spike_x - 3, base_y),
                (spike_x + 3, base_y),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_mid"], [
                (spike_x, tip_y),
                (spike_x - 2, base_y),
                (spike_x + 2, base_y),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_light"], [
                (spike_x, tip_y),
                (spike_x - 1, int((tip_y + base_y) / 2)),
                (spike_x, base_y),
            ])
            # Edge highlight
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["rock_edge"],
                             (spike_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["rock_shine"],
                             (spike_x, tip_y, 1, 1))
    def _draw_beast_tail(surface, cx, cy, facing, phase, action):
        """Short thick tail."""
        back_dir = -facing
        base_x = cx + back_dir * 15
        base_y = cy + 2
        # Tail wave
        tail_wave = math.sin(phase * 1.2) * 3
        if action == "walk":
            tail_wave = math.sin(phase * 1.5) * 5
        elif action == "attack":
            tail_wave = math.sin(phase * 2) * 6
        segments = 5
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (10 + t * 16))
            y_off = int(2 + t * 6 - t * t * 4)
            wave = math.sin(phase * 1.2 + t * math.pi) * (3 + t * 2)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))
        for i in range(len(points) - 1):
            thickness = max(3, 11 - i * 2)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                                    (points[i][0] + 2, points[i][1] + 2),
                                    (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                    thickness + 1)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_darkest"],
                                    points[i], points[i + 1], thickness)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_dark"],
                                    points[i], points[i + 1],
                                    max(1, thickness - 2))
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_mid"],
                                    (points[i][0], points[i][1] - 1),
                                    (points[i + 1][0], points[i + 1][1] - 1),
                                    max(1, thickness - 4))
        # Tail spikes at end
        if len(points) >= 2:
            end = points[-1]
            for r in range(3, 0, -1):
                _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_dark"], [
                    (end[0], end[1] - 4),
                    (end[0] - 2, end[1]),
                    (end[0] + 2, end[1]),
                ])
                _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_mid"], [
                    (end[0], end[1] - 3),
                    (end[0] - 1, end[1]),
                    (end[0] + 1, end[1]),
                ])
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["rock_shine"],
                                 (end[0], end[1] - 3, 1, 1))
                break
    def _draw_beast_legs(surface, cx, cy, facing, phase, action, is_rear=True):
        """Thick beast legs with big claws."""
        # Two legs (near and far)
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
            # Thick leg
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                                    (leg_top_x + 2, leg_top_y + 2),
                                    (leg_bot_x + 2, leg_bot_y + 2), 8)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_darkest"],
                                    (leg_top_x, leg_top_y),
                                    (leg_bot_x, leg_bot_y), 7)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_dark"],
                                    (leg_top_x, leg_top_y),
                                    (leg_bot_x, leg_bot_y), 5)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_mid"],
                                    (leg_top_x - 1, leg_top_y),
                                    (leg_bot_x - 1, leg_bot_y), 3)
            _NS_bhorgathul._aaline(surface, _NS_bhorgathul.PALETTE["hide_light"],
                                    (leg_top_x - 2, leg_top_y),
                                    (leg_bot_x - 2, leg_bot_y), 1)
            # Foot/paw with claws
            paw_x = leg_bot_x
            paw_y = leg_bot_y
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["shadow_deep"], [
                (paw_x - 5, paw_y + 1),
                (paw_x + 6, paw_y + 1),
                (paw_x + 5, paw_y + 5),
                (paw_x - 5, paw_y + 5),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_darkest"], [
                (paw_x - 5, paw_y),
                (paw_x + 6, paw_y),
                (paw_x + 5, paw_y + 4),
                (paw_x - 5, paw_y + 4),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_dark"], [
                (paw_x - 4, paw_y + 1),
                (paw_x + 5, paw_y + 1),
                (paw_x + 4, paw_y + 3),
                (paw_x - 4, paw_y + 3),
            ])
            # Claws (3 per foot, curved forward)
            for cx_off in (-3, 0, 3):
                claw_x = paw_x + cx_off + facing
                claw_y = paw_y + 3
                _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["fang_dark"], [
                    (claw_x, claw_y),
                    (claw_x + facing, claw_y + 4),
                    (claw_x + facing * 2, claw_y + 1),
                ])
                _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["fang_mid"], [
                    (claw_x, claw_y),
                    (claw_x + facing, claw_y + 3),
                    (claw_x + facing * 2, claw_y + 1),
                ])
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fang_light"],
                                 (claw_x + facing, claw_y + 3, 1, 1))
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fang_shine"],
                                 (claw_x + facing * 2, claw_y + 1, 1, 1))
    def _draw_beast_torso(surface, cx, cy, facing, phase):
        """Main body torso - bulky quadruped."""
        body_shape = [
            (cx - 18, cy + 2),
            (cx - 20, cy - 4),
            (cx - 16, cy - 10),
            (cx - 8, cy - 12),
            (cx + 6, cy - 12),
            (cx + 16, cy - 10),
            (cx + 20, cy - 4),
            (cx + 22, cy + 2),
            (cx + 20, cy + 8),
            (cx + 14, cy + 12),
            (cx + 4, cy + 13),
            (cx - 6, cy + 13),
            (cx - 14, cy + 12),
            (cx - 20, cy + 8),
        ]
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                              [(px + 2, py + 3) for px, py in body_shape])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_darkest"], body_shape)
        # Upper hide
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_dark"], [
            (cx - 18, cy),
            (cx - 15, cy - 9),
            (cx - 6, cy - 11),
            (cx + 6, cy - 11),
            (cx + 15, cy - 9),
            (cx + 19, cy - 4),
            (cx + 20, cy),
            (cx + 15, cy + 3),
            (cx - 15, cy + 3),
            (cx - 18, cy),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_mid"], [
            (cx - 14, cy - 3),
            (cx - 12, cy - 8),
            (cx - 4, cy - 9),
            (cx + 6, cy - 9),
            (cx + 12, cy - 8),
            (cx + 15, cy - 3),
            (cx + 13, cy),
            (cx - 10, cy),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_light"], [
            (cx - 6, cy - 6),
            (cx + 2, cy - 7),
            (cx + 8, cy - 5),
            (cx + 6, cy - 3),
            (cx - 4, cy - 3),
        ])
        # Belly (tan)
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["belly_dark"], [
            (cx - 15, cy + 3),
            (cx + 15, cy + 3),
            (cx + 20, cy + 6),
            (cx + 14, cy + 12),
            (cx + 4, cy + 13),
            (cx - 6, cy + 13),
            (cx - 14, cy + 12),
            (cx - 20, cy + 6),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["belly_mid"], [
            (cx - 13, cy + 5),
            (cx + 13, cy + 5),
            (cx + 16, cy + 7),
            (cx + 10, cy + 12),
            (cx - 6, cy + 12),
            (cx - 12, cy + 11),
            (cx - 15, cy + 7),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["belly_light"], [
            (cx - 10, cy + 7),
            (cx + 10, cy + 7),
            (cx + 13, cy + 9),
            (cx + 6, cy + 11),
            (cx - 6, cy + 11),
            (cx - 12, cy + 9),
        ])
        # Belly stripes
        for i, y_off in enumerate((5, 8, 11)):
            pygame.draw.line(surface, _NS_bhorgathul.PALETTE["belly_darkest"],
                             (cx - 10 + i, cy + y_off),
                             (cx + 10 - i, cy + y_off), 1)
        # Hide texture (scales/rough patches)
        for row in range(2):
            y_row = cy - 5 + row * 4
            for dx in (-11, -6, -1, 4, 9):
                offset_x = (row % 2) * 2 - 1
                pygame.draw.line(surface, _NS_bhorgathul.PALETTE["hide_darkest"],
                                 (cx + dx + offset_x - 1, y_row),
                                 (cx + dx + offset_x, y_row - 1), 1)
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["hide_edge"],
                                 (cx + dx + offset_x, y_row - 1, 1, 1))
        # Rage cracks (orange glow through hide)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for crack in [
            [(cx - 12, cy - 2), (cx - 8, cy + 1), (cx - 5, cy + 4)],
            [(cx + 8, cy - 4), (cx + 12, cy - 1), (cx + 14, cy + 3)],
            [(cx - 3, cy + 8), (cx + 2, cy + 10)],
        ]:
            for i in range(len(crack) - 1):
                pygame.draw.line(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_dark"],
                                  _NS_bhorgathul._alpha(220 * pulse)),
                                 crack[i], crack[i + 1], 1)
                pygame.draw.line(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_mid"],
                                  _NS_bhorgathul._alpha(180 * pulse)),
                                 crack[i], crack[i + 1], 1)
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_hot"],
                                  _NS_bhorgathul._alpha(240 * pulse)),
                                 (crack[i][0], crack[i][1], 1, 1))
    def _draw_beast_head(surface, cx, cy, facing, phase, mouth_open, action):
        """Big beast head with giant jaw."""
        # Head shape (elongated snout)
        head_shape = [
            (cx - 10 * facing, cy + 4),
            (cx - 12 * facing, cy - 2),
            (cx - 8 * facing, cy - 10),
            (cx - 2 * facing, cy - 12),
            (cx + 6 * facing, cy - 11),
            (cx + 14 * facing, cy - 8),
            (cx + 20 * facing, cy - 3),
            (cx + 22 * facing, cy + 2),
            (cx + 18 * facing, cy + 6),
            (cx + 10 * facing, cy + 8),
            (cx + 2 * facing, cy + 9),
            (cx - 6 * facing, cy + 8),
        ]
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in head_shape])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_darkest"],
                              head_shape)
        # Upper head
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_dark"], [
            (cx - 10 * facing, cy + 3),
            (cx - 10 * facing, cy - 1),
            (cx - 6 * facing, cy - 9),
            (cx + 5 * facing, cy - 10),
            (cx + 13 * facing, cy - 7),
            (cx + 19 * facing, cy - 2),
            (cx + 20 * facing, cy + 1),
            (cx + 15 * facing, cy + 1),
            (cx + 5 * facing, cy),
            (cx - 5 * facing, cy + 1),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_mid"], [
            (cx - 7 * facing, cy - 1),
            (cx - 4 * facing, cy - 8),
            (cx + 5 * facing, cy - 9),
            (cx + 12 * facing, cy - 5),
            (cx + 16 * facing, cy - 1),
            (cx + 5 * facing, cy - 2),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["hide_light"], [
            (cx - 2 * facing, cy - 5),
            (cx + 4 * facing, cy - 7),
            (cx + 10 * facing, cy - 4),
            (cx + 5 * facing, cy - 2),
        ])
        # Small rock spikes on head
        for i, (off_x, off_y, h) in enumerate([
            (-6, -8, 5), (-2, -11, 6), (3, -10, 5),
        ]):
            spike_x = cx + int(off_x * facing)
            base_y = cy + off_y
            tip_y = base_y - h
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_darkest"], [
                (spike_x, tip_y),
                (spike_x - 2, base_y),
                (spike_x + 2, base_y),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_dark"], [
                (spike_x, tip_y),
                (spike_x - 1, base_y),
                (spike_x + 1, base_y),
            ])
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["rock_edge"],
                             (spike_x, tip_y, 1, 1))
        # Snout tan
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["belly_dark"], [
            (cx + 14 * facing, cy - 2),
            (cx + 20 * facing, cy),
            (cx + 21 * facing, cy + 3),
            (cx + 18 * facing, cy + 5),
            (cx + 14 * facing, cy + 4),
        ])
        _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["belly_mid"], [
            (cx + 16 * facing, cy - 1),
            (cx + 19 * facing, cy + 1),
            (cx + 17 * facing, cy + 4),
            (cx + 15 * facing, cy + 3),
        ])
        # Nostril
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                         (cx + 18 * facing, cy - 1, 2, 1))
        # Big glowing eye
        _NS_bhorgathul._draw_beast_eye(surface, cx + 3 * facing, cy - 4, facing,
                                        phase)
        # Big mouth with fangs
        _NS_bhorgathul._draw_beast_mouth(surface, cx, cy, facing, phase, mouth_open,
                                          action)
    def _draw_beast_eye(surface, cx, cy, facing, phase):
        """Orange-red glowing eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        ex = cx + 2 * facing
        ey = cy
        # Deep socket
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))
        # Glow halo
        for radius in range(6, 0, -1):
            alpha = _NS_bhorgathul._alpha(100 * (6 - radius) / 6 * pulse)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["eye_mid"], alpha),
                                     (ex + 1, ey), radius)
        # Iris
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["eye_dark"], (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["eye_mid"], (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["eye_light"], (ex + 1, ey, 2, 1))
        pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["eye_glow"], (ex + 2, ey, 1, 1))
        # Vertical pupil
        pygame.draw.line(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                         (ex + 1, ey - 1), (ex + 1, ey + 1), 1)
    def _draw_beast_mouth(surface, cx, cy, facing, phase, mouth_open, action):
        """Giant jaw with big fangs."""
        mouth_y = cy + 3
        mouth_x_start = cx + 3 * facing
        mouth_x_end = cx + 20 * facing
        if mouth_open > 0:
            # Open mouth cavity
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end - 2, mouth_y + int(mouth_open)),
                (mouth_x_start + 2, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["fire_darkest"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing * 2, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing * 2, mouth_y + int(mouth_open * 0.7) - 1),
            ])
            # Orange rage glow inside
            glow_cx = cx + 11 * facing
            glow_cy = mouth_y + int(mouth_open * 0.5)
            glow_r = int(3 + mouth_open * 0.4)
            for r in range(glow_r + 3, 0, -1):
                alpha = _NS_bhorgathul._alpha(180 * (glow_r + 3 - r) / (glow_r + 3))
                _NS_bhorgathul._aacircle(surface,
                                         (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                         (glow_cx, glow_cy), r)
            _NS_bhorgathul._aacircle(surface, _NS_bhorgathul.PALETTE["fire_mid"],
                                     (glow_cx, glow_cy), max(1, glow_r - 1))
            _NS_bhorgathul._aacircle(surface, _NS_bhorgathul.PALETTE["fire_light"],
                                     (glow_cx, glow_cy), max(1, glow_r - 3))
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_shine"],
                             (glow_cx, glow_cy, 1, 1))
            # Upper fangs (big)
            for i, x_off in enumerate((5, 9, 13, 17)):
                fang_x = cx + int(x_off * facing)
                fang_size = 4 if i in (1, 2) else 3
                fang_tip_y = mouth_y + int(mouth_open * 0.75) + fang_size
                pygame.draw.line(surface, _NS_bhorgathul.PALETTE["fang_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 3)
                pygame.draw.line(surface, _NS_bhorgathul.PALETTE["fang_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_bhorgathul.PALETTE["fang_light"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fang_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Lower fangs
            for i, x_off in enumerate((7, 11, 15)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 4
                pygame.draw.line(surface, _NS_bhorgathul.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_bhorgathul.PALETTE["fang_light"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fang_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Drool
            if mouth_open > 5:
                for x_off in (6, 12):
                    drip_x = cx + int(x_off * facing)
                    drip_y = mouth_y + int(mouth_open) + 2
                    pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_dark"],
                                     (drip_x, drip_y, 1, 2))
                    pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_light"],
                                     (drip_x, drip_y, 1, 1))
        else:
            # Closed mouth with fangs
            pygame.draw.line(surface, _NS_bhorgathul.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            for x_off in (7, 11, 15):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fang_mid"],
                                 (fang_x, mouth_y + 1, 1, 3))
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fang_light"],
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
        pygame.draw.ellipse(shadow, (5, 3, 2, 180), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_dust_cloud(surface, cx, cy, phase, facing, intense=False):
        """Dust rising from feet during walk/attack."""
        strength = 1.5 if intense else 1.0
        # Dust puffs
        for i, offset in enumerate((-20, -12, -4, 4, 12, 20)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset - facing * int(t * 8)
            sy = cy - int(t * 12)
            alpha = _NS_bhorgathul._alpha(180 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_dark"], alpha),
                                     (sx, sy), 3)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_bhorgathul.PALETTE["dust_light"], alpha),
                             (sx, sy - 1, 1, 1))
    def _draw_rage_aura(surface, x, y, phase):
        """Orange rage aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_bhorgathul._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_bhorgathul._aacircle(aura,
                                         (*_NS_bhorgathul.PALETTE["fire_darkest"], alpha),
                                         (110, 90), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_bhorgathul._alpha((50 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_bhorgathul._aacircle(aura,
                                         (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                         (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Rage embers floating
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.4)
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with rock/rune texture."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_bhorgathul.PALETTE["fire_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_bhorgathul.PALETTE["hide_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_bhorgathul.PALETTE["fire_dark"], 220),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_bhorgathul.PALETTE["fire_mid"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_bhorgathul.PALETTE["fire_hot"],
                                        _NS_bhorgathul._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - Bite/Claw Impact (MELEE)
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic melee attack FX: claw slash + bite impact at close range."""
        progress = getattr(boss, "_bho_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        # Target position (nearby for melee)
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y
        # Limit range to melee range
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist > 80:
            tx = x + int(dx / dist * 60)
            ty = y + int(dy / dist * 60)
        # PHASE 1: Wind-up (0-30%)
        if progress < 0.3:
            t = progress / 0.3
            # Small glow at mouth building up
            mouth_x = x + facing * 22
            mouth_y = y - 6
            for r in range(int(4 + t * 4), 0, -1):
                alpha = _NS_bhorgathul._alpha(150 * t * r / 6)
                _NS_bhorgathul._aacircle(surface,
                                         (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                         (mouth_x, mouth_y), r)
        # PHASE 2: SLASH & BITE IMPACT (30-70%)
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            # Claw slash arc in front of boss
            slash_cx = x + facing * 30
            slash_cy = y - 2
            arc_radius = 28
            start_angle = math.radians(-60) if facing == 1 else math.radians(-120)
            end_angle = math.radians(60) if facing == 1 else math.radians(240)
            current_angle = start_angle + (end_angle - start_angle) * t
            # 3 parallel claw slashes
            for line_i, offset in enumerate((-6, 0, 6)):
                num_pts = 10
                prev_pt = None
                for step in range(num_pts + 1):
                    step_t = step / num_pts
                    a = start_angle + (current_angle - start_angle) * step_t
                    r = arc_radius + offset
                    px = slash_cx + int(math.cos(a) * r) * facing
                    py = slash_cy + int(math.sin(a) * r)
                    if prev_pt is not None:
                        alpha = _NS_bhorgathul._alpha(220 * step_t
                                                      * (1 - t * 0.3))
                        pygame.draw.line(surface,
                                         (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                         prev_pt, (px, py), 4)
                        pygame.draw.line(surface,
                                         (*_NS_bhorgathul.PALETTE["fire_mid"], alpha),
                                         prev_pt, (px, py), 3)
                        pygame.draw.line(surface,
                                         (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                                         prev_pt, (px, py), 2)
                        pygame.draw.line(surface,
                                         (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                         prev_pt, (px, py), 1)
                    prev_pt = (px, py)
                # Bright tip
                tip_a = current_angle
                tip_r = arc_radius + offset
                tip_x = slash_cx + int(math.cos(tip_a) * tip_r) * facing
                tip_y = slash_cy + int(math.sin(tip_a) * tip_r)
                for r in range(4, 0, -1):
                    alpha = _NS_bhorgathul._alpha(220 * (4 - r) / 4)
                    _NS_bhorgathul._aacircle(surface,
                                             (*_NS_bhorgathul.PALETTE["fire_hot"],
                                              alpha),
                                             (tip_x, tip_y), r)
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_shine"],
                                 (tip_x, tip_y, 1, 1))
            # Sparks
            for i in range(8):
                spark_angle = start_angle + (current_angle - start_angle) \
                              * (0.3 + (i % 5) * 0.15)
                spark_r = arc_radius + math.sin(boss.pulse * 3 + i) * 8
                sx = slash_cx + int(math.cos(spark_angle) * spark_r) * facing
                sy = slash_cy + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_hot"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_shine"],
                                 (sx, sy, 1, 1))
        # PHASE 3: IMPACT at target (70-100%)
        else:
            t = (progress - 0.7) / 0.3
            impact_r = int(8 + t * 22)
            alpha = _NS_bhorgathul._alpha(240 * (1 - t))
            # Impact rings
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                     (tx, ty), impact_r + 2, 3)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_mid"], alpha),
                                     (tx, ty), impact_r, 2)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                                     (tx, ty), max(1, impact_r - 5), 1)
            # Bright core
            core_r = max(1, int(5 * (1 - t)))
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_hot"], alpha),
                                     (tx, ty), core_r + 2)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                     (tx, ty), max(1, core_r))
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["white"],
                             (tx, ty, 1, 1))
            # 3 claw scratch marks at target
            scratch_len = int(14 * (1 - t * 0.3))
            for i, y_off in enumerate((-7, 0, 7)):
                start_sx = tx - scratch_len // 2 * facing
                end_sx = tx + scratch_len // 2 * facing
                sy_pos = ty + y_off + int(math.sin(i) * 2)
                pygame.draw.line(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                 (start_sx, sy_pos - 1),
                                 (end_sx, sy_pos - 1), 2)
                pygame.draw.line(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                                 (start_sx, sy_pos),
                                 (end_sx, sy_pos), 1)
                pygame.draw.line(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                 (start_sx + 2, sy_pos),
                                 (end_sx - 2, sy_pos), 1)
            # Radial burst particles
            for i in range(10):
                angle_p = i * math.pi / 5
                pr = int(impact_r * (0.6 + (i % 3) * 0.2))
                px = tx + int(math.cos(angle_p) * pr)
                py = ty + int(math.sin(angle_p) * pr * 0.8)
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_hot"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                 (px, py, 1, 1))
            # Small rock chunks flying
            for i in range(6):
                angle_r = i * math.pi / 3
                rock_dist = int(t * 25)
                rx = tx + int(math.cos(angle_r) * rock_dist)
                ry = ty + int(math.sin(angle_r) * rock_dist * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["rock_dark"], alpha),
                                 (rx, ry, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["rock_mid"], alpha),
                                 (rx, ry, 2, 2))
    # ============================================================
    # SKILL: Q - UPROAR (Roar wave in front)
    # ============================================================
    def _draw_uproar_fx(surface, boss, x, y, timer, phase):
        """Roar sonic wave from mouth in front of boss."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        mouth_x = x + facing * 25
        mouth_y = y - 6
        # Multi-arc waves expanding
        for wave_i in range(4):
            wave_t = max(0.0, progress - wave_i * 0.12)
            if wave_t <= 0:
                continue
            wave_dist = int(wave_t * 100)
            wave_r = int(15 + wave_t * 30)
            wave_x = mouth_x + facing * wave_dist
            wave_y = mouth_y
            alpha = _NS_bhorgathul._alpha(230 * (1 - wave_t))
            for arc_r in range(wave_r, wave_r - 4, -1):
                if arc_r < 2:
                    continue
                for a_step in range(-35, 36, 3):
                    angle = math.radians(a_step)
                    ax = wave_x + int(math.cos(angle) * arc_r) * facing
                    ay = wave_y + int(math.sin(angle) * arc_r)
                    color_key = ["fire_dark", "fire_mid", "fire_light",
                                 "fire_hot"][min(3, wave_r - arc_r)]
                    pygame.draw.rect(surface,
                                     (*_NS_bhorgathul.PALETTE[color_key], alpha),
                                     (ax, ay, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                     (ax, ay, 1, 1))
        # Ground crack lines emanating from mouth
        for i, y_off in enumerate((-15, 0, 15)):
            crack_end_x = mouth_x + facing * int(progress * 90)
            crack_end_y = mouth_y + y_off + 30
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_dark"], 180),
                             (mouth_x, mouth_y + 30), (crack_end_x, crack_end_y), 3)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_light"], 220),
                             (mouth_x, mouth_y + 30), (crack_end_x, crack_end_y), 1)
    # ============================================================
    # SKILL: W - THUNDER CLAP (Ground slam AoE)
    # ============================================================
    def _draw_thunderclap_ground(surface, boss, x, y, timer, phase):
        """Ground shockwave circle."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple expanding rings
        for i in range(3):
            ring_t = max(0.0, progress - i * 0.15)
            r = int(ring_t * 80)
            if r > 5:
                alpha = _NS_bhorgathul._alpha(220 * (1 - ring_t))
                pygame.draw.ellipse(surface,
                                    (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_bhorgathul.PALETTE["fire_mid"], alpha),
                                    (x - r + 3, y + 40 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                                    (x - r + 6, y + 40 - r // 3 + 4,
                                     r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_thunderclap_fx(surface, boss, x, y, timer, phase):
        """Rock chunks bursting up around boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground shatter - rock chunks bursting
        chunk_positions = [
            (0, 40), (-25, 42), (25, 42), (-45, 38), (45, 38),
            (-15, 45), (15, 45), (-35, 45), (35, 45),
            (-55, 40), (55, 40),
        ]
        for i, (dx, dy) in enumerate(chunk_positions):
            delay = i * 0.03
            local_t = max(0.0, min(1.0, (progress - delay) / (1 - delay)))
            if local_t <= 0:
                continue
            # Rock chunks rise then fall
            if local_t < 0.4:
                height = int((local_t / 0.4) * 20)
            else:
                height = int(20 * (1 - (local_t - 0.4) / 0.6))
            cx_r = x + dx
            cy_r = y + dy - height
            # Rock chunk
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["shadow_deep"], [
                (cx_r - 3, cy_r + 3),
                (cx_r + 4, cy_r + 3),
                (cx_r + 4, cy_r - 2),
                (cx_r - 3, cy_r - 2),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_darkest"], [
                (cx_r - 3, cy_r + 2),
                (cx_r + 4, cy_r + 2),
                (cx_r + 4, cy_r - 3),
                (cx_r - 3, cy_r - 3),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_dark"], [
                (cx_r - 2, cy_r + 1),
                (cx_r + 3, cy_r + 1),
                (cx_r + 3, cy_r - 2),
                (cx_r - 2, cy_r - 2),
            ])
            _NS_bhorgathul._poly(surface, _NS_bhorgathul.PALETTE["rock_mid"], [
                (cx_r - 1, cy_r),
                (cx_r + 2, cy_r),
                (cx_r + 2, cy_r - 1),
                (cx_r - 1, cy_r - 1),
            ])
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["rock_edge"],
                             (cx_r, cy_r - 1, 1, 1))
            # Fire glow from beneath
            if local_t < 0.5:
                alpha = _NS_bhorgathul._alpha(200 * (1 - local_t * 2))
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_hot"], alpha),
                                 (cx_r, y + dy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                 (cx_r, y + dy, 1, 1))
        # Central impact flash
        if progress < 0.3:
            t = progress / 0.3
            flash_r = int(15 + t * 15)
            alpha = _NS_bhorgathul._alpha(240 * (1 - t))
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_hot"], alpha),
                                     (x, y + 42), flash_r)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                     (x, y + 42), max(1, flash_r - 8))
    # ============================================================
    # SKILL: E - TRAMPLE (Charge with rocks)
    # ============================================================
    def _draw_trample_ground(surface, boss, x, y, timer, phase):
        """Trail of trampled ground behind boss."""
        facing = boss.direction
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Trail behind
        trail_length = int(progress * 100)
        for i in range(6):
            tx = x - facing * (i * 12) - facing * int(progress * 20)
            ty = y + 45
            alpha = _NS_bhorgathul._alpha(180 * (1 - i / 6))
            pygame.draw.ellipse(surface,
                                (*_NS_bhorgathul.PALETTE["dust_dark"], alpha),
                                (tx - 12, ty - 3, 24, 6))
            pygame.draw.ellipse(surface,
                                (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                (tx - 8, ty - 2, 16, 4))
    def _draw_trample_fx(surface, boss, x, y, timer, phase):
        """Dust trail and small rocks flying behind."""
        facing = boss.direction
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Dust cloud rising behind boss
        for i in range(12):
            t = (phase * 0.6 + i * 0.1) % 1.0
            offset = -facing * (10 + i * 6)
            sx = x + offset + int(math.sin(phase + i) * 4)
            sy = y + 40 - int(t * 30)
            alpha = _NS_bhorgathul._alpha(200 * (1 - t))
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_dark"], alpha),
                                     (sx, sy), 4)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_mid"], alpha),
                                     (sx, sy - 1), 3)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_light"], alpha),
                                     (sx, sy - 2), 2)
        # Rock chunks flying
        for i in range(8):
            rt = (phase * 0.8 + i * 0.12) % 1.0
            rock_x = x - facing * (5 + i * 8) + int(math.sin(phase * 2 + i) * 5)
            rock_y = y + 42 - int(rt * 20)
            alpha = _NS_bhorgathul._alpha(240 * (1 - rt))
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_dark"], alpha),
                             (rock_x, rock_y, 3, 3))
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_mid"], alpha),
                             (rock_x, rock_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_edge"], alpha),
                             (rock_x, rock_y, 1, 1))
        # Speed lines in front
        for i in range(6):
            line_y = y - 10 + i * 8
            line_start = x + facing * 25
            line_end = x + facing * (40 + int(progress * 20))
            alpha = _NS_bhorgathul._alpha(200)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                             (line_start, line_y), (line_end, line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                             (line_start, line_y), (line_end, line_y), 1)
    # ============================================================
    # SKILL: R - ONSLAUGHT (Ultimate charge)
    # ============================================================
    def _draw_onslaught_ground(surface, boss, x, y, timer, phase):
        """Ground scar + dust cloud BEHIND boss (rendered before body)."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Long ground scar trail behind
        for i in range(10):
            tx = x - facing * (i * 15)
            ty = y + 46
            alpha = _NS_bhorgathul._alpha(220 * (1 - i / 10))
            pygame.draw.ellipse(surface,
                                (*_NS_bhorgathul.PALETTE["fire_darkest"], alpha),
                                (tx - 16, ty - 4, 32, 8))
            pygame.draw.ellipse(surface,
                                (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                                (tx - 12, ty - 3, 24, 6))
            pygame.draw.ellipse(surface,
                                (*_NS_bhorgathul.PALETTE["fire_mid"], alpha),
                                (tx - 8, ty - 2, 16, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                                (tx - 4, ty - 1, 8, 2))
        # Dust cloud rising BEHIND boss only (no coverage on body)
        for i in range(20):
            t = (phase * 0.6 + i * 0.08) % 1.0
            # OFFSET: pastikan hanya di belakang (jauh dari body)
            offset = -facing * (35 + i * 5)  # >>> mulai jauh di belakang
            sx = x + offset + int(math.sin(phase + i) * 6)
            sy = y + 40 - int(t * 40)
            alpha = _NS_bhorgathul._alpha(230 * (1 - t))
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_dark"], alpha),
                                     (sx, sy), 5)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_mid"], alpha),
                                     (sx, sy - 1), 4)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["dust_light"], alpha),
                                     (sx, sy - 2), 3)
            if i % 2 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))
    def _draw_onslaught_fx(surface, boss, x, y, timer, phase):
        """Speed lines + rocks + subtle aura (foreground - NOT covering body)."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big rock chunks flying (di belakang, jauh dari body)
        for i in range(12):
            rt = (phase * 0.8 + i * 0.09) % 1.0
            # Rocks mulai jauh di belakang boss
            rock_x = x - facing * (30 + i * 10) + int(math.sin(phase * 2 + i) * 8)
            rock_y = y + 42 - int(rt * 35)
            alpha = _NS_bhorgathul._alpha(240 * (1 - rt))
            size = 4 if i % 3 == 0 else 3
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_darkest"], alpha),
                             (rock_x, rock_y, size + 1, size + 1))
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_dark"], alpha),
                             (rock_x, rock_y, size, size))
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_mid"], alpha),
                             (rock_x, rock_y, size - 1, size - 1))
            pygame.draw.rect(surface,
                             (*_NS_bhorgathul.PALETTE["rock_edge"], alpha),
                             (rock_x, rock_y, 1, 1))
        # Speed lines HANYA di depan boss (bukan menutupi body)
        for i in range(10):
            line_y = y - 15 + i * 6
            # Mulai dari DEPAN body, bukan overlap
            line_start_x = x + facing * 32
            line_len = 25 + int(math.sin(phase * 3 + i) * 10)
            line_end_x = x + facing * (32 + line_len)
            alpha = _NS_bhorgathul._alpha(230)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_dark"], alpha),
                             (line_start_x, line_y), (line_end_x, line_y), 3)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_mid"], alpha),
                             (line_start_x, line_y), (line_end_x, line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                             (line_start_x, line_y), (line_end_x, line_y), 1)
            pygame.draw.line(surface,
                             (*_NS_bhorgathul.PALETTE["fire_shine"], alpha),
                             (line_start_x + 5, line_y), (line_end_x - 3, line_y), 1)
        # Rage aura TIPIS di sekitar boss (ring only, tidak solid)
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        for r in range(38, 32, -1):  # >>> hanya ring luar tipis
            alpha = _NS_bhorgathul._alpha(140 * pulse * (38 - r) / 6)
            _NS_bhorgathul._aacircle(surface,
                                     (*_NS_bhorgathul.PALETTE["fire_light"], alpha),
                                     (x, y), r, 1)
        # Fire wisps di samping (small dots, tidak overlap body)
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            wisp_r = 40 + int(math.sin(phase * 2 + i) * 5)
            wx = x + int(math.cos(angle) * wisp_r)
            wy = y + int(math.sin(angle) * wisp_r * 0.5)
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_hot"],
                             (wx, wy, 2, 2))
            pygame.draw.rect(surface, _NS_bhorgathul.PALETTE["fire_shine"],
                             (wx, wy, 1, 1))



# ====================================================================
# MORKHELVIS (NECROGARGOYLE) - Mini Boss
# ====================================================================

class _NS_morkhelvis:
    """Namespace morkhelvis - Necrogargoyle boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Stone body (dark grey with slight green tint)
        "stone_darkest": (10, 15, 18),
        "stone_dark": (30, 40, 45),
        "stone_mid": (60, 75, 80),
        "stone_light": (100, 115, 120),
        "stone_edge": (150, 165, 170),
        "stone_shine": (200, 215, 220),
        # Ancient/moss brown accents
        "moss_dark": (25, 30, 15),
        "moss_mid": (60, 70, 30),
        "moss_light": (110, 120, 55),
        # Soul cyan (main glow color)
        "soul_darkest": (5, 20, 30),
        "soul_dark": (15, 60, 90),
        "soul_mid": (40, 140, 200),
        "soul_light": (100, 210, 255),
        "soul_hot": (170, 240, 255),
        "soul_shine": (230, 250, 255),
        # Bone/skull (aged bone with cyan tint)
        "bone_dark": (55, 65, 60),
        "bone_mid": (140, 155, 145),
        "bone_light": (215, 225, 215),
        "bone_shine": (245, 255, 250),
        # Eye (deep cyan)
        "eye_socket": (2, 5, 10),
        "eye_dark": (10, 40, 70),
        "eye_mid": (30, 130, 200),
        "eye_light": (120, 220, 255),
        "eye_glow": (200, 245, 255),
        # Wing membrane (dark stone with cyan glow through)
        "membrane_dark": (18, 28, 35),
        "membrane_mid": (35, 55, 70),
        "membrane_glow": (80, 170, 220),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morkhelvis._clamp(color)
        if _NS_morkhelvis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morkhelvis._clamp(color)
        if _NS_morkhelvis.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morkhelvis._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morkhelvis(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_morkhelvis._update_mkh_attack_anim(boss)
        attacking = bool(getattr(boss, "_mkh_attack_active", False))
        # Floating bob (heavier gargoyle - slower bob)
        float_bob = math.sin(pulse * 0.5) * 4
        y_floating = y - 6 + int(float_bob)
        # Ambient behind
        _NS_morkhelvis._draw_soul_aura(surface, x, y_floating, pulse)
        _NS_morkhelvis._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_morkhelvis._draw_gravechill_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating shadow
        _NS_morkhelvis._draw_floating_shadow(surface, x, y + 52, pulse)
        # Soul wisps rising
        _NS_morkhelvis._draw_soul_wisps(surface, x, y_floating + 22, pulse,
                                         intense=attacking)
        # Body
        _NS_morkhelvis._draw_gargoyle_body(surface, x, y_floating, boss.direction,
                                            pulse, "attack" if attacking else "idle",
                                            getattr(boss, "_mkh_attack_progress", 0.0))
        # Basic attack projectile (skull soul bolt)
        if attacking and not active_skill:
            _NS_morkhelvis._draw_basic_attack_fx(surface, boss, x, y_floating)
        # Skill FX
        if active_skill == "q":
            _NS_morkhelvis._draw_soulassumption_fx(surface, boss, x, y_floating,
                                                    skill_timer, pulse)
        elif active_skill == "w":
            _NS_morkhelvis._draw_gravechill_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morkhelvis._draw_familiar_fx(surface, boss, x, y_floating,
                                              skill_timer, pulse)
        elif active_skill == "r":
            _NS_morkhelvis._draw_summonfamiliars_fx(surface, boss, x, y_floating,
                                                     skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mkh_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mkh_previous_timer", timer))
        active = bool(getattr(boss, "_mkh_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._mkh_attack_active = True
            boss._mkh_attack_frame = 0
            active = True
        if active:
            boss._mkh_attack_frame = int(getattr(boss, "_mkh_attack_frame", 0)) + 1
            attack_duration = 35
            if boss._mkh_attack_frame >= attack_duration:
                boss._mkh_attack_active = False
                boss._mkh_attack_frame = 0
                active = False
        boss._mkh_previous_timer = timer
        if active:
            attack_duration = 35
            boss._mkh_attack_progress = min(1.0,
                boss._mkh_attack_frame / attack_duration)
        else:
            boss._mkh_attack_progress = 0.0
    # ============================================================
    # BODY (Gargoyle - stone quadruped with wings)
    # ============================================================
    def _draw_gargoyle_body(surface, cx, cy, facing, phase, action,
                             attack_progress):
        """Full gargoyle body with stone wings & 3 skulls."""
        # Wings behind
        _NS_morkhelvis._draw_stone_wings(surface, cx, cy - 6, facing, phase,
                                          action, attack_progress)
        # Tail behind
        _NS_morkhelvis._draw_stone_tail(surface, cx, cy + 6, facing, phase)
        # Rear legs dangling (floating)
        _NS_morkhelvis._draw_gargoyle_legs(surface, cx, cy + 8, facing, phase)
        # Main torso
        _NS_morkhelvis._draw_gargoyle_torso(surface, cx, cy, facing, phase)
        # Central chest skull (glowing)
        _NS_morkhelvis._draw_chest_skull(surface, cx, cy + 2, facing, phase, action)
        # Arms with skull-heads (long stone arms with claws)
        arm_swing = 0
        if action == "attack":
            arm_swing = int(math.sin(attack_progress * math.pi) * 5)
        _NS_morkhelvis._draw_stone_arms(surface, cx, cy, facing, phase, arm_swing,
                                         action, attack_progress)
        # Head with horns
        _NS_morkhelvis._draw_gargoyle_head(surface, cx, cy - 18, facing, phase)
    def _draw_stone_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Two large stone wings behind body."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 4
        else:
            beat = math.sin(phase * 1.0) * 3
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),
            (1, 0.7, 0.75),
        ]):
            base_x = cx - facing * 4
            base_y = cy - 2
            spar1_len = int(30 * size_mult)
            spar1_angle = math.pi * 0.7 * side_mult - math.radians(beat)
            spar2_len = int(34 * size_mult)
            spar2_angle = math.pi * 0.88 * side_mult - math.radians(beat * 0.8)
            spar3_len = int(26 * size_mult)
            spar3_angle = math.pi * 1.08 * side_mult - math.radians(beat * 0.5)
            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)
            membrane_points = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                (int(tip1_x * 0.6 + tip2_x * 0.4),
                 int(tip1_y * 0.6 + tip2_y * 0.4) + int(3 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.6 + tip3_x * 0.4),
                 int(tip2_y * 0.6 + tip3_y * 0.4) + int(3 * size_mult)),
                (tip3_x, tip3_y),
                (base_x - facing * 3, base_y + int(5 * size_mult)),
            ]
            wing_surf = pygame.Surface((170, 110), pygame.SRCALPHA)
            offset_x = base_x - 85
            offset_y = base_y - 55
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]
            _NS_morkhelvis._poly(wing_surf,
                                  (*_NS_morkhelvis.PALETTE["membrane_dark"],
                                   int(220 * alpha_mult)),
                                  local_points)
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.8 + cx_local * 0.2),
                     int(p[1] * 0.8 + cy_local * 0.2))
                )
            _NS_morkhelvis._poly(wing_surf,
                                  (*_NS_morkhelvis.PALETTE["stone_darkest"],
                                   int(200 * alpha_mult)),
                                  inner_pts)
            _NS_morkhelvis._poly(wing_surf,
                                  (*_NS_morkhelvis.PALETTE["membrane_mid"],
                                   int(160 * alpha_mult)),
                                  inner_pts)
            # Wing bones (stone spars)
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                pygame.draw.line(wing_surf,
                                 (*_NS_morkhelvis.PALETTE["stone_darkest"],
                                  int(255 * alpha_mult)),
                                 bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_morkhelvis.PALETTE["stone_dark"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_morkhelvis.PALETTE["stone_mid"],
                                  int(200 * alpha_mult)),
                                 bone_base, tip, 1)
                # Stone claw at end
                _NS_morkhelvis._aacircle(wing_surf,
                                         (*_NS_morkhelvis.PALETTE["stone_darkest"],
                                          int(240 * alpha_mult)),
                                         tip, 2)
                _NS_morkhelvis._aacircle(wing_surf,
                                         (*_NS_morkhelvis.PALETTE["stone_mid"],
                                          int(240 * alpha_mult)),
                                         tip, 1)
            # Cyan glow lines along top edge (soul infusion)
            pygame.draw.line(wing_surf,
                             (*_NS_morkhelvis.PALETTE["membrane_glow"],
                              int(200 * alpha_mult)),
                             bone_base,
                             (tip1_x - offset_x, tip1_y - offset_y), 1)
            # Glowing tip
            pygame.draw.rect(wing_surf,
                             (*_NS_morkhelvis.PALETTE["soul_light"],
                              int(240 * alpha_mult)),
                             (tip1_x - offset_x, tip1_y - offset_y, 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_stone_tail(surface, cx, cy, facing, phase):
        """Stone segmented tail."""
        back_dir = -facing
        base_x = cx + back_dir * 14
        base_y = cy + 2
        segments = 7
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (10 + t * 22))
            y_off = int(2 + t * 8 - t * t * 6)
            wave = math.sin(phase * 1.0 + t * math.pi) * (3 + t * 3)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))
        for i in range(len(points) - 1):
            thickness = max(2, 9 - i)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                                    (points[i][0] + 2, points[i][1] + 2),
                                    (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                    thickness + 1)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                                    points[i], points[i + 1], thickness)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_dark"],
                                    points[i], points[i + 1],
                                    max(1, thickness - 2))
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_mid"],
                                    (points[i][0], points[i][1] - 1),
                                    (points[i + 1][0], points[i + 1][1] - 1),
                                    max(1, thickness - 4))
        # Tail tip cyan glow
        if len(points) >= 2:
            end = points[-1]
            for r in range(4, 0, -1):
                alpha = _NS_morkhelvis._alpha(180 * (4 - r) / 4)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_light"],
                                          alpha),
                                         end, r)
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                             (end[0], end[1], 1, 1))
    def _draw_gargoyle_legs(surface, cx, cy, facing, phase):
        """Dangling rear legs."""
        sway = math.sin(phase * 0.8) * 2
        for side, x_base in [(-1, -10), (1, -4)]:
            leg_x = cx + x_base
            leg_top_y = cy
            leg_bot_y = cy + 14 + int(sway * side)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                                    (leg_x + 1, leg_top_y + 1),
                                    (leg_x + 1 + int(sway * side),
                                     leg_bot_y + 1), 6)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                                    (leg_x, leg_top_y),
                                    (leg_x + int(sway * side), leg_bot_y), 5)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_dark"],
                                    (leg_x, leg_top_y),
                                    (leg_x + int(sway * side), leg_bot_y), 3)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_mid"],
                                    (leg_x - 1, leg_top_y),
                                    (leg_x - 1 + int(sway * side),
                                     leg_bot_y), 1)
            # Stone claws
            claw_x = leg_x + int(sway * side)
            claw_y = leg_bot_y
            for cx_off in (-2, 0, 2):
                _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_darkest"], [
                    (claw_x + cx_off, claw_y),
                    (claw_x + cx_off - 1, claw_y + 4),
                    (claw_x + cx_off + 1, claw_y + 4),
                ])
                _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_mid"], [
                    (claw_x + cx_off, claw_y + 1),
                    (claw_x + cx_off, claw_y + 3),
                    (claw_x + cx_off + 1, claw_y + 3),
                ])
                pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["stone_edge"],
                                 (claw_x + cx_off, claw_y + 3, 1, 1))
    def _draw_gargoyle_torso(surface, cx, cy, facing, phase):
        """Main body torso (stone, bulky)."""
        body_shape = [
            (cx - 15, cy),
            (cx - 17, cy - 5),
            (cx - 13, cy - 10),
            (cx - 6, cy - 12),
            (cx + 6, cy - 12),
            (cx + 13, cy - 10),
            (cx + 17, cy - 5),
            (cx + 19, cy + 1),
            (cx + 16, cy + 8),
            (cx + 8, cy + 12),
            (cx - 2, cy + 13),
            (cx - 10, cy + 12),
            (cx - 16, cy + 8),
            (cx - 18, cy + 2),
        ]
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                              [(px + 2, py + 3) for px, py in body_shape])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                              body_shape)
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_dark"], [
            (cx - 15, cy - 2),
            (cx - 12, cy - 9),
            (cx - 4, cy - 11),
            (cx + 6, cy - 11),
            (cx + 12, cy - 9),
            (cx + 16, cy - 4),
            (cx + 17, cy),
            (cx + 13, cy + 3),
            (cx - 13, cy + 3),
            (cx - 15, cy),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_mid"], [
            (cx - 12, cy - 3),
            (cx - 9, cy - 7),
            (cx - 2, cy - 9),
            (cx + 6, cy - 9),
            (cx + 9, cy - 7),
            (cx + 13, cy - 3),
            (cx + 11, cy),
            (cx - 8, cy),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_light"], [
            (cx - 4, cy - 6),
            (cx + 2, cy - 7),
            (cx + 7, cy - 5),
            (cx + 5, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Chest cavity (dark hole for skull)
        pygame.draw.ellipse(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                            (cx - 4, cy - 2, 8, 10))
        pygame.draw.ellipse(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                            (cx - 3, cy - 1, 6, 8))
        # Stone segments/plates
        for row in range(2):
            y_row = cy - 6 + row * 3
            for dx in (-9, -4, 4, 9):
                offset_x = (row % 2) * 2 - 1
                pygame.draw.line(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                                 (cx + dx + offset_x - 1, y_row),
                                 (cx + dx + offset_x, y_row - 1), 1)
                pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["stone_edge"],
                                 (cx + dx + offset_x, y_row - 1, 1, 1))
        # Cracks with cyan glow (soul cracks)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for crack in [
            [(cx - 8, cy + 5), (cx - 4, cy + 8), (cx - 2, cy + 11)],
            [(cx + 6, cy + 4), (cx + 9, cy + 7), (cx + 11, cy + 10)],
        ]:
            for i in range(len(crack) - 1):
                pygame.draw.line(surface,
                                 (*_NS_morkhelvis.PALETTE["soul_dark"],
                                  _NS_morkhelvis._alpha(220 * pulse)),
                                 crack[i], crack[i + 1], 1)
                pygame.draw.line(surface,
                                 (*_NS_morkhelvis.PALETTE["soul_light"],
                                  _NS_morkhelvis._alpha(180 * pulse)),
                                 crack[i], crack[i + 1], 1)
    def _draw_chest_skull(surface, cx, cy, facing, phase, action):
        """Glowing skull in chest cavity."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        if action == "attack":
            pulse = min(1.0, pulse + 0.3)
        skull_x = cx
        skull_y = cy + 2
        # Outer glow
        for r in range(7, 0, -1):
            alpha = _NS_morkhelvis._alpha(120 * (7 - r) / 7 * pulse)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_light"], alpha),
                                     (skull_x, skull_y), r)
        # Skull shape (small)
        skull_pts = [
            (skull_x - 2, skull_y - 1),
            (skull_x - 3, skull_y + 1),
            (skull_x - 2, skull_y + 3),
            (skull_x + 2, skull_y + 3),
            (skull_x + 3, skull_y + 1),
            (skull_x + 2, skull_y - 1),
        ]
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["bone_dark"], skull_pts)
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["bone_mid"], [
            (skull_x - 2, skull_y),
            (skull_x - 2, skull_y + 2),
            (skull_x + 2, skull_y + 2),
            (skull_x + 2, skull_y),
        ])
        # Glowing eye sockets
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                         (skull_x - 1, skull_y, 1, 1))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                         (skull_x + 1, skull_y, 1, 1))
        # Jaw teeth
        pygame.draw.line(surface, _NS_morkhelvis.PALETTE["bone_light"],
                         (skull_x - 1, skull_y + 3),
                         (skull_x + 1, skull_y + 3), 1)
    def _draw_stone_arms(surface, cx, cy, facing, phase, swing, action,
                          attack_progress):
        """Two long stone arms ending in skull-hands."""
        arm_configs = [
            (-1, -14),  # left arm
            (1, 14),    # right arm
        ]
        for side, x_base in arm_configs:
            base_x = cx + x_base
            base_y = cy - 6
            # Arm reaches forward during attack
            if action == "attack":
                hand_x = base_x + facing * (8 + swing)
                hand_y = base_y + 14 - swing
            else:
                hand_x = base_x + int(math.sin(phase * 0.6 + side) * 2)
                hand_y = base_y + 18
            # Elbow midpoint
            mx = int((base_x + hand_x) / 2) + side * 2
            my = int((base_y + hand_y) / 2)
            # Upper arm (stone)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                                    (base_x + 1, base_y + 1),
                                    (mx + 1, my + 1), 6)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                                    (base_x, base_y), (mx, my), 6)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_dark"],
                                    (base_x, base_y), (mx, my), 4)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_mid"],
                                    (base_x - 1, base_y),
                                    (mx - 1, my), 2)
            # Forearm
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                                    (mx + 1, my + 1),
                                    (hand_x + 1, hand_y + 1), 5)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                                    (mx, my), (hand_x, hand_y), 5)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_dark"],
                                    (mx, my), (hand_x, hand_y), 3)
            _NS_morkhelvis._aaline(surface, _NS_morkhelvis.PALETTE["stone_mid"],
                                    (mx - 1, my), (hand_x - 1, hand_y), 1)
            # Skull-hand at end
            _NS_morkhelvis._draw_hand_skull(surface, hand_x, hand_y, facing,
                                             phase, side, action)
    def _draw_hand_skull(surface, sx, sy, facing, phase, side, action):
        """Skull-shaped hand with glowing eyes."""
        pulse = math.sin(phase * 2.5 + side) * 0.3 + 0.7
        if action == "attack":
            pulse = min(1.0, pulse + 0.4)
        # Outer glow
        for r in range(6, 0, -1):
            alpha = _NS_morkhelvis._alpha(140 * (6 - r) / 6 * pulse)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_light"], alpha),
                                     (sx, sy), r)
        # Skull shape
        skull_pts = [
            (sx - 4, sy - 3),
            (sx - 5, sy),
            (sx - 4, sy + 3),
            (sx - 2, sy + 5),
            (sx + 2, sy + 5),
            (sx + 4, sy + 3),
            (sx + 5, sy),
            (sx + 4, sy - 3),
        ]
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in skull_pts])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["bone_dark"], skull_pts)
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["bone_mid"], [
            (sx - 3, sy - 2),
            (sx - 4, sy),
            (sx - 3, sy + 2),
            (sx + 3, sy + 2),
            (sx + 4, sy),
            (sx + 3, sy - 2),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["bone_light"], [
            (sx - 2, sy - 1),
            (sx + 2, sy - 1),
            (sx + 2, sy + 1),
            (sx - 2, sy + 1),
        ])
        # Glowing eye sockets
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                         (sx - 3, sy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                         (sx + 2, sy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_mid"],
                         (sx - 3, sy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_mid"],
                         (sx + 2, sy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                         (sx - 2, sy, 1, 1))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                         (sx + 2, sy, 1, 1))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                         (sx - 2, sy, 1, 1))
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                         (sx + 2, sy, 1, 1))
        # Jaw teeth
        for tx in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["bone_light"],
                             (sx + tx, sy + 3, 1, 2))
        # Soul flame emanating (small)
        for i in range(3):
            wisp_t = (phase * 0.5 + i * 0.33) % 1.0
            wx = sx + int(math.sin(phase + i) * 3)
            wy = sy - 4 - int(wisp_t * 6)
            alpha = _NS_morkhelvis._alpha(200 * (1 - wisp_t) * pulse)
            pygame.draw.rect(surface, (*_NS_morkhelvis.PALETTE["soul_light"], alpha),
                             (wx, wy, 1, 1))
            pygame.draw.rect(surface, (*_NS_morkhelvis.PALETTE["soul_shine"], alpha),
                             (wx, wy - 1, 1, 1))
    def _draw_gargoyle_head(surface, cx, cy, facing, phase):
        """Gargoyle head with horns and glowing eyes."""
        head_shape = [
            (cx - 7, cy + 4),
            (cx - 8, cy - 1),
            (cx - 6, cy - 6),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 6, cy - 6),
            (cx + 8, cy - 1),
            (cx + 7, cy + 4),
            (cx + 4, cy + 7),
            (cx - 4, cy + 7),
        ]
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in head_shape])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                              head_shape)
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_dark"], [
            (cx - 7, cy + 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 5),
            (cx + 5, cy - 5),
            (cx + 7, cy - 1),
            (cx + 7, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_mid"], [
            (cx - 5, cy),
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["stone_light"],
                         (cx - 2, cy - 1, 4, 2))
        # Horns (curving back)
        for side in (-1, 1):
            for i, (off_x, off_y, len_h) in enumerate([
                (5, -4, 6), (6, -2, 8),
            ]):
                bx = cx + side * off_x
                by = cy + off_y
                tx_h = bx + side * (len_h - 2)
                ty_h = by - len_h
                _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                                      [(tx_h + 1, ty_h + 1),
                                       (bx - 1, by + 1),
                                       (bx + 1, by + 1)])
                _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_darkest"],
                                      [(tx_h, ty_h), (bx - 2, by), (bx + 2, by)])
                _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["stone_dark"],
                                      [(tx_h, ty_h), (bx - 1, by), (bx + 1, by)])
                pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["stone_mid"],
                                 (tx_h, ty_h, 1, 1))
        # Glowing eyes
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["eye_socket"],
                             (eye_x - 1, cy - 1, 3, 2))
            for r in range(3, 0, -1):
                alpha = _NS_morkhelvis._alpha(180 * (3 - r) / 3 * pulse)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["eye_glow"],
                                          alpha),
                                         (eye_x, cy), r)
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                             (eye_x, cy, 1, 1))
        # Mouth line
        pygame.draw.line(surface, _NS_morkhelvis.PALETTE["shadow_deep"],
                         (cx - 3, cy + 4), (cx + 3, cy + 4), 1)
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.15 + 0.85
        shadow = pygame.Surface((130, 30), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, int((13 - radius) * 14 * pulse))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 110 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 8, int(160 * pulse)), (8, 9, 114, 12))
        surface.blit(shadow, (x - 65, y - 15))
    def _draw_soul_aura(surface, x, y, phase):
        """Cyan soul aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_morkhelvis._alpha((90 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_morkhelvis._aacircle(aura,
                                         (*_NS_morkhelvis.PALETTE["soul_dark"],
                                          alpha),
                                         (110, 100), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_morkhelvis._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_morkhelvis._aacircle(aura,
                                         (*_NS_morkhelvis.PALETTE["soul_mid"],
                                          alpha),
                                         (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating soul particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                             (sx, sy, 1, 1))
    def _draw_soul_wisps(surface, cx, cy, phase, intense=False):
        """Rising cyan soul wisps."""
        strength = 1.4 if intense else 1.0
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24, -30, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_morkhelvis._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_dark"], alpha),
                                     (sx, sy), 3)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_morkhelvis.PALETTE["soul_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_morkhelvis.PALETTE["soul_shine"], alpha),
                             (sx, sy - 2, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morkhelvis.PALETTE["soul_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_morkhelvis.PALETTE["stone_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_morkhelvis.PALETTE["soul_mid"], 220),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morkhelvis.PALETTE["soul_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_morkhelvis.PALETTE["soul_hot"],
                                        _NS_morkhelvis._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - Soul Skull Bolt
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic ranged: skull bolt projectile from hand."""
        progress = getattr(boss, "_mkh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        tx, ty = _NS_morkhelvis._target_position(boss, x, y)
        # PHASE 1: Charge at hand-skull
        if progress < 0.4:
            t = progress / 0.4
            hand_x = x + facing * 22
            hand_y = y + 2
            charge_r = int(3 + t * 6)
            for r in range(charge_r + 4, 0, -1):
                alpha = _NS_morkhelvis._alpha(180 * (charge_r + 4 - r)
                                              / (charge_r + 4) * t)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_dark"], alpha),
                                         (hand_x, hand_y), r)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_mid"],
                                      _NS_morkhelvis._alpha(220 * t)),
                                     (hand_x, hand_y), max(1, charge_r - 2))
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_hot"],
                                      _NS_morkhelvis._alpha(240 * t)),
                                     (hand_x, hand_y), max(1, charge_r - 4))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                             (hand_x, hand_y, 1, 1))
            # Orbit sparks
            for i in range(5):
                a = boss.pulse * 6 + i * math.pi * 2 / 5
                sr = charge_r + 3
                sx = hand_x + int(math.cos(a) * sr)
                sy = hand_y + int(math.sin(a) * sr)
                pygame.draw.rect(surface,
                                 (*_NS_morkhelvis.PALETTE["soul_shine"],
                                  _NS_morkhelvis._alpha(240 * t)),
                                 (sx, sy, 1, 1))
        # PHASE 2: Ghost skull projectile flight
        else:
            t = min(1.0, (progress - 0.4) / 0.55)
            start_x = x + facing * 26
            start_y = y + 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Trail of small skulls/wisps
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_morkhelvis._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_darkest"],
                                          alpha),
                                         (px, py), size)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_dark"],
                                          alpha),
                                         (px, py), max(1, size - 1))
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_mid"],
                                          alpha),
                                         (px, py), max(1, size - 2))
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_light"],
                                          alpha),
                                         (px, py), max(1, size - 3))
                if i < 4:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 1))
                        pygame.draw.rect(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Skull head projectile
            # Outer glow
            for r in range(11, 3, -1):
                alpha = _NS_morkhelvis._alpha(120 * (11 - r) / 11)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_light"],
                                          alpha),
                                         (bx, by), r)
            # Skull body
            skull_pts = [
                (bx - 4, by - 3),
                (bx - 5, by),
                (bx - 4, by + 3),
                (bx - 2, by + 5),
                (bx + 2, by + 5),
                (bx + 4, by + 3),
                (bx + 5, by),
                (bx + 4, by - 3),
            ]
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_dark"],
                                  skull_pts)
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_mid"], [
                (bx - 3, by - 2),
                (bx - 4, by),
                (bx - 3, by + 2),
                (bx + 3, by + 2),
                (bx + 4, by),
                (bx + 3, by - 2),
            ])
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_light"], [
                (bx - 2, by - 1),
                (bx + 2, by - 1),
                (bx + 2, by + 1),
                (bx - 2, by + 1),
            ])
            # Skull eyes (bright)
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                             (bx - 2, by - 1, 2, 2))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                             (bx + 1, by - 1, 2, 2))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                             (bx - 1, by, 1, 1))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                             (bx + 2, by, 1, 1))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["white"],
                             (bx - 1, by, 1, 1))
            # Jaw teeth
            for tx_off in (-2, 0, 2):
                pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["bone_light"],
                                 (bx + tx_off, by + 3, 1, 2))
            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(8 + st * 22)
                alpha = _NS_morkhelvis._alpha(240 * (1 - st))
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_darkest"],
                                          alpha),
                                         (tx, ty), radius + 3, 3)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_dark"],
                                          alpha),
                                         (tx, ty), radius, 3)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_mid"],
                                          alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_light"],
                                          alpha),
                                         (tx, ty), max(1, radius - 11), 1)
                core_r = max(1, int(6 * (1 - st)))
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_hot"],
                                          alpha),
                                         (tx, ty), core_r + 1)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_shine"],
                                          alpha),
                                         (tx, ty), max(1, core_r - 1))
                for i in range(10):
                    angle = i * math.pi / 5
                    ex = tx + int(math.cos(angle) * radius)
                    ey = ty + int(math.sin(angle) * radius * 0.8)
                    pygame.draw.rect(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: Q - SOUL ASSUMPTION (beam of souls to target)
    # ============================================================
    def _draw_soulassumption_fx(surface, boss, x, y, timer, phase):
        """Soul-draining beam of skulls."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morkhelvis._target_position(boss, x, y)
        start_x = x + facing * 26
        start_y = y + 2
        if progress < 0.3:
            # Charge
            t = progress / 0.3
            charge_r = int(5 + t * 9)
            for r in range(charge_r + 5, 0, -1):
                alpha = _NS_morkhelvis._alpha(220 * (charge_r + 5 - r)
                                              / (charge_r + 5) * t)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_mid"], alpha),
                                         (start_x, start_y), r)
            _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_light"],
                                     (start_x, start_y), max(1, charge_r - 3))
            _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                                     (start_x, start_y), max(1, charge_r - 5))
        else:
            t = (progress - 0.3) / 0.7
            # Continuous beam of souls flying to target
            # Multiple soul-skulls streaming
            beam_length = math.hypot(tx - start_x, ty - start_y)
            num_souls = 8
            for i in range(num_souls):
                soul_t = ((phase * 0.4) + i / num_souls) % 1.0
                sx = int(start_x + (tx - start_x) * soul_t)
                sy = int(start_y + (ty - start_y) * soul_t)
                soul_size = 4 - int(soul_t * 2)
                alpha = _NS_morkhelvis._alpha(240 * (1 - soul_t * 0.3))
                # Small skull shape
                for r in range(soul_size + 3, 0, -1):
                    a = _NS_morkhelvis._alpha(120 * (soul_size + 3 - r)
                                              / (soul_size + 3))
                    _NS_morkhelvis._aacircle(surface,
                                             (*_NS_morkhelvis.PALETTE["soul_light"],
                                              a),
                                             (sx, sy), r)
                _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_dark"],
                                         (sx, sy), soul_size)
                _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_mid"],
                                         (sx, sy), max(1, soul_size - 1))
                _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                                         (sx, sy), max(1, soul_size - 2))
                pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                                 (sx, sy, 1, 1))
            # Beam line connecting
            pygame.draw.line(surface, (*_NS_morkhelvis.PALETTE["soul_dark"], 160),
                             (start_x, start_y), (tx, ty), 2)
            pygame.draw.line(surface, (*_NS_morkhelvis.PALETTE["soul_light"], 200),
                             (start_x, start_y), (tx, ty), 1)
            # Impact at target (continuous)
            for r in range(12, 0, -2):
                alpha = _NS_morkhelvis._alpha(180 * (12 - r) / 12)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_mid"], alpha),
                                         (tx, ty), r)
            _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_light"],
                                     (tx, ty), 4)
            _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                                     (tx, ty), 2)
    # ============================================================
    # SKILL: W - GRAVE CHILL (ice crystals AoE)
    # ============================================================
    def _draw_gravechill_ground(surface, boss, x, y, timer, phase):
        """Frozen ground effect."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Ground area in front of boss
        start_x = x + facing * 20
        r = int(60 * min(1.0, progress * 2))
        if r > 5:
            alpha = _NS_morkhelvis._alpha(160 * (1 - progress * 0.3))
            pygame.draw.ellipse(surface, (*_NS_morkhelvis.PALETTE["soul_darkest"],
                                           alpha),
                                (start_x - r + 30, y + 40 - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morkhelvis.PALETTE["soul_dark"], alpha),
                                (start_x - r + 33, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_gravechill_fx(surface, boss, x, y, timer, phase):
        """Ice crystals bursting from ground."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        start_x = x + facing * 50
        base_y = y + 40
        # Multiple ice crystals in a cone/area
        crystal_positions = [
            (0, 0), (-15, -5), (15, -5), (-30, 3), (30, 3),
            (-8, -12), (8, -12), (0, -18), (-20, 10), (20, 10),
            (-40, -2), (40, -2),
        ]
        for i, (dx, dy) in enumerate(crystal_positions):
            # Rise and fall animation
            delay = i * 0.04
            local_t = max(0.0, min(1.0, (progress - delay) / (1 - delay)))
            if local_t <= 0:
                continue
            if local_t < 0.3:
                height = int((local_t / 0.3) * 18)
            else:
                height = int(18 * (1 - (local_t - 0.3) / 0.7 * 0.4))
            cx_ice = start_x + dx * facing
            cy_ice = base_y + dy
            # Ice crystal shape (angular)
            tip_x = cx_ice
            tip_y = cy_ice - height
            base_a = (cx_ice - 4, cy_ice)
            base_b = (cx_ice + 4, cy_ice)
            mid_l = (cx_ice - 3, cy_ice - height // 2)
            mid_r = (cx_ice + 3, cy_ice - height // 2)
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (mid_l[0] + 1, mid_l[1] + 1),
                (base_a[0] + 1, base_a[1] + 1),
                (base_b[0] + 1, base_b[1] + 1),
                (mid_r[0] + 1, mid_r[1] + 1),
            ])
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_darkest"], [
                (tip_x, tip_y), mid_l, base_a, base_b, mid_r,
            ])
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_dark"], [
                (tip_x, tip_y),
                (cx_ice - 2, cy_ice - height // 2),
                (cx_ice - 3, cy_ice),
                (cx_ice + 3, cy_ice),
                (cx_ice + 2, cy_ice - height // 2),
            ])
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_mid"], [
                (tip_x, tip_y),
                (cx_ice - 1, cy_ice - height // 2),
                (cx_ice - 2, cy_ice),
                (cx_ice + 2, cy_ice),
                (cx_ice + 1, cy_ice - height // 2),
            ])
            _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_light"], [
                (tip_x, tip_y),
                (cx_ice, cy_ice - height // 2),
                (cx_ice, cy_ice - 2),
            ])
            # Bright tip
            for r in range(3, 0, -1):
                alpha = _NS_morkhelvis._alpha(220 * (3 - r) / 3)
                _NS_morkhelvis._aacircle(surface,
                                         (*_NS_morkhelvis.PALETTE["soul_hot"],
                                          alpha),
                                         (tip_x, tip_y), r)
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))
    # ============================================================
    # SKILL: E - FAMILIAR (single bird projectile)
    # ============================================================
    def _draw_familiar_fx(surface, boss, x, y, timer, phase):
        """Familiar bird flying to target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morkhelvis._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 4
        t = progress
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t
                 - math.sin(t * math.pi) * 15)  # arc trajectory
        # Wing flap
        flap = math.sin(phase * 8) * 4
        # Draw bird (spirit crow)
        _NS_morkhelvis._draw_spirit_bird(surface, bx, by, facing, flap, phase)
        # Trail behind
        for i in range(6):
            trail_t = max(0.0, t - i * 0.08)
            tpx = int(start_x + (tx - start_x) * trail_t)
            tpy = int(start_y + (ty - start_y) * trail_t
                      - math.sin(trail_t * math.pi) * 15)
            alpha = _NS_morkhelvis._alpha(180 - i * 30)
            size = max(1, 4 - i)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_mid"], alpha),
                                     (tpx, tpy), size)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_light"], alpha),
                                     (tpx, tpy), max(1, size - 1))
            pygame.draw.rect(surface, (*_NS_morkhelvis.PALETTE["soul_shine"], alpha),
                             (tpx, tpy, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(8 + st * 18)
            alpha = _NS_morkhelvis._alpha(240 * (1 - st))
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_dark"], alpha),
                                     (tx, ty), radius, 2)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_mid"], alpha),
                                     (tx, ty), max(1, radius - 4), 1)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_light"], alpha),
                                     (tx, ty), max(1, radius // 2))
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_shine"], alpha),
                                     (tx, ty), max(1, radius // 4))
    def _draw_spirit_bird(surface, bx, by, facing, flap, phase):
        """Cyan spirit bird/crow."""
        # Outer glow
        for r in range(8, 0, -1):
            alpha = _NS_morkhelvis._alpha(120 * (8 - r) / 8)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_light"], alpha),
                                     (bx, by), r)
        # Body (ellipse)
        pygame.draw.ellipse(surface, _NS_morkhelvis.PALETTE["soul_dark"],
                            (bx - 5, by - 2, 10, 5))
        pygame.draw.ellipse(surface, _NS_morkhelvis.PALETTE["soul_mid"],
                            (bx - 4, by - 1, 8, 3))
        # Wings (spread with flap)
        wing_h = int(4 + flap)
        # Left wing
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_dark"], [
            (bx - 3, by),
            (bx - 12, by - wing_h),
            (bx - 10, by + 1),
            (bx - 3, by + 2),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_mid"], [
            (bx - 3, by),
            (bx - 10, by - wing_h + 1),
            (bx - 8, by),
            (bx - 3, by + 1),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_light"], [
            (bx - 3, by),
            (bx - 8, by - wing_h + 2),
            (bx - 6, by),
        ])
        # Right wing
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_dark"], [
            (bx + 3, by),
            (bx + 12, by - wing_h),
            (bx + 10, by + 1),
            (bx + 3, by + 2),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_mid"], [
            (bx + 3, by),
            (bx + 10, by - wing_h + 1),
            (bx + 8, by),
            (bx + 3, by + 1),
        ])
        _NS_morkhelvis._poly(surface, _NS_morkhelvis.PALETTE["soul_light"], [
            (bx + 3, by),
            (bx + 8, by - wing_h + 2),
            (bx + 6, by),
        ])
        # Head (front-facing based on direction)
        head_x = bx + facing * 5
        _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_dark"],
                                 (head_x, by - 1), 3)
        _NS_morkhelvis._aacircle(surface, _NS_morkhelvis.PALETTE["soul_mid"],
                                 (head_x, by - 1), 2)
        # Beak
        pygame.draw.line(surface, _NS_morkhelvis.PALETTE["bone_light"],
                         (head_x + facing * 2, by - 1),
                         (head_x + facing * 4, by), 1)
        # Eye
        pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_shine"],
                         (head_x + facing, by - 2, 1, 1))
        # Tail trailing wisps
        pygame.draw.line(surface,
                         (*_NS_morkhelvis.PALETTE["soul_light"], 200),
                         (bx - facing * 5, by),
                         (bx - facing * 9, by + 1), 1)
    # ============================================================
    # SKILL: R - SUMMON FAMILIARS (2 birds)
    # ============================================================
    def _draw_summonfamiliars_fx(surface, boss, x, y, timer, phase):
        """Summon 2 spirit birds that fly toward target."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morkhelvis._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 4
        # Summoning circle at boss
        if progress < 0.3:
            t = progress / 0.3
            r = int(15 * t)
            alpha = _NS_morkhelvis._alpha(220 * t)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_dark"], alpha),
                                     (start_x, start_y), r + 2, 2)
            _NS_morkhelvis._aacircle(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_mid"], alpha),
                                     (start_x, start_y), r, 1)
            # Runes
            for i in range(6):
                a = phase * 3 + i * math.pi / 3
                rx = start_x + int(math.cos(a) * r)
                ry = start_y + int(math.sin(a) * r)
                pygame.draw.rect(surface, _NS_morkhelvis.PALETTE["soul_hot"],
                                 (rx, ry, 2, 2))
        # 2 birds flying with sinusoidal offset paths
        if progress > 0.2:
            fly_t = min(1.0, (progress - 0.2) / 0.8)
            for bird_i, y_offset_mult in enumerate([-1, 1]):
                # Each bird has slightly different path
                path_y_offset = y_offset_mult * int(20 * math.sin(fly_t * math.pi))
                bx = int(start_x + (tx - start_x) * fly_t)
                by = int(start_y + (ty - start_y) * fly_t + path_y_offset)
                flap = math.sin(phase * 8 + bird_i * math.pi) * 4
                _NS_morkhelvis._draw_spirit_bird(surface, bx, by, facing, flap,
                                                  phase)
                # Trail per bird
                for i in range(5):
                    trail_t = max(0.0, fly_t - i * 0.08)
                    path_off = y_offset_mult * int(20 * math.sin(trail_t * math.pi))
                    tpx = int(start_x + (tx - start_x) * trail_t)
                    tpy = int(start_y + (ty - start_y) * trail_t + path_off)
                    alpha = _NS_morkhelvis._alpha(180 - i * 30)
                    size = max(1, 4 - i)
                    _NS_morkhelvis._aacircle(surface,
                                             (*_NS_morkhelvis.PALETTE["soul_mid"],
                                              alpha),
                                             (tpx, tpy), size)
                    _NS_morkhelvis._aacircle(surface,
                                             (*_NS_morkhelvis.PALETTE["soul_light"],
                                              alpha),
                                             (tpx, tpy), max(1, size - 1))
                    pygame.draw.rect(surface,
                                     (*_NS_morkhelvis.PALETTE["soul_shine"], alpha),
                                     (tpx, tpy, 1, 1))
                # Impact on arrival
                if fly_t > 0.9:
                    st = (fly_t - 0.9) / 0.1
                    radius = int(6 + st * 14)
                    alpha = _NS_morkhelvis._alpha(240 * (1 - st))
                    impact_x = tx
                    impact_y = ty + path_y_offset
                    _NS_morkhelvis._aacircle(surface,
                                             (*_NS_morkhelvis.PALETTE["soul_dark"],
                                              alpha),
                                             (impact_x, impact_y), radius, 2)
                    _NS_morkhelvis._aacircle(surface,
                                             (*_NS_morkhelvis.PALETTE["soul_light"],
                                              alpha),
                                             (impact_x, impact_y),
                                             max(1, radius // 2))
                    _NS_morkhelvis._aacircle(surface,
                                             (*_NS_morkhelvis.PALETTE["soul_shine"],
                                              alpha),
                                             (impact_x, impact_y),
                                             max(1, radius // 4))



# ====================================================================
# VORTHAKUL (TERROR OF THE ABYSS) - Mini Boss
# ====================================================================

class _NS_vorthakul:
    """Namespace vorthakul - Void terror boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Void purple (main body)
        "void_darkest": (8, 3, 15),
        "void_dark": (25, 12, 45),
        "void_mid": (55, 30, 90),
        "void_light": (95, 60, 145),
        "void_edge": (145, 100, 195),
        "void_shine": (200, 165, 235),
        # Magenta/pink glow (eyes, mouth, spikes glow)
        "pink_darkest": (35, 5, 25),
        "pink_dark": (95, 15, 60),
        "pink_mid": (190, 35, 115),
        "pink_light": (255, 90, 175),
        "pink_hot": (255, 150, 210),
        "pink_shine": (255, 220, 240),
        # Belly (dark chitin)
        "belly_darkest": (15, 8, 25),
        "belly_dark": (40, 22, 55),
        "belly_mid": (75, 50, 95),
        "belly_light": (120, 90, 145),
        # Teeth/fangs (bone white with pink tint)
        "fang_dark": (70, 55, 65),
        "fang_mid": (160, 140, 155),
        "fang_light": (235, 220, 230),
        "fang_shine": (255, 245, 250),
        # Eye (magenta glowing)
        "eye_socket": (5, 2, 8),
        "eye_darkest": (40, 5, 25),
        "eye_dark": (110, 20, 70),
        "eye_mid": (220, 50, 140),
        "eye_light": (255, 130, 200),
        "eye_glow": (255, 210, 240),
        # Spike (chitinous with pink glow)
        "spike_dark": (30, 15, 45),
        "spike_mid": (75, 45, 110),
        "spike_light": (150, 105, 195),
        "spike_glow": (255, 100, 195),
        # Void aura
        "aura_dark": (20, 8, 35),
        "aura_mid": (70, 30, 110),
        "aura_light": (160, 90, 210),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vorthakul._clamp(color)
        if _NS_vorthakul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vorthakul._clamp(color)
        if _NS_vorthakul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vorthakul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vorthakul(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_vorthakul._update_vth_attack_anim(boss)
        attacking = (
            getattr(boss, "_vth_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Floating bob offset
        float_bob = math.sin(pulse * 0.7) * 6
        y_floating = y - 8 + int(float_bob)
        # Ambient behind
        _NS_vorthakul._draw_void_aura(surface, x, y_floating, pulse)
        _NS_vorthakul._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "q":
            _NS_vorthakul._draw_rupture_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vorthakul._draw_scream_ground(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorthakul._draw_feast_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating shadow
        _NS_vorthakul._draw_floating_shadow(surface, x, y + 52, pulse)
        # Body
        if attacking:
            _NS_vorthakul._draw_vth_attack(surface, boss, x, y_floating)
            # >>> BASIC ATTACK FX (claw slash + bite impact) <<<
            if not active_skill:
                _NS_vorthakul._draw_basic_attack_fx(surface, boss, x, y_floating)
        else:
            _NS_vorthakul._draw_vth_float(surface, boss, x, y_floating)
        # Foreground FX (skills)
        if active_skill == "q":
            _NS_vorthakul._draw_rupture_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vorthakul._draw_scream_foreground(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vorthakul._draw_voidspikes_foreground(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorthakul._draw_feast_foreground(surface, boss, x, y_floating, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE (FIXED)
    # ============================================================
    def _update_vth_attack_anim(boss):
        """Track attack animation - triggers on cooldown reset."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vth_previous_timer", timer))
        active = bool(getattr(boss, "_vth_attack_active", False))
        # Trigger: timer just reset (was high, now low) OR timer near max
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._vth_attack_active = True
            boss._vth_attack_frame = 0
            active = True
        if active:
            boss._vth_attack_frame = int(getattr(boss, "_vth_attack_frame", 0)) + 1
            attack_duration = 35  # ~0.6 detik
            if boss._vth_attack_frame >= attack_duration:
                boss._vth_attack_active = False
                boss._vth_attack_frame = 0
                active = False
        boss._vth_previous_timer = timer
        if active:
            attack_duration = 35
            boss._vth_attack_progress = min(1.0,
                boss._vth_attack_frame / attack_duration)
        else:
            boss._vth_attack_progress = 0.0
    # ============================================================
    # ENTRY POINT (FIXED)
    # ============================================================
    def draw_vorthakul(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_vorthakul._update_vth_attack_anim(boss)
        # Attacking = animation is playing
        attacking = bool(getattr(boss, "_vth_attack_active", False))
        # Floating bob offset
        float_bob = math.sin(pulse * 0.7) * 6
        y_floating = y - 8 + int(float_bob)
        # Ambient behind
        _NS_vorthakul._draw_void_aura(surface, x, y_floating, pulse)
        _NS_vorthakul._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "q":
            _NS_vorthakul._draw_rupture_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vorthakul._draw_scream_ground(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorthakul._draw_feast_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating shadow
        _NS_vorthakul._draw_floating_shadow(surface, x, y + 52, pulse)
        # Body
        if attacking:
            _NS_vorthakul._draw_vth_attack(surface, boss, x, y_floating)
            # >>> BASIC ATTACK PROJECTILE (only when no skill active) <<<
            if not active_skill:
                _NS_vorthakul._draw_basic_attack_fx(surface, boss, x, y_floating)
        else:
            _NS_vorthakul._draw_vth_float(surface, boss, x, y_floating)
        # Foreground FX (skills)
        if active_skill == "q":
            _NS_vorthakul._draw_rupture_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vorthakul._draw_scream_foreground(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vorthakul._draw_voidspikes_foreground(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorthakul._draw_feast_foreground(surface, boss, x, y_floating, skill_timer, pulse)
    # ============================================================
    # BASIC ATTACK FX - RANGED VOID PROJECTILE
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic ranged attack: void orb projectile dengan comet trail."""
        progress = getattr(boss, "_vth_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        tx, ty = _NS_vorthakul._target_position(boss, x, y)
        # ==================== PHASE 1: CHARGE (0-40%) ====================
        # Pink void energy terkumpul di mulut boss
        if progress < 0.4:
            t = progress / 0.4
            mouth_x = x + facing * 28
            mouth_y = y - 6
            # Growing charge orb
            charge_r = int(3 + t * 7)
            # Outer glow halo
            for r in range(charge_r + 5, 0, -1):
                alpha = _NS_vorthakul._alpha(180 * (charge_r + 5 - r)
                                             / (charge_r + 5) * t)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                        (mouth_x, mouth_y), r)
            # Mid layer
            for r in range(charge_r + 2, 0, -1):
                alpha = _NS_vorthakul._alpha(220 * (charge_r + 2 - r)
                                             / (charge_r + 2) * t)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_mid"], alpha),
                                        (mouth_x, mouth_y), r)
            # Bright core
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["pink_light"],
                                     _NS_vorthakul._alpha(240 * t)),
                                    (mouth_x, mouth_y), max(1, charge_r - 2))
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["pink_hot"],
                                     _NS_vorthakul._alpha(255 * t)),
                                    (mouth_x, mouth_y), max(1, charge_r - 4))
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["pink_shine"],
                                     _NS_vorthakul._alpha(255 * t)),
                                    (mouth_x, mouth_y), max(1, charge_r - 6))
            # Orbiting sparks (energy gathering)
            for i in range(6):
                angle = boss.pulse * 6 + i * math.pi / 3
                orbit_r = charge_r + 3 + int(math.sin(boss.pulse * 4 + i) * 2)
                sx = mouth_x + int(math.cos(angle) * orbit_r)
                sy = mouth_y + int(math.sin(angle) * orbit_r)
                pygame.draw.rect(surface,
                                 (*_NS_vorthakul.PALETTE["pink_hot"],
                                  _NS_vorthakul._alpha(240 * t)),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_vorthakul.PALETTE["pink_shine"],
                                  _NS_vorthakul._alpha(255 * t)),
                                 (sx, sy, 1, 1))
            # Attracting particles (flowing INTO charge)
            for i in range(4):
                p_t = (boss.pulse * 0.3 + i * 0.25) % 1.0
                p_dist = int((1 - p_t) * 15)
                p_angle = i * math.pi / 2 + boss.pulse
                px = mouth_x + int(math.cos(p_angle) * p_dist)
                py = mouth_y + int(math.sin(p_angle) * p_dist)
                alpha = _NS_vorthakul._alpha(200 * p_t * t)
                pygame.draw.rect(surface,
                                 (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                 (px, py, 1, 1))
        # ==================== PHASE 2: PROJECTILE FLIGHT (40-95%) ====================
        else:
            t = (progress - 0.4) / 0.55
            t = min(1.0, t)
            # Launch point at mouth
            start_x = x + facing * 32
            start_y = y - 6
            # Current projectile position
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # ---------- LONG COMET TRAIL ----------
            for i in range(11):
                trail_t = max(0.0, t - i * 0.045)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_vorthakul._alpha(230 - i * 22)
                size = max(1, 8 - i)
                # Outer dark
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_darkest"], alpha),
                                        (px, py), size)
                # Mid
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_mid"], alpha),
                                        (px, py), max(1, size - 2))
                # Light
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                        (px, py), max(1, size - 3))
                # Sparkles around trail
                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s)
                                           * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s)
                                           * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_vorthakul.PALETTE["pink_hot"],
                                          alpha),
                                         (spark_x, spark_y, 1, 1))
            # ---------- VOID ORB HEAD ----------
            # Radial glow halo
            for r in range(14, 3, -2):
                alpha_h = _NS_vorthakul._alpha(90 * (14 - r) / 14)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_light"], alpha_h),
                                        (bx, by), r)
            # Main orb layers
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_darkest"],
                                    (bx, by), 9)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_dark"],
                                    (bx, by), 7)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_mid"],
                                    (bx, by), 5)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_light"],
                                    (bx, by), 3)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_hot"],
                                    (bx, by), 2)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_shine"],
                                    (bx, by), 1)
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["white"],
                             (bx, by, 1, 1))
            # Void tendrils around orb (spiky void aura)
            for i in range(6):
                angle = boss.pulse * 3 + i * math.pi / 3
                tendril_len = 6 + int(math.sin(boss.pulse * 4 + i) * 2)
                tx_end = bx + int(math.cos(angle) * tendril_len)
                ty_end = by + int(math.sin(angle) * tendril_len)
                pygame.draw.line(surface,
                                 (*_NS_vorthakul.PALETTE["pink_light"], 200),
                                 (bx, by), (tx_end, ty_end), 1)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                                 (tx_end, ty_end, 1, 1))
            # ---------- IMPACT SPLASH (near target) ----------
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(8 + st * 26)
                alpha_i = _NS_vorthakul._alpha(240 * (1 - st))
                # Expanding rings
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_darkest"],
                                         alpha_i),
                                        (tx, ty), radius + 3, 3)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_dark"],
                                         alpha_i),
                                        (tx, ty), radius, 3)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_mid"],
                                         alpha_i),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_light"],
                                         alpha_i),
                                        (tx, ty), max(1, radius - 11), 1)
                # Bright core burst
                core_r = max(1, int(8 * (1 - st)))
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_hot"],
                                         alpha_i),
                                        (tx, ty), core_r + 1)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_shine"],
                                         alpha_i),
                                        (tx, ty), max(1, core_r - 1))
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["white"],
                                 (tx, ty, 1, 1))
                # Radial burst particles
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.8)
                    pygame.draw.rect(surface,
                                     (*_NS_vorthakul.PALETTE["pink_hot"], alpha_i),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_vorthakul.PALETTE["pink_shine"], alpha_i),
                                     (ex, ey, 1, 1))
                # Radial lines
                for i in range(8):
                    angle_l = i * math.pi / 4
                    line_end_x = tx + int(math.cos(angle_l) * (radius + 4))
                    line_end_y = ty + int(math.sin(angle_l) * (radius + 4) * 0.8)
                    pygame.draw.line(surface,
                                     (*_NS_vorthakul.PALETTE["pink_light"], alpha_i),
                                     (tx, ty), (line_end_x, line_end_y), 1)
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vth_float(surface, boss, x, y):
        """Idle/moving floating pose."""
        phase = boss.pulse
        _NS_vorthakul._draw_void_wisps(surface, x, y + 30, phase)
        _NS_vorthakul._draw_vth_body(surface, x, y, boss.direction, phase, "float")
    def _draw_vth_attack(surface, boss, x, y):
        """Attack swing pose (melee bite)."""
        progress = getattr(boss, "_vth_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Swing forward (bite lunge)
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction  # rear back
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 20)) * boss.direction  # lunge forward
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(15 * (1 - t)) * boss.direction  # recover
            lift = int(-2 + t * 2)
        _NS_vorthakul._draw_void_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_vorthakul._draw_vth_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
    # ============================================================
    # BODY (Quadruped void terror)
    # ============================================================
    def _draw_vth_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw void terror body: legs, tail, main body, head."""
        # Back spikes (behind)
        _NS_vorthakul._draw_back_spikes(surface, cx, cy - 8, facing, phase)
        # Tail behind
        _NS_vorthakul._draw_void_tail(surface, cx, cy + 2, facing, phase)
        # Rear legs (dangling since floating)
        _NS_vorthakul._draw_dangling_legs(surface, cx, cy, facing, phase)
        # Main body
        _NS_vorthakul._draw_void_body(surface, cx, cy, facing, phase)
        # Front claws (dangling)
        _NS_vorthakul._draw_front_claws(surface, cx, cy, facing, phase)
        # Head with big mouth
        head_lunge = 0
        if action == "attack":
            if attack_progress < 0.35:
                head_lunge = -int(attack_progress / 0.35 * 4) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                head_lunge = int((-4 + t * 18)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(14 * (1 - t)) * facing
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 8)
        _NS_vorthakul._draw_void_head(surface, cx + facing * 20 + head_lunge, cy - 6,
                                       facing, phase, mouth_open)
    def _draw_back_spikes(surface, cx, cy, facing, phase):
        """Large spikes on back (crown of spikes)."""
        spike_configs = [
            (-14, 2, 8),   # (x_off, y_off, height)
            (-9, 0, 12),
            (-4, -2, 14),
            (1, -3, 16),   # tallest
            (6, -2, 14),
            (11, 0, 11),
            (16, 2, 8),
        ]
        for i, (x_off, y_off, h) in enumerate(spike_configs):
            sway = math.sin(phase * 0.5 + i * 0.4) * 1
            spike_x = cx + x_off
            base_y = cy + y_off
            tip_y = base_y - h + int(sway)
            # Shadow
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"], [
                (spike_x + 2, tip_y + 2),
                (spike_x - 3, base_y + 2),
                (spike_x + 3, base_y + 2),
            ])
            # Main spike
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_dark"], [
                (spike_x, tip_y),
                (spike_x - 3, base_y),
                (spike_x + 3, base_y),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_mid"], [
                (spike_x, tip_y),
                (spike_x - 2, base_y),
                (spike_x + 2, base_y),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_light"], [
                (spike_x, tip_y),
                (spike_x - 1, base_y),
                (spike_x + 1, base_y),
            ])
            # Glow tip
            pulse = math.sin(phase * 2 + i * 0.5) * 0.3 + 0.7
            for r in range(3, 0, -1):
                alpha = _NS_vorthakul._alpha(180 * (3 - r) / 3 * pulse)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["spike_glow"], alpha),
                                        (spike_x, tip_y), r)
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_hot"],
                             (spike_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                             (spike_x, tip_y - 1, 1, 1))
    def _draw_void_tail(surface, cx, cy, facing, phase):
        """Curling tail with spike at end."""
        back_dir = -facing
        base_x = cx + back_dir * 15
        base_y = cy + 3
        segments = 7
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (10 + t * 22))
            y_off = int(2 + t * 10 - t * t * 8)
            wave = math.sin(phase * 1.1 + t * math.pi) * (3 + t * 3)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))
        # Draw tail segments
        for i in range(len(points) - 1):
            thickness = max(2, 9 - i)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                                  (points[i][0] + 2, points[i][1] + 2),
                                  (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                  thickness + 1)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_darkest"],
                                  points[i], points[i + 1], thickness)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_dark"],
                                  points[i], points[i + 1], max(1, thickness - 2))
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_mid"],
                                  (points[i][0], points[i][1] - 1),
                                  (points[i + 1][0], points[i + 1][1] - 1),
                                  max(1, thickness - 4))
        # Small spikes along tail
        for i in range(1, len(points) - 1, 2):
            spike_size = max(1, 4 - i // 2)
            spike_x = points[i][0]
            spike_y = points[i][1] - max(1, 5 - i)
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_dark"], [
                (points[i][0] - 2, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 2, points[i][1] - 1),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_mid"], [
                (points[i][0] - 1, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 1, points[i][1] - 1),
            ])
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_hot"],
                             (spike_x, spike_y, 1, 1))
        # Big tail spike at end
        if len(points) >= 2:
            end = points[-1]
            prev = points[-2]
            spike_angle = math.atan2(end[1] - prev[1], end[0] - prev[0])
            spike_len = 12
            spike_tip = (end[0] + int(math.cos(spike_angle) * spike_len),
                         end[1] + int(math.sin(spike_angle) * spike_len))
            perp = spike_angle + math.pi / 2
            base_a = (end[0] + int(math.cos(perp) * 4),
                      end[1] + int(math.sin(perp) * 4))
            base_b = (end[0] - int(math.cos(perp) * 4),
                      end[1] - int(math.sin(perp) * 4))
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"], [
                (spike_tip[0] + 2, spike_tip[1] + 2),
                (base_a[0] + 2, base_a[1] + 2),
                (base_b[0] + 2, base_b[1] + 2),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_dark"],
                                [spike_tip, base_a, base_b])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_mid"], [
                spike_tip,
                (int((spike_tip[0] + base_a[0]) / 2),
                 int((spike_tip[1] + base_a[1]) / 2)),
                end,
            ])
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_dark"], spike_tip, 3)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_light"], spike_tip, 2)
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                             (spike_tip[0], spike_tip[1], 1, 1))
    def _draw_dangling_legs(surface, cx, cy, facing, phase):
        """Rear legs dangling (floating)."""
        sway = math.sin(phase * 0.8) * 2
        for side, x_base in [(-1, -12), (1, -6)]:
            leg_x = cx + x_base
            leg_top_y = cy + 8
            leg_bot_y = cy + 20 + int(sway * side)
            # Leg limb
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                                  (leg_x + 1, leg_top_y + 1),
                                  (leg_x + 1 + int(sway * side), leg_bot_y + 1), 6)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_darkest"],
                                  (leg_x, leg_top_y),
                                  (leg_x + int(sway * side), leg_bot_y), 5)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_dark"],
                                  (leg_x, leg_top_y),
                                  (leg_x + int(sway * side), leg_bot_y), 3)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_mid"],
                                  (leg_x - 1, leg_top_y),
                                  (leg_x - 1 + int(sway * side), leg_bot_y), 1)
            # Claws at end
            claw_x = leg_x + int(sway * side)
            claw_y = leg_bot_y
            for cx_off in (-2, 0, 2):
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["fang_dark"], [
                    (claw_x + cx_off, claw_y),
                    (claw_x + cx_off - 1, claw_y + 3),
                    (claw_x + cx_off + 1, claw_y + 3),
                ])
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_mid"],
                                 (claw_x + cx_off, claw_y + 1, 1, 2))
    def _draw_front_claws(surface, cx, cy, facing, phase):
        """Front claws hanging forward."""
        sway = math.sin(phase * 0.9 + 1) * 2
        for side, x_base in [(-1, 8), (1, 14)]:
            leg_x = cx + x_base * facing
            leg_top_y = cy + 6
            leg_bot_y = cy + 18 + int(sway * side)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                                  (leg_x + 1, leg_top_y + 1),
                                  (leg_x + 1 + int(sway * side), leg_bot_y + 1), 5)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_darkest"],
                                  (leg_x, leg_top_y),
                                  (leg_x + int(sway * side), leg_bot_y), 4)
            _NS_vorthakul._aaline(surface, _NS_vorthakul.PALETTE["void_dark"],
                                  (leg_x, leg_top_y),
                                  (leg_x + int(sway * side), leg_bot_y), 2)
            # Claws
            claw_x = leg_x + int(sway * side)
            claw_y = leg_bot_y
            for cx_off in (-2, 0, 2):
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["fang_dark"], [
                    (claw_x + cx_off, claw_y),
                    (claw_x + cx_off - 1, claw_y + 4),
                    (claw_x + cx_off + 1, claw_y + 4),
                ])
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["fang_mid"], [
                    (claw_x + cx_off, claw_y + 1),
                    (claw_x + cx_off, claw_y + 3),
                    (claw_x + cx_off + 1, claw_y + 3),
                ])
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_light"],
                                 (claw_x + cx_off, claw_y + 3, 1, 1))
    def _draw_void_body(surface, cx, cy, facing, phase):
        """Main body (bulky void torso)."""
        body_shape = [
            (cx - 17, cy),
            (cx - 19, cy - 5),
            (cx - 14, cy - 10),
            (cx - 6, cy - 12),
            (cx + 6, cy - 12),
            (cx + 15, cy - 10),
            (cx + 19, cy - 5),
            (cx + 21, cy + 1),
            (cx + 18, cy + 8),
            (cx + 10, cy + 12),
            (cx - 2, cy + 13),
            (cx - 12, cy + 12),
            (cx - 18, cy + 8),
            (cx - 20, cy + 2),
        ]
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in body_shape])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_darkest"], body_shape)
        # Upper void purple
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_dark"], [
            (cx - 17, cy - 2),
            (cx - 13, cy - 9),
            (cx - 4, cy - 11),
            (cx + 6, cy - 11),
            (cx + 13, cy - 9),
            (cx + 18, cy - 4),
            (cx + 19, cy),
            (cx + 15, cy + 3),
            (cx - 13, cy + 3),
            (cx - 17, cy),
        ])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_mid"], [
            (cx - 13, cy - 3),
            (cx - 10, cy - 7),
            (cx - 2, cy - 9),
            (cx + 6, cy - 9),
            (cx + 10, cy - 7),
            (cx + 14, cy - 3),
            (cx + 12, cy),
            (cx - 8, cy),
        ])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_light"], [
            (cx - 4, cy - 6),
            (cx + 2, cy - 7),
            (cx + 8, cy - 5),
            (cx + 6, cy - 2),
            (cx - 2, cy - 2),
        ])
        # Shine highlight
        pygame.draw.rect(surface, _NS_vorthakul.PALETTE["void_edge"],
                         (cx + 2, cy - 6, 3, 1))
        pygame.draw.rect(surface, _NS_vorthakul.PALETTE["void_shine"],
                         (cx + 3, cy - 6, 1, 1))
        # Belly (chitin plates)
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["belly_dark"], [
            (cx - 13, cy + 3),
            (cx + 13, cy + 3),
            (cx + 18, cy + 6),
            (cx + 10, cy + 12),
            (cx - 2, cy + 13),
            (cx - 12, cy + 12),
            (cx - 18, cy + 6),
        ])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["belly_mid"], [
            (cx - 11, cy + 5),
            (cx + 11, cy + 5),
            (cx + 14, cy + 7),
            (cx + 8, cy + 11),
            (cx - 2, cy + 12),
            (cx - 10, cy + 11),
            (cx - 13, cy + 7),
        ])
        # Chitin plate lines
        for y_off in (5, 8, 11):
            pygame.draw.line(surface, _NS_vorthakul.PALETTE["belly_darkest"],
                             (cx - 10, cy + y_off),
                             (cx + 10, cy + y_off), 1)
        # Scale/texture on back
        for row in range(2):
            y_row = cy - 6 + row * 3
            for dx in (-9, -4, 1, 6, 11):
                offset_x = (row % 2) * 2 - 1
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["void_darkest"],
                                 (cx + dx + offset_x - 1, y_row),
                                 (cx + dx + offset_x, y_row - 1), 1)
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["void_darkest"],
                                 (cx + dx + offset_x, y_row - 1),
                                 (cx + dx + offset_x + 1, y_row), 1)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["void_edge"],
                                 (cx + dx + offset_x, y_row - 1, 1, 1))
    def _draw_void_head(surface, cx, cy, facing, phase, mouth_open):
        """Head with huge mouth full of teeth."""
        # Head shape (compact, wide mouth)
        head_shape = [
            (cx - 10 * facing, cy + 4),
            (cx - 11 * facing, cy - 3),
            (cx - 7 * facing, cy - 10),
            (cx - 1 * facing, cy - 13),
            (cx + 6 * facing, cy - 12),
            (cx + 13 * facing, cy - 8),
            (cx + 17 * facing, cy - 3),
            (cx + 19 * facing, cy + 2),
            (cx + 16 * facing, cy + 7),
            (cx + 8 * facing, cy + 10),
            (cx - 2 * facing, cy + 10),
            (cx - 8 * facing, cy + 8),
        ]
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in head_shape])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_darkest"], head_shape)
        # Upper head void
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_dark"], [
            (cx - 10 * facing, cy + 2),
            (cx - 10 * facing, cy - 2),
            (cx - 6 * facing, cy - 9),
            (cx + 5 * facing, cy - 11),
            (cx + 12 * facing, cy - 7),
            (cx + 16 * facing, cy - 2),
            (cx + 17 * facing, cy + 1),
            (cx + 13 * facing, cy + 1),
            (cx + 5 * facing, cy),
            (cx - 5 * facing, cy + 1),
        ])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_mid"], [
            (cx - 7 * facing, cy - 1),
            (cx - 4 * facing, cy - 8),
            (cx + 5 * facing, cy - 9),
            (cx + 12 * facing, cy - 5),
            (cx + 14 * facing, cy - 1),
            (cx + 5 * facing, cy - 2),
        ])
        _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_light"], [
            (cx - 2 * facing, cy - 5),
            (cx + 4 * facing, cy - 7),
            (cx + 9 * facing, cy - 4),
            (cx + 5 * facing, cy - 2),
        ])
        # Head horns/crest
        _NS_vorthakul._draw_head_crest(surface, cx, cy, facing, phase)
        # Eyes (2 glowing pink eyes)
        _NS_vorthakul._draw_void_eyes(surface, cx, cy, facing, phase)
        # Nostril
        pygame.draw.rect(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                         (cx + 14 * facing, cy - 2, 2, 1))
        # MOUTH with teeth
        _NS_vorthakul._draw_void_mouth(surface, cx, cy, facing, phase, mouth_open)
    def _draw_head_crest(surface, cx, cy, facing, phase):
        """Curved horns on head."""
        for i, (base_off_x, base_off_y, angle_off, length) in enumerate([
            (-4, -9, math.pi * 0.72, 11),
            (-1, -11, math.pi * 0.62, 14),
            (3, -10, math.pi * 0.55, 11),
        ]):
            sway = math.sin(phase * 0.4 + i * 0.4) * 1
            base_x = cx + int(base_off_x * facing)
            base_y = cy + base_off_y
            tip_x = cx + int((base_off_x + math.cos(angle_off) * length * -1) * facing)
            tip_y = base_y - int(math.sin(angle_off) * length) + int(sway)
            perp_x = -math.sin(angle_off)
            perp_y = math.cos(angle_off)
            pa_x = base_x + int(perp_x * 2)
            pa_y = base_y + int(perp_y * 2)
            pb_x = base_x - int(perp_x * 2)
            pb_y = base_y - int(perp_y * 2)
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_dark"],
                                [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            # Glowing tip
            pulse = math.sin(phase * 2 + i * 0.7) * 0.3 + 0.7
            _NS_vorthakul._aacircle(surface, (*_NS_vorthakul.PALETTE["pink_light"],
                                              _NS_vorthakul._alpha(200 * pulse)),
                                    (tip_x, tip_y), 2)
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                             (tip_x, tip_y, 1, 1))
    def _draw_void_eyes(surface, cx, cy, facing, phase):
        """Two glowing pink eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Two eyes on head
        for i, (eye_off_x, eye_off_y) in enumerate([(2, -4), (7, -3)]):
            ex = cx + int(eye_off_x * facing)
            ey = cy + eye_off_y
            # Socket
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 4, 3))
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["eye_socket"],
                             (ex, ey - 1, 3, 3))
            # Glow halo
            for radius in range(5, 0, -1):
                alpha = _NS_vorthakul._alpha(90 * (5 - radius) / 5 * pulse)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["eye_mid"], alpha),
                                        (ex + 1, ey), radius)
            # Iris
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["eye_dark"], (ex, ey, 3, 2))
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["eye_mid"], (ex + 1, ey, 2, 2))
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["eye_light"], (ex + 1, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["eye_glow"], (ex + 2, ey, 1, 1))
    def _draw_void_mouth(surface, cx, cy, facing, phase, mouth_open):
        """Huge mouth with rows of sharp teeth."""
        mouth_y = cy + 3
        mouth_x_start = cx + 1 * facing
        mouth_x_end = cx + 17 * facing
        if mouth_open > 0:
            # Open mouth cavity
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end - 2, mouth_y + int(mouth_open)),
                (mouth_x_start + 2, mouth_y + int(mouth_open * 0.8)),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["eye_darkest"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing * 2, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing * 2, mouth_y + int(mouth_open * 0.8) - 1),
            ])
            # Inner glow (pink void)
            glow_cx = cx + 9 * facing
            glow_cy = mouth_y + int(mouth_open * 0.5)
            glow_r = int(3 + mouth_open * 0.4)
            for r in range(glow_r + 3, 0, -1):
                alpha = _NS_vorthakul._alpha(180 * (glow_r + 3 - r) / (glow_r + 3))
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                        (glow_cx, glow_cy), r)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_mid"],
                                    (glow_cx, glow_cy), max(1, glow_r - 1))
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_light"],
                                    (glow_cx, glow_cy), max(1, glow_r - 3))
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                             (glow_cx, glow_cy, 1, 1))
            # Upper teeth (multiple rows)
            for i, x_off in enumerate((3, 6, 9, 12, 15)):
                fang_x = cx + int(x_off * facing)
                fang_size = 3 if i in (1, 2, 3) else 2
                fang_tip_y = mouth_y + int(mouth_open * 0.7) + fang_size
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y - 1, 1, 1))
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Lower teeth
            for i, x_off in enumerate((4, 7, 10, 13)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 3
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_mid"],
                                 (fang_x, fang_top_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Drool
            if mouth_open > 4:
                for x_off in (5, 11):
                    drip_x = cx + int(x_off * facing)
                    drip_y = mouth_y + int(mouth_open) + 2
                    pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_dark"],
                                     (drip_x, drip_y, 1, 2))
                    pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_light"],
                                     (drip_x, drip_y, 1, 1))
        else:
            # Closed mouth with visible fangs
            pygame.draw.line(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            for x_off in (4, 7, 10, 13):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_mid"],
                                 (fang_x, mouth_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_light"],
                                 (fang_x, mouth_y + 2, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        """Small shadow below floating boss."""
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((120, 28), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, int((12 - radius) * 14 * pulse))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 14 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 2, 8, int(150 * pulse)), (8, 8, 104, 12))
        surface.blit(shadow, (x - 60, y - 14))
    def _draw_void_aura(surface, x, y, phase):
        """Purple void aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_vorthakul._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vorthakul._aacircle(aura,
                                        (*_NS_vorthakul.PALETTE["aura_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_vorthakul._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vorthakul._aacircle(aura,
                                        (*_NS_vorthakul.PALETTE["aura_mid"], alpha),
                                        (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_vorthakul._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vorthakul._aacircle(aura,
                                        (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating void particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_vorthakul.PALETTE["void_light"] if i % 2 == 0 \
                else _NS_vorthakul.PALETTE["pink_mid"]
            hot_color = _NS_vorthakul.PALETTE["void_edge"] if i % 2 == 0 \
                else _NS_vorthakul.PALETTE["pink_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_void_wisps(surface, cx, cy, phase, intense=False):
        """Rising void wisps under floating boss."""
        strength = 1.5 if intense else 1.0
        # Rising purple wisps
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_vorthakul._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["aura_dark"], alpha),
                                    (sx, sy), 3)
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["aura_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Pink sparkles
        for i in range(8):
            spark_t = (phase * 0.6 + i * 0.15) % 1.0
            ex = cx - 26 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(spark_t * 22)
            alpha = _NS_vorthakul._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                                 (ex, ey, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with void runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vorthakul.PALETTE["aura_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_vorthakul.PALETTE["void_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_vorthakul.PALETTE["void_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_vorthakul.PALETTE["pink_dark"], 180),
                            (40, 24, 90, 14), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vorthakul.PALETTE["pink_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vorthakul.PALETTE["pink_hot"],
                                       _NS_vorthakul._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL: Q - RUPTURE (ground spikes burst)
    # ============================================================
    def _draw_rupture_ground(surface, boss, x, y, timer, phase):
        """Warning circle on ground before spikes burst."""
        tx, ty = _NS_vorthakul._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            t = progress / 0.5
            r = int(25 * t)
            alpha = _NS_vorthakul._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_vorthakul.PALETTE["pink_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 1)
    def _draw_rupture_foreground(surface, boss, x, y, timer, phase):
        """Pink spikes burst up from ground."""
        tx, ty = _NS_vorthakul._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            return
        t = (progress - 0.5) / 0.5
        # Multiple spikes burst
        num_spikes = 7
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes
            radius = 8 + (i % 3) * 6
            sx = tx + int(math.cos(angle) * radius)
            sy = ty + int(math.sin(angle) * radius * 0.4)
            # Spike height animates: shoots up then slowly falls
            if t < 0.3:
                spike_h = int((t / 0.3) * 25)
            else:
                spike_h = int(25 * (1 - (t - 0.3) / 0.7 * 0.3))
            spike_h = max(3, spike_h)
            # Draw spike (pointed upward)
            tip_x = sx
            tip_y = sy - spike_h
            base_a = (sx - 3, sy)
            base_b = (sx + 3, sy)
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                                [(tip_x + 1, tip_y + 1),
                                 (base_a[0] + 1, base_a[1] + 1),
                                 (base_b[0] + 1, base_b[1] + 1)])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_dark"],
                                [(tip_x, tip_y), base_a, base_b])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_mid"],
                                [(tip_x, tip_y),
                                 (sx - 2, sy - 1),
                                 (sx + 2, sy - 1)])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_light"],
                                [(tip_x, tip_y),
                                 (sx - 1, sy - spike_h // 2),
                                 (sx + 1, sy - spike_h // 2)])
            # Glowing tip
            for r in range(3, 0, -1):
                alpha = _NS_vorthakul._alpha(200 * (3 - r) / 3)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                                        (tip_x, tip_y), r)
            pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                             (tip_x, tip_y, 1, 1))
        # Center burst
        if t < 0.5:
            burst_r = int(5 + t * 20)
            alpha = _NS_vorthakul._alpha(240 * (1 - t * 2))
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                    (tx, ty), burst_r, 2)
            _NS_vorthakul._aacircle(surface,
                                    (*_NS_vorthakul.PALETTE["pink_shine"], alpha),
                                    (tx, ty), burst_r // 2)
    # ============================================================
    # SKILL: W - FERAL SCREAM (fear AoE)
    # ============================================================
    def _draw_scream_ground(surface, boss, x, y, timer, pulse):
        """Ground shockwave from scream."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple expanding rings
        for i in range(3):
            ring_t = max(0.0, progress - i * 0.15)
            r = int(ring_t * 90)
            if r > 5:
                alpha = _NS_vorthakul._alpha(200 * (1 - ring_t))
                pygame.draw.ellipse(surface,
                                    (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_vorthakul.PALETTE["pink_mid"], alpha),
                                    (x - r + 3, y + 40 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                    (x - r + 6, y + 40 - r // 3 + 4,
                                     r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_scream_foreground(surface, boss, x, y, timer, pulse):
        """Scream wave FX in air."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Sonic wave arcs in front of mouth
        mouth_x = x + facing * 28
        mouth_y = y - 6
        for i in range(4):
            wave_t = max(0.0, progress - i * 0.12)
            if wave_t <= 0:
                continue
            wave_dist = int(wave_t * 100)
            wave_r = int(15 + wave_t * 25)
            wave_x = mouth_x + facing * wave_dist
            wave_y = mouth_y
            alpha = _NS_vorthakul._alpha(230 * (1 - wave_t))
            # Arc wave
            for arc_r in range(wave_r, wave_r - 4, -1):
                if arc_r < 2:
                    continue
                # Draw arc as multiple points
                for a_step in range(-30, 31, 3):
                    angle = math.radians(a_step)
                    ax = wave_x + int(math.cos(angle) * arc_r) * facing
                    ay = wave_y + int(math.sin(angle) * arc_r)
                    pygame.draw.rect(surface,
                                     (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                     (ax, ay, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                                     (ax, ay, 1, 1))
            # Wave particles
            for p in range(6):
                pa = math.radians(-30 + p * 12)
                px = wave_x + int(math.cos(pa) * wave_r) * facing
                py = wave_y + int(math.sin(pa) * wave_r)
                pygame.draw.rect(surface,
                                 (*_NS_vorthakul.PALETTE["pink_shine"], alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: E - VOID SPIKES (projectile volley)
    # ============================================================
    def _draw_voidspikes_foreground(surface, boss, x, y, timer, pulse):
        """Volley of spike projectiles."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vorthakul._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in mouth
            t = progress / 0.2
            mouth_x = x + facing * 28
            mouth_y = y - 6
            for r in range(int(6 * t) + 4, 0, -1):
                alpha = _NS_vorthakul._alpha(200 * (int(6 * t) + 4 - r)
                                             / max(1, int(6 * t) + 4))
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                        (mouth_x, mouth_y), r)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_light"],
                                    (mouth_x, mouth_y), max(1, int(4 * t)))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 32
            start_y = y - 6
            # 3 spike projectiles with slight vertical offset
            for spike_i, y_offset in enumerate((-8, 0, 8)):
                delay = spike_i * 0.1
                spike_t = max(0.0, min(1.0, (t - delay) / (1 - delay)))
                if spike_t <= 0:
                    continue
                target_y = ty + y_offset
                bx = int(start_x + (tx - start_x) * spike_t)
                by = int(start_y + (target_y - start_y) * spike_t)
                # Direction angle
                angle = math.atan2(target_y - start_y, tx - start_x)
                # Draw spike shape (elongated)
                length = 14
                tip_x = bx + int(math.cos(angle) * length / 2)
                tip_y = by + int(math.sin(angle) * length / 2)
                back_x = bx - int(math.cos(angle) * length / 2)
                back_y = by - int(math.sin(angle) * length / 2)
                # Perpendicular for width
                perp_angle = angle + math.pi / 2
                perp_x = math.cos(perp_angle) * 3
                perp_y = math.sin(perp_angle) * 3
                # Trail
                for i in range(5):
                    trail_t = max(0.0, spike_t - i * 0.05)
                    tpx = int(start_x + (tx - start_x) * trail_t)
                    tpy = int(start_y + (target_y - start_y) * trail_t)
                    alpha = _NS_vorthakul._alpha(200 - i * 35)
                    size = max(1, 4 - i)
                    _NS_vorthakul._aacircle(surface,
                                            (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                            (tpx, tpy), size)
                    _NS_vorthakul._aacircle(surface,
                                            (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                            (tpx, tpy), max(1, size - 1))
                # Spike body
                spike_points = [
                    (tip_x, tip_y),
                    (int(back_x + perp_x), int(back_y + perp_y)),
                    (int(back_x - perp_x), int(back_y - perp_y)),
                ]
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"],
                                    [(p[0] + 1, p[1] + 1) for p in spike_points])
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_dark"],
                                    spike_points)
                # Inner
                inner_pts = [
                    (tip_x, tip_y),
                    (int(back_x + perp_x * 0.6), int(back_y + perp_y * 0.6)),
                    (int(back_x - perp_x * 0.6), int(back_y - perp_y * 0.6)),
                ]
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["spike_mid"],
                                    inner_pts)
                _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["pink_light"], [
                    (tip_x, tip_y),
                    (int(back_x + perp_x * 0.3), int(back_y + perp_y * 0.3)),
                    (int(back_x - perp_x * 0.3), int(back_y - perp_y * 0.3)),
                ])
                # Bright tip
                _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_hot"],
                                        (tip_x, tip_y), 2)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["pink_shine"],
                                 (tip_x, tip_y, 1, 1))
                # Impact
                if spike_t > 0.9:
                    st = (spike_t - 0.9) / 0.1
                    impact_r = int(4 + st * 10)
                    alpha = _NS_vorthakul._alpha(240 * (1 - st))
                    _NS_vorthakul._aacircle(surface,
                                            (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                            (tx, target_y), impact_r, 2)
                    _NS_vorthakul._aacircle(surface,
                                            (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                                            (tx, target_y), max(1, impact_r // 2))
    # ============================================================
    # SKILL: R - FEAST (huge devour bite)
    # ============================================================
    def _draw_feast_ground(surface, boss, x, y, timer, pulse):
        """Marking circle on target."""
        tx, ty = _NS_vorthakul._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(30 + math.sin(pulse * 3) * 5)
        alpha = _NS_vorthakul._alpha(220 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface, (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_vorthakul.PALETTE["pink_mid"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                            (tx - r + 6, ty - r // 3 + 4,
                             r * 2 - 12, r * 2 // 3 - 8), 1)
        # Runes around
        for i in range(8):
            angle = pulse * 0.5 + i * math.pi / 4
            rx = tx + int(math.cos(angle) * r)
            ry = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                             (rx, ry, 2, 2))
    def _draw_feast_foreground(surface, boss, x, y, timer, pulse):
        """Massive jaw appears and bites down."""
        tx, ty = _NS_vorthakul._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind-up: massive shadow gathers above target
            t = progress / 0.3
            for r in range(int(30 * t), 0, -3):
                alpha = _NS_vorthakul._alpha(180 * t * (30 * t - r) / max(1, 30 * t))
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["void_darkest"], alpha),
                                        (tx, ty - 40), r)
        elif progress < 0.7:
            # Bite: massive jaws close on target
            t = (progress - 0.3) / 0.4
            jaw_open = int((1 - t) * 40 + 5)
            # Upper jaw
            upper_y = ty - jaw_open
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"], [
                (tx - 42, upper_y - 20),
                (tx + 42, upper_y - 20),
                (tx + 35, upper_y),
                (tx - 35, upper_y),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_darkest"], [
                (tx - 40, upper_y - 18),
                (tx + 40, upper_y - 18),
                (tx + 32, upper_y - 2),
                (tx - 32, upper_y - 2),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_dark"], [
                (tx - 36, upper_y - 15),
                (tx + 36, upper_y - 15),
                (tx + 30, upper_y - 4),
                (tx - 30, upper_y - 4),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_mid"], [
                (tx - 30, upper_y - 12),
                (tx + 30, upper_y - 12),
                (tx + 26, upper_y - 6),
                (tx - 26, upper_y - 6),
            ])
            # Upper teeth
            for i, tx_off in enumerate((-28, -20, -12, -4, 4, 12, 20, 28)):
                fang_x = tx + tx_off
                fang_size = 5 if abs(tx_off) < 16 else 4
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_dark"],
                                 (fang_x, upper_y - 2),
                                 (fang_x, upper_y + fang_size), 2)
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_mid"],
                                 (fang_x, upper_y - 2),
                                 (fang_x, upper_y + fang_size), 1)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_light"],
                                 (fang_x, upper_y + fang_size, 1, 1))
            # Lower jaw
            lower_y = ty + jaw_open
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["shadow_deep"], [
                (tx - 35, lower_y),
                (tx + 35, lower_y),
                (tx + 42, lower_y + 20),
                (tx - 42, lower_y + 20),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_darkest"], [
                (tx - 32, lower_y + 2),
                (tx + 32, lower_y + 2),
                (tx + 40, lower_y + 18),
                (tx - 40, lower_y + 18),
            ])
            _NS_vorthakul._poly(surface, _NS_vorthakul.PALETTE["void_dark"], [
                (tx - 30, lower_y + 4),
                (tx + 30, lower_y + 4),
                (tx + 36, lower_y + 15),
                (tx - 36, lower_y + 15),
            ])
            # Lower teeth
            for i, tx_off in enumerate((-26, -18, -10, -2, 6, 14, 22)):
                fang_x = tx + tx_off
                fang_size = 5 if abs(tx_off) < 16 else 4
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_dark"],
                                 (fang_x, lower_y + 2),
                                 (fang_x, lower_y - fang_size), 2)
                pygame.draw.line(surface, _NS_vorthakul.PALETTE["fang_mid"],
                                 (fang_x, lower_y + 2),
                                 (fang_x, lower_y - fang_size), 1)
                pygame.draw.rect(surface, _NS_vorthakul.PALETTE["fang_light"],
                                 (fang_x, lower_y - fang_size, 1, 1))
            # Pink void glow inside mouth
            for r in range(15, 0, -2):
                alpha = _NS_vorthakul._alpha(180 * (15 - r) / 15)
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_dark"], alpha),
                                        (tx, ty), r)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_light"],
                                    (tx, ty), 5)
            _NS_vorthakul._aacircle(surface, _NS_vorthakul.PALETTE["pink_shine"],
                                    (tx, ty), 2)
        else:
            # Aftermath: chomp effect
            t = (progress - 0.7) / 0.3
            for r in range(int(35 * (1 - t)), 0, -3):
                alpha = _NS_vorthakul._alpha(200 * (1 - t))
                _NS_vorthakul._aacircle(surface,
                                        (*_NS_vorthakul.PALETTE["pink_hot"], alpha),
                                        (tx, ty), r, 2)
            # Particles
            for i in range(12):
                angle = i * math.pi / 6
                pt = t * 40
                px = tx + int(math.cos(angle) * pt)
                py = ty + int(math.sin(angle) * pt * 0.7)
                alpha = _NS_vorthakul._alpha(240 * (1 - t))
                pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_light"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_vorthakul.PALETTE["pink_shine"], alpha),
                                 (px, py, 1, 1))



# ====================================================================
# XAELMORAN (ELEMENTAL WEAVER) - TRUE BOSS
# ====================================================================

class _NS_xaelmoran:
    """Namespace xaelmoran - Elemental Weaver boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Robe purple-gold (main)
        "robe_darkest": (15, 8, 25),
        "robe_dark": (40, 22, 60),
        "robe_mid": (75, 45, 105),
        "robe_light": (120, 85, 160),
        "robe_edge": (170, 130, 210),
        # Gold trim
        "gold_dark": (85, 55, 15),
        "gold_mid": (170, 125, 40),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 170),
        # Skin (pale mage)
        "skin_dark": (140, 105, 90),
        "skin_mid": (200, 165, 145),
        "skin_light": (235, 210, 190),
        "skin_shine": (255, 240, 225),
        # Hair (blonde)
        "hair_dark": (110, 75, 25),
        "hair_mid": (180, 135, 60),
        "hair_light": (240, 210, 130),
        "hair_shine": (255, 245, 200),
        # Cold (Quas) - blue
        "cold_darkest": (5, 15, 40),
        "cold_dark": (20, 60, 130),
        "cold_mid": (60, 140, 230),
        "cold_light": (140, 210, 255),
        "cold_hot": (200, 240, 255),
        "cold_shine": (240, 255, 255),
        # Magic (Wex) - purple/magenta
        "magic_darkest": (25, 5, 40),
        "magic_dark": (80, 20, 130),
        "magic_mid": (170, 60, 220),
        "magic_light": (220, 140, 255),
        "magic_hot": (240, 190, 255),
        "magic_shine": (255, 230, 255),
        # Fire (Exort) - orange/red
        "fire_darkest": (40, 10, 5),
        "fire_dark": (140, 45, 10),
        "fire_mid": (240, 110, 30),
        "fire_light": (255, 180, 80),
        "fire_hot": (255, 220, 130),
        "fire_shine": (255, 250, 210),
        # Invoke (yellow/gold arcane)
        "invoke_darkest": (40, 25, 5),
        "invoke_dark": (130, 90, 20),
        "invoke_mid": (230, 180, 50),
        "invoke_light": (255, 225, 130),
        "invoke_shine": (255, 250, 200),
        # Eyes (glowing white/gold)
        "eye_socket": (15, 8, 20),
        "eye_glow": (255, 240, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xaelmoran._clamp(color)
        if _NS_xaelmoran.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xaelmoran._clamp(color)
        if _NS_xaelmoran.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xaelmoran._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xaelmoran(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_xaelmoran._update_xlm_attack_anim(boss)
        attacking = (
            getattr(boss, "_xlm_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Floating bob
        float_bob = math.sin(pulse * 0.6) * 5
        y_floating = y - 10 + int(float_bob)
        # Ambient
        _NS_xaelmoran._draw_arcane_aura(surface, x, y_floating, pulse)
        _NS_xaelmoran._draw_ground_circle(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "r":
            _NS_xaelmoran._draw_invoke_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating shadow
        _NS_xaelmoran._draw_floating_shadow(surface, x, y + 52, pulse)
        # Robe wisps
        _NS_xaelmoran._draw_robe_wisps(surface, x, y_floating + 20, pulse,
                                        intense=attacking)
        # Body
        _NS_xaelmoran._draw_magus_body(surface, x, y_floating, boss.direction,
                                        pulse, "attack" if attacking else "idle",
                                        getattr(boss, "_xlm_attack_progress", 0.0))
        # Orbiting elemental orbs (always visible)
        _NS_xaelmoran._draw_element_orbs(surface, x, y_floating - 5, pulse,
                                          active_skill)
        # Basic attack projectile / skill FX
        if attacking and not active_skill:
            _NS_xaelmoran._draw_basic_attack_fx(surface, boss, x, y_floating)
        if active_skill == "q":
            _NS_xaelmoran._draw_quas_beam(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xaelmoran._draw_wex_beam(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xaelmoran._draw_exort_beam(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xaelmoran._draw_invoke_foreground(surface, boss, x, y_floating, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE (FIXED)
    # ============================================================
    def _update_xlm_attack_anim(boss):
        """Track attack animation - triggers on cooldown reset."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xlm_previous_timer", timer))
        active = bool(getattr(boss, "_xlm_attack_active", False))
        # Trigger: timer just reset (was high, now low) OR timer near max
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._xlm_attack_active = True
            boss._xlm_attack_frame = 0
            active = True
        if active:
            boss._xlm_attack_frame = int(getattr(boss, "_xlm_attack_frame", 0)) + 1
            # Attack animation lasts ~30 frames
            attack_duration = 30
            if boss._xlm_attack_frame >= attack_duration:
                boss._xlm_attack_active = False
                boss._xlm_attack_frame = 0
                active = False
        boss._xlm_previous_timer = timer
        if active:
            attack_duration = 30
            boss._xlm_attack_progress = min(1.0,
                boss._xlm_attack_frame / attack_duration)
        else:
            boss._xlm_attack_progress = 0.0
    # ============================================================
    # ENTRY POINT (FIXED)
    # ============================================================
    def draw_xaelmoran(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_xaelmoran._update_xlm_attack_anim(boss)
        # Attacking = animation is playing
        attacking = bool(getattr(boss, "_xlm_attack_active", False))
        # Floating bob
        float_bob = math.sin(pulse * 0.6) * 5
        y_floating = y - 10 + int(float_bob)
        # Ambient
        _NS_xaelmoran._draw_arcane_aura(surface, x, y_floating, pulse)
        _NS_xaelmoran._draw_ground_circle(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "r":
            _NS_xaelmoran._draw_invoke_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating shadow
        _NS_xaelmoran._draw_floating_shadow(surface, x, y + 52, pulse)
        # Robe wisps
        _NS_xaelmoran._draw_robe_wisps(surface, x, y_floating + 20, pulse,
                                        intense=attacking)
        # Body
        _NS_xaelmoran._draw_magus_body(surface, x, y_floating, boss.direction,
                                        pulse, "attack" if attacking else "idle",
                                        getattr(boss, "_xlm_attack_progress", 0.0))
        # Orbiting elemental orbs (always visible)
        _NS_xaelmoran._draw_element_orbs(surface, x, y_floating - 5, pulse,
                                          active_skill)
        # >>> BASIC ATTACK PROJECTILE (only when no skill active) <<<
        if attacking and not active_skill:
            _NS_xaelmoran._draw_basic_attack_fx(surface, boss, x, y_floating)
        # Skill projectiles
        if active_skill == "q":
            _NS_xaelmoran._draw_quas_beam(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xaelmoran._draw_wex_beam(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xaelmoran._draw_exort_beam(surface, boss, x, y_floating, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xaelmoran._draw_invoke_foreground(surface, boss, x, y_floating, skill_timer, pulse)
    # ============================================================
    # BODY (Humanoid Magus)
    # ============================================================
    def _draw_magus_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw magus body: robe, torso, arms, head."""
        # Robe (bottom, flowing)
        _NS_xaelmoran._draw_robe(surface, cx, cy + 12, facing, phase)
        # Torso
        _NS_xaelmoran._draw_torso(surface, cx, cy, facing, phase)
        # Arms (raised for casting)
        raise_amount = 0
        if action == "attack":
            raise_amount = int(math.sin(attack_progress * math.pi) * 6)
        _NS_xaelmoran._draw_arms(surface, cx, cy, facing, phase, raise_amount,
                                  action, attack_progress)
        # Head
        _NS_xaelmoran._draw_head(surface, cx, cy - 20, facing, phase)
        # Collar/shoulder pads (over torso)
        _NS_xaelmoran._draw_collar(surface, cx, cy - 8, facing, phase)
    def _draw_robe(surface, cx, cy, facing, phase):
        """Flowing robe bottom."""
        sway = math.sin(phase * 0.7) * 2
        # Robe outer shape (trapezoidal, flowing)
        robe_points = [
            (cx - 12, cy - 12),  # top left
            (cx + 12, cy - 12),  # top right
            (cx + 18 + int(sway), cy + 8),   # bottom right (flare)
            (cx + 14 + int(sway * 0.5), cy + 14),
            (cx + 4, cy + 16),
            (cx - 4, cy + 16),
            (cx - 14 - int(sway * 0.5), cy + 14),
            (cx - 18 - int(sway), cy + 8),  # bottom left
        ]
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in robe_points])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_darkest"], robe_points)
        # Middle shade
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_dark"], [
            (cx - 11, cy - 10),
            (cx + 11, cy - 10),
            (cx + 16, cy + 6),
            (cx + 12, cy + 12),
            (cx + 3, cy + 14),
            (cx - 3, cy + 14),
            (cx - 12, cy + 12),
            (cx - 16, cy + 6),
        ])
        # Highlight
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_mid"], [
            (cx - 8, cy - 8),
            (cx + 8, cy - 8),
            (cx + 12, cy + 4),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 12, cy + 4),
        ])
        # Center highlight
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_light"], [
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 4, cy + 8),
            (cx - 4, cy + 8),
        ])
        # Gold trim along bottom edge
        for i in range(-16, 17, 2):
            trim_x = cx + i
            trim_y = cy + 14 + int(math.sin(i * 0.3) * 1)
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_dark"],
                             (trim_x, trim_y, 2, 2))
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_mid"],
                             (trim_x, trim_y, 1, 1))
        # Gold vertical stripe (center)
        pygame.draw.line(surface, _NS_xaelmoran.PALETTE["gold_dark"],
                         (cx, cy - 10), (cx, cy + 14), 2)
        pygame.draw.line(surface, _NS_xaelmoran.PALETTE["gold_mid"],
                         (cx, cy - 10), (cx, cy + 14), 1)
        # Gold diamond ornaments
        for oy in (-4, 4):
            pygame.draw.polygon(surface, _NS_xaelmoran.PALETTE["gold_light"], [
                (cx, cy + oy - 2), (cx + 2, cy + oy),
                (cx, cy + oy + 2), (cx - 2, cy + oy),
            ])
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_shine"],
                             (cx, cy + oy, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Upper body torso."""
        torso_points = [
            (cx - 10, cy - 8),
            (cx - 11, cy - 2),
            (cx - 10, cy + 4),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 10, cy + 4),
            (cx + 11, cy - 2),
            (cx + 10, cy - 8),
        ]
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_points])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_darkest"], torso_points)
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_dark"], [
            (cx - 9, cy - 7),
            (cx - 10, cy - 2),
            (cx - 9, cy + 3),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 9, cy + 3),
            (cx + 10, cy - 2),
            (cx + 9, cy - 7),
        ])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_mid"], [
            (cx - 6, cy - 5),
            (cx - 7, cy + 2),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 7, cy + 2),
            (cx + 6, cy - 5),
        ])
        # Center chest highlight
        pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["robe_light"],
                         (cx - 2, cy - 4, 4, 8))
        # Gold center emblem (arcane symbol)
        pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_mid"],
                         (cx - 3, cy, 6, 3))
        pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_light"],
                         (cx - 2, cy, 4, 2))
        pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_shine"],
                         (cx - 1, cy, 2, 1))
        # Belt line
        pygame.draw.line(surface, _NS_xaelmoran.PALETTE["gold_dark"],
                         (cx - 9, cy + 6), (cx + 9, cy + 6), 1)
        pygame.draw.line(surface, _NS_xaelmoran.PALETTE["gold_mid"],
                         (cx - 8, cy + 6), (cx + 8, cy + 6), 1)
    def _draw_collar(surface, cx, cy, facing, phase):
        """High collar/shoulder pads."""
        # High collar behind head
        collar_points = [
            (cx - 12, cy),
            (cx - 14, cy - 8),
            (cx - 10, cy - 12),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 10, cy - 12),
            (cx + 14, cy - 8),
            (cx + 12, cy),
        ]
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in collar_points])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_darkest"], collar_points)
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_dark"], [
            (cx - 11, cy - 1),
            (cx - 13, cy - 7),
            (cx - 9, cy - 11),
            (cx + 9, cy - 11),
            (cx + 13, cy - 7),
            (cx + 11, cy - 1),
        ])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["robe_mid"], [
            (cx - 9, cy - 2),
            (cx - 11, cy - 6),
            (cx - 7, cy - 9),
            (cx + 7, cy - 9),
            (cx + 11, cy - 6),
            (cx + 9, cy - 2),
        ])
        # Gold trim on collar edges
        for side in (-1, 1):
            for i in range(3):
                tx = cx + side * (10 + i)
                ty = cy - 8 - i
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_mid"],
                                 (tx, ty, 1, 2))
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_light"],
                                 (tx, ty, 1, 1))
        # Shoulder gem (glowing)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            gx = cx + side * 9
            gy = cy - 2
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_dark"],
                                    (gx, gy), 3)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_mid"],
                                    (gx, gy), 2)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE["invoke_light"],
                                     _NS_xaelmoran._alpha(255 * pulse)),
                                    (gx, gy), 1)
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["invoke_shine"],
                             (gx, gy, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, raise_amount, action,
                    attack_progress):
        """Arms with hands, raised for casting."""
        # Base arm positions
        # Idle: arms slightly out
        # Attack: arms raised forward
        base_y = cy - 4
        hand_offset_y = -raise_amount
        # Left arm
        l_shoulder = (cx - 10, base_y)
        l_hand = (cx - 12 - int(math.sin(phase * 0.6) * 1),
                  base_y + 8 + hand_offset_y)
        if action == "attack":
            # Raise forward
            l_hand = (cx - 6 - facing * int(attack_progress * 4),
                      base_y - 2 - raise_amount)
        # Right arm (facing side, more prominent)
        r_shoulder = (cx + 10, base_y)
        r_hand = (cx + 12 + int(math.sin(phase * 0.6 + 1) * 1),
                  base_y + 8 + hand_offset_y)
        if action == "attack":
            r_hand = (cx + 6 + facing * int(attack_progress * 6),
                      base_y - 2 - raise_amount)
        # Draw both arms
        for shoulder, hand in [(l_shoulder, l_hand), (r_shoulder, r_hand)]:
            # Elbow midpoint (bent)
            mx = int((shoulder[0] + hand[0]) / 2)
            my = int((shoulder[1] + hand[1]) / 2) + 2
            # Upper arm
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["shadow_deep"],
                                  (shoulder[0] + 1, shoulder[1] + 1),
                                  (mx + 1, my + 1), 5)
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["robe_darkest"],
                                  shoulder, (mx, my), 5)
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["robe_dark"],
                                  shoulder, (mx, my), 3)
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["robe_mid"],
                                  (shoulder[0] - 1, shoulder[1]),
                                  (mx - 1, my), 1)
            # Forearm
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["shadow_deep"],
                                  (mx + 1, my + 1),
                                  (hand[0] + 1, hand[1] + 1), 4)
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["robe_darkest"],
                                  (mx, my), hand, 4)
            _NS_xaelmoran._aaline(surface, _NS_xaelmoran.PALETTE["robe_dark"],
                                  (mx, my), hand, 2)
            # Hand (skin)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["shadow_deep"],
                                    (hand[0] + 1, hand[1] + 1), 3)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["skin_dark"],
                                    hand, 3)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["skin_mid"],
                                    hand, 2)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["skin_light"],
                                    (hand[0], hand[1] - 1), 1)
            # Gold cuff at wrist
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_dark"],
                             (hand[0] - 2, hand[1] + 1, 4, 2))
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_mid"],
                             (hand[0] - 2, hand[1] + 1, 4, 1))
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["gold_shine"],
                             (hand[0], hand[1] + 1, 1, 1))
            # Casting glow at hand during attack
            if action == "attack":
                for r in range(4, 0, -1):
                    alpha = _NS_xaelmoran._alpha(180 * (4 - r) / 4
                                                  * attack_progress)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE["invoke_light"],
                                             alpha),
                                            hand, r)
    def _draw_head(surface, cx, cy, facing, phase):
        """Head with pale skin, blonde hair, glowing eyes."""
        # Hair back (flowing)
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["shadow_deep"], [
            (cx - 8, cy - 4),
            (cx - 10, cy + 4),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 10, cy + 4),
            (cx + 8, cy - 4),
        ])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["hair_dark"], [
            (cx - 7, cy - 3),
            (cx - 9, cy + 3),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 9, cy + 3),
            (cx + 7, cy - 3),
        ])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["hair_mid"], [
            (cx - 6, cy - 2),
            (cx - 8, cy + 3),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 8, cy + 3),
            (cx + 6, cy - 2),
        ])
        # Face (skin oval)
        face_points = [
            (cx - 5, cy - 2),
            (cx - 6, cy + 2),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 2),
        ]
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["skin_dark"], face_points)
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["skin_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy + 2),
            (cx - 4, cy + 5),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 4, cy + 5),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
        ])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["skin_light"], [
            (cx - 2, cy),
            (cx - 3, cy + 3),
            (cx - 1, cy + 5),
            (cx + 1, cy + 5),
            (cx + 3, cy + 3),
            (cx + 2, cy),
        ])
        # Front hair (bangs)
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["hair_dark"], [
            (cx - 6, cy - 2),
            (cx - 5, cy + 1),
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 5, cy + 1),
            (cx + 6, cy - 2),
        ])
        _NS_xaelmoran._poly(surface, _NS_xaelmoran.PALETTE["hair_mid"], [
            (cx - 5, cy - 1),
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 5, cy - 1),
        ])
        # Hair highlights
        pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["hair_light"],
                         (cx - 3, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["hair_shine"],
                         (cx + 2, cy - 1, 1, 1))
        # Glowing eyes (white/gold)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            # Socket
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["eye_socket"],
                             (eye_x, cy + 2, 2, 2))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_xaelmoran._alpha(200 * (3 - r) / 3 * pulse)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["eye_glow"],
                                         alpha),
                                        (eye_x, cy + 3), r)
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["white"],
                             (eye_x, cy + 3, 1, 1))
        # Long hair down (side strands)
        for side in (-1, 1):
            for i in range(3):
                strand_x = cx + side * (5 + i)
                strand_y_top = cy + 3 + i * 2
                strand_y_bot = cy + 12 + i * 2
                pygame.draw.line(surface, _NS_xaelmoran.PALETTE["hair_dark"],
                                 (strand_x, strand_y_top),
                                 (strand_x - side, strand_y_bot), 2)
                pygame.draw.line(surface, _NS_xaelmoran.PALETTE["hair_mid"],
                                 (strand_x, strand_y_top),
                                 (strand_x - side, strand_y_bot), 1)
    # ============================================================
    # ORBITING ELEMENTAL ORBS (Quas, Wex, Exort)
    # ============================================================
    def _draw_element_orbs(surface, cx, cy, phase, active_skill):
        """3 elemental orbs orbiting around magus."""
        # Highlighted orb (based on active skill)
        highlight = None
        if active_skill == "q":
            highlight = "cold"
        elif active_skill == "w":
            highlight = "magic"
        elif active_skill == "e":
            highlight = "fire"
        elif active_skill == "r":
            highlight = "all"
        orbs = [
            ("cold", 0, ["cold_dark", "cold_mid", "cold_light", "cold_hot",
                         "cold_shine"]),
            ("magic", math.pi * 2 / 3, ["magic_dark", "magic_mid", "magic_light",
                                         "magic_hot", "magic_shine"]),
            ("fire", math.pi * 4 / 3, ["fire_dark", "fire_mid", "fire_light",
                                        "fire_hot", "fire_shine"]),
        ]
        for name, angle_off, colors in orbs:
            angle = phase * 0.8 + angle_off
            orbit_r = 22
            # Elliptical orbit
            ox = cx + int(math.cos(angle) * orbit_r)
            oy = cy + int(math.sin(angle) * orbit_r * 0.5) - 8
            is_hot = (highlight == name or highlight == "all")
            size_mult = 1.3 if is_hot else 1.0
            base_r = int(4 * size_mult)
            # Outer glow
            for r in range(int(base_r + 5), 0, -1):
                alpha = _NS_xaelmoran._alpha(150 * (base_r + 5 - r)
                                              / (base_r + 5))
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[colors[0]], alpha),
                                        (ox, oy), r)
            # Orb layers (dark to bright)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[colors[0]],
                                    (ox, oy), base_r)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[colors[1]],
                                    (ox, oy), max(1, base_r - 1))
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[colors[2]],
                                    (ox, oy), max(1, base_r - 2))
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[colors[3]],
                                    (ox, oy), max(1, base_r - 3))
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[colors[4]],
                             (ox, oy, 1, 1))
            # Rune ring around orb (arcane circle)
            ring_r = base_r + 3
            for i in range(8):
                rune_a = phase * 2 + i * math.pi / 4
                rx = ox + int(math.cos(rune_a) * ring_r)
                ry = oy + int(math.sin(rune_a) * ring_r)
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[colors[3]],
                                 (rx, ry, 1, 1))
            # Sparkles orbiting orb
            for s in range(3):
                sp_a = phase * 4 + s * math.pi * 2 / 3
                sp_r = base_r + 2
                sx = ox + int(math.cos(sp_a) * sp_r)
                sy = oy + int(math.sin(sp_a) * sp_r)
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[colors[4]],
                                 (sx, sy, 1, 1))
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
        pygame.draw.ellipse(shadow, (5, 3, 10, int(150 * pulse)), (8, 8, 104, 12))
        surface.blit(shadow, (x - 60, y - 14))
    def _draw_arcane_aura(surface, x, y, phase):
        """Purple-gold arcane aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_xaelmoran._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_xaelmoran._aacircle(aura,
                                        (*_NS_xaelmoran.PALETTE["robe_dark"], alpha),
                                        (110, 100), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_xaelmoran._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xaelmoran._aacircle(aura,
                                        (*_NS_xaelmoran.PALETTE["invoke_dark"], alpha),
                                        (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating particles (mixed elemental)
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            color_key = ["cold_mid", "magic_mid", "fire_mid", "invoke_mid"][i % 4]
            hot_key = ["cold_hot", "magic_hot", "fire_hot", "invoke_shine"][i % 4]
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[color_key],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[hot_key],
                             (sx, sy, 1, 1))
    def _draw_robe_wisps(surface, cx, cy, phase, intense=False):
        """Wisps flowing from robe bottom."""
        strength = 1.4 if intense else 1.0
        for i, offset in enumerate((-14, -8, -2, 4, 10, 16, -20, 20)):
            t = (phase * 0.4 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 20)
            alpha = _NS_xaelmoran._alpha(180 * (1 - t) * strength)
            if alpha <= 0:
                continue
            color_key = ["robe_mid", "invoke_dark", "robe_light"][i % 3]
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[color_key], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_xaelmoran.PALETTE["invoke_light"], alpha),
                             (sx, sy, 1, 1))
    def _draw_ground_circle(surface, x, y, phase, skill):
        """Arcane circle on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xaelmoran.PALETTE["robe_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_xaelmoran.PALETTE["invoke_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_xaelmoran.PALETTE["invoke_mid"], 230),
                            (25, 22, 120, 18), 1)
        # Runes around
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_xaelmoran.PALETTE["invoke_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_xaelmoran.PALETTE["invoke_light"],
                                        _NS_xaelmoran._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - ARCANE BOLT (Ranged)
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic ranged attack: arcane bolt (gold+purple mixed)."""
        progress = getattr(boss, "_xlm_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        tx, ty = _NS_xaelmoran._target_position(boss, x, y)
        # PHASE 1: Charge at hand
        if progress < 0.4:
            t = progress / 0.4
            hand_x = x + facing * 12
            hand_y = y - 6
            charge_r = int(3 + t * 6)
            for r in range(charge_r + 4, 0, -1):
                alpha = _NS_xaelmoran._alpha(180 * (charge_r + 4 - r)
                                              / (charge_r + 4) * t)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE["invoke_mid"],
                                     _NS_xaelmoran._alpha(220 * t)),
                                    (hand_x, hand_y), max(1, charge_r - 2))
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE["invoke_light"],
                                     _NS_xaelmoran._alpha(240 * t)),
                                    (hand_x, hand_y), max(1, charge_r - 4))
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["invoke_shine"],
                             (hand_x, hand_y, 1, 1))
            # Orbiting sparks
            for i in range(5):
                a = boss.pulse * 6 + i * math.pi * 2 / 5
                sr = charge_r + 3
                sx = hand_x + int(math.cos(a) * sr)
                sy = hand_y + int(math.sin(a) * sr)
                pygame.draw.rect(surface,
                                 (*_NS_xaelmoran.PALETTE["invoke_shine"],
                                  _NS_xaelmoran._alpha(240 * t)),
                                 (sx, sy, 1, 1))
        # PHASE 2: Projectile flight
        else:
            t = min(1.0, (progress - 0.4) / 0.55)
            start_x = x + facing * 14
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xaelmoran._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_darkest"],
                                         alpha),
                                        (px, py), size)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_dark"],
                                         alpha),
                                        (px, py), max(1, size - 1))
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_mid"],
                                         alpha),
                                        (px, py), max(1, size - 2))
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_light"],
                                         alpha),
                                        (px, py), max(1, size - 3))
                if i < 4:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 1))
                        pygame.draw.rect(surface,
                                         (*_NS_xaelmoran.PALETTE["invoke_shine"],
                                          alpha),
                                         (spark_x, spark_y, 1, 1))
            # Bright head
            for r in range(12, 3, -2):
                alpha = _NS_xaelmoran._alpha(80 * (12 - r) / 12)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_light"],
                                         alpha),
                                        (bx, by), r)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_darkest"],
                                    (bx, by), 7)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_dark"],
                                    (bx, by), 5)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_mid"],
                                    (bx, by), 3)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_light"],
                                    (bx, by), 2)
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["white"], (bx, by, 1, 1))
            # Impact
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(6 + st * 20)
                alpha = _NS_xaelmoran._alpha(240 * (1 - st))
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_dark"],
                                         alpha),
                                        (tx, ty), radius, 2)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_mid"],
                                         alpha),
                                        (tx, ty), max(1, radius - 4), 1)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE["invoke_light"],
                                         alpha),
                                        (tx, ty), max(1, radius // 3))
                for i in range(8):
                    angle = i * math.pi / 4
                    ex = tx + int(math.cos(angle) * radius)
                    ey = ty + int(math.sin(angle) * radius * 0.8)
                    pygame.draw.rect(surface,
                                     (*_NS_xaelmoran.PALETTE["invoke_shine"],
                                      alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: Q - QUAS (Cold Beam - Blue)
    # ============================================================
    def _draw_quas_beam(surface, boss, x, y, timer, phase):
        _NS_xaelmoran._draw_element_beam(surface, boss, x, y, timer, phase,
                                          duration=50,
                                          color_prefix="cold",
                                          impact_effect="ice")
    # ============================================================
    # SKILL: W - WEX (Magic Beam - Purple)
    # ============================================================
    def _draw_wex_beam(surface, boss, x, y, timer, phase):
        _NS_xaelmoran._draw_element_beam(surface, boss, x, y, timer, phase,
                                          duration=45,
                                          color_prefix="magic",
                                          impact_effect="stun")
    # ============================================================
    # SKILL: E - EXORT (Fire Beam - Orange)
    # ============================================================
    def _draw_exort_beam(surface, boss, x, y, timer, phase):
        _NS_xaelmoran._draw_element_beam(surface, boss, x, y, timer, phase,
                                          duration=55,
                                          color_prefix="fire",
                                          impact_effect="burn")
    def _draw_element_beam(surface, boss, x, y, timer, phase, duration,
                            color_prefix, impact_effect):
        """Reusable elemental beam (used by Q/W/E)."""
        facing = boss.direction
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xaelmoran._target_position(boss, x, y)
        c_darkest = f"{color_prefix}_darkest"
        c_dark = f"{color_prefix}_dark"
        c_mid = f"{color_prefix}_mid"
        c_light = f"{color_prefix}_light"
        c_hot = f"{color_prefix}_hot"
        c_shine = f"{color_prefix}_shine"
        # PHASE 1: Charge (0-30%)
        if progress < 0.3:
            t = progress / 0.3
            hand_x = x + facing * 14
            hand_y = y - 6
            charge_r = int(4 + t * 8)
            for r in range(charge_r + 5, 0, -1):
                alpha = _NS_xaelmoran._alpha(200 * (charge_r + 5 - r)
                                              / (charge_r + 5) * t)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[c_dark], alpha),
                                        (hand_x, hand_y), r)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_mid],
                                     _NS_xaelmoran._alpha(240 * t)),
                                    (hand_x, hand_y), max(1, charge_r - 2))
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_light],
                                     _NS_xaelmoran._alpha(255 * t)),
                                    (hand_x, hand_y), max(1, charge_r - 4))
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_shine],
                                     _NS_xaelmoran._alpha(255 * t)),
                                    (hand_x, hand_y), max(1, charge_r - 6))
            for i in range(6):
                a = phase * 5 + i * math.pi / 3
                sr = charge_r + 3 + int(math.sin(phase * 4 + i) * 2)
                sx = hand_x + int(math.cos(a) * sr)
                sy = hand_y + int(math.sin(a) * sr)
                pygame.draw.rect(surface,
                                 (*_NS_xaelmoran.PALETTE[c_shine],
                                  _NS_xaelmoran._alpha(240 * t)),
                                 (sx, sy, 2, 2))
        # PHASE 2: Projectile bolt travels to target (30-70%)
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            start_x = x + facing * 16
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Long trail
            for i in range(14):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xaelmoran._alpha(240 - i * 17)
                size = max(1, 9 - i)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[c_darkest], alpha),
                                        (px, py), size)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[c_dark], alpha),
                                        (px, py), max(1, size - 1))
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[c_mid], alpha),
                                        (px, py), max(1, size - 2))
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[c_light], alpha),
                                        (px, py), max(1, size - 3))
                # Sparks around trail
                if i < 6:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_xaelmoran.PALETTE[c_hot], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Bright head
            for r in range(16, 3, -2):
                alpha = _NS_xaelmoran._alpha(100 * (16 - r) / 16)
                _NS_xaelmoran._aacircle(surface,
                                        (*_NS_xaelmoran.PALETTE[c_light], alpha),
                                        (bx, by), r)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[c_darkest], (bx, by), 10)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[c_dark], (bx, by), 8)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[c_mid], (bx, by), 6)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[c_light], (bx, by), 4)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[c_hot], (bx, by), 2)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[c_shine], (bx, by), 1)
            pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["white"], (bx, by, 1, 1))
        # PHASE 3: Impact explosion (70-100%)
        else:
            t = (progress - 0.7) / 0.3
            radius = int(10 + t * 30)
            alpha = _NS_xaelmoran._alpha(240 * (1 - t))
            # Element-specific ground effect
            if impact_effect == "ice":
                # Ice shards
                for i in range(10):
                    angle = i * math.pi / 5 + phase * 0.2
                    shard_r = int(radius * (0.5 + (i % 3) * 0.2))
                    sx = tx + int(math.cos(angle) * shard_r)
                    sy = ty + int(math.sin(angle) * shard_r * 0.6)
                    shard_h = 8
                    _NS_xaelmoran._poly(surface,
                                        (*_NS_xaelmoran.PALETTE[c_dark], alpha), [
                        (sx, sy - shard_h),
                        (sx - 2, sy),
                        (sx + 2, sy),
                    ])
                    _NS_xaelmoran._poly(surface,
                                        (*_NS_xaelmoran.PALETTE[c_mid], alpha), [
                        (sx, sy - shard_h),
                        (sx - 1, sy),
                        (sx + 1, sy),
                    ])
                    pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[c_shine],
                                     (sx, sy - shard_h, 1, 1))
            elif impact_effect == "burn":
                # Fire flames rising
                for i in range(12):
                    angle = i * math.pi / 6
                    fr = int(radius * (0.4 + (i % 3) * 0.25))
                    fx = tx + int(math.cos(angle) * fr)
                    fy = ty + int(math.sin(angle) * fr * 0.6)
                    flame_h = 6 + int(math.sin(phase * 5 + i) * 3)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[c_dark],
                                             alpha),
                                            (fx, fy - flame_h // 2), 3)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[c_mid],
                                             alpha),
                                            (fx, fy - flame_h // 2), 2)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[c_hot],
                                             alpha),
                                            (fx, fy - flame_h), 1)
            # Impact rings
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_darkest], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_dark], alpha),
                                    (tx, ty), radius, 3)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_mid], alpha),
                                    (tx, ty), max(1, radius - 6), 2)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_light], alpha),
                                    (tx, ty), max(1, radius - 12), 1)
            # Bright core
            core_r = max(1, int(8 * (1 - t)))
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_hot], alpha),
                                    (tx, ty), core_r + 1)
            _NS_xaelmoran._aacircle(surface,
                                    (*_NS_xaelmoran.PALETTE[c_shine], alpha),
                                    (tx, ty), max(1, core_r - 1))
            # Radial particles
            for i in range(14):
                angle = i * math.pi / 7
                pr = int(radius * (0.7 + (i % 3) * 0.15))
                px = tx + int(math.cos(angle) * pr)
                py = ty + int(math.sin(angle) * pr * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_xaelmoran.PALETTE[c_hot], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xaelmoran.PALETTE[c_shine], alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: R - INVOKE (Combined all elements)
    # ============================================================
    def _draw_invoke_ground(surface, boss, x, y, timer, phase):
        """Grand arcane circle beneath target."""
        tx, ty = _NS_xaelmoran._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2.5))
        if r > 5:
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            alpha = _NS_xaelmoran._alpha(220 * pulse)
            # Large arcane circle
            pygame.draw.ellipse(surface, (*_NS_xaelmoran.PALETTE["invoke_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_xaelmoran.PALETTE["invoke_mid"], alpha),
                                (tx - r + 4, ty - r // 3 + 3,
                                 r * 2 - 8, r * 2 // 3 - 6), 2)
            pygame.draw.ellipse(surface, (*_NS_xaelmoran.PALETTE["invoke_light"], alpha),
                                (tx - r + 10, ty - r // 3 + 6,
                                 r * 2 - 20, r * 2 // 3 - 12), 1)
            # Inner rune circle
            inner_r = r * 2 // 3
            pygame.draw.ellipse(surface, (*_NS_xaelmoran.PALETTE["invoke_mid"], alpha),
                                (tx - inner_r, ty - inner_r // 3,
                                 inner_r * 2, inner_r * 2 // 3), 2)
            # Runes
            for i in range(16):
                angle = phase * 0.5 + i * math.pi / 8
                rx = tx + int(math.cos(angle) * r * 0.8)
                ry = ty + int(math.sin(angle) * r * 0.8 * 0.4)
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["invoke_shine"],
                                 (rx, ry, 2, 2))
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["white"],
                                 (rx, ry, 1, 1))
    def _draw_invoke_foreground(surface, boss, x, y, timer, phase):
        """Three orbs converge at target and explode."""
        tx, ty = _NS_xaelmoran._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.5:
            # Orbs launch toward target
            t = progress / 0.5
            start_x = x + facing * 14
            start_y = y - 10
            elements = [
                ("cold_dark", "cold_mid", "cold_light", "cold_shine"),
                ("magic_dark", "magic_mid", "magic_light", "magic_shine"),
                ("fire_dark", "fire_mid", "fire_light", "fire_shine"),
            ]
            for i, (dc, mc, lc, sc) in enumerate(elements):
                # Spiral/curved path
                spiral_offset = math.sin(t * math.pi * 2 + i * math.pi * 2 / 3) * 30 * (1 - t)
                bx = int(start_x + (tx - start_x) * t)
                by = int(start_y + (ty - start_y) * t + spiral_offset)
                # Trail
                for j in range(6):
                    trail_t = max(0.0, t - j * 0.06)
                    sp_off = math.sin(trail_t * math.pi * 2 + i * math.pi * 2 / 3) \
                             * 30 * (1 - trail_t)
                    px = int(start_x + (tx - start_x) * trail_t)
                    py = int(start_y + (ty - start_y) * trail_t + sp_off)
                    alpha = _NS_xaelmoran._alpha(220 - j * 30)
                    size = max(1, 5 - j)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[dc], alpha),
                                            (px, py), size)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[mc], alpha),
                                            (px, py), max(1, size - 1))
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[lc], alpha),
                                            (px, py), max(1, size - 2))
                # Head
                for r in range(8, 0, -1):
                    alpha = _NS_xaelmoran._alpha(140 * (8 - r) / 8)
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[lc], alpha),
                                            (bx, by), r)
                _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[dc], (bx, by), 5)
                _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[mc], (bx, by), 3)
                _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE[lc], (bx, by), 2)
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE[sc], (bx, by, 1, 1))
        else:
            # Massive combined explosion
            t = (progress - 0.5) / 0.5
            radius = int(15 + t * 55)
            alpha = _NS_xaelmoran._alpha(255 * (1 - t))
            # Multi-color explosion rings
            for i, color_key in enumerate([
                "invoke_darkest", "invoke_dark", "invoke_mid",
                "cold_mid", "magic_mid", "fire_mid",
                "invoke_light", "invoke_shine",
            ]):
                ring_r = radius - i * 5
                if ring_r > 0:
                    _NS_xaelmoran._aacircle(surface,
                                            (*_NS_xaelmoran.PALETTE[color_key], alpha),
                                            (tx, ty), ring_r, 2)
            # Center white flash
            core_r = max(1, int(15 * (1 - t)))
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["invoke_shine"],
                                    (tx, ty), core_r + 2)
            _NS_xaelmoran._aacircle(surface, _NS_xaelmoran.PALETTE["white"],
                                    (tx, ty), max(1, core_r))
            # Radial rays (3 colors)
            for i in range(24):
                angle = i * math.pi / 12
                ray_len = radius + 8
                lx = tx + int(math.cos(angle) * ray_len)
                ly = ty + int(math.sin(angle) * ray_len * 0.9)
                color_choice = ["cold_hot", "magic_hot", "fire_hot"][i % 3]
                pygame.draw.line(surface,
                                 (*_NS_xaelmoran.PALETTE[color_choice], alpha),
                                 (tx, ty), (lx, ly), 2)
                pygame.draw.rect(surface, _NS_xaelmoran.PALETTE["white"],
                                 (lx, ly, 2, 2))
            # Elemental particles bursting outward
            for i in range(20):
                angle = i * math.pi / 10 + phase * 0.5
                pr = int(radius * (0.6 + (i % 4) * 0.15))
                px = tx + int(math.cos(angle) * pr)
                py = ty + int(math.sin(angle) * pr * 0.8)
                color_choice = ["cold_shine", "magic_shine", "fire_shine",
                                "invoke_shine"][i % 4]
                pygame.draw.rect(surface,
                                 (*_NS_xaelmoran.PALETTE[color_choice], alpha),
                                 (px, py, 2, 2))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_bhorgathul(surface, boss, x, y):
    """Entry point bhorgathul."""
    return _NS_bhorgathul.draw_bhorgathul(surface, boss, x, y)


def draw_morkhelvis(surface, boss, x, y):
    """Entry point morkhelvis."""
    return _NS_morkhelvis.draw_morkhelvis(surface, boss, x, y)


def draw_vorthakul(surface, boss, x, y):
    """Entry point vorthakul."""
    return _NS_vorthakul.draw_vorthakul(surface, boss, x, y)


def draw_xaelmoran(surface, boss, x, y):
    """Entry point xaelmoran."""
    return _NS_xaelmoran.draw_xaelmoran(surface, boss, x, y)
