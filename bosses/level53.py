"""
bosses/level53.py - Semua boss Level 53

Berisi:
  - dorakai   (mini boss - RANGED blood-drum oni, area demon)
  - hitokage  (mini boss - MELEE sunfire blade master, sun breathing)
  - kazuren   (mini boss - MELEE shadow of the void, masked ninja)
  - tsukiyora (TRUE BOSS - RANGED moon-born sovereign, goddess)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================================================
# DORAKAI - MINI BOSS
# ====================================================================================================

class _NS_dorakai:
    """Namespace dorakai - Blood-drum demon mini boss (AREA/RANGED)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Grey demon skin (dead flesh)
        "skin_darkest": (35, 30, 40),
        "skin_dark": (75, 70, 85),
        "skin_mid": (130, 120, 135),
        "skin_light": (180, 170, 180),
        "skin_shine": (215, 205, 215),

        # Dark spiky demon hair (black-blue)
        "hair_darkest": (10, 8, 18),
        "hair_dark": (25, 22, 40),
        "hair_mid": (55, 50, 75),
        "hair_light": (95, 90, 115),

        # Pink-red demon eyes (glowing)
        "eye_darkest": (60, 5, 25),
        "eye_dark": (140, 20, 55),
        "eye_mid": (230, 60, 110),
        "eye_light": (255, 130, 170),
        "eye_glow": (255, 200, 220),

        # Red demon face markings
        "mark_dark": (100, 15, 20),
        "mark_mid": (200, 35, 40),
        "mark_light": (255, 90, 70),

        # Purple sash / hakama
        "cloth_darkest": (25, 10, 40),
        "cloth_dark": (55, 25, 75),
        "cloth_mid": (95, 55, 125),
        "cloth_light": (150, 100, 180),

        # Red sash/belt
        "sash_dark": (85, 20, 25),
        "sash_mid": (155, 40, 45),
        "sash_light": (215, 80, 75),
        "sash_shine": (250, 130, 120),

        # Drum wood (dark brown)
        "drum_darkest": (25, 15, 8),
        "drum_dark": (65, 40, 20),
        "drum_mid": (120, 80, 45),
        "drum_light": (180, 130, 80),
        "drum_shine": (225, 175, 120),

        # Drum skin (tan leather)
        "skin_drum_dark": (135, 90, 50),
        "skin_drum_mid": (200, 155, 100),
        "skin_drum_light": (245, 210, 155),

        # Kanji red (drum face symbols)
        "kanji_dark": (85, 15, 15),
        "kanji_mid": (170, 30, 30),
        "kanji_light": (240, 70, 60),

        # Chain (rope binding drums)
        "chain_dark": (35, 30, 20),
        "chain_mid": (95, 80, 55),
        "chain_light": (155, 135, 95),

        # Blood sound wave (main skill - red/pink energy)
        "sound_darkest": (55, 5, 15),
        "sound_dark": (135, 20, 45),
        "sound_mid": (220, 45, 85),
        "sound_light": (255, 100, 140),
        "sound_hot": (255, 175, 195),
        "sound_shine": (255, 235, 240),

        # Deep dark red for shadow
        "blood_dark": (60, 10, 15),
        "blood_mid": (120, 20, 30),
        "blood_light": (200, 40, 50),

        # Music note black
        "note_dark": (20, 5, 15),
        "note_mid": (60, 20, 40),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_dorakai._clamp(color)
        if _NS_dorakai.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_dorakai._clamp(color)
        if _NS_dorakai.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_dorakai._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_dorakai(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_dorakai._detect_moving(boss)
        _NS_dorakai._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_dr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient
        _NS_dorakai._draw_shadow(surface, x, y + 46)
        _NS_dorakai._draw_sound_aura(surface, x, y, pulse, active_skill)
        _NS_dorakai._draw_ground_ring(surface, x, y + 42, pulse, active_skill)

        # Skill ground FX
        if active_skill == "w":
            _NS_dorakai._draw_echo_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_dorakai._draw_dissonant_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_dorakai._draw_binding_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_dorakai._draw_final_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_dorakai._draw_dr_attack(surface, boss, x, y)
        elif active_skill in ("q", "w", "e", "r", "d"):
            _NS_dorakai._draw_dr_body_skill(surface, boss, x, y, active_skill, skill_timer)
        elif moving:
            _NS_dorakai._draw_dr_walk(surface, boss, x, y)
        else:
            _NS_dorakai._draw_dr_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_dorakai._draw_rapid_beat_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_dorakai._draw_echo_chamber_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_dorakai._draw_dissonant_explosion_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_dorakai._draw_binding_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_dorakai._draw_final_performance_fx(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_dr_previous_timer", 0))
        active = bool(getattr(boss, "_dr_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._dr_attack_active = True
            boss._dr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._dr_attack_frame = int(getattr(boss, "_dr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._dr_attack_active = False
            boss._dr_attack_frame = 0
            active = False

        boss._dr_previous_timer = timer
        boss._dr_attack_progress = (
            min(1.0, getattr(boss, "_dr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_dr_last_x"):
            boss._dr_last_x = boss.x
            boss._dr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._dr_last_x)
        dy = abs(boss.y - boss._dr_last_y)
        boss._dr_last_x = boss.x
        boss._dr_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_dr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_dorakai._draw_dr_body(surface, x, y + bob,
                                   boss.direction, boss.pulse, "idle")

    def _draw_dr_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.8) * 3)
        sway = int(math.sin(phase * 0.9) * 2)
        _NS_dorakai._draw_dr_body(surface, x + sway, y + bob,
                                   boss.direction, phase, "walk")

    def _draw_dr_attack(surface, boss, x, y):
        """Basic attack: quick drum beat gesture with sound wave."""
        progress = getattr(boss, "_dr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Slap the drum then follow-through
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 3)
        elif progress < 0.7:
            t = (progress - 0.4) / 0.3
            lunge = int((-2 + t * 8)) * boss.direction
            lift = int(3 - t * 4)
        else:
            t = (progress - 0.7) / 0.3
            lunge = int(6 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)

        _NS_dorakai._draw_dr_body(surface, x + lunge, y - lift,
                                   boss.direction, boss.pulse, "attack",
                                   progress)

        # Basic ranged attack: sound wave arc from front drum
        _NS_dorakai._draw_basic_soundwave(surface, boss, x + lunge, y - lift,
                                           progress)

    def _draw_dr_body_skill(surface, boss, x, y, skill, timer):
        """Body pose during skill casting."""
        durations = {"q": 50, "w": 80, "e": 60, "r": 90, "d": 120}
        duration = durations.get(skill, 60)
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if skill == "q":
            # Rapid beats - shake pose alternating
            shake = int(math.sin(progress * 20) * 2)
            lift = int(math.sin(progress * 20) * 2)
            _NS_dorakai._draw_dr_body(surface, x + shake, y + lift,
                                       boss.direction, boss.pulse,
                                       "skill_q", progress)
        elif skill == "w":
            # Echo chamber - both arms extended casting
            lift = int(math.sin(progress * math.pi) * 3)
            _NS_dorakai._draw_dr_body(surface, x, y - lift,
                                       boss.direction, boss.pulse,
                                       "skill_w", progress)
        elif skill == "e":
            # Dissonant explosion - big powerful stance
            if progress < 0.3:
                t = progress / 0.3
                lift = int(t * 5)
            elif progress < 0.6:
                lift = 5
            else:
                t = (progress - 0.6) / 0.4
                lift = int(5 * (1 - t))
            _NS_dorakai._draw_dr_body(surface, x, y - lift,
                                       boss.direction, boss.pulse,
                                       "skill_e", progress)
        elif skill == "r":
            # Rhythmic binding - slow rhythmic sway
            sway = int(math.sin(progress * 8) * 3)
            _NS_dorakai._draw_dr_body(surface, x + sway, y,
                                       boss.direction, boss.pulse,
                                       "skill_r", progress)
        elif skill == "d":
            # Final performance - dramatic pose
            lift = int(math.sin(progress * math.pi) * 6)
            _NS_dorakai._draw_dr_body(surface, x, y - lift,
                                       boss.direction, boss.pulse,
                                       "skill_d", progress)

    # ============================================================
    # BODY - Muscular demon with drums attached
    # ============================================================
    def _draw_dr_body(surface, cx, cy, facing, phase, action, action_progress=0):
        """Full body draw - muscular oni with drums covering body."""
        # Long spiky hair back
        _NS_dorakai._draw_hair_back(surface, cx, cy - 16, facing, phase)

        # Legs (hakama pants)
        _NS_dorakai._draw_legs(surface, cx, cy + 22, facing, phase, action)

        # Torso (muscular bare chest with markings)
        _NS_dorakai._draw_torso(surface, cx, cy + 4, facing, phase)

        # Drum on BACK (visible from side)
        _NS_dorakai._draw_back_drum(surface, cx, cy + 4, facing, phase, action, action_progress)

        # Waist sash and hakama top
        _NS_dorakai._draw_waist(surface, cx, cy + 12, facing, phase)

        # Arms (with drum chains linking arm drums)
        _NS_dorakai._draw_arms(surface, cx, cy + 6, facing, phase, action, action_progress)

        # Drums on chest/torso (visible in front)
        _NS_dorakai._draw_chest_drums(surface, cx, cy + 4, facing, phase, action, action_progress)

        # Head with horns
        _NS_dorakai._draw_head(surface, cx, cy - 16, facing, phase, action)

    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long spiky dark hair flowing back."""
        sway = math.sin(phase * 0.5) * 2

        # Big hair mass
        hair_shape = [
            (cx - 10, cy - 4),
            (cx - 13, cy + 4),
            (cx - 16 + int(sway), cy + 14),
            (cx - 18 + int(sway), cy + 24),
            (cx - 15 + int(sway), cy + 32),
            (cx - 8, cy + 34),
            (cx - 2, cy + 30),
            (cx + 4, cy + 20),
            (cx + 6, cy + 8),
            (cx + 2, cy - 2),
        ]
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in hair_shape])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_darkest"], hair_shape)
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_dark"], [
            (cx - 9, cy - 3),
            (cx - 12, cy + 5),
            (cx - 14 + int(sway), cy + 14),
            (cx - 16 + int(sway), cy + 22),
            (cx - 13 + int(sway), cy + 28),
            (cx - 6, cy + 30),
            (cx, cy + 26),
            (cx + 3, cy + 16),
            (cx + 4, cy + 6),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_mid"], [
            (cx - 10, cy + 4),
            (cx - 12, cy + 14),
            (cx - 12 + int(sway), cy + 22),
            (cx - 8, cy + 26),
            (cx - 2, cy + 22),
            (cx, cy + 12),
        ])

        # Wild spike tips
        spike_positions = [
            (cx - 18, cy + 8, cx - 22, cy + 12, cx - 16, cy + 16),
            (cx - 20, cy + 22, cx - 24, cy + 26, cx - 16, cy + 30),
            (cx - 14, cy + 32, cx - 18, cy + 36, cx - 10, cy + 34),
        ]
        for pts in spike_positions:
            _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"], [
                (pts[0] + 1, pts[1] + 1),
                (pts[2] + 1, pts[3] + 1),
                (pts[4] + 1, pts[5] + 1),
            ])
            _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_darkest"], [
                (pts[0], pts[1]),
                (pts[2], pts[3]),
                (pts[4], pts[5]),
            ])
            _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_dark"], [
                (int((pts[0] + pts[4]) / 2), int((pts[1] + pts[5]) / 2)),
                (pts[2], pts[3]),
                (pts[4], pts[5]),
            ])

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Bare demon legs (grey skin) below hakama."""
        if action == "walk":
            leg_swing = math.sin(phase * 1.5) * 3
        else:
            leg_swing = 0

        lx = cx - 4
        rx = cx + 4
        lx_end = int(lx - leg_swing)
        rx_end = int(rx + leg_swing)

        for leg_x, leg_x_end in [(lx, lx_end), (rx, rx_end)]:
            # Shadow
            _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["shadow_deep"],
                                (leg_x + 2, cy + 2), (leg_x_end + 2, cy + 14 + 2), 6)
            # Grey skin lower legs
            _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["skin_darkest"],
                                (leg_x, cy), (leg_x_end, cy + 14), 6)
            _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["skin_dark"],
                                (leg_x, cy), (leg_x_end, cy + 14), 4)
            _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["skin_mid"],
                                (leg_x - 1, cy), (leg_x_end - 1, cy + 14), 2)

            # Red vein/marking on leg
            pygame.draw.line(surface, _NS_dorakai.PALETTE["mark_dark"],
                             (leg_x, cy + 3), (leg_x - 1, cy + 10), 1)

            # Bare foot (demon claws)
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["shadow_deep"],
                                (leg_x_end - 4, cy + 13, 10, 4))
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_darkest"],
                                (leg_x_end - 4, cy + 12, 9, 3))
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_dark"],
                                (leg_x_end - 3, cy + 12, 7, 2))
            # Toe claws
            for toe_i in range(3):
                pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_shine"],
                                 (leg_x_end + toe_i * 2 - 2, cy + 14, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular bare chest with red markings."""
        # Torso shape (broader, muscular)
        torso = [
            (cx - 10, cy - 6),
            (cx - 12, cy),
            (cx - 11, cy + 10),
            (cx - 8, cy + 16),
            (cx + 8, cy + 16),
            (cx + 11, cy + 10),
            (cx + 12, cy),
            (cx + 10, cy - 6),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in torso])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_darkest"], torso)
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_dark"], [
            (cx - 9, cy - 5),
            (cx - 11, cy),
            (cx - 10, cy + 9),
            (cx - 7, cy + 14),
            (cx + 7, cy + 14),
            (cx + 10, cy + 9),
            (cx + 11, cy),
            (cx + 9, cy - 5),
            (cx + 5, cy - 7),
            (cx - 5, cy - 7),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_mid"], [
            (cx - 7, cy - 3),
            (cx - 9, cy + 2),
            (cx - 8, cy + 8),
            (cx - 5, cy + 12),
            (cx + 5, cy + 12),
            (cx + 8, cy + 8),
            (cx + 9, cy + 2),
            (cx + 7, cy - 3),
        ])

        # Muscle definition lines
        # Chest line down middle
        pygame.draw.line(surface, _NS_dorakai.PALETTE["skin_darkest"],
                         (cx, cy - 3), (cx, cy + 8), 1)
        # Pec definitions
        pygame.draw.line(surface, _NS_dorakai.PALETTE["skin_darkest"],
                         (cx - 5, cy), (cx - 3, cy + 4), 1)
        pygame.draw.line(surface, _NS_dorakai.PALETTE["skin_darkest"],
                         (cx + 5, cy), (cx + 3, cy + 4), 1)
        # Abs
        for ab_y in (8, 11):
            pygame.draw.line(surface, _NS_dorakai.PALETTE["skin_darkest"],
                             (cx - 4, cy + ab_y), (cx + 4, cy + ab_y), 1)

        # Muscle highlights
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_light"], (cx - 4, cy - 1, 2, 3))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_light"], (cx + 3, cy - 1, 2, 3))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_shine"], (cx - 3, cy, 1, 1))

        # Red demon markings on skin (blood veins pattern)
        for i, (mx, my) in enumerate([(-7, -2), (-4, 4), (5, 3), (7, -1)]):
            pygame.draw.line(surface, _NS_dorakai.PALETTE["mark_dark"],
                             (cx + mx, cy + my), (cx + mx + 1, cy + my + 3), 1)
            pygame.draw.line(surface, _NS_dorakai.PALETTE["mark_mid"],
                             (cx + mx, cy + my + 1), (cx + mx + 1, cy + my + 2), 1)

    def _draw_back_drum(surface, cx, cy, facing, phase, action, progress):
        """Big drum on back (partially visible behind body)."""
        back_dir = -facing
        drum_x = cx + back_dir * 10
        drum_y = cy

        # Big oval drum (back)
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["shadow_deep"],
                            (drum_x - 8 + 2, drum_y - 10 + 2, 12, 20))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_darkest"],
                            (drum_x - 8, drum_y - 10, 12, 20))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_dark"],
                            (drum_x - 7, drum_y - 9, 10, 18))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_mid"],
                            (drum_x - 6, drum_y - 8, 8, 16))

        # Rim highlights (top and bottom)
        pygame.draw.line(surface, _NS_dorakai.PALETTE["drum_light"],
                         (drum_x - 6, drum_y - 8), (drum_x + 1, drum_y - 8), 1)
        pygame.draw.line(surface, _NS_dorakai.PALETTE["drum_light"],
                         (drum_x - 6, drum_y + 7), (drum_x + 1, drum_y + 7), 1)

        # Chain/rope wrapping visible
        for chain_y in (-6, -2, 2, 6):
            pygame.draw.line(surface, _NS_dorakai.PALETTE["chain_dark"],
                             (drum_x - 8, drum_y + chain_y),
                             (drum_x + 4, drum_y + chain_y), 1)

    def _draw_waist(surface, cx, cy, facing, phase):
        """Waist sash (red) with hakama below (purple)."""
        # Red sash around waist
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["shadow_deep"],
                         (cx - 12, cy, 24, 5))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["sash_dark"],
                         (cx - 11, cy, 22, 4))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["sash_mid"],
                         (cx - 11, cy, 22, 3))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["sash_light"],
                         (cx - 10, cy + 1, 20, 1))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["sash_shine"],
                         (cx - 5, cy + 1, 3, 1))

        # Sash knot on side
        knot_x = cx + facing * 8
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["sash_dark"],
                            (knot_x - 2, cy + 2, 5, 3))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["sash_mid"],
                            (knot_x - 2, cy + 2, 4, 2))

        # Purple hakama below sash
        hakama = [
            (cx - 10, cy + 4),
            (cx - 12, cy + 8),
            (cx - 10, cy + 12),
            (cx + 10, cy + 12),
            (cx + 12, cy + 8),
            (cx + 10, cy + 4),
        ]
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in hakama])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["cloth_darkest"], hakama)
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["cloth_dark"], [
            (cx - 9, cy + 5),
            (cx - 10, cy + 8),
            (cx - 9, cy + 11),
            (cx + 9, cy + 11),
            (cx + 10, cy + 8),
            (cx + 9, cy + 5),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["cloth_mid"], [
            (cx - 6, cy + 6),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 6, cy + 6),
        ])

    def _draw_arms(surface, cx, cy, facing, phase, action, progress):
        """Arms with drum on shoulder + hand pose based on action."""
        back_arm_x = cx - facing * 8
        front_arm_x = cx + facing * 8

        # Determine hand positions based on action
        if action == "attack":
            # Beating drum (front hand strikes chest drum)
            if progress < 0.4:
                t = progress / 0.4
                # Raise hand up ready to strike
                elbow_fx = front_arm_x + facing * 1
                elbow_fy = cy + 2 - int(t * 3)
                hand_fx = cx + facing * (5 - int(t * 2))
                hand_fy = cy - int(t * 5)
                elbow_bx = back_arm_x + facing * 1
                elbow_by = cy + 6
                hand_bx = back_arm_x + facing * 1
                hand_by = cy + 14
            elif progress < 0.7:
                t = (progress - 0.4) / 0.3
                # Strike down
                elbow_fx = front_arm_x + facing * 2
                elbow_fy = cy + 3 + int(t * 3)
                hand_fx = cx + facing * (4 + int(t * 4))
                hand_fy = cy + int(t * 8)
                elbow_bx = back_arm_x + facing * 1
                elbow_by = cy + 6
                hand_bx = back_arm_x + facing * 1
                hand_by = cy + 14
            else:
                t = (progress - 0.7) / 0.3
                # Recover
                elbow_fx = front_arm_x + facing * 2
                elbow_fy = cy + 6 - int(t * 1)
                hand_fx = cx + facing * (8 - int(t * 2))
                hand_fy = cy + 8 - int(t * 1)
                elbow_bx = back_arm_x + facing * 1
                elbow_by = cy + 6
                hand_bx = back_arm_x + facing * 1
                hand_by = cy + 14
        elif action == "skill_q":
            # Rapid beats - hands alternating fast
            beat_t = math.sin(progress * 30)
            elbow_fx = front_arm_x + facing * 2
            elbow_fy = cy + 3 + int(beat_t * 2)
            hand_fx = cx + facing * (5 + int(beat_t * 3))
            hand_fy = cy + 4 + int(beat_t * 4)
            elbow_bx = back_arm_x + facing * 2
            elbow_by = cy + 3 - int(beat_t * 2)
            hand_bx = cx - facing * (3 + int(beat_t * 3))
            hand_by = cy + 4 - int(beat_t * 4)
        elif action == "skill_w":
            # Echo chamber - both arms wide extended
            elbow_fx = front_arm_x + facing * 3
            elbow_fy = cy - 2
            hand_fx = cx + facing * 14
            hand_fy = cy - 6
            elbow_bx = back_arm_x - facing * 3
            elbow_by = cy - 2
            hand_bx = cx - facing * 14
            hand_by = cy - 6
        elif action == "skill_e":
            # Dissonant explosion - both hands up smashing outward
            if progress < 0.5:
                t = progress / 0.5
                elbow_fx = front_arm_x + facing * 1
                elbow_fy = cy - int(t * 3)
                hand_fx = cx + facing * (4 + int(t * 2))
                hand_fy = cy - int(t * 6)
                elbow_bx = back_arm_x - facing * 1
                elbow_by = cy - int(t * 3)
                hand_bx = cx - facing * (4 + int(t * 2))
                hand_by = cy - int(t * 6)
            else:
                t = (progress - 0.5) / 0.5
                # Slam down
                elbow_fx = front_arm_x + facing * 3
                elbow_fy = cy + int(t * 4)
                hand_fx = cx + facing * (8 + int(t * 3))
                hand_fy = cy + int(t * 6)
                elbow_bx = back_arm_x - facing * 3
                elbow_by = cy + int(t * 4)
                hand_bx = cx - facing * (8 + int(t * 3))
                hand_by = cy + int(t * 6)
        elif action == "skill_r":
            # Rhythmic binding - conducting motion
            wave = math.sin(progress * 6) * 3
            elbow_fx = front_arm_x + facing * 2
            elbow_fy = cy - int(wave)
            hand_fx = cx + facing * (10 + int(wave))
            hand_fy = cy - 2 - int(wave * 2)
            elbow_bx = back_arm_x - facing * 2
            elbow_by = cy + int(wave)
            hand_bx = cx - facing * (10 + int(wave))
            hand_by = cy - 2 + int(wave * 2)
        elif action == "skill_d":
            # Final performance - arms wide dramatic
            beat_t = math.sin(progress * 15)
            elbow_fx = front_arm_x + facing * 3
            elbow_fy = cy - 3 + int(beat_t * 2)
            hand_fx = cx + facing * (12 + int(beat_t * 3))
            hand_fy = cy - 6
            elbow_bx = back_arm_x - facing * 3
            elbow_by = cy - 3 - int(beat_t * 2)
            hand_bx = cx - facing * (12 + int(beat_t * 3))
            hand_by = cy - 6
        elif action == "walk":
            swing = math.sin(phase * 1.5) * 2
            elbow_fx = front_arm_x + facing * 1
            elbow_fy = cy + 6 + int(swing)
            hand_fx = front_arm_x + facing * 2
            hand_fy = cy + 14 + int(swing)
            elbow_bx = back_arm_x - facing * 1
            elbow_by = cy + 6 - int(swing)
            hand_bx = back_arm_x - facing * 2
            hand_by = cy + 14 - int(swing)
        else:  # idle
            breath = math.sin(phase * 0.6) * 1
            elbow_fx = front_arm_x + facing * 2
            elbow_fy = cy + 6 + int(breath)
            hand_fx = front_arm_x + facing * 3
            hand_fy = cy + 14 + int(breath)
            elbow_bx = back_arm_x - facing * 2
            elbow_by = cy + 6
            hand_bx = back_arm_x - facing * 3
            hand_by = cy + 14

        # Draw back arm first
        _NS_dorakai._draw_single_arm(surface,
                                      (back_arm_x, cy - 4),
                                      (elbow_bx, elbow_by),
                                      (hand_bx, hand_by), back=True)

        # Small drum on back shoulder (upper arm)
        _NS_dorakai._draw_shoulder_drum(surface, back_arm_x, cy - 2, back=True)

        # Draw front arm
        _NS_dorakai._draw_single_arm(surface,
                                      (front_arm_x, cy - 4),
                                      (elbow_fx, elbow_fy),
                                      (hand_fx, hand_fy), back=False)

        # Small drum on front shoulder
        _NS_dorakai._draw_shoulder_drum(surface, front_arm_x, cy - 2, back=False)

    def _draw_shoulder_drum(surface, sx, sy, back=False):
        """Small round drum on shoulder."""
        drum_dark = _NS_dorakai.PALETTE["drum_darkest" if back else "drum_dark"]
        drum_mid = _NS_dorakai.PALETTE["drum_dark" if back else "drum_mid"]
        drum_light = _NS_dorakai.PALETTE["drum_mid" if back else "drum_light"]

        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["shadow_deep"],
                            (sx - 4 + 1, sy - 3 + 1, 8, 6))
        pygame.draw.ellipse(surface, drum_dark, (sx - 4, sy - 3, 8, 6))
        pygame.draw.ellipse(surface, drum_mid, (sx - 3, sy - 2, 6, 4))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_dark"],
                            (sx - 2, sy - 2, 4, 3))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_mid"],
                            (sx - 2, sy - 2, 3, 2))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["kanji_dark"], (sx, sy - 1, 1, 1))

    def _draw_single_arm(surface, shoulder, elbow, hand, back=False):
        """Grey demon arm."""
        _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["shadow_deep"],
                            (shoulder[0] + 2, shoulder[1] + 2),
                            (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["shadow_deep"],
                            (elbow[0] + 2, elbow[1] + 2),
                            (hand[0] + 2, hand[1] + 2), 5)

        skin_darkest = _NS_dorakai.PALETTE["skin_darkest"]
        skin_dark = _NS_dorakai.PALETTE["skin_darkest" if back else "skin_dark"]
        skin_mid = _NS_dorakai.PALETTE["skin_dark" if back else "skin_mid"]
        skin_light = _NS_dorakai.PALETTE["skin_mid" if back else "skin_light"]

        # Upper arm (muscular)
        _NS_dorakai._aaline(surface, skin_darkest, shoulder, elbow, 6)
        _NS_dorakai._aaline(surface, skin_dark, shoulder, elbow, 5)
        _NS_dorakai._aaline(surface, skin_mid, shoulder, elbow, 3)
        _NS_dorakai._aaline(surface, skin_light, (shoulder[0], shoulder[1] - 1),
                            (elbow[0], elbow[1] - 1), 1)

        # Forearm
        _NS_dorakai._aaline(surface, skin_darkest, elbow, hand, 5)
        _NS_dorakai._aaline(surface, skin_dark, elbow, hand, 4)
        _NS_dorakai._aaline(surface, skin_mid, elbow, hand, 2)

        # Red vein on forearm
        pygame.draw.line(surface, _NS_dorakai.PALETTE["mark_dark"],
                         (int((elbow[0] + hand[0]) / 2),
                          int((elbow[1] + hand[1]) / 2)),
                         (hand[0], hand[1] - 1), 1)

        # Hand with claws
        _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["shadow_deep"],
                              (hand[0] + 1, hand[1] + 1), 3)
        _NS_dorakai._aacircle(surface, skin_dark, hand, 3)
        _NS_dorakai._aacircle(surface, skin_mid, hand, 2)
        # Sharp claw tips
        for cl_i in range(3):
            claw_x = hand[0] + (cl_i - 1) * 2
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_shine"],
                             (claw_x, hand[1] + 2, 1, 1))

    def _draw_chest_drums(surface, cx, cy, facing, phase, action, progress):
        """Multiple drums attached to chest/belly."""
        # Central big drum on chest
        _NS_dorakai._draw_single_drum(surface, cx, cy + 2, 8, 10, "big", phase,
                                       glowing=(action in ("attack", "skill_q", "skill_e", "skill_d")))

        # Side drum
        side_drum_x = cx + facing * 10
        _NS_dorakai._draw_single_drum(surface, side_drum_x, cy + 6, 5, 6, "small", phase,
                                       glowing=(action in ("skill_w", "skill_r")))

        # Belly drum (lower)
        _NS_dorakai._draw_single_drum(surface, cx + facing * 3, cy + 12, 5, 6, "small", phase,
                                       glowing=(action in ("skill_e", "skill_d")))

        # Chain linking drums
        pygame.draw.line(surface, _NS_dorakai.PALETTE["chain_dark"],
                         (cx - 4, cy - 2), (cx + facing * 8, cy + 4), 1)
        pygame.draw.line(surface, _NS_dorakai.PALETTE["chain_mid"],
                         (cx - 4, cy - 2), (cx + facing * 8, cy + 4), 1)
        pygame.draw.line(surface, _NS_dorakai.PALETTE["chain_dark"],
                         (cx + facing * 4, cy + 6), (cx + facing * 6, cy + 12), 1)

    def _draw_single_drum(surface, cx, cy, w, h, size, phase, glowing=False):
        """Draw one drum with wood frame + tan skin + kanji symbol."""
        # Wood outer frame
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["shadow_deep"],
                            (cx - w + 1, cy - h // 2 + 1, w * 2, h))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_darkest"],
                            (cx - w, cy - h // 2, w * 2, h))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_dark"],
                            (cx - w + 1, cy - h // 2 + 1, w * 2 - 2, h - 2))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_mid"],
                            (cx - w + 2, cy - h // 2 + 1, w * 2 - 4, h - 3))

        # Tan drum skin face
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_dark"],
                            (cx - w + 3, cy - h // 2 + 2, w * 2 - 6, h - 4))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_mid"],
                            (cx - w + 3, cy - h // 2 + 2, w * 2 - 6, h - 5))
        pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_light"],
                            (cx - w + 4, cy - h // 2 + 3, w * 2 - 9, h - 7))

        # Red kanji symbol on drum face (響 - Echo)
        if size == "big":
            # Big centered kanji
            kanji_color = _NS_dorakai.PALETTE["kanji_light"] if glowing \
                else _NS_dorakai.PALETTE["kanji_mid"]
            # Simple kanji-like shape (vertical + horizontal lines)
            pygame.draw.line(surface, _NS_dorakai.PALETTE["kanji_dark"],
                             (cx - 2, cy - 2), (cx + 2, cy - 2), 1)
            pygame.draw.line(surface, kanji_color,
                             (cx - 2, cy - 2), (cx + 2, cy - 2), 1)
            pygame.draw.line(surface, _NS_dorakai.PALETTE["kanji_dark"],
                             (cx, cy - 3), (cx, cy + 3), 1)
            pygame.draw.line(surface, kanji_color,
                             (cx, cy - 3), (cx, cy + 3), 1)
            pygame.draw.line(surface, kanji_color,
                             (cx - 2, cy + 1), (cx + 2, cy + 1), 1)
            pygame.draw.line(surface, kanji_color,
                             (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
        else:
            kanji_color = _NS_dorakai.PALETTE["kanji_light"] if glowing \
                else _NS_dorakai.PALETTE["kanji_mid"]
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["kanji_dark"],
                             (cx - 1, cy - 1, 3, 3))
            pygame.draw.rect(surface, kanji_color,
                             (cx - 1, cy - 1, 2, 2))
            pygame.draw.line(surface, _NS_dorakai.PALETTE["kanji_light"],
                             (cx, cy - 1), (cx, cy + 1), 1)

        # Rim rivets
        for rivet_i in range(4):
            angle = rivet_i * math.pi / 2 + math.pi / 4
            rx = cx + int(math.cos(angle) * (w - 1))
            ry = cy + int(math.sin(angle) * (h // 2 - 1))
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["chain_light"], (rx, ry, 1, 1))

        # Glow effect when active
        if glowing:
            pulse = math.sin(phase * 4) * 0.3 + 0.7
            for r in range(4, 0, -1):
                alpha = _NS_dorakai._alpha(120 * (4 - r) / 4 * pulse)
                pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_light"], alpha),
                                    (cx - w - r, cy - h // 2 - r,
                                     w * 2 + r * 2, h + r * 2), 1)

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Demon head with horns, red-pink glowing eyes, sharp fangs."""
        # Neck
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["shadow_deep"],
                         (cx - 3, cy + 8, 5, 6))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_darkest"],
                         (cx - 3, cy + 8, 4, 6))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_dark"],
                         (cx - 2, cy + 8, 3, 5))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_mid"],
                         (cx - 1, cy + 8, 2, 4))

        # Hair on top (spiky)
        _NS_dorakai._draw_head_hair(surface, cx, cy, facing, phase)

        # HORNS (two small demon horns)
        _NS_dorakai._draw_horns(surface, cx, cy - 6, facing, phase)

        # FACE (angular demon face)
        face_shape = [
            (cx - 6, cy - 2),
            (cx - 7, cy + 2),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 3, cy + 8),
            (cx + 6 + facing, cy + 6),
            (cx + 7 + facing, cy + 2),
            (cx + 5, cy - 2),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in face_shape])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_darkest"], face_shape)
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx - 2, cy + 7),
            (cx + 3, cy + 7),
            (cx + 5 + facing, cy + 5),
            (cx + 6 + facing, cy + 2),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 3),
            (cx - 2, cy + 6),
            (cx + 2, cy + 6),
            (cx + 4 + facing, cy + 4),
            (cx + 4 + facing, cy + 1),
            (cx + 2, cy - 2),
            (cx - 1, cy - 2),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_light"],
                         (cx + facing * 2, cy + 2, 1, 2))

        # Red face markings (jagged demon marks around eyes)
        _NS_dorakai._draw_face_marks(surface, cx, cy, facing, phase)

        # GLOWING EYES (pink-red)
        _NS_dorakai._draw_demon_eyes(surface, cx, cy + 1, facing, phase)

        # Nose hint
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_darkest"],
                         (cx + facing * 1, cy + 3, 1, 1))

        # SHARP FANGED MOUTH (open, showing fangs)
        _NS_dorakai._draw_fang_mouth(surface, cx, cy + 6, facing, phase, action)

        # Pointed demon ear
        ear_x = cx + facing * 6
        ear_y = cy + 1
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"], [
            (ear_x + 1, ear_y + 1),
            (ear_x + facing * 3 + 1, ear_y - 3 + 1),
            (ear_x + facing * 2 + 1, ear_y + 3 + 1),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_dark"], [
            (ear_x, ear_y),
            (ear_x + facing * 3, ear_y - 3),
            (ear_x + facing * 2, ear_y + 3),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["skin_mid"], [
            (ear_x + facing, ear_y),
            (ear_x + facing * 2, ear_y - 2),
            (ear_x + facing * 2, ear_y + 2),
        ])

    def _draw_head_hair(surface, cx, cy, facing, phase):
        """Spiky dark hair on top of head."""
        top_hair = [
            (cx - 8, cy - 3),
            (cx - 9, cy),
            (cx - 6, cy + 3),
            (cx - 4, cy - 1),
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 4, cy - 1),
            (cx + 6, cy + 3),
            (cx + 9, cy),
            (cx + 8, cy - 3),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ]
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in top_hair])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_darkest"], top_hair)
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_dark"], [
            (cx - 7, cy - 2),
            (cx - 8, cy),
            (cx - 5, cy + 2),
            (cx - 3, cy),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 3, cy),
            (cx + 5, cy + 2),
            (cx + 8, cy),
            (cx + 7, cy - 2),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        _NS_dorakai._poly(surface, _NS_dorakai.PALETTE["hair_mid"], [
            (cx - 5, cy - 1),
            (cx - 6, cy),
            (cx - 3, cy + 1),
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 3, cy + 1),
            (cx + 6, cy),
            (cx + 5, cy - 1),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])

    def _draw_horns(surface, cx, cy, facing, phase):
        """Two demon horns pointing up-back."""
        for side in (-1, 1):
            base_x = cx + side * 3
            base_y = cy - 2
            mid_x = cx + side * 5
            mid_y = cy - 7
            tip_x = cx + side * 3
            tip_y = cy - 12

            # Draw horn as tapered line segments
            prev = (base_x, base_y)
            for step in range(1, 5):
                t = step / 4
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y)
                thickness = max(1, 4 - step)
                _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["shadow_deep"],
                                    (prev[0] + 1, prev[1] + 1),
                                    (bx + 1, by + 1), thickness + 1)
                _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["hair_darkest"],
                                    prev, (bx, by), thickness)
                _NS_dorakai._aaline(surface, _NS_dorakai.PALETTE["skin_darkest"],
                                    prev, (bx, by), max(1, thickness - 1))
                prev = (bx, by)

            # Tip
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["skin_dark"],
                             (tip_x, tip_y, 1, 1))

    def _draw_face_marks(surface, cx, cy, facing, phase):
        """Jagged red demon markings around eyes."""
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        alpha = _NS_dorakai._alpha(220 * pulse)

        # Left eye jagged mark going up
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_dark"], alpha),
                         (cx - 3, cy - 3), (cx - 4, cy - 1), 2)
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_mid"], alpha),
                         (cx - 3, cy - 3), (cx - 4, cy - 1), 1)
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_dark"], alpha),
                         (cx - 4, cy - 1), (cx - 5, cy + 2), 1)

        # Right eye jagged mark
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_dark"], alpha),
                         (cx + 3, cy - 3), (cx + 4, cy - 1), 2)
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_mid"], alpha),
                         (cx + 3, cy - 3), (cx + 4, cy - 1), 1)
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_dark"], alpha),
                         (cx + 4, cy - 1), (cx + 5, cy + 2), 1)

        # Cheek marks
        cheek_x = cx + facing * 3
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_dark"], alpha),
                         (cheek_x, cy + 4), (cheek_x + facing * 2, cy + 3), 2)
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_mid"], alpha),
                         (cheek_x, cy + 4), (cheek_x + facing * 2, cy + 3), 1)

        # Forehead mark
        pygame.draw.line(surface, (*_NS_dorakai.PALETTE["mark_dark"], alpha),
                         (cx - 1, cy - 4), (cx + 1, cy - 4), 1)

    def _draw_demon_eyes(surface, cx, cy, facing, phase):
        """Glowing pink-red demon eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        for eye_x_off in (-3, 3):
            ex = cx + eye_x_off
            ey = cy

            # Socket
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 4, 3))

            # Glow halo
            for r in range(4, 0, -1):
                alpha = _NS_dorakai._alpha(100 * (4 - r) / 4 * pulse)
                _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE["eye_mid"], alpha),
                                       (ex + 1, ey), r)

            # Eye body
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["eye_darkest"],
                             (ex, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["eye_dark"],
                             (ex, ey, 3, 2))
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["eye_mid"],
                             (ex + 1, ey, 2, 2))
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["eye_light"],
                             (ex + 1, ey, 1, 1))
            # Bright core
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["eye_glow"],
                             (ex + 2, ey, 1, 1))
            # Vertical slit pupil
            pygame.draw.line(surface, _NS_dorakai.PALETTE["shadow_deep"],
                             (ex + 1, ey - 1), (ex + 1, ey + 1), 1)

    def _draw_fang_mouth(surface, cx, cy, facing, phase, action):
        """Sharp fanged mouth."""
        # Determine open state
        if action in ("skill_e", "skill_d"):
            mouth_open = 3
        elif action == "attack" or action == "skill_q":
            mouth_open = 2
        else:
            mouth_open = 1

        # Mouth cavity
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["shadow_deep"],
                         (cx - 2, cy - 1, 6, mouth_open + 1))
        pygame.draw.rect(surface, _NS_dorakai.PALETTE["eye_darkest"],
                         (cx - 2, cy, 5, mouth_open))

        if mouth_open >= 2:
            # Red glow inside (throat)
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["blood_mid"],
                             (cx, cy, 3, mouth_open - 1))
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_dark"],
                             (cx + 1, cy, 2, 1))

        # Upper fangs
        for fang_x in (0, 3):
            fx = cx - 1 + fang_x
            pygame.draw.line(surface, _NS_dorakai.PALETTE["skin_shine"],
                             (fx, cy - 1), (fx, cy + 1), 1)
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["white"],
                             (fx, cy + 1, 1, 1))

        # Lower fangs
        if mouth_open >= 2:
            for fang_x in (1, 3):
                fx = cx - 1 + fang_x
                pygame.draw.line(surface, _NS_dorakai.PALETTE["skin_shine"],
                                 (fx, cy + mouth_open - 1), (fx, cy + mouth_open), 1)

    # ============================================================
    # BASIC ATTACK - Sound wave crescent from front drum
    # ============================================================
    def _draw_basic_soundwave(surface, boss, x, y, progress):
        """Ranged sound wave crescent projectile."""
        if progress < 0.4:
            # Wind-up: red energy gathering at chest drum
            t = progress / 0.4
            drum_x = x
            drum_y = y + 6
            r = int(2 + t * 3)
            for radius in range(r + 3, 0, -1):
                alpha = _NS_dorakai._alpha(180 * (r + 3 - radius) / (r + 3))
                _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE["sound_dark"], alpha),
                                       (drum_x, drum_y), radius)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_mid"], (drum_x, drum_y), r)
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_hot"], (drum_x, drum_y, 1, 1))
            return

        # Launch crescent sound wave
        facing = boss.direction
        t = (progress - 0.4) / 0.6
        t = max(0.0, min(1.0, t))

        start_x = x + facing * 8
        start_y = y + 4
        travel_dist = 180
        curr_x = int(start_x + facing * t * travel_dist)
        curr_y = start_y

        # Draw crescent arc (multiple layers)
        arc_r = int(20 + t * 8)
        arc_angle_span = math.pi * 0.6  # 108 degrees

        for layer_i, (thickness, alpha_val, color) in enumerate([
            (7, 100, "sound_darkest"),
            (5, 150, "sound_dark"),
            (3, 220, "sound_mid"),
            (2, 250, "sound_light"),
            (1, 255, "sound_hot"),
        ]):
            actual_alpha = _NS_dorakai._alpha(alpha_val * (1 - t * 0.3))
            if actual_alpha <= 0:
                continue

            # Draw arc segments
            num_pts = 15
            pts = []
            for i in range(num_pts + 1):
                arc_t = i / num_pts
                # Angle range facing forward (curved shape)
                curr_angle = -arc_angle_span / 2 + arc_t * arc_angle_span
                # facing determines direction
                angle_offset = 0 if facing > 0 else math.pi
                px = curr_x + math.cos(curr_angle + angle_offset) * arc_r
                py = curr_y + math.sin(curr_angle + angle_offset) * arc_r
                pts.append((int(px), int(py)))

            for i in range(len(pts) - 1):
                _NS_dorakai._aaline(surface,
                                    (*_NS_dorakai.PALETTE[color], actual_alpha),
                                    pts[i], pts[i + 1], thickness)

        # Music note particles trailing
        for i in range(5):
            trail_t = max(0.0, t - i * 0.1)
            if trail_t <= 0:
                continue
            trail_x = int(start_x + facing * trail_t * travel_dist)
            trail_y = start_y + int(math.sin(trail_t * 5 + i) * 4)
            alpha_trail = _NS_dorakai._alpha(200 - i * 40)
            # Small crescent
            pygame.draw.rect(surface, (*_NS_dorakai.PALETTE["sound_hot"], alpha_trail),
                             (trail_x, trail_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_dorakai.PALETTE["sound_shine"], alpha_trail),
                             (trail_x, trail_y, 1, 1))

        # Impact at end
        if t > 0.9:
            tx, ty = _NS_dorakai._target_position(boss, x, y)
            st = (t - 0.9) / 0.1
            radius = int(8 + st * 15)
            alpha = _NS_dorakai._alpha(240 * (1 - st))
            _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE["sound_dark"], alpha),
                                   (tx, ty), radius, 2)
            _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE["sound_mid"], alpha),
                                   (tx, ty), max(1, radius - 5), 2)
            _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE["sound_light"], alpha),
                                   (tx, ty), max(1, radius - 10), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_dorakai.PALETTE["sound_hot"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 28), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 14 - radius, 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 3, 5, 180), (5, 8, 110, 12))
        pygame.draw.ellipse(shadow, (60, 10, 20, 100), (12, 10, 96, 10))
        surface.blit(shadow, (x - 60, y - 14))

    def _draw_sound_aura(surface, x, y, phase, skill):
        """Red-pink sound aura."""
        pulse = math.sin(phase * 0.5) * 0.3 + 0.7
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_dorakai._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_dorakai._aacircle(aura, (*_NS_dorakai.PALETTE["sound_darkest"], alpha),
                                       (100, 90), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_dorakai._alpha((45 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_dorakai._aacircle(aura, (*_NS_dorakai.PALETTE["sound_dark"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))

        # Floating music notes
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 45 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5) - 5
            # Small note
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_mid"], (sx, sy, 2, 1))
            pygame.draw.line(surface, _NS_dorakai.PALETTE["sound_mid"],
                             (sx + 1, sy), (sx + 1, sy - 2), 1)
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Red ring beneath boss."""
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        ring = pygame.Surface((140, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_dorakai.PALETTE["sound_darkest"], 200),
                            (5, 14, 130, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_dorakai.PALETTE["sound_dark"], 220),
                            (14, 16, 112, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_dorakai.PALETTE["sound_mid"], 200),
                            (26, 18, 88, 14), 1)

        # Beat marks (rhythmic pulses)
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            x1 = 70 + int(math.cos(angle) * 42)
            y1 = 25 + int(math.sin(angle) * 8)
            x2 = 70 + int(math.cos(angle) * 62)
            y2 = 25 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_dorakai.PALETTE["sound_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_dorakai.PALETTE["sound_hot"],
                                       _NS_dorakai._alpha(180 * pulse)),
                                (12, 10, 116, 30), 1)
        surface.blit(ring, (x - 70, y - 21))

    # ============================================================
    # SKILL Q - RAPID DRUM BEATING (multiple sound crescents)
    # ============================================================
    def _draw_rapid_beat_fx(surface, boss, x, y, timer, phase):
        """Multiple sound waves fire in rapid succession."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Launch multiple waves at intervals
        num_waves = 5
        for wave_i in range(num_waves):
            wave_delay = wave_i * 0.15
            wave_t = progress - wave_delay
            if wave_t <= 0 or wave_t >= 0.85:
                continue

            wave_progress = wave_t / 0.85
            start_x = x + facing * 8
            start_y = y + 4 + (wave_i - 2) * 4  # vertical spread
            curr_x = int(start_x + facing * wave_progress * 180)
            curr_y = start_y

            arc_r = int(15 + wave_progress * 6)
            arc_angle_span = math.pi * 0.5

            for layer_i, (thickness, alpha_val, color) in enumerate([
                (5, 150, "sound_dark"),
                (3, 220, "sound_mid"),
                (2, 250, "sound_light"),
                (1, 255, "sound_hot"),
            ]):
                actual_alpha = _NS_dorakai._alpha(alpha_val * (1 - wave_progress * 0.3))
                num_pts = 12
                pts = []
                for i in range(num_pts + 1):
                    arc_t = i / num_pts
                    curr_angle = -arc_angle_span / 2 + arc_t * arc_angle_span
                    angle_offset = 0 if facing > 0 else math.pi
                    px = curr_x + math.cos(curr_angle + angle_offset) * arc_r
                    py = curr_y + math.sin(curr_angle + angle_offset) * arc_r
                    pts.append((int(px), int(py)))
                for i in range(len(pts) - 1):
                    _NS_dorakai._aaline(surface,
                                        (*_NS_dorakai.PALETTE[color], actual_alpha),
                                        pts[i], pts[i + 1], thickness)

    # ============================================================
    # SKILL W - ECHO CHAMBER (concentric rings around target)
    # ============================================================
    def _draw_echo_ground(surface, boss, x, y, timer, pulse):
        """Ground indicator at target."""
        tx, ty = _NS_dorakai._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_darkest"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_dark"], 160),
                                (tx - r + 4, ty - r // 3 + 2, r * 2 - 8, r * 2 // 3 - 4))

    def _draw_echo_chamber_fx(surface, boss, x, y, timer, phase):
        """Concentric expanding rings around target."""
        tx, ty = _NS_dorakai._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple ring waves pulsing outward
        num_rings = 5
        for ring_i in range(num_rings):
            ring_t = ((phase * 0.5 + ring_i * 0.2) % 1.0)
            ring_r = int(ring_t * 60)
            if ring_r < 3:
                continue

            alpha = _NS_dorakai._alpha(220 * (1 - ring_t))
            for layer_thickness, layer_color in [(3, "sound_dark"),
                                                 (2, "sound_mid"),
                                                 (1, "sound_light")]:
                pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE[layer_color], alpha),
                                    (tx - ring_r, ty - ring_r // 2,
                                     ring_r * 2, ring_r), layer_thickness)

        # Static outer ring (echo chamber boundary)
        outer_r = 55
        boundary_alpha = _NS_dorakai._alpha(200 * (0.7 + math.sin(phase * 2) * 0.3))
        pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_hot"], boundary_alpha),
                            (tx - outer_r, ty - outer_r // 2,
                             outer_r * 2, outer_r), 2)
        pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_shine"], boundary_alpha),
                            (tx - outer_r + 1, ty - outer_r // 2 + 1,
                             outer_r * 2 - 2, outer_r - 2), 1)

        # Rotating music notes on boundary
        for i in range(8):
            note_angle = phase * 1.5 + i * math.pi / 4
            nx = tx + int(math.cos(note_angle) * outer_r)
            ny = ty + int(math.sin(note_angle) * outer_r // 2)
            # Draw note
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_hot"], (nx, ny, 2, 2))
            pygame.draw.line(surface, _NS_dorakai.PALETTE["sound_hot"],
                             (nx + 1, ny), (nx + 1, ny - 3), 1)
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_shine"], (nx, ny, 1, 1))

    # ============================================================
    # SKILL E - DISSONANT EXPLOSION (massive shockwave)
    # ============================================================
    def _draw_dissonant_ground(surface, boss, x, y, timer, pulse):
        """Ground crack pattern."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return

        t = (progress - 0.3) / 0.7
        r = int(t * 55)

        # Central dark scorch
        pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_darkest"], 220),
                            (x - r, y + 42 - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_dark"], 200),
                            (x - r + 4, y + 42 - r // 3 + 2,
                             r * 2 - 8, r * 2 // 3 - 4))

        # Radial cracks
        for i in range(10):
            angle = i * math.pi / 5
            sx = x + int(math.cos(angle) * r * 0.3)
            sy = y + 44 + int(math.sin(angle) * r * 0.15)
            ex = x + int(math.cos(angle) * r * 0.9)
            ey = y + 44 + int(math.sin(angle) * r * 0.45)
            pygame.draw.line(surface, _NS_dorakai.PALETTE["shadow_deep"],
                             (sx, sy), (ex, ey), 3)
            pygame.draw.line(surface, _NS_dorakai.PALETTE["sound_dark"],
                             (sx, sy), (ex, ey), 1)

    def _draw_dissonant_explosion_fx(surface, boss, x, y, timer, phase):
        """Massive shockwave burst outward."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge phase - energy gathering
            t = progress / 0.3
            cx = x
            cy = y - 5
            r = int(4 + t * 10)
            for radius in range(r + 6, 0, -1):
                alpha = _NS_dorakai._alpha(200 * (r + 6 - radius) / (r + 6))
                _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE["sound_dark"], alpha),
                                       (cx, cy), radius)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_mid"], (cx, cy), r)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_light"], (cx, cy), max(1, r - 3))
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_shine"], (cx, cy), max(1, r - 5))
        else:
            # Explosion phase
            t = (progress - 0.3) / 0.7
            explosion_r = int(15 + t * 70)

            # Multiple concentric shockwaves
            for wave_i in range(4):
                wave_t = min(1.0, t - wave_i * 0.1)
                if wave_t <= 0:
                    continue
                wave_r = int(wave_t * 80)
                alpha = _NS_dorakai._alpha(220 * (1 - wave_t))
                for thickness, color in [(4, "sound_darkest"),
                                         (3, "sound_dark"),
                                         (2, "sound_mid"),
                                         (1, "sound_light")]:
                    _NS_dorakai._aacircle(surface, (*_NS_dorakai.PALETTE[color], alpha),
                                           (x, y), wave_r, thickness)

            # Radial burst rays
            for i in range(16):
                angle_s = i * math.pi / 8
                ray_len = explosion_r
                ex = x + int(math.cos(angle_s) * ray_len)
                ey = y + int(math.sin(angle_s) * ray_len)
                pygame.draw.line(surface, (*_NS_dorakai.PALETTE["sound_light"],
                                           _NS_dorakai._alpha(220 * (1 - t))),
                                 (x, y), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_dorakai.PALETTE["sound_hot"],
                                           _NS_dorakai._alpha(240 * (1 - t))),
                                 (x, y), (ex, ey), 1)
                # Sparkle at tip
                pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_shine"], (ex, ey, 2, 2))

            # Central star burst
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_darkest"], (x, y), 10)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_dark"], (x, y), 8)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_mid"], (x, y), 5)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_light"], (x, y), 3)
            _NS_dorakai._aacircle(surface, _NS_dorakai.PALETTE["sound_shine"], (x, y), 1)

            # Flying music notes
            for i in range(15):
                note_angle = i * math.pi * 2 / 15 + phase
                note_r = explosion_r * 0.7 + int(math.sin(phase * 3 + i) * 5)
                nx = x + int(math.cos(note_angle) * note_r)
                ny = y + int(math.sin(note_angle) * note_r)
                pygame.draw.rect(surface, _NS_dorakai.PALETTE["note_dark"], (nx, ny, 3, 2))
                pygame.draw.line(surface, _NS_dorakai.PALETTE["note_dark"],
                                 (nx + 2, ny), (nx + 2, ny - 3), 1)

    # ============================================================
    # SKILL R - RHYTHMIC BINDING (rings around target)
    # ============================================================
    def _draw_binding_ground(surface, boss, x, y, timer, pulse):
        """Ground pattern at target."""
        tx, ty = _NS_dorakai._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_darkest"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))

    def _draw_binding_fx(surface, boss, x, y, timer, phase):
        """Multiple concentric rings binding target."""
        tx, ty = _NS_dorakai._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Static concentric rings pulsing
        for ring_i, ring_r in enumerate((25, 40, 55)):
            pulse_ring = math.sin(phase * 3 + ring_i * 1.5) * 0.3 + 0.7
            alpha = _NS_dorakai._alpha(220 * pulse_ring)

            for thickness, color in [(3, "sound_darkest"),
                                     (2, "sound_dark"),
                                     (1, "sound_mid")]:
                pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE[color], alpha),
                                    (tx - ring_r, ty - ring_r // 2,
                                     ring_r * 2, ring_r), thickness)

            # Bright markers on ring
            for i in range(6):
                marker_angle = phase * (1 + ring_i * 0.3) + i * math.pi / 3
                mx = tx + int(math.cos(marker_angle) * ring_r)
                my = ty + int(math.sin(marker_angle) * ring_r // 2)
                pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_hot"], (mx, my, 2, 2))
                pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_shine"], (mx, my, 1, 1))

        # Connecting energy beam from boss
        beam_alpha = _NS_dorakai._alpha(150 + math.sin(phase * 4) * 40)
        _NS_dorakai._aaline(surface, (*_NS_dorakai.PALETTE["sound_mid"], beam_alpha),
                            (x + boss.direction * 10, y - 4), (tx, ty), 2)
        _NS_dorakai._aaline(surface, (*_NS_dorakai.PALETTE["sound_hot"], beam_alpha),
                            (x + boss.direction * 10, y - 4), (tx, ty), 1)

        # Vertical energy bars binding (imprisonment cage effect)
        cage_r = 40
        for i in range(8):
            bar_angle = i * math.pi / 4 + phase * 0.5
            bx = tx + int(math.cos(bar_angle) * cage_r)
            by_base = ty + int(math.sin(bar_angle) * cage_r // 2)
            by_top = by_base - 30
            bar_alpha = _NS_dorakai._alpha(200 * (0.6 + math.sin(phase * 3 + i) * 0.4))
            pygame.draw.line(surface, (*_NS_dorakai.PALETTE["sound_dark"], bar_alpha),
                             (bx, by_base), (bx, by_top), 2)
            pygame.draw.line(surface, (*_NS_dorakai.PALETTE["sound_light"], bar_alpha),
                             (bx, by_base), (bx, by_top), 1)
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["sound_hot"], (bx, by_top, 1, 1))

    # ============================================================
    # SKILL D - FINAL PERFORMANCE (massive area drum solo)
    # ============================================================
    def _draw_final_ground(surface, boss, x, y, timer, pulse):
        """Ground scorched from performance."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_darkest"], 200),
                                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_dark"], 180),
                                (x - r + 4, y + 42 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            # Blood pool interior
            pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["blood_dark"], 200),
                                (x - r + 10, y + 42 - r // 4,
                                 r * 2 - 20, r // 2))

    def _draw_final_performance_fx(surface, boss, x, y, timer, phase):
        """Massive multi-drum performance with expanding sound waves and floating drums."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Floating summoned drums around boss
        num_drums = 6
        for drum_i in range(num_drums):
            drum_angle = phase * 1.5 + drum_i * math.pi * 2 / num_drums
            drum_r = 50 + int(math.sin(phase * 2 + drum_i) * 5)
            dx = x + int(math.cos(drum_angle) * drum_r)
            dy = y - 5 + int(math.sin(drum_angle) * drum_r * 0.5)

            # Draw glowing drum
            drum_size = 8
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["shadow_deep"],
                                (dx - drum_size + 1, dy - drum_size // 2 + 1,
                                 drum_size * 2, drum_size))
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_darkest"],
                                (dx - drum_size, dy - drum_size // 2,
                                 drum_size * 2, drum_size))
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["drum_dark"],
                                (dx - drum_size + 1, dy - drum_size // 2 + 1,
                                 drum_size * 2 - 2, drum_size - 2))
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_dark"],
                                (dx - drum_size + 2, dy - drum_size // 2 + 2,
                                 drum_size * 2 - 4, drum_size - 4))
            pygame.draw.ellipse(surface, _NS_dorakai.PALETTE["skin_drum_mid"],
                                (dx - drum_size + 3, dy - drum_size // 2 + 2,
                                 drum_size * 2 - 6, drum_size - 5))

            # Kanji on each drum
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["kanji_dark"],
                             (dx - 1, dy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_dorakai.PALETTE["kanji_mid"],
                             (dx - 1, dy - 1, 2, 2))

            # Glow around drum
            beat_pulse = math.sin(phase * 6 + drum_i) * 0.5 + 0.5
            for r_glow in range(5, 0, -1):
                alpha = _NS_dorakai._alpha(120 * beat_pulse * (5 - r_glow) / 5)
                pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_hot"], alpha),
                                    (dx - drum_size - r_glow, dy - drum_size // 2 - r_glow,
                                     drum_size * 2 + r_glow * 2,
                                     drum_size + r_glow * 2), 1)

            # Sound wave from each drum
            for wave_i in range(2):
                wave_t = ((phase * 0.5 + drum_i * 0.2 + wave_i * 0.5) % 1.0)
                wave_r = int(wave_t * 25)
                if wave_r < 3:
                    continue
                wave_alpha = _NS_dorakai._alpha(200 * (1 - wave_t))
                pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE["sound_light"], wave_alpha),
                                    (dx - wave_r, dy - wave_r // 2,
                                     wave_r * 2, wave_r), 2)

        # Massive central shockwaves pulsing outward
        for wave_i in range(4):
            wave_t = ((phase * 0.4 + wave_i * 0.25) % 1.0)
            wave_r = int(wave_t * 100)
            if wave_r < 5:
                continue
            wave_alpha = _NS_dorakai._alpha(180 * (1 - wave_t))
            for thickness, color in [(4, "sound_darkest"),
                                     (3, "sound_dark"),
                                     (2, "sound_mid"),
                                     (1, "sound_light")]:
                pygame.draw.ellipse(surface, (*_NS_dorakai.PALETTE[color], wave_alpha),
                                    (x - wave_r, y - wave_r // 2,
                                     wave_r * 2, wave_r), thickness)

        # Music notes flying everywhere
        for i in range(25):
            note_t = ((phase * 0.6 + i * 0.05) % 1.0)
            note_angle = i * math.pi / 12 + phase * 0.3
            note_r = int(note_t * 100)
            nx = x + int(math.cos(note_angle) * note_r)
            ny = y - 5 + int(math.sin(note_angle) * note_r * 0.6)
            alpha = _NS_dorakai._alpha(220 * (1 - note_t))
            # Music note shape
            pygame.draw.rect(surface, (*_NS_dorakai.PALETTE["note_dark"], alpha),
                             (nx, ny, 3, 2))
            pygame.draw.line(surface, (*_NS_dorakai.PALETTE["note_dark"], alpha),
                             (nx + 2, ny), (nx + 2, ny - 4), 1)
            pygame.draw.rect(surface, (*_NS_dorakai.PALETTE["sound_hot"], alpha),
                             (nx, ny, 1, 1))


# ====================================================================================================
# HITOKAGE - MINI BOSS
# ====================================================================================================

class _NS_hitokage:
    """Namespace hitokage - Sunfire blade master mini boss (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Dark red-brown hair (long)
        "hair_darkest": (30, 10, 15),
        "hair_dark": (75, 25, 30),
        "hair_mid": (135, 50, 45),
        "hair_light": (190, 90, 70),
        "hair_shine": (230, 140, 100),

        # Skin (Japanese tan)
        "skin_darkest": (95, 55, 35),
        "skin_dark": (160, 105, 75),
        "skin_mid": (220, 175, 130),
        "skin_light": (250, 220, 180),
        "skin_shine": (255, 240, 210),

        # Demon Slayer face marks (red pattern on face)
        "mark_dark": (100, 15, 20),
        "mark_mid": (200, 35, 40),
        "mark_light": (255, 90, 70),

        # Red haori (outer robe with pattern)
        "haori_darkest": (55, 15, 20),
        "haori_dark": (115, 30, 35),
        "haori_mid": (175, 55, 55),
        "haori_light": (225, 100, 90),
        "haori_shine": (250, 160, 140),

        # Dark uniform (Demon Slayer black-navy uniform)
        "uniform_darkest": (10, 12, 22),
        "uniform_dark": (25, 30, 50),
        "uniform_mid": (55, 60, 90),
        "uniform_light": (90, 95, 130),

        # Belt (leather brown)
        "belt_dark": (35, 20, 10),
        "belt_mid": (85, 55, 25),
        "belt_light": (140, 95, 50),

        # Sword (katana - dark blade with hint of red)
        "blade_darkest": (15, 12, 18),
        "blade_dark": (40, 30, 45),
        "blade_mid": (100, 85, 105),
        "blade_light": (180, 165, 180),
        "blade_shine": (240, 230, 235),
        "blade_edge": (255, 255, 255),

        # Sword hilt
        "hilt_dark": (30, 20, 15),
        "hilt_mid": (70, 45, 30),
        "hilt_wrap": (140, 20, 25),

        # Sun fire (main skill color - orange-red flames)
        "sun_darkest": (55, 10, 5),
        "sun_dark": (140, 35, 10),
        "sun_mid": (225, 90, 20),
        "sun_light": (255, 160, 50),
        "sun_hot": (255, 210, 100),
        "sun_shine": (255, 245, 200),

        # Yellow-white sun core
        "solar_core": (255, 250, 220),
        "solar_glow": (255, 235, 160),

        # Eyes (crimson red like blood)
        "eye_dark": (80, 15, 15),
        "eye_mid": (200, 40, 40),
        "eye_light": (255, 100, 80),

        # Blue sky (Clear Blue Sky ultimate)
        "sky_dark": (20, 40, 90),
        "sky_mid": (80, 140, 210),
        "sky_light": (170, 220, 255),
        "sky_shine": (240, 250, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_hitokage._clamp(color)
        if _NS_hitokage.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_hitokage._clamp(color)
        if _NS_hitokage.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_hitokage._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 100 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_hitokage(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_hitokage._detect_moving(boss)
        _NS_hitokage._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_hk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient
        _NS_hitokage._draw_shadow(surface, x, y + 46)
        _NS_hitokage._draw_sun_aura(surface, x, y, pulse, active_skill)
        _NS_hitokage._draw_ground_ring(surface, x, y + 42, pulse, active_skill)

        # D - Clear Blue Sky background
        if active_skill == "d":
            _NS_hitokage._draw_blue_sky_bg(surface, boss, x, y, skill_timer, pulse)

        # Skill ground FX
        if active_skill == "e":
            _NS_hitokage._draw_thrust_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_hitokage._draw_sunflower_ground(surface, boss, x, y, skill_timer, pulse)

        # Body - use skill-specific poses if active skill is a slash
        if active_skill == "q":
            _NS_hitokage._draw_hk_body_skill(surface, boss, x, y, "q", skill_timer)
        elif active_skill == "w":
            _NS_hitokage._draw_hk_body_skill(surface, boss, x, y, "w", skill_timer)
        elif active_skill == "e":
            _NS_hitokage._draw_hk_body_skill(surface, boss, x, y, "e", skill_timer)
        elif active_skill == "r":
            _NS_hitokage._draw_hk_body_skill(surface, boss, x, y, "r", skill_timer)
        elif active_skill == "d":
            _NS_hitokage._draw_hk_body_skill(surface, boss, x, y, "d", skill_timer)
        elif attacking:
            _NS_hitokage._draw_hk_attack(surface, boss, x, y)
        elif moving:
            _NS_hitokage._draw_hk_walk(surface, boss, x, y)
        else:
            _NS_hitokage._draw_hk_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_hitokage._draw_scorching_sun_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_hitokage._draw_blazing_sun_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_hitokage._draw_bright_red_sun_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_hitokage._draw_sunflower_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_hitokage._draw_clear_blue_sky_fx(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_hk_previous_timer", 0))
        active = bool(getattr(boss, "_hk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._hk_attack_active = True
            boss._hk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._hk_attack_frame = int(getattr(boss, "_hk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._hk_attack_active = False
            boss._hk_attack_frame = 0
            active = False

        boss._hk_previous_timer = timer
        boss._hk_attack_progress = (
            min(1.0, getattr(boss, "_hk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_hk_last_x"):
            boss._hk_last_x = boss.x
            boss._hk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._hk_last_x)
        dy = abs(boss.y - boss._hk_last_y)
        boss._hk_last_x = boss.x
        boss._hk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_hk_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_hitokage._draw_hk_body(surface, x, y + bob,
                                    boss.direction, boss.pulse, "idle")

    def _draw_hk_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(math.sin(phase * 1.8) * 3)
        sway = int(math.sin(phase * 0.9) * 2)
        _NS_hitokage._draw_hk_body(surface, x + sway, y + bob,
                                    boss.direction, phase, "walk")

    def _draw_hk_attack(surface, boss, x, y):
        """Basic MELEE swing attack."""
        progress = getattr(boss, "_hk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Katana swing arc: wind-up → swing → follow-through
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_hitokage._draw_hk_body(surface, x + lunge, y - lift,
                                    boss.direction, boss.pulse, "attack",
                                    progress)

        # Draw basic swing trail (small orange arc)
        _NS_hitokage._draw_basic_swing_trail(surface, boss, x + lunge, y - lift,
                                              progress)

    def _draw_hk_body_skill(surface, boss, x, y, skill, timer):
        """Body pose during skill casting."""
        durations = {"q": 55, "w": 65, "e": 60, "r": 80, "d": 90}
        duration = durations.get(skill, 60)
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Different poses per skill
        if skill == "q":  # upward slash - wind up then swing up
            if progress < 0.4:
                t = progress / 0.4
                lunge = -int(t * 3) * boss.direction
                lift = int(t * 3)
            else:
                t = (progress - 0.4) / 0.6
                lunge = int(t * 6) * boss.direction
                lift = int(3 - t * 5)
            _NS_hitokage._draw_hk_body(surface, x + lunge, y - lift,
                                        boss.direction, boss.pulse, "skill_q", progress)
        elif skill == "w":  # circular spin
            if progress < 0.3:
                t = progress / 0.3
                lift = int(t * 3)
                lunge = 0
            elif progress < 0.7:
                lift = 3
                lunge = 0
            else:
                t = (progress - 0.7) / 0.3
                lift = int(3 - t * 3)
                lunge = 0
            _NS_hitokage._draw_hk_body(surface, x + lunge, y - lift,
                                        boss.direction, boss.pulse, "skill_w", progress)
        elif skill == "e":  # thrust - lunge forward
            if progress < 0.3:
                t = progress / 0.3
                lunge = -int(t * 4) * boss.direction
                lift = int(t * 2)
            else:
                t = (progress - 0.3) / 0.7
                lunge = int((-4 + t * 20)) * boss.direction
                lift = int(2 - t * 2)
            _NS_hitokage._draw_hk_body(surface, x + lunge, y - lift,
                                        boss.direction, boss.pulse, "skill_e", progress)
        elif skill == "r":  # sunflower - thrust then bloom
            if progress < 0.25:
                t = progress / 0.25
                lunge = -int(t * 4) * boss.direction
                lift = int(t * 2)
            elif progress < 0.5:
                t = (progress - 0.25) / 0.25
                lunge = int((-4 + t * 18)) * boss.direction
                lift = int(2 - t * 2)
            else:
                t = (progress - 0.5) / 0.5
                lunge = int(14 * (1 - t)) * boss.direction
                lift = 0
            _NS_hitokage._draw_hk_body(surface, x + lunge, y - lift,
                                        boss.direction, boss.pulse, "skill_r", progress)
        elif skill == "d":  # final form - dramatic pose
            if progress < 0.5:
                t = progress / 0.5
                lift = int(t * 5)
                lunge = 0
            else:
                t = (progress - 0.5) / 0.5
                lift = int(5 - t * 2) + int(t * 10) * (1 if t > 0.3 else 0)
                lunge = int(t * 8) * boss.direction
            _NS_hitokage._draw_hk_body(surface, x + lunge, y - lift,
                                        boss.direction, boss.pulse, "skill_d", progress)

    # ============================================================
    # BODY - Samurai in red haori with katana
    # ============================================================
    def _draw_hk_body(surface, cx, cy, facing, phase, action, action_progress=0):
        """Full body draw with pose variations."""
        # Long hair back layer
        _NS_hitokage._draw_hair_back(surface, cx, cy - 16, facing, phase)

        # Legs (hakama-style pants)
        _NS_hitokage._draw_legs(surface, cx, cy + 22, facing, phase, action)

        # Haori trailing back
        _NS_hitokage._draw_haori_back(surface, cx, cy + 4, facing, phase)

        # Torso
        _NS_hitokage._draw_torso(surface, cx, cy + 4, facing, phase)

        # Belt with sword sheath
        _NS_hitokage._draw_belt_and_sheath(surface, cx, cy + 12, facing, phase, action)

        # Arms with sword
        _NS_hitokage._draw_arms_and_sword(surface, cx, cy + 4, facing, phase,
                                            action, action_progress)

        # Head
        _NS_hitokage._draw_head(surface, cx, cy - 16, facing, phase)

    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long dark red hair flowing behind."""
        sway = math.sin(phase * 0.5) * 2

        hair_shape = [
            (cx - 8, cy - 4),
            (cx - 12, cy + 2),
            (cx - 14 + int(sway), cy + 12),
            (cx - 16 + int(sway), cy + 22),
            (cx - 14 + int(sway), cy + 34),
            (cx - 10, cy + 40),
            (cx - 4, cy + 42),
            (cx + 2, cy + 40),
            (cx + 6, cy + 30),
            (cx + 4, cy + 18),
            (cx + 2, cy + 8),
            (cx - 2, cy - 2),
        ]
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in hair_shape])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["hair_darkest"], hair_shape)
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["hair_dark"], [
            (cx - 7, cy - 3),
            (cx - 11, cy + 3),
            (cx - 13 + int(sway), cy + 12),
            (cx - 14 + int(sway), cy + 22),
            (cx - 12 + int(sway), cy + 32),
            (cx - 8, cy + 36),
            (cx - 2, cy + 38),
            (cx + 2, cy + 34),
            (cx + 4, cy + 22),
            (cx + 2, cy + 10),
            (cx - 2, cy),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["hair_mid"], [
            (cx - 8, cy + 2),
            (cx - 10, cy + 12),
            (cx - 10 + int(sway), cy + 22),
            (cx - 8, cy + 30),
            (cx - 4, cy + 32),
            (cx, cy + 26),
            (cx, cy + 14),
            (cx - 2, cy + 4),
        ])

        # Strand highlights
        for i in range(3):
            sx = cx - 4 + i * 3
            sy1 = cy + 8
            sy2 = cy + 30
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["hair_light"],
                                  (sx, sy1), (sx - 1, sy2), 1)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Legs with hakama/dark pants."""
        if action == "walk":
            leg_swing = math.sin(phase * 1.5) * 3
        elif action in ("skill_e", "skill_r"):
            leg_swing = 2 * facing
        else:
            leg_swing = 0

        lx = cx - 4
        rx = cx + 4
        lx_end = int(lx - leg_swing)
        rx_end = int(rx + leg_swing)

        for leg_x, leg_x_end in [(lx, lx_end), (rx, rx_end)]:
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["shadow_deep"],
                                  (leg_x + 2, cy + 2), (leg_x_end + 2, cy + 14 + 2), 6)
            # Dark uniform pants
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["uniform_darkest"],
                                  (leg_x, cy), (leg_x_end, cy + 14), 6)
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["uniform_dark"],
                                  (leg_x, cy), (leg_x_end, cy + 14), 4)
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["uniform_mid"],
                                  (leg_x - 1, cy), (leg_x_end - 1, cy + 14), 2)

            # Boots/foot
            pygame.draw.ellipse(surface, _NS_hitokage.PALETTE["shadow_deep"],
                                (leg_x_end - 4, cy + 13, 10, 4))
            pygame.draw.ellipse(surface, _NS_hitokage.PALETTE["uniform_darkest"],
                                (leg_x_end - 4, cy + 12, 9, 3))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["belt_mid"],
                             (leg_x_end - 2, cy + 12, 6, 1))

    def _draw_haori_back(surface, cx, cy, facing, phase):
        """Red haori trailing back."""
        sway = math.sin(phase * 0.6) * 2
        back_dir = -facing
        base_x = cx + back_dir * 8
        base_y = cy - 4

        cape_pts = [
            (base_x, base_y - 2),
            (base_x + back_dir * 4, base_y + 4),
            (base_x + back_dir * 8 + int(sway), base_y + 14),
            (base_x + back_dir * 10 + int(sway), base_y + 24),
            (base_x + back_dir * 6, base_y + 28),
            (base_x, base_y + 20),
            (base_x - back_dir * 2, base_y + 8),
        ]
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in cape_pts])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_darkest"], cape_pts)
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_dark"], [
            (base_x + back_dir * 1, base_y),
            (base_x + back_dir * 5, base_y + 5),
            (base_x + back_dir * 8 + int(sway), base_y + 14),
            (base_x + back_dir * 9 + int(sway), base_y + 22),
            (base_x + back_dir * 4, base_y + 24),
            (base_x, base_y + 16),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_mid"], [
            (base_x + back_dir * 2, base_y + 3),
            (base_x + back_dir * 6 + int(sway), base_y + 12),
            (base_x + back_dir * 6 + int(sway), base_y + 18),
            (base_x + back_dir * 2, base_y + 18),
            (base_x, base_y + 12),
        ])

        # Flame pattern on cape edge (red on darker)
        for i, y_off in enumerate((8, 14, 20)):
            flame_x = base_x + back_dir * (5 + i)
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_dark"],
                             (flame_x, base_y + y_off, 2, 1))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_mid"],
                             (flame_x, base_y + y_off, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Torso: red haori over dark uniform."""
        # Base uniform layer
        uniform_torso = [
            (cx - 8, cy - 4),
            (cx - 9, cy),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 9, cy),
            (cx + 8, cy - 4),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ]
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in uniform_torso])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["uniform_darkest"], uniform_torso)
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["uniform_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 8, cy),
            (cx + 7, cy - 3),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])

        # Red haori open in middle (V-shape)
        # Left side
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_darkest"], [
            (cx - 9, cy - 3),
            (cx - 10, cy + 2),
            (cx - 8, cy + 12),
            (cx - 4, cy + 12),
            (cx - 2, cy + 4),
            (cx - 4, cy - 5),
            (cx - 6, cy - 5),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_dark"], [
            (cx - 8, cy - 2),
            (cx - 9, cy + 2),
            (cx - 7, cy + 10),
            (cx - 4, cy + 10),
            (cx - 2, cy + 4),
            (cx - 4, cy - 4),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_mid"], [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 6),
            (cx - 3, cy - 2),
        ])

        # Right side
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_darkest"], [
            (cx + 9, cy - 3),
            (cx + 10, cy + 2),
            (cx + 8, cy + 12),
            (cx + 4, cy + 12),
            (cx + 2, cy + 4),
            (cx + 4, cy - 5),
            (cx + 6, cy - 5),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_dark"], [
            (cx + 8, cy - 2),
            (cx + 9, cy + 2),
            (cx + 7, cy + 10),
            (cx + 4, cy + 10),
            (cx + 2, cy + 4),
            (cx + 4, cy - 4),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["haori_mid"], [
            (cx + 6, cy),
            (cx + 7, cy + 4),
            (cx + 5, cy + 8),
            (cx + 3, cy + 6),
            (cx + 3, cy - 2),
        ])

        # Middle V - showing white/gray uniform underneath
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["uniform_light"], [
            (cx - 3, cy - 5),
            (cx, cy + 2),
            (cx + 3, cy - 5),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])

        # Flame pattern accents on haori (red darker on red)
        for i, y_off in enumerate((2, 6)):
            for side in (-1, 1):
                flame_x = cx + side * 5
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_dark"],
                                 (flame_x, cy + y_off, 2, 1))
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_mid"],
                                 (flame_x, cy + y_off, 1, 1))

    def _draw_belt_and_sheath(surface, cx, cy, facing, phase, action):
        """Leather belt with katana sheath."""
        # Belt
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["shadow_deep"],
                         (cx - 9, cy, 18, 4))
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["belt_dark"],
                         (cx - 9, cy, 18, 3))
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["belt_mid"],
                         (cx - 9, cy + 1, 18, 1))

        # Belt buckle
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["belt_light"],
                         (cx - 2, cy, 4, 3))
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["belt_mid"],
                         (cx - 1, cy + 1, 2, 1))

        # Sword sheath on hip (only if not attacking - during attack sword is out)
        # Show empty sheath during attack actions
        show_full_sheath = action not in ("attack", "skill_q", "skill_w", "skill_e",
                                           "skill_r", "skill_d")

        sheath_x = cx - facing * 6
        sheath_y = cy + 2

        # Draw sheath
        for i in range(20):
            sy = sheath_y + i
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["shadow_deep"],
                                  (sheath_x - facing * 4 + 1, sy + 1),
                                  (sheath_x + facing * 6 + 1, sy + i // 4 + 1), 3)
            _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_darkest"],
                                  (sheath_x - facing * 4, sy),
                                  (sheath_x + facing * 6, sy + i // 4), 3)
            if i % 3 == 0:
                _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_dark"],
                                      (sheath_x - facing * 4, sy),
                                      (sheath_x + facing * 6, sy + i // 4), 2)

    def _draw_arms_and_sword(surface, cx, cy, facing, phase, action, progress):
        """Arms holding katana. Sword animation depends on action."""
        # Determine sword position based on action
        sword_pose = _NS_hitokage._compute_sword_pose(cx, cy, facing, action, progress, phase)

        # Draw back arm (left)
        back_arm_x = cx - facing * 6
        back_shoulder = (back_arm_x, cy - 2)
        back_hand = sword_pose.get("back_hand", (cx - facing * 2, cy + 8))
        back_elbow = ((back_shoulder[0] + back_hand[0]) // 2,
                      (back_shoulder[1] + back_hand[1]) // 2 + 2)
        _NS_hitokage._draw_single_arm(surface, back_shoulder, back_elbow,
                                        back_hand, back=True)

        # Draw front arm (right - main sword arm)
        front_arm_x = cx + facing * 6
        front_shoulder = (front_arm_x, cy - 2)
        front_hand = sword_pose.get("front_hand", (cx + facing * 8, cy + 6))
        front_elbow = ((front_shoulder[0] + front_hand[0]) // 2,
                       (front_shoulder[1] + front_hand[1]) // 2 + 2)
        _NS_hitokage._draw_single_arm(surface, front_shoulder, front_elbow,
                                        front_hand, back=False)

        # Draw sword (blade + hilt) at hand position
        if sword_pose.get("show_sword", True):
            _NS_hitokage._draw_katana(surface, front_hand, sword_pose["blade_angle"],
                                       sword_pose.get("blade_length", 22),
                                       facing, phase, sword_pose.get("fire_trail", False))

    def _compute_sword_pose(cx, cy, facing, action, progress, phase):
        """Return sword handle position and blade angle based on action."""
        pose = {"show_sword": True, "fire_trail": False}

        if action == "idle":
            breath = math.sin(phase * 0.6) * 1
            pose["front_hand"] = (cx + facing * 8, cy + 8 + int(breath))
            pose["back_hand"] = (cx - facing * 3, cy + 10 + int(breath))
            # Sword pointing down-forward (relaxed grip)
            pose["blade_angle"] = math.radians(90 * facing + 20 * facing)
        elif action == "walk":
            swing = math.sin(phase * 1.5) * 2
            pose["front_hand"] = (cx + facing * 8, cy + 10 + int(swing))
            pose["back_hand"] = (cx - facing * 3, cy + 12)
            pose["blade_angle"] = math.radians(90 * facing + 30 * facing)
        elif action == "attack":
            # Horizontal swing
            if progress < 0.3:
                t = progress / 0.3
                # Wind-up: sword raised behind
                angle = -30 - t * 60
                pose["front_hand"] = (cx - facing * 2 + int(t * 2), cy - int(t * 4))
                pose["back_hand"] = (cx - facing * 6, cy + 4)
                pose["blade_angle"] = math.radians(angle * facing)
            elif progress < 0.6:
                t = (progress - 0.3) / 0.3
                # Swing across (fast)
                angle = -90 + t * 180
                pose["front_hand"] = (cx + facing * int(2 + t * 10), cy - 4 + int(t * 6))
                pose["back_hand"] = (cx + facing * int(-4 + t * 4), cy + 4)
                pose["blade_angle"] = math.radians(angle * facing)
                pose["fire_trail"] = True
            else:
                t = (progress - 0.6) / 0.4
                # Follow through
                angle = 90 + t * 20
                pose["front_hand"] = (cx + facing * (12 - int(t * 4)), cy + 2 + int(t * 4))
                pose["back_hand"] = (cx + facing * (0 - int(t * 2)), cy + 6)
                pose["blade_angle"] = math.radians(angle * facing)
                pose["fire_trail"] = True
        elif action == "skill_q":
            # Upward slash
            if progress < 0.35:
                t = progress / 0.35
                # Wind up down
                angle = 90 + t * 60
                pose["front_hand"] = (cx + facing * 4, cy + 10 - int(t * 2))
                pose["back_hand"] = (cx - facing * 2, cy + 12)
                pose["blade_angle"] = math.radians(angle * facing)
            else:
                t = (progress - 0.35) / 0.65
                # Fast upward slash
                angle = 150 - t * 240
                pose["front_hand"] = (cx + facing * (4 + int(t * 6)), cy + 8 - int(t * 14))
                pose["back_hand"] = (cx + facing * (-2 + int(t * 4)), cy + 12 - int(t * 8))
                pose["blade_angle"] = math.radians(angle * facing)
                pose["fire_trail"] = True
        elif action == "skill_w":
            # Circular spin - sword rotates fast
            spin_angle = progress * 720
            pose["front_hand"] = (cx + facing * 6, cy + 6)
            pose["back_hand"] = (cx - facing * 4, cy + 8)
            pose["blade_angle"] = math.radians(spin_angle * facing)
            pose["fire_trail"] = True
        elif action == "skill_e":
            # Thrust forward - sword horizontal pointing forward
            if progress < 0.3:
                t = progress / 0.3
                pose["front_hand"] = (cx + facing * (4 + int(t * 2)), cy + 4)
                pose["back_hand"] = (cx + facing * (int(t * 2)), cy + 6)
                pose["blade_angle"] = math.radians(0 * facing)
            else:
                t = (progress - 0.3) / 0.7
                # Full thrust extension
                pose["front_hand"] = (cx + facing * (6 + int(t * 10)), cy + 4)
                pose["back_hand"] = (cx + facing * (2 + int(t * 6)), cy + 6)
                pose["blade_angle"] = math.radians(0 * facing)
                pose["fire_trail"] = True
        elif action == "skill_r":
            # Sunflower - thrust then bloom
            if progress < 0.4:
                t = progress / 0.4
                # Charge thrust
                pose["front_hand"] = (cx + facing * (4 + int(t * 10)), cy + 4)
                pose["back_hand"] = (cx + facing * (int(t * 4)), cy + 6)
                pose["blade_angle"] = math.radians(0 * facing)
            elif progress < 0.6:
                # Full thrust
                pose["front_hand"] = (cx + facing * 16, cy + 4)
                pose["back_hand"] = (cx + facing * 8, cy + 6)
                pose["blade_angle"] = math.radians(0 * facing)
                pose["fire_trail"] = True
            else:
                t = (progress - 0.6) / 0.4
                # Rapid multi-slash (rotate)
                spin_angle = t * 540
                pose["front_hand"] = (cx + facing * (16 - int(t * 6)), cy + 4)
                pose["back_hand"] = (cx + facing * (8 - int(t * 4)), cy + 6)
                pose["blade_angle"] = math.radians(spin_angle * facing)
                pose["fire_trail"] = True
        elif action == "skill_d":
            # Clear Blue Sky - dramatic overhead slash
            if progress < 0.4:
                t = progress / 0.4
                # Raise sword high overhead
                angle = 90 + t * 90
                pose["front_hand"] = (cx + facing * (2 + int(t * 2)),
                                       cy + 4 - int(t * 12))
                pose["back_hand"] = (cx - facing * (2 - int(t * 4)),
                                      cy + 6 - int(t * 8))
                pose["blade_angle"] = math.radians((90 + angle) * facing)
            else:
                t = (progress - 0.4) / 0.6
                # Massive swing down and across
                angle = 180 - t * 260
                pose["front_hand"] = (cx + facing * (4 + int(t * 14)),
                                       cy - 8 + int(t * 16))
                pose["back_hand"] = (cx + facing * (2 + int(t * 6)),
                                      cy - 2 + int(t * 10))
                pose["blade_angle"] = math.radians(angle * facing)
                pose["fire_trail"] = True

        return pose

    def _draw_single_arm(surface, shoulder, elbow, hand, back=False):
        """Arm with red haori sleeve."""
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["shadow_deep"],
                              (shoulder[0] + 2, shoulder[1] + 2),
                              (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["shadow_deep"],
                              (elbow[0] + 2, elbow[1] + 2),
                              (hand[0] + 2, hand[1] + 2), 5)

        haori_dark = _NS_hitokage.PALETTE["haori_darkest" if back else "haori_dark"]
        haori_mid = _NS_hitokage.PALETTE["haori_dark" if back else "haori_mid"]
        haori_light = _NS_hitokage.PALETTE["haori_mid" if back else "haori_light"]

        # Upper arm (red sleeve)
        _NS_hitokage._aaline(surface, haori_dark, shoulder, elbow, 6)
        _NS_hitokage._aaline(surface, haori_mid, shoulder, elbow, 4)
        _NS_hitokage._aaline(surface, haori_light, shoulder, elbow, 2)

        # Forearm
        _NS_hitokage._aaline(surface, haori_dark, elbow, hand, 5)
        _NS_hitokage._aaline(surface, haori_mid, elbow, hand, 3)

        # Skin visible at wrist
        skin_dark = _NS_hitokage.PALETTE["skin_darkest" if back else "skin_dark"]
        skin_mid = _NS_hitokage.PALETTE["skin_dark" if back else "skin_mid"]
        _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["shadow_deep"],
                                (hand[0] + 1, hand[1] + 1), 3)
        _NS_hitokage._aacircle(surface, skin_dark, hand, 3)
        _NS_hitokage._aacircle(surface, skin_mid, hand, 2)

    def _draw_katana(surface, handle_pos, angle, blade_length, facing, phase, fire_trail):
        """Draw katana sword: hilt + blade with proper angle."""
        hx, hy = handle_pos

        # Blade end point
        blade_end_x = hx + math.cos(angle) * blade_length
        blade_end_y = hy + math.sin(angle) * blade_length

        # Hilt (opposite direction of blade)
        hilt_len = 6
        hilt_end_x = hx - math.cos(angle) * hilt_len
        hilt_end_y = hy - math.sin(angle) * hilt_len

        # Shadow
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1),
                              (int(blade_end_x + 1), int(blade_end_y + 1)), 4)

        # BLADE (dark katana with sharp edge)
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_darkest"],
                              (hx, hy),
                              (int(blade_end_x), int(blade_end_y)), 4)
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_dark"],
                              (hx, hy),
                              (int(blade_end_x), int(blade_end_y)), 3)
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_mid"],
                              (hx, hy),
                              (int(blade_end_x), int(blade_end_y)), 2)

        # Edge highlight (thin bright line along top of blade)
        perp_angle = angle - math.pi / 2
        edge_offset_x = math.cos(perp_angle) * 1.5
        edge_offset_y = math.sin(perp_angle) * 1.5
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_shine"],
                              (int(hx + edge_offset_x), int(hy + edge_offset_y)),
                              (int(blade_end_x + edge_offset_x),
                               int(blade_end_y + edge_offset_y)), 1)
        # Very bright edge line
        edge2_offset_x = math.cos(perp_angle) * 2
        edge2_offset_y = math.sin(perp_angle) * 2
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["blade_edge"],
                              (int(hx + edge2_offset_x), int(hy + edge2_offset_y)),
                              (int(blade_end_x + edge2_offset_x),
                               int(blade_end_y + edge2_offset_y)), 1)

        # Blade tip
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["blade_shine"],
                         (int(blade_end_x), int(blade_end_y), 1, 1))
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["blade_edge"],
                         (int(blade_end_x), int(blade_end_y), 1, 1))

        # HILT GUARD (tsuba)
        _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["hilt_dark"],
                                (int(hx), int(hy)), 3)
        _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["hilt_mid"],
                                (int(hx), int(hy)), 2)

        # HILT WRAP (red)
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["hilt_dark"],
                              (int(hx), int(hy)),
                              (int(hilt_end_x), int(hilt_end_y)), 4)
        _NS_hitokage._aaline(surface, _NS_hitokage.PALETTE["hilt_wrap"],
                              (int(hx), int(hy)),
                              (int(hilt_end_x), int(hilt_end_y)), 3)
        # Wrap pattern (diamonds)
        for wrap_t in (0.25, 0.5, 0.75):
            wx = int(hx + (hilt_end_x - hx) * wrap_t)
            wy = int(hy + (hilt_end_y - hy) * wrap_t)
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["hilt_dark"], (wx, wy, 1, 1))

        # FIRE TRAIL on blade (when swinging)
        if fire_trail:
            for i in range(6):
                trail_t = i / 6
                trail_x = hx + (blade_end_x - hx) * trail_t
                trail_y = hy + (blade_end_y - hy) * trail_t
                # Fire particles along blade
                for offset_dir in (1, -1):
                    fx = int(trail_x + math.cos(perp_angle) * offset_dir * (3 + i))
                    fy = int(trail_y + math.sin(perp_angle) * offset_dir * (3 + i))
                    alpha = _NS_hitokage._alpha(220 - i * 30)
                    _NS_hitokage._aacircle(surface, (*_NS_hitokage.PALETTE["sun_dark"], alpha),
                                            (fx, fy), 2)
                    pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["sun_hot"], alpha),
                                     (fx, fy, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with distinctive face marks (Demon Slayer Mark)."""
        # Neck
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["shadow_deep"],
                         (cx - 2, cy + 8, 4, 6))
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["skin_dark"],
                         (cx - 2, cy + 8, 3, 5))
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["skin_mid"],
                         (cx - 1, cy + 8, 2, 4))

        # Hair on top of head
        _NS_hitokage._draw_head_hair(surface, cx, cy, facing, phase)

        # FACE
        face_shape = [
            (cx - 6, cy - 3),
            (cx - 7, cy + 1),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 3, cy + 8),
            (cx + 6 + facing, cy + 6),
            (cx + 7 + facing, cy + 1),
            (cx + 5, cy - 3),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ]
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in face_shape])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["skin_darkest"], face_shape)
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["skin_dark"], [
            (cx - 5, cy - 2),
            (cx - 6, cy + 1),
            (cx - 4, cy + 5),
            (cx - 2, cy + 7),
            (cx + 3, cy + 7),
            (cx + 5 + facing, cy + 5),
            (cx + 6 + facing, cy + 1),
            (cx + 4, cy - 2),
            (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["skin_mid"], [
            (cx - 3, cy - 1),
            (cx - 4, cy + 2),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 4 + facing, cy + 3),
            (cx + 4 + facing, cy),
            (cx + 2, cy - 3),
            (cx - 1, cy - 3),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["skin_light"],
                         (cx + facing * 2, cy + 2, 1, 2))

        # DEMON SLAYER FACE MARKS (red flame-like pattern on forehead & cheek)
        _NS_hitokage._draw_face_marks(surface, cx, cy, facing, phase)

        # EYES (crimson red)
        for ex_off in (-3, 3):
            ex = cx + ex_off
            ey = cy + 1
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["skin_light"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["eye_dark"],
                             (ex + (1 if ex_off > 0 else 0), ey, 1, 1))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["eye_mid"],
                             (ex + (1 if ex_off > 0 else 0), ey, 1, 1))
        # Bright eye glow (crimson eyes)
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["eye_light"],
                         (cx + facing * 3, cy + 1, 1, 1))

        # Nose hint
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["skin_darkest"],
                         (cx + facing * 1, cy + 3, 1, 1))

        # Mouth (serious line)
        pygame.draw.line(surface, _NS_hitokage.PALETTE["shadow_deep"],
                         (cx - 1, cy + 6), (cx + 2, cy + 6), 1)

    def _draw_head_hair(surface, cx, cy, facing, phase):
        """Long dark red hair on top of head with side bangs."""
        # Top hair mass
        top_hair = [
            (cx - 8, cy - 3),
            (cx - 9, cy),
            (cx - 7, cy + 4),
            (cx - 5, cy),
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy),
            (cx + 7, cy + 4),
            (cx + 9, cy),
            (cx + 8, cy - 3),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ]
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in top_hair])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["hair_darkest"], top_hair)
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["hair_dark"], [
            (cx - 7, cy - 2),
            (cx - 8, cy),
            (cx - 6, cy + 3),
            (cx - 4, cy),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 4, cy),
            (cx + 6, cy + 3),
            (cx + 8, cy),
            (cx + 7, cy - 2),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        _NS_hitokage._poly(surface, _NS_hitokage.PALETTE["hair_mid"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 1),
            (cx - 3, cy + 2),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 3, cy + 2),
            (cx + 6, cy + 1),
            (cx + 5, cy - 1),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])
        # Light streaks
        pygame.draw.line(surface, _NS_hitokage.PALETTE["hair_light"],
                         (cx - 2, cy - 5), (cx - 2, cy - 2), 1)
        pygame.draw.line(surface, _NS_hitokage.PALETTE["hair_light"],
                         (cx + 2, cy - 5), (cx + 2, cy - 2), 1)

        # Side bangs framing face
        pygame.draw.line(surface, _NS_hitokage.PALETTE["hair_darkest"],
                         (cx - 7, cy - 2), (cx - 6, cy + 6), 2)
        pygame.draw.line(surface, _NS_hitokage.PALETTE["hair_mid"],
                         (cx - 6, cy), (cx - 5, cy + 5), 1)
        pygame.draw.line(surface, _NS_hitokage.PALETTE["hair_darkest"],
                         (cx + 7, cy - 2), (cx + 6, cy + 6), 2)
        pygame.draw.line(surface, _NS_hitokage.PALETTE["hair_mid"],
                         (cx + 6, cy), (cx + 5, cy + 5), 1)

    def _draw_face_marks(surface, cx, cy, facing, phase):
        """Demon Slayer Mark - red flame-like pattern on forehead and cheek."""
        # Forehead flame mark (curved lines)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        alpha = _NS_hitokage._alpha(220 * pulse)

        # Left forehead swirl
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_dark"], alpha),
                         (cx - 3, cy - 3), (cx - 1, cy - 4), 2)
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_mid"], alpha),
                         (cx - 3, cy - 3), (cx - 1, cy - 4), 1)
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_dark"], alpha),
                         (cx - 3, cy - 3), (cx - 3, cy - 1), 1)

        # Right forehead swirl
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_dark"], alpha),
                         (cx + 1, cy - 4), (cx + 3, cy - 3), 2)
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_mid"], alpha),
                         (cx + 1, cy - 4), (cx + 3, cy - 3), 1)
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_dark"], alpha),
                         (cx + 3, cy - 3), (cx + 3, cy - 1), 1)

        # Cheek flame mark (on front-facing cheek)
        cheek_x = cx + facing * 3
        cheek_y = cy + 3
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_dark"], alpha),
                         (cheek_x, cheek_y), (cheek_x + facing * 2, cheek_y + 1), 2)
        pygame.draw.line(surface, (*_NS_hitokage.PALETTE["mark_mid"], alpha),
                         (cheek_x, cheek_y), (cheek_x + facing * 2, cheek_y + 1), 1)
        pygame.draw.rect(surface, _NS_hitokage.PALETTE["mark_light"],
                         (cheek_x, cheek_y, 1, 1))

    # ============================================================
    # BASIC ATTACK - Small orange sun arc trail
    # ============================================================
    def _draw_basic_swing_trail(surface, boss, x, y, progress):
        """Draw sword slash arc for basic attack (only during swing phase)."""
        if progress < 0.3 or progress > 0.85:
            return

        facing = boss.direction
        # Arc from top-back to bottom-front
        t = (progress - 0.3) / 0.55  # 0 to 1 during swing

        # Center of arc (in front of body)
        arc_cx = x + facing * 12
        arc_cy = y + 2
        arc_radius = 24

        # Multiple layers of arc trail
        for layer_i, (thickness, alpha_val, color) in enumerate([
            (7, 100, "sun_darkest"),
            (5, 150, "sun_dark"),
            (4, 200, "sun_mid"),
            (2, 240, "sun_light"),
            (1, 255, "sun_hot"),
        ]):
            # Draw arc from wind-up angle to current angle
            start_angle = math.radians(-100 * facing)
            end_angle = math.radians((-100 + t * 200) * facing)

            # Sample points along arc
            num_pts = 20
            pts = []
            for i in range(num_pts + 1):
                arc_t = i / num_pts
                curr_angle = start_angle + (end_angle - start_angle) * arc_t
                px = arc_cx + math.cos(curr_angle) * arc_radius
                py = arc_cy + math.sin(curr_angle) * arc_radius
                pts.append((int(px), int(py)))

            # Fade tail
            for i in range(len(pts) - 1):
                fade = i / max(1, len(pts) - 1)
                curr_alpha = _NS_hitokage._alpha(alpha_val * fade)
                _NS_hitokage._aaline(surface,
                                      (*_NS_hitokage.PALETTE[color], curr_alpha),
                                      pts[i], pts[i + 1], thickness)

        # Sparks along leading edge
        end_angle = math.radians((-100 + t * 200) * facing)
        end_x = int(arc_cx + math.cos(end_angle) * arc_radius)
        end_y = int(arc_cy + math.sin(end_angle) * arc_radius)
        for i in range(8):
            spark_angle = boss.pulse * 5 + i * math.pi / 4
            sx = end_x + int(math.cos(spark_angle) * 6)
            sy = end_y + int(math.sin(spark_angle) * 6)
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_shine"], (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 26), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius, 90 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 3, 5, 180), (5, 7, 100, 12))
        surface.blit(shadow, (x - 55, y - 13))

    def _draw_sun_aura(surface, x, y, phase, skill):
        """Orange sun aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.3 + 0.7
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_hitokage._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_hitokage._aacircle(aura, (*_NS_hitokage.PALETTE["sun_darkest"], alpha),
                                        (100, 90), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_hitokage._alpha((45 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_hitokage._aacircle(aura, (*_NS_hitokage.PALETTE["sun_dark"], alpha),
                                        (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))

        # Rising fire embers
        for i in range(12):
            ember_t = (phase * 0.6 + i * 0.09) % 1.0
            ex = x + int((i - 6) * 8) + int(math.sin(phase + i) * 3)
            ey = y + 30 - int(ember_t * 40)
            alpha = _NS_hitokage._alpha(220 * (1 - ember_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["sun_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["sun_hot"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Orange sun ring beneath boss."""
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        ring = pygame.Surface((140, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_hitokage.PALETTE["sun_darkest"], 200),
                            (5, 14, 130, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_hitokage.PALETTE["sun_dark"], 220),
                            (14, 16, 112, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_hitokage.PALETTE["sun_mid"], 200),
                            (26, 18, 88, 14), 1)

        # Sun rays
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            x1 = 70 + int(math.cos(angle) * 42)
            y1 = 25 + int(math.sin(angle) * 8)
            x2 = 70 + int(math.cos(angle) * 62)
            y2 = 25 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_hitokage.PALETTE["sun_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            color = _NS_hitokage.PALETTE["sky_light"] if skill == "d" \
                else _NS_hitokage.PALETTE["sun_hot"]
            pygame.draw.ellipse(ring, (*color, _NS_hitokage._alpha(180 * pulse)),
                                (12, 10, 116, 30), 1)
        surface.blit(ring, (x - 70, y - 21))

    # ============================================================
    # SKILL Q - SCORCHING SUN RISING (upward slash)
    # ============================================================
    def _draw_scorching_sun_fx(surface, boss, x, y, timer, phase):
        """Upward crescent slash of sun fire."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.35:
            return  # wind-up phase

        t = (progress - 0.35) / 0.65

        # Big crescent arc going upward
        arc_cx = x + facing * 16
        arc_cy = y + 8
        arc_radius = int(28 + t * 8)

        # Arc from bottom to top-forward
        start_angle = math.radians(60 * facing)
        end_angle = math.radians(-140 * facing)

        # Draw arc with multiple layers
        for layer_i, (thickness, alpha_val, color) in enumerate([
            (10, 100, "sun_darkest"),
            (7, 150, "sun_dark"),
            (5, 200, "sun_mid"),
            (3, 240, "sun_light"),
            (2, 255, "sun_hot"),
            (1, 255, "sun_shine"),
        ]):
            num_pts = 25
            pts = []
            for i in range(num_pts + 1):
                arc_t = i / num_pts
                curr_angle = start_angle + (end_angle - start_angle) * arc_t * t
                px = arc_cx + math.cos(curr_angle) * arc_radius
                py = arc_cy + math.sin(curr_angle) * arc_radius
                pts.append((int(px), int(py)))

            for i in range(len(pts) - 1):
                fade = min(1.0, (i / max(1, len(pts) - 1)) * 1.5) * (1 - t * 0.5)
                curr_alpha = _NS_hitokage._alpha(alpha_val * fade)
                _NS_hitokage._aaline(surface,
                                      (*_NS_hitokage.PALETTE[color], curr_alpha),
                                      pts[i], pts[i + 1], thickness)

        # Fire embers at arc leading edge
        end_angle_curr = start_angle + (end_angle - start_angle) * t
        end_x = int(arc_cx + math.cos(end_angle_curr) * arc_radius)
        end_y = int(arc_cy + math.sin(end_angle_curr) * arc_radius)

        for i in range(12):
            spark_angle = phase * 4 + i * math.pi / 6
            spark_r = 4 + int(math.sin(phase * 3 + i) * 3)
            sx = end_x + int(math.cos(spark_angle) * spark_r)
            sy = end_y + int(math.sin(spark_angle) * spark_r)
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_shine"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL W - BLAZING SUN (circular spin slash)
    # ============================================================
    def _draw_blazing_sun_fx(surface, boss, x, y, timer, phase):
        """Full 360° ring of fire around boss."""
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ring expands and rotates
        if progress < 0.2:
            t = progress / 0.2
            radius = int(t * 45)
        elif progress < 0.8:
            radius = 45 + int(math.sin(phase * 2) * 3)
        else:
            t = (progress - 0.8) / 0.2
            radius = int(45 * (1 - t))

        if radius < 5:
            return

        # Multiple concentric rings
        rotation = phase * 5

        for ring_i, (r_offset, thickness, alpha_val, color) in enumerate([
            (6, 6, 100, "sun_darkest"),
            (3, 5, 150, "sun_dark"),
            (0, 4, 220, "sun_mid"),
            (-2, 3, 250, "sun_light"),
            (-4, 2, 255, "sun_hot"),
        ]):
            r = radius + r_offset
            if r < 3:
                continue
            # Draw as many arc segments (rotating)
            num_segments = 24
            for i in range(num_segments):
                seg_angle_start = rotation + i * (math.pi * 2 / num_segments)
                seg_angle_end = seg_angle_start + (math.pi * 2 / num_segments) * 0.9
                x1 = x + int(math.cos(seg_angle_start) * r)
                y1 = y + int(math.sin(seg_angle_start) * r * 0.6)
                x2 = x + int(math.cos(seg_angle_end) * r)
                y2 = y + int(math.sin(seg_angle_end) * r * 0.6)
                # Vary alpha for motion feel
                alpha_var = _NS_hitokage._alpha(alpha_val * (0.5 + 0.5 * abs(math.sin(i * 0.5 + phase))))
                _NS_hitokage._aaline(surface, (*_NS_hitokage.PALETTE[color], alpha_var),
                                      (x1, y1), (x2, y2), thickness)

        # Fire particles on ring
        for i in range(20):
            angle = phase * 3 + i * math.pi / 10
            r = radius + int(math.sin(phase * 4 + i) * 4)
            px = x + int(math.cos(angle) * r)
            py = y + int(math.sin(angle) * r * 0.6)
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_hot"], (px, py, 2, 2))
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_shine"], (px, py, 1, 1))

    # ============================================================
    # SKILL E - BRIGHT RED SUN (piercing thrust with vertical pillar)
    # ============================================================
    def _draw_thrust_ground(surface, boss, x, y, timer, phase):
        """Ground scorch line for thrust."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return

        t = (progress - 0.3) / 0.7
        line_len = int(120 * t)

        base_x = x + facing * 16
        base_y = y + 42

        # Scorched ground trail
        for i in range(line_len // 4):
            px = base_x + i * 4 * facing
            alpha = _NS_hitokage._alpha(200 * (1 - i * 4 / line_len))
            pygame.draw.line(surface, (*_NS_hitokage.PALETTE["sun_darkest"], alpha),
                             (px, base_y - 1), (px, base_y + 2), 3)
            pygame.draw.line(surface, (*_NS_hitokage.PALETTE["sun_dark"], alpha),
                             (px, base_y), (px, base_y + 1), 2)

    def _draw_bright_red_sun_fx(surface, boss, x, y, timer, phase):
        """Massive vertical pillar of sun fire piercing forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_hitokage._target_position(boss, x, y)

        if progress < 0.3:
            # Wind-up: gathering fire at sword tip
            t = progress / 0.3
            sword_tip_x = x + facing * 20
            sword_tip_y = y - 2
            r = int(3 + t * 6)
            for radius in range(r + 4, 0, -1):
                alpha = _NS_hitokage._alpha(200 * (r + 4 - radius) / (r + 4))
                _NS_hitokage._aacircle(surface, (*_NS_hitokage.PALETTE["sun_dark"], alpha),
                                        (sword_tip_x, sword_tip_y), radius)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_mid"], (sword_tip_x, sword_tip_y), r)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_hot"], (sword_tip_x, sword_tip_y), max(1, r - 2))
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_shine"], (sword_tip_x, sword_tip_y), max(1, r - 3))
            return

        # Thrust phase - long piercing horizontal line + vertical pillar at target
        t = (progress - 0.3) / 0.7
        intensity = math.sin(t * math.pi)

        thrust_start_x = x + facing * 20
        thrust_start_y = y - 2
        thrust_length = int(180 * t)
        thrust_end_x = thrust_start_x + facing * thrust_length
        thrust_end_y = thrust_start_y

        # Horizontal piercing beam
        for layer_i, (thickness, alpha_val, color) in enumerate([
            (12, 100, "sun_darkest"),
            (8, 150, "sun_dark"),
            (5, 220, "sun_mid"),
            (3, 250, "sun_light"),
            (1, 255, "sun_hot"),
        ]):
            actual_alpha = _NS_hitokage._alpha(alpha_val * intensity)
            if actual_alpha <= 0:
                continue
            _NS_hitokage._aaline(surface, (*_NS_hitokage.PALETTE[color], actual_alpha),
                                  (thrust_start_x, thrust_start_y),
                                  (thrust_end_x, thrust_end_y), thickness)

        # Massive vertical pillar at thrust end
        if t > 0.3:
            pillar_x = thrust_end_x
            pillar_bottom_y = thrust_end_y + 50
            pillar_top_y = thrust_end_y - 80

            for layer_i, (width, alpha_val, color) in enumerate([
                (18, 100, "sun_darkest"),
                (14, 150, "sun_dark"),
                (10, 220, "sun_mid"),
                (6, 250, "sun_light"),
                (3, 255, "sun_hot"),
                (1, 255, "sun_shine"),
            ]):
                actual_alpha = _NS_hitokage._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE[color], actual_alpha),
                                 (pillar_x - width // 2, pillar_top_y,
                                  width, pillar_bottom_y - pillar_top_y))

            # Sparks rising up pillar
            for i in range(20):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                sy = pillar_bottom_y - int(spark_t * (pillar_bottom_y - pillar_top_y))
                sx = pillar_x + int(math.sin(phase * 5 + i) * 8)
                alpha = _NS_hitokage._alpha(240 * intensity * (1 - spark_t * 0.5))
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["sun_hot"], alpha),
                                 (sx, sy, 2, 3))
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["sun_shine"], alpha),
                                 (sx, sy, 1, 2))

            # Impact burst at pillar base
            burst_r = int(15 + t * 15)
            burst_alpha = _NS_hitokage._alpha(240 * intensity)
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = pillar_x + int(math.cos(angle_s) * burst_r)
                ey = pillar_bottom_y + int(math.sin(angle_s) * burst_r * 0.5)
                pygame.draw.line(surface, (*_NS_hitokage.PALETTE["sun_light"], burst_alpha),
                                 (pillar_x, pillar_bottom_y), (ex, ey), 2)

    # ============================================================
    # SKILL R - SUNFLOWER THRUST (thrust + explosion of petal slashes)
    # ============================================================
    def _draw_sunflower_ground(surface, boss, x, y, timer, phase):
        """Ground scorch pattern (sunflower)."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            return

        target_x = x + facing * 60
        target_y = y + 40
        t = (progress - 0.5) / 0.5
        r = int(t * 55)

        pygame.draw.ellipse(surface, (*_NS_hitokage.PALETTE["sun_darkest"], 200),
                            (target_x - r, target_y - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface, (*_NS_hitokage.PALETTE["sun_dark"], 180),
                            (target_x - r + 4, target_y - r // 3 + 2,
                             r * 2 - 8, r * 2 // 3 - 4))

    def _draw_sunflower_fx(surface, boss, x, y, timer, phase):
        """Central thrust then explosion of slashes like sunflower petals."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Charge phase - gathering at sword tip
            t = progress / 0.4
            sword_tip_x = x + facing * 20
            sword_tip_y = y - 2
            r = int(4 + t * 8)
            for radius in range(r + 5, 0, -1):
                alpha = _NS_hitokage._alpha(200 * (r + 5 - radius) / (r + 5))
                _NS_hitokage._aacircle(surface, (*_NS_hitokage.PALETTE["sun_dark"], alpha),
                                        (sword_tip_x, sword_tip_y), radius)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_mid"], (sword_tip_x, sword_tip_y), r)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_hot"], (sword_tip_x, sword_tip_y), max(1, r - 3))
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["solar_core"], (sword_tip_x, sword_tip_y), max(1, r - 5))

        elif progress < 0.6:
            # Thrust phase - forward beam
            t = (progress - 0.4) / 0.2
            start_x = x + facing * 20
            start_y = y - 2
            end_x = start_x + facing * int(80 * t)
            end_y = start_y

            for layer_i, (thickness, alpha_val, color) in enumerate([
                (10, 150, "sun_darkest"),
                (6, 200, "sun_mid"),
                (3, 250, "sun_light"),
                (1, 255, "sun_hot"),
            ]):
                _NS_hitokage._aaline(surface, (*_NS_hitokage.PALETTE[color], alpha_val),
                                      (start_x, start_y), (end_x, end_y), thickness)

        else:
            # Explosion phase - sunflower petals radiating out
            t = (progress - 0.6) / 0.4
            explosion_center_x = x + facing * 60
            explosion_center_y = y - 2

            # Central bright core
            core_r = int(8 + math.sin(phase * 3) * 2)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_darkest"],
                                    (explosion_center_x, explosion_center_y), core_r + 3)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_dark"],
                                    (explosion_center_x, explosion_center_y), core_r + 2)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_mid"],
                                    (explosion_center_x, explosion_center_y), core_r)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_light"],
                                    (explosion_center_x, explosion_center_y), core_r - 2)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_hot"],
                                    (explosion_center_x, explosion_center_y), max(1, core_r - 4))
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["solar_core"],
                                    (explosion_center_x, explosion_center_y), 2)
            pygame.draw.rect(surface, _NS_hitokage.PALETTE["white"],
                             (explosion_center_x, explosion_center_y, 1, 1))

            # Radiating petal slashes (elongated triangles like sunflower petals)
            num_petals = 12
            petal_length = int(20 + t * 40)

            for i in range(num_petals):
                angle = i * math.pi * 2 / num_petals + phase * 0.3
                petal_tip_x = explosion_center_x + int(math.cos(angle) * petal_length)
                petal_tip_y = explosion_center_y + int(math.sin(angle) * petal_length)

                # Petal shape (thin elongated)
                perp_angle = angle + math.pi / 2
                base_a = (explosion_center_x + int(math.cos(perp_angle) * 4),
                          explosion_center_y + int(math.sin(perp_angle) * 4))
                base_b = (explosion_center_x - int(math.cos(perp_angle) * 4),
                          explosion_center_y - int(math.sin(perp_angle) * 4))

                alpha = _NS_hitokage._alpha(240 * (1 - t * 0.5))
                _NS_hitokage._poly(surface, (*_NS_hitokage.PALETTE["sun_darkest"], alpha), [
                    (petal_tip_x, petal_tip_y), base_a, base_b,
                ])
                # Bright center petal
                mid_a = (int((petal_tip_x + base_a[0]) / 2),
                         int((petal_tip_y + base_a[1]) / 2))
                mid_b = (int((petal_tip_x + base_b[0]) / 2),
                         int((petal_tip_y + base_b[1]) / 2))
                _NS_hitokage._poly(surface, (*_NS_hitokage.PALETTE["sun_mid"], alpha), [
                    (petal_tip_x, petal_tip_y), mid_a, mid_b,
                ])
                # Tip glow
                _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sun_hot"],
                                        (petal_tip_x, petal_tip_y), 2)
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_shine"],
                                 (petal_tip_x, petal_tip_y, 1, 1))

            # Additional sparkle explosion
            for i in range(20):
                spark_angle = phase * 2 + i * math.pi / 10
                spark_r = petal_length + int(math.sin(phase * 4 + i) * 8)
                sx = explosion_center_x + int(math.cos(spark_angle) * spark_r)
                sy = explosion_center_y + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sun_shine"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL D - CLEAR BLUE SKY (transcendent single massive slash)
    # ============================================================
    def _draw_blue_sky_bg(surface, boss, x, y, timer, phase):
        """Blue sky transformation background."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Sky glow gradient - transitioning from red to clear blue
        pulse = math.sin(phase * 0.8) * 0.2 + 0.8
        aura_alpha = _NS_hitokage._alpha(180 * pulse)

        sky_aura = pygame.Surface((300, 250), pygame.SRCALPHA)
        # Blue outer glow
        for r in range(140, 30, -6):
            alpha = _NS_hitokage._alpha((140 - r) * 1.0 * pulse)
            _NS_hitokage._aacircle(sky_aura, (*_NS_hitokage.PALETTE["sky_dark"], alpha),
                                    (150, 125), r)
        # Blue mid
        for r in range(90, 20, -4):
            alpha = _NS_hitokage._alpha((90 - r) * 1.3 * pulse)
            _NS_hitokage._aacircle(sky_aura, (*_NS_hitokage.PALETTE["sky_mid"], alpha),
                                    (150, 125), r)
        # Bright core
        for r in range(40, 5, -2):
            alpha = _NS_hitokage._alpha((40 - r) * 2.0 * pulse)
            _NS_hitokage._aacircle(sky_aura, (*_NS_hitokage.PALETTE["sky_light"], alpha),
                                    (150, 125), r)
        surface.blit(sky_aura, (x - 150, y - 125))

    def _draw_clear_blue_sky_fx(surface, boss, x, y, timer, phase):
        """The ultimate transcendent slash - massive white-blue arc."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Charge phase - blade glowing intensely with blue-white light
            t = progress / 0.4
            sword_tip_x = x + facing * 4
            sword_tip_y = y - 20
            r = int(5 + t * 12)

            # Bright white-blue charging orb at sword tip
            for radius in range(r + 8, 0, -1):
                alpha = _NS_hitokage._alpha(200 * (r + 8 - radius) / (r + 8))
                _NS_hitokage._aacircle(surface, (*_NS_hitokage.PALETTE["sky_dark"], alpha),
                                        (sword_tip_x, sword_tip_y), radius)
            for radius in range(r + 3, 0, -1):
                alpha = _NS_hitokage._alpha(220 * (r + 3 - radius) / (r + 3))
                _NS_hitokage._aacircle(surface, (*_NS_hitokage.PALETTE["sky_mid"], alpha),
                                        (sword_tip_x, sword_tip_y), radius)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sky_light"], (sword_tip_x, sword_tip_y), r - 2)
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["sky_shine"], (sword_tip_x, sword_tip_y), max(1, r - 4))
            _NS_hitokage._aacircle(surface, _NS_hitokage.PALETTE["white"], (sword_tip_x, sword_tip_y), max(1, r - 6))

            # Sparkles gathering
            for i in range(10):
                angle = phase * 5 + i * math.pi / 5
                sx = sword_tip_x + int(math.cos(angle) * (r + 3))
                sy = sword_tip_y + int(math.sin(angle) * (r + 3))
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sky_shine"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["white"], (sx, sy, 1, 1))

        else:
            # Slash phase - massive arc of blue-white light
            t = (progress - 0.4) / 0.6

            # Huge arc from top to bottom-forward
            arc_cx = x + facing * 8
            arc_cy = y + 4
            arc_radius = int(50 + t * 20)

            start_angle = math.radians(-120 * facing)
            end_angle = math.radians(80 * facing)

            # Draw MASSIVE arc with many layers
            for layer_i, (thickness, alpha_val, color) in enumerate([
                (16, 80, "sky_dark"),
                (12, 130, "sky_mid"),
                (8, 180, "sky_light"),
                (5, 220, "sky_shine"),
                (3, 250, "white"),
                (1, 255, "white"),
            ]):
                num_pts = 30
                pts = []
                for i in range(num_pts + 1):
                    arc_t = i / num_pts
                    curr_angle = start_angle + (end_angle - start_angle) * arc_t * t
                    px = arc_cx + math.cos(curr_angle) * arc_radius
                    py = arc_cy + math.sin(curr_angle) * arc_radius
                    pts.append((int(px), int(py)))

                for i in range(len(pts) - 1):
                    fade = min(1.0, (i / max(1, len(pts) - 1)) * 1.3) * (1 - t * 0.3)
                    curr_alpha = _NS_hitokage._alpha(alpha_val * fade)
                    _NS_hitokage._aaline(surface,
                                          (*_NS_hitokage.PALETTE[color], curr_alpha),
                                          pts[i], pts[i + 1], thickness)

            # Massive sparkle burst at end of arc
            end_angle_curr = start_angle + (end_angle - start_angle) * t
            end_x = int(arc_cx + math.cos(end_angle_curr) * arc_radius)
            end_y = int(arc_cy + math.sin(end_angle_curr) * arc_radius)

            for i in range(20):
                spark_angle = phase * 3 + i * math.pi / 10
                spark_r = 6 + int(math.sin(phase * 4 + i) * 5)
                sx = end_x + int(math.cos(spark_angle) * spark_r)
                sy = end_y + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["sky_shine"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_hitokage.PALETTE["white"], (sx, sy, 1, 1))

            # Trailing petal sparkles along arc
            for i in range(15):
                arc_t = i / 15
                curr_angle = start_angle + (end_angle - start_angle) * arc_t * t
                px = int(arc_cx + math.cos(curr_angle) * (arc_radius + 6))
                py = int(arc_cy + math.sin(curr_angle) * (arc_radius + 6))
                alpha = _NS_hitokage._alpha(200 * (1 - t * 0.5))
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["sky_shine"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_hitokage.PALETTE["white"], alpha),
                                 (px, py, 1, 1))


# ====================================================================================================
# KAZUREN - MINI BOSS
# ====================================================================================================

class _NS_kazuren:
    """Namespace kazuren - Masked shadow ninja mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Black Akatsuki cloak
        "cloak_darkest": (5, 5, 8),
        "cloak_dark": (20, 20, 28),
        "cloak_mid": (45, 42, 55),
        "cloak_light": (75, 70, 85),
        "cloak_shine": (110, 105, 120),

        # Red cloud accents (Akatsuki cloud)
        "red_darkest": (60, 10, 15),
        "red_dark": (130, 25, 30),
        "red_mid": (200, 45, 50),
        "red_light": (240, 90, 85),
        "red_shine": (255, 160, 150),

        # Orange mask (Tobi mask)
        "mask_darkest": (70, 30, 5),
        "mask_dark": (140, 65, 15),
        "mask_mid": (215, 115, 30),
        "mask_light": (250, 170, 60),
        "mask_shine": (255, 220, 130),

        # Sharingan red eye
        "sharingan_darkest": (30, 3, 5),
        "sharingan_dark": (110, 15, 20),
        "sharingan_mid": (200, 30, 35),
        "sharingan_light": (255, 80, 70),
        "sharingan_glow": (255, 180, 160),

        # Skin (aged)
        "skin_darkest": (75, 45, 30),
        "skin_dark": (140, 90, 65),
        "skin_mid": (200, 150, 110),
        "skin_light": (240, 200, 160),

        # Spiky hair (dark)
        "hair_darkest": (10, 10, 15),
        "hair_dark": (30, 30, 40),
        "hair_mid": (60, 55, 70),
        "hair_light": (100, 95, 110),

        # Pants (dark)
        "pants_dark": (25, 22, 28),
        "pants_mid": (55, 50, 60),
        "pants_light": (85, 80, 95),

        # Bandages (leg wraps, tan)
        "bandage_dark": (110, 90, 65),
        "bandage_mid": (175, 155, 120),
        "bandage_light": (225, 205, 165),

        # Fire (orange skill)
        "fire_darkest": (60, 15, 5),
        "fire_dark": (140, 45, 10),
        "fire_mid": (220, 100, 20),
        "fire_light": (255, 175, 50),
        "fire_hot": (255, 220, 120),
        "fire_shine": (255, 250, 200),

        # Kamui purple (dimension portal / phase)
        "kamui_darkest": (15, 5, 30),
        "kamui_dark": (45, 15, 80),
        "kamui_mid": (110, 45, 170),
        "kamui_light": (170, 100, 230),
        "kamui_hot": (215, 160, 255),
        "kamui_shine": (245, 220, 255),

        # Wood needles (brown-yellow)
        "wood_darkest": (35, 25, 10),
        "wood_dark": (85, 60, 20),
        "wood_mid": (150, 115, 45),
        "wood_light": (215, 180, 90),
        "wood_shine": (250, 225, 150),

        # Rinnegan (purple with rings)
        "rin_darkest": (25, 10, 40),
        "rin_dark": (70, 30, 110),
        "rin_mid": (140, 80, 200),
        "rin_light": (200, 150, 240),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kazuren._clamp(color)
        if _NS_kazuren.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kazuren._clamp(color)
        if _NS_kazuren.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kazuren._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kazuren(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kazuren._detect_moving(boss)
        _NS_kazuren._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_kazuren._draw_shadow(surface, x, y + 46)

        # Phase shift makes body translucent
        phasing = (active_skill == "w")
        # Rinnegan ultimate aura
        rinnegan_mode = (active_skill == "r")

        if rinnegan_mode:
            _NS_kazuren._draw_rinnegan_aura(surface, x, y, pulse)

        _NS_kazuren._draw_ground_seal(surface, x, y + 42, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_kazuren._draw_wood_needles_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kazuren._draw_dimension_portal_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if phasing:
            _NS_kazuren._draw_kz_phase_body(surface, boss, x, y, skill_timer)
        elif attacking:
            _NS_kazuren._draw_kz_attack(surface, boss, x, y, rinnegan_mode)
        elif moving:
            _NS_kazuren._draw_kz_walk(surface, boss, x, y, rinnegan_mode)
        else:
            _NS_kazuren._draw_kz_idle(surface, boss, x, y, rinnegan_mode)

        # Foreground skill FX
        if active_skill == "q":
            _NS_kazuren._draw_fire_bomb_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kazuren._draw_phase_shift_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kazuren._draw_wood_needles_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kazuren._draw_dimension_portal_skill(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kz_previous_timer", 0))
        active = bool(getattr(boss, "_kz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._kz_attack_active = True
            boss._kz_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kz_attack_frame = int(getattr(boss, "_kz_attack_frame", 0)) + 1
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
    def _draw_kz_idle(surface, boss, x, y, rinnegan_mode):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_kazuren._draw_kz_body(surface, x, y + bob,
                                   boss.direction, boss.pulse, "idle",
                                   rinnegan_mode=rinnegan_mode)

    def _draw_kz_walk(surface, boss, x, y, rinnegan_mode):
        phase = boss.pulse * 2.2
        bob = int(math.sin(phase * 1.8) * 2)
        sway = int(math.sin(phase * 0.9) * 2)
        _NS_kazuren._draw_kz_body(surface, x + sway, y + bob,
                                   boss.direction, phase, "walk",
                                   rinnegan_mode=rinnegan_mode)

    def _draw_kz_attack(surface, boss, x, y, rinnegan_mode):
        progress = getattr(boss, "_kz_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        if progress < 0.5:
            t = progress / 0.5
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        else:
            t = (progress - 0.5) / 0.5
            lunge = int(t * 5) * boss.direction
            lift = int(2 - t * 2)

        _NS_kazuren._draw_kz_body(surface, x + lunge, y - lift,
                                   boss.direction, boss.pulse, "attack",
                                   progress, rinnegan_mode=rinnegan_mode)

        # Basic ranged attack: fire ball projectile from Sharingan
        _NS_kazuren._draw_basic_fireball(surface, boss, x + lunge, y - lift,
                                          progress)

    def _draw_kz_phase_body(surface, boss, x, y, timer):
        """During Phase Shift (W) - body becomes translucent purple ghost."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Fade based on phase: fade OUT then IN
        if progress < 0.4:
            alpha_mult = 1.0 - (progress / 0.4) * 0.7
        elif progress < 0.7:
            alpha_mult = 0.3
        else:
            alpha_mult = 0.3 + ((progress - 0.7) / 0.3) * 0.7

        # Draw to alpha surface
        ghost_surf = pygame.Surface((120, 140), pygame.SRCALPHA)
        _NS_kazuren._draw_kz_body(ghost_surf, 60, 70,
                                   boss.direction, boss.pulse, "idle",
                                   rinnegan_mode=False)
        # Apply alpha
        ghost_surf.set_alpha(int(255 * alpha_mult))
        surface.blit(ghost_surf, (x - 60, y - 70))

        # Purple aura swirl around body
        for i in range(10):
            angle = boss.pulse * 3 + i * math.pi / 5
            r = 20 + int(math.sin(boss.pulse * 2 + i) * 6)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r * 0.6) - 8
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["kamui_dark"], (sx, sy), 3)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["kamui_mid"], (sx, sy), 2)
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["kamui_hot"], (sx, sy, 1, 1))

    # ============================================================
    # BODY - Humanoid Akatsuki Ninja
    # ============================================================
    def _draw_kz_body(surface, cx, cy, facing, phase, action,
                     attack_progress=0, rinnegan_mode=False):
        """Draw humanoid: legs, cloak (Akatsuki), arms, masked head."""
        # Legs (mostly hidden by cloak, but bandaged feet show)
        _NS_kazuren._draw_legs(surface, cx, cy + 22, facing, phase, action)

        # Cloak back trailing
        _NS_kazuren._draw_cloak_back(surface, cx, cy + 4, facing, phase)

        # Torso (Akatsuki cloak)
        _NS_kazuren._draw_torso(surface, cx, cy + 4, facing, phase)

        # Arms
        _NS_kazuren._draw_arms(surface, cx, cy + 6, facing, phase, action,
                                attack_progress)

        # Head + spiky hair + mask
        _NS_kazuren._draw_head(surface, cx, cy - 16, facing, phase, rinnegan_mode)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Two legs with dark pants and bandaged feet."""
        if action == "walk":
            leg_swing = math.sin(phase * 1.5) * 2
        else:
            leg_swing = 0

        lx = cx - 4
        ly = cy
        lx_end = int(lx - leg_swing)
        rx = cx + 4
        ry = cy
        rx_end = int(rx + leg_swing)

        for leg_x, leg_x_end in [(lx, lx_end), (rx, rx_end)]:
            # Shadow
            _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["shadow_deep"],
                                (leg_x + 2, ly + 2), (leg_x_end + 2, ly + 14 + 2), 5)
            # Pants
            _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["pants_dark"],
                                (leg_x, ly), (leg_x_end, ly + 10), 5)
            _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["pants_mid"],
                                (leg_x, ly), (leg_x_end, ly + 10), 3)

            # Bandage wraps at ankle (visible under cloak)
            for w_i in range(3):
                wy = ly + 10 + w_i * 2
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["bandage_dark"],
                                 (leg_x_end - 3, wy, 6, 2))
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["bandage_mid"],
                                 (leg_x_end - 3, wy, 6, 1))
                pygame.draw.line(surface, _NS_kazuren.PALETTE["bandage_dark"],
                                 (leg_x_end - 3, wy + 1),
                                 (leg_x_end + 3, wy + 1), 1)

            # Sandal (foot)
            pygame.draw.ellipse(surface, _NS_kazuren.PALETTE["shadow_deep"],
                                (leg_x_end - 4, ly + 17, 10, 4))
            pygame.draw.ellipse(surface, _NS_kazuren.PALETTE["pants_dark"],
                                (leg_x_end - 4, ly + 16, 9, 3))

    def _draw_cloak_back(surface, cx, cy, facing, phase):
        """Long trailing black cloak with red cloud pattern."""
        sway = math.sin(phase * 0.6) * 2
        back_dir = -facing
        base_x = cx + back_dir * 8
        base_y = cy - 6

        # Long cape trailing back
        cape_pts = [
            (base_x, base_y - 4),
            (base_x + back_dir * 6, base_y),
            (base_x + back_dir * 10 + int(sway), base_y + 8),
            (base_x + back_dir * 14 + int(sway), base_y + 18),
            (base_x + back_dir * 12 + int(sway), base_y + 28),
            (base_x + back_dir * 6, base_y + 30),
            (base_x, base_y + 24),
            (base_x - back_dir * 3, base_y + 10),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in cape_pts])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_darkest"], cape_pts)

        # Inner darker shading
        inner_pts = [
            (base_x + back_dir * 1, base_y - 2),
            (base_x + back_dir * 5, base_y + 1),
            (base_x + back_dir * 8 + int(sway), base_y + 9),
            (base_x + back_dir * 11 + int(sway), base_y + 18),
            (base_x + back_dir * 9 + int(sway), base_y + 24),
            (base_x + back_dir * 4, base_y + 25),
            (base_x, base_y + 20),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_dark"], inner_pts)

        # Mid highlight
        highlight_pts = [
            (base_x + back_dir * 3, base_y + 2),
            (base_x + back_dir * 6 + int(sway), base_y + 10),
            (base_x + back_dir * 8 + int(sway), base_y + 18),
            (base_x + back_dir * 4, base_y + 20),
            (base_x + back_dir * 1, base_y + 14),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_mid"], highlight_pts)

        # Red cloud pattern on cape (Akatsuki cloud)
        cloud_x = base_x + back_dir * 6 + int(sway)
        cloud_y = base_y + 14
        _NS_kazuren._draw_akatsuki_cloud(surface, cloud_x, cloud_y, 4)

    def _draw_akatsuki_cloud(surface, cx, cy, size):
        """Red cloud with white outline (Akatsuki cloud pattern)."""
        # White border
        for pt_offset in [(-3, -1), (-1, -2), (2, -2), (3, 0), (2, 2), (0, 2), (-2, 2), (-3, 0)]:
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["red_shine"],
                                   (cx + pt_offset[0], cy + pt_offset[1]), size - 1)
        # Red fill
        for pt_offset in [(-2, 0), (0, -1), (2, -1), (2, 1), (0, 1)]:
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["red_dark"],
                                   (cx + pt_offset[0], cy + pt_offset[1]), size - 2)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["red_mid"], (cx, cy), size - 2)

    def _draw_torso(surface, cx, cy, facing, phase):
        """Akatsuki black cloak with high collar and red clouds."""
        # Torso shape (cloak with wide collar)
        torso = [
            (cx - 10, cy - 6),
            (cx - 11, cy),
            (cx - 10, cy + 10),
            (cx - 7, cy + 20),
            (cx + 7, cy + 20),
            (cx + 10, cy + 10),
            (cx + 11, cy),
            (cx + 10, cy - 6),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in torso])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_darkest"], torso)

        # Inner shading
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_dark"], [
            (cx - 9, cy - 5),
            (cx - 10, cy + 1),
            (cx - 9, cy + 9),
            (cx - 6, cy + 18),
            (cx + 6, cy + 18),
            (cx + 9, cy + 9),
            (cx + 10, cy + 1),
            (cx + 9, cy - 5),
            (cx + 5, cy - 7),
            (cx - 5, cy - 7),
        ])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_mid"], [
            (cx - 6, cy - 3),
            (cx - 7, cy + 3),
            (cx - 6, cy + 12),
            (cx - 3, cy + 16),
            (cx + 3, cy + 16),
            (cx + 6, cy + 12),
            (cx + 7, cy + 3),
            (cx + 6, cy - 3),
        ])

        # HIGH COLLAR (Akatsuki style - stands up around neck)
        collar_pts = [
            (cx - 7, cy - 8),
            (cx - 9, cy - 14),
            (cx - 7, cy - 16),
            (cx - 3, cy - 15),
            (cx + 3, cy - 15),
            (cx + 7, cy - 16),
            (cx + 9, cy - 14),
            (cx + 7, cy - 8),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_darkest"], collar_pts)
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["cloak_dark"], [
            (cx - 6, cy - 8),
            (cx - 8, cy - 13),
            (cx - 6, cy - 15),
            (cx + 6, cy - 15),
            (cx + 8, cy - 13),
            (cx + 6, cy - 8),
        ])
        # Collar edge highlight
        _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["cloak_mid"],
                            (cx - 6, cy - 14), (cx + 6, cy - 14), 1)

        # V opening at collar (dark shadow)
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"], [
            (cx - 3, cy - 8),
            (cx, cy - 4),
            (cx + 3, cy - 8),
            (cx + 2, cy - 9),
            (cx - 2, cy - 9),
        ])

        # RED CLOUDS on cloak (front visible)
        _NS_kazuren._draw_akatsuki_cloud(surface, cx - 4, cy + 6, 4)
        _NS_kazuren._draw_akatsuki_cloud(surface, cx + 5, cy + 13, 3)

        # Red inner lining hint at bottom
        pygame.draw.line(surface, _NS_kazuren.PALETTE["red_dark"],
                         (cx - 7, cy + 20), (cx + 7, cy + 20), 1)

    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms in black cloak sleeves."""
        back_arm_x = cx - facing * 6
        front_arm_x = cx + facing * 6

        if action == "attack":
            if attack_progress < 0.5:
                t = attack_progress / 0.5
                # Front arm rises (pointing/casting)
                elbow_fx = front_arm_x + facing * 2
                elbow_fy = cy + 3 - int(t * 4)
                hand_fx = cx + facing * (8 + int(t * 4))
                hand_fy = cy - 2 - int(t * 4)
                # Back arm lower
                elbow_bx = back_arm_x + facing * 1
                elbow_by = cy + 6
                hand_bx = back_arm_x + facing * 1
                hand_by = cy + 12
            else:
                t = (attack_progress - 0.5) / 0.5
                # Extend forward
                elbow_fx = front_arm_x + facing * (2 + int(t * 4))
                elbow_fy = cy - 1
                hand_fx = cx + facing * (12 + int(t * 6))
                hand_fy = cy - 6 + int(t * 3)
                elbow_bx = back_arm_x + facing * 0
                elbow_by = cy + 6
                hand_bx = back_arm_x - facing * 1
                hand_by = cy + 12
        elif action == "walk":
            swing = math.sin(phase * 1.5) * 2
            elbow_fx = front_arm_x + facing * 1
            elbow_fy = cy + 6 + int(swing)
            hand_fx = front_arm_x + facing * 2
            hand_fy = cy + 12 + int(swing)
            elbow_bx = back_arm_x - facing * 1
            elbow_by = cy + 6 - int(swing)
            hand_bx = back_arm_x - facing * 2
            hand_by = cy + 12 - int(swing)
        else:  # idle
            breath = math.sin(phase * 0.6) * 1
            elbow_fx = front_arm_x + facing * 1
            elbow_fy = cy + 6 + int(breath)
            hand_fx = front_arm_x + facing * 2
            hand_fy = cy + 13 + int(breath)
            elbow_bx = back_arm_x - facing * 1
            elbow_by = cy + 6
            hand_bx = back_arm_x - facing * 2
            hand_by = cy + 13

        _NS_kazuren._draw_single_arm(surface,
                                      (back_arm_x, cy - 2),
                                      (elbow_bx, elbow_by),
                                      (hand_bx, hand_by), back=True)
        _NS_kazuren._draw_single_arm(surface,
                                      (front_arm_x, cy - 2),
                                      (elbow_fx, elbow_fy),
                                      (hand_fx, hand_fy), back=False)

    def _draw_single_arm(surface, shoulder, elbow, hand, back=False):
        """Arm with cloak sleeve."""
        _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["shadow_deep"],
                            (shoulder[0] + 2, shoulder[1] + 2),
                            (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["shadow_deep"],
                            (elbow[0] + 2, elbow[1] + 2),
                            (hand[0] + 2, hand[1] + 2), 5)

        cloak_dark = _NS_kazuren.PALETTE["cloak_darkest" if back else "cloak_dark"]
        cloak_mid = _NS_kazuren.PALETTE["cloak_dark" if back else "cloak_mid"]

        # Upper arm (sleeve)
        _NS_kazuren._aaline(surface, cloak_dark, shoulder, elbow, 6)
        _NS_kazuren._aaline(surface, cloak_mid, shoulder, elbow, 4)
        # Forearm (sleeve)
        _NS_kazuren._aaline(surface, cloak_dark, elbow, hand, 5)
        _NS_kazuren._aaline(surface, cloak_mid, elbow, hand, 3)

        # Sleeve cuff (slight red line)
        cuff_dx = (hand[0] - elbow[0]) / max(1, math.hypot(hand[0] - elbow[0], hand[1] - elbow[1]))
        cuff_dy = (hand[1] - elbow[1]) / max(1, math.hypot(hand[0] - elbow[0], hand[1] - elbow[1]))
        cuff_x = hand[0] - int(cuff_dx * 3)
        cuff_y = hand[1] - int(cuff_dy * 3)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["red_dark"], (cuff_x, cuff_y), 2)

        # Hand (skin visible from sleeve)
        skin_dark = _NS_kazuren.PALETTE["skin_darkest" if back else "skin_dark"]
        skin_mid = _NS_kazuren.PALETTE["skin_dark" if back else "skin_mid"]
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["shadow_deep"],
                               (hand[0] + 1, hand[1] + 1), 3)
        _NS_kazuren._aacircle(surface, skin_dark, hand, 3)
        _NS_kazuren._aacircle(surface, skin_mid, hand, 2)
        pygame.draw.rect(surface, _NS_kazuren.PALETTE["skin_light"],
                         (hand[0] - 1, hand[1] - 1, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, rinnegan_mode):
        """Spiky hair + orange spiral mask with Sharingan eyehole."""
        # HAIR SPIKES (behind mask)
        _NS_kazuren._draw_hair_spikes(surface, cx, cy, facing, phase)

        # MASK (Tobi orange spiral mask)
        _NS_kazuren._draw_mask(surface, cx, cy, facing, phase, rinnegan_mode)

    def _draw_hair_spikes(surface, cx, cy, facing, phase):
        """Wild spiky dark hair around/behind mask."""
        # Back hair mass
        back_shape = [
            (cx - 10, cy - 4),
            (cx - 13, cy + 2),
            (cx - 14, cy + 10),
            (cx - 11, cy + 16),
            (cx - 5, cy + 18),
            (cx, cy + 16),
            (cx - 2, cy + 4),
            (cx - 4, cy - 4),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in back_shape])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["hair_darkest"], back_shape)
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["hair_dark"], [
            (cx - 9, cy - 3),
            (cx - 12, cy + 3),
            (cx - 12, cy + 12),
            (cx - 8, cy + 15),
            (cx - 3, cy + 14),
            (cx - 3, cy + 4),
        ])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["hair_mid"], [
            (cx - 10, cy + 4),
            (cx - 10, cy + 10),
            (cx - 6, cy + 12),
            (cx - 5, cy + 6),
        ])

        # Spiky tips on top
        spike_positions = [
            (cx - 10, cy - 8, cx - 6, cy - 4),
            (cx - 5, cy - 10, cx - 2, cy - 4),
            (cx - 1, cy - 11, cx + 2, cy - 4),
            (cx + 3, cy - 10, cx + 5, cy - 4),
            (cx + 6, cy - 8, cx + 8, cy - 4),
            # Side spikes
            (cx - 14, cy + 2, cx - 12, cy + 6),
            (cx - 14, cy + 10, cx - 11, cy + 14),
        ]
        for pts in spike_positions:
            tx1, ty1, tx2, ty2 = pts
            # Shadow
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"], [
                (tx1 + 1, ty1 + 1),
                (tx2 - 1, ty2 + 1),
                (tx2 + 1, ty2 + 1),
            ])
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["hair_darkest"], [
                (tx1, ty1),
                (tx2 - 2, ty2),
                (tx2 + 2, ty2),
            ])
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["hair_dark"], [
                (tx1, ty1 + 1),
                (tx2 - 1, ty2),
                (tx2 + 1, ty2),
            ])

    def _draw_mask(surface, cx, cy, facing, phase, rinnegan_mode):
        """Orange spiral mask with single Sharingan eyehole."""
        # Mask shape (oval, tilted for profile-view)
        mask_shape = [
            (cx - 8, cy - 3),
            (cx - 9, cy + 2),
            (cx - 7, cy + 8),
            (cx - 2, cy + 11),
            (cx + 4, cy + 11),
            (cx + 8 + facing, cy + 8),
            (cx + 9 + facing, cy + 2),
            (cx + 8, cy - 3),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ]
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in mask_shape])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["mask_darkest"], mask_shape)

        # Mid orange
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["mask_dark"], [
            (cx - 7, cy - 2),
            (cx - 8, cy + 2),
            (cx - 6, cy + 7),
            (cx - 2, cy + 10),
            (cx + 4, cy + 10),
            (cx + 7 + facing, cy + 7),
            (cx + 8 + facing, cy + 2),
            (cx + 7, cy - 2),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["mask_mid"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 4, cy + 8),
            (cx + 3, cy + 8),
            (cx + 6 + facing, cy + 5),
            (cx + 6, cy - 1),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])

        # SPIRAL PATTERN on mask (concentric arcs converging to eye)
        # Center of spiral is at the eye hole
        eye_x = cx + facing * 2
        eye_y = cy + 2

        # Draw spiral rings (partial arcs)
        for ring_r in [3, 5, 7]:
            for i in range(8):
                angle_start = i * math.pi / 4 + phase * 0.02
                sx = eye_x + int(math.cos(angle_start) * ring_r)
                sy = eye_y + int(math.sin(angle_start) * ring_r * 0.9)
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["mask_darkest"],
                                 (sx, sy, 1, 1))

        # Highlight streak on mask (top-left shine)
        _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["mask_light"], [
            (cx - 3, cy - 3),
            (cx, cy - 4),
            (cx + 1, cy - 2),
            (cx - 2, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_kazuren.PALETTE["mask_shine"], (cx - 1, cy - 3, 2, 1))

        # SHARINGAN EYE HOLE
        _NS_kazuren._draw_sharingan_eye(surface, eye_x, eye_y, facing, phase, rinnegan_mode)

    def _draw_sharingan_eye(surface, ex, ey, facing, phase, rinnegan_mode):
        """Bright red Sharingan eye with tomoe / Rinnegan pattern."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Deep socket
        pygame.draw.rect(surface, _NS_kazuren.PALETTE["shadow_deep"],
                         (ex - 3, ey - 2, 6, 5))

        if rinnegan_mode:
            # RINNEGAN - purple with concentric rings
            for r in range(6, 0, -1):
                alpha = _NS_kazuren._alpha(90 * (6 - r) / 6 * pulse)
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["rin_light"], alpha), (ex, ey), r)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["rin_darkest"], (ex, ey), 3)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["rin_dark"], (ex, ey), 2)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["rin_mid"], (ex, ey), 1)
            # Ring pattern
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["rin_dark"], (ex - 3, ey, 7, 1))
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["rin_dark"], (ex, ey - 3, 1, 7))
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["shadow"], (ex, ey, 1, 1))
        else:
            # SHARINGAN - red with tomoe
            for r in range(6, 0, -1):
                alpha = _NS_kazuren._alpha(100 * (6 - r) / 6 * pulse)
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["sharingan_mid"], alpha),
                                       (ex, ey), r)

            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["sharingan_darkest"], (ex, ey), 3)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["sharingan_dark"], (ex, ey), 2)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["sharingan_mid"], (ex, ey), 2)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["sharingan_light"], (ex + facing, ey), 1)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["sharingan_glow"], (ex + facing, ey), 1)

            # Central black pupil
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["shadow"], (ex, ey, 1, 1))

            # 3 tomoe marks (rotating around pupil)
            for i in range(3):
                angle = phase * 0.5 + i * (math.pi * 2 / 3)
                tx = ex + int(math.cos(angle) * 2)
                ty = ey + int(math.sin(angle) * 2)
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["shadow"], (tx, ty, 1, 1))

    # ============================================================
    # BASIC ATTACK - Small Fire Ball projectile from Sharingan
    # ============================================================
    def _draw_basic_fireball(surface, boss, x, y, progress):
        facing = boss.direction
        # Fire forms at extended hand
        hx = x + facing * (14 + int(progress * 6))
        hy = y - 2

        if progress < 0.45:
            # PHASE 1: Charge fire in hand
            t = progress / 0.45
            r = int(3 + t * 4)

            for radius in range(r + 4, 0, -1):
                alpha = _NS_kazuren._alpha(180 * (r + 4 - radius) / (r + 4))
                _NS_kazuren._aacircle(surface,
                                       (*_NS_kazuren.PALETTE["fire_dark"], alpha),
                                       (hx, hy), radius)

            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_darkest"], (hx, hy), r + 1)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_dark"], (hx, hy), r)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_mid"], (hx, hy), max(1, r - 1))
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_light"], (hx, hy), max(1, r - 2))
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_hot"], (hx, hy), max(1, r - 3))
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["fire_shine"], (hx, hy, 1, 1))

            # Flickering flames around
            for i in range(6):
                angle = boss.pulse * 6 + i * math.pi / 3
                sx = hx + int(math.cos(angle) * (r + 2))
                sy = hy + int(math.sin(angle) * (r + 2))
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["fire_hot"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["fire_shine"], (sx, sy, 1, 1))
            return

        # PHASE 2: Projectile
        tx, ty = _NS_kazuren._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 2

        t = (progress - 0.45) / 0.55
        t = max(0.0, min(1.0, t))
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Fire comet trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_kazuren._alpha(230 - i * 25)
            size = max(1, 7 - i)
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_darkest"], alpha),
                                   (px, py), size)
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_dark"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_mid"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                   (px, py), max(1, size - 3))

            if i < 4:
                for s in range(2):
                    angle_s = boss.pulse * 5 + i + s * 2
                    spark_x = px + int(math.cos(angle_s) * (size + 1))
                    spark_y = py + int(math.sin(angle_s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_kazuren.PALETTE["fire_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright fireball head
        for r in range(11, 3, -2):
            alpha = _NS_kazuren._alpha(100 * (11 - r) / 11)
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                   (bx, by), r)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_darkest"], (bx, by), 7)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_dark"], (bx, by), 6)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_mid"], (bx, by), 4)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_light"], (bx, by), 2)
        _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_kazuren.PALETTE["white"], (bx, by, 1, 1))

        # Flame tips
        for i in range(4):
            angle = boss.pulse * 4 + i * math.pi / 2
            fx = bx + int(math.cos(angle) * 6)
            fy = by + int(math.sin(angle) * 6)
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["fire_hot"], (fx, fy, 1, 1))

        # Impact
        if t > 0.85:
            st = (t - 0.85) / 0.15
            radius = int(8 + st * 20)
            alpha = _NS_kazuren._alpha(240 * (1 - st))
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_dark"], alpha),
                                   (tx, ty), radius, 2)
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_mid"], alpha),
                                   (tx, ty), max(1, radius - 5), 2)
            _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                   (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 26), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius, 90 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 3, 5, 180), (5, 7, 100, 12))
        surface.blit(shadow, (x - 55, y - 13))

    def _draw_rinnegan_aura(surface, x, y, phase):
        """Purple Rinnegan aura around boss."""
        pulse = math.sin(phase * 0.6) * 0.3 + 0.7
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_kazuren._alpha((90 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kazuren._aacircle(aura, (*_NS_kazuren.PALETTE["kamui_darkest"], alpha),
                                       (100, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_kazuren._alpha((55 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_kazuren._aacircle(aura, (*_NS_kazuren.PALETTE["kamui_dark"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))

        # Floating purple particles
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 40 + int(math.sin(phase * 2 + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5) - 5
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["kamui_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["kamui_hot"], (sx, sy, 1, 1))

    def _draw_ground_seal(surface, x, y, phase, skill):
        """Ground seal circle beneath boss."""
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        ring = pygame.Surface((140, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kazuren.PALETTE["cloak_dark"], 200),
                            (5, 14, 130, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_kazuren.PALETTE["red_dark"], 200),
                            (14, 16, 112, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_kazuren.PALETTE["kamui_dark"], 180),
                            (30, 18, 80, 14), 1)

        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 70 + int(math.cos(angle) * 40)
            y1 = 24 + int(math.sin(angle) * 8)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 24 + int(math.sin(angle) * 11)
            color = _NS_kazuren.PALETTE["red_mid"] if i % 2 == 0 else _NS_kazuren.PALETTE["kamui_mid"]
            pygame.draw.line(ring, (*color, 220), (x1, y1), (x2, y2), 1)

        if skill:
            color = _NS_kazuren.PALETTE["kamui_hot"] if skill in ("w", "r") \
                else _NS_kazuren.PALETTE["fire_hot"] if skill == "q" \
                else _NS_kazuren.PALETTE["wood_light"]
            pygame.draw.ellipse(ring, (*color, _NS_kazuren._alpha(180 * pulse)),
                                (12, 10, 116, 30), 1)
        surface.blit(ring, (x - 70, y - 21))

    # ============================================================
    # SKILL Q - FIRE STYLE: BOMB BLAST
    # ============================================================
    def _draw_fire_bomb_skill(surface, boss, x, y, timer, phase):
        """Massive fire bomb projectile that explodes on impact."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kazuren._target_position(boss, x, y)

        if progress < 0.3:
            # Charge huge fire in hand
            t = progress / 0.3
            cx = x + facing * 18
            cy = y - 2
            cr = int(6 + t * 12)

            # Outer glow
            for r in range(cr + 8, 0, -2):
                alpha = _NS_kazuren._alpha(180 * (cr + 8 - r) / (cr + 8))
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_dark"], alpha),
                                       (cx, cy), r)

            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_darkest"], (cx, cy), cr + 1)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_dark"], (cx, cy), cr)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_mid"], (cx, cy), cr - 3)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_light"], (cx, cy), max(1, cr - 6))
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_hot"], (cx, cy), max(1, cr - 9))
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["white"], (cx, cy, 1, 1))

            # Fire tendrils spiraling
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                for r_step in (cr - 1, cr + 2):
                    sx = cx + int(math.cos(angle) * r_step)
                    sy = cy + int(math.sin(angle) * r_step)
                    pygame.draw.rect(surface, _NS_kazuren.PALETTE["fire_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 26
            start_y = y - 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long fiery trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kazuren._alpha(240 - i * 20)
                size = max(1, 10 - i)

                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_darkest"], alpha),
                                       (px, py), size)
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_mid"], alpha),
                                       (px, py), max(1, size - 3))
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                       (px, py), max(1, size - 5))

                # Trail sparks
                if i < 6:
                    for s in range(3):
                        angle_s = phase * 4 + i + s * 2
                        spark_x = px + int(math.cos(angle_s) * (size + 2))
                        spark_y = py + int(math.sin(angle_s) * (size + 2))
                        pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["fire_hot"], alpha),
                                         (spark_x, spark_y, 2, 2))
                        pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["fire_shine"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Bright bomb head
            for r in range(15, 3, -2):
                alpha = _NS_kazuren._alpha(100 * (15 - r) / 15)
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                       (bx, by), r)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_darkest"], (bx, by), 12)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_dark"], (bx, by), 10)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_mid"], (bx, by), 7)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_light"], (bx, by), 4)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_hot"], (bx, by), 2)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["fire_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["white"], (bx, by, 1, 1))

            # Massive explosion
            if t > 0.82:
                st = (t - 0.82) / 0.18
                radius = int(15 + st * 40)
                alpha = _NS_kazuren._alpha(240 * (1 - st))

                # Concentric explosion rings
                for i in range(4):
                    r_ring = radius - i * 10
                    if r_ring > 0:
                        _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_darkest"], alpha),
                                               (tx, ty), r_ring + 3, 3)
                        _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_dark"], alpha),
                                               (tx, ty), r_ring, 3)
                        _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_mid"], alpha),
                                               (tx, ty), max(1, r_ring - 5), 2)
                        _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                               (tx, ty), max(1, r_ring - 10), 1)

                # Radial burst
                for i in range(16):
                    angle_s = i * math.pi / 8
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_kazuren.PALETTE["fire_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["fire_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["fire_shine"], alpha),
                                     (ex, ey, 1, 1))

    # ============================================================
    # SKILL W - PHASE SHIFT (Kamui dimension shift)
    # ============================================================
    def _draw_phase_shift_fx(surface, boss, x, y, timer, phase):
        """Purple swirling vortex around boss during phase."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Purple vortex particles spiraling around boss
        for i in range(20):
            angle = phase * 4 + i * math.pi / 10
            radius = 15 + int(math.sin(phase * 3 + i) * 8) + int(progress * 20)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.7) - 5
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["kamui_darkest"], (sx, sy), 3)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["kamui_dark"], (sx, sy), 2)
            _NS_kazuren._aacircle(surface, _NS_kazuren.PALETTE["kamui_mid"], (sx, sy), 1)
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["kamui_hot"], (sx, sy, 1, 1))

        # Central vortex swirl
        if 0.3 < progress < 0.7:
            for r in range(20, 2, -3):
                angle_offset = phase * 6
                for i in range(6):
                    angle = angle_offset + i * math.pi / 3
                    sx = x + int(math.cos(angle) * r)
                    sy = y + int(math.sin(angle) * r * 0.6) - 5
                    alpha = _NS_kazuren._alpha(200 * (20 - r) / 20)
                    pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["kamui_light"], alpha),
                                     (sx, sy, 2, 2))

        # Space distortion lines
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r1 = 8
            r2 = 25 + int(math.sin(phase * 3 + i) * 5)
            sx = x + int(math.cos(angle) * r1)
            sy = y + int(math.sin(angle) * r1 * 0.6) - 5
            ex = x + int(math.cos(angle) * r2)
            ey = y + int(math.sin(angle) * r2 * 0.6) - 5
            _NS_kazuren._aaline(surface, _NS_kazuren.PALETTE["kamui_mid"], (sx, sy), (ex, ey), 1)
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["kamui_hot"], (ex, ey, 1, 1))

    # ============================================================
    # SKILL E - WOOD STYLE: NEEDLE JUTSU
    # ============================================================
    def _draw_wood_needles_ground(surface, boss, x, y, timer, phase):
        """Ground crack/growth base."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground cracks in front of boss
        base_x = x + facing * 30
        base_y = y + 42

        if progress < 0.2:
            # Cracks appear
            t = progress / 0.2
            for i in range(6):
                cx = base_x + int((i - 2.5) * 15)
                crack_len = int(t * 15)
                pygame.draw.line(surface, (*_NS_kazuren.PALETTE["shadow_deep"], 220),
                                 (cx, base_y),
                                 (cx + int(math.cos(i) * crack_len),
                                  base_y - int(math.sin(i) * crack_len)), 2)

        # Persistent ground line
        pygame.draw.line(surface, _NS_kazuren.PALETTE["wood_darkest"],
                         (base_x - 60, base_y), (base_x + 60, base_y), 2)
        pygame.draw.line(surface, _NS_kazuren.PALETTE["wood_dark"],
                         (base_x - 60, base_y + 1), (base_x + 60, base_y + 1), 1)

    def _draw_wood_needles_skill(surface, boss, x, y, timer, phase):
        """Multiple wood needles erupt from ground in front of boss."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        base_x = x + facing * 30
        base_y = y + 40

        # Grow needles based on progress
        if progress < 0.5:
            t = progress / 0.5
            growth = t
        else:
            t = (progress - 0.5) / 0.5
            growth = 1.0 - t * 0.3  # slowly retract

        # Draw many needles in row
        for i in range(9):
            needle_x = base_x + int((i - 4) * 12)
            offset_delay = i * 0.05
            local_growth = max(0.0, min(1.0, growth - offset_delay))
            needle_h = int(local_growth * (30 + math.sin(i * 1.5) * 8))

            if needle_h < 2:
                continue

            needle_top_y = base_y - needle_h

            # Needle shape - triangular spike
            width_bot = 4
            width_top = 1

            # Shadow
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["shadow_deep"], [
                (needle_x - width_bot + 1, base_y + 1),
                (needle_x + width_top + 1, needle_top_y + 1),
                (needle_x + width_bot + 1, base_y + 1),
            ])
            # Dark base
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["wood_darkest"], [
                (needle_x - width_bot, base_y),
                (needle_x + width_top, needle_top_y),
                (needle_x + width_bot, base_y),
            ])
            # Mid wood
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["wood_dark"], [
                (needle_x - width_bot + 1, base_y),
                (needle_x, needle_top_y),
                (needle_x + width_bot - 1, base_y),
            ])
            # Highlight
            _NS_kazuren._poly(surface, _NS_kazuren.PALETTE["wood_mid"], [
                (needle_x - 1, base_y - 2),
                (needle_x, needle_top_y),
                (needle_x + 1, base_y - 2),
            ])
            # Bright tip
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["wood_light"],
                             (needle_x, needle_top_y, 1, 3))
            pygame.draw.rect(surface, _NS_kazuren.PALETTE["wood_shine"],
                             (needle_x, needle_top_y, 1, 1))

            # Wood texture lines
            for tex_y in range(needle_top_y + 3, base_y, 4):
                tex_ratio = (tex_y - needle_top_y) / needle_h
                tex_w = int(width_top + (width_bot - width_top) * tex_ratio)
                pygame.draw.line(surface, _NS_kazuren.PALETTE["wood_darkest"],
                                 (needle_x - tex_w, tex_y),
                                 (needle_x + tex_w, tex_y), 1)

        # Dust/debris at base
        for i in range(15):
            angle = phase + i * math.pi / 7
            r = int(math.sin(phase * 2 + i) * 8) + 20
            dx = base_x + int(math.cos(angle) * r)
            dy = base_y + int(math.sin(angle) * 3)
            alpha = _NS_kazuren._alpha(180 * (1 - abs(math.sin(phase + i))))
            pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["wood_dark"], alpha),
                             (dx, dy, 2, 2))

    # ============================================================
    # SKILL R - RINNEGAN: DIMENSION REALITY (portal/black hole)
    # ============================================================
    def _draw_dimension_portal_ground(surface, boss, x, y, timer, phase):
        """Huge purple black hole portal at target."""
        tx, ty = _NS_kazuren._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Portal opening
            t = progress / 0.3
            r = int(t * 45)
            alpha = _NS_kazuren._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_kazuren.PALETTE["kamui_darkest"], alpha),
                                (tx - r, ty - r // 2, r * 2, r))
            pygame.draw.ellipse(surface, (*_NS_kazuren.PALETTE["kamui_dark"], alpha),
                                (tx - r + 3, ty - r // 2 + 2, r * 2 - 6, r - 4))
        else:
            # Fully open black hole
            t = (progress - 0.3) / 0.7
            r = int(45 + math.sin(phase * 2) * 5)
            alpha_fade = _NS_kazuren._alpha(220 * (1 - t * 0.3))

            # Outer dark ring
            pygame.draw.ellipse(surface, (*_NS_kazuren.PALETTE["shadow"], alpha_fade),
                                (tx - r - 2, ty - r // 2 - 2, r * 2 + 4, r + 4))
            pygame.draw.ellipse(surface, (*_NS_kazuren.PALETTE["kamui_darkest"], alpha_fade),
                                (tx - r, ty - r // 2, r * 2, r))
            pygame.draw.ellipse(surface, (*_NS_kazuren.PALETTE["kamui_dark"], alpha_fade),
                                (tx - r + 4, ty - r // 2 + 2, r * 2 - 8, r - 4))
            # Center dark abyss
            pygame.draw.ellipse(surface, (*_NS_kazuren.PALETTE["shadow"], alpha_fade),
                                (tx - r // 3, ty - r // 6, r * 2 // 3, r // 3))

    def _draw_dimension_portal_skill(surface, boss, x, y, timer, phase):
        """Rings, particles being sucked into portal."""
        tx, ty = _NS_kazuren._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Opening - swirls forming
            t = progress / 0.3
            for i in range(12):
                angle = phase * 5 + i * math.pi / 6
                r = 60 - int(t * 40)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                alpha = _NS_kazuren._alpha(200 * t)
                _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["kamui_light"], alpha),
                                       (sx, sy), 3)
                pygame.draw.rect(surface, _NS_kazuren.PALETTE["kamui_hot"], (sx, sy, 1, 1))
            return

        # Fully active
        t = (progress - 0.3) / 0.7
        alpha_fade = _NS_kazuren._alpha(240 * (1 - t * 0.5))

        # Multiple spiraling rings inside portal
        for ring_i in range(4):
            base_r = 40 - ring_i * 8
            ring_wobble = int(math.sin(phase * 2 + ring_i) * 3)
            r = base_r + ring_wobble
            if r < 3:
                continue

            for i in range(16):
                angle = phase * (4 + ring_i * 2) + i * math.pi / 8
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                color = [_NS_kazuren.PALETTE["kamui_light"],
                         _NS_kazuren.PALETTE["kamui_mid"],
                         _NS_kazuren.PALETTE["kamui_hot"],
                         _NS_kazuren.PALETTE["kamui_shine"]][ring_i]
                pygame.draw.rect(surface, (*color, alpha_fade), (sx, sy, 2, 2))

        # Debris being pulled in from outside
        for i in range(20):
            debris_angle = phase * 0.5 + i * math.pi / 10
            # Distance shrinks over time (being sucked in)
            debris_t = ((phase * 0.4 + i * 0.13) % 1.0)
            outer_r = 80
            inner_r = 20
            debris_r = int(outer_r - debris_t * (outer_r - inner_r))
            dx = tx + int(math.cos(debris_angle) * debris_r)
            dy = ty + int(math.sin(debris_angle) * debris_r * 0.5)
            alpha = _NS_kazuren._alpha(240 * debris_t)
            # Debris rocks/particles
            pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["kamui_darkest"], alpha),
                             (dx, dy, 3, 2))
            pygame.draw.rect(surface, (*_NS_kazuren.PALETTE["kamui_dark"], alpha),
                             (dx, dy, 2, 1))

        # Gravity lines pulling toward center
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            r_out = 55
            r_in = 30
            sx = tx + int(math.cos(angle) * r_out)
            sy = ty + int(math.sin(angle) * r_out * 0.5)
            ex = tx + int(math.cos(angle) * r_in)
            ey = ty + int(math.sin(angle) * r_in * 0.5)
            _NS_kazuren._aaline(surface, (*_NS_kazuren.PALETTE["kamui_hot"], alpha_fade),
                                (sx, sy), (ex, ey), 1)

        # Bright core
        core_pulse = math.sin(phase * 3) * 0.3 + 0.7
        _NS_kazuren._aacircle(surface, (*_NS_kazuren.PALETTE["kamui_shine"],
                                         _NS_kazuren._alpha(180 * core_pulse)),
                               (tx, ty), 3)
        pygame.draw.rect(surface, _NS_kazuren.PALETTE["white"], (tx, ty, 1, 1))


# ====================================================================================================
# TSUKIYORA - TRUE BOSS
# ====================================================================================================

class _NS_tsukiyora:
    """Namespace tsukiyora - Moon-Born Sovereign goddess mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # White-silver hair (long flowing)
        "hair_darkest": (90, 85, 100),
        "hair_dark": (150, 145, 160),
        "hair_mid": (205, 200, 215),
        "hair_light": (235, 232, 245),
        "hair_shine": (255, 253, 255),

        # Pale skin (porcelain white with cool undertones)
        "skin_darkest": (140, 120, 130),
        "skin_dark": (195, 175, 185),
        "skin_mid": (230, 215, 220),
        "skin_light": (250, 240, 240),
        "skin_shine": (255, 252, 250),

        # White kimono/robe
        "robe_darkest": (100, 95, 115),
        "robe_dark": (170, 165, 180),
        "robe_mid": (215, 210, 225),
        "robe_light": (240, 238, 248),
        "robe_shine": (255, 255, 255),

        # Purple/dark trim on kimono
        "trim_darkest": (25, 15, 40),
        "trim_dark": (60, 35, 95),
        "trim_mid": (110, 65, 155),
        "trim_light": (170, 120, 210),

        # Red third eye + forehead diamond (Rinne Sharingan)
        "third_eye_darkest": (40, 5, 10),
        "third_eye_dark": (110, 15, 25),
        "third_eye_mid": (200, 30, 40),
        "third_eye_light": (255, 90, 80),
        "third_eye_glow": (255, 200, 180),

        # Yellow-gold eyes (byakugan-like pale)
        "eye_dark": (150, 130, 60),
        "eye_mid": (210, 190, 100),
        "eye_light": (250, 235, 160),

        # Black chakra / truth seeker orb
        "void_darkest": (2, 0, 5),
        "void_dark": (12, 5, 20),
        "void_mid": (28, 15, 45),
        "void_light": (60, 35, 90),
        "void_shine": (110, 70, 160),

        # Purple cosmic energy
        "cosmic_darkest": (15, 5, 30),
        "cosmic_dark": (50, 20, 90),
        "cosmic_mid": (115, 55, 180),
        "cosmic_light": (180, 120, 235),
        "cosmic_hot": (220, 170, 255),
        "cosmic_shine": (245, 225, 255),

        # Blood red moon (Tsukuyomi)
        "moon_darkest": (40, 5, 10),
        "moon_dark": (110, 20, 25),
        "moon_mid": (185, 40, 45),
        "moon_light": (240, 90, 80),
        "moon_glow": (255, 170, 150),

        # Bone (skeletal weapons)
        "bone_darkest": (50, 45, 35),
        "bone_dark": (130, 120, 95),
        "bone_mid": (200, 190, 165),
        "bone_light": (240, 232, 210),
        "bone_shine": (255, 250, 235),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_tsukiyora._clamp(color)
        if _NS_tsukiyora.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_tsukiyora._clamp(color)
        if _NS_tsukiyora.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_tsukiyora._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_tsukiyora(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_tsukiyora._detect_moving(boss)
        _NS_tsukiyora._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_tk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient background
        _NS_tsukiyora._draw_shadow(surface, x, y + 46)
        _NS_tsukiyora._draw_cosmic_aura(surface, x, y, pulse, active_skill)
        _NS_tsukiyora._draw_ground_ring(surface, x, y + 42, pulse, active_skill)

        # D - Eternal Tsukuyomi red moon in background
        if active_skill == "d":
            _NS_tsukiyora._draw_blood_moon_bg(surface, boss, x, y, skill_timer, pulse)

        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_tsukiyora._draw_yomi_dimension_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_tsukiyora._draw_bones_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_tsukiyora._draw_tk_attack(surface, boss, x, y)
        elif moving:
            _NS_tsukiyora._draw_tk_walk(surface, boss, x, y)
        else:
            _NS_tsukiyora._draw_tk_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_tsukiyora._draw_truth_orb_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_tsukiyora._draw_yomi_dimension_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_tsukiyora._draw_bone_needles_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_tsukiyora._draw_bones_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_tsukiyora._draw_tsukuyomi_fx(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_tk_previous_timer", 0))
        active = bool(getattr(boss, "_tk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._tk_attack_active = True
            boss._tk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._tk_attack_frame = int(getattr(boss, "_tk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._tk_attack_active = False
            boss._tk_attack_frame = 0
            active = False

        boss._tk_previous_timer = timer
        boss._tk_attack_progress = (
            min(1.0, getattr(boss, "_tk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_tk_last_x"):
            boss._tk_last_x = boss.x
            boss._tk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._tk_last_x)
        dy = abs(boss.y - boss._tk_last_y)
        boss._tk_last_x = boss.x
        boss._tk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_tk_idle(surface, boss, x, y):
        # Floating goddess - subtle float
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_tsukiyora._draw_tk_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_tk_walk(surface, boss, x, y):
        phase = boss.pulse * 1.8
        bob = int(math.sin(phase * 1.5) * 3)
        sway = int(math.sin(phase * 0.8) * 2)
        _NS_tsukiyora._draw_tk_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk")

    def _draw_tk_attack(surface, boss, x, y):
        progress = getattr(boss, "_tk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Elegant hand cast (arms extend)
        if progress < 0.5:
            t = progress / 0.5
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 3)
        else:
            t = (progress - 0.5) / 0.5
            lunge = int(t * 4) * boss.direction
            lift = int(3 - t * 3)

        _NS_tsukiyora._draw_tk_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack",
                                     progress)

        # Basic ranged attack: dark chakra orb from hand
        _NS_tsukiyora._draw_basic_chakra_orb(surface, boss, x + lunge, y - lift,
                                              progress)

    # ============================================================
    # BODY - Tall Goddess (long kimono, horns, long hair)
    # ============================================================
    def _draw_tk_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Tall elegant goddess."""
        # Long trailing hair BEHIND everything
        _NS_tsukiyora._draw_hair_back(surface, cx, cy - 16, facing, phase)

        # Kimono skirt (bottom - covers legs, flowing)
        _NS_tsukiyora._draw_kimono_skirt(surface, cx, cy + 12, facing, phase)

        # Torso (kimono top)
        _NS_tsukiyora._draw_torso(surface, cx, cy - 2, facing, phase)

        # Arms with long sleeves
        _NS_tsukiyora._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)

        # Neck + head
        _NS_tsukiyora._draw_head(surface, cx, cy - 18, facing, phase)

    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long silver hair flowing down to the ground behind body."""
        sway = math.sin(phase * 0.4) * 2

        # Massive hair mass behind body (goes from head down past body to floor)
        hair_shape = [
            (cx - 12, cy + 2),
            (cx - 16, cy + 8),
            (cx - 20, cy + 18),
            (cx - 22 + int(sway), cy + 30),
            (cx - 20 + int(sway), cy + 44),
            (cx - 15 + int(sway), cy + 56),
            (cx - 6, cy + 60),
            (cx + 4, cy + 58),
            (cx + 10 - int(sway), cy + 52),
            (cx + 14 - int(sway), cy + 40),
            (cx + 14 - int(sway), cy + 26),
            (cx + 10, cy + 14),
            (cx + 6, cy + 6),
        ]
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in hair_shape])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_darkest"], hair_shape)

        # Dark layer
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_dark"], [
            (cx - 11, cy + 3),
            (cx - 15, cy + 10),
            (cx - 18, cy + 20),
            (cx - 20 + int(sway), cy + 30),
            (cx - 18 + int(sway), cy + 42),
            (cx - 14 + int(sway), cy + 52),
            (cx - 6, cy + 56),
            (cx + 3, cy + 54),
            (cx + 8 - int(sway), cy + 48),
            (cx + 12 - int(sway), cy + 38),
            (cx + 12 - int(sway), cy + 26),
            (cx + 9, cy + 14),
            (cx + 5, cy + 6),
        ])

        # Mid layer (streams of hair)
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_mid"], [
            (cx - 9, cy + 4),
            (cx - 12, cy + 12),
            (cx - 15, cy + 22),
            (cx - 16 + int(sway), cy + 32),
            (cx - 14 + int(sway), cy + 44),
            (cx - 10 + int(sway), cy + 50),
            (cx - 4, cy + 52),
            (cx + 2, cy + 50),
            (cx + 6 - int(sway), cy + 44),
            (cx + 8 - int(sway), cy + 34),
            (cx + 8 - int(sway), cy + 22),
            (cx + 6, cy + 12),
            (cx + 4, cy + 6),
        ])

        # Light strands (highlights)
        for strand_i in range(4):
            strand_x_base = cx + (strand_i - 1.5) * 5
            strand_offset_x = int(math.sin(phase * 0.3 + strand_i) * 2)
            strand_pts = [
                (strand_x_base + strand_offset_x, cy + 8),
                (strand_x_base + strand_offset_x - 1, cy + 24),
                (strand_x_base + strand_offset_x, cy + 40),
                (strand_x_base + strand_offset_x + 1, cy + 50),
            ]
            for i in range(len(strand_pts) - 1):
                _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["hair_light"],
                                       strand_pts[i], strand_pts[i + 1], 1)

        # Hair flowing side sweeps
        for i in range(3):
            side_x = cx - 14 - i * 2 + int(math.sin(phase * 0.4 + i) * 2)
            side_y1 = cy + 15 + i * 8
            side_y2 = side_y1 + 12
            _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["hair_light"],
                                   (side_x, side_y1), (side_x - 1, side_y2), 1)

    def _draw_kimono_skirt(surface, cx, cy, facing, phase):
        """Long white kimono skirt covering legs."""
        sway = math.sin(phase * 0.5) * 2

        # Skirt shape (widens toward bottom)
        skirt_shape = [
            (cx - 8, cy - 4),
            (cx - 10, cy + 4),
            (cx - 13, cy + 14),
            (cx - 16 + int(sway), cy + 26),
            (cx - 14 + int(sway), cy + 32),
            (cx + 14 - int(sway), cy + 32),
            (cx + 16 - int(sway), cy + 26),
            (cx + 13, cy + 14),
            (cx + 10, cy + 4),
            (cx + 8, cy - 4),
        ]
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in skirt_shape])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_darkest"], skirt_shape)

        # Mid layer
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx - 9, cy + 4),
            (cx - 12, cy + 14),
            (cx - 14 + int(sway), cy + 24),
            (cx - 12 + int(sway), cy + 30),
            (cx + 12 - int(sway), cy + 30),
            (cx + 14 - int(sway), cy + 24),
            (cx + 12, cy + 14),
            (cx + 9, cy + 4),
            (cx + 7, cy - 3),
        ])

        # Light layer (main visible)
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx - 7, cy + 4),
            (cx - 10, cy + 14),
            (cx - 11 + int(sway), cy + 22),
            (cx - 9 + int(sway), cy + 28),
            (cx + 9 - int(sway), cy + 28),
            (cx + 11 - int(sway), cy + 22),
            (cx + 10, cy + 14),
            (cx + 7, cy + 4),
            (cx + 5, cy - 2),
        ])

        # Front center panel highlight
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_light"], [
            (cx - 2, cy),
            (cx - 3, cy + 8),
            (cx - 4, cy + 18),
            (cx - 3, cy + 26),
            (cx + 3, cy + 26),
            (cx + 4, cy + 18),
            (cx + 3, cy + 8),
            (cx + 2, cy),
        ])

        # Purple trim at bottom hem
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["trim_darkest"],
                         (cx - 14 + int(sway), cy + 30),
                         (cx + 14 - int(sway), cy + 30), 2)
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["trim_mid"],
                         (cx - 13 + int(sway), cy + 30),
                         (cx + 13 - int(sway), cy + 30), 1)

        # Vertical purple stripes on skirt
        for stripe_x in (-6, 0, 6):
            pygame.draw.line(surface, _NS_tsukiyora.PALETTE["trim_dark"],
                             (cx + stripe_x, cy + 2),
                             (cx + stripe_x, cy + 28), 1)

        # Kimono buttons/decorations vertical
        for i, dy in enumerate((0, 8, 16, 24)):
            btn_y = cy + dy
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["trim_darkest"],
                                     (cx, btn_y), 2)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["trim_mid"],
                                     (cx, btn_y), 1)
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["trim_light"],
                             (cx, btn_y - 1, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Kimono top - white with V collar."""
        torso = [
            (cx - 8, cy - 4),
            (cx - 9, cy + 2),
            (cx - 8, cy + 12),
            (cx + 8, cy + 12),
            (cx + 9, cy + 2),
            (cx + 8, cy - 4),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ]
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in torso])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_darkest"], torso)

        # Kimono fold layer
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy + 2),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 8, cy + 2),
            (cx + 7, cy - 3),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx - 6, cy + 3),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 6, cy + 3),
            (cx + 5, cy - 2),
        ])

        # V-neck collar showing skin
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["skin_dark"], [
            (cx - 3, cy - 5),
            (cx, cy),
            (cx + 3, cy - 5),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["skin_mid"], [
            (cx - 2, cy - 4),
            (cx, cy - 1),
            (cx + 2, cy - 4),
        ])

        # Purple collar trim (edges of V)
        _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["trim_dark"],
                               (cx - 5, cy - 6), (cx, cy), 2)
        _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["trim_mid"],
                               (cx - 5, cy - 6), (cx, cy), 1)
        _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["trim_dark"],
                               (cx + 5, cy - 6), (cx, cy), 2)
        _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["trim_mid"],
                               (cx + 5, cy - 6), (cx, cy), 1)

        # Belt (obi)
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                         (cx - 8, cy + 10, 16, 4))
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["trim_darkest"],
                         (cx - 8, cy + 10, 16, 3))
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["trim_dark"],
                         (cx - 8, cy + 11, 16, 2))
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["trim_mid"],
                         (cx - 8, cy + 12, 16, 1))

        # Highlight sheen on chest
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["robe_light"],
                         (cx - 3, cy + 3, 1, 4))

    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Long-sleeved arms with wide kimono sleeves."""
        back_arm_x = cx - facing * 6
        front_arm_x = cx + facing * 6

        if action == "attack":
            if attack_progress < 0.5:
                t = attack_progress / 0.5
                # Elegant pose - both arms rise, palms out
                elbow_fx = front_arm_x + facing * 2
                elbow_fy = cy + 3 - int(t * 3)
                hand_fx = cx + facing * (8 + int(t * 4))
                hand_fy = cy - 2 - int(t * 4)
                elbow_bx = back_arm_x + facing * 1
                elbow_by = cy + 4 - int(t * 2)
                hand_bx = cx - facing * (4 + int(t * 2))
                hand_by = cy + 6 - int(t * 3)
            else:
                t = (attack_progress - 0.5) / 0.5
                # Front hand pushes forward with orb
                elbow_fx = front_arm_x + facing * (2 + int(t * 3))
                elbow_fy = cy - 1
                hand_fx = cx + facing * (12 + int(t * 6))
                hand_fy = cy - 6 + int(t * 3)
                elbow_bx = back_arm_x + facing * 1
                elbow_by = cy + 2
                hand_bx = cx - facing * 5
                hand_by = cy + 3
        elif action == "walk":
            swing = math.sin(phase * 1.4) * 2
            elbow_fx = front_arm_x + facing * 1
            elbow_fy = cy + 6 + int(swing)
            hand_fx = front_arm_x + facing * 2
            hand_fy = cy + 14 + int(swing)
            elbow_bx = back_arm_x - facing * 1
            elbow_by = cy + 6 - int(swing)
            hand_bx = back_arm_x - facing * 2
            hand_by = cy + 14 - int(swing)
        else:  # idle - elegant relaxed pose (hands slightly out)
            breath = math.sin(phase * 0.6) * 1
            elbow_fx = front_arm_x + facing * 2
            elbow_fy = cy + 6 + int(breath)
            hand_fx = front_arm_x + facing * 4
            hand_fy = cy + 14 + int(breath)
            elbow_bx = back_arm_x - facing * 2
            elbow_by = cy + 6
            hand_bx = back_arm_x - facing * 3
            hand_by = cy + 14

        # Draw back arm
        _NS_tsukiyora._draw_single_arm(surface,
                                         (back_arm_x, cy - 2),
                                         (elbow_bx, elbow_by),
                                         (hand_bx, hand_by), back=True)
        # Draw front arm
        _NS_tsukiyora._draw_single_arm(surface,
                                         (front_arm_x, cy - 2),
                                         (elbow_fx, elbow_fy),
                                         (hand_fx, hand_fy), back=False)

    def _draw_single_arm(surface, shoulder, elbow, hand, back=False):
        """Arm with long flowing white sleeve."""
        _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                               (shoulder[0] + 2, shoulder[1] + 2),
                               (elbow[0] + 2, elbow[1] + 2), 6)
        _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                               (elbow[0] + 2, elbow[1] + 2),
                               (hand[0] + 2, hand[1] + 2), 7)

        robe_dark = _NS_tsukiyora.PALETTE["robe_darkest" if back else "robe_dark"]
        robe_mid = _NS_tsukiyora.PALETTE["robe_dark" if back else "robe_mid"]
        robe_light = _NS_tsukiyora.PALETTE["robe_mid" if back else "robe_light"]

        # Upper arm (sleeve)
        _NS_tsukiyora._aaline(surface, robe_dark, shoulder, elbow, 6)
        _NS_tsukiyora._aaline(surface, robe_mid, shoulder, elbow, 4)

        # Wide flowing sleeve (bell-shape) toward hand
        # Draw sleeve as tapered
        _NS_tsukiyora._aaline(surface, robe_dark, elbow, hand, 8)
        _NS_tsukiyora._aaline(surface, robe_mid, elbow, hand, 6)
        _NS_tsukiyora._aaline(surface, robe_light, elbow, hand, 3)

        # Purple cuff at sleeve end
        cuff_r = 5
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["trim_darkest"],
                                 hand, cuff_r)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["trim_dark"],
                                 hand, cuff_r - 1)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["trim_mid"],
                                 hand, cuff_r - 2)

        # Hand (pale)
        skin_dark = _NS_tsukiyora.PALETTE["skin_darkest" if back else "skin_dark"]
        skin_mid = _NS_tsukiyora.PALETTE["skin_dark" if back else "skin_mid"]
        _NS_tsukiyora._aacircle(surface, skin_dark, (hand[0], hand[1] + 1), 3)
        _NS_tsukiyora._aacircle(surface, skin_mid, (hand[0], hand[1] + 1), 2)
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["skin_light"],
                         (hand[0], hand[1] + 1, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with rabbit horns, white hair with parted center, pale face."""
        # Neck
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                         (cx - 2, cy + 8, 4, 6))
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["skin_dark"],
                         (cx - 2, cy + 8, 3, 5))
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["skin_mid"],
                         (cx - 1, cy + 8, 2, 4))

        # Hair on head (top, parted)
        _NS_tsukiyora._draw_head_hair(surface, cx, cy, facing, phase)

        # RABBIT HORNS (two curved horns going up-back)
        _NS_tsukiyora._draw_horns(surface, cx, cy - 6, facing, phase)

        # FACE
        face_shape = [
            (cx - 5, cy - 2),
            (cx - 6, cy + 2),
            (cx - 4, cy + 6),
            (cx - 1, cy + 8),
            (cx + 3, cy + 8),
            (cx + 5 + facing, cy + 6),
            (cx + 6 + facing, cy + 2),
            (cx + 5, cy - 2),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in face_shape])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["skin_dark"], face_shape)
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["skin_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy + 2),
            (cx - 3, cy + 5),
            (cx, cy + 7),
            (cx + 3, cy + 7),
            (cx + 5 + facing, cy + 5),
            (cx + 5 + facing, cy + 2),
            (cx + 4, cy - 1),
            (cx, cy - 3),
        ])
        # Cheek highlight
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["skin_light"], [
            (cx - 2, cy),
            (cx, cy + 2),
            (cx + 2 + facing, cy + 3),
            (cx, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["skin_shine"],
                         (cx + facing * 2, cy + 2, 1, 1))

        # RED DIAMOND on forehead (Rinne-Sharingan third eye placeholder)
        _NS_tsukiyora._draw_forehead_diamond(surface, cx, cy - 2, phase)

        # EYES (pale gold Byakugan-like)
        _NS_tsukiyora._draw_eyes(surface, cx, cy + 2, facing, phase)

        # Lips (small dark)
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["third_eye_dark"],
                         (cx + facing * 2, cy + 6, 2, 1))

    def _draw_head_hair(surface, cx, cy, facing, phase):
        """Hair on top of head - parted in middle, framing face."""
        # Top hair mass
        top_hair = [
            (cx - 8, cy - 4),
            (cx - 9, cy - 1),
            (cx - 7, cy + 4),
            (cx - 4, cy),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 4, cy),
            (cx + 7, cy + 4),
            (cx + 9, cy - 1),
            (cx + 8, cy - 4),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in top_hair])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_darkest"], top_hair)
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy - 1),
            (cx - 6, cy + 3),
            (cx - 4, cy),
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 4, cy),
            (cx + 6, cy + 3),
            (cx + 8, cy - 1),
            (cx + 7, cy - 3),
            (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_mid"], [
            (cx - 5, cy - 2),
            (cx - 6, cy + 1),
            (cx - 3, cy + 2),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 3, cy + 2),
            (cx + 6, cy + 1),
            (cx + 5, cy - 2),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])

        # Light highlights
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["hair_light"], [
            (cx - 2, cy - 5),
            (cx, cy - 6),
            (cx + 2, cy - 5),
            (cx + 1, cy - 3),
            (cx - 1, cy - 3),
        ])

        # Side bangs
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["hair_mid"],
                         (cx - 7, cy - 3), (cx - 6, cy + 6), 2)
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["hair_light"],
                         (cx - 6, cy - 2), (cx - 6, cy + 5), 1)
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["hair_mid"],
                         (cx + 7, cy - 3), (cx + 6, cy + 6), 2)
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["hair_light"],
                         (cx + 6, cy - 2), (cx + 6, cy + 5), 1)

    def _draw_horns(surface, cx, cy, facing, phase):
        """Two curved rabbit-like horns pointing up-back."""
        for side_i, side in enumerate((-1, 1)):
            # Curved horn: base near head, curving upward-back
            base_x = cx + side * 4
            base_y = cy - 2
            mid_x = cx + side * 6
            mid_y = cy - 8
            tip_x = cx + side * 4
            tip_y = cy - 14

            # Horn segments
            prev = (base_x, base_y)
            for step in range(1, 6):
                t = step / 5
                # Bezier-style curve
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y)
                thickness = max(1, 6 - step)
                _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                                       (prev[0] + 1, prev[1] + 1),
                                       (bx + 1, by + 1), thickness + 1)
                _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["bone_darkest"],
                                       prev, (bx, by), thickness)
                _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["bone_dark"],
                                       prev, (bx, by), max(1, thickness - 1))
                _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["bone_mid"],
                                       (prev[0], prev[1] - 1), (bx, by - 1),
                                       max(1, thickness - 2))
                prev = (bx, by)

            # Tip highlight
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["bone_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["bone_shine"],
                             (tip_x, tip_y, 1, 1))

    def _draw_forehead_diamond(surface, cx, cy, phase):
        """Red diamond mark on forehead (represents third eye)."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Glow
        for r in range(4, 0, -1):
            alpha = _NS_tsukiyora._alpha(120 * (4 - r) / 4 * pulse)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["third_eye_glow"], alpha),
                                     (cx, cy), r)
        # Diamond shape
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["third_eye_darkest"], [
            (cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy),
        ])
        _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["third_eye_mid"], [
            (cx, cy - 1), (cx + 1, cy), (cx, cy + 1), (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["third_eye_light"], (cx, cy, 1, 1))

    def _draw_eyes(surface, cx, cy, facing, phase):
        """Pale golden Byakugan-like eyes (no pupil)."""
        for eye_x_off in (-3, 3):
            ex = cx + eye_x_off
            ey = cy

            # Socket
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 2))
            # Pale eye (no visible pupil - Byakugan style)
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["eye_dark"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 1))
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["eye_light"],
                             (ex, ey - 1, 1, 1))

        # Long dark eyelashes
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                         (cx - 4, cy - 2), (cx - 2, cy - 2), 1)
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                         (cx + 2, cy - 2), (cx + 4, cy - 2), 1)

    # ============================================================
    # BASIC ATTACK - Small dark chakra orb from hand
    # ============================================================
    def _draw_basic_chakra_orb(surface, boss, x, y, progress):
        facing = boss.direction
        hx = x + facing * (16 + int(progress * 6))
        hy = y - 6

        if progress < 0.45:
            # PHASE 1: Form dark chakra orb in hand
            t = progress / 0.45
            r = int(3 + t * 4)

            # Void glow
            for radius in range(r + 5, 0, -1):
                alpha = _NS_tsukiyora._alpha(180 * (r + 5 - radius) / (r + 5))
                _NS_tsukiyora._aacircle(surface,
                                         (*_NS_tsukiyora.PALETTE["void_light"], alpha),
                                         (hx, hy), radius)

            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_dark"], (hx, hy), r + 1)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_darkest"], (hx, hy), r)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_dark"], (hx, hy), max(1, r - 1))
            # Purple rim
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_mid"], (hx, hy), r, 1)

            # Cosmic sparkles around
            for i in range(6):
                angle = boss.pulse * 5 + i * math.pi / 3
                sx = hx + int(math.cos(angle) * (r + 3))
                sy = hy + int(math.sin(angle) * (r + 3))
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["cosmic_hot"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["cosmic_shine"], (sx, sy, 1, 1))
            return

        # PHASE 2: Fly to target
        tx, ty = _NS_tsukiyora._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 6

        t = (progress - 0.45) / 0.55
        t = max(0.0, min(1.0, t))
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Void trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_tsukiyora._alpha(220 - i * 25)
            size = max(1, 7 - i)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha),
                                     (px, py), size + 1)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["void_darkest"], alpha),
                                     (px, py), size)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["void_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_mid"], alpha),
                                     (px, py), size, 1)

            if i < 4:
                for s in range(2):
                    angle_s = boss.pulse * 5 + i + s * 2
                    spark_x = px + int(math.cos(angle_s) * (size + 1))
                    spark_y = py + int(math.sin(angle_s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_tsukiyora.PALETTE["cosmic_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright void orb head
        for r in range(11, 3, -2):
            alpha = _NS_tsukiyora._alpha(100 * (11 - r) / 11)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_light"], alpha),
                                     (bx, by), r)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_mid"], (bx, by), 7, 1)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_darkest"], (bx, by), 6)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_dark"], (bx, by), 4)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_dark"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["cosmic_hot"], (bx, by, 1, 1))

        # Impact
        if t > 0.85:
            st = (t - 0.85) / 0.15
            radius = int(8 + st * 20)
            alpha = _NS_tsukiyora._alpha(240 * (1 - st))
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["void_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha),
                                     (tx, ty), radius, 2)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_mid"], alpha),
                                     (tx, ty), max(1, radius - 5), 2)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_light"], alpha),
                                     (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["cosmic_hot"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 30), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius, 110 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 3, 8, 180), (5, 8, 120, 14))
        pygame.draw.ellipse(shadow, (40, 20, 70, 100), (12, 10, 106, 10))
        surface.blit(shadow, (x - 65, y - 15))

    def _draw_cosmic_aura(surface, x, y, phase, skill):
        """Purple cosmic aura around goddess."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_tsukiyora._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_tsukiyora._aacircle(aura, (*_NS_tsukiyora.PALETTE["cosmic_darkest"], alpha),
                                         (110, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_tsukiyora._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_tsukiyora._aacircle(aura, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha),
                                         (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Floating cosmic dust particles / stars
        for i in range(20):
            angle = phase * 0.25 + i * math.pi / 10
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5) - 8
            color = _NS_tsukiyora.PALETTE["cosmic_light"] if i % 3 != 0 else _NS_tsukiyora.PALETTE["cosmic_shine"]
            pygame.draw.rect(surface, color, (sx, sy, 1, 1))
            if i % 4 == 0:
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["white"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ring beneath boss with cosmic pattern."""
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_tsukiyora.PALETTE["cosmic_darkest"], 200),
                            (5, 16, 140, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_tsukiyora.PALETTE["cosmic_dark"], 220),
                            (14, 18, 122, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_tsukiyora.PALETTE["cosmic_mid"], 200),
                            (26, 20, 98, 16), 1)

        # Cosmic runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 45)
            y1 = 28 + int(math.sin(angle) * 9)
            x2 = 75 + int(math.cos(angle) * 65)
            y2 = 28 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_tsukiyora.PALETTE["cosmic_hot"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            color = _NS_tsukiyora.PALETTE["moon_light"] if skill == "d" \
                else _NS_tsukiyora.PALETTE["cosmic_hot"]
            pygame.draw.ellipse(ring, (*color, _NS_tsukiyora._alpha(180 * pulse)),
                                (12, 12, 126, 32), 1)
        surface.blit(ring, (x - 75, y - 23))

    # ============================================================
    # SKILL Q - EXPANSIVE TRUTH SEEKER ORB
    # ============================================================
    def _draw_truth_orb_skill(surface, boss, x, y, timer, phase):
        """Massive void orb that expands forward."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Small orb forming in hand
            t = progress / 0.3
            cx = x + facing * 18
            cy = y - 6
            cr = int(4 + t * 8)

            for r in range(cr + 6, 0, -2):
                alpha = _NS_tsukiyora._alpha(180 * (cr + 6 - r) / (cr + 6))
                _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha),
                                         (cx, cy), r)

            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_mid"], (cx, cy), cr + 1, 2)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_darkest"], (cx, cy), cr)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_dark"], (cx, cy), max(1, cr - 2))

            # Purple ring around
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = cx + int(math.cos(angle) * (cr + 3))
                sy = cy + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["cosmic_hot"], (sx, sy, 2, 2))
        else:
            # Massive expanding orb moves forward
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 26
            start_y = y - 6

            # Grows and travels
            orb_r = int(15 + t * 40)
            bx = int(start_x + (200 * t * facing))
            by = start_y

            # Ultra-massive dark orb
            for r in range(orb_r + 10, 0, -3):
                alpha = _NS_tsukiyora._alpha(150 * (orb_r + 10 - r) / (orb_r + 10))
                _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha),
                                         (bx, by), r)

            # Purple outer ring (very bright)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_hot"], (bx, by), orb_r + 3, 3)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_light"], (bx, by), orb_r + 2, 2)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_mid"], (bx, by), orb_r + 1, 2)
            # Pure void interior
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["shadow"], (bx, by), orb_r)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_darkest"], (bx, by), orb_r - 2)
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["void_dark"], (bx, by), max(1, orb_r - 5))

            # Purple sparkles around
            for i in range(16):
                angle = phase * 3 + i * math.pi / 8
                r_s = orb_r + 5 + int(math.sin(phase * 2 + i) * 3)
                sx = bx + int(math.cos(angle) * r_s)
                sy = by + int(math.sin(angle) * r_s)
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["cosmic_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["cosmic_shine"], (sx, sy, 1, 1))

            # Devastation trail
            for i in range(6):
                trail_t = t - i * 0.05
                if trail_t < 0:
                    continue
                trail_x = int(start_x + (200 * trail_t * facing))
                trail_r = orb_r - i * 4
                if trail_r < 2:
                    continue
                alpha = _NS_tsukiyora._alpha(180 - i * 30)
                _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["void_darkest"], alpha),
                                         (trail_x, by), trail_r)
                _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha),
                                         (trail_x, by), trail_r, 2)

    # ============================================================
    # SKILL W - YOMI DIMENSION (target trapped in void portal)
    # ============================================================
    def _draw_yomi_dimension_ground(surface, boss, x, y, timer, phase):
        """Purple portal opening at target."""
        tx, ty = _NS_tsukiyora._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            t = progress / 0.3
            r = int(t * 40)
        else:
            r = 40 + int(math.sin(phase * 2) * 3)

        alpha_fade = _NS_tsukiyora._alpha(220)
        pygame.draw.ellipse(surface, (*_NS_tsukiyora.PALETTE["shadow"], alpha_fade),
                            (tx - r - 2, ty - r // 2 - 2, r * 2 + 4, r + 4))
        pygame.draw.ellipse(surface, (*_NS_tsukiyora.PALETTE["cosmic_darkest"], alpha_fade),
                            (tx - r, ty - r // 2, r * 2, r))
        pygame.draw.ellipse(surface, (*_NS_tsukiyora.PALETTE["cosmic_dark"], alpha_fade),
                            (tx - r + 3, ty - r // 2 + 2, r * 2 - 6, r - 4))
        pygame.draw.ellipse(surface, (*_NS_tsukiyora.PALETTE["void_darkest"], alpha_fade),
                            (tx - r + 8, ty - r // 2 + 4, r * 2 - 16, r - 8))

    def _draw_yomi_dimension_fx(surface, boss, x, y, timer, phase):
        """Swirling void portal + energy pulling target."""
        tx, ty = _NS_tsukiyora._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            return

        # Multiple spiral rings
        for ring_i in range(4):
            base_r = 35 - ring_i * 6
            r = base_r + int(math.sin(phase * 2 + ring_i) * 3)
            if r < 3:
                continue

            for i in range(14):
                angle = phase * (5 + ring_i * 2) + i * math.pi / 7
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                color = [_NS_tsukiyora.PALETTE["cosmic_light"],
                         _NS_tsukiyora.PALETTE["cosmic_mid"],
                         _NS_tsukiyora.PALETTE["cosmic_hot"],
                         _NS_tsukiyora.PALETTE["cosmic_shine"]][ring_i]
                pygame.draw.rect(surface, color, (sx, sy, 2, 2))

        # Debris being sucked in
        for i in range(15):
            debris_t = ((phase * 0.4 + i * 0.13) % 1.0)
            debris_angle = phase * 0.5 + i * math.pi / 8
            outer_r = 70
            inner_r = 15
            debris_r = int(outer_r - debris_t * (outer_r - inner_r))
            dx = tx + int(math.cos(debris_angle) * debris_r)
            dy = ty + int(math.sin(debris_angle) * debris_r * 0.5)
            alpha = _NS_tsukiyora._alpha(220 * debris_t)
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["cosmic_hot"], alpha),
                             (dx, dy, 2, 2))
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["cosmic_shine"], alpha),
                             (dx, dy, 1, 1))

        # Beam of connection from boss to portal
        beam_alpha = _NS_tsukiyora._alpha(150 + math.sin(phase * 4) * 40)
        _NS_tsukiyora._aaline(surface, (*_NS_tsukiyora.PALETTE["cosmic_hot"], beam_alpha),
                               (x + boss.direction * 14, y - 4), (tx, ty), 2)
        _NS_tsukiyora._aaline(surface, (*_NS_tsukiyora.PALETTE["cosmic_shine"], beam_alpha),
                               (x + boss.direction * 14, y - 4), (tx, ty), 1)

    # ============================================================
    # SKILL E - BONE ASH KILLER (barrage of bone needles)
    # ============================================================
    def _draw_bone_needles_skill(surface, boss, x, y, timer, phase):
        """Fire barrage of bone needles from hand toward target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_tsukiyora._target_position(boss, x, y)

        start_x = x + facing * 18
        start_y = y - 4

        if progress < 0.2:
            # Charge - bone particles gathering in hand
            t = progress / 0.2
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                r = int((1 - t) * 10)
                sx = start_x + int(math.cos(angle) * r)
                sy = start_y + int(math.sin(angle) * r)
                _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["bone_dark"], (sx, sy), 2)
                _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["bone_mid"], (sx, sy), 1)
            # Ready core
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["bone_dark"],
                                     (start_x, start_y), int(t * 3))
            return

        # Barrage phase - many needles fly
        t = (progress - 0.2) / 0.8
        num_needles = 20

        for i in range(num_needles):
            # Each needle has slight time offset and angle variation
            needle_t = min(1.0, max(0.0, t - i * 0.02))
            if needle_t <= 0:
                continue

            # Spread angle
            spread_angle = math.atan2(ty - start_y, tx - start_x)
            spread = (i - num_needles / 2) * 0.05
            angle_i = spread_angle + spread

            # Distance based on time
            travel_dist = math.hypot(tx - start_x, ty - start_y)
            travel = needle_t * travel_dist * 1.1

            nx = int(start_x + math.cos(angle_i) * travel)
            ny = int(start_y + math.sin(angle_i) * travel)

            # Draw needle (elongated shape pointing in direction)
            needle_len = 6
            back_x = int(nx - math.cos(angle_i) * needle_len)
            back_y = int(ny - math.sin(angle_i) * needle_len)

            # Trail (streaking bone dust)
            for trail_i in range(3):
                trail_step_t = needle_t - trail_i * 0.03
                if trail_step_t <= 0:
                    continue
                trail_travel = trail_step_t * travel_dist * 1.1
                tx_p = int(start_x + math.cos(angle_i) * trail_travel)
                ty_p = int(start_y + math.sin(angle_i) * trail_travel)
                alpha_t = _NS_tsukiyora._alpha(180 - trail_i * 50)
                pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["bone_light"], alpha_t),
                                 (tx_p, ty_p, 2, 2))

            # Needle body
            _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["shadow_deep"],
                                   (back_x + 1, back_y + 1), (nx + 1, ny + 1), 2)
            _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["bone_darkest"],
                                   (back_x, back_y), (nx, ny), 2)
            _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["bone_dark"],
                                   (back_x, back_y), (nx, ny), 1)
            _NS_tsukiyora._aaline(surface, _NS_tsukiyora.PALETTE["bone_light"],
                                   (back_x, back_y), (nx, ny - 1), 1)
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["bone_shine"], (nx, ny, 1, 1))

            # Impact spark
            if needle_t > 0.95:
                _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["cosmic_hot"], (nx, ny), 2)
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["white"], (nx, ny, 1, 1))

    # ============================================================
    # SKILL R - ALL-KILLING ASH BONES (huge bones erupt from ground)
    # ============================================================
    def _draw_bones_ground(surface, boss, x, y, timer, phase):
        """Ground cracks preparing for bones."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        base_x = x + facing * 40
        base_y = y + 42

        if progress < 0.2:
            t = progress / 0.2
            # Crack the ground
            for i in range(8):
                cx_pt = base_x + int((i - 4) * 12)
                crack_len = int(t * 20)
                pygame.draw.line(surface, (*_NS_tsukiyora.PALETTE["shadow_deep"], 220),
                                 (cx_pt, base_y),
                                 (cx_pt + int(math.cos(i * 0.7) * crack_len),
                                  base_y - int(math.sin(i * 0.7) * crack_len // 2)), 2)

        # Persistent dark ground
        pygame.draw.line(surface, _NS_tsukiyora.PALETTE["bone_darkest"],
                         (base_x - 70, base_y), (base_x + 70, base_y), 2)

    def _draw_bones_skill(surface, boss, x, y, timer, phase):
        """Massive bone spikes erupt in a wide area."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        base_x = x + facing * 40
        base_y = y + 40

        # Growth animation
        if progress < 0.5:
            growth = progress / 0.5
        else:
            growth = 1.0 - (progress - 0.5) / 0.5 * 0.2

        # Draw MANY massive bones in area
        bones = [
            # (x_offset, base_h, width)
            (-50, 35, 6), (-38, 45, 7), (-25, 55, 8), (-12, 50, 7),
            (0, 60, 9), (12, 55, 8), (25, 48, 7), (38, 40, 6), (50, 32, 5),
            # Second row (behind, smaller)
            (-42, 25, 4), (-20, 30, 5), (-5, 32, 5), (18, 28, 4), (40, 22, 4),
        ]

        for bone_i, (x_off, base_h, w) in enumerate(bones):
            delay = bone_i * 0.03
            local_growth = max(0.0, min(1.0, growth - delay))
            bone_h = int(local_growth * base_h)

            if bone_h < 3:
                continue

            bone_x = base_x + x_off
            bone_top_y = base_y - bone_h

            # Bone spike - jagged shape
            # Shadow
            _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["shadow_deep"], [
                (bone_x - w + 1, base_y + 1),
                (bone_x - w // 2 + 1, bone_top_y + bone_h // 3 + 1),
                (bone_x + 1, bone_top_y + 1),
                (bone_x + w // 2 + 1, bone_top_y + bone_h // 3 + 1),
                (bone_x + w + 1, base_y + 1),
            ])
            # Main bone body
            _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["bone_darkest"], [
                (bone_x - w, base_y),
                (bone_x - w // 2 - 1, bone_top_y + bone_h // 2),
                (bone_x - 2, bone_top_y),
                (bone_x + 2, bone_top_y),
                (bone_x + w // 2 + 1, bone_top_y + bone_h // 2),
                (bone_x + w, base_y),
            ])
            _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["bone_dark"], [
                (bone_x - w + 1, base_y),
                (bone_x - w // 2, bone_top_y + bone_h // 2),
                (bone_x - 1, bone_top_y + 1),
                (bone_x + 1, bone_top_y + 1),
                (bone_x + w // 2, bone_top_y + bone_h // 2),
                (bone_x + w - 1, base_y),
            ])
            # Mid highlight (facing light)
            _NS_tsukiyora._poly(surface, _NS_tsukiyora.PALETTE["bone_mid"], [
                (bone_x - 1, base_y),
                (bone_x - 2, bone_top_y + bone_h // 2),
                (bone_x, bone_top_y + 2),
                (bone_x + 2, bone_top_y + bone_h // 2),
                (bone_x + 1, base_y),
            ])
            # Bright tip
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["bone_light"],
                             (bone_x, bone_top_y, 1, 3))
            pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["bone_shine"],
                             (bone_x, bone_top_y, 1, 1))

            # Cracks/ridges on bone
            for ridge_y in range(bone_top_y + 4, base_y - 2, 5):
                ratio = (ridge_y - bone_top_y) / bone_h
                ridge_w = int(2 + (w - 2) * ratio)
                pygame.draw.line(surface, _NS_tsukiyora.PALETTE["bone_darkest"],
                                 (bone_x - ridge_w, ridge_y),
                                 (bone_x + ridge_w, ridge_y), 1)

        # Dust cloud at base
        for i in range(20):
            angle = phase * 0.5 + i * math.pi / 10
            r = int(math.sin(phase * 2 + i) * 15) + 30
            dx = base_x + int(math.cos(angle) * r)
            dy = base_y + int(math.sin(angle) * 3)
            alpha = _NS_tsukiyora._alpha(150 * (1 - abs(math.sin(phase * 0.5 + i))))
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["bone_dark"], alpha),
                             (dx, dy, 3, 2))
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["bone_mid"], alpha),
                             (dx, dy, 2, 1))

    # ============================================================
    # SKILL D - ETERNAL TSUKUYOMI (blood moon in sky + red aura)
    # ============================================================
    def _draw_blood_moon_bg(surface, boss, x, y, timer, phase):
        """Massive blood-red moon appears in sky."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Moon position (upper right area)
        moon_x = x + 150
        moon_y = y - 120

        # Rise animation
        if progress < 0.3:
            t = progress / 0.3
            moon_y = int(y - 120 * t)
            moon_r = int(50 * t)
        else:
            t = (progress - 0.3) / 0.7
            moon_r = 50 + int(math.sin(phase * 1.5) * 3)

        if moon_r < 3:
            return

        # Blood red aura around moon
        for r in range(moon_r + 25, moon_r, -3):
            alpha = _NS_tsukiyora._alpha(120 * (moon_r + 25 - r) / 25)
            _NS_tsukiyora._aacircle(surface, (*_NS_tsukiyora.PALETTE["moon_dark"], alpha),
                                     (moon_x, moon_y), r)

        # Moon body
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_darkest"],
                                 (moon_x, moon_y), moon_r)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_dark"],
                                 (moon_x, moon_y), moon_r - 2)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_mid"],
                                 (moon_x, moon_y), moon_r - 6)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_light"],
                                 (moon_x - 5, moon_y - 5), moon_r - 12)
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_glow"],
                                 (moon_x - 8, moon_y - 8), max(1, moon_r - 20))

        # Crater/tomoe pattern on moon (Rinne-Sharingan look)
        # Center dot
        _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_darkest"],
                                 (moon_x, moon_y), 3)
        # Rings around
        for ring_r in (12, 20, 30):
            _NS_tsukiyora._aacircle(surface, _NS_tsukiyora.PALETTE["moon_darkest"],
                                     (moon_x, moon_y), ring_r, 1)
        # Tomoe marks (3 rotating dots)
        for i in range(3):
            angle = phase * 0.2 + i * (math.pi * 2 / 3)
            for r_pos in (10, 18, 26):
                tmx = moon_x + int(math.cos(angle) * r_pos)
                tmy = moon_y + int(math.sin(angle) * r_pos)
                pygame.draw.rect(surface, _NS_tsukiyora.PALETTE["moon_darkest"],
                                 (tmx - 1, tmy - 1, 3, 3))

    def _draw_tsukuyomi_fx(surface, boss, x, y, timer, phase):
        """Blood red aura + falling petals/particles during Tsukuyomi."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Red aura pulse around boss
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        aura_alpha = _NS_tsukiyora._alpha(180 * pulse)

        aura = pygame.Surface((250, 250), pygame.SRCALPHA)
        for r in range(120, 30, -6):
            alpha = _NS_tsukiyora._alpha((120 - r) * 1.2 * pulse)
            _NS_tsukiyora._aacircle(aura, (*_NS_tsukiyora.PALETTE["moon_darkest"], alpha),
                                     (125, 125), r)
        for r in range(80, 20, -4):
            alpha = _NS_tsukiyora._alpha((80 - r) * 1.5 * pulse)
            _NS_tsukiyora._aacircle(aura, (*_NS_tsukiyora.PALETTE["moon_dark"], alpha),
                                     (125, 125), r)
        surface.blit(aura, (x - 125, y - 125))

        # Falling red petals / particles
        for i in range(25):
            fall_t = ((phase * 0.5 + i * 0.08) % 1.0)
            px = x + int((i - 12) * 12) + int(math.sin(fall_t * 6) * 4)
            py = y - 80 + int(fall_t * 160)
            alpha = _NS_tsukiyora._alpha(220 * (1 - abs(fall_t - 0.5) * 1.5))
            # Petal
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["moon_dark"], alpha),
                             (px, py, 3, 2))
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["moon_mid"], alpha),
                             (px, py, 2, 1))
            pygame.draw.rect(surface, (*_NS_tsukiyora.PALETTE["moon_light"], alpha),
                             (px, py, 1, 1))

        # Runic red circle at ground
        ring_r = 60 + int(math.sin(phase * 2) * 4)
        pygame.draw.ellipse(surface, (*_NS_tsukiyora.PALETTE["moon_darkest"], aura_alpha),
                            (x - ring_r, y + 40 - ring_r // 3,
                             ring_r * 2, ring_r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_tsukiyora.PALETTE["moon_mid"], aura_alpha),
                            (x - ring_r + 4, y + 42 - ring_r // 3,
                             ring_r * 2 - 8, ring_r * 2 // 3 - 4), 2)

        # Rune marks on circle
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = x + int(math.cos(angle) * (ring_r - 5))
            y1 = y + 42 + int(math.sin(angle) * (ring_r // 3 - 2))
            x2 = x + int(math.cos(angle) * (ring_r + 5))
            y2 = y + 42 + int(math.sin(angle) * (ring_r // 3 + 2))
            pygame.draw.line(surface, (*_NS_tsukiyora.PALETTE["moon_light"], aura_alpha),
                             (x1, y1), (x2, y2), 1)


# ====================================================================================================
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ====================================================================================================
def draw_dorakai(surface, boss, x, y):
    """Entry point dorakai."""
    return _NS_dorakai.draw_dorakai(surface, boss, x, y)

def draw_hitokage(surface, boss, x, y):
    """Entry point hitokage."""
    return _NS_hitokage.draw_hitokage(surface, boss, x, y)

def draw_kazuren(surface, boss, x, y):
    """Entry point kazuren."""
    return _NS_kazuren.draw_kazuren(surface, boss, x, y)

def draw_tsukiyora(surface, boss, x, y):
    """Entry point tsukiyora."""
    return _NS_tsukiyora.draw_tsukiyora(surface, boss, x, y)
