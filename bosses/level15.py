"""
bosses/level15.py - Semua boss Level 15

Berisi:
  - auroth      (mini boss - MELEE celestial bastion tank titan)
  - morvein     (mini boss - MELEE phantom lancer knight)
  - thorvak     (mini boss - MELEE ancient grovewarden treant)
  - yamako      (TRUE BOSS - Primordial Woodshaper, MELEE)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan: state prefix Auroth di-rename _aur_ -> _aro_ supaya tidak
bentrok dengan Aureth'zar (Level 10) & Aurelix (Level 12) saat
jadi hero bersamaan. Nama fungsi namespace (_draw_aur_*) TIDAK
disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# auroth.py
# ====================================================================



class _NS_auroth:
    """Namespace auroth - Celestial Bastion tank titan (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Armor (heavy gold plate)
        "armor_darkest": (25, 15, 5),
        "armor_dark": (75, 50, 15),
        "armor_mid": (160, 115, 30),
        "armor_light": (230, 185, 65),
        "armor_edge": (255, 220, 120),
        "armor_shine": (255, 245, 200),

        # Dark inner armor / plates
        "plate_darkest": (10, 8, 5),
        "plate_dark": (35, 25, 15),
        "plate_mid": (70, 55, 35),

        # Radiant energy (core, aura)
        "rad_darkest": (60, 30, 0),
        "rad_dark": (150, 90, 5),
        "rad_mid": (240, 170, 20),
        "rad_light": (255, 220, 80),
        "rad_hot": (255, 245, 150),
        "rad_shine": (255, 253, 220),

        # Eye glow (menacing yellow-white)
        "eye_socket": (5, 3, 0),
        "eye_dark": (80, 50, 5),
        "eye_mid": (230, 180, 40),
        "eye_light": (255, 235, 130),
        "eye_glow": (255, 255, 230),

        # Rune/glyph highlights
        "rune_dim": (120, 70, 15),
        "rune_bright": (255, 220, 90),

        # Shadow/highlights
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 0),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_auroth._clamp(color)
        if _NS_auroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_auroth._clamp(color)
        if _NS_auroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_auroth._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_auroth._clamp(color), points)

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
        return int(x + 120 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_auroth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_auroth._update_aur_attack_anim(boss)
        attacking = (
            getattr(boss, "_aro_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_auroth._draw_radiant_aura(surface, x, y, pulse)
        _NS_auroth._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_auroth._draw_consecration_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_auroth._draw_ward_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_auroth._draw_guardian_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_auroth._draw_ionicedge_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_auroth._draw_aur_attack(surface, boss, x, y)
        else:
            _NS_auroth._draw_aur_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_auroth._draw_ionicedge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_auroth._draw_ward_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_auroth._draw_consecration_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_auroth._draw_guardian_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_aur_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aro_previous_timer", 0))
        active = bool(getattr(boss, "_aro_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aro_attack_active = True
            boss._aro_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._aro_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._aro_attack_frame = int(
                getattr(boss, "_aro_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._aro_attack_active = False
            boss._aro_attack_frame = 0
            active = False

        boss._aro_previous_timer = timer
        boss._aro_attack_progress = (
            min(1.0, getattr(boss, "_aro_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_aur_idle(surface, boss, x, y):
        # Heavy floating bob (slow).
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_auroth._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_auroth._draw_radiant_wisps(surface, x, y + 45, boss.pulse)
        _NS_auroth._draw_aur_body(surface, x, y + bob, boss.direction,
                                    boss.pulse, "idle")

    def _draw_aur_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_aro_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_aro_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.5) * 4)
        # Big titan arm sweep: wind-up back → forward sweep → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lean = int(t * -3) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 8)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_auroth._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_auroth._draw_radiant_wisps(surface, x + lean, y + 45, boss.pulse, intense=True)
        _NS_auroth._draw_aur_body(surface, x + lean, y + bob - lift,
                                    facing, boss.pulse, "attack",
                                    progress)
        _NS_auroth._draw_swing_arc(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (bulky titan armored knight)
    # ============================================================
    def _draw_aur_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Massive legs/lower body (floating - no visible feet).
        _NS_auroth._draw_titan_legs(surface, cx, cy + 12, facing, phase)

        # Torso (broad chest).
        _NS_auroth._draw_titan_torso(surface, cx, cy, facing, phase)

        # Back arm (secondary, non-swing).
        _NS_auroth._draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress)

        # Head with horned helm.
        _NS_auroth._draw_titan_head(surface, cx, cy - 20, facing, phase)

        # Front arm (swing arm) - drawn last so overlaps.
        _NS_auroth._draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress)

    def _draw_titan_legs(surface, cx, cy, facing, phase):
        """Large bulky armored legs/skirt tapered wider at bottom."""
        sway = math.sin(phase * 0.4) * 1

        # Wide armored skirt / thigh armor.
        skirt_pts = [
            (cx - 12, cy - 6),
            (cx + 12, cy - 6),
            (cx + 15, cy + 4),
            (cx + 13, cy + 12),
            (cx + 8, cy + 18),
            (cx - 8, cy + 18),
            (cx - 13, cy + 12),
            (cx - 15, cy + 4),
        ]
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 3) for p in skirt_pts])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], skirt_pts)

        # Main plate color.
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
            (cx - 11, cy - 5),
            (cx + 11, cy - 5),
            (cx + 14, cy + 4),
            (cx + 12, cy + 11),
            (cx + 7, cy + 17),
            (cx - 7, cy + 17),
            (cx - 12, cy + 11),
            (cx - 14, cy + 4),
        ])

        # Mid highlight.
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_mid"], [
            (cx - 9, cy - 3),
            (cx + 9, cy - 3),
            (cx + 12, cy + 3),
            (cx + 10, cy + 10),
            (cx + 5, cy + 15),
            (cx - 5, cy + 15),
            (cx - 10, cy + 10),
            (cx - 12, cy + 3),
        ])

        # Vertical plate divisions.
        for x_off in (-8, -3, 3, 8):
            pygame.draw.line(surface, _NS_auroth.PALETTE["armor_darkest"],
                             (cx + x_off, cy - 4),
                             (cx + int(x_off * 1.3), cy + 15), 1)
            pygame.draw.line(surface, _NS_auroth.PALETTE["armor_edge"],
                             (cx + x_off + 1, cy - 4),
                             (cx + int(x_off * 1.3) + 1, cy + 15), 1)

        # Central emblem (radiant symbol).
        emblem_y = cy + 5
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["plate_darkest"],
                              (cx, emblem_y), 4)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_darkest"],
                              (cx, emblem_y), 3)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_dark"],
                              (cx, emblem_y), 2)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_mid"],
                              (cx, emblem_y), 1)

        # Radiant glow around emblem.
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(6, 1, -1):
            alpha = _NS_auroth._alpha(80 * pulse * (6 - r) / 6)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                   (cx, emblem_y), r)

        # Highlight edges.
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                         (cx - 10, cy - 4, 20, 1))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_shine"],
                         (cx - 4, cy - 4, 8, 1))

        # BOTTOM: energy trailing wisps (no feet - floating).
        _NS_auroth._draw_leg_energy_wisps(surface, cx, cy + 18, phase)

    def _draw_leg_energy_wisps(surface, cx, cy, phase):
        """Energy trailing from bottom of skirt (floating effect)."""
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 8 + i * 4 + int(math.sin(phase + i) * 2)
            wy = cy + int(wisp_t * 8)
            alpha = _NS_auroth._alpha(220 * (1 - wisp_t))
            if alpha <= 0:
                continue
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_dark"], alpha),
                                   (wx, wy), 2)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                   (wx, wy), 1)
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], alpha),
                             (wx, wy, 1, 1))

    def _draw_titan_torso(surface, cx, cy, facing, phase):
        """Broad muscular armored chest with glowing core."""
        # Torso shape (V-shape, very wide at shoulders).
        torso_pts = [
            (cx - 13, cy - 5),  # left shoulder wide
            (cx - 10, cy + 6),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 10, cy + 6),
            (cx + 13, cy - 5),  # right shoulder wide
            (cx + 11, cy - 8),
            (cx - 11, cy - 8),
        ]
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], torso_pts)

        # Chest plate (main).
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
            (cx - 11, cy - 6),
            (cx + 11, cy - 6),
            (cx + 10, cy + 7),
            (cx - 10, cy + 7),
        ])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_mid"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 8, cy + 5),
            (cx - 8, cy + 5),
        ])

        # Muscle definition (V lines).
        pygame.draw.line(surface, _NS_auroth.PALETTE["armor_darkest"],
                         (cx, cy - 4), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_auroth.PALETTE["armor_darkest"],
                         (cx, cy - 4), (cx + 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_auroth.PALETTE["armor_edge"],
                         (cx - 1, cy - 3), (cx - 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_auroth.PALETTE["armor_edge"],
                         (cx + 1, cy - 3), (cx + 4, cy + 5), 1)

        # BIG CENTRAL GLOWING CORE (radiant energy).
        pulse = math.sin(phase * 2) * 0.35 + 0.65
        core_x = cx
        core_y = cy + 1

        # Outer big glow.
        for r in range(12, 2, -1):
            alpha = _NS_auroth._alpha(140 * pulse * (12 - r) / 12)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                   (core_x, core_y), r)

        # Core outline (metal ring).
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["plate_darkest"],
                              (core_x, core_y), 5)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["armor_dark"],
                              (core_x, core_y), 5, 1)

        # Core inner (glowing).
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_darkest"],
                              (core_x, core_y), 4)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_dark"],
                              (core_x, core_y), 3)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_mid"],
                              (core_x, core_y), 2)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_hot"],
                              (core_x, core_y), 1)
        pygame.draw.rect(surface, _NS_auroth.PALETTE["white"],
                         (core_x, core_y, 1, 1))

        # Rays radiating from core.
        for i in range(6):
            ray_angle = phase * 0.5 + i * math.pi / 3
            rx = core_x + int(math.cos(ray_angle) * 8)
            ry = core_y + int(math.sin(ray_angle) * 8)
            alpha = _NS_auroth._alpha(180 * pulse)
            pygame.draw.line(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                             (core_x, core_y), (rx, ry), 1)

        # HUGE PAULDRONS (shoulder armor with spikes).
        for side in (-1, 1):
            _NS_auroth._draw_pauldron(surface, cx + side * 12, cy - 4, side, phase)

    def _draw_pauldron(surface, cx, cy, side, phase):
        """Massive spiked shoulder pauldron."""
        # Main pauldron shape (wider, with 2 spikes on top).
        paul_pts = [
            (cx - 5, cy),
            (cx - 4, cy - 5),
            (cx - 1, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 5),
            (cx + 6, cy),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ]
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], paul_pts)

        # Main color.
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
            (cx - 4, cy),
            (cx - 3, cy - 4),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_mid"], [
            (cx - 3, cy - 1),
            (cx - 1, cy - 5),
            (cx + 2, cy - 5),
            (cx + 4, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                         (cx - 1, cy - 4, 3, 1))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_shine"],
                         (cx, cy - 4, 2, 1))

        # 2 SPIKES on top of pauldron.
        for spike_x_off in (-2, 2):
            spike_x = cx + spike_x_off
            spike_tip_y = cy - 10
            _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 1, cy - 6),
                (spike_x + 2, cy - 6),
            ])
            _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, cy - 6),
                (spike_x + 2, cy - 6),
            ])
            _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
                (spike_x, spike_tip_y),
                (spike_x, cy - 6),
                (spike_x + 1, cy - 6),
            ])
            pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"],
                             (spike_x, spike_tip_y, 1, 1))

        # Small glowing rune on pauldron.
        pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
        rune_alpha = _NS_auroth._alpha(200 * pulse)
        pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_mid"], rune_alpha),
                         (cx - 1, cy, 3, 1))
        pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], rune_alpha),
                         (cx, cy, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (non-swing). Bulky armored."""
        sway = math.sin(phase * 0.5) * 1

        # During attack, arm braces back.
        if action == "attack":
            elbow_y_off = int(math.sin(attack_progress * math.pi) * -2)
            elbow_x_off = -int(math.sin(attack_progress * math.pi) * 3) * facing
        else:
            elbow_y_off = 4 + int(sway)
            elbow_x_off = 0

        shoulder_x = cx - facing * 12
        shoulder_y = cy - 2

        # Upper arm.
        elbow_x = shoulder_x - facing * 3 + elbow_x_off
        elbow_y = shoulder_y + elbow_y_off + 3

        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)

        # Forearm.
        hand_x = elbow_x - facing * 2
        hand_y = elbow_y + 6

        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)

        # Gauntlet (big fist).
        _NS_auroth._draw_gauntlet(surface, hand_x, hand_y, facing, phase, small=False)

    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - the swinging arm."""
        # Determine swing angle.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up (arm goes back-down).
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.2 + t * -math.pi * 0.5
                forearm_bend = 0.4
            elif attack_progress < 0.6:
                # SWEEP forward (arc across).
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.7 + t * math.pi * 1.1  # -126° to +72°
                forearm_bend = 0.4 - t * 0.8
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.4 - t * math.pi * 0.6
                forearm_bend = -0.4 + t * 0.4
        else:
            arm_angle = -math.pi * 0.15 + math.sin(phase * 0.4) * 0.05
            forearm_bend = 0.5

        shoulder_x = cx + facing * 12
        shoulder_y = cy - 2

        arm_len = 9
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len) + 2

        forearm_len = 8
        forearm_angle = arm_angle + forearm_bend
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm (thick).
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 7)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 3)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_edge"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 6)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_auroth._aaline(surface, _NS_auroth.PALETTE["armor_mid"],
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), 2)

        # Elbow spike.
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_darkest"],
                         (elbow_x - 1, elbow_y - 3, 2, 3))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                         (elbow_x, elbow_y - 2, 1, 2))

        # Gauntlet (large glowing fist).
        _NS_auroth._draw_gauntlet(surface, hand_x, hand_y, facing, phase, small=False,
                                    glowing=(action == "attack"))

        # Store hand position for swing arc.
        _NS_auroth._front_hand = (hand_x, hand_y)

    def _draw_gauntlet(surface, hx, hy, facing, phase, small=False, glowing=False):
        """Big armored fist gauntlet."""
        size = 3 if small else 5

        # Base.
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1), size + 1)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["armor_darkest"],
                              (hx, hy), size)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["armor_dark"],
                              (hx, hy), size - 1)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["armor_mid"],
                              (hx, hy), size - 2)
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                         (hx - 1, hy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_shine"],
                         (hx, hy - 1, 1, 1))

        # Knuckle spikes.
        for spike_dx in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_darkest"],
                             (hx + spike_dx, hy - size - 1, 1, 2))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                             (hx + spike_dx, hy - size - 1, 1, 1))

        # Glowing knuckle rune.
        if glowing:
            pulse = math.sin(phase * 3) * 0.4 + 0.6
            for r in range(5, 1, -1):
                alpha = _NS_auroth._alpha(160 * pulse * (5 - r) / 5)
                _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                       (hx, hy), r)
            _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_hot"], (hx, hy), 1)
            pygame.draw.rect(surface, _NS_auroth.PALETTE["white"], (hx, hy, 1, 1))

    def _draw_titan_head(surface, cx, cy, facing, phase):
        """Horned crown helm with glowing visor eyes."""
        # Base helm shape.
        helm_pts = [
            (cx - 7, cy + 4),
            (cx - 8, cy - 1),
            (cx - 6, cy - 6),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 6, cy - 6),
            (cx + 8, cy - 1),
            (cx + 7, cy + 4),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
        ]
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 2) for p in helm_pts])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], helm_pts)

        # Main helm color.
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
            (cx - 6, cy + 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 5),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 5, cy - 5),
            (cx + 7, cy - 1),
            (cx + 6, cy + 3),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_mid"], [
            (cx - 5, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ])

        # Top highlight.
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                         (cx - 1, cy - 5, 3, 1))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_shine"],
                         (cx, cy - 5, 1, 1))

        # DARK VISOR SLIT with glowing eyes.
        visor_y = cy - 1
        pygame.draw.rect(surface, _NS_auroth.PALETTE["shadow_deep"],
                         (cx - 5, visor_y, 10, 3))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["eye_socket"],
                         (cx - 4, visor_y, 8, 2))

        # 2 GLOWING YELLOW EYES.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = visor_y + 1
            # Glow.
            for r in range(3, 0, -1):
                alpha = _NS_auroth._alpha(180 * pulse * (3 - r) / 3)
                _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_auroth.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["eye_glow"], (ex, ey, 1, 1))

        # Mouth grille (small vertical lines).
        for x_off in (-2, 0, 2):
            pygame.draw.line(surface, _NS_auroth.PALETTE["shadow_deep"],
                             (cx + x_off, cy + 3), (cx + x_off, cy + 5), 1)

        # HORNED CROWN on top.
        _NS_auroth._draw_horned_crown(surface, cx, cy - 6, facing, phase)

        # Cheek guards.
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_auroth.PALETTE["armor_darkest"],
                             (cx + side * 6, cy),
                             (cx + side * 5, cy + 5), 1)
            pygame.draw.line(surface, _NS_auroth.PALETTE["armor_edge"],
                             (cx + side * 5, cy), (cx + side * 5, cy + 4), 1)

    def _draw_horned_crown(surface, cx, cy, facing, phase):
        """Large horn crest (2 curved horns + central spike)."""
        beat = math.sin(phase * 1.5) * 1

        # CENTRAL big spike (tallest).
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"], [
            (cx + 1, cy - 10 + int(beat)),
            (cx - 2, cy - 3),
            (cx + 3, cy - 3),
        ])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], [
            (cx, cy - 10 + int(beat)),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
        ])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
            (cx, cy - 9 + int(beat)),
            (cx - 1, cy - 3),
            (cx + 1, cy - 3),
        ])
        _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_mid"], [
            (cx, cy - 8 + int(beat)),
            (cx, cy - 3),
            (cx + 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_edge"],
                         (cx, cy - 8 + int(beat), 1, 1))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"],
                         (cx, cy - 10 + int(beat), 1, 1))

        # Side horns (curving OUTWARD).
        for side in (-1, 1):
            # Horn goes up and out.
            base_x = cx + side * 3
            base_y = cy - 2
            mid_x = cx + side * 7
            mid_y = cy - 6
            tip_x = cx + side * 9
            tip_y = cy - 8 + int(beat * 0.5)

            # Shadow.
            _NS_auroth._poly(surface, _NS_auroth.PALETTE["shadow_deep"], [
                (base_x + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
                (mid_x + 1, mid_y + 2),
            ])

            # Main horn.
            _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_darkest"], [
                (base_x, base_y),
                (base_x + side * 2, base_y - 1),
                (tip_x, tip_y),
                (mid_x - side * 1, mid_y + 1),
            ])
            _NS_auroth._poly(surface, _NS_auroth.PALETTE["armor_dark"], [
                (base_x + side * 1, base_y - 1),
                (tip_x - side * 1, tip_y),
                (mid_x, mid_y + 1),
            ])
            # Highlight along top edge.
            pygame.draw.line(surface, _NS_auroth.PALETTE["armor_edge"],
                             (base_x + side * 1, base_y - 2),
                             (tip_x, tip_y), 1)
            pygame.draw.line(surface, _NS_auroth.PALETTE["armor_shine"],
                             (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2 - 1)),
                             (tip_x, tip_y), 1)

            # Bright tip.
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_shine"],
                             (tip_x, tip_y - 1, 1, 1))

    # ============================================================
    # SWING ARC (melee attack)
    # ============================================================
    def _draw_swing_arc(surface, boss, x, y, progress):
        """Curved gold energy trail from arm sweep."""
        if progress < 0.35 or progress > 0.7:
            return

        facing = boss.direction
        swing_t = (progress - 0.35) / 0.25
        swing_t = max(0, min(1, swing_t))
        alpha_val = int(255 * (1 - abs(swing_t - 0.5) * 1.5))
        alpha_val = max(0, alpha_val)

        # Arc center (in front of boss).
        center_x = x + facing * 5
        center_y = y + 5
        arc_radius = 26

        start_angle = -math.pi * 0.85 * facing
        end_angle = math.pi * 0.3 * facing
        current_angle = start_angle + (end_angle - start_angle) * swing_t

        # Arc trail (from swing start to current position).
        num_segments = 14
        for i in range(num_segments):
            t = i / num_segments
            seg_angle = start_angle + (current_angle - start_angle) * t
            seg_x = center_x + int(math.cos(seg_angle) * arc_radius) * facing
            seg_y = center_y + int(math.sin(seg_angle) * arc_radius)
            seg_alpha = _NS_auroth._alpha(alpha_val * t)
            size = int(2 + t * 4)

            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_darkest"], seg_alpha),
                                   (seg_x, seg_y), size)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_dark"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 1))
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_mid"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 2))
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Bright leading edge (crescent line).
        for i in range(6):
            edge_t = 1 - i * 0.1
            edge_angle = start_angle + (current_angle - start_angle) * edge_t
            ex1 = center_x + int(math.cos(edge_angle) * (arc_radius - 2)) * facing
            ey1 = center_y + int(math.sin(edge_angle) * (arc_radius - 2))
            ex2 = center_x + int(math.cos(edge_angle) * (arc_radius + 3)) * facing
            ey2 = center_y + int(math.sin(edge_angle) * (arc_radius + 3))
            e_alpha = _NS_auroth._alpha(alpha_val * (1 - i * 0.15))
            pygame.draw.line(surface, (*_NS_auroth.PALETTE["rad_hot"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 1)
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_shine"], e_alpha),
                             (ex2, ey2, 1, 1))

        # Sparks flying outward.
        for i in range(10):
            spark_angle = current_angle + i * 0.1 * facing
            spark_dist = arc_radius + i * 2
            sx = center_x + int(math.cos(spark_angle) * spark_dist) * facing
            sy = center_y + int(math.sin(spark_angle) * spark_dist)
            spark_alpha = _NS_auroth._alpha(220 - i * 20)
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], spark_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_shine"], spark_alpha),
                             (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.15 + 0.85
        shadow = pygame.Surface((140, 25), pygame.SRCALPHA)
        w = int(110 * pulse)
        h = int(13 * pulse)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (70 - w // 2 - radius, 12 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (20, 15, 5, 160),
                            (70 - w // 2, 12 - h // 2, w, h))
        surface.blit(shadow, (x - 70, y - 12))

    def _draw_radiant_wisps(surface, cx, cy, phase, intense=False):
        """Rising gold energy wisps."""
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 32 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_auroth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_darkest"], alpha),
                                   (sx, sy), 3)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_dark"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(8):
            spark_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 26)
            alpha = _NS_auroth._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_radiant_aura(surface, x, y, phase):
        """Large radiant gold aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_auroth._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_auroth._aacircle(aura, (*_NS_auroth.PALETTE["rad_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_auroth._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_auroth._aacircle(aura, (*_NS_auroth.PALETTE["rad_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_auroth._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_auroth._aacircle(aura, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Orbiting sparkles.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Gold ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_auroth.PALETTE["rad_darkest"], 200),
                            (5, 18, 160, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_auroth.PALETTE["rad_dark"], 220),
                            (14, 20, 142, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_auroth.PALETTE["rad_mid"], 230),
                            (25, 22, 120, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_auroth.PALETTE["rad_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_auroth.PALETTE["rad_hot"],
                                        _NS_auroth._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q: IONIC EDGE (enhanced arm sweep)
    # ============================================================
    def _draw_ionicedge_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground damage indicator (crescent in front).
        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            r = int(30 + t * 20)
            alpha = _NS_auroth._alpha(180 * (1 - t))
            # Draw arc/crescent in front.
            center_x = x + facing * 25
            center_y = y + 30
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                (center_x - r, center_y - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_hot"], alpha),
                                (center_x - r + 3, center_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_ionicedge_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Enhanced sweeping crescent blade of energy.
        if progress > 0.2 and progress < 0.9:
            t = (progress - 0.2) / 0.7
            intensity = math.sin(t * math.pi)

            center_x = x + facing * 8
            center_y = y + 3
            radius = 32

            # Multiple crescent layers (thicker blade).
            start_angle = -math.pi * 0.85 * facing
            end_angle = math.pi * 0.4 * facing
            current_angle = start_angle + (end_angle - start_angle) * t

            # Sweeping trail.
            num_segs = 20
            for i in range(num_segs):
                seg_t = i / num_segs
                seg_angle = start_angle + (current_angle - start_angle) * seg_t

                for r_offset in range(-3, 4):
                    seg_x = center_x + int(math.cos(seg_angle) * (radius + r_offset)) * facing
                    seg_y = center_y + int(math.sin(seg_angle) * (radius + r_offset))
                    alpha_layer = _NS_auroth._alpha(200 * intensity * seg_t *
                                                     (4 - abs(r_offset)) / 4)
                    if alpha_layer > 0:
                        if abs(r_offset) <= 1:
                            color = _NS_auroth.PALETTE["rad_hot"]
                        elif abs(r_offset) <= 2:
                            color = _NS_auroth.PALETTE["rad_light"]
                        else:
                            color = _NS_auroth.PALETTE["rad_mid"]
                        pygame.draw.rect(surface, (*color, alpha_layer),
                                         (seg_x, seg_y, 2, 2))

            # Bright edge line.
            for i in range(6):
                edge_t = 1 - i * 0.08
                edge_angle = start_angle + (current_angle - start_angle) * edge_t
                ex1 = center_x + int(math.cos(edge_angle) * (radius - 4)) * facing
                ey1 = center_y + int(math.sin(edge_angle) * (radius - 4))
                ex2 = center_x + int(math.cos(edge_angle) * (radius + 5)) * facing
                ey2 = center_y + int(math.sin(edge_angle) * (radius + 5))
                e_alpha = _NS_auroth._alpha(240 * intensity * (1 - i * 0.12))
                pygame.draw.line(surface, (*_NS_auroth.PALETTE["rad_shine"], e_alpha),
                                 (ex1, ey1), (ex2, ey2), 2)
                pygame.draw.line(surface, (*_NS_auroth.PALETTE["white"], e_alpha),
                                 (ex1, ey1), (ex2, ey2), 1)

            # Sparks flying off blade.
            for i in range(12):
                sp_angle = current_angle + i * 0.1 * facing
                sp_dist = radius + 4 + i
                sx = center_x + int(math.cos(sp_angle) * sp_dist) * facing
                sy = center_y + int(math.sin(sp_angle) * sp_dist)
                sp_alpha = _NS_auroth._alpha(230 - i * 15)
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], sp_alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_shine"], sp_alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL W: TRANSCENDENT WARD (place ward)
    # ============================================================
    def _draw_ward_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_auroth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ward ground ring (grows over time, allied buff zone).
        t = min(1.0, progress * 2)
        r = int(50 * t)
        if r > 3:
            alpha = _NS_auroth._alpha(180)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

            # Runes around ring.
            for i in range(8):
                angle = phase * 0.5 + i * math.pi / 4
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (sx - 1, sy, 3, 1))
                pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (sx, sy - 1, 1, 3))
                pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_shine"], (sx, sy, 1, 1))

    def _draw_ward_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_auroth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ward totem (small floating orb on staff).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        ward_y = ty - 15 + int(math.sin(phase * 1.5) * 2)

        # Small pillar under ward.
        pygame.draw.rect(surface, _NS_auroth.PALETTE["shadow_deep"],
                         (tx - 2, ty - 5, 4, 8))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_darkest"],
                         (tx - 2, ty - 5, 4, 7))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_dark"],
                         (tx - 1, ty - 4, 2, 6))
        pygame.draw.rect(surface, _NS_auroth.PALETTE["armor_mid"],
                         (tx, ty - 3, 1, 4))

        # WARD ORB (bright glowing).
        for r in range(10, 1, -1):
            alpha = _NS_auroth._alpha(140 * pulse * (10 - r) / 10)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                   (tx, ward_y), r)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_darkest"], (tx, ward_y), 5)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_dark"], (tx, ward_y), 4)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_mid"], (tx, ward_y), 3)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_light"], (tx, ward_y), 2)
        _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_shine"], (tx, ward_y), 1)
        pygame.draw.rect(surface, _NS_auroth.PALETTE["white"], (tx, ward_y, 1, 1))

        # Orbiting energy rings around ward.
        for i in range(3):
            ring_angle = phase * 2 + i * math.pi * 2 / 3
            rx = tx + int(math.cos(ring_angle) * 7)
            ry = ward_y + int(math.sin(ring_angle) * 3)
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_shine"], (rx, ry, 1, 1))

        # Rising sparkles from ward.
        for i in range(6):
            spark_t = (phase * 0.8 + i * 0.15) % 1.0
            sx = tx + int(math.sin(phase + i) * 5)
            sy = ward_y - int(spark_t * 15)
            alpha = _NS_auroth._alpha(220 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_shine"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: CONSECRATION (AoE around boss)
    # ============================================================
    def _draw_consecration_ground(surface, boss, x, y, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 3 expanding concentric rings around boss.
        for i in range(3):
            r_base = 20 + i * 15
            r = r_base + int(math.sin(phase * 2 + i) * 3)
            alpha = _NS_auroth._alpha(200 - i * 40)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_dark"], alpha),
                                (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                (x - r + 2, y + 45 - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)

    def _draw_consecration_foreground(surface, boss, x, y, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rising pillars of light around boss (like sacred ground).
        num_pillars = 10
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars + phase * 0.3
            r = 40
            px = x + int(math.cos(angle) * r)
            py_base = y + 40 + int(math.sin(angle) * r * 0.4)

            # Pillar rises from ground with waves.
            for layer in range(5):
                layer_t = (phase * 0.8 + i * 0.15 + layer * 0.1) % 1.0
                layer_y = py_base - int(layer_t * 30)
                layer_alpha = _NS_auroth._alpha(200 * (1 - layer_t))
                layer_w = int(4 - layer_t * 2)

                if layer_alpha > 0 and layer_w > 0:
                    pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_dark"], layer_alpha),
                                     (px - layer_w // 2, layer_y, layer_w, 2))
                    pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_mid"], layer_alpha),
                                     (px, layer_y, 1, 2))
                    pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], layer_alpha),
                                     (px, layer_y, 1, 1))

        # Ground sparkles.
        for i in range(16):
            angle = i * math.pi * 2 / 16 + phase * 0.4
            sp_r = 30 + int((i % 3) * 10)
            sx = x + int(math.cos(angle) * sp_r)
            sy = y + 40 + int(math.sin(angle) * sp_r * 0.4)
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL R: ETERNAL GUARDIAN (leap + dome shield)
    # ============================================================
    def _draw_guardian_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_auroth._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Wind-up: target indicator grows.
            t = progress / 0.4
            r = int(40 * t)
            alpha = _NS_auroth._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning runes.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_auroth.PALETTE["rad_hot"], (sx, sy, 2, 2))
        else:
            # Sanctified area after landing.
            r = 45
            alpha = _NS_auroth._alpha(200)
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_auroth.PALETTE["rad_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_guardian_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_auroth._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Wind-up: energy gathering above.
            t = progress / 0.4
            # Beam from sky.
            beam_top_y = max(0, ty - 100)
            for w, alpha in [(6, 80), (4, 140), (2, 220)]:
                pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_light"],
                                            _NS_auroth._alpha(alpha * t)),
                                 (tx - w // 2, beam_top_y, w, ty - beam_top_y - 30))

            gather_y = beam_top_y
            gather_r = int(4 + t * 8)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_auroth._alpha(200 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                       (tx, gather_y), r)
            _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_shine"],
                                   (tx, gather_y), max(1, gather_r - 2))
        elif progress < 0.55:
            # STRIKE: massive beam.
            t = (progress - 0.4) / 0.15
            intensity = math.sin(t * math.pi)

            beam_top_y = max(0, ty - 250)
            for layer_i, (width, alpha_val) in enumerate([
                (18, 100), (14, 140), (10, 180), (6, 220), (3, 255),
            ]):
                actual_alpha = _NS_auroth._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_auroth.PALETTE["rad_darkest"],
                    _NS_auroth.PALETTE["rad_dark"],
                    _NS_auroth.PALETTE["rad_mid"],
                    _NS_auroth.PALETTE["rad_light"],
                    _NS_auroth.PALETTE["rad_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, beam_top_y,
                                  width, ty - beam_top_y))

            # Impact explosion.
            impact_r = int(20 + t * 30)
            impact_alpha = _NS_auroth._alpha(240 * intensity)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_darkest"], impact_alpha),
                                   (tx, ty), impact_r + 4, 3)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_dark"], impact_alpha),
                                   (tx, ty), impact_r, 3)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_mid"], impact_alpha),
                                   (tx, ty), max(1, impact_r - 6), 2)
            _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_hot"], impact_alpha),
                                   (tx, ty), max(1, impact_r - 12), 1)

            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_auroth.PALETTE["rad_light"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
        else:
            # Protective dome + ward orb persists.
            t = (progress - 0.55) / 0.45
            r = 50
            breath = math.sin(phase * 2) * 2

            dome_surf = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
            center = (r + 10, r + 10)

            for i, (thickness, alpha_val) in enumerate([
                (3, 100), (2, 140), (1, 180),
            ]):
                pygame.draw.ellipse(dome_surf,
                                    (*_NS_auroth.PALETTE["rad_hot"], alpha_val),
                                    (10, 10 + int(breath),
                                     r * 2, r * 2 - int(breath) * 2), thickness)
                pygame.draw.ellipse(dome_surf,
                                    (*_NS_auroth.PALETTE["rad_shine"], alpha_val),
                                    (11, 11 + int(breath),
                                     r * 2 - 2, r * 2 - 2 - int(breath) * 2), 1)

            # Dome sparkles.
            for i in range(18):
                angle = phase * 1.2 + i * math.pi / 9
                sx = center[0] + int(math.cos(angle) * r)
                sy = center[1] + int(math.sin(angle) * r * 0.7) - r // 3
                pygame.draw.rect(dome_surf, _NS_auroth.PALETTE["rad_shine"], (sx, sy, 2, 2))
                pygame.draw.rect(dome_surf, _NS_auroth.PALETTE["white"], (sx, sy, 1, 1))

            surface.blit(dome_surf, (tx - r - 10, ty - r - 10))

            # Central ward orb inside dome.
            ward_pulse = math.sin(phase * 2.5) * 0.3 + 0.7
            ward_y = ty - 12
            for r_o in range(8, 1, -1):
                alpha = _NS_auroth._alpha(140 * ward_pulse * (8 - r_o) / 8)
                _NS_auroth._aacircle(surface, (*_NS_auroth.PALETTE["rad_light"], alpha),
                                       (tx, ward_y), r_o)
            _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_darkest"], (tx, ward_y), 4)
            _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_mid"], (tx, ward_y), 3)
            _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_hot"], (tx, ward_y), 2)
            _NS_auroth._aacircle(surface, _NS_auroth.PALETTE["rad_shine"], (tx, ward_y), 1)
            pygame.draw.rect(surface, _NS_auroth.PALETTE["white"], (tx, ward_y, 1, 1))

            # Rising particles inside dome.
            for i in range(8):
                p_t = (phase * 0.6 + i * 0.12) % 1.0
                px = tx - 20 + i * 5 + int(math.sin(phase + i) * 3)
                py = ty + 10 - int(p_t * 35)
                alpha = _NS_auroth._alpha(200 * (1 - p_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_hot"], alpha),
                                     (px, py, 1, 1))
                    pygame.draw.rect(surface, (*_NS_auroth.PALETTE["rad_shine"], alpha),
                                     (px, py, 1, 1))


# ====================================================================
# morvein.py
# ====================================================================



class _NS_morvein:
    """Namespace morvein - Phantom Lancer knight (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Armor (dark obsidian black)
        "armor_darkest": (5, 8, 15),
        "armor_dark": (18, 25, 45),
        "armor_mid": (45, 55, 85),
        "armor_light": (95, 110, 155),
        "armor_edge": (160, 175, 220),
        "armor_shine": (220, 230, 255),

        # Crystal (bright cyan-blue)
        "crystal_darkest": (5, 25, 60),
        "crystal_dark": (20, 70, 150),
        "crystal_mid": (60, 150, 240),
        "crystal_light": (140, 210, 255),
        "crystal_hot": (200, 240, 255),
        "crystal_shine": (240, 250, 255),

        # Phantom aura (spectral blue-cyan)
        "phantom_darkest": (10, 20, 50),
        "phantom_dark": (30, 70, 130),
        "phantom_mid": (70, 140, 220),
        "phantom_light": (150, 210, 255),
        "phantom_hot": (220, 240, 255),

        # Cape (dark blue-purple)
        "cape_dark": (15, 10, 35),
        "cape_mid": (35, 25, 75),
        "cape_light": (75, 60, 130),

        # Horse spectral (dark grey with blue tint)
        "horse_dark": (20, 25, 40),
        "horse_mid": (50, 60, 85),
        "horse_light": (100, 115, 155),
        "horse_shine": (170, 190, 230),

        # Horse mane (blue spectral flame)
        "mane_dark": (30, 80, 150),
        "mane_mid": (80, 160, 240),
        "mane_light": (180, 220, 255),

        # Eye (fierce cyan-white)
        "eye_socket": (2, 5, 15),
        "eye_dark": (10, 40, 100),
        "eye_mid": (80, 180, 255),
        "eye_light": (200, 240, 255),
        "eye_glow": (240, 255, 255),

        # Skin (pale phantom knight)
        "skin_dark": (65, 55, 60),
        "skin_mid": (130, 115, 120),
        "skin_light": (195, 180, 185),

        # Hair (long black)
        "hair_darkest": (5, 5, 10),
        "hair_dark": (20, 20, 30),
        "hair_mid": (50, 50, 70),
        "hair_light": (100, 100, 130),

        # Lance (dark metal with blue crystal)
        "lance_dark": (15, 18, 30),
        "lance_mid": (55, 65, 95),
        "lance_light": (130, 145, 180),

        "shadow": (0, 0, 0),
        "shadow_deep": (1, 2, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morvein._clamp(color)
        if _NS_morvein.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvein._clamp(color)
        if _NS_morvein.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_morvein._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_morvein._clamp(color), points)

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
        return int(x + 180 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morvein(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_morvein._update_mv_attack_anim(boss)
        attacking = (
            getattr(boss, "_mv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        phantom_form = active_skill == "r"

        # Ambient.
        _NS_morvein._draw_phantom_aura(surface, x, y, pulse, phantom_form)
        _NS_morvein._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_morvein._draw_spectralcharge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvein._draw_violentstrike_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_morvein._draw_puncture_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_morvein._draw_mv_attack(surface, boss, x, y, phantom_form)
        else:
            _NS_morvein._draw_mv_idle(surface, boss, x, y, phantom_form)

        # Foreground FX.
        if active_skill == "q":
            _NS_morvein._draw_puncture_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvein._draw_violentstrike_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvein._draw_spectralcharge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvein._draw_phantom_foreground(surface, boss, x, y, skill_timer, pulse)

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
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._mv_attack_dir = int(getattr(boss, "direction", 1))
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

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_mv_idle(surface, boss, x, y, phantom_form):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_morvein._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_morvein._draw_phantom_wisps(surface, x, y + 42, boss.pulse)
        _NS_morvein._draw_mv_body(surface, x, y + bob, boss.direction,
                                    boss.pulse, "idle", phantom_form=phantom_form)

    def _draw_mv_attack(surface, boss, x, y, phantom_form):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mv_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_mv_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.7) * 5)
        # Lance thrust: pull back → thrust forward → recover
        if progress < 0.35:
            t = progress / 0.35
            lean = int(t * -3) * facing
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            lean = int((-3 + t * 9)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.55) / 0.45
            lean = int(6 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_morvein._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_morvein._draw_phantom_wisps(surface, x + lean, y + 42, boss.pulse, intense=True)
        _NS_morvein._draw_mv_body(surface, x + lean, y + bob - lift,
                                    facing, boss.pulse, "attack",
                                    progress, phantom_form=phantom_form)
        _NS_morvein._draw_lance_slash(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (knight on spectral horse)
    # ============================================================
    def _draw_mv_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                      phantom_form=False):
        # Draw horse first.
        _NS_morvein._draw_spectral_horse(surface, cx, cy + 8, facing, phase, phantom_form)

        # Saddle.
        _NS_morvein._draw_saddle(surface, cx, cy + 2, facing, phase, phantom_form)

        # Rider.
        _NS_morvein._draw_knight_rider(surface, cx, cy - 10, facing, phase, action,
                                         attack_progress, phantom_form)

    def _draw_spectral_horse(surface, cx, cy, facing, phase, phantom_form):
        """Dark spectral horse with blue flame mane."""
        base_alpha = 180 if phantom_form else 255
        h_dark = _NS_morvein.PALETTE["horse_dark"]
        h_mid = _NS_morvein.PALETTE["horse_mid"]
        h_light = _NS_morvein.PALETTE["horse_light"]
        h_shine = _NS_morvein.PALETTE["horse_shine"]
        if phantom_form:
            h_dark = (60, 100, 180)
            h_mid = (100, 150, 220)
            h_light = (160, 200, 250)
            h_shine = (220, 240, 255)

        # Body (side profile).
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
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in body_pts])
        _NS_morvein._poly(surface, h_dark, body_pts)

        # Upper body highlight.
        _NS_morvein._poly(surface, h_mid, [
            (cx - 16, cy - 2),
            (cx - 14, cy - 8),
            (cx - 6, cy - 10),
            (cx + 4, cy - 10),
            (cx + 12, cy - 8),
            (cx + 17, cy - 4),
            (cx + 15, cy),
            (cx - 14, cy),
        ])
        _NS_morvein._poly(surface, h_light, [
            (cx - 12, cy - 4),
            (cx - 8, cy - 8),
            (cx + 2, cy - 9),
            (cx + 10, cy - 6),
            (cx + 12, cy - 3),
            (cx - 8, cy - 3),
        ])
        # Sheen.
        _NS_morvein._poly(surface, h_shine, [
            (cx - 4, cy - 7),
            (cx + 2, cy - 8),
            (cx + 6, cy - 6),
            (cx + 2, cy - 5),
            (cx - 3, cy - 5),
        ])

        # Blue crystal armor plates on horse (chest and rear).
        _NS_morvein._draw_horse_armor(surface, cx, cy, facing, phase, phantom_form)

        # LEGS.
        _NS_morvein._draw_horse_legs(surface, cx, cy, facing, phase, phantom_form,
                                       h_dark, h_mid)

        # HEAD/NECK with armored barding.
        _NS_morvein._draw_horse_head(surface, cx, cy, facing, phase, phantom_form,
                                       h_dark, h_mid, h_light, h_shine)

        # TAIL (spectral blue flame).
        _NS_morvein._draw_horse_tail(surface, cx, cy, facing, phase, phantom_form)

    def _draw_horse_armor(surface, cx, cy, facing, phase, phantom_form):
        """Blue crystal armor plates on horse body."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Chest plate crystal.
        chest_x = cx + facing * 12
        chest_y = cy - 4

        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], [
            (chest_x - 2, chest_y - 2),
            (chest_x + 2, chest_y - 2),
            (chest_x + 3, chest_y + 1),
            (chest_x, chest_y + 3),
            (chest_x - 3, chest_y + 1),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_dark"], [
            (chest_x - 1, chest_y - 1),
            (chest_x + 1, chest_y - 1),
            (chest_x + 2, chest_y + 1),
            (chest_x, chest_y + 2),
            (chest_x - 2, chest_y + 1),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_mid"], [
            (chest_x, chest_y),
            (chest_x + 1, chest_y + 1),
            (chest_x, chest_y + 1),
        ])
        # Glow.
        for r in range(4, 0, -1):
            alpha = _NS_morvein._alpha(100 * pulse * (4 - r) / 4)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                    (chest_x, chest_y), r)
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"], (chest_x, chest_y, 1, 1))

    def _draw_horse_legs(surface, cx, cy, facing, phase, phantom_form, h_dark, h_mid):
        """4 horse legs."""
        leg_wave = math.sin(phase * 1.2) * 1

        legs = [
            (cx - 12, "back_far", -1),
            (cx - 10, "back_near", 1),
            (cx + 10, "front_far", -1),
            (cx + 12, "front_near", 1),
        ]

        for leg_x, name, phase_off in legs:
            offset = int(leg_wave * phase_off)
            top_y = cy + 6
            knee_y = cy + 14 + offset
            hoof_y = cy + 22 + offset

            _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                                 (leg_x + 1, top_y + 1),
                                 (leg_x + 1, knee_y + 1), 4)
            _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                                 (leg_x + 1, knee_y + 1),
                                 (leg_x + 1, hoof_y + 1), 3)

            _NS_morvein._aaline(surface, h_dark, (leg_x, top_y), (leg_x, knee_y), 4)
            _NS_morvein._aaline(surface, h_mid, (leg_x, top_y), (leg_x, knee_y), 2)

            _NS_morvein._aaline(surface, h_dark, (leg_x, knee_y), (leg_x, hoof_y), 3)
            _NS_morvein._aaline(surface, h_mid, (leg_x, knee_y), (leg_x, hoof_y), 1)

            # Hoof (metal armor).
            pygame.draw.rect(surface, _NS_morvein.PALETTE["shadow_deep"],
                             (leg_x - 2, hoof_y - 1, 4, 3))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["armor_darkest"],
                             (leg_x - 2, hoof_y, 4, 2))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["armor_dark"],
                             (leg_x - 1, hoof_y, 2, 1))

            # Small crystal glow on hoof if phantom.
            if phantom_form:
                pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_mid"],
                                 (leg_x, hoof_y, 1, 1))
                pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"],
                                 (leg_x, hoof_y, 1, 1))

    def _draw_horse_head(surface, cx, cy, facing, phase, phantom_form,
                          h_dark, h_mid, h_light, h_shine):
        """Horse head with armored barding."""
        neck_base_x = cx + facing * 15
        neck_base_y = cy - 8

        neck_tip_x = neck_base_x + facing * 8
        neck_tip_y = neck_base_y - 6

        # Neck.
        prev = (neck_base_x, neck_base_y)
        for step in range(1, 5):
            t = step / 4
            nx = int((1 - t) * neck_base_x + t * neck_tip_x)
            ny = int((1 - t) * neck_base_y + t * neck_tip_y)
            thickness = 8 - step
            _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                                 (prev[0] + 1, prev[1] + 1),
                                 (nx + 1, ny + 1), thickness + 1)
            _NS_morvein._aaline(surface, h_dark, prev, (nx, ny), thickness)
            _NS_morvein._aaline(surface, h_mid, prev, (nx, ny), max(1, thickness - 2))
            _NS_morvein._aaline(surface, h_light,
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
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_morvein._poly(surface, h_dark, head_pts)
        _NS_morvein._poly(surface, h_mid, [
            (hx - 3 * facing, hy - 2),
            (hx + 2 * facing, hy - 3),
            (hx + 5 * facing, hy - 1),
            (hx + 7 * facing, hy + 1),
            (hx + 5 * facing, hy + 3),
            (hx - 2 * facing, hy + 3),
        ])
        _NS_morvein._poly(surface, h_light, [
            (hx, hy - 1),
            (hx + 4 * facing, hy),
            (hx + 5 * facing, hy + 2),
            (hx + 2 * facing, hy + 2),
        ])

        # ARMORED FACE PLATE (dark with crystal center).
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], [
            (hx - 1 * facing, hy - 2),
            (hx + 4 * facing, hy - 2),
            (hx + 6 * facing, hy),
            (hx + 4 * facing, hy + 2),
            (hx - 1 * facing, hy + 2),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_dark"], [
            (hx, hy - 1),
            (hx + 4 * facing, hy - 1),
            (hx + 5 * facing, hy),
            (hx + 4 * facing, hy + 1),
            (hx, hy + 1),
        ])
        pygame.draw.rect(surface, _NS_morvein.PALETTE["armor_edge"],
                         (hx + 2 * facing, hy - 1, 1, 1))

        # Crystal at center of face plate.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crystal_x = hx + 2 * facing
        crystal_y = hy
        for r in range(3, 0, -1):
            alpha = _NS_morvein._alpha(120 * pulse * (3 - r) / 3)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                    (crystal_x, crystal_y), r)
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"],
                         (crystal_x, crystal_y, 1, 1))

        # Ear.
        _NS_morvein._poly(surface, h_dark, [
            (hx - 2 * facing, hy - 3),
            (hx - 3 * facing, hy - 6),
            (hx, hy - 3),
        ])
        _NS_morvein._poly(surface, h_mid, [
            (hx - 1 * facing, hy - 3),
            (hx - 2 * facing, hy - 5),
            (hx, hy - 3),
        ])

        # Eye (glowing blue).
        eye_x = hx + 1 * facing
        eye_y = hy - 1
        pygame.draw.rect(surface, _NS_morvein.PALETTE["shadow_deep"],
                         (eye_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_socket"],
                         (eye_x, eye_y, 1, 1))
        for r in range(2, 0, -1):
            alpha = _NS_morvein._alpha(180 * pulse * (2 - r) / 2)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["eye_mid"], alpha),
                                    (eye_x, eye_y), r)
        pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_glow"], (eye_x, eye_y, 1, 1))

        # Mouth line.
        pygame.draw.line(surface, _NS_morvein.PALETTE["shadow_deep"],
                         (hx + 4 * facing, hy + 4),
                         (hx + 7 * facing, hy + 4), 1)

        # SPECTRAL MANE (blue flame).
        _NS_morvein._draw_spectral_mane(surface, neck_base_x, neck_base_y,
                                          neck_tip_x, neck_tip_y, facing, phase)

    def _draw_spectral_mane(surface, base_x, base_y, tip_x, tip_y, facing, phase):
        """Blue flame-like mane."""
        sway = math.sin(phase * 1.2) * 2

        for i in range(6):
            t = i / 5
            mx = int((1 - t) * base_x + t * tip_x)
            my = int((1 - t) * base_y + t * tip_y)

            # Mane strand goes back and up (like flame).
            flame_len = 4 + int(math.sin(phase * 2 + i) * 2)
            strand_x = mx - facing * (1 + int(sway * 0.3))
            strand_y = my - flame_len

            # Flame effect.
            _NS_morvein._aaline(surface, _NS_morvein.PALETTE["mane_dark"],
                                 (mx, my), (strand_x, strand_y), 2)
            _NS_morvein._aaline(surface, _NS_morvein.PALETTE["mane_mid"],
                                 (mx, my), (strand_x, strand_y), 1)
            pygame.draw.rect(surface, _NS_morvein.PALETTE["mane_light"],
                             (strand_x, strand_y, 1, 1))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"],
                             (strand_x, strand_y - 1, 1, 1))

    def _draw_horse_tail(surface, cx, cy, facing, phase, phantom_form):
        """Spectral flame tail."""
        sway = math.sin(phase * 0.9) * 3
        base_x = cx - facing * 18
        base_y = cy - 2

        # Tail as flowing flame strands.
        for i in range(3):
            spread = (i - 1) * 2
            for step in range(1, 6):
                t = step / 5
                tx = base_x - facing * int(t * 10) + spread
                ty = base_y + int(t * 8) - int(math.sin(phase * 1.5 + i + t * 3) * 3)
                # Wave.
                tx += int(math.sin(phase * 1.2 + i + t * 2) * 2)
                thickness = max(1, 4 - step)

                _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                                     (tx + 1, ty + 1), (tx + 1, ty + 1), thickness + 1)
                _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["mane_dark"],
                                        (tx, ty), thickness)
                _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["mane_mid"],
                                        (tx, ty), max(1, thickness - 1))
                pygame.draw.rect(surface, _NS_morvein.PALETTE["mane_light"],
                                 (tx, ty, 1, 1))

        # Bright hot tip.
        end_x = base_x - facing * 10
        end_y = base_y + 8
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"], (end_x, end_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_shine"], (end_x, end_y - 1, 1, 1))

    def _draw_saddle(surface, cx, cy, facing, phase, phantom_form):
        """Dark saddle with crystal."""
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
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in saddle_pts])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], saddle_pts)
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_dark"], [
            (cx - 8, cy - 1),
            (cx + 8, cy - 1),
            (cx + 9, cy + 2),
            (cx - 9, cy + 2),
        ])

        # Saddle blanket (dark blue-purple).
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["cape_dark"], [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 8, cy + 1),
            (cx - 8, cy + 1),
        ])

        # Crystal gem in center of saddle.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_x = cx
        gem_y = cy - 2
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_darkest"], [
            (gem_x - 2, gem_y),
            (gem_x, gem_y - 2),
            (gem_x + 2, gem_y),
            (gem_x, gem_y + 2),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_mid"], [
            (gem_x - 1, gem_y),
            (gem_x, gem_y - 1),
            (gem_x + 1, gem_y),
            (gem_x, gem_y + 1),
        ])
        for r in range(4, 0, -1):
            alpha = _NS_morvein._alpha(120 * pulse * (4 - r) / 4)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                    (gem_x, gem_y), r)
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"], (gem_x, gem_y, 1, 1))

    def _draw_knight_rider(surface, cx, cy, facing, phase, action, attack_progress,
                            phantom_form):
        """Knight rider on horse."""
        # Cape behind.
        _NS_morvein._draw_cape(surface, cx, cy + 2, facing, phase, phantom_form)

        # Robe/lower body.
        _NS_morvein._draw_rider_lower(surface, cx, cy + 8, facing, phase)

        # Torso.
        _NS_morvein._draw_rider_torso(surface, cx, cy + 2, facing, phase, phantom_form)

        # Reins arm (back).
        _NS_morvein._draw_reins_arm(surface, cx, cy + 2, facing, phase)

        # Head.
        _NS_morvein._draw_knight_head(surface, cx, cy - 8, facing, phase, phantom_form)

        # Lance arm.
        _NS_morvein._draw_lance_arm(surface, cx, cy + 2, facing, phase, action,
                                      attack_progress)

    def _draw_cape(surface, cx, cy, facing, phase, phantom_form):
        """Dark cape flowing behind."""
        sway = math.sin(phase * 0.6) * 3
        cape_pts = [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 10 + int(sway), cy + 8),
            (cx + 12 + int(sway), cy + 16),
            (cx + 8 + int(sway), cy + 22),
            (cx - 8 - int(sway), cy + 22),
            (cx - 12 - int(sway), cy + 16),
            (cx - 10 - int(sway), cy + 8),
        ]
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in cape_pts])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["cape_dark"], cape_pts)
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["cape_mid"], [
            (cx - 6, cy + 1),
            (cx + 6, cy + 1),
            (cx + 9 + int(sway), cy + 9),
            (cx + 6 + int(sway), cy + 20),
            (cx - 6 - int(sway), cy + 20),
            (cx - 9 - int(sway), cy + 9),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["cape_light"], [
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 4, cy + 14),
            (cx - 4, cy + 14),
        ])

    def _draw_rider_lower(surface, cx, cy, facing, phase):
        """Armored legs on saddle."""
        # Legs armor (visible above saddle).
        for side in (-1, 1):
            leg_x = cx + side * 3
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"], [
                (leg_x - 2, cy - 4),
                (leg_x + 2, cy - 4),
                (leg_x + 2, cy + 2),
                (leg_x - 2, cy + 2),
            ])
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], [
                (leg_x - 2, cy - 4),
                (leg_x + 2, cy - 4),
                (leg_x + 2, cy + 2),
                (leg_x - 2, cy + 2),
            ])
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_dark"], [
                (leg_x - 1, cy - 3),
                (leg_x + 1, cy - 3),
                (leg_x + 1, cy + 1),
                (leg_x - 1, cy + 1),
            ])
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_mid"], [
                (leg_x, cy - 2),
                (leg_x, cy),
            ])
            pygame.draw.rect(surface, _NS_morvein.PALETTE["armor_edge"],
                             (leg_x, cy - 2, 1, 1))

    def _draw_rider_torso(surface, cx, cy, facing, phase, phantom_form):
        """Dark armored torso with crystal chest."""
        torso_pts = [
            (cx - 8, cy - 3),
            (cx - 7, cy + 5),
            (cx + 7, cy + 5),
            (cx + 8, cy - 3),
            (cx + 7, cy - 5),
            (cx - 7, cy - 5),
        ]
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in torso_pts])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], torso_pts)
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_mid"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])

        # Muscle V-lines.
        pygame.draw.line(surface, _NS_morvein.PALETTE["armor_darkest"],
                         (cx, cy - 2), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_morvein.PALETTE["armor_darkest"],
                         (cx, cy - 2), (cx + 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_morvein.PALETTE["armor_edge"],
                         (cx - 1, cy - 1), (cx - 3, cy + 2), 1)
        pygame.draw.line(surface, _NS_morvein.PALETTE["armor_edge"],
                         (cx + 1, cy - 1), (cx + 3, cy + 2), 1)

        # BIG CRYSTAL on chest.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crystal_x = cx
        crystal_y = cy + 1

        # Crystal diamond shape.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], [
            (crystal_x - 3, crystal_y),
            (crystal_x, crystal_y - 3),
            (crystal_x + 3, crystal_y),
            (crystal_x, crystal_y + 3),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_darkest"], [
            (crystal_x - 2, crystal_y),
            (crystal_x, crystal_y - 2),
            (crystal_x + 2, crystal_y),
            (crystal_x, crystal_y + 2),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_dark"], [
            (crystal_x - 1, crystal_y),
            (crystal_x, crystal_y - 1),
            (crystal_x + 1, crystal_y),
            (crystal_x, crystal_y + 1),
        ])
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"],
                         (crystal_x, crystal_y, 1, 1))
        # Glow.
        for r in range(6, 1, -1):
            alpha = _NS_morvein._alpha(100 * pulse * (6 - r) / 6)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                    (crystal_x, crystal_y), r)

        # Shoulder pauldrons (dark with spikes).
        for side in (-1, 1):
            _NS_morvein._draw_shoulder_spike(surface, cx + side * 7, cy - 3, side, phase)

    def _draw_shoulder_spike(surface, cx, cy, side, phase):
        """Dark spiky shoulder pauldron."""
        # Base pauldron.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"], [
            (cx - 3, cy + 1),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 3, cy + 1),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], [
            (cx - 3, cy),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 3, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_dark"], [
            (cx - 2, cy),
            (cx - 1, cy - 2),
            (cx + 1, cy - 2),
            (cx + 2, cy),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_morvein.PALETTE["armor_edge"],
                         (cx - 1, cy - 1, 3, 1))

        # Spike jutting up-outward.
        spike_x = cx + side * 2
        spike_tip_y = cy - 7
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"], [
            (spike_x + 1, spike_tip_y + 1),
            (spike_x - 1, cy - 3),
            (spike_x + 2, cy - 3),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_darkest"], [
            (spike_x, spike_tip_y),
            (spike_x - 1, cy - 3),
            (spike_x + 2, cy - 3),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["armor_dark"], [
            (spike_x, spike_tip_y),
            (spike_x, cy - 3),
            (spike_x + 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_mid"],
                         (spike_x, spike_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"],
                         (spike_x, spike_tip_y, 1, 1))

    def _draw_reins_arm(surface, cx, cy, facing, phase):
        """Back arm holding reins."""
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 3
        hand_x = shoulder_x + facing * 3
        hand_y = shoulder_y + 8 + int(sway)

        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_darkest"],
                             (shoulder_x, shoulder_y), (hand_x, hand_y), 4)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_dark"],
                             (shoulder_x, shoulder_y), (hand_x, hand_y), 2)

        # Gauntlet.
        _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["armor_darkest"],
                                (hand_x, hand_y), 2)
        _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["armor_dark"],
                                (hand_x, hand_y), 1)

        # Reins line.
        rein_end_x = hand_x + facing * 20
        rein_end_y = hand_y + 4
        pygame.draw.line(surface, _NS_morvein.PALETTE["cape_dark"],
                         (hand_x + facing, hand_y), (rein_end_x, rein_end_y), 1)

    def _draw_lance_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding lance."""
        # Lance thrust animation.
        if action == "attack":
            if attack_progress < 0.35:
                # Pull back.
                t = attack_progress / 0.35
                arm_angle = -0.2 - t * 0.4  # pull elbow up-back
                lance_extend = -t * 3
            elif attack_progress < 0.55:
                # THRUST forward.
                t = (attack_progress - 0.35) / 0.20
                arm_angle = -0.6 + t * 0.5
                lance_extend = -3 + t * 15  # extend forward
            else:
                # Recover.
                t = (attack_progress - 0.55) / 0.45
                arm_angle = -0.1 - t * 0.1
                lance_extend = 12 * (1 - t)
        else:
            arm_angle = -0.2 + math.sin(phase * 0.5) * 0.05
            lance_extend = 0

        shoulder_x = cx + facing * 6
        shoulder_y = cy - 3

        elbow_x = shoulder_x + int(math.cos(arm_angle) * 5) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * 5) + 3
        hand_x = elbow_x + int(math.cos(arm_angle * 0.5) * 6) * facing + int(lance_extend * facing)
        hand_y = elbow_y + int(math.sin(arm_angle * 0.5) * 3) + 2

        # Upper arm.
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 5)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_mid"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_morvein._aaline(surface, _NS_morvein.PALETTE["armor_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Gauntlet.
        _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["armor_darkest"],
                                (hand_x, hand_y), 3)
        _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["armor_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_morvein.PALETTE["armor_edge"],
                         (hand_x, hand_y - 1, 1, 1))

        # LANCE.
        _NS_morvein._draw_phantom_lance(surface, hand_x, hand_y, facing, phase, action,
                                          attack_progress)

    def _draw_phantom_lance(surface, hand_x, hand_y, facing, phase, action, attack_progress):
        """Long lance with blue crystal blade."""
        # Lance angle - mostly horizontal forward.
        if action == "attack":
            if attack_progress < 0.35:
                angle = 0.15 - (attack_progress / 0.35) * 0.1
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.20
                angle = 0.05 - t * 0.1
            else:
                t = (attack_progress - 0.55) / 0.45
                angle = -0.05 + t * 0.15
        else:
            angle = 0.1 + math.sin(phase * 0.5) * 0.03

        # Lance length.
        lance_len = 32
        tip_x = hand_x + int(math.cos(angle) * lance_len) * facing
        tip_y = hand_y + int(math.sin(angle) * lance_len)
        butt_x = hand_x - int(math.cos(angle) * 8) * facing
        butt_y = hand_y - int(math.sin(angle) * 8)

        # Shaft.
        pygame.draw.line(surface, _NS_morvein.PALETTE["shadow_deep"],
                         (butt_x + 1, butt_y + 1), (tip_x + 1, tip_y + 1), 4)
        pygame.draw.line(surface, _NS_morvein.PALETTE["lance_dark"],
                         (butt_x, butt_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_morvein.PALETTE["lance_mid"],
                         (butt_x, butt_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_morvein.PALETTE["lance_light"],
                         (butt_x, butt_y - 1), (tip_x, tip_y - 1), 1)

        # LANCE HEAD (bright blue crystal blade).
        # Perpendicular for blade width.
        perp = angle + math.pi / 2
        blade_len = 12

        # Blade tip position (beyond shaft tip).
        blade_tip_x = tip_x + int(math.cos(angle) * blade_len) * facing
        blade_tip_y = tip_y + int(math.sin(angle) * blade_len)

        # Blade base (widened at shaft tip).
        blade_a_x = tip_x + int(math.cos(perp) * 3) * facing
        blade_a_y = tip_y + int(math.sin(perp) * 3)
        blade_b_x = tip_x - int(math.cos(perp) * 3) * facing
        blade_b_y = tip_y - int(math.sin(perp) * 3)

        # Shadow.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"], [
            (blade_tip_x + 1, blade_tip_y + 1),
            (blade_a_x + 1, blade_a_y + 1),
            (blade_b_x + 1, blade_b_y + 1),
        ])

        # Blade dark outline.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_darkest"],
                          [(blade_tip_x, blade_tip_y),
                           (blade_a_x, blade_a_y),
                           (blade_b_x, blade_b_y)])
        # Inner blade.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_dark"], [
            (blade_tip_x, blade_tip_y),
            (int((blade_a_x + tip_x) / 2 + math.cos(perp) * 1 * facing),
             int((blade_a_y + tip_y) / 2 + math.sin(perp) * 1)),
            (int((blade_b_x + tip_x) / 2 - math.cos(perp) * 1 * facing),
             int((blade_b_y + tip_y) / 2 - math.sin(perp) * 1)),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["crystal_mid"], [
            (blade_tip_x, blade_tip_y),
            (int((blade_tip_x + tip_x) / 2),
             int((blade_tip_y + tip_y) / 2)),
            (tip_x, tip_y),
        ])
        # Bright edge.
        pygame.draw.line(surface, _NS_morvein.PALETTE["crystal_light"],
                         (tip_x, tip_y), (blade_tip_x, blade_tip_y), 1)
        pygame.draw.line(surface, _NS_morvein.PALETTE["crystal_hot"],
                         (int((tip_x + blade_tip_x) / 2),
                          int((tip_y + blade_tip_y) / 2)),
                         (blade_tip_x, blade_tip_y), 1)
        pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvein.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))

        # Glow around blade.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(8, 1, -1):
            alpha = _NS_morvein._alpha(100 * pulse * (8 - r) / 8)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                    (blade_tip_x, blade_tip_y), r)

        # Small crystal accents on shaft.
        for t_pos in (0.3, 0.6):
            crystal_x = int(butt_x + (tip_x - butt_x) * t_pos)
            crystal_y = int(butt_y + (tip_y - butt_y) * t_pos)
            pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_darkest"],
                             (crystal_x - 1, crystal_y, 3, 1))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_mid"],
                             (crystal_x, crystal_y, 1, 1))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"],
                             (crystal_x, crystal_y, 1, 1))

        # Store lance tip position for slash arc.
        _NS_morvein._lance_tip = (blade_tip_x, blade_tip_y)

    def _draw_knight_head(surface, cx, cy, facing, phase, phantom_form):
        """Knight head with long black hair and glowing blue eyes."""
        # Head base.
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
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_pts])

        skin_d = _NS_morvein.PALETTE["skin_dark"]
        skin_m = _NS_morvein.PALETTE["skin_mid"]
        skin_l = _NS_morvein.PALETTE["skin_light"]
        if phantom_form:
            skin_d = (100, 130, 180)
            skin_m = (150, 180, 220)
            skin_l = (200, 220, 245)

        _NS_morvein._poly(surface, skin_d, head_pts)
        _NS_morvein._poly(surface, skin_m, [
            (cx - 4, cy - 1),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
            (cx + 4, cy - 4),
            (cx + 4, cy - 1),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_morvein._poly(surface, skin_l, [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])

        # LONG BLACK HAIR.
        _NS_morvein._draw_long_hair(surface, cx, cy, facing, phase)

        # GLOWING BLUE EYES.
        _NS_morvein._draw_knight_eyes(surface, cx, cy - 3, facing, phase, phantom_form)

    def _draw_long_hair(surface, cx, cy, facing, phase):
        """Long flowing black hair."""
        sway = math.sin(phase * 0.7) * 1

        # Hair on top and sides (flowing down back).
        # Top of head.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_darkest"], [
            (cx - 5, cy - 5),
            (cx - 5, cy - 7),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 5, cy - 7),
            (cx + 6, cy - 5),
            (cx + 5, cy - 3),
            (cx - 5, cy - 3),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_dark"], [
            (cx - 4, cy - 5),
            (cx - 4, cy - 6),
            (cx - 1, cy - 7),
            (cx + 2, cy - 7),
            (cx + 4, cy - 6),
            (cx + 5, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_mid"], [
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_morvein.PALETTE["hair_light"],
                         (cx - 1, cy - 6, 2, 1))

        # Side hair (flowing down past shoulders).
        for side in (-1, 1):
            side_x = cx + side * 5
            side_pts = [
                (side_x, cy - 4),
                (side_x + side * 2, cy - 2 + int(sway)),
                (side_x + side * 3, cy + 3 + int(sway)),
                (side_x + side * 2, cy + 8 + int(sway)),
                (side_x, cy + 6),
                (side_x - side * 1, cy),
            ]
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_darkest"], side_pts)
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_dark"], [
                (side_x, cy - 3),
                (side_x + side * 1, cy - 1 + int(sway)),
                (side_x + side * 2, cy + 3 + int(sway)),
                (side_x + side * 1, cy + 6 + int(sway)),
                (side_x - side * 0, cy + 5),
            ])
            _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_mid"], [
                (side_x, cy - 2),
                (side_x + side * 1, cy + 2 + int(sway)),
                (side_x, cy + 4),
            ])

        # Front bangs covering forehead partially.
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_dark"], [
            (cx - 3, cy - 5),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 3, cy - 5),
        ])
        _NS_morvein._poly(surface, _NS_morvein.PALETTE["hair_darkest"], [
            (cx - 2, cy - 4),
            (cx - 1, cy - 3),
            (cx + 2, cy - 3),
        ])

    def _draw_knight_eyes(surface, cx, cy, facing, phase, phantom_form):
        """Piercing blue eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_morvein.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_socket"],
                             (ex, ey - 1, 1, 2))

            # Eye glow.
            for r in range(3, 0, -1):
                alpha = _NS_morvein._alpha(160 * pulse * (3 - r) / 3)
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)

            pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_mid"], (ex, ey, 1, 1))
            if phantom_form:
                pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_glow"], (ex, ey, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_morvein.PALETTE["eye_light"], (ex, ey, 1, 1))

    # ============================================================
    # LANCE SLASH (melee thrust effect)
    # ============================================================
    def _draw_lance_slash(surface, boss, x, y, progress):
        """Thrust and slash line trail during attack."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction

        # Thrust phase (0.35-0.55): forward piercing line.
        if progress < 0.55:
            t = (progress - 0.35) / 0.20
            intensity = math.sin(t * math.pi)

            if hasattr(_NS_morvein, "_lance_tip"):
                tip_x, tip_y = _NS_morvein._lance_tip
            else:
                tip_x = x + facing * 40
                tip_y = y

            # Forward piercing energy trail.
            trail_len = int(20 * t)
            end_x = tip_x + facing * trail_len
            end_y = tip_y

            for w, alpha_val in [(6, 80), (4, 140), (2, 200), (1, 255)]:
                actual_alpha = _NS_morvein._alpha(alpha_val * intensity)
                pygame.draw.line(surface, (*_NS_morvein.PALETTE["crystal_light"], actual_alpha),
                                 (tip_x, tip_y), (end_x, end_y), w)

            # Bright piercing tip.
            for r in range(6, 0, -1):
                alpha = _NS_morvein._alpha(200 * intensity * (6 - r) / 6)
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_hot"], alpha),
                                        (end_x, end_y), r)
            _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["crystal_shine"],
                                    (end_x, end_y), 2)
            pygame.draw.rect(surface, _NS_morvein.PALETTE["white"], (end_x, end_y, 1, 1))

            # Sparks flying.
            for i in range(6):
                spark_angle = i * math.pi / 3
                spark_dist = 5 + i
                sx = end_x + int(math.cos(spark_angle) * spark_dist)
                sy = end_y + int(math.sin(spark_angle) * spark_dist)
                spark_alpha = _NS_morvein._alpha(220 * intensity - i * 20)
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_hot"], spark_alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], spark_alpha),
                                 (sx, sy, 1, 1))

        # Recovery phase - lingering trail (0.55-0.75).
        else:
            t = (progress - 0.55) / 0.20
            alpha = _NS_morvein._alpha(200 * (1 - t))
            if hasattr(_NS_morvein, "_lance_tip"):
                tip_x, tip_y = _NS_morvein._lance_tip
                for i in range(5):
                    trail_dist = 20 - i * 4
                    tx = tip_x + facing * trail_dist
                    ty = tip_y
                    a = _NS_morvein._alpha(alpha * (1 - i * 0.2))
                    _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_mid"], a),
                                            (tx, ty), max(1, 3 - i))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((160, 28), pygame.SRCALPHA)
        w = int(120 * pulse)
        h = int(13 * pulse)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (80 - w // 2 - radius, 14 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (5, 10, 25, 170),
                            (80 - w // 2, 14 - h // 2, w, h))
        surface.blit(shadow, (x - 80, y - 14))

    def _draw_phantom_wisps(surface, cx, cy, phase, intense=False):
        """Blue spectral wisps."""
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 32 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_morvein._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["phantom_darkest"], alpha),
                                    (sx, sy), 3)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["phantom_dark"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_morvein.PALETTE["phantom_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvein.PALETTE["phantom_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(8):
            spark_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 26)
            alpha = _NS_morvein._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_phantom_aura(surface, x, y, phase, phantom_form):
        """Spectral blue aura background."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_morvein._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvein._aacircle(aura, (*_NS_morvein.PALETTE["phantom_darkest"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_morvein._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvein._aacircle(aura, (*_NS_morvein.PALETTE["phantom_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_morvein._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_morvein._aacircle(aura, (*_NS_morvein.PALETTE["phantom_mid"], alpha),
                                        (110, 90), radius)

        # Extra brightness for phantom form.
        if phantom_form:
            for radius in range(45, 5, -3):
                alpha = _NS_morvein._alpha((45 - radius) * 1.5 * pulse)
                if alpha > 0:
                    _NS_morvein._aacircle(aura, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                            (110, 90), radius)

        surface.blit(aura, (x - 110, y - 90))

        # Orbiting spectral particles.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_morvein.PALETTE["phantom_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvein.PALETTE["crystal_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Blue ground ring with crystal runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvein.PALETTE["phantom_darkest"], 200),
                            (5, 18, 170, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_morvein.PALETTE["phantom_dark"], 220),
                            (14, 20, 152, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_morvein.PALETTE["phantom_mid"], 230),
                            (25, 22, 130, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 47)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morvein.PALETTE["crystal_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_morvein.PALETTE["crystal_hot"],
                                        _NS_morvein._alpha(150 * pulse)),
                                (15, 12, 150, 38), 1)
        surface.blit(ring, (x - 90, y - 27))

    # ============================================================
    # SKILL Q: PUNCTURE (piercing lance beam with pull)
    # ============================================================
    def _draw_puncture_ground(surface, boss, x, y, timer, phase):
        pass

    def _draw_puncture_foreground(surface, boss, x, y, timer, phase):
        """Long piercing lance energy beam pulling target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvein._target_position(boss, x, y)

        if hasattr(_NS_morvein, "_lance_tip"):
            start_x, start_y = _NS_morvein._lance_tip
        else:
            start_x = x + facing * 40
            start_y = y - 5

        if progress < 0.2:
            # Charge.
            t = progress / 0.2
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morvein._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                        (start_x, start_y), r)
            _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["crystal_hot"],
                                    (start_x, start_y), max(1, cr - 4))
            _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["white"],
                                    (start_x, start_y), max(1, cr - 6))
        else:
            # BEAM PUNCTURE.
            t = (progress - 0.2) / 0.8
            intensity = math.sin(t * math.pi)

            # Direction.
            dx = tx - start_x
            dy = ty - start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx = dx / length
                ny = dy / length
                end_x = int(start_x + nx * (length + 30))
                end_y = int(start_y + ny * (length + 30))
            else:
                end_x = tx + facing * 200
                end_y = ty
                nx, ny = facing, 0

            # Multi-layer piercing beam.
            for layer_i, (width, alpha_val) in enumerate([
                (12, 100), (8, 140), (5, 180), (3, 220), (1, 255),
            ]):
                actual_alpha = _NS_morvein._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_morvein.PALETTE["crystal_darkest"],
                    _NS_morvein.PALETTE["crystal_dark"],
                    _NS_morvein.PALETTE["crystal_mid"],
                    _NS_morvein.PALETTE["crystal_light"],
                    _NS_morvein.PALETTE["crystal_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (end_x, end_y), width)

            # Pulling arrows/chevrons back to caster (pulling effect).
            num_arrows = 5
            for i in range(num_arrows):
                arrow_t = (phase * 2 + i * 0.2) % 1.0
                # Arrows move from target toward caster (backward flow).
                px = int(tx + (start_x - tx) * arrow_t)
                py = int(ty + (start_y - ty) * arrow_t)
                arrow_alpha = _NS_morvein._alpha(220 * intensity * (1 - arrow_t * 0.3))

                # Chevron pointing toward caster (opposite of beam direction).
                chev_size = 3
                # Perpendicular for chevron wings.
                pygame.draw.line(surface,
                                 (*_NS_morvein.PALETTE["crystal_hot"], arrow_alpha),
                                 (px, py),
                                 (px + int(ny * chev_size), py - int(nx * chev_size)),
                                 2)
                pygame.draw.line(surface,
                                 (*_NS_morvein.PALETTE["crystal_hot"], arrow_alpha),
                                 (px, py),
                                 (px - int(ny * chev_size), py + int(nx * chev_size)),
                                 2)
                pygame.draw.rect(surface,
                                 (*_NS_morvein.PALETTE["crystal_shine"], arrow_alpha),
                                 (px, py, 2, 2))

            # Bright source.
            for r in range(10, 2, -1):
                alpha = _NS_morvein._alpha(180 * intensity * (10 - r) / 10)
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                        (start_x, start_y), r)
            _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["crystal_shine"],
                                    (start_x, start_y), 4)
            _NS_morvein._aacircle(surface, _NS_morvein.PALETTE["white"],
                                    (start_x, start_y), 2)

            # Impact.
            impact_r = int(12 + t * 20)
            impact_alpha = _NS_morvein._alpha(240 * intensity)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_darkest"], impact_alpha),
                                    (tx, ty), impact_r + 3, 3)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_dark"], impact_alpha),
                                    (tx, ty), impact_r, 3)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_mid"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 5), 2)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_hot"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 10), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], impact_alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: VIOLENT STRIKE (wide arc slash)
    # ============================================================
    def _draw_violentstrike_ground(surface, boss, x, y, timer, phase):
        # No ground effect for arc slash.
        pass

    def _draw_violentstrike_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Big crescent arc sweep in front.
        if progress > 0.2 and progress < 0.9:
            t = (progress - 0.2) / 0.7
            intensity = math.sin(t * math.pi)

            center_x = x + facing * 8
            center_y = y + 3
            radius = 40  # Wide arc.

            start_angle = -math.pi * 0.9 * facing
            end_angle = math.pi * 0.5 * facing
            current_angle = start_angle + (end_angle - start_angle) * t

            # Thick multi-layer crescent arc.
            num_segs = 24
            for i in range(num_segs):
                seg_t = i / num_segs
                seg_angle = start_angle + (current_angle - start_angle) * seg_t

                for r_offset in range(-4, 5):
                    seg_x = center_x + int(math.cos(seg_angle) * (radius + r_offset)) * facing
                    seg_y = center_y + int(math.sin(seg_angle) * (radius + r_offset))
                    alpha_layer = _NS_morvein._alpha(200 * intensity * seg_t *
                                                      (5 - abs(r_offset)) / 5)
                    if alpha_layer > 0:
                        if abs(r_offset) <= 1:
                            color = _NS_morvein.PALETTE["crystal_hot"]
                        elif abs(r_offset) <= 2:
                            color = _NS_morvein.PALETTE["crystal_light"]
                        else:
                            color = _NS_morvein.PALETTE["crystal_mid"]
                        pygame.draw.rect(surface, (*color, alpha_layer),
                                         (seg_x, seg_y, 2, 2))

            # Bright leading edge.
            for i in range(8):
                edge_t = 1 - i * 0.06
                edge_angle = start_angle + (current_angle - start_angle) * edge_t
                ex1 = center_x + int(math.cos(edge_angle) * (radius - 5)) * facing
                ey1 = center_y + int(math.sin(edge_angle) * (radius - 5))
                ex2 = center_x + int(math.cos(edge_angle) * (radius + 6)) * facing
                ey2 = center_y + int(math.sin(edge_angle) * (radius + 6))
                e_alpha = _NS_morvein._alpha(240 * intensity * (1 - i * 0.1))
                pygame.draw.line(surface, (*_NS_morvein.PALETTE["crystal_shine"], e_alpha),
                                 (ex1, ey1), (ex2, ey2), 2)
                pygame.draw.line(surface, (*_NS_morvein.PALETTE["white"], e_alpha),
                                 (ex1, ey1), (ex2, ey2), 1)

            # Sparks flying off.
            for i in range(12):
                sp_angle = current_angle + i * 0.1 * facing
                sp_dist = radius + 5 + i
                sx = center_x + int(math.cos(sp_angle) * sp_dist) * facing
                sy = center_y + int(math.sin(sp_angle) * sp_dist)
                sp_alpha = _NS_morvein._alpha(230 - i * 15)
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_hot"], sp_alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], sp_alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: SPECTRAL CHARGE (dash forward)
    # ============================================================
    def _draw_spectralcharge_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvein._target_position(boss, x, y)

        # Ground charge trail (fading blue streaks).
        num_streaks = 12
        for i in range(num_streaks):
            t = i / num_streaks
            trail_visible = progress > t * 0.7
            if not trail_visible:
                continue

            arc_x = int(x + (tx - x) * t)
            arc_y = int(y + (ty - y) * t) + 30

            fade = max(0, 1 - (progress - t * 0.7) * 2)
            alpha = _NS_morvein._alpha(200 * fade)
            if alpha <= 0:
                continue

            # Streak lines.
            for streak_off in (-3, 0, 3):
                pygame.draw.line(surface,
                                 (*_NS_morvein.PALETTE["phantom_mid"], alpha),
                                 (arc_x - facing * 8, arc_y + streak_off),
                                 (arc_x + facing * 3, arc_y + streak_off), 1)
                pygame.draw.line(surface,
                                 (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                 (arc_x - facing * 4, arc_y + streak_off),
                                 (arc_x + facing * 2, arc_y + streak_off), 1)

    def _draw_spectralcharge_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvein._target_position(boss, x, y)

        # Show phantom horse silhouette dashing.
        if progress < 0.85:
            t = progress / 0.85
            dash_x = int(x + (tx - x) * t)
            dash_y = int(y + (ty - y) * t)

            # Motion blur trail (multiple ghost images).
            for i in range(6):
                blur_t = max(0.0, t - i * 0.05)
                bx = int(x + (tx - x) * blur_t)
                by = int(y + (ty - y) * blur_t)
                alpha = _NS_morvein._alpha(180 - i * 25)

                # Simplified horse silhouette.
                horse_w = 18
                horse_h = 8
                pygame.draw.ellipse(surface,
                                    (*_NS_morvein.PALETTE["phantom_dark"], alpha),
                                    (bx - horse_w, by - horse_h // 2,
                                     horse_w * 2, horse_h))
                pygame.draw.ellipse(surface,
                                    (*_NS_morvein.PALETTE["phantom_mid"], alpha),
                                    (bx - horse_w + 2, by - horse_h // 2 + 1,
                                     horse_w * 2 - 4, horse_h - 2))

                # Head bump.
                pygame.draw.ellipse(surface,
                                    (*_NS_morvein.PALETTE["phantom_dark"], alpha),
                                    (bx + facing * horse_w - 4, by - 3, 8, 5))

                # Sparks around.
                for s in range(3):
                    spark_angle = phase * 5 + s * math.pi * 2 / 3
                    spark_x = bx + int(math.cos(spark_angle) * (horse_w + 3))
                    spark_y = by + int(math.sin(spark_angle) * 5)
                    pygame.draw.rect(surface,
                                     (*_NS_morvein.PALETTE["crystal_hot"], alpha),
                                     (spark_x, spark_y, 2, 2))

            # Bright leading energy blade.
            for r in range(8, 1, -1):
                alpha = _NS_morvein._alpha(200 * (8 - r) / 8)
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_light"], alpha),
                                        (dash_x + facing * 20, dash_y), r)
            pygame.draw.rect(surface, _NS_morvein.PALETTE["white"],
                             (dash_x + facing * 20, dash_y, 1, 1))
        else:
            # Impact at end.
            t = (progress - 0.85) / 0.15
            radius = int(15 + t * 25)
            alpha = _NS_morvein._alpha(240 * (1 - t))
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_mid"], alpha),
                                    (tx, ty), radius, 2)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["crystal_hot"], alpha),
                                    (tx, ty), max(1, radius - 8), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL R: PHANTOM SUMMONING (transform phantom)
    # ============================================================
    def _draw_phantom_foreground(surface, boss, x, y, timer, phase):
        """Phantom form effects around boss."""
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))

        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Rising spectral flames around boss.
        for i in range(12):
            t = (phase * 0.4 + i * 0.08) % 1.0
            angle = i * math.pi / 6 + phase * 0.2
            r = 35 + int(math.sin(phase + i) * 5)
            fx = x + int(math.cos(angle) * r)
            fy = y + int(math.sin(angle) * r * 0.4) + 20
            fy -= int(t * 50)  # Rise up.
            alpha = _NS_morvein._alpha(230 * (1 - t) * pulse)
            if alpha > 0:
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["phantom_dark"], alpha),
                                        (fx, fy), 3)
                _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["phantom_mid"], alpha),
                                        (fx, fy), 2)
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_hot"], alpha),
                                 (fx, fy, 1, 1))
                pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], alpha),
                                 (fx, fy, 1, 1))

        # Phantom form crystal sparkles.
        for i in range(15):
            angle = phase * 1.5 + i * math.pi / 7
            r = 40 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r * 0.5)
            alpha = _NS_morvein._alpha(230 * pulse)
            pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_morvein.PALETTE["crystal_shine"], alpha),
                             (sx, sy, 1, 1))

        # Spectral trail behind (motion trail even when idle).
        facing = boss.direction
        for i in range(4):
            trail_x = x - facing * (i + 1) * 8
            trail_y = y + int(math.sin(phase * 2 + i) * 2)
            trail_alpha = _NS_morvein._alpha(150 - i * 30)
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["phantom_mid"], trail_alpha),
                                    (trail_x, trail_y), max(1, 5 - i))
            _NS_morvein._aacircle(surface, (*_NS_morvein.PALETTE["phantom_light"], trail_alpha),
                                    (trail_x, trail_y), max(1, 3 - i))


