"""
bosses/level35.py - Semua boss Level 35

Berisi:
  - kaerissa    (mini boss - MELEE bloodwhirl assassin, daggers)
  - thorgaruk   (mini boss - MELEE skyhorn, storm axe)
  - zorathiel   (mini boss - RANGED arcanist, arcane magic)
  - lyssarethys (TRUE BOSS - RANGED heartbane, magenta soul magic)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _thg_ (thorgaruk), _zor_ (zorathiel), _lys_ (lyssarethys) sudah unik.
  - _kae_ (kaerissa) di-rename -> _krs_ (bentrok dengan kaervosth
    level 26), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KAERISSA (BLOODWHIRL) - Mini Boss
# ====================================================================

class _NS_kaerissa:
    """Namespace kaerissa - assassin mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (fair, slight cool tint)
        "skin_darkest": (55, 35, 35),
        "skin_dark": (110, 75, 70),
        "skin_mid": (185, 145, 130),
        "skin_light": (230, 200, 185),
        "skin_shine": (250, 235, 225),
        # Leather armor (dark brown-black)
        "leather_darkest": (10, 6, 8),
        "leather_dark": (30, 18, 20),
        "leather_mid": (60, 40, 42),
        "leather_light": (105, 75, 78),
        "leather_edge": (150, 115, 115),
        # Metal buckles/plates (steel)
        "steel_dark": (25, 25, 30),
        "steel_mid": (75, 78, 88),
        "steel_light": (150, 155, 165),
        "steel_shine": (215, 220, 230),
        # HAIR (deep red)
        "hair_darkest": (45, 8, 10),
        "hair_dark": (95, 20, 22),
        "hair_mid": (170, 40, 40),
        "hair_light": (225, 75, 65),
        "hair_shine": (255, 140, 110),
        # BLOOD RED MAGIC (signature)
        "blood_darkest": (40, 3, 8),
        "blood_dark": (110, 10, 20),
        "blood_mid": (200, 30, 40),
        "blood_light": (255, 80, 90),
        "blood_hot": (255, 160, 160),
        "blood_shine": (255, 220, 220),
        # Blade steel
        "blade_dark": (60, 55, 65),
        "blade_mid": (145, 145, 160),
        "blade_light": (220, 220, 235),
        "blade_shine": (255, 255, 255),
        # Eye (red glow)
        "eye_socket": (10, 3, 5),
        "eye_dark": (100, 15, 20),
        "eye_mid": (220, 50, 55),
        "eye_light": (255, 130, 130),
        # Corset red inner
        "corset_dark": (55, 8, 15),
        "corset_mid": (120, 20, 30),
        "corset_light": (180, 55, 65),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaerissa._clamp(color)
        if _NS_kaerissa.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaerissa._clamp(color)
        if _NS_kaerissa.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaerissa._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaerissa(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_kaerissa._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_krs_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_kaerissa._draw_blood_aura(surface, x, y, pulse)
        _NS_kaerissa._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_kaerissa._draw_prepare_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaerissa._draw_deathlotus_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaerissa._draw_shunpo_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if active_skill == "e" and skill_timer > 25:
            # Shunpo: teleport/dash phase.
            _NS_kaerissa._draw_krs_shunpo_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_kaerissa._draw_krs_attack(surface, boss, x, y)
        else:
            _NS_kaerissa._draw_krs_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_kaerissa._draw_daggerthrow_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaerissa._draw_prepare_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaerissa._draw_shunpo_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaerissa._draw_deathlotus_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_krs_previous_timer", 0))
        active = bool(getattr(boss, "_krs_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._krs_attack_active = True
            boss._krs_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._krs_attack_frame = int(getattr(boss, "_krs_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._krs_attack_active = False
            boss._krs_attack_frame = 0
            active = False
        boss._krs_previous_timer = timer
        boss._krs_attack_progress = (
            min(1.0, getattr(boss, "_krs_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_krs_float(surface, boss, x, y):
        """Idle: floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_kaerissa._draw_shadow(surface, x, y + 52)
        _NS_kaerissa._draw_blood_wisps(surface, x, y + 25, boss.pulse)
        _NS_kaerissa._draw_krs_body(surface, x, y - 4 + hover,
                                    boss.direction, boss.pulse, "float", 0)
    def _draw_krs_attack(surface, boss, x, y):
        """Attack: DAGGER SLASH (melee swing)."""
        progress = getattr(boss, "_krs_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        lean = 0
        if progress < 0.35:
            t = progress / 0.35
            lean = -int(t * 3) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 9)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lean = int(6 * (1 - t)) * boss.direction
        _NS_kaerissa._draw_shadow(surface, x + lean, y + 52)
        _NS_kaerissa._draw_blood_wisps(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_kaerissa._draw_krs_body(surface, x + lean, y - 4 + hover,
                                    boss.direction, boss.pulse, "attack", progress)
        # Slash arc.
        _NS_kaerissa._draw_dagger_swing_arc(surface, boss, x + lean, y + hover, progress)
    def _draw_krs_shunpo_body(surface, boss, x, y, skill_timer, pulse):
        """During E skill: dash with afterimage trail."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.6) * 5)
        if progress < 0.25:
            # Wind-up flash at boss.
            t = progress / 0.25
            _NS_kaerissa._draw_shadow(surface, x, y + 52)
            _NS_kaerissa._draw_krs_body(surface, x, y - 4 + hover,
                                        boss.direction, pulse, "float", 0)
            # Charging blood glow.
            core_x = x
            core_y = y - 6 + hover
            pulse_mult = math.sin(pulse * 4) * 0.4 + 0.6
            for r in range(int(24 * t), 0, -2):
                alpha = _NS_kaerissa._alpha(150 * pulse_mult * (24 - r) / 24)
                if alpha > 0:
                    _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                           (core_x, core_y), r)
        elif progress < 0.65:
            # Dash phase — draw multiple afterimages.
            t = (progress - 0.25) / 0.40
            tx, ty = _NS_kaerissa._target_position(boss, x, y)
            dash_x = int(x + (tx - x) * t)
            dash_y = int(y + (ty - y) * t)
            # Afterimages (ghosts).
            for i in range(5):
                trail_t = max(0.0, t - i * 0.07)
                gx = int(x + (tx - x) * trail_t)
                gy = int(y + (ty - y) * trail_t)
                alpha_scale = (1.0 - i / 5) * 0.6
                ghost_surf = pygame.Surface((80, 100), pygame.SRCALPHA)
                _NS_kaerissa._draw_krs_body_to(ghost_surf, 40, 50 + hover,
                                               boss.direction, pulse, "float", 0,
                                               alpha_scale)
                surface.blit(ghost_surf, (gx - 40, gy - 50))
            # Current position - full body.
            _NS_kaerissa._draw_shadow(surface, dash_x, dash_y + 52)
            _NS_kaerissa._draw_krs_body(surface, dash_x, dash_y - 4 + hover,
                                        boss.direction, pulse, "attack", 0.55)
        else:
            # Arrival — strike pose at target.
            t = (progress - 0.65) / 0.35
            tx, ty = _NS_kaerissa._target_position(boss, x, y)
            _NS_kaerissa._draw_shadow(surface, tx, ty + 52)
            _NS_kaerissa._draw_krs_body(surface, tx, ty - 4 + hover,
                                        boss.direction, pulse, "attack", 0.6)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_krs_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_kaerissa._draw_krs_body_to(surface, cx, cy, facing, phase, action,
                                       attack_progress, 1.0)
    def _draw_krs_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Assassin body — leather armor, red hair, dual daggers."""
        # Hair flowing back (behind body).
        _NS_kaerissa._draw_flowing_red_hair(surface, cx, cy - 22, facing, phase, alpha_scale)
        # Legs (leather pants + boots).
        _NS_kaerissa._draw_krs_legs(surface, cx, cy + 8, facing, phase, alpha_scale)
        # Torso (corset + leather chest armor).
        _NS_kaerissa._draw_krs_torso(surface, cx, cy, facing, phase, alpha_scale)
        # Arms + daggers.
        _NS_kaerissa._draw_krs_arms(surface, cx, cy, facing, phase, action,
                                    attack_progress, alpha_scale)
        # Head + hair front + face.
        _NS_kaerissa._draw_krs_head(surface, cx, cy - 22, facing, phase, alpha_scale)
    def _draw_flowing_red_hair(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Long flowing red hair behind."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.8) * 3
        # Main hair volume.
        hair_pts = [
            (cx - 12, cy - 3),
            (cx - 15 + int(sway), cy + 3),
            (cx - 18 + int(sway), cy + 14),
            (cx - 15 + int(sway), cy + 26),
            (cx - 10 + int(sway * 1.3), cy + 34),
            (cx - 2, cy + 38),
            (cx + 8, cy + 32),
            (cx + 12, cy + 22),
            (cx + 13, cy + 8),
            (cx + 12, cy - 3),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"], hair_pts,
                                 alpha_base, offset=(2, 3))
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["hair_darkest"], hair_pts,
                                 alpha_base)
        # Mid tone.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["hair_dark"], [
            (cx - 10, cy - 2),
            (cx - 13 + int(sway), cy + 5),
            (cx - 15 + int(sway), cy + 15),
            (cx - 12 + int(sway), cy + 25),
            (cx - 4, cy + 32),
            (cx + 6, cy + 28),
            (cx + 10, cy + 18),
            (cx + 11, cy + 6),
            (cx + 10, cy - 2),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ], alpha_base)
        # Hair strands (streaked).
        for i in range(5):
            strand_x_off = -8 + i * 4
            strand_wave = math.sin(phase * 0.8 + i) * 2
            sx1 = cx + strand_x_off
            sy1 = cy - 3
            sx2 = cx + strand_x_off + int(strand_wave) - facing * 2
            sy2 = cy + 18
            sx3 = cx + strand_x_off + int(strand_wave * 2) - facing * 3
            sy3 = cy + 30
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["hair_mid"],
                                       (sx1, sy1), (sx2, sy2), 2, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["hair_light"],
                                       (sx2, sy2), (sx3, sy3), 1, alpha_base)
        # Top sheen highlight.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["hair_mid"], [
            (cx - 5, cy - 6), (cx + 5, cy - 6),
            (cx + 3, cy - 3), (cx - 3, cy - 3),
        ], alpha_base)
        pygame.draw.rect(surface, _NS_kaerissa.PALETTE["hair_shine"], (cx - 2, cy - 6, 2, 1))
        pygame.draw.rect(surface, _NS_kaerissa.PALETTE["hair_shine"], (cx + 1, cy - 5, 1, 1))
    def _draw_krs_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Head with red hair bangs + red glowing eyes + smirk."""
        alpha_base = int(255 * alpha_scale)
        # Head shape.
        head_pts = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 6, cy + 9),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 6, cy + 9),
            (cx + 7, cy + 4),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"], head_pts,
                                 alpha_base, offset=(2, 2))
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["skin_darkest"], head_pts,
                                 alpha_base)
        # Skin dark.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 5, cy + 8),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
        ], alpha_base)
        # Cheek highlight.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["skin_mid"], [
            (cx - 3, cy + 2), (cx + 3, cy + 2),
            (cx + 4, cy + 5), (cx + 2, cy + 8),
            (cx - 2, cy + 8), (cx - 4, cy + 5),
        ], alpha_base)
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["skin_light"], [
            (cx - 1, cy + 3), (cx + 1, cy + 3),
            (cx + 1, cy + 5), (cx - 1, cy + 5),
        ], alpha_base)
        # HAIR FRONT (bangs — red, side-swept).
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["hair_darkest"], [
            (cx - 6, cy - 3), (cx - 5, cy + 1),
            (cx + 5, cy + 1), (cx + 6, cy - 3),
            (cx + 3, cy - 3), (cx - 3, cy - 3),
        ], alpha_base)
        # Side-swept bang across forehead (asymmetric).
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["hair_dark"], [
            (cx - 5, cy - 2),
            (cx - 3, cy),
            (cx + 4, cy + 2),
            (cx + 5, cy),
            (cx + 3, cy - 2),
        ], alpha_base)
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["hair_mid"], [
            (cx - 3, cy),
            (cx + 2, cy + 1),
            (cx + 3, cy - 1),
            (cx, cy - 1),
        ], alpha_base)
        pygame.draw.rect(surface, _NS_kaerissa.PALETTE["hair_light"], (cx + 1, cy, 1, 1))
        # Long side lock hanging down.
        for i in range(3):
            sx = cx - 6 - i
            sy = cy + 3 + i * 2
            pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["hair_darkest"], alpha_base),
                             (sx, sy), (sx - 1, sy + 4), 2)
            pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["hair_dark"], alpha_base),
                             (sx, sy), (sx - 1, sy + 4), 1)
        # RED GLOWING EYES.
        _NS_kaerissa._draw_red_eyes(surface, cx, cy + 5, phase, alpha_scale)
        # Small nose.
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["skin_light"], alpha_base),
                         (cx, cy + 7, 1, 1))
        # SMIRK (small mouth with lipstick).
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha_base),
                         (cx - 1, cy + 9, 3, 1))
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha_base),
                         (cx, cy + 9, 2, 1))
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha_base),
                         (cx + 1, cy + 9, 1, 1))
    def _draw_red_eyes(surface, cx, cy, phase, alpha_scale=1.0):
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            for r in range(5, 0, -1):
                a = _NS_kaerissa._alpha(140 * (5 - r) / 5 * pulse * alpha_scale)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["eye_mid"], a),
                                       (ex, ey), r)
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["eye_mid"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["eye_light"], alpha_base),
                             (ex, ey, 1, 1))
    def _draw_krs_torso(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Corset + chest armor plate."""
        alpha_base = int(255 * alpha_scale)
        # Main torso shape (hourglass with narrow waist).
        torso_pts = [
            (cx - 9, cy - 9),
            (cx - 10, cy - 4),
            (cx - 7, cy),         # waist
            (cx - 6, cy + 4),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 6, cy + 4),
            (cx + 7, cy),
            (cx + 10, cy - 4),
            (cx + 9, cy - 9),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ]
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"], torso_pts,
                                 alpha_base, offset=(2, 2))
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["leather_darkest"], torso_pts,
                                 alpha_base)
        # Leather mid tone.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["leather_dark"], [
            (cx - 8, cy - 8),
            (cx - 9, cy - 4),
            (cx - 6, cy),
            (cx - 5, cy + 4),
            (cx - 7, cy + 8),
            (cx + 7, cy + 8),
            (cx + 5, cy + 4),
            (cx + 6, cy),
            (cx + 9, cy - 4),
            (cx + 8, cy - 8),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ], alpha_base)
        # Chest armor plate (top).
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["leather_mid"], [
            (cx - 6, cy - 8),
            (cx - 7, cy - 5),
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 7, cy - 5),
            (cx + 6, cy - 8),
        ], alpha_base)
        # Highlight.
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_light"], alpha_base),
                         (cx - 5, cy - 8), (cx + 5, cy - 8), 1)
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_edge"], alpha_base),
                         (cx - 4, cy - 8), (cx + 4, cy - 8), 1)
        # RED CORSET showing in décolletage V-shape.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["corset_dark"], [
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 2, cy - 6),
            (cx, cy - 3),
            (cx - 2, cy - 6),
        ], alpha_base)
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["corset_mid"], [
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx + 1, cy - 6),
            (cx, cy - 4),
            (cx - 1, cy - 6),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["corset_light"], alpha_base),
                         (cx, cy - 8, 1, 1))
        # Skin décolletage above corset.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["skin_dark"], [
            (cx - 4, cy - 11),
            (cx + 4, cy - 11),
            (cx + 3, cy - 10),
            (cx - 3, cy - 10),
        ], alpha_base)
        pygame.draw.rect(surface, _NS_kaerissa.PALETTE["skin_mid"], (cx - 2, cy - 11, 4, 1))
        pygame.draw.rect(surface, _NS_kaerissa.PALETTE["skin_light"], (cx - 1, cy - 11, 2, 1))
        # Buckle straps across waist (steel).
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_darkest"], alpha_base),
                         (cx - 6, cy + 2), (cx + 6, cy + 2), 2)
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_light"], alpha_base),
                         (cx - 6, cy + 2), (cx + 6, cy + 2), 1)
        # Belt buckle.
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_dark"], alpha_base),
                         (cx - 2, cy + 1, 4, 3))
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_mid"], alpha_base),
                         (cx - 1, cy + 1, 3, 2))
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_light"], alpha_base),
                         (cx - 1, cy + 1, 1, 1))
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_shine"], alpha_base),
                         (cx, cy + 1, 1, 1))
        # Cloth folds (vertical dark lines).
        for x_off in (-6, -3, 3, 6):
            pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_darkest"], alpha_base),
                             (cx + x_off, cy + 3), (cx + x_off, cy + 8), 1)
        # Side leather edges.
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_light"], alpha_base),
                         (cx - 9, cy - 4), (cx - 7, cy + 8), 1)
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["leather_edge"], alpha_base),
                         (cx + 9, cy - 4), (cx + 7, cy + 8), 1)
    def _draw_krs_arms(surface, cx, cy, facing, phase, action, attack_progress,
                       alpha_scale=1.0):
        """Two arms each holding a dagger."""
        alpha_base = int(255 * alpha_scale)
        # Both arms — one may swing forward in attack.
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 9
            base_y = cy - 5
            is_swing_arm = (side == facing)  # facing side arm does the swing
            # Determine arm angle.
            if action == "attack" and is_swing_arm:
                # Wind-up → slash → recover.
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    angle_deg = -30 - t * 70  # back over head
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    angle_deg = -100 + t * 180  # slash forward
                else:
                    t = (attack_progress - 0.6) / 0.4
                    angle_deg = 80 - t * 110
            elif action == "attack" and not is_swing_arm:
                # Off-hand pulled back slightly.
                if attack_progress < 0.6:
                    angle_deg = 40
                else:
                    angle_deg = 25
            else:
                # Idle: both arms at sides, dagger tips down/back.
                sway = math.sin(phase * 0.7 + side_i * 0.5) * 2
                angle_deg = 25 + sway
            angle_rad = math.radians(angle_deg)
            arm_len = 12
            hand_x = base_x + int(math.cos(angle_rad) * arm_len) * side
            hand_y = base_y + int(math.sin(angle_rad) * arm_len)
            elbow_x = base_x + int(math.cos(angle_rad + 0.3) * arm_len * 0.5) * side
            elbow_y = base_y + int(math.sin(angle_rad + 0.3) * arm_len * 0.5)
            # Upper arm (leather sleeve).
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                                       (base_x + 1, base_y + 1),
                                       (elbow_x + 1, elbow_y + 1), 4, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_darkest"],
                                       (base_x, base_y), (elbow_x, elbow_y), 3, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_dark"],
                                       (base_x, base_y), (elbow_x, elbow_y), 2, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_mid"],
                                       (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1,
                                       alpha_base)
            # Forearm (skin — bare arm below elbow).
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                                       (elbow_x + 1, elbow_y + 1),
                                       (hand_x + 1, hand_y + 1), 4, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["skin_darkest"],
                                       (elbow_x, elbow_y), (hand_x, hand_y), 3, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["skin_dark"],
                                       (elbow_x, elbow_y), (hand_x, hand_y), 2, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["skin_mid"],
                                       (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1,
                                       alpha_base)
            # Bracer/glove at wrist (leather).
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["leather_darkest"], alpha_base),
                             (hand_x - 2, hand_y - 1, 4, 3))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["leather_mid"], alpha_base),
                             (hand_x - 2, hand_y - 1, 4, 1))
            # DAGGER held in hand.
            _NS_kaerissa._draw_dagger(surface, hand_x, hand_y, angle_rad, side, phase,
                                      alpha_base, is_swinging=(action == "attack" and is_swing_arm))
    def _draw_dagger(surface, hx, hy, angle_rad, side, phase, alpha_base,
                     is_swinging=False):
        """Curved dagger with red edge glow."""
        # Blade direction extends from hand.
        # Dagger length ~14.
        blade_len = 14
        # Adjust angle to make dagger extend outward from hand.
        # Blade tip.
        tip_x = hx + int(math.cos(angle_rad) * blade_len) * side
        tip_y = hy + int(math.sin(angle_rad) * blade_len)
        # Blade sides (perpendicular).
        perp = angle_rad + math.pi / 2
        edge_off = 2
        # Blade base near hilt.
        base_a = (hx + int(math.cos(perp) * edge_off),
                  hy + int(math.sin(perp) * edge_off))
        base_b = (hx - int(math.cos(perp) * edge_off),
                  hy - int(math.sin(perp) * edge_off))
        # Slight curve — mid points offset toward one side.
        mid_x = hx + int(math.cos(angle_rad) * blade_len * 0.5) * side
        mid_y = hy + int(math.sin(angle_rad) * blade_len * 0.5)
        mid_a = (mid_x + int(math.cos(perp) * (edge_off - 1)),
                 mid_y + int(math.sin(perp) * (edge_off - 1)))
        mid_b = (mid_x - int(math.cos(perp) * (edge_off - 1)),
                 mid_y - int(math.sin(perp) * (edge_off - 1)))
        # Blade polygon (curved dagger shape).
        blade_pts = [tip_x, tip_y]
        blade_polygon = [
            (tip_x, tip_y),
            mid_a,
            base_a,
            base_b,
            mid_b,
        ]
        # Shadow.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                                 [(p[0] + 1, p[1] + 1) for p in blade_polygon],
                                 alpha_base)
        # Blade.
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["blade_dark"],
                                 blade_polygon, alpha_base)
        _NS_kaerissa._poly_alpha(surface, _NS_kaerissa.PALETTE["blade_mid"], [
            (tip_x, tip_y),
            (int((tip_x + mid_a[0]) / 2), int((tip_y + mid_a[1]) / 2)),
            (int((mid_a[0] + base_a[0]) / 2), int((mid_a[1] + base_a[1]) / 2)),
            (hx, hy),
            (int((mid_b[0] + base_b[0]) / 2), int((mid_b[1] + base_b[1]) / 2)),
            (int((tip_x + mid_b[0]) / 2), int((tip_y + mid_b[1]) / 2)),
        ], alpha_base)
        # Blade highlight (center strip).
        _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["blade_light"],
                                   (hx, hy), (tip_x, tip_y), 1, alpha_base)
        # Tip shine.
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blade_shine"], alpha_base),
                         (tip_x, tip_y, 1, 1))
        # RED EDGE glow along blade.
        # Blood-red line along cutting edge.
        edge_glow_a = (int((tip_x + mid_a[0]) / 2), int((tip_y + mid_a[1]) / 2))
        _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["blood_dark"],
                                   base_a, edge_glow_a, 1, alpha_base)
        _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["blood_mid"],
                                   base_a, edge_glow_a, 1, int(alpha_base * 0.7))
        # Red glow at tip.
        _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha_base),
                               (tip_x, tip_y), 2)
        _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha_base),
                               (tip_x, tip_y), 1)
        # Extra intense red aura when swinging.
        if is_swinging:
            for r in range(5, 0, -1):
                alpha = _NS_kaerissa._alpha(120 * (5 - r) / 5 * alpha_base / 255)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                       (tip_x, tip_y), r + 1)
        # HILT / GUARD.
        # Crossguard perpendicular to blade at hand.
        guard_a = (hx + int(math.cos(perp) * 3),
                   hy + int(math.sin(perp) * 3))
        guard_b = (hx - int(math.cos(perp) * 3),
                   hy - int(math.sin(perp) * 3))
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["steel_dark"], alpha_base),
                         guard_a, guard_b, 2)
        pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["steel_mid"], alpha_base),
                         guard_a, guard_b, 1)
        # Pommel (back).
        pommel_x = hx - int(math.cos(angle_rad) * 3) * side
        pommel_y = hy - int(math.sin(angle_rad) * 3)
        _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["steel_dark"], alpha_base),
                               (pommel_x, pommel_y), 2)
        _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha_base),
                               (pommel_x, pommel_y), 1)
        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha_base),
                         (pommel_x, pommel_y, 1, 1))
    def _draw_krs_legs(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Slim legs with leather pants + boots."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.8) * 2
        for side in (-1, 1):
            hip_x = cx + side * 4
            hip_y = cy
            knee_x = cx + side * 5 + int(sway * 0.5)
            knee_y = cy + 12
            foot_x = cx + side * 3 + int(sway)
            foot_y = cy + 22
            # Thigh + shin (leather pants).
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                                       (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1),
                                       5, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_darkest"],
                                       (hip_x, hip_y), (knee_x, knee_y), 4, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_dark"],
                                       (hip_x, hip_y), (knee_x, knee_y), 3, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_mid"],
                                       (hip_x, hip_y - 1), (knee_x, knee_y - 1), 1,
                                       alpha_base)
            # Boot.
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                                       (knee_x + 1, knee_y + 1), (foot_x + 1, foot_y + 1),
                                       5, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_darkest"],
                                       (knee_x, knee_y), (foot_x, foot_y), 4, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_dark"],
                                       (knee_x, knee_y), (foot_x, foot_y), 3, alpha_base)
            _NS_kaerissa._aaline_alpha(surface, _NS_kaerissa.PALETTE["leather_light"],
                                       (knee_x - side, knee_y), (foot_x - side, foot_y), 1,
                                       alpha_base)
            # Buckle straps on boot.
            for buckle_y in (14, 18):
                by = cy + buckle_y
                pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["steel_dark"], alpha_base),
                                 (cx + side * 3, by), (cx + side * 6, by), 1)
                pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_mid"], alpha_base),
                                 (cx + side * 4, by, 1, 1))
            # Knee pad (small armor).
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_dark"], alpha_base),
                             (knee_x - 2, knee_y - 1, 4, 2))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_mid"], alpha_base),
                             (knee_x - 2, knee_y - 1, 4, 1))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["steel_light"], alpha_base),
                             (knee_x - 1, knee_y - 1, 1, 1))
    # ============================================================
    # DAGGER SWING ARC (melee attack visual)
    # ============================================================
    def _draw_dagger_swing_arc(surface, boss, x, y, progress):
        """Red arc trail when dagger swings."""
        if not (0.4 <= progress <= 0.7):
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.3
        cx = x
        cy = y - 6
        radius = 26
        # Arc sweeps from -100° to +80°.
        start_angle = -100 + t * 180 - 30
        end_angle = -100 + t * 180 + 10
        num_pts = 12
        pts = []
        for i in range(num_pts):
            a_deg = start_angle + (end_angle - start_angle) * i / (num_pts - 1)
            a_rad = math.radians(a_deg)
            px = cx + int(math.cos(a_rad) * radius) * facing
            py = cy + int(math.sin(a_rad) * radius)
            pts.append((px, py))
        arc_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        for i in range(len(pts) - 1):
            alpha = _NS_kaerissa._alpha(200 * (i / len(pts)))
            p1 = (pts[i][0] - cx + 50, pts[i][1] - cy + 50)
            p2 = (pts[i + 1][0] - cx + 50, pts[i + 1][1] - cy + 50)
            pygame.draw.line(arc_surf, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                             p1, p2, 4)
            pygame.draw.line(arc_surf, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                             p1, p2, 3)
            pygame.draw.line(arc_surf, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                             p1, p2, 2)
            pygame.draw.line(arc_surf, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                             p1, p2, 1)
        surface.blit(arc_surf, (cx - 50, cy - 50))
        # Sparks along arc.
        for i in range(5):
            sp_t = (t * 3 + i * 0.18) % 1.0
            idx = int(sp_t * (num_pts - 1))
            sp = pts[idx]
            spx = sp[0] + int(math.sin(t * 6 + i) * 3)
            spy = sp[1] + int(math.cos(t * 6 + i) * 3)
            alpha = _NS_kaerissa._alpha(230)
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha), (spx, spy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_shine"], alpha), (spx, spy, 1, 1))
    # ============================================================
    # HELPERS
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_kaerissa._poly(surface, color, points)
            return
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_kaerissa._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_kaerissa._aaline(surface, color, start, end, width)
            return
        c = _NS_kaerissa._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
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
        pygame.draw.ellipse(shadow, (8, 2, 3, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (100, 15, 20, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_blood_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_kaerissa._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kaerissa._aacircle(aura, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_kaerissa._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaerissa._aacircle(aura, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kaerissa._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaerissa._aacircle(aura, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_kaerissa.PALETTE["blood_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaerissa.PALETTE["blood_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaerissa.PALETTE["blood_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_kaerissa.PALETTE["blood_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_kaerissa.PALETTE["blood_mid"], 230),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_kaerissa.PALETTE["blood_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaerissa.PALETTE["blood_hot"],
                                       _NS_kaerissa._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_blood_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_kaerissa._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_kaerissa._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising blood embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_kaerissa._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                   (sx, sy), 3)
            _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                             (sx, sy - 2, 1, 1))
    # ============================================================
    # SKILL: Q - DAGGER THROW (ranged projectile)
    # ============================================================
    def _draw_daggerthrow_skill(surface, boss, x, y, timer, phase):
        """Dagger projectile spinning to target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaerissa._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.2:
            # Wind-up glow on hand.
            t = progress / 0.2
            hand_x = x + facing * 16
            hand_y = y - 4 + hover
            cr = int(3 + t * 5)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kaerissa._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                       (hand_x, hand_y), r)
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_mid"], (hand_x, hand_y),
                                   max(1, cr - 2))
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_light"], (hand_x, hand_y),
                                   max(1, cr - 4))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 20
            start_y = y - 4 + hover
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Red trail.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kaerissa._alpha(230 - i * 22)
                size = max(1, 6 - i)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                       (px, py), size)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                       (px, py), max(1, size - 3))
                if i < 4:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                        pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Spinning dagger head.
            spin_angle = phase * 8 + t * 20  # rapid spin
            angle_to_target = math.atan2(ty - start_y, tx - start_x)
            # Draw dagger as elongated shape.
            blade_len = 12
            tip = (bx + int(math.cos(spin_angle) * blade_len),
                   by + int(math.sin(spin_angle) * blade_len))
            back = (bx - int(math.cos(spin_angle) * 4),
                    by - int(math.sin(spin_angle) * 4))
            perp = spin_angle + math.pi / 2
            side_a = (bx + int(math.cos(perp) * 2),
                      by + int(math.sin(perp) * 2))
            side_b = (bx - int(math.cos(perp) * 2),
                      by - int(math.sin(perp) * 2))
            _NS_kaerissa._poly(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                               [(tip[0] + 1, tip[1] + 1),
                                (side_a[0] + 1, side_a[1] + 1),
                                (back[0] + 1, back[1] + 1),
                                (side_b[0] + 1, side_b[1] + 1)])
            _NS_kaerissa._poly(surface, _NS_kaerissa.PALETTE["blade_dark"],
                               [tip, side_a, back, side_b])
            _NS_kaerissa._poly(surface, _NS_kaerissa.PALETTE["blade_mid"],
                               [tip,
                                (int((tip[0] + side_a[0]) / 2), int((tip[1] + side_a[1]) / 2)),
                                (bx, by),
                                (int((tip[0] + side_b[0]) / 2), int((tip[1] + side_b[1]) / 2))])
            _NS_kaerissa._aaline(surface, _NS_kaerissa.PALETTE["blade_light"],
                                 (bx, by), tip, 1)
            pygame.draw.rect(surface, _NS_kaerissa.PALETTE["blade_shine"], (tip[0], tip[1], 1, 1))
            # Red glow at tip.
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_light"], tip, 2)
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_hot"], tip, 1)
            # Radial glow around dagger.
            for r in range(8, 3, -1):
                alpha = _NS_kaerissa._alpha(80 * (8 - r) / 8)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (bx, by), r)
            # Impact — dagger sticks and burst.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(8 + st * 22)
                alpha = _NS_kaerissa._alpha(240 * (1 - st))
                # Dagger stuck (final position).
                _NS_kaerissa._poly(surface,
                                   (*_NS_kaerissa.PALETTE["blade_dark"], alpha),
                                   [tip, side_a, back, side_b])
                # Burst rings.
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                       (tx, ty), radius + 3, 3)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 2)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                       (tx, ty), max(1, radius - 12), 1)
                # Radiating red sparks.
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                     (tx, ty), (ex, ey), 1)
                    pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: W - PREPARE (buff aura rings)
    # ============================================================
    def _draw_prepare_ground(surface, boss, x, y, timer, phase):
        """Red rune circles under boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(30 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_kaerissa._alpha(200 - i * 45)
            _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                   (x, y + 42), r, 2)
            _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                   (x, y + 42), r, 1)
    def _draw_prepare_foreground(surface, boss, x, y, timer, phase):
        """Rotating red rings + rising red energy around boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.6) * 5)
        core_y = y - 4 + hover
        # 3 rotating rings at different angles/speeds.
        for ring_i in range(3):
            ring_r = 30 - ring_i * 5
            speed = 1.5 + ring_i * 0.5
            tilt = ring_i * math.pi / 6  # tilt for depth
            # Draw ring as ellipse rotated.
            ring_surf = pygame.Surface((ring_r * 2 + 6, ring_r * 2 + 6), pygame.SRCALPHA)
            center = (ring_r + 3, ring_r + 3)
            # Ring color layers.
            for lw, alpha_val in [(2, 100 + ring_i * 30), (1, 200)]:
                pygame.draw.ellipse(ring_surf, (*_NS_kaerissa.PALETTE["blood_mid"], alpha_val),
                                    (0, ring_r - int(ring_r * 0.35) + 3,
                                     ring_r * 2, int(ring_r * 0.7)), lw)
                pygame.draw.ellipse(ring_surf, (*_NS_kaerissa.PALETTE["blood_light"], alpha_val),
                                    (2, ring_r - int(ring_r * 0.3) + 3,
                                     ring_r * 2 - 4, int(ring_r * 0.6)), 1)
            # Sparkles along ring.
            for k in range(8):
                spark_angle = phase * speed + k * math.pi / 4 + tilt
                sx = center[0] + int(math.cos(spark_angle) * ring_r)
                sy = center[1] + int(math.sin(spark_angle) * ring_r * 0.35)
                pygame.draw.rect(ring_surf, _NS_kaerissa.PALETTE["blood_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(ring_surf, _NS_kaerissa.PALETTE["blood_shine"], (sx, sy, 1, 1))
            surface.blit(ring_surf, (x - ring_r - 3, core_y - int(ring_r * 0.35) - 3))
        # Rising energy motes.
        for i in range(10):
            angle = phase * 1 + i * math.pi / 5
            radius = 25 + int((i % 3) * 5)
            sx = x + int(math.cos(angle) * radius)
            sy_base = core_y + int(math.sin(angle) * radius * 0.3)
            rise = int((phase * 0.5 + i * 0.1) % 1.0 * 20)
            sy = sy_base - rise
            alpha = _NS_kaerissa._alpha(220 * (1 - rise / 20))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: E - SHUNPO (blink dash)
    # ============================================================
    def _draw_shunpo_ground(surface, boss, x, y, timer, phase):
        """Red flash markers at start & target."""
        tx, ty = _NS_kaerissa._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Start ring (fades).
        if progress < 0.4:
            fade = 1.0 - progress / 0.4
            for i in range(2):
                r = int(28 + i * 5)
                alpha = _NS_kaerissa._alpha(200 * fade - i * 50)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (x, y + 42), r, 2)
        # Target ring (grows).
        if progress > 0.3:
            grow = min(1.0, (progress - 0.3) / 0.4)
            for i in range(3):
                r = int((25 + i * 5) * grow)
                alpha = _NS_kaerissa._alpha(220 - i * 55)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                       (tx, ty + 20), r, 2)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                       (tx, ty + 20), max(1, r - 3), 1)
    def _draw_shunpo_foreground(surface, boss, x, y, timer, phase):
        """Blink dash trail + arrival explosion."""
        tx, ty = _NS_kaerissa._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.65:
            # Trail streak.
            t = min(1.0, progress / 0.65)
            # Multiple red streaks between start & target.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.05)
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t)
                alpha = _NS_kaerissa._alpha(240 - i * 40)
                for r in range(4, 0, -1):
                    _NS_kaerissa._aacircle(surface,
                                           (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                           (px, py), r)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (px, py), 2)
                pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                                 (px, py, 1, 1))
        else:
            # Arrival explosion at target.
            t = (progress - 0.65) / 0.35
            intensity = math.sin(t * math.pi)
            radius = int(8 + t * 25)
            alpha = _NS_kaerissa._alpha(240 * intensity)
            # Radial red spikes (dagger burst).
            for i in range(12):
                angle = i * math.pi / 6 + t
                sp_x = tx + int(math.cos(angle) * radius)
                sp_y = ty + int(math.sin(angle) * radius)
                sp_start_x = tx + int(math.cos(angle) * 3)
                sp_start_y = ty + int(math.sin(angle) * 3)
                perp = angle + math.pi / 2
                w = 2
                pa = (sp_start_x + int(math.cos(perp) * w),
                      sp_start_y + int(math.sin(perp) * w))
                pb = (sp_start_x - int(math.cos(perp) * w),
                      sp_start_y - int(math.sin(perp) * w))
                pygame.draw.polygon(surface, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                    [(sp_x, sp_y), pa, pb])
                pygame.draw.polygon(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                    [(sp_x, sp_y),
                                     (int((sp_x + pa[0]) / 2), int((sp_y + pa[1]) / 2)),
                                     (tx, ty),
                                     (int((sp_x + pb[0]) / 2), int((sp_y + pb[1]) / 2))])
                pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                 (tx, ty), (sp_x, sp_y), 1)
                pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_shine"], alpha),
                                 (sp_x, sp_y, 2, 2))
            # Central glow.
            for r in range(int(intensity * 15), 0, -2):
                alpha2 = _NS_kaerissa._alpha(150 * intensity * (20 - r) / 20)
                if alpha2 > 0:
                    _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha2),
                                           (tx, ty), r)
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_shine"], (tx, ty), 3)
            pygame.draw.rect(surface, _NS_kaerissa.PALETTE["white"], (tx, ty, 1, 1))
    # ============================================================
    # SKILL: R - DEATH LOTUS (spinning dagger whirl)
    # ============================================================
    def _draw_deathlotus_ground(surface, boss, x, y, timer, phase):
        """Whirling red vortex on ground."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Concentric ellipses (like vortex from ref image).
        for i in range(4):
            r = int(40 + i * 12 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_kaerissa._alpha(220 - i * 45)
            _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_darkest"], alpha),
                                   (x, y + 44), r, 2)
            _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                   (x, y + 44), r, 1)
        # Spiral curves inside vortex.
        for arm_i in range(3):
            arm_offset = arm_i * (math.pi * 2 / 3)
            for k in range(20):
                t = k / 20
                spiral_r = 15 + t * 45
                spiral_angle = phase * 3 + arm_offset + t * 6
                sx = x + int(math.cos(spiral_angle) * spiral_r)
                sy = y + 44 + int(math.sin(spiral_angle) * spiral_r * 0.4)
                alpha = _NS_kaerissa._alpha(220 * (1 - t))
                pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                                 (sx, sy, 1, 1))
    def _draw_deathlotus_foreground(surface, boss, x, y, timer, phase):
        """Rotating daggers orbiting boss + red vortex."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.6) * 5)
        core_y = y - 4 + hover
        # Rotating orbit rings (like vortex encircling boss).
        for ring_i in range(3):
            ring_r = 40 - ring_i * 8
            speed = 3 + ring_i * 0.5
            ring_alpha = 180
            # Draw partial arc ellipses at multiple angles.
            for i in range(12):
                arc_angle_start = phase * speed + i * math.pi / 6
                arc_x = x + int(math.cos(arc_angle_start) * ring_r)
                arc_y = core_y + int(math.sin(arc_angle_start) * ring_r * 0.5)
                next_angle = phase * speed + (i + 1) * math.pi / 6
                arc_x2 = x + int(math.cos(next_angle) * ring_r)
                arc_y2 = core_y + int(math.sin(next_angle) * ring_r * 0.5)
                alpha = _NS_kaerissa._alpha(ring_alpha)
                pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["blood_dark"], alpha),
                                 (arc_x, arc_y), (arc_x2, arc_y2), 2)
                pygame.draw.line(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                 (arc_x, arc_y), (arc_x2, arc_y2), 1)
                if i % 2 == 0:
                    pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_light"], alpha),
                                     (arc_x, arc_y, 1, 1))
        # Spinning daggers around boss.
        num_daggers = 6
        for i in range(num_daggers):
            dag_angle = phase * 4 + i * (math.pi * 2 / num_daggers)
            dag_r = 45
            dx = x + int(math.cos(dag_angle) * dag_r)
            dy = core_y + int(math.sin(dag_angle) * dag_r * 0.55)
            # Dagger points outward (tangent direction).
            tangent = dag_angle + math.pi / 2
            blade_len = 10
            tip_x = dx + int(math.cos(tangent) * blade_len)
            tip_y = dy + int(math.sin(tangent) * blade_len)
            back_x = dx - int(math.cos(tangent) * 3)
            back_y = dy - int(math.sin(tangent) * 3)
            perp = tangent + math.pi / 2
            side_a = (dx + int(math.cos(perp) * 2), dy + int(math.sin(perp) * 2))
            side_b = (dx - int(math.cos(perp) * 2), dy - int(math.sin(perp) * 2))
            # Depth cue - back daggers smaller/darker.
            is_behind = math.sin(dag_angle) < 0
            base_color = _NS_kaerissa.PALETTE["blade_dark"] if is_behind \
                else _NS_kaerissa.PALETTE["blade_mid"]
            _NS_kaerissa._poly(surface, _NS_kaerissa.PALETTE["shadow_deep"],
                               [(tip_x + 1, tip_y + 1),
                                (side_a[0] + 1, side_a[1] + 1),
                                (back_x + 1, back_y + 1),
                                (side_b[0] + 1, side_b[1] + 1)])
            _NS_kaerissa._poly(surface, _NS_kaerissa.PALETTE["blade_dark"],
                               [(tip_x, tip_y), side_a, (back_x, back_y), side_b])
            _NS_kaerissa._poly(surface, base_color,
                               [(tip_x, tip_y),
                                (int((tip_x + side_a[0]) / 2),
                                 int((tip_y + side_a[1]) / 2)),
                                (dx, dy),
                                (int((tip_x + side_b[0]) / 2),
                                 int((tip_y + side_b[1]) / 2))])
            _NS_kaerissa._aaline(surface, _NS_kaerissa.PALETTE["blade_light"],
                                 (dx, dy), (tip_x, tip_y), 1)
            # Red glow on tip.
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_light"], (tip_x, tip_y), 2)
            _NS_kaerissa._aacircle(surface, _NS_kaerissa.PALETTE["blood_hot"], (tip_x, tip_y), 1)
            # Motion blur trail behind each dagger.
            for k in range(3):
                trail_angle = dag_angle - k * 0.15
                tx_pos = x + int(math.cos(trail_angle) * dag_r)
                ty_pos = core_y + int(math.sin(trail_angle) * dag_r * 0.55)
                alpha = _NS_kaerissa._alpha(150 - k * 40)
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (tx_pos, ty_pos), 3)
        # Additional radial sparks bursting outward.
        for i in range(20):
            spark_angle = phase * 2 + i * math.pi / 10
            sp_r = 50 + int(math.sin(phase * 3 + i) * 10)
            sx = x + int(math.cos(spark_angle) * sp_r)
            sy = core_y + int(math.sin(spark_angle) * sp_r * 0.55)
            alpha = _NS_kaerissa._alpha(200)
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaerissa.PALETTE["blood_shine"], alpha),
                             (sx, sy, 1, 1))
        # Central red glow (boss empowered).
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(20, 0, -2):
            alpha = _NS_kaerissa._alpha(120 * pulse * (20 - r) / 20)
            if alpha > 0:
                _NS_kaerissa._aacircle(surface, (*_NS_kaerissa.PALETTE["blood_mid"], alpha),
                                       (x, core_y), r)



