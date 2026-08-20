"""
bosses/level27.py - Semua boss Level 27

Berisi:
  - kyumirra   (mini boss - RANGED nine-tailed fox enchantress)
  - morvakhul  (mini boss - MELEE undying executioner, cursed axe)
  - nyxariel   (mini boss - MELEE abyssal trickster, trident)
  - zarethyr   (TRUE BOSS - RANGED astral sovereign, cosmic mage)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kyu_ (kyumirra), _zar_ (zarethyr) sudah unik.
  - _mor_ (morvakhul) di-rename -> _mok_ (bentrok dengan Morgath level 1),
    termasuk atribut _last_x/_last_y.
  - _nyx_ (nyxariel) di-rename -> _nyl_ (bentrok dengan nyxarath level 7
    & nyxareva level 11), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KYUMIRRA (FOX ENCHANTRESS) - Mini Boss
# ====================================================================

class _NS_kyumirra:
    """Namespace kyumirra - HD nine-tailed fox enchantress boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale porcelain)
        "skin_darkest": (140, 100, 90),
        "skin_dark": (200, 160, 145),
        "skin_mid": (235, 200, 185),
        "skin_light": (250, 225, 210),
        "skin_shine": (255, 245, 235),
        # Dark hair (black-navy)
        "hair_darkest": (10, 8, 20),
        "hair_dark": (30, 25, 45),
        "hair_mid": (60, 55, 85),
        "hair_light": (110, 100, 140),
        "hair_shine": (180, 170, 210),
        # Kimono red (deep crimson)
        "kimono_darkest": (35, 8, 15),
        "kimono_dark": (85, 20, 30),
        "kimono_mid": (155, 35, 50),
        "kimono_light": (215, 60, 80),
        "kimono_shine": (255, 130, 145),
        # Gold trim (kimono accents)
        "gold_darkest": (45, 30, 5),
        "gold_dark": (115, 85, 25),
        "gold_mid": (200, 160, 55),
        "gold_light": (245, 215, 115),
        "gold_shine": (255, 240, 180),
        # White nine tails
        "tail_darkest": (85, 90, 110),
        "tail_dark": (145, 150, 175),
        "tail_mid": (195, 200, 220),
        "tail_light": (230, 235, 245),
        "tail_shine": (255, 255, 255),
        # Fox ear tips (dark)
        "ear_dark": (25, 15, 30),
        "ear_light": (200, 170, 190),  # inner pink
        # Blue magic orb (main projectile)
        "magic_darkest": (5, 20, 55),
        "magic_dark": (20, 65, 145),
        "magic_mid": (55, 135, 230),
        "magic_light": (130, 200, 255),
        "magic_hot": (200, 235, 255),
        "magic_shine": (240, 250, 255),
        # Pink charm (Q & E)
        "charm_darkest": (55, 5, 40),
        "charm_dark": (140, 20, 100),
        "charm_mid": (230, 60, 170),
        "charm_light": (255, 130, 210),
        "charm_hot": (255, 200, 240),
        "charm_shine": (255, 240, 250),
        # Eye (gold amber)
        "eye_dark": (40, 15, 5),
        "eye_mid": (180, 100, 20),
        "eye_light": (255, 180, 60),
        "eye_glow": (255, 240, 180),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 8),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kyumirra._clamp(color)
        if _NS_kyumirra.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kyumirra._clamp(color)
        if _NS_kyumirra.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_kyumirra._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_kyumirra._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_kyumirra._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kyumirra(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kyumirra._detect_moving(boss)
        _NS_kyumirra._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kyu_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_kyumirra._draw_spirit_aura(surface, x, y, pulse)
        _NS_kyumirra._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX
        if active_skill == "r":
            _NS_kyumirra._draw_spirit_rush_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_kyumirra._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_kyumirra._draw_float_move(surface, boss, x, y)
        else:
            _NS_kyumirra._draw_float_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_kyumirra._draw_orb_of_deception(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kyumirra._draw_fox_fire(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kyumirra._draw_charm(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kyumirra._draw_spirit_rush_fg(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kyu_previous_timer", 0))
        active = bool(getattr(boss, "_kyu_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kyu_attack_active = True
            boss._kyu_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kyu_attack_frame = int(getattr(boss, "_kyu_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kyu_attack_active = False
            boss._kyu_attack_frame = 0
            active = False
        boss._kyu_previous_timer = timer
        boss._kyu_attack_progress = (
            min(1.0, getattr(boss, "_kyu_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kyu_last_x"):
            boss._kyu_last_x = boss.x
            boss._kyu_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kyu_last_x)
        dy = abs(boss.y - boss._kyu_last_y)
        boss._kyu_last_x = boss.x
        boss._kyu_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_kyumirra._draw_hover_shadow(surface, x, y + 55, boss.pulse)
        _NS_kyumirra._draw_spirit_mist(surface, x, y + 45, boss.pulse)
        _NS_kyumirra._draw_body(surface, x + sway, y + bob,
                                boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_kyumirra._draw_hover_shadow(surface, x + sway, y + 55, phase)
        _NS_kyumirra._draw_spirit_mist(surface, x + sway, y + 45, phase,
                                       trail=True, facing=boss.direction)
        _NS_kyumirra._draw_body(surface, x + sway, y + bob,
                                boss.direction, phase, "move")
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_kyu_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # For ranged mage: subtle cast forward motion
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
            lift = int(3 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(7 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_kyumirra._draw_hover_shadow(surface, x + lunge, y + 55, boss.pulse)
        _NS_kyumirra._draw_spirit_mist(surface, x + lunge, y + 45, boss.pulse,
                                       intense=True)
        _NS_kyumirra._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_kyumirra._draw_basic_orb_projectile(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # NINE TAILS BEHIND (draw first, behind body)
        _NS_kyumirra._draw_nine_tails(surface, cx, cy, facing, phase, action)
        # Legs (kimono skirt + slim legs)
        _NS_kyumirra._draw_legs(surface, cx, cy + 20, facing, phase)
        # Kimono skirt (red with gold trim)
        _NS_kyumirra._draw_skirt(surface, cx, cy + 12, facing, phase)
        # Torso (kimono top, off-shoulder)
        _NS_kyumirra._draw_torso(surface, cx, cy, facing, phase)
        # Arms
        _NS_kyumirra._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head (face, dark hair, fox ears)
        _NS_kyumirra._draw_head(surface, cx, cy - 22, facing, phase)
        # Magic orb held in hand
        _NS_kyumirra._draw_hand_orb(surface, cx, cy, facing, phase, action, attack_progress)
    # ---------- NINE TAILS (iconic feature) ----------
    def _draw_nine_tails(surface, cx, cy, facing, phase, action):
        """9 flowing white tails behind the body."""
        # Tails fan out behind based on facing
        back_dir = -facing
        base_x = cx + back_dir * 2
        base_y = cy + 4
        # Different angles for each tail (spread fan)
        tail_configs = [
            # (angle_offset_from_back, length, wave_speed, wave_amp)
            (-0.8, 26, 1.2, 3),
            (-0.55, 30, 1.0, 3),
            (-0.3, 33, 1.4, 4),
            (-0.1, 35, 1.1, 3),
            (0.0, 36, 1.3, 4),   # center/top
            (0.15, 34, 1.5, 4),
            (0.35, 32, 1.0, 3),
            (0.6, 28, 1.2, 3),
            (0.85, 25, 1.4, 3),
        ]
        # Draw tails (back to front for layering)
        for i, (ang_off, length, wave_speed, wave_amp) in enumerate(tail_configs):
            # Base angle points back
            base_angle = math.pi + ang_off * back_dir
            wave = math.sin(phase * wave_speed + i * 0.4) * wave_amp
            # Curve the tail
            mid_ratio = 0.5
            mid_x = base_x + int(math.cos(base_angle) * length * mid_ratio)
            mid_y = base_y + int(math.sin(base_angle) * length * mid_ratio) - int(wave * 0.5)
            tip_x = base_x + int(math.cos(base_angle) * length)
            tip_y = base_y + int(math.sin(base_angle) * length) - int(wave)
            _NS_kyumirra._draw_single_tail(surface, base_x, base_y, mid_x, mid_y,
                                           tip_x, tip_y, i)
    def _draw_single_tail(surface, bx, by, mx, my, tx, ty, tail_i):
        """Draw one fluffy fox tail from base to tip."""
        # Segments along the tail
        segments = 8
        prev_top = None
        prev_bot = None
        for seg in range(segments + 1):
            t = seg / segments
            # Bezier curve
            px = int((1 - t) ** 2 * bx + 2 * (1 - t) * t * mx + t ** 2 * tx)
            py = int((1 - t) ** 2 * by + 2 * (1 - t) * t * my + t ** 2 * ty)
            # Thickness (fluffy: thicker in middle, tapers at ends)
            if t < 0.3:
                thick = int(3 + t * 10)
            elif t < 0.7:
                thick = int(6 + math.sin((t - 0.3) * math.pi / 0.4) * 2)
            else:
                thick = int(8 - (t - 0.7) * 22)
                thick = max(2, thick)
            # Perpendicular direction
            # Compute tangent from adjacent point
            if seg < segments:
                next_t = (seg + 1) / segments
                next_x = int((1 - next_t) ** 2 * bx + 2 * (1 - next_t) * next_t * mx + next_t ** 2 * tx)
                next_y = int((1 - next_t) ** 2 * by + 2 * (1 - next_t) * next_t * my + next_t ** 2 * ty)
                tan_ang = math.atan2(next_y - py, next_x - px)
            elif seg > 0:
                prev_t = (seg - 1) / segments
                prev_x = int((1 - prev_t) ** 2 * bx + 2 * (1 - prev_t) * prev_t * mx + prev_t ** 2 * tx)
                prev_y = int((1 - prev_t) ** 2 * by + 2 * (1 - prev_t) * prev_t * my + prev_t ** 2 * ty)
                tan_ang = math.atan2(py - prev_y, px - prev_x)
            else:
                tan_ang = 0
            perp = tan_ang + math.pi / 2
            top_x = px + int(math.cos(perp) * thick)
            top_y = py + int(math.sin(perp) * thick)
            bot_x = px - int(math.cos(perp) * thick)
            bot_y = py - int(math.sin(perp) * thick)
            if prev_top is not None:
                # Draw segment (shadow, dark, mid, light layers)
                seg_poly = [prev_top, (top_x, top_y), (bot_x, bot_y), prev_bot]
                _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                                   [(p[0] + 1, p[1] + 2) for p in seg_poly])
                _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["tail_darkest"], seg_poly)
                # Inner layers
                inner_top = (int(prev_top[0] * 0.8 + px * 0.2),
                             int(prev_top[1] * 0.8 + py * 0.2))
                inner_top2 = (int(top_x * 0.8 + px * 0.2),
                              int(top_y * 0.8 + py * 0.2))
                inner_bot = (int(prev_bot[0] * 0.8 + px * 0.2),
                             int(prev_bot[1] * 0.8 + py * 0.2))
                inner_bot2 = (int(bot_x * 0.8 + px * 0.2),
                              int(bot_y * 0.8 + py * 0.2))
                _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["tail_dark"],
                                   [inner_top, inner_top2, inner_bot2, inner_bot])
                _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["tail_mid"], [
                    (int(inner_top[0] * 0.7 + px * 0.3),
                     int(inner_top[1] * 0.7 + py * 0.3)),
                    (int(inner_top2[0] * 0.7 + px * 0.3),
                     int(inner_top2[1] * 0.7 + py * 0.3)),
                    (int(inner_bot2[0] * 0.7 + px * 0.3),
                     int(inner_bot2[1] * 0.7 + py * 0.3)),
                    (int(inner_bot[0] * 0.7 + px * 0.3),
                     int(inner_bot[1] * 0.7 + py * 0.3)),
                ])
                # Center highlight line
                pygame.draw.line(surface, _NS_kyumirra.PALETTE["tail_light"],
                                 prev_top, (top_x, top_y), 1)
            prev_top = (top_x, top_y)
            prev_bot = (bot_x, bot_y)
        # WHITE TIP at end (bright)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["tail_dark"], (tx, ty), 4)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["tail_mid"], (tx, ty), 3)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["tail_light"], (tx - 1, ty - 1), 2)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["tail_shine"], (tx - 1, ty - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["white"], (tx, ty, 1, 1))
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase):
        # Slim legs under skirt
        for side in (-1, 1):
            lx = cx + side * 3
            ly = cy
            # Thigh (skin visible)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                                 (lx + 1, ly + 1), (lx + 1, ly + 12 + 1), 4)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["skin_darkest"],
                                 (lx, ly), (lx, ly + 12), 3)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["skin_dark"],
                                 (lx, ly), (lx, ly + 12), 2)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["skin_mid"],
                                 (lx, ly), (lx, ly + 12), 1)
            # Boot / shoe at bottom
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["shadow_deep"], [
                (lx - 2 + 1, ly + 13 + 1), (lx + 2 + 1, ly + 13 + 1),
                (lx + 3 + 1, ly + 16 + 1), (lx - 2 + 1, ly + 16 + 1),
            ])
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_darkest"], [
                (lx - 2, ly + 13), (lx + 2, ly + 13),
                (lx + 3, ly + 16), (lx - 2, ly + 16),
            ])
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_dark"], [
                (lx - 1, ly + 13), (lx + 1, ly + 13),
                (lx + 2, ly + 15), (lx - 1, ly + 15),
            ])
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_mid"],
                             (lx - 1, ly + 13, 3, 1))
    # ---------- SKIRT ----------
    def _draw_skirt(surface, cx, cy, facing, phase):
        # Red kimono skirt (short, flowing)
        sway = math.sin(phase * 0.6) * 2
        skirt_pts = [
            (cx - 9, cy - 3),
            (cx - 11, cy + 8 + int(sway)),
            (cx - 8, cy + 11 + int(sway * 0.5)),
            (cx + 8, cy + 11 + int(sway * 0.5)),
            (cx + 11, cy + 8 + int(sway)),
            (cx + 9, cy - 3),
        ]
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in skirt_pts])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_darkest"], skirt_pts)
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_dark"], [
            (cx - 8, cy - 2),
            (cx - 10, cy + 7 + int(sway)),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 10, cy + 7 + int(sway)),
            (cx + 8, cy - 2),
        ])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_mid"], [
            (cx - 6, cy - 1),
            (cx - 8, cy + 5),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 8, cy + 5),
            (cx + 6, cy - 1),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["kimono_light"],
                         (cx - 4, cy + 1), (cx - 5, cy + 6), 1)
        # Gold trim along bottom edge
        for i in range(6):
            t = i / 5
            px = int(cx - 10 + 20 * t)
            py = int(cy + 8 + int(sway * (1 - abs(t - 0.5) * 2)))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_dark"], (px - 1, py, 3, 2))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_mid"], (px, py, 1, 2))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_shine"], (px, py, 1, 1))
        # BELL (lonceng gantung di pinggang)
        bell_x = cx + facing * 6
        bell_y = cy + 2
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                               (bell_x + 1, bell_y + 1), 3)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["gold_darkest"], (bell_x, bell_y), 3)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["gold_dark"], (bell_x, bell_y), 2)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["gold_mid"], (bell_x, bell_y), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_shine"], (bell_x, bell_y - 1, 1, 1))
        # Bell slit
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                         (bell_x - 1, bell_y + 1), (bell_x + 1, bell_y + 1), 1)
        # Red tassel below bell
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["kimono_dark"],
                         (bell_x, bell_y + 3), (bell_x, bell_y + 6), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["kimono_mid"], (bell_x, bell_y + 6, 1, 1))
    # ---------- TORSO (kimono top, off-shoulder) ----------
    def _draw_torso(surface, cx, cy, facing, phase):
        # Slim feminine torso
        pts = [
            (cx - 8, cy - 8),
            (cx - 10, cy - 4),
            (cx - 9, cy + 3),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 9, cy + 3),
            (cx + 10, cy - 4),
            (cx + 8, cy - 8),
        ]
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in pts])
        # OFF-SHOULDER: top part shows skin
        shoulder_pts = [
            (cx - 8, cy - 8), (cx + 8, cy - 8),
            (cx + 10, cy - 4), (cx + 8, cy - 3),
            (cx - 8, cy - 3), (cx - 10, cy - 4),
        ]
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_darkest"], shoulder_pts)
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_dark"], [
            (cx - 7, cy - 7), (cx + 7, cy - 7),
            (cx + 8, cy - 4), (cx + 7, cy - 4),
            (cx - 7, cy - 4), (cx - 8, cy - 4),
        ])
        # Chest highlight
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["skin_light"],
                         (cx - 3, cy - 6), (cx + 3, cy - 6), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["skin_shine"], (cx, cy - 6, 1, 1))
        # KIMONO TOP (red, below shoulder line)
        kimono_pts = [
            (cx - 10, cy - 4),
            (cx - 9, cy + 3),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 9, cy + 3),
            (cx + 10, cy - 4),
            (cx + 8, cy - 3),
            (cx - 8, cy - 3),
        ]
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_darkest"], kimono_pts)
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_dark"], [
            (cx - 9, cy - 3), (cx - 8, cy + 3),
            (cx - 6, cy + 9), (cx + 6, cy + 9),
            (cx + 8, cy + 3), (cx + 9, cy - 3),
            (cx + 7, cy - 2), (cx - 7, cy - 2),
        ])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["kimono_mid"], [
            (cx - 7, cy - 1), (cx - 6, cy + 3),
            (cx - 4, cy + 8), (cx + 4, cy + 8),
            (cx + 6, cy + 3), (cx + 7, cy - 1),
            (cx + 5, cy), (cx - 5, cy),
        ])
        # V-neck opening (chest V-shape showing more skin)
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_dark"], [
            (cx - 2, cy - 3), (cx + 2, cy - 3), (cx, cy + 1),
        ])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_mid"], [
            (cx - 1, cy - 3), (cx + 1, cy - 3), (cx, cy),
        ])
        # Gold sash/obi at waist
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_darkest"], (cx - 9, cy + 6, 18, 4))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_dark"], (cx - 8, cy + 6, 16, 3))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_mid"], (cx - 7, cy + 6, 14, 2))
        # Highlight streak on obi
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["gold_light"],
                         (cx - 6, cy + 7), (cx + 6, cy + 7), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_shine"], (cx - 3, cy + 6, 6, 1))
        # Center clasp/knot on obi
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["kimono_darkest"], (cx - 2, cy + 6, 4, 4))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["kimono_dark"], (cx - 1, cy + 7, 2, 2))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["kimono_mid"], (cx - 1, cy + 7, 1, 1))
    # ---------- ARMS ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        # Right hand (dominant/facing) holds magic orb
        # Left hand rests or gestures
        for side in (-1, 1):
            base_x = cx + side * 9
            base_y = cy - 3
            is_dominant = (side * facing > 0)
            if action == "attack" and is_dominant:
                # Cast forward motion
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    # Pull back, raise hand
                    elbow_offset_x = int(-3 * facing)
                    elbow_offset_y = int(2 - t * 4)
                    hand_offset_x = int(-2 * facing)
                    hand_offset_y = int(-2 - t * 3)
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    # Extend forward
                    elbow_offset_x = int((-3 + t * 8) * facing)
                    elbow_offset_y = int(-2)
                    hand_offset_x = int((-2 + t * 16) * facing)
                    hand_offset_y = int(-5 + t * 3)
                else:
                    t = (attack_progress - 0.6) / 0.4
                    # Retract
                    elbow_offset_x = int((5 - t * 2) * facing)
                    elbow_offset_y = int(-2 + t)
                    hand_offset_x = int((14 - t * 6) * facing)
                    hand_offset_y = int(-2 + t * 2)
            else:
                # Idle: hand held forward with orb
                swing = math.sin(phase * 0.6 + side) * 0.15
                if is_dominant:
                    elbow_offset_x = int(4 * facing + math.sin(swing) * 1)
                    elbow_offset_y = 0
                    hand_offset_x = int(12 * facing)
                    hand_offset_y = -2
                else:
                    # Non-dominant hand rests at side
                    elbow_offset_x = int(math.sin(swing) * 2 * side)
                    elbow_offset_y = 3
                    hand_offset_x = int(math.sin(swing * 1.5) * 3 * side + side * 2)
                    hand_offset_y = 8
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm — has red kimono sleeve
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                                 (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["kimono_darkest"],
                                 (base_x, base_y), (elbow_x, elbow_y), 4)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["kimono_dark"],
                                 (base_x, base_y), (elbow_x, elbow_y), 3)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["kimono_mid"],
                                 (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow — kimono cuff with gold trim
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["kimono_darkest"],
                                   (elbow_x, elbow_y), 3)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["kimono_dark"],
                                   (elbow_x, elbow_y), 2)
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["gold_mid"],
                             (elbow_x - 1, elbow_y - 1, 3, 1))
            # Forearm — skin exposed
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                                 (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["skin_darkest"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 3)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["skin_dark"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 2)
            _NS_kyumirra._aaline(surface, _NS_kyumirra.PALETTE["skin_mid"],
                                 (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
            # Hand (small delicate with claws)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 3)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["skin_darkest"],
                                   (hand_x, hand_y), 3)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 2)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["skin_mid"],
                                   (hand_x, hand_y), 1)
            # Tiny claw tips
            for claw_off in (-1, 0, 1):
                pygame.draw.rect(surface, _NS_kyumirra.PALETTE["ear_dark"],
                                 (hand_x + claw_off, hand_y - 2, 1, 1))
            if is_dominant:
                _NS_kyumirra._orb_hand_pos = (hand_x, hand_y)
    # ---------- HEAD ----------
    def _draw_head(surface, cx, cy, facing, phase):
        # Face — feminine oval
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
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_darkest"], face_pts)
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_dark"], [
            (cx - 5, cy - 2), (cx - 6, cy + 1),
            (cx - 5, cy + 4), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 4),
            (cx + 6, cy + 1), (cx + 5, cy - 2),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["skin_mid"], [
            (cx - 3, cy - 1), (cx - 4, cy + 1),
            (cx - 3, cy + 3), (cx - 1, cy + 6),
            (cx + 1, cy + 6), (cx + 3, cy + 3),
            (cx + 4, cy + 1), (cx + 3, cy - 1),
            (cx + 2, cy - 5), (cx - 2, cy - 5),
        ])
        # Highlight cheek
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["skin_light"],
                         (cx - 2 * facing, cy, 1, 1))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["skin_shine"],
                         (cx - 2 * facing, cy - 1, 1, 1))
        # EYES (gold amber, cunning look)
        eye_pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            # Eye slit (feline shape)
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["shadow_deep"], (ex - 1, ey - 1, 3, 2))
            # Iris
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_kyumirra._alpha(100 * (3 - r) / 3 * eye_pulse)
                _NS_kyumirra._aacircle(surface,
                                       (*_NS_kyumirra.PALETTE["eye_light"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["eye_glow"], (ex, ey, 1, 1))
            # Vertical slit pupil (cat-like)
            pygame.draw.line(surface, _NS_kyumirra.PALETTE["shadow_deep"],
                             (ex, ey - 1), (ex, ey + 1), 1)
        # LIPS (pink lipstick)
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["charm_dark"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_mid"], (cx, cy + 5, 1, 1))
        # DARK HAIR flowing
        _NS_kyumirra._draw_hair(surface, cx, cy, facing, phase)
        # FOX EARS on top
        _NS_kyumirra._draw_fox_ears(surface, cx, cy - 7, facing, phase)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Dark long hair flowing behind."""
        sway = math.sin(phase * 0.4) * 2
        # Long hair behind (past shoulders)
        hair_pts = [
            (cx - 7, cy - 5),
            (cx - 9, cy - 2 + int(sway * 0.3)),
            (cx - 10, cy + 4 + int(sway * 0.5)),
            (cx - 11, cy + 12 + int(sway)),
            (cx - 9, cy + 20 + int(sway * 1.2)),
            (cx - 4, cy + 22 + int(sway)),
            (cx + 4, cy + 22 + int(sway)),
            (cx + 9, cy + 20 + int(sway * 1.2)),
            (cx + 11, cy + 12 + int(sway)),
            (cx + 10, cy + 4 + int(sway * 0.5)),
            (cx + 9, cy - 2 + int(sway * 0.3)),
            (cx + 7, cy - 5),
        ]
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["hair_darkest"], hair_pts)
        # Mid hair
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["hair_dark"], [
            (cx - 6, cy - 5),
            (cx - 8, cy + 4 + int(sway * 0.5)),
            (cx - 9, cy + 15 + int(sway)),
            (cx - 3, cy + 20 + int(sway)),
            (cx + 3, cy + 20 + int(sway)),
            (cx + 9, cy + 15 + int(sway)),
            (cx + 8, cy + 4 + int(sway * 0.5)),
            (cx + 6, cy - 5),
        ])
        # Top hair (front bangs)
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["hair_dark"], [
            (cx - 5, cy - 7), (cx - 6, cy - 3),
            (cx - 3, cy - 5), (cx, cy - 6),
            (cx + 3, cy - 5), (cx + 6, cy - 3),
            (cx + 5, cy - 7),
        ])
        _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["hair_mid"], [
            (cx - 4, cy - 7), (cx - 4, cy - 4),
            (cx - 1, cy - 5), (cx + 2, cy - 5),
            (cx + 4, cy - 4), (cx + 4, cy - 7),
        ])
        # Highlight strand
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["hair_light"],
                         (cx - 2, cy - 6), (cx + 2, cy - 6), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["hair_shine"],
                         (cx, cy - 6, 1, 1))
        # Side strands
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["hair_light"],
                         (cx - 7, cy + 2), (cx - 8, cy + 12 + int(sway)), 1)
        pygame.draw.line(surface, _NS_kyumirra.PALETTE["hair_light"],
                         (cx + 7, cy + 2), (cx + 8, cy + 12 + int(sway)), 1)
    def _draw_fox_ears(surface, cx, cy, facing, phase):
        """Two fox ears on top of head."""
        # Slight ear twitch
        twitch = math.sin(phase * 0.8) * 0.5
        for side in (-1, 1):
            ear_base_x = cx + side * 4
            ear_base_y = cy + 2
            ear_tip_x = ear_base_x + side * 3
            ear_tip_y = ear_base_y - 8 + int(twitch)
            # Outer black ear
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["shadow_deep"], [
                (ear_base_x - 2 + 1, ear_base_y + 1),
                (ear_base_x + 3 + 1, ear_base_y + 1),
                (ear_tip_x + 1, ear_tip_y + 1),
            ])
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["hair_darkest"], [
                (ear_base_x - 2, ear_base_y),
                (ear_base_x + 3, ear_base_y),
                (ear_tip_x, ear_tip_y),
            ])
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["hair_dark"], [
                (ear_base_x - 1, ear_base_y),
                (ear_base_x + 2, ear_base_y),
                (ear_tip_x, ear_tip_y),
            ])
            # Inner ear (pink)
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["ear_dark"], [
                (ear_base_x, ear_base_y - 1),
                (ear_base_x + 1, ear_base_y - 1),
                (ear_tip_x - side, ear_tip_y + 2),
            ])
            _NS_kyumirra._poly(surface, _NS_kyumirra.PALETTE["ear_light"], [
                (ear_base_x + side, ear_base_y - 1),
                (ear_tip_x - side * 2, ear_tip_y + 3),
            ])
            # Ear tip highlight
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["hair_light"],
                             (ear_tip_x, ear_tip_y, 1, 1))
    # ---------- MAGIC ORB in hand ----------
    def _draw_hand_orb(surface, cx, cy, facing, phase, action, attack_progress):
        hand_pos = getattr(_NS_kyumirra, "_orb_hand_pos", None)
        if hand_pos is None:
            hand_pos = (cx + facing * 15, cy - 2)
        hx, hy = hand_pos
        orb_x = hx + facing * 4
        orb_y = hy
        # Don't show orb during middle of cast (it's the projectile)
        if action == "attack" and 0.3 < attack_progress < 0.75:
            return
        orb_pulse = math.sin(phase * 2) * 0.3 + 0.7
        orb_r = 5
        # Halo glow
        for r in range(orb_r + 4, 0, -1):
            alpha = _NS_kyumirra._alpha(100 * (orb_r + 4 - r) / (orb_r + 4) * orb_pulse)
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["magic_light"], alpha),
                                   (orb_x, orb_y), r)
        # Core orb
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_darkest"], (orb_x, orb_y), orb_r)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_dark"], (orb_x, orb_y), orb_r - 1)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_mid"], (orb_x, orb_y), orb_r - 2)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_light"], (orb_x - 1, orb_y - 1), 2)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_hot"], (orb_x - 1, orb_y - 1), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["magic_shine"],
                         (orb_x - 1, orb_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["white"],
                         (orb_x - 1, orb_y - 1, 1, 1))
        # Sparkles around orb
        for i in range(4):
            spark_ang = phase * 3 + i * math.pi / 2
            spark_r = orb_r + 3
            sx = orb_x + int(math.cos(spark_ang) * spark_r)
            sy = orb_y + int(math.sin(spark_ang) * spark_r)
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["magic_hot"], (sx, sy, 1, 1))
    # ============================================================
    # BASIC ATTACK: small blue orb projectile
    # ============================================================
    def _draw_basic_orb_projectile(surface, boss, x, y, progress):
        if progress < 0.3 or progress > 0.85:
            return
        facing = boss.direction
        tx, ty = _NS_kyumirra._target_position(boss, x, y)
        start_x = x + facing * 18
        start_y = y - 2
        t = (progress - 0.3) / 0.55
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(5):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_kyumirra._alpha(200 - i * 35)
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["magic_dark"], alpha),
                                   (px, py), max(1, 5 - i))
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["magic_mid"], alpha),
                                   (px, py), max(1, 3 - i))
            pygame.draw.rect(surface,
                             (*_NS_kyumirra.PALETTE["magic_light"], alpha),
                             (px, py, 1, 1))
        # Main orb
        for r in range(8, 0, -1):
            alpha = _NS_kyumirra._alpha(100 * (8 - r) / 8)
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["magic_light"], alpha),
                                   (bx, by), r)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_darkest"], (bx, by), 5)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_dark"], (bx, by), 4)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_mid"], (bx, by), 3)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_light"], (bx, by), 2)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["white"], (bx, by, 1, 1))
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
        pygame.draw.ellipse(shadow, (5, 2, 12, 170), (5, 8, 120, 12))
        pygame.draw.ellipse(shadow, (30, 15, 55, 110), (12, 10, 106, 9))
        surface.blit(shadow, (x - 65, y - 15))
    def _draw_spirit_mist(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Pink/blue spirit mist below character."""
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base mist
        mist = pygame.Surface((150, 40), pygame.SRCALPHA)
        for radius in range(32, 3, -3):
            alpha = _NS_kyumirra._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kyumirra.PALETTE["charm_darkest"], alpha),
                    (75 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2))
                )
        for radius in range(20, 3, -2):
            alpha = _NS_kyumirra._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kyumirra.PALETTE["magic_dark"], alpha),
                    (75 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 75, cy - 8))
        # Rising sparkles (alternating pink and blue)
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24)):
            t = (phase * 0.4 + i * 0.14) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 2)
            sy = cy + 4 - int(t * 22)
            alpha = _NS_kyumirra._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            color_dark = _NS_kyumirra.PALETTE["charm_dark"] if i % 2 else _NS_kyumirra.PALETTE["magic_dark"]
            color_light = _NS_kyumirra.PALETTE["charm_light"] if i % 2 else _NS_kyumirra.PALETTE["magic_light"]
            color_hot = _NS_kyumirra.PALETTE["charm_hot"] if i % 2 else _NS_kyumirra.PALETTE["magic_hot"]
            _NS_kyumirra._aacircle(surface, (*color_dark, alpha), (sx, sy), 2)
            pygame.draw.rect(surface, (*color_light, alpha), (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*color_hot, alpha), (sx, sy - 2, 1, 1))
        # Trail behind
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kyumirra._alpha(180 - i * 30)
                if alpha <= 0:
                    continue
                _NS_kyumirra._aacircle(surface,
                                       (*_NS_kyumirra.PALETTE["charm_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_kyumirra._aacircle(surface,
                                       (*_NS_kyumirra.PALETTE["magic_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_kyumirra.PALETTE["magic_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_spirit_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 190), pygame.SRCALPHA)
        # Pink outer aura
        for radius in range(95, 5, -5):
            alpha = _NS_kyumirra._alpha((95 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_kyumirra._aacircle(aura,
                                       (*_NS_kyumirra.PALETTE["charm_darkest"], alpha),
                                       (110, 95), radius)
        # Blue inner aura
        for radius in range(60, 5, -4):
            alpha = _NS_kyumirra._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kyumirra._aacircle(aura,
                                       (*_NS_kyumirra.PALETTE["magic_dark"], alpha),
                                       (110, 95), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kyumirra._alpha((35 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_kyumirra._aacircle(aura,
                                       (*_NS_kyumirra.PALETTE["magic_mid"], alpha),
                                       (110, 95), radius)
        surface.blit(aura, (x - 110, y - 95))
        # Floating spirit lights (alternating pink/blue)
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            if i % 2:
                pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_mid"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_hot"], (sx, sy, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_kyumirra.PALETTE["magic_mid"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_kyumirra.PALETTE["magic_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kyumirra.PALETTE["charm_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_kyumirra.PALETTE["magic_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_kyumirra.PALETTE["charm_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_kyumirra.PALETTE["magic_mid"],
                                   _NS_kyumirra._alpha(180 * pulse)),
                            (40, 24, 90, 14), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 27 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 27 + int(math.sin(angle) * 12)
            col = _NS_kyumirra.PALETTE["charm_light"] if i % 2 else _NS_kyumirra.PALETTE["magic_light"]
            pygame.draw.line(ring, (*col, 220), (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kyumirra.PALETTE["charm_hot"],
                                 _NS_kyumirra._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: ORB OF DECEPTION (boomerang)
    # ============================================================
    def _draw_orb_of_deception(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kyumirra._target_position(boss, x, y)
        start_x = x + facing * 18
        start_y = y - 2
        # Boomerang: t=0..0.5 = go out, t=0.5..1 = return
        if progress < 0.5:
            t = progress / 0.5
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            outgoing = True
        else:
            t = (progress - 0.5) / 0.5
            bx = int(tx + (start_x - tx) * t)
            by = int(ty + (start_y - ty) * t)
            outgoing = False
        # Big pink orb with heart shape hint
        # Trail
        for i in range(8):
            if outgoing:
                trail_t = max(0.0, (progress / 0.5) - i * 0.05)
                if trail_t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
            else:
                trail_t = max(0.0, ((progress - 0.5) / 0.5) - i * 0.05)
                if trail_t <= 0:
                    continue
                px = int(tx + (start_x - tx) * trail_t)
                py = int(ty + (start_y - ty) * trail_t)
            alpha = _NS_kyumirra._alpha(230 - i * 28)
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["charm_darkest"], alpha),
                                   (px, py), max(1, 7 - i))
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["charm_dark"], alpha),
                                   (px, py), max(1, 5 - i))
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["charm_mid"], alpha),
                                   (px, py), max(1, 3 - i))
            pygame.draw.rect(surface,
                             (*_NS_kyumirra.PALETTE["charm_hot"], alpha),
                             (px, py, 1, 1))
        # Main orb (BIG spinning heart-shaped ball)
        spin = phase * 5
        # Radial glow
        for r in range(14, 0, -2):
            alpha = _NS_kyumirra._alpha(100 * (14 - r) / 14)
            _NS_kyumirra._aacircle(surface,
                                   (*_NS_kyumirra.PALETTE["charm_light"], alpha),
                                   (bx, by), r)
        # Core sphere
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["shadow_deep"], (bx + 1, by + 1), 9)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["charm_darkest"], (bx, by), 8)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["charm_dark"], (bx, by), 7)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["charm_mid"], (bx, by), 5)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["charm_light"], (bx - 1, by - 1), 3)
        _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["charm_hot"], (bx - 1, by - 1), 2)
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_shine"], (bx - 1, by - 1, 1, 1))
        pygame.draw.rect(surface, _NS_kyumirra.PALETTE["white"], (bx - 1, by - 1, 1, 1))
        # Orbiting sparkles around
        for i in range(6):
            sp_ang = spin + i * math.pi / 3
            sp_r = 11
            sx = bx + int(math.cos(sp_ang) * sp_r)
            sy = by + int(math.sin(sp_ang) * sp_r)
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_shine"], (sx, sy, 1, 1))
        # Direction indicator arrow (return)
        if not outgoing:
            back_ang = math.atan2(start_y - by, start_x - bx)
            arr_end_x = bx + int(math.cos(back_ang) * 15)
            arr_end_y = by + int(math.sin(back_ang) * 15)
            pygame.draw.line(surface,
                             (*_NS_kyumirra.PALETTE["charm_shine"], 200),
                             (bx, by), (arr_end_x, arr_end_y), 1)
    # ============================================================
    # SKILL W: FOX-FIRE (3 homing spirits)
    # ============================================================
    def _draw_fox_fire(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kyumirra._target_position(boss, x, y)
        # 3 fox-fires orbiting then launching
        # Phase 1 (0-0.3): orbit around caster
        # Phase 2 (0.3-1.0): fly to target with slight arc
        for fire_i in range(3):
            fire_delay = fire_i * 0.08
            fire_progress = max(0.0, progress - fire_delay)
            if fire_progress < 0.3:
                # Orbiting around caster
                orbit_t = fire_progress / 0.3
                orbit_ang = phase * 4 + fire_i * (2 * math.pi / 3)
                orbit_r = 12 + int((1 - orbit_t) * 8)
                fx = x + int(math.cos(orbit_ang) * orbit_r)
                fy = y - 4 + int(math.sin(orbit_ang) * orbit_r * 0.4)
            elif fire_progress < 1.0:
                # Fly to target (each has slight offset for visual variation)
                fly_t = (fire_progress - 0.3) / 0.7
                start_x = x + int(math.cos(fire_i * 2.0) * 10)
                start_y = y - 4
                # Arc with slight curve based on fire index
                target_offset_x = int(math.sin(fire_i * 1.3) * 15)
                target_offset_y = int(math.cos(fire_i * 1.3) * 8)
                fx = int(start_x + (tx + target_offset_x - start_x) * fly_t)
                fy = int(start_y + (ty + target_offset_y - start_y) * fly_t)
                # Slight arc
                arc = -math.sin(fly_t * math.pi) * 15
                fy += int(arc)
            else:
                continue
            # Draw fox-fire (blue flame/spirit)
            # Radial glow
            for r in range(9, 0, -1):
                alpha = _NS_kyumirra._alpha(150 * (9 - r) / 9)
                _NS_kyumirra._aacircle(surface,
                                       (*_NS_kyumirra.PALETTE["magic_light"], alpha),
                                       (fx, fy), r)
            # Core
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_darkest"], (fx, fy), 5)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_dark"], (fx, fy), 4)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_mid"], (fx, fy), 3)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_light"], (fx - 1, fy - 1), 2)
            _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["magic_hot"], (fx - 1, fy - 1), 1)
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["magic_shine"], (fx - 1, fy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["white"], (fx - 1, fy - 1, 1, 1))
            # Flame tail (wispy)
            for tail_i in range(4):
                tail_offset_x = -int(math.cos(phase * 3 + fire_i) * (tail_i + 1) * 2)
                tail_offset_y = int(math.sin(phase * 3 + fire_i) * (tail_i + 1))
                tail_alpha = _NS_kyumirra._alpha(180 - tail_i * 40)
                tx_t = fx + tail_offset_x
                ty_t = fy + tail_offset_y + tail_i
                _NS_kyumirra._aacircle(surface,
                                       (*_NS_kyumirra.PALETTE["magic_mid"], tail_alpha),
                                       (tx_t, ty_t), max(1, 3 - tail_i))
                pygame.draw.rect(surface,
                                 (*_NS_kyumirra.PALETTE["magic_light"], tail_alpha),
                                 (tx_t, ty_t, 1, 1))
    # ============================================================
    # SKILL E: CHARM (kiss with heart)
    # ============================================================
    def _draw_charm(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kyumirra._target_position(boss, x, y)
        start_x = x + facing * 8
        start_y = y - 20  # Kiss comes from face/mouth
        if progress < 0.15:
            # Wind-up: hearts gathering around mouth
            t = progress / 0.15
            for i in range(3):
                ang = phase * 3 + i * 2 * math.pi / 3
                r = int((1 - t) * 6 + 3)
                hx = start_x + int(math.cos(ang) * r)
                hy = start_y + int(math.sin(ang) * r)
                _NS_kyumirra._aacircle(surface, _NS_kyumirra.PALETTE["charm_mid"], (hx, hy), 2)
                pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_hot"], (hx, hy, 1, 1))
        else:
            # Heart projectile flying
            t = (progress - 0.15) / 0.85
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Wobble path for kiss motion
            wobble = math.sin(t * 8) * 3
            # Trail of small hearts
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                perp_ang = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
                wob = math.sin(trail_t * 8) * 3
                px += int(math.cos(perp_ang) * wob)
                py += int(math.sin(perp_ang) * wob)
                alpha = _NS_kyumirra._alpha(220 - i * 30)
                # Small heart shape
                _NS_kyumirra._draw_heart(surface, px, py, max(2, 5 - i),
                                         (*_NS_kyumirra.PALETTE["charm_mid"], alpha))
                _NS_kyumirra._draw_heart(surface, px, py, max(1, 3 - i),
                                         (*_NS_kyumirra.PALETTE["charm_hot"], alpha))
            # MAIN HEART (big glowing)
            # Radial glow
            for r in range(12, 0, -2):
                alpha = _NS_kyumirra._alpha(100 * (12 - r) / 12)
                _NS_kyumirra._aacircle(surface,
                                       (*_NS_kyumirra.PALETTE["charm_light"], alpha),
                                       (bx, by), r)
            _NS_kyumirra._draw_heart(surface, bx, by, 7,
                                     _NS_kyumirra.PALETTE["shadow_deep"])
            _NS_kyumirra._draw_heart(surface, bx, by, 6,
                                     _NS_kyumirra.PALETTE["charm_darkest"])
            _NS_kyumirra._draw_heart(surface, bx, by, 5,
                                     _NS_kyumirra.PALETTE["charm_dark"])
            _NS_kyumirra._draw_heart(surface, bx, by, 4,
                                     _NS_kyumirra.PALETTE["charm_mid"])
            _NS_kyumirra._draw_heart(surface, bx, by, 3,
                                     _NS_kyumirra.PALETTE["charm_light"])
            _NS_kyumirra._draw_heart(surface, bx, by, 2,
                                     _NS_kyumirra.PALETTE["charm_hot"])
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["charm_shine"], (bx, by, 1, 1))
            pygame.draw.rect(surface, _NS_kyumirra.PALETTE["white"], (bx, by, 1, 1))
    def _draw_heart(surface, cx, cy, size, color):
        """Draw a simple heart shape at cx, cy with given size."""
        if size <= 0:
            return
        # Two circles + triangle for heart
        _NS_kyumirra._aacircle(surface, color, (cx - size // 2, cy - size // 3), max(1, size // 2))
        _NS_kyumirra._aacircle(surface, color, (cx + size // 2, cy - size // 3), max(1, size // 2))
        # Bottom triangle
        _NS_kyumirra._poly(surface, color, [
            (cx - size, cy),
            (cx + size, cy),
            (cx, cy + size),
        ])
    # ============================================================
    # SKILL R: SPIRIT RUSH (triple dash)
    # ============================================================
    def _draw_spirit_rush_ground(surface, boss, x, y, timer, phase):
        pass  # handled in foreground
    def _draw_spirit_rush_fg(surface, boss, x, y, timer, phase):
        """Triple dash with fox tail arc trails."""
        facing = boss.direction
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # 3 dash arcs
        for dash_i in range(3):
            dash_start = dash_i * 0.3
            dash_end = dash_start + 0.25
            if progress < dash_start:
                continue
            dash_local = min(1.0, max(0.0, (progress - dash_start) / (dash_end - dash_start)))
            # Dash direction
            dash_dir = 1 if dash_i % 2 == 0 else -1
            dash_offset_x = dash_dir * facing * (dash_i + 1) * 30
            # Fading trail from previous dashes
            fade = 1 - min(1.0, max(0.0, (progress - dash_end)) / 0.3)
            # Arc curve trail (fox tail shape)
            arc_start_x = x + dash_offset_x - dash_dir * facing * 60
            arc_start_y = y
            arc_end_x = x + dash_offset_x
            arc_end_y = y
            # Draw arc (curved slash trail)
            segments = 20
            for s in range(segments):
                t1 = s / segments
                t2 = (s + 1) / segments
                # Curved path (parabolic arc going up-down)
                seg_x1 = int(arc_start_x + (arc_end_x - arc_start_x) * t1)
                seg_y1 = int(arc_start_y - math.sin(t1 * math.pi) * 20)
                seg_x2 = int(arc_start_x + (arc_end_x - arc_start_x) * t2)
                seg_y2 = int(arc_start_y - math.sin(t2 * math.pi) * 20)
                # Reveal based on dash progress
                if t2 > dash_local:
                    continue
                # Thickness based on position (thicker in middle like fox tail)
                thick = int(math.sin(t1 * math.pi) * 5 + 2)
                alpha = _NS_kyumirra._alpha(240 * fade * (1 - abs(t1 - 0.5)))
                _NS_kyumirra._aaline(surface,
                                     (*_NS_kyumirra.PALETTE["magic_darkest"], alpha),
                                     (seg_x1, seg_y1), (seg_x2, seg_y2), thick + 2)
                _NS_kyumirra._aaline(surface,
                                     (*_NS_kyumirra.PALETTE["magic_dark"], alpha),
                                     (seg_x1, seg_y1), (seg_x2, seg_y2), thick)
                _NS_kyumirra._aaline(surface,
                                     (*_NS_kyumirra.PALETTE["magic_mid"], alpha),
                                     (seg_x1, seg_y1), (seg_x2, seg_y2), max(1, thick - 2))
                _NS_kyumirra._aaline(surface,
                                     (*_NS_kyumirra.PALETTE["magic_light"], alpha),
                                     (seg_x1, seg_y1), (seg_x2, seg_y2), 1)
            # Sparkles along dash trail
            for s in range(5):
                sp_t = s / 5
                if sp_t > dash_local:
                    continue
                spx = int(arc_start_x + (arc_end_x - arc_start_x) * sp_t)
                spy = int(arc_start_y - math.sin(sp_t * math.pi) * 20)
                sp_alpha = _NS_kyumirra._alpha(240 * fade)
                pygame.draw.rect(surface, (*_NS_kyumirra.PALETTE["magic_hot"], sp_alpha),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_kyumirra.PALETTE["magic_shine"], sp_alpha),
                                 (spx, spy, 1, 1))
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_kyumirra).keys()):
    _attr = vars(_NS_kyumirra)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_kyumirra, _attr_name, staticmethod(_attr))



