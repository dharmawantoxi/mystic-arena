"""
bosses/level14.py - Semua boss Level 14

Berisi:
  - azureth     (mini boss - RANGED arcane sky-scribe)
  - luminar     (mini boss - RANGED eternal custodian, mounted)
  - solara      (mini boss - MELEE dawnforged sentinel)
  - pyraethis   (TRUE BOSS - Eternal Firebird, RANGED)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan: state prefix Solara di-rename _sol_ -> _slr_ supaya tidak
bentrok dengan Solvarin (Level 13) saat dua-duanya jadi hero
bersamaan. Nama fungsi namespace (_draw_sol_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# azureth.py
# ====================================================================



class _NS_azureth:
    """Namespace azureth - Arcane Sky-Scribe mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe biru (main body/cloak)
        "robe_darkest": (5, 10, 30),
        "robe_dark": (15, 30, 75),
        "robe_mid": (35, 65, 140),
        "robe_light": (75, 120, 210),
        "robe_edge": (130, 180, 250),
        "robe_shine": (200, 230, 255),

        # Gold trim (armor, ornaments)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (100, 70, 20),
        "gold_mid": (185, 140, 45),
        "gold_light": (240, 205, 100),
        "gold_shine": (255, 245, 180),

        # Skin (pale mystical)
        "skin_dark": (100, 80, 90),
        "skin_mid": (170, 145, 155),
        "skin_light": (220, 200, 205),
        "skin_shine": (245, 230, 235),

        # Arcane blue energy (magic, projectile, orb)
        "arc_darkest": (5, 15, 40),
        "arc_dark": (20, 55, 130),
        "arc_mid": (60, 130, 230),
        "arc_light": (140, 200, 255),
        "arc_hot": (200, 235, 255),
        "arc_shine": (245, 250, 255),

        # Eye glow (bright cyan-white)
        "eye_socket": (5, 5, 15),
        "eye_darkest": (10, 30, 70),
        "eye_dark": (30, 80, 170),
        "eye_mid": (100, 180, 255),
        "eye_light": (200, 240, 255),
        "eye_glow": (255, 255, 255),

        # Hair/beard (silver-white)
        "hair_dark": (80, 90, 110),
        "hair_mid": (150, 160, 180),
        "hair_light": (220, 225, 240),
        "hair_shine": (250, 252, 255),

        # Wing feathers (gold/white crown wings)
        "wing_dark": (100, 75, 25),
        "wing_mid": (200, 165, 70),
        "wing_light": (250, 220, 130),
        "wing_shine": (255, 250, 210),

        # Staff wood (dark)
        "staff_dark": (25, 15, 10),
        "staff_mid": (60, 40, 25),
        "staff_light": (110, 80, 50),

        # Mystic sparkles / stars
        "star_dim": (100, 130, 200),
        "star_bright": (230, 240, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 6),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_azureth._clamp(color)
        if _NS_azureth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_azureth._clamp(color)
        if _NS_azureth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_azureth._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_azureth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_azureth._update_azu_attack_anim(boss)
        attacking = (
            getattr(boss, "_azu_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_azureth._draw_arcane_aura(surface, x, y, pulse)
        _NS_azureth._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_azureth._draw_concussive_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_azureth._draw_ancientseal_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_azureth._draw_mysticflare_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (always floating).
        if attacking:
            _NS_azureth._draw_azu_attack(surface, boss, x, y)
        else:
            _NS_azureth._draw_azu_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_azureth._draw_arcanebolt_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_azureth._draw_concussive_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_azureth._draw_ancientseal_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_azureth._draw_mysticflare_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_azu_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_azu_previous_timer", 0))
        active = bool(getattr(boss, "_azu_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._azu_attack_active = True
            boss._azu_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._azu_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._azu_attack_frame = int(
                getattr(boss, "_azu_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._azu_attack_active = False
            boss._azu_attack_frame = 0
            active = False

        boss._azu_previous_timer = timer
        boss._azu_attack_progress = (
            min(1.0, getattr(boss, "_azu_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS (all floating)
    # ============================================================
    def _draw_azu_idle(surface, boss, x, y):
        # Floating bob (gentle up/down).
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_azureth._draw_floating_shadow(surface, x, y + 50, boss.pulse)
        _NS_azureth._draw_arcane_wisps(surface, x, y + 40, boss.pulse)
        _NS_azureth._draw_azu_body(surface, x, y + bob,
                                    boss.direction, boss.pulse, "idle")

    def _draw_azu_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_azu_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_azu_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Floating base bob.
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        # Cast animation: pull staff back → thrust forward.
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 3)
            lean = int(t * -2) * facing
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            lift = int(3 - t * 5)
            lean = int((-2 + t * 6)) * facing
        else:
            t = (progress - 0.55) / 0.45
            lift = int(-2 + t * 2)
            lean = int(4 * (1 - t)) * facing

        _NS_azureth._draw_floating_shadow(surface, x + lean, y + 50, boss.pulse)
        _NS_azureth._draw_arcane_wisps(surface, x + lean, y + 40, boss.pulse,
                                        intense=True)
        _NS_azureth._draw_azu_body(surface, x + lean, y + bob - lift,
                                    facing, boss.pulse, "attack",
                                    progress)
        _NS_azureth._draw_arcane_projectile(surface, boss, x + lean,
                                             y + bob - lift, progress)

    # ============================================================
    # BODY (humanoid mage: head, robe, arms, staff)
    # ============================================================
    def _draw_azu_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Draw robe/lower body first (behind).
        _NS_azureth._draw_flowing_robe(surface, cx, cy + 6, facing, phase)

        # Torso.
        _NS_azureth._draw_mage_torso(surface, cx, cy - 2, facing, phase)

        # Cape behind head.
        _NS_azureth._draw_cape(surface, cx, cy - 4, facing, phase)

        # Arms (holding staff).
        _NS_azureth._draw_mage_arms(surface, cx, cy - 2, facing, phase, action,
                                     attack_progress)

        # Head last (front).
        _NS_azureth._draw_mage_head(surface, cx, cy - 14, facing, phase, action,
                                     attack_progress)

        # Staff (drawn between arms).
        _NS_azureth._draw_arcane_staff(surface, cx, cy - 2, facing, phase, action,
                                        attack_progress)

    def _draw_flowing_robe(surface, cx, cy, facing, phase):
        """Flowing lower robe (like a dress, tapered wider at bottom)."""
        sway = math.sin(phase * 0.8) * 2

        # Robe shape (trapezoid tapered).
        robe_pts = [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 14 + int(sway), cy + 12),
            (cx + 10 + int(sway), cy + 18),
            (cx + 3 + int(sway * 0.5), cy + 22),
            (cx - 3 - int(sway * 0.5), cy + 22),
            (cx - 10 - int(sway), cy + 18),
            (cx - 14 - int(sway), cy + 12),
        ]

        _NS_azureth._poly(surface, _NS_azureth.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in robe_pts])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_darkest"], robe_pts)

        # Mid tone.
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 12 + int(sway), cy + 12),
            (cx + 8 + int(sway), cy + 17),
            (cx - 8 - int(sway), cy + 17),
            (cx - 12 - int(sway), cy + 12),
        ])

        # Highlight.
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 8 + int(sway * 0.7), cy + 10),
            (cx + 5 + int(sway * 0.5), cy + 15),
            (cx - 5 - int(sway * 0.5), cy + 15),
            (cx - 8 - int(sway * 0.7), cy + 10),
        ])

        # Bright edge.
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_light"], [
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
        ])

        # Gold trim at bottom.
        for i, (dx1, dx2, dy) in enumerate([
            (-13, 13, 12), (-11, 11, 16), (-8, 8, 20),
        ]):
            trim_y = cy + dy
            pygame.draw.line(surface, _NS_azureth.PALETTE["gold_dark"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 2)
            pygame.draw.line(surface, _NS_azureth.PALETTE["gold_mid"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 1)

        # Runes/stars on robe (mystic pattern).
        for i, (rx, ry) in enumerate([(-4, 4), (3, 6), (-2, 10), (5, 12)]):
            star_x = cx + rx
            star_y = cy + ry
            pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_light"],
                             (star_x, star_y, 1, 1))
            if (int(phase * 3) + i) % 4 < 2:
                pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_shine"],
                                 (star_x, star_y, 1, 1))

    def _draw_mage_torso(surface, cx, cy, facing, phase):
        """Upper body torso with armor plates."""
        # Torso shape (V-shape, wider at shoulders).
        torso_pts = [
            (cx - 10, cy - 4),  # left shoulder
            (cx - 8, cy + 5),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 8, cy + 5),
            (cx + 10, cy - 4),  # right shoulder
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ]
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_darkest"], torso_pts)

        # Chest armor plate (dark blue).
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_dark"], [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 7, cy + 5),
            (cx - 7, cy + 5),
        ])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_mid"], [
            (cx - 6, cy - 3),
            (cx + 6, cy - 3),
            (cx + 5, cy + 3),
            (cx - 5, cy + 3),
        ])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_light"], [
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])

        # Gold shoulder pauldrons.
        for side in (-1, 1):
            pauldron_x = cx + side * 9
            _NS_azureth._poly(surface, _NS_azureth.PALETTE["gold_darkest"], [
                (pauldron_x - 3, cy - 5),
                (pauldron_x + 3, cy - 5),
                (pauldron_x + 4, cy - 1),
                (pauldron_x + 2, cy + 2),
                (pauldron_x - 2, cy + 2),
                (pauldron_x - 4, cy - 1),
            ])
            _NS_azureth._poly(surface, _NS_azureth.PALETTE["gold_dark"], [
                (pauldron_x - 3, cy - 4),
                (pauldron_x + 3, cy - 4),
                (pauldron_x + 3, cy - 1),
                (pauldron_x - 3, cy - 1),
            ])
            _NS_azureth._poly(surface, _NS_azureth.PALETTE["gold_mid"], [
                (pauldron_x - 2, cy - 3),
                (pauldron_x + 2, cy - 3),
                (pauldron_x + 2, cy - 2),
                (pauldron_x - 2, cy - 2),
            ])
            pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_light"],
                             (pauldron_x - 1, cy - 3, 2, 1))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_shine"],
                             (pauldron_x, cy - 3, 1, 1))

        # Central chest gem (arcane blue).
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_dark"],
                         (cx - 2, cy - 1, 4, 4))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_darkest"],
                         (cx - 1, cy, 3, 3))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_dark"],
                         (cx - 1, cy, 2, 2))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_mid"],
                         (cx, cy, 1, 1))
        # Glow around gem.
        for r in range(4, 0, -1):
            alpha = _NS_azureth._alpha(80 * gem_pulse * (4 - r) / 4)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (cx, cy + 1), r)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Flowing cape behind."""
        sway = math.sin(phase * 0.6) * 3
        cape_pts = [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 12 + int(sway), cy + 8),
            (cx + 15 + int(sway), cy + 16),
            (cx + 10 + int(sway), cy + 22),
            (cx - 10 - int(sway), cy + 22),
            (cx - 15 - int(sway), cy + 16),
            (cx - 12 - int(sway), cy + 8),
        ]
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in cape_pts])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_darkest"], cape_pts)
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["robe_dark"], [
            (cx - 7, cy + 1),
            (cx + 7, cy + 1),
            (cx + 11 + int(sway), cy + 9),
            (cx + 8 + int(sway), cy + 20),
            (cx - 8 - int(sway), cy + 20),
            (cx - 11 - int(sway), cy + 9),
        ])
        # Gold clasp at neck.
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_darkest"],
                         (cx - 3, cy - 1, 6, 2))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_mid"],
                         (cx - 2, cy, 4, 1))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_shine"],
                         (cx - 1, cy, 2, 1))

    def _draw_mage_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms - one holds staff, other is at side."""
        # Arm sway during idle.
        sway = math.sin(phase * 0.7) * 1

        # Staff-holding arm (facing side).
        if action == "attack":
            if attack_progress < 0.35:
                # Pull back.
                staff_arm_angle = -0.3 - (attack_progress / 0.35) * 0.4
            elif attack_progress < 0.55:
                # Thrust.
                t = (attack_progress - 0.35) / 0.20
                staff_arm_angle = -0.7 + t * 1.2
            else:
                # Return.
                t = (attack_progress - 0.55) / 0.45
                staff_arm_angle = 0.5 - t * 0.5
        else:
            staff_arm_angle = math.sin(phase * 0.5) * 0.15

        # Front arm (holding staff).
        shoulder_x = cx + facing * 7
        shoulder_y = cy - 2
        elbow_x = shoulder_x + int(math.cos(staff_arm_angle) * 6) * facing
        elbow_y = shoulder_y + int(math.sin(staff_arm_angle) * 6) + 4
        hand_x = elbow_x + int(math.cos(staff_arm_angle * 0.5) * 5) * facing
        hand_y = elbow_y + int(math.sin(staff_arm_angle * 0.5) * 3) + 3

        # Upper arm.
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 5)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_mid"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand (skin tone).
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["shadow_deep"],
                               (hand_x + 1, hand_y + 1), 3)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["skin_dark"],
                               (hand_x, hand_y), 3)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["skin_mid"],
                               (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_azureth.PALETTE["skin_light"],
                         (hand_x, hand_y - 1, 1, 1))

        # Gold bracer on wrist.
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_dark"],
                         (hand_x - 2, hand_y + 2, 5, 2))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_mid"],
                         (hand_x - 1, hand_y + 2, 3, 1))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_shine"],
                         (hand_x, hand_y + 2, 1, 1))

        # Store hand position for staff.
        _NS_azureth._staff_hand = (hand_x, hand_y)

        # Back arm (at side, simpler).
        back_shoulder_x = cx - facing * 7
        back_shoulder_y = cy - 2
        back_hand_x = back_shoulder_x - facing * 2
        back_hand_y = back_shoulder_y + 10 + int(sway)

        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["shadow_deep"],
                             (back_shoulder_x + 1, back_shoulder_y + 1),
                             (back_hand_x + 1, back_hand_y + 1), 4)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_darkest"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 4)
        _NS_azureth._aaline(surface, _NS_azureth.PALETTE["robe_dark"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 2)

        # Back hand.
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["skin_dark"],
                               (back_hand_x, back_hand_y), 2)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["skin_mid"],
                               (back_hand_x, back_hand_y), 1)

    def _draw_arcane_staff(surface, cx, cy, facing, phase, action, attack_progress):
        """Long staff with glowing arcane orb at top."""
        if not hasattr(_NS_azureth, "_staff_hand"):
            return
        hand_x, hand_y = _NS_azureth._staff_hand

        # Staff angle.
        if action == "attack":
            if attack_progress < 0.35:
                angle = math.pi * -0.35 + (attack_progress / 0.35) * 0.2
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.20
                angle = math.pi * -0.15 - t * 0.5
            else:
                t = (attack_progress - 0.55) / 0.45
                angle = math.pi * -0.65 + t * 0.3
        else:
            angle = math.pi * -0.35 + math.sin(phase * 0.5) * 0.05

        angle *= facing

        # Staff length.
        staff_len = 30
        top_x = hand_x + int(math.cos(angle) * staff_len) * facing
        top_y = hand_y + int(math.sin(angle) * staff_len)
        bot_x = hand_x - int(math.cos(angle) * 8) * facing
        bot_y = hand_y - int(math.sin(angle) * 8)

        # Wooden shaft.
        pygame.draw.line(surface, _NS_azureth.PALETTE["shadow_deep"],
                         (bot_x + 1, bot_y + 1), (top_x + 1, top_y + 1), 4)
        pygame.draw.line(surface, _NS_azureth.PALETTE["staff_dark"],
                         (bot_x, bot_y), (top_x, top_y), 3)
        pygame.draw.line(surface, _NS_azureth.PALETTE["staff_mid"],
                         (bot_x, bot_y), (top_x, top_y), 2)
        pygame.draw.line(surface, _NS_azureth.PALETTE["staff_light"],
                         (bot_x, bot_y - 1), (top_x, top_y - 1), 1)

        # Gold wrapping (mid staff).
        mid_x = (top_x + bot_x) // 2
        mid_y = (top_y + bot_y) // 2
        for offset in (-4, -2, 0, 2, 4):
            perp_x = -math.sin(angle) * facing
            perp_y = math.cos(angle)
            wx1 = mid_x + int(offset * math.cos(angle) * facing) - int(perp_x * 2)
            wy1 = mid_y + int(offset * math.sin(angle)) - int(perp_y * 2)
            wx2 = mid_x + int(offset * math.cos(angle) * facing) + int(perp_x * 2)
            wy2 = mid_y + int(offset * math.sin(angle)) + int(perp_y * 2)
            pygame.draw.line(surface, _NS_azureth.PALETTE["gold_dark"],
                             (wx1, wy1), (wx2, wy2), 1)

        # Gold crown at top holding orb.
        crown_pts = [
            (top_x - 4, top_y + 2),
            (top_x - 3, top_y - 2),
            (top_x, top_y - 4),
            (top_x + 3, top_y - 2),
            (top_x + 4, top_y + 2),
        ]
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["gold_darkest"], crown_pts)
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["gold_dark"], [
            (top_x - 3, top_y + 1),
            (top_x - 2, top_y - 1),
            (top_x + 2, top_y - 1),
            (top_x + 3, top_y + 1),
        ])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["gold_mid"], [
            (top_x - 2, top_y),
            (top_x, top_y - 1),
            (top_x + 2, top_y),
        ])

        # Arcane orb (glowing blue).
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        orb_x = top_x
        orb_y = top_y - 6

        # Outer glow layers.
        for r in range(12, 3, -1):
            alpha = _NS_azureth._alpha(100 * pulse * (12 - r) / 12)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (orb_x, orb_y), r)
        for r in range(8, 1, -1):
            alpha = _NS_azureth._alpha(160 * pulse * (8 - r) / 8)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                   (orb_x, orb_y), r)

        # Orb core.
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_darkest"],
                               (orb_x, orb_y), 5)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_dark"],
                               (orb_x, orb_y), 4)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_mid"],
                               (orb_x, orb_y), 3)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"],
                               (orb_x, orb_y), 2)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_hot"],
                               (orb_x, orb_y), 1)
        pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_shine"],
                         (orb_x, orb_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["white"],
                         (orb_x, orb_y, 1, 1))

        # Sparks around orb.
        for i in range(5):
            spark_angle = phase * 2 + i * math.pi * 2 / 5
            sx = orb_x + int(math.cos(spark_angle) * 7)
            sy = orb_y + int(math.sin(spark_angle) * 7)
            pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_shine"], (sx, sy, 1, 1))

        # Store orb position for projectile launch.
        _NS_azureth._orb_pos = (orb_x, orb_y)

    def _draw_mage_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Bearded mage head with gold crown/wings."""
        # Head shape (oval, slightly angled).
        head_pts = [
            (cx - 6, cy + 2),
            (cx - 7, cy - 2),
            (cx - 5, cy - 6),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 5, cy - 6),
            (cx + 7, cy - 2),
            (cx + 6, cy + 2),
            (cx + 4, cy + 5),
            (cx - 4, cy + 5),
        ]
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["skin_dark"], head_pts)
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["skin_mid"], [
            (cx - 5, cy),
            (cx - 5, cy - 4),
            (cx - 2, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["skin_light"], [
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])
        pygame.draw.rect(surface, _NS_azureth.PALETTE["skin_shine"],
                         (cx - 1, cy - 3, 2, 1))

        # Silver-white hair/beard flowing.
        beard_sway = math.sin(phase * 0.6) * 1
        # Beard (flowing down from chin).
        beard_pts = [
            (cx - 4, cy + 3),
            (cx + 4, cy + 3),
            (cx + 5, cy + 6),
            (cx + 4 + int(beard_sway), cy + 10),
            (cx + int(beard_sway), cy + 12),
            (cx - 4 + int(beard_sway), cy + 10),
            (cx - 5, cy + 6),
        ]
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["hair_dark"], beard_pts)
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["hair_mid"], [
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 4, cy + 7),
            (cx + int(beard_sway), cy + 10),
            (cx - 3, cy + 7),
        ])
        pygame.draw.rect(surface, _NS_azureth.PALETTE["hair_light"],
                         (cx - 1, cy + 5, 2, 3))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["hair_shine"],
                         (cx, cy + 6, 1, 1))

        # Hair behind head (long silver).
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["hair_dark"], [
            (cx - 6, cy - 4),
            (cx - 7, cy - 1),
            (cx - 8, cy + 4),
            (cx - 6, cy + 6),
            (cx - 4, cy + 2),
            (cx - 4, cy - 3),
        ])
        _NS_azureth._poly(surface, _NS_azureth.PALETTE["hair_mid"], [
            (cx - 6, cy - 2),
            (cx - 7, cy + 2),
            (cx - 5, cy + 4),
            (cx - 4, cy),
        ])

        # GOLD CROWN WINGS (small feathered wings on sides of head).
        _NS_azureth._draw_head_wings(surface, cx, cy, facing, phase)

        # EYES (glowing blue).
        _NS_azureth._draw_mage_eyes(surface, cx, cy - 3, facing, phase, action)

        # Small mystic gem on forehead.
        gem_pulse = math.sin(phase * 3) * 0.4 + 0.6
        pygame.draw.rect(surface, _NS_azureth.PALETTE["gold_dark"],
                         (cx - 1, cy - 6, 3, 2))
        pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_dark"],
                         (cx, cy - 6, 1, 1))
        for r in range(3, 0, -1):
            alpha = _NS_azureth._alpha(120 * gem_pulse * (3 - r) / 3)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (cx, cy - 6), r)

    def _draw_head_wings(surface, cx, cy, facing, phase):
        """Gold feathered wings extending from sides of head (crown)."""
        beat = math.sin(phase * 1.5) * 2

        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy - 3

            # Three feathers per side.
            for i, (angle_off, length) in enumerate([
                (0.7, 7), (0.5, 9), (0.3, 6),
            ]):
                angle = math.pi * angle_off * side - math.radians(beat + i * 2)
                tip_x = base_x + int(math.cos(angle) * length) * side
                tip_y = base_y - int(math.sin(angle) * length)

                # Feather body.
                perp = angle + math.pi / 2
                pa_x = base_x + int(math.cos(perp) * 2) * side
                pa_y = base_y + int(math.sin(perp) * 2)
                pb_x = base_x - int(math.cos(perp) * 2) * side
                pb_y = base_y - int(math.sin(perp) * 2)

                _NS_azureth._poly(surface, _NS_azureth.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (pa_x + 1, pa_y + 1),
                    (pb_x + 1, pb_y + 1),
                ])
                _NS_azureth._poly(surface, _NS_azureth.PALETTE["wing_dark"],
                                   [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
                _NS_azureth._poly(surface, _NS_azureth.PALETTE["wing_mid"], [
                    (tip_x, tip_y),
                    (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                    (base_x, base_y),
                ])
                _NS_azureth._poly(surface, _NS_azureth.PALETTE["wing_light"], [
                    (tip_x, tip_y),
                    (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                    (base_x, base_y),
                ])
                pygame.draw.rect(surface, _NS_azureth.PALETTE["wing_shine"],
                                 (tip_x, tip_y, 1, 1))

    def _draw_mage_eyes(surface, cx, cy, facing, phase, action):
        """Glowing bright blue eyes."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            # Socket.
            pygame.draw.rect(surface, _NS_azureth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_azureth._alpha(100 * pulse * (4 - r) / 4)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            # Iris.
            pygame.draw.rect(surface, _NS_azureth.PALETTE["eye_darkest"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["eye_dark"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["eye_mid"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

    # ============================================================
    # ARCANE PROJECTILE (basic attack)
    # ============================================================
    def _draw_arcane_projectile(surface, boss, x, y, progress):
        """Blue arcane bolt projectile fired from staff orb."""
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_azureth._target_position(boss, x, y)

        # Launch from staff orb.
        if hasattr(_NS_azureth, "_orb_pos"):
            start_x, start_y = _NS_azureth._orb_pos
        else:
            start_x = x + facing * 20
            start_y = y - 20

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Comet trail.
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_azureth._alpha(230 - i * 25)

            size = max(1, 7 - i)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                   (px, py), size)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (px, py), max(1, size - 3))

            # Sparks.
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright bolt head.
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_darkest"], (bx, by), 8)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_dark"], (bx, by), 6)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_mid"], (bx, by), 4)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"], (bx, by), 3)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_hot"], (bx, by), 2)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_azureth.PALETTE["white"], (bx, by, 1, 1))

        # Radial glow.
        for r in range(12, 3, -2):
            alpha = _NS_azureth._alpha(80 * (12 - r) / 12)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (bx, by), r)

        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 20)
            alpha = _NS_azureth._alpha(240 * (1 - st))
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                   (tx, ty), max(1, radius - 4), 2)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (tx, ty), max(1, radius - 10), 1)

            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_shine"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        """Small floating shadow (indicates flying)."""
        # Shadow smaller and pulsing (because floating).
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        w = int(70 * pulse)
        h = int(10 * pulse)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (50 - w // 2 - radius, 10 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (5, 10, 30, 140),
                            (50 - w // 2, 10 - h // 2, w, h))
        surface.blit(shadow, (x - 50, y - 10))

    def _draw_arcane_wisps(surface, cx, cy, phase, intense=False):
        """Floating arcane wisps/particles below the mage."""
        strength = 1.5 if intense else 1.0

        # Rising wisps.
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 24 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_azureth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                   (sx, sy), 3)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Small stars sparkling.
        for i in range(6):
            star_t = (phase * 0.4 + i * 0.17) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(star_t * 24)
            alpha = _NS_azureth._alpha(230 * (1 - star_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["star_bright"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_arcane_aura(surface, x, y, phase):
        """Large arcane blue aura background."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_azureth._alpha((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_azureth._aacircle(aura, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                       (100, 80), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_azureth._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_azureth._aacircle(aura, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                       (100, 80), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_azureth._alpha((30 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_azureth._aacircle(aura, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                       (100, 80), radius)
        surface.blit(aura, (x - 100, y - 80))

        # Floating stars.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_azureth.PALETTE["star_dim"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["star_bright"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_azureth.PALETTE["arc_darkest"], 200),
                            (5, 15, 150, 25), 3)
        pygame.draw.ellipse(ring, (*_NS_azureth.PALETTE["arc_dark"], 220),
                            (14, 17, 132, 21), 2)
        pygame.draw.ellipse(ring, (*_NS_azureth.PALETTE["arc_mid"], 230),
                            (25, 19, 110, 17), 1)

        # Runes around ring.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_azureth.PALETTE["arc_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_azureth.PALETTE["arc_hot"],
                                        _NS_azureth._alpha(150 * pulse)),
                                (15, 10, 130, 35), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q: ARCANE BOLT (enhanced ranged bolt)
    # ============================================================
    def _draw_arcanebolt_skill(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_azureth._target_position(boss, x, y)

        if progress < 0.25:
            # Charge at orb.
            t = progress / 0.25
            if hasattr(_NS_azureth, "_orb_pos"):
                start_x, start_y = _NS_azureth._orb_pos
            else:
                start_x = x + facing * 20
                start_y = y - 20
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_azureth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                       (start_x, start_y), r)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_mid"],
                                   (start_x, start_y), cr - 2)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"],
                                   (start_x, start_y), max(1, cr - 4))
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_shine"],
                                   (start_x, start_y), max(1, cr - 6))

            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = start_x + int(math.cos(angle) * (cr + 3))
                sy = start_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            if hasattr(_NS_azureth, "_orb_pos"):
                start_x, start_y = _NS_azureth._orb_pos
            else:
                start_x = x + facing * 20
                start_y = y - 20
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Extra bright comet trail.
            for i in range(11):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_azureth._alpha(240 - i * 22)

                size = max(1, 9 - i)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                       (px, py), size)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                       (px, py), max(1, size - 3))

                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Huge bright head.
            for r in range(15, 3, -2):
                alpha = _NS_azureth._alpha(100 * (15 - r) / 15)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                       (bx, by), r)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_darkest"], (bx, by), 10)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_dark"], (bx, by), 8)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_mid"], (bx, by), 5)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"], (bx, by), 3)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_azureth.PALETTE["white"], (bx, by, 1, 1))

            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 30)
                alpha = _NS_azureth._alpha(240 * (1 - st))
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                       (tx, ty), radius + 4, 3)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 2)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                       (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: CONCUSSIVE SHOT (large orb with AoE slow)
    # ============================================================
    def _draw_concussive_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_azureth._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # AoE ring at target after arrival.
        if progress > 0.5:
            t = (progress - 0.5) / 0.5
            r = int(15 + t * 30)
            alpha = _NS_azureth._alpha(200 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_concussive_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_azureth._target_position(boss, x, y)

        if hasattr(_NS_azureth, "_orb_pos"):
            start_x, start_y = _NS_azureth._orb_pos
        else:
            start_x = x + facing * 20
            start_y = y - 20

        if progress < 0.5:
            # Traveling large orb.
            t = progress / 0.5
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # BIG orb (concussive - bigger than Q).
            for r in range(18, 3, -1):
                alpha = _NS_azureth._alpha(120 * (18 - r) / 18)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                       (bx, by), r)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_darkest"], (bx, by), 12)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_dark"], (bx, by), 10)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_mid"], (bx, by), 7)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"], (bx, by), 4)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_shine"], (bx, by), 2)

            # Long spiraling trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                spiral_angle = phase * 5 + i * 0.5
                spiral_r = 4 + i
                px += int(math.cos(spiral_angle) * spiral_r)
                py += int(math.sin(spiral_angle) * spiral_r)
                alpha = _NS_azureth._alpha(200 - i * 15)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                       (px, py), max(1, 5 - i // 3))
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                 (px, py, 1, 1))
        else:
            # Impact explosion.
            t = (progress - 0.5) / 0.5
            radius = int(20 + t * 35)
            alpha = _NS_azureth._alpha(240 * (1 - t))

            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                   (tx, ty), radius + 4, 3)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                   (tx, ty), max(1, radius - 6), 2)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                   (tx, ty), max(1, radius - 15), 1)

            # Radial shockwave lines.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.line(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL E: ANCIENT SEAL (silence seal on target)
    # ============================================================
    def _draw_ancientseal_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_azureth._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ring at target's feet.
        r = int(20 + math.sin(phase * 2) * 3)
        alpha = _NS_azureth._alpha(180)
        pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)

    def _draw_ancientseal_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_azureth._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Sigil/seal above target (rotating rune circle).
        seal_y = ty - 20
        rot = phase * 1.5

        # Outer rotating rune ring.
        r_outer = 15
        for i in range(8):
            angle = rot + i * math.pi / 4
            rune_x = tx + int(math.cos(angle) * r_outer)
            rune_y = seal_y + int(math.sin(angle) * r_outer * 0.6)
            # Star/cross shape.
            pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_dark"],
                             (rune_x - 1, rune_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_light"],
                             (rune_x, rune_y, 1, 1))
            pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_shine"],
                             (rune_x, rune_y, 1, 1))

        # Inner circle.
        for r in range(10, 6, -1):
            alpha = _NS_azureth._alpha(80 * (10 - r) / 4)
            _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                   (tx, seal_y), r)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_darkest"],
                               (tx, seal_y), 6, 1)
        _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"],
                               (tx, seal_y), 4, 1)

        # Central seal symbol.
        pygame.draw.line(surface, _NS_azureth.PALETTE["arc_hot"],
                         (tx - 3, seal_y), (tx + 3, seal_y), 1)
        pygame.draw.line(surface, _NS_azureth.PALETTE["arc_hot"],
                         (tx, seal_y - 3), (tx, seal_y + 3), 1)
        pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_shine"],
                         (tx, seal_y, 1, 1))

        # Chains from seal to boss orb (connection).
        if hasattr(_NS_azureth, "_orb_pos"):
            orb_x, orb_y = _NS_azureth._orb_pos
            for i in range(6):
                t = i / 6
                # Wavy line.
                lx = int(orb_x + (tx - orb_x) * t)
                ly = int(orb_y + (seal_y - orb_y) * t)
                lx += int(math.sin(phase * 3 + i) * 3)
                alpha = _NS_azureth._alpha(180)
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                 (lx, ly, 1, 1))
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_shine"], alpha),
                                 (lx, ly, 1, 1))

        # Sparkles falling from seal onto target.
        for i in range(5):
            spark_t = (phase * 0.8 + i * 0.2) % 1.0
            sx = tx + int(math.sin(phase + i * 2) * 6)
            sy = seal_y + int(spark_t * 20)
            alpha = _NS_azureth._alpha(220 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_azureth.PALETTE["arc_shine"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL R: MYSTIC FLARE (massive AoE storm)
    # ============================================================
    def _draw_mysticflare_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_azureth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Warning circle growing.
            t = progress / 0.3
            r = int(40 * t)
            alpha = _NS_azureth._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_light"], (sx, sy, 2, 2))
        else:
            # Active storm zone.
            t = (progress - 0.3) / 0.7
            r = 45
            alpha = _NS_azureth._alpha(160)
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))

    def _draw_mysticflare_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_azureth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up: energy gathering in sky.
            t = progress / 0.3
            gather_y = ty - int((1 - t) * 80)
            gather_r = int(4 + t * 6)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_azureth._alpha(180 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_dark"], alpha),
                                       (tx, gather_y), r)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_light"],
                                   (tx, gather_y), gather_r - 2)
            pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_shine"],
                             (tx, gather_y, 1, 1))
        else:
            # Vortex storm.
            t = (progress - 0.3) / 0.7
            r = 45
            intensity = math.sin(t * math.pi) * 0.5 + 0.5

            # Spinning vortex layers.
            for layer in range(4):
                rot = phase * (2 + layer) + layer * math.pi / 2
                layer_r = r - layer * 8
                for i in range(20):
                    angle = rot + i * math.pi / 10
                    px = tx + int(math.cos(angle) * layer_r)
                    py = ty + int(math.sin(angle) * layer_r * 0.5)
                    alpha = _NS_azureth._alpha(200 * intensity)
                    color = [_NS_azureth.PALETTE["arc_dark"],
                             _NS_azureth.PALETTE["arc_mid"],
                             _NS_azureth.PALETTE["arc_light"],
                             _NS_azureth.PALETTE["arc_hot"]][layer]
                    pygame.draw.rect(surface, (*color, alpha),
                                     (px, py, 2, 2))

            # Central bright core.
            for r_c in range(12, 2, -1):
                alpha = _NS_azureth._alpha(120 * intensity * (12 - r_c) / 12)
                _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                       (tx, ty), r_c)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["arc_shine"], (tx, ty), 4)
            _NS_azureth._aacircle(surface, _NS_azureth.PALETTE["white"], (tx, ty), 2)

            # Descending bolts from sky.
            for i in range(6):
                bolt_t = (phase * 0.8 + i * 0.15) % 1.0
                bolt_x = tx + int(math.sin(phase * 2 + i) * 20)
                bolt_start_y = ty - 80
                bolt_end_y = ty - int((1 - bolt_t) * 80)
                alpha = _NS_azureth._alpha(220 * intensity)

                # Bolt line.
                pygame.draw.line(surface, (*_NS_azureth.PALETTE["arc_light"], alpha),
                                 (bolt_x, bolt_start_y), (bolt_x, bolt_end_y), 2)
                pygame.draw.line(surface, (*_NS_azureth.PALETTE["arc_shine"], alpha),
                                 (bolt_x, bolt_start_y), (bolt_x, bolt_end_y), 1)

                # Impact when reaching ground.
                if bolt_t > 0.85:
                    ir = int((bolt_t - 0.85) * 40)
                    _NS_azureth._aacircle(surface, (*_NS_azureth.PALETTE["arc_hot"], alpha),
                                           (bolt_x, ty), ir, 1)

            # Ambient sparkles in vortex.
            for i in range(15):
                spark_angle = phase * 3 + i * math.pi / 7
                spark_r = int((phase * 20 + i * 5) % r)
                sx = tx + int(math.cos(spark_angle) * spark_r)
                sy = ty + int(math.sin(spark_angle) * spark_r * 0.5)
                pygame.draw.rect(surface, _NS_azureth.PALETTE["arc_shine"], (sx, sy, 1, 1))


