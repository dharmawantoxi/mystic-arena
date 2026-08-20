"""
bosses/level16.py - Semua boss Level 16

Berisi:
  - ignirus     (mini boss - RANGED infernal pyromancer mage)
  - leoric      (mini boss - MELEE lionheart guardian tank)
  - shirotaka   (mini boss - MELEE tideborn tactician shinobi)
  - seiryukong  (TRUE BOSS - Celestial Simian, MELEE)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# ignirus.py
# ====================================================================



class _NS_ignirus:
    """Namespace ignirus - Infernal Pyromancer mage (RANGED)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe (dark crimson)
        "robe_darkest": (25, 5, 8),
        "robe_dark": (75, 15, 20),
        "robe_mid": (150, 35, 40),
        "robe_light": (215, 75, 60),
        "robe_edge": (245, 130, 90),

        # Gold trim (armor accents)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (105, 70, 20),
        "gold_mid": (195, 145, 45),
        "gold_light": (245, 205, 90),
        "gold_shine": (255, 245, 180),

        # Dark leather/plate underarmor
        "plate_darkest": (8, 5, 3),
        "plate_dark": (30, 20, 10),
        "plate_mid": (60, 40, 20),

        # FIRE (bright yellow-orange-red gradient)
        "fire_darkest": (60, 15, 0),
        "fire_dark": (170, 50, 5),
        "fire_mid": (240, 130, 20),
        "fire_light": (255, 200, 60),
        "fire_hot": (255, 240, 130),
        "fire_shine": (255, 253, 220),

        # Skin (warm mage complexion)
        "skin_dark": (110, 80, 65),
        "skin_mid": (185, 145, 115),
        "skin_light": (230, 195, 165),
        "skin_shine": (250, 225, 200),

        # Hair (fiery red-orange)
        "hair_dark": (100, 30, 15),
        "hair_mid": (200, 75, 20),
        "hair_light": (255, 150, 40),
        "hair_hot": (255, 220, 100),

        # Eyes (amber gold)
        "eye_socket": (10, 5, 0),
        "eye_dark": (80, 50, 10),
        "eye_mid": (230, 170, 50),
        "eye_light": (255, 230, 130),
        "eye_glow": (255, 250, 200),

        # Ember particles
        "ember_dim": (140, 60, 10),
        "ember_bright": (255, 180, 50),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 0),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ignirus._clamp(color)
        if _NS_ignirus.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_ignirus._clamp(color)
        if _NS_ignirus.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_ignirus._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_ignirus._clamp(color), points)

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
    def draw_ignirus(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_ignirus._update_ig_attack_anim(boss)
        attacking = (
            getattr(boss, "_ig_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_ignirus._draw_fire_aura(surface, x, y, pulse)
        _NS_ignirus._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_ignirus._draw_burstfireball_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ignirus._draw_vengeance_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_ignirus._draw_ig_attack(surface, boss, x, y)
        else:
            _NS_ignirus._draw_ig_idle(surface, boss, x, y)

        # Pyrogenic dragon passive icon flies (foreground).
        if active_skill or attacking:
            _NS_ignirus._draw_pyrogenic_dragon(surface, boss, x, y, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_ignirus._draw_searingtorrent_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_ignirus._draw_flameshot_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ignirus._draw_burstfireball_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ignirus._draw_vengeance_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_ig_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ig_previous_timer", 0))
        active = bool(getattr(boss, "_ig_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ig_attack_active = True
            boss._ig_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._ig_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._ig_attack_frame = int(
                getattr(boss, "_ig_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._ig_attack_active = False
            boss._ig_attack_frame = 0
            active = False

        boss._ig_previous_timer = timer
        boss._ig_attack_progress = (
            min(1.0, getattr(boss, "_ig_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_ig_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_ignirus._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_ignirus._draw_ember_wisps(surface, x, y + 42, boss.pulse)
        _NS_ignirus._draw_ig_body(surface, x, y + bob, boss.direction,
                                    boss.pulse, "idle")

    def _draw_ig_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_ig_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_ig_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.7) * 5)
        # Cast animation: pull hand back → thrust forward → recover.
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

        _NS_ignirus._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_ignirus._draw_ember_wisps(surface, x + lean, y + 42, boss.pulse, intense=True)
        _NS_ignirus._draw_ig_body(surface, x + lean, y + bob - lift,
                                    facing, boss.pulse, "attack",
                                    progress)
        _NS_ignirus._draw_fireball_projectile(surface, boss, x + lean,
                                                y + bob - lift, progress)

    # ============================================================
    # BODY (mage humanoid)
    # ============================================================
    def _draw_ig_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cape/robe back.
        _NS_ignirus._draw_flowing_robe(surface, cx, cy + 6, facing, phase)

        # Torso.
        _NS_ignirus._draw_mage_torso(surface, cx, cy - 2, facing, phase)

        # Back arm.
        _NS_ignirus._draw_back_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

        # Head with fiery hair.
        _NS_ignirus._draw_mage_head(surface, cx, cy - 14, facing, phase)

        # Front arm (casting arm) - last.
        _NS_ignirus._draw_cast_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

    def _draw_flowing_robe(surface, cx, cy, facing, phase):
        """Long dark red robe."""
        sway = math.sin(phase * 0.8) * 2

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
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in robe_pts])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["robe_darkest"], robe_pts)

        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 12 + int(sway), cy + 12),
            (cx + 8 + int(sway), cy + 17),
            (cx - 8 - int(sway), cy + 17),
            (cx - 12 - int(sway), cy + 12),
        ])

        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 8 + int(sway * 0.7), cy + 10),
            (cx + 5 + int(sway * 0.5), cy + 15),
            (cx - 5 - int(sway * 0.5), cy + 15),
            (cx - 8 - int(sway * 0.7), cy + 10),
        ])

        # Bright edge (fire tint).
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["robe_light"], [
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
        ])

        # Gold trim at bottom (embers).
        for i, (dx1, dx2, dy) in enumerate([
            (-13, 13, 12), (-11, 11, 16), (-8, 8, 20),
        ]):
            trim_y = cy + dy
            pygame.draw.line(surface, _NS_ignirus.PALETTE["gold_dark"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 2)
            pygame.draw.line(surface, _NS_ignirus.PALETTE["gold_mid"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 1)

        # Flame runes on robe.
        for i, (rx, ry) in enumerate([(-4, 4), (3, 6), (-2, 10), (5, 12)]):
            rune_x = cx + rx
            rune_y = cy + ry
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["gold_light"],
                             (rune_x, rune_y, 1, 1))
            if (int(phase * 3) + i) % 4 < 2:
                pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"],
                                 (rune_x, rune_y, 1, 1))

    def _draw_mage_torso(surface, cx, cy, facing, phase):
        """Chest armor with gold trim."""
        torso_pts = [
            (cx - 10, cy - 4),
            (cx - 8, cy + 5),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 8, cy + 5),
            (cx + 10, cy - 4),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ]
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["plate_darkest"], torso_pts)

        # Chest plate (dark leather).
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["plate_dark"], [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 7, cy + 5),
            (cx - 7, cy + 5),
        ])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["plate_mid"], [
            (cx - 6, cy - 3),
            (cx + 6, cy - 3),
            (cx + 5, cy + 3),
            (cx - 5, cy + 3),
        ])

        # Red robe over chest (overlapping).
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["robe_dark"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["robe_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])

        # Gold shoulder pauldrons (flame-shaped).
        for side in (-1, 1):
            _NS_ignirus._draw_flame_pauldron(surface, cx + side * 9, cy - 4, side, phase)

        # Central fire gem.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_y = cy + 1
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["gold_dark"],
                         (cx - 2, gem_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_darkest"],
                         (cx - 1, gem_y, 3, 2))
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_mid"],
                         (cx, gem_y, 1, 1))
        for r in range(4, 0, -1):
            alpha = _NS_ignirus._alpha(120 * pulse * (4 - r) / 4)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                    (cx, gem_y), r)

        # Gold belt line.
        pygame.draw.line(surface, _NS_ignirus.PALETTE["gold_dark"],
                         (cx - 8, cy + 6), (cx + 8, cy + 6), 1)
        pygame.draw.line(surface, _NS_ignirus.PALETTE["gold_mid"],
                         (cx - 7, cy + 6), (cx + 7, cy + 6), 1)

    def _draw_flame_pauldron(surface, cx, cy, side, phase):
        """Flame-shaped gold pauldron."""
        # Flame-like shape (pointy top).
        paul_pts = [
            (cx - 4, cy),
            (cx - 3, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 7),
            (cx + 3, cy - 5),
            (cx + 4, cy - 2),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ]
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["gold_darkest"], paul_pts)

        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["gold_dark"], [
            (cx - 3, cy),
            (cx - 2, cy - 3),
            (cx, cy - 5),
            (cx + 2, cy - 5),
            (cx + 3, cy - 2),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["gold_mid"], [
            (cx - 2, cy - 1),
            (cx - 1, cy - 3),
            (cx + 1, cy - 4),
            (cx + 2, cy - 2),
            (cx + 1, cy),
            (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["gold_shine"],
                         (cx, cy - 4, 1, 1))

        # Flame tip.
        pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_mid"],
                         (cx + 1, cy - 7, 1, 1))
        alpha = _NS_ignirus._alpha(200 * pulse)
        pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                         (cx + 1, cy - 7, 1, 1))

        # Small ember rising.
        for i in range(2):
            e_t = (phase * 1.5 + i * 0.5 + side) % 1.0
            ex = cx + 1 + int(math.sin(phase + i + side) * 1)
            ey = cy - 7 - int(e_t * 5)
            e_alpha = _NS_ignirus._alpha(200 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], e_alpha),
                             (ex, ey, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (idle at side or charging)."""
        sway = math.sin(phase * 0.7) * 1

        shoulder_x = cx - facing * 7
        shoulder_y = cy - 2
        # Back hand held down/side.
        hand_x = shoulder_x - facing * 1
        hand_y = shoulder_y + 10 + int(sway)

        # Arm segments.
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_darkest"],
                             (shoulder_x, shoulder_y), (hand_x, hand_y), 4)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_dark"],
                             (shoulder_x, shoulder_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["skin_dark"],
                               (hand_x, hand_y), 2)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["skin_mid"],
                               (hand_x, hand_y), 1)

        # Small flame in back hand (mage always has fire).
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_ignirus._alpha(120 * pulse * (4 - r) / 4)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                    (hand_x, hand_y - 2), r)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"], (hand_x, hand_y - 2), 2)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"], (hand_x, hand_y - 2), 1)
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"], (hand_x, hand_y - 2, 1, 1))

        # Rising ember from hand flame.
        for i in range(2):
            e_t = (phase * 1.5 + i * 0.5) % 1.0
            ex = hand_x + int(math.sin(phase + i) * 2)
            ey = hand_y - 3 - int(e_t * 8)
            e_alpha = _NS_ignirus._alpha(200 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], e_alpha),
                             (ex, ey, 1, 1))

    def _draw_cast_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front casting arm."""
        # Cast animation.
        if action == "attack":
            if attack_progress < 0.35:
                # Pull back.
                t = attack_progress / 0.35
                arm_angle = -0.3 - t * 0.5
            elif attack_progress < 0.55:
                # Thrust forward.
                t = (attack_progress - 0.35) / 0.20
                arm_angle = -0.8 + t * 1.3
            else:
                # Return.
                t = (attack_progress - 0.55) / 0.45
                arm_angle = 0.5 - t * 0.6
        else:
            arm_angle = -0.15 + math.sin(phase * 0.5) * 0.15

        shoulder_x = cx + facing * 7
        shoulder_y = cy - 2

        elbow_x = shoulder_x + int(math.cos(arm_angle) * 5) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * 5) + 3
        hand_x = elbow_x + int(math.cos(arm_angle * 0.5) * 6) * facing
        hand_y = elbow_y + int(math.sin(arm_angle * 0.5) * 3) + 2

        # Upper arm.
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 5)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_mid"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 1)

        # Forearm.
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_ignirus._aaline(surface, _NS_ignirus.PALETTE["robe_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Gold bracer at wrist.
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["gold_dark"],
                         (hand_x - 2, hand_y + 2, 5, 2))
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["gold_mid"],
                         (hand_x - 1, hand_y + 2, 3, 1))

        # Hand.
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["shadow_deep"],
                               (hand_x + 1, hand_y + 1), 3)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["skin_dark"],
                               (hand_x, hand_y), 3)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["skin_mid"],
                               (hand_x, hand_y), 2)

        # BIG FLAME IN CASTING HAND.
        _NS_ignirus._draw_hand_flame(surface, hand_x, hand_y, facing, phase, action)

        # Store hand pos for projectile.
        _NS_ignirus._cast_hand = (hand_x, hand_y - 2)

    def _draw_hand_flame(surface, hand_x, hand_y, facing, phase, action):
        """Big flame ball in hand."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        flame_y = hand_y - 3

        # Bigger during attack charge.
        if action == "attack":
            base_r = 8
        else:
            base_r = 6

        # Outer glow.
        for r in range(base_r + 5, 1, -1):
            alpha = _NS_ignirus._alpha(140 * pulse * (base_r + 5 - r) / (base_r + 5))
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                    (hand_x, flame_y), r)

        # Core flame (elongated upward).
        # Bottom big circle.
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_darkest"],
                               (hand_x, flame_y), base_r - 2)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"],
                               (hand_x, flame_y), base_r - 3)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"],
                               (hand_x, flame_y), base_r - 4)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_light"],
                               (hand_x, flame_y), base_r - 5)

        # Flame tongue rising (elongated shape).
        tongue_h = 6 + int(math.sin(phase * 3) * 2)
        for i in range(tongue_h):
            t = i / tongue_h
            width = int((1 - t) * 3)
            fy = flame_y - i - 3
            fx = hand_x + int(math.sin(phase * 4 + i * 0.5) * 1)

            if width > 0:
                if i < tongue_h // 3:
                    color = _NS_ignirus.PALETTE["fire_mid"]
                elif i < tongue_h * 2 // 3:
                    color = _NS_ignirus.PALETTE["fire_light"]
                else:
                    color = _NS_ignirus.PALETTE["fire_hot"]
                pygame.draw.rect(surface, color, (fx - width // 2, fy, width, 1))

        # Very bright core.
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"], (hand_x, flame_y), 2)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_shine"], (hand_x, flame_y), 1)
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["white"], (hand_x, flame_y, 1, 1))

        # Sparks around.
        for i in range(5):
            spark_angle = phase * 2 + i * math.pi * 2 / 5
            sx = hand_x + int(math.cos(spark_angle) * (base_r + 2))
            sy = flame_y + int(math.sin(spark_angle) * (base_r + 2))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"], (sx, sy, 1, 1))

    def _draw_mage_head(surface, cx, cy, facing, phase):
        """Head with fiery red hair."""
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
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["skin_dark"], head_pts)
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 4),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # FIERY HAIR (spiky, glowing).
        _NS_ignirus._draw_fire_hair(surface, cx, cy, facing, phase)

        # AMBER GLOWING EYES.
        _NS_ignirus._draw_mage_eyes(surface, cx, cy - 2, facing, phase)

        # Small nose.
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["skin_dark"], (cx, cy, 1, 1))

        # Stern mouth.
        pygame.draw.line(surface, _NS_ignirus.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

    def _draw_fire_hair(surface, cx, cy, facing, phase):
        """Wild fiery red hair with flame-like tips."""
        wave = math.sin(phase * 1.5) * 1

        # Base hair mass on top.
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["hair_dark"], [
            (cx - 5, cy - 5),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx, cy - 10),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 5, cy - 5),
            (cx + 4, cy - 3),
            (cx - 4, cy - 3),
        ])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["hair_mid"], [
            (cx - 4, cy - 5),
            (cx - 3, cy - 8),
            (cx, cy - 9),
            (cx + 3, cy - 8),
            (cx + 4, cy - 5),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_ignirus._poly(surface, _NS_ignirus.PALETTE["hair_light"], [
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])

        # SPIKY FLAME TIPS (5-7 tips going up, wavy).
        for i, (spike_x_off, spike_h_base) in enumerate([
            (-5, 4), (-3, 6), (-1, 8), (1, 9), (3, 7), (5, 4),
        ]):
            spike_h = spike_h_base + int(math.sin(phase * 2 + i * 0.5) * 2)
            spike_x = cx + spike_x_off + int(wave * 0.5)
            spike_top_y = cy - 10 - spike_h

            # Flame tip (tapered upward).
            for j in range(spike_h):
                t = j / spike_h
                width = max(1, int((1 - t) * 2))
                fy = cy - 10 - j
                fx = spike_x + int(math.sin(phase * 3 + i + j * 0.3) * 1)

                if j < spike_h // 3:
                    color = _NS_ignirus.PALETTE["hair_dark"]
                elif j < spike_h * 2 // 3:
                    color = _NS_ignirus.PALETTE["hair_mid"]
                elif j < spike_h * 4 // 5:
                    color = _NS_ignirus.PALETTE["hair_light"]
                else:
                    color = _NS_ignirus.PALETTE["fire_hot"]
                pygame.draw.rect(surface, color, (fx - width // 2, fy, width, 1))

            # Very hot tip.
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"],
                             (spike_x, cy - 10 - spike_h, 1, 1))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_shine"],
                             (spike_x, cy - 10 - spike_h, 1, 1))

        # Ember particles rising from hair.
        for i in range(4):
            e_t = (phase * 0.7 + i * 0.25) % 1.0
            ex = cx - 4 + i * 3 + int(math.sin(phase + i) * 2)
            ey = cy - 15 - int(e_t * 10)
            alpha = _NS_ignirus._alpha(200 * (1 - e_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["ember_bright"], alpha),
                                 (ex, ey, 1, 1))

        # Side hair (short strands).
        for side in (-1, 1):
            side_x = cx + side * 5
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["hair_dark"],
                             (side_x, cy - 4, 1, 4))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["hair_mid"],
                             (side_x, cy - 3, 1, 3))

    def _draw_mage_eyes(surface, cx, cy, facing, phase):
        """Amber glowing eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_ignirus.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["eye_socket"],
                             (ex, ey - 1, 1, 2))

            # Glow.
            for r in range(3, 0, -1):
                alpha = _NS_ignirus._alpha(140 * pulse * (3 - r) / 3)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)

            pygame.draw.rect(surface, _NS_ignirus.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["eye_glow"], (ex, ey, 1, 1))

    # ============================================================
    # PYROGENIC DRAGON (Passive)
    # ============================================================
    def _draw_pyrogenic_dragon(surface, boss, x, y, phase):
        """Small pyrogenic dragon flying around boss (passive)."""
        facing = boss.direction

        # Dragon orbits boss.
        orbit_angle = phase * 1.5
        orbit_r = 30
        dx = x + int(math.cos(orbit_angle) * orbit_r) - 15 * facing
        dy = y - 20 + int(math.sin(orbit_angle) * orbit_r * 0.4)

        dragon_facing = 1 if math.cos(orbit_angle) > 0 else -1

        # Dragon body (small dragon silhouette).
        # Body oval.
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_darkest"], (dx, dy), 4)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"], (dx, dy), 3)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"], (dx, dy), 2)

        # Wings (2 small).
        wing_flap = math.sin(phase * 4) * 3
        for side in (-1, 1):
            wing_tip_x = dx + side * 6
            wing_tip_y = dy - 3 + int(wing_flap)
            pygame.draw.line(surface, _NS_ignirus.PALETTE["fire_dark"],
                             (dx, dy - 1), (wing_tip_x, wing_tip_y), 2)
            pygame.draw.line(surface, _NS_ignirus.PALETTE["fire_mid"],
                             (dx, dy - 1), (wing_tip_x, wing_tip_y), 1)
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"],
                             (wing_tip_x, wing_tip_y, 1, 1))

        # Head/snout.
        head_x = dx + dragon_facing * 4
        head_y = dy - 1
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"], (head_x, head_y), 2)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"], (head_x, head_y), 1)
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"],
                         (head_x + dragon_facing, head_y, 1, 1))

        # Tail.
        tail_x = dx - dragon_facing * 5
        tail_y = dy + 1
        pygame.draw.line(surface, _NS_ignirus.PALETTE["fire_dark"],
                         (dx, dy + 1), (tail_x, tail_y), 2)
        pygame.draw.line(surface, _NS_ignirus.PALETTE["fire_mid"],
                         (dx, dy + 1), (tail_x, tail_y), 1)
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"], (tail_x, tail_y, 1, 1))

        # Glow around dragon.
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(8, 1, -1):
            alpha = _NS_ignirus._alpha(80 * pulse * (8 - r) / 8)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                    (dx, dy), r)

        # Trailing embers.
        for i in range(3):
            trail_angle = orbit_angle - i * 0.3
            tx = x + int(math.cos(trail_angle) * orbit_r) - 15 * facing
            ty = y - 20 + int(math.sin(trail_angle) * orbit_r * 0.4)
            alpha = _NS_ignirus._alpha(180 - i * 50)
            pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                             (tx, ty, 1, 1))

    # ============================================================
    # FIREBALL PROJECTILE (Basic attack)
    # ============================================================
    def _draw_fireball_projectile(surface, boss, x, y, progress):
        """Small fireball projectile."""
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_ignirus._target_position(boss, x, y)

        if hasattr(_NS_ignirus, "_cast_hand"):
            start_x, start_y = _NS_ignirus._cast_hand
        else:
            start_x = x + facing * 15
            start_y = y - 5

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Comet trail.
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_ignirus._alpha(230 - i * 25)

            size = max(1, 7 - i)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                    (px, py), size)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                    (px, py), max(1, size - 3))

            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright fireball head.
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_darkest"], (bx, by), 8)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"], (bx, by), 6)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"], (bx, by), 4)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_light"], (bx, by), 3)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"], (bx, by), 2)
        _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_ignirus.PALETTE["white"], (bx, by, 1, 1))

        # Radial glow.
        for r in range(12, 3, -2):
            alpha = _NS_ignirus._alpha(80 * (12 - r) / 12)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                    (bx, by), r)

        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_ignirus._alpha(240 * (1 - st))
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                    (tx, ty), max(1, radius - 4), 2)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                    (tx, ty), max(1, radius - 10), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((120, 22), pygame.SRCALPHA)
        w = int(90 * pulse)
        h = int(11 * pulse)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (60 - w // 2 - radius, 11 - h // 2 - radius // 2,
                 w + radius * 2, h + radius),
            )
        pygame.draw.ellipse(shadow, (20, 5, 5, 160),
                            (60 - w // 2, 11 - h // 2, w, h))
        surface.blit(shadow, (x - 60, y - 11))

    def _draw_ember_wisps(surface, cx, cy, phase, intense=False):
        """Rising ember particles."""
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 30 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_ignirus._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                    (sx, sy), 3)
            _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Ember sparks.
        for i in range(8):
            spark_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 26)
            alpha = _NS_ignirus._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_ignirus._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_ignirus._aacircle(aura, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_ignirus._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_ignirus._aacircle(aura, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_ignirus._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_ignirus._aacircle(aura, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Orbiting fire embers.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_ignirus.PALETTE["fire_darkest"], 200),
                            (5, 18, 160, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_ignirus.PALETTE["fire_dark"], 220),
                            (14, 20, 142, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_ignirus.PALETTE["fire_mid"], 230),
                            (25, 22, 120, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_ignirus.PALETTE["fire_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_ignirus.PALETTE["fire_hot"],
                                        _NS_ignirus._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q: SEARING TORRENT (elongated fire torrent)
    # ============================================================
    def _draw_searingtorrent_foreground(surface, boss, x, y, timer, phase):
        """Long scorching torrent of fire forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if hasattr(_NS_ignirus, "_cast_hand"):
            start_x, start_y = _NS_ignirus._cast_hand
        else:
            start_x = x + facing * 15
            start_y = y - 5

        if progress < 0.2:
            # Charge in hand.
            t = progress / 0.2
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_ignirus._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"],
                                    (start_x, start_y), max(1, cr - 4))
        else:
            # UNLEASH torrent forward.
            t = (progress - 0.2) / 0.8
            intensity = math.sin(t * math.pi) * 0.5 + 0.5

            # Torrent extends forward as elongated flame.
            torrent_len = int(120 * min(1.0, t * 2))

            # Draw as multiple layered thick oval strokes.
            for layer_i, (thickness, alpha_val, color_key) in enumerate([
                (14, 100, "fire_darkest"),
                (11, 140, "fire_dark"),
                (8, 180, "fire_mid"),
                (5, 220, "fire_light"),
                (3, 250, "fire_hot"),
                (1, 255, "fire_shine"),
            ]):
                actual_alpha = _NS_ignirus._alpha(alpha_val * intensity)
                # Draw as thick line.
                pygame.draw.line(surface,
                                 (*_NS_ignirus.PALETTE[color_key], actual_alpha),
                                 (start_x, start_y),
                                 (start_x + facing * torrent_len, start_y), thickness)

            # Waving fire tongues along torrent (irregular flames).
            num_flames = 8
            for i in range(num_flames):
                seg_t = i / num_flames
                sx = start_x + facing * int(torrent_len * seg_t)
                # Wave pattern.
                sy = start_y + int(math.sin(phase * 4 + i * 0.5) * 6)

                # Flame tongue at each segment.
                flame_h = 8 + int(math.sin(phase * 3 + i) * 3)
                for h in range(flame_h):
                    ht = h / flame_h
                    width = max(1, int((1 - ht) * 4))
                    fy = sy - h - 3
                    fx = sx + int(math.sin(phase * 5 + h * 0.3) * 1)

                    if h < flame_h // 3:
                        color = _NS_ignirus.PALETTE["fire_mid"]
                    elif h < flame_h * 2 // 3:
                        color = _NS_ignirus.PALETTE["fire_light"]
                    else:
                        color = _NS_ignirus.PALETTE["fire_hot"]
                    alpha_v = _NS_ignirus._alpha(200 * intensity)
                    pygame.draw.rect(surface, (*color, alpha_v),
                                     (fx - width // 2, fy, width, 1))

            # Sparks flying off.
            for i in range(16):
                spark_t = (phase * 3 + i * 0.08) % 1.0
                spark_x = start_x + facing * int(torrent_len * spark_t)
                spark_y = start_y + int(math.sin(phase * 5 + i) * 10)
                alpha = _NS_ignirus._alpha(240 * intensity)
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_shine"], alpha),
                                 (spark_x, spark_y, 1, 1))

            # Bright source at hand.
            for r in range(10, 1, -1):
                alpha = _NS_ignirus._alpha(180 * intensity * (10 - r) / 10)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                        (start_x, start_y), r)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"],
                                    (start_x, start_y), 4)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["white"],
                                    (start_x, start_y), 2)

    # ============================================================
    # SKILL W: FLAME SHOT (bigger fireball)
    # ============================================================
    def _draw_flameshot_foreground(surface, boss, x, y, timer, phase):
        """Enhanced fireball with bigger trail."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_ignirus._target_position(boss, x, y)

        if hasattr(_NS_ignirus, "_cast_hand"):
            start_x, start_y = _NS_ignirus._cast_hand
        else:
            start_x = x + facing * 15
            start_y = y - 5

        if progress < 0.2:
            # Charge (bigger).
            t = progress / 0.2
            cr = int(5 + t * 12)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_ignirus._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                        (start_x, start_y), r)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"],
                                    (start_x, start_y), max(1, cr - 4))
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_shine"],
                                    (start_x, start_y), max(1, cr - 6))
        else:
            t = (progress - 0.2) / 0.8
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Extra bright trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_ignirus._alpha(240 - i * 20)

                size = max(1, 10 - i)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                        (px, py), size)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                        (px, py), max(1, size - 3))

                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Huge fireball head.
            for r in range(15, 3, -2):
                alpha = _NS_ignirus._alpha(100 * (15 - r) / 15)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_light"], alpha),
                                        (bx, by), r)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_darkest"], (bx, by), 10)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"], (bx, by), 8)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"], (bx, by), 5)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_light"], (bx, by), 3)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["white"], (bx, by, 1, 1))

            # Impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_ignirus._alpha(240 * (1 - st))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                        (tx, ty), radius + 4, 3)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL E: BURST FIREBALL (AoE explosion at target)
    # ============================================================
    def _draw_burstfireball_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_ignirus._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.5:
            # AoE circle on ground.
            t = (progress - 0.5) / 0.5
            r = int(20 + t * 30)
            alpha = _NS_ignirus._alpha(220 * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_burstfireball_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_ignirus._target_position(boss, x, y)

        if hasattr(_NS_ignirus, "_cast_hand"):
            start_x, start_y = _NS_ignirus._cast_hand
        else:
            start_x = x + facing * 15
            start_y = y - 5

        if progress < 0.5:
            # Fireball flying to target.
            t = progress / 0.5
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Trail.
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_ignirus._alpha(200 - i * 22)
                size = max(1, 6 - i)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                                        (px, py), size)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                                        (px, py), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                 (px, py, 1, 1))

            # Fireball head.
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_darkest"], (bx, by), 6)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_dark"], (bx, by), 5)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_mid"], (bx, by), 3)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"], (bx, by), 2)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_shine"], (bx, by), 1)
        else:
            # BURST EXPLOSION at target.
            t = (progress - 0.5) / 0.5
            intensity = math.sin(t * math.pi) * 0.5 + 0.5
            radius = int(20 + t * 35)
            alpha = _NS_ignirus._alpha(255 * intensity)

            # Multi-layer explosion.
            for r in range(radius, 2, -3):
                a = _NS_ignirus._alpha(alpha * (radius - r) / radius)
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_darkest"], a),
                                        (tx, ty), r)
            for r in range(int(radius * 0.8), 2, -3):
                a = _NS_ignirus._alpha(alpha * (radius * 0.8 - r) / (radius * 0.8))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_dark"], a),
                                        (tx, ty), r)
            for r in range(int(radius * 0.6), 2, -2):
                a = _NS_ignirus._alpha(alpha * (radius * 0.6 - r) / (radius * 0.6))
                _NS_ignirus._aacircle(surface, (*_NS_ignirus.PALETTE["fire_mid"], a),
                                        (tx, ty), r)
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_hot"], (tx, ty), max(1, radius // 4))
            _NS_ignirus._aacircle(surface, _NS_ignirus.PALETTE["fire_shine"], (tx, ty), max(1, radius // 6))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["white"], (tx, ty, 1, 1))

            # Radial burst.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.line(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 2, 2))

            # Rising sparkles.
            for i in range(12):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                sx = tx - 15 + i * 3 + int(math.sin(phase + i) * 3)
                sy = ty - int(spark_t * 30)
                s_alpha = _NS_ignirus._alpha(220 * intensity * (1 - spark_t))
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], s_alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL R: VENGEANCE FLAMES (ring of fire around boss)
    # ============================================================
    def _draw_vengeance_ground(surface, boss, x, y, timer, phase):
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ring of fire on ground.
        r = 55 + int(math.sin(phase * 2) * 3)
        alpha = _NS_ignirus._alpha(220)
        pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_darkest"], alpha),
                            (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_dark"], alpha),
                            (x - r + 3, y + 45 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_mid"], alpha),
                            (x - r + 8, y + 45 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_vengeance_foreground(surface, boss, x, y, timer, phase):
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # RING OF FLAMES around boss.
        r = 55
        num_flames = 16

        for i in range(num_flames):
            angle = i * math.pi * 2 / num_flames + phase * 0.3
            # Position on ellipse (isometric-ish).
            fx = x + int(math.cos(angle) * r)
            fy = y + 45 + int(math.sin(angle) * r * 0.35)

            # Draw flame column rising.
            flame_h = 10 + int(math.sin(phase * 3 + i) * 4)
            for h in range(flame_h):
                ht = h / flame_h
                width = max(1, int((1 - ht) * 4))
                fy_pos = fy - h
                fx_pos = fx + int(math.sin(phase * 4 + i + h * 0.5) * 1)

                if h < flame_h // 3:
                    color = _NS_ignirus.PALETTE["fire_dark"]
                elif h < flame_h * 2 // 3:
                    color = _NS_ignirus.PALETTE["fire_mid"]
                elif h < flame_h * 4 // 5:
                    color = _NS_ignirus.PALETTE["fire_light"]
                else:
                    color = _NS_ignirus.PALETTE["fire_hot"]
                pygame.draw.rect(surface, color, (fx_pos - width // 2, fy_pos, width, 1))

            # Very hot tip.
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_hot"],
                             (fx, fy - flame_h, 1, 1))
            pygame.draw.rect(surface, _NS_ignirus.PALETTE["fire_shine"],
                             (fx, fy - flame_h, 1, 1))

            # Rising ember.
            e_t = (phase * 1 + i * 0.1) % 1.0
            ex = fx + int(math.sin(phase + i) * 2)
            ey = fy - flame_h - int(e_t * 15)
            alpha = _NS_ignirus._alpha(220 * (1 - e_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_ignirus.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Center pulse waves.
        pulse_t = (phase * 0.6) % 1.0
        pulse_r = int(r * 0.7 + pulse_t * 20)
        pulse_alpha = _NS_ignirus._alpha(180 * (1 - pulse_t))
        if pulse_alpha > 0:
            pygame.draw.ellipse(surface, (*_NS_ignirus.PALETTE["fire_hot"], pulse_alpha),
                                (x - pulse_r, y + 45 - pulse_r // 3,
                                 pulse_r * 2, pulse_r * 2 // 3), 2)


# ====================================================================
# leoric.py
# ====================================================================



class _NS_leoric:
    """Namespace leoric - Lionheart Guardian knight tank (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Gold armor (main)
        "gold_darkest": (35, 20, 5),
        "gold_dark": (95, 65, 20),
        "gold_mid": (180, 130, 40),
        "gold_light": (240, 195, 80),
        "gold_edge": (255, 225, 130),
        "gold_shine": (255, 250, 210),

        # Blue royal (accent armor, cloth)
        "royal_darkest": (5, 10, 30),
        "royal_dark": (15, 30, 75),
        "royal_mid": (35, 65, 140),
        "royal_light": (80, 130, 210),
        "royal_edge": (150, 190, 240),

        # Steel silver (sword, plating)
        "steel_dark": (30, 35, 45),
        "steel_mid": (95, 105, 125),
        "steel_light": (170, 180, 200),
        "steel_shine": (230, 235, 245),

        # Holy light energy
        "holy_darkest": (50, 30, 5),
        "holy_dark": (140, 90, 15),
        "holy_mid": (240, 180, 50),
        "holy_light": (255, 220, 110),
        "holy_hot": (255, 245, 170),
        "holy_shine": (255, 253, 230),

        # Skin (warrior tan)
        "skin_dark": (100, 75, 60),
        "skin_mid": (175, 140, 115),
        "skin_light": (225, 195, 170),
        "skin_shine": (250, 225, 205),

        # Hair (brown short)
        "hair_dark": (60, 40, 20),
        "hair_mid": (110, 75, 40),
        "hair_light": (170, 130, 80),

        # Eyes (warm brown)
        "eye_socket": (20, 15, 10),
        "eye_dark": (70, 45, 25),
        "eye_mid": (140, 100, 60),
        "eye_light": (220, 180, 130),

        # Cape (dark blue-purple)
        "cape_dark": (10, 8, 30),
        "cape_mid": (30, 25, 70),
        "cape_light": (70, 60, 130),

        # Sapphire gems
        "gem_dark": (10, 30, 80),
        "gem_mid": (60, 130, 220),
        "gem_light": (160, 220, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_leoric._clamp(color)
        if _NS_leoric.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_leoric._clamp(color)
        if _NS_leoric.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_leoric._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_leoric._clamp(color), points)

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
    def draw_leoric(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_leoric._update_lr_attack_anim(boss)
        attacking = (
            getattr(boss, "_lr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        immortal = active_skill == "r"

        # Ambient.
        _NS_leoric._draw_holy_aura(surface, x, y, pulse, immortal)
        _NS_leoric._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_leoric._draw_sacredhammer_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_leoric._draw_fearlesscharge_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_leoric._draw_lr_attack(surface, boss, x, y)
        else:
            _NS_leoric._draw_lr_idle(surface, boss, x, y)

        # Immortality shield bubble (over body).
        if active_skill == "r":
            _NS_leoric._draw_immortality_shield(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_leoric._draw_fearlesscharge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_leoric._draw_sacredhammer_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_leoric._draw_concealblast_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_lr_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_lr_previous_timer", 0))
        active = bool(getattr(boss, "_lr_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._lr_attack_active = True
            boss._lr_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._lr_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._lr_attack_frame = int(
                getattr(boss, "_lr_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._lr_attack_active = False
            boss._lr_attack_frame = 0
            active = False

        boss._lr_previous_timer = timer
        boss._lr_attack_progress = (
            min(1.0, getattr(boss, "_lr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_lr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_leoric._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_leoric._draw_holy_wisps(surface, x, y + 45, boss.pulse)
        _NS_leoric._draw_lr_body(surface, x, y + bob, boss.direction,
                                   boss.pulse, "idle")

    def _draw_lr_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_lr_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_lr_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.5) * 4)
        # Sword swing wind-up → forward slash → recovery.
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

        _NS_leoric._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_leoric._draw_holy_wisps(surface, x + lean, y + 45, boss.pulse, intense=True)
        _NS_leoric._draw_lr_body(surface, x + lean, y + bob - lift,
                                   facing, boss.pulse, "attack",
                                   progress)
        _NS_leoric._draw_sword_slash_arc(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (heavy armored knight)
    # ============================================================
    def _draw_lr_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cape behind.
        _NS_leoric._draw_cape(surface, cx, cy - 2, facing, phase)

        # Legs/skirt.
        _NS_leoric._draw_knight_legs(surface, cx, cy + 10, facing, phase)

        # Torso (chest armor + blue cloth).
        _NS_leoric._draw_knight_torso(surface, cx, cy - 2, facing, phase)

        # LION SHIELD arm (opposite of sword arm).
        # Shield is on LEFT side of character (opposite of facing direction if facing right).
        # But for visual consistency, shield goes to back-side (side away from viewer).
        shield_side = -1  # Always draw shield on back side.
        _NS_leoric._draw_shield_arm(surface, cx, cy - 2, facing, shield_side, phase, action,
                                      attack_progress)

        # Head with hair.
        _NS_leoric._draw_knight_head(surface, cx, cy - 18, facing, phase)

        # Sword arm (front) - drawn last.
        _NS_leoric._draw_sword_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Dark blue cape flowing behind."""
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
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 2) for p in cape_pts])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["cape_dark"], cape_pts)
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["cape_mid"], [
            (cx - 6, cy + 1),
            (cx + 6, cy + 1),
            (cx + 10 + int(sway), cy + 11),
            (cx + 7 + int(sway), cy + 22),
            (cx - 7 - int(sway), cy + 22),
            (cx - 10 - int(sway), cy + 11),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["cape_light"], [
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 4, cy + 14),
            (cx - 4, cy + 14),
        ])

        # Gold trim at bottom edge.
        for dx1, dx2, dy in [(-13, 13, 18), (-11, 11, 22)]:
            trim_y = cy + dy
            pygame.draw.line(surface, _NS_leoric.PALETTE["gold_dark"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 1)
            pygame.draw.line(surface, _NS_leoric.PALETTE["gold_light"],
                             (cx + dx1 - int(sway), trim_y),
                             (cx + dx2 + int(sway), trim_y), 1)

    def _draw_knight_legs(surface, cx, cy, facing, phase):
        """Armored skirt/tassets covering legs."""
        # Gold plate skirt.
        skirt_pts = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy + 4),
            (cx + 10, cy + 12),
            (cx + 6, cy + 16),
            (cx - 6, cy + 16),
            (cx - 10, cy + 12),
            (cx - 12, cy + 4),
        ]
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 3) for p in skirt_pts])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_darkest"], skirt_pts)

        # Main gold plate.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_dark"], [
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 11, cy + 4),
            (cx + 9, cy + 11),
            (cx + 5, cy + 15),
            (cx - 5, cy + 15),
            (cx - 9, cy + 11),
            (cx - 11, cy + 4),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 9, cy + 3),
            (cx + 7, cy + 10),
            (cx + 4, cy + 13),
            (cx - 4, cy + 13),
            (cx - 7, cy + 10),
            (cx - 9, cy + 3),
        ])

        # Vertical plate divisions.
        for x_off in (-6, 0, 6):
            pygame.draw.line(surface, _NS_leoric.PALETTE["gold_darkest"],
                             (cx + x_off, cy - 4),
                             (cx + int(x_off * 1.3), cy + 13), 1)
            pygame.draw.line(surface, _NS_leoric.PALETTE["gold_edge"],
                             (cx + x_off + 1, cy - 4),
                             (cx + int(x_off * 1.3) + 1, cy + 13), 1)

        # Blue cloth underneath (visible through gaps).
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["royal_dark"], [
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 3, cy + 16),
            (cx - 3, cy + 16),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["royal_mid"], [
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 2, cy + 14),
            (cx - 2, cy + 14),
        ])

        # Central emblem (small cross/gem).
        emblem_y = cy + 5
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_darkest"],
                              (cx, emblem_y), 3)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gem_dark"],
                              (cx, emblem_y), 2)
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gem_light"],
                         (cx, emblem_y, 1, 1))

        # BOOTS/GREAVES below.
        for side in (-1, 1):
            boot_x = cx + side * 4
            _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"], [
                (boot_x - 3, cy + 15),
                (boot_x + 3, cy + 15),
                (boot_x + 4, cy + 22),
                (boot_x - 4, cy + 22),
            ])
            _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_darkest"], [
                (boot_x - 3, cy + 14),
                (boot_x + 3, cy + 14),
                (boot_x + 4, cy + 21),
                (boot_x - 4, cy + 21),
            ])
            _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_dark"], [
                (boot_x - 3, cy + 15),
                (boot_x + 3, cy + 15),
                (boot_x + 3, cy + 20),
                (boot_x - 3, cy + 20),
            ])
            _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_mid"], [
                (boot_x - 2, cy + 16),
                (boot_x + 2, cy + 16),
                (boot_x + 2, cy + 19),
                (boot_x - 2, cy + 19),
            ])
            pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_edge"],
                             (boot_x - 1, cy + 17, 2, 1))

    def _draw_knight_torso(surface, cx, cy, facing, phase):
        """Chest armor with royal blue underneath."""
        # Torso base.
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
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_darkest"], torso_pts)

        # Main gold chest plate.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_dark"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 8, cy + 6),
            (cx - 8, cy + 6),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ])

        # Muscle V-lines.
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_darkest"],
                         (cx, cy - 3), (cx - 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_darkest"],
                         (cx, cy - 3), (cx + 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_edge"],
                         (cx, cy - 2), (cx - 3, cy + 4), 1)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_edge"],
                         (cx, cy - 2), (cx + 3, cy + 4), 1)

        # Blue cloth chest strip (visible in middle).
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["royal_dark"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["royal_mid"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        pygame.draw.rect(surface, _NS_leoric.PALETTE["royal_edge"],
                         (cx - 1, cy - 2, 2, 1))

        # Central sapphire gem.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_y = cy + 1
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_dark"],
                         (cx - 2, gem_y - 1, 4, 3))
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gem_dark"], [
            (cx - 1, gem_y),
            (cx, gem_y - 1),
            (cx + 1, gem_y),
            (cx, gem_y + 1),
        ])
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gem_light"], (cx, gem_y, 1, 1))
        # Glow.
        for r in range(4, 0, -1):
            alpha = _NS_leoric._alpha(80 * pulse * (4 - r) / 4)
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["gem_mid"], alpha),
                                   (cx, gem_y), r)

        # SHOULDER PAULDRONS (big gold with spikes).
        for side in (-1, 1):
            _NS_leoric._draw_pauldron(surface, cx + side * 10, cy - 4, side, phase)

    def _draw_pauldron(surface, cx, cy, side, phase):
        """Big spiked shoulder pauldron."""
        # Main pauldron shape.
        paul_pts = [
            (cx - 4, cy),
            (cx - 3, cy - 5),
            (cx - 1, cy - 7),
            (cx + 2, cy - 7),
            (cx + 4, cy - 5),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ]
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_darkest"], paul_pts)

        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_dark"], [
            (cx - 3, cy - 1),
            (cx - 2, cy - 4),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
            (cx + 3, cy - 4),
            (cx + 4, cy - 1),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_mid"], [
            (cx - 2, cy - 2),
            (cx - 1, cy - 5),
            (cx + 2, cy - 5),
            (cx + 3, cy - 2),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_edge"],
                         (cx - 1, cy - 4, 3, 1))
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_shine"],
                         (cx, cy - 4, 1, 1))

        # Small blue gem in pauldron center.
        pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gem_dark"], (cx, cy - 1, 1, 1))
        pygame.draw.rect(surface, (*_NS_leoric.PALETTE["gem_light"],
                                    _NS_leoric._alpha(220 * pulse)), (cx, cy - 1, 1, 1))

        # Curved edge highlight.
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_edge"],
                         (cx - 3, cy - 1), (cx + 3, cy - 1), 1)

    def _draw_shield_arm(surface, cx, cy, facing, shield_side, phase, action, attack_progress):
        """Arm holding lion shield."""
        # Shield arm holds still or braces.
        if action == "attack":
            arm_lift = int(math.sin(attack_progress * math.pi) * -1)
        else:
            arm_lift = int(math.sin(phase * 0.4) * 1)

        # Shield side (opposite of facing sword arm).
        arm_side = -facing  # Always opposite of facing.
        shoulder_x = cx + arm_side * 9
        shoulder_y = cy - 3
        # Arm bent forward holding shield in front.
        elbow_x = shoulder_x + arm_side * 2
        elbow_y = shoulder_y + 5 + arm_lift
        hand_x = shoulder_x + arm_side * 4
        hand_y = shoulder_y + 3

        # Upper arm.
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)

        # Forearm (goes to shield behind it).
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)

        # LION SHIELD.
        _NS_leoric._draw_lion_shield(surface, hand_x + arm_side * 6, hand_y - 2,
                                       arm_side, phase)

    def _draw_lion_shield(surface, cx, cy, facing, phase):
        """Big golden lion crest shield."""
        # Shield shape (kite/teardrop).
        shield_pts = [
            (cx - 6, cy - 8),
            (cx + 6, cy - 8),
            (cx + 8, cy - 4),
            (cx + 8, cy + 4),
            (cx + 5, cy + 10),
            (cx, cy + 12),
            (cx - 5, cy + 10),
            (cx - 8, cy + 4),
            (cx - 8, cy - 4),
        ]
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in shield_pts])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_darkest"], shield_pts)

        # Main gold face.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_dark"], [
            (cx - 5, cy - 7),
            (cx + 5, cy - 7),
            (cx + 7, cy - 4),
            (cx + 7, cy + 3),
            (cx + 4, cy + 9),
            (cx, cy + 11),
            (cx - 4, cy + 9),
            (cx - 7, cy + 3),
            (cx - 7, cy - 4),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["gold_mid"], [
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy - 3),
            (cx + 6, cy + 2),
            (cx + 3, cy + 7),
            (cx, cy + 9),
            (cx - 3, cy + 7),
            (cx - 6, cy + 2),
            (cx - 6, cy - 3),
        ])

        # Highlight edge.
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_edge"],
                         (cx - 5, cy - 7), (cx + 5, cy - 7), 1)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_shine"],
                         (cx - 2, cy - 7), (cx + 2, cy - 7), 1)

        # BLUE CENTER (background for lion).
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["royal_dark"], [
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 4, cy - 2),
            (cx + 4, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 3),
            (cx - 4, cy - 2),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["royal_mid"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 3, cy - 1),
            (cx + 3, cy + 2),
            (cx + 1, cy + 5),
            (cx - 1, cy + 5),
            (cx - 3, cy + 2),
            (cx - 3, cy - 1),
        ])

        # LION HEAD in center (simplified pixel).
        # Mane (surrounding golden).
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_dark"], (cx, cy), 4)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_mid"], (cx, cy), 3)

        # Lion face (small).
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_edge"], (cx - 2, cy - 1, 4, 3))
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_dark"], (cx - 1, cy - 1, 1, 1))  # eye
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_dark"], (cx + 1, cy - 1, 1, 1))  # eye
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_darkest"], (cx, cy + 1, 1, 1))  # nose

        # Small mane spikes around head.
        for i in range(8):
            angle = i * math.pi / 4
            mx = cx + int(math.cos(angle) * 5)
            my = cy + int(math.sin(angle) * 5)
            pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_edge"], (mx, my, 1, 1))
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_shine"], (mx, my, 1, 1))

        # Center gem below lion.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_y = cy + 6
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gem_dark"], (cx - 1, gem_y, 2, 2))
        pygame.draw.rect(surface, (*_NS_leoric.PALETTE["gem_light"],
                                    _NS_leoric._alpha(220 * pulse)), (cx, gem_y, 1, 1))

        # Border rivets/studs around shield edge.
        for angle in [-math.pi / 3, 0, math.pi / 3, math.pi / 2, math.pi * 2 / 3,
                      math.pi, -math.pi * 2 / 3, -math.pi / 2]:
            rx = cx + int(math.cos(angle) * 6.5)
            ry = cy + int(math.sin(angle) * 8)
            pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_darkest"], (rx, ry, 1, 1))
            pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_edge"], (rx, ry, 1, 1))

    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding long sword."""
        # Sword swing angle.
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.2 + t * -math.pi * 0.5
                sword_angle = arm_angle - math.pi * 0.15
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.7 + t * math.pi * 1.0
                sword_angle = arm_angle
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.3 - t * math.pi * 0.5
                sword_angle = arm_angle + math.pi * 0.05
        else:
            arm_angle = -math.pi * 0.15 + math.sin(phase * 0.5) * 0.05
            sword_angle = arm_angle - math.pi * 0.1

        shoulder_x = cx + facing * 10
        shoulder_y = cy - 3

        arm_len = 8
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len) + 2

        forearm_len = 7
        forearm_angle = arm_angle + 0.3
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm.
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_edge"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)

        # Forearm (gold gauntlet).
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_leoric._aaline(surface, _NS_leoric.PALETTE["gold_mid"],
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), 1)

        # Gauntlet (big fist with knuckle detail).
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 4)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_darkest"],
                              (hand_x, hand_y), 4)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_dark"],
                              (hand_x, hand_y), 3)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_mid"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_edge"],
                         (hand_x, hand_y - 1, 1, 1))

        # LONG SWORD.
        _NS_leoric._draw_long_sword(surface, hand_x, hand_y, sword_angle, facing,
                                      phase, action, attack_progress)

    def _draw_long_sword(surface, hand_x, hand_y, angle, facing, phase, action, attack_progress):
        """Long steel sword with gold crossguard."""
        # Handle.
        handle_len = 5
        blade_len = 26

        guard_x = hand_x + int(math.cos(angle) * handle_len) * facing
        guard_y = hand_y + int(math.sin(angle) * handle_len)

        blade_tip_x = guard_x + int(math.cos(angle) * blade_len) * facing
        blade_tip_y = guard_y + int(math.sin(angle) * blade_len)

        pommel_x = hand_x - int(math.cos(angle) * 3) * facing
        pommel_y = hand_y - int(math.sin(angle) * 3)

        # HANDLE (dark wrapped).
        pygame.draw.line(surface, _NS_leoric.PALETTE["shadow_deep"],
                         (pommel_x + 1, pommel_y + 1), (guard_x + 1, guard_y + 1), 4)
        pygame.draw.line(surface, _NS_leoric.PALETTE["cape_dark"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 3)
        pygame.draw.line(surface, _NS_leoric.PALETTE["cape_mid"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 2)

        # Wrap lines on handle.
        for i in range(1, 4):
            t = i / 4
            wrap_x = int(pommel_x + (guard_x - pommel_x) * t)
            wrap_y = int(pommel_y + (guard_y - pommel_y) * t)
            perp = angle + math.pi / 2
            wx1 = wrap_x + int(math.cos(perp) * 1) * facing
            wy1 = wrap_y + int(math.sin(perp) * 1)
            wx2 = wrap_x - int(math.cos(perp) * 1) * facing
            wy2 = wrap_y - int(math.sin(perp) * 1)
            pygame.draw.line(surface, _NS_leoric.PALETTE["gold_dark"], (wx1, wy1), (wx2, wy2), 1)

        # CROSSGUARD (gold horizontal bar).
        perp = angle + math.pi / 2
        guard_a_x = guard_x + int(math.cos(perp) * 4) * facing
        guard_a_y = guard_y + int(math.sin(perp) * 4)
        guard_b_x = guard_x - int(math.cos(perp) * 4) * facing
        guard_b_y = guard_y - int(math.sin(perp) * 4)

        pygame.draw.line(surface, _NS_leoric.PALETTE["shadow_deep"],
                         (guard_a_x + 1, guard_a_y + 1),
                         (guard_b_x + 1, guard_b_y + 1), 4)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_darkest"],
                         (guard_a_x, guard_a_y), (guard_b_x, guard_b_y), 3)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_dark"],
                         (guard_a_x, guard_a_y), (guard_b_x, guard_b_y), 2)
        pygame.draw.line(surface, _NS_leoric.PALETTE["gold_mid"],
                         (guard_a_x, guard_a_y - 1), (guard_b_x, guard_b_y - 1), 1)

        # Central gold ball on crossguard.
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_darkest"],
                              (guard_x, guard_y), 2)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_mid"], (guard_x, guard_y), 1)
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_shine"], (guard_x, guard_y, 1, 1))

        # POMMEL (gold ball).
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["shadow_deep"],
                              (pommel_x + 1, pommel_y + 1), 3)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_darkest"],
                              (pommel_x, pommel_y), 3)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_dark"],
                              (pommel_x, pommel_y), 2)
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["gold_mid"],
                              (pommel_x, pommel_y), 1)
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gold_shine"], (pommel_x, pommel_y, 1, 1))

        # BLADE (steel).
        # Blade width.
        edge_offset = 2
        blade_ba_x = guard_x + int(math.cos(perp) * edge_offset) * facing
        blade_ba_y = guard_y + int(math.sin(perp) * edge_offset)
        blade_bb_x = guard_x - int(math.cos(perp) * edge_offset) * facing
        blade_bb_y = guard_y - int(math.sin(perp) * edge_offset)
        blade_ta_x = blade_tip_x + int(math.cos(perp) * 1) * facing
        blade_ta_y = blade_tip_y + int(math.sin(perp) * 1)
        blade_tb_x = blade_tip_x - int(math.cos(perp) * 1) * facing
        blade_tb_y = blade_tip_y - int(math.sin(perp) * 1)

        # Shadow.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"], [
            (blade_ba_x + 1, blade_ba_y + 1),
            (blade_bb_x + 1, blade_bb_y + 1),
            (blade_tb_x + 1, blade_tb_y + 1),
            (blade_ta_x + 1, blade_ta_y + 1),
        ])
        # Dark base.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["steel_dark"], [
            (blade_ba_x, blade_ba_y),
            (blade_bb_x, blade_bb_y),
            (blade_tb_x, blade_tb_y),
            (blade_ta_x, blade_ta_y),
        ])
        # Mid steel.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["steel_mid"], [
            (int((blade_ba_x + guard_x) / 2), int((blade_ba_y + guard_y) / 2)),
            (blade_tip_x, blade_tip_y),
            (int((blade_bb_x + guard_x) / 2), int((blade_bb_y + guard_y) / 2)),
        ])

        # Bright center groove line.
        for i in range(1, 8):
            t = i / 8
            line_x = int(guard_x + (blade_tip_x - guard_x) * t)
            line_y = int(guard_y + (blade_tip_y - guard_y) * t)
            pygame.draw.rect(surface, _NS_leoric.PALETTE["steel_light"], (line_x, line_y, 1, 1))

        # Sharp bright edge.
        pygame.draw.line(surface, _NS_leoric.PALETTE["steel_light"],
                         (blade_ba_x, blade_ba_y), (blade_ta_x, blade_ta_y), 1)

        # Bright tip.
        _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["steel_shine"],
                              (blade_tip_x, blade_tip_y), 1)
        pygame.draw.rect(surface, _NS_leoric.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))

        # Blue gem embedded near base of blade.
        gem_pos_x = int(guard_x + (blade_tip_x - guard_x) * 0.2)
        gem_pos_y = int(guard_y + (blade_tip_y - guard_y) * 0.2)
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gem_dark"],
                         (gem_pos_x - 1, gem_pos_y, 2, 1))
        pygame.draw.rect(surface, _NS_leoric.PALETTE["gem_light"], (gem_pos_x, gem_pos_y, 1, 1))

        # Store sword tip for slash arc.
        _NS_leoric._sword_tip = (blade_tip_x, blade_tip_y)

    def _draw_knight_head(surface, cx, cy, facing, phase):
        """Handsome warrior head with brown hair."""
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
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["shadow_deep"],
                         [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["skin_dark"], head_pts)
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 4),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_leoric.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # BROWN HAIR (short, spiky on top).
        _NS_leoric._draw_short_hair(surface, cx, cy, facing, phase)

        # BROWN EYES (warm, determined).
        _NS_leoric._draw_warrior_eyes(surface, cx, cy - 2, facing, phase)

        # Nose.
        pygame.draw.rect(surface, _NS_leoric.PALETTE["skin_dark"], (cx, cy, 1, 1))

        # Mouth (stern line).
        pygame.draw.line(surface, _NS_leoric.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

        # Small beard/goatee.
        pygame.draw.rect(surface, _NS_leoric.PALETTE["hair_dark"], (cx - 1, cy + 4, 3, 1))
        pygame.draw.rect(surface, _NS_leoric.PALETTE["hair_mid"], (cx, cy + 4, 1, 1))

    def _draw_short_hair(surface, cx, cy, facing, phase):
        """Short brown hair (spiky top)."""
        # Base hair mass on top.
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["hair_dark"], [
            (cx - 5, cy - 5),
            (cx - 5, cy - 7),
            (cx - 3, cy - 8),
            (cx, cy - 8),
            (cx + 3, cy - 8),
            (cx + 5, cy - 7),
            (cx + 5, cy - 5),
            (cx + 4, cy - 3),
            (cx - 4, cy - 3),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["hair_mid"], [
            (cx - 4, cy - 5),
            (cx - 3, cy - 7),
            (cx, cy - 7),
            (cx + 3, cy - 7),
            (cx + 4, cy - 5),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_leoric._poly(surface, _NS_leoric.PALETTE["hair_light"], [
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])

        # Spiky tufts on top.
        for i, (spike_x_off, spike_h) in enumerate([
            (-3, 2), (-1, 3), (2, 2), (4, 1),
        ]):
            spike_x = cx + spike_x_off
            spike_y = cy - 8 - spike_h
            pygame.draw.rect(surface, _NS_leoric.PALETTE["hair_dark"],
                             (spike_x, spike_y, 1, spike_h))
            pygame.draw.rect(surface, _NS_leoric.PALETTE["hair_mid"],
                             (spike_x, spike_y + 1, 1, spike_h - 1))

        # Front bang.
        pygame.draw.rect(surface, _NS_leoric.PALETTE["hair_dark"], (cx - 2, cy - 5, 5, 1))
        pygame.draw.rect(surface, _NS_leoric.PALETTE["hair_mid"], (cx - 1, cy - 5, 3, 1))

    def _draw_warrior_eyes(surface, cx, cy, facing, phase):
        """Warm determined brown eyes."""
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_leoric.PALETTE["shadow_deep"],
                             (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_leoric.PALETTE["eye_socket"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_leoric.PALETTE["eye_mid"], (ex, ey, 1, 1))

    # ============================================================
    # SWORD SLASH ARC
    # ============================================================
    def _draw_sword_slash_arc(surface, boss, x, y, progress):
        """Gold energy slash arc."""
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
            seg_alpha = _NS_leoric._alpha(alpha_val * t)
            size = int(2 + t * 4)

            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_darkest"], seg_alpha),
                                   (seg_x, seg_y), size)
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_dark"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 1))
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_mid"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 2))
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_light"], seg_alpha),
                                   (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Bright edge.
        for i in range(6):
            edge_t = 1 - i * 0.1
            edge_angle = start_angle + (current_angle - start_angle) * edge_t
            ex1 = center_x + int(math.cos(edge_angle) * (arc_radius - 2)) * facing
            ey1 = center_y + int(math.sin(edge_angle) * (arc_radius - 2))
            ex2 = center_x + int(math.cos(edge_angle) * (arc_radius + 4)) * facing
            ey2 = center_y + int(math.sin(edge_angle) * (arc_radius + 4))
            e_alpha = _NS_leoric._alpha(alpha_val * (1 - i * 0.13))
            pygame.draw.line(surface, (*_NS_leoric.PALETTE["holy_hot"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 1)
            pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], e_alpha),
                             (ex2, ey2, 1, 1))

        # Sparks flying.
        for i in range(10):
            spark_angle = current_angle + i * 0.1 * facing
            spark_dist = arc_radius + i * 2
            sx = center_x + int(math.cos(spark_angle) * spark_dist) * facing
            sy = center_y + int(math.sin(spark_angle) * spark_dist)
            spark_alpha = _NS_leoric._alpha(220 - i * 20)
            pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], spark_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], spark_alpha),
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
        pygame.draw.ellipse(shadow, (10, 15, 30, 160),
                            (70 - w // 2, 12 - h // 2, w, h))
        surface.blit(shadow, (x - 70, y - 12))

    def _draw_holy_wisps(surface, cx, cy, phase, intense=False):
        """Rising gold holy wisps."""
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 32 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_leoric._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_darkest"], alpha),
                                   (sx, sy), 3)
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_dark"], alpha),
                                   (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(8):
            spark_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 26)
            alpha = _NS_leoric._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_holy_aura(surface, x, y, phase, immortal):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_leoric._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_leoric._aacircle(aura, (*_NS_leoric.PALETTE["holy_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_leoric._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_leoric._aacircle(aura, (*_NS_leoric.PALETTE["holy_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_leoric._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_leoric._aacircle(aura, (*_NS_leoric.PALETTE["holy_mid"], alpha),
                                       (110, 90), radius)

        # Extra brightness for immortality.
        if immortal:
            for radius in range(45, 5, -3):
                alpha = _NS_leoric._alpha((45 - radius) * 1.5 * pulse)
                if alpha > 0:
                    _NS_leoric._aacircle(aura, (*_NS_leoric.PALETTE["holy_light"], alpha),
                                           (110, 90), radius)

        surface.blit(aura, (x - 110, y - 90))

        # Orbiting stars.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_leoric.PALETTE["holy_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_leoric.PALETTE["holy_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_leoric.PALETTE["holy_darkest"], 200),
                            (5, 18, 160, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_leoric.PALETTE["holy_dark"], 220),
                            (14, 20, 142, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_leoric.PALETTE["holy_mid"], 230),
                            (25, 22, 120, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_leoric.PALETTE["holy_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_leoric.PALETTE["holy_hot"],
                                        _NS_leoric._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q: FEARLESS CHARGE (forward dash)
    # ============================================================
    def _draw_fearlesscharge_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_leoric._target_position(boss, x, y)

        # Ground charge trail.
        num_streaks = 10
        for i in range(num_streaks):
            t = i / num_streaks
            trail_visible = progress > t * 0.7
            if not trail_visible:
                continue

            arc_x = int(x + (tx - x) * t)
            arc_y = int(y + (ty - y) * t) + 30

            fade = max(0, 1 - (progress - t * 0.7) * 2)
            alpha = _NS_leoric._alpha(200 * fade)
            if alpha <= 0:
                continue

            # Arrow streak on ground.
            for streak_off in (-3, 0, 3):
                pygame.draw.line(surface, (*_NS_leoric.PALETTE["holy_mid"], alpha),
                                 (arc_x - facing * 8, arc_y + streak_off),
                                 (arc_x + facing * 3, arc_y + streak_off), 1)
                pygame.draw.line(surface, (*_NS_leoric.PALETTE["holy_hot"], alpha),
                                 (arc_x - facing * 4, arc_y + streak_off),
                                 (arc_x + facing * 2, arc_y + streak_off), 1)

    def _draw_fearlesscharge_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_leoric._target_position(boss, x, y)

        if progress < 0.85:
            # Motion trail behind boss (afterimages of shield forward).
            t = progress / 0.85
            dash_x = int(x + (tx - x) * t)

            for i in range(5):
                blur_t = max(0.0, t - i * 0.06)
                bx = int(x + (tx - x) * blur_t)
                alpha = _NS_leoric._alpha(150 - i * 25)

                # Simplified shield silhouette.
                shield_w = 12
                shield_h = 14
                pygame.draw.ellipse(surface,
                                    (*_NS_leoric.PALETTE["gold_dark"], alpha),
                                    (bx + facing * 6 - shield_w // 2,
                                     y - shield_h // 2,
                                     shield_w, shield_h))
                pygame.draw.ellipse(surface,
                                    (*_NS_leoric.PALETTE["gold_mid"], alpha),
                                    (bx + facing * 6 - shield_w // 2 + 2,
                                     y - shield_h // 2 + 2,
                                     shield_w - 4, shield_h - 4))
                pygame.draw.rect(surface,
                                 (*_NS_leoric.PALETTE["gold_shine"], alpha),
                                 (bx + facing * 6, y, 2, 2))

            # Bright leading edge (shield ram effect).
            for r in range(10, 1, -1):
                alpha = _NS_leoric._alpha(200 * (10 - r) / 10)
                _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_light"], alpha),
                                       (dash_x + facing * 15, y), r)
            pygame.draw.rect(surface, _NS_leoric.PALETTE["white"],
                             (dash_x + facing * 15, y, 1, 1))

            # Arrow chevrons pointing forward (charge direction).
            for i in range(4):
                arrow_t = (phase * 3 + i * 0.25) % 1.0
                arrow_x = dash_x + facing * int(arrow_t * 30)
                arrow_y = y
                a_alpha = _NS_leoric._alpha(220 * (1 - arrow_t))
                # Chevron arrow >.
                pygame.draw.line(surface, (*_NS_leoric.PALETTE["holy_hot"], a_alpha),
                                 (arrow_x, arrow_y - 3),
                                 (arrow_x + facing * 3, arrow_y), 2)
                pygame.draw.line(surface, (*_NS_leoric.PALETTE["holy_hot"], a_alpha),
                                 (arrow_x + facing * 3, arrow_y),
                                 (arrow_x, arrow_y + 3), 2)
        else:
            # Impact at end.
            t = (progress - 0.85) / 0.15
            radius = int(15 + t * 25)
            alpha = _NS_leoric._alpha(240 * (1 - t))
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_mid"], alpha),
                                   (tx, ty), radius, 2)
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_hot"], alpha),
                                   (tx, ty), max(1, radius - 8), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: SACRED HAMMER (big overhead slam)
    # ============================================================
    def _draw_sacredhammer_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground impact circle in front.
        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            r = int(20 + t * 35)
            alpha = _NS_leoric._alpha(220 * (1 - t * 0.4))
            center_x = x + facing * 25
            center_y = y + 30

            pygame.draw.ellipse(surface, (*_NS_leoric.PALETTE["holy_darkest"], alpha),
                                (center_x - r, center_y - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_leoric.PALETTE["holy_dark"], alpha),
                                (center_x - r + 3, center_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_leoric.PALETTE["holy_mid"], alpha),
                                (center_x - r + 8, center_y - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_sacredhammer_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        center_x = x + facing * 25
        center_y = y + 15

        if progress < 0.3:
            # Wind-up: sword raised high with charging light.
            t = progress / 0.3
            # Bright sword above.
            sword_y = y - 30 - int(t * 20)
            for w, alpha_v in [(6, 100), (4, 160), (2, 220)]:
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_light"],
                                            _NS_leoric._alpha(alpha_v * t)),
                                 (x + facing * 5 - w // 2, sword_y, w, 20))

            # Bright orb charging above sword.
            gather_r = int(4 + t * 8)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_leoric._alpha(200 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_light"], alpha),
                                       (x + facing * 5, sword_y), r)
            _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["holy_shine"],
                                   (x + facing * 5, sword_y), max(1, gather_r - 2))
        else:
            # SLAM: MASSIVE explosion at ground.
            t = (progress - 0.3) / 0.7
            intensity = math.sin(t * math.pi) * 0.5 + 0.5

            radius = int(30 + t * 30)
            alpha = _NS_leoric._alpha(240 * intensity)

            # Multi-layer explosion.
            for r in range(radius, 2, -3):
                a = _NS_leoric._alpha(alpha * (radius - r) / radius)
                _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_darkest"], a),
                                       (center_x, center_y), r)
            for r in range(int(radius * 0.8), 2, -2):
                a = _NS_leoric._alpha(alpha * (radius * 0.8 - r) / (radius * 0.8))
                _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_dark"], a),
                                       (center_x, center_y), r)
            for r in range(int(radius * 0.6), 2, -2):
                a = _NS_leoric._alpha(alpha * (radius * 0.6 - r) / (radius * 0.6))
                _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_mid"], a),
                                       (center_x, center_y), r)
            _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["holy_hot"],
                                   (center_x, center_y), max(1, radius // 4))
            _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["holy_shine"],
                                   (center_x, center_y), max(1, radius // 6))
            pygame.draw.rect(surface, _NS_leoric.PALETTE["white"],
                             (center_x, center_y, 1, 1))

            # Radial burst LINES.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = center_x + int(math.cos(angle_s) * radius)
                ey = center_y + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.line(surface, (*_NS_leoric.PALETTE["holy_hot"], alpha),
                                 (center_x, center_y), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], alpha),
                                 (ex, ey, 2, 2))

            # Rising pillar sparkles.
            for i in range(15):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                sx = center_x - 20 + i * 3 + int(math.sin(phase + i) * 4)
                sy = center_y - int(spark_t * 40)
                s_alpha = _NS_leoric._alpha(220 * intensity * (1 - spark_t))
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], s_alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], s_alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: CONCEAL BLAST (shield energy blast)
    # ============================================================
    def _draw_concealblast_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_leoric._target_position(boss, x, y)

        # Shield origin (on back side).
        shield_x = x - facing * 6
        shield_y = y - 5

        if progress < 0.2:
            # Charge on shield.
            t = progress / 0.2
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_leoric._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_light"], alpha),
                                       (shield_x, shield_y), r)
            _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["holy_hot"],
                                   (shield_x, shield_y), max(1, cr - 4))
            _NS_leoric._aacircle(surface, _NS_leoric.PALETTE["white"],
                                   (shield_x, shield_y), max(1, cr - 6))
        else:
            # BLAST forward as arc wave.
            t = (progress - 0.2) / 0.8

            # Wave expands forward.
            wave_dist = int(t * 100)

            # Arc wave (concentric arcs).
            for wave_i in range(3):
                wave_off = wave_i * 8
                actual_dist = wave_dist - wave_off
                if actual_dist < 5:
                    continue
                wave_alpha = _NS_leoric._alpha(220 * (1 - t) * (1 - wave_i * 0.2))

                # Draw arc as multiple points.
                for a_off in range(-4, 5):
                    arc_angle = a_off * 0.15
                    ax = shield_x + facing * int(math.cos(arc_angle) * actual_dist)
                    ay = shield_y + int(math.sin(arc_angle) * actual_dist * 0.5)

                    _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_dark"], wave_alpha),
                                           (ax, ay), 3)
                    _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_mid"], wave_alpha),
                                           (ax, ay), 2)
                    pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], wave_alpha),
                                     (ax, ay, 1, 1))
                    pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_shine"], wave_alpha),
                                     (ax, ay, 1, 1))

            # Sparkles trailing wave.
            for i in range(8):
                sp_angle = (i - 4) * 0.12
                sp_dist = wave_dist + i * 3 - 10
                if sp_dist < 5:
                    continue
                sx = shield_x + facing * int(math.cos(sp_angle) * sp_dist)
                sy = shield_y + int(math.sin(sp_angle) * sp_dist * 0.5)
                alpha = _NS_leoric._alpha(200 * (1 - t))
                pygame.draw.rect(surface, (*_NS_leoric.PALETTE["holy_hot"], alpha),
                                 (sx, sy, 2, 2))

    # ============================================================
    # SKILL R: IMMORTALITY (protective shield bubble)
    # ============================================================
    def _draw_immortality_shield(surface, boss, x, y, timer, phase):
        """Protective gold bubble around boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        pulse = math.sin(phase * 2) * 0.3 + 0.7
        breath = math.sin(phase * 2) * 2
        r = 45 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multiple bubble rings.
        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_leoric._aacircle(bubble, (*_NS_leoric.PALETTE["holy_hot"], alpha_val),
                                   center, r - i, thickness)
            _NS_leoric._aacircle(bubble, (*_NS_leoric.PALETTE["holy_shine"], alpha_val),
                                   center, r - i - 1, 1)

        # Sparkles around bubble.
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_leoric.PALETTE["holy_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_leoric.PALETTE["holy_shine"], (sx, sy, 1, 1))

        # Cross/plus shapes inside bubble (protection symbols).
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            inner_r = r - 15
            px = center[0] + int(math.cos(angle) * inner_r)
            py = center[1] + int(math.sin(angle) * inner_r)
            pygame.draw.line(bubble, _NS_leoric.PALETTE["holy_shine"],
                             (px - 2, py), (px + 2, py), 1)
            pygame.draw.line(bubble, _NS_leoric.PALETTE["holy_shine"],
                             (px, py - 2), (px, py + 2), 1)
            pygame.draw.rect(bubble, _NS_leoric.PALETTE["white"], (px, py, 1, 1))

        surface.blit(bubble, (x - r - 10, y - r - 10))

        # Reflect pulse waves periodically.
        pulse_t = (phase * 0.6) % 1.0
        pulse_r = int(r + pulse_t * 15)
        pulse_alpha = _NS_leoric._alpha(180 * (1 - pulse_t))
        if pulse_alpha > 0:
            _NS_leoric._aacircle(surface, (*_NS_leoric.PALETTE["holy_hot"], pulse_alpha),
                                   (x, y), pulse_r, 2)


# ====================================================================
# shirotaka.py
# ====================================================================



class _NS_shirotaka:
    """Namespace shirotaka - Tideborn Tactician shinobi (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe/gi (dark navy blue)
        "robe_darkest": (5, 10, 25),
        "robe_dark": (15, 25, 60),
        "robe_mid": (35, 55, 110),
        "robe_light": (75, 100, 165),
        "robe_edge": (135, 165, 220),

        # Armor plates (dark blue-black metal)
        "armor_darkest": (8, 10, 20),
        "armor_dark": (25, 32, 55),
        "armor_mid": (55, 65, 95),
        "armor_light": (110, 125, 165),
        "armor_edge": (180, 195, 230),
        "armor_shine": (230, 240, 255),

        # Skin (pale warrior)
        "skin_dark": (120, 95, 85),
        "skin_mid": (185, 155, 140),
        "skin_light": (225, 200, 185),
        "skin_shine": (245, 225, 210),

        # Hair (silver-white)
        "hair_darkest": (100, 105, 120),
        "hair_dark": (160, 170, 185),
        "hair_mid": (215, 220, 230),
        "hair_light": (245, 248, 255),
        "hair_shine": (255, 255, 255),

        # Water (cyan-blue)
        "water_darkest": (5, 30, 60),
        "water_dark": (20, 80, 150),
        "water_mid": (60, 160, 230),
        "water_light": (140, 220, 255),
        "water_hot": (200, 245, 255),
        "water_shine": (240, 253, 255),

        # Steel blade
        "blade_dark": (30, 35, 50),
        "blade_mid": (95, 110, 135),
        "blade_light": (180, 195, 220),
        "blade_shine": (240, 248, 255),

        # Eye (fierce red)
        "eye_socket": (10, 5, 5),
        "eye_dark": (80, 15, 20),
        "eye_mid": (200, 40, 45),
        "eye_light": (255, 130, 120),
        "eye_glow": (255, 220, 200),

        # Explosion/fire (for paper bomb)
        "expl_dark": (100, 40, 5),
        "expl_mid": (240, 130, 20),
        "expl_light": (255, 220, 100),
        "expl_hot": (255, 245, 180),

        # Paper (tag/bomb)
        "paper_dark": (120, 90, 60),
        "paper_mid": (200, 170, 130),
        "paper_light": (240, 220, 180),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_shirotaka._clamp(color)
        if _NS_shirotaka.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_shirotaka._clamp(color)
        if _NS_shirotaka.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_shirotaka._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_shirotaka._clamp(color), points)

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
    def draw_shirotaka(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_shirotaka._update_st_attack_anim(boss)
        attacking = (
            getattr(boss, "_st_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_shirotaka._draw_water_aura(surface, x, y, pulse)
        _NS_shirotaka._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_shirotaka._draw_waterboundary_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_shirotaka._draw_paperbomb_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_shirotaka._draw_st_attack(surface, boss, x, y)
        else:
            _NS_shirotaka._draw_st_idle(surface, boss, x, y)

        # Shadow clones (Skill E).
        if active_skill == "e":
            _NS_shirotaka._draw_shadow_clones(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_shirotaka._draw_hiraishin_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_shirotaka._draw_waterboundary_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_shirotaka._draw_paperbomb_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_st_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_st_previous_timer", 0))
        active = bool(getattr(boss, "_st_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._st_attack_active = True
            boss._st_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._st_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._st_attack_frame = int(
                getattr(boss, "_st_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._st_attack_active = False
            boss._st_attack_frame = 0
            active = False

        boss._st_previous_timer = timer
        boss._st_attack_progress = (
            min(1.0, getattr(boss, "_st_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_st_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        _NS_shirotaka._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_shirotaka._draw_water_wisps(surface, x, y + 42, boss.pulse)
        _NS_shirotaka._draw_st_body(surface, x, y + bob, boss.direction,
                                     boss.pulse, "idle")

    def _draw_st_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_st_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_st_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.6) * 4)
        # Fast sword slash: quick wind up → fast slash → recover
        if progress < 0.3:
            t = progress / 0.3
            lean = int(t * -3) * facing
            lift = int(t * 2)
        elif progress < 0.5:
            t = (progress - 0.3) / 0.20
            lean = int((-3 + t * 9)) * facing
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.5) / 0.5
            lean = int(6 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        _NS_shirotaka._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_shirotaka._draw_water_wisps(surface, x + lean, y + 42, boss.pulse, intense=True)
        _NS_shirotaka._draw_st_body(surface, x + lean, y + bob - lift,
                                     facing, boss.pulse, "attack",
                                     progress)
        _NS_shirotaka._draw_dual_slash_arc(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (shinobi humanoid)
    # ============================================================
    def _draw_st_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Legs/hakama.
        _NS_shirotaka._draw_shinobi_legs(surface, cx, cy + 10, facing, phase)

        # Torso base.
        _NS_shirotaka._draw_shinobi_torso(surface, cx, cy - 2, facing, phase)

        # STIFF SHOULDER ARMOR PLATES (large flat plates - signature).
        _NS_shirotaka._draw_shoulder_plates(surface, cx, cy - 3, facing, phase)

        # Back arm (holding blade).
        _NS_shirotaka._draw_back_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

        # Head with silver hair.
        _NS_shirotaka._draw_shinobi_head(surface, cx, cy - 18, facing, phase)

        # Front arm (main sword) - last.
        _NS_shirotaka._draw_front_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

    def _draw_shinobi_legs(surface, cx, cy, facing, phase):
        """Dark hakama with wraps."""
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
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in legs_pts])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["robe_darkest"], legs_pts)

        # Main color.
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["robe_dark"], [
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 11, cy + 4),
            (cx + 9 + int(sway), cy + 13),
            (cx + 5, cy + 19),
            (cx - 5, cy + 19),
            (cx - 9 - int(sway), cy + 13),
            (cx - 11, cy + 4),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["robe_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 9, cy + 3),
            (cx + 7, cy + 12),
            (cx + 4, cy + 17),
            (cx - 4, cy + 17),
            (cx - 7, cy + 12),
            (cx - 9, cy + 3),
        ])

        # Fold lines.
        for x_off in (-5, 0, 5):
            pygame.draw.line(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                             (cx + x_off, cy - 4),
                             (cx + int(x_off * 1.4), cy + 17), 1)

        # Leg separation.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                         (cx, cy + 3), (cx, cy + 18), 1)

        # Belt / obi.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_darkest"],
                         (cx - 10, cy - 6, 20, 3))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_dark"],
                         (cx - 10, cy - 6, 20, 2))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_mid"],
                         (cx - 9, cy - 6, 18, 1))
        # Belt buckle.
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["armor_darkest"],
                                 (cx, cy - 5), 3)
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["armor_mid"], (cx, cy - 5), 2)
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["water_dark"], (cx, cy - 5), 1)
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_hot"], (cx, cy - 5, 1, 1))

        # Sandals + leg wraps.
        for side in (-1, 1):
            wrap_x = cx + side * 4
            # Wraps.
            for wrap_y_off in (16, 18):
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["robe_edge"],
                                 (wrap_x - 3, cy + wrap_y_off, 6, 1))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                                 (wrap_x - 3, cy + wrap_y_off + 1, 6, 1))
            # Sandal.
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                             (wrap_x - 4, cy + 20, 8, 3))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_dark"],
                             (wrap_x - 4, cy + 20, 8, 2))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_mid"],
                             (wrap_x - 3, cy + 20, 6, 1))

    def _draw_shinobi_torso(surface, cx, cy, facing, phase):
        """Blue gi torso base."""
        torso_pts = [
            (cx - 10, cy - 4),
            (cx - 9, cy + 5),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 9, cy + 5),
            (cx + 10, cy - 4),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ]
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["robe_darkest"], torso_pts)

        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["robe_dark"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 8, cy + 7),
            (cx - 8, cy + 7),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["robe_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
        ])

        # Fur collar around neck (white/silver).
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_darkest"], [
            (cx - 7, cy - 5),
            (cx + 7, cy - 5),
            (cx + 6, cy - 3),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
            (cx - 6, cy - 3),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_dark"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 5, cy - 3),
            (cx - 5, cy - 3),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_mid"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_light"], (cx - 1, cy - 4, 2, 1))

        # Cross-fold of gi.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                         (cx - 5, cy - 2), (cx, cy + 2), 1)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                         (cx + 5, cy - 2), (cx, cy + 2), 1)

    def _draw_shoulder_plates(surface, cx, cy, facing, phase):
        """Stiff shoulder armor plates (large flat plates - signature Tobirama)."""
        for side in (-1, 1):
            plate_x = cx + side * 10
            plate_y = cy

            # Large plate extending outward and slightly up.
            # Wide flat top edge.
            plate_pts = [
                (plate_x - 5, plate_y - 4),
                (plate_x + 6 * side, plate_y - 5),
                (plate_x + 8 * side, plate_y - 3),
                (plate_x + 7 * side, plate_y + 1),
                (plate_x + 3 * side, plate_y + 3),
                (plate_x - 4, plate_y + 3),
                (plate_x - 5, plate_y),
            ]
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in plate_pts])
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["armor_darkest"], plate_pts)

            # Main plate color.
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["armor_dark"], [
                (plate_x - 4, plate_y - 3),
                (plate_x + 5 * side, plate_y - 4),
                (plate_x + 7 * side, plate_y - 2),
                (plate_x + 6 * side, plate_y),
                (plate_x + 2 * side, plate_y + 2),
                (plate_x - 3, plate_y + 2),
                (plate_x - 4, plate_y),
            ])
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["armor_mid"], [
                (plate_x - 3, plate_y - 2),
                (plate_x + 4 * side, plate_y - 3),
                (plate_x + 6 * side, plate_y - 1),
                (plate_x + 4 * side, plate_y + 1),
                (plate_x - 2, plate_y + 1),
                (plate_x - 3, plate_y - 1),
            ])

            # Top edge highlight.
            pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_edge"],
                             (plate_x - 3, plate_y - 3),
                             (plate_x + 5 * side, plate_y - 4), 1)
            pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_shine"],
                             (plate_x - 1, plate_y - 3),
                             (plate_x + 3 * side, plate_y - 4), 1)

            # Rivets/bolts on plate.
            for rivet_off in (-2, 3):
                rx = plate_x + rivet_off * side
                ry = plate_y - 1
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_darkest"], (rx, ry, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm holding second blade."""
        sway = math.sin(phase * 0.5) * 1

        # Position back arm angled forward/down.
        if action == "attack":
            # Back blade also strikes.
            if attack_progress < 0.3:
                arm_angle = -0.1 - (attack_progress / 0.3) * 0.3
            elif attack_progress < 0.5:
                t = (attack_progress - 0.3) / 0.20
                arm_angle = -0.4 + t * 0.6
            else:
                t = (attack_progress - 0.5) / 0.5
                arm_angle = 0.2 - t * 0.4
        else:
            arm_angle = -0.1 + math.sin(phase * 0.5) * 0.05

        shoulder_x = cx - facing * 8
        shoulder_y = cy + 1

        elbow_x = shoulder_x - facing * int(math.cos(arm_angle) * 5)
        elbow_y = shoulder_y + int(math.sin(arm_angle) * 5) + 3
        hand_x = elbow_x - facing * int(math.cos(arm_angle * 0.5) * 5)
        hand_y = elbow_y + int(math.sin(arm_angle * 0.5) * 2) + 2

        # Upper arm.
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["robe_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["robe_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 1)

        # Forearm (skin bare + bandage).
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["skin_mid"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Bandage wraps.
        for wy in (elbow_y + 2, elbow_y + 4):
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_mid"],
                             (elbow_x - 2, wy, 4, 1))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_darkest"],
                             (elbow_x - 2, wy + 1, 4, 1))

        # Hand.
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 2)
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["skin_mid"],
                                 (hand_x, hand_y), 1)

        # BACK BLADE (short katana).
        _NS_shirotaka._draw_back_blade(surface, hand_x, hand_y, facing, phase, action,
                                        attack_progress)

    def _draw_back_blade(surface, hand_x, hand_y, facing, phase, action, attack_progress):
        """Back-hand short katana."""
        # Blade angle (opposite of front, points slightly back-down).
        if action == "attack":
            if attack_progress < 0.3:
                angle = math.pi * 0.15
            elif attack_progress < 0.5:
                t = (attack_progress - 0.3) / 0.20
                angle = math.pi * 0.15 - t * 0.4
            else:
                angle = math.pi * -0.1
        else:
            angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.05

        blade_len = 18
        tip_x = hand_x - int(math.cos(angle) * blade_len) * facing
        tip_y = hand_y - int(math.sin(angle) * blade_len)

        # Blade shaft.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1), (tip_x + 1, tip_y + 1), 3)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["blade_dark"],
                         (hand_x, hand_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["blade_mid"],
                         (hand_x, hand_y), (tip_x, tip_y), 1)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["blade_light"],
                         (hand_x, hand_y - 1), (tip_x, tip_y - 1), 1)

        # Tip.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["blade_shine"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["white"], (tip_x, tip_y, 1, 1))

        # Store back blade tip for slash.
        _NS_shirotaka._back_blade_tip = (tip_x, tip_y)

    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding main katana."""
        # Sword swing animation.
        if action == "attack":
            if attack_progress < 0.3:
                t = attack_progress / 0.3
                arm_angle = -math.pi * 0.15 + t * -math.pi * 0.4
            elif attack_progress < 0.5:
                t = (attack_progress - 0.3) / 0.20
                arm_angle = -math.pi * 0.55 + t * math.pi * 0.9
            else:
                t = (attack_progress - 0.5) / 0.5
                arm_angle = math.pi * 0.35 - t * math.pi * 0.5
        else:
            arm_angle = -math.pi * 0.1 + math.sin(phase * 0.5) * 0.05

        shoulder_x = cx + facing * 8
        shoulder_y = cy + 1

        arm_len = 6
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len) + 2

        forearm_len = 6
        forearm_angle = arm_angle + 0.3
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm.
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["robe_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["robe_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 1)

        # Forearm (skin bare).
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["skin_mid"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_shirotaka._aaline(surface, _NS_shirotaka.PALETTE["skin_light"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Bandage wraps.
        for wy in (elbow_y + 2, elbow_y + 4):
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_mid"],
                             (elbow_x - 2, wy, 4, 1))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_darkest"],
                             (elbow_x - 2, wy + 1, 4, 1))

        # Hand.
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 2)
        _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["skin_mid"],
                                 (hand_x, hand_y), 1)

        # FRONT KATANA.
        _NS_shirotaka._draw_front_katana(surface, hand_x, hand_y, arm_angle - math.pi * 0.1,
                                          facing, phase, action, attack_progress)

    def _draw_front_katana(surface, hand_x, hand_y, angle, facing, phase, action, attack_progress):
        """Long straight katana."""
        # Handle.
        handle_len = 4
        blade_len = 24

        guard_x = hand_x + int(math.cos(angle) * handle_len) * facing
        guard_y = hand_y + int(math.sin(angle) * handle_len)

        blade_tip_x = guard_x + int(math.cos(angle) * blade_len) * facing
        blade_tip_y = guard_y + int(math.sin(angle) * blade_len)

        pommel_x = hand_x - int(math.cos(angle) * 3) * facing
        pommel_y = hand_y - int(math.sin(angle) * 3)

        # Handle wrapped.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                         (pommel_x + 1, pommel_y + 1), (guard_x + 1, guard_y + 1), 3)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_darkest"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 2)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_mid"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 1)

        # Guard (small tsuba).
        perp = angle + math.pi / 2
        gd_a_x = guard_x + int(math.cos(perp) * 2) * facing
        gd_a_y = guard_y + int(math.sin(perp) * 2)
        gd_b_x = guard_x - int(math.cos(perp) * 2) * facing
        gd_b_y = guard_y - int(math.sin(perp) * 2)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_darkest"],
                         (gd_a_x, gd_a_y), (gd_b_x, gd_b_y), 2)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_mid"],
                         (gd_a_x, gd_a_y - 1), (gd_b_x, gd_b_y - 1), 1)

        # BLADE (thin katana blade).
        perp = angle + math.pi / 2
        blade_ba_x = guard_x + int(math.cos(perp) * 1) * facing
        blade_ba_y = guard_y + int(math.sin(perp) * 1)
        blade_bb_x = guard_x - int(math.cos(perp) * 1) * facing
        blade_bb_y = guard_y - int(math.sin(perp) * 1)
        blade_ta_x = blade_tip_x
        blade_ta_y = blade_tip_y

        # Shadow.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                         (guard_x + 1, guard_y + 1),
                         (blade_tip_x + 1, blade_tip_y + 1), 3)

        # Blade main body.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["blade_dark"],
                         (guard_x, guard_y), (blade_tip_x, blade_tip_y), 2)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["blade_mid"],
                         (guard_x, guard_y), (blade_tip_x, blade_tip_y), 1)

        # Bright edge line.
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["blade_light"],
                         (guard_x, guard_y - 1), (blade_tip_x, blade_tip_y - 1), 1)

        # Sharp tip.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["blade_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))

        # Water chakra glow along blade during attack.
        if action == "attack":
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            for r in range(4, 0, -1):
                alpha = _NS_shirotaka._alpha(80 * pulse * (4 - r) / 4)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_light"], alpha),
                                          (blade_tip_x, blade_tip_y), r)

        # Store sword tip for slash arc.
        _NS_shirotaka._sword_tip = (blade_tip_x, blade_tip_y)

    def _draw_shinobi_head(surface, cx, cy, facing, phase):
        """Head with silver spiky hair."""
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
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["skin_dark"], head_pts)
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 4),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # SILVER SPIKY HAIR.
        _NS_shirotaka._draw_silver_hair(surface, cx, cy, facing, phase)

        # HEADBAND (dark blue with metal plate).
        _NS_shirotaka._draw_headband(surface, cx, cy - 4, facing, phase)

        # RED FIERCE EYES.
        _NS_shirotaka._draw_fierce_eyes(surface, cx, cy - 1, facing, phase)

        # Small nose.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["skin_dark"], (cx, cy + 1, 1, 1))

        # Facial marking (red line under each eye, like Tobirama).
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["eye_dark"],
                         (cx - 3, cy + 1), (cx - 1, cy + 1), 1)
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["eye_dark"],
                         (cx + 1, cy + 1), (cx + 3, cy + 1), 1)

        # Mouth (stern).
        pygame.draw.line(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                         (cx - 2, cy + 3), (cx + 2, cy + 3), 1)

    def _draw_silver_hair(surface, cx, cy, facing, phase):
        """Silver white spiky hair going back."""
        wave = math.sin(phase * 1.0) * 1

        # Base hair mass.
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_darkest"], [
            (cx - 6, cy - 5),
            (cx - 6, cy - 7),
            (cx - 3, cy - 8),
            (cx, cy - 8),
            (cx + 3, cy - 8),
            (cx + 6, cy - 7),
            (cx + 6, cy - 5),
            (cx + 5, cy - 3),
            (cx - 5, cy - 3),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_dark"], [
            (cx - 5, cy - 5),
            (cx - 4, cy - 7),
            (cx, cy - 7),
            (cx + 4, cy - 7),
            (cx + 5, cy - 5),
            (cx + 4, cy - 3),
            (cx - 4, cy - 3),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_mid"], [
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])
        _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_light"], [
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])

        # SPIKY BACK-POINTING TUFTS (silver spiky hair).
        # Main tufts going up and slightly back.
        for i, (spike_x_off, spike_h) in enumerate([
            (-5, 3), (-3, 4), (-1, 4), (1, 4), (3, 3), (5, 2),
        ]):
            spike_x = cx + spike_x_off
            spike_top_y = cy - 8 - spike_h + int(wave * 0.3)

            # Tapered spike upward.
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_darkest"], [
                (spike_x - 1, cy - 7),
                (spike_x + 1, cy - 7),
                (spike_x, spike_top_y),
            ])
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_dark"], [
                (spike_x - 1, cy - 7),
                (spike_x + 1, cy - 7),
                (spike_x, spike_top_y + 1),
            ])
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_mid"], [
                (spike_x, cy - 7),
                (spike_x, spike_top_y),
            ])
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_light"],
                             (spike_x, spike_top_y, 1, 1))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_shine"],
                             (spike_x, spike_top_y, 1, 1))

        # Back-pointing spikes on sides (bigger, more prominent).
        for side in (-1, 1):
            side_x = cx + side * 5
            # 2 big back spikes per side.
            for i, (back_off, height) in enumerate([(2, 5), (1, 3)]):
                spike_end_x = side_x + side * (2 + back_off)
                spike_end_y = cy - 4 - height + int(wave * 0.5)

                _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_darkest"], [
                    (side_x, cy - 4),
                    (side_x, cy - 2),
                    (spike_end_x, spike_end_y),
                ])
                _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_dark"], [
                    (side_x, cy - 3),
                    (side_x + side * 1, cy - 3),
                    (spike_end_x, spike_end_y + 1),
                ])
                _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["hair_mid"], [
                    (side_x + side * 1, cy - 3),
                    (spike_end_x, spike_end_y + 1),
                ])
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_light"],
                                 (spike_end_x, spike_end_y, 1, 1))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_shine"],
                                 (spike_end_x, spike_end_y, 1, 1))

        # Front bangs.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_dark"], (cx - 2, cy - 5, 5, 1))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_mid"], (cx - 1, cy - 5, 3, 1))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["hair_light"], (cx, cy - 5, 1, 1))

    def _draw_headband(surface, cx, cy, facing, phase):
        """Dark blue headband with metal plate."""
        # Cloth strip.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                         (cx - 6, cy, 12, 3))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["robe_darkest"],
                         (cx - 6, cy, 12, 2))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["robe_dark"],
                         (cx - 6, cy, 12, 1))

        # Metal plate.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                         (cx - 4, cy - 1, 8, 3))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_darkest"],
                         (cx - 4, cy - 1, 8, 3))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_mid"],
                         (cx - 3, cy - 1, 6, 2))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_light"],
                         (cx - 3, cy - 1, 6, 1))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["armor_shine"],
                         (cx - 2, cy - 1, 2, 1))

        # Water symbol on plate.
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_dark"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_hot"], (cx, cy, 1, 1))

    def _draw_fierce_eyes(surface, cx, cy, facing, phase):
        """Fierce red eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["eye_socket"],
                             (ex, ey - 1, 1, 2))

            # Red glow.
            for r in range(2, 0, -1):
                alpha = _NS_shirotaka._alpha(160 * pulse * (2 - r) / 2)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["eye_mid"], alpha),
                                          (ex, ey), r)

            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["eye_light"], (ex, ey, 1, 1))

    # ============================================================
    # DUAL SLASH ARC
    # ============================================================
    def _draw_dual_slash_arc(surface, boss, x, y, progress):
        """Two arc slashes - front and back blade."""
        if progress < 0.3 or progress > 0.65:
            return

        facing = boss.direction
        swing_t = (progress - 0.3) / 0.20
        swing_t = max(0, min(1, swing_t))
        alpha_val = int(255 * (1 - abs(swing_t - 0.5) * 1.5))
        alpha_val = max(0, alpha_val)

        # FRONT SLASH (main).
        center_x = x + facing * 5
        center_y = y + 3
        arc_radius = 28

        start_angle = -math.pi * 0.85 * facing
        end_angle = math.pi * 0.35 * facing
        current_angle = start_angle + (end_angle - start_angle) * swing_t

        # Arc trail (front).
        num_segments = 14
        for i in range(num_segments):
            t = i / num_segments
            seg_angle = start_angle + (current_angle - start_angle) * t
            seg_x = center_x + int(math.cos(seg_angle) * arc_radius) * facing
            seg_y = center_y + int(math.sin(seg_angle) * arc_radius)
            seg_alpha = _NS_shirotaka._alpha(alpha_val * t)
            size = int(2 + t * 4)

            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_darkest"], seg_alpha),
                                      (seg_x, seg_y), size)
            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_dark"], seg_alpha),
                                      (seg_x, seg_y), max(1, size - 1))
            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_mid"], seg_alpha),
                                      (seg_x, seg_y), max(1, size - 2))
            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_light"], seg_alpha),
                                      (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # BACK SLASH (secondary, smaller opposite direction).
        back_center_x = x - facing * 5
        back_center_y = y + 4
        back_radius = 20
        back_start = math.pi * 0.85 * facing
        back_end = -math.pi * 0.35 * facing
        back_current = back_start + (back_end - back_start) * swing_t

        num_back = 10
        for i in range(num_back):
            t = i / num_back
            seg_angle = back_start + (back_current - back_start) * t
            seg_x = back_center_x + int(math.cos(seg_angle) * back_radius) * facing
            seg_y = back_center_y + int(math.sin(seg_angle) * back_radius)
            seg_alpha = _NS_shirotaka._alpha(alpha_val * t * 0.7)  # weaker
            size = int(1 + t * 3)

            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_dark"], seg_alpha),
                                      (seg_x, seg_y), size)
            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_mid"], seg_alpha),
                                      (seg_x, seg_y), max(1, size - 1))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Bright edge lines on both arcs.
        for i in range(5):
            edge_t = 1 - i * 0.15
            # Front edge.
            edge_angle = start_angle + (current_angle - start_angle) * edge_t
            ex1 = center_x + int(math.cos(edge_angle) * (arc_radius - 2)) * facing
            ey1 = center_y + int(math.sin(edge_angle) * (arc_radius - 2))
            ex2 = center_x + int(math.cos(edge_angle) * (arc_radius + 3)) * facing
            ey2 = center_y + int(math.sin(edge_angle) * (arc_radius + 3))
            e_alpha = _NS_shirotaka._alpha(alpha_val * (1 - i * 0.15))
            pygame.draw.line(surface, (*_NS_shirotaka.PALETTE["water_hot"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 1)
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_shine"], e_alpha),
                             (ex2, ey2, 1, 1))

        # Water sparkles.
        for i in range(8):
            spark_angle = current_angle + i * 0.12 * facing
            spark_dist = arc_radius + i * 2
            sx = center_x + int(math.cos(spark_angle) * spark_dist) * facing
            sy = center_y + int(math.sin(spark_angle) * spark_dist)
            spark_alpha = _NS_shirotaka._alpha(220 - i * 20)
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], spark_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_shine"], spark_alpha),
                             (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_floating_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
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
        pygame.draw.ellipse(shadow, (5, 10, 25, 160),
                            (70 - w // 2, 12 - h // 2, w, h))
        surface.blit(shadow, (x - 70, y - 12))

    def _draw_water_wisps(surface, cx, cy, phase, intense=False):
        """Blue water wisps."""
        strength = 1.5 if intense else 1.0

        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 32 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 30)
            alpha = _NS_shirotaka._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_darkest"], alpha),
                                      (sx, sy), 3)
            _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_dark"], alpha),
                                      (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(8):
            spark_t = (phase * 0.4 + i * 0.15) % 1.0
            ex = cx - 28 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 26)
            alpha = _NS_shirotaka._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_water_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_shirotaka._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_shirotaka._aacircle(aura, (*_NS_shirotaka.PALETTE["water_darkest"], alpha),
                                          (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_shirotaka._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_shirotaka._aacircle(aura, (*_NS_shirotaka.PALETTE["water_dark"], alpha),
                                          (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_shirotaka._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_shirotaka._aacircle(aura, (*_NS_shirotaka.PALETTE["water_mid"], alpha),
                                          (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Water droplets orbiting.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 55), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_shirotaka.PALETTE["water_darkest"], 200),
                            (5, 18, 160, 27), 3)
        pygame.draw.ellipse(ring, (*_NS_shirotaka.PALETTE["water_dark"], 220),
                            (14, 20, 142, 23), 2)
        pygame.draw.ellipse(ring, (*_NS_shirotaka.PALETTE["water_mid"], 230),
                            (25, 22, 120, 19), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_shirotaka.PALETTE["water_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_shirotaka.PALETTE["water_hot"],
                                        _NS_shirotaka._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q: HIRAISHIN MARKED SLICE (kunai teleport)
    # ============================================================
    def _draw_hiraishin_foreground(surface, boss, x, y, timer, phase):
        """Marked kunai flying to target + teleport flash."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_shirotaka._target_position(boss, x, y)

        start_x = x + facing * 10
        start_y = y - 5

        if progress < 0.15:
            # Charge/prep.
            t = progress / 0.15
            cr = int(3 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_shirotaka._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_mid"], alpha),
                                          (start_x, start_y), r)
            _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["water_hot"],
                                     (start_x, start_y), max(1, cr - 2))
        elif progress < 0.6:
            # Kunai flying.
            t = (progress - 0.15) / 0.45
            kx = int(start_x + (tx - start_x) * t)
            ky = int(start_y + (ty - start_y) * t)

            # Draw kunai (diamond blade + handle).
            # Get direction angle.
            dx = tx - start_x
            dy = ty - start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx = dx / length
                ny = dy / length
            else:
                nx = facing
                ny = 0

            # Kunai body.
            perp_x = -ny * 3
            perp_y = nx * 3
            tip_ext_x = int(nx * 5)
            tip_ext_y = int(ny * 5)
            back_ext_x = int(-nx * 4)
            back_ext_y = int(-ny * 4)

            kunai_pts = [
                (kx + tip_ext_x, ky + tip_ext_y),  # tip
                (kx + int(perp_x), ky + int(perp_y)),  # side
                (kx + back_ext_x, ky + back_ext_y),  # back
                (kx - int(perp_x), ky - int(perp_y)),  # other side
            ]
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in kunai_pts])
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["blade_dark"], kunai_pts)
            _NS_shirotaka._poly(surface, _NS_shirotaka.PALETTE["blade_mid"], [
                (kx + tip_ext_x, ky + tip_ext_y),
                (kx + int(perp_x * 0.5), ky + int(perp_y * 0.5)),
                (kx, ky),
                (kx - int(perp_x * 0.5), ky - int(perp_y * 0.5)),
            ])
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["blade_shine"],
                             (kx + tip_ext_x, ky + tip_ext_y, 1, 1))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["white"],
                             (kx + tip_ext_x, ky + tip_ext_y, 1, 1))

            # Handle wrap (dark).
            pygame.draw.line(surface, _NS_shirotaka.PALETTE["armor_darkest"],
                             (kx, ky),
                             (kx + back_ext_x, ky + back_ext_y), 2)

            # Paper tag on kunai (small).
            tag_x = kx + int(back_ext_x * 1.5)
            tag_y = ky + int(back_ext_y * 1.5)
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_dark"],
                             (tag_x - 1, tag_y, 3, 2))
            pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_mid"],
                             (tag_x, tag_y, 2, 1))

            # Water trail behind kunai.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                tx_pos = int(start_x + (tx - start_x) * trail_t)
                ty_pos = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_shirotaka._alpha(200 - i * 25)
                size = max(1, 4 - i)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_dark"], alpha),
                                          (tx_pos, ty_pos), size)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_light"], alpha),
                                          (tx_pos, ty_pos), max(1, size - 2))
        else:
            # TELEPORT flash at target + slash.
            t = (progress - 0.6) / 0.4
            intensity = math.sin(t * math.pi)

            # Bright teleport flash at target.
            for r in range(20, 2, -2):
                alpha = _NS_shirotaka._alpha(200 * intensity * (20 - r) / 20)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_light"], alpha),
                                          (tx, ty), r)
            for r in range(12, 1, -1):
                alpha = _NS_shirotaka._alpha(240 * intensity * (12 - r) / 12)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_hot"], alpha),
                                          (tx, ty), r)
            _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["water_shine"], (tx, ty), 5)
            _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["white"], (tx, ty), 3)

            # Slash line at target (fast attack).
            for angle_i in range(3):
                slash_angle = -math.pi / 4 + angle_i * math.pi / 4
                sx1 = tx + int(math.cos(slash_angle) * 15)
                sy1 = ty + int(math.sin(slash_angle) * 15)
                sx2 = tx - int(math.cos(slash_angle) * 15)
                sy2 = ty - int(math.sin(slash_angle) * 15)
                slash_alpha = _NS_shirotaka._alpha(220 * intensity)
                pygame.draw.line(surface, (*_NS_shirotaka.PALETTE["blade_shine"], slash_alpha),
                                 (sx1, sy1), (sx2, sy2), 2)
                pygame.draw.line(surface, (*_NS_shirotaka.PALETTE["water_hot"], slash_alpha),
                                 (sx1, sy1), (sx2, sy2), 1)

            # Radial burst.
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * 20)
                ey = ty + int(math.sin(angle_s) * 20)
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_shine"],
                                            _NS_shirotaka._alpha(200 * intensity)),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["white"],
                                            _NS_shirotaka._alpha(200 * intensity)),
                                 (ex, ey, 1, 1))

    # ============================================================
    # SKILL W: MOKUTON WATER BOUNDARY (water wall forward)
    # ============================================================
    def _draw_waterboundary_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Water spreading forward on ground.
        if progress > 0.25:
            t = (progress - 0.25) / 0.75
            wave_dist = int(80 * t)

            # Water pools spreading.
            for i in range(-3, 4):
                pool_x = x + facing * (30 + i * 15)
                pool_y = y + 35 + int(math.sin(phase + i) * 2)
                if abs(pool_x - x) > wave_dist:
                    continue
                r = 8 + int(math.sin(phase * 2 + i) * 2)
                alpha = _NS_shirotaka._alpha(200 * (1 - t * 0.5))
                pygame.draw.ellipse(surface, (*_NS_shirotaka.PALETTE["water_dark"], alpha),
                                    (pool_x - r, pool_y - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_shirotaka.PALETTE["water_mid"], alpha),
                                    (pool_x - r + 2, pool_y - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_hot"], (pool_x, pool_y, 1, 1))

    def _draw_waterboundary_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            # Charge - hand seal.
            t = progress / 0.25
            hand_x = x + facing * 8
            hand_y = y - 3
            for r in range(int(6 + t * 8), 0, -1):
                alpha = _NS_shirotaka._alpha(180 * (6 + t * 8 - r) / (6 + t * 8))
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_mid"], alpha),
                                          (hand_x, hand_y), r)
            _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["water_hot"], (hand_x, hand_y), 4)
        else:
            # WATER WALL rising and sweeping forward.
            t = (progress - 0.25) / 0.75
            wall_progress = min(1.0, t * 2)
            wall_dist = int(80 * wall_progress)

            # Wall base position.
            wall_x = x + facing * (20 + wall_dist)

            # Draw water wall as vertical curving column.
            wall_height = 40
            wall_width = 18

            # Multi-layer wave column.
            for layer_i in range(6):
                layer_offset = layer_i * 3
                layer_alpha_base = 200 - layer_i * 30
                for h in range(wall_height):
                    ht = h / wall_height
                    width = wall_width - int(ht * ht * wall_width * 0.3)
                    wave = int(math.sin(phase * 3 + h * 0.3 + layer_i) * 3)

                    fy = y + 30 - h
                    fx = wall_x + wave - layer_offset * facing

                    if h < wall_height // 4:
                        color = _NS_shirotaka.PALETTE["water_darkest"]
                    elif h < wall_height // 2:
                        color = _NS_shirotaka.PALETTE["water_dark"]
                    elif h < wall_height * 3 // 4:
                        color = _NS_shirotaka.PALETTE["water_mid"]
                    else:
                        color = _NS_shirotaka.PALETTE["water_light"]

                    alpha = _NS_shirotaka._alpha(layer_alpha_base)
                    pygame.draw.rect(surface, (*color, alpha),
                                     (fx - width // 2, fy, width, 2))

            # Foam/spray at top.
            for i in range(8):
                spray_t = (phase * 1.5 + i * 0.15) % 1.0
                spray_x = wall_x - 6 + i * 2 + int(math.sin(phase * 2 + i) * 3)
                spray_y = y - 15 - int(spray_t * 10)
                alpha = _NS_shirotaka._alpha(220 * (1 - spray_t))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], alpha),
                                 (spray_x, spray_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_shine"], alpha),
                                 (spray_x, spray_y, 1, 1))

            # Curl at top (wave crest).
            curl_y = y - 8
            for cx_off in range(-8, 9, 2):
                curl_x = wall_x + cx_off
                curl_h = 4 - abs(cx_off) // 2
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_light"],
                                 (curl_x, curl_y, 1, curl_h))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["water_hot"],
                                 (curl_x, curl_y, 1, 1))

            # Trailing water splashes behind wall.
            for i in range(5):
                trail_x = wall_x - facing * (5 + i * 6)
                trail_y = y + 20 + int(math.sin(phase * 2 + i) * 3)
                alpha = _NS_shirotaka._alpha(180 - i * 30)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_mid"], alpha),
                                          (trail_x, trail_y), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["water_hot"], alpha),
                                 (trail_x, trail_y, 1, 1))

    # ============================================================
    # SKILL E: KAGE BUNSHIN (shadow clones)
    # ============================================================
    def _draw_shadow_clones(surface, boss, x, y, timer, phase):
        """2 shadow clone copies behind boss attacking."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # 2 clones on either side of boss.
        for i, side in enumerate([-1, 1]):
            clone_x = x + side * 25
            clone_y = y
            # Wobble.
            clone_x += int(math.sin(phase * 2 + i * math.pi) * 2)
            clone_y += int(math.sin(phase * 1.5 + i) * 3)

            # Semi-transparent clone (draw simplified silhouette).
            alpha_body = _NS_shirotaka._alpha(180)

            # Body silhouette (simplified).
            # Legs.
            for leg_side in (-1, 1):
                leg_x = clone_x + leg_side * 3
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["robe_dark"], alpha_body),
                                 (leg_x - 2, clone_y + 5, 4, 15))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["robe_mid"], alpha_body),
                                 (leg_x - 1, clone_y + 6, 2, 13))

            # Torso.
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["robe_darkest"], alpha_body),
                             (clone_x - 7, clone_y - 6, 14, 12))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["robe_dark"], alpha_body),
                             (clone_x - 6, clone_y - 5, 12, 10))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["robe_mid"], alpha_body),
                             (clone_x - 4, clone_y - 3, 8, 6))

            # Shoulder plates.
            for shl_side in (-1, 1):
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["armor_dark"], alpha_body),
                                 (clone_x + shl_side * 7 - 2, clone_y - 6, 4, 3))

            # Head.
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["skin_mid"], alpha_body),
                             (clone_x - 4, clone_y - 14, 8, 8))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["skin_light"], alpha_body),
                             (clone_x - 3, clone_y - 13, 6, 6))

            # Silver hair spikes.
            for spike_off in (-3, -1, 1, 3):
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["hair_mid"], alpha_body),
                                 (clone_x + spike_off, clone_y - 17, 1, 4))
                pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["hair_light"], alpha_body),
                                 (clone_x + spike_off, clone_y - 17, 1, 2))

            # Red eyes.
            pulse = math.sin(phase * 2.5) * 0.3 + 0.7
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["eye_mid"], alpha_body),
                             (clone_x - 2, clone_y - 11, 1, 1))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["eye_mid"], alpha_body),
                             (clone_x + 1, clone_y - 11, 1, 1))
            alpha_glow = _NS_shirotaka._alpha(150 * pulse)
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["eye_light"], alpha_glow),
                             (clone_x - 2, clone_y - 11, 1, 1))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["eye_light"], alpha_glow),
                             (clone_x + 1, clone_y - 11, 1, 1))

            # Katana held out (angled to boss target).
            blade_angle = math.pi * (-0.1 if side > 0 else -0.9)
            blade_len = 20
            blade_start_x = clone_x + side * 8
            blade_start_y = clone_y - 2
            blade_end_x = blade_start_x + int(math.cos(blade_angle) * blade_len)
            blade_end_y = blade_start_y + int(math.sin(blade_angle) * blade_len)

            pygame.draw.line(surface, (*_NS_shirotaka.PALETTE["blade_dark"], alpha_body),
                             (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), 2)
            pygame.draw.line(surface, (*_NS_shirotaka.PALETTE["blade_light"], alpha_body),
                             (blade_start_x, blade_start_y - 1),
                             (blade_end_x, blade_end_y - 1), 1)
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["blade_shine"], alpha_body),
                             (blade_end_x, blade_end_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["white"], alpha_body),
                             (blade_end_x, blade_end_y, 1, 1))

            # Shadow smoke around clone (indicates clone).
            for s in range(4):
                s_angle = phase * 1.5 + s * math.pi / 2
                s_r = 15 + int(math.sin(phase + s) * 2)
                sx = clone_x + int(math.cos(s_angle) * s_r)
                sy = clone_y + int(math.sin(s_angle) * s_r * 0.5)
                alpha_s = _NS_shirotaka._alpha(150)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["shadow_deep"], alpha_s),
                                          (sx, sy), 3)
                _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["water_dark"], alpha_s),
                                          (sx, sy), 2)

    # ============================================================
    # SKILL R: TANDEM PAPER BOMBS (chain explosions)
    # ============================================================
    def _draw_paperbomb_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_shirotaka._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground scorching around target.
        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            # 3 explosion sites (target + 2 near).
            for i, offset in enumerate([(0, 0), (-30, -10), (25, 5)]):
                site_x = tx + offset[0]
                site_y = ty + offset[1]
                # Explosion timing per site.
                site_delay = i * 0.15
                if t < site_delay:
                    continue
                site_t = min(1.0, (t - site_delay) / 0.4)

                r = int(25 * site_t)
                alpha = _NS_shirotaka._alpha(220 * (1 - site_t * 0.5))
                if r > 3:
                    pygame.draw.ellipse(surface, (*_NS_shirotaka.PALETTE["expl_dark"], alpha),
                                        (site_x - r, site_y - r // 3, r * 2, r * 2 // 3))
                    pygame.draw.ellipse(surface, (*_NS_shirotaka.PALETTE["expl_mid"], alpha),
                                        (site_x - r + 3, site_y - r // 3 + 2,
                                         r * 2 - 6, r * 2 // 3 - 4))
                    pygame.draw.ellipse(surface, (*_NS_shirotaka.PALETTE["expl_light"], alpha),
                                        (site_x - r + 8, site_y - r // 3 + 4,
                                         r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_paperbomb_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_shirotaka._target_position(boss, x, y)

        start_x = x + facing * 10
        start_y = y - 5

        if progress < 0.2:
            # Prep - hand seal + paper bombs summon.
            t = progress / 0.2
            # Show paper tags around hand.
            for i in range(5):
                angle = i * math.pi * 2 / 5 + phase * 0.5
                r_base = 8 + int(t * 4)
                px = start_x + int(math.cos(angle) * r_base)
                py = start_y + int(math.sin(angle) * r_base * 0.7)

                # Paper tag.
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                                 (px - 2, py - 1, 4, 4))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_dark"],
                                 (px - 2, py - 1, 4, 4))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_mid"],
                                 (px - 1, py - 1, 3, 3))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_light"],
                                 (px, py, 1, 1))
                # Red rune.
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["eye_mid"], (px, py, 1, 1))
        elif progress < 0.35:
            # Throw tags to target.
            t = (progress - 0.2) / 0.15
            for i in range(3):
                # Different trajectories.
                offset_x = (i - 1) * 20
                offset_y = (i - 1) * 5
                fly_delay = i * 0.1
                if t < fly_delay:
                    continue
                fly_t = min(1.0, (t - fly_delay) / 0.5)

                px = int(start_x + (tx + offset_x - start_x) * fly_t)
                py = int(start_y + (ty + offset_y - start_y) * fly_t)
                # Add arc lift.
                py -= int(math.sin(fly_t * math.pi) * 20)

                # Paper tag (spinning).
                spin = phase * 5 + i
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["shadow_deep"],
                                 (px - 2, py - 1, 4, 4))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_dark"],
                                 (px - 2, py - 2, 4, 4))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_mid"],
                                 (px - 1, py - 2, 3, 3))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["paper_light"],
                                 (px, py - 1, 1, 1))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["eye_mid"], (px, py - 1, 1, 1))
        else:
            # CHAIN EXPLOSIONS.
            t = (progress - 0.35) / 0.65

            # 3 explosion sites with cascading timing.
            for i, offset in enumerate([(0, 0), (-30, -10), (25, 5)]):
                site_x = tx + offset[0]
                site_y = ty + offset[1]

                # Each explosion delayed.
                site_delay = i * 0.2
                if t < site_delay:
                    continue
                site_t = min(1.0, (t - site_delay) / 0.4)
                intensity = math.sin(site_t * math.pi)

                radius = int(15 + site_t * 25)
                alpha = _NS_shirotaka._alpha(255 * intensity)

                # Multi-layer explosion.
                for r in range(radius, 2, -3):
                    a = _NS_shirotaka._alpha(alpha * (radius - r) / radius)
                    _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["expl_dark"], a),
                                              (site_x, site_y), r)
                for r in range(int(radius * 0.8), 2, -2):
                    a = _NS_shirotaka._alpha(alpha * (radius * 0.8 - r) / (radius * 0.8))
                    _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["expl_mid"], a),
                                              (site_x, site_y), r)
                for r in range(int(radius * 0.6), 2, -2):
                    a = _NS_shirotaka._alpha(alpha * (radius * 0.6 - r) / (radius * 0.6))
                    _NS_shirotaka._aacircle(surface, (*_NS_shirotaka.PALETTE["expl_light"], a),
                                              (site_x, site_y), r)
                _NS_shirotaka._aacircle(surface, _NS_shirotaka.PALETTE["expl_hot"],
                                          (site_x, site_y), max(1, radius // 4))
                pygame.draw.rect(surface, _NS_shirotaka.PALETTE["white"],
                                 (site_x, site_y, 1, 1))

                # Radial burst lines.
                for j in range(12):
                    angle_s = j * math.pi / 6
                    ex = site_x + int(math.cos(angle_s) * radius)
                    ey = site_y + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_shirotaka.PALETTE["expl_hot"], alpha),
                                     (site_x, site_y), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["expl_hot"], alpha),
                                     (ex, ey, 2, 2))

                # Rising smoke/debris.
                for j in range(8):
                    smoke_t = (phase * 2 + j * 0.15) % 1.0
                    sx = site_x - 10 + j * 3 + int(math.sin(phase + j) * 2)
                    sy = site_y - int(smoke_t * 25)
                    s_alpha = _NS_shirotaka._alpha(200 * intensity * (1 - smoke_t))
                    pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["expl_mid"], s_alpha),
                                     (sx, sy, 1, 1))
                    pygame.draw.rect(surface, (*_NS_shirotaka.PALETTE["expl_hot"], s_alpha),
                                     (sx, sy, 1, 1))