# ====================================================================
# MORVAKHUL (UNDYING EXECUTIONER) - Mini Boss
# ====================================================================

class _NS_morvakhul:
    """Namespace morvakhul - HD undying executioner boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark plate armor (black steel)
        "armor_darkest": (5, 8, 12),
        "armor_dark": (20, 25, 32),
        "armor_mid": (50, 58, 68),
        "armor_light": (95, 105, 118),
        "armor_shine": (160, 170, 185),
        # Cursed green energy (glow, aura, axe crack)
        "curse_darkest": (5, 25, 15),
        "curse_dark": (15, 70, 35),
        "curse_mid": (40, 160, 70),
        "curse_light": (110, 230, 130),
        "curse_hot": (180, 255, 180),
        "curse_shine": (230, 255, 230),
        # Pale undead skin (grey-white)
        "skin_darkest": (55, 55, 65),
        "skin_dark": (100, 100, 115),
        "skin_mid": (155, 155, 170),
        "skin_light": (205, 205, 215),
        "skin_shine": (240, 240, 245),
        # Black hair
        "hair_darkest": (5, 5, 12),
        "hair_dark": (18, 18, 30),
        "hair_mid": (40, 40, 55),
        "hair_light": (75, 75, 90),
        # Bone (skeleton spine, accents)
        "bone_dark": (55, 50, 40),
        "bone_mid": (130, 120, 100),
        "bone_light": (200, 190, 170),
        "bone_shine": (240, 235, 220),
        # Leather straps (dark brown)
        "leather_dark": (25, 18, 12),
        "leather_mid": (55, 40, 28),
        # Cape/tattered cloth
        "cloth_darkest": (10, 12, 18),
        "cloth_dark": (25, 28, 38),
        "cloth_mid": (45, 50, 65),
        # Green fire ember
        "ember_dark": (10, 55, 20),
        "ember_mid": (60, 180, 80),
        "ember_hot": (180, 255, 180),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 5),
        # Eye glow (bright green)
        "eye_dark": (5, 40, 15),
        "eye_mid": (60, 200, 90),
        "eye_glow": (180, 255, 190),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morvakhul._clamp(color)
        if _NS_morvakhul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvakhul._clamp(color)
        if _NS_morvakhul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_morvakhul._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_morvakhul._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_morvakhul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morvakhul(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morvakhul._detect_moving(boss)
        _NS_morvakhul._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_mok_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        buff_active = active_skill in ("w", "r")
        # Ambient (bigger green aura when W or R active)
        _NS_morvakhul._draw_death_aura(surface, x, y, pulse, buff_active,
                                       is_ultimate=(active_skill == "r"))
        _NS_morvakhul._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "q":
            _NS_morvakhul._draw_penalty_zone(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvakhul._draw_blood_lust_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvakhul._draw_execution_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvakhul._draw_retribution_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_morvakhul._draw_attack_pose(surface, boss, x, y, buff_active,
                                            active_skill == "r")
        elif moving:
            _NS_morvakhul._draw_float_move(surface, boss, x, y, buff_active,
                                           active_skill == "r")
        else:
            _NS_morvakhul._draw_float_idle(surface, boss, x, y, buff_active,
                                           active_skill == "r")
        # Foreground skill FX
        if active_skill == "q":
            _NS_morvakhul._draw_penalty_swing_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvakhul._draw_blood_lust_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvakhul._draw_execution_strike_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvakhul._draw_retribution_fg(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 52)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mok_previous_timer", 0))
        active = bool(getattr(boss, "_mok_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._mok_attack_active = True
            boss._mok_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mok_attack_frame = int(getattr(boss, "_mok_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mok_attack_active = False
            boss._mok_attack_frame = 0
            active = False
        boss._mok_previous_timer = timer
        boss._mok_attack_progress = (
            min(1.0, getattr(boss, "_mok_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_mok_last_x"):
            boss._mok_last_x = boss.x
            boss._mok_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mok_last_x)
        dy = abs(boss.y - boss._mok_last_y)
        boss._mok_last_x = boss.x
        boss._mok_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y, buff=False, ult=False):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_morvakhul._draw_hover_shadow(surface, x, y + 55, boss.pulse)
        _NS_morvakhul._draw_death_mist(surface, x, y + 45, boss.pulse, ult=ult)
        _NS_morvakhul._draw_body(surface, x + sway, y + bob,
                                 boss.direction, boss.pulse, "idle",
                                 buff=buff, ult=ult)
    def _draw_float_move(surface, boss, x, y, buff=False, ult=False):
        phase = boss.pulse * 1.9
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_morvakhul._draw_hover_shadow(surface, x + sway, y + 55, phase)
        _NS_morvakhul._draw_death_mist(surface, x + sway, y + 45, phase,
                                       trail=True, facing=boss.direction, ult=ult)
        _NS_morvakhul._draw_body(surface, x + sway, y + bob,
                                 boss.direction, phase, "move",
                                 buff=buff, ult=ult)
    def _draw_attack_pose(surface, boss, x, y, buff=False, ult=False):
        progress = getattr(boss, "_mok_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up → heavy overhead swing → recover
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 6) * boss.direction
            lift = int(t * 6)
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-6 + t * 22)) * boss.direction
            lift = int(6 - t * 10)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(16 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4)
        _NS_morvakhul._draw_hover_shadow(surface, x + lunge, y + 55, boss.pulse)
        _NS_morvakhul._draw_death_mist(surface, x + lunge, y + 45, boss.pulse,
                                       intense=True, ult=ult)
        _NS_morvakhul._draw_body(surface, x + lunge, y - lift,
                                 boss.direction, boss.pulse, "attack", progress,
                                 buff=buff, ult=ult)
        _NS_morvakhul._draw_axe_swing_fx(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                   buff=False, ult=False):
        # Blood Lust / Ult body glow
        if buff or ult:
            _NS_morvakhul._draw_body_glow(surface, cx, cy, phase, ult)
        # Tattered cape behind
        _NS_morvakhul._draw_cape(surface, cx, cy, facing, phase, action)
        # Skeleton spine armor behind
        _NS_morvakhul._draw_spine(surface, cx, cy, facing, phase)
        # Legs (armored)
        _NS_morvakhul._draw_legs(surface, cx, cy + 24, facing, phase)
        # Torso armor (dark cracked plate)
        _NS_morvakhul._draw_torso(surface, cx, cy, facing, phase, buff, ult)
        # SPIKY PAULDRONS
        _NS_morvakhul._draw_spiky_pauldrons(surface, cx, cy - 10, facing, phase, ult)
        # Arms
        _NS_morvakhul._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head (undead pale, glowing green eyes, black hair)
        _NS_morvakhul._draw_head(surface, cx, cy - 26, facing, phase, ult)
        # BIG EXECUTIONER AXE
        _NS_morvakhul._draw_executioner_axe(surface, cx, cy, facing, phase, action,
                                            attack_progress, ult)
        # Sparkles when buffed
        if buff or ult:
            _NS_morvakhul._draw_body_sparkles(surface, cx, cy, phase, ult)
    def _draw_body_glow(surface, cx, cy, phase, ult=False):
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        glow = pygame.Surface((160, 160), pygame.SRCALPHA)
        max_r = 70 if ult else 55
        for r in range(max_r, 5, -4):
            alpha = _NS_morvakhul._alpha((max_r - r) * 2 * pulse)
            _NS_morvakhul._aacircle(glow,
                                    (*_NS_morvakhul.PALETTE["curse_dark"], alpha),
                                    (80, 80), r)
        for r in range(int(max_r * 0.7), 5, -3):
            alpha = _NS_morvakhul._alpha((int(max_r * 0.7) - r) * 3 * pulse)
            _NS_morvakhul._aacircle(glow,
                                    (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                    (80, 80), r)
        surface.blit(glow, (cx - 80, cy - 80))
        # Radial energy lines
        if ult:
            for i in range(8):
                ang = phase * 0.5 + i * math.pi / 4
                for length_mult in (0.6, 1.0):
                    end_x = cx + int(math.cos(ang) * 60 * length_mult)
                    end_y = cy + int(math.sin(ang) * 60 * length_mult)
                    pygame.draw.line(surface,
                                     (*_NS_morvakhul.PALETTE["curse_hot"],
                                      _NS_morvakhul._alpha(180 * pulse)),
                                     (cx, cy), (end_x, end_y), 1)
    # ---------- CAPE ----------
    def _draw_cape(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 3
        if action == "move":
            sway = math.sin(phase * 1.2) * 5
        back_dir = -facing
        base_x = cx + back_dir * 6
        base_y = cy - 8
        # Tattered cape (rough bottom edge)
        # Left/right tips + notched bottom
        top_a = (base_x - 6, base_y)
        top_b = (base_x + 10 * back_dir, base_y)
        bot_a = (base_x - 14 + int(sway), base_y + 38)
        bot_b = (base_x + 18 * back_dir + int(sway), base_y + 35)
        # Notched bottom points
        notch_pts = []
        for i in range(6):
            t = i / 5
            nx = int(bot_a[0] + (bot_b[0] - bot_a[0]) * t)
            ny = int(bot_a[1] + (bot_b[1] - bot_a[1]) * t)
            # Alternate notches
            if i % 2 == 0:
                ny -= 4
            notch_pts.append((nx, ny))
        cape_pts = [top_a, top_b] + notch_pts[::-1]
        # Shadow
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in cape_pts])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["cloth_darkest"], cape_pts)
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["cloth_dark"], [
            (top_a[0] + 1, top_a[1] + 2),
            (top_b[0] - 1 * back_dir, top_b[1] + 2),
        ] + [(p[0], p[1] - 2) for p in notch_pts[::-1]])
        # Highlight on cape fold
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["cloth_mid"],
                         (base_x, base_y + 2),
                         (base_x + int(sway * 0.5), base_y + 20), 1)
    # ---------- SPINE (skeleton back armor accessory) ----------
    def _draw_spine(surface, cx, cy, facing, phase):
        back_dir = -facing
        spine_x = cx + back_dir * 4
        spine_y_top = cy - 12
        spine_y_bot = cy + 12
        # Vertical spine
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                         (spine_x + 1, spine_y_top + 1),
                         (spine_x + 1, spine_y_bot + 1), 4)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["bone_dark"],
                         (spine_x, spine_y_top), (spine_x, spine_y_bot), 3)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["bone_mid"],
                         (spine_x, spine_y_top), (spine_x, spine_y_bot), 2)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["bone_light"],
                         (spine_x - 1, spine_y_top), (spine_x - 1, spine_y_bot), 1)
        # Vertebrae bumps (every few pixels)
        for y_off in range(-10, 12, 4):
            vy = cy + y_off
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["bone_dark"],
                                    (spine_x, vy), 2)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["bone_mid"],
                                    (spine_x, vy), 1)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["bone_light"],
                             (spine_x, vy, 1, 1))
        # Rib bones extending outward
        for rib_y in (-6, -2, 2, 6):
            ry = cy + rib_y
            rib_end_x = spine_x + back_dir * 8
            rib_curve_y = ry + 2
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["bone_dark"],
                             (spine_x, ry), (rib_end_x, rib_curve_y), 2)
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["bone_mid"],
                             (spine_x, ry), (rib_end_x, rib_curve_y), 1)
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase):
        for side in (-1, 1):
            lx = cx + side * 5
            ly = cy
            # Thigh (armored)
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"], [
                (lx - 4 + 1, ly + 1), (lx + 4 + 1, ly + 1),
                (lx + 5 + 1, ly + 12 + 1), (lx - 5 + 1, ly + 12 + 1),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                (lx - 4, ly), (lx + 4, ly), (lx + 5, ly + 12), (lx - 5, ly + 12),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], [
                (lx - 3, ly + 1), (lx + 3, ly + 1),
                (lx + 4, ly + 11), (lx - 4, ly + 11),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
                (lx - 2, ly + 2), (lx + 2, ly + 2),
                (lx + 3, ly + 10), (lx - 3, ly + 10),
            ])
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_light"],
                             (lx, ly + 2), (lx, ly + 10), 1)
            # Cracks with green glow
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_dark"],
                             (lx - 2, ly + 3), (lx - 1, ly + 8), 1)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_mid"], (lx - 1, ly + 5, 1, 1))
            # Knee guard (spiked)
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                (lx - 4, ly + 12), (lx + 4, ly + 12),
                (lx + 3, ly + 15), (lx - 3, ly + 15),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], [
                (lx - 3, ly + 12), (lx + 3, ly + 12),
                (lx + 2, ly + 14), (lx - 2, ly + 14),
            ])
            # Knee spike
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                (lx - 2, ly + 12), (lx + 2, ly + 12), (lx, ly + 9),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
                (lx - 1, ly + 12), (lx + 1, ly + 12), (lx, ly + 10),
            ])
            # Boot (heavy armored)
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                (lx - 4, ly + 15), (lx + 4, ly + 15),
                (lx + 6, ly + 20), (lx - 3, ly + 20),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], [
                (lx - 3, ly + 16), (lx + 3, ly + 16),
                (lx + 5, ly + 19), (lx - 2, ly + 19),
            ])
            # Boot spikes
            for spike in (-3, 0, 4):
                _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                    (lx + spike, ly + 18), (lx + spike + 1, ly + 18),
                    (lx + spike, ly + 20 + facing),
                ])
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_mid"],
                                 (lx + spike, ly + 19, 1, 1))
    # ---------- TORSO ----------
    def _draw_torso(surface, cx, cy, facing, phase, buff, ult):
        # Broad muscular chest plate with cracks
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
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in pts])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], pts)
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], [
            (cx - 11, cy - 9), (cx - 13, cy - 5), (cx - 12, cy + 5),
            (cx - 9, cy + 17), (cx + 9, cy + 17),
            (cx + 12, cy + 5), (cx + 13, cy - 5), (cx + 11, cy - 9),
        ])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
            (cx - 9, cy - 7), (cx - 11, cy - 3), (cx - 10, cy + 3),
            (cx - 7, cy + 14), (cx + 7, cy + 14),
            (cx + 10, cy + 3), (cx + 11, cy - 3), (cx + 9, cy - 7),
        ])
        # Central chest highlight
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_light"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 2, cy + 3), (cx - 2, cy + 3),
        ])
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_shine"],
                         (cx - 1, cy - 5), (cx - 1, cy + 2), 1)
        # CRACKS with GREEN GLOW (execution/cursed motif) - very iconic!
        crack_pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        crack_alpha = _NS_morvakhul._alpha(230 * crack_pulse)
        # Vertical crack down chest
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_darkest"],
                         (cx, cy - 8), (cx, cy + 12), 2)
        pygame.draw.line(surface, (*_NS_morvakhul.PALETTE["curse_dark"], crack_alpha),
                         (cx, cy - 8), (cx, cy + 12), 1)
        # Branching cracks
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_darkest"],
                         (cx, cy - 4), (cx - 5, cy + 2), 2)
        pygame.draw.line(surface, (*_NS_morvakhul.PALETTE["curse_mid"], crack_alpha),
                         (cx, cy - 4), (cx - 5, cy + 2), 1)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_darkest"],
                         (cx, cy + 4), (cx + 6, cy + 10), 2)
        pygame.draw.line(surface, (*_NS_morvakhul.PALETTE["curse_mid"], crack_alpha),
                         (cx, cy + 4), (cx + 6, cy + 10), 1)
        # Green glow spots at crack intersections
        for spot in ((cx, cy - 3), (cx, cy + 4), (cx - 3, cy + 1), (cx + 4, cy + 8)):
            for r in range(3, 0, -1):
                alpha = _NS_morvakhul._alpha(180 * (3 - r) / 3 * crack_pulse)
                _NS_morvakhul._aacircle(surface,
                                        (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                                        spot, r)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_shine"],
                             (spot[0], spot[1], 1, 1))
        # Belt with skull emblem
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["leather_dark"],
                         (cx - 11, cy + 14, 22, 4))
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["leather_mid"],
                         (cx - 10, cy + 14, 20, 2))
        # Skull belt buckle
        _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                                (cx, cy + 16), 4)
        _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["bone_dark"],
                                (cx, cy + 16), 3)
        _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["bone_mid"],
                                (cx, cy + 16), 2)
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["bone_light"],
                         (cx, cy + 15, 1, 1))
        # Skull eye sockets
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                         (cx - 1, cy + 16, 1, 1))
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                         (cx + 1, cy + 16, 1, 1))
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_hot"],
                         (cx - 1, cy + 16, 1, 1))
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_hot"],
                         (cx + 1, cy + 16, 1, 1))
    # ---------- SPIKY PAULDRONS ----------
    def _draw_spiky_pauldrons(surface, cx, cy, facing, phase, ult=False):
        for side in (-1, 1):
            sx = cx + side * 13
            sy = cy
            # Large pauldron plate
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"], [
                (sx - 7 + 2, sy - 4 + 2), (sx + 8 + 2, sy - 4 + 2),
                (sx + 9 + 2, sy + 6 + 2), (sx - 8 + 2, sy + 6 + 2),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                (sx - 7, sy - 4), (sx + 8, sy - 4),
                (sx + 9, sy + 6), (sx - 8, sy + 6),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], [
                (sx - 6, sy - 3), (sx + 7, sy - 3),
                (sx + 8, sy + 5), (sx - 7, sy + 5),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
                (sx - 4, sy - 2), (sx + 5, sy - 2),
                (sx + 6, sy + 3), (sx - 5, sy + 3),
            ])
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_light"],
                             (sx - 2, sy - 1), (sx - 2, sy + 3), 1)
            # MULTIPLE SPIKES on pauldron (executioner's aesthetic)
            spike_configs = [
                (-4, -4, -6, -10),   # front spike
                (0, -4, -1, -12),    # tall center spike
                (4, -4, 5, -9),      # back spike
            ]
            for base_off_x, base_off_y, tip_off_x, tip_off_y in spike_configs:
                base_x = sx + base_off_x
                base_y = sy + base_off_y
                tip_x = sx + tip_off_x
                tip_y = sy + tip_off_y
                # Spike shadow
                _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"], [
                    (base_x - 2 + 1, base_y + 1),
                    (base_x + 2 + 1, base_y + 1),
                    (tip_x + 1, tip_y + 1),
                ])
                # Spike layered
                _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                    (base_x - 2, base_y), (base_x + 2, base_y), (tip_x, tip_y),
                ])
                _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], [
                    (base_x - 1, base_y), (base_x + 1, base_y), (tip_x, tip_y),
                ])
                _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
                    (base_x, base_y - 1), (tip_x, tip_y),
                    (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2)),
                ])
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_light"],
                                 (tip_x, tip_y, 1, 1))
                # Ultimate glow on spike tips
                if ult:
                    pulse = math.sin(phase * 3) * 0.3 + 0.7
                    for r in range(4, 0, -1):
                        alpha = _NS_morvakhul._alpha(140 * (4 - r) / 4 * pulse)
                        _NS_morvakhul._aacircle(surface,
                                                (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                                                (tip_x, tip_y), r)
            # Green crack on pauldron
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_dark"],
                             (sx - 3, sy - 1), (sx + 2, sy + 3), 1)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_mid"],
                             (sx, sy + 1, 1, 1))
    # ---------- ARMS ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        for side, is_axe_side in ((-1, False), (1, True)):
            base_x = cx + side * 12
            base_y = cy - 4
            is_dominant = (side * facing > 0)
            if action == "attack":
                if attack_progress < 0.4:
                    # Wind up: raise axe UP-BACK
                    t = attack_progress / 0.4
                    if is_dominant:
                        elbow_offset_x = int(-9 * facing)
                        elbow_offset_y = int(-11 - t * 3)
                        hand_offset_x = int(-14 * facing)
                        hand_offset_y = int(-18)
                    else:
                        # Support hand grips axe
                        elbow_offset_x = int(-5 * facing)
                        elbow_offset_y = int(-9 - t * 2)
                        hand_offset_x = int(-10 * facing)
                        hand_offset_y = int(-16)
                elif attack_progress < 0.65:
                    # HEAVY SWING DOWN
                    t = (attack_progress - 0.4) / 0.25
                    if is_dominant:
                        elbow_offset_x = int((-9 + t * 18) * facing)
                        elbow_offset_y = int(-14 + t * 20)
                        hand_offset_x = int((-14 + t * 30) * facing)
                        hand_offset_y = int(-18 + t * 24)
                    else:
                        elbow_offset_x = int((-5 + t * 12) * facing)
                        elbow_offset_y = int(-11 + t * 18)
                        hand_offset_x = int((-10 + t * 20) * facing)
                        hand_offset_y = int(-16 + t * 22)
                else:
                    # Recovery
                    t = (attack_progress - 0.65) / 0.35
                    if is_dominant:
                        elbow_offset_x = int((9 - t * 4) * facing)
                        elbow_offset_y = int(6 - t * 2)
                        hand_offset_x = int((16 - t * 6) * facing)
                        hand_offset_y = int(6 + t * 1)
                    else:
                        elbow_offset_x = int((7 - t * 3) * facing)
                        elbow_offset_y = int(7 - t * 2)
                        hand_offset_x = int((10 - t * 4) * facing)
                        hand_offset_y = int(6 + t * 1)
            else:
                # Idle: axe held resting in front
                swing = math.sin(phase * 0.5 + side) * 0.1
                if is_dominant:
                    elbow_offset_x = int(4 * facing + math.sin(swing) * 2)
                    elbow_offset_y = 4
                    hand_offset_x = int(11 * facing)
                    hand_offset_y = 8
                else:
                    elbow_offset_x = int(2 * facing)
                    elbow_offset_y = 4
                    hand_offset_x = int(7 * facing)
                    hand_offset_y = 6
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm (armored)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                                  (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 8)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                                  (base_x, base_y), (elbow_x, elbow_y), 7)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_dark"],
                                  (base_x, base_y), (elbow_x, elbow_y), 5)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_mid"],
                                  (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_light"],
                                  (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow (spiked joint)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                                    (elbow_x, elbow_y), 4)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_dark"],
                                    (elbow_x, elbow_y), 3)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_mid"],
                                    (elbow_x, elbow_y), 2)
            # Small elbow spike
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                             (elbow_x - 1, elbow_y - 4, 2, 3))
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_mid"],
                             (elbow_x, elbow_y - 3, 1, 1))
            # Forearm
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                                  (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 7)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                                  (elbow_x, elbow_y), (hand_x, hand_y), 6)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_dark"],
                                  (elbow_x, elbow_y), (hand_x, hand_y), 4)
            _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_mid"],
                                  (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
            # Green crack glow on forearm
            mid_arm_x = int((elbow_x + hand_x) / 2)
            mid_arm_y = int((elbow_y + hand_y) / 2)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_mid"],
                             (mid_arm_x, mid_arm_y, 1, 1))
            # Spiked gauntlet
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                                    (hand_x + 1, hand_y + 1), 5)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                                    (hand_x, hand_y), 4)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_dark"],
                                    (hand_x, hand_y), 3)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_mid"],
                                    (hand_x, hand_y), 2)
            # Knuckle spikes
            for kspike in (-1, 0, 1):
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                                 (hand_x + kspike, hand_y - 3, 1, 2))
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_mid"],
                                 (hand_x + kspike, hand_y - 2, 1, 1))
            if is_axe_side:
                _NS_morvakhul._last_axe_hand = (hand_x, hand_y, 0.0)
            else:
                _NS_morvakhul._last_off_hand = (hand_x, hand_y)
    # ---------- HEAD ----------
    def _draw_head(surface, cx, cy, facing, phase, ult=False):
        # Face — pale undead
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
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["skin_darkest"], face_pts)
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["skin_dark"], [
            (cx - 5, cy - 2), (cx - 6, cy + 1),
            (cx - 5, cy + 4), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 4),
            (cx + 6, cy + 1), (cx + 5, cy - 2),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["skin_mid"], [
            (cx - 3, cy - 1), (cx - 4, cy + 1),
            (cx - 3, cy + 3), (cx - 1, cy + 6),
            (cx + 1, cy + 6), (cx + 3, cy + 3),
            (cx + 4, cy + 1), (cx + 3, cy - 1),
            (cx + 2, cy - 5), (cx - 2, cy - 5),
        ])
        # Deathly cheek highlight
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["skin_light"],
                         (cx - 2 * facing, cy, 1, 1))
        # GLOWING GREEN EYES — very intense
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_col_glow = _NS_morvakhul.PALETTE["curse_hot"] if ult \
            else _NS_morvakhul.PALETTE["eye_glow"]
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            # Deep dark socket
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["shadow_deep"], (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            # HUGE halo glow
            for r in range(6, 0, -1):
                alpha = _NS_morvakhul._alpha(160 * (6 - r) / 6 * eye_pulse)
                _NS_morvakhul._aacircle(surface,
                                        (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                        (ex, ey), r)
            # Bright green core
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, eye_col_glow, (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["white"], (ex, ey - 1, 1, 1))
        # Grim mouth (thin line)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["skin_darkest"],
                         (cx - 1, cy + 6), (cx + 1, cy + 6), 1)
        # BLACK HAIR covering top of head + sides (creepy long hair)
        _NS_morvakhul._draw_hair(surface, cx, cy, facing, phase)
        # Green energy wisps rising from head
        for i in range(3):
            wisp_t = (phase * 0.7 + i * 0.33) % 1.0
            wx = cx - 3 + i * 3 + int(math.sin(phase * 2 + i) * 2)
            wy = cy - 8 - int(wisp_t * 12)
            alpha = _NS_morvakhul._alpha(200 * (1 - wisp_t))
            _NS_morvakhul._aacircle(surface,
                                    (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                    (wx, wy), 2)
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                             (wx, wy - 1, 1, 1))
    def _draw_hair(surface, cx, cy, facing, phase):
        """Long black hair covering top of head and hanging past shoulders."""
        sway = math.sin(phase * 0.4) * 2
        # Long hair silhouette (past shoulders, wispy)
        hair_pts = [
            (cx - 7, cy - 4),
            (cx - 9, cy),
            (cx - 10, cy + 6 + int(sway * 0.5)),
            (cx - 9, cy + 14 + int(sway)),
            (cx - 6, cy + 20 + int(sway * 1.2)),
            (cx - 2, cy + 22),
            (cx + 2, cy + 22),
            (cx + 6, cy + 20 + int(sway * 1.2)),
            (cx + 9, cy + 14 + int(sway)),
            (cx + 10, cy + 6 + int(sway * 0.5)),
            (cx + 9, cy),
            (cx + 7, cy - 4),
        ]
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["hair_darkest"], hair_pts)
        # Mid hair
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["hair_dark"], [
            (cx - 6, cy - 4),
            (cx - 8, cy + 4),
            (cx - 8, cy + 14 + int(sway)),
            (cx - 4, cy + 20),
            (cx + 4, cy + 20),
            (cx + 8, cy + 14 + int(sway)),
            (cx + 8, cy + 4),
            (cx + 6, cy - 4),
        ])
        # Front bangs covering forehead (partial eyes coverage - creepy)
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["hair_darkest"], [
            (cx - 5, cy - 7), (cx - 7, cy - 2),
            (cx - 4, cy - 3), (cx - 1, cy - 5),
            (cx + 1, cy - 5), (cx + 4, cy - 3),
            (cx + 7, cy - 2), (cx + 5, cy - 7),
        ])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["hair_dark"], [
            (cx - 4, cy - 6), (cx - 5, cy - 3),
            (cx - 2, cy - 4), (cx + 2, cy - 4),
            (cx + 5, cy - 3), (cx + 4, cy - 6),
        ])
        # Highlight strands
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["hair_mid"],
                         (cx - 6, cy - 2), (cx - 7, cy + 8 + int(sway)), 1)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["hair_mid"],
                         (cx + 6, cy - 2), (cx + 7, cy + 8 + int(sway)), 1)
        # Single bright strand on top
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["hair_light"],
                         (cx - 1, cy - 6), (cx - 1, cy - 3), 1)
    # ---------- EXECUTIONER AXE ----------
    def _draw_executioner_axe(surface, cx, cy, facing, phase, action, attack_progress,
                               ult=False):
        hand_data = getattr(_NS_morvakhul, "_last_axe_hand", None)
        if hand_data is None:
            hx, hy = cx + facing * 22, cy + 6
        else:
            hx, hy, _ = hand_data
        # Handle length (from hand)
        handle_len = 42
        # Angle
        if action == "attack":
            if attack_progress < 0.4:
                # Wind-up UP-BACK (raised overhead)
                if facing > 0:
                    handle_angle = -math.pi * 0.85
                else:
                    handle_angle = -math.pi * 0.15
            elif attack_progress < 0.65:
                # Massive swing DOWN
                t = (attack_progress - 0.4) / 0.25
                if facing > 0:
                    handle_angle = -math.pi * 0.85 + t * math.pi * 1.1
                else:
                    handle_angle = -math.pi * 0.15 - t * math.pi * 1.1
            else:
                # Recovery
                t = (attack_progress - 0.65) / 0.35
                if facing > 0:
                    handle_angle = math.pi * 0.25 - t * math.pi * 0.1
                else:
                    handle_angle = math.pi * 0.75 + t * math.pi * 0.1
        else:
            # Idle: axe held slightly diagonal down-forward
            if facing > 0:
                handle_angle = math.pi * 0.2 + math.sin(phase * 0.5) * 0.05
            else:
                handle_angle = math.pi * 0.8 + math.sin(phase * 0.5) * 0.05
        # Handle tip (blade end)
        blade_x = hx + int(math.cos(handle_angle) * handle_len)
        blade_y = hy + int(math.sin(handle_angle) * handle_len)
        # Pommel (behind hand)
        pom_x = hx - int(math.cos(handle_angle) * 6)
        pom_y = hy - int(math.sin(handle_angle) * 6)
        # === HANDLE (dark wood + steel) ===
        _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                              (pom_x + 2, pom_y + 2), (blade_x + 2, blade_y + 2), 6)
        _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_darkest"],
                              (pom_x, pom_y), (blade_x, blade_y), 5)
        _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_dark"],
                              (pom_x, pom_y), (blade_x, blade_y), 3)
        _NS_morvakhul._aaline(surface, _NS_morvakhul.PALETTE["armor_mid"],
                              (pom_x, pom_y - 1), (blade_x, blade_y - 1), 1)
        # Handle wraps
        for wrap_t in (0.3, 0.55, 0.8):
            wx = int(pom_x + (blade_x - pom_x) * wrap_t)
            wy = int(pom_y + (blade_y - pom_y) * wrap_t)
            perp = handle_angle + math.pi / 2
            wp_x = int(math.cos(perp) * 3)
            wp_y = int(math.sin(perp) * 3)
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["leather_dark"],
                             (wx - wp_x, wy - wp_y), (wx + wp_x, wy + wp_y), 2)
            pygame.draw.line(surface, _NS_morvakhul.PALETTE["leather_mid"],
                             (wx - wp_x, wy - wp_y), (wx + wp_x, wy + wp_y), 1)
        # Pommel (spike at bottom)
        _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                                (pom_x + 1, pom_y + 1), 4)
        _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_darkest"], (pom_x, pom_y), 3)
        _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["armor_dark"], (pom_x, pom_y), 2)
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_mid"], (pom_x, pom_y, 1, 1))
        # Pommel spike
        pom_spike_x = pom_x - int(math.cos(handle_angle) * 5)
        pom_spike_y = pom_y - int(math.sin(handle_angle) * 5)
        perp_spike = handle_angle + math.pi / 2
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
            (pom_x + int(math.cos(perp_spike) * 2), pom_y + int(math.sin(perp_spike) * 2)),
            (pom_x - int(math.cos(perp_spike) * 2), pom_y - int(math.sin(perp_spike) * 2)),
            (pom_spike_x, pom_spike_y),
        ])
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
            (pom_x + int(math.cos(perp_spike) * 1), pom_y + int(math.sin(perp_spike) * 1)),
            (pom_x - int(math.cos(perp_spike) * 1), pom_y - int(math.sin(perp_spike) * 1)),
            (pom_spike_x, pom_spike_y),
        ])
        pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_light"],
                         (pom_spike_x, pom_spike_y, 1, 1))
        # === MASSIVE AXE BLADE HEAD ===
        # Perpendicular direction for blade width
        perp = handle_angle + math.pi / 2
        # Blade is a large crescent/half-moon shape attached perpendicular to handle
        # Main blade points
        blade_base_x = blade_x
        blade_base_y = blade_y
        # Top of blade (opposite side of cutting edge)
        blade_top_x = blade_base_x - int(math.cos(perp) * 5)
        blade_top_y = blade_base_y - int(math.sin(perp) * 5)
        # Cutting edge (curved outward from handle)
        cutting_edge_far_x = blade_base_x + int(math.cos(perp) * 18)
        cutting_edge_far_y = blade_base_y + int(math.sin(perp) * 18)
        # Blade tips (front and back curve points)
        blade_front_x = blade_base_x + int(math.cos(handle_angle) * 12) + int(math.cos(perp) * 14)
        blade_front_y = blade_base_y + int(math.sin(handle_angle) * 12) + int(math.sin(perp) * 14)
        blade_back_x = blade_base_x - int(math.cos(handle_angle) * 12) + int(math.cos(perp) * 14)
        blade_back_y = blade_base_y - int(math.sin(handle_angle) * 12) + int(math.sin(perp) * 14)
        # Blade polygon (crescent shape)
        blade_poly = [
            (blade_base_x + int(math.cos(handle_angle) * 4),
             blade_base_y + int(math.sin(handle_angle) * 4)),   # front connection
            blade_front_x, blade_front_y,  # (placeholder, will replace below)
            cutting_edge_far_x, cutting_edge_far_y,
            blade_back_x, blade_back_y,
            (blade_base_x - int(math.cos(handle_angle) * 4),
             blade_base_y - int(math.sin(handle_angle) * 4)),   # back connection
            blade_top_x, blade_top_y,
        ]
        # Fix format (was mixing tuples & scalars)
        blade_poly = [
            (blade_base_x + int(math.cos(handle_angle) * 4),
             blade_base_y + int(math.sin(handle_angle) * 4)),
            (blade_front_x, blade_front_y),
            (cutting_edge_far_x, cutting_edge_far_y),
            (blade_back_x, blade_back_y),
            (blade_base_x - int(math.cos(handle_angle) * 4),
             blade_base_y - int(math.sin(handle_angle) * 4)),
            (blade_top_x, blade_top_y),
        ]
        # Shadow
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["shadow_deep"],
                            [(p[0] + 3, p[1] + 3) for p in blade_poly])
        # Base dark blade
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], blade_poly)
        # Inner darker (main body of blade)
        inner_poly = []
        for p in blade_poly:
            inner_poly.append((int(p[0] * 0.85 + blade_base_x * 0.15),
                               int(p[1] * 0.85 + blade_base_y * 0.15)))
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_dark"], inner_poly)
        # Mid layer
        _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
            (int(p[0] * 0.7 + blade_base_x * 0.3),
             int(p[1] * 0.7 + blade_base_y * 0.3))
            for p in blade_poly
        ])
        # Highlight sheen on top
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_light"],
                         (blade_base_x, blade_base_y),
                         (int((blade_top_x + blade_base_x) / 2),
                          int((blade_top_y + blade_base_y) / 2)), 1)
        # CUTTING EDGE HIGHLIGHT (bright edge line)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_light"],
                         (blade_front_x, blade_front_y),
                         (cutting_edge_far_x, cutting_edge_far_y), 2)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_shine"],
                         (blade_front_x, blade_front_y),
                         (cutting_edge_far_x, cutting_edge_far_y), 1)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_light"],
                         (cutting_edge_far_x, cutting_edge_far_y),
                         (blade_back_x, blade_back_y), 2)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["armor_shine"],
                         (cutting_edge_far_x, cutting_edge_far_y),
                         (blade_back_x, blade_back_y), 1)
        # GREEN CURSED CRACKS running through blade (iconic!)
        crack_pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        col_curse_mid = _NS_morvakhul.PALETTE["curse_hot"] if ult \
            else _NS_morvakhul.PALETTE["curse_mid"]
        col_curse_hot = _NS_morvakhul.PALETTE["curse_shine"] if ult \
            else _NS_morvakhul.PALETTE["curse_hot"]
        # Main crack from center to cutting edge
        crack_mid_x = int((blade_base_x + cutting_edge_far_x) / 2)
        crack_mid_y = int((blade_base_y + cutting_edge_far_y) / 2)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_darkest"],
                         (blade_base_x, blade_base_y),
                         (cutting_edge_far_x, cutting_edge_far_y), 3)
        pygame.draw.line(surface, (*_NS_morvakhul.PALETTE["curse_dark"],
                                   _NS_morvakhul._alpha(240 * crack_pulse)),
                         (blade_base_x, blade_base_y),
                         (cutting_edge_far_x, cutting_edge_far_y), 2)
        pygame.draw.line(surface, (*col_curse_mid,
                                   _NS_morvakhul._alpha(255 * crack_pulse)),
                         (blade_base_x, blade_base_y),
                         (cutting_edge_far_x, cutting_edge_far_y), 1)
        # Branch cracks
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_darkest"],
                         (crack_mid_x, crack_mid_y),
                         (int((crack_mid_x + blade_front_x) / 2),
                          int((crack_mid_y + blade_front_y) / 2)), 2)
        pygame.draw.line(surface, (*col_curse_mid,
                                   _NS_morvakhul._alpha(240 * crack_pulse)),
                         (crack_mid_x, crack_mid_y),
                         (int((crack_mid_x + blade_front_x) / 2),
                          int((crack_mid_y + blade_front_y) / 2)), 1)
        pygame.draw.line(surface, _NS_morvakhul.PALETTE["curse_darkest"],
                         (crack_mid_x, crack_mid_y),
                         (int((crack_mid_x + blade_back_x) / 2),
                          int((crack_mid_y + blade_back_y) / 2)), 2)
        pygame.draw.line(surface, (*col_curse_mid,
                                   _NS_morvakhul._alpha(240 * crack_pulse)),
                         (crack_mid_x, crack_mid_y),
                         (int((crack_mid_x + blade_back_x) / 2),
                          int((crack_mid_y + blade_back_y) / 2)), 1)
        # Bright glow spots at crack intersections
        for spot in ((crack_mid_x, crack_mid_y),
                     (blade_base_x, blade_base_y),
                     (cutting_edge_far_x, cutting_edge_far_y)):
            for r in range(5, 0, -1):
                alpha = _NS_morvakhul._alpha(180 * (5 - r) / 5 * crack_pulse)
                _NS_morvakhul._aacircle(surface,
                                        (*col_curse_hot, alpha),
                                        spot, r)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["white"],
                             (spot[0], spot[1], 1, 1))
        # SPIKES on top of blade (back edge)
        for spike_off in (-4, 0, 4):
            spike_base_x = blade_top_x + int(math.cos(handle_angle) * spike_off * 0.5)
            spike_base_y = blade_top_y + int(math.sin(handle_angle) * spike_off * 0.5)
            spike_tip_x = spike_base_x - int(math.cos(perp) * 4)
            spike_tip_y = spike_base_y - int(math.sin(perp) * 4)
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_darkest"], [
                (spike_base_x - int(math.cos(handle_angle) * 2),
                 spike_base_y - int(math.sin(handle_angle) * 2)),
                (spike_base_x + int(math.cos(handle_angle) * 2),
                 spike_base_y + int(math.sin(handle_angle) * 2)),
                (spike_tip_x, spike_tip_y),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["armor_mid"], [
                spike_base_x, spike_base_y, spike_tip_x, spike_tip_y,
            ] if False else [
                (spike_base_x - int(math.cos(handle_angle) * 1),
                 spike_base_y - int(math.sin(handle_angle) * 1)),
                (spike_base_x + int(math.cos(handle_angle) * 1),
                 spike_base_y + int(math.sin(handle_angle) * 1)),
                (spike_tip_x, spike_tip_y),
            ])
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["armor_light"],
                             (spike_tip_x, spike_tip_y, 1, 1))
    def _draw_body_sparkles(surface, cx, cy, phase, ult=False):
        col_hot = _NS_morvakhul.PALETTE["curse_shine"] if ult \
            else _NS_morvakhul.PALETTE["curse_hot"]
        for i in range(10):
            t = (phase * 0.6 + i * 0.1) % 1.0
            angle = i * math.pi / 5
            r = 30 + int(math.sin(phase + i) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy - 5 + int(math.sin(angle) * r) - int(t * 15)
            alpha = _NS_morvakhul._alpha(240 * (1 - t))
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["curse_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*col_hot, alpha), (sx, sy, 1, 1))
    # ============================================================
    # ATTACK FX: Big overhead axe swing arc
    # ============================================================
    def _draw_axe_swing_fx(surface, boss, x, y, progress):
        if progress < 0.4 or progress > 0.75:
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.35
        arc_cx = x + facing * 12
        arc_cy = y - 6
        # MASSIVE green crescent slash (executioner cleave)
        for i in range(6):
            layer_t = max(0, t - i * 0.07)
            if layer_t <= 0:
                continue
            alpha = _NS_morvakhul._alpha(250 * (1 - layer_t) * (1 - i * 0.14))
            radius = int(38 + layer_t * 12 + i * 4)
            if facing > 0:
                start_angle = -math.pi * 0.85
                end_angle = math.pi * 0.25
            else:
                start_angle = -math.pi * 0.15
                end_angle = math.pi * 0.75 + math.pi
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.15)
            steps = 16
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_darkest"], alpha),
                                          prev_pt, (px, py), 7)
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_dark"], alpha),
                                          prev_pt, (px, py), 5)
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                          prev_pt, (px, py), 3)
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_light"], alpha),
                                          prev_pt, (px, py), 2)
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                                          prev_pt, (px, py), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_morvakhul.PALETTE["curse_shine"], alpha),
                                     (px, py, 2, 2))
                prev_pt = (px, py)
        # Green sparks/embers flying
        if facing > 0:
            lead_angle = -math.pi * 0.85 + math.pi * 1.1 * t
        else:
            lead_angle = -math.pi * 0.15 - math.pi * 1.1 * t
        for i in range(12):
            spark_r = 38 + i * 3
            sx = arc_cx + int(math.cos(lead_angle) * spark_r)
            sy = arc_cy + int(math.sin(lead_angle) * spark_r)
            alpha = _NS_morvakhul._alpha(240 * (1 - i / 12))
            _NS_morvakhul._aacircle(surface,
                                    (*_NS_morvakhul.PALETTE["ember_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["ember_mid"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["ember_hot"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_hover_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, int((15 - radius) * 15 * pulse))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 5, 3, 180), (5, 9, 140, 14))
        pygame.draw.ellipse(shadow, (10, 40, 20, 120), (15, 11, 120, 10))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_death_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False, ult=False):
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        col_dark = _NS_morvakhul.PALETTE["curse_darkest"]
        col_mid = _NS_morvakhul.PALETTE["curse_dark"]
        col_light = _NS_morvakhul.PALETTE["curse_hot"] if ult else _NS_morvakhul.PALETTE["curse_light"]
        # Base mist
        mist = pygame.Surface((160, 45), pygame.SRCALPHA)
        for radius in range(35, 3, -3):
            alpha = _NS_morvakhul._alpha((35 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*col_dark, alpha),
                    (80 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2))
                )
        for radius in range(22, 3, -2):
            alpha = _NS_morvakhul._alpha((22 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*col_mid, alpha),
                    (80 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 80, cy - 8))
        # Rising green embers
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = _NS_morvakhul._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morvakhul._aacircle(surface,
                                    (*_NS_morvakhul.PALETTE["curse_dark"], alpha),
                                    (sx, sy), 3)
            _NS_morvakhul._aacircle(surface,
                                    (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*col_light, alpha), (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["ember_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_morvakhul._alpha(180 - i * 28)
                if alpha <= 0:
                    continue
                _NS_morvakhul._aacircle(surface,
                                        (*col_dark, alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_morvakhul._aacircle(surface,
                                        (*col_mid, alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*col_light, alpha), (sx, sy - 1, 2, 2))
    def _draw_death_aura(surface, x, y, phase, buff=False, is_ultimate=False):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        max_r = 105 if is_ultimate else (85 if buff else 75)
        for radius in range(max_r, 5, -5):
            alpha = _NS_morvakhul._alpha((max_r - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_morvakhul._aacircle(aura,
                                        (*_NS_morvakhul.PALETTE["curse_darkest"], alpha),
                                        (120, 100), radius)
        for radius in range(int(max_r * 0.65), 5, -4):
            alpha = _NS_morvakhul._alpha((int(max_r * 0.65) - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_morvakhul._aacircle(aura,
                                        (*_NS_morvakhul.PALETTE["curse_dark"], alpha),
                                        (120, 100), radius)
        for radius in range(int(max_r * 0.4), 5, -3):
            alpha = _NS_morvakhul._alpha((int(max_r * 0.4) - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_morvakhul._aacircle(aura,
                                        (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                        (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating green embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvakhul.PALETTE["curse_darkest"], 200),
                            (5, 20, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_morvakhul.PALETTE["shadow_deep"], 220),
                            (14, 22, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_morvakhul.PALETTE["curse_dark"], 230),
                            (25, 24, 130, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_morvakhul.PALETTE["curse_mid"],
                                   _NS_morvakhul._alpha(180 * pulse)),
                            (40, 26, 100, 14), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morvakhul.PALETTE["curse_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_morvakhul.PALETTE["curse_hot"],
                                 _NS_morvakhul._alpha(150 * pulse)),
                                (15, 12, 150, 38), 1)
        surface.blit(ring, (x - 90, y - 28))
    # ============================================================
    # SKILL Q: PENALTY ZONE (cleave forward + green circle)
    # ============================================================
    def _draw_penalty_zone(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Zone appears in front of caster after swing
        if progress < 0.3:
            return
        zone_x = x + facing * 55
        zone_y = y + 45
        # Growing/pulsing curse circle
        t = (progress - 0.3) / 0.7
        r = int(45 * min(1.0, t * 2))
        alpha_base = 220 * (1 - t * 0.3)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Multiple ring layers
        for i, (rad_off, thick, ab) in enumerate([
            (0, 3, alpha_base), (5, 2, alpha_base * 0.85), (10, 1, alpha_base * 0.7),
        ]):
            pygame.draw.ellipse(surface,
                                (*_NS_morvakhul.PALETTE["curse_dark"],
                                 _NS_morvakhul._alpha(ab * pulse)),
                                (zone_x - r + rad_off, zone_y - (r - rad_off) // 3,
                                 (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
        # Cursed runes around inside
        for i in range(6):
            ang = i * math.pi / 3 + phase * 0.3
            rx = zone_x + int(math.cos(ang) * (r * 0.6))
            ry = zone_y + int(math.sin(ang) * (r * 0.6) * 0.4)
            spike_h = int(6 + math.sin(phase * 3 + i) * 2)
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["curse_darkest"], [
                (rx - 2, ry), (rx + 2, ry), (rx, ry - spike_h),
            ])
            _NS_morvakhul._poly(surface, _NS_morvakhul.PALETTE["curse_mid"], [
                (rx - 1, ry), (rx + 1, ry), (rx, ry - spike_h + 1),
            ])
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_hot"],
                             (rx, ry - spike_h, 1, 1))
            pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_shine"],
                             (rx, ry - spike_h, 1, 1))
        # Bubbling energy in center
        for i in range(5):
            bt = (phase * 0.5 + i * 0.2) % 1.0
            bx = zone_x + int(math.cos(i * 1.3) * (r * 0.4))
            by = zone_y + int(math.sin(i * 1.3) * (r * 0.15)) - int(bt * 12)
            b_alpha = _NS_morvakhul._alpha(200 * (1 - bt))
            _NS_morvakhul._aacircle(surface,
                                    (*_NS_morvakhul.PALETTE["curse_mid"], b_alpha),
                                    (bx, by), 3)
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["curse_hot"], b_alpha),
                             (bx, by, 1, 1))
    def _draw_penalty_swing_fx(surface, boss, x, y, timer, phase):
        """Green cleave arc when Q is triggered."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.35:
            return
        t = progress / 0.35
        arc_cx = x + facing * 15
        arc_cy = y - 4
        # Wide crescent arc (green cleave)
        for i in range(5):
            layer_t = max(0, t - i * 0.08)
            if layer_t <= 0:
                continue
            alpha = _NS_morvakhul._alpha(250 * (1 - i * 0.15))
            radius = int(40 + layer_t * 10 + i * 3)
            if facing > 0:
                start_angle = -math.pi * 0.6
                end_angle = math.pi * 0.6
            else:
                start_angle = math.pi * 0.4
                end_angle = math.pi * 1.6
            current_end = start_angle + (end_angle - start_angle) * min(1.0, layer_t + 0.2)
            steps = 14
            prev_pt = None
            for s in range(steps + 1):
                seg_t = s / steps
                ang = start_angle + (current_end - start_angle) * seg_t
                px = arc_cx + int(math.cos(ang) * radius)
                py = arc_cy + int(math.sin(ang) * radius)
                if prev_pt is not None:
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_dark"], alpha),
                                          prev_pt, (px, py), 5)
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                          prev_pt, (px, py), 3)
                    _NS_morvakhul._aaline(surface,
                                          (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                                          prev_pt, (px, py), 1)
                prev_pt = (px, py)
    # ============================================================
    # SKILL W: BLOOD LUST (self buff)
    # ============================================================
    def _draw_blood_lust_ground(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Green rune circle beneath caster
        r = int(50 * min(1.0, progress * 2))
        if r > 3:
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 3, 240), (5, 2, 200), (10, 1, 160),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_morvakhul.PALETTE["curse_dark"],
                                     _NS_morvakhul._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 45 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
            # Rune spikes
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.3
                rx = x + int(math.cos(ang) * r)
                ry = y + 45 + int(math.sin(ang) * r * 0.4)
                spike_h = int(7 + math.sin(phase * 2 + i) * 3)
                _NS_morvakhul._poly(surface,
                                    (*_NS_morvakhul.PALETTE["curse_darkest"], 240), [
                    (rx - 2, ry), (rx + 2, ry), (rx, ry - spike_h),
                ])
                _NS_morvakhul._poly(surface,
                                    (*_NS_morvakhul.PALETTE["curse_mid"], 220), [
                    (rx - 1, ry), (rx + 1, ry), (rx, ry - spike_h + 1),
                ])
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_hot"],
                                 (rx, ry - spike_h, 1, 1))
    def _draw_blood_lust_fg(surface, boss, x, y, timer, phase):
        """Vertical green light pillar rising through boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pillar_h = 90
        pillar_alpha = _NS_morvakhul._alpha(150 * pulse)
        for width, color_key in [
            (24, "curse_dark"), (16, "curse_mid"),
            (10, "curse_light"), (5, "curse_hot"),
            (2, "curse_shine"),
        ]:
            pygame.draw.rect(surface,
                             (*_NS_morvakhul.PALETTE[color_key], pillar_alpha),
                             (x - width // 2, y - pillar_h + 30, width, pillar_h))
        # Rising sparkles
        for i in range(12):
            spark_t = (phase * 1.5 + i * 0.08) % 1.0
            spark_y = y + 30 - int(spark_t * pillar_h)
            spark_x = x + int(math.sin(phase * 3 + i) * 6)
            alpha = _NS_morvakhul._alpha(240 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                             (spark_x, spark_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_morvakhul.PALETTE["curse_shine"], alpha),
                             (spark_x, spark_y, 1, 1))
    # ============================================================
    # SKILL E: EXECUTION STRIKE (axe swing forward pulls enemy)
    # ============================================================
    def _draw_execution_ground(surface, boss, x, y, timer, phase):
        pass
    def _draw_execution_strike_fg(surface, boss, x, y, timer, phase):
        """Elongated axe swipe forward with pull effect line."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvakhul._target_position(boss, x, y)
        # Extended reach line (like axe extending forward)
        start_x = x + facing * 20
        start_y = y
        if progress < 0.3:
            # Wind-up glow at hand
            t = progress / 0.3
            cr = int(5 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_morvakhul._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_morvakhul._aacircle(surface,
                                        (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                        (start_x, start_y), r)
            _NS_morvakhul._aacircle(surface, _NS_morvakhul.PALETTE["curse_hot"],
                                    (start_x, start_y), cr - 2)
        elif progress < 0.7:
            # STRIKE FORWARD - long slash
            t = (progress - 0.3) / 0.4
            strike_end_x = int(start_x + (tx - start_x) * t)
            strike_end_y = int(start_y + (ty - start_y) * t)
            # Big elongated slash trail (like giant axe extending)
            perp_ang = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            for offset in (-5, -3, -1, 1, 3, 5):
                perp_x = int(math.cos(perp_ang) * offset)
                perp_y = int(math.sin(perp_ang) * offset)
                alpha = _NS_morvakhul._alpha(220 * (1 - abs(offset) / 5))
                _NS_morvakhul._aaline(surface,
                                      (*_NS_morvakhul.PALETTE["curse_darkest"], alpha),
                                      (start_x + perp_x, start_y + perp_y),
                                      (strike_end_x + perp_x, strike_end_y + perp_y), 3)
                _NS_morvakhul._aaline(surface,
                                      (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                      (start_x + perp_x, start_y + perp_y),
                                      (strike_end_x + perp_x, strike_end_y + perp_y), 2)
                _NS_morvakhul._aaline(surface,
                                      (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                                      (start_x + perp_x, start_y + perp_y),
                                      (strike_end_x + perp_x, strike_end_y + perp_y), 1)
            # Pull effect: arrow toward caster at target
            for i in range(4):
                arrow_x = int(strike_end_x - (strike_end_x - start_x) * (i * 0.1 + 0.3))
                arrow_y = int(strike_end_y - (strike_end_y - start_y) * (i * 0.1 + 0.3))
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_shine"],
                                 (arrow_x, arrow_y, 2, 2))
            # Impact splash at target
            for r in range(8, 0, -1):
                alpha = _NS_morvakhul._alpha(200 * (8 - r) / 8)
                _NS_morvakhul._aacircle(surface,
                                        (*_NS_morvakhul.PALETTE["curse_light"], alpha),
                                        (strike_end_x, strike_end_y), r)
        else:
            # Fade
            t = (progress - 0.7) / 0.3
            alpha = _NS_morvakhul._alpha(150 * (1 - t))
            _NS_morvakhul._aaline(surface,
                                  (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                  (start_x, start_y), (tx, ty), 2)
    # ============================================================
    # SKILL R: RETRIBUTION (massive radial AoE)
    # ============================================================
    def _draw_retribution_ground(surface, boss, x, y, timer, phase):
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # HUGE curse rune circle
        r = int(90 * min(1.0, progress * 1.5))
        if r > 3:
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 4, 240), (10, 3, 200), (20, 2, 160), (30, 1, 120),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_morvakhul.PALETTE["curse_dark"],
                                     _NS_morvakhul._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 50 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
            # Massive rune spikes
            for i in range(16):
                ang = i * math.pi / 8 + phase * 0.2
                spike_h = int(15 + math.sin(phase * 3 + i) * 4)
                rx = x + int(math.cos(ang) * r)
                ry = y + 50 + int(math.sin(ang) * r * 0.4)
                _NS_morvakhul._poly(surface,
                                    (*_NS_morvakhul.PALETTE["curse_darkest"], 240), [
                    (rx - 3, ry), (rx + 3, ry), (rx, ry - spike_h),
                ])
                _NS_morvakhul._poly(surface,
                                    (*_NS_morvakhul.PALETTE["curse_mid"], 240), [
                    (rx - 2, ry), (rx + 2, ry), (rx, ry - spike_h + 1),
                ])
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_hot"],
                                 (rx, ry - spike_h, 1, 2))
                pygame.draw.rect(surface, _NS_morvakhul.PALETTE["curse_shine"],
                                 (rx, ry - spike_h, 1, 1))
    def _draw_retribution_fg(surface, boss, x, y, timer, phase):
        """Massive green upward burst — Retribution."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Wind-up: gathering
            t = progress / 0.2
            for r in range(15, 0, -1):
                alpha = _NS_morvakhul._alpha(200 * (15 - r) / 15 * t)
                _NS_morvakhul._aacircle(surface,
                                        (*_NS_morvakhul.PALETTE["curse_dark"], alpha),
                                        (x, y), r)
        elif progress < 0.5:
            # ERUPTION - massive radial burst upward
            t = (progress - 0.2) / 0.3
            intensity = math.sin(t * math.pi)
            # Huge vertical & radial spikes of green energy
            burst_r = int(30 + t * 90)
            # Radial spikes shooting outward (like art reference)
            for i in range(20):
                ang = i * math.pi / 10 + phase * 0.1
                spike_far = burst_r + int(math.sin(i * 2) * 15)
                spike_near = int(burst_r * 0.15)
                perp = ang + math.pi / 2
                perp_x = math.cos(perp) * 4
                perp_y = math.sin(perp) * 4
                spike_tip_x = x + int(math.cos(ang) * spike_far)
                spike_tip_y = y + int(math.sin(ang) * spike_far)
                spike_base1_x = x + int(math.cos(ang) * spike_near + perp_x)
                spike_base1_y = y + int(math.sin(ang) * spike_near + perp_y)
                spike_base2_x = x + int(math.cos(ang) * spike_near - perp_x)
                spike_base2_y = y + int(math.sin(ang) * spike_near - perp_y)
                alpha = _NS_morvakhul._alpha(255 * intensity)
                _NS_morvakhul._poly(surface,
                                    (*_NS_morvakhul.PALETTE["curse_darkest"], alpha), [
                    (spike_base1_x, spike_base1_y),
                    (spike_tip_x, spike_tip_y),
                    (spike_base2_x, spike_base2_y),
                ])
                _NS_morvakhul._poly(surface,
                                    (*_NS_morvakhul.PALETTE["curse_dark"], alpha), [
                    (int(spike_base1_x * 0.7 + x * 0.3),
                     int(spike_base1_y * 0.7 + y * 0.3)),
                    (spike_tip_x, spike_tip_y),
                    (int(spike_base2_x * 0.7 + x * 0.3),
                     int(spike_base2_y * 0.7 + y * 0.3)),
                ])
                pygame.draw.line(surface,
                                 (*_NS_morvakhul.PALETTE["curse_mid"], alpha),
                                 (int(spike_base1_x * 0.5 + spike_base2_x * 0.5),
                                  int(spike_base1_y * 0.5 + spike_base2_y * 0.5)),
                                 (spike_tip_x, spike_tip_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_morvakhul.PALETTE["curse_hot"], alpha),
                                 (int(spike_base1_x * 0.5 + spike_base2_x * 0.5),
                                  int(spike_base1_y * 0.5 + spike_base2_y * 0.5)),
                                 (spike_tip_x, spike_tip_y), 1)
                pygame.draw.rect(surface,
                                 (*_NS_morvakhul.PALETTE["curse_shine"], alpha),
                                 (spike_tip_x, spike_tip_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_morvakhul.PALETTE["white"], alpha),
                                 (spike_tip_x, spike_tip_y, 1, 1))
            # Central core explosion
            core_alpha = _NS_morvakhul._alpha(240 * intensity)
            for r in range(30, 0, -3):
                _NS_morvakhul._aacircle(surface,
                                        (*_NS_morvakhul.PALETTE["curse_hot"],
                                         _NS_morvakhul._alpha(core_alpha * (30 - r) / 30)),
                                        (x, y), r)
        else:
            # Aftermath - lingering embers
            t = (progress - 0.5) / 0.5
            for i in range(20):
                rise_t = (phase * 0.6 + i * 0.08) % 1.0
                rx = x - 40 + int(math.sin(phase + i) * 40)
                ry = y + 30 - int(rise_t * 70)
                alpha = _NS_morvakhul._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_morvakhul._aacircle(surface,
                                            (*_NS_morvakhul.PALETTE["ember_dark"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_morvakhul.PALETTE["ember_hot"], alpha),
                                     (rx, ry, 1, 1))
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_morvakhul).keys()):
    _attr = vars(_NS_morvakhul)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_morvakhul, _attr_name, staticmethod(_attr))



# ====================================================================
# NYXARIEL (ABYSSAL TRICKSTER) - Mini Boss
# ====================================================================

class _NS_nyxariel:
    """Namespace nyxariel - HD abyssal trickster boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Teal/cyan skin (main body)
        "skin_darkest": (10, 30, 40),
        "skin_dark": (25, 70, 90),
        "skin_mid": (55, 130, 155),
        "skin_light": (110, 190, 210),
        "skin_shine": (180, 235, 245),
        # Belly (lighter cream/pale blue)
        "belly_dark": (60, 95, 115),
        "belly_mid": (130, 175, 195),
        "belly_light": (200, 225, 235),
        # Blue trident energy (glowing weapon)
        "trident_darkest": (5, 20, 60),
        "trident_dark": (15, 60, 140),
        "trident_mid": (55, 130, 230),
        "trident_light": (130, 210, 255),
        "trident_hot": (200, 240, 255),
        "trident_shine": (240, 250, 255),
        # Orange/amber eyes
        "eye_dark": (40, 15, 5),
        "eye_mid": (200, 100, 20),
        "eye_light": (255, 180, 60),
        "eye_glow": (255, 230, 150),
        # Wood/bronze trident shaft
        "wood_dark": (35, 25, 15),
        "wood_mid": (80, 55, 30),
        "wood_light": (140, 100, 55),
        # Bronze/gold trim
        "bronze_dark": (60, 40, 15),
        "bronze_mid": (140, 100, 40),
        "bronze_light": (220, 175, 90),
        # Leather straps (dark)
        "leather_dark": (25, 18, 15),
        "leather_mid": (55, 40, 30),
        "leather_light": (95, 70, 50),
        # Fang / teeth
        "fang_dark": (60, 55, 45),
        "fang_mid": (180, 170, 155),
        "fang_light": (230, 225, 210),
        # Water/foam effects
        "water_dark": (20, 55, 90),
        "water_mid": (60, 130, 190),
        "water_light": (150, 210, 240),
        "water_foam": (230, 245, 255),
        # Shark colors (for ultimate)
        "shark_darkest": (30, 45, 55),
        "shark_dark": (65, 85, 100),
        "shark_mid": (110, 130, 150),
        "shark_light": (170, 190, 210),
        "shark_belly": (220, 225, 230),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxariel._clamp(color)
        if _NS_nyxariel.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxariel._clamp(color)
        if _NS_nyxariel.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_nyxariel._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_nyxariel._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_nyxariel._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyxariel(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxariel._detect_moving(boss)
        _NS_nyxariel._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nyl_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_nyxariel._draw_water_aura(surface, x, y, pulse)
        _NS_nyxariel._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_nyxariel._draw_trident_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxariel._draw_shark_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxariel._draw_hop_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with buoyant bob
        # Special: during "E" skill = untargetable hop (shark form) → hide body
        hide_body = (active_skill == "e" and skill_timer > 25)
        if not hide_body:
            if attacking:
                _NS_nyxariel._draw_attack_pose(surface, boss, x, y)
            elif moving:
                _NS_nyxariel._draw_float_move(surface, boss, x, y)
            else:
                _NS_nyxariel._draw_float_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_nyxariel._draw_urchin_strike_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxariel._draw_seastone_trident_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxariel._draw_playful_hop_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxariel._draw_gnarly_shark_fg(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyl_previous_timer", 0))
        active = bool(getattr(boss, "_nyl_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nyl_attack_active = True
            boss._nyl_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nyl_attack_frame = int(getattr(boss, "_nyl_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nyl_attack_active = False
            boss._nyl_attack_frame = 0
            active = False
        boss._nyl_previous_timer = timer
        boss._nyl_attack_progress = (
            min(1.0, getattr(boss, "_nyl_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nyl_last_x"):
            boss._nyl_last_x = boss.x
            boss._nyl_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nyl_last_x)
        dy = abs(boss.y - boss._nyl_last_y)
        boss._nyl_last_x = boss.x
        boss._nyl_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        # Buoyant bob (like floating in water)
        bob = int(math.sin(boss.pulse * 0.8) * 4)
        sway = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_nyxariel._draw_hover_shadow(surface, x, y + 48, boss.pulse)
        _NS_nyxariel._draw_water_ripples(surface, x, y + 40, boss.pulse)
        _NS_nyxariel._draw_body(surface, x + sway, y + bob,
                                boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(math.sin(phase * 1.0) * 5)
        sway = int(math.sin(phase * 0.8) * 3)
        _NS_nyxariel._draw_hover_shadow(surface, x + sway, y + 48, phase)
        _NS_nyxariel._draw_water_ripples(surface, x + sway, y + 40, phase,
                                         trail=True, facing=boss.direction)
        _NS_nyxariel._draw_body(surface, x + sway, y + bob,
                                boss.direction, phase, "move")
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_nyl_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # QUICK JAB — small wind-back then thrust forward
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(3 - t * 4)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_nyxariel._draw_hover_shadow(surface, x + lunge, y + 48, boss.pulse)
        _NS_nyxariel._draw_water_ripples(surface, x + lunge, y + 40, boss.pulse,
                                         intense=True)
        _NS_nyxariel._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_nyxariel._draw_trident_jab_fx(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY (small chibi fish-humanoid)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Tail behind
        _NS_nyxariel._draw_tail(surface, cx, cy + 8, facing, phase)
        # Legs (short webbed)
        _NS_nyxariel._draw_legs(surface, cx, cy + 14, facing, phase, action)
        # Body torso (small, teal with belly)
        _NS_nyxariel._draw_torso(surface, cx, cy, facing, phase)
        # Arms
        _NS_nyxariel._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # BIG head with dorsal fin, gills, eyes, mouth
        _NS_nyxariel._draw_head(surface, cx, cy - 14, facing, phase)
        # TRIDENT (held in dominant hand)
        _NS_nyxariel._draw_trident(surface, cx, cy, facing, phase, action, attack_progress)
    # ---------- TAIL ----------
    def _draw_tail(surface, cx, cy, facing, phase):
        back_dir = -facing
        base_x = cx + back_dir * 6
        base_y = cy
        wave = math.sin(phase * 1.5) * 2
        # Tail curves back with wave
        tip_x = base_x + back_dir * 10
        tip_y = base_y + 4 + int(wave)
        mid_x = base_x + back_dir * 5
        mid_y = base_y + 2
        # Shadow
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                             (base_x + 1, base_y + 2), (tip_x + 1, tip_y + 2), 4)
        # Tail body
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                             (base_x, base_y), (mid_x, mid_y), 4)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_dark"],
                             (base_x, base_y), (mid_x, mid_y), 3)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_mid"],
                             (mid_x, mid_y), (tip_x, tip_y), 2)
        # Tail fin (fan shape at end)
        fin_pts = [
            (tip_x, tip_y),
            (tip_x + back_dir * 5, tip_y - 4 + int(wave * 0.5)),
            (tip_x + back_dir * 7, tip_y - 1),
            (tip_x + back_dir * 6, tip_y + 3),
            (tip_x + back_dir * 4, tip_y + 5 + int(wave * 0.5)),
        ]
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in fin_pts])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_darkest"], fin_pts)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_dark"], [
            (tip_x + back_dir, tip_y),
            (tip_x + back_dir * 4, tip_y - 3),
            (tip_x + back_dir * 5, tip_y),
            (tip_x + back_dir * 5, tip_y + 2),
            (tip_x + back_dir * 3, tip_y + 4),
        ])
        # Highlight strand
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["skin_mid"],
                         (tip_x + back_dir, tip_y),
                         (tip_x + back_dir * 6, tip_y - 2), 1)
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase, action):
        # Two short legs with webbed feet
        # Slight kick animation when moving/attacking
        kick_offset = 0
        if action == "move":
            kick_offset = int(math.sin(phase * 3) * 2)
        for side in (-1, 1):
            lx = cx + side * 3
            ly = cy
            actual_kick = kick_offset if side > 0 else -kick_offset
            # Thigh
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                                 (lx + 1, ly + 1), (lx + actual_kick + 1, ly + 6 + 1), 5)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                                 (lx, ly), (lx + actual_kick, ly + 6), 4)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_dark"],
                                 (lx, ly), (lx + actual_kick, ly + 6), 3)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_mid"],
                                 (lx, ly), (lx + actual_kick, ly + 6), 1)
            # Webbed foot
            foot_x = lx + actual_kick
            foot_y = ly + 6
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"], [
                (foot_x - 3 + 1, foot_y + 1), (foot_x + 3 + 1, foot_y + 1),
                (foot_x + 4 + 1, foot_y + 3 + 1), (foot_x - 3 + 1, foot_y + 3 + 1),
            ])
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_darkest"], [
                (foot_x - 3, foot_y), (foot_x + 3, foot_y),
                (foot_x + 4, foot_y + 3), (foot_x - 3, foot_y + 3),
            ])
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_dark"], [
                (foot_x - 2, foot_y + 1), (foot_x + 2, foot_y + 1),
                (foot_x + 3, foot_y + 2), (foot_x - 2, foot_y + 2),
            ])
            # Webbing (small toe lines)
            for toe in (-2, 0, 2):
                pygame.draw.line(surface, _NS_nyxariel.PALETTE["skin_mid"],
                                 (foot_x + toe, foot_y + 1),
                                 (foot_x + toe, foot_y + 3), 1)
            # Toe claws
            for toe in (-3, 0, 3):
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_mid"],
                                 (foot_x + toe, foot_y + 3, 1, 1))
    # ---------- TORSO (small teal body with pale belly) ----------
    def _draw_torso(surface, cx, cy, facing, phase):
        # Compact rounded body
        breath = math.sin(phase * 0.9) * 0.5
        body_pts = [
            (cx - 7, cy - 5),
            (cx - 8, cy - 1),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 8, cy - 1),
            (cx + 7, cy - 5),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ]
        # Shadow
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in body_pts])
        # Base
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_darkest"], body_pts)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_dark"], [
            (cx - 6, cy - 4), (cx - 7, cy - 1),
            (cx - 6, cy + 3), (cx - 4, cy + 7),
            (cx + 4, cy + 7), (cx + 6, cy + 3),
            (cx + 7, cy - 1), (cx + 6, cy - 4),
            (cx + 3, cy - 7), (cx - 3, cy - 7),
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_mid"], [
            (cx - 4, cy - 3), (cx - 6, cy),
            (cx - 4, cy + 3), (cx + 4, cy + 3),
            (cx + 6, cy), (cx + 4, cy - 3),
            (cx + 2, cy - 6), (cx - 2, cy - 6),
        ])
        # BELLY (pale front)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["belly_dark"], [
            (cx - 4, cy), (cx + 4, cy),
            (cx + 3, cy + 7), (cx - 3, cy + 7),
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["belly_mid"], [
            (cx - 3, cy + 1), (cx + 3, cy + 1),
            (cx + 2, cy + 6), (cx - 2, cy + 6),
        ])
        # Belly segments (2 horizontal lines)
        for y_off in (3, 5):
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["belly_dark"],
                             (cx - 2, cy + y_off), (cx + 2, cy + y_off), 1)
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["belly_light"],
                         (cx - 1, cy + 2, 2, 1))
        # LEATHER STRAP diagonal across chest
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["leather_dark"],
                         (cx - 6, cy - 3), (cx + 6, cy + 4), 2)
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["leather_mid"],
                         (cx - 6, cy - 3), (cx + 6, cy + 4), 1)
        # Buckle on strap
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["bronze_dark"],
                         (cx, cy, 3, 2))
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["bronze_mid"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["bronze_light"],
                         (cx, cy, 1, 1))
        # Small spots on body (fish scales pattern)
        for spot_pos in ((cx - 3, cy - 3), (cx + 3, cy - 3), (cx - 5, cy),
                          (cx + 5, cy), (cx - 4, cy - 5), (cx + 4, cy - 5)):
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                             (spot_pos[0], spot_pos[1], 1, 1))
    # ---------- ARMS ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        for side in (-1, 1):
            base_x = cx + side * 7
            base_y = cy - 3
            is_dominant = (side * facing > 0)
            if action == "attack" and is_dominant:
                # Trident jab motion
                if attack_progress < 0.3:
                    t = attack_progress / 0.3
                    # Pull back
                    elbow_offset_x = int(-4 * facing)
                    elbow_offset_y = int(2 - t * 2)
                    hand_offset_x = int(-6 * facing)
                    hand_offset_y = int(-2)
                elif attack_progress < 0.55:
                    t = (attack_progress - 0.3) / 0.25
                    # Thrust forward
                    elbow_offset_x = int((-4 + t * 14) * facing)
                    elbow_offset_y = 0
                    hand_offset_x = int((-6 + t * 22) * facing)
                    hand_offset_y = 0
                else:
                    t = (attack_progress - 0.55) / 0.45
                    # Retract
                    elbow_offset_x = int((10 - t * 4) * facing)
                    elbow_offset_y = 0
                    hand_offset_x = int((16 - t * 6) * facing)
                    hand_offset_y = 0
            else:
                # Idle sway
                swing = math.sin(phase * 0.7 + side) * 0.15
                if is_dominant:
                    # Holds trident diagonally
                    elbow_offset_x = int(3 * facing)
                    elbow_offset_y = 2
                    hand_offset_x = int(8 * facing)
                    hand_offset_y = 4
                else:
                    # Non-dominant hand
                    elbow_offset_x = int(math.sin(swing) * 2 * side)
                    elbow_offset_y = 3
                    hand_offset_x = int(math.sin(swing * 1.5) * 3 * side)
                    hand_offset_y = 6
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                                 (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 4)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                                 (base_x, base_y), (elbow_x, elbow_y), 3)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_dark"],
                                 (base_x, base_y), (elbow_x, elbow_y), 2)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_mid"],
                                 (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                                   (elbow_x, elbow_y), 2)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["skin_dark"],
                                   (elbow_x, elbow_y), 1)
            # Forearm
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                                 (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 3)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_dark"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 2)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["skin_mid"],
                                 (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
            # Hand (small with claws)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 3)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                                   (hand_x, hand_y), 2)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 1)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["skin_mid"],
                             (hand_x, hand_y, 1, 1))
            # Tiny claw tips
            for claw in (-1, 1):
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_mid"],
                                 (hand_x + claw * facing, hand_y - 1, 1, 1))
            if is_dominant:
                _NS_nyxariel._last_trident_hand = (hand_x, hand_y)
    # ---------- HEAD (big chibi fish head) ----------
    def _draw_head(surface, cx, cy, facing, phase):
        # Larger head proportional to body (chibi)
        # Head shape (rounded top, tapered chin)
        head_pts = [
            (cx - 8, cy - 3),
            (cx - 9, cy + 1),
            (cx - 8, cy + 5),
            (cx - 5, cy + 8),
            (cx - 1, cy + 9),
            (cx + 3, cy + 9),
            (cx + 7, cy + 6),
            (cx + 9, cy + 3),
            (cx + 10, cy - 1),
            (cx + 8, cy - 5),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ]
        # Shift head slightly forward based on facing
        head_pts = [(p[0] + facing, p[1]) for p in head_pts]
        # Shadow
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head_pts])
        # Base
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_darkest"], head_pts)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_dark"], [
            (cx - 7 + facing, cy - 2), (cx - 8 + facing, cy + 1),
            (cx - 7 + facing, cy + 4), (cx - 4 + facing, cy + 7),
            (cx + 2 + facing, cy + 8), (cx + 6 + facing, cy + 5),
            (cx + 8 + facing, cy + 2), (cx + 9 + facing, cy - 1),
            (cx + 7 + facing, cy - 4), (cx + 3 + facing, cy - 7),
            (cx - 3 + facing, cy - 7),
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_mid"], [
            (cx - 5 + facing, cy - 1), (cx - 6 + facing, cy + 1),
            (cx - 4 + facing, cy + 4), (cx + 2 + facing, cy + 5),
            (cx + 5 + facing, cy + 2), (cx + 6 + facing, cy - 1),
            (cx + 4 + facing, cy - 5), (cx - 2 + facing, cy - 5),
        ])
        # BELLY / snout white area (bottom of face)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["belly_dark"], [
            (cx - 3 + facing, cy + 3), (cx + 3 + facing, cy + 3),
            (cx + 2 + facing, cy + 8), (cx - 2 + facing, cy + 8),
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["belly_mid"], [
            (cx - 2 + facing, cy + 4), (cx + 2 + facing, cy + 4),
            (cx + 1 + facing, cy + 7), (cx - 1 + facing, cy + 7),
        ])
        # DORSAL FIN on top of head
        _NS_nyxariel._draw_head_fin(surface, cx + facing, cy - 8, facing, phase)
        # GILL FINS on sides of cheeks
        _NS_nyxariel._draw_gill_fins(surface, cx + facing, cy + 4, facing, phase)
        # EYES (big amber orange)
        _NS_nyxariel._draw_eyes(surface, cx + facing, cy, facing, phase)
        # MOUTH (wide with small teeth)
        _NS_nyxariel._draw_mouth(surface, cx + facing, cy + 6, facing, phase)
        # Spots on head
        for spot in ((cx - 4 + facing, cy - 3), (cx + 4 + facing, cy - 3),
                     (cx - 6 + facing, cy), (cx + 6 + facing, cy + 1)):
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                             (spot[0], spot[1], 1, 1))
    def _draw_head_fin(surface, cx, cy, facing, phase):
        """Dorsal fin on top of head (like fish crest)."""
        wave = math.sin(phase * 1.5) * 1
        fin_pts = [
            (cx - 3, cy + 2),
            (cx - 2, cy - 2 + int(wave)),
            (cx, cy - 5 + int(wave)),
            (cx + 2, cy - 3 + int(wave)),
            (cx + 4, cy - 6 + int(wave)),
            (cx + 5, cy - 2),
            (cx + 4, cy + 2),
        ]
        # Shift for facing
        fin_pts = [(p[0] + facing * 2, p[1]) for p in fin_pts]
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in fin_pts])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_darkest"], fin_pts)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_dark"], [
            (cx - 2 + facing * 2, cy + 1),
            (cx - 1 + facing * 2, cy - 1 + int(wave)),
            (cx + 1 + facing * 2, cy - 3 + int(wave)),
            (cx + 3 + facing * 2, cy - 4 + int(wave)),
            (cx + 4 + facing * 2, cy - 1),
            (cx + 3 + facing * 2, cy + 1),
        ])
        # Highlight strand
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["skin_mid"],
                         (cx + facing * 2, cy - 3 + int(wave)),
                         (cx + 3 + facing * 2, cy - 1), 1)
        # Bright tips
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["skin_light"],
                         (cx + facing * 2, cy - 4 + int(wave), 1, 1))
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["skin_shine"],
                         (cx + 4 + facing * 2, cy - 5 + int(wave), 1, 1))
    def _draw_gill_fins(surface, cx, cy, facing, phase):
        """Cheek fins on both sides."""
        for side in (-1, 1):
            fin_x = cx + side * 8
            fin_y = cy
            wave = math.sin(phase * 1.2 + side) * 1
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"], [
                (fin_x + 1, fin_y - 1 + 1),
                (fin_x + side * 4 + 1, fin_y - 2 + int(wave) + 1),
                (fin_x + side * 5 + 1, fin_y + 1),
                (fin_x + side * 3 + 1, fin_y + 3 + int(wave) + 1),
                (fin_x + 1, fin_y + 1 + 1),
            ])
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_darkest"], [
                (fin_x, fin_y - 1),
                (fin_x + side * 4, fin_y - 2 + int(wave)),
                (fin_x + side * 5, fin_y),
                (fin_x + side * 3, fin_y + 3 + int(wave)),
                (fin_x, fin_y + 1),
            ])
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["skin_dark"], [
                (fin_x, fin_y),
                (fin_x + side * 3, fin_y - 1 + int(wave * 0.5)),
                (fin_x + side * 4, fin_y),
                (fin_x + side * 2, fin_y + 2 + int(wave * 0.5)),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["skin_mid"],
                             (fin_x, fin_y),
                             (fin_x + side * 4, fin_y - 1 + int(wave * 0.5)), 1)
    def _draw_eyes(surface, cx, cy, facing, phase):
        """Big amber-orange eyes."""
        eye_pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            # Eye white/socket area (round)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                                   (ex + 1, ey + 1), 3)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["belly_light"],
                                   (ex, ey), 3)
            # Iris (orange amber)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["eye_dark"], (ex, ey), 2)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["eye_mid"], (ex, ey), 2)
            # Bright center
            for r in range(3, 0, -1):
                alpha = _NS_nyxariel._alpha(100 * (3 - r) / 3 * eye_pulse)
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["eye_light"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["eye_light"], (ex, ey, 1, 1))
            # Vertical pupil (slit)
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                             (ex, ey - 1), (ex, ey + 1), 1)
            # Bright shine
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["eye_glow"],
                             (ex - 1, ey - 1, 1, 1))
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["white"],
                             (ex - 1, ey - 1, 1, 1))
    def _draw_mouth(surface, cx, cy, facing, phase):
        """Wide mouth with small sharp teeth."""
        # Mouth line
        mouth_pts = [
            (cx - 4, cy),
            (cx - 3, cy + 1),
            (cx, cy + 2),
            (cx + 3, cy + 1),
            (cx + 4, cy),
        ]
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                         (cx - 4, cy), (cx + 4, cy), 2)
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["skin_darkest"],
                         (cx - 3, cy + 1), (cx + 3, cy + 1), 1)
        # Small teeth (top row)
        for tx_off in (-3, -1, 1, 3):
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_dark"],
                             (cx + tx_off, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_mid"],
                             (cx + tx_off, cy, 1, 1))
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_light"],
                         (cx, cy, 1, 1))
        # Bottom lip highlight (belly color)
        pygame.draw.line(surface, _NS_nyxariel.PALETTE["belly_mid"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
    # ---------- TRIDENT ----------
    def _draw_trident(surface, cx, cy, facing, phase, action, attack_progress):
        hand_data = getattr(_NS_nyxariel, "_last_trident_hand", None)
        if hand_data is None:
            hx, hy = cx + facing * 12, cy + 2
        else:
            hx, hy = hand_data
        # Trident length
        trident_len = 32
        # Angle
        if action == "attack":
            if attack_progress < 0.3:
                # Pull back — angle up
                if facing > 0:
                    blade_angle = -math.pi * 0.15
                else:
                    blade_angle = math.pi + math.pi * 0.15
            elif attack_progress < 0.55:
                # Thrust forward — horizontal
                if facing > 0:
                    blade_angle = 0
                else:
                    blade_angle = math.pi
            else:
                t = (attack_progress - 0.55) / 0.45
                if facing > 0:
                    blade_angle = -t * 0.1
                else:
                    blade_angle = math.pi + t * 0.1
        else:
            # Idle: diagonal down-forward
            if facing > 0:
                blade_angle = math.pi * 0.15 + math.sin(phase * 0.5) * 0.05
            else:
                blade_angle = math.pi * 0.85 + math.sin(phase * 0.5) * 0.05
        # Shaft
        # Trident tip position
        tip_center_x = hx + int(math.cos(blade_angle) * trident_len)
        tip_center_y = hy + int(math.sin(blade_angle) * trident_len)
        # Pommel (behind hand)
        pom_x = hx - int(math.cos(blade_angle) * 6)
        pom_y = hy - int(math.sin(blade_angle) * 6)
        # Shaft (wooden)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                             (pom_x + 1, pom_y + 1), (tip_center_x + 1, tip_center_y + 1), 4)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_dark"],
                             (pom_x, pom_y), (tip_center_x, tip_center_y), 3)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_mid"],
                             (pom_x, pom_y), (tip_center_x, tip_center_y), 2)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_light"],
                             (pom_x, pom_y - 1), (tip_center_x, tip_center_y - 1), 1)
        # Bronze binding at intervals along shaft
        for wrap_t in (0.25, 0.5, 0.75):
            wx = int(pom_x + (tip_center_x - pom_x) * wrap_t)
            wy = int(pom_y + (tip_center_y - pom_y) * wrap_t)
            perp = blade_angle + math.pi / 2
            wp_x = int(math.cos(perp) * 2)
            wp_y = int(math.sin(perp) * 2)
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["bronze_dark"],
                             (wx - wp_x, wy - wp_y), (wx + wp_x, wy + wp_y), 2)
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["bronze_light"],
                             (wx - wp_x, wy - wp_y), (wx + wp_x, wy + wp_y), 1)
        # Bronze pommel
        _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["shadow_deep"], (pom_x, pom_y), 3)
        _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["bronze_dark"], (pom_x, pom_y), 2)
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["bronze_light"], (pom_x, pom_y, 1, 1))
        # ==== TRIDENT HEAD (3 prongs) ====
        # Base of prongs at tip_center
        prong_perp = blade_angle + math.pi / 2
        prong_side_x = math.cos(prong_perp)
        prong_side_y = math.sin(prong_perp)
        # Center prong (longest, straight forward)
        center_tip_x = tip_center_x + int(math.cos(blade_angle) * 12)
        center_tip_y = tip_center_y + int(math.sin(blade_angle) * 12)
        # Side prongs (shorter, angled outward)
        side_prong_len = 9
        side_spread = 5
        left_base_x = tip_center_x + int(prong_side_x * side_spread)
        left_base_y = tip_center_y + int(prong_side_y * side_spread)
        right_base_x = tip_center_x - int(prong_side_x * side_spread)
        right_base_y = tip_center_y - int(prong_side_y * side_spread)
        left_tip_x = left_base_x + int(math.cos(blade_angle) * side_prong_len) + int(prong_side_x * 2)
        left_tip_y = left_base_y + int(math.sin(blade_angle) * side_prong_len) + int(prong_side_y * 2)
        right_tip_x = right_base_x + int(math.cos(blade_angle) * side_prong_len) - int(prong_side_x * 2)
        right_tip_y = right_base_y + int(math.sin(blade_angle) * side_prong_len) - int(prong_side_y * 2)
        # Crossbar (connects the 3 prong bases)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                             (left_base_x + 1, left_base_y + 1),
                             (right_base_x + 1, right_base_y + 1), 4)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["bronze_dark"],
                             (left_base_x, left_base_y), (right_base_x, right_base_y), 3)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["bronze_mid"],
                             (left_base_x, left_base_y), (right_base_x, right_base_y), 2)
        _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["bronze_light"],
                             (left_base_x, left_base_y - 1), (right_base_x, right_base_y - 1), 1)
        # Draw each prong (crystal blue with glow)
        for base_pt, tip_pt in [
            ((tip_center_x, tip_center_y), (center_tip_x, center_tip_y)),
            ((left_base_x, left_base_y), (left_tip_x, left_tip_y)),
            ((right_base_x, right_base_y), (right_tip_x, right_tip_y)),
        ]:
            # Prong shape (elongated triangle)
            prong_angle = math.atan2(tip_pt[1] - base_pt[1], tip_pt[0] - base_pt[0])
            prong_perp_local = prong_angle + math.pi / 2
            pw = 2
            edge_a = (base_pt[0] + int(math.cos(prong_perp_local) * pw),
                      base_pt[1] + int(math.sin(prong_perp_local) * pw))
            edge_b = (base_pt[0] - int(math.cos(prong_perp_local) * pw),
                      base_pt[1] - int(math.sin(prong_perp_local) * pw))
            # Shadow
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"], [
                (edge_a[0] + 1, edge_a[1] + 1),
                (tip_pt[0] + 1, tip_pt[1] + 1),
                (edge_b[0] + 1, edge_b[1] + 1),
            ])
            # Base blade
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["trident_darkest"], [
                edge_a, tip_pt, edge_b,
            ])
            _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["trident_dark"], [
                (int(edge_a[0] * 0.8 + base_pt[0] * 0.2),
                 int(edge_a[1] * 0.8 + base_pt[1] * 0.2)),
                tip_pt,
                (int(edge_b[0] * 0.8 + base_pt[0] * 0.2),
                 int(edge_b[1] * 0.8 + base_pt[1] * 0.2)),
            ])
            # Center line highlight
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_mid"],
                                 base_pt, tip_pt, 2)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_light"],
                                 base_pt, tip_pt, 1)
            # Glow along edges
            glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
            _NS_nyxariel._aaline(surface,
                                 (*_NS_nyxariel.PALETTE["trident_light"],
                                  _NS_nyxariel._alpha(200 * glow_pulse)),
                                 edge_a, tip_pt, 1)
            _NS_nyxariel._aaline(surface,
                                 (*_NS_nyxariel.PALETTE["trident_hot"],
                                  _NS_nyxariel._alpha(255 * glow_pulse)),
                                 edge_b, tip_pt, 1)
            # Tip sparkle
            for r in range(4, 0, -1):
                alpha = _NS_nyxariel._alpha(120 * (4 - r) / 4 * glow_pulse)
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["trident_light"], alpha),
                                       tip_pt, r)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_hot"],
                             (tip_pt[0], tip_pt[1], 1, 1))
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_shine"],
                             (tip_pt[0], tip_pt[1], 1, 1))
        # Central glow between prongs
        for r in range(6, 0, -1):
            alpha = _NS_nyxariel._alpha(80 * (6 - r) / 6 * (math.sin(phase * 2) * 0.3 + 0.7))
            _NS_nyxariel._aacircle(surface,
                                   (*_NS_nyxariel.PALETTE["trident_mid"], alpha),
                                   (tip_center_x, tip_center_y), r)
    # ============================================================
    # ATTACK FX: Trident jab thrust
    # ============================================================
    def _draw_trident_jab_fx(surface, boss, x, y, progress):
        if progress < 0.3 or progress > 0.7:
            return
        facing = boss.direction
        t = (progress - 0.3) / 0.4
        # Thrust line trail
        thrust_x = x + facing * 30
        thrust_y = y - 2
        # 3 parallel thrust lines (matching trident prongs)
        for prong_off in (-4, 0, 4):
            for i in range(3):
                layer_alpha = _NS_nyxariel._alpha(220 * (1 - t) * (1 - i * 0.25))
                start_x = x + facing * (10 + i * 5)
                end_x = thrust_x + facing * 5
                _NS_nyxariel._aaline(surface,
                                     (*_NS_nyxariel.PALETTE["trident_dark"], layer_alpha),
                                     (start_x, thrust_y + prong_off),
                                     (end_x, thrust_y + prong_off), 3)
                _NS_nyxariel._aaline(surface,
                                     (*_NS_nyxariel.PALETTE["trident_mid"], layer_alpha),
                                     (start_x, thrust_y + prong_off),
                                     (end_x, thrust_y + prong_off), 2)
                _NS_nyxariel._aaline(surface,
                                     (*_NS_nyxariel.PALETTE["trident_light"], layer_alpha),
                                     (start_x, thrust_y + prong_off),
                                     (end_x, thrust_y + prong_off), 1)
        # Impact splash at end
        splash_alpha = _NS_nyxariel._alpha(240 * (1 - t))
        for r in range(8, 0, -2):
            _NS_nyxariel._aacircle(surface,
                                   (*_NS_nyxariel.PALETTE["trident_light"],
                                    _NS_nyxariel._alpha(splash_alpha * (8 - r) / 8)),
                                   (thrust_x + facing * 8, thrust_y), r)
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_shine"],
                         (thrust_x + facing * 8, thrust_y, 2, 2))
        # Sparks flying
        for i in range(6):
            spark_ang = i * math.pi / 3 + phase_offset_hack(t)
            sp_r = 8 + int(t * 6)
            sx = thrust_x + facing * 8 + int(math.cos(spark_ang) * sp_r)
            sy = thrust_y + int(math.sin(spark_ang) * sp_r)
            pygame.draw.rect(surface, (*_NS_nyxariel.PALETTE["trident_hot"], splash_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_nyxariel.PALETTE["trident_shine"], splash_alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_hover_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((110, 24), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, int((11 - radius) * 14 * pulse))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 90 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 5, 12, 160), (5, 7, 100, 10))
        pygame.draw.ellipse(shadow, (15, 40, 70, 100), (12, 9, 86, 7))
        surface.blit(shadow, (x - 55, y - 12))
    def _draw_water_ripples(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Water splash/ripple effects beneath floating body."""
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Water ripple rings
        for i in range(3):
            ripple_t = (phase * 0.6 + i * 0.33) % 1.0
            r_ellipse = int(15 + ripple_t * 25)
            alpha = _NS_nyxariel._alpha(180 * (1 - ripple_t) * strength)
            if alpha > 0:
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                    (cx - r_ellipse, cy - r_ellipse // 3,
                                     r_ellipse * 2, r_ellipse * 2 // 3), 1)
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxariel.PALETTE["water_light"], alpha),
                                    (cx - r_ellipse + 1, cy - r_ellipse // 3,
                                     r_ellipse * 2 - 2, r_ellipse * 2 // 3), 1)
        # Bubble sparkles rising
        for i in range(8):
            t = (phase * 0.5 + i * 0.12) % 1.0
            bx = cx - 20 + i * 5 + int(math.sin(phase + i) * 3)
            by = cy + 3 - int(t * 18)
            alpha = _NS_nyxariel._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxariel._aacircle(surface,
                                   (*_NS_nyxariel.PALETTE["water_light"], alpha),
                                   (bx, by), 2, 1)
            pygame.draw.rect(surface,
                             (*_NS_nyxariel.PALETTE["water_foam"], alpha),
                             (bx, by, 1, 1))
        # Foam splashes
        for i in range(5):
            foam_ang = i * math.pi / 2.5 + phase * 0.3
            fr = 18 + int(math.sin(phase + i) * 4)
            fx = cx + int(math.cos(foam_ang) * fr)
            fy = cy + int(math.sin(foam_ang) * fr * 0.4)
            alpha = _NS_nyxariel._alpha(200 * strength)
            pygame.draw.rect(surface, (*_NS_nyxariel.PALETTE["water_foam"], alpha),
                             (fx, fy, 2, 2))
        # Trail behind
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxariel._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["water_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyxariel.PALETTE["water_foam"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_water_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_nyxariel._alpha((85 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_nyxariel._aacircle(aura,
                                       (*_NS_nyxariel.PALETTE["water_dark"], alpha),
                                       (100, 90), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_nyxariel._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyxariel._aacircle(aura,
                                       (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Floating bubbles
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["water_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["water_foam"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxariel.PALETTE["water_dark"], 200),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxariel.PALETTE["trident_darkest"], 220),
                            (14, 18, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxariel.PALETTE["water_mid"], 230),
                            (25, 20, 110, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_nyxariel.PALETTE["trident_light"], 180),
                            (40, 22, 80, 12), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_nyxariel.PALETTE["trident_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_nyxariel.PALETTE["trident_hot"],
                                 _NS_nyxariel._alpha(150 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q: URCHIN STRIKE (dash lunge)
    # ============================================================
    def _draw_urchin_strike_fx(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Motion streaks (dash effect)
        trail_len = 70
        for i in range(10):
            t = i / 10
            tx = x - facing * int(trail_len * t)
            ty = y + int(math.sin(t * math.pi) * 3)
            alpha = _NS_nyxariel._alpha(200 * (1 - t) * (1 - progress * 0.5))
            _NS_nyxariel._aaline(surface,
                                 (*_NS_nyxariel.PALETTE["trident_dark"], alpha),
                                 (tx, ty), (tx + facing * 10, ty), 4)
            _NS_nyxariel._aaline(surface,
                                 (*_NS_nyxariel.PALETTE["trident_mid"], alpha),
                                 (tx, ty), (tx + facing * 10, ty), 2)
            _NS_nyxariel._aaline(surface,
                                 (*_NS_nyxariel.PALETTE["trident_light"], alpha),
                                 (tx, ty), (tx + facing * 10, ty), 1)
        # Impact burst at end
        if progress > 0.5:
            tx_target, ty_target = _NS_nyxariel._target_position(boss, x, y)
            t = (progress - 0.5) / 0.5
            r = int(10 + t * 15)
            alpha = _NS_nyxariel._alpha(240 * (1 - t))
            _NS_nyxariel._aacircle(surface,
                                   (*_NS_nyxariel.PALETTE["trident_dark"], alpha),
                                   (tx_target, ty_target), r, 3)
            _NS_nyxariel._aacircle(surface,
                                   (*_NS_nyxariel.PALETTE["trident_mid"], alpha),
                                   (tx_target, ty_target), max(1, r - 3), 2)
            _NS_nyxariel._aacircle(surface,
                                   (*_NS_nyxariel.PALETTE["trident_hot"], alpha),
                                   (tx_target, ty_target), max(1, r - 6), 1)
            for i in range(6):
                ang = i * math.pi / 3
                ex = tx_target + int(math.cos(ang) * r)
                ey = ty_target + int(math.sin(ang) * r)
                pygame.draw.rect(surface, (*_NS_nyxariel.PALETTE["trident_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL W: SEASTONE TRIDENT (throw projectile)
    # ============================================================
    def _draw_trident_ground(surface, boss, x, y, timer, phase):
        pass  # handled in foreground
    def _draw_seastone_trident_projectile(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxariel._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 6
        if progress < 0.15:
            # Wind-up: pull back trident glowing
            t = progress / 0.15
            gather_r = int(6 + t * 4)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_nyxariel._alpha(200 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["trident_mid"], alpha),
                                       (start_x - facing * 5, start_y), r)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["trident_light"],
                                   (start_x - facing * 5, start_y), gather_r - 2)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_shine"],
                             (start_x - facing * 5, start_y, 2, 2))
        elif progress < 0.85:
            # Trident FLYING
            t = (progress - 0.15) / 0.7
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Motion trail
            for i in range(6):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_nyxariel._alpha(220 - i * 30)
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["trident_dark"], alpha),
                                       (px, py), max(1, 5 - i))
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["trident_mid"], alpha),
                                       (px, py), max(1, 3 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyxariel.PALETTE["trident_light"], alpha),
                                 (px, py, 1, 1))
            # DRAW SPINNING TRIDENT (mini version)
            spin_angle = phase * 8
            proj_angle = math.atan2(ty - start_y, tx - start_x)
            # Trident projectile with 3 prongs pointing forward
            # Shaft
            shaft_end_x = bx - int(math.cos(proj_angle) * 12)
            shaft_end_y = by - int(math.sin(proj_angle) * 12)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_dark"],
                                 (bx, by), (shaft_end_x, shaft_end_y), 3)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_mid"],
                                 (bx, by), (shaft_end_x, shaft_end_y), 2)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_light"],
                                 (bx, by), (shaft_end_x, shaft_end_y), 1)
            # 3 glowing prongs
            proj_perp = proj_angle + math.pi / 2
            for prong_off in (-4, 0, 4):
                base_x = bx + int(math.cos(proj_perp) * prong_off)
                base_y = by + int(math.sin(proj_perp) * prong_off)
                tip_x = base_x + int(math.cos(proj_angle) * 8)
                tip_y = base_y + int(math.sin(proj_angle) * 8)
                # Glow around prong
                for r in range(4, 0, -1):
                    alpha = _NS_nyxariel._alpha(150 * (4 - r) / 4)
                    _NS_nyxariel._aacircle(surface,
                                           (*_NS_nyxariel.PALETTE["trident_light"], alpha),
                                           (int((base_x + tip_x) / 2),
                                            int((base_y + tip_y) / 2)), r)
                _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_darkest"],
                                     (base_x, base_y), (tip_x, tip_y), 3)
                _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_mid"],
                                     (base_x, base_y), (tip_x, tip_y), 2)
                _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_light"],
                                     (base_x, base_y), (tip_x, tip_y), 1)
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_hot"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_shine"],
                                 (tip_x, tip_y, 1, 1))
            # Big glow around whole projectile
            for r in range(12, 0, -2):
                alpha = _NS_nyxariel._alpha(80 * (12 - r) / 12)
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["trident_mid"], alpha),
                                       (bx, by), r)
        else:
            # Trident STUCK in ground, glowing
            t = (progress - 0.85) / 0.15
            # Trident planted vertical
            stuck_x = tx
            stuck_y = ty
            # Shaft (vertical)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_dark"],
                                 (stuck_x, stuck_y - 15), (stuck_x, stuck_y + 3), 3)
            _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["wood_mid"],
                                 (stuck_x, stuck_y - 15), (stuck_x, stuck_y + 3), 2)
            # 3 prongs pointing up
            for prong_x in (-4, 0, 4):
                px = stuck_x + prong_x
                py_base = stuck_y - 15
                py_tip = py_base - 8
                for r in range(4, 0, -1):
                    alpha = _NS_nyxariel._alpha(180 * (4 - r) / 4)
                    _NS_nyxariel._aacircle(surface,
                                           (*_NS_nyxariel.PALETTE["trident_light"], alpha),
                                           (px, (py_base + py_tip) // 2), r)
                _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_darkest"],
                                     (px, py_base), (px, py_tip), 3)
                _NS_nyxariel._aaline(surface, _NS_nyxariel.PALETTE["trident_mid"],
                                     (px, py_base), (px, py_tip), 2)
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["trident_shine"],
                                 (px, py_tip, 1, 1))
            # Pulsing ground glow around stuck trident
            pulse_r = int(15 + math.sin(phase * 3) * 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxariel.PALETTE["trident_dark"], 180),
                                (stuck_x - pulse_r, stuck_y - pulse_r // 3,
                                 pulse_r * 2, pulse_r * 2 // 3), 2)
    # ============================================================
    # SKILL E: PLAYFUL / TRICKSTER (hop untargetable)
    # ============================================================
    def _draw_hop_ground(surface, boss, x, y, timer, phase):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground splash where he was
        if progress < 0.3:
            t = progress / 0.3
            r = int(15 + t * 10)
            alpha = _NS_nyxariel._alpha(220 * (1 - t))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxariel.PALETTE["water_foam"], alpha),
                                (x - r + 3, y + 45 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 1)
            # Water splash particles flying outward
            for i in range(10):
                ang = i * math.pi / 5
                sr = int(t * 20)
                sx = x + int(math.cos(ang) * sr)
                sy = y + 45 + int(math.sin(ang) * sr * 0.4)
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["water_light"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["water_foam"], (sx, sy, 1, 1))
    def _draw_playful_hop_fx(surface, boss, x, y, timer, phase):
        """Untargetable hop - character does small hop then lands."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if 0.3 <= progress < 0.9:
            # Show fish silhouette leaping (untargetable form)
            # Hop arc
            t = (progress - 0.3) / 0.6
            hop_x = x + int(math.sin(t * math.pi) * 40 * boss.direction)
            hop_y = y - int(math.sin(t * math.pi) * 30)
            # Draw silhouette (transparent fish shape)
            alpha = _NS_nyxariel._alpha(200 * math.sin(t * math.pi))
            # Small fish body silhouette
            fish_pts = [
                (hop_x - 8, hop_y),
                (hop_x - 6, hop_y - 3),
                (hop_x + 3, hop_y - 3),
                (hop_x + 6, hop_y - 1),
                (hop_x + 8, hop_y + 1),
                (hop_x + 6, hop_y + 3),
                (hop_x + 3, hop_y + 3),
                (hop_x - 6, hop_y + 3),
            ]
            _NS_nyxariel._poly(surface,
                               (*_NS_nyxariel.PALETTE["skin_darkest"], alpha),
                               fish_pts)
            _NS_nyxariel._poly(surface,
                               (*_NS_nyxariel.PALETTE["skin_dark"], alpha),
                               [(p[0], p[1]) for p in fish_pts])
            # Tail fin
            _NS_nyxariel._poly(surface,
                               (*_NS_nyxariel.PALETTE["skin_darkest"], alpha), [
                (hop_x - 8, hop_y - 1),
                (hop_x - 12, hop_y - 4),
                (hop_x - 12, hop_y + 4),
                (hop_x - 8, hop_y + 1),
            ])
            # Eye
            pygame.draw.rect(surface, (*_NS_nyxariel.PALETTE["eye_light"], alpha),
                             (hop_x + 3, hop_y - 1, 1, 1))
            # Water trail behind
            for i in range(6):
                trail_t = max(0, t - i * 0.05)
                trail_x = x + int(math.sin(trail_t * math.pi) * 40 * boss.direction)
                trail_y = y - int(math.sin(trail_t * math.pi) * 30)
                t_alpha = _NS_nyxariel._alpha(180 * math.sin(trail_t * math.pi) * (1 - i / 6))
                if t_alpha > 0:
                    _NS_nyxariel._aacircle(surface,
                                           (*_NS_nyxariel.PALETTE["water_mid"], t_alpha),
                                           (trail_x, trail_y), max(1, 4 - i))
                    pygame.draw.rect(surface,
                                     (*_NS_nyxariel.PALETTE["water_foam"], t_alpha),
                                     (trail_x, trail_y, 1, 1))
    # ============================================================
    # SKILL R: GNARLY SHARK (Ultimate)
    # ============================================================
    def _draw_shark_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nyxariel._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Warning water ripple at target
        if progress < 0.3:
            t = progress / 0.3
            r = int(30 + t * 20)
            alpha = _NS_nyxariel._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxariel.PALETTE["water_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
        else:
            # After shark passes: water trail
            t = (progress - 0.3) / 0.7
            trail_len = 100
            trail_start_x = x + boss.direction * 30
            trail_end_x = tx
            trail_start_y = y + 45
            trail_end_y = ty
            for i in range(8):
                seg_t = i / 8
                sx = int(trail_start_x + (trail_end_x - trail_start_x) * seg_t)
                sy = int(trail_start_y + (trail_end_y - trail_start_y) * seg_t)
                alpha = _NS_nyxariel._alpha(150 * (1 - t) * (1 - seg_t * 0.3))
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                    (sx - 12, sy - 5, 24, 10))
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxariel.PALETTE["water_foam"], alpha),
                                    (sx - 8, sy - 3, 16, 6))
    def _draw_gnarly_shark_fg(surface, boss, x, y, timer, phase):
        """MASSIVE shark leaping through the area."""
        tx, ty = _NS_nyxariel._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.15:
            # Wind-up: gathering water at fizz position
            t = progress / 0.15
            gather_r = int(8 + t * 6)
            for r in range(gather_r + 5, 0, -1):
                alpha = _NS_nyxariel._alpha(220 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                       (x, y + 10), r)
            _NS_nyxariel._aacircle(surface, _NS_nyxariel.PALETTE["water_foam"],
                                   (x, y + 10), gather_r - 2)
            return
        if progress >= 0.15 and progress < 0.85:
            # SHARK LEAP animation
            t = (progress - 0.15) / 0.7
            # Shark position (arc from fizz to target)
            shark_start_x = x + facing * 20
            shark_start_y = y
            shark_x = int(shark_start_x + (tx - shark_start_x) * t)
            # Arc up then down
            shark_y = int(shark_start_y + (ty - shark_start_y) * t - math.sin(t * math.pi) * 40)
            _NS_nyxariel._draw_shark(surface, shark_x, shark_y, facing, phase, t)
            # Water splash under shark
            splash_y = y + 40
            for i in range(6):
                splash_x = shark_x - int(facing * i * 8) + int(math.sin(phase * 3 + i) * 3)
                splash_alpha = _NS_nyxariel._alpha(220 - i * 30)
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["water_light"], splash_alpha),
                                       (splash_x, splash_y), max(2, 6 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyxariel.PALETTE["water_foam"], splash_alpha),
                                 (splash_x, splash_y - 1, 2, 2))
            # Water spray above shark
            for i in range(10):
                spray_ang = math.pi + i * math.pi / 10
                sr = 20 + int(math.sin(phase * 4 + i) * 5)
                sx = shark_x + int(math.cos(spray_ang) * sr) * facing
                sy = shark_y + int(math.sin(spray_ang) * sr)
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["water_foam"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_nyxariel.PALETTE["white"], (sx, sy, 1, 1))
        else:
            # Aftermath: water splashing where shark landed
            t = (progress - 0.85) / 0.15
            for i in range(15):
                ang = i * math.pi / 7.5
                r = int(15 + t * 25)
                sx = tx + int(math.cos(ang) * r)
                sy = ty + int(math.sin(ang) * r * 0.6)
                alpha = _NS_nyxariel._alpha(240 * (1 - t))
                _NS_nyxariel._aacircle(surface,
                                       (*_NS_nyxariel.PALETTE["water_mid"], alpha),
                                       (sx, sy), 3)
                pygame.draw.rect(surface,
                                 (*_NS_nyxariel.PALETTE["water_foam"], alpha),
                                 (sx, sy, 2, 2))
    def _draw_shark(surface, cx, cy, facing, phase, t):
        """Draw the MASSIVE shark leaping."""
        # Shark angle (tilts based on arc)
        # At t=0.5 shark is horizontal, otherwise tilts up/down
        angle = math.sin(t * math.pi) * -0.3 * facing + (1 if t > 0.5 else -1) * 0.2 * facing
        # Big shark body (elongated fusiform)
        shark_len = 60
        body_pts_top = []
        body_pts_bot = []
        for i in range(11):
            p_t = i / 10
            # Along shark length
            along_x = int(math.cos(angle) * (shark_len * (p_t - 0.5))) * facing
            along_y = int(math.sin(angle) * (shark_len * (p_t - 0.5))) * facing
            # Thickness (fusiform - fat middle, tapered ends)
            thick = int(math.sin(p_t * math.pi) * 12 + 2)
            perp = angle + math.pi / 2
            top_x = cx + along_x + int(math.cos(perp) * thick)
            top_y = cy + along_y + int(math.sin(perp) * thick)
            bot_x = cx + along_x - int(math.cos(perp) * thick)
            bot_y = cy + along_y - int(math.sin(perp) * thick)
            body_pts_top.append((top_x, top_y))
            body_pts_bot.append((bot_x, bot_y))
        # Full body polygon
        body_pts = body_pts_top + list(reversed(body_pts_bot))
        # Shadow
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in body_pts])
        # Body layers
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_darkest"], body_pts)
        # Top darker
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_dark"], body_pts_top + [
            (int((body_pts_top[-1][0] + body_pts_bot[-1][0]) / 2),
             int((body_pts_top[-1][1] + body_pts_bot[-1][1]) / 2)),
            (int((body_pts_top[0][0] + body_pts_bot[0][0]) / 2),
             int((body_pts_top[0][1] + body_pts_bot[0][1]) / 2)),
        ])
        # Mid layer
        mid_pts_top = []
        for i, p in enumerate(body_pts_top):
            p_t = i / 10
            thick = int(math.sin(p_t * math.pi) * 8 + 1)
            perp = angle + math.pi / 2
            along_x = int(math.cos(angle) * (shark_len * (p_t - 0.5))) * facing
            along_y = int(math.sin(angle) * (shark_len * (p_t - 0.5))) * facing
            top_x = cx + along_x + int(math.cos(perp) * thick)
            top_y = cy + along_y + int(math.sin(perp) * thick)
            mid_pts_top.append((top_x, top_y))
        # BELLY (light bottom)
        belly_pts_bot = []
        for i, p in enumerate(body_pts_bot):
            p_t = i / 10
            thick = int(math.sin(p_t * math.pi) * 10 + 1)
            perp = angle + math.pi / 2
            along_x = int(math.cos(angle) * (shark_len * (p_t - 0.5))) * facing
            along_y = int(math.sin(angle) * (shark_len * (p_t - 0.5))) * facing
            bot_x = cx + along_x - int(math.cos(perp) * thick)
            bot_y = cy + along_y - int(math.sin(perp) * thick)
            belly_pts_bot.append((bot_x, bot_y))
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_belly"],
                           belly_pts_bot + list(reversed([
                               (int((body_pts_top[i][0] + body_pts_bot[i][0]) / 2),
                                int((body_pts_top[i][1] + body_pts_bot[i][1]) / 2))
                               for i in range(11)
                           ])))
        # Highlight streak along top
        for i in range(len(mid_pts_top) - 1):
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["shark_light"],
                             mid_pts_top[i], mid_pts_top[i + 1], 1)
        # DORSAL FIN on top
        mid_idx = 5
        dorsal_base_x = cx + int(math.cos(angle) * (shark_len * (mid_idx / 10 - 0.5))) * facing
        dorsal_base_y = cy + int(math.sin(angle) * (shark_len * (mid_idx / 10 - 0.5))) * facing
        perp = angle + math.pi / 2
        dorsal_tip_x = dorsal_base_x + int(math.cos(perp) * 22)
        dorsal_tip_y = dorsal_base_y + int(math.sin(perp) * 22)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_darkest"], [
            (dorsal_base_x - 6 * facing, dorsal_base_y + int(math.sin(perp) * 12) - 6),
            (dorsal_tip_x, dorsal_tip_y),
            (dorsal_base_x + 4 * facing, dorsal_base_y + int(math.sin(perp) * 12)),
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_dark"], [
            (dorsal_base_x - 5 * facing, dorsal_base_y + int(math.sin(perp) * 12) - 5),
            (dorsal_tip_x - facing, dorsal_tip_y),
            (dorsal_base_x + 3 * facing, dorsal_base_y + int(math.sin(perp) * 12) - 1),
        ])
        # TAIL FIN (crescent moon shape at end)
        tail_base = body_pts_top[0]  # back of shark
        tail_offset_x = int(math.cos(angle) * -15) * facing
        tail_offset_y = int(math.sin(angle) * -15) * facing
        tail_tip_up = (tail_base[0] + tail_offset_x + int(math.cos(perp) * 15),
                       tail_base[1] + tail_offset_y + int(math.sin(perp) * 15))
        tail_tip_down = (tail_base[0] + tail_offset_x - int(math.cos(perp) * 15),
                         tail_base[1] + tail_offset_y - int(math.sin(perp) * 15))
        tail_mid = (tail_base[0] + tail_offset_x, tail_base[1] + tail_offset_y)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_darkest"], [
            body_pts_top[0], tail_tip_up, tail_mid,
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_darkest"], [
            body_pts_bot[0], tail_tip_down, tail_mid,
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_dark"], [
            body_pts_top[0], tail_tip_up,
            (int((tail_tip_up[0] + tail_mid[0]) / 2),
             int((tail_tip_up[1] + tail_mid[1]) / 2)),
        ])
        # HEAD/JAW area (at facing end)
        head_pos = body_pts_top[-1]
        head_center_x = int((body_pts_top[-1][0] + body_pts_bot[-1][0]) / 2) + int(math.cos(angle) * 6) * facing
        head_center_y = int((body_pts_top[-1][1] + body_pts_bot[-1][1]) / 2) + int(math.sin(angle) * 6) * facing
        # OPEN MOUTH — massive jaw
        # Mouth opening
        mouth_top_pts = [
            (head_center_x - int(math.cos(angle) * 10) * facing,
             head_center_y - int(math.sin(angle) * 10) * facing + int(math.cos(perp) * 4)),
            (head_center_x + int(math.cos(angle) * 10) * facing,
             head_center_y + int(math.sin(angle) * 10) * facing),
            (head_center_x - int(math.cos(angle) * 10) * facing,
             head_center_y - int(math.sin(angle) * 10) * facing - int(math.cos(perp) * 4)),
        ]
        # Dark inner mouth
        mouth_pts = [
            (head_center_x + int(math.cos(perp) * 6),
             head_center_y + int(math.sin(perp) * 6)),
            (head_center_x + int(math.cos(angle) * 12) * facing,
             head_center_y + int(math.sin(angle) * 12) * facing),
            (head_center_x - int(math.cos(perp) * 6),
             head_center_y - int(math.sin(perp) * 6)),
        ]
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shadow_deep"], mouth_pts)
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["eye_dark"], [
            (mouth_pts[0][0] + facing, mouth_pts[0][1]),
            (int((mouth_pts[1][0] + mouth_pts[0][0]) / 2),
             int((mouth_pts[1][1] + mouth_pts[0][1]) / 2)),
            (int((mouth_pts[1][0] + mouth_pts[2][0]) / 2),
             int((mouth_pts[1][1] + mouth_pts[2][1]) / 2)),
            (mouth_pts[2][0] + facing, mouth_pts[2][1]),
        ])
        # SHARP TEETH (jagged rows)
        for tooth_i in range(5):
            tt = tooth_i / 4
            # Upper teeth
            u_x = int(mouth_pts[0][0] + (mouth_pts[1][0] - mouth_pts[0][0]) * tt)
            u_y = int(mouth_pts[0][1] + (mouth_pts[1][1] - mouth_pts[0][1]) * tt)
            u_tip_x = u_x + int(math.cos(perp) * 2)
            u_tip_y = u_y + int(math.sin(perp) * 2)
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["fang_light"],
                             (u_x, u_y), (u_tip_x, u_tip_y), 1)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_light"],
                             (u_tip_x, u_tip_y, 1, 1))
            # Lower teeth
            l_x = int(mouth_pts[2][0] + (mouth_pts[1][0] - mouth_pts[2][0]) * tt)
            l_y = int(mouth_pts[2][1] + (mouth_pts[1][1] - mouth_pts[2][1]) * tt)
            l_tip_x = l_x - int(math.cos(perp) * 2)
            l_tip_y = l_y - int(math.sin(perp) * 2)
            pygame.draw.line(surface, _NS_nyxariel.PALETTE["fang_light"],
                             (l_x, l_y), (l_tip_x, l_tip_y), 1)
            pygame.draw.rect(surface, _NS_nyxariel.PALETTE["fang_light"],
                             (l_tip_x, l_tip_y, 1, 1))
        # EYE (small yellow angry)
        eye_x = head_center_x - int(math.cos(angle) * 3) * facing + int(math.cos(perp) * 5)
        eye_y = head_center_y - int(math.sin(angle) * 3) * facing + int(math.sin(perp) * 5)
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["shadow_deep"],
                         (eye_x - 1, eye_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["eye_mid"], (eye_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_nyxariel.PALETTE["eye_glow"], (eye_x, eye_y, 1, 1))
        # SIDE FIN
        side_fin_base_x = cx + int(math.cos(angle) * 5) * facing - int(math.cos(perp) * 4)
        side_fin_base_y = cy + int(math.sin(angle) * 5) * facing - int(math.sin(perp) * 4)
        side_fin_tip_x = side_fin_base_x - int(math.cos(perp) * 12) - int(math.cos(angle) * 5) * facing
        side_fin_tip_y = side_fin_base_y - int(math.sin(perp) * 12) - int(math.sin(angle) * 5) * facing
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_darkest"], [
            (side_fin_base_x - 3 * facing, side_fin_base_y),
            (side_fin_tip_x, side_fin_tip_y),
            (side_fin_base_x + 3 * facing, side_fin_base_y),
        ])
        _NS_nyxariel._poly(surface, _NS_nyxariel.PALETTE["shark_dark"], [
            (side_fin_base_x - 2 * facing, side_fin_base_y),
            (side_fin_tip_x, side_fin_tip_y),
            (side_fin_base_x + 2 * facing, side_fin_base_y),
        ])
