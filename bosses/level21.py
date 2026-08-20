"""
bosses/level21.py - Semua boss Level 21

Berisi:
  - kurogari    (mini boss - MELEE shadow ninja void reaper)
  - morvekhar   (mini boss - MELEE iron juggernaut mace tank)
  - vorgath     (mini boss - MELEE demon warden chain ball)
  - nexthyrius  (TRUE BOSS - RANGED spectral chain warden)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _krg_ (kurogari), _morv_ (morvekhar), _vorg_ (vorgath),
    _nex_ (nexthyrius) sudah unik. Nama fungsi namespace (_draw_*)
    TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KUROGARI (VOID REAPER) - Mini Boss
# ====================================================================

class _NS_kurogari:
    """Namespace kurogari - mini boss shadow ninja reaper."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Pale demonic skin
        "skin_darkest": (40, 30, 45),
        "skin_dark": (95, 75, 95),
        "skin_mid": (160, 135, 155),
        "skin_light": (210, 190, 205),
        "skin_shine": (240, 225, 235),
        # Silver/white ninja hair
        "hair_darkest": (60, 55, 75),
        "hair_dark": (110, 105, 130),
        "hair_mid": (170, 165, 185),
        "hair_light": (220, 215, 230),
        "hair_shine": (250, 248, 255),
        # Dark purple armor (main)
        "armor_darkest": (10, 5, 18),
        "armor_dark": (30, 15, 45),
        "armor_mid": (60, 35, 80),
        "armor_light": (110, 75, 140),
        "armor_edge": (160, 120, 190),
        # Crimson/magenta glow (blade, eyes, runes)
        "crimson_darkest": (30, 3, 15),
        "crimson_dark": (90, 10, 40),
        "crimson_mid": (180, 25, 75),
        "crimson_light": (240, 60, 130),
        "crimson_hot": (255, 110, 170),
        "crimson_shine": (255, 200, 220),
        # Blood red (armor accents)
        "blood_dark": (60, 8, 15),
        "blood_mid": (140, 20, 30),
        "blood_light": (220, 50, 60),
        # Eye glow (bright pink-red)
        "eye_socket": (8, 2, 6),
        "eye_darkest": (50, 5, 20),
        "eye_dark": (130, 15, 50),
        "eye_mid": (230, 40, 100),
        "eye_light": (255, 100, 160),
        "eye_glow": (255, 200, 220),
        # Blade metal (dark steel with crimson edge)
        "blade_darkest": (15, 10, 20),
        "blade_dark": (45, 35, 55),
        "blade_mid": (100, 85, 115),
        "blade_light": (180, 165, 195),
        "blade_shine": (240, 230, 250),
        # Gold trim (small accents)
        "gold_dark": (80, 55, 15),
        "gold_mid": (180, 140, 40),
        "gold_light": (240, 210, 100),
        # Void/shadow (dark portal)
        "void_darkest": (5, 2, 12),
        "void_dark": (18, 8, 35),
        "void_mid": (45, 20, 75),
        # Shadow mist
        "mist_dark": (25, 10, 40),
        "mist_mid": (80, 30, 110),
        "mist_light": (180, 80, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kurogari._clamp(color)
        if _NS_kurogari.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kurogari._clamp(color)
        if _NS_kurogari.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kurogari._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kurogari(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_kurogari._update_krg_attack_anim(boss)
        attacking = (
            getattr(boss, "_krg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_kurogari._draw_shadow_aura(surface, x, y, pulse)
        _NS_kurogari._draw_ground_ring(surface, x, y + 42, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_kurogari._draw_demonic_feast_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kurogari._draw_anima_ground(surface, boss, x, y, skill_timer, pulse)
        # If in Demonic Feast (W), boss is submerged - draw minimal / ghost form
        if active_skill == "w":
            _NS_kurogari._draw_krg_submerged(surface, boss, x, y, skill_timer, pulse)
        else:
            # Normal body render
            _NS_kurogari._draw_krg_floating(surface, boss, x, y, attacking, active_skill)
        # Foreground FX
        if active_skill == "q":
            _NS_kurogari._draw_soul_reap(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kurogari._draw_pinpoint_ninja(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kurogari._draw_anima_foreground(surface, boss, x, y, skill_timer, pulse)
        # Basic melee swing
        if attacking and active_skill is None:
            _NS_kurogari._draw_basic_swing(surface, boss, x, y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_krg_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_krg_previous_timer", 0))
        active = bool(getattr(boss, "_krg_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._krg_attack_active = True
            boss._krg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._krg_attack_frame = int(getattr(boss, "_krg_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._krg_attack_active = False
            boss._krg_attack_frame = 0
            active = False
        boss._krg_previous_timer = timer
        boss._krg_attack_progress = (
            min(1.0, getattr(boss, "_krg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # FLOATING POSE
    # ============================================================
    def _draw_krg_floating(surface, boss, x, y, attacking, active_skill):
        float_bob = math.sin(boss.pulse * 0.7) * 5
        _NS_kurogari._draw_shadow(surface, x, y + 46)
        _NS_kurogari._draw_shadow_mist(surface, x, y + 28, boss.pulse)
        progress = getattr(boss, "_krg_attack_progress", 0)
        # Swing arm animation
        swing_angle = 0
        if attacking and active_skill is None:
            # Swing: 0 -> up-back (charge) -> forward-down (strike) -> back to rest
            if progress < 0.4:
                # Wind up
                t = progress / 0.4
                swing_angle = -math.pi * 0.6 * t
            elif progress < 0.65:
                # Strike
                t = (progress - 0.4) / 0.25
                swing_angle = -math.pi * 0.6 + math.pi * 1.4 * t
            else:
                # Return
                t = (progress - 0.65) / 0.35
                swing_angle = math.pi * 0.8 * (1 - t)
        _NS_kurogari._draw_krg_body(surface, x, int(y + float_bob),
                                     boss.direction, boss.pulse,
                                     swing_angle, progress if attacking else 0,
                                     active_skill)
    def _draw_krg_submerged(surface, boss, x, y, timer, pulse):
        """During W skill - boss is a shadow silhouette."""
        # Just a portal + fading silhouette
        alpha = _NS_kurogari._alpha(80 + math.sin(pulse * 2) * 40)
        silhouette_pts = [
            (x - 8, y - 25),
            (x - 12, y - 5),
            (x - 8, y + 15),
            (x + 8, y + 15),
            (x + 12, y - 5),
            (x + 8, y - 25),
        ]
        _NS_kurogari._poly(surface, (*_NS_kurogari.PALETTE["void_darkest"], alpha),
                            silhouette_pts)
        # Two glowing eyes visible
        for eye_off in (-3, 3):
            ex = x + eye_off
            ey = y - 18
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_light"], (ex, ey, 1, 1))
    # ============================================================
    # BODY - Demonic Ninja (upright, floating, cape/hair flowing)
    # ============================================================
    def _draw_krg_body(surface, cx, cy, facing, phase, swing_angle,
                        attack_progress, active_skill):
        # Draw hair/cape sash behind
        _NS_kurogari._draw_flowing_hair(surface, cx, cy, facing, phase)
        # Draw back scarf/sash tails
        _NS_kurogari._draw_back_sash(surface, cx, cy, facing, phase)
        # Under floating - shadow wisps
        _NS_kurogari._draw_floating_wisps(surface, cx, cy + 28, phase)
        # Legs (armored, hanging down while floating)
        _NS_kurogari._draw_ninja_legs(surface, cx, cy + 10, facing, phase)
        # Torso armor
        _NS_kurogari._draw_ninja_torso(surface, cx, cy, facing, phase)
        # Arms (with blade in dominant hand)
        _NS_kurogari._draw_ninja_arms(surface, cx, cy, facing, phase,
                                       swing_angle, attack_progress, active_skill)
        # Shoulder pauldrons (spiked)
        _NS_kurogari._draw_shoulder_pauldrons(surface, cx, cy - 12, facing, phase)
        # Head with oni mask
        _NS_kurogari._draw_oni_head(surface, cx, cy - 26, facing, phase, attack_progress)
    def _draw_flowing_hair(surface, cx, cy, facing, phase):
        """Long silver hair flowing back."""
        back_dir = -facing
        sway = math.sin(phase * 0.6) * 3
        # Main hair mass behind head (long tail)
        hair_pts = [
            (cx + back_dir * 4, cy - 30),
            (cx + back_dir * 12, cy - 25 + int(sway)),
            (cx + back_dir * 18, cy - 15 + int(sway * 1.2)),
            (cx + back_dir * 22, cy - 5 + int(sway * 1.5)),
            (cx + back_dir * 24, cy + 5 + int(sway * 2)),
            (cx + back_dir * 22, cy + 15 + int(sway * 1.5)),
            (cx + back_dir * 18, cy + 12),
            (cx + back_dir * 12, cy),
            (cx + back_dir * 6, cy - 15),
            (cx + back_dir * 2, cy - 28),
        ]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["hair_darkest"], hair_pts)
        # Inner hair
        inner_pts = [
            (cx + back_dir * 3, cy - 28),
            (cx + back_dir * 10, cy - 23 + int(sway)),
            (cx + back_dir * 15, cy - 13 + int(sway * 1.2)),
            (cx + back_dir * 18, cy - 3 + int(sway * 1.5)),
            (cx + back_dir * 20, cy + 6 + int(sway * 1.8)),
            (cx + back_dir * 17, cy + 10),
            (cx + back_dir * 10, cy - 2),
            (cx + back_dir * 4, cy - 22),
        ]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["hair_dark"], inner_pts)
        # Hair strand highlights
        for i, offset in enumerate([(cx + back_dir * 8, cy - 22),
                                     (cx + back_dir * 14, cy - 12),
                                     (cx + back_dir * 18, cy - 2),
                                     (cx + back_dir * 19, cy + 8)]):
            highlight_x = offset[0] + int(sway * 0.5 * i)
            highlight_y = offset[1]
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["hair_mid"],
                                  (highlight_x, highlight_y - 1),
                                  (highlight_x + back_dir * 3, highlight_y + 1), 1)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["hair_light"],
                             (highlight_x, highlight_y, 1, 1))
        # Crimson tips (magic glow at hair ends)
        for tip in [(cx + back_dir * 24, cy + 5 + int(sway * 2)),
                    (cx + back_dir * 22, cy + 15 + int(sway * 1.5)),
                    (cx + back_dir * 18, cy - 15 + int(sway * 1.2))]:
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_dark"], tip, 2)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"], (tip[0], tip[1], 1, 1))
    def _draw_back_sash(surface, cx, cy, facing, phase):
        """Red sash/scarf tails flowing behind."""
        back_dir = -facing
        sway = math.sin(phase * 0.5 + 1) * 4
        # Two sash tails
        for i, base_y_off in enumerate((-5, 5)):
            base_x = cx + back_dir * 6
            base_y = cy + base_y_off
            tip_x = cx + back_dir * (16 + i * 4) + int(sway * (1 + i * 0.3))
            tip_y = cy + base_y_off + 15 + int(sway * 0.5)
            # Sash shape
            sash_pts = [
                (base_x, base_y - 2),
                (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2) - 1),
                (tip_x, tip_y),
                (tip_x + back_dir * 2, tip_y + 3),
                (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2) + 2),
                (base_x, base_y + 2),
            ]
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in sash_pts])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blood_dark"], sash_pts)
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blood_mid"], [
                (base_x, base_y - 1),
                (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2)),
                (tip_x, tip_y + 1),
                (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2) + 1),
            ])
            # Highlight
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["blood_light"],
                             (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2), 1, 1))
    def _draw_ninja_torso(surface, cx, cy, facing, phase):
        """Dark armored torso with crimson runes."""
        torso_pts = [
            (cx - 9, cy - 15),
            (cx - 11, cy - 8),
            (cx - 10, cy + 5),
            (cx - 8, cy + 12),
            (cx + 8, cy + 12),
            (cx + 10, cy + 5),
            (cx + 11, cy - 8),
            (cx + 9, cy - 15),
        ]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in torso_pts])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_darkest"], torso_pts)
        # Armor body
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_dark"], [
            (cx - 8, cy - 14),
            (cx - 10, cy - 7),
            (cx - 9, cy + 4),
            (cx - 7, cy + 11),
            (cx + 7, cy + 11),
            (cx + 9, cy + 4),
            (cx + 10, cy - 7),
            (cx + 8, cy - 14),
        ])
        # Chest plate (mid tone)
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_mid"], [
            (cx - 6, cy - 12),
            (cx - 8, cy - 5),
            (cx - 7, cy + 3),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 3),
            (cx + 8, cy - 5),
            (cx + 6, cy - 12),
        ])
        # Chest highlight
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_light"], [
            (cx - 4, cy - 10),
            (cx - 5, cy - 4),
            (cx - 3, cy + 2),
            (cx + 3, cy + 2),
            (cx + 5, cy - 4),
            (cx + 4, cy - 10),
        ])
        # Center rune (crimson glow gem in chest)
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_kurogari._alpha(180 * (5 - r) / 5 * gem_pulse)
            _NS_kurogari._aacircle(surface, (*_NS_kurogari.PALETTE["crimson_mid"], alpha),
                                    (cx, cy - 4), r)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_dark"],
                         (cx - 1, cy - 5, 3, 3))
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_light"],
                         (cx, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"], (cx, cy - 4, 1, 1))
        # Belly rune lines (crimson etched details)
        for y_off in (2, 6, 10):
            pygame.draw.line(surface, _NS_kurogari.PALETTE["crimson_darkest"],
                             (cx - 5, cy + y_off), (cx + 5, cy + y_off), 1)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_dark"],
                             (cx - 1, cy + y_off, 3, 1))
        # Side armor plates (highlights)
        pygame.draw.line(surface, _NS_kurogari.PALETTE["armor_edge"],
                         (cx - 8, cy - 10), (cx - 8, cy + 5), 1)
        pygame.draw.line(surface, _NS_kurogari.PALETTE["armor_edge"],
                         (cx + 8, cy - 10), (cx + 8, cy + 5), 1)
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase):
        """Spiked shoulder armor."""
        for side in (-1, 1):
            sx = cx + side * 11
            # Main pauldron
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"], [
                (sx + side * 1, cy - 4),
                (sx + side * 6, cy - 2),
                (sx + side * 7, cy + 3),
                (sx + side * 4, cy + 6),
                (sx - side * 1, cy + 5),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_darkest"], [
                (sx, cy - 4),
                (sx + side * 5, cy - 2),
                (sx + side * 6, cy + 3),
                (sx + side * 3, cy + 5),
                (sx - side * 2, cy + 4),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_dark"], [
                (sx, cy - 3),
                (sx + side * 4, cy - 1),
                (sx + side * 5, cy + 2),
                (sx + side * 2, cy + 4),
                (sx - side * 1, cy + 3),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_mid"], [
                (sx, cy - 2),
                (sx + side * 3, cy),
                (sx + side * 3, cy + 2),
                (sx, cy + 3),
            ])
            # Spike on top
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_darkest"], [
                (sx + side * 2, cy - 4),
                (sx + side * 3, cy - 8),
                (sx + side * 4, cy - 4),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_dark"], [
                (sx + side * 2, cy - 4),
                (sx + side * 3, cy - 7),
                (sx + side * 4, cy - 4),
            ])
            # Spike glow tip
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                             (sx + side * 3, cy - 8, 1, 1))
            # Crimson accent on pauldron
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_mid"],
                             (sx + side * 3, cy + 1, 2, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                             (sx + side * 3, cy + 1, 1, 1))
    def _draw_ninja_arms(surface, cx, cy, facing, phase, swing_angle,
                          attack_progress, active_skill):
        """Two arms - dominant holds the sabit/kusarigama."""
        back_side = -facing
        front_side = facing
        # Back arm (default position)
        back_shoulder = (cx + back_side * 10, cy - 12)
        back_elbow = (cx + back_side * 13, cy - 2)
        back_hand = (cx + back_side * 11, cy + 10)
        _NS_kurogari._draw_arm(surface, back_shoulder, back_elbow, back_hand, phase)
        # Front arm - holds blade, animates with swing
        front_shoulder = (cx + front_side * 10, cy - 12)
        if abs(swing_angle) > 0.01:
            # Swinging - hand position rotates
            arm_len = 18
            hand_x = front_shoulder[0] + int(math.cos(swing_angle - math.pi / 2)
                                              * arm_len) * front_side
            hand_y = front_shoulder[1] + int(math.sin(swing_angle - math.pi / 2)
                                              * arm_len)
            elbow_x = int((front_shoulder[0] + hand_x) / 2 + front_side * 3)
            elbow_y = int((front_shoulder[1] + hand_y) / 2) - 2
            front_elbow = (elbow_x, elbow_y)
            front_hand = (hand_x, hand_y)
        elif active_skill == "q":
            # Extended forward for skill Q cast
            front_elbow = (cx + front_side * 15, cy - 5)
            front_hand = (cx + front_side * 22, cy - 2)
        else:
            # Idle - blade at side
            idle_bob = int(math.sin(phase * 0.6) * 2)
            front_elbow = (cx + front_side * 14, cy - 2 + idle_bob)
            front_hand = (cx + front_side * 12, cy + 10 + idle_bob)
        _NS_kurogari._draw_arm(surface, front_shoulder, front_elbow, front_hand, phase)
        # Draw the sabit blade in front hand
        if active_skill != "w":  # Hidden during W
            _NS_kurogari._draw_sabit_blade(surface, front_hand, front_shoulder,
                                            facing, phase, swing_angle)
    def _draw_arm(surface, shoulder, elbow, hand, phase):
        """Single arm segment with armor."""
        # Upper arm (armored)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_darkest"],
                              shoulder, elbow, 4)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_dark"],
                              shoulder, elbow, 3)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 1)
        # Elbow armor plate
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["armor_darkest"], elbow, 3)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["armor_dark"], elbow, 2)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_mid"],
                         (elbow[0], elbow[1], 1, 1))
        # Forearm (armored gauntlet)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 4)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_darkest"],
                              elbow, hand, 3)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_dark"],
                              elbow, hand, 2)
        # Hand (armored fist)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["shadow_deep"],
                                (hand[0] + 1, hand[1] + 1), 4)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["armor_darkest"], hand, 3)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["armor_dark"], hand, 2)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["armor_mid"],
                         (hand[0] - 1, hand[1] - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["armor_edge"], (hand[0], hand[1] - 1, 1, 1))
    def _draw_sabit_blade(surface, hand, shoulder, facing, phase, swing_angle):
        """Curved sabit/kusarigama blade with crimson glow."""
        # Blade points outward from hand
        # Determine blade direction based on swing_angle
        if abs(swing_angle) > 0.01:
            blade_angle = swing_angle
        else:
            blade_angle = math.pi * 0.15 * facing  # slight downward angle
        # Blade base (attaches to hand)
        base_x = hand[0]
        base_y = hand[1]
        # Curved blade points (sabit/scythe shape)
        blade_len = 24
        # Blade goes in an arc: base -> mid-out -> tip curved back
        mid_angle = blade_angle - math.pi / 2 * facing
        mid_x = base_x + int(math.cos(mid_angle) * blade_len * 0.5)
        mid_y = base_y + int(math.sin(mid_angle) * blade_len * 0.5)
        tip_angle = blade_angle - math.pi / 2 * facing - math.pi * 0.35 * facing
        tip_x = base_x + int(math.cos(mid_angle) * blade_len * 0.4) \
                       + int(math.cos(tip_angle) * blade_len * 0.6)
        tip_y = base_y + int(math.sin(mid_angle) * blade_len * 0.4) \
                       + int(math.sin(tip_angle) * blade_len * 0.6)
        # Inner curve point
        inner_x = base_x + int(math.cos(mid_angle) * blade_len * 0.3) \
                         + int(math.cos(tip_angle + math.pi * 0.15) * blade_len * 0.3)
        inner_y = base_y + int(math.sin(mid_angle) * blade_len * 0.3) \
                         + int(math.sin(tip_angle + math.pi * 0.15) * blade_len * 0.3)
        # Handle grip perpendicular
        grip_perp = blade_angle
        grip_a = (base_x + int(math.cos(grip_perp) * 3),
                  base_y + int(math.sin(grip_perp) * 3))
        grip_b = (base_x - int(math.cos(grip_perp) * 3),
                  base_y - int(math.sin(grip_perp) * 3))
        # Shadow behind blade
        blade_pts_shadow = [
            (grip_a[0] + 2, grip_a[1] + 2),
            (mid_x + 2, mid_y + 2),
            (tip_x + 2, tip_y + 2),
            (inner_x + 2, inner_y + 2),
            (grip_b[0] + 2, grip_b[1] + 2),
        ]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"], blade_pts_shadow)
        # Main blade shape (curved)
        blade_pts = [grip_a, mid_x_mid_pt := (mid_x, mid_y),
                     (tip_x, tip_y), (inner_x, inner_y), grip_b]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blade_darkest"], blade_pts)
        # Inner blade
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blade_dark"], [
            (int((grip_a[0] + base_x) / 2), int((grip_a[1] + base_y) / 2)),
            (mid_x, mid_y),
            (tip_x, tip_y),
            (inner_x, inner_y),
            (int((grip_b[0] + base_x) / 2), int((grip_b[1] + base_y) / 2)),
        ])
        # Blade shine
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blade_mid"], [
            (int((grip_a[0] + mid_x) / 2), int((grip_a[1] + mid_y) / 2)),
            (int((mid_x + tip_x) / 2), int((mid_y + tip_y) / 2)),
            (int((tip_x + inner_x) / 2), int((tip_y + inner_y) / 2)),
        ])
        # Cutting edge (crimson glow along outer curve)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["crimson_dark"],
                              grip_a, (mid_x, mid_y), 2)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["crimson_mid"],
                              grip_a, (mid_x, mid_y), 1)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["crimson_dark"],
                              (mid_x, mid_y), (tip_x, tip_y), 2)
        _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["crimson_light"],
                              (mid_x, mid_y), (tip_x, tip_y), 1)
        # Blade tip glow
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_dark"], (tip_x, tip_y), 3)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_mid"], (tip_x, tip_y), 2)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_hot"], (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                         (tip_x, tip_y, 1, 1))
        # Handle wrap
        pygame.draw.line(surface, _NS_kurogari.PALETTE["blood_dark"], grip_a, grip_b, 3)
        pygame.draw.line(surface, _NS_kurogari.PALETTE["blood_mid"], grip_a, grip_b, 1)
        # Swing trail effect
        if abs(swing_angle) > 0.01:
            for i in range(5):
                trail_angle = swing_angle - i * 0.1 * (1 if swing_angle > 0 else -1)
                trail_tip_x = hand[0] + int(math.cos(trail_angle - math.pi / 2 * facing)
                                             * blade_len * 0.7)
                trail_tip_y = hand[1] + int(math.sin(trail_angle - math.pi / 2 * facing)
                                             * blade_len * 0.7)
                alpha = _NS_kurogari._alpha(180 - i * 35)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                        (trail_tip_x, trail_tip_y), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                 (trail_tip_x, trail_tip_y, 1, 1))
    def _draw_ninja_legs(surface, cx, cy, facing, phase):
        """Armored legs hanging while floating."""
        # Legs tucked slightly (floating pose)
        leg_bob = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            # Thigh
            thigh_top = (cx + side * 3, cy - 2)
            knee = (cx + side * 4, cy + 6 + int(leg_bob * 0.5))
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["shadow_deep"],
                                  (thigh_top[0] + 1, thigh_top[1] + 1),
                                  (knee[0] + 1, knee[1] + 1), 6)
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_darkest"],
                                  thigh_top, knee, 5)
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_dark"],
                                  thigh_top, knee, 4)
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_mid"],
                                  (thigh_top[0], thigh_top[1] - 1),
                                  (knee[0], knee[1] - 1), 2)
            # Knee guard
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["armor_darkest"], knee, 4)
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["armor_dark"], knee, 3)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_mid"],
                             (knee[0], knee[1], 1, 1))
            # Shin (curled back for floating)
            foot = (cx + side * 3, cy + 15 + int(leg_bob))
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["shadow_deep"],
                                  (knee[0] + 1, knee[1] + 1),
                                  (foot[0] + 1, foot[1] + 1), 5)
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_darkest"],
                                  knee, foot, 4)
            _NS_kurogari._aaline(surface, _NS_kurogari.PALETTE["armor_dark"],
                                  knee, foot, 3)
            # Foot / boot
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"], [
                (foot[0] - 3, foot[1] - 1),
                (foot[0] + side * 5, foot[1] + 1),
                (foot[0] + side * 4, foot[1] + 3),
                (foot[0] - 3, foot[1] + 2),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_darkest"], [
                (foot[0] - 3, foot[1] - 1),
                (foot[0] + side * 4, foot[1]),
                (foot[0] + side * 3, foot[1] + 2),
                (foot[0] - 3, foot[1] + 1),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_dark"], [
                (foot[0] - 2, foot[1]),
                (foot[0] + side * 3, foot[1] + 1),
                (foot[0] - 2, foot[1] + 1),
            ])
    def _draw_oni_head(surface, cx, cy, facing, phase, attack_progress):
        """Head with oni mask (demonic ninja mask)."""
        # Head shape
        head_pts = [
            (cx - 7, cy - 8),
            (cx - 8, cy - 3),
            (cx - 7, cy + 3),
            (cx - 5, cy + 7),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 7),
            (cx + 7, cy + 3),
            (cx + 8, cy - 3),
            (cx + 7, cy - 8),
            (cx + 3, cy - 10),
            (cx - 3, cy - 10),
        ]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["skin_darkest"], head_pts)
        # Skin (upper face only, mask covers lower)
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["skin_dark"], [
            (cx - 6, cy - 8),
            (cx - 7, cy - 3),
            (cx - 6, cy + 1),
            (cx + 6, cy + 1),
            (cx + 7, cy - 3),
            (cx + 6, cy - 8),
            (cx + 3, cy - 9),
            (cx - 3, cy - 9),
        ])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["skin_mid"], [
            (cx - 5, cy - 6),
            (cx - 6, cy - 2),
            (cx + 6, cy - 2),
            (cx + 5, cy - 6),
        ])
        # Headband/bandana (red with crimson)
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blood_dark"], [
            (cx - 7, cy - 8),
            (cx - 7, cy - 5),
            (cx + 7, cy - 5),
            (cx + 7, cy - 8),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["blood_mid"], [
            (cx - 6, cy - 7),
            (cx - 6, cy - 6),
            (cx + 6, cy - 6),
            (cx + 6, cy - 7),
        ])
        # Crimson symbol on headband (center dot)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_darkest"],
                         (cx - 1, cy - 7, 3, 2))
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_mid"], (cx, cy - 7, 2, 1))
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"], (cx, cy - 7, 1, 1))
        # Horns (small oni horns on sides of head)
        for side in (-1, 1):
            horn_base = (cx + side * 6, cy - 8)
            horn_tip = (cx + side * 8, cy - 12)
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"], [
                (horn_base[0], horn_base[1] + 1),
                (horn_tip[0] + 1, horn_tip[1] + 1),
                (horn_base[0] + side * 2, horn_base[1] + 1),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_darkest"], [
                (horn_base[0], horn_base[1]),
                (horn_tip[0], horn_tip[1]),
                (horn_base[0] + side * 2, horn_base[1]),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_dark"], [
                (horn_base[0], horn_base[1]),
                (horn_tip[0], horn_tip[1]),
                (horn_base[0] + side * 1, horn_base[1]),
            ])
            # Horn tip glow
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                             (horn_tip[0], horn_tip[1], 1, 1))
        # EYES (glowing pink/red under mask)
        _NS_kurogari._draw_oni_eyes(surface, cx, cy - 2, facing, phase)
        # ONI MASK (lower face - metal mouth guard)
        _NS_kurogari._draw_oni_mask(surface, cx, cy + 3, facing, phase, attack_progress)
    def _draw_oni_eyes(surface, cx, cy, facing, phase):
        """Glowing crimson/pink eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-3, 3):
            ex = cx + eye_off
            ey = cy
            # Socket
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_socket"],
                             (ex - 1, ey, 3, 2))
            # Glow halo
            for radius in range(4, 0, -1):
                alpha = _NS_kurogari._alpha(100 * (4 - radius) / 4 * pulse)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["eye_mid"], alpha),
                                        (ex, ey), radius)
            # Iris
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_darkest"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
    def _draw_oni_mask(surface, cx, cy, facing, phase, attack_progress):
        """Metal mouth guard mask with fangs."""
        # Mask shape (covers nose to chin)
        mask_pts = [
            (cx - 6, cy - 3),
            (cx - 7, cy),
            (cx - 6, cy + 4),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 6, cy + 4),
            (cx + 7, cy),
            (cx + 6, cy - 3),
        ]
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in mask_pts])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_darkest"], mask_pts)
        # Mask surface
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_dark"], [
            (cx - 5, cy - 2),
            (cx - 6, cy),
            (cx - 5, cy + 3),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 5, cy + 3),
            (cx + 6, cy),
            (cx + 5, cy - 2),
        ])
        _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["armor_mid"], [
            (cx - 4, cy - 1),
            (cx - 5, cy + 1),
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 5, cy + 1),
            (cx + 4, cy - 1),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["armor_edge"], (cx - 2, cy, 4, 1))
        # Fangs on mask (metal teeth)
        for fang_x_off in (-3, 0, 3):
            fang_x = cx + fang_x_off
            fang_top_y = cy + 3
            fang_tip_y = fang_top_y + 3
            if attack_progress > 0.4 and attack_progress < 0.7:
                # Show fangs when striking
                fang_tip_y += 1
            pygame.draw.line(surface, _NS_kurogari.PALETTE["blade_darkest"],
                             (fang_x, fang_top_y), (fang_x, fang_tip_y), 1)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["blade_mid"],
                             (fang_x, fang_top_y, 1, 2))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["blade_light"],
                             (fang_x, fang_tip_y, 1, 1))
        # Crimson glow lines on mask (rune tattoo)
        pygame.draw.line(surface, _NS_kurogari.PALETTE["crimson_dark"],
                         (cx - 4, cy + 2), (cx - 2, cy + 4), 1)
        pygame.draw.line(surface, _NS_kurogari.PALETTE["crimson_mid"],
                         (cx + 2, cy + 4), (cx + 4, cy + 2), 1)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                         (cx - 2, cy + 4, 1, 1))
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                         (cx + 2, cy + 4, 1, 1))
    def _draw_floating_wisps(surface, cx, cy, phase):
        """Shadow wisps under floating body."""
        # Swirling dark energy
        for i in range(6):
            angle = phase * 0.9 + i * math.pi / 3
            r = 10 + int(math.sin(phase * 1.5 + i) * 3)
            wx = cx + int(math.cos(angle) * r)
            wy = cy + int(math.sin(angle) * r * 0.4)
            alpha = _NS_kurogari._alpha(160 + math.sin(phase * 2 + i) * 50)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["mist_dark"], alpha),
                                    (wx, wy), 3)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["mist_mid"], alpha),
                                    (wx, wy), 2)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"], (wx, wy, 1, 1))
        # Small floating shadow petals
        for i in range(4):
            angle = phase * 1.2 + i * math.pi / 2
            px = cx + int(math.cos(angle) * 14)
            py = cy + int(math.sin(angle) * 5) - 2
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["void_dark"], [
                (px, py - 1),
                (px - 2, py + 1),
                (px, py + 1),
            ])
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_light"],
                             (px, py, 1, 1))
    # ============================================================
    # BASIC ATTACK - Melee Sabit Swing
    # ============================================================
    def _draw_basic_swing(surface, boss, x, y):
        """Extra crimson slash arc during basic melee."""
        progress = getattr(boss, "_krg_attack_progress", 0)
        if progress < 0.4 or progress > 0.75:
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.35
        # Arc trail from up-back to down-front
        center_x = x + facing * 4
        center_y = y - 4
        arc_r = 28
        # Draw arc slash
        start_angle = -math.pi * 0.7
        end_angle = math.pi * 0.4
        current_angle = start_angle + (end_angle - start_angle) * t
        # Slash trail (multiple crescent segments)
        for i in range(8):
            seg_t = max(0, t - i * 0.05)
            seg_angle = start_angle + (end_angle - start_angle) * seg_t
            sx = center_x + int(math.cos(seg_angle) * arc_r) * facing
            sy = center_y + int(math.sin(seg_angle) * arc_r)
            alpha = _NS_kurogari._alpha(220 - i * 25)
            size = max(1, 6 - i)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["crimson_darkest"], alpha),
                                    (sx, sy), size)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["crimson_mid"], alpha),
                                    (sx, sy), max(1, size - 1))
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                    (sx, sy), max(1, size - 3))
            pygame.draw.rect(surface,
                             (*_NS_kurogari.PALETTE["crimson_shine"], alpha),
                             (sx, sy, 1, 1))
        # Impact sparks at strike moment
        if 0.4 < t < 0.7:
            tip_x = center_x + int(math.cos(current_angle) * arc_r) * facing
            tip_y = center_y + int(math.sin(current_angle) * arc_r)
            for i in range(6):
                spark_angle = i * math.pi / 3
                spark_x = tip_x + int(math.cos(spark_angle) * 6)
                spark_y = tip_y + int(math.sin(spark_angle) * 6)
                pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                                 (spark_x, spark_y, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 2, 10, 170), (5, 8, 110, 12))
        pygame.draw.ellipse(shadow, (60, 15, 60, 100), (12, 10, 96, 8))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_shadow_aura(surface, x, y, phase):
        """Compact but intense shadow/crimson aura."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(75, 5, -4):
            alpha = _NS_kurogari._alpha((75 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kurogari._aacircle(aura,
                                        (*_NS_kurogari.PALETTE["mist_dark"], alpha),
                                        (90, 80), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_kurogari._alpha((45 - radius) * 1.7 * pulse)
            if alpha > 0:
                _NS_kurogari._aacircle(aura,
                                        (*_NS_kurogari.PALETTE["mist_mid"], alpha),
                                        (90, 80), radius)
        for radius in range(25, 5, -2):
            alpha = _NS_kurogari._alpha((25 - radius) * 2 * pulse)
            if alpha > 0:
                _NS_kurogari._aacircle(aura,
                                        (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                        (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))
        # Floating embers (crimson + shadow)
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 30 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            color = _NS_kurogari.PALETTE["crimson_mid"] if i % 2 else _NS_kurogari.PALETTE["mist_mid"]
            hot = _NS_kurogari.PALETTE["crimson_hot"] if i % 2 else _NS_kurogari.PALETTE["mist_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
    def _draw_shadow_mist(surface, cx, cy, phase):
        """Shadow mist around boss."""
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(28, 3, -3):
            alpha = _NS_kurogari._alpha((28 - radius) * 2.8 * pulse)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                                    (*_NS_kurogari.PALETTE["mist_dark"], alpha),
                                    (70 - radius * 2, 22 - radius // 3,
                                     radius * 4, max(3, radius // 2)))
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising crimson wisps
        for i in range(5):
            t = (phase * 0.4 + i * 0.18) % 1.0
            sx = cx + (-18 + i * 8) + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 22)
            alpha = _NS_kurogari._alpha(200 * (1 - t))
            if alpha > 0:
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["mist_mid"], alpha),
                                        (sx, sy), 2)
                pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                                 (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kurogari.PALETTE["mist_dark"], 200),
                            (5, 15, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_kurogari.PALETTE["crimson_darkest"], 220),
                            (14, 17, 122, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_kurogari.PALETTE["crimson_dark"], 230),
                            (25, 19, 100, 14), 1)
        # Rune ticks
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 42)
            y1 = 25 + int(math.sin(angle) * 8)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 25 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_kurogari.PALETTE["crimson_hot"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kurogari.PALETTE["crimson_hot"],
                                 _NS_kurogari._alpha(150 * pulse)),
                                (15, 8, 120, 32), 1)
        surface.blit(ring, (x - 75, y - 23))
    # ============================================================
    # SKILL Q - SOUL REAP (line skillshot)
    # ============================================================
    def _draw_soul_reap(surface, boss, x, y, timer, phase):
        """Long crescent blade projectile that pierces forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kurogari._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in hand
            t = progress / 0.2
            hand_x = x + facing * 22
            hand_y = y - 2
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kurogari._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_mid"],
                                    (hand_x, hand_y), cr - 2)
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_hot"],
                                    (hand_x, hand_y), max(1, cr - 4))
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_shine"],
                                    (hand_x, hand_y), max(1, cr - 6))
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                                 (sx, sy, 1, 1))
        else:
            # Flying crescent blade
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 26
            start_y = y - 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Movement angle
            angle = math.atan2(ty - start_y, tx - start_x)
            perp = angle + math.pi / 2
            # Long trail
            for i in range(14):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kurogari._alpha(240 - i * 17)
                size = max(1, 7 - i)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_darkest"], alpha),
                                        (px, py), size)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                        (px, py), max(1, size - 3))
            # Crescent blade shape at head
            blade_len = 22
            # Front tip (leading point)
            tip_x = bx + int(math.cos(angle) * blade_len * 0.6)
            tip_y = by + int(math.sin(angle) * blade_len * 0.6)
            # Wings (top and bottom of crescent)
            wing_a = (bx + int(math.cos(perp) * 8),
                      by + int(math.sin(perp) * 8))
            wing_b = (bx - int(math.cos(perp) * 8),
                      by - int(math.sin(perp) * 8))
            # Back point (concave part of crescent)
            back_x = bx - int(math.cos(angle) * 4)
            back_y = by - int(math.sin(angle) * 4)
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (wing_a[0] + 1, wing_a[1] + 1),
                (back_x + 1, back_y + 1),
                (wing_b[0] + 1, wing_b[1] + 1),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["crimson_darkest"], [
                (tip_x, tip_y), wing_a, (back_x, back_y), wing_b,
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["crimson_dark"], [
                (tip_x, tip_y),
                (int((tip_x + wing_a[0]) / 2), int((tip_y + wing_a[1]) / 2)),
                (bx, by),
                (int((tip_x + wing_b[0]) / 2), int((tip_y + wing_b[1]) / 2)),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["crimson_mid"], [
                (tip_x, tip_y),
                (int((tip_x + bx) / 2 + math.cos(perp) * 2),
                 int((tip_y + by) / 2 + math.sin(perp) * 2)),
                (bx, by),
                (int((tip_x + bx) / 2 - math.cos(perp) * 2),
                 int((tip_y + by) / 2 - math.sin(perp) * 2)),
            ])
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_hot"], (tip_x, tip_y), 2)
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_shine"], (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["white"], (tip_x, tip_y, 1, 1))
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(10 + st * 22)
                alpha = _NS_kurogari._alpha(240 * (1 - st))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                        (tx, ty), max(1, radius - 10), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - DEMONIC FEAST (portal / untargetable)
    # ============================================================
    def _draw_demonic_feast_ground(surface, boss, x, y, timer, phase):
        """Shadow portal opens under boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Portal grows
        r = int(30 * min(1.0, progress * 3))
        if r > 3:
            # Outer dark ring
            pygame.draw.ellipse(surface, (*_NS_kurogari.PALETTE["void_darkest"], 240),
                                (x - r, y + 40 - r // 2, r * 2, r))
            pygame.draw.ellipse(surface, (*_NS_kurogari.PALETTE["void_dark"], 230),
                                (x - r + 3, y + 40 - r // 2 + 2,
                                 r * 2 - 6, r - 4))
            pygame.draw.ellipse(surface, (*_NS_kurogari.PALETTE["void_mid"], 200),
                                (x - r + 8, y + 40 - r // 2 + 4,
                                 r * 2 - 16, r - 8))
            # Swirling portal center
            for i in range(6):
                angle = phase * 3 + i * math.pi / 3
                inner_r = r * 0.5
                px = x + int(math.cos(angle) * inner_r)
                py = y + 40 + int(math.sin(angle) * inner_r * 0.4)
                _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_dark"],
                                        (px, py), 3)
                _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_hot"],
                                        (px, py), 1)
            # Center pulse
            pulse_r = int(4 + math.sin(phase * 4) * 2)
            for pr in range(pulse_r, 0, -1):
                alpha = _NS_kurogari._alpha(150 * (pulse_r - pr) / pulse_r)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                        (x, y + 40), pr)
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["white"], (x, y + 40, 1, 1))
            # Rising shadow tendrils
            for i in range(8):
                tendril_t = (phase * 0.8 + i * 0.12) % 1.0
                tx = x + int(math.sin(phase + i) * 15) + (i - 4) * 3
                ty = y + 40 - int(tendril_t * 40)
                alpha = _NS_kurogari._alpha(220 * (1 - tendril_t))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["void_mid"], alpha),
                                        (tx, ty), 3)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["mist_mid"], alpha),
                                        (tx, ty), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                 (tx, ty, 1, 1))
    # ============================================================
    # SKILL E - PINPOINT NINJA (phantom dash + explosion)
    # ============================================================
    def _draw_pinpoint_ninja(surface, boss, x, y, timer, phase):
        """Phantom rushes to target and explodes."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kurogari._target_position(boss, x, y)
        start_x = x + facing * 15
        start_y = y - 5
        if progress < 0.15:
            # Summoning phantom
            t = progress / 0.15
            cr = int(6 + t * 10)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kurogari._alpha(180 * (cr + 4 - r) / (cr + 4))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["void_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_mid"],
                                    (start_x, start_y), cr - 3)
            _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_light"],
                                    (start_x, start_y), max(1, cr - 5))
        else:
            # Phantom rushes
            t = (progress - 0.15) / 0.85
            dist = math.hypot(tx - start_x, ty - start_y)
            angle = math.atan2(ty - start_y, tx - start_x)
            head_x = int(start_x + math.cos(angle) * dist * t)
            head_y = int(start_y + math.sin(angle) * dist * t)
            # Phantom trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + math.cos(angle) * dist * trail_t)
                py = int(start_y + math.sin(angle) * dist * trail_t)
                alpha = _NS_kurogari._alpha(220 - i * 20)
                size = max(1, 7 - i)
                # Ghostly ninja silhouette
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["void_darkest"], alpha),
                                        (px, py), size)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["void_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["mist_mid"], alpha),
                                        (px, py), max(1, size - 2))
                # Crimson glow at trail
                if i < 5:
                    pygame.draw.rect(surface,
                                     (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                     (px, py, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_kurogari.PALETTE["crimson_shine"], alpha),
                                     (px, py, 1, 1))
            # Phantom head (leading form)
            phantom_pts = [
                (head_x, head_y - 8),
                (head_x - 6, head_y - 2),
                (head_x - 5, head_y + 5),
                (head_x + 5, head_y + 5),
                (head_x + 6, head_y - 2),
            ]
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in phantom_pts])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["void_darkest"], phantom_pts)
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["void_dark"], [
                (head_x, head_y - 6),
                (head_x - 4, head_y - 1),
                (head_x - 3, head_y + 3),
                (head_x + 3, head_y + 3),
                (head_x + 4, head_y - 1),
            ])
            # Glowing eyes on phantom
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                             (head_x - 2, head_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                             (head_x + 1, head_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                             (head_x - 2, head_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                             (head_x + 1, head_y - 2, 1, 1))
            # Wispy motion streaks around phantom
            for i in range(4):
                streak_angle = angle + math.pi + (i - 1.5) * 0.3
                streak_x = head_x + int(math.cos(streak_angle) * 8)
                streak_y = head_y + int(math.sin(streak_angle) * 8)
                pygame.draw.line(surface, _NS_kurogari.PALETTE["crimson_light"],
                                 (head_x, head_y), (streak_x, streak_y), 1)
            # EXPLOSION on arrival
            if t > 0.8:
                st = (t - 0.8) / 0.2
                radius = int(12 + st * 32)
                alpha = _NS_kurogari._alpha(240 * (1 - st))
                # Multi-ring burst
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_darkest"], alpha),
                                        (tx, ty), radius + 4, 3)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_mid"], alpha),
                                        (tx, ty), max(1, radius - 6), 2)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_shine"], alpha),
                                        (tx, ty), max(1, radius // 4))
                # Radial blades bursting outward
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.85)
                    pygame.draw.line(surface,
                                     (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_kurogari.PALETTE["crimson_shine"], alpha),
                                     (ex, ey, 2, 2))
                # Reveal eye icons around explosion (like passive)
                for i in range(3):
                    eye_angle = i * math.pi * 2 / 3
                    eye_x = tx + int(math.cos(eye_angle) * (radius + 8))
                    eye_y = ty + int(math.sin(eye_angle) * (radius + 8) * 0.7) - 8
                    pygame.draw.rect(surface,
                                     (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                     (eye_x - 1, eye_y, 3, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_kurogari.PALETTE["crimson_shine"], alpha),
                                     (eye_x, eye_y, 1, 1))
    # ============================================================
    # SKILL R - ANIMA SHADOW (transformation buff)
    # ============================================================
    def _draw_anima_ground(surface, boss, x, y, timer, phase):
        """Ground energy rings during transformation."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(35 + i * 8 + math.sin(phase * 2 + i) * 4)
            alpha = _NS_kurogari._alpha(200 - i * 50)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                    (x, y + 40), r, 2)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                    (x, y + 40), r, 1)
    def _draw_anima_foreground(surface, boss, x, y, timer, phase):
        """Massive aura + demonic wings/silhouette manifests."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Rising crimson columns
        for i in range(12):
            t = (phase * 1.3 + i * 0.1) % 1.0
            rx = x + int(math.sin(phase + i) * 26)
            ry = y + 30 - int(t * 70)
            alpha = _NS_kurogari._alpha(220 * (1 - t))
            if alpha > 0:
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_dark"], alpha),
                                        (rx, ry), 4)
                _NS_kurogari._aacircle(surface,
                                        (*_NS_kurogari.PALETTE["crimson_light"], alpha),
                                        (rx, ry), 2)
                pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                                 (rx, ry, 1, 1))
        # Demonic phantom wings expanding from back
        wing_scale = min(1.0, progress * 2)
        wing_span = int(65 * wing_scale)
        for side in (-1, 1):
            # Wing bones
            for i, angle_deg in enumerate((25, 5, -15, -35)):
                angle = math.radians(angle_deg + math.sin(phase) * 4)
                tip_x = x + side * int(math.cos(angle) * wing_span)
                tip_y = y - 8 - int(math.sin(angle) * wing_span)
                pygame.draw.line(surface, _NS_kurogari.PALETTE["shadow_deep"],
                                 (x, y - 8), (tip_x, tip_y), 3)
                pygame.draw.line(surface, _NS_kurogari.PALETTE["void_darkest"],
                                 (x, y - 8), (tip_x, tip_y), 2)
                # Blade tip
                _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_hot"],
                                        (tip_x, tip_y), 2)
                pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                                 (tip_x, tip_y, 1, 1))
            # Membrane
            membrane = [(x, y - 8)]
            for angle_deg in (25, 5, -15, -35):
                angle = math.radians(angle_deg + math.sin(phase) * 4)
                tip_x = x + side * int(math.cos(angle) * wing_span)
                tip_y = y - 8 - int(math.sin(angle) * wing_span)
                membrane.append((tip_x, tip_y))
            membrane.append((x, y + 15))
            wing_surf = pygame.Surface((wing_span * 2 + 40, wing_span * 2 + 40),
                                        pygame.SRCALPHA)
            offset_x = x - wing_span - 20
            offset_y = y - wing_span - 20
            local = [(p[0] - offset_x, p[1] - offset_y) for p in membrane]
            _NS_kurogari._poly(wing_surf,
                                (*_NS_kurogari.PALETTE["void_darkest"], 200), local)
            _NS_kurogari._poly(wing_surf,
                                (*_NS_kurogari.PALETTE["crimson_darkest"], 140), local)
            surface.blit(wing_surf, (offset_x, offset_y))
        # Orbiting shadow blades
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 45 + int(math.sin(phase * 1.5 + i) * 8)
            bx = x + int(math.cos(angle) * r)
            by = y + int(math.sin(angle) * r * 0.5)
            # Small blade shape
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["crimson_darkest"], [
                (bx, by - 3), (bx + 3, by), (bx, by + 3), (bx - 3, by),
            ])
            _NS_kurogari._poly(surface, _NS_kurogari.PALETTE["crimson_hot"], [
                (bx, by - 2), (bx + 2, by), (bx, by + 2), (bx - 2, by),
            ])
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                             (bx, by, 1, 1))
        # Demon head silhouette above (crown effect)
        crown_y = y - 45
        for r in range(7, 0, -1):
            alpha = _NS_kurogari._alpha(200 * (7 - r) / 7)
            _NS_kurogari._aacircle(surface,
                                    (*_NS_kurogari.PALETTE["crimson_hot"], alpha),
                                    (x, crown_y), r)
        _NS_kurogari._aacircle(surface, _NS_kurogari.PALETTE["crimson_shine"],
                                (x, crown_y), 2)
        pygame.draw.rect(surface, _NS_kurogari.PALETTE["white"], (x, crown_y, 1, 1))
        # Two glowing demon eyes above head
        for eye_off in (-4, 4):
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_hot"],
                             (x + eye_off, crown_y - 6, 2, 2))
            pygame.draw.rect(surface, _NS_kurogari.PALETTE["crimson_shine"],
                             (x + eye_off, crown_y - 6, 1, 1))



# ====================================================================
# MORVEKHAR (DEATHFORGED) - Mini Boss
# ====================================================================

class _NS_morvekhar:
    """Namespace morvekhar - Mini boss iron juggernaut dengan mace."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Iron armor (dark, weathered)
        "iron_darkest": (10, 12, 15),
        "iron_dark": (30, 35, 40),
        "iron_mid": (65, 72, 80),
        "iron_light": (120, 130, 140),
        "iron_shine": (190, 200, 210),
        "iron_edge": (230, 235, 245),
        # Rust / weathered accents
        "rust_dark": (55, 30, 15),
        "rust_mid": (110, 60, 30),
        "rust_light": (170, 100, 50),
        # Gold trim
        "gold_dark": (90, 65, 20),
        "gold_mid": (170, 130, 45),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 160),
        # Necromancy green (soul magic - Mordekaiser signature)
        "soul_darkest": (5, 25, 20),
        "soul_dark": (15, 65, 55),
        "soul_mid": (40, 155, 130),
        "soul_light": (100, 230, 200),
        "soul_hot": (180, 255, 235),
        "soul_shine": (230, 255, 250),
        # Cape (dark tattered)
        "cape_darkest": (5, 5, 8),
        "cape_dark": (20, 20, 28),
        "cape_mid": (45, 45, 60),
        "cape_light": (85, 85, 110),
        # Bone / skull accents
        "bone_dark": (60, 55, 45),
        "bone_mid": (140, 130, 110),
        "bone_light": (210, 200, 180),
        # Eyes (glowing green)
        "eye_socket": (2, 8, 5),
        "eye_glow": (100, 255, 200),
        "eye_hot": (200, 255, 240),
        # Ground effects
        "ground_dark": (5, 20, 15),
        "ground_mid": (30, 80, 65),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morvekhar._clamp(color)
        if _NS_morvekhar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvekhar._clamp(color)
        if _NS_morvekhar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morvekhar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morvekhar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_morvekhar._update_morv_attack_anim(boss)
        attacking = (
            getattr(boss, "_morv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind.
        _NS_morvekhar._draw_soul_aura(surface, x, y, pulse)
        _NS_morvekhar._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_morvekhar._draw_soul_cleave_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvekhar._draw_realm_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvekhar._draw_dash_trail(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_morvekhar._draw_morv_attack(surface, boss, x, y)
        else:
            _NS_morvekhar._draw_morv_idle(surface, boss, x, y)
        # W shield bubble (over body).
        if active_skill == "w":
            _NS_morvekhar._draw_ironbound_shield(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_morvekhar._draw_soul_cleave_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvekhar._draw_realm_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_morv_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_morv_previous_timer", 0))
        active = bool(getattr(boss, "_morv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._morv_attack_active = True
            boss._morv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._morv_attack_frame = int(getattr(boss, "_morv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._morv_attack_active = False
            boss._morv_attack_frame = 0
            active = False
        boss._morv_previous_timer = timer
        boss._morv_attack_progress = (
            min(1.0, getattr(boss, "_morv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_morv_idle(surface, boss, x, y):
        """Floating idle - heavy armor with slow bob."""
        bob = int(math.sin(boss.pulse * 0.5) * 3)  # slower/heavier bob
        sway = int(math.sin(boss.pulse * 0.3) * 1)
        _NS_morvekhar._draw_shadow(surface, x + sway, y + 50, phase=boss.pulse)
        _NS_morvekhar._draw_soul_wisps(surface, x + sway, y + 42, boss.pulse)
        _NS_morvekhar._draw_morv_body(surface, x + sway, y + bob,
                                       boss.direction, boss.pulse, "idle")
    def _draw_morv_attack(surface, boss, x, y):
        progress = getattr(boss, "_morv_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up (raise mace) → downward slam → recovery.
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-2 + t * 10)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(8 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_morvekhar._draw_shadow(surface, x + lunge, y + 50, phase=boss.pulse)
        _NS_morvekhar._draw_soul_wisps(surface, x + lunge, y + 42, boss.pulse, intense=True)
        _NS_morvekhar._draw_morv_body(surface, x + lunge, y + bob - lift,
                                       boss.direction, boss.pulse, "attack", progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_morv_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Heavy iron juggernaut body."""
        # Tattered cape behind.
        _NS_morvekhar._draw_tattered_cape(surface, cx, cy, facing, phase)
        # Legs (heavy armored, planted or slightly floating).
        _NS_morvekhar._draw_heavy_legs(surface, cx, cy + 14, facing, phase)
        # Torso (huge armored chest).
        _NS_morvekhar._draw_iron_torso(surface, cx, cy, facing, phase)
        # Back arm (holds cape/relaxed).
        _NS_morvekhar._draw_back_arm(surface, cx, cy, facing, phase)
        # Head (spiked helm).
        _NS_morvekhar._draw_iron_helm(surface, cx + facing * 1, cy - 22, facing, phase)
        # Front arm with mace weapon.
        _NS_morvekhar._draw_mace_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_tattered_cape(surface, cx, cy, facing, phase):
        """Dark tattered cape."""
        sway = math.sin(phase * 0.7) * 3
        back = -facing
        cape_top = (cx + back * 6, cy - 16)
        cape_shoulder_a = (cx + back * 10, cy - 12)
        cape_shoulder_b = (cx + back * 12, cy - 6)
        cape_mid = (cx + back * 16 + int(sway), cy + 4)
        cape_bot1 = (cx + back * 20 + int(sway * 1.5), cy + 16)
        cape_bot2 = (cx + back * 14 + int(sway), cy + 22)
        cape_bot3 = (cx + back * 6, cy + 20)
        cape_side = (cx + back * 3, cy - 10)
        pts = [cape_top, cape_shoulder_a, cape_shoulder_b, cape_mid,
               cape_bot1, cape_bot2, cape_bot3, cape_side]
        # Shadow.
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in pts])
        # Cape layers.
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["cape_darkest"], pts)
        pts_inner = [
            cape_top,
            cape_shoulder_a,
            (cape_shoulder_b[0] + facing, cape_shoulder_b[1]),
            (cape_mid[0] + facing * 2, cape_mid[1]),
            (cape_bot1[0] + facing * 2, cape_bot1[1] - 2),
            (cape_bot3[0] + facing * 2, cape_bot3[1] - 2),
            cape_side,
        ]
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["cape_dark"], pts_inner)
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["cape_mid"], [
            (cape_top[0] + facing, cape_top[1] + 1),
            (cape_shoulder_a[0] + facing, cape_shoulder_a[1] + 1),
            (cape_mid[0] + facing * 5, cape_mid[1]),
            (cape_bot3[0] + facing * 3, cape_bot3[1] - 4),
            (cape_side[0] + facing, cape_side[1] + 1),
        ])
        # Tattered edges (jagged bottom).
        for i, (px_off, py_off) in enumerate([(-3, 2), (0, 3), (3, 2), (6, 4)]):
            tear_x = cape_bot2[0] + int(px_off * -facing)
            tear_y = cape_bot2[1] + py_off
            pygame.draw.line(surface, _NS_morvekhar.PALETTE["cape_darkest"],
                             (tear_x, cape_bot2[1] - 2),
                             (tear_x, tear_y), 2)
        # Cape edge highlights.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["cape_light"],
                              cape_top, cape_shoulder_a, 1)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["cape_light"],
                              (cape_bot1[0], cape_bot1[1] - 1),
                              (cape_bot2[0], cape_bot2[1] - 1), 1)
        # Green soul glow at cape edges.
        for i, edge in enumerate([cape_bot1, cape_bot2]):
            alpha = _NS_morvekhar._alpha(140 + math.sin(phase * 2 + i) * 40)
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                     edge, 3)
            pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                             (edge[0], edge[1], 1, 1))
    def _draw_heavy_legs(surface, cx, cy, facing, phase):
        """Heavy armored plated legs (floating slightly)."""
        sway = math.sin(phase * 0.5) * 1
        for side in (-1, 1):
            hip = (cx + side * 5, cy - 3)
            knee = (cx + side * 6, cy + 7 + int(sway))
            foot = (cx + side * 6, cy + 16 + int(sway))
            # Shadow.
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                                  (hip[0] + 1, hip[1] + 1),
                                  (knee[0] + 1, knee[1] + 1), 8)
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                                  (knee[0] + 1, knee[1] + 1),
                                  (foot[0] + 1, foot[1] + 1), 7)
            # Thigh armor (thick plates).
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"], hip, knee, 8)
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"], hip, knee, 6)
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                                  (hip[0] - 1, hip[1]), (knee[0] - 1, knee[1]), 3)
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_light"],
                                  (hip[0] - 2, hip[1]), (knee[0] - 2, knee[1]), 1)
            # Shin armor.
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"], knee, foot, 7)
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"], knee, foot, 5)
            _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                                  (knee[0] - 1, knee[1]), (foot[0] - 1, foot[1]), 2)
            # Knee guard (spiked).
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], [
                (knee[0] - 4, knee[1] - 2),
                (knee[0] + 4, knee[1] - 2),
                (knee[0] + 5, knee[1] + 2),
                (knee[0] - 5, knee[1] + 2),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
                (knee[0] - 3, knee[1] - 1),
                (knee[0] + 3, knee[1] - 1),
                (knee[0] + 4, knee[1] + 1),
                (knee[0] - 4, knee[1] + 1),
            ])
            # Knee spike.
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
                (knee[0] - 2, knee[1] - 2),
                (knee[0] + 2, knee[1] - 2),
                (knee[0], knee[1] - 5),
            ])
            # Gold accent.
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["gold_mid"],
                             (knee[0] - 1, knee[1], 2, 1))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_light"],
                             (knee[0], knee[1], 1, 1))
            # Massive iron boot.
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["shadow_deep"], [
                (foot[0] - 5, foot[1] - 1),
                (foot[0] + 6, foot[1] - 1),
                (foot[0] + 5, foot[1] + 4),
                (foot[0] - 4, foot[1] + 4),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], [
                (foot[0] - 5, foot[1] - 2),
                (foot[0] + 6, foot[1] - 2),
                (foot[0] + 5, foot[1] + 3),
                (foot[0] - 4, foot[1] + 3),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
                (foot[0] - 4, foot[1] - 1),
                (foot[0] + 5, foot[1] - 1),
                (foot[0] + 4, foot[1] + 2),
                (foot[0] - 3, foot[1] + 2),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_mid"], [
                (foot[0] - 3, foot[1]),
                (foot[0] + 4, foot[1]),
                (foot[0] + 3, foot[1] + 1),
                (foot[0] - 2, foot[1] + 1),
            ])
            # Boot spikes on top.
            for spike_off in (-2, 2):
                _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
                    (foot[0] + spike_off - 1, foot[1] - 2),
                    (foot[0] + spike_off + 1, foot[1] - 2),
                    (foot[0] + spike_off, foot[1] - 4),
                ])
            # Rust.
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["rust_mid"],
                             (foot[0] - 2, foot[1] + 2, 3, 1))
    def _draw_iron_torso(surface, cx, cy, facing, phase):
        """Massive armored chest plate."""
        breath = math.sin(phase * 0.6) * 1
        # Main torso (wide/bulky).
        torso = [
            (cx - 14, cy - 14),   # left shoulder outer
            (cx - 16, cy - 8),    # left arm socket
            (cx - 13, cy),        # left rib
            (cx - 10, cy + 8),    # left waist
            (cx - 6, cy + 14),    # left hip
            (cx + 6, cy + 14),    # right hip
            (cx + 10, cy + 8),    # right waist
            (cx + 13, cy),        # right rib
            (cx + 16, cy - 8),    # right arm socket
            (cx + 14, cy - 14),   # right shoulder outer
            (cx + 6, cy - 16),    # collar right
            (cx - 6, cy - 16),    # collar left
        ]
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in torso])
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], torso)
        # Base armor plate.
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
            (cx - 13, cy - 13), (cx - 15, cy - 8), (cx - 12, cy),
            (cx - 9, cy + 7), (cx - 5, cy + 13), (cx + 5, cy + 13),
            (cx + 9, cy + 7), (cx + 12, cy), (cx + 15, cy - 8),
            (cx + 13, cy - 13), (cx + 5, cy - 15), (cx - 5, cy - 15),
        ])
        # Mid highlight (raised chest plate).
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_mid"], [
            (cx - 10, cy - 12), (cx - 12, cy - 6), (cx - 10, cy + 2),
            (cx - 7, cy + 8), (cx + 7, cy + 8), (cx + 10, cy + 2),
            (cx + 12, cy - 6), (cx + 10, cy - 12),
        ])
        # Central chest emblem (large plate).
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
            (cx - 6, cy - 10), (cx - 8, cy - 4), (cx - 5, cy + 4),
            (cx + 5, cy + 4), (cx + 8, cy - 4), (cx + 6, cy - 10),
        ])
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
            (cx - 5, cy - 9), (cx - 7, cy - 4), (cx - 4, cy + 3),
            (cx + 4, cy + 3), (cx + 7, cy - 4), (cx + 5, cy - 9),
        ])
        # Center jewel (soul essence - glowing green).
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        jewel_x, jewel_y = cx, cy - 3
        for r in range(6, 0, -1):
            alpha = _NS_morvekhar._alpha(150 * (6 - r) / 6 * pulse)
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                     (jewel_x, jewel_y), r)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_darkest"], (jewel_x, jewel_y), 4)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_dark"], (jewel_x, jewel_y), 3)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_mid"], (jewel_x, jewel_y), 2)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_light"], (jewel_x, jewel_y), 1)
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_shine"], (jewel_x, jewel_y, 1, 1))
        # Armor plate segments/lines.
        pygame.draw.line(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                         (cx - 8, cy - 4), (cx + 8, cy - 4), 1)
        pygame.draw.line(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                         (cx - 7, cy + 4), (cx + 7, cy + 4), 1)
        # Rivets.
        for rx, ry in [(cx - 9, cy - 6), (cx + 9, cy - 6),
                       (cx - 8, cy + 6), (cx + 8, cy + 6)]:
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_shine"], (rx, ry, 1, 1))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_dark"], (rx + 1, ry + 1, 1, 1))
        # Massive spiked pauldrons.
        for side in (-1, 1):
            sx = cx + side * 14
            sy = cy - 12
            # Base pauldron.
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["shadow_deep"], [
                (sx + side * 1, sy - 5),
                (sx + side * 7, sy - 2),
                (sx + side * 8, sy + 4),
                (sx + side * 3, sy + 7),
                (sx - side * 3, sy + 4),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], [
                (sx, sy - 6),
                (sx + side * 6, sy - 3),
                (sx + side * 7, sy + 3),
                (sx + side * 2, sy + 6),
                (sx - side * 4, sy + 3),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
                (sx, sy - 5),
                (sx + side * 5, sy - 2),
                (sx + side * 6, sy + 2),
                (sx + side * 1, sy + 5),
                (sx - side * 3, sy + 2),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_mid"], [
                (sx, sy - 3),
                (sx + side * 3, sy - 1),
                (sx + side * 4, sy + 1),
                (sx, sy + 3),
                (sx - side * 2, sy + 1),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
                (sx, sy - 2),
                (sx + side * 2, sy),
                (sx, sy + 1),
                (sx - side * 1, sy),
            ])
            # Big spikes on pauldron.
            for spike_i, (sp_off_x, sp_off_y, sp_len) in enumerate([
                (5, -3, 6), (7, 0, 7), (5, 3, 5),
            ]):
                base_x = sx + side * sp_off_x
                base_y = sy + sp_off_y
                tip_x = base_x + side * sp_len
                tip_y = base_y - 1
                # Spike.
                _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], [
                    (base_x, base_y - 2),
                    (base_x, base_y + 2),
                    (tip_x, tip_y),
                ])
                _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
                    (base_x + side, base_y - 1),
                    (base_x + side, base_y + 1),
                    (tip_x - side, tip_y),
                ])
                _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
                    (base_x + side * 2, base_y),
                    (tip_x - side, tip_y),
                    (tip_x, tip_y),
                ])
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_edge"],
                                 (tip_x, tip_y, 1, 1))
            # Gold trim.
            pygame.draw.line(surface, _NS_morvekhar.PALETTE["gold_mid"],
                             (sx - side * 3, sy + 5), (sx + side * 3, sy + 6), 1)
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["gold_light"],
                             (sx, sy + 5, 1, 1))
            # Soul glow at pauldron socket.
            glow_alpha = _NS_morvekhar._alpha(180 + math.sin(phase * 2 + side) * 40)
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_mid"], glow_alpha),
                                     (sx - side * 2, sy + 1), 2)
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_light"],
                             (sx - side * 2, sy + 1, 1, 1))
        # Belt/hip armor.
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                         (cx - 10, cy + 11, 20, 4))
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_dark"],
                         (cx - 9, cy + 12, 18, 2))
        # Belt buckle (gold with green).
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["gold_dark"],
                         (cx - 4, cy + 11, 8, 4))
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["gold_mid"],
                         (cx - 3, cy + 12, 6, 2))
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["gold_light"],
                         (cx - 2, cy + 12, 4, 1))
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_light"],
                         (cx, cy + 13, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm (relaxed, armored)."""
        back = -facing
        sway = math.sin(phase * 0.5) * 1
        shoulder = (cx + back * 12, cy - 10)
        elbow = (cx + back * 15, cy - 1 + int(sway))
        hand = (cx + back * 13, cy + 8 + int(sway))
        # Shadow.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 5)
        # Upper arm (armored).
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"], shoulder, elbow, 6)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"], shoulder, elbow, 4)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 2)
        # Forearm (bracer).
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"], elbow, hand, 5)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"], elbow, hand, 3)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                              (elbow[0] - 1, elbow[1]),
                              (hand[0] - 1, hand[1]), 1)
        # Elbow guard.
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_dark"], elbow, 3)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_light"], elbow, 1)
        # Gauntlet fist.
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_darkest"], hand, 4)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_dark"], hand, 3)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_mid"],
                                 (hand[0] - 1, hand[1] - 1), 1)
        # Knuckle spikes.
        for k_off in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_light"],
                             (hand[0] + k_off, hand[1] - 3, 1, 1))
    def _draw_iron_helm(surface, cx, cy, facing, phase):
        """Spiked demonic helmet with glowing eyes."""
        # Helm main shape (tall, angular).
        helm = [
            (cx - 8, cy + 4),     # left jaw
            (cx - 10, cy),        # left cheek
            (cx - 9, cy - 5),     # left temple
            (cx - 6, cy - 10),    # left forehead
            (cx - 2, cy - 12),    # top left
            (cx + 3, cy - 12),    # top right
            (cx + 7, cy - 10),    # right forehead
            (cx + 10, cy - 5),    # right temple
            (cx + 10, cy),        # right cheek
            (cx + 8, cy + 4),     # right jaw
            (cx + 5, cy + 7),     # chin right
            (cx - 5, cy + 7),     # chin left
        ]
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in helm])
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], helm)
        # Base helm color.
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
            (cx - 7, cy + 4), (cx - 9, cy), (cx - 8, cy - 5),
            (cx - 5, cy - 9), (cx - 1, cy - 11), (cx + 2, cy - 11),
            (cx + 6, cy - 9), (cx + 9, cy - 5), (cx + 9, cy),
            (cx + 7, cy + 4), (cx + 4, cy + 6), (cx - 4, cy + 6),
        ])
        # Face plate mid highlight.
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_mid"], [
            (cx - 6, cy + 3), (cx - 7, cy), (cx - 6, cy - 4),
            (cx - 3, cy - 8), (cx, cy - 10), (cx + 3, cy - 8),
            (cx + 6, cy - 4), (cx + 7, cy), (cx + 5, cy + 3),
            (cx + 3, cy + 5), (cx - 3, cy + 5),
        ])
        # Central face ridge (raised).
        _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
            (cx - 2, cy - 6), (cx - 3, cy - 2), (cx - 1, cy + 3),
            (cx + 2, cy + 3), (cx + 3, cy - 2), (cx + 2, cy - 6),
        ])
        pygame.draw.line(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                         (cx, cy - 6), (cx, cy + 3), 1)
        # HELM CROWN SPIKES (top).
        _NS_morvekhar._draw_helm_spikes(surface, cx, cy, facing, phase)
        # EYE SLIT with glowing green eyes.
        _NS_morvekhar._draw_helm_eyes(surface, cx, cy, phase)
        # Mouth grill (horizontal lines).
        for y_off in (2, 4):
            pygame.draw.line(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                             (cx - 3, cy + y_off), (cx + 3, cy + y_off), 1)
        # Cheek plate rivets.
        for rx, ry in [(cx - 7, cy), (cx + 7, cy), (cx - 6, cy + 3), (cx + 6, cy + 3)]:
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_shine"], (rx, ry, 1, 1))
        # Gold trim on brow.
        pygame.draw.line(surface, _NS_morvekhar.PALETTE["gold_mid"],
                         (cx - 5, cy - 8), (cx + 5, cy - 8), 1)
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["gold_light"],
                         (cx, cy - 8, 1, 1))
    def _draw_helm_spikes(surface, cx, cy, facing, phase):
        """Crown of spikes on top of helm."""
        wave = math.sin(phase * 0.4) * 1
        # Multiple spikes at top.
        for i, (dx, dy, length) in enumerate([
            (-6, -10, 4),
            (-3, -12, 6),
            (0, -13, 8),  # center tallest
            (3, -12, 6),
            (6, -10, 4),
        ]):
            offset = int(wave) if i % 2 == 0 else -int(wave)
            base_x = cx + dx
            base_y = cy + dy
            tip_y = base_y - length + offset
            # Shadow.
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["shadow_deep"], [
                (base_x - 1, base_y + 1),
                (base_x + 3, base_y + 1),
                (base_x + 1, tip_y + 1),
            ])
            # Spike body.
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"], [
                (base_x - 2, base_y),
                (base_x + 2, base_y),
                (base_x, tip_y),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
                (base_x - 1, base_y),
                (base_x + 1, base_y),
                (base_x, tip_y),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_mid"], [
                (base_x, base_y),
                (base_x + 1, base_y),
                (base_x, tip_y),
            ])
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_light"],
                             (base_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_edge"],
                             (base_x, tip_y, 1, 1))
            # Soul glow at spike tip (for tallest ones).
            if length >= 6:
                glow_alpha = _NS_morvekhar._alpha(160 + math.sin(phase * 2 + i) * 40)
                pygame.draw.rect(surface,
                                 (*_NS_morvekhar.PALETTE["soul_mid"], glow_alpha),
                                 (base_x, tip_y - 1, 1, 1))
    def _draw_helm_eyes(surface, cx, cy, phase):
        """Glowing green eye slits."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 5
            # Deep socket.
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["eye_socket"],
                             (ex - 1, ey, 3, 2))
            # Green glow halo.
            for r in range(6, 0, -1):
                alpha = _NS_morvekhar._alpha(100 * (6 - r) / 6 * pulse)
                _NS_morvekhar._aacircle(surface,
                                         (*_NS_morvekhar.PALETTE["eye_glow"], alpha),
                                         (ex, ey), r)
            # Eye core (bright green slit).
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_mid"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["eye_glow"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["eye_hot"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_mace_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding massive spiked mace - overhead slam."""
        shoulder = (cx + facing * 12, cy - 10)
        # Arm angle based on attack progress.
        # Angle 0 = arm horizontal forward
        # Negative angle = arm UP (overhead)
        # Positive angle = arm DOWN
        if action == "attack":
            if attack_progress < 0.4:
                # Wind-up: raise mace HIGH above head.
                t = attack_progress / 0.4
                # Start from resting (slight down) → raise fully up-back
                arm_angle = -math.pi * 0.15 - t * math.pi * 0.7  # goes from -0.15π to -0.85π (up & back)
                mace_extra = int(t * 3)
            elif attack_progress < 0.65:
                # SLAM DOWN! Fast arc from overhead to forward-down.
                t = (attack_progress - 0.4) / 0.25
                # From -0.85π (overhead) → +0.35π (down-forward)
                arm_angle = -math.pi * 0.85 + t * math.pi * 1.2
                mace_extra = int(3 + t * 2)  # mace extends during slam
            else:
                # Recovery: return to idle position.
                t = (attack_progress - 0.65) / 0.35
                arm_angle = math.pi * 0.35 - t * math.pi * 0.2
                mace_extra = int(5 - t * 5)
        else:
            # Idle: mace held out to side, slightly down.
            hover = math.sin(phase * 0.7) * 2
            arm_angle = math.pi * 0.15
            mace_extra = int(hover)
        # Calc elbow position (arm extends from shoulder at arm_angle).
        arm_len = 10
        elbow_x = shoulder[0] + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder[1] + int(math.sin(arm_angle) * arm_len)
        # Forearm extends further in same direction (slightly bent).
        forearm_angle = arm_angle + math.pi * 0.1
        forearm_len = 10
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)
        # Mace head extends from hand in same direction.
        mace_len = 14 + mace_extra
        mace_angle = forearm_angle
        mace_head_x = hand_x + int(math.cos(mace_angle) * mace_len) * facing
        mace_head_y = hand_y + int(math.sin(mace_angle) * mace_len)
        # === DRAW ARM ===
        # Upper arm shadow.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow_x + 1, elbow_y + 1), 7)
        # Upper arm.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                              shoulder, (elbow_x, elbow_y), 7)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"],
                              shoulder, (elbow_x, elbow_y), 5)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow_x, elbow_y - 1), 2)
        # Forearm.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 6)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                              (elbow_x - 1, elbow_y),
                              (hand_x - 1, hand_y), 2)
        # Elbow guard.
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_darkest"], (elbow_x, elbow_y), 3)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_dark"], (elbow_x, elbow_y), 2)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_light"], (elbow_x, elbow_y), 1)
        # Gauntlet fist.
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_darkest"], (hand_x, hand_y), 5)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_dark"], (hand_x, hand_y), 4)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_mid"],
                                (hand_x - 1, hand_y - 1), 2)
        # === DRAW MACE ===
        _NS_morvekhar._draw_mace(surface, hand_x, hand_y, mace_head_x, mace_head_y,
                                 mace_angle, facing, phase, action, attack_progress)
    def _draw_mace(surface, hand_x, hand_y, head_x, head_y, angle, facing,
                    phase, action, attack_progress):
        """Draw the mace - handle + spiked head."""
        # === HANDLE ===
        # Shadow.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1),
                              (head_x + 1, head_y + 1), 4)
        # Wooden/iron handle.
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                              (hand_x, hand_y), (head_x, head_y), 4)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_dark"],
                              (hand_x, hand_y), (head_x, head_y), 3)
        _NS_morvekhar._aaline(surface, _NS_morvekhar.PALETTE["iron_mid"],
                              (hand_x, hand_y - 1), (head_x, head_y - 1), 1)
        # Handle wrapping (gold rings).
        for t_wrap in (0.3, 0.55, 0.8):
            wx = int(hand_x + (head_x - hand_x) * t_wrap)
            wy = int(hand_y + (head_y - hand_y) * t_wrap)
            _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["gold_dark"], (wx, wy), 2)
            _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["gold_mid"], (wx, wy), 1)
        # === MACE HEAD (large spiked ball) ===
        # Motion blur trail during swing.
        if action == "attack" and 0.4 < attack_progress < 0.7:
            blur_t = (attack_progress - 0.4) / 0.3
            for i in range(4):
                b_x = int(head_x - (head_x - hand_x) * 0.15 * i)
                b_y = int(head_y - (head_y - hand_y) * 0.15 * i)
                alpha = _NS_morvekhar._alpha(150 * (1 - i / 4) * blur_t)
                _NS_morvekhar._aacircle(surface,
                                         (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                         (b_x, b_y), 8 - i)
                _NS_morvekhar._aacircle(surface,
                                         (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                                         (b_x, b_y), 5 - i)
        # Mace head shadow.
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                                 (head_x + 2, head_y + 2), 10)
        # Spikes around mace head (8 directions).
        for i in range(8):
            spike_angle = i * math.pi / 4 + angle * 0.5
            base_x = head_x + int(math.cos(spike_angle) * 7)
            base_y = head_y + int(math.sin(spike_angle) * 7)
            tip_x = head_x + int(math.cos(spike_angle) * 13)
            tip_y = head_y + int(math.sin(spike_angle) * 13)
            # Perpendicular for spike base width.
            perp_x = -math.sin(spike_angle)
            perp_y = math.cos(spike_angle)
            base_a = (base_x + int(perp_x * 2), base_y + int(perp_y * 2))
            base_b = (base_x - int(perp_x * 2), base_y - int(perp_y * 2))
            # Spike.
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                                [base_a, base_b, (tip_x, tip_y)])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_dark"], [
                (int((base_a[0] + base_x) / 2), int((base_a[1] + base_y) / 2)),
                (int((base_b[0] + base_x) / 2), int((base_b[1] + base_y) / 2)),
                (tip_x, tip_y),
            ])
            _NS_morvekhar._poly(surface, _NS_morvekhar.PALETTE["iron_light"], [
                (base_x, base_y),
                (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2)),
                (tip_x, tip_y),
            ])
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_edge"],
                             (tip_x, tip_y, 1, 1))
        # Main mace ball body.
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_darkest"], (head_x, head_y), 8)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_dark"], (head_x, head_y), 7)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_mid"], (head_x - 1, head_y - 1), 5)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_light"], (head_x - 2, head_y - 2), 2)
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_edge"],
                         (head_x - 2, head_y - 2, 1, 1))
        # Central soul core (glowing green inside mace).
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_morvekhar._alpha(150 * (5 - r) / 5 * pulse)
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                     (head_x, head_y), r)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_darkest"], (head_x, head_y), 3)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_dark"], (head_x, head_y), 2)
        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["soul_light"], (head_x, head_y), 1)
        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_shine"], (head_x, head_y, 1, 1))
        # Sparks around mace during attack.
        if action == "attack" and 0.35 < attack_progress < 0.75:
            for i in range(8):
                spark_angle = phase * 5 + i * math.pi / 4
                sx = head_x + int(math.cos(spark_angle) * 15)
                sy = head_y + int(math.sin(spark_angle) * 15)
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_shine"], (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, phase=0):
        """Heavy shadow (this is a big juggernaut)."""
        offset_y = int(math.sin(phase * 0.5) * 1)
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 5, 3, 180), (5, 8, 140, 14))
        pygame.draw.ellipse(shadow, (10, 40, 30, 120), (12, 10, 126, 10))
        surface.blit(shadow, (x - 75, y - 15 + offset_y))
    def _draw_soul_wisps(surface, cx, cy, phase, intense=False):
        """Green soul wisps rising from below (necromancy floating)."""
        strength = 1.4 if intense else 1.0
        # Wisps rising.
        for i in range(9):
            wisp_t = (phase * 0.5 + i * 0.13) % 1.0
            wx = cx - 18 + i * 4 + int(math.sin(phase + i) * 3)
            wy = cy + 12 - int(wisp_t * 24)
            alpha = _NS_morvekhar._alpha(220 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_darkest"], alpha),
                                         (wx, wy), 3)
                _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_dark"], alpha),
                                         (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                                 (wx, wy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_hot"], alpha),
                                 (wx, wy - 2, 1, 1))
        # Ghost skulls rising (subtle - necromancer theme).
        for i in range(3):
            skull_t = (phase * 0.3 + i * 0.35) % 1.0
            sx = cx - 15 + i * 15 + int(math.sin(phase + i * 2) * 4)
            sy = cy + 8 - int(skull_t * 28)
            alpha = _NS_morvekhar._alpha(140 * (1 - skull_t) * strength)
            if alpha > 0:
                # Tiny ghost skull.
                _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["bone_mid"], alpha),
                                         (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["shadow_deep"], alpha),
                                 (sx - 1, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["shadow_deep"], alpha),
                                 (sx + 1, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                                 (sx - 1, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                                 (sx + 1, sy, 1, 1))
    def _draw_soul_aura(surface, x, y, phase):
        """Green necromancy aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_morvekhar._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvekhar._aacircle(aura, (*_NS_morvekhar.PALETTE["soul_darkest"], alpha),
                                         (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_morvekhar._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvekhar._aacircle(aura, (*_NS_morvekhar.PALETTE["soul_dark"], alpha),
                                         (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_morvekhar._alpha((35 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvekhar._aacircle(aura, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                         (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating soul embers.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Green ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvekhar.PALETTE["soul_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_morvekhar.PALETTE["soul_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_morvekhar.PALETTE["soul_mid"], 230),
                            (25, 22, 120, 18), 1)
        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morvekhar.PALETTE["soul_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_morvekhar.PALETTE["soul_hot"],
                                        _NS_morvekhar._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: SOUL CLEAVE (mace swing with lingering AOE)
    # ============================================================
    def _draw_soul_cleave_ground(surface, boss, x, y, timer, phase):
        """Lingering green ground puddle in swing arc."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Puddle in front of boss.
        puddle_x = x + facing * 30
        puddle_y = y + 44
        r = int(45 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_darkest"], 200),
                                (puddle_x - r, puddle_y - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_dark"], 180),
                                (puddle_x - r + 3, puddle_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_mid"], 140),
                                (puddle_x - r + 8, puddle_y - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Bubbling sparkles.
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = puddle_x + int(math.cos(angle) * r * 0.6)
                sy = puddle_y + int(math.sin(angle) * r * 0.25)
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_light"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_hot"], (sx, sy, 1, 1))
    def _draw_soul_cleave_foreground(surface, boss, x, y, timer, phase):
        """Rising green energy from puddle + swing arc."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big cleave arc (initial swing).
        if progress < 0.35:
            t = progress / 0.35
            arc_alpha = _NS_morvekhar._alpha(240 * (1 - t))
            # Arc trail from boss forward.
            arc_center_x = x + facing * 15
            arc_center_y = y - 5
            arc_r = int(35 + t * 15)
            # Draw arc as multiple lines forming crescent.
            for i in range(-4, 5):
                arc_angle = -math.pi * 0.3 + i * math.pi * 0.08
                start_x = arc_center_x + int(math.cos(arc_angle) * (arc_r - 5)) * facing
                start_y = arc_center_y + int(math.sin(arc_angle) * (arc_r - 5))
                end_x = arc_center_x + int(math.cos(arc_angle) * arc_r) * facing
                end_y = arc_center_y + int(math.sin(arc_angle) * arc_r)
                pygame.draw.line(surface, (*_NS_morvekhar.PALETTE["soul_mid"], arc_alpha),
                                 (start_x, start_y), (end_x, end_y), 3)
                pygame.draw.line(surface, (*_NS_morvekhar.PALETTE["soul_hot"], arc_alpha),
                                 (start_x, start_y), (end_x, end_y), 1)
        # Rising fume from puddle.
        puddle_x = x + facing * 30
        puddle_y = y + 44
        r = int(45 * min(1.0, progress * 2))
        if r > 5:
            for i in range(6):
                col_angle = i * math.pi * 2 / 6 + phase * 0.1
                col_x = puddle_x + int(math.cos(col_angle) * r * 0.5)
                col_y_base = puddle_y + int(math.sin(col_angle) * r * 0.2)
                for layer in range(5):
                    layer_t = (phase * 0.6 + i * 0.3 + layer * 0.2) % 1.0
                    layer_y = col_y_base - int(layer_t * 20)
                    layer_alpha = _NS_morvekhar._alpha(180 * (1 - layer_t))
                    layer_w = int(5 + layer_t * 3)
                    layer_h = int(2 + layer_t * 2)
                    pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_dark"], layer_alpha),
                                        (col_x - layer_w, layer_y - layer_h,
                                         layer_w * 2, layer_h * 2))
                    pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_mid"], layer_alpha),
                                        (col_x - layer_w + 1, layer_y - layer_h + 1,
                                         layer_w * 2 - 2, layer_h * 2 - 2))
                    pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_light"], layer_alpha),
                                     (col_x, layer_y, 1, 1))
                    pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_hot"], layer_alpha),
                                     (col_x, layer_y - 1, 1, 1))
    # ============================================================
    # SKILL W: INDESTRUCTIBLE (aura shield)
    # ============================================================
    def _draw_ironbound_shield(surface, boss, x, y, timer, phase):
        """Rotating green aura shield around boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Bubble radius (breathing).
        breath = math.sin(phase * 1.5) * 3
        r = 55 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Ring layers.
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 150), (1, 200),
        ]):
            _NS_morvekhar._aacircle(bubble, (*_NS_morvekhar.PALETTE["soul_dark"], alpha_val),
                                     center, r - i, thickness)
            _NS_morvekhar._aacircle(bubble, (*_NS_morvekhar.PALETTE["soul_mid"], alpha_val),
                                     center, r - i - 1, 1)
        # Rotating shield plates (hexagon pattern around edge).
        for i in range(12):
            angle = phase * 1.2 + i * math.pi / 6
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            # Small shield plate.
            plate_alpha = _NS_morvekhar._alpha(200)
            _NS_morvekhar._poly(bubble, (*_NS_morvekhar.PALETTE["soul_dark"], plate_alpha), [
                (sx - 2, sy),
                (sx, sy - 3),
                (sx + 2, sy),
                (sx, sy + 3),
            ])
            _NS_morvekhar._poly(bubble, (*_NS_morvekhar.PALETTE["soul_mid"], plate_alpha), [
                (sx - 1, sy),
                (sx, sy - 2),
                (sx + 1, sy),
                (sx, sy + 2),
            ])
            pygame.draw.rect(bubble, _NS_morvekhar.PALETTE["soul_light"], (sx, sy, 1, 1))
            pygame.draw.rect(bubble, _NS_morvekhar.PALETTE["soul_hot"], (sx, sy, 1, 1))
        # Inner rune circle.
        for i in range(6):
            angle = -phase * 0.8 + i * math.pi / 3
            inner_r = r - 12
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            # Rune symbol (small cross).
            pygame.draw.line(bubble, (*_NS_morvekhar.PALETTE["soul_light"], 200),
                             (bx - 2, by), (bx + 2, by), 1)
            pygame.draw.line(bubble, (*_NS_morvekhar.PALETTE["soul_light"], 200),
                             (bx, by - 2), (bx, by + 2), 1)
            pygame.draw.rect(bubble, _NS_morvekhar.PALETTE["soul_hot"], (bx, by, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Sparks bursting outward.
        for i in range(8):
            spark_t = (phase * 0.8 + i * 0.125) % 1.0
            angle = i * math.pi / 4 + phase * 0.3
            spark_r = r + int(spark_t * 15)
            sx = x + int(math.cos(angle) * spark_r)
            sy = y + int(math.sin(angle) * spark_r)
            alpha = _NS_morvekhar._alpha(240 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_hot"], alpha), (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_shine"], alpha), (sx, sy, 1, 1))
    # ============================================================
    # SKILL E: DEATH'S ADVANCE (dash trail)
    # ============================================================
    def _draw_dash_trail(surface, boss, x, y, timer, phase):
        """Green dash trail behind boss."""
        facing = boss.direction
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Trail streaks.
        for i in range(9):
            offset = (i + 1) * 8
            tx = x - facing * offset
            ty = y + int(math.sin(phase + i) * 2)
            alpha = _NS_morvekhar._alpha(240 * (1 - i / 9) * (1 - progress * 0.4))
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_darkest"], alpha),
                                     (tx, ty), max(2, 10 - i))
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_dark"], alpha),
                                     (tx, ty), max(1, 7 - i))
            _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                     (tx, ty), max(1, 5 - i))
            pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                             (tx, ty, 2, 2))
            pygame.draw.rect(surface, (*_NS_morvekhar.PALETTE["soul_hot"], alpha),
                             (tx, ty, 1, 1))
        # Speed lines.
        for i in range(5):
            line_y_off = (i - 2) * 4
            line_x = x - facing * 20
            line_end_x = x - facing * 50
            alpha = _NS_morvekhar._alpha(180 * (1 - progress * 0.6))
            pygame.draw.line(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                             (line_x, y + line_y_off),
                             (line_end_x, y + line_y_off), 1)
    # ============================================================
    # SKILL R: REALM OF DEATH (portal ultimate)
    # ============================================================
    def _draw_realm_ground(surface, boss, x, y, timer, phase):
        """Ground portal circle."""
        tx, ty = _NS_morvekhar._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 2))
        if r > 5:
            # Dark portal ground.
            pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_dark"], 200),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["ground_dark"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Runes at edge.
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.2
                rx = tx + int(math.cos(angle) * r * 0.9)
                ry = ty + int(math.sin(angle) * r * 0.35)
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_hot"], (rx - 1, ry, 2, 1))
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_shine"], (rx, ry, 1, 1))
    def _draw_realm_foreground(surface, boss, x, y, timer, phase):
        """Vertical green portal + chain from boss to target."""
        tx, ty = _NS_morvekhar._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Portal rising.
            t = progress / 0.3
            portal_h = int(t * 55)
            portal_w = int(t * 20)
            if portal_h > 4:
                # Portal ellipse (vertical).
                portal_rect = (tx - portal_w, ty - portal_h,
                                portal_w * 2, portal_h * 2)
                # Outer glow.
                for r_i in range(3):
                    alpha = _NS_morvekhar._alpha(220 - r_i * 50)
                    pygame.draw.ellipse(surface,
                                         (*_NS_morvekhar.PALETTE["soul_dark"], alpha),
                                         (portal_rect[0] - r_i * 2,
                                          portal_rect[1] - r_i * 2,
                                          portal_rect[2] + r_i * 4,
                                          portal_rect[3] + r_i * 4), 2)
                # Inner dark.
                pygame.draw.ellipse(surface, _NS_morvekhar.PALETTE["ground_dark"],
                                    (tx - portal_w + 4, ty - portal_h + 4,
                                     portal_w * 2 - 8, portal_h * 2 - 8))
                # Bright core.
                pygame.draw.ellipse(surface, _NS_morvekhar.PALETTE["soul_darkest"],
                                    (tx - portal_w + 6, ty - portal_h + 6,
                                     portal_w * 2 - 12, portal_h * 2 - 12))
        elif progress < 0.85:
            # Full portal + chains pulling target.
            t = (progress - 0.3) / 0.55
            portal_h = 55
            portal_w = 20
            portal_pulse = math.sin(phase * 2) * 3
            # Portal outer ring.
            for r_i in range(4):
                alpha = _NS_morvekhar._alpha(240 - r_i * 50)
                pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                    (tx - portal_w - r_i * 2 + int(portal_pulse),
                                     ty - portal_h - r_i * 2,
                                     portal_w * 2 + r_i * 4 - int(portal_pulse * 2),
                                     portal_h * 2 + r_i * 4), 2)
            # Portal fill (dark abyss).
            pygame.draw.ellipse(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                                (tx - portal_w + 3, ty - portal_h + 3,
                                 portal_w * 2 - 6, portal_h * 2 - 6))
            pygame.draw.ellipse(surface, _NS_morvekhar.PALETTE["soul_darkest"],
                                (tx - portal_w + 5, ty - portal_h + 5,
                                 portal_w * 2 - 10, portal_h * 2 - 10))
            # Inner swirling energy.
            for swirl_i in range(6):
                swirl_angle = phase * 3 + swirl_i * math.pi / 3
                sw_x = tx + int(math.cos(swirl_angle) * (portal_w - 8))
                sw_y = ty + int(math.sin(swirl_angle) * (portal_h - 10))
                alpha = _NS_morvekhar._alpha(200)
                _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                         (sw_x, sw_y), 3)
                _NS_morvekhar._aacircle(surface, (*_NS_morvekhar.PALETTE["soul_light"], alpha),
                                         (sw_x, sw_y), 2)
                pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_hot"], (sw_x, sw_y, 1, 1))
            # Portal edge glow.
            edge_pulse = math.sin(phase * 4) * 0.3 + 0.7
            for glow_i in range(3):
                alpha = _NS_morvekhar._alpha(160 * edge_pulse * (1 - glow_i / 3))
                pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_hot"], alpha),
                                    (tx - portal_w - glow_i, ty - portal_h - glow_i,
                                     portal_w * 2 + glow_i * 2,
                                     portal_h * 2 + glow_i * 2), 1)
            # === CHAINS from boss to portal (pulling target soul) ===
            for chain_i in range(3):
                offset_y = (chain_i - 1) * 4
                num_links = 12
                for seg in range(num_links):
                    seg_t = seg / num_links
                    # Chain sway animation.
                    sway = math.sin(phase * 2 + seg * 0.5 + chain_i) * 3
                    sx = int(x + (tx - x) * seg_t)
                    sy = int(y - 8 + (ty - y + 8) * seg_t) + offset_y + int(sway)
                    if seg % 2 == 0:
                        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["shadow_deep"],
                                                 (sx + 1, sy + 1), 3)
                        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                                                 (sx, sy), 3)
                        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_dark"],
                                                 (sx, sy), 2)
                        _NS_morvekhar._aacircle(surface, _NS_morvekhar.PALETTE["iron_light"],
                                                 (sx - 1, sy - 1), 1)
                    else:
                        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_darkest"],
                                         (sx - 1, sy - 1, 3, 3))
                        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_dark"],
                                         (sx, sy, 2, 2))
                        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["iron_light"],
                                         (sx, sy, 1, 1))
                    # Green energy on chain.
                    if seg % 3 == 0:
                        pygame.draw.rect(surface, _NS_morvekhar.PALETTE["soul_hot"],
                                         (sx, sy, 1, 1))
        else:
            # Aftermath: portal closing.
            t = (progress - 0.85) / 0.15
            portal_h = int(55 * (1 - t))
            portal_w = int(20 * (1 - t))
            if portal_h > 3:
                alpha = _NS_morvekhar._alpha(220 * (1 - t))
                pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["soul_mid"], alpha),
                                    (tx - portal_w, ty - portal_h,
                                     portal_w * 2, portal_h * 2), 2)
                pygame.draw.ellipse(surface, (*_NS_morvekhar.PALETTE["ground_dark"], alpha),
                                    (tx - portal_w + 2, ty - portal_h + 2,
                                     portal_w * 2 - 4, portal_h * 2 - 4))



