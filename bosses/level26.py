"""
bosses/level26.py - Semua boss Level 26

Berisi:
  - aelyrion   (mini boss - MELEE steel maiden divine guardian)
  - kaervosth  (mini boss - MELEE stormblade rogue knight)
  - morvyssk   (mini boss - MELEE corrosive purple ooze)
  - vaelmyrra  (TRUE BOSS - MELEE crimson matriarch, obsidian warlord)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _ael_ (aelyrion), _kae_ (kaervosth), _vae_ (vaelmyrra) sudah unik.
  - _mor_ (morvyssk) di-rename -> _mvy_ (bentrok dengan Morgath level 1),
    termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# AELYRION (DIVINE GUARDIAN) - Mini Boss
# ====================================================================

class _NS_aelyrion:
    """Namespace aelyrion - HD steel maiden guardian boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Steel armor (silver / plate)
        "steel_darkest": (18, 22, 32),
        "steel_dark": (55, 65, 85),
        "steel_mid": (110, 125, 150),
        "steel_light": (180, 195, 220),
        "steel_shine": (235, 245, 255),
        "steel_white": (255, 255, 255),
        # Gold trim (royal accents)
        "gold_darkest": (45, 30, 8),
        "gold_dark": (110, 80, 25),
        "gold_mid": (190, 150, 55),
        "gold_light": (240, 210, 110),
        "gold_shine": (255, 240, 180),
        # Divine blue energy (crystals, glow, beams)
        "energy_darkest": (5, 15, 40),
        "energy_dark": (15, 55, 120),
        "energy_mid": (50, 130, 220),
        "energy_light": (110, 200, 255),
        "energy_hot": (180, 235, 255),
        "energy_shine": (230, 250, 255),
        # Skin (face, neck) — pale porcelain
        "skin_dark": (150, 110, 95),
        "skin_mid": (215, 175, 155),
        "skin_light": (245, 215, 195),
        "skin_shine": (255, 235, 220),
        # Hair (blonde / golden)
        "hair_darkest": (55, 35, 15),
        "hair_dark": (120, 85, 35),
        "hair_mid": (200, 155, 75),
        "hair_light": (245, 210, 130),
        "hair_shine": (255, 240, 190),
        # Divine white/holy
        "holy_dim": (200, 220, 255),
        "holy_bright": (240, 250, 255),
        # Shadow / eye socket
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        # Eye (blue divine)
        "eye_dark": (10, 30, 70),
        "eye_mid": (60, 140, 220),
        "eye_light": (150, 220, 255),
        "eye_glow": (220, 245, 255),
        # Cape (dark navy → blue glow trim)
        "cape_dark": (10, 15, 35),
        "cape_mid": (25, 40, 80),
        "cape_light": (50, 80, 140),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_aelyrion._clamp(color)
        if _NS_aelyrion.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_aelyrion._clamp(color)
        if _NS_aelyrion.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        # Defensive: pygame requires >= 3 points for polygon
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_aelyrion._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_aelyrion._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_aelyrion._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_aelyrion(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_aelyrion._detect_moving(boss)
        _NS_aelyrion._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_ael_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_aelyrion._draw_divine_aura(surface, x, y, pulse)
        _NS_aelyrion._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX (behind)
        if active_skill == "w":
            _NS_aelyrion._draw_guardian_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aelyrion._draw_dash_trail(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aelyrion._draw_divine_gate_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with hover bob
        if attacking:
            _NS_aelyrion._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_aelyrion._draw_float_move(surface, boss, x, y)
        else:
            _NS_aelyrion._draw_float_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_aelyrion._draw_thorned_ray(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_aelyrion._draw_guardian_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aelyrion._draw_dash_shield(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aelyrion._draw_divine_gate_wings(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ael_previous_timer", 0))
        active = bool(getattr(boss, "_ael_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._ael_attack_active = True
            boss._ael_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._ael_attack_frame = int(getattr(boss, "_ael_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._ael_attack_active = False
            boss._ael_attack_frame = 0
            active = False
        boss._ael_previous_timer = timer
        boss._ael_attack_progress = (
            min(1.0, getattr(boss, "_ael_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_ael_last_x"):
            boss._ael_last_x = boss.x
            boss._ael_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ael_last_x)
        dy = abs(boss.y - boss._ael_last_y)
        boss._ael_last_x = boss.x
        boss._ael_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_aelyrion._draw_hover_shadow(surface, x, y + 55, boss.pulse)
        _NS_aelyrion._draw_hover_energy(surface, x, y + 42, boss.pulse)
        _NS_aelyrion._draw_body(surface, x + sway, y + bob,
                                boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_aelyrion._draw_hover_shadow(surface, x + sway, y + 55, phase)
        _NS_aelyrion._draw_hover_energy(surface, x + sway, y + 42, phase, trail=True,
                                        facing=boss.direction)
        _NS_aelyrion._draw_body(surface, x + sway, y + bob,
                                boss.direction, phase, "move")
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_ael_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up (lean back+up) → forward step lunge → recover
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 18)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(13 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_aelyrion._draw_hover_shadow(surface, x + lunge, y + 55, boss.pulse)
        _NS_aelyrion._draw_hover_energy(surface, x + lunge, y + 42, boss.pulse,
                                        intense=True)
        _NS_aelyrion._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_aelyrion._draw_sword_swing_fx(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY - Steel Maiden with cape, armor, floating
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        _NS_aelyrion._draw_cape(surface, cx, cy, facing, phase, action)
        _NS_aelyrion._draw_legs(surface, cx, cy + 22, facing, phase)
        _NS_aelyrion._draw_torso(surface, cx, cy, facing, phase)
        _NS_aelyrion._draw_shoulders(surface, cx, cy - 8, facing, phase)
        _NS_aelyrion._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_aelyrion._draw_head(surface, cx, cy - 24, facing, phase)
        _NS_aelyrion._draw_sword(surface, cx, cy, facing, phase, action, attack_progress)
    # ---------- CAPE ----------
    def _draw_cape(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 3
        if action == "move":
            sway = math.sin(phase * 1.2) * 5
        back_dir = -facing
        base_x = cx + back_dir * 6
        base_y = cy - 6
        top_a = (base_x - 5, base_y)
        top_b = (base_x + 8 * back_dir, base_y)
        bot_a = (base_x - 10 + int(sway), base_y + 34)
        bot_b = (base_x + 16 * back_dir + int(sway), base_y + 30)
        mid_a = (base_x - 8 + int(sway * 0.5), base_y + 18)
        mid_b = (base_x + 13 * back_dir + int(sway * 0.5), base_y + 17)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"], [
            (top_a[0] + 2, top_a[1] + 2), (top_b[0] + 2, top_b[1] + 2),
            (bot_b[0] + 2, bot_b[1] + 2), (bot_a[0] + 2, bot_a[1] + 2),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["cape_dark"],
                           [top_a, top_b, mid_b, bot_b, bot_a, mid_a])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["cape_mid"], [
            (top_a[0] + 1, top_a[1] + 2), (top_b[0] - 1 * back_dir, top_b[1] + 2),
            (mid_b[0] - 2 * back_dir, mid_b[1]),
            (mid_a[0] + 2, mid_a[1]),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["cape_light"], [
            (top_a[0] + 2, top_a[1] + 3), (top_b[0] - 2 * back_dir, top_b[1] + 3),
            (int((top_b[0] + mid_b[0]) / 2), int((top_b[1] + mid_b[1]) / 2)),
            (int((top_a[0] + mid_a[0]) / 2), int((top_a[1] + mid_a[1]) / 2)),
        ])
        # Glowing blue trim along bottom edge
        for i in range(6):
            t = i / 5
            px = int(bot_a[0] + (bot_b[0] - bot_a[0]) * t)
            py = int(bot_a[1] + (bot_b[1] - bot_a[1]) * t)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["energy_dark"], (px, py), 2)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_light"], (px, py, 1, 1))
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase):
        for side in (-1, 1):
            lx = cx + side * 4
            ly = cy
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"], [
                (lx - 3 + 1, ly + 1), (lx + 3 + 1, ly + 1),
                (lx + 4 + 1, ly + 10 + 1), (lx - 4 + 1, ly + 10 + 1),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_darkest"], [
                (lx - 3, ly), (lx + 3, ly), (lx + 4, ly + 10), (lx - 4, ly + 10),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_dark"], [
                (lx - 2, ly + 1), (lx + 2, ly + 1),
                (lx + 3, ly + 9), (lx - 3, ly + 9),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_mid"], [
                (lx - 1, ly + 2), (lx + 1, ly + 2),
                (lx + 2, ly + 8), (lx - 2, ly + 8),
            ])
            pygame.draw.line(surface, _NS_aelyrion.PALETTE["steel_light"],
                             (lx, ly + 2), (lx, ly + 8), 1)
            pygame.draw.line(surface, _NS_aelyrion.PALETTE["gold_mid"],
                             (lx - 3, ly), (lx + 3, ly), 1)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_light"],
                             (lx - 1, ly, 2, 1))
            # Foot (pointed armored boot)
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_darkest"], [
                (lx - 4, ly + 10), (lx + 4, ly + 10),
                (lx + 5, ly + 13), (lx - 3, ly + 13),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_dark"], [
                (lx - 3, ly + 11), (lx + 3, ly + 11),
                (lx + 4, ly + 12), (lx - 2, ly + 12),
            ])
    # ---------- TORSO ----------
    def _draw_torso(surface, cx, cy, facing, phase):
        pts = [
            (cx - 10, cy - 8),
            (cx - 12, cy - 4),
            (cx - 10, cy + 6),
            (cx - 8, cy + 16),
            (cx + 8, cy + 16),
            (cx + 10, cy + 6),
            (cx + 12, cy - 4),
            (cx + 10, cy - 8),
        ]
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in pts])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_darkest"], pts)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_dark"], [
            (cx - 9, cy - 7), (cx - 11, cy - 4), (cx - 9, cy + 5),
            (cx - 7, cy + 15), (cx + 7, cy + 15),
            (cx + 9, cy + 5), (cx + 11, cy - 4), (cx + 9, cy - 7),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_mid"], [
            (cx - 7, cy - 5), (cx - 9, cy - 2), (cx - 7, cy + 3),
            (cx - 5, cy + 12), (cx + 5, cy + 12),
            (cx + 7, cy + 3), (cx + 9, cy - 2), (cx + 7, cy - 5),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_light"], [
            (cx - 3, cy - 3), (cx + 3, cy - 3),
            (cx + 4, cy + 4), (cx - 4, cy + 4),
        ])
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["steel_shine"],
                         (cx - 1, cy - 2), (cx - 1, cy + 3), 1)
        # BLUE ENERGY CRYSTAL center chest
        crystal_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        cry_x, cry_y = cx, cy - 1
        for r in range(8, 0, -1):
            alpha = _NS_aelyrion._alpha(80 * (8 - r) / 8 * crystal_pulse)
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                   (cry_x, cry_y), r)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["energy_darkest"], [
            (cry_x, cry_y - 4), (cry_x + 3, cry_y),
            (cry_x, cry_y + 4), (cry_x - 3, cry_y),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["energy_dark"], [
            (cry_x, cry_y - 3), (cry_x + 2, cry_y),
            (cry_x, cry_y + 3), (cry_x - 2, cry_y),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["energy_mid"], [
            (cry_x, cry_y - 2), (cry_x + 1, cry_y),
            (cry_x, cry_y + 2), (cry_x - 1, cry_y),
        ])
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_hot"],
                         (cry_x, cry_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_shine"],
                         (cry_x, cry_y, 1, 1))
        # Gold trim belt
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["gold_dark"],
                         (cx - 10, cy + 6), (cx + 10, cy + 6), 1)
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["gold_mid"],
                         (cx - 9, cy + 6), (cx + 9, cy + 6), 1)
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["gold_light"],
                         (cx - 4, cy + 6), (cx + 4, cy + 6), 1)
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_dark"],
                         (cx - 2, cy + 5, 4, 3))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_mid"],
                         (cx - 1, cy + 6, 2, 1))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_shine"],
                         (cx, cy + 6, 1, 1))
    # ---------- SHOULDERS ----------
    def _draw_shoulders(surface, cx, cy, facing, phase):
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for side in (-1, 1):
            sx = cx + side * 12
            sy = cy
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"], [
                (sx - 6 + 2, sy - 3 + 2), (sx + 6 + 2, sy - 3 + 2),
                (sx + 7 + 2, sy + 5 + 2), (sx - 7 + 2, sy + 5 + 2),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_darkest"], [
                (sx - 6, sy - 3), (sx + 6, sy - 3),
                (sx + 7, sy + 5), (sx - 7, sy + 5),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_dark"], [
                (sx - 5, sy - 2), (sx + 5, sy - 2),
                (sx + 6, sy + 4), (sx - 6, sy + 4),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_mid"], [
                (sx - 3, sy - 1), (sx + 3, sy - 1),
                (sx + 4, sy + 3), (sx - 4, sy + 3),
            ])
            pygame.draw.line(surface, _NS_aelyrion.PALETTE["steel_light"],
                             (sx - 1, sy), (sx - 1, sy + 3), 1)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["steel_shine"],
                             (sx, sy, 1, 1))
            pygame.draw.line(surface, _NS_aelyrion.PALETTE["gold_mid"],
                             (sx - 6, sy - 3), (sx + 6, sy - 3), 1)
            # Blue crystal on pauldron
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_light"],
                                    _NS_aelyrion._alpha(150 * pulse)),
                                   (sx, sy + 2), 4)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["energy_darkest"], (sx, sy + 2), 2)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["energy_mid"], (sx, sy + 2), 1)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_shine"],
                             (sx, sy + 2, 1, 1))
    # ---------- ARMS (with proper overhead swing) ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        for side, is_sword_side in ((-1, False), (1, True)):
            base_x = cx + side * 11
            base_y = cy - 4
            is_dominant = (side * facing > 0)
            if action == "attack" and is_dominant:
                if attack_progress < 0.35:
                    # Wind-up: arm raised UP-BACK
                    t = attack_progress / 0.35
                    elbow_offset_x = int(-6 * facing)
                    elbow_offset_y = int(-8 + t * -2)
                    hand_offset_x = int(-10 * facing)
                    hand_offset_y = int(-14)
                elif attack_progress < 0.6:
                    # Swing down-forward
                    t = (attack_progress - 0.35) / 0.25
                    elbow_offset_x = int((-6 + t * 12) * facing)
                    elbow_offset_y = int(-10 + t * 14)
                    hand_offset_x = int((-10 + t * 22) * facing)
                    hand_offset_y = int(-14 + t * 18)
                else:
                    # Recovery
                    t = (attack_progress - 0.6) / 0.4
                    elbow_offset_x = int((6 - t * 2) * facing)
                    elbow_offset_y = int(4 - t * 2)
                    hand_offset_x = int((12 - t * 4) * facing)
                    hand_offset_y = int(4 + t * 1)
            else:
                # Idle sway
                swing = math.sin(phase * 0.6 + side) * 0.15
                elbow_offset_x = int(math.sin(swing) * 4 * side)
                elbow_offset_y = 6
                hand_offset_x = int(math.sin(swing * 1.5) * 6 * side)
                hand_offset_y = 12
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["shadow_deep"],
                                 (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 6)
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_darkest"],
                                 (base_x, base_y), (elbow_x, elbow_y), 5)
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_dark"],
                                 (base_x, base_y), (elbow_x, elbow_y), 3)
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_mid"],
                                 (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow joint
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["steel_darkest"],
                                   (elbow_x, elbow_y), 3)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["steel_dark"],
                                   (elbow_x, elbow_y), 2)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["steel_light"],
                             (elbow_x, elbow_y, 1, 1))
            # Forearm
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["shadow_deep"],
                                 (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 5)
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_darkest"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 4)
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_dark"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 2)
            _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_mid"],
                                 (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
            # Hand (gauntlet)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 4)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["steel_darkest"],
                                   (hand_x, hand_y), 3)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["steel_dark"],
                                   (hand_x, hand_y), 2)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["steel_light"],
                             (hand_x, hand_y, 1, 1))
            if is_sword_side:
                _NS_aelyrion._last_sword_hand = (hand_x, hand_y, 0.0)
    # ---------- HEAD ----------
    def _draw_head(surface, cx, cy, facing, phase):
        face_pts = [
            (cx - 5, cy - 4), (cx - 6, cy),
            (cx - 5, cy + 4), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 4),
            (cx + 6, cy), (cx + 5, cy - 4),
            (cx + 3, cy - 7), (cx - 3, cy - 7),
        ]
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["skin_dark"], face_pts)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["skin_mid"], [
            (cx - 4, cy - 3), (cx - 5, cy),
            (cx - 4, cy + 3), (cx - 1, cy + 6),
            (cx + 3, cy + 6), (cx + 5, cy + 3),
            (cx + 5, cy - 1), (cx + 4, cy - 6),
            (cx - 2, cy - 6),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["skin_light"], [
            (cx - 3, cy - 2), (cx - 4, cy),
            (cx - 2, cy + 3), (cx + 2, cy + 4),
            (cx + 4, cy + 2), (cx + 4, cy - 2),
            (cx + 2, cy - 5), (cx - 1, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["skin_shine"],
                         (cx - 2 * facing, cy - 1, 1, 1))
        # EYES glowing blue
        eye_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 1
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["shadow_deep"], (ex - 1, ey, 2, 1))
            for r in range(3, 0, -1):
                alpha = _NS_aelyrion._alpha(120 * (3 - r) / 3 * eye_pulse)
                _NS_aelyrion._aacircle(surface,
                                       (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # LIPS
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["skin_dark"],
                         (cx - 1, cy + 4), (cx + 1, cy + 4), 1)
        _NS_aelyrion._draw_hair(surface, cx, cy, facing, phase)
        _NS_aelyrion._draw_crown(surface, cx, cy - 7, facing, phase)
    def _draw_hair(surface, cx, cy, facing, phase):
        sway = math.sin(phase * 0.5) * 2
        hair_pts = [
            (cx - 6, cy - 5),
            (cx - 8, cy - 2 + int(sway * 0.3)),
            (cx - 9, cy + 4 + int(sway * 0.5)),
            (cx - 10, cy + 12 + int(sway)),
            (cx - 8, cy + 20 + int(sway * 1.2)),
            (cx - 4, cy + 22 + int(sway)),
            (cx + 4, cy + 22 + int(sway)),
            (cx + 8, cy + 20 + int(sway * 1.2)),
            (cx + 10, cy + 12 + int(sway)),
            (cx + 9, cy + 4 + int(sway * 0.5)),
            (cx + 8, cy - 2 + int(sway * 0.3)),
            (cx + 6, cy - 5),
        ]
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["hair_darkest"], hair_pts)
        mid_pts = [
            (cx - 5, cy - 5),
            (cx - 7, cy + 4 + int(sway * 0.5)),
            (cx - 8, cy + 15 + int(sway)),
            (cx - 3, cy + 20 + int(sway)),
            (cx + 3, cy + 20 + int(sway)),
            (cx + 8, cy + 15 + int(sway)),
            (cx + 7, cy + 4 + int(sway * 0.5)),
            (cx + 5, cy - 5),
        ]
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["hair_dark"], mid_pts)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["hair_mid"], [
            (cx - 4, cy - 5),
            (cx - 6, cy + 8 + int(sway * 0.4)),
            (cx - 5, cy + 18 + int(sway)),
            (cx + 5, cy + 18 + int(sway)),
            (cx + 6, cy + 8 + int(sway * 0.4)),
            (cx + 4, cy - 5),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["hair_dark"], [
            (cx - 5, cy - 7), (cx - 6, cy - 3),
            (cx - 3, cy - 5), (cx, cy - 6),
            (cx + 3, cy - 5), (cx + 6, cy - 3),
            (cx + 5, cy - 7),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["hair_mid"], [
            (cx - 4, cy - 7), (cx - 4, cy - 4),
            (cx - 1, cy - 5), (cx + 2, cy - 5),
            (cx + 4, cy - 4), (cx + 4, cy - 7),
        ])
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["hair_light"],
                         (cx - 2, cy - 6), (cx + 2, cy - 6), 1)
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["hair_shine"],
                         (cx, cy - 6, 1, 1))
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["hair_light"],
                         (cx - 6, cy + 2), (cx - 7, cy + 12 + int(sway)), 1)
        pygame.draw.line(surface, _NS_aelyrion.PALETTE["hair_light"],
                         (cx + 6, cy + 2), (cx + 7, cy + 12 + int(sway)), 1)
    def _draw_crown(surface, cx, cy, facing, phase):
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_dark"], (cx - 5, cy, 11, 2))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_mid"], (cx - 5, cy, 11, 1))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_shine"], (cx - 3, cy, 6, 1))
        # Center tall spike
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["gold_dark"], [
            (cx, cy - 5), (cx - 2, cy), (cx + 2, cy),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["gold_mid"], [
            (cx, cy - 4), (cx - 1, cy), (cx + 1, cy),
        ])
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_shine"], (cx, cy - 3, 1, 2))
        # Center jewel (blue diamond)
        jewel_pulse = math.sin(phase * 2) * 0.3 + 0.7
        jy = cy + 1
        for r in range(3, 0, -1):
            alpha = _NS_aelyrion._alpha(150 * (3 - r) / 3 * jewel_pulse)
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                   (cx, jy), r)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["energy_darkest"], [
            (cx, jy - 1), (cx + 1, jy), (cx, jy + 1), (cx - 1, jy),
        ])
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_hot"], (cx, jy, 1, 1))
        # Side spikes (proper triangles)
        for side in (-1, 1):
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["gold_dark"], [
                (cx + side * 4, cy - 2),
                (cx + side * 3, cy),
                (cx + side * 5, cy),
            ])
            _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["gold_mid"], [
                (cx + side * 4, cy - 1),
                (cx + side * 3, cy),
                (cx + side * 5, cy),
            ])
    # ---------- SWORD (Overhead swing) ----------
    def _draw_sword(surface, cx, cy, facing, phase, action, attack_progress):
        hand_data = getattr(_NS_aelyrion, "_last_sword_hand", None)
        if hand_data is None:
            hx, hy = cx + facing * 22, cy + 2
        else:
            hx, hy, _ = hand_data
        blade_len = 26
        # SWING FROM TOP TO BOTTOM (overhead chop)
        # Angle convention: 0 = right, pi/2 = down, -pi/2 = up
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up — sword raised UP-BACK
                if facing > 0:
                    blade_angle = -math.pi * 0.75  # up-back-left
                else:
                    blade_angle = -math.pi * 0.25  # up-back-right (mirror)
            elif attack_progress < 0.6:
                # Swing DOWN through arc
                t = (attack_progress - 0.35) / 0.25
                if facing > 0:
                    # from -135° down to +45° (down-forward)
                    blade_angle = -math.pi * 0.75 + t * math.pi
                else:
                    # from -45° down to +135° (down-forward left mirror)
                    blade_angle = -math.pi * 0.25 - t * math.pi
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                if facing > 0:
                    blade_angle = math.pi * 0.25 - t * math.pi * 0.1
                else:
                    blade_angle = math.pi * 0.75 + t * math.pi * 0.1
        else:
            # Rest: pointing down-forward
            if facing > 0:
                blade_angle = math.pi * 0.15 + math.sin(phase * 0.5) * 0.05
            else:
                blade_angle = math.pi * 0.85 + math.sin(phase * 0.5) * 0.05
        tip_x = hx + int(math.cos(blade_angle) * blade_len)
        tip_y = hy + int(math.sin(blade_angle) * blade_len)
        perp = blade_angle + math.pi / 2
        pw = 2
        edge_a = (hx + int(math.cos(perp) * pw), hy + int(math.sin(perp) * pw))
        edge_b = (hx - int(math.cos(perp) * pw), hy - int(math.sin(perp) * pw))
        mid_x = int((hx + tip_x) / 2)
        mid_y = int((hy + tip_y) / 2)
        mid_a = (mid_x + int(math.cos(perp) * 3), mid_y + int(math.sin(perp) * 3))
        mid_b = (mid_x - int(math.cos(perp) * 3), mid_y - int(math.sin(perp) * 3))
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"], [
            (edge_a[0] + 2, edge_a[1] + 2),
            (mid_a[0] + 2, mid_a[1] + 2),
            (tip_x + 2, tip_y + 2),
            (mid_b[0] + 2, mid_b[1] + 2),
            (edge_b[0] + 2, edge_b[1] + 2),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_darkest"], [
            edge_a, mid_a, (tip_x, tip_y), mid_b, edge_b,
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_dark"], [
            (int(edge_a[0] * 0.9 + hx * 0.1), int(edge_a[1] * 0.9 + hy * 0.1)),
            mid_a, (tip_x, tip_y), mid_b,
            (int(edge_b[0] * 0.9 + hx * 0.1), int(edge_b[1] * 0.9 + hy * 0.1)),
        ])
        _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_mid"], (hx, hy), (tip_x, tip_y), 2)
        _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_light"], (hx, hy), (tip_x, tip_y), 1)
        _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["steel_shine"],
                             (int(hx * 0.7 + tip_x * 0.3), int(hy * 0.7 + tip_y * 0.3)),
                             (int(hx * 0.3 + tip_x * 0.7), int(hy * 0.3 + tip_y * 0.7)), 1)
        # Blue glow trim along edges
        glow_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for pt_pair in [(edge_a, mid_a), (mid_a, (tip_x, tip_y)),
                        (edge_b, mid_b), (mid_b, (tip_x, tip_y))]:
            _NS_aelyrion._aaline(surface,
                                 (*_NS_aelyrion.PALETTE["energy_light"],
                                  _NS_aelyrion._alpha(200 * glow_pulse)),
                                 pt_pair[0], pt_pair[1], 1)
        _NS_aelyrion._aacircle(surface,
                               (*_NS_aelyrion.PALETTE["energy_hot"],
                                _NS_aelyrion._alpha(220 * glow_pulse)),
                               (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_shine"], (tip_x, tip_y, 1, 1))
        # Cross guard (gold)
        cg_perp = blade_angle + math.pi / 2
        cg_len = 5
        cga = (hx + int(math.cos(cg_perp) * cg_len), hy + int(math.sin(cg_perp) * cg_len))
        cgb = (hx - int(math.cos(cg_perp) * cg_len), hy - int(math.sin(cg_perp) * cg_len))
        _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["gold_darkest"], cga, cgb, 3)
        _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["gold_mid"], cga, cgb, 2)
        _NS_aelyrion._aaline(surface, _NS_aelyrion.PALETTE["gold_shine"], cga, cgb, 1)
        # Pommel
        pom_x = hx - int(math.cos(blade_angle) * 4)
        pom_y = hy - int(math.sin(blade_angle) * 4)
        _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["gold_darkest"], (pom_x, pom_y), 3)
        _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["gold_mid"], (pom_x, pom_y), 2)
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_shine"], (pom_x, pom_y, 1, 1))
    # ============================================================
    # ATTACK FX: Overhead sword swing arc
    # ============================================================
    def _draw_sword_swing_fx(surface, boss, x, y, progress):
        if progress < 0.35 or progress > 0.75:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.4
        # Arc pivot at shoulder level, arc sweeps overhead → down-forward
        arc_cx = x + facing * 8
        arc_cy = y - 8
        for i in range(4):
            layer_t = max(0, t - i * 0.1)
            if layer_t <= 0:
                continue
            alpha = _NS_aelyrion._alpha(240 * (1 - layer_t) * (1 - i * 0.2))
            radius = int(22 + layer_t * 6 + i * 2)
            if facing > 0:
                start_angle = -math.pi * 0.75
                end_angle = math.pi * 0.25
            else:
                start_angle = -math.pi * 0.25
                end_angle = math.pi * 0.75
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 12
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_aelyrion._aaline(surface,
                                         (*_NS_aelyrion.PALETTE["energy_darkest"], alpha),
                                         prev_pt, (px, py), 4)
                    _NS_aelyrion._aaline(surface,
                                         (*_NS_aelyrion.PALETTE["energy_mid"], alpha),
                                         prev_pt, (px, py), 2)
                    _NS_aelyrion._aaline(surface,
                                         (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                         prev_pt, (px, py), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_aelyrion.PALETTE["energy_shine"], alpha),
                                     (px, py, 1, 1))
                prev_pt = (px, py)
        # Sparks at leading edge
        if facing > 0:
            lead_angle = -math.pi * 0.75 + math.pi * t
        else:
            lead_angle = -math.pi * 0.25 - math.pi * t
        for i in range(8):
            spark_r = 22 + i
            sx = arc_cx + int(math.cos(lead_angle) * spark_r)
            sy = arc_cy + int(math.sin(lead_angle) * spark_r)
            alpha = _NS_aelyrion._alpha(220 * (1 - i / 8))
            pygame.draw.rect(surface, (*_NS_aelyrion.PALETTE["energy_hot"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_aelyrion.PALETTE["energy_shine"], alpha), (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_hover_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, int((12 - radius) * 15 * pulse))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 12, 160), (5, 8, 110, 10))
        pygame.draw.ellipse(shadow, (20, 40, 90, 100), (15, 10, 90, 7))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_hover_energy(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        mist = pygame.Surface((140, 40), pygame.SRCALPHA)
        for radius in range(30, 3, -3):
            alpha = _NS_aelyrion._alpha((30 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_aelyrion.PALETTE["energy_dark"], alpha),
                    (70 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_aelyrion._alpha((18 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_aelyrion.PALETTE["energy_mid"], alpha),
                    (70 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 8))
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24)):
            t = (phase * 0.4 + i * 0.14) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 2)
            sy = cy + 4 - int(t * 20)
            alpha = _NS_aelyrion._alpha(240 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_dark"], alpha), (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_aelyrion.PALETTE["energy_light"], alpha), (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_aelyrion.PALETTE["energy_shine"], alpha), (sx, sy - 2, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_aelyrion._alpha(180 - i * 30)
                if alpha <= 0:
                    continue
                _NS_aelyrion._aacircle(surface,
                                       (*_NS_aelyrion.PALETTE["energy_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_aelyrion._aacircle(surface,
                                       (*_NS_aelyrion.PALETTE["energy_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_divine_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_aelyrion._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_aelyrion._aacircle(aura,
                                       (*_NS_aelyrion.PALETTE["energy_dark"], alpha),
                                       (100, 90), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_aelyrion._alpha((50 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_aelyrion._aacircle(aura,
                                       (*_NS_aelyrion.PALETTE["energy_mid"], alpha),
                                       (100, 90), radius)
        for radius in range(25, 5, -3):
            alpha = _NS_aelyrion._alpha((25 - radius) * 2 * pulse)
            if alpha > 0:
                _NS_aelyrion._aacircle(aura,
                                       (*_NS_aelyrion.PALETTE["holy_dim"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_aelyrion.PALETTE["energy_light"] if i % 2 else _NS_aelyrion.PALETTE["holy_bright"]
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_aelyrion.PALETTE["energy_dark"], 200),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_aelyrion.PALETTE["energy_darkest"], 220),
                            (14, 18, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_aelyrion.PALETTE["energy_mid"], 230),
                            (25, 20, 110, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_aelyrion.PALETTE["energy_light"], 180),
                            (40, 22, 80, 12), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_aelyrion.PALETTE["energy_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_aelyrion.PALETTE["energy_hot"],
                                 _NS_aelyrion._alpha(150 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q: THORNED RAY
    # ============================================================
    def _draw_thorned_ray(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_aelyrion._target_position(boss, x, y)
        start_x = x + facing * 26
        start_y = y - 4
        if progress < 0.2:
            t = progress / 0.2
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_aelyrion._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_aelyrion._aacircle(surface,
                                       (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                       (start_x, start_y), r)
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["energy_mid"],
                                   (start_x, start_y), max(1, cr - 1))
            _NS_aelyrion._aacircle(surface, _NS_aelyrion.PALETTE["energy_shine"],
                                   (start_x, start_y), max(1, cr - 3))
        elif progress < 0.75:
            t = (progress - 0.2) / 0.55
            intensity = math.sin(t * math.pi)
            beam_end_x = tx
            beam_end_y = ty
            for width, color_key, alpha_base in [
                (12, "energy_darkest", 100),
                (8, "energy_dark", 140),
                (5, "energy_mid", 180),
                (3, "energy_light", 220),
                (1, "energy_shine", 255),
            ]:
                actual_alpha = _NS_aelyrion._alpha(alpha_base * intensity)
                _NS_aelyrion._aaline(surface,
                                     (*_NS_aelyrion.PALETTE[color_key], actual_alpha),
                                     (start_x, start_y), (beam_end_x, beam_end_y), width)
            beam_len = math.hypot(beam_end_x - start_x, beam_end_y - start_y)
            steps = max(4, int(beam_len / 15))
            for i in range(steps):
                st = i / steps + (phase * 0.5) % (1 / steps)
                sx = int(start_x + (beam_end_x - start_x) * st)
                sy = int(start_y + (beam_end_y - start_y) * st)
                offset = math.sin(phase * 4 + i) * 3
                perp_ang = math.atan2(beam_end_y - start_y, beam_end_x - start_x) + math.pi / 2
                sx += int(math.cos(perp_ang) * offset)
                sy += int(math.sin(perp_ang) * offset)
                pygame.draw.rect(surface,
                                 (*_NS_aelyrion.PALETTE["energy_hot"],
                                  _NS_aelyrion._alpha(240 * intensity)),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_aelyrion.PALETTE["energy_shine"],
                                  _NS_aelyrion._alpha(240 * intensity)),
                                 (sx, sy, 1, 1))
            burst_r = int(8 + t * 12)
            burst_alpha = _NS_aelyrion._alpha(240 * intensity)
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_dark"], burst_alpha),
                                   (tx, ty), burst_r + 2, 3)
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_mid"], burst_alpha),
                                   (tx, ty), burst_r)
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_light"], burst_alpha),
                                   (tx, ty), max(1, burst_r - 3))
            _NS_aelyrion._aacircle(surface,
                                   (*_NS_aelyrion.PALETTE["energy_shine"], burst_alpha),
                                   (tx, ty), max(1, burst_r - 6))
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.5
                ex = tx + int(math.cos(ang) * burst_r)
                ey = ty + int(math.sin(ang) * burst_r)
                pygame.draw.line(surface,
                                 (*_NS_aelyrion.PALETTE["energy_hot"], burst_alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface,
                                 (*_NS_aelyrion.PALETTE["energy_shine"], burst_alpha),
                                 (ex, ey, 2, 2))
        else:
            t = (progress - 0.75) / 0.25
            alpha = _NS_aelyrion._alpha(180 * (1 - t))
            _NS_aelyrion._aaline(surface,
                                 (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                 (start_x, start_y), (tx, ty), 2)
    # ============================================================
    # SKILL W: ANCIENT GUARDIAN
    # ============================================================
    def _draw_guardian_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aelyrion._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 2.5))
        if r > 3:
            pulse = math.sin(phase * 1.5) * 0.2 + 0.8
            pygame.draw.ellipse(surface,
                                (*_NS_aelyrion.PALETTE["energy_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_aelyrion.PALETTE["energy_dark"], 200),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_aelyrion.PALETTE["energy_mid"],
                                 _NS_aelyrion._alpha(180 * pulse)),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 1)
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.2
                rx = tx + int(math.cos(ang) * r)
                ry = ty + int(math.sin(ang) * r * 0.4)
                spike_h = int(6 + math.sin(phase * 2 + i) * 3)
                _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["energy_darkest"], [
                    (rx - 2, ry), (rx + 2, ry), (rx, ry - spike_h),
                ])
                _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["energy_mid"], [
                    (rx - 1, ry), (rx + 1, ry), (rx, ry - spike_h + 1),
                ])
                pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_shine"],
                                 (rx, ry - spike_h, 1, 1))
    def _draw_guardian_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aelyrion._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return
        t = (progress - 0.3) / 0.7
        emerge_y = ty - int(t * 30)
        fist_size = int(15 + t * 8)
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["shadow_deep"], [
            (tx - fist_size + 2, emerge_y - 6 + 2),
            (tx + fist_size + 2, emerge_y - 6 + 2),
            (tx + fist_size + 2, emerge_y + 12 + 2),
            (tx - fist_size + 2, emerge_y + 12 + 2),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_darkest"], [
            (tx - fist_size, emerge_y - 6),
            (tx + fist_size, emerge_y - 6),
            (tx + fist_size, emerge_y + 12),
            (tx - fist_size, emerge_y + 12),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_dark"], [
            (tx - fist_size + 2, emerge_y - 4),
            (tx + fist_size - 2, emerge_y - 4),
            (tx + fist_size - 2, emerge_y + 10),
            (tx - fist_size + 2, emerge_y + 10),
        ])
        _NS_aelyrion._poly(surface, _NS_aelyrion.PALETTE["steel_mid"], [
            (tx - fist_size + 4, emerge_y - 2),
            (tx + fist_size - 4, emerge_y - 2),
            (tx + fist_size - 4, emerge_y + 8),
            (tx - fist_size + 4, emerge_y + 8),
        ])
        for side in (-1, 1):
            ex = tx + side * (fist_size // 2)
            ey = emerge_y
            for r in range(4, 0, -1):
                alpha = _NS_aelyrion._alpha(150 * (4 - r) / 4)
                _NS_aelyrion._aacircle(surface,
                                       (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_aelyrion.PALETTE["energy_shine"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_mid"],
                         (tx - fist_size, emerge_y - 6, fist_size * 2, 2))
        pygame.draw.rect(surface, _NS_aelyrion.PALETTE["gold_shine"],
                         (tx - 2, emerge_y - 6, 4, 1))
        for i in range(6):
            ang = i * math.pi / 3 + phase * 0.5
            outer_r = 40
            ox = tx + int(math.cos(ang) * outer_r)
            oy = ty + int(math.sin(ang) * outer_r * 0.5)
            alpha = _NS_aelyrion._alpha(220)
            pygame.draw.line(surface,
                             (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                             (ox, oy), (tx, ty), 1)
            pygame.draw.rect(surface,
                             (*_NS_aelyrion.PALETTE["energy_hot"], alpha),
                             (int((ox + tx) / 2), int((oy + ty) / 2), 2, 2))
    # ============================================================
    # SKILL E: GUARD CHARGE
    # ============================================================
    def _draw_dash_trail(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        trail_len = 60
        for i in range(8):
            t = i / 8
            tx = x - facing * int(trail_len * t)
            ty = y + int(math.sin(t * math.pi) * 3)
            alpha = _NS_aelyrion._alpha(200 * (1 - t) * (1 - progress * 0.5))
            _NS_aelyrion._aaline(surface,
                                 (*_NS_aelyrion.PALETTE["energy_dark"], alpha),
                                 (tx, ty), (tx + facing * 8, ty), 4)
            _NS_aelyrion._aaline(surface,
                                 (*_NS_aelyrion.PALETTE["energy_mid"], alpha),
                                 (tx, ty), (tx + facing * 8, ty), 2)
            _NS_aelyrion._aaline(surface,
                                 (*_NS_aelyrion.PALETTE["energy_light"], alpha),
                                 (tx, ty), (tx + facing * 8, ty), 1)
    def _draw_dash_shield(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            return
        t = (progress - 0.5) / 0.5
        r = int(30 + t * 15)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i, (thick, a) in enumerate([(3, 120), (2, 160), (1, 220)]):
            _NS_aelyrion._aacircle(bubble,
                                   (*_NS_aelyrion.PALETTE["energy_dark"],
                                    _NS_aelyrion._alpha(a * pulse)),
                                   center, r - i, thick)
            _NS_aelyrion._aacircle(bubble,
                                   (*_NS_aelyrion.PALETTE["energy_mid"],
                                    _NS_aelyrion._alpha(a * pulse)),
                                   center, r - i - 1, 1)
        for i in range(6):
            ang = i * math.pi / 3 + phase * 0.5
            hx1 = center[0] + int(math.cos(ang) * (r - 4))
            hy1 = center[1] + int(math.sin(ang) * (r - 4))
            hx2 = center[0] + int(math.cos(ang + math.pi / 3) * (r - 4))
            hy2 = center[1] + int(math.sin(ang + math.pi / 3) * (r - 4))
            pygame.draw.line(bubble,
                             (*_NS_aelyrion.PALETTE["energy_light"],
                              _NS_aelyrion._alpha(200 * pulse)),
                             (hx1, hy1), (hx2, hy2), 1)
        for i in range(16):
            ang = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(ang) * r)
            sy = center[1] + int(math.sin(ang) * r)
            pygame.draw.rect(bubble, _NS_aelyrion.PALETTE["energy_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_aelyrion.PALETTE["energy_shine"], (sx, sy, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
    # ============================================================
    # SKILL R: DIVINE GATE
    # ============================================================
    def _draw_divine_gate_ground(surface, boss, x, y, timer, phase):
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        r = int(70 * min(1.0, progress * 2))
        if r > 3:
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 3, 240), (6, 2, 200), (12, 1, 160),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_aelyrion.PALETTE["energy_dark"],
                                     _NS_aelyrion._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 45 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
            for i in range(12):
                ang = i * math.pi / 6 + phase * 0.3
                x1 = x + int(math.cos(ang) * r * 0.5)
                y1 = y + 45 + int(math.sin(ang) * r * 0.2)
                x2 = x + int(math.cos(ang) * r)
                y2 = y + 45 + int(math.sin(ang) * r * 0.4)
                pygame.draw.line(surface,
                                 (*_NS_aelyrion.PALETTE["energy_light"], 220),
                                 (x1, y1), (x2, y2), 1)
                pygame.draw.rect(surface,
                                 (*_NS_aelyrion.PALETTE["energy_shine"], 240),
                                 (x2, y2, 2, 2))
    def _draw_divine_gate_wings(surface, boss, x, y, timer, phase):
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            t = progress / 0.2
            pillar_h = int(t * 120)
            pillar_alpha = _NS_aelyrion._alpha(220 * t)
            for width, color_key in [
                (16, "energy_dark"), (10, "energy_mid"),
                (6, "energy_light"), (2, "energy_shine"),
            ]:
                pygame.draw.rect(surface,
                                 (*_NS_aelyrion.PALETTE[color_key], pillar_alpha),
                                 (x - width // 2, y - pillar_h + 30, width, pillar_h))
            return
        t = min(1.0, (progress - 0.2) / 0.8)
        wing_open = t
        wing_beat = math.sin(phase * 1.5) * 3
        for side in (-1, 1):
            bx = x + side * 8
            by = y - 12
            wing_span = int(45 * wing_open)
            wing_height = int(30 * wing_open)
            if wing_span < 5:
                continue
            wing_pts = [
                (bx, by),
                (bx + side * wing_span, by - wing_height + int(wing_beat)),
                (bx + side * (wing_span - 5), by - wing_height // 3),
                (bx + side * (wing_span - 15), by + wing_height // 4),
                (bx + side * 5, by + wing_height // 3),
            ]
            wing_surf = pygame.Surface((120, 100), pygame.SRCALPHA)
            offset_x = bx - 60
            offset_y = by - 50
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in wing_pts]
            _NS_aelyrion._poly(wing_surf,
                               (*_NS_aelyrion.PALETTE["steel_darkest"], 220),
                               local_pts)
            _NS_aelyrion._poly(wing_surf,
                               (*_NS_aelyrion.PALETTE["steel_dark"], 220),
                               [(int(p[0] * 0.9 + local_pts[0][0] * 0.1),
                                 int(p[1] * 0.9 + local_pts[0][1] * 0.1))
                                for p in local_pts])
            # Feather rows
            for row in range(4):
                row_t = (row + 1) / 4
                for f in range(6):
                    ft = f / 6
                    fx_end = int(local_pts[0][0] + (local_pts[1][0] - local_pts[0][0]) * ft
                                 + (local_pts[4][0] - local_pts[0][0]) * (1 - ft) * (1 - row_t))
                    fy_end = int(local_pts[0][1] + (local_pts[1][1] - local_pts[0][1]) * ft
                                 + (local_pts[4][1] - local_pts[0][1]) * (1 - ft) * (1 - row_t))
                    fx_start = int(local_pts[0][0] * (1 - row_t * 0.3) + fx_end * (row_t * 0.3))
                    fy_start = int(local_pts[0][1] * (1 - row_t * 0.3) + fy_end * (row_t * 0.3))
                    color_key = ["steel_dark", "steel_mid", "steel_light", "steel_shine"][row]
                    pygame.draw.line(wing_surf,
                                     (*_NS_aelyrion.PALETTE[color_key], 240),
                                     (fx_start, fy_start), (fx_end, fy_end), 2)
                    pygame.draw.line(wing_surf,
                                     (*_NS_aelyrion.PALETTE["steel_shine"], 200),
                                     (fx_start, fy_start), (fx_end, fy_end), 1)
            # Blue leading edge glow
            pygame.draw.line(wing_surf,
                             (*_NS_aelyrion.PALETTE["energy_light"], 240),
                             local_pts[0], local_pts[1], 2)
            pygame.draw.line(wing_surf,
                             (*_NS_aelyrion.PALETTE["energy_shine"], 255),
                             local_pts[0], local_pts[1], 1)
            _NS_aelyrion._aacircle(wing_surf,
                                   (*_NS_aelyrion.PALETTE["energy_hot"], 240),
                                   local_pts[1], 3)
            pygame.draw.rect(wing_surf, _NS_aelyrion.PALETTE["energy_shine"],
                             (local_pts[1][0], local_pts[1][1], 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
        # Falling feathers
        for i in range(6):
            t_fall = (phase * 0.4 + i * 0.15) % 1.0
            fx = x - 30 + i * 10 + int(math.sin(phase + i) * 5)
            fy = y - 30 + int(t_fall * 60)
            alpha = _NS_aelyrion._alpha(220 * (1 - t_fall))
            pygame.draw.rect(surface,
                             (*_NS_aelyrion.PALETTE["steel_light"], alpha),
                             (fx, fy, 2, 3))
            pygame.draw.rect(surface,
                             (*_NS_aelyrion.PALETTE["energy_shine"], alpha),
                             (fx, fy, 1, 1))
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# (avoids "unbound method" issues without @staticmethod boilerplate)
# ============================================================
for _attr_name in list(vars(_NS_aelyrion).keys()):
    _attr = vars(_NS_aelyrion)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_aelyrion, _attr_name, staticmethod(_attr))



# ====================================================================
# KAERVOSTH (STORMBLADE KNIGHT) - Mini Boss
# ====================================================================

class _NS_kaervosth:
    """Namespace kaervosth - HD stormblade knight boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Steel-blue armor
        "steel_darkest": (15, 20, 35),
        "steel_dark": (45, 60, 90),
        "steel_mid": (95, 115, 155),
        "steel_light": (170, 190, 225),
        "steel_shine": (230, 240, 255),
        # Gold trim (royal knight)
        "gold_darkest": (50, 35, 8),
        "gold_dark": (120, 90, 30),
        "gold_mid": (200, 160, 60),
        "gold_light": (245, 215, 115),
        "gold_shine": (255, 240, 185),
        # Storm blue energy (sword, lightning, hammer)
        "storm_darkest": (5, 20, 60),
        "storm_dark": (20, 65, 140),
        "storm_mid": (60, 140, 235),
        "storm_light": (130, 200, 255),
        "storm_hot": (200, 235, 255),
        "storm_shine": (240, 250, 255),
        # Divine gold energy (God's Strength / Ultimate)
        "divine_darkest": (60, 40, 5),
        "divine_dark": (150, 100, 20),
        "divine_mid": (240, 190, 50),
        "divine_light": (255, 230, 130),
        "divine_hot": (255, 245, 200),
        "divine_shine": (255, 255, 240),
        # Cape (dark red / burgundy)
        "cape_darkest": (35, 8, 12),
        "cape_dark": (75, 20, 30),
        "cape_mid": (135, 40, 55),
        "cape_light": (185, 70, 85),
        # Leather / brown accents
        "leather_dark": (40, 25, 15),
        "leather_mid": (75, 50, 30),
        "leather_light": (125, 90, 55),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        # Helm slit eye
        "eye_dark": (8, 25, 60),
        "eye_mid": (60, 140, 220),
        "eye_glow": (180, 230, 255),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaervosth._clamp(color)
        if _NS_kaervosth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaervosth._clamp(color)
        if _NS_kaervosth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_kaervosth._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_kaervosth._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_kaervosth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaervosth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaervosth._detect_moving(boss)
        _NS_kaervosth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kae_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Determine buff mode (E or R active = glowing aura)
        buff_active = active_skill in ("e", "r")
        # Ambient
        _NS_kaervosth._draw_knight_aura(surface, x, y, pulse, buff_active,
                                        is_ultimate=(active_skill == "r"))
        _NS_kaervosth._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_kaervosth._draw_cleave_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaervosth._draw_gods_strength_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaervosth._draw_ultimate_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_kaervosth._draw_attack_pose(surface, boss, x, y, buff_active,
                                            active_skill == "r")
        elif moving:
            _NS_kaervosth._draw_float_move(surface, boss, x, y, buff_active,
                                           active_skill == "r")
        else:
            _NS_kaervosth._draw_float_idle(surface, boss, x, y, buff_active,
                                           active_skill == "r")
        # Foreground FX
        if active_skill == "q":
            _NS_kaervosth._draw_storm_hammer(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaervosth._draw_cleave_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaervosth._draw_gods_strength_aura(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaervosth._draw_ultimate_aura(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kae_previous_timer", 0))
        active = bool(getattr(boss, "_kae_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kae_attack_active = True
            boss._kae_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kae_attack_frame = int(getattr(boss, "_kae_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kae_attack_active = False
            boss._kae_attack_frame = 0
            active = False
        boss._kae_previous_timer = timer
        boss._kae_attack_progress = (
            min(1.0, getattr(boss, "_kae_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kae_last_x"):
            boss._kae_last_x = boss.x
            boss._kae_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kae_last_x)
        dy = abs(boss.y - boss._kae_last_y)
        boss._kae_last_x = boss.x
        boss._kae_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y, buff=False, ult=False):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_kaervosth._draw_hover_shadow(surface, x, y + 55, boss.pulse)
        _NS_kaervosth._draw_hover_energy(surface, x, y + 42, boss.pulse, ult=ult)
        _NS_kaervosth._draw_body(surface, x + sway, y + bob,
                                 boss.direction, boss.pulse, "idle",
                                 buff=buff, ult=ult)
    def _draw_float_move(surface, boss, x, y, buff=False, ult=False):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_kaervosth._draw_hover_shadow(surface, x + sway, y + 55, phase)
        _NS_kaervosth._draw_hover_energy(surface, x + sway, y + 42, phase,
                                         trail=True, facing=boss.direction, ult=ult)
        _NS_kaervosth._draw_body(surface, x + sway, y + bob,
                                 boss.direction, phase, "move",
                                 buff=buff, ult=ult)
    def _draw_attack_pose(surface, boss, x, y, buff=False, ult=False):
        progress = getattr(boss, "_kae_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back → forward swing → recover
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 18)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(13 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_kaervosth._draw_hover_shadow(surface, x + lunge, y + 55, boss.pulse)
        _NS_kaervosth._draw_hover_energy(surface, x + lunge, y + 42, boss.pulse,
                                         intense=True, ult=ult)
        _NS_kaervosth._draw_body(surface, x + lunge, y - lift,
                                 boss.direction, boss.pulse, "attack", progress,
                                 buff=buff, ult=ult)
        _NS_kaervosth._draw_greatsword_swing_fx(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                   buff=False, ult=False):
        # Ultimate: draw expanding golden aura around body first
        if ult:
            _NS_kaervosth._draw_ult_body_glow(surface, cx, cy, phase)
        # Cape behind
        _NS_kaervosth._draw_cape(surface, cx, cy, facing, phase, action)
        # Legs (armored greaves)
        _NS_kaervosth._draw_legs(surface, cx, cy + 22, facing, phase)
        # Torso armor
        _NS_kaervosth._draw_torso(surface, cx, cy, facing, phase, buff, ult)
        # Shoulders (spiky pauldrons)
        _NS_kaervosth._draw_shoulders(surface, cx, cy - 8, facing, phase, ult)
        # Arms (with greatsword grip)
        _NS_kaervosth._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head (helm with slit eye + horns)
        _NS_kaervosth._draw_head(surface, cx, cy - 24, facing, phase, ult)
        # GREATSWORD (last so it's on top)
        _NS_kaervosth._draw_greatsword(surface, cx, cy, facing, phase, action,
                                       attack_progress, buff, ult)
        # Buff aura sparkles
        if buff:
            _NS_kaervosth._draw_body_sparkles(surface, cx, cy, phase, ult)
    def _draw_ult_body_glow(surface, cx, cy, phase):
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Massive golden radial glow
        glow = pygame.Surface((160, 160), pygame.SRCALPHA)
        for r in range(70, 5, -4):
            alpha = _NS_kaervosth._alpha((70 - r) * 2 * pulse)
            _NS_kaervosth._aacircle(glow,
                                    (*_NS_kaervosth.PALETTE["divine_mid"], alpha),
                                    (80, 80), r)
        for r in range(45, 5, -3):
            alpha = _NS_kaervosth._alpha((45 - r) * 3 * pulse)
            _NS_kaervosth._aacircle(glow,
                                    (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                                    (80, 80), r)
        surface.blit(glow, (cx - 80, cy - 80))
        # Radial light rays
        for i in range(8):
            ang = phase * 0.5 + i * math.pi / 4
            for length_mult in (0.7, 1.0):
                end_x = cx + int(math.cos(ang) * 70 * length_mult)
                end_y = cy + int(math.sin(ang) * 70 * length_mult)
                pygame.draw.line(surface,
                                 (*_NS_kaervosth.PALETTE["divine_hot"],
                                  _NS_kaervosth._alpha(180 * pulse)),
                                 (cx, cy), (end_x, end_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_kaervosth.PALETTE["divine_shine"],
                                  _NS_kaervosth._alpha(220 * pulse)),
                                 (cx, cy), (end_x, end_y), 1)
    # ---------- CAPE ----------
    def _draw_cape(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 3
        if action == "move":
            sway = math.sin(phase * 1.2) * 6
        back_dir = -facing
        base_x = cx + back_dir * 8
        base_y = cy - 8
        # Cape shape (long trapezoid)
        top_a = (base_x - 5, base_y)
        top_b = (base_x + 10 * back_dir, base_y)
        bot_a = (base_x - 12 + int(sway), base_y + 38)
        bot_b = (base_x + 18 * back_dir + int(sway), base_y + 34)
        mid_a = (base_x - 9 + int(sway * 0.5), base_y + 20)
        mid_b = (base_x + 15 * back_dir + int(sway * 0.5), base_y + 19)
        # Shadow
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
            (top_a[0] + 2, top_a[1] + 2), (top_b[0] + 2, top_b[1] + 2),
            (bot_b[0] + 2, bot_b[1] + 2), (bot_a[0] + 2, bot_a[1] + 2),
        ])
        # Base
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["cape_darkest"],
                            [top_a, top_b, mid_b, bot_b, bot_a, mid_a])
        # Mid tone (interior fold)
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["cape_dark"], [
            (top_a[0] + 1, top_a[1] + 2), (top_b[0] - 1 * back_dir, top_b[1] + 2),
            (mid_b[0] - 2 * back_dir, mid_b[1]),
            (mid_a[0] + 2, mid_a[1]),
        ])
        # Highlight fold
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["cape_mid"], [
            (top_a[0] + 2, top_a[1] + 3), (top_b[0] - 2 * back_dir, top_b[1] + 3),
            (int((top_b[0] + mid_b[0]) / 2), int((top_b[1] + mid_b[1]) / 2)),
            (int((top_a[0] + mid_a[0]) / 2), int((top_a[1] + mid_a[1]) / 2)),
        ])
        # Highlight edge
        pygame.draw.line(surface, _NS_kaervosth.PALETTE["cape_light"],
                         top_a, mid_a, 1)
        # Gold trim along bottom edge
        for i in range(6):
            t = i / 5
            px = int(bot_a[0] + (bot_b[0] - bot_a[0]) * t)
            py = int(bot_a[1] + (bot_b[1] - bot_a[1]) * t)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_dark"],
                             (px - 1, py, 3, 2))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (px, py, 1, 2))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                             (px, py, 1, 1))
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase):
        for side in (-1, 1):
            lx = cx + side * 5
            ly = cy
            # Thigh plate
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
                (lx - 4 + 1, ly + 1), (lx + 4 + 1, ly + 1),
                (lx + 5 + 1, ly + 12 + 1), (lx - 5 + 1, ly + 12 + 1),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
                (lx - 4, ly), (lx + 4, ly), (lx + 5, ly + 12), (lx - 5, ly + 12),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
                (lx - 3, ly + 1), (lx + 3, ly + 1),
                (lx + 4, ly + 11), (lx - 4, ly + 11),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
                (lx - 2, ly + 2), (lx + 2, ly + 2),
                (lx + 3, ly + 10), (lx - 3, ly + 10),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["steel_light"],
                             (lx, ly + 2), (lx, ly + 10), 1)
            # Gold trim
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_dark"],
                             (lx - 4, ly), (lx + 4, ly), 1)
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (lx - 3, ly), (lx + 3, ly), 1)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                             (lx - 1, ly, 2, 1))
            # Knee cap (round armor)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_darkest"],
                                    (lx, ly + 12), 4)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_dark"],
                                    (lx, ly + 12), 3)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_mid"],
                                    (lx, ly + 12), 2)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (lx, ly + 12, 1, 1))
            # Sabaton (armored foot)
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
                (lx - 4, ly + 15), (lx + 4, ly + 15),
                (lx + 6, ly + 18), (lx - 3, ly + 18),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
                (lx - 3, ly + 16), (lx + 3, ly + 16),
                (lx + 5, ly + 17), (lx - 2, ly + 17),
            ])
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_dark"],
                             (lx + 2, ly + 17, 2, 1))
    # ---------- TORSO ----------
    def _draw_torso(surface, cx, cy, facing, phase, buff, ult):
        # Broad muscular chest plate
        pts = [
            (cx - 11, cy - 8),
            (cx - 14, cy - 3),
            (cx - 12, cy + 8),
            (cx - 9, cy + 16),
            (cx + 9, cy + 16),
            (cx + 12, cy + 8),
            (cx + 14, cy - 3),
            (cx + 11, cy - 8),
        ]
        # Shadow
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in pts])
        # Base plate
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], pts)
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
            (cx - 10, cy - 7), (cx - 13, cy - 3), (cx - 11, cy + 7),
            (cx - 8, cy + 15), (cx + 8, cy + 15),
            (cx + 11, cy + 7), (cx + 13, cy - 3), (cx + 10, cy - 7),
        ])
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
            (cx - 8, cy - 5), (cx - 11, cy - 1), (cx - 9, cy + 5),
            (cx - 6, cy + 12), (cx + 6, cy + 12),
            (cx + 9, cy + 5), (cx + 11, cy - 1), (cx + 8, cy - 5),
        ])
        # Central chest ridge (raised armor plating)
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_light"], [
            (cx - 3, cy - 4), (cx + 3, cy - 4),
            (cx + 4, cy + 4), (cx - 4, cy + 4),
        ])
        # Sheen
        pygame.draw.line(surface, _NS_kaervosth.PALETTE["steel_shine"],
                         (cx - 1, cy - 3), (cx - 1, cy + 3), 1)
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                         (cx - 1, cy - 2, 1, 1))
        # Gold ornate center emblem
        gold_col = _NS_kaervosth.PALETTE["divine_light"] if ult \
            else _NS_kaervosth.PALETTE["gold_mid"]
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["gold_dark"], [
            (cx - 4, cy), (cx + 4, cy),
            (cx + 3, cy + 4), (cx - 3, cy + 4),
        ])
        _NS_kaervosth._poly(surface, gold_col, [
            (cx - 3, cy + 1), (cx + 3, cy + 1),
            (cx + 2, cy + 3), (cx - 2, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                         (cx, cy + 2, 1, 1))
        # Vertical armor slats (chest lines)
        for offset in (-6, -2, 2, 6):
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["steel_darkest"],
                             (cx + offset, cy - 4),
                             (cx + offset, cy + 10), 1)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_light"],
                             (cx + offset - 1, cy - 3, 1, 1))
        # Belt (bottom of torso)
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["leather_dark"],
                         (cx - 10, cy + 12, 20, 4))
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["leather_mid"],
                         (cx - 9, cy + 12, 18, 2))
        # Gold buckle
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_darkest"],
                         (cx - 3, cy + 12, 6, 4))
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                         (cx - 2, cy + 13, 4, 2))
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                         (cx - 1, cy + 13, 2, 1))
    # ---------- SHOULDERS ----------
    def _draw_shoulders(surface, cx, cy, facing, phase, ult=False):
        for side in (-1, 1):
            sx = cx + side * 13
            sy = cy
            # Large spiky pauldron
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
                (sx - 7 + 2, sy - 4 + 2), (sx + 8 + 2, sy - 4 + 2),
                (sx + 9 + 2, sy + 6 + 2), (sx - 8 + 2, sy + 6 + 2),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
                (sx - 7, sy - 4), (sx + 8, sy - 4),
                (sx + 9, sy + 6), (sx - 8, sy + 6),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
                (sx - 6, sy - 3), (sx + 7, sy - 3),
                (sx + 8, sy + 5), (sx - 7, sy + 5),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
                (sx - 4, sy - 2), (sx + 5, sy - 2),
                (sx + 6, sy + 3), (sx - 5, sy + 3),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["steel_light"],
                             (sx - 2, sy - 1), (sx - 2, sy + 3), 1)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                             (sx - 1, sy - 1, 1, 1))
            # Spike on top of pauldron
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
                (sx - 2 + 1, sy - 4 + 1),
                (sx + 3 + 1, sy - 4 + 1),
                (sx + 1 + 1, sy - 10 + 1),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
                (sx - 2, sy - 4), (sx + 3, sy - 4), (sx + 1, sy - 10),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
                (sx - 1, sy - 4), (sx + 2, sy - 4), (sx + 1, sy - 9),
            ])
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_light"],
                             (sx + 1, sy - 9, 1, 1))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                             (sx + 1, sy - 10, 1, 1))
            # Gold trim edge
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_dark"],
                             (sx - 7, sy - 4), (sx + 8, sy - 4), 1)
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (sx - 6, sy - 4), (sx + 7, sy - 4), 1)
            # Ultimate: golden rim glow
            if ult:
                pulse = math.sin(phase * 3) * 0.3 + 0.7
                for r in range(5, 0, -1):
                    alpha = _NS_kaervosth._alpha(120 * (5 - r) / 5 * pulse)
                    _NS_kaervosth._aacircle(surface,
                                            (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                                            (sx, sy - 8), r)
    # ---------- ARMS (with two-handed greatsword grip) ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        # Both hands grip the greatsword (two-handed)
        for side, is_sword_side in ((-1, False), (1, True)):
            base_x = cx + side * 12
            base_y = cy - 4
            is_dominant = (side * facing > 0)
            if action == "attack":
                if attack_progress < 0.35:
                    # Wind up: BOTH arms lift sword UP and BACK
                    t = attack_progress / 0.35
                    if is_dominant:
                        elbow_offset_x = int(-8 * facing)
                        elbow_offset_y = int(-10 - t * 2)
                        hand_offset_x = int(-12 * facing)
                        hand_offset_y = int(-16)
                    else:
                        # Support hand
                        elbow_offset_x = int(-4 * facing)
                        elbow_offset_y = int(-8 - t * 2)
                        hand_offset_x = int(-8 * facing)
                        hand_offset_y = int(-14)
                elif attack_progress < 0.6:
                    # Swing DOWN-FORWARD
                    t = (attack_progress - 0.35) / 0.25
                    if is_dominant:
                        elbow_offset_x = int((-8 + t * 16) * facing)
                        elbow_offset_y = int(-12 + t * 18)
                        hand_offset_x = int((-12 + t * 26) * facing)
                        hand_offset_y = int(-16 + t * 22)
                    else:
                        elbow_offset_x = int((-4 + t * 10) * facing)
                        elbow_offset_y = int(-10 + t * 16)
                        hand_offset_x = int((-8 + t * 18) * facing)
                        hand_offset_y = int(-14 + t * 20)
                else:
                    # Recovery
                    t = (attack_progress - 0.6) / 0.4
                    if is_dominant:
                        elbow_offset_x = int((8 - t * 4) * facing)
                        elbow_offset_y = int(6 - t * 2)
                        hand_offset_x = int((14 - t * 6) * facing)
                        hand_offset_y = int(6 + t * 1)
                    else:
                        elbow_offset_x = int((6 - t * 3) * facing)
                        elbow_offset_y = int(6 - t * 2)
                        hand_offset_x = int((10 - t * 4) * facing)
                        hand_offset_y = int(6 + t * 1)
            else:
                # Idle: hold sword in front, resting stance
                swing = math.sin(phase * 0.5 + side) * 0.1
                if is_dominant:
                    elbow_offset_x = int(4 * facing + math.sin(swing) * 2)
                    elbow_offset_y = 4
                    hand_offset_x = int(10 * facing)
                    hand_offset_y = 8
                else:
                    elbow_offset_x = int(2 * facing)
                    elbow_offset_y = 4
                    hand_offset_x = int(6 * facing)
                    hand_offset_y = 6
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                                  (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 7)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_darkest"],
                                  (base_x, base_y), (elbow_x, elbow_y), 6)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_dark"],
                                  (base_x, base_y), (elbow_x, elbow_y), 4)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_mid"],
                                  (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_light"],
                                  (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow (armored)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_darkest"],
                                    (elbow_x, elbow_y), 4)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_dark"],
                                    (elbow_x, elbow_y), 3)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_mid"],
                                    (elbow_x, elbow_y), 2)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (elbow_x, elbow_y, 1, 1))
            # Forearm
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                                  (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 6)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_darkest"],
                                  (elbow_x, elbow_y), (hand_x, hand_y), 5)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_dark"],
                                  (elbow_x, elbow_y), (hand_x, hand_y), 3)
            _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_mid"],
                                  (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
            # Hand (gauntlet with knuckle plate)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                                    (hand_x + 1, hand_y + 1), 5)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_darkest"],
                                    (hand_x, hand_y), 4)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_dark"],
                                    (hand_x, hand_y), 3)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["steel_mid"],
                                    (hand_x, hand_y), 2)
            # Gold knuckle
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_dark"],
                             (hand_x - 1, hand_y - 1, 3, 2))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (hand_x, hand_y - 1, 2, 1))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                             (hand_x, hand_y - 1, 1, 1))
            if is_sword_side:
                _NS_kaervosth._last_sword_hand = (hand_x, hand_y, 0.0)
            else:
                _NS_kaervosth._last_off_hand = (hand_x, hand_y)
    # ---------- HEAD (helm with slit + crown horns) ----------
    def _draw_head(surface, cx, cy, facing, phase, ult=False):
        # Helm shape (rounded top, narrower jaw)
        helm_pts = [
            (cx - 7, cy - 3),   # left side
            (cx - 8, cy + 1),
            (cx - 6, cy + 6),
            (cx - 3, cy + 9),
            (cx + 3, cy + 9),
            (cx + 6, cy + 6),
            (cx + 8, cy + 1),
            (cx + 7, cy - 3),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        # Shadow
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in helm_pts])
        # Base helm
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], helm_pts)
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
            (cx - 6, cy - 2), (cx - 7, cy + 1),
            (cx - 5, cy + 5), (cx - 2, cy + 8),
            (cx + 2, cy + 8), (cx + 5, cy + 5),
            (cx + 7, cy + 1), (cx + 6, cy - 2),
            (cx + 4, cy - 7), (cx - 4, cy - 7),
        ])
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
            (cx - 4, cy - 1), (cx - 5, cy + 1),
            (cx - 3, cy + 4), (cx - 1, cy + 7),
            (cx + 1, cy + 7), (cx + 3, cy + 4),
            (cx + 5, cy + 1), (cx + 4, cy - 1),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])
        # Highlight on helm
        pygame.draw.line(surface, _NS_kaervosth.PALETTE["steel_light"],
                         (cx - 3 * facing, cy - 4), (cx - 3 * facing, cy + 4), 1)
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                         (cx - 3 * facing, cy - 4, 1, 1))
        # HELM SLIT (eye area) — horizontal opening with glowing blue eye
        slit_y = cy + 1
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                         (cx - 5, slit_y, 11, 2))
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["eye_dark"],
                         (cx - 4, slit_y, 9, 1))
        # Glowing eye (bright dot in slit)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_col = _NS_kaervosth.PALETTE["divine_hot"] if ult else _NS_kaervosth.PALETTE["storm_hot"]
        eye_glow_col = _NS_kaervosth.PALETTE["divine_light"] if ult else _NS_kaervosth.PALETTE["storm_light"]
        # Halo around eye
        for r in range(4, 0, -1):
            alpha = _NS_kaervosth._alpha(120 * (4 - r) / 4 * eye_pulse)
            _NS_kaervosth._aacircle(surface,
                                    (*eye_glow_col, alpha),
                                    (cx + facing * 2, slit_y), r)
        pygame.draw.rect(surface, eye_col,
                         (cx + facing * 2, slit_y, 2, 1))
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["storm_shine"],
                         (cx + facing * 2, slit_y, 1, 1))
        # CROWN HORNS on sides of helm
        _NS_kaervosth._draw_helm_horns(surface, cx, cy - 6, facing, phase, ult)
        # Gold trim on helm forehead
        pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_dark"],
                         (cx - 5, cy - 8), (cx + 5, cy - 8), 1)
        pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_mid"],
                         (cx - 4, cy - 7), (cx + 4, cy - 7), 1)
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                         (cx - 1, cy - 7, 2, 1))
        # Center forehead ornament (jewel)
        jewel_col = _NS_kaervosth.PALETTE["divine_light"] if ult \
            else _NS_kaervosth.PALETTE["storm_light"]
        for r in range(3, 0, -1):
            alpha = _NS_kaervosth._alpha(150 * (3 - r) / 3 * eye_pulse)
            _NS_kaervosth._aacircle(surface,
                                    (*jewel_col, alpha),
                                    (cx, cy - 5), r)
        pygame.draw.rect(surface, jewel_col, (cx, cy - 5, 1, 1))
    def _draw_helm_horns(surface, cx, cy, facing, phase, ult=False):
        # Three horns/spikes: 2 side + 1 center taller
        # Center tall spike
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
            (cx + 1, cy - 6 + 1), (cx - 2 + 1, cy + 1), (cx + 2 + 1, cy + 1),
        ])
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
            (cx, cy - 6), (cx - 2, cy), (cx + 2, cy),
        ])
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
            (cx, cy - 5), (cx - 1, cy), (cx + 1, cy),
        ])
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_light"],
                         (cx, cy - 5, 1, 3))
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                         (cx, cy - 6, 1, 1))
        # Side horns (bigger, curving out)
        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy + 1
            tip_x = cx + side * 9
            tip_y = cy - 5
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
                (base_x - 2 + 1, base_y + 1),
                (base_x + 2 + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
                (base_x - 2, base_y), (base_x + 2, base_y), (tip_x, tip_y),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
                (base_x - 1, base_y), (base_x + 1, base_y),
                (tip_x - side, tip_y + 1),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
                (base_x, base_y), (base_x + side, base_y - 1),
                (tip_x - side * 2, tip_y + 2),
            ])
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                             (tip_x, tip_y, 1, 1))
            # Ultimate glow on horn tips
            if ult:
                pulse = math.sin(phase * 3) * 0.3 + 0.7
                for r in range(3, 0, -1):
                    alpha = _NS_kaervosth._alpha(150 * (3 - r) / 3 * pulse)
                    _NS_kaervosth._aacircle(surface,
                                            (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                                            (tip_x, tip_y), r)
    # ---------- GREATSWORD (massive two-handed blade) ----------
    def _draw_greatsword(surface, cx, cy, facing, phase, action, attack_progress,
                          buff=False, ult=False):
        hand_data = getattr(_NS_kaervosth, "_last_sword_hand", None)
        if hand_data is None:
            hx, hy = cx + facing * 22, cy + 6
        else:
            hx, hy, _ = hand_data
        blade_len = 44  # LONG greatsword
        # SWING FROM TOP (overhead chop)
        if action == "attack":
            if attack_progress < 0.35:
                if facing > 0:
                    blade_angle = -math.pi * 0.8
                else:
                    blade_angle = -math.pi * 0.2
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                if facing > 0:
                    blade_angle = -math.pi * 0.8 + t * math.pi * 1.05
                else:
                    blade_angle = -math.pi * 0.2 - t * math.pi * 1.05
            else:
                t = (attack_progress - 0.6) / 0.4
                if facing > 0:
                    blade_angle = math.pi * 0.25 - t * math.pi * 0.1
                else:
                    blade_angle = math.pi * 0.75 + t * math.pi * 0.1
        else:
            # Rest: sword held in front-down at ready
            if facing > 0:
                blade_angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.05
            else:
                blade_angle = math.pi * 0.9 + math.sin(phase * 0.5) * 0.05
        tip_x = hx + int(math.cos(blade_angle) * blade_len)
        tip_y = hy + int(math.sin(blade_angle) * blade_len)
        perp = blade_angle + math.pi / 2
        pw = 3  # blade width
        edge_a = (hx + int(math.cos(perp) * pw), hy + int(math.sin(perp) * pw))
        edge_b = (hx - int(math.cos(perp) * pw), hy - int(math.sin(perp) * pw))
        # Mid-blade widest
        mid_ratio = 0.4
        mid_x = int(hx + (tip_x - hx) * mid_ratio)
        mid_y = int(hy + (tip_y - hy) * mid_ratio)
        mid_pw = 4
        mid_a = (mid_x + int(math.cos(perp) * mid_pw), mid_y + int(math.sin(perp) * mid_pw))
        mid_b = (mid_x - int(math.cos(perp) * mid_pw), mid_y - int(math.sin(perp) * mid_pw))
        # Tip taper
        tip_perp_x = tip_x + int(math.cos(perp) * 1)
        tip_perp_y = tip_y + int(math.sin(perp) * 1)
        tip_perp_x2 = tip_x - int(math.cos(perp) * 1)
        tip_perp_y2 = tip_y - int(math.sin(perp) * 1)
        # Shadow
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
            (edge_a[0] + 3, edge_a[1] + 3),
            (mid_a[0] + 3, mid_a[1] + 3),
            (tip_x + 3, tip_y + 3),
            (mid_b[0] + 3, mid_b[1] + 3),
            (edge_b[0] + 3, edge_b[1] + 3),
        ])
        # Base blade (darkest steel)
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
            edge_a, mid_a, (tip_x, tip_y), mid_b, edge_b,
        ])
        # Layered blade shine
        _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
            (int(edge_a[0] * 0.85 + hx * 0.15), int(edge_a[1] * 0.85 + hy * 0.15)),
            mid_a, (tip_x, tip_y), mid_b,
            (int(edge_b[0] * 0.85 + hx * 0.15), int(edge_b[1] * 0.85 + hy * 0.15)),
        ])
        # Central fuller (blood groove)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_mid"],
                              (hx, hy), (tip_x, tip_y), 3)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_light"],
                              (hx, hy), (tip_x, tip_y), 2)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["steel_shine"],
                              (hx, hy), (tip_x, tip_y), 1)
        # ENERGY GLOW along blade edges (blue storm or gold divine)
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        if ult:
            glow_col_mid = _NS_kaervosth.PALETTE["divine_mid"]
            glow_col_light = _NS_kaervosth.PALETTE["divine_light"]
            glow_col_hot = _NS_kaervosth.PALETTE["divine_hot"]
        else:
            glow_col_mid = _NS_kaervosth.PALETTE["storm_mid"]
            glow_col_light = _NS_kaervosth.PALETTE["storm_light"]
            glow_col_hot = _NS_kaervosth.PALETTE["storm_hot"]
        for pt_pair in [(edge_a, mid_a), (mid_a, (tip_x, tip_y)),
                        (edge_b, mid_b), (mid_b, (tip_x, tip_y))]:
            _NS_kaervosth._aaline(surface,
                                  (*glow_col_light,
                                   _NS_kaervosth._alpha(220 * glow_pulse)),
                                  pt_pair[0], pt_pair[1], 2)
            _NS_kaervosth._aaline(surface,
                                  (*glow_col_hot,
                                   _NS_kaervosth._alpha(255 * glow_pulse)),
                                  pt_pair[0], pt_pair[1], 1)
        # Radial glow around blade
        for i in range(6):
            t = i / 6
            gx = int(hx + (tip_x - hx) * t)
            gy = int(hy + (tip_y - hy) * t)
            for r in range(5, 0, -1):
                alpha = _NS_kaervosth._alpha(60 * (5 - r) / 5 * glow_pulse)
                _NS_kaervosth._aacircle(surface,
                                        (*glow_col_mid, alpha),
                                        (gx, gy), r)
        # Tip sparkle (huge)
        for r in range(8, 0, -1):
            alpha = _NS_kaervosth._alpha(180 * (8 - r) / 8 * glow_pulse)
            _NS_kaervosth._aacircle(surface,
                                    (*glow_col_light, alpha),
                                    (tip_x, tip_y), r)
        _NS_kaervosth._aacircle(surface, glow_col_hot, (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Lightning arcs on blade (when Q charging or idle)
        if not action == "attack" or attack_progress < 0.3:
            for i in range(3):
                arc_t = (phase * 3 + i * 0.5) % 1.0
                arc_start_x = int(hx + (tip_x - hx) * arc_t)
                arc_start_y = int(hy + (tip_y - hy) * arc_t)
                arc_end_x = arc_start_x + int(math.sin(phase * 8 + i) * 4)
                arc_end_y = arc_start_y + int(math.cos(phase * 8 + i) * 4)
                pygame.draw.line(surface,
                                 (*glow_col_hot,
                                  _NS_kaervosth._alpha(220 * glow_pulse)),
                                 (arc_start_x, arc_start_y),
                                 (arc_end_x, arc_end_y), 1)
        # ==== CROSS GUARD (elaborate, gold) ====
        cg_perp = blade_angle + math.pi / 2
        cg_len = 8
        cga = (hx + int(math.cos(cg_perp) * cg_len), hy + int(math.sin(cg_perp) * cg_len))
        cgb = (hx - int(math.cos(cg_perp) * cg_len), hy - int(math.sin(cg_perp) * cg_len))
        # Shadow
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                              (cga[0] + 1, cga[1] + 1), (cgb[0] + 1, cgb[1] + 1), 5)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["gold_darkest"], cga, cgb, 4)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["gold_dark"], cga, cgb, 3)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["gold_mid"], cga, cgb, 2)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["gold_shine"], cga, cgb, 1)
        # Gems on cross guard tips
        for cg_pt in (cga, cgb):
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["gold_darkest"],
                                    (cg_pt[0], cg_pt[1]), 2)
            pygame.draw.rect(surface, glow_col_hot, (cg_pt[0], cg_pt[1], 1, 1))
        # ==== HANDLE (leather-wrapped grip) ====
        handle_len = 10
        handle_end_x = hx - int(math.cos(blade_angle) * handle_len)
        handle_end_y = hy - int(math.sin(blade_angle) * handle_len)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 5)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["leather_dark"],
                              (hx, hy), (handle_end_x, handle_end_y), 4)
        _NS_kaervosth._aaline(surface, _NS_kaervosth.PALETTE["leather_mid"],
                              (hx, hy), (handle_end_x, handle_end_y), 2)
        # Grip wrap lines
        for i in range(1, 4):
            wrap_t = i / 4
            wx = int(hx + (handle_end_x - hx) * wrap_t)
            wy = int(hy + (handle_end_y - hy) * wrap_t)
            wrap_perp_x = int(math.cos(cg_perp) * 2)
            wrap_perp_y = int(math.sin(cg_perp) * 2)
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["gold_dark"],
                             (wx - wrap_perp_x, wy - wrap_perp_y),
                             (wx + wrap_perp_x, wy + wrap_perp_y), 1)
        # ==== POMMEL (round gold) ====
        pom_x = handle_end_x - int(math.cos(blade_angle) * 3)
        pom_y = handle_end_y - int(math.sin(blade_angle) * 3)
        _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["shadow_deep"],
                                (pom_x + 1, pom_y + 1), 5)
        _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["gold_darkest"], (pom_x, pom_y), 4)
        _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["gold_dark"], (pom_x, pom_y), 3)
        _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["gold_mid"], (pom_x, pom_y), 2)
        pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"], (pom_x, pom_y, 1, 1))
        # Pommel gem
        pygame.draw.rect(surface, glow_col_hot, (pom_x, pom_y, 1, 1))
    def _draw_body_sparkles(surface, cx, cy, phase, ult=False):
        col_hot = _NS_kaervosth.PALETTE["divine_hot"] if ult else _NS_kaervosth.PALETTE["storm_hot"]
        col_shine = _NS_kaervosth.PALETTE["divine_shine"] if ult else _NS_kaervosth.PALETTE["storm_shine"]
        for i in range(8):
            t = (phase * 0.6 + i * 0.13) % 1.0
            angle = i * math.pi / 4
            r = 28 + int(math.sin(phase + i) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy - 5 + int(math.sin(angle) * r) - int(t * 15)
            alpha = _NS_kaervosth._alpha(240 * (1 - t))
            pygame.draw.rect(surface, (*col_hot, alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*col_shine, alpha), (sx, sy, 1, 1))
    # ============================================================
    # ATTACK FX: Great Cleave swing arc
    # ============================================================
    def _draw_greatsword_swing_fx(surface, boss, x, y, progress):
        if progress < 0.35 or progress > 0.75:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.4
        arc_cx = x + facing * 10
        arc_cy = y - 6
        # BIG crescent slash with gold accent
        for i in range(5):
            layer_t = max(0, t - i * 0.08)
            if layer_t <= 0:
                continue
            alpha = _NS_kaervosth._alpha(240 * (1 - layer_t) * (1 - i * 0.15))
            radius = int(30 + layer_t * 8 + i * 3)
            if facing > 0:
                start_angle = -math.pi * 0.8
                end_angle = math.pi * 0.25
            else:
                start_angle = -math.pi * 0.2
                end_angle = math.pi * 0.75 + math.pi
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 14
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    # Outer glow
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_dark"], alpha),
                                          prev_pt, (px, py), 6)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_mid"], alpha),
                                          prev_pt, (px, py), 4)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                                          prev_pt, (px, py), 2)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                                          prev_pt, (px, py), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                                     (px, py, 1, 1))
                prev_pt = (px, py)
        # Sparks flying off leading edge
        if facing > 0:
            lead_angle = -math.pi * 0.8 + math.pi * 1.05 * t
        else:
            lead_angle = -math.pi * 0.2 - math.pi * 1.05 * t
        for i in range(10):
            spark_r = 30 + i * 2
            sx = arc_cx + int(math.cos(lead_angle) * spark_r)
            sy = arc_cy + int(math.sin(lead_angle) * spark_r)
            alpha = _NS_kaervosth._alpha(240 * (1 - i / 10))
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                             (sx, sy, 1, 1))
            # Random small sparks
            offset_ang = lead_angle + math.sin(i * 3) * 0.3
            offset_r = spark_r + int(math.cos(i * 2) * 5)
            ox = arc_cx + int(math.cos(offset_ang) * offset_r)
            oy = arc_cy + int(math.sin(offset_ang) * offset_r)
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                             (ox, oy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_hover_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((130, 30), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, int((13 - radius) * 15 * pulse))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 110 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 12, 170), (5, 8, 120, 12))
        pygame.draw.ellipse(shadow, (20, 30, 60, 110), (15, 10, 100, 8))
        surface.blit(shadow, (x - 65, y - 15))
    def _draw_hover_energy(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False, ult=False):
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        col_dark = _NS_kaervosth.PALETTE["divine_dark"] if ult else _NS_kaervosth.PALETTE["storm_dark"]
        col_mid = _NS_kaervosth.PALETTE["divine_mid"] if ult else _NS_kaervosth.PALETTE["storm_mid"]
        col_light = _NS_kaervosth.PALETTE["divine_light"] if ult else _NS_kaervosth.PALETTE["storm_light"]
        col_shine = _NS_kaervosth.PALETTE["divine_shine"] if ult else _NS_kaervosth.PALETTE["storm_shine"]
        # Mist
        mist = pygame.Surface((150, 40), pygame.SRCALPHA)
        for radius in range(32, 3, -3):
            alpha = _NS_kaervosth._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*col_dark, alpha),
                    (75 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2))
                )
        for radius in range(20, 3, -2):
            alpha = _NS_kaervosth._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*col_mid, alpha),
                    (75 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 75, cy - 8))
        # Rising sparkles
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24)):
            t = (phase * 0.4 + i * 0.14) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 2)
            sy = cy + 4 - int(t * 20)
            alpha = _NS_kaervosth._alpha(240 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaervosth._aacircle(surface, (*col_dark, alpha), (sx, sy), 2)
            pygame.draw.rect(surface, (*col_light, alpha), (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*col_shine, alpha), (sx, sy - 2, 1, 1))
        # Trail behind
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kaervosth._alpha(180 - i * 30)
                if alpha <= 0:
                    continue
                _NS_kaervosth._aacircle(surface, (*col_dark, alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_kaervosth._aacircle(surface, (*col_mid, alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*col_light, alpha), (sx, sy - 1, 2, 2))
    def _draw_knight_aura(surface, x, y, phase, buff=False, is_ultimate=False):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        if is_ultimate:
            # Massive gold aura
            for radius in range(100, 5, -5):
                alpha = _NS_kaervosth._alpha((100 - radius) * 1.4 * pulse)
                _NS_kaervosth._aacircle(aura,
                                        (*_NS_kaervosth.PALETTE["divine_dark"], alpha),
                                        (110, 100), radius)
            for radius in range(60, 5, -4):
                alpha = _NS_kaervosth._alpha((60 - radius) * 1.8 * pulse)
                _NS_kaervosth._aacircle(aura,
                                        (*_NS_kaervosth.PALETTE["divine_mid"], alpha),
                                        (110, 100), radius)
        elif buff:
            for radius in range(80, 5, -5):
                alpha = _NS_kaervosth._alpha((80 - radius) * 1.2 * pulse)
                _NS_kaervosth._aacircle(aura,
                                        (*_NS_kaervosth.PALETTE["divine_dark"], alpha),
                                        (110, 100), radius)
        else:
            # Default: subtle blue aura
            for radius in range(70, 5, -5):
                alpha = _NS_kaervosth._alpha((70 - radius) * 1.0 * pulse)
                _NS_kaervosth._aacircle(aura,
                                        (*_NS_kaervosth.PALETTE["storm_dark"], alpha),
                                        (110, 100), radius)
            for radius in range(40, 5, -3):
                alpha = _NS_kaervosth._alpha((40 - radius) * 1.5 * pulse)
                _NS_kaervosth._aacircle(aura,
                                        (*_NS_kaervosth.PALETTE["storm_mid"], alpha),
                                        (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating particles
        col = _NS_kaervosth.PALETTE["divine_light"] if (buff or is_ultimate) \
            else _NS_kaervosth.PALETTE["storm_light"]
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, col, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["white"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        if skill == "r":
            col_dark = _NS_kaervosth.PALETTE["divine_dark"]
            col_mid = _NS_kaervosth.PALETTE["divine_mid"]
            col_light = _NS_kaervosth.PALETTE["divine_light"]
        else:
            col_dark = _NS_kaervosth.PALETTE["storm_dark"]
            col_mid = _NS_kaervosth.PALETTE["storm_mid"]
            col_light = _NS_kaervosth.PALETTE["storm_light"]
        pygame.draw.ellipse(ring, (*col_dark, 200), (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_kaervosth.PALETTE["steel_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*col_mid, 230), (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*col_light, 180), (40, 24, 90, 14), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 45)
            y1 = 27 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 27 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*col_light, 220), (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kaervosth.PALETTE["divine_hot"],
                                 _NS_kaervosth._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: STORM HAMMER (projectile with lightning trail)
    # ============================================================
    def _draw_storm_hammer(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaervosth._target_position(boss, x, y)
        start_x = x + facing * 28
        start_y = y - 8
        if progress < 0.2:
            # Charge — lightning gathers at hand
            t = progress / 0.2
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kaervosth._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_kaervosth._aacircle(surface,
                                        (*_NS_kaervosth.PALETTE["storm_mid"], alpha),
                                        (start_x, start_y), r)
            _NS_kaervosth._aacircle(surface, _NS_kaervosth.PALETTE["storm_hot"],
                                    (start_x, start_y), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["storm_shine"],
                             (start_x, start_y, 2, 2))
            # Lightning arcs around charge
            for i in range(5):
                arc_ang = phase * 5 + i * math.pi * 2 / 5
                ax = start_x + int(math.cos(arc_ang) * (cr + 2))
                ay = start_y + int(math.sin(arc_ang) * (cr + 2))
                pygame.draw.line(surface, _NS_kaervosth.PALETTE["storm_hot"],
                                 (start_x, start_y), (ax, ay), 1)
        else:
            # Hammer projectile flying with lightning
            t = (progress - 0.2) / 0.8
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Lightning trail behind projectile
            segments = 8
            for i in range(segments):
                seg_t = t - i * 0.05
                if seg_t <= 0:
                    continue
                seg_x = int(start_x + (bx - start_x) * (seg_t / t))
                seg_y = int(start_y + (by - start_y) * (seg_t / t))
                # Zigzag lightning
                perp_ang = math.atan2(by - start_y, bx - start_x) + math.pi / 2
                jitter = math.sin(phase * 20 + i * 2) * 6 * (1 - i / segments)
                seg_x += int(math.cos(perp_ang) * jitter)
                seg_y += int(math.sin(perp_ang) * jitter)
                alpha = _NS_kaervosth._alpha(220 - i * 22)
                if i > 0:
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["storm_dark"], alpha),
                                          prev_pt, (seg_x, seg_y), 5)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["storm_mid"], alpha),
                                          prev_pt, (seg_x, seg_y), 3)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["storm_light"], alpha),
                                          prev_pt, (seg_x, seg_y), 2)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["storm_hot"], alpha),
                                          prev_pt, (seg_x, seg_y), 1)
                prev_pt = (seg_x, seg_y)
            # HAMMER HEAD (rectangular block with lightning glow)
            # Radial glow
            for r in range(14, 0, -2):
                alpha = _NS_kaervosth._alpha(100 * (14 - r) / 14)
                _NS_kaervosth._aacircle(surface,
                                        (*_NS_kaervosth.PALETTE["storm_light"], alpha),
                                        (bx, by), r)
            # Hammer body
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["shadow_deep"], [
                (bx - 8 + 2, by - 6 + 2), (bx + 8 + 2, by - 6 + 2),
                (bx + 8 + 2, by + 6 + 2), (bx - 8 + 2, by + 6 + 2),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_darkest"], [
                (bx - 8, by - 6), (bx + 8, by - 6),
                (bx + 8, by + 6), (bx - 8, by + 6),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_dark"], [
                (bx - 7, by - 5), (bx + 7, by - 5),
                (bx + 7, by + 5), (bx - 7, by + 5),
            ])
            _NS_kaervosth._poly(surface, _NS_kaervosth.PALETTE["steel_mid"], [
                (bx - 5, by - 3), (bx + 5, by - 3),
                (bx + 5, by + 3), (bx - 5, by + 3),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_kaervosth.PALETTE["steel_light"],
                             (bx - 3, by - 2), (bx - 3, by + 2), 1)
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["steel_shine"],
                             (bx - 3, by - 2, 1, 1))
            # Gold trim on hammer
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (bx - 8, by - 6, 16, 1))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_mid"],
                             (bx - 8, by + 5, 16, 1))
            pygame.draw.rect(surface, _NS_kaervosth.PALETTE["gold_shine"],
                             (bx - 1, by - 6, 2, 1))
            # Handle sticking out
            for handle_side in ((-8, 0), (8, 0)):
                hxs = bx + handle_side[0]
                hys = by + handle_side[1]
                pygame.draw.rect(surface, _NS_kaervosth.PALETTE["leather_dark"],
                                 (hxs - 2, hys - 1, 2, 2))
            # Lightning arcs around hammer
            for i in range(6):
                arc_ang = phase * 8 + i * math.pi / 3
                ar = 12
                ax1 = bx + int(math.cos(arc_ang) * (ar - 3))
                ay1 = by + int(math.sin(arc_ang) * (ar - 3))
                ax2 = bx + int(math.cos(arc_ang) * ar)
                ay2 = by + int(math.sin(arc_ang) * ar)
                pygame.draw.line(surface, _NS_kaervosth.PALETTE["storm_hot"],
                                 (ax1, ay1), (ax2, ay2), 2)
                pygame.draw.line(surface, _NS_kaervosth.PALETTE["storm_shine"],
                                 (ax1, ay1), (ax2, ay2), 1)
            # Impact stun burst
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(15 + st * 25)
                alpha = _NS_kaervosth._alpha(255 * (1 - st))
                _NS_kaervosth._aacircle(surface,
                                        (*_NS_kaervosth.PALETTE["storm_dark"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_kaervosth._aacircle(surface,
                                        (*_NS_kaervosth.PALETTE["storm_mid"], alpha),
                                        (tx, ty), radius, 2)
                _NS_kaervosth._aacircle(surface,
                                        (*_NS_kaervosth.PALETTE["storm_hot"], alpha),
                                        (tx, ty), max(1, radius - 6), 1)
                # Stun stars around target
                for i in range(6):
                    star_ang = i * math.pi / 3 + phase * 2
                    sx_st = tx + int(math.cos(star_ang) * (radius - 3))
                    sy_st = ty + int(math.sin(star_ang) * (radius - 3))
                    for pt_off in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                        pygame.draw.rect(surface,
                                         (*_NS_kaervosth.PALETTE["storm_shine"], alpha),
                                         (sx_st + pt_off[0], sy_st + pt_off[1], 1, 1))
    # ============================================================
    # SKILL W: GREAT CLEAVE
    # ============================================================
    def _draw_cleave_ground(surface, boss, x, y, timer, phase):
        pass  # Foreground FX handles this
    def _draw_cleave_foreground(surface, boss, x, y, timer, phase):
        """Wide crescent gold energy cleave in front of boss."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        arc_cx = x + facing * 12
        arc_cy = y - 4
        if progress < 0.2:
            # Wind-up glow at sword
            return
        t = (progress - 0.2) / 0.8
        # Multi-layer big cleave arc
        for i in range(6):
            layer_t = max(0, t - i * 0.06)
            if layer_t <= 0:
                continue
            alpha = _NS_kaervosth._alpha(240 * (1 - layer_t) * (1 - i * 0.12))
            radius = int(40 + layer_t * 12 + i * 4)
            if facing > 0:
                start_angle = -math.pi * 0.7
                end_angle = math.pi * 0.35
            else:
                start_angle = -math.pi * 0.3
                end_angle = math.pi * 0.7 + math.pi
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 16
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_darkest"], alpha),
                                          prev_pt, (px, py), 7)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_dark"], alpha),
                                          prev_pt, (px, py), 5)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_mid"], alpha),
                                          prev_pt, (px, py), 3)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                                          prev_pt, (px, py), 2)
                    _NS_kaervosth._aaline(surface,
                                          (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                                          prev_pt, (px, py), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                                     (px, py, 2, 2))
                prev_pt = (px, py)
        # Rain of gold sparks
        for i in range(15):
            spark_t = (phase * 3 + i * 0.15) % 1.0
            spark_ang = -math.pi * 0.5 + math.pi * spark_t * facing
            sr = 40 + int(math.sin(i * 2) * 15)
            sx = arc_cx + int(math.cos(spark_ang) * sr)
            sy = arc_cy + int(math.sin(spark_ang) * sr) + int(spark_t * 10)
            alpha = _NS_kaervosth._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL E: GOD'S STRENGTH (self buff)
    # ============================================================
    def _draw_gods_strength_ground(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Golden circle beneath
        r = int(45 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_kaervosth.PALETTE["divine_dark"], 220),
                                (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_kaervosth.PALETTE["divine_mid"],
                                 _NS_kaervosth._alpha(200 * pulse)),
                                (x - r + 5, y + 45 - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_kaervosth.PALETTE["divine_light"], 180),
                                (x - r + 12, y + 45 - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12), 1)
            # Rune spikes emerging
            for i in range(6):
                ang = i * math.pi / 3 + phase * 0.3
                rx = x + int(math.cos(ang) * r)
                ry = y + 45 + int(math.sin(ang) * r * 0.4)
                spike_h = int(8 + math.sin(phase * 2 + i) * 3)
                _NS_kaervosth._poly(surface,
                                    (*_NS_kaervosth.PALETTE["divine_darkest"], 240), [
                    (rx - 2, ry), (rx + 2, ry), (rx, ry - spike_h),
                ])
                _NS_kaervosth._poly(surface,
                                    (*_NS_kaervosth.PALETTE["divine_mid"], 220), [
                    (rx - 1, ry), (rx + 1, ry), (rx, ry - spike_h + 1),
                ])
                pygame.draw.rect(surface, _NS_kaervosth.PALETTE["divine_shine"],
                                 (rx, ry - spike_h, 1, 1))
    def _draw_gods_strength_aura(surface, boss, x, y, timer, phase):
        """Golden vertical light pillar rising through boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Vertical light pillar
        pillar_h = 100
        pillar_alpha = _NS_kaervosth._alpha(150 * pulse)
        for width, color_key in [
            (24, "divine_dark"), (16, "divine_mid"),
            (10, "divine_light"), (5, "divine_hot"),
            (2, "divine_shine"),
        ]:
            pygame.draw.rect(surface,
                             (*_NS_kaervosth.PALETTE[color_key], pillar_alpha),
                             (x - width // 2, y - pillar_h + 30, width, pillar_h))
        # Rising sparkles inside pillar
        for i in range(10):
            spark_t = (phase * 1.5 + i * 0.1) % 1.0
            spark_y = y + 30 - int(spark_t * pillar_h)
            spark_x = x + int(math.sin(phase * 3 + i) * 5)
            alpha = _NS_kaervosth._alpha(240 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                             (spark_x, spark_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                             (spark_x, spark_y, 1, 1))
    # ============================================================
    # SKILL R: TITAN'S WRATH (Ultimate)
    # ============================================================
    def _draw_ultimate_ground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # HUGE golden rune circle
        r = int(75 * min(1.0, progress * 2))
        if r > 3:
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 4, 240), (8, 3, 200), (16, 2, 160), (24, 1, 120),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_kaervosth.PALETTE["divine_dark"],
                                     _NS_kaervosth._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 45 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
            # Big spokes
            for i in range(12):
                ang = i * math.pi / 6 + phase * 0.3
                x1 = x + int(math.cos(ang) * r * 0.4)
                y1 = y + 45 + int(math.sin(ang) * r * 0.15)
                x2 = x + int(math.cos(ang) * r)
                y2 = y + 45 + int(math.sin(ang) * r * 0.4)
                pygame.draw.line(surface,
                                 (*_NS_kaervosth.PALETTE["divine_mid"], 220),
                                 (x1, y1), (x2, y2), 2)
                pygame.draw.line(surface,
                                 (*_NS_kaervosth.PALETTE["divine_hot"], 240),
                                 (x1, y1), (x2, y2), 1)
                pygame.draw.rect(surface,
                                 (*_NS_kaervosth.PALETTE["divine_shine"], 255),
                                 (x2, y2, 2, 2))
    def _draw_ultimate_aura(surface, boss, x, y, timer, phase):
        """Massive divine golden explosion effect."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # BIG light pillar
        if progress < 0.3:
            t = progress / 0.3
            pillar_h = int(t * 200)
            pillar_alpha = _NS_kaervosth._alpha(220 * t)
            for width, color_key in [
                (32, "divine_dark"), (22, "divine_mid"),
                (14, "divine_light"), (8, "divine_hot"),
                (3, "divine_shine"),
            ]:
                pygame.draw.rect(surface,
                                 (*_NS_kaervosth.PALETTE[color_key], pillar_alpha),
                                 (x - width // 2, y - pillar_h + 30, width, pillar_h))
        # Radial burst rays continuous
        for i in range(16):
            ang = phase * 0.5 + i * math.pi / 8
            length = 90 + int(math.sin(phase * 3 + i) * 15)
            end_x = x + int(math.cos(ang) * length)
            end_y = y + int(math.sin(ang) * length)
            alpha = _NS_kaervosth._alpha(180 * pulse)
            pygame.draw.line(surface,
                             (*_NS_kaervosth.PALETTE["divine_mid"], alpha),
                             (x, y), (end_x, end_y), 3)
            pygame.draw.line(surface,
                             (*_NS_kaervosth.PALETTE["divine_light"], alpha),
                             (x, y), (end_x, end_y), 2)
            pygame.draw.line(surface,
                             (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                             (x, y), (end_x, end_y), 1)
            pygame.draw.rect(surface,
                             (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                             (end_x, end_y, 2, 2))
        # Rising gold particles all around
        for i in range(20):
            t_rise = (phase * 0.8 + i * 0.08) % 1.0
            px = x - 60 + i * 6 + int(math.sin(phase + i) * 8)
            py = y + 30 - int(t_rise * 100)
            alpha = _NS_kaervosth._alpha(240 * (1 - t_rise))
            _NS_kaervosth._aacircle(surface,
                                    (*_NS_kaervosth.PALETTE["divine_mid"], alpha),
                                    (px, py), 2)
            pygame.draw.rect(surface,
                             (*_NS_kaervosth.PALETTE["divine_hot"], alpha),
                             (px, py, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_kaervosth.PALETTE["divine_shine"], alpha),
                             (px, py, 1, 1))
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_kaervosth).keys()):
    _attr = vars(_NS_kaervosth)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_kaervosth, _attr_name, staticmethod(_attr))



# ====================================================================
# MORVYSSK (CORROSIVE OOZE) - Mini Boss
# ====================================================================

class _NS_morvyssk:
    """Namespace morvyssk - HD purple ooze monster boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Deep purple slime body
        "slime_darkest": (18, 8, 30),
        "slime_dark": (45, 20, 70),
        "slime_mid": (85, 40, 130),
        "slime_light": (140, 75, 195),
        "slime_shine": (200, 150, 240),
        "slime_gloss": (240, 210, 255),
        # Magenta / pink glow (core, eyes, mouth)
        "glow_darkest": (35, 5, 25),
        "glow_dark": (100, 20, 80),
        "glow_mid": (200, 50, 170),
        "glow_light": (255, 120, 220),
        "glow_hot": (255, 180, 240),
        "glow_shine": (255, 230, 250),
        # Black horns
        "horn_darkest": (5, 3, 8),
        "horn_dark": (18, 12, 25),
        "horn_mid": (40, 30, 55),
        "horn_light": (75, 60, 95),
        # Fang / teeth (white-ish with purple tint)
        "fang_dark": (60, 45, 80),
        "fang_mid": (180, 160, 200),
        "fang_light": (230, 220, 240),
        "fang_shine": (255, 250, 255),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 5),
        # Ground pool / drip
        "pool_dark": (25, 10, 45),
        "pool_mid": (65, 25, 105),
        "pool_light": (130, 60, 180),
        # Toxic bubble accents
        "bubble_dark": (50, 15, 90),
        "bubble_mid": (140, 60, 200),
        "bubble_light": (220, 160, 250),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morvyssk._clamp(color)
        if _NS_morvyssk.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvyssk._clamp(color)
        if _NS_morvyssk.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_morvyssk._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_morvyssk._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_morvyssk._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morvyssk(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morvyssk._detect_moving(boss)
        _NS_morvyssk._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_mvy_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_morvyssk._draw_slime_aura(surface, x, y, pulse)
        _NS_morvyssk._draw_ground_pool(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind)
        if active_skill == "q":
            _NS_morvyssk._draw_split_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvyssk._draw_slam_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvyssk._draw_glue_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating/hovering with liquid bob
        if attacking:
            _NS_morvyssk._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_morvyssk._draw_float_move(surface, boss, x, y)
        else:
            _NS_morvyssk._draw_float_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_morvyssk._draw_split_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvyssk._draw_stick_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvyssk._draw_slam_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvyssk._draw_glue_tether(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mvy_previous_timer", 0))
        active = bool(getattr(boss, "_mvy_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._mvy_attack_active = True
            boss._mvy_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mvy_attack_frame = int(getattr(boss, "_mvy_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mvy_attack_active = False
            boss._mvy_attack_frame = 0
            active = False
        boss._mvy_previous_timer = timer
        boss._mvy_attack_progress = (
            min(1.0, getattr(boss, "_mvy_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_mvy_last_x"):
            boss._mvy_last_x = boss.x
            boss._mvy_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mvy_last_x)
        dy = abs(boss.y - boss._mvy_last_y)
        boss._mvy_last_x = boss.x
        boss._mvy_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES (floating slime)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        squish = math.sin(boss.pulse * 0.8) * 0.08
        _NS_morvyssk._draw_shadow(surface, x, y + 55)
        _NS_morvyssk._draw_drip_pool(surface, x, y + 45, boss.pulse)
        _NS_morvyssk._draw_body(surface, x, y + bob,
                                boss.direction, boss.pulse, "idle", squish=squish)
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        squish = math.sin(phase * 1.2) * 0.15
        _NS_morvyssk._draw_shadow(surface, x + sway, y + 55)
        _NS_morvyssk._draw_drip_pool(surface, x + sway, y + 45, phase, trail=True,
                                     facing=boss.direction)
        _NS_morvyssk._draw_body(surface, x + sway, y + bob,
                                boss.direction, phase, "move", squish=squish)
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_mvy_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back → forward slam → recover
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 5)
            squish = -0.15 * t
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 16)) * boss.direction
            lift = int(5 - t * 8)
            squish = -0.15 + t * 0.35
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(12 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3)
            squish = 0.2 * (1 - t)
        _NS_morvyssk._draw_shadow(surface, x + lunge, y + 55)
        _NS_morvyssk._draw_drip_pool(surface, x + lunge, y + 45, boss.pulse,
                                     intense=True)
        _NS_morvyssk._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress,
                                squish=squish)
        _NS_morvyssk._draw_tentacle_swing(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY - Blob slime with horns, face, arms/tentacles
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0, squish=0):
        # Base blob body (wide bottom, rounded top)
        _NS_morvyssk._draw_blob(surface, cx, cy, phase, squish)
        # Tentacle arms
        _NS_morvyssk._draw_tentacle_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Face (eyes, mouth)
        _NS_morvyssk._draw_face(surface, cx, cy - 8, facing, phase)
        # Horns on top
        _NS_morvyssk._draw_horns(surface, cx, cy - 22, facing, phase)
        # Chest core (glowing magenta orb)
        _NS_morvyssk._draw_chest_core(surface, cx, cy + 4, phase)
        # Drip strands hanging down
        _NS_morvyssk._draw_hanging_drips(surface, cx, cy + 20, phase)
    # ---------- BLOB (main body) ----------
    def _draw_blob(surface, cx, cy, phase, squish=0):
        # Squish effect: wider when squish>0, taller when squish<0
        w_mult = 1 + squish
        h_mult = 1 - squish * 0.5
        # Bulbous main body — wider at bottom (drippy weight)
        w = int(28 * w_mult)
        h_top = int(18 * h_mult)
        h_bot = int(24 * h_mult)
        # Wobbly outline points (with subtle phase-based wobble)
        wobble = lambda i: math.sin(phase * 1.5 + i * 0.8) * 1.5
        body_pts = [
            (cx - w + int(wobble(0)), cy - h_top // 2),
            (cx - w - 2 + int(wobble(1)), cy + h_top // 2),
            (cx - w + 2 + int(wobble(2)), cy + h_bot // 2),
            (cx - w + 6 + int(wobble(3)), cy + h_bot),
            (cx - 8 + int(wobble(4)), cy + h_bot + 3),
            (cx + 8 + int(wobble(5)), cy + h_bot + 3),
            (cx + w - 6 + int(wobble(6)), cy + h_bot),
            (cx + w - 2 + int(wobble(7)), cy + h_bot // 2),
            (cx + w + 2 + int(wobble(8)), cy + h_top // 2),
            (cx + w + int(wobble(9)), cy - h_top // 2),
            (cx + w - 4 + int(wobble(10)), cy - h_top),
            (cx + 6 + int(wobble(11)), cy - h_top - 2),
            (cx - 6 + int(wobble(12)), cy - h_top - 2),
            (cx - w + 4 + int(wobble(13)), cy - h_top),
        ]
        # Shadow drop
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in body_pts])
        # Base darkest fill
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["slime_darkest"], body_pts)
        # Layered fills inward for depth
        dark_pts = []
        for p in body_pts:
            dark_pts.append((int(p[0] * 0.9 + cx * 0.1),
                             int(p[1] * 0.9 + cy * 0.1)))
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["slime_dark"], dark_pts)
        mid_pts = []
        for p in body_pts:
            mid_pts.append((int(p[0] * 0.75 + cx * 0.25),
                            int(p[1] * 0.75 + cy * 0.25)))
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["slime_mid"], mid_pts)
        # Light center highlight (blob shine on upper left)
        light_x = cx - int(w * 0.35)
        light_y = cy - int(h_top * 0.3)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_light"],
                               (light_x, light_y), int(w * 0.35))
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_shine"],
                               (light_x - 2, light_y - 2), int(w * 0.18))
        # Bright gloss dot (wet reflection)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_gloss"],
                               (light_x - 4, light_y - 4), max(2, int(w * 0.08)))
        pygame.draw.rect(surface, _NS_morvyssk.PALETTE["white"],
                         (light_x - 5, light_y - 5, 1, 1))
        # Small internal bubbles floating inside body
        for i in range(4):
            bt = (phase * 0.5 + i * 0.25) % 1.0
            bx = cx - w // 2 + int((i * w // 2) + math.sin(phase + i) * 3)
            by = cy + h_top // 2 - int(bt * h_bot)
            br = 2 + i % 2
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["bubble_dark"], (bx, by), br)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["bubble_mid"], (bx, by), max(1, br - 1))
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["bubble_light"], (bx, by, 1, 1))
    # ---------- TENTACLE ARMS ----------
    def _draw_tentacle_arms(surface, cx, cy, facing, phase, action, attack_progress):
        for side in (-1, 1):
            base_x = cx + side * 22
            base_y = cy + 2
            # Attack pose: dominant side swings
            is_dominant = (side * facing > 0)
            if action == "attack" and is_dominant:
                if attack_progress < 0.35:
                    # Coil back
                    t = attack_progress / 0.35
                    reach = -6 * facing * t
                    droop = -8 * t
                elif attack_progress < 0.6:
                    # Swing forward + up
                    t = (attack_progress - 0.35) / 0.25
                    reach = int((-6 + t * 40) * facing)
                    droop = int(-8 + t * 4)
                else:
                    t = (attack_progress - 0.6) / 0.4
                    reach = int(34 * (1 - t)) * facing
                    droop = int(-4 + t * 10)
            else:
                # Idle sway
                reach = int(math.sin(phase * 0.7 + side) * 4 * side)
                droop = int(math.sin(phase * 0.9) * 3 + 8)
            # Draw tentacle as bezier-like curve segments
            end_x = base_x + reach + side * 8
            end_y = base_y + droop + 12
            mid_x = int((base_x + end_x) / 2 + side * 4)
            mid_y = int((base_y + end_y) / 2 + math.sin(phase + side) * 2)
            prev = (base_x, base_y)
            segments = 6
            for step in range(1, segments + 1):
                t = step / segments
                # Quadratic bezier
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * end_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * end_y)
                thickness = max(2, 9 - step)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                                     (prev[0] + 2, prev[1] + 2),
                                     (bx + 2, by + 2), thickness + 1)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                     prev, (bx, by), thickness)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                     prev, (bx, by), max(1, thickness - 2))
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                     (prev[0], prev[1] - 1),
                                     (bx, by - 1), max(1, thickness - 4))
                # Highlight strand
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_light"],
                                     (prev[0] - 1, prev[1] - 1),
                                     (bx - 1, by - 1), max(1, thickness - 6))
                prev = (bx, by)
            # Blob at the end (tentacle tip)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                                   (end_x + 1, end_y + 2), 6)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"], (end_x, end_y), 5)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_dark"], (end_x, end_y), 4)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"], (end_x, end_y), 3)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_light"], (end_x - 1, end_y - 1), 2)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["slime_gloss"],
                             (end_x - 1, end_y - 1, 1, 1))
    # ---------- FACE (evil grinning) ----------
    def _draw_face(surface, cx, cy, facing, phase):
        # EYES — glowing magenta menacing
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 7
            ey = cy
            # Deep socket
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                                   (ex + 1, ey + 1), 5)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                   (ex, ey), 5)
            # Halo glow
            for r in range(8, 2, -1):
                alpha = _NS_morvyssk._alpha(80 * (8 - r) / 8 * eye_pulse)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                       (ex, ey), r)
            # Eye slit (angry, angled)
            angle_off = -side * 0.3  # angled inward for anger
            eye_shape = [
                (ex - 3, ey + 1),
                (ex - 2, ey - 2 + int(angle_off * 2)),
                (ex + 2, ey - 2 - int(angle_off * 2)),
                (ex + 3, ey + 1),
                (ex + 2, ey + 2),
                (ex - 2, ey + 2),
            ]
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["glow_dark"], eye_shape)
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["glow_mid"], [
                (ex - 2, ey), (ex - 1, ey - 1 + int(angle_off)),
                (ex + 1, ey - 1 - int(angle_off)), (ex + 2, ey),
                (ex + 1, ey + 1), (ex - 1, ey + 1),
            ])
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["glow_light"], [
                (ex - 1, ey), (ex + 1, ey), (ex, ey + 1),
            ])
            # Bright core
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_hot"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_shine"], (ex, ey - 1, 1, 1))
        # MOUTH — wide evil grin with teeth
        _NS_morvyssk._draw_mouth(surface, cx, cy + 8, phase)
    def _draw_mouth(surface, cx, cy, phase):
        # Wide grinning mouth shape
        mouth_pulse = math.sin(phase * 1.2) * 0.2 + 0.8
        # Mouth outline (curved grin)
        mouth_pts = [
            (cx - 12, cy - 1),
            (cx - 10, cy + 2),
            (cx - 6, cy + 4),
            (cx, cy + 5),
            (cx + 6, cy + 4),
            (cx + 10, cy + 2),
            (cx + 12, cy - 1),
            (cx + 10, cy),
            (cx + 6, cy + 1),
            (cx, cy + 2),
            (cx - 6, cy + 1),
            (cx - 10, cy),
        ]
        # Shadow
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in mouth_pts])
        # Dark cavity
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["slime_darkest"], mouth_pts)
        # Glow inside mouth (magenta)
        inner_pts = [
            (cx - 10, cy),
            (cx - 8, cy + 2),
            (cx - 4, cy + 3),
            (cx, cy + 4),
            (cx + 4, cy + 3),
            (cx + 8, cy + 2),
            (cx + 10, cy),
        ]
        _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["glow_darkest"], inner_pts)
        # Deep glow
        for r_off in range(3, 0, -1):
            alpha = _NS_morvyssk._alpha(150 * (3 - r_off) / 3 * mouth_pulse)
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                   (cx, cy + 2), 5 + r_off)
        pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_hot"], (cx, cy + 2, 2, 1))
        # TEETH — jagged fangs (top row)
        for i, tx_off in enumerate((-9, -6, -3, 0, 3, 6, 9)):
            fang_x = cx + tx_off
            fang_top_y = cy - 1
            fang_tip_y = cy + 3
            # Alternate tooth height (jagged look)
            if i % 2 == 0:
                fang_tip_y = cy + 3
            else:
                fang_tip_y = cy + 2
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["fang_dark"], [
                (fang_x - 1, fang_top_y),
                (fang_x + 1, fang_top_y),
                (fang_x, fang_tip_y),
            ])
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["fang_mid"], [
                (fang_x, fang_top_y),
                (fang_x + 1, fang_top_y),
                (fang_x, fang_tip_y - 1),
            ])
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["fang_light"],
                             (fang_x, fang_top_y, 1, 1))
        # Bottom teeth (fewer, shorter)
        for i, tx_off in enumerate((-7, -3, 0, 3, 7)):
            fang_x = cx + tx_off
            fang_bot_y = cy + 4
            fang_tip_y = cy + 2
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["fang_dark"], [
                (fang_x - 1, fang_bot_y),
                (fang_x + 1, fang_bot_y),
                (fang_x, fang_tip_y),
            ])
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["fang_mid"],
                             (fang_x, fang_tip_y, 1, 1))
    # ---------- HORNS ----------
    def _draw_horns(surface, cx, cy, facing, phase):
        # Two curved black horns
        for side in (-1, 1):
            base_x = cx + side * 6
            base_y = cy + 4
            # Curve back
            tip_x = base_x + side * 3
            tip_y = base_y - 12
            mid_x = base_x + side * 6
            mid_y = base_y - 6
            # Horn shape (curved cone)
            horn_pts = [
                (base_x - 3, base_y),
                (base_x + 3, base_y),
                (mid_x, mid_y),
                (tip_x, tip_y),
            ]
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in horn_pts])
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["horn_darkest"], horn_pts)
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["horn_dark"], [
                (base_x - 2, base_y),
                (base_x + 2, base_y),
                (int(mid_x * 0.8 + cx * 0.2), mid_y),
                (tip_x, tip_y),
            ])
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["horn_mid"], [
                (base_x - 1 + side, base_y),
                (base_x + 1, base_y - 2),
                (tip_x, tip_y + 2),
            ])
            # Highlight streak
            pygame.draw.line(surface, _NS_morvyssk.PALETTE["horn_light"],
                             (base_x + side, base_y - 1),
                             (tip_x, tip_y + 1), 1)
            # Tip shine
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["horn_light"],
                             (tip_x, tip_y, 1, 1))
    # ---------- CHEST CORE (glowing orb) ----------
    def _draw_chest_core(surface, cx, cy, phase):
        pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        # Outer glow halo
        for r in range(15, 0, -1):
            alpha = _NS_morvyssk._alpha(60 * (15 - r) / 15 * pulse)
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                   (cx, cy), r)
        # Core body
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_darkest"], (cx, cy), 7)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_dark"], (cx, cy), 6)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_mid"], (cx, cy), 4)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_light"], (cx, cy), 3)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_hot"], (cx, cy), 2)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_shine"], (cx - 1, cy - 1), 1)
        pygame.draw.rect(surface, _NS_morvyssk.PALETTE["white"], (cx - 1, cy - 1, 1, 1))
        # Energy sparks around core
        for i in range(6):
            ang = phase * 2 + i * math.pi / 3
            sr = 10 + int(math.sin(phase * 3 + i) * 2)
            sx = cx + int(math.cos(ang) * sr)
            sy = cy + int(math.sin(ang) * sr)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_light"], (sx, sy, 1, 1))
    # ---------- DRIPS (hanging slime strands) ----------
    def _draw_hanging_drips(surface, cx, cy, phase):
        # Several drips hanging from body bottom
        drip_positions = [-18, -10, -3, 5, 12, 20]
        for i, dx in enumerate(drip_positions):
            drip_len = int(6 + math.sin(phase * 1.5 + i) * 3 + (i % 2) * 3)
            drip_x = cx + dx
            drip_top = cy
            drip_bot = cy + drip_len
            # Drip stem
            _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                                 (drip_x + 1, drip_top + 1),
                                 (drip_x + 1, drip_bot + 1), 3)
            _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                 (drip_x, drip_top), (drip_x, drip_bot), 3)
            _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                 (drip_x, drip_top), (drip_x, drip_bot), 2)
            _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                 (drip_x, drip_top), (drip_x, drip_bot - 1), 1)
            # Drop at bottom
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                   (drip_x, drip_bot + 1), 3)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                   (drip_x, drip_bot + 1), 2)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                   (drip_x, drip_bot + 1), 1)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["slime_light"],
                             (drip_x, drip_bot, 1, 1))
    # ============================================================
    # ATTACK FX: Tentacle Swing
    # ============================================================
    def _draw_tentacle_swing(surface, boss, x, y, progress):
        if progress < 0.35 or progress > 0.7:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.35
        # Slime splash arc from tentacle sweep
        arc_cx = x + facing * 30
        arc_cy = y + 4
        # Sweeping trail
        for i in range(4):
            layer_t = max(0, t - i * 0.1)
            if layer_t <= 0:
                continue
            alpha = _NS_morvyssk._alpha(200 * (1 - layer_t) * (1 - i * 0.2))
            radius = int(18 + layer_t * 6 + i * 2)
            if facing > 0:
                start_angle = -math.pi * 0.6
                end_angle = math.pi * 0.3
            else:
                start_angle = -math.pi * 0.4
                end_angle = math.pi * 0.6 + math.pi
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 10
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_morvyssk._aaline(surface,
                                         (*_NS_morvyssk.PALETTE["slime_darkest"], alpha),
                                         prev_pt, (px, py), 4)
                    _NS_morvyssk._aaline(surface,
                                         (*_NS_morvyssk.PALETTE["slime_mid"], alpha),
                                         prev_pt, (px, py), 2)
                    _NS_morvyssk._aaline(surface,
                                         (*_NS_morvyssk.PALETTE["glow_light"], alpha),
                                         prev_pt, (px, py), 1)
                prev_pt = (px, py)
        # Slime droplets flying off
        for i in range(8):
            drop_ang = -math.pi * 0.5 + math.pi * t + i * 0.15 * facing
            dr = 22 + i * 2
            dx = arc_cx + int(math.cos(drop_ang) * dr)
            dy = arc_cy + int(math.sin(drop_ang) * dr) + i * 2
            alpha = _NS_morvyssk._alpha(220 * (1 - i / 8))
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["slime_dark"], alpha),
                                   (dx, dy), 3)
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["slime_mid"], alpha),
                                   (dx, dy), 2)
            pygame.draw.rect(surface, (*_NS_morvyssk.PALETTE["glow_light"], alpha),
                             (dx, dy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 8, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 15, 55, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_drip_pool(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Slime dripping down and pooling on floor."""
        strength = 1.5 if intense else 1.0
        # Ground pool (elliptical stain)
        pulse = math.sin(phase * 1.0) * 0.15 + 0.85
        pool = pygame.Surface((160, 40), pygame.SRCALPHA)
        for r in range(30, 5, -3):
            alpha = _NS_morvyssk._alpha((30 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    pool, (*_NS_morvyssk.PALETTE["pool_dark"], alpha),
                    (80 - r * 2, 20 - r // 3, r * 4, max(3, r // 2))
                )
        for r in range(18, 3, -2):
            alpha = _NS_morvyssk._alpha((18 - r) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    pool, (*_NS_morvyssk.PALETTE["pool_mid"], alpha),
                    (80 - r, 20 - r // 4, r * 2, max(2, r // 3))
                )
        surface.blit(pool, (cx - 80, cy - 5))
        # Small bubbles rising from pool
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            bx = cx - 20 + i * 8 + int(math.sin(phase + i) * 2)
            by = cy + 3 - int(t * 15)
            alpha = _NS_morvyssk._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["bubble_dark"], alpha),
                                   (bx, by), 2)
            pygame.draw.rect(surface,
                             (*_NS_morvyssk.PALETTE["bubble_light"], alpha),
                             (bx, by - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_morvyssk.PALETTE["glow_hot"], alpha),
                             (bx, by - 2, 1, 1))
        # Trail behind
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_morvyssk._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["pool_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["pool_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_morvyssk.PALETTE["glow_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_slime_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_morvyssk._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvyssk._aacircle(aura,
                                       (*_NS_morvyssk.PALETTE["slime_dark"], alpha),
                                       (100, 90), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_morvyssk._alpha((50 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_morvyssk._aacircle(aura,
                                       (*_NS_morvyssk.PALETTE["glow_dark"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Floating slime particles
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["slime_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_light"], (sx, sy, 1, 1))
    def _draw_ground_pool(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvyssk.PALETTE["pool_dark"], 200),
                            (5, 18, 160, 26))
        pygame.draw.ellipse(ring, (*_NS_morvyssk.PALETTE["slime_darkest"], 220),
                            (14, 20, 142, 22))
        pygame.draw.ellipse(ring, (*_NS_morvyssk.PALETTE["pool_mid"], 200),
                            (25, 22, 120, 18))
        pygame.draw.ellipse(ring, (*_NS_morvyssk.PALETTE["glow_dark"],
                                   _NS_morvyssk._alpha(150 * pulse)),
                            (40, 24, 90, 14))
        # Small drip splatters around
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 85 + int(math.cos(angle) * 55)
            y1 = 27 + int(math.sin(angle) * 10)
            pygame.draw.rect(ring, (*_NS_morvyssk.PALETTE["pool_mid"], 220),
                             (x1, y1, 3, 2))
            pygame.draw.rect(ring, (*_NS_morvyssk.PALETTE["glow_light"], 200),
                             (x1, y1, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_morvyssk.PALETTE["glow_hot"],
                                       _NS_morvyssk._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: SPLIT, SPLIT (AoE jump + mini slimes)
    # ============================================================
    def _draw_split_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morvyssk._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Warning circle at landing zone
        if progress < 0.5:
            t = progress / 0.5
            r = int(45 * t)
            alpha = _NS_morvyssk._alpha(220 * t)
            pygame.draw.ellipse(surface, (*_NS_morvyssk.PALETTE["glow_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6), 2)
    def _draw_split_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morvyssk._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Mini slimes launching from boss toward target
            for i in range(3):
                t = min(1.0, progress * 2 + i * 0.1)
                if t > 1.0 or t < 0:
                    continue
                # Arc trajectory (up then down)
                sx = int(x + (tx - x) * t)
                arc_h = -math.sin(t * math.pi) * 40
                sy = int(y + (ty - y) * t + arc_h)
                # Offset for multiple projectiles
                sx += int(math.sin(i * 2) * 15)
                sy += i * 3
                # Slime ball
                size = 6 + i
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                                       (sx + 1, sy + 2), size + 1)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                       (sx, sy), size)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                       (sx, sy), size - 1)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                       (sx, sy), size - 2)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_light"],
                                       (sx - 1, sy - 1), max(1, size - 4))
                pygame.draw.rect(surface, _NS_morvyssk.PALETTE["slime_gloss"],
                                 (sx - 1, sy - 1, 1, 1))
                # Trail of drops
                for j in range(3):
                    trail_t = max(0, t - j * 0.05)
                    if trail_t <= 0:
                        continue
                    trail_x = int(x + (tx - x) * trail_t) + int(math.sin(i * 2) * 15)
                    trail_arc = -math.sin(trail_t * math.pi) * 40
                    trail_y = int(y + (ty - y) * trail_t + trail_arc) + i * 3
                    alpha = _NS_morvyssk._alpha(180 - j * 50)
                    _NS_morvyssk._aacircle(surface,
                                           (*_NS_morvyssk.PALETTE["slime_dark"], alpha),
                                           (trail_x, trail_y), max(1, 4 - j))
        else:
            # Impact splash + mini slimes landed
            t = (progress - 0.5) / 0.5
            splash_r = int(15 + t * 30)
            splash_alpha = _NS_morvyssk._alpha(240 * (1 - t))
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["glow_darkest"], splash_alpha),
                                   (tx, ty), splash_r + 3, 3)
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["glow_mid"], splash_alpha),
                                   (tx, ty), splash_r, 2)
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["glow_light"], splash_alpha),
                                   (tx, ty), max(1, splash_r - 6), 1)
            # Radial burst
            for i in range(10):
                ang = i * math.pi / 5
                ex = tx + int(math.cos(ang) * splash_r)
                ey = ty + int(math.sin(ang) * splash_r * 0.7)
                pygame.draw.line(surface, (*_NS_morvyssk.PALETTE["glow_hot"], splash_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_morvyssk.PALETTE["glow_shine"], splash_alpha),
                                 (ex, ey, 2, 2))
            # Mini slimes on ground after landing
            for i in range(3):
                mini_ang = i * math.pi * 2 / 3 + phase * 0.5
                mx = tx + int(math.cos(mini_ang) * 20)
                my = ty + int(math.sin(mini_ang) * 8)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                       (mx, my), 6)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                       (mx, my), 5)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                       (mx, my), 3)
                pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_light"], (mx, my, 1, 1))
    # ============================================================
    # SKILL W: STICK, STICK (Projectile tether)
    # ============================================================
    def _draw_stick_projectile(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvyssk._target_position(boss, x, y)
        start_x = x + facing * 25
        start_y = y + 2
        if progress < 0.2:
            # Charge in mouth/hand
            t = progress / 0.2
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_morvyssk._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                       (start_x, start_y), r)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                   (start_x, start_y), cr)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                   (start_x, start_y), max(1, cr - 2))
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_hot"],
                                   (start_x, start_y), max(1, cr - 4))
        else:
            # Projectile flying to target with slime tether behind
            t = (progress - 0.2) / 0.8
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # SLIME TETHER trailing behind projectile back to boss
            segments = 12
            for i in range(segments):
                seg_t = i / segments
                seg_x = int(start_x + (bx - start_x) * seg_t)
                seg_y = int(start_y + (by - start_y) * seg_t)
                # Wavy tether
                offset = math.sin(phase * 4 + i * 0.5) * 4 * (1 - seg_t)
                perp_ang = math.atan2(by - start_y, bx - start_x) + math.pi / 2
                seg_x += int(math.cos(perp_ang) * offset)
                seg_y += int(math.sin(perp_ang) * offset)
                if i > 0:
                    thickness = max(2, 6 - i // 3)
                    _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                         prev_pt, (seg_x, seg_y), thickness)
                    _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                         prev_pt, (seg_x, seg_y), max(1, thickness - 2))
                    _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                         prev_pt, (seg_x, seg_y), 1)
                prev_pt = (seg_x, seg_y)
            # Projectile head (slime ball)
            for r in range(10, 0, -1):
                alpha = _NS_morvyssk._alpha(100 * (10 - r) / 10)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_light"], alpha),
                                       (bx, by), r)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["shadow_deep"], (bx + 1, by + 1), 7)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"], (bx, by), 7)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_dark"], (bx, by), 6)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"], (bx, by), 4)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_mid"], (bx, by), 3)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_hot"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_shine"], (bx, by, 1, 1))
            # Spikes on projectile (sticky look)
            for i in range(6):
                sp_ang = phase * 2 + i * math.pi / 3
                spx = bx + int(math.cos(sp_ang) * 8)
                spy = by + int(math.sin(sp_ang) * 8)
                _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["slime_dark"], [
                    (bx + int(math.cos(sp_ang) * 5), by + int(math.sin(sp_ang) * 5)),
                    (spx, spy),
                    (bx + int(math.cos(sp_ang + 0.3) * 5), by + int(math.sin(sp_ang + 0.3) * 5)),
                ])
                pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_light"], (spx, spy, 1, 1))
            # Impact effect on hit
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(10 + st * 15)
                alpha = _NS_morvyssk._alpha(240 * (1 - st))
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                       (tx, ty), max(1, radius - 4), 2)
                for i in range(8):
                    ang = i * math.pi / 4
                    ex = tx + int(math.cos(ang) * radius)
                    ey = ty + int(math.sin(ang) * radius)
                    pygame.draw.rect(surface, (*_NS_morvyssk.PALETTE["glow_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL E: SLAM, SLAM
    # ============================================================
    def _draw_slam_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morvyssk._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning zone
            t = progress / 0.4
            r = int(50 * t)
            alpha = _NS_morvyssk._alpha(220 * t)
            for i in range(3):
                pygame.draw.ellipse(surface,
                                    (*_NS_morvyssk.PALETTE["glow_dark"], alpha),
                                    (tx - r + i * 5, ty - r // 3 + i * 2,
                                     (r - i * 5) * 2, (r - i * 5) * 2 // 3), 2)
        else:
            # Post-slam slime puddle
            t = (progress - 0.4) / 0.6
            r = int(40 + t * 15)
            alpha = _NS_morvyssk._alpha(200 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_morvyssk.PALETTE["slime_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_morvyssk.PALETTE["pool_dark"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_morvyssk.PALETTE["pool_mid"], alpha),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10))
            # Bubbles on puddle
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.3
                bx = tx + int(math.cos(ang) * (r * 0.6))
                by = ty + int(math.sin(ang) * (r * 0.6) * 0.5)
                _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["bubble_dark"], (bx, by), 2)
                pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_light"], (bx, by, 1, 1))
    def _draw_slam_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morvyssk._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Boss jumping in air (energy gathering above target)
            t = progress / 0.4
            jump_y = ty - int((1 - t) * 80)
            for r in range(12, 0, -1):
                alpha = _NS_morvyssk._alpha(180 * (12 - r) / 12)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                       (tx, jump_y), r)
            _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_hot"], (tx, jump_y), 4)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_shine"], (tx, jump_y, 2, 2))
        elif progress < 0.55:
            # SLAM IMPACT
            t = (progress - 0.4) / 0.15
            radius = int(20 + t * 40)
            alpha = _NS_morvyssk._alpha(255 * (1 - t))
            # Shockwave rings
            for i in range(3):
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_darkest"], alpha),
                                       (tx, ty), radius + i * 4, 3)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                       (tx, ty), radius + i * 4 - 2, 2)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_light"], alpha),
                                       (tx, ty), max(1, radius + i * 4 - 4), 1)
            # Ground crystals bursting up (crystal spikes)
            for i in range(8):
                ang = i * math.pi / 4
                crystal_x = tx + int(math.cos(ang) * 25)
                crystal_y = ty + int(math.sin(ang) * 10)
                crystal_h = int(15 * (1 - t))
                _NS_morvyssk._poly(surface,
                                   (*_NS_morvyssk.PALETTE["glow_darkest"], alpha), [
                    (crystal_x - 3, crystal_y),
                    (crystal_x + 3, crystal_y),
                    (crystal_x, crystal_y - crystal_h),
                ])
                _NS_morvyssk._poly(surface,
                                   (*_NS_morvyssk.PALETTE["glow_mid"], alpha), [
                    (crystal_x - 2, crystal_y),
                    (crystal_x + 2, crystal_y),
                    (crystal_x, crystal_y - crystal_h + 1),
                ])
                pygame.draw.rect(surface, (*_NS_morvyssk.PALETTE["glow_shine"], alpha),
                                 (crystal_x, crystal_y - crystal_h, 1, 2))
    # ============================================================
    # SKILL R: GLUE, GLUE (Ultimate CC tether)
    # ============================================================
    def _draw_glue_ground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Sticky pool at boss location
        r = int(40 * min(1.0, progress * 2))
        if r > 3:
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 3, 220), (5, 2, 180), (10, 1, 140),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_morvyssk.PALETTE["glow_dark"],
                                     _NS_morvyssk._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 45 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
    def _draw_glue_tether(surface, boss, x, y, timer, phase):
        """Sticky slime tether pulling target."""
        tx, ty = _NS_morvyssk._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Origin at boss chest core
        origin_x = x
        origin_y = y + 4
        # THICK GOOP TETHER connecting boss to target
        segments = 15
        prev_pt = None
        for i in range(segments + 1):
            t = i / segments
            # Wavy connection
            seg_x = int(origin_x + (tx - origin_x) * t)
            seg_y = int(origin_y + (ty - origin_y) * t)
            wave = math.sin(phase * 3 + i * 0.4) * 6 * math.sin(t * math.pi)
            perp_ang = math.atan2(ty - origin_y, tx - origin_x) + math.pi / 2
            seg_x += int(math.cos(perp_ang) * wave)
            seg_y += int(math.sin(perp_ang) * wave)
            if prev_pt is not None:
                thickness = 8
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["shadow_deep"],
                                     (prev_pt[0] + 2, prev_pt[1] + 2),
                                     (seg_x + 2, seg_y + 2), thickness + 1)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_darkest"],
                                     prev_pt, (seg_x, seg_y), thickness)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_dark"],
                                     prev_pt, (seg_x, seg_y), thickness - 2)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_mid"],
                                     prev_pt, (seg_x, seg_y), thickness - 4)
                _NS_morvyssk._aaline(surface, _NS_morvyssk.PALETTE["slime_light"],
                                     (prev_pt[0], prev_pt[1] - 1),
                                     (seg_x, seg_y - 1), max(1, thickness - 6))
                # Glowing streak
                _NS_morvyssk._aaline(surface,
                                     (*_NS_morvyssk.PALETTE["glow_light"], 200),
                                     prev_pt, (seg_x, seg_y), 1)
            prev_pt = (seg_x, seg_y)
        # Pulsing energy along tether
        for i in range(5):
            pulse_t = (phase * 0.8 + i * 0.2) % 1.0
            px = int(origin_x + (tx - origin_x) * pulse_t)
            py = int(origin_y + (ty - origin_y) * pulse_t)
            wave = math.sin(phase * 3 + pulse_t * 15) * 6 * math.sin(pulse_t * math.pi)
            perp_ang = math.atan2(ty - origin_y, tx - origin_x) + math.pi / 2
            px += int(math.cos(perp_ang) * wave)
            py += int(math.sin(perp_ang) * wave)
            for r in range(5, 0, -1):
                alpha = _NS_morvyssk._alpha(180 * (5 - r) / 5)
                _NS_morvyssk._aacircle(surface,
                                       (*_NS_morvyssk.PALETTE["glow_hot"], alpha),
                                       (px, py), r)
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_shine"], (px, py, 1, 1))
        # Sticky blob at target end
        for r in range(12, 0, -1):
            alpha = _NS_morvyssk._alpha(120 * (12 - r) / 12)
            _NS_morvyssk._aacircle(surface,
                                   (*_NS_morvyssk.PALETTE["glow_mid"], alpha),
                                   (tx, ty), r)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_darkest"], (tx, ty), 8)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_dark"], (tx, ty), 6)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["slime_mid"], (tx, ty), 4)
        _NS_morvyssk._aacircle(surface, _NS_morvyssk.PALETTE["glow_hot"], (tx, ty), 2)
        pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_shine"], (tx, ty, 1, 1))
        # Slime spikes anchoring to target
        for i in range(8):
            ang = i * math.pi / 4 + phase * 0.5
            spike_x = tx + int(math.cos(ang) * 12)
            spike_y = ty + int(math.sin(ang) * 12)
            _NS_morvyssk._poly(surface, _NS_morvyssk.PALETTE["slime_dark"], [
                (tx + int(math.cos(ang) * 6), ty + int(math.sin(ang) * 6)),
                (spike_x, spike_y),
                (tx + int(math.cos(ang + 0.4) * 6), ty + int(math.sin(ang + 0.4) * 6)),
            ])
            pygame.draw.rect(surface, _NS_morvyssk.PALETTE["glow_light"], (spike_x, spike_y, 1, 1))
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_morvyssk).keys()):
    _attr = vars(_NS_morvyssk)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_morvyssk, _attr_name, staticmethod(_attr))



