"""
bosses/level24.py - Semua boss Level 24

Berisi:
  - khalzaredh  (mini boss - MELEE sandborn prince)
  - nyxaroth    (mini boss - RANGED void-starweaver mage)
  - veshtrax    (mini boss - MELEE sapphire executor duelist)
  - solareth    (TRUE BOSS - MELEE sunborn herald, solar tank)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kz_ (khalzaredh), _nx_ (nyxaroth), _vst_ (veshtrax),
    _sl_ (solareth) sudah unik. Nama fungsi namespace (_draw_*)
    TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KHALZAREDH (SANDBORN PRINCE) - Mini Boss
# ====================================================================

class _NS_khalzaredh:
    """Namespace khalzaredh - Sand Prince mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tanned desert warrior)
        "skin_darkest": (60, 30, 15),
        "skin_dark": (110, 65, 35),
        "skin_mid": (170, 115, 70),
        "skin_light": (215, 165, 115),
        "skin_shine": (245, 210, 160),
        # White/cream cloth (sorban, sash)
        "cloth_dark": (140, 120, 90),
        "cloth_mid": (200, 180, 145),
        "cloth_light": (240, 225, 195),
        "cloth_shine": (255, 250, 230),
        # Gold armor & crown (dominant)
        "gold_darkest": (60, 40, 5),
        "gold_dark": (130, 90, 20),
        "gold_mid": (200, 155, 45),
        "gold_light": (245, 210, 90),
        "gold_shine": (255, 240, 170),
        "gold_white": (255, 255, 220),
        # Emerald gems (crown, armor accents)
        "gem_dark": (10, 60, 45),
        "gem_mid": (30, 140, 105),
        "gem_light": (90, 220, 175),
        "gem_shine": (200, 255, 235),
        # Sand element (main FX color)
        "sand_darkest": (70, 45, 15),
        "sand_dark": (140, 95, 35),
        "sand_mid": (215, 165, 75),
        "sand_light": (245, 215, 130),
        "sand_hot": (255, 235, 170),
        "sand_shine": (255, 250, 220),
        # Scimitar blade
        "blade_darkest": (30, 25, 15),
        "blade_dark": (100, 90, 60),
        "blade_mid": (180, 165, 120),
        "blade_light": (230, 220, 180),
        "blade_shine": (255, 250, 220),
        # Dark cloth (pants, belt)
        "leather_dark": (35, 22, 12),
        "leather_mid": (75, 50, 25),
        "leather_light": (130, 90, 50),
        # Beard/hair (black)
        "hair_dark": (10, 8, 6),
        "hair_mid": (40, 30, 22),
        # Eye (glowing gold)
        "eye_glow": (255, 220, 100),
        "eye_hot": (255, 240, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_khalzaredh._clamp(color)
        if _NS_khalzaredh.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_khalzaredh._clamp(color)
        if _NS_khalzaredh.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_khalzaredh._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_khalzaredh(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_khalzaredh._detect_moving(boss)
        _NS_khalzaredh._update_kz_attack_anim(boss)
        attacking = (
                getattr(boss, "_kz_attack_active", False)
                or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind (sand aura).
        _NS_khalzaredh._draw_sand_aura(surface, x, y, pulse)
        _NS_khalzaredh._draw_ground_sand_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_khalzaredh._draw_desert_tornado_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_khalzaredh._draw_quicksand_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khalzaredh._draw_sandstorm_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if active_skill == "w":
            # Quicksand form (partially sand).
            _NS_khalzaredh._draw_kz_quicksand_form(surface, boss, x, y, skill_timer)
        elif attacking:
            _NS_khalzaredh._draw_kz_attack(surface, boss, x, y)
        elif moving:
            _NS_khalzaredh._draw_kz_float(surface, boss, x, y)
        else:
            _NS_khalzaredh._draw_kz_idle(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_khalzaredh._draw_sand_wave_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khalzaredh._draw_desert_tornado_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khalzaredh._draw_sandstorm_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_kz_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kz_previous_timer", 0))
        active = bool(getattr(boss, "_kz_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kz_attack_active = True
            boss._kz_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kz_attack_frame = int(
                getattr(boss, "_kz_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._kz_attack_active = False
            boss._kz_attack_frame = 0
            active = False
        boss._kz_previous_timer = timer
        boss._kz_attack_progress = (
            min(1.0, getattr(boss, "_kz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kz_last_x"):
            boss._kz_last_x = boss.x
            boss._kz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kz_last_x)
        dy = abs(boss.y - boss._kz_last_y)
        boss._kz_last_x = boss.x
        boss._kz_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_kz_idle(surface, boss, x, y):
        # Floating: hovers slightly above ground with slow bob.
        float_bob = int(math.sin(boss.pulse * 0.6) * 3) - 4  # slight lift
        _NS_khalzaredh._draw_shadow(surface, x, y + 50)
        _NS_khalzaredh._draw_sand_trail(surface, x, y + 40, boss.pulse, floating=True)
        _NS_khalzaredh._draw_kz_body(surface, x, y + float_bob,
                                     boss.direction, boss.pulse, "idle")
    def _draw_kz_float(surface, boss, x, y):
        """Floating movement (as requested)."""
        phase = boss.pulse * 1.8
        float_bob = int(math.sin(phase * 0.9) * 5) - 6  # more lift while moving
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_khalzaredh._draw_shadow(surface, x + sway, y + 50, moving=True)
        _NS_khalzaredh._draw_sand_trail(surface, x + sway, y + 42, phase,
                                        floating=True, moving=True,
                                        facing=boss.direction)
        _NS_khalzaredh._draw_kz_body(surface, x + sway, y + float_bob,
                                     boss.direction, phase, "float")
    def _draw_kz_attack(surface, boss, x, y):
        """Scimitar swing animation."""
        progress = getattr(boss, "_kz_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up → swing → recovery.
        if progress < 0.35:
            # Wind-up: pull back.
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3) - 4  # still floating
        elif progress < 0.6:
            # Swing forward.
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(3 - t * 5) - 4
        else:
            # Recovery.
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2) - 4
        _NS_khalzaredh._draw_shadow(surface, x + lunge, y + 50)
        _NS_khalzaredh._draw_sand_trail(surface, x + lunge, y + 42, boss.pulse,
                                        floating=True, intense=True)
        _NS_khalzaredh._draw_kz_body(surface, x + lunge, y + lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Sand slash effect during swing.
        if 0.35 <= progress < 0.75:
            _NS_khalzaredh._draw_scimitar_slash(surface, boss, x + lunge, y + lift,
                                                progress)
    def _draw_kz_quicksand_form(surface, boss, x, y, skill_timer):
        """During W skill, partially transformed into sand."""
        float_bob = int(math.sin(boss.pulse * 1.2) * 4) - 6
        _NS_khalzaredh._draw_shadow(surface, x, y + 50)
        _NS_khalzaredh._draw_sand_trail(surface, x, y + 42, boss.pulse,
                                        floating=True, intense=True)
        # Body renders with sand dissolution effect.
        _NS_khalzaredh._draw_kz_body(surface, x, y + float_bob,
                                     boss.direction, boss.pulse, "quicksand")
        # Extra sand swirl around body.
        _NS_khalzaredh._draw_quicksand_swirl(surface, x, y + float_bob, boss.pulse)
    # ============================================================
    # BODY (Humanoid: legs/robe, torso, arms, head with turban)
    # ============================================================
    def _draw_kz_body(surface, cx, cy, facing, phase, action,
                      attack_progress=0):
        """Draw humanoid warrior with scimitar."""
        # Robe/legs tail (flowing bottom).
        _NS_khalzaredh._draw_robe_bottom(surface, cx, cy + 22, facing, phase, action)
        # Body torso.
        _NS_khalzaredh._draw_kz_torso(surface, cx, cy, facing, phase, action)
        # Back arm (holding side).
        _NS_khalzaredh._draw_back_arm(surface, cx, cy + 4, facing, phase, action,
                                      attack_progress)
        # Head with turban.
        _NS_khalzaredh._draw_kz_head(surface, cx, cy - 22, facing, phase, action)
        # Front arm + scimitar (foreground).
        _NS_khalzaredh._draw_sword_arm(surface, cx, cy + 4, facing, phase, action,
                                       attack_progress)
    def _draw_robe_bottom(surface, cx, cy, facing, phase, action):
        """Flowing robe/pants bottom (floating so it sways more)."""
        sway = math.sin(phase * 0.8) * 3
        # Main robe shape - triangular tapering, tails floating.
        robe_pts = [
            (cx - 14, cy - 8),
            (cx + 14, cy - 8),
            (cx + 18 + int(sway), cy + 8),
            (cx + 12 + int(sway * 1.5), cy + 16),
            (cx + 4, cy + 18),
            (cx - 4, cy + 18),
            (cx - 12 - int(sway * 1.5), cy + 16),
            (cx - 18 - int(sway), cy + 8),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in robe_pts])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["leather_dark"], robe_pts)
        # Sash overlay (cream cloth).
        sash_pts = [
            (cx - 12, cy - 6),
            (cx + 12, cy - 6),
            (cx + 14, cy + 2),
            (cx - 14, cy + 2),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_dark"], sash_pts)
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_mid"], [
            (cx - 11, cy - 5),
            (cx + 11, cy - 5),
            (cx + 12, cy + 1),
            (cx - 12, cy + 1),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_light"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 9, cy - 2),
            (cx - 9, cy - 2),
        ])
        # Gold belt buckle.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_dark"],
                         (cx - 4, cy - 5, 8, 6))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_mid"],
                         (cx - 3, cy - 4, 6, 4))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_light"],
                         (cx - 2, cy - 3, 4, 2))
        # Emerald gem in center.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_dark"],
                         (cx - 1, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_mid"],
                         (cx - 1, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_light"],
                         (cx, cy - 3, 1, 1))
        # Robe highlights (folds).
        for i, x_off in enumerate((-10, -4, 4, 10)):
            pygame.draw.line(surface, _NS_khalzaredh.PALETTE["leather_mid"],
                             (cx + x_off, cy + 4),
                             (cx + x_off + int(sway * 0.5), cy + 16), 1)
        # Bottom tail sand dissolution (floating character).
        for i in range(6):
            t = (phase * 0.4 + i * 0.15) % 1.0
            px = cx + int((i - 2.5) * 5) + int(math.sin(phase + i) * 2)
            py = cy + 18 + int(t * 10)
            alpha = _NS_khalzaredh._alpha(200 * (1 - t))
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha), (px, py), 2)
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha), (px, py, 1, 1))
    def _draw_kz_torso(surface, cx, cy, facing, phase, action):
        """Muscular bare torso with gold pauldrons."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape (V-shape muscular).
        torso_pts = [
            (cx - 12, cy - 12),
            (cx - 14, cy - 8),
            (cx - 12, cy + 2),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 12, cy + 2),
            (cx + 14, cy - 8),
            (cx + 12, cy - 12),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["skin_darkest"], torso_pts)
        # Main skin fill.
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["skin_dark"], [
            (cx - 11, cy - 11),
            (cx - 13, cy - 7),
            (cx - 11, cy + 1),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 11, cy + 1),
            (cx + 13, cy - 7),
            (cx + 11, cy - 11),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["skin_mid"], [
            (cx - 9, cy - 9),
            (cx - 10, cy - 5),
            (cx - 8, cy),
            (cx - 5, cy + 7),
            (cx + 5, cy + 7),
            (cx + 8, cy),
            (cx + 10, cy - 5),
            (cx + 9, cy - 9),
        ])
        # Abs definition.
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                         (cx, cy - 6), (cx, cy + 7), 1)
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                         (cx - 5, cy - 2), (cx + 5, cy - 2), 1)
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                         (cx - 5, cy + 3), (cx + 5, cy + 3), 1)
        # Chest highlights.
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["skin_light"],
                         (cx - 6, cy - 7), (cx - 5, cy - 4), 1)
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["skin_light"],
                         (cx + 6, cy - 7), (cx + 5, cy - 4), 1)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["skin_shine"],
                         (cx - 5, cy - 7, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["skin_shine"],
                         (cx + 4, cy - 7, 1, 1))
        # Gold chest ornament (pectoral piece).
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_dark"], [
            (cx - 6, cy - 10),
            (cx + 6, cy - 10),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_mid"], [
            (cx - 5, cy - 9),
            (cx + 5, cy - 9),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        # Gem center.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_dark"],
                         (cx - 1, cy - 9, 2, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_mid"],
                         (cx - 1, cy - 9, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_shine"],
                         (cx, cy - 9, 1, 1))
        # Pauldrons (shoulder armor).
        for side in (-1, 1):
            shoulder_x = cx + side * 12
            shoulder_y = cy - 10
            # Base pauldron.
            _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["shadow_deep"], [
                (shoulder_x - 4, shoulder_y),
                (shoulder_x + 5, shoulder_y - 2),
                (shoulder_x + 6, shoulder_y + 4),
                (shoulder_x - 3, shoulder_y + 4),
            ])
            _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_dark"], [
                (shoulder_x - 4, shoulder_y),
                (shoulder_x + 4, shoulder_y - 2),
                (shoulder_x + 5, shoulder_y + 3),
                (shoulder_x - 3, shoulder_y + 3),
            ])
            _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_mid"], [
                (shoulder_x - 3, shoulder_y),
                (shoulder_x + 3, shoulder_y - 1),
                (shoulder_x + 4, shoulder_y + 2),
                (shoulder_x - 2, shoulder_y + 2),
            ])
            _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_light"], [
                (shoulder_x - 2, shoulder_y),
                (shoulder_x + 2, shoulder_y),
                (shoulder_x + 2, shoulder_y + 1),
                (shoulder_x - 1, shoulder_y + 1),
            ])
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_shine"],
                             (shoulder_x - 1, shoulder_y, 1, 1))
    def _draw_kz_head(surface, cx, cy, facing, phase, action):
        """Head with turban, crown, beard."""
        # Head shape.
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
            (cx + 3, cy + 7),
            (cx - 3, cy + 7),
            (cx - 5, cy + 5),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in head_pts])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["skin_darkest"], head_pts)
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["skin_dark"], [
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
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["skin_mid"], [
            (cx - 5, cy - 1),
            (cx - 6, cy - 4),
            (cx - 3, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 4),
            (cx + 5, cy - 1),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        # Cheekbone highlight.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["skin_light"],
                         (cx + facing * 3, cy - 3, 1, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["skin_shine"],
                         (cx + facing * 3, cy - 3, 1, 1))
        # BEARD (short, styled).
        beard_pts = [
            (cx - 4, cy + 1),
            (cx + 4, cy + 1),
            (cx + 5, cy + 4),
            (cx + 3, cy + 7),
            (cx - 3, cy + 7),
            (cx - 5, cy + 4),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["hair_dark"], beard_pts)
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["hair_mid"], [
            (cx - 3, cy + 2),
            (cx + 3, cy + 2),
            (cx + 4, cy + 4),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 4),
        ])
        # Mustache.
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["hair_dark"],
                         (cx - 3, cy + 1), (cx + 3, cy + 1), 1)
        # EYE (glowing gold, intense stare).
        ex = cx + facing * 2
        ey = cy - 3
        # Glow.
        for r in range(4, 0, -1):
            alpha = _NS_khalzaredh._alpha(120 * (4 - r) / 4)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["eye_glow"], alpha), (ex, ey), r)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["shadow_deep"], (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["eye_glow"], (ex, ey, 2, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["eye_hot"], (ex + 1, ey, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["white"], (ex + 1, ey, 1, 1))
        # Second eye (dimmer, farther).
        ex2 = cx - facing * 2
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["shadow_deep"], (ex2 - 1, ey, 2, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["eye_glow"], (ex2, ey, 1, 1))
        # Eyebrows (thick).
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["hair_dark"],
                         (cx - 5, cy - 5), (cx - 1, cy - 6), 1)
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["hair_dark"],
                         (cx + 1, cy - 6), (cx + 5, cy - 5), 1)
        # TURBAN (white cloth wrapping).
        _NS_khalzaredh._draw_turban(surface, cx, cy - 6, facing, phase)
        # CROWN (gold with emerald).
        _NS_khalzaredh._draw_crown(surface, cx, cy - 8, facing, phase)
        # Turban tail (flowing behind).
        tail_sway = math.sin(phase * 0.9) * 3
        back_dir = -facing
        tail_pts = [
            (cx + back_dir * 6, cy - 4),
            (cx + back_dir * 12 + int(tail_sway), cy),
            (cx + back_dir * 16 + int(tail_sway * 1.5), cy + 6),
            (cx + back_dir * 14 + int(tail_sway * 1.5), cy + 10),
            (cx + back_dir * 8, cy + 8),
            (cx + back_dir * 4, cy + 2),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in tail_pts])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_dark"], tail_pts)
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_mid"], [
            (cx + back_dir * 6, cy - 3),
            (cx + back_dir * 11 + int(tail_sway), cy),
            (cx + back_dir * 14 + int(tail_sway * 1.5), cy + 5),
            (cx + back_dir * 12 + int(tail_sway * 1.5), cy + 8),
            (cx + back_dir * 7, cy + 6),
            (cx + back_dir * 4, cy + 2),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_light"], [
            (cx + back_dir * 7, cy - 2),
            (cx + back_dir * 10 + int(tail_sway), cy + 1),
            (cx + back_dir * 11 + int(tail_sway), cy + 4),
            (cx + back_dir * 8, cy + 4),
        ])
    def _draw_turban(surface, cx, cy, facing, phase):
        """White turban wrapping around head."""
        turban_pts = [
            (cx - 9, cy),
            (cx - 10, cy - 3),
            (cx - 7, cy - 6),
            (cx - 2, cy - 8),
            (cx + 4, cy - 8),
            (cx + 9, cy - 6),
            (cx + 11, cy - 3),
            (cx + 10, cy),
            (cx + 8, cy + 2),
            (cx - 8, cy + 2),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in turban_pts])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_dark"], turban_pts)
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_mid"], [
            (cx - 8, cy),
            (cx - 9, cy - 3),
            (cx - 6, cy - 5),
            (cx - 1, cy - 7),
            (cx + 3, cy - 7),
            (cx + 8, cy - 5),
            (cx + 10, cy - 3),
            (cx + 9, cy),
            (cx - 7, cy),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["cloth_light"], [
            (cx - 5, cy - 2),
            (cx - 6, cy - 4),
            (cx - 2, cy - 6),
            (cx + 3, cy - 6),
            (cx + 7, cy - 4),
            (cx + 8, cy - 2),
        ])
        # Wrap lines.
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["cloth_dark"],
                         (cx - 8, cy - 1), (cx + 9, cy - 1), 1)
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["cloth_dark"],
                         (cx - 7, cy - 4), (cx + 8, cy - 4), 1)
        # Highlight sheen.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["cloth_shine"],
                         (cx - 2, cy - 5, 3, 1))
    def _draw_crown(surface, cx, cy, facing, phase):
        """Gold crown with emerald gems on turban front."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Crown band.
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_darkest"], [
            (cx - 8, cy - 1),
            (cx + 8, cy - 1),
            (cx + 9, cy + 2),
            (cx - 9, cy + 2),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_dark"], [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 8, cy + 1),
            (cx - 8, cy + 1),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_mid"], [
            (cx - 6, cy),
            (cx + 6, cy),
            (cx + 7, cy + 1),
            (cx - 7, cy + 1),
        ])
        pygame.draw.line(surface, _NS_khalzaredh.PALETTE["gold_light"],
                         (cx - 5, cy), (cx + 5, cy), 1)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_shine"],
                         (cx - 2, cy, 1, 1))
        # Center peak (crown pointed top).
        peak_pts = [
            (cx - 3, cy - 1),
            (cx - 1, cy - 5),
            (cx + 1, cy - 5),
            (cx + 3, cy - 1),
        ]
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_darkest"],
                             [(p[0], p[1] + 1) for p in peak_pts])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_dark"], peak_pts)
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_mid"], [
            (cx - 2, cy - 1),
            (cx - 1, cy - 4),
            (cx + 1, cy - 4),
            (cx + 2, cy - 1),
        ])
        _NS_khalzaredh._poly(surface, _NS_khalzaredh.PALETTE["gold_light"], [
            (cx - 1, cy - 1),
            (cx, cy - 3),
            (cx + 1, cy - 1),
        ])
        # EMERALD in crown center.
        gem_alpha = _NS_khalzaredh._alpha(180 + 70 * pulse)
        for r in range(4, 0, -1):
            alpha = _NS_khalzaredh._alpha(gem_alpha * (4 - r) / 4)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["gem_mid"], alpha), (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_dark"], (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_mid"], (cx - 1, cy, 2, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_light"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_shine"], (cx, cy, 1, 1))
        # Side gems (smaller).
        for side in (-1, 1):
            gx = cx + side * 5
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_dark"], (gx - 1, cy, 2, 1))
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_mid"], (gx, cy, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action,
                       attack_progress):
        """Back arm (opposite side of sword arm)."""
        back_dir = -facing
        # Shoulder.
        shoulder_x = cx + back_dir * 10
        shoulder_y = cy - 8
        # Arm hangs down naturally.
        sway = math.sin(phase * 0.6) * 1
        elbow_x = shoulder_x + back_dir * 3 + int(sway)
        elbow_y = shoulder_y + 8
        hand_x = elbow_x + back_dir * 1 + int(sway)
        hand_y = elbow_y + 8
        # Upper arm.
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1),
                               (elbow_x + 1, elbow_y + 1), 5)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_dark"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_mid"],
                               (shoulder_x + back_dir, shoulder_y),
                               (elbow_x + back_dir, elbow_y), 2)
        # Forearm.
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                               (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_dark"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Gold armband on elbow.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_dark"],
                         (elbow_x - 2, elbow_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_mid"],
                         (elbow_x - 1, elbow_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_light"],
                         (elbow_x, elbow_y - 1, 1, 1))
        # Hand (fist).
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["shadow_deep"], (hand_x + 1, hand_y + 1), 3)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["skin_darkest"], (hand_x, hand_y), 3)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["skin_mid"], (hand_x, hand_y - 1, 1, 1))
    def _draw_sword_arm(surface, cx, cy, facing, phase, action,
                         attack_progress):
        """Front arm holding scimitar with OVERHEAD swing animation."""
        # Shoulder position.
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 8
        # Compute arm/sword angles based on attack progress.
        # NOTE: In pygame, Y+ = DOWN. So "up" = negative Y = negative sin.
        # We use angle where positive = UP (we'll negate sin when applying).
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise scimitar HIGH UP and BACK.
                t = attack_progress / 0.35
                # Angle from horizontal-back (pi) → straight up-back (0.75pi)
                arm_angle = math.pi * 0.55 + t * math.pi * 0.35  # 0.55pi → 0.9pi (up-back)
                sword_extra = math.pi * 0.3  # blade points up
            elif attack_progress < 0.6:
                # SWING DOWN: from up-back to down-forward.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * 0.9 - t * math.pi * 1.1  # 0.9pi → -0.2pi
                sword_extra = math.pi * (0.3 - t * 0.6)
            else:
                # Recovery: arm returns to rest.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.2 + t * 0.35)  # back to rest ~0.15pi
                sword_extra = math.pi * (-0.3 + t * 0.4)
        elif action == "float":
            # Sword held loosely, angled slightly down-forward.
            arm_angle = math.pi * 0.12 + math.sin(phase) * 0.05
            sword_extra = math.pi * 0.1
        else:  # idle
            arm_angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.03
            sword_extra = math.pi * 0.05
        # Elbow position.
        # Convention: arm_angle 0 = forward, pi/2 = UP, pi = backward, -pi/2 = down.
        upper_len = 10
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)  # NEGATE for pygame
        # Hand position.
        forearm_len = 10
        hand_angle = arm_angle - math.pi * 0.15
        hand_x = elbow_x + int(math.cos(hand_angle) * forearm_len) * facing
        hand_y = elbow_y - int(math.sin(hand_angle) * forearm_len)  # NEGATE
        # Upper arm.
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 6)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["skin_light"],
                         (shoulder_x + facing * 2, shoulder_y - 1, 1, 1))
        # Forearm.
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 5)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["skin_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Gold armband elbow.
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_dark"], (elbow_x, elbow_y), 3)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_mid"], (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_light"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # Wrist gauntlet (gold).
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_dark"], (hand_x, hand_y), 4)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_mid"], (hand_x, hand_y), 3)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_light"], (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_shine"],
                         (hand_x - 1, hand_y - 1, 1, 1))
        # Emerald on gauntlet.
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_dark"],
                         (hand_x, hand_y, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_light"],
                         (hand_x, hand_y, 1, 1))
        # SCIMITAR (curved blade).
        sword_angle = hand_angle + sword_extra
        _NS_khalzaredh._draw_scimitar(surface, hand_x, hand_y, sword_angle, facing, phase)
    def _draw_scimitar(surface, hx, hy, angle, facing, phase):
        """Curved scimitar sword. Angle uses convention: 0=forward, pi/2=UP."""
        # Handle extends OPPOSITE to blade direction.
        handle_len = 8
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy + int(math.sin(angle) * handle_len)  # + because handle goes down when blade up
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["leather_dark"],
                (hx, hy), (handle_end_x, handle_end_y), 3)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["leather_mid"],
                (hx, hy), (handle_end_x, handle_end_y), 2)
        # Wrap lines on handle.
        for i in range(3):
            t = (i + 1) / 4
            wx = int(hx + (handle_end_x - hx) * t)
            wy = int(hy + (handle_end_y - hy) * t)
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_dark"], (wx, wy, 1, 1))
        # Pommel (gold ball).
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                  (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_dark"],
                  (handle_end_x, handle_end_y), 3)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_mid"],
                  (handle_end_x, handle_end_y), 2)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gold_shine"],
                         (handle_end_x, handle_end_y - 1, 1, 1))
        # Crossguard (perpendicular to blade).
        perp = angle + math.pi / 2
        cg_a_x = hx + int(math.cos(perp) * 4) * facing
        cg_a_y = hy - int(math.sin(perp) * 4)
        cg_b_x = hx - int(math.cos(perp) * 4) * facing
        cg_b_y = hy + int(math.sin(perp) * 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                (cg_a_x + 1, cg_a_y + 1), (cg_b_x + 1, cg_b_y + 1), 4)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["gold_dark"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 3)
        _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["gold_mid"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 2)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_light"], (cg_a_x, cg_a_y), 1)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["gold_light"], (cg_b_x, cg_b_y), 1)
        # CURVED BLADE - scimitar shape.
        blade_start_x = hx
        blade_start_y = hy
        blade_len = 28
        # Blade extends in direction of `angle`.
        # Curve: slight bend so tip curves further.
        curve_angle_1 = angle + math.pi * 0.05
        curve_angle_2 = angle + math.pi * 0.15  # scimitar curves
        mid_x = blade_start_x + int(math.cos(curve_angle_1)
                                     * blade_len * 0.5) * facing
        mid_y = blade_start_y - int(math.sin(curve_angle_1) * blade_len * 0.5)
        tip_x = mid_x + int(math.cos(curve_angle_2)
                             * blade_len * 0.55) * facing
        tip_y = mid_y - int(math.sin(curve_angle_2) * blade_len * 0.55)
        # Draw blade as curved segments.
        segments = 10
        prev = (blade_start_x, blade_start_y)
        for i in range(1, segments + 1):
            t = i / segments
            bx = int((1 - t) ** 2 * blade_start_x + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * blade_start_y + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            thickness = max(1, 5 - int(t * 4))
            _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1),
                    thickness + 1)
            _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["blade_darkest"],
                    prev, (bx, by), thickness)
            _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["blade_dark"],
                    prev, (bx, by), max(1, thickness - 1))
            _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["blade_mid"],
                    prev, (bx, by), max(1, thickness - 2))
            _NS_khalzaredh._aaline(surface, _NS_khalzaredh.PALETTE["blade_light"],
                    (prev[0], prev[1] - 1), (bx, by - 1), 1)
            if i % 3 == 0:
                pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["blade_shine"], (bx, by - 1, 1, 1))
            prev = (bx, by)
        # Tip point.
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["blade_darkest"], (tip_x, tip_y), 2)
        _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["blade_mid"], (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["blade_shine"], (tip_x, tip_y, 1, 1))
        # Emerald in center of blade base.
        emerald_x = blade_start_x + int(math.cos(angle) * 6) * facing
        emerald_y = blade_start_y - int(math.sin(angle) * 6)
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_dark"],
                         (emerald_x - 1, emerald_y, 2, 2))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_mid"],
                         (emerald_x, emerald_y, 1, 1))
        pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["gem_shine"],
                         (emerald_x, emerald_y, 1, 1))
    def _draw_scimitar_slash(surface, boss, cx, cy, progress):
        """Sand arc slash effect - OVERHEAD swing (up → down)."""
        facing = boss.direction
        swing_t = max(0.0, min(1.0, (progress - 0.35) / 0.4))
        # Arc center at shoulder.
        arc_center_x = cx + facing * 6
        arc_center_y = cy - 4
        radius = 28
        # Slash sweeps from ABOVE (angle=pi/2, straight up) DOWN to FORWARD (angle=0).
        # Convention: 0 = forward, pi/2 = up.
        num_slices = 10
        for slice_i in range(num_slices):
            slice_t = slice_i / num_slices
            # Current sweep progress.
            sweep_angle_start = math.pi * 0.75  # up-back
            sweep_angle_end = -math.pi * 0.15   # down-forward
            # Trailing slices lag behind.
            local_swing = max(0.0, swing_t - slice_t * 0.15)
            angle = sweep_angle_start + (sweep_angle_end - sweep_angle_start) * local_swing
            fade = 1 - slice_t * 0.8
            alpha = _NS_khalzaredh._alpha(240 * fade
                            * (1 - abs(swing_t - 0.5) * 1.4))
            if alpha <= 0:
                continue
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)  # NEGATE for up
            size = max(2, int(6 * fade))
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_darkest"], alpha),
                      (arc_x, arc_y), size + 1)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                      (arc_x, arc_y), size)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                      (arc_x, arc_y), max(1, size - 1))
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                      (arc_x, arc_y), max(1, size - 2))
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                             (arc_x, arc_y, 1, 1))
        # Bright crescent arc line following current swing position.
        crescent_pts = []
        for slice_i in range(num_slices + 1):
            slice_t = slice_i / num_slices
            sweep_angle_start = math.pi * 0.75
            sweep_angle_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.1)
            angle = sweep_angle_start + (sweep_angle_end - sweep_angle_start) * local_swing
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            crescent_pts.append((arc_x, arc_y))
        if len(crescent_pts) > 1:
            for i in range(len(crescent_pts) - 1):
                alpha = _NS_khalzaredh._alpha(200 * (1 - abs(swing_t - 0.5) * 1.5))
                _NS_khalzaredh._aaline(surface, (*_NS_khalzaredh.PALETTE["sand_shine"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 2)
    def _draw_quicksand_swirl(surface, cx, cy, phase):
        """Sand particles swirling around body during W skill."""
        for i in range(20):
            angle = phase * 2 + i * math.pi / 10
            radius = 25 + int(math.sin(phase * 1.5 + i) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * radius * 0.7)
            alpha = _NS_khalzaredh._alpha(200 + math.sin(phase * 3 + i) * 55)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha), (sx, sy), 2)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha), (sx, sy), 1)
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SAND TRAIL (floating footprint replacement)
    # ============================================================
    def _draw_sand_trail(surface, cx, cy, phase, floating=False,
                         moving=False, intense=False, facing=1):
        """Sand particles rising/floating below Khaleed."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Rising sand from below (since floating).
        mist = pygame.Surface((150, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for radius in range(28, 3, -2):
            alpha = _NS_khalzaredh._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                    (75 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_khalzaredh._alpha((18 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                    (75 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 8))
        # Rising sand particles.
        for i, offset in enumerate((-22, -14, -6, 2, 10, 18, 26, -30)):
            t = (phase * 0.5 + i * 0.12) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 20)
            alpha = _NS_khalzaredh._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha), (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                             (sx, sy - 1, 1, 1))
        # Golden sparkles (bright grains).
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.1) % 1.0
            ex = cx - 24 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 2 - int(spark_t * 18)
            alpha = _NS_khalzaredh._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail behind.
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_khalzaredh._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 3, 2, 150), (5, 7, 110, 12))
        pygame.draw.ellipse(shadow, (40, 30, 10, 90), (12, 9, 96, 8))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_sand_aura(surface, x, y, phase):
        """Golden sand aura behind boss."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((190, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_khalzaredh._alpha((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_khalzaredh._aacircle(aura, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                         (95, 80), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_khalzaredh._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_khalzaredh._aacircle(aura, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                                         (95, 80), radius)
        for radius in range(25, 5, -2):
            alpha = _NS_khalzaredh._alpha((25 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_khalzaredh._aacircle(aura, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                         (95, 80), radius)
        surface.blit(aura, (x - 95, y - 80))
        # Floating sand embers.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 34 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["sand_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["sand_hot"], (sx, sy, 1, 1))
    def _draw_ground_sand_ring(surface, x, y, phase, skill):
        """Ground ring with sand runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_khalzaredh.PALETTE["sand_dark"], 200),
                            (5, 16, 150, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_khalzaredh.PALETTE["sand_darkest"], 220),
                            (14, 18, 132, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_khalzaredh.PALETTE["sand_mid"], 200),
                            (25, 20, 110, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_khalzaredh.PALETTE["gold_dark"], 180),
                            (40, 22, 80, 14), 1)
        # Arabian-style runes.
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 66)
            y2 = 28 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_khalzaredh.PALETTE["sand_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, (*_NS_khalzaredh.PALETTE["gold_light"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_khalzaredh.PALETTE["sand_hot"],
                                       _NS_khalzaredh._alpha(150 * pulse)),
                                (15, 10, 130, 38), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL: Q - SAND WAVE (projectile)
    # ============================================================
    def _draw_sand_wave_skill(surface, boss, x, y, timer, phase):
        """Forward-traveling sand wave with slow effect."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khalzaredh._target_position(boss, x, y)
        if progress < 0.15:
            # Charge in sword.
            t = progress / 0.15
            charge_x = x + facing * 30
            charge_y = y + 2
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_khalzaredh._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                         (charge_x, charge_y), r)
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_mid"],
                                     (charge_x, charge_y), cr - 2)
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_light"],
                                     (charge_x, charge_y), max(1, cr - 4))
        else:
            t = (progress - 0.15) / 0.85
            # Wave travels forward.
            start_x = x + facing * 32
            start_y = y + 2
            wave_x = int(start_x + (tx - start_x) * t)
            wave_y = int(start_y + (ty - start_y) * t)
            # Curved wave crescent shape (multiple sand crescents).
            for i in range(6):
                arc_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * arc_t)
                py = int(start_y + (ty - start_y) * arc_t)
                alpha = _NS_khalzaredh._alpha(240 - i * 30)
                # Crescent arc.
                for j in range(-3, 4):
                    ay = py + j * 3
                    ax = px + int(abs(j) * 2) * (-facing)  # curve back
                    size = 5 - abs(j)
                    if size > 0:
                        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_darkest"], alpha),
                                                 (ax, ay), size + 1)
                        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                                 (ax, ay), size)
                        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                                                 (ax, ay), max(1, size - 1))
                        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                                 (ax, ay), max(1, size - 2))
                        pygame.draw.rect(surface,
                                         (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                                         (ax, ay, 1, 1))
            # Bright leading edge.
            for r in range(12, 3, -2):
                alpha = _NS_khalzaredh._alpha(80 * (12 - r) / 12)
                _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                         (wave_x, wave_y), r)
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_shine"],
                                     (wave_x, wave_y), 3)
            pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["white"],
                             (wave_x, wave_y, 1, 1))
            # Slow effect on target.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                # Chains around target legs.
                for i in range(6):
                    angle = i * math.pi / 3 + phase * 0.5
                    cx = tx + int(math.cos(angle) * 12)
                    cy = ty + int(math.sin(angle) * 4) + 6
                    alpha = _NS_khalzaredh._alpha(240 * (1 - st))
                    _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                             (cx, cy), 3)
                    pygame.draw.rect(surface,
                                     (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                                     (cx, cy, 1, 1))
    # ============================================================
    # SKILL: W - QUICKSAND GUARD (ground rings + HP regen)
    # ============================================================
    def _draw_quicksand_ground(surface, boss, x, y, timer, phase):
        """Sand rings around boss during W."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(28 + i * 8 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_khalzaredh._alpha(200 - i * 50)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                                     (x, y + 40), r, 2)
            _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                     (x, y + 40), r, 1)
        # HP regen sparkles (green with gold).
        for i in range(8):
            angle = phase * 1.5 + i * math.pi / 4
            sr = 30 + int(math.sin(phase + i) * 5)
            sx = x + int(math.cos(angle) * sr)
            sy = y + 30 + int(math.sin(angle) * sr * 0.3)
            alpha = _NS_khalzaredh._alpha(200)
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["gem_light"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_khalzaredh.PALETTE["gem_shine"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: E - DESERT TORNADO (spinning column)
    # ============================================================
    def _draw_desert_tornado_ground(surface, boss, x, y, timer, phase):
        """Ground swirl at target for tornado."""
        tx, ty = _NS_khalzaredh._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(40 * min(1.0, progress * 3))
        if r > 3:
            # Spinning ground swirl.
            for i in range(3):
                offset_angle = phase * 3 + i * math.pi * 2 / 3
                pygame.draw.ellipse(surface,
                                    (*_NS_khalzaredh.PALETTE["sand_dark"], 200 - i * 40),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
    def _draw_desert_tornado_foreground(surface, boss, x, y, timer, phase):
        """Vertical spinning sand tornado."""
        tx, ty = _NS_khalzaredh._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Tornado height and base radius.
        max_height = 70
        height = int(max_height * min(1.0, progress * 3))
        base_r = 30
        if height < 5:
            return
        # Draw tornado as stacked ellipses (spiraling).
        num_layers = 15
        for layer_i in range(num_layers):
            layer_t = layer_i / num_layers
            layer_y = ty - int(layer_t * height)
            # Radius tapers upward slightly.
            layer_r = int(base_r * (1 - layer_t * 0.3))
            # Rotation phase.
            rot = phase * 4 + layer_i * 0.4
            # Multi-band spiral.
            for band in range(3):
                band_angle = rot + band * math.pi * 2 / 3
                bx_offset = int(math.cos(band_angle) * layer_r * 0.7)
                by_offset = int(math.sin(band_angle) * layer_r * 0.15)
                alpha = _NS_khalzaredh._alpha(180 - layer_i * 5)
                # Sand band ellipse.
                pygame.draw.ellipse(surface,
                                    (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                    (tx - layer_r + bx_offset,
                                     layer_y - 3 + by_offset,
                                     layer_r + 6, 6))
                pygame.draw.ellipse(surface,
                                    (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                                    (tx - layer_r + bx_offset + 1,
                                     layer_y - 2 + by_offset,
                                     layer_r + 4, 4))
            # Main outline ellipse (thin).
            pygame.draw.ellipse(surface,
                                (*_NS_khalzaredh.PALETTE["sand_darkest"], 150),
                                (tx - layer_r, layer_y - 3, layer_r * 2, 6), 1)
            # Bright highlights (grains).
            for _ in range(2):
                grain_angle = rot + _ * math.pi
                gx = tx + int(math.cos(grain_angle) * layer_r * 0.8)
                gy = layer_y + int(math.sin(grain_angle) * 2)
                pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["sand_hot"], (gx, gy, 1, 1))
                pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["sand_shine"], (gx, gy, 1, 1))
        # Top of tornado (thin wisp).
        top_y = ty - height
        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], 120),
                                 (tx, top_y - 3), 4)
        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_mid"], 100),
                                 (tx, top_y - 6), 3)
        _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_light"], 80),
                                 (tx, top_y - 10), 2)
    # ============================================================
    # SKILL: R - FURIOUS SANDSTORM (large forward wave)
    # ============================================================
    def _draw_sandstorm_ground(surface, boss, x, y, timer, phase):
        """Ground swirl during sandstorm."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground dust cloud extending forward.
        extent = int(120 * min(1.0, progress * 2))
        if extent > 5:
            for i in range(3):
                r_h = 30 - i * 5
                pygame.draw.ellipse(surface,
                                    (*_NS_khalzaredh.PALETTE["sand_dark"], 180 - i * 40),
                                    (x, y + 30 - r_h,
                                     extent * facing if facing > 0 else -extent,
                                     r_h * 2))
                if facing < 0:
                    pygame.draw.ellipse(surface,
                                        (*_NS_khalzaredh.PALETTE["sand_dark"], 180 - i * 40),
                                        (x - extent, y + 30 - r_h,
                                         extent, r_h * 2))
    def _draw_sandstorm_foreground(surface, boss, x, y, timer, phase):
        """Massive sandstorm wave rolling forward."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Charge-up: raising arms, gathering sand.
            t = progress / 0.2
            gather_x = x
            gather_y = y - 20
            gather_r = int(8 + t * 20)
            for r in range(gather_r + 5, 0, -2):
                alpha = _NS_khalzaredh._alpha(180 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                         (gather_x, gather_y), r)
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_mid"],
                                     (gather_x, gather_y), gather_r - 3)
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_light"],
                                     (gather_x, gather_y), max(1, gather_r - 6))
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_hot"],
                                     (gather_x, gather_y), max(1, gather_r - 10))
        else:
            # Sandstorm rolling forward.
            t = (progress - 0.2) / 0.8
            storm_dist = int(t * 180)
            storm_x = x + storm_dist * facing
            storm_y = y
            # Massive rolling wave (multi-column).
            for col_i in range(-2, 3):
                col_offset_x = col_i * 20 * facing
                col_x = storm_x - col_offset_x
                col_delay = abs(col_i) * 0.05
                col_t = max(0.0, t - col_delay)
                if col_t <= 0:
                    continue
                # Vertical sand column.
                col_height = int(60 + math.sin(phase * 2 + col_i) * 8)
                for layer_i in range(10):
                    layer_t = layer_i / 10
                    layer_y = storm_y + 20 - int(layer_t * col_height)
                    layer_w = int(18 + math.sin(phase * 3 + layer_i) * 3)
                    layer_h = int(6 + layer_t * 2)
                    alpha = _NS_khalzaredh._alpha(200 - layer_i * 8)
                    if alpha <= 0:
                        continue
                    pygame.draw.ellipse(surface,
                                        (*_NS_khalzaredh.PALETTE["sand_darkest"], alpha),
                                        (col_x - layer_w, layer_y - layer_h,
                                         layer_w * 2, layer_h * 2))
                    pygame.draw.ellipse(surface,
                                        (*_NS_khalzaredh.PALETTE["sand_dark"], alpha),
                                        (col_x - layer_w + 2, layer_y - layer_h + 1,
                                         layer_w * 2 - 4, layer_h * 2 - 2))
                    pygame.draw.ellipse(surface,
                                        (*_NS_khalzaredh.PALETTE["sand_mid"], alpha),
                                        (col_x - layer_w + 4, layer_y - layer_h + 2,
                                         layer_w * 2 - 8, layer_h * 2 - 4))
                    # Bright sand grains.
                    grain_x = col_x + int(math.sin(phase * 4 + layer_i) * layer_w * 0.7)
                    grain_y = layer_y + int(math.cos(phase * 4 + layer_i) * layer_h * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                     (grain_x, grain_y, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_khalzaredh.PALETTE["sand_hot"], alpha),
                                     (grain_x, grain_y, 1, 1))
            # Bright leading edge.
            for r in range(20, 5, -2):
                alpha = _NS_khalzaredh._alpha(100 * (20 - r) / 20)
                _NS_khalzaredh._aacircle(surface, (*_NS_khalzaredh.PALETTE["sand_light"], alpha),
                                         (storm_x, storm_y), r)
            _NS_khalzaredh._aacircle(surface, _NS_khalzaredh.PALETTE["sand_shine"],
                                     (storm_x, storm_y), 4)
            # Radial burst on leading edge.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = storm_x + int(math.cos(angle_s) * 20)
                ey = storm_y + int(math.sin(angle_s) * 15)
                pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["sand_hot"], (ex, ey, 2, 2))
                pygame.draw.rect(surface, _NS_khalzaredh.PALETTE["sand_shine"], (ex, ey, 1, 1))



# ====================================================================
# NYXAROTH (VOID-STARWEAVER) - Mini Boss
# ====================================================================

class _NS_nyxaroth:
    """Namespace nyxaroth - Cosmic Mage mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale, ethereal)
        "skin_darkest": (90, 70, 100),
        "skin_dark": (150, 125, 155),
        "skin_mid": (210, 185, 210),
        "skin_light": (240, 220, 240),
        "skin_shine": (255, 245, 255),
        # Hair (purple-silver gradient)
        "hair_darkest": (35, 20, 55),
        "hair_dark": (75, 50, 105),
        "hair_mid": (150, 115, 180),
        "hair_light": (210, 180, 230),
        "hair_shine": (245, 225, 255),
        # Dark cosmic dress (deep navy-purple)
        "dress_darkest": (8, 5, 25),
        "dress_dark": (25, 15, 55),
        "dress_mid": (55, 35, 95),
        "dress_light": (90, 65, 140),
        "dress_shine": (140, 110, 190),
        # Cosmic accents (blue crystal star-like)
        "crystal_dark": (20, 40, 90),
        "crystal_mid": (60, 110, 200),
        "crystal_light": (130, 190, 255),
        "crystal_shine": (220, 245, 255),
        # Astral purple magic (main FX)
        "astral_darkest": (20, 5, 45),
        "astral_dark": (60, 20, 120),
        "astral_mid": (130, 60, 220),
        "astral_light": (190, 130, 255),
        "astral_hot": (230, 190, 255),
        "astral_shine": (245, 230, 255),
        # Star sparkle (cyan-white)
        "star_dark": (40, 80, 160),
        "star_mid": (120, 180, 250),
        "star_light": (200, 235, 255),
        "star_shine": (255, 255, 255),
        # Void black (Supernova center)
        "void_darkest": (0, 0, 0),
        "void_dark": (10, 5, 20),
        "void_edge": (30, 10, 60),
        # Eye (glowing violet)
        "eye_iris": (140, 90, 220),
        "eye_glow": (200, 160, 255),
        "eye_hot": (240, 220, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxaroth._clamp(color)
        if _NS_nyxaroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxaroth._clamp(color)
        if _NS_nyxaroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxaroth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyxaroth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxaroth._detect_moving(boss)
        _NS_nyxaroth._update_nx_attack_anim(boss)
        attacking = (
            getattr(boss, "_nx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind (cosmic aura + starfield).
        _NS_nyxaroth._draw_cosmic_aura(surface, x, y, pulse)
        _NS_nyxaroth._draw_starfield(surface, x, y, pulse)
        _NS_nyxaroth._draw_ground_astral_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_nyxaroth._draw_cosmic_fusion_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxaroth._draw_supernova_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating).
        if attacking:
            _NS_nyxaroth._draw_nx_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxaroth._draw_nx_float(surface, boss, x, y)
        else:
            _NS_nyxaroth._draw_nx_idle(surface, boss, x, y)
        # Cosmic fusion orb around body.
        if active_skill == "e":
            _NS_nyxaroth._draw_cosmic_fusion_orbit(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_nyxaroth._draw_astral_echo_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxaroth._draw_astral_wave_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxaroth._draw_supernova_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_nx_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nx_previous_timer", 0))
        active = bool(getattr(boss, "_nx_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nx_attack_active = True
            boss._nx_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nx_attack_frame = int(
                getattr(boss, "_nx_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._nx_attack_active = False
            boss._nx_attack_frame = 0
            active = False
        boss._nx_previous_timer = timer
        boss._nx_attack_progress = (
            min(1.0, getattr(boss, "_nx_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nx_last_x"):
            boss._nx_last_x = boss.x
            boss._nx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nx_last_x)
        dy = abs(boss.y - boss._nx_last_y)
        boss._nx_last_x = boss.x
        boss._nx_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_nx_idle(surface, boss, x, y):
        """Floating idle with slow bob."""
        float_bob = int(math.sin(boss.pulse * 0.5) * 4) - 5
        _NS_nyxaroth._draw_shadow(surface, x, y + 50)
        _NS_nyxaroth._draw_astral_trail(surface, x, y + 42, boss.pulse, floating=True)
        _NS_nyxaroth._draw_nx_body(surface, x, y + float_bob,
                     boss.direction, boss.pulse, "idle")
    def _draw_nx_float(surface, boss, x, y):
        """Floating movement (mage doesn't walk)."""
        phase = boss.pulse * 1.5
        float_bob = int(math.sin(phase * 0.8) * 6) - 7
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_nyxaroth._draw_shadow(surface, x + sway, y + 50, moving=True)
        _NS_nyxaroth._draw_astral_trail(surface, x + sway, y + 42, phase,
                          floating=True, moving=True,
                          facing=boss.direction)
        _NS_nyxaroth._draw_nx_body(surface, x + sway, y + float_bob,
                     boss.direction, phase, "float")
    def _draw_nx_attack(surface, boss, x, y):
        """Cast animation: raise arm, orb charges, then projectile fires."""
        progress = getattr(boss, "_nx_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Mage doesn't lunge - just slight recoil.
        if progress < 0.4:
            # Charge-up (arm rises).
            t = progress / 0.4
            lift = -int(t * 3) - 5  # slight rise
            recoil = 0
        elif progress < 0.55:
            # Cast (small recoil).
            t = (progress - 0.4) / 0.15
            lift = -int(3) - 5
            recoil = int(t * 3) * -boss.direction  # push back slightly
        else:
            # Recovery.
            t = (progress - 0.55) / 0.45
            lift = -int(3 * (1 - t)) - 5
            recoil = int(3 * (1 - t)) * -boss.direction
        _NS_nyxaroth._draw_shadow(surface, x + recoil, y + 50)
        _NS_nyxaroth._draw_astral_trail(surface, x + recoil, y + 42, boss.pulse,
                          floating=True, intense=True)
        _NS_nyxaroth._draw_nx_body(surface, x + recoil, y + lift,
                     boss.direction, boss.pulse, "attack", progress)
        # Projectile.
        _NS_nyxaroth._draw_astral_bolt(surface, boss, x + recoil, y + lift, progress)
    # ============================================================
    # BODY (Humanoid mage: dress bottom, torso, arms, head)
    # ============================================================
    def _draw_nx_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Draw ethereal mage floating."""
        # Dress bottom (flowing).
        _NS_nyxaroth._draw_dress_bottom(surface, cx, cy + 22, facing, phase, action)
        # Body torso.
        _NS_nyxaroth._draw_nx_torso(surface, cx, cy, facing, phase, action)
        # Back arm (holding orb or hanging).
        _NS_nyxaroth._draw_back_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
        # Head with cosmic hair.
        _NS_nyxaroth._draw_nx_head(surface, cx, cy - 22, facing, phase, action)
        # Front arm (casting or holding orb).
        _NS_nyxaroth._draw_cast_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
    def _draw_dress_bottom(surface, cx, cy, facing, phase, action):
        """Flowing cosmic dress with dissolution at edges."""
        sway = math.sin(phase * 0.7) * 3
        # Main dress shape (long, tapering).
        dress_pts = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 16 + int(sway), cy + 4),
            (cx + 20 + int(sway * 1.3), cy + 14),
            (cx + 14 + int(sway * 1.5), cy + 22),
            (cx + 4, cy + 24),
            (cx - 4, cy + 24),
            (cx - 14 - int(sway * 1.5), cy + 22),
            (cx - 20 - int(sway * 1.3), cy + 14),
            (cx - 16 - int(sway), cy + 4),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in dress_pts])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["dress_darkest"], dress_pts)
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["dress_dark"], [
            (cx - 11, cy - 7),
            (cx + 11, cy - 7),
            (cx + 15 + int(sway), cy + 4),
            (cx + 18 + int(sway * 1.3), cy + 13),
            (cx + 12 + int(sway * 1.5), cy + 20),
            (cx - 12 - int(sway * 1.5), cy + 20),
            (cx - 18 - int(sway * 1.3), cy + 13),
            (cx - 15 - int(sway), cy + 4),
        ])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["dress_mid"], [
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 12 + int(sway), cy + 4),
            (cx + 14 + int(sway * 1.3), cy + 12),
            (cx + 8, cy + 16),
            (cx - 8, cy + 16),
            (cx - 14 - int(sway * 1.3), cy + 12),
            (cx - 12 - int(sway), cy + 4),
        ])
        # Dress folds/highlights.
        for i, x_off in enumerate((-10, -5, 0, 5, 10)):
            pygame.draw.line(surface, _NS_nyxaroth.PALETTE["dress_light"],
                             (cx + x_off, cy - 4),
                             (cx + x_off + int(sway * 0.6), cy + 18), 1)
        # Crystal star accents on dress.
        for cx_off, cy_off in [(-6, 0), (6, 5), (-4, 12), (5, -2)]:
            star_x = cx + cx_off
            star_y = cy + cy_off
            _NS_nyxaroth._draw_small_star(surface, star_x, star_y, phase)
        # Bottom dissolution (mist particles floating).
        for i in range(10):
            t = (phase * 0.3 + i * 0.1) % 1.0
            px = cx + int((i - 4.5) * 4) + int(math.sin(phase + i) * 3)
            py = cy + 22 + int(t * 12)
            alpha = _NS_nyxaroth._alpha(180 * (1 - t))
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha), (px, py), 2)
            pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                             (px, py, 1, 1))
            if i % 3 == 0:
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                                 (px, py - 1, 1, 1))
    def _draw_small_star(surface, cx, cy, phase):
        """Small 4-point star crystal accent."""
        pulse = math.sin(phase * 2 + cx * 0.1) * 0.4 + 0.6
        alpha = _NS_nyxaroth._alpha(200 * pulse)
        # 4-point star.
        _NS_nyxaroth._poly(surface, (*_NS_nyxaroth.PALETTE["crystal_dark"], alpha), [
            (cx, cy - 3), (cx + 1, cy), (cx, cy + 3), (cx - 1, cy),
        ])
        pygame.draw.line(surface, (*_NS_nyxaroth.PALETTE["crystal_mid"], alpha),
                         (cx - 3, cy), (cx + 3, cy), 1)
        pygame.draw.line(surface, (*_NS_nyxaroth.PALETTE["crystal_light"], alpha),
                         (cx, cy - 2), (cx, cy + 2), 1)
        pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["crystal_shine"], alpha),
                         (cx, cy, 1, 1))
    def _draw_nx_torso(surface, cx, cy, facing, phase, action):
        """Slim feminine torso with cosmic dress top."""
        # Torso outline.
        torso_pts = [
            (cx - 8, cy - 12),
            (cx - 9, cy - 8),
            (cx - 8, cy - 2),
            (cx - 6, cy + 6),
            (cx - 3, cy + 10),
            (cx + 3, cy + 10),
            (cx + 6, cy + 6),
            (cx + 8, cy - 2),
            (cx + 9, cy - 8),
            (cx + 8, cy - 12),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_pts])
        # Dress top (cosmic dark).
        dress_top_pts = [
            (cx - 8, cy - 10),
            (cx - 9, cy - 6),
            (cx - 8, cy),
            (cx - 6, cy + 6),
            (cx - 3, cy + 9),
            (cx + 3, cy + 9),
            (cx + 6, cy + 6),
            (cx + 8, cy),
            (cx + 9, cy - 6),
            (cx + 8, cy - 10),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["dress_darkest"], dress_top_pts)
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["dress_dark"], [
            (cx - 7, cy - 9),
            (cx - 8, cy - 6),
            (cx - 7, cy),
            (cx - 5, cy + 5),
            (cx + 5, cy + 5),
            (cx + 7, cy),
            (cx + 8, cy - 6),
            (cx + 7, cy - 9),
        ])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["dress_mid"], [
            (cx - 5, cy - 8),
            (cx - 6, cy - 4),
            (cx - 5, cy),
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 5, cy),
            (cx + 6, cy - 4),
            (cx + 5, cy - 8),
        ])
        # Chest crystal (V-shape neckline).
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["crystal_dark"], [
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx, cy - 3),
        ])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["crystal_mid"], [
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["crystal_light"],
                         (cx - 1, cy - 6, 2, 1))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["crystal_shine"],
                         (cx, cy - 6, 1, 1))
        # Bare shoulders (skin).
        for side in (-1, 1):
            sh_x = cx + side * 8
            sh_y = cy - 10
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_darkest"], (sh_x, sh_y), 4)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_dark"], (sh_x, sh_y), 3)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_mid"],
                      (sh_x + side, sh_y - 1), 2)
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["skin_light"],
                             (sh_x + side, sh_y - 1, 1, 1))
        # Crystal shoulder pauldrons (cosmic).
        for side in (-1, 1):
            sh_x = cx + side * 8
            sh_y = cy - 12
            _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["shadow_deep"], [
                (sh_x - 2, sh_y),
                (sh_x + 3 * side, sh_y - 3),
                (sh_x + 4 * side, sh_y + 2),
                (sh_x - 1, sh_y + 3),
            ])
            _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["crystal_dark"], [
                (sh_x - 2, sh_y),
                (sh_x + 3 * side, sh_y - 3),
                (sh_x + 3 * side, sh_y + 1),
                (sh_x - 1, sh_y + 2),
            ])
            _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["crystal_mid"], [
                (sh_x - 1, sh_y),
                (sh_x + 2 * side, sh_y - 2),
                (sh_x + 2 * side, sh_y + 1),
            ])
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["crystal_light"],
                             (sh_x + side, sh_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["crystal_shine"],
                             (sh_x + side, sh_y - 1, 1, 1))
        # Waist detail (belt with star).
        pygame.draw.line(surface, _NS_nyxaroth.PALETTE["crystal_dark"],
                         (cx - 6, cy + 6), (cx + 6, cy + 6), 1)
        _NS_nyxaroth._draw_small_star(surface, cx, cy + 6, phase)
    def _draw_nx_head(surface, cx, cy, facing, phase, action):
        """Head with flowing purple hair."""
        # Hair back (behind head, long flowing).
        _NS_nyxaroth._draw_hair_back(surface, cx, cy, facing, phase)
        # Face.
        face_pts = [
            (cx - 5, cy),
            (cx - 6, cy - 4),
            (cx - 5, cy - 7),
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 6, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx + 1, cy + 6),
            (cx - 1, cy + 6),
            (cx - 3, cy + 4),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in face_pts])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["skin_darkest"], face_pts)
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 5, cy - 4),
            (cx - 4, cy - 6),
            (cx - 1, cy - 8),
            (cx + 2, cy - 8),
            (cx + 4, cy - 6),
            (cx + 5, cy - 4),
            (cx + 4, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["skin_mid"], [
            (cx - 3, cy - 1),
            (cx - 4, cy - 4),
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 4, cy - 4),
            (cx + 3, cy - 1),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
        ])
        # Cheek highlight.
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["skin_light"],
                         (cx + facing * 2, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["skin_shine"],
                         (cx + facing * 2, cy - 2, 1, 1))
        # Hair front (bangs).
        _NS_nyxaroth._draw_hair_front(surface, cx, cy - 8, facing, phase)
        # EYES (glowing violet).
        # Main eye (facing side).
        ex = cx + facing * 2
        ey = cy - 4
        for r in range(4, 0, -1):
            alpha = _NS_nyxaroth._alpha(140 * (4 - r) / 4)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["eye_glow"], alpha), (ex, ey), r)
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["eye_iris"], (ex, ey, 2, 2))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["eye_glow"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["eye_hot"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["white"], (ex + 1, ey, 1, 1))
        # Second eye (dimmer).
        ex2 = cx - facing * 2
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
                         (ex2 - 1, ey, 2, 2))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["eye_iris"], (ex2, ey, 1, 1))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["eye_glow"], (ex2, ey, 1, 1))
        # Delicate lips.
        pygame.draw.line(surface, _NS_nyxaroth.PALETTE["hair_darkest"],
                         (cx - 1, cy + 3), (cx + 1, cy + 3), 1)
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["astral_mid"],
                         (cx, cy + 3, 1, 1))
        # Small star sparkle floating near face.
        star_offset_x = int(math.sin(phase * 1.5) * 3)
        star_offset_y = int(math.cos(phase * 1.5) * 2)
        _NS_nyxaroth._draw_small_star(surface,
                        cx + facing * 8 + star_offset_x,
                        cy - 5 + star_offset_y, phase)
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long flowing purple hair behind head."""
        sway = math.sin(phase * 0.8) * 3
        # Back hair mass.
        hair_pts = [
            (cx - 7, cy - 8),
            (cx - 9, cy - 4),
            (cx - 11 - int(sway * 0.5), cy + 4),
            (cx - 12 - int(sway), cy + 12),
            (cx - 10 - int(sway * 1.5), cy + 20),
            (cx - 6 - int(sway * 1.5), cy + 24),
            (cx - 2, cy + 22),
            (cx + 2, cy + 22),
            (cx + 6 + int(sway * 1.5), cy + 24),
            (cx + 10 + int(sway * 1.5), cy + 20),
            (cx + 12 + int(sway), cy + 12),
            (cx + 11 + int(sway * 0.5), cy + 4),
            (cx + 9, cy - 4),
            (cx + 7, cy - 8),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in hair_pts])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_darkest"], hair_pts)
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_dark"], [
            (cx - 6, cy - 7),
            (cx - 8, cy - 3),
            (cx - 10 - int(sway * 0.5), cy + 4),
            (cx - 11 - int(sway), cy + 12),
            (cx - 9 - int(sway * 1.5), cy + 18),
            (cx + 9 + int(sway * 1.5), cy + 18),
            (cx + 11 + int(sway), cy + 12),
            (cx + 10 + int(sway * 0.5), cy + 4),
            (cx + 8, cy - 3),
            (cx + 6, cy - 7),
        ])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_mid"], [
            (cx - 4, cy - 5),
            (cx - 6, cy),
            (cx - 8 - int(sway * 0.5), cy + 8),
            (cx - 6 - int(sway), cy + 15),
            (cx + 6 + int(sway), cy + 15),
            (cx + 8 + int(sway * 0.5), cy + 8),
            (cx + 6, cy),
            (cx + 4, cy - 5),
        ])
        # Hair strand highlights.
        for i, x_off in enumerate((-6, -3, 3, 6)):
            pygame.draw.line(surface, _NS_nyxaroth.PALETTE["hair_light"],
                             (cx + x_off, cy - 4),
                             (cx + x_off + int(sway * 0.3), cy + 16), 1)
        # Bright shine strand.
        pygame.draw.line(surface, _NS_nyxaroth.PALETTE["hair_shine"],
                         (cx - 2, cy - 6),
                         (cx - 1 + int(sway * 0.3), cy + 12), 1)
        # Star sparkles in hair.
        for i in range(3):
            spark_t = (phase * 0.5 + i * 0.33) % 1.0
            sx = cx + int(math.sin(phase * 2 + i * 2) * 8)
            sy = cy + int(spark_t * 20)
            alpha = _NS_nyxaroth._alpha(240 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                             (sx, sy, 1, 1))
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front bangs framing face."""
        # Bangs on both sides.
        bang_pts = [
            (cx - 6, cy),
            (cx - 7, cy - 3),
            (cx - 4, cy - 5),
            (cx - 1, cy - 6),
            (cx + 3, cy - 6),
            (cx + 6, cy - 5),
            (cx + 7, cy - 3),
            (cx + 6, cy),
            (cx + 4, cy - 1),
            (cx + 1, cy - 2),
            (cx - 2, cy - 2),
            (cx - 5, cy - 1),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_darkest"], bang_pts)
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_dark"], [
            (cx - 5, cy),
            (cx - 6, cy - 2),
            (cx - 3, cy - 4),
            (cx, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 4),
            (cx + 6, cy - 2),
            (cx + 5, cy),
            (cx - 3, cy),
        ])
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_mid"], [
            (cx - 4, cy - 1),
            (cx - 4, cy - 3),
            (cx - 1, cy - 4),
            (cx + 2, cy - 4),
            (cx + 5, cy - 3),
            (cx + 5, cy - 1),
        ])
        # Highlights.
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["hair_light"],
                         (cx - 2, cy - 4, 1, 2))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["hair_shine"],
                         (cx - 2, cy - 4, 1, 1))
        # Side bang strand (falls over one eye).
        strand_pts = [
            (cx + facing * 3, cy - 3),
            (cx + facing * 5, cy),
            (cx + facing * 4, cy + 3),
            (cx + facing * 2, cy + 2),
        ]
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_darkest"], strand_pts)
        _NS_nyxaroth._poly(surface, _NS_nyxaroth.PALETTE["hair_mid"], [
            (cx + facing * 3, cy - 2),
            (cx + facing * 4, cy),
            (cx + facing * 3, cy + 2),
        ])
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm - usually hangs or holds orb behind body."""
        back_dir = -facing
        if action == "attack" and 0.2 < attack_progress < 0.7:
            # During cast, back arm supports (raised slightly).
            shoulder_x = cx + back_dir * 8
            shoulder_y = cy - 8
            hand_x = shoulder_x + back_dir * 6
            hand_y = shoulder_y - 4
        else:
            # Hanging at side with orb behind.
            sway = math.sin(phase * 0.6) * 1
            shoulder_x = cx + back_dir * 8
            shoulder_y = cy - 8
            hand_x = shoulder_x + back_dir * 3 + int(sway)
            hand_y = shoulder_y + 12
        elbow_x = int((shoulder_x + hand_x) / 2 + back_dir * 2)
        elbow_y = int((shoulder_y + hand_y) / 2)
        # Upper arm.
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 4)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["dress_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["dress_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["dress_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)
        # Forearm (bare skin at wrist).
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["skin_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["skin_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 1)
        # Hand (small).
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_darkest"], (hand_x, hand_y), 2)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_dark"], (hand_x, hand_y), 1)
        # Small floating orb near back hand (idle only).
        if action != "attack":
            orb_x = hand_x + back_dir * 4
            orb_y = hand_y - 4 + int(math.sin(phase * 1.5) * 2)
            _NS_nyxaroth._draw_astral_orb_small(surface, orb_x, orb_y, phase)
    def _draw_cast_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - raises to cast and holds the astral orb."""
        shoulder_x = cx + facing * 8
        shoulder_y = cy - 8
        # Determine arm angle.
        # Convention: 0 = forward, pi/2 = UP.
        if action == "attack":
            if attack_progress < 0.4:
                # Wind-up: raise arm high (charging orb).
                t = attack_progress / 0.4
                arm_angle = math.pi * (0.15 + t * 0.45)  # forward → up-forward
                orb_radius = int(4 + t * 6)  # orb grows
            elif attack_progress < 0.55:
                # Cast: arm thrusts forward.
                t = (attack_progress - 0.4) / 0.15
                arm_angle = math.pi * (0.6 - t * 0.5)  # up-forward → forward
                orb_radius = int(10 - t * 6)  # orb shrinks as fired
            else:
                # Recovery: arm lowers.
                t = (attack_progress - 0.55) / 0.45
                arm_angle = math.pi * (0.1 + (1 - t) * 0.05)
                orb_radius = 3
        elif action == "float":
            # Extended forward, palm holding orb.
            arm_angle = math.pi * 0.1 + math.sin(phase * 0.7) * 0.05
            orb_radius = 4
        else:  # idle
            arm_angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.03
            orb_radius = 4
        # Elbow.
        upper_len = 9
        elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y - int(math.sin(arm_angle) * upper_len)
        # Hand (further out).
        forearm_len = 10
        hand_angle = arm_angle - math.pi * 0.05
        hand_x = elbow_x + int(math.cos(hand_angle) * forearm_len) * facing
        hand_y = elbow_y - int(math.sin(hand_angle) * forearm_len)
        # Upper arm (dress sleeve dark).
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 5)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["dress_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["dress_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["dress_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)
        # Elbow crystal ornament.
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["crystal_dark"], (elbow_x, elbow_y), 3)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["crystal_mid"], (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["crystal_light"],
                         (elbow_x, elbow_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["crystal_shine"],
                         (elbow_x, elbow_y - 1, 1, 1))
        # Forearm (bare skin).
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["skin_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["skin_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_nyxaroth._aaline(surface, _NS_nyxaroth.PALETTE["skin_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Hand (open palm holding orb).
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_darkest"], (hand_x, hand_y), 3)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["skin_mid"], (hand_x, hand_y - 1), 1)
        # ASTRAL ORB in palm.
        orb_x = hand_x + int(math.cos(hand_angle) * 4) * facing
        orb_y = hand_y - int(math.sin(hand_angle) * 4)
        _NS_nyxaroth._draw_astral_orb(surface, orb_x, orb_y, phase, orb_radius,
                        charging=(action == "attack" and attack_progress < 0.4))
    def _draw_astral_orb(surface, cx, cy, phase, radius, charging=False):
        """Purple cosmic orb (main power source in palm)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        boost = 1.5 if charging else 1.0
        # Outer glow.
        for r in range(int(radius * 3), 0, -1):
            alpha = _NS_nyxaroth._alpha(60 * (radius * 3 - r) / (radius * 3) * pulse * boost)
            if alpha > 0:
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                          (cx, cy), r)
        # Core orb layers.
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_darkest"], (cx, cy), radius + 1)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_dark"], (cx, cy), radius)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"], (cx, cy), max(1, radius - 1))
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"], (cx, cy), max(1, radius - 2))
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_hot"], (cx, cy), max(1, radius - 3))
        if radius > 4:
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"], (cx, cy), 1)
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["white"], (cx, cy, 1, 1))
        # Orbiting stars.
        for i in range(3):
            angle = phase * 2 + i * math.pi * 2 / 3
            orbit_r = radius + 3
            sx = cx + int(math.cos(angle) * orbit_r)
            sy = cy + int(math.sin(angle) * orbit_r * 0.6)
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_shine"], (sx, sy, 1, 1))
    def _draw_astral_orb_small(surface, cx, cy, phase):
        """Small floating orb (companion)."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_nyxaroth._alpha(80 * (6 - r) / 6 * pulse)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha), (cx, cy), r)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"], (cx, cy), 3)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["astral_shine"], (cx, cy, 1, 1))
    # ============================================================
    # RANGED ATTACK — ASTRAL BOLT
    # ============================================================
    def _draw_astral_bolt(surface, boss, x, y, progress):
        """Basic ranged attack: astral projectile."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_nyxaroth._target_position(boss, x, y)
        # Fire from hand position.
        start_x = x + facing * 22
        start_y = y - 8
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet-like purple trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxaroth._alpha(220 - i * 25)
            size = max(1, 6 - i)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_darkest"], alpha),
                      (px, py), size + 1)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                      (px, py), size)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                      (px, py), max(1, size - 1))
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                      (px, py), max(1, size - 2))
            if i < 3:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright bolt head.
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_darkest"], (bx, by), 7)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_dark"], (bx, by), 5)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"], (bx, by), 4)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"], (bx, by), 3)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_hot"], (bx, by), 2)
        _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["white"], (bx, by, 1, 1))
        # 4-pointed star shape overlay.
        pygame.draw.line(surface, _NS_nyxaroth.PALETTE["star_shine"],
                         (bx - 6, by), (bx + 6, by), 1)
        pygame.draw.line(surface, _NS_nyxaroth.PALETTE["star_shine"],
                         (bx, by - 6), (bx, by + 6), 1)
        # Impact.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(6 + st * 20)
            alpha = _NS_nyxaroth._alpha(240 * (1 - st))
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                      (tx, ty), radius, 3)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                      (tx, ty), max(1, radius - 4), 2)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                      (tx, ty), max(1, radius - 8), 1)
    # ============================================================
    # ASTRAL TRAIL (floating particles)
    # ============================================================
    def _draw_astral_trail(surface, cx, cy, phase, floating=False,
                            moving=False, intense=False, facing=1):
        """Cosmic particles rising below mage."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Purple mist cloud.
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.3) * 0.3 + 0.7
        for radius in range(28, 3, -2):
            alpha = _NS_nyxaroth._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_nyxaroth._alpha((18 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                    (70 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 8))
        # Rising cosmic particles.
        for i, offset in enumerate((-22, -14, -6, 2, 10, 18, 26, -30)):
            t = (phase * 0.5 + i * 0.12) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 22)
            alpha = _NS_nyxaroth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha), (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                             (sx, sy - 1, 1, 1))
        # Star sparkles.
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.1) % 1.0
            ex = cx - 24 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 2 - int(spark_t * 20)
            alpha = _NS_nyxaroth._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail behind.
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxaroth._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                          (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 3, 15, 150), (5, 7, 110, 12))
        pygame.draw.ellipse(shadow, (30, 15, 60, 90), (12, 9, 96, 8))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_cosmic_aura(surface, x, y, phase):
        """Large cosmic aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_nyxaroth._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxaroth._aacircle(aura, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                          (100, 90), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_nyxaroth._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyxaroth._aacircle(aura, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                          (100, 90), radius)
        for radius in range(28, 5, -2):
            alpha = _NS_nyxaroth._alpha((28 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_nyxaroth._aacircle(aura, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
    def _draw_starfield(surface, x, y, phase):
        """Twinkling stars around boss."""
        for i in range(20):
            angle = phase * 0.2 + i * math.pi / 10
            radius = 40 + int(math.sin(phase * 0.5 + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 10 + int(math.sin(angle) * radius * 0.55)
            twinkle = math.sin(phase * 3 + i * 1.7) * 0.5 + 0.5
            alpha = _NS_nyxaroth._alpha(200 * twinkle)
            if i % 4 == 0:
                # Big star (4-point).
                pygame.draw.line(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                                 (sx - 2, sy), (sx + 2, sy), 1)
                pygame.draw.line(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                                 (sx, sy - 2), (sx, sy + 2), 1)
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["white"], alpha),
                                 (sx, sy, 1, 1))
            else:
                # Small dot.
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                                 (sx, sy, 1, 1))
    def _draw_ground_astral_ring(surface, x, y, phase, skill):
        """Ground ring with cosmic runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxaroth.PALETTE["astral_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxaroth.PALETTE["astral_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxaroth.PALETTE["astral_mid"], 200),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_nyxaroth.PALETTE["crystal_dark"], 180),
                            (40, 24, 90, 14), 1)
        # Rune stars around ring.
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_nyxaroth.PALETTE["astral_light"], 200),
                             (x1, y1), (x2, y2), 1)
            # Small star at outer end.
            pygame.draw.line(ring, (*_NS_nyxaroth.PALETTE["star_shine"], 240),
                             (x2 - 1, y2), (x2 + 1, y2), 1)
            pygame.draw.line(ring, (*_NS_nyxaroth.PALETTE["star_shine"], 240),
                             (x2, y2 - 1), (x2, y2 + 1), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxaroth.PALETTE["astral_hot"],
                                        _NS_nyxaroth._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL: Q - ASTRAL ECHO (piercing bolt with bounce)
    # ============================================================
    def _draw_astral_echo_skill(surface, boss, x, y, timer, phase):
        """Powerful astral bolt shooting forward with lingering echo."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxaroth._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in hand.
            t = progress / 0.2
            charge_x = x + facing * 22
            charge_y = y - 12
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_nyxaroth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                          (charge_x, charge_y), r)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"],
                      (charge_x, charge_y), cr - 2)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"],
                      (charge_x, charge_y), max(1, cr - 4))
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"],
                      (charge_x, charge_y), max(1, cr - 6))
            # Sparks orbiting.
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_shine"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 26
            start_y = y - 12
            # Direct laser beam (pierces).
            beam_x = int(start_x + (tx - start_x) * min(1.0, t * 1.5))
            beam_y = int(start_y + (ty - start_y) * min(1.0, t * 1.5))
            beam_end_x = beam_x
            beam_end_y = beam_y
            # Extend beam past target.
            if t > 0.5:
                extra = (t - 0.5) / 0.5 * 80
                dx = tx - start_x
                dy = ty - start_y
                dist = max(1, math.sqrt(dx * dx + dy * dy))
                beam_end_x = int(tx + dx / dist * extra)
                beam_end_y = int(ty + dy / dist * extra)
            # Layered beam.
            for width, color, alpha_val in [
                (7, _NS_nyxaroth.PALETTE["astral_darkest"], 200),
                (5, _NS_nyxaroth.PALETTE["astral_dark"], 220),
                (3, _NS_nyxaroth.PALETTE["astral_mid"], 240),
                (2, _NS_nyxaroth.PALETTE["astral_light"], 250),
                (1, _NS_nyxaroth.PALETTE["astral_shine"], 255),
            ]:
                pygame.draw.line(surface, (*color, alpha_val),
                                 (start_x, start_y),
                                 (beam_end_x, beam_end_y), width)
            # Bright head.
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_darkest"],
                      (beam_end_x, beam_end_y), 8)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_dark"],
                      (beam_end_x, beam_end_y), 6)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"],
                      (beam_end_x, beam_end_y), 4)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"],
                      (beam_end_x, beam_end_y), 3)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"],
                      (beam_end_x, beam_end_y), 2)
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["white"],
                             (beam_end_x, beam_end_y, 1, 1))
            # 4-point star at head.
            pygame.draw.line(surface, _NS_nyxaroth.PALETTE["star_shine"],
                             (beam_end_x - 8, beam_end_y),
                             (beam_end_x + 8, beam_end_y), 1)
            pygame.draw.line(surface, _NS_nyxaroth.PALETTE["star_shine"],
                             (beam_end_x, beam_end_y - 8),
                             (beam_end_x, beam_end_y + 8), 1)
            # Trailing sparks along beam.
            beam_dx = beam_end_x - start_x
            beam_dy = beam_end_y - start_y
            beam_len = max(1, math.sqrt(beam_dx ** 2 + beam_dy ** 2))
            for i in range(int(beam_len / 12)):
                trail_t = i * 12 / beam_len
                px = int(start_x + beam_dx * trail_t)
                py = int(start_y + beam_dy * trail_t)
                perp_x = -beam_dy / beam_len
                perp_y = beam_dx / beam_len
                offset = math.sin(phase * 5 + i) * 4
                spx = int(px + perp_x * offset)
                spy = int(py + perp_y * offset)
                pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_light"], (spx, spy, 2, 2))
                pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_shine"], (spx, spy, 1, 1))
    # ============================================================
    # SKILL: W - ASTRAL WAVE (crescent wave with slow)
    # ============================================================
    def _draw_astral_wave_skill(surface, boss, x, y, timer, phase):
        """Crescent astral wave sweeping forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyxaroth._target_position(boss, x, y)
        if progress < 0.15:
            # Wind-up: swirl in hand.
            t = progress / 0.15
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                r = int(6 + t * 8)
                sx = x + facing * 22 + int(math.cos(angle) * r)
                sy = y - 12 + int(math.sin(angle) * r)
                alpha = _NS_nyxaroth._alpha(200)
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                          (sx, sy), 2)
                pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_light"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.15) / 0.85
            start_x = x + facing * 26
            start_y = y - 12
            wave_x = int(start_x + (tx - start_x) * t)
            wave_y = int(start_y + (ty - start_y) * t)
            # Crescent shape (arc of stars).
            for arc_i in range(-4, 5):
                # Curve back based on distance from center.
                curve_offset = int(abs(arc_i) * abs(arc_i) * 0.8)
                ax = wave_x - curve_offset * facing
                ay = wave_y + arc_i * 4
                fade = 1 - abs(arc_i) / 5.0
                alpha = _NS_nyxaroth._alpha(230 * fade)
                size = max(1, 5 - abs(arc_i) // 2)
                # Bright astral orb at each point.
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_darkest"], alpha),
                          (ax, ay), size + 1)
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                          (ax, ay), size)
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                          (ax, ay), max(1, size - 1))
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                          (ax, ay), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["astral_shine"], alpha),
                                 (ax, ay, 1, 1))
            # Trailing crescents (echo behind).
            for echo_i in range(1, 4):
                echo_t = max(0.0, t - echo_i * 0.08)
                echo_x = int(start_x + (tx - start_x) * echo_t)
                echo_y = int(start_y + (ty - start_y) * echo_t)
                echo_alpha_mult = 1 - echo_i * 0.25
                for arc_i in range(-3, 4):
                    curve_offset = int(abs(arc_i) * abs(arc_i) * 0.8)
                    ax = echo_x - curve_offset * facing
                    ay = echo_y + arc_i * 4
                    fade = (1 - abs(arc_i) / 4.0) * echo_alpha_mult
                    alpha = _NS_nyxaroth._alpha(180 * fade)
                    if alpha > 0:
                        _NS_nyxaroth._aacircle(surface,
                                  (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                                  (ax, ay), 2)
                        pygame.draw.rect(surface,
                                         (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                                         (ax, ay, 1, 1))
            # Star sparkles inside wave.
            for i in range(8):
                spark_angle = phase * 4 + i * math.pi / 4
                sx = wave_x + int(math.cos(spark_angle) * 12) - facing * 4
                sy = wave_y + int(math.sin(spark_angle) * 12)
                alpha = _NS_nyxaroth._alpha(240)
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                                 (sx, sy, 2, 2))
    # ============================================================
    # SKILL: E - COSMIC FUSION (buff, orbiting stars)
    # ============================================================
    def _draw_cosmic_fusion_ground(surface, boss, x, y, timer, pulse):
        """Ground swirl during fusion buff."""
        for i in range(3):
            r = int(28 + i * 6 + math.sin(pulse * 2 + i) * 3)
            alpha = _NS_nyxaroth._alpha(200 - i * 50)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                      (x, y + 40), r, 2)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                      (x, y + 40), r, 1)
    def _draw_cosmic_fusion_orbit(surface, boss, x, y, timer, phase):
        """Stars orbiting around body."""
        # Orbit around boss.
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            orbit_r = 32
            sx = x + int(math.cos(angle) * orbit_r)
            sy = y - 5 + int(math.sin(angle) * orbit_r * 0.5)
            # Star trail.
            for tr in range(3):
                trail_angle = angle - tr * 0.15
                tx_pos = x + int(math.cos(trail_angle) * orbit_r)
                ty_pos = y - 5 + int(math.sin(trail_angle) * orbit_r * 0.5)
                alpha = _NS_nyxaroth._alpha(240 - tr * 60)
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                          (tx_pos, ty_pos), max(1, 3 - tr))
            # Star.
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_dark"], (sx, sy), 4)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"], (sx, sy), 3)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"], (sx, sy), 2)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"], (sx, sy), 1)
            pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["white"], (sx, sy, 1, 1))
            # 4-point star flare.
            pygame.draw.line(surface, _NS_nyxaroth.PALETTE["star_shine"],
                             (sx - 3, sy), (sx + 3, sy), 1)
            pygame.draw.line(surface, _NS_nyxaroth.PALETTE["star_shine"],
                             (sx, sy - 3), (sx, sy + 3), 1)
    # ============================================================
    # SKILL: R - SUPERNOVA (black hole)
    # ============================================================
    def _draw_supernova_ground(surface, boss, x, y, timer, phase):
        """Ground shadow expanding under black hole."""
        tx, ty = _NS_nyxaroth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 2))
        if r > 5:
            # Dark expanding disk.
            pygame.draw.ellipse(surface, (*_NS_nyxaroth.PALETTE["void_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_nyxaroth.PALETTE["void_edge"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_nyxaroth.PALETTE["astral_darkest"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_supernova_foreground(surface, boss, x, y, timer, phase):
        """Massive black hole with spiral accretion disk."""
        tx, ty = _NS_nyxaroth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Wind-up: gathering energy.
            t = progress / 0.2
            gather_r = int(6 + t * 15)
            for r in range(gather_r + 6, 0, -2):
                alpha = _NS_nyxaroth._alpha(180 * (gather_r + 6 - r) / (gather_r + 6))
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                          (tx, ty), r)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_mid"], (tx, ty), gather_r - 3)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_light"], (tx, ty),
                      max(1, gather_r - 6))
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"], (tx, ty),
                      max(1, gather_r - 9))
            # Swirling collapse particles.
            for i in range(12):
                angle = phase * 5 + i * math.pi / 6
                spiral_r = int(30 - t * 20)
                sx = tx + int(math.cos(angle) * spiral_r)
                sy = ty + int(math.sin(angle) * spiral_r * 0.7)
                pygame.draw.rect(surface, _NS_nyxaroth.PALETTE["star_shine"], (sx, sy, 2, 2))
        elif progress < 0.8:
            # BLACK HOLE FORMED.
            t = (progress - 0.2) / 0.6
            # Central void (black).
            void_r = int(15 + t * 10)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["void_darkest"], (tx, ty), void_r + 2)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["void_dark"], (tx, ty), void_r)
            # Event horizon ring (glowing purple edge).
            for r in range(void_r + 8, void_r, -1):
                alpha = _NS_nyxaroth._alpha(200 * (r - void_r) / 8)
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_hot"], alpha),
                          (tx, ty), r, 1)
            _NS_nyxaroth._aacircle(surface, _NS_nyxaroth.PALETTE["astral_shine"], (tx, ty), void_r + 1, 1)
            # Accretion disk (spiral).
            for arm_i in range(3):
                arm_offset = arm_i * math.pi * 2 / 3
                for step_i in range(20):
                    step_t = step_i / 20
                    spiral_angle = phase * 3 + arm_offset + step_t * math.pi * 4
                    spiral_r = void_r + 3 + int(step_t * 40)
                    sx = tx + int(math.cos(spiral_angle) * spiral_r)
                    sy = ty + int(math.sin(spiral_angle) * spiral_r * 0.4)
                    alpha = _NS_nyxaroth._alpha(240 - step_i * 8)
                    _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                              (sx, sy), 3)
                    _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                              (sx, sy), 2)
                    _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                              (sx, sy), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_nyxaroth.PALETTE["astral_shine"], alpha),
                                     (sx, sy, 1, 1))
            # Pulling stars inward.
            for i in range(20):
                pull_t = (phase * 0.8 + i * 0.05) % 1.0
                pull_angle = i * math.pi / 10
                start_r = 80
                cur_r = int(start_r * (1 - pull_t))
                if cur_r < void_r:
                    continue
                sx = tx + int(math.cos(pull_angle) * cur_r)
                sy = ty + int(math.sin(pull_angle) * cur_r * 0.55)
                alpha = _NS_nyxaroth._alpha(220 * (1 - pull_t))
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_light"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Bright center flare (pulsing).
            flare_pulse = math.sin(phase * 4) * 0.5 + 0.5
            for r in range(void_r + 15, void_r, -2):
                alpha = _NS_nyxaroth._alpha(80 * flare_pulse)
                _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_hot"], alpha),
                          (tx, ty), r)
        else:
            # Aftermath: collapse and burst outward.
            t = (progress - 0.8) / 0.2
            burst_r = int(30 + t * 60)
            alpha = _NS_nyxaroth._alpha(240 * (1 - t))
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_dark"], alpha),
                      (tx, ty), burst_r + 5, 4)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_mid"], alpha),
                      (tx, ty), burst_r, 3)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                      (tx, ty), max(1, burst_r - 8), 2)
            _NS_nyxaroth._aacircle(surface, (*_NS_nyxaroth.PALETTE["astral_shine"], alpha),
                      (tx, ty), max(1, burst_r - 16), 1)
            # Radial burst lines.
            for i in range(16):
                angle = i * math.pi / 8
                ex = tx + int(math.cos(angle) * burst_r)
                ey = ty + int(math.sin(angle) * burst_r * 0.7)
                pygame.draw.line(surface, (*_NS_nyxaroth.PALETTE["astral_light"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_nyxaroth.PALETTE["star_shine"], alpha),
                                 (ex, ey, 2, 2))



# ====================================================================
# VESHTRAX (SAPPHIRE EXECUTOR) - Mini Boss
# ====================================================================

class _NS_veshtrax:
    """Namespace veshtrax - mini boss noble duelist tema biru + gold."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Blue royal (main theme)
        "blue_darkest": (5, 10, 30),
        "blue_dark": (15, 35, 80),
        "blue_mid": (40, 90, 175),
        "blue_light": (100, 165, 240),
        "blue_hot": (170, 220, 255),
        "blue_shine": (230, 245, 255),
        # Deep navy shadow
        "navy_darkest": (3, 5, 18),
        "navy_dark": (10, 20, 45),
        # Silver armor
        "silver_darkest": (30, 35, 50),
        "silver_dark": (75, 85, 105),
        "silver_mid": (140, 150, 175),
        "silver_light": (210, 220, 235),
        "silver_shine": (250, 252, 255),
        # Skin (fair noble)
        "skin_darkest": (100, 75, 75),
        "skin_dark": (175, 145, 140),
        "skin_mid": (225, 200, 190),
        "skin_light": (245, 230, 220),
        "skin_shine": (255, 245, 240),
        # Hair (golden blonde)
        "hair_darkest": (55, 35, 10),
        "hair_dark": (125, 90, 30),
        "hair_mid": (210, 165, 70),
        "hair_light": (245, 215, 130),
        "hair_shine": (255, 240, 180),
        # Gold trim (accents)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (110, 75, 20),
        "gold_mid": (200, 155, 55),
        "gold_light": (250, 220, 120),
        "gold_shine": (255, 250, 220),
        # Blade (silver with blue glow)
        "blade_darkest": (25, 30, 55),
        "blade_dark": (70, 90, 140),
        "blade_mid": (155, 185, 235),
        "blade_light": (220, 235, 255),
        "blade_shine": (255, 255, 255),
        # Blue crystal petals
        "crystal_dark": (20, 55, 130),
        "crystal_mid": (75, 155, 245),
        "crystal_light": (170, 220, 255),
        "crystal_shine": (240, 250, 255),
        # Eye (piercing blue)
        "eye_dark": (15, 40, 90),
        "eye_mid": (75, 155, 235),
        "eye_light": (180, 225, 255),
        "eye_shine": (255, 255, 255),
        # Cape (deep blue with lighter inner)
        "cape_darkest": (5, 10, 25),
        "cape_dark": (15, 30, 70),
        "cape_mid": (35, 75, 155),
        "cape_light": (90, 145, 220),
        "cape_shine": (170, 210, 250),
        # Ambient mist
        "mist_dark": (10, 20, 45),
        "mist_mid": (40, 80, 145),
        "mist_light": (130, 180, 235),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_veshtrax._clamp(color)
        if _NS_veshtrax.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_veshtrax._clamp(color)
        if _NS_veshtrax.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_veshtrax._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 250 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_veshtrax(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_veshtrax._update_vst_attack_anim(boss)
        attacking = (
            getattr(boss, "_vst_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_veshtrax._draw_blue_aura(surface, x, y, pulse)
        _NS_veshtrax._draw_ground_ring(surface, x, y + 55, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_veshtrax._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_veshtrax._draw_phantom_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_veshtrax._draw_sovereignty_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with elegant bob
        # E skill makes body invisible (phantom) for middle portion
        show_body = True
        if active_skill == "e" and skill_timer > 0:
            e_duration = 60
            e_progress = 1 - skill_timer / e_duration
            if 0.25 < e_progress < 0.75:
                show_body = False
        floating_bob = math.sin(pulse * 0.7) * 5
        if show_body:
            if attacking:
                _NS_veshtrax._draw_vst_attack(surface, boss, x, y - floating_bob)
            else:
                _NS_veshtrax._draw_vst_idle(surface, boss, x, y - floating_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_veshtrax._draw_puncture_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_veshtrax._draw_dash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_veshtrax._draw_phantom_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_veshtrax._draw_sovereignty_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vst_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vst_previous_timer", 0))
        active = bool(getattr(boss, "_vst_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vst_attack_active = True
            boss._vst_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vst_attack_frame = int(getattr(boss, "_vst_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vst_attack_active = False
            boss._vst_attack_frame = 0
            active = False
        boss._vst_previous_timer = timer
        boss._vst_attack_progress = (
            min(1.0, getattr(boss, "_vst_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vst_idle(surface, boss, x, y):
        _NS_veshtrax._draw_shadow(surface, x, y + 60)
        _NS_veshtrax._draw_blue_petals(surface, x, y, boss.pulse)
        _NS_veshtrax._draw_vst_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_vst_attack(surface, boss, x, y):
        progress = getattr(boss, "_vst_attack_progress", 0.0)
        # Elegant rapier thrust animation
        if progress < 0.3:
            t = progress / 0.3
            swing_offset = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            swing_offset = int((-3 + t * 12)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.55) / 0.45
            swing_offset = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_veshtrax._draw_shadow(surface, x + swing_offset, y + 60)
        _NS_veshtrax._draw_blue_petals(surface, x + swing_offset, y, boss.pulse, intense=True)
        _NS_veshtrax._draw_vst_body(surface, x + swing_offset, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        _NS_veshtrax._draw_rapier_slash(surface, x + swing_offset, y - lift,
                                         boss.direction, progress)
    # ============================================================
    # BODY (noble swordsman)
    # ============================================================
    def _draw_vst_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw duelist body: cape → legs → torso → arms → head → hair → rapier."""
        # Order: cape (behind) → legs → torso → arms → shoulder → head → hair → rapier
        _NS_veshtrax._draw_flowing_cape(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_veshtrax._draw_noble_legs(surface, cx, cy + 20, facing, phase)
        _NS_veshtrax._draw_noble_torso(surface, cx, cy, facing, phase)
        _NS_veshtrax._draw_vst_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_veshtrax._draw_shoulder_pauldrons(surface, cx, cy - 8, facing, phase)
        # Head lunge on attack
        head_lunge = 0
        if action == "attack":
            if attack_progress < 0.3:
                t = attack_progress / 0.3
                head_lunge = -int(t * 2) * facing
            elif attack_progress < 0.55:
                t = (attack_progress - 0.3) / 0.25
                head_lunge = int((-2 + t * 6)) * facing
            else:
                t = (attack_progress - 0.55) / 0.45
                head_lunge = int(4 * (1 - t)) * facing
        _NS_veshtrax._draw_vst_head(surface, cx + head_lunge, cy - 24, facing, phase)
        _NS_veshtrax._draw_wavy_hair(surface, cx + head_lunge, cy - 22, facing, phase)
        # RAPIER (held by near hand)
        _NS_veshtrax._draw_rapier(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_flowing_cape(surface, cx, cy, facing, phase, action, attack_progress):
        """Blue cape flowing behind body."""
        # Cape flap animation
        if action == "attack":
            flap = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            flap = math.sin(phase * 0.8) * 4
        # Cape starts from shoulders, flows down-back
        back_dir = -facing
        # Cape shape (billowing behind)
        cape_pts = [
            # Top attachment (shoulders)
            (cx + facing * 4, cy - 14),
            (cx + back_dir * 2, cy - 14),
            (cx + back_dir * 8, cy - 12),
            # Flowing back-out
            (cx + back_dir * 14, cy - 4),
            (cx + back_dir * 18 + int(flap), cy + 4),
            (cx + back_dir * 22 + int(flap), cy + 14),
            (cx + back_dir * 20 + int(flap * 0.7), cy + 24),
            (cx + back_dir * 14 + int(flap * 0.5), cy + 32),
            # Bottom
            (cx + back_dir * 6, cy + 30),
            (cx, cy + 26),
            (cx + facing * 2, cy + 18),
            (cx + facing * 4, cy + 8),
        ]
        # Shadow
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in cape_pts])
        # Cape layers (dark to light)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["cape_darkest"], cape_pts)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["cape_dark"], [
            (cx + facing * 4, cy - 13),
            (cx + back_dir * 2, cy - 13),
            (cx + back_dir * 7, cy - 11),
            (cx + back_dir * 12, cy - 3),
            (cx + back_dir * 16 + int(flap), cy + 4),
            (cx + back_dir * 19 + int(flap), cy + 13),
            (cx + back_dir * 17 + int(flap * 0.7), cy + 22),
            (cx + back_dir * 12 + int(flap * 0.5), cy + 30),
            (cx + back_dir * 5, cy + 28),
            (cx, cy + 24),
            (cx + facing * 2, cy + 16),
            (cx + facing * 3, cy + 6),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["cape_mid"], [
            (cx + facing * 3, cy - 11),
            (cx + back_dir * 1, cy - 11),
            (cx + back_dir * 5, cy - 9),
            (cx + back_dir * 10, cy - 2),
            (cx + back_dir * 13 + int(flap), cy + 5),
            (cx + back_dir * 15 + int(flap), cy + 12),
            (cx + back_dir * 13 + int(flap * 0.6), cy + 20),
            (cx + back_dir * 9, cy + 26),
            (cx + back_dir * 3, cy + 24),
            (cx, cy + 20),
            (cx + facing * 2, cy + 12),
        ])
        # Cape inner highlight (fold shine)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["cape_light"], [
            (cx + back_dir * 3, cy - 5),
            (cx + back_dir * 6, cy + 2),
            (cx + back_dir * 8, cy + 10),
            (cx + back_dir * 6, cy + 18),
            (cx + back_dir * 2, cy + 18),
            (cx, cy + 10),
            (cx + facing, cy + 2),
        ])
        # Cape fold lines (vertical dark streaks)
        for stripe_i, x_off in enumerate((3, 8, 13)):
            stripe_x_start = cx + back_dir * x_off
            stripe_x_end = cx + back_dir * (x_off + int(flap * 0.4))
            pygame.draw.line(surface, _NS_veshtrax.PALETTE["cape_darkest"],
                             (stripe_x_start, cy - 5),
                             (stripe_x_end, cy + 22), 1)
        # Bright shine along top edge
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["cape_shine"],
                         (cx + facing * 2, cy - 12),
                         (cx + back_dir * 4, cy - 10), 1)
        # Gold trim along top (collar area)
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["gold_dark"],
                         (cx + facing * 4, cy - 14),
                         (cx + back_dir * 8, cy - 12), 1)
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["gold_mid"],
                         (cx + facing * 4, cy - 13),
                         (cx + back_dir * 8, cy - 11), 1)
    def _draw_noble_legs(surface, cx, cy, facing, phase):
        """Slim armored legs."""
        for side_mult in (-1, 1):
            leg_x = cx + side_mult * 6
            # Thigh
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"], [
                (leg_x - 4 + 2, cy - 6 + 2), (leg_x + 4 + 2, cy - 6 + 2),
                (leg_x + 5 + 2, cy + 5 + 2), (leg_x - 5 + 2, cy + 5 + 2),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_darkest"], [
                (leg_x - 4, cy - 6), (leg_x + 4, cy - 6),
                (leg_x + 5, cy + 5), (leg_x - 5, cy + 5),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_dark"], [
                (leg_x - 3, cy - 5), (leg_x + 3, cy - 5),
                (leg_x + 4, cy + 4), (leg_x - 4, cy + 4),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_mid"], [
                (leg_x - 2, cy - 4), (leg_x + 2, cy - 4),
                (leg_x + 3, cy + 3), (leg_x - 3, cy + 3),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_light"], [
                (leg_x - 1, cy - 3), (leg_x + 1, cy - 3),
                (leg_x + 1, cy + 2), (leg_x - 1, cy + 2),
            ])
            # Knee gold trim
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_dark"],
                             (leg_x - 5, cy, 10, 3))
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_mid"],
                             (leg_x - 4, cy + 1, 8, 1))
            # Lower leg / boot (silver armored)
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"], [
                (leg_x - 5 + 2, cy + 5 + 2), (leg_x + 5 + 2, cy + 5 + 2),
                (leg_x + 6 + 2, cy + 15 + 2), (leg_x - 6 + 2, cy + 15 + 2),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_darkest"], [
                (leg_x - 5, cy + 5), (leg_x + 5, cy + 5),
                (leg_x + 6, cy + 15), (leg_x - 6, cy + 15),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_dark"], [
                (leg_x - 4, cy + 6), (leg_x + 4, cy + 6),
                (leg_x + 5, cy + 14), (leg_x - 5, cy + 14),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_mid"], [
                (leg_x - 3, cy + 8), (leg_x + 3, cy + 8),
                (leg_x + 4, cy + 13), (leg_x - 4, cy + 13),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_light"], [
                (leg_x - 2, cy + 8), (leg_x + 1, cy + 8),
                (leg_x + 2, cy + 12), (leg_x - 2, cy + 12),
            ])
            # Boot gold trim
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_dark"],
                             (leg_x - 6, cy + 13, 12, 3))
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_mid"],
                             (leg_x - 5, cy + 14, 10, 1))
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_light"],
                             (leg_x - 1, cy + 14, 2, 1))
    def _draw_noble_torso(surface, cx, cy, facing, phase):
        """Slim armored torso with center chest gem."""
        breath = math.sin(phase * 0.6) * 1
        # Slim knight torso
        torso_pts = [
            (cx - 9, cy + 10),
            (cx - 11, cy + 2),
            (cx - 11, cy - 5 - int(breath)),
            (cx - 9, cy - 11),
            (cx - 4, cy - 14),
            (cx + 4, cy - 14),
            (cx + 9, cy - 11),
            (cx + 11, cy - 5 - int(breath)),
            (cx + 11, cy + 2),
            (cx + 9, cy + 10),
        ]
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_darkest"], torso_pts)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_dark"], [
            (cx - 8, cy + 9), (cx - 10, cy + 1), (cx - 10, cy - 4),
            (cx - 8, cy - 10), (cx - 3, cy - 13), (cx + 3, cy - 13),
            (cx + 8, cy - 10), (cx + 10, cy - 4), (cx + 10, cy + 1),
            (cx + 8, cy + 9),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_mid"], [
            (cx - 6, cy + 7), (cx - 8, cy), (cx - 7, cy - 9),
            (cx - 2, cy - 12), (cx + 2, cy - 12), (cx + 7, cy - 9),
            (cx + 8, cy), (cx + 6, cy + 7),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_light"], [
            (cx - 4, cy + 5), (cx - 6, cy - 1), (cx - 3, cy - 8),
            (cx + 3, cy - 8), (cx + 6, cy - 1), (cx + 4, cy + 5),
        ])
        # Chest highlight
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["blue_shine"], [
            (cx - 2, cy - 5), (cx + 2, cy - 5),
            (cx + 3, cy - 1), (cx + 1, cy + 2), (cx - 1, cy + 2), (cx - 3, cy - 1),
        ])
        # Silver plate details (breastplate)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_dark"], [
            (cx - 5, cy - 8), (cx + 5, cy - 8),
            (cx + 6, cy - 4), (cx + 4, cy + 2), (cx - 4, cy + 2), (cx - 6, cy - 4),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_mid"], [
            (cx - 4, cy - 7), (cx + 4, cy - 7),
            (cx + 5, cy - 4), (cx + 3, cy + 1), (cx - 3, cy + 1), (cx - 5, cy - 4),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_light"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 3, cy - 3), (cx + 1, cy), (cx - 1, cy), (cx - 3, cy - 3),
        ])
        # Skin (V-neckline)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["skin_dark"], [
            (cx - 3, cy - 11), (cx + 3, cy - 11),
            (cx + 1, cy - 8), (cx - 1, cy - 8),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["skin_mid"], [
            (cx - 2, cy - 10), (cx + 2, cy - 10),
            (cx + 1, cy - 9), (cx - 1, cy - 9),
        ])
        # BLUE CRYSTAL GEM on chest (signature)
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_veshtrax._alpha(240 * gem_pulse)
        # Diamond shape
        gem_pts = [
            (cx, cy - 5),
            (cx + 3, cy - 2),
            (cx, cy + 2),
            (cx - 3, cy - 2),
        ]
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in gem_pts])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["crystal_dark"], gem_pts)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["crystal_mid"], [
            (cx, cy - 4), (cx + 2, cy - 2), (cx, cy + 1), (cx - 2, cy - 2),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["crystal_light"], [
            (cx, cy - 3), (cx + 1, cy - 2), (cx, cy), (cx - 1, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["crystal_shine"], (cx, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["white"], (cx, cy - 2, 1, 1))
        # Gem glow
        for r in range(5, 0, -1):
            alpha = _NS_veshtrax._alpha(80 * (5 - r) / 5 * gem_pulse)
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha),
                                    (cx, cy - 2), r)
        # Gold trim borders
        # Neckline
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["gold_dark"],
                         (cx - 6, cy - 10), (cx + 6, cy - 10), 1)
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["gold_mid"],
                         (cx - 6, cy - 11), (cx + 6, cy - 11), 1)
        # Waist
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_darkest"],
                         (cx - 10, cy + 8, 20, 3))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_dark"],
                         (cx - 9, cy + 9, 18, 2))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_mid"],
                         (cx - 8, cy + 10, 16, 1))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_light"],
                         (cx - 1, cy + 10, 2, 1))
    def _draw_vst_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two slim armored arms."""
        idle_sway = math.sin(phase * 0.6) * 2
        # FAR ARM (behind body — free hand, gestures elegantly)
        far_shoulder = (cx - facing * 10, cy - 10)
        far_elbow = (cx - facing * 14, cy - 3 + int(idle_sway * 0.3))
        far_hand = (cx - facing * 18, cy + 6 + int(idle_sway * 0.4))
        _NS_veshtrax._draw_noble_arm(surface, far_shoulder, far_elbow, far_hand,
                                      facing, phase, dark=True)
        # NEAR ARM (holds RAPIER) — thrusts on attack
        if action == "attack":
            # Rapier thrust
            if attack_progress < 0.3:
                # Wind-up: arm back, sword back
                t = attack_progress / 0.3
                angle = math.radians(-30 - t * 100) * facing
                arm_len = 18
            elif attack_progress < 0.55:
                # THRUST forward
                t = (attack_progress - 0.3) / 0.25
                angle = math.radians(-130 + t * 150) * facing
                arm_len = 22 + int(t * 6)  # arm extends
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                angle = math.radians(20 - t * 40) * facing
                arm_len = 22 - int(t * 4)
            shoulder = (cx + facing * 10, cy - 10)
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            hand = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_veshtrax._draw_noble_arm(surface, shoulder, elbow, hand,
                                          facing, phase, dark=False)
        else:
            # Idle: sword held elegantly forward/side
            near_shoulder = (cx + facing * 10, cy - 10)
            near_elbow = (cx + facing * 14, cy - 3 + int(idle_sway * 0.3))
            near_hand = (cx + facing * 18, cy + 8 + int(idle_sway * 0.4))
            _NS_veshtrax._draw_noble_arm(surface, near_shoulder, near_elbow, near_hand,
                                          facing, phase, dark=False)
    def _draw_noble_arm(surface, shoulder, elbow, hand, facing, phase, dark=False):
        """Slim armored arm with blue+silver."""
        blue_dark_c = _NS_veshtrax.PALETTE["blue_darkest"] if dark else _NS_veshtrax.PALETTE["blue_dark"]
        blue_mid_c = _NS_veshtrax.PALETTE["blue_dark"] if dark else _NS_veshtrax.PALETTE["blue_mid"]
        blue_light_c = _NS_veshtrax.PALETTE["blue_mid"] if dark else _NS_veshtrax.PALETTE["blue_light"]
        # Shadow
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                              (shoulder[0] + 2, shoulder[1] + 2),
                              (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                              (elbow[0] + 2, elbow[1] + 2),
                              (hand[0] + 2, hand[1] + 2), 5)
        # Upper arm (blue)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["blue_darkest"], shoulder, elbow, 6)
        _NS_veshtrax._aaline(surface, blue_dark_c, shoulder, elbow, 4)
        _NS_veshtrax._aaline(surface, blue_mid_c,
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 3)
        _NS_veshtrax._aaline(surface, blue_light_c,
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 1)
        # Gold band on upper arm
        mid_ux = (shoulder[0] + elbow[0]) // 2
        mid_uy = (shoulder[1] + elbow[1]) // 2
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_dark"], (mid_ux, mid_uy), 3)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_mid"], (mid_ux, mid_uy), 2)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_light"], (mid_ux, mid_uy, 1, 1))
        # Elbow joint (silver armored)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["silver_darkest"],
                         (elbow[0] - 3, elbow[1] - 3, 7, 7))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["silver_dark"],
                         (elbow[0] - 3, elbow[1] - 3, 6, 6))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["silver_mid"],
                         (elbow[0] - 2, elbow[1] - 2, 4, 4))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["silver_light"],
                         (elbow[0] - 1, elbow[1] - 2, 2, 2))
        # Forearm (silver gauntlet)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["silver_darkest"], elbow, hand, 5)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["silver_dark"], elbow, hand, 3)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["silver_mid"],
                              (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 2)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["silver_light"],
                              (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 1)
        # Gold wrist band
        wrist_ux = int(elbow[0] * 0.25 + hand[0] * 0.75)
        wrist_uy = int(elbow[1] * 0.25 + hand[1] * 0.75)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_dark"], (wrist_ux, wrist_uy), 3)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_mid"], (wrist_ux, wrist_uy), 2)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_light"],
                         (wrist_ux, wrist_uy - 1, 1, 1))
        # HAND (armored gauntlet)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                           (hand[0] + 1, hand[1] + 1), 4)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["silver_darkest"], hand, 4)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["silver_dark"], hand, 3)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["silver_mid"], hand, 2)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["silver_light"],
                         (hand[0], hand[1] - 1, 1, 1))
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase):
        """Elegant pauldrons with blue crystal accent."""
        for side in (-1, 1):
            base_x = cx + side * 11
            base_y = cy
            # Pauldron dome shape (smaller for noble style)
            pauld_pts = [
                (base_x - 5, base_y - 1), (base_x - 4, base_y - 7),
                (base_x, base_y - 9), (base_x + 3, base_y - 8),
                (base_x + 6, base_y - 5), (base_x + 6, base_y),
                (base_x + 4, base_y + 3), (base_x - 4, base_y + 3),
            ]
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                                [(px + 2, py + 2) for px, py in pauld_pts])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_darkest"], pauld_pts)
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_dark"], [
                (base_x - 4, base_y - 1), (base_x - 3, base_y - 6),
                (base_x, base_y - 8), (base_x + 3, base_y - 7),
                (base_x + 5, base_y - 4), (base_x + 5, base_y),
                (base_x + 3, base_y + 2), (base_x - 3, base_y + 2),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_mid"], [
                (base_x - 2, base_y - 1), (base_x - 2, base_y - 5),
                (base_x, base_y - 7), (base_x + 2, base_y - 6),
                (base_x + 4, base_y - 3), (base_x + 4, base_y),
                (base_x + 3, base_y + 1), (base_x - 2, base_y + 1),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["silver_light"], [
                (base_x - 1, base_y - 4), (base_x + 1, base_y - 5),
                (base_x + 3, base_y - 2), (base_x + 1, base_y),
            ])
            # Gold trim rim
            pygame.draw.line(surface, _NS_veshtrax.PALETTE["gold_dark"],
                             (base_x - 5, base_y + 2), (base_x + 5, base_y + 2), 2)
            pygame.draw.line(surface, _NS_veshtrax.PALETTE["gold_mid"],
                             (base_x - 5, base_y + 2), (base_x + 5, base_y + 2), 1)
            # BLUE CRYSTAL SHARD on pauldron top (small)
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            crystal_alpha = _NS_veshtrax._alpha(220 * pulse)
            # Crystal shard shape
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"], [
                (base_x - 1 + 1, base_y - 7 + 1),
                (base_x + 1, base_y - 12 + 1),
                (base_x + 2 + 1, base_y - 7 + 1),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["crystal_dark"], [
                (base_x - 1, base_y - 7), (base_x, base_y - 12), (base_x + 2, base_y - 7),
            ])
            _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["crystal_mid"], [
                (base_x, base_y - 7), (base_x, base_y - 12), (base_x + 1, base_y - 9),
            ])
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["crystal_shine"],
                             (base_x, base_y - 12, 1, 1))
            # Crystal glow
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], crystal_alpha),
                                    (base_x, base_y - 10), 2)
    def _draw_vst_head(surface, cx, cy, facing, phase):
        """Handsome noble face with piercing blue eyes."""
        # Face shape (slightly angular, masculine noble)
        head_pts = [
            (cx - 6, cy + 5), (cx - 7, cy + 1), (cx - 7, cy - 4),
            (cx - 5, cy - 8), (cx - 1, cy - 10), (cx + 3, cy - 10),
            (cx + 6, cy - 7), (cx + 7, cy - 3), (cx + 7, cy + 2),
            (cx + 5, cy + 6), (cx, cy + 7),
        ]
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in head_pts])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["skin_darkest"], head_pts)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["skin_dark"], [
            (cx - 6, cy + 4), (cx - 6, cy), (cx - 6, cy - 3),
            (cx - 4, cy - 7), (cx, cy - 9), (cx + 3, cy - 9),
            (cx + 5, cy - 6), (cx + 6, cy - 2), (cx + 6, cy + 1),
            (cx + 4, cy + 5), (cx, cy + 6),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["skin_mid"], [
            (cx - 4, cy + 3), (cx - 5, cy - 1), (cx - 4, cy - 5),
            (cx - 1, cy - 7), (cx + 3, cy - 7), (cx + 5, cy - 4),
            (cx + 5, cy + 1), (cx + 3, cy + 4), (cx, cy + 5),
        ])
        # Cheek highlight
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["skin_light"], [
            (cx + facing * 2, cy - 3), (cx + facing * 4, cy - 1),
            (cx + facing * 3, cy + 2), (cx + facing, cy),
        ])
        # BLUE EYES (piercing gaze)
        _NS_veshtrax._draw_blue_eye(surface, cx - 3, cy - 3, phase)
        _NS_veshtrax._draw_blue_eye(surface, cx + 3, cy - 3, phase)
        # Sharp eyebrows
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["hair_dark"],
                         (cx - 5, cy - 5), (cx - 1, cy - 5), 1)
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["hair_dark"],
                         (cx + 1, cy - 5), (cx + 5, cy - 5), 1)
        # Nose (small)
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["skin_darkest"],
                         (cx, cy - 1), (cx, cy + 2), 1)
        # Confident smirk (small curve)
        pygame.draw.line(surface, _NS_veshtrax.PALETTE["skin_darkest"],
                         (cx - 1, cy + 3), (cx + 2, cy + 3), 1)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["skin_darkest"], (cx + 2, cy + 2, 1, 1))
    def _draw_blue_eye(surface, ex, ey, phase):
        """Piercing blue eye."""
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        # Halo
        for r in range(3, 0, -1):
            alpha = _NS_veshtrax._alpha(80 * (3 - r) / 3 * pulse)
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["eye_mid"], alpha), (ex, ey), r)
        # Eye white
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["white"], (ex - 1, ey - 1, 3, 2))
        # Iris (blue)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["eye_dark"], (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["eye_mid"], (ex, ey, 2, 1))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["eye_light"], (ex + 1, ey, 1, 1))
        # Sparkle
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["eye_shine"], (ex, ey, 1, 1))
    def _draw_wavy_hair(surface, cx, cy, facing, phase):
        """Wavy blonde hair (medium length)."""
        sway = math.sin(phase * 0.6) * 2
        # Main hair shape (behind head, medium length)
        hair_pts = [
            (cx - 8, cy - 6),
            (cx - 10, cy - 2),
            (cx - 11 + int(sway), cy + 6),
            (cx - 10 + int(sway), cy + 12),
            (cx - 6, cy + 16),
            (cx + 6, cy + 16),
            (cx + 10 - int(sway), cy + 12),
            (cx + 11 - int(sway), cy + 6),
            (cx + 10, cy - 2),
            (cx + 8, cy - 6),
            (cx + 5, cy - 9), (cx - 5, cy - 9),
        ]
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in hair_pts])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_darkest"], hair_pts)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_dark"], [
            (cx - 7, cy - 5), (cx - 9, cy - 1),
            (cx - 10 + int(sway), cy + 5),
            (cx - 9 + int(sway), cy + 11),
            (cx - 4, cy + 14),
            (cx + 4, cy + 14),
            (cx + 9 - int(sway), cy + 11),
            (cx + 10 - int(sway), cy + 5),
            (cx + 9, cy - 1), (cx + 7, cy - 5),
            (cx + 4, cy - 8), (cx - 4, cy - 8),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_mid"], [
            (cx - 6, cy - 3), (cx - 7, cy + 2),
            (cx - 8 + int(sway), cy + 8),
            (cx - 2, cy + 12), (cx + 2, cy + 12),
            (cx + 8 - int(sway), cy + 8),
            (cx + 7, cy + 2), (cx + 6, cy - 3),
        ])
        # Highlights
        for streak_x in (-5, -2, 2, 5):
            for streak_i in range(3):
                sy_start = cy - 2 + streak_i * 5
                pygame.draw.line(surface, _NS_veshtrax.PALETTE["hair_light"],
                                 (cx + streak_x, sy_start),
                                 (cx + streak_x + int(sway * 0.5), sy_start + 4), 1)
        # Bright shine
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["hair_shine"], (cx - 3, cy - 4, 1, 3))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["hair_shine"], (cx + 3, cy - 4, 1, 3))
        # Front bangs (side-swept)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_dark"], [
            (cx - 6, cy - 5), (cx - 4, cy - 9), (cx + 1, cy - 10),
            (cx + 4, cy - 9), (cx + 6, cy - 5),
            (cx + 3, cy - 4), (cx, cy - 6), (cx - 3, cy - 4),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_mid"], [
            (cx - 5, cy - 5), (cx - 3, cy - 8), (cx + 1, cy - 9),
            (cx + 4, cy - 8), (cx + 5, cy - 5),
            (cx + 2, cy - 4), (cx, cy - 6), (cx - 2, cy - 4),
        ])
        # Side-swept lock (falling to one side)
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_dark"], [
            (cx + facing * 3, cy - 8),
            (cx + facing * 6, cy - 5),
            (cx + facing * 7, cy - 1),
            (cx + facing * 5, cy - 2),
            (cx + facing * 4, cy - 6),
        ])
        _NS_veshtrax._poly(surface, _NS_veshtrax.PALETTE["hair_mid"], [
            (cx + facing * 4, cy - 7),
            (cx + facing * 5, cy - 3),
            (cx + facing * 4, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["hair_light"],
                         (cx + facing * 5, cy - 6, 1, 1))
    def _draw_rapier(surface, cx, cy, facing, phase, action, attack_progress):
        """Elegant thin silver rapier with blue glow."""
        # Determine hand position and sword angle
        if action == "attack":
            if attack_progress < 0.3:
                # Wind-up (arm back)
                t = attack_progress / 0.3
                sword_angle = math.radians(-30 - t * 100) * facing
                arm_len = 18
            elif attack_progress < 0.55:
                # THRUST
                t = (attack_progress - 0.3) / 0.25
                sword_angle = math.radians(-130 + t * 150) * facing
                arm_len = 22 + int(t * 6)
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                sword_angle = math.radians(20 - t * 40) * facing
                arm_len = 22 - int(t * 4)
            shoulder = (cx + facing * 10, cy - 10)
            hand = (shoulder[0] + int(math.cos(sword_angle) * arm_len),
                    shoulder[1] + int(math.sin(sword_angle) * arm_len))
            # Sword direction matches arm
            blade_angle = sword_angle
        else:
            # Idle: sword pointed forward+down
            idle_sway = math.sin(phase * 0.6) * 2
            hand = (cx + facing * 18, cy + 8 + int(idle_sway * 0.4))
            blade_angle = math.radians(20) * facing  # forward and slightly down
        # Sword direction
        ux = math.cos(blade_angle)
        uy = math.sin(blade_angle)
        # Blade (long thin rapier)
        blade_len = 34
        blade_tip = (hand[0] + int(ux * blade_len),
                     hand[1] + int(uy * blade_len))
        # Perpendicular for width
        perp_x = -uy
        perp_y = ux
        # Shadow
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                              (hand[0] + 2, hand[1] + 2),
                              (blade_tip[0] + 2, blade_tip[1] + 2), 3)
        # BLADE - thin elegant with silver + blue glow
        # Blue glow surrounding blade
        for r in range(6, 0, -2):
            glow_alpha = _NS_veshtrax._alpha(60 * (6 - r) / 6)
            # Draw glow as thick lines
            for pt_i in range(0, blade_len, 3):
                px = int(hand[0] + ux * pt_i)
                py = int(hand[1] + uy * pt_i)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], glow_alpha),
                                        (px, py), r)
        # Blade body (silver, thin)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["shadow_deep"], hand, blade_tip, 3)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["blade_darkest"], hand, blade_tip, 3)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["blade_dark"], hand, blade_tip, 2)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["blade_mid"],
                              (hand[0] + int(perp_x), hand[1] + int(perp_y)),
                              (blade_tip[0] + int(perp_x), blade_tip[1] + int(perp_y)), 1)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["blade_light"], hand, blade_tip, 1)
        # Blade tip glow (bright)
        _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["blade_shine"], blade_tip, 2)
        _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["crystal_light"], blade_tip, 3)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["white"], (blade_tip[0], blade_tip[1], 1, 1))
        # CROSSGUARD (small perpendicular bar at hand)
        guard_len = 6
        guard_a = (hand[0] + int(perp_x * guard_len),
                   hand[1] + int(perp_y * guard_len))
        guard_b = (hand[0] - int(perp_x * guard_len),
                   hand[1] - int(perp_y * guard_len))
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["shadow_deep"],
                              (guard_a[0] + 1, guard_a[1] + 1),
                              (guard_b[0] + 1, guard_b[1] + 1), 3)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["gold_darkest"], guard_a, guard_b, 3)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["gold_dark"], guard_a, guard_b, 2)
        _NS_veshtrax._aaline(surface, _NS_veshtrax.PALETTE["gold_mid"],
                              (guard_a[0], guard_a[1] - 1),
                              (guard_b[0], guard_b[1] - 1), 1)
        # Guard tips (small decorative circles)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_light"], guard_a, 2)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_light"], guard_b, 2)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_shine"], (guard_a[0], guard_a[1], 1, 1))
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_shine"], (guard_b[0], guard_b[1], 1, 1))
        # BASKET HILT (ornate ring near guard)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_darkest"], hand, 4, 1)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_dark"], hand, 3, 1)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_mid"], hand, 2, 1)
        # HANDLE (below hand - small grip pommel)
        handle_bottom_x = hand[0] - int(ux * 5)
        handle_bottom_y = hand[1] - int(uy * 5)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_darkest"],
                           (handle_bottom_x + 1, handle_bottom_y + 1), 3)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_dark"],
                           (handle_bottom_x, handle_bottom_y), 3)
        pygame.draw.circle(surface, _NS_veshtrax.PALETTE["gold_mid"],
                           (handle_bottom_x, handle_bottom_y), 2)
        pygame.draw.rect(surface, _NS_veshtrax.PALETTE["gold_light"],
                         (handle_bottom_x - 1, handle_bottom_y - 1, 1, 1))
    # ============================================================
    # RAPIER SLASH (basic attack arc)
    # ============================================================
    def _draw_rapier_slash(surface, cx, cy, facing, progress):
        """Blue slash arc from rapier — sharp and quick (thrust style)."""
        if progress < 0.3 or progress > 0.7:
            return
        t = (progress - 0.3) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_veshtrax._alpha(255 * intensity)
        # For thrust: narrow forward slash (short arc)
        arc_cx = cx + facing * 24
        arc_cy = cy + 2
        arc_r = 20
        # Narrower arc for rapier thrust
        start_angle = math.radians(-45) if facing > 0 else math.radians(180 + 45)
        end_angle = math.radians(45) if facing > 0 else math.radians(180 - 45)
        sweep = start_angle + (end_angle - start_angle) * t
        trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
        prev_pt = None
        num_segments = 10
        for i in range(num_segments + 1):
            seg_t = i / num_segments
            angle = trail_start + (sweep - trail_start) * seg_t
            px = arc_cx + int(math.cos(angle) * arc_r)
            py = arc_cy + int(math.sin(angle) * arc_r)
            if prev_pt is not None:
                for thickness, color in [
                    (5, (*_NS_veshtrax.PALETTE["blue_darkest"], alpha // 3)),
                    (3, (*_NS_veshtrax.PALETTE["blue_dark"], alpha // 2)),
                    (2, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha)),
                    (1, (*_NS_veshtrax.PALETTE["crystal_light"], alpha)),
                ]:
                    pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
            prev_pt = (px, py)
        # Forward THRUST energy line (extra visual for pierce style)
        thrust_end_x = arc_cx + facing * 30
        thrust_end_y = arc_cy
        for thickness, color in [
            (4, (*_NS_veshtrax.PALETTE["blue_dark"], alpha // 2)),
            (2, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha)),
            (1, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha)),
        ]:
            pygame.draw.line(surface, color, (arc_cx, arc_cy), (thrust_end_x, thrust_end_y),
                             thickness)
        # Blue crystal shards along arc
        for i in range(5):
            angle = math.radians(-45) + math.radians(90) * (i / 5)
            if facing < 0:
                angle = math.radians(180) - angle
            shard_r = arc_r + int(math.sin(i + progress * 8) * 3)
            sx = arc_cx + int(math.cos(angle) * shard_r)
            sy = arc_cy + int(math.sin(angle) * shard_r)
            # Small crystal shard (triangle)
            _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                (sx, sy - 2), (sx - 1, sy + 1), (sx + 1, sy + 1),
            ])
            _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha), [
                (sx, sy - 2), (sx, sy), (sx + 1, sy),
            ])
            pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                             (sx, sy - 2, 1, 1))
    # ============================================================
    # BLUE PETALS (ambient particles)
    # ============================================================
    def _draw_blue_petals(surface, cx, cy, phase, intense=False):
        """Blue crystal petals floating around."""
        strength = 1.4 if intense else 1.0
        # Orbiting petals
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 40 + int(math.sin(phase + i) * 10)
            px = cx + int(math.cos(angle) * radius)
            py = cy + int(math.sin(angle) * radius * 0.5)
            alpha = _NS_veshtrax._alpha(230 * strength)
            # Petal shape (small diamond/leaf)
            _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                (px, py - 2), (px + 1, py), (px, py + 2), (px - 1, py),
            ])
            _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha), [
                (px, py - 1), (px + 1, py), (px, py + 1), (px - 1, py),
            ])
            pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                             (px, py, 1, 1))
        # Rising petals
        for i in range(6):
            t = (phase * 0.4 + i * 0.17) % 1.0
            rx = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            ry = cy + 25 - int(t * 45)
            alpha = _NS_veshtrax._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                # Small falling petal
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                    (rx, ry - 2), (rx + 1, ry), (rx, ry + 2), (rx - 1, ry),
                ])
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha), [
                    (rx, ry - 1), (rx + 1, ry), (rx, ry),
                ])
        # Small sparkles
        for i in range(10):
            spark_t = (phase * 0.6 + i * 0.1) % 1.0
            sx = cx - 30 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 20 - int(spark_t * 40)
            alpha = _NS_veshtrax._alpha(220 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 8, 20, 170), (5, 8, 110, 10))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_blue_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_veshtrax._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_veshtrax._aacircle(aura, (*_NS_veshtrax.PALETTE["mist_dark"], alpha),
                                        (110, 100), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_veshtrax._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_veshtrax._aacircle(aura, (*_NS_veshtrax.PALETTE["mist_mid"], alpha),
                                        (110, 100), radius)
        for radius in range(32, 5, -3):
            alpha = _NS_veshtrax._alpha((32 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_veshtrax._aacircle(aura, (*_NS_veshtrax.PALETTE["blue_dark"], alpha),
                                        (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating outer blue sparks
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 50 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["crystal_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["crystal_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 52), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_veshtrax.PALETTE["mist_dark"], 200),
                            (5, 17, 160, 25), 3)
        pygame.draw.ellipse(ring, (*_NS_veshtrax.PALETTE["blue_darkest"], 220),
                            (14, 19, 142, 21), 2)
        pygame.draw.ellipse(ring, (*_NS_veshtrax.PALETTE["blue_dark"], 230),
                            (25, 21, 120, 17), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 45)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 70)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_veshtrax.PALETTE["crystal_mid"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.line(ring, (*_NS_veshtrax.PALETTE["crystal_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_veshtrax.PALETTE["crystal_shine"],
                                        _NS_veshtrax._alpha(150 * pulse)),
                                (14, 11, 142, 37), 1)
        surface.blit(ring, (x - 85, y - 26))
    # ============================================================
    # SKILL Q - PUNCTURE (range projectile - straight line beam)
    # ============================================================
    def _draw_puncture_skill(surface, boss, x, y, timer, phase):
        """Straight sword beam that pierces enemies."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_veshtrax._target_position(boss, x, y)
        # Start from sword tip
        start_x = x + facing * 32
        start_y = y - 2
        if progress < 0.25:
            # Charge at sword tip
            t = progress / 0.25
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_veshtrax._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["crystal_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["crystal_light"],
                                    (start_x, start_y), max(1, cr - 4))
            _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["crystal_shine"],
                                    (start_x, start_y), max(1, cr - 6))
            pygame.draw.rect(surface, _NS_veshtrax.PALETTE["white"], (start_x, start_y, 1, 1))
            # Small crystal shards gathering
            for i in range(6):
                ang = phase * 4 + i * math.pi / 3
                sx = start_x + int(math.cos(ang) * (cr + 3))
                sy = start_y + int(math.sin(ang) * (cr + 3))
                pygame.draw.rect(surface, _NS_veshtrax.PALETTE["crystal_shine"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.25) / 0.75
            # Direction from start to target
            dx = tx - start_x
            dy = ty - start_y
            travel_len = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / travel_len, dy / travel_len
            # Beam extends toward target
            beam_end_x = int(start_x + ux * travel_len * min(1.0, t * 1.5))
            beam_end_y = int(start_y + uy * travel_len * min(1.0, t * 1.5))
            # Fade in/out
            beam_intensity = 1.0
            if t > 0.8:
                beam_intensity = 1 - (t - 0.8) / 0.2
            # STRAIGHT LINE BEAM (multi-layer)
            for thickness, color, alpha_mult in [
                (10, _NS_veshtrax.PALETTE["blue_darkest"], 0.7),
                (7, _NS_veshtrax.PALETTE["blue_dark"], 0.85),
                (5, _NS_veshtrax.PALETTE["blue_mid"], 1.0),
                (3, _NS_veshtrax.PALETTE["crystal_mid"], 1.0),
                (2, _NS_veshtrax.PALETTE["crystal_light"], 1.0),
                (1, _NS_veshtrax.PALETTE["crystal_shine"], 1.0),
            ]:
                actual_alpha = _NS_veshtrax._alpha(240 * beam_intensity * alpha_mult)
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (beam_end_x, beam_end_y), thickness)
            # Bright core center
            pygame.draw.line(surface, (*_NS_veshtrax.PALETTE["white"],
                                        _NS_veshtrax._alpha(255 * beam_intensity)),
                             (start_x, start_y), (beam_end_x, beam_end_y), 1)
            # Perpendicular direction
            perp_x = -uy
            perp_y = ux
            # Crystal shards flying along beam
            for i in range(12):
                shard_t = (phase * 2 + i * 0.09) % 1.0
                shard_x = start_x + int((beam_end_x - start_x) * shard_t)
                shard_y = start_y + int((beam_end_y - start_y) * shard_t)
                offset = math.sin(phase * 5 + i) * 4
                shard_x += int(perp_x * offset)
                shard_y += int(perp_y * offset)
                alpha = _NS_veshtrax._alpha(240 * beam_intensity * (1 - abs(offset) / 5))
                # Small crystal
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                    (shard_x, shard_y - 2), (shard_x + 1, shard_y),
                    (shard_x, shard_y + 2), (shard_x - 1, shard_y),
                ])
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha), [
                    (shard_x, shard_y - 1), (shard_x + 1, shard_y), (shard_x, shard_y),
                ])
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (shard_x, shard_y, 1, 1))
            # Impact at target end
            if t > 0.5:
                impact_r = int(15 + (t - 0.5) * 25)
                impact_alpha = _NS_veshtrax._alpha(240 * beam_intensity)
                # Big burst
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["blue_darkest"], impact_alpha),
                                        (tx, ty), impact_r + 3, 3)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["blue_mid"], impact_alpha),
                                        (tx, ty), impact_r, 2)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], impact_alpha),
                                        (tx, ty), max(1, impact_r - 5), 2)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], impact_alpha),
                                        (tx, ty), max(1, impact_r - 10), 1)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["white"], impact_alpha),
                                        (tx, ty), max(1, impact_r // 4))
                # Radial burst (crystal shards flying out)
                for i in range(12):
                    ang_s = i * math.pi / 6
                    ex = tx + int(math.cos(ang_s) * impact_r)
                    ey = ty + int(math.sin(ang_s) * impact_r)
                    pygame.draw.line(surface, (*_NS_veshtrax.PALETTE["crystal_light"], impact_alpha),
                                     (tx, ty), (ex, ey), 2)
                    # Crystal shard tip
                    _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], impact_alpha), [
                        (ex, ey - 2), (ex + 1, ey), (ex, ey + 2), (ex - 1, ey),
                    ])
                    pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["white"], impact_alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - THORNY ASSAULT (dash)
    # ============================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Dash line trail on ground."""
        tx, ty = _NS_veshtrax._target_position(boss, x, y)
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Trail from starting position to target direction
        if progress < 0.7:
            alpha = _NS_veshtrax._alpha(200 * (1 - progress))
            for w, c in [(6, _NS_veshtrax.PALETTE["blue_darkest"]),
                         (3, _NS_veshtrax.PALETTE["crystal_mid"]),
                         (1, _NS_veshtrax.PALETTE["crystal_light"])]:
                pygame.draw.line(surface, (*c, alpha), (x, y + 55),
                                 (tx, ty + 20), w)
    def _draw_dash_foreground(surface, boss, x, y, timer, phase):
        """Afterimages of boss dashing forward."""
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # After-images streaking behind
        for i in range(7):
            offset = i * 15 * -facing
            alpha = _NS_veshtrax._alpha(200 * (1 - progress) * (1 - i / 7))
            if alpha <= 0:
                continue
            # Ghost silhouette (blue tinted)
            afterimage = pygame.Surface((30, 70), pygame.SRCALPHA)
            for r in range(15, 0, -2):
                _NS_veshtrax._aacircle(afterimage,
                                        (*_NS_veshtrax.PALETTE["crystal_mid"],
                                         alpha * (15 - r) // 15),
                                        (15, 35), r)
            _NS_veshtrax._aacircle(afterimage,
                                    (*_NS_veshtrax.PALETTE["crystal_light"], alpha),
                                    (15, 35), 8)
            _NS_veshtrax._aacircle(afterimage,
                                    (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                    (15, 35), 4)
            surface.blit(afterimage, (x + offset - 15, y - 35))
        # Dash streak lines (horizontal)
        for i in range(10):
            streak_y = y - 15 + i * 4
            streak_len = int(60 * (1 - progress))
            end_x = x - facing * streak_len
            alpha = _NS_veshtrax._alpha(220 * (1 - progress) * (1 - i / 10))
            if alpha > 0:
                pygame.draw.line(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha),
                                 (x, streak_y), (end_x, streak_y), 2)
                pygame.draw.line(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (x, streak_y), (end_x, streak_y), 1)
        # Speed lines with crystal petals
        for i in range(8):
            petal_t = (phase * 2 + i * 0.12) % 1.0
            px = x - facing * int(petal_t * 60) + int(math.sin(phase + i) * 5)
            py = y - 15 + int(math.cos(phase + i) * 15)
            alpha = _NS_veshtrax._alpha(220 * (1 - progress) * (1 - petal_t))
            if alpha > 0:
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                    (px, py - 2), (px + 1, py), (px, py + 2), (px - 1, py),
                ])
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL E - PHANTOM EXECUTION (blink)
    # ============================================================
    def _draw_phantom_ground(surface, boss, x, y, timer, phase):
        """Rings on ground where boss was + where boss appears."""
        tx, ty = _NS_veshtrax._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Origin ring (fading)
        if progress < 0.5:
            fade = 1 - progress / 0.5
            for i in range(2):
                r = int(30 + i * 6)
                alpha = _NS_veshtrax._alpha(220 * fade - i * 60)
                if alpha > 0:
                    _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha),
                                            (x, y + 55), r, 2)
        # Target ring (growing where boss will appear)
        if progress > 0.25:
            t_target = (progress - 0.25) / 0.75
            for i in range(2):
                r = int((30 + i * 6) * min(1.0, t_target * 2))
                alpha = _NS_veshtrax._alpha(220 - i * 60)
                if alpha > 0:
                    _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha),
                                            (tx, ty + 20), r, 2)
    def _draw_phantom_foreground(surface, boss, x, y, timer, phase):
        """Phantom dissolve/reappear effect."""
        tx, ty = _NS_veshtrax._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.25:
            # PHASE 1: Dissolving (body still shown, particles dissolve out)
            t = progress / 0.25
            for i in range(20):
                ang = i * math.pi / 10
                dist = int(t * 40)
                dx = x + int(math.cos(ang) * dist)
                dy = y + int(math.sin(ang) * dist * 0.7) - 20
                alpha = _NS_veshtrax._alpha(230 * (1 - t * 0.3))
                # Petal particle
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                    (dx, dy - 2), (dx + 1, dy), (dx, dy + 2), (dx - 1, dy),
                ])
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha), [
                    (dx, dy - 1), (dx + 1, dy), (dx, dy + 1),
                ])
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (dx, dy, 1, 1))
        elif progress < 0.75:
            # PHASE 2: Phantom trail from origin to target
            t = (progress - 0.25) / 0.5
            # Fading blue silhouette at origin
            fade_alpha = _NS_veshtrax._alpha(180 * (1 - t))
            for r in range(20, 0, -2):
                a = _NS_veshtrax._alpha(fade_alpha * (20 - r) / 20)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], a),
                                        (x, y - 5), r)
            # Traveling phantom particles
            for i in range(12):
                path_t = max(0, t - i * 0.06)
                if path_t <= 0:
                    continue
                px = int(x + (tx - x) * path_t)
                py = int((y - 5) + (ty - (y - 5)) * path_t)
                alpha = _NS_veshtrax._alpha(240 - i * 22)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha),
                                        (px, py), 4)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha),
                                        (px, py), 3)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha),
                                        (px, py), 2)
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["white"], alpha),
                                 (px, py, 1, 1))
            # Appearing silhouette at target (growing)
            appear_alpha = _NS_veshtrax._alpha(200 * t)
            for r in range(int(t * 20), 0, -2):
                a = _NS_veshtrax._alpha(appear_alpha * (r) / max(1, int(t * 20)))
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], a),
                                        (tx, ty - 5), r)
        else:
            # PHASE 3: Reappearing (body coming back)
            t = (progress - 0.75) / 0.25
            # Explosion of petals at target (welcome back)
            for i in range(15):
                ang = i * math.pi / 7.5
                dist = int(t * 35)
                dx = tx + int(math.cos(ang) * dist)
                dy = ty + int(math.sin(ang) * dist * 0.7) - 5
                alpha = _NS_veshtrax._alpha(240 * (1 - t * 0.5))
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                    (dx, dy - 2), (dx + 1, dy), (dx, dy + 2), (dx - 1, dy),
                ])
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha), [
                    (dx, dy - 1), (dx + 1, dy), (dx, dy),
                ])
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (dx, dy, 1, 1))
            # Slash arc behind target (execution!)
            slash_intensity = math.sin(t * math.pi)
            slash_alpha = _NS_veshtrax._alpha(230 * slash_intensity)
            arc_r = 25
            start_ang = math.radians(-60) if facing > 0 else math.radians(180 + 60)
            end_ang = math.radians(60) if facing > 0 else math.radians(180 - 60)
            prev_pt = None
            for i in range(12):
                seg_t = i / 11
                ang = start_ang + (end_ang - start_ang) * seg_t
                sx = tx + int(math.cos(ang) * arc_r)
                sy = ty + int(math.sin(ang) * arc_r)
                if prev_pt is not None:
                    for thickness, color in [
                        (5, (*_NS_veshtrax.PALETTE["blue_darkest"], slash_alpha // 3)),
                        (3, (*_NS_veshtrax.PALETTE["crystal_mid"], slash_alpha)),
                        (2, (*_NS_veshtrax.PALETTE["crystal_light"], slash_alpha)),
                        (1, (*_NS_veshtrax.PALETTE["crystal_shine"], slash_alpha)),
                    ]:
                        pygame.draw.line(surface, color, prev_pt, (sx, sy), thickness)
                prev_pt = (sx, sy)
    # ============================================================
    # SKILL R - SOVEREIGNTY (multi-slash finale)
    # ============================================================
    def _draw_sovereignty_ground(surface, boss, x, y, timer, phase):
        """Big ground area at target with crystal pattern."""
        tx, ty = _NS_veshtrax._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 1.8))
        if r > 5:
            # Big concentric rings
            for ring_i in range(3):
                ring_r = r - ring_i * 12
                if ring_r <= 0:
                    continue
                alpha = _NS_veshtrax._alpha(200 - ring_i * 40)
                pygame.draw.ellipse(surface, (*_NS_veshtrax.PALETTE["blue_darkest"], alpha),
                                    (tx - ring_r, ty - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha),
                                    (tx - ring_r + 3, ty - ring_r // 3 + 2,
                                     ring_r * 2 - 6, ring_r * 2 // 3 - 4), 1)
            # Star pattern lines from center
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.2
                ex = tx + int(math.cos(ang) * r)
                ey = ty + int(math.sin(ang) * r * 0.4)
                pygame.draw.line(surface, (*_NS_veshtrax.PALETTE["crystal_light"], 200),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], 200),
                                 (tx, ty), (ex, ey), 1)
    def _draw_sovereignty_foreground(surface, boss, x, y, timer, phase):
        """Multi-slash pattern from all directions (blue rapier storm)."""
        tx, ty = _NS_veshtrax._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.25:
            # PHASE 1: Wind-up (energy gathering + circle warning)
            t = progress / 0.25
            # Warning circle at target
            r_warn = int(50 * t)
            warn_alpha = _NS_veshtrax._alpha(220 * t)
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], warn_alpha),
                                    (tx, ty), r_warn, 2)
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], warn_alpha),
                                    (tx, ty), r_warn, 1)
            # Rune circle
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(ang) * r_warn)
                sy = ty + int(math.sin(ang) * r_warn * 0.4)
                pygame.draw.rect(surface, _NS_veshtrax.PALETTE["crystal_shine"], (sx, sy, 3, 3))
                pygame.draw.rect(surface, _NS_veshtrax.PALETTE["white"], (sx, sy, 1, 1))
            # Energy gather at boss
            gather_r = int(4 + t * 12)
            for r in range(gather_r + 4, 0, -1):
                alpha = _NS_veshtrax._alpha(180 * (gather_r + 4 - r) / (gather_r + 4))
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha),
                                        (x, y - 5), r)
            _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["crystal_hot"] if False
                                    else _NS_veshtrax.PALETTE["crystal_light"],
                                    (x, y - 5), max(1, gather_r - 4))
        elif progress < 0.75:
            # PHASE 2: MULTI-SLASH — many slash arcs cross through target
            t = (progress - 0.25) / 0.5
            intensity = math.sin(t * math.pi)
            # Number of slashes based on progress (build up)
            num_slashes = int(t * 12) + 4
            for slash_i in range(num_slashes):
                # Each slash appears/fades at different time
                slash_delay = slash_i * 0.05
                slash_t = max(0, t - slash_delay)
                if slash_t > 0.5:
                    continue
                slash_intensity = math.sin(slash_t * 2 * math.pi) if slash_t < 0.5 else 0
                if slash_intensity <= 0:
                    continue
                # Random angle for each slash (deterministic based on slash_i)
                slash_angle = slash_i * math.pi / 6 + phase * 0.3
                slash_len = 60
                # Slash line through target
                sx1 = tx - int(math.cos(slash_angle) * slash_len)
                sy1 = ty - int(math.sin(slash_angle) * slash_len)
                sx2 = tx + int(math.cos(slash_angle) * slash_len)
                sy2 = ty + int(math.sin(slash_angle) * slash_len)
                alpha = _NS_veshtrax._alpha(255 * slash_intensity * intensity)
                # Multi-layer slash
                for thickness, color in [
                    (6, (*_NS_veshtrax.PALETTE["blue_darkest"], alpha // 3)),
                    (4, (*_NS_veshtrax.PALETTE["blue_dark"], alpha // 2)),
                    (3, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha)),
                    (2, (*_NS_veshtrax.PALETTE["crystal_light"], alpha)),
                    (1, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha)),
                ]:
                    pygame.draw.line(surface, color, (sx1, sy1), (sx2, sy2), thickness)
                # Crystal shards at slash endpoints
                for pt in [(sx1, sy1), (sx2, sy2)]:
                    _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                        (pt[0], pt[1] - 3), (pt[0] + 2, pt[1]),
                        (pt[0], pt[1] + 3), (pt[0] - 2, pt[1]),
                    ])
                    _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha), [
                        (pt[0], pt[1] - 1), (pt[0] + 1, pt[1]), (pt[0], pt[1] + 1),
                    ])
                    pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["white"], alpha),
                                     (pt[0], pt[1], 1, 1))
            # Central impact glow at target
            central_r = int(15 + t * 25)
            central_alpha = _NS_veshtrax._alpha(240 * intensity)
            for r in range(central_r, 3, -2):
                a = _NS_veshtrax._alpha(central_alpha * (central_r - r) / central_r)
                _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], a),
                                        (tx, ty), r)
            _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["crystal_shine"], (tx, ty), 4)
            _NS_veshtrax._aacircle(surface, _NS_veshtrax.PALETTE["white"], (tx, ty), 2)
            # Crystal petals blowing outward
            for i in range(20):
                pet_ang = i * math.pi / 10 + phase * 0.4
                pet_r = int(30 + t * 40 + math.sin(phase * 2 + i) * 5)
                px = tx + int(math.cos(pet_ang) * pet_r)
                py = ty + int(math.sin(pet_ang) * pet_r * 0.6)
                alpha = _NS_veshtrax._alpha(230 * intensity)
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                    (px, py - 2), (px + 1, py), (px, py + 2), (px - 1, py),
                ])
                _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], alpha), [
                    (px, py - 1), (px + 1, py), (px, py),
                ])
                pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                 (px, py, 1, 1))
        else:
            # PHASE 3: Aftermath (fading crystals + big burst)
            t = (progress - 0.75) / 0.25
            # Big final burst ring
            burst_r = int(60 + t * 30)
            burst_alpha = _NS_veshtrax._alpha(220 * (1 - t))
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_mid"], burst_alpha),
                                    (tx, ty), burst_r, 3)
            _NS_veshtrax._aacircle(surface, (*_NS_veshtrax.PALETTE["crystal_light"], burst_alpha),
                                    (tx, ty), burst_r, 1)
            # Falling crystal petals
            for i in range(15):
                fall_t = (phase * 0.7 + i * 0.08) % 1.0
                fx = tx + int(math.sin(phase + i) * 40)
                fy = ty - 30 + int(fall_t * 60)
                alpha = _NS_veshtrax._alpha(220 * (1 - t) * (1 - fall_t))
                if alpha > 0:
                    _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_dark"], alpha), [
                        (fx, fy - 2), (fx + 1, fy), (fx, fy + 2), (fx - 1, fy),
                    ])
                    _NS_veshtrax._poly(surface, (*_NS_veshtrax.PALETTE["crystal_light"], alpha), [
                        (fx, fy - 1), (fx + 1, fy), (fx, fy),
                    ])
                    pygame.draw.rect(surface, (*_NS_veshtrax.PALETTE["crystal_shine"], alpha),
                                     (fx, fy, 1, 1))