# ====================================================================
# VORGATH (DEMON WARDEN) - Mini Boss
# ====================================================================

class _NS_vorgath:
    """Namespace vorgath - Mini boss demon warden dengan chain ball."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale demon flesh)
        "skin_darkest": (35, 25, 40),
        "skin_dark": (85, 65, 90),
        "skin_mid": (150, 125, 155),
        "skin_light": (210, 190, 215),
        "skin_shine": (245, 230, 245),
        # Hair (silver-white)
        "hair_dark": (90, 85, 110),
        "hair_mid": (170, 165, 190),
        "hair_light": (230, 225, 240),
        "hair_shine": (255, 255, 255),
        # Armor (dark bronze/black)
        "armor_darkest": (15, 10, 20),
        "armor_dark": (45, 30, 55),
        "armor_mid": (85, 60, 95),
        "armor_light": (140, 110, 155),
        "armor_shine": (200, 175, 215),
        "armor_gold": (180, 140, 60),
        "armor_gold_light": (240, 210, 130),
        # Cape (dark purple)
        "cape_darkest": (10, 5, 20),
        "cape_dark": (30, 15, 55),
        "cape_mid": (60, 35, 95),
        "cape_light": (110, 75, 155),
        # Demon Power (purple energy)
        "demon_darkest": (15, 5, 30),
        "demon_dark": (50, 20, 90),
        "demon_mid": (120, 55, 190),
        "demon_light": (180, 110, 240),
        "demon_hot": (220, 170, 255),
        "demon_shine": (250, 220, 255),
        # Chain (dark iron)
        "chain_dark": (20, 15, 25),
        "chain_mid": (65, 55, 75),
        "chain_light": (140, 130, 150),
        "chain_shine": (210, 200, 220),
        # Eyes (glowing purple)
        "eye_socket": (5, 2, 10),
        "eye_glow": (180, 100, 255),
        "eye_hot": (240, 200, 255),
        # Ground / crack
        "crack_dark": (5, 2, 15),
        "crack_mid": (60, 25, 100),
        "crack_light": (160, 90, 220),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vorgath._clamp(color)
        if _NS_vorgath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vorgath._clamp(color)
        if _NS_vorgath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vorgath._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vorgath(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_vorgath._update_vorg_attack_anim(boss)
        attacking = (
            getattr(boss, "_vorg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind (aura + floating dust).
        _NS_vorgath._draw_demon_aura(surface, x, y, pulse)
        _NS_vorgath._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_vorgath._draw_demonic_impact_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorgath._draw_demonic_domain_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vorgath._draw_demon_purge_trail(surface, boss, x, y, skill_timer, pulse)
        # Body (floating with bob).
        if attacking:
            _NS_vorgath._draw_vorg_attack(surface, boss, x, y)
        else:
            _NS_vorgath._draw_vorg_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_vorgath._draw_demon_gaze_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vorgath._draw_demonic_impact_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorgath._draw_demonic_domain_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vorg_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vorg_previous_timer", 0))
        active = bool(getattr(boss, "_vorg_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vorg_attack_active = True
            boss._vorg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vorg_attack_frame = int(getattr(boss, "_vorg_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vorg_attack_active = False
            boss._vorg_attack_frame = 0
            active = False
        boss._vorg_previous_timer = timer
        boss._vorg_attack_progress = (
            min(1.0, getattr(boss, "_vorg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vorg_float(surface, boss, x, y):
        """Floating idle - hovers with slow bob."""
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_vorgath._draw_shadow(surface, x + sway, y + 50, floating=True, phase=boss.pulse)
        _NS_vorgath._draw_floating_wisps(surface, x + sway, y + 40, boss.pulse)
        _NS_vorgath._draw_vorg_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "float")
    def _draw_vorg_attack(surface, boss, x, y):
        progress = getattr(boss, "_vorg_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up → swing → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_vorgath._draw_shadow(surface, x + lunge, y + 50, floating=True, phase=boss.pulse)
        _NS_vorgath._draw_floating_wisps(surface, x + lunge, y + 40, boss.pulse, intense=True)
        _NS_vorgath._draw_vorg_body(surface, x + lunge, y + bob - lift,
                                     boss.direction, boss.pulse, "attack", progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_vorg_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw floating demon warden with cape, chain ball."""
        # Cape (behind).
        _NS_vorgath._draw_cape(surface, cx, cy, facing, phase)
        # Legs (floating - crossed/bent, no ground contact).
        _NS_vorgath._draw_float_legs(surface, cx, cy + 12, facing, phase)
        # Torso.
        _NS_vorgath._draw_torso(surface, cx, cy, facing, phase)
        # Left arm (back arm, holding cape/relaxed).
        _NS_vorgath._draw_back_arm(surface, cx, cy, facing, phase)
        # Head (with silver hair).
        _NS_vorgath._draw_head(surface, cx + facing * 2, cy - 18, facing, phase)
        # Front arm + chain ball (main weapon).
        _NS_vorgath._draw_chain_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_cape(surface, cx, cy, facing, phase):
        """Dark purple cape flowing behind."""
        sway = math.sin(phase * 0.8) * 3
        back = -facing
        cape_top = (cx + back * 4, cy - 14)
        cape_shoulder = (cx + back * 8, cy - 10)
        cape_mid = (cx + back * 14 + int(sway), cy + 2)
        cape_bot1 = (cx + back * 18 + int(sway * 1.5), cy + 14)
        cape_bot2 = (cx + back * 12 + int(sway), cy + 18)
        cape_bot3 = (cx + back * 4, cy + 16)
        cape_side = (cx + back * 2, cy - 8)
        # Shadow.
        pts_shadow = [(p[0] + 2, p[1] + 2) for p in
                      [cape_top, cape_shoulder, cape_mid, cape_bot1, cape_bot2, cape_bot3, cape_side]]
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["shadow_deep"], pts_shadow)
        # Cape layers.
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["cape_darkest"],
                          [cape_top, cape_shoulder, cape_mid, cape_bot1, cape_bot2, cape_bot3, cape_side])
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["cape_dark"],
                          [cape_top, cape_shoulder,
                           (cape_mid[0] + facing * 2, cape_mid[1]),
                           (cape_bot1[0] + facing * 2, cape_bot1[1] - 2),
                           (cape_bot3[0] + facing * 2, cape_bot3[1] - 2),
                           cape_side])
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["cape_mid"],
                          [(cape_top[0] + facing, cape_top[1] + 1),
                           (cape_shoulder[0] + facing, cape_shoulder[1] + 1),
                           (cape_mid[0] + facing * 4, cape_mid[1]),
                           (cape_bot3[0] + facing * 3, cape_bot3[1] - 4),
                           (cape_side[0] + facing, cape_side[1] + 1)])
        # Cape edge highlights.
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["cape_light"],
                            cape_top, cape_shoulder, 1)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["cape_light"],
                            (cape_bot1[0], cape_bot1[1] - 1),
                            (cape_bot2[0], cape_bot2[1] - 1), 1)
    def _draw_float_legs(surface, cx, cy, facing, phase):
        """Legs bent/dangling since floating - dark armored."""
        sway = math.sin(phase * 0.6) * 2
        # Left leg.
        hip_a = (cx - 4, cy - 2)
        knee_a = (cx - 6 - facing, cy + 6 + int(sway))
        foot_a = (cx - 3 - facing, cy + 14 + int(sway))
        # Right leg (slightly different angle - dangling naturally).
        hip_b = (cx + 4, cy - 2)
        knee_b = (cx + 5 + facing, cy + 8 - int(sway))
        foot_b = (cx + 7 + facing, cy + 15 - int(sway))
        for hip, knee, foot in [(hip_a, knee_a, foot_a), (hip_b, knee_b, foot_b)]:
            # Shadow.
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["shadow_deep"],
                                (hip[0] + 1, hip[1] + 1), (knee[0] + 1, knee[1] + 1), 6)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["shadow_deep"],
                                (knee[0] + 1, knee[1] + 1), (foot[0] + 1, foot[1] + 1), 5)
            # Thigh (armor).
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_darkest"], hip, knee, 6)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_dark"], hip, knee, 4)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_mid"],
                                (hip[0] - 1, hip[1]), (knee[0] - 1, knee[1]), 2)
            # Shin.
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_darkest"], knee, foot, 5)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_dark"], knee, foot, 3)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_mid"],
                                (knee[0] - 1, knee[1]), (foot[0] - 1, foot[1]), 1)
            # Knee guard (gold accent).
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_gold"], knee, 3)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_gold_light"], knee, 2)
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_light"], (knee[0], knee[1], 1, 1))
            # Boot.
            _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["armor_darkest"], [
                (foot[0] - 3, foot[1] - 1),
                (foot[0] + 4, foot[1] - 1),
                (foot[0] + 3, foot[1] + 3),
                (foot[0] - 2, foot[1] + 3),
            ])
            _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["armor_dark"], [
                (foot[0] - 2, foot[1]),
                (foot[0] + 3, foot[1]),
                (foot[0] + 2, foot[1] + 2),
                (foot[0] - 1, foot[1] + 2),
            ])
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular bare chest with armor accents."""
        breath = math.sin(phase * 0.7) * 1
        # Main torso shape (V-shape muscular).
        torso = [
            (cx - 10, cy - 12),   # left shoulder
            (cx - 12, cy - 4),    # left rib
            (cx - 10, cy + 4),    # left waist
            (cx - 6, cy + 10),    # left hip
            (cx + 6, cy + 10),    # right hip
            (cx + 10, cy + 4),    # right waist
            (cx + 12, cy - 4),    # right rib
            (cx + 10, cy - 12),   # right shoulder
            (cx + 4, cy - 14),    # neck right
            (cx - 4, cy - 14),    # neck left
        ]
        # Shadow.
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso])
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_darkest"], torso)
        # Skin base.
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_dark"], [
            (cx - 9, cy - 11), (cx - 11, cy - 4), (cx - 9, cy + 3),
            (cx - 5, cy + 9), (cx + 5, cy + 9), (cx + 9, cy + 3),
            (cx + 11, cy - 4), (cx + 9, cy - 11), (cx + 3, cy - 13),
            (cx - 3, cy - 13),
        ])
        # Muscle definition (mid tone).
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_mid"], [
            (cx - 7, cy - 10), (cx - 9, cy - 4), (cx - 7, cy + 2),
            (cx - 4, cy + 7), (cx + 4, cy + 7), (cx + 7, cy + 2),
            (cx + 9, cy - 4), (cx + 7, cy - 10),
        ])
        # Highlight (pec muscles).
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_light"], [
            (cx - 5, cy - 8), (cx - 6, cy - 3), (cx - 2, cy - 1),
            (cx + 2, cy - 1), (cx + 6, cy - 3), (cx + 5, cy - 8),
            (cx + 2, cy - 9), (cx - 2, cy - 9),
        ])
        # Split down middle (chest line).
        pygame.draw.line(surface, _NS_vorgath.PALETTE["skin_darkest"],
                         (cx, cy - 8), (cx, cy + 2), 1)
        # Ab lines.
        for ab_y in (0, 3, 6):
            pygame.draw.line(surface, _NS_vorgath.PALETTE["skin_darkest"],
                             (cx - 4, cy + ab_y), (cx + 4, cy + ab_y), 1)
        # Belt (dark armor with gold buckle).
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_darkest"],
                         (cx - 8, cy + 8, 16, 4))
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_dark"],
                         (cx - 7, cy + 9, 14, 2))
        # Belt buckle.
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_gold"],
                         (cx - 3, cy + 8, 6, 4))
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_gold_light"],
                         (cx - 2, cy + 9, 4, 2))
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_light"],
                         (cx, cy + 10, 1, 1))
        # Shoulder pauldrons (dark spiked armor).
        for side in (-1, 1):
            sx = cx + side * 10
            sy = cy - 11
            _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["shadow_deep"], [
                (sx + side * 1, sy - 3),
                (sx + side * 5, sy - 1),
                (sx + side * 6, sy + 3),
                (sx + side * 2, sy + 5),
                (sx - side * 2, sy + 3),
            ])
            _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["armor_darkest"], [
                (sx, sy - 4),
                (sx + side * 4, sy - 2),
                (sx + side * 5, sy + 2),
                (sx + side * 1, sy + 4),
                (sx - side * 3, sy + 2),
            ])
            _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["armor_dark"], [
                (sx, sy - 3),
                (sx + side * 3, sy - 1),
                (sx + side * 4, sy + 1),
                (sx, sy + 3),
                (sx - side * 2, sy + 1),
            ])
            # Spike on pauldron.
            _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["armor_mid"], [
                (sx + side * 4, sy - 3),
                (sx + side * 6, sy - 5),
                (sx + side * 5, sy - 1),
            ])
            # Gold trim.
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_gold"],
                             (sx + side * 2, sy + 3, 2, 1))
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_light"],
                             (sx + side * 3, sy + 3, 1, 1))
        # Chest tattoo/mark (demon sigil - purple).
        pulse = math.sin(phase * 1.5) * 0.4 + 0.6
        alpha = _NS_vorgath._alpha(220 * pulse)
        sigil_surf = pygame.Surface((14, 10), pygame.SRCALPHA)
        pygame.draw.line(sigil_surf, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                         (7, 1), (7, 8), 1)
        pygame.draw.line(sigil_surf, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                         (3, 4), (11, 4), 1)
        pygame.draw.line(sigil_surf, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                         (5, 2), (9, 6), 1)
        pygame.draw.line(sigil_surf, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                         (9, 2), (5, 6), 1)
        surface.blit(sigil_surf, (cx - 7, cy - 5))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm (relaxed, holding cape or fist)."""
        back = -facing
        sway = math.sin(phase * 0.5) * 1
        shoulder = (cx + back * 8, cy - 10)
        elbow = (cx + back * 12, cy - 2 + int(sway))
        hand = (cx + back * 10, cy + 6 + int(sway))
        # Shadow.
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["shadow_deep"],
                            (shoulder[0] + 1, shoulder[1] + 1),
                            (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["shadow_deep"],
                            (elbow[0] + 1, elbow[1] + 1),
                            (hand[0] + 1, hand[1] + 1), 4)
        # Upper arm.
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["skin_darkest"], shoulder, elbow, 5)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["skin_dark"], shoulder, elbow, 3)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["skin_mid"],
                            (shoulder[0], shoulder[1] - 1), (elbow[0], elbow[1] - 1), 1)
        # Forearm (with bracer).
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_darkest"], elbow, hand, 4)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_dark"], elbow, hand, 3)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_mid"],
                            (elbow[0] - 1, elbow[1]), (hand[0] - 1, hand[1]), 1)
        # Bracer gold accent.
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_gold"], elbow, 2)
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_light"], (elbow[0], elbow[1], 1, 1))
        # Fist.
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["skin_darkest"], hand, 3)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["skin_dark"], hand, 2)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["skin_mid"], (hand[0], hand[1] - 1), 1)
    def _draw_head(surface, cx, cy, facing, phase):
        """Head with silver hair, glowing eyes, demonic mark."""
        # Head shape.
        head = [
            (cx - 6, cy - 2),
            (cx - 7, cy - 6),
            (cx - 5, cy - 10),
            (cx - 1, cy - 12),
            (cx + 4, cy - 11),
            (cx + 7, cy - 8),
            (cx + 7, cy - 3),
            (cx + 5, cy + 2),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
            (cx - 5, cy + 2),
        ]
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in head])
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_darkest"], head)
        # Skin base.
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_dark"], [
            (cx - 5, cy - 2), (cx - 6, cy - 6), (cx - 4, cy - 9),
            (cx - 1, cy - 11), (cx + 3, cy - 10), (cx + 6, cy - 7),
            (cx + 6, cy - 3), (cx + 4, cy + 1), (cx + 2, cy + 3),
            (cx - 2, cy + 3), (cx - 4, cy + 1),
        ])
        # Face highlight.
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_mid"], [
            (cx - 3, cy - 4), (cx - 4, cy - 7), (cx, cy - 9),
            (cx + 3, cy - 8), (cx + 5, cy - 5), (cx + 4, cy - 1),
            (cx + 2, cy + 1), (cx - 2, cy + 1), (cx - 3, cy - 1),
        ])
        # Cheek/nose highlight.
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["skin_light"], [
            (cx, cy - 6), (cx + 3, cy - 5), (cx + 2, cy - 2), (cx, cy - 3),
        ])
        # HAIR (silver-white, swept back with spikes).
        _NS_vorgath._draw_hair(surface, cx, cy, facing, phase)
        # DEMON MARK on forehead (small purple sigil).
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        mark_alpha = _NS_vorgath._alpha(240 * pulse)
        mark_surf = pygame.Surface((6, 4), pygame.SRCALPHA)
        pygame.draw.polygon(mark_surf, (*_NS_vorgath.PALETTE["demon_mid"], mark_alpha),
                            [(3, 0), (5, 2), (3, 3), (1, 2)])
        pygame.draw.rect(mark_surf, (*_NS_vorgath.PALETTE["demon_hot"], mark_alpha),
                         (3, 1, 1, 2))
        surface.blit(mark_surf, (cx - 3, cy - 8))
        # EYES (glowing purple).
        _NS_vorgath._draw_glow_eyes(surface, cx, cy, facing, phase)
        # Stern brow.
        pygame.draw.line(surface, _NS_vorgath.PALETTE["skin_darkest"],
                         (cx - 4, cy - 6), (cx - 2, cy - 5), 1)
        pygame.draw.line(surface, _NS_vorgath.PALETTE["skin_darkest"],
                         (cx + 2, cy - 5), (cx + 4, cy - 6), 1)
        # Mouth (grim line).
        pygame.draw.line(surface, _NS_vorgath.PALETTE["skin_darkest"],
                         (cx - 2, cy), (cx + 2, cy), 1)
        # Jaw shadow.
        pygame.draw.line(surface, _NS_vorgath.PALETTE["skin_darkest"],
                         (cx - 3, cy + 2), (cx + 3, cy + 2), 1)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Silver spiky hair swept back."""
        wave = math.sin(phase * 0.5) * 1
        # Main hair mass (top and back).
        hair_shape = [
            (cx - 6, cy - 6),
            (cx - 7, cy - 10),
            (cx - 4, cy - 13),
            (cx - 1, cy - 14),
            (cx + 3, cy - 13),
            (cx + 6, cy - 11),
            (cx + 8, cy - 8),
            (cx + 6, cy - 6),
            (cx + 2, cy - 9),
            (cx - 3, cy - 9),
        ]
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in hair_shape])
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["hair_dark"], hair_shape)
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["hair_mid"], [
            (cx - 5, cy - 7), (cx - 6, cy - 10), (cx - 3, cy - 12),
            (cx, cy - 13), (cx + 3, cy - 12), (cx + 5, cy - 10),
            (cx + 6, cy - 8), (cx + 4, cy - 7), (cx, cy - 9),
            (cx - 3, cy - 9),
        ])
        _NS_vorgath._poly(surface, _NS_vorgath.PALETTE["hair_light"], [
            (cx - 3, cy - 9), (cx - 4, cy - 11), (cx - 1, cy - 12),
            (cx + 2, cy - 11), (cx + 1, cy - 10), (cx - 1, cy - 10),
        ])
        # Hair spikes (back, swept).
        for i, (dx, dy, length) in enumerate([
            (-6, -8, 3), (-4, -12, 2), (2, -13, 2), (5, -11, 3), (7, -8, 3),
        ]):
            offset = int(wave) if i % 2 == 0 else -int(wave)
            spike_x = cx + dx
            spike_y = cy + dy + offset
            tip_x = spike_x - facing * length
            tip_y = spike_y - length
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["hair_dark"],
                                (spike_x, spike_y), (tip_x, tip_y), 2)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["hair_mid"],
                                (spike_x, spike_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["hair_light"], (tip_x, tip_y, 1, 1))
        # Hair shine highlights.
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["hair_shine"], (cx - 1, cy - 12, 2, 1))
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["hair_shine"], (cx + 2, cy - 11, 1, 1))
    def _draw_glow_eyes(surface, cx, cy, facing, phase):
        """Glowing purple demon eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side, ex_off in [(-1, -2), (1, 3)]:
            ex = cx + ex_off
            ey = cy - 4
            # Socket.
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Glow halo.
            for r in range(5, 0, -1):
                alpha = _NS_vorgath._alpha(100 * (5 - r) / 5 * pulse)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["eye_glow"], alpha),
                                       (ex, ey), r)
            # Eye core.
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["eye_glow"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["eye_hot"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_chain_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding chain ball weapon."""
        # Base positions.
        shoulder = (cx + facing * 8, cy - 10)
        # Arm angle and ball position depend on action.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: arm back, ball behind.
                t = attack_progress / 0.35
                arm_angle = math.pi * (0.9 - t * 0.3) * (-facing if facing > 0 else 1)
                arm_len = 12
                chain_len = 18 + int(t * 8)
                chain_angle = math.pi * (1.1 - t * 0.2) * (-facing if facing > 0 else 1)
            elif attack_progress < 0.6:
                # Swing forward!
                t = (attack_progress - 0.35) / 0.25
                arm_angle = math.pi * (0.6 - t * 0.7) * (-facing if facing > 0 else 1)
                arm_len = 12
                chain_len = 26 - int(t * 4)
                chain_angle = math.pi * (0.9 - t * 1.2) * (-facing if facing > 0 else 1)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * (-0.1 + t * 0.5) * (-facing if facing > 0 else 1)
                arm_len = 12
                chain_len = 22 - int(t * 6)
                chain_angle = math.pi * (-0.3 + t * 0.5) * (-facing if facing > 0 else 1)
        else:
            # Float idle: ball hovers in front.
            hover = math.sin(phase * 0.8) * 3
            arm_angle = math.pi * 0.35 * (-facing if facing > 0 else 1)
            arm_len = 12
            chain_len = 16 + int(hover)
            chain_angle = math.pi * 0.55 * (-facing if facing > 0 else 1)
        # Calc elbow position.
        # Arm goes from shoulder outward at arm_angle.
        elbow_x = shoulder[0] + int(math.cos(arm_angle) * arm_len) * (facing if facing > 0 else -1)
        elbow_y = shoulder[1] + int(math.sin(arm_angle) * arm_len)
        # Hand at end of forearm (extends from elbow).
        hand_x = elbow_x + facing * 6
        hand_y = elbow_y + 2
        # Ball position (from hand via chain).
        ball_x = hand_x + int(math.cos(chain_angle) * chain_len) * (facing if facing > 0 else -1)
        ball_y = hand_y + int(math.sin(chain_angle) * chain_len)
        # === DRAW ARM ===
        # Upper arm.
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["shadow_deep"],
                            (shoulder[0] + 1, shoulder[1] + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["skin_darkest"],
                            shoulder, (elbow_x, elbow_y), 5)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["skin_dark"],
                            shoulder, (elbow_x, elbow_y), 3)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["skin_mid"],
                            (shoulder[0], shoulder[1] - 1),
                            (elbow_x, elbow_y - 1), 1)
        # Forearm (with bracer/gauntlet).
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_mid"],
                            (elbow_x - 1, elbow_y),
                            (hand_x - 1, hand_y), 1)
        # Elbow gold accent.
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_gold"],
                              (elbow_x, elbow_y), 2)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_gold_light"],
                              (elbow_x, elbow_y), 1)
        # Fist (gauntleted).
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 4)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_dark"],
                              (hand_x, hand_y), 3)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_mid"],
                              (hand_x - 1, hand_y - 1), 1)
        # === DRAW CHAIN (segments from fist to ball) ===
        num_links = 6
        for i in range(num_links + 1):
            t = i / num_links
            lx = int(hand_x + (ball_x - hand_x) * t)
            ly = int(hand_y + (ball_y - hand_y) * t)
            # Small chain link.
            if i % 2 == 0:
                _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["chain_dark"], (lx, ly), 2)
                _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["chain_mid"], (lx, ly), 1)
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["chain_light"], (lx, ly, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["chain_dark"], (lx - 1, ly - 1, 2, 2))
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["chain_mid"], (lx, ly, 1, 1))
        # === DRAW DEMONIC BALL ===
        _NS_vorgath._draw_demon_ball(surface, ball_x, ball_y, phase, action, attack_progress)
    def _draw_demon_ball(surface, bx, by, phase, action, attack_progress):
        """The signature demon orb - purple glowing sphere with spikes."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        intensity = 1.0
        if action == "attack" and 0.35 < attack_progress < 0.7:
            intensity = 1.5  # brighter during swing
        # Outer glow aura.
        for r in range(16, 4, -2):
            alpha = _NS_vorgath._alpha(80 * (16 - r) / 16 * pulse * intensity)
            _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha), (bx, by), r)
        # Ball spikes (metal ring around ball).
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.3
            spike_x = bx + int(math.cos(angle) * 9)
            spike_y = by + int(math.sin(angle) * 9)
            base_x = bx + int(math.cos(angle) * 6)
            base_y = by + int(math.sin(angle) * 6)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_darkest"],
                                (base_x, base_y), (spike_x, spike_y), 2)
            _NS_vorgath._aaline(surface, _NS_vorgath.PALETTE["armor_dark"],
                                (base_x, base_y), (spike_x, spike_y), 1)
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_mid"],
                             (spike_x, spike_y, 1, 1))
        # Main ball body (dark iron sphere).
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["shadow_deep"], (bx + 1, by + 1), 8)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_darkest"], (bx, by), 8)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_dark"], (bx, by), 7)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["armor_mid"], (bx - 1, by - 1), 5)
        # Purple core (glowing energy).
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_darkest"], (bx, by), 5)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_dark"], (bx, by), 4)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_mid"], (bx, by), 3)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_light"], (bx, by), 2)
        _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["white"], (bx, by, 1, 1))
        # Ball highlight (top-left shine).
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_shine"], (bx - 3, by - 3, 1, 1))
        pygame.draw.rect(surface, _NS_vorgath.PALETTE["armor_light"], (bx - 2, by - 3, 1, 1))
        # Sparks around ball (during attack).
        if action == "attack" and 0.3 < attack_progress < 0.75:
            for i in range(6):
                spark_angle = phase * 4 + i * math.pi / 3
                sx = bx + int(math.cos(spark_angle) * 12)
                sy = by + int(math.sin(spark_angle) * 12)
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_shine"], (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, floating=False, phase=0):
        """Floating shadow (smaller, more diffuse if floating)."""
        offset_y = 0
        if floating:
            offset_y = int(math.sin(phase * 0.6) * 2)
        shadow = pygame.Surface((120, 24), pygame.SRCALPHA)
        # Fainter shadow because floating.
        max_alpha = 130 if floating else 180
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * (max_alpha // 10))
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius // 2, 100 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (5, 3, 15, max_alpha - 30), (10, 8, 100, 8))
        surface.blit(shadow, (x - 60, y - 12 + offset_y))
    def _draw_floating_wisps(surface, cx, cy, phase, intense=False):
        """Purple wisps rising from below (floating effect)."""
        strength = 1.4 if intense else 1.0
        # Wisps rising.
        for i in range(8):
            wisp_t = (phase * 0.5 + i * 0.14) % 1.0
            wx = cx - 15 + i * 4 + int(math.sin(phase + i) * 3)
            wy = cy + 10 - int(wisp_t * 22)
            alpha = _NS_vorgath._alpha(200 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_darkest"], alpha),
                                       (wx, wy), 3)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_dark"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_hot"], alpha),
                                 (wx, wy - 1, 1, 1))
        # Sparkles.
        for i in range(6):
            spark_t = (phase * 0.7 + i * 0.18) % 1.0
            sx = cx - 12 + i * 5 + int(math.sin(phase * 1.5 + i) * 4)
            sy = cy + 6 - int(spark_t * 18)
            alpha = _NS_vorgath._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_hot"], alpha), (sx, sy, 1, 1))
    def _draw_demon_aura(surface, x, y, phase):
        """Large purple aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_vorgath._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vorgath._aacircle(aura, (*_NS_vorgath.PALETTE["demon_darkest"], alpha),
                                       (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_vorgath._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vorgath._aacircle(aura, (*_NS_vorgath.PALETTE["demon_dark"], alpha),
                                       (100, 85), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_vorgath._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vorgath._aacircle(aura, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                       (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))
        # Floating embers.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Purple ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vorgath.PALETTE["demon_darkest"], 200),
                            (5, 16, 150, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_vorgath.PALETTE["demon_dark"], 220),
                            (14, 18, 132, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_vorgath.PALETTE["demon_mid"], 230),
                            (25, 20, 110, 18), 1)
        # Runes.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vorgath.PALETTE["demon_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vorgath.PALETTE["demon_hot"], _NS_vorgath._alpha(150 * pulse)),
                                (15, 10, 130, 36), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q: DEMON GAZE (ranged projectile that pulls)
    # ============================================================
    def _draw_demon_gaze_skill(surface, boss, x, y, timer, phase):
        """Purple orb projectile with pull chains."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vorgath._target_position(boss, x, y)
        if progress < 0.25:
            # Charge in ball / hand.
            t = progress / 0.25
            charge_x = x + facing * 30
            charge_y = y + 2
            cr = int(4 + t * 8)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_vorgath._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_darkest"], alpha),
                                       (charge_x, charge_y), r)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_dark"], (charge_x, charge_y), cr)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_mid"], (charge_x, charge_y), cr - 2)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_light"], (charge_x, charge_y), max(1, cr - 4))
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_shine"], (charge_x, charge_y), max(1, cr - 6))
            # Sparks.
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 34
            start_y = y + 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Comet trail.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.045)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_vorgath._alpha(240 - i * 24)
                size = max(1, 8 - i)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_darkest"], alpha),
                                       (px, py), size)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                                       (px, py), max(1, size - 3))
            # Bright head.
            for r in range(13, 3, -2):
                alpha = _NS_vorgath._alpha(100 * (13 - r) / 13)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha), (bx, by), r)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_darkest"], (bx, by), 9)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_dark"], (bx, by), 7)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_mid"], (bx, by), 4)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_light"], (bx, by), 3)
            _NS_vorgath._aacircle(surface, _NS_vorgath.PALETTE["demon_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_vorgath.PALETTE["white"], (bx, by, 1, 1))
            # Sparks around orb.
            for i in range(5):
                angle = phase * 5 + i * math.pi / 2.5
                sx = bx + int(math.cos(angle) * 11)
                sy = by + int(math.sin(angle) * 11)
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_hot"], (sx, sy, 1, 1))
            # Impact + pull chains from target back to boss.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                # Impact ring.
                radius = int(10 + st * 22)
                alpha = _NS_vorgath._alpha(240 * (1 - st))
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_darkest"], alpha),
                                       (tx, ty), radius + 3, 3)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 2)
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                                       (tx, ty), max(1, radius - 10), 1)
                # Pull chains from target to boss.
                for chain_i in range(3):
                    offset = (chain_i - 1) * 3
                    for seg in range(0, 100, 8):
                        seg_t = seg / 100.0
                        sx = int(tx + (x - tx) * seg_t)
                        sy = int(ty + (y - ty) * seg_t) + offset
                        _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["chain_dark"], alpha),
                                               (sx, sy), 2)
                        pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                         (sx, sy, 1, 1))
    # ============================================================
    # SKILL W: DEMONIC IMPACT (ground slam AOE)
    # ============================================================
    def _draw_demonic_impact_ground(surface, boss, x, y, timer, phase):
        """Crack radiating from boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2.5))
        if r > 3:
            # Dark crater.
            pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["crack_dark"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["crack_mid"], 200),
                                (x - r + 4, y + 42 - r // 3, r * 2 - 8, r * 2 // 3 - 4))
            # Radiating cracks.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.1
                end_x = x + int(math.cos(angle) * r)
                end_y = y + 44 + int(math.sin(angle) * r * 0.4)
                # Zigzag crack.
                mid_x = x + int(math.cos(angle) * r * 0.5)
                mid_y = y + 44 + int(math.sin(angle) * r * 0.2)
                offset = math.sin(angle * 3) * 3
                mid_x += int(offset)
                pygame.draw.line(surface, _NS_vorgath.PALETTE["crack_dark"],
                                 (x, y + 44), (mid_x, mid_y), 2)
                pygame.draw.line(surface, _NS_vorgath.PALETTE["crack_light"],
                                 (mid_x, mid_y), (end_x, end_y), 1)
    def _draw_demonic_impact_foreground(surface, boss, x, y, timer, phase):
        """Purple energy bursts + shockwave ring."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2.5))
        if r < 5:
            return
        # Shockwave ring.
        t_wave = min(1.0, progress * 1.5)
        wave_r = int(r * t_wave)
        alpha = _NS_vorgath._alpha(200 * (1 - t_wave))
        _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                              (x, y + 44), wave_r, 2)
        _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_hot"], alpha),
                              (x, y + 44), wave_r + 2, 1)
        # Energy pillars around crater.
        for i in range(6):
            angle = i * math.pi / 3 + phase * 0.2
            px = x + int(math.cos(angle) * r * 0.7)
            py = y + 44 + int(math.sin(angle) * r * 0.3)
            for layer in range(5):
                layer_t = (phase * 0.7 + i * 0.3 + layer * 0.2) % 1.0
                ly = py - int(layer_t * 25)
                lalpha = _NS_vorgath._alpha(200 * (1 - layer_t))
                lw = int(4 + layer_t * 3)
                lh = int(2 + layer_t * 2)
                pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["demon_dark"], lalpha),
                                    (px - lw, ly - lh, lw * 2, lh * 2))
                pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["demon_mid"], lalpha),
                                    (px - lw + 1, ly - lh + 1, lw * 2 - 2, lh * 2 - 2))
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_light"], lalpha),
                                 (px, ly, 1, 1))
    # ============================================================
    # SKILL E: DEMON PURGE (dash trail)
    # ============================================================
    def _draw_demon_purge_trail(surface, boss, x, y, timer, phase):
        """Purple dash trail behind boss."""
        facing = boss.direction
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Trail streaks behind boss.
        for i in range(8):
            offset = (i + 1) * 8
            tx = x - facing * offset
            ty = y + int(math.sin(phase + i) * 2)
            alpha = _NS_vorgath._alpha(220 * (1 - i / 8) * (1 - progress * 0.5))
            _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_darkest"], alpha),
                                   (tx, ty), max(2, 8 - i))
            _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_dark"], alpha),
                                   (tx, ty), max(1, 6 - i))
            _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                   (tx, ty), max(1, 4 - i))
            pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                             (tx, ty, 2, 2))
            pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_hot"], alpha),
                             (tx, ty, 1, 1))
    # ============================================================
    # SKILL R: DEMONIC DOMAIN (huge circle ultimate)
    # ============================================================
    def _draw_demonic_domain_ground(surface, boss, x, y, timer, phase):
        """Huge domain circle on ground."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 2))
        if r > 5:
            # Outer domain ring.
            pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["demon_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["demon_dark"], 200),
                                (x - r + 4, y + 42 - r // 3, r * 2 - 8, r * 2 // 3 - 4), 2)
            # Fill interior.
            pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["crack_dark"], 130),
                                (x - r + 8, y + 44 - r // 3, r * 2 - 16, r * 2 // 3 - 8))
            pygame.draw.ellipse(surface, (*_NS_vorgath.PALETTE["crack_mid"], 100),
                                (x - r + 12, y + 46 - r // 3, r * 2 - 24, r * 2 // 3 - 12))
            # Runes around edge.
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.2
                rx = x + int(math.cos(angle) * r * 0.9)
                ry = y + 44 + int(math.sin(angle) * r * 0.35)
                # Small rune symbol.
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_hot"], (rx - 1, ry, 2, 1))
                pygame.draw.rect(surface, _NS_vorgath.PALETTE["demon_shine"], (rx, ry, 1, 1))
    def _draw_demonic_domain_foreground(surface, boss, x, y, timer, phase):
        """Purple energy walls rising from domain circle."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 2))
        if r < 10:
            return
        # Rising energy pillars around edge.
        num_pillars = 16
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars + phase * 0.15
            px = x + int(math.cos(angle) * r * 0.85)
            py = y + 44 + int(math.sin(angle) * r * 0.35)
            # Vertical pillar.
            pillar_height = int(30 + math.sin(phase * 2 + i) * 5)
            for h in range(pillar_height):
                h_t = h / pillar_height
                py_layer = py - h
                alpha = _NS_vorgath._alpha(200 * (1 - h_t))
                width = max(1, 3 - h // 8)
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_dark"], alpha),
                                 (px - width, py_layer, width * 2, 1))
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                 (px, py_layer, 1, 1))
                if h < 6:
                    pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_hot"], alpha),
                                     (px, py_layer, 1, 1))
        # Rotating inner pull chains toward center.
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            edge_x = x + int(math.cos(angle) * r * 0.75)
            edge_y = y + 44 + int(math.sin(angle) * r * 0.3)
            # Chain segments from edge to center.
            for seg_t in range(0, 100, 15):
                st = seg_t / 100.0
                # Anim: chains move toward center.
                pull_t = (st + phase * 0.5) % 1.0
                sx = int(edge_x + (x - edge_x) * pull_t)
                sy = int(edge_y + (y + 44 - edge_y) * pull_t)
                alpha = _NS_vorgath._alpha(220 * (1 - pull_t * 0.5))
                _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["chain_dark"], alpha),
                                       (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_vorgath.PALETTE["demon_light"], alpha),
                                 (sx, sy, 1, 1))
        # Central vortex (energy swirl at boss position).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for vr in range(15, 3, -2):
            alpha = _NS_vorgath._alpha(100 * (15 - vr) / 15 * pulse)
            _NS_vorgath._aacircle(surface, (*_NS_vorgath.PALETTE["demon_mid"], alpha),
                                   (x, y + 44), vr)