# ====================================================================
# luminar.py
# ====================================================================



class _NS_luminar:
    """Namespace luminar - Eternal Custodian mini boss (RANGED, mounted)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe (blue-white wizard)
        "robe_darkest": (15, 20, 45),
        "robe_dark": (40, 55, 100),
        "robe_mid": (85, 110, 175),
        "robe_light": (160, 185, 235),
        "robe_edge": (215, 230, 255),
        "robe_shine": (245, 250, 255),

        # Light energy (holy yellow-gold)
        "light_darkest": (60, 35, 5),
        "light_dark": (150, 100, 20),
        "light_mid": (240, 180, 50),
        "light_bright": (255, 225, 120),
        "light_hot": (255, 245, 180),
        "light_shine": (255, 255, 240),

        # Horse (white/cream)
        "horse_dark": (100, 90, 80),
        "horse_mid": (180, 170, 155),
        "horse_light": (240, 230, 215),
        "horse_shine": (255, 250, 240),

        # Horse mane/tail (silvery)
        "mane_dark": (130, 130, 145),
        "mane_mid": (200, 200, 215),
        "mane_light": (245, 245, 255),

        # Saddle/tack (brown leather with gold)
        "saddle_dark": (50, 30, 15),
        "saddle_mid": (110, 70, 35),
        "saddle_light": (170, 120, 60),

        # Gold ornaments
        "gold_dark": (100, 70, 20),
        "gold_mid": (200, 155, 50),
        "gold_light": (250, 220, 110),
        "gold_shine": (255, 245, 190),

        # Skin (old man)
        "skin_dark": (110, 90, 80),
        "skin_mid": (180, 155, 140),
        "skin_light": (225, 205, 190),
        "skin_shine": (245, 230, 220),

        # Hair/beard (white)
        "hair_dark": (150, 155, 165),
        "hair_mid": (210, 215, 225),
        "hair_light": (245, 248, 255),
        "hair_shine": (255, 255, 255),

        # Eye (bright light)
        "eye_socket": (10, 15, 30),
        "eye_dark": (70, 90, 150),
        "eye_mid": (180, 220, 255),
        "eye_glow": (255, 255, 255),

        # Staff wood
        "staff_dark": (50, 35, 20),
        "staff_mid": (100, 75, 45),
        "staff_light": (160, 125, 80),

        # Aura background
        "aura_dim": (80, 65, 30),
        "aura_bright": (240, 210, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_luminar._clamp(color)
        if _NS_luminar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_luminar._clamp(color)
        if _NS_luminar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        # Guard: need >= 3 points and non-degenerate.
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_luminar._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_luminar._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 250 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_luminar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_luminar._update_lum_attack_anim(boss)
        attacking = (
            getattr(boss, "_lum_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        spirit_form = active_skill == "r"

        # Ambient behind.
        _NS_luminar._draw_light_aura(surface, x, y, pulse, spirit_form)
        _NS_luminar._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_luminar._draw_wisp_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_luminar._draw_blindinglight_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating/mounted).
        if attacking:
            _NS_luminar._draw_lum_attack(surface, boss, x, y, spirit_form)
        else:
            _NS_luminar._draw_lum_idle(surface, boss, x, y, spirit_form)

        # Foreground FX.
        if active_skill == "q":
            _NS_luminar._draw_illuminate_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_luminar._draw_blindinglight_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_luminar._draw_wisp_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_luminar._draw_spiritform_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_lum_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_lum_previous_timer", 0))
        active = bool(getattr(boss, "_lum_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._lum_attack_active = True
            boss._lum_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._lum_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._lum_attack_frame = int(
                getattr(boss, "_lum_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._lum_attack_active = False
            boss._lum_attack_frame = 0
            active = False

        boss._lum_previous_timer = timer
        boss._lum_attack_progress = (
            min(1.0, getattr(boss, "_lum_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_lum_idle(surface, boss, x, y, spirit_form):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_luminar._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_luminar._draw_light_wisps(surface, x, y + 42, boss.pulse)
        _NS_luminar._draw_lum_body(surface, x, y + bob, boss.direction,
                                    boss.pulse, "idle", spirit_form=spirit_form)

    def _draw_lum_attack(surface, boss, x, y, spirit_form):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_lum_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_lum_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.7) * 5)
        # Wizard casts light spell (staff lifted then pointed forward).
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 3)
            lean = int(t * -1) * facing
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            lift = int(3 - t * 5)
            lean = int((-1 + t * 3)) * facing
        else:
            t = (progress - 0.55) / 0.45
            lift = int(-2 + t * 2)
            lean = int(2 * (1 - t)) * facing

        _NS_luminar._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_luminar._draw_light_wisps(surface, x + lean, y + 42, boss.pulse, intense=True)
        _NS_luminar._draw_lum_body(surface, x + lean, y + bob - lift,
                                    facing, boss.pulse, "attack",
                                    progress, spirit_form=spirit_form)
        _NS_luminar._draw_light_projectile(surface, boss, x + lean,
                                            y + bob - lift, progress)

    # ============================================================
    # BODY (wizard on horse)
    # ============================================================
    def _draw_lum_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0, spirit_form=False):
        # Draw horse first (base).
        _NS_luminar._draw_horse(surface, cx, cy + 8, facing, phase, spirit_form)

        # Saddle blanket.
        _NS_luminar._draw_saddle(surface, cx, cy + 2, facing, phase, spirit_form)

        # Wizard rider on top.
        _NS_luminar._draw_rider(surface, cx, cy - 10, facing, phase, action,
                                 attack_progress, spirit_form)

    def _draw_horse(surface, cx, cy, facing, phase, spirit_form):
        """White horse body (side profile, standing/floating)."""
        # Alpha for spirit form.
        base_alpha = 180 if spirit_form else 255
        # Ghostly tint.
        horse_dark = _NS_luminar.PALETTE["horse_dark"]
        horse_mid = _NS_luminar.PALETTE["horse_mid"]
        horse_light = _NS_luminar.PALETTE["horse_light"]
        horse_shine = _NS_luminar.PALETTE["horse_shine"]
        if spirit_form:
            horse_dark = (150, 180, 210)
            horse_mid = (200, 220, 240)
            horse_light = (230, 240, 255)
            horse_shine = (250, 253, 255)

        # Body (oval, side view).
        body_pts = [
            (cx - 18, cy),
            (cx - 20, cy - 4),
            (cx - 16, cy - 9),
            (cx - 8, cy - 11),
            (cx + 6, cy - 11),
            (cx + 14, cy - 9),
            (cx + 18, cy - 5),
            (cx + 20, cy),
            (cx + 18, cy + 5),
            (cx + 12, cy + 8),
            (cx + 4, cy + 9),
            (cx - 6, cy + 9),
            (cx - 14, cy + 8),
            (cx - 18, cy + 5),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in body_pts])
        _NS_luminar._poly(surface, horse_dark, body_pts)

        # Body highlight (upper).
        _NS_luminar._poly(surface, horse_mid, [
            (cx - 16, cy - 2),
            (cx - 14, cy - 8),
            (cx - 6, cy - 10),
            (cx + 4, cy - 10),
            (cx + 12, cy - 8),
            (cx + 17, cy - 4),
            (cx + 15, cy),
            (cx - 14, cy),
        ])
        _NS_luminar._poly(surface, horse_light, [
            (cx - 12, cy - 4),
            (cx - 8, cy - 8),
            (cx + 2, cy - 9),
            (cx + 10, cy - 6),
            (cx + 12, cy - 3),
            (cx - 8, cy - 3),
        ])
        # Bright shine.
        _NS_luminar._poly(surface, horse_shine, [
            (cx - 4, cy - 7),
            (cx + 2, cy - 8),
            (cx + 6, cy - 6),
            (cx + 2, cy - 5),
            (cx - 3, cy - 5),
        ])

        # LEGS (4 legs, front/back pairs).
        _NS_luminar._draw_horse_legs(surface, cx, cy, facing, phase, spirit_form,
                                      horse_dark, horse_mid, horse_light)

        # HEAD/NECK (curving forward).
        _NS_luminar._draw_horse_head(surface, cx, cy, facing, phase, spirit_form,
                                      horse_dark, horse_mid, horse_light, horse_shine)

        # TAIL (flowing back).
        _NS_luminar._draw_horse_tail(surface, cx, cy, facing, phase, spirit_form)

    def _draw_horse_legs(surface, cx, cy, facing, phase, spirit_form,
                          h_dark, h_mid, h_light):
        """4 horse legs (2 front, 2 back)."""
        # Slight leg animation (like trotting/hovering).
        leg_wave = math.sin(phase * 1.5) * 1

        # Positions of 4 legs (front pair + back pair).
        # In side view: front leg pair (near + far), back leg pair.
        legs = [
            (cx - 12, "back_far", -1),  # back far
            (cx - 10, "back_near", 1),  # back near
            (cx + 10, "front_far", -1), # front far
            (cx + 12, "front_near", 1), # front near
        ]

        for leg_x, name, phase_off in legs:
            offset = int(leg_wave * phase_off)
            top_y = cy + 6
            knee_y = cy + 14 + offset
            hoof_y = cy + 22 + offset

            # Shadow.
            _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                                 (leg_x + 1, top_y + 1),
                                 (leg_x + 1, knee_y + 1), 4)
            _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                                 (leg_x + 1, knee_y + 1),
                                 (leg_x + 1, hoof_y + 1), 3)

            # Upper leg.
            _NS_luminar._aaline(surface, h_dark,
                                 (leg_x, top_y), (leg_x, knee_y), 4)
            _NS_luminar._aaline(surface, h_mid,
                                 (leg_x, top_y), (leg_x, knee_y), 2)
            # Lower leg.
            _NS_luminar._aaline(surface, h_dark,
                                 (leg_x, knee_y), (leg_x, hoof_y), 3)
            _NS_luminar._aaline(surface, h_mid,
                                 (leg_x, knee_y), (leg_x, hoof_y), 1)

            # Hoof (dark).
            pygame.draw.rect(surface, _NS_luminar.PALETTE["shadow_deep"],
                             (leg_x - 2, hoof_y - 1, 4, 3))
            pygame.draw.rect(surface, _NS_luminar.PALETTE["saddle_dark"],
                             (leg_x - 2, hoof_y, 4, 2))
            pygame.draw.rect(surface, _NS_luminar.PALETTE["saddle_mid"],
                             (leg_x - 1, hoof_y, 2, 1))

    def _draw_horse_head(surface, cx, cy, facing, phase, spirit_form,
                          h_dark, h_mid, h_light, h_shine):
        """Horse head/neck curving forward."""
        # Neck base at front of body.
        neck_base_x = cx + facing * 15
        neck_base_y = cy - 8

        # Neck curves forward and up.
        neck_tip_x = neck_base_x + facing * 8
        neck_tip_y = neck_base_y - 6

        # Draw neck as tapered thick line.
        prev = (neck_base_x, neck_base_y)
        for step in range(1, 5):
            t = step / 4
            nx = int((1 - t) * neck_base_x + t * neck_tip_x)
            ny = int((1 - t) * neck_base_y + t * neck_tip_y)
            thickness = 8 - step
            _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                                 (prev[0] + 1, prev[1] + 1),
                                 (nx + 1, ny + 1), thickness + 1)
            _NS_luminar._aaline(surface, h_dark, prev, (nx, ny), thickness)
            _NS_luminar._aaline(surface, h_mid, prev, (nx, ny), max(1, thickness - 2))
            _NS_luminar._aaline(surface, h_light,
                                 (prev[0], prev[1] - 1), (nx, ny - 1),
                                 max(1, thickness - 4))
            prev = (nx, ny)

        # Head.
        hx = neck_tip_x + facing * 4
        hy = neck_tip_y - 2
        head_pts = [
            (hx - 4 * facing, hy - 3),
            (hx + 2 * facing, hy - 4),
            (hx + 6 * facing, hy - 2),
            (hx + 8 * facing, hy + 1),
            (hx + 7 * facing, hy + 4),
            (hx + 2 * facing, hy + 5),
            (hx - 3 * facing, hy + 4),
            (hx - 4 * facing, hy),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_luminar._poly(surface, h_dark, head_pts)
        _NS_luminar._poly(surface, h_mid, [
            (hx - 3 * facing, hy - 2),
            (hx + 2 * facing, hy - 3),
            (hx + 5 * facing, hy - 1),
            (hx + 7 * facing, hy + 1),
            (hx + 5 * facing, hy + 3),
            (hx - 2 * facing, hy + 3),
        ])
        _NS_luminar._poly(surface, h_light, [
            (hx, hy - 1),
            (hx + 4 * facing, hy),
            (hx + 5 * facing, hy + 2),
            (hx + 2 * facing, hy + 2),
        ])

        # Ear.
        _NS_luminar._poly(surface, h_dark, [
            (hx - 2 * facing, hy - 3),
            (hx - 3 * facing, hy - 6),
            (hx, hy - 3),
        ])
        _NS_luminar._poly(surface, h_mid, [
            (hx - 1 * facing, hy - 3),
            (hx - 2 * facing, hy - 5),
            (hx, hy - 3),
        ])

        # Eye.
        eye_x = hx + 2 * facing
        eye_y = hy
        pygame.draw.rect(surface, _NS_luminar.PALETTE["shadow_deep"],
                         (eye_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_luminar.PALETTE["eye_socket"],
                         (eye_x, eye_y, 1, 1))
        if spirit_form:
            pygame.draw.rect(surface, _NS_luminar.PALETTE["eye_glow"],
                             (eye_x, eye_y, 1, 1))

        # Nostril.
        pygame.draw.rect(surface, _NS_luminar.PALETTE["shadow_deep"],
                         (hx + 6 * facing, hy + 2, 1, 1))

        # Mouth line.
        pygame.draw.line(surface, _NS_luminar.PALETTE["shadow_deep"],
                         (hx + 4 * facing, hy + 4),
                         (hx + 7 * facing, hy + 4), 1)

        # MANE flowing along neck.
        _NS_luminar._draw_horse_mane(surface, neck_base_x, neck_base_y,
                                      neck_tip_x, neck_tip_y, facing, phase, spirit_form)

    def _draw_horse_mane(surface, base_x, base_y, tip_x, tip_y, facing, phase, spirit_form):
        """Silvery mane along neck."""
        sway = math.sin(phase * 0.8) * 2

        mane_dark = _NS_luminar.PALETTE["mane_dark"]
        mane_mid = _NS_luminar.PALETTE["mane_mid"]
        mane_light = _NS_luminar.PALETTE["mane_light"]
        if spirit_form:
            mane_dark = (200, 220, 245)
            mane_mid = (230, 240, 255)
            mane_light = (250, 253, 255)

        # Draw mane strands along neck.
        for i in range(5):
            t = i / 4
            mx = int((1 - t) * base_x + t * tip_x)
            my = int((1 - t) * base_y + t * tip_y)
            # Mane hangs down/back.
            strand_len = 5 - i
            strand_x_off = -facing * (2 + int(sway * 0.5))
            strand_y_off = 3 + int(sway * 0.3)

            _NS_luminar._aaline(surface, mane_dark,
                                 (mx, my - 1),
                                 (mx + strand_x_off, my + strand_y_off + strand_len), 2)
            _NS_luminar._aaline(surface, mane_mid,
                                 (mx, my - 1),
                                 (mx + strand_x_off, my + strand_y_off + strand_len - 1), 1)
            pygame.draw.rect(surface, mane_light,
                             (mx + strand_x_off // 2, my + 1, 1, 1))

    def _draw_horse_tail(surface, cx, cy, facing, phase, spirit_form):
        """Long flowing tail at back of horse."""
        sway = math.sin(phase * 0.7) * 3
        base_x = cx - facing * 18
        base_y = cy - 2

        mane_dark = _NS_luminar.PALETTE["mane_dark"]
        mane_mid = _NS_luminar.PALETTE["mane_mid"]
        mane_light = _NS_luminar.PALETTE["mane_light"]
        if spirit_form:
            mane_dark = (200, 220, 245)
            mane_mid = (230, 240, 255)
            mane_light = (250, 253, 255)

        # Tail flows back and down.
        points = [(base_x, base_y)]
        for i in range(1, 6):
            t = i / 5
            tail_x = base_x - facing * int(t * 8)
            tail_y = base_y + int(t * 12) + int(math.sin(phase * 1.2 + t * 3) * 2)
            points.append((tail_x, tail_y))

        for i in range(len(points) - 1):
            thickness = max(2, 6 - i)
            _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                                 (points[i][0] + 1, points[i][1] + 1),
                                 (points[i + 1][0] + 1, points[i + 1][1] + 1),
                                 thickness + 1)
            _NS_luminar._aaline(surface, mane_dark,
                                 points[i], points[i + 1], thickness)
            _NS_luminar._aaline(surface, mane_mid,
                                 points[i], points[i + 1], max(1, thickness - 1))
            _NS_luminar._aaline(surface, mane_light,
                                 (points[i][0], points[i][1] - 1),
                                 (points[i + 1][0], points[i + 1][1] - 1),
                                 max(1, thickness - 3))

    def _draw_saddle(surface, cx, cy, facing, phase, spirit_form):
        """Leather saddle with gold trim."""
        saddle_pts = [
            (cx - 9, cy),
            (cx - 10, cy - 3),
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 10, cy - 3),
            (cx + 9, cy),
            (cx + 6, cy + 3),
            (cx - 6, cy + 3),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in saddle_pts])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["saddle_dark"], saddle_pts)

        # Saddle blanket (blue with gold trim).
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_darkest"], [
            (cx - 8, cy - 1),
            (cx + 8, cy - 1),
            (cx + 9, cy + 2),
            (cx - 9, cy + 2),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_dark"], [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 8, cy + 1),
            (cx - 8, cy + 1),
        ])

        # Gold trim edges.
        pygame.draw.line(surface, _NS_luminar.PALETTE["gold_dark"],
                         (cx - 9, cy + 2), (cx + 9, cy + 2), 1)
        pygame.draw.line(surface, _NS_luminar.PALETTE["gold_light"],
                         (cx - 8, cy + 2), (cx + 8, cy + 2), 1)

        # Front pommel (saddle horn).
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["saddle_dark"], [
            (cx + facing * 7, cy - 4),
            (cx + facing * 9, cy - 6),
            (cx + facing * 11, cy - 4),
            (cx + facing * 9, cy - 2),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["saddle_mid"], [
            (cx + facing * 8, cy - 5),
            (cx + facing * 10, cy - 4),
            (cx + facing * 9, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_luminar.PALETTE["gold_mid"],
                         (cx + facing * 9, cy - 4, 1, 1))

    def _draw_rider(surface, cx, cy, facing, phase, action, attack_progress, spirit_form):
        """Wizard rider - torso up (sitting on horse)."""
        # Robe/lower body (visible above saddle).
        _NS_luminar._draw_rider_robe(surface, cx, cy + 8, facing, phase, spirit_form)

        # Torso.
        _NS_luminar._draw_rider_torso(surface, cx, cy + 2, facing, phase, spirit_form)

        # Non-staff arm (reins hand).
        _NS_luminar._draw_reins_arm(surface, cx, cy + 2, facing, phase, spirit_form)

        # Head.
        _NS_luminar._draw_wizard_head(surface, cx, cy - 8, facing, phase, spirit_form)

        # Staff arm.
        _NS_luminar._draw_staff_arm(surface, cx, cy + 2, facing, phase, action,
                                     attack_progress, spirit_form)

    def _draw_rider_robe(surface, cx, cy, facing, phase, spirit_form):
        """Bottom of wizard robe visible above saddle."""
        sway = math.sin(phase * 0.6) * 1
        robe_pts = [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 10 + int(sway), cy + 2),
            (cx + 8 + int(sway), cy + 5),
            (cx - 8 - int(sway), cy + 5),
            (cx - 10 - int(sway), cy + 2),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in robe_pts])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_darkest"], robe_pts)
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 9 + int(sway), cy + 2),
            (cx - 9 - int(sway), cy + 2),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 6, cy + 1),
            (cx - 6, cy + 1),
        ])

        # Gold trim.
        pygame.draw.line(surface, _NS_luminar.PALETTE["gold_mid"],
                         (cx - 9 - int(sway), cy + 4),
                         (cx + 9 + int(sway), cy + 4), 1)

    def _draw_rider_torso(surface, cx, cy, facing, phase, spirit_form):
        """Upper body torso with robe."""
        torso_pts = [
            (cx - 8, cy - 3),
            (cx - 7, cy + 5),
            (cx + 7, cy + 5),
            (cx + 8, cy - 3),
            (cx + 7, cy - 5),
            (cx - 7, cy - 5),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in torso_pts])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_darkest"], torso_pts)
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])

        # Central chest emblem (light gem).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_y = cy + 1
        pygame.draw.rect(surface, _NS_luminar.PALETTE["gold_dark"],
                         (cx - 2, gem_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_luminar.PALETTE["light_dark"],
                         (cx - 1, gem_y, 3, 2))
        pygame.draw.rect(surface, _NS_luminar.PALETTE["light_bright"],
                         (cx, gem_y, 1, 1))
        # Glow around gem.
        for r in range(4, 0, -1):
            alpha = _NS_luminar._alpha(80 * pulse * (4 - r) / 4)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (cx, gem_y), r)

    def _draw_reins_arm(surface, cx, cy, facing, phase, spirit_form):
        """Arm holding reins (non-staff side)."""
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 3
        hand_x = shoulder_x + facing * 3
        hand_y = shoulder_y + 8 + int(sway)

        # Arm.
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["robe_darkest"],
                             (shoulder_x, shoulder_y), (hand_x, hand_y), 4)
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["robe_dark"],
                             (shoulder_x, shoulder_y), (hand_x, hand_y), 2)

        # Hand (skin).
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)

        # Reins line (going to horse head).
        rein_end_x = hand_x + facing * 20
        rein_end_y = hand_y + 4
        pygame.draw.line(surface, _NS_luminar.PALETTE["saddle_dark"],
                         (hand_x + facing, hand_y), (rein_end_x, rein_end_y), 1)

    def _draw_staff_arm(surface, cx, cy, facing, phase, action, attack_progress, spirit_form):
        """Arm holding staff with orb."""
        # Determine angle.
        if action == "attack":
            if attack_progress < 0.35:
                arm_angle = -0.5 - (attack_progress / 0.35) * 0.3
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.20
                arm_angle = -0.8 + t * 1.0
            else:
                t = (attack_progress - 0.55) / 0.45
                arm_angle = 0.2 - t * 0.7
        else:
            arm_angle = -0.5 + math.sin(phase * 0.5) * 0.1

        shoulder_x = cx + facing * 6
        shoulder_y = cy - 3

        elbow_x = shoulder_x + int(math.cos(arm_angle) * 5) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * 5) + 3
        hand_x = elbow_x + int(math.cos(arm_angle * 0.5) * 5) * facing
        hand_y = elbow_y + int(math.sin(arm_angle * 0.5) * 3) + 2

        # Arm segments.
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 4)
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["robe_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["robe_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)

        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 3)
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["robe_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_luminar._aaline(surface, _NS_luminar.PALETTE["robe_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)

        # Draw staff from hand.
        _NS_luminar._draw_light_staff(surface, hand_x, hand_y, facing, phase,
                                        action, attack_progress)

    def _draw_light_staff(surface, hand_x, hand_y, facing, phase, action, attack_progress):
        """Wooden staff with glowing orb at top."""
        # Staff angle.
        if action == "attack":
            if attack_progress < 0.35:
                angle = -math.pi * 0.4 - (attack_progress / 0.35) * 0.15
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.20
                angle = -math.pi * 0.55 + t * 0.35
            else:
                t = (attack_progress - 0.55) / 0.45
                angle = -math.pi * 0.2 - t * 0.2
        else:
            angle = -math.pi * 0.4 + math.sin(phase * 0.5) * 0.03

        staff_len = 28
        top_x = hand_x + int(math.cos(angle) * staff_len) * facing
        top_y = hand_y + int(math.sin(angle) * staff_len)
        bot_x = hand_x - int(math.cos(angle) * 6) * facing
        bot_y = hand_y - int(math.sin(angle) * 6)

        # Shaft.
        pygame.draw.line(surface, _NS_luminar.PALETTE["shadow_deep"],
                         (bot_x + 1, bot_y + 1), (top_x + 1, top_y + 1), 4)
        pygame.draw.line(surface, _NS_luminar.PALETTE["staff_dark"],
                         (bot_x, bot_y), (top_x, top_y), 3)
        pygame.draw.line(surface, _NS_luminar.PALETTE["staff_mid"],
                         (bot_x, bot_y), (top_x, top_y), 2)
        pygame.draw.line(surface, _NS_luminar.PALETTE["staff_light"],
                         (bot_x, bot_y - 1), (top_x, top_y - 1), 1)

        # Gold wrappings.
        for t_pos in (0.3, 0.6):
            wrap_x = int(bot_x + (top_x - bot_x) * t_pos)
            wrap_y = int(bot_y + (top_y - bot_y) * t_pos)
            perp = angle + math.pi / 2
            wa = (wrap_x + int(math.cos(perp) * 2) * facing,
                  wrap_y + int(math.sin(perp) * 2))
            wb = (wrap_x - int(math.cos(perp) * 2) * facing,
                  wrap_y - int(math.sin(perp) * 2))
            pygame.draw.line(surface, _NS_luminar.PALETTE["gold_mid"], wa, wb, 1)
            pygame.draw.line(surface, _NS_luminar.PALETTE["gold_light"],
                             (wa[0], wa[1] - 1), (wb[0], wb[1] - 1), 1)

        # Gold prongs holding orb at top.
        prong_pts = [
            (top_x - 3, top_y + 2),
            (top_x - 3, top_y - 3),
            (top_x, top_y - 5),
            (top_x + 3, top_y - 3),
            (top_x + 3, top_y + 2),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["gold_dark"], prong_pts)
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["gold_mid"], [
            (top_x - 2, top_y + 1),
            (top_x - 2, top_y - 2),
            (top_x + 2, top_y - 2),
            (top_x + 2, top_y + 1),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["gold_light"], [
            (top_x - 1, top_y),
            (top_x, top_y - 1),
            (top_x + 1, top_y),
        ])

        # Glowing light orb.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        orb_x = top_x
        orb_y = top_y - 7

        # Big outer glow.
        for r in range(14, 3, -1):
            alpha = _NS_luminar._alpha(120 * pulse * (14 - r) / 14)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (orb_x, orb_y), r)
        for r in range(9, 1, -1):
            alpha = _NS_luminar._alpha(180 * pulse * (9 - r) / 9)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_mid"], alpha),
                                    (orb_x, orb_y), r)

        # Orb core.
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_darkest"],
                                (orb_x, orb_y), 5)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_dark"],
                                (orb_x, orb_y), 4)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_mid"],
                                (orb_x, orb_y), 3)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_bright"],
                                (orb_x, orb_y), 2)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_hot"],
                                (orb_x, orb_y), 1)
        pygame.draw.rect(surface, _NS_luminar.PALETTE["white"],
                         (orb_x, orb_y, 1, 1))

        # Radiating light rays.
        for i in range(8):
            ray_angle = phase * 0.5 + i * math.pi / 4
            ray_r = 12
            rx = orb_x + int(math.cos(ray_angle) * ray_r)
            ry = orb_y + int(math.sin(ray_angle) * ray_r)
            alpha = _NS_luminar._alpha(180 * pulse)
            pygame.draw.line(surface, (*_NS_luminar.PALETTE["light_hot"], alpha),
                             (orb_x, orb_y), (rx, ry), 1)

        # Sparks.
        for i in range(5):
            spark_angle = phase * 2 + i * math.pi * 2 / 5
            sx = orb_x + int(math.cos(spark_angle) * 7)
            sy = orb_y + int(math.sin(spark_angle) * 7)
            pygame.draw.rect(surface, _NS_luminar.PALETTE["light_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_luminar.PALETTE["light_shine"], (sx, sy, 1, 1))

        # Store orb position.
        _NS_luminar._orb_pos = (orb_x, orb_y)

    def _draw_wizard_head(surface, cx, cy, facing, phase, spirit_form):
        """Old wizard head with long white beard and hair."""
        # Head.
        head_pts = [
            (cx - 5, cy + 2),
            (cx - 6, cy - 1),
            (cx - 4, cy - 5),
            (cx - 1, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 2),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_pts])

        if spirit_form:
            # Ghostly translucent head.
            skin_d = (200, 220, 245)
            skin_m = (225, 235, 250)
            skin_l = (245, 250, 255)
        else:
            skin_d = _NS_luminar.PALETTE["skin_dark"]
            skin_m = _NS_luminar.PALETTE["skin_mid"]
            skin_l = _NS_luminar.PALETTE["skin_light"]

        _NS_luminar._poly(surface, skin_d, head_pts)
        _NS_luminar._poly(surface, skin_m, [
            (cx - 4, cy - 1),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
            (cx + 4, cy - 4),
            (cx + 4, cy - 1),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_luminar._poly(surface, skin_l, [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_luminar.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # LONG WHITE BEARD (main feature).
        beard_sway = math.sin(phase * 0.6) * 1

        # Beard flows down past neck to chest.
        beard_pts = [
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 5, cy + 6),
            (cx + 6, cy + 10),
            (cx + 4 + int(beard_sway), cy + 14),
            (cx + int(beard_sway), cy + 16),
            (cx - 4 + int(beard_sway), cy + 14),
            (cx - 6, cy + 10),
            (cx - 5, cy + 6),
        ]
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["hair_dark"], beard_pts)
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["hair_mid"], [
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
            (cx + 4, cy + 8),
            (cx + int(beard_sway), cy + 14),
            (cx - 4 + int(beard_sway), cy + 12),
            (cx - 4, cy + 8),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["hair_light"], [
            (cx - 1, cy + 5),
            (cx + 1, cy + 5),
            (cx + 2, cy + 10),
            (cx + int(beard_sway), cy + 13),
            (cx - 1 + int(beard_sway), cy + 12),
            (cx - 2, cy + 10),
        ])
        pygame.draw.rect(surface, _NS_luminar.PALETTE["hair_shine"],
                         (cx, cy + 7, 1, 3))

        # Mustache.
        pygame.draw.rect(surface, _NS_luminar.PALETTE["hair_mid"],
                         (cx - 3, cy + 1, 6, 1))
        pygame.draw.rect(surface, _NS_luminar.PALETTE["hair_light"],
                         (cx - 2, cy + 1, 4, 1))

        # Long white hair behind head.
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["hair_dark"], [
            (cx - 5, cy - 4),
            (cx - 7, cy - 1),
            (cx - 8, cy + 4),
            (cx - 9, cy + 8),
            (cx - 6, cy + 10),
            (cx - 4, cy + 5),
            (cx - 4, cy),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["hair_mid"], [
            (cx - 5, cy - 2),
            (cx - 7, cy + 2),
            (cx - 7, cy + 7),
            (cx - 5, cy + 8),
            (cx - 4, cy + 3),
        ])
        _NS_luminar._poly(surface, _NS_luminar.PALETTE["hair_light"], [
            (cx - 5, cy),
            (cx - 6, cy + 5),
            (cx - 5, cy + 6),
            (cx - 4, cy + 2),
        ])

        # Wizard EYES (bright and wise).
        _NS_luminar._draw_wizard_eyes(surface, cx, cy - 3, facing, phase, spirit_form)

        # Halo above head in spirit form.
        if spirit_form:
            halo_pulse = math.sin(phase * 2) * 0.3 + 0.7
            for r in range(8, 3, -1):
                alpha = _NS_luminar._alpha(120 * halo_pulse * (8 - r) / 8)
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_hot"], alpha),
                                        (cx, cy - 10), r)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_hot"],
                                    (cx, cy - 10), 5, 1)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_shine"],
                                    (cx, cy - 10), 4, 1)

    def _draw_wizard_eyes(surface, cx, cy, facing, phase, spirit_form):
        """Wise glowing eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_luminar.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))

            if spirit_form:
                # Fully glowing white eyes.
                for r in range(3, 0, -1):
                    alpha = _NS_luminar._alpha(200 * pulse * (3 - r) / 3)
                    _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                                            (ex, ey), r)
                pygame.draw.rect(surface, _NS_luminar.PALETTE["white"], (ex, ey, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_luminar.PALETTE["eye_dark"],
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, _NS_luminar.PALETTE["eye_mid"],
                                 (ex, ey, 1, 1))
                # Small glow.
                alpha = _NS_luminar._alpha(120 * pulse)
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                        (ex, ey), 2)

    # ============================================================
    # LIGHT PROJECTILE (basic attack)
    # ============================================================
    def _draw_light_projectile(surface, boss, x, y, progress):
        """Light beam projectile from staff orb."""
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_luminar._target_position(boss, x, y)

        if hasattr(_NS_luminar, "_orb_pos"):
            start_x, start_y = _NS_luminar._orb_pos
        else:
            start_x = x + facing * 20
            start_y = y - 20

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Bright light comet trail.
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_luminar._alpha(230 - i * 22)

            size = max(1, 8 - i)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_darkest"], alpha),
                                    (px, py), size)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (px, py), max(1, size - 3))

            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_luminar.PALETTE["light_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright head.
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_darkest"], (bx, by), 8)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_dark"], (bx, by), 6)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_mid"], (bx, by), 4)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_bright"], (bx, by), 3)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_hot"], (bx, by), 2)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_luminar.PALETTE["white"], (bx, by, 1, 1))

        # Radial glow.
        for r in range(14, 3, -2):
            alpha = _NS_luminar._alpha(90 * (14 - r) / 14)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (bx, by), r)

        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_luminar._alpha(240 * (1 - st))
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_mid"], alpha),
                                    (tx, ty), radius, 2)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (tx, ty), max(1, radius - 6), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((140, 25), pygame.SRCALPHA)
        w = int(100 * pulse)
        h = int(12 * pulse)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (70 - w // 2 - radius, 12 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (10, 15, 30, 150),
                            (70 - w // 2, 12 - h // 2, w, h))
        surface.blit(shadow, (x - 70, y - 12))

    def _draw_light_wisps(surface, cx, cy, phase, intense=False):
        """Golden light particles floating around."""
        strength = 1.5 if intense else 1.0

        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 30 + i * 8 + int(math.sin(phase + i) * 3)
            sy = cy + 15 - int(t * 30)
            alpha = _NS_luminar._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_dark"], alpha),
                                    (sx, sy), 3)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright stars.
        for i in range(6):
            star_t = (phase * 0.4 + i * 0.17) % 1.0
            ex = cx - 25 + i * 10 + int(math.sin(phase + i) * 4)
            ey = cy + 12 - int(star_t * 24)
            alpha = _NS_luminar._alpha(230 * (1 - star_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_light_aura(surface, x, y, phase, spirit_form):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)

        # Outer aura.
        for radius in range(90, 5, -5):
            alpha = _NS_luminar._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_luminar._aacircle(aura, (*_NS_luminar.PALETTE["aura_dim"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_luminar._alpha((60 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_luminar._aacircle(aura, (*_NS_luminar.PALETTE["light_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_luminar._alpha((35 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_luminar._aacircle(aura, (*_NS_luminar.PALETTE["light_mid"], alpha),
                                        (110, 90), radius)

        # Spirit form extra bright.
        if spirit_form:
            for radius in range(45, 5, -3):
                alpha = _NS_luminar._alpha((45 - radius) * 1.5 * pulse)
                if alpha > 0:
                    _NS_luminar._aacircle(aura, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                            (110, 90), radius)

        surface.blit(aura, (x - 110, y - 90))

        # Orbiting stars.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_luminar.PALETTE["light_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_luminar.PALETTE["light_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_luminar.PALETTE["light_darkest"], 200),
                            (5, 18, 170, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_luminar.PALETTE["light_dark"], 220),
                            (14, 20, 152, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_luminar.PALETTE["light_mid"], 230),
                            (25, 22, 130, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 47)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_luminar.PALETTE["light_bright"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_luminar.PALETTE["light_hot"],
                                        _NS_luminar._alpha(150 * pulse)),
                                (15, 12, 150, 38), 1)
        surface.blit(ring, (x - 90, y - 27))

    # ============================================================
    # SKILL Q: ILLUMINATE (line-piercing light beam)
    # ============================================================
    def _draw_illuminate_skill(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_luminar._target_position(boss, x, y)

        if hasattr(_NS_luminar, "_orb_pos"):
            start_x, start_y = _NS_luminar._orb_pos
        else:
            start_x = x + facing * 20
            start_y = y - 20

        if progress < 0.35:
            # Charge at orb (BIG bright ball forming).
            t = progress / 0.35
            cr = int(4 + t * 14)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_luminar._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_bright"],
                                    (start_x, start_y), max(1, cr - 4))
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_hot"],
                                    (start_x, start_y), max(1, cr - 6))
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_shine"],
                                    (start_x, start_y), max(1, cr - 8))
            pygame.draw.rect(surface, _NS_luminar.PALETTE["white"],
                             (start_x, start_y, 1, 1))

            # Charging sparks.
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = start_x + int(math.cos(angle) * (cr + 4))
                sy = start_y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_luminar.PALETTE["light_hot"], (sx, sy, 1, 1))
        elif progress < 0.85:
            # BEAM PHASE - massive light beam piercing through.
            t = (progress - 0.35) / 0.5
            intensity = math.sin(t * math.pi)

            # Direction to target (extended to end of screen).
            dx = tx - start_x
            dy = ty - start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx = dx / length
                ny = dy / length
                # Extend beam past target.
                end_x = int(start_x + nx * (length + 100))
                end_y = int(start_y + ny * (length + 100))
            else:
                end_x = tx + facing * 200
                end_y = ty

            # Multi-layered beam (thick with bright core).
            for layer_i, (width, alpha_val) in enumerate([
                (18, 80), (14, 120), (10, 160), (6, 200), (3, 240), (1, 255),
            ]):
                actual_alpha = _NS_luminar._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_luminar.PALETTE["light_darkest"],
                    _NS_luminar.PALETTE["light_dark"],
                    _NS_luminar.PALETTE["light_mid"],
                    _NS_luminar.PALETTE["light_bright"],
                    _NS_luminar.PALETTE["light_hot"],
                    _NS_luminar.PALETTE["white"],
                ]
                color = colors[min(layer_i, 5)]

                # Draw thick line as beam.
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (end_x, end_y), width)

            # Sparks along beam.
            for i in range(20):
                spark_t = (phase * 3 + i * 0.1) % 1.0
                spark_x = int(start_x + (end_x - start_x) * spark_t)
                spark_y = int(start_y + (end_y - start_y) * spark_t)
                # Perpendicular offset.
                perp_x = -ny * math.sin(phase * 5 + i) * 6
                perp_y = nx * math.sin(phase * 5 + i) * 6
                spark_x += int(perp_x)
                spark_y += int(perp_y)
                alpha = _NS_luminar._alpha(240 * intensity)
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_hot"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["white"], alpha),
                                 (spark_x, spark_y, 1, 1))

            # Bright bulb at start.
            for r in range(12, 2, -1):
                alpha = _NS_luminar._alpha(200 * intensity * (12 - r) / 12)
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                        (start_x, start_y), r)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_shine"],
                                    (start_x, start_y), 4)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["white"],
                                    (start_x, start_y), 2)

            # Impact explosion at target.
            impact_r = int(15 + t * 25)
            impact_alpha = _NS_luminar._alpha(240 * intensity)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_darkest"], impact_alpha),
                                    (tx, ty), impact_r + 4, 3)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_dark"], impact_alpha),
                                    (tx, ty), impact_r, 3)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_mid"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 6), 2)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_hot"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 12), 1)

            # Radial burst at impact.
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_luminar.PALETTE["light_hot"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], impact_alpha),
                                 (ex, ey, 2, 2))
        else:
            # Fade / aftermath.
            t = (progress - 0.85) / 0.15
            for i in range(8):
                rise_t = (phase * 0.6 + i * 0.13) % 1.0
                rx = tx + int(math.sin(phase + i) * 15)
                ry = ty - int(rise_t * 25)
                alpha = _NS_luminar._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                                     (rx, ry, 1, 1))

    # ============================================================
    # SKILL W: BLINDING LIGHT (AoE flash push)
    # ============================================================
    def _draw_blindinglight_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        center_x = x + facing * 40
        center_y = y + 25

        # Expanding light circle on ground.
        if progress > 0.2:
            t = (progress - 0.2) / 0.8
            r = int(15 + t * 45)
            alpha = _NS_luminar._alpha(200 * (1 - t))
            pygame.draw.ellipse(surface, (*_NS_luminar.PALETTE["light_darkest"], alpha),
                                (center_x - r, center_y - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_luminar.PALETTE["light_mid"], alpha),
                                (center_x - r + 3, center_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                (center_x - r + 8, center_y - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_blindinglight_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        center_x = x + facing * 40
        center_y = y + 15

        if progress < 0.2:
            # Charge up.
            t = progress / 0.2
            cr = int(4 + t * 8)
            if hasattr(_NS_luminar, "_orb_pos"):
                sx, sy = _NS_luminar._orb_pos
            else:
                sx = x + facing * 20
                sy = y - 20
            for r in range(cr + 3, 0, -1):
                alpha = _NS_luminar._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                        (sx, sy), r)
        else:
            # BIG FLASH burst.
            t = (progress - 0.2) / 0.8
            intensity = math.sin(t * math.pi)
            radius = int(20 + t * 50)

            # Multi-layer flash.
            for r in range(radius, 2, -3):
                alpha = _NS_luminar._alpha(180 * intensity * (radius - r) / radius)
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                        (center_x, center_y), r)
            for r in range(int(radius * 0.7), 2, -3):
                alpha = _NS_luminar._alpha(200 * intensity * (radius * 0.7 - r) / (radius * 0.7))
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_hot"], alpha),
                                        (center_x, center_y), r)
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_shine"],
                                    (center_x, center_y), max(1, radius // 3))
            _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["white"],
                                    (center_x, center_y), max(1, radius // 5))

            # Radial shockwave lines (pushback effect).
            alpha_val = _NS_luminar._alpha(230 * intensity)
            for i in range(16):
                angle_s = i * math.pi / 8
                # Two lines per direction.
                for line_off in (0, 3):
                    ex = center_x + int(math.cos(angle_s) * (radius + line_off))
                    ey = center_y + int(math.sin(angle_s) * (radius + line_off) * 0.7)
                    ix = center_x + int(math.cos(angle_s) * (radius - 6))
                    iy = center_y + int(math.sin(angle_s) * (radius - 6) * 0.7)
                    pygame.draw.line(surface, (*_NS_luminar.PALETTE["light_hot"], alpha_val),
                                     (ix, iy), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha_val),
                                     (ex, ey, 2, 2))

            # Star sparkles.
            for i in range(20):
                spark_angle = phase * 3 + i * math.pi / 10
                spark_r = int(radius * (0.5 + (i % 4) * 0.15))
                sx = center_x + int(math.cos(spark_angle) * spark_r)
                sy = center_y + int(math.sin(spark_angle) * spark_r * 0.7)
                pygame.draw.rect(surface, _NS_luminar.PALETTE["light_shine"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_luminar.PALETTE["white"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: WILL-O-WISP (blue wisp pulsing pull)
    # ============================================================
    def _draw_wisp_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_luminar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground indicator - pulsing rings.
        r = int(25 + math.sin(phase * 2) * 5)
        alpha = _NS_luminar._alpha(180)

        pygame.draw.ellipse(surface, (*_NS_luminar.PALETTE["light_dark"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_luminar.PALETTE["light_mid"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)

        # Pulling lines (from ring to center).
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.5
            pull_t = (phase + i * 0.1) % 1.0
            ex = tx + int(math.cos(angle) * r * (1 - pull_t * 0.7))
            ey = ty + int(math.sin(angle) * r * (1 - pull_t * 0.7) * 0.5)
            alpha_p = _NS_luminar._alpha(200 * (1 - pull_t))
            pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_hot"], alpha_p),
                             (ex, ey, 2, 2))

    def _draw_wisp_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_luminar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wisp floating above ground.
        float_y = ty - 20 + int(math.sin(phase * 2) * 4)
        wisp_x = tx + int(math.sin(phase * 1.5) * 5)

        # Wisp pulse (rhythmic).
        pulse_beat = (math.sin(phase * 3) + 1) / 2  # 0-1

        # Outer glow.
        for r in range(18, 2, -1):
            alpha = _NS_luminar._alpha(140 * pulse_beat * (18 - r) / 18)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (wisp_x, float_y), r)

        # Wisp core (bright blue-white).
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_darkest"],
                                (wisp_x, float_y), 5)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_dark"],
                                (wisp_x, float_y), 4)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_bright"],
                                (wisp_x, float_y), 3)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_hot"],
                                (wisp_x, float_y), 2)
        _NS_luminar._aacircle(surface, _NS_luminar.PALETTE["light_shine"],
                                (wisp_x, float_y), 1)
        pygame.draw.rect(surface, _NS_luminar.PALETTE["white"],
                         (wisp_x, float_y, 1, 1))

        # Wisp face (2 small eyes and tail).
        pygame.draw.rect(surface, _NS_luminar.PALETTE["shadow_deep"],
                         (wisp_x - 2, float_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_luminar.PALETTE["shadow_deep"],
                         (wisp_x + 1, float_y - 1, 1, 1))

        # Trailing tail (below wisp).
        for i in range(4):
            trail_t = (phase * 0.8 + i * 0.15) % 1.0
            trail_y = float_y + int(trail_t * 12)
            trail_x = wisp_x + int(math.sin(phase * 2 + i) * 3)
            alpha = _NS_luminar._alpha(200 * (1 - trail_t))
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                    (trail_x, trail_y), max(1, 3 - i))
            pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                             (trail_x, trail_y, 1, 1))

        # Rhythmic pulse expanding rings.
        pulse_t = (phase * 0.8) % 1.0
        pulse_r = int(pulse_t * 30)
        pulse_alpha = _NS_luminar._alpha(200 * (1 - pulse_t))
        if pulse_alpha > 0:
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_hot"], pulse_alpha),
                                    (wisp_x, float_y), pulse_r, 2)
            _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_shine"], pulse_alpha),
                                    (wisp_x, float_y), max(1, pulse_r - 2), 1)

    # ============================================================
    # SKILL R: SPIRIT FORM (transform to ghostly ethereal form)
    # ============================================================
    def _draw_spiritform_foreground(surface, boss, x, y, timer, phase):
        """Boss transforms into ethereal spirit form (already handled in body draw)."""
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Extra ethereal effects around boss.
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Spectral wings behind (ethereal white wings).
        _NS_luminar._draw_spirit_wings(surface, x, y - 10, boss.direction, phase)

        # Ascending light particles.
        for i in range(15):
            t = (phase * 0.4 + i * 0.07) % 1.0
            px = x - 35 + i * 5 + int(math.sin(phase + i) * 5)
            py = y + 30 - int(t * 60)
            alpha = _NS_luminar._alpha(230 * (1 - t) * pulse)
            if alpha > 0:
                _NS_luminar._aacircle(surface, (*_NS_luminar.PALETTE["light_bright"], alpha),
                                        (px, py), 2)
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_luminar.PALETTE["white"], alpha),
                                 (px, py, 1, 1))

        # Divine sparkles.
        for i in range(10):
            angle = phase * 1.5 + i * math.pi / 5
            r = 45 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r * 0.5)
            alpha = _NS_luminar._alpha(230 * pulse)
            pygame.draw.rect(surface, (*_NS_luminar.PALETTE["light_shine"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_luminar.PALETTE["white"], alpha),
                             (sx, sy, 1, 1))

    def _draw_spirit_wings(surface, cx, cy, facing, phase):
        """Ethereal angelic wings for spirit form."""
        beat = math.sin(phase * 1.2) * 3

        wing_surf = pygame.Surface((160, 120), pygame.SRCALPHA)
        offset_x = cx - 80
        offset_y = cy - 60

        for side_mult in (-1, 1):
            base_x = 80 - side_mult * 8
            base_y = 60

            # Wing feathers (3 layers).
            for i, (angle_off, length) in enumerate([
                (0.5, 30), (0.3, 35), (0.15, 28), (0.0, 22),
            ]):
                angle = math.pi * angle_off * side_mult - math.radians(beat)
                tip_x = base_x + int(math.cos(angle) * length) * (-side_mult)
                tip_y = base_y - int(math.sin(angle) * length) - 5

                # Feather.
                perp = angle + math.pi / 2
                pa_x = base_x + int(math.cos(perp) * 3) * (-side_mult)
                pa_y = base_y + int(math.sin(perp) * 3)
                pb_x = base_x - int(math.cos(perp) * 3) * (-side_mult)
                pb_y = base_y - int(math.sin(perp) * 3)

                # Translucent white feather.
                pygame.draw.polygon(wing_surf,
                                    (*_NS_luminar.PALETTE["light_bright"], 120),
                                    [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
                pygame.draw.polygon(wing_surf,
                                    (*_NS_luminar.PALETTE["light_hot"], 160),
                                    [(tip_x, tip_y),
                                     (int((tip_x + base_x) / 2),
                                      int((tip_y + base_y) / 2)),
                                     (base_x, base_y)])
                pygame.draw.polygon(wing_surf,
                                    (*_NS_luminar.PALETTE["light_shine"], 200),
                                    [(tip_x, tip_y),
                                     (int((tip_x + base_x) * 0.7),
                                      int((tip_y + base_y) * 0.7)),
                                     (base_x, base_y)])
                # Bright tip.
                pygame.draw.rect(wing_surf,
                                 (*_NS_luminar.PALETTE["white"], 240),
                                 (tip_x, tip_y, 2, 2))

        surface.blit(wing_surf, (offset_x, offset_y))


# ====================================================================
# solara.py
# ====================================================================



class _NS_solara:
    """Namespace solara - Dawnforged Sentinel mini boss (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Armor (gold plate)
        "armor_darkest": (30, 15, 5),
        "armor_dark": (85, 50, 15),
        "armor_mid": (170, 115, 40),
        "armor_light": (235, 185, 80),
        "armor_edge": (255, 220, 130),
        "armor_shine": (255, 245, 200),

        # Bronze/copper undertone
        "bronze_dark": (60, 30, 10),
        "bronze_mid": (130, 75, 30),
        "bronze_light": (200, 140, 60),

        # Solar fire (hammer glow, aura)
        "solar_darkest": (50, 15, 0),
        "solar_dark": (130, 50, 5),
        "solar_mid": (230, 120, 20),
        "solar_light": (255, 190, 60),
        "solar_hot": (255, 235, 130),
        "solar_shine": (255, 250, 220),

        # Red accents (cape, inner robes)
        "red_dark": (60, 15, 15),
        "red_mid": (140, 35, 30),
        "red_light": (210, 70, 55),

        # Eye glow (fierce white-gold)
        "eye_socket": (10, 5, 0),
        "eye_darkest": (60, 30, 5),
        "eye_dark": (150, 90, 20),
        "eye_mid": (240, 180, 60),
        "eye_light": (255, 235, 150),
        "eye_glow": (255, 255, 240),

        # Skin (weathered warrior)
        "skin_dark": (90, 60, 45),
        "skin_mid": (160, 115, 90),
        "skin_light": (215, 175, 145),

        # Hair (fiery blonde)
        "hair_dark": (100, 55, 15),
        "hair_mid": (190, 130, 40),
        "hair_light": (250, 210, 100),
        "hair_shine": (255, 245, 190),

        # Hammer head
        "hammer_dark": (40, 25, 10),
        "hammer_mid": (110, 75, 30),
        "hammer_light": (200, 145, 55),

        # Ground / holy
        "holy_dim": (150, 110, 50),
        "holy_bright": (255, 230, 140),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 2, 1),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_solara._clamp(color)
        if _NS_solara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_solara._clamp(color)
        if _NS_solara.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_solara._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 100 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_solara(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_solara._update_sol_attack_anim(boss)
        attacking = (
            getattr(boss, "_slr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_solara._draw_solar_aura(surface, x, y, pulse)
        _NS_solara._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_solara._draw_luminosity_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_solara._draw_solarguardian_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_solara._draw_starbreaker_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_solara._draw_sol_attack(surface, boss, x, y)
        else:
            _NS_solara._draw_sol_idle(surface, boss, x, y)

        # Solar Guardian dome over allies (drawn on top).
        if active_skill == "r":
            _NS_solara._draw_solarguardian_dome(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_solara._draw_starbreaker_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_solara._draw_celestialhammer_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_solara._draw_luminosity_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_solara._draw_solarguardian_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_sol_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_slr_previous_timer", 0))
        active = bool(getattr(boss, "_slr_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._slr_attack_active = True
            boss._slr_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._slr_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._slr_attack_frame = int(
                getattr(boss, "_slr_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._slr_attack_active = False
            boss._slr_attack_frame = 0
            active = False

        boss._slr_previous_timer = timer
        boss._slr_attack_progress = (
            min(1.0, getattr(boss, "_slr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_sol_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_solara._draw_floating_shadow(surface, x, y + 50, boss.pulse)
        _NS_solara._draw_solar_wisps(surface, x, y + 40, boss.pulse)
        _NS_solara._draw_sol_body(surface, x, y + bob, boss.direction,
                                   boss.pulse, "idle")

    def _draw_sol_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_slr_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_slr_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.7) * 5)
        # Hammer swing: rear-back → forward smash → recovery
        if progress < 0.35:
            t = progress / 0.35
            lean = int(t * -3) * facing
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 9)) * facing
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(6 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_solara._draw_floating_shadow(surface, x + lean, y + 50, boss.pulse)
        _NS_solara._draw_solar_wisps(surface, x + lean, y + 40, boss.pulse,
                                      intense=True)
        _NS_solara._draw_sol_body(surface, x + lean, y + bob - lift,
                                   facing, boss.pulse, "attack",
                                   progress)
        _NS_solara._draw_swing_arc(surface, boss, x + lean, y + bob - lift,
                                    progress)

    # ============================================================
    # BODY (heavy armored knight)
    # ============================================================
    def _draw_sol_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cape behind.
        _NS_solara._draw_cape(surface, cx, cy - 2, facing, phase)

        # Legs/lower armor (skirt).
        _NS_solara._draw_armor_skirt(surface, cx, cy + 6, facing, phase)

        # Torso.
        _NS_solara._draw_knight_torso(surface, cx, cy - 2, facing, phase)

        # Non-hammer arm (shield-side or free).
        _NS_solara._draw_free_arm(surface, cx, cy - 2, facing, phase, action,
                                   attack_progress)

        # Head with helmet.
        _NS_solara._draw_knight_head(surface, cx, cy - 14, facing, phase)

        # Hammer arm + hammer (drawn last so hammer overlays).
        _NS_solara._draw_hammer_arm(surface, cx, cy - 2, facing, phase, action,
                                     attack_progress)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Red cape flowing behind."""
        sway = math.sin(phase * 0.6) * 3
        cape_pts = [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 11 + int(sway), cy + 10),
            (cx + 13 + int(sway), cy + 18),
            (cx + 8 + int(sway), cy + 24),
            (cx - 8 - int(sway), cy + 24),
            (cx - 13 - int(sway), cy + 18),
            (cx - 11 - int(sway), cy + 10),
        ]
        _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 2) for p in cape_pts])
        _NS_solara._poly(surface, _NS_solara.PALETTE["red_dark"], cape_pts)
        _NS_solara._poly(surface, _NS_solara.PALETTE["red_mid"], [
            (cx - 6, cy + 1),
            (cx + 6, cy + 1),
            (cx + 10 + int(sway), cy + 11),
            (cx + 7 + int(sway), cy + 22),
            (cx - 7 - int(sway), cy + 22),
            (cx - 10 - int(sway), cy + 11),
        ])
        _NS_solara._poly(surface, _NS_solara.PALETTE["red_light"], [
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 4, cy + 14),
            (cx - 4, cy + 14),
        ])

        # Gold trim at bottom edge of cape.
        for dx1, dx2, dy in [(-13, 13, 18), (-11, 11, 22)]:
            trim_y = cy + dy
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_dark"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 1)
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_light"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 1)

    def _draw_armor_skirt(surface, cx, cy, facing, phase):
        """Armored skirt/tassets covering legs."""
        # Main plate.
        skirt_pts = [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 11, cy + 10),
            (cx + 8, cy + 15),
            (cx - 8, cy + 15),
            (cx - 11, cy + 10),
        ]
        _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in skirt_pts])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"], skirt_pts)
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
            (cx - 8, cy - 3),
            (cx + 8, cy - 3),
            (cx + 10, cy + 9),
            (cx + 7, cy + 14),
            (cx - 7, cy + 14),
            (cx - 10, cy + 9),
        ])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_mid"], [
            (cx - 6, cy - 1),
            (cx + 6, cy - 1),
            (cx + 8, cy + 8),
            (cx + 5, cy + 12),
            (cx - 5, cy + 12),
            (cx - 8, cy + 8),
        ])

        # Vertical plate divisions.
        for x_off in (-6, 0, 6):
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_darkest"],
                             (cx + x_off, cy - 3),
                             (cx + int(x_off * 1.3), cy + 13), 1)

        # Central emblem (sun symbol).
        emblem_y = cy + 5
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_darkest"],
                         (cx - 3, emblem_y - 2, 6, 5))
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_dark"],
                              (cx, emblem_y), 3)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_mid"],
                              (cx, emblem_y), 2)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_light"],
                              (cx, emblem_y), 1)
        # Sun rays.
        for i in range(4):
            angle = i * math.pi / 2
            rx = cx + int(math.cos(angle) * 4)
            ry = emblem_y + int(math.sin(angle) * 4)
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_light"], (rx, ry, 1, 1))

        # Highlight edges.
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_edge"], [
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 5, cy + 3),
            (cx - 5, cy + 3),
        ])

        # Boots/greaves below skirt.
        for side in (-1, 1):
            boot_x = cx + side * 4
            _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"], [
                (boot_x - 3, cy + 15),
                (boot_x + 3, cy + 15),
                (boot_x + 4, cy + 20),
                (boot_x - 4, cy + 20),
            ])
            _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
                (boot_x - 3, cy + 14),
                (boot_x + 3, cy + 14),
                (boot_x + 4, cy + 19),
                (boot_x - 4, cy + 19),
            ])
            _NS_solara._poly(surface, _NS_solara.PALETTE["armor_mid"], [
                (boot_x - 2, cy + 15),
                (boot_x + 2, cy + 15),
                (boot_x + 3, cy + 18),
                (boot_x - 3, cy + 18),
            ])
            pygame.draw.rect(surface, _NS_solara.PALETTE["armor_edge"],
                             (boot_x - 1, cy + 16, 2, 1))

    def _draw_knight_torso(surface, cx, cy, facing, phase):
        """Heavy chest plate."""
        torso_pts = [
            (cx - 11, cy - 4),
            (cx - 9, cy + 5),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 9, cy + 5),
            (cx + 11, cy - 4),
            (cx + 9, cy - 6),
            (cx - 9, cy - 6),
        ]
        _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"], torso_pts)

        # Main chest plate.
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 8, cy + 6),
            (cx - 8, cy + 6),
        ])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ])

        # Muscle definition (V-shape lines).
        pygame.draw.line(surface, _NS_solara.PALETTE["armor_darkest"],
                         (cx, cy - 3), (cx - 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_solara.PALETTE["armor_darkest"],
                         (cx, cy - 3), (cx + 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_solara.PALETTE["armor_edge"],
                         (cx, cy - 2), (cx - 3, cy + 4), 1)
        pygame.draw.line(surface, _NS_solara.PALETTE["armor_edge"],
                         (cx, cy - 2), (cx + 3, cy + 4), 1)

        # Central sun emblem (glowing).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        emblem_y = cy + 1
        # Ring.
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_darkest"],
                              (cx, emblem_y), 4)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_dark"],
                              (cx, emblem_y), 3)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_mid"],
                              (cx, emblem_y), 2)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_hot"],
                              (cx, emblem_y), 1)
        # Rays around emblem.
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.3
            rx = cx + int(math.cos(angle) * 5)
            ry = emblem_y + int(math.sin(angle) * 5)
            alpha = _NS_solara._alpha(200 * pulse)
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_light"], (rx, ry, 1, 1))

        # Glow around emblem.
        for r in range(6, 1, -1):
            alpha = _NS_solara._alpha(70 * pulse * (6 - r) / 6)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                  (cx, emblem_y), r)

        # Shoulder pauldrons (big, gold).
        for side in (-1, 1):
            paul_x = cx + side * 10
            paul_pts = [
                (paul_x - 4, cy - 5),
                (paul_x + 4, cy - 5),
                (paul_x + 5, cy - 1),
                (paul_x + 3, cy + 3),
                (paul_x - 3, cy + 3),
                (paul_x - 5, cy - 1),
            ]
            _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in paul_pts])
            _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"], paul_pts)
            _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
                (paul_x - 3, cy - 4),
                (paul_x + 3, cy - 4),
                (paul_x + 4, cy - 1),
                (paul_x + 2, cy + 2),
                (paul_x - 2, cy + 2),
                (paul_x - 4, cy - 1),
            ])
            _NS_solara._poly(surface, _NS_solara.PALETTE["armor_mid"], [
                (paul_x - 2, cy - 3),
                (paul_x + 2, cy - 3),
                (paul_x + 3, cy),
                (paul_x - 3, cy),
            ])
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_edge"],
                             (paul_x - 2, cy - 2), (paul_x + 2, cy - 2), 1)
            pygame.draw.rect(surface, _NS_solara.PALETTE["armor_shine"],
                             (paul_x, cy - 3, 1, 1))
            # Rivet stud.
            pygame.draw.rect(surface, _NS_solara.PALETTE["bronze_light"],
                             (paul_x, cy + 1, 1, 1))

    def _draw_free_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Non-hammer arm (back side)."""
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx - facing * 9
        shoulder_y = cy - 2
        # During attack, arm braces.
        if action == "attack":
            elbow_y_off = -3 + int(math.sin(attack_progress * math.pi) * -2)
        else:
            elbow_y_off = 4 + int(sway)

        elbow_x = shoulder_x - facing * 3
        elbow_y = shoulder_y + elbow_y_off
        hand_x = elbow_x - facing * 2
        hand_y = elbow_y + 5

        # Upper arm.
        _NS_solara._aaline(surface, _NS_solara.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 5)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_solara._aaline(surface, _NS_solara.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 4)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Gauntlet.
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 3)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_dark"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_edge"],
                         (hand_x, hand_y - 1, 1, 1))

    def _draw_hammer_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Main arm holding hammer with swing animation."""
        # Determine swing angle based on action.
        if action == "attack":
            if attack_progress < 0.35:
                # Rear back (raise hammer up-back).
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.3 + t * -math.pi * 0.4  # from -54° to -126°
                hammer_angle = arm_angle - math.pi * 0.2
            elif attack_progress < 0.6:
                # Swing forward (smash down).
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.7 + t * math.pi * 0.9  # sweep down
                hammer_angle = arm_angle
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.2 - t * math.pi * 0.5
                hammer_angle = arm_angle + math.pi * 0.1
        else:
            # Idle: hammer resting on shoulder or held ready.
            arm_angle = -math.pi * 0.3 + math.sin(phase * 0.5) * 0.05
            hammer_angle = arm_angle - math.pi * 0.2

        shoulder_x = cx + facing * 9
        shoulder_y = cy - 2

        arm_len = 8
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len)

        forearm_len = 7
        forearm_angle = arm_angle + 0.3
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm.
        _NS_solara._aaline(surface, _NS_solara.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_edge"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_solara._aaline(surface, _NS_solara.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_solara._aaline(surface, _NS_solara.PALETTE["armor_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Gauntlet.
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 4)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 4)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_dark"],
                              (hand_x, hand_y), 3)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_mid"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_edge"],
                         (hand_x, hand_y - 1, 1, 1))

        # HAMMER.
        _NS_solara._draw_solar_hammer(surface, hand_x, hand_y, hammer_angle,
                                        facing, phase, action, attack_progress)

    def _draw_solar_hammer(surface, hand_x, hand_y, angle, facing, phase, action,
                            attack_progress):
        """Big war hammer with solar glow."""
        # Hammer shaft length.
        shaft_len = 18
        head_end_x = hand_x + int(math.cos(angle) * shaft_len) * facing
        head_end_y = hand_y + int(math.sin(angle) * shaft_len)
        # Back end (pommel).
        pommel_x = hand_x - int(math.cos(angle) * 4) * facing
        pommel_y = hand_y - int(math.sin(angle) * 4)

        # Wooden shaft.
        pygame.draw.line(surface, _NS_solara.PALETTE["shadow_deep"],
                         (pommel_x + 1, pommel_y + 1),
                         (head_end_x + 1, head_end_y + 1), 4)
        pygame.draw.line(surface, _NS_solara.PALETTE["hammer_dark"],
                         (pommel_x, pommel_y), (head_end_x, head_end_y), 3)
        pygame.draw.line(surface, _NS_solara.PALETTE["hammer_mid"],
                         (pommel_x, pommel_y), (head_end_x, head_end_y), 2)
        pygame.draw.line(surface, _NS_solara.PALETTE["hammer_light"],
                         (pommel_x, pommel_y - 1),
                         (head_end_x, head_end_y - 1), 1)

        # Gold wrapping bands.
        for t_pos in (0.3, 0.6):
            wrap_x = int(pommel_x + (head_end_x - pommel_x) * t_pos)
            wrap_y = int(pommel_y + (head_end_y - pommel_y) * t_pos)
            perp = angle + math.pi / 2
            wa = (wrap_x + int(math.cos(perp) * 3) * facing,
                  wrap_y + int(math.sin(perp) * 3))
            wb = (wrap_x - int(math.cos(perp) * 3) * facing,
                  wrap_y - int(math.sin(perp) * 3))
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_dark"], wa, wb, 1)
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_edge"],
                             (wa[0], wa[1] - 1), (wb[0], wb[1] - 1), 1)

        # Hammer HEAD (big rectangular block).
        perp = angle + math.pi / 2
        head_w = 9
        head_h = 7
        # Compute 4 corners of hammer head oriented to shaft.
        cos_a = math.cos(angle) * facing
        sin_a = math.sin(angle)
        # Extend beyond shaft tip.
        head_center_x = head_end_x + int(cos_a * 4)
        head_center_y = head_end_y + int(sin_a * 4)

        # Perpendicular axis for head width.
        perp_x = -sin_a
        perp_y = cos_a

        # 4 corners.
        c1 = (head_center_x - int(cos_a * head_w) + int(perp_x * head_h),
              head_center_y - int(sin_a * head_w) + int(perp_y * head_h))
        c2 = (head_center_x + int(cos_a * head_w) + int(perp_x * head_h),
              head_center_y + int(sin_a * head_w) + int(perp_y * head_h))
        c3 = (head_center_x + int(cos_a * head_w) - int(perp_x * head_h),
              head_center_y + int(sin_a * head_w) - int(perp_y * head_h))
        c4 = (head_center_x - int(cos_a * head_w) - int(perp_x * head_h),
              head_center_y - int(sin_a * head_w) - int(perp_y * head_h))

        # Shadow.
        _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"],
                         [(c[0] + 2, c[1] + 2) for c in (c1, c2, c3, c4)])

        # Head block (layers).
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"],
                         [c1, c2, c3, c4])
        # Inner smaller block.
        inner_shrink = 0.8
        cx_h = sum(c[0] for c in (c1, c2, c3, c4)) / 4
        cy_h = sum(c[1] for c in (c1, c2, c3, c4)) / 4
        inner = [(int(c[0] * inner_shrink + cx_h * (1 - inner_shrink)),
                  int(c[1] * inner_shrink + cy_h * (1 - inner_shrink)))
                 for c in (c1, c2, c3, c4)]
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], inner)

        inner2 = [(int(c[0] * 0.6 + cx_h * 0.4),
                   int(c[1] * 0.6 + cy_h * 0.4))
                  for c in (c1, c2, c3, c4)]
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_mid"], inner2)

        # Center highlight.
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_edge"],
                         (int(cx_h - 1), int(cy_h - 1), 2, 2))
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_shine"],
                         (int(cx_h), int(cy_h), 1, 1))

        # GLOWING SOLAR CORE inside hammer head.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        core_x = int(cx_h)
        core_y = int(cy_h)

        for r in range(8, 1, -1):
            alpha = _NS_solara._alpha(160 * pulse * (8 - r) / 8)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                  (core_x, core_y), r)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_dark"],
                              (core_x, core_y), 3)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_mid"],
                              (core_x, core_y), 2)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_hot"],
                              (core_x, core_y), 1)
        pygame.draw.rect(surface, _NS_solara.PALETTE["white"],
                         (core_x, core_y, 1, 1))

        # Trailing sparks around hammer head.
        for i in range(6):
            spark_angle = phase * 2 + i * math.pi / 3
            sx = core_x + int(math.cos(spark_angle) * (head_w + 2))
            sy = core_y + int(math.sin(spark_angle) * (head_h + 2))
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_shine"], (sx, sy, 1, 1))

        # Pommel (small solar orb).
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["armor_darkest"],
                              (pommel_x, pommel_y), 2)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_mid"],
                              (pommel_x, pommel_y), 1)

        # Store hammer head position for swing arc.
        _NS_solara._hammer_head = (core_x, core_y)
        _NS_solara._hammer_angle = angle

    def _draw_knight_head(surface, cx, cy, facing, phase):
        """Helmet with sun-ray crest and glowing visor."""
        # Helmet base.
        helm_pts = [
            (cx - 6, cy + 3),
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 3),
            (cx + 5, cy + 6),
            (cx - 5, cy + 6),
        ]
        _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 2) for p in helm_pts])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"], helm_pts)

        # Main helm color.
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
            (cx - 5, cy + 2),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx - 1, cy - 8),
            (cx + 1, cy - 8),
            (cx + 4, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 2),
            (cx + 4, cy + 5),
            (cx - 4, cy + 5),
        ])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_mid"], [
            (cx - 4, cy - 1),
            (cx - 3, cy - 5),
            (cx, cy - 7),
            (cx + 3, cy - 5),
            (cx + 4, cy - 1),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])

        # Highlight top.
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_edge"],
                         (cx - 1, cy - 6, 3, 1))
        pygame.draw.rect(surface, _NS_solara.PALETTE["armor_shine"],
                         (cx, cy - 6, 1, 1))

        # Visor slit (dark, with glowing eyes).
        visor_y = cy - 2
        pygame.draw.rect(surface, _NS_solara.PALETTE["shadow_deep"],
                         (cx - 4, visor_y, 8, 3))
        pygame.draw.rect(surface, _NS_solara.PALETTE["eye_socket"],
                         (cx - 3, visor_y, 6, 2))

        # Eyes (glowing solar).
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = visor_y + 1
            # Glow behind.
            for r in range(3, 0, -1):
                alpha = _NS_solara._alpha(120 * pulse * (3 - r) / 3)
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                      (ex, ey), r)
            pygame.draw.rect(surface, _NS_solara.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_solara.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

        # Mouth grille (small vertical lines below visor).
        for x_off in (-2, 0, 2):
            pygame.draw.line(surface, _NS_solara.PALETTE["shadow_deep"],
                             (cx + x_off, cy + 1), (cx + x_off, cy + 3), 1)

        # SOLAR CREST/HORNS (sun-ray shape on top).
        _NS_solara._draw_solar_crest(surface, cx, cy, facing, phase)

        # Cheek guards.
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_darkest"],
                             (cx + side * 5, cy - 1),
                             (cx + side * 4, cy + 4), 1)
            pygame.draw.line(surface, _NS_solara.PALETTE["armor_edge"],
                             (cx + side * 4, cy - 1),
                             (cx + side * 4, cy + 3), 1)

    def _draw_solar_crest(surface, cx, cy, facing, phase):
        """Sun-ray crest on top of helmet."""
        beat = math.sin(phase * 1.5) * 1

        # Big central spike (needs 3 points minimum).
        _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"], [
            (cx + 1, cy - 16 + int(beat)),
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
        ])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"], [
            (cx, cy - 16 + int(beat)),
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
        ])
        _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
            (cx, cy - 15 + int(beat)),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
        ])
        # FIX: was only 2 points, now proper triangle.
        _NS_solara._poly(surface, _NS_solara.PALETTE["solar_mid"], [
            (cx, cy - 14 + int(beat)),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
        ])
        pygame.draw.rect(surface, _NS_solara.PALETTE["solar_light"],
                         (cx, cy - 14 + int(beat), 1, 1))

        # Side spikes (fan out).
        for i, (angle_off, length) in enumerate([
            (0.85, 8), (0.65, 10), (0.4, 7),
        ]):
            for side in (-1, 1):
                angle = math.pi * angle_off * side
                tip_x = cx + int(math.cos(angle) * length)
                tip_y = cy - 8 - int(math.sin(angle) * length) + int(beat * 0.5)
                base_x = cx + int(math.cos(angle) * 2)
                base_y = cy - 8

                perp = angle + math.pi / 2
                pa_x = base_x + int(math.cos(perp) * 1)
                pa_y = base_y + int(math.sin(perp) * 1)
                pb_x = base_x - int(math.cos(perp) * 1)
                pb_y = base_y - int(math.sin(perp) * 1)

                # Make sure points differ (avoid degenerate polys).
                if (pa_x, pa_y) == (pb_x, pb_y):
                    pb_x += 1

                _NS_solara._poly(surface, _NS_solara.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (pa_x + 1, pa_y + 1),
                    (pb_x + 1, pb_y + 1),
                ])
                _NS_solara._poly(surface, _NS_solara.PALETTE["armor_darkest"],
                                 [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])

                # Mid triangle - make sure 3 unique points.
                mid_a = (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2))
                if mid_a == (tip_x, tip_y) or mid_a == (base_x, base_y):
                    mid_a = (mid_a[0] + 1, mid_a[1])
                _NS_solara._poly(surface, _NS_solara.PALETTE["armor_dark"], [
                    (tip_x, tip_y),
                    mid_a,
                    (base_x, base_y),
                ])

                mid_b = (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2))
                if mid_b == (tip_x, tip_y) or mid_b == (base_x, base_y):
                    mid_b = (mid_b[0] + 1, mid_b[1])
                _NS_solara._poly(surface, _NS_solara.PALETTE["solar_mid"], [
                    (tip_x, tip_y),
                    mid_b,
                    (base_x, base_y),
                ])
                pygame.draw.rect(surface, _NS_solara.PALETTE["solar_light"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_solara.PALETTE["solar_hot"],
                                 (tip_x, tip_y, 1, 1))
    # ============================================================
    # SWING ARC (melee slash effect)
    # ============================================================
    def _draw_swing_arc(surface, boss, x, y, progress):
        """Arc trail from hammer swing."""
        # Only during swing phase (0.35 - 0.6).
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction

        # Get hammer position if available.
        if not hasattr(_NS_solara, "_hammer_head"):
            return
        hammer_x, hammer_y = _NS_solara._hammer_head

        # Arc from previous swing position to current.
        swing_t = (progress - 0.35) / 0.25
        swing_t = max(0, min(1, swing_t))
        alpha_val = int(255 * (1 - abs(swing_t - 0.5) * 2))

        # Arc as curved line of glowing segments.
        center_x = x + facing * 6
        center_y = y + 4
        arc_radius = 22

        # Trail from start angle to current angle.
        start_angle = -math.pi * 0.9 * facing
        end_angle = math.pi * 0.2 * facing
        current_angle = start_angle + (end_angle - start_angle) * swing_t

        # Draw arc trail.
        num_segments = 12
        for i in range(num_segments):
            t = i / num_segments
            seg_angle = start_angle + (current_angle - start_angle) * t
            seg_x = center_x + int(math.cos(seg_angle) * arc_radius) * facing
            seg_y = center_y + int(math.sin(seg_angle) * arc_radius)
            seg_alpha = _NS_solara._alpha(alpha_val * t)
            size = int(3 + t * 4)

            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_darkest"], seg_alpha),
                                  (seg_x, seg_y), size)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_dark"], seg_alpha),
                                  (seg_x, seg_y), max(1, size - 1))
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_mid"], seg_alpha),
                                  (seg_x, seg_y), max(1, size - 2))
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], seg_alpha),
                                  (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Sparks flying.
        for i in range(8):
            spark_angle = current_angle + i * 0.15 * facing
            spark_dist = arc_radius + i * 2
            sx = center_x + int(math.cos(spark_angle) * spark_dist) * facing
            sy = center_y + int(math.sin(spark_angle) * spark_dist)
            spark_alpha = _NS_solara._alpha(220 - i * 25)
            pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_hot"], spark_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_shine"], spark_alpha),
                             (sx, sy, 1, 1))

        # Impact flash at end of swing (last 25%).
        if swing_t > 0.75:
            impact_t = (swing_t - 0.75) / 0.25
            impact_x = center_x + int(math.cos(current_angle) * arc_radius) * facing
            impact_y = center_y + int(math.sin(current_angle) * arc_radius)
            radius = int(6 + impact_t * 12)
            impact_alpha = _NS_solara._alpha(230 * (1 - impact_t))

            for r in range(radius, 1, -1):
                a = _NS_solara._alpha(impact_alpha * (radius - r) / radius)
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], a),
                                      (impact_x, impact_y), r)
            _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_hot"],
                                  (impact_x, impact_y), 3)
            _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_shine"],
                                  (impact_x, impact_y), 2)
            pygame.draw.rect(surface, _NS_solara.PALETTE["white"],
                             (impact_x, impact_y, 1, 1))

            # Radial burst lines.
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = impact_x + int(math.cos(angle_s) * radius)
                ey = impact_y + int(math.sin(angle_s) * radius)
                pygame.draw.line(surface, (*_NS_solara.PALETTE["solar_hot"], impact_alpha),
                                 (impact_x, impact_y), (ex, ey), 1)

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        w = int(70 * pulse)
        h = int(10 * pulse)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (50 - w // 2 - radius, 10 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (30, 15, 5, 150),
                            (50 - w // 2, 10 - h // 2, w, h))
        surface.blit(shadow, (x - 50, y - 10))

    def _draw_solar_wisps(surface, cx, cy, phase, intense=False):
        """Rising solar sparks/embers below the knight."""
        strength = 1.5 if intense else 1.0

        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 24 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_solara._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_darkest"], alpha),
                                  (sx, sy), 3)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_dark"], alpha),
                                  (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Embers.
        for i in range(6):
            ember_t = (phase * 0.4 + i * 0.17) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(ember_t * 24)
            alpha = _NS_solara._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_solar_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_solara._alpha((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_solara._aacircle(aura, (*_NS_solara.PALETTE["solar_darkest"], alpha),
                                      (100, 80), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_solara._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_solara._aacircle(aura, (*_NS_solara.PALETTE["solar_dark"], alpha),
                                      (100, 80), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_solara._alpha((30 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_solara._aacircle(aura, (*_NS_solara.PALETTE["solar_mid"], alpha),
                                      (100, 80), radius)
        surface.blit(aura, (x - 100, y - 80))

        # Floating embers.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_solara.PALETTE["solar_darkest"], 200),
                            (5, 15, 150, 25), 3)
        pygame.draw.ellipse(ring, (*_NS_solara.PALETTE["solar_dark"], 220),
                            (14, 17, 132, 21), 2)
        pygame.draw.ellipse(ring, (*_NS_solara.PALETTE["solar_mid"], 230),
                            (25, 19, 110, 17), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_solara.PALETTE["solar_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_solara.PALETTE["solar_hot"],
                                        _NS_solara._alpha(150 * pulse)),
                                (15, 10, 130, 35), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q: STARBREAKER (3 swings, escalating)
    # ============================================================
    def _draw_starbreaker_ground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground crack under boss expanding with each swing.
        # 3 pulses at 0.3, 0.55, 0.9.
        for pulse_t in (0.3, 0.55, 0.85):
            if progress > pulse_t and progress < pulse_t + 0.15:
                t = (progress - pulse_t) / 0.15
                r = int(20 + t * 30)
                # Third swing bigger.
                if pulse_t > 0.8:
                    r = int(30 + t * 45)
                alpha = _NS_solara._alpha(200 * (1 - t))
                pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_darkest"], alpha),
                                    (x - r, y + 35 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_mid"], alpha),
                                    (x - r + 3, y + 35 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                                    (x - r + 8, y + 35 - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_starbreaker_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 3 shockwave pulses forward.
        for i, pulse_t in enumerate((0.3, 0.55, 0.85)):
            if progress > pulse_t and progress < pulse_t + 0.2:
                t = (progress - pulse_t) / 0.2
                # Third pulse biggest.
                max_r = 60 if i == 2 else 40
                r = int(max_r * t)
                alpha = _NS_solara._alpha(220 * (1 - t))

                # Expanding ring in front.
                center_x = x + facing * 20
                center_y = y + 25

                for ring_r in range(r, max(1, r - 8), -2):
                    ring_alpha = _NS_solara._alpha(alpha * (r - abs(ring_r - r + 4)) / r)
                    pygame.draw.ellipse(surface,
                                        (*_NS_solara.PALETTE["solar_light"], ring_alpha),
                                        (center_x - ring_r, center_y - ring_r // 3,
                                         ring_r * 2, ring_r * 2 // 3), 2)

                # Radial sparks.
                for j in range(12):
                    angle_s = j * math.pi / 6
                    sx = center_x + int(math.cos(angle_s) * r)
                    sy = center_y + int(math.sin(angle_s) * r * 0.5)
                    pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_shine"], alpha),
                                     (sx, sy, 1, 1))

                # Rising columns of fire.
                if i == 2:  # Only for third biggest swing
                    for j in range(6):
                        col_angle = j * math.pi / 3 + phase * 0.2
                        col_r = int(r * 0.6)
                        col_x = center_x + int(math.cos(col_angle) * col_r)
                        col_y_base = center_y + int(math.sin(col_angle) * col_r * 0.5)
                        for layer in range(4):
                            layer_y = col_y_base - int(layer * 6 + t * 15)
                            layer_alpha = _NS_solara._alpha(200 * (1 - layer * 0.2) * (1 - t))
                            pygame.draw.ellipse(surface,
                                                (*_NS_solara.PALETTE["solar_mid"],
                                                 layer_alpha),
                                                (col_x - 3, layer_y - 2, 6, 4))
                            pygame.draw.rect(surface,
                                             (*_NS_solara.PALETTE["solar_hot"],
                                              layer_alpha),
                                             (col_x, layer_y, 1, 1))

    # ============================================================
    # SKILL W: CELESTIAL HAMMER (throw hammer projectile)
    # ============================================================
    def _draw_celestialhammer_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_solara._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 10

        if progress < 0.5:
            # Hammer flying to target.
            t = progress / 0.5
            hx = int(start_x + (tx - start_x) * t)
            hy = int(start_y + (ty - start_y) * t)
            spin = phase * 4  # spin animation

            # Draw spinning hammer.
            _NS_solara._draw_flying_hammer(surface, hx, hy, spin, phase)

            # Trail behind.
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                tx_pos = int(start_x + (tx - start_x) * trail_t)
                ty_pos = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_solara._alpha(200 - i * 22)
                size = max(1, 6 - i)
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_darkest"], alpha),
                                      (tx_pos, ty_pos), size)
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_dark"], alpha),
                                      (tx_pos, ty_pos), max(1, size - 1))
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_mid"], alpha),
                                      (tx_pos, ty_pos), max(1, size - 2))
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                      (tx_pos, ty_pos), max(1, size - 3))

        else:
            # Hammer returning (recall).
            t = (progress - 0.5) / 0.5
            hx = int(tx + (start_x - tx) * t)
            hy = int(ty + (start_y - ty) * t)
            spin = phase * 4

            _NS_solara._draw_flying_hammer(surface, hx, hy, spin, phase)

            # Return trail.
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                tx_pos = int(tx + (start_x - tx) * trail_t)
                ty_pos = int(ty + (start_y - ty) * trail_t)
                alpha = _NS_solara._alpha(200 - i * 22)
                size = max(1, 6 - i)
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_dark"], alpha),
                                      (tx_pos, ty_pos), size)
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                      (tx_pos, ty_pos), max(1, size - 2))

    def _draw_flying_hammer(surface, hx, hy, spin, phase):
        """Small spinning hammer projectile."""
        # Rotating hammer head.
        cos_s = math.cos(spin)
        sin_s = math.sin(spin)

        # Shaft.
        shaft_len = 6
        shaft_end_x = hx + int(cos_s * shaft_len)
        shaft_end_y = hy + int(sin_s * shaft_len)
        shaft_start_x = hx - int(cos_s * 3)
        shaft_start_y = hy - int(sin_s * 3)

        pygame.draw.line(surface, _NS_solara.PALETTE["hammer_dark"],
                         (shaft_start_x, shaft_start_y),
                         (shaft_end_x, shaft_end_y), 2)
        pygame.draw.line(surface, _NS_solara.PALETTE["hammer_mid"],
                         (shaft_start_x, shaft_start_y),
                         (shaft_end_x, shaft_end_y), 1)

        # Hammer head (perpendicular).
        perp_x = -sin_s * 4
        perp_y = cos_s * 4
        head_a = (shaft_end_x + int(perp_x), shaft_end_y + int(perp_y))
        head_b = (shaft_end_x - int(perp_x), shaft_end_y - int(perp_y))

        pygame.draw.line(surface, _NS_solara.PALETTE["armor_darkest"],
                         head_a, head_b, 5)
        pygame.draw.line(surface, _NS_solara.PALETTE["armor_dark"],
                         head_a, head_b, 3)
        pygame.draw.line(surface, _NS_solara.PALETTE["armor_mid"],
                         head_a, head_b, 1)

        # Glow around hammer.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(10, 2, -1):
            alpha = _NS_solara._alpha(100 * pulse * (10 - r) / 10)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                  (hx, hy), r)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_hot"], (hx, hy), 2)
        pygame.draw.rect(surface, _NS_solara.PALETTE["solar_shine"], (hx, hy, 1, 1))

    # ============================================================
    # SKILL E: LUMINOSITY (healing pulse aura)
    # ============================================================
    def _draw_luminosity_ground(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Expanding healing rings.
        for i in range(2):
            r = int(20 + i * 15 + progress * 40)
            alpha = _NS_solara._alpha(200 - i * 60 - int(progress * 100))
            if alpha > 0:
                pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_shine"], alpha),
                                    (x - r + 2, y + 40 - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)

    def _draw_luminosity_foreground(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Bright golden aura around boss.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        # Halo above head.
        halo_y = y - 30
        halo_r = 12 + int(math.sin(phase * 2) * 2)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_hot"],
                              (x, halo_y), halo_r, 2)
        _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_shine"],
                              (x, halo_y), halo_r - 1, 1)

        # Cross/plus healing symbols floating around boss.
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            r = 40 + int(math.sin(phase * 2 + i) * 5)
            hx = x + int(math.cos(angle) * r)
            hy = y + int(math.sin(angle) * r * 0.5)
            alpha = _NS_solara._alpha(220)

            # Plus sign.
            pygame.draw.line(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                             (hx - 2, hy), (hx + 2, hy), 1)
            pygame.draw.line(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                             (hx, hy - 2), (hx, hy + 2), 1)
            pygame.draw.rect(surface, _NS_solara.PALETTE["solar_shine"], (hx, hy, 1, 1))

        # Rising light particles.
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            px = x - 30 + i * 6 + int(math.sin(phase + i) * 3)
            py = y + 20 - int(t * 40)
            alpha = _NS_solara._alpha(230 * (1 - t) * pulse)
            if alpha > 0:
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                      (px, py), 2)
                pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_shine"], alpha),
                                 (px, py, 1, 1))

    # ============================================================
    # SKILL R: SOLAR GUARDIAN (dive + sanctified dome)
    # ============================================================
    def _draw_solarguardian_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_solara._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Wind-up: target circle grows.
            t = progress / 0.5
            r = int(35 * t)
            alpha = _NS_solara._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)

            # Runes around target.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_solara.PALETTE["solar_light"],
                                 (sx, sy, 2, 2))
        else:
            # Sanctified area.
            t = (progress - 0.5) / 0.5
            r = 40
            alpha = _NS_solara._alpha(180 * (1 - t * 0.3))
            pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_solarguardian_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_solara._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Boss channeling in air (light gathering).
            t = progress / 0.5
            # Beam from boss going up.
            beam_top = y - 60 - int(t * 30)
            for w, alpha in [(6, 60), (4, 120), (2, 200), (1, 255)]:
                pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_light"],
                                            _NS_solara._alpha(alpha * t)),
                                 (x - w // 2, beam_top, w, y - beam_top - 20))

            # Light sphere above.
            gather_y = beam_top
            gather_r = int(4 + t * 8)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_solara._alpha(200 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_light"], alpha),
                                      (x, gather_y), r)
            _NS_solara._aacircle(surface, _NS_solara.PALETTE["solar_shine"],
                                  (x, gather_y), gather_r - 2)
        elif progress < 0.65:
            # STRIKE PHASE: massive beam crashes to target.
            t = (progress - 0.5) / 0.15
            intensity = math.sin(t * math.pi)

            # Beam from sky.
            beam_top_y = max(0, ty - 250)
            for layer_i, (width, alpha_val) in enumerate([
                (16, 100), (12, 140), (8, 180), (4, 220), (2, 255),
            ]):
                actual_alpha = _NS_solara._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_solara.PALETTE["solar_darkest"],
                    _NS_solara.PALETTE["solar_dark"],
                    _NS_solara.PALETTE["solar_mid"],
                    _NS_solara.PALETTE["solar_light"],
                    _NS_solara.PALETTE["solar_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, beam_top_y,
                                  width, ty - beam_top_y))

            # Impact explosion.
            impact_r = int(20 + t * 30)
            impact_alpha = _NS_solara._alpha(240 * intensity)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_darkest"], impact_alpha),
                                  (tx, ty), impact_r + 4, 3)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_dark"], impact_alpha),
                                  (tx, ty), impact_r, 3)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_mid"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 6), 2)
            _NS_solara._aacircle(surface, (*_NS_solara.PALETTE["solar_hot"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 12), 1)

            # Radial burst.
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_solara.PALETTE["solar_light"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)

    def _draw_solarguardian_dome(surface, boss, x, y, timer, phase):
        """Protective dome after impact."""
        tx, ty = _NS_solara._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.65:
            return

        # Dome appears after impact.
        t = (progress - 0.65) / 0.35
        r = 45
        breath = math.sin(phase * 2) * 2

        dome_surf = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Dome hemisphere (upper half).
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            pygame.draw.ellipse(dome_surf, (*_NS_solara.PALETTE["solar_hot"], alpha_val),
                                (10, 10 + int(breath),
                                 r * 2, r * 2 - int(breath) * 2), thickness)
            pygame.draw.ellipse(dome_surf, (*_NS_solara.PALETTE["solar_shine"], alpha_val),
                                (11, 11 + int(breath),
                                 r * 2 - 2, r * 2 - 2 - int(breath) * 2), 1)

        # Sparkles on dome.
        for i in range(16):
            angle = phase * 1.2 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r * 0.7) - r // 3
            pygame.draw.rect(dome_surf, _NS_solara.PALETTE["solar_shine"], (sx, sy, 2, 2))
            pygame.draw.rect(dome_surf, _NS_solara.PALETTE["white"], (sx, sy, 1, 1))

        surface.blit(dome_surf, (tx - r - 10, ty - r - 10))

        # Rising particles inside.
        for i in range(8):
            p_t = (phase * 0.6 + i * 0.12) % 1.0
            px = tx - 20 + i * 5 + int(math.sin(phase + i) * 3)
            py = ty + 10 - int(p_t * 30)
            alpha = _NS_solara._alpha(200 * (1 - p_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_hot"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_solara.PALETTE["solar_shine"], alpha),
                                 (px, py, 1, 1))


# ====================================================================
# pyraethis.py
# ====================================================================



class _NS_pyraethis:
    """Namespace pyraethis - Eternal Firebird TRUE BOSS (RANGED)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        "feather_darkest": (40, 10, 5),
        "feather_dark": (110, 30, 10),
        "feather_mid": (200, 70, 15),
        "feather_light": (255, 140, 30),
        "feather_bright": (255, 200, 70),
        "feather_shine": (255, 245, 160),

        "belly_dark": (120, 60, 10),
        "belly_mid": (220, 145, 30),
        "belly_light": (255, 220, 90),
        "belly_shine": (255, 250, 200),

        "core_darkest": (30, 5, 0),
        "core_dark": (100, 25, 5),
        "core_mid": (200, 60, 10),
        "core_light": (255, 120, 25),

        "flame_darkest": (60, 20, 0),
        "flame_dark": (170, 60, 5),
        "flame_mid": (240, 130, 20),
        "flame_light": (255, 200, 60),
        "flame_hot": (255, 240, 130),
        "flame_shine": (255, 253, 220),

        "eye_socket": (10, 3, 0),
        "eye_dark": (100, 20, 5),
        "eye_mid": (240, 80, 20),
        "eye_light": (255, 200, 80),
        "eye_glow": (255, 250, 180),

        "beak_dark": (60, 35, 10),
        "beak_mid": (140, 90, 30),
        "beak_light": (220, 170, 70),

        "claw_dark": (30, 15, 5),
        "claw_mid": (80, 45, 15),
        "claw_light": (150, 100, 40),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 1, 0),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_pyraethis._clamp(color)
        if _NS_pyraethis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_pyraethis._clamp(color)
        if _NS_pyraethis.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_pyraethis._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_pyraethis._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 250 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_pyraethis(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_pyraethis._update_phx_attack_anim(boss)
        attacking = (
            getattr(boss, "_phx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        supernova = active_skill == "r"

        _NS_pyraethis._draw_fire_aura(surface, x, y, pulse)
        _NS_pyraethis._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        if active_skill == "q":
            _NS_pyraethis._draw_icarusdive_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_pyraethis._draw_sunray_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_pyraethis._draw_supernova_ground(surface, boss, x, y, skill_timer, pulse)

        if supernova:
            _NS_pyraethis._draw_supernova_egg(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_pyraethis._draw_phx_attack(surface, boss, x, y)
        else:
            _NS_pyraethis._draw_phx_idle(surface, boss, x, y)

        if active_skill == "w":
            _NS_pyraethis._draw_firespirits(surface, boss, x, y, skill_timer, pulse)

        if active_skill == "q":
            _NS_pyraethis._draw_icarusdive_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_pyraethis._draw_sunray_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_pyraethis._draw_supernova_foreground(surface, boss, x, y, skill_timer, pulse)

    def _update_phx_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_phx_previous_timer", 0))
        active = bool(getattr(boss, "_phx_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._phx_attack_active = True
            boss._phx_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._phx_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._phx_attack_frame = int(
                getattr(boss, "_phx_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._phx_attack_active = False
            boss._phx_attack_frame = 0
            active = False

        boss._phx_previous_timer = timer
        boss._phx_attack_progress = (
            min(1.0, getattr(boss, "_phx_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_phx_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 6)
        _NS_pyraethis._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_pyraethis._draw_fire_wisps(surface, x, y + 45, boss.pulse)
        _NS_pyraethis._draw_phx_body(surface, x, y + bob, boss.direction,
                                       boss.pulse, "idle")

    def _draw_phx_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_phx_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_phx_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.7) * 6)
        if progress < 0.35:
            t = progress / 0.35
            lean = int(t * -3) * facing
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 10)) * facing
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(7 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_pyraethis._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_pyraethis._draw_fire_wisps(surface, x + lean, y + 45, boss.pulse, intense=True)
        _NS_pyraethis._draw_phx_body(surface, x + lean, y + bob - lift,
                                       facing, boss.pulse, "attack",
                                       progress)
        _NS_pyraethis._draw_fireball_projectile(surface, boss, x + lean,
                                                  y + bob - lift, progress)

    # ============================================================
    # PHOENIX BODY - REDESIGNED
    # ============================================================
    def _draw_phx_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw order: back wing → tail → body → belly → front wing → head → legs."""
        if action == "attack":
            flap_phase = phase * 2 + attack_progress * 3
        else:
            flap_phase = phase * 1.5

        # BACK wing (further from viewer, drawn first).
        _NS_pyraethis._draw_single_wing(surface, cx, cy - 4, facing, flap_phase,
                                          side=-1, scale=0.9)

        # Fire tail (behind body).
        _NS_pyraethis._draw_fire_tail(surface, cx, cy + 4, facing, phase)

        # Main body.
        _NS_pyraethis._draw_phoenix_body(surface, cx, cy, facing, phase)

        # Legs peeking below.
        _NS_pyraethis._draw_phoenix_legs(surface, cx, cy + 8, facing, phase)

        # FRONT wing (closer to viewer).
        _NS_pyraethis._draw_single_wing(surface, cx, cy - 4, facing, flap_phase,
                                          side=1, scale=1.0)

        # Head with beak.
        beak_lunge = 0
        if action == "attack":
            if attack_progress < 0.35:
                beak_lunge = -int(attack_progress / 0.35 * 3) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                beak_lunge = int((-3 + t * 10)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                beak_lunge = int(7 * (1 - t)) * facing

        _NS_pyraethis._draw_phoenix_head(surface, cx + facing * 4 + beak_lunge,
                                          cy - 10, facing, phase, action)

    def _draw_single_wing(surface, cx, cy, facing, flap_phase, side, scale):
        """Draw ONE wing - side=-1 is back, side=+1 is front.
        Wing extends UP and OUTWARD."""
        flap = math.sin(flap_phase) * 3

        # Wing base at shoulder.
        base_x = cx + side * 4
        base_y = cy

        # Wing extends outward (side direction) and up.
        # Main wing tip position.
        wing_span = int(28 * scale)
        wing_height = int(22 * scale) + int(flap * 2)

        tip_x = base_x + side * wing_span
        tip_y = base_y - wing_height

        # Middle wing point (creates arc).
        mid_x = base_x + side * (wing_span // 2)
        mid_y = base_y - wing_height - 3

        # Bottom back wing corner.
        back_x = base_x + side * (wing_span // 2 - 4)
        back_y = base_y + 8

        # Wing shape as ONE polygon (like a curved feather fan).
        wing_pts = [
            (base_x, base_y - 2),
            (base_x + side * 3, base_y - 6),
            (mid_x - side * 2, mid_y),
            (tip_x, tip_y),
            (tip_x + side * 2, tip_y + 4),
            (tip_x, tip_y + 8),
            (mid_x, mid_y + 8),
            (back_x, back_y),
            (base_x, base_y + 4),
        ]

        # Shadow.
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in wing_pts])

        # Base wing color.
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_darkest"], wing_pts)

        # Second layer (smaller).
        inner_pts = [
            (base_x + side * 1, base_y - 2),
            (base_x + side * 3, base_y - 5),
            (mid_x - side * 1, mid_y + 1),
            (int(tip_x - side * 2), tip_y + 2),
            (int(tip_x - side * 1), tip_y + 6),
            (mid_x, mid_y + 6),
            (back_x + side * 2, back_y - 2),
            (base_x + side * 2, base_y + 2),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_dark"], inner_pts)

        # Third layer (mid orange, upper section).
        upper_pts = [
            (base_x + side * 2, base_y - 4),
            (mid_x, mid_y + 2),
            (tip_x - side * 2, tip_y + 4),
            (mid_x + side * 1, mid_y + 4),
            (base_x + side * 3, base_y),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_mid"], upper_pts)

        # Bright streak (light orange along top edge).
        light_pts = [
            (base_x + side * 3, base_y - 3),
            (mid_x, mid_y + 1),
            (tip_x - side * 3, tip_y + 3),
            (mid_x + side * 2, mid_y + 3),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_light"], light_pts)

        # Feather separation lines (radiating from base to tips).
        num_feathers = 5
        for i in range(num_feathers):
            t = i / (num_feathers - 1)
            # Feather tip position (along wing edge).
            ftx = int(base_x + (tip_x - base_x) * t)
            fty = int(base_y + (tip_y - base_y) * t)
            # Adjust for arc.
            if t > 0 and t < 1:
                fty -= int(math.sin(t * math.pi) * 4)

            # Line from base to feather tip.
            pygame.draw.line(surface, _NS_pyraethis.PALETTE["feather_darkest"],
                             (base_x + side * 2, base_y - 1),
                             (ftx, fty), 1)

            # Bright hot feather tips.
            if i > 0:
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["feather_bright"],
                                 (ftx - 1, fty - 1, 2, 2))
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"],
                                 (ftx, fty, 1, 1))
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_shine"],
                                 (ftx, fty, 1, 1))

        # Trailing embers from wing tip.
        for e in range(3):
            ember_t = (flap_phase * 0.5 + e * 0.3) % 1.0
            ex = tip_x + int(math.sin(flap_phase + e) * 3)
            ey = tip_y + int(ember_t * 8)
            alpha = _NS_pyraethis._alpha(200 * (1 - ember_t))
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_pyraethis.PALETTE["flame_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_fire_tail(surface, cx, cy, facing, phase):
        """Long trailing fire tail flowing DOWN behind."""
        base_x = cx
        base_y = cy + 2

        # Just 3 main streaks (not 5) for cleaner look.
        # All go straight DOWN with slight fan.
        for i in range(3):
            spread = (i - 1) * 5  # -5, 0, 5
            tail_len = 26 + int(math.sin(phase + i) * 3)

            # Points along tail (S-curve).
            points = [(base_x + spread, base_y)]
            for step in range(1, 5):
                t = step / 4
                # Straight down with slight sway.
                tx = base_x + spread + int(math.sin(phase * 1.5 + t * 2 + i) * 3)
                ty = base_y + int(t * tail_len)
                points.append((tx, ty))

            # Draw tapered flame.
            for j in range(len(points) - 1):
                thickness = max(2, 6 - j * 2)

                _NS_pyraethis._aaline(surface,
                                       _NS_pyraethis.PALETTE["shadow_deep"],
                                       (points[j][0] + 1, points[j][1] + 1),
                                       (points[j + 1][0] + 1, points[j + 1][1] + 1),
                                       thickness + 1)
                _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["feather_darkest"],
                                       points[j], points[j + 1], thickness)
                _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["feather_dark"],
                                       points[j], points[j + 1], max(1, thickness - 1))
                _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["feather_mid"],
                                       points[j], points[j + 1], max(1, thickness - 2))
                if thickness > 3:
                    _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["feather_light"],
                                           points[j], points[j + 1], max(1, thickness - 3))

            # Bright hot tip.
            end = points[-1]
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["feather_bright"], end, 2)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_hot"], end, 1)
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_shine"],
                             (end[0], end[1], 1, 1))

            # Rising embers from tail tip.
            for e in range(2):
                ember_t = (phase * 0.8 + i * 0.2 + e * 0.4) % 1.0
                ex = end[0] + int(math.sin(phase + i + e) * 3)
                ey = end[1] + int(ember_t * 10)
                alpha = _NS_pyraethis._alpha(200 * (1 - ember_t))
                if alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                     (ex, ey, 1, 1))

    def _draw_phoenix_body(surface, cx, cy, facing, phase):
        """Round chest body (facing 3/4 view)."""
        breath = math.sin(phase * 0.8) * 1

        # Main body oval - a bit chubby.
        body_pts = [
            (cx - 8, cy),
            (cx - 9, cy - 4),
            (cx - 6, cy - 8),
            (cx - 1, cy - 10),
            (cx + 4, cy - 10),
            (cx + 8, cy - 8),
            (cx + 10, cy - 4),
            (cx + 9, cy),
            (cx + 7, cy + 5),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
            (cx - 7, cy + 5),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in body_pts])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["core_darkest"], body_pts)

        # Upper back (dark red-orange).
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_dark"], [
            (cx - 8, cy - 2),
            (cx - 6, cy - 7),
            (cx - 1, cy - 9),
            (cx + 4, cy - 9),
            (cx + 7, cy - 7),
            (cx + 9, cy - 2),
            (cx + 7, cy + 1),
            (cx - 7, cy + 1),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_mid"], [
            (cx - 6, cy - 4),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 6, cy - 4),
            (cx + 5, cy - 1),
            (cx - 5, cy - 1),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_light"], [
            (cx - 3, cy - 5),
            (cx + 2, cy - 6),
            (cx + 4, cy - 4),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])

        # Chest belly (bright gold).
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["belly_dark"], [
            (cx - 7, cy + 1),
            (cx + 7, cy + 1),
            (cx + 8, cy + 3),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
            (cx - 8, cy + 3),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["belly_mid"], [
            (cx - 6, cy + 2),
            (cx + 6, cy + 2),
            (cx + 6, cy + 4),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
            (cx - 6, cy + 4),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["belly_light"], [
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ])
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["belly_shine"],
                         (cx - 1, cy + 3, 2, 2))

        # Feather chevrons on chest.
        for row in range(2):
            y_row = cy + 2 + row * 2
            for dx in (-3, 0, 3):
                pygame.draw.line(surface, _NS_pyraethis.PALETTE["belly_dark"],
                                 (cx + dx - 1, y_row),
                                 (cx + dx, y_row + 1), 1)
                pygame.draw.line(surface, _NS_pyraethis.PALETTE["belly_dark"],
                                 (cx + dx, y_row + 1),
                                 (cx + dx + 1, y_row), 1)

        # Glowing chest core.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(5, 1, -1):
            alpha = _NS_pyraethis._alpha(100 * pulse * (5 - r) / 5)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                     (cx, cy + 4), r)

    def _draw_phoenix_legs(surface, cx, cy, facing, phase):
        """Small folded legs with talons."""
        for side in (-1, 1):
            leg_x = cx + side * 2
            top_y = cy - 2
            bot_y = cy + 4

            _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                                   (leg_x + 1, top_y + 1), (leg_x + 1, bot_y + 1), 3)
            _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["claw_dark"],
                                   (leg_x, top_y), (leg_x, bot_y), 2)
            _NS_pyraethis._aaline(surface, _NS_pyraethis.PALETTE["claw_mid"],
                                   (leg_x, top_y), (leg_x, bot_y), 1)

            # Talons (3 small).
            for talon_off in (-2, 0, 2):
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["claw_dark"],
                                 (leg_x + talon_off, bot_y, 1, 2))
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["claw_mid"],
                                 (leg_x + talon_off, bot_y - 1, 1, 1))

    def _draw_phoenix_head(surface, cx, cy, facing, phase, action):
        """Phoenix head with crest, beak, glowing eye."""
        # Head shape (round with pointed beak).
        head_pts = [
            (cx - 5 * facing, cy + 3),
            (cx - 6 * facing, cy),
            (cx - 5 * facing, cy - 4),
            (cx - 2 * facing, cy - 6),
            (cx + 2 * facing, cy - 6),
            (cx + 5 * facing, cy - 4),
            (cx + 6 * facing, cy - 1),
            (cx + 5 * facing, cy + 2),
            (cx + 2 * facing, cy + 4),
            (cx - 3 * facing, cy + 4),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_darkest"], head_pts)

        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_dark"], [
            (cx - 4 * facing, cy + 2),
            (cx - 5 * facing, cy),
            (cx - 4 * facing, cy - 3),
            (cx - 1 * facing, cy - 5),
            (cx + 3 * facing, cy - 5),
            (cx + 5 * facing, cy - 3),
            (cx + 5 * facing, cy + 1),
            (cx + 2 * facing, cy + 3),
            (cx - 3 * facing, cy + 3),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_mid"], [
            (cx - 3 * facing, cy + 1),
            (cx - 3 * facing, cy - 2),
            (cx, cy - 4),
            (cx + 3 * facing, cy - 3),
            (cx + 4 * facing, cy - 1),
            (cx + 3 * facing, cy + 1),
            (cx, cy + 2),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_light"], [
            (cx - 1 * facing, cy - 2),
            (cx + 2 * facing, cy - 3),
            (cx + 3 * facing, cy - 1),
            (cx + 1 * facing, cy),
            (cx - 1 * facing, cy),
        ])

        # CREST on top of head.
        _NS_pyraethis._draw_head_crest(surface, cx, cy - 5, facing, phase)

        # BEAK.
        _NS_pyraethis._draw_phoenix_beak(surface, cx, cy, facing, phase, action)

        # EYE.
        _NS_pyraethis._draw_phoenix_eye(surface, cx + 1 * facing, cy - 2, facing, phase)

    def _draw_head_crest(surface, cx, cy, facing, phase):
        """3 fire feather spikes on top of head, angled BACK (opposite to facing)."""
        beat = math.sin(phase * 1.2) * 1

        # Feathers angle back and up.
        # angle_dx negative = back (against facing direction)
        for i, (angle_dx, angle_dy, length) in enumerate([
            (-1, -3, 6),   # back short
            (-0.5, -4, 8), # middle taller
            (0.5, -3, 7),  # forward slight
        ]):
            base_x = cx + int(i - 1)
            base_y = cy

            tip_x = base_x + int(angle_dx * facing * length * 0.5)
            tip_y = base_y + int(angle_dy) - int(beat)

            # Widen at base.
            pa_x = base_x - 1
            pa_y = base_y + 1
            pb_x = base_x + 1
            pb_y = base_y + 1

            _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_darkest"],
                                 [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_dark"], [
                (tip_x, tip_y),
                ((tip_x + pa_x) // 2, (tip_y + pa_y) // 2),
                ((tip_x + pb_x) // 2, (tip_y + pb_y) // 2),
            ])
            _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["feather_mid"], [
                (tip_x, tip_y),
                (tip_x, base_y),
                (base_x, base_y),
            ])
            # Bright tip.
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["feather_bright"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"],
                             (tip_x, tip_y - 1, 1, 1))

    def _draw_phoenix_beak(surface, cx, cy, facing, phase, action):
        """Sharp gold beak."""
        beak_open = 0
        if action == "attack":
            beak_open = 1

        # Upper beak.
        upper_pts = [
            (cx + 4 * facing, cy - 2),
            (cx + 8 * facing, cy),
            (cx + 4 * facing, cy + 1),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in upper_pts])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["beak_dark"], upper_pts)
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["beak_mid"], [
            (cx + 4 * facing, cy - 1),
            (cx + 7 * facing, cy),
            (cx + 4 * facing, cy),
        ])
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["beak_light"],
                         (cx + 5 * facing, cy - 1, 1, 1))

        # Lower beak.
        lower_offset = beak_open
        lower_pts = [
            (cx + 4 * facing, cy + 1),
            (cx + 7 * facing, cy + 2 + lower_offset),
            (cx + 4 * facing, cy + 3 + lower_offset),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in lower_pts])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["beak_dark"], lower_pts)

        # Mouth glow.
        if beak_open > 0:
            for r in range(3, 0, -1):
                alpha = _NS_pyraethis._alpha(180 * (3 - r) / 3)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                         (cx + 5 * facing, cy + 1), r)
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_shine"],
                             (cx + 5 * facing, cy + 1, 1, 1))

    def _draw_phoenix_eye(surface, cx, cy, facing, phase):
        """Fierce glowing eye."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 3, 3))
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["eye_socket"],
                         (cx, cy - 1, 2, 2))

        for r in range(4, 0, -1):
            alpha = _NS_pyraethis._alpha(140 * pulse * (4 - r) / 4)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["eye_mid"], alpha),
                                     (cx, cy), r)

        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["eye_dark"], (cx, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["eye_mid"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["eye_light"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["eye_glow"], (cx, cy, 1, 1))

    # ============================================================
    # SUPERNOVA EGG
    # ============================================================
    def _draw_supernova_egg(surface, boss, x, y, timer, phase):
        cx = x
        cy = y

        bob = int(math.sin(phase * 0.7) * 3)
        cy += bob

        _NS_pyraethis._draw_floating_shadow(surface, x, y + 55, phase)

        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(50, 5, -3):
            alpha = _NS_pyraethis._alpha(90 * pulse * (50 - r) / 50)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                     (cx, cy), r)
        for r in range(30, 5, -2):
            alpha = _NS_pyraethis._alpha(140 * pulse * (30 - r) / 30)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                     (cx, cy), r)

        egg_pts = [
            (cx, cy - 22),
            (cx - 8, cy - 16),
            (cx - 12, cy - 6),
            (cx - 13, cy + 4),
            (cx - 10, cy + 14),
            (cx - 4, cy + 20),
            (cx + 4, cy + 20),
            (cx + 10, cy + 14),
            (cx + 13, cy + 4),
            (cx + 12, cy - 6),
            (cx + 8, cy - 16),
        ]
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 3) for p in egg_pts])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["core_darkest"], egg_pts)

        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["core_dark"], [
            (cx, cy - 21),
            (cx - 7, cy - 15),
            (cx - 11, cy - 5),
            (cx - 12, cy + 4),
            (cx - 9, cy + 13),
            (cx - 3, cy + 19),
            (cx + 3, cy + 19),
            (cx + 9, cy + 13),
            (cx + 12, cy + 4),
            (cx + 11, cy - 5),
            (cx + 7, cy - 15),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["core_mid"], [
            (cx, cy - 18),
            (cx - 6, cy - 12),
            (cx - 9, cy - 3),
            (cx - 10, cy + 4),
            (cx - 8, cy + 10),
            (cx - 3, cy + 15),
            (cx + 3, cy + 15),
            (cx + 8, cy + 10),
            (cx + 10, cy + 4),
            (cx + 9, cy - 3),
            (cx + 6, cy - 12),
        ])
        _NS_pyraethis._poly(surface, _NS_pyraethis.PALETTE["core_light"], [
            (cx, cy - 14),
            (cx - 4, cy - 8),
            (cx - 6, cy),
            (cx - 6, cy + 6),
            (cx - 2, cy + 11),
            (cx + 2, cy + 11),
            (cx + 6, cy + 6),
            (cx + 6, cy),
            (cx + 4, cy - 8),
        ])

        crack_pulse = math.sin(phase * 3) * 0.4 + 0.6
        crack_alpha = _NS_pyraethis._alpha(240 * crack_pulse)

        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], crack_alpha),
                         (cx, cy - 18), (cx - 1, cy - 10), 1)
        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_shine"], crack_alpha),
                         (cx - 1, cy - 10), (cx + 1, cy), 1)
        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], crack_alpha),
                         (cx + 1, cy), (cx - 1, cy + 10), 1)
        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], crack_alpha),
                         (cx - 1, cy + 10), (cx, cy + 18), 1)

        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], crack_alpha),
                         (cx - 10, cy - 2), (cx - 4, cy - 1), 1)
        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_shine"], crack_alpha),
                         (cx - 4, cy - 1), (cx + 4, cy + 1), 1)
        pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], crack_alpha),
                         (cx + 4, cy + 1), (cx + 10, cy + 2), 1)

        for r in range(5, 0, -1):
            alpha = _NS_pyraethis._alpha(200 * crack_pulse * (5 - r) / 5)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                     (cx, cy), r)
        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_shine"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["white"], (cx, cy, 1, 1))

        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_light"],
                         (cx - 4, cy - 12, 2, 2))
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"],
                         (cx - 4, cy - 12, 1, 1))

        for i in range(6):
            flame_t = (phase * 0.7 + i * 0.15) % 1.0
            fx = cx - 6 + i * 3 + int(math.sin(phase + i) * 2)
            fy = cy - 22 - int(flame_t * 15)
            alpha = _NS_pyraethis._alpha(220 * (1 - flame_t))
            if alpha > 0:
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                         (fx, fy), 2)
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (fx, fy, 1, 1))

    # ============================================================
    # FIREBALL PROJECTILE
    # ============================================================
    def _draw_fireball_projectile(surface, boss, x, y, progress):
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_pyraethis._target_position(boss, x, y)

        start_x = x + facing * 12
        start_y = y - 10

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_pyraethis._alpha(230 - i * 22)

            size = max(1, 8 - i)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                                     (px, py), size)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                     (px, py), max(1, size - 2))
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                     (px, py), max(1, size - 3))

            if i < 5:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_darkest"], (bx, by), 8)
        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_dark"], (bx, by), 6)
        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_mid"], (bx, by), 4)
        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_light"], (bx, by), 3)
        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_hot"], (bx, by), 2)
        _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_pyraethis.PALETTE["white"], (bx, by, 1, 1))

        for r in range(14, 3, -2):
            alpha = _NS_pyraethis._alpha(90 * (14 - r) / 14)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                     (bx, by), r)

        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 25)
            alpha = _NS_pyraethis._alpha(240 * (1 - st))
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                     (tx, ty), radius, 3)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                     (tx, ty), max(1, radius - 4), 2)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                     (tx, ty), max(1, radius - 10), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_shine"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((160, 30), pygame.SRCALPHA)
        w = int(120 * pulse)
        h = int(14 * pulse)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (80 - w // 2 - radius, 15 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (30, 10, 0, 170),
                            (80 - w // 2, 15 - h // 2, w, h))
        surface.blit(shadow, (x - 80, y - 15))

    def _draw_fire_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 32 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 32)
            alpha = _NS_pyraethis._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                                     (sx, sy), 3)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        for i in range(8):
            ember_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(ember_t * 26)
            alpha = _NS_pyraethis._alpha(240 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_pyraethis._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_pyraethis._aacircle(aura, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                                         (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_pyraethis._alpha((70 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_pyraethis._aacircle(aura, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                         (120, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_pyraethis._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_pyraethis._aacircle(aura, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                         (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))

        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_pyraethis.PALETTE["flame_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_pyraethis.PALETTE["flame_dark"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_pyraethis.PALETTE["flame_mid"], 230),
                            (25, 24, 140, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_pyraethis.PALETTE["core_dark"], 180),
                            (40, 26, 110, 18), 1)

        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 50)
            y1 = 35 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_pyraethis.PALETTE["flame_light"], 230),
                             (x1, y1), (x2, y2), 1)

        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sr = 65
            sx = 95 + int(math.cos(angle) * sr)
            sy = 35 + int(math.sin(angle) * sr * 0.35)
            pygame.draw.line(ring, (*_NS_pyraethis.PALETTE["flame_hot"], 240),
                             (sx - 2, sy), (sx + 2, sy), 1)
            pygame.draw.line(ring, (*_NS_pyraethis.PALETTE["flame_hot"], 240),
                             (sx, sy - 2), (sx, sy + 2), 1)
            pygame.draw.rect(ring, (*_NS_pyraethis.PALETTE["flame_shine"], 240),
                             (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring, (*_NS_pyraethis.PALETTE["flame_hot"],
                                        _NS_pyraethis._alpha(180 * pulse)),
                                (15, 14, 160, 42), 1)
        surface.blit(ring, (x - 95, y - 30))

    # ============================================================
    # SKILL Q: ICARUS DIVE
    # ============================================================
    def _draw_icarusdive_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraethis._target_position(boss, x, y)

        num_points = 15
        for i in range(num_points):
            t = i / num_points
            trail_visible = progress > t * 0.6
            if not trail_visible:
                continue

            arc_x = int(x + (tx - x) * t)
            arc_y_base = int(y + (ty - y) * t)
            arc_y = arc_y_base + 25

            fade = max(0, 1 - (progress - t * 0.6) * 2)
            alpha = _NS_pyraethis._alpha(220 * fade)
            if alpha <= 0:
                continue

            r = int(6 + math.sin(phase * 3 + i) * 2)
            pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                (arc_x - r, arc_y - r // 2, r * 2, r))
            pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                (arc_x - r + 1, arc_y - r // 2 + 1, r * 2 - 2, r - 2))
            pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                             (arc_x, arc_y, 1, 1))

    def _draw_icarusdive_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraethis._target_position(boss, x, y)

        if progress < 0.9:
            t = progress / 0.9
            arc_x = int(x + (tx - x) * t)
            arc_y = int(y + (ty - y) * t)
            arc_lift = int(math.sin(t * math.pi) * -50)
            arc_y += arc_lift

            self_size = 12
            for r in range(self_size + 4, 2, -1):
                alpha = _NS_pyraethis._alpha(120 * (self_size + 4 - r) / (self_size + 4))
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                         (arc_x, arc_y), r)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_darkest"],
                                     (arc_x, arc_y), self_size)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_dark"],
                                     (arc_x, arc_y), self_size - 2)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_mid"],
                                     (arc_x, arc_y), self_size - 4)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_light"],
                                     (arc_x, arc_y), self_size - 6)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_hot"],
                                     (arc_x, arc_y), 2)
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["white"],
                             (arc_x, arc_y, 1, 1))

            wing_span = 8
            wing_flap = math.sin(phase * 3) * 3
            for side in (-1, 1):
                wing_tip_x = arc_x + side * wing_span
                wing_tip_y = arc_y - 4 + int(wing_flap)
                pygame.draw.line(surface, _NS_pyraethis.PALETTE["feather_darkest"],
                                 (arc_x, arc_y - 2),
                                 (wing_tip_x, wing_tip_y), 2)
                pygame.draw.line(surface, _NS_pyraethis.PALETTE["feather_mid"],
                                 (arc_x, arc_y - 2),
                                 (wing_tip_x, wing_tip_y), 1)
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"],
                                 (wing_tip_x, wing_tip_y, 1, 1))

            for i in range(12):
                trail_t = max(0.0, t - i * 0.05)
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t)
                py += int(math.sin(trail_t * math.pi) * -50)
                alpha = _NS_pyraethis._alpha(200 - i * 15)
                size = max(1, 7 - i // 2)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                         (px, py), size)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                         (px, py), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (px, py, 1, 1))
        else:
            t = (progress - 0.9) / 0.1
            radius = int(20 + t * 30)
            alpha = _NS_pyraethis._alpha(240 * (1 - t))
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                                     (tx, ty), radius + 4, 3)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                     (tx, ty), radius, 3)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                     (tx, ty), max(1, radius - 6), 2)
            _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                     (tx, ty), max(1, radius - 15), 1)
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_shine"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: FIRE SPIRITS
    # ============================================================
    def _draw_firespirits(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        orbit_r = 40

        for i in range(3):
            angle = phase * 1.2 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * orbit_r)
            sy = y + int(math.sin(angle) * orbit_r * 0.5) - 5

            spirit_pulse = math.sin(phase * 3 + i) * 0.3 + 0.7

            for r in range(10, 1, -1):
                alpha = _NS_pyraethis._alpha(130 * spirit_pulse * (10 - r) / 10)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                         (sx, sy), r)

            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_darkest"], (sx, sy), 5)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_dark"], (sx, sy), 4)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_mid"], (sx, sy), 3)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_light"], (sx, sy), 2)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_hot"], (sx, sy), 1)
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_shine"], (sx, sy, 1, 1))

            for e in range(3):
                trail_angle = angle - e * 0.2
                tx_ = x + int(math.cos(trail_angle) * orbit_r)
                ty_ = y + int(math.sin(trail_angle) * orbit_r * 0.5) - 5
                alpha = _NS_pyraethis._alpha(200 - e * 60)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                         (tx_, ty_), max(1, 3 - e))
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (tx_, ty_, 1, 1))

            wing_flap = math.sin(phase * 4 + i) * 2
            for side in (-1, 1):
                wtx = sx + side * 4
                wty = sy - 2 + int(wing_flap)
                pygame.draw.line(surface, _NS_pyraethis.PALETTE["feather_dark"],
                                 (sx, sy - 1), (wtx, wty), 1)
                pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"],
                                 (wtx, wty, 1, 1))

    # ============================================================
    # SKILL E: SUN RAY
    # ============================================================
    def _draw_sunray_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_pyraethis._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.2:
            r = int(20 + math.sin(phase * 2) * 3)
            alpha = _NS_pyraethis._alpha(200)
            pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_sunray_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraethis._target_position(boss, x, y)

        start_x = x + facing * 12
        start_y = y - 10

        if progress < 0.2:
            t = progress / 0.2
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_pyraethis._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                         (start_x, start_y), r)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_mid"],
                                     (start_x, start_y), cr - 2)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_hot"],
                                     (start_x, start_y), max(1, cr - 4))
        else:
            t = (progress - 0.2) / 0.8
            intensity_growth = min(1.0, t * 2)

            dx = tx - start_x
            dy = ty - start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx = dx / length
                ny = dy / length
                end_x = int(start_x + nx * (length + 50))
                end_y = int(start_y + ny * (length + 50))
            else:
                end_x = tx + facing * 200
                end_y = ty
                nx, ny = facing, 0

            base_widths = [(20, 80), (16, 130), (12, 170), (8, 210), (4, 250), (2, 255)]
            for layer_i, (base_w, alpha_val) in enumerate(base_widths):
                actual_width = int(base_w * intensity_growth)
                if actual_width < 1:
                    continue
                actual_alpha = _NS_pyraethis._alpha(alpha_val)
                colors = [
                    _NS_pyraethis.PALETTE["flame_darkest"],
                    _NS_pyraethis.PALETTE["flame_dark"],
                    _NS_pyraethis.PALETTE["flame_mid"],
                    _NS_pyraethis.PALETTE["flame_light"],
                    _NS_pyraethis.PALETTE["flame_hot"],
                    _NS_pyraethis.PALETTE["white"],
                ]
                color = colors[min(layer_i, 5)]
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (end_x, end_y), actual_width)

            for i in range(24):
                spark_t = (phase * 3 + i * 0.08) % 1.0
                spark_x = int(start_x + (end_x - start_x) * spark_t)
                spark_y = int(start_y + (end_y - start_y) * spark_t)
                perp_x = -ny * math.sin(phase * 5 + i) * 8
                perp_y = nx * math.sin(phase * 5 + i) * 8
                spark_x += int(perp_x)
                spark_y += int(perp_y)
                alpha = _NS_pyraethis._alpha(240 * intensity_growth)
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["white"], alpha),
                                 (spark_x, spark_y, 1, 1))

            for r in range(14, 2, -1):
                alpha = _NS_pyraethis._alpha(200 * intensity_growth * (14 - r) / 14)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_light"], alpha),
                                         (start_x, start_y), r)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_shine"],
                                     (start_x, start_y), 5)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["white"],
                                     (start_x, start_y), 3)

            impact_r = int(15 + t * 25)
            impact_alpha = _NS_pyraethis._alpha(240 * intensity_growth)
            for r in range(impact_r, 2, -2):
                a = _NS_pyraethis._alpha(impact_alpha * (impact_r - r) / impact_r)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], a),
                                         (tx, ty), r)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_hot"], (tx, ty), 4)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["white"], (tx, ty), 2)

            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_shine"], impact_alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL R: SUPERNOVA
    # ============================================================
    def _draw_supernova_ground(surface, boss, x, y, timer, phase):
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 35 + int(math.sin(phase * 2) * 3)
        alpha = _NS_pyraethis._alpha(220)
        pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], alpha),
                            (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                            (x - r + 3, y + 40 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                            (x - r + 8, y + 40 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 1)

        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            sx = x + int(math.cos(angle) * r)
            sy = y + 40 + int(math.sin(angle) * r * 0.35)
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"], (sx - 1, sy, 3, 1))
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_hot"], (sx, sy - 1, 1, 3))
            pygame.draw.rect(surface, _NS_pyraethis.PALETTE["flame_shine"], (sx, sy, 1, 1))

    def _draw_supernova_foreground(surface, boss, x, y, timer, phase):
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.85:
            t = (progress - 0.85) / 0.15
            radius = int(40 + t * 90)
            alpha = _NS_pyraethis._alpha(255 * (1 - t))

            for r in range(radius, 2, -3):
                a = _NS_pyraethis._alpha(alpha * (radius - r) / radius)
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_darkest"], a),
                                         (x, y), r)
            for r in range(int(radius * 0.8), 2, -3):
                a = _NS_pyraethis._alpha(alpha * (radius * 0.8 - r) / (radius * 0.8))
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], a),
                                         (x, y), r)
            for r in range(int(radius * 0.6), 2, -2):
                a = _NS_pyraethis._alpha(alpha * (radius * 0.6 - r) / (radius * 0.6))
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], a),
                                         (x, y), r)
            for r in range(int(radius * 0.4), 2, -2):
                a = _NS_pyraethis._alpha(alpha * (radius * 0.4 - r) / (radius * 0.4))
                _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_hot"], a),
                                         (x, y), r)
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["flame_shine"],
                                     (x, y), max(1, radius // 4))
            _NS_pyraethis._aacircle(surface, _NS_pyraethis.PALETTE["white"],
                                     (x, y), max(1, radius // 8))

            for i in range(24):
                angle_s = i * math.pi / 12
                ex = x + int(math.cos(angle_s) * radius)
                ey = y + int(math.sin(angle_s) * radius)
                pygame.draw.line(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                 (x, y), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_shine"], alpha),
                                 (ex, ey, 3, 3))
        else:
            for i in range(10):
                t = (phase * 0.6 + i * 0.1) % 1.0
                sx = x - 30 + i * 6 + int(math.sin(phase + i) * 4)
                sy = y - 25 - int(t * 30)
                alpha = _NS_pyraethis._alpha(220 * (1 - t))
                if alpha > 0:
                    _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_dark"], alpha),
                                             (sx, sy), 3)
                    _NS_pyraethis._aacircle(surface, (*_NS_pyraethis.PALETTE["flame_mid"], alpha),
                                             (sx, sy), 2)
                    pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_hot"], alpha),
                                     (sx, sy, 1, 1))
                    pygame.draw.rect(surface, (*_NS_pyraethis.PALETTE["flame_shine"], alpha),
                                     (sx, sy, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_azureth(surface, boss, x, y):
    """Entry point azureth."""
    return _NS_azureth.draw_azureth(surface, boss, x, y)


def draw_luminar(surface, boss, x, y):
    """Entry point luminar."""
    return _NS_luminar.draw_luminar(surface, boss, x, y)


def draw_solara(surface, boss, x, y):
    """Entry point solara."""
    return _NS_solara.draw_solara(surface, boss, x, y)


def draw_pyraethis(surface, boss, x, y):
    """Entry point pyraethis."""
    return _NS_pyraethis.draw_pyraethis(surface, boss, x, y)
