"""
bosses/level46.py - Semua boss Level 46

Berisi:
  - akaroth    (mini boss - MELEE crimson fist, blood brawler)
  - kassadin   (mini boss - RANGED void walker, void blade)
  - shimorakh  (mini boss - RANGED root of shadows, shadow magic)
  - sunakage   (TRUE BOSS - RANGED sand shadow, sand mage)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kas_ (kassadin), _shi_ (shimorakh), _sun_ (sunakage) sudah unik.
  - _aka_ (akaroth) di-rename -> _akr_ (bentrok dengan akashari
    level 7), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# AKAROTH (CRIMSON FIST) - Mini Boss
# ====================================================================

class _NS_akaroth:
    """Namespace akaroth - Crimson Fist demon boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale grey demon)
        "skin_shadow": (140, 130, 145),
        "skin_dark": (185, 175, 190),
        "skin_mid": (215, 205, 215),
        "skin_light": (235, 228, 235),
        "skin_shine": (250, 245, 250),
        # Blue tattoos (mystical demon markings)
        "tat_darkest": (10, 25, 60),
        "tat_dark": (25, 55, 110),
        "tat_mid": (55, 110, 180),
        "tat_light": (110, 170, 230),
        "tat_shine": (180, 220, 255),
        # Pink/magenta hair
        "hair_darkest": (100, 20, 40),
        "hair_dark": (170, 40, 70),
        "hair_mid": (220, 70, 105),
        "hair_light": (245, 130, 155),
        "hair_shine": (255, 190, 210),
        # Pants (grey/beige)
        "pants_darkest": (35, 30, 25),
        "pants_dark": (75, 65, 50),
        "pants_mid": (125, 110, 85),
        "pants_light": (175, 155, 120),
        "pants_shine": (215, 195, 155),
        # Sash (dark red)
        "sash_dark": (60, 15, 20),
        "sash_mid": (130, 35, 45),
        "sash_light": (200, 70, 80),
        # Belt (green/olive)
        "belt_dark": (25, 45, 35),
        "belt_mid": (60, 90, 65),
        "belt_light": (120, 155, 120),
        # Golden yellow eyes (demon)
        "eye_dark": (100, 60, 5),
        "eye_mid": (220, 160, 30),
        "eye_light": (255, 220, 100),
        "eye_shine": (255, 250, 200),
        # Crimson (E, R skills - lotus/pursuit)
        "crimson_darkest": (55, 5, 20),
        "crimson_dark": (140, 15, 40),
        "crimson_mid": (220, 30, 65),
        "crimson_light": (255, 90, 120),
        "crimson_shine": (255, 180, 200),
        # Air blue (Q, W - shockwave/needles)
        "air_darkest": (10, 35, 80),
        "air_dark": (30, 90, 170),
        "air_mid": (80, 160, 230),
        "air_light": (170, 220, 255),
        "air_shine": (240, 250, 255),
        # Absorption purple (D)
        "abs_darkest": (25, 10, 60),
        "abs_dark": (65, 25, 130),
        "abs_mid": (140, 60, 220),
        "abs_light": (200, 130, 255),
        "abs_shine": (240, 210, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_akaroth._clamp(color)
        if _NS_akaroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_akaroth._clamp(color)
        if _NS_akaroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_akaroth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_akaroth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_akaroth._detect_moving(boss)
        _NS_akaroth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_akr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_akaroth._draw_crimson_aura(surface, x, y, pulse)
        _NS_akaroth._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_akaroth._draw_lotus_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akaroth._draw_pursuit_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_akaroth._draw_absorption_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Handle special body positions for skills
        body_x_offset = 0
        body_y_offset = 0
        show_body = True
        if active_skill == "e":
            duration = 75
            e_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if e_prog < 0.4:
                # Leap up
                t = e_prog / 0.4
                body_y_offset = -int(math.sin(t * math.pi) * 40)
            elif e_prog < 0.55:
                # Falling
                t = (e_prog - 0.4) / 0.15
                body_y_offset = -int((1 - t) * 20)
        if active_skill == "r":
            duration = 90
            r_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if 0.2 < r_prog < 0.8:
                # Dash motion (body moves toward target)
                dash_t = (r_prog - 0.2) / 0.6
                tx, ty = _NS_akaroth._target_position(boss, x, y)
                body_x_offset = int((tx - x - boss.direction * 40) * dash_t)
        # Body
        if show_body:
            actual_x = x + body_x_offset
            actual_y = y + body_y_offset + float_bob
            if attacking:
                _NS_akaroth._draw_body_attack(surface, boss, actual_x, actual_y)
            elif moving:
                _NS_akaroth._draw_body_walk(surface, boss, actual_x, actual_y)
            else:
                _NS_akaroth._draw_body_idle(surface, boss, actual_x, actual_y)
        # D - Absorption effect (over body)
        if active_skill == "d":
            _NS_akaroth._draw_absorption_aura(surface, boss, x, y + float_bob,
                                              skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_akaroth._draw_shockwave_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_akaroth._draw_needles_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_akaroth._draw_lotus_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akaroth._draw_pursuit_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_akr_previous_timer", 0))
        active = bool(getattr(boss, "_akr_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._akr_attack_active = True
            boss._akr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._akr_attack_frame = int(getattr(boss, "_akr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._akr_attack_active = False
            boss._akr_attack_frame = 0
            active = False
        boss._akr_previous_timer = timer
        boss._akr_attack_progress = (
            min(1.0, getattr(boss, "_akr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_akr_last_x"):
            boss._akr_last_x = boss.x
            boss._akr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._akr_last_x)
        dy = abs(boss.y - boss._akr_last_y)
        boss._akr_last_x = boss.x
        boss._akr_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_akaroth._draw_shadow(surface, x, y + 50)
        _NS_akaroth._draw_crimson_mist(surface, x, y + 44, boss.pulse)
        _NS_akaroth._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_akaroth._draw_shadow(surface, x + sway, y + 50)
        _NS_akaroth._draw_crimson_mist(surface, x + sway, y + 44, phase, trail=True,
                                       facing=boss.direction)
        _NS_akaroth._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_akr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Punch motion (melee)
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 14)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(10 * (1 - t)) * boss.direction
        _NS_akaroth._draw_shadow(surface, x + lunge, y + 50)
        _NS_akaroth._draw_crimson_mist(surface, x + lunge, y + 44, boss.pulse,
                                       intense=True)
        _NS_akaroth._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_akaroth._draw_punch_impact(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw shirtless demon: pants, sash, tattooed body, spiky hair."""
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                arm_swing = -int(attack_progress / 0.35 * 12) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_swing = int((-12 + t * 30)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_swing = int(18 * (1 - t)) * facing
        # Order: back arm → body/torso → pants → front arm → head
        # Back arm (relaxed)
        _NS_akaroth._draw_arm(surface, cx - facing * 9, cy - 4, facing, phase,
                              -arm_swing // 2, back=True)
        # Torso (shirtless with tattoos)
        _NS_akaroth._draw_torso(surface, cx, cy, facing, phase, action)
        # Pants
        _NS_akaroth._draw_pants(surface, cx, cy, facing, phase)
        # Front arm (punching)
        _NS_akaroth._draw_arm(surface, cx + facing * 6, cy - 4, facing, phase,
                              arm_swing, back=False, action=action,
                              attack_progress=attack_progress)
        # Head
        _NS_akaroth._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Shirtless muscular torso with blue tattoo stripes."""
        # Torso shape (muscular, wider shoulders)
        torso_shape = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 4),
            (cx - 13, cy + 4),
            (cx - 11, cy + 14),
            (cx - 8, cy + 20),
            (cx + 8, cy + 20),
            (cx + 11, cy + 14),
            (cx + 13, cy + 4),
            (cx + 14, cy - 4),
            (cx + 12, cy - 8),
        ]
        # Shadow
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in torso_shape])
        # Base skin (dark)
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_shadow"], torso_shape)
        # Mid tone
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_dark"], [
            (cx - 11, cy - 7),
            (cx - 13, cy - 3),
            (cx - 12, cy + 4),
            (cx - 10, cy + 13),
            (cx - 7, cy + 19),
            (cx + 7, cy + 19),
            (cx + 10, cy + 13),
            (cx + 12, cy + 4),
            (cx + 13, cy - 3),
            (cx + 11, cy - 7),
        ])
        # Highlight mid (chest/abs)
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_mid"], [
            (cx - 8, cy - 4),
            (cx - 10, cy + 2),
            (cx - 8, cy + 12),
            (cx - 4, cy + 17),
            (cx + 4, cy + 17),
            (cx + 8, cy + 12),
            (cx + 10, cy + 2),
            (cx + 8, cy - 4),
        ])
        # Bright chest highlight
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_light"], [
            (cx - 4, cy - 3),
            (cx - 6, cy + 4),
            (cx - 4, cy + 8),
            (cx + 4, cy + 8),
            (cx + 6, cy + 4),
            (cx + 4, cy - 3),
        ])
        # Shine spot on chest
        pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shine"],
                         (cx - 2, cy + 2), (cx - 2, cy + 6), 1)
        # MUSCLE DEFINITION LINES (abs, chest line)
        # Center vertical line (sternum)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shadow"],
                         (cx, cy - 3), (cx, cy + 14), 1)
        # Pectoral separation
        pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shadow"],
                         (cx - 6, cy + 2), (cx - 1, cy + 4), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shadow"],
                         (cx + 6, cy + 2), (cx + 1, cy + 4), 1)
        # Ab lines (horizontal)
        for y_off in (6, 10, 14):
            pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shadow"],
                             (cx - 5, cy + y_off), (cx - 1, cy + y_off), 1)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shadow"],
                             (cx + 1, cy + y_off), (cx + 5, cy + y_off), 1)
        # BLUE TATTOO STRIPES (crossing across chest/arms - signature markings)
        # Horizontal stripes across chest
        for y_off in (-3, 2, 7, 12):
            # Left side stripe
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["tat_darkest"], [
                (cx - 13, cy + y_off),
                (cx - 13, cy + y_off + 2),
                (cx - 1, cy + y_off + 2),
                (cx - 1, cy + y_off),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["tat_dark"], [
                (cx - 12, cy + y_off),
                (cx - 12, cy + y_off + 2),
                (cx - 2, cy + y_off + 2),
                (cx - 2, cy + y_off),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["tat_mid"], [
                (cx - 12, cy + y_off + 1),
                (cx - 2, cy + y_off + 1),
                (cx - 2, cy + y_off + 1),
                (cx - 12, cy + y_off + 1),
            ])
            # Right side stripe
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["tat_darkest"], [
                (cx + 1, cy + y_off),
                (cx + 1, cy + y_off + 2),
                (cx + 13, cy + y_off + 2),
                (cx + 13, cy + y_off),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["tat_dark"], [
                (cx + 2, cy + y_off),
                (cx + 2, cy + y_off + 2),
                (cx + 12, cy + y_off + 2),
                (cx + 12, cy + y_off),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_light"],
                             (cx - 11, cy + y_off), (cx - 3, cy + y_off), 1)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_light"],
                             (cx + 3, cy + y_off), (cx + 11, cy + y_off), 1)
        # Add glow on tattoos (mystical)
        glow_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for y_off in (-3, 2, 7, 12):
            alpha = _NS_akaroth._alpha(80 * glow_pulse)
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["tat_shine"], alpha),
                             (cx - 10, cy + y_off), (cx - 4, cy + y_off), 1)
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["tat_shine"], alpha),
                             (cx + 4, cy + y_off), (cx + 10, cy + y_off), 1)
        # SASH across chest (dark red diagonal)
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["sash_dark"], [
            (cx - 14, cy - 2),
            (cx - 12, cy + 3),
            (cx + 12, cy + 3),
            (cx + 14, cy - 2),
            (cx + 12, cy - 5),
            (cx - 12, cy - 5),
        ])
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["sash_mid"], [
            (cx - 13, cy - 1),
            (cx - 11, cy + 2),
            (cx + 11, cy + 2),
            (cx + 13, cy - 1),
            (cx + 11, cy - 4),
            (cx - 11, cy - 4),
        ])
        # Sash highlight
        pygame.draw.line(surface, _NS_akaroth.PALETTE["sash_light"],
                         (cx - 10, cy - 3), (cx + 10, cy - 3), 1)
    def _draw_pants(surface, cx, cy, facing, phase):
        """Baggy grey/beige martial arts pants with green belt."""
        # Pants shape (baggy)
        pants_shape = [
            (cx - 10, cy + 18),
            (cx - 12, cy + 24),
            (cx - 13, cy + 30),
            (cx - 10, cy + 34),
            (cx - 3, cy + 34),
            (cx - 2, cy + 28),
            (cx + 2, cy + 28),
            (cx + 3, cy + 34),
            (cx + 10, cy + 34),
            (cx + 13, cy + 30),
            (cx + 12, cy + 24),
            (cx + 10, cy + 18),
        ]
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in pants_shape])
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["pants_darkest"], pants_shape)
        # Mid tone
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["pants_dark"], [
            (cx - 9, cy + 19),
            (cx - 11, cy + 24),
            (cx - 12, cy + 30),
            (cx - 9, cy + 33),
            (cx - 3, cy + 33),
            (cx - 2, cy + 28),
            (cx + 2, cy + 28),
            (cx + 3, cy + 33),
            (cx + 9, cy + 33),
            (cx + 12, cy + 30),
            (cx + 11, cy + 24),
            (cx + 9, cy + 19),
        ])
        # Light tone (folds/highlights)
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["pants_mid"], [
            (cx - 8, cy + 22),
            (cx - 10, cy + 28),
            (cx - 7, cy + 32),
            (cx - 3, cy + 32),
            (cx - 3, cy + 27),
            (cx + 3, cy + 27),
            (cx + 3, cy + 32),
            (cx + 7, cy + 32),
            (cx + 10, cy + 28),
            (cx + 8, cy + 22),
        ])
        # Highlight streaks
        pygame.draw.line(surface, _NS_akaroth.PALETTE["pants_light"],
                         (cx - 6, cy + 22), (cx - 7, cy + 30), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["pants_light"],
                         (cx + 6, cy + 22), (cx + 7, cy + 30), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["pants_shine"],
                         (cx - 6, cy + 25), (cx - 7, cy + 28), 1)
        # GREEN BELT (obi)
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["belt_dark"], [
            (cx - 12, cy + 17),
            (cx - 13, cy + 22),
            (cx + 13, cy + 22),
            (cx + 12, cy + 17),
        ])
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["belt_mid"], [
            (cx - 11, cy + 18),
            (cx - 12, cy + 21),
            (cx + 12, cy + 21),
            (cx + 11, cy + 18),
        ])
        # Belt highlight
        pygame.draw.line(surface, _NS_akaroth.PALETTE["belt_light"],
                         (cx - 10, cy + 19), (cx + 10, cy + 19), 1)
        # Belt knot at front
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["belt_dark"], [
            (cx - 3, cy + 20),
            (cx - 4, cy + 24),
            (cx + 4, cy + 24),
            (cx + 3, cy + 20),
        ])
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["belt_mid"], [
            (cx - 2, cy + 21),
            (cx - 3, cy + 23),
            (cx + 3, cy + 23),
            (cx + 2, cy + 21),
        ])
        # Blue tattoo stripes on legs (matching torso)
        for leg_side in (-1, 1):
            for y_off in (23, 27, 31):
                start_x = cx + leg_side * 4
                end_x = cx + leg_side * 10
                pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                                 (start_x, cy + y_off),
                                 (end_x, cy + y_off), 1)
                pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_mid"],
                                 (start_x, cy + y_off), (end_x, cy + y_off), 1)
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Muscular tattooed arm."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.55
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 12
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 14
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If attacking, extend fist forward for punch
        if action == "attack" and not back and attack_progress > 0.35:
            hand_x = cx + facing * (14 + int(attack_progress * 12))
            hand_y = cy - 2 + int(math.sin(attack_progress * math.pi) * -3)
        thickness = 7 if not back else 6
        # Shadow
        _NS_akaroth._aaline(surface, _NS_akaroth.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm (skin, muscular)
        color_main = _NS_akaroth.PALETTE["skin_shadow"] if back \
            else _NS_akaroth.PALETTE["skin_dark"]
        color_mid = _NS_akaroth.PALETTE["skin_dark"] if back \
            else _NS_akaroth.PALETTE["skin_mid"]
        color_light = _NS_akaroth.PALETTE["skin_light"]
        _NS_akaroth._aaline(surface, color_main,
                            (shoulder_x, shoulder_y),
                            (elbow_x, elbow_y), thickness)
        _NS_akaroth._aaline(surface, color_mid,
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        if not back:
            _NS_akaroth._aaline(surface, color_light,
                                (shoulder_x, shoulder_y - 2),
                                (elbow_x, elbow_y - 2), max(1, thickness - 5))
        # Elbow (small circle)
        _NS_akaroth._aacircle(surface, color_main, (elbow_x, elbow_y), 3)
        _NS_akaroth._aacircle(surface, color_mid, (elbow_x, elbow_y), 2)
        # Forearm
        _NS_akaroth._aaline(surface, _NS_akaroth.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_akaroth._aaline(surface, color_main,
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_akaroth._aaline(surface, color_mid,
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # BLUE TATTOO STRIPES on arm (perpendicular bands)
        # Upper arm bands
        arm_dx = elbow_x - shoulder_x
        arm_dy = elbow_y - shoulder_y
        arm_len = max(1, math.sqrt(arm_dx * arm_dx + arm_dy * arm_dy))
        perp_x = -arm_dy / arm_len
        perp_y = arm_dx / arm_len
        for i in range(3):
            t = (i + 1) / 4
            tx = shoulder_x + arm_dx * t
            ty = shoulder_y + arm_dy * t
            band_w = thickness // 2 + 1
            pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                             (int(tx + perp_x * band_w),
                              int(ty + perp_y * band_w)),
                             (int(tx - perp_x * band_w),
                              int(ty - perp_y * band_w)), 1)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_mid"],
                             (int(tx + perp_x * (band_w - 1)),
                              int(ty + perp_y * (band_w - 1))),
                             (int(tx - perp_x * (band_w - 1)),
                              int(ty - perp_y * (band_w - 1))), 1)
        # Forearm bands
        fore_dx = hand_x - elbow_x
        fore_dy = hand_y - elbow_y
        fore_len = max(1, math.sqrt(fore_dx * fore_dx + fore_dy * fore_dy))
        perp_x = -fore_dy / fore_len
        perp_y = fore_dx / fore_len
        for i in range(3):
            t = (i + 1) / 4
            tx = elbow_x + fore_dx * t
            ty = elbow_y + fore_dy * t
            band_w = (thickness - 1) // 2 + 1
            pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                             (int(tx + perp_x * band_w),
                              int(ty + perp_y * band_w)),
                             (int(tx - perp_x * band_w),
                              int(ty - perp_y * band_w)), 1)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_mid"],
                             (int(tx + perp_x * (band_w - 1)),
                              int(ty + perp_y * (band_w - 1))),
                             (int(tx - perp_x * (band_w - 1)),
                              int(ty - perp_y * (band_w - 1))), 1)
        # FIST (closed hand for punching)
        _NS_akaroth._aacircle(surface, _NS_akaroth.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 5)
        _NS_akaroth._aacircle(surface, color_main, (hand_x, hand_y), 5)
        _NS_akaroth._aacircle(surface, color_mid, (hand_x, hand_y), 4)
        _NS_akaroth._aacircle(surface, color_light, (hand_x - 1, hand_y - 1), 2)
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["skin_shine"],
                         (hand_x - 1, hand_y - 1, 1, 1))
        # Knuckle lines
        pygame.draw.line(surface, _NS_akaroth.PALETTE["skin_shadow"],
                         (hand_x - 2, hand_y), (hand_x + 2, hand_y), 1)
        # Blue tattoo band on wrist
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (hand_x - 3, hand_y + 3), (hand_x + 3, hand_y + 3), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_mid"],
                         (hand_x - 3, hand_y + 3), (hand_x + 3, hand_y + 3), 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Demon head with pink hair, blue tattoos, yellow eyes."""
        # Face shape
        face_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy - 6),
            (cx - 6, cy - 10),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy - 2),
            (cx + 5, cy + 3),
            (cx + 1, cy + 5),
            (cx - 3, cy + 5),
            (cx - 6, cy + 3),
        ]
        # Shadow
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_dark"], [
            (cx - 6, cy - 3),
            (cx - 7, cy - 6),
            (cx - 5, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 9),
            (cx + 7, cy - 6),
            (cx + 6, cy - 3),
            (cx + 4, cy + 2),
            (cx, cy + 4),
            (cx - 4, cy + 2),
        ])
        # Lighter mid
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["skin_shine"],
                         (cx - 3 * facing, cy - 4, 1, 1))
        # BLUE TATTOO STRIPES on face (2 horizontal on each side of face)
        # Left face stripe
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_darkest"],
                         (cx - 7, cy - 3), (cx - 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (cx - 7, cy - 3), (cx - 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_mid"],
                         (cx - 6, cy - 3), (cx - 5, cy - 3), 1)
        # Right face stripe
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_darkest"],
                         (cx + 4, cy - 3), (cx + 7, cy - 3), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (cx + 4, cy - 3), (cx + 7, cy - 3), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_mid"],
                         (cx + 5, cy - 3), (cx + 6, cy - 3), 1)
        # Forehead stripes (2 vertical near hairline)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (cx - 3, cy - 10), (cx - 3, cy - 8), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (cx + 3, cy - 10), (cx + 3, cy - 8), 1)
        # Cheek stripes (below eyes)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (cx - 5, cy), (cx - 3, cy), 1)
        pygame.draw.line(surface, _NS_akaroth.PALETTE["tat_dark"],
                         (cx + 3, cy), (cx + 5, cy), 1)
        # YELLOW DEMON EYES
        _NS_akaroth._draw_eye(surface, cx - 3, cy - 5, facing, phase, action)
        _NS_akaroth._draw_eye(surface, cx + 3, cy - 5, facing, phase, action)
        # Mouth
        if action == "attack":
            # Snarl (open mouth showing fangs)
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["shadow_deep"],
                             (cx - 2, cy + 1, 4, 2))
            pygame.draw.rect(surface, (60, 15, 25),
                             (cx - 1, cy + 1, 3, 2))
            # Fangs
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["skin_shine"],
                             (cx - 1, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["skin_shine"],
                             (cx + 1, cy + 1, 1, 1))
        else:
            # Determined line
            pygame.draw.line(surface, _NS_akaroth.PALETTE["shadow_deep"],
                             (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        # PINK SPIKY HAIR
        _NS_akaroth._draw_hair(surface, cx, cy, facing, phase)
    def _draw_eye(surface, cx, cy, facing, phase, action):
        """Yellow demon eye with black pupil."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Sclera dark
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 3, 2))
        # Yellow iris fills most of eye
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["eye_dark"],
                         (cx - 1, cy, 3, 1))
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["eye_mid"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["eye_light"],
                         (cx + facing, cy, 1, 1))
        # Highlight
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["eye_shine"],
                         (cx, cy, 1, 1))
        # Glow when attacking
        if action == "attack":
            for r in range(4, 0, -1):
                alpha = _NS_akaroth._alpha(100 * (4 - r) / 4 * pulse)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["eye_light"], alpha),
                                      (cx, cy), r)
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["eye_shine"],
                             (cx, cy, 1, 1))
    def _draw_hair(surface, cx, cy, facing, phase):
        """Spiky pink/magenta hair swept back."""
        cy_h = cy - 22  # hair position
        # Back hair base
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["shadow_deep"], [
            (cx - 9, cy_h - 8),
            (cx - 8, cy_h - 13),
            (cx - 3, cy_h - 15),
            (cx + 3, cy_h - 15),
            (cx + 8, cy_h - 13),
            (cx + 9, cy_h - 8),
            (cx + 8, cy_h - 5),
            (cx - 8, cy_h - 5),
        ])
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_darkest"], [
            (cx - 8, cy_h - 8),
            (cx - 7, cy_h - 13),
            (cx - 2, cy_h - 14),
            (cx + 3, cy_h - 14),
            (cx + 7, cy_h - 12),
            (cx + 8, cy_h - 7),
        ])
        # Main dark pink
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_dark"], [
            (cx - 7, cy_h - 9),
            (cx - 6, cy_h - 12),
            (cx - 1, cy_h - 13),
            (cx + 3, cy_h - 13),
            (cx + 6, cy_h - 11),
            (cx + 7, cy_h - 8),
        ])
        # Bright pink mid
        _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_mid"], [
            (cx - 5, cy_h - 10),
            (cx - 3, cy_h - 12),
            (cx + 2, cy_h - 12),
            (cx + 5, cy_h - 10),
            (cx + 4, cy_h - 8),
            (cx - 3, cy_h - 8),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_akaroth.PALETTE["hair_light"],
                         (cx - 2, cy_h - 11), (cx + 2, cy_h - 11), 1)
        pygame.draw.rect(surface, _NS_akaroth.PALETTE["hair_shine"],
                         (cx, cy_h - 12, 1, 1))
        # SPIKY BANGS on forehead (Akaza-style forward-swept)
        for spike_x_off, spike_h in [(-5, -2), (-3, -3), (0, -4), (2, -3), (4, -2)]:
            sx = cx + spike_x_off
            sy = cy_h - 5
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx, sy + spike_h),
                (sx + 2, sy),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_mid"], [
                (sx, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
        # BIG SWEPT-BACK SPIKES (upward-back like Akaza)
        top_sway = math.sin(phase * 0.6) * 1
        for spike_i, (spike_x_off, spike_h, back_off) in enumerate([
            (-6, -6, -4), (-4, -9, -3), (-1, -11, -1), (2, -11, 1),
            (5, -9, 3), (7, -6, 4),
        ]):
            sx = cx + spike_x_off + int(top_sway * (spike_i - 2.5) / 3)
            sy = cy_h - 13
            end_x = sx + back_off
            end_y = sy + spike_h
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (end_x, end_y),
                (sx + 2, sy),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (end_x, end_y + 1),
                (sx + 1, sy),
            ])
            _NS_akaroth._poly(surface, _NS_akaroth.PALETTE["hair_mid"], [
                (sx, sy),
                (end_x, end_y + 1),
                (sx + 1, sy),
            ])
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["hair_light"],
                             (end_x, end_y + 1, 1, 1))
            if spike_i in (2, 3):
                pygame.draw.rect(surface, _NS_akaroth.PALETTE["hair_shine"],
                                 (end_x, end_y + 1, 1, 1))
    # ============================================================
    # BASIC MELEE - Punch impact ripple
    # ============================================================
    def _draw_punch_impact(surface, boss, x, y, progress):
        """Punch impact - shockwave ripple where fist strikes."""
        if progress < 0.5 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.5) / 0.35
        # Impact position (in front of body where fist extends)
        impact_x = x + facing * 30
        impact_y = y - 4
        # Expanding shockwave ring
        r = int(6 + t * 20)
        alpha = _NS_akaroth._alpha(240 * (1 - t))
        _NS_akaroth._aacircle(surface,
                              (*_NS_akaroth.PALETTE["air_darkest"], alpha),
                              (impact_x, impact_y), r + 2, 2)
        _NS_akaroth._aacircle(surface,
                              (*_NS_akaroth.PALETTE["air_dark"], alpha),
                              (impact_x, impact_y), r, 2)
        _NS_akaroth._aacircle(surface,
                              (*_NS_akaroth.PALETTE["air_mid"], alpha),
                              (impact_x, impact_y), max(1, r - 3), 1)
        _NS_akaroth._aacircle(surface,
                              (*_NS_akaroth.PALETTE["air_light"], alpha),
                              (impact_x, impact_y), max(1, r - 6), 1)
        # Center bright flash
        _NS_akaroth._aacircle(surface,
                              (*_NS_akaroth.PALETTE["air_shine"], alpha),
                              (impact_x, impact_y), max(1, 3 - int(t * 3)))
        # Air burst sparks
        for i in range(6):
            angle = i * math.pi / 3
            ex = impact_x + int(math.cos(angle) * (r + 3))
            ey = impact_y + int(math.sin(angle) * (r + 3))
            pygame.draw.rect(surface,
                             (*_NS_akaroth.PALETTE["air_shine"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_akaroth.PALETTE["white"], alpha),
                             (ex, ey, 1, 1))
    # ============================================================
    # FLOATING MIST
    # ============================================================
    def _draw_crimson_mist(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Red/crimson battle aura mist below body."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((130, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(28, 3, -3):
            alpha = _NS_akaroth._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                    (65 - radius, 20 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(18, 2, -2):
            alpha = _NS_akaroth._alpha((18 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                    (65 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 65, cy - 10))
        # Rising crimson particles
        for i in range(6):
            t = (phase * 0.5 + i * 0.15) % 1.0
            px = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            py = cy + 4 - int(t * 22)
            alpha = _NS_akaroth._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                      (px, py), 3)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                      (px, py - 1), 2)
                pygame.draw.rect(surface,
                                 (*_NS_akaroth.PALETTE["crimson_light"], alpha),
                                 (px, py - 1, 1, 1))
        # Blue tattoo sparks mixed in
        for i in range(4):
            t = (phase * 0.7 + i * 0.25) % 1.0
            px = cx - 12 + i * 8 + int(math.cos(phase + i) * 4)
            py = cy + 4 - int(t * 18)
            alpha = _NS_akaroth._alpha(180 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_akaroth.PALETTE["tat_mid"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_akaroth.PALETTE["tat_light"], alpha),
                                 (px, py, 1, 1))
        # Trail
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_akaroth._alpha(140 - i * 25)
                if alpha > 0:
                    _NS_akaroth._aacircle(surface,
                                          (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                          (sx, sy), max(1, 4 - i))
                    pygame.draw.rect(surface, _NS_akaroth.PALETTE["crimson_light"],
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 110 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (8, 3, 5, 170), (5, 6, 120, 12))
        pygame.draw.ellipse(shadow, (60, 15, 25, 100), (15, 8, 100, 8))
        surface.blit(shadow, (x - 65, y - 12))
    def _draw_crimson_aura(surface, x, y, phase):
        """Crimson battle aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_akaroth._alpha((85 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_akaroth._aacircle(aura,
                                      (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                                      (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_akaroth._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_akaroth._aacircle(aura,
                                      (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                      (100, 85), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_akaroth._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_akaroth._aacircle(aura,
                                      (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                      (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))
        # Floating red particles
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 38 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_akaroth.PALETTE["crimson_light"] if i % 3 != 0 \
                else _NS_akaroth.PALETTE["tat_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["white"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground crimson ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_akaroth.PALETTE["crimson_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_akaroth.PALETTE["crimson_dark"], 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_akaroth.PALETTE["crimson_mid"], 200),
                            (25, 19, 110, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_akaroth.PALETTE["crimson_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_akaroth.PALETTE["crimson_shine"],
                                        _NS_akaroth._alpha(160 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - AIR SHOCKWAVE (palm strike releases arc)
    # ============================================================
    def _draw_shockwave_skill(surface, boss, x, y, timer, phase):
        """Blue crescent shockwave from palm strike."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind up - blue glow at palm
            t = progress / 0.3
            palm_x = x + facing * 20
            palm_y = y - 4
            for r in range(int(8 * t), 0, -1):
                alpha = _NS_akaroth._alpha(200 * t * (8 - r) / 8)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["air_mid"], alpha),
                                      (palm_x, palm_y), r)
            _NS_akaroth._aacircle(surface, _NS_akaroth.PALETTE["air_light"],
                                  (palm_x, palm_y), 3)
            _NS_akaroth._aacircle(surface, _NS_akaroth.PALETTE["air_shine"],
                                  (palm_x, palm_y), 1)
        else:
            # SHOCKWAVE CRESCENT expanding forward
            t = (progress - 0.3) / 0.7
            palm_x = x + facing * 22
            palm_y = y - 4
            # Distance shockwave travels
            wave_dist = int(t * 90)
            wave_center_x = palm_x + facing * wave_dist
            wave_center_y = palm_y
            # Draw crescent arc (opens facing target direction)
            arc_radius = 25 + int(t * 15)
            # Multiple arc traces (motion blur)
            for trace in range(4):
                trace_dist = wave_dist - trace * 8
                if trace_dist < 0:
                    continue
                trace_x = palm_x + facing * trace_dist
                trace_y = palm_y
                alpha = _NS_akaroth._alpha(240 - trace * 40)
                # Crescent arc pointing forward (facing direction)
                num_arc = 15
                arc_pts_inner = []
                arc_pts_outer = []
                for i in range(num_arc):
                    arc_t = i / (num_arc - 1)
                    # Arc from -pi/2.5 to +pi/2.5 relative to facing
                    arc_angle = -math.pi / 2.5 + arc_t * (2 * math.pi / 2.5)
                    if facing == -1:
                        arc_angle = math.pi - arc_angle
                    ix = trace_x + int(math.cos(arc_angle) * (arc_radius - 4))
                    iy = trace_y + int(math.sin(arc_angle) * (arc_radius - 4))
                    ox = trace_x + int(math.cos(arc_angle) * (arc_radius + 4))
                    oy = trace_y + int(math.sin(arc_angle) * (arc_radius + 4))
                    arc_pts_inner.append((ix, iy))
                    arc_pts_outer.append((ox, oy))
                # Draw thick arc
                for i in range(len(arc_pts_inner) - 1):
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_darkest"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 5)
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_dark"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 3)
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_mid"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 2)
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_light"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 1)
                    # Outer glow
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_light"], alpha),
                                     arc_pts_outer[i], arc_pts_outer[i + 1], 2)
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_shine"], alpha),
                                     arc_pts_outer[i], arc_pts_outer[i + 1], 1)
                # Bright middle
                for i in range(len(arc_pts_inner) - 1):
                    mx1 = (arc_pts_inner[i][0] + arc_pts_outer[i][0]) // 2
                    my1 = (arc_pts_inner[i][1] + arc_pts_outer[i][1]) // 2
                    mx2 = (arc_pts_inner[i + 1][0] + arc_pts_outer[i + 1][0]) // 2
                    my2 = (arc_pts_inner[i + 1][1] + arc_pts_outer[i + 1][1]) // 2
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["air_shine"], alpha),
                                     (mx1, my1), (mx2, my2), 1)
                    pygame.draw.line(surface,
                                     (*_NS_akaroth.PALETTE["white"], alpha),
                                     (mx1, my1), (mx2, my2), 1)
    # ============================================================
    # SKILL W - COMPASS NEEDLES (multi-directional needles)
    # ============================================================
    def _draw_needles_skill(surface, boss, x, y, timer, phase):
        """Multiple blue needle projectiles from center."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akaroth._target_position(boss, x, y)
        # Origin at boss center
        origin_x = x
        origin_y = y - 10
        if progress < 0.2:
            # Charge - compass symbol appears at center
            t = progress / 0.2
            for r in range(int(15 * t), 0, -1):
                alpha = _NS_akaroth._alpha(180 * t)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["air_dark"], alpha),
                                      (origin_x, origin_y), r, 1)
            # 8-point compass star
            for i in range(8):
                angle = i * math.pi / 4 + phase
                sx = origin_x + int(math.cos(angle) * 12 * t)
                sy = origin_y + int(math.sin(angle) * 12 * t)
                pygame.draw.line(surface, _NS_akaroth.PALETTE["air_bright"] if False
                                 else _NS_akaroth.PALETTE["air_light"],
                                 (origin_x, origin_y), (sx, sy), 1)
                pygame.draw.rect(surface, _NS_akaroth.PALETTE["air_shine"],
                                 (sx, sy, 1, 1))
            # Central compass rose
            _NS_akaroth._aacircle(surface, _NS_akaroth.PALETTE["air_mid"],
                                  (origin_x, origin_y), 4)
            _NS_akaroth._aacircle(surface, _NS_akaroth.PALETTE["air_light"],
                                  (origin_x, origin_y), 2)
        else:
            # NEEDLES SHOOT OUT in all directions, then track target
            t = (progress - 0.2) / 0.8
            num_needles = 12
            for i in range(num_needles):
                base_angle = i * math.pi * 2 / num_needles + math.pi / 24
                # First half: needles go outward, second half: they curve toward target
                if t < 0.4:
                    # Straight out
                    needle_t = t / 0.4
                    distance = int(needle_t * 40)
                    nx = origin_x + int(math.cos(base_angle) * distance)
                    ny = origin_y + int(math.sin(base_angle) * distance)
                else:
                    # Curve toward target
                    curve_t = (t - 0.4) / 0.6
                    # Start position
                    sx = origin_x + int(math.cos(base_angle) * 40)
                    sy = origin_y + int(math.sin(base_angle) * 40)
                    # Interpolate toward target
                    nx = int(sx + (tx - sx) * curve_t)
                    ny = int(sy + (ty - sy) * curve_t)
                # Direction of needle (velocity vector)
                if t < 0.4:
                    dir_angle = base_angle
                else:
                    # Angle from needle to target
                    dx = tx - nx
                    dy = ty - ny
                    dir_angle = math.atan2(dy, dx)
                # Draw needle shape (elongated diamond/arrow)
                needle_len = 12
                tip_x = nx + int(math.cos(dir_angle) * needle_len)
                tip_y = ny + int(math.sin(dir_angle) * needle_len)
                back_x = nx - int(math.cos(dir_angle) * 4)
                back_y = ny - int(math.sin(dir_angle) * 4)
                # Perpendicular for needle width
                perp_x = -math.sin(dir_angle)
                perp_y = math.cos(dir_angle)
                mid_a_x = nx + int(perp_x * 2)
                mid_a_y = ny + int(perp_y * 2)
                mid_b_x = nx - int(perp_x * 2)
                mid_b_y = ny - int(perp_y * 2)
                alpha = _NS_akaroth._alpha(240)
                # Needle body (elongated diamond)
                _NS_akaroth._poly(surface,
                                  (*_NS_akaroth.PALETTE["air_darkest"], alpha),
                                  [(tip_x, tip_y), (mid_a_x, mid_a_y),
                                   (back_x, back_y), (mid_b_x, mid_b_y)])
                _NS_akaroth._poly(surface,
                                  (*_NS_akaroth.PALETTE["air_dark"], alpha),
                                  [(tip_x, tip_y),
                                   (int(mid_a_x * 0.7 + tip_x * 0.3),
                                    int(mid_a_y * 0.7 + tip_y * 0.3)),
                                   (nx, ny),
                                   (int(mid_b_x * 0.7 + tip_x * 0.3),
                                    int(mid_b_y * 0.7 + tip_y * 0.3))])
                # Bright core line
                pygame.draw.line(surface,
                                 (*_NS_akaroth.PALETTE["air_mid"], alpha),
                                 (back_x, back_y), (tip_x, tip_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_akaroth.PALETTE["air_light"], alpha),
                                 (back_x, back_y), (tip_x, tip_y), 1)
                # Tip highlight
                pygame.draw.rect(surface,
                                 (*_NS_akaroth.PALETTE["air_shine"], alpha),
                                 (tip_x, tip_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_akaroth.PALETTE["white"], alpha),
                                 (tip_x, tip_y, 1, 1))
                # Trail behind needle
                for trail_i in range(3):
                    trail_offset = trail_i * 3
                    trail_x = back_x - int(math.cos(dir_angle) * trail_offset)
                    trail_y = back_y - int(math.sin(dir_angle) * trail_offset)
                    trail_alpha = _NS_akaroth._alpha(180 - trail_i * 50)
                    pygame.draw.rect(surface,
                                     (*_NS_akaroth.PALETTE["air_light"], trail_alpha),
                                     (trail_x, trail_y, 1, 1))
    # ============================================================
    # SKILL E - CRIMSON BLOOM (lotus ripple explosion)
    # ============================================================
    def _draw_lotus_ground(surface, boss, x, y, timer, phase):
        """Crimson lotus/ripple ground effect."""
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akaroth._target_position(boss, x, y)
        # Impact position (in front of boss)
        impact_x = int((x + tx) / 2)
        impact_y = ty
        if progress > 0.5:
            # After slam - expanding ripples
            t = (progress - 0.5) / 0.5
            # Multiple ring ripples
            for ring_i in range(4):
                ring_t = t - ring_i * 0.15
                if ring_t <= 0:
                    continue
                r = int(ring_t * 60)
                alpha = _NS_akaroth._alpha(230 * (1 - ring_t))
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                                    (impact_x - r, impact_y - r // 3,
                                     r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                    (impact_x - r + 2, impact_y - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                    (impact_x - r + 5, impact_y - r // 3 + 3,
                                     r * 2 - 10, r * 2 // 3 - 6), 1)
    def _draw_lotus_skill(surface, boss, x, y, timer, phase):
        """Crimson lotus flower + slam explosion."""
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akaroth._target_position(boss, x, y)
        impact_x = int((x + tx) / 2)
        impact_y = ty
        if progress < 0.4:
            # LEAP UP + charge lotus above (boss position raised in main draw)
            t = progress / 0.4
            # Lotus flower pattern above boss (petals radiating)
            lotus_y = y - 40 - int(math.sin(t * math.pi) * 20)
            # Draw 8-petal lotus
            for petal_i in range(8):
                petal_angle = petal_i * math.pi / 4 + phase * 0.5
                petal_len = int(15 * t)
                # Petal shape (triangular)
                tip_x = impact_x + int(math.cos(petal_angle) * petal_len)
                tip_y = lotus_y + int(math.sin(petal_angle) * petal_len)
                perp_x = -math.sin(petal_angle)
                perp_y = math.cos(petal_angle)
                base_a_x = impact_x + int(perp_x * 3)
                base_a_y = lotus_y + int(perp_y * 3)
                base_b_x = impact_x - int(perp_x * 3)
                base_b_y = lotus_y - int(perp_y * 3)
                alpha = _NS_akaroth._alpha(220 * t)
                _NS_akaroth._poly(surface,
                                  (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                                  [(tip_x, tip_y), (base_a_x, base_a_y),
                                   (base_b_x, base_b_y)])
                _NS_akaroth._poly(surface,
                                  (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                  [(tip_x, tip_y),
                                   (int(base_a_x * 0.7 + tip_x * 0.3),
                                    int(base_a_y * 0.7 + tip_y * 0.3)),
                                   (int(base_b_x * 0.7 + tip_x * 0.3),
                                    int(base_b_y * 0.7 + tip_y * 0.3))])
                _NS_akaroth._poly(surface,
                                  (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                  [(tip_x, tip_y),
                                   (int(base_a_x * 0.5 + tip_x * 0.5),
                                    int(base_a_y * 0.5 + tip_y * 0.5)),
                                   (int(base_b_x * 0.5 + tip_x * 0.5),
                                    int(base_b_y * 0.5 + tip_y * 0.5))])
                pygame.draw.line(surface,
                                 (*_NS_akaroth.PALETTE["crimson_shine"], alpha),
                                 (impact_x, lotus_y), (tip_x, tip_y), 1)
            # Center lotus core (bright bloom)
            for r in range(int(8 * t), 0, -1):
                alpha = _NS_akaroth._alpha(200 * t * (8 - r) / 8)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_light"], alpha),
                                      (impact_x, lotus_y), r)
            _NS_akaroth._aacircle(surface, _NS_akaroth.PALETTE["crimson_shine"],
                                  (impact_x, lotus_y), max(1, int(3 * t)))
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["white"],
                             (impact_x, lotus_y, 1, 1))
        elif progress < 0.5:
            # Falling - streak of red as boss slams down
            t = (progress - 0.4) / 0.1
            for streak in range(6):
                sy = y - 40 + int(t * 40) - streak * 4
                alpha = _NS_akaroth._alpha(220 - streak * 30)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                      (impact_x, sy), 5)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                      (impact_x, sy), 3)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_light"], alpha),
                                      (impact_x, sy), 2)
        else:
            # SLAM IMPACT - massive explosion
            t = (progress - 0.5) / 0.5
            # Central explosion
            r = int(20 + t * 40)
            alpha = _NS_akaroth._alpha(255 * (1 - t))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                                  (impact_x, impact_y), r + 4)
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                  (impact_x, impact_y), r)
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                  (impact_x, impact_y), max(1, r - 8))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_light"], alpha),
                                  (impact_x, impact_y), max(1, r - 16))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_shine"], alpha),
                                  (impact_x, impact_y), max(1, r // 4))
            # Radial burst spikes (like lotus petals shooting out)
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = impact_x + int(math.cos(angle_s) * r * 1.2)
                ey = impact_y + int(math.sin(angle_s) * r * 1.2 * 0.7)
                # Spike-shaped ray
                pygame.draw.line(surface,
                                 (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                 (impact_x, impact_y), (ex, ey), 3)
                pygame.draw.line(surface,
                                 (*_NS_akaroth.PALETTE["crimson_light"], alpha),
                                 (impact_x, impact_y), (ex, ey), 1)
                pygame.draw.rect(surface,
                                 (*_NS_akaroth.PALETTE["crimson_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL R - HUNTER'S DASH (lock-on multi-hit dash)
    # ============================================================
    def _draw_pursuit_ground(surface, boss, x, y, timer, phase):
        """Dash trail on ground."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akaroth._target_position(boss, x, y)
        if 0.2 < progress < 0.9:
            # Long streaking trail on ground
            for i in range(10):
                dt = (progress - 0.2) / 0.7 - i * 0.05
                if dt < 0:
                    continue
                dx = int(x + (tx - x) * dt)
                dy = ty + 40
                alpha = _NS_akaroth._alpha(180 * (1 - i / 10))
                # Ground trail marks
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                    (dx - 10, dy - 3, 20, 6))
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                    (dx - 6, dy - 2, 12, 4))
    def _draw_pursuit_skill(surface, boss, x, y, timer, phase):
        """Lock-on target + dash streaks + multi-hit."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akaroth._target_position(boss, x, y)
        if progress < 0.2:
            # LOCK-ON reticle on target
            t = progress / 0.2
            # Circular reticle
            for ring_i in range(2):
                r_ring = 20 - ring_i * 4
                pygame.draw.circle(surface,
                                   _NS_akaroth.PALETTE["crimson_light"],
                                   (tx, ty - 10), r_ring, 2)
            # Crosshair
            pygame.draw.line(surface, _NS_akaroth.PALETTE["crimson_light"],
                             (tx - 25, ty - 10), (tx - 15, ty - 10), 2)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["crimson_light"],
                             (tx + 15, ty - 10), (tx + 25, ty - 10), 2)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["crimson_light"],
                             (tx, ty - 35), (tx, ty - 25), 2)
            pygame.draw.line(surface, _NS_akaroth.PALETTE["crimson_light"],
                             (tx, ty + 5), (tx, ty + 15), 2)
            # Corner brackets
            for corner_x, corner_y in [(-18, -28), (18, -28), (-18, 8), (18, 8)]:
                bx = tx + corner_x
                by = ty - 10 + corner_y
                sign_x = 1 if corner_x > 0 else -1
                sign_y = 1 if corner_y > 0 else -1
                pygame.draw.line(surface, _NS_akaroth.PALETTE["crimson_shine"],
                                 (bx, by), (bx - sign_x * 4, by), 2)
                pygame.draw.line(surface, _NS_akaroth.PALETTE["crimson_shine"],
                                 (bx, by), (bx, by - sign_y * 4), 2)
        elif progress < 0.85:
            # DASH - massive streaking trail
            t = (progress - 0.2) / 0.65
            dash_x = int(x + (tx - x - facing * 40) * t)
            # Multiple horizontal streak lines
            for line_i in range(5):
                streak_y_offset = (line_i - 2) * 4
                line_y = y - 10 + streak_y_offset
                for i in range(10):
                    trail_t = t - i * 0.08
                    if trail_t < 0:
                        continue
                    sx = int(x + (dash_x - x) * trail_t)
                    alpha = _NS_akaroth._alpha(220 - i * 22)
                    _NS_akaroth._aaline(surface,
                                        (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                                        (sx - facing * 30, line_y),
                                        (sx, line_y), 3)
                    _NS_akaroth._aaline(surface,
                                        (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                        (sx - facing * 30, line_y),
                                        (sx, line_y), 2)
                    _NS_akaroth._aaline(surface,
                                        (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                        (sx - facing * 30, line_y),
                                        (sx, line_y), 1)
            # Big central streak
            _NS_akaroth._aaline(surface,
                                (*_NS_akaroth.PALETTE["crimson_dark"], 240),
                                (x, y - 10), (dash_x, y - 10), 5)
            _NS_akaroth._aaline(surface,
                                (*_NS_akaroth.PALETTE["crimson_mid"], 240),
                                (x, y - 10), (dash_x, y - 10), 3)
            _NS_akaroth._aaline(surface,
                                (*_NS_akaroth.PALETTE["crimson_light"], 240),
                                (x, y - 10), (dash_x, y - 10), 2)
            _NS_akaroth._aaline(surface,
                                (*_NS_akaroth.PALETTE["crimson_shine"], 240),
                                (x, y - 10), (dash_x, y - 10), 1)
            # Multi-hit impacts at target
            hit_count = int(t * 6)
            for hit_i in range(hit_count):
                hit_progress = (t * 6 - hit_i) / 6
                if hit_progress < 0 or hit_progress > 1:
                    continue
                hit_alpha = _NS_akaroth._alpha(200 * (1 - hit_progress))
                offset_x = int(math.sin(hit_i * 2.5) * 8)
                offset_y = int(math.cos(hit_i * 2.5) * 5)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_light"], hit_alpha),
                                      (tx + offset_x, ty - 10 + offset_y), 8)
                _NS_akaroth._aacircle(surface,
                                      (*_NS_akaroth.PALETTE["crimson_shine"], hit_alpha),
                                      (tx + offset_x, ty - 10 + offset_y), 4)
                pygame.draw.rect(surface,
                                 (*_NS_akaroth.PALETTE["white"], hit_alpha),
                                 (tx + offset_x, ty - 10 + offset_y, 2, 2))
        else:
            # Final big blow
            t = (progress - 0.85) / 0.15
            radius = int(15 + t * 30)
            alpha = _NS_akaroth._alpha(255 * (1 - t))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_darkest"], alpha),
                                  (tx, ty), radius + 4)
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_dark"], alpha),
                                  (tx, ty), radius)
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_mid"], alpha),
                                  (tx, ty), max(1, radius - 8))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_light"], alpha),
                                  (tx, ty), max(1, radius - 16))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["crimson_shine"], alpha),
                                  (tx, ty), max(1, radius // 5))
            # Star burst
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * radius * 1.3)
                ey = ty + int(math.sin(angle_s) * radius * 1.3)
                pygame.draw.line(surface,
                                 (*_NS_akaroth.PALETTE["crimson_shine"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_akaroth.PALETTE["white"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL D - STYLE ABSORPTION (analyze/replicate)
    # ============================================================
    def _draw_absorption_ground(surface, boss, x, y, timer, pulse):
        """Purple ground ring."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 2))
        if r > 3:
            # Multiple rotating rings
            for ring_i in range(2):
                offset = ring_i * 4
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["abs_darkest"], 200),
                                    (x - r + offset, y + 40 - r // 3 + offset // 2,
                                     r * 2 - offset * 2, r * 2 // 3 - offset), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_akaroth.PALETTE["abs_mid"], 180),
                                    (x - r + offset + 2, y + 40 - r // 3 + offset // 2 + 1,
                                     r * 2 - offset * 2 - 4, r * 2 // 3 - offset - 2), 1)
    def _draw_absorption_aura(surface, boss, x, y, timer, phase):
        """Purple aura absorbing energy around boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Absorbing aura around body
        breath = math.sin(phase * 2.5) * 3
        r = 45 + int(breath)
        aura_surf = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)
        # Layered purple aura
        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_akaroth._aacircle(aura_surf,
                                  (*_NS_akaroth.PALETTE["abs_darkest"], alpha_val),
                                  center, r - i, thickness)
            _NS_akaroth._aacircle(aura_surf,
                                  (*_NS_akaroth.PALETTE["abs_mid"], alpha_val),
                                  center, r - i - 1, 1)
        # Energy being absorbed (spirals INWARD toward center)
        for i in range(20):
            spiral_t = (phase * 1.5 + i * 0.1) % 1.0
            spiral_r = int((1 - spiral_t) * r)
            angle = phase * 2 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * spiral_r)
            sy = center[1] + int(math.sin(angle) * spiral_r)
            alpha = _NS_akaroth._alpha(220 * (1 - spiral_t))
            pygame.draw.rect(aura_surf, (*_NS_akaroth.PALETTE["abs_light"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(aura_surf, (*_NS_akaroth.PALETTE["abs_shine"], alpha),
                             (sx, sy, 1, 1))
        surface.blit(aura_surf, (x - r - 15, y - r - 15))
        # Ghostly silhouettes of "absorbed styles" appearing around
        for i in range(3):
            g_angle = phase * 0.5 + i * math.pi * 2 / 3
            gx = x + int(math.cos(g_angle) * (r + 15))
            gy = y + int(math.sin(g_angle) * (r + 15) * 0.5)
            g_alpha = _NS_akaroth._alpha(150 + math.sin(phase * 2 + i) * 60)
            # Simple humanoid silhouette
            # Head
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["abs_mid"], g_alpha),
                                  (gx, gy - 10), 3)
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["abs_light"], g_alpha),
                                  (gx, gy - 10), 2)
            # Body
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["abs_mid"], g_alpha),
                             (gx, gy - 7), (gx, gy + 5), 4)
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["abs_light"], g_alpha),
                             (gx, gy - 7), (gx, gy + 5), 2)
            # Arms
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["abs_mid"], g_alpha),
                             (gx, gy - 4), (gx - 4, gy + 2), 2)
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["abs_mid"], g_alpha),
                             (gx, gy - 4), (gx + 4, gy + 2), 2)
            # Legs
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["abs_mid"], g_alpha),
                             (gx, gy + 5), (gx - 3, gy + 12), 2)
            pygame.draw.line(surface,
                             (*_NS_akaroth.PALETTE["abs_mid"], g_alpha),
                             (gx, gy + 5), (gx + 3, gy + 12), 2)
            # Energy line from silhouette to boss (being absorbed)
            _NS_akaroth._aaline(surface,
                                (*_NS_akaroth.PALETTE["abs_light"], g_alpha),
                                (gx, gy), (x, y), 1)
        # Rising purple particles
        for i in range(10):
            p_t = (phase + i * 0.13) % 1.0
            px = x + int(math.sin(phase * 2 + i) * 30)
            py = y - int(p_t * 40) + 10
            alpha = _NS_akaroth._alpha(220 * (1 - p_t))
            _NS_akaroth._aacircle(surface,
                                  (*_NS_akaroth.PALETTE["abs_mid"], alpha),
                                  (px, py), 2)
            pygame.draw.rect(surface, _NS_akaroth.PALETTE["abs_shine"],
                             (px, py, 1, 1))



# ====================================================================
# KASSADIN (VOID WALKER) - Mini Boss
# ====================================================================

class _NS_kassadin:
    """Namespace kassadin - Void Walker boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Void purple (primary theme)
        "void_darkest": (8, 3, 20),
        "void_dark": (30, 10, 55),
        "void_mid": (75, 25, 130),
        "void_light": (145, 60, 220),
        "void_bright": (200, 120, 255),
        "void_shine": (240, 200, 255),
        # Pink/magenta accent (bright void)
        "pink_dark": (100, 20, 80),
        "pink_mid": (200, 50, 160),
        "pink_light": (255, 120, 220),
        "pink_shine": (255, 200, 240),
        # Armor (dark metallic purple/black)
        "armor_darkest": (5, 3, 12),
        "armor_dark": (20, 15, 35),
        "armor_mid": (45, 35, 65),
        "armor_light": (85, 70, 115),
        "armor_shine": (145, 130, 175),
        # Gold trim accents
        "gold_dark": (80, 55, 15),
        "gold_mid": (170, 130, 40),
        "gold_light": (240, 200, 100),
        "gold_shine": (255, 240, 180),
        # Cloak/robe (dark purple with gradient)
        "robe_darkest": (12, 5, 25),
        "robe_dark": (28, 15, 45),
        "robe_mid": (55, 30, 85),
        "robe_light": (95, 60, 140),
        # Void eyes (glowing pink/purple)
        "eye_socket": (5, 2, 12),
        "eye_dark": (60, 10, 90),
        "eye_mid": (180, 60, 220),
        "eye_light": (240, 150, 255),
        "eye_glow": (255, 220, 255),
        # Mask (dark visor)
        "mask_darkest": (2, 1, 5),
        "mask_dark": (15, 10, 25),
        "mask_mid": (40, 30, 55),
        "mask_light": (70, 55, 90),
        # Rift/tear (deep space)
        "rift_darkest": (2, 0, 8),
        "rift_dark": (20, 5, 40),
        "rift_mid": (60, 20, 100),
        "rift_edge": (180, 80, 240),
        # Ambient mist
        "mist_dark": (25, 10, 40),
        "mist_mid": (60, 25, 90),
        "mist_light": (130, 70, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kassadin._clamp(color)
        if _NS_kassadin.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kassadin._clamp(color)
        if _NS_kassadin.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kassadin._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kassadin(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kassadin._detect_moving(boss)
        _NS_kassadin._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kas_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_kassadin._draw_void_aura(surface, x, y, pulse)
        _NS_kassadin._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_kassadin._draw_rift_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kassadin._draw_riftwalk_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 4)
        # Handle riftwalk teleport (make body invisible mid-teleport)
        show_body = True
        if active_skill == "r":
            duration = 60
            r_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if 0.3 < r_prog < 0.7:
                show_body = False
        # Body (always floating)
        if show_body:
            if attacking:
                _NS_kassadin._draw_body_attack(surface, boss, x, y + float_bob)
            elif moving:
                _NS_kassadin._draw_body_walk(surface, boss, x, y + float_bob)
            else:
                _NS_kassadin._draw_body_idle(surface, boss, x, y + float_bob)
        # W - Shield bubble (over body)
        if active_skill == "w":
            _NS_kassadin._draw_force_pulse_shield(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_kassadin._draw_null_sphere_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kassadin._draw_force_pulse_wave(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kassadin._draw_void_rift_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kassadin._draw_riftwalk_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kas_previous_timer", 0))
        active = bool(getattr(boss, "_kas_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kas_attack_active = True
            boss._kas_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kas_attack_frame = int(getattr(boss, "_kas_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kas_attack_active = False
            boss._kas_attack_frame = 0
            active = False
        boss._kas_previous_timer = timer
        boss._kas_attack_progress = (
            min(1.0, getattr(boss, "_kas_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kas_last_x"):
            boss._kas_last_x = boss.x
            boss._kas_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kas_last_x)
        dy = abs(boss.y - boss._kas_last_y)
        boss._kas_last_x = boss.x
        boss._kas_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_kassadin._draw_shadow(surface, x, y + 50)
        _NS_kassadin._draw_void_mist(surface, x, y + 44, boss.pulse)
        _NS_kassadin._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_kassadin._draw_shadow(surface, x + sway, y + 50)
        _NS_kassadin._draw_void_mist(surface, x + sway, y + 44, phase, trail=True,
                                     facing=boss.direction)
        _NS_kassadin._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_kas_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Melee swing motion
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 4) * boss.direction
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-4 + t * 12)) * boss.direction
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(8 * (1 - t)) * boss.direction
        _NS_kassadin._draw_shadow(surface, x + lunge, y + 50)
        _NS_kassadin._draw_void_mist(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_kassadin._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                                "attack", progress)
        _NS_kassadin._draw_basic_melee_swing(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw armored void walker: robe, horned helm, glowing eyes."""
        # Order: back arm → robe → front arm → head/helm
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.4:
                arm_swing = -int(attack_progress / 0.4 * 10) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                arm_swing = int((-10 + t * 28)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_swing = int(18 * (1 - t)) * facing
        # Back tendrils (void energy behind)
        _NS_kassadin._draw_void_tendrils(surface, cx, cy, facing, phase)
        # Back arm
        _NS_kassadin._draw_arm(surface, cx - facing * 8, cy - 4, facing, phase,
                               -arm_swing // 2, back=True)
        # Robe (main body)
        _NS_kassadin._draw_robe(surface, cx, cy, facing, phase, action)
        # Front arm (holding void energy)
        _NS_kassadin._draw_arm(surface, cx + facing * 6, cy - 4, facing, phase,
                               arm_swing, back=False, action=action,
                               attack_progress=attack_progress)
        # Head with horned helm
        _NS_kassadin._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_void_tendrils(surface, cx, cy, facing, phase):
        """Void energy tendrils floating behind body."""
        # Multiple wispy tendrils
        for i in range(5):
            side = -1 if i < 3 else 1
            offset_x = (i - 2) * 3
            base_x = cx + offset_x * side
            base_y = cy - 8
            wave = math.sin(phase * 0.8 + i * 0.7) * 3
            # Tendril going up-back
            for seg in range(4):
                t = seg / 4
                seg_x = base_x + int(side * (5 + seg * 4)) + int(wave * (seg + 1) / 3)
                seg_y = base_y - int((seg + 1) * 5)
                alpha = _NS_kassadin._alpha(180 - seg * 30)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (seg_x, seg_y), max(1, 4 - seg))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (seg_x, seg_y), max(1, 3 - seg))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                       (seg_x, seg_y), max(1, 2 - seg))
                if seg < 2:
                    pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                                     (seg_x, seg_y, 1, 1))
    def _draw_robe(surface, cx, cy, facing, phase, action):
        """Dark void robe with armor plates."""
        sway = math.sin(phase * 0.7) * 2
        # Main robe shape (long flowing)
        robe_shape = [
            (cx - 14, cy - 8),        # left shoulder
            (cx - 16, cy - 2),        # upper left
            (cx - 18, cy + 6),        # mid left
            (cx - 20, cy + 16),       # lower left
            (cx - 18 + int(sway), cy + 26),   # bottom left tip
            (cx - 12, cy + 32),       # bottom mid-left
            (cx - 4, cy + 34),        # bottom lowest
            (cx + 4, cy + 34),
            (cx + 12, cy + 32),
            (cx + 18 + int(sway), cy + 26),
            (cx + 20, cy + 16),
            (cx + 18, cy + 6),
            (cx + 16, cy - 2),
            (cx + 14, cy - 8),
        ]
        # Shadow
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in robe_shape])
        # Darkest base
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["robe_darkest"], robe_shape)
        # Mid tone
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["robe_dark"], [
            (cx - 13, cy - 7),
            (cx - 15, cy - 1),
            (cx - 17, cy + 6),
            (cx - 18, cy + 16),
            (cx - 16, cy + 24),
            (cx - 10, cy + 30),
            (cx + 10, cy + 30),
            (cx + 16, cy + 24),
            (cx + 18, cy + 16),
            (cx + 17, cy + 6),
            (cx + 15, cy - 1),
            (cx + 13, cy - 7),
        ])
        # Highlight chest area
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["robe_mid"], [
            (cx - 10, cy - 5),
            (cx - 12, cy + 2),
            (cx - 14, cy + 12),
            (cx - 10, cy + 22),
            (cx + 10, cy + 22),
            (cx + 14, cy + 12),
            (cx + 12, cy + 2),
            (cx + 10, cy - 5),
        ])
        # Robe highlights (folds)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["robe_light"],
                         (cx - 8, cy + 4), (cx - 10, cy + 20), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["robe_light"],
                         (cx + 8, cy + 4), (cx + 10, cy + 20), 1)
        # Chest armor plate (dark metal with gold trim)
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_darkest"], [
            (cx - 8, cy - 6),
            (cx - 10, cy - 2),
            (cx - 9, cy + 8),
            (cx - 6, cy + 12),
            (cx + 6, cy + 12),
            (cx + 9, cy + 8),
            (cx + 10, cy - 2),
            (cx + 8, cy - 6),
        ])
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_dark"], [
            (cx - 7, cy - 5),
            (cx - 9, cy - 1),
            (cx - 8, cy + 7),
            (cx - 5, cy + 11),
            (cx + 5, cy + 11),
            (cx + 8, cy + 7),
            (cx + 9, cy - 1),
            (cx + 7, cy - 5),
        ])
        # Central highlight on chest
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_mid"], [
            (cx - 4, cy - 3),
            (cx - 5, cy + 2),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 5, cy + 2),
            (cx + 4, cy - 3),
        ])
        pygame.draw.line(surface, _NS_kassadin.PALETTE["armor_light"],
                         (cx - 2, cy), (cx - 2, cy + 6), 1)
        # Gold trim edges
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_dark"],
                         (cx - 8, cy - 6), (cx - 10, cy - 2), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_dark"],
                         (cx + 8, cy - 6), (cx + 10, cy - 2), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_mid"],
                         (cx - 9, cy - 3), (cx - 9, cy + 5), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_mid"],
                         (cx + 9, cy - 3), (cx + 9, cy + 5), 1)
        # Central gem (void stone - glowing purple)
        pulse_glow = math.sin(phase * 2) * 0.3 + 0.7
        _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["gold_dark"],
                               (cx, cy + 3), 3)
        _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_darkest"],
                               (cx, cy + 3), 2)
        _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_mid"],
                               (cx, cy + 3), 2)
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                         (cx, cy + 3, 1, 1))
        # Radiating glow
        for r in range(6, 1, -1):
            alpha = _NS_kassadin._alpha(80 * (6 - r) / 6 * pulse_glow)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                   (cx, cy + 3), r)
        # Shoulder pauldrons (spiky armor)
        for side_mult in (-1, 1):
            sx = cx + 12 * side_mult
            sy = cy - 6
            # Base pauldron
            _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_darkest"], [
                (sx, sy - 4),
                (sx - 3 * side_mult, sy - 2),
                (sx - 4 * side_mult, sy + 3),
                (sx - 2 * side_mult, sy + 6),
                (sx + 3 * side_mult, sy + 4),
                (sx + 4 * side_mult, sy - 1),
            ])
            _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_dark"], [
                (sx, sy - 3),
                (sx - 2 * side_mult, sy - 1),
                (sx - 3 * side_mult, sy + 3),
                (sx + 3 * side_mult, sy + 3),
                (sx + 3 * side_mult, sy - 1),
            ])
            _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_mid"], [
                (sx, sy - 2),
                (sx - 1 * side_mult, sy),
                (sx + 2 * side_mult, sy + 1),
                (sx + 2 * side_mult, sy - 1),
            ])
            pygame.draw.rect(surface, _NS_kassadin.PALETTE["armor_shine"],
                             (sx + side_mult, sy - 1, 1, 1))
            # Gold trim
            pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_mid"],
                             (sx - 3 * side_mult, sy + 3),
                             (sx + 3 * side_mult, sy + 4), 1)
            # Small spike
            _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_darkest"], [
                (sx + 3 * side_mult, sy - 4),
                (sx + 5 * side_mult, sy - 6),
                (sx + 4 * side_mult, sy - 2),
            ])
        # Bottom edge tattered highlights
        for x_off in (-14, -6, 2, 10):
            fold_y = cy + 28 + int(math.sin(phase + x_off) * 1)
            pygame.draw.line(surface, _NS_kassadin.PALETTE["robe_dark"],
                             (cx + x_off, fold_y - 4),
                             (cx + x_off, fold_y), 1)
        # Void energy leaking from bottom of robe
        for i in range(4):
            angle_i = i * math.pi / 4 + phase * 0.3
            wisp_x = cx + int(math.sin(angle_i) * 12)
            wisp_y = cy + 32 + int(math.sin(phase + i) * 2)
            alpha = _NS_kassadin._alpha(160 + math.sin(phase * 2 + i) * 40)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                   (wisp_x, wisp_y), 3)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                   (wisp_x, wisp_y), 2)
            pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                             (wisp_x, wisp_y, 1, 1))
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Draw armored arm with void glow."""
        depth = 0.7 if back else 1.0
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.55
        # Shoulder to elbow
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 12
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        # Elbow to hand
        hand_len = 14
        hand_angle = base_angle - math.radians(swing * 0.7)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If attacking with energy, extend forward
        if action == "attack" and not back and attack_progress > 0.4:
            hand_x = cx + facing * (10 + int(attack_progress * 10))
            hand_y = cy + int(math.sin(attack_progress * math.pi) * -6)
        # Arm thickness
        thickness = 6 if not back else 5
        color_main = _NS_kassadin.PALETTE["armor_darkest"] if back \
            else _NS_kassadin.PALETTE["armor_dark"]
        color_mid = _NS_kassadin.PALETTE["armor_dark"] if back \
            else _NS_kassadin.PALETTE["armor_mid"]
        # Shadow
        _NS_kassadin._aaline(surface, _NS_kassadin.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 2),
                             (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm (armored)
        _NS_kassadin._aaline(surface, color_main,
                             (shoulder_x, shoulder_y),
                             (elbow_x, elbow_y), thickness)
        _NS_kassadin._aaline(surface, color_mid,
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Elbow armor detail
        _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["armor_darkest"],
                               (elbow_x, elbow_y), 3)
        _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["armor_dark"],
                               (elbow_x, elbow_y), 2)
        # Gold trim on elbow
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["gold_mid"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # Forearm
        _NS_kassadin._aaline(surface, _NS_kassadin.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 2),
                             (hand_x + 1, hand_y + 2), thickness)
        _NS_kassadin._aaline(surface, color_main,
                             (elbow_x, elbow_y),
                             (hand_x, hand_y), thickness - 1)
        _NS_kassadin._aaline(surface, color_mid,
                             (elbow_x, elbow_y - 1),
                             (hand_x, hand_y - 1), max(1, thickness - 3))
        # Void gauntlet at wrist (glowing)
        if not back:
            gauntlet_pulse = math.sin(phase * 2) * 0.3 + 0.7
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["armor_darkest"],
                                   (hand_x, hand_y), 5)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["armor_dark"],
                                   (hand_x, hand_y), 4)
            # Void energy in palm
            for r in range(5, 0, -1):
                alpha = _NS_kassadin._alpha(150 * (5 - r) / 5 * gauntlet_pulse)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                       (hand_x, hand_y), r)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_mid"],
                                   (hand_x, hand_y), 2)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_bright"],
                                   (hand_x, hand_y), 1)
            # Void sparks around gauntlet
            for i in range(4):
                s_angle = phase * 2 + i * math.pi / 2
                sx = hand_x + int(math.cos(s_angle) * 6)
                sy = hand_y + int(math.sin(s_angle) * 6)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"],
                                 (sx, sy, 1, 1))
            # Claws (small)
            for cl in range(3):
                cl_x = hand_x + int(math.cos(hand_angle + cl * 0.5) * 5) * facing
                cl_y = hand_y + int(math.sin(hand_angle + cl * 0.5) * 5)
                pygame.draw.line(surface, _NS_kassadin.PALETTE["armor_darkest"],
                                 (hand_x, hand_y), (cl_x, cl_y), 2)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["armor_light"],
                                 (cl_x, cl_y, 1, 1))
        else:
            # Back hand (simpler)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["armor_darkest"],
                                   (hand_x, hand_y), 3)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["armor_dark"],
                                   (hand_x, hand_y), 2)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Horned void helm with glowing eye slits."""
        # Helm main shape
        helm_shape = [
            (cx - 8, cy),
            (cx - 9, cy - 4),
            (cx - 8, cy - 10),
            (cx - 4, cy - 14),
            (cx + 4, cy - 14),
            (cx + 8, cy - 10),
            (cx + 9, cy - 4),
            (cx + 8, cy),
            (cx + 6, cy + 4),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 6, cy + 4),
        ]
        # Shadow
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["shadow_deep"],
                           [(px + 1, py + 2) for px, py in helm_shape])
        # Main helm (dark armor)
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_darkest"], helm_shape)
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_dark"], [
            (cx - 7, cy),
            (cx - 8, cy - 4),
            (cx - 7, cy - 9),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 7, cy - 9),
            (cx + 8, cy - 4),
            (cx + 7, cy),
            (cx + 5, cy + 3),
            (cx - 5, cy + 3),
        ])
        # Helm ridge (top center)
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["armor_mid"], [
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 3, cy - 8),
            (cx - 3, cy - 8),
        ])
        pygame.draw.line(surface, _NS_kassadin.PALETTE["armor_light"],
                         (cx, cy - 12), (cx, cy - 4), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["armor_shine"],
                         (cx, cy - 10), (cx, cy - 6), 1)
        # Face plate (visor/mask - dark)
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["mask_darkest"], [
            (cx - 6, cy - 6),
            (cx - 7, cy - 3),
            (cx - 5, cy + 2),
            (cx + 5, cy + 2),
            (cx + 7, cy - 3),
            (cx + 6, cy - 6),
        ])
        _NS_kassadin._poly(surface, _NS_kassadin.PALETTE["mask_dark"], [
            (cx - 5, cy - 5),
            (cx - 6, cy - 3),
            (cx - 4, cy + 1),
            (cx + 4, cy + 1),
            (cx + 6, cy - 3),
            (cx + 5, cy - 5),
        ])
        # GLOWING EYE SLITS (pink/purple)
        _NS_kassadin._draw_void_eyes(surface, cx, cy, facing, phase, action)
        # HORNS (curved back)
        _NS_kassadin._draw_horns(surface, cx, cy, facing, phase)
        # Chin/jaw armor detail
        pygame.draw.line(surface, _NS_kassadin.PALETTE["armor_mid"],
                         (cx - 4, cy + 4), (cx + 4, cy + 4), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_mid"],
                         (cx - 3, cy + 5), (cx + 3, cy + 5), 1)
        # Side jaw plates
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_mid"],
                         (cx - 7, cy - 1), (cx - 6, cy + 3), 1)
        pygame.draw.line(surface, _NS_kassadin.PALETTE["gold_mid"],
                         (cx + 7, cy - 1), (cx + 6, cy + 3), 1)
    def _draw_void_eyes(surface, cx, cy, facing, phase, action):
        """Glowing pink/purple eye slits."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.3 if action == "attack" else 1.0
        # Left eye slit
        left_x = cx - 3
        right_x = cx + 3
        eye_y = cy - 2
        # Deep dark socket
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_socket"],
                         (left_x - 1, eye_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_socket"],
                         (right_x - 1, eye_y - 1, 3, 2))
        # Glow halo
        for r in range(6, 0, -1):
            alpha = _NS_kassadin._alpha(100 * (6 - r) / 6 * pulse * intensity)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["eye_mid"], alpha),
                                   (left_x, eye_y), r)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["eye_mid"], alpha),
                                   (right_x, eye_y), r)
        # Eye slit core
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_dark"],
                         (left_x - 1, eye_y, 3, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_dark"],
                         (right_x - 1, eye_y, 3, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_mid"],
                         (left_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_mid"],
                         (right_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_light"],
                         (left_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_light"],
                         (right_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_glow"],
                         (left_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_kassadin.PALETTE["eye_glow"],
                         (right_x, eye_y, 1, 1))
    def _draw_horns(surface, cx, cy, facing, phase):
        """Two large curved horns on helm."""
        sway = math.sin(phase * 0.3) * 1
        # Two horns curving up-back-outward
        for side_mult, base_off in ((-1, -5), (1, 5)):
            # Multiple segments for curved horn
            base_x = cx + base_off
            base_y = cy - 11
            # Horn goes UP first then curves outward
            segments = [
                (0, -3),
                (1 * side_mult, -6),
                (3 * side_mult, -9),
                (6 * side_mult, -11),
                (10 * side_mult, -12),
                (13 * side_mult, -11),
            ]
            prev_x, prev_y = base_x, base_y
            for i, (dx, dy) in enumerate(segments):
                seg_x = base_x + dx + int(sway * i / 3)
                seg_y = base_y + dy
                thickness = max(2, 5 - i // 2)
                _NS_kassadin._aaline(surface, _NS_kassadin.PALETTE["shadow_deep"],
                                     (prev_x + 1, prev_y + 1),
                                     (seg_x + 1, seg_y + 1), thickness + 1)
                _NS_kassadin._aaline(surface, _NS_kassadin.PALETTE["armor_darkest"],
                                     (prev_x, prev_y), (seg_x, seg_y), thickness)
                _NS_kassadin._aaline(surface, _NS_kassadin.PALETTE["armor_dark"],
                                     (prev_x, prev_y - 1),
                                     (seg_x, seg_y - 1), max(1, thickness - 1))
                _NS_kassadin._aaline(surface, _NS_kassadin.PALETTE["armor_mid"],
                                     (prev_x, prev_y - 2),
                                     (seg_x, seg_y - 2), max(1, thickness - 3))
                prev_x, prev_y = seg_x, seg_y
            # Sharp tip with void glow
            tip_x = base_x + segments[-1][0]
            tip_y = base_y + segments[-1][1]
            pygame.draw.rect(surface, _NS_kassadin.PALETTE["armor_shine"],
                             (tip_x, tip_y, 1, 1))
            # Void spark at tip
            alpha = _NS_kassadin._alpha(200 + math.sin(phase * 3) * 50)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                   (tip_x, tip_y), 2)
            pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"],
                             (tip_x, tip_y, 1, 1))
    # ============================================================
    # BASIC MELEE ATTACK - Void Slash
    # ============================================================
    def _draw_basic_melee_swing(surface, boss, x, y, progress):
        """Melee slash with void trail."""
        if progress < 0.4 or progress > 0.85:
            return
        facing = boss.direction
        # Swing arc
        swing_t = (progress - 0.4) / 0.45
        swing_angle = -math.pi * 0.3 + swing_t * math.pi * 0.7
        origin_x = x + facing * 8
        origin_y = y - 8
        arc_radius = 26
        # Multiple slash traces (arc)
        for trace in range(6):
            trace_t = swing_t - trace * 0.06
            if trace_t < 0:
                continue
            t_angle = -math.pi * 0.3 + trace_t * math.pi * 0.7
            ex = origin_x + int(math.cos(t_angle) * arc_radius) * facing
            ey = origin_y + int(math.sin(t_angle) * arc_radius)
            alpha = _NS_kassadin._alpha(230 - trace * 35)
            # Slash line (from origin to arc point)
            _NS_kassadin._aaline(surface,
                                 (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                 (origin_x, origin_y), (ex, ey), 5)
            _NS_kassadin._aaline(surface,
                                 (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                 (origin_x, origin_y), (ex, ey), 3)
            _NS_kassadin._aaline(surface,
                                 (*_NS_kassadin.PALETTE["void_light"], alpha),
                                 (origin_x, origin_y), (ex, ey), 1)
            # Bright endpoint
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                   (ex, ey), 3)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_shine"], alpha),
                                   (ex, ey), 1)
        # Sparks along arc
        for i in range(8):
            sp_angle = -math.pi * 0.3 + (swing_t - 0.05) * math.pi * 0.7
            sp_r = arc_radius + i * 2 - 8
            sx = origin_x + int(math.cos(sp_angle) * sp_r) * facing
            sy = origin_y + int(math.sin(sp_angle) * sp_r)
            pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"], (sx, sy, 1, 1))
    # ============================================================
    # FLOATING MIST (below body)
    # ============================================================
    def _draw_void_mist(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Void chakra mist below Kassadin."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base cloudy void
        for radius in range(28, 3, -2):
            alpha = _NS_kassadin._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kassadin.PALETTE["mist_dark"], alpha),
                    (60 - radius, 20 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(18, 2, -2):
            alpha = _NS_kassadin._alpha((18 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kassadin.PALETTE["mist_mid"], alpha),
                    (60 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 60, cy - 10))
        # Rising void particles
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 24 + i * 7 + int(math.sin(phase + i) * 4)
            py = cy + 4 - int(t * 25)
            alpha = _NS_kassadin._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                _NS_kassadin._aacircle(surface,
                                       (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (px, py), 3)
                _NS_kassadin._aacircle(surface,
                                       (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (px, py - 1), 2)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_light"],
                                 (px, py - 1, 1, 1))
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                                 (px, py - 2, 1, 1))
        # Pink sparks (magenta accent)
        for i in range(5):
            spark_t = (phase * 0.7 + i * 0.2) % 1.0
            sx = cx - 20 + i * 10 + int(math.sin(phase + i) * 5)
            sy = cy + 4 - int(spark_t * 22)
            alpha = _NS_kassadin._alpha(200 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_kassadin.PALETTE["pink_mid"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_kassadin.PALETTE["pink_light"], alpha),
                                 (sx, sy, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kassadin._alpha(160 - i * 25)
                if alpha > 0:
                    _NS_kassadin._aacircle(surface,
                                           (*_NS_kassadin.PALETTE["mist_dark"], alpha),
                                           (sx, sy), max(1, 5 - i))
                    _NS_kassadin._aacircle(surface,
                                           (*_NS_kassadin.PALETTE["mist_mid"], alpha),
                                           (sx, sy), max(1, 3 - i))
                    pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_light"],
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 110 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (5, 2, 8, 170), (5, 6, 120, 14))
        pygame.draw.ellipse(shadow, (40, 15, 60, 100), (15, 8, 100, 10))
        surface.blit(shadow, (x - 65, y - 13))
    def _draw_void_aura(surface, x, y, phase):
        """Massive void aura (purple)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_kassadin._alpha((95 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_kassadin._aacircle(aura, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_kassadin._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kassadin._aacircle(aura, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kassadin._alpha((35 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_kassadin._aacircle(aura, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating void particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_kassadin.PALETTE["void_light"] if i % 3 != 0 \
                else _NS_kassadin.PALETTE["pink_light"]
            hot_color = _NS_kassadin.PALETTE["void_shine"] if i % 3 != 0 \
                else _NS_kassadin.PALETTE["pink_shine"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground void ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kassadin.PALETTE["void_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kassadin.PALETTE["void_dark"], 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_kassadin.PALETTE["void_mid"], 200),
                            (25, 19, 110, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_kassadin.PALETTE["void_light"], 210),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kassadin.PALETTE["void_bright"],
                                       _NS_kassadin._alpha(150 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - NULL SPHERE (Void orb projectile)
    # ============================================================
    def _draw_null_sphere_skill(surface, boss, x, y, timer, phase):
        """Void energy sphere flying to target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kassadin._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in hand
            t = progress / 0.2
            hand_x = x + facing * 20
            hand_y = y - 6
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kassadin._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                       (hand_x, hand_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_kassadin._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (hand_x, hand_y), r)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_mid"],
                                   (hand_x, hand_y), max(1, cr - 2))
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_light"],
                                   (hand_x, hand_y), max(1, cr - 4))
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_shine"],
                                   (hand_x, hand_y), max(1, cr - 6))
            # Void sparks
            for i in range(6):
                s_angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(s_angle) * (cr + 3))
                sy = hand_y + int(math.sin(s_angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 22
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Comet trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kassadin._alpha(240 - i * 22)
                size = max(1, 8 - i)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                       (px, py), size)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                       (px, py), max(1, size - 3))
                # Sparks
                if i < 5:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Main sphere head (RING orbital style like reference)
            # Draw ring shape
            ring_r = 10
            for angle_i in range(24):
                angle_a = angle_i * math.pi / 12 + phase
                rx = bx + int(math.cos(angle_a) * ring_r)
                ry = by + int(math.sin(angle_a) * ring_r)
                _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_dark"], (rx, ry), 3)
                _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_mid"], (rx, ry), 2)
                _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_light"], (rx, ry), 1)
            # Inner glow
            for r in range(ring_r - 1, 0, -1):
                alpha = _NS_kassadin._alpha(120 * (ring_r - r) / ring_r)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (bx, by), r)
            # Bright core
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_bright"], (bx, by), 3)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_shine"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_kassadin.PALETTE["white"], (bx, by, 1, 1))
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_kassadin._alpha(255 * (1 - st))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                       (tx, ty), radius + 3, 3)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (tx, ty), max(1, radius - 6), 2)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                       (tx, ty), max(1, radius - 12), 1)
                # Radial rays
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius)
                    pygame.draw.line(surface,
                                     (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"],
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - FORCE PULSE (cone wave + shield)
    # ============================================================
    def _draw_force_pulse_shield(surface, boss, x, y, timer, phase):
        """Shield bubble around Kassadin during W."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Shield bubble
        breath = math.sin(phase * 2) * 2
        r = 40 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Ring layers
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            _NS_kassadin._aacircle(bubble, (*_NS_kassadin.PALETTE["void_dark"], alpha_val),
                                   center, r - i, thickness)
            _NS_kassadin._aacircle(bubble, (*_NS_kassadin.PALETTE["void_mid"], alpha_val),
                                   center, r - i - 1, 1)
        # Rotating sparkles
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_kassadin.PALETTE["void_bright"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_kassadin.PALETTE["void_shine"], (sx, sy, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
    def _draw_force_pulse_wave(surface, boss, x, y, timer, phase):
        """Cone wave forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind up - hand glows
            t = progress / 0.3
            hand_x = x + facing * 22
            hand_y = y - 4
            for r in range(int(6 + t * 4), 0, -1):
                alpha = _NS_kassadin._alpha(200 * t)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                       (hand_x, hand_y), r)
            _NS_kassadin._aacircle(surface, _NS_kassadin.PALETTE["void_shine"],
                                   (hand_x, hand_y), 2)
        elif progress < 0.75:
            # WAVE expands forward
            t = (progress - 0.3) / 0.45
            wave_dist = int(t * 140)
            start_x = x + facing * 22
            start_y = y - 4
            # Cone shape
            cone_length = 30 + int(t * 100)
            cone_width_near = 8
            cone_width_far = int(20 + t * 30)
            far_x = start_x + facing * cone_length
            far_y = start_y
            # Multiple layered cone waves
            for layer_i, (layer_dist, alpha_v) in enumerate([
                (0, 100), (5, 160), (10, 220),
            ]):
                l_alpha = _NS_kassadin._alpha(alpha_v * (1 - t * 0.5))
                near_w = cone_width_near + layer_i
                far_w = cone_width_far + layer_i * 2
                cone_pts = [
                    (start_x, start_y - near_w),
                    (far_x, far_y - far_w),
                    (far_x, far_y + far_w),
                    (start_x, start_y + near_w),
                ]
                cone_surf = pygame.Surface((160, 100), pygame.SRCALPHA)
                offset_x = min(p[0] for p in cone_pts) - 5
                offset_y = min(p[1] for p in cone_pts) - 5
                local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in cone_pts]
                if layer_i == 0:
                    _NS_kassadin._poly(cone_surf,
                                       (*_NS_kassadin.PALETTE["void_dark"], l_alpha),
                                       local_pts)
                elif layer_i == 1:
                    _NS_kassadin._poly(cone_surf,
                                       (*_NS_kassadin.PALETTE["void_mid"], l_alpha),
                                       local_pts)
                else:
                    _NS_kassadin._poly(cone_surf,
                                       (*_NS_kassadin.PALETTE["void_light"], l_alpha),
                                       local_pts)
                surface.blit(cone_surf, (offset_x, offset_y))
            # Bright leading edge
            for i in range(8):
                y_off = -cone_width_far + int(i * cone_width_far * 2 / 7)
                edge_x = far_x
                edge_y = far_y + y_off
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                                 (edge_x, edge_y, 2, 2))
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"],
                                 (edge_x, edge_y, 1, 1))
            # Energy streaks along cone
            for i in range(6):
                streak_t = (phase + i * 0.2) % 1.0
                sx = start_x + int(facing * cone_length * streak_t)
                sy_off = int(math.sin(phase + i) * 4)
                streak_w = int(cone_width_near +
                               (cone_width_far - cone_width_near) * streak_t) - 3
                sy = start_y + sy_off
                pygame.draw.line(surface, _NS_kassadin.PALETTE["void_bright"],
                                 (sx, sy - streak_w),
                                 (sx + facing * 8, sy - streak_w), 2)
                pygame.draw.line(surface, _NS_kassadin.PALETTE["void_shine"],
                                 (sx, sy + streak_w),
                                 (sx + facing * 8, sy + streak_w), 1)
    # ============================================================
    # SKILL E - VOID RIFT (rift at target that explodes)
    # ============================================================
    def _draw_rift_ground(surface, boss, x, y, timer, phase):
        """Rift portal at target location."""
        tx, ty = _NS_kassadin._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Rift forming (grows)
            t = progress / 0.5
            r = int(15 + t * 20)
            # Outer ring shadow
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["rift_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["rift_dark"], 240),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["rift_mid"], 200),
                                (tx - r + 6, ty - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8))
            # Rift edge (bright ring)
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["rift_edge"], 240),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["void_bright"], 180),
                                (tx - r + 1, ty - r // 3 + 1,
                                 r * 2 - 2, r * 2 // 3 - 2), 1)
    def _draw_void_rift_skill(surface, boss, x, y, timer, phase):
        """Rift portal foreground effects + explosion."""
        tx, ty = _NS_kassadin._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Rift active - energy swirling
            t = progress / 0.5
            r = int(15 + t * 20)
            # Rotating void tendrils around rift
            for i in range(12):
                angle = phase * 2 + i * math.pi / 6
                inner_r = 4
                outer_r = r - 2
                sx = tx + int(math.cos(angle) * inner_r)
                sy = ty + int(math.sin(angle) * inner_r * 0.4)
                ex = tx + int(math.cos(angle) * outer_r)
                ey = ty + int(math.sin(angle) * outer_r * 0.4)
                pygame.draw.line(surface, _NS_kassadin.PALETTE["void_mid"],
                                 (sx, sy), (ex, ey), 2)
                pygame.draw.line(surface, _NS_kassadin.PALETTE["void_light"],
                                 (sx, sy), (ex, ey), 1)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"],
                                 (ex, ey, 1, 1))
            # Central void
            for r_i in range(6, 0, -1):
                alpha = _NS_kassadin._alpha(180 * (6 - r_i) / 6)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["rift_darkest"], alpha),
                                       (tx, ty), r_i)
            # Warning particles rising
            for i in range(8):
                p_t = (phase + i * 0.15) % 1.0
                px = tx + int(math.sin(phase + i) * r * 0.6)
                py = ty - int(p_t * 20)
                alpha = _NS_kassadin._alpha(200 * (1 - p_t) * t)
                pygame.draw.rect(surface, (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                 (px, py, 2, 2))
        else:
            # EXPLOSION
            t = (progress - 0.5) / 0.5
            radius = int(20 + t * 45)
            alpha = _NS_kassadin._alpha(255 * (1 - t))
            # Multi-layer explosion
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                   (tx, ty), radius + 5)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                   (tx, ty), radius)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                   (tx, ty), max(1, radius - 8))
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                   (tx, ty), max(1, radius - 16))
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                   (tx, ty), max(1, radius - 24))
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_shine"], alpha),
                                   (tx, ty), max(1, radius // 6))
            # Shockwave rings
            for wave in range(2):
                w_r = int(radius + wave * 10)
                w_alpha = _NS_kassadin._alpha(180 * (1 - t) * (1 - wave * 0.4))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_bright"], w_alpha),
                                       (tx, ty), w_r, 2)
            # Radial burst
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * radius * 1.1)
                ey = ty + int(math.sin(angle_s) * radius * 1.1)
                pygame.draw.line(surface,
                                 (*_NS_kassadin.PALETTE["void_light"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"],
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL R - RIFTWALK (blink teleport + AOE)
    # ============================================================
    def _draw_riftwalk_ground(surface, boss, x, y, timer, pulse):
        """Ground ring at destination."""
        tx, ty = _NS_kassadin._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.7:
            # Arrival ring
            t = (progress - 0.7) / 0.3
            r = int(15 + t * 30)
            alpha = _NS_kassadin._alpha(220 * (1 - t * 0.7))
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                (tx - r + 6, ty - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_riftwalk_skill(surface, boss, x, y, timer, phase):
        """Teleport - departure and arrival effects."""
        tx, ty = _NS_kassadin._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # DEPARTURE - void swallow effect
            t = progress / 0.3
            r = int((1 - t) * 40 + 10)
            # Void collapsing on Kassadin
            for i in range(12):
                angle = phase * 3 + i * math.pi / 6
                dist = r + int(math.sin(phase * 2 + i) * 3)
                sx = x + int(math.cos(angle) * dist)
                sy = y + int(math.sin(angle) * dist * 0.6)
                alpha = _NS_kassadin._alpha(220 * t)
                # Streaks pointing inward
                inner_x = x + int(math.cos(angle) * 5)
                inner_y = y + int(math.sin(angle) * 5 * 0.6)
                pygame.draw.line(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                 (sx, sy), (inner_x, inner_y), 3)
                pygame.draw.line(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                 (sx, sy), (inner_x, inner_y), 2)
                pygame.draw.line(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                 (sx, sy), (inner_x, inner_y), 1)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"], (sx, sy, 2, 2))
            # Central void expanding
            for r_i in range(int(t * 20), 0, -2):
                alpha = _NS_kassadin._alpha(180 * t)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["rift_darkest"], alpha),
                                       (x, y), r_i)
        elif progress < 0.7:
            # MID-TELEPORT - streaks between departure and arrival
            t = (progress - 0.3) / 0.4
            # Line of void energy between start and end
            for i in range(6):
                seg_t = (t + i * 0.1) % 1.0
                sx = int(x + (tx - x) * seg_t)
                sy = int(y + (ty - y) * seg_t)
                alpha = _NS_kassadin._alpha(200 * (1 - abs(seg_t - 0.5) * 2))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                       (sx, sy), 6)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                       (sx, sy), 4)
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                       (sx, sy), 2)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_bright"], (sx, sy, 1, 1))
            # Trail lines
            _NS_kassadin._aaline(surface, (*_NS_kassadin.PALETTE["void_mid"], 100),
                                 (x, y), (tx, ty), 2)
            _NS_kassadin._aaline(surface, (*_NS_kassadin.PALETTE["void_light"], 150),
                                 (x, y), (tx, ty), 1)
        else:
            # ARRIVAL - burst at destination
            t = (progress - 0.7) / 0.3
            radius = int(15 + t * 40)
            alpha = _NS_kassadin._alpha(255 * (1 - t))
            # Explosion at arrival
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_darkest"], alpha),
                                   (tx, ty), radius + 5)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_dark"], alpha),
                                   (tx, ty), radius)
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_mid"], alpha),
                                   (tx, ty), max(1, radius - 8))
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_light"], alpha),
                                   (tx, ty), max(1, radius - 16))
            _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                   (tx, ty), max(1, radius - 24))
            # Radial burst
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * radius * 1.2)
                ey = ty + int(math.sin(angle_s) * radius * 1.2)
                pygame.draw.line(surface,
                                 (*_NS_kassadin.PALETTE["void_bright"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, _NS_kassadin.PALETTE["void_shine"],
                                 (ex, ey, 2, 2))
            # Shockwave
            for wave in range(2):
                w_r = radius + wave * 12
                w_alpha = _NS_kassadin._alpha(200 * (1 - t) * (1 - wave * 0.4))
                _NS_kassadin._aacircle(surface, (*_NS_kassadin.PALETTE["void_bright"], w_alpha),
                                       (tx, ty), w_r, 2)



# ====================================================================
# SHIMORAKH (ROOT OF SHADOWS) - Mini Boss
# ====================================================================

class _NS_shimorakh:
    """Namespace shimorakh - Root of Shadows boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones (aged, pale)
        "skin_shadow": (135, 110, 95),
        "skin_dark": (185, 155, 135),
        "skin_mid": (215, 185, 165),
        "skin_light": (240, 215, 195),
        "skin_shine": (255, 235, 215),
        # Wrinkle/age lines
        "wrinkle": (110, 85, 70),
        # White/grey hair
        "hair_darkest": (55, 55, 60),
        "hair_dark": (110, 110, 115),
        "hair_mid": (170, 170, 175),
        "hair_light": (220, 220, 225),
        "hair_shine": (250, 250, 250),
        # Bandages (off-white/cream)
        "bandage_shadow": (140, 130, 115),
        "bandage_dark": (185, 175, 155),
        "bandage_mid": (215, 205, 185),
        "bandage_light": (240, 232, 215),
        "bandage_shine": (255, 250, 240),
        # Dark robe (near-black grey)
        "robe_darkest": (8, 8, 12),
        "robe_dark": (22, 22, 30),
        "robe_mid": (45, 45, 55),
        "robe_light": (75, 75, 88),
        "robe_edge": (105, 105, 118),
        # Inner kimono (white)
        "kimono_shadow": (170, 170, 170),
        "kimono_dark": (200, 200, 200),
        "kimono_mid": (225, 225, 225),
        "kimono_light": (245, 245, 245),
        "kimono_shine": (255, 255, 255),
        # Left eye (natural, dark)
        "eye_dark": (25, 20, 20),
        "eye_mid": (55, 45, 40),
        "eye_light": (110, 90, 75),
        # Crimson eye (Q skill)
        "crimson_darkest": (50, 5, 5),
        "crimson_dark": (120, 15, 15),
        "crimson_mid": (200, 30, 30),
        "crimson_light": (255, 80, 60),
        "crimson_shine": (255, 180, 150),
        # Green sealing (W skill)
        "seal_darkest": (5, 40, 20),
        "seal_dark": (15, 90, 40),
        "seal_mid": (60, 200, 90),
        "seal_light": (150, 255, 170),
        "seal_shine": (220, 255, 230),
        # Wind (E skill) - white/silver-blue
        "wind_darkest": (50, 60, 75),
        "wind_dark": (110, 130, 155),
        "wind_mid": (180, 200, 225),
        "wind_light": (225, 240, 255),
        "wind_shine": (255, 255, 255),
        # Purple genjutsu (R skill)
        "gen_darkest": (20, 5, 45),
        "gen_dark": (55, 15, 100),
        "gen_mid": (130, 50, 200),
        "gen_light": (200, 130, 255),
        "gen_shine": (240, 210, 255),
        # Shadow beast (D skill)
        "beast_darkest": (10, 8, 15),
        "beast_dark": (35, 30, 40),
        "beast_mid": (70, 60, 75),
        "beast_light": (115, 100, 120),
        "beast_fur": (85, 75, 90),
        "beast_belly": (60, 50, 55),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_shimorakh._clamp(color)
        if _NS_shimorakh.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_shimorakh._clamp(color)
        if _NS_shimorakh.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_shimorakh._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_shimorakh(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_shimorakh._detect_moving(boss)
        _NS_shimorakh._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_shi_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_shimorakh._draw_shadow_aura(surface, x, y, pulse)
        _NS_shimorakh._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_shimorakh._draw_seal_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_shimorakh._draw_mindfetter_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_shimorakh._draw_beast_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Body
        if attacking:
            _NS_shimorakh._draw_body_attack(surface, boss, x, y + float_bob)
        elif moving:
            _NS_shimorakh._draw_body_walk(surface, boss, x, y + float_bob)
        else:
            _NS_shimorakh._draw_body_idle(surface, boss, x, y + float_bob)
        # Q - Crimson rebirth aura (over body)
        if active_skill == "q":
            _NS_shimorakh._draw_crimson_rebirth(surface, boss, x, y + float_bob,
                                                skill_timer, pulse)
        # Foreground FX
        if active_skill == "w":
            _NS_shimorakh._draw_seal_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_shimorakh._draw_windscythe_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_shimorakh._draw_mindfetter_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_shimorakh._draw_shadow_beast_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_shi_previous_timer", 0))
        active = bool(getattr(boss, "_shi_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._shi_attack_active = True
            boss._shi_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._shi_attack_frame = int(getattr(boss, "_shi_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._shi_attack_active = False
            boss._shi_attack_frame = 0
            active = False
        boss._shi_previous_timer = timer
        boss._shi_attack_progress = (
            min(1.0, getattr(boss, "_shi_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_shi_last_x"):
            boss._shi_last_x = boss.x
            boss._shi_last_y = boss.y
            return False
        dx = abs(boss.x - boss._shi_last_x)
        dy = abs(boss.y - boss._shi_last_y)
        boss._shi_last_x = boss.x
        boss._shi_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_shimorakh._draw_shadow(surface, x, y + 50)
        _NS_shimorakh._draw_shadow_mist(surface, x, y + 44, boss.pulse)
        _NS_shimorakh._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_shimorakh._draw_shadow(surface, x + sway, y + 50)
        _NS_shimorakh._draw_shadow_mist(surface, x + sway, y + 44, phase, trail=True,
                                        facing=boss.direction)
        _NS_shimorakh._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_shi_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Cast motion (extends hand forward)
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_shimorakh._draw_shadow(surface, x + lunge, y + 50)
        _NS_shimorakh._draw_shadow_mist(surface, x + lunge, y + 44, boss.pulse,
                                        intense=True)
        _NS_shimorakh._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                                 "attack", progress)
        _NS_shimorakh._draw_basic_shadow_projectile(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw old ninja: dark robe, bandaged head+arm, white hair."""
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.4:
                arm_swing = -int(attack_progress / 0.4 * 8) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                arm_swing = int((-8 + t * 24)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_swing = int(16 * (1 - t)) * facing
        # Back arm (bandaged - his right arm is heavily wrapped)
        _NS_shimorakh._draw_bandaged_arm(surface, cx - facing * 8, cy - 4, facing,
                                         phase, -arm_swing // 2, back=True)
        # Robe (main body)
        _NS_shimorakh._draw_robe(surface, cx, cy, facing, phase, action)
        # Front arm (normal, casting)
        _NS_shimorakh._draw_arm(surface, cx + facing * 4, cy - 4, facing, phase,
                                arm_swing, back=False, action=action,
                                attack_progress=attack_progress)
        # Head
        _NS_shimorakh._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_robe(surface, cx, cy, facing, phase, action):
        """Dark grey robe with white inner kimono."""
        sway = math.sin(phase * 0.7) * 1
        # Main robe shape
        robe_shape = [
            (cx - 13, cy - 8),
            (cx - 15, cy - 2),
            (cx - 17, cy + 8),
            (cx - 18, cy + 20),
            (cx - 15 + int(sway), cy + 30),
            (cx - 4, cy + 34),
            (cx + 4, cy + 34),
            (cx + 15 + int(sway), cy + 30),
            (cx + 18, cy + 20),
            (cx + 17, cy + 8),
            (cx + 15, cy - 2),
            (cx + 13, cy - 8),
        ]
        # Shadow
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in robe_shape])
        # Base darkest
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["robe_darkest"], robe_shape)
        # Dark grey main
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["robe_dark"], [
            (cx - 12, cy - 7),
            (cx - 14, cy - 1),
            (cx - 16, cy + 8),
            (cx - 17, cy + 20),
            (cx - 13, cy + 28),
            (cx - 4, cy + 32),
            (cx + 4, cy + 32),
            (cx + 13, cy + 28),
            (cx + 17, cy + 20),
            (cx + 16, cy + 8),
            (cx + 14, cy - 1),
            (cx + 12, cy - 7),
        ])
        # Mid tone
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["robe_mid"], [
            (cx - 10, cy - 5),
            (cx - 12, cy + 2),
            (cx - 14, cy + 12),
            (cx - 13, cy + 24),
            (cx - 4, cy + 28),
            (cx + 4, cy + 28),
            (cx + 13, cy + 24),
            (cx + 14, cy + 12),
            (cx + 12, cy + 2),
            (cx + 10, cy - 5),
        ])
        # Highlight folds
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_light"],
                         (cx - 7, cy + 2), (cx - 9, cy + 22), 1)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_light"],
                         (cx + 7, cy + 2), (cx + 9, cy + 22), 1)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_edge"],
                         (cx - 8, cy + 8), (cx - 9, cy + 18), 1)
        # WHITE INNER KIMONO (V-neck collar visible in center)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["kimono_shadow"], [
            (cx - 5, cy - 8),
            (cx - 6, cy - 4),
            (cx - 3, cy + 2),
            (cx, cy + 6),
            (cx + 3, cy + 2),
            (cx + 6, cy - 4),
            (cx + 5, cy - 8),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["kimono_dark"], [
            (cx - 4, cy - 7),
            (cx - 5, cy - 3),
            (cx - 2, cy + 2),
            (cx, cy + 5),
            (cx + 2, cy + 2),
            (cx + 5, cy - 3),
            (cx + 4, cy - 7),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["kimono_mid"], [
            (cx - 3, cy - 6),
            (cx - 4, cy - 2),
            (cx - 1, cy + 1),
            (cx + 1, cy + 1),
            (cx + 4, cy - 2),
            (cx + 3, cy - 6),
        ])
        # Bright kimono highlight
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["kimono_light"],
                         (cx - 2, cy - 5), (cx - 2, cy), 1)
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["kimono_shine"],
                         (cx - 2, cy - 4, 1, 1))
        # Collar overlap (left over right - traditional)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_darkest"],
                         (cx - 5, cy - 5), (cx, cy + 4), 1)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_darkest"],
                         (cx + 5, cy - 5), (cx, cy + 4), 1)
        # OBI belt (dark)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["robe_darkest"], [
            (cx - 14, cy + 16),
            (cx - 15, cy + 22),
            (cx + 15, cy + 22),
            (cx + 14, cy + 16),
        ])
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_light"],
                         (cx - 13, cy + 17), (cx + 13, cy + 17), 1)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_darkest"],
                         (cx - 14, cy + 21), (cx + 14, cy + 21), 1)
        # Bottom robe hem highlights
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["robe_light"],
                         (cx - 14, cy + 28), (cx + 14, cy + 28), 1)
        # Legs / bottom (kimono showing through)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["kimono_dark"], [
            (cx - 9, cy + 30),
            (cx - 10, cy + 34),
            (cx + 10, cy + 34),
            (cx + 9, cy + 30),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["kimono_mid"], [
            (cx - 8, cy + 31),
            (cx - 9, cy + 33),
            (cx + 9, cy + 33),
            (cx + 8, cy + 31),
        ])
    def _draw_bandaged_arm(surface, cx, cy, facing, phase, swing, back=True):
        """Bandaged right arm (heavily wrapped in white bandages)."""
        base_angle = math.pi * 0.55 + math.radians(swing)
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.5)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        thickness = 6
        # Shadow of arm
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 2),
                              (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Base bandage color (upper arm)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["bandage_shadow"],
                              (shoulder_x, shoulder_y),
                              (elbow_x, elbow_y), thickness)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["bandage_dark"],
                              (shoulder_x, shoulder_y),
                              (elbow_x, elbow_y), thickness - 1)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["bandage_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 2),
                              (hand_x + 1, hand_y + 2), thickness)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["bandage_shadow"],
                              (elbow_x, elbow_y),
                              (hand_x, hand_y), thickness - 1)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["bandage_dark"],
                              (elbow_x, elbow_y),
                              (hand_x, hand_y), thickness - 2)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["bandage_mid"],
                              (elbow_x, elbow_y - 1),
                              (hand_x, hand_y - 1), max(1, thickness - 4))
        # BANDAGE WRAP LINES (diagonal stripes indicating wrapping)
        # Upper arm wraps
        arm_dx = elbow_x - shoulder_x
        arm_dy = elbow_y - shoulder_y
        arm_len = max(1, math.sqrt(arm_dx * arm_dx + arm_dy * arm_dy))
        perp_x = -arm_dy / arm_len
        perp_y = arm_dx / arm_len
        for i in range(4):
            t = (i + 0.5) / 4
            wx = shoulder_x + arm_dx * t
            wy = shoulder_y + arm_dy * t
            wa_x = wx + perp_x * 3
            wa_y = wy + perp_y * 3
            wb_x = wx - perp_x * 3
            wb_y = wy - perp_y * 3
            pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_shadow"],
                             (int(wa_x), int(wa_y)),
                             (int(wb_x), int(wb_y)), 1)
        # Forearm wraps
        fore_dx = hand_x - elbow_x
        fore_dy = hand_y - elbow_y
        fore_len = max(1, math.sqrt(fore_dx * fore_dx + fore_dy * fore_dy))
        perp_x = -fore_dy / fore_len
        perp_y = fore_dx / fore_len
        for i in range(5):
            t = (i + 0.5) / 5
            wx = elbow_x + fore_dx * t
            wy = elbow_y + fore_dy * t
            wa_x = wx + perp_x * 2.5
            wa_y = wy + perp_y * 2.5
            wb_x = wx - perp_x * 2.5
            wb_y = wy - perp_y * 2.5
            pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_shadow"],
                             (int(wa_x), int(wa_y)),
                             (int(wb_x), int(wb_y)), 1)
        # Bandaged fist (wrapped hand)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 4)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["bandage_shadow"],
                                (hand_x, hand_y), 4)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["bandage_dark"],
                                (hand_x, hand_y), 3)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["bandage_mid"],
                                (hand_x - 1, hand_y - 1), 2)
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["bandage_light"],
                         (hand_x - 1, hand_y - 1, 1, 1))
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Front arm (normal skin, dark sleeve)."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If casting, extend forward for hand seal
        if action == "attack" and attack_progress > 0.4:
            hand_x = cx + facing * (12 + int(attack_progress * 10))
            hand_y = cy - 2 - int(math.sin(attack_progress * math.pi) * 4)
        thickness = 6
        # Shadow
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 2),
                              (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Robe sleeve (dark)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["robe_darkest"],
                              (shoulder_x, shoulder_y),
                              (elbow_x, elbow_y), thickness)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["robe_dark"],
                              (shoulder_x, shoulder_y),
                              (elbow_x, elbow_y), thickness - 1)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["robe_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm (skin visible after sleeve, or full sleeve)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 2),
                              (hand_x + 1, hand_y + 2), thickness)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["robe_darkest"],
                              (elbow_x, elbow_y),
                              (hand_x, hand_y), thickness - 1)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["robe_dark"],
                              (elbow_x, elbow_y),
                              (hand_x, hand_y), thickness - 2)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["robe_mid"],
                              (elbow_x, elbow_y - 1),
                              (hand_x, hand_y - 1), max(1, thickness - 4))
        # Sleeve cuff (wider at hand)
        perp_x = -math.sin(hand_angle)
        perp_y = math.cos(hand_angle)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["robe_darkest"], [
            (hand_x - int(perp_x * 3), hand_y - int(perp_y * 3)),
            (hand_x + int(perp_x * 3), hand_y + int(perp_y * 3)),
            (hand_x + int(perp_x * 3) - facing * 2,
             hand_y + int(perp_y * 3) + 2),
            (hand_x - int(perp_x * 3) - facing * 2,
             hand_y - int(perp_y * 3) + 2),
        ])
        # Skin hand
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["skin_shadow"],
                                (hand_x, hand_y), 3)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["skin_mid"],
                                (hand_x - 1, hand_y - 1), 1)
        # Hand seal glow when casting
        if action == "attack" and attack_progress > 0.3:
            intensity = min(1.0, (attack_progress - 0.3) / 0.3)
            for r in range(int(5 * intensity), 0, -1):
                alpha = _NS_shimorakh._alpha(160 * (5 - r) / 5 * intensity)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_light"], alpha),
                                        (hand_x, hand_y), r)
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_shine"],
                             (hand_x, hand_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Elder head with bandaged right eye, white hair."""
        # Face shape
        face_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy - 6),
            (cx - 6, cy - 10),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy - 2),
            (cx + 5, cy + 3),
            (cx + 1, cy + 5),
            (cx - 3, cy + 5),
            (cx - 6, cy + 3),
        ]
        # Shadow
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["skin_dark"], [
            (cx - 6, cy - 3),
            (cx - 7, cy - 6),
            (cx - 5, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 9),
            (cx + 7, cy - 6),
            (cx + 6, cy - 3),
            (cx + 4, cy + 2),
            (cx, cy + 4),
            (cx - 4, cy + 2),
        ])
        # Lighter mid
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 4, 2, 2))
        # AGE WRINKLES (forehead + cheeks)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["wrinkle"],
                         (cx - 4, cy - 7), (cx - 1, cy - 7), 1)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["wrinkle"],
                         (cx + 1, cy - 7), (cx + 4, cy - 7), 1)
        # Wrinkles under eyes
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["wrinkle"],
                         (cx - 5, cy - 3), (cx - 3, cy - 3), 1)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["wrinkle"],
                         (cx + 3, cy - 3), (cx + 5, cy - 3), 1)
        # LEFT EYE (natural, dark, cold)
        _NS_shimorakh._draw_left_eye(surface, cx - 3 * facing, cy - 5, facing, phase,
                                     action)
        # RIGHT EYE (bandaged/covered with cloth strip diagonally)
        # We'll draw the bandage across the right eye
        # Bandage strip going from top-right down across the eye
        _NS_shimorakh._draw_eye_bandage(surface, cx, cy, facing)
        # Mouth (stoic frown)
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        # Slight downturn (grim)
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["wrinkle"],
                         (cx - 3, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["wrinkle"],
                         (cx + 2, cy + 3, 1, 1))
        # BANDAGED HEAD (wrap over top of head like turban/head wrap)
        _NS_shimorakh._draw_head_bandage(surface, cx, cy, facing, phase)
        # WHITE HAIR (visible on sides and back)
        _NS_shimorakh._draw_hair(surface, cx, cy, facing, phase)
        # SMALL BEARD/STUBBLE (aged look)
        for i in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["hair_dark"],
                             (cx + i, cy + 4, 1, 1))
    def _draw_left_eye(surface, cx, cy, facing, phase, action):
        """Left eye (natural, cold dark)."""
        # Eye socket dark
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["white"],
                         (cx - 1, cy, 3, 1))
        # Pupil (dark, small)
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["eye_dark"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["eye_mid"],
                         (cx + facing, cy, 1, 1))
        # Highlight
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["kimono_shine"],
                         (cx, cy - 1, 1, 1))
    def _draw_eye_bandage(surface, cx, cy, facing):
        """Bandage strip diagonally covering the right eye."""
        # Diagonal strip from top-right of head down across right eye area
        # The right eye is at cx + 3 * facing when facing right
        right_side = facing
        strip_top_x = cx + right_side * 5
        strip_top_y = cy - 12
        strip_bot_x = cx + right_side * 2
        strip_bot_y = cy - 3
        # Draw diagonal bandage strip
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["bandage_shadow"], [
            (strip_top_x - 1, strip_top_y),
            (strip_top_x + 3 * right_side, strip_top_y + 1),
            (strip_bot_x + 3 * right_side, strip_bot_y),
            (strip_bot_x, strip_bot_y - 1),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["bandage_dark"], [
            (strip_top_x, strip_top_y),
            (strip_top_x + 2 * right_side, strip_top_y + 1),
            (strip_bot_x + 2 * right_side, strip_bot_y),
            (strip_bot_x, strip_bot_y - 1),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["bandage_mid"], [
            (strip_top_x + right_side, strip_top_y),
            (strip_top_x + 2 * right_side, strip_top_y + 1),
            (strip_bot_x + 1 * right_side, strip_bot_y - 1),
            (strip_bot_x, strip_bot_y - 1),
        ])
        # Bright edge highlight
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_light"],
                         (strip_top_x + right_side, strip_top_y + 1),
                         (strip_bot_x + right_side, strip_bot_y), 1)
    def _draw_head_bandage(surface, cx, cy, facing, phase):
        """Bandage wrap around top/back of head (like a bandana/turban)."""
        # The bandage wraps around the head
        # Draw as horizontal band across forehead
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["bandage_shadow"], [
            (cx - 8, cy - 12),
            (cx - 9, cy - 10),
            (cx - 8, cy - 8),
            (cx + 8, cy - 8),
            (cx + 9, cy - 10),
            (cx + 8, cy - 12),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["bandage_dark"], [
            (cx - 7, cy - 11),
            (cx - 8, cy - 10),
            (cx - 7, cy - 9),
            (cx + 7, cy - 9),
            (cx + 8, cy - 10),
            (cx + 7, cy - 11),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["bandage_mid"], [
            (cx - 6, cy - 11),
            (cx - 6, cy - 9),
            (cx + 6, cy - 9),
            (cx + 6, cy - 11),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_light"],
                         (cx - 5, cy - 10), (cx + 5, cy - 10), 1)
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["bandage_shine"],
                         (cx - 2, cy - 10, 4, 1))
        # Bandage wrap lines (vertical stripes on the wrap)
        for x_off in (-5, -2, 1, 4):
            pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_shadow"],
                             (cx + x_off, cy - 11), (cx + x_off, cy - 9), 1)
        # Small trailing bandage end (little wisp)
        trail_x = cx - 7 * facing
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["bandage_dark"],
                         (trail_x, cy - 9, 2, 3))
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["bandage_mid"],
                         (trail_x, cy - 9, 1, 3))
    def _draw_hair(surface, cx, cy, facing, phase):
        """White/grey messy hair visible below bandage, on sides and back."""
        # Back hair fills area behind head
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"], [
            (cx - 9, cy - 8),
            (cx - 8, cy - 13),
            (cx - 3, cy - 15),
            (cx + 3, cy - 15),
            (cx + 8, cy - 13),
            (cx + 9, cy - 8),
            (cx + 8, cy - 5),
            (cx - 8, cy - 5),
        ])
        # Base dark grey hair (behind bandage)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["hair_darkest"], [
            (cx - 8, cy - 8),
            (cx - 7, cy - 14),
            (cx - 2, cy - 15),
            (cx + 3, cy - 15),
            (cx + 7, cy - 13),
            (cx + 8, cy - 7),
        ])
        # Mid grey (top of head above bandage)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["hair_dark"], [
            (cx - 7, cy - 12),
            (cx - 5, cy - 14),
            (cx + 3, cy - 14),
            (cx + 6, cy - 12),
            (cx + 6, cy - 11),
            (cx - 6, cy - 11),
        ])
        # Light grey highlights
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["hair_mid"], [
            (cx - 4, cy - 13),
            (cx + 2, cy - 13),
            (cx + 3, cy - 12),
            (cx - 3, cy - 12),
        ])
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["hair_light"],
                         (cx - 2, cy - 13), (cx + 1, cy - 13), 1)
        # Side hair strands (jutting out from below bandage)
        for side_mult in (-1, 1):
            # 2 strands per side
            for i, dy in enumerate((-6, -3)):
                sx = cx + 7 * side_mult
                sy = cy + dy
                end_x = sx + side_mult * 3
                end_y = sy + 1
                _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["hair_darkest"], [
                    (sx, sy - 1),
                    (end_x, end_y),
                    (sx, sy + 1),
                ])
                _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["hair_dark"], [
                    (sx, sy),
                    (int((sx + end_x) / 2), end_y),
                    (sx, sy + 1),
                ])
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["hair_mid"],
                                 (sx + side_mult, sy, 1, 1))
    # ============================================================
    # BASIC RANGED - Shadow Chakra Bullet
    # ============================================================
    def _draw_basic_shadow_projectile(surface, boss, x, y, progress):
        """Small dark chakra projectile."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 6
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_shimorakh._alpha(220 - i * 25)
            size = max(1, 5 - i)
            _NS_shimorakh._aacircle(surface,
                                    (*_NS_shimorakh.PALETTE["gen_darkest"], alpha),
                                    (px, py), size)
            _NS_shimorakh._aacircle(surface,
                                    (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_shimorakh._aacircle(surface,
                                    (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                    (px, py), max(1, size - 2))
        # Main projectile head
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["gen_darkest"], (bx, by), 6)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["gen_dark"], (bx, by), 4)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["gen_mid"], (bx, by), 3)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["gen_light"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_shine"], (bx, by, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(8 + st * 15)
            alpha = _NS_shimorakh._alpha(230 * (1 - st))
            _NS_shimorakh._aacircle(surface,
                                    (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                    (tx, ty), radius, 2)
            _NS_shimorakh._aacircle(surface,
                                    (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                    (tx, ty), max(1, radius - 4), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_shimorakh.PALETTE["gen_light"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # FLOATING SHADOW MIST
    # ============================================================
    def _draw_shadow_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Dark purple/shadow mist below body."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((130, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_shimorakh._alpha((30 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_shimorakh.PALETTE["gen_darkest"], alpha),
                    (65 - radius, 20 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(18, 2, -2):
            alpha = _NS_shimorakh._alpha((18 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                    (65 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 65, cy - 10))
        # Rising dark wisps
        for i in range(6):
            t = (phase * 0.5 + i * 0.15) % 1.0
            px = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            py = cy + 4 - int(t * 22)
            alpha = _NS_shimorakh._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                        (px, py), 3)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                        (px, py - 1), 2)
                pygame.draw.rect(surface,
                                 (*_NS_shimorakh.PALETTE["gen_light"], alpha),
                                 (px, py - 1, 1, 1))
        # Trail behind
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_shimorakh._alpha(140 - i * 25)
                if alpha > 0:
                    _NS_shimorakh._aacircle(surface,
                                            (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                            (sx, sy), max(1, 4 - i))
                    pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_light"],
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 110 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (5, 3, 8, 170), (5, 6, 120, 12))
        pygame.draw.ellipse(shadow, (40, 20, 60, 100), (15, 8, 100, 8))
        surface.blit(shadow, (x - 65, y - 12))
    def _draw_shadow_aura(surface, x, y, phase):
        """Dark purple aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_shimorakh._alpha((85 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_shimorakh._aacircle(aura,
                                        (*_NS_shimorakh.PALETTE["gen_darkest"], alpha),
                                        (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_shimorakh._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_shimorakh._aacircle(aura,
                                        (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                        (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))
        # Floating shadow particles
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 38 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_light"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with dark runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_shimorakh.PALETTE["gen_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_shimorakh.PALETTE["gen_dark"], 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_shimorakh.PALETTE["gen_mid"], 200),
                            (25, 19, 110, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_shimorakh.PALETTE["gen_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_shimorakh.PALETTE["gen_light"],
                                        _NS_shimorakh._alpha(160 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - CRIMSON REBIRTH (restore + red eye flash)
    # ============================================================
    def _draw_crimson_rebirth(surface, boss, x, y, timer, phase):
        """Red magical eye + healing white flash."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Red eye pattern appears above body
            t = progress / 0.4
            eye_y = y - 40
            eye_r = int(18 * t)
            # Outer red glow
            for r in range(eye_r + 8, 0, -2):
                alpha = _NS_shimorakh._alpha(200 * t * (eye_r + 8 - r) / (eye_r + 8))
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["crimson_dark"], alpha),
                                        (x, eye_y), r)
            if eye_r > 3:
                # Concentric red circles (eye pattern - like target/tomoe)
                for ring_i in range(3):
                    r_ring = eye_r - ring_i * 4
                    if r_ring > 1:
                        alpha = _NS_shimorakh._alpha(230 * t)
                        _NS_shimorakh._aacircle(surface,
                                                (*_NS_shimorakh.PALETTE["crimson_darkest"], alpha),
                                                (x, eye_y), r_ring, 2)
                        _NS_shimorakh._aacircle(surface,
                                                (*_NS_shimorakh.PALETTE["crimson_mid"], alpha),
                                                (x, eye_y), r_ring - 1, 1)
                # Inner iris (bright red)
                _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["crimson_dark"],
                                        (x, eye_y), max(2, eye_r // 3))
                _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["crimson_mid"],
                                        (x, eye_y), max(1, eye_r // 4))
                _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["crimson_light"],
                                        (x, eye_y), max(1, eye_r // 6))
                # Bright pupil/tomoe (3 tomoe pattern)
                for i in range(3):
                    tomoe_angle = phase * 2 + i * math.pi * 2 / 3
                    tx_t = x + int(math.cos(tomoe_angle) * eye_r * 0.5)
                    ty_t = eye_y + int(math.sin(tomoe_angle) * eye_r * 0.5)
                    pygame.draw.rect(surface, _NS_shimorakh.PALETTE["crimson_darkest"],
                                     (tx_t, ty_t, 2, 2))
                    pygame.draw.rect(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                                     (tx_t, ty_t, 1, 1))
                # Center dot
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                                 (x - 1, eye_y - 1, 2, 2))
        elif progress < 0.7:
            # WHITE HEALING FLASH (afterimages)
            t = (progress - 0.4) / 0.3
            # Multiple after-images fading
            for i in range(4):
                offset_x = int(math.sin(phase * 3 + i) * 8 * (1 - t))
                alpha = _NS_shimorakh._alpha(180 * (1 - t) * (1 - i / 4))
                # White ghostly silhouette
                for r in range(20, 5, -2):
                    _NS_shimorakh._aacircle(surface,
                                            (*_NS_shimorakh.PALETTE["kimono_shine"],
                                             _NS_shimorakh._alpha(alpha * (20 - r) / 20)),
                                            (x + offset_x, y - 10), r)
            # Rising white particles (healing sparkles)
            for i in range(12):
                p_t = (phase + i * 0.15) % 1.0
                px = x + int(math.sin(phase * 2 + i) * 20)
                py = y - int(p_t * 40) + 10
                alpha = _NS_shimorakh._alpha(220 * (1 - t) * (1 - p_t))
                if alpha > 0:
                    _NS_shimorakh._aacircle(surface,
                                            (*_NS_shimorakh.PALETTE["kimono_shine"], alpha),
                                            (px, py), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_shimorakh.PALETTE["white"], alpha),
                                     (px, py, 1, 1))
        else:
            # Aftermath - subtle red glow lingering
            t = (progress - 0.7) / 0.3
            for r in range(15, 5, -3):
                alpha = _NS_shimorakh._alpha(120 * (1 - t) * (15 - r) / 15)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["crimson_mid"], alpha),
                                        (x, y - 15), r)
    # ============================================================
    # SKILL W - SEALING RITE (green sealing runes)
    # ============================================================
    def _draw_seal_ground(surface, boss, x, y, timer, phase):
        """Green sealing circle on ground at target."""
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.2:
            t = min(1.0, (progress - 0.2) / 0.5)
            r = int(35 * t)
            if r > 3:
                # Outer ring
                pygame.draw.ellipse(surface,
                                    (*_NS_shimorakh.PALETTE["seal_darkest"], 200),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
                # Middle ring
                pygame.draw.ellipse(surface,
                                    (*_NS_shimorakh.PALETTE["seal_dark"], 220),
                                    (tx - r + 4, ty - r // 3 + 2,
                                     r * 2 - 8, r * 2 // 3 - 4), 2)
                # Inner ring
                pygame.draw.ellipse(surface,
                                    (*_NS_shimorakh.PALETTE["seal_mid"], 200),
                                    (tx - r + 10, ty - r // 3 + 4,
                                     r * 2 - 20, r * 2 // 3 - 8), 1)
                # Runes around ring
                for i in range(12):
                    angle = i * math.pi / 6 + phase * 0.3
                    x1 = tx + int(math.cos(angle) * (r - 2))
                    y1 = ty + int(math.sin(angle) * (r - 2) * 0.4)
                    x2 = tx + int(math.cos(angle) * (r + 4))
                    y2 = ty + int(math.sin(angle) * (r + 4) * 0.4)
                    pygame.draw.line(surface, _NS_shimorakh.PALETTE["seal_light"],
                                     (x1, y1), (x2, y2), 1)
                # Central rune symbol (pentagram-like)
                for i in range(5):
                    star_angle = i * math.pi * 2 / 5 - math.pi / 2 + phase * 0.2
                    sx = tx + int(math.cos(star_angle) * (r * 0.5))
                    sy = ty + int(math.sin(star_angle) * (r * 0.5) * 0.4)
                    next_angle = (i + 2) * math.pi * 2 / 5 - math.pi / 2 + phase * 0.2
                    nx = tx + int(math.cos(next_angle) * (r * 0.5))
                    ny = ty + int(math.sin(next_angle) * (r * 0.5) * 0.4)
                    pygame.draw.line(surface, _NS_shimorakh.PALETTE["seal_mid"],
                                     (sx, sy), (nx, ny), 1)
    def _draw_seal_skill(surface, boss, x, y, timer, phase):
        """Sealing spikes rise up at target."""
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Charge - hand seal glow
            t = progress / 0.2
            hand_x = x + boss.direction * 22
            hand_y = y - 4
            for r in range(int(8 * t), 0, -1):
                alpha = _NS_shimorakh._alpha(200 * t)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["seal_mid"], alpha),
                                        (hand_x, hand_y), r)
            _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["seal_light"],
                                    (hand_x, hand_y), 3)
            _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["seal_shine"],
                                    (hand_x, hand_y), 1)
        elif progress < 0.6:
            # SPIKES RISING from seal circle
            t = (progress - 0.2) / 0.4
            num_spikes = 8
            r_ring = 25
            for i in range(num_spikes):
                angle = i * math.pi * 2 / num_spikes + phase * 0.1
                sp_x = tx + int(math.cos(angle) * r_ring)
                sp_base_y = ty + int(math.sin(angle) * r_ring * 0.4)
                sp_h = int(t * 30)
                sp_tip_y = sp_base_y - sp_h
                # Spike shape
                _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"], [
                    (sp_x - 3, sp_base_y + 1),
                    (sp_x + 1, sp_tip_y + 1),
                    (sp_x + 3, sp_base_y + 1),
                ])
                _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["seal_darkest"], [
                    (sp_x - 3, sp_base_y),
                    (sp_x, sp_tip_y),
                    (sp_x + 3, sp_base_y),
                ])
                _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["seal_dark"], [
                    (sp_x - 2, sp_base_y),
                    (sp_x, sp_tip_y),
                    (sp_x + 2, sp_base_y),
                ])
                _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["seal_mid"], [
                    (sp_x - 1, sp_base_y),
                    (sp_x, sp_tip_y),
                    (sp_x + 1, sp_base_y),
                ])
                # Bright glowing tip
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["seal_light"],
                                 (sp_x, sp_tip_y, 1, 2))
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["seal_shine"],
                                 (sp_x, sp_tip_y, 1, 1))
        else:
            # Sealing complete - green stars/chakra released
            t = (progress - 0.6) / 0.4
            for i in range(10):
                p_t = (phase + i * 0.13) % 1.0
                px = tx + int(math.sin(phase * 2 + i) * 30)
                py = ty - int(p_t * 40)
                alpha = _NS_shimorakh._alpha(220 * (1 - t) * (1 - p_t))
                if alpha > 0:
                    # Small star shape
                    pygame.draw.line(surface,
                                     (*_NS_shimorakh.PALETTE["seal_light"], alpha),
                                     (px - 2, py), (px + 2, py), 1)
                    pygame.draw.line(surface,
                                     (*_NS_shimorakh.PALETTE["seal_light"], alpha),
                                     (px, py - 2), (px, py + 2), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_shimorakh.PALETTE["seal_shine"], alpha),
                                     (px, py, 1, 1))
    # ============================================================
    # SKILL E - WIND SCYTHE (crescent wind blade)
    # ============================================================
    def _draw_windscythe_skill(surface, boss, x, y, timer, phase):
        """Wind crescent blade travels in arc to target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        if progress < 0.25:
            # Wind up - gathering wind at hand
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 4
            for r in range(int(10 * t), 0, -1):
                alpha = _NS_shimorakh._alpha(200 * t * (10 - r) / 10)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_dark"], alpha),
                                        (hand_x, hand_y), r)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_mid"], alpha),
                                        (hand_x, hand_y), max(1, r - 2))
            _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["wind_light"],
                                    (hand_x, hand_y), 3)
            _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["wind_shine"],
                                    (hand_x, hand_y), 1)
            # Wind swirl streams
            for i in range(6):
                s_angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(s_angle) * (6 + t * 4))
                sy = hand_y + int(math.sin(s_angle) * (6 + t * 4))
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["wind_light"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["wind_shine"],
                                 (sx, sy, 1, 1))
        else:
            # CRESCENT WIND BLADE traveling to target
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 24
            start_y = y - 6
            cur_x = int(start_x + (tx - start_x) * t)
            cur_y = int(start_y + (ty - start_y) * t)
            # Draw big crescent arc (curved wind blade)
            arc_radius = 30
            # Direction from start to end
            dx = tx - start_x
            dy = ty - start_y
            direction_angle = math.atan2(dy, dx)
            # Crescent spans perpendicular to travel direction
            num_arc = 20
            arc_pts_inner = []
            arc_pts_outer = []
            for i in range(num_arc):
                arc_t = i / (num_arc - 1)
                # Curve angle from -60 to +60 degrees relative to direction
                curve_angle = direction_angle + math.pi / 2 - arc_t * math.pi
                # Inner arc (closer to travel line)
                ix = cur_x + int(math.cos(curve_angle) * (arc_radius - 3))
                iy = cur_y + int(math.sin(curve_angle) * (arc_radius - 3))
                arc_pts_inner.append((ix, iy))
                # Outer arc
                ox = cur_x + int(math.cos(curve_angle) * (arc_radius + 3))
                oy = cur_y + int(math.sin(curve_angle) * (arc_radius + 3))
                arc_pts_outer.append((ox, oy))
            # Draw crescent as thick arc (multi-layer)
            for layer_i, (thickness, color_key) in enumerate([
                (5, "wind_darkest"),
                (3, "wind_dark"),
                (2, "wind_mid"),
                (1, "wind_light"),
            ]):
                for i in range(len(arc_pts_inner) - 1):
                    pygame.draw.line(surface,
                                     _NS_shimorakh.PALETTE[color_key],
                                     arc_pts_inner[i], arc_pts_inner[i + 1],
                                     thickness)
                    pygame.draw.line(surface,
                                     _NS_shimorakh.PALETTE[color_key],
                                     arc_pts_outer[i], arc_pts_outer[i + 1],
                                     thickness)
            # Bright inner glow line (middle of crescent)
            for i in range(len(arc_pts_inner) - 1):
                mx1 = (arc_pts_inner[i][0] + arc_pts_outer[i][0]) // 2
                my1 = (arc_pts_inner[i][1] + arc_pts_outer[i][1]) // 2
                mx2 = (arc_pts_inner[i + 1][0] + arc_pts_outer[i + 1][0]) // 2
                my2 = (arc_pts_inner[i + 1][1] + arc_pts_outer[i + 1][1]) // 2
                pygame.draw.line(surface, _NS_shimorakh.PALETTE["wind_shine"],
                                 (mx1, my1), (mx2, my2), 1)
            # Trail streaks behind
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_shimorakh._alpha(180 - i * 25)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_mid"], alpha),
                                        (px, py), max(1, 4 - i))
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_light"], alpha),
                                        (px, py), max(1, 3 - i))
                pygame.draw.rect(surface,
                                 (*_NS_shimorakh.PALETTE["wind_shine"], alpha),
                                 (px, py, 1, 1))
            # Wind particles/streaks flying off arc
            for i in range(8):
                sp_angle = direction_angle + math.pi / 2 - (i / 7) * math.pi
                sp_x = cur_x + int(math.cos(sp_angle) * (arc_radius + 8))
                sp_y = cur_y + int(math.sin(sp_angle) * (arc_radius + 8))
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["wind_shine"],
                                 (sp_x, sp_y, 1, 1))
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["white"],
                                 (sp_x, sp_y, 1, 1))
            # Impact at target
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 25)
                alpha = _NS_shimorakh._alpha(240 * (1 - st))
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_darkest"], alpha),
                                        (tx, ty), radius, 2)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["wind_light"], alpha),
                                        (tx, ty), max(1, radius - 10), 1)
                # Radial slash burst
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius)
                    pygame.draw.line(surface,
                                     (*_NS_shimorakh.PALETTE["wind_shine"], alpha),
                                     (tx, ty), (ex, ey), 1)
    # ============================================================
    # SKILL R - MIND FETTER (purple genjutsu vortex)
    # ============================================================
    def _draw_mindfetter_ground(surface, boss, x, y, timer, phase):
        """Purple ring on ground at target."""
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(28 * min(1.0, progress * 2.5))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_shimorakh.PALETTE["gen_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_shimorakh.PALETTE["gen_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
    def _draw_mindfetter_skill(surface, boss, x, y, timer, phase):
        """Purple vortex above target - mind control effect."""
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Charge finger point from boss to target (line pointing)
            t = progress / 0.2
            hand_x = x + boss.direction * 24
            hand_y = y - 4
            for r in range(int(8 * t), 0, -1):
                alpha = _NS_shimorakh._alpha(200 * t)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                        (hand_x, hand_y), r)
            _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["gen_light"],
                                    (hand_x, hand_y), 3)
            # Beam line toward target
            beam_end_x = int(hand_x + (tx - hand_x) * t)
            beam_end_y = int(hand_y + (ty - hand_y) * t)
            _NS_shimorakh._aaline(surface,
                                  (*_NS_shimorakh.PALETTE["gen_mid"], 180),
                                  (hand_x, hand_y), (beam_end_x, beam_end_y), 2)
            _NS_shimorakh._aaline(surface,
                                  (*_NS_shimorakh.PALETTE["gen_light"], 220),
                                  (hand_x, hand_y), (beam_end_x, beam_end_y), 1)
        else:
            # PURPLE VORTEX above target
            t = (progress - 0.2) / 0.8
            vortex_x = tx
            vortex_y = ty - 30
            # Spiraling vortex layers
            for spiral_i in range(3):
                spiral_r_base = 15 + spiral_i * 5
                for i in range(24):
                    angle = phase * 3 + i * math.pi / 12 + spiral_i * 0.5
                    layer_r = spiral_r_base - int(math.sin(angle * 2) * 3)
                    sx = vortex_x + int(math.cos(angle) * layer_r)
                    sy = vortex_y + int(math.sin(angle) * layer_r * 0.5)
                    alpha = _NS_shimorakh._alpha(200 - spiral_i * 40)
                    if spiral_i == 0:
                        _NS_shimorakh._aacircle(surface,
                                                (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                                (sx, sy), 3)
                        _NS_shimorakh._aacircle(surface,
                                                (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                                (sx, sy), 2)
                    else:
                        _NS_shimorakh._aacircle(surface,
                                                (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                                (sx, sy), 2)
                        pygame.draw.rect(surface,
                                         (*_NS_shimorakh.PALETTE["gen_light"], alpha),
                                         (sx, sy, 1, 1))
            # Central dark hole (mind trapped)
            for r in range(10, 0, -1):
                alpha = _NS_shimorakh._alpha(180 * (10 - r) / 10)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_darkest"], alpha),
                                        (vortex_x, vortex_y), r)
            # Radial tendrils descending onto target
            for i in range(6):
                angle = phase * 2 + i * math.pi / 3
                start_pt = (vortex_x + int(math.cos(angle) * 5),
                           vortex_y + int(math.sin(angle) * 5 * 0.5))
                end_pt = (tx + int(math.cos(angle) * 8),
                         ty + int(math.sin(angle) * 3))
                alpha = _NS_shimorakh._alpha(180 * math.sin(phase * 3 + i))
                if alpha > 0:
                    pygame.draw.line(surface,
                                     (*_NS_shimorakh.PALETTE["gen_light"], alpha),
                                     start_pt, end_pt, 1)
            # Purple mist around target
            for i in range(8):
                m_angle = phase * 1.5 + i * math.pi / 4
                mx = tx + int(math.cos(m_angle) * 15)
                my = ty + int(math.sin(m_angle) * 8) - 5
                alpha = _NS_shimorakh._alpha(180)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                        (mx, my), 3)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                        (mx, my), 2)
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_light"],
                                 (mx, my, 1, 1))
    # ============================================================
    # SKILL D - SHADOW BEAST (summon dark beast)
    # ============================================================
    def _draw_beast_ground(surface, boss, x, y, timer, phase):
        """Ground summoning circle."""
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Beast appears between boss and target
        beast_x = int(x + (tx - x) * 0.45)
        beast_y = ty
        if progress < 0.2:
            # Summoning circle
            t = progress / 0.2
            r = int(35 * t)
            if r > 3:
                pygame.draw.ellipse(surface,
                                    (*_NS_shimorakh.PALETTE["gen_darkest"], 220),
                                    (beast_x - r, beast_y - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_shimorakh.PALETTE["gen_dark"], 220),
                                    (beast_x - r + 3, beast_y - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                # Runes
                for i in range(8):
                    angle = i * math.pi / 4 + phase * 0.5
                    x1 = beast_x + int(math.cos(angle) * (r - 3))
                    y1 = beast_y + int(math.sin(angle) * (r - 3) * 0.4)
                    x2 = beast_x + int(math.cos(angle) * (r + 3))
                    y2 = beast_y + int(math.sin(angle) * (r + 3) * 0.4)
                    pygame.draw.line(surface, _NS_shimorakh.PALETTE["gen_light"],
                                     (x1, y1), (x2, y2), 1)
    def _draw_shadow_beast_skill(surface, boss, x, y, timer, phase):
        """Draw shadow beast attacking target."""
        tx, ty = _NS_shimorakh._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        beast_x = int(x + (tx - x) * 0.45)
        beast_y = ty
        facing = 1 if tx > x else -1
        if progress < 0.2:
            # Beast rising from portal (dark smoke)
            t = progress / 0.2
            beast_scale = t
            # Purple/dark smoke
            for i in range(12):
                s_angle = i * math.pi / 6
                s_dist = int(20 * (1 - t))
                sx = beast_x + int(math.cos(s_angle) * s_dist)
                sy = beast_y + int(math.sin(s_angle) * s_dist * 0.4) - int(t * 5)
                alpha = _NS_shimorakh._alpha(220 * (1 - t))
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                        (sx, sy), 5)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                        (sx, sy), 3)
            _NS_shimorakh._draw_beast_body(surface, beast_x, beast_y, facing, phase,
                                           beast_scale, action="idle")
        elif progress < 0.85:
            # Beast attacking (roar + lunge)
            phase_beast = phase
            # Alternate between idle and lunge
            action = "attack" if math.sin(phase_beast * 2) > 0 else "idle"
            _NS_shimorakh._draw_beast_body(surface, beast_x, beast_y, facing,
                                           phase_beast, 1.0, action=action)
        else:
            # Beast fading away
            t = (progress - 0.85) / 0.15
            _NS_shimorakh._draw_beast_body(surface, beast_x, beast_y, facing,
                                           phase, 1.0 - t * 0.5, action="idle")
            # Fading purple smoke
            for i in range(10):
                s_angle = i * math.pi / 5
                sx = beast_x + int(math.cos(s_angle) * 25)
                sy = beast_y + int(math.sin(s_angle) * 10)
                alpha = _NS_shimorakh._alpha(200 * (1 - t))
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_dark"], alpha),
                                        (sx, sy), 4)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                        (sx, sy), 2)
    def _draw_beast_body(surface, cx, cy, facing, phase, scale, action="idle"):
        """Draw shadow beast (dark quadruped creature)."""
        s = scale
        if s < 0.1:
            return
        # Bob for breathing
        bob = int(math.sin(phase * 1.5) * 2)
        cy = cy + bob
        # Beast dimensions (large horizontal body)
        body_w = int(35 * s)
        body_h = int(18 * s)
        # BODY (main mass - oval)
        body_shape = [
            (cx - body_w + facing * 3, cy - body_h // 2),
            (cx - body_w, cy - body_h // 4),
            (cx - body_w + 2, cy + body_h // 4),
            (cx - body_w + 5, cy + body_h // 2),
            (cx + body_w - 5, cy + body_h // 2),
            (cx + body_w - 2, cy + body_h // 4),
            (cx + body_w, cy - body_h // 4),
            (cx + body_w - facing * 3, cy - body_h // 2 - 2),
            (cx + facing * (body_w - 10), cy - body_h // 2 - 4),
            (cx - facing * (body_w - 10), cy - body_h // 2 - 4),
        ]
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in body_shape])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_darkest"], body_shape)
        # Body mid tone
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_dark"], [
            (cx - body_w + 3, cy - body_h // 2 + 1),
            (cx - body_w + 2, cy - body_h // 4),
            (cx - body_w + 4, cy + body_h // 2 - 2),
            (cx + body_w - 4, cy + body_h // 2 - 2),
            (cx + body_w - 2, cy - body_h // 4),
            (cx + body_w - 3, cy - body_h // 2 + 1),
        ])
        # Belly (lighter tan)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_belly"], [
            (cx - body_w + 8, cy + 2),
            (cx + body_w - 8, cy + 2),
            (cx + body_w - 10, cy + body_h // 2 - 1),
            (cx - body_w + 10, cy + body_h // 2 - 1),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_mid"], [
            (cx - body_w + 10, cy + 4),
            (cx + body_w - 10, cy + 4),
            (cx + body_w - 12, cy + body_h // 2 - 2),
            (cx - body_w + 12, cy + body_h // 2 - 2),
        ])
        # Fur highlights on back
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_fur"], [
            (cx - body_w + 5, cy - body_h // 2 + 2),
            (cx + body_w - 5, cy - body_h // 2 + 2),
            (cx + body_w - 8, cy),
            (cx - body_w + 8, cy),
        ])
        # Light highlight strip on back
        pygame.draw.line(surface, _NS_shimorakh.PALETTE["beast_light"],
                         (cx - body_w + 6, cy - body_h // 2 + 3),
                         (cx + body_w - 6, cy - body_h // 2 + 3), 1)
        # Fur texture spots (leopard-like darker spots on body)
        for i in range(6):
            sp_x = cx + int(math.sin(i * 1.7) * body_w * 0.6)
            sp_y = cy - 2 + int(math.cos(i * 2.3) * body_h * 0.3)
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["beast_darkest"],
                             (sp_x, sp_y, 2, 2))
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                             (sp_x, sp_y, 1, 1))
        # SPIKES/RIDGES ALONG BACK
        for i in range(5):
            spike_x = cx - body_w + 8 + i * ((body_w * 2 - 16) // 4)
            spike_top = cy - body_h // 2 - 3 - int(math.sin(phase + i) * 1)
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"], [
                (spike_x - 2, cy - body_h // 2 + 1),
                (spike_x, spike_top + 1),
                (spike_x + 2, cy - body_h // 2 + 1),
            ])
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_darkest"], [
                (spike_x - 2, cy - body_h // 2),
                (spike_x, spike_top),
                (spike_x + 2, cy - body_h // 2),
            ])
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_dark"], [
                (spike_x - 1, cy - body_h // 2),
                (spike_x, spike_top),
                (spike_x + 1, cy - body_h // 2),
            ])
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["beast_light"],
                             (spike_x, spike_top, 1, 1))
        # LEGS (4 legs)
        leg_base_y = cy + body_h // 2
        leg_h = int(12 * s)
        for i, leg_off in enumerate((-body_w + 8, -body_w + 16,
                                     body_w - 16, body_w - 8)):
            leg_x = cx + leg_off
            # Lunging animation
            leg_bend = 0
            if action == "attack":
                leg_bend = int(math.sin(phase * 4 + i) * 2)
            leg_end_y = leg_base_y + leg_h + leg_bend
            # Shadow of leg
            _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                                  (leg_x + 1, leg_base_y + 1),
                                  (leg_x + 1, leg_end_y + 1), 5)
            # Main leg
            _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_darkest"],
                                  (leg_x, leg_base_y),
                                  (leg_x, leg_end_y), 4)
            _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_dark"],
                                  (leg_x, leg_base_y),
                                  (leg_x, leg_end_y), 3)
            _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_fur"],
                                  (leg_x - 1, leg_base_y),
                                  (leg_x - 1, leg_end_y), 1)
            # Paw (claws)
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_darkest"], [
                (leg_x - 3, leg_end_y),
                (leg_x + 3, leg_end_y),
                (leg_x + 2, leg_end_y + 2),
                (leg_x - 2, leg_end_y + 2),
            ])
            # Claws
            for c in (-2, 0, 2):
                pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_dark"],
                                 (leg_x + c, leg_end_y + 2),
                                 (leg_x + c, leg_end_y + 3), 1)
                pygame.draw.rect(surface, _NS_shimorakh.PALETTE["bandage_mid"],
                                 (leg_x + c, leg_end_y + 3, 1, 1))
        # HEAD (large, at front of body)
        head_x = cx + facing * (body_w - 5)
        head_y = cy - body_h // 2 + 2
        head_r = int(11 * s)
        # Head shadow
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                                (head_x + 1, head_y + 1), head_r + 1)
        # Head base
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["beast_darkest"],
                                (head_x, head_y), head_r)
        # Head with elongated snout (like a big cat/wolf hybrid)
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_darkest"], [
            (head_x - facing * 2, head_y - 3),
            (head_x + facing * (head_r + 6), head_y - 2),
            (head_x + facing * (head_r + 8), head_y + 2),
            (head_x + facing * (head_r + 6), head_y + 5),
            (head_x - facing * 2, head_y + 5),
        ])
        _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_dark"], [
            (head_x, head_y - 2),
            (head_x + facing * (head_r + 5), head_y - 1),
            (head_x + facing * (head_r + 6), head_y + 2),
            (head_x + facing * (head_r + 5), head_y + 4),
            (head_x, head_y + 4),
        ])
        # Head highlight (top)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["beast_fur"],
                                (head_x - 2, head_y - 2), head_r - 3)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["beast_light"],
                                (head_x - 3, head_y - 3), head_r - 5)
        # EARS (pointed, up)
        for ear_off_x, ear_off_y in ((-4, -8), (3, -8)):
            ear_x = head_x + ear_off_x
            ear_y = head_y + ear_off_y
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["shadow_deep"], [
                (ear_x - 1, ear_y + 3),
                (ear_x + 1, ear_y - 3),
                (ear_x + 3, ear_y + 3),
            ])
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_darkest"], [
                (ear_x, ear_y + 3),
                (ear_x + 1, ear_y - 2),
                (ear_x + 3, ear_y + 3),
            ])
            _NS_shimorakh._poly(surface, _NS_shimorakh.PALETTE["beast_dark"], [
                (ear_x + 1, ear_y + 2),
                (ear_x + 2, ear_y - 1),
                (ear_x + 2, ear_y + 2),
            ])
        # GLOWING PURPLE EYES
        eye_y = head_y - 2
        for eye_off_x in (-3, 3):
            ex = head_x + eye_off_x
            # Glow halo
            for r in range(4, 0, -1):
                alpha = _NS_shimorakh._alpha(200 * (4 - r) / 4)
                _NS_shimorakh._aacircle(surface,
                                        (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                        (ex, eye_y), r)
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_light"],
                             (ex, eye_y, 1, 1))
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_shine"],
                             (ex, eye_y, 1, 1))
        # SNOUT/MOUTH with fangs
        snout_x = head_x + facing * (head_r + 4)
        snout_y = head_y + 2
        # Open mouth if attacking
        mouth_open = 4 if action == "attack" else 1
        # Mouth cavity
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                         (snout_x - facing * 3, snout_y, facing * 5, mouth_open))
        if mouth_open > 2:
            pygame.draw.rect(surface, (60, 20, 30),
                             (snout_x - facing * 2, snout_y + 1,
                              facing * 3, mouth_open - 2))
        # Fangs
        for f_off in (-2, 0, 2):
            fx = snout_x - facing * 3 + facing * f_off
            fy = snout_y
            # Upper fang
            pygame.draw.line(surface, _NS_shimorakh.PALETTE["bandage_mid"],
                             (fx, fy), (fx, fy + mouth_open - 1), 1)
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["bandage_light"],
                             (fx, fy + mouth_open - 1, 1, 1))
        # Nose
        pygame.draw.rect(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                         (snout_x - facing, snout_y - 2, 2, 1))
        # TAIL
        tail_start_x = cx - facing * (body_w - 3)
        tail_start_y = cy - body_h // 4
        # Tail curves back and up with wave
        tail_wave = math.sin(phase * 1.5) * 3
        tail_mid_x = tail_start_x - facing * 8
        tail_mid_y = tail_start_y - 3 + int(tail_wave)
        tail_end_x = tail_start_x - facing * 14
        tail_end_y = tail_start_y - 6 + int(tail_wave * 1.5)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["shadow_deep"],
                              (tail_start_x + 1, tail_start_y + 1),
                              (tail_mid_x + 1, tail_mid_y + 1), 5)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_darkest"],
                              (tail_start_x, tail_start_y),
                              (tail_mid_x, tail_mid_y), 4)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_dark"],
                              (tail_start_x, tail_start_y),
                              (tail_mid_x, tail_mid_y), 3)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_darkest"],
                              (tail_mid_x, tail_mid_y),
                              (tail_end_x, tail_end_y), 3)
        _NS_shimorakh._aaline(surface, _NS_shimorakh.PALETTE["beast_dark"],
                              (tail_mid_x, tail_mid_y),
                              (tail_end_x, tail_end_y), 2)
        # Tail tuft
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["beast_darkest"],
                                (tail_end_x, tail_end_y), 3)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["beast_dark"],
                                (tail_end_x, tail_end_y), 2)
        _NS_shimorakh._aacircle(surface, _NS_shimorakh.PALETTE["beast_fur"],
                                (tail_end_x - 1, tail_end_y - 1), 1)
        # Purple aura around beast
        for i in range(6):
            aura_angle = phase * 0.8 + i * math.pi / 3
            a_x = cx + int(math.cos(aura_angle) * body_w)
            a_y = cy + int(math.sin(aura_angle) * body_h // 2)
            alpha = _NS_shimorakh._alpha(120 + math.sin(phase * 2 + i) * 40)
            _NS_shimorakh._aacircle(surface,
                                    (*_NS_shimorakh.PALETTE["gen_mid"], alpha),
                                    (a_x, a_y), 2)
            pygame.draw.rect(surface, _NS_shimorakh.PALETTE["gen_light"],
                             (a_x, a_y, 1, 1))



# ====================================================================
# SUNAKAGE (SAND SHADOW) - TRUE BOSS
# ====================================================================

class _NS_sunakage:
    """Namespace sunakage - Sand Shadow boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones (pale, ashen)
        "skin_shadow": (155, 130, 120),
        "skin_dark": (205, 180, 165),
        "skin_mid": (235, 210, 195),
        "skin_light": (250, 232, 215),
        "skin_shine": (255, 248, 238),
        # Rust red hair (mystical, weathered)
        "hair_darkest": (55, 15, 8),
        "hair_dark": (120, 35, 20),
        "hair_mid": (180, 60, 30),
        "hair_light": (220, 100, 55),
        "hair_shine": (250, 150, 100),
        # Rune tattoo (dark red mystical)
        "tattoo_dark": (90, 15, 10),
        "tattoo_mid": (170, 30, 20),
        "tattoo_light": (230, 70, 45),
        # Dark eye rings (cursed sleepless)
        "eyering_dark": (30, 15, 20),
        "eyering_mid": (60, 30, 35),
        # Robe (dark red/maroon, weathered)
        "robe_darkest": (25, 8, 10),
        "robe_dark": (65, 18, 22),
        "robe_mid": (110, 30, 35),
        "robe_light": (160, 55, 60),
        "robe_shine": (200, 90, 90),
        # Undershirt (dark grey/black)
        "shirt_darkest": (10, 8, 12),
        "shirt_dark": (25, 22, 30),
        "shirt_mid": (50, 45, 60),
        "shirt_light": (80, 75, 90),
        # SAND (main theme! golden-brown)
        "sand_darkest": (60, 40, 15),
        "sand_dark": (120, 85, 35),
        "sand_mid": (200, 155, 70),
        "sand_light": (240, 200, 110),
        "sand_bright": (255, 225, 155),
        "sand_shine": (255, 245, 210),
        # Sand vessel (darker sand color, tan-brown)
        "gourd_darkest": (50, 35, 15),
        "gourd_dark": (95, 70, 30),
        "gourd_mid": (160, 120, 55),
        "gourd_light": (210, 170, 90),
        "gourd_shine": (245, 220, 150),
        # Rope/straps
        "rope_dark": (60, 40, 20),
        "rope_mid": (120, 85, 40),
        "rope_light": (180, 140, 80),
        # Belt
        "belt_dark": (35, 25, 15),
        "belt_mid": (75, 55, 30),
        # Amber-green eyes (mystical)
        "eye_dark": (20, 55, 45),
        "eye_mid": (80, 150, 130),
        "eye_light": (160, 220, 200),
        "eye_shine": (220, 250, 235),
        # Dust particles (light gold)
        "dust_dark": (100, 75, 35),
        "dust_mid": (180, 140, 65),
        "dust_light": (240, 210, 130),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sunakage._clamp(color)
        if _NS_sunakage.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_sunakage._clamp(color)
        if _NS_sunakage.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_sunakage._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_sunakage(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sunakage._detect_moving(boss)
        _NS_sunakage._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_sun_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_sunakage._draw_sand_aura(surface, x, y, pulse)
        _NS_sunakage._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_sunakage._draw_sand_claw_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sunakage._draw_desert_tomb_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Body (always floating on sand)
        if attacking:
            _NS_sunakage._draw_body_attack(surface, boss, x, y + float_bob)
        elif moving:
            _NS_sunakage._draw_body_walk(surface, boss, x, y + float_bob)
        else:
            _NS_sunakage._draw_body_idle(surface, boss, x, y + float_bob)
        # E - Sand shield dome (over body)
        if active_skill == "e":
            _NS_sunakage._draw_sand_bulwark_dome(surface, boss, x, y + float_bob,
                                                 skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_sunakage._draw_sand_surge_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sunakage._draw_sand_claw_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sunakage._draw_desert_tomb_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sun_previous_timer", 0))
        active = bool(getattr(boss, "_sun_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._sun_attack_active = True
            boss._sun_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._sun_attack_frame = int(getattr(boss, "_sun_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._sun_attack_active = False
            boss._sun_attack_frame = 0
            active = False
        boss._sun_previous_timer = timer
        boss._sun_attack_progress = (
            min(1.0, getattr(boss, "_sun_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_sun_last_x"):
            boss._sun_last_x = boss.x
            boss._sun_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sun_last_x)
        dy = abs(boss.y - boss._sun_last_y)
        boss._sun_last_x = boss.x
        boss._sun_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_sunakage._draw_shadow(surface, x, y + 50)
        _NS_sunakage._draw_sand_mist(surface, x, y + 44, boss.pulse)
        _NS_sunakage._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_sunakage._draw_shadow(surface, x + sway, y + 50)
        _NS_sunakage._draw_sand_mist(surface, x + sway, y + 44, phase, trail=True,
                                     facing=boss.direction)
        _NS_sunakage._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_sun_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Cast motion (extends hand forward - ranged caster)
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_sunakage._draw_shadow(surface, x + lunge, y + 50)
        _NS_sunakage._draw_sand_mist(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_sunakage._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                                "attack", progress)
        _NS_sunakage._draw_basic_sand_projectile(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw Sunakage body: sand vessel (back), robe, head with hair."""
        # Order: back arm → gourd (back) → robe → front arm (casting) → head
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.4:
                arm_swing = -int(attack_progress / 0.4 * 8) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                arm_swing = int((-8 + t * 24)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_swing = int(16 * (1 - t)) * facing
        # Back arm (crossed over chest in idle)
        if action == "idle":
            _NS_sunakage._draw_arm_crossed(surface, cx, cy, facing, phase, back=True)
        else:
            _NS_sunakage._draw_arm(surface, cx - facing * 8, cy - 4, facing, phase,
                                   -arm_swing // 2, back=True)
        # Sand vessel on back
        _NS_sunakage._draw_sand_vessel(surface, cx - facing * 12, cy - 6, facing, phase)
        # Robe
        _NS_sunakage._draw_robe(surface, cx, cy, facing, phase, action)
        # Front arm
        if action == "idle":
            _NS_sunakage._draw_arm_crossed(surface, cx, cy, facing, phase, back=False)
        else:
            _NS_sunakage._draw_arm(surface, cx + facing * 4, cy - 4, facing, phase,
                                   arm_swing, back=False, action=action,
                                   attack_progress=attack_progress)
        # Head
        _NS_sunakage._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_sand_vessel(surface, cx, cy, facing, phase):
        """Large sand vessel on back (with runic emblem, no kanji)."""
        # Main vessel shape (rounded)
        vessel_shape = [
            (cx - 8, cy - 10),
            (cx - 10, cy - 5),
            (cx - 11, cy + 3),
            (cx - 10, cy + 12),
            (cx - 6, cy + 18),
            (cx + 2, cy + 20),
            (cx + 8, cy + 18),
            (cx + 12, cy + 12),
            (cx + 13, cy + 3),
            (cx + 12, cy - 5),
            (cx + 10, cy - 10),
            (cx + 4, cy - 13),
            (cx - 2, cy - 13),
        ]
        # Shadow
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in vessel_shape])
        # Base darkest
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["gourd_darkest"], vessel_shape)
        # Mid tone
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["gourd_dark"], [
            (cx - 7, cy - 9),
            (cx - 9, cy - 4),
            (cx - 10, cy + 3),
            (cx - 9, cy + 11),
            (cx - 5, cy + 17),
            (cx + 2, cy + 19),
            (cx + 7, cy + 17),
            (cx + 11, cy + 11),
            (cx + 12, cy + 3),
            (cx + 11, cy - 4),
            (cx + 9, cy - 9),
            (cx + 3, cy - 12),
            (cx - 1, cy - 12),
        ])
        # Lighter mid
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["gourd_mid"], [
            (cx - 5, cy - 7),
            (cx - 7, cy - 2),
            (cx - 8, cy + 4),
            (cx - 7, cy + 10),
            (cx - 3, cy + 15),
            (cx + 2, cy + 17),
            (cx + 6, cy + 15),
            (cx + 9, cy + 10),
            (cx + 10, cy + 4),
            (cx + 9, cy - 2),
            (cx + 7, cy - 7),
            (cx + 2, cy - 10),
            (cx, cy - 10),
        ])
        # Highlight (side lit)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["gourd_light"], [
            (cx - 3, cy - 5),
            (cx - 5, cy),
            (cx - 5, cy + 8),
            (cx - 2, cy + 13),
            (cx + 2, cy + 13),
            (cx + 3, cy),
            (cx + 2, cy - 6),
        ])
        # Bright shine spot
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["gourd_shine"],
                               (cx - 3, cy - 2), 2)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_shine"],
                         (cx - 3, cy - 3, 1, 1))
        # Top opening (dark hole where sand comes out)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shadow_deep"], [
            (cx - 3, cy - 12),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 3, cy - 12),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["gourd_darkest"], [
            (cx - 2, cy - 11),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 2, cy - 11),
        ])
        # Sand overflow at top
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_mid"],
                         (cx - 2, cy - 11, 4, 1))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_light"],
                         (cx - 1, cy - 11, 2, 1))
        # Straps/ropes around vessel (X pattern)
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["rope_dark"],
                             (cx - 10, cy + 2), (cx + 12, cy + 2), 2)
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["rope_mid"],
                             (cx - 10, cy + 2), (cx + 12, cy + 2), 1)
        pygame.draw.line(surface, _NS_sunakage.PALETTE["rope_light"],
                         (cx - 8, cy + 1), (cx + 10, cy + 1), 1)
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["rope_dark"],
                             (cx, cy - 8), (cx, cy + 18), 2)
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["rope_mid"],
                             (cx, cy - 8), (cx, cy + 18), 1)
        pygame.draw.line(surface, _NS_sunakage.PALETTE["rope_light"],
                         (cx - 1, cy - 6), (cx - 1, cy + 16), 1)
        # RUNIC EMBLEM on vessel (diamond rune, bukan kanji)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["gourd_darkest"],
                         (cx - 3, cy + 6, 6, 6))
        # Diamond rune outer
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shadow_deep"], [
            (cx, cy + 7),
            (cx + 2, cy + 9),
            (cx, cy + 11),
            (cx - 2, cy + 9),
        ])
        # Diamond rune inner
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["sand_dark"], [
            (cx, cy + 8),
            (cx + 1, cy + 9),
            (cx, cy + 10),
            (cx - 1, cy + 9),
        ])
        # Center dot
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_bright"],
                         (cx, cy + 9, 1, 1))
        # Sand tendrils floating out of vessel top
        for i in range(3):
            wisp_t = (phase * 0.5 + i * 0.3) % 1.0
            wx = cx + int(math.sin(phase + i) * 4)
            wy = cy - 12 - int(wisp_t * 12)
            alpha = _NS_sunakage._alpha(200 * (1 - wisp_t))
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                   (wx, wy), 3)
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                   (wx, wy), 2)
            pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                             (wx, wy, 1, 1))
            pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_bright"], alpha),
                             (wx, wy - 1, 1, 1))
    def _draw_robe(surface, cx, cy, facing, phase, action):
        """Dark red maroon weathered robe."""
        sway = math.sin(phase * 0.7) * 1
        # Main robe shape
        robe_shape = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 2),
            (cx - 16, cy + 8),
            (cx - 17, cy + 20),
            (cx - 14 + int(sway), cy + 30),
            (cx - 4, cy + 34),
            (cx + 4, cy + 34),
            (cx + 14 + int(sway), cy + 30),
            (cx + 17, cy + 20),
            (cx + 16, cy + 8),
            (cx + 14, cy - 2),
            (cx + 12, cy - 8),
        ]
        # Shadow
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in robe_shape])
        # Base darkest
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["robe_darkest"], robe_shape)
        # Mid maroon
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["robe_dark"], [
            (cx - 11, cy - 7),
            (cx - 13, cy - 1),
            (cx - 15, cy + 8),
            (cx - 16, cy + 20),
            (cx - 12, cy + 28),
            (cx - 4, cy + 32),
            (cx + 4, cy + 32),
            (cx + 12, cy + 28),
            (cx + 16, cy + 20),
            (cx + 15, cy + 8),
            (cx + 13, cy - 1),
            (cx + 11, cy - 7),
        ])
        # Mid tone
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["robe_mid"], [
            (cx - 9, cy - 5),
            (cx - 11, cy + 2),
            (cx - 13, cy + 12),
            (cx - 12, cy + 24),
            (cx - 4, cy + 28),
            (cx + 4, cy + 28),
            (cx + 12, cy + 24),
            (cx + 13, cy + 12),
            (cx + 11, cy + 2),
            (cx + 9, cy - 5),
        ])
        # Highlight folds
        pygame.draw.line(surface, _NS_sunakage.PALETTE["robe_light"],
                         (cx - 6, cy + 2), (cx - 8, cy + 22), 1)
        pygame.draw.line(surface, _NS_sunakage.PALETTE["robe_light"],
                         (cx + 6, cy + 2), (cx + 8, cy + 22), 1)
        pygame.draw.line(surface, _NS_sunakage.PALETTE["robe_shine"],
                         (cx - 6, cy + 6), (cx - 7, cy + 18), 1)
        # Dark undershirt visible at collar and center
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shirt_darkest"], [
            (cx - 4, cy - 7),
            (cx - 5, cy - 3),
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 5, cy - 3),
            (cx + 4, cy - 7),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shirt_dark"], [
            (cx - 3, cy - 6),
            (cx - 4, cy - 2),
            (cx - 2, cy + 3),
            (cx + 2, cy + 3),
            (cx + 4, cy - 2),
            (cx + 3, cy - 6),
        ])
        pygame.draw.line(surface, _NS_sunakage.PALETTE["shirt_light"],
                         (cx, cy - 5), (cx, cy + 2), 1)
        # Belt (wide, dark leather)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["belt_dark"], [
            (cx - 14, cy + 16),
            (cx - 15, cy + 22),
            (cx + 15, cy + 22),
            (cx + 14, cy + 16),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["belt_mid"], [
            (cx - 13, cy + 17),
            (cx - 14, cy + 21),
            (cx + 14, cy + 21),
            (cx + 13, cy + 17),
        ])
        # Belt buckle
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["gourd_mid"],
                         (cx - 3, cy + 18, 6, 3))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["gourd_light"],
                         (cx - 2, cy + 18, 4, 2))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["gourd_shine"],
                         (cx - 1, cy + 18, 2, 1))
        # Legs (dark pants below robe)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shirt_darkest"], [
            (cx - 8, cy + 28),
            (cx - 9, cy + 34),
            (cx - 4, cy + 34),
            (cx - 3, cy + 28),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shirt_darkest"], [
            (cx + 3, cy + 28),
            (cx + 4, cy + 34),
            (cx + 9, cy + 34),
            (cx + 8, cy + 28),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shirt_dark"], [
            (cx - 7, cy + 29),
            (cx - 8, cy + 33),
            (cx - 5, cy + 33),
            (cx - 4, cy + 29),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shirt_dark"], [
            (cx + 4, cy + 29),
            (cx + 5, cy + 33),
            (cx + 8, cy + 33),
            (cx + 7, cy + 29),
        ])
    def _draw_arm_crossed(surface, cx, cy, facing, phase, back=False):
        """Arm crossed over chest (idle pose)."""
        if back:
            shoulder_x = cx - facing * 8
        else:
            shoulder_x = cx + facing * 8
        shoulder_y = cy - 4
        elbow_x = shoulder_x - facing * (2 if back else 4)
        elbow_y = shoulder_y + 4
        hand_x = cx + facing * (3 if back else -3)
        hand_y = cy + 4
        thickness = 6 if not back else 5
        color_main = _NS_sunakage.PALETTE["robe_darkest"] if back \
            else _NS_sunakage.PALETTE["robe_dark"]
        color_mid = _NS_sunakage.PALETTE["robe_dark"] if back \
            else _NS_sunakage.PALETTE["robe_mid"]
        # Shadow
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 2),
                             (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm
        _NS_sunakage._aaline(surface, color_main,
                             (shoulder_x, shoulder_y),
                             (elbow_x, elbow_y), thickness)
        _NS_sunakage._aaline(surface, color_mid,
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm (crossed)
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 2),
                             (hand_x + 1, hand_y + 2), thickness)
        _NS_sunakage._aaline(surface, color_main,
                             (elbow_x, elbow_y),
                             (hand_x, hand_y), thickness - 1)
        _NS_sunakage._aaline(surface, color_mid,
                             (elbow_x, elbow_y - 1),
                             (hand_x, hand_y - 1), max(1, thickness - 3))
        # Hand
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["shadow_deep"],
                               (hand_x + 1, hand_y + 1), 3)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_shadow"],
                               (hand_x, hand_y), 3)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_dark"],
                               (hand_x, hand_y), 2)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_mid"],
                               (hand_x - 1, hand_y - 1), 1)
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Draw arm extended (casting)."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.55
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If casting, extend forward
        if action == "attack" and not back and attack_progress > 0.4:
            hand_x = cx + facing * (12 + int(attack_progress * 10))
            hand_y = cy - 2 - int(math.sin(attack_progress * math.pi) * 4)
        thickness = 6 if not back else 5
        color_main = _NS_sunakage.PALETTE["robe_darkest"] if back \
            else _NS_sunakage.PALETTE["robe_dark"]
        color_mid = _NS_sunakage.PALETTE["robe_dark"] if back \
            else _NS_sunakage.PALETTE["robe_mid"]
        # Shadow
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 2),
                             (elbow_x + 1, elbow_y + 2), thickness + 1)
        _NS_sunakage._aaline(surface, color_main,
                             (shoulder_x, shoulder_y),
                             (elbow_x, elbow_y), thickness)
        _NS_sunakage._aaline(surface, color_mid,
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm
        _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 2),
                             (hand_x + 1, hand_y + 2), thickness)
        _NS_sunakage._aaline(surface, color_main,
                             (elbow_x, elbow_y),
                             (hand_x, hand_y), thickness - 1)
        _NS_sunakage._aaline(surface, color_mid,
                             (elbow_x, elbow_y - 1),
                             (hand_x, hand_y - 1), max(1, thickness - 3))
        # Hand
        if not back:
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 3)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_shadow"],
                                   (hand_x, hand_y), 3)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 2)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_mid"],
                                   (hand_x - 1, hand_y - 1), 1)
            # Sand energy in palm when casting
            if action == "attack" and attack_progress > 0.3:
                intensity = min(1.0, (attack_progress - 0.3) / 0.3)
                for r in range(int(6 * intensity), 0, -1):
                    alpha = _NS_sunakage._alpha(180 * (6 - r) / 6 * intensity)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                           (hand_x, hand_y), r)
                _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_light"],
                                       (hand_x, hand_y), 2)
                pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_shine"],
                                 (hand_x, hand_y, 1, 1))
        else:
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["shadow_deep"],
                                   (hand_x, hand_y), 3)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["skin_shadow"],
                                   (hand_x, hand_y), 2)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with rust red hair, rune tattoo, dark eye rings, green eyes."""
        # Face shape
        face_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy - 6),
            (cx - 6, cy - 10),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy - 2),
            (cx + 5, cy + 3),
            (cx + 1, cy + 5),
            (cx - 3, cy + 5),
            (cx - 6, cy + 3),
        ]
        # Shadow
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shadow_deep"],
                           [(px + 1, py + 2) for px, py in face_shape])
        # Base skin (pale)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["skin_dark"], [
            (cx - 6, cy - 3),
            (cx - 7, cy - 6),
            (cx - 5, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 9),
            (cx + 7, cy - 6),
            (cx + 6, cy - 3),
            (cx + 4, cy + 2),
            (cx, cy + 4),
            (cx - 4, cy + 2),
        ])
        # Lighter mid
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["skin_shine"],
                         (cx - 3 * facing, cy - 4, 1, 1))
        # RUNE TATTOO (mystical circle/triangle, bukan kanji)
        _NS_sunakage._draw_rune_tattoo(surface, cx - 4 * facing, cy - 9, facing)
        # Dark eye rings (cursed insomnia)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eyering_dark"],
                         (cx - 5, cy - 6, 5, 4))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eyering_mid"],
                         (cx - 5, cy - 6, 5, 3))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eyering_dark"],
                         (cx + 1, cy - 6, 5, 4))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eyering_mid"],
                         (cx + 1, cy - 6, 5, 3))
        # Eyes (amber-green, mystical cold)
        _NS_sunakage._draw_eye(surface, cx - 3, cy - 5, facing, phase, action)
        _NS_sunakage._draw_eye(surface, cx + 3, cy - 5, facing, phase, action)
        # Mouth (flat, stoic)
        pygame.draw.line(surface, _NS_sunakage.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        # RUST RED SPIKY HAIR
        _NS_sunakage._draw_hair(surface, cx, cy, facing, phase)
    def _draw_rune_tattoo(surface, cx, cy, facing):
        """Mystical rune tattoo - circle with triangle (bukan kanji)."""
        # Outer circle ring
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["tattoo_dark"],
                               (cx, cy + 2), 3, 1)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["tattoo_mid"],
                               (cx, cy + 2), 2, 1)
        # Triangle inside (desert peak symbol - pointing up)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["tattoo_dark"], [
            (cx, cy),
            (cx - 2, cy + 3),
            (cx + 2, cy + 3),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["tattoo_mid"], [
            (cx, cy + 1),
            (cx - 1, cy + 3),
            (cx + 1, cy + 3),
        ])
        # Center bright dot
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["tattoo_light"],
                         (cx, cy + 2, 1, 1))
    def _draw_eye(surface, cx, cy, facing, phase, action):
        """Amber-green mystical eyes."""
        # Sclera (white)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["white"],
                         (cx - 1, cy, 3, 1))
        # Iris (green amber)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eye_dark"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eye_mid"],
                         (cx + facing, cy, 1, 1))
        # Highlight
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["eye_shine"],
                         (cx, cy - 1, 1, 1))
        if action == "attack":
            # Slight glow when attacking
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["eye_light"], (cx, cy, 1, 1))
    def _draw_hair(surface, cx, cy, facing, phase):
        """Rust red spiky messy hair."""
        cy_h = cy - 22  # hair position (above face)
        # Back hair base (fills area behind head)
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["shadow_deep"], [
            (cx - 9, cy_h - 8),
            (cx - 8, cy_h - 13),
            (cx - 3, cy_h - 15),
            (cx + 3, cy_h - 15),
            (cx + 8, cy_h - 13),
            (cx + 9, cy_h - 8),
            (cx + 8, cy_h - 5),
            (cx - 8, cy_h - 5),
        ])
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_darkest"], [
            (cx - 8, cy_h - 8),
            (cx - 7, cy_h - 13),
            (cx - 2, cy_h - 14),
            (cx + 3, cy_h - 14),
            (cx + 7, cy_h - 12),
            (cx + 8, cy_h - 7),
        ])
        # Main dark red
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_dark"], [
            (cx - 7, cy_h - 9),
            (cx - 6, cy_h - 12),
            (cx - 1, cy_h - 13),
            (cx + 3, cy_h - 13),
            (cx + 6, cy_h - 11),
            (cx + 7, cy_h - 8),
        ])
        # Bright red mid
        _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_mid"], [
            (cx - 5, cy_h - 10),
            (cx - 3, cy_h - 12),
            (cx + 2, cy_h - 12),
            (cx + 5, cy_h - 10),
            (cx + 4, cy_h - 8),
            (cx - 3, cy_h - 8),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_sunakage.PALETTE["hair_light"],
                         (cx - 2, cy_h - 11), (cx + 2, cy_h - 11), 1)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["hair_shine"],
                         (cx, cy_h - 12, 1, 1))
        # SPIKY BANGS (messy tufts on forehead)
        for spike_x_off, spike_h in [(-5, -2), (-3, -3), (0, -4), (2, -3), (4, -2)]:
            sx = cx + spike_x_off
            sy = cy_h - 5
            _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx, sy + spike_h),
                (sx + 2, sy),
            ])
            _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
            _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_mid"], [
                (sx, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
        # Side messy spikes
        for side_mult in (-1, 1):
            for spike_i, (dy, spike_len) in enumerate([(-8, 3), (-4, 4), (-1, 3)]):
                sx = cx + 7 * side_mult
                sy = cy_h + dy
                end_x = sx + side_mult * spike_len
                end_y = sy - 1
                _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_darkest"], [
                    (sx, sy - 2),
                    (end_x, end_y - 1),
                    (end_x, end_y + 1),
                    (sx, sy + 2),
                ])
                _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_dark"], [
                    (sx, sy - 1),
                    (end_x, end_y),
                    (sx, sy + 1),
                ])
                _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_mid"], [
                    (sx, sy),
                    (int((sx + end_x) / 2), end_y),
                    (sx, sy + 1),
                ])
        # TOP SPIKES
        top_sway = math.sin(phase * 0.6) * 1
        for spike_i, (spike_x_off, spike_h) in enumerate([
            (-5, -5), (-3, -7), (-1, -8), (1, -8), (3, -7), (5, -5),
        ]):
            sx = cx + spike_x_off + int(top_sway * (spike_i - 2.5) / 3)
            sy = cy_h - 13
            end_y = sy + spike_h
            _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx, end_y),
                (sx + 2, sy),
            ])
            _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx, end_y + 1),
                (sx + 1, sy),
            ])
            _NS_sunakage._poly(surface, _NS_sunakage.PALETTE["hair_mid"], [
                (sx, sy),
                (sx, end_y + 1),
                (sx + 1, sy),
            ])
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["hair_light"],
                             (sx, end_y + 1, 1, 1))
            if spike_i in (2, 3):
                pygame.draw.rect(surface, _NS_sunakage.PALETTE["hair_shine"],
                                 (sx, end_y + 1, 1, 1))
    # ============================================================
    # BASIC RANGED - Small Sand Projectile
    # ============================================================
    def _draw_basic_sand_projectile(surface, boss, x, y, progress):
        """Small sand bullet projectile."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_sunakage._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 6
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Sand trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_sunakage._alpha(200 - i * 22)
            size = max(1, 5 - i)
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                   (px, py), size)
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                   (px, py), max(1, size - 2))
            # Scattered sand grains
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 8 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 8 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_bright"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Main projectile head
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_darkest"], (bx, by), 6)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_dark"], (bx, by), 5)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_mid"], (bx, by), 3)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_light"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_bright"], (bx, by, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(8 + st * 15)
            alpha = _NS_sunakage._alpha(230 * (1 - st))
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                   (tx, ty), radius, 2)
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                   (tx, ty), max(1, radius - 4), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # FLOATING SAND MIST
    # ============================================================
    def _draw_sand_mist(surface, cx, cy, phase, trail=False, facing=1,
                       intense=False):
        """Sand cloud below body."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((150, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base sand cloud
        for radius in range(35, 3, -3):
            alpha = _NS_sunakage._alpha((35 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                    (75 - radius, 22 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(22, 3, -2):
            alpha = _NS_sunakage._alpha((22 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                    (75 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        for radius in range(14, 2, -2):
            alpha = _NS_sunakage._alpha((14 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                    (75 - radius, 22 - radius // 5,
                     radius * 2, max(2, radius // 4))
                )
        surface.blit(mist, (cx - 75, cy - 12))
        # Swirling sand particles
        for i in range(10):
            angle = phase * 2 + i * math.pi / 5
            radius = 12 + int(math.sin(phase * 3 + i) * 4)
            px = cx + int(math.cos(angle) * radius)
            py = cy + 4 + int(math.sin(angle) * radius * 0.3)
            alpha = _NS_sunakage._alpha(200 * strength)
            pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_bright"], alpha),
                             (px, py, 1, 1))
        # Sand grains rising
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 24 + i * 7 + int(math.sin(phase + i) * 3)
            py = cy + 4 - int(t * 20)
            alpha = _NS_sunakage._alpha(180 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_shine"], alpha),
                                 (px, py - 1, 1, 1))
        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_sunakage._alpha(160 - i * 25)
                if alpha > 0:
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                           (sx, sy), max(1, 5 - i))
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                           (sx, sy), max(1, 3 - i))
                    pygame.draw.rect(surface,
                                     (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 26), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 120 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (5, 3, 2, 170), (5, 6, 130, 14))
        pygame.draw.ellipse(shadow, (60, 40, 15, 100), (15, 8, 110, 10))
        surface.blit(shadow, (x - 70, y - 13))
    def _draw_sand_aura(surface, x, y, phase):
        """Golden sand aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_sunakage._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_sunakage._aacircle(aura,
                                       (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_sunakage._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_sunakage._aacircle(aura,
                                       (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_sunakage._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_sunakage._aacircle(aura,
                                       (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Swirling sand particles
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground sand ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_sunakage.PALETTE["sand_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_sunakage.PALETTE["sand_dark"], 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_sunakage.PALETTE["sand_mid"], 200),
                            (25, 19, 110, 16), 1)
        # Runes around
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_sunakage.PALETTE["sand_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_sunakage.PALETTE["sand_bright"],
                                        _NS_sunakage._alpha(160 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - SAND SURGE (large sand wave)
    # ============================================================
    def _draw_sand_surge_skill(surface, boss, x, y, timer, phase):
        """Large sand wave surging forward."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sunakage._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in palm
            t = progress / 0.2
            hand_x = x + facing * 22
            hand_y = y - 4
            cr = int(4 + t * 8)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_sunakage._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                       (hand_x, hand_y), r)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_mid"],
                                   (hand_x, hand_y), max(1, cr - 2))
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_light"],
                                   (hand_x, hand_y), max(1, cr - 4))
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_shine"],
                                   (hand_x, hand_y), max(1, cr - 6))
            # Sand grains swirling
            for i in range(6):
                s_angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(s_angle) * (cr + 3))
                sy = hand_y + int(math.sin(s_angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_bright"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 24
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # BIG SAND SURGE trail (wide, wave-like)
            for i in range(12):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_sunakage._alpha(240 - i * 20)
                size = max(2, 12 - i)
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                       (px, py), size)
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                       (px, py), max(1, size - 3))
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                       (px, py), max(1, size - 5))
                # Scattered sand grains
                if i < 6:
                    for s in range(3):
                        s_off = math.sin(t * 10 + i * 2 + s) * (size + 3)
                        c_off = math.cos(t * 10 + i * 2 + s) * (size + 3)
                        spark_x = px + int(s_off)
                        spark_y = py + int(c_off)
                        pygame.draw.rect(surface,
                                         (*_NS_sunakage.PALETTE["sand_bright"], alpha),
                                         (spark_x, spark_y, 1, 1))
                        pygame.draw.rect(surface,
                                         (*_NS_sunakage.PALETTE["sand_shine"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Massive head
            for r in range(18, 3, -2):
                alpha = _NS_sunakage._alpha(100 * (18 - r) / 18)
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                       (bx, by), r)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_darkest"], (bx, by), 12)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_dark"], (bx, by), 9)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_mid"], (bx, by), 6)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_light"], (bx, by), 3)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_shine"], (bx, by), 1)
            # Impact (bury target)
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_sunakage._alpha(240 * (1 - st))
                # Sand pile buries target
                pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                    (tx - radius, ty - radius // 2,
                                     radius * 2, radius))
                pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                    (tx - radius + 3, ty - radius // 2 + 2,
                                     radius * 2 - 6, radius - 4))
                pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                    (tx - radius + 8, ty - radius // 2 + 4,
                                     radius * 2 - 16, radius - 8))
                # Radial dust burst
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.6)
                    pygame.draw.rect(surface,
                                     (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_sunakage.PALETTE["sand_shine"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - SAND CLAW (giant claw from ground)
    # ============================================================
    def _draw_sand_claw_ground(surface, boss, x, y, timer, phase):
        """Ground crack where claw emerges."""
        tx, ty = _NS_sunakage._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Ground crack forming
            t = progress / 0.3
            crack_w = int(30 * t)
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["shadow_deep"], 220),
                                (tx - crack_w, ty - 4, crack_w * 2, 8))
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_darkest"], 200),
                                (tx - crack_w + 2, ty - 3, crack_w * 2 - 4, 6))
    def _draw_sand_claw_skill(surface, boss, x, y, timer, phase):
        """Giant sand claw rises from ground and slams."""
        tx, ty = _NS_sunakage._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Claw emerging (rising up from ground)
            t = progress / 0.3
            hand_scale = t
            hand_y = ty + int((1 - t) * 20)
            # Debris/dust
            for i in range(8):
                d_angle = i * math.pi / 4
                d_dist = 25 * t
                dx = tx + int(math.cos(d_angle) * d_dist)
                dy = ty + int(math.sin(d_angle) * d_dist * 0.4) - int(t * 10)
                alpha = _NS_sunakage._alpha(200 * (1 - t))
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                       (dx, dy), 4)
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                       (dx, dy), 3)
            _NS_sunakage._draw_giant_claw(surface, tx, hand_y, phase, hand_scale,
                                          grabbing=False)
        elif progress < 0.7:
            # Claw grabs/holds
            _NS_sunakage._draw_giant_claw(surface, tx, ty, phase, 1.0, grabbing=True)
        else:
            # Claw crushing/sinking
            t = (progress - 0.7) / 0.3
            hand_y = ty + int(t * 15)
            # Sand fragments falling
            for i in range(12):
                d_angle = i * math.pi / 6
                d_dist = 30
                dx = tx + int(math.cos(d_angle) * d_dist)
                dy = ty + int(math.sin(d_angle) * d_dist * 0.4) + int(t * 10)
                alpha = _NS_sunakage._alpha(200 * (1 - t))
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                       (dx, dy), 3)
                pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                 (dx, dy, 1, 1))
    def _draw_giant_claw(surface, cx, cy, phase, scale, grabbing=False):
        """Draw giant sand claw (5-fingered)."""
        s = scale
        # Palm (main mass)
        palm_r = int(22 * s)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["shadow_deep"],
                               (cx + 2, cy + 2), palm_r)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_darkest"], (cx, cy), palm_r)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_dark"], (cx, cy),
                               palm_r - 3)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_mid"],
                               (cx - 3, cy - 3), palm_r - 7)
        # Highlight
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_light"],
                               (cx - 5, cy - 5), palm_r - 12)
        _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_bright"],
                               (cx - 6, cy - 6), palm_r // 4)
        pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_shine"],
                         (cx - 7, cy - 7, 2, 2))
        # Cracks/texture
        for i in range(3):
            c_angle = i * math.pi / 3 + phase * 0.1
            cx1 = cx + int(math.cos(c_angle) * (palm_r - 6))
            cy1 = cy + int(math.sin(c_angle) * (palm_r - 6))
            cx2 = cx + int(math.cos(c_angle) * (palm_r - 2))
            cy2 = cy + int(math.sin(c_angle) * (palm_r - 2))
            pygame.draw.line(surface, _NS_sunakage.PALETTE["sand_darkest"],
                             (cx1, cy1), (cx2, cy2), 1)
        # 5 FINGERS
        finger_angles = [-math.pi * 0.6, -math.pi * 0.35, -math.pi * 0.1,
                         math.pi * 0.15, math.pi * 0.4]
        for i, base_angle in enumerate(finger_angles):
            if grabbing:
                # Fingers curled inward
                curl_amount = math.pi * 0.3
                finger_angle = base_angle
                finger_len = int(15 * s)
                bx = cx + int(math.cos(finger_angle) * (palm_r - 2))
                by = cy + int(math.sin(finger_angle) * (palm_r - 2))
                mid_angle = base_angle + curl_amount * (1 if i < 2 else -1)
                mx = bx + int(math.cos(mid_angle) * finger_len * 0.6)
                my = by + int(math.sin(mid_angle) * finger_len * 0.6)
                tip_angle = mid_angle + curl_amount * 0.7 * (1 if i < 2 else -1)
                tx_f = mx + int(math.cos(tip_angle) * finger_len * 0.4)
                ty_f = my + int(math.sin(tip_angle) * finger_len * 0.4)
            else:
                # Fingers extended
                finger_len = int(20 * s)
                bx = cx + int(math.cos(base_angle) * (palm_r - 2))
                by = cy + int(math.sin(base_angle) * (palm_r - 2))
                mx = bx + int(math.cos(base_angle) * finger_len * 0.5)
                my = by + int(math.sin(base_angle) * finger_len * 0.5)
                tx_f = bx + int(math.cos(base_angle) * finger_len)
                ty_f = by + int(math.sin(base_angle) * finger_len)
            thickness = max(3, int(7 * s))
            # Finger segments
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["shadow_deep"],
                                 (bx + 1, by + 1), (mx + 1, my + 1), thickness + 1)
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["sand_darkest"],
                                 (bx, by), (mx, my), thickness)
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["sand_dark"],
                                 (bx, by), (mx, my), thickness - 2)
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["sand_mid"],
                                 (bx, by - 1), (mx, my - 1), max(1, thickness - 4))
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["shadow_deep"],
                                 (mx + 1, my + 1), (tx_f + 1, ty_f + 1), thickness)
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["sand_darkest"],
                                 (mx, my), (tx_f, ty_f), thickness - 1)
            _NS_sunakage._aaline(surface, _NS_sunakage.PALETTE["sand_dark"],
                                 (mx, my), (tx_f, ty_f), thickness - 3)
            # Knuckle joint
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_dark"],
                                   (mx, my), max(2, thickness // 2))
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_mid"],
                                   (mx - 1, my - 1), max(1, thickness // 2 - 1))
            # Sharp fingertip (claw-like)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_darkest"],
                                   (tx_f, ty_f), 3)
            _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_dark"],
                                   (tx_f, ty_f), 2)
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_light"],
                             (tx_f, ty_f, 1, 1))
        # Sand falling
        for i in range(6):
            f_t = (phase * 0.7 + i * 0.15) % 1.0
            fx = cx - 15 + i * 6
            fy = cy + 15 + int(f_t * 20)
            alpha = _NS_sunakage._alpha(200 * (1 - f_t))
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                   (fx, fy), 2)
            pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                             (fx, fy, 1, 1))
    # ============================================================
    # SKILL E - SAND BULWARK (dome around body)
    # ============================================================
    def _draw_sand_bulwark_dome(surface, boss, x, y, timer, phase):
        """Sand shield dome around body."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(phase * 2) * 2
        r = 40 + int(breath)
        dome_surf = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)
        # Dome layers
        for i in range(3):
            offset = i * 2
            alpha_val = 200 - i * 40
            _NS_sunakage._aacircle(dome_surf,
                                   (*_NS_sunakage.PALETTE["sand_darkest"], alpha_val),
                                   center, r - offset, 3)
            _NS_sunakage._aacircle(dome_surf,
                                   (*_NS_sunakage.PALETTE["sand_dark"], alpha_val),
                                   center, r - offset - 1, 2)
            _NS_sunakage._aacircle(dome_surf,
                                   (*_NS_sunakage.PALETTE["sand_mid"], alpha_val),
                                   center, r - offset - 2, 1)
        # Solid sand filling (translucent)
        for r_i in range(r - 4, r - 15, -2):
            alpha = _NS_sunakage._alpha(80 * (r - r_i) / r)
            _NS_sunakage._aacircle(dome_surf, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                   center, r_i)
        # Sand grain texture
        for i in range(30):
            angle = phase * 0.3 + i * math.pi / 15
            grain_r = r - 3 + int(math.sin(phase + i) * 2)
            gx = center[0] + int(math.cos(angle) * grain_r)
            gy = center[1] + int(math.sin(angle) * grain_r)
            pygame.draw.rect(dome_surf, _NS_sunakage.PALETTE["sand_mid"], (gx, gy, 2, 2))
            pygame.draw.rect(dome_surf, _NS_sunakage.PALETTE["sand_light"], (gx, gy, 1, 1))
        # Bright highlight spot
        highlight_x = center[0] - r // 2
        highlight_y = center[1] - r // 2
        _NS_sunakage._aacircle(dome_surf, _NS_sunakage.PALETTE["sand_bright"],
                               (highlight_x, highlight_y), 6)
        _NS_sunakage._aacircle(dome_surf, _NS_sunakage.PALETTE["sand_shine"],
                               (highlight_x - 1, highlight_y - 1), 3)
        pygame.draw.rect(dome_surf, _NS_sunakage.PALETTE["white"],
                         (highlight_x - 2, highlight_y - 2, 2, 2))
        # Swirling sand around dome
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * (r + 3))
            sy = center[1] + int(math.sin(angle) * (r + 3))
            pygame.draw.rect(dome_surf, _NS_sunakage.PALETTE["sand_bright"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(dome_surf, _NS_sunakage.PALETTE["sand_shine"], (sx, sy, 1, 1))
        surface.blit(dome_surf, (x - r - 15, y - r - 15))
        # Deflected projectiles FX
        for i in range(4):
            deflect_t = (phase * 0.8 + i * 0.25) % 1.0
            if deflect_t > 0.7:
                d_angle = i * math.pi / 2 + phase * 0.5
                d_r = r + int((1 - deflect_t) * 20)
                dx = x + int(math.cos(d_angle) * d_r)
                dy = y + int(math.sin(d_angle) * d_r)
                pygame.draw.line(surface, _NS_sunakage.PALETTE["belt_dark"],
                                 (dx, dy),
                                 (dx + int(math.cos(d_angle) * 8),
                                  dy + int(math.sin(d_angle) * 8)), 2)
                pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_bright"],
                                 (dx, dy, 2, 2))
    # ============================================================
    # SKILL R - DESERT TOMB (massive sand vortex)
    # ============================================================
    def _draw_desert_tomb_ground(surface, boss, x, y, timer, phase):
        """Ground vortex."""
        tx, ty = _NS_sunakage._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Ground vortex forming
            t = progress / 0.3
            r = int(30 * t)
            alpha = _NS_sunakage._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        elif progress > 0.7:
            # Aftermath crater
            t = (progress - 0.7) / 0.3
            r = int(40)
            alpha = _NS_sunakage._alpha(220 * (1 - t))
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10))
    def _draw_desert_tomb_skill(surface, boss, x, y, timer, phase):
        """Massive swirling sand tomb tornado around target."""
        tx, ty = _NS_sunakage._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Sand gathering upward from ground
            t = progress / 0.3
            for i in range(20):
                angle = phase * 3 + i * math.pi / 10
                pillar_h = int(t * 60)
                spiral_r = int((1 - i / 20) * 30) + int(math.sin(phase * 2 + i) * 3)
                sx = tx + int(math.cos(angle) * spiral_r)
                sy_base = ty
                for h in range(pillar_h):
                    sy = sy_base - h
                    if sy < ty - pillar_h:
                        break
                    if h % 3 == 0:
                        alpha = _NS_sunakage._alpha(200 * t * (1 - h / pillar_h))
                        _NS_sunakage._aacircle(surface,
                                               (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                               (sx, sy), 3)
                        pygame.draw.rect(surface,
                                         (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                         (sx, sy, 1, 1))
        elif progress < 0.7:
            # FULL TOMB - tall tornado
            _NS_sunakage._draw_sand_tornado(surface, tx, ty, phase, 1.0)
            # Debris orbiting
            for i in range(15):
                orb_angle = phase * 4 + i * math.pi / 7
                orb_r = 30 + int(math.sin(phase * 3 + i) * 5)
                orb_h = int((math.sin(phase * 2 + i * 0.5) + 1) * 30)
                ox = tx + int(math.cos(orb_angle) * orb_r)
                oy = ty - orb_h + int(math.sin(orb_angle) * orb_r * 0.3)
                _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_dark"], (ox, oy), 3)
                _NS_sunakage._aacircle(surface, _NS_sunakage.PALETTE["sand_mid"], (ox, oy), 2)
                pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_bright"],
                                 (ox, oy, 1, 1))
        else:
            # Tomb collapsing (CRUSHING PHASE)
            t = (progress - 0.7) / 0.3
            _NS_sunakage._draw_sand_tornado(surface, tx, ty, phase, 1.0 - t * 0.7)
            # Compression flash
            if t < 0.5:
                flash_alpha = _NS_sunakage._alpha(220 * (1 - t * 2))
                for r in range(30, 5, -3):
                    alpha = _NS_sunakage._alpha(flash_alpha * (30 - r) / 30)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_bright"], alpha),
                                           (tx, ty - 15), r)
            # Sand debris falling
            for i in range(10):
                d_angle = i * math.pi / 5
                d_dist = 25 + int(t * 15)
                dx = tx + int(math.cos(d_angle) * d_dist)
                dy = ty + int(math.sin(d_angle) * d_dist * 0.5) + int(t * 20)
                alpha = _NS_sunakage._alpha(220 * (1 - t))
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                       (dx, dy), 3)
                _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                       (dx, dy), 2)
                pygame.draw.rect(surface, (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                 (dx, dy, 1, 1))
    def _draw_sand_tornado(surface, cx, cy, phase, intensity):
        """Draw swirling sand tornado."""
        tornado_h = 70
        num_layers = 14
        for layer_i in range(num_layers):
            layer_t = layer_i / num_layers
            layer_y = cy - int(layer_t * tornado_h)
            width_factor = math.sin(layer_t * math.pi) * 0.5 + 0.7
            layer_w = int(30 * width_factor * intensity)
            for i in range(int(20 * intensity)):
                angle = phase * 4 + i * math.pi * 2 / 20 + layer_i * 0.3
                sx = cx + int(math.cos(angle) * layer_w)
                sy = layer_y + int(math.sin(angle) * layer_w * 0.3)
                d = abs(math.cos(angle))
                alpha = _NS_sunakage._alpha(200 * intensity)
                if d > 0.7:  # Front-facing (bright)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                           (sx, sy), 3)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_bright"], alpha),
                                           (sx, sy), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_sunakage.PALETTE["sand_shine"], alpha),
                                     (sx, sy, 1, 1))
                elif d > 0.4:  # Side
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_mid"], alpha),
                                           (sx, sy), 3)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_light"], alpha),
                                           (sx, sy), 2)
                else:  # Back-facing (dark)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                           (sx, sy), 3)
                    _NS_sunakage._aacircle(surface,
                                           (*_NS_sunakage.PALETTE["sand_dark"], alpha),
                                           (sx, sy), 2)
        # Central dark core (target trapped)
        core_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(int(20 * intensity * core_pulse), 0, -2):
            alpha = _NS_sunakage._alpha(160 * intensity * (20 - r) / 20)
            _NS_sunakage._aacircle(surface, (*_NS_sunakage.PALETTE["sand_darkest"], alpha),
                                   (cx, cy - tornado_h // 2), r)
        # Top swirling cap
        for i in range(10):
            angle = phase * 3 + i * math.pi / 5
            top_x = cx + int(math.cos(angle) * 18 * intensity)
            top_y = cy - tornado_h + int(math.sin(angle) * 6)
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_bright"], (top_x, top_y, 2, 2))
            pygame.draw.rect(surface, _NS_sunakage.PALETTE["sand_shine"], (top_x, top_y, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_akaroth(surface, boss, x, y):
    """Entry point akaroth."""
    return _NS_akaroth.draw_akaroth(surface, boss, x, y)


def draw_kassadin(surface, boss, x, y):
    """Entry point kassadin."""
    return _NS_kassadin.draw_kassadin(surface, boss, x, y)


def draw_shimorakh(surface, boss, x, y):
    """Entry point shimorakh."""
    return _NS_shimorakh.draw_shimorakh(surface, boss, x, y)


def draw_sunakage(surface, boss, x, y):
    """Entry point sunakage."""
    return _NS_sunakage.draw_sunakage(surface, boss, x, y)