# ====================================================================
# NEXTHYRIUS (CHAINED HOLLOW) - TRUE BOSS
# ====================================================================

class _NS_nexthyrius:
    """Namespace nexthyrius - True Boss spektral chain warden."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Spectral body (dark ghost/wraith)
        "spec_darkest": (2, 8, 12),
        "spec_dark": (10, 25, 35),
        "spec_mid": (25, 55, 70),
        "spec_light": (55, 100, 120),
        "spec_edge": (100, 160, 180),
        # Green soul fire (Thresh signature)
        "soul_darkest": (2, 20, 18),
        "soul_dark": (10, 60, 55),
        "soul_mid": (30, 160, 140),
        "soul_light": (80, 240, 200),
        "soul_hot": (170, 255, 230),
        "soul_shine": (230, 255, 245),
        # Bright teal (glowing eyes/lantern core)
        "teal_dark": (0, 80, 90),
        "teal_mid": (0, 180, 200),
        "teal_light": (80, 240, 255),
        "teal_shine": (200, 255, 255),
        # Chain (dark iron with glow)
        "chain_darkest": (5, 10, 12),
        "chain_dark": (25, 35, 40),
        "chain_mid": (70, 85, 95),
        "chain_light": (150, 170, 180),
        "chain_shine": (220, 235, 240),
        # Shoulder crown / horns (spec bone)
        "bone_dark": (30, 55, 55),
        "bone_mid": (90, 130, 130),
        "bone_light": (180, 220, 220),
        # Lantern glass/frame
        "lantern_frame_dark": (15, 20, 15),
        "lantern_frame_mid": (55, 65, 55),
        "lantern_frame_light": (130, 145, 135),
        "lantern_frame_gold": (180, 165, 80),
        "lantern_gold_light": (240, 220, 130),
        # Cape/robe tatters
        "robe_darkest": (2, 8, 10),
        "robe_dark": (10, 25, 30),
        "robe_mid": (30, 60, 65),
        "robe_light": (65, 110, 115),
        # Ground / crack (spectral corruption)
        "crack_dark": (2, 15, 12),
        "crack_mid": (15, 60, 50),
        "crack_light": (60, 180, 150),
        # Nether purple (TRUE BOSS accent)
        "nether_dark": (20, 10, 40),
        "nether_mid": (70, 40, 130),
        "nether_light": (150, 100, 220),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nexthyrius._clamp(color)
        if _NS_nexthyrius.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nexthyrius._clamp(color)
        if _NS_nexthyrius.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nexthyrius._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nexthyrius(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_nexthyrius._update_nex_attack_anim(boss)
        attacking = (
            getattr(boss, "_nex_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient BIG aura (TRUE BOSS).
        _NS_nexthyrius._draw_spectral_aura(surface, x, y, pulse)
        _NS_nexthyrius._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_nexthyrius._draw_hook_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nexthyrius._draw_lantern_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nexthyrius._draw_reap_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nexthyrius._draw_prison_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_nexthyrius._draw_nex_attack(surface, boss, x, y)
        else:
            _NS_nexthyrius._draw_nex_float(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_nexthyrius._draw_hook_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nexthyrius._draw_lantern_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nexthyrius._draw_reap_sweep(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nexthyrius._draw_prison_walls(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_nex_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nex_previous_timer", 0))
        active = bool(getattr(boss, "_nex_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nex_attack_active = True
            boss._nex_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nex_attack_frame = int(getattr(boss, "_nex_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nex_attack_active = False
            boss._nex_attack_frame = 0
            active = False
        boss._nex_previous_timer = timer
        boss._nex_attack_progress = (
            min(1.0, getattr(boss, "_nex_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_nex_float(surface, boss, x, y):
        """Ghostly floating idle."""
        bob = int(math.sin(boss.pulse * 0.5) * 6)  # deeper bob (bigger boss)
        sway = int(math.sin(boss.pulse * 0.35) * 3)
        _NS_nexthyrius._draw_shadow(surface, x + sway, y + 52, phase=boss.pulse)
        _NS_nexthyrius._draw_soul_wisps(surface, x + sway, y + 44, boss.pulse)
        _NS_nexthyrius._draw_nex_body(surface, x + sway, y + bob,
                                       boss.direction, boss.pulse, "idle")
    def _draw_nex_attack(surface, boss, x, y):
        progress = getattr(boss, "_nex_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back → chain whip forward → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_nexthyrius._draw_shadow(surface, x + lunge, y + 52, phase=boss.pulse)
        _NS_nexthyrius._draw_soul_wisps(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_nexthyrius._draw_nex_body(surface, x + lunge, y + bob - lift,
                                       boss.direction, boss.pulse, "attack", progress)
        # Chain whip projectile.
        _NS_nexthyrius._draw_basic_chain_whip(surface, boss, x + lunge,
                                               y + bob - lift, progress)
    # ============================================================
    # BODY
    # ============================================================
    def _draw_nex_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Spectral chain warden body."""
        # Trailing ghost tail (bottom - instead of legs, wraith form).
        _NS_nexthyrius._draw_ghost_tail(surface, cx, cy + 10, facing, phase)
        # Tattered robe.
        _NS_nexthyrius._draw_tattered_robe(surface, cx, cy, facing, phase)
        # Chained arms binding torso (decorative chains).
        _NS_nexthyrius._draw_body_chains(surface, cx, cy, facing, phase)
        # Torso (skeletal spectral).
        _NS_nexthyrius._draw_spectral_torso(surface, cx, cy, facing, phase)
        # Back arm (holding cape).
        _NS_nexthyrius._draw_back_arm(surface, cx, cy, facing, phase)
        # Massive spiked shoulder crown/spikes.
        _NS_nexthyrius._draw_shoulder_crown(surface, cx, cy - 8, facing, phase)
        # Ghostly head (skull-like with green flame).
        _NS_nexthyrius._draw_ghost_head(surface, cx + facing * 2, cy - 24, facing, phase)
        # Front arm with lantern/chain.
        _NS_nexthyrius._draw_lantern_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_ghost_tail(surface, cx, cy, facing, phase):
        """Wraith tail below body (no legs - ghost)."""
        sway = math.sin(phase * 0.6) * 4
        # Tapering ghost tail shape.
        segments = 7
        points_left = [(cx - 12, cy)]
        points_right = [(cx + 12, cy)]
        for i in range(1, segments + 1):
            t = i / segments
            width = int(12 * (1 - t * 0.85))
            offset_x = int(math.sin(phase * 0.8 + t * 3) * (4 + t * 4))
            y_off = int(t * 22)
            cx_here = cx + offset_x + int(sway * t * 0.5)
            points_left.append((cx_here - width, cy + y_off))
            points_right.append((cx_here + width, cy + y_off))
        # Combine into single polygon.
        tail_shape = points_left + list(reversed(points_right))
        # Shadow.
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 2) for p in tail_shape])
        # Layered tail with fading alpha.
        tail_surf = pygame.Surface((80, 40), pygame.SRCALPHA)
        offset_x_surf = cx - 40
        offset_y_surf = cy
        local_pts = [(p[0] - offset_x_surf, p[1] - offset_y_surf) for p in tail_shape]
        _NS_nexthyrius._poly(tail_surf, (*_NS_nexthyrius.PALETTE["spec_darkest"], 220), local_pts)
        # Inner smaller.
        inner_pts = []
        cx_local = sum(p[0] for p in local_pts) / len(local_pts)
        cy_local = sum(p[1] for p in local_pts) / len(local_pts)
        for p in local_pts:
            inner_pts.append((int(p[0] * 0.85 + cx_local * 0.15),
                              int(p[1] * 0.85 + cy_local * 0.15)))
        _NS_nexthyrius._poly(tail_surf, (*_NS_nexthyrius.PALETTE["spec_dark"], 200), inner_pts)
        # Inner glow.
        inner2_pts = []
        for p in local_pts:
            inner2_pts.append((int(p[0] * 0.65 + cx_local * 0.35),
                               int(p[1] * 0.65 + cy_local * 0.35)))
        _NS_nexthyrius._poly(tail_surf, (*_NS_nexthyrius.PALETTE["spec_mid"], 160), inner2_pts)
        surface.blit(tail_surf, (offset_x_surf, offset_y_surf))
        # Green soul flames rising from tail bottom.
        for i in range(6):
            flame_t = (phase * 0.6 + i * 0.16) % 1.0
            fx = cx - 8 + i * 3 + int(math.sin(phase + i) * 3)
            fy = cy + 20 - int(flame_t * 15)
            alpha = _NS_nexthyrius._alpha(200 * (1 - flame_t))
            if alpha > 0:
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_dark"], alpha),
                                          (fx, fy), 2)
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                 (fx, fy, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], alpha),
                                 (fx, fy - 1, 1, 1))
    def _draw_tattered_robe(surface, cx, cy, facing, phase):
        """Long tattered spectral robe."""
        sway = math.sin(phase * 0.6) * 3
        back = -facing
        # Robe wraps around body.
        robe_top_L = (cx - 12, cy - 10)
        robe_top_R = (cx + 12, cy - 10)
        robe_side_L = (cx - 16 + int(sway * 0.3), cy + 2)
        robe_side_R = (cx + 16 - int(sway * 0.3), cy + 2)
        robe_bot_L = (cx - 20 + int(sway * 0.6), cy + 16)
        robe_bot_R = (cx + 20 - int(sway * 0.6), cy + 16)
        # Back part flowing.
        robe_back_top = (cx + back * 8, cy - 12)
        robe_back_mid = (cx + back * 16 + int(sway), cy + 4)
        robe_back_bot = (cx + back * 22 + int(sway * 1.5), cy + 20)
        # Draw back flow first.
        back_shape = [robe_top_L if facing > 0 else robe_top_R,
                       robe_back_top, robe_back_mid, robe_back_bot,
                       robe_bot_L if facing > 0 else robe_bot_R,
                       robe_side_L if facing > 0 else robe_side_R]
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in back_shape])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["robe_darkest"], back_shape)
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["robe_dark"], [
            back_shape[0],
            (back_shape[1][0] + facing, back_shape[1][1] + 1),
            (back_shape[2][0] + facing * 2, back_shape[2][1]),
            (back_shape[3][0] + facing * 2, back_shape[3][1] - 2),
            back_shape[4],
            back_shape[5],
        ])
        # Front robe body.
        front_shape = [robe_top_L, robe_top_R, robe_side_R, robe_bot_R,
                        robe_bot_L, robe_side_L]
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["robe_darkest"], front_shape)
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["robe_dark"], [
            (robe_top_L[0] + 1, robe_top_L[1] + 1),
            (robe_top_R[0] - 1, robe_top_R[1] + 1),
            (robe_side_R[0] - 1, robe_side_R[1]),
            (robe_bot_R[0] - 2, robe_bot_R[1] - 2),
            (robe_bot_L[0] + 2, robe_bot_L[1] - 2),
            (robe_side_L[0] + 1, robe_side_L[1]),
        ])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["robe_mid"], [
            (cx - 8, cy - 8), (cx + 8, cy - 8),
            (cx + 10, cy + 4), (cx + 6, cy + 14),
            (cx - 6, cy + 14), (cx - 10, cy + 4),
        ])
        # Tattered edges (jagged bottom).
        for i in range(6):
            tear_x = cx - 15 + i * 6 + int(math.sin(phase + i) * 2)
            tear_y_top = cy + 12
            tear_y_bot = cy + 18 + int(math.sin(phase * 1.5 + i) * 3)
            pygame.draw.line(surface, _NS_nexthyrius.PALETTE["robe_darkest"],
                             (tear_x, tear_y_top), (tear_x, tear_y_bot), 2)
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["robe_dark"],
                             (tear_x, tear_y_top, 1, tear_y_bot - tear_y_top))
        # Green glow at robe edges (soul essence).
        for i, edge in enumerate([(cx - 18, cy + 14), (cx + 18, cy + 14),
                                    (cx, cy + 18)]):
            alpha = _NS_nexthyrius._alpha(160 + math.sin(phase * 2 + i) * 40)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                      edge, 3)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                      edge, 1)
    def _draw_body_chains(surface, cx, cy, facing, phase):
        """Decorative chains wrapping around body."""
        # Chain wraps around torso diagonally.
        wave = math.sin(phase * 0.8) * 1
        for chain_i, y_start in enumerate([-6, 0, 6]):
            for seg in range(6):
                t = seg / 6.0
                # Diagonal wrap.
                sx = int(cx - 12 + t * 24)
                sy = int(cy + y_start + math.sin(t * math.pi * 2 + phase + chain_i) * 2)
                if seg % 2 == 0:
                    _NS_nexthyrius._aacircle(surface,
                                              _NS_nexthyrius.PALETTE["chain_darkest"],
                                              (sx, sy), 2)
                    _NS_nexthyrius._aacircle(surface,
                                              _NS_nexthyrius.PALETTE["chain_mid"],
                                              (sx, sy), 1)
                else:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_darkest"],
                                     (sx - 1, sy - 1, 2, 2))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"],
                                     (sx, sy, 1, 1))
    def _draw_spectral_torso(surface, cx, cy, facing, phase):
        """Skeletal spectral torso."""
        breath = math.sin(phase * 0.6) * 1
        # Main torso.
        torso = [
            (cx - 10, cy - 14),
            (cx - 12, cy - 6),
            (cx - 10, cy + 2),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 10, cy + 2),
            (cx + 12, cy - 6),
            (cx + 10, cy - 14),
            (cx + 4, cy - 16),
            (cx - 4, cy - 16),
        ]
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in torso])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_darkest"], torso)
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_dark"], [
            (cx - 9, cy - 13), (cx - 11, cy - 6), (cx - 9, cy + 1),
            (cx - 5, cy + 7), (cx + 5, cy + 7), (cx + 9, cy + 1),
            (cx + 11, cy - 6), (cx + 9, cy - 13),
            (cx + 3, cy - 15), (cx - 3, cy - 15),
        ])
        # Rib cage lines (skeletal).
        for rib_y in (-10, -6, -2, 2):
            pygame.draw.line(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                             (cx - 7, cy + rib_y), (cx + 7, cy + rib_y), 1)
            pygame.draw.line(surface, _NS_nexthyrius.PALETTE["spec_mid"],
                             (cx - 6, cy + rib_y + 1), (cx + 6, cy + rib_y + 1), 1)
        # Central spine glow (soul channel).
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for i in range(4):
            y_seg = cy - 8 + i * 4
            alpha = _NS_nexthyrius._alpha(200 * pulse)
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_dark"], alpha),
                             (cx - 1, y_seg - 1, 2, 3))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                             (cx, y_seg, 1, 2))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], alpha),
                             (cx, y_seg, 1, 1))
        # Central chest jewel (heart soul).
        jewel_y = cy - 4
        for r in range(7, 0, -1):
            alpha = _NS_nexthyrius._alpha(180 * (7 - r) / 7 * pulse)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                      (cx, jewel_y), r)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_darkest"], (cx, jewel_y), 4)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_dark"], (cx, jewel_y), 3)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["teal_mid"], (cx, jewel_y), 2)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["teal_light"], (cx, jewel_y), 1)
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["white"], (cx, jewel_y, 1, 1))
    def _draw_shoulder_crown(surface, cx, cy, facing, phase):
        """Massive crown of spikes on shoulders (Thresh iconic)."""
        wave = math.sin(phase * 0.4) * 1
        # Bone spikes going up and out from shoulders.
        # 3 spikes each side + 3 in center rising taller.
        for i, (dx, dy, length, angle_deg) in enumerate([
            # Left side spikes.
            (-14, -4, 8, -110),
            (-12, -8, 12, -100),
            (-10, -12, 10, -90),
            # Center tall spikes (crown).
            (-6, -14, 16, -85),
            (-2, -16, 20, -85),  # tallest
            (2, -16, 20, -85),   # tallest
            (6, -14, 16, -85),
            # Right side spikes.
            (10, -12, 10, -90),
            (12, -8, 12, -100),
            (14, -4, 8, -110),
        ]):
            offset = int(wave) if i % 2 == 0 else -int(wave)
            angle_rad = math.radians(angle_deg)
            base_x = cx + dx
            base_y = cy + dy
            tip_x = base_x + int(math.cos(angle_rad) * length)
            tip_y = base_y + int(math.sin(angle_rad) * length) + offset
            # Spike body (bone with green glow).
            perp_x = -math.sin(angle_rad)
            perp_y = math.cos(angle_rad)
            base_a = (base_x + int(perp_x * 2), base_y + int(perp_y * 2))
            base_b = (base_x - int(perp_x * 2), base_y - int(perp_y * 2))
            # Shadow.
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                                  [(tip_x + 1, tip_y + 1),
                                   (base_a[0] + 1, base_a[1] + 1),
                                   (base_b[0] + 1, base_b[1] + 1)])
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                                  [(tip_x, tip_y), base_a, base_b])
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["bone_dark"], [
                (tip_x, tip_y),
                (int((tip_x + base_a[0]) / 2), int((tip_y + base_a[1]) / 2)),
                (base_x, base_y),
            ])
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["bone_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["bone_light"],
                             (tip_x, tip_y, 1, 1))
            # Green glow at spike tip.
            glow_alpha = _NS_nexthyrius._alpha(180 + math.sin(phase * 2 + i) * 40)
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_light"], glow_alpha),
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], glow_alpha),
                             (tip_x, tip_y - 1, 1, 1))
    def _draw_ghost_head(surface, cx, cy, facing, phase):
        """Ghostly demonic skull head with green flames."""
        # Skull-like head shape.
        head = [
            (cx - 7, cy + 4),
            (cx - 8, cy - 2),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 3, cy - 9),
            (cx + 7, cy - 6),
            (cx + 8, cy - 1),
            (cx + 6, cy + 4),
            (cx + 3, cy + 7),
            (cx - 3, cy + 7),
        ]
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                              [(px + 1, py + 2) for px, py in head])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_darkest"], head)
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_dark"], [
            (cx - 6, cy + 3), (cx - 7, cy - 2), (cx - 5, cy - 7),
            (cx - 1, cy - 9), (cx + 3, cy - 8), (cx + 6, cy - 5),
            (cx + 7, cy - 1), (cx + 5, cy + 3), (cx + 2, cy + 6),
            (cx - 2, cy + 6),
        ])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_mid"], [
            (cx - 4, cy + 1), (cx - 5, cy - 3), (cx - 3, cy - 6),
            (cx, cy - 7), (cx + 3, cy - 6), (cx + 5, cy - 3),
            (cx + 4, cy + 1), (cx + 2, cy + 4), (cx - 2, cy + 4),
        ])
        # Cheek highlight.
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["spec_light"], [
            (cx - 1, cy - 4), (cx + 2, cy - 3), (cx + 1, cy), (cx - 1, cy - 1),
        ])
        # SKULL FEATURES:
        # Deep eye sockets with GREEN FLAMES inside.
        _NS_nexthyrius._draw_flame_eyes(surface, cx, cy, phase)
        # Skeletal nose hole.
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                         (cx, cy - 1, 1, 1))
        # Grinning skeletal teeth.
        for tooth_x in (-3, -1, 1, 3):
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["bone_light"],
                             (cx + tooth_x, cy + 3, 1, 3))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                             (cx + tooth_x, cy + 3, 1, 1))
        # Cheek shadow.
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                         (cx - 4, cy + 2), (cx - 2, cy + 3), 1)
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                         (cx + 2, cy + 3), (cx + 4, cy + 2), 1)
        # GREEN FLAMES rising from top of head.
        _NS_nexthyrius._draw_head_flames(surface, cx, cy - 8, phase)
    def _draw_flame_eyes(surface, cx, cy, phase):
        """Deep green flaming eye sockets."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        flame_wave = math.sin(phase * 3) * 1
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 4
            # Deep socket.
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                             (ex - 2, ey - 2, 4, 4))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                             (ex - 1, ey - 1, 3, 3))
            # Green glow halo.
            for r in range(7, 0, -1):
                alpha = _NS_nexthyrius._alpha(120 * (7 - r) / 7 * pulse)
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                          (ex, ey), r)
            # Flame core (rising).
            flame_top_y = ey - 2 - int(flame_wave)
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_dark"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_mid"], (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["teal_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["teal_light"], (ex, ey, 1, 1))
            # Flame tip flicker.
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (ex, flame_top_y, 1, 1))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_head_flames(surface, cx, cy, phase):
        """Wispy green flames rising from top of skull."""
        for i in range(7):
            flame_t = (phase * 0.6 + i * 0.14) % 1.0
            fx = cx - 6 + i * 2 + int(math.sin(phase + i) * 2)
            fy = cy - int(flame_t * 14)
            alpha = _NS_nexthyrius._alpha(220 * (1 - flame_t))
            if alpha > 0:
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_darkest"], alpha),
                                          (fx, fy), 2)
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_dark"], alpha),
                                          (fx, fy), 1)
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                 (fx, fy, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                 (fx, fy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], alpha),
                                 (fx, fy - 2, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm (spectral, holding cape/relaxed)."""
        back = -facing
        sway = math.sin(phase * 0.5) * 1
        shoulder = (cx + back * 10, cy - 10)
        elbow = (cx + back * 14, cy + int(sway))
        hand = (cx + back * 12, cy + 8 + int(sway))
        # Shadow.
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                                (shoulder[0] + 1, shoulder[1] + 1),
                                (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                                (elbow[0] + 1, elbow[1] + 1),
                                (hand[0] + 1, hand[1] + 1), 4)
        # Upper arm (spectral/thin).
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                                shoulder, elbow, 5)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_dark"],
                                shoulder, elbow, 3)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_mid"],
                                (shoulder[0], shoulder[1] - 1),
                                (elbow[0], elbow[1] - 1), 1)
        # Forearm.
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                                elbow, hand, 4)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_dark"],
                                elbow, hand, 3)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_mid"],
                                (elbow[0] - 1, elbow[1]), (hand[0] - 1, hand[1]), 1)
        # Elbow joint.
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_dark"], elbow, 2)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_mid"], elbow, 1)
        # Skeletal claw hand.
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_dark"], hand, 3)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_mid"], hand, 2)
        # Claw fingers.
        for finger_off in (-2, 0, 2):
            pygame.draw.line(surface, _NS_nexthyrius.PALETTE["bone_dark"],
                             hand, (hand[0] + finger_off - back * 2,
                                    hand[1] + 3), 1)
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["bone_light"],
                             (hand[0] + finger_off - back * 2, hand[1] + 3, 1, 1))
    def _draw_lantern_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding spectral lantern with chain."""
        shoulder = (cx + facing * 10, cy - 10)
        # Arm angle based on attack.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: arm draws back.
                t = attack_progress / 0.35
                arm_angle = 0.25 + t * 0.4  # arm goes back
                lantern_dist = 12
            elif attack_progress < 0.6:
                # WHIP FORWARD!
                t = (attack_progress - 0.35) / 0.25
                arm_angle = 0.65 - t * 0.9  # arm swings forward
                lantern_dist = int(12 + t * 8)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = -0.25 + t * 0.5
                lantern_dist = int(20 - t * 8)
        else:
            # Idle: lantern hangs down and slightly forward.
            hover = math.sin(phase * 0.8) * 2
            arm_angle = 0.35
            lantern_dist = 14 + int(hover)
        # Calc elbow position.
        arm_len = 9
        elbow_x = shoulder[0] + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder[1] + int(math.sin(arm_angle) * arm_len)
        # Forearm slightly bent.
        forearm_angle = arm_angle + 0.15
        forearm_len = 8
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)
        # Lantern hangs below hand (or extends during attack).
        if action == "attack" and 0.35 < attack_progress < 0.6:
            # During swing: lantern extends forward with force.
            lantern_x = hand_x + facing * lantern_dist
            lantern_y = hand_y + int(lantern_dist * 0.3)
        else:
            # Idle/rest: lantern hangs below.
            lantern_x = hand_x + int(facing * lantern_dist * 0.3)
            lantern_y = hand_y + lantern_dist
        # === ARM ===
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                                (shoulder[0] + 1, shoulder[1] + 1),
                                (elbow_x + 1, elbow_y + 1), 6)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                                shoulder, (elbow_x, elbow_y), 5)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_dark"],
                                shoulder, (elbow_x, elbow_y), 4)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_mid"],
                                (shoulder[0], shoulder[1] - 1),
                                (elbow_x, elbow_y - 1), 2)
        # Forearm.
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                                (elbow_x + 1, elbow_y + 1),
                                (hand_x + 1, hand_y + 1), 5)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_darkest"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_dark"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_nexthyrius._aaline(surface, _NS_nexthyrius.PALETTE["spec_mid"],
                                (elbow_x - 1, elbow_y),
                                (hand_x - 1, hand_y), 1)
        # Elbow joint (bone).
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_dark"], (elbow_x, elbow_y), 3)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_mid"], (elbow_x, elbow_y), 2)
        # Skeletal claw hand.
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_dark"], (hand_x, hand_y), 4)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_mid"], (hand_x, hand_y), 3)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["bone_light"],
                                  (hand_x - 1, hand_y - 1), 1)
        # === CHAIN from hand to lantern ===
        num_links = 8
        for i in range(num_links + 1):
            t = i / num_links
            # Chain sags naturally (parabolic).
            sag = math.sin(t * math.pi) * 3 if action != "attack" else 0
            lx = int(hand_x + (lantern_x - hand_x) * t)
            ly = int(hand_y + (lantern_y - hand_y) * t + sag)
            if i % 2 == 0:
                _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (lx, ly), 2)
                _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_mid"], (lx, ly), 1)
            else:
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (lx - 1, ly - 1, 2, 2))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"], (lx, ly, 1, 1))
            # Green glow every 3rd link.
            if i % 3 == 0:
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_light"], (lx, ly, 1, 1))
        # === LANTERN ===
        _NS_nexthyrius._draw_lantern(surface, lantern_x, lantern_y, phase, action, attack_progress)
    def _draw_lantern(surface, lx, ly, phase, action, attack_progress):
        """Green spectral lantern with soul flame inside."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        intensity = 1.0
        if action == "attack" and 0.35 < attack_progress < 0.7:
            intensity = 1.5
        # === LANTERN FRAME ===
        # Top ring (where chain connects).
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_frame_dark"],
                         (lx - 2, ly - 7, 4, 2))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_frame_gold"],
                         (lx - 2, ly - 6, 4, 1))
        # Top cap.
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"], [
            (lx - 5, ly - 5), (lx + 5, ly - 5), (lx + 4, ly - 3), (lx - 4, ly - 3),
        ])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["lantern_frame_dark"], [
            (lx - 5, ly - 5), (lx + 5, ly - 5), (lx + 4, ly - 3), (lx - 4, ly - 3),
        ])
        _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["lantern_frame_gold"], [
            (lx - 4, ly - 5), (lx + 4, ly - 5), (lx + 3, ly - 4), (lx - 3, ly - 4),
        ])
        # Glass cage (frame vertical bars).
        # Aura glow first (behind lantern glass).
        for r in range(18, 3, -2):
            alpha = _NS_nexthyrius._alpha(100 * (18 - r) / 18 * pulse * intensity)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                      (lx, ly), r)
        for r in range(10, 2, -1):
            alpha = _NS_nexthyrius._alpha(160 * (10 - r) / 10 * pulse * intensity)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                      (lx, ly), r)
        # Lantern body (main box).
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                         (lx - 5, ly - 3, 10, 10))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_frame_dark"],
                         (lx - 5, ly - 3, 10, 10))
        # Glass interior.
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_darkest"],
                         (lx - 4, ly - 2, 8, 8))
        # SOUL FLAME inside (big glowing).
        flame_wave = math.sin(phase * 4) * 1
        flame_top_y = ly - 2 + int(flame_wave)
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_dark"],
                         (lx - 3, flame_top_y, 6, 7))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_mid"],
                         (lx - 2, flame_top_y + 1, 4, 6))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["teal_mid"],
                         (lx - 1, flame_top_y + 1, 3, 5))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["teal_light"],
                         (lx - 1, flame_top_y + 2, 3, 4))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_shine"],
                         (lx, flame_top_y + 2, 1, 3))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["white"],
                         (lx, flame_top_y + 3, 1, 1))
        # Vertical frame bars.
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["lantern_frame_mid"],
                         (lx - 5, ly - 3), (lx - 5, ly + 7), 1)
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["lantern_frame_mid"],
                         (lx + 4, ly - 3), (lx + 4, ly + 7), 1)
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["lantern_frame_mid"],
                         (lx, ly - 3), (lx, ly + 7), 1)
        # Horizontal bars.
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["lantern_frame_mid"],
                         (lx - 5, ly + 2), (lx + 4, ly + 2), 1)
        # Bottom cap.
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_frame_dark"],
                         (lx - 5, ly + 7, 10, 2))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_frame_gold"],
                         (lx - 4, ly + 7, 8, 1))
        # Gold highlights on frame corners.
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_gold_light"],
                         (lx - 5, ly - 3, 1, 1))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_gold_light"],
                         (lx + 4, ly - 3, 1, 1))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_gold_light"],
                         (lx - 5, ly + 7, 1, 1))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["lantern_gold_light"],
                         (lx + 4, ly + 7, 1, 1))
        # Sparks around lantern during attack.
        if action == "attack" and 0.35 < attack_progress < 0.7:
            for i in range(8):
                spark_angle = phase * 5 + i * math.pi / 4
                sx = lx + int(math.cos(spark_angle) * 12)
                sy = ly + int(math.sin(spark_angle) * 12)
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_shine"], (sx, sy, 1, 1))
    # ============================================================
    # BASIC ATTACK: CHAIN WHIP (ranged)
    # ============================================================
    def _draw_basic_chain_whip(surface, boss, x, y, progress):
        """Chain whip during basic attack (short-range chain flick)."""
        if progress < 0.4:
            return
        facing = boss.direction
        tx, ty = _NS_nexthyrius._target_position(boss, x, y)
        # Whip goes forward.
        t = (progress - 0.4) / 0.35
        t = min(1.0, t)
        start_x = x + facing * 22
        start_y = y + 2
        # Whip extends forward reaching partway to target.
        whip_range = min(180, math.hypot(tx - start_x, ty - start_y))
        angle_to_target = math.atan2(ty - start_y, tx - start_x)
        end_x = int(start_x + math.cos(angle_to_target) * whip_range * t)
        end_y = int(start_y + math.sin(angle_to_target) * whip_range * t)
        # Draw chain segments.
        num_segs = 12
        for i in range(num_segs):
            seg_t = i / num_segs
            sx = int(start_x + (end_x - start_x) * seg_t)
            sy = int(start_y + (end_y - start_y) * seg_t)
            # Wave motion during whip.
            wave = math.sin(seg_t * math.pi * 2 - progress * 8) * 3 * (1 - seg_t)
            perp = angle_to_target + math.pi / 2
            sx += int(math.cos(perp) * wave)
            sy += int(math.sin(perp) * wave)
            if i % 2 == 0:
                _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (sx, sy), 3)
                _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_mid"], (sx, sy), 2)
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"], (sx, sy, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_darkest"],
                                 (sx - 2, sy - 2, 4, 4))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_mid"], (sx - 1, sy - 1, 2, 2))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"], (sx, sy, 1, 1))
            # Green glow.
            if i % 3 == 0:
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_light"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (sx, sy - 1, 1, 1))
        # Chain tip: hook/blade.
        _NS_nexthyrius._draw_hook_tip(surface, end_x, end_y, angle_to_target)
    def _draw_hook_tip(surface, x, y, angle):
        """Sharp hook at chain tip."""
        # Base.
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (x, y), 4)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_dark"], (x, y), 3)
        # Hook barbs (spikes going backward from tip).
        for barb_angle in (math.pi * 0.7, math.pi * 1.3):
            actual_angle = angle + barb_angle
            barb_x = x + int(math.cos(actual_angle) * 5)
            barb_y = y + int(math.sin(actual_angle) * 5)
            pygame.draw.line(surface, _NS_nexthyrius.PALETTE["chain_darkest"],
                             (x, y), (barb_x, barb_y), 2)
            pygame.draw.line(surface, _NS_nexthyrius.PALETTE["chain_light"],
                             (x, y), (barb_x, barb_y), 1)
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_shine"],
                             (barb_x, barb_y, 1, 1))
        # Bright green core at hook.
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_darkest"], (x, y), 2)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_mid"], (x, y), 1)
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (x, y, 1, 1))
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["white"], (x, y, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, phase=0):
        """Big spectral shadow."""
        offset_y = int(math.sin(phase * 0.5) * 2)
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius, 140 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 8, 5, 170), (5, 8, 150, 16))
        pygame.draw.ellipse(shadow, (10, 60, 45, 120), (12, 10, 136, 12))
        surface.blit(shadow, (x - 80, y - 16 + offset_y))
    def _draw_soul_wisps(surface, cx, cy, phase, intense=False):
        """Green soul wisps + tortured souls rising."""
        strength = 1.4 if intense else 1.0
        # Wisps rising.
        for i in range(10):
            wisp_t = (phase * 0.4 + i * 0.12) % 1.0
            wx = cx - 22 + i * 4 + int(math.sin(phase + i) * 3)
            wy = cy + 14 - int(wisp_t * 28)
            alpha = _NS_nexthyrius._alpha(220 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_darkest"], alpha),
                                          (wx, wy), 3)
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_dark"], alpha),
                                          (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                 (wx, wy, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                 (wx, wy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], alpha),
                                 (wx, wy - 2, 1, 1))
        # Tortured ghost faces (small skulls).
        for i in range(4):
            skull_t = (phase * 0.3 + i * 0.28) % 1.0
            sx = cx - 18 + i * 12 + int(math.sin(phase + i * 2) * 4)
            sy = cy + 10 - int(skull_t * 32)
            alpha = _NS_nexthyrius._alpha(160 * (1 - skull_t) * strength)
            if alpha > 0:
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["bone_mid"], alpha),
                                          (sx, sy), 3)
                # Eyes.
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["shadow_deep"], alpha),
                                 (sx - 1, sy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["shadow_deep"], alpha),
                                 (sx + 1, sy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                 (sx - 1, sy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                 (sx + 1, sy - 1, 1, 1))
                # Mouth.
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["shadow_deep"], alpha),
                                 (sx, sy + 1, 1, 1))
    def _draw_spectral_aura(surface, x, y, phase):
        """Massive intimidating aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        # Outer aura.
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(115, 5, -5):
            alpha = _NS_nexthyrius._alpha((115 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_nexthyrius._aacircle(aura, (*_NS_nexthyrius.PALETTE["spec_darkest"], alpha),
                                          (130, 110), radius)
        for radius in range(80, 5, -4):
            alpha = _NS_nexthyrius._alpha((80 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nexthyrius._aacircle(aura, (*_NS_nexthyrius.PALETTE["soul_darkest"], alpha),
                                          (130, 110), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_nexthyrius._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nexthyrius._aacircle(aura, (*_NS_nexthyrius.PALETTE["soul_dark"], alpha),
                                          (130, 110), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_nexthyrius._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nexthyrius._aacircle(aura, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                          (130, 110), radius)
        # Purple nether inner tint.
        for radius in range(25, 5, -3):
            alpha = _NS_nexthyrius._alpha((25 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nexthyrius._aacircle(aura, (*_NS_nexthyrius.PALETTE["nether_dark"], alpha),
                                          (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Floating embers (green + purple).
        for i in range(18):
            angle = phase * 0.3 + i * math.pi / 9
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_nexthyrius.PALETTE["soul_mid"] if i % 4 != 0 else _NS_nexthyrius.PALETTE["nether_mid"]
            hot = _NS_nexthyrius.PALETTE["soul_hot"] if i % 4 != 0 else _NS_nexthyrius.PALETTE["nether_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Big ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nexthyrius.PALETTE["soul_darkest"], 200),
                            (5, 20, 180, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_nexthyrius.PALETTE["soul_dark"], 220),
                            (14, 22, 162, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_nexthyrius.PALETTE["soul_mid"], 230),
                            (25, 24, 140, 20), 1)
        pygame.draw.ellipse(ring, (*_NS_nexthyrius.PALETTE["nether_dark"], 180),
                            (40, 26, 110, 16), 1)
        # Runes.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 34 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_nexthyrius.PALETTE["soul_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_nexthyrius.PALETTE["soul_hot"],
                                        _NS_nexthyrius._alpha(180 * pulse)),
                                (15, 12, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))
    # ============================================================
    # SKILL Q: DEATH SENTENCE (long hook projectile)
    # ============================================================
    def _draw_hook_ground(surface, boss, x, y, timer, phase):
        """Windup ground effect at boss feet."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Green energy pooling at boss location during hook.
        for i in range(3):
            r = int(20 + i * 5 + math.sin(phase * 2) * 2)
            alpha = _NS_nexthyrius._alpha(150 - i * 40)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                      (x, y + 44), r, 2)
    def _draw_hook_projectile(surface, boss, x, y, timer, phase):
        """Long-range hook chain projectile - Thresh Q signature."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nexthyrius._target_position(boss, x, y)
        if progress < 0.15:
            # Windup: chain gathering in hand.
            t = progress / 0.15
            hand_x = x + facing * 22
            hand_y = y - 4
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_nexthyrius._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_dark"], alpha),
                                          (hand_x, hand_y), r)
            _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_mid"], (hand_x, hand_y), cr)
            _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_hot"], (hand_x, hand_y), max(1, cr - 3))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["white"], (hand_x, hand_y, 1, 1))
            # Sparks.
            for i in range(5):
                angle = phase * 4 + i * math.pi / 2.5
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (sx, sy, 1, 1))
        elif progress < 0.6:
            # Chain flying forward.
            t = (progress - 0.15) / 0.45
            start_x = x + facing * 26
            start_y = y - 4
            # Hook position (extends toward target).
            hook_x = int(start_x + (tx - start_x) * t)
            hook_y = int(start_y + (ty - start_y) * t)
            # === CHAIN SEGMENTS ===
            num_segs = 15
            angle_to = math.atan2(hook_y - start_y, hook_x - start_x)
            for i in range(num_segs + 1):
                seg_t = i / num_segs
                if seg_t > t:
                    break
                # Position along chain (only up to current hook position).
                actual_t = seg_t
                sx = int(start_x + (tx - start_x) * actual_t)
                sy = int(start_y + (ty - start_y) * actual_t)
                # Small wave.
                wave = math.sin(seg_t * math.pi * 4 + phase * 6) * 2
                perp = angle_to + math.pi / 2
                sx += int(math.cos(perp) * wave)
                sy += int(math.sin(perp) * wave)
                # Draw link.
                _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                                          (sx + 1, sy + 1), 3)
                if i % 2 == 0:
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (sx, sy), 3)
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_dark"], (sx, sy), 2)
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_light"], (sx - 1, sy - 1), 1)
                else:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_darkest"],
                                     (sx - 2, sy - 2, 4, 4))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_mid"],
                                     (sx - 1, sy - 1, 2, 2))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"], (sx, sy, 1, 1))
                # Green glow on chain.
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_light"], (sx, sy, 1, 1))
                if i % 2 == 0:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (sx, sy - 1, 1, 1))
            # === GLOWING TRAIL behind hook ===
            for glow_i in range(6):
                glow_t = max(0, t - glow_i * 0.06)
                gx = int(start_x + (tx - start_x) * glow_t)
                gy = int(start_y + (ty - start_y) * glow_t)
                alpha = _NS_nexthyrius._alpha(220 - glow_i * 32)
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                          (gx, gy), max(1, 6 - glow_i))
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                          (gx, gy), max(1, 4 - glow_i))
            # === HOOK HEAD (menacing) ===
            _NS_nexthyrius._draw_hook_tip(surface, hook_x, hook_y, angle_to)
            # Extra bright glow around hook.
            for r in range(10, 2, -1):
                alpha = _NS_nexthyrius._alpha(120 * (10 - r) / 10)
                _NS_nexthyrius._aacircle(surface,
                                          (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                          (hook_x, hook_y), r)
            # Impact burst.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                burst_r = int(15 + st * 20)
                burst_alpha = _NS_nexthyrius._alpha(240 * (1 - st))
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_darkest"], burst_alpha),
                                          (hook_x, hook_y), burst_r + 3, 3)
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], burst_alpha),
                                          (hook_x, hook_y), burst_r, 2)
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_light"], burst_alpha),
                                          (hook_x, hook_y), max(1, burst_r - 5), 1)
                for i in range(10):
                    ang = i * math.pi / 5
                    ex = hook_x + int(math.cos(ang) * burst_r)
                    ey = hook_y + int(math.sin(ang) * burst_r)
                    pygame.draw.rect(surface,
                                     (*_NS_nexthyrius.PALETTE["soul_hot"], burst_alpha),
                                     (ex, ey, 2, 2))
        else:
            # Pulling target back (chain retracts).
            t = (progress - 0.6) / 0.4
            start_x = x + facing * 26
            start_y = y - 4
            # Hook pulls back toward boss.
            hook_x = int(tx + (start_x - tx) * t)
            hook_y = int(ty + (start_y - ty) * t)
            # Chain from boss to hook.
            num_segs = 12
            for i in range(num_segs + 1):
                seg_t = i / num_segs
                sx = int(start_x + (hook_x - start_x) * seg_t)
                sy = int(start_y + (hook_y - start_y) * seg_t)
                if i % 2 == 0:
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (sx, sy), 3)
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_mid"], (sx, sy), 2)
                else:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_dark"], (sx - 1, sy - 1, 2, 2))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_light"], (sx, sy, 1, 1))
            # Hook head.
            _NS_nexthyrius._draw_hook_tip(surface, hook_x, hook_y,
                                            math.atan2(start_y - hook_y, start_x - hook_x))
    # ============================================================
    # SKILL W: DARK PASSAGE (lantern projectile)
    # ============================================================
    def _draw_lantern_ground(surface, boss, x, y, timer, phase):
        """Safe zone at lantern destination."""
        tx, ty = _NS_nexthyrius._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.4:
            # Circle of safety at destination.
            r = int(35 + math.sin(phase * 2) * 3)
            alpha = _NS_nexthyrius._alpha(220)
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                (tx - r + 6, ty - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
            # Runes.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.3
                rx = tx + int(math.cos(angle) * r * 0.85)
                ry = ty + int(math.sin(angle) * r * 0.32)
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (rx, ry, 2, 1))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_shine"], (rx, ry, 1, 1))
    def _draw_lantern_projectile(surface, boss, x, y, timer, phase):
        """Lantern arcs through air to target location."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nexthyrius._target_position(boss, x, y)
        if progress < 0.4:
            # Lantern flying (parabolic arc).
            t = progress / 0.4
            start_x = x + facing * 24
            start_y = y - 4
            # Parabolic arc trajectory.
            lx = int(start_x + (tx - start_x) * t)
            arc_height = -30  # up
            ly = int(start_y + (ty - start_y) * t + arc_height * math.sin(t * math.pi))
            # Chain trailing from boss to lantern.
            num_segs = 15
            for i in range(num_segs):
                seg_t = i / num_segs * t
                sx = int(start_x + (tx - start_x) * seg_t)
                sy = int(start_y + (ty - start_y) * seg_t
                          + arc_height * math.sin(seg_t * math.pi))
                if i % 2 == 0:
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"], (sx, sy), 2)
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_mid"], (sx, sy), 1)
                else:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_dark"], (sx - 1, sy - 1, 2, 2))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"], (sx, sy, 1, 1))
                if i % 3 == 0:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_light"], (sx, sy, 1, 1))
            # Big glowing lantern.
            for r in range(15, 3, -2):
                alpha = _NS_nexthyrius._alpha(120 * (15 - r) / 15)
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                          (lx, ly), r)
            _NS_nexthyrius._draw_lantern(surface, lx, ly, phase, "idle", 0)
        else:
            # Lantern rests at destination + pulsing glow.
            t = (progress - 0.4) / 0.6
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            # Ambient lantern glow at target.
            for r in range(25, 3, -2):
                alpha = _NS_nexthyrius._alpha(100 * (25 - r) / 25 * pulse)
                _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                          (tx, ty - 8), r)
            _NS_nexthyrius._draw_lantern(surface, tx, ty - 8, phase, "idle", 0)
            # Sparks rising.
            for i in range(8):
                spark_t = (phase * 0.8 + i * 0.125) % 1.0
                sx = tx - 8 + i * 2 + int(math.sin(phase + i) * 3)
                sy = ty - int(spark_t * 20)
                alpha = _NS_nexthyrius._alpha(200 * (1 - spark_t))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], alpha), (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_shine"], alpha), (sx, sy - 1, 1, 1))
    # ============================================================
    # SKILL E: FLAY (sweeping chain arc)
    # ============================================================
    def _draw_reap_ground(surface, boss, x, y, timer, phase):
        """Arc mark on ground during sweep."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground arc trail.
        arc_r = 55
        arc_alpha = _NS_nexthyrius._alpha(180 * (1 - progress))
        for i in range(-6, 7):
            angle = i * math.pi / 15
            gx = x + int(math.cos(angle) * arc_r) * facing
            gy = y + 44 + int(math.sin(angle) * arc_r * 0.3)
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], arc_alpha),
                             (gx, gy, 2, 1))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], arc_alpha),
                             (gx, gy, 1, 1))
    def _draw_reap_sweep(surface, boss, x, y, timer, phase):
        """Sweeping chain arc from behind to in front."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Arc animates from back to front.
        arc_center_x = x + facing * 5
        arc_center_y = y - 5
        arc_radius = 55
        # Current sweep angle (from behind to forward).
        start_angle = -math.pi * 0.7
        end_angle = math.pi * 0.3
        current_angle = start_angle + (end_angle - start_angle) * progress
        # Draw arc chain (multiple segments).
        for i in range(-3, 4):
            offset_angle = current_angle + i * 0.15
            for r_off in range(0, 5):
                seg_r = arc_radius - r_off * 2
                sx = arc_center_x + int(math.cos(offset_angle) * seg_r) * facing
                sy = arc_center_y + int(math.sin(offset_angle) * seg_r)
                alpha = _NS_nexthyrius._alpha(220 - abs(i) * 40 - r_off * 20)
                if alpha > 0:
                    _NS_nexthyrius._aacircle(surface,
                                              (*_NS_nexthyrius.PALETTE["chain_darkest"], alpha),
                                              (sx, sy), 3)
                    _NS_nexthyrius._aacircle(surface,
                                              (*_NS_nexthyrius.PALETTE["chain_mid"], alpha),
                                              (sx, sy), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_nexthyrius.PALETTE["soul_light"], alpha),
                                     (sx, sy, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_nexthyrius.PALETTE["soul_hot"], alpha),
                                     (sx, sy - 1, 1, 1))
        # Motion trail crescent glow.
        for trail_i in range(6):
            trail_angle = current_angle - trail_i * 0.12
            if trail_angle < start_angle:
                break
            for j in range(-2, 3):
                offset = j * 0.08
                tr_x = arc_center_x + int(math.cos(trail_angle + offset) * arc_radius) * facing
                tr_y = arc_center_y + int(math.sin(trail_angle + offset) * arc_radius)
                alpha = _NS_nexthyrius._alpha(180 * (1 - trail_i / 6))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                 (tr_x, tr_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], alpha),
                                 (tr_x, tr_y, 1, 1))
    # ============================================================
    # SKILL R: THE VOID PRISON (chain cage ultimate)
    # ============================================================
    def _draw_prison_ground(surface, boss, x, y, timer, phase):
        """Prison ground circle."""
        tx, ty = _NS_nexthyrius._target_position(boss, x, y)
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2.5))
        if r > 5:
            # Dark prison floor.
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_dark"], 200),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            # Purple void inside.
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["nether_dark"], 200),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10))
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["shadow_deep"], 180),
                                (tx - r + 15, ty - r // 3 + 7,
                                 r * 2 - 30, r * 2 // 3 - 14))
            # Rune circles at edge.
            for i in range(16):
                angle = i * math.pi / 8 + phase * 0.15
                rx = tx + int(math.cos(angle) * r * 0.9)
                ry = ty + int(math.sin(angle) * r * 0.32)
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"], (rx - 1, ry, 3, 1))
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_shine"], (rx, ry, 1, 1))
    def _draw_prison_walls(surface, boss, x, y, timer, phase):
        """Vertical chain walls forming a cage."""
        tx, ty = _NS_nexthyrius._target_position(boss, x, y)
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2.5))
        if r < 10:
            return
        # Circle of vertical chain bars.
        num_bars = 20
        for i in range(num_bars):
            angle = i * math.pi * 2 / num_bars + phase * 0.1
            bar_x = tx + int(math.cos(angle) * r * 0.9)
            bar_y_base = ty + int(math.sin(angle) * r * 0.32)
            # Bar height.
            bar_height = int(45 + math.sin(phase * 2 + i * 0.5) * 3)
            # Draw vertical chain bar.
            for seg in range(bar_height // 4):
                seg_y = bar_y_base - seg * 4
                # Alternate link style.
                if seg % 2 == 0:
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_darkest"],
                                              (bar_x, seg_y), 3)
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_dark"],
                                              (bar_x, seg_y), 2)
                    _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["chain_light"],
                                              (bar_x - 1, seg_y - 1), 1)
                else:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_darkest"],
                                     (bar_x - 2, seg_y - 2, 4, 4))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_mid"],
                                     (bar_x - 1, seg_y - 1, 2, 2))
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["chain_light"],
                                     (bar_x, seg_y, 1, 1))
                # Green energy on chain.
                pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_light"],
                                 (bar_x, seg_y, 1, 1))
                if seg % 2 == 0:
                    pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"],
                                     (bar_x, seg_y - 1, 1, 1))
            # Top spike/tip.
            top_y = bar_y_base - bar_height
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["shadow_deep"], [
                (bar_x - 2, top_y + 1),
                (bar_x + 2, top_y + 1),
                (bar_x, top_y - 5),
            ])
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["chain_darkest"], [
                (bar_x - 2, top_y),
                (bar_x + 2, top_y),
                (bar_x, top_y - 4),
            ])
            _NS_nexthyrius._poly(surface, _NS_nexthyrius.PALETTE["chain_mid"], [
                (bar_x - 1, top_y),
                (bar_x + 1, top_y),
                (bar_x, top_y - 3),
            ])
            # Green tip glow.
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_hot"],
                             (bar_x, top_y - 4, 1, 1))
            pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["soul_shine"],
                             (bar_x, top_y - 4, 1, 1))
        # Horizontal green energy rings connecting bars (top and middle).
        for ring_y_off in (-20, -40):
            ring_alpha = _NS_nexthyrius._alpha(180 + math.sin(phase * 2) * 30)
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_dark"], ring_alpha),
                                (tx - int(r * 0.9), ty + ring_y_off - int(r * 0.32),
                                 int(r * 1.8), int(r * 0.64)), 2)
            pygame.draw.ellipse(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], ring_alpha),
                                (tx - int(r * 0.85), ty + ring_y_off - int(r * 0.3),
                                 int(r * 1.7), int(r * 0.6)), 1)
        # Ghost skulls trapped inside prison.
        for i in range(4):
            ghost_angle = phase * 0.3 + i * math.pi / 2
            ghost_r = r * 0.4
            gx = tx + int(math.cos(ghost_angle) * ghost_r)
            gy = ty - 15 + int(math.sin(ghost_angle) * ghost_r * 0.5)
            ghost_alpha = _NS_nexthyrius._alpha(180)
            # Ghost body.
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_dark"], ghost_alpha),
                                      (gx, gy), 5)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], ghost_alpha),
                                      (gx, gy), 3)
            # Eyes.
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["shadow_deep"], ghost_alpha),
                             (gx - 1, gy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["shadow_deep"], ghost_alpha),
                             (gx + 1, gy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], ghost_alpha),
                             (gx - 1, gy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_nexthyrius.PALETTE["soul_hot"], ghost_alpha),
                             (gx + 1, gy - 1, 1, 1))
        # Central menacing eye at prison center (watching).
        center_pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_r = int(6 + math.sin(phase) * 1)
        for er in range(eye_r + 5, 0, -1):
            alpha = _NS_nexthyrius._alpha(120 * (eye_r + 5 - er) / (eye_r + 5) * center_pulse)
            _NS_nexthyrius._aacircle(surface, (*_NS_nexthyrius.PALETTE["soul_mid"], alpha),
                                      (tx, ty - 12), er)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["soul_darkest"], (tx, ty - 12), eye_r)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["teal_mid"], (tx, ty - 12), eye_r - 2)
        _NS_nexthyrius._aacircle(surface, _NS_nexthyrius.PALETTE["teal_light"], (tx, ty - 12), 2)
        pygame.draw.rect(surface, _NS_nexthyrius.PALETTE["white"], (tx, ty - 12, 1, 1))
        # Vertical pupil.
        pygame.draw.line(surface, _NS_nexthyrius.PALETTE["shadow_deep"],
                         (tx, ty - 15), (tx, ty - 9), 1)

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kurogari(surface, boss, x, y):
    """Entry point kurogari."""
    return _NS_kurogari.draw_kurogari(surface, boss, x, y)


def draw_morvekhar(surface, boss, x, y):
    """Entry point morvekhar."""
    return _NS_morvekhar.draw_morvekhar(surface, boss, x, y)


def draw_vorgath(surface, boss, x, y):
    """Entry point vorgath."""
    return _NS_vorgath.draw_vorgath(surface, boss, x, y)


def draw_nexthyrius(surface, boss, x, y):
    """Entry point nexthyrius."""
    return _NS_nexthyrius.draw_nexthyrius(surface, boss, x, y)