# ====================================================================
# thorvak.py
# ====================================================================



class _NS_thorvak:
    """Namespace thorvak - Ancient Grovewarden treant tank (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Wood/bark (main body)
        "bark_darkest": (18, 12, 8),
        "bark_dark": (55, 40, 22),
        "bark_mid": (95, 70, 40),
        "bark_light": (150, 115, 65),
        "bark_edge": (200, 165, 95),

        # Dark inner wood
        "wood_darkest": (10, 6, 4),
        "wood_dark": (30, 20, 10),

        # Nature green (leaves, glow, veins)
        "nat_darkest": (5, 25, 8),
        "nat_dark": (20, 70, 25),
        "nat_mid": (60, 155, 50),
        "nat_light": (130, 220, 90),
        "nat_hot": (200, 255, 140),
        "nat_shine": (240, 255, 200),

        # Toxic bright green (energy)
        "energy_dark": (15, 100, 30),
        "energy_mid": (60, 200, 60),
        "energy_bright": (150, 255, 100),
        "energy_hot": (220, 255, 180),

        # Eye glow
        "eye_socket": (2, 8, 3),
        "eye_dark": (10, 60, 15),
        "eye_mid": (60, 200, 60),
        "eye_light": (180, 255, 130),
        "eye_glow": (240, 255, 200),

        # Vines (darker green)
        "vine_dark": (25, 55, 20),
        "vine_mid": (70, 130, 45),
        "vine_light": (140, 200, 90),

        # Moss (yellowish-green)
        "moss_dark": (60, 80, 25),
        "moss_mid": (120, 150, 55),
        "moss_light": (180, 210, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 1),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thorvak._clamp(color)
        if _NS_thorvak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_thorvak._clamp(color)
        if _NS_thorvak.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_thorvak._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_thorvak._clamp(color), points)

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
        return int(x + 120 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thorvak(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_thorvak._update_thv_attack_anim(boss)
        attacking = (
            getattr(boss, "_thv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_thorvak._draw_nature_aura(surface, x, y, pulse)
        _NS_thorvak._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        _NS_thorvak._draw_falling_leaves(surface, x, y, pulse)

        # Skill ground FX.
        if active_skill == "e":
            _NS_thorvak._draw_vengeance_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thorvak._draw_natureswrath_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorvak._draw_dryad_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_thorvak._draw_seed_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_thorvak._draw_thv_attack(surface, boss, x, y)
        else:
            _NS_thorvak._draw_thv_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_thorvak._draw_seed_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thorvak._draw_natureswrath_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorvak._draw_vengeance_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorvak._draw_dryad_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_thv_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_thv_previous_timer", 0))
        active = bool(getattr(boss, "_thv_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._thv_attack_active = True
            boss._thv_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._thv_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._thv_attack_frame = int(
                getattr(boss, "_thv_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._thv_attack_active = False
            boss._thv_attack_frame = 0
            active = False

        boss._thv_previous_timer = timer
        boss._thv_attack_progress = (
            min(1.0, getattr(boss, "_thv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_thv_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_thorvak._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_thorvak._draw_nature_wisps(surface, x, y + 45, boss.pulse)
        _NS_thorvak._draw_thv_body(surface, x, y + bob, boss.direction,
                                     boss.pulse, "idle")

    def _draw_thv_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_thv_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_thv_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.5) * 4)
        # Wind up → sweep → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lean = int(t * -3) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 8)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_thorvak._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_thorvak._draw_nature_wisps(surface, x + lean, y + 45, boss.pulse, intense=True)
        _NS_thorvak._draw_thv_body(surface, x + lean, y + bob - lift,
                                     facing, boss.pulse, "attack",
                                     progress)
        _NS_thorvak._draw_swing_arc(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (wooden titan)
    # ============================================================
    def _draw_thv_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Legs (wooden trunk).
        _NS_thorvak._draw_treant_legs(surface, cx, cy + 12, facing, phase)

        # Torso (bark armor with core).
        _NS_thorvak._draw_treant_torso(surface, cx, cy, facing, phase)

        # Back arm.
        _NS_thorvak._draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress)

        # Head with antlers.
        _NS_thorvak._draw_treant_head(surface, cx, cy - 20, facing, phase)

        # Front arm (swing arm) - last.
        _NS_thorvak._draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress)

    def _draw_treant_legs(surface, cx, cy, facing, phase):
        """Wooden trunk legs with root base."""
        sway = math.sin(phase * 0.4) * 1

        # Wide root/trunk base.
        base_pts = [
            (cx - 13, cy - 6),
            (cx + 13, cy - 6),
            (cx + 16, cy + 4),
            (cx + 14, cy + 12),
            (cx + 9, cy + 18),
            (cx - 9, cy + 18),
            (cx - 14, cy + 12),
            (cx - 16, cy + 4),
        ]
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in base_pts])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_darkest"], base_pts)

        # Main bark color.
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_dark"], [
            (cx - 12, cy - 5),
            (cx + 12, cy - 5),
            (cx + 15, cy + 4),
            (cx + 13, cy + 11),
            (cx + 8, cy + 17),
            (cx - 8, cy + 17),
            (cx - 13, cy + 11),
            (cx - 15, cy + 4),
        ])

        # Mid bark texture.
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_mid"], [
            (cx - 10, cy - 3),
            (cx + 10, cy - 3),
            (cx + 13, cy + 3),
            (cx + 11, cy + 10),
            (cx + 6, cy + 15),
            (cx - 6, cy + 15),
            (cx - 11, cy + 10),
            (cx - 13, cy + 3),
        ])

        # Bark grain lines (vertical wood texture).
        for x_off in (-9, -4, 0, 4, 9):
            grain_x = cx + x_off + int(sway)
            pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_darkest"],
                             (grain_x, cy - 4),
                             (grain_x + int(x_off * 0.15), cy + 15), 1)
            pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_edge"],
                             (grain_x + 1, cy - 4),
                             (grain_x + 1 + int(x_off * 0.15), cy + 15), 1)

        # Central emblem (nature core).
        emblem_y = cy + 5
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["wood_darkest"],
                               (cx, emblem_y), 4)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_darkest"],
                               (cx, emblem_y), 3)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_dark"],
                               (cx, emblem_y), 2)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_mid"],
                               (cx, emblem_y), 1)

        # Emblem glow.
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(6, 1, -1):
            alpha = _NS_thorvak._alpha(100 * pulse * (6 - r) / 6)
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                    (cx, emblem_y), r)

        # ROOTS extending down and out.
        _NS_thorvak._draw_roots(surface, cx, cy + 17, phase)

        # Moss on bottom edges.
        for i in (-8, -4, 3, 7):
            moss_x = cx + i
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["moss_dark"],
                             (moss_x - 1, cy + 15, 3, 2))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["moss_mid"],
                             (moss_x, cy + 15, 2, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["moss_light"],
                             (moss_x, cy + 15, 1, 1))

    def _draw_roots(surface, cx, cy, phase):
        """Wooden roots hanging below body (floating effect)."""
        sway = math.sin(phase * 0.6) * 2

        # 3 main root strands going down.
        for i, (start_off, curl) in enumerate([
            (-8, -2), (0, 0), (8, 2),
        ]):
            base_x = cx + start_off
            base_y = cy
            end_x = base_x + curl + int(sway * 0.3)
            end_y = cy + 12

            # Draw as curve.
            prev = (base_x, base_y)
            for step in range(1, 5):
                t = step / 4
                rx = int(base_x + (end_x - base_x) * t)
                ry = int(base_y + (end_y - base_y) * t)
                # Wave.
                rx += int(math.sin(phase + i + t * 2) * 2)
                thickness = max(1, 4 - step)

                _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                                     (prev[0] + 1, prev[1] + 1),
                                     (rx + 1, ry + 1), thickness + 1)
                _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                                     prev, (rx, ry), thickness)
                _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                                     prev, (rx, ry), max(1, thickness - 1))
                _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_mid"],
                                     (prev[0], prev[1] - 1), (rx, ry - 1),
                                     max(1, thickness - 2))
                prev = (rx, ry)

            # Green glow at root tip.
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_light"],
                             (end_x, end_y, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"],
                             (end_x, end_y, 1, 1))

    def _draw_treant_torso(surface, cx, cy, facing, phase):
        """Massive bark chest with glowing green core."""
        # Torso shape.
        torso_pts = [
            (cx - 14, cy - 5),
            (cx - 11, cy + 6),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 11, cy + 6),
            (cx + 14, cy - 5),
            (cx + 12, cy - 8),
            (cx - 12, cy - 8),
        ]
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_darkest"], torso_pts)

        # Main chest bark.
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_dark"], [
            (cx - 12, cy - 6),
            (cx + 12, cy - 6),
            (cx + 11, cy + 7),
            (cx - 11, cy + 7),
        ])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_mid"], [
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 9, cy + 5),
            (cx - 9, cy + 5),
        ])

        # Muscle definition (V-shape lines like wood ridges).
        pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_darkest"],
                         (cx, cy - 4), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_darkest"],
                         (cx, cy - 4), (cx + 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (cx - 1, cy - 3), (cx - 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (cx + 1, cy - 3), (cx + 4, cy + 5), 1)

        # Bark cracks (small horizontal).
        for i, y_off in enumerate([-3, 0, 3]):
            crack_x = cx - 8 + (i * 5) % 16
            pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_darkest"],
                             (crack_x, cy + y_off),
                             (crack_x + 4, cy + y_off), 1)

        # BIG GLOWING GREEN CORE.
        pulse = math.sin(phase * 2) * 0.35 + 0.65
        core_x = cx
        core_y = cy + 1

        # Outer glow.
        for r in range(12, 2, -1):
            alpha = _NS_thorvak._alpha(140 * pulse * (12 - r) / 12)
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                    (core_x, core_y), r)

        # Core outline (bark ring).
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["wood_darkest"],
                               (core_x, core_y), 5)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["bark_dark"],
                               (core_x, core_y), 5, 1)

        # Core inner glow.
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_darkest"],
                               (core_x, core_y), 4)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_dark"],
                               (core_x, core_y), 3)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_mid"],
                               (core_x, core_y), 2)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_hot"],
                               (core_x, core_y), 1)
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["white"],
                         (core_x, core_y, 1, 1))

        # Leaf/vein rays radiating from core.
        for i in range(6):
            ray_angle = phase * 0.5 + i * math.pi / 3
            rx = core_x + int(math.cos(ray_angle) * 8)
            ry = core_y + int(math.sin(ray_angle) * 8)
            alpha = _NS_thorvak._alpha(180 * pulse)
            pygame.draw.line(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                             (core_x, core_y), (rx, ry), 1)

        # PAULDRONS (bark shoulder pads with spikes/leaves).
        for side in (-1, 1):
            _NS_thorvak._draw_bark_pauldron(surface, cx + side * 13, cy - 4, side, phase)

        # Vines wrapping around torso.
        _NS_thorvak._draw_vines_on_torso(surface, cx, cy, phase)

    def _draw_bark_pauldron(surface, cx, cy, side, phase):
        """Bark shoulder pauldron with jutting spikes and leaves."""
        # Main pauldron.
        paul_pts = [
            (cx - 5, cy),
            (cx - 4, cy - 5),
            (cx - 1, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 5),
            (cx + 6, cy),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ]
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_darkest"], paul_pts)

        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_dark"], [
            (cx - 4, cy),
            (cx - 3, cy - 4),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_mid"], [
            (cx - 3, cy - 1),
            (cx - 1, cy - 5),
            (cx + 2, cy - 5),
            (cx + 4, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (cx - 1, cy - 4, 3, 1))

        # 2 SPIKES on top (like broken branches).
        for spike_x_off in (-2, 2):
            spike_x = cx + spike_x_off
            spike_tip_y = cy - 11
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 1, cy - 6),
                (spike_x + 2, cy - 6),
            ])
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, cy - 6),
                (spike_x + 2, cy - 6),
            ])
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_dark"], [
                (spike_x, spike_tip_y),
                (spike_x, cy - 6),
                (spike_x + 1, cy - 6),
            ])
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_mid"], [
                (spike_x, spike_tip_y),
                (spike_x, cy - 8),
                (spike_x + 1, cy - 8),
            ])
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                             (spike_x, spike_tip_y, 1, 1))

            # Green glow tip.
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"],
                             (spike_x, spike_tip_y, 1, 1))

        # Leaf on pauldron.
        leaf_x = cx + side * 2
        leaf_y = cy - 2
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["nat_darkest"], [
            (leaf_x, leaf_y - 2),
            (leaf_x - 2, leaf_y),
            (leaf_x, leaf_y + 2),
            (leaf_x + 2, leaf_y),
        ])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["nat_dark"], [
            (leaf_x, leaf_y - 1),
            (leaf_x - 1, leaf_y),
            (leaf_x, leaf_y + 1),
            (leaf_x + 1, leaf_y),
        ])
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"],
                         (leaf_x, leaf_y, 1, 1))

        # Rune glow.
        pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
        rune_alpha = _NS_thorvak._alpha(200 * pulse)
        pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_mid"], rune_alpha),
                         (cx - 1, cy + 1, 3, 1))
        pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], rune_alpha),
                         (cx, cy + 1, 1, 1))

    def _draw_vines_on_torso(surface, cx, cy, phase):
        """Vines wrapping around torso."""
        sway = math.sin(phase * 0.8) * 1

        # Diagonal vine across chest.
        for i in range(4):
            t = i / 3
            vx = int(cx - 8 + t * 16 + sway * t)
            vy = int(cy - 4 + t * 8)
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["vine_dark"],
                             (vx, vy, 2, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["vine_mid"],
                             (vx, vy, 1, 1))

        # Small leaves along vine.
        for i in (1, 3):
            t = i / 3
            vx = int(cx - 8 + t * 16 + sway * t)
            vy = int(cy - 4 + t * 8) - 1
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_dark"], (vx - 1, vy, 3, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"], (vx, vy, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (secondary)."""
        sway = math.sin(phase * 0.5) * 1

        if action == "attack":
            elbow_y_off = int(math.sin(attack_progress * math.pi) * -2)
            elbow_x_off = -int(math.sin(attack_progress * math.pi) * 3) * facing
        else:
            elbow_y_off = 4 + int(sway)
            elbow_x_off = 0

        shoulder_x = cx - facing * 12
        shoulder_y = cy - 2

        elbow_x = shoulder_x - facing * 3 + elbow_x_off
        elbow_y = shoulder_y + elbow_y_off + 3

        # Upper arm.
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 6)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_mid"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 2)

        # Forearm.
        hand_x = elbow_x - facing * 2
        hand_y = elbow_y + 6

        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 5)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 3)

        # Small leaves along arm.
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_dark"],
                         (elbow_x - 1, elbow_y - 3, 3, 1))
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"],
                         (elbow_x, elbow_y - 3, 1, 1))

        # Root-hand.
        _NS_thorvak._draw_root_hand(surface, hand_x, hand_y, facing, phase)

    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - swinging."""
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.2 + t * -math.pi * 0.5
                forearm_bend = 0.4
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.7 + t * math.pi * 1.1
                forearm_bend = 0.4 - t * 0.8
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.4 - t * math.pi * 0.6
                forearm_bend = -0.4 + t * 0.4
        else:
            arm_angle = -math.pi * 0.15 + math.sin(phase * 0.4) * 0.05
            forearm_bend = 0.5

        shoulder_x = cx + facing * 12
        shoulder_y = cy - 2

        arm_len = 9
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len) + 2

        forearm_len = 8
        forearm_angle = arm_angle + forearm_bend
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm (thick bark).
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 7)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_mid"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 3)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_edge"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 6)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_mid"],
                             (elbow_x, elbow_y - 1),
                             (hand_x, hand_y - 1), 2)

        # Elbow bark spike.
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_darkest"],
                         (elbow_x - 1, elbow_y - 3, 2, 3))
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (elbow_x, elbow_y - 2, 1, 2))

        # Leaves on arm.
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_dark"],
                         (int((shoulder_x + elbow_x) / 2) - 1,
                          int((shoulder_y + elbow_y) / 2) - 3, 3, 1))
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"],
                         (int((shoulder_x + elbow_x) / 2),
                          int((shoulder_y + elbow_y) / 2) - 3, 1, 1))

        # Root-hand (glowing during attack).
        _NS_thorvak._draw_root_hand(surface, hand_x, hand_y, facing, phase,
                                     glowing=(action == "attack"))

        # Store for swing arc.
        _NS_thorvak._front_hand = (hand_x, hand_y)

    def _draw_root_hand(surface, hx, hy, facing, phase, glowing=False):
        """Wooden hand made of gnarled roots."""
        # Base hand.
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["shadow_deep"],
                               (hx + 1, hy + 1), 5)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["bark_darkest"],
                               (hx, hy), 5)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["bark_dark"],
                               (hx, hy), 4)
        _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["bark_mid"],
                               (hx, hy), 3)
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (hx - 1, hy - 1, 2, 1))

        # Root-finger claws (3 spike claws).
        for finger_dx in (-2, 0, 2):
            claw_x = hx + finger_dx
            claw_tip_y = hy - 7
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"], [
                (claw_x + 1, claw_tip_y + 1),
                (claw_x - 1, hy - 3),
                (claw_x + 1, hy - 3),
            ])
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_darkest"], [
                (claw_x, claw_tip_y),
                (claw_x - 1, hy - 3),
                (claw_x + 1, hy - 3),
            ])
            _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_dark"], [
                (claw_x, claw_tip_y),
                (claw_x, hy - 3),
            ])
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                             (claw_x, claw_tip_y, 1, 1))

        # Glowing green rune on palm.
        if glowing:
            pulse = math.sin(phase * 3) * 0.4 + 0.6
            for r in range(5, 1, -1):
                alpha = _NS_thorvak._alpha(160 * pulse * (5 - r) / 5)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                        (hx, hy), r)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_hot"], (hx, hy), 1)
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_shine"], (hx, hy, 1, 1))

    def _draw_treant_head(surface, cx, cy, facing, phase):
        """Wooden head with antlers, moss beard, and glowing green eyes."""
        # Head base (rounded wooden).
        head_pts = [
            (cx - 7, cy + 4),
            (cx - 8, cy - 1),
            (cx - 6, cy - 6),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 6, cy - 6),
            (cx + 8, cy - 1),
            (cx + 7, cy + 4),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
        ]
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_darkest"], head_pts)

        # Main bark color.
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_dark"], [
            (cx - 6, cy + 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 5),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 5, cy - 5),
            (cx + 7, cy - 1),
            (cx + 6, cy + 3),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["bark_mid"], [
            (cx - 5, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ])

        # Wooden face highlights.
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (cx - 1, cy - 5, 3, 1))
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_edge"],
                         (cx, cy - 5, 1, 1))

        # Wood grain lines on face.
        pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_darkest"],
                         (cx - 4, cy - 2), (cx + 4, cy - 2), 1)
        pygame.draw.line(surface, _NS_thorvak.PALETTE["bark_darkest"],
                         (cx - 5, cy + 2), (cx + 5, cy + 2), 1)

        # EYES (glowing green).
        _NS_thorvak._draw_treant_eyes(surface, cx, cy - 2, facing, phase)

        # NOSE (small wooden knob).
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_darkest"],
                         (cx - 1, cy, 2, 2))
        pygame.draw.rect(surface, _NS_thorvak.PALETTE["bark_mid"],
                         (cx - 1, cy, 1, 1))

        # MOSS BEARD (below face).
        _NS_thorvak._draw_moss_beard(surface, cx, cy + 3, facing, phase)

        # ANTLERS (branch horns).
        _NS_thorvak._draw_antlers(surface, cx, cy - 6, facing, phase)

    def _draw_treant_eyes(surface, cx, cy, facing, phase):
        """Deep glowing green eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            # Deep socket.
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["eye_socket"],
                             (ex, ey - 1, 2, 2))

            # Eye glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_thorvak._alpha(160 * pulse * (4 - r) / 4)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                        (ex, ey), r)

            # Iris.
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["eye_dark"], (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["eye_glow"], (ex, ey, 1, 1))

    def _draw_moss_beard(surface, cx, cy, facing, phase):
        """Moss hanging down like a beard."""
        sway = math.sin(phase * 0.6) * 1

        beard_pts = [
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 5, cy + 3),
            (cx + 3 + int(sway), cy + 6),
            (cx + int(sway), cy + 7),
            (cx - 3 + int(sway), cy + 6),
            (cx - 5, cy + 3),
        ]
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["moss_dark"], beard_pts)
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["moss_mid"], [
            (cx - 3, cy + 1),
            (cx + 3, cy + 1),
            (cx + 4, cy + 3),
            (cx + int(sway), cy + 6),
            (cx - 4, cy + 3),
        ])
        _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["moss_light"], [
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + int(sway), cy + 5),
            (cx - 2, cy + 3),
        ])

        # Small leaves.
        for dx in (-3, 0, 3):
            leaf_x = cx + dx + int(sway * 0.5)
            leaf_y = cy + 4
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_dark"], (leaf_x, leaf_y, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"], (leaf_x, leaf_y, 1, 1))

    def _draw_antlers(surface, cx, cy, facing, phase):
        """Big branching antlers on top of head (like deer horns)."""
        beat = math.sin(phase * 1.2) * 1

        # Draw 2 main antlers (one each side).
        for side in (-1, 1):
            # Main branch going up-out.
            base_x = cx + side * 2
            base_y = cy
            mid_x = cx + side * 6
            mid_y = cy - 6
            tip_x = cx + side * 9
            tip_y = cy - 11 + int(beat * 0.5)

            # Main antler shaft.
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                                 (base_x + 1, base_y + 1),
                                 (mid_x + 1, mid_y + 1), 4)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                                 (base_x, base_y), (mid_x, mid_y), 4)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                                 (base_x, base_y), (mid_x, mid_y), 2)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_mid"],
                                 (base_x, base_y - 1),
                                 (mid_x, mid_y - 1), 1)

            # Upper part of antler.
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                                 (mid_x + 1, mid_y + 1),
                                 (tip_x + 1, tip_y + 1), 3)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                                 (mid_x, mid_y), (tip_x, tip_y), 3)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                                 (mid_x, mid_y), (tip_x, tip_y), 2)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_mid"],
                                 (mid_x, mid_y - 1),
                                 (tip_x, tip_y - 1), 1)

            # Branch 1: goes UP from mid.
            branch1_tip_x = mid_x + side * 3
            branch1_tip_y = mid_y - 5 + int(beat)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                                 (mid_x, mid_y), (branch1_tip_x, branch1_tip_y), 2)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                                 (mid_x, mid_y), (branch1_tip_x, branch1_tip_y), 1)
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_light"],
                             (branch1_tip_x, branch1_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"],
                             (branch1_tip_x, branch1_tip_y, 1, 1))

            # Branch 2: goes UP from tip.
            branch2_tip_x = tip_x + side * 2
            branch2_tip_y = tip_y - 4 + int(beat * 0.5)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_darkest"],
                                 (tip_x, tip_y), (branch2_tip_x, branch2_tip_y), 2)
            _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["bark_dark"],
                                 (tip_x, tip_y), (branch2_tip_x, branch2_tip_y), 1)
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_light"],
                             (branch2_tip_x, branch2_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"],
                             (branch2_tip_x, branch2_tip_y, 1, 1))

            # Main tip glow.
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_shine"],
                             (tip_x, tip_y - 1, 1, 1))

            # Small leaves along antler.
            for t_pos in (0.4, 0.7):
                leaf_x = int(base_x + (tip_x - base_x) * t_pos)
                leaf_y = int(base_y + (tip_y - base_y) * t_pos) - 1
                pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_dark"],
                                 (leaf_x, leaf_y, 1, 1))
                pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"],
                                 (leaf_x, leaf_y, 1, 1))

    # ============================================================
    # SWING ARC (melee attack)
    # ============================================================
    def _draw_swing_arc(surface, boss, x, y, progress):
        """Green nature energy sweep arc."""
        if progress < 0.35 or progress > 0.7:
            return

        facing = boss.direction
        swing_t = (progress - 0.35) / 0.25
        swing_t = max(0, min(1, swing_t))
        alpha_val = int(255 * (1 - abs(swing_t - 0.5) * 1.5))
        alpha_val = max(0, alpha_val)

        center_x = x + facing * 5
        center_y = y + 5
        arc_radius = 26

        start_angle = -math.pi * 0.85 * facing
        end_angle = math.pi * 0.3 * facing
        current_angle = start_angle + (end_angle - start_angle) * swing_t

        # Arc trail.
        num_segments = 14
        for i in range(num_segments):
            t = i / num_segments
            seg_angle = start_angle + (current_angle - start_angle) * t
            seg_x = center_x + int(math.cos(seg_angle) * arc_radius) * facing
            seg_y = center_y + int(math.sin(seg_angle) * arc_radius)
            seg_alpha = _NS_thorvak._alpha(alpha_val * t)
            size = int(2 + t * 4)

            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_darkest"], seg_alpha),
                                    (seg_x, seg_y), size)
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_dark"], seg_alpha),
                                    (seg_x, seg_y), max(1, size - 1))
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_mid"], seg_alpha),
                                    (seg_x, seg_y), max(1, size - 2))
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], seg_alpha),
                                    (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Bright edge.
        for i in range(6):
            edge_t = 1 - i * 0.1
            edge_angle = start_angle + (current_angle - start_angle) * edge_t
            ex1 = center_x + int(math.cos(edge_angle) * (arc_radius - 2)) * facing
            ey1 = center_y + int(math.sin(edge_angle) * (arc_radius - 2))
            ex2 = center_x + int(math.cos(edge_angle) * (arc_radius + 3)) * facing
            ey2 = center_y + int(math.sin(edge_angle) * (arc_radius + 3))
            e_alpha = _NS_thorvak._alpha(alpha_val * (1 - i * 0.15))
            pygame.draw.line(surface, (*_NS_thorvak.PALETTE["nat_hot"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 1)
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_shine"], e_alpha),
                             (ex2, ey2, 1, 1))

        # Leaves flying off.
        for i in range(6):
            leaf_angle = current_angle + i * 0.15 * facing
            leaf_dist = arc_radius + i * 3
            lx = center_x + int(math.cos(leaf_angle) * leaf_dist) * facing
            ly = center_y + int(math.sin(leaf_angle) * leaf_dist)
            leaf_alpha = _NS_thorvak._alpha(220 - i * 25)
            # Tiny leaf shape.
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_dark"], leaf_alpha),
                             (lx - 1, ly, 3, 1))
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_mid"], leaf_alpha),
                             (lx, ly, 1, 1))
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], leaf_alpha),
                             (lx, ly, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.15 + 0.85
        shadow = pygame.Surface((140, 25), pygame.SRCALPHA)
        w = int(110 * pulse)
        h = int(13 * pulse)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (70 - w // 2 - radius, 12 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (10, 20, 5, 160),
                            (70 - w // 2, 12 - h // 2, w, h))
        surface.blit(shadow, (x - 70, y - 12))

    def _draw_nature_wisps(surface, cx, cy, phase, intense=False):
        """Rising green energy wisps."""
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 32 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_thorvak._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_darkest"], alpha),
                                    (sx, sy), 3)
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(8):
            spark_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 26)
            alpha = _NS_thorvak._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_falling_leaves(surface, cx, cy, phase):
        """Small leaves gently falling around boss (ambient)."""
        for i in range(6):
            t = (phase * 0.3 + i * 0.17) % 1.0
            lx = cx - 40 + i * 15 + int(math.sin(phase * 0.5 + i) * 15)
            ly = cy - 40 + int(t * 90)
            rot_phase = phase * 2 + i
            alpha = _NS_thorvak._alpha(200 * (1 - t * 0.3))

            # Simple leaf shape.
            leaf_color = _NS_thorvak.PALETTE["nat_dark"] if i % 2 else _NS_thorvak.PALETTE["nat_mid"]
            if math.sin(rot_phase) > 0:
                # Horizontal orientation.
                pygame.draw.rect(surface, (*leaf_color, alpha), (lx - 1, ly, 3, 1))
                pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                 (lx, ly, 1, 1))
            else:
                # Vertical orientation.
                pygame.draw.rect(surface, (*leaf_color, alpha), (lx, ly - 1, 1, 3))
                pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                 (lx, ly, 1, 1))

    def _draw_nature_aura(surface, x, y, phase):
        """Green nature aura background."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_thorvak._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_thorvak._aacircle(aura, (*_NS_thorvak.PALETTE["nat_darkest"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_thorvak._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_thorvak._aacircle(aura, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_thorvak._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thorvak._aacircle(aura, (*_NS_thorvak.PALETTE["nat_mid"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Orbiting leaves/embers.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Green ground ring with vine runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thorvak.PALETTE["nat_darkest"], 200),
                            (5, 18, 160, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_thorvak.PALETTE["nat_dark"], 220),
                            (14, 20, 142, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_thorvak.PALETTE["nat_mid"], 230),
                            (25, 22, 120, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_thorvak.PALETTE["nat_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_thorvak.PALETTE["nat_hot"],
                                        _NS_thorvak._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q: SEED OF NATURE (projectile)
    # ============================================================
    def _draw_seed_ground(surface, boss, x, y, timer, phase):
        # Nothing on ground for Q.
        pass

    def _draw_seed_foreground(surface, boss, x, y, timer, phase):
        """Green seed projectile with trail."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_thorvak._target_position(boss, x, y)

        if hasattr(_NS_thorvak, "_front_hand"):
            start_x, start_y = _NS_thorvak._front_hand
        else:
            start_x = x + facing * 20
            start_y = y

        if progress < 0.15:
            # Charge in hand.
            t = progress / 0.15
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_thorvak._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_hot"],
                                    (start_x, start_y), max(1, cr - 4))
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_shine"],
                                    (start_x, start_y), max(1, cr - 6))
        else:
            # Flying projectile.
            t = (progress - 0.15) / 0.85
            t = min(1.0, t)
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Trail with vine-like curl.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_thorvak._alpha(240 - i * 22)

                size = max(1, 8 - i)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_darkest"], alpha),
                                        (px, py), size)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                        (px, py), max(1, size - 3))

                # Small leaves in trail.
                if i < 5 and i % 2 == 0:
                    leaf_x = px + int(math.sin(t * 6 + i) * 4)
                    leaf_y = py + int(math.cos(t * 6 + i) * 4)
                    pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                     (leaf_x - 1, leaf_y, 3, 1))
                    pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], alpha),
                                     (leaf_x, leaf_y, 1, 1))

            # Seed head (bright glowing sphere).
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_darkest"], (bx, by), 8)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_dark"], (bx, by), 6)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_mid"], (bx, by), 4)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_light"], (bx, by), 3)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_hot"], (bx, by), 2)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["white"], (bx, by, 1, 1))

            # Aura around seed.
            for r in range(14, 3, -2):
                alpha = _NS_thorvak._alpha(90 * (14 - r) / 14)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                        (bx, by), r)

            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(10 + st * 25)
                alpha = _NS_thorvak._alpha(240 * (1 - st))
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_mid"], alpha),
                                        (tx, ty), max(1, radius - 4), 2)
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_hot"], alpha),
                                        (tx, ty), max(1, radius - 10), 1)

                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_shine"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: NATURE'S WRATH (vines in fan)
    # ============================================================
    def _draw_natureswrath_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground scorching pattern in front (fan shape).
        if progress > 0.2:
            t = (progress - 0.2) / 0.8
            fan_radius = int(50 * t)
            # Ground marks in fan.
            for i in range(-3, 4):
                angle = i * 0.15
                fx = x + int(math.cos(angle) * fan_radius) * facing
                fy = y + 35 + int(math.sin(angle) * fan_radius * 0.3)
                alpha = _NS_thorvak._alpha(180 * (1 - t * 0.5))
                pygame.draw.ellipse(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                    (fx - 3, fy - 1, 6, 3))
                pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_mid"], alpha),
                                 (fx, fy, 1, 1))

    def _draw_natureswrath_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # VINES erupt in fan shape forward.
        if progress > 0.15:
            t = (progress - 0.15) / 0.85
            grow_t = min(1.0, t * 3)  # Vines grow fast.

            # Multiple vines in fan.
            num_vines = 7
            for i in range(num_vines):
                angle_offset = (i - num_vines // 2) * 0.18  # spread
                vine_angle = angle_offset

                # Vine grows from ground.
                vine_len = int(50 * grow_t)
                vine_base_x = x + facing * 15
                vine_base_y = y + 35

                # Curl up path.
                num_segments = 8
                prev_x = vine_base_x
                prev_y = vine_base_y
                for seg in range(1, num_segments + 1):
                    seg_t = seg / num_segments
                    # Vine goes out then curls up.
                    seg_dist = vine_len * seg_t
                    seg_x = vine_base_x + int(math.cos(vine_angle) * seg_dist) * facing
                    seg_y = vine_base_y + int(math.sin(vine_angle) * seg_dist * 0.3)
                    # Add curl upward.
                    seg_y -= int(seg_t * seg_t * 20)
                    # Wave.
                    seg_x += int(math.sin(phase * 3 + i + seg_t * 3) * 2)

                    thickness = max(1, 4 - seg)

                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                                         (prev_x + 1, prev_y + 1),
                                         (seg_x + 1, seg_y + 1), thickness + 1)
                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["nat_darkest"],
                                         (prev_x, prev_y), (seg_x, seg_y), thickness)
                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["nat_dark"],
                                         (prev_x, prev_y), (seg_x, seg_y),
                                         max(1, thickness - 1))
                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["nat_mid"],
                                         (prev_x, prev_y - 1),
                                         (seg_x, seg_y - 1), max(1, thickness - 2))

                    prev_x, prev_y = seg_x, seg_y

                # Thorns/spikes on vine tip.
                for spike_off in (-2, 0, 2):
                    sx = prev_x + spike_off
                    sy = prev_y - 4
                    _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["nat_darkest"], [
                        (sx, sy),
                        (prev_x + spike_off - 1, prev_y),
                        (prev_x + spike_off + 1, prev_y),
                    ])
                    _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["nat_mid"], [
                        (sx, sy),
                        (prev_x + spike_off, prev_y),
                    ])
                    pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"], (sx, sy, 1, 1))
                    pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_shine"], (sx, sy, 1, 1))

                # Bright glow at tip.
                for r in range(4, 0, -1):
                    alpha = _NS_thorvak._alpha(160 * (4 - r) / 4)
                    _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                            (prev_x, prev_y), r)

    # ============================================================
    # SKILL E: NATURE'S VENGEANCE (defense aura)
    # ============================================================
    def _draw_vengeance_ground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground rings pulsing.
        for i in range(2):
            r = int(30 + i * 12 + math.sin(phase * 2) * 3)
            alpha = _NS_thorvak._alpha(200 - i * 60)
            pygame.draw.ellipse(surface, (*_NS_thorvak.PALETTE["nat_mid"], alpha),
                                (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                (x - r + 2, y + 45 - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)

    def _draw_vengeance_foreground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Green defense bubble around boss.
        breath = math.sin(phase * 2) * 2
        r = 40 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_thorvak._aacircle(bubble, (*_NS_thorvak.PALETTE["nat_mid"], alpha_val),
                                    center, r - i, thickness)
            _NS_thorvak._aacircle(bubble, (*_NS_thorvak.PALETTE["nat_light"], alpha_val),
                                    center, r - i - 1, 1)

        # Rotating sparkles.
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_thorvak.PALETTE["nat_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_thorvak.PALETTE["nat_shine"], (sx, sy, 1, 1))

        # Leaves orbiting inside bubble.
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            inner_r = r - 10
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            alpha = _NS_thorvak._alpha(200)
            # Leaf.
            pygame.draw.rect(bubble, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                             (bx - 1, by, 3, 1))
            pygame.draw.rect(bubble, (*_NS_thorvak.PALETTE["nat_mid"], alpha), (bx, by, 1, 1))
            pygame.draw.rect(bubble, (*_NS_thorvak.PALETTE["nat_hot"], alpha), (bx, by, 1, 1))

        surface.blit(bubble, (x - r - 10, y - r - 10))

        # Reflect wave (pulsing outward).
        pulse_t = (phase * 0.8) % 1.0
        pulse_r = int(r + pulse_t * 15)
        pulse_alpha = _NS_thorvak._alpha(180 * (1 - pulse_t))
        if pulse_alpha > 0:
            _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_hot"], pulse_alpha),
                                    (x, y), pulse_r, 2)

    # ============================================================
    # SKILL R: WRATH OF DRYAD (thorny vines forward)
    # ============================================================
    def _draw_dryad_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground scorching in wider fan.
        if progress > 0.2:
            t = (progress - 0.2) / 0.8
            fan_radius = int(75 * t)
            for i in range(-5, 6):
                angle = i * 0.15
                fx = x + int(math.cos(angle) * fan_radius) * facing
                fy = y + 35 + int(math.sin(angle) * fan_radius * 0.3)
                alpha = _NS_thorvak._alpha(220 * (1 - t * 0.4))
                pygame.draw.ellipse(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                    (fx - 4, fy - 2, 8, 4))
                pygame.draw.ellipse(surface, (*_NS_thorvak.PALETTE["nat_mid"], alpha),
                                    (fx - 3, fy - 1, 6, 2))
                pygame.draw.rect(surface, (*_NS_thorvak.PALETTE["nat_hot"], alpha),
                                 (fx, fy, 1, 1))

    def _draw_dryad_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.2:
            # Charge (green energy gathering at chest).
            t = progress / 0.2
            cr = int(6 + t * 12)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_thorvak._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_dark"], alpha),
                                        (x, y), r)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_mid"], (x, y), cr - 2)
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_hot"],
                                    (x, y), max(1, cr - 4))
            _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_shine"],
                                    (x, y), max(1, cr - 6))
            pygame.draw.rect(surface, _NS_thorvak.PALETTE["white"], (x, y, 1, 1))

            # Charging sparks.
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = x + int(math.cos(angle) * (cr + 4))
                sy = y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"], (sx, sy, 1, 1))
        else:
            # HUGE thorny vines burst forward in wide fan.
            t = (progress - 0.2) / 0.8
            grow_t = min(1.0, t * 3)

            # Many vines in wide fan.
            num_vines = 11
            for i in range(num_vines):
                angle_offset = (i - num_vines // 2) * 0.14  # wider spread
                vine_angle = angle_offset

                vine_len = int(75 * grow_t)
                vine_base_x = x + facing * 15
                vine_base_y = y + 30

                num_segments = 10
                prev_x = vine_base_x
                prev_y = vine_base_y
                for seg in range(1, num_segments + 1):
                    seg_t = seg / num_segments
                    seg_dist = vine_len * seg_t
                    seg_x = vine_base_x + int(math.cos(vine_angle) * seg_dist) * facing
                    seg_y = vine_base_y + int(math.sin(vine_angle) * seg_dist * 0.3)
                    # Curl up more dramatically.
                    seg_y -= int(seg_t * seg_t * 30)
                    # Wave.
                    seg_x += int(math.sin(phase * 3 + i + seg_t * 3) * 2)

                    thickness = max(1, 5 - seg // 2)

                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["shadow_deep"],
                                         (prev_x + 1, prev_y + 1),
                                         (seg_x + 1, seg_y + 1), thickness + 1)
                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["nat_darkest"],
                                         (prev_x, prev_y), (seg_x, seg_y), thickness)
                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["nat_dark"],
                                         (prev_x, prev_y), (seg_x, seg_y),
                                         max(1, thickness - 1))
                    _NS_thorvak._aaline(surface, _NS_thorvak.PALETTE["nat_mid"],
                                         (prev_x, prev_y - 1),
                                         (seg_x, seg_y - 1), max(1, thickness - 2))

                    # Thorn on side of vine.
                    if seg % 2 == 0 and seg > 2:
                        thorn_side = 1 if seg % 4 == 0 else -1
                        thorn_x = seg_x + thorn_side * 2
                        thorn_y = seg_y - 1
                        pygame.draw.line(surface, _NS_thorvak.PALETTE["nat_darkest"],
                                         (seg_x, seg_y), (thorn_x, thorn_y), 1)
                        pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"],
                                         (thorn_x, thorn_y, 1, 1))

                    prev_x, prev_y = seg_x, seg_y

                # BIG THORN CLUSTER at vine tip.
                for thorn_angle_off in range(-2, 3):
                    thorn_a = math.pi * 0.5 + thorn_angle_off * 0.3
                    thorn_len = 5 + abs(thorn_angle_off)
                    ttx = prev_x + int(math.cos(thorn_a) * thorn_len * facing)
                    tty = prev_y - int(math.sin(thorn_a) * thorn_len)
                    _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["shadow_deep"], [
                        (ttx + 1, tty + 1),
                        (prev_x - 1, prev_y),
                        (prev_x + 1, prev_y),
                    ])
                    _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["nat_darkest"], [
                        (ttx, tty),
                        (prev_x - 1, prev_y),
                        (prev_x + 1, prev_y),
                    ])
                    _NS_thorvak._poly(surface, _NS_thorvak.PALETTE["nat_dark"], [
                        (ttx, tty),
                        (prev_x, prev_y),
                    ])
                    pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_hot"], (ttx, tty, 1, 1))
                    pygame.draw.rect(surface, _NS_thorvak.PALETTE["nat_shine"], (ttx, tty, 1, 1))

                # Bright glow at tip.
                for r in range(6, 0, -1):
                    alpha = _NS_thorvak._alpha(180 * (6 - r) / 6)
                    _NS_thorvak._aacircle(surface, (*_NS_thorvak.PALETTE["nat_light"], alpha),
                                            (prev_x, prev_y), r)
                _NS_thorvak._aacircle(surface, _NS_thorvak.PALETTE["nat_hot"],
                                        (prev_x, prev_y), 2)
                pygame.draw.rect(surface, _NS_thorvak.PALETTE["white"], (prev_x, prev_y, 1, 1))