# ====================================================================
# VAELMYRRA (CRIMSON MATRIARCH) - TRUE BOSS
# ====================================================================

class _NS_vaelmyrra:
    """Namespace vaelmyrra - HD crimson matriarch TRUE BOSS."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark obsidian armor
        "armor_darkest": (8, 5, 10),
        "armor_dark": (25, 18, 25),
        "armor_mid": (55, 40, 50),
        "armor_light": (100, 80, 90),
        "armor_shine": (170, 150, 160),
        # Blood crimson (main accent)
        "blood_darkest": (25, 3, 8),
        "blood_dark": (75, 10, 20),
        "blood_mid": (155, 25, 40),
        "blood_light": (225, 55, 70),
        "blood_hot": (255, 100, 100),
        "blood_shine": (255, 180, 170),
        # Gold accents (royal warlord)
        "gold_darkest": (45, 30, 5),
        "gold_dark": (110, 80, 20),
        "gold_mid": (200, 155, 45),
        "gold_light": (245, 210, 105),
        "gold_shine": (255, 240, 180),
        # Skin (dark warlord)
        "skin_darkest": (35, 20, 15),
        "skin_dark": (75, 50, 40),
        "skin_mid": (125, 90, 70),
        "skin_light": (170, 130, 100),
        "skin_shine": (210, 175, 145),
        # White silver hair
        "hair_darkest": (60, 55, 60),
        "hair_dark": (120, 115, 125),
        "hair_mid": (180, 175, 185),
        "hair_light": (225, 220, 230),
        "hair_shine": (255, 255, 255),
        # Fur mantle (black with dark red tips)
        "fur_darkest": (5, 3, 5),
        "fur_dark": (15, 10, 12),
        "fur_mid": (35, 25, 28),
        "fur_light": (65, 50, 55),
        "fur_tip": (90, 30, 40),  # reddish tip
        # Cape / sash red
        "cape_darkest": (25, 5, 10),
        "cape_dark": (65, 15, 25),
        "cape_mid": (120, 30, 40),
        "cape_light": (180, 55, 65),
        # Eye (piercing amber/red)
        "eye_dark": (30, 10, 8),
        "eye_mid": (180, 60, 30),
        "eye_light": (240, 150, 80),
        "eye_glow": (255, 220, 180),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        # Ember/spark
        "ember_dark": (100, 20, 10),
        "ember_mid": (220, 80, 30),
        "ember_light": (255, 180, 80),
        "ember_hot": (255, 240, 180),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vaelmyrra._clamp(color)
        if _NS_vaelmyrra.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vaelmyrra._clamp(color)
        if _NS_vaelmyrra.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_vaelmyrra._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_vaelmyrra._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_vaelmyrra._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vaelmyrra(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vaelmyrra._detect_moving(boss)
        _NS_vaelmyrra._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_vae_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # TRUE BOSS ambient (bigger scale)
        _NS_vaelmyrra._draw_blood_aura(surface, x, y, pulse)
        _NS_vaelmyrra._draw_ground_ring(surface, x, y + 55, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":
            _NS_vaelmyrra._draw_execution_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaelmyrra._draw_ultimate_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vaelmyrra._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with intimidating hover
        if attacking:
            _NS_vaelmyrra._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_vaelmyrra._draw_float_move(surface, boss, x, y)
        else:
            _NS_vaelmyrra._draw_float_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_vaelmyrra._draw_sweep_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vaelmyrra._draw_dash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vaelmyrra._draw_execution_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaelmyrra._draw_ultimate_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vae_previous_timer", 0))
        active = bool(getattr(boss, "_vae_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vae_attack_active = True
            boss._vae_attack_frame = 0
            active = True
            # Alternate blade side each attack
            boss._vae_attack_side = 1 - getattr(boss, "_vae_attack_side", 0)
        elif active and timer > 0:
            boss._vae_attack_frame = int(getattr(boss, "_vae_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vae_attack_active = False
            boss._vae_attack_frame = 0
            active = False
        boss._vae_previous_timer = timer
        boss._vae_attack_progress = (
            min(1.0, getattr(boss, "_vae_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_vae_last_x"):
            boss._vae_last_x = boss.x
            boss._vae_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vae_last_x)
        dy = abs(boss.y - boss._vae_last_y)
        boss._vae_last_x = boss.x
        boss._vae_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        sway = int(math.sin(boss.pulse * 0.35) * 2)
        _NS_vaelmyrra._draw_hover_shadow(surface, x, y + 60, boss.pulse)
        _NS_vaelmyrra._draw_hover_energy(surface, x, y + 45, boss.pulse)
        _NS_vaelmyrra._draw_body(surface, x + sway, y + bob,
                                 boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_vaelmyrra._draw_hover_shadow(surface, x + sway, y + 60, phase)
        _NS_vaelmyrra._draw_hover_energy(surface, x + sway, y + 45, phase,
                                         trail=True, facing=boss.direction)
        _NS_vaelmyrra._draw_body(surface, x + sway, y + bob,
                                 boss.direction, phase, "move")
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_vae_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back → forward slash → recover
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 6) * boss.direction
            lift = int(t * 5)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-6 + t * 20)) * boss.direction
            lift = int(5 - t * 8)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3)
        _NS_vaelmyrra._draw_hover_shadow(surface, x + lunge, y + 60, boss.pulse)
        _NS_vaelmyrra._draw_hover_energy(surface, x + lunge, y + 45, boss.pulse,
                                         intense=True)
        _NS_vaelmyrra._draw_body(surface, x + lunge, y - lift,
                                 boss.direction, boss.pulse, "attack", progress)
        _NS_vaelmyrra._draw_blade_swing_fx(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY (bigger than mini-boss)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Draw cape red sash BEHIND
        _NS_vaelmyrra._draw_cape_sash(surface, cx, cy, facing, phase, action)
        # Legs (armored)
        _NS_vaelmyrra._draw_legs(surface, cx, cy + 26, facing, phase)
        # Torso armor
        _NS_vaelmyrra._draw_torso(surface, cx, cy, facing, phase)
        # FUR MANTLE on shoulders (iconic)
        _NS_vaelmyrra._draw_fur_mantle(surface, cx, cy - 10, facing, phase)
        # Arms (dual wielders)
        _NS_vaelmyrra._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head (dark skin, silver curls)
        _NS_vaelmyrra._draw_head(surface, cx, cy - 28, facing, phase)
        # DUAL CURVED BLADES (khopesh/scimitars)
        _NS_vaelmyrra._draw_dual_blades(surface, cx, cy, facing, phase, action, attack_progress)
    # ---------- CAPE / SASH ----------
    def _draw_cape_sash(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 3
        if action == "move":
            sway = math.sin(phase * 1.2) * 5
        # Sash hanging from waist (red flowing cloth)
        back_dir = -facing
        base_x = cx + back_dir * 4
        base_y = cy + 12
        # Long sash flowing behind
        sash_pts = [
            (base_x - 6, base_y),
            (base_x + 10 * back_dir, base_y),
            (base_x + 14 * back_dir + int(sway), base_y + 30),
            (base_x + int(sway * 1.2), base_y + 40),
            (base_x - 8 + int(sway * 0.5), base_y + 32),
        ]
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in sash_pts])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["cape_darkest"], sash_pts)
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["cape_dark"], [
            (base_x - 5, base_y + 1),
            (base_x + 9 * back_dir, base_y + 1),
            (base_x + 12 * back_dir + int(sway * 0.9), base_y + 28),
            (base_x + int(sway * 1.1), base_y + 37),
            (base_x - 6 + int(sway * 0.4), base_y + 30),
        ])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["cape_mid"], [
            (base_x - 3, base_y + 2),
            (base_x + 6 * back_dir, base_y + 2),
            (base_x + 8 * back_dir + int(sway * 0.7), base_y + 22),
            (base_x + int(sway * 0.9), base_y + 30),
            (base_x - 3 + int(sway * 0.3), base_y + 24),
        ])
        # Highlight strand
        pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["cape_light"],
                         (base_x, base_y + 2),
                         (base_x + int(sway), base_y + 30), 1)
        # Gold trim edge along bottom
        for i in range(4):
            t = i / 3
            px = int(sash_pts[2][0] + (sash_pts[3][0] - sash_pts[2][0]) * t)
            py = int(sash_pts[2][1] + (sash_pts[3][1] - sash_pts[2][1]) * t)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_dark"], (px, py, 2, 2))
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_mid"], (px, py, 1, 1))
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase):
        for side in (-1, 1):
            lx = cx + side * 5
            ly = cy
            # Thigh armor
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["shadow_deep"], [
                (lx - 4 + 1, ly + 1), (lx + 4 + 1, ly + 1),
                (lx + 5 + 1, ly + 12 + 1), (lx - 5 + 1, ly + 12 + 1),
            ])
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_darkest"], [
                (lx - 4, ly), (lx + 4, ly), (lx + 5, ly + 12), (lx - 5, ly + 12),
            ])
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_dark"], [
                (lx - 3, ly + 1), (lx + 3, ly + 1),
                (lx + 4, ly + 11), (lx - 4, ly + 11),
            ])
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_mid"], [
                (lx - 2, ly + 2), (lx + 2, ly + 2),
                (lx + 3, ly + 10), (lx - 3, ly + 10),
            ])
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["armor_light"],
                             (lx, ly + 2), (lx, ly + 10), 1)
            # Gold trim on top
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                             (lx - 4, ly), (lx + 4, ly), 1)
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_mid"],
                             (lx - 3, ly), (lx + 3, ly), 1)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_shine"],
                             (lx - 1, ly, 2, 1))
            # Red slit down thigh (armor gap accent)
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["blood_dark"],
                             (lx, ly + 3), (lx, ly + 9), 1)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_mid"], (lx, ly + 5, 1, 1))
            # Knee cap
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_darkest"],
                                    (lx, ly + 12), 4)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_dark"],
                                    (lx, ly + 12), 3)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_mid"],
                                    (lx, ly + 12), 2)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_mid"],
                             (lx, ly + 12, 1, 1))
            # Boot (armored)
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_darkest"], [
                (lx - 4, ly + 15), (lx + 4, ly + 15),
                (lx + 6, ly + 20), (lx - 3, ly + 20),
            ])
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_dark"], [
                (lx - 3, ly + 16), (lx + 3, ly + 16),
                (lx + 5, ly + 19), (lx - 2, ly + 19),
            ])
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_mid"], [
                (lx - 2, ly + 17), (lx + 2, ly + 17),
                (lx + 4, ly + 18), (lx - 1, ly + 18),
            ])
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                             (lx + 3, ly + 18, 2, 1))
    # ---------- TORSO ----------
    def _draw_torso(surface, cx, cy, facing, phase):
        # Feminine warrior silhouette (bigger for TRUE BOSS)
        pts = [
            (cx - 12, cy - 10),
            (cx - 14, cy - 5),
            (cx - 13, cy + 6),
            (cx - 10, cy + 18),
            (cx + 10, cy + 18),
            (cx + 13, cy + 6),
            (cx + 14, cy - 5),
            (cx + 12, cy - 10),
        ]
        # Shadow
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in pts])
        # Base
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_darkest"], pts)
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_dark"], [
            (cx - 11, cy - 9), (cx - 13, cy - 5), (cx - 12, cy + 5),
            (cx - 9, cy + 17), (cx + 9, cy + 17),
            (cx + 12, cy + 5), (cx + 13, cy - 5), (cx + 11, cy - 9),
        ])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_mid"], [
            (cx - 9, cy - 7), (cx - 11, cy - 3), (cx - 10, cy + 3),
            (cx - 7, cy + 14), (cx + 7, cy + 14),
            (cx + 10, cy + 3), (cx + 11, cy - 3), (cx + 9, cy - 7),
        ])
        # Central chest V (armor plating)
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_light"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 2, cy + 2), (cx, cy + 4), (cx - 2, cy + 2),
        ])
        pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["armor_shine"],
                         (cx - 1, cy - 5), (cx - 1, cy + 2), 1)
        # RED CENTER EMBLEM (matriarch crest — inverted triangle blood mark)
        emb_x = cx
        emb_y = cy - 1
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["blood_darkest"], [
            (emb_x - 3, emb_y - 3), (emb_x + 3, emb_y - 3),
            (emb_x, emb_y + 3),
        ])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["blood_dark"], [
            (emb_x - 2, emb_y - 2), (emb_x + 2, emb_y - 2),
            (emb_x, emb_y + 2),
        ])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["blood_mid"], [
            (emb_x - 1, emb_y - 1), (emb_x + 1, emb_y - 1),
            (emb_x, emb_y + 1),
        ])
        # Emblem glow
        emblem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_vaelmyrra._alpha(80 * (6 - r) / 6 * emblem_pulse)
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                    (emb_x, emb_y), r)
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_shine"],
                         (emb_x, emb_y, 1, 1))
        # Belt (gold with red center)
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["armor_darkest"],
                         (cx - 11, cy + 12, 22, 5))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["armor_dark"],
                         (cx - 10, cy + 12, 20, 3))
        # Gold trim on belt
        pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                         (cx - 11, cy + 12), (cx + 11, cy + 12), 1)
        pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_mid"],
                         (cx - 10, cy + 12), (cx + 10, cy + 12), 1)
        # Center belt buckle (gold with blood gem)
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_darkest"],
                         (cx - 4, cy + 12, 8, 5))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                         (cx - 3, cy + 13, 6, 3))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_mid"],
                         (cx - 2, cy + 13, 4, 2))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_mid"],
                         (cx - 1, cy + 14, 2, 2))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_hot"],
                         (cx, cy + 14, 1, 1))
    # ---------- FUR MANTLE (iconic feature) ----------
    def _draw_fur_mantle(surface, cx, cy, facing, phase):
        """Large black fur pauldron covering shoulders."""
        # Base mantle silhouette (spans across both shoulders + neck)
        mantle_pts = [
            (cx - 18, cy + 2),
            (cx - 22, cy - 2),
            (cx - 20, cy - 8),
            (cx - 14, cy - 11),
            (cx - 6, cy - 13),
            (cx, cy - 14),
            (cx + 6, cy - 13),
            (cx + 14, cy - 11),
            (cx + 20, cy - 8),
            (cx + 22, cy - 2),
            (cx + 18, cy + 2),
            (cx + 14, cy + 5),
            (cx - 14, cy + 5),
        ]
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in mantle_pts])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["fur_darkest"], mantle_pts)
        # Layered fur texture (jagged edges)
        # Middle darker
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["fur_dark"], [
            (cx - 17, cy + 1), (cx - 20, cy - 3),
            (cx - 18, cy - 7), (cx - 12, cy - 10),
            (cx - 4, cy - 12), (cx + 4, cy - 12),
            (cx + 12, cy - 10), (cx + 18, cy - 7),
            (cx + 20, cy - 3), (cx + 17, cy + 1),
            (cx + 12, cy + 3), (cx - 12, cy + 3),
        ])
        # Mid tone highlights (fur clumps)
        for clump_x in (-15, -8, 0, 8, 15):
            clump_cx = cx + clump_x
            clump_y = cy - 6 + int(math.sin(phase * 0.5 + clump_x * 0.1) * 1)
            _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["fur_mid"], [
                (clump_cx - 3, clump_y),
                (clump_cx - 2, clump_y - 4),
                (clump_cx, clump_y - 5),
                (clump_cx + 2, clump_y - 4),
                (clump_cx + 3, clump_y),
            ])
            # Highlight tip
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["fur_light"],
                             (clump_cx - 1, clump_y - 4),
                             (clump_cx + 1, clump_y - 4), 1)
        # Red tips on outer fur (blood-stained warrior look)
        for tip_x in (-20, -10, 10, 20):
            tip_cx = cx + tip_x
            tip_y = cy - 8
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["fur_tip"],
                             (tip_cx - 1, tip_y),
                             (tip_cx + 1, tip_y - 2), 1)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_dark"],
                             (tip_cx, tip_y - 2, 1, 1))
        # Jagged bottom fur strands hanging
        for hang_x in (-16, -8, 8, 16):
            hang_cx = cx + hang_x
            hang_y = cy + 3
            wisp_len = 4 + int(math.sin(phase * 0.7 + hang_x * 0.2) * 1)
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["fur_darkest"],
                             (hang_cx, hang_y),
                             (hang_cx, hang_y + wisp_len), 2)
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["fur_dark"],
                             (hang_cx, hang_y),
                             (hang_cx, hang_y + wisp_len), 1)
            # Red tip
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["fur_tip"],
                             (hang_cx, hang_y + wisp_len, 1, 1))
    # ---------- ARMS (dual wielders) ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        attack_side = getattr(_NS_vaelmyrra, "_current_attack_side", 1)
        # Each attack alternates which arm swings
        # side 1 = right, -1 = left
        for side in (-1, 1):
            base_x = cx + side * 14
            base_y = cy - 4
            is_attacking_side = (action == "attack" and side == (attack_side if attack_side else facing))
            # Simplify: always right-side (facing) leads attack
            is_attacking_side = (action == "attack" and side * facing > 0)
            if is_attacking_side:
                if attack_progress < 0.35:
                    # Wind up UP-BACK
                    t = attack_progress / 0.35
                    elbow_offset_x = int(-8 * facing)
                    elbow_offset_y = int(-9 - t * 2)
                    hand_offset_x = int(-13 * facing)
                    hand_offset_y = int(-15)
                elif attack_progress < 0.6:
                    # Swing down-forward
                    t = (attack_progress - 0.35) / 0.25
                    elbow_offset_x = int((-8 + t * 16) * facing)
                    elbow_offset_y = int(-11 + t * 18)
                    hand_offset_x = int((-13 + t * 28) * facing)
                    hand_offset_y = int(-15 + t * 22)
                else:
                    # Recovery
                    t = (attack_progress - 0.6) / 0.4
                    elbow_offset_x = int((8 - t * 3) * facing)
                    elbow_offset_y = int(7 - t * 2)
                    hand_offset_x = int((15 - t * 4) * facing)
                    hand_offset_y = int(7 + t * 1)
            else:
                # Idle stance — arm at side holding blade
                swing = math.sin(phase * 0.6 + side) * 0.15
                elbow_offset_x = int(math.sin(swing) * 3 * side)
                elbow_offset_y = 7
                hand_offset_x = int(math.sin(swing * 1.2) * 5 * side + side * 4)
                hand_offset_y = 14
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm (armored)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                                  (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 7)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["armor_darkest"],
                                  (base_x, base_y), (elbow_x, elbow_y), 6)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["armor_dark"],
                                  (base_x, base_y), (elbow_x, elbow_y), 4)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["armor_mid"],
                                  (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["armor_light"],
                                  (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow joint (gold accent)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_darkest"],
                                    (elbow_x, elbow_y), 4)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_dark"],
                                    (elbow_x, elbow_y), 3)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                                    (elbow_x, elbow_y), 2)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_mid"],
                             (elbow_x, elbow_y, 1, 1))
            # Forearm (skin visible or armor — for warrior look, some skin)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                                  (elbow_x + 1, elbow_y + 2), (hand_x + 1, hand_y + 2), 5)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["skin_darkest"],
                                  (elbow_x, elbow_y), (hand_x, hand_y), 4)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["skin_dark"],
                                  (elbow_x, elbow_y), (hand_x, hand_y), 3)
            _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["skin_mid"],
                                  (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
            # Gauntlet on wrist (bracer)
            wrist_x = int((elbow_x + hand_x) * 0.55)
            wrist_y = int((elbow_y + hand_y) * 0.55)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_darkest"],
                                    (wrist_x, wrist_y), 3)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_dark"],
                                    (wrist_x, wrist_y), 2)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                             (wrist_x, wrist_y, 1, 1))
            # Hand grip (dark)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                                    (hand_x + 1, hand_y + 1), 4)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_darkest"],
                                    (hand_x, hand_y), 3)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["armor_dark"],
                                    (hand_x, hand_y), 2)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["skin_mid"],
                             (hand_x, hand_y, 1, 1))
            # Store hand positions for blade attachment
            if side > 0:
                _NS_vaelmyrra._hand_right = (hand_x, hand_y)
            else:
                _NS_vaelmyrra._hand_left = (hand_x, hand_y)
    # ---------- HEAD (dark skin, silver curls) ----------
    def _draw_head(surface, cx, cy, facing, phase):
        # Face — narrower, fierce
        face_pts = [
            (cx - 6, cy - 3),
            (cx - 7, cy + 1),
            (cx - 6, cy + 5),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 6, cy + 5),
            (cx + 7, cy + 1),
            (cx + 6, cy - 3),
            (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ]
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["skin_darkest"], face_pts)
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["skin_dark"], [
            (cx - 5, cy - 2), (cx - 6, cy + 1),
            (cx - 5, cy + 4), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 4),
            (cx + 6, cy + 1), (cx + 5, cy - 2),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["skin_mid"], [
            (cx - 3, cy - 1), (cx - 4, cy + 1),
            (cx - 3, cy + 3), (cx - 1, cy + 6),
            (cx + 1, cy + 6), (cx + 3, cy + 3),
            (cx + 4, cy + 1), (cx + 3, cy - 1),
            (cx + 2, cy - 5), (cx - 2, cy - 5),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["skin_light"],
                         (cx - 2 * facing, cy, 1, 1))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["skin_shine"],
                         (cx - 2 * facing, cy - 1, 1, 1))
        # EYES — piercing amber/red glow
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            # Deep socket
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["shadow_deep"], (ex - 1, ey, 2, 1))
            # Glow halo
            for r in range(4, 0, -1):
                alpha = _NS_vaelmyrra._alpha(120 * (4 - r) / 4 * eye_pulse)
                _NS_vaelmyrra._aacircle(surface,
                                        (*_NS_vaelmyrra.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # Scar across face (warrior mark)
        pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["skin_darkest"],
                         (cx - 3 * facing, cy - 2),
                         (cx - facing, cy + 3), 1)
        # LIPS (firm line)
        pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["skin_darkest"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
        # SILVER CURLY HAIR (iconic)
        _NS_vaelmyrra._draw_silver_curls(surface, cx, cy, facing, phase)
    def _draw_silver_curls(surface, cx, cy, facing, phase):
        """Distinctive white/silver curly hair volume."""
        sway = math.sin(phase * 0.4) * 1
        # Large voluminous hair silhouette
        hair_pts = [
            (cx - 8, cy - 4),
            (cx - 10, cy - 2),
            (cx - 11, cy - 6),
            (cx - 9, cy - 10),
            (cx - 5, cy - 12),
            (cx, cy - 13),
            (cx + 5, cy - 12),
            (cx + 9, cy - 10),
            (cx + 11, cy - 6),
            (cx + 10, cy - 2),
            (cx + 8, cy - 4),
            (cx + 6, cy - 6),
            (cx - 6, cy - 6),
        ]
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["hair_darkest"], hair_pts)
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["hair_dark"], [
            (cx - 8, cy - 5), (cx - 10, cy - 7),
            (cx - 8, cy - 10), (cx - 4, cy - 11),
            (cx + 4, cy - 11), (cx + 8, cy - 10),
            (cx + 10, cy - 7), (cx + 8, cy - 5),
            (cx + 5, cy - 7), (cx - 5, cy - 7),
        ])
        # Curl highlights (clumps of curly texture)
        for curl_x in (-8, -3, 3, 8):
            curl_cx = cx + curl_x
            curl_y = cy - 9 + int(sway)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["hair_mid"],
                                    (curl_cx, curl_y), 3)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["hair_light"],
                                    (curl_cx - 1, curl_y - 1), 2)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["hair_shine"],
                             (curl_cx - 1, curl_y - 1, 1, 1))
        # Additional curl on top
        for top_curl in (-5, 0, 5):
            tx = cx + top_curl
            ty = cy - 11 + int(sway)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["hair_mid"],
                                    (tx, ty), 2)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["hair_light"],
                                    (tx, ty), 1)
        # Side curl hanging down (visible on facing side)
        side_curl_x = cx + facing * 8
        for i in range(3):
            cx_i = side_curl_x + int(math.sin(phase * 0.5 + i) * 1)
            cy_i = cy - 3 + i * 3
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["hair_dark"],
                                    (cx_i, cy_i), 2)
            _NS_vaelmyrra._aacircle(surface, _NS_vaelmyrra.PALETTE["hair_mid"],
                                    (cx_i - 1, cy_i - 1), 1)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["hair_light"],
                             (cx_i - 1, cy_i - 1, 1, 1))
    # ---------- DUAL CURVED BLADES (khopesh / scimitars) ----------
    def _draw_dual_blades(surface, cx, cy, facing, phase, action, attack_progress):
        # Get hand positions
        hand_r = getattr(_NS_vaelmyrra, "_hand_right", (cx + 20, cy + 8))
        hand_l = getattr(_NS_vaelmyrra, "_hand_left", (cx - 20, cy + 8))
        # Blade attached to each hand
        for side, hand in ((1, hand_r), (-1, hand_l)):
            is_attacking_side = (action == "attack" and side * facing > 0)
            _NS_vaelmyrra._draw_curved_blade(surface, hand[0], hand[1], facing,
                                             side, phase, action, attack_progress,
                                             is_attacking_side)
    def _draw_curved_blade(surface, hx, hy, facing, blade_side, phase, action,
                            attack_progress, is_attacking):
        """Curved khopesh-style blade (sabit)."""
        blade_len = 32
        # Blade angle
        if is_attacking:
            if attack_progress < 0.35:
                # Wind-up UP-BACK
                if facing > 0:
                    blade_angle = -math.pi * 0.75
                else:
                    blade_angle = -math.pi * 0.25
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                if facing > 0:
                    blade_angle = -math.pi * 0.75 + t * math.pi
                else:
                    blade_angle = -math.pi * 0.25 - t * math.pi
            else:
                t = (attack_progress - 0.6) / 0.4
                if facing > 0:
                    blade_angle = math.pi * 0.25 - t * math.pi * 0.1
                else:
                    blade_angle = math.pi * 0.75 + t * math.pi * 0.1
        else:
            # Idle: blades pointing down-outward
            if blade_side > 0:
                blade_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.03
            else:
                blade_angle = math.pi * 0.65 + math.sin(phase * 0.5) * 0.03
        # KHOPESH CURVE — blade curves outward at top
        # Compute base, mid, and tip with curvature
        base_x, base_y = hx, hy
        # Straight segment first (short)
        straight_len = 10
        straight_end_x = base_x + int(math.cos(blade_angle) * straight_len)
        straight_end_y = base_y + int(math.sin(blade_angle) * straight_len)
        # Curved segment — perpendicular offset increases toward tip
        # Curve outward (blade_side positive = curve right)
        curve_dir = 1 if blade_side > 0 else -1
        # Compute curve points (bezier-like)
        segments = 8
        blade_points_edge_out = []
        blade_points_edge_in = []
        for i in range(segments + 1):
            t = i / segments
            # Position along blade
            along_x = straight_end_x + int(math.cos(blade_angle) * (blade_len - straight_len) * t)
            along_y = straight_end_y + int(math.sin(blade_angle) * (blade_len - straight_len) * t)
            # Curve offset (parabolic)
            curve_off = math.sin(t * math.pi * 0.7) * 12 * curve_dir
            # Perpendicular direction from blade axis
            perp = blade_angle + math.pi / 2
            curve_x = int(math.cos(perp) * curve_off)
            curve_y = int(math.sin(perp) * curve_off)
            center_x = along_x + curve_x
            center_y = along_y + curve_y
            # Blade thickness (thicker in middle, taper at ends)
            thick = int(3 + math.sin(t * math.pi) * 2)
            edge_out_x = center_x + int(math.cos(perp) * thick * curve_dir)
            edge_out_y = center_y + int(math.sin(perp) * thick * curve_dir)
            edge_in_x = center_x - int(math.cos(perp) * thick * curve_dir)
            edge_in_y = center_y - int(math.sin(perp) * thick * curve_dir)
            blade_points_edge_out.append((edge_out_x, edge_out_y))
            blade_points_edge_in.append((edge_in_x, edge_in_y))
        # Build blade polygon
        blade_poly = blade_points_edge_out + list(reversed(blade_points_edge_in))
        # Add straight base
        base_perp_x = int(math.cos(blade_angle + math.pi / 2) * 3)
        base_perp_y = int(math.sin(blade_angle + math.pi / 2) * 3)
        blade_poly = ([
            (base_x + base_perp_x, base_y + base_perp_y),
            (base_x - base_perp_x, base_y - base_perp_y),
        ] + blade_poly)
        # Shadow
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in blade_poly])
        # Base blade (darkest)
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_darkest"], blade_poly)
        # Layered blade (mid)
        inner_poly = []
        for p in blade_poly:
            inner_poly.append((int(p[0] * 0.85 + (base_x + (straight_end_x - base_x) * 0.7) * 0.15),
                               int(p[1] * 0.85 + (base_y + (straight_end_y - base_y) * 0.7) * 0.15)))
        _NS_vaelmyrra._poly(surface, _NS_vaelmyrra.PALETTE["armor_dark"], inner_poly)
        # Gold trim edge (outer cutting edge)
        for i in range(len(blade_points_edge_out) - 1):
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_darkest"],
                             blade_points_edge_out[i], blade_points_edge_out[i + 1], 3)
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_dark"],
                             blade_points_edge_out[i], blade_points_edge_out[i + 1], 2)
            pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["gold_mid"],
                             blade_points_edge_out[i], blade_points_edge_out[i + 1], 1)
        # Blade center line highlight
        for i in range(segments):
            t = i / segments
            along_x = straight_end_x + int(math.cos(blade_angle) * (blade_len - straight_len) * t)
            along_y = straight_end_y + int(math.sin(blade_angle) * (blade_len - straight_len) * t)
            curve_off = math.sin(t * math.pi * 0.7) * 12 * curve_dir
            perp = blade_angle + math.pi / 2
            cx_line = along_x + int(math.cos(perp) * curve_off)
            cy_line = along_y + int(math.sin(perp) * curve_off)
            if i > 0:
                pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["armor_mid"],
                                 prev_line, (cx_line, cy_line), 2)
                pygame.draw.line(surface, _NS_vaelmyrra.PALETTE["armor_light"],
                                 prev_line, (cx_line, cy_line), 1)
            prev_line = (cx_line, cy_line)
        # BLOOD RED GLOW along inner edge (menacing)
        glow_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for i in range(len(blade_points_edge_in) - 1):
            _NS_vaelmyrra._aaline(surface,
                                  (*_NS_vaelmyrra.PALETTE["blood_dark"],
                                   _NS_vaelmyrra._alpha(180 * glow_pulse)),
                                  blade_points_edge_in[i],
                                  blade_points_edge_in[i + 1], 2)
            _NS_vaelmyrra._aaline(surface,
                                  (*_NS_vaelmyrra.PALETTE["blood_mid"],
                                   _NS_vaelmyrra._alpha(220 * glow_pulse)),
                                  blade_points_edge_in[i],
                                  blade_points_edge_in[i + 1], 1)
        # Tip sparkle
        tip_x, tip_y = blade_points_edge_out[-1]
        for r in range(5, 0, -1):
            alpha = _NS_vaelmyrra._alpha(150 * (5 - r) / 5 * glow_pulse)
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_light"], alpha),
                                    (tip_x, tip_y), r)
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_hot"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_shine"], (tip_x, tip_y, 1, 1))
        # Hilt guard (gold cross)
        guard_perp = blade_angle + math.pi / 2
        guard_len = 4
        ga = (base_x + int(math.cos(guard_perp) * guard_len),
              base_y + int(math.sin(guard_perp) * guard_len))
        gb = (base_x - int(math.cos(guard_perp) * guard_len),
              base_y - int(math.sin(guard_perp) * guard_len))
        _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["gold_darkest"], ga, gb, 3)
        _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["gold_dark"], ga, gb, 2)
        _NS_vaelmyrra._aaline(surface, _NS_vaelmyrra.PALETTE["gold_mid"], ga, gb, 1)
    # ============================================================
    # ATTACK FX: Dual blade crescent swing
    # ============================================================
    def _draw_blade_swing_fx(surface, boss, x, y, progress):
        if progress < 0.35 or progress > 0.75:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.4
        arc_cx = x + facing * 12
        arc_cy = y - 4
        # BIG BLOOD RED crescent slash
        for i in range(5):
            layer_t = max(0, t - i * 0.08)
            if layer_t <= 0:
                continue
            alpha = _NS_vaelmyrra._alpha(255 * (1 - layer_t) * (1 - i * 0.15))
            radius = int(32 + layer_t * 10 + i * 3)
            if facing > 0:
                start_angle = -math.pi * 0.75
                end_angle = math.pi * 0.25
            else:
                start_angle = -math.pi * 0.25
                end_angle = math.pi * 0.75 + math.pi
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 14
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                          prev_pt, (px, py), 6)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                          prev_pt, (px, py), 4)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                          prev_pt, (px, py), 2)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_light"], alpha),
                                          prev_pt, (px, py), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                     (px, py, 1, 1))
                prev_pt = (px, py)
        # Blood spatters flying outward
        if facing > 0:
            lead_angle = -math.pi * 0.75 + math.pi * t
        else:
            lead_angle = -math.pi * 0.25 - math.pi * t
        for i in range(12):
            spark_r = 32 + i * 3
            sx = arc_cx + int(math.cos(lead_angle) * spark_r)
            sy = arc_cy + int(math.sin(lead_angle) * spark_r)
            alpha = _NS_vaelmyrra._alpha(240 * (1 - i / 12))
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                    (sx, sy), 3)
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND (TRUE BOSS scale)
    # ============================================================
    def _draw_hover_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((160, 34), pygame.SRCALPHA)
        for radius in range(16, 0, -1):
            alpha = max(0, int((16 - radius) * 15 * pulse))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 17 - radius, 140 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 5, 180), (5, 10, 150, 14))
        pygame.draw.ellipse(shadow, (40, 10, 20, 120), (15, 12, 130, 10))
        surface.blit(shadow, (x - 80, y - 17))
    def _draw_hover_energy(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blood/ember plumes below."""
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Blood mist
        mist = pygame.Surface((160, 45), pygame.SRCALPHA)
        for radius in range(35, 3, -3):
            alpha = _NS_vaelmyrra._alpha((35 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                    (80 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2))
                )
        for radius in range(22, 3, -2):
            alpha = _NS_vaelmyrra._alpha((22 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                    (80 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 80, cy - 8))
        # Rising blood embers
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = _NS_vaelmyrra._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["ember_dark"], alpha),
                                    (sx, sy), 3)
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["ember_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["ember_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["ember_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vaelmyrra._alpha(180 - i * 28)
                if alpha <= 0:
                    continue
                _NS_vaelmyrra._aacircle(surface,
                                        (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_vaelmyrra._aacircle(surface,
                                        (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["ember_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_blood_aura(surface, x, y, phase):
        """TRUE BOSS massive aura - blood red intimidating."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_vaelmyrra._alpha((105 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_vaelmyrra._aacircle(aura,
                                        (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                        (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_vaelmyrra._alpha((70 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vaelmyrra._aacircle(aura,
                                        (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                        (120, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_vaelmyrra._alpha((40 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_vaelmyrra._aacircle(aura,
                                        (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                        (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["ember_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["ember_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Big TRUE BOSS ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vaelmyrra.PALETTE["blood_darkest"], 200),
                            (5, 20, 170, 28), 4)
        pygame.draw.ellipse(ring, (*_NS_vaelmyrra.PALETTE["armor_darkest"], 220),
                            (14, 22, 152, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_vaelmyrra.PALETTE["blood_dark"], 230),
                            (25, 24, 130, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_vaelmyrra.PALETTE["blood_mid"],
                                   _NS_vaelmyrra._alpha(180 * pulse)),
                            (40, 26, 100, 16), 1)
        # Runes / spikes around
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 30 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 30 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_vaelmyrra.PALETTE["blood_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, (*_NS_vaelmyrra.PALETTE["blood_hot"], 240),
                             (x2, y2, 2, 2))
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_vaelmyrra.PALETTE["blood_hot"],
                                 _NS_vaelmyrra._alpha(160 * pulse)),
                                (15, 15, 150, 40), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q: SOVEREIGN'S SWEEP (wide crimson arc)
    # ============================================================
    def _draw_sweep_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        arc_cx = x + facing * 14
        arc_cy = y - 4
        if progress < 0.15:
            # Wind-up glow
            return
        t = (progress - 0.15) / 0.85
        # HUGE arc with dark crimson trail
        for i in range(7):
            layer_t = max(0, t - i * 0.06)
            if layer_t <= 0:
                continue
            alpha = _NS_vaelmyrra._alpha(255 * (1 - layer_t) * (1 - i * 0.12))
            radius = int(50 + layer_t * 15 + i * 4)
            if facing > 0:
                start_angle = -math.pi * 0.75
                end_angle = math.pi * 0.35
            else:
                start_angle = -math.pi * 0.25
                end_angle = math.pi * 0.75 + math.pi
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 18
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                          prev_pt, (px, py), 8)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                          prev_pt, (px, py), 5)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                          prev_pt, (px, py), 3)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_light"], alpha),
                                          prev_pt, (px, py), 2)
                    _NS_vaelmyrra._aaline(surface,
                                          (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                          prev_pt, (px, py), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_vaelmyrra.PALETTE["blood_shine"], alpha),
                                     (px, py, 2, 2))
                prev_pt = (px, py)
        # Blood spatter rain
        for i in range(18):
            spatter_t = (phase * 2 + i * 0.15) % 1.0
            spatter_ang = -math.pi * 0.5 + math.pi * spatter_t * facing
            sr = 50 + int(math.sin(i * 2) * 20)
            sx = arc_cx + int(math.cos(spatter_ang) * sr)
            sy = arc_cy + int(math.sin(spatter_ang) * sr) + int(spatter_t * 15)
            alpha = _NS_vaelmyrra._alpha(230 * (1 - spatter_t))
            pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                             (sx, sy, 3, 3))
            pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL W: RELENTLESS ASSAULT (triple dash)
    # ============================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        pass  # foreground handles
    def _draw_dash_foreground(surface, boss, x, y, timer, phase):
        """Triple dash forward with blade trail."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Motion streaks behind
        trail_len = 90
        for i in range(12):
            t = i / 12
            tx = x - facing * int(trail_len * t)
            ty = y + int(math.sin(t * math.pi * 2) * 4)
            alpha = _NS_vaelmyrra._alpha(220 * (1 - t) * (1 - progress * 0.3))
            _NS_vaelmyrra._aaline(surface,
                                  (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                  (tx, ty), (tx + facing * 12, ty), 6)
            _NS_vaelmyrra._aaline(surface,
                                  (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                  (tx, ty), (tx + facing * 12, ty), 4)
            _NS_vaelmyrra._aaline(surface,
                                  (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                  (tx, ty), (tx + facing * 12, ty), 2)
            _NS_vaelmyrra._aaline(surface,
                                  (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                  (tx, ty), (tx + facing * 12, ty), 1)
        # Blade slash marks at dash positions (3 pulses = 3 dashes)
        for dash_i in range(3):
            dash_phase = (progress * 3) - dash_i
            if 0 <= dash_phase <= 1:
                dash_x = x - facing * int(dash_phase * 40)
                dash_alpha = _NS_vaelmyrra._alpha(255 * (1 - dash_phase))
                # X slash mark
                for a in (math.pi / 4, -math.pi / 4):
                    end1_x = dash_x + int(math.cos(a) * 15)
                    end1_y = y + int(math.sin(a) * 15) - 5
                    end2_x = dash_x - int(math.cos(a) * 15)
                    end2_y = y - int(math.sin(a) * 15) - 5
                    pygame.draw.line(surface, (*_NS_vaelmyrra.PALETTE["blood_dark"], dash_alpha),
                                     (end1_x, end1_y), (end2_x, end2_y), 4)
                    pygame.draw.line(surface, (*_NS_vaelmyrra.PALETTE["blood_mid"], dash_alpha),
                                     (end1_x, end1_y), (end2_x, end2_y), 2)
                    pygame.draw.line(surface, (*_NS_vaelmyrra.PALETTE["blood_hot"], dash_alpha),
                                     (end1_x, end1_y), (end2_x, end2_y), 1)
    # ============================================================
    # SKILL E: PUBLIC EXECUTION (slam down)
    # ============================================================
    def _draw_execution_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning circle
            t = progress / 0.4
            r = int(60 * t)
            alpha = _NS_vaelmyrra._alpha(220 * t)
            pygame.draw.ellipse(surface, (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                (x - r, y + 50 - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface, (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                (x - r + 5, y + 50 - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6), 2)
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.3
                sx = x + int(math.cos(ang) * r)
                sy = y + 50 + int(math.sin(ang) * r * 0.4)
                pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_hot"], (sx, sy, 3, 3))
        else:
            # After slam - blood crack lines on ground
            t = (progress - 0.4) / 0.6
            r = int(35 + t * 20)
            alpha = _NS_vaelmyrra._alpha(200 * (1 - t * 0.5))
            for crack_i in range(8):
                crack_ang = crack_i * math.pi / 4
                cr_end_x = x + int(math.cos(crack_ang) * r)
                cr_end_y = y + 50 + int(math.sin(crack_ang) * r * 0.5)
                pygame.draw.line(surface,
                                 (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                 (x, y + 50), (cr_end_x, cr_end_y), 3)
                pygame.draw.line(surface,
                                 (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                 (x, y + 50), (cr_end_x, cr_end_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                 (x, y + 50), (cr_end_x, cr_end_y), 1)
    def _draw_execution_foreground(surface, boss, x, y, timer, phase):
        """Blood eruption from slam."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            return
        t = (progress - 0.4) / 0.6
        # Vertical blood geysers erupting
        for i in range(10):
            geyser_ang = i * math.pi * 2 / 10
            geyser_r = 30 + int(math.sin(t * math.pi) * 10)
            gx = x + int(math.cos(geyser_ang) * geyser_r)
            gy_ground = y + 50 + int(math.sin(geyser_ang) * geyser_r * 0.4)
            geyser_h = int((1 - t) * 40)
            alpha = _NS_vaelmyrra._alpha(220 * (1 - t))
            # Rising blood pillar
            for h in range(0, geyser_h, 2):
                px = gx + int(math.sin(phase * 3 + h * 0.2) * 2)
                py = gy_ground - h
                pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                 (px - 2, py, 4, 3))
                pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                 (px - 1, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                 (px, py, 1, 1))
            # Blood droplet at top
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha),
                                    (gx, gy_ground - geyser_h), 3)
            _NS_vaelmyrra._aacircle(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                    (gx, gy_ground - geyser_h), 2)
            pygame.draw.rect(surface, (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                             (gx, gy_ground - geyser_h, 1, 1))
    # ============================================================
    # SKILL R: ALL WILL KNEEL (ULTIMATE)
    # ============================================================
    def _draw_ultimate_ground(surface, boss, x, y, timer, phase):
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # MASSIVE blood rune circle
        r = int(90 * min(1.0, progress * 1.5))
        if r > 3:
            # Multiple concentric rings
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 4, 240), (10, 3, 200), (20, 2, 160), (30, 1, 120),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_darkest"],
                                     _NS_vaelmyrra._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 50 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
            # Massive rune spikes emerging radially
            for i in range(16):
                ang = i * math.pi / 8 + phase * 0.2
                spike_h = int(15 + math.sin(phase * 3 + i) * 5)
                rx = x + int(math.cos(ang) * r)
                ry = y + 50 + int(math.sin(ang) * r * 0.4)
                _NS_vaelmyrra._poly(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_darkest"], 240), [
                    (rx - 3, ry), (rx + 3, ry), (rx, ry - spike_h),
                ])
                _NS_vaelmyrra._poly(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_dark"], 240), [
                    (rx - 2, ry), (rx + 2, ry), (rx, ry - spike_h + 1),
                ])
                _NS_vaelmyrra._poly(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_mid"], 240), [
                    (rx - 1, ry), (rx + 1, ry), (rx, ry - spike_h + 2),
                ])
                pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_hot"],
                                 (rx, ry - spike_h, 1, 2))
                pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_shine"],
                                 (rx, ry - spike_h, 1, 1))
    def _draw_ultimate_foreground(surface, boss, x, y, timer, phase):
        """Massive radial red spike burst — All Will Kneel."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Wind-up: gathering energy above
            t = progress / 0.2
            gather_y = y - int(t * 40)
            for r in range(15, 0, -1):
                alpha = _NS_vaelmyrra._alpha(200 * (15 - r) / 15)
                _NS_vaelmyrra._aacircle(surface,
                                        (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha),
                                        (x, gather_y), r)
            _NS_vaelmyrra._aacircle(surface,
                                    _NS_vaelmyrra.PALETTE["blood_hot"],
                                    (x, gather_y), 5)
            pygame.draw.rect(surface, _NS_vaelmyrra.PALETTE["blood_shine"], (x, gather_y, 2, 2))
        elif progress < 0.5:
            # SLAM PHASE: massive radial burst
            t = (progress - 0.2) / 0.3
            intensity = math.sin(t * math.pi)
            # HUGE radial spikes (like ambessa ult art)
            burst_r = int(20 + t * 90)
            for i in range(24):
                ang = i * math.pi / 12 + phase * 0.1
                spike_far = burst_r + int(math.sin(i * 2) * 15)
                spike_near = int(burst_r * 0.2)
                # Spike shape (long triangle)
                perp = ang + math.pi / 2
                perp_x = math.cos(perp) * 4
                perp_y = math.sin(perp) * 4
                spike_tip_x = x + int(math.cos(ang) * spike_far)
                spike_tip_y = y + int(math.sin(ang) * spike_far)
                spike_base1_x = x + int(math.cos(ang) * spike_near + perp_x)
                spike_base1_y = y + int(math.sin(ang) * spike_near + perp_y)
                spike_base2_x = x + int(math.cos(ang) * spike_near - perp_x)
                spike_base2_y = y + int(math.sin(ang) * spike_near - perp_y)
                alpha = _NS_vaelmyrra._alpha(255 * intensity)
                _NS_vaelmyrra._poly(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_darkest"], alpha), [
                    (spike_base1_x, spike_base1_y),
                    (spike_tip_x, spike_tip_y),
                    (spike_base2_x, spike_base2_y),
                ])
                # Inner brighter layer
                mid_perp_x = perp_x * 0.6
                mid_perp_y = perp_y * 0.6
                _NS_vaelmyrra._poly(surface,
                                    (*_NS_vaelmyrra.PALETTE["blood_dark"], alpha), [
                    (x + int(math.cos(ang) * spike_near + mid_perp_x),
                     y + int(math.sin(ang) * spike_near + mid_perp_y)),
                    (spike_tip_x, spike_tip_y),
                    (x + int(math.cos(ang) * spike_near - mid_perp_x),
                     y + int(math.sin(ang) * spike_near - mid_perp_y)),
                ])
                # Bright core line
                pygame.draw.line(surface,
                                 (*_NS_vaelmyrra.PALETTE["blood_mid"], alpha),
                                 (x + int(math.cos(ang) * spike_near),
                                  y + int(math.sin(ang) * spike_near)),
                                 (spike_tip_x, spike_tip_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_vaelmyrra.PALETTE["blood_hot"], alpha),
                                 (x + int(math.cos(ang) * spike_near),
                                  y + int(math.sin(ang) * spike_near)),
                                 (spike_tip_x, spike_tip_y), 1)
                # Tip sparkle
                pygame.draw.rect(surface,
                                 (*_NS_vaelmyrra.PALETTE["blood_shine"], alpha),
                                 (spike_tip_x, spike_tip_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_vaelmyrra.PALETTE["white"], alpha),
                                 (spike_tip_x, spike_tip_y, 1, 1))
            # Central explosion glow
            core_alpha = _NS_vaelmyrra._alpha(240 * intensity)
            for r in range(30, 0, -3):
                _NS_vaelmyrra._aacircle(surface,
                                        (*_NS_vaelmyrra.PALETTE["blood_hot"],
                                         _NS_vaelmyrra._alpha(core_alpha * (30 - r) / 30)),
                                        (x, y), r)
        else:
            # Aftermath: lingering embers rising
            t = (progress - 0.5) / 0.5
            for i in range(20):
                rise_t = (phase * 0.6 + i * 0.08) % 1.0
                rx = x - 40 + int(math.sin(phase + i) * 40)
                ry = y + 30 - int(rise_t * 70)
                alpha = _NS_vaelmyrra._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_vaelmyrra._aacircle(surface,
                                            (*_NS_vaelmyrra.PALETTE["ember_dark"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_vaelmyrra.PALETTE["ember_hot"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_vaelmyrra.PALETTE["ember_light"], alpha),
                                     (rx, ry - 1, 1, 1))
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_vaelmyrra).keys()):
    _attr = vars(_NS_vaelmyrra)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_vaelmyrra, _attr_name, staticmethod(_attr))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_aelyrion(surface, boss, x, y):
    """Entry point aelyrion."""
    return _NS_aelyrion.draw_aelyrion(surface, boss, x, y)


def draw_kaervosth(surface, boss, x, y):
    """Entry point kaervosth."""
    return _NS_kaervosth.draw_kaervosth(surface, boss, x, y)


def draw_morvyssk(surface, boss, x, y):
    """Entry point morvyssk."""
    return _NS_morvyssk.draw_morvyssk(surface, boss, x, y)


def draw_vaelmyrra(surface, boss, x, y):
    """Entry point vaelmyrra."""
    return _NS_vaelmyrra.draw_vaelmyrra(surface, boss, x, y)