# ====================================================================
# seiryukong.py
# ====================================================================



class _NS_seiryukong:
    """Namespace seiryukong - Celestial Simian TRUE BOSS (MELEE)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Gold armor (main)
        "gold_darkest": (35, 20, 5),
        "gold_dark": (95, 65, 20),
        "gold_mid": (180, 130, 40),
        "gold_light": (240, 195, 80),
        "gold_edge": (255, 225, 130),
        "gold_shine": (255, 250, 210),

        # Fur (brown-cream monkey body)
        "fur_darkest": (30, 20, 10),
        "fur_dark": (85, 55, 30),
        "fur_mid": (150, 105, 65),
        "fur_light": (215, 175, 125),
        "fur_shine": (245, 220, 175),

        # Skin (monkey face/palms - pinkish tan)
        "skin_dark": (110, 75, 60),
        "skin_mid": (180, 135, 105),
        "skin_light": (225, 185, 155),
        "skin_shine": (245, 210, 185),

        # Fire hair (bright red-orange)
        "fire_darkest": (70, 15, 5),
        "fire_dark": (180, 45, 15),
        "fire_mid": (240, 110, 25),
        "fire_light": (255, 180, 50),
        "fire_hot": (255, 235, 120),
        "fire_shine": (255, 253, 210),

        # Red cloth (sash, decorations)
        "red_dark": (80, 15, 15),
        "red_mid": (170, 35, 30),
        "red_light": (230, 80, 65),

        # Staff wood (dark red-brown wrap)
        "staff_dark": (50, 25, 10),
        "staff_mid": (110, 65, 25),

        # Eye (bright amber)
        "eye_socket": (10, 5, 0),
        "eye_dark": (80, 45, 5),
        "eye_mid": (235, 175, 40),
        "eye_light": (255, 230, 130),
        "eye_glow": (255, 250, 200),

        # Green cloth (sash accent)
        "green_dark": (20, 60, 25),
        "green_mid": (60, 130, 55),

        # Aura holy
        "aura_dim": (100, 65, 15),
        "aura_bright": (255, 210, 90),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 0),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_seiryukong._clamp(color)
        if _NS_seiryukong.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_seiryukong._clamp(color)
        if _NS_seiryukong.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_seiryukong._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_seiryukong._clamp(color), points)

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
    def draw_seiryukong(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_seiryukong._update_sk_attack_anim(boss)
        attacking = (
            getattr(boss, "_sk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient (large TRUE BOSS).
        _NS_seiryukong._draw_holy_aura(surface, x, y, pulse)
        _NS_seiryukong._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "r":
            _NS_seiryukong._draw_wukong_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_seiryukong._draw_boundless_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_seiryukong._draw_sk_attack(surface, boss, x, y)
        else:
            _NS_seiryukong._draw_sk_idle(surface, boss, x, y)

        # Jingu Mastery soldier clones.
        if active_skill == "e":
            _NS_seiryukong._draw_jingu_soldiers(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_seiryukong._draw_boundless_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_seiryukong._draw_treedance_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_seiryukong._draw_wukong_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_sk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sk_previous_timer", 0))
        active = bool(getattr(boss, "_sk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._sk_attack_active = True
            boss._sk_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._sk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._sk_attack_frame = int(
                getattr(boss, "_sk_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._sk_attack_active = False
            boss._sk_attack_frame = 0
            active = False

        boss._sk_previous_timer = timer
        boss._sk_attack_progress = (
            min(1.0, getattr(boss, "_sk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_sk_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_seiryukong._draw_floating_shadow(surface, x, y + 55, boss.pulse)
        _NS_seiryukong._draw_ember_wisps(surface, x, y + 42, boss.pulse)
        _NS_seiryukong._draw_sk_body(surface, x, y + bob, boss.direction,
                                       boss.pulse, "idle")

    def _draw_sk_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_sk_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_sk_attack_dir", None)
        if facing is None:
            facing = boss.direction

        bob = int(math.sin(boss.pulse * 0.6) * 5)
        # Staff swing: wind up → forward sweep → recover.
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

        _NS_seiryukong._draw_floating_shadow(surface, x + lean, y + 55, boss.pulse)
        _NS_seiryukong._draw_ember_wisps(surface, x + lean, y + 42, boss.pulse, intense=True)
        _NS_seiryukong._draw_sk_body(surface, x + lean, y + bob - lift,
                                       facing, boss.pulse, "attack",
                                       progress)
        _NS_seiryukong._draw_staff_swing_arc(surface, boss, x + lean, y + bob - lift, progress)

    # ============================================================
    # BODY (monkey warrior humanoid)
    # ============================================================
    def _draw_sk_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Tail (behind body).
        _NS_seiryukong._draw_monkey_tail(surface, cx, cy + 4, facing, phase)

        # Legs.
        _NS_seiryukong._draw_monkey_legs(surface, cx, cy + 10, facing, phase)

        # Torso with armor.
        _NS_seiryukong._draw_monkey_torso(surface, cx, cy - 2, facing, phase)

        # Back arm.
        _NS_seiryukong._draw_back_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

        # Head with fire hair + crown.
        _NS_seiryukong._draw_monkey_head(surface, cx, cy - 16, facing, phase)

        # Front arm holding staff - last.
        _NS_seiryukong._draw_staff_arm(surface, cx, cy - 2, facing, phase, action, attack_progress)

    def _draw_monkey_tail(surface, cx, cy, facing, phase):
        """Long monkey tail curling behind."""
        sway = math.sin(phase * 0.8) * 3
        base_x = cx - facing * 8
        base_y = cy + 2

        # Curling tail with S-curve.
        points = [(base_x, base_y)]
        for step in range(1, 7):
            t = step / 6
            tail_x = base_x - facing * int(t * 15)
            tail_y = base_y - int(math.sin(t * math.pi) * 12) - int(t * 4)
            # Wave.
            tail_x += int(math.sin(phase * 1.5 + t * 3) * 2)
            points.append((tail_x, tail_y))

        # Draw tapered tail.
        for i in range(len(points) - 1):
            thickness = max(2, 6 - i)
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                    (points[i][0] + 1, points[i][1] + 1),
                                    (points[i + 1][0] + 1, points[i + 1][1] + 1),
                                    thickness + 1)
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                                    points[i], points[i + 1], thickness)
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_dark"],
                                    points[i], points[i + 1], max(1, thickness - 1))
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_mid"],
                                    (points[i][0], points[i][1] - 1),
                                    (points[i + 1][0], points[i + 1][1] - 1),
                                    max(1, thickness - 3))

        # Tail tip tuft (bushy).
        end = points[-1]
        for i in range(4):
            angle = i * math.pi / 2 + phase * 0.5
            tuft_x = end[0] + int(math.cos(angle) * 2)
            tuft_y = end[1] + int(math.sin(angle) * 2)
            _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["fur_dark"],
                                       (tuft_x, tuft_y), 2)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fur_light"], (tuft_x, tuft_y, 1, 1))

    def _draw_monkey_legs(surface, cx, cy, facing, phase):
        """Legs with wraps and green shorts."""
        sway = math.sin(phase * 0.5) * 1

        # Green pants/shorts base.
        pants_pts = [
            (cx - 9, cy - 6),
            (cx + 9, cy - 6),
            (cx + 10, cy + 2),
            (cx + 8, cy + 6),
            (cx - 8, cy + 6),
            (cx - 10, cy + 2),
        ]
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in pants_pts])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["green_dark"], pants_pts)
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["green_mid"], [
            (cx - 8, cy - 5),
            (cx + 8, cy - 5),
            (cx + 9, cy + 1),
            (cx + 7, cy + 5),
            (cx - 7, cy + 5),
            (cx - 9, cy + 1),
        ])

        # Red sash tied at waist.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_dark"],
                         (cx - 10, cy - 6, 20, 3))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_mid"],
                         (cx - 10, cy - 6, 20, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_light"],
                         (cx - 9, cy - 6, 18, 1))

        # Sash hanging down (draped).
        for tail_off in (-4, 4):
            tail_x = cx + tail_off
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_dark"],
                             (tail_x, cy - 3, 2, 6))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_mid"],
                             (tail_x, cy - 3, 1, 6))

        # Legs (furry).
        for side in (-1, 1):
            leg_x = cx + side * 4
            top_y = cy + 6
            bot_y = cy + 14

            # Furry thigh.
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                    (leg_x + 1, top_y + 1),
                                    (leg_x + 1, bot_y + 1), 4)
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                                    (leg_x, top_y), (leg_x, bot_y), 4)
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_dark"],
                                    (leg_x, top_y), (leg_x, bot_y), 2)
            _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_mid"],
                                    (leg_x, top_y - 1), (leg_x, bot_y - 1), 1)

            # Leg wraps (like bandages).
            for wrap_y in (bot_y - 1, bot_y + 1):
                pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_dark"],
                                 (leg_x - 3, wrap_y, 6, 1))
                pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_mid"],
                                 (leg_x - 2, wrap_y, 4, 1))
                pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                                 (leg_x - 1, wrap_y, 2, 1))

            # Foot/paw.
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                             (leg_x - 3, bot_y + 3, 7, 3))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                             (leg_x - 3, bot_y + 3, 7, 2))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fur_dark"],
                             (leg_x - 2, bot_y + 3, 5, 1))
            # Toe claws.
            for toe in (-2, 0, 2):
                pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_dark"],
                                 (leg_x + toe, bot_y + 4, 1, 1))
                pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                                 (leg_x + toe, bot_y + 4, 1, 1))

    def _draw_monkey_torso(surface, cx, cy, facing, phase):
        """Bare furry chest with gold armor accents."""
        # Torso base (furry).
        torso_pts = [
            (cx - 10, cy - 4),
            (cx - 8, cy + 5),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 8, cy + 5),
            (cx + 10, cy - 4),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ]
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_darkest"], torso_pts)

        # Furry chest color.
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_dark"], [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 8, cy + 6),
            (cx - 8, cy + 6),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ])

        # Lighter belly (fur cream).
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_light"], [
            (cx - 4, cy - 1),
            (cx + 4, cy - 1),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ])

        # Muscle definition (chest lines).
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                         (cx - 4, cy - 2), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                         (cx + 4, cy - 2), (cx + 3, cy + 3), 1)
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                         (cx, cy - 3), (cx, cy + 5), 1)

        # GOLD CHEST PLATE (partial, ornate).
        _NS_seiryukong._draw_chest_plate(surface, cx, cy, facing, phase)

        # SHOULDER PAULDRONS (gold ornate).
        for side in (-1, 1):
            _NS_seiryukong._draw_gold_pauldron(surface, cx + side * 10, cy - 4, side, phase)

        # RED SASH across chest (diagonal).
        _NS_seiryukong._draw_diagonal_sash(surface, cx, cy, facing, phase)

    def _draw_chest_plate(surface, cx, cy, facing, phase):
        """Ornate gold chest plate."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Central plate ornament (V-shape).
        plate_pts = [
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
            (cx + 6, cy),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
            (cx - 6, cy),
        ]
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in plate_pts])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_darkest"], plate_pts)
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_dark"], [
            (cx - 4, cy - 2),
            (cx + 4, cy - 2),
            (cx + 5, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
            (cx - 5, cy),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_mid"], [
            (cx - 3, cy - 1),
            (cx + 3, cy - 1),
            (cx + 4, cy),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
            (cx - 4, cy),
        ])
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (cx - 2, cy - 2, 5, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_shine"],
                         (cx - 1, cy - 2, 3, 1))

        # Central gem/emblem.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_dark"], (cx, cy, 1, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_mid"], (cx, cy, 1, 1))
        # Glow.
        for r in range(3, 0, -1):
            alpha = _NS_seiryukong._alpha(120 * pulse * (3 - r) / 3)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["red_light"], alpha),
                                       (cx, cy + 1), r)

        # Belt at bottom.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_dark"],
                         (cx - 7, cy + 6, 14, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_mid"],
                         (cx - 6, cy + 6, 12, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (cx - 5, cy + 6, 10, 1))

        # Buckle center.
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["gold_darkest"],
                                   (cx, cy + 7), 2)
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_shine"], (cx, cy + 7, 1, 1))

    def _draw_gold_pauldron(surface, cx, cy, side, phase):
        """Ornate gold pauldron with spikes."""
        # Main pauldron shape.
        paul_pts = [
            (cx - 4, cy),
            (cx - 3, cy - 5),
            (cx - 1, cy - 7),
            (cx + 2, cy - 7),
            (cx + 4, cy - 5),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ]
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_darkest"], paul_pts)

        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_dark"], [
            (cx - 3, cy),
            (cx - 2, cy - 4),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
            (cx + 3, cy - 4),
            (cx + 4, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_mid"], [
            (cx - 2, cy - 1),
            (cx - 1, cy - 5),
            (cx + 2, cy - 5),
            (cx + 3, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (cx - 1, cy - 4, 3, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_shine"],
                         (cx, cy - 4, 2, 1))

        # Spike on top of pauldron.
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["shadow_deep"], [
            (cx + 1, cy - 10),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_darkest"], [
            (cx, cy - 10),
            (cx - 1, cy - 6),
            (cx + 2, cy - 6),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["gold_dark"], [
            (cx, cy - 10),
            (cx, cy - 6),
            (cx + 1, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"], (cx, cy - 10, 1, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_shine"], (cx, cy - 10, 1, 1))

        # Red gem on pauldron.
        pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_dark"], (cx, cy - 1, 1, 1))
        alpha = _NS_seiryukong._alpha(200 * pulse)
        pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["red_light"], alpha), (cx, cy - 1, 1, 1))

    def _draw_diagonal_sash(surface, cx, cy, facing, phase):
        """Red sash draped diagonally across chest."""
        sway = math.sin(phase * 0.5) * 1

        # Diagonal sash line.
        for i in range(5):
            t = i / 4
            sx = int(cx - 8 + t * 16 + sway * t)
            sy = int(cy - 4 + t * 10)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_dark"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_mid"],
                             (sx, sy, 2, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (secondary hand on staff or free)."""
        sway = math.sin(phase * 0.5) * 1

        if action == "attack":
            elbow_y_off = int(math.sin(attack_progress * math.pi) * -2)
        else:
            elbow_y_off = 5 + int(sway)

        shoulder_x = cx - facing * 10
        shoulder_y = cy - 2

        elbow_x = shoulder_x - facing * 3
        elbow_y = shoulder_y + elbow_y_off
        hand_x = elbow_x - facing * 1
        hand_y = elbow_y + 6

        # Upper arm (furry).
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                (shoulder_x + 1, shoulder_y + 1),
                                (elbow_x + 1, elbow_y + 1), 5)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_dark"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_mid"],
                                (shoulder_x, shoulder_y - 1),
                                (elbow_x, elbow_y - 1), 1)

        # Forearm (skin - lighter).
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                (elbow_x + 1, elbow_y + 1),
                                (hand_x + 1, hand_y + 1), 4)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["skin_dark"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["skin_mid"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Gold wrist bracer.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_dark"],
                         (hand_x - 2, hand_y - 2, 5, 3))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_mid"],
                         (hand_x - 1, hand_y - 2, 3, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (hand_x, hand_y - 2, 1, 1))

        # Hand.
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 2)
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["skin_mid"],
                                   (hand_x, hand_y), 1)

    def _draw_staff_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding long golden staff (over shoulder in idle)."""
        # Staff angle.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up (staff back).
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.3 + t * -math.pi * 0.4
                staff_extend_angle = arm_angle - math.pi * 0.3
            elif attack_progress < 0.6:
                # SWEEP forward.
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.7 + t * math.pi * 1.0
                staff_extend_angle = arm_angle
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.3 - t * math.pi * 0.5
                staff_extend_angle = arm_angle + math.pi * 0.1
        else:
            # Idle: staff resting on shoulder.
            arm_angle = -math.pi * 0.35 + math.sin(phase * 0.5) * 0.05
            staff_extend_angle = arm_angle - math.pi * 0.5

        shoulder_x = cx + facing * 10
        shoulder_y = cy - 2

        arm_len = 6
        elbow_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * arm_len) + 2

        forearm_len = 6
        forearm_angle = arm_angle + 0.3
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

        # Upper arm (furry).
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                (shoulder_x + 1, shoulder_y + 1),
                                (elbow_x + 1, elbow_y + 1), 6)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_darkest"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_dark"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["fur_mid"],
                                (shoulder_x, shoulder_y - 1),
                                (elbow_x, elbow_y - 1), 2)

        # Forearm (skin).
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                (elbow_x + 1, elbow_y + 1),
                                (hand_x + 1, hand_y + 1), 5)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["skin_dark"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["skin_mid"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_seiryukong._aaline(surface, _NS_seiryukong.PALETTE["skin_light"],
                                (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Gold wrist bracer.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_dark"],
                         (hand_x - 2, hand_y - 2, 5, 3))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_mid"],
                         (hand_x - 1, hand_y - 2, 3, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (hand_x, hand_y - 2, 1, 1))

        # Hand.
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 3)
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["skin_mid"],
                                   (hand_x, hand_y), 2)

        # GOLDEN STAFF.
        _NS_seiryukong._draw_golden_staff(surface, hand_x, hand_y, staff_extend_angle,
                                            facing, phase, action, attack_progress)

    def _draw_golden_staff(surface, hand_x, hand_y, angle, facing, phase, action, attack_progress):
        """Long golden bo staff (ruyi jingu bang)."""
        # Staff length.
        staff_len = 36  # Long staff.
        half_len = staff_len // 2

        # Both ends of staff.
        tip1_x = hand_x + int(math.cos(angle) * half_len) * facing
        tip1_y = hand_y + int(math.sin(angle) * half_len)
        tip2_x = hand_x - int(math.cos(angle) * half_len) * facing
        tip2_y = hand_y - int(math.sin(angle) * half_len)

        # Shadow.
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                         (tip1_x + 1, tip1_y + 1), (tip2_x + 1, tip2_y + 1), 4)

        # Staff shaft (gold).
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["gold_darkest"],
                         (tip1_x, tip1_y), (tip2_x, tip2_y), 3)
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["gold_dark"],
                         (tip1_x, tip1_y), (tip2_x, tip2_y), 2)
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["gold_mid"],
                         (tip1_x, tip1_y - 1), (tip2_x, tip2_y - 1), 1)
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (tip1_x, tip1_y - 1), (tip2_x, tip2_y - 1), 1)

        # Red wrap bands on staff (3 sections).
        for band_t in (0.25, 0.5, 0.75):
            band_x = int(tip2_x + (tip1_x - tip2_x) * band_t)
            band_y = int(tip2_y + (tip1_y - tip2_y) * band_t)
            perp = angle + math.pi / 2
            ba_x = band_x + int(math.cos(perp) * 2) * facing
            ba_y = band_y + int(math.sin(perp) * 2)
            bb_x = band_x - int(math.cos(perp) * 2) * facing
            bb_y = band_y - int(math.sin(perp) * 2)
            pygame.draw.line(surface, _NS_seiryukong.PALETTE["red_dark"], (ba_x, ba_y), (bb_x, bb_y), 2)
            pygame.draw.line(surface, _NS_seiryukong.PALETTE["red_mid"],
                             (ba_x, ba_y - 1), (bb_x, bb_y - 1), 1)

        # Ornate caps at both ends (larger metallic).
        for tip_x, tip_y in [(tip1_x, tip1_y), (tip2_x, tip2_y)]:
            _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                                       (tip_x + 1, tip_y + 1), 3)
            _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["gold_darkest"],
                                       (tip_x, tip_y), 3)
            _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["gold_dark"],
                                       (tip_x, tip_y), 2)
            _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["gold_mid"],
                                       (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_shine"], (tip_x, tip_y, 1, 1))

        # Glow along staff during attack.
        if action == "attack":
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            # Glow at forward tip.
            for r in range(6, 0, -1):
                alpha = _NS_seiryukong._alpha(150 * pulse * (6 - r) / 6)
                _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                           (tip1_x, tip1_y), r)

        # Store staff tips for arc.
        _NS_seiryukong._staff_tip = (tip1_x, tip1_y)
        _NS_seiryukong._staff_end = (tip2_x, tip2_y)

    def _draw_monkey_head(surface, cx, cy, facing, phase):
        """Monkey head with fire hair + golden crown."""
        # Head base (round).
        head_pts = [
            (cx - 6, cy + 4),
            (cx - 7, cy),
            (cx - 6, cy - 5),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 6, cy - 5),
            (cx + 7, cy),
            (cx + 6, cy + 4),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ]
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_darkest"], head_pts)

        # Furry head (dark brown outer, lighter inner).
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_dark"], [
            (cx - 5, cy + 3),
            (cx - 6, cy),
            (cx - 5, cy - 4),
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 5, cy + 3),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ])

        # FACE (lighter skin oval - like monkey face).
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 4, cy - 3),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 4, cy - 3),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["skin_mid"], [
            (cx - 3, cy - 1),
            (cx - 3, cy - 3),
            (cx - 1, cy - 5),
            (cx + 1, cy - 5),
            (cx + 3, cy - 3),
            (cx + 3, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # AMBER EYES.
        _NS_seiryukong._draw_monkey_eyes(surface, cx, cy - 2, facing, phase)

        # Nose (small monkey nose).
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["skin_dark"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["shadow_deep"], (cx, cy + 1, 1, 1))

        # Mouth (monkey grin).
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        # Small fang.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["white"], (cx - 1, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["white"], (cx + 1, cy + 3, 1, 1))

        # EARS (monkey ears - small triangular on sides).
        for side in (-1, 1):
            ear_x = cx + side * 6
            _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_darkest"], [
                (ear_x, cy - 2),
                (ear_x + side * 2, cy - 4),
                (ear_x + side * 2, cy),
            ])
            _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fur_dark"], [
                (ear_x, cy - 2),
                (ear_x + side * 1, cy - 3),
                (ear_x + side * 1, cy - 1),
            ])
            _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["skin_dark"], [
                (ear_x + side * 1, cy - 2),
                (ear_x + side * 1, cy - 1),
            ])

        # FIRE HAIR (fiery red mane on top).
        _NS_seiryukong._draw_fire_hair(surface, cx, cy - 5, facing, phase)

        # GOLDEN CROWN/HEADBAND.
        _NS_seiryukong._draw_golden_crown(surface, cx, cy - 5, facing, phase)

    def _draw_monkey_eyes(surface, cx, cy, facing, phase):
        """Bright amber eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy

            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["eye_socket"],
                             (ex, ey - 1, 1, 2))

            # Amber glow.
            for r in range(3, 0, -1):
                alpha = _NS_seiryukong._alpha(140 * pulse * (3 - r) / 3)
                _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["eye_mid"], alpha),
                                           (ex, ey), r)

            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["eye_glow"], (ex, ey, 1, 1))

    def _draw_fire_hair(surface, cx, cy, facing, phase):
        """Wild fiery red hair on top of head (like Wukong's flame)."""
        wave = math.sin(phase * 1.5) * 1

        # Base hair mass.
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fire_darkest"], [
            (cx - 6, cy),
            (cx - 6, cy - 2),
            (cx - 4, cy - 3),
            (cx, cy - 4),
            (cx + 4, cy - 3),
            (cx + 6, cy - 2),
            (cx + 6, cy),
        ])
        _NS_seiryukong._poly(surface, _NS_seiryukong.PALETTE["fire_dark"], [
            (cx - 5, cy),
            (cx - 4, cy - 2),
            (cx, cy - 3),
            (cx + 4, cy - 2),
            (cx + 5, cy),
        ])

        # SPIKY FLAME TIPS.
        for i, (spike_x_off, spike_h_base) in enumerate([
            (-5, 4), (-3, 6), (-1, 8), (1, 9), (3, 7), (5, 4),
        ]):
            spike_h = spike_h_base + int(math.sin(phase * 2 + i * 0.5) * 2)
            spike_x = cx + spike_x_off + int(wave * 0.5)
            spike_top_y = cy - 3 - spike_h

            # Flame tip (tapered upward).
            for j in range(spike_h):
                t = j / spike_h
                width = max(1, int((1 - t) * 2))
                fy = cy - 3 - j
                fx = spike_x + int(math.sin(phase * 3 + i + j * 0.3) * 1)

                if j < spike_h // 3:
                    color = _NS_seiryukong.PALETTE["fire_dark"]
                elif j < spike_h * 2 // 3:
                    color = _NS_seiryukong.PALETTE["fire_mid"]
                elif j < spike_h * 4 // 5:
                    color = _NS_seiryukong.PALETTE["fire_light"]
                else:
                    color = _NS_seiryukong.PALETTE["fire_hot"]
                pygame.draw.rect(surface, color, (fx - width // 2, fy, width, 1))

            # Hot tip.
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"],
                             (spike_x, cy - 3 - spike_h, 1, 1))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_shine"],
                             (spike_x, cy - 3 - spike_h, 1, 1))

        # Rising ember particles.
        for i in range(5):
            e_t = (phase * 0.7 + i * 0.2) % 1.0
            ex = cx - 4 + i * 2 + int(math.sin(phase + i) * 2)
            ey = cy - 15 - int(e_t * 12)
            alpha = _NS_seiryukong._alpha(220 * (1 - e_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_golden_crown(surface, cx, cy, facing, phase):
        """Golden circlet headband."""
        # Circlet base (horizontal gold band).
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["shadow_deep"],
                         (cx - 5, cy - 1, 10, 3))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_darkest"],
                         (cx - 5, cy - 1, 10, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_dark"],
                         (cx - 5, cy - 1, 10, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_mid"],
                         (cx - 4, cy - 1, 8, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"],
                         (cx - 3, cy - 1, 6, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_shine"],
                         (cx - 1, cy - 1, 3, 1))

        # Center ornate gem/emblem.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["red_dark"], (cx, cy - 1, 1, 1))
        alpha = _NS_seiryukong._alpha(200 * pulse)
        pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["red_light"], alpha), (cx, cy - 1, 1, 1))

        # Small side ornaments.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_darkest"], (cx - 5, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_darkest"], (cx + 4, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"], (cx - 5, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_edge"], (cx + 4, cy - 2, 1, 1))

    # ============================================================
    # STAFF SWING ARC
    # ============================================================
    def _draw_staff_swing_arc(surface, boss, x, y, progress):
        """Gold energy swing arc from staff sweep."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        swing_t = (progress - 0.35) / 0.25
        swing_t = max(0, min(1, swing_t))
        alpha_val = int(255 * (1 - abs(swing_t - 0.5) * 1.5))
        alpha_val = max(0, alpha_val)

        # Arc center - based on where hands are.
        center_x = x + facing * 8
        center_y = y + 3
        arc_radius = 36  # Larger arc (long staff).

        start_angle = -math.pi * 0.9 * facing
        end_angle = math.pi * 0.4 * facing
        current_angle = start_angle + (end_angle - start_angle) * swing_t

        # Arc trail.
        num_segments = 20
        for i in range(num_segments):
            t = i / num_segments
            seg_angle = start_angle + (current_angle - start_angle) * t
            seg_x = center_x + int(math.cos(seg_angle) * arc_radius) * facing
            seg_y = center_y + int(math.sin(seg_angle) * arc_radius)
            seg_alpha = _NS_seiryukong._alpha(alpha_val * t)
            size = int(2 + t * 5)

            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_darkest"], seg_alpha),
                                       (seg_x, seg_y), size)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_dark"], seg_alpha),
                                       (seg_x, seg_y), max(1, size - 1))
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_mid"], seg_alpha),
                                       (seg_x, seg_y), max(1, size - 2))
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_light"], seg_alpha),
                                       (seg_x, seg_y), max(1, size - 3))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], seg_alpha),
                             (seg_x, seg_y, 1, 1))

        # Bright edge crescent.
        for i in range(8):
            edge_t = 1 - i * 0.08
            edge_angle = start_angle + (current_angle - start_angle) * edge_t
            ex1 = center_x + int(math.cos(edge_angle) * (arc_radius - 3)) * facing
            ey1 = center_y + int(math.sin(edge_angle) * (arc_radius - 3))
            ex2 = center_x + int(math.cos(edge_angle) * (arc_radius + 5)) * facing
            ey2 = center_y + int(math.sin(edge_angle) * (arc_radius + 5))
            e_alpha = _NS_seiryukong._alpha(alpha_val * (1 - i * 0.1))
            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["fire_hot"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 2)
            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["fire_shine"], e_alpha),
                             (ex1, ey1), (ex2, ey2), 1)
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["white"], e_alpha),
                             (ex2, ey2, 1, 1))

        # Sparks flying off.
        for i in range(12):
            spark_angle = current_angle + i * 0.1 * facing
            spark_dist = arc_radius + i * 2
            sx = center_x + int(math.cos(spark_angle) * spark_dist) * facing
            sy = center_y + int(math.sin(spark_angle) * spark_dist)
            spark_alpha = _NS_seiryukong._alpha(230 - i * 18)
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], spark_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], spark_alpha),
                             (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT (TRUE BOSS bigger scale)
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
        pygame.draw.ellipse(shadow, (20, 12, 5, 170),
                            (80 - w // 2, 15 - h // 2, w, h))
        surface.blit(shadow, (x - 80, y - 15))

    def _draw_ember_wisps(surface, cx, cy, phase, intense=False):
        """Rising gold/fire embers below boss."""
        strength = 1.5 if intense else 1.0

        for i in range(12):
            t = (phase * 0.5 + i * 0.09) % 1.0
            sx = cx - 34 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 32)
            alpha = _NS_seiryukong._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["fire_darkest"], alpha),
                                       (sx, sy), 3)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["fire_dark"], alpha),
                                       (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_mid"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Bright sparks.
        for i in range(10):
            spark_t = (phase * 0.4 + i * 0.13) % 1.0
            ex = cx - 30 + i * 7 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(spark_t * 28)
            alpha = _NS_seiryukong._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_holy_aura(surface, x, y, phase):
        """Large gold/fire aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_seiryukong._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_seiryukong._aacircle(aura, (*_NS_seiryukong.PALETTE["fire_darkest"], alpha),
                                           (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_seiryukong._alpha((70 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_seiryukong._aacircle(aura, (*_NS_seiryukong.PALETTE["fire_dark"], alpha),
                                           (120, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_seiryukong._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_seiryukong._aacircle(aura, (*_NS_seiryukong.PALETTE["gold_mid"], alpha),
                                           (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))

        # Orbiting embers.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["gold_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large gold ground ring (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_seiryukong.PALETTE["gold_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_seiryukong.PALETTE["gold_dark"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_seiryukong.PALETTE["gold_mid"], 230),
                            (25, 24, 140, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_seiryukong.PALETTE["red_dark"], 180),
                            (40, 26, 110, 18), 1)

        # Rays.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 50)
            y1 = 35 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_seiryukong.PALETTE["gold_light"], 230),
                             (x1, y1), (x2, y2), 1)

        # Monkey face-like runes.
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sr = 65
            sx = 95 + int(math.cos(angle) * sr)
            sy = 35 + int(math.sin(angle) * sr * 0.35)
            pygame.draw.rect(ring, (*_NS_seiryukong.PALETTE["fire_hot"], 240),
                             (sx - 1, sy - 1, 3, 3), 1)
            pygame.draw.rect(ring, (*_NS_seiryukong.PALETTE["fire_shine"], 240),
                             (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring, (*_NS_seiryukong.PALETTE["fire_hot"],
                                        _NS_seiryukong._alpha(180 * pulse)),
                                (15, 14, 160, 42), 1)
        surface.blit(ring, (x - 95, y - 30))

    # ============================================================
    # SKILL Q: BOUNDLESS STRIKE (leap + strike)
    # ============================================================
    def _draw_boundless_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_seiryukong._target_position(boss, x, y)

        # Leap trail (arrows on ground).
        num_streaks = 8
        for i in range(num_streaks):
            t = i / num_streaks
            trail_visible = progress > t * 0.6
            if not trail_visible:
                continue

            arc_x = int(x + (tx - x) * t)
            arc_y = int(y + (ty - y) * t) + 30

            fade = max(0, 1 - (progress - t * 0.6) * 2)
            alpha = _NS_seiryukong._alpha(200 * fade)
            if alpha <= 0:
                continue

            # Streak lines.
            for streak_off in (-3, 0, 3):
                pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha),
                                 (arc_x - facing * 8, arc_y + streak_off),
                                 (arc_x + facing * 3, arc_y + streak_off), 1)
                pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (arc_x - facing * 4, arc_y + streak_off),
                                 (arc_x + facing * 2, arc_y + streak_off), 1)

    def _draw_boundless_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_seiryukong._target_position(boss, x, y)

        if progress < 0.85:
            # Leap arc trajectory.
            t = progress / 0.85
            arc_x = int(x + (tx - x) * t)
            arc_y = int(y + (ty - y) * t)
            # Parabolic arc lift.
            arc_lift = int(math.sin(t * math.pi) * -50)
            arc_y += arc_lift

            # Motion blur trail (afterimages).
            for i in range(6):
                blur_t = max(0.0, t - i * 0.05)
                bx = int(x + (tx - x) * blur_t)
                by = int(y + (ty - y) * blur_t)
                by += int(math.sin(blur_t * math.pi) * -50)
                alpha = _NS_seiryukong._alpha(180 - i * 25)

                # Simplified monkey silhouette (small).
                # Body.
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fur_dark"], alpha),
                                 (bx - 4, by - 4, 8, 12))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_dark"], alpha),
                                 (bx - 3, by - 4, 6, 4))

                # Fire hair.
                for spike_i in range(3):
                    sx = bx - 2 + spike_i * 2
                    pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                     (sx, by - 8, 1, 3))

                # Staff.
                staff_end_x = bx + facing * 10
                staff_end_y = by
                pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha),
                                 (bx, by), (staff_end_x, staff_end_y), 2)
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_shine"], alpha),
                                 (staff_end_x, staff_end_y, 1, 1))

            # Leading bright glow.
            for r in range(10, 1, -1):
                alpha = _NS_seiryukong._alpha(200 * (10 - r) / 10)
                _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                           (arc_x + facing * 12, arc_y), r)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["white"],
                             (arc_x + facing * 12, arc_y, 1, 1))

            # Chevron arrows forward.
            for i in range(4):
                arrow_t = (phase * 3 + i * 0.25) % 1.0
                arrow_x = arc_x + facing * int(arrow_t * 30)
                arrow_y = arc_y
                a_alpha = _NS_seiryukong._alpha(220 * (1 - arrow_t))
                pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["fire_hot"], a_alpha),
                                 (arrow_x, arrow_y - 3),
                                 (arrow_x + facing * 3, arrow_y), 2)
                pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["fire_hot"], a_alpha),
                                 (arrow_x + facing * 3, arrow_y),
                                 (arrow_x, arrow_y + 3), 2)
        else:
            # Impact at target with stun stars.
            t = (progress - 0.85) / 0.15
            radius = int(15 + t * 25)
            alpha = _NS_seiryukong._alpha(240 * (1 - t))
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_darkest"], alpha),
                                       (tx, ty), radius + 3, 3)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha),
                                       (tx, ty), radius, 2)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                       (tx, ty), max(1, radius - 8), 1)

            # STARS spinning around target (stun effect).
            for i in range(5):
                star_angle = phase * 4 + i * math.pi * 2 / 5
                star_r = 20
                sx = tx + int(math.cos(star_angle) * star_r)
                sy = ty - 15 + int(math.sin(star_angle) * 6)

                # Star shape (cross + rotated cross).
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (sx - 1, sy, 3, 1))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (sx, sy - 1, 1, 3))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["white"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL W: TREE DANCE (agility boost + tree silhouette)
    # ============================================================
    def _draw_treedance_foreground(surface, boss, x, y, timer, phase):
        """Tree silhouette appears behind boss + speed lines."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Tree behind boss (translucent silhouette).
        tree_x = x
        tree_y = y + 5

        # Tree trunk.
        trunk_pts = [
            (tree_x - 4, tree_y + 20),
            (tree_x + 4, tree_y + 20),
            (tree_x + 3, tree_y - 15),
            (tree_x - 3, tree_y - 15),
        ]
        _NS_seiryukong._poly(surface, (*_NS_seiryukong.PALETTE["staff_dark"], 150), trunk_pts)
        _NS_seiryukong._poly(surface, (*_NS_seiryukong.PALETTE["staff_mid"], 180), [
            (tree_x - 3, tree_y + 18),
            (tree_x + 3, tree_y + 18),
            (tree_x + 2, tree_y - 14),
            (tree_x - 2, tree_y - 14),
        ])

        # Bark texture.
        for grain_y in range(tree_y - 10, tree_y + 15, 4):
            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["fur_darkest"], 200),
                             (tree_x - 2, grain_y), (tree_x + 2, grain_y), 1)

        # Tree canopy (leaves - translucent gold-green).
        canopy_alpha = 180
        canopy_r_base = 25
        for i in range(3):
            leaf_x = tree_x + (i - 1) * 8
            leaf_y = tree_y - 20 - i * 3
            canopy_r = canopy_r_base - i * 3
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["green_dark"], canopy_alpha),
                                       (leaf_x, leaf_y), canopy_r)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["green_mid"], canopy_alpha),
                                       (leaf_x, leaf_y), canopy_r - 3)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_mid"], canopy_alpha),
                                       (leaf_x, leaf_y), canopy_r - 8)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_light"], canopy_alpha),
                                       (leaf_x, leaf_y), canopy_r - 12)

        # Speed lines around boss (agility effect).
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            line_r = 30 + int(math.sin(phase * 2 + i) * 5)
            lx1 = x + int(math.cos(angle) * line_r)
            ly1 = y + int(math.sin(angle) * line_r * 0.5)
            lx2 = x + int(math.cos(angle) * (line_r + 8))
            ly2 = y + int(math.sin(angle) * (line_r + 8) * 0.5)
            pygame.draw.line(surface, _NS_seiryukong.PALETTE["gold_light"], (lx1, ly1), (lx2, ly2), 1)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (lx2, ly2, 1, 1))

        # Falling leaves.
        for i in range(6):
            t = (phase * 0.5 + i * 0.15) % 1.0
            lx = tree_x - 15 + i * 5 + int(math.sin(phase + i) * 4)
            ly = tree_y - 20 + int(t * 45)
            alpha = _NS_seiryukong._alpha(220 * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_light"], alpha),
                                 (lx - 1, ly, 3, 1))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (lx, ly, 1, 1))

    # ============================================================
    # SKILL E: JINGU MASTERY (2 soldier clones)
    # ============================================================
    def _draw_jingu_soldiers(surface, boss, x, y, timer, phase):
        """2 monkey soldier clones next to boss (mini versions)."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # 2 clones on either side.
        for i, side in enumerate([-1, 1]):
            clone_x = x + side * 28
            clone_y = y + int(math.sin(phase * 1.5 + i * math.pi) * 3)

            alpha_body = _NS_seiryukong._alpha(200)

            # Body (mini monkey with gold armor).
            # Legs.
            for leg_side in (-1, 1):
                leg_x = clone_x + leg_side * 2
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["green_dark"], alpha_body),
                                 (leg_x - 1, clone_y + 5, 2, 8))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fur_dark"], alpha_body),
                                 (leg_x - 1, clone_y + 12, 2, 3))

            # Torso.
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fur_darkest"], alpha_body),
                             (clone_x - 5, clone_y - 4, 10, 10))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fur_dark"], alpha_body),
                             (clone_x - 4, clone_y - 3, 8, 8))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fur_light"], alpha_body),
                             (clone_x - 2, clone_y - 1, 4, 5))

            # Gold armor plate.
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_dark"], alpha_body),
                             (clone_x - 3, clone_y - 3, 6, 3))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha_body),
                             (clone_x - 2, clone_y - 3, 4, 2))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_edge"], alpha_body),
                             (clone_x - 1, clone_y - 3, 2, 1))

            # Head.
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fur_dark"], alpha_body),
                             (clone_x - 3, clone_y - 11, 6, 6))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["skin_mid"], alpha_body),
                             (clone_x - 2, clone_y - 10, 4, 4))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["skin_light"], alpha_body),
                             (clone_x - 1, clone_y - 9, 2, 2))

            # Fire hair (mini).
            for spike_x_off in (-2, 0, 2):
                for h in range(3):
                    fh_color = [_NS_seiryukong.PALETTE["fire_dark"],
                                _NS_seiryukong.PALETTE["fire_mid"],
                                _NS_seiryukong.PALETTE["fire_hot"]][h]
                    pygame.draw.rect(surface, (*fh_color, alpha_body),
                                     (clone_x + spike_x_off, clone_y - 12 - h, 1, 1))

            # Small crown.
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha_body),
                             (clone_x - 3, clone_y - 10, 6, 1))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["red_mid"], alpha_body),
                             (clone_x, clone_y - 10, 1, 1))

            # Eyes.
            pulse = math.sin(phase * 2.5) * 0.3 + 0.7
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["eye_mid"], alpha_body),
                             (clone_x - 1, clone_y - 8, 1, 1))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["eye_mid"], alpha_body),
                             (clone_x + 1, clone_y - 8, 1, 1))
            alpha_glow = _NS_seiryukong._alpha(150 * pulse)
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["eye_light"], alpha_glow),
                             (clone_x - 1, clone_y - 8, 1, 1))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["eye_light"], alpha_glow),
                             (clone_x + 1, clone_y - 8, 1, 1))

            # Mini staff held out to attack.
            staff_angle = math.pi * (-0.1 if side > 0 else -0.9) + math.sin(phase * 3) * 0.2
            staff_len = 16
            staff_start_x = clone_x + side * 6
            staff_start_y = clone_y - 2
            staff_end_x = staff_start_x + int(math.cos(staff_angle) * staff_len)
            staff_end_y = staff_start_y + int(math.sin(staff_angle) * staff_len)
            staff_back_x = staff_start_x - int(math.cos(staff_angle) * 4)
            staff_back_y = staff_start_y - int(math.sin(staff_angle) * 4)

            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_dark"], alpha_body),
                             (staff_back_x, staff_back_y), (staff_end_x, staff_end_y), 2)
            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha_body),
                             (staff_back_x, staff_back_y), (staff_end_x, staff_end_y), 1)
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_edge"], alpha_body),
                             (staff_end_x, staff_end_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_shine"], alpha_body),
                             (staff_end_x, staff_end_y, 1, 1))

            # Glow around clones.
            pulse2 = math.sin(phase * 2 + i) * 0.3 + 0.7
            for r in range(10, 3, -1):
                a = _NS_seiryukong._alpha(60 * pulse2 * (10 - r) / 10)
                _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["gold_light"], a),
                                           (clone_x, clone_y), r)

    # ============================================================
    # SKILL R: WUKONG'S COMMAND (spinning staff area)
    # ============================================================
    def _draw_wukong_ground(surface, boss, x, y, timer, phase):
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # HUGE ground ring around boss.
        r = 65 + int(math.sin(phase * 2) * 3)
        alpha = _NS_seiryukong._alpha(220)
        pygame.draw.ellipse(surface, (*_NS_seiryukong.PALETTE["gold_darkest"], alpha),
                            (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_seiryukong.PALETTE["gold_dark"], alpha),
                            (x - r + 4, y + 45 - r // 3 + 3,
                             r * 2 - 8, r * 2 // 3 - 6), 3)
        pygame.draw.ellipse(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha),
                            (x - r + 10, y + 45 - r // 3 + 6,
                             r * 2 - 20, r * 2 // 3 - 12), 2)
        pygame.draw.ellipse(surface, (*_NS_seiryukong.PALETTE["gold_light"], alpha),
                            (x - r + 18, y + 45 - r // 3 + 10,
                             r * 2 - 36, r * 2 // 3 - 20), 1)

        # Runic monkey face symbols around perimeter.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            sx = x + int(math.cos(angle) * r)
            sy = y + 45 + int(math.sin(angle) * r * 0.35)
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (sx - 2, sy, 5, 1))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (sx, sy - 2, 1, 5))
            pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_shine"], (sx, sy, 1, 1))

    def _draw_wukong_foreground(surface, boss, x, y, timer, phase):
        duration = 150
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # SPINNING STAFF - draw multiple staff copies at different rotations.
        spin_speed = phase * 5

        # 3-4 staff copies rotating around boss.
        for i in range(4):
            spin_angle = spin_speed + i * math.pi / 2
            staff_len = 32
            # Staff center at boss position.
            tip1_x = x + int(math.cos(spin_angle) * staff_len)
            tip1_y = y + int(math.sin(spin_angle) * staff_len * 0.5)
            tip2_x = x - int(math.cos(spin_angle) * staff_len)
            tip2_y = y - int(math.sin(spin_angle) * staff_len * 0.5)

            # Fade based on rotation position (motion blur effect).
            alpha = _NS_seiryukong._alpha(180 - i * 30)

            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_dark"], alpha),
                             (tip1_x, tip1_y), (tip2_x, tip2_y), 3)
            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_mid"], alpha),
                             (tip1_x, tip1_y), (tip2_x, tip2_y), 2)
            pygame.draw.line(surface, (*_NS_seiryukong.PALETTE["gold_edge"], alpha),
                             (tip1_x, tip1_y - 1), (tip2_x, tip2_y - 1), 1)

            # Bright tips.
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                             (tip1_x, tip1_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                             (tip2_x, tip2_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], alpha),
                             (tip1_x, tip1_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], alpha),
                             (tip2_x, tip2_y, 1, 1))

        # Spiraling energy rings.
        num_spirals = 3
        for spiral_i in range(num_spirals):
            spiral_offset = spiral_i * (math.pi * 2 / num_spirals)
            for i in range(20):
                spiral_t = i / 20
                spiral_angle = spin_speed * 2 + spiral_offset + spiral_t * math.pi * 2
                spiral_r = 20 + spiral_t * 40
                sx = x + int(math.cos(spiral_angle) * spiral_r)
                sy = y + int(math.sin(spiral_angle) * spiral_r * 0.5)
                alpha = _NS_seiryukong._alpha(200 * (1 - spiral_t * 0.4))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["gold_light"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 1, 1))

        # Rising sparkles.
        for i in range(15):
            spark_t = (phase * 0.7 + i * 0.07) % 1.0
            sx = x - 30 + i * 4 + int(math.sin(phase + i) * 3)
            sy = y + 20 - int(spark_t * 40)
            alpha = _NS_seiryukong._alpha(220 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_seiryukong.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))

        # Wukong face symbol above boss (aura).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        face_y = y - 40
        # Simple stylized face.
        # Outline circle.
        for r in range(15, 5, -1):
            alpha = _NS_seiryukong._alpha(120 * pulse * (15 - r) / 15)
            _NS_seiryukong._aacircle(surface, (*_NS_seiryukong.PALETTE["fire_hot"], alpha),
                                       (x, face_y), r)
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["gold_dark"], (x, face_y), 8, 1)
        _NS_seiryukong._aacircle(surface, _NS_seiryukong.PALETTE["gold_light"], (x, face_y), 7, 1)

        # Fierce eyes on face.
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (x - 3, face_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (x + 2, face_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_shine"], (x - 2, face_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_shine"], (x + 2, face_y - 1, 1, 1))
        # Mouth (fierce grin).
        pygame.draw.line(surface, _NS_seiryukong.PALETTE["fire_hot"],
                         (x - 3, face_y + 3), (x + 3, face_y + 3), 1)
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (x - 2, face_y + 4, 1, 1))
        pygame.draw.rect(surface, _NS_seiryukong.PALETTE["fire_hot"], (x + 2, face_y + 4, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_ignirus(surface, boss, x, y):
    """Entry point ignirus."""
    return _NS_ignirus.draw_ignirus(surface, boss, x, y)


def draw_leoric(surface, boss, x, y):
    """Entry point leoric."""
    return _NS_leoric.draw_leoric(surface, boss, x, y)


def draw_shirotaka(surface, boss, x, y):
    """Entry point shirotaka."""
    return _NS_shirotaka.draw_shirotaka(surface, boss, x, y)


def draw_seiryukong(surface, boss, x, y):
    """Entry point seiryukong."""
    return _NS_seiryukong.draw_seiryukong(surface, boss, x, y)