# ====================================================================
# SOLARETH (SUNBORN HERALD) - TRUE BOSS
# ====================================================================

class _NS_solareth:
    """Namespace solareth - Radiant Solar TRUE BOSS."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (bronze tanned warrior)
        "skin_darkest": (70, 40, 25),
        "skin_dark": (130, 80, 50),
        "skin_mid": (190, 140, 95),
        "skin_light": (230, 190, 145),
        "skin_shine": (250, 225, 190),
        # Hair (fiery orange-red)
        "hair_darkest": (55, 15, 5),
        "hair_dark": (120, 45, 15),
        "hair_mid": (200, 90, 25),
        "hair_light": (245, 155, 55),
        "hair_shine": (255, 220, 130),
        # Gold armor (dominant - radiant)
        "gold_darkest": (55, 30, 5),
        "gold_dark": (125, 80, 15),
        "gold_mid": (200, 155, 40),
        "gold_light": (245, 210, 85),
        "gold_hot": (255, 235, 140),
        "gold_shine": (255, 250, 200),
        "gold_white": (255, 255, 240),
        # Bright solar (skill FX main)
        "solar_darkest": (80, 40, 5),
        "solar_dark": (180, 100, 15),
        "solar_mid": (240, 165, 40),
        "solar_light": (255, 210, 90),
        "solar_hot": (255, 240, 160),
        "solar_shine": (255, 255, 220),
        "solar_white": (255, 255, 255),
        # Red cape/accent
        "red_dark": (75, 15, 15),
        "red_mid": (145, 30, 30),
        "red_light": (200, 65, 55),
        "red_glow": (240, 110, 80),
        # Sun ruby gems
        "ruby_dark": (60, 10, 10),
        "ruby_mid": (170, 30, 30),
        "ruby_light": (240, 90, 75),
        "ruby_shine": (255, 200, 170),
        # Dark plate armor accent
        "plate_dark": (35, 25, 15),
        "plate_mid": (75, 55, 30),
        "plate_light": (130, 100, 60),
        # Sword blade (bright steel with gold edge)
        "blade_darkest": (35, 30, 20),
        "blade_dark": (110, 100, 70),
        "blade_mid": (190, 175, 130),
        "blade_light": (240, 225, 180),
        "blade_shine": (255, 250, 220),
        # Eye (radiant amber-gold)
        "eye_iris": (200, 130, 30),
        "eye_glow": (255, 200, 90),
        "eye_hot": (255, 240, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_solareth._clamp(color)
        if _NS_solareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_solareth._clamp(color)
        if _NS_solareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_solareth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_solareth(surface, boss, x, y):
        """Entry point untuk TRUE BOSS Solareth."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_solareth._detect_moving(boss)
        _NS_solareth._update_sl_attack_anim(boss)
        attacking = (
            getattr(boss, "_sl_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # LARGE ambient (TRUE BOSS scale).
        _NS_solareth._draw_solar_aura(surface, x, y, pulse)
        _NS_solareth._draw_sun_rays(surface, x, y - 10, pulse)
        _NS_solareth._draw_ground_solar_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_solareth._draw_eclipse_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_solareth._draw_solarflare_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_solareth._draw_zenithblade_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_solareth._draw_sl_attack(surface, boss, x, y)
        elif moving:
            _NS_solareth._draw_sl_float(surface, boss, x, y)
        else:
            _NS_solareth._draw_sl_idle(surface, boss, x, y)
        # Eclipse shield bubble (over body).
        if active_skill == "w":
            _NS_solareth._draw_eclipse_bubble(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_solareth._draw_shieldofdaybreak_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_solareth._draw_zenithblade_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_solareth._draw_solarflare_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_sl_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sl_previous_timer", 0))
        active = bool(getattr(boss, "_sl_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._sl_attack_active = True
            boss._sl_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._sl_attack_frame = int(
                getattr(boss, "_sl_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._sl_attack_active = False
            boss._sl_attack_frame = 0
            active = False
        boss._sl_previous_timer = timer
        boss._sl_attack_progress = (
            min(1.0, getattr(boss, "_sl_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_sl_last_x"):
            boss._sl_last_x = boss.x
            boss._sl_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sl_last_x)
        dy = abs(boss.y - boss._sl_last_y)
        boss._sl_last_x = boss.x
        boss._sl_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_sl_idle(surface, boss, x, y):
        """Floating majestic idle."""
        float_bob = int(math.sin(boss.pulse * 0.5) * 4) - 6
        _NS_solareth._draw_shadow(surface, x, y + 52)
        _NS_solareth._draw_solar_trail(surface, x, y + 44, boss.pulse, floating=True)
        _NS_solareth._draw_sl_body(surface, x, y + float_bob,
                     boss.direction, boss.pulse, "idle")
    def _draw_sl_float(surface, boss, x, y):
        """Floating movement (holy warrior levitates)."""
        phase = boss.pulse * 1.6
        float_bob = int(math.sin(phase * 0.8) * 6) - 8
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_solareth._draw_shadow(surface, x + sway, y + 52, moving=True)
        _NS_solareth._draw_solar_trail(surface, x + sway, y + 44, phase,
                         floating=True, moving=True,
                         facing=boss.direction)
        _NS_solareth._draw_sl_body(surface, x + sway, y + float_bob,
                     boss.direction, phase, "float")
    def _draw_sl_attack(surface, boss, x, y):
        """Sword swing (overhead solar strike)."""
        progress = getattr(boss, "_sl_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up → swing → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3) - 6
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * boss.direction
            lift = int(3 - t * 7) - 6
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4) - 6
        _NS_solareth._draw_shadow(surface, x + lunge, y + 52)
        _NS_solareth._draw_solar_trail(surface, x + lunge, y + 44, boss.pulse,
                         floating=True, intense=True)
        _NS_solareth._draw_sl_body(surface, x + lunge, y + lift,
                     boss.direction, boss.pulse, "attack", progress)
        if 0.35 <= progress < 0.75:
            _NS_solareth._draw_sword_slash(surface, boss, x + lunge, y + lift,
                             progress)
    # ============================================================
    # BODY (Humanoid warrior: cape, dress bottom, torso, arms, head+crown)
    # ============================================================
    def _draw_sl_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Draw majestic solar warrior."""
        # Red cape behind (flowing).
        _NS_solareth._draw_cape(surface, cx, cy, facing, phase, action)
        # Armored skirt/plates bottom.
        _NS_solareth._draw_armor_skirt(surface, cx, cy + 22, facing, phase, action)
        # Torso (chestplate).
        _NS_solareth._draw_sl_torso(surface, cx, cy, facing, phase, action)
        # Shield arm (back arm holds shield).
        _NS_solareth._draw_shield_arm(surface, cx, cy + 4, facing, phase, action,
                        attack_progress)
        # Head + sun crown.
        _NS_solareth._draw_sl_head(surface, cx, cy - 22, facing, phase, action)
        # Sword arm (front - foreground).
        _NS_solareth._draw_sword_arm(surface, cx, cy + 4, facing, phase, action,
                       attack_progress)
    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Red flowing cape behind body."""
        back_dir = -facing
        sway = math.sin(phase * 0.7) * 4
        # Cape shape (long trailing).
        cape_pts = [
            (cx + back_dir * 8, cy - 14),
            (cx + back_dir * 12, cy - 10),
            (cx + back_dir * 18 + int(sway), cy - 2),
            (cx + back_dir * 22 + int(sway * 1.3), cy + 8),
            (cx + back_dir * 24 + int(sway * 1.6), cy + 18),
            (cx + back_dir * 20 + int(sway * 1.8), cy + 30),
            (cx + back_dir * 12 + int(sway * 1.5), cy + 38),
            (cx + back_dir * 2, cy + 36),
            (cx + back_dir * 6, cy + 24),
            (cx + back_dir * 10, cy + 8),
            (cx + back_dir * 8, cy - 6),
        ]
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in cape_pts])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["red_dark"], cape_pts)
        # Mid shade.
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["red_mid"], [
            (cx + back_dir * 8, cy - 12),
            (cx + back_dir * 11, cy - 8),
            (cx + back_dir * 16 + int(sway), cy - 2),
            (cx + back_dir * 20 + int(sway * 1.3), cy + 8),
            (cx + back_dir * 22 + int(sway * 1.6), cy + 18),
            (cx + back_dir * 18 + int(sway * 1.8), cy + 28),
            (cx + back_dir * 10 + int(sway * 1.5), cy + 34),
            (cx + back_dir * 4, cy + 30),
            (cx + back_dir * 8, cy + 18),
            (cx + back_dir * 10, cy),
        ])
        # Highlight (bright red).
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["red_light"], [
            (cx + back_dir * 9, cy - 8),
            (cx + back_dir * 13, cy - 2),
            (cx + back_dir * 15 + int(sway), cy + 8),
            (cx + back_dir * 14 + int(sway * 1.3), cy + 20),
            (cx + back_dir * 10 + int(sway * 1.5), cy + 28),
            (cx + back_dir * 8, cy + 24),
        ])
        # Bright edge sheen.
        pygame.draw.line(surface, _NS_solareth.PALETTE["red_glow"],
                         (cx + back_dir * 10, cy - 4),
                         (cx + back_dir * 12 + int(sway), cy + 22), 1)
        # Cape fold lines.
        for i in range(3):
            fold_x = cx + back_dir * (12 + i * 3)
            pygame.draw.line(surface, _NS_solareth.PALETTE["red_dark"],
                             (fold_x, cy - 4),
                             (fold_x + int(sway * 0.8), cy + 24), 1)
        # Gold trim edge on cape.
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_dark"],
                         (cx + back_dir * 20 + int(sway * 1.5), cy + 28),
                         (cx + back_dir * 12 + int(sway * 1.5), cy + 36), 2)
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_mid"],
                         (cx + back_dir * 19 + int(sway * 1.5), cy + 28),
                         (cx + back_dir * 12 + int(sway * 1.5), cy + 35), 1)
    def _draw_armor_skirt(surface, cx, cy, facing, phase, action):
        """Armored plate skirt bottom."""
        sway = math.sin(phase * 0.5) * 1
        # Base skirt shape (gold plates).
        skirt_pts = [
            (cx - 14, cy - 8),
            (cx + 14, cy - 8),
            (cx + 18 + int(sway), cy + 4),
            (cx + 16 + int(sway), cy + 14),
            (cx + 10, cy + 18),
            (cx - 10, cy + 18),
            (cx - 16 - int(sway), cy + 14),
            (cx - 18 - int(sway), cy + 4),
        ]
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in skirt_pts])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"], skirt_pts)
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_dark"], [
            (cx - 13, cy - 7),
            (cx + 13, cy - 7),
            (cx + 17 + int(sway), cy + 4),
            (cx + 15 + int(sway), cy + 13),
            (cx + 9, cy + 17),
            (cx - 9, cy + 17),
            (cx - 15 - int(sway), cy + 13),
            (cx - 17 - int(sway), cy + 4),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
            (cx - 11, cy - 5),
            (cx + 11, cy - 5),
            (cx + 14 + int(sway), cy + 4),
            (cx + 12 + int(sway), cy + 12),
            (cx - 12 - int(sway), cy + 12),
            (cx - 14 - int(sway), cy + 4),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_light"], [
            (cx - 9, cy - 3),
            (cx + 9, cy - 3),
            (cx + 11, cy + 4),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 11, cy + 4),
        ])
        # Plate divisions (vertical lines).
        for x_off in (-9, -3, 3, 9):
            pygame.draw.line(surface, _NS_solareth.PALETTE["gold_darkest"],
                             (cx + x_off, cy - 6),
                             (cx + x_off + int(sway * 0.5), cy + 16), 1)
        # Central belt buckle (sun emblem).
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_darkest"],
                         (cx - 5, cy - 8, 10, 6))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_dark"],
                         (cx - 4, cy - 8, 8, 5))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_mid"],
                         (cx - 3, cy - 7, 6, 4))
        # Sun emblem in center.
        _NS_solareth._draw_sun_emblem(surface, cx, cy - 5, phase, small=True)
        # Bottom trim.
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cx - 8, cy + 10), (cx + 8, cy + 10), 1)
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_hot"],
                         (cx - 7, cy + 11), (cx + 7, cy + 11), 1)
    def _draw_sun_emblem(surface, cx, cy, phase, small=False):
        """Solar sun emblem (8-point star with center)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        size = 2 if small else 4
        # Rays (8-point).
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.5
            ex = cx + int(math.cos(angle) * size)
            ey = cy + int(math.sin(angle) * size)
            alpha = _NS_solareth._alpha(240 * pulse)
            pygame.draw.line(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                             (cx, cy), (ex, ey), 1)
        # Center circle.
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_darkest"], (cx, cy), size - 1)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_mid"], (cx, cy), max(1, size - 2))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_shine"], (cx, cy, 1, 1))
    def _draw_sl_torso(surface, cx, cy, facing, phase, action):
        """Ornate gold breastplate."""
        breath = math.sin(phase * 0.7) * 1
        # Chestplate outline.
        chest_pts = [
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
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in chest_pts])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"], chest_pts)
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_dark"], [
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
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
            (cx - 10, cy - 9),
            (cx - 12, cy - 5),
            (cx - 10, cy),
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 10, cy),
            (cx + 12, cy - 5),
            (cx + 10, cy - 9),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_light"], [
            (cx - 8, cy - 7),
            (cx - 9, cy - 4),
            (cx - 7, cy - 1),
            (cx + 7, cy - 1),
            (cx + 9, cy - 4),
            (cx + 8, cy - 7),
        ])
        # Sun emblem in chest center (BIG).
        _NS_solareth._draw_sun_emblem(surface, cx, cy - 3, phase, small=False)
        # Highlight sheen on chest.
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_hot"],
                         (cx - 8, cy - 6), (cx - 7, cy - 3), 1)
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_hot"],
                         (cx + 8, cy - 6), (cx + 7, cy - 3), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cx - 7, cy - 7, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cx + 7, cy - 7, 1, 1))
        # Pauldrons (BIG sun-motif shoulders).
        for side in (-1, 1):
            sh_x = cx + side * 13
            sh_y = cy - 10
            # Base pauldron (larger).
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"], [
                (sh_x - 5, sh_y - 1),
                (sh_x + 6 * side, sh_y - 4),
                (sh_x + 7 * side, sh_y + 4),
                (sh_x - 4, sh_y + 5),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"], [
                (sh_x - 5, sh_y - 1),
                (sh_x + 6 * side, sh_y - 4),
                (sh_x + 7 * side, sh_y + 4),
                (sh_x - 4, sh_y + 5),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_dark"], [
                (sh_x - 4, sh_y - 1),
                (sh_x + 5 * side, sh_y - 3),
                (sh_x + 6 * side, sh_y + 3),
                (sh_x - 3, sh_y + 4),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
                (sh_x - 3, sh_y - 1),
                (sh_x + 4 * side, sh_y - 2),
                (sh_x + 5 * side, sh_y + 2),
                (sh_x - 2, sh_y + 3),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_light"], [
                (sh_x - 2, sh_y),
                (sh_x + 3 * side, sh_y - 1),
                (sh_x + 3 * side, sh_y + 1),
                (sh_x - 1, sh_y + 2),
            ])
            pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                             (sh_x, sh_y - 1, 1, 1))
            # Spike on top of pauldron (radiant point).
            spike_x = sh_x + 3 * side
            spike_y = sh_y - 4
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"], [
                (spike_x - 1, spike_y),
                (spike_x + 1 * side, spike_y - 5),
                (spike_x + 2 * side, spike_y),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
                (spike_x, spike_y),
                (spike_x + 1 * side, spike_y - 4),
                (spike_x + 1 * side, spike_y),
            ])
            pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                             (spike_x + 1 * side, spike_y - 3, 1, 1))
    def _draw_sl_head(surface, cx, cy, facing, phase, action):
        """Head with fiery orange hair and sunburst crown."""
        # Hair back (flowing fiery orange).
        _NS_solareth._draw_hair_back(surface, cx, cy, facing, phase)
        # Face.
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
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in face_pts])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["skin_darkest"], face_pts)
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["skin_dark"], [
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
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["skin_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy - 4),
            (cx - 3, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy - 4),
            (cx + 4, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Cheek highlight (bright bronze).
        pygame.draw.rect(surface, _NS_solareth.PALETTE["skin_light"],
                         (cx + facing * 3, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["skin_shine"],
                         (cx + facing * 3, cy - 2, 1, 1))
        # EYES (glowing amber - main).
        ex = cx + facing * 2
        ey = cy - 3
        for r in range(4, 0, -1):
            alpha = _NS_solareth._alpha(140 * (4 - r) / 4)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["eye_glow"], alpha),
                      (ex, ey), r)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["shadow_deep"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["eye_iris"], (ex, ey, 2, 2))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["eye_glow"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["eye_hot"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["white"], (ex + 1, ey, 1, 1))
        # Second eye.
        ex2 = cx - facing * 2
        pygame.draw.rect(surface, _NS_solareth.PALETTE["shadow_deep"],
                         (ex2 - 1, ey, 2, 2))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["eye_iris"], (ex2, ey, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["eye_glow"], (ex2, ey, 1, 1))
        # Eyebrows (thick, determined).
        pygame.draw.line(surface, _NS_solareth.PALETTE["hair_darkest"],
                         (cx - 5, cy - 5), (cx - 1, cy - 6), 1)
        pygame.draw.line(surface, _NS_solareth.PALETTE["hair_darkest"],
                         (cx + 1, cy - 6), (cx + 5, cy - 5), 1)
        # Lips.
        pygame.draw.line(surface, _NS_solareth.PALETTE["red_dark"],
                         (cx - 1, cy + 3), (cx + 1, cy + 3), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["red_mid"],
                         (cx, cy + 3, 1, 1))
        # Front hair strands (bangs).
        _NS_solareth._draw_hair_front(surface, cx, cy - 7, facing, phase)
        # SUN CROWN (large, sunburst).
        _NS_solareth._draw_sun_crown(surface, cx, cy - 8, facing, phase)
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long fiery orange hair flowing behind."""
        sway = math.sin(phase * 0.7) * 3
        hair_pts = [
            (cx - 7, cy - 8),
            (cx - 10, cy - 4),
            (cx - 13 - int(sway * 0.5), cy + 4),
            (cx - 14 - int(sway), cy + 14),
            (cx - 11 - int(sway * 1.5), cy + 22),
            (cx - 6 - int(sway * 1.5), cy + 24),
            (cx + 6 + int(sway * 1.5), cy + 24),
            (cx + 11 + int(sway * 1.5), cy + 22),
            (cx + 14 + int(sway), cy + 14),
            (cx + 13 + int(sway * 0.5), cy + 4),
            (cx + 10, cy - 4),
            (cx + 7, cy - 8),
        ]
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in hair_pts])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["hair_darkest"], hair_pts)
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["hair_dark"], [
            (cx - 6, cy - 7),
            (cx - 9, cy - 3),
            (cx - 12 - int(sway * 0.5), cy + 4),
            (cx - 12 - int(sway), cy + 12),
            (cx - 10 - int(sway * 1.5), cy + 20),
            (cx + 10 + int(sway * 1.5), cy + 20),
            (cx + 12 + int(sway), cy + 12),
            (cx + 12 + int(sway * 0.5), cy + 4),
            (cx + 9, cy - 3),
            (cx + 6, cy - 7),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["hair_mid"], [
            (cx - 5, cy - 5),
            (cx - 8, cy),
            (cx - 10 - int(sway * 0.5), cy + 8),
            (cx - 8 - int(sway), cy + 16),
            (cx + 8 + int(sway), cy + 16),
            (cx + 10 + int(sway * 0.5), cy + 8),
            (cx + 8, cy),
            (cx + 5, cy - 5),
        ])
        # Hair strand highlights (bright orange).
        for i, x_off in enumerate((-8, -4, 4, 8)):
            pygame.draw.line(surface, _NS_solareth.PALETTE["hair_light"],
                             (cx + x_off, cy - 4),
                             (cx + x_off + int(sway * 0.4), cy + 18), 1)
        # Golden shine strands.
        pygame.draw.line(surface, _NS_solareth.PALETTE["hair_shine"],
                         (cx - 3, cy - 6),
                         (cx - 2 + int(sway * 0.3), cy + 14), 1)
        pygame.draw.line(surface, _NS_solareth.PALETTE["hair_shine"],
                         (cx + 3, cy - 6),
                         (cx + 2 + int(sway * 0.3), cy + 14), 1)
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front bangs (partial - most is under crown)."""
        bang_pts = [
            (cx - 5, cy + 3),
            (cx - 6, cy),
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 6, cy),
            (cx + 5, cy + 3),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ]
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["hair_darkest"], bang_pts)
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["hair_dark"], [
            (cx - 4, cy + 2),
            (cx - 5, cy),
            (cx - 2, cy - 1),
            (cx + 2, cy - 1),
            (cx + 5, cy),
            (cx + 4, cy + 2),
        ])
        # Side strand.
        pygame.draw.rect(surface, _NS_solareth.PALETTE["hair_mid"],
                         (cx + facing * 4, cy + 1, 1, 3))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["hair_light"],
                         (cx + facing * 4, cy + 1, 1, 2))
    def _draw_sun_crown(surface, cx, cy, facing, phase):
        """Large sunburst crown with radiating gold rays."""
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        # Crown band (base).
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"], [
            (cx - 9, cy),
            (cx + 9, cy),
            (cx + 10, cy + 3),
            (cx - 10, cy + 3),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"], [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 9, cy + 3),
            (cx - 9, cy + 3),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_dark"], [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 8, cy + 2),
            (cx - 8, cy + 2),
        ])
        _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
            (cx - 6, cy),
            (cx + 6, cy),
            (cx + 7, cy + 2),
            (cx - 7, cy + 2),
        ])
        pygame.draw.line(surface, _NS_solareth.PALETTE["gold_light"],
                         (cx - 5, cy), (cx + 5, cy), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cx - 2, cy, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cx + 2, cy, 1, 1))
        # SUNBURST RAYS (radiating up).
        for i in range(9):
            angle_deg = 90 - (i - 4) * 22  # from -50° to 130°
            angle = math.radians(angle_deg)
            ray_len = 8 + int(math.cos((i - 4) * 0.5) * 3)  # tallest in center
            base_x = cx + int(math.cos(angle) * 2)
            base_y = cy - int(math.sin(angle) * 2)
            tip_x = cx + int(math.cos(angle) * ray_len)
            tip_y = cy - int(math.sin(angle) * ray_len)
            perp = angle + math.pi / 2
            base_a_x = base_x + int(math.cos(perp) * 1.5)
            base_a_y = base_y - int(math.sin(perp) * 1.5)
            base_b_x = base_x - int(math.cos(perp) * 1.5)
            base_b_y = base_y + int(math.sin(perp) * 1.5)
            # Shadow.
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_a_x + 1, base_a_y + 1),
                (base_b_x + 1, base_b_y + 1),
            ])
            # Base ray.
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"],
                  [(tip_x, tip_y), (base_a_x, base_a_y), (base_b_x, base_b_y)])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_dark"], [
                (tip_x, tip_y),
                (int((tip_x + base_a_x) / 2), int((tip_y + base_a_y) / 2)),
                (base_x, base_y),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            # Bright tip.
            pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                             (tip_x, tip_y, 1, 1))
        # Center ruby gem (large).
        gem_alpha = _NS_solareth._alpha(200 + 55 * pulse)
        for r in range(5, 0, -1):
            alpha = _NS_solareth._alpha(gem_alpha * (5 - r) / 5)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["ruby_mid"], alpha),
                      (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_dark"],
                         (cx - 2, cy, 4, 3))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_mid"],
                         (cx - 1, cy, 3, 3))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_light"],
                         (cx, cy, 2, 2))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_shine"],
                         (cx, cy, 1, 1))
    def _draw_shield_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm holds LARGE sun shield."""
        back_dir = -facing
        # Shoulder.
        shoulder_x = cx + back_dir * 12
        shoulder_y = cy - 8
        # Arm bends forward holding shield up.
        sway = math.sin(phase * 0.6) * 1
        elbow_x = shoulder_x + back_dir * 2 + int(sway)
        elbow_y = shoulder_y + 6
        hand_x = elbow_x + back_dir * 1 + int(sway)
        hand_y = elbow_y + 8
        # Upper arm (gold armor).
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 6)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_mid"],
                (shoulder_x + back_dir, shoulder_y),
                (elbow_x + back_dir, elbow_y), 2)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_light"],
                         (shoulder_x + back_dir * 2, shoulder_y - 1, 1, 1))
        # Forearm.
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1),
                (hand_x + 1, hand_y + 1), 5)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Elbow armor (spiked).
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_darkest"], (elbow_x, elbow_y), 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_dark"], (elbow_x, elbow_y), 3)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_mid"], (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_light"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # LARGE SUN SHIELD.
        _NS_solareth._draw_sun_shield(surface, hand_x + back_dir * 6, hand_y - 2,
                        facing, phase)
    def _draw_sun_shield(surface, cx, cy, facing, phase):
        """Large circular sun shield."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        shield_r = 18
        # Shadow.
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["shadow_deep"],
                  (cx + 2, cy + 2), shield_r + 1)
        # Outer rim (dark gold).
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_darkest"], (cx, cy), shield_r + 1)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_dark"], (cx, cy), shield_r)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_mid"], (cx, cy), shield_r - 2)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_darkest"], (cx, cy), shield_r - 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_dark"], (cx, cy), shield_r - 5)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_mid"], (cx, cy), shield_r - 7)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_light"], (cx, cy), shield_r - 9)
        # Center ruby gem.
        for r in range(6, 0, -1):
            alpha = _NS_solareth._alpha(180 * (6 - r) / 6 * pulse)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["ruby_light"], alpha),
                      (cx, cy), r + 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["ruby_dark"], (cx, cy), 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["ruby_mid"], (cx, cy), 3)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["ruby_light"], (cx, cy), 2)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["ruby_shine"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["white"], (cx, cy, 1, 1))
        # Sunburst rays on shield (radiating from center).
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.3
            inner_r = 5
            outer_r = shield_r - 2
            ix = cx + int(math.cos(angle) * inner_r)
            iy = cy + int(math.sin(angle) * inner_r)
            ox = cx + int(math.cos(angle) * outer_r)
            oy = cy + int(math.sin(angle) * outer_r)
            alpha = _NS_solareth._alpha(200 * pulse)
            pygame.draw.line(surface, (*_NS_solareth.PALETTE["gold_hot"], alpha),
                             (ix, iy), (ox, oy), 1)
        # Outer spikes (protruding).
        for i in range(8):
            angle = i * math.pi / 4 + math.pi / 8
            spike_base_r = shield_r
            spike_tip_r = shield_r + 4
            base_x = cx + int(math.cos(angle) * spike_base_r)
            base_y = cy + int(math.sin(angle) * spike_base_r)
            tip_x = cx + int(math.cos(angle) * spike_tip_r)
            tip_y = cy + int(math.sin(angle) * spike_tip_r)
            perp = angle + math.pi / 2
            perp_a_x = base_x + int(math.cos(perp) * 2)
            perp_a_y = base_y + int(math.sin(perp) * 2)
            perp_b_x = base_x - int(math.cos(perp) * 2)
            perp_b_y = base_y - int(math.sin(perp) * 2)
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_darkest"], [
                (tip_x, tip_y), (perp_a_x, perp_a_y), (perp_b_x, perp_b_y),
            ])
            _NS_solareth._poly(surface, _NS_solareth.PALETTE["gold_mid"], [
                (tip_x, tip_y),
                (int((tip_x + perp_a_x) / 2), int((tip_y + perp_a_y) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_hot"],
                             (tip_x, tip_y, 1, 1))
        # Outer highlight arc.
        for arc_r in range(shield_r - 1, shield_r):
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_shine"],
                      (cx, cy), arc_r, 1)
    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding long sword - overhead strike."""
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 8
        # Angle convention: 0 = forward, pi/2 = UP.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise sword up-back.
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.55 + t * 0.35)
                sword_extra = math.pi * 0.3
            elif attack_progress < 0.6:
                # SWING DOWN.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (0.9 - t * 1.1)
                sword_extra = math.pi * (0.3 - t * 0.6)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.2 + t * 0.35)
                sword_extra = math.pi * (-0.3 + t * 0.4)
        elif action == "float":
            arm_angle = math.pi * 0.12 + math.sin(phase) * 0.05
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
        # Upper arm (gold armor).
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                (shoulder_x + 1, shoulder_y + 1),
                (elbow_x + 1, elbow_y + 1), 7)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_darkest"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_dark"],
                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_mid"],
                (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 3)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_light"],
                (shoulder_x, shoulder_y - 2), (elbow_x, elbow_y - 2), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (shoulder_x + facing * 2, shoulder_y - 2, 1, 1))
        # Forearm.
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 6)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_darkest"],
                (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_dark"],
                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_mid"],
                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Elbow armor.
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_darkest"], (elbow_x, elbow_y), 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_dark"], (elbow_x, elbow_y), 3)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_mid"], (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (elbow_x - 1, elbow_y - 1, 1, 1))
        # Gauntlet.
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_darkest"], (hand_x, hand_y), 5)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_dark"], (hand_x, hand_y), 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_mid"], (hand_x, hand_y), 3)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_light"], (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (hand_x - 1, hand_y - 1, 1, 1))
        # Ruby on gauntlet.
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_mid"],
                         (hand_x, hand_y, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_light"],
                         (hand_x, hand_y, 1, 1))
        # LONG SWORD.
        sword_angle = hand_angle + sword_extra
        _NS_solareth._draw_solar_sword(surface, hand_x, hand_y, sword_angle,
                         facing, phase)
    def _draw_solar_sword(surface, hx, hy, angle, facing, phase):
        """Long broadsword with gold hilt."""
        # Handle (opposite direction).
        handle_len = 8
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy + int(math.sin(angle) * handle_len)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["plate_dark"],
                (hx, hy), (handle_end_x, handle_end_y), 3)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["plate_mid"],
                (hx, hy), (handle_end_x, handle_end_y), 2)
        # Gold wraps on handle.
        for i in range(3):
            t = (i + 1) / 4
            wx = int(hx + (handle_end_x - hx) * t)
            wy = int(hy + (handle_end_y - hy) * t)
            pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_mid"], (wx, wy, 1, 1))
        # Pommel (ruby ball).
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["shadow_deep"],
                  (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_darkest"],
                  (handle_end_x, handle_end_y), 4)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_dark"],
                  (handle_end_x, handle_end_y), 3)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["ruby_mid"],
                  (handle_end_x, handle_end_y), 2)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["ruby_light"],
                  (handle_end_x, handle_end_y), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["ruby_shine"],
                         (handle_end_x, handle_end_y - 1, 1, 1))
        # Crossguard (elaborate).
        perp = angle + math.pi / 2
        cg_a_x = hx + int(math.cos(perp) * 5) * facing
        cg_a_y = hy - int(math.sin(perp) * 5)
        cg_b_x = hx - int(math.cos(perp) * 5) * facing
        cg_b_y = hy + int(math.sin(perp) * 5)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                (cg_a_x + 1, cg_a_y + 1), (cg_b_x + 1, cg_b_y + 1), 4)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_darkest"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 3)
        _NS_solareth._aaline(surface, _NS_solareth.PALETTE["gold_dark"],
                (cg_a_x, cg_a_y), (cg_b_x, cg_b_y), 2)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_light"], (cg_a_x, cg_a_y), 2)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["gold_light"], (cg_b_x, cg_b_y), 2)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cg_a_x, cg_a_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_shine"],
                         (cg_b_x, cg_b_y - 1, 1, 1))
        # STRAIGHT LONG BLADE.
        blade_len = 34
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy - int(math.sin(angle) * blade_len)
        # Segmented blade for shading.
        segments = 12
        prev = (hx, hy)
        for i in range(1, segments + 1):
            t = i / segments
            bx = int(hx + (tip_x - hx) * t)
            by = int(hy + (tip_y - hy) * t)
            thickness = max(1, 5 - int(t * 3))
            _NS_solareth._aaline(surface, _NS_solareth.PALETTE["shadow_deep"],
                    (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1),
                    thickness + 1)
            _NS_solareth._aaline(surface, _NS_solareth.PALETTE["blade_darkest"],
                    prev, (bx, by), thickness)
            _NS_solareth._aaline(surface, _NS_solareth.PALETTE["blade_dark"],
                    prev, (bx, by), max(1, thickness - 1))
            _NS_solareth._aaline(surface, _NS_solareth.PALETTE["blade_mid"],
                    prev, (bx, by), max(1, thickness - 2))
            _NS_solareth._aaline(surface, _NS_solareth.PALETTE["blade_light"],
                    (prev[0], prev[1] - 1), (bx, by - 1), 1)
            # Golden fuller (blood groove down center) - solar glow.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_mid"],
                                 (bx, by, 1, 1))
                pygame.draw.rect(surface, _NS_solareth.PALETTE["gold_hot"],
                                 (bx, by, 1, 1))
            prev = (bx, by)
        # Tip.
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["blade_darkest"], (tip_x, tip_y), 2)
        _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["blade_mid"], (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_solareth.PALETTE["blade_shine"], (tip_x, tip_y, 1, 1))
        # Solar glow around blade (energy).
        glow_mid_x = int(hx + (tip_x - hx) * 0.5)
        glow_mid_y = int(hy + (tip_y - hy) * 0.5)
        for r in range(6, 1, -1):
            alpha = _NS_solareth._alpha(60 * (6 - r) / 6)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                      (glow_mid_x, glow_mid_y), r)
    def _draw_sword_slash(surface, boss, cx, cy, progress):
        """Solar arc slash during sword swing."""
        facing = boss.direction
        swing_t = max(0.0, min(1.0, (progress - 0.35) / 0.4))
        arc_center_x = cx + facing * 6
        arc_center_y = cy - 4
        radius = 32
        # Slash sweeps overhead.
        num_slices = 12
        for slice_i in range(num_slices):
            slice_t = slice_i / num_slices
            sweep_angle_start = math.pi * 0.75
            sweep_angle_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.12)
            angle = sweep_angle_start + (sweep_angle_end - sweep_angle_start) * local_swing
            fade = 1 - slice_t * 0.75
            alpha = _NS_solareth._alpha(240 * fade
                            * (1 - abs(swing_t - 0.5) * 1.4))
            if alpha <= 0:
                continue
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            size = max(2, int(7 * fade))
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_darkest"], alpha),
                      (arc_x, arc_y), size + 1)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                      (arc_x, arc_y), size)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                      (arc_x, arc_y), max(1, size - 1))
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_light"], alpha),
                      (arc_x, arc_y), max(1, size - 2))
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                      (arc_x, arc_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                             (arc_x, arc_y, 1, 1))
        # Bright crescent arc line.
        crescent_pts = []
        for slice_i in range(num_slices + 1):
            slice_t = slice_i / num_slices
            sweep_angle_start = math.pi * 0.75
            sweep_angle_end = -math.pi * 0.15
            local_swing = max(0.0, swing_t - slice_t * 0.08)
            angle = sweep_angle_start + (sweep_angle_end - sweep_angle_start) * local_swing
            arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
            arc_y = arc_center_y - int(math.sin(angle) * radius)
            crescent_pts.append((arc_x, arc_y))
        if len(crescent_pts) > 1:
            for i in range(len(crescent_pts) - 1):
                alpha = _NS_solareth._alpha(230 * (1 - abs(swing_t - 0.5) * 1.4))
                _NS_solareth._aaline(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 2)
                _NS_solareth._aaline(surface, (*_NS_solareth.PALETTE["solar_white"], alpha),
                        crescent_pts[i], crescent_pts[i + 1], 1)
    # ============================================================
    # SOLAR TRAIL (floating particles)
    # ============================================================
    def _draw_solar_trail(surface, cx, cy, phase, floating=False,
                            moving=False, intense=False, facing=1):
        """Bright gold particles rising below boss."""
        strength = 1.5 if intense else 1.0
        strength *= 1.2 if moving else 1.0
        # Gold mist cloud.
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.3) * 0.3 + 0.7
        for radius in range(32, 3, -2):
            alpha = _NS_solareth._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_solareth._alpha((20 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising gold embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_solareth._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                      (sx, sy), 3)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                      (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Bright sparkles.
        for i in range(12):
            spark_t = (phase * 0.7 + i * 0.09) % 1.0
            ex = cx - 28 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_solareth._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                                 (ex, ey, 1, 1))
        # Movement trail.
        if moving:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_solareth._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                          (sx, sy), max(2, 7 - i))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                          (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT (TRUE BOSS scale)
    # ============================================================
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 3, 2, 170), (5, 9, 140, 14))
        pygame.draw.ellipse(shadow, (60, 40, 10, 110), (12, 11, 126, 10))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_solar_aura(surface, x, y, phase):
        """BIG radiant solar aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_solareth._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_solareth._aacircle(aura, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                          (120, 100), radius)
        for radius in range(70, 5, -3):
            alpha = _NS_solareth._alpha((70 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_solareth._aacircle(aura, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                          (120, 100), radius)
        for radius in range(40, 5, -2):
            alpha = _NS_solareth._alpha((40 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_solareth._aacircle(aura, (*_NS_solareth.PALETTE["solar_light"], alpha),
                          (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Radial sun rays outward.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            inner_r = 55
            outer_r = 80 + int(math.sin(phase + i) * 8)
            ix = x + int(math.cos(angle) * inner_r)
            iy = y - 5 + int(math.sin(angle) * inner_r * 0.5)
            ox = x + int(math.cos(angle) * outer_r)
            oy = y - 5 + int(math.sin(angle) * outer_r * 0.5)
            alpha = _NS_solareth._alpha(150 * pulse)
            pygame.draw.line(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                             (ix, iy), (ox, oy), 2)
            pygame.draw.line(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                             (ix, iy), (ox, oy), 1)
    def _draw_sun_rays(surface, x, y, phase):
        """Rotating radial rays behind boss."""
        for i in range(16):
            angle = phase * 0.15 + i * math.pi / 8
            length = 90 + int(math.sin(phase + i) * 10)
            ex = x + int(math.cos(angle) * length)
            ey = y + int(math.sin(angle) * length * 0.6)
            alpha = _NS_solareth._alpha(80)
            pygame.draw.line(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                             (x, y), (ex, ey), 1)
    def _draw_ground_solar_ring(surface, x, y, phase, skill):
        """Large ground ring with solar runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_solareth.PALETTE["solar_dark"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_solareth.PALETTE["solar_darkest"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_solareth.PALETTE["solar_mid"], 200),
                            (25, 25, 140, 20), 1)
        pygame.draw.ellipse(ring, (*_NS_solareth.PALETTE["gold_dark"], 180),
                            (40, 27, 110, 16), 1)
        # Runes.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 33 + int(math.sin(angle) * 10)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 33 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_solareth.PALETTE["solar_light"], 220),
                             (x1, y1), (x2, y2), 1)
            # Star at outer tip.
            pygame.draw.rect(ring, (*_NS_solareth.PALETTE["solar_shine"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_solareth.PALETTE["solar_hot"],
                                        _NS_solareth._alpha(180 * pulse)),
                                (15, 12, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))
    # ============================================================
    # SKILL: Q - SHIELD OF DAYBREAK (sword swing + slow/stun)
    # ============================================================
    def _draw_shieldofdaybreak_skill(surface, boss, x, y, timer, phase):
        """Empowered sword swing arc with solar shockwave."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_solareth._target_position(boss, x, y)
        if progress < 0.3:
            # Wind-up: sword glows brighter.
            t = progress / 0.3
            charge_x = x + facing * 20
            charge_y = y - 20
            cr = int(6 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_solareth._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                          (charge_x, charge_y), r)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_mid"],
                      (charge_x, charge_y), cr - 3)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_light"],
                      (charge_x, charge_y), max(1, cr - 6))
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_shine"],
                      (charge_x, charge_y), max(1, cr - 9))
        else:
            t = (progress - 0.3) / 0.7
            # Massive solar crescent arc forward.
            arc_center_x = x + facing * 12
            arc_center_y = y - 10
            radius = int(50 + t * 30)
            # Sweeping arc (like Q image).
            num_slices = 20
            for slice_i in range(num_slices):
                slice_t = slice_i / num_slices
                sweep_start = math.pi * 0.9
                sweep_end = -math.pi * 0.2
                local_t = max(0.0, min(1.0, t * 1.3 - slice_t * 0.15))
                angle = sweep_start + (sweep_end - sweep_start) * local_t
                fade = 1 - slice_t * 0.7
                alpha = _NS_solareth._alpha(230 * fade * (1 - t * 0.3))
                if alpha <= 0:
                    continue
                arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
                arc_y = arc_center_y - int(math.sin(angle) * radius)
                size = max(3, int(9 * fade))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_darkest"], alpha),
                          (arc_x, arc_y), size + 2)
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                          (arc_x, arc_y), size + 1)
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                          (arc_x, arc_y), size)
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_light"], alpha),
                          (arc_x, arc_y), max(1, size - 1))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                          (arc_x, arc_y), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                                 (arc_x, arc_y, 1, 1))
            # Bright leading crescent line.
            crescent_pts = []
            for slice_i in range(num_slices + 1):
                slice_t = slice_i / num_slices
                sweep_start = math.pi * 0.9
                sweep_end = -math.pi * 0.2
                local_t = max(0.0, min(1.0, t * 1.3 - slice_t * 0.08))
                angle = sweep_start + (sweep_end - sweep_start) * local_t
                arc_x = arc_center_x + int(math.cos(angle) * radius) * facing
                arc_y = arc_center_y - int(math.sin(angle) * radius)
                crescent_pts.append((arc_x, arc_y))
            if len(crescent_pts) > 1:
                for i in range(len(crescent_pts) - 1):
                    alpha = _NS_solareth._alpha(240 * (1 - t * 0.3))
                    _NS_solareth._aaline(surface, (*_NS_solareth.PALETTE["solar_white"], alpha),
                            crescent_pts[i], crescent_pts[i + 1], 2)
            # Impact stars at end.
            if t > 0.7:
                st = (t - 0.7) / 0.3
                for i in range(6):
                    angle_s = i * math.pi / 3
                    ix = tx + int(math.cos(angle_s) * 15)
                    iy = ty + int(math.sin(angle_s) * 10)
                    alpha = _NS_solareth._alpha(240 * (1 - st))
                    _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                              (ix, iy), 4)
                    pygame.draw.rect(surface,
                                     (*_NS_solareth.PALETTE["solar_shine"], alpha),
                                     (ix, iy, 2, 2))
    # ============================================================
    # SKILL: W - ECLIPSE (defensive shield bubble)
    # ============================================================
    def _draw_eclipse_ground(surface, boss, x, y, timer, phase):
        """Solar rings under boss for eclipse."""
        for i in range(3):
            r = int(38 + i * 10 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_solareth._alpha(200 - i * 50)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                      (x, y + 42), r, 2)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_light"], alpha),
                      (x, y + 42), r, 1)
    def _draw_eclipse_bubble(surface, boss, x, y, timer, phase):
        """Eclipse-style shield bubble (dark ring w/ solar corona)."""
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)
        bubble = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)
        # DARK CORE (eclipse effect - like moon).
        for inner_r in range(r - 8, 0, -3):
            alpha = _NS_solareth._alpha(80 * (r - inner_r) / r)
            _NS_solareth._aacircle(bubble, (*_NS_solareth.PALETTE["shadow_deep"], alpha),
                      center, inner_r)
        # Bright corona ring.
        for thickness in range(4, 0, -1):
            alpha_val = 220 - (4 - thickness) * 40
            _NS_solareth._aacircle(bubble, (*_NS_solareth.PALETTE["solar_dark"], alpha_val),
                      center, r, thickness + 2)
            _NS_solareth._aacircle(bubble, (*_NS_solareth.PALETTE["solar_mid"], alpha_val),
                      center, r - 1, thickness + 1)
            _NS_solareth._aacircle(bubble, (*_NS_solareth.PALETTE["solar_hot"], alpha_val),
                      center, r - 2, thickness)
        _NS_solareth._aacircle(bubble, _NS_solareth.PALETTE["solar_shine"], center, r, 1)
        _NS_solareth._aacircle(bubble, _NS_solareth.PALETTE["solar_white"], center, r + 1, 1)
        # Rotating solar flares along edge.
        for i in range(16):
            angle = phase * 1.2 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_solareth.PALETTE["solar_hot"], (sx, sy, 3, 3))
            pygame.draw.rect(bubble, _NS_solareth.PALETTE["solar_shine"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_solareth.PALETTE["white"], (sx, sy, 1, 1))
        # Corona flares reaching outward.
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            inner_x = center[0] + int(math.cos(angle) * (r + 2))
            inner_y = center[1] + int(math.sin(angle) * (r + 2))
            outer_x = center[0] + int(math.cos(angle) * (r + 10))
            outer_y = center[1] + int(math.sin(angle) * (r + 10))
            alpha = _NS_solareth._alpha(200 + math.sin(phase * 3 + i) * 55)
            pygame.draw.line(bubble, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 2)
            pygame.draw.line(bubble, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 1)
        surface.blit(bubble, (x - r - 15, y - r - 15))
    # ============================================================
    # SKILL: E - ZENITH BLADE (dash beam forward)
    # ============================================================
    def _draw_zenithblade_ground(surface, boss, x, y, timer, phase):
        """Wide streak on ground during dash."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return
        t = (progress - 0.3) / 0.7
        length = int(t * 180)
        # Ground streak.
        if length > 5:
            for i in range(3):
                h = 8 - i * 2
                if facing > 0:
                    pygame.draw.ellipse(surface,
                                        (*_NS_solareth.PALETTE["solar_mid"],
                                         180 - i * 50),
                                        (x, y + 30 - h, length, h * 2))
                else:
                    pygame.draw.ellipse(surface,
                                        (*_NS_solareth.PALETTE["solar_mid"],
                                         180 - i * 50),
                                        (x - length, y + 30 - h, length, h * 2))
    def _draw_zenithblade_foreground(surface, boss, x, y, timer, phase):
        """Solar beam energy shooting forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_solareth._target_position(boss, x, y)
        if progress < 0.3:
            # Wind-up: sword low, gathering energy.
            t = progress / 0.3
            gather_x = x + facing * 15
            gather_y = y + 4
            gather_r = int(6 + t * 12)
            for r in range(gather_r + 5, 0, -1):
                alpha = _NS_solareth._alpha(200 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                          (gather_x, gather_y), r)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_mid"],
                      (gather_x, gather_y), gather_r - 3)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_light"],
                      (gather_x, gather_y), max(1, gather_r - 6))
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_shine"],
                      (gather_x, gather_y), max(1, gather_r - 9))
        else:
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 20
            start_y = y - 4
            # Full beam.
            beam_end_x = int(start_x + (tx - start_x) * min(1.0, t * 1.3))
            beam_end_y = int(start_y + (ty - start_y) * min(1.0, t * 1.3))
            # Layered beam.
            for width, color, alpha_val in [
                (10, _NS_solareth.PALETTE["solar_darkest"], 180),
                (7, _NS_solareth.PALETTE["solar_dark"], 220),
                (5, _NS_solareth.PALETTE["solar_mid"], 240),
                (3, _NS_solareth.PALETTE["solar_light"], 250),
                (2, _NS_solareth.PALETTE["solar_hot"], 255),
                (1, _NS_solareth.PALETTE["solar_shine"], 255),
            ]:
                pygame.draw.line(surface, (*color, alpha_val),
                                 (start_x, start_y),
                                 (beam_end_x, beam_end_y), width)
            # Head impact.
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_darkest"],
                      (beam_end_x, beam_end_y), 12)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_dark"],
                      (beam_end_x, beam_end_y), 9)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_mid"],
                      (beam_end_x, beam_end_y), 6)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_light"],
                      (beam_end_x, beam_end_y), 4)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_hot"],
                      (beam_end_x, beam_end_y), 2)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_shine"],
                      (beam_end_x, beam_end_y), 1)
            pygame.draw.rect(surface, _NS_solareth.PALETTE["white"],
                             (beam_end_x, beam_end_y, 1, 1))
            # Radial burst at head.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = beam_end_x + int(math.cos(angle_s) * 14)
                ey = beam_end_y + int(math.sin(angle_s) * 14)
                pygame.draw.line(surface, _NS_solareth.PALETTE["solar_hot"],
                                 (beam_end_x, beam_end_y), (ex, ey), 2)
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_shine"],
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
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_hot"], (spx, spy, 2, 2))
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_shine"], (spx, spy, 1, 1))
    # ============================================================
    # SKILL: R - SOLAR FLARE (massive AoE explosion)
    # ============================================================
    def _draw_solarflare_ground(surface, boss, x, y, timer, phase):
        """Growing solar disk under boss."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 2))
        if r > 5:
            # Expanding gold disk.
            for i in range(4):
                thickness = 4 - i
                pygame.draw.ellipse(surface,
                                    (*_NS_solareth.PALETTE["solar_dark"], 200 - i * 40),
                                    (x - r, y + 45 - r // 3,
                                     r * 2, r * 2 // 3), thickness)
                pygame.draw.ellipse(surface,
                                    (*_NS_solareth.PALETTE["solar_mid"], 200 - i * 40),
                                    (x - r + 3, y + 45 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), max(1, thickness - 1))
    def _draw_solarflare_foreground(surface, boss, x, y, timer, phase):
        """Massive solar explosion emanating from boss."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Wind-up: energy gathering at boss.
            t = progress / 0.25
            gather_r = int(10 + t * 25)
            for r in range(gather_r + 8, 0, -2):
                alpha = _NS_solareth._alpha(200 * (gather_r + 8 - r) / (gather_r + 8))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                          (x, y - 5), r)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_mid"],
                      (x, y - 5), gather_r - 5)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_light"],
                      (x, y - 5), max(1, gather_r - 10))
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_shine"],
                      (x, y - 5), max(1, gather_r - 15))
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_white"],
                      (x, y - 5), max(1, gather_r - 20))
            # Gathering swirls.
            for i in range(16):
                angle = phase * 4 + i * math.pi / 8
                spiral_r = int(60 - t * 40)
                sx = x + int(math.cos(angle) * spiral_r)
                sy = y - 5 + int(math.sin(angle) * spiral_r * 0.6)
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_shine"], (sx, sy, 1, 1))
        elif progress < 0.75:
            # EXPLOSION expanding.
            t = (progress - 0.25) / 0.5
            explosion_r = int(30 + t * 100)
            # Multi-layer shockwave.
            alpha = _NS_solareth._alpha(240 * (1 - t * 0.5))
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_darkest"], alpha),
                      (x, y - 5), explosion_r + 4, 4)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_dark"], alpha),
                      (x, y - 5), explosion_r, 4)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                      (x, y - 5), max(1, explosion_r - 6), 3)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_light"], alpha),
                      (x, y - 5), max(1, explosion_r - 12), 2)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                      (x, y - 5), max(1, explosion_r - 18), 2)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha),
                      (x, y - 5), max(1, explosion_r - 24), 1)
            # Inner bright core.
            core_r = max(5, int(30 - t * 20))
            for r in range(core_r + 5, 0, -1):
                core_alpha = _NS_solareth._alpha(200 * (core_r + 5 - r) / (core_r + 5) * (1 - t * 0.3))
                _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], core_alpha),
                          (x, y - 5), r)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_shine"], (x, y - 5), core_r // 2)
            _NS_solareth._aacircle(surface, _NS_solareth.PALETTE["solar_white"], (x, y - 5), max(1, core_r // 4))
            pygame.draw.rect(surface, _NS_solareth.PALETTE["white"], (x, y - 5, 1, 1))
            # Radial SUN RAYS shooting outward.
            for i in range(24):
                angle = i * math.pi / 12 + phase * 0.2
                inner_r = 5
                outer_r = explosion_r + 8
                ix = x + int(math.cos(angle) * inner_r)
                iy = y - 5 + int(math.sin(angle) * inner_r)
                ox = x + int(math.cos(angle) * outer_r)
                oy = y - 5 + int(math.sin(angle) * outer_r * 0.7)
                alpha_r = _NS_solareth._alpha(230 * (1 - t * 0.4))
                pygame.draw.line(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha_r),
                                 (ix, iy), (ox, oy), 2)
                pygame.draw.line(surface, (*_NS_solareth.PALETTE["solar_shine"], alpha_r),
                                 (ix, iy), (ox, oy), 1)
                pygame.draw.rect(surface, (*_NS_solareth.PALETTE["solar_white"], alpha_r),
                                 (ox, oy, 2, 2))
            # Floating solar embers.
            for i in range(20):
                ember_angle = phase * 2 + i * math.pi / 10
                ember_r = int(explosion_r * (0.5 + math.sin(phase * 3 + i) * 0.3))
                ex = x + int(math.cos(ember_angle) * ember_r)
                ey = y - 5 + int(math.sin(ember_angle) * ember_r * 0.7)
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_hot"], (ex, ey, 2, 2))
                pygame.draw.rect(surface, _NS_solareth.PALETTE["solar_shine"], (ex, ey, 1, 1))
        else:
            # Aftermath: lingering solar glow fading.
            t = (progress - 0.75) / 0.25
            fade_r = int(130 * (1 - t * 0.3))
            alpha = _NS_solareth._alpha(180 * (1 - t))
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_mid"], alpha),
                      (x, y - 5), fade_r, 3)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_light"], alpha),
                      (x, y - 5), max(1, fade_r - 8), 2)
            _NS_solareth._aacircle(surface, (*_NS_solareth.PALETTE["solar_hot"], alpha),
                      (x, y - 5), max(1, fade_r - 16), 1)
            # Rising embers.
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.08) % 1.0
                rx = x + int(math.sin(phase + i) * 40)
                ry = y - int(rise_t * 60)
                em_alpha = _NS_solareth._alpha(200 * (1 - t) * (1 - rise_t))
                if em_alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_solareth.PALETTE["solar_hot"], em_alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_solareth.PALETTE["solar_shine"], em_alpha),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_khalzaredh(surface, boss, x, y):
    """Entry point khalzaredh."""
    return _NS_khalzaredh.draw_khalzaredh(surface, boss, x, y)


def draw_nyxaroth(surface, boss, x, y):
    """Entry point nyxaroth."""
    return _NS_nyxaroth.draw_nyxaroth(surface, boss, x, y)


def draw_veshtrax(surface, boss, x, y):
    """Entry point veshtrax."""
    return _NS_veshtrax.draw_veshtrax(surface, boss, x, y)


def draw_solareth(surface, boss, x, y):
    """Entry point solareth."""
    return _NS_solareth.draw_solareth(surface, boss, x, y)