# ====================================================================
# THORGARUK (SKYHORN) - Mini Boss
# ====================================================================

class _NS_thorgaruk:
    """Namespace thorgaruk - minotaur mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Fur / hide (brown-tan)
        "fur_darkest": (18, 10, 5),
        "fur_dark": (55, 32, 15),
        "fur_mid": (105, 68, 32),
        "fur_light": (160, 115, 65),
        "fur_edge": (210, 165, 105),
        "fur_shine": (240, 210, 155),
        # Skin/nose (pinkish-brown)
        "skin_dark": (65, 40, 30),
        "skin_mid": (120, 80, 65),
        "skin_light": (180, 130, 105),
        # Horn (bone/ivory - cream)
        "horn_darkest": (35, 25, 15),
        "horn_dark": (95, 75, 45),
        "horn_mid": (170, 145, 100),
        "horn_light": (225, 205, 160),
        "horn_shine": (250, 240, 210),
        # Armor (dark steel with blue tint)
        "armor_darkest": (5, 8, 18),
        "armor_dark": (22, 30, 50),
        "armor_mid": (55, 75, 110),
        "armor_light": (110, 140, 180),
        "armor_edge": (170, 200, 225),
        "armor_shine": (220, 240, 250),
        # Gold trim
        "gold_dark": (55, 40, 12),
        "gold_mid": (165, 125, 40),
        "gold_light": (240, 210, 120),
        # CYAN ARCANE (signature - runes, gems, axe glow, eyes)
        "arcane_darkest": (3, 25, 55),
        "arcane_dark": (15, 70, 150),
        "arcane_mid": (55, 150, 235),
        "arcane_light": (140, 215, 255),
        "arcane_hot": (200, 240, 255),
        "arcane_shine": (245, 252, 255),
        # Blade (axe head - blue steel)
        "blade_darkest": (10, 25, 55),
        "blade_dark": (35, 65, 110),
        "blade_mid": (95, 145, 200),
        "blade_light": (170, 210, 245),
        "blade_shine": (230, 245, 255),
        # Eye (bright cyan)
        "eye_socket": (0, 5, 15),
        "eye_dark": (5, 40, 100),
        "eye_mid": (80, 190, 255),
        "eye_light": (210, 245, 255),
        # Ground rune / ambient
        "rune_dark": (10, 30, 65),
        "rune_mid": (60, 130, 210),
        "rune_light": (150, 220, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thorgaruk._clamp(color)
        if _NS_thorgaruk.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_thorgaruk._clamp(color)
        if _NS_thorgaruk.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_thorgaruk._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thorgaruk(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_thorgaruk._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_thg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_thorgaruk._draw_arcane_aura(surface, x, y, pulse)
        _NS_thorgaruk._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_thorgaruk._draw_empower_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorgaruk._draw_polarity_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorgaruk._draw_skewer_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — special handling for E (dash).
        if active_skill == "e" and skill_timer > 15:
            _NS_thorgaruk._draw_thg_skewer_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_thorgaruk._draw_thg_attack(surface, boss, x, y)
        else:
            _NS_thorgaruk._draw_thg_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_thorgaruk._draw_shockwave_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thorgaruk._draw_empower_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorgaruk._draw_skewer_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorgaruk._draw_polarity_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_thg_previous_timer", 0))
        active = bool(getattr(boss, "_thg_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._thg_attack_active = True
            boss._thg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._thg_attack_frame = int(getattr(boss, "_thg_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._thg_attack_active = False
            boss._thg_attack_frame = 0
            active = False
        boss._thg_previous_timer = timer
        boss._thg_attack_progress = (
            min(1.0, getattr(boss, "_thg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_thg_float(surface, boss, x, y):
        """Idle: floating with hover bob."""
        hover = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_thorgaruk._draw_shadow(surface, x, y + 54)
        _NS_thorgaruk._draw_arcane_sparks(surface, x, y + 25, boss.pulse)
        _NS_thorgaruk._draw_thg_body(surface, x, y - 4 + hover,
                                     boss.direction, boss.pulse, "float", 0)
    def _draw_thg_attack(surface, boss, x, y):
        """Attack: MASSIVE AXE SWING melee."""
        progress = getattr(boss, "_thg_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.5) * 5)
        lean = 0
        if progress < 0.4:
            t = progress / 0.4
            lean = -int(t * 5) * boss.direction  # heavy wind-up
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lean = int((-5 + t * 12)) * boss.direction  # forward slam
        else:
            t = (progress - 0.65) / 0.35
            lean = int(7 * (1 - t)) * boss.direction
        _NS_thorgaruk._draw_shadow(surface, x + lean, y + 54)
        _NS_thorgaruk._draw_arcane_sparks(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_thorgaruk._draw_thg_body(surface, x + lean, y - 4 + hover,
                                     boss.direction, boss.pulse, "attack", progress)
        # Axe swing arc + slam impact.
        _NS_thorgaruk._draw_axe_swing_arc(surface, boss, x + lean, y + hover, progress)
    def _draw_thg_skewer_body(surface, boss, x, y, skill_timer, pulse):
        """During E skill: charge dash with axe extended."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.5) * 5)
        if progress < 0.25:
            # Wind-up.
            t = progress / 0.25
            lean = -int(t * 4) * boss.direction
            _NS_thorgaruk._draw_shadow(surface, x + lean, y + 54)
            _NS_thorgaruk._draw_thg_body(surface, x + lean, y - 4 + hover,
                                         boss.direction, pulse, "float", 0)
            # Charging cyan glow around body.
            core_x = x
            core_y = y - 6 + hover
            pm = math.sin(pulse * 4) * 0.4 + 0.6
            for r in range(int(30 * t), 0, -2):
                alpha = _NS_thorgaruk._alpha(160 * pm * (30 - r) / 30)
                if alpha > 0:
                    _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                            (core_x, core_y), r)
        elif progress < 0.75:
            # DASH phase — draw multiple afterimages.
            t = (progress - 0.25) / 0.50
            tx, ty = _NS_thorgaruk._target_position(boss, x, y)
            dash_x = int(x + (tx - x) * t)
            dash_y = int(y + (ty - y) * t)
            # Afterimages.
            for i in range(5):
                trail_t = max(0.0, t - i * 0.07)
                gx = int(x + (tx - x) * trail_t)
                gy = int(y + (ty - y) * trail_t)
                alpha_scale = (1.0 - i / 5) * 0.55
                ghost_surf = pygame.Surface((110, 140), pygame.SRCALPHA)
                _NS_thorgaruk._draw_thg_body_to(ghost_surf, 55, 70 + hover,
                                                boss.direction, pulse, "float", 0,
                                                alpha_scale)
                surface.blit(ghost_surf, (gx - 55, gy - 70))
            # Current position.
            _NS_thorgaruk._draw_shadow(surface, dash_x, dash_y + 54)
            _NS_thorgaruk._draw_thg_body(surface, dash_x, dash_y - 4 + hover,
                                         boss.direction, pulse, "attack", 0.55)
        else:
            # Arrival - impact pose.
            t = (progress - 0.75) / 0.25
            tx, ty = _NS_thorgaruk._target_position(boss, x, y)
            _NS_thorgaruk._draw_shadow(surface, tx, ty + 54)
            _NS_thorgaruk._draw_thg_body(surface, tx, ty - 4 + hover,
                                         boss.direction, pulse, "attack", 0.7)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_thg_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_thorgaruk._draw_thg_body_to(surface, cx, cy, facing, phase, action,
                                        attack_progress, 1.0)
    def _draw_thg_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Minotaur body — hide, armor, big horns, giant axe."""
        # Legs / lower fur (short, sturdy).
        _NS_thorgaruk._draw_thg_legs(surface, cx, cy + 12, facing, phase, alpha_scale)
        # Torso (bulk furry with armor).
        _NS_thorgaruk._draw_thg_torso(surface, cx, cy, facing, phase, alpha_scale)
        # Shoulder armor & pauldrons.
        _NS_thorgaruk._draw_thg_pauldrons(surface, cx, cy - 6, facing, phase, alpha_scale)
        # Arms + axe.
        _NS_thorgaruk._draw_thg_arms(surface, cx, cy, facing, phase, action,
                                     attack_progress, alpha_scale)
        # Head with helmet + horns + face.
        _NS_thorgaruk._draw_thg_head(surface, cx, cy - 22, facing, phase, alpha_scale)
    def _draw_thg_legs(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Thick furry legs with hooves."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.6) * 1
        for side in (-1, 1):
            hip_x = cx + side * 5
            hip_y = cy
            knee_x = cx + side * 6 + int(sway * 0.5)
            knee_y = cy + 10
            hoof_x = cx + side * 5 + int(sway)
            hoof_y = cy + 20
            # Thigh (fur).
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                        (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1),
                                        8, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_darkest"],
                                        (hip_x, hip_y), (knee_x, knee_y), 7, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_dark"],
                                        (hip_x, hip_y), (knee_x, knee_y), 6, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_mid"],
                                        (hip_x, hip_y), (knee_x, knee_y), 4, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_light"],
                                        (hip_x - side, hip_y - 1), (knee_x - side, knee_y - 1),
                                        1, alpha_base)
            # Fur tufts.
            for tuft_y in (2, 5, 8):
                ty = cy + tuft_y
                tx = cx + side * 6
                pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["fur_darkest"], alpha_base),
                                 (tx - side * 2, ty), (tx + side * 3, ty + 1), 1)
                pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["fur_dark"], alpha_base),
                                 (tx - side * 1, ty), (tx + side * 2, ty + 1), 1)
            # Shin (fur - narrow).
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                        (knee_x + 1, knee_y + 1), (hoof_x + 1, hoof_y + 1),
                                        6, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_darkest"],
                                        (knee_x, knee_y), (hoof_x, hoof_y), 5, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_dark"],
                                        (knee_x, knee_y), (hoof_x, hoof_y), 4, alpha_base)
            _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_mid"],
                                        (knee_x, knee_y - 1), (hoof_x, hoof_y - 1), 2, alpha_base)
            # HOOF (black/dark plate).
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], [
                (hoof_x - 4 + 1, hoof_y + 1),
                (hoof_x + 4 + 1, hoof_y + 1),
                (hoof_x + 4 + 1, hoof_y + 5 + 1),
                (hoof_x - 4 + 1, hoof_y + 5 + 1),
            ], alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["horn_darkest"], [
                (hoof_x - 4, hoof_y),
                (hoof_x + 4, hoof_y),
                (hoof_x + 4, hoof_y + 5),
                (hoof_x - 4, hoof_y + 5),
            ], alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["horn_dark"], [
                (hoof_x - 4, hoof_y + 1),
                (hoof_x + 4, hoof_y + 1),
                (hoof_x + 3, hoof_y + 4),
                (hoof_x - 3, hoof_y + 4),
            ], alpha_base)
            # Hoof split line.
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["shadow_deep"], alpha_base),
                             (hoof_x, hoof_y + 1), (hoof_x, hoof_y + 4), 1)
            # Highlight.
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["horn_mid"], alpha_base),
                             (hoof_x - 3, hoof_y + 1, 2, 1))
            # Metal ankle band (with cyan gem).
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_darkest"], alpha_base),
                             (hoof_x - 4, hoof_y - 2, 8, 3))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_dark"], alpha_base),
                             (hoof_x - 4, hoof_y - 2, 8, 2))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_mid"], alpha_base),
                             (hoof_x - 3, hoof_y - 2, 6, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha_base),
                             (hoof_x - 1, hoof_y - 1, 2, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                             (hoof_x, hoof_y - 1, 1, 1))
    def _draw_thg_torso(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Bulk furry torso with armor plates."""
        alpha_base = int(255 * alpha_scale)
        # Torso shape (wide, muscular).
        torso_pts = [
            (cx - 16, cy - 10),
            (cx - 19, cy - 4),
            (cx - 17, cy + 4),
            (cx - 15, cy + 12),
            (cx + 15, cy + 12),
            (cx + 17, cy + 4),
            (cx + 19, cy - 4),
            (cx + 16, cy - 10),
            (cx + 9, cy - 13),
            (cx - 9, cy - 13),
        ]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], torso_pts,
                                  alpha_base, offset=(3, 3))
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_darkest"], torso_pts,
                                  alpha_base)
        # Torso fur mid.
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_dark"], [
            (cx - 15, cy - 9),
            (cx - 17, cy - 3),
            (cx - 15, cy + 4),
            (cx - 13, cy + 11),
            (cx + 13, cy + 11),
            (cx + 15, cy + 4),
            (cx + 17, cy - 3),
            (cx + 15, cy - 9),
            (cx + 8, cy - 12),
            (cx - 8, cy - 12),
        ], alpha_base)
        # Center chest (fur highlight).
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_mid"], [
            (cx - 10, cy - 8),
            (cx - 12, cy - 2),
            (cx - 10, cy + 5),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 10, cy + 5),
            (cx + 12, cy - 2),
            (cx + 10, cy - 8),
        ], alpha_base)
        # CHEST ARMOR PLATE (dark blue with cyan gem).
        armor_pts = [
            (cx - 8, cy - 6),
            (cx - 10, cy - 1),
            (cx - 8, cy + 5),
            (cx + 8, cy + 5),
            (cx + 10, cy - 1),
            (cx + 8, cy - 6),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], armor_pts,
                                  alpha_base, offset=(1, 1))
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_darkest"], armor_pts,
                                  alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_dark"], [
            (cx - 7, cy - 5),
            (cx - 9, cy - 1),
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 9, cy - 1),
            (cx + 7, cy - 5),
            (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_mid"], [
            (cx - 6, cy - 3),
            (cx - 7, cy + 1),
            (cx - 5, cy + 3),
            (cx + 5, cy + 3),
            (cx + 7, cy + 1),
            (cx + 6, cy - 3),
        ], alpha_base)
        # Highlight edge.
        pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["armor_light"], alpha_base),
                         (cx - 4, cy - 7), (cx + 4, cy - 7), 1)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_shine"], alpha_base),
                         (cx - 2, cy - 7, 4, 1))
        # Gold trim edges.
        pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["gold_mid"], alpha_base),
                         (cx - 8, cy - 6), (cx - 10, cy - 1), 1)
        pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["gold_mid"], alpha_base),
                         (cx + 8, cy - 6), (cx + 10, cy - 1), 1)
        pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["gold_light"], alpha_base),
                         (cx - 5, cy - 8), (cx + 5, cy - 8), 1)
        # CYAN GEM on chest.
        gem_y = cy + 1
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_thorgaruk._alpha(180 * (6 - r) / 6 * pulse * alpha_scale)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                    (cx, gem_y), r)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha_base),
                                (cx, gem_y), 3)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                                (cx, gem_y), 2)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha_base),
                         (cx, gem_y, 1, 1))
        # Belly fur (below armor).
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_mid"], [
            (cx - 8, cy + 5),
            (cx + 8, cy + 5),
            (cx + 10, cy + 8),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 10, cy + 8),
        ], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_light"], [
            (cx - 6, cy + 7),
            (cx + 6, cy + 7),
            (cx + 7, cy + 9),
            (cx + 4, cy + 11),
            (cx - 4, cy + 11),
            (cx - 7, cy + 9),
        ], alpha_base)
        # Fur texture ticks on side.
        for i, y_off in enumerate((-5, 0, 5)):
            for x_off in (-14, 14):
                tx = cx + x_off
                ty = cy + y_off
                pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["fur_darkest"], alpha_base),
                                 (tx, ty), (tx + (1 if x_off > 0 else -1), ty + 1), 1)
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["fur_edge"], alpha_base),
                                 (tx, ty, 1, 1))
    def _draw_thg_pauldrons(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Big spiky shoulder armor pauldrons with cyan gems."""
        alpha_base = int(255 * alpha_scale)
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 14
            base_y = cy
            # Pauldron shape (angular, chunky).
            pad_pts = [
                (base_x, base_y - 3),
                (base_x + side * 5, base_y - 6),
                (base_x + side * 9, base_y - 2),
                (base_x + side * 10, base_y + 4),
                (base_x + side * 5, base_y + 7),
                (base_x + side * 1, base_y + 6),
            ]
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], pad_pts,
                                      alpha_base, offset=(2, 2))
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_darkest"], pad_pts,
                                      alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_dark"], [
                (base_x + side * 1, base_y - 2),
                (base_x + side * 4, base_y - 5),
                (base_x + side * 8, base_y - 1),
                (base_x + side * 9, base_y + 3),
                (base_x + side * 5, base_y + 6),
                (base_x + side * 2, base_y + 5),
            ], alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_mid"], [
                (base_x + side * 2, base_y - 1),
                (base_x + side * 4, base_y - 3),
                (base_x + side * 6, base_y),
                (base_x + side * 6, base_y + 3),
                (base_x + side * 3, base_y + 4),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_light"], alpha_base),
                             (base_x + side * 3, base_y - 2, 2, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_edge"], alpha_base),
                             (base_x + side * 3, base_y - 2, 1, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_shine"], alpha_base),
                             (base_x + side * 4, base_y - 3, 1, 1))
            # Gold trim edge.
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["gold_mid"], alpha_base),
                             (base_x + side * 5, base_y - 6),
                             (base_x + side * 9, base_y - 2), 1)
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["gold_light"], alpha_base),
                             (base_x + side * 6, base_y - 5),
                             (base_x + side * 8, base_y - 3), 1)
            # SPIKE on top (bone/steel).
            spike_tip_x = base_x + side * 5
            spike_tip_y = base_y - 10
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], [
                (spike_tip_x + 1, spike_tip_y + 1),
                (base_x + side * 3 + 1, base_y - 5 + 1),
                (base_x + side * 7 + 1, base_y - 5 + 1),
            ], alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_darkest"], [
                (spike_tip_x, spike_tip_y),
                (base_x + side * 3, base_y - 5),
                (base_x + side * 7, base_y - 5),
            ], alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_dark"], [
                (spike_tip_x, spike_tip_y),
                (base_x + side * 4, base_y - 5),
                (base_x + side * 6, base_y - 5),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_light"], alpha_base),
                             (spike_tip_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                             (spike_tip_x, spike_tip_y, 1, 1))
            # CYAN GEM on pauldron.
            gem_x = base_x + side * 5
            gem_y = base_y + 2
            pulse = math.sin(phase * 2 + side_i) * 0.3 + 0.7
            for r in range(4, 0, -1):
                alpha = _NS_thorgaruk._alpha(150 * pulse * (4 - r) / 4 * alpha_scale)
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                        (gem_x, gem_y), r)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha_base),
                             (gem_x - 1, gem_y - 1, 3, 2))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                             (gem_x, gem_y - 1, 2, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha_base),
                             (gem_x, gem_y - 1, 1, 1))
    def _draw_thg_arms(surface, cx, cy, facing, phase, action, attack_progress,
                       alpha_scale=1.0):
        """Two massive arms holding giant axe two-handed."""
        alpha_base = int(255 * alpha_scale)
        # Both hands grip the axe handle.
        # Axe swing computed here for all cases.
        # AXE ANGLE.
        if action == "attack":
            if attack_progress < 0.4:
                # Wind-up: raise axe back over shoulder.
                t = attack_progress / 0.4
                axe_angle_deg = -30 - t * 100  # back over head
            elif attack_progress < 0.65:
                # Slam forward.
                t = (attack_progress - 0.4) / 0.25
                axe_angle_deg = -130 + t * 210  # arc down forward
            else:
                # Recovery.
                t = (attack_progress - 0.65) / 0.35
                axe_angle_deg = 80 - t * 110
        else:
            # Idle: axe held forward-down at rest.
            axe_angle_deg = 40 + math.sin(phase * 0.5) * 3
        axe_angle_rad = math.radians(axe_angle_deg)
        # Compute grip positions.
        # Front hand at end of handle, back hand mid-handle.
        handle_len = 40
        # Handle base near boss center.
        handle_base_x = cx + facing * 3
        handle_base_y = cy - 2
        # Handle tip (where axe head is).
        tip_x = handle_base_x + int(math.cos(axe_angle_rad) * handle_len) * facing
        tip_y = handle_base_y + int(math.sin(axe_angle_rad) * handle_len)
        # Two grip positions.
        grip_front_x = handle_base_x + int(math.cos(axe_angle_rad) * (handle_len - 8)) * facing
        grip_front_y = handle_base_y + int(math.sin(axe_angle_rad) * (handle_len - 8))
        grip_back_x = handle_base_x + int(math.cos(axe_angle_rad) * 5) * facing
        grip_back_y = handle_base_y + int(math.sin(axe_angle_rad) * 5)
        # Draw BACK arm first (behind axe handle).
        back_shoulder_x = cx - facing * 10
        back_shoulder_y = cy - 5
        _NS_thorgaruk._draw_arm_segment(surface, back_shoulder_x, back_shoulder_y,
                                        grip_back_x, grip_back_y, alpha_base)
        # AXE (drawn between arms in Z-order).
        _NS_thorgaruk._draw_giant_axe(surface, handle_base_x, handle_base_y,
                                      tip_x, tip_y, facing, phase, alpha_base,
                                      is_swinging=(action == "attack"))
        # FRONT arm on top.
        front_shoulder_x = cx + facing * 10
        front_shoulder_y = cy - 5
        _NS_thorgaruk._draw_arm_segment(surface, front_shoulder_x, front_shoulder_y,
                                        grip_front_x, grip_front_y, alpha_base)
    def _draw_arm_segment(surface, sx, sy, hx, hy, alpha_base):
        """Muscular furry arm from shoulder to hand grip."""
        # Compute elbow midpoint with slight bend.
        mid_x = (sx + hx) // 2
        mid_y = (sy + hy) // 2 + 2
        # Upper arm (fur, thick).
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                    (sx + 1, sy + 1), (mid_x + 1, mid_y + 1), 8, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_darkest"],
                                    (sx, sy), (mid_x, mid_y), 7, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_dark"],
                                    (sx, sy), (mid_x, mid_y), 6, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["fur_mid"],
                                    (sx, sy - 1), (mid_x, mid_y - 1), 3, alpha_base)
        # Forearm (arm bracer - dark blue armor).
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                    (mid_x + 1, mid_y + 1), (hx + 1, hy + 1), 7, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["armor_darkest"],
                                    (mid_x, mid_y), (hx, hy), 6, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["armor_dark"],
                                    (mid_x, mid_y), (hx, hy), 5, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["armor_mid"],
                                    (mid_x, mid_y - 1), (hx, hy - 1), 2, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["armor_light"],
                                    (mid_x, mid_y - 2), (hx, hy - 2), 1, alpha_base)
        # Small cyan glow on bracer.
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                         (mid_x + (hx - mid_x) // 2, mid_y + (hy - mid_y) // 2, 1, 1))
        # Elbow joint (armor plate).
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["armor_darkest"], alpha_base),
                                (mid_x, mid_y), 4)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["armor_mid"], alpha_base),
                                (mid_x, mid_y), 3)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_shine"], alpha_base),
                         (mid_x - 1, mid_y - 1, 1, 1))
        # HAND grip (fur knuckles + armor grip).
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["shadow_deep"], alpha_base),
                                (hx + 1, hy + 1), 4)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["fur_darkest"], alpha_base),
                                (hx, hy), 3)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["fur_dark"], alpha_base),
                                (hx, hy), 2)
    def _draw_giant_axe(surface, base_x, base_y, tip_x, tip_y, facing, phase,
                        alpha_base, is_swinging=False):
        """Two-headed giant axe with cyan glowing blade."""
        # Handle (wooden or dark metal).
        handle_dx = tip_x - base_x
        handle_dy = tip_y - base_y
        handle_len = math.hypot(handle_dx, handle_dy)
        if handle_len < 1:
            return
        angle = math.atan2(handle_dy, handle_dx)
        perp = angle + math.pi / 2
        # Handle line (thick).
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                    (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1),
                                    4, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_darkest"],
                                    (base_x, base_y), (tip_x, tip_y), 3, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_dark"],
                                    (base_x, base_y), (tip_x, tip_y), 2, alpha_base)
        # Handle highlight.
        offset_x = int(math.cos(perp) * 1)
        offset_y = int(math.sin(perp) * 1)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_mid"],
                                    (base_x + offset_x, base_y + offset_y),
                                    (tip_x + offset_x, tip_y + offset_y), 1, alpha_base)
        # Handle wrap details (chain windings).
        for wrap_i in range(4):
            wrap_t = 0.3 + wrap_i * 0.15
            wx = int(base_x + handle_dx * wrap_t)
            wy = int(base_y + handle_dy * wrap_t)
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["armor_darkest"], alpha_base),
                             (wx + int(math.cos(perp) * 2),
                              wy + int(math.sin(perp) * 2)),
                             (wx - int(math.cos(perp) * 2),
                              wy - int(math.sin(perp) * 2)), 1)
        # AXE HEAD (large double-bladed shape at tip).
        # Blade shape extends perpendicular to handle.
        blade_w = 14   # width perpendicular to handle
        blade_l = 12   # length along handle direction
        # Center of axe head (a bit before the tip so blade extends beyond).
        head_cx = tip_x - int(math.cos(angle) * (blade_l // 2))
        head_cy = tip_y - int(math.sin(angle) * (blade_l // 2))
        # Blade 4 corners (double-headed).
        # Top blade (up-perpendicular).
        top_far_x = head_cx + int(math.cos(perp) * blade_w)
        top_far_y = head_cy + int(math.sin(perp) * blade_w)
        top_forward_x = top_far_x + int(math.cos(angle) * blade_l // 2)
        top_forward_y = top_far_y + int(math.sin(angle) * blade_l // 2)
        top_back_x = top_far_x - int(math.cos(angle) * blade_l // 2)
        top_back_y = top_far_y - int(math.sin(angle) * blade_l // 2)
        # Bottom blade (down-perpendicular).
        bot_far_x = head_cx - int(math.cos(perp) * blade_w)
        bot_far_y = head_cy - int(math.sin(perp) * blade_w)
        bot_forward_x = bot_far_x + int(math.cos(angle) * blade_l // 2)
        bot_forward_y = bot_far_y + int(math.sin(angle) * blade_l // 2)
        bot_back_x = bot_far_x - int(math.cos(angle) * blade_l // 2)
        bot_back_y = bot_far_y - int(math.sin(angle) * blade_l // 2)
        # Central hub connecting to handle.
        hub_front_x = head_cx + int(math.cos(angle) * blade_l // 2)
        hub_front_y = head_cy + int(math.sin(angle) * blade_l // 2)
        hub_back_x = head_cx - int(math.cos(angle) * blade_l // 2)
        hub_back_y = head_cy - int(math.sin(angle) * blade_l // 2)
        # Top blade polygon (curved crescent-like).
        top_blade_pts = [
            (hub_front_x, hub_front_y),
            (top_forward_x, top_forward_y),
            (top_far_x, top_far_y),
            (top_back_x, top_back_y),
            (hub_back_x, hub_back_y),
        ]
        # Shadow.
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                  [(p[0] + 2, p[1] + 2) for p in top_blade_pts], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["blade_darkest"],
                                  top_blade_pts, alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["blade_dark"], [
            (hub_front_x, hub_front_y),
            (int((hub_front_x + top_forward_x) / 2), int((hub_front_y + top_forward_y) / 2)),
            (int((top_far_x + top_forward_x) / 2), int((top_far_y + top_forward_y) / 2)),
            (int((top_far_x + top_back_x) / 2), int((top_far_y + top_back_y) / 2)),
            (int((hub_back_x + top_back_x) / 2), int((hub_back_y + top_back_y) / 2)),
            (hub_back_x, hub_back_y),
        ], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["blade_mid"], [
            (head_cx, head_cy),
            (int((head_cx + top_forward_x) / 2), int((head_cy + top_forward_y) / 2)),
            (int((head_cx * 0.4 + top_far_x * 0.6)), int((head_cy * 0.4 + top_far_y * 0.6))),
            (int((head_cx + top_back_x) / 2), int((head_cy + top_back_y) / 2)),
        ], alpha_base)
        # Blade edge highlight.
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["blade_light"],
                                    (top_forward_x, top_forward_y),
                                    (top_far_x, top_far_y), 1, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["blade_shine"],
                                    (top_far_x, top_far_y),
                                    (top_back_x, top_back_y), 1, alpha_base)
        # Bottom blade (mirror).
        bot_blade_pts = [
            (hub_front_x, hub_front_y),
            (bot_forward_x, bot_forward_y),
            (bot_far_x, bot_far_y),
            (bot_back_x, bot_back_y),
            (hub_back_x, hub_back_y),
        ]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                  [(p[0] + 2, p[1] + 2) for p in bot_blade_pts], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["blade_darkest"],
                                  bot_blade_pts, alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["blade_dark"], [
            (hub_front_x, hub_front_y),
            (int((hub_front_x + bot_forward_x) / 2), int((hub_front_y + bot_forward_y) / 2)),
            (int((bot_far_x + bot_forward_x) / 2), int((bot_far_y + bot_forward_y) / 2)),
            (int((bot_far_x + bot_back_x) / 2), int((bot_far_y + bot_back_y) / 2)),
            (int((hub_back_x + bot_back_x) / 2), int((hub_back_y + bot_back_y) / 2)),
            (hub_back_x, hub_back_y),
        ], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["blade_mid"], [
            (head_cx, head_cy),
            (int((head_cx + bot_forward_x) / 2), int((head_cy + bot_forward_y) / 2)),
            (int((head_cx * 0.4 + bot_far_x * 0.6)), int((head_cy * 0.4 + bot_far_y * 0.6))),
            (int((head_cx + bot_back_x) / 2), int((head_cy + bot_back_y) / 2)),
        ], alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["blade_light"],
                                    (bot_forward_x, bot_forward_y),
                                    (bot_far_x, bot_far_y), 1, alpha_base)
        _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["blade_shine"],
                                    (bot_far_x, bot_far_y),
                                    (bot_back_x, bot_back_y), 1, alpha_base)
        # Central hub (dark metal + cyan gem).
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["armor_darkest"], alpha_base),
                                (head_cx, head_cy), 4)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["armor_dark"], alpha_base),
                                (head_cx, head_cy), 3)
        _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha_base),
                                (head_cx, head_cy), 2)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                         (head_cx, head_cy, 1, 1))
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha_base),
                         (head_cx, head_cy, 1, 1))
        # CYAN GLOW around axe head.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        strength = 1.6 if is_swinging else 1.0
        for r in range(int(14 * strength), 4, -2):
            alpha = _NS_thorgaruk._alpha(120 * pulse * strength * (14 - r) / 14 * alpha_base / 255)
            if alpha > 0:
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                        (head_cx, head_cy), r)
        # Blade tips glow.
        for tip in [(top_far_x, top_far_y), (bot_far_x, bot_far_y)]:
            for r in range(4, 0, -1):
                alpha = _NS_thorgaruk._alpha(140 * pulse * strength * (4 - r) / 4 * alpha_base / 255)
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                        tip, r)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha_base),
                             (tip[0], tip[1], 1, 1))
    def _draw_thg_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Minotaur head — helmet, horns, snout, glowing eyes."""
        alpha_base = int(255 * alpha_scale)
        # HEAD SHAPE (fur, elongated snout).
        head_pts = [
            (cx - 8, cy),         # back top
            (cx - 9, cy + 4),
            (cx - 8, cy + 10),
            (cx - 4, cy + 14),    # jaw back
            (cx + 4, cy + 15),    # snout mid
            (cx + 10, cy + 13),   # snout front
            (cx + 12, cy + 10),
            (cx + 11, cy + 6),
            (cx + 9, cy + 3),
            (cx + 8, cy),
            (cx + 4, cy - 2),
            (cx - 4, cy - 2),
        ]
        # Adjust for facing.
        if facing == -1:
            head_pts = [(2 * cx - p[0], p[1]) for p in head_pts]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], head_pts,
                                  alpha_base, offset=(2, 2))
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_darkest"], head_pts,
                                  alpha_base)
        # Fur mid.
        head_mid_pts_r = [
            (cx - 7, cy + 1),
            (cx - 8, cy + 4),
            (cx - 7, cy + 9),
            (cx - 3, cy + 13),
            (cx + 4, cy + 14),
            (cx + 9, cy + 12),
            (cx + 11, cy + 9),
            (cx + 10, cy + 6),
            (cx + 8, cy + 3),
            (cx + 7, cy + 1),
            (cx + 3, cy - 1),
            (cx - 3, cy - 1),
        ]
        if facing == -1:
            head_mid_pts_r = [(2 * cx - p[0], p[1]) for p in head_mid_pts_r]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["fur_dark"], head_mid_pts_r,
                                  alpha_base)
        # SNOUT (skin, pinkish-brown, front of face).
        snout_pts_r = [
            (cx + 4, cy + 10),
            (cx + 10, cy + 11),
            (cx + 11, cy + 12),
            (cx + 8, cy + 14),
            (cx + 4, cy + 14),
        ]
        if facing == -1:
            snout_pts_r = [(2 * cx - p[0], p[1]) for p in snout_pts_r]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["skin_dark"], snout_pts_r,
                                  alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["skin_mid"], [
            (cx + 5 * facing, cy + 11),
            (cx + 9 * facing, cy + 12),
            (cx + 7 * facing, cy + 13),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["skin_light"], alpha_base),
                         (cx + 7 * facing, cy + 11, 1, 1))
        # NOSTRIL.
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["shadow_deep"], alpha_base),
                         (cx + 8 * facing, cy + 12, 2, 1))
        # TUSKS (small ivory tusks curving up from lower jaw).
        for tusk_side in (-1, 1):
            tusk_x = cx + facing * 4 + tusk_side * 2
            tusk_y = cy + 14
            tusk_tip_x = tusk_x + tusk_side * 1
            tusk_tip_y = tusk_y - 3
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["horn_dark"], [
                (tusk_x - 1, tusk_y),
                (tusk_x + 1, tusk_y),
                (tusk_tip_x, tusk_tip_y),
            ], alpha_base)
            _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["horn_mid"], [
                (tusk_x, tusk_y),
                (tusk_x + 1, tusk_y),
                (tusk_tip_x, tusk_tip_y),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["horn_light"], alpha_base),
                             (tusk_tip_x, tusk_tip_y, 1, 1))
        # HELMET (top of head - dark blue armor plate with gold trim).
        helmet_pts_r = [
            (cx - 7, cy - 2),
            (cx - 8, cy + 2),
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 8, cy + 2),
            (cx + 7, cy - 2),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ]
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"], helmet_pts_r,
                                  alpha_base, offset=(1, 1))
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_darkest"], helmet_pts_r,
                                  alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_dark"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 4, cy + 3),
            (cx + 4, cy + 3),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ], alpha_base)
        _NS_thorgaruk._poly_alpha(surface, _NS_thorgaruk.PALETTE["armor_mid"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx + 5, cy + 2),
            (cx + 4, cy),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_light"], alpha_base),
                         (cx - 2, cy, 4, 1))
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["armor_shine"], alpha_base),
                         (cx - 1, cy, 2, 1))
        # Helmet CENTER GEM (cyan, in forehead).
        gem_y = cy + 2
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_thorgaruk._alpha(150 * pulse * (4 - r) / 4 * alpha_scale)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                    (cx, gem_y), r)
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha_base),
                         (cx - 1, gem_y - 1, 3, 2))
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                         (cx, gem_y - 1, 2, 1))
        pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha_base),
                         (cx, gem_y - 1, 1, 1))
        # BIG CURVED HORNS (bone/ivory, sweeping outward).
        _NS_thorgaruk._draw_horns(surface, cx, cy - 2, phase, alpha_base)
        # GLOWING CYAN EYES.
        _NS_thorgaruk._draw_thg_eyes(surface, cx + facing * 3, cy + 7, facing, phase, alpha_scale)
    def _draw_horns(surface, cx, cy, phase, alpha_base):
        """Two large curved horns sweeping outward from helmet."""
        sway = math.sin(phase * 0.3) * 1
        for side in (-1, 1):
            # Horn base at helmet.
            base_x = cx + side * 5
            base_y = cy
            # Horn curves outward and down.
            # Segment 1 (upper): from base going up-out.
            seg1_x = cx + side * 8
            seg1_y = cy - 4
            # Segment 2 (mid): peak of curve.
            seg2_x = cx + side * 12 + int(sway * side)
            seg2_y = cy - 2
            # Segment 3 (tip): curving down and forward.
            seg3_x = cx + side * 14 + int(sway * side)
            seg3_y = cy + 4
            # Draw as tapered segments.
            # Shadow.
            for i, ((x1, y1), (x2, y2), thick) in enumerate([
                ((base_x, base_y), (seg1_x, seg1_y), 6),
                ((seg1_x, seg1_y), (seg2_x, seg2_y), 5),
                ((seg2_x, seg2_y), (seg3_x, seg3_y), 4),
            ]):
                _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["shadow_deep"],
                                            (x1 + 1, y1 + 1), (x2 + 1, y2 + 1),
                                            thick + 1, alpha_base)
            # Base layer dark.
            for i, ((x1, y1), (x2, y2), thick) in enumerate([
                ((base_x, base_y), (seg1_x, seg1_y), 6),
                ((seg1_x, seg1_y), (seg2_x, seg2_y), 5),
                ((seg2_x, seg2_y), (seg3_x, seg3_y), 4),
            ]):
                _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_darkest"],
                                            (x1, y1), (x2, y2), thick, alpha_base)
                _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_dark"],
                                            (x1, y1), (x2, y2), max(1, thick - 1), alpha_base)
                _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_mid"],
                                            (x1, y1 - 1), (x2, y2 - 1), max(1, thick - 3),
                                            alpha_base)
                _NS_thorgaruk._aaline_alpha(surface, _NS_thorgaruk.PALETTE["horn_light"],
                                            (x1, y1 - 2), (x2, y2 - 2), 1, alpha_base)
            # Tip highlight (bright).
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["horn_shine"], alpha_base),
                             (seg3_x, seg3_y, 1, 1))
            # Horn ring bands (decorative gold + cyan).
            for band_x, band_y in [(seg1_x, seg1_y), (seg2_x, seg2_y)]:
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["gold_dark"], alpha_base),
                                 (band_x - 2, band_y - 1, 4, 2))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["gold_mid"], alpha_base),
                                 (band_x - 2, band_y - 1, 4, 1))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha_base),
                                 (band_x, band_y, 1, 1))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha_base),
                                 (band_x, band_y, 1, 1))
    def _draw_thg_eyes(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Bright cyan eyes (helmet visor style)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        # Single glowing eye visor (or 2 tightly).
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            for r in range(5, 0, -1):
                a = _NS_thorgaruk._alpha(150 * (5 - r) / 5 * pulse * alpha_scale)
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], a),
                                        (ex, ey), r)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["eye_mid"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["eye_light"], alpha_base),
                             (ex, ey, 1, 1))
    # ============================================================
    # HELPERS
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_thorgaruk._poly(surface, color, points)
            return
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_thorgaruk._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_thorgaruk._aaline(surface, color, start, end, width)
            return
        c = _NS_thorgaruk._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (14 - radius, 16 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 12, 170), (5, 9, 150, 16))
        pygame.draw.ellipse(shadow, (20, 40, 80, 110), (12, 11, 136, 12))
        surface.blit(shadow, (x - 80, y - 16))
    def _draw_arcane_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 180), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_thorgaruk._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_thorgaruk._aacircle(aura, (*_NS_thorgaruk.PALETTE["arcane_darkest"], alpha),
                                        (120, 90), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_thorgaruk._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thorgaruk._aacircle(aura, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                        (120, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_thorgaruk._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thorgaruk._aacircle(aura, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                        (120, 90), radius)
        surface.blit(aura, (x - 120, y - 90))
        # Floating cyan motes.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thorgaruk.PALETTE["arcane_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_thorgaruk.PALETTE["arcane_dark"], 220),
                            (16, 22, 158, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_thorgaruk.PALETTE["arcane_mid"], 230),
                            (30, 24, 130, 22), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 35 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_thorgaruk.PALETTE["arcane_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_thorgaruk.PALETTE["arcane_hot"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_thorgaruk.PALETTE["arcane_hot"],
                                       _NS_thorgaruk._alpha(150 * pulse)),
                                (16, 12, 158, 40), 1)
        surface.blit(ring, (x - 95, y - 30))
    def _draw_arcane_sparks(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(40, 3, -3):
            alpha = _NS_thorgaruk._alpha((40 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_thorgaruk.PALETTE["arcane_darkest"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(25, 3, -2):
            alpha = _NS_thorgaruk._alpha((25 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising cyan sparks.
        for i, offset in enumerate((-28, -20, -12, -4, 4, 12, 20, 28, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_thorgaruk._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                    (sx, sy), 3)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                             (sx, sy - 2, 1, 1))
    # ============================================================
    # AXE SWING ARC
    # ============================================================
    def _draw_axe_swing_arc(surface, boss, x, y, progress):
        """Bright cyan slash arc when axe swings."""
        if not (0.4 <= progress <= 0.75):
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.35
        cx = x
        cy = y - 4
        radius = 40
        # Arc sweeps from top back to front-down.
        start_angle = -120 + t * 200 - 40
        end_angle = -120 + t * 200 + 10
        num_pts = 14
        pts = []
        for i in range(num_pts):
            a_deg = start_angle + (end_angle - start_angle) * i / (num_pts - 1)
            a_rad = math.radians(a_deg)
            px = cx + int(math.cos(a_rad) * radius) * facing
            py = cy + int(math.sin(a_rad) * radius)
            pts.append((px, py))
        arc_surf = pygame.Surface((140, 140), pygame.SRCALPHA)
        for i in range(len(pts) - 1):
            alpha = _NS_thorgaruk._alpha(220 * (i / len(pts)))
            p1 = (pts[i][0] - cx + 70, pts[i][1] - cy + 70)
            p2 = (pts[i + 1][0] - cx + 70, pts[i + 1][1] - cy + 70)
            pygame.draw.line(arc_surf, (*_NS_thorgaruk.PALETTE["arcane_darkest"], alpha),
                             p1, p2, 6)
            pygame.draw.line(arc_surf, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                             p1, p2, 4)
            pygame.draw.line(arc_surf, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                             p1, p2, 3)
            pygame.draw.line(arc_surf, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                             p1, p2, 2)
            pygame.draw.line(arc_surf, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                             p1, p2, 1)
        surface.blit(arc_surf, (cx - 70, cy - 70))
        # Sparkles along arc.
        for i in range(6):
            sp_t = (t * 3 + i * 0.16) % 1.0
            idx = int(sp_t * (num_pts - 1))
            sp = pts[idx]
            spx = sp[0] + int(math.sin(t * 6 + i) * 4)
            spy = sp[1] + int(math.cos(t * 6 + i) * 4)
            alpha = _NS_thorgaruk._alpha(240)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_hot"], alpha),
                             (spx, spy, 2, 2))
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                             (spx, spy, 1, 1))
    # ============================================================
    # SKILL: Q - SHOCKWAVE (ground slam forward wave)
    # ============================================================
    def _draw_shockwave_foreground(surface, boss, x, y, timer, phase):
        """Cyan wave of spikes shooting forward from boss."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 5)
        if progress < 0.2:
            # Wind-up glow at ground.
            t = progress / 0.2
            gx = x + facing * 20
            gy = y + 45
            for r in range(int(15 * t), 0, -2):
                alpha = _NS_thorgaruk._alpha(200 * t * (15 - r) / 15)
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                        (gx, gy), r)
        else:
            # Wave shoots forward — rising spike columns.
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 30
            start_y = y + 42
            # Wave travels distance.
            wave_dist = int(t * 200)
            end_x = start_x + facing * wave_dist
            # 8 spikes along the wave line at different intervals.
            num_spikes = 8
            for i in range(num_spikes):
                spike_delay = i * 0.06
                spike_t = t - spike_delay
                if spike_t <= 0:
                    continue
                spike_dist = int(min(spike_t, 0.4) * 250)
                sx = start_x + facing * spike_dist
                sy_base = start_y
                # Spike rise animation.
                if spike_t < 0.1:
                    spike_h = int(spike_t * 10 * 50)  # rising
                elif spike_t < 0.25:
                    spike_h = 50  # full
                else:
                    spike_h = max(0, 50 - int((spike_t - 0.25) * 200))
                if spike_h < 3:
                    continue
                spike_tip_y = sy_base - spike_h
                # Draw as tall thin triangle.
                spike_w = 4
                _NS_thorgaruk._poly(surface, _NS_thorgaruk.PALETTE["shadow_deep"], [
                    (sx + 1, spike_tip_y + 1),
                    (sx - spike_w + 1, sy_base + 1),
                    (sx + spike_w + 1, sy_base + 1),
                ])
                _NS_thorgaruk._poly(surface, _NS_thorgaruk.PALETTE["arcane_darkest"], [
                    (sx, spike_tip_y),
                    (sx - spike_w, sy_base),
                    (sx + spike_w, sy_base),
                ])
                _NS_thorgaruk._poly(surface, _NS_thorgaruk.PALETTE["arcane_dark"], [
                    (sx, spike_tip_y),
                    (sx - spike_w + 1, sy_base),
                    (sx + spike_w - 1, sy_base),
                ])
                _NS_thorgaruk._poly(surface, _NS_thorgaruk.PALETTE["arcane_mid"], [
                    (sx, spike_tip_y),
                    (sx - 1, sy_base - 5),
                    (sx + 1, sy_base - 5),
                ])
                _NS_thorgaruk._poly(surface, _NS_thorgaruk.PALETTE["arcane_light"], [
                    (sx, spike_tip_y),
                    (sx, sy_base - 15),
                    (sx + 1, sy_base - 15),
                ])
                # Bright tip.
                pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_shine"],
                                 (sx, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["white"],
                                 (sx, spike_tip_y, 1, 1))
                # Radial glow around tip.
                for r in range(4, 0, -1):
                    alpha = _NS_thorgaruk._alpha(150 * (4 - r) / 4)
                    _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                            (sx, spike_tip_y), r)
                # Ground crack at base.
                pygame.draw.line(surface, _NS_thorgaruk.PALETTE["arcane_mid"],
                                 (sx - 3, sy_base + 1),
                                 (sx + 3, sy_base + 1), 1)
    # ============================================================
    # SKILL: W - EMPOWER (self buff aura)
    # ============================================================
    def _draw_empower_ground(surface, boss, x, y, timer, phase):
        """Rune circles glow brighter."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_thorgaruk._alpha(200 - i * 45)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                    (x, y + 46), r, 2)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                    (x, y + 46), r, 1)
    def _draw_empower_foreground(surface, boss, x, y, timer, phase):
        """Spiraling cyan energy around boss + rising arrows."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 5)
        core_y = y - 4 + hover
        # Spiral energy streams (from ref image: swirl motion).
        num_streams = 3
        for stream_i in range(num_streams):
            stream_offset = stream_i * (math.pi * 2 / num_streams)
            for k in range(15):
                t = k / 15
                spiral_r = 15 + t * 40
                spiral_angle = phase * 2 + stream_offset + t * 4
                sx = x + int(math.cos(spiral_angle) * spiral_r)
                sy = core_y + int(math.sin(spiral_angle) * spiral_r * 0.6)
                alpha = _NS_thorgaruk._alpha(220 * (1 - t))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                 (sx, sy, 1, 1))
                if k % 3 == 0:
                    pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_hot"], alpha),
                                     (sx, sy, 1, 1))
        # Rising cyan arrows/chevrons around body.
        for i in range(6):
            angle = i * math.pi / 3
            arrow_r = 32
            ax = x + int(math.cos(angle) * arrow_r)
            ay_base = core_y + int(math.sin(angle) * arrow_r * 0.6)
            rise_t = (phase * 0.8 + i * 0.16) % 1.0
            ay = ay_base - int(rise_t * 30)
            alpha = _NS_thorgaruk._alpha(220 * (1 - rise_t))
            _NS_thorgaruk._poly(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha), [
                (ax, ay - 3), (ax - 3, ay), (ax + 3, ay),
            ])
            _NS_thorgaruk._poly(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha), [
                (ax, ay - 2), (ax - 2, ay), (ax + 2, ay),
            ])
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                             (ax, ay - 2, 1, 1))
        # Central body glow (empowered).
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(20, 0, -2):
            alpha = _NS_thorgaruk._alpha(80 * pulse * (20 - r) / 20)
            if alpha > 0:
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                        (x, core_y), r)
    # ============================================================
    # SKILL: E - SKEWER (charge dash)
    # ============================================================
    def _draw_skewer_ground(surface, boss, x, y, timer, phase):
        """Cyan trail from boss to target on ground."""
        tx, ty = _NS_thorgaruk._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Dash line.
        if 0.2 < progress < 0.85:
            t = (progress - 0.2) / 0.65
            travel_x = int(x + (tx - x) * t)
            travel_y = int(y + (ty - y) * t)
            # Trail line.
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_darkest"], 220),
                             (x, y + 44), (travel_x, travel_y + 30), 6)
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], 240),
                             (x, y + 44), (travel_x, travel_y + 30), 4)
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], 220),
                             (x, y + 44), (travel_x, travel_y + 30), 2)
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], 200),
                             (x, y + 44), (travel_x, travel_y + 30), 1)
    def _draw_skewer_foreground(surface, boss, x, y, timer, phase):
        """Cyan blade streaks and impact at target."""
        tx, ty = _NS_thorgaruk._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 5)
        if 0.25 < progress < 0.75:
            # Cyan streaks radiating.
            t = (progress - 0.25) / 0.5
            angle_to_target = math.atan2(ty - y, tx - x)
            perp = angle_to_target + math.pi / 2
            travel_x = int(x + (tx - x) * t)
            travel_y = int(y + (ty - y) * t)
            # Multiple radial streaks around boss during dash.
            for i in range(8):
                sr = 20 + i * 3
                offset = math.sin(phase * 3 + i) * 4
                s_x1 = travel_x + int(math.cos(perp) * offset)
                s_y1 = travel_y - 4 + hover + int(math.sin(perp) * offset)
                s_x2 = s_x1 - int(math.cos(angle_to_target) * sr)
                s_y2 = s_y1 - int(math.sin(angle_to_target) * sr)
                alpha = _NS_thorgaruk._alpha(200 - i * 20)
                pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                 (s_x1, s_y1), (s_x2, s_y2), 2)
                pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                                 (s_x1, s_y1), (s_x2, s_y2), 1)
        elif progress >= 0.75:
            # Impact burst at target.
            t = (progress - 0.75) / 0.25
            intensity = math.sin(t * math.pi)
            radius = int(15 + t * 25)
            alpha = _NS_thorgaruk._alpha(240 * intensity)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_darkest"], alpha),
                                    (tx, ty), radius + 4, 3)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                    (tx, ty), max(1, radius - 5), 2)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                    (tx, ty), max(1, radius - 12), 1)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                                    (tx, ty), max(1, radius // 4))
            # Radial cyan spikes.
            for i in range(12):
                a = i * math.pi / 6
                ex = tx + int(math.cos(a) * radius)
                ey = ty + int(math.sin(a) * radius * 0.7)
                pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL: R - REVERSE POLARITY (magnetic pull vortex)
    # ============================================================
    def _draw_polarity_ground(surface, boss, x, y, timer, phase):
        """Concentric magnetic vortex on ground."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(4):
            r = int(40 + i * 12 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_thorgaruk._alpha(230 - i * 45)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_darkest"], alpha),
                                    (x, y + 48), r, 2)
            _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                    (x, y + 48), r, 1)
        # Rune tick marks.
        for i in range(16):
            angle = phase * 0.4 + i * math.pi / 8
            r1 = 55
            r2 = 75
            x1 = x + int(math.cos(angle) * r1)
            y1 = y + 48 + int(math.sin(angle) * r1 * 0.4)
            x2 = x + int(math.cos(angle) * r2)
            y2 = y + 48 + int(math.sin(angle) * r2 * 0.4)
            pygame.draw.line(surface, _NS_thorgaruk.PALETTE["arcane_light"], (x1, y1), (x2, y2), 2)
            pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_shine"], (x2, y2, 2, 2))
    def _draw_polarity_foreground(surface, boss, x, y, timer, phase):
        """Inward-pulling spiral streams + central burst."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        hover = int(math.sin(phase * 0.5) * 5)
        core_y = y - 4 + hover
        # Inward-pulling energy streams (opposite of outward spirals).
        num_streams = 12
        for stream_i in range(num_streams):
            stream_offset = stream_i * (math.pi * 2 / num_streams)
            for k in range(10):
                t = k / 10
                # Reversed spiral — from outside pulling in.
                pull_r = 65 - t * 60
                pull_angle = phase * 2 + stream_offset - t * 3  # reverse direction
                sx = x + int(math.cos(pull_angle) * pull_r)
                sy = core_y + int(math.sin(pull_angle) * pull_r * 0.5)
                alpha = _NS_thorgaruk._alpha(240 * (1 - t))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_mid"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                                 (sx, sy, 1, 1))
        # Central pulsing core.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        core_r = int(15 + pulse * 5)
        for r in range(core_r + 5, 0, -2):
            alpha = _NS_thorgaruk._alpha(180 * pulse * (core_r + 5 - r) / (core_r + 5))
            if alpha > 0:
                _NS_thorgaruk._aacircle(surface, (*_NS_thorgaruk.PALETTE["arcane_dark"], alpha),
                                        (x, core_y), r)
        _NS_thorgaruk._aacircle(surface, _NS_thorgaruk.PALETTE["arcane_mid"], (x, core_y), core_r - 3)
        _NS_thorgaruk._aacircle(surface, _NS_thorgaruk.PALETTE["arcane_light"], (x, core_y), core_r - 6)
        _NS_thorgaruk._aacircle(surface, _NS_thorgaruk.PALETTE["arcane_shine"], (x, core_y),
                                max(1, core_r - 8))
        pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["white"], (x, core_y, 1, 1))
        # Radial rays bursting outward from center (interspersed with the pull).
        for i in range(8):
            ray_angle = phase * 1.5 + i * math.pi / 4
            ray_r = 45 + int(math.sin(phase * 3 + i) * 5)
            rx1 = x + int(math.cos(ray_angle) * 12)
            ry1 = core_y + int(math.sin(ray_angle) * 8)
            rx2 = x + int(math.cos(ray_angle) * ray_r)
            ry2 = core_y + int(math.sin(ray_angle) * ray_r * 0.6)
            alpha = _NS_thorgaruk._alpha(180)
            pygame.draw.line(surface, (*_NS_thorgaruk.PALETTE["arcane_light"], alpha),
                             (rx1, ry1), (rx2, ry2), 1)
            pygame.draw.rect(surface, (*_NS_thorgaruk.PALETTE["arcane_hot"], alpha),
                             (rx2, ry2, 1, 1))
        # Small stun stars circling above (indicating stunned enemies).
        for i in range(3):
            star_angle = phase * 2 + i * (math.pi * 2 / 3)
            sr = 40
            stx = x + int(math.cos(star_angle) * sr)
            sty = core_y - 30 + int(math.sin(star_angle) * 4)
            pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_light"], (stx - 1, sty, 3, 1))
            pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_light"], (stx, sty - 1, 1, 3))
            pygame.draw.rect(surface, _NS_thorgaruk.PALETTE["arcane_shine"], (stx, sty, 1, 1))



# ====================================================================
# ZORATHIEL (ARCANIST) - Mini Boss
# ====================================================================

class _NS_zorathiel:
    """Namespace zorathiel - arcane mystic mage."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (mystic blue-tinted)
        "skin_darkest": (15, 25, 45),
        "skin_dark": (40, 65, 95),
        "skin_mid": (85, 120, 155),
        "skin_light": (150, 180, 210),
        "skin_shine": (210, 230, 245),
        # Robe main (deep purple-blue)
        "robe_darkest": (10, 8, 25),
        "robe_dark": (30, 25, 60),
        "robe_mid": (60, 50, 110),
        "robe_light": (110, 90, 170),
        "robe_edge": (160, 130, 220),
        "robe_shine": (210, 190, 250),
        # Armor plates (dark blue metallic)
        "armor_darkest": (5, 10, 25),
        "armor_dark": (20, 35, 65),
        "armor_mid": (55, 80, 130),
        "armor_light": (110, 145, 195),
        "armor_shine": (180, 210, 240),
        # Gold trim on armor
        "gold_dark": (60, 45, 15),
        "gold_mid": (170, 130, 45),
        "gold_light": (240, 210, 120),
        # HAIR (purple-magenta spiky)
        "hair_darkest": (25, 5, 35),
        "hair_dark": (70, 20, 90),
        "hair_mid": (140, 50, 175),
        "hair_light": (200, 100, 230),
        "hair_shine": (240, 180, 250),
        # ARCANE BLUE MAGIC (signature)
        "arcane_darkest": (5, 20, 60),
        "arcane_dark": (15, 60, 150),
        "arcane_mid": (55, 130, 230),
        "arcane_light": (130, 200, 255),
        "arcane_hot": (200, 235, 255),
        "arcane_shine": (240, 250, 255),
        # Cyan lightning (bright bolt core)
        "bolt_dark": (20, 90, 180),
        "bolt_mid": (100, 190, 255),
        "bolt_light": (200, 240, 255),
        "bolt_shine": (255, 255, 255),
        # Eye (bright cyan glow)
        "eye_socket": (2, 5, 15),
        "eye_dark": (10, 50, 120),
        "eye_mid": (80, 180, 255),
        "eye_light": (200, 240, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zorathiel._clamp(color)
        if _NS_zorathiel.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zorathiel._clamp(color)
        if _NS_zorathiel.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zorathiel._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zorathiel(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_zorathiel._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_zor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_zorathiel._draw_arcane_aura(surface, x, y, pulse)
        _NS_zorathiel._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_zorathiel._draw_pillar_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zorathiel._draw_shield_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zorathiel._draw_traveler_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        # During R (teleport), boss may be dashing/streaking.
        if active_skill == "r" and skill_timer > 20:
            _NS_zorathiel._draw_zor_traveler_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_zorathiel._draw_zor_attack(surface, boss, x, y)
        else:
            _NS_zorathiel._draw_zor_float(surface, boss, x, y)
        # Shield bubble (over body).
        if active_skill == "e":
            _NS_zorathiel._draw_shield_bubble(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_zorathiel._draw_mysticbolt_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zorathiel._draw_pillar_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zorathiel._draw_traveler_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zor_previous_timer", 0))
        active = bool(getattr(boss, "_zor_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._zor_attack_active = True
            boss._zor_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._zor_attack_frame = int(getattr(boss, "_zor_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._zor_attack_active = False
            boss._zor_attack_frame = 0
            active = False
        boss._zor_previous_timer = timer
        boss._zor_attack_progress = (
            min(1.0, getattr(boss, "_zor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_zor_float(surface, boss, x, y):
        """Idle/moving: floating with hover bob + orb hover."""
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_zorathiel._draw_shadow(surface, x, y + 52)
        _NS_zorathiel._draw_arcane_sparks(surface, x, y + 25, boss.pulse)
        _NS_zorathiel._draw_zor_body(surface, x, y - 4 + hover,
                                     boss.direction, boss.pulse, "float", 0)
    def _draw_zor_attack(surface, boss, x, y):
        """Attack: cast pose - both arms forward, orbs energizing."""
        progress = getattr(boss, "_zor_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        # Wind-up + cast forward + recover.
        lean = 0
        lift = 0
        if progress < 0.35:
            t = progress / 0.35
            lean = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 8)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_zorathiel._draw_shadow(surface, x + lean, y + 52)
        _NS_zorathiel._draw_arcane_sparks(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_zorathiel._draw_zor_body(surface, x + lean, y - 4 + hover - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Bolt projectile emerges from front hand.
        _NS_zorathiel._draw_mysticbolt_projectile(surface, boss, x + lean, y - 4 + hover - lift,
                                                  progress)
    def _draw_zor_traveler_body(surface, boss, x, y, skill_timer, pulse):
        """During R skill mid-cast: boss becomes streaking arcane blur."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.6) * 5)
        if progress < 0.35:
            # Charge phase — draw body with intense arcane glow.
            _NS_zorathiel._draw_shadow(surface, x, y + 52)
            _NS_zorathiel._draw_arcane_sparks(surface, x, y + 25, pulse, intense=True)
            _NS_zorathiel._draw_zor_body(surface, x, y - 4 + hover,
                                         boss.direction, pulse, "attack", 0.3)
            # Extra charging aura.
            core_x = x
            core_y = y - 8 + hover
            pulse_mult = math.sin(pulse * 4) * 0.4 + 0.6
            for r in range(int(30 * progress / 0.35), 0, -2):
                alpha = _NS_zorathiel._alpha(140 * pulse_mult * (30 - r) / 30)
                if alpha > 0:
                    _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                            (core_x, core_y), r)
        elif progress < 0.65:
            # DASH phase — draw streak trail, boss as blur.
            t = (progress - 0.35) / 0.30
            tx, ty = _NS_zorathiel._target_position(boss, x, y)
            dash_x = int(x + (tx - x) * t)
            dash_y = int(y + (ty - y) * t)
            # Ghost trail (multiple faded copies).
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                gx = int(x + (tx - x) * trail_t)
                gy = int(y + (ty - y) * trail_t)
                alpha_scale = (1.0 - i / 6) * 0.7
                ghost_surf = pygame.Surface((80, 100), pygame.SRCALPHA)
                _NS_zorathiel._draw_zor_body_to(ghost_surf, 40, 50 + hover,
                                                boss.direction, pulse, "float", 0,
                                                alpha_scale)
                surface.blit(ghost_surf, (gx - 40, gy - 50))
        else:
            # Reappear at target.
            t = (progress - 0.65) / 0.35
            tx, ty = _NS_zorathiel._target_position(boss, x, y)
            _NS_zorathiel._draw_shadow(surface, tx, ty + 52)
            _NS_zorathiel._draw_zor_body(surface, tx, ty - 4 + hover,
                                         boss.direction, pulse, "attack", 0.6)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_zor_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_zorathiel._draw_zor_body_to(surface, cx, cy, facing, phase, action,
                                        attack_progress, 1.0)
    def _draw_zor_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Draw mage body — robe, armor, arms with floating orbs, head with spiky hair."""
        # Chains/tassels behind robe (subtle).
        _NS_zorathiel._draw_robe_trail(surface, cx, cy + 14, facing, phase, alpha_scale)
        # Main robe body.
        _NS_zorathiel._draw_robe_body(surface, cx, cy, facing, phase, alpha_scale)
        # Chest armor plate.
        _NS_zorathiel._draw_chest_armor(surface, cx, cy - 4, facing, phase, alpha_scale)
        # Shoulder pauldrons.
        _NS_zorathiel._draw_shoulder_pauldrons(surface, cx, cy - 8, facing, phase, alpha_scale)
        # Arms + orbs.
        _NS_zorathiel._draw_mage_arms(surface, cx, cy, facing, phase, action,
                                      attack_progress, alpha_scale)
        # Head + spiky hair + face.
        _NS_zorathiel._draw_mage_head(surface, cx, cy - 22, facing, phase, alpha_scale)
    def _draw_robe_trail(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Flowing robe bottom (ethereal, like ghost tail)."""
        alpha_base = int(255 * alpha_scale)
        for i in range(5):
            t = i / 4
            wave = math.sin(phase * 1.0 + i * 0.5) * (3 + i)
            trail_x = cx + int(wave)
            trail_y = cy + int(i * 5)
            width = int(20 - i * 2)
            alpha = int(220 * alpha_scale) - i * 32
            if alpha <= 0:
                continue
            trail_surf = pygame.Surface((width * 2 + 4, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(trail_surf, (*_NS_zorathiel.PALETTE["robe_darkest"], alpha),
                                (0, 0, width * 2, 8))
            pygame.draw.ellipse(trail_surf, (*_NS_zorathiel.PALETTE["robe_dark"], alpha),
                                (2, 1, width * 2 - 4, 6))
            pygame.draw.ellipse(trail_surf, (*_NS_zorathiel.PALETTE["robe_mid"], max(0, alpha - 40)),
                                (4, 2, width * 2 - 8, 4))
            # Purple magic tint.
            pygame.draw.ellipse(trail_surf, (*_NS_zorathiel.PALETTE["robe_light"], max(0, alpha - 80)),
                                (6, 3, width * 2 - 12, 2))
            surface.blit(trail_surf, (trail_x - width, trail_y))
        # Arcane wisps below.
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx + int(math.sin(phase + i) * 12)
            wy = cy + 4 + int(wisp_t * 22)
            alpha = _NS_zorathiel._alpha(180 * (1 - wisp_t) * alpha_scale)
            if alpha > 0:
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                 (wx, wy, 1, 1))
    def _draw_robe_body(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Purple-blue robe torso."""
        alpha_base = int(255 * alpha_scale)
        sway = math.sin(phase * 0.7) * 1
        # Main robe (wider at bottom).
        robe_pts = [
            (cx - 10, cy - 12),
            (cx - 13, cy - 4),
            (cx - 16, cy + 6),
            (cx - 20, cy + 16),
            (cx + 20, cy + 16),
            (cx + 16, cy + 6),
            (cx + 13, cy - 4),
            (cx + 10, cy - 12),
        ]
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"], robe_pts,
                                  alpha_base, offset=(2, 2))
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["robe_darkest"], robe_pts,
                                  alpha_base)
        # Mid tone.
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["robe_dark"], [
            (cx - 9, cy - 11),
            (cx - 12, cy - 3),
            (cx - 14, cy + 6),
            (cx - 17, cy + 14),
            (cx + 17, cy + 14),
            (cx + 14, cy + 6),
            (cx + 12, cy - 3),
            (cx + 9, cy - 11),
        ], alpha_base)
        # Robe center shading.
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["robe_mid"], [
            (cx - 7, cy - 10),
            (cx - 9, cy),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 9, cy),
            (cx + 7, cy - 10),
        ], alpha_base)
        # Cloth folds (vertical dark lines).
        for x_off in (-8, -3, 3, 8):
            pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["robe_darkest"], alpha_base),
                             (cx + x_off, cy - 4),
                             (cx + x_off + int(sway), cy + 14), 1)
        # Robe edge highlights (purple).
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["robe_light"], alpha_base),
                         (cx - 10, cy - 10), (cx - 18, cy + 14), 1)
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["robe_edge"], alpha_base),
                         (cx + 10, cy - 10), (cx + 18, cy + 14), 1)
    def _draw_chest_armor(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Dark blue armor plate on chest with gold trim + arcane gem."""
        alpha_base = int(255 * alpha_scale)
        # Chest plate shape.
        plate_pts = [
            (cx - 8, cy - 4),
            (cx - 9, cy + 2),
            (cx - 7, cy + 8),
            (cx + 7, cy + 8),
            (cx + 9, cy + 2),
            (cx + 8, cy - 4),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ]
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"], plate_pts,
                                  alpha_base, offset=(1, 1))
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_darkest"], plate_pts,
                                  alpha_base)
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy + 2),
            (cx - 6, cy + 7),
            (cx + 6, cy + 7),
            (cx + 8, cy + 2),
            (cx + 7, cy - 3),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ], alpha_base)
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_mid"], [
            (cx - 5, cy - 2),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 2),
        ], alpha_base)
        pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["armor_light"], alpha_base),
                         (cx - 4, cy - 2, 8, 1))
        pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["armor_shine"], alpha_base),
                         (cx - 2, cy - 2, 4, 1))
        # Gold trim edges.
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["gold_dark"], alpha_base),
                         (cx - 8, cy - 4), (cx - 9, cy + 2), 1)
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["gold_mid"], alpha_base),
                         (cx + 8, cy - 4), (cx + 9, cy + 2), 1)
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["gold_mid"], alpha_base),
                         (cx - 5, cy - 6), (cx + 5, cy - 6), 1)
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["gold_light"], alpha_base),
                         (cx - 4, cy - 6), (cx + 4, cy - 6), 1)
        # ARCANE GEM (center of chest).
        gem_y = cy + 3
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_zorathiel._alpha(180 * (6 - r) / 6 * pulse * alpha_scale)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                    (cx, gem_y), r)
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha_base),
                                (cx, gem_y), 3)
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha_base),
                                (cx, gem_y), 2)
        pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_shine"], alpha_base),
                         (cx, gem_y, 1, 1))
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Dark blue spiky pauldrons with gold trim."""
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            base_x = cx + side * 10
            base_y = cy
            # Pauldron shape (angular, pointed outward).
            pad_pts = [
                (base_x, base_y - 2),
                (base_x + side * 6, base_y - 5),
                (base_x + side * 9, base_y - 1),
                (base_x + side * 8, base_y + 5),
                (base_x + side * 2, base_y + 6),
            ]
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"], pad_pts,
                                      alpha_base, offset=(1, 1))
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_darkest"], pad_pts,
                                      alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_dark"], [
                (base_x + side * 1, base_y - 1),
                (base_x + side * 5, base_y - 4),
                (base_x + side * 8, base_y),
                (base_x + side * 7, base_y + 4),
                (base_x + side * 2, base_y + 5),
            ], alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_mid"], [
                (base_x + side * 2, base_y),
                (base_x + side * 4, base_y - 3),
                (base_x + side * 6, base_y - 1),
                (base_x + side * 5, base_y + 2),
                (base_x + side * 3, base_y + 3),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["armor_light"], alpha_base),
                             (base_x + side * 4, base_y - 2, 1, 1))
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["armor_shine"], alpha_base),
                             (base_x + side * 4, base_y - 2, 1, 1))
            # Gold trim.
            pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["gold_mid"], alpha_base),
                             (base_x + side * 6, base_y - 5),
                             (base_x + side * 9, base_y - 1), 1)
            pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["gold_light"], alpha_base),
                             (base_x + side * 7, base_y - 4),
                             (base_x + side * 8, base_y - 2), 1)
            # Spike on top of pauldron.
            spike_tip_x = base_x + side * 5
            spike_tip_y = base_y - 8
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"], [
                (spike_tip_x + 1, spike_tip_y + 1),
                (base_x + side * 3 + 1, base_y - 4 + 1),
                (base_x + side * 7 + 1, base_y - 4 + 1),
            ], alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_darkest"], [
                (spike_tip_x, spike_tip_y),
                (base_x + side * 3, base_y - 4),
                (base_x + side * 7, base_y - 4),
            ], alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["armor_dark"], [
                (spike_tip_x, spike_tip_y),
                (base_x + side * 4, base_y - 4),
                (base_x + side * 6, base_y - 4),
            ], alpha_base)
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha_base),
                             (spike_tip_x, spike_tip_y, 1, 1))
            # Small gem on pauldron.
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha_base),
                             (base_x + side * 4, base_y + 1, 2, 2))
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha_base),
                             (base_x + side * 4, base_y + 1, 1, 1))
    def _draw_mage_arms(surface, cx, cy, facing, phase, action, attack_progress,
                        alpha_scale=1.0):
        """Both arms with floating arcane orbs at hands."""
        alpha_base = int(255 * alpha_scale)
        # Base positions for both hands.
        # Idle: both hands out to sides at hip level.
        # Attack: front hand raises up-forward, casts bolt.
        for side_i, side in enumerate((-1, 1)):
            base_x = cx + side * 10
            base_y = cy - 2
            # Determine hand position based on action.
            is_casting_arm = (side == facing)
            if action == "attack" and is_casting_arm:
                # Front arm raises up during cast.
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    angle_deg = 30 + t * -80  # from down-side to up-forward
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    angle_deg = -50 + t * 40  # thrust forward
                else:
                    t = (attack_progress - 0.6) / 0.4
                    angle_deg = -10 + t * 40  # recover
                angle_rad = math.radians(angle_deg)
                arm_len = 14
                hand_x = base_x + int(math.cos(angle_rad) * arm_len) * side
                hand_y = base_y + int(math.sin(angle_rad) * arm_len)
                # Elbow bent slightly.
                elbow_x = base_x + int(math.cos(angle_rad + 0.3) * arm_len * 0.5) * side
                elbow_y = base_y + int(math.sin(angle_rad + 0.3) * arm_len * 0.5)
            else:
                # Idle: arm angled out to side, orb floating.
                sway = math.sin(phase * 0.7 + side_i * 0.5) * 2
                hand_x = base_x + side * 10 + int(sway)
                hand_y = base_y + 8
                elbow_x = base_x + side * 5
                elbow_y = base_y + 4
            # Upper arm (shoulder to elbow) - robe sleeve.
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"],
                                        (base_x + 1, base_y + 1),
                                        (elbow_x + 1, elbow_y + 1), 5, alpha_base)
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["robe_darkest"],
                                        (base_x, base_y), (elbow_x, elbow_y), 4, alpha_base)
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["robe_dark"],
                                        (base_x, base_y), (elbow_x, elbow_y), 3, alpha_base)
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["robe_mid"],
                                        (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1,
                                        alpha_base)
            # Forearm - robe sleeve + gold cuff at end.
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"],
                                        (elbow_x + 1, elbow_y + 1),
                                        (hand_x + 1, hand_y + 1), 5, alpha_base)
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["robe_darkest"],
                                        (elbow_x, elbow_y), (hand_x, hand_y), 4, alpha_base)
            _NS_zorathiel._aaline_alpha(surface, _NS_zorathiel.PALETTE["robe_dark"],
                                        (elbow_x, elbow_y), (hand_x, hand_y), 3, alpha_base)
            # Gold cuff at wrist.
            _NS_zorathiel._aacircle(surface,
                                    (*_NS_zorathiel.PALETTE["gold_dark"], alpha_base),
                                    (hand_x, hand_y), 3)
            _NS_zorathiel._aacircle(surface,
                                    (*_NS_zorathiel.PALETTE["gold_mid"], alpha_base),
                                    (hand_x, hand_y), 2)
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["gold_light"], alpha_base),
                             (hand_x, hand_y - 1, 1, 1))
            # HAND (skin, blue tint).
            _NS_zorathiel._aacircle(surface,
                                    (*_NS_zorathiel.PALETTE["skin_dark"], alpha_base),
                                    (hand_x, hand_y + 2), 2)
            _NS_zorathiel._aacircle(surface,
                                    (*_NS_zorathiel.PALETTE["skin_mid"], alpha_base),
                                    (hand_x, hand_y + 2), 1)
            # FLOATING ARCANE ORB above/near hand.
            orb_y_offset = -5 if not (action == "attack" and is_casting_arm) else -8
            orb_x = hand_x
            orb_y = hand_y + orb_y_offset
            orb_size = 5 if not (action == "attack" and is_casting_arm) else 7
            _NS_zorathiel._draw_arcane_orb(surface, orb_x, orb_y, orb_size, phase, alpha_scale,
                                           intense=(action == "attack" and is_casting_arm))
            # Small energy connection between hand and orb.
            for k in range(3):
                lx = orb_x + int(math.sin(phase * 4 + k) * 1)
                ly = hand_y + (orb_y - hand_y) * (k + 1) // 4
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha_base),
                                 (lx, ly, 1, 1))
    def _draw_arcane_orb(surface, cx, cy, radius, phase, alpha_scale=1.0, intense=False):
        """Glowing blue arcane orb (electric)."""
        alpha_base = int(255 * alpha_scale)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        strength = 1.5 if intense else 1.0
        # Outer glow halo.
        for r in range(radius + 6, radius, -1):
            alpha = _NS_zorathiel._alpha(140 * pulse * strength * (radius + 6 - r) / 6 * alpha_scale)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                    (cx, cy), r)
        # Orb core (dark to bright).
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha_base),
                                (cx, cy), radius)
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha_base),
                                (cx, cy), radius - 1)
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha_base),
                                (cx, cy), radius - 2)
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha_base),
                                (cx, cy), max(1, radius - 3))
        _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_hot"], alpha_base),
                                (cx, cy), max(1, radius - 4))
        pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_shine"], alpha_base),
                         (cx, cy, 1, 1))
        pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["white"], alpha_base),
                         (cx, cy, 1, 1))
        # Electric arcs around orb.
        num_arcs = 4 if intense else 3
        for i in range(num_arcs):
            arc_angle = phase * 3 + i * (math.pi * 2 / num_arcs)
            end_r = radius + 2 + int(math.sin(phase * 5 + i) * 2)
            ax = cx + int(math.cos(arc_angle) * end_r)
            ay = cy + int(math.sin(arc_angle) * end_r)
            # Small lightning zigzag.
            mid_x = cx + int(math.cos(arc_angle) * (end_r - 2))
            mid_y = cy + int(math.sin(arc_angle) * (end_r - 2))
            perp = arc_angle + math.pi / 2
            mid_x += int(math.cos(perp) * 1)
            mid_y += int(math.sin(perp) * 1)
            pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_mid"], alpha_base),
                             (cx, cy), (mid_x, mid_y), 1)
            pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_light"], alpha_base),
                             (mid_x, mid_y), (ax, ay), 1)
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["bolt_shine"], alpha_base),
                             (ax, ay, 1, 1))
    def _draw_mage_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Head with spiky purple hair + blue face + glowing cyan eyes."""
        alpha_base = int(255 * alpha_scale)
        # Head shape.
        head_pts = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 6, cy + 9),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 6, cy + 9),
            (cx + 7, cy + 4),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"], head_pts,
                                  alpha_base, offset=(2, 2))
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["skin_darkest"], head_pts,
                                  alpha_base)
        # Skin mid.
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 5, cy + 8),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
        ], alpha_base)
        # Cheek highlight.
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["skin_mid"], [
            (cx - 3, cy + 2), (cx + 3, cy + 2),
            (cx + 4, cy + 5), (cx + 2, cy + 8),
            (cx - 2, cy + 8), (cx - 4, cy + 5),
        ], alpha_base)
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["skin_light"], [
            (cx - 1, cy + 3), (cx + 1, cy + 3),
            (cx + 1, cy + 5), (cx - 1, cy + 5),
        ], alpha_base)
        # SPIKY PURPLE HAIR on top (multiple spikes).
        # Hair base.
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["hair_darkest"], [
            (cx - 6, cy - 2),
            (cx - 7, cy + 1),
            (cx + 7, cy + 1),
            (cx + 6, cy - 2),
        ], alpha_base)
        _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx + 5, cy - 1),
            (cx + 4, cy + 1),
            (cx - 4, cy + 1),
        ], alpha_base)
        # Multiple hair spikes going UP.
        spikes = [
            (-5, -4, -5, -10, 3),   # far left
            (-2, -3, -3, -14, 5),   # left mid (tallest)
            (1, -3, 2, -13, 5),     # right mid
            (4, -3, 5, -9, 3),      # right
            (0, -3, 0, -12, 4),     # center
        ]
        for i, (base_x, base_y, tip_x, tip_y, width) in enumerate(spikes):
            sway = math.sin(phase * 0.5 + i * 0.4) * 1
            bx = cx + base_x
            by = cy + base_y
            tx = cx + tip_x + int(sway)
            ty = cy + tip_y
            # Spike shape.
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["shadow_deep"], [
                (tx + 1, ty + 1),
                (bx - width + 1, by + 1),
                (bx + width + 1, by + 1),
            ], alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["hair_darkest"], [
                (tx, ty),
                (bx - width, by),
                (bx + width, by),
            ], alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["hair_dark"], [
                (tx, ty),
                (bx - width + 1, by),
                (bx + width - 1, by),
            ], alpha_base)
            _NS_zorathiel._poly_alpha(surface, _NS_zorathiel.PALETTE["hair_mid"], [
                (tx, ty),
                (bx, by - 1),
                (bx + width - 1, by),
            ], alpha_base)
            # Tip highlight.
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["hair_light"], alpha_base),
                             (tx, ty, 1, 1))
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["hair_shine"], alpha_base),
                             (tx, ty, 1, 1))
        # GLOWING CYAN EYES.
        _NS_zorathiel._draw_mage_eyes(surface, cx, cy + 5, phase, alpha_scale)
        # Small nose highlight.
        pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["skin_light"], alpha_base),
                         (cx, cy + 7, 1, 1))
        # Mouth (small grim line).
        pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["skin_darkest"], alpha_base),
                         (cx - 2, cy + 10), (cx + 2, cy + 10), 1)
    def _draw_mage_eyes(surface, cx, cy, phase, alpha_scale=1.0):
        """Bright cyan glowing eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            # Socket.
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo.
            for r in range(5, 0, -1):
                a = _NS_zorathiel._alpha(140 * (5 - r) / 5 * pulse * alpha_scale)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], a),
                                        (ex, ey), r)
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["eye_mid"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["eye_light"], alpha_base),
                             (ex, ey, 1, 1))
    # ============================================================
    # HELPERS
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_zorathiel._poly(surface, color, points)
            return
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_zorathiel._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_zorathiel._aaline(surface, color, start, end, width)
            return
        c = _NS_zorathiel._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
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
        pygame.draw.ellipse(shadow, (3, 5, 15, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (20, 60, 130, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_arcane_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_zorathiel._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zorathiel._aacircle(aura, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_zorathiel._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zorathiel._aacircle(aura, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_zorathiel._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zorathiel._aacircle(aura, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating arcane motes.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_zorathiel.PALETTE["arcane_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zorathiel.PALETTE["arcane_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zorathiel.PALETTE["arcane_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_zorathiel.PALETTE["arcane_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_zorathiel.PALETTE["arcane_mid"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_zorathiel.PALETTE["robe_mid"], 180),
                            (40, 24, 90, 14), 1)
        # Rune tick marks.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_zorathiel.PALETTE["arcane_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_zorathiel.PALETTE["arcane_hot"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zorathiel.PALETTE["arcane_hot"],
                                       _NS_zorathiel._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_arcane_sparks(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        # Cloud below.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_zorathiel._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_zorathiel._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising sparks.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_zorathiel._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                    (sx, sy), 3)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Purple wisps (accent).
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 20 + i * 10 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 20)
            alpha = _NS_zorathiel._alpha(180 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["robe_mid"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["robe_light"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # RANGED ATTACK — MYSTIC BOLT PROJECTILE
    # ============================================================
    def _draw_mysticbolt_projectile(surface, boss, x, y, progress):
        """Blue arcane bolt from front hand."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_zorathiel._target_position(boss, x, y)
        # Launch from front hand.
        start_x = x + facing * 20
        start_y = y - 4
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Electric comet trail.
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_zorathiel._alpha(230 - i * 22)
            size = max(1, 7 - i)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                    (px, py), size)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                    (px, py), max(1, size - 3))
            # Lightning sparks around trail.
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["bolt_shine"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright bolt head.
        _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_darkest"], (bx, by), 8)
        _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_dark"], (bx, by), 6)
        _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_mid"], (bx, by), 4)
        _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_light"], (bx, by), 3)
        _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_hot"], (bx, by), 2)
        _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["bolt_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_zorathiel.PALETTE["white"], (bx, by, 1, 1))
        # Radial glow.
        for r in range(12, 3, -2):
            alpha = _NS_zorathiel._alpha(80 * (12 - r) / 12)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                    (bx, by), r)
        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_zorathiel._alpha(240 * (1 - st))
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                    (tx, ty), max(1, radius - 4), 2)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                    (tx, ty), max(1, radius - 10), 1)
            # Lightning burst.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_mid"], alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["bolt_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL: Q - MYSTIC BOLT (enhanced projectile)
    # ============================================================
    def _draw_mysticbolt_skill(surface, boss, x, y, timer, phase):
        """Enhanced version of Mystic Bolt with bigger charge & trail."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zorathiel._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.2:
            # Charge in front hand.
            t = progress / 0.2
            hand_x = x + facing * 20
            hand_y = y - 4 + hover
            cr = int(5 + t * 8)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_zorathiel._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                        (hand_x, hand_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_zorathiel._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_mid"], (hand_x, hand_y),
                                    cr - 2)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_light"], (hand_x, hand_y),
                                    max(1, cr - 4))
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_shine"], (hand_x, hand_y),
                                    max(1, cr - 6))
            # Sparks.
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_zorathiel.PALETTE["bolt_shine"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 24
            start_y = y - 4 + hover
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # LARGER comet trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_zorathiel._alpha(240 - i * 20)
                size = max(1, 10 - i)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                        (px, py), size)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                        (px, py), max(1, size - 3))
                if i < 6:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_zorathiel.PALETTE["bolt_light"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Huge bright head.
            for r in range(16, 3, -2):
                alpha = _NS_zorathiel._alpha(100 * (16 - r) / 16)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                        (bx, by), r)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_darkest"], (bx, by), 11)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_dark"], (bx, by), 9)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_mid"], (bx, by), 6)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_light"], (bx, by), 4)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_hot"], (bx, by), 2)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["bolt_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_zorathiel.PALETTE["white"], (bx, by, 1, 1))
            # Big impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(14 + st * 28)
                alpha = _NS_zorathiel._alpha(240 * (1 - st))
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                        (tx, ty), radius + 4, 3)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                # Lightning arcs.
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_mid"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_light"], alpha),
                                     (tx, ty), (ex, ey), 1)
                    pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["bolt_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: W - ENCHANTED PILLAR
    # ============================================================
    def _draw_pillar_ground(surface, boss, x, y, timer, phase):
        """Rune circle on ground at target."""
        tx, ty = _NS_zorathiel._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r_max = 32
        r = int(r_max * min(1.0, progress * 3))
        if r > 3:
            for i in range(3):
                rr = r - i * 4
                if rr <= 2:
                    continue
                alpha = _NS_zorathiel._alpha(200 - i * 40)
                pygame.draw.ellipse(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                    (tx - rr, ty - rr // 3, rr * 2, rr * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                    (tx - rr + 2, ty - rr // 3 + 1,
                                     rr * 2 - 4, rr * 2 // 3 - 2), 1)
            # Rune markers around ring.
            for i in range(8):
                angle = phase * 0.5 + i * math.pi / 4
                mx = tx + int(math.cos(angle) * r)
                my = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_zorathiel.PALETTE["arcane_light"], (mx, my, 2, 2))
                pygame.draw.rect(surface, _NS_zorathiel.PALETTE["arcane_hot"], (mx, my, 1, 1))
    def _draw_pillar_foreground(surface, boss, x, y, timer, phase):
        """Vertical energy pillar rising at target."""
        tx, ty = _NS_zorathiel._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Ground charging (small warning flash).
            t = progress / 0.15
            alpha = _NS_zorathiel._alpha(200 * t)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                    (tx, ty), int(8 + t * 5), 1)
        else:
            # Pillar rises upward.
            t = min(1.0, (progress - 0.15) / 0.5)
            pillar_h = int(90 * t)
            pillar_top_y = ty - pillar_h
            # Multi-layer beam (thick center, tapered).
            for layer_i, (width, alpha_val) in enumerate([
                (16, 90), (12, 130), (8, 170), (5, 210), (2, 250),
            ]):
                actual_alpha = _NS_zorathiel._alpha(alpha_val * min(1.0, progress * 3))
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_zorathiel.PALETTE["arcane_darkest"],
                    _NS_zorathiel.PALETTE["arcane_dark"],
                    _NS_zorathiel.PALETTE["arcane_mid"],
                    _NS_zorathiel.PALETTE["arcane_light"],
                    _NS_zorathiel.PALETTE["arcane_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, pillar_top_y,
                                  width, pillar_h))
            # Zigzag lightning up the pillar.
            for arrow_i in range(4):
                arrow_t = (phase * 1.5 + arrow_i * 0.25) % 1.0
                ay = ty - int(arrow_t * pillar_h)
                # Small zigzag lightning.
                zig_x = tx + int(math.sin(arrow_t * math.pi * 4) * 4)
                zig_x2 = tx + int(math.cos(arrow_t * math.pi * 4 + 1) * 4)
                pygame.draw.line(surface, _NS_zorathiel.PALETTE["bolt_shine"],
                                 (zig_x, ay - 4), (zig_x2, ay), 1)
                pygame.draw.line(surface, _NS_zorathiel.PALETTE["bolt_shine"],
                                 (zig_x2, ay), (zig_x, ay + 4), 1)
            # Sparkle top.
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_light"],
                                    (tx, pillar_top_y), 5)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_shine"],
                                    (tx, pillar_top_y), 3)
            pygame.draw.rect(surface, _NS_zorathiel.PALETTE["white"], (tx, pillar_top_y, 1, 1))
            # Sparkles rising outside pillar.
            for i in range(8):
                sp_t = (phase * 1 + i * 0.15) % 1.0
                sp_y = ty - int(sp_t * pillar_h)
                sp_x = tx + int(math.sin(phase * 3 + i) * 12)
                alpha = _NS_zorathiel._alpha(200 * (1 - sp_t))
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_hot"], alpha),
                                 (sp_x, sp_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_shine"], alpha),
                                 (sp_x, sp_y, 1, 1))
    # ============================================================
    # SKILL: E - MAGIC SHIELD
    # ============================================================
    def _draw_shield_ground(surface, boss, x, y, timer, phase):
        """Rune circle on ground."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(32 + i * 6 + math.sin(phase * 2) * 3)
            alpha = _NS_zorathiel._alpha(190 - i * 60)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                    (x, y + 44), r, 2)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_hot"], alpha),
                                    (x, y + 44), r, 1)
    def _draw_shield_bubble(surface, boss, x, y, timer, phase):
        """Translucent blue shield bubble around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(phase * 2) * 3
        r = 45 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Multiple ring layers (translucent).
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            _NS_zorathiel._aacircle(bubble, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha_val),
                                    center, r - i, thickness)
            _NS_zorathiel._aacircle(bubble, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha_val),
                                    center, r - i - 1, 1)
        # Hexagonal shield pattern (like octagon rune from ref image).
        for i in range(8):
            a1 = i * math.pi / 4 + phase * 0.5
            a2 = (i + 1) * math.pi / 4 + phase * 0.5
            x1 = center[0] + int(math.cos(a1) * (r - 4))
            y1 = center[1] + int(math.sin(a1) * (r - 4))
            x2 = center[0] + int(math.cos(a2) * (r - 4))
            y2 = center[1] + int(math.sin(a2) * (r - 4))
            pygame.draw.line(bubble, (*_NS_zorathiel.PALETTE["arcane_light"], 200),
                             (x1, y1), (x2, y2), 1)
        # Rotating sparkles along edge.
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_zorathiel.PALETTE["arcane_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_zorathiel.PALETTE["arcane_hot"], (sx, sy, 1, 1))
        # Runic diamonds at 4 cardinal points.
        for i in range(4):
            angle = i * math.pi / 2 + phase * 0.3
            dx = center[0] + int(math.cos(angle) * (r - 2))
            dy = center[1] + int(math.sin(angle) * (r - 2))
            # Diamond shape.
            pygame.draw.polygon(bubble, (*_NS_zorathiel.PALETTE["arcane_hot"], 220), [
                (dx, dy - 3), (dx + 3, dy), (dx, dy + 3), (dx - 3, dy),
            ])
            pygame.draw.polygon(bubble, (*_NS_zorathiel.PALETTE["arcane_shine"], 240), [
                (dx, dy - 2), (dx + 2, dy), (dx, dy + 2), (dx - 2, dy),
            ])
        surface.blit(bubble, (x - r - 10, y - r - 10))
    # ============================================================
    # SKILL: R - FATAL TRAVELER (teleport dash beam)
    # ============================================================
    def _draw_traveler_ground(surface, boss, x, y, timer, phase):
        """Rune circles at boss + target."""
        tx, ty = _NS_zorathiel._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # At boss (fades as she teleports).
        if progress < 0.5:
            fade = 1.0 - progress * 2
            for i in range(2):
                r = int(30 + i * 6)
                alpha = _NS_zorathiel._alpha(200 * fade - i * 50)
                pygame.draw.ellipse(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
        # At target (grows).
        if progress > 0.3:
            grow = min(1.0, (progress - 0.3) / 0.4)
            for i in range(3):
                r = int((25 + i * 6) * grow)
                alpha = _NS_zorathiel._alpha(200 - i * 50)
                pygame.draw.ellipse(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                    (tx - r, ty + 25 - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                    (tx - r + 2, ty + 25 - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)
    def _draw_traveler_foreground(surface, boss, x, y, timer, phase):
        """Massive electric beam from boss to target during dash."""
        tx, ty = _NS_zorathiel._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.35:
            # Charge phase - orb between hands charging.
            t = progress / 0.35
            hover = int(math.sin(phase * 0.6) * 5)
            core_x = x
            core_y = y - 8 + hover
            cr = int(6 + t * 12)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_zorathiel._alpha(200 * (cr + 8 - r) / (cr + 8))
                _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], alpha),
                                        (core_x, core_y), r)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_dark"], (core_x, core_y),
                                    cr)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_mid"], (core_x, core_y),
                                    cr - 2)
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_light"], (core_x, core_y),
                                    max(1, cr - 4))
            _NS_zorathiel._aacircle(surface, _NS_zorathiel.PALETTE["arcane_shine"], (core_x, core_y),
                                    max(1, cr - 6))
            pygame.draw.rect(surface, _NS_zorathiel.PALETTE["white"], (core_x, core_y, 1, 1))
            # Lightning sparks around.
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                sx = core_x + int(math.cos(angle) * (cr + 5))
                sy = core_y + int(math.sin(angle) * (cr + 5))
                pygame.draw.line(surface, _NS_zorathiel.PALETTE["bolt_light"],
                                 (core_x, core_y), (sx, sy), 1)
                pygame.draw.rect(surface, _NS_zorathiel.PALETTE["bolt_shine"], (sx, sy, 2, 2))
        elif progress < 0.65:
            # BEAM PHASE - massive horizontal lightning beam from start to target.
            t = (progress - 0.35) / 0.30
            intensity = math.sin(t * math.pi)
            hover = int(math.sin(phase * 0.6) * 5)
            start_x = x
            start_y = y - 8 + hover
            # Compute beam path.
            beam_len = int(math.hypot(tx - start_x, ty - start_y))
            angle = math.atan2(ty - start_y, tx - start_x)
            perp_angle = angle + math.pi / 2
            # Multi-layer beam.
            for layer_i, (width, alpha_val) in enumerate([
                (16, 80), (12, 120), (8, 160), (5, 200), (2, 250),
            ]):
                actual_alpha = _NS_zorathiel._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_zorathiel.PALETTE["arcane_darkest"],
                    _NS_zorathiel.PALETTE["arcane_dark"],
                    _NS_zorathiel.PALETTE["arcane_mid"],
                    _NS_zorathiel.PALETTE["arcane_light"],
                    _NS_zorathiel.PALETTE["arcane_shine"],
                ]
                color = colors[min(layer_i, 4)]
                # Draw beam as thick line.
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (tx, ty), width)
            # Zigzag lightning along beam.
            for zz_i in range(6):
                zz_t = zz_i / 6
                base_x = int(start_x + (tx - start_x) * zz_t)
                base_y = int(start_y + (ty - start_y) * zz_t)
                # Zigzag offset perpendicular.
                zz_offset = math.sin(phase * 6 + zz_i) * 6
                zx = base_x + int(math.cos(perp_angle) * zz_offset)
                zy = base_y + int(math.sin(perp_angle) * zz_offset)
                next_t = (zz_i + 1) / 6
                next_base_x = int(start_x + (tx - start_x) * next_t)
                next_base_y = int(start_y + (ty - start_y) * next_t)
                next_zz_offset = math.sin(phase * 6 + zz_i + 1) * 6
                nzx = next_base_x + int(math.cos(perp_angle) * next_zz_offset)
                nzy = next_base_y + int(math.sin(perp_angle) * next_zz_offset)
                pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_shine"],
                                           _NS_zorathiel._alpha(255 * intensity)),
                                 (zx, zy), (nzx, nzy), 2)
                pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["white"],
                                           _NS_zorathiel._alpha(255 * intensity)),
                                 (zx, zy), (nzx, nzy), 1)
            # Sparkles along beam.
            for i in range(20):
                sp_t = (phase * 2 + i * 0.05) % 1.0
                sp_x = int(start_x + (tx - start_x) * sp_t)
                sp_y = int(start_y + (ty - start_y) * sp_t)
                sp_off = math.sin(phase * 4 + i) * 8
                sp_x += int(math.cos(perp_angle) * sp_off)
                sp_y += int(math.sin(perp_angle) * sp_off)
                alpha = _NS_zorathiel._alpha(240 * intensity)
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["bolt_shine"], alpha),
                                 (sp_x, sp_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["white"], alpha),
                                 (sp_x, sp_y, 1, 1))
            # Big impact at target.
            impact_r = int(15 + t * 20)
            impact_alpha = _NS_zorathiel._alpha(240 * intensity)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_darkest"], impact_alpha),
                                    (tx, ty), impact_r + 3, 3)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], impact_alpha),
                                    (tx, ty), impact_r, 3)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_mid"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 6), 2)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_light"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 12), 1)
            _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_shine"], impact_alpha),
                                    (tx, ty), max(1, impact_r // 4))
            # Radial lightning burst.
            for i in range(12):
                a = i * math.pi / 6
                ex = tx + int(math.cos(a) * impact_r)
                ey = ty + int(math.sin(a) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_zorathiel.PALETTE["bolt_shine"], impact_alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["white"], impact_alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath - lingering sparkles at target.
            t = (progress - 0.65) / 0.35
            for i in range(12):
                s_t = (phase * 0.8 + i * 0.08) % 1.0
                sx = tx + int(math.sin(phase + i) * 20)
                sy = ty - int(s_t * 25)
                alpha = _NS_zorathiel._alpha(200 * (1 - t) * (1 - s_t))
                if alpha > 0:
                    _NS_zorathiel._aacircle(surface, (*_NS_zorathiel.PALETTE["arcane_dark"], alpha),
                                            (sx, sy), 2)
                    pygame.draw.rect(surface, (*_NS_zorathiel.PALETTE["arcane_light"], alpha),
                                     (sx, sy, 1, 1))



# ====================================================================
# LYSSARETHYS (HEARTBANE) - TRUE BOSS
# ====================================================================

class _NS_lyssarethys:
    """Namespace lyssarethys - succubus mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale demonic purple-blue tint)
        "skin_darkest": (30, 20, 40),
        "skin_dark": (75, 55, 90),
        "skin_mid": (130, 105, 145),
        "skin_light": (190, 165, 200),
        "skin_shine": (230, 210, 235),
        # Latex/leather outfit (dark purple-black gloss)
        "cloth_darkest": (8, 4, 15),
        "cloth_dark": (28, 18, 40),
        "cloth_mid": (55, 35, 75),
        "cloth_light": (100, 70, 130),
        "cloth_shine": (170, 130, 200),
        # HAIR (magenta/pink)
        "hair_darkest": (55, 8, 35),
        "hair_dark": (110, 20, 70),
        "hair_mid": (175, 40, 110),
        "hair_light": (230, 90, 160),
        "hair_shine": (255, 170, 210),
        # MAGENTA/PINK MAGIC (signature color)
        "magic_darkest": (40, 5, 25),
        "magic_dark": (110, 15, 70),
        "magic_mid": (200, 40, 130),
        "magic_light": (255, 100, 190),
        "magic_hot": (255, 180, 230),
        "magic_shine": (255, 230, 245),
        # Eye (bright magenta glow)
        "eye_socket": (10, 2, 8),
        "eye_dark": (100, 10, 50),
        "eye_mid": (220, 40, 130),
        "eye_light": (255, 130, 200),
        "eye_glow": (255, 220, 240),
        # Whip tentacles (dark with pink barbs)
        "whip_dark": (15, 5, 20),
        "whip_mid": (55, 25, 65),
        "whip_edge": (110, 60, 130),
        # Purple accent (deep shadow magic)
        "shade_darkest": (12, 5, 20),
        "shade_dark": (35, 15, 55),
        "shade_mid": (70, 35, 100),
        "shade_light": (140, 90, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_lyssarethys._clamp(color)
        if _NS_lyssarethys.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_lyssarethys._clamp(color)
        if _NS_lyssarethys.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_lyssarethys._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_lyssarethys(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_lyssarethys._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_lys_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient.
        _NS_lyssarethys._draw_shade_aura(surface, x, y, pulse)
        _NS_lyssarethys._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "r":
            _NS_lyssarethys._draw_lastcaress_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_lyssarethys._draw_allure_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        # During R, boss may be "vanishing" - draw as shadow.
        if active_skill == "r":
            _NS_lyssarethys._draw_lys_lastcaress_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_lyssarethys._draw_lys_attack(surface, boss, x, y)
        else:
            _NS_lyssarethys._draw_lys_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_lyssarethys._draw_hatespike_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_lyssarethys._draw_allure_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_lyssarethys._draw_whiplash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_lyssarethys._draw_lastcaress_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_lys_previous_timer", 0))
        active = bool(getattr(boss, "_lys_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._lys_attack_active = True
            boss._lys_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._lys_attack_frame = int(getattr(boss, "_lys_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._lys_attack_active = False
            boss._lys_attack_frame = 0
            active = False
        boss._lys_previous_timer = timer
        boss._lys_attack_progress = (
            min(1.0, getattr(boss, "_lys_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_lys_float(surface, boss, x, y):
        """Idle / hover — floating pose."""
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_lyssarethys._draw_shadow(surface, x, y + 52)
        _NS_lyssarethys._draw_shadow_wisps(surface, x, y + 25, boss.pulse)
        _NS_lyssarethys._draw_lys_body(surface, x, y - 4 + hover,
                                       boss.direction, boss.pulse, "float", 0)
    def _draw_lys_attack(surface, boss, x, y):
        """Attack: WHIP SWING melee (tentacle lash)."""
        progress = getattr(boss, "_lys_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        hover = int(math.sin(boss.pulse * 0.6) * 5)
        # Body lean.
        lean = 0
        if progress < 0.35:
            t = progress / 0.35
            lean = -int(t * 3) * boss.direction  # pull back
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 8)) * boss.direction  # forward swing
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * boss.direction
        _NS_lyssarethys._draw_shadow(surface, x + lean, y + 52)
        _NS_lyssarethys._draw_shadow_wisps(surface, x + lean, y + 25, boss.pulse, intense=True)
        _NS_lyssarethys._draw_lys_body(surface, x + lean, y - 4 + hover,
                                       boss.direction, boss.pulse, "attack", progress)
        # Whip swing trail overlay.
        _NS_lyssarethys._draw_whip_swing_arc(surface, boss, x + lean, y + hover, progress)
    def _draw_lys_lastcaress_body(surface, boss, x, y, skill_timer, pulse):
        """During R skill: body vanishes → shadow phase → reappears at target."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - skill_timer / duration))
        hover = int(math.sin(pulse * 0.6) * 5)
        if progress < 0.25:
            # Fade out — dissolve into shadow.
            t = progress / 0.25
            alpha_scale = 1.0 - t
            _NS_lyssarethys._draw_shadow(surface, x, y + 52)
            # Ghost body (fading).
            ghost_surf = pygame.Surface((100, 120), pygame.SRCALPHA)
            _NS_lyssarethys._draw_lys_body_to(ghost_surf, 50, 60 + hover,
                                              boss.direction, pulse, "float", 0,
                                              alpha_scale)
            surface.blit(ghost_surf, (x - 50, y - 60))
            # Rising shadow smoke.
            for i in range(8):
                sy_off = int(t * 30) + int(math.sin(pulse + i) * 6)
                sx_off = int(math.sin(i * 0.8) * 12)
                salpha = _NS_lyssarethys._alpha(200 * t)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["shade_dark"], salpha),
                                          (x + sx_off, y + hover - sy_off), 4)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["shade_mid"], salpha),
                                          (x + sx_off, y + hover - sy_off), 2)
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], salpha),
                                 (x + sx_off, y + hover - sy_off, 1, 1))
        elif progress < 0.55:
            # Shadow dash phase — only shadow silhouette between boss & target.
            t = (progress - 0.25) / 0.30
            tx, ty = _NS_lyssarethys._target_position(boss, x, y)
            dash_x = int(x + (tx - x) * t)
            dash_y = int(y + (ty - y) * t)
            # Shadow silhouette (running pose).
            _NS_lyssarethys._draw_shadow_silhouette(surface, dash_x, dash_y + hover,
                                                    boss.direction, pulse)
            # Trailing shadow.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.08)
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t)
                talpha = _NS_lyssarethys._alpha(180 - i * 30)
                _NS_lyssarethys._draw_shadow_silhouette_trail(surface, px, py + hover,
                                                              boss.direction, talpha)
        elif progress < 0.7:
            # Reappear at target with burst.
            t = (progress - 0.55) / 0.15
            tx, ty = _NS_lyssarethys._target_position(boss, x, y)
            alpha_scale = t
            _NS_lyssarethys._draw_shadow(surface, tx, ty + 30)
            ghost_surf = pygame.Surface((100, 120), pygame.SRCALPHA)
            _NS_lyssarethys._draw_lys_body_to(ghost_surf, 50, 60 + hover,
                                              -boss.direction, pulse, "attack", 0.55,
                                              alpha_scale)
            surface.blit(ghost_surf, (tx - 50, ty - 30 - 60))
        else:
            # Full reappeared, striking pose.
            tx, ty = _NS_lyssarethys._target_position(boss, x, y)
            _NS_lyssarethys._draw_shadow(surface, tx, ty + 30)
            _NS_lyssarethys._draw_lys_body(surface, tx, ty - 30 + hover,
                                           -boss.direction, pulse, "attack", 0.6)
    # ============================================================
    # BODY (with alpha_scale support for phasing)
    # ============================================================
    def _draw_lys_body(surface, cx, cy, facing, phase, action, attack_progress):
        _NS_lyssarethys._draw_lys_body_to(surface, cx, cy, facing, phase, action,
                                          attack_progress, 1.0)
    def _draw_lys_body_to(surface, cx, cy, facing, phase, action, attack_progress,
                          alpha_scale=1.0):
        """Main body draw with optional alpha (for phasing R skill)."""
        # WHIP TENTACLES (behind body - from back/shoulders).
        _NS_lyssarethys._draw_whip_tentacles(surface, cx, cy - 4, facing, phase, action,
                                             attack_progress, alpha_scale)
        # Long flowing HAIR (behind body).
        _NS_lyssarethys._draw_flowing_hair(surface, cx, cy - 26, facing, phase, alpha_scale)
        # Legs (thigh + boots).
        _NS_lyssarethys._draw_lys_legs(surface, cx, cy + 8, facing, phase, alpha_scale)
        # Torso (corset/latex).
        _NS_lyssarethys._draw_lys_torso(surface, cx, cy, facing, phase, alpha_scale)
        # Arms.
        _NS_lyssarethys._draw_lys_arms(surface, cx, cy, facing, phase, action,
                                       attack_progress, alpha_scale)
        # Head (face + eyes + hair front bangs).
        _NS_lyssarethys._draw_lys_head(surface, cx, cy - 22, facing, phase, alpha_scale)
    def _draw_flowing_hair(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Long magenta hair flowing back (main volume behind head)."""
        sway = math.sin(phase * 0.8) * 3
        # Main hair volume (thick shape behind head).
        hair_pts = [
            (cx - 12, cy - 4),
            (cx - 15 + int(sway), cy + 2),
            (cx - 18 + int(sway), cy + 12),
            (cx - 16 + int(sway), cy + 22),
            (cx - 12 + int(sway * 1.5), cy + 32),
            (cx - 6 + int(sway * 1.5), cy + 38),
            (cx + 2, cy + 40),
            (cx + 10, cy + 34),
            (cx + 12, cy + 22),
            (cx + 10, cy + 8),
            (cx + 12, cy - 4),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        alpha_base = int(255 * alpha_scale)
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"], hair_pts,
                                    alpha_base, offset=(2, 3))
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["hair_darkest"], hair_pts,
                                    alpha_base)
        # Mid tone.
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["hair_dark"], [
            (cx - 10, cy - 3),
            (cx - 13 + int(sway), cy + 4),
            (cx - 16 + int(sway), cy + 14),
            (cx - 13 + int(sway * 1.5), cy + 26),
            (cx - 6, cy + 34),
            (cx + 4, cy + 34),
            (cx + 9, cy + 24),
            (cx + 10, cy + 10),
            (cx + 10, cy - 3),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ], alpha_base)
        # Hair strands (magenta highlights).
        for i in range(4):
            strand_x_off = -8 + i * 5
            strand_wave = math.sin(phase * 0.8 + i) * 2
            sx1 = cx + strand_x_off
            sy1 = cy - 3
            sx2 = cx + strand_x_off + int(strand_wave) - facing * 2
            sy2 = cy + 20
            sx3 = cx + strand_x_off + int(strand_wave * 2) - facing * 3
            sy3 = cy + 30
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["hair_mid"],
                                          (sx1, sy1), (sx2, sy2), 2, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["hair_light"],
                                          (sx2, sy2), (sx3, sy3), 1, alpha_base)
        # Ponytail streaks.
        for i, (dx, dy) in enumerate([(-4, 5), (0, 8), (4, 5), (-2, 15), (2, 15)]):
            pygame.draw.line(surface, _NS_lyssarethys.PALETTE["hair_light"],
                             (cx + dx, cy + dy), (cx + dx, cy + dy + 3), 1)
        # Highlight sheen on top.
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["hair_mid"], [
            (cx - 6, cy - 6), (cx + 6, cy - 6),
            (cx + 4, cy - 2), (cx - 4, cy - 2),
        ], alpha_base)
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["hair_shine"],
                         (cx - 2, cy - 6, 2, 1))
    def _draw_lys_head(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Face with magenta glowing eyes + demon horns/spikes."""
        # Head shape (feminine oval).
        head_pts = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 6, cy + 9),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 6, cy + 9),
            (cx + 7, cy + 4),
            (cx + 6, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        alpha_base = int(255 * alpha_scale)
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"], head_pts,
                                    alpha_base, offset=(2, 2))
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["skin_darkest"], head_pts,
                                    alpha_base)
        # Skin mid tone.
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 5, cy + 8),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
        ], alpha_base)
        # Skin light (cheek highlight).
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["skin_mid"], [
            (cx - 3, cy + 2), (cx + 3, cy + 2),
            (cx + 4, cy + 5), (cx + 2, cy + 8),
            (cx - 2, cy + 8), (cx - 4, cy + 5),
        ], alpha_base)
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["skin_light"], [
            (cx - 1, cy + 3), (cx + 1, cy + 3),
            (cx + 1, cy + 5), (cx - 1, cy + 5),
        ], alpha_base)
        # Front bangs (magenta hair over forehead).
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["hair_darkest"], [
            (cx - 6, cy - 3), (cx - 5, cy + 1), (cx - 2, cy + 2),
            (cx + 2, cy + 2), (cx + 5, cy + 1), (cx + 6, cy - 3),
            (cx + 3, cy - 3), (cx - 3, cy - 3),
        ], alpha_base)
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["hair_dark"], [
            (cx - 5, cy - 2), (cx - 3, cy + 1), (cx + 3, cy + 1),
            (cx + 5, cy - 2), (cx + 2, cy - 2), (cx - 2, cy - 2),
        ], alpha_base)
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["hair_mid"], (cx - 2, cy - 2, 4, 1))
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["hair_light"], (cx, cy - 2, 1, 1))
        # DEMON HORNS on sides (small curved spikes).
        for side in (-1, 1):
            horn_x = cx + side * 6
            horn_tip_x = cx + side * 9
            horn_tip_y = cy - 4
            _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["cloth_darkest"], [
                (horn_x, cy - 1), (horn_x, cy + 2), (horn_tip_x, horn_tip_y),
            ], alpha_base)
            _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["cloth_dark"], [
                (horn_x, cy), (horn_x + side, cy + 1),
                (horn_tip_x - side, horn_tip_y + 1),
            ], alpha_base)
            pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_light"],
                             (horn_tip_x, horn_tip_y, 1, 1))
        # GLOWING MAGENTA EYES.
        _NS_lyssarethys._draw_magenta_eyes(surface, cx, cy + 4, phase, alpha_scale)
        # Lips (magenta lipstick, small smirk).
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_dark"], (cx - 1, cy + 9, 3, 1))
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_mid"], (cx, cy + 9, 2, 1))
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_light"], (cx + 1, cy + 9, 1, 1))
    def _draw_magenta_eyes(surface, cx, cy, phase, alpha_scale=1.0):
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_base = int(255 * alpha_scale)
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy
            # Deep socket.
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["eye_socket"], alpha_base),
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo.
            for r in range(5, 0, -1):
                a = _NS_lyssarethys._alpha(120 * (5 - r) / 5 * pulse * alpha_scale)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["eye_mid"], a),
                                          (ex, ey), r)
            # Bright core.
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["eye_light"], alpha_base),
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["eye_glow"], alpha_base),
                             (ex, ey, 1, 1))
    def _draw_lys_torso(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Corset/latex torso — hourglass shape."""
        alpha_base = int(255 * alpha_scale)
        # Torso shape (hourglass with narrow waist).
        torso_pts = [
            (cx - 9, cy - 9),   # top-left shoulder
            (cx - 10, cy - 4),
            (cx - 7, cy),       # waist narrow
            (cx - 6, cy + 4),
            (cx - 8, cy + 9),   # hip
            (cx + 8, cy + 9),
            (cx + 6, cy + 4),
            (cx + 7, cy),
            (cx + 10, cy - 4),
            (cx + 9, cy - 9),
            (cx + 5, cy - 11),  # neckline
            (cx - 5, cy - 11),
        ]
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"], torso_pts,
                                    alpha_base, offset=(2, 2))
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["cloth_darkest"], torso_pts,
                                    alpha_base)
        # Mid tone.
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["cloth_dark"], [
            (cx - 8, cy - 8),
            (cx - 9, cy - 4),
            (cx - 6, cy),
            (cx - 5, cy + 4),
            (cx - 7, cy + 8),
            (cx + 7, cy + 8),
            (cx + 5, cy + 4),
            (cx + 6, cy),
            (cx + 9, cy - 4),
            (cx + 8, cy - 8),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ], alpha_base)
        # Bust curve highlight.
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["cloth_mid"], [
            (cx - 5, cy - 7), (cx - 2, cy - 5), (cx - 2, cy - 2),
            (cx + 2, cy - 2), (cx + 2, cy - 5), (cx + 5, cy - 7),
        ], alpha_base)
        # Latex sheen (bright vertical stripe).
        pygame.draw.line(surface, _NS_lyssarethys.PALETTE["cloth_shine"],
                         (cx - 3, cy - 5), (cx - 4, cy + 6), 1)
        pygame.draw.line(surface, _NS_lyssarethys.PALETTE["cloth_shine"],
                         (cx + 3, cy - 5), (cx + 4, cy + 6), 1)
        # Skin décolletage (chest showing).
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["skin_dark"], [
            (cx - 3, cy - 10), (cx + 3, cy - 10),
            (cx + 2, cy - 7), (cx - 2, cy - 7),
        ], alpha_base)
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["skin_mid"], (cx - 1, cy - 9, 2, 1))
        pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["skin_light"], (cx, cy - 9, 1, 1))
        # Magenta gem/glow on chest (center).
        gem_y = cy - 4
        for r in range(4, 0, -1):
            alpha = _NS_lyssarethys._alpha(180 * (4 - r) / 4 * alpha_scale)
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha),
                                      (cx, gem_y), r)
        pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha_base),
                         (cx - 1, gem_y - 1, 3, 2))
        pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha_base),
                         (cx, gem_y - 1, 2, 1))
        pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_shine"], alpha_base),
                         (cx, gem_y - 1, 1, 1))
    def _draw_lys_arms(surface, cx, cy, facing, phase, action, attack_progress,
                       alpha_scale=1.0):
        """Two arms — one may whip in attack, other on hip."""
        alpha_base = int(255 * alpha_scale)
        # LEFT arm (rear-facing, on hip).
        opp = -facing
        arm_l_base = (cx + opp * 8, cy - 6)
        sway = math.sin(phase * 0.5) * 1
        arm_l_hand = (cx + opp * 10, cy + 4 + int(sway))
        _NS_lyssarethys._draw_arm_segment(surface, arm_l_base, arm_l_hand, alpha_base)
        # RIGHT arm (facing side): swings during attack (holds whip source).
        swing_side = facing
        arm_r_base = (cx + swing_side * 8, cy - 6)
        # Swing angles.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up (arm goes back).
                t = attack_progress / 0.35
                angle_deg = -30 - t * 90  # back over head
            elif attack_progress < 0.6:
                # Forward whip.
                t = (attack_progress - 0.35) / 0.25
                angle_deg = -120 + t * 200  # sweep forward
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                angle_deg = 80 - t * 110
            angle_rad = math.radians(angle_deg)
            arm_len = 14
            arm_r_hand = (arm_r_base[0] + int(math.cos(angle_rad) * arm_len) * swing_side,
                          arm_r_base[1] + int(math.sin(angle_rad) * arm_len))
        else:
            arm_r_hand = (cx + swing_side * 12, cy + 4)
        _NS_lyssarethys._draw_arm_segment(surface, arm_r_base, arm_r_hand, alpha_base)
        # Claw hand tips (small pink glow at fingertips).
        for hand_pos in (arm_l_hand, arm_r_hand):
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["skin_darkest"], alpha_base),
                                      hand_pos, 2)
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["skin_dark"], alpha_base),
                                      hand_pos, 1)
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha_base),
                             (hand_pos[0], hand_pos[1] - 1, 1, 1))
    def _draw_arm_segment(surface, start, end, alpha_base):
        """Slim arm with latex sleeve."""
        _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                      (start[0] + 1, start[1] + 1),
                                      (end[0] + 1, end[1] + 1), 4, alpha_base)
        _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["cloth_darkest"],
                                      start, end, 3, alpha_base)
        _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["cloth_dark"],
                                      start, end, 2, alpha_base)
        _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["cloth_mid"],
                                      (start[0], start[1] - 1), (end[0], end[1] - 1), 1,
                                      alpha_base)
    def _draw_lys_legs(surface, cx, cy, facing, phase, alpha_scale=1.0):
        """Legs with thigh-high boots (partial - since floating, legs are curved back)."""
        alpha_base = int(255 * alpha_scale)
        # Since floating, legs dangle/curl slightly.
        sway = math.sin(phase * 0.8) * 2
        for side in (-1, 1):
            hip_x = cx + side * 4
            hip_y = cy
            knee_x = cx + side * 5 + int(sway * 0.5)
            knee_y = cy + 12
            foot_x = cx + side * 3 + int(sway)
            foot_y = cy + 22
            # Thigh (bare skin — or latex).
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                          (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1),
                                          5, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["skin_darkest"],
                                          (hip_x, hip_y), (knee_x, knee_y), 4, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["skin_dark"],
                                          (hip_x, hip_y), (knee_x, knee_y), 3, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["skin_mid"],
                                          (hip_x, hip_y - 1), (knee_x, knee_y - 1), 1,
                                          alpha_base)
            # Boot (latex, black).
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                          (knee_x + 1, knee_y + 1), (foot_x + 1, foot_y + 1),
                                          5, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["cloth_darkest"],
                                          (knee_x, knee_y), (foot_x, foot_y), 4, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["cloth_dark"],
                                          (knee_x, knee_y), (foot_x, foot_y), 3, alpha_base)
            _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["cloth_mid"],
                                          (knee_x - side, knee_y), (foot_x - side, foot_y), 1,
                                          alpha_base)
            # Boot heel spike.
            pygame.draw.line(surface, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha_base),
                             (foot_x, foot_y), (foot_x + side * 2, foot_y + 3), 1)
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha_base),
                             (foot_x + side * 2, foot_y + 3, 1, 1))
    # ============================================================
    # WHIP TENTACLES (back accessory - dynamic)
    # ============================================================
    def _draw_whip_tentacles(surface, cx, cy, facing, phase, action, attack_progress,
                             alpha_scale=1.0):
        """Two whip-like tentacles from her back with sharp arrow-tips."""
        alpha_base = int(255 * alpha_scale)
        # Two tentacles: one curled up, one out.
        for i, (side, base_angle_deg, curl_offset) in enumerate([
            (-1, 130, 0),
            (1, 50, 0.5),
        ]):
            # Base at shoulder blade area.
            base_x = cx + side * 6
            base_y = cy + 2
            # If attacking, whip lashes forward.
            if action == "attack" and i == 0:  # first tentacle swings
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    angle_offset = -40 * t
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    angle_offset = -40 + t * 180
                else:
                    t = (attack_progress - 0.6) / 0.4
                    angle_offset = 140 * (1 - t)
                base_angle = math.radians(base_angle_deg + angle_offset * facing)
            else:
                # Idle: gentle wave.
                wave = math.sin(phase * 0.7 + curl_offset) * 15
                base_angle = math.radians(base_angle_deg + wave)
            # Draw tentacle as curve segments.
            segments = 8
            points = [(base_x, base_y)]
            for k in range(1, segments + 1):
                t_seg = k / segments
                seg_len = 5
                # Add wave curl.
                curl = math.sin(phase * 1.2 + k * 0.5 + curl_offset) * (2 + t_seg * 3)
                angle_at_k = base_angle + math.radians(curl * 8)
                last_x, last_y = points[-1]
                nx = last_x + math.cos(angle_at_k) * seg_len
                ny = last_y - math.sin(angle_at_k) * seg_len
                points.append((int(nx), int(ny)))
            # Draw segments with taper.
            for k in range(len(points) - 1):
                thickness = max(1, 5 - k // 2)
                _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                              (points[k][0] + 1, points[k][1] + 1),
                                              (points[k + 1][0] + 1, points[k + 1][1] + 1),
                                              thickness + 1, alpha_base)
                _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["whip_dark"],
                                              points[k], points[k + 1], thickness, alpha_base)
                _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["whip_mid"],
                                              points[k], points[k + 1], max(1, thickness - 1),
                                              alpha_base)
                # Pink edge highlight.
                _NS_lyssarethys._aaline_alpha(surface, _NS_lyssarethys.PALETTE["whip_edge"],
                                              (points[k][0], points[k][1] - 1),
                                              (points[k + 1][0], points[k + 1][1] - 1), 1,
                                              alpha_base)
                # Small barb.
                if k % 2 == 1 and k < len(points) - 1:
                    bp = points[k]
                    pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha_base),
                                     (bp[0], bp[1] - 1, 1, 1))
                    pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha_base),
                                     (bp[0], bp[1], 1, 1))
            # ARROW/BLADE TIP at end (large magenta spike).
            if len(points) >= 2:
                end = points[-1]
                prev = points[-2]
                tip_angle = math.atan2(end[1] - prev[1], end[0] - prev[0])
                tip_len = 8
                tip_end = (end[0] + int(math.cos(tip_angle) * tip_len),
                           end[1] + int(math.sin(tip_angle) * tip_len))
                perp = tip_angle + math.pi / 2
                base_a = (end[0] + int(math.cos(perp) * 3),
                          end[1] + int(math.sin(perp) * 3))
                base_b = (end[0] - int(math.cos(perp) * 3),
                          end[1] - int(math.sin(perp) * 3))
                _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                            [(tip_end[0] + 1, tip_end[1] + 1),
                                             (base_a[0] + 1, base_a[1] + 1),
                                             (base_b[0] + 1, base_b[1] + 1)], alpha_base)
                _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["magic_darkest"],
                                            [tip_end, base_a, base_b], alpha_base)
                _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["magic_dark"], [
                    tip_end,
                    (int((tip_end[0] + base_a[0]) / 2), int((tip_end[1] + base_a[1]) / 2)),
                    end,
                    (int((tip_end[0] + base_b[0]) / 2), int((tip_end[1] + base_b[1]) / 2)),
                ], alpha_base)
                _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["magic_mid"], [
                    tip_end, end,
                    (int((end[0] + base_a[0]) / 2), int((end[1] + base_a[1]) / 2)),
                ], alpha_base)
                # Glowing tip.
                _NS_lyssarethys._aacircle(surface,
                                          (*_NS_lyssarethys.PALETTE["magic_light"], alpha_base),
                                          tip_end, 2)
                _NS_lyssarethys._aacircle(surface,
                                          (*_NS_lyssarethys.PALETTE["magic_shine"], alpha_base),
                                          tip_end, 1)
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["white"], alpha_base),
                                 (tip_end[0], tip_end[1], 1, 1))
    # ============================================================
    # WHIP SWING ARC (attack visual)
    # ============================================================
    def _draw_whip_swing_arc(surface, boss, x, y, progress):
        """Motion trail arc when whip swings forward."""
        if not (0.4 <= progress <= 0.7):
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.3
        # Arc center at boss.
        cx = x
        cy = y - 4
        radius = 30
        # Arc sweeps from -100° to +80° during t 0→1.
        start_angle = -100 + t * 180 - 30
        end_angle = -100 + t * 180 + 10
        num_pts = 12
        pts = []
        for i in range(num_pts):
            a_deg = start_angle + (end_angle - start_angle) * i / (num_pts - 1)
            a_rad = math.radians(a_deg)
            px = cx + int(math.cos(a_rad) * radius) * facing
            py = cy + int(math.sin(a_rad) * radius)
            pts.append((px, py))
        # Draw arc trail (fading).
        arc_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        for i in range(len(pts) - 1):
            alpha = _NS_lyssarethys._alpha(200 * (i / len(pts)))
            p1_local = (pts[i][0] - cx + 60, pts[i][1] - cy + 60)
            p2_local = (pts[i + 1][0] - cx + 60, pts[i + 1][1] - cy + 60)
            pygame.draw.line(arc_surf, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                             p1_local, p2_local, 4)
            pygame.draw.line(arc_surf, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha),
                             p1_local, p2_local, 3)
            pygame.draw.line(arc_surf, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha),
                             p1_local, p2_local, 2)
            pygame.draw.line(arc_surf, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                             p1_local, p2_local, 1)
        surface.blit(arc_surf, (cx - 60, cy - 60))
        # Sparkles along arc.
        for i in range(6):
            sp_t = (t * 3 + i * 0.15) % 1.0
            idx = int(sp_t * (num_pts - 1))
            sp = pts[idx]
            spx = sp[0] + int(math.sin(t * 6 + i) * 3)
            spy = sp[1] + int(math.cos(t * 6 + i) * 3)
            alpha = _NS_lyssarethys._alpha(220)
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_hot"], alpha), (spx, spy, 2, 2))
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_shine"], alpha), (spx, spy, 1, 1))
    # ============================================================
    # SHADOW SILHOUETTE (during R skill dash)
    # ============================================================
    def _draw_shadow_silhouette(surface, cx, cy, facing, phase):
        """Blue-purple shadowy running form."""
        # Simple body silhouette (dashing pose).
        body_pts = [
            (cx - 4, cy - 20),
            (cx + 4, cy - 20),
            (cx + 5, cy - 5),
            (cx + 8, cy + 10),
            (cx + 4, cy + 20),
            (cx - 4, cy + 20),
            (cx - 8, cy + 10),
            (cx - 5, cy - 5),
        ]
        _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["shade_darkest"], body_pts)
        _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["shade_dark"], [
            (cx - 3, cy - 19),
            (cx + 3, cy - 19),
            (cx + 4, cy - 5),
            (cx + 6, cy + 8),
            (cx + 3, cy + 18),
            (cx - 3, cy + 18),
            (cx - 6, cy + 8),
            (cx - 4, cy - 5),
        ])
        # Head hint.
        _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["shade_mid"],
                                  (cx, cy - 22), 4)
        # Eyes glowing.
        for side in (-1, 1):
            pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_light"],
                             (cx + side * 2 - 1, cy - 22, 1, 1))
            pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_shine"],
                             (cx + side * 2 - 1, cy - 22, 1, 1))
        # Trailing wisps.
        for i in range(4):
            wisp_x = cx - facing * (5 + i * 3)
            wisp_y = cy + int(math.sin(phase + i) * 4)
            alpha = _NS_lyssarethys._alpha(180 - i * 40)
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["shade_dark"], alpha),
                                      (wisp_x, wisp_y), 3)
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["shade_mid"], alpha),
                                      (wisp_x, wisp_y), 2)
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                             (wisp_x, wisp_y, 1, 1))
    def _draw_shadow_silhouette_trail(surface, cx, cy, facing, alpha_base):
        body_pts = [
            (cx - 3, cy - 20),
            (cx + 3, cy - 20),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
        ]
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["shade_darkest"], body_pts,
                                    alpha_base)
        _NS_lyssarethys._poly_alpha(surface, _NS_lyssarethys.PALETTE["shade_mid"], [
            (cx - 2, cy - 18), (cx + 2, cy - 18),
            (cx + 4, cy + 8), (cx - 4, cy + 8),
        ], alpha_base)
    # ============================================================
    # HELPERS for alpha-aware drawing
    # ============================================================
    def _poly_alpha(surface, color, points, alpha, offset=(0, 0)):
        if alpha >= 250 and offset == (0, 0):
            _NS_lyssarethys._poly(surface, color, points)
            return
        # Draw to alpha surface.
        min_x = min(p[0] for p in points) - 4
        min_y = min(p[1] for p in points) - 4
        max_x = max(p[0] for p in points) + 4
        max_y = max(p[1] for p in points) + 4
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        local_pts = [(p[0] - min_x + offset[0], p[1] - min_y + offset[1]) for p in points]
        alpha_surf = pygame.Surface((w + offset[0], h + offset[1]), pygame.SRCALPHA)
        c = _NS_lyssarethys._clamp(color)
        pygame.draw.polygon(alpha_surf, (*c, alpha), local_pts)
        surface.blit(alpha_surf, (min_x, min_y))
    def _aaline_alpha(surface, color, start, end, width, alpha):
        if alpha >= 250:
            _NS_lyssarethys._aaline(surface, color, start, end, width)
            return
        c = _NS_lyssarethys._clamp(color)
        pygame.draw.line(surface, (*c, alpha), start, end, width)
    # ============================================================
    # SHADOW WISPS (ambient)
    # ============================================================
    def _draw_shadow_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0
        # Cloud below.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_lyssarethys._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_lyssarethys.PALETTE["shade_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_lyssarethys._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_lyssarethys.PALETTE["shade_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising magenta motes.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 30)
            alpha = _NS_lyssarethys._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                      (sx, sy), 3)
            _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha),
                                      (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Small hearts drifting up (subtle theme).
        for i in range(3):
            heart_t = (phase * 0.3 + i * 0.35) % 1.0
            hx = cx - 20 + i * 20 + int(math.sin(phase + i) * 5)
            hy = cy + 5 - int(heart_t * 30)
            alpha = _NS_lyssarethys._alpha(150 * (1 - heart_t) * strength)
            if alpha > 0:
                _NS_lyssarethys._draw_mini_heart(surface, hx, hy,
                                                 _NS_lyssarethys.PALETTE["magic_mid"], alpha)
    def _draw_mini_heart(surface, cx, cy, color, alpha):
        """Small 5x4 heart shape."""
        c = _NS_lyssarethys._clamp(color)
        # Two lobes and a point.
        pygame.draw.rect(surface, (*c, alpha), (cx - 2, cy - 1, 2, 2))
        pygame.draw.rect(surface, (*c, alpha), (cx + 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, (*c, alpha), (cx - 1, cy, 3, 1))
        pygame.draw.rect(surface, (*c, alpha), (cx, cy + 1, 1, 1))
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
        pygame.draw.ellipse(shadow, (3, 2, 5, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (60, 15, 60, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_shade_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_lyssarethys._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_lyssarethys._aacircle(aura, (*_NS_lyssarethys.PALETTE["shade_darkest"], alpha),
                                          (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_lyssarethys._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_lyssarethys._aacircle(aura, (*_NS_lyssarethys.PALETTE["shade_dark"], alpha),
                                          (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_lyssarethys._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_lyssarethys._aacircle(aura, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                          (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating pink motes.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_lyssarethys.PALETTE["shade_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_lyssarethys.PALETTE["magic_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_lyssarethys.PALETTE["magic_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_lyssarethys.PALETTE["shade_dark"], 180),
                            (40, 24, 90, 14), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_lyssarethys.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_lyssarethys.PALETTE["magic_hot"],
                                       _NS_lyssarethys._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL: Q - HATE SPIKE (ranged shard)
    # ============================================================
    def _draw_hatespike_skill(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyssarethys._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.25:
            # Charge in hand.
            t = progress / 0.25
            hand_x = x + facing * 16
            hand_y = y - 6 + hover
            cr = int(4 + t * 6)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_lyssarethys._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                          (hand_x, hand_y), r)
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_mid"],
                                      (hand_x, hand_y), cr - 2)
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_light"],
                                      (hand_x, hand_y), max(1, cr - 4))
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_shine"],
                                      (hand_x, hand_y), max(1, cr - 6))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 20
            start_y = y - 6 + hover
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Spike-shaped comet: elongated shard trail.
            angle_to_target = math.atan2(ty - start_y, tx - start_x)
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_lyssarethys._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                          (px, py), size)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha),
                                          (px, py), max(1, size - 1))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha),
                                          (px, py), max(1, size - 2))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                                          (px, py), max(1, size - 3))
            # SHARP SHARD HEAD (arrow/dagger shape).
            spike_len = 12
            tip = (bx + int(math.cos(angle_to_target) * spike_len),
                   by + int(math.sin(angle_to_target) * spike_len))
            perp = angle_to_target + math.pi / 2
            base_a = (bx + int(math.cos(perp) * 4),
                      by + int(math.sin(perp) * 4))
            base_b = (bx - int(math.cos(perp) * 4),
                      by - int(math.sin(perp) * 4))
            back = (bx - int(math.cos(angle_to_target) * 8),
                    by - int(math.sin(angle_to_target) * 8))
            # Layered spike.
            _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                  [(tip[0] + 1, tip[1] + 1),
                                   (base_a[0] + 1, base_a[1] + 1),
                                   (back[0] + 1, back[1] + 1),
                                   (base_b[0] + 1, base_b[1] + 1)])
            _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["magic_darkest"],
                                  [tip, base_a, back, base_b])
            _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["magic_dark"], [
                tip,
                (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
                (bx, by),
                (int((tip[0] + base_b[0]) / 2), int((tip[1] + base_b[1]) / 2)),
            ])
            _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["magic_mid"], [
                tip, (bx, by),
                (int((bx + base_a[0]) / 2), int((by + base_a[1]) / 2)),
            ])
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_light"], tip, 2)
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_shine"], tip, 1)
            pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["white"], (tip[0], tip[1], 1, 1))
            # Impact.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(10 + st * 22)
                alpha = _NS_lyssarethys._alpha(240 * (1 - st))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                          (tx, ty), radius + 3, 3)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha),
                                          (tx, ty), radius, 2)
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                                          (tx, ty), max(1, radius - 6), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL: W - ALLURE (heart projectile)
    # ============================================================
    def _draw_allure_ground(surface, boss, x, y, timer, pulse):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Charm heart aura on ground.
        for i in range(2):
            r = int(30 + i * 8 + math.sin(pulse * 2) * 3)
            alpha = _NS_lyssarethys._alpha(180 - i * 60)
            pygame.draw.ellipse(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
    def _draw_allure_foreground(surface, boss, x, y, timer, phase):
        """Heart projectile flying toward target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyssarethys._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.2:
            # Charge — big heart forming in hand.
            t = progress / 0.2
            hand_x = x + facing * 16
            hand_y = y - 6 + hover
            hr = int(5 + t * 6)
            for r in range(hr + 5, 0, -1):
                alpha = _NS_lyssarethys._alpha(200 * (hr + 5 - r) / (hr + 5))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                          (hand_x, hand_y), r)
            _NS_lyssarethys._draw_big_heart(surface, hand_x, hand_y, hr,
                                            _NS_lyssarethys.PALETTE["magic_mid"],
                                            _NS_lyssarethys.PALETTE["magic_light"],
                                            _NS_lyssarethys.PALETTE["magic_shine"])
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 22
            start_y = y - 6 + hover
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Trail — small hearts.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.07)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t) + int(math.sin(trail_t * 8) * 3)
                alpha = _NS_lyssarethys._alpha(220 - i * 32)
                _NS_lyssarethys._draw_mini_heart(surface, px, py,
                                                 _NS_lyssarethys.PALETTE["magic_mid"], alpha)
            # Big heart projectile head.
            heart_size = 8
            for r in range(heart_size + 4, 0, -1):
                alpha = _NS_lyssarethys._alpha(120 * (heart_size + 4 - r) / (heart_size + 4))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha),
                                          (bx, by), r)
            _NS_lyssarethys._draw_big_heart(surface, bx, by, heart_size,
                                            _NS_lyssarethys.PALETTE["magic_mid"],
                                            _NS_lyssarethys.PALETTE["magic_light"],
                                            _NS_lyssarethys.PALETTE["magic_shine"])
            # Impact: burst of hearts.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                for i in range(8):
                    angle = i * math.pi / 4
                    dist = int(st * 25)
                    hx = tx + int(math.cos(angle) * dist)
                    hy = ty + int(math.sin(angle) * dist * 0.7)
                    alpha = _NS_lyssarethys._alpha(240 * (1 - st))
                    _NS_lyssarethys._draw_mini_heart(surface, hx, hy,
                                                     _NS_lyssarethys.PALETTE["magic_light"], alpha)
    def _draw_big_heart(surface, cx, cy, size, color_body, color_light, color_shine):
        """Draw a heart shape (roughly)."""
        c_body = _NS_lyssarethys._clamp(color_body)
        c_light = _NS_lyssarethys._clamp(color_light)
        c_shine = _NS_lyssarethys._clamp(color_shine)
        # Two circles (lobes) + triangle bottom.
        r = max(2, size // 2)
        # Lobes.
        _NS_lyssarethys._aacircle(surface, c_body, (cx - r, cy - r // 2), r)
        _NS_lyssarethys._aacircle(surface, c_body, (cx + r, cy - r // 2), r)
        # Triangle point.
        pygame.draw.polygon(surface, c_body, [
            (cx - r - r // 2, cy - r // 4),
            (cx + r + r // 2, cy - r // 4),
            (cx, cy + r + r // 2),
        ])
        # Highlights.
        pygame.draw.rect(surface, c_light, (cx - r - 1, cy - r - 1, 2, 2))
        pygame.draw.rect(surface, c_shine, (cx - r, cy - r, 1, 1))
    # ============================================================
    # SKILL: E - WHIP LASH (melee whip lash with dash+trail)
    # ============================================================
    def _draw_whiplash_foreground(surface, boss, x, y, timer, phase):
        """Long whip lash sweeping forward at target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyssarethys._target_position(boss, x, y)
        hover = int(math.sin(phase * 0.6) * 5)
        if progress < 0.3:
            # Wind-up: pull back whip.
            t = progress / 0.3
            # Just aura charge on tentacles (visualized via body tentacles).
            for i in range(4):
                sp_angle = phase * 4 + i * math.pi / 2
                sx = x + int(math.cos(sp_angle) * 20)
                sy = y - 4 + hover + int(math.sin(sp_angle) * 20)
                alpha = _NS_lyssarethys._alpha(200 * t)
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_hot"], alpha),
                                 (sx, sy, 2, 2))
        elif progress < 0.7:
            # Whip extends toward target.
            t = (progress - 0.3) / 0.4
            # Whip curve from boss to target.
            start_x = x + facing * 10
            start_y = y - 6 + hover
            # Extend curve.
            end_x = int(start_x + (tx - start_x) * min(1.0, t * 1.5))
            end_y = int(start_y + (ty - start_y) * min(1.0, t * 1.5))
            # Whip as bezier curve with wave.
            segments = 12
            points = []
            for i in range(segments + 1):
                seg_t = i / segments
                # Straight line + sinusoidal wave.
                wave = math.sin(seg_t * math.pi * 2 + phase * 3) * 8 * (1 - seg_t)
                perp_dx = -(end_y - start_y)
                perp_dy = (end_x - start_x)
                perp_len = max(1, math.sqrt(perp_dx ** 2 + perp_dy ** 2))
                perp_dx /= perp_len
                perp_dy /= perp_len
                base_x = int(start_x + (end_x - start_x) * seg_t + perp_dx * wave)
                base_y = int(start_y + (end_y - start_y) * seg_t + perp_dy * wave)
                points.append((base_x, base_y))
            # Draw whip segments (tapered).
            for i in range(len(points) - 1):
                thickness = max(1, 4 - i // 3)
                pygame.draw.line(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                 (points[i][0] + 1, points[i][1] + 1),
                                 (points[i + 1][0] + 1, points[i + 1][1] + 1),
                                 thickness + 2)
                pygame.draw.line(surface, _NS_lyssarethys.PALETTE["magic_darkest"],
                                 points[i], points[i + 1], thickness + 1)
                pygame.draw.line(surface, _NS_lyssarethys.PALETTE["magic_dark"],
                                 points[i], points[i + 1], thickness)
                pygame.draw.line(surface, _NS_lyssarethys.PALETTE["magic_mid"],
                                 points[i], points[i + 1], max(1, thickness - 1))
                # Pink edge.
                if thickness >= 2:
                    pygame.draw.line(surface, _NS_lyssarethys.PALETTE["magic_light"],
                                     (points[i][0], points[i][1] - 1),
                                     (points[i + 1][0], points[i + 1][1] - 1), 1)
                # Sparkles.
                if i % 2 == 0:
                    pygame.draw.rect(surface, _NS_lyssarethys.PALETTE["magic_hot"],
                                     (points[i][0], points[i][1], 1, 1))
            # WHIP TIP — arrowhead blade.
            if len(points) >= 2:
                end = points[-1]
                prev = points[-2]
                tip_angle = math.atan2(end[1] - prev[1], end[0] - prev[0])
                tip_len = 10
                tip_end = (end[0] + int(math.cos(tip_angle) * tip_len),
                           end[1] + int(math.sin(tip_angle) * tip_len))
                perp = tip_angle + math.pi / 2
                ba = (end[0] + int(math.cos(perp) * 4),
                      end[1] + int(math.sin(perp) * 4))
                bb = (end[0] - int(math.cos(perp) * 4),
                      end[1] - int(math.sin(perp) * 4))
                _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["shadow_deep"],
                                      [(tip_end[0] + 1, tip_end[1] + 1),
                                       (ba[0] + 1, ba[1] + 1), (bb[0] + 1, bb[1] + 1)])
                _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["magic_darkest"],
                                      [tip_end, ba, bb])
                _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["magic_dark"], [
                    tip_end,
                    (int((tip_end[0] + ba[0]) / 2), int((tip_end[1] + ba[1]) / 2)),
                    end,
                    (int((tip_end[0] + bb[0]) / 2), int((tip_end[1] + bb[1]) / 2)),
                ])
                _NS_lyssarethys._poly(surface, _NS_lyssarethys.PALETTE["magic_mid"], [
                    tip_end, end,
                    (int((tip_end[0] + ba[0]) / 2), int((tip_end[1] + ba[1]) / 2)),
                ])
                _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_light"], tip_end, 2)
                _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_shine"], tip_end, 1)
            # Impact burst at target when whip fully extends.
            if t > 0.6:
                st = (t - 0.6) / 0.4
                radius = int(8 + st * 18)
                alpha = _NS_lyssarethys._alpha(240 * (1 - st))
                _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha),
                                          (tx, ty), radius, 2)
                for i in range(8):
                    angle = i * math.pi / 4
                    ex = tx + int(math.cos(angle) * radius)
                    ey = ty + int(math.sin(angle) * radius)
                    pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_hot"], alpha),
                                     (ex, ey, 2, 2))
        else:
            # Recover: whip retracts, small residue.
            t = (progress - 0.7) / 0.3
            for i in range(4):
                alpha = _NS_lyssarethys._alpha(150 * (1 - t))
                sp = phase * 3 + i
                sx = x + facing * 15 + int(math.cos(sp) * 10)
                sy = y - 4 + hover + int(math.sin(sp) * 10)
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL: R - LAST CARESS (leap strike burst)
    # ============================================================
    def _draw_lastcaress_ground(surface, boss, x, y, timer, phase):
        """Purple runes on ground at boss + at target."""
        tx, ty = _NS_lyssarethys._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Circle at boss location (fading as she vanishes).
        if progress < 0.5:
            fade = 1.0 - progress * 2
            for i in range(2):
                r = int(30 + i * 6)
                alpha = _NS_lyssarethys._alpha(180 * fade - i * 40)
                pygame.draw.ellipse(surface, (*_NS_lyssarethys.PALETTE["magic_mid"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
        # Circle at target location (grows as she arrives).
        if progress > 0.3:
            grow = min(1.0, (progress - 0.3) / 0.4)
            for i in range(3):
                r = int((25 + i * 8) * grow)
                alpha = _NS_lyssarethys._alpha(200 - i * 50)
                pygame.draw.ellipse(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                    (tx - r, ty + 25 - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_lyssarethys.PALETTE["magic_dark"], alpha),
                                    (tx - r + 2, ty + 25 - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)
    def _draw_lastcaress_foreground(surface, boss, x, y, timer, phase):
        """Explosion at target during strike."""
        tx, ty = _NS_lyssarethys._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.6 and progress < 0.9:
            # Strike explosion at target.
            t = (progress - 0.6) / 0.3
            intensity = math.sin(t * math.pi)
            # Radial magenta burst (like Evelynn ult).
            num_spikes = 16
            for i in range(num_spikes):
                angle = i * math.pi * 2 / num_spikes + t * 0.5
                length = int(50 * intensity)
                sp_start = 8
                sx1 = tx + int(math.cos(angle) * sp_start)
                sy1 = ty + int(math.sin(angle) * sp_start)
                sx2 = tx + int(math.cos(angle) * length)
                sy2 = ty + int(math.sin(angle) * length)
                alpha = _NS_lyssarethys._alpha(240 * intensity)
                # Spike shape.
                perp = angle + math.pi / 2
                w = 3
                pa = (sx1 + int(math.cos(perp) * w), sy1 + int(math.sin(perp) * w))
                pb = (sx1 - int(math.cos(perp) * w), sy1 - int(math.sin(perp) * w))
                # Layered.
                pygame.draw.polygon(surface, (*_NS_lyssarethys.PALETTE["magic_darkest"], alpha),
                                    [(sx2, sy2), pa, pb])
                pygame.draw.polygon(surface,
                                    (*_NS_lyssarethys.PALETTE["magic_dark"],
                                     _NS_lyssarethys._alpha(240 * intensity)),
                                    [(sx2, sy2),
                                     (int((sx2 + pa[0]) / 2), int((sy2 + pa[1]) / 2)),
                                     (tx, ty),
                                     (int((sx2 + pb[0]) / 2), int((sy2 + pb[1]) / 2))])
                pygame.draw.line(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                                 (tx, ty), (sx2, sy2), 2)
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_shine"], alpha),
                                 (sx2, sy2, 2, 2))
            # Central big glow.
            for r in range(int(intensity * 20), 0, -2):
                alpha = _NS_lyssarethys._alpha(150 * intensity * (25 - r) / 25)
                if alpha > 0:
                    _NS_lyssarethys._aacircle(surface, (*_NS_lyssarethys.PALETTE["magic_light"], alpha),
                                              (tx, ty), r)
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["magic_shine"], (tx, ty), 4)
            _NS_lyssarethys._aacircle(surface, _NS_lyssarethys.PALETTE["white"], (tx, ty), 2)
        elif progress >= 0.9:
            # Aftermath sparkles.
            t = (progress - 0.9) / 0.1
            for i in range(10):
                angle = i * math.pi / 5 + t * 3
                dist = 20 + int(t * 20)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.7)
                alpha = _NS_lyssarethys._alpha(200 * (1 - t))
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_lyssarethys.PALETTE["magic_shine"], alpha),
                                 (sx, sy, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kaerissa(surface, boss, x, y):
    """Entry point kaerissa."""
    return _NS_kaerissa.draw_kaerissa(surface, boss, x, y)


def draw_thorgaruk(surface, boss, x, y):
    """Entry point thorgaruk."""
    return _NS_thorgaruk.draw_thorgaruk(surface, boss, x, y)


def draw_zorathiel(surface, boss, x, y):
    """Entry point zorathiel."""
    return _NS_zorathiel.draw_zorathiel(surface, boss, x, y)


def draw_lyssarethys(surface, boss, x, y):
    """Entry point lyssarethys."""
    return _NS_lyssarethys.draw_lyssarethys(surface, boss, x, y)
