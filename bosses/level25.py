"""
bosses/level25.py - Semua boss Level 25

Berisi:
  - grimjack   (mini boss - MELEE cackling fiend assassin, void/poison)
  - morvaeth   (mini boss - MELEE crimson reaver assassin)
  - vulkareth  (mini boss - MELEE emberborn titan, dual form lava)
  - okeanora   (TRUE BOSS - MELEE deepborn oracle priestess + kraken)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _gj_ (grimjack), _mv_ (morvaeth), _vk_ (vulkareth),
    _ok_ (okeanora) sudah unik. Nama fungsi namespace (_draw_*)
    TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# GRIMJACK (CACKLING FIEND) - Mini Boss
# ====================================================================

class _NS_grimjack:
    """Namespace grimjack - Demon Jester mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # White mask/face (ghostly pale)
        "mask_darkest": (95, 85, 90),
        "mask_dark": (160, 150, 155),
        "mask_mid": (215, 205, 210),
        "mask_light": (240, 235, 240),
        "mask_shine": (255, 250, 255),
        # Red parts (hat, outfit)
        "red_darkest": (55, 10, 15),
        "red_dark": (125, 20, 30),
        "red_mid": (190, 40, 55),
        "red_light": (235, 80, 90),
        "red_shine": (255, 160, 170),
        # Purple parts (hat, outfit)
        "purple_darkest": (30, 10, 55),
        "purple_dark": (65, 25, 105),
        "purple_mid": (115, 50, 175),
        "purple_light": (170, 100, 225),
        "purple_shine": (220, 175, 250),
        # Void/magic purple (skills, teleport)
        "void_darkest": (25, 5, 45),
        "void_dark": (60, 15, 105),
        "void_mid": (125, 40, 195),
        "void_light": (185, 100, 245),
        "void_hot": (225, 165, 255),
        "void_shine": (245, 220, 255),
        "void_white": (255, 245, 255),
        # Green poison
        "poison_darkest": (15, 40, 8),
        "poison_dark": (40, 100, 20),
        "poison_mid": (100, 190, 40),
        "poison_light": (170, 240, 80),
        "poison_hot": (220, 255, 140),
        "poison_shine": (245, 255, 210),
        # Steel dagger blade
        "blade_darkest": (30, 30, 35),
        "blade_dark": (85, 85, 95),
        "blade_mid": (155, 155, 165),
        "blade_light": (210, 210, 220),
        "blade_shine": (250, 250, 255),
        # Gold accents (bells, dagger hilt)
        "gold_dark": (110, 75, 15),
        "gold_mid": (200, 155, 40),
        "gold_light": (245, 210, 90),
        "gold_shine": (255, 240, 170),
        # Eye (glowing evil red-orange, empty)
        "eye_glow": (255, 120, 40),
        "eye_hot": (255, 200, 100),
        "eye_socket": (5, 2, 8),
        # Mouth (creepy red grin)
        "mouth_dark": (60, 5, 15),
        "mouth_mid": (150, 20, 30),
        "mouth_light": (220, 60, 70),
        # Leather (belt, boots)
        "leather_dark": (40, 25, 15),
        "leather_mid": (85, 55, 30),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grimjack._clamp(color)
        if _NS_grimjack.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_grimjack._clamp(color)
        if _NS_grimjack.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_grimjack._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_grimjack._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_grimjack._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_grimjack(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_grimjack._detect_moving(boss)
        _NS_grimjack._update_gj_attack_anim(boss)
        attacking = (
            getattr(boss, "_gj_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind.
        _NS_grimjack._draw_void_aura(surface, x, y, pulse)
        _NS_grimjack._draw_ground_void_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_grimjack._draw_deceive_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grimjack._draw_jackbox_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_grimjack._draw_hallucinate_ground(surface, boss, x, y, skill_timer, pulse)
        # Determine body visibility (Q makes invisible).
        invisibility_alpha = 255
        if active_skill == "q":
            duration = 45
            progress = max(0.0, min(1.0, 1 - skill_timer / duration))
            # Fade out first, then reappear.
            if progress < 0.4:
                invisibility_alpha = int(255 * (1 - progress / 0.4))
            elif progress < 0.7:
                invisibility_alpha = 30  # invisible
            else:
                invisibility_alpha = int(255 * ((progress - 0.7) / 0.3))
        # Body.
        if invisibility_alpha > 20:
            if attacking:
                _NS_grimjack._draw_gj_attack(surface, boss, x, y, invisibility_alpha)
            elif moving:
                _NS_grimjack._draw_gj_float(surface, boss, x, y, invisibility_alpha)
            else:
                _NS_grimjack._draw_gj_idle(surface, boss, x, y, invisibility_alpha)
        # Foreground FX.
        if active_skill == "q":
            _NS_grimjack._draw_deceive_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grimjack._draw_jackbox_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_grimjack._draw_twoshiv_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_grimjack._draw_hallucinate_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_gj_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gj_previous_timer", 0))
        active = bool(getattr(boss, "_gj_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._gj_attack_active = True
            boss._gj_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._gj_attack_frame = int(
                getattr(boss, "_gj_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._gj_attack_active = False
            boss._gj_attack_frame = 0
            active = False
        boss._gj_previous_timer = timer
        boss._gj_attack_progress = (
            min(1.0, getattr(boss, "_gj_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_gj_last_x"):
            boss._gj_last_x = boss.x
            boss._gj_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gj_last_x)
        dy = abs(boss.y - boss._gj_last_y)
        boss._gj_last_x = boss.x
        boss._gj_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_gj_idle(surface, boss, x, y, alpha=255):
        bob = int(math.sin(boss.pulse * 0.7) * 4) - 5
        _NS_grimjack._draw_shadow(surface, x, y + 50)
        _NS_grimjack._draw_void_particles(surface, x, y + 42, boss.pulse)
        _NS_grimjack._draw_gj_body(surface, x, y + bob,
                       boss.direction, boss.pulse, "idle", 0, alpha)
    def _draw_gj_float(surface, boss, x, y, alpha=255):
        """Floating movement (jester hovers spookily)."""
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.0) * 6) - 7
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_grimjack._draw_shadow(surface, x + sway, y + 50, moving=True)
        _NS_grimjack._draw_void_particles(surface, x + sway, y + 42, phase,
                              moving=True, facing=boss.direction)
        _NS_grimjack._draw_gj_body(surface, x + sway, y + bob,
                       boss.direction, phase, "float", 0, alpha)
    def _draw_gj_attack(surface, boss, x, y, alpha=255):
        """Dagger stab/slash."""
        progress = getattr(boss, "_gj_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3) - 5
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * boss.direction
            lift = int(3 - t * 6) - 5
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3) - 5
        _NS_grimjack._draw_shadow(surface, x + lunge, y + 50)
        _NS_grimjack._draw_void_particles(surface, x + lunge, y + 42, boss.pulse,
                              intense=True)
        _NS_grimjack._draw_gj_body(surface, x + lunge, y + lift,
                       boss.direction, boss.pulse, "attack", progress, alpha)
        if 0.35 <= progress < 0.75:
            _NS_grimjack._draw_dagger_slash(surface, boss, x + lunge, y + lift,
                              progress)
    # ============================================================
    # BODY (Demon Jester)
    # ============================================================
    def _draw_gj_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0, alpha=255):
        """Draw demon jester."""
        # For invisibility, draw all to alpha surface then blit.
        if alpha < 255:
            # Create temp surface.
            temp = pygame.Surface((120, 100), pygame.SRCALPHA)
            local_cx = 60
            local_cy = 50
            _NS_grimjack._draw_gj_body_impl(temp, local_cx, local_cy, facing, phase,
                                action, attack_progress)
            temp.set_alpha(alpha)
            surface.blit(temp, (cx - 60, cy - 50))
        else:
            _NS_grimjack._draw_gj_body_impl(surface, cx, cy, facing, phase,
                                action, attack_progress)
    def _draw_gj_body_impl(surface, cx, cy, facing, phase, action,
                             attack_progress=0):
        """Actual body draw implementation."""
        # Legs.
        _NS_grimjack._draw_gj_legs(surface, cx, cy + 18, facing, phase, action)
        # Torso (jester outfit).
        _NS_grimjack._draw_gj_torso(surface, cx, cy, facing, phase, action)
        # Back arm with dagger.
        _NS_grimjack._draw_back_dagger_arm(surface, cx, cy + 4, facing, phase,
                               action, attack_progress)
        # Head (jester mask + hat).
        _NS_grimjack._draw_gj_head(surface, cx, cy - 20, facing, phase, action)
        # Front arm with dagger (foreground).
        _NS_grimjack._draw_front_dagger_arm(surface, cx, cy + 4, facing, phase,
                                action, attack_progress)
    def _draw_gj_legs(surface, cx, cy, facing, phase, action):
        """Jester legs with checkered pants."""
        for side_i, side in enumerate((-1, 1)):
            leg_x = cx + side * 5
            leg_top_y = cy - 4
            leg_bot_y = cy + 4
            # Alternate red/purple stripes.
            first_color = _NS_grimjack.PALETTE["red_dark"] if side < 0 else _NS_grimjack.PALETTE["purple_dark"]
            first_mid = _NS_grimjack.PALETTE["red_mid"] if side < 0 else _NS_grimjack.PALETTE["purple_mid"]
            # Leg (checkered).
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                    (leg_x + 1, leg_top_y + 1),
                    (leg_x + 1, leg_bot_y + 1), 5)
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                    (leg_x, leg_top_y), (leg_x, leg_bot_y), 4)
            _NS_grimjack._aaline(surface, first_color,
                    (leg_x, leg_top_y), (leg_x, leg_bot_y), 3)
            _NS_grimjack._aaline(surface, first_mid,
                    (leg_x - 1, leg_top_y), (leg_x - 1, leg_bot_y), 1)
            # Checkered pattern segments.
            for cy_off in range(-3, 5, 2):
                # Alternate.
                if cy_off % 4 == -3 or cy_off % 4 == 1:
                    color = _NS_grimjack.PALETTE["purple_dark"] if side < 0 else _NS_grimjack.PALETTE["red_dark"]
                    color_mid = _NS_grimjack.PALETTE["purple_mid"] if side < 0 else _NS_grimjack.PALETTE["red_mid"]
                    pygame.draw.rect(surface, color,
                                     (leg_x - 1, leg_top_y + cy_off + 3, 3, 1))
                    pygame.draw.rect(surface, color_mid,
                                     (leg_x - 1, leg_top_y + cy_off + 3, 2, 1))
            # Boot (dark leather).
            foot_x = leg_x
            foot_y = leg_bot_y
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"], [
                (foot_x - 3, foot_y),
                (foot_x + 4 * facing, foot_y),
                (foot_x + 4 * facing, foot_y + 3),
                (foot_x - 3, foot_y + 3),
            ])
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["leather_dark"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 4 * facing, foot_y - 1),
                (foot_x + 4 * facing, foot_y + 2),
                (foot_x - 3, foot_y + 2),
            ])
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["leather_mid"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 3 * facing, foot_y - 1),
                (foot_x + 3 * facing, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_dark"],
                             (foot_x + facing, foot_y - 1, 1, 1))
    def _draw_gj_torso(surface, cx, cy, facing, phase, action):
        """Jester outfit torso with red/purple diamond pattern."""
        breath = math.sin(phase * 0.8) * 1
        # Torso outline.
        torso_pts = [
            (cx - 10, cy - 12),
            (cx - 12, cy - 8),
            (cx - 11, cy - 2),
            (cx - 8, cy + 6),
            (cx - 4, cy + 10),
            (cx + 4, cy + 10),
            (cx + 8, cy + 6),
            (cx + 11, cy - 2),
            (cx + 12, cy - 8),
            (cx + 10, cy - 12),
        ]
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_pts])
        # DIAMOND CHECKERED PATTERN.
        # Draw base as left half red, right half purple, then overlay diamonds.
        # Left side (red).
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_darkest"], [
            (cx - 10, cy - 12),
            (cx, cy - 12),
            (cx, cy + 10),
            (cx - 4, cy + 10),
            (cx - 8, cy + 6),
            (cx - 11, cy - 2),
            (cx - 12, cy - 8),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_dark"], [
            (cx - 9, cy - 11),
            (cx, cy - 11),
            (cx, cy + 9),
            (cx - 4, cy + 9),
            (cx - 7, cy + 5),
            (cx - 10, cy - 2),
            (cx - 11, cy - 7),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_mid"], [
            (cx - 7, cy - 9),
            (cx, cy - 9),
            (cx, cy + 7),
            (cx - 5, cy + 7),
            (cx - 8, cy),
            (cx - 9, cy - 6),
        ])
        # Right side (purple).
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["purple_darkest"], [
            (cx, cy - 12),
            (cx + 10, cy - 12),
            (cx + 12, cy - 8),
            (cx + 11, cy - 2),
            (cx + 8, cy + 6),
            (cx + 4, cy + 10),
            (cx, cy + 10),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["purple_dark"], [
            (cx, cy - 11),
            (cx + 9, cy - 11),
            (cx + 11, cy - 7),
            (cx + 10, cy - 2),
            (cx + 7, cy + 5),
            (cx + 4, cy + 9),
            (cx, cy + 9),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["purple_mid"], [
            (cx, cy - 9),
            (cx + 7, cy - 9),
            (cx + 9, cy - 6),
            (cx + 8, cy),
            (cx + 5, cy + 7),
            (cx, cy + 7),
        ])
        # Diamond accents (invert colors in small squares).
        # Red side gets purple diamonds.
        for y_off in (-8, -3, 2, 7):
            for x_off in (-8, -3):
                dx = cx + x_off
                dy = cy + y_off
                _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["purple_dark"], [
                    (dx, dy - 1), (dx + 1, dy), (dx, dy + 1), (dx - 1, dy),
                ])
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["purple_mid"], (dx, dy, 1, 1))
        # Purple side gets red diamonds.
        for y_off in (-8, -3, 2, 7):
            for x_off in (3, 8):
                dx = cx + x_off
                dy = cy + y_off
                _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_dark"], [
                    (dx, dy - 1), (dx + 1, dy), (dx, dy + 1), (dx - 1, dy),
                ])
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["red_mid"], (dx, dy, 1, 1))
        # Center vertical seam.
        pygame.draw.line(surface, _NS_grimjack.PALETTE["shadow_deep"],
                         (cx, cy - 12), (cx, cy + 10), 1)
        # Highlight sheen.
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["red_light"],
                         (cx - 6, cy - 10, 1, 1))
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["purple_light"],
                         (cx + 6, cy - 10, 1, 1))
        # Ruffled collar (frilly jester collar around neck).
        _NS_grimjack._draw_jester_collar(surface, cx, cy - 12, facing, phase)
    def _draw_jester_collar(surface, cx, cy, facing, phase):
        """Frilly ruff collar around neck."""
        # Multiple triangular points around neck.
        collar_pts = []
        for i in range(-5, 6):
            base_x = cx + i * 2
            base_y = cy + 1
            tip_y = cy - 2 + int(math.sin(phase * 0.5 + i) * 1)
            # Alternate red/purple.
            if abs(i) % 2 == 0:
                color = _NS_grimjack.PALETTE["red_darkest"]
                mid_color = _NS_grimjack.PALETTE["red_mid"]
            else:
                color = _NS_grimjack.PALETTE["purple_darkest"]
                mid_color = _NS_grimjack.PALETTE["purple_mid"]
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"], [
                (base_x - 1, base_y + 1),
                (base_x + 2, base_y + 1),
                (base_x, tip_y + 1),
            ])
            _NS_grimjack._poly(surface, color, [
                (base_x - 1, base_y),
                (base_x + 2, base_y),
                (base_x, tip_y),
            ])
            pygame.draw.rect(surface, mid_color, (base_x, tip_y + 1, 1, 1))
        # Bell in center of collar.
        _NS_grimjack._draw_jester_bell(surface, cx, cy + 3, phase)
    def _draw_jester_bell(surface, cx, cy, phase):
        """Gold bell (jester accessory)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Bell shape.
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"], [
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["gold_dark"], [
            (cx - 2, cy - 1),
            (cx + 2, cy - 1),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["gold_mid"], [
            (cx - 1, cy - 1),
            (cx + 1, cy - 1),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_light"],
                         (cx - 1, cy, 1, 1))
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_shine"],
                         (cx - 1, cy, 1, 1))
        # Small clapper.
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_dark"],
                         (cx, cy + 3, 1, 1))
    def _draw_gj_head(surface, cx, cy, facing, phase, action):
        """Jester head - mask face + big hat with 2 horns/points + bells."""
        # Head (mask - white/pale).
        face_pts = [
            (cx - 6, cy),
            (cx - 7, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 7, cy - 4),
            (cx + 6, cy),
            (cx + 4, cy + 5),
            (cx + 1, cy + 7),
            (cx - 1, cy + 7),
            (cx - 4, cy + 5),
        ]
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in face_pts])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["mask_darkest"], face_pts)
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["mask_dark"], [
            (cx - 5, cy),
            (cx - 6, cy - 4),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 6, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["mask_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy - 4),
            (cx - 3, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy - 4),
            (cx + 4, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Bright white cheek highlight.
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["mask_light"],
                         (cx + facing * 3, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["mask_shine"],
                         (cx + facing * 3, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["mask_shine"],
                         (cx - facing * 3, cy - 3, 1, 1))
        # EMPTY GLOWING EYES (creepy).
        for eye_side in (-1, 1):
            eye_x = cx + eye_side * 2
            eye_y = cy - 3
            # Deep socket.
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_socket"],
                             (eye_x - 1, eye_y - 1, 3, 3))
            # Glow.
            for r in range(4, 0, -1):
                alpha = _NS_grimjack._alpha(160 * (4 - r) / 4)
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["eye_glow"], alpha),
                          (eye_x, eye_y), r)
            # Bright eye core.
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_glow"], (eye_x, eye_y, 1, 1))
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_hot"], (eye_x, eye_y, 1, 1))
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["white"], (eye_x, eye_y, 1, 1))
        # CREEPY GRIN MOUTH (red).
        # Wide grin curved.
        grin_pts = [
            (cx - 4, cy + 3),
            (cx - 3, cy + 5),
            (cx, cy + 6),
            (cx + 3, cy + 5),
            (cx + 4, cy + 3),
            (cx + 3, cy + 3),
            (cx, cy + 4),
            (cx - 3, cy + 3),
        ]
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["mouth_dark"], grin_pts)
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["mouth_mid"], [
            (cx - 3, cy + 3),
            (cx - 2, cy + 5),
            (cx, cy + 5),
            (cx + 2, cy + 5),
            (cx + 3, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["mouth_light"],
                         (cx, cy + 4, 1, 1))
        # Small fangs at grin corners.
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["mask_light"],
                         (cx - 3, cy + 4, 1, 1))
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["mask_light"],
                         (cx + 2, cy + 4, 1, 1))
        # JESTER HAT (2 curved horns/points with bells on tips).
        _NS_grimjack._draw_jester_hat(surface, cx, cy - 8, facing, phase)
    def _draw_jester_hat(surface, cx, cy, facing, phase):
        """3-point jester hat with bells."""
        sway = math.sin(phase * 0.8) * 2
        # Hat base band (around head).
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"], [
            (cx - 8, cy - 1),
            (cx + 8, cy - 1),
            (cx + 9, cy + 2),
            (cx - 9, cy + 2),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_darkest"], [
            (cx - 8, cy),
            (cx, cy),
            (cx, cy + 2),
            (cx - 9, cy + 2),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["purple_darkest"], [
            (cx, cy),
            (cx + 8, cy),
            (cx + 9, cy + 2),
            (cx, cy + 2),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_dark"], [
            (cx - 7, cy + 1),
            (cx, cy + 1),
            (cx, cy + 2),
            (cx - 8, cy + 2),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["purple_dark"], [
            (cx, cy + 1),
            (cx + 7, cy + 1),
            (cx + 8, cy + 2),
            (cx, cy + 2),
        ])
        # Highlight band.
        pygame.draw.line(surface, _NS_grimjack.PALETTE["red_mid"],
                         (cx - 6, cy + 1), (cx, cy + 1), 1)
        pygame.draw.line(surface, _NS_grimjack.PALETTE["purple_mid"],
                         (cx + 1, cy + 1), (cx + 6, cy + 1), 1)
        # 3 Hat points/horns (left, center, right).
        # LEFT POINT (curves left).
        _NS_grimjack._draw_hat_point(surface, cx - 6, cy, -1, -3, 8,
                         _NS_grimjack.PALETTE["red_darkest"],
                         _NS_grimjack.PALETTE["red_dark"],
                         _NS_grimjack.PALETTE["red_mid"],
                         _NS_grimjack.PALETTE["red_light"],
                         sway)
        # CENTER POINT (up).
        _NS_grimjack._draw_hat_point(surface, cx, cy, 0, -1, 10,
                         _NS_grimjack.PALETTE["purple_darkest"],
                         _NS_grimjack.PALETTE["purple_dark"],
                         _NS_grimjack.PALETTE["purple_mid"],
                         _NS_grimjack.PALETTE["purple_light"],
                         sway * 0.5)
        # RIGHT POINT (curves right).
        _NS_grimjack._draw_hat_point(surface, cx + 6, cy, 1, -3, 8,
                         _NS_grimjack.PALETTE["red_darkest"],
                         _NS_grimjack.PALETTE["red_dark"],
                         _NS_grimjack.PALETTE["red_mid"],
                         _NS_grimjack.PALETTE["red_light"],
                         sway)
    def _draw_hat_point(surface, base_x, base_y, curve_dir, curl_x, length,
                         darkest, dark, mid, light, sway):
        """Draw single hat point with bell tip."""
        # Point curves upward with slight curl.
        tip_x = base_x + curl_x + int(sway * 0.5)
        tip_y = base_y - length
        # Bezier midpoint.
        mid_x = base_x + curl_x // 2
        mid_y = base_y - length // 2
        segments = 6
        prev = (base_x, base_y)
        for i in range(1, segments + 1):
            t = i / segments
            bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            thickness = max(1, 4 - int(t * 3))
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1),
                    (bx + 1, by + 1), thickness + 1)
            _NS_grimjack._aaline(surface, darkest,
                    prev, (bx, by), thickness)
            _NS_grimjack._aaline(surface, dark,
                    prev, (bx, by), max(1, thickness - 1))
            _NS_grimjack._aaline(surface, mid,
                    (prev[0], prev[1] - 1), (bx, by - 1),
                    max(1, thickness - 2))
            pygame.draw.rect(surface, light,
                             (bx, by - 1, 1, 1))
            prev = (bx, by)
        # BELL at tip.
        _NS_grimjack._draw_hat_bell(surface, tip_x, tip_y, sway)
    def _draw_hat_bell(surface, cx, cy, sway):
        """Bell at hat tip."""
        # Bell.
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["shadow_deep"], [
            (cx - 1, cy),
            (cx + 1, cy),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["gold_dark"], [
            (cx - 1, cy - 1),
            (cx + 1, cy - 1),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])
        _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["gold_mid"], [
            (cx, cy - 1),
            (cx + 1, cy - 1),
            (cx + 1, cy),
            (cx, cy),
        ])
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_light"],
                         (cx, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_shine"],
                         (cx, cy - 1, 1, 1))
    def _draw_back_dagger_arm(surface, cx, cy, facing, phase, action,
                                attack_progress):
        """Back arm holding dagger."""
        back_dir = -facing
        shoulder_x = cx + back_dir * 9
        shoulder_y = cy - 8
        sway = math.sin(phase * 0.6) * 1
        # Angle (back arm swings opposite of front during attack).
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.2 - t * 0.3)  # forward → down
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (-0.1 + t * 0.4)  # comes back
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (0.3 - t * 0.1)
        else:
            arm_angle = math.pi * 0.15 + sway * 0.1
        upper_len = 8
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * back_dir
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)
        hand_x = elbow_x + int(math.cos(arm_angle - math.pi * 0.2)
                                * 8) * back_dir
        hand_y = elbow_y - int(math.sin(arm_angle - math.pi * 0.2) * 8)
        # Upper arm (red).
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 4)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["red_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["red_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["red_mid"],
                (shoulder_x + back_dir, shoulder_y),
                (elbow_x + back_dir, elbow_y), 1)
        # Elbow (gold puffball).
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["gold_dark"], (elbow_x, elbow_y), 2)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["gold_mid"], (elbow_x, elbow_y), 1)
        # Forearm (purple).
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1),
                (hand_x + 1, hand_y + 1), 4)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["purple_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["purple_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Hand (dark glove).
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["shadow_deep"],
                  (hand_x + 1, hand_y + 1), 3)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["leather_dark"],
                  (hand_x, hand_y), 3)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["leather_mid"],
                  (hand_x, hand_y), 2)
        # DAGGER in back hand (points down/back).
        dagger_angle = arm_angle - math.pi * 0.4
        _NS_grimjack._draw_poison_dagger(surface, hand_x, hand_y, dagger_angle,
                             back_dir, phase, small=True)
    def _draw_front_dagger_arm(surface, cx, cy, facing, phase, action,
                                 attack_progress):
        """Front arm with main dagger (foreground)."""
        shoulder_x = cx + facing * 9
        shoulder_y = cy - 8
        # Angle: 0 = forward, pi/2 = UP.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise back.
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.4 + t * 0.4)
                dagger_extra = math.pi * 0.2
            elif attack_progress < 0.6:
                # Stab forward.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (0.8 - t * 0.9)
                dagger_extra = math.pi * (0.2 - t * 0.4)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.1 + t * 0.3)
                dagger_extra = math.pi * (-0.2 + t * 0.3)
        elif action == "float":
            arm_angle = math.pi * 0.15 + math.sin(phase) * 0.05
            dagger_extra = math.pi * 0.1
        else:
            arm_angle = math.pi * 0.12 + math.sin(phase * 0.5) * 0.03
            dagger_extra = math.pi * 0.08
        upper_len = 9
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)
        forearm_len = 9
        hand_angle = arm_angle - math.pi * 0.15
        hand_x = elbow_x + int(math.cos(hand_angle) * forearm_len) * facing
        hand_y = elbow_y - int(math.sin(hand_angle) * forearm_len)
        # Upper arm (purple).
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 5)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["purple_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["purple_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["purple_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)
        # Elbow puffball (gold).
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["shadow_deep"],
                  (elbow_x + 1, elbow_y + 1), 3)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["gold_dark"],
                  (elbow_x, elbow_y), 3)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["gold_mid"],
                  (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_shine"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # Forearm (red).
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1),
                (hand_x + 1, hand_y + 1), 5)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["red_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["red_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["red_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Hand (dark glove).
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["shadow_deep"],
                  (hand_x + 1, hand_y + 1), 4)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["leather_dark"],
                  (hand_x, hand_y), 4)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["leather_mid"],
                  (hand_x, hand_y), 3)
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_dark"],
                         (hand_x, hand_y, 1, 1))
        # MAIN DAGGER.
        dagger_angle = hand_angle + dagger_extra
        _NS_grimjack._draw_poison_dagger(surface, hand_x, hand_y, dagger_angle,
                             facing, phase, small=False)
    def _draw_poison_dagger(surface, hx, hy, angle, facing, phase, small=False):
        """Curved dagger with poison drip."""
        # Handle (behind hand).
        handle_len = 5 if small else 6
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy + int(math.sin(angle) * handle_len)
        # Handle (dark leather with gold wrap).
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["leather_dark"],
                (hx, hy), (handle_end_x, handle_end_y), 2)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["leather_mid"],
                (hx, hy), (handle_end_x, handle_end_y), 1)
        # Gold pommel.
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["gold_dark"],
                  (handle_end_x, handle_end_y), 2)
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["gold_mid"],
                  (handle_end_x, handle_end_y), 1)
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_shine"],
                         (handle_end_x, handle_end_y, 1, 1))
        # Crossguard.
        perp = angle + math.pi / 2
        cg_a_x = hx + int(math.cos(perp) * 3) * facing
        cg_a_y = hy - int(math.sin(perp) * 3)
        cg_b_x = hx - int(math.cos(perp) * 3) * facing
        cg_b_y = hy + int(math.sin(perp) * 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                (cg_a_x + 1, cg_a_y + 1),
                (cg_b_x + 1, cg_b_y + 1), 3)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["gold_dark"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 2)
        _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["gold_mid"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 1)
        # BLADE (short curved dagger).
        blade_len = 12 if small else 16
        # Slight curve.
        curve_angle_1 = angle + math.pi * 0.04
        curve_angle_2 = angle + math.pi * 0.1
        mid_x = hx + int(math.cos(curve_angle_1) * blade_len * 0.5) * facing
        mid_y = hy - int(math.sin(curve_angle_1) * blade_len * 0.5)
        tip_x = mid_x + int(math.cos(curve_angle_2)
                             * blade_len * 0.55) * facing
        tip_y = mid_y - int(math.sin(curve_angle_2) * blade_len * 0.55)
        segments = 8
        prev = (hx, hy)
        for i in range(1, segments + 1):
            t = i / segments
            bx = int((1 - t) ** 2 * hx + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * hy + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            thickness = max(1, 3 - int(t * 2))
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1),
                    thickness + 1)
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["blade_darkest"],
                    prev, (bx, by), thickness)
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["blade_dark"],
                    prev, (bx, by), max(1, thickness - 1))
            _NS_grimjack._aaline(surface, _NS_grimjack.PALETTE["blade_mid"],
                    prev, (bx, by), max(1, thickness - 2))
            # Bright edge.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["blade_shine"],
                                 (bx, by, 1, 1))
            prev = (bx, by)
        # Tip.
        _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["blade_darkest"], (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_grimjack.PALETTE["blade_shine"], (tip_x, tip_y, 1, 1))
        # POISON DRIP (green glow along blade).
        poison_pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        glow_alpha = _NS_grimjack._alpha(200 * poison_pulse)
        # Poison line on blade.
        pygame.draw.line(surface, (*_NS_grimjack.PALETTE["poison_mid"], glow_alpha),
                         (hx, hy), (tip_x, tip_y), 1)
        # Small drip at tip.
        drip_y = tip_y + int(math.sin(phase * 3) * 2)
        _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_dark"], glow_alpha),
                  (tip_x, drip_y + 2), 2)
        _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_mid"], glow_alpha),
                  (tip_x, drip_y + 2), 1)
        pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["poison_light"], glow_alpha),
                         (tip_x, drip_y + 2, 1, 1))
        pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["poison_hot"], glow_alpha),
                         (tip_x, drip_y + 2, 1, 1))
        # Glow around blade.
        for r in range(4, 1, -1):
            alpha = _NS_grimjack._alpha(60 * (4 - r) / 4 * poison_pulse)
            glow_mid_x = int(hx + (tip_x - hx) * 0.5)
            glow_mid_y = int(hy + (tip_y - hy) * 0.5)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_light"], alpha),
                      (glow_mid_x, glow_mid_y), r)
    def _draw_dagger_slash(surface, boss, cx, cy, progress):
        """Purple/green slash arc during dagger attack."""
        facing = boss.direction
        swing_t = max(0.0, min(1.0, (progress - 0.35) / 0.4))
        arc_center_x = cx + facing * 6
        arc_center_y = cy - 4
        radius = 24  # small arc (dagger short)
        num_slices = 10
        for slice_i in range(num_slices):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.7
            sweep_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.1)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            fade = 1 - slice_t * 0.75
            alpha = _NS_grimjack._alpha(240 * fade
                            * (1 - abs(swing_t - 0.5) * 1.4))
            if alpha <= 0:
                continue
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            size = max(2, int(5 * fade))
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_darkest"], alpha),
                      (arc_x, arc_y), size + 1)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                      (arc_x, arc_y), size)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                      (arc_x, arc_y), max(1, size - 1))
            # Green poison mixed in.
            if slice_i % 3 == 0:
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_mid"], alpha),
                          (arc_x, arc_y), max(1, size - 1))
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["poison_hot"], alpha),
                                 (arc_x, arc_y, 1, 1))
            else:
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_light"], alpha),
                          (arc_x, arc_y), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (arc_x, arc_y, 1, 1))
    # ============================================================
    # VOID PARTICLES / AMBIENT
    # ============================================================
    def _draw_void_particles(surface, cx, cy, phase, intense=False,
                              moving=False, facing=1):
        """Purple void particles rising below jester."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Purple mist cloud.
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.3) * 0.3 + 0.7
        for radius in range(28, 3, -2):
            alpha = _NS_grimjack._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_grimjack.PALETTE["void_darkest"], alpha),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_grimjack._alpha((18 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                    (70 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 8))
        # Rising void particles.
        for i, offset in enumerate((-22, -14, -6, 2, 10, 18, 26, -28)):
            t = (phase * 0.5 + i * 0.12) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 22)
            alpha = _NS_grimjack._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                      (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                             (sx, sy - 1, 1, 1))
        # Green poison sparks.
        for i in range(6):
            spark_t = (phase * 0.7 + i * 0.15) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            ey = cy + 2 - int(spark_t * 18)
            alpha = _NS_grimjack._alpha(200 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["poison_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["poison_hot"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail.
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_grimjack._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                          (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (sx, sy - 1, 1, 1))
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 10, 160), (5, 7, 110, 12))
        pygame.draw.ellipse(shadow, (40, 20, 60, 100), (12, 9, 96, 8))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_void_aura(surface, x, y, phase):
        """Purple void aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((190, 170), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_grimjack._alpha((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_grimjack._aacircle(aura, (*_NS_grimjack.PALETTE["void_darkest"], alpha),
                          (95, 85), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_grimjack._alpha((50 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_grimjack._aacircle(aura, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                          (95, 85), radius)
        for radius in range(25, 5, -2):
            alpha = _NS_grimjack._alpha((25 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_grimjack._aacircle(aura, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                          (95, 85), radius)
        surface.blit(aura, (x - 95, y - 85))
        # Floating void embers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            r = 34 + int(math.sin(phase + i) * 8)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_hot"], (sx, sy, 1, 1))
    def _draw_ground_void_ring(surface, x, y, phase, skill):
        """Ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_grimjack.PALETTE["void_dark"], 200),
                            (5, 17, 160, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_grimjack.PALETTE["void_darkest"], 220),
                            (14, 19, 142, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_grimjack.PALETTE["void_mid"], 200),
                            (25, 21, 120, 16), 1)
        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 29 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 29 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_grimjack.PALETTE["void_hot"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, (*_NS_grimjack.PALETTE["void_shine"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_grimjack.PALETTE["void_hot"],
                                        _NS_grimjack._alpha(150 * pulse)),
                                (15, 11, 140, 36), 1)
        surface.blit(ring, (x - 85, y - 25))
    # ============================================================
    # SKILL Q: DECEIVE (teleport + invisibility)
    # ============================================================
    def _draw_deceive_ground(surface, boss, x, y, timer, phase):
        """Purple smoke ring on ground where boss was/is."""
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(28 * min(1.0, progress * 3))
        if r > 3:
            alpha = _NS_grimjack._alpha(200 * (1 - progress * 0.5))
            pygame.draw.ellipse(surface, (*_NS_grimjack.PALETTE["void_darkest"], alpha),
                                (x - r, y + 42 - r // 3,
                                 r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                                (x - r + 3, y + 42 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
    def _draw_deceive_foreground(surface, boss, x, y, timer, phase):
        """Purple teleport smoke cloud."""
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Vanish smoke.
            t = progress / 0.4
            for i in range(20):
                angle = phase * 3 + i * math.pi / 10
                r = int(20 + t * 25)
                sx = x + int(math.cos(angle) * r)
                sy = y - 8 + int(math.sin(angle) * r * 0.8)
                alpha = _NS_grimjack._alpha(220 * (1 - t))
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_darkest"], alpha),
                          (sx, sy), 4)
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                          (sx, sy), 3)
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                          (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_light"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (sx, sy, 1, 1))
        elif progress < 0.7:
            # Fully invisible - trailing purple wisps toward new position.
            trail_t = (progress - 0.4) / 0.3
            for i in range(12):
                wisp_angle = i * math.pi / 6
                wisp_r = int(20 + math.sin(phase * 4 + i) * 8)
                wx = x + int(math.cos(wisp_angle) * wisp_r)
                wy = y - 8 + int(math.sin(wisp_angle) * wisp_r * 0.5)
                alpha = _NS_grimjack._alpha(180)
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                          (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (wx, wy, 1, 1))
        else:
            # Reappear smoke.
            t = (progress - 0.7) / 0.3
            for i in range(20):
                angle = phase * 3 + i * math.pi / 10
                r = int(35 * (1 - t))
                sx = x + int(math.cos(angle) * r)
                sy = y - 8 + int(math.sin(angle) * r * 0.8)
                alpha = _NS_grimjack._alpha(220 * (1 - t))
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                          (sx, sy), 3)
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                          (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL W: JACK IN THE BOX (trap)
    # ============================================================
    def _draw_jackbox_ground(surface, boss, x, y, timer, phase):
        """Faint circle marking box location."""
        tx, ty = _NS_grimjack._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Faint shadow under box.
        _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["shadow_deep"], 150),
                  (tx, ty + 5), 10)
    def _draw_jackbox_foreground(surface, boss, x, y, timer, phase):
        """Wooden box that pops open."""
        tx, ty = _NS_grimjack._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Box appears then eventually pops.
        if progress < 0.6:
            # Box sitting (invisible-ish placement).
            box_alpha = _NS_grimjack._alpha(180)
            # Wooden box (small square).
            box_pts = [
                (tx - 6, ty - 4),
                (tx + 6, ty - 4),
                (tx + 6, ty + 4),
                (tx - 6, ty + 4),
            ]
            _NS_grimjack._poly(surface, (*_NS_grimjack.PALETTE["shadow_deep"], box_alpha),
                  [(px + 1, py + 1) for px, py in box_pts])
            _NS_grimjack._poly(surface, (*_NS_grimjack.PALETTE["leather_dark"], box_alpha),
                  box_pts)
            _NS_grimjack._poly(surface, (*_NS_grimjack.PALETTE["leather_mid"], box_alpha), [
                (tx - 5, ty - 3),
                (tx + 5, ty - 3),
                (tx + 5, ty + 3),
                (tx - 5, ty + 3),
            ])
            # Wood grain lines.
            pygame.draw.line(surface,
                             (*_NS_grimjack.PALETTE["leather_dark"], box_alpha),
                             (tx - 5, ty), (tx + 5, ty), 1)
            # Purple gem on front.
            pygame.draw.rect(surface,
                             (*_NS_grimjack.PALETTE["void_dark"], box_alpha),
                             (tx - 1, ty - 1, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_grimjack.PALETTE["void_hot"], box_alpha),
                             (tx, ty, 1, 1))
            # Crank handle on side.
            pygame.draw.rect(surface,
                             (*_NS_grimjack.PALETTE["gold_dark"], box_alpha),
                             (tx + 6, ty - 2, 2, 1))
            pygame.draw.rect(surface,
                             (*_NS_grimjack.PALETTE["gold_mid"], box_alpha),
                             (tx + 7, ty - 2, 1, 1))
            # Warning ! marks (as timer runs out).
            if progress > 0.4:
                warn_alpha = _NS_grimjack._alpha(240 * math.sin(phase * 6) ** 2)
                pygame.draw.rect(surface,
                                 (*_NS_grimjack.PALETTE["red_light"], warn_alpha),
                                 (tx, ty - 12, 1, 4))
                pygame.draw.rect(surface,
                                 (*_NS_grimjack.PALETTE["red_light"], warn_alpha),
                                 (tx, ty - 6, 1, 1))
        else:
            # POP UP! Mini jester head springs out.
            t = (progress - 0.6) / 0.4
            spring_height = int(20 * math.sin(t * math.pi))
            pop_y = ty - spring_height
            # Spring (zigzag line).
            for i in range(5):
                zz_t = i / 5
                zz_x = tx + int(math.sin(zz_t * math.pi * 4) * 3)
                zz_y = ty - int(zz_t * spring_height)
                if i < 4:
                    nxt_t = (i + 1) / 5
                    nxt_x = tx + int(math.sin(nxt_t * math.pi * 4) * 3)
                    nxt_y = ty - int(nxt_t * spring_height)
                    pygame.draw.line(surface, _NS_grimjack.PALETTE["gold_dark"],
                                     (zz_x, zz_y), (nxt_x, nxt_y), 2)
                    pygame.draw.line(surface, _NS_grimjack.PALETTE["gold_mid"],
                                     (zz_x, zz_y), (nxt_x, nxt_y), 1)
            # Mini jester head (scary).
            head_pop_y = pop_y - 2
            # Face.
            _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["mask_dark"], (tx, head_pop_y), 4)
            _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["mask_mid"], (tx, head_pop_y), 3)
            # Red glowing eyes.
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_glow"],
                             (tx - 1, head_pop_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_glow"],
                             (tx + 1, head_pop_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_hot"],
                             (tx - 1, head_pop_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["eye_hot"],
                             (tx + 1, head_pop_y - 1, 1, 1))
            # Grin.
            pygame.draw.line(surface, _NS_grimjack.PALETTE["mouth_dark"],
                             (tx - 2, head_pop_y + 1),
                             (tx + 2, head_pop_y + 1), 1)
            # Mini hat point.
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["red_dark"], [
                (tx - 2, head_pop_y - 3),
                (tx, head_pop_y - 6),
                (tx + 2, head_pop_y - 3),
            ])
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["gold_mid"],
                             (tx, head_pop_y - 6, 1, 1))
            # Box still open (top flipped up).
            box_pts = [
                (tx - 6, ty),
                (tx + 6, ty),
                (tx + 6, ty + 4),
                (tx - 6, ty + 4),
            ]
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["leather_dark"], box_pts)
            _NS_grimjack._poly(surface, _NS_grimjack.PALETTE["leather_mid"], [
                (tx - 5, ty + 1),
                (tx + 5, ty + 1),
                (tx + 5, ty + 3),
                (tx - 5, ty + 3),
            ])
            # Purple gem still there.
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_hot"],
                             (tx, ty + 2, 1, 1))
            # Fear burst around.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                r = int(15 + t * 15)
                fx = tx + int(math.cos(angle) * r)
                fy = ty + int(math.sin(angle) * r * 0.5)
                alpha = _NS_grimjack._alpha(200 * (1 - t))
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                          (fx, fy), 2)
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (fx, fy, 1, 1))
    # ============================================================
    # SKILL E: TWO-SHIV POISON (throw 2 daggers)
    # ============================================================
    def _draw_twoshiv_skill(surface, boss, x, y, timer, phase):
        """Throw 2 poisoned daggers."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_grimjack._target_position(boss, x, y)
        if progress < 0.2:
            # Wind-up: prepare daggers.
            t = progress / 0.2
            for side_off in (-4, 4):
                charge_x = x + facing * 15 + side_off
                charge_y = y - 8
                cr = int(3 + t * 4)
                for r in range(cr + 3, 0, -1):
                    alpha = _NS_grimjack._alpha(180 * (cr + 3 - r) / (cr + 3))
                    _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_dark"], alpha),
                              (charge_x, charge_y), r)
                _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["poison_mid"],
                          (charge_x, charge_y), cr - 1)
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["poison_hot"],
                                 (charge_x, charge_y, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            # 2 daggers spiraling toward target.
            for dagger_i, side_off in enumerate((-8, 8)):
                start_x = x + facing * 16
                start_y = y - 8 + side_off
                # Slight arc.
                mid_x = int((start_x + tx) / 2)
                mid_y = int((start_y + ty) / 2) - 15 + side_off
                # Bezier interpolation.
                bx = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tx)
                by = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * ty)
                # Compute dagger angle from motion.
                if t < 0.99:
                    t2 = min(1.0, t + 0.05)
                    bx2 = int((1 - t2) ** 2 * start_x + 2 * (1 - t2) * t2 * mid_x
                             + t2 ** 2 * tx)
                    by2 = int((1 - t2) ** 2 * start_y + 2 * (1 - t2) * t2 * mid_y
                             + t2 ** 2 * ty)
                    dagger_angle = math.atan2(by2 - by, bx2 - bx)
                else:
                    dagger_angle = math.atan2(ty - my_prev if False else 0, 1)
                # Poison trail behind.
                for trail_i in range(6):
                    tr_t = max(0.0, t - trail_i * 0.05)
                    trx = int((1 - tr_t) ** 2 * start_x + 2 * (1 - tr_t) * tr_t * mid_x
                             + tr_t ** 2 * tx)
                    try_ = int((1 - tr_t) ** 2 * start_y + 2 * (1 - tr_t) * tr_t * mid_y
                             + tr_t ** 2 * ty)
                    alpha = _NS_grimjack._alpha(220 - trail_i * 30)
                    size = max(1, 5 - trail_i)
                    _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_darkest"], alpha),
                              (trx, try_), size + 1)
                    _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_dark"], alpha),
                              (trx, try_), size)
                    _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_mid"], alpha),
                              (trx, try_), max(1, size - 1))
                    _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_light"], alpha),
                              (trx, try_), max(1, size - 2))
                    pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["poison_hot"], alpha),
                                     (trx, try_, 1, 1))
                # Rotating dagger sprite.
                # Blade length.
                blade_len = 8
                cos_a = math.cos(dagger_angle)
                sin_a = math.sin(dagger_angle)
                tip_x = int(bx + cos_a * blade_len)
                tip_y = int(by + sin_a * blade_len)
                handle_x = int(bx - cos_a * 4)
                handle_y = int(by - sin_a * 4)
                # Handle.
                pygame.draw.line(surface, _NS_grimjack.PALETTE["shadow_deep"],
                                 (bx + 1, by + 1), (handle_x + 1, handle_y + 1), 3)
                pygame.draw.line(surface, _NS_grimjack.PALETTE["leather_dark"],
                                 (bx, by), (handle_x, handle_y), 2)
                pygame.draw.line(surface, _NS_grimjack.PALETTE["gold_dark"],
                                 (bx, by), (handle_x, handle_y), 1)
                # Blade.
                pygame.draw.line(surface, _NS_grimjack.PALETTE["shadow_deep"],
                                 (bx + 1, by + 1), (tip_x + 1, tip_y + 1), 3)
                pygame.draw.line(surface, _NS_grimjack.PALETTE["blade_darkest"],
                                 (bx, by), (tip_x, tip_y), 2)
                pygame.draw.line(surface, _NS_grimjack.PALETTE["blade_mid"],
                                 (bx, by), (tip_x, tip_y), 1)
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["blade_shine"],
                                 (tip_x, tip_y, 1, 1))
                # Poison drip along blade.
                mid_bx = int((bx + tip_x) / 2)
                mid_by = int((by + tip_y) / 2)
                _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["poison_hot"], (mid_bx, mid_by), 1)
                # Impact at target.
                if t > 0.9:
                    st = (t - 0.9) / 0.1
                    for r in range(5, 0, -1):
                        alpha = _NS_grimjack._alpha(200 * (1 - st) * (5 - r) / 5)
                        _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["poison_mid"], alpha),
                                  (tx, ty), r + int(st * 5))
                    pygame.draw.rect(surface, _NS_grimjack.PALETTE["poison_shine"],
                                     (tx, ty, 1, 1))
                    # Poison DoT skulls (small).
                    for i in range(3):
                        skull_angle = i * math.pi * 2 / 3 + phase * 0.5
                        sx = tx + int(math.cos(skull_angle) * 8)
                        sy = ty + int(math.sin(skull_angle) * 6)
                        pygame.draw.rect(surface, _NS_grimjack.PALETTE["poison_dark"], (sx, sy, 2, 2))
                        pygame.draw.rect(surface, _NS_grimjack.PALETTE["poison_hot"], (sx, sy, 1, 1))
    # ============================================================
    # SKILL R: HALLUCINATE (clone appears)
    # ============================================================
    def _draw_hallucinate_ground(surface, boss, x, y, timer, phase):
        """Rings under boss + clone position."""
        # Under boss.
        for i in range(2):
            r = int(28 + i * 6 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_grimjack._alpha(200 - i * 60)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                      (x, y + 42), r, 2)
    def _draw_hallucinate_foreground(surface, boss, x, y, timer, phase):
        """Clone appears beside boss with purple energy."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Clone position (opposite side of facing).
        clone_x = x - facing * 40
        clone_y = y - 5
        if progress < 0.3:
            # Clone materializing.
            t = progress / 0.3
            # Purple energy gathering.
            for r in range(int(15 * t) + 3, 0, -1):
                alpha = _NS_grimjack._alpha(200 * (15 * t + 3 - r) / (15 * t + 3))
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                          (clone_x, clone_y), r)
            _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["void_mid"], (clone_x, clone_y),
                      max(1, int(15 * t) - 3))
            _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["void_light"], (clone_x, clone_y),
                      max(1, int(15 * t) - 6))
            # Spiraling energy.
            for i in range(12):
                angle = phase * 5 + i * math.pi / 6
                spiral_r = int(40 - t * 25)
                sx = clone_x + int(math.cos(angle) * spiral_r)
                sy = clone_y + int(math.sin(angle) * spiral_r * 0.6)
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_shine"], (sx, sy, 1, 1))
        elif progress < 0.85:
            # Clone visible - draw silhouette copy of boss.
            # Semi-transparent clone (purple tinted).
            clone_alpha = int(180 + math.sin(phase * 4) * 40)
            temp = pygame.Surface((120, 100), pygame.SRCALPHA)
            local_cx = 60
            local_cy = 50
            # Draw clone body simplified with purple tint.
            _NS_grimjack._draw_gj_body_impl(temp, local_cx, local_cy, -facing, phase,
                                "idle", 0)
            # Purple tint overlay.
            tint = pygame.Surface((120, 100), pygame.SRCALPHA)
            tint.fill((*_NS_grimjack.PALETTE["void_mid"], 100))
            temp.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
            temp.set_alpha(clone_alpha)
            surface.blit(temp, (clone_x - 60, clone_y - 50))
            # Purple aura around clone.
            for r in range(12, 4, -1):
                alpha = _NS_grimjack._alpha(60 * (12 - r) / 12)
                _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_light"], alpha),
                          (clone_x, clone_y), r)
            # Sparkles orbiting clone.
            for i in range(6):
                angle = phase * 2 + i * math.pi / 3
                sr = 22
                sx = clone_x + int(math.cos(angle) * sr)
                sy = clone_y + int(math.sin(angle) * sr * 0.6)
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_grimjack.PALETTE["void_shine"], (sx, sy, 1, 1))
        else:
            # Clone EXPLODES!
            t = (progress - 0.85) / 0.15
            explosion_r = int(20 + t * 45)
            alpha = _NS_grimjack._alpha(240 * (1 - t))
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_darkest"], alpha),
                      (clone_x, clone_y), explosion_r + 3, 4)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_dark"], alpha),
                      (clone_x, clone_y), explosion_r, 3)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_mid"], alpha),
                      (clone_x, clone_y), max(1, explosion_r - 6), 2)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_light"], alpha),
                      (clone_x, clone_y), max(1, explosion_r - 12), 1)
            _NS_grimjack._aacircle(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                      (clone_x, clone_y), max(1, explosion_r - 18), 1)
            # Bright center.
            _NS_grimjack._aacircle(surface, _NS_grimjack.PALETTE["void_shine"], (clone_x, clone_y), 4)
            pygame.draw.rect(surface, _NS_grimjack.PALETTE["white"], (clone_x, clone_y, 1, 1))
            # Radial burst.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = clone_x + int(math.cos(angle_s) * explosion_r)
                ey = clone_y + int(math.sin(angle_s) * explosion_r * 0.7)
                pygame.draw.line(surface, (*_NS_grimjack.PALETTE["void_hot"], alpha),
                                 (clone_x, clone_y), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_grimjack.PALETTE["void_shine"], alpha),
                                 (ex, ey, 2, 2))