# ====================================================================
# yamako.py
# ====================================================================



class _NS_yamako:
    """Namespace yamako - Primordial Woodshaper TRUE BOSS (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe/gi (dark green shinobi)
        "robe_darkest": (5, 15, 8),
        "robe_dark": (18, 45, 22),
        "robe_mid": (40, 85, 45),
        "robe_light": (85, 140, 90),
        "robe_edge": (140, 190, 140),

        # Wood/bark armor (brown)
        "wood_darkest": (18, 12, 5),
        "wood_dark": (55, 35, 15),
        "wood_mid": (100, 70, 30),
        "wood_light": (160, 120, 55),
        "wood_edge": (210, 170, 90),

        # Skin (weathered warrior)
        "skin_dark": (100, 75, 60),
        "skin_mid": (170, 135, 110),
        "skin_light": (220, 190, 165),
        "skin_shine": (245, 220, 195),

        # Hair (long black)
        "hair_darkest": (5, 5, 10),
        "hair_dark": (15, 15, 25),
        "hair_mid": (40, 40, 55),
        "hair_light": (85, 85, 105),

        # Chakra green (bright life energy)
        "chakra_darkest": (5, 40, 10),
        "chakra_dark": (20, 100, 30),
        "chakra_mid": (60, 190, 70),
        "chakra_light": (140, 240, 130),
        "chakra_hot": (200, 255, 170),
        "chakra_shine": (240, 255, 220),

        # Eye glow (fierce green)
        "eye_socket": (2, 15, 5),
        "eye_dark": (20, 80, 25),
        "eye_mid": (80, 200, 80),
        "eye_light": (180, 250, 150),
        "eye_glow": (240, 255, 220),

        # Headband metal (silver-grey)
        "band_dark": (35, 40, 50),
        "band_mid": (95, 105, 120),
        "band_light": (170, 180, 195),
        "band_shine": (235, 240, 250),

        # Sword blade (steel with green tint)
        "blade_dark": (25, 40, 30),
        "blade_mid": (85, 115, 95),
        "blade_light": (170, 200, 180),
        "blade_shine": (230, 245, 235),

        # Leaves/foliage
        "leaf_dark": (15, 60, 20),
        "leaf_mid": (55, 140, 55),
        "leaf_light": (130, 220, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 1),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_yamako._clamp(color)
        if _NS_yamako.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_yamako._clamp(color)
        if _NS_yamako.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_yamako._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_yamako._clamp(color), points)

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
        return int(x + 150 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_yamako(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_yamako._update_ym_attack_anim(boss)
        attacking = (
            getattr(boss, "_ym_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient (large for TRUE BOSS).
        _NS_yamako._draw_chakra_aura(surface, x, y, pulse)
        _NS_yamako._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        _NS_yamako._draw_falling_leaves(surface, x, y, pulse)

        # Skill ground FX.
        if active_skill == "q":
            _NS_yamako._draw_deepforest_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_yamako._draw_woodcreation_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_yamako._draw_woodgolem_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_yamako._draw_kannon_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_yamako._draw_ym_attack(surface, boss, x, y)
        else:
            _NS_yamako._draw_ym_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_yamako._draw_deepforest_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_yamako._draw_woodcreation_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_yamako._draw_woodgolem_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_yamako._draw_kannon_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_ym_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ym_previous_timer", 0))
        active = bool(getattr(boss, "_ym_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ym_attack_active = True
            boss._ym_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._ym_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._ym_attack_frame = int(
                getattr(boss, "_ym_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._ym_attack_active = False
            boss._ym_attack_frame = 0
            active = False

        boss._ym_previous_timer = timer
        boss._ym_attack_progress = (
            min(1.0, getattr(boss, "_ym_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_ym_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_yamako._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_yamako._draw_chakra_wisps(surface, x, y + 42, boss.pulse)
        _NS_yamako._draw_ym_body(surface, x, y + bob, boss.direction,
                                   boss.pulse, "idle")

    def _draw_ym_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_ym_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_ym_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.6) * 5)
        # Sword swing: wind up back → forward slash → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lean = int(t * -3) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lean = int((-3 + t * 9)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(6 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_yamako._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_yamako._draw_chakra_wisps(surface, x + lean, y + 42, boss.pulse, intense=True)
        _NS_yamako._draw_ym_body(surface, x + lean, y + bob - lift,
                                   facing, boss.pulse, "attack",
                                   progress)
        _NS_yamako._draw_sword_slash(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (shinobi humanoid)
    # ============================================================
    def _draw_ym_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Legs/hakama.
        _NS_yamako._draw_shinobi_legs(surface, cx, cy + 10, facing, phase)

        # Sword scabbard on back (visible behind).
        _NS_yamako._draw_scabbard(surface, cx, cy - 2, facing, phase)

        # Torso (gi with wood chest armor).
        _NS_yamako._draw_shinobi_torso(surface, cx, cy - 2, facing, phase)

        # Back arm.
        _NS_yamako._draw_back_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

        # Head.
        _NS_yamako._draw_shinobi_head(surface, cx, cy - 18, facing, phase)

        # Sword arm (front) - drawn last.
        _NS_yamako._draw_sword_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

    def _draw_shinobi_legs(surface, cx, cy, facing, phase):
        """Hakama (baggy pants) with wraps."""
        sway = math.sin(phase * 0.5) * 1

        # Hakama shape.
        legs_pts = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy + 4),
            (cx + 10 + int(sway), cy + 14),
            (cx + 6, cy + 20),
            (cx - 6, cy + 20),
            (cx - 10 - int(sway), cy + 14),
            (cx - 12, cy + 4),
        ]
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 3) for p in legs_pts])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["robe_darkest"], legs_pts)

        # Main hakama color.
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["robe_dark"], [
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 11, cy + 4),
            (cx + 9 + int(sway), cy + 13),
            (cx + 5, cy + 19),
            (cx - 5, cy + 19),
            (cx - 9 - int(sway), cy + 13),
            (cx - 11, cy + 4),
        ])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["robe_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 9, cy + 3),
            (cx + 7, cy + 12),
            (cx + 4, cy + 17),
            (cx - 4, cy + 17),
            (cx - 7, cy + 12),
            (cx - 9, cy + 3),
        ])

        # Vertical hakama fold lines.
        for x_off in (-5, 0, 5):
            pygame.draw.line(surface, _NS_yamako.PALETTE["robe_darkest"],
                             (cx + x_off, cy - 4),
                             (cx + int(x_off * 1.4), cy + 17), 1)

        # Leg separation (center).
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_darkest"],
                         (cx, cy + 3), (cx, cy + 18), 1)

        # Wood belt at waist.
        pygame.draw.rect(surface, _NS_yamako.PALETTE["wood_darkest"],
                         (cx - 10, cy - 6, 20, 3))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["wood_dark"],
                         (cx - 10, cy - 6, 20, 2))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["wood_mid"],
                         (cx - 9, cy - 6, 18, 1))
        # Belt buckle (wood circle).
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"], (cx, cy - 5), 3)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_mid"], (cx, cy - 5), 2)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["chakra_dark"], (cx, cy - 5), 1)
        pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (cx, cy - 5, 1, 1))

        # Sandals + leg wraps at bottom.
        for side in (-1, 1):
            wrap_x = cx + side * 4
            # Leg wraps (bandage lines).
            for wrap_y_off in (16, 18):
                pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_edge"],
                                 (wrap_x - 3, cy + wrap_y_off, 6, 1))
                pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_darkest"],
                                 (wrap_x - 3, cy + wrap_y_off + 1, 6, 1))
            # Sandal (waraji).
            pygame.draw.rect(surface, _NS_yamako.PALETTE["shadow_deep"],
                             (wrap_x - 4, cy + 20, 8, 3))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["wood_dark"],
                             (wrap_x - 4, cy + 20, 8, 2))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["wood_mid"],
                             (wrap_x - 3, cy + 20, 6, 1))

    def _draw_scabbard(surface, cx, cy, facing, phase):
        """Sword scabbard visible on back."""
        back_x = cx - facing * 5
        # Scabbard as diagonal line behind torso.
        scab_start_x = back_x - facing * 3
        scab_start_y = cy - 8
        scab_end_x = back_x + facing * 8
        scab_end_y = cy + 12

        # Shadow.
        pygame.draw.line(surface, _NS_yamako.PALETTE["shadow_deep"],
                         (scab_start_x + 1, scab_start_y + 1),
                         (scab_end_x + 1, scab_end_y + 1), 4)
        # Scabbard body.
        pygame.draw.line(surface, _NS_yamako.PALETTE["wood_darkest"],
                         (scab_start_x, scab_start_y), (scab_end_x, scab_end_y), 3)
        pygame.draw.line(surface, _NS_yamako.PALETTE["wood_dark"],
                         (scab_start_x, scab_start_y), (scab_end_x, scab_end_y), 2)
        pygame.draw.line(surface, _NS_yamako.PALETTE["wood_mid"],
                         (scab_start_x, scab_start_y - 1),
                         (scab_end_x, scab_end_y - 1), 1)

        # Cap at end.
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"],
                              (scab_end_x, scab_end_y), 2)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_mid"],
                              (scab_end_x, scab_end_y), 1)

    def _draw_shinobi_torso(surface, cx, cy, facing, phase):
        """Gi (kimono) with wood chest armor plate."""
        # Torso base (V shape).
        torso_pts = [
            (cx - 10, cy - 4),
            (cx - 9, cy + 6),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 9, cy + 6),
            (cx + 10, cy - 4),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ]
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["robe_darkest"], torso_pts)

        # Gi color.
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["robe_dark"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 8, cy + 7),
            (cx - 8, cy + 7),
        ])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["robe_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
        ])

        # Cross-fold of gi (V collar).
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_darkest"],
                         (cx - 5, cy - 5), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_darkest"],
                         (cx + 5, cy - 5), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_edge"],
                         (cx - 4, cy - 4), (cx, cy), 1)
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_edge"],
                         (cx + 4, cy - 4), (cx, cy), 1)

        # WOOD CHEST ARMOR PLATE (round with rings).
        _NS_yamako._draw_chest_plate(surface, cx, cy, facing, phase)

        # WOOD SHOULDER PAULDRONS.
        for side in (-1, 1):
            _NS_yamako._draw_wood_pauldron(surface, cx + side * 10, cy - 4, side, phase)

    def _draw_chest_plate(surface, cx, cy, facing, phase):
        """Round wood chest plate with chakra glow."""
        plate_y = cy + 2

        # Plate shape (circular wooden).
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["shadow_deep"],
                              (cx + 1, plate_y + 1), 5)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"],
                              (cx, plate_y), 5)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_dark"],
                              (cx, plate_y), 4)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_mid"],
                              (cx, plate_y), 3)

        # Wood grain rings.
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"],
                              (cx, plate_y), 3, 1)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"],
                              (cx, plate_y), 2, 1)

        # Center chakra core.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_yamako._alpha(140 * pulse * (4 - r) / 4)
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                                   (cx, plate_y), r)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["chakra_darkest"], (cx, plate_y), 2)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["chakra_mid"], (cx, plate_y), 1)
        pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (cx, plate_y, 1, 1))

    def _draw_wood_pauldron(surface, cx, cy, side, phase):
        """Wood pauldron on shoulder (like Hashirama's canister-shaped)."""
        # Cylinder shape.
        paul_pts = [
            (cx - 4, cy),
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 4, cy),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ]
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_darkest"], paul_pts)
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_dark"], [
            (cx - 3, cy),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 3, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_mid"], [
            (cx - 2, cy - 1),
            (cx - 1, cy - 3),
            (cx + 1, cy - 3),
            (cx + 2, cy - 1),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
        ])

        # Wood grain circle detail (like tree rings on end).
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"], (cx, cy), 2, 1)
        pygame.draw.rect(surface, _NS_yamako.PALETTE["wood_edge"],
                         (cx - 1, cy - 1, 2, 1))

        # Ropes/wraps around pauldron.
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_edge"],
                         (cx - 4, cy - 1), (cx + 4, cy - 1), 1)
        pygame.draw.line(surface, _NS_yamako.PALETTE["robe_edge"],
                         (cx - 4, cy + 2), (cx + 4, cy + 2), 1)

        # Small leaf on pauldron.
        leaf_y = cy - 3
        pygame.draw.rect(surface, _NS_yamako.PALETTE["leaf_dark"],
                         (cx - 1, leaf_y - 1, 3, 1))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["leaf_mid"], (cx, leaf_y - 1, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (not holding sword)."""
        sway = math.sin(phase * 0.5) * 1

        if action == "attack":
            # Braces for sword swing.
            elbow_y_off = int(math.sin(attack_progress * math.pi) * -2)
            elbow_x_off = -int(math.sin(attack_progress * math.pi) * 3) * facing
        else:
            elbow_y_off = 5 + int(sway)
            elbow_x_off = 0

        shoulder_x = cx - facing * 10
        shoulder_y = cy - 2

        elbow_x = shoulder_x - facing * 2 + elbow_x_off
        elbow_y = shoulder_y + elbow_y_off + 3
        hand_x = elbow_x - facing * 1
        hand_y = elbow_y + 6

        # Upper arm.
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 5)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["robe_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["robe_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["robe_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)

        # Forearm (skin-toned, cuff exposed).
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 4)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["skin_mid"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Bandage wrap on forearm.
        for wy in (elbow_y + 2, elbow_y + 4):
            pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_edge"],
                             (elbow_x - 2, wy, 4, 1))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_darkest"],
                             (elbow_x - 2, wy + 1, 4, 1))

        # Hand.
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["skin_dark"],
                              (hand_x, hand_y), 2)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["skin_mid"],
                              (hand_x, hand_y), 1)

        # Doing hand-seal (chakra pool between hands during idle/attack).
        if action != "attack":
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            seal_x = hand_x + facing * 3
            seal_y = hand_y - 2
            for r in range(3, 0, -1):
                alpha = _NS_yamako._alpha(100 * pulse * (3 - r) / 3)
                _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                                       (seal_x, seal_y), r)
            pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (seal_x, seal_y, 1, 1))

    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding wood sword."""
        # Sword swing animation.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up (raise sword up-back).
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.2 + t * -math.pi * 0.5
                sword_angle = arm_angle - math.pi * 0.15
            elif attack_progress < 0.6:
                # SLASH down-forward.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.7 + t * math.pi * 1.0
                sword_angle = arm_angle
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.3 - t * math.pi * 0.5
                sword_angle = arm_angle + math.pi * 0.05
        else:
            arm_angle = -math.pi * 0.15 + math.sin(phase * 0.5) * 0.05
            sword_angle = arm_angle - math.pi * 0.1

        shoulder_x = cx + facing * 10
        shoulder_y = cy - 2

        arm_len = 8
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len) + 2

        forearm_len = 7
        forearm_angle = arm_angle + 0.3
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm.
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["robe_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["robe_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["robe_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)

        # Forearm (skin).
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 4)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["skin_mid"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_yamako._aaline(surface, _NS_yamako.PALETTE["skin_light"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Bandage wrap.
        for wy in (elbow_y + 2, elbow_y + 4):
            pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_edge"],
                             (elbow_x - 2, wy, 4, 1))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_darkest"],
                             (elbow_x - 2, wy + 1, 4, 1))

        # Hand.
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["skin_dark"],
                              (hand_x, hand_y), 3)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["skin_mid"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_yamako.PALETTE["skin_light"],
                         (hand_x, hand_y - 1, 1, 1))

        # SWORD/KATANA.
        _NS_yamako._draw_wood_katana(surface, hand_x, hand_y, sword_angle, facing, phase,
                                       action, attack_progress)

    def _draw_wood_katana(surface, hand_x, hand_y, angle, facing, phase, action, attack_progress):
        """Wood katana (green-tinted blade)."""
        # Handle length.
        handle_len = 5
        blade_len = 24

        # Guard position.
        guard_x = hand_x + int(math.cos(angle) * handle_len) * facing
        guard_y = hand_y + int(math.sin(angle) * handle_len)

        # Blade tip position.
        blade_tip_x = guard_x + int(math.cos(angle) * blade_len) * facing
        blade_tip_y = guard_y + int(math.sin(angle) * blade_len)

        # Pommel (butt end).
        pommel_x = hand_x - int(math.cos(angle) * 3) * facing
        pommel_y = hand_y - int(math.sin(angle) * 3)

        # HANDLE (wrapped tsuka).
        pygame.draw.line(surface, _NS_yamako.PALETTE["shadow_deep"],
                         (pommel_x + 1, pommel_y + 1), (guard_x + 1, guard_y + 1), 4)
        pygame.draw.line(surface, _NS_yamako.PALETTE["hair_darkest"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 3)
        pygame.draw.line(surface, _NS_yamako.PALETTE["hair_dark"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 2)

        # Handle wrap diamond pattern.
        for i in range(1, 4):
            t = i / 4
            wrap_x = int(pommel_x + (guard_x - pommel_x) * t)
            wrap_y = int(pommel_y + (guard_y - pommel_y) * t)
            perp = angle + math.pi / 2
            wx1 = wrap_x + int(math.cos(perp) * 1) * facing
            wy1 = wrap_y + int(math.sin(perp) * 1)
            wx2 = wrap_x - int(math.cos(perp) * 1) * facing
            wy2 = wrap_y - int(math.sin(perp) * 1)
            pygame.draw.line(surface, _NS_yamako.PALETTE["robe_edge"], (wx1, wy1), (wx2, wy2), 1)

        # GUARD (tsuba - round wooden).
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["shadow_deep"],
                              (guard_x + 1, guard_y + 1), 3)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"],
                              (guard_x, guard_y), 3)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_dark"],
                              (guard_x, guard_y), 2)
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_mid"],
                              (guard_x, guard_y), 1)

        # BLADE (steel with green tint).
        # Perpendicular for blade width.
        perp = angle + math.pi / 2

        # Blade edge positions (thin).
        edge_a_offset = 2
        blade_ba_x = guard_x + int(math.cos(perp) * edge_a_offset) * facing
        blade_ba_y = guard_y + int(math.sin(perp) * edge_a_offset)
        blade_bb_x = guard_x - int(math.cos(perp) * edge_a_offset) * facing
        blade_bb_y = guard_y - int(math.sin(perp) * edge_a_offset)
        blade_ta_x = blade_tip_x + int(math.cos(perp) * 1) * facing
        blade_ta_y = blade_tip_y + int(math.sin(perp) * 1)
        blade_tb_x = blade_tip_x - int(math.cos(perp) * 1) * facing
        blade_tb_y = blade_tip_y - int(math.sin(perp) * 1)

        # Blade shadow.
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"], [
            (blade_ba_x + 1, blade_ba_y + 1),
            (blade_bb_x + 1, blade_bb_y + 1),
            (blade_tb_x + 1, blade_tb_y + 1),
            (blade_ta_x + 1, blade_ta_y + 1),
        ])

        # Dark base.
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["blade_dark"], [
            (blade_ba_x, blade_ba_y),
            (blade_bb_x, blade_bb_y),
            (blade_tb_x, blade_tb_y),
            (blade_ta_x, blade_ta_y),
        ])

        # Mid steel.
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["blade_mid"], [
            (int((blade_ba_x + guard_x) / 2), int((blade_ba_y + guard_y) / 2)),
            (blade_tip_x, blade_tip_y),
            (int((blade_bb_x + guard_x) / 2), int((blade_bb_y + guard_y) / 2)),
        ])

        # Bright edge (sharp).
        pygame.draw.line(surface, _NS_yamako.PALETTE["blade_light"],
                         (blade_ba_x, blade_ba_y), (blade_ta_x, blade_ta_y), 1)

        # Sharp tip.
        _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["blade_shine"], (blade_tip_x, blade_tip_y), 1)
        pygame.draw.rect(surface, _NS_yamako.PALETTE["white"], (blade_tip_x, blade_tip_y, 1, 1))

        # Chakra glow along blade (green energy infused).
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_yamako._alpha(80 * pulse * (4 - r) / 4)
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                                   (blade_tip_x, blade_tip_y), r)

        # Store sword tip position for slash arc.
        _NS_yamako._sword_tip = (blade_tip_x, blade_tip_y)
        _NS_yamako._sword_angle = angle

    def _draw_shinobi_head(surface, cx, cy, facing, phase):
        """Head with headband, long black hair."""
        # Head base.
        head_pts = [
            (cx - 5, cy + 3),
            (cx - 6, cy),
            (cx - 5, cy - 5),
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 5),
            (cx + 6, cy),
            (cx + 5, cy + 3),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ]
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["skin_dark"], head_pts)
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 4),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_yamako.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # LONG BLACK HAIR (behind head + sides).
        _NS_yamako._draw_long_hair(surface, cx, cy, facing, phase)

        # HEADBAND (silver metal plate).
        _NS_yamako._draw_headband(surface, cx, cy - 5, facing, phase)

        # EYES (fierce dark with glow).
        _NS_yamako._draw_shinobi_eyes(surface, cx, cy - 2, facing, phase)

        # Small nose line.
        pygame.draw.rect(surface, _NS_yamako.PALETTE["shadow_deep"], (cx, cy, 1, 1))

        # Mouth line.
        pygame.draw.line(surface, _NS_yamako.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

    def _draw_long_hair(surface, cx, cy, facing, phase):
        """Long flowing black hair."""
        sway = math.sin(phase * 0.6) * 2

        # Hair top (crown of head).
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["hair_darkest"], [
            (cx - 5, cy - 5),
            (cx - 4, cy - 7),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 4, cy - 7),
            (cx + 5, cy - 5),
            (cx + 5, cy - 4),
            (cx - 5, cy - 4),
        ])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["hair_dark"], [
            (cx - 4, cy - 5),
            (cx - 3, cy - 6),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 3, cy - 6),
            (cx + 4, cy - 5),
        ])
        _NS_yamako._poly(surface, _NS_yamako.PALETTE["hair_mid"], [
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])

        # Side hair strands (long, framing face).
        for side in (-1, 1):
            side_x = cx + side * 5
            side_pts = [
                (side_x, cy - 4),
                (side_x + side * 1, cy),
                (side_x + side * 2, cy + 5 + int(sway * 0.5)),
                (side_x + side * 1, cy + 10 + int(sway)),
                (side_x, cy + 6),
                (side_x - side * 1, cy),
            ]
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["hair_darkest"], side_pts)
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["hair_dark"], [
                (side_x, cy - 3),
                (side_x + side * 1, cy + 1),
                (side_x + side * 1, cy + 8 + int(sway * 0.5)),
                (side_x, cy + 5),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["hair_mid"], [
                (side_x, cy - 2),
                (side_x, cy + 4),
            ])

        # BIG hair mass BEHIND head/shoulders (long flowing).
        back_hair_pts = [
            (cx - 5, cy - 3),
            (cx - 7, cy),
            (cx - 8, cy + 5),
            (cx - 9, cy + 12),
            (cx - 7, cy + 18 + int(sway)),
            (cx - 3, cy + 22),
            (cx + 3, cy + 22),
            (cx + 7, cy + 18 + int(sway)),
            (cx + 9, cy + 12),
            (cx + 8, cy + 5),
            (cx + 7, cy),
            (cx + 5, cy - 3),
        ]
        # This is drawn behind head, so we skip drawing (should be drawn before torso for depth).
        # But here we simulate it partially with visible parts.
        for side in (-1, 1):
            hair_end_x = cx + side * 7 + int(sway * side)
            hair_end_y = cy + 20
            hair_mid_x = cx + side * 8
            hair_mid_y = cy + 10

            # Draw single flowing strand behind head.
            pygame.draw.line(surface, _NS_yamako.PALETTE["hair_darkest"],
                             (cx + side * 5, cy - 2),
                             (hair_mid_x, hair_mid_y), 3)
            pygame.draw.line(surface, _NS_yamako.PALETTE["hair_darkest"],
                             (hair_mid_x, hair_mid_y),
                             (hair_end_x, hair_end_y), 3)
            pygame.draw.line(surface, _NS_yamako.PALETTE["hair_dark"],
                             (cx + side * 5, cy - 2),
                             (hair_mid_x, hair_mid_y), 2)
            pygame.draw.line(surface, _NS_yamako.PALETTE["hair_dark"],
                             (hair_mid_x, hair_mid_y),
                             (hair_end_x, hair_end_y), 2)
            pygame.draw.line(surface, _NS_yamako.PALETTE["hair_mid"],
                             (cx + side * 5, cy - 1),
                             (hair_mid_x, hair_mid_y - 1), 1)

    def _draw_headband(surface, cx, cy, facing, phase):
        """Metal headband with symbol."""
        # Cloth strip base (around head).
        pygame.draw.rect(surface, _NS_yamako.PALETTE["shadow_deep"],
                         (cx - 6, cy, 12, 3))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_darkest"],
                         (cx - 6, cy, 12, 2))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_dark"],
                         (cx - 6, cy, 12, 1))

        # Metal plate (center).
        pygame.draw.rect(surface, _NS_yamako.PALETTE["shadow_deep"],
                         (cx - 4, cy - 1, 8, 3))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["band_dark"],
                         (cx - 4, cy - 1, 8, 3))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["band_mid"],
                         (cx - 3, cy - 1, 6, 2))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["band_light"],
                         (cx - 3, cy - 1, 6, 1))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["band_shine"],
                         (cx - 2, cy - 1, 2, 1))

        # Symbol (leaf or spiral - just a small mark).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_dark"], (cx, cy, 1, 1))
        alpha_g = _NS_yamako._alpha(180 * pulse)
        pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], alpha_g), (cx, cy, 1, 1))

        # Ends of cloth headband hanging down.
        pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_dark"],
                         (cx - 7, cy, 1, 5))
        pygame.draw.rect(surface, _NS_yamako.PALETTE["robe_dark"],
                         (cx + 6, cy, 1, 5))

    def _draw_shinobi_eyes(surface, cx, cy, facing, phase):
        """Fierce dark eyes with chakra glow."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_yamako.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["eye_socket"],
                             (ex, ey - 1, 1, 2))

            # Chakra glow behind.
            for r in range(3, 0, -1):
                alpha = _NS_yamako._alpha(140 * pulse * (3 - r) / 3)
                _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)

            pygame.draw.rect(surface, _NS_yamako.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["eye_light"], (ex, ey, 1, 1))

    # ============================================================
    # SWORD SLASH ARC
    # ============================================================
    def _draw_sword_slash(surface, boss, x, y, progress):
        """Green energy slash arc."""
        if progress < 0.35 or progress > 0.7:
            return

        facing = boss.direction
        swing_t = (progress - 0.35) / 0.25
        swing_t = max(0, min(1, swing_t))
        alpha_val = int(255 * (1 - abs(swing_t - 0.5) * 1.5))
        alpha_val = max(0, alpha_val)

        center_x = x + facing * 5
        center_y = y + 3
        arc_radius = 32

        start_angle = -math.pi * 0.85 * facing
        end_angle = math.pi * 0.35 * facing
        current_angle = start_angle + (end_angle - start_angle) * swing_t

        # Arc trail.
        num_segments = 18
        for i in range(num_segments):
            t = i / num_segments
            seg_angle = start_angle + (current_angle - start_angle) * t
            seg_x = center_x + int(math.cos(seg_angle) * arc_radius) * facing
            seg_y = center_y + int(math.sin(seg_angle) * arc_radius)
            seg_alpha = _NS_yamako._alpha(alpha_val * t)
            size = int(2 + t * 4)

            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_darkest"], seg_alpha),
                                   (seg_x, seg_y), size)
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_dark"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 1))
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_mid"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 2))
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_light"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Bright edge.
        for i in range(6):
            edge_t = 1 - i * 0.1
            edge_angle = start_angle + (current_angle - start_angle) * edge_t
            ex1 = center_x + int(math.cos(edge_angle) * (arc_radius - 2)) * facing
            ey1 = center_y + int(math.sin(edge_angle) * (arc_radius - 2))
            ex2 = center_x + int(math.cos(edge_angle) * (arc_radius + 4)) * facing
            ey2 = center_y + int(math.sin(edge_angle) * (arc_radius + 4))
            e_alpha = _NS_yamako._alpha(alpha_val * (1 - i * 0.13))
            pygame.draw.line(surface, (*_NS_yamako.PALETTE["chakra_hot"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 1)
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_shine"], e_alpha),
                             (ex2, ey2, 1, 1))

        # Leaves flying off from slash.
        for i in range(8):
            leaf_angle = current_angle + i * 0.12 * facing
            leaf_dist = arc_radius + i * 2
            lx = center_x + int(math.cos(leaf_angle) * leaf_dist) * facing
            ly = center_y + int(math.sin(leaf_angle) * leaf_dist)
            leaf_alpha = _NS_yamako._alpha(220 - i * 20)
            # Small leaf.
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["leaf_dark"], leaf_alpha),
                             (lx - 1, ly, 3, 1))
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["leaf_mid"], leaf_alpha),
                             (lx, ly, 1, 1))
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], leaf_alpha),
                             (lx, ly, 1, 1))

    # ============================================================
    # AMBIENT (TRUE BOSS bigger)
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
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
        pygame.draw.ellipse(shadow, (5, 15, 5, 170),
                            (80 - w // 2, 15 - h // 2, w, h))
        surface.blit(shadow, (x - 80, y - 15))

    def _draw_chakra_wisps(surface, cx, cy, phase, intense=False):
        """Green chakra wisps rising."""
        strength = 1.5 if intense else 1.0

        for i in range(12):
            t = (phase * 0.5 + i * 0.1) % 1.0
            sx = cx - 34 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 32)
            alpha = _NS_yamako._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_darkest"], alpha),
                                   (sx, sy), 3)
            _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_dark"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(10):
            spark_t = (phase * 0.4 + i * 0.13) % 1.0
            ex = cx - 30 + i * 7 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 28)
            alpha = _NS_yamako._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_falling_leaves(surface, cx, cy, phase):
        """Small leaves falling around boss."""
        for i in range(8):
            t = (phase * 0.3 + i * 0.13) % 1.0
            lx = cx - 50 + i * 15 + int(math.sin(phase * 0.5 + i) * 15)
            ly = cy - 50 + int(t * 110)
            rot_phase = phase * 2 + i
            alpha = _NS_yamako._alpha(200 * (1 - t * 0.3))

            leaf_color = _NS_yamako.PALETTE["leaf_dark"] if i % 2 else _NS_yamako.PALETTE["leaf_mid"]
            if math.sin(rot_phase) > 0:
                pygame.draw.rect(surface, (*leaf_color, alpha), (lx - 1, ly, 3, 1))
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["leaf_light"], alpha),
                                 (lx, ly, 1, 1))
            else:
                pygame.draw.rect(surface, (*leaf_color, alpha), (lx, ly - 1, 1, 3))
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["leaf_light"], alpha),
                                 (lx, ly, 1, 1))

    def _draw_chakra_aura(surface, x, y, phase):
        """Large chakra aura background (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_yamako._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_yamako._aacircle(aura, (*_NS_yamako.PALETTE["chakra_darkest"], alpha),
                                       (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_yamako._alpha((70 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_yamako._aacircle(aura, (*_NS_yamako.PALETTE["chakra_dark"], alpha),
                                       (120, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_yamako._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_yamako._aacircle(aura, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                                       (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))

        # Orbiting chakra particles.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large ground ring with kanji-like runes (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_yamako.PALETTE["chakra_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_yamako.PALETTE["chakra_dark"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_yamako.PALETTE["chakra_mid"], 230),
                            (25, 24, 140, 22), 1)

        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 50)
            y1 = 35 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_yamako.PALETTE["chakra_light"], 230),
                             (x1, y1), (x2, y2), 1)

        # Kanji-like square symbols around edge.
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sr = 65
            sx = 95 + int(math.cos(angle) * sr)
            sy = 35 + int(math.sin(angle) * sr * 0.35)
            pygame.draw.rect(ring, (*_NS_yamako.PALETTE["chakra_hot"], 240),
                             (sx - 2, sy - 1, 4, 3), 1)
            pygame.draw.line(ring, (*_NS_yamako.PALETTE["chakra_hot"], 240),
                             (sx - 1, sy), (sx + 1, sy), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_yamako.PALETTE["chakra_hot"],
                                        _NS_yamako._alpha(180 * pulse)),
                                (15, 14, 160, 42), 1)
        surface.blit(ring, (x - 95, y - 30))

    # ============================================================
    # SKILL Q: MOKUTON DEEP FOREST (roots erupt from ground)
    # ============================================================
    def _draw_deepforest_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_yamako._target_position(boss, x, y)

        # Ground scorching/root pattern around target.
        if progress > 0.15:
            t = (progress - 0.15) / 0.85
            r = int(45 * min(1.0, t * 2))

            alpha = _NS_yamako._alpha(200)
            pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["wood_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["wood_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["wood_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_deepforest_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_yamako._target_position(boss, x, y)

        if progress < 0.15:
            # Hand seal charging.
            t = progress / 0.15
            for r in range(int(6 + t * 8), 0, -1):
                alpha = _NS_yamako._alpha(180 * (6 + t * 8 - r) / (6 + t * 8))
                _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                                       (x, y - 5), r)
        else:
            # Massive roots/trees erupt from ground at target.
            t = (progress - 0.15) / 0.85
            grow_t = min(1.0, t * 2.5)

            # Multiple tree/root trunks erupting.
            num_roots = 7
            for i in range(num_roots):
                # Spread roots around target.
                angle_offset = (i - num_roots // 2) * 0.25
                root_base_x = tx + int(math.sin(angle_offset) * 20)
                root_base_y = ty + 5

                # Root grows upward.
                root_height = int(40 * grow_t) + int(math.sin(phase + i) * 3)

                # Draw as thick gnarled tree trunk.
                num_segments = 6
                prev_x = root_base_x
                prev_y = root_base_y
                for seg in range(1, num_segments + 1):
                    seg_t = seg / num_segments
                    seg_x = root_base_x + int(math.sin(phase + i + seg_t * 3) * 4)
                    seg_y = root_base_y - int(seg_t * root_height)

                    thickness = max(2, 8 - seg)

                    _NS_yamako._aaline(surface, _NS_yamako.PALETTE["shadow_deep"],
                                        (prev_x + 1, prev_y + 1),
                                        (seg_x + 1, seg_y + 1), thickness + 1)
                    _NS_yamako._aaline(surface, _NS_yamako.PALETTE["wood_darkest"],
                                        (prev_x, prev_y), (seg_x, seg_y), thickness)
                    _NS_yamako._aaline(surface, _NS_yamako.PALETTE["wood_dark"],
                                        (prev_x, prev_y), (seg_x, seg_y),
                                        max(1, thickness - 2))
                    _NS_yamako._aaline(surface, _NS_yamako.PALETTE["wood_mid"],
                                        (prev_x, prev_y - 1),
                                        (seg_x, seg_y - 1), max(1, thickness - 4))
                    prev_x, prev_y = seg_x, seg_y

                # Branches at top (gnarled fingers).
                for branch_angle in (-0.5, 0, 0.5):
                    b_end_x = prev_x + int(math.sin(branch_angle) * 6)
                    b_end_y = prev_y - 5
                    pygame.draw.line(surface, _NS_yamako.PALETTE["wood_darkest"],
                                     (prev_x, prev_y), (b_end_x, b_end_y), 2)
                    pygame.draw.line(surface, _NS_yamako.PALETTE["wood_dark"],
                                     (prev_x, prev_y), (b_end_x, b_end_y), 1)
                    # Green tip.
                    pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_mid"],
                                     (b_end_x, b_end_y, 1, 1))
                    pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"],
                                     (b_end_x, b_end_y, 1, 1))

                # Leaves on trunk.
                if grow_t > 0.7:
                    for leaf_y_off in (10, 20, 30):
                        leaf_x = root_base_x + int(math.sin(phase + i) * 3)
                        leaf_y = root_base_y - leaf_y_off
                        pygame.draw.rect(surface, _NS_yamako.PALETTE["leaf_dark"],
                                         (leaf_x - 1, leaf_y, 3, 1))
                        pygame.draw.rect(surface, _NS_yamako.PALETTE["leaf_mid"],
                                         (leaf_x, leaf_y, 1, 1))

    # ============================================================
    # SKILL W: WOOD CREATION (protective shell around ally)
    # ============================================================
    def _draw_woodcreation_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_yamako._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ring around target.
        t = min(1.0, progress * 2)
        r = int(40 * t)
        if r > 3:
            alpha = _NS_yamako._alpha(180)
            pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_woodcreation_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_yamako._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Wooden shell dome around target.
        r = 30 + int(math.sin(phase * 2) * 2)

        shell = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multiple wood plank strips forming dome.
        num_strips = 8
        for i in range(num_strips):
            angle = i * math.pi / num_strips
            # Strip end points.
            end1_x = center[0] + int(math.cos(angle) * r)
            end1_y = center[1] + int(math.sin(angle) * r * 0.7) - r // 3
            end2_x = center[0] - int(math.cos(angle) * r)
            end2_y = center[1] - int(math.sin(angle) * r * 0.7) - r // 3

            pygame.draw.line(shell, (*_NS_yamako.PALETTE["wood_darkest"], 200),
                             (end1_x, end1_y), (end2_x, end2_y), 3)
            pygame.draw.line(shell, (*_NS_yamako.PALETTE["wood_dark"], 220),
                             (end1_x, end1_y), (end2_x, end2_y), 2)
            pygame.draw.line(shell, (*_NS_yamako.PALETTE["wood_mid"], 200),
                             (end1_x, end1_y - 1), (end2_x, end2_y - 1), 1)

        # Chakra glow on dome.
        for r_g in range(r + 5, r - 3, -1):
            alpha = _NS_yamako._alpha(120 * pulse * (r + 5 - r_g) / 8)
            pygame.draw.ellipse(shell, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                                (10 + r - r_g, 10 + r - r_g,
                                 r_g * 2, r_g * 2 - r_g), 1)

        # Sparkles on shell.
        for i in range(12):
            angle = phase * 1.5 + i * math.pi / 6
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r * 0.7) - r // 3
            pygame.draw.rect(shell, _NS_yamako.PALETTE["chakra_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(shell, _NS_yamako.PALETTE["chakra_shine"], (sx, sy, 1, 1))

        surface.blit(shell, (tx - r - 10, ty - r - 10))

        # Rising healing sparkles inside.
        for i in range(8):
            t = (phase * 0.6 + i * 0.13) % 1.0
            sx = tx - 15 + i * 4 + int(math.sin(phase + i) * 2)
            sy = ty + 10 - int(t * 25)
            alpha = _NS_yamako._alpha(220 * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_shine"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: WOOD GOLEM (summon golem)
    # ============================================================
    def _draw_woodgolem_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground circle where golem summoned.
        summon_x = x + facing * 50
        summon_y = y + 35

        r = int(25 + math.sin(phase * 2) * 3)
        alpha = _NS_yamako._alpha(200)
        pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["wood_darkest"], alpha),
                            (summon_x - r, summon_y - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["wood_dark"], alpha),
                            (summon_x - r + 3, summon_y - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4))

    def _draw_woodgolem_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        summon_x = x + facing * 50
        summon_y = y + 15

        # Golem rises up from ground.
        rise_t = min(1.0, progress * 2)
        golem_scale = rise_t

        # Golem body (chunky wooden humanoid).
        if golem_scale > 0.2:
            body_h = int(35 * golem_scale)
            body_w = int(18 * golem_scale)

            gx = summon_x
            gy = summon_y + 20 - body_h

            # Golem legs (thick trunks).
            for side in (-1, 1):
                leg_x = gx + side * 5
                _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"], [
                    (leg_x - 3, gy + body_h - 1),
                    (leg_x + 3, gy + body_h - 1),
                    (leg_x + 4, gy + body_h + 5),
                    (leg_x - 4, gy + body_h + 5),
                ])
                _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_darkest"], [
                    (leg_x - 3, gy + body_h - 2),
                    (leg_x + 3, gy + body_h - 2),
                    (leg_x + 4, gy + body_h + 4),
                    (leg_x - 4, gy + body_h + 4),
                ])
                _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_dark"], [
                    (leg_x - 2, gy + body_h - 1),
                    (leg_x + 2, gy + body_h - 1),
                    (leg_x + 3, gy + body_h + 3),
                    (leg_x - 3, gy + body_h + 3),
                ])
                _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_mid"], [
                    (leg_x - 1, gy + body_h),
                    (leg_x + 1, gy + body_h),
                    (leg_x + 1, gy + body_h + 2),
                    (leg_x - 1, gy + body_h + 2),
                ])

            # Golem torso (barrel shape).
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"], [
                (gx - body_w // 2, gy + 5),
                (gx + body_w // 2, gy + 5),
                (gx + body_w // 2 + 2, gy + body_h - 5),
                (gx - body_w // 2 - 2, gy + body_h - 5),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_darkest"], [
                (gx - body_w // 2, gy + 5),
                (gx + body_w // 2, gy + 5),
                (gx + body_w // 2 + 2, gy + body_h - 4),
                (gx - body_w // 2 - 2, gy + body_h - 4),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_dark"], [
                (gx - body_w // 2 + 1, gy + 6),
                (gx + body_w // 2 - 1, gy + 6),
                (gx + body_w // 2 + 1, gy + body_h - 5),
                (gx - body_w // 2 - 1, gy + body_h - 5),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_mid"], [
                (gx - body_w // 2 + 3, gy + 8),
                (gx + body_w // 2 - 3, gy + 8),
                (gx + body_w // 2 - 2, gy + body_h - 8),
                (gx - body_w // 2 + 2, gy + body_h - 8),
            ])

            # Wood grain lines.
            for grain_y in range(gy + 10, gy + body_h - 6, 5):
                pygame.draw.line(surface, _NS_yamako.PALETTE["wood_darkest"],
                                 (gx - body_w // 2 + 2, grain_y),
                                 (gx + body_w // 2 - 2, grain_y), 1)

            # Golem HEAD (blocky angry).
            head_y = gy - 2
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["shadow_deep"], [
                (gx - 6, head_y - 1),
                (gx + 6, head_y - 1),
                (gx + 7, head_y + 8),
                (gx - 7, head_y + 8),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_darkest"], [
                (gx - 6, head_y),
                (gx + 6, head_y),
                (gx + 6, head_y + 7),
                (gx - 6, head_y + 7),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_dark"], [
                (gx - 5, head_y + 1),
                (gx + 5, head_y + 1),
                (gx + 5, head_y + 6),
                (gx - 5, head_y + 6),
            ])
            _NS_yamako._poly(surface, _NS_yamako.PALETTE["wood_mid"], [
                (gx - 4, head_y + 2),
                (gx + 4, head_y + 2),
                (gx + 4, head_y + 5),
                (gx - 4, head_y + 5),
            ])

            # Golem eyes (glowing green).
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            for side in (-1, 1):
                ex = gx + side * 2
                ey = head_y + 3
                for r in range(3, 0, -1):
                    alpha = _NS_yamako._alpha(180 * pulse * (3 - r) / 3)
                    _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                                           (ex, ey), r)
                pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (ex, ey, 1, 1))
                pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_shine"], (ex, ey, 1, 1))

            # Angry mouth.
            pygame.draw.line(surface, _NS_yamako.PALETTE["shadow_deep"],
                             (gx - 3, head_y + 5), (gx + 3, head_y + 5), 1)

            # Golem ARMS (thick).
            for side in (-1, 1):
                arm_top_x = gx + side * (body_w // 2 + 2)
                arm_top_y = gy + 8
                arm_bot_x = arm_top_x + side * 3
                arm_bot_y = gy + body_h - 5

                # Upper arm.
                _NS_yamako._aaline(surface, _NS_yamako.PALETTE["wood_darkest"],
                                    (arm_top_x, arm_top_y), (arm_bot_x, arm_bot_y), 6)
                _NS_yamako._aaline(surface, _NS_yamako.PALETTE["wood_dark"],
                                    (arm_top_x, arm_top_y), (arm_bot_x, arm_bot_y), 4)
                _NS_yamako._aaline(surface, _NS_yamako.PALETTE["wood_mid"],
                                    (arm_top_x, arm_top_y - 1),
                                    (arm_bot_x, arm_bot_y - 1), 2)

                # Fist.
                _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["shadow_deep"],
                                       (arm_bot_x + 1, arm_bot_y + 1), 4)
                _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_darkest"],
                                       (arm_bot_x, arm_bot_y), 4)
                _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_dark"],
                                       (arm_bot_x, arm_bot_y), 3)
                _NS_yamako._aacircle(surface, _NS_yamako.PALETTE["wood_mid"],
                                       (arm_bot_x, arm_bot_y), 2)

            # Chakra glow from body cracks.
            for i in range(3):
                crack_y = gy + 12 + i * 8
                pygame.draw.line(surface,
                                 (*_NS_yamako.PALETTE["chakra_hot"],
                                  _NS_yamako._alpha(200 * pulse)),
                                 (gx - 3, crack_y), (gx + 3, crack_y), 1)

        # Chakra particles rising from summoning.
        for i in range(12):
            t = (phase * 0.6 + i * 0.09) % 1.0
            sx = summon_x - 20 + i * 4 + int(math.sin(phase + i) * 3)
            sy = summon_y + 20 - int(t * 30)
            alpha = _NS_yamako._alpha(220 * (1 - t))
            if alpha > 0:
                _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                                       (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL R: SHINSU SENJU (Colossal wooden statue - TRUE BOSS ULTIMATE)
    # ============================================================
    def _draw_kannon_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 180
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # HUGE ground ring around boss (massive summon).
        r = 80 + int(math.sin(phase * 2) * 4)
        alpha = _NS_yamako._alpha(220)
        pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["chakra_darkest"], alpha),
                            (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["chakra_dark"], alpha),
                            (x - r + 4, y + 45 - r // 3 + 3,
                             r * 2 - 8, r * 2 // 3 - 6), 3)
        pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                            (x - r + 10, y + 45 - r // 3 + 6,
                             r * 2 - 20, r * 2 // 3 - 12), 2)
        pygame.draw.ellipse(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                            (x - r + 18, y + 45 - r // 3 + 10,
                             r * 2 - 36, r * 2 // 3 - 20), 1)

        # Big rune symbols around perimeter.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            sx = x + int(math.cos(angle) * r)
            sy = y + 45 + int(math.sin(angle) * r * 0.35)
            pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (sx - 2, sy - 1, 5, 1))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_hot"], (sx, sy - 2, 1, 5))
            pygame.draw.rect(surface, _NS_yamako.PALETTE["chakra_shine"], (sx, sy, 1, 1))

    def _draw_kannon_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 180
        progress = max(0.0, min(1.0, 1 - timer / duration))

        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # HUGE ethereal Kannon statue behind boss.
        statue_x = x
        statue_y = y - 5
        statue_scale = min(1.0, progress * 1.5)

        # Statue main body (translucent green).
        statue_surf = pygame.Surface((180, 240), pygame.SRCALPHA)
        sc = statue_scale

        cx_s = 90
        cy_s = 120

        # Statue head (crowned).
        head_y = int(cy_s - 80 * sc)
        head_r = int(20 * sc)
        pygame.draw.ellipse(statue_surf,
                            (*_NS_yamako.PALETTE["chakra_dark"], 180),
                            (cx_s - head_r, head_y - head_r,
                             head_r * 2, head_r * 2))
        pygame.draw.ellipse(statue_surf,
                            (*_NS_yamako.PALETTE["chakra_mid"], 200),
                            (cx_s - head_r + 3, head_y - head_r + 3,
                             head_r * 2 - 6, head_r * 2 - 6))
        pygame.draw.ellipse(statue_surf,
                            (*_NS_yamako.PALETTE["chakra_light"], 220),
                            (cx_s - head_r + 8, head_y - head_r + 8,
                             head_r * 2 - 16, head_r * 2 - 16))

        # Serene face features.
        # Eyes (closed like meditation).
        pygame.draw.line(statue_surf,
                         (*_NS_yamako.PALETTE["chakra_darkest"], 220),
                         (cx_s - 8, head_y - 2), (cx_s - 3, head_y - 2), 1)
        pygame.draw.line(statue_surf,
                         (*_NS_yamako.PALETTE["chakra_darkest"], 220),
                         (cx_s + 3, head_y - 2), (cx_s + 8, head_y - 2), 1)
        # Mouth (calm line).
        pygame.draw.line(statue_surf,
                         (*_NS_yamako.PALETTE["chakra_darkest"], 220),
                         (cx_s - 3, head_y + 6), (cx_s + 3, head_y + 6), 1)

        # Crown/halo spikes.
        for i in range(-2, 3):
            angle = math.pi * 0.7 + i * 0.15
            tip_x = cx_s + int(math.cos(angle) * (head_r + 8))
            tip_y = head_y - int(math.sin(angle) * (head_r + 8))
            base_x = cx_s + int(math.cos(angle) * head_r)
            base_y = head_y - int(math.sin(angle) * head_r)
            pygame.draw.line(statue_surf,
                             (*_NS_yamako.PALETTE["chakra_mid"], 220),
                             (base_x, base_y), (tip_x, tip_y), 2)
            pygame.draw.rect(statue_surf, _NS_yamako.PALETTE["chakra_shine"],
                             (tip_x, tip_y, 1, 1))

        # Statue torso.
        torso_top = head_y + head_r
        torso_bot = int(cy_s + 60 * sc)
        torso_w = int(40 * sc)
        pygame.draw.polygon(statue_surf,
                            (*_NS_yamako.PALETTE["chakra_dark"], 160), [
                                (cx_s - torso_w // 2, torso_top),
                                (cx_s + torso_w // 2, torso_top),
                                (cx_s + torso_w // 2 + 5, torso_bot),
                                (cx_s - torso_w // 2 - 5, torso_bot),
                            ])
        pygame.draw.polygon(statue_surf,
                            (*_NS_yamako.PALETTE["chakra_mid"], 180), [
                                (cx_s - torso_w // 2 + 3, torso_top + 3),
                                (cx_s + torso_w // 2 - 3, torso_top + 3),
                                (cx_s + torso_w // 2 + 2, torso_bot - 3),
                                (cx_s - torso_w // 2 - 2, torso_bot - 3),
                            ])

        # MANY ARMS radiating out (thousand hand kannon).
        num_arms = 18
        for i in range(num_arms):
            arm_angle = math.pi * (i - num_arms // 2) / num_arms * 0.9 - math.pi / 2
            # Vary arm position along torso.
            arm_base_y = torso_top + int((i / num_arms) * (torso_bot - torso_top))
            arm_side = 1 if i % 2 == 0 else -1

            arm_base_x = cx_s + arm_side * (torso_w // 2)

            # Arm length varies.
            arm_len = int((30 + (i % 4) * 8) * sc)
            arm_tip_x = arm_base_x + int(math.cos(arm_angle * (0.3 + i / num_arms * 0.5)) *
                                          arm_len * arm_side)
            arm_tip_y = arm_base_y + int(math.sin(arm_angle * (0.3 + i / num_arms * 0.5)) *
                                          arm_len * 0.5)

            thickness = max(2, int(4 * sc))

            pygame.draw.line(statue_surf,
                             (*_NS_yamako.PALETTE["chakra_dark"], 150),
                             (arm_base_x, arm_base_y),
                             (arm_tip_x, arm_tip_y), thickness)
            pygame.draw.line(statue_surf,
                             (*_NS_yamako.PALETTE["chakra_mid"], 180),
                             (arm_base_x, arm_base_y),
                             (arm_tip_x, arm_tip_y), max(1, thickness - 1))

            # Small hand at tip.
            pygame.draw.circle(statue_surf,
                               (*_NS_yamako.PALETTE["chakra_light"], 200),
                               (arm_tip_x, arm_tip_y), 3)
            pygame.draw.rect(statue_surf,
                             (*_NS_yamako.PALETTE["chakra_hot"], 240),
                             (arm_tip_x, arm_tip_y, 1, 1))

        # Bright chakra core in statue chest.
        for r in range(15, 2, -1):
            alpha = _NS_yamako._alpha(150 * pulse * (15 - r) / 15)
            pygame.draw.circle(statue_surf,
                               (*_NS_yamako.PALETTE["chakra_light"], alpha),
                               (cx_s, int(cy_s - 20 * sc)), r)
        pygame.draw.circle(statue_surf,
                           _NS_yamako.PALETTE["chakra_shine"],
                           (cx_s, int(cy_s - 20 * sc)), 4)
        pygame.draw.circle(statue_surf, _NS_yamako.PALETTE["white"],
                           (cx_s, int(cy_s - 20 * sc)), 2)

        surface.blit(statue_surf, (statue_x - 90, statue_y - 120))

        # Massive chakra particles rising.
        for i in range(20):
            t = (phase * 0.5 + i * 0.05) % 1.0
            px = x - 50 + i * 5 + int(math.sin(phase + i) * 5)
            py = y + 30 - int(t * 100)
            alpha = _NS_yamako._alpha(230 * (1 - t) * pulse)
            if alpha > 0:
                _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_mid"], alpha),
                                       (px, py), 3)
                _NS_yamako._aacircle(surface, (*_NS_yamako.PALETTE["chakra_light"], alpha),
                                       (px, py), 2)
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_hot"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_yamako.PALETTE["chakra_shine"], alpha),
                                 (px, py, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_auroth(surface, boss, x, y):
    """Entry point auroth."""
    return _NS_auroth.draw_auroth(surface, boss, x, y)


def draw_morvein(surface, boss, x, y):
    """Entry point morvein."""
    return _NS_morvein.draw_morvein(surface, boss, x, y)


def draw_thorvak(surface, boss, x, y):
    """Entry point thorvak."""
    return _NS_thorvak.draw_thorvak(surface, boss, x, y)


def draw_yamako(surface, boss, x, y):
    """Entry point yamako."""
    return _NS_yamako.draw_yamako(surface, boss, x, y)