# Simple helper for the fx (avoid missing phase var)
def phase_offset_hack(t):
    return t * 6.28
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_nyxariel).keys()):
    _attr = vars(_NS_nyxariel)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_nyxariel, _attr_name, staticmethod(_attr))



# ====================================================================
# ZARETHYR (ASTRAL SOVEREIGN) - TRUE BOSS
# ====================================================================

class _NS_zarethyr:
    """Namespace zarethyr - HD astral sovereign TRUE BOSS."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Deep navy robe (main outfit)
        "robe_darkest": (5, 8, 25),
        "robe_dark": (18, 25, 55),
        "robe_mid": (40, 55, 100),
        "robe_light": (85, 105, 160),
        "robe_shine": (150, 175, 220),
        # Silver/white robe inner (lining)
        "silver_dark": (95, 105, 130),
        "silver_mid": (170, 180, 205),
        "silver_light": (220, 228, 240),
        "silver_shine": (250, 253, 255),
        # Gold trim (royal accents)
        "gold_darkest": (45, 30, 8),
        "gold_dark": (110, 80, 25),
        "gold_mid": (200, 160, 55),
        "gold_light": (245, 215, 115),
        "gold_shine": (255, 240, 180),
        # Cosmic blue light (main FX color)
        "cosmic_darkest": (5, 15, 55),
        "cosmic_dark": (15, 55, 145),
        "cosmic_mid": (55, 130, 235),
        "cosmic_light": (130, 200, 255),
        "cosmic_hot": (200, 235, 255),
        "cosmic_shine": (240, 250, 255),
        # Skin (pale porcelain)
        "skin_dark": (155, 120, 105),
        "skin_mid": (215, 180, 165),
        "skin_light": (245, 215, 200),
        "skin_shine": (255, 235, 225),
        # Hair (dark navy blue with silver highlights)
        "hair_darkest": (8, 12, 30),
        "hair_dark": (22, 30, 60),
        "hair_mid": (55, 70, 115),
        "hair_light": (110, 130, 180),
        "hair_shine": (180, 195, 230),
        # Star/gem (bright blue)
        "gem_dark": (10, 40, 100),
        "gem_mid": (60, 140, 235),
        "gem_light": (150, 220, 255),
        "gem_hot": (220, 245, 255),
        # Eye (bright celestial blue)
        "eye_dark": (5, 25, 65),
        "eye_mid": (70, 160, 240),
        "eye_glow": (200, 240, 255),
        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 10),
        "white": (255, 255, 255),
    }
    # ---------- helpers ----------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zarethyr._clamp(color)
        if _NS_zarethyr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zarethyr._clamp(color)
        if _NS_zarethyr.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_zarethyr._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_zarethyr._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_zarethyr._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    def _draw_star_4point(surface, cx, cy, size, color, alpha=255):
        """Draw a 4-pointed star (sparkle)."""
        color = (*_NS_zarethyr._clamp(color)[:3], _NS_zarethyr._alpha(alpha))
        pts = [
            (cx, cy - size),
            (cx + max(1, size // 3), cy - max(1, size // 3)),
            (cx + size, cy),
            (cx + max(1, size // 3), cy + max(1, size // 3)),
            (cx, cy + size),
            (cx - max(1, size // 3), cy + max(1, size // 3)),
            (cx - size, cy),
            (cx - max(1, size // 3), cy - max(1, size // 3)),
        ]
        _NS_zarethyr._poly(surface, color, pts)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zarethyr(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zarethyr._detect_moving(boss)
        _NS_zarethyr._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_zar_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (big cosmic aura)
        _NS_zarethyr._draw_cosmic_aura(surface, x, y, pulse,
                                       is_ultimate=(active_skill == "r"))
        _NS_zarethyr._draw_constellation_ring(surface, x, y + 55, pulse, active_skill)
        # Skill ground FX (behind)
        if active_skill == "w":
            _NS_zarethyr._draw_stardust_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zarethyr._draw_dawn_triumph_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating majestic
        if attacking:
            _NS_zarethyr._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_zarethyr._draw_float_move(surface, boss, x, y)
        else:
            _NS_zarethyr._draw_float_idle(surface, boss, x, y)
        # Foreground skill FX
        if active_skill == "q":
            _NS_zarethyr._draw_infinite_extension(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zarethyr._draw_stardust_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zarethyr._draw_reality_shock(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zarethyr._draw_dawn_triumph_fg(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zar_previous_timer", 0))
        active = bool(getattr(boss, "_zar_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._zar_attack_active = True
            boss._zar_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._zar_attack_frame = int(getattr(boss, "_zar_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._zar_attack_active = False
            boss._zar_attack_frame = 0
            active = False
        boss._zar_previous_timer = timer
        boss._zar_attack_progress = (
            min(1.0, getattr(boss, "_zar_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zar_last_x"):
            boss._zar_last_x = boss.x
            boss._zar_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zar_last_x)
        dy = abs(boss.y - boss._zar_last_y)
        boss._zar_last_x = boss.x
        boss._zar_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSES
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_zarethyr._draw_hover_shadow(surface, x, y + 60, boss.pulse)
        _NS_zarethyr._draw_cosmic_plume(surface, x, y + 45, boss.pulse)
        _NS_zarethyr._draw_body(surface, x + sway, y + bob,
                                boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_zarethyr._draw_hover_shadow(surface, x + sway, y + 60, phase)
        _NS_zarethyr._draw_cosmic_plume(surface, x + sway, y + 45, phase,
                                        trail=True, facing=boss.direction)
        _NS_zarethyr._draw_body(surface, x + sway, y + bob,
                                boss.direction, phase, "move")
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_zar_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Elegant cast motion (mage graceful)
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
            lift = int(3 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(7 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_zarethyr._draw_hover_shadow(surface, x + lunge, y + 60, boss.pulse)
        _NS_zarethyr._draw_cosmic_plume(surface, x + lunge, y + 45, boss.pulse,
                                        intense=True)
        _NS_zarethyr._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_zarethyr._draw_starlight_bolt(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY (TRUE BOSS scale - bigger)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Robe skirt behind (flowing)
        _NS_zarethyr._draw_robe_skirt(surface, cx, cy + 8, facing, phase, action)
        # Legs (partially hidden by robe)
        _NS_zarethyr._draw_legs(surface, cx, cy + 22, facing, phase)
        # Torso (robe top)
        _NS_zarethyr._draw_torso(surface, cx, cy, facing, phase)
        # Gold epaulettes (shoulders)
        _NS_zarethyr._draw_epaulettes(surface, cx, cy - 8, facing, phase)
        # Arms (with flowing sleeves)
        _NS_zarethyr._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head (handsome face + navy hair + forehead gem)
        _NS_zarethyr._draw_head(surface, cx, cy - 26, facing, phase)
        # Constellation stars orbiting body (TRUE BOSS signature)
        _NS_zarethyr._draw_orbiting_stars(surface, cx, cy, phase)
        # Hand light orb (if idle/casting)
        _NS_zarethyr._draw_hand_light(surface, cx, cy, facing, phase, action, attack_progress)
    # ---------- ROBE SKIRT ----------
    def _draw_robe_skirt(surface, cx, cy, facing, phase, action):
        """Long flowing robe skirt."""
        sway = math.sin(phase * 0.5) * 3
        if action == "move":
            sway = math.sin(phase * 1.2) * 5
        # Wider trapezoidal robe (long flowing)
        top_a = (cx - 10, cy - 6)
        top_b = (cx + 10, cy - 6)
        bot_a = (cx - 20 + int(sway), cy + 30)
        bot_b = (cx + 20 + int(sway), cy + 28)
        mid_a = (cx - 14 + int(sway * 0.5), cy + 12)
        mid_b = (cx + 14 + int(sway * 0.5), cy + 12)
        # Shadow
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["shadow_deep"], [
            (top_a[0] + 2, top_a[1] + 2), (top_b[0] + 2, top_b[1] + 2),
            (bot_b[0] + 2, bot_b[1] + 2), (bot_a[0] + 2, bot_a[1] + 2),
        ])
        # Base robe (dark navy)
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_darkest"],
                           [top_a, top_b, mid_b, bot_b, bot_a, mid_a])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_dark"], [
            (top_a[0] + 1, top_a[1] + 1), (top_b[0] - 1, top_b[1] + 1),
            (mid_b[0] - 1, mid_b[1]), (bot_b[0] - 2, bot_b[1] - 2),
            (bot_a[0] + 2, bot_a[1] - 2), (mid_a[0] + 1, mid_a[1]),
        ])
        # Central highlight fold
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_mid"], [
            (cx - 2, cy - 4), (cx + 2, cy - 4),
            (cx + 5, cy + 20), (cx - 5, cy + 20),
        ])
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["robe_light"],
                         (cx, cy - 4), (cx, cy + 20), 1)
        # SILVER/WHITE INNER LINING visible at bottom hem
        for i in range(6):
            t = i / 5
            px = int(bot_a[0] + (bot_b[0] - bot_a[0]) * t)
            py = int(bot_a[1] + (bot_b[1] - bot_a[1]) * t)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["silver_dark"],
                             (px - 1, py, 3, 2))
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["silver_mid"],
                             (px, py, 1, 1))
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["silver_light"],
                             (px, py, 1, 1))
        # Gold trim runes along bottom
        for i in range(3):
            t = 0.2 + i * 0.3
            px = int(bot_a[0] + (bot_b[0] - bot_a[0]) * t)
            py = int(bot_a[1] + (bot_b[1] - bot_a[1]) * t) - 3
            _NS_zarethyr._draw_star_4point(surface, px, py, 2,
                                           _NS_zarethyr.PALETTE["gold_mid"])
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_shine"],
                             (px, py, 1, 1))
    # ---------- LEGS ----------
    def _draw_legs(surface, cx, cy, facing, phase):
        # Feet visible at bottom (small)
        for side in (-1, 1):
            lx = cx + side * 3
            ly = cy + 15
            # Shoe/boot
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["shadow_deep"], [
                (lx - 2 + 1, ly + 1), (lx + 3 + 1, ly + 1),
                (lx + 4 + 1, ly + 3 + 1), (lx - 2 + 1, ly + 3 + 1),
            ])
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_darkest"], [
                (lx - 2, ly), (lx + 3, ly),
                (lx + 4, ly + 3), (lx - 2, ly + 3),
            ])
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_dark"], [
                (lx - 1, ly + 1), (lx + 2, ly + 1),
                (lx + 3, ly + 2), (lx - 1, ly + 2),
            ])
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_mid"],
                             (lx + 2, ly + 1, 2, 1))
    # ---------- TORSO ----------
    def _draw_torso(surface, cx, cy, facing, phase):
        # Slim mage torso
        pts = [
            (cx - 10, cy - 10),
            (cx - 12, cy - 5),
            (cx - 11, cy + 5),
            (cx - 9, cy + 15),
            (cx + 9, cy + 15),
            (cx + 11, cy + 5),
            (cx + 12, cy - 5),
            (cx + 10, cy - 10),
        ]
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in pts])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_darkest"], pts)
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["robe_dark"], [
            (cx - 9, cy - 9), (cx - 11, cy - 5), (cx - 10, cy + 4),
            (cx - 8, cy + 14), (cx + 8, cy + 14),
            (cx + 10, cy + 4), (cx + 11, cy - 5), (cx + 9, cy - 9),
        ])
        # Silver/white central chest panel (V-neck accent)
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["silver_dark"], [
            (cx - 4, cy - 8), (cx + 4, cy - 8),
            (cx + 3, cy + 3), (cx - 3, cy + 3),
        ])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["silver_mid"], [
            (cx - 3, cy - 7), (cx + 3, cy - 7),
            (cx + 2, cy + 2), (cx - 2, cy + 2),
        ])
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["silver_light"],
                         (cx, cy - 6), (cx, cy), 1)
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["silver_shine"],
                         (cx, cy - 5, 1, 1))
        # Gold trim at V-neck edges
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["gold_dark"],
                         (cx - 4, cy - 8), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["gold_dark"],
                         (cx + 4, cy - 8), (cx + 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["gold_mid"],
                         (cx - 4, cy - 8), (cx + 4, cy - 8), 1)
        # BLUE GEMSTONE PENDANT at chest
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_x = cx
        gem_y = cy - 3
        # Halo
        for r in range(7, 0, -1):
            alpha = _NS_zarethyr._alpha(90 * (7 - r) / 7 * gem_pulse)
            _NS_zarethyr._aacircle(surface,
                                   (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                   (gem_x, gem_y), r)
        # Diamond gem
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gem_dark"], [
            (gem_x, gem_y - 3), (gem_x + 2, gem_y),
            (gem_x, gem_y + 3), (gem_x - 2, gem_y),
        ])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gem_mid"], [
            (gem_x, gem_y - 2), (gem_x + 1, gem_y),
            (gem_x, gem_y + 2), (gem_x - 1, gem_y),
        ])
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gem_hot"], (gem_x, gem_y, 1, 1))
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (gem_x, gem_y - 1, 1, 1))
        # Gold sash/belt at waist
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_dark"],
                         (cx - 10, cy + 11, 20, 3))
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_mid"],
                         (cx - 9, cy + 11, 18, 2))
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_shine"],
                         (cx - 4, cy + 11, 8, 1))
        # Center buckle with star
        _NS_zarethyr._draw_star_4point(surface, cx, cy + 12, 2,
                                       _NS_zarethyr.PALETTE["cosmic_hot"])
    # ---------- EPAULETTES (gold shoulder ornaments with stars) ----------
    def _draw_epaulettes(surface, cx, cy, facing, phase):
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for side in (-1, 1):
            sx = cx + side * 12
            sy = cy
            # Base pauldron (gold)
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["shadow_deep"], [
                (sx - 6 + 2, sy - 3 + 2), (sx + 7 + 2, sy - 3 + 2),
                (sx + 8 + 2, sy + 4 + 2), (sx - 7 + 2, sy + 4 + 2),
            ])
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gold_darkest"], [
                (sx - 6, sy - 3), (sx + 7, sy - 3),
                (sx + 8, sy + 4), (sx - 7, sy + 4),
            ])
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gold_dark"], [
                (sx - 5, sy - 2), (sx + 6, sy - 2),
                (sx + 7, sy + 3), (sx - 6, sy + 3),
            ])
            _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gold_mid"], [
                (sx - 3, sy - 1), (sx + 4, sy - 1),
                (sx + 5, sy + 2), (sx - 4, sy + 2),
            ])
            pygame.draw.line(surface, _NS_zarethyr.PALETTE["gold_light"],
                             (sx - 2, sy), (sx - 2, sy + 2), 1)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_shine"],
                             (sx - 1, sy, 1, 1))
            # STAR ORNAMENT on top of pauldron
            _NS_zarethyr._draw_star_4point(surface, sx, sy - 4, 3,
                                           _NS_zarethyr.PALETTE["cosmic_light"],
                                           alpha=int(200 * pulse))
            _NS_zarethyr._draw_star_4point(surface, sx, sy - 4, 2,
                                           _NS_zarethyr.PALETTE["cosmic_hot"],
                                           alpha=int(240 * pulse))
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (sx, sy - 4, 1, 1))
            # Hanging chain from pauldron
            for chain_y in (sy + 5, sy + 8):
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_dark"],
                                 (sx + side * 3, chain_y, 1, 1))
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_mid"],
                                 (sx + side * 3, chain_y, 1, 1))
    # ---------- ARMS ----------
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        for side in (-1, 1):
            base_x = cx + side * 11
            base_y = cy - 4
            is_dominant = (side * facing > 0)
            if action == "attack" and is_dominant:
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    # Raise hand for cast
                    elbow_offset_x = int(-2 * facing)
                    elbow_offset_y = int(2 - t * 5)
                    hand_offset_x = int(-1 * facing)
                    hand_offset_y = int(-3 - t * 4)
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    # Extend forward (cast!)
                    elbow_offset_x = int((-2 + t * 9) * facing)
                    elbow_offset_y = int(-3)
                    hand_offset_x = int((-1 + t * 18) * facing)
                    hand_offset_y = int(-7 + t * 5)
                else:
                    t = (attack_progress - 0.6) / 0.4
                    # Retract
                    elbow_offset_x = int((7 - t * 3) * facing)
                    elbow_offset_y = int(-3 + t)
                    hand_offset_x = int((17 - t * 5) * facing)
                    hand_offset_y = int(-2 + t * 2)
            else:
                # Idle: dominant hand extended (casting stance)
                swing = math.sin(phase * 0.6 + side) * 0.15
                if is_dominant:
                    elbow_offset_x = int(4 * facing + math.sin(swing) * 1)
                    elbow_offset_y = -1
                    hand_offset_x = int(13 * facing)
                    hand_offset_y = -4
                else:
                    # Non-dominant hand rests at side
                    elbow_offset_x = int(math.sin(swing) * 2 * side)
                    elbow_offset_y = 4
                    hand_offset_x = int(math.sin(swing * 1.5) * 3 * side + side * 2)
                    hand_offset_y = 10
            elbow_x = base_x + elbow_offset_x
            elbow_y = base_y + elbow_offset_y
            hand_x = base_x + hand_offset_x
            hand_y = base_y + hand_offset_y
            # Upper arm — dark robe sleeve (wide)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["shadow_deep"],
                                 (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 6)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["robe_darkest"],
                                 (base_x, base_y), (elbow_x, elbow_y), 5)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["robe_dark"],
                                 (base_x, base_y), (elbow_x, elbow_y), 3)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["robe_mid"],
                                 (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)
            # Elbow cuff (gold band)
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["gold_dark"],
                                   (elbow_x, elbow_y), 3)
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["gold_mid"],
                                   (elbow_x, elbow_y), 2)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gold_shine"],
                             (elbow_x, elbow_y, 1, 1))
            # Forearm — flared sleeve (wider than upper)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["shadow_deep"],
                                 (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 7)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["robe_darkest"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 6)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["robe_dark"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 4)
            _NS_zarethyr._aaline(surface, _NS_zarethyr.PALETTE["robe_mid"],
                                 (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
            # Silver inner cuff at wrist
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["silver_dark"],
                                   (hand_x - int(facing), hand_y), 3)
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["silver_mid"],
                                   (hand_x - int(facing), hand_y), 2)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["silver_light"],
                             (hand_x - int(facing), hand_y, 1, 1))
            # Gold trim on cuff
            pygame.draw.line(surface, _NS_zarethyr.PALETTE["gold_mid"],
                             (hand_x - int(facing * 2), hand_y - 2),
                             (hand_x - int(facing * 2), hand_y + 2), 1)
            # Hand (elegant, skin)
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 3)
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 2)
            _NS_zarethyr._aacircle(surface, _NS_zarethyr.PALETTE["skin_mid"],
                                   (hand_x, hand_y), 1)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["skin_light"],
                             (hand_x, hand_y, 1, 1))
            if is_dominant:
                _NS_zarethyr._cast_hand_pos = (hand_x, hand_y)
    # ---------- HEAD ----------
    def _draw_head(surface, cx, cy, facing, phase):
        # Face — handsome male features
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
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["skin_dark"], face_pts)
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["skin_mid"], [
            (cx - 5, cy - 2), (cx - 6, cy + 1),
            (cx - 5, cy + 4), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 4),
            (cx + 6, cy + 1), (cx + 5, cy - 2),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["skin_light"], [
            (cx - 3, cy - 1), (cx - 4, cy + 1),
            (cx - 3, cy + 3), (cx - 1, cy + 6),
            (cx + 1, cy + 6), (cx + 3, cy + 3),
            (cx + 4, cy + 1), (cx + 3, cy - 1),
            (cx + 2, cy - 5), (cx - 2, cy - 5),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["skin_shine"],
                         (cx - 2 * facing, cy, 1, 1))
        # EYES — bright celestial blue
        eye_pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 1
            # Socket
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["shadow_deep"], (ex - 1, ey, 2, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_zarethyr._alpha(120 * (3 - r) / 3 * eye_pulse)
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # LIPS (subtle male line)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["skin_dark"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
        # Navy blue hair
        _NS_zarethyr._draw_hair(surface, cx, cy, facing, phase)
        # FOREHEAD GEM (blue crystal — signature!)
        _NS_zarethyr._draw_forehead_gem(surface, cx, cy - 5, phase)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Dark navy hair with silver highlights, swept back."""
        sway = math.sin(phase * 0.4) * 1
        # Top/back of head hair
        hair_pts = [
            (cx - 6, cy - 5),
            (cx - 7, cy - 2),
            (cx - 8, cy + 3 + int(sway * 0.5)),
            (cx - 6, cy + 7 + int(sway)),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 6, cy + 7 + int(sway)),
            (cx + 8, cy + 3 + int(sway * 0.5)),
            (cx + 7, cy - 2),
            (cx + 6, cy - 5),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["hair_darkest"], hair_pts)
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["hair_dark"], [
            (cx - 5, cy - 5), (cx - 6, cy - 2),
            (cx - 7, cy + 3 + int(sway * 0.5)),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 7, cy + 3 + int(sway * 0.5)),
            (cx + 6, cy - 2),
            (cx + 5, cy - 5),
            (cx + 4, cy - 7), (cx - 4, cy - 7),
        ])
        # Front bangs (swept sides)
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["hair_darkest"], [
            (cx - 5, cy - 7), (cx - 6, cy - 3),
            (cx - 4, cy - 4), (cx - 2, cy - 5),
            (cx + 2, cy - 5), (cx + 4, cy - 4),
            (cx + 6, cy - 3), (cx + 5, cy - 7),
        ])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["hair_dark"], [
            (cx - 4, cy - 7), (cx - 4, cy - 4),
            (cx - 1, cy - 5), (cx + 1, cy - 5),
            (cx + 4, cy - 4), (cx + 4, cy - 7),
        ])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["hair_mid"], [
            (cx - 3, cy - 6), (cx - 2, cy - 4),
            (cx + 2, cy - 4), (cx + 3, cy - 6),
        ])
        # SILVER HIGHLIGHT streaks (signature)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["hair_light"],
                         (cx - 3, cy - 6), (cx - 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["hair_light"],
                         (cx + 3, cy - 6), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["hair_shine"],
                         (cx - 1, cy - 7), (cx - 1, cy - 5), 1)
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["hair_shine"],
                         (cx, cy - 7, 1, 1))
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["hair_shine"],
                         (cx + 2, cy - 7, 1, 1))
        # Side strands
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["hair_light"],
                         (cx - 7, cy - 1), (cx - 8, cy + 3), 1)
        pygame.draw.line(surface, _NS_zarethyr.PALETTE["hair_light"],
                         (cx + 7, cy - 1), (cx + 8, cy + 3), 1)
    def _draw_forehead_gem(surface, cx, cy, phase):
        """Blue crystal gem on forehead (signature feature)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Halo
        for r in range(5, 0, -1):
            alpha = _NS_zarethyr._alpha(150 * (5 - r) / 5 * pulse)
            _NS_zarethyr._aacircle(surface,
                                   (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                   (cx, cy), r)
        # Diamond gem
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gem_dark"], [
            (cx, cy - 2), (cx + 1, cy),
            (cx, cy + 2), (cx - 1, cy),
        ])
        _NS_zarethyr._poly(surface, _NS_zarethyr.PALETTE["gem_mid"], [
            (cx, cy - 1), (cx + 1, cy),
            (cx, cy + 1), (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["gem_hot"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (cx, cy, 1, 1))
    # ---------- ORBITING STARS ----------
    def _draw_orbiting_stars(surface, cx, cy, phase):
        """Constellation stars orbiting body (TRUE BOSS signature)."""
        for i in range(5):
            orbit_ang = phase * 0.6 + i * math.pi * 2 / 5
            orbit_r = 34 + int(math.sin(phase + i) * 5)
            sx = cx + int(math.cos(orbit_ang) * orbit_r)
            sy = cy - 5 + int(math.sin(orbit_ang) * orbit_r * 0.5)
            twinkle = math.sin(phase * 3 + i * 1.3) * 0.5 + 0.5
            size = int(2 + twinkle * 2)
            # Star glow halo
            for r in range(size + 2, 0, -1):
                alpha = _NS_zarethyr._alpha(80 * (size + 2 - r) / (size + 2))
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                       (sx, sy), r)
            # 4-point star
            _NS_zarethyr._draw_star_4point(surface, sx, sy, size,
                                           _NS_zarethyr.PALETTE["cosmic_hot"])
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (sx, sy, 1, 1))
    # ---------- HAND LIGHT ORB ----------
    def _draw_hand_light(surface, cx, cy, facing, phase, action, attack_progress):
        hand_pos = getattr(_NS_zarethyr, "_cast_hand_pos", None)
        if hand_pos is None:
            return
        hx, hy = hand_pos
        # Don't show during middle of cast (it becomes projectile)
        if action == "attack" and 0.3 < attack_progress < 0.75:
            return
        orb_pulse = math.sin(phase * 2) * 0.3 + 0.7
        orb_x = hx + facing * 3
        orb_y = hy - 1
        # Halo
        for r in range(7, 0, -1):
            alpha = _NS_zarethyr._alpha(110 * (7 - r) / 7 * orb_pulse)
            _NS_zarethyr._aacircle(surface,
                                   (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                   (orb_x, orb_y), r)
        # Core star
        _NS_zarethyr._draw_star_4point(surface, orb_x, orb_y, 4,
                                       _NS_zarethyr.PALETTE["cosmic_mid"])
        _NS_zarethyr._draw_star_4point(surface, orb_x, orb_y, 3,
                                       _NS_zarethyr.PALETTE["cosmic_hot"])
        _NS_zarethyr._draw_star_4point(surface, orb_x, orb_y, 2,
                                       _NS_zarethyr.PALETTE["cosmic_shine"])
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (orb_x, orb_y, 1, 1))
        # Sparkles around
        for i in range(4):
            spark_ang = phase * 3 + i * math.pi / 2
            spark_r = 6
            sx = orb_x + int(math.cos(spark_ang) * spark_r)
            sy = orb_y + int(math.sin(spark_ang) * spark_r)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["cosmic_hot"], (sx, sy, 1, 1))
    # ============================================================
    # BASIC ATTACK: Small cosmic bolt
    # ============================================================
    def _draw_starlight_bolt(surface, boss, x, y, progress):
        if progress < 0.3 or progress > 0.85:
            return
        facing = boss.direction
        tx, ty = _NS_zarethyr._target_position(boss, x, y)
        hand_pos = getattr(_NS_zarethyr, "_cast_hand_pos", None)
        if hand_pos:
            start_x, start_y = hand_pos[0] + facing * 3, hand_pos[1]
        else:
            start_x = x + facing * 20
            start_y = y - 4
        t = (progress - 0.3) / 0.55
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail (long comet)
        for i in range(6):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_zarethyr._alpha(220 - i * 32)
            _NS_zarethyr._aacircle(surface,
                                   (*_NS_zarethyr.PALETTE["cosmic_dark"], alpha),
                                   (px, py), max(1, 6 - i))
            _NS_zarethyr._aacircle(surface,
                                   (*_NS_zarethyr.PALETTE["cosmic_mid"], alpha),
                                   (px, py), max(1, 4 - i))
            pygame.draw.rect(surface,
                             (*_NS_zarethyr.PALETTE["cosmic_hot"], alpha),
                             (px, py, 1, 1))
        # Main bolt
        for r in range(10, 0, -1):
            alpha = _NS_zarethyr._alpha(100 * (10 - r) / 10)
            _NS_zarethyr._aacircle(surface,
                                   (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                   (bx, by), r)
        _NS_zarethyr._draw_star_4point(surface, bx, by, 5,
                                       _NS_zarethyr.PALETTE["cosmic_dark"])
        _NS_zarethyr._draw_star_4point(surface, bx, by, 4,
                                       _NS_zarethyr.PALETTE["cosmic_mid"])
        _NS_zarethyr._draw_star_4point(surface, bx, by, 3,
                                       _NS_zarethyr.PALETTE["cosmic_hot"])
        _NS_zarethyr._draw_star_4point(surface, bx, by, 2,
                                       _NS_zarethyr.PALETTE["cosmic_shine"])
        pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (bx, by, 1, 1))
    # ============================================================
    # AMBIENT / GROUND (TRUE BOSS scale)
    # ============================================================
    def _draw_hover_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, int((15 - radius) * 15 * pulse))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 3, 8, 170), (5, 9, 140, 12))
        pygame.draw.ellipse(shadow, (20, 30, 70, 110), (15, 11, 120, 8))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_cosmic_plume(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Cosmic starlight plumes beneath character."""
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Blue mist
        mist = pygame.Surface((160, 45), pygame.SRCALPHA)
        for radius in range(35, 3, -3):
            alpha = _NS_zarethyr._alpha((35 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zarethyr.PALETTE["cosmic_dark"], alpha),
                    (80 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2))
                )
        for radius in range(22, 3, -2):
            alpha = _NS_zarethyr._alpha((22 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zarethyr.PALETTE["cosmic_mid"], alpha),
                    (80 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 80, cy - 8))
        # Rising star particles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = _NS_zarethyr._alpha(240 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_zarethyr._draw_star_4point(surface, sx, sy, 2,
                                           _NS_zarethyr.PALETTE["cosmic_hot"],
                                           alpha=alpha)
            pygame.draw.rect(surface, (*_NS_zarethyr.PALETTE["white"], alpha),
                             (sx, sy, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_zarethyr._alpha(180 - i * 28)
                if alpha <= 0:
                    continue
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_dark"], alpha),
                                       (sx, sy), max(2, 7 - i))
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_mid"], alpha),
                                       (sx, sy), max(1, 5 - i))
                _NS_zarethyr._draw_star_4point(surface, sx, sy, 2,
                                               _NS_zarethyr.PALETTE["cosmic_light"],
                                               alpha=alpha)
    def _draw_cosmic_aura(surface, x, y, phase, is_ultimate=False):
        """TRUE BOSS massive cosmic aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        max_r = 110 if is_ultimate else 90
        for radius in range(max_r, 5, -5):
            alpha = _NS_zarethyr._alpha((max_r - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zarethyr._aacircle(aura,
                                       (*_NS_zarethyr.PALETTE["cosmic_darkest"], alpha),
                                       (120, 105), radius)
        for radius in range(int(max_r * 0.7), 5, -4):
            alpha = _NS_zarethyr._alpha((int(max_r * 0.7) - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_zarethyr._aacircle(aura,
                                       (*_NS_zarethyr.PALETTE["cosmic_dark"], alpha),
                                       (120, 105), radius)
        for radius in range(int(max_r * 0.4), 5, -3):
            alpha = _NS_zarethyr._alpha((int(max_r * 0.4) - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_zarethyr._aacircle(aura,
                                       (*_NS_zarethyr.PALETTE["cosmic_mid"], alpha),
                                       (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # BACKGROUND STARS scattered
        for i in range(20):
            angle = phase * 0.2 + i * math.pi / 10
            r = 50 + (i * 7) % 40
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.4)
            twinkle = math.sin(phase * 2 + i * 1.5) * 0.5 + 0.5
            if twinkle > 0.5:
                _NS_zarethyr._draw_star_4point(surface, sx, sy, 1,
                                               _NS_zarethyr.PALETTE["cosmic_hot"],
                                               alpha=int(200 * twinkle))
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"],
                                 (sx, sy, 1, 1))
    def _draw_constellation_ring(surface, x, y, phase, skill):
        """Big constellation-styled ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zarethyr.PALETTE["cosmic_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_zarethyr.PALETTE["cosmic_dark"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_zarethyr.PALETTE["cosmic_mid"], 230),
                            (25, 24, 140, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_zarethyr.PALETTE["cosmic_light"],
                                   _NS_zarethyr._alpha(180 * pulse)),
                            (40, 26, 110, 18), 1)
        # Constellation connect-lines (star nodes with lines between)
        star_positions = []
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            sx = 95 + int(math.cos(angle) * 60)
            sy = 34 + int(math.sin(angle) * 12)
            star_positions.append((sx, sy))
        # Draw connection lines between adjacent stars
        for i in range(len(star_positions)):
            p1 = star_positions[i]
            p2 = star_positions[(i + 1) % len(star_positions)]
            pygame.draw.line(ring, (*_NS_zarethyr.PALETTE["cosmic_light"], 180),
                             p1, p2, 1)
        # Draw stars at nodes
        for pos in star_positions:
            _NS_zarethyr._draw_star_4point(ring, pos[0], pos[1], 2,
                                           _NS_zarethyr.PALETTE["cosmic_hot"])
            pygame.draw.rect(ring, _NS_zarethyr.PALETTE["white"], (pos[0], pos[1], 1, 1))
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_zarethyr.PALETTE["cosmic_shine"],
                                 _NS_zarethyr._alpha(150 * pulse)),
                                (15, 15, 160, 40), 1)
        surface.blit(ring, (x - 95, y - 30))
    # ============================================================
    # SKILL Q: INFINITE EXTENSION (long piercing light beam)
    # ============================================================
    def _draw_infinite_extension(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zarethyr._target_position(boss, x, y)
        hand_pos = getattr(_NS_zarethyr, "_cast_hand_pos", None)
        if hand_pos:
            start_x, start_y = hand_pos[0] + facing * 3, hand_pos[1]
        else:
            start_x = x + facing * 22
            start_y = y - 4
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_zarethyr._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                       (start_x, start_y), r)
            _NS_zarethyr._draw_star_4point(surface, start_x, start_y, cr,
                                           _NS_zarethyr.PALETTE["cosmic_hot"])
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (start_x, start_y, 2, 2))
        elif progress < 0.75:
            # BEAM (long straight piercing light)
            t = (progress - 0.2) / 0.55
            intensity = math.sin(t * math.pi)
            # Extend beyond target for "infinite" feel
            beam_end_x = tx + facing * 60
            beam_end_y = ty
            # Multi-layer beam
            for width, color_key, alpha_base in [
                (14, "cosmic_darkest", 100),
                (10, "cosmic_dark", 140),
                (6, "cosmic_mid", 180),
                (4, "cosmic_light", 220),
                (2, "cosmic_hot", 245),
                (1, "cosmic_shine", 255),
            ]:
                actual_alpha = _NS_zarethyr._alpha(alpha_base * intensity)
                _NS_zarethyr._aaline(surface,
                                     (*_NS_zarethyr.PALETTE[color_key], actual_alpha),
                                     (start_x, start_y), (beam_end_x, beam_end_y), width)
            # Sparkles along beam
            beam_len = math.hypot(beam_end_x - start_x, beam_end_y - start_y)
            steps = max(6, int(beam_len / 15))
            for i in range(steps):
                st = i / steps + (phase * 0.5) % (1 / steps)
                sx = int(start_x + (beam_end_x - start_x) * st)
                sy = int(start_y + (beam_end_y - start_y) * st)
                offset = math.sin(phase * 4 + i) * 3
                perp_ang = math.atan2(beam_end_y - start_y, beam_end_x - start_x) + math.pi / 2
                sx += int(math.cos(perp_ang) * offset)
                sy += int(math.sin(perp_ang) * offset)
                _NS_zarethyr._draw_star_4point(surface, sx, sy, 2,
                                               _NS_zarethyr.PALETTE["cosmic_hot"],
                                               alpha=int(240 * intensity))
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (sx, sy, 1, 1))
            # Impact star burst at target
            burst_r = int(10 + t * 15)
            burst_alpha = _NS_zarethyr._alpha(240 * intensity)
            for r in range(burst_r + 4, 0, -2):
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_light"],
                                        _NS_zarethyr._alpha(burst_alpha * (burst_r + 4 - r) / (burst_r + 4))),
                                       (tx, ty), r)
            _NS_zarethyr._draw_star_4point(surface, tx, ty, burst_r,
                                           _NS_zarethyr.PALETTE["cosmic_shine"],
                                           alpha=burst_alpha)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (tx, ty, 2, 2))
        else:
            # Fade
            t = (progress - 0.75) / 0.25
            alpha = _NS_zarethyr._alpha(180 * (1 - t))
            _NS_zarethyr._aaline(surface,
                                 (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                 (start_x, start_y), (tx, ty), 2)
    # ============================================================
    # SKILL W: STARDUST (AoE delayed explosion)
    # ============================================================
    def _draw_stardust_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_zarethyr._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Warning circle grows, then explosion
        if progress < 0.55:
            # Warning
            t = progress / 0.55
            r = int(50 * t)
            alpha = _NS_zarethyr._alpha(220 * t)
            pygame.draw.ellipse(surface, (*_NS_zarethyr.PALETTE["cosmic_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_zarethyr.PALETTE["cosmic_mid"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6), 2)
            pygame.draw.ellipse(surface, (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                (tx - r + 12, ty - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12), 1)
            # Runes around circle
            for i in range(6):
                ang = i * math.pi / 3 + phase * 0.3
                rx = tx + int(math.cos(ang) * r)
                ry = ty + int(math.sin(ang) * r * 0.4)
                _NS_zarethyr._draw_star_4point(surface, rx, ry, 2,
                                               _NS_zarethyr.PALETTE["cosmic_hot"])
        else:
            # After explosion — residual glow
            t = (progress - 0.55) / 0.45
            r = int(50 + t * 10)
            alpha = _NS_zarethyr._alpha(200 * (1 - t))
            pygame.draw.ellipse(surface, (*_NS_zarethyr.PALETTE["cosmic_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_zarethyr.PALETTE["cosmic_mid"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
    def _draw_stardust_fg(surface, boss, x, y, timer, phase):
        """Explosion of stars when timer expires."""
        tx, ty = _NS_zarethyr._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.55:
            # Gathering stars in center (pre-explosion)
            t = progress / 0.55
            gather_r = int(6 + t * 8)
            for r in range(gather_r + 4, 0, -1):
                alpha = _NS_zarethyr._alpha(180 * (gather_r + 4 - r) / (gather_r + 4))
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                       (tx, ty - 5), r)
            _NS_zarethyr._draw_star_4point(surface, tx, ty - 5, gather_r,
                                           _NS_zarethyr.PALETTE["cosmic_hot"])
        elif progress < 0.75:
            # EXPLOSION - burst of stars radially
            t = (progress - 0.55) / 0.2
            burst_r = int(20 + t * 45)
            # Central bright explosion
            core_alpha = _NS_zarethyr._alpha(255 * (1 - t))
            for r in range(30, 0, -3):
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_hot"],
                                        _NS_zarethyr._alpha(core_alpha * (30 - r) / 30)),
                                       (tx, ty), r)
            # Radial stars flying outward
            for i in range(12):
                ang = i * math.pi / 6 + phase * 0.2
                star_r = burst_r
                sx = tx + int(math.cos(ang) * star_r)
                sy = ty + int(math.sin(ang) * star_r)
                _NS_zarethyr._draw_star_4point(surface, sx, sy, 4,
                                               _NS_zarethyr.PALETTE["cosmic_light"],
                                               alpha=core_alpha)
                _NS_zarethyr._draw_star_4point(surface, sx, sy, 2,
                                               _NS_zarethyr.PALETTE["cosmic_hot"],
                                               alpha=core_alpha)
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (sx, sy, 1, 1))
                # Trail line from center to star
                pygame.draw.line(surface,
                                 (*_NS_zarethyr.PALETTE["cosmic_mid"], core_alpha),
                                 (tx, ty), (sx, sy), 1)
        else:
            # Aftermath - lingering star sparkles
            t = (progress - 0.75) / 0.25
            for i in range(10):
                sparkle_t = (phase * 0.5 + i * 0.1) % 1.0
                sx = tx + int(math.sin(phase + i) * 40)
                sy = ty - int(sparkle_t * 20)
                alpha = _NS_zarethyr._alpha(200 * (1 - t) * (1 - sparkle_t))
                if alpha > 0:
                    _NS_zarethyr._draw_star_4point(surface, sx, sy, 2,
                                                   _NS_zarethyr.PALETTE["cosmic_hot"],
                                                   alpha=alpha)
    # ============================================================
    # SKILL E: REALITY SHOCK (3 sequential light waves)
    # ============================================================
    def _draw_reality_shock(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zarethyr._target_position(boss, x, y)
        hand_pos = getattr(_NS_zarethyr, "_cast_hand_pos", None)
        if hand_pos:
            start_x, start_y = hand_pos[0] + facing * 3, hand_pos[1]
        else:
            start_x = x + facing * 22
            start_y = y - 4
        # 3 waves fired sequentially
        for wave_i in range(3):
            wave_delay = wave_i * 0.18
            wave_progress = max(0.0, progress - wave_delay)
            if wave_progress <= 0 or wave_progress > 0.6:
                continue
            wave_t = wave_progress / 0.6
            # Beam travels from start to target
            wave_end_x = int(start_x + (tx - start_x) * wave_t)
            wave_end_y = int(start_y + (ty - start_y) * wave_t)
            # Beam width varies per wave (thicker each subsequent wave)
            beam_width = 3 + wave_i * 2
            # Fade out toward end
            wave_alpha = _NS_zarethyr._alpha(240 * (1 - wave_t * 0.5))
            # Multi-layer beam (crescent/spear-like wave)
            for width_mult, color_key in [
                (2.5, "cosmic_darkest"),
                (2.0, "cosmic_dark"),
                (1.5, "cosmic_mid"),
                (1.0, "cosmic_light"),
                (0.5, "cosmic_hot"),
            ]:
                w = max(1, int(beam_width * width_mult))
                _NS_zarethyr._aaline(surface,
                                     (*_NS_zarethyr.PALETTE[color_key], wave_alpha),
                                     (start_x, start_y),
                                     (wave_end_x, wave_end_y), w)
            # Bright head star
            _NS_zarethyr._draw_star_4point(surface, wave_end_x, wave_end_y, 5,
                                           _NS_zarethyr.PALETTE["cosmic_shine"],
                                           alpha=wave_alpha)
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"],
                             (wave_end_x, wave_end_y, 2, 2))
            # Impact stars when reaches target
            if wave_t > 0.9:
                impact_alpha = _NS_zarethyr._alpha(240)
                for r in range(10, 0, -2):
                    _NS_zarethyr._aacircle(surface,
                                           (*_NS_zarethyr.PALETTE["cosmic_light"],
                                            _NS_zarethyr._alpha(impact_alpha * (10 - r) / 10)),
                                           (tx, ty), r + wave_i * 3)
                for i in range(6):
                    ang = i * math.pi / 3 + wave_i * 0.3
                    ex = tx + int(math.cos(ang) * 12)
                    ey = ty + int(math.sin(ang) * 12)
                    _NS_zarethyr._draw_star_4point(surface, ex, ey, 2,
                                                   _NS_zarethyr.PALETTE["cosmic_hot"],
                                                   alpha=impact_alpha)
    # ============================================================
    # SKILL R: DAWN'S TRIUMPH (multiple light pillars from sky)
    # ============================================================
    def _draw_dawn_triumph_ground(surface, boss, x, y, timer, phase):
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big AoE circle around caster
        r = int(90 * min(1.0, progress * 1.5))
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        if r > 3:
            for i, (rad_off, thick, alpha_base) in enumerate([
                (0, 4, 240), (10, 3, 200), (20, 2, 160), (30, 1, 120),
            ]):
                pygame.draw.ellipse(surface,
                                    (*_NS_zarethyr.PALETTE["cosmic_dark"],
                                     _NS_zarethyr._alpha(alpha_base * pulse)),
                                    (x - r + rad_off, y + 55 - (r - rad_off) // 3,
                                     (r - rad_off) * 2, (r - rad_off) * 2 // 3), thick)
            # Star markers around perimeter (where pillars will strike)
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.15
                mx = x + int(math.cos(ang) * r * 0.7)
                my = y + 55 + int(math.sin(ang) * r * 0.28)
                _NS_zarethyr._draw_star_4point(surface, mx, my, 3,
                                               _NS_zarethyr.PALETTE["cosmic_hot"])
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (mx, my, 1, 1))
    def _draw_dawn_triumph_fg(surface, boss, x, y, timer, phase):
        """Multiple light pillars falling from sky."""
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Pillar positions (like art reference - multiple around area)
        pillar_positions = []
        for i in range(6):
            ang = i * math.pi / 3 + math.pi / 6  # offset for variety
            r = 55
            px = x + int(math.cos(ang) * r)
            py = y + 55 + int(math.sin(ang) * r * 0.4)
            pillar_positions.append((px, py, i * 0.08))  # staggered delay
        if progress < 0.15:
            # Wind-up: gathering light above
            t = progress / 0.15
            gather_y = y - int(t * 60)
            for r in range(15, 0, -1):
                alpha = _NS_zarethyr._alpha(200 * (15 - r) / 15)
                _NS_zarethyr._aacircle(surface,
                                       (*_NS_zarethyr.PALETTE["cosmic_light"], alpha),
                                       (x, gather_y), r)
            _NS_zarethyr._draw_star_4point(surface, x, gather_y, 8,
                                           _NS_zarethyr.PALETTE["cosmic_shine"])
            pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"], (x, gather_y, 2, 2))
            return
        # PILLARS FALLING
        for pillar_x, pillar_ground_y, delay in pillar_positions:
            local_progress = max(0.0, (progress - 0.15) / 0.85 - delay)
            if local_progress <= 0:
                continue
            # Each pillar has 3 phases: warning, strike, aftermath
            if local_progress < 0.15:
                # Warning circle at ground
                t = local_progress / 0.15
                r_warn = int(15 * t)
                alpha_warn = _NS_zarethyr._alpha(200 * t)
                pygame.draw.ellipse(surface,
                                    (*_NS_zarethyr.PALETTE["cosmic_light"], alpha_warn),
                                    (pillar_x - r_warn, pillar_ground_y - r_warn // 3,
                                     r_warn * 2, r_warn * 2 // 3), 2)
                # Small star at ground
                _NS_zarethyr._draw_star_4point(surface, pillar_x, pillar_ground_y, 3,
                                               _NS_zarethyr.PALETTE["cosmic_hot"])
            elif local_progress < 0.4:
                # STRIKE - pillar of light falling
                t = (local_progress - 0.15) / 0.25
                intensity = math.sin(t * math.pi)
                # Pillar from top of screen to ground
                pillar_top_y = max(0, pillar_ground_y - 200)
                # Multi-layer pillar
                for width, color_key, alpha_base in [
                    (14, "cosmic_darkest", 100),
                    (10, "cosmic_dark", 150),
                    (6, "cosmic_mid", 200),
                    (3, "cosmic_light", 230),
                    (1, "cosmic_shine", 255),
                ]:
                    actual_alpha = _NS_zarethyr._alpha(alpha_base * intensity)
                    pygame.draw.rect(surface,
                                     (*_NS_zarethyr.PALETTE[color_key], actual_alpha),
                                     (pillar_x - width // 2, pillar_top_y,
                                      width, pillar_ground_y - pillar_top_y))
                # Rising sparkles along pillar
                for i in range(8):
                    sp_t = (phase * 2 + i * 0.13) % 1.0
                    sp_y = pillar_ground_y - int(sp_t * (pillar_ground_y - pillar_top_y))
                    sp_x = pillar_x + int(math.sin(phase * 3 + i) * 4)
                    _NS_zarethyr._draw_star_4point(surface, sp_x, sp_y, 2,
                                                   _NS_zarethyr.PALETTE["cosmic_hot"],
                                                   alpha=int(240 * intensity))
                # BIG impact star at ground
                impact_r = int(12 + t * 20)
                impact_alpha = _NS_zarethyr._alpha(240 * intensity)
                for r in range(impact_r + 4, 0, -2):
                    _NS_zarethyr._aacircle(surface,
                                           (*_NS_zarethyr.PALETTE["cosmic_light"],
                                            _NS_zarethyr._alpha(impact_alpha * (impact_r + 4 - r) / (impact_r + 4))),
                                           (pillar_x, pillar_ground_y), r)
                _NS_zarethyr._draw_star_4point(surface, pillar_x, pillar_ground_y, impact_r,
                                               _NS_zarethyr.PALETTE["cosmic_shine"],
                                               alpha=impact_alpha)
                pygame.draw.rect(surface, _NS_zarethyr.PALETTE["white"],
                                 (pillar_x, pillar_ground_y, 2, 2))
                # Radial ground burst
                for i in range(8):
                    ang = i * math.pi / 4
                    ex = pillar_x + int(math.cos(ang) * impact_r)
                    ey = pillar_ground_y + int(math.sin(ang) * impact_r * 0.6)
                    pygame.draw.line(surface,
                                     (*_NS_zarethyr.PALETTE["cosmic_hot"], impact_alpha),
                                     (pillar_x, pillar_ground_y), (ex, ey), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_zarethyr.PALETTE["white"], impact_alpha),
                                     (ex, ey, 1, 1))
            else:
                # Aftermath - lingering glow
                t = min(1.0, (local_progress - 0.4) / 0.4)
                fade_alpha = _NS_zarethyr._alpha(180 * (1 - t))
                _NS_zarethyr._draw_star_4point(surface, pillar_x, pillar_ground_y, 3,
                                               _NS_zarethyr.PALETTE["cosmic_hot"],
                                               alpha=fade_alpha)
# ============================================================
# AUTO-CONVERT ALL METHODS TO STATICMETHOD
# ============================================================
for _attr_name in list(vars(_NS_zarethyr).keys()):
    _attr = vars(_NS_zarethyr)[_attr_name]
    if callable(_attr) and not _attr_name.startswith('__') \
            and not isinstance(_attr, (staticmethod, classmethod)):
        setattr(_NS_zarethyr, _attr_name, staticmethod(_attr))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kyumirra(surface, boss, x, y):
    """Entry point kyumirra."""
    return _NS_kyumirra.draw_kyumirra(surface, boss, x, y)


def draw_morvakhul(surface, boss, x, y):
    """Entry point morvakhul."""
    return _NS_morvakhul.draw_morvakhul(surface, boss, x, y)


def draw_nyxariel(surface, boss, x, y):
    """Entry point nyxariel."""
    return _NS_nyxariel.draw_nyxariel(surface, boss, x, y)


def draw_zarethyr(surface, boss, x, y):
    """Entry point zarethyr."""
    return _NS_zarethyr.draw_zarethyr(surface, boss, x, y)
