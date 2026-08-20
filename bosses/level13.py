"""
bosses/level13.py - Semua boss Level 13

Berisi:
  - kaeldris   (mini boss - Warrior Commander)
  - pyraklos   (mini boss - Spartan War Champion)
  - velmyrth   (mini boss - Phantom Assassin)
  - solvarin   (TRUE BOSS - Holy Paladin Warden)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# kaeldris.py
# ====================================================================

# ====================================================================
# KAELDRIS - THE CRIMSON VANGUARD (Mini Boss Warrior)
# ====================================================================


class _NS_kaeldris:
    """Namespace kaeldris - Mini Boss Warrior Commander."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Gold armor (main)
        "gold_darkest": (35, 22, 5),
        "gold_dark": (95, 65, 15),
        "gold_mid": (180, 130, 40),
        "gold_light": (240, 195, 85),
        "gold_shine": (255, 240, 170),
        "gold_white": (255, 255, 220),

        # Crimson cape/plume (deep red)
        "cape_darkest": (30, 5, 8),
        "cape_dark": (90, 15, 20),
        "cape_mid": (170, 30, 35),
        "cape_light": (230, 70, 65),
        "cape_edge": (255, 140, 115),

        # Skin (warrior tan)
        "skin_darkest": (60, 40, 30),
        "skin_dark": (120, 85, 65),
        "skin_mid": (185, 145, 115),
        "skin_light": (235, 200, 170),
        "skin_shine": (250, 230, 215),

        # Under-armor / leather
        "leather_dark": (25, 15, 12),
        "leather_mid": (60, 35, 25),
        "leather_light": (110, 75, 55),

        # Axe metal (steel + gold trim)
        "steel_darkest": (10, 10, 12),
        "steel_dark": (40, 40, 48),
        "steel_mid": (95, 95, 105),
        "steel_light": (170, 170, 180),
        "steel_shine": (230, 230, 235),

        # Fire/blood magic (bright orange-red glow)
        "fire_darkest": (35, 5, 0),
        "fire_dark": (120, 25, 5),
        "fire_mid": (225, 70, 15),
        "fire_light": (255, 150, 45),
        "fire_hot": (255, 210, 85),
        "fire_shine": (255, 245, 190),

        # Eye (bright amber)
        "eye_socket": (5, 3, 2),
        "eye_dark": (60, 30, 10),
        "eye_mid": (180, 110, 30),
        "eye_light": (255, 190, 80),
        "eye_glow": (255, 240, 160),

        # Shadow accents
        "shadow_red": (25, 8, 10),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaeldris._clamp(color)
        if _NS_kaeldris.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaeldris._clamp(color)
        if _NS_kaeldris.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_kaeldris._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_kaeldris._clamp(color), points)

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
    def draw_kaeldris(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaeldris._detect_moving(boss)
        _NS_kaeldris._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kae_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_kaeldris._draw_battle_aura(surface, x, y, pulse)
        _NS_kaeldris._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_kaeldris._draw_press_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaeldris._draw_duel_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaeldris._draw_moment_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_kaeldris._draw_kae_attack(surface, boss, x, y)
        elif moving:
            _NS_kaeldris._draw_kae_float(surface, boss, x, y)
        else:
            _NS_kaeldris._draw_kae_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_kaeldris._draw_overwhelming_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaeldris._draw_press_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaeldris._draw_moment_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaeldris._draw_duel_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kae_previous_timer", 0))
        active = bool(getattr(boss, "_kae_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._kae_attack_active = True
            boss._kae_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._kae_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._kae_attack_frame = int(getattr(boss, "_kae_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kae_attack_active = False
            boss._kae_attack_frame = 0
            active = False

        boss._kae_previous_timer = timer
        boss._kae_attack_progress = (
            min(1.0, getattr(boss, "_kae_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_kae_last_x"):
            boss._kae_last_x = boss.x
            boss._kae_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kae_last_x)
        dy = abs(boss.y - boss._kae_last_y)
        boss._kae_last_x = boss.x
        boss._kae_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_kae_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_kaeldris._draw_shadow(surface, x, y + 55)
        _NS_kaeldris._draw_ember_wisps(surface, x, y + 40, boss.pulse)
        _NS_kaeldris._draw_kae_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_kae_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_kaeldris._draw_shadow(surface, x + sway, y + 55)
        _NS_kaeldris._draw_ember_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_kaeldris._draw_kae_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")

    def _draw_kae_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_kae_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_kae_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Heavy axe swing: wind-up back → downward chop → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * facing
            lift = int(t * 6)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 16)) * facing
            lift = int(6 - t * 10)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * facing
            lift = int(-4 + t * 4)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_kaeldris._draw_shadow(surface, x + lunge, y + 55)
        _NS_kaeldris._draw_ember_wisps(surface, x + lunge, y + 40, boss.pulse,
                                        intense=True)
        _NS_kaeldris._draw_kae_body(surface, x + lunge, y - lift + bob,
                                     facing, boss.pulse, "attack",
                                     progress)

    # ============================================================
    # BODY
    # ============================================================
    def _draw_kae_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Roman warrior commander body."""
        # Cape behind body (flowing).
        _NS_kaeldris._draw_battle_cape(surface, cx, cy, facing, phase)

        # Lower body (armored greaves + skirt).
        _NS_kaeldris._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso (breastplate).
        _NS_kaeldris._draw_torso(surface, cx, cy, facing, phase)

        # Axe swing angle (axe default UP over shoulder, swings DOWN forward).
        axe_angle = 0
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: lean back further overhead.
                t = attack_progress / 0.35
                axe_angle = -math.pi * 0.3 * t  # tilt slightly back
            elif attack_progress < 0.6:
                # Downward chop forward (huge arc down).
                t = (attack_progress - 0.35) / 0.25
                axe_angle = -math.pi * 0.3 + math.pi * 1.3 * t  # swing down forward
            else:
                # Return to shoulder.
                t = (attack_progress - 0.6) / 0.4
                axe_angle = math.pi * 1.0 * (1 - t)  # return up

        # Back arm.
        _NS_kaeldris._draw_back_arm(surface, cx, cy - 4, facing, phase, action)

        # Head with helm + plume.
        _NS_kaeldris._draw_helmed_head(surface, cx + facing * 2, cy - 22,
                                        facing, phase, action, attack_progress)

        # Front arm holding axe.
        _NS_kaeldris._draw_axe_arm(surface, cx, cy - 4, facing, phase,
                                    action, axe_angle, attack_progress)

    def _draw_battle_cape(surface, cx, cy, facing, phase):
        """Long crimson cape."""
        wave = math.sin(phase * 0.7) * 3

        # Main cape shape.
        cape = [
            (cx - facing * 9, cy - 13),
            (cx - facing * 17 + int(wave), cy - 6),
            (cx - facing * 21 + int(wave), cy + 8),
            (cx - facing * 19 + int(wave * 0.5), cy + 22),
            (cx - facing * 13, cy + 32 + int(wave * 0.5)),
            (cx - facing * 3, cy + 34),
            (cx + facing * 3, cy + 30),
            (cx + facing * 5, cy + 14),
            (cx - facing * 2, cy - 11),
        ]
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in cape])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_darkest"], cape)
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_dark"], [
            (cx - facing * 8, cy - 12),
            (cx - facing * 16 + int(wave), cy - 5),
            (cx - facing * 20 + int(wave), cy + 7),
            (cx - facing * 18 + int(wave * 0.5), cy + 21),
            (cx - facing * 12, cy + 30 + int(wave * 0.5)),
            (cx - facing * 3, cy + 32),
            (cx + facing * 3, cy + 28),
            (cx + facing * 4, cy + 13),
            (cx - facing * 2, cy - 10),
        ])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_mid"], [
            (cx - facing * 11, cy - 7),
            (cx - facing * 16 + int(wave * 0.7), cy),
            (cx - facing * 14 + int(wave * 0.5), cy + 18),
            (cx - facing * 5, cy + 24),
            (cx - facing * 2, cy + 12),
            (cx - facing * 6, cy - 4),
        ])

        # Cape highlight (light crimson).
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_light"], [
            (cx - facing * 8, cy - 4),
            (cx - facing * 12 + int(wave * 0.5), cy + 4),
            (cx - facing * 10 + int(wave * 0.3), cy + 12),
            (cx - facing * 5, cy + 8),
        ])

        # Gold trim along cape edge.
        edge_pts = [
            (cx - facing * 17 + int(wave), cy - 6),
            (cx - facing * 21 + int(wave), cy + 8),
            (cx - facing * 19 + int(wave * 0.5), cy + 22),
            (cx - facing * 13, cy + 32 + int(wave * 0.5)),
        ]
        for i in range(len(edge_pts) - 1):
            _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                  edge_pts[i], edge_pts[i + 1], 2)
            _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                  edge_pts[i], edge_pts[i + 1], 1)

        # Vertical fold shadows.
        for i, dx in enumerate((-4, 2, 8)):
            wave_off = math.sin(phase * 0.7 + i) * 1
            offset_x = cx - facing * dx
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["cape_darkest"],
                             (offset_x, cy - 2),
                             (offset_x - facing * 3 + int(wave_off),
                              cy + 26), 1)

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Armored waist + skirt (Roman pteruges - leather strips)."""
        wave = math.sin(phase * 0.9) * 2

        # Belt/hip armor.
        hip = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 4),
            (cx - 10, cy + 4),
            (cx - 12, cy),
        ]
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hip])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_darkest"], hip)
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_dark"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5), (cx + 11, cy),
            (cx + 9, cy + 3), (cx - 9, cy + 3), (cx - 11, cy),
        ])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_mid"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3), (cx + 9, cy),
            (cx + 7, cy + 2), (cx - 7, cy + 2), (cx - 9, cy),
        ])

        # Belt buckle (gem).
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                         (cx - 3, cy - 3, 7, 6))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_dark"],
                         (cx - 2, cy - 2, 5, 5))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_dark"],
                         (cx - 1, cy - 1, 3, 3))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_mid"],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_light"],
                         (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_shine"],
                         (cx, cy - 1, 1, 1))

        # PTERUGES (leather strips hanging down like Roman skirt).
        for i, dx in enumerate((-9, -5, -1, 3, 7)):
            strip_h = 12 + int(math.sin(phase * 0.5 + i) * 1)
            wave_off = math.sin(phase * 0.6 + i * 0.4) * 1
            strip_pts = [
                (cx + dx - 2, cy + 3),
                (cx + dx + 2, cy + 3),
                (cx + dx + 2 + int(wave_off * 0.3), cy + 3 + strip_h),
                (cx + dx + int(wave_off * 0.5), cy + 5 + strip_h),
                (cx + dx - 2 + int(wave_off * 0.3), cy + 3 + strip_h),
            ]
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in strip_pts])
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["leather_dark"],
                                strip_pts)
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["leather_mid"], [
                (cx + dx - 1, cy + 4),
                (cx + dx + 1, cy + 4),
                (cx + dx + 1 + int(wave_off * 0.3), cy + 3 + strip_h - 2),
                (cx + dx - 1 + int(wave_off * 0.3), cy + 3 + strip_h - 2),
            ])
            # Gold stud at top.
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_mid"],
                             (cx + dx, cy + 4, 1, 1))
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                             (cx + dx, cy + 4, 1, 1))

        # Legs (armored greaves visible below skirt).
        for side in (-1, 1):
            lx = cx + side * 5
            ly1 = cy + 16
            ly2 = cy + 24
            # Greave (gold).
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                             (lx + 2, ly1 + 2), (lx + 2, ly2 + 2), 6)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                             (lx, ly1), (lx, ly2), 5)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_dark"],
                             (lx, ly1), (lx, ly2), 4)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_mid"],
                             (lx + side, ly1), (lx + side, ly2), 2)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_light"],
                             (lx + side, ly1), (lx + side, ly2 - 2), 1)

            # Boot at bottom.
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"], [
                (lx - 3, ly2), (lx + 3, ly2),
                (lx + 4, ly2 + 3), (lx - 4, ly2 + 3),
            ])
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["leather_dark"], [
                (lx - 2, ly2 - 1), (lx + 2, ly2 - 1),
                (lx + 3, ly2 + 2), (lx - 3, ly2 + 2),
            ])
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["leather_mid"], [
                (lx - 2, ly2), (lx + 2, ly2),
                (lx + 2, ly2 + 1), (lx - 2, ly2 + 1),
            ])

    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular gold breastplate."""
        breath = math.sin(phase * 0.7) * 1

        # Torso base (leather under-tunic).
        torso = [
            (cx - 12, cy - 14),
            (cx - 14, cy - 8),
            (cx - 13, cy),
            (cx - 11, cy + 8),
            (cx - 9, cy + 14),
            (cx + 9, cy + 14),
            (cx + 11, cy + 8),
            (cx + 13, cy),
            (cx + 14, cy - 8),
            (cx + 12, cy - 14),
        ]
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["leather_dark"], torso)
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["leather_mid"], [
            (cx - 11, cy - 13), (cx - 13, cy - 7), (cx - 12, cy),
            (cx - 10, cy + 7), (cx - 8, cy + 13),
            (cx + 8, cy + 13), (cx + 10, cy + 7), (cx + 12, cy),
            (cx + 13, cy - 7), (cx + 11, cy - 13),
        ])

        # Gold breastplate (large ornate).
        chest = [
            (cx - 11, cy - 12),
            (cx + 11, cy - 12),
            (cx + 13, cy - 4),
            (cx + 10, cy + 6),
            (cx + 5, cy + 10),
            (cx - 5, cy + 10),
            (cx - 10, cy + 6),
            (cx - 13, cy - 4),
        ]
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_darkest"], chest)
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_dark"], [
            (cx - 10, cy - 11), (cx + 10, cy - 11), (cx + 12, cy - 4),
            (cx + 9, cy + 5), (cx + 4, cy + 9), (cx - 4, cy + 9),
            (cx - 9, cy + 5), (cx - 12, cy - 4),
        ])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_mid"], [
            (cx - 8, cy - 9), (cx + 8, cy - 9), (cx + 10, cy - 3),
            (cx + 7, cy + 3), (cx + 3, cy + 7), (cx - 3, cy + 7),
            (cx - 7, cy + 3), (cx - 10, cy - 3),
        ])

        # Muscled abdomen pattern (Roman lorica musculata).
        # Chest ridges.
        pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                         (cx - 5, cy - 4), (cx + 5, cy - 4), 1)
        pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_light"],
                         (cx - 5, cy - 5), (cx + 5, cy - 5), 1)
        # Center line.
        pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                         (cx, cy - 10), (cx, cy + 5), 1)
        # Abs.
        for i in range(2):
            y_ab = cy + i * 4
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                             (cx - 5, y_ab), (cx - 1, y_ab), 1)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                             (cx + 1, y_ab), (cx + 5, y_ab), 1)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_light"],
                             (cx - 5, y_ab - 1), (cx - 1, y_ab - 1), 1)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_light"],
                             (cx + 1, y_ab - 1), (cx + 5, y_ab - 1), 1)

        # Chest highlight.
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_light"], [
            (cx + facing * 2, cy - 8),
            (cx + facing * 6, cy - 5),
            (cx + facing * 5, cy - 1),
            (cx + facing * 1, cy - 3 + int(breath)),
        ])
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (cx + facing * 4, cy - 7, 1, 1))

        # Central emblem (fire gem).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        emblem_alpha = _NS_kaeldris._alpha(240 * pulse)
        for r in range(4, 0, -1):
            alpha = _NS_kaeldris._alpha(150 * pulse * (4 - r) / 4)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["fire_mid"], alpha),
                (cx, cy - 7), r)
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_darkest"],
                         (cx - 1, cy - 8, 3, 3))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_dark"],
                         (cx - 1, cy - 8, 2, 2))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_hot"],
                         (cx, cy - 8, 1, 1))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_shine"],
                         (cx, cy - 8, 1, 1))

        # Shoulder pauldrons (gold, ornate).
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 11
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                                     (sh_x + 1, sh_y + 1), 6)
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                                     (sh_x, sh_y), 6)
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                     (sh_x, sh_y), 5)
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                     (sh_x + side, sh_y - 1), 3)
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_light"],
                                     (sh_x + side, sh_y - 1), 2)
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                             (sh_x + side, sh_y - 2, 1, 1))
            # Small ridges on pauldron (decorative).
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                             (sh_x - 2, sh_y + 2), (sh_x + 2, sh_y + 2), 1)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_light"],
                             (sh_x - 2, sh_y + 1), (sh_x + 2, sh_y + 1), 1)
            # Fire ember in pauldron.
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_mid"],
                             (sh_x, sh_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_hot"],
                             (sh_x, sh_y, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 2
        sh_x = cx - facing * 10
        sh_y = cy
        elb_x = cx - facing * 13
        elb_y = cy + 9 + int(sway)
        hand_x = cx - facing * 10
        hand_y = cy + 18

        # Upper arm (leather + gold band).
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 6)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_mid"],
                              (sh_x, sh_y), (elb_x, elb_y), 3)
        # Gold arm band.
        band_mid = ((sh_x + elb_x) // 2, (sh_y + elb_y) // 2)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                 band_mid, 3)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                 band_mid, 2)
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (band_mid[0], band_mid[1], 1, 1))

        # Forearm (gauntlet).
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 5)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 4)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 3)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_mid"],
                              (elb_x, elb_y), (hand_x, hand_y), 1)

        # Fist.
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                                 (hand_x, hand_y), 3)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                 (hand_x, hand_y), 2)

    def _draw_axe_arm(surface, cx, cy, facing, phase, action, axe_angle,
                       attack_progress):
        """Front arm holding the massive battle axe."""
        sh_x = cx + facing * 11
        sh_y = cy

        # Arm position based on axe angle.
        arm_base = -math.pi * 0.2 + axe_angle * 0.4
        elb_x = sh_x + int(math.cos(arm_base) * 10) * facing
        elb_y = sh_y + int(math.sin(arm_base) * 10) + 4

        grip_angle = arm_base + axe_angle * 0.5
        hand_x = elb_x + int(math.cos(grip_angle) * 11) * facing
        hand_y = elb_y + int(math.sin(grip_angle) * 11)

        # Upper arm (leather).
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 7)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_mid"],
                              (sh_x, sh_y), (elb_x, elb_y), 4)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["skin_dark"],
                              (sh_x + facing, sh_y - 1),
                              (elb_x + facing, elb_y - 1), 2)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["skin_mid"],
                              (sh_x + facing, sh_y - 2),
                              (elb_x + facing, elb_y - 2), 1)

        # Gold arm band.
        band_mid = ((sh_x + elb_x) // 2, (sh_y + elb_y) // 2)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                 band_mid, 3)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                 band_mid, 2)
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (band_mid[0], band_mid[1], 1, 1))

        # Forearm (gauntlet).
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 7)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 6)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_mid"],
                              (elb_x, elb_y), (hand_x, hand_y), 2)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["gold_light"],
                              (elb_x + facing, elb_y - 1),
                              (hand_x + facing, hand_y - 1), 1)

        # Fist (gauntlet).
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                                 (hand_x, hand_y), 5)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                 (hand_x, hand_y), 4)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                 (hand_x, hand_y - 1), 3)
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (hand_x, hand_y - 1, 1, 1))

        # Draw the battle axe.
        _NS_kaeldris._draw_battle_axe(surface, hand_x, hand_y, facing, phase,
                                       axe_angle, action, attack_progress)

    def _draw_battle_axe(surface, hx, hy, facing, phase, angle, action,
                          attack_progress):
        """Massive double-bladed battle axe."""
        # Axe head points based on angle.
        base_angle = -math.pi * 0.5 + angle  # default UP (over shoulder)

        shaft_len = 38
        # Direction.
        dx = math.cos(base_angle) * facing
        dy = math.sin(base_angle)

        # Butt (below hand).
        butt_x = hx - int(dx * 8)
        butt_y = hy - int(dy * 8)

        # Axe head position (top of shaft).
        head_x = hx + int(dx * shaft_len)
        head_y = hy + int(dy * shaft_len)

        # Perpendicular.
        perp_x = -math.sin(base_angle) * facing
        perp_y = math.cos(base_angle)

        # Shadow shaft.
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                              (butt_x + 2, butt_y + 2),
                              (head_x + 2, head_y + 2), 4)
        # Shaft (dark wood + steel).
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_dark"],
                              (butt_x, butt_y), (head_x, head_y), 3)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_mid"],
                              (butt_x, butt_y), (head_x, head_y), 2)
        _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["leather_light"],
                              (butt_x, butt_y), (head_x, head_y), 1)

        # Grip wraps.
        for i in range(1, 5):
            t = i / 5
            wx = int(butt_x + (head_x - butt_x) * t)
            wy = int(butt_y + (head_y - butt_y) * t)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_dark"],
                             (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                             (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)

        # Pommel/butt cap (gold).
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                 (butt_x, butt_y), 3)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                 (butt_x, butt_y), 2)
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (butt_x, butt_y, 1, 1))

        # AXE HEAD (double-bladed, crescent shape on both sides).
        # Central hub at head position.
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                                 (head_x + 1, head_y + 1), 5)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["steel_darkest"],
                                 (head_x, head_y), 5)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["steel_dark"],
                                 (head_x, head_y), 4)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_dark"],
                                 (head_x, head_y), 3)
        _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_mid"],
                                 (head_x, head_y), 2)
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (head_x, head_y, 1, 1))

        # Two crescent blades (one on each side of head).
        for blade_side in (-1, 1):
            # Blade tip (outward).
            tip_x = head_x + int(perp_x * blade_side * 14)
            tip_y = head_y + int(perp_y * blade_side * 14)

            # Blade curves upward toward shaft direction.
            curve_x = head_x + int(perp_x * blade_side * 8) + int(dx * 6)
            curve_y = head_y + int(perp_y * blade_side * 8) + int(dy * 6)

            # Blade back curves other direction.
            back_x = head_x + int(perp_x * blade_side * 8) - int(dx * 6)
            back_y = head_y + int(perp_y * blade_side * 8) - int(dy * 6)

            # Inner base points near hub.
            inner_top = (head_x + int(perp_x * blade_side * 4) + int(dx * 3),
                         head_y + int(perp_y * blade_side * 4) + int(dy * 3))
            inner_bot = (head_x + int(perp_x * blade_side * 4) - int(dx * 3),
                         head_y + int(perp_y * blade_side * 4) - int(dy * 3))

            blade_pts = [
                inner_top, curve_x_y := (curve_x, curve_y),
                (tip_x, tip_y), (back_x, back_y), inner_bot,
            ]

            # Shadow.
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                                [(p[0] + 2, p[1] + 2) for p in blade_pts])
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["steel_darkest"],
                                blade_pts)
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["steel_dark"], [
                (int(inner_top[0] * 0.85 + head_x * 0.15),
                 int(inner_top[1] * 0.85 + head_y * 0.15)),
                (int(curve_x * 0.9 + head_x * 0.1),
                 int(curve_y * 0.9 + head_y * 0.1)),
                (int(tip_x * 0.92 + head_x * 0.08),
                 int(tip_y * 0.92 + head_y * 0.08)),
                (int(back_x * 0.9 + head_x * 0.1),
                 int(back_y * 0.9 + head_y * 0.1)),
                (int(inner_bot[0] * 0.85 + head_x * 0.15),
                 int(inner_bot[1] * 0.85 + head_y * 0.15)),
            ])
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["steel_mid"], [
                (int(inner_top[0] * 0.6 + head_x * 0.4),
                 int(inner_top[1] * 0.6 + head_y * 0.4)),
                (int(curve_x * 0.75 + head_x * 0.25),
                 int(curve_y * 0.75 + head_y * 0.25)),
                (int(tip_x * 0.8 + head_x * 0.2),
                 int(tip_y * 0.8 + head_y * 0.2)),
                (int(back_x * 0.75 + head_x * 0.25),
                 int(back_y * 0.75 + head_y * 0.25)),
                (int(inner_bot[0] * 0.6 + head_x * 0.4),
                 int(inner_bot[1] * 0.6 + head_y * 0.4)),
            ])

            # Edge highlight (bright).
            _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["steel_light"],
                                  (curve_x, curve_y), (tip_x, tip_y), 1)
            _NS_kaeldris._aaline(surface, _NS_kaeldris.PALETTE["steel_shine"],
                                  (curve_x, curve_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))

            # Fire ember on blade (flavor).
            pulse = math.sin(phase * 2 + blade_side) * 0.3 + 0.7
            ember_alpha = _NS_kaeldris._alpha(200 * pulse)
            ember_x = int(head_x + (tip_x - head_x) * 0.4)
            ember_y = int(head_y + (tip_y - head_y) * 0.4)
            for r in range(3, 0, -1):
                alpha = _NS_kaeldris._alpha(ember_alpha * (3 - r) / 3)
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_mid"], alpha),
                    (ember_x, ember_y), r)
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_hot"],
                             (ember_x, ember_y, 1, 1))

        # Spike on top of axe head (thrusting spike).
        spike_tip_x = head_x + int(dx * 8)
        spike_tip_y = head_y + int(dy * 8)
        spike_a = (head_x + int(perp_x * 2), head_y + int(perp_y * 2))
        spike_b = (head_x - int(perp_x * 2), head_y - int(perp_y * 2))
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"], [
            (spike_tip_x + 1, spike_tip_y + 1),
            (spike_a[0] + 1, spike_a[1] + 1),
            (spike_b[0] + 1, spike_b[1] + 1),
        ])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["steel_darkest"],
                            [(spike_tip_x, spike_tip_y), spike_a, spike_b])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["steel_dark"], [
            (spike_tip_x, spike_tip_y),
            (int((spike_tip_x + spike_a[0]) / 2),
             int((spike_tip_y + spike_a[1]) / 2)),
            (head_x, head_y),
        ])
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["steel_light"],
                         (spike_tip_x, spike_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["steel_shine"],
                         (spike_tip_x, spike_tip_y, 1, 1))

        # Swing streak during attack (arc of fire).
        if action == "attack" and 0.35 < attack_progress < 0.7:
            streak_intensity = math.sin((attack_progress - 0.35) / 0.35 * math.pi)
            streak_alpha = _NS_kaeldris._alpha(230 * streak_intensity)

            arc_start = base_angle - 0.4
            arc_end = base_angle
            for i in range(8):
                arc_t = i / 8
                trail_angle = arc_start + (arc_end - arc_start) * arc_t
                trail_dx = math.cos(trail_angle) * facing
                trail_dy = math.sin(trail_angle)
                trail_len = shaft_len + 10
                trail_x = hx + int(trail_dx * trail_len)
                trail_y = hy + int(trail_dy * trail_len)

                alpha_t = _NS_kaeldris._alpha(streak_alpha * (1 - arc_t) * 0.8)
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha_t),
                    (trail_x, trail_y), 5)
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_mid"], alpha_t),
                    (trail_x, trail_y), 3)
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_hot"], alpha_t),
                    (trail_x, trail_y), 1)

    def _draw_helmed_head(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Roman helmet with red horsehair plume."""
        # HELMET (gold with face guard).
        _NS_kaeldris._draw_helm(surface, cx, cy, facing, phase)

        # PLUME (red horsehair crest on top).
        _NS_kaeldris._draw_plume(surface, cx, cy, facing, phase)

        # EYE GLOW through helm slit.
        _NS_kaeldris._draw_helm_eye(surface, cx + facing * 2, cy - 3,
                                     facing, phase, action, attack_progress)

    def _draw_helm(surface, cx, cy, facing, phase):
        """Gold Roman helmet."""
        # Helmet dome shape.
        helm = [
            (cx - 8, cy + 5),
            (cx - 10, cy - 1),
            (cx - 9, cy - 8),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 9, cy - 8),
            (cx + 10, cy - 1),
            (cx + 8, cy + 5),
            (cx + 6, cy + 8),
            (cx - 6, cy + 8),
        ]
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in helm])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_darkest"], helm)
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_dark"], [
            (cx - 7, cy + 4), (cx - 9, cy - 1), (cx - 8, cy - 7),
            (cx - 3, cy - 11), (cx + 3, cy - 11), (cx + 8, cy - 7),
            (cx + 9, cy - 1), (cx + 7, cy + 4),
            (cx + 5, cy + 7), (cx - 5, cy + 7),
        ])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_mid"], [
            (cx - 6, cy - 3), (cx - 8, cy - 6), (cx - 6, cy - 10),
            (cx - 2, cy - 11), (cx + 2, cy - 11), (cx + 6, cy - 10),
            (cx + 8, cy - 6), (cx + 6, cy - 3),
        ])

        # Highlight (top-facing side).
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_light"], [
            (cx + facing * 2, cy - 9),
            (cx + facing * 6, cy - 6),
            (cx + facing * 5, cy - 2),
            (cx + facing * 1, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (cx + facing * 5, cy - 7, 1, 1))

        # Face guard (T-shape slit).
        # Vertical bar down center.
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                         (cx - 1, cy - 6, 3, 10))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                         (cx - 1, cy - 6, 2, 10))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_dark"],
                         (cx - 1, cy - 6, 1, 10))
        # Eye slit (horizontal opening).
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                         (cx - 6, cy - 4, 12, 3))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["eye_socket"],
                         (cx - 5, cy - 3, 10, 2))

        # Cheek guards (side panels).
        for side in (-1, 1):
            cheek_pts = [
                (cx + side * 6, cy - 2),
                (cx + side * 9, cy),
                (cx + side * 8, cy + 5),
                (cx + side * 4, cy + 7),
            ]
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                                cheek_pts)
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_dark"], [
                (cx + side * 5, cy - 1),
                (cx + side * 8, cy + 1),
                (cx + side * 7, cy + 5),
                (cx + side * 4, cy + 6),
            ])
            _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["gold_mid"], [
                (cx + side * 6, cy + 2),
                (cx + side * 7, cy + 4),
                (cx + side * 5, cy + 5),
            ])
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_light"],
                             (cx + side * 7, cy + 2, 1, 1))

        # Helm rim/band (bottom edge decoration).
        pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_darkest"],
                         (cx - 8, cy + 5), (cx + 8, cy + 5), 1)
        pygame.draw.line(surface, _NS_kaeldris.PALETTE["gold_shine"],
                         (cx - 7, cy + 4), (cx + 7, cy + 4), 1)

    def _draw_plume(surface, cx, cy, facing, phase):
        """Red horsehair plume on top of helmet."""
        wave = math.sin(phase * 0.8) * 2

        # Plume base (attached to helm top).
        base_x = cx
        base_y = cy - 12

        # Plume shape (arching backward).
        plume = [
            (cx - facing * 2, cy - 11),
            (cx + facing * 2, cy - 12),
            (cx - facing * 3, cy - 18 + int(wave)),
            (cx - facing * 8, cy - 20 + int(wave)),
            (cx - facing * 12, cy - 16 + int(wave * 0.5)),
            (cx - facing * 13, cy - 10),
            (cx - facing * 10, cy - 8),
            (cx - facing * 5, cy - 10),
        ]
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in plume])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_darkest"], plume)
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_dark"], [
            (cx - facing * 1, cy - 11),
            (cx + facing * 1, cy - 11),
            (cx - facing * 3, cy - 17 + int(wave)),
            (cx - facing * 7, cy - 19 + int(wave)),
            (cx - facing * 11, cy - 15 + int(wave * 0.5)),
            (cx - facing * 12, cy - 10),
            (cx - facing * 8, cy - 9),
            (cx - facing * 4, cy - 10),
        ])
        _NS_kaeldris._poly(surface, _NS_kaeldris.PALETTE["cape_mid"], [
            (cx, cy - 11),
            (cx - facing * 4, cy - 16 + int(wave)),
            (cx - facing * 8, cy - 17 + int(wave)),
            (cx - facing * 10, cy - 13),
            (cx - facing * 6, cy - 11),
        ])

        # Highlight strands.
        for i in range(3):
            strand_off = i * 2
            wave_off = math.sin(phase * 0.8 + i * 0.5) * 1
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["cape_light"],
                             (cx - facing * (strand_off + 2), cy - 11),
                             (cx - facing * (strand_off + 5),
                              cy - 16 + int(wave_off)), 1)
            pygame.draw.line(surface, _NS_kaeldris.PALETTE["cape_edge"],
                             (cx - facing * (strand_off + 6),
                              cy - 15 + int(wave_off)),
                             (cx - facing * (strand_off + 9),
                              cy - 12), 1)

        # Bright tip highlights.
        for i in range(2):
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["cape_edge"],
                             (cx - facing * (8 + i * 2),
                              cy - 19 + int(wave), 1, 1))

    def _draw_helm_eye(surface, cx, cy, facing, phase, action, attack_progress):
        """Amber eye glow through helm slit."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        if action == "attack" and attack_progress > 0.2:
            pulse = min(1.0, pulse + 0.4)

        ex = cx
        ey = cy

        # Halo glow.
        for radius in range(4, 0, -1):
            alpha = _NS_kaeldris._alpha(150 * (4 - radius) / 4 * pulse)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["eye_mid"], alpha),
                (ex, ey), radius)

        # Eye slit glow (horizontal).
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["eye_dark"],
                         (ex - 1, ey, 3, 1))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["eye_mid"],
                         (ex - 1, ey, 2, 1))
        pygame.draw.rect(surface, _NS_kaeldris.PALETTE["eye_light"],
                         (ex, ey, 1, 1))
        if pulse > 0.85:
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 1, 2, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (45, 15, 12, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_battle_aura(surface, x, y, phase):
        """Fire/crimson battle aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_kaeldris._alpha((85 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kaeldris._aacircle(aura,
                    (*_NS_kaeldris.PALETTE["fire_darkest"], alpha),
                    (110, 100), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_kaeldris._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaeldris._aacircle(aura,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                    (110, 100), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_kaeldris._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaeldris._aacircle(aura,
                    (*_NS_kaeldris.PALETTE["cape_dark"], alpha),
                    (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Floating gold + fire particles.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = (_NS_kaeldris.PALETTE["fire_mid"] if i % 2 == 0
                     else _NS_kaeldris.PALETTE["gold_mid"])
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Battle-themed ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaeldris.PALETTE["fire_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_kaeldris.PALETTE["fire_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_kaeldris.PALETTE["gold_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_kaeldris.PALETTE["cape_dark"], 180),
                            (40, 24, 90, 14), 1)

        # Sword-mark runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_kaeldris.PALETTE["fire_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_kaeldris.PALETTE["fire_hot"],
                 _NS_kaeldris._alpha(150 * pulse)),
                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    def _draw_ember_wisps(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Fire ember wisps."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_kaeldris._alpha((30 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_kaeldris.PALETTE["fire_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_kaeldris._alpha((20 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_kaeldris._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["fire_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["fire_hot"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["fire_shine"], alpha),
                (sx, sy - 1, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kaeldris._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_darkest"], alpha),
                    (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface,
                    (*_NS_kaeldris.PALETTE["fire_mid"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_kaeldris.PALETTE["fire_hot"], alpha),
                    (sx, sy, 1, 1))

    # ============================================================
    # SKILL: Q - OVERWHELMING ODDS (arrow burst forward)
    # ============================================================
    def _draw_overwhelming_skill(surface, boss, x, y, timer, phase):
        """Chaotic burst: fire arrows/spears radiating outward toward target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaeldris._target_position(boss, x, y)

        if progress < 0.25:
            # Wind-up: gather energy at chest.
            t = progress / 0.25
            chest_x = x
            chest_y = y - 8
            cr = int(4 + t * 10)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kaeldris._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                    (chest_x, chest_y), r)
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["fire_mid"],
                                     (chest_x, chest_y), max(1, cr - 2))
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["fire_light"],
                                     (chest_x, chest_y), max(1, cr - 4))
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["fire_shine"],
                                     (chest_x, chest_y), max(1, cr - 6))
        else:
            # Burst of arrows/projectiles forward.
            t = (progress - 0.25) / 0.75

            # Draw target area burst (glowing on target).
            target_r = int(30 + t * 15)
            target_alpha = _NS_kaeldris._alpha(180 * (1 - t * 0.5))
            for r in range(target_r + 3, 5, -3):
                alpha = _NS_kaeldris._alpha(target_alpha * (target_r + 3 - r) / (target_r + 3))
                pygame.draw.ellipse(surface,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                    (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)

            # Multiple arrows flying to target area.
            num_arrows = 8
            for i in range(num_arrows):
                arrow_delay = i * 0.06
                arrow_t = max(0.0, t - arrow_delay)
                if arrow_t <= 0 or arrow_t > 1:
                    continue

                # Slight spread on target.
                spread_offset_x = math.sin(i * 2.1) * 20
                spread_offset_y = math.cos(i * 1.7) * 12
                target_x = tx + int(spread_offset_x)
                target_y = ty + int(spread_offset_y)

                start_x = x + facing * 20
                start_y = y - 10
                ax = int(start_x + (target_x - start_x) * arrow_t)
                ay = int(start_y + (target_y - start_y) * arrow_t)

                # Arrow direction.
                dx_a = target_x - start_x
                dy_a = target_y - start_y
                length = max(1, math.sqrt(dx_a ** 2 + dy_a ** 2))
                ux = dx_a / length
                uy = dy_a / length

                # Arrow shape (line + arrow head).
                arrow_back_x = ax - int(ux * 6)
                arrow_back_y = ay - int(uy * 6)
                arrow_tip_x = ax + int(ux * 4)
                arrow_tip_y = ay + int(uy * 4)

                # Trail.
                for tr in range(4):
                    tr_t = arrow_t - tr * 0.03
                    if tr_t <= 0:
                        continue
                    tpx = int(start_x + (target_x - start_x) * tr_t)
                    tpy = int(start_y + (target_y - start_y) * tr_t)
                    trail_alpha = _NS_kaeldris._alpha(200 - tr * 40)
                    _NS_kaeldris._aacircle(surface,
                        (*_NS_kaeldris.PALETTE["fire_mid"], trail_alpha),
                        (tpx, tpy), max(1, 3 - tr))

                # Arrow body.
                pygame.draw.line(surface, _NS_kaeldris.PALETTE["fire_darkest"],
                                 (arrow_back_x, arrow_back_y),
                                 (arrow_tip_x, arrow_tip_y), 2)
                pygame.draw.line(surface, _NS_kaeldris.PALETTE["fire_mid"],
                                 (arrow_back_x, arrow_back_y),
                                 (arrow_tip_x, arrow_tip_y), 1)
                pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_hot"],
                                 (arrow_tip_x, arrow_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kaeldris.PALETTE["fire_shine"],
                                 (arrow_tip_x, arrow_tip_y, 1, 1))

            # Impact bursts at target when arrows arrive.
            if t > 0.6:
                st = (t - 0.6) / 0.4
                for i in range(6):
                    burst_delay = i * 0.05
                    burst_t = max(0.0, st - burst_delay)
                    if burst_t <= 0:
                        continue
                    burst_x = tx + int(math.sin(i * 2.3) * 15)
                    burst_y = ty + int(math.cos(i * 1.9) * 10)
                    burst_r = int(4 + burst_t * 12)
                    burst_alpha = _NS_kaeldris._alpha(240 * (1 - burst_t))
                    _NS_kaeldris._aacircle(surface,
                        (*_NS_kaeldris.PALETTE["fire_dark"], burst_alpha),
                        (burst_x, burst_y), burst_r, 2)
                    _NS_kaeldris._aacircle(surface,
                        (*_NS_kaeldris.PALETTE["fire_mid"], burst_alpha),
                        (burst_x, burst_y), max(1, burst_r - 2), 1)
                    _NS_kaeldris._aacircle(surface,
                        (*_NS_kaeldris.PALETTE["fire_hot"], burst_alpha),
                        (burst_x, burst_y), max(1, burst_r - 4))

    # ============================================================
    # SKILL: W - PRESS THE ATTACK (buff aura on boss)
    # ============================================================
    def _draw_press_ground(surface, boss, x, y, timer, phase):
        """Gold radiant rings under boss."""
        for i in range(3):
            r = int(30 + i * 6 + math.sin(phase * 2 + i) * 2)
            alpha = _NS_kaeldris._alpha(200 - i * 50)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["gold_mid"], alpha),
                (x, y + 40), r, 2)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["gold_light"], alpha),
                (x, y + 40), r, 1)

    def _draw_press_foreground(surface, boss, x, y, timer, phase):
        """Rising gold light pillars around boss + heal effect."""
        # Gold pillars rising up around boss.
        num_pillars = 6
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars + phase * 0.15
            px = x + int(math.cos(angle) * 40)
            py_base = y + 40 + int(math.sin(angle) * 12)

            pillar_h = 45
            for layer_i, (width, alpha_val) in enumerate([
                (5, 80), (3, 130), (2, 180), (1, 220),
            ]):
                actual_alpha = _NS_kaeldris._alpha(alpha_val)
                colors = [
                    _NS_kaeldris.PALETTE["gold_dark"],
                    _NS_kaeldris.PALETTE["gold_mid"],
                    _NS_kaeldris.PALETTE["gold_light"],
                    _NS_kaeldris.PALETTE["gold_shine"],
                ]
                color = colors[min(layer_i, 3)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (px - width // 2, py_base - pillar_h,
                                  width, pillar_h))

            # Bright top.
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["gold_shine"],
                                     (px, py_base - pillar_h), 2)
            pygame.draw.rect(surface, _NS_kaeldris.PALETTE["gold_white"],
                             (px, py_base - pillar_h, 1, 1))

        # Rising sparkles.
        for i in range(12):
            spark_t = (phase * 0.6 + i * 0.1) % 1.0
            sr = 45
            angle = i * math.pi / 6 + phase * 0.3
            sx = x + int(math.cos(angle) * sr)
            sy = y + 30 - int(spark_t * 40)
            alpha = _NS_kaeldris._alpha(230 * (1 - spark_t))
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["gold_light"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["gold_shine"], alpha), (sx, sy, 1, 1))

        # Heart-shape or plus indicating heal (float above boss).
        heal_bob = int(math.sin(phase * 1.5) * 3)
        heal_y = y - 40 + heal_bob
        heal_alpha = _NS_kaeldris._alpha(220 + math.sin(phase * 2) * 30)
        # Plus symbol.
        pygame.draw.rect(surface,
            (*_NS_kaeldris.PALETTE["gold_shine"], heal_alpha),
            (x - 1, heal_y - 4, 3, 9))
        pygame.draw.rect(surface,
            (*_NS_kaeldris.PALETTE["gold_shine"], heal_alpha),
            (x - 4, heal_y - 1, 9, 3))
        pygame.draw.rect(surface,
            (*_NS_kaeldris.PALETTE["white"], heal_alpha),
            (x, heal_y, 1, 1))

    # ============================================================
    # SKILL: E - MOMENT OF COURAGE (counter attack burst)
    # ============================================================
    def _draw_moment_ground(surface, boss, x, y, timer, phase):
        """Fire flash under boss."""
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(28 + i * 6 + math.sin(phase * 3) * 3)
            alpha = _NS_kaeldris._alpha(220 - i * 60)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["fire_mid"], alpha),
                (x, y + 40), r, 2)

    def _draw_moment_foreground(surface, boss, x, y, timer, phase):
        """Sharp fire flash + counter slash."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge (flash gathers).
            t = progress / 0.3
            flash_r = int(6 + t * 8)
            flash_x = x + facing * 15
            flash_y = y - 10
            for r in range(flash_r + 3, 0, -1):
                alpha = _NS_kaeldris._alpha(220 * (flash_r + 3 - r) / (flash_r + 3))
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                    (flash_x, flash_y), r)
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["fire_mid"],
                                     (flash_x, flash_y), max(1, flash_r - 2))
            _NS_kaeldris._aacircle(surface, _NS_kaeldris.PALETTE["fire_shine"],
                                     (flash_x, flash_y), max(1, flash_r - 4))
        else:
            # Sharp forward slash flash.
            t = (progress - 0.3) / 0.7
            intensity = math.sin(t * math.pi)

            # Star-burst flash.
            burst_x = x + facing * 35
            burst_y = y - 10
            burst_r = int(15 + t * 20)
            burst_alpha = _NS_kaeldris._alpha(255 * intensity)

            # Big glow.
            for r in range(burst_r + 4, 0, -2):
                alpha = _NS_kaeldris._alpha(burst_alpha * (burst_r + 4 - r) / (burst_r + 4))
                _NS_kaeldris._aacircle(surface,
                    (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                    (burst_x, burst_y), r)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["fire_mid"], burst_alpha),
                (burst_x, burst_y), burst_r // 2)
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["fire_light"], burst_alpha),
                (burst_x, burst_y), max(1, burst_r // 3))
            _NS_kaeldris._aacircle(surface,
                (*_NS_kaeldris.PALETTE["fire_shine"], burst_alpha),
                (burst_x, burst_y), max(1, burst_r // 5))
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["white"], burst_alpha),
                (burst_x, burst_y, 2, 2))

            # 4-point star burst lines.
            for angle_i in range(8):
                angle = angle_i * math.pi / 4
                line_len = burst_r + 8
                lx = burst_x + int(math.cos(angle) * line_len)
                ly = burst_y + int(math.sin(angle) * line_len)
                pygame.draw.line(surface,
                    (*_NS_kaeldris.PALETTE["fire_light"], burst_alpha),
                    (burst_x, burst_y), (lx, ly), 2)
                pygame.draw.line(surface,
                    (*_NS_kaeldris.PALETTE["fire_shine"], burst_alpha),
                    (burst_x, burst_y), (lx, ly), 1)
                pygame.draw.rect(surface,
                    (*_NS_kaeldris.PALETTE["white"], burst_alpha),
                    (lx, ly, 1, 1))

    # ============================================================
    # SKILL: R - DUEL (arena ring around boss + target)
    # ============================================================
    def _draw_duel_ground(surface, boss, x, y, timer, phase):
        """Arena ring on ground encompassing boss + target."""
        tx, ty = _NS_kaeldris._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Center is midpoint between boss and target.
        cx = (x + tx) // 2
        cy = (y + ty) // 2 + 30

        # Arena radius (large enough to encompass both).
        dist = max(80, math.sqrt((tx - x) ** 2 + (ty - y) ** 2) // 2 + 50)
        r = int(dist)

        if progress < 0.3:
            # Ring appears.
            t = progress / 0.3
            r_now = int(r * t)
            alpha = _NS_kaeldris._alpha(200 * t)
            pygame.draw.ellipse(surface,
                (*_NS_kaeldris.PALETTE["fire_darkest"], alpha),
                (cx - r_now, cy - r_now // 3, r_now * 2, r_now * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                (*_NS_kaeldris.PALETTE["fire_dark"], alpha),
                (cx - r_now + 3, cy - r_now // 3 + 2,
                 r_now * 2 - 6, r_now * 2 // 3 - 4), 2)
        else:
            # Sustained arena.
            t = (progress - 0.3) / 0.7
            pulse_r = int(math.sin(phase * 3) * 3)
            r_now = r + pulse_r

            alpha = _NS_kaeldris._alpha(220 * (1 - t * 0.3))
            for i in range(3):
                arc_r = r_now - i * 5
                if arc_r < 5:
                    continue
                arc_alpha = _NS_kaeldris._alpha(alpha * (1 - i * 0.3))
                pygame.draw.ellipse(surface,
                    (*_NS_kaeldris.PALETTE["fire_dark"], arc_alpha),
                    (cx - arc_r, cy - arc_r // 3,
                     arc_r * 2, arc_r * 2 // 3), 3 - i)
                pygame.draw.ellipse(surface,
                    (*_NS_kaeldris.PALETTE["fire_mid"], arc_alpha),
                    (cx - arc_r + 2, cy - arc_r // 3 + 1,
                     arc_r * 2 - 4, arc_r * 2 // 3 - 2), 2 - i if i < 2 else 1)

            # Vertical fire pillars around ring.
            num_pillars = 10
            for i in range(num_pillars):
                angle = i * math.pi * 2 / num_pillars + phase * 0.15
                px = cx + int(math.cos(angle) * r_now)
                py = cy + int(math.sin(angle) * r_now * 0.4)
                # Small vertical fire tick.
                for layer_i, (width, alpha_val) in enumerate([
                    (3, 80), (2, 130), (1, 200),
                ]):
                    pygame.draw.rect(surface,
                        (*_NS_kaeldris.PALETTE["fire_mid"], alpha_val),
                        (px - width // 2, py - 12,
                         width, 12))
                pygame.draw.rect(surface,
                    _NS_kaeldris.PALETTE["fire_hot"], (px, py - 12, 1, 1))
                pygame.draw.rect(surface,
                    _NS_kaeldris.PALETTE["fire_shine"], (px, py - 12, 1, 1))

    def _draw_duel_foreground(surface, boss, x, y, timer, phase):
        """Fire pillar effects + connecting fire beam between boss and target."""
        tx, ty = _NS_kaeldris._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up: pillars forming.
            pass  # ground handles it
        else:
            # Sustained: connecting fire tether between boss and target.
            t = (progress - 0.3) / 0.7
            intensity = min(1.0, t * 3) * (1 - t * 0.3)

            # Beam pulsing between boss chest and target.
            beam_alpha = _NS_kaeldris._alpha(180 * intensity)
            beam_pulse = math.sin(phase * 3) * 0.3 + 0.7

            # Multiple layers.
            for width, alpha_mult in [(5, 0.4), (3, 0.7), (1, 1.0)]:
                pygame.draw.line(surface,
                    (*_NS_kaeldris.PALETTE["fire_mid"],
                     _NS_kaeldris._alpha(beam_alpha * alpha_mult * beam_pulse)),
                    (x, y - 8), (tx, ty), width)

            # Central bright core.
            pygame.draw.line(surface,
                (*_NS_kaeldris.PALETTE["fire_shine"], beam_alpha),
                (x, y - 8), (tx, ty), 1)

            # Sparks along beam.
            for i in range(10):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                sx = int(x + (tx - x) * spark_t)
                sy = int(y - 8 + (ty - (y - 8)) * spark_t)
                sy += int(math.sin(phase * 5 + i) * 3)
                spark_alpha = _NS_kaeldris._alpha(240 * intensity * (1 - spark_t * 0.3))
                pygame.draw.rect(surface,
                    (*_NS_kaeldris.PALETTE["fire_hot"], spark_alpha),
                    (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_kaeldris.PALETTE["fire_shine"], spark_alpha),
                    (sx, sy, 1, 1))

            # "DUEL" indicator - crossed swords icon above center.
            mid_x = (x + tx) // 2
            mid_y = min(y, ty) - 50
            icon_alpha = _NS_kaeldris._alpha(230)
            # Two crossed sword lines.
            pygame.draw.line(surface,
                (*_NS_kaeldris.PALETTE["steel_light"], icon_alpha),
                (mid_x - 6, mid_y - 5), (mid_x + 6, mid_y + 5), 2)
            pygame.draw.line(surface,
                (*_NS_kaeldris.PALETTE["steel_light"], icon_alpha),
                (mid_x + 6, mid_y - 5), (mid_x - 6, mid_y + 5), 2)
            # Highlight.
            pygame.draw.line(surface,
                (*_NS_kaeldris.PALETTE["steel_shine"], icon_alpha),
                (mid_x - 5, mid_y - 4), (mid_x + 5, mid_y + 4), 1)
            pygame.draw.line(surface,
                (*_NS_kaeldris.PALETTE["steel_shine"], icon_alpha),
                (mid_x + 5, mid_y - 4), (mid_x - 5, mid_y + 4), 1)
            # Center gem.
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["fire_hot"], icon_alpha),
                (mid_x - 1, mid_y - 1, 3, 3))
            pygame.draw.rect(surface,
                (*_NS_kaeldris.PALETTE["fire_shine"], icon_alpha),
                (mid_x, mid_y, 1, 1))


# ====================================================================
# pyraklos.py
# ====================================================================

# ====================================================================
# PYRAKLOS - THE EMBER CHAMPION (Mini Boss Spartan Warrior)
# ====================================================================


class _NS_pyraklos:
    """Namespace pyraklos - Mini Boss Spartan War Champion."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Gold armor (main)
        "gold_darkest": (35, 22, 5),
        "gold_dark": (95, 65, 15),
        "gold_mid": (185, 140, 45),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 175),
        "gold_white": (255, 255, 225),

        # Crimson (cape, plume, under-tunic)
        "crimson_darkest": (30, 5, 8),
        "crimson_dark": (95, 15, 22),
        "crimson_mid": (175, 35, 40),
        "crimson_light": (235, 75, 65),
        "crimson_edge": (255, 145, 115),

        # Skin (warrior tan, sun-scorched)
        "skin_darkest": (55, 35, 25),
        "skin_dark": (115, 80, 55),
        "skin_mid": (180, 140, 105),
        "skin_light": (230, 195, 160),
        "skin_shine": (250, 230, 210),

        # Under-armor / leather
        "leather_dark": (25, 15, 10),
        "leather_mid": (60, 35, 22),
        "leather_light": (110, 75, 50),

        # Steel (spear tip)
        "steel_darkest": (12, 10, 15),
        "steel_dark": (45, 42, 50),
        "steel_mid": (100, 98, 108),
        "steel_light": (175, 172, 182),
        "steel_shine": (235, 232, 240),

        # Bronze (spear shaft accents)
        "bronze_dark": (70, 40, 15),
        "bronze_mid": (140, 90, 35),
        "bronze_light": (210, 155, 75),

        # Fire (magic/spectral glow)
        "fire_darkest": (35, 5, 0),
        "fire_dark": (115, 25, 5),
        "fire_mid": (225, 75, 15),
        "fire_light": (255, 155, 50),
        "fire_hot": (255, 215, 90),
        "fire_shine": (255, 245, 195),

        # Eye (bright amber glow)
        "eye_socket": (5, 3, 2),
        "eye_dark": (60, 30, 10),
        "eye_mid": (180, 115, 30),
        "eye_light": (255, 195, 85),
        "eye_glow": (255, 240, 165),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_pyraklos._clamp(color)
        if _NS_pyraklos.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_pyraklos._clamp(color)
        if _NS_pyraklos.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_pyraklos._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_pyraklos._clamp(color), points)

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
    def draw_pyraklos(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_pyraklos._detect_moving(boss)
        _NS_pyraklos._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_pyr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_pyraklos._draw_battle_aura(surface, x, y, pulse)
        _NS_pyraklos._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_pyraklos._draw_bulwark_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_pyraklos._draw_arena_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_pyraklos._draw_rebuke_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_pyraklos._draw_pyr_attack(surface, boss, x, y)
        elif moving:
            _NS_pyraklos._draw_pyr_float(surface, boss, x, y)
        else:
            _NS_pyraklos._draw_pyr_idle(surface, boss, x, y)

        # Bulwark shield glow (over shield).
        if active_skill == "e":
            _NS_pyraklos._draw_bulwark_glow(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_pyraklos._draw_spear_of_mars(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_pyraklos._draw_rebuke_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_pyraklos._draw_arena_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_pyr_previous_timer", 0))
        active = bool(getattr(boss, "_pyr_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._pyr_attack_active = True
            boss._pyr_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._pyr_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._pyr_attack_frame = int(getattr(boss, "_pyr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._pyr_attack_active = False
            boss._pyr_attack_frame = 0
            active = False

        boss._pyr_previous_timer = timer
        boss._pyr_attack_progress = (
            min(1.0, getattr(boss, "_pyr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_pyr_last_x"):
            boss._pyr_last_x = boss.x
            boss._pyr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._pyr_last_x)
        dy = abs(boss.y - boss._pyr_last_y)
        boss._pyr_last_x = boss.x
        boss._pyr_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_pyr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_pyraklos._draw_shadow(surface, x, y + 55)
        _NS_pyraklos._draw_ember_wisps(surface, x, y + 40, boss.pulse)
        _NS_pyraklos._draw_pyr_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_pyr_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_pyraklos._draw_shadow(surface, x + sway, y + 55)
        _NS_pyraklos._draw_ember_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_pyraklos._draw_pyr_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")

    def _draw_pyr_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_pyr_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_pyr_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # SPEAR THRUST: wind-up pull back → forward thrust → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 6) * facing
            lift = int(t * 2)
        elif progress < 0.55:
            # Explosive forward thrust.
            t = (progress - 0.35) / 0.2
            lunge = int((-6 + t * 22)) * facing
            lift = int(2 - t * 3)
        else:
            # Recovery.
            t = (progress - 0.55) / 0.45
            lunge = int(16 * (1 - t)) * facing
            lift = int(-1 + t * 1)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_pyraklos._draw_shadow(surface, x + lunge, y + 55)
        _NS_pyraklos._draw_ember_wisps(surface, x + lunge, y + 40, boss.pulse,
                                        intense=True)
        _NS_pyraklos._draw_pyr_body(surface, x + lunge, y - lift + bob,
                                     facing, boss.pulse, "attack",
                                     progress)

    # ============================================================
    # BODY
    # ============================================================
    def _draw_pyr_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Spartan warrior body with spear + shield."""
        # Cape behind body.
        _NS_pyraklos._draw_cape(surface, cx, cy, facing, phase)

        # Lower body.
        _NS_pyraklos._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso.
        _NS_pyraklos._draw_torso(surface, cx, cy, facing, phase)

        # Compute spear thrust extension.
        spear_thrust = 0
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: pull back.
                t = attack_progress / 0.35
                spear_thrust = -int(t * 6)
            elif attack_progress < 0.55:
                # Thrust forward.
                t = (attack_progress - 0.35) / 0.2
                spear_thrust = int(-6 + t * 22)
            else:
                t = (attack_progress - 0.55) / 0.45
                spear_thrust = int(16 * (1 - t))

        # BACK ARM holds SHIELD (large round Aspis).
        # Shield is on the BACK side (facing away from viewer target direction).
        _NS_pyraklos._draw_shield_arm(surface, cx, cy - 4, facing, phase, action)

        # Head with helm + plume.
        _NS_pyraklos._draw_helmed_head(surface, cx + facing * 2, cy - 22,
                                        facing, phase, action, attack_progress)

        # FRONT ARM holds SPEAR (main weapon).
        _NS_pyraklos._draw_spear_arm(surface, cx, cy - 4, facing, phase,
                                      action, spear_thrust, attack_progress)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Crimson cape flowing behind."""
        wave = math.sin(phase * 0.7) * 3

        cape = [
            (cx - facing * 9, cy - 13),
            (cx - facing * 17 + int(wave), cy - 6),
            (cx - facing * 21 + int(wave), cy + 8),
            (cx - facing * 19 + int(wave * 0.5), cy + 22),
            (cx - facing * 13, cy + 32 + int(wave * 0.5)),
            (cx - facing * 3, cy + 34),
            (cx + facing * 3, cy + 30),
            (cx + facing * 5, cy + 14),
            (cx - facing * 2, cy - 11),
        ]
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in cape])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_darkest"], cape)
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_dark"], [
            (cx - facing * 8, cy - 12),
            (cx - facing * 16 + int(wave), cy - 5),
            (cx - facing * 20 + int(wave), cy + 7),
            (cx - facing * 18 + int(wave * 0.5), cy + 21),
            (cx - facing * 12, cy + 30 + int(wave * 0.5)),
            (cx - facing * 3, cy + 32),
            (cx + facing * 3, cy + 28),
            (cx + facing * 4, cy + 13),
            (cx - facing * 2, cy - 10),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_mid"], [
            (cx - facing * 11, cy - 7),
            (cx - facing * 16 + int(wave * 0.7), cy),
            (cx - facing * 14 + int(wave * 0.5), cy + 18),
            (cx - facing * 5, cy + 24),
            (cx - facing * 2, cy + 12),
            (cx - facing * 6, cy - 4),
        ])
        # Highlight strand.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_light"], [
            (cx - facing * 8, cy - 4),
            (cx - facing * 12 + int(wave * 0.5), cy + 4),
            (cx - facing * 10 + int(wave * 0.3), cy + 12),
            (cx - facing * 5, cy + 8),
        ])

        # Gold trim.
        edge_pts = [
            (cx - facing * 17 + int(wave), cy - 6),
            (cx - facing * 21 + int(wave), cy + 8),
            (cx - facing * 19 + int(wave * 0.5), cy + 22),
            (cx - facing * 13, cy + 32 + int(wave * 0.5)),
        ]
        for i in range(len(edge_pts) - 1):
            _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["gold_dark"],
                                  edge_pts[i], edge_pts[i + 1], 2)
            _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["gold_mid"],
                                  edge_pts[i], edge_pts[i + 1], 1)

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Roman warrior belt + pteruges + greaves."""
        wave = math.sin(phase * 0.9) * 2

        # Belt/hip.
        hip = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 4),
            (cx - 10, cy + 4),
            (cx - 12, cy),
        ]
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hip])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_darkest"], hip)
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_dark"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5), (cx + 11, cy),
            (cx + 9, cy + 3), (cx - 9, cy + 3), (cx - 11, cy),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_mid"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3), (cx + 9, cy),
            (cx + 7, cy + 2), (cx - 7, cy + 2), (cx - 9, cy),
        ])

        # Central belt buckle (fire gem).
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                         (cx - 3, cy - 3, 7, 6))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_dark"],
                         (cx - 2, cy - 2, 5, 5))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_dark"],
                         (cx - 1, cy - 1, 3, 3))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_mid"],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_light"],
                         (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_shine"],
                         (cx, cy - 1, 1, 1))

        # PTERUGES (leather strips like Roman skirt).
        for i, dx in enumerate((-9, -5, -1, 3, 7)):
            strip_h = 12 + int(math.sin(phase * 0.5 + i) * 1)
            wave_off = math.sin(phase * 0.6 + i * 0.4) * 1
            strip_pts = [
                (cx + dx - 2, cy + 3),
                (cx + dx + 2, cy + 3),
                (cx + dx + 2 + int(wave_off * 0.3), cy + 3 + strip_h),
                (cx + dx + int(wave_off * 0.5), cy + 5 + strip_h),
                (cx + dx - 2 + int(wave_off * 0.3), cy + 3 + strip_h),
            ]
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in strip_pts])
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["leather_dark"],
                                strip_pts)
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["leather_mid"], [
                (cx + dx - 1, cy + 4),
                (cx + dx + 1, cy + 4),
                (cx + dx + 1 + int(wave_off * 0.3), cy + 3 + strip_h - 2),
                (cx + dx - 1 + int(wave_off * 0.3), cy + 3 + strip_h - 2),
            ])
            # Gold stud at top.
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_mid"],
                             (cx + dx, cy + 4, 1, 1))
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                             (cx + dx, cy + 4, 1, 1))

        # Legs (armored greaves).
        for side in (-1, 1):
            lx = cx + side * 5
            ly1 = cy + 16
            ly2 = cy + 24
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                             (lx + 2, ly1 + 2), (lx + 2, ly2 + 2), 6)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                             (lx, ly1), (lx, ly2), 5)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_dark"],
                             (lx, ly1), (lx, ly2), 4)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_mid"],
                             (lx + side, ly1), (lx + side, ly2), 2)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_light"],
                             (lx + side, ly1), (lx + side, ly2 - 2), 1)

            # Boot at bottom.
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"], [
                (lx - 3, ly2), (lx + 3, ly2),
                (lx + 4, ly2 + 3), (lx - 4, ly2 + 3),
            ])
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["leather_dark"], [
                (lx - 2, ly2 - 1), (lx + 2, ly2 - 1),
                (lx + 3, ly2 + 2), (lx - 3, ly2 + 2),
            ])
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["leather_mid"], [
                (lx - 2, ly2), (lx + 2, ly2),
                (lx + 2, ly2 + 1), (lx - 2, ly2 + 1),
            ])

    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular gold breastplate (lorica musculata)."""
        breath = math.sin(phase * 0.7) * 1

        # Under-tunic (crimson visible around).
        torso = [
            (cx - 12, cy - 14),
            (cx - 14, cy - 8),
            (cx - 13, cy),
            (cx - 11, cy + 8),
            (cx - 9, cy + 14),
            (cx + 9, cy + 14),
            (cx + 11, cy + 8),
            (cx + 13, cy),
            (cx + 14, cy - 8),
            (cx + 12, cy - 14),
        ]
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_darkest"], torso)
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_dark"], [
            (cx - 11, cy - 13), (cx - 13, cy - 7), (cx - 12, cy),
            (cx - 10, cy + 7), (cx - 8, cy + 13),
            (cx + 8, cy + 13), (cx + 10, cy + 7), (cx + 12, cy),
            (cx + 13, cy - 7), (cx + 11, cy - 13),
        ])

        # Gold breastplate.
        chest = [
            (cx - 11, cy - 12),
            (cx + 11, cy - 12),
            (cx + 13, cy - 4),
            (cx + 10, cy + 6),
            (cx + 5, cy + 10),
            (cx - 5, cy + 10),
            (cx - 10, cy + 6),
            (cx - 13, cy - 4),
        ]
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_darkest"], chest)
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_dark"], [
            (cx - 10, cy - 11), (cx + 10, cy - 11), (cx + 12, cy - 4),
            (cx + 9, cy + 5), (cx + 4, cy + 9), (cx - 4, cy + 9),
            (cx - 9, cy + 5), (cx - 12, cy - 4),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_mid"], [
            (cx - 8, cy - 9), (cx + 8, cy - 9), (cx + 10, cy - 3),
            (cx + 7, cy + 3), (cx + 3, cy + 7), (cx - 3, cy + 7),
            (cx - 7, cy + 3), (cx - 10, cy - 3),
        ])

        # Muscle ridges (chest lines).
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                         (cx - 5, cy - 4), (cx + 5, cy - 4), 1)
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_light"],
                         (cx - 5, cy - 5), (cx + 5, cy - 5), 1)
        # Center line.
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                         (cx, cy - 10), (cx, cy + 5), 1)
        # Abs.
        for i in range(2):
            y_ab = cy + i * 4
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                             (cx - 5, y_ab), (cx - 1, y_ab), 1)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                             (cx + 1, y_ab), (cx + 5, y_ab), 1)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_light"],
                             (cx - 5, y_ab - 1), (cx - 1, y_ab - 1), 1)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_light"],
                             (cx + 1, y_ab - 1), (cx + 5, y_ab - 1), 1)

        # Chest highlight.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_light"], [
            (cx + facing * 2, cy - 8),
            (cx + facing * 6, cy - 5),
            (cx + facing * 5, cy - 1),
            (cx + facing * 1, cy - 3 + int(breath)),
        ])
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                         (cx + facing * 4, cy - 7, 1, 1))

        # Central fire emblem.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_pyraklos._alpha(150 * pulse * (4 - r) / 4)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["fire_mid"], alpha),
                (cx, cy - 7), r)
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_darkest"],
                         (cx - 1, cy - 8, 3, 3))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_dark"],
                         (cx - 1, cy - 8, 2, 2))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_hot"],
                         (cx, cy - 8, 1, 1))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_shine"],
                         (cx, cy - 8, 1, 1))

        # Shoulder pauldrons (gold).
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 11
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                                     (sh_x + 1, sh_y + 1), 6)
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                                     (sh_x, sh_y), 6)
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_dark"],
                                     (sh_x, sh_y), 5)
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_mid"],
                                     (sh_x + side, sh_y - 1), 3)
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_light"],
                                     (sh_x + side, sh_y - 1), 2)
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                             (sh_x + side, sh_y - 2, 1, 1))
            # Ridge lines.
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                             (sh_x - 2, sh_y + 2), (sh_x + 2, sh_y + 2), 1)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_light"],
                             (sh_x - 2, sh_y + 1), (sh_x + 2, sh_y + 1), 1)

    def _draw_shield_arm(surface, cx, cy, facing, phase, action):
        """Back arm holding the massive round Aspis shield."""
        sway = math.sin(phase * 0.5) * 1
        sh_x = cx - facing * 10
        sh_y = cy
        # Arm folded inward holding shield.
        elb_x = cx - facing * 6
        elb_y = cy + 6 + int(sway)
        hand_x = cx - facing * 4
        hand_y = cy + 10

        # Upper arm (leather).
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 7)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["leather_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 4)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_mid"],
                              (sh_x - facing, sh_y - 1),
                              (elb_x - facing, elb_y - 1), 2)

        # Forearm (behind shield).
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 5)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 4)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 3)

        # SHIELD (large round Aspis on the "back" side of body, but visible
        # since it's held to the side).
        # Position shield center slightly forward of elbow.
        shield_cx = cx - facing * 2
        shield_cy = cy + 2
        shield_r = 18

        _NS_pyraklos._draw_aspis_shield(surface, shield_cx, shield_cy,
                                         shield_r, facing, phase)

    def _draw_aspis_shield(surface, cx, cy, radius, facing, phase):
        """Draw the round Aspis shield."""
        # Shadow.
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                                 (cx + 2, cy + 2), radius)

        # Outer rim (dark bronze).
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["bronze_dark"],
                                 (cx, cy), radius)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["bronze_mid"],
                                 (cx, cy), radius - 1)

        # Wooden body (crimson painted).
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["crimson_dark"],
                                 (cx, cy), radius - 3)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["crimson_mid"],
                                 (cx, cy), radius - 4)

        # Inner gold rim.
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_dark"],
                                 (cx, cy), radius - 5, 1)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_mid"],
                                 (cx, cy), radius - 6, 1)

        # Central boss (raised gold dome).
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                                 (cx, cy), 7)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_dark"],
                                 (cx, cy), 6)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_mid"],
                                 (cx + facing, cy - 1), 5)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_light"],
                                 (cx + facing, cy - 1), 3)
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                         (cx + facing, cy - 2, 1, 1))

        # Center Spartan symbol (Λ - lambda or spear).
        # Draw a spear/star pattern radiating from center.
        for angle_i in range(8):
            angle = angle_i * math.pi / 4 + phase * 0.05
            x1 = cx + int(math.cos(angle) * 3)
            y1 = cy + int(math.sin(angle) * 3)
            x2 = cx + int(math.cos(angle) * (radius - 8))
            y2 = cy + int(math.sin(angle) * (radius - 8))
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                             (x1, y1), (x2, y2), 1)
        # Bright inner star.
        for angle_i in range(4):
            angle = angle_i * math.pi / 2 + phase * 0.05
            x2 = cx + int(math.cos(angle) * (radius - 10))
            y2 = cy + int(math.sin(angle) * (radius - 10))
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_mid"],
                             (cx, cy), (x2, y2), 1)

        # Highlight on top-front of shield.
        for i in range(2):
            hl_angle = -math.pi / 4 - i * 0.2 * facing
            hx = cx + int(math.cos(hl_angle) * (radius - 5))
            hy = cy + int(math.sin(hl_angle) * (radius - 5))
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["crimson_edge"],
                                     (hx, hy), 2 - i)

        # Rim rivets (dots around outer edge).
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.02
            rx = cx + int(math.cos(angle) * (radius - 2))
            ry = cy + int(math.sin(angle) * (radius - 2))
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_mid"],
                             (rx, ry, 1, 1))
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                             (rx, ry, 1, 1))

    def _draw_spear_arm(surface, cx, cy, facing, phase, action, thrust,
                         attack_progress):
        """Front arm holding the spear."""
        sh_x = cx + facing * 11
        sh_y = cy

        # Arm extends slightly during thrust.
        elb_x = sh_x + facing * (8 + thrust // 2)
        elb_y = cy + 4

        hand_x = elb_x + facing * (10 + thrust // 2)
        hand_y = cy + 4

        # Upper arm (skin).
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 7)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_mid"],
                              (sh_x + facing, sh_y - 1),
                              (elb_x + facing, elb_y - 1), 3)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["skin_light"],
                              (sh_x + facing, sh_y - 2),
                              (elb_x + facing, elb_y - 2), 1)

        # Gold arm band.
        band_mid = ((sh_x + elb_x) // 2, (sh_y + elb_y) // 2)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_dark"],
                                 band_mid, 3)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_mid"],
                                 band_mid, 2)
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                         (band_mid[0], band_mid[1], 1, 1))

        # Forearm (gauntlet).
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 7)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 6)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["gold_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["gold_mid"],
                              (elb_x, elb_y), (hand_x, hand_y), 2)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["gold_light"],
                              (elb_x + facing, elb_y - 1),
                              (hand_x + facing, hand_y - 1), 1)

        # Fist gripping shaft.
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                                 (hand_x, hand_y), 4)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_dark"],
                                 (hand_x, hand_y), 3)
        _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["gold_mid"],
                                 (hand_x, hand_y - 1), 2)

        # Draw spear.
        _NS_pyraklos._draw_spear(surface, hand_x, hand_y, facing, phase,
                                  thrust, action, attack_progress)

    def _draw_spear(surface, hx, hy, facing, phase, thrust, action,
                     attack_progress):
        """Long spear with leaf-shaped blade."""
        # Spear points horizontally FORWARD (facing direction) when at rest.
        # It's a long weapon.
        shaft_len = 42
        tip_len = 10

        # Direction: horizontal facing.
        dx = facing
        dy = 0

        # Butt (back of spear, behind hand).
        butt_x = hx - int(dx * 14)
        butt_y = hy

        # Tip (front).
        tip_x = hx + int(dx * shaft_len)
        tip_y = hy

        # Perpendicular for width.
        perp_x = 0
        perp_y = 1

        # SHAFT (dark wood + bronze accents).
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                              (butt_x + 1, butt_y + 2),
                              (tip_x + 1, tip_y + 2), 3)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["leather_dark"],
                              (butt_x, butt_y), (tip_x, tip_y), 3)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["leather_mid"],
                              (butt_x, butt_y), (tip_x, tip_y), 2)
        _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["leather_light"],
                              (butt_x, butt_y - 1), (tip_x, tip_y - 1), 1)

        # Bronze binding rings along shaft.
        for i in range(1, 6):
            t = i / 6
            wx = int(butt_x + (tip_x - butt_x) * t)
            wy = butt_y
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["bronze_dark"],
                             (wx, wy - 2), (wx, wy + 2), 1)
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["bronze_light"],
                             (wx, wy - 1, 1, 1))

        # BUTT SPIKE (small bronze cap at back).
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"], [
            (butt_x - int(dx * 4) + 1, butt_y + 1),
            (butt_x + 1, butt_y - 2 + 1),
            (butt_x + 1, butt_y + 2 + 1),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["bronze_dark"], [
            (butt_x - int(dx * 4), butt_y),
            (butt_x, butt_y - 2),
            (butt_x, butt_y + 2),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["bronze_mid"], [
            (butt_x - int(dx * 3), butt_y),
            (butt_x, butt_y - 1),
            (butt_x, butt_y + 1),
        ])

        # SPEAR TIP (leaf-shaped blade).
        # Blade base is at end of shaft.
        blade_base_x = tip_x
        blade_base_y = tip_y

        # Blade tip point.
        blade_tip_x = blade_base_x + int(dx * tip_len)
        blade_tip_y = blade_base_y

        # Widest part (mid of blade).
        blade_mid_x = blade_base_x + int(dx * tip_len * 0.4)
        blade_mid_y = blade_base_y

        # Blade sides (leaf shape).
        blade_up = (blade_mid_x, blade_mid_y - 3)
        blade_down = (blade_mid_x, blade_mid_y + 3)

        # Shadow.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"], [
            (blade_base_x + 1, blade_base_y - 1 + 1),
            (blade_up[0] + 1, blade_up[1] + 1),
            (blade_tip_x + 1, blade_tip_y + 1),
            (blade_down[0] + 1, blade_down[1] + 1),
            (blade_base_x + 1, blade_base_y + 1 + 1),
        ])
        # Dark steel.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["steel_darkest"], [
            (blade_base_x, blade_base_y - 1),
            blade_up,
            (blade_tip_x, blade_tip_y),
            blade_down,
            (blade_base_x, blade_base_y + 1),
        ])
        # Inner blade.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["steel_dark"], [
            (blade_base_x + int(dx * 1), blade_base_y - 1),
            (blade_mid_x, blade_mid_y - 2),
            (blade_tip_x - int(dx * 1), blade_tip_y),
            (blade_mid_x, blade_mid_y + 2),
            (blade_base_x + int(dx * 1), blade_base_y + 1),
        ])
        # Mid highlight.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["steel_mid"], [
            (blade_base_x + int(dx * 2), blade_base_y - 1),
            (blade_mid_x, blade_mid_y - 1),
            (blade_tip_x - int(dx * 2), blade_tip_y),
            (blade_mid_x, blade_mid_y + 1),
        ])
        # Central ridge (bright line along blade).
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["steel_light"],
                         (blade_base_x, blade_base_y),
                         (blade_tip_x, blade_tip_y), 1)
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["steel_shine"],
                         (blade_base_x + int(dx * 2), blade_base_y),
                         (blade_tip_x - int(dx * 2), blade_tip_y), 1)
        # Tip point highlight.
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["steel_shine"],
                         (blade_tip_x - int(dx * 1), blade_tip_y, 1, 1))

        # Bronze socket where blade meets shaft.
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["bronze_dark"],
                         (blade_base_x - int(dx * 2) - 1, blade_base_y - 2, 3, 5))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["bronze_mid"],
                         (blade_base_x - int(dx * 2), blade_base_y - 1, 2, 3))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["bronze_light"],
                         (blade_base_x - int(dx * 2), blade_base_y - 1, 1, 1))

        # Thrust streak during attack.
        if action == "attack" and 0.35 < attack_progress < 0.65:
            streak_intensity = math.sin((attack_progress - 0.35) / 0.3 * math.pi)
            streak_alpha = _NS_pyraklos._alpha(230 * streak_intensity)

            # Horizontal streak lines behind spear tip.
            for i in range(1, 6):
                t = i * 0.15
                sx = blade_tip_x - int(dx * i * 8)
                sy = blade_tip_y
                alpha_t = _NS_pyraklos._alpha(streak_alpha * (1 - t) * 0.9)
                pygame.draw.line(surface,
                    (*_NS_pyraklos.PALETTE["fire_light"], alpha_t),
                    (sx, sy - 1), (sx - int(dx * 4), sy - 1), 2)
                pygame.draw.line(surface,
                    (*_NS_pyraklos.PALETTE["fire_hot"], alpha_t),
                    (sx, sy), (sx - int(dx * 4), sy), 1)
                pygame.draw.line(surface,
                    (*_NS_pyraklos.PALETTE["fire_shine"], alpha_t),
                    (sx, sy + 1), (sx - int(dx * 4), sy + 1), 1)

    def _draw_helmed_head(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Spartan helm with red plume."""
        _NS_pyraklos._draw_helm(surface, cx, cy, facing, phase)
        _NS_pyraklos._draw_plume(surface, cx, cy, facing, phase)
        _NS_pyraklos._draw_helm_eye(surface, cx + facing * 2, cy - 3,
                                     facing, phase, action, attack_progress)

    def _draw_helm(surface, cx, cy, facing, phase):
        """Corinthian-style helm."""
        # Helmet dome (fuller, more angular than Kaeldris).
        helm = [
            (cx - 8, cy + 5),
            (cx - 10, cy - 1),
            (cx - 10, cy - 8),
            (cx - 6, cy - 12),
            (cx + 6, cy - 12),
            (cx + 10, cy - 8),
            (cx + 10, cy - 1),
            (cx + 8, cy + 5),
            (cx + 6, cy + 8),
            (cx - 6, cy + 8),
        ]
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in helm])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_darkest"], helm)
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_dark"], [
            (cx - 7, cy + 4), (cx - 9, cy - 1), (cx - 9, cy - 7),
            (cx - 5, cy - 11), (cx + 5, cy - 11), (cx + 9, cy - 7),
            (cx + 9, cy - 1), (cx + 7, cy + 4),
            (cx + 5, cy + 7), (cx - 5, cy + 7),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_mid"], [
            (cx - 6, cy - 3), (cx - 8, cy - 6), (cx - 6, cy - 10),
            (cx - 2, cy - 11), (cx + 2, cy - 11), (cx + 6, cy - 10),
            (cx + 8, cy - 6), (cx + 6, cy - 3),
        ])

        # Highlight.
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_light"], [
            (cx + facing * 2, cy - 9),
            (cx + facing * 6, cy - 6),
            (cx + facing * 5, cy - 2),
            (cx + facing * 1, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                         (cx + facing * 5, cy - 7, 1, 1))

        # T-slit face guard (Corinthian style).
        # Nose bar.
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                         (cx - 1, cy - 6, 3, 10))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                         (cx - 1, cy - 6, 2, 10))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_dark"],
                         (cx - 1, cy - 6, 1, 10))
        # Eye slits (two separate almond shapes).
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                         (cx - 6, cy - 4, 4, 3))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["eye_socket"],
                         (cx - 5, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                         (cx + 2, cy - 4, 4, 3))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["eye_socket"],
                         (cx + 3, cy - 3, 3, 2))

        # Cheek guards (side panels extending down).
        for side in (-1, 1):
            cheek_pts = [
                (cx + side * 6, cy - 2),
                (cx + side * 9, cy),
                (cx + side * 8, cy + 5),
                (cx + side * 4, cy + 7),
            ]
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                                cheek_pts)
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_dark"], [
                (cx + side * 5, cy - 1),
                (cx + side * 8, cy + 1),
                (cx + side * 7, cy + 5),
                (cx + side * 4, cy + 6),
            ])
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["gold_mid"], [
                (cx + side * 6, cy + 2),
                (cx + side * 7, cy + 4),
                (cx + side * 5, cy + 5),
            ])
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_light"],
                             (cx + side * 7, cy + 2, 1, 1))

        # Helm rim.
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_darkest"],
                         (cx - 8, cy + 5), (cx + 8, cy + 5), 1)
        pygame.draw.line(surface, _NS_pyraklos.PALETTE["gold_shine"],
                         (cx - 7, cy + 4), (cx + 7, cy + 4), 1)

    def _draw_plume(surface, cx, cy, facing, phase):
        """Red horsehair plume (crest on top of helm)."""
        wave = math.sin(phase * 0.8) * 2

        # Plume rises high and curves back.
        plume = [
            (cx - facing * 2, cy - 11),
            (cx + facing * 2, cy - 12),
            (cx - facing * 3, cy - 18 + int(wave)),
            (cx - facing * 8, cy - 22 + int(wave)),
            (cx - facing * 13, cy - 18 + int(wave * 0.5)),
            (cx - facing * 14, cy - 10),
            (cx - facing * 10, cy - 8),
            (cx - facing * 5, cy - 10),
        ]
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in plume])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_darkest"], plume)
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_dark"], [
            (cx - facing * 1, cy - 11),
            (cx + facing * 1, cy - 11),
            (cx - facing * 3, cy - 17 + int(wave)),
            (cx - facing * 7, cy - 21 + int(wave)),
            (cx - facing * 12, cy - 17 + int(wave * 0.5)),
            (cx - facing * 13, cy - 10),
            (cx - facing * 8, cy - 9),
            (cx - facing * 4, cy - 10),
        ])
        _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["crimson_mid"], [
            (cx, cy - 11),
            (cx - facing * 4, cy - 17 + int(wave)),
            (cx - facing * 8, cy - 19 + int(wave)),
            (cx - facing * 11, cy - 14),
            (cx - facing * 6, cy - 11),
        ])

        # Highlight strands.
        for i in range(3):
            strand_off = i * 2
            wave_off = math.sin(phase * 0.8 + i * 0.5) * 1
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["crimson_light"],
                             (cx - facing * (strand_off + 2), cy - 11),
                             (cx - facing * (strand_off + 5),
                              cy - 17 + int(wave_off)), 1)
            pygame.draw.line(surface, _NS_pyraklos.PALETTE["crimson_edge"],
                             (cx - facing * (strand_off + 6),
                              cy - 16 + int(wave_off)),
                             (cx - facing * (strand_off + 10),
                              cy - 13), 1)

        # Tip highlights.
        for i in range(2):
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["crimson_edge"],
                             (cx - facing * (8 + i * 2),
                              cy - 21 + int(wave), 1, 1))

        # Plume mounting bracket (gold at helm top).
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_dark"],
                         (cx - 2, cy - 12, 5, 2))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_mid"],
                         (cx - 2, cy - 12, 4, 1))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                         (cx, cy - 12, 1, 1))

    def _draw_helm_eye(surface, cx, cy, facing, phase, action, attack_progress):
        """Amber eye glow through helm slit."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        if action == "attack" and attack_progress > 0.2:
            pulse = min(1.0, pulse + 0.4)

        ex = cx
        ey = cy

        # Halo.
        for radius in range(4, 0, -1):
            alpha = _NS_pyraklos._alpha(150 * (4 - radius) / 4 * pulse)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["eye_mid"], alpha),
                (ex, ey), radius)

        # Eye through slit.
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["eye_dark"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["eye_mid"],
                         (ex - 1, ey, 2, 2))
        pygame.draw.rect(surface, _NS_pyraklos.PALETTE["eye_light"],
                         (ex, ey, 1, 1))
        if pulse > 0.85:
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 1, 2, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (45, 15, 12, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_battle_aura(surface, x, y, phase):
        """Fire/crimson battle aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_pyraklos._alpha((85 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_pyraklos._aacircle(aura,
                    (*_NS_pyraklos.PALETTE["fire_darkest"], alpha),
                    (110, 100), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_pyraklos._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_pyraklos._aacircle(aura,
                    (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                    (110, 100), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_pyraklos._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_pyraklos._aacircle(aura,
                    (*_NS_pyraklos.PALETTE["crimson_dark"], alpha),
                    (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Floating gold + fire particles.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = (_NS_pyraklos.PALETTE["fire_mid"] if i % 2 == 0
                     else _NS_pyraklos.PALETTE["gold_mid"])
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Battle ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_pyraklos.PALETTE["fire_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_pyraklos.PALETTE["fire_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_pyraklos.PALETTE["gold_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_pyraklos.PALETTE["crimson_dark"], 180),
                            (40, 24, 90, 14), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_pyraklos.PALETTE["fire_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_pyraklos.PALETTE["fire_hot"],
                 _NS_pyraklos._alpha(150 * pulse)),
                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    def _draw_ember_wisps(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Fire ember wisps."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_pyraklos._alpha((30 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_pyraklos.PALETTE["fire_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_pyraklos._alpha((20 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_pyraklos._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["fire_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["fire_hot"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["fire_shine"], alpha),
                (sx, sy - 1, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_pyraklos._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_darkest"], alpha),
                    (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface,
                    (*_NS_pyraklos.PALETTE["fire_mid"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_pyraklos.PALETTE["fire_hot"], alpha),
                    (sx, sy, 1, 1))

    # ============================================================
    # SKILL: Q - SPEAR OF MARS (thrown spear projectile)
    # ============================================================
    def _draw_spear_of_mars(surface, boss, x, y, timer, phase):
        """Thrown legendary spear that flies to target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraklos._target_position(boss, x, y)

        if progress < 0.2:
            # Wind-up: raise spear + gather energy.
            t = progress / 0.2
            charge_x = x + facing * 25
            charge_y = y - 15
            cr = int(3 + t * 10)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_pyraklos._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                    (charge_x, charge_y), r)
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["fire_mid"],
                                     (charge_x, charge_y), max(1, cr - 2))
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["fire_light"],
                                     (charge_x, charge_y), max(1, cr - 4))
            _NS_pyraklos._aacircle(surface, _NS_pyraklos.PALETTE["fire_shine"],
                                     (charge_x, charge_y), max(1, cr - 6))

            # Sparks around charge.
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_hot"],
                                 (sx, sy, 1, 1))
        else:
            # Spear flies to target.
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 30
            start_y = y - 10
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Direction.
            dx_a = tx - start_x
            dy_a = ty - start_y
            length = max(1, math.sqrt(dx_a ** 2 + dy_a ** 2))
            ux = dx_a / length
            uy = dy_a / length

            # Trail of fire embers.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_pyraklos._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_darkest"], alpha),
                    (px, py), size)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                    (px, py), max(1, size - 1))
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_mid"], alpha),
                    (px, py), max(1, size - 2))
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_light"], alpha),
                    (px, py), max(1, size - 3))

            # Draw actual spear shape flying.
            spear_len = 24
            back_x = bx - int(ux * spear_len * 0.6)
            back_y = by - int(uy * spear_len * 0.6)
            tip_x = bx + int(ux * spear_len * 0.4)
            tip_y = by + int(uy * spear_len * 0.4)

            # Shaft.
            _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["shadow_deep"],
                                  (back_x + 1, back_y + 1),
                                  (tip_x + 1, tip_y + 1), 3)
            _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["leather_dark"],
                                  (back_x, back_y), (tip_x, tip_y), 2)
            _NS_pyraklos._aaline(surface, _NS_pyraklos.PALETTE["leather_light"],
                                  (back_x, back_y), (tip_x, tip_y), 1)

            # Spear tip (bright).
            perp_x = -uy
            perp_y = ux
            tip_up = (tip_x - int(ux * 2) + int(perp_x * 2),
                      tip_y - int(uy * 2) + int(perp_y * 2))
            tip_down = (tip_x - int(ux * 2) - int(perp_x * 2),
                        tip_y - int(uy * 2) - int(perp_y * 2))
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["steel_darkest"], [
                (int(tip_x + ux * 3), int(tip_y + uy * 3)),
                tip_up, tip_down,
            ])
            _NS_pyraklos._poly(surface, _NS_pyraklos.PALETTE["steel_light"], [
                (int(tip_x + ux * 2), int(tip_y + uy * 2)),
                (int((tip_up[0] + tip_x) / 2), int((tip_up[1] + tip_y) / 2)),
                (int((tip_down[0] + tip_x) / 2),
                 int((tip_down[1] + tip_y) / 2)),
            ])
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["white"],
                             (int(tip_x + ux * 3), int(tip_y + uy * 3), 1, 1))
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["fire_shine"],
                             (int(tip_x + ux * 2), int(tip_y + uy * 2), 1, 1))

            # Big fire aura around spear.
            for r in range(9, 2, -2):
                alpha = _NS_pyraklos._alpha(100 * (9 - r) / 9)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_light"], alpha),
                    (bx, by), r)

            # Impact at target.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(10 + st * 25)
                alpha = _NS_pyraklos._alpha(240 * (1 - st))
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_darkest"], alpha),
                    (tx, ty), radius + 3, 3)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                    (tx, ty), radius, 2)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_mid"], alpha),
                    (tx, ty), max(1, radius - 5), 2)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_light"], alpha),
                    (tx, ty), max(1, radius - 10), 1)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_shine"], alpha),
                    (tx, ty), max(1, radius // 4))

                # Radial sparks.
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                        (*_NS_pyraklos.PALETTE["fire_hot"], alpha),
                        (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                        (*_NS_pyraklos.PALETTE["fire_shine"], alpha),
                        (ex, ey, 1, 1))

    # ============================================================
    # SKILL: W - GOD'S REBUKE (shield bash + arc slash)
    # ============================================================
    def _draw_rebuke_ground(surface, boss, x, y, timer, phase):
        """Impact ring on ground where shield hits."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            hit_x = x + facing * 40
            hit_y = y + 40
            r = int(15 + t * 25)
            alpha = _NS_pyraklos._alpha(200 * (1 - t))
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                (hit_x, hit_y), r, 2)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["fire_mid"], alpha),
                (hit_x, hit_y), max(1, r - 4), 1)

    def _draw_rebuke_foreground(surface, boss, x, y, timer, phase):
        """Crescent shield-bash arc forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up on shield.
            t = progress / 0.3
            shield_x = x - facing * 2
            shield_y = y + 2
            for r in range(int(4 + t * 12), 0, -2):
                alpha = _NS_pyraklos._alpha(180 * t * (14 - r) / 14)
                _NS_pyraklos._aacircle(surface,
                    (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                    (shield_x, shield_y), r)
        else:
            # Crescent slash forward.
            t = (progress - 0.3) / 0.7
            intensity = math.sin(t * math.pi)

            # Big crescent arc.
            center_x = x
            center_y = y - 5
            radius = 55 + int(t * 15)
            arc_alpha = _NS_pyraklos._alpha(240 * intensity)

            arc_points = []
            arc_start = -math.pi / 2.5
            arc_end = math.pi / 2.5
            for i in range(18):
                arc_t = i / 17
                angle = arc_start + (arc_end - arc_start) * arc_t
                ax = center_x + int(math.cos(angle) * radius) * facing
                ay = center_y + int(math.sin(angle) * radius)
                arc_points.append((ax, ay))

            # Layered arc lines.
            for i in range(len(arc_points) - 1):
                _NS_pyraklos._aaline(surface,
                    (*_NS_pyraklos.PALETTE["fire_darkest"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 8)
                _NS_pyraklos._aaline(surface,
                    (*_NS_pyraklos.PALETTE["fire_dark"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 6)
                _NS_pyraklos._aaline(surface,
                    (*_NS_pyraklos.PALETTE["fire_mid"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 4)
                _NS_pyraklos._aaline(surface,
                    (*_NS_pyraklos.PALETTE["fire_light"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 2)
                _NS_pyraklos._aaline(surface,
                    (*_NS_pyraklos.PALETTE["fire_shine"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 1)

            # Bright sparks along arc.
            for i, pt in enumerate(arc_points):
                if i % 2 == 0:
                    pygame.draw.rect(surface,
                        (*_NS_pyraklos.PALETTE["white"], arc_alpha),
                        (pt[0], pt[1], 2, 2))

            # Rock debris flying (knocked back enemies).
            for i in range(8):
                debris_t = (phase * 0.6 + i * 0.1) % 1.0
                debris_x = x + facing * (30 + int(debris_t * 40))
                debris_y = y + int(math.sin(phase + i) * 15) - int(debris_t * 8)
                debris_alpha = _NS_pyraklos._alpha(200 * intensity * (1 - debris_t))
                pygame.draw.rect(surface,
                    (*_NS_pyraklos.PALETTE["leather_dark"], debris_alpha),
                    (debris_x, debris_y, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_pyraklos.PALETTE["leather_mid"], debris_alpha),
                    (debris_x, debris_y, 1, 1))

    # ============================================================
    # SKILL: E - BULWARK (shield glow buff)
    # ============================================================
    def _draw_bulwark_ground(surface, boss, x, y, timer, phase):
        """Gold defensive ring under boss."""
        for i in range(2):
            r = int(30 + i * 6 + math.sin(phase * 2) * 2)
            alpha = _NS_pyraklos._alpha(200 - i * 60)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["gold_mid"], alpha),
                (x, y + 40), r, 2)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["gold_light"], alpha),
                (x, y + 40), r, 1)

    def _draw_bulwark_glow(surface, boss, x, y, timer, phase):
        """Massive golden light around shield + boss."""
        facing = boss.direction
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Glow around shield.
        shield_x = x - facing * 2
        shield_y = y - 2

        # Layered glow.
        glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        center = (40, 40)
        for radius in range(38, 3, -3):
            alpha = _NS_pyraklos._alpha((38 - radius) * 3 * pulse)
            if alpha > 0:
                _NS_pyraklos._aacircle(glow_surf,
                    (*_NS_pyraklos.PALETTE["gold_mid"], alpha), center, radius)
        for radius in range(24, 3, -2):
            alpha = _NS_pyraklos._alpha((24 - radius) * 4 * pulse)
            if alpha > 0:
                _NS_pyraklos._aacircle(glow_surf,
                    (*_NS_pyraklos.PALETTE["gold_light"], alpha), center, radius)
        # Bright core.
        _NS_pyraklos._aacircle(glow_surf, _NS_pyraklos.PALETTE["gold_shine"],
                                 center, 6)
        _NS_pyraklos._aacircle(glow_surf, _NS_pyraklos.PALETTE["gold_white"],
                                 center, 3)

        surface.blit(glow_surf, (shield_x - 40, shield_y - 40))

        # Deflected arrows/swords flying off shield.
        for i in range(6):
            defl_t = (phase * 0.8 + i * 0.15) % 1.0
            defl_angle = -math.pi / 3 + (i * math.pi / 5) * facing
            defl_r = int(20 + defl_t * 30)
            dx = shield_x + int(math.cos(defl_angle) * defl_r) * facing
            dy = shield_y + int(math.sin(defl_angle) * defl_r)
            defl_alpha = _NS_pyraklos._alpha(220 * (1 - defl_t))

            # Small deflected arrow/sword shape.
            pygame.draw.line(surface,
                (*_NS_pyraklos.PALETTE["steel_dark"], defl_alpha),
                (dx, dy), (dx + int(math.cos(defl_angle) * 5) * facing,
                          dy + int(math.sin(defl_angle) * 5)), 2)
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["steel_light"], defl_alpha),
                (dx + int(math.cos(defl_angle) * 5) * facing,
                 dy + int(math.sin(defl_angle) * 5), 1, 1))
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["steel_shine"], defl_alpha),
                (dx + int(math.cos(defl_angle) * 5) * facing,
                 dy + int(math.sin(defl_angle) * 5), 1, 1))

        # Rotating rune sparkles around shield.
        for i in range(12):
            angle = phase * 1.2 + i * math.pi / 6
            sr = 35
            sx = shield_x + int(math.cos(angle) * sr)
            sy = shield_y + int(math.sin(angle) * sr)
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_shine"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_pyraklos.PALETTE["gold_white"],
                             (sx, sy, 1, 1))

    # ============================================================
    # SKILL: R - ARENA OF BLOOD (spectral spear arena)
    # ============================================================
    def _draw_arena_ground(surface, boss, x, y, timer, phase):
        """Fire arena ring around target."""
        tx, ty = _NS_pyraklos._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Center around target.
        arena_r = 70

        if progress < 0.25:
            # Ring appears.
            t = progress / 0.25
            r_now = int(arena_r * t)
            alpha = _NS_pyraklos._alpha(200 * t)
            pygame.draw.ellipse(surface,
                (*_NS_pyraklos.PALETTE["fire_darkest"], alpha),
                (tx - r_now, ty - r_now // 3, r_now * 2, r_now * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                (tx - r_now + 3, ty - r_now // 3 + 2,
                 r_now * 2 - 6, r_now * 2 // 3 - 4), 2)
        else:
            # Sustained arena.
            t = (progress - 0.25) / 0.75
            pulse_r = int(math.sin(phase * 3) * 3)
            r_now = arena_r + pulse_r

            alpha = _NS_pyraklos._alpha(230 * (1 - t * 0.3))
            for i in range(3):
                arc_r = r_now - i * 5
                if arc_r < 5:
                    continue
                arc_alpha = _NS_pyraklos._alpha(alpha * (1 - i * 0.3))
                pygame.draw.ellipse(surface,
                    (*_NS_pyraklos.PALETTE["fire_dark"], arc_alpha),
                    (tx - arc_r, ty - arc_r // 3,
                     arc_r * 2, arc_r * 2 // 3), 3 - i)
                pygame.draw.ellipse(surface,
                    (*_NS_pyraklos.PALETTE["fire_mid"], arc_alpha),
                    (tx - arc_r + 2, ty - arc_r // 3 + 1,
                     arc_r * 2 - 4, arc_r * 2 // 3 - 2),
                    max(1, 2 - i))

    def _draw_arena_foreground(surface, boss, x, y, timer, phase):
        """Spectral spears standing around arena edge."""
        tx, ty = _NS_pyraklos._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        arena_r = 70

        if progress < 0.25:
            # Rising: spears grow from ground.
            t = progress / 0.25
            num_spears = 12
            for i in range(num_spears):
                angle = i * math.pi * 2 / num_spears + phase * 0.05
                sx = tx + int(math.cos(angle) * arena_r)
                sy = ty + int(math.sin(angle) * arena_r * 0.4)

                spear_h = int(30 * t)
                _NS_pyraklos._draw_spectral_spear(surface, sx, sy, spear_h,
                                                    phase, alpha_mult=t)
        elif progress < 0.85:
            # Sustained arena with spectral spears + occasional strikes.
            num_spears = 12
            for i in range(num_spears):
                angle = i * math.pi * 2 / num_spears + phase * 0.05
                sx = tx + int(math.cos(angle) * arena_r)
                sy = ty + int(math.sin(angle) * arena_r * 0.4)

                # Some spears occasionally "strike" inward.
                strike_phase = (phase * 1.5 + i * 0.5) % 2.0
                if strike_phase < 0.3:
                    # Strike animation.
                    strike_t = strike_phase / 0.3
                    strike_offset = int(math.sin(strike_t * math.pi) * 15)
                    sx_strike = sx - int(math.cos(angle) * strike_offset)
                    sy_strike = sy - int(math.sin(angle) * strike_offset * 0.5)
                    _NS_pyraklos._draw_spectral_spear(surface, sx_strike,
                                                       sy_strike, 32, phase,
                                                       alpha_mult=1.0)
                    # Strike flash.
                    pygame.draw.rect(surface,
                        _NS_pyraklos.PALETTE["fire_shine"],
                        (sx_strike, sy_strike - 32, 2, 2))
                else:
                    _NS_pyraklos._draw_spectral_spear(surface, sx, sy, 30,
                                                       phase, alpha_mult=1.0)

            # "ARENA OF BLOOD" indicator - fire logo center above.
            logo_bob = int(math.sin(phase * 1.5) * 3)
            logo_y = ty - arena_r + logo_bob - 5
            logo_alpha = _NS_pyraklos._alpha(230)
            # Crossed spears icon.
            pygame.draw.line(surface,
                (*_NS_pyraklos.PALETTE["fire_light"], logo_alpha),
                (tx - 8, logo_y - 4), (tx + 8, logo_y + 4), 2)
            pygame.draw.line(surface,
                (*_NS_pyraklos.PALETTE["fire_light"], logo_alpha),
                (tx + 8, logo_y - 4), (tx - 8, logo_y + 4), 2)
            pygame.draw.line(surface,
                (*_NS_pyraklos.PALETTE["fire_shine"], logo_alpha),
                (tx - 7, logo_y - 3), (tx + 7, logo_y + 3), 1)
            pygame.draw.line(surface,
                (*_NS_pyraklos.PALETTE["fire_shine"], logo_alpha),
                (tx + 7, logo_y - 3), (tx - 7, logo_y + 3), 1)
            # Center gem.
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["fire_hot"], logo_alpha),
                (tx - 1, logo_y - 1, 3, 3))
            pygame.draw.rect(surface,
                (*_NS_pyraklos.PALETTE["fire_shine"], logo_alpha),
                (tx, logo_y, 1, 1))
        else:
            # Fading: spears sink.
            t = (progress - 0.85) / 0.15
            num_spears = 12
            for i in range(num_spears):
                angle = i * math.pi * 2 / num_spears + phase * 0.05
                sx = tx + int(math.cos(angle) * arena_r)
                sy = ty + int(math.sin(angle) * arena_r * 0.4)
                spear_h = int(30 * (1 - t))
                if spear_h > 0:
                    _NS_pyraklos._draw_spectral_spear(surface, sx, sy, spear_h,
                                                       phase, alpha_mult=1 - t)

    def _draw_spectral_spear(surface, sx, sy_ground, height, phase, alpha_mult=1.0):
        """Draw one spectral spear rising from ground."""
        if height <= 0:
            return
        alpha_base = _NS_pyraklos._alpha(220 * alpha_mult)

        # Shaft (fire glow line).
        for width, alpha_mult2 in [(3, 0.4), (2, 0.7), (1, 1.0)]:
            pygame.draw.line(surface,
                (*_NS_pyraklos.PALETTE["fire_mid"],
                 _NS_pyraklos._alpha(alpha_base * alpha_mult2)),
                (sx, sy_ground), (sx, sy_ground - height), width)

        # Bright core.
        pygame.draw.line(surface,
            (*_NS_pyraklos.PALETTE["fire_shine"], alpha_base),
            (sx, sy_ground), (sx, sy_ground - height + 2), 1)

        # Spear tip at top (leaf blade shape).
        tip_y = sy_ground - height
        _NS_pyraklos._poly(surface, (*_NS_pyraklos.PALETTE["fire_darkest"], alpha_base), [
            (sx, tip_y - 4),
            (sx - 2, tip_y),
            (sx + 2, tip_y),
        ])
        _NS_pyraklos._poly(surface, (*_NS_pyraklos.PALETTE["fire_light"], alpha_base), [
            (sx, tip_y - 3),
            (sx - 1, tip_y - 1),
            (sx + 1, tip_y - 1),
        ])
        pygame.draw.rect(surface, (*_NS_pyraklos.PALETTE["fire_shine"], alpha_base),
                         (sx, tip_y - 3, 1, 1))
        pygame.draw.rect(surface, (*_NS_pyraklos.PALETTE["white"], alpha_base),
                         (sx, tip_y - 4, 1, 1))

        # Glow around tip.
        for r in range(4, 0, -1):
            alpha = _NS_pyraklos._alpha(alpha_base * (4 - r) / 4 * 0.6)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["fire_mid"], alpha),
                (sx, tip_y - 1), r)

        # Base flame at ground.
        for r in range(3, 0, -1):
            alpha = _NS_pyraklos._alpha(alpha_base * (3 - r) / 3)
            _NS_pyraklos._aacircle(surface,
                (*_NS_pyraklos.PALETTE["fire_dark"], alpha),
                (sx, sy_ground), r)


# ====================================================================
# velmyrth.py
# ====================================================================

# ====================================================================
# VELMYRTH - THE SILENT EXECUTIONER (Mini Boss Assassin)
# ====================================================================


class _NS_velmyrth:
    """Namespace velmyrth - Mini Boss Phantom Assassin."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Cloak deep purple (main)
        "cloak_darkest": (8, 3, 15),
        "cloak_dark": (25, 12, 45),
        "cloak_mid": (55, 30, 85),
        "cloak_light": (100, 65, 140),
        "cloak_edge": (170, 130, 200),

        # Under-cloak (very dark, near black)
        "under_darkest": (3, 2, 8),
        "under_dark": (12, 8, 20),
        "under_mid": (30, 22, 40),
        "under_light": (60, 50, 70),

        # Skin (pale, cold)
        "skin_darkest": (45, 40, 55),
        "skin_dark": (85, 75, 95),
        "skin_mid": (145, 130, 155),
        "skin_light": (210, 195, 215),
        "skin_shine": (240, 230, 245),

        # Mask (bone white)
        "mask_dark": (95, 90, 105),
        "mask_mid": (170, 165, 175),
        "mask_light": (230, 225, 235),
        "mask_shine": (255, 250, 255),

        # Blade (dark steel + purple glow)
        "blade_darkest": (10, 8, 15),
        "blade_dark": (40, 35, 55),
        "blade_mid": (85, 80, 105),
        "blade_light": (170, 160, 190),
        "blade_shine": (230, 220, 240),

        # Phantom magic purple (bright glow)
        "magic_darkest": (25, 5, 40),
        "magic_dark": (75, 25, 120),
        "magic_mid": (155, 65, 210),
        "magic_light": (215, 130, 250),
        "magic_hot": (240, 190, 255),
        "magic_shine": (255, 230, 255),

        # Eye glow (magenta-pink through mask)
        "eye_socket": (5, 2, 8),
        "eye_dark": (60, 15, 80),
        "eye_mid": (180, 60, 200),
        "eye_light": (240, 140, 250),
        "eye_glow": (255, 210, 255),

        # Shadow/void
        "shadow_purple": (15, 8, 25),
        "shadow_mid": (40, 30, 55),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_velmyrth._clamp(color)
        if _NS_velmyrth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_velmyrth._clamp(color)
        if _NS_velmyrth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_velmyrth._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_velmyrth._clamp(color), points)

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
    def draw_velmyrth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_velmyrth._detect_moving(boss)
        _NS_velmyrth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_vel_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Check if E (Blur/invisibility) active for opacity.
        blur_alpha = 255
        if active_skill == "e":
            # Fade to semi-transparent.
            duration = 60
            prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            # Fade in then out.
            blur_intensity = math.sin(prog * math.pi)
            blur_alpha = int(255 * (1 - blur_intensity * 0.6))

        # Ambient behind.
        _NS_velmyrth._draw_phantom_aura(surface, x, y, pulse)
        _NS_velmyrth._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "r":
            _NS_velmyrth._draw_coupdegrace_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_velmyrth._draw_blur_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_velmyrth._draw_phantomstrike_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (with optional alpha).
        if blur_alpha < 255:
            # Render to intermediate surface for alpha blending.
            body_surf = pygame.Surface((200, 220), pygame.SRCALPHA)
            offset_x = x - 100
            offset_y = y - 110
            if attacking:
                _NS_velmyrth._draw_vel_attack(body_surf, boss, 100, 110)
            elif moving:
                _NS_velmyrth._draw_vel_float(body_surf, boss, 100, 110)
            else:
                _NS_velmyrth._draw_vel_idle(body_surf, boss, 100, 110)
            body_surf.set_alpha(blur_alpha)
            surface.blit(body_surf, (offset_x, offset_y))
        else:
            if attacking:
                _NS_velmyrth._draw_vel_attack(surface, boss, x, y)
            elif moving:
                _NS_velmyrth._draw_vel_float(surface, boss, x, y)
            else:
                _NS_velmyrth._draw_vel_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_velmyrth._draw_stifling_dagger(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_velmyrth._draw_phantomstrike_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_velmyrth._draw_blur_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_velmyrth._draw_coupdegrace_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vel_previous_timer", 0))
        active = bool(getattr(boss, "_vel_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vel_attack_active = True
            boss._vel_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._vel_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._vel_attack_frame = int(getattr(boss, "_vel_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vel_attack_active = False
            boss._vel_attack_frame = 0
            active = False

        boss._vel_previous_timer = timer
        boss._vel_attack_progress = (
            min(1.0, getattr(boss, "_vel_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_vel_last_x"):
            boss._vel_last_x = boss.x
            boss._vel_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vel_last_x)
        dy = abs(boss.y - boss._vel_last_y)
        boss._vel_last_x = boss.x
        boss._vel_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_vel_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_velmyrth._draw_shadow(surface, x, y + 55)
        _NS_velmyrth._draw_shadow_mist(surface, x, y + 40, boss.pulse)
        _NS_velmyrth._draw_vel_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_vel_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 6)
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_velmyrth._draw_shadow(surface, x + sway, y + 55)
        _NS_velmyrth._draw_shadow_mist(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_velmyrth._draw_vel_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")

    def _draw_vel_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_vel_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_vel_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Dual dagger swing (fast, crossing motion).
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 3) * facing
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-3 + t * 14)) * facing
            lift = int(3 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(11 * (1 - t)) * facing
            lift = int(-3 + t * 3)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_velmyrth._draw_shadow(surface, x + lunge, y + 55)
        _NS_velmyrth._draw_shadow_mist(surface, x + lunge, y + 40, boss.pulse,
                                        intense=True)
        _NS_velmyrth._draw_vel_body(surface, x + lunge, y - lift + bob,
                                     facing, boss.pulse, "attack",
                                     progress)

    # ============================================================
    # BODY (Slim humanoid assassin)
    # ============================================================
    def _draw_vel_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Slim hooded assassin with dual daggers."""
        # Cape/cloak flowing behind.
        _NS_velmyrth._draw_flowing_cape(surface, cx, cy, facing, phase)

        # Lower body (slim, robed).
        _NS_velmyrth._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso (slim armor).
        _NS_velmyrth._draw_torso(surface, cx, cy, facing, phase)

        # Compute dagger swing angles.
        dagger_angle_front = 0
        dagger_angle_back = 0
        if action == "attack":
            if attack_progress < 0.3:
                # Wind-up: pull back.
                t = attack_progress / 0.3
                dagger_angle_front = -math.pi * 0.3 * t
                dagger_angle_back = math.pi * 0.3 * t
            elif attack_progress < 0.55:
                # Cross-slash.
                t = (attack_progress - 0.3) / 0.25
                dagger_angle_front = -math.pi * 0.3 + math.pi * 0.7 * t
                dagger_angle_back = math.pi * 0.3 - math.pi * 0.7 * t
            else:
                # Return.
                t = (attack_progress - 0.55) / 0.45
                dagger_angle_front = math.pi * 0.4 * (1 - t)
                dagger_angle_back = -math.pi * 0.4 * (1 - t)

        # Back arm with dagger.
        _NS_velmyrth._draw_dagger_arm(surface, cx, cy - 4, facing, phase,
                                       action, dagger_angle_back, attack_progress,
                                       is_back=True)

        # Hooded head with mask.
        _NS_velmyrth._draw_hooded_head(surface, cx + facing * 1, cy - 22,
                                        facing, phase, action, attack_progress)

        # Front arm with dagger.
        _NS_velmyrth._draw_dagger_arm(surface, cx, cy - 4, facing, phase,
                                       action, dagger_angle_front, attack_progress,
                                       is_back=False)

    def _draw_flowing_cape(surface, cx, cy, facing, phase):
        """Long flowing dark purple cape."""
        wave = math.sin(phase * 0.7) * 3

        # Cape spans wide and flows down.
        cape = [
            (cx - facing * 9, cy - 12),
            (cx - facing * 16 + int(wave), cy - 6),
            (cx - facing * 20 + int(wave), cy + 8),
            (cx - facing * 18 + int(wave * 0.5), cy + 22),
            (cx - facing * 12, cy + 30 + int(wave * 0.5)),
            (cx - facing * 2, cy + 32),
            (cx + facing * 4, cy + 28),
            (cx + facing * 6, cy + 14),
            (cx - facing * 2, cy - 10),
        ]
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in cape])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_darkest"], cape)
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_dark"], [
            (cx - facing * 8, cy - 11),
            (cx - facing * 15 + int(wave), cy - 5),
            (cx - facing * 19 + int(wave), cy + 7),
            (cx - facing * 17 + int(wave * 0.5), cy + 21),
            (cx - facing * 11, cy + 28 + int(wave * 0.5)),
            (cx - facing * 2, cy + 30),
            (cx + facing * 4, cy + 26),
            (cx + facing * 5, cy + 13),
            (cx - facing * 2, cy - 9),
        ])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_mid"], [
            (cx - facing * 10, cy - 6),
            (cx - facing * 15 + int(wave * 0.7), cy),
            (cx - facing * 13 + int(wave * 0.5), cy + 18),
            (cx - facing * 4, cy + 24),
            (cx - facing * 2, cy + 12),
            (cx - facing * 6, cy - 3),
        ])

        # Cape edge highlights (light purple trim).
        edge_pts = [
            (cx - facing * 16 + int(wave), cy - 6),
            (cx - facing * 20 + int(wave), cy + 8),
            (cx - facing * 18 + int(wave * 0.5), cy + 22),
            (cx - facing * 12, cy + 30 + int(wave * 0.5)),
        ]
        for i in range(len(edge_pts) - 1):
            _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_light"],
                                  edge_pts[i], edge_pts[i + 1], 1)

        # Vertical fold lines (drape).
        for i, dx in enumerate((-4, 2, 8)):
            wave_off = math.sin(phase * 0.7 + i) * 1
            offset_x = cx - facing * dx
            pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_darkest"],
                             (offset_x, cy - 2),
                             (offset_x - facing * 2 + int(wave_off),
                              cy + 24), 1)

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Slim lower body with hanging tabard/loincloth."""
        wave = math.sin(phase * 0.9) * 2

        # Slim hip/waist.
        hip = [
            (cx - 7, cy - 6),
            (cx + 7, cy - 6),
            (cx + 8, cy),
            (cx + 6, cy + 6),
            (cx - 6, cy + 6),
            (cx - 8, cy),
        ]
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hip])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_darkest"], hip)
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_dark"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5), (cx + 7, cy),
            (cx + 5, cy + 5), (cx - 5, cy + 5), (cx - 7, cy),
        ])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_mid"], [
            (cx - 5, cy - 3), (cx + 5, cy - 3), (cx + 6, cy),
            (cx + 4, cy + 3), (cx - 4, cy + 3), (cx - 6, cy),
        ])

        # Center gem/belt buckle (glowing magic).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_velmyrth._alpha(240 * pulse)
        for r in range(4, 0, -1):
            alpha = _NS_velmyrth._alpha(150 * pulse * (4 - r) / 4)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                (cx, cy - 1), r)
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_darkest"],
                         (cx - 1, cy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_mid"],
                         (cx - 1, cy - 2, 2, 2))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_light"],
                         (cx - 1, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                         (cx, cy - 2, 1, 1))

        # Hanging tabard (dark cloth in front, between legs).
        tabard = [
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 3, cy + 16 + int(wave * 0.5)),
            (cx, cy + 20),
            (cx - 3, cy + 16 - int(wave * 0.5)),
        ]
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in tabard])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_darkest"], tabard)
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_dark"], [
            (cx - 3, cy + 6), (cx + 3, cy + 6),
            (cx + 2, cy + 15 + int(wave * 0.5)),
            (cx, cy + 18),
            (cx - 2, cy + 15 - int(wave * 0.5)),
        ])
        # Small magic emblem on tabard.
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_dark"],
                         (cx, cy + 10, 1, 3))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_mid"],
                         (cx, cy + 11, 1, 1))

        # Slim legs (thigh + boots).
        for side in (-1, 1):
            lx = cx + side * 4
            ly1 = cy + 4
            ly2 = cy + 20
            pygame.draw.line(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                             (lx + 2, ly1 + 2), (lx + 2, ly2 + 2), 5)
            pygame.draw.line(surface, _NS_velmyrth.PALETTE["under_darkest"],
                             (lx, ly1), (lx, ly2), 4)
            pygame.draw.line(surface, _NS_velmyrth.PALETTE["under_dark"],
                             (lx, ly1), (lx, ly2), 3)
            pygame.draw.line(surface, _NS_velmyrth.PALETTE["under_mid"],
                             (lx - side, ly1), (lx - side, ly2 - 4), 1)

            # Boot at bottom.
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"], [
                (lx - 3, ly2), (lx + 3, ly2),
                (lx + 4, ly2 + 3), (lx - 4, ly2 + 3),
            ])
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_darkest"], [
                (lx - 2, ly2 - 1), (lx + 2, ly2 - 1),
                (lx + 3, ly2 + 2), (lx - 3, ly2 + 2),
            ])
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_mid"], [
                (lx - 2, ly2), (lx + 2, ly2),
                (lx + 2, ly2 + 1), (lx - 2, ly2 + 1),
            ])

    def _draw_torso(surface, cx, cy, facing, phase):
        """Slim torso with subtle armor."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape (SLIM - not as wide as tank).
        torso = [
            (cx - 8, cy - 14),
            (cx - 10, cy - 8),
            (cx - 9, cy),
            (cx - 8, cy + 8),
            (cx - 7, cy + 14),
            (cx + 7, cy + 14),
            (cx + 8, cy + 8),
            (cx + 9, cy),
            (cx + 10, cy - 8),
            (cx + 8, cy - 14),
        ]
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_darkest"], torso)

        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_dark"], [
            (cx - 7, cy - 13), (cx - 9, cy - 7), (cx - 8, cy),
            (cx - 7, cy + 7), (cx - 6, cy + 13),
            (cx + 6, cy + 13), (cx + 7, cy + 7), (cx + 8, cy),
            (cx + 9, cy - 7), (cx + 7, cy - 13),
        ])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_mid"], [
            (cx - 5, cy - 10), (cx - 7, cy - 5), (cx - 6, cy),
            (cx - 5, cy + 5), (cx - 4, cy + 10),
            (cx + 4, cy + 10), (cx + 5, cy + 5), (cx + 6, cy),
            (cx + 7, cy - 5), (cx + 5, cy - 10),
        ])

        # Chest highlight.
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["under_light"], [
            (cx + facing * 2, cy - 8),
            (cx + facing * 4, cy - 5),
            (cx + facing * 3, cy),
            (cx + facing * 1, cy - 3 + int(breath)),
        ])

        # Cross straps (leather).
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                         (cx - 8, cy - 8), (cx + 8, cy + 4), 2)
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_dark"],
                         (cx - 8, cy - 8), (cx + 8, cy + 4), 1)
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                         (cx + 8, cy - 8), (cx - 8, cy + 4), 2)
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_dark"],
                         (cx + 8, cy - 8), (cx - 8, cy + 4), 1)

        # Center gem (small magic core).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_darkest"],
                         (cx - 1, cy - 3, 3, 3))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_dark"],
                         (cx - 1, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_light"],
                         (cx, cy - 2, 1, 1))
        if pulse > 0.85:
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                             (cx, cy - 2, 1, 1))

        # Slim waist accent (belt line).
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_dark"],
                         (cx - 8, cy + 10), (cx + 8, cy + 10), 1)
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_mid"],
                         (cx - 6, cy + 10), (cx + 6, cy + 10), 1)

    def _draw_dagger_arm(surface, cx, cy, facing, phase, action,
                          dagger_angle, attack_progress, is_back=False):
        """Arm holding curved dagger."""
        side = -1 if is_back else 1
        sh_x = cx + facing * side * 9
        sh_y = cy

        # Arm angle based on dagger angle.
        arm_base = -math.pi * 0.15 if not is_back else -math.pi * 0.25
        elb_angle = arm_base + dagger_angle * 0.4
        elb_x = sh_x + int(math.cos(elb_angle) * 8) * facing * (1 if not is_back else -1)
        elb_y = sh_y + int(math.sin(elb_angle) * 8) + 4

        grip_angle = elb_angle + dagger_angle * 0.5
        hand_x = elb_x + int(math.cos(grip_angle) * 9) * facing * (1 if not is_back else -1)
        hand_y = elb_y + int(math.sin(grip_angle) * 9)

        # Thin cloak sleeve.
        thickness = 4 if not is_back else 3

        # Upper arm.
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), thickness + 2)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), thickness + 1)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), thickness)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_mid"],
                              (sh_x + facing, sh_y - 1),
                              (elb_x + facing, elb_y - 1),
                              max(1, thickness - 2))

        # Forearm.
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), thickness + 1)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), thickness)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_dark"],
                              (elb_x, elb_y), (hand_x, hand_y),
                              max(1, thickness - 1))

        # Hand (pale skin).
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                                 (hand_x + 1, hand_y + 1), 3)
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["skin_darkest"],
                                 (hand_x, hand_y), 3)
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["skin_mid"],
                         (hand_x, hand_y - 1, 1, 1))

        # Draw the dagger.
        _NS_velmyrth._draw_curved_dagger(surface, hand_x, hand_y, facing, phase,
                                          dagger_angle, action, attack_progress,
                                          is_back)

    def _draw_curved_dagger(surface, hx, hy, facing, phase, angle, action,
                             attack_progress, is_back):
        """Curved assassin dagger."""
        # Dagger points forward (roughly horizontal).
        side_mult = -1 if is_back else 1
        base_angle = angle * side_mult

        blade_len = 18
        # Direction.
        dx = math.cos(base_angle) * facing
        dy = math.sin(base_angle)

        # Guard is at hand position.
        guard_x = hx
        guard_y = hy

        # Tip.
        tip_x = guard_x + int(dx * blade_len)
        # Curved: tip goes slightly up.
        tip_y = guard_y + int(dy * blade_len) - 3

        # Perpendicular.
        perp_x = -math.sin(base_angle) * facing
        perp_y = math.cos(base_angle)

        # Small pommel.
        pommel_x = guard_x - int(dx * 4)
        pommel_y = guard_y - int(dy * 4)
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                                 (pommel_x + 1, pommel_y + 1), 2)
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["blade_darkest"],
                                 (pommel_x, pommel_y), 2)
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["blade_dark"],
                                 (pommel_x, pommel_y), 1)
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_dark"],
                         (pommel_x, pommel_y, 1, 1))

        # Guard (small crossbar).
        guard_a = (guard_x + int(perp_x * 3), guard_y + int(perp_y * 3))
        guard_b = (guard_x - int(perp_x * 3), guard_y - int(perp_y * 3))
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                              (guard_a[0] + 1, guard_a[1] + 1),
                              (guard_b[0] + 1, guard_b[1] + 1), 2)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["blade_dark"],
                              guard_a, guard_b, 2)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["blade_mid"],
                              guard_a, guard_b, 1)

        # BLADE (curved shape).
        # Mid point (curve peak).
        mid_x = guard_x + int(dx * blade_len * 0.5)
        mid_y = guard_y + int(dy * blade_len * 0.5) - 2

        # Blade edge polygon (curved).
        blade_base_a = (guard_x + int(perp_x * 2),
                        guard_y + int(perp_y * 2))
        blade_base_b = (guard_x - int(perp_x * 2),
                        guard_y - int(perp_y * 2))
        blade_mid_a = (mid_x + int(perp_x * 3),
                       mid_y + int(perp_y * 3))
        blade_mid_b = (mid_x - int(perp_x * 2),
                       mid_y - int(perp_y * 2))

        # Shadow.
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"], [
            (blade_base_a[0] + 1, blade_base_a[1] + 1),
            (blade_mid_a[0] + 1, blade_mid_a[1] + 1),
            (tip_x + 1, tip_y + 1),
            (blade_mid_b[0] + 1, blade_mid_b[1] + 1),
            (blade_base_b[0] + 1, blade_base_b[1] + 1),
        ])
        # Dark blade.
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["blade_darkest"], [
            blade_base_a, blade_mid_a, (tip_x, tip_y),
            blade_mid_b, blade_base_b,
        ])
        # Inner blade.
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["blade_dark"], [
            (int(blade_base_a[0] * 0.7 + guard_x * 0.3),
             int(blade_base_a[1] * 0.7 + guard_y * 0.3)),
            (int(blade_mid_a[0] * 0.7 + mid_x * 0.3),
             int(blade_mid_a[1] * 0.7 + mid_y * 0.3)),
            (int(tip_x * 0.85 + mid_x * 0.15),
             int(tip_y * 0.85 + mid_y * 0.15)),
            (int(blade_mid_b[0] * 0.7 + mid_x * 0.3),
             int(blade_mid_b[1] * 0.7 + mid_y * 0.3)),
            (int(blade_base_b[0] * 0.7 + guard_x * 0.3),
             int(blade_base_b[1] * 0.7 + guard_y * 0.3)),
        ])

        # Blade edge highlight (magic purple glow).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        edge_alpha = _NS_velmyrth._alpha(220 * pulse)
        _NS_velmyrth._aaline(surface,
            (*_NS_velmyrth.PALETTE["magic_dark"], edge_alpha),
            blade_base_a, (tip_x, tip_y), 1)
        _NS_velmyrth._aaline(surface,
            (*_NS_velmyrth.PALETTE["magic_mid"], edge_alpha),
            (int((blade_base_a[0] + blade_mid_a[0]) / 2),
             int((blade_base_a[1] + blade_mid_a[1]) / 2)),
            (tip_x, tip_y), 1)

        # Bright edge highlight.
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["blade_light"],
                              blade_mid_a, (tip_x, tip_y), 1)

        # Tip glow (magic purple).
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["magic_dark"],
                                 (tip_x, tip_y), 2)
        _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["magic_mid"],
                                 (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                         (tip_x, tip_y, 1, 1))

        # Swing streak during attack.
        if action == "attack" and 0.3 < attack_progress < 0.6:
            streak_intensity = math.sin((attack_progress - 0.3) / 0.3 * math.pi)
            streak_alpha = _NS_velmyrth._alpha(220 * streak_intensity)

            # Arc trail.
            arc_start = base_angle - 0.6
            arc_end = base_angle
            for i in range(6):
                arc_t = i / 6
                trail_angle = arc_start + (arc_end - arc_start) * arc_t
                trail_dx = math.cos(trail_angle) * facing
                trail_dy = math.sin(trail_angle)
                trail_x = guard_x + int(trail_dx * blade_len)
                trail_y = guard_y + int(trail_dy * blade_len) - 2

                alpha_t = _NS_velmyrth._alpha(streak_alpha * (1 - arc_t) * 0.9)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha_t),
                    (trail_x, trail_y), 3)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_mid"], alpha_t),
                    (trail_x, trail_y), 2)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_light"], alpha_t),
                    (trail_x, trail_y), 1)

    def _draw_hooded_head(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Hooded head with pale mask underneath."""
        # HOOD (large, covering top of head).
        _NS_velmyrth._draw_hood(surface, cx, cy, facing, phase)

        # MASK (pale, in shadow inside hood).
        _NS_velmyrth._draw_mask(surface, cx, cy, facing, phase, action,
                                 attack_progress)

    def _draw_hood(surface, cx, cy, facing, phase):
        """Large pointed hood."""
        wave = math.sin(phase * 0.5) * 1

        # Hood outer shape.
        hood = [
            (cx - 9, cy + 5),
            (cx - 11, cy),
            (cx - 10, cy - 8),
            (cx - 6, cy - 14 + int(wave)),
            (cx, cy - 16 + int(wave)),
            (cx + 6, cy - 14 - int(wave)),
            (cx + 10, cy - 8),
            (cx + 11, cy),
            (cx + 9, cy + 5),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
        ]
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in hood])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_darkest"], hood)

        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_dark"], [
            (cx - 8, cy + 4), (cx - 10, cy), (cx - 9, cy - 7),
            (cx - 5, cy - 13 + int(wave)), (cx, cy - 15 + int(wave)),
            (cx + 5, cy - 13 - int(wave)), (cx + 9, cy - 7),
            (cx + 10, cy), (cx + 8, cy + 4),
            (cx + 4, cy + 6), (cx - 4, cy + 6),
        ])
        # Mid layer only on top (leave inside dark for shadow of mask).
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_mid"], [
            (cx - 8, cy - 2),
            (cx - 8, cy - 7),
            (cx - 4, cy - 12 + int(wave)),
            (cx, cy - 14 + int(wave)),
            (cx + 4, cy - 12 - int(wave)),
            (cx + 8, cy - 7),
            (cx + 8, cy - 2),
        ])

        # Hood highlight edge (light purple).
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_light"],
                              (cx + facing * 4, cy - 12),
                              (cx + facing * 8, cy - 4), 1)
        _NS_velmyrth._aaline(surface, _NS_velmyrth.PALETTE["cloak_edge"],
                              (cx + facing * 6, cy - 10),
                              (cx + facing * 7, cy - 6), 1)

        # Hood inside shadow (very dark inside opening).
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 5, cy + 4),
            (cx - 5, cy + 4),
        ])

        # Hood pointed tip (small horn-like protrusions).
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_darkest"], [
            (cx + facing * 2, cy - 15 + int(wave)),
            (cx + facing * 8, cy - 20 + int(wave)),
            (cx + facing * 4, cy - 13 + int(wave)),
        ])
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["cloak_dark"], [
            (cx + facing * 3, cy - 15 + int(wave)),
            (cx + facing * 7, cy - 18 + int(wave)),
            (cx + facing * 4, cy - 14 + int(wave)),
        ])
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["cloak_edge"],
                         (cx + facing * 8, cy - 20, 1, 1))

    def _draw_mask(surface, cx, cy, facing, phase, action, attack_progress):
        """Pale mask with glowing magenta eyes inside hood shadow."""
        # Mask base (small pale oval visible in hood opening).
        mask_shape = [
            (cx - 4, cy),
            (cx - 5, cy - 3),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 3),
            (cx + 4, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ]
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["mask_dark"], mask_shape)
        _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["mask_mid"], [
            (cx - 3, cy - 1), (cx - 4, cy - 3),
            (cx - 2, cy - 4), (cx + 2, cy - 4),
            (cx + 4, cy - 3), (cx + 3, cy - 1),
            (cx + 2, cy + 2), (cx - 2, cy + 2),
        ])
        # Mask highlight.
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["mask_light"],
                         (cx + facing * 2, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_velmyrth.PALETTE["mask_shine"],
                         (cx + facing * 2, cy - 3, 1, 1))

        # Cheek marks (dark slashes on mask).
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_darkest"],
                         (cx - 3, cy + 1), (cx - 2, cy + 3), 1)
        pygame.draw.line(surface, _NS_velmyrth.PALETTE["cloak_darkest"],
                         (cx + 3, cy + 1), (cx + 2, cy + 3), 1)

        # GLOWING MAGENTA EYES (2 slit eyes).
        _NS_velmyrth._draw_glowing_eyes(surface, cx, cy - 2, facing, phase,
                                          action, attack_progress)

    def _draw_glowing_eyes(surface, cx, cy, facing, phase, action,
                            attack_progress):
        """Bright magenta glowing eyes on mask."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Brighter during attack.
        if action == "attack" and attack_progress > 0.2:
            pulse = min(1.0, pulse + 0.4)

        # 2 eyes (slit).
        for eye_i, dx in enumerate((-2, 2)):
            ex = cx + dx
            ey = cy

            # Halo glow.
            for radius in range(4, 0, -1):
                alpha = _NS_velmyrth._alpha(120 * (4 - radius) / 4 * pulse)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["eye_mid"], alpha),
                    (ex, ey), radius)

            # Slit (thin horizontal).
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["eye_mid"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            if pulse > 0.85:
                pygame.draw.rect(surface, _NS_velmyrth.PALETTE["eye_glow"],
                                 (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 1, 3, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (35, 15, 50, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_phantom_aura(surface, x, y, phase):
        """Purple phantom aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 190), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_velmyrth._alpha((80 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_velmyrth._aacircle(aura,
                    (*_NS_velmyrth.PALETTE["magic_darkest"], alpha),
                    (100, 95), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_velmyrth._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_velmyrth._aacircle(aura,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (100, 95), radius)
        for radius in range(28, 5, -3):
            alpha = _NS_velmyrth._alpha((28 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_velmyrth._aacircle(aura,
                    (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                    (100, 95), radius)
        surface.blit(aura, (x - 100, y - 95))

        # Floating phantom particles.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Purple rune ring on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_velmyrth.PALETTE["magic_darkest"], 200),
                            (5, 16, 150, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_velmyrth.PALETTE["shadow_purple"], 220),
                            (14, 18, 132, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_velmyrth.PALETTE["magic_dark"], 230),
                            (25, 20, 110, 18), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 29 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 29 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_velmyrth.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_velmyrth.PALETTE["magic_hot"],
                 _NS_velmyrth._alpha(150 * pulse)),
                (15, 10, 130, 38), 1)
        surface.blit(ring, (x - 80, y - 25))

    def _draw_shadow_mist(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Shadow/phantom mist."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(28, 3, -3):
            alpha = _NS_velmyrth._alpha((28 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_velmyrth.PALETTE["shadow_purple"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(18, 3, -2):
            alpha = _NS_velmyrth._alpha((18 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising sparks.
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_velmyrth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_velmyrth.PALETTE["magic_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_velmyrth.PALETTE["magic_hot"], alpha), (sx, sy, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_velmyrth._alpha(150 - i * 22)
                if alpha <= 0:
                    continue
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["shadow_purple"], alpha),
                    (sx, sy), max(2, 6 - i))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["magic_light"], alpha),
                    (sx, sy - 1, 2, 2))

    # ============================================================
    # SKILL: Q - STIFLING DAGGER (thrown dagger projectile)
    # ============================================================
    def _draw_stifling_dagger(surface, boss, x, y, timer, phase):
        """Thrown purple dagger flying to target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_velmyrth._target_position(boss, x, y)

        if progress < 0.15:
            # Wind-up: charge at hand.
            t = progress / 0.15
            tip_x = x + facing * 22
            tip_y = y - 6
            cr = int(3 + t * 5)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_velmyrth._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (tip_x, tip_y), r)
            _NS_velmyrth._aacircle(surface, _NS_velmyrth.PALETTE["magic_mid"],
                                     (tip_x, tip_y), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                             (tip_x, tip_y, 1, 1))
        else:
            # Dagger flying to target.
            t = (progress - 0.15) / 0.85
            start_x = x + facing * 24
            start_y = y - 6

            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Direction of flight.
            fly_dx = tx - start_x
            fly_dy = ty - start_y
            fly_len = max(1, math.sqrt(fly_dx * fly_dx + fly_dy * fly_dy))
            fly_ux = fly_dx / fly_len
            fly_uy = fly_dy / fly_len

            # Trail behind dagger.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_velmyrth._alpha(230 - i * 25)
                size = max(1, 6 - i)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_darkest"], alpha),
                    (px, py), size)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (px, py), max(1, size - 1))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                    (px, py), max(1, size - 2))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_light"], alpha),
                    (px, py), max(1, size - 3))

            # Draw actual dagger shape (elongated).
            perp_x = -fly_uy
            perp_y = fly_ux
            # Blade base + tip.
            base_x = bx - int(fly_ux * 6)
            base_y = by - int(fly_uy * 6)
            tip_x = bx + int(fly_ux * 6)
            tip_y = by + int(fly_uy * 6)
            side_a = (bx + int(perp_x * 2), by + int(perp_y * 2))
            side_b = (bx - int(perp_x * 2), by - int(perp_y * 2))

            # Shadow.
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["shadow_deep"], [
                (base_x + 1, base_y + 1),
                (side_a[0] + 1, side_a[1] + 1),
                (tip_x + 1, tip_y + 1),
                (side_b[0] + 1, side_b[1] + 1),
            ])
            # Dark.
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["blade_darkest"], [
                base_x, base_y]) if False else _NS_velmyrth._poly(surface,
                _NS_velmyrth.PALETTE["blade_darkest"], [
                    (base_x, base_y), side_a, (tip_x, tip_y), side_b,
                ])
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["blade_dark"], [
                (base_x, base_y), side_a, (tip_x, tip_y), side_b,
            ])
            _NS_velmyrth._poly(surface, _NS_velmyrth.PALETTE["magic_mid"], [
                (base_x, base_y),
                (int((side_a[0] + tip_x) / 2), int((side_a[1] + tip_y) / 2)),
                (tip_x, tip_y),
                (int((side_b[0] + tip_x) / 2), int((side_b[1] + tip_y) / 2)),
            ])
            # Bright tip.
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))

            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(6 + st * 20)
                alpha = _NS_velmyrth._alpha(240 * (1 - st))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_darkest"], alpha),
                    (tx, ty), radius + 2, 2)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (tx, ty), radius, 2)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                    (tx, ty), max(1, radius - 4), 1)
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_light"], alpha),
                    (tx, ty), max(1, radius - 8), 1)
                # Sparks radiating.
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.8)
                    pygame.draw.rect(surface,
                        (*_NS_velmyrth.PALETTE["magic_hot"], alpha),
                        (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                        (*_NS_velmyrth.PALETTE["magic_shine"], alpha),
                        (ex, ey, 1, 1))

    # ============================================================
    # SKILL: W - PHANTOM STRIKE (teleport dash to target)
    # ============================================================
    def _draw_phantomstrike_ground(surface, boss, x, y, timer, phase):
        """Streak trail from boss to target."""
        facing = boss.direction
        tx, ty = _NS_velmyrth._target_position(boss, x, y)
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.7:
            # Streak of afterimages.
            intensity = math.sin(progress / 0.7 * math.pi)
            for i in range(10):
                t = i / 10
                sx = int(x + (tx - x) * t)
                sy = int(y + (ty - y) * t)
                alpha = _NS_velmyrth._alpha(200 * intensity * (1 - t * 0.3))
                pygame.draw.line(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (sx, sy + 40), (sx, sy + 42), 2)
                pygame.draw.line(surface,
                    (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                    (sx, sy + 40), (sx, sy + 42), 1)

    def _draw_phantomstrike_foreground(surface, boss, x, y, timer, phase):
        """Motion streak + arrival flash + afterimages."""
        facing = boss.direction
        tx, ty = _NS_velmyrth._target_position(boss, x, y)
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Streak of purple energy from boss to target.
            t = progress / 0.4
            intensity = math.sin(t * math.pi)

            # Main streak beam.
            beam_alpha = _NS_velmyrth._alpha(240 * intensity)
            for width, alpha_mult in [(6, 0.4), (4, 0.6), (2, 0.9), (1, 1.0)]:
                pygame.draw.line(surface,
                    (*_NS_velmyrth.PALETTE["magic_mid"],
                     _NS_velmyrth._alpha(beam_alpha * alpha_mult)),
                    (x, y - 5), (tx, ty), width)

            # Central bright core.
            pygame.draw.line(surface,
                (*_NS_velmyrth.PALETTE["magic_shine"], beam_alpha),
                (x, y - 5), (tx, ty), 1)

            # Sparks along streak.
            for i in range(15):
                t_spark = (phase * 3 + i * 0.1) % 1.0
                sx = int(x + (tx - x) * t_spark)
                sy = int(y - 5 + (ty - (y - 5)) * t_spark)
                sy += int(math.sin(phase * 5 + i) * 3)
                spark_alpha = _NS_velmyrth._alpha(240 * intensity * (1 - t_spark * 0.3))
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["magic_hot"], spark_alpha),
                    (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["magic_shine"], spark_alpha),
                    (sx, sy, 1, 1))

            # Afterimages of boss along streak.
            for i in range(4):
                ai_t = i / 4
                ai_x = int(x + (tx - x) * ai_t)
                ai_y = int(y + (ty - y) * ai_t)
                ai_alpha = _NS_velmyrth._alpha(150 * intensity * (1 - ai_t))
                # Simple silhouette.
                for r in range(5, 0, -1):
                    _NS_velmyrth._aacircle(surface,
                        (*_NS_velmyrth.PALETTE["magic_dark"],
                         _NS_velmyrth._alpha(ai_alpha * (5 - r) / 5)),
                        (ai_x, ai_y - 10), r)
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["cloak_dark"], ai_alpha),
                    (ai_x - 3, ai_y - 15, 6, 12))
        elif progress < 0.7:
            # Arrival flash at target.
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)
            flash_r = int(15 + intensity * 25)
            flash_alpha = _NS_velmyrth._alpha(240 * intensity)

            for r in range(flash_r + 3, 0, -2):
                alpha = _NS_velmyrth._alpha(flash_alpha * (flash_r + 3 - r) / (flash_r + 3))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (tx, ty), r)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_mid"], flash_alpha),
                (tx, ty), flash_r // 2)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_light"], flash_alpha),
                (tx, ty), max(1, flash_r // 3))
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_shine"], flash_alpha),
                (tx, ty), max(1, flash_r // 5))

            # Radial sparks.
            for i in range(16):
                angle = i * math.pi / 8
                er = flash_r + 5
                ex = tx + int(math.cos(angle) * er)
                ey = ty + int(math.sin(angle) * er)
                pygame.draw.line(surface,
                    (*_NS_velmyrth.PALETTE["magic_hot"], flash_alpha),
                    (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["magic_shine"], flash_alpha),
                    (ex, ey, 1, 1))

    # ============================================================
    # SKILL: E - BLUR (invisibility, MISSED text effect)
    # ============================================================
    def _draw_blur_ground(surface, boss, x, y, timer, phase):
        """Ripple rings under boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(28 + i * 6 + math.sin(phase * 2 + i) * 2)
            alpha = _NS_velmyrth._alpha(160 - i * 40)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                (x, y + 40), r, 1)

    def _draw_blur_foreground(surface, boss, x, y, timer, phase):
        """Distortion effect + occasional 'MISSED' text."""
        # Simple distortion sparkles around boss.
        for i in range(15):
            angle = i * math.pi / 7.5 + phase * 0.4
            r = 35 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.6)
            alpha = _NS_velmyrth._alpha(180 + math.sin(phase * 3 + i) * 60)
            pygame.draw.rect(surface,
                (*_NS_velmyrth.PALETTE["magic_light"], alpha), (sx, sy, 1, 1))

        # Ghostly afterimages trailing.
        for i in range(3):
            ai_offset = (i + 1) * 12
            ai_x = x - boss.direction * ai_offset
            ai_alpha = _NS_velmyrth._alpha(80 - i * 20)
            # Simplified silhouette.
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["cloak_mid"], ai_alpha),
                (ai_x, y - 15), 6)
            pygame.draw.rect(surface,
                (*_NS_velmyrth.PALETTE["cloak_dark"], ai_alpha),
                (ai_x - 4, y - 10, 8, 20))

    # ============================================================
    # SKILL: R - COUP DE GRACE (critical strike enhancement)
    # ============================================================
    def _draw_coupdegrace_ground(surface, boss, x, y, timer, phase):
        """Intense purple ring on ground."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple rings pulsing.
        for i in range(3):
            r = int(35 + i * 8 + math.sin(phase * 3 + i) * 4)
            alpha = _NS_velmyrth._alpha(200 - i * 40)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                (x, y + 40), r, 2)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                (x, y + 40), r, 1)

        # Runic symbols floating.
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.5
            rr = 42
            sx = x + int(math.cos(angle) * rr)
            sy = y + 40 + int(math.sin(angle) * rr * 0.4)
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                             (sx, sy, 1, 1))

    def _draw_coupdegrace_foreground(surface, boss, x, y, timer, phase):
        """Massive purple slash + CRITICAL burst."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge phase: energy gathers around boss.
            t = progress / 0.3
            for i in range(12):
                angle = i * math.pi / 6 + phase * 3
                r = int((1 - t) * 30 + 10)
                sx = x + int(math.cos(angle) * r)
                sy = y - 5 + int(math.sin(angle) * r)
                pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_hot"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_velmyrth.PALETTE["magic_shine"],
                                 (sx, sy, 1, 1))

            # Both blades glow intensely.
            for i in range(2):
                blade_x = x + facing * (12 + i * 4)
                blade_y = y - 5 + i * 3
                for r in range(6, 0, -1):
                    alpha = _NS_velmyrth._alpha(180 * t * (6 - r) / 6)
                    _NS_velmyrth._aacircle(surface,
                        (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                        (blade_x, blade_y), r)
        elif progress < 0.65:
            # STRIKE! Massive slash arc + huge burst.
            t = (progress - 0.3) / 0.35
            intensity = math.sin(t * math.pi)

            # Big crescent arc slash in front.
            center_x = x
            center_y = y - 5
            radius = 55 + int(t * 15)
            arc_alpha = _NS_velmyrth._alpha(240 * intensity)

            arc_points = []
            arc_start = -math.pi / 2.5
            arc_end = math.pi / 2.5
            for i in range(20):
                arc_t = i / 19
                angle = arc_start + (arc_end - arc_start) * arc_t
                ax = center_x + int(math.cos(angle) * radius) * facing
                ay = center_y + int(math.sin(angle) * radius)
                arc_points.append((ax, ay))

            # Layered arc.
            for i in range(len(arc_points) - 1):
                _NS_velmyrth._aaline(surface,
                    (*_NS_velmyrth.PALETTE["magic_darkest"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 8)
                _NS_velmyrth._aaline(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 6)
                _NS_velmyrth._aaline(surface,
                    (*_NS_velmyrth.PALETTE["magic_mid"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 4)
                _NS_velmyrth._aaline(surface,
                    (*_NS_velmyrth.PALETTE["magic_light"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 2)
                _NS_velmyrth._aaline(surface,
                    (*_NS_velmyrth.PALETTE["magic_shine"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 1)

            # Bright sparks along arc.
            for i, pt in enumerate(arc_points):
                if i % 2 == 0:
                    pygame.draw.rect(surface,
                        (*_NS_velmyrth.PALETTE["white"], arc_alpha),
                        (pt[0], pt[1], 2, 2))

            # Impact burst at arc center-front.
            impact_x = x + facing * 55
            impact_y = y
            imp_r = int(15 + intensity * 25)
            imp_alpha = _NS_velmyrth._alpha(240 * intensity)

            for r in range(imp_r + 3, 0, -2):
                alpha = _NS_velmyrth._alpha(imp_alpha * (imp_r + 3 - r) / (imp_r + 3))
                _NS_velmyrth._aacircle(surface,
                    (*_NS_velmyrth.PALETTE["magic_dark"], alpha),
                    (impact_x, impact_y), r)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_mid"], imp_alpha),
                (impact_x, impact_y), imp_r // 2)
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_light"], imp_alpha),
                (impact_x, impact_y), max(1, imp_r // 3))
            _NS_velmyrth._aacircle(surface,
                (*_NS_velmyrth.PALETTE["magic_shine"], imp_alpha),
                (impact_x, impact_y), max(1, imp_r // 5))
            pygame.draw.rect(surface,
                (*_NS_velmyrth.PALETTE["white"], imp_alpha),
                (impact_x, impact_y, 2, 2))

            # Radial burst lines.
            for i in range(16):
                angle_s = i * math.pi / 8
                er = imp_r + 10
                ex = impact_x + int(math.cos(angle_s) * er)
                ey = impact_y + int(math.sin(angle_s) * er)
                pygame.draw.line(surface,
                    (*_NS_velmyrth.PALETTE["magic_light"], imp_alpha),
                    (impact_x, impact_y), (ex, ey), 2)
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["magic_shine"], imp_alpha),
                    (ex, ey, 2, 2))

            # "CRITICAL!" text effect (just visual sparks in a cluster).
            if t > 0.3:
                text_alpha = _NS_velmyrth._alpha(240 * intensity)
                text_x = impact_x
                text_y = impact_y - 30
                # Draw ! symbol.
                for i in range(3):
                    pygame.draw.rect(surface,
                        (*_NS_velmyrth.PALETTE["magic_hot"], text_alpha),
                        (text_x - 1, text_y - i * 4, 2, 3))
                pygame.draw.rect(surface,
                    (*_NS_velmyrth.PALETTE["magic_shine"], text_alpha),
                    (text_x - 1, text_y + 6, 2, 2))
        else:
            # Aftermath: purple sparks lingering.
            t = (progress - 0.65) / 0.35
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = x + facing * 40 + int(math.sin(phase + i) * 30)
                ry = y - int(rise_t * 30)
                alpha = _NS_velmyrth._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface,
                        (*_NS_velmyrth.PALETTE["magic_mid"], alpha),
                        (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                        (*_NS_velmyrth.PALETTE["magic_hot"], alpha),
                        (rx, ry, 1, 1))


# ====================================================================
# solvarin.py
# ====================================================================

# ====================================================================
# SOLVARIN - THE RADIANT WARDEN (True Boss Holy Paladin)
# ====================================================================


class _NS_solvarin:
    """Namespace solvarin - True Boss Holy Paladin Warden."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # White-silver armor (main)
        "silver_darkest": (35, 40, 50),
        "silver_dark": (85, 90, 105),
        "silver_mid": (155, 160, 175),
        "silver_light": (215, 220, 230),
        "silver_shine": (250, 252, 255),

        # Gold trim (accent armor)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (110, 75, 15),
        "gold_mid": (200, 150, 45),
        "gold_light": (250, 210, 100),
        "gold_shine": (255, 245, 180),
        "gold_white": (255, 255, 230),

        # Blue tabard/cloth
        "blue_darkest": (10, 20, 45),
        "blue_dark": (25, 50, 105),
        "blue_mid": (55, 105, 180),
        "blue_light": (130, 180, 235),
        "blue_edge": (200, 225, 250),

        # Yellow-gold cape
        "cape_darkest": (55, 40, 10),
        "cape_dark": (135, 100, 25),
        "cape_mid": (215, 175, 60),
        "cape_light": (250, 220, 130),
        "cape_edge": (255, 245, 190),

        # Skin (paladin fair)
        "skin_darkest": (60, 45, 40),
        "skin_dark": (125, 95, 80),
        "skin_mid": (195, 160, 135),
        "skin_light": (240, 215, 190),
        "skin_shine": (255, 240, 220),

        # Warhammer metal (steel + gold)
        "hammer_darkest": (15, 15, 20),
        "hammer_dark": (55, 55, 65),
        "hammer_mid": (115, 115, 130),
        "hammer_light": (190, 190, 205),
        "hammer_shine": (245, 245, 250),

        # Holy light (bright divine yellow-white)
        "holy_darkest": (60, 45, 10),
        "holy_dark": (155, 115, 25),
        "holy_mid": (250, 210, 80),
        "holy_light": (255, 240, 160),
        "holy_hot": (255, 250, 210),
        "holy_shine": (255, 255, 250),

        # Green heal (Q skill)
        "heal_dark": (20, 80, 40),
        "heal_mid": (60, 180, 90),
        "heal_light": (140, 240, 160),
        "heal_shine": (220, 255, 230),

        # Eye (bright blue/white paladin)
        "eye_socket": (5, 10, 20),
        "eye_dark": (30, 60, 120),
        "eye_mid": (140, 190, 240),
        "eye_light": (220, 240, 255),
        "eye_glow": (255, 255, 255),

        # Cross/religious accent (red)
        "cross_dark": (100, 20, 25),
        "cross_mid": (200, 45, 50),
        "cross_light": (255, 130, 120),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_solvarin._clamp(color)
        if _NS_solvarin.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_solvarin._clamp(color)
        if _NS_solvarin.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_solvarin._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_solvarin._clamp(color), points)

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
    def draw_solvarin(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_solvarin._detect_moving(boss)
        _NS_solvarin._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_sol_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_solvarin._draw_holy_aura(surface, x, y, pulse)
        _NS_solvarin._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_solvarin._draw_repel_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_solvarin._draw_degen_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_solvarin._draw_guardian_ground(surface, boss, x, y, skill_timer, pulse)

        # Guardian Angel WINGS behind body!
        if active_skill == "r":
            _NS_solvarin._draw_guardian_wings(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_solvarin._draw_sol_attack(surface, boss, x, y)
        elif moving:
            _NS_solvarin._draw_sol_float(surface, boss, x, y)
        else:
            _NS_solvarin._draw_sol_idle(surface, boss, x, y)

        # Repel shield bubble (over body).
        if active_skill == "w":
            _NS_solvarin._draw_repel_bubble(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_solvarin._draw_purification_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_solvarin._draw_degen_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_solvarin._draw_guardian_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sol_previous_timer", 0))
        active = bool(getattr(boss, "_sol_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._sol_attack_active = True
            boss._sol_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._sol_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._sol_attack_frame = int(getattr(boss, "_sol_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._sol_attack_active = False
            boss._sol_attack_frame = 0
            active = False

        boss._sol_previous_timer = timer
        boss._sol_attack_progress = (
            min(1.0, getattr(boss, "_sol_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_sol_last_x"):
            boss._sol_last_x = boss.x
            boss._sol_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sol_last_x)
        dy = abs(boss.y - boss._sol_last_y)
        boss._sol_last_x = boss.x
        boss._sol_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_sol_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_solvarin._draw_shadow(surface, x, y + 55)
        _NS_solvarin._draw_holy_wisps(surface, x, y + 40, boss.pulse)
        _NS_solvarin._draw_sol_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_sol_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_solvarin._draw_shadow(surface, x + sway, y + 55)
        _NS_solvarin._draw_holy_wisps(surface, x + sway, y + 40, phase,
                                       trail=True, facing=boss.direction)
        _NS_solvarin._draw_sol_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")

    def _draw_sol_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_sol_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_sol_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # HAMMER SMASH: overhead raise → downward smash → recovery.
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 4) * facing
            lift = int(t * 8)
        elif progress < 0.6:
            # Explosive smash down.
            t = (progress - 0.4) / 0.2
            lunge = int((-4 + t * 12)) * facing
            lift = int(8 - t * 12)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(8 * (1 - t)) * facing
            lift = int(-4 + t * 4)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_solvarin._draw_shadow(surface, x + lunge, y + 55)
        _NS_solvarin._draw_holy_wisps(surface, x + lunge, y + 40, boss.pulse,
                                       intense=True)
        _NS_solvarin._draw_sol_body(surface, x + lunge, y - lift + bob,
                                     facing, boss.pulse, "attack",
                                     progress)

    # ============================================================
    # BODY
    # ============================================================
    def _draw_sol_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Paladin body with warhammer + wing helm."""
        # Cape behind body.
        _NS_solvarin._draw_cape(surface, cx, cy, facing, phase)

        # Lower body (silver greaves + blue tabard).
        _NS_solvarin._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso (silver breastplate + gold trim).
        _NS_solvarin._draw_torso(surface, cx, cy, facing, phase)

        # Compute hammer swing angle.
        hammer_angle = 0
        if action == "attack":
            if attack_progress < 0.4:
                # Wind-up: raise back overhead.
                t = attack_progress / 0.4
                hammer_angle = -math.pi * 0.4 * t  # tilt back
            elif attack_progress < 0.6:
                # Downward smash.
                t = (attack_progress - 0.4) / 0.2
                hammer_angle = -math.pi * 0.4 + math.pi * 1.2 * t
            else:
                # Return to shoulder.
                t = (attack_progress - 0.6) / 0.4
                hammer_angle = math.pi * 0.8 * (1 - t)

        # Back arm.
        _NS_solvarin._draw_back_arm(surface, cx, cy - 4, facing, phase, action)

        # Head with wing helm.
        _NS_solvarin._draw_wing_helm_head(surface, cx + facing * 2, cy - 22,
                                           facing, phase, action, attack_progress)

        # Front arm with warhammer.
        _NS_solvarin._draw_hammer_arm(surface, cx, cy - 4, facing, phase,
                                       action, hammer_angle, attack_progress)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Yellow-gold paladin cape."""
        wave = math.sin(phase * 0.7) * 3

        cape = [
            (cx - facing * 9, cy - 13),
            (cx - facing * 17 + int(wave), cy - 6),
            (cx - facing * 21 + int(wave), cy + 8),
            (cx - facing * 19 + int(wave * 0.5), cy + 22),
            (cx - facing * 13, cy + 32 + int(wave * 0.5)),
            (cx - facing * 3, cy + 34),
            (cx + facing * 3, cy + 30),
            (cx + facing * 5, cy + 14),
            (cx - facing * 2, cy - 11),
        ]
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in cape])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["cape_darkest"], cape)
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["cape_dark"], [
            (cx - facing * 8, cy - 12),
            (cx - facing * 16 + int(wave), cy - 5),
            (cx - facing * 20 + int(wave), cy + 7),
            (cx - facing * 18 + int(wave * 0.5), cy + 21),
            (cx - facing * 12, cy + 30 + int(wave * 0.5)),
            (cx - facing * 3, cy + 32),
            (cx + facing * 3, cy + 28),
            (cx + facing * 4, cy + 13),
            (cx - facing * 2, cy - 10),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["cape_mid"], [
            (cx - facing * 11, cy - 7),
            (cx - facing * 16 + int(wave * 0.7), cy),
            (cx - facing * 14 + int(wave * 0.5), cy + 18),
            (cx - facing * 5, cy + 24),
            (cx - facing * 2, cy + 12),
            (cx - facing * 6, cy - 4),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["cape_light"], [
            (cx - facing * 8, cy - 4),
            (cx - facing * 12 + int(wave * 0.5), cy + 4),
            (cx - facing * 10 + int(wave * 0.3), cy + 12),
            (cx - facing * 5, cy + 8),
        ])

        # Silver trim along cape edge.
        edge_pts = [
            (cx - facing * 17 + int(wave), cy - 6),
            (cx - facing * 21 + int(wave), cy + 8),
            (cx - facing * 19 + int(wave * 0.5), cy + 22),
            (cx - facing * 13, cy + 32 + int(wave * 0.5)),
        ]
        for i in range(len(edge_pts) - 1):
            _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_dark"],
                                  edge_pts[i], edge_pts[i + 1], 2)
            _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_light"],
                                  edge_pts[i], edge_pts[i + 1], 1)

        # Fold shadows.
        for i, dx in enumerate((-4, 2, 8)):
            wave_off = math.sin(phase * 0.7 + i) * 1
            offset_x = cx - facing * dx
            pygame.draw.line(surface, _NS_solvarin.PALETTE["cape_darkest"],
                             (offset_x, cy - 2),
                             (offset_x - facing * 3 + int(wave_off),
                              cy + 26), 1)

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Silver hip armor + blue tabard + silver greaves."""
        wave = math.sin(phase * 0.9) * 2

        # Silver hip plate.
        hip = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 4),
            (cx - 10, cy + 4),
            (cx - 12, cy),
        ]
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hip])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_darkest"], hip)
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_dark"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5), (cx + 11, cy),
            (cx + 9, cy + 3), (cx - 9, cy + 3), (cx - 11, cy),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_mid"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3), (cx + 9, cy),
            (cx + 7, cy + 2), (cx - 7, cy + 2), (cx - 9, cy),
        ])
        # Gold trim.
        pygame.draw.line(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 10, cy + 4), (cx + 10, cy + 4), 1)
        pygame.draw.line(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (cx - 9, cy + 4), (cx + 9, cy + 4), 1)

        # Central belt buckle (gold + holy gem).
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 3, cy - 3, 7, 6))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (cx - 2, cy - 2, 5, 5))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_dark"],
                         (cx - 1, cy - 1, 3, 3))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_mid"],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_light"],
                         (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_shine"],
                         (cx, cy - 1, 1, 1))

        # BLUE TABARD (long cloth panel hanging in center).
        tabard_pts = [
            (cx - 5, cy + 3),
            (cx + 5, cy + 3),
            (cx + 6 + int(wave * 0.3), cy + 18),
            (cx + 4, cy + 24),
            (cx - 4, cy + 24),
            (cx - 6 + int(wave * 0.3), cy + 18),
        ]
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in tabard_pts])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["blue_darkest"],
                            tabard_pts)
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["blue_dark"], [
            (cx - 4, cy + 4), (cx + 4, cy + 4),
            (cx + 5 + int(wave * 0.3), cy + 17), (cx + 3, cy + 23),
            (cx - 3, cy + 23), (cx - 5 + int(wave * 0.3), cy + 17),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["blue_mid"], [
            (cx - 3, cy + 6), (cx + 3, cy + 6),
            (cx + 3, cy + 16), (cx - 3, cy + 16),
        ])
        # Gold cross emblem on tabard.
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 1, cy + 10, 3, 8))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 3, cy + 12, 7, 3))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (cx - 1, cy + 10, 2, 7))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (cx - 3, cy + 12, 6, 2))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                         (cx, cy + 12, 1, 1))
        # Gold trim on tabard edge.
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              (cx - 5, cy + 3),
                              (cx - 6 + int(wave * 0.3), cy + 18), 1)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              (cx + 5, cy + 3),
                              (cx + 6 + int(wave * 0.3), cy + 18), 1)

        # Legs (silver greaves visible on sides).
        for side in (-1, 1):
            lx = cx + side * 7
            ly1 = cy + 4
            ly2 = cy + 24
            pygame.draw.line(surface, _NS_solvarin.PALETTE["shadow_deep"],
                             (lx + 2, ly1 + 2), (lx + 2, ly2 + 2), 6)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_darkest"],
                             (lx, ly1), (lx, ly2), 5)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_dark"],
                             (lx, ly1), (lx, ly2), 4)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_mid"],
                             (lx + side, ly1), (lx + side, ly2), 2)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_light"],
                             (lx + side, ly1), (lx + side, ly2 - 2), 1)
            # Gold knee accent.
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                             (lx - 2, ly1 + 8, 5, 3))
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                             (lx - 1, ly1 + 8, 3, 2))
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                             (lx, ly1 + 8, 1, 1))

            # Boot at bottom (silver + gold).
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"], [
                (lx - 3, ly2), (lx + 3, ly2),
                (lx + 4, ly2 + 3), (lx - 4, ly2 + 3),
            ])
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_darkest"], [
                (lx - 2, ly2 - 1), (lx + 2, ly2 - 1),
                (lx + 3, ly2 + 2), (lx - 3, ly2 + 2),
            ])
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_mid"], [
                (lx - 2, ly2), (lx + 2, ly2),
                (lx + 2, ly2 + 1), (lx - 2, ly2 + 1),
            ])
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                             (lx, ly2, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Silver breastplate with gold trim + blue accents."""
        breath = math.sin(phase * 0.7) * 1

        # Under-tunic (blue visible around edges).
        torso = [
            (cx - 12, cy - 14),
            (cx - 14, cy - 8),
            (cx - 13, cy),
            (cx - 11, cy + 8),
            (cx - 9, cy + 14),
            (cx + 9, cy + 14),
            (cx + 11, cy + 8),
            (cx + 13, cy),
            (cx + 14, cy - 8),
            (cx + 12, cy - 14),
        ]
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["blue_darkest"], torso)
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["blue_dark"], [
            (cx - 11, cy - 13), (cx - 13, cy - 7), (cx - 12, cy),
            (cx - 10, cy + 7), (cx - 8, cy + 13),
            (cx + 8, cy + 13), (cx + 10, cy + 7), (cx + 12, cy),
            (cx + 13, cy - 7), (cx + 11, cy - 13),
        ])

        # Silver breastplate (main plate).
        chest = [
            (cx - 11, cy - 12),
            (cx + 11, cy - 12),
            (cx + 13, cy - 4),
            (cx + 10, cy + 6),
            (cx + 5, cy + 10),
            (cx - 5, cy + 10),
            (cx - 10, cy + 6),
            (cx - 13, cy - 4),
        ]
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_darkest"], chest)
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_dark"], [
            (cx - 10, cy - 11), (cx + 10, cy - 11), (cx + 12, cy - 4),
            (cx + 9, cy + 5), (cx + 4, cy + 9), (cx - 4, cy + 9),
            (cx - 9, cy + 5), (cx - 12, cy - 4),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_mid"], [
            (cx - 8, cy - 9), (cx + 8, cy - 9), (cx + 10, cy - 3),
            (cx + 7, cy + 3), (cx + 3, cy + 7), (cx - 3, cy + 7),
            (cx - 7, cy + 3), (cx - 10, cy - 3),
        ])

        # Muscle ridges on chest.
        pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_darkest"],
                         (cx - 5, cy - 4), (cx + 5, cy - 4), 1)
        pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_light"],
                         (cx - 5, cy - 5), (cx + 5, cy - 5), 1)
        # Center line.
        pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_darkest"],
                         (cx, cy - 10), (cx, cy + 5), 1)
        # Abs.
        for i in range(2):
            y_ab = cy + i * 4
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_darkest"],
                             (cx - 5, y_ab), (cx - 1, y_ab), 1)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_darkest"],
                             (cx + 1, y_ab), (cx + 5, y_ab), 1)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_light"],
                             (cx - 5, y_ab - 1), (cx - 1, y_ab - 1), 1)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["silver_light"],
                             (cx + 1, y_ab - 1), (cx + 5, y_ab - 1), 1)

        # Gold trim along chest edges.
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              (cx - 11, cy - 12), (cx + 11, cy - 12), 2)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_mid"],
                              (cx - 11, cy - 12), (cx + 11, cy - 12), 1)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              (cx - 13, cy - 4), (cx - 10, cy + 6), 1)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              (cx + 13, cy - 4), (cx + 10, cy + 6), 1)

        # Highlight (top-front).
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_light"], [
            (cx + facing * 2, cy - 8),
            (cx + facing * 6, cy - 5),
            (cx + facing * 5, cy - 1),
            (cx + facing * 1, cy - 3 + int(breath)),
        ])
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["silver_shine"],
                         (cx + facing * 4, cy - 7, 1, 1))

        # Central HOLY GEM (glowing yellow).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_solvarin._alpha(180 * pulse * (5 - r) / 5)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_mid"], alpha),
                (cx, cy - 7), r)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 2, cy - 8, 5, 4))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_darkest"],
                         (cx - 1, cy - 8, 3, 3))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_dark"],
                         (cx - 1, cy - 8, 2, 2))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_mid"],
                         (cx, cy - 8, 1, 1))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_shine"],
                         (cx, cy - 8, 1, 1))

        # Shoulder pauldrons (large gold with silver core).
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 11
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["shadow_deep"],
                                     (sh_x + 1, sh_y + 1), 7)
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_darkest"],
                                     (sh_x, sh_y), 7)
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_dark"],
                                     (sh_x, sh_y), 6)
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_mid"],
                                     (sh_x + side, sh_y - 1), 4)
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_light"],
                                     (sh_x + side, sh_y - 1), 2)
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                             (sh_x + side, sh_y - 2, 1, 1))
            # Small holy gem in pauldron.
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_mid"],
                             (sh_x, sh_y, 1, 1))
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_shine"],
                             (sh_x, sh_y, 1, 1))
            # Small feather-like decoration on pauldron.
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_light"], [
                (sh_x + side * 4, sh_y - 4),
                (sh_x + side * 7, sh_y - 8),
                (sh_x + side * 5, sh_y - 3),
            ])
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_shine"], [
                (sh_x + side * 4, sh_y - 4),
                (sh_x + side * 6, sh_y - 6),
                (sh_x + side * 5, sh_y - 3),
            ])

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 1
        sh_x = cx - facing * 10
        sh_y = cy
        elb_x = cx - facing * 13
        elb_y = cy + 9 + int(sway)
        hand_x = cx - facing * 10
        hand_y = cy + 18

        # Upper arm (silver + gold band).
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 7)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_mid"],
                              (sh_x - facing, sh_y - 1),
                              (elb_x - facing, elb_y - 1), 2)

        # Gold arm band.
        band_mid = ((sh_x + elb_x) // 2, (sh_y + elb_y) // 2)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_dark"],
                                 band_mid, 3)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_mid"],
                                 band_mid, 2)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                         (band_mid[0], band_mid[1], 1, 1))

        # Forearm (silver gauntlet).
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 6)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 4)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_mid"],
                              (elb_x, elb_y), (hand_x, hand_y), 1)

        # Fist.
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["silver_darkest"],
                                 (hand_x, hand_y), 3)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["silver_dark"],
                                 (hand_x, hand_y), 2)

    def _draw_hammer_arm(surface, cx, cy, facing, phase, action, hammer_angle,
                          attack_progress):
        """Front arm holding the warhammer."""
        sh_x = cx + facing * 11
        sh_y = cy

        # Arm position based on hammer angle.
        arm_base = -math.pi * 0.15 + hammer_angle * 0.5
        elb_x = sh_x + int(math.cos(arm_base) * 10) * facing
        elb_y = sh_y + int(math.sin(arm_base) * 10) + 4

        grip_angle = arm_base + hammer_angle * 0.4
        hand_x = elb_x + int(math.cos(grip_angle) * 12) * facing
        hand_y = elb_y + int(math.sin(grip_angle) * 12)

        # Upper arm (silver).
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 8)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 7)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_mid"],
                              (sh_x + facing, sh_y - 1),
                              (elb_x + facing, elb_y - 1), 3)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_light"],
                              (sh_x + facing, sh_y - 2),
                              (elb_x + facing, elb_y - 2), 1)

        # Gold arm band.
        band_mid = ((sh_x + elb_x) // 2, (sh_y + elb_y) // 2)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_dark"],
                                 band_mid, 3)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_mid"],
                                 band_mid, 2)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                         (band_mid[0], band_mid[1], 1, 1))

        # Forearm (silver gauntlet with gold).
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 7)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 6)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_mid"],
                              (elb_x, elb_y), (hand_x, hand_y), 2)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_light"],
                              (elb_x + facing, elb_y - 1),
                              (hand_x + facing, hand_y - 1), 1)

        # Fist gripping hammer.
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["silver_darkest"],
                                 (hand_x, hand_y), 5)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["silver_dark"],
                                 (hand_x, hand_y), 4)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["silver_mid"],
                                 (hand_x, hand_y - 1), 3)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (hand_x, hand_y, 1, 1))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["silver_shine"],
                         (hand_x, hand_y - 1, 1, 1))

        # Draw warhammer.
        _NS_solvarin._draw_warhammer(surface, hand_x, hand_y, facing, phase,
                                      hammer_angle, action, attack_progress)

    def _draw_warhammer(surface, hx, hy, facing, phase, angle, action,
                          attack_progress):
        """Big warhammer with square/rectangular head."""
        # Hammer default points UP (over shoulder).
        base_angle = -math.pi * 0.5 + angle

        shaft_len = 34
        # Direction.
        dx = math.cos(base_angle) * facing
        dy = math.sin(base_angle)

        # Butt (below hand).
        butt_x = hx - int(dx * 10)
        butt_y = hy - int(dy * 10)

        # Head position (top of shaft).
        head_x = hx + int(dx * shaft_len)
        head_y = hy + int(dy * shaft_len)

        # Perpendicular for width.
        perp_x = -math.sin(base_angle) * facing
        perp_y = math.cos(base_angle)

        # SHADOW SHAFT.
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["shadow_deep"],
                              (butt_x + 2, butt_y + 2),
                              (head_x + 2, head_y + 2), 4)
        # Shaft (silver metal + gold accents).
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["hammer_darkest"],
                              (butt_x, butt_y), (head_x, head_y), 3)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["hammer_dark"],
                              (butt_x, butt_y), (head_x, head_y), 2)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["hammer_mid"],
                              (butt_x, butt_y), (head_x, head_y), 1)

        # Gold binding rings.
        for i in range(1, 5):
            t = i / 5
            wx = int(butt_x + (head_x - butt_x) * t)
            wy = int(butt_y + (head_y - butt_y) * t)
            pygame.draw.line(surface, _NS_solvarin.PALETTE["gold_dark"],
                             (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                             (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)

        # POMMEL (small gold at butt).
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["shadow_deep"],
                                 (butt_x + 1, butt_y + 1), 3)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_dark"],
                                 (butt_x, butt_y), 3)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["gold_mid"],
                                 (butt_x, butt_y), 2)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                         (butt_x, butt_y, 1, 1))

        # WARHAMMER HEAD (large square/rectangular block).
        # Head is a rectangle centered at head position, oriented perpendicular
        # to shaft.
        head_width = 8  # perpendicular to shaft
        head_length = 14  # along perpendicular (wider)

        # 4 corners of hammer head.
        c1 = (head_x + int(perp_x * head_length) + int(dx * head_width),
              head_y + int(perp_y * head_length) + int(dy * head_width))
        c2 = (head_x + int(perp_x * head_length) - int(dx * head_width),
              head_y + int(perp_y * head_length) - int(dy * head_width))
        c3 = (head_x - int(perp_x * head_length) - int(dx * head_width),
              head_y - int(perp_y * head_length) - int(dy * head_width))
        c4 = (head_x - int(perp_x * head_length) + int(dx * head_width),
              head_y - int(perp_y * head_length) + int(dy * head_width))

        # Shadow.
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"], [
            (c1[0] + 2, c1[1] + 2), (c2[0] + 2, c2[1] + 2),
            (c3[0] + 2, c3[1] + 2), (c4[0] + 2, c4[1] + 2),
        ])
        # Dark base.
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["hammer_darkest"],
                            [c1, c2, c3, c4])
        # Mid layer.
        inner_c1 = (int(c1[0] * 0.85 + head_x * 0.15),
                    int(c1[1] * 0.85 + head_y * 0.15))
        inner_c2 = (int(c2[0] * 0.85 + head_x * 0.15),
                    int(c2[1] * 0.85 + head_y * 0.15))
        inner_c3 = (int(c3[0] * 0.85 + head_x * 0.15),
                    int(c3[1] * 0.85 + head_y * 0.15))
        inner_c4 = (int(c4[0] * 0.85 + head_x * 0.15),
                    int(c4[1] * 0.85 + head_y * 0.15))
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["hammer_dark"],
                            [inner_c1, inner_c2, inner_c3, inner_c4])
        # Bright layer.
        inner2_c1 = (int(c1[0] * 0.7 + head_x * 0.3),
                     int(c1[1] * 0.7 + head_y * 0.3))
        inner2_c2 = (int(c2[0] * 0.7 + head_x * 0.3),
                     int(c2[1] * 0.7 + head_y * 0.3))
        inner2_c3 = (int(c3[0] * 0.7 + head_x * 0.3),
                     int(c3[1] * 0.7 + head_y * 0.3))
        inner2_c4 = (int(c4[0] * 0.7 + head_x * 0.3),
                     int(c4[1] * 0.7 + head_y * 0.3))
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["hammer_mid"],
                            [inner2_c1, inner2_c2, inner2_c3, inner2_c4])

        # Gold trim on edges (top and side).
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              c1, c2, 2)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_mid"],
                              c1, c2, 1)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              c3, c4, 2)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_mid"],
                              c3, c4, 1)

        # Central highlight.
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["hammer_light"],
                                 (head_x + int(perp_x * head_length * 0.5),
                                  head_y + int(perp_y * head_length * 0.5)), 2)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["hammer_shine"],
                                 (head_x + int(perp_x * head_length * 0.5),
                                  head_y + int(perp_y * head_length * 0.5)), 1)

        # Central HOLY GEM/CROSS on hammer head (glowing).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_solvarin._alpha(240 * pulse)
        for r in range(4, 0, -1):
            alpha = _NS_solvarin._alpha(180 * pulse * (4 - r) / 4)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_mid"], alpha),
                (head_x, head_y), r)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (head_x - 2, head_y - 2, 5, 5))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_dark"],
                         (head_x - 1, head_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_mid"],
                         (head_x - 1, head_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_light"],
                         (head_x, head_y, 1, 1))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_shine"],
                         (head_x, head_y, 1, 1))

        # Small spikes on top of hammer head.
        for spike_side in (-1, 1):
            spike_base_x = head_x + int(perp_x * head_length * spike_side * 0.6)
            spike_base_y = head_y + int(perp_y * head_length * spike_side * 0.6)
            spike_tip_x = spike_base_x + int(dx * (head_width + 4))
            spike_tip_y = spike_base_y + int(dy * (head_width + 4))
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["hammer_darkest"], [
                (spike_tip_x, spike_tip_y),
                (spike_base_x + int(perp_x * 2 * spike_side),
                 spike_base_y + int(perp_y * 2 * spike_side)),
                (spike_base_x - int(perp_x * 2 * spike_side),
                 spike_base_y - int(perp_y * 2 * spike_side)),
            ])
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["hammer_mid"], [
                (spike_tip_x, spike_tip_y),
                (spike_base_x + int(perp_x * spike_side),
                 spike_base_y + int(perp_y * spike_side)),
                (spike_base_x, spike_base_y),
            ])
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["hammer_shine"],
                             (spike_tip_x, spike_tip_y, 1, 1))

        # SMASH STREAK during attack.
        if action == "attack" and 0.4 < attack_progress < 0.7:
            streak_intensity = math.sin((attack_progress - 0.4) / 0.3 * math.pi)
            streak_alpha = _NS_solvarin._alpha(230 * streak_intensity)

            # Vertical smash trail behind hammer.
            arc_start = base_angle - 0.3
            arc_end = base_angle
            for i in range(8):
                arc_t = i / 8
                trail_angle = arc_start + (arc_end - arc_start) * arc_t
                trail_dx = math.cos(trail_angle) * facing
                trail_dy = math.sin(trail_angle)
                trail_len = shaft_len + 10
                trail_x = hx + int(trail_dx * trail_len)
                trail_y = hy + int(trail_dy * trail_len)

                alpha_t = _NS_solvarin._alpha(streak_alpha * (1 - arc_t) * 0.8)
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_dark"], alpha_t),
                    (trail_x, trail_y), 5)
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_mid"], alpha_t),
                    (trail_x, trail_y), 3)
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_light"], alpha_t),
                    (trail_x, trail_y), 1)

    def _draw_wing_helm_head(surface, cx, cy, facing, phase, action,
                              attack_progress):
        """Wing helm (helm with side wings) + face + white beard-less."""
        _NS_solvarin._draw_wing_helm(surface, cx, cy, facing, phase)
        _NS_solvarin._draw_face(surface, cx, cy, facing, phase)
        _NS_solvarin._draw_helm_eye(surface, cx + facing * 2, cy - 3,
                                     facing, phase, action, attack_progress)

    def _draw_wing_helm(surface, cx, cy, facing, phase):
        """Silver+gold helm with WING protrusions on sides."""
        # Helm dome.
        helm = [
            (cx - 8, cy + 3),
            (cx - 10, cy - 2),
            (cx - 10, cy - 9),
            (cx - 6, cy - 13),
            (cx + 6, cy - 13),
            (cx + 10, cy - 9),
            (cx + 10, cy - 2),
            (cx + 8, cy + 3),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
        ]
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in helm])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_darkest"], helm)
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_dark"], [
            (cx - 7, cy + 2), (cx - 9, cy - 2), (cx - 9, cy - 8),
            (cx - 5, cy - 12), (cx + 5, cy - 12), (cx + 9, cy - 8),
            (cx + 9, cy - 2), (cx + 7, cy + 2),
            (cx + 5, cy + 4), (cx - 5, cy + 4),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_mid"], [
            (cx - 6, cy - 5), (cx - 8, cy - 7), (cx - 6, cy - 11),
            (cx - 2, cy - 12), (cx + 2, cy - 12), (cx + 6, cy - 11),
            (cx + 8, cy - 7), (cx + 6, cy - 5),
        ])

        # Highlight on helm (top-facing side).
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_light"], [
            (cx + facing * 2, cy - 10),
            (cx + facing * 6, cy - 7),
            (cx + facing * 5, cy - 3),
            (cx + facing * 1, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["silver_shine"],
                         (cx + facing * 5, cy - 8, 1, 1))

        # Gold trim on helm edges.
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_dark"],
                              (cx - 8, cy + 3), (cx + 8, cy + 3), 2)
        _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["gold_mid"],
                              (cx - 8, cy + 3), (cx + 8, cy + 3), 1)
        pygame.draw.line(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 6, cy - 13), (cx + 6, cy - 13), 1)
        pygame.draw.line(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (cx - 5, cy - 13), (cx + 5, cy - 13), 1)

        # Nose guard (small).
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["shadow_deep"],
                         (cx - 1, cy - 4, 3, 6))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["silver_darkest"],
                         (cx - 1, cy - 4, 2, 6))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["silver_dark"],
                         (cx - 1, cy - 4, 1, 6))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                         (cx - 1, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                         (cx - 1, cy - 4, 1, 1))

        # HELMET WINGS (side wings like Hermes/Valkyrie).
        _NS_solvarin._draw_helm_wings(surface, cx, cy, facing, phase)

    def _draw_helm_wings(surface, cx, cy, facing, phase):
        """Small feathered wings on side of helm."""
        wave = math.sin(phase * 0.8) * 1

        # Draw wings on both sides.
        for side in (-1, 1):
            wing_base_x = cx + side * 9
            wing_base_y = cy - 6

            # Wing extends outward + upward.
            # Main feather (top, largest).
            feather1_tip = (wing_base_x + side * 8, wing_base_y - 5 + int(wave))
            feather2_tip = (wing_base_x + side * 10, wing_base_y - 2 + int(wave))
            feather3_tip = (wing_base_x + side * 8, wing_base_y + 1 + int(wave))

            # Main wing shape.
            wing_pts = [
                (wing_base_x, wing_base_y),
                feather1_tip,
                (int(feather1_tip[0] * 0.5 + feather2_tip[0] * 0.5),
                 int(feather1_tip[1] * 0.5 + feather2_tip[1] * 0.5) + 1),
                feather2_tip,
                (int(feather2_tip[0] * 0.5 + feather3_tip[0] * 0.5),
                 int(feather2_tip[1] * 0.5 + feather3_tip[1] * 0.5) + 1),
                feather3_tip,
                (wing_base_x, wing_base_y + 2),
            ]

            # Shadow.
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in wing_pts])
            # Base dark.
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_darkest"],
                                wing_pts)
            # Mid.
            inner_pts = []
            cx_l = sum(p[0] for p in wing_pts) / len(wing_pts)
            cy_l = sum(p[1] for p in wing_pts) / len(wing_pts)
            for p in wing_pts:
                inner_pts.append(
                    (int(p[0] * 0.75 + cx_l * 0.25),
                     int(p[1] * 0.75 + cy_l * 0.25))
                )
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_dark"],
                                inner_pts)
            _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["silver_mid"], [
                (wing_base_x + side * 2, wing_base_y),
                (int(feather1_tip[0] * 0.7 + wing_base_x * 0.3),
                 int(feather1_tip[1] * 0.7 + wing_base_y * 0.3)),
                (int(feather2_tip[0] * 0.5 + wing_base_x * 0.5),
                 int(feather2_tip[1] * 0.5 + wing_base_y * 0.5)),
                (wing_base_x + side * 2, wing_base_y + 1),
            ])

            # Feather ridges (bright lines).
            for tip in (feather1_tip, feather2_tip, feather3_tip):
                _NS_solvarin._aaline(surface, _NS_solvarin.PALETTE["silver_light"],
                                      (wing_base_x + side, wing_base_y),
                                      tip, 1)
                pygame.draw.rect(surface, _NS_solvarin.PALETTE["silver_shine"],
                                 (tip[0], tip[1], 1, 1))

            # Gold tip on wing base (mounting).
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_dark"],
                             (wing_base_x - 1, wing_base_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_mid"],
                             (wing_base_x, wing_base_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["gold_shine"],
                             (wing_base_x, wing_base_y - 1, 1, 1))

    def _draw_face(surface, cx, cy, facing, phase):
        """Face area (visible under wing helm, no full face guard)."""
        # Small face visible below helm rim.
        # Chin area.
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["shadow_deep"], [
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["skin_dark"], [
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
        ])
        _NS_solvarin._poly(surface, _NS_solvarin.PALETTE["skin_mid"], [
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 1, cy + 6),
            (cx - 1, cy + 6),
        ])

        # Mouth (small line).
        pygame.draw.line(surface, _NS_solvarin.PALETTE["skin_darkest"],
                         (cx - 1, cy + 6), (cx + 1, cy + 6), 1)

    def _draw_helm_eye(surface, cx, cy, facing, phase, action, attack_progress):
        """Bright blue-white eye glow through helm opening."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        if action == "attack" and attack_progress > 0.2:
            pulse = min(1.0, pulse + 0.4)

        ex = cx
        ey = cy

        # Halo (holy glow).
        for radius in range(5, 0, -1):
            alpha = _NS_solvarin._alpha(140 * (5 - radius) / 5 * pulse)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_light"], alpha),
                (ex, ey), radius)

        # Eye (bright blue-white).
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["eye_socket"],
                         (ex - 2, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["eye_dark"],
                         (ex - 1, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["eye_mid"],
                         (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["eye_light"],
                         (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["eye_glow"],
                         (ex + 1, ey, 1, 1))
        if pulse > 0.85:
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["white"],
                             (ex + 1, ey, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 2, 3, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (60, 55, 15, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_holy_aura(surface, x, y, phase):
        """Bright holy gold + white aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((240, 220), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_solvarin._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_solvarin._aacircle(aura,
                    (*_NS_solvarin.PALETTE["holy_darkest"], alpha),
                    (120, 110), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_solvarin._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_solvarin._aacircle(aura,
                    (*_NS_solvarin.PALETTE["holy_dark"], alpha),
                    (120, 110), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_solvarin._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_solvarin._aacircle(aura,
                    (*_NS_solvarin.PALETTE["holy_mid"], alpha),
                    (120, 110), radius)
        surface.blit(aura, (x - 120, y - 110))

        # Floating light particles.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = (_NS_solvarin.PALETTE["holy_mid"] if i % 2 == 0
                     else _NS_solvarin.PALETTE["gold_mid"])
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_solvarin.PALETTE["holy_shine"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Holy gold rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_solvarin.PALETTE["holy_darkest"], 200),
                            (5, 20, 170, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_solvarin.PALETTE["holy_dark"], 220),
                            (14, 22, 152, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_solvarin.PALETTE["gold_dark"], 230),
                            (25, 24, 130, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_solvarin.PALETTE["gold_mid"], 180),
                            (40, 26, 100, 18), 1)

        # Cross-shape runes (religious symbols).
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 35 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_solvarin.PALETTE["holy_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_solvarin.PALETTE["holy_shine"],
                 _NS_solvarin._alpha(180 * pulse)),
                (15, 14, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))

    def _draw_holy_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Holy light wisps."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_solvarin._alpha((30 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_solvarin.PALETTE["holy_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_solvarin._alpha((20 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_solvarin.PALETTE["holy_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising sparkles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_solvarin._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["holy_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["holy_light"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["holy_shine"], alpha),
                (sx, sy - 1, 1, 1))

        # Small white feathers floating (holy accent).
        for i in range(4):
            feather_t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 20 + i * 12 + int(math.sin(phase * 1.2 + i) * 4)
            fy = cy + 8 - int(feather_t * 22)
            alpha = _NS_solvarin._alpha(180 * (1 - feather_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["silver_light"], alpha),
                    (fx, fy, 2, 1))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["silver_shine"], alpha),
                    (fx, fy, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_solvarin._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_darkest"], alpha),
                    (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["holy_mid"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["holy_light"], alpha),
                    (sx, sy, 1, 1))

    # ============================================================
    # SKILL: Q - PURIFICATION (green heal beam + damage burst)
    # ============================================================
    def _draw_purification_skill(surface, boss, x, y, timer, phase):
        """Green heal wave + gold damage burst on target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_solvarin._target_position(boss, x, y)

        if progress < 0.25:
            # Wind-up: gather green light in hand.
            t = progress / 0.25
            hand_x = x + facing * 25
            hand_y = y - 10
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_solvarin._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["heal_dark"], alpha),
                    (hand_x, hand_y), r)
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["heal_mid"],
                                     (hand_x, hand_y), max(1, cr - 2))
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["heal_light"],
                                     (hand_x, hand_y), max(1, cr - 4))
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["heal_shine"],
                                     (hand_x, hand_y), max(1, cr - 6))
        else:
            # Beam of green light to target + damage burst.
            t = (progress - 0.25) / 0.75
            intensity = math.sin(t * math.pi)

            # Green beam from hand to target.
            beam_alpha = _NS_solvarin._alpha(220 * intensity)
            start_x = x + facing * 28
            start_y = y - 10
            for width, alpha_mult in [(6, 0.4), (4, 0.6), (2, 0.9), (1, 1.0)]:
                pygame.draw.line(surface,
                    (*_NS_solvarin.PALETTE["heal_mid"],
                     _NS_solvarin._alpha(beam_alpha * alpha_mult)),
                    (start_x, start_y), (tx, ty), width)
            pygame.draw.line(surface,
                (*_NS_solvarin.PALETTE["heal_shine"], beam_alpha),
                (start_x, start_y), (tx, ty), 1)

            # Sparkles along beam.
            for i in range(12):
                t_spark = (phase * 3 + i * 0.1) % 1.0
                sx = int(start_x + (tx - start_x) * t_spark)
                sy = int(start_y + (ty - start_y) * t_spark)
                sy += int(math.sin(phase * 5 + i) * 3)
                spark_alpha = _NS_solvarin._alpha(240 * intensity * (1 - t_spark * 0.3))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["heal_light"], spark_alpha),
                    (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["heal_shine"], spark_alpha),
                    (sx, sy, 1, 1))

            # Green heal aura at target (heal effect).
            heal_r = int(15 + intensity * 15)
            heal_alpha = _NS_solvarin._alpha(200 * intensity)
            for r in range(heal_r + 3, 3, -2):
                alpha = _NS_solvarin._alpha(heal_alpha * (heal_r + 3 - r) / (heal_r + 3))
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["heal_dark"], alpha),
                    (tx, ty), r)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["heal_mid"], heal_alpha),
                (tx, ty), heal_r // 2)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["heal_light"], heal_alpha),
                (tx, ty), max(1, heal_r // 3))
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["heal_shine"], heal_alpha),
                (tx, ty), max(1, heal_r // 5))

            # Rising healing plus signs around target.
            for i in range(5):
                plus_t = (phase * 0.6 + i * 0.2) % 1.0
                px = tx + int(math.sin(phase + i) * 15)
                py = ty - int(plus_t * 30)
                plus_alpha = _NS_solvarin._alpha(240 * intensity * (1 - plus_t))
                # Plus symbol.
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["heal_shine"], plus_alpha),
                    (px - 1, py - 3, 3, 7))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["heal_shine"], plus_alpha),
                    (px - 3, py - 1, 7, 3))
                pygame.draw.rect(surface,
                    (*_NS_solvarin.PALETTE["white"], plus_alpha),
                    (px, py, 1, 1))

            # Gold damage burst (impact) after 50%.
            if t > 0.5:
                burst_t = (t - 0.5) / 0.5
                burst_r = int(20 + burst_t * 25)
                burst_alpha = _NS_solvarin._alpha(240 * (1 - burst_t))
                # Big holy explosion.
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_darkest"], burst_alpha),
                    (tx, ty), burst_r + 3, 3)
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_dark"], burst_alpha),
                    (tx, ty), burst_r, 2)
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_mid"], burst_alpha),
                    (tx, ty), max(1, burst_r - 6), 2)
                _NS_solvarin._aacircle(surface,
                    (*_NS_solvarin.PALETTE["holy_light"], burst_alpha),
                    (tx, ty), max(1, burst_r - 12), 1)
                # Radial star burst.
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * burst_r)
                    ey = ty + int(math.sin(angle_s) * burst_r * 0.75)
                    pygame.draw.line(surface,
                        (*_NS_solvarin.PALETTE["holy_light"], burst_alpha),
                        (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                        (*_NS_solvarin.PALETTE["holy_shine"], burst_alpha),
                        (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - REPEL (gold shield bubble)
    # ============================================================
    def _draw_repel_ground(surface, boss, x, y, timer, phase):
        """Gold ring under boss."""
        for i in range(2):
            r = int(32 + i * 6 + math.sin(phase * 2) * 3)
            alpha = _NS_solvarin._alpha(200 - i * 60)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["gold_mid"], alpha),
                (x, y + 40), r, 2)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["gold_light"], alpha),
                (x, y + 40), r, 1)

    def _draw_repel_bubble(surface, boss, x, y, timer, phase):
        """Golden dome shield around boss."""
        breath = math.sin(phase * 2) * 2
        r = 55 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multiple ring layers (golden dome).
        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_solvarin._aacircle(bubble,
                (*_NS_solvarin.PALETTE["gold_dark"], alpha_val),
                center, r - i, thickness)
            _NS_solvarin._aacircle(bubble,
                (*_NS_solvarin.PALETTE["holy_mid"], alpha_val),
                center, r - i - 1, 1)

        # Inner fill glow.
        for radius in range(r - 3, 5, -4):
            alpha = _NS_solvarin._alpha(40)
            _NS_solvarin._aacircle(bubble,
                (*_NS_solvarin.PALETTE["holy_light"], alpha), center, radius)

        # Shine highlights.
        for i in range(3):
            hl_angle = -math.pi / 4 + i * 0.2
            hx = center[0] + int(math.cos(hl_angle) * (r - 5))
            hy = center[1] + int(math.sin(hl_angle) * (r - 5))
            _NS_solvarin._aacircle(bubble,
                _NS_solvarin.PALETTE["holy_shine"], (hx, hy), 3 - i)

        # Rotating cross/rune sparkles.
        for i in range(16):
            angle = phase * 1.2 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble,
                _NS_solvarin.PALETTE["holy_shine"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble,
                _NS_solvarin.PALETTE["gold_white"], (sx, sy, 1, 1))

        # Vertical cross-shape "runes" inside dome.
        for angle_off in (0, math.pi / 2, math.pi, math.pi * 1.5):
            angle = angle_off + phase * 0.3
            rx = center[0] + int(math.cos(angle) * (r - 12))
            ry = center[1] + int(math.sin(angle) * (r - 12))
            # Small cross symbol.
            pygame.draw.line(bubble,
                (*_NS_solvarin.PALETTE["holy_hot"], 200),
                (rx - 2, ry), (rx + 2, ry), 1)
            pygame.draw.line(bubble,
                (*_NS_solvarin.PALETTE["holy_hot"], 200),
                (rx, ry - 2), (rx, ry + 2), 1)
            pygame.draw.rect(bubble,
                _NS_solvarin.PALETTE["white"], (rx, ry, 1, 1))

        surface.blit(bubble, (x - r - 10, y - r - 10))

    # ============================================================
    # SKILL: E - DEGEN AURA (spectral chains around enemies)
    # ============================================================
    def _draw_degen_ground(surface, boss, x, y, timer, phase):
        """Dark red/gold aura ring."""
        for i in range(3):
            r = int(38 + i * 6 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_solvarin._alpha(180 - i * 40)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["cross_dark"], alpha),
                (x, y + 40), r, 2)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["cross_mid"], alpha),
                (x, y + 40), r, 1)

    def _draw_degen_foreground(surface, boss, x, y, timer, phase):
        """Spectral X-shape chains + slowing effect visual."""
        # Draw X-crosses floating around aura area.
        aura_r = 55
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.3
            xr = aura_r + int(math.sin(phase * 2 + i) * 5)
            cx = x + int(math.cos(angle) * xr)
            cy = y + int(math.sin(angle) * xr * 0.6)

            pulse = math.sin(phase * 2 + i) * 0.3 + 0.7
            x_alpha = _NS_solvarin._alpha(200 * pulse)

            # X-shape (two crossed lines).
            _NS_solvarin._aaline(surface,
                (*_NS_solvarin.PALETTE["cross_dark"], x_alpha),
                (cx - 3, cy - 3), (cx + 3, cy + 3), 2)
            _NS_solvarin._aaline(surface,
                (*_NS_solvarin.PALETTE["cross_mid"], x_alpha),
                (cx - 3, cy - 3), (cx + 3, cy + 3), 1)
            _NS_solvarin._aaline(surface,
                (*_NS_solvarin.PALETTE["cross_dark"], x_alpha),
                (cx + 3, cy - 3), (cx - 3, cy + 3), 2)
            _NS_solvarin._aaline(surface,
                (*_NS_solvarin.PALETTE["cross_mid"], x_alpha),
                (cx + 3, cy - 3), (cx - 3, cy + 3), 1)
            # Center bright.
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["cross_light"], x_alpha),
                (cx, cy, 1, 1))

        # Chains going from boss outward.
        for i in range(4):
            angle = i * math.pi / 2 + phase * 0.2
            chain_len = aura_r
            chain_end_x = x + int(math.cos(angle) * chain_len)
            chain_end_y = y + int(math.sin(angle) * chain_len * 0.6)

            # Chain segments.
            segments = 5
            for seg in range(segments):
                t1 = seg / segments
                t2 = (seg + 1) / segments
                sx1 = int(x + (chain_end_x - x) * t1)
                sy1 = int(y + (chain_end_y - y) * t1)
                sx2 = int(x + (chain_end_x - x) * t2)
                sy2 = int(y + (chain_end_y - y) * t2)
                # Chain segment (dark link).
                _NS_solvarin._aacircle(surface,
                    _NS_solvarin.PALETTE["cross_dark"],
                    ((sx1 + sx2) // 2, (sy1 + sy2) // 2), 2)
                _NS_solvarin._aacircle(surface,
                    _NS_solvarin.PALETTE["cross_mid"],
                    ((sx1 + sx2) // 2, (sy1 + sy2) // 2), 1)

    # ============================================================
    # SKILL: R - GUARDIAN ANGEL (angel wings + massive holy aura)
    # ============================================================
    def _draw_guardian_ground(surface, boss, x, y, timer, phase):
        """Massive golden ring under boss."""
        for i in range(3):
            r = int(45 + i * 8 + math.sin(phase * 2 + i) * 4)
            alpha = _NS_solvarin._alpha(220 - i * 50)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_mid"], alpha),
                (x, y + 40), r, 3)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_light"], alpha),
                (x, y + 40), r, 2)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_shine"], alpha),
                (x, y + 40), r, 1)

    def _draw_guardian_wings(surface, boss, x, y, timer, phase):
        """MASSIVE angel wings appearing behind boss."""
        pulse = math.sin(phase * 0.8) * 0.15 + 0.85
        wing_beat = math.sin(phase * 1.5) * 3
        facing = boss.direction

        # Wings on BOTH sides of body (behind).
        for side in (-1, 1):
            wing_base_x = x - facing * 2
            wing_base_y = y - 8

            # Multiple large feathers.
            num_feathers = 7
            for f_i in range(num_feathers):
                # Angle spreads from ~-30° to ~+30° from horizontal
                # (radiating out from base).
                feather_angle = math.pi * 0.15 + f_i * (math.pi * 0.55) / (num_feathers - 1)
                feather_len = 45 + f_i * 3 + int(wing_beat)
                # Middle feathers longest.
                mid_boost = int(math.sin(f_i / (num_feathers - 1) * math.pi) * 12)
                feather_len += mid_boost

                # Tip position.
                tip_x = wing_base_x + int(math.cos(feather_angle) * feather_len) * side
                tip_y = wing_base_y - int(math.sin(feather_angle) * feather_len)

                # Perpendicular for feather width.
                perp_angle = feather_angle + math.pi / 2
                perp_x_val = math.cos(perp_angle) * side
                perp_y_val = -math.sin(perp_angle)

                # Feather base (2 points near wing_base).
                fb_a = (wing_base_x + int(perp_x_val * 3),
                        wing_base_y + int(perp_y_val * 3))
                fb_b = (wing_base_x - int(perp_x_val * 3),
                        wing_base_y - int(perp_y_val * 3))
                # Feather mid (widest).
                mid_x = int((wing_base_x + tip_x) / 2)
                mid_y = int((wing_base_y + tip_y) / 2)
                fm_a = (mid_x + int(perp_x_val * 5),
                        mid_y + int(perp_y_val * 5))
                fm_b = (mid_x - int(perp_x_val * 5),
                        mid_y - int(perp_y_val * 5))

                feather_pts = [fb_a, fm_a, (tip_x, tip_y), fm_b, fb_b]

                # Draw feather on alpha surface for translucency.
                feather_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                offset_x = wing_base_x - 60
                offset_y = wing_base_y - 60
                local_pts = [(p[0] - offset_x, p[1] - offset_y)
                             for p in feather_pts]

                alpha_feather = _NS_solvarin._alpha(230 * pulse)
                # Shadow.
                _NS_solvarin._poly(feather_surf,
                    (*_NS_solvarin.PALETTE["shadow_deep"], alpha_feather),
                    [(p[0] + 1, p[1] + 1) for p in local_pts])
                # Base dark.
                _NS_solvarin._poly(feather_surf,
                    (*_NS_solvarin.PALETTE["silver_dark"], alpha_feather),
                    local_pts)
                # Mid.
                inner_pts = []
                cx_l = sum(p[0] for p in local_pts) / len(local_pts)
                cy_l = sum(p[1] for p in local_pts) / len(local_pts)
                for p in local_pts:
                    inner_pts.append(
                        (int(p[0] * 0.8 + cx_l * 0.2),
                         int(p[1] * 0.8 + cy_l * 0.2))
                    )
                _NS_solvarin._poly(feather_surf,
                    (*_NS_solvarin.PALETTE["silver_mid"], alpha_feather),
                    inner_pts)
                # Bright.
                _NS_solvarin._poly(feather_surf,
                    (*_NS_solvarin.PALETTE["silver_light"], alpha_feather), [
                        (int((fb_a[0] - offset_x + tip_x - offset_x) / 2),
                         int((fb_a[1] - offset_y + tip_y - offset_y) / 2)),
                        (tip_x - offset_x, tip_y - offset_y),
                        (int((fb_b[0] - offset_x + tip_x - offset_x) / 2),
                         int((fb_b[1] - offset_y + tip_y - offset_y) / 2)),
                    ])

                # Feather spine (bright ridge).
                pygame.draw.line(feather_surf,
                    (*_NS_solvarin.PALETTE["silver_shine"], alpha_feather),
                    (fb_a[0] - offset_x, fb_a[1] - offset_y),
                    (tip_x - offset_x, tip_y - offset_y), 1)
                pygame.draw.line(feather_surf,
                    (*_NS_solvarin.PALETTE["white"], alpha_feather),
                    (int((fb_a[0] - offset_x + tip_x - offset_x) / 2),
                     int((fb_a[1] - offset_y + tip_y - offset_y) / 2)),
                    (tip_x - offset_x, tip_y - offset_y), 1)
                # Tip highlight.
                pygame.draw.rect(feather_surf,
                    (*_NS_solvarin.PALETTE["holy_shine"], alpha_feather),
                    (tip_x - offset_x, tip_y - offset_y, 1, 1))

                surface.blit(feather_surf, (offset_x, offset_y))

    def _draw_guardian_foreground(surface, boss, x, y, timer, phase):
        """Extra holy aura + falling feathers + angelic light."""
        # Halo above boss.
        halo_bob = int(math.sin(phase * 0.5) * 2)
        halo_y = y - 40 + halo_bob
        halo_pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Halo ring.
        for r in range(10, 5, -1):
            alpha = _NS_solvarin._alpha(200 * halo_pulse * (10 - r) / 10)
            _NS_solvarin._aacircle(surface,
                (*_NS_solvarin.PALETTE["holy_mid"], alpha),
                (x, halo_y), r)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["holy_dark"],
                                 (x, halo_y), 8, 2)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["holy_light"],
                                 (x, halo_y), 8, 1)
        _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["holy_shine"],
                                 (x, halo_y), 7, 1)

        # Bright cross inside halo.
        pygame.draw.line(surface, _NS_solvarin.PALETTE["holy_hot"],
                         (x - 3, halo_y), (x + 3, halo_y), 1)
        pygame.draw.line(surface, _NS_solvarin.PALETTE["holy_hot"],
                         (x, halo_y - 3), (x, halo_y + 3), 1)
        pygame.draw.rect(surface, _NS_solvarin.PALETTE["white"],
                         (x, halo_y, 1, 1))

        # Falling feathers around boss.
        for i in range(10):
            feather_t = (phase * 0.4 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.1
            fr = 30 + int(feather_t * 25)
            fx = x + int(math.cos(angle) * fr)
            fy = y - 20 + int(feather_t * 60)  # falling down
            f_alpha = _NS_solvarin._alpha(200 * (1 - feather_t * 0.5))

            # Small feather shape (elongated).
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["silver_dark"], f_alpha),
                (fx, fy, 2, 3))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["silver_light"], f_alpha),
                (fx, fy, 1, 2))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["silver_shine"], f_alpha),
                (fx, fy, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["holy_shine"], f_alpha),
                (fx, fy + 3, 1, 1))

        # Rising holy sparkles.
        for i in range(15):
            spark_t = (phase * 0.7 + i * 0.08) % 1.0
            angle = i * math.pi / 7 + phase * 0.2
            sr = 45 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(angle) * sr)
            sy = y + 20 - int(spark_t * 50)
            spark_alpha = _NS_solvarin._alpha(240 * (1 - spark_t))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["holy_light"], spark_alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_solvarin.PALETTE["holy_shine"], spark_alpha),
                (sx, sy, 1, 1))

        # Golden light pillars around boss (large aura).
        num_pillars = 8
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars + phase * 0.1
            px = x + int(math.cos(angle) * 48)
            py_base = y + 40 + int(math.sin(angle) * 15)

            pillar_h = 50
            for layer_i, (width, alpha_val) in enumerate([
                (5, 100), (3, 150), (2, 200), (1, 240),
            ]):
                actual_alpha = _NS_solvarin._alpha(alpha_val)
                colors = [
                    _NS_solvarin.PALETTE["holy_dark"],
                    _NS_solvarin.PALETTE["holy_mid"],
                    _NS_solvarin.PALETTE["holy_light"],
                    _NS_solvarin.PALETTE["holy_shine"],
                ]
                color = colors[min(layer_i, 3)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (px - width // 2, py_base - pillar_h,
                                  width, pillar_h))

            # Bright top.
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["holy_shine"],
                                     (px, py_base - pillar_h), 3)
            _NS_solvarin._aacircle(surface, _NS_solvarin.PALETTE["white"],
                                     (px, py_base - pillar_h), 1)


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kaeldris(surface, boss, x, y):
    """Entry point kaeldris."""
    return _NS_kaeldris.draw_kaeldris(surface, boss, x, y)


def draw_pyraklos(surface, boss, x, y):
    """Entry point pyraklos."""
    return _NS_pyraklos.draw_pyraklos(surface, boss, x, y)


def draw_velmyrth(surface, boss, x, y):
    """Entry point velmyrth."""
    return _NS_velmyrth.draw_velmyrth(surface, boss, x, y)


def draw_solvarin(surface, boss, x, y):
    """Entry point solvarin."""
    return _NS_solvarin.draw_solvarin(surface, boss, x, y)