# ====================================================================
# MORVAETH (CRIMSON REAVER) - Mini Boss
# ====================================================================

class _NS_morvaeth:
    """Namespace morvaeth - Crimson assassin mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale ethereal)
        "skin_darkest": (85, 60, 65),
        "skin_dark": (150, 115, 115),
        "skin_mid": (210, 180, 180),
        "skin_light": (240, 215, 210),
        "skin_shine": (255, 240, 235),
        # Silver/white hair
        "hair_darkest": (50, 45, 55),
        "hair_dark": (110, 105, 115),
        "hair_mid": (180, 175, 190),
        "hair_light": (225, 220, 230),
        "hair_shine": (250, 250, 255),
        # Dark obsidian armor
        "armor_darkest": (10, 8, 15),
        "armor_dark": (30, 25, 40),
        "armor_mid": (60, 50, 70),
        "armor_light": (105, 90, 115),
        "armor_shine": (150, 130, 160),
        # Crimson/magenta pink accents (main FX)
        "crimson_darkest": (45, 5, 30),
        "crimson_dark": (110, 20, 65),
        "crimson_mid": (200, 40, 110),
        "crimson_light": (250, 90, 155),
        "crimson_hot": (255, 150, 200),
        "crimson_shine": (255, 220, 235),
        "crimson_white": (255, 245, 250),
        # Blood red (deeper accent)
        "blood_dark": (75, 10, 20),
        "blood_mid": (170, 30, 45),
        "blood_light": (230, 65, 80),
        # Cape (dark purple-red)
        "cape_darkest": (25, 10, 25),
        "cape_dark": (55, 20, 50),
        "cape_mid": (105, 35, 85),
        "cape_light": (160, 65, 130),
        # Spear/glaive blade (crimson steel)
        "blade_darkest": (40, 10, 25),
        "blade_dark": (100, 20, 55),
        "blade_mid": (185, 40, 100),
        "blade_light": (240, 90, 155),
        "blade_hot": (255, 160, 205),
        "blade_shine": (255, 230, 240),
        # Eye (glowing crimson red)
        "eye_iris": (200, 40, 60),
        "eye_glow": (255, 90, 110),
        "eye_hot": (255, 200, 200),
        # Void black (accent)
        "void_dark": (15, 5, 20),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morvaeth._clamp(color)
        if _NS_morvaeth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvaeth._clamp(color)
        if _NS_morvaeth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        # Guard against invalid polygon.
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_morvaeth._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_morvaeth._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_morvaeth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morvaeth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morvaeth._detect_moving(boss)
        _NS_morvaeth._update_mv_attack_anim(boss)
        attacking = (
            getattr(boss, "_mv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind.
        _NS_morvaeth._draw_crimson_aura(surface, x, y, pulse)
        _NS_morvaeth._draw_ground_crimson_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_morvaeth._draw_dawn_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvaeth._draw_finalslash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvaeth._draw_execution_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_morvaeth._draw_mv_attack(surface, boss, x, y)
        elif moving:
            _NS_morvaeth._draw_mv_float(surface, boss, x, y)
        else:
            _NS_morvaeth._draw_mv_idle(surface, boss, x, y)
        # Buff aura around body (E skill).
        if active_skill == "e":
            _NS_morvaeth._draw_finalslash_buff(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_morvaeth._draw_dawn_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvaeth._draw_vengeance_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvaeth._draw_execution_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mv_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mv_previous_timer", 0))
        active = bool(getattr(boss, "_mv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._mv_attack_active = True
            boss._mv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mv_attack_frame = int(
                getattr(boss, "_mv_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._mv_attack_active = False
            boss._mv_attack_frame = 0
            active = False
        boss._mv_previous_timer = timer
        boss._mv_attack_progress = (
            min(1.0, getattr(boss, "_mv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_mv_last_x"):
            boss._mv_last_x = boss.x
            boss._mv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mv_last_x)
        dy = abs(boss.y - boss._mv_last_y)
        boss._mv_last_x = boss.x
        boss._mv_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_mv_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3) - 5
        _NS_morvaeth._draw_shadow(surface, x, y + 50)
        _NS_morvaeth._draw_crimson_trail(surface, x, y + 42, boss.pulse, floating=True)
        _NS_morvaeth._draw_mv_body(surface, x, y + bob,
                     boss.direction, boss.pulse, "idle")
    def _draw_mv_float(surface, boss, x, y):
        """Floating movement (assassin glides)."""
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 0.9) * 5) - 7
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_morvaeth._draw_shadow(surface, x + sway, y + 50, moving=True)
        _NS_morvaeth._draw_crimson_trail(surface, x + sway, y + 42, phase,
                           floating=True, moving=True,
                           facing=boss.direction)
        _NS_morvaeth._draw_mv_body(surface, x + sway, y + bob,
                     boss.direction, phase, "float")
    def _draw_mv_attack(surface, boss, x, y):
        """Spear swing/thrust."""
        progress = getattr(boss, "_mv_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2) - 5
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * boss.direction
            lift = int(2 - t * 4) - 5
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2) - 5
        _NS_morvaeth._draw_shadow(surface, x + lunge, y + 50)
        _NS_morvaeth._draw_crimson_trail(surface, x + lunge, y + 42, boss.pulse,
                           floating=True, intense=True)
        _NS_morvaeth._draw_mv_body(surface, x + lunge, y + lift,
                     boss.direction, boss.pulse, "attack", progress)
        if 0.35 <= progress < 0.75:
            _NS_morvaeth._draw_spear_slash(surface, boss, x + lunge, y + lift,
                             progress)
    # ============================================================
    # BODY (Assassin humanoid with long spear)
    # ============================================================
    def _draw_mv_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw crimson assassin."""
        # Cape behind (flowing).
        _NS_morvaeth._draw_cape(surface, cx, cy, facing, phase, action)
        # Armor skirt bottom.
        _NS_morvaeth._draw_armor_skirt(surface, cx, cy + 22, facing, phase, action)
        # Torso (dark armor).
        _NS_morvaeth._draw_mv_torso(surface, cx, cy, facing, phase, action)
        # Back arm (hangs or supports).
        _NS_morvaeth._draw_back_arm(surface, cx, cy + 4, facing, phase, action,
                      attack_progress)
        # Head with long hair.
        _NS_morvaeth._draw_mv_head(surface, cx, cy - 22, facing, phase, action)
        # Front arm holding SPEAR/GLAIVE (foreground).
        _NS_morvaeth._draw_spear_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Dark purple cape trailing behind."""
        back_dir = -facing
        sway = math.sin(phase * 0.8) * 3
        cape_pts = [
            (cx + back_dir * 6, cy - 12),
            (cx + back_dir * 10, cy - 8),
            (cx + back_dir * 15 + int(sway), cy),
            (cx + back_dir * 18 + int(sway * 1.3), cy + 10),
            (cx + back_dir * 20 + int(sway * 1.5), cy + 22),
            (cx + back_dir * 16 + int(sway * 1.6), cy + 32),
            (cx + back_dir * 10 + int(sway * 1.4), cy + 36),
            (cx + back_dir * 2, cy + 32),
            (cx + back_dir * 5, cy + 20),
            (cx + back_dir * 8, cy + 4),
            (cx + back_dir * 6, cy - 6),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in cape_pts])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["cape_darkest"], cape_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["cape_dark"], [
            (cx + back_dir * 6, cy - 10),
            (cx + back_dir * 9, cy - 6),
            (cx + back_dir * 13 + int(sway), cy),
            (cx + back_dir * 16 + int(sway * 1.3), cy + 10),
            (cx + back_dir * 18 + int(sway * 1.5), cy + 22),
            (cx + back_dir * 14 + int(sway * 1.6), cy + 30),
            (cx + back_dir * 8 + int(sway * 1.4), cy + 32),
            (cx + back_dir * 4, cy + 28),
            (cx + back_dir * 8, cy + 4),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["cape_mid"], [
            (cx + back_dir * 8, cy - 6),
            (cx + back_dir * 11 + int(sway), cy + 2),
            (cx + back_dir * 13 + int(sway * 1.3), cy + 12),
            (cx + back_dir * 14 + int(sway * 1.5), cy + 22),
            (cx + back_dir * 10 + int(sway * 1.6), cy + 26),
            (cx + back_dir * 6, cy + 22),
        ])
        # Fold lines.
        for i, off in enumerate((8, 12, 16)):
            fold_x = cx + back_dir * off
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["cape_darkest"],
                             (fold_x, cy - 4),
                             (fold_x + int(sway * 0.8), cy + 24), 1)
        # Crimson glow trim on edge.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                         (cx + back_dir * 16 + int(sway * 1.5), cy + 22),
                         (cx + back_dir * 10 + int(sway * 1.5), cy + 34), 2)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                         (cx + back_dir * 15 + int(sway * 1.5), cy + 22),
                         (cx + back_dir * 10 + int(sway * 1.5), cy + 33), 1)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (cx + back_dir * 12 + int(sway * 1.5), cy + 28, 1, 1))
        # Bottom cape dissolution particles.
        for i in range(5):
            t = (phase * 0.4 + i * 0.15) % 1.0
            px = cx + back_dir * (10 + i * 3) + int(math.sin(phase + i) * 2)
            py = cy + 32 + int(t * 10)
            alpha = _NS_morvaeth._alpha(180 * (1 - t))
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                      (px, py), 2)
            pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                             (px, py, 1, 1))
    def _draw_armor_skirt(surface, cx, cy, facing, phase, action):
        """Dark armor plates bottom."""
        sway = math.sin(phase * 0.6) * 1
        skirt_pts = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 14 + int(sway), cy + 2),
            (cx + 12 + int(sway), cy + 12),
            (cx + 8, cy + 16),
            (cx - 8, cy + 16),
            (cx - 12 - int(sway), cy + 12),
            (cx - 14 - int(sway), cy + 2),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in skirt_pts])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], skirt_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_dark"], [
            (cx - 11, cy - 7),
            (cx + 11, cy - 7),
            (cx + 13 + int(sway), cy + 2),
            (cx + 11 + int(sway), cy + 11),
            (cx + 7, cy + 15),
            (cx - 7, cy + 15),
            (cx - 11 - int(sway), cy + 11),
            (cx - 13 - int(sway), cy + 2),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 10 + int(sway), cy + 2),
            (cx + 8 + int(sway), cy + 10),
            (cx - 8 - int(sway), cy + 10),
            (cx - 10 - int(sway), cy + 2),
        ])
        # Plate divisions.
        for x_off in (-7, -2, 2, 7):
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                             (cx + x_off, cy - 6),
                             (cx + x_off + int(sway * 0.5), cy + 14), 1)
        # Crimson central belt gem (V-shape).
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], [
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx, cy),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["crimson_darkest"], [
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx, cy - 1),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["crimson_dark"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                         (cx, cy - 4, 1, 2))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (cx, cy - 4, 1, 1))
        # Trim highlights.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_shine"],
                         (cx - 9, cy - 6), (cx + 9, cy - 6), 1)
        # Bottom crimson trim.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                         (cx - 7, cy + 12), (cx + 7, cy + 12), 1)
    def _draw_mv_torso(surface, cx, cy, facing, phase, action):
        """Elegant dark armored torso with crimson accents."""
        breath = math.sin(phase * 0.7) * 1
        # Torso outline (V-shape masculine).
        torso_pts = [
            (cx - 12, cy - 12),
            (cx - 14, cy - 8),
            (cx - 12, cy - 2),
            (cx - 9, cy + 6),
            (cx - 4, cy + 10),
            (cx + 4, cy + 10),
            (cx + 9, cy + 6),
            (cx + 12, cy - 2),
            (cx + 14, cy - 8),
            (cx + 12, cy - 12),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_pts])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], torso_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_dark"], [
            (cx - 11, cy - 11),
            (cx - 13, cy - 7),
            (cx - 11, cy - 2),
            (cx - 8, cy + 5),
            (cx - 3, cy + 9),
            (cx + 3, cy + 9),
            (cx + 8, cy + 5),
            (cx + 11, cy - 2),
            (cx + 13, cy - 7),
            (cx + 11, cy - 11),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
            (cx - 9, cy - 9),
            (cx - 11, cy - 5),
            (cx - 9, cy),
            (cx - 5, cy + 5),
            (cx + 5, cy + 5),
            (cx + 9, cy),
            (cx + 11, cy - 5),
            (cx + 9, cy - 9),
        ])
        # Armor plate line highlights.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_light"],
                         (cx - 7, cy - 8), (cx - 6, cy - 4), 1)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_light"],
                         (cx + 7, cy - 8), (cx + 6, cy - 4), 1)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_shine"],
                         (cx + facing * 6, cy - 8, 1, 1))
        # CRIMSON CHEST CRYSTAL (V-shape gem).
        crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
        crystal_alpha = _NS_morvaeth._alpha(240 * crystal_pulse)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx, cy - 1),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["crimson_darkest"], [
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx, cy - 2),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["crimson_dark"], [
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                         (cx - 1, cy - 5, 2, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (cx, cy - 5, 1, 1))
        # Glow around chest crystal.
        for r in range(4, 0, -1):
            alpha = _NS_morvaeth._alpha(80 * (4 - r) / 4 * crystal_pulse)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                      (cx, cy - 5), r)
        # Crimson stripes on armor sides.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                         (cx - 10, cy - 6), (cx - 8, cy + 2), 1)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                         (cx + 10, cy - 6), (cx + 8, cy + 2), 1)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                         (cx - 9, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                         (cx + 9, cy - 3, 1, 1))
        # Pauldrons (angular, sharp).
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 10
            # Angular pauldron.
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
                (sh_x - 3, sh_y),
                (sh_x + 5 * side, sh_y - 3),
                (sh_x + 6 * side, sh_y + 3),
                (sh_x - 2, sh_y + 4),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], [
                (sh_x - 3, sh_y),
                (sh_x + 5 * side, sh_y - 3),
                (sh_x + 5 * side, sh_y + 3),
                (sh_x - 2, sh_y + 3),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_dark"], [
                (sh_x - 2, sh_y),
                (sh_x + 4 * side, sh_y - 2),
                (sh_x + 4 * side, sh_y + 2),
                (sh_x - 1, sh_y + 2),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
                (sh_x - 1, sh_y),
                (sh_x + 3 * side, sh_y - 1),
                (sh_x + 3 * side, sh_y + 1),
                (sh_x, sh_y + 1),
            ])
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_shine"],
                             (sh_x + side, sh_y - 1, 1, 1))
            # Crimson accent line on pauldron.
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                             (sh_x, sh_y + 3),
                             (sh_x + 4 * side, sh_y + 2), 1)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                             (sh_x + 2 * side, sh_y + 2, 1, 1))
            # Small spike on pauldron top.
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], [
                (sh_x + 2 * side, sh_y - 2),
                (sh_x + 3 * side, sh_y - 5),
                (sh_x + 4 * side, sh_y - 2),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
                (sh_x + 3 * side, sh_y - 4),
                (sh_x + 3 * side, sh_y - 2),
                (sh_x + 4 * side, sh_y - 2),
            ])
    def _draw_mv_head(surface, cx, cy, facing, phase, action):
        """Elegant pale face with long silver hair."""
        # Long silver hair back (very long).
        _NS_morvaeth._draw_long_hair_back(surface, cx, cy, facing, phase)
        # Face (angular masculine).
        face_pts = [
            (cx - 6, cy),
            (cx - 7, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 7, cy - 4),
            (cx + 6, cy),
            (cx + 4, cy + 5),
            (cx + 1, cy + 7),
            (cx - 1, cy + 7),
            (cx - 4, cy + 5),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in face_pts])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["skin_darkest"], face_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["skin_dark"], [
            (cx - 5, cy),
            (cx - 6, cy - 4),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 6, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["skin_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy - 4),
            (cx - 3, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy - 4),
            (cx + 4, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Sharp cheekbone.
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["skin_light"],
                         (cx + facing * 3, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["skin_shine"],
                         (cx + facing * 3, cy - 2, 1, 1))
        # Silver hair bangs (front, long side strand).
        _NS_morvaeth._draw_long_hair_front(surface, cx, cy - 7, facing, phase)
        # EYES (glowing crimson red, intense).
        # Main eye.
        ex = cx + facing * 2
        ey = cy - 3
        for r in range(4, 0, -1):
            alpha = _NS_morvaeth._alpha(180 * (4 - r) / 4)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["eye_glow"], alpha),
                      (ex, ey), r)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["eye_iris"], (ex, ey, 2, 2))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["eye_glow"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["eye_hot"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (ex + 1, ey, 1, 1))
        # Second eye (dimmer).
        ex2 = cx - facing * 2
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                         (ex2 - 1, ey, 2, 2))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["eye_iris"], (ex2, ey, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["eye_glow"], (ex2, ey, 1, 1))
        # Sharp eyebrows.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["hair_darkest"],
                         (cx - 5, cy - 5), (cx - 1, cy - 6), 1)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["hair_darkest"],
                         (cx + 1, cy - 6), (cx + 5, cy - 5), 1)
        # Delicate stern lips.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["blood_dark"],
                         (cx - 1, cy + 3), (cx + 1, cy + 3), 1)
    def _draw_long_hair_back(surface, cx, cy, facing, phase):
        """VERY long silver flowing hair."""
        sway = math.sin(phase * 0.7) * 4
        # Long hair mass (extends far below).
        hair_pts = [
            (cx - 7, cy - 8),
            (cx - 10, cy - 4),
            (cx - 13 - int(sway * 0.5), cy + 6),
            (cx - 15 - int(sway), cy + 18),
            (cx - 14 - int(sway * 1.5), cy + 30),
            (cx - 10 - int(sway * 1.8), cy + 40),
            (cx - 4 - int(sway * 1.5), cy + 44),
            (cx + 4 + int(sway * 1.5), cy + 44),
            (cx + 10 + int(sway * 1.8), cy + 40),
            (cx + 14 + int(sway * 1.5), cy + 30),
            (cx + 15 + int(sway), cy + 18),
            (cx + 13 + int(sway * 0.5), cy + 6),
            (cx + 10, cy - 4),
            (cx + 7, cy - 8),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in hair_pts])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_darkest"], hair_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_dark"], [
            (cx - 6, cy - 7),
            (cx - 9, cy - 3),
            (cx - 12 - int(sway * 0.5), cy + 6),
            (cx - 13 - int(sway), cy + 18),
            (cx - 12 - int(sway * 1.5), cy + 28),
            (cx - 8 - int(sway * 1.8), cy + 38),
            (cx + 8 + int(sway * 1.8), cy + 38),
            (cx + 12 + int(sway * 1.5), cy + 28),
            (cx + 13 + int(sway), cy + 18),
            (cx + 12 + int(sway * 0.5), cy + 6),
            (cx + 9, cy - 3),
            (cx + 6, cy - 7),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_mid"], [
            (cx - 5, cy - 5),
            (cx - 8, cy),
            (cx - 10 - int(sway * 0.5), cy + 10),
            (cx - 10 - int(sway), cy + 20),
            (cx - 6 - int(sway * 1.5), cy + 28),
            (cx + 6 + int(sway * 1.5), cy + 28),
            (cx + 10 + int(sway), cy + 20),
            (cx + 10 + int(sway * 0.5), cy + 10),
            (cx + 8, cy),
            (cx + 5, cy - 5),
        ])
        # Silver strand highlights.
        for i, x_off in enumerate((-8, -4, 4, 8)):
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["hair_light"],
                             (cx + x_off, cy - 4),
                             (cx + x_off + int(sway * 0.3), cy + 32), 1)
        # Bright shine strands.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["hair_shine"],
                         (cx - 3, cy - 6),
                         (cx - 2 + int(sway * 0.3), cy + 30), 1)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["hair_shine"],
                         (cx + 3, cy - 6),
                         (cx + 2 + int(sway * 0.3), cy + 30), 1)
        # Bottom hair particles (dissolution).
        for i in range(4):
            t = (phase * 0.3 + i * 0.2) % 1.0
            px = cx + int((i - 1.5) * 6) + int(math.sin(phase + i) * 3)
            py = cy + 44 + int(t * 8)
            alpha = _NS_morvaeth._alpha(150 * (1 - t))
            pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["hair_light"], alpha),
                             (px, py, 1, 1))
    def _draw_long_hair_front(surface, cx, cy, facing, phase):
        """Silver bangs framing face."""
        # Bangs.
        bang_pts = [
            (cx - 6, cy + 3),
            (cx - 7, cy),
            (cx - 4, cy - 3),
            (cx, cy - 4),
            (cx + 4, cy - 3),
            (cx + 7, cy),
            (cx + 6, cy + 3),
            (cx + 3, cy),
            (cx - 3, cy),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_darkest"], bang_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_dark"], [
            (cx - 5, cy + 2),
            (cx - 6, cy),
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 6, cy),
            (cx + 5, cy + 2),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_mid"], [
            (cx - 4, cy + 1),
            (cx - 4, cy - 1),
            (cx - 1, cy - 2),
            (cx + 3, cy - 2),
            (cx + 5, cy - 1),
            (cx + 4, cy + 1),
        ])
        # Highlights.
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["hair_light"],
                         (cx - 2, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["hair_shine"],
                         (cx - 1, cy - 2, 1, 1))
        # Long side strand (falls to shoulder).
        strand_pts = [
            (cx + facing * 5, cy - 1),
            (cx + facing * 7, cy + 4),
            (cx + facing * 6, cy + 10),
            (cx + facing * 3, cy + 8),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_darkest"], strand_pts)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["hair_mid"], [
            (cx + facing * 5, cy),
            (cx + facing * 6, cy + 4),
            (cx + facing * 5, cy + 8),
        ])
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["hair_light"],
                         (cx + facing * 5, cy + 1),
                         (cx + facing * 5, cy + 7), 1)
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm hangs at side."""
        back_dir = -facing
        b_shoulder_x = cx + back_dir * 11
        b_shoulder_y = cy - 8
        sway = math.sin(phase * 0.6) * 1
        b_elbow_x = b_shoulder_x + back_dir * 2 + int(sway)
        b_elbow_y = b_shoulder_y + 8
        b_hand_x = b_elbow_x + back_dir * 1 + int(sway)
        b_hand_y = b_elbow_y + 8
        # Upper arm.
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                (b_shoulder_x + 1, b_shoulder_y + 1),
                (b_elbow_x + 1, b_elbow_y + 1), 5)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                (b_shoulder_x, b_shoulder_y), (b_elbow_x, b_elbow_y), 4)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                (b_shoulder_x, b_shoulder_y), (b_elbow_x, b_elbow_y), 3)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                (b_shoulder_x + back_dir, b_shoulder_y),
                (b_elbow_x + back_dir, b_elbow_y), 1)
        # Elbow.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                  (b_elbow_x, b_elbow_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_dark"],
                  (b_elbow_x, b_elbow_y), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                         (b_elbow_x, b_elbow_y, 1, 1))
        # Forearm.
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                (b_elbow_x + 1, b_elbow_y + 1),
                (b_hand_x + 1, b_hand_y + 1), 4)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 3)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 2)
        # Gauntlet.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                  (b_hand_x, b_hand_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_dark"],
                  (b_hand_x, b_hand_y), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_mid"],
                         (b_hand_x, b_hand_y - 1, 1, 1))
    def _draw_spear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding LONG spear/glaive."""
        shoulder_x = cx + facing * 11
        shoulder_y = cy - 8
        # Angle convention: 0 = forward, pi/2 = UP.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise spear back.
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.5 + t * 0.35)
                spear_extra = math.pi * 0.25
            elif attack_progress < 0.6:
                # Slash down-forward.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (0.85 - t * 1.05)
                spear_extra = math.pi * (0.25 - t * 0.5)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.2 + t * 0.35)
                spear_extra = math.pi * (-0.25 + t * 0.35)
        elif action == "float":
            # Spear held forward.
            arm_angle = math.pi * 0.15 + math.sin(phase) * 0.05
            spear_extra = math.pi * 0.05
        else:
            arm_angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.03
            spear_extra = math.pi * 0.05
        upper_len = 10
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)
        forearm_len = 10
        hand_angle = arm_angle - math.pi * 0.15
        hand_x = elbow_x + int(math.cos(hand_angle) * forearm_len) * facing
        hand_y = elbow_y - int(math.sin(hand_angle) * forearm_len)
        # Upper arm.
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 6)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_light"],
                         (shoulder_x + facing * 2, shoulder_y - 1, 1, 1))
        # Elbow armor.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                  (elbow_x, elbow_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_dark"],
                  (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                         (elbow_x, elbow_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (elbow_x, elbow_y, 1, 1))
        # Forearm.
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1),
                (hand_x + 1, hand_y + 1), 5)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Gauntlet.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                  (hand_x + 1, hand_y + 1), 4)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                  (hand_x, hand_y), 4)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_dark"],
                  (hand_x, hand_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_mid"],
                  (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (hand_x - 1, hand_y - 1, 1, 1))
        # LONG CRIMSON SPEAR/GLAIVE.
        spear_angle = hand_angle + spear_extra
        _NS_morvaeth._draw_crimson_spear(surface, hand_x, hand_y, spear_angle,
                           facing, phase)
    def _draw_crimson_spear(surface, hx, hy, angle, facing, phase):
        """LONG crimson glaive spear."""
        # Shaft handle (behind hand, short back).
        handle_len = 12
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy + int(math.sin(angle) * handle_len)
        # Shaft (dark obsidian).
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                (hx, hy), (handle_end_x, handle_end_y), 3)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                (hx, hy), (handle_end_x, handle_end_y), 2)
        # Crimson wrap on shaft.
        for i in range(2):
            t = (i + 1) / 3
            wx = int(hx + (handle_end_x - hx) * t)
            wy = int(hy + (handle_end_y - hy) * t)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                             (wx, wy, 1, 1))
        # Pommel (spike back end).
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                  (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                  (handle_end_x, handle_end_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_darkest"],
                  (handle_end_x, handle_end_y), 2)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                  (handle_end_x, handle_end_y), 1)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (handle_end_x, handle_end_y, 1, 1))
        # LONG BLADE (extending forward from hand, curved crescent-like).
        blade_len = 44  # LONG!
        # Slight curve.
        curve_angle_1 = angle + math.pi * 0.02
        curve_angle_2 = angle + math.pi * 0.08
        mid_x = hx + int(math.cos(curve_angle_1)
                          * blade_len * 0.5) * facing
        mid_y = hy - int(math.sin(curve_angle_1) * blade_len * 0.5)
        tip_x = mid_x + int(math.cos(curve_angle_2)
                             * blade_len * 0.55) * facing
        tip_y = mid_y - int(math.sin(curve_angle_2) * blade_len * 0.55)
        # Draw segmented blade.
        segments = 14
        prev = (hx, hy)
        for i in range(1, segments + 1):
            t = i / segments
            bx = int((1 - t) ** 2 * hx + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * hy + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            thickness = max(1, 5 - int(t * 3))
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1),
                    thickness + 1)
            # Dark blade edge.
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["blade_darkest"],
                    prev, (bx, by), thickness)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["blade_dark"],
                    prev, (bx, by), max(1, thickness - 1))
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["blade_mid"],
                    prev, (bx, by), max(1, thickness - 2))
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["blade_light"],
                    prev, (bx, by), max(1, thickness - 3))
            # Bright hot line down center.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["blade_hot"],
                                 (bx, by, 1, 1))
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["blade_shine"],
                                 (bx, by, 1, 1))
            prev = (bx, by)
        # Sharp tip.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["blade_darkest"],
                  (tip_x, tip_y), 2)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["blade_mid"],
                  (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["blade_hot"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["blade_shine"],
                         (tip_x, tip_y, 1, 1))
        # Crimson glow around blade (energy).
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 1, -1):
            alpha = _NS_morvaeth._alpha(80 * (6 - r) / 6 * glow_pulse)
            glow_mid_x = int(hx + (tip_x - hx) * 0.5)
            glow_mid_y = int(hy + (tip_y - hy) * 0.5)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_light"], alpha),
                      (glow_mid_x, glow_mid_y), r)
        # Bright energy line ON the blade (following its length).
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                         (hx, hy), (tip_x, tip_y), 1)
    def _draw_spear_slash(surface, boss, cx, cy, progress):
        """Crimson slash arc during spear swing."""
        facing = boss.direction
        swing_t = max(0.0, min(1.0, (progress - 0.35) / 0.4))
        arc_center_x = cx + facing * 6
        arc_center_y = cy - 4
        radius = 38  # LARGE arc due to long spear
        num_slices = 14
        for slice_i in range(num_slices):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.75
            sweep_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.1)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            fade = 1 - slice_t * 0.75
            alpha = _NS_morvaeth._alpha(240 * fade
                            * (1 - abs(swing_t - 0.5) * 1.4))
            if alpha <= 0:
                continue
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            size = max(2, int(7 * fade))
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                      (arc_x, arc_y), size + 1)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                      (arc_x, arc_y), size)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                      (arc_x, arc_y), max(1, size - 1))
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_light"], alpha),
                      (arc_x, arc_y), max(1, size - 2))
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                      (arc_x, arc_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                             (arc_x, arc_y, 1, 1))
        # Bright leading edge crescent.
        crescent_pts = []
        for slice_i in range(num_slices + 1):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.75
            sweep_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.06)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            crescent_pts.append((arc_x, arc_y))
        if len(crescent_pts) > 1:
            for i in range(len(crescent_pts) - 1):
                alpha = _NS_morvaeth._alpha(240 * (1 - abs(swing_t - 0.5) * 1.4))
                _NS_morvaeth._aaline(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 2)
                _NS_morvaeth._aaline(surface, (*_NS_morvaeth.PALETTE["crimson_white"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 1)
    # ============================================================
    # CRIMSON TRAIL / AMBIENT
    # ============================================================
    def _draw_crimson_trail(surface, cx, cy, phase, floating=False,
                              moving=False, intense=False, facing=1):
        """Crimson particles rising below assassin."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Crimson mist cloud.
        mist = pygame.Surface((150, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.3) * 0.3 + 0.7
        for radius in range(30, 3, -2):
            alpha = _NS_morvaeth._alpha((30 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_morvaeth._alpha((18 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                    (75 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 8))
        # Rising crimson particles.
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24, -28)):
            t = (phase * 0.5 + i * 0.12) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 22)
            alpha = _NS_morvaeth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                      (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                             (sx, sy - 1, 1, 1))
        # Bright pink sparkles.
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.1) % 1.0
            ex = cx - 24 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 2 - int(spark_t * 20)
            alpha = _NS_morvaeth._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail.
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_morvaeth._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                          (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                                 (sx, sy - 1, 1, 1))
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((130, 28), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 14 - radius, 110 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 8, 160), (5, 8, 120, 12))
        pygame.draw.ellipse(shadow, (60, 20, 40, 100), (12, 10, 106, 8))
        surface.blit(shadow, (x - 65, y - 14))
    def _draw_crimson_aura(surface, x, y, phase):
        """Crimson aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_morvaeth._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvaeth._aacircle(aura, (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                          (100, 90), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_morvaeth._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvaeth._aacircle(aura, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                          (100, 90), radius)
        for radius in range(30, 5, -2):
            alpha = _NS_morvaeth._alpha((30 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_morvaeth._aacircle(aura, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Floating crimson embers.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            r = 38 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"], (sx, sy, 1, 1))
    def _draw_ground_crimson_ring(surface, x, y, phase, skill):
        """Ground ring with crimson runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 52), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["crimson_darkest"], 200),
                            (5, 17, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["crimson_dark"], 220),
                            (14, 19, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["crimson_mid"], 200),
                            (25, 21, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["blood_dark"], 180),
                            (40, 23, 90, 14), 1)
        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 29 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 29 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morvaeth.PALETTE["crimson_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, (*_NS_morvaeth.PALETTE["crimson_shine"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["crimson_hot"],
                                        _NS_morvaeth._alpha(150 * pulse)),
                                (15, 11, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 26))
    # ============================================================
    # SKILL Q: DAWN'S APB (dash forward with spear thrust)
    # ============================================================
    def _draw_dawn_ground(surface, boss, x, y, timer, phase):
        """Dash streak on ground."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return
        t = (progress - 0.3) / 0.7
        length = int(t * 150)
        if length > 5:
            for i in range(3):
                h = 6 - i * 2
                if facing > 0:
                    pygame.draw.ellipse(surface,
                                        (*_NS_morvaeth.PALETTE["crimson_mid"],
                                         180 - i * 50),
                                        (x, y + 32 - h, length, h * 2))
                else:
                    pygame.draw.ellipse(surface,
                                        (*_NS_morvaeth.PALETTE["crimson_mid"],
                                         180 - i * 50),
                                        (x - length, y + 32 - h, length, h * 2))
    def _draw_dawn_foreground(surface, boss, x, y, timer, phase):
        """Dash forward with crimson streak."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvaeth._target_position(boss, x, y)
        if progress < 0.3:
            # Wind-up.
            t = progress / 0.3
            charge_x = x + facing * 22
            charge_y = y - 10
            cr = int(5 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morvaeth._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                          (charge_x, charge_y), r)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                      (charge_x, charge_y), cr - 3)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_light"],
                      (charge_x, charge_y), max(1, cr - 6))
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                      (charge_x, charge_y), max(1, cr - 9))
        else:
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 22
            start_y = y - 8
            # Dash beam forward (crimson line).
            beam_end_x = int(start_x + (tx - start_x) * min(1.0, t * 1.4))
            beam_end_y = int(start_y + (ty - start_y) * min(1.0, t * 1.4))
            # Layered dash beam.
            for width, color, alpha_val in [
                (8, _NS_morvaeth.PALETTE["crimson_darkest"], 180),
                (5, _NS_morvaeth.PALETTE["crimson_dark"], 220),
                (3, _NS_morvaeth.PALETTE["crimson_mid"], 240),
                (2, _NS_morvaeth.PALETTE["crimson_light"], 250),
                (1, _NS_morvaeth.PALETTE["crimson_shine"], 255),
            ]:
                pygame.draw.line(surface, (*color, alpha_val),
                                 (start_x, start_y),
                                 (beam_end_x, beam_end_y), width)
            # Spear thrust head at end.
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_darkest"],
                      (beam_end_x, beam_end_y), 9)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_dark"],
                      (beam_end_x, beam_end_y), 7)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_mid"],
                      (beam_end_x, beam_end_y), 5)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_light"],
                      (beam_end_x, beam_end_y), 3)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                      (beam_end_x, beam_end_y), 2)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                      (beam_end_x, beam_end_y), 1)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"],
                             (beam_end_x, beam_end_y, 1, 1))
            # 4-point crimson star at head.
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                             (beam_end_x - 8, beam_end_y),
                             (beam_end_x + 8, beam_end_y), 1)
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                             (beam_end_x, beam_end_y - 8),
                             (beam_end_x, beam_end_y + 8), 1)
            # Trailing sparks.
            beam_dx = beam_end_x - start_x
            beam_dy = beam_end_y - start_y
            beam_len = max(1, math.sqrt(beam_dx ** 2 + beam_dy ** 2))
            for i in range(int(beam_len / 10)):
                trail_t = i * 10 / beam_len
                px = int(start_x + beam_dx * trail_t)
                py = int(start_y + beam_dy * trail_t)
                perp_x = -beam_dy / beam_len
                perp_y = beam_dx / beam_len
                offset = math.sin(phase * 5 + i) * 5
                spx = int(px + perp_x * offset)
                spy = int(py + perp_y * offset)
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"], (spx, spy, 2, 2))
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_shine"], (spx, spy, 1, 1))
    # ============================================================
    # SKILL W: VENGEANCE (fan-shape AoE arc + pull)
    # ============================================================
    def _draw_vengeance_skill(surface, boss, x, y, timer, phase):
        """Fan-shape crimson arc that pulls enemies."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Wind-up.
            t = progress / 0.15
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                r = int(4 + t * 10)
                sx = x + facing * 20 + int(math.cos(angle) * r)
                sy = y - 10 + int(math.sin(angle) * r)
                alpha = _NS_morvaeth._alpha(200)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                          (sx, sy), 2)
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.15) / 0.85
            # Fan-shape arc (wider than basic slash).
            arc_center_x = x + facing * 10
            arc_center_y = y - 8
            # Full fan sweep.
            fan_start = math.pi * 0.85
            fan_end = -math.pi * 0.25
            fan_range = fan_start - fan_end
            # Grow radius over time.
            max_radius = 60
            radius = int(max_radius * min(1.0, t * 1.5))
            # Draw fan as multiple radial "spokes" and arcs.
            num_spokes = 10
            for spoke_i in range(num_spokes + 1):
                spoke_t = spoke_i / num_spokes
                spoke_angle = fan_start - fan_range * spoke_t
                # Fill along spoke with fading particles.
                num_particles = 8
                for p_i in range(num_particles):
                    p_t = (p_i + 1) / num_particles
                    px = arc_center_x + int(math.cos(spoke_angle)
                                              * radius * p_t) * facing
                    py = arc_center_y - int(math.sin(spoke_angle)
                                             * radius * p_t)
                    # Fade toward outer.
                    fade = 1 - p_t * 0.4
                    alpha = _NS_morvaeth._alpha(200 * fade * (1 - t * 0.4))
                    if alpha <= 0:
                        continue
                    _NS_morvaeth._aacircle(surface,
                              (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                              (px, py), 3)
                    _NS_morvaeth._aacircle(surface,
                              (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                              (px, py), 2)
                    _NS_morvaeth._aacircle(surface,
                              (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                              (px, py), 1)
                    if p_i % 2 == 0:
                        pygame.draw.rect(surface,
                                         (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                                         (px, py, 1, 1))
            # Bright OUTER arc (crescent line).
            arc_pts = []
            for i in range(num_spokes * 2 + 1):
                arc_t = i / (num_spokes * 2)
                arc_angle = fan_start - fan_range * arc_t
                ax = arc_center_x + int(math.cos(arc_angle) * radius) * facing
                ay = arc_center_y - int(math.sin(arc_angle) * radius)
                arc_pts.append((ax, ay))
            if len(arc_pts) > 1:
                for i in range(len(arc_pts) - 1):
                    alpha = _NS_morvaeth._alpha(250 * (1 - t * 0.3))
                    _NS_morvaeth._aaline(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                            arc_pts[i], arc_pts[i + 1], 3)
                    _NS_morvaeth._aaline(surface, (*_NS_morvaeth.PALETTE["crimson_white"], alpha),
                            arc_pts[i], arc_pts[i + 1], 1)
            # Pull arrows (from outer inward - PULL effect indicator).
            for spoke_i in range(0, num_spokes + 1, 2):
                spoke_t = spoke_i / num_spokes
                spoke_angle = fan_start - fan_range * spoke_t
                outer_x = arc_center_x + int(math.cos(spoke_angle)
                                              * radius) * facing
                outer_y = arc_center_y - int(math.sin(spoke_angle) * radius)
                inner_x = arc_center_x + int(math.cos(spoke_angle)
                                              * (radius - 20)) * facing
                inner_y = arc_center_y - int(math.sin(spoke_angle)
                                              * (radius - 20))
                alpha = _NS_morvaeth._alpha(220 * (1 - t * 0.5))
                pygame.draw.line(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                                 (outer_x, outer_y), (inner_x, inner_y), 2)
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                                 (inner_x, inner_y, 2, 2))
    # ============================================================
    # SKILL E: FINAL SLASH (buff + heal aura)
    # ============================================================
    def _draw_finalslash_ground(surface, boss, x, y, timer, phase):
        """Ground buff rings under boss."""
        for i in range(3):
            r = int(32 + i * 8 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_morvaeth._alpha(200 - i * 50)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                      (x, y + 42), r, 2)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_light"], alpha),
                      (x, y + 42), r, 1)
    def _draw_finalslash_buff(surface, boss, x, y, timer, phase):
        """Buff aura around boss - rotating marks + heal glow."""
        # Rotating crimson marks (4-point stars).
        num_marks = 6
        for i in range(num_marks):
            angle = phase * 1.5 + i * math.pi * 2 / num_marks
            orbit_r = 32
            sx = x + int(math.cos(angle) * orbit_r)
            sy = y - 5 + int(math.sin(angle) * orbit_r * 0.5)
            # Trail.
            for tr in range(3):
                trail_angle = angle - tr * 0.15
                tx_pos = x + int(math.cos(trail_angle) * orbit_r)
                ty_pos = y - 5 + int(math.sin(trail_angle) * orbit_r * 0.5)
                alpha = _NS_morvaeth._alpha(230 - tr * 60)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                          (tx_pos, ty_pos), max(1, 3 - tr))
            # 4-point star (mark shape).
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_dark"], (sx, sy), 4)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_mid"], (sx, sy), 3)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_light"], (sx, sy), 2)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_shine"], (sx, sy), 1)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (sx, sy, 1, 1))
            # Star rays.
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                             (sx - 4, sy), (sx + 4, sy), 1)
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                             (sx, sy - 4), (sx, sy + 4), 1)
        # Heal +HP indicator (rising particles).
        for i in range(6):
            heal_t = (phase * 0.6 + i * 0.15) % 1.0
            hx = x + int((i - 2.5) * 8) + int(math.sin(phase + i) * 3)
            hy = y - 5 - int(heal_t * 40)
            alpha = _NS_morvaeth._alpha(230 * (1 - heal_t))
            if alpha > 0:
                # Green heal color (mix crimson-hot).
                _NS_morvaeth._aacircle(surface, (100, 220, 100, alpha), (hx, hy), 2)
                pygame.draw.rect(surface, (180, 255, 180, alpha), (hx, hy, 1, 1))
                pygame.draw.rect(surface, (255, 255, 255, alpha), (hx, hy, 1, 1))
    # ============================================================
    # SKILL R: EXECUTION (leap up + slam down)
    # ============================================================
    def _draw_execution_ground(surface, boss, x, y, timer, phase):
        """Ground target zone marker."""
        tx, ty = _NS_morvaeth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Wind-up: warning circle grows.
            t = progress / 0.5
            r = int(35 * t)
            alpha = _NS_morvaeth._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning marks.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["crimson_hot"], (sx, sy, 2, 2))
        else:
            # Post-impact.
            t = (progress - 0.5) / 0.5
            r = int(35 + t * 25)
            alpha = _NS_morvaeth._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_execution_foreground(surface, boss, x, y, timer, phase):
        """Leap up + slam down with crimson explosion."""
        tx, ty = _NS_morvaeth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.35:
            # LEAP UP phase - boss visible from above.
            t = progress / 0.35
            # Show ascending line + energy gathering above target.
            leap_y = ty - int(t * 100)
            leap_r = int(6 + t * 6)
            for r in range(leap_r + 4, 0, -1):
                alpha = _NS_morvaeth._alpha(180 * (leap_r + 4 - r) / (leap_r + 4))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                          (tx, leap_y), r)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_mid"], (tx, leap_y),
                      leap_r - 2)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_light"],
                      (tx, leap_y), max(1, leap_r - 4))
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_shine"],
                      (tx, leap_y), max(1, leap_r - 6))
            # Trail down from sky.
            for i in range(6):
                tr_t = t - i * 0.05
                if tr_t <= 0:
                    continue
                tr_y = ty - int(tr_t * 100)
                alpha = _NS_morvaeth._alpha(150 - i * 20)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                          (tx, tr_y), max(1, 4 - i))
        elif progress < 0.55:
            # SLAM DOWN phase.
            t = (progress - 0.35) / 0.2
            # Descending line (fast, from top of screen).
            slam_start_y = max(0, ty - 100)
            slam_y = int(slam_start_y + (ty - slam_start_y) * t)
            # Bright descending beam.
            for width, color, alpha_val in [
                (12, _NS_morvaeth.PALETTE["crimson_darkest"], 140),
                (8, _NS_morvaeth.PALETTE["crimson_dark"], 180),
                (5, _NS_morvaeth.PALETTE["crimson_mid"], 220),
                (3, _NS_morvaeth.PALETTE["crimson_light"], 250),
                (1, _NS_morvaeth.PALETTE["crimson_shine"], 255),
            ]:
                pygame.draw.line(surface, (*color, alpha_val),
                                 (tx, slam_start_y),
                                 (tx, slam_y), width)
            # Bright head (descending).
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_darkest"], (tx, slam_y), 10)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_dark"], (tx, slam_y), 7)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_mid"], (tx, slam_y), 5)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_light"], (tx, slam_y), 3)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_hot"], (tx, slam_y), 2)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_shine"], (tx, slam_y), 1)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (tx, slam_y, 1, 1))
        elif progress < 0.85:
            # IMPACT EXPLOSION.
            t = (progress - 0.55) / 0.3
            impact_r = int(20 + t * 60)
            alpha = _NS_morvaeth._alpha(240 * (1 - t * 0.5))
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_darkest"], alpha),
                      (tx, ty), impact_r + 4, 4)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                      (tx, ty), impact_r, 4)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                      (tx, ty), max(1, impact_r - 6), 3)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_light"], alpha),
                      (tx, ty), max(1, impact_r - 12), 2)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                      (tx, ty), max(1, impact_r - 18), 1)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                      (tx, ty), max(1, impact_r // 4))
            # Bright center core.
            core_r = max(3, int(20 - t * 15))
            for r in range(core_r + 5, 0, -1):
                core_alpha = _NS_morvaeth._alpha(200 * (core_r + 5 - r) / (core_r + 5)
                                     * (1 - t * 0.3))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], core_alpha),
                          (tx, ty), r)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["crimson_shine"], (tx, ty), core_r // 2)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (tx, ty, 1, 1))
            # Radial burst rays.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_white"], alpha),
                                 (ex, ey, 2, 2))
            # Cross/star mark at center (suppress effect indicator).
            for i in range(4):
                cross_angle = i * math.pi / 2 + math.pi / 4
                cx_end = tx + int(math.cos(cross_angle) * (impact_r + 8))
                cy_end = ty + int(math.sin(cross_angle) * (impact_r + 8) * 0.7)
                pygame.draw.line(surface, (*_NS_morvaeth.PALETTE["crimson_shine"], alpha),
                                 (tx, ty), (cx_end, cy_end), 2)
        else:
            # Aftermath: lingering marks.
            t = (progress - 0.85) / 0.15
            for i in range(8):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 40)
                alpha = _NS_morvaeth._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_dark"], alpha),
                              (rx, ry), 3)
                    _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["crimson_mid"], alpha),
                              (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["crimson_hot"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# VULKARETH (EMBERBORN TITAN) - Mini Boss
# ====================================================================

class _NS_vulkareth:
    """Namespace vulkareth - Lava Demon mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Obsidian black (skin/armor)
        "obs_darkest": (8, 5, 8),
        "obs_dark": (25, 18, 22),
        "obs_mid": (55, 40, 45),
        "obs_light": (95, 70, 75),
        "obs_shine": (140, 105, 110),
        # Lava cracks (glowing through skin)
        "crack_darkest": (60, 15, 5),
        "crack_dark": (140, 45, 10),
        "crack_mid": (220, 90, 20),
        "crack_light": (255, 155, 40),
        "crack_hot": (255, 210, 90),
        "crack_shine": (255, 245, 170),
        # Fire/lava FX main
        "fire_darkest": (65, 15, 5),
        "fire_dark": (155, 45, 10),
        "fire_mid": (230, 95, 20),
        "fire_light": (255, 165, 55),
        "fire_hot": (255, 220, 110),
        "fire_shine": (255, 250, 200),
        "fire_white": (255, 255, 240),
        # Molten lava (ground pools)
        "lava_darkest": (50, 10, 5),
        "lava_dark": (130, 35, 8),
        "lava_mid": (210, 75, 15),
        "lava_light": (250, 145, 35),
        "lava_hot": (255, 200, 75),
        # Bone/horn (curved horns)
        "horn_darkest": (30, 20, 15),
        "horn_dark": (75, 55, 40),
        "horn_mid": (130, 100, 75),
        "horn_light": (190, 155, 120),
        # Iron armor accents (spikes)
        "iron_dark": (35, 30, 25),
        "iron_mid": (85, 75, 65),
        "iron_light": (150, 140, 125),
        # Eye (glowing red-orange)
        "eye_glow": (255, 80, 20),
        "eye_hot": (255, 180, 60),
        "eye_white": (255, 240, 180),
        # Weapon blade (dark obsidian with fire)
        "blade_dark": (30, 20, 20),
        "blade_mid": (75, 60, 60),
        "blade_light": (130, 105, 100),
        # Nether (Cataclysm form - purple/red accent)
        "nether_dark": (35, 10, 30),
        "nether_mid": (110, 30, 90),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vulkareth._clamp(color)
        if _NS_vulkareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vulkareth._clamp(color)
        if _NS_vulkareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        # Guard against invalid polygon (need 3+ points).
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_vulkareth._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_vulkareth._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_vulkareth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vulkareth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vulkareth._detect_moving(boss)
        _NS_vulkareth._update_vk_attack_anim(boss)
        attacking = (
            getattr(boss, "_vk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Detect Cataclysm form (R skill or cataclysm_form flag).
        is_cataclysm = (active_skill == "r"
                        or getattr(boss, "cataclysm_form", False))
        # Ambient behind.
        _NS_vulkareth._draw_lava_aura(surface, x, y, pulse, is_cataclysm)
        _NS_vulkareth._draw_ground_lava_ring(surface, x, y + 50, pulse, active_skill,
                               is_cataclysm)
        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_vulkareth._draw_volcano_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_vulkareth._draw_chaos_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vulkareth._draw_cataclysm_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if is_cataclysm:
            if attacking:
                _NS_vulkareth._draw_vk_cataclysm_attack(surface, boss, x, y)
            elif moving:
                _NS_vulkareth._draw_vk_cataclysm_float(surface, boss, x, y)
            else:
                _NS_vulkareth._draw_vk_cataclysm_idle(surface, boss, x, y)
        else:
            if attacking:
                _NS_vulkareth._draw_vk_attack(surface, boss, x, y)
            elif moving:
                _NS_vulkareth._draw_vk_float(surface, boss, x, y)
            else:
                _NS_vulkareth._draw_vk_idle(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_vulkareth._draw_chaos_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vulkareth._draw_volcano_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vulkareth._draw_cinder_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vulkareth._draw_cataclysm_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vk_previous_timer", 0))
        active = bool(getattr(boss, "_vk_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vk_attack_active = True
            boss._vk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vk_attack_frame = int(
                getattr(boss, "_vk_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._vk_attack_active = False
            boss._vk_attack_frame = 0
            active = False
        boss._vk_previous_timer = timer
        boss._vk_attack_progress = (
            min(1.0, getattr(boss, "_vk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_vk_last_x"):
            boss._vk_last_x = boss.x
            boss._vk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vk_last_x)
        dy = abs(boss.y - boss._vk_last_y)
        boss._vk_last_x = boss.x
        boss._vk_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # NORMAL FORM POSE ROUTERS
    # ============================================================
    def _draw_vk_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3) - 5
        _NS_vulkareth._draw_shadow(surface, x, y + 52)
        _NS_vulkareth._draw_lava_particles(surface, x, y + 44, boss.pulse)
        _NS_vulkareth._draw_vk_body(surface, x, y + bob,
                       boss.direction, boss.pulse, "idle")
    def _draw_vk_float(surface, boss, x, y):
        """Floating movement (demon levitates over lava)."""
        phase = boss.pulse * 1.6
        bob = int(math.sin(phase * 0.8) * 5) - 7
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_vulkareth._draw_shadow(surface, x + sway, y + 52, moving=True)
        _NS_vulkareth._draw_lava_particles(surface, x + sway, y + 44, phase,
                             moving=True, facing=boss.direction)
        _NS_vulkareth._draw_vk_body(surface, x + sway, y + bob,
                       boss.direction, phase, "float")
    def _draw_vk_attack(surface, boss, x, y):
        """Melee swing with lava sword."""
        progress = getattr(boss, "_vk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3) - 5
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * boss.direction
            lift = int(3 - t * 7) - 5
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4) - 5
        _NS_vulkareth._draw_shadow(surface, x + lunge, y + 52)
        _NS_vulkareth._draw_lava_particles(surface, x + lunge, y + 44, boss.pulse,
                             intense=True)
        _NS_vulkareth._draw_vk_body(surface, x + lunge, y + lift,
                       boss.direction, boss.pulse, "attack", progress)
        if 0.35 <= progress < 0.75:
            _NS_vulkareth._draw_fire_slash(surface, boss, x + lunge, y + lift,
                             progress)
    # ============================================================
    # CATACLYSM FORM POSE ROUTERS
    # ============================================================
    def _draw_vk_cataclysm_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4) - 7
        _NS_vulkareth._draw_shadow(surface, x, y + 54, cataclysm=True)
        _NS_vulkareth._draw_lava_particles(surface, x, y + 46, boss.pulse, intense=True)
        _NS_vulkareth._draw_vk_cataclysm_body(surface, x, y + bob,
                                boss.direction, boss.pulse, "idle")
    def _draw_vk_cataclysm_float(surface, boss, x, y):
        phase = boss.pulse * 1.6
        bob = int(math.sin(phase * 0.7) * 6) - 9
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_vulkareth._draw_shadow(surface, x + sway, y + 54, moving=True, cataclysm=True)
        _NS_vulkareth._draw_lava_particles(surface, x + sway, y + 46, phase,
                             intense=True, moving=True,
                             facing=boss.direction)
        _NS_vulkareth._draw_vk_cataclysm_body(surface, x + sway, y + bob,
                                boss.direction, phase, "float")
    def _draw_vk_cataclysm_attack(surface, boss, x, y):
        progress = getattr(boss, "_vk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 4) - 7
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(4 - t * 8) - 7
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4) - 7
        _NS_vulkareth._draw_shadow(surface, x + lunge, y + 54, cataclysm=True)
        _NS_vulkareth._draw_lava_particles(surface, x + lunge, y + 46, boss.pulse,
                             intense=True)
        _NS_vulkareth._draw_vk_cataclysm_body(surface, x + lunge, y + lift,
                                boss.direction, boss.pulse, "attack",
                                progress)
        if 0.35 <= progress < 0.75:
            _NS_vulkareth._draw_fire_slash(surface, boss, x + lunge, y + lift,
                             progress, big=True)
    # ============================================================
    # NORMAL BODY (Demon warrior)
    # ============================================================
    def _draw_vk_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Draw demon body."""
        # Tail (behind).
        _NS_vulkareth._draw_vk_tail(surface, cx, cy + 4, facing, phase)
        # Legs/lower.
        _NS_vulkareth._draw_vk_legs(surface, cx, cy + 20, facing, phase, action)
        # Back arm (holding blade or hanging).
        _NS_vulkareth._draw_back_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
        # Torso (armored obsidian).
        _NS_vulkareth._draw_vk_torso(surface, cx, cy, facing, phase, action)
        # Head with horns.
        _NS_vulkareth._draw_vk_head(surface, cx, cy - 22, facing, phase, action)
        # Front arm holding sword (foreground).
        _NS_vulkareth._draw_sword_arm(surface, cx, cy + 4, facing, phase, action,
                        attack_progress)
    def _draw_vk_tail(surface, cx, cy, facing, phase):
        """Demon tail with fire tip."""
        back_dir = -facing
        sway = math.sin(phase * 0.8) * 4
        base_x = cx + back_dir * 10
        base_y = cy + 8
        segments = 6
        prev = (base_x, base_y)
        for i in range(1, segments + 1):
            t = i / segments
            bx = base_x + int(back_dir * t * 16)
            by = base_y + int(t * 8) - int(math.sin(t * math.pi) * 6) + int(sway * t)
            thickness = max(2, 7 - i)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1),
                    (bx + 1, by + 1), thickness + 1)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                    prev, (bx, by), thickness)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                    prev, (bx, by), max(1, thickness - 1))
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_mid"],
                    (prev[0], prev[1] - 1), (bx, by - 1), max(1, thickness - 3))
            # Lava crack along tail.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_mid"],
                                 (bx, by, 1, 1))
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                                 (bx, by, 1, 1))
            prev = (bx, by)
        # Spade tail tip (fire).
        tip_x, tip_y = prev
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
            (tip_x + back_dir * 4 + 1, tip_y - 2 + 1),
            (tip_x + back_dir * 6 + 1, tip_y + 3 + 1),
            (tip_x + back_dir * 4 + 1, tip_y + 4 + 1),
            (tip_x + 1, tip_y + 1),
        ])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], [
            (tip_x + back_dir * 4, tip_y - 2),
            (tip_x + back_dir * 6, tip_y + 3),
            (tip_x + back_dir * 4, tip_y + 4),
            (tip_x, tip_y),
        ])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
            (tip_x + back_dir * 4, tip_y - 1),
            (tip_x + back_dir * 5, tip_y + 2),
            (tip_x + back_dir * 4, tip_y + 3),
            (tip_x + back_dir * 1, tip_y),
        ])
        # Fire glow on tip.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_dark"],
                  (tip_x + back_dir * 4, tip_y + 1), 3)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_mid"],
                  (tip_x + back_dir * 4, tip_y + 1), 2)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                         (tip_x + back_dir * 4, tip_y + 1, 1, 1))
    def _draw_vk_legs(surface, cx, cy, facing, phase, action):
        """Demon legs with armor."""
        for side_i, side in enumerate((-1, 1)):
            leg_x = cx + side * 6
            leg_top_y = cy - 6
            leg_bot_y = cy + 6
            # Thigh armor.
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                    (leg_x + 1, leg_top_y + 1),
                    (leg_x + 1, leg_bot_y + 1), 8)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                    (leg_x, leg_top_y), (leg_x, leg_bot_y), 7)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                    (leg_x, leg_top_y), (leg_x, leg_bot_y), 5)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_mid"],
                    (leg_x - 1, leg_top_y), (leg_x - 1, leg_bot_y), 2)
            # Lava crack down leg.
            for cy_off in range(-4, 6, 3):
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_mid"],
                                 (leg_x, leg_top_y + cy_off + 4, 1, 2))
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                                 (leg_x, leg_top_y + cy_off + 4, 1, 1))
            # Cloven hoof/foot.
            foot_x = leg_x
            foot_y = leg_bot_y
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
                (foot_x - 3, foot_y),
                (foot_x + 5 * facing, foot_y),
                (foot_x + 5 * facing, foot_y + 4),
                (foot_x - 3, foot_y + 4),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 5 * facing, foot_y - 1),
                (foot_x + 5 * facing, foot_y + 3),
                (foot_x - 3, foot_y + 3),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 4 * facing, foot_y - 1),
                (foot_x + 4 * facing, foot_y + 2),
                (foot_x - 2, foot_y + 2),
            ])
            # Hoof toes (2 claws).
            for c_off in (0, 3):
                claw_x = foot_x + c_off * facing
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_dark"],
                                 (claw_x, foot_y + 3, 1, 2))
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                                 (claw_x, foot_y + 4, 1, 1))
            # Ankle spike (small horn).
            spike_x = leg_x + side * 2
            spike_y = leg_bot_y - 2
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_darkest"], [
                (spike_x, spike_y),
                (spike_x + side * 4, spike_y - 3),
                (spike_x + side * 2, spike_y + 1),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_mid"], [
                (spike_x + side, spike_y),
                (spike_x + side * 3, spike_y - 2),
                (spike_x + side * 2, spike_y),
            ])
    def _draw_vk_torso(surface, cx, cy, facing, phase, action):
        """Muscular obsidian torso with lava cracks."""
        breath = math.sin(phase * 0.7) * 1
        # Torso outline (broad shoulders).
        torso_pts = [
            (cx - 14, cy - 12),
            (cx - 16, cy - 8),
            (cx - 14, cy - 2),
            (cx - 11, cy + 8),
            (cx - 5, cy + 14),
            (cx + 5, cy + 14),
            (cx + 11, cy + 8),
            (cx + 14, cy - 2),
            (cx + 16, cy - 8),
            (cx + 14, cy - 12),
            (cx + 8, cy - 15),
            (cx - 8, cy - 15),
        ]
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_pts])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], torso_pts)
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
            (cx - 13, cy - 11),
            (cx - 15, cy - 7),
            (cx - 13, cy - 2),
            (cx - 10, cy + 7),
            (cx - 4, cy + 13),
            (cx + 4, cy + 13),
            (cx + 10, cy + 7),
            (cx + 13, cy - 2),
            (cx + 15, cy - 7),
            (cx + 13, cy - 11),
            (cx + 7, cy - 14),
            (cx - 7, cy - 14),
        ])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_mid"], [
            (cx - 11, cy - 9),
            (cx - 13, cy - 5),
            (cx - 11, cy),
            (cx - 8, cy + 6),
            (cx + 8, cy + 6),
            (cx + 11, cy),
            (cx + 13, cy - 5),
            (cx + 11, cy - 9),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ])
        # Highlights.
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["obs_light"],
                         (cx - 8, cy - 10, 2, 2))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["obs_light"],
                         (cx + 6, cy - 10, 2, 2))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["obs_shine"],
                         (cx - 8, cy - 10, 1, 1))
        # LAVA CRACKS on chest (glowing).
        crack_pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vulkareth._alpha(240 * crack_pulse)
        # Vertical center crack.
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx, cy - 12), (cx, cy + 8), 2)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_mid"], crack_alpha),
                         (cx, cy - 11), (cx, cy + 7), 1)
        # Horizontal cracks.
        for y_off in (-8, -2, 4):
            pygame.draw.line(surface,
                             (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                             (cx - 6, cy + y_off), (cx + 6, cy + y_off), 1)
            # Bright hot spots along crack.
            for x_off in (-4, 0, 4):
                pygame.draw.rect(surface,
                                 (*_NS_vulkareth.PALETTE["crack_hot"], crack_alpha),
                                 (cx + x_off, cy + y_off, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_vulkareth.PALETTE["crack_shine"], crack_alpha),
                                 (cx + x_off, cy + y_off, 1, 1))
        # Diagonal cracks.
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx - 8, cy - 5), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx + 8, cy - 5), (cx + 3, cy + 3), 1)
        # Chest emblem (demon skull glowing).
        _NS_vulkareth._draw_chest_ember(surface, cx, cy - 4, phase)
        # Pauldrons (spike shoulders).
        for side in (-1, 1):
            sh_x = cx + side * 14
            sh_y = cy - 12
            # Base pauldron.
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
                (sh_x - 4, sh_y),
                (sh_x + 5 * side, sh_y - 4),
                (sh_x + 6 * side, sh_y + 3),
                (sh_x - 3, sh_y + 4),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], [
                (sh_x - 4, sh_y),
                (sh_x + 5 * side, sh_y - 4),
                (sh_x + 5 * side, sh_y + 3),
                (sh_x - 3, sh_y + 3),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
                (sh_x - 3, sh_y),
                (sh_x + 4 * side, sh_y - 3),
                (sh_x + 4 * side, sh_y + 2),
                (sh_x - 2, sh_y + 2),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_mid"], [
                (sh_x - 2, sh_y),
                (sh_x + 3 * side, sh_y - 2),
                (sh_x + 3 * side, sh_y + 1),
                (sh_x - 1, sh_y + 1),
            ])
            # 2 horn spikes on pauldron.
            for spike_i, (sp_off_x, sp_len) in enumerate([(2, 6), (5, 4)]):
                spike_base_x = sh_x + sp_off_x * side
                spike_base_y = sh_y - 2
                spike_tip_x = spike_base_x + int(sp_off_x * 0.2 * side)
                spike_tip_y = spike_base_y - sp_len
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
                    (spike_tip_x + 1, spike_tip_y + 1),
                    (spike_base_x - 1, spike_base_y),
                    (spike_base_x + 1, spike_base_y),
                ])
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_darkest"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x - 1, spike_base_y),
                    (spike_base_x + 1, spike_base_y),
                ])
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_dark"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x, spike_base_y - 1),
                    (spike_base_x + 1, spike_base_y),
                ])
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_mid"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x, spike_base_y),
                    (int((spike_tip_x + spike_base_x) / 2),
                     spike_base_y - 2),
                ])
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                                 (spike_tip_x, spike_tip_y, 1, 1))
                # Lava glow at horn base.
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                                 (spike_base_x, spike_base_y, 1, 1))
    def _draw_chest_ember(surface, cx, cy, phase):
        """Glowing ember/skull symbol in chest center."""
        pulse = math.sin(phase * 2.5) * 0.4 + 0.6
        # Deep glow.
        for r in range(6, 0, -1):
            alpha = _NS_vulkareth._alpha(180 * (6 - r) / 6 * pulse)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["crack_dark"], alpha),
                      (cx, cy), r)
        # Core ember.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_dark"], (cx, cy), 3)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_mid"], (cx, cy), 2)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_light"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_hot"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_shine"], (cx, cy, 1, 1))
    def _draw_vk_head(surface, cx, cy, facing, phase, action):
        """Demon head with big horns."""
        # Head shape (angular).
        head_pts = [
            (cx - 7, cy),
            (cx - 8, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 8, cy - 4),
            (cx + 7, cy),
            (cx + 5, cy + 5),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
            (cx - 5, cy + 5),
        ]
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"],
              [(px + 1, py + 2) for px, py in head_pts])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], head_pts)
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
            (cx - 6, cy),
            (cx - 7, cy - 4),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 7, cy - 4),
            (cx + 6, cy),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_mid"], [
            (cx - 5, cy - 1),
            (cx - 6, cy - 4),
            (cx - 3, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy - 4),
            (cx + 5, cy - 1),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["obs_light"],
                         (cx + facing * 3, cy - 3, 1, 2))
        # LAVA CRACKS on face.
        crack_pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vulkareth._alpha(230 * crack_pulse)
        # Vertical cheek crack.
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx - 3, cy - 6), (cx - 2, cy + 3), 1)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx + 3, cy - 6), (cx + 2, cy + 3), 1)
        # Bright hot spot.
        pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["crack_mid"], crack_alpha),
                         (cx - 3, cy - 2, 1, 1))
        pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["crack_hot"], crack_alpha),
                         (cx + 3, cy - 2, 1, 1))
        # EYES (glowing red-orange).
        for eye_side in (-1, 1):
            eye_x = cx + eye_side * 3
            eye_y = cy - 3
            for r in range(4, 0, -1):
                alpha = _NS_vulkareth._alpha(180 * (4 - r) / 4)
                _NS_vulkareth._aacircle(surface,
                          (*_NS_vulkareth.PALETTE["eye_glow"], alpha),
                          (eye_x, eye_y), r)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                             (eye_x - 1, eye_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["eye_glow"],
                             (eye_x, eye_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["eye_hot"],
                             (eye_x, eye_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["eye_white"],
                             (eye_x, eye_y - 1, 1, 1))
        # Snarl mouth with fangs.
        pygame.draw.line(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                         (cx - 3, cy + 4), (cx + 3, cy + 4), 2)
        pygame.draw.line(surface, _NS_vulkareth.PALETTE["crack_dark"],
                         (cx - 3, cy + 4), (cx + 3, cy + 4), 1)
        # Fangs.
        for fang_off in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                             (cx + fang_off, cy + 5, 1, 2))
        # BIG CURVED HORNS.
        _NS_vulkareth._draw_demon_horns(surface, cx, cy - 6, facing, phase)
    def _draw_demon_horns(surface, cx, cy, facing, phase):
        """Large curved demon horns."""
        # Two horns curving back and up.
        for side in (-1, 1):
            base_x = cx + side * 4
            base_y = cy
            # Horn curves outward and back.
            mid_x = base_x + side * 5
            mid_y = base_y - 6
            tip_x = base_x + side * 4
            tip_y = base_y - 12
            # Draw as bezier segments.
            segments = 6
            prev = (base_x, base_y)
            for i in range(1, segments + 1):
                t = i / segments
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * tip_y)
                thickness = max(1, 5 - int(t * 3))
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1),
                        (bx + 1, by + 1), thickness + 1)
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["horn_darkest"],
                        prev, (bx, by), thickness)
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["horn_dark"],
                        prev, (bx, by), max(1, thickness - 1))
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["horn_mid"],
                        (prev[0], prev[1] - 1), (bx, by - 1),
                        max(1, thickness - 2))
                # Horn ridge highlight.
                if i % 2 == 0:
                    pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                                     (bx, by - 1, 1, 1))
                prev = (bx, by)
            # Sharp tip.
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["horn_darkest"],
                      (tip_x, tip_y), 2)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["horn_mid"],
                      (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                             (tip_x, tip_y, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm hangs at side."""
        back_dir = -facing
        b_shoulder_x = cx + back_dir * 12
        b_shoulder_y = cy - 6
        sway = math.sin(phase * 0.6) * 1
        b_elbow_x = b_shoulder_x + back_dir * 3 + int(sway)
        b_elbow_y = b_shoulder_y + 8
        b_hand_x = b_elbow_x + back_dir * 1 + int(sway)
        b_hand_y = b_elbow_y + 8
        # Upper arm.
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                (b_shoulder_x + 1, b_shoulder_y + 1),
                (b_elbow_x + 1, b_elbow_y + 1), 6)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                (b_shoulder_x, b_shoulder_y), (b_elbow_x, b_elbow_y), 5)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                (b_shoulder_x, b_shoulder_y), (b_elbow_x, b_elbow_y), 4)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_mid"],
                (b_shoulder_x + back_dir, b_shoulder_y),
                (b_elbow_x + back_dir, b_elbow_y), 2)
        # Lava crack.
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_mid"],
                         (int((b_shoulder_x + b_elbow_x) / 2),
                          int((b_shoulder_y + b_elbow_y) / 2), 1, 1))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                         (int((b_shoulder_x + b_elbow_x) / 2),
                          int((b_shoulder_y + b_elbow_y) / 2), 1, 1))
        # Forearm.
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                (b_elbow_x + 1, b_elbow_y + 1),
                (b_hand_x + 1, b_hand_y + 1), 5)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 4)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 3)
        # Clawed hand.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                  (b_hand_x + 1, b_hand_y + 1), 4)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                  (b_hand_x, b_hand_y), 4)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_dark"],
                  (b_hand_x, b_hand_y), 3)
        # Claws.
        for c_i, c_off in enumerate((-3, -1, 2)):
            claw_x = b_hand_x + c_off + int(back_dir * 2)
            claw_y = b_hand_y + 3
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_dark"],
                             (claw_x, claw_y, 1, 2))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                             (claw_x, claw_y + 1, 1, 1))
    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding lava sword."""
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 6
        # Angle convention: 0 = forward, pi/2 = UP.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise sword up-back.
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.55 + t * 0.35)
                sword_extra = math.pi * 0.3
            elif attack_progress < 0.6:
                # Swing down.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (0.9 - t * 1.1)
                sword_extra = math.pi * (0.3 - t * 0.6)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.2 + t * 0.35)
                sword_extra = math.pi * (-0.3 + t * 0.4)
        elif action == "float":
            arm_angle = math.pi * 0.15 + math.sin(phase) * 0.05
            sword_extra = math.pi * 0.1
        else:
            arm_angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.03
            sword_extra = math.pi * 0.05
        upper_len = 11
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)
        forearm_len = 11
        hand_angle = arm_angle - math.pi * 0.15
        hand_x = elbow_x + int(math.cos(hand_angle) * forearm_len) * facing
        hand_y = elbow_y - int(math.sin(hand_angle) * forearm_len)
        # Upper arm.
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 7)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        # Lava crack on arm.
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_mid"],
                         (int((shoulder_x + elbow_x) / 2),
                          int((shoulder_y + elbow_y) / 2), 1, 1))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                         (int((shoulder_x + elbow_x) / 2),
                          int((shoulder_y + elbow_y) / 2), 1, 1))
        # Forearm.
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1),
                (hand_x + 1, hand_y + 1), 6)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Elbow spike.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_darkest"], (elbow_x, elbow_y), 4)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_dark"], (elbow_x, elbow_y), 3)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_mid"], (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # Clawed hand.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                  (hand_x + 1, hand_y + 1), 5)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                  (hand_x, hand_y), 5)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_dark"],
                  (hand_x, hand_y), 4)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_mid"],
                  (hand_x, hand_y), 3)
        # LAVA SWORD.
        sword_angle = hand_angle + sword_extra
        _NS_vulkareth._draw_lava_sword(surface, hand_x, hand_y, sword_angle,
                         facing, phase)
    def _draw_lava_sword(surface, hx, hy, angle, facing, phase):
        """Curved lava blade with fire glow."""
        # Handle (opposite direction).
        handle_len = 8
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy + int(math.sin(angle) * handle_len)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                (hx, hy), (handle_end_x, handle_end_y), 3)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                (hx, hy), (handle_end_x, handle_end_y), 2)
        # Pommel (glowing ember).
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                  (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                  (handle_end_x, handle_end_y), 3)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_dark"],
                  (handle_end_x, handle_end_y), 2)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_mid"],
                  (handle_end_x, handle_end_y), 1)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                         (handle_end_x, handle_end_y, 1, 1))
        # Crossguard (spiky iron).
        perp = angle + math.pi / 2
        cg_a_x = hx + int(math.cos(perp) * 5) * facing
        cg_a_y = hy - int(math.sin(perp) * 5)
        cg_b_x = hx - int(math.cos(perp) * 5) * facing
        cg_b_y = hy + int(math.sin(perp) * 5)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                (cg_a_x + 1, cg_a_y + 1), (cg_b_x + 1, cg_b_y + 1), 4)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_darkest"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 3)
        _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["obs_dark"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 2)
        # Small horns on crossguard.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["horn_dark"], (cg_a_x, cg_a_y), 2)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["horn_dark"], (cg_b_x, cg_b_y), 2)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                         (cg_a_x, cg_a_y - 1, 1, 1))
        # CURVED BLADE with lava glow.
        blade_start_x = hx
        blade_start_y = hy
        blade_len = 32
        # Slight curve.
        curve_angle_1 = angle + math.pi * 0.03
        curve_angle_2 = angle + math.pi * 0.1
        mid_x = blade_start_x + int(math.cos(curve_angle_1)
                                     * blade_len * 0.5) * facing
        mid_y = blade_start_y - int(math.sin(curve_angle_1) * blade_len * 0.5)
        tip_x = mid_x + int(math.cos(curve_angle_2)
                             * blade_len * 0.55) * facing
        tip_y = mid_y - int(math.sin(curve_angle_2) * blade_len * 0.55)
        # Blade segments.
        segments = 10
        prev = (blade_start_x, blade_start_y)
        for i in range(1, segments + 1):
            t = i / segments
            bx = int((1 - t) ** 2 * blade_start_x + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * blade_start_y + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            thickness = max(1, 5 - int(t * 3))
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1),
                    thickness + 1)
            # Dark blade edge.
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["blade_dark"],
                    prev, (bx, by), thickness)
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["blade_mid"],
                    prev, (bx, by), max(1, thickness - 1))
            # LAVA FIRE along blade center (glowing).
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["crack_dark"],
                    prev, (bx, by), max(1, thickness - 2))
            _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["crack_mid"],
                    prev, (bx, by), max(1, thickness - 3))
            # Bright spots.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                                 (bx, by, 1, 1))
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_shine"],
                                 (bx, by, 1, 1))
            prev = (bx, by)
        # Tip.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["blade_dark"], (tip_x, tip_y), 2)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_mid"], (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_shine"], (tip_x, tip_y, 1, 1))
        # Fire glow along blade.
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 1, -1):
            alpha = _NS_vulkareth._alpha(80 * (6 - r) / 6 * glow_pulse)
            glow_mid_x = int(hx + (tip_x - hx) * 0.5)
            glow_mid_y = int(hy + (tip_y - hy) * 0.5)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_light"], alpha),
                      (glow_mid_x, glow_mid_y), r)
    def _draw_fire_slash(surface, boss, cx, cy, progress, big=False):
        """Fire slash arc during sword swing."""
        facing = boss.direction
        swing_t = max(0.0, min(1.0, (progress - 0.35) / 0.4))
        arc_center_x = cx + facing * 6
        arc_center_y = cy - 4
        radius = 34 if big else 28
        num_slices = 12 if big else 10
        for slice_i in range(num_slices):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.75
            sweep_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.12)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            fade = 1 - slice_t * 0.75
            alpha = _NS_vulkareth._alpha(240 * fade
                            * (1 - abs(swing_t - 0.5) * 1.4))
            if alpha <= 0:
                continue
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            size = max(2, int((8 if big else 6) * fade))
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_darkest"], alpha),
                      (arc_x, arc_y), size + 1)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                      (arc_x, arc_y), size)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                      (arc_x, arc_y), max(1, size - 1))
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_light"], alpha),
                      (arc_x, arc_y), max(1, size - 2))
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                      (arc_x, arc_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                             (arc_x, arc_y, 1, 1))
        # Bright crescent arc line.
        crescent_pts = []
        for slice_i in range(num_slices + 1):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.75
            sweep_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.08)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            crescent_pts.append((arc_x, arc_y))
        if len(crescent_pts) > 1:
            for i in range(len(crescent_pts) - 1):
                alpha = _NS_vulkareth._alpha(230 * (1 - abs(swing_t - 0.5) * 1.4))
                _NS_vulkareth._aaline(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 2)
                _NS_vulkareth._aaline(surface, (*_NS_vulkareth.PALETTE["fire_white"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 1)
    # ============================================================
    # CATACLYSM FORM BODY (Winged demon, bigger)
    # ============================================================
    def _draw_vk_cataclysm_body(surface, cx, cy, facing, phase, action,
                                  attack_progress=0):
        """Draw winged Cataclysm form."""
        # Wings FIRST (behind).
        _NS_vulkareth._draw_demon_wings(surface, cx, cy - 4, facing, phase, action,
                          attack_progress)
        # Tail (behind).
        _NS_vulkareth._draw_vk_tail(surface, cx, cy + 6, facing, phase)
        # Legs.
        _NS_vulkareth._draw_vk_legs(surface, cx, cy + 22, facing, phase, action)
        # Back arm.
        _NS_vulkareth._draw_back_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
        # Torso (larger).
        _NS_vulkareth._draw_cataclysm_torso(surface, cx, cy, facing, phase, action)
        # Head with bigger horns.
        _NS_vulkareth._draw_cataclysm_head(surface, cx, cy - 24, facing, phase, action)
        # Sword arm.
        _NS_vulkareth._draw_sword_arm(surface, cx, cy + 4, facing, phase, action,
                        attack_progress)
    def _draw_demon_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Bat-like demon wings."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 4
        else:
            beat = math.sin(phase * 1.0) * 3
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing
            (1, 0.7, 0.75),   # near wing
        ]):
            base_x = cx - facing * 6
            base_y = cy - 2
            spar1_len = int(30 * size_mult)
            spar1_angle = math.pi * 0.65 * side_mult - math.radians(beat)
            spar2_len = int(35 * size_mult)
            spar2_angle = math.pi * 0.85 * side_mult - math.radians(beat * 0.8)
            spar3_len = int(28 * size_mult)
            spar3_angle = math.pi * 1.05 * side_mult - math.radians(beat * 0.5)
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
            wing_surf = pygame.Surface((180, 120), pygame.SRCALPHA)
            offset_x = base_x - 90
            offset_y = base_y - 60
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]
            _NS_vulkareth._poly(wing_surf, (*_NS_vulkareth.PALETTE["obs_darkest"], int(220 * alpha_mult)),
                  local_points)
            # Inner darker fill.
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.8 + cx_local * 0.2),
                     int(p[1] * 0.8 + cy_local * 0.2))
                )
            _NS_vulkareth._poly(wing_surf, (*_NS_vulkareth.PALETTE["obs_dark"], int(200 * alpha_mult)),
                  inner_pts)
            # Fire membrane (glowing).
            _NS_vulkareth._poly(wing_surf, (*_NS_vulkareth.PALETTE["crack_dark"], int(140 * alpha_mult)),
                  inner_pts)
            # Wing bones/fingers (spar lines) - dark obsidian.
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                pygame.draw.line(wing_surf,
                                 (*_NS_vulkareth.PALETTE["obs_darkest"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_vulkareth.PALETTE["obs_dark"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_vulkareth.PALETTE["obs_mid"],
                                  int(180 * alpha_mult)),
                                 bone_base, tip, 1)
                # Claw at end of each finger.
                _NS_vulkareth._aacircle(wing_surf,
                          (*_NS_vulkareth.PALETTE["horn_darkest"], int(240 * alpha_mult)),
                          tip, 2)
                _NS_vulkareth._aacircle(wing_surf,
                          (*_NS_vulkareth.PALETTE["horn_light"], int(240 * alpha_mult)),
                          tip, 1)
            # Fire glow along top edge.
            pygame.draw.line(wing_surf,
                             (*_NS_vulkareth.PALETTE["crack_hot"],
                              int(220 * alpha_mult)),
                             bone_base,
                             (tip1_x - offset_x, tip1_y - offset_y), 1)
            # Ember sparkle at wing tip.
            pygame.draw.rect(wing_surf,
                             (*_NS_vulkareth.PALETTE["fire_hot"], int(240 * alpha_mult)),
                             (tip1_x - offset_x, tip1_y - offset_y, 2, 2))
            pygame.draw.rect(wing_surf,
                             (*_NS_vulkareth.PALETTE["fire_shine"], int(240 * alpha_mult)),
                             (tip1_x - offset_x, tip1_y - offset_y, 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_cataclysm_torso(surface, cx, cy, facing, phase, action):
        """Bigger torso with more lava cracks."""
        breath = math.sin(phase * 0.7) * 1
        # Torso outline (broader).
        torso_pts = [
            (cx - 16, cy - 14),
            (cx - 18, cy - 10),
            (cx - 16, cy - 2),
            (cx - 12, cy + 9),
            (cx - 6, cy + 15),
            (cx + 6, cy + 15),
            (cx + 12, cy + 9),
            (cx + 16, cy - 2),
            (cx + 18, cy - 10),
            (cx + 16, cy - 14),
            (cx + 9, cy - 17),
            (cx - 9, cy - 17),
        ]
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_pts])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], torso_pts)
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
            (cx - 15, cy - 13),
            (cx - 17, cy - 9),
            (cx - 15, cy - 2),
            (cx - 11, cy + 8),
            (cx - 5, cy + 14),
            (cx + 5, cy + 14),
            (cx + 11, cy + 8),
            (cx + 15, cy - 2),
            (cx + 17, cy - 9),
            (cx + 15, cy - 13),
            (cx + 8, cy - 16),
            (cx - 8, cy - 16),
        ])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_mid"], [
            (cx - 13, cy - 11),
            (cx - 15, cy - 7),
            (cx - 12, cy + 2),
            (cx - 9, cy + 7),
            (cx + 9, cy + 7),
            (cx + 12, cy + 2),
            (cx + 15, cy - 7),
            (cx + 13, cy - 11),
            (cx + 7, cy - 14),
            (cx - 7, cy - 14),
        ])
        # LOTS of lava cracks (Cataclysm form more intense).
        crack_pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        crack_alpha = _NS_vulkareth._alpha(255 * crack_pulse)
        # Big vertical center crack.
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx, cy - 14), (cx, cy + 10), 3)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_mid"], crack_alpha),
                         (cx, cy - 13), (cx, cy + 9), 2)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_hot"], crack_alpha),
                         (cx, cy - 12), (cx, cy + 8), 1)
        # Horizontal.
        for y_off in (-10, -4, 2, 8):
            pygame.draw.line(surface,
                             (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                             (cx - 8, cy + y_off), (cx + 8, cy + y_off), 2)
            pygame.draw.line(surface,
                             (*_NS_vulkareth.PALETTE["crack_mid"], crack_alpha),
                             (cx - 6, cy + y_off), (cx + 6, cy + y_off), 1)
            for x_off in (-6, -3, 0, 3, 6):
                pygame.draw.rect(surface,
                                 (*_NS_vulkareth.PALETTE["crack_hot"], crack_alpha),
                                 (cx + x_off, cy + y_off, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_vulkareth.PALETTE["crack_shine"], crack_alpha),
                                 (cx + x_off, cy + y_off, 1, 1))
        # Big glowing chest ember (BIGGER in Cataclysm).
        _NS_vulkareth._draw_chest_ember_big(surface, cx, cy - 4, phase)
        # Larger pauldrons with more spikes.
        for side in (-1, 1):
            sh_x = cx + side * 16
            sh_y = cy - 12
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
                (sh_x - 5, sh_y),
                (sh_x + 6 * side, sh_y - 5),
                (sh_x + 7 * side, sh_y + 4),
                (sh_x - 4, sh_y + 5),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], [
                (sh_x - 5, sh_y),
                (sh_x + 6 * side, sh_y - 5),
                (sh_x + 6 * side, sh_y + 4),
                (sh_x - 4, sh_y + 4),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
                (sh_x - 4, sh_y),
                (sh_x + 5 * side, sh_y - 4),
                (sh_x + 5 * side, sh_y + 3),
                (sh_x - 3, sh_y + 3),
            ])
            _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_mid"], [
                (sh_x - 3, sh_y),
                (sh_x + 4 * side, sh_y - 3),
                (sh_x + 4 * side, sh_y + 2),
                (sh_x - 2, sh_y + 2),
            ])
            # 3 big horn spikes.
            for spike_i, (sp_off_x, sp_len) in enumerate([(1, 5), (4, 7), (6, 5)]):
                spike_base_x = sh_x + sp_off_x * side
                spike_base_y = sh_y - 3
                spike_tip_x = spike_base_x + int(sp_off_x * 0.2 * side)
                spike_tip_y = spike_base_y - sp_len
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
                    (spike_tip_x + 1, spike_tip_y + 1),
                    (spike_base_x - 1, spike_base_y),
                    (spike_base_x + 1, spike_base_y),
                ])
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_darkest"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x - 1, spike_base_y),
                    (spike_base_x + 1, spike_base_y),
                ])
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_dark"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x, spike_base_y - 1),
                    (spike_base_x + 1, spike_base_y),
                ])
                _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["horn_mid"], [
                    (spike_tip_x, spike_tip_y),
                    (spike_base_x, spike_base_y),
                    (int((spike_tip_x + spike_base_x) / 2),
                     spike_base_y - 2),
                ])
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                                 (spike_tip_x, spike_tip_y, 1, 1))
                # Fire at base.
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                                 (spike_base_x, spike_base_y, 1, 1))
    def _draw_chest_ember_big(surface, cx, cy, phase):
        """Big glowing chest core in Cataclysm form."""
        pulse = math.sin(phase * 2.5) * 0.4 + 0.6
        # Big glow.
        for r in range(10, 0, -1):
            alpha = _NS_vulkareth._alpha(180 * (10 - r) / 10 * pulse)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["crack_dark"], alpha),
                      (cx, cy), r)
        # Core.
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_darkest"], (cx, cy), 5)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_dark"], (cx, cy), 4)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_mid"], (cx, cy), 3)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_light"], (cx, cy), 2)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_hot"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_shine"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["white"], (cx, cy, 1, 1))
    def _draw_cataclysm_head(surface, cx, cy, facing, phase, action):
        """Bigger head with larger horns in Cataclysm form."""
        # Head (slightly larger).
        head_pts = [
            (cx - 8, cy),
            (cx - 9, cy - 4),
            (cx - 7, cy - 9),
            (cx - 3, cy - 11),
            (cx + 3, cy - 11),
            (cx + 7, cy - 9),
            (cx + 9, cy - 4),
            (cx + 8, cy),
            (cx + 6, cy + 6),
            (cx + 2, cy + 9),
            (cx - 2, cy + 9),
            (cx - 6, cy + 6),
        ]
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"],
              [(px + 1, py + 2) for px, py in head_pts])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_darkest"], head_pts)
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_dark"], [
            (cx - 7, cy),
            (cx - 8, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 8, cy - 4),
            (cx + 7, cy),
            (cx + 5, cy + 5),
            (cx - 5, cy + 5),
        ])
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["obs_mid"], [
            (cx - 6, cy - 1),
            (cx - 7, cy - 4),
            (cx - 4, cy - 7),
            (cx + 3, cy - 7),
            (cx + 6, cy - 4),
            (cx + 6, cy - 1),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])
        # Bigger lava cracks on face.
        crack_pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vulkareth._alpha(255 * crack_pulse)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx - 4, cy - 7), (cx - 3, cy + 4), 2)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_dark"], crack_alpha),
                         (cx + 4, cy - 7), (cx + 3, cy + 4), 2)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_mid"], crack_alpha),
                         (cx - 4, cy - 6), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface,
                         (*_NS_vulkareth.PALETTE["crack_mid"], crack_alpha),
                         (cx + 4, cy - 6), (cx + 3, cy + 3), 1)
        pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["crack_hot"], crack_alpha),
                         (cx - 3, cy - 2, 1, 1))
        pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["crack_hot"], crack_alpha),
                         (cx + 3, cy - 2, 1, 1))
        # EYES (intense glow, bigger).
        for eye_side in (-1, 1):
            eye_x = cx + eye_side * 3
            eye_y = cy - 3
            for r in range(5, 0, -1):
                alpha = _NS_vulkareth._alpha(220 * (5 - r) / 5)
                _NS_vulkareth._aacircle(surface,
                          (*_NS_vulkareth.PALETTE["eye_glow"], alpha),
                          (eye_x, eye_y), r)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                             (eye_x - 1, eye_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["eye_glow"],
                             (eye_x, eye_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["eye_hot"],
                             (eye_x, eye_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["white"],
                             (eye_x, eye_y - 1, 1, 1))
        # Roaring mouth (open) with fangs.
        mouth_open = 4 if action == "attack" else 3
        _NS_vulkareth._poly(surface, _NS_vulkareth.PALETTE["shadow_deep"], [
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 3, cy + 4 + mouth_open),
            (cx - 3, cy + 4 + mouth_open),
        ])
        # Fire inside mouth (glowing).
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_mid"],
                  (cx, cy + 4 + mouth_open // 2), 2)
        _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_hot"],
                  (cx, cy + 4 + mouth_open // 2), 1)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_shine"],
                         (cx, cy + 4 + mouth_open // 2, 1, 1))
        # Upper fangs.
        for fang_off in (-3, -1, 1, 3):
            pygame.draw.line(surface, _NS_vulkareth.PALETTE["horn_dark"],
                             (cx + fang_off, cy + 4),
                             (cx + fang_off, cy + 6), 1)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                             (cx + fang_off, cy + 5, 1, 1))
        # Lower fangs.
        for fang_off in (-2, 2):
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                             (cx + fang_off, cy + 4 + mouth_open - 1, 1, 1))
        # LARGER HORNS.
        _NS_vulkareth._draw_bigger_horns(surface, cx, cy - 6, facing, phase)
    def _draw_bigger_horns(surface, cx, cy, facing, phase):
        """Massive curved horns for Cataclysm form."""
        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy
            mid_x = base_x + side * 7
            mid_y = base_y - 7
            tip_x = base_x + side * 5
            tip_y = base_y - 16
            segments = 8
            prev = (base_x, base_y)
            for i in range(1, segments + 1):
                t = i / segments
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * tip_y)
                thickness = max(1, 6 - int(t * 4))
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1),
                        (bx + 1, by + 1), thickness + 1)
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["horn_darkest"],
                        prev, (bx, by), thickness)
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["horn_dark"],
                        prev, (bx, by), max(1, thickness - 1))
                _NS_vulkareth._aaline(surface, _NS_vulkareth.PALETTE["horn_mid"],
                        (prev[0], prev[1] - 1), (bx, by - 1),
                        max(1, thickness - 2))
                if i % 2 == 0:
                    pygame.draw.rect(surface, _NS_vulkareth.PALETTE["horn_light"],
                                     (bx, by - 1, 1, 1))
                    # Fire ember at horn ridge.
                    pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                                     (bx, by - 1, 1, 1))
                prev = (bx, by)
            # Sharp glowing tip.
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["horn_darkest"],
                      (tip_x, tip_y), 2)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["crack_mid"],
                      (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["crack_hot"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_shine"],
                             (tip_x, tip_y, 1, 1))
    # ============================================================
    # LAVA PARTICLES / AMBIENT
    # ============================================================
    def _draw_lava_particles(surface, cx, cy, phase, intense=False,
                              moving=False, facing=1):
        """Lava embers rising below boss."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Fire mist cloud.
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.3) * 0.3 + 0.7
        for radius in range(32, 3, -2):
            alpha = _NS_vulkareth._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vulkareth.PALETTE["fire_darkest"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_vulkareth._alpha((20 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising fire embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_vulkareth._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                      (sx, sy), 3)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                      (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Bright sparkles.
        for i in range(12):
            spark_t = (phase * 0.7 + i * 0.09) % 1.0
            ex = cx - 28 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_vulkareth._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail.
        if moving:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vulkareth._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          (sx, sy), max(2, 7 - i))
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                          (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                 (sx, sy - 1, 1, 1))
    def _draw_shadow(surface, x, y, moving=False, cataclysm=False):
        size_w = 160 if cataclysm else 130
        size_h = 32 if cataclysm else 28
        shadow = pygame.Surface((size_w + 20, size_h + 6), pygame.SRCALPHA)
        for radius in range(size_h // 2, 0, -1):
            alpha = max(0, (size_h // 2 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, size_h // 2 + 2 - radius,
                 size_w + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 3, 2, 170),
                            (5, size_h // 2 - 4, size_w + 10, 12))
        pygame.draw.ellipse(shadow, (60, 20, 10, 100),
                            (12, size_h // 2 - 3, size_w - 4, 8))
        surface.blit(shadow, (x - size_w // 2 - 10, y - size_h // 2 - 3))
    def _draw_lava_aura(surface, x, y, phase, is_cataclysm):
        """Fire aura (larger for Cataclysm form)."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        base_r = 105 if is_cataclysm else 75
        aura = pygame.Surface((base_r * 2 + 20, base_r * 2 + 20), pygame.SRCALPHA)
        center = (base_r + 10, base_r + 10)
        for radius in range(base_r, 5, -4):
            alpha = _NS_vulkareth._alpha((base_r - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vulkareth._aacircle(aura, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          center, radius)
        for radius in range(base_r * 2 // 3, 5, -3):
            alpha = _NS_vulkareth._alpha((base_r * 2 // 3 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vulkareth._aacircle(aura, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                          center, radius)
        surface.blit(aura, (x - base_r - 10, y - base_r - 10))
        # Floating fire embers.
        num_embers = 16 if is_cataclysm else 10
        for i in range(num_embers):
            angle = phase * 0.3 + i * math.pi * 2 / num_embers
            ember_r = int(base_r * 0.5) + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * ember_r)
            sy = y - 5 + int(math.sin(angle) * ember_r * 0.5)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_lava_ring(surface, x, y, phase, skill, is_cataclysm):
        """Ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        size_w = 190 if is_cataclysm else 160
        size_h = 55 if is_cataclysm else 48
        ring = pygame.Surface((size_w, size_h), pygame.SRCALPHA)
        cx_r, cy_r = size_w // 2, size_h // 2
        pygame.draw.ellipse(ring, (*_NS_vulkareth.PALETTE["fire_dark"], 200),
                            (5, cy_r - 10, size_w - 10, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_vulkareth.PALETTE["fire_darkest"], 220),
                            (14, cy_r - 8, size_w - 28, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_vulkareth.PALETTE["fire_dark"], 200),
                            (25, cy_r - 6, size_w - 50, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_vulkareth.PALETTE["lava_mid"], 180),
                            (40, cy_r - 4, size_w - 80, 12), 1)
        # Runes.
        num_runes = 12 if is_cataclysm else 8
        for i in range(num_runes):
            angle = phase * 0.3 + i * math.pi * 2 / num_runes
            x1 = cx_r + int(math.cos(angle) * (size_w // 2 - 20))
            y1 = cy_r + int(math.sin(angle) * (size_h // 3 - 2))
            x2 = cx_r + int(math.cos(angle) * (size_w // 2 - 8))
            y2 = cy_r + int(math.sin(angle) * (size_h // 3 + 2))
            pygame.draw.line(ring, (*_NS_vulkareth.PALETTE["fire_hot"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, (*_NS_vulkareth.PALETTE["fire_shine"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vulkareth.PALETTE["fire_hot"],
                                        _NS_vulkareth._alpha(160 * pulse)),
                                (15, 8, size_w - 30, size_h - 16), 1)
        surface.blit(ring, (x - size_w // 2, y - size_h // 2))
    # ============================================================
    # SKILL Q: CHAOS ASSAULT (leap forward)
    # ============================================================
    def _draw_chaos_ground(surface, boss, x, y, timer, phase):
        """Ground crack at landing spot."""
        tx, ty = _NS_vulkareth._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            return
        t = (progress - 0.5) / 0.5
        r = int(35 * min(1.0, t * 2))
        if r > 3:
            # Cracked ground.
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_dark"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_mid"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_chaos_foreground(surface, boss, x, y, timer, phase):
        """Leap arc + landing impact."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vulkareth._target_position(boss, x, y)
        if progress < 0.5:
            # Leap arc (fire trail).
            t = progress / 0.5
            start_x = x
            start_y = y - 10
            # Arc trajectory (parabolic).
            arc_x = int(start_x + (tx - start_x) * t)
            peak_y = min(start_y, ty) - 60
            arc_y = int(start_y + (ty - start_y) * t - math.sin(t * math.pi) * 60)
            # Trail behind.
            for i in range(8):
                tt = max(0.0, t - i * 0.04)
                trail_x = int(start_x + (tx - start_x) * tt)
                trail_y = int(start_y + (ty - start_y) * tt
                              - math.sin(tt * math.pi) * 60)
                alpha = _NS_vulkareth._alpha(200 - i * 25)
                size = max(1, 6 - i)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_darkest"], alpha),
                          (trail_x, trail_y), size + 1)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          (trail_x, trail_y), size)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                          (trail_x, trail_y), max(1, size - 1))
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                          (trail_x, trail_y), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                                 (trail_x, trail_y, 1, 1))
        else:
            # Landing impact.
            t = (progress - 0.5) / 0.5
            impact_r = int(15 + t * 30)
            alpha = _NS_vulkareth._alpha(240 * (1 - t))
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_darkest"], alpha),
                      (tx, ty), impact_r + 3, 3)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                      (tx, ty), impact_r, 3)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                      (tx, ty), max(1, impact_r - 5), 2)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_light"], alpha),
                      (tx, ty), max(1, impact_r - 10), 1)
            # Radial burst.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SKILL W: VOLCANO ERUPTION (magma pillar at target)
    # ============================================================
    def _draw_volcano_ground(surface, boss, x, y, timer, phase):
        """Growing magma pool at target."""
        tx, ty = _NS_vulkareth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_dark"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_mid"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            pygame.draw.ellipse(surface, (*_NS_vulkareth.PALETTE["lava_light"], 200),
                                (tx - r + 14, ty - r // 3 + 6,
                                 r * 2 - 28, r * 2 // 3 - 12))
    def _draw_volcano_foreground(surface, boss, x, y, timer, phase):
        """Magma pillar erupting from ground."""
        tx, ty = _NS_vulkareth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_height = 75
        height = int(max_height * min(1.0, progress * 2.5))
        base_r = 22
        if height < 5:
            return
        # Vertical magma pillar (stacked ellipses).
        num_layers = 14
        for layer_i in range(num_layers):
            layer_t = layer_i / num_layers
            layer_y = ty - int(layer_t * height)
            layer_w = int(base_r * (1 - layer_t * 0.4))
            wobble = int(math.sin(phase * 3 + layer_i) * 2)
            alpha = _NS_vulkareth._alpha(230 - layer_i * 8)
            if alpha <= 0:
                continue
            # Dark base.
            pygame.draw.ellipse(surface,
                                (*_NS_vulkareth.PALETTE["fire_darkest"], alpha),
                                (tx - layer_w + wobble, layer_y - 4,
                                 layer_w * 2, 8))
            # Mid.
            pygame.draw.ellipse(surface,
                                (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                                (tx - layer_w + wobble + 2, layer_y - 3,
                                 layer_w * 2 - 4, 6))
            pygame.draw.ellipse(surface,
                                (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                                (tx - layer_w + wobble + 4, layer_y - 2,
                                 layer_w * 2 - 8, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_vulkareth.PALETTE["fire_light"], alpha),
                                (tx - layer_w + wobble + 6, layer_y - 1,
                                 layer_w * 2 - 12, 3))
            # Bright hot core.
            if layer_i % 2 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                 (tx + wobble, layer_y, 2, 1))
                pygame.draw.rect(surface,
                                 (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                                 (tx + wobble, layer_y, 1, 1))
        # Top of pillar (bursting flames).
        top_y = ty - height
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.5
            ember_x = tx + int(math.cos(angle) * 8)
            ember_y = top_y - int(math.sin(angle) * 8) - 4
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_dark"],
                      (ember_x, ember_y), 3)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_mid"],
                      (ember_x, ember_y), 2)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_hot"],
                      (ember_x, ember_y), 1)
            pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_shine"],
                             (ember_x, ember_y, 1, 1))
        # Bright core at top.
        for r in range(8, 0, -1):
            alpha = _NS_vulkareth._alpha(180 * (8 - r) / 8)
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                      (tx, top_y - 2), r)
        pygame.draw.rect(surface, _NS_vulkareth.PALETTE["white"], (tx, top_y - 2, 1, 1))
        # Falling magma droplets.
        for i in range(6):
            drop_t = (phase * 0.8 + i * 0.15) % 1.0
            drop_x = tx + int((i - 2.5) * 6) + int(math.sin(phase + i) * 3)
            drop_y = top_y - 8 + int(drop_t * 40)
            alpha = _NS_vulkareth._alpha(220 * (1 - drop_t))
            _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                      (drop_x, drop_y), 2)
            pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                             (drop_x, drop_y, 1, 1))
    # ============================================================
    # SKILL E: CINDER SWEEP (weapon swing with fire trail)
    # ============================================================
    def _draw_cinder_skill(surface, boss, x, y, timer, phase):
        """Enhanced cinder sweep - big fire crescent forward."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Wind-up.
            t = progress / 0.25
            charge_x = x + facing * 20
            charge_y = y - 15
            cr = int(6 + t * 12)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_vulkareth._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          (charge_x, charge_y), r)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_mid"],
                      (charge_x, charge_y), cr - 3)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_light"],
                      (charge_x, charge_y), max(1, cr - 6))
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_shine"],
                      (charge_x, charge_y), max(1, cr - 9))
        else:
            t = (progress - 0.25) / 0.75
            arc_center_x = x + facing * 10
            arc_center_y = y - 8
            radius = int(45 + t * 25)
            # Big sweeping arc.
            num_slices = 18
            for slice_i in range(num_slices):
                slice_t = slice_i / num_slices
                sweep_start = math.pi * 0.85
                sweep_end = -math.pi * 0.2
                local_t = max(0.0, min(1.0, t * 1.3 - slice_t * 0.15))
                angle = sweep_start + (sweep_end - sweep_start) * local_t
                fade = 1 - slice_t * 0.7
                alpha = _NS_vulkareth._alpha(230 * fade * (1 - t * 0.3))
                if alpha <= 0:
                    continue
                arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
                arc_y = arc_center_y - int(math.sin(angle) * radius)
                size = max(2, int(9 * fade))
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_darkest"], alpha),
                          (arc_x, arc_y), size + 2)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          (arc_x, arc_y), size + 1)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                          (arc_x, arc_y), size)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_light"], alpha),
                          (arc_x, arc_y), max(1, size - 1))
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                          (arc_x, arc_y), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                                 (arc_x, arc_y, 1, 1))
            # Bright leading edge.
            crescent_pts = []
            for slice_i in range(num_slices + 1):
                slice_t = slice_i / num_slices
                sweep_start = math.pi * 0.85
                sweep_end = -math.pi * 0.2
                local_t = max(0.0, min(1.0, t * 1.3 - slice_t * 0.08))
                angle = sweep_start + (sweep_end - sweep_start) * local_t
                arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
                arc_y = arc_center_y - int(math.sin(angle) * radius)
                crescent_pts.append((arc_x, arc_y))
            if len(crescent_pts) > 1:
                for i in range(len(crescent_pts) - 1):
                    alpha = _NS_vulkareth._alpha(240 * (1 - t * 0.3))
                    _NS_vulkareth._aaline(surface, (*_NS_vulkareth.PALETTE["fire_white"], alpha),
                            crescent_pts[i], crescent_pts[i + 1], 2)
    # ============================================================
    # SKILL R: CATACLYSM (transformation + AoE burn)
    # ============================================================
    def _draw_cataclysm_ground(surface, boss, x, y, timer, phase):
        """Growing lava ring under boss."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 1.5))
        if r > 5:
            for i in range(4):
                thickness = 4 - i
                pygame.draw.ellipse(surface,
                                    (*_NS_vulkareth.PALETTE["lava_darkest"], 220 - i * 40),
                                    (x - r, y + 44 - r // 3,
                                     r * 2, r * 2 // 3), thickness)
                pygame.draw.ellipse(surface,
                                    (*_NS_vulkareth.PALETTE["lava_dark"], 220 - i * 40),
                                    (x - r + 3, y + 44 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), max(1, thickness - 1))
                pygame.draw.ellipse(surface,
                                    (*_NS_vulkareth.PALETTE["lava_mid"], 200 - i * 40),
                                    (x - r + 8, y + 44 - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8), max(1, thickness - 2))
    def _draw_cataclysm_foreground(surface, boss, x, y, timer, phase):
        """Transformation burst + burning aura."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Transformation burst.
            t = progress / 0.3
            burst_r = int(15 + t * 40)
            for r in range(burst_r + 5, 0, -2):
                alpha = _NS_vulkareth._alpha(220 * (burst_r + 5 - r) / (burst_r + 5))
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          (x, y - 5), r)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_mid"], (x, y - 5), burst_r - 5)
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_light"], (x, y - 5),
                      max(1, burst_r - 10))
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_hot"], (x, y - 5),
                      max(1, burst_r - 15))
            _NS_vulkareth._aacircle(surface, _NS_vulkareth.PALETTE["fire_shine"], (x, y - 5),
                      max(1, burst_r - 20))
            # Spiral energy.
            for i in range(16):
                angle = phase * 5 + i * math.pi / 8
                spiral_r = int(60 - t * 40)
                sx = x + int(math.cos(angle) * spiral_r)
                sy = y - 5 + int(math.sin(angle) * spiral_r * 0.6)
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_vulkareth.PALETTE["fire_shine"], (sx, sy, 1, 1))
        elif progress < 0.75:
            # Burning aura around Cataclysm form.
            for i in range(24):
                angle = phase * 2 + i * math.pi / 12
                r = 55 + int(math.sin(phase + i) * 12)
                sx = x + int(math.cos(angle) * r)
                sy = y - 5 + int(math.sin(angle) * r * 0.55)
                alpha = _NS_vulkareth._alpha(220)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                          (sx, sy), 3)
                _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                          (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Rising flame pillars around.
            for i in range(8):
                pillar_angle = i * math.pi / 4 + phase * 0.3
                pillar_r = 60
                px = x + int(math.cos(pillar_angle) * pillar_r)
                py_base = y + 20 + int(math.sin(pillar_angle) * pillar_r * 0.4)
                for h in range(5):
                    py = py_base - h * 4
                    alpha = _NS_vulkareth._alpha(200 - h * 30)
                    _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                              (px, py), max(1, 4 - h))
                    _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                              (px, py), max(1, 3 - h))
                    pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                     (px, py, 1, 1))
        else:
            # Aftermath: lingering flames rising.
            t = (progress - 0.75) / 0.25
            for i in range(14):
                rise_t = (phase * 0.8 + i * 0.08) % 1.0
                rx = x + int(math.sin(phase + i) * 40)
                ry = y - int(rise_t * 50)
                alpha = _NS_vulkareth._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_dark"], alpha),
                              (rx, ry), 3)
                    _NS_vulkareth._aacircle(surface, (*_NS_vulkareth.PALETTE["fire_mid"], alpha),
                              (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_hot"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface, (*_NS_vulkareth.PALETTE["fire_shine"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# OKEANORA (DEEPBORN ORACLE) - TRUE BOSS
# ====================================================================

class _NS_okeanora:
    """Namespace okeanora - Kraken Priestess TRUE BOSS."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tan warrior)
        "skin_darkest": (55, 30, 20),
        "skin_dark": (110, 70, 45),
        "skin_mid": (170, 115, 75),
        "skin_light": (215, 165, 115),
        "skin_shine": (245, 210, 165),
        # Hair (dark brown/black flowing)
        "hair_darkest": (15, 10, 8),
        "hair_dark": (40, 28, 22),
        "hair_mid": (75, 55, 45),
        "hair_light": (120, 90, 75),
        # Dark ocean cloth (green top)
        "cloth_darkest": (5, 25, 25),
        "cloth_dark": (15, 55, 55),
        "cloth_mid": (30, 95, 90),
        "cloth_light": (60, 145, 135),
        # Gold armor accents
        "gold_darkest": (55, 35, 5),
        "gold_dark": (120, 85, 20),
        "gold_mid": (195, 155, 45),
        "gold_light": (240, 205, 85),
        "gold_hot": (255, 235, 145),
        "gold_shine": (255, 250, 210),
        # Kraken green magic (main FX)
        "kraken_darkest": (5, 45, 40),
        "kraken_dark": (15, 100, 90),
        "kraken_mid": (30, 190, 170),
        "kraken_light": (95, 245, 220),
        "kraken_hot": (170, 255, 240),
        "kraken_shine": (225, 255, 250),
        "kraken_white": (250, 255, 255),
        # Tentacle body (dark green with lighter suckers)
        "tent_darkest": (5, 30, 30),
        "tent_dark": (15, 65, 65),
        "tent_mid": (30, 115, 105),
        "tent_light": (70, 175, 155),
        "tent_shine": (140, 230, 210),
        # Sucker (light)
        "sucker_dark": (15, 60, 55),
        "sucker_mid": (60, 145, 135),
        "sucker_light": (130, 220, 200),
        # Totem wood/gold
        "totem_dark": (35, 25, 15),
        "totem_mid": (75, 55, 30),
        "totem_light": (135, 105, 65),
        # Eye of totem (glowing green)
        "totem_eye": (100, 255, 220),
        "totem_eye_hot": (200, 255, 240),
        # Sea/ocean deep blue
        "sea_dark": (5, 20, 45),
        "sea_mid": (15, 60, 110),
        # Character eye (deep human)
        "eye_iris": (60, 90, 100),
        "eye_dark": (30, 30, 40),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_okeanora._clamp(color)
        if _NS_okeanora.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_okeanora._clamp(color)
        if _NS_okeanora.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_okeanora._clamp(color),
                                 points[0], points[1], 1)
            elif len(points) == 1:
                pygame.draw.rect(surface, _NS_okeanora._clamp(color),
                                 (points[0][0], points[0][1], 1, 1))
            return
        pygame.draw.polygon(surface, _NS_okeanora._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_okeanora(surface, boss, x, y):
        """Entry point untuk TRUE BOSS Okeanora."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_okeanora._detect_moving(boss)
        _NS_okeanora._update_ok_attack_anim(boss)
        attacking = (
            getattr(boss, "_ok_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind (kraken aura).
        _NS_okeanora._draw_kraken_aura(surface, x, y, pulse)
        _NS_okeanora._draw_ocean_mist(surface, x, y, pulse)
        _NS_okeanora._draw_ground_kraken_ring(surface, x, y + 52, pulse, active_skill)
        # BACKGROUND tentacles (ambient - always visible).
        _NS_okeanora._draw_ambient_tentacles(surface, x, y, pulse)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_okeanora._draw_tentacle_smash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_okeanora._draw_testspirit_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_okeanora._draw_leap_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_okeanora._draw_ok_attack(surface, boss, x, y)
        elif moving:
            _NS_okeanora._draw_ok_float(surface, boss, x, y)
        else:
            _NS_okeanora._draw_ok_idle(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_okeanora._draw_tentacle_smash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_okeanora._draw_harsh_lesson_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_okeanora._draw_testspirit_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_okeanora._draw_leap_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_ok_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ok_previous_timer", 0))
        active = bool(getattr(boss, "_ok_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._ok_attack_active = True
            boss._ok_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._ok_attack_frame = int(
                getattr(boss, "_ok_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._ok_attack_active = False
            boss._ok_attack_frame = 0
            active = False
        boss._ok_previous_timer = timer
        boss._ok_attack_progress = (
            min(1.0, getattr(boss, "_ok_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_ok_last_x"):
            boss._ok_last_x = boss.x
            boss._ok_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ok_last_x)
        dy = abs(boss.y - boss._ok_last_y)
        boss._ok_last_x = boss.x
        boss._ok_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_ok_idle(surface, boss, x, y):
        """Floating majestic idle."""
        bob = int(math.sin(boss.pulse * 0.5) * 4) - 6
        _NS_okeanora._draw_shadow(surface, x, y + 52)
        _NS_okeanora._draw_ocean_trail(surface, x, y + 44, boss.pulse, floating=True)
        _NS_okeanora._draw_ok_body(surface, x, y + bob,
                     boss.direction, boss.pulse, "idle")
    def _draw_ok_float(surface, boss, x, y):
        """Floating movement (priestess levitates)."""
        phase = boss.pulse * 1.6
        bob = int(math.sin(phase * 0.8) * 6) - 8
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_okeanora._draw_shadow(surface, x + sway, y + 52, moving=True)
        _NS_okeanora._draw_ocean_trail(surface, x + sway, y + 44, phase,
                         floating=True, moving=True,
                         facing=boss.direction)
        _NS_okeanora._draw_ok_body(surface, x + sway, y + bob,
                     boss.direction, phase, "float")
    def _draw_ok_attack(surface, boss, x, y):
        """Totem overhead slam."""
        progress = getattr(boss, "_ok_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 4) - 6
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * boss.direction
            lift = int(4 - t * 8) - 6
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4) - 6
        _NS_okeanora._draw_shadow(surface, x + lunge, y + 52)
        _NS_okeanora._draw_ocean_trail(surface, x + lunge, y + 44, boss.pulse,
                         floating=True, intense=True)
        _NS_okeanora._draw_ok_body(surface, x + lunge, y + lift,
                     boss.direction, boss.pulse, "attack", progress)
        if 0.35 <= progress < 0.75:
            _NS_okeanora._draw_totem_slash(surface, boss, x + lunge, y + lift,
                             progress)
    # ============================================================
    # BODY (Priestess with totem)
    # ============================================================
    def _draw_ok_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Draw kraken priestess body."""
        # Back tentacles (behind body, always visible).
        _NS_okeanora._draw_back_tentacles(surface, cx, cy, facing, phase, action)
        # Skirt/loincloth bottom.
        _NS_okeanora._draw_priestess_skirt(surface, cx, cy + 22, facing, phase, action)
        # Torso (muscular).
        _NS_okeanora._draw_ok_torso(surface, cx, cy, facing, phase, action)
        # Back arm (hangs).
        _NS_okeanora._draw_back_arm(surface, cx, cy + 4, facing, phase, action,
                      attack_progress)
        # Head with long hair.
        _NS_okeanora._draw_ok_head(surface, cx, cy - 22, facing, phase, action)
        # Front arm holding TOTEM (foreground).
        _NS_okeanora._draw_totem_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
    def _draw_back_tentacles(surface, cx, cy, facing, phase, action):
        """Multiple kraken tentacles rising behind body."""
        # Draw 3 tentacles behind (arranged fan-shape).
        tentacle_configs = [
            (-25, -8, math.pi * 0.85, 45, 0),   # left back
            (0, -12, math.pi * 0.6, 55, 0.5),   # center back
            (25, -8, math.pi * 0.4, 45, 1.0),   # right back
        ]
        for base_off_x, base_off_y, angle_base, length, phase_off in tentacle_configs:
            _NS_okeanora._draw_single_tentacle(surface, cx + base_off_x,
                                 cy + base_off_y, angle_base,
                                 length, phase + phase_off,
                                 curl=math.sin(phase + phase_off) * 0.4)
    def _draw_single_tentacle(surface, base_x, base_y, base_angle, length,
                                phase, curl=0):
        """Draw a single kraken tentacle from base_x/base_y."""
        # Tentacle curves with sinusoidal wave.
        segments = 12
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            # Base trajectory follows angle.
            base_dist = t * length
            # Add curl (sinusoidal along length).
            curl_amt = math.sin(t * math.pi * 1.5 + phase) * length * 0.15
            wave_angle = base_angle + curl + curl_amt * 0.05
            bx = base_x + int(math.cos(wave_angle) * base_dist)
            by = base_y - int(math.sin(wave_angle) * base_dist)
            # Additional wave sway.
            sway_x = int(math.sin(t * math.pi * 2 + phase) * 4)
            sway_y = int(math.cos(t * math.pi * 2 + phase) * 3)
            bx += sway_x
            by += sway_y
            points.append((bx, by))
        # Draw tentacle segments (tapered thickness).
        for i in range(len(points) - 1):
            t = i / len(points)
            thickness = max(2, 8 - int(t * 6))
            # Shadow.
            _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                    (points[i][0] + 1, points[i][1] + 1),
                    (points[i + 1][0] + 1, points[i + 1][1] + 1),
                    thickness + 1)
            # Dark body.
            _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["tent_darkest"],
                    points[i], points[i + 1], thickness)
            _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["tent_dark"],
                    points[i], points[i + 1], max(1, thickness - 1))
            _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["tent_mid"],
                    points[i], points[i + 1], max(1, thickness - 3))
            _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["tent_light"],
                    (points[i][0], points[i][1] - 1),
                    (points[i + 1][0], points[i + 1][1] - 1),
                    max(1, thickness - 5))
            # Suckers along tentacle (every 2 segments).
            if i > 0 and i % 2 == 0 and thickness > 3:
                sucker_x = points[i][0]
                sucker_y = points[i][1]
                _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["sucker_dark"],
                          (sucker_x, sucker_y), 2)
                _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["sucker_mid"],
                          (sucker_x, sucker_y), 1)
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["sucker_light"],
                                 (sucker_x, sucker_y, 1, 1))
            # Bright green glow highlight along tentacle.
            if i % 3 == 0:
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_light"],
                                 (points[i][0], points[i][1], 1, 1))
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"],
                                 (points[i][0], points[i][1], 1, 1))
        # Tip curls with glow.
        if len(points) >= 2:
            tip = points[-1]
            # Kraken green glow at tip.
            for r in range(4, 0, -1):
                alpha = _NS_okeanora._alpha(150 * (4 - r) / 4)
                _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                          tip, r)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_light"], tip, 2)
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_shine"],
                             (tip[0], tip[1], 1, 1))
    def _draw_priestess_skirt(surface, cx, cy, facing, phase, action):
        """Dark green/gold skirt bottom with tribal accents."""
        sway = math.sin(phase * 0.6) * 2
        # Wide skirt.
        skirt_pts = [
            (cx - 14, cy - 8),
            (cx + 14, cy - 8),
            (cx + 18 + int(sway), cy + 2),
            (cx + 16 + int(sway), cy + 14),
            (cx + 10, cy + 18),
            (cx - 10, cy + 18),
            (cx - 16 - int(sway), cy + 14),
            (cx - 18 - int(sway), cy + 2),
        ]
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in skirt_pts])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["cloth_darkest"], skirt_pts)
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["cloth_dark"], [
            (cx - 13, cy - 7),
            (cx + 13, cy - 7),
            (cx + 17 + int(sway), cy + 2),
            (cx + 15 + int(sway), cy + 13),
            (cx + 9, cy + 17),
            (cx - 9, cy + 17),
            (cx - 15 - int(sway), cy + 13),
            (cx - 17 - int(sway), cy + 2),
        ])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["cloth_mid"], [
            (cx - 11, cy - 5),
            (cx + 11, cy - 5),
            (cx + 14 + int(sway), cy + 2),
            (cx + 12 + int(sway), cy + 12),
            (cx - 12 - int(sway), cy + 12),
            (cx - 14 - int(sway), cy + 2),
        ])
        # Skirt fold lines.
        for x_off in (-8, -3, 3, 8):
            pygame.draw.line(surface, _NS_okeanora.PALETTE["cloth_darkest"],
                             (cx + x_off, cy - 6),
                             (cx + x_off + int(sway * 0.5), cy + 16), 1)
        # Gold belt.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_darkest"],
                         (cx - 12, cy - 8, 24, 4))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_dark"],
                         (cx - 11, cy - 7, 22, 3))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_mid"],
                         (cx - 10, cy - 6, 20, 2))
        pygame.draw.line(surface, _NS_okeanora.PALETTE["gold_light"],
                         (cx - 9, cy - 6), (cx + 9, cy - 6), 1)
        # Gold buckle with green gem in center.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_darkest"],
                         (cx - 4, cy - 9, 8, 6))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_dark"],
                         (cx - 3, cy - 8, 6, 5))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_mid"],
                         (cx - 2, cy - 7, 4, 3))
        # Center gem.
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_okeanora._alpha(150 * (4 - r) / 4 * gem_pulse)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                      (cx, cy - 6), r)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_dark"],
                         (cx - 1, cy - 7, 2, 2))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_mid"], (cx, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"], (cx, cy - 6, 1, 1))
        # Bottom trim (gold).
        pygame.draw.line(surface, _NS_okeanora.PALETTE["gold_light"],
                         (cx - 9, cy + 12), (cx + 9, cy + 12), 1)
    def _draw_ok_torso(surface, cx, cy, facing, phase, action):
        """Muscular female torso with green top + tribal tattoos."""
        breath = math.sin(phase * 0.7) * 1
        # Torso outline (broad shoulders, muscular).
        torso_pts = [
            (cx - 13, cy - 12),
            (cx - 15, cy - 8),
            (cx - 13, cy - 2),
            (cx - 10, cy + 6),
            (cx - 5, cy + 10),
            (cx + 5, cy + 10),
            (cx + 10, cy + 6),
            (cx + 13, cy - 2),
            (cx + 15, cy - 8),
            (cx + 13, cy - 12),
        ]
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_pts])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_darkest"], torso_pts)
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_dark"], [
            (cx - 12, cy - 11),
            (cx - 14, cy - 7),
            (cx - 12, cy - 2),
            (cx - 9, cy + 5),
            (cx - 4, cy + 9),
            (cx + 4, cy + 9),
            (cx + 9, cy + 5),
            (cx + 12, cy - 2),
            (cx + 14, cy - 7),
            (cx + 12, cy - 11),
        ])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_mid"], [
            (cx - 10, cy - 9),
            (cx - 12, cy - 5),
            (cx - 10, cy),
            (cx - 6, cy + 5),
            (cx + 6, cy + 5),
            (cx + 10, cy),
            (cx + 12, cy - 5),
            (cx + 10, cy - 9),
        ])
        # Green tank top (crop top with V neck).
        top_pts = [
            (cx - 11, cy - 10),
            (cx + 11, cy - 10),
            (cx + 12, cy - 4),
            (cx + 10, cy),
            (cx - 10, cy),
            (cx - 12, cy - 4),
        ]
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in top_pts])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["cloth_darkest"], top_pts)
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["cloth_dark"], [
            (cx - 10, cy - 9),
            (cx + 10, cy - 9),
            (cx + 11, cy - 4),
            (cx + 9, cy - 1),
            (cx - 9, cy - 1),
            (cx - 11, cy - 4),
        ])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["cloth_mid"], [
            (cx - 8, cy - 7),
            (cx + 8, cy - 7),
            (cx + 9, cy - 4),
            (cx + 7, cy - 2),
            (cx - 7, cy - 2),
            (cx - 9, cy - 4),
        ])
        # V-neck cut (skin showing).
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_dark"], [
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx, cy - 3),
        ])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_mid"], [
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx, cy - 4),
        ])
        # Highlight sheen on top.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["cloth_light"],
                         (cx - 7, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["cloth_light"],
                         (cx + 5, cy - 8, 2, 1))
        # ABS definition (muscular).
        pygame.draw.line(surface, _NS_okeanora.PALETTE["skin_darkest"],
                         (cx, cy), (cx, cy + 8), 1)
        pygame.draw.line(surface, _NS_okeanora.PALETTE["skin_darkest"],
                         (cx - 4, cy + 3), (cx + 4, cy + 3), 1)
        pygame.draw.line(surface, _NS_okeanora.PALETTE["skin_darkest"],
                         (cx - 4, cy + 6), (cx + 4, cy + 6), 1)
        # TRIBAL TATTOO on arm/shoulder (kraken pattern).
        # Left shoulder tribal marks.
        for i, (x_off, y_off) in enumerate([(-11, -7), (-11, -3), (-12, 1)]):
            pygame.draw.line(surface, _NS_okeanora.PALETTE["shadow_deep"],
                             (cx + x_off - 1, cy + y_off),
                             (cx + x_off + 2, cy + y_off + 1), 1)
        # Bicep muscle highlight.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_light"],
                         (cx + facing * 8, cy - 8, 1, 2))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_shine"],
                         (cx + facing * 8, cy - 8, 1, 1))
        # Big Pauldrons (gold - kraken tentacle motif).
        for side in (-1, 1):
            sh_x = cx + side * 13
            sh_y = cy - 10
            _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["shadow_deep"], [
                (sh_x - 4, sh_y),
                (sh_x + 5 * side, sh_y - 3),
                (sh_x + 6 * side, sh_y + 3),
                (sh_x - 3, sh_y + 4),
            ])
            _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["gold_darkest"], [
                (sh_x - 4, sh_y),
                (sh_x + 5 * side, sh_y - 3),
                (sh_x + 5 * side, sh_y + 3),
                (sh_x - 3, sh_y + 3),
            ])
            _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["gold_dark"], [
                (sh_x - 3, sh_y),
                (sh_x + 4 * side, sh_y - 2),
                (sh_x + 4 * side, sh_y + 2),
                (sh_x - 2, sh_y + 2),
            ])
            _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["gold_mid"], [
                (sh_x - 2, sh_y),
                (sh_x + 3 * side, sh_y - 1),
                (sh_x + 3 * side, sh_y + 1),
                (sh_x - 1, sh_y + 1),
            ])
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_light"],
                             (sh_x + side * 2, sh_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_shine"],
                             (sh_x + side * 2, sh_y - 1, 1, 1))
            # Small kraken green gem on pauldron.
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_dark"],
                             (sh_x + side * 3, sh_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"],
                             (sh_x + side * 3, sh_y + 1, 1, 1))
    def _draw_ok_head(surface, cx, cy, facing, phase, action):
        """Head with tan skin, dark long hair, gold earrings."""
        # Long hair back (very long).
        _NS_okeanora._draw_priestess_hair_back(surface, cx, cy, facing, phase)
        # Face (angular, strong).
        face_pts = [
            (cx - 6, cy),
            (cx - 7, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 7, cy - 4),
            (cx + 6, cy),
            (cx + 4, cy + 5),
            (cx + 1, cy + 7),
            (cx - 1, cy + 7),
            (cx - 4, cy + 5),
        ]
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in face_pts])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_darkest"], face_pts)
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_dark"], [
            (cx - 5, cy),
            (cx - 6, cy - 4),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 6, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["skin_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy - 4),
            (cx - 3, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy - 4),
            (cx + 4, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Cheek highlight.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_light"],
                         (cx + facing * 3, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_shine"],
                         (cx + facing * 3, cy - 2, 1, 1))
        # EYES (deep serious blue-green).
        for eye_side in (-1, 1):
            eye_x = cx + eye_side * 2
            eye_y = cy - 3
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["shadow_deep"],
                             (eye_x - 1, eye_y, 3, 2))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["white"],
                             (eye_x - 1, eye_y, 3, 2))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["eye_iris"],
                             (eye_x, eye_y, 2, 2))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["eye_dark"],
                             (eye_x, eye_y, 1, 1))
        # Strong eyebrows.
        pygame.draw.line(surface, _NS_okeanora.PALETTE["hair_darkest"],
                         (cx - 5, cy - 5), (cx - 1, cy - 6), 1)
        pygame.draw.line(surface, _NS_okeanora.PALETTE["hair_darkest"],
                         (cx + 1, cy - 6), (cx + 5, cy - 5), 1)
        # Serious lips.
        pygame.draw.line(surface, _NS_okeanora.PALETTE["skin_darkest"],
                         (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_dark"],
                         (cx, cy + 3, 1, 1))
        # Front bangs.
        _NS_okeanora._draw_priestess_hair_front(surface, cx, cy - 7, facing, phase)
        # Gold earrings (large hoops).
        for side in (-1, 1):
            ear_x = cx + side * 7
            ear_y = cy + 1
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["shadow_deep"],
                      (ear_x + 1, ear_y + 1), 2)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_dark"], (ear_x, ear_y), 2)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_mid"], (ear_x, ear_y), 2, 1)
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_light"],
                             (ear_x, ear_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_shine"],
                             (ear_x, ear_y - 1, 1, 1))
    def _draw_priestess_hair_back(surface, cx, cy, facing, phase):
        """Very long dark flowing hair."""
        sway = math.sin(phase * 0.7) * 4
        hair_pts = [
            (cx - 7, cy - 8),
            (cx - 10, cy - 4),
            (cx - 13 - int(sway * 0.5), cy + 6),
            (cx - 15 - int(sway), cy + 18),
            (cx - 13 - int(sway * 1.5), cy + 30),
            (cx - 9 - int(sway * 1.8), cy + 40),
            (cx - 3 - int(sway * 1.5), cy + 44),
            (cx + 3 + int(sway * 1.5), cy + 44),
            (cx + 9 + int(sway * 1.8), cy + 40),
            (cx + 13 + int(sway * 1.5), cy + 30),
            (cx + 15 + int(sway), cy + 18),
            (cx + 13 + int(sway * 0.5), cy + 6),
            (cx + 10, cy - 4),
            (cx + 7, cy - 8),
        ]
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in hair_pts])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["hair_darkest"], hair_pts)
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["hair_dark"], [
            (cx - 6, cy - 7),
            (cx - 9, cy - 3),
            (cx - 12 - int(sway * 0.5), cy + 6),
            (cx - 13 - int(sway), cy + 18),
            (cx - 11 - int(sway * 1.5), cy + 28),
            (cx - 6 - int(sway * 1.8), cy + 38),
            (cx + 6 + int(sway * 1.8), cy + 38),
            (cx + 11 + int(sway * 1.5), cy + 28),
            (cx + 13 + int(sway), cy + 18),
            (cx + 12 + int(sway * 0.5), cy + 6),
            (cx + 9, cy - 3),
            (cx + 6, cy - 7),
        ])
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["hair_mid"], [
            (cx - 5, cy - 5),
            (cx - 8, cy),
            (cx - 10 - int(sway * 0.5), cy + 10),
            (cx - 8 - int(sway), cy + 20),
            (cx + 8 + int(sway), cy + 20),
            (cx + 10 + int(sway * 0.5), cy + 10),
            (cx + 8, cy),
            (cx + 5, cy - 5),
        ])
        # Hair strand highlights.
        for i, x_off in enumerate((-8, -4, 4, 8)):
            pygame.draw.line(surface, _NS_okeanora.PALETTE["hair_light"],
                             (cx + x_off, cy - 4),
                             (cx + x_off + int(sway * 0.3), cy + 30), 1)
    def _draw_priestess_hair_front(surface, cx, cy, facing, phase):
        """Front bangs."""
        bang_pts = [
            (cx - 6, cy + 3),
            (cx - 7, cy),
            (cx - 4, cy - 3),
            (cx, cy - 4),
            (cx + 4, cy - 3),
            (cx + 7, cy),
            (cx + 6, cy + 3),
            (cx + 3, cy),
            (cx - 3, cy),
        ]
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["hair_darkest"], bang_pts)
        _NS_okeanora._poly(surface, _NS_okeanora.PALETTE["hair_dark"], [
            (cx - 5, cy + 2),
            (cx - 6, cy),
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 6, cy),
            (cx + 5, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["hair_mid"], (cx - 1, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["hair_light"], (cx - 1, cy - 2, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (muscular, hangs)."""
        back_dir = -facing
        b_shoulder_x = cx + back_dir * 12
        b_shoulder_y = cy - 8
        sway = math.sin(phase * 0.6) * 1
        b_elbow_x = b_shoulder_x + back_dir * 2 + int(sway)
        b_elbow_y = b_shoulder_y + 8
        b_hand_x = b_elbow_x + back_dir * 1 + int(sway)
        b_hand_y = b_elbow_y + 8
        # Upper arm (muscular tan skin).
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                (b_shoulder_x + 1, b_shoulder_y + 1),
                (b_elbow_x + 1, b_elbow_y + 1), 6)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_darkest"],
                (b_shoulder_x, b_shoulder_y), (b_elbow_x, b_elbow_y), 5)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_dark"],
                (b_shoulder_x, b_shoulder_y), (b_elbow_x, b_elbow_y), 4)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_mid"],
                (b_shoulder_x + back_dir, b_shoulder_y),
                (b_elbow_x + back_dir, b_elbow_y), 2)
        # Tribal tattoo on arm.
        mid_x = int((b_shoulder_x + b_elbow_x) / 2)
        mid_y = int((b_shoulder_y + b_elbow_y) / 2)
        pygame.draw.line(surface, _NS_okeanora.PALETTE["shadow_deep"],
                         (mid_x - 1, mid_y), (mid_x + 2, mid_y + 1), 1)
        # Gold armband.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_dark"],
                         (b_elbow_x - 2, b_elbow_y - 2, 5, 3))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_mid"],
                         (b_elbow_x - 1, b_elbow_y - 2, 4, 2))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_light"],
                         (b_elbow_x, b_elbow_y - 2, 1, 1))
        # Forearm.
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                (b_elbow_x + 1, b_elbow_y + 1),
                (b_hand_x + 1, b_hand_y + 1), 5)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_darkest"],
                (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 4)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_dark"],
                (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 3)
        # Hand (fist).
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["shadow_deep"],
                  (b_hand_x + 1, b_hand_y + 1), 3)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["skin_darkest"],
                  (b_hand_x, b_hand_y), 3)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["skin_dark"],
                  (b_hand_x, b_hand_y), 2)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_mid"],
                         (b_hand_x, b_hand_y - 1, 1, 1))
    def _draw_totem_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding LARGE totem with eye."""
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 8
        # Angle convention.
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.55 + t * 0.4)
                totem_extra = math.pi * 0.3
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (0.95 - t * 1.15)
                totem_extra = math.pi * (0.3 - t * 0.6)
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.2 + t * 0.35)
                totem_extra = math.pi * (-0.3 + t * 0.4)
        elif action == "float":
            arm_angle = math.pi * 0.15 + math.sin(phase) * 0.05
            totem_extra = math.pi * 0.1
        else:
            arm_angle = math.pi * 0.12 + math.sin(phase * 0.5) * 0.03
            totem_extra = math.pi * 0.08
        upper_len = 11
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)
        forearm_len = 11
        hand_angle = arm_angle - math.pi * 0.15
        hand_x = elbow_x + int(math.cos(hand_angle) * forearm_len) * facing
        hand_y = elbow_y - int(math.sin(hand_angle) * forearm_len)
        # Upper arm.
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 7)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["skin_light"],
                         (shoulder_x + facing * 2, shoulder_y - 1, 1, 1))
        # Tribal tattoo on arm.
        mid_x = int((shoulder_x + elbow_x) / 2)
        mid_y = int((shoulder_y + elbow_y) / 2)
        pygame.draw.line(surface, _NS_okeanora.PALETTE["shadow_deep"],
                         (mid_x - 1, mid_y - 1), (mid_x + 2, mid_y), 1)
        # Gold armband.
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_darkest"], (elbow_x, elbow_y), 4)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_dark"], (elbow_x, elbow_y), 3)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_mid"], (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_light"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_shine"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # Kraken green gem on armband.
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"],
                         (elbow_x + 1, elbow_y + 1, 1, 1))
        # Forearm.
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1),
                (hand_x + 1, hand_y + 1), 6)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["skin_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Hand (large grip).
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["shadow_deep"],
                  (hand_x + 1, hand_y + 1), 5)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["skin_darkest"],
                  (hand_x, hand_y), 5)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["skin_dark"],
                  (hand_x, hand_y), 4)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["skin_mid"],
                  (hand_x, hand_y), 3)
        # LARGE TOTEM STAFF.
        totem_angle = hand_angle + totem_extra
        _NS_okeanora._draw_totem(surface, hand_x, hand_y, totem_angle, facing, phase)
    def _draw_totem(surface, hx, hy, angle, facing, phase):
        """LARGE totem staff with glowing eye."""
        # Handle/shaft (below the totem head).
        handle_len = 10
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy + int(math.sin(angle) * handle_len)
        # Wooden shaft.
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 5)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["totem_dark"],
                (hx, hy), (handle_end_x, handle_end_y), 4)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["totem_mid"],
                (hx, hy), (handle_end_x, handle_end_y), 3)
        _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["totem_light"],
                (hx, hy - 1), (handle_end_x, handle_end_y - 1), 1)
        # Gold cap at handle end.
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["shadow_deep"],
                  (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_dark"],
                  (handle_end_x, handle_end_y), 3)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_mid"],
                  (handle_end_x, handle_end_y), 2)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_light"],
                         (handle_end_x, handle_end_y - 1, 1, 1))
        # TOTEM HEAD (large sphere with tentacle arms).
        head_len = 22
        head_cx = hx + int(math.cos(angle) * head_len) * facing
        head_cy = hy - int(math.sin(angle) * head_len)
        # Connector between shaft and head (thick wood).
        for step in range(1, 6):
            t = step / 5
            tx = int(hx + (head_cx - hx) * t)
            ty = int(hy + (head_cy - hy) * t)
            thickness = 5 + int((1 - t) * 2)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["shadow_deep"],
                      (tx + 1, ty + 1), thickness)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["totem_dark"], (tx, ty), thickness)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["totem_mid"], (tx, ty), thickness - 1)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["totem_light"], (tx, ty), thickness - 3)
        # Big head (gold sphere).
        head_r = 9
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["shadow_deep"],
                  (head_cx + 1, head_cy + 1), head_r + 1)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_darkest"],
                  (head_cx, head_cy), head_r)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_dark"],
                  (head_cx, head_cy), head_r - 1)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_mid"],
                  (head_cx, head_cy), head_r - 2)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["gold_light"],
                  (head_cx, head_cy - 1), head_r - 4)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_shine"],
                         (head_cx - 2, head_cy - 3, 1, 1))
        # GLOWING GREEN EYE center of totem.
        eye_pulse = math.sin(phase * 2) * 0.4 + 0.6
        for r in range(7, 0, -1):
            alpha = _NS_okeanora._alpha(180 * (7 - r) / 7 * eye_pulse)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                      (head_cx, head_cy), r)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_dark"], (head_cx, head_cy), 4)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_mid"], (head_cx, head_cy), 3)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_light"], (head_cx, head_cy), 2)
        _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_hot"], (head_cx, head_cy), 1)
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_shine"],
                         (head_cx, head_cy, 1, 1))
        pygame.draw.rect(surface, _NS_okeanora.PALETTE["white"], (head_cx, head_cy, 1, 1))
        # Vertical pupil (kraken-like).
        pygame.draw.line(surface, _NS_okeanora.PALETTE["shadow_deep"],
                         (head_cx, head_cy - 3),
                         (head_cx, head_cy + 3), 1)
        # Tentacle arms on totem (top).
        for i in range(3):
            arm_angle_offset = (i - 1) * math.pi * 0.3
            tent_angle = angle + math.pi * 0.5 + arm_angle_offset
            # Add wave.
            wave = math.sin(phase * 1.5 + i) * 0.3
            for step in range(1, 5):
                st = step / 4
                arm_length = 8
                base_x = head_cx
                base_y = head_cy - head_r + 2
                arm_x = base_x + int(math.cos(tent_angle + wave * st)
                                     * arm_length * st) * facing
                arm_y = base_y - int(math.sin(tent_angle + wave * st)
                                     * arm_length * st)
                thickness = max(1, 3 - step // 2)
                if step == 1:
                    prev = (base_x, base_y)
                else:
                    _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["shadow_deep"],
                            (prev[0] + 1, prev[1] + 1),
                            (arm_x + 1, arm_y + 1), thickness + 1)
                    _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["gold_dark"],
                            prev, (arm_x, arm_y), thickness)
                    _NS_okeanora._aaline(surface, _NS_okeanora.PALETTE["gold_mid"],
                            prev, (arm_x, arm_y), max(1, thickness - 1))
                    pygame.draw.rect(surface, _NS_okeanora.PALETTE["gold_light"],
                                     (arm_x, arm_y, 1, 1))
                prev = (arm_x, arm_y)
            # Green glow at tentacle tip.
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"],
                             (arm_x, arm_y, 1, 1))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_shine"],
                             (arm_x, arm_y, 1, 1))
        # Aura around totem head.
        aura_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(head_r + 6, head_r, -1):
            alpha = _NS_okeanora._alpha(80 * (r - head_r) / 6 * aura_pulse)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_light"], alpha),
                      (head_cx, head_cy), r)
    def _draw_totem_slash(surface, boss, cx, cy, progress):
        """Kraken green slash arc during totem swing."""
        facing = boss.direction
        swing_t = max(0.0, min(1.0, (progress - 0.35) / 0.4))
        arc_center_x = cx + facing * 8
        arc_center_y = cy - 6
        radius = 40  # LARGE (big totem)
        num_slices = 14
        for slice_i in range(num_slices):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.85
            sweep_end = -math.pi * 0.2
            local_swing = max(0.0, swing_t - slice_t * 0.1)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            fade = 1 - slice_t * 0.75
            alpha = _NS_okeanora._alpha(240 * fade
                            * (1 - abs(swing_t - 0.5) * 1.4))
            if alpha <= 0:
                continue
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            size = max(2, int(8 * fade))
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                      (arc_x, arc_y), size + 1)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                      (arc_x, arc_y), size)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                      (arc_x, arc_y), max(1, size - 1))
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_light"], alpha),
                      (arc_x, arc_y), max(1, size - 2))
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                      (arc_x, arc_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                             (arc_x, arc_y, 1, 1))
        # Bright leading crescent line.
        crescent_pts = []
        for slice_i in range(num_slices + 1):
            slice_t = slice_i / num_slices
            sweep_start = math.pi * 0.85
            sweep_end = -math.pi * 0.2
            local_swing = max(0.0, swing_t - slice_t * 0.06)
            angle = sweep_start + (sweep_end - sweep_start) * local_swing
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            crescent_pts.append((arc_x, arc_y))
        if len(crescent_pts) > 1:
            for i in range(len(crescent_pts) - 1):
                alpha = _NS_okeanora._alpha(240 * (1 - abs(swing_t - 0.5) * 1.4))
                _NS_okeanora._aaline(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 2)
                _NS_okeanora._aaline(surface, (*_NS_okeanora.PALETTE["kraken_white"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 1)
    # ============================================================
    # AMBIENT TENTACLES (background - always visible)
    # ============================================================
    def _draw_ambient_tentacles(surface, x, y, phase):
        """Additional tentacles emerging from ground around boss (ambient FX)."""
        # 4 small tentacles emerging from ground in fan behind boss.
        for i, (off_x, off_y, angle_base) in enumerate([
            (-45, 25, math.pi * 0.95),  # far left
            (-25, 35, math.pi * 0.85),  # near left
            (25, 35, math.pi * 0.15),   # near right
            (45, 25, math.pi * 0.05),   # far right
        ]):
            base_x = x + off_x
            base_y = y + off_y
            length = 30 + int(math.sin(phase * 0.5 + i) * 5)
            _NS_okeanora._draw_single_tentacle(surface, base_x, base_y, angle_base,
                                 length, phase + i * 0.8, curl=0.2)
    # ============================================================
    # OCEAN TRAIL / AMBIENT
    # ============================================================
    def _draw_ocean_trail(surface, cx, cy, phase, floating=False,
                            moving=False, intense=False, facing=1):
        """Green particles rising below priestess."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Ocean green mist cloud.
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.3) * 0.3 + 0.7
        for radius in range(32, 3, -2):
            alpha = _NS_okeanora._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_okeanora._alpha((20 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising green particles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_okeanora._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                      (sx, sy), 3)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                      (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Bright sparkles.
        for i in range(12):
            spark_t = (phase * 0.7 + i * 0.09) % 1.0
            ex = cx - 28 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_okeanora._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail.
        if moving:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_okeanora._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                          (sx, sy), max(2, 7 - i))
                _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                          (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                                 (sx, sy - 1, 1, 1))
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 8, 8, 170), (5, 9, 140, 14))
        pygame.draw.ellipse(shadow, (20, 60, 55, 110), (12, 11, 126, 10))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_kraken_aura(surface, x, y, phase):
        """Big kraken green aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_okeanora._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_okeanora._aacircle(aura, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                          (120, 105), radius)
        for radius in range(70, 5, -3):
            alpha = _NS_okeanora._alpha((70 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_okeanora._aacircle(aura, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                          (120, 105), radius)
        for radius in range(40, 5, -2):
            alpha = _NS_okeanora._alpha((40 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_okeanora._aacircle(aura, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                          (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # Floating kraken embers.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            r = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"], (sx, sy, 1, 1))
    def _draw_ocean_mist(surface, x, y, phase):
        """Faint ocean mist background (moving waves)."""
        # Draw faint wavy horizontal lines around boss.
        for i in range(4):
            wave_y = y - 20 + i * 15
            wave_alpha = _NS_okeanora._alpha(60)
            for xp in range(-90, 90, 4):
                offset = int(math.sin(xp * 0.05 + phase + i) * 3)
                px = x + xp
                py = wave_y + offset
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_dark"], wave_alpha),
                                 (px, py, 2, 1))
    def _draw_ground_kraken_ring(surface, x, y, phase, skill):
        """Large ground ring with kraken runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_okeanora.PALETTE["kraken_dark"], 200),
                            (5, 20, 190, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_okeanora.PALETTE["kraken_darkest"], 220),
                            (14, 22, 172, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_okeanora.PALETTE["kraken_mid"], 200),
                            (25, 25, 150, 20), 1)
        pygame.draw.ellipse(ring, (*_NS_okeanora.PALETTE["kraken_dark"], 180),
                            (45, 27, 110, 16), 1)
        # Runes (spiraling).
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 55)
            y1 = 33 + int(math.sin(angle) * 10)
            x2 = 100 + int(math.cos(angle) * 86)
            y2 = 33 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_okeanora.PALETTE["kraken_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, (*_NS_okeanora.PALETTE["kraken_shine"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_okeanora.PALETTE["kraken_hot"],
                                        _NS_okeanora._alpha(180 * pulse)),
                                (15, 12, 170, 44), 1)
        surface.blit(ring, (x - 100, y - 30))
    # ============================================================
    # SKILL Q: TENTACLE SMASH (spawn tentacle at target)
    # ============================================================
    def _draw_tentacle_smash_ground(surface, boss, x, y, timer, phase):
        """Ground crack + spawn marker at target."""
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(30 * min(1.0, progress * 3))
        if r > 3:
            # Ground ripple.
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_dark"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_mid"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)
    def _draw_tentacle_smash_foreground(surface, boss, x, y, timer, pulse):
        """Tentacle rises at target and smashes down."""
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Wind-up: totem raises.
            pass  # (arm anim handled separately if needed)
        elif progress < 0.5:
            # Tentacle rises from ground.
            t = (progress - 0.2) / 0.3
            tent_height = int(50 * t)
            _NS_okeanora._draw_single_tentacle(surface, tx, ty + 10, math.pi * 0.5,
                                 tent_height, pulse * 2, curl=0.1)
        elif progress < 0.75:
            # Tentacle smashes DOWN.
            t = (progress - 0.5) / 0.25
            # Smash arc from up to down.
            smash_angle = math.pi * 0.5 - t * math.pi * 0.7
            _NS_okeanora._draw_single_tentacle(surface, tx, ty + 10, smash_angle,
                                 55, pulse * 2, curl=0.3)
        else:
            # Impact.
            t = (progress - 0.75) / 0.25
            impact_r = int(20 + t * 25)
            alpha = _NS_okeanora._alpha(240 * (1 - t))
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                      (tx, ty), impact_r + 2, 3)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                      (tx, ty), impact_r, 2)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                      (tx, ty), max(1, impact_r - 5), 2)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_light"], alpha),
                      (tx, ty), max(1, impact_r - 10), 1)
            # Radial burst.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                                 (ex, ey, 1, 1))
            # Ambient tentacle still visible partially.
            _NS_okeanora._draw_single_tentacle(surface, tx, ty + 5, -math.pi * 0.2,
                                 int(30 * (1 - t)), pulse * 2, curl=0.5)
    # ============================================================
    # SKILL W: HARSH LESSON (dash forward with green energy)
    # ============================================================
    def _draw_harsh_lesson_skill(surface, boss, x, y, timer, phase):
        """Dash forward + kraken green energy stream."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        if progress < 0.25:
            # Wind-up.
            t = progress / 0.25
            charge_x = x + facing * 25
            charge_y = y - 10
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_okeanora._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                          (charge_x, charge_y), r)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_mid"],
                      (charge_x, charge_y), cr - 3)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_light"],
                      (charge_x, charge_y), max(1, cr - 6))
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_shine"],
                      (charge_x, charge_y), max(1, cr - 9))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 30
            start_y = y - 8
            # Dash beam forward.
            beam_end_x = int(start_x + (tx - start_x) * min(1.0, t * 1.3))
            beam_end_y = int(start_y + (ty - start_y) * min(1.0, t * 1.3))
            # Layered kraken beam.
            for width, color, alpha_val in [
                (10, _NS_okeanora.PALETTE["kraken_darkest"], 180),
                (7, _NS_okeanora.PALETTE["kraken_dark"], 220),
                (5, _NS_okeanora.PALETTE["kraken_mid"], 240),
                (3, _NS_okeanora.PALETTE["kraken_light"], 250),
                (2, _NS_okeanora.PALETTE["kraken_hot"], 255),
                (1, _NS_okeanora.PALETTE["kraken_shine"], 255),
            ]:
                pygame.draw.line(surface, (*color, alpha_val),
                                 (start_x, start_y),
                                 (beam_end_x, beam_end_y), width)
            # Bright head.
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_darkest"],
                      (beam_end_x, beam_end_y), 12)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_dark"],
                      (beam_end_x, beam_end_y), 9)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_mid"],
                      (beam_end_x, beam_end_y), 6)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_light"],
                      (beam_end_x, beam_end_y), 4)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_hot"],
                      (beam_end_x, beam_end_y), 2)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_shine"],
                      (beam_end_x, beam_end_y), 1)
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["white"],
                             (beam_end_x, beam_end_y, 1, 1))
            # Radial burst at head.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = beam_end_x + int(math.cos(angle_s) * 14)
                ey = beam_end_y + int(math.sin(angle_s) * 14)
                pygame.draw.line(surface, _NS_okeanora.PALETTE["kraken_hot"],
                                 (beam_end_x, beam_end_y), (ex, ey), 2)
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_shine"],
                                 (ex, ey, 2, 2))
            # Sparks along beam.
            beam_dx = beam_end_x - start_x
            beam_dy = beam_end_y - start_y
            beam_len = max(1, math.sqrt(beam_dx ** 2 + beam_dy ** 2))
            for i in range(int(beam_len / 10)):
                trail_t = i * 10 / beam_len
                px = int(start_x + beam_dx * trail_t)
                py = int(start_y + beam_dy * trail_t)
                perp_x = -beam_dy / beam_len
                perp_y = beam_dx / beam_len
                offset = math.sin(phase * 5 + i) * 5
                spx = int(px + perp_x * offset)
                spy = int(py + perp_y * offset)
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"], (spx, spy, 2, 2))
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_shine"], (spx, spy, 1, 1))
    # ============================================================
    # SKILL E: TEST OF SPIRIT (spirit extraction)
    # ============================================================
    def _draw_testspirit_ground(surface, boss, x, y, timer, phase):
        """Ground circle at target."""
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(25 * min(1.0, progress * 2))
        if r > 3:
            for i in range(3):
                alpha = _NS_okeanora._alpha(220 - i * 60)
                pygame.draw.ellipse(surface,
                                    (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                                    (tx - r, ty - r // 3,
                                     r * 2, r * 2 // 3), 2)
    def _draw_testspirit_foreground(surface, boss, x, y, timer, phase):
        """Spirit extracted from target - green ghostly figure."""
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Spirit extracting (rising).
            t = progress / 0.3
            spirit_y = ty - int(t * 30)
            spirit_alpha = _NS_okeanora._alpha(200 * t)
            # Ghostly figure (simple silhouette).
            _NS_okeanora._draw_spirit_figure(surface, tx, spirit_y, phase, spirit_alpha)
            # Extraction beam from ground.
            for i in range(4):
                beam_y = ty - int(t * 30 * (i + 1) / 4)
                alpha = _NS_okeanora._alpha(180 - i * 30)
                pygame.draw.line(surface,
                                 (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                                 (tx - 2, beam_y),
                                 (tx + 2, beam_y), 1)
        elif progress < 0.85:
            # Spirit floating (fully visible).
            float_bob = int(math.sin(phase * 2) * 3)
            spirit_y = ty - 30 + float_bob
            _NS_okeanora._draw_spirit_figure(surface, tx, spirit_y, phase, 220)
            # Chain connecting spirit to boss (kraken tether).
            chain_start_x = x
            chain_start_y = y - 15
            chain_end_x = tx
            chain_end_y = spirit_y
            # Draw wavy chain.
            for step in range(10):
                st = step / 10
                nt = (step + 1) / 10
                bx1 = int(chain_start_x + (chain_end_x - chain_start_x) * st)
                by1 = int(chain_start_y + (chain_end_y - chain_start_y) * st)
                bx2 = int(chain_start_x + (chain_end_x - chain_start_x) * nt)
                by2 = int(chain_start_y + (chain_end_y - chain_start_y) * nt)
                wave = int(math.sin(phase * 3 + step) * 4)
                perp_len = 1
                pygame.draw.line(surface, _NS_okeanora.PALETTE["kraken_dark"],
                                 (bx1, by1 + wave),
                                 (bx2, by2 + wave), 3)
                pygame.draw.line(surface, _NS_okeanora.PALETTE["kraken_mid"],
                                 (bx1, by1 + wave),
                                 (bx2, by2 + wave), 2)
                pygame.draw.line(surface, _NS_okeanora.PALETTE["kraken_hot"],
                                 (bx1, by1 + wave),
                                 (bx2, by2 + wave), 1)
        else:
            # Spirit dissipating.
            t = (progress - 0.85) / 0.15
            spirit_y = ty - 30 - int(t * 20)
            spirit_alpha = _NS_okeanora._alpha(200 * (1 - t))
            if spirit_alpha > 0:
                _NS_okeanora._draw_spirit_figure(surface, tx, spirit_y, phase, spirit_alpha)
    def _draw_spirit_figure(surface, cx, cy, phase, alpha):
        """Green ghostly humanoid figure."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Outer glow.
        for r in range(12, 4, -1):
            glow_alpha = _NS_okeanora._alpha(alpha * (12 - r) / 12 * 0.4 * pulse)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], glow_alpha),
                      (cx, cy), r)
        # Simple humanoid silhouette (head + body).
        # Head.
        _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha), (cx, cy - 6), 3)
        _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha), (cx, cy - 6), 2)
        # Body (elongated).
        _NS_okeanora._poly(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha), [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ])
        _NS_okeanora._poly(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha), [
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
        ])
        # Arms (raised, ghostly).
        wave = math.sin(phase * 1.5) * 2
        pygame.draw.line(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                         (cx - 3, cy - 1),
                         (cx - 6 + int(wave), cy - 4), 2)
        pygame.draw.line(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                         (cx + 3, cy - 1),
                         (cx + 6 + int(wave), cy - 4), 2)
        # Trailing bottom (ghost tail).
        for i in range(3):
            tail_alpha = _NS_okeanora._alpha(alpha * (3 - i) / 3)
            wave_x = int(math.sin(phase * 2 + i) * 3)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], tail_alpha),
                      (cx + wave_x, cy + 6 + i * 2), 2)
            pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_hot"], tail_alpha),
                             (cx + wave_x, cy + 6 + i * 2, 1, 1))
        # Bright core.
        pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                         (cx, cy - 6, 1, 1))
        pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                         (cx, cy - 1, 1, 1))
        # +HP indicator floating.
        heal_alpha = _NS_okeanora._alpha(alpha)
        pygame.draw.rect(surface, (100, 220, 100, heal_alpha),
                         (cx - 8, cy - 12, 3, 1))
        pygame.draw.rect(surface, (100, 220, 100, heal_alpha),
                         (cx - 7, cy - 13, 1, 3))
    # ============================================================
    # SKILL R: LEAP OF FAITH (leap + massive slam + spawn tentacles)
    # ============================================================
    def _draw_leap_ground(surface, boss, x, y, timer, phase):
        """Ground marker + expanding impact."""
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning circle grows.
            t = progress / 0.4
            r = int(60 * t)
            alpha = _NS_okeanora._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning marks.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_okeanora.PALETTE["kraken_hot"], (sx, sy, 2, 2))
        else:
            # Post-impact: expanding kraken pool.
            t = (progress - 0.4) / 0.6
            r = int(60 + t * 35)
            alpha = _NS_okeanora._alpha(220 * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_leap_foreground(surface, boss, x, y, timer, phase):
        """Massive leap slam + spawn multiple tentacles around impact."""
        tx, ty = _NS_okeanora._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Leap phase - energy gathering above target.
            t = progress / 0.3
            gather_y = ty - int((1 - t) * 80)
            gather_r = int(8 + t * 10)
            for r in range(gather_r + 5, 0, -1):
                alpha = _NS_okeanora._alpha(200 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                          (tx, gather_y), r)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_mid"],
                      (tx, gather_y), gather_r - 3)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_light"],
                      (tx, gather_y), max(1, gather_r - 6))
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_shine"],
                      (tx, gather_y), max(1, gather_r - 9))
        elif progress < 0.5:
            # Slam DOWN from sky.
            t = (progress - 0.3) / 0.2
            slam_start_y = max(0, ty - 100)
            slam_y = int(slam_start_y + (ty - slam_start_y) * t)
            # Bright descending beam.
            for width, color, alpha_val in [
                (14, _NS_okeanora.PALETTE["kraken_darkest"], 140),
                (10, _NS_okeanora.PALETTE["kraken_dark"], 180),
                (6, _NS_okeanora.PALETTE["kraken_mid"], 220),
                (3, _NS_okeanora.PALETTE["kraken_light"], 250),
                (1, _NS_okeanora.PALETTE["kraken_shine"], 255),
            ]:
                pygame.draw.line(surface, (*color, alpha_val),
                                 (tx, slam_start_y),
                                 (tx, slam_y), width)
            # Bright descending head.
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_darkest"], (tx, slam_y), 12)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_dark"], (tx, slam_y), 9)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_mid"], (tx, slam_y), 6)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_light"], (tx, slam_y), 4)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_hot"], (tx, slam_y), 2)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_shine"], (tx, slam_y), 1)
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["white"], (tx, slam_y, 1, 1))
        elif progress < 0.85:
            # IMPACT + spawn multiple tentacles!
            t = (progress - 0.5) / 0.35
            impact_r = int(25 + t * 55)
            alpha = _NS_okeanora._alpha(240 * (1 - t * 0.5))
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_darkest"], alpha),
                      (tx, ty), impact_r + 3, 4)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_dark"], alpha),
                      (tx, ty), impact_r, 3)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                      (tx, ty), max(1, impact_r - 6), 3)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_light"], alpha),
                      (tx, ty), max(1, impact_r - 12), 2)
            _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                      (tx, ty), max(1, impact_r - 18), 1)
            # Bright center.
            core_r = max(4, int(15 - t * 10))
            for r in range(core_r + 5, 0, -1):
                core_alpha = _NS_okeanora._alpha(200 * (core_r + 5 - r) / (core_r + 5)
                                     * (1 - t * 0.3))
                _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_hot"], core_alpha),
                          (tx, ty), r)
            _NS_okeanora._aacircle(surface, _NS_okeanora.PALETTE["kraken_shine"], (tx, ty), core_r // 2)
            pygame.draw.rect(surface, _NS_okeanora.PALETTE["white"], (tx, ty, 1, 1))
            # SPAWN 6 TENTACLES around impact!
            for i in range(6):
                tent_angle = i * math.pi / 3 + math.pi / 6
                tent_base_x = tx + int(math.cos(tent_angle) * 30)
                tent_base_y = ty + int(math.sin(tent_angle) * 20) + 5
                # Tentacle grows over time.
                tent_length = int(40 * min(1.0, t * 1.5))
                if tent_length > 5:
                    _NS_okeanora._draw_single_tentacle(surface, tent_base_x, tent_base_y,
                                         math.pi * 0.6, tent_length,
                                         phase + i * 0.5, curl=0.3)
            # Radial burst rays.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_okeanora.PALETTE["kraken_shine"], alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["white"], alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath: tentacles retreat + rising particles.
            t = (progress - 0.85) / 0.15
            # Fading tentacles.
            for i in range(6):
                tent_angle = i * math.pi / 3 + math.pi / 6
                tent_base_x = tx + int(math.cos(tent_angle) * 30)
                tent_base_y = ty + int(math.sin(tent_angle) * 20) + 5
                tent_length = int(40 * (1 - t))
                if tent_length > 5:
                    _NS_okeanora._draw_single_tentacle(surface, tent_base_x, tent_base_y,
                                         math.pi * 0.6, tent_length,
                                         phase + i * 0.5, curl=0.3)
            # Rising particles.
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - int(rise_t * 50)
                alpha = _NS_okeanora._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_okeanora._aacircle(surface, (*_NS_okeanora.PALETTE["kraken_mid"], alpha),
                              (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_okeanora.PALETTE["kraken_hot"], alpha),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_grimjack(surface, boss, x, y):
    """Entry point grimjack."""
    return _NS_grimjack.draw_grimjack(surface, boss, x, y)


def draw_morvaeth(surface, boss, x, y):
    """Entry point morvaeth."""
    return _NS_morvaeth.draw_morvaeth(surface, boss, x, y)


def draw_vulkareth(surface, boss, x, y):
    """Entry point vulkareth."""
    return _NS_vulkareth.draw_vulkareth(surface, boss, x, y)


def draw_okeanora(surface, boss, x, y):
    """Entry point okeanora."""
    return _NS_okeanora.draw_okeanora(surface, boss, x, y)
