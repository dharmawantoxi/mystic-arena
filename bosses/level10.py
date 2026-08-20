"""
bosses/level10.py - Semua boss Level 10

Berisi:
  - krognarr   (mini boss)
  - raz        (mini boss)
  - vraskhan   (mini boss)
  - aurethzar  (TRUE BOSS - ranged solar archer)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# krognarr.py
# ====================================================================

# ====================================================================
# KROGNARR - THE EARTHBOUND
# Mini-boss: Crystal-infused stone golem
# ====================================================================


class _NS_krognarr:
    """Namespace krognarr - stone golem dengan kristal hijau menyala."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Stone body (dark mossy rock)
        "stone_darkest": (18, 22, 15),
        "stone_dark": (42, 48, 35),
        "stone_mid": (75, 82, 60),
        "stone_light": (120, 128, 95),
        "stone_edge": (165, 170, 130),
        "stone_shine": (210, 215, 175),

        # Moss overlay (dark green patches)
        "moss_dark": (25, 55, 20),
        "moss_mid": (55, 95, 35),
        "moss_light": (95, 145, 55),

        # Crystal green (glowing shards)
        "crystal_darkest": (15, 45, 10),
        "crystal_dark": (40, 100, 25),
        "crystal_mid": (110, 200, 55),
        "crystal_light": (180, 250, 110),
        "crystal_hot": (220, 255, 160),
        "crystal_shine": (245, 255, 220),

        # Gold/amber accents (eye, runes)
        "amber_dark": (95, 60, 15),
        "amber_mid": (200, 145, 40),
        "amber_light": (250, 210, 100),
        "amber_shine": (255, 245, 180),

        # Earth eruption (brown-gold)
        "earth_dark": (50, 35, 15),
        "earth_mid": (110, 80, 35),
        "earth_light": (180, 140, 70),

        # Cracks (glowing crystal veins through body)
        "vein_dark": (30, 80, 20),
        "vein_mid": (90, 180, 45),
        "vein_hot": (180, 250, 120),

        # Nether accents
        "nether_dark": (30, 15, 55),
        "nether_mid": (80, 40, 120),
        "nether_light": (150, 100, 200),

        # Dust/mist
        "dust_dark": (40, 45, 30),
        "dust_mid": (95, 100, 70),
        "dust_light": (160, 165, 125),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_krognarr._clamp(color)
        if _NS_krognarr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_krognarr._clamp(color)
        if _NS_krognarr.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_krognarr._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_krognarr(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_krognarr._detect_moving(boss)
        _NS_krognarr._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_krg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_krognarr._draw_earth_aura(surface, x, y, pulse)
        _NS_krognarr._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_krognarr._draw_seismic_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_krognarr._draw_rampart_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_krognarr._draw_eruption_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_krognarr._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_krognarr._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_krognarr._draw_idle_pose(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_krognarr._draw_stone_strike(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_krognarr._draw_seismic_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_krognarr._draw_rampart_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_krognarr._draw_eruption_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_krg_previous_timer", 0))
        active = bool(getattr(boss, "_krg_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._krg_attack_active = True
            boss._krg_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._krg_attack_dir = int(getattr(boss, "direction", 1))
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

    def _detect_moving(boss):
        if not hasattr(boss, "_krg_last_x"):
            boss._krg_last_x = boss.x
            boss._krg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._krg_last_x)
        dy = abs(boss.y - boss._krg_last_y)
        boss._krg_last_x = boss.x
        boss._krg_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        # Floating bob - lebih smooth dan tinggi.
        float_y = int(math.sin(boss.pulse * 0.6) * 6)
        _NS_krognarr._draw_shadow(surface, x, y + 52)
        _NS_krognarr._draw_float_dust(surface, x, y + 48, boss.pulse)
        _NS_krognarr._draw_body(surface, x, y - 8 + float_y,
                                 boss.direction, boss.pulse, "idle")

    def _draw_walk_pose(surface, boss, x, y):
        phase = boss.pulse * 2.0
        float_y = int(math.sin(phase * 0.8) * 8)  # bob lebih dinamis
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_krognarr._draw_shadow(surface, x + sway, y + 52)
        _NS_krognarr._draw_float_dust(surface, x + sway, y + 48, phase,
                                       trail=True, facing=boss.direction)
        _NS_krognarr._draw_body(surface, x + sway, y - 8 + float_y,
                                 boss.direction, phase, "walk")

    def _draw_attack_pose(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_krg_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_krg_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Wind-up → swing → recovery (melee style).
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * facing
            lift = int(t * 6)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 16)) * facing
            lift = int(6 - t * 8)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        float_y = int(math.sin(boss.pulse * 0.6) * 4)

        _NS_krognarr._draw_shadow(surface, x + lunge, y + 52)
        _NS_krognarr._draw_float_dust(surface, x + lunge, y + 48, boss.pulse, intense=True)
        _NS_krognarr._draw_body(surface, x + lunge, y - 8 - lift + float_y,
                                 facing, boss.pulse, "attack", progress)

    # ============================================================
    # BODY - Stone Golem layout
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Golem: legs (floating stubs), torso, arms, head with crystal crown."""
        # Legs (short stumpy, floating).
        _NS_krognarr._draw_legs(surface, cx, cy + 24, facing, phase, action)

        # Torso (bulky).
        _NS_krognarr._draw_torso(surface, cx, cy + 4, facing, phase)

        # Back crystal spikes.
        _NS_krognarr._draw_back_crystals(surface, cx, cy, facing, phase)

        # Arms with swing animation.
        _NS_krognarr._draw_arms(surface, cx, cy + 2, facing, phase, action,
                                 attack_progress)

        # Head with crystal crown.
        _NS_krognarr._draw_head(surface, cx, cy - 18, facing, phase, action)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Short stumpy stone legs (floating, so they dangle)."""
        dangle = math.sin(phase * 0.8) * 1

        for side, off_x in enumerate((-8, 8)):
            lx = cx + off_x
            ly = cy + int(dangle) + side  # slight offset

            # Leg shape (chunky stone stub).
            leg_shape = [
                (lx - 6, ly - 8),
                (lx + 6, ly - 8),
                (lx + 7, ly - 2),
                (lx + 6, ly + 4),
                (lx + 4, ly + 8),
                (lx - 4, ly + 8),
                (lx - 6, ly + 4),
                (lx - 7, ly - 2),
            ]
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                                [(p[0] + 2, p[1] + 2) for p in leg_shape])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_darkest"], leg_shape)
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_dark"], [
                (lx - 5, ly - 7), (lx + 5, ly - 7),
                (lx + 6, ly - 2), (lx + 5, ly + 4),
                (lx + 3, ly + 7), (lx - 3, ly + 7),
                (lx - 5, ly + 4), (lx - 6, ly - 2),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_mid"], [
                (lx - 3, ly - 6), (lx + 3, ly - 6),
                (lx + 4, ly - 2), (lx + 3, ly + 3),
                (lx - 3, ly + 3), (lx - 4, ly - 2),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_light"], [
                (lx - 1, ly - 5), (lx + 2, ly - 5),
                (lx + 2, ly - 1), (lx - 1, ly - 1),
            ])

            # Moss on legs.
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["moss_dark"],
                             (lx - 5, ly + 2, 3, 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["moss_mid"],
                             (lx - 5, ly + 2, 2, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["moss_dark"],
                             (lx + 2, ly + 3, 3, 2))

            # Small crystal shard on leg.
            crystal_glow = math.sin(phase * 1.5 + side) * 0.3 + 0.7
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_darkest"],
                             (lx + 1, ly - 3, 2, 3))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                             (lx + 1, ly - 3, 1, 2))
            pygame.draw.rect(surface,
                             _NS_krognarr._clamp((
                                 _NS_krognarr.PALETTE["crystal_hot"][0] * crystal_glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][1] * crystal_glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][2] * crystal_glow,
                             )),
                             (lx + 1, ly - 3, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Bulky stone torso with cracks and moss."""
        breath = math.sin(phase * 0.5) * 1

        # Main torso shape (broad shoulders).
        torso_shape = [
            (cx - 18, cy - 12),
            (cx - 22, cy - 8),
            (cx - 24, cy - 2),
            (cx - 22, cy + 6),
            (cx - 18, cy + 14),
            (cx - 10, cy + 18),
            (cx + 10, cy + 18),
            (cx + 18, cy + 14),
            (cx + 22, cy + 6),
            (cx + 24, cy - 2),
            (cx + 22, cy - 8),
            (cx + 18, cy - 12),
            (cx + 10, cy - 14),
            (cx - 10, cy - 14),
        ]
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                            [(p[0] + 3, p[1] + 3) for p in torso_shape])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_darkest"], torso_shape)

        # Mid stone layer.
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_dark"], [
            (cx - 16, cy - 11), (cx - 20, cy - 7), (cx - 22, cy - 2),
            (cx - 20, cy + 5), (cx - 16, cy + 12), (cx - 8, cy + 16),
            (cx + 8, cy + 16), (cx + 16, cy + 12), (cx + 20, cy + 5),
            (cx + 22, cy - 2), (cx + 20, cy - 7), (cx + 16, cy - 11),
            (cx + 8, cy - 13), (cx - 8, cy - 13),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_mid"], [
            (cx - 14, cy - 9), (cx - 17, cy - 4), (cx - 17, cy + 4),
            (cx - 13, cy + 10), (cx - 5, cy + 13), (cx + 5, cy + 13),
            (cx + 13, cy + 10), (cx + 17, cy + 4), (cx + 17, cy - 4),
            (cx + 14, cy - 9), (cx + 6, cy - 11), (cx - 6, cy - 11),
        ])

        # Chest highlight.
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_light"], [
            (cx - 8, cy - 6), (cx - 10, cy - 2), (cx - 8, cy + 4),
            (cx - 3, cy + 6), (cx + 3, cy + 6), (cx + 8, cy + 4),
            (cx + 10, cy - 2), (cx + 8, cy - 6),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_edge"], [
            (cx - 4, cy - 4), (cx - 5, cy - 1), (cx - 3, cy + 2),
            (cx + 3, cy + 2), (cx + 5, cy - 1), (cx + 4, cy - 4),
        ])

        # BIG CENTER CRYSTAL in chest (heart).
        heart_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        heart_x, heart_y = cx, cy + 1

        # Crystal socket (dark).
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["shadow_deep"],
                         (heart_x - 3, heart_y - 4, 6, 8))
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["stone_darkest"],
                         (heart_x - 3, heart_y - 4, 6, 8))

        # Glowing halo behind heart.
        for r in range(8, 1, -1):
            alpha = _NS_krognarr._alpha(120 * (8 - r) / 8 * heart_pulse)
            _NS_krognarr._aacircle(surface,
                                    (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                    (heart_x, heart_y), r)

        # Diamond crystal shape.
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_darkest"], [
            (heart_x, heart_y - 5), (heart_x + 3, heart_y),
            (heart_x, heart_y + 5), (heart_x - 3, heart_y),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_dark"], [
            (heart_x, heart_y - 4), (heart_x + 2, heart_y),
            (heart_x, heart_y + 4), (heart_x - 2, heart_y),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_mid"], [
            (heart_x, heart_y - 3), (heart_x + 2, heart_y),
            (heart_x, heart_y + 3), (heart_x - 2, heart_y),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_light"], [
            (heart_x, heart_y - 2), (heart_x + 1, heart_y),
            (heart_x, heart_y + 2), (heart_x - 1, heart_y),
        ])
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                         (heart_x, heart_y - 1, 1, 1))

        # Cracks radiating from heart (glowing veins).
        vein_bright = math.sin(phase * 1.5) * 0.4 + 0.6
        veins = [
            [(cx - 3, cy - 1), (cx - 8, cy - 5), (cx - 13, cy - 3)],
            [(cx - 3, cy + 1), (cx - 9, cy + 5), (cx - 14, cy + 8)],
            [(cx + 3, cy - 1), (cx + 8, cy - 5), (cx + 13, cy - 3)],
            [(cx + 3, cy + 1), (cx + 9, cy + 5), (cx + 14, cy + 8)],
            [(cx, cy + 4), (cx + 2, cy + 10), (cx, cy + 15)],
        ]
        for vein in veins:
            for i in range(len(vein) - 1):
                _NS_krognarr._aaline(surface, _NS_krognarr.PALETTE["vein_dark"],
                                      vein[i], vein[i + 1], 2)
                _NS_krognarr._aaline(surface,
                                      _NS_krognarr._clamp((
                                          _NS_krognarr.PALETTE["vein_mid"][0] * vein_bright,
                                          _NS_krognarr.PALETTE["vein_mid"][1] * vein_bright,
                                          _NS_krognarr.PALETTE["vein_mid"][2] * vein_bright,
                                      )),
                                      vein[i], vein[i + 1], 1)

        # Moss patches on shoulders.
        moss_spots = [
            (cx - 16, cy - 4, 4, 3), (cx - 12, cy + 8, 5, 3),
            (cx + 12, cy - 6, 4, 3), (cx + 14, cy + 6, 4, 3),
            (cx - 8, cy + 14, 6, 2),
        ]
        for mx, my, mw, mh in moss_spots:
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["moss_dark"],
                             (mx, my, mw, mh))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["moss_mid"],
                             (mx, my, mw - 1, mh - 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["moss_light"],
                             (mx + 1, my, 1, 1))

        # Small crystal shards embedded in torso.
        for cx_off, cy_off, size in [(-14, -8, 2), (12, -10, 2), (-16, 10, 2),
                                       (15, 8, 2), (-6, -12, 1), (7, -12, 1)]:
            sx = cx + cx_off
            sy = cy + cy_off
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_darkest"],
                             (sx, sy, size + 1, size + 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                             (sx, sy, size, size + 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_light"],
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                             (sx, sy, 1, 1))

    def _draw_back_crystals(surface, cx, cy, facing, phase):
        """Large crystal spikes growing from shoulders/back."""
        crystal_configs = [
            # (offset_x, offset_y, tip_y_offset, width, glow_phase)
            (-14, -8, -18, 4, 0.0),
            (-8, -14, -26, 5, 0.3),
            (0, -16, -30, 6, 0.6),
            (8, -14, -26, 5, 0.9),
            (14, -8, -18, 4, 1.2),
        ]

        for ox, oy, tip_off, width, phase_off in crystal_configs:
            bx = cx + ox
            by = cy + oy
            tx = cx + ox + int(math.sin(phase * 0.3 + phase_off) * 1)
            ty = cy + tip_off

            glow = math.sin(phase * 1.5 + phase_off) * 0.3 + 0.7

            # Crystal shape (elongated diamond pointing up).
            crystal_shape = [
                (tx, ty),
                (bx + width, by - 2),
                (bx + width - 1, by + 2),
                (bx - width + 1, by + 2),
                (bx - width, by - 2),
            ]
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in crystal_shape])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_darkest"],
                                crystal_shape)
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_dark"], [
                (tx, ty),
                (bx + width - 1, by - 1),
                (bx - width + 1, by - 1),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_mid"], [
                (tx, ty),
                (bx + width - 2, by - 2),
                (bx, by),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_light"], [
                (tx, ty),
                (int((tx + bx) / 2 + 1), int((ty + by) / 2)),
                (bx, by - 1),
            ])

            # Glowing tip.
            pygame.draw.rect(surface,
                             _NS_krognarr._clamp((
                                 _NS_krognarr.PALETTE["crystal_hot"][0] * glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][1] * glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][2] * glow,
                             )),
                             (tx, ty, 1, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                             (tx, ty, 1, 1))

            # Glow halo around crystal tip.
            for r in range(4, 0, -1):
                alpha = _NS_krognarr._alpha(80 * (4 - r) / 4 * glow)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (tx, ty), r)

    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two bulky stone arms with fist. Swing during attack."""
        # Base arm angles.
        idle_sway = math.sin(phase * 0.6) * 3

        for side_i, side_x in enumerate((-1, 1)):
            shoulder_x = cx + side_x * 20
            shoulder_y = cy - 6

            # Determine arm angle.
            if action == "attack":
                # Front arm swings, back arm braces.
                if side_x == facing:  # front arm (swings)
                    if attack_progress < 0.35:
                        # Wind-up (back).
                        t = attack_progress / 0.35
                        swing = -30 - t * 40
                    elif attack_progress < 0.6:
                        # Swing forward.
                        t = (attack_progress - 0.35) / 0.25
                        swing = -70 + t * 130
                    else:
                        # Recovery.
                        t = (attack_progress - 0.6) / 0.4
                        swing = 60 - t * 60
                    arm_angle_deg = swing
                else:
                    arm_angle_deg = 15 + idle_sway
            elif action == "walk":
                # Swaying arms while floating.
                arm_angle_deg = math.sin(phase * 1.2 + side_i * math.pi) * 12
            else:
                arm_angle_deg = 10 + idle_sway * side_x

            arm_angle = math.radians(90 + arm_angle_deg * side_x)

            # Upper arm segment.
            upper_len = 14
            elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * side_x
            elbow_y = shoulder_y + int(math.sin(arm_angle) * upper_len)

            # Forearm segment.
            forearm_angle = arm_angle + math.radians(20 * side_x)
            if action == "attack" and side_x == facing:
                if 0.35 <= attack_progress < 0.6:
                    # Extended punch.
                    forearm_angle = arm_angle
            forearm_len = 12
            fist_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * side_x
            fist_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

            # Draw arm segments.
            _NS_krognarr._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                            (elbow_x, elbow_y), 7, phase)
            _NS_krognarr._draw_arm_segment(surface, (elbow_x, elbow_y),
                                            (fist_x, fist_y), 6, phase)

            # Fist (stone chunk).
            _NS_krognarr._draw_fist(surface, fist_x, fist_y, side_x, phase,
                                     action == "attack" and side_x == facing
                                     and 0.35 <= attack_progress < 0.6)

    def _draw_arm_segment(surface, start, end, thickness, phase):
        """Draw one arm segment (upper arm or forearm)."""
        # Shadow.
        _NS_krognarr._aaline(surface, _NS_krognarr.PALETTE["shadow_deep"],
                              (start[0] + 2, start[1] + 2),
                              (end[0] + 2, end[1] + 2), thickness + 2)
        # Base stone.
        _NS_krognarr._aaline(surface, _NS_krognarr.PALETTE["stone_darkest"],
                              start, end, thickness + 1)
        _NS_krognarr._aaline(surface, _NS_krognarr.PALETTE["stone_dark"],
                              start, end, thickness)
        _NS_krognarr._aaline(surface, _NS_krognarr.PALETTE["stone_mid"],
                              (start[0], start[1] - 1), (end[0], end[1] - 1),
                              max(1, thickness - 2))
        _NS_krognarr._aaline(surface, _NS_krognarr.PALETTE["stone_light"],
                              (start[0], start[1] - 2), (end[0], end[1] - 2),
                              max(1, thickness - 4))

        # Small crystal on arm.
        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_dark"],
                         (mid_x, mid_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_light"],
                         (mid_x, mid_y - 1, 1, 1))

    def _draw_fist(surface, cx, cy, facing, phase, punching):
        """Chunky stone fist."""
        size = 8 if punching else 7

        # Fist shape (rocky knuckles).
        fist_shape = [
            (cx - size, cy - size // 2),
            (cx - size + 1, cy - size + 1),
            (cx + size - 1, cy - size + 1),
            (cx + size, cy - size // 2),
            (cx + size, cy + size // 2 - 1),
            (cx + size - 2, cy + size),
            (cx - size + 2, cy + size),
            (cx - size, cy + size // 2 - 1),
        ]
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in fist_shape])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_darkest"], fist_shape)
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_dark"], [
            (cx - size + 1, cy - size // 2),
            (cx + size - 1, cy - size // 2),
            (cx + size - 1, cy + size // 2 - 1),
            (cx - size + 1, cy + size // 2 - 1),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_mid"], [
            (cx - size + 2, cy - size // 2 + 1),
            (cx + size - 2, cy - size // 2 + 1),
            (cx + size - 3, cy + size // 2 - 2),
            (cx - size + 3, cy + size // 2 - 2),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_light"], [
            (cx - 2, cy - size // 2 + 2),
            (cx + 2, cy - size // 2 + 2),
            (cx + 1, cy - 1),
            (cx - 1, cy - 1),
        ])

        # Knuckles (small bumps).
        for kx in (-4, -1, 2, 5):
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["stone_darkest"],
                             (cx + kx, cy - size // 2, 2, 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["stone_edge"],
                             (cx + kx, cy - size // 2, 1, 1))

        # Crystal spike on knuckles (if punching, brighter).
        glow_mult = 1.0 if punching else 0.7
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_darkest"],
                         (cx - 1, cy - size - 2, 3, 4))
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                         (cx - 1, cy - size - 2, 2, 3))
        pygame.draw.rect(surface,
                         _NS_krognarr._clamp((
                             _NS_krognarr.PALETTE["crystal_light"][0] * glow_mult,
                             _NS_krognarr.PALETTE["crystal_light"][1] * glow_mult,
                             _NS_krognarr.PALETTE["crystal_light"][2] * glow_mult,
                         )),
                         (cx - 1, cy - size - 2, 1, 2))
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                         (cx - 1, cy - size - 2, 1, 1))

        # Punching glow.
        if punching:
            for r in range(10, 2, -2):
                alpha = _NS_krognarr._alpha(140 * (10 - r) / 10)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (cx, cy), r)

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Stone head with crystal crown/horns and glowing eye(s)."""
        # Head shape (boxy stone).
        head_shape = [
            (cx - 10, cy - 6),
            (cx - 12, cy - 2),
            (cx - 11, cy + 4),
            (cx - 7, cy + 8),
            (cx + 7, cy + 8),
            (cx + 11, cy + 4),
            (cx + 12, cy - 2),
            (cx + 10, cy - 6),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_darkest"], head_shape)

        # Mid stone.
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_dark"], [
            (cx - 9, cy - 5), (cx - 11, cy - 2), (cx - 10, cy + 3),
            (cx - 6, cy + 7), (cx + 6, cy + 7), (cx + 10, cy + 3),
            (cx + 11, cy - 2), (cx + 9, cy - 5), (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_mid"], [
            (cx - 7, cy - 4), (cx - 8, cy), (cx - 6, cy + 5),
            (cx + 6, cy + 5), (cx + 8, cy), (cx + 7, cy - 4),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])

        # Cheek highlight.
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["stone_light"], [
            (cx - 4, cy - 2), (cx - 5, cy + 2), (cx - 2, cy + 4),
            (cx + 2, cy + 4), (cx + 5, cy + 2), (cx + 4, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["stone_edge"],
                         (cx - 1, cy - 1, 2, 2))

        # Crystal crown on top of head.
        _NS_krognarr._draw_head_crystals(surface, cx, cy - 8, phase)

        # GLOWING EYES (single wide slit or two eyes).
        _NS_krognarr._draw_golem_eyes(surface, cx, cy, facing, phase)

        # Mouth (dark slit with glow if attacking).
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["shadow_deep"],
                         (cx - 3, cy + 5, 6, 1))
        if action == "attack":
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                             (cx - 3, cy + 5, 6, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_light"],
                             (cx - 2, cy + 5, 4, 1))

        # Small crystal shards on chin/cheek.
        for cx_off, cy_off in [(-9, 2), (8, 3)]:
            sx = cx + cx_off
            sy = cy + cy_off
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_darkest"],
                             (sx, sy, 2, 3))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                             (sx, sy, 1, 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_light"],
                             (sx, sy, 1, 1))

    def _draw_head_crystals(surface, cx, cy, phase):
        """Crystal crown on head."""
        crown = [
            (-6, -1, -8, 3),   # left
            (-2, -3, -12, 4),  # left-center (tallest)
            (2, -3, -12, 4),   # right-center (tallest)
            (6, -1, -8, 3),    # right
        ]
        for ox, oy, tip_off, width in crown:
            bx = cx + ox
            by = cy + oy
            tx = bx
            ty = cy + tip_off

            glow = math.sin(phase * 1.2 + ox * 0.3) * 0.3 + 0.7

            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"], [
                (tx + 1, ty + 1),
                (bx + width // 2 + 1, by + 1),
                (bx - width // 2 + 1, by + 1),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_darkest"], [
                (tx, ty),
                (bx + width // 2, by),
                (bx - width // 2, by),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_dark"], [
                (tx, ty),
                (bx + width // 2 - 1, by),
                (bx, by),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_mid"], [
                (tx, ty),
                (bx, by),
                (bx - width // 2 + 1, by),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_light"], [
                (tx, ty),
                (int((tx + bx) / 2), int((ty + by) / 2)),
                (bx, by),
            ])
            pygame.draw.rect(surface,
                             _NS_krognarr._clamp((
                                 _NS_krognarr.PALETTE["crystal_hot"][0] * glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][1] * glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][2] * glow,
                             )),
                             (tx, ty, 1, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                             (tx, ty, 1, 1))

    def _draw_golem_eyes(surface, cx, cy, facing, phase):
        """Two glowing green eye slits."""
        pulse = math.sin(phase * 1.8) * 0.3 + 0.7

        for eye_x in (-4, 4):
            ex = cx + eye_x
            ey = cy - 1

            # Deep socket.
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["shadow_deep"],
                             (ex - 2, ey - 1, 4, 3))

            # Glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_krognarr._alpha(120 * (4 - r) / 4 * pulse)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (ex, ey), r)

            # Iris.
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_darkest"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_dark"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_hot"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                             (ex, ey, 1, 1))

    # ============================================================
    # FLOATING DUST / AMBIENT
    # ============================================================
    def _draw_float_dust(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Dust particles floating below the levitating golem."""
        strength = 1.5 if intense else 1.0

        # Dust cloud below.
        dust = pygame.Surface((140, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_krognarr._alpha((30 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    dust, (*_NS_krognarr.PALETTE["dust_dark"], alpha),
                    (70 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_krognarr._alpha((18 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    dust, (*_NS_krognarr.PALETTE["dust_mid"], alpha),
                    (70 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(dust, (cx - 70, cy - 10))

        # Falling pebbles + rising crystal sparkles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, -32, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy - 2 + int(t * 20)  # falling
            alpha = _NS_krognarr._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Pebble.
            pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_dark"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_mid"], alpha),
                             (sx, sy, 1, 1))

        # Rising green crystal motes.
        for i in range(7):
            mote_t = (phase * 0.5 + i * 0.16) % 1.0
            mx = cx - 22 + i * 7 + int(math.sin(phase + i) * 4)
            my = cy + 4 - int(mote_t * 22)
            alpha = _NS_krognarr._alpha(220 * (1 - mote_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                 (mx, my, 2, 2))
                pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                 (mx, my, 1, 1))

        # Trail behind while moving.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_krognarr._alpha(150 - i * 28)
                if alpha <= 0:
                    continue
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["dust_mid"], alpha),
                                        (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                 (sx, sy - 1, 2, 2))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 40, 20, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_earth_aura(surface, x, y, phase):
        """Green earth aura pulse."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_krognarr._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_krognarr._aacircle(aura,
                                        (*_NS_krognarr.PALETTE["dust_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_krognarr._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_krognarr._aacircle(aura,
                                        (*_NS_krognarr.PALETTE["crystal_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_krognarr._alpha((30 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_krognarr._aacircle(aura,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Floating crystal motes around body.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 42 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_krognarr.PALETTE["dust_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_krognarr.PALETTE["crystal_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_krognarr.PALETTE["crystal_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_krognarr.PALETTE["amber_dark"], 180),
                            (40, 24, 90, 14), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_krognarr.PALETTE["crystal_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_krognarr.PALETTE["crystal_hot"],
                                        _NS_krognarr._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q — STONE STRIKE (jagged crystal projectile)
    # ============================================================
    def _draw_stone_strike(surface, boss, x, y, timer, phase):
        """Jagged crystal shard hurled forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_krognarr._target_position(boss, x, y)

        if progress < 0.2:
            # Charge in fist.
            t = progress / 0.2
            hand_x = x + facing * 28
            hand_y = y - 4
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_krognarr._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_darkest"], alpha),
                                        (hand_x, hand_y), r)
            # Jagged crystal shape forming.
            _NS_krognarr._draw_crystal_shard(surface, hand_x, hand_y, cr, phase, facing)
        else:
            # Projectile flight.
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 32
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Trail.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_krognarr._alpha(230 - i * 22)
                size = max(1, 8 - i)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_darkest"], alpha),
                                        (px, py), size)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_light"], alpha),
                                        (px, py), max(1, size - 3))

                if i < 4:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                        pygame.draw.rect(surface,
                                         (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Bright jagged shard.
            _NS_krognarr._draw_crystal_shard(surface, bx, by, 8, phase, facing)

            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(10 + st * 26)
                alpha = _NS_krognarr._alpha(240 * (1 - st))
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_light"], alpha),
                                        (tx, ty), max(1, radius - 11), 1)

                # Crystal shards flying outward.
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                     (ex, ey, 3, 3))
                    pygame.draw.rect(surface,
                                     (*_NS_krognarr.PALETTE["crystal_shine"], alpha),
                                     (ex, ey, 1, 1))

    def _draw_crystal_shard(surface, cx, cy, size, phase, facing):
        """Draw a jagged pointed crystal shard."""
        glow = math.sin(phase * 3) * 0.2 + 0.8

        # Elongated diamond pointed toward facing direction.
        tip_x = cx + facing * size
        back_x = cx - facing * size

        shape = [
            (tip_x, cy),
            (cx + facing * 1, cy - size // 2),
            (back_x + facing * 1, cy - 1),
            (back_x, cy),
            (back_x + facing * 1, cy + 1),
            (cx + facing * 1, cy + size // 2),
        ]
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_darkest"], shape)
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_dark"], [
            (tip_x - facing, cy),
            (cx, cy - size // 2 + 1),
            (back_x + facing, cy),
            (cx, cy + size // 2 - 1),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_mid"], [
            (tip_x - facing * 2, cy),
            (cx, cy - size // 3),
            (back_x + facing * 2, cy),
            (cx, cy + size // 3),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_light"], [
            (tip_x - facing * 3, cy),
            (cx, cy - size // 4),
            (cx - facing, cy),
        ])
        # Bright tip.
        pygame.draw.rect(surface,
                         _NS_krognarr._clamp((
                             _NS_krognarr.PALETTE["crystal_hot"][0] * glow,
                             _NS_krognarr.PALETTE["crystal_hot"][1] * glow,
                             _NS_krognarr.PALETTE["crystal_hot"][2] * glow,
                         )),
                         (tip_x - facing, cy, 1, 1))
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                         (tip_x, cy, 1, 1))

    # ============================================================
    # SKILL W — SEISMIC TREMOR (ground shockwave)
    # ============================================================
    def _draw_seismic_ground(surface, boss, x, y, timer, phase):
        """Concentric shockwave rings on ground."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple expanding rings.
        for ring_i in range(3):
            ring_offset = ring_i * 0.25
            ring_t = (progress + ring_offset) % 1.0
            r = int(15 + ring_t * 70)
            alpha = _NS_krognarr._alpha(220 * (1 - ring_t))
            if alpha <= 0:
                continue
            # Perspective ellipse.
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["crystal_darkest"], alpha),
                                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["crystal_dark"], alpha),
                                (x - r + 2, y + 42 - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 2)
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                (x - r + 4, y + 42 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 1)

    def _draw_seismic_foreground(surface, boss, x, y, timer, phase):
        """Rocks bouncing up + sparkles."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rocks/pebbles ejected upward around boss.
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.3
            dist = 35 + int(math.sin(phase * 2 + i) * 15)
            rock_x = x + int(math.cos(angle) * dist)
            rock_y_base = y + 42 + int(math.sin(angle) * dist * 0.35)

            # Bouncing motion.
            bounce_t = (phase * 1.5 + i * 0.3) % 1.0
            rock_y = rock_y_base - int(math.sin(bounce_t * math.pi) * 20)

            alpha = _NS_krognarr._alpha(220 * (1 - bounce_t * 0.3))
            size = 2 + (i % 2)

            # Rock.
            pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["shadow_deep"], alpha),
                             (rock_x + 1, rock_y + 1, size + 1, size + 1))
            pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_darkest"], alpha),
                             (rock_x, rock_y, size + 1, size + 1))
            pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_dark"], alpha),
                             (rock_x, rock_y, size, size))
            pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_mid"], alpha),
                             (rock_x, rock_y, size - 1 if size > 1 else 1, 1))

        # Crystal sparkles.
        for i in range(15):
            angle = i * math.pi * 2 / 15 + phase * 0.5
            sp_dist = 40 + int(math.sin(phase + i) * 20)
            sx = x + int(math.cos(angle) * sp_dist)
            sy = y + 42 + int(math.sin(angle) * sp_dist * 0.35)
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_hot"],
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                             (sx, sy, 1, 1))

    # ============================================================
    # SKILL E — CRYSTAL RAMPART (crystal wall)
    # ============================================================
    def _draw_rampart_ground(surface, boss, x, y, timer, phase):
        """Small runic circle at wall base."""
        tx, ty = _NS_krognarr._target_position(boss, x, y)
        # Wall is placed slightly in front of boss.
        wall_x = x + boss.direction * 50
        wall_y = y + 42

        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        alpha = _NS_krognarr._alpha(200)
        r = 30
        pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["crystal_darkest"], alpha),
                            (wall_x - r, wall_y - r // 3, r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["crystal_dark"], alpha),
                            (wall_x - r + 3, wall_y - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_rampart_foreground(surface, boss, x, y, timer, phase):
        """Rising crystal spires forming a wall."""
        wall_x = x + boss.direction * 50
        wall_y = y + 42

        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Growth phase (crystals rise from ground).
        if progress < 0.35:
            growth_t = progress / 0.35
        else:
            growth_t = 1.0

        # 5 crystal spires side by side.
        spires = [
            (-18, 22),  # (x_offset, max_height)
            (-9, 34),
            (0, 40),   # tallest center
            (9, 34),
            (18, 22),
        ]

        for i, (spire_x_off, max_h) in enumerate(spires):
            spire_x = wall_x + spire_x_off
            current_h = int(max_h * growth_t)
            if current_h < 3:
                continue

            spire_base_y = wall_y
            spire_tip_y = wall_y - current_h

            # Pulse glow.
            glow = math.sin(phase * 1.5 + i * 0.4) * 0.3 + 0.7

            # Wide base, narrow tip (elongated diamond).
            width = 5 + (2 if i == 2 else 1 if i in (1, 3) else 0)

            shape = [
                (spire_x, spire_tip_y),
                (spire_x + width, spire_base_y - current_h // 3),
                (spire_x + width - 1, spire_base_y),
                (spire_x - width + 1, spire_base_y),
                (spire_x - width, spire_base_y - current_h // 3),
            ]
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                                [(p[0] + 2, p[1] + 2) for p in shape])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_darkest"], shape)

            # Facet layers.
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_dark"], [
                (spire_x, spire_tip_y),
                (spire_x + width - 1, spire_base_y - current_h // 3),
                (spire_x + width - 2, spire_base_y - 1),
                (spire_x - width + 2, spire_base_y - 1),
                (spire_x - width + 1, spire_base_y - current_h // 3),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_mid"], [
                (spire_x, spire_tip_y + 1),
                (spire_x + width - 2, spire_base_y - current_h // 3),
                (spire_x, spire_base_y - 2),
            ])
            _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_light"], [
                (spire_x, spire_tip_y + 2),
                (spire_x + 1, spire_base_y - current_h // 2),
                (spire_x, spire_base_y - current_h // 3),
            ])

            # Bright edge line.
            pygame.draw.line(surface, _NS_krognarr.PALETTE["crystal_hot"],
                             (spire_x, spire_tip_y + 1),
                             (spire_x, spire_base_y - 3), 1)

            # Glowing tip.
            pygame.draw.rect(surface,
                             _NS_krognarr._clamp((
                                 _NS_krognarr.PALETTE["crystal_hot"][0] * glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][1] * glow,
                                 _NS_krognarr.PALETTE["crystal_hot"][2] * glow,
                             )),
                             (spire_x, spire_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                             (spire_x, spire_tip_y, 1, 1))

            # Glow halo at tip.
            for r in range(5, 0, -1):
                alpha = _NS_krognarr._alpha(120 * (5 - r) / 5 * glow)
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                        (spire_x, spire_tip_y), r)

        # Rising sparkles.
        for i in range(10):
            spark_t = (phase * 1.2 + i * 0.15) % 1.0
            sx = wall_x - 20 + i * 4
            sy = wall_y - int(spark_t * 30)
            alpha = _NS_krognarr._alpha(240 * (1 - spark_t) * growth_t)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_shine"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL R — EARTH ERUPTION (massive crystal eruption)
    # ============================================================
    def _draw_eruption_ground(surface, boss, x, y, timer, phase):
        """Warning circle then massive crater."""
        tx, ty = _NS_krognarr._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.35:
            # Warning circle.
            t = progress / 0.35
            r = int(15 + t * 25)
            alpha = _NS_krognarr._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["amber_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning runes.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_light"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_krognarr.PALETTE["amber_light"],
                                 (sx, sy, 1, 1))
        else:
            # Aftermath crater.
            t = (progress - 0.35) / 0.65
            r = int(40 + t * 15)
            alpha = _NS_krognarr._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["earth_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["earth_mid"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_krognarr.PALETTE["amber_dark"], alpha),
                                (tx - r + 10, ty - r // 3 + 4,
                                 r * 2 - 20, r * 2 // 3 - 8))

    def _draw_eruption_foreground(surface, boss, x, y, timer, phase):
        """Massive crystals bursting from ground."""
        tx, ty = _NS_krognarr._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.35:
            # Wind-up: small tremors + light gathering.
            t = progress / 0.35
            for i in range(6):
                angle = i * math.pi / 3 + phase
                dist = int(20 * (1 - t))
                px = tx + int(math.cos(angle) * dist)
                py = ty + int(math.sin(angle) * dist * 0.4)
                alpha = _NS_krognarr._alpha(200 * t)
                pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                 (px, py, 2, 2))
        elif progress < 0.7:
            # ERUPTION! Massive crystals bursting up.
            t = (progress - 0.35) / 0.35

            # Central massive crystal.
            main_h = int(t * 60)
            _NS_krognarr._draw_eruption_crystal(surface, tx, ty, main_h, 10, phase, 0)

            # Surrounding crystals.
            crystal_configs = [
                (-20, 45, 6, 0.3),
                (20, 45, 6, 0.6),
                (-35, 30, 5, 0.9),
                (35, 30, 5, 1.2),
                (-12, 55, 7, 0.15),
                (12, 55, 7, 0.45),
            ]
            for ox, max_h_c, w, phase_off in crystal_configs:
                h_c = int(max_h_c * min(1.0, t * 1.3))
                if h_c > 3:
                    _NS_krognarr._draw_eruption_crystal(surface, tx + ox, ty,
                                                         h_c, w, phase, phase_off)

            # Debris flying up.
            for i in range(20):
                angle = i * math.pi / 10
                debris_t = (phase * 2 + i * 0.1) % 1.0
                dx = tx + int(math.cos(angle) * (10 + debris_t * 40))
                dy = ty - int(debris_t * 50) + int(math.sin(angle) * 10)
                alpha = _NS_krognarr._alpha(230 * (1 - debris_t))
                if alpha > 0:
                    # Stone chunks.
                    pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_dark"], alpha),
                                     (dx, dy, 3, 3))
                    pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["stone_mid"], alpha),
                                     (dx, dy, 2, 2))
                    # Crystal sparkle.
                    if i % 2 == 0:
                        pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                         (dx + 1, dy + 1, 1, 1))

            # Massive golden burst light.
            burst_r = int(30 + t * 20)
            for r in range(burst_r, 5, -3):
                alpha = _NS_krognarr._alpha(80 * (burst_r - r) / burst_r * (1 - t))
                _NS_krognarr._aacircle(surface,
                                        (*_NS_krognarr.PALETTE["amber_light"], alpha),
                                        (tx, ty - 20), r)
        else:
            # Aftermath: crystals slowly sink/fade.
            t = (progress - 0.7) / 0.3
            fade = 1 - t

            main_h = int(60 * fade)
            _NS_krognarr._draw_eruption_crystal(surface, tx, ty, main_h, 10, phase, 0)

            # Lingering sparkles.
            for i in range(10):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 20)
                ry = ty - int(rise_t * 30)
                alpha = _NS_krognarr._alpha(200 * fade * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_krognarr.PALETTE["crystal_hot"], alpha),
                                     (rx, ry, 2, 2))

    def _draw_eruption_crystal(surface, cx, cy_base, height, width, phase, phase_off):
        """Draw a large upward-pointing crystal for eruption."""
        if height < 3:
            return
        tip_y = cy_base - height
        glow = math.sin(phase * 1.5 + phase_off) * 0.3 + 0.7

        # Elongated crystal shape.
        shape = [
            (cx, tip_y),
            (cx + width, cy_base - height // 2),
            (cx + width - 2, cy_base),
            (cx - width + 2, cy_base),
            (cx - width, cy_base - height // 2),
        ]
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in shape])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_darkest"], shape)

        # Facet.
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_dark"], [
            (cx, tip_y),
            (cx + width - 1, cy_base - height // 2),
            (cx + width - 3, cy_base - 1),
            (cx - width + 3, cy_base - 1),
            (cx - width + 1, cy_base - height // 2),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_mid"], [
            (cx, tip_y + 1),
            (cx + width - 2, cy_base - height // 2),
            (cx, cy_base - 2),
        ])
        _NS_krognarr._poly(surface, _NS_krognarr.PALETTE["crystal_light"], [
            (cx, tip_y + 2),
            (cx + 1, cy_base - height // 2),
            (cx, cy_base - height // 3),
        ])

        # Bright edge.
        pygame.draw.line(surface, _NS_krognarr.PALETTE["crystal_hot"],
                         (cx, tip_y + 1), (cx, cy_base - 3), 1)

        # Glowing tip.
        pygame.draw.rect(surface,
                         _NS_krognarr._clamp((
                             _NS_krognarr.PALETTE["crystal_hot"][0] * glow,
                             _NS_krognarr.PALETTE["crystal_hot"][1] * glow,
                             _NS_krognarr.PALETTE["crystal_hot"][2] * glow,
                         )),
                         (cx, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_krognarr.PALETTE["crystal_shine"],
                         (cx, tip_y, 1, 1))

        # Halo at tip.
        for r in range(6, 0, -1):
            alpha = _NS_krognarr._alpha(140 * (6 - r) / 6 * glow)
            _NS_krognarr._aacircle(surface,
                                    (*_NS_krognarr.PALETTE["crystal_mid"], alpha),
                                    (cx, tip_y), r)


# ====================================================================
# raz.py
# ====================================================================

# ====================================================================
# RAZ - The Heat of Despair - Mini Boss (Fire Monk)
# ====================================================================


class _NS_raz:
    """Namespace raz - Fire monk mini boss (floating)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (dark tan/brown - monk)
        "skin_darkest": (45, 22, 15),
        "skin_dark": (95, 55, 32),
        "skin_mid": (155, 95, 60),
        "skin_light": (210, 145, 95),
        "skin_shine": (245, 185, 135),

        # Hair (black)
        "hair_darkest": (8, 5, 10),
        "hair_dark": (25, 18, 22),
        "hair_mid": (55, 42, 48),
        "hair_light": (95, 78, 85),

        # Cloth pants (dark brown-black)
        "cloth_darkest": (18, 12, 10),
        "cloth_dark": (45, 32, 22),
        "cloth_mid": (85, 62, 42),
        "cloth_light": (135, 100, 68),

        # Red sash/bandana
        "red_darkest": (55, 8, 12),
        "red_dark": (115, 20, 25),
        "red_mid": (185, 35, 40),
        "red_light": (235, 65, 60),
        "red_shine": (255, 145, 130),

        # Metal armor (dark iron - belt/wristbands)
        "armor_darkest": (12, 10, 15),
        "armor_dark": (35, 30, 38),
        "armor_mid": (75, 68, 82),
        "armor_light": (128, 122, 140),

        # Gold accents (small trim)
        "gold_dark": (105, 72, 25),
        "gold_mid": (185, 138, 55),
        "gold_light": (240, 205, 115),

        # FIRE (main FX - orange-red flames)
        "fire_darkest": (55, 10, 5),
        "fire_dark": (135, 35, 8),
        "fire_mid": (230, 90, 20),
        "fire_light": (255, 160, 55),
        "fire_hot": (255, 220, 120),
        "fire_shine": (255, 250, 200),
        "fire_white": (255, 255, 240),

        # Ember (deep red glow)
        "ember_dark": (95, 20, 10),
        "ember_mid": (180, 55, 20),
        "ember_light": (240, 120, 45),

        # Eye glow (bright orange)
        "eye_dark": (85, 30, 5),
        "eye_mid": (220, 110, 25),
        "eye_light": (255, 200, 90),
        "eye_glow": (255, 245, 190),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 1, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_raz._clamp(color)
        if _NS_raz.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_raz._clamp(color)
        if _NS_raz.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_raz._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_raz(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_raz._detect_moving(boss)
        _NS_raz._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_raz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_raz._draw_fire_aura(surface, x, y, pulse)
        _NS_raz._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX
        if active_skill == "w":
            _NS_raz._draw_searing_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_raz._draw_surge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_raz._draw_gloom_ground(surface, boss, x, y, skill_timer, pulse)

        # BODY
        if active_skill == "e":
            _NS_raz._draw_surge_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_raz._draw_searing_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_raz._draw_gloom_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_raz._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_raz._draw_float_move(surface, boss, x, y)
        else:
            _NS_raz._draw_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_raz._draw_overdrive_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_raz._draw_searing_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_raz._draw_surge_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_raz._draw_gloom_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_raz_previous_timer", 0))
        active = bool(getattr(boss, "_raz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._raz_attack_active = True
            boss._raz_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._raz_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._raz_attack_frame = int(getattr(boss, "_raz_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._raz_attack_active = False
            boss._raz_attack_frame = 0
            active = False

        boss._raz_previous_timer = timer
        boss._raz_attack_progress = (
            min(1.0, getattr(boss, "_raz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_raz_last_x"):
            boss._raz_last_x = boss.x
            boss._raz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._raz_last_x)
        dy = abs(boss.y - boss._raz_last_y)
        boss._raz_last_x = boss.x
        boss._raz_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.5) * 6)
        float_sway = int(math.sin(boss.pulse * 0.35) * 2)
        _NS_raz._draw_shadow_float(surface, x, y + 52, boss.pulse, intensity=1.0)
        _NS_raz._draw_fire_wisps(surface, x, y + 46, boss.pulse, intensity=1.0)
        _NS_raz._draw_body(surface, x + float_sway, y + float_bob,
                            boss.direction, boss.pulse, "idle")

    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.7
        float_bob = int(math.sin(phase * 0.7) * 5)
        float_sway = int(math.sin(phase * 0.5) * 2)
        _NS_raz._draw_shadow_float(surface, x + float_sway, y + 52, phase,
                                    intensity=0.85)
        _NS_raz._draw_fire_wisps(surface, x + float_sway, y + 46, phase,
                                  intensity=1.5, trail=True, facing=boss.direction)
        _NS_raz._draw_body(surface, x + float_sway, y + float_bob,
                            boss.direction, phase, "float")

    def _draw_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_raz_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_raz_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Fire punch - quick jab
        if progress < 0.15:
            t = progress / 0.15
            lunge = -int(t * 3) * facing
            lift = int(t * 2)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        elif progress < 0.35:
            t = (progress - 0.15) / 0.20
            t_ease = 1 - (1 - t) ** 2
            lunge = int((-3 + t_ease * 16)) * facing
            lift = int(2 - t_ease * 3)
            float_bob = 0
        else:
            t = (progress - 0.35) / 0.65
            lunge = int(13 * (1 - t)) * facing
            lift = int(-1 + t)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4 * t)

        _NS_raz._draw_shadow_float(surface, x + lunge, y + 52, boss.pulse,
                                    intensity=0.9)
        _NS_raz._draw_fire_wisps(surface, x + lunge, y + 46, boss.pulse,
                                  intensity=1.3)
        _NS_raz._draw_body(surface, x + lunge, y - lift + float_bob,
                            facing, boss.pulse, "attack", progress)
        # Punch impact FX
        _NS_raz._draw_punch_impact(surface, boss, x + lunge,
                                    y - lift + float_bob, progress)

    def _draw_surge_body(surface, boss, x, y, timer, phase):
        """Energy Surge - focused stance."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        float_bob = int(math.sin(progress * math.pi * 3) * -3)

        _NS_raz._draw_shadow_float(surface, x, y + 52, phase, intensity=0.85)
        _NS_raz._draw_fire_wisps(surface, x, y + 46, phase, intensity=1.8)
        # Focused stance (fists together at chest)
        _NS_raz._draw_body(surface, x, y + float_bob, boss.direction, phase,
                            "surge", attack_progress=progress)

    def _draw_searing_body(surface, boss, x, y, timer, phase):
        """Searing Fist - dash forward."""
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_raz._target_position(boss, x, y)

        if progress < 0.75:
            t = progress / 0.75
            t_ease = 1 - (1 - t) ** 3
            cx = int(x + (tx - x) * t_ease * 0.9)
            cy = int(y + (ty - y) * t_ease * 0.9)
        else:
            cx = int(x + (tx - x) * 0.9)
            cy = int(y + (ty - y) * 0.9)

        float_bob = int(math.sin(phase * 0.5) * 3)
        _NS_raz._draw_shadow_float(surface, cx, cy + 52, phase, intensity=0.8)
        _NS_raz._draw_fire_wisps(surface, cx, cy + 46, phase, intensity=1.9,
                                  trail=True, facing=boss.direction)
        # Attack pose (fist forward)
        _NS_raz._draw_body(surface, cx, cy + float_bob, boss.direction, phase,
                            "attack", attack_progress=0.35)

    def _draw_gloom_body(surface, boss, x, y, timer, phase):
        """Death Gloom - leap up then crash down."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_raz._target_position(boss, x, y)

        if progress < 0.35:
            # LEAP UP (offscreen)
            t = progress / 0.35
            t_ease = 1 - (1 - t) ** 2
            leap_h = int(t_ease * 200)
            cx = x
            cy = y - leap_h
            _NS_raz._draw_shadow_float(surface, x, y + 52, phase, intensity=0.6 * (1 - t_ease))
            if t_ease < 0.9:
                _NS_raz._draw_fire_wisps(surface, cx, cy + 46, phase, intensity=1.5,
                                          trail=True, facing=1)
                _NS_raz._draw_body(surface, cx, cy, boss.direction, phase, "attack",
                                    attack_progress=0.35)
            # Rising fire trail
            for i in range(int(t * 15)):
                fy = y - int((i / 15) * leap_h)
                alpha = _NS_raz._alpha(220 * (1 - i / 15))
                fx = x + int(math.sin(phase + i) * 4)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha), (fx, fy), 4)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha), (fx, fy), 3)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha), (fx, fy), 2)
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_white"], alpha),
                    (fx, fy, 1, 1))
        elif progress < 0.55:
            # AIRBORNE - preparing to crash (offscreen, invisible)
            pass
        elif progress < 0.75:
            # CRASH DOWN
            t = (progress - 0.55) / 0.20
            t_ease = t ** 2
            crash_y = int(ty - (1 - t_ease) * 250)
            cx = tx
            cy = crash_y
            _NS_raz._draw_shadow_float(surface, tx, ty + 52, phase, intensity=t_ease * 0.9)
            _NS_raz._draw_fire_wisps(surface, cx, cy + 46, phase, intensity=2.0,
                                      trail=True, facing=1)
            _NS_raz._draw_body(surface, cx, cy, boss.direction, phase, "attack",
                                attack_progress=0.35)

            # Falling fire meteor trail (from above to boss)
            for i in range(20):
                trail_t = i / 20
                trail_y = int(crash_y - trail_t * 100)
                trail_x = tx + int(math.sin(phase * 2 + i) * 4)
                alpha = _NS_raz._alpha(240 * (1 - trail_t) * t_ease)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (trail_x, trail_y), 6)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (trail_x, trail_y), 5)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (trail_x, trail_y), 4)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (trail_x, trail_y), 2)
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_white"], alpha),
                    (trail_x, trail_y, 1, 1))
        else:
            # LANDED - standing at destination
            float_bob = int(math.sin(phase * 0.5) * 3)
            _NS_raz._draw_shadow_float(surface, tx, ty + 52, phase, intensity=1.0)
            _NS_raz._draw_fire_wisps(surface, tx, ty + 46, phase, intensity=1.8)
            _NS_raz._draw_body(surface, tx, ty + float_bob, boss.direction, phase, "idle")

    # ============================================================
    # BODY (Fire Monk)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw fire monk body."""
        # Legs (baggy pants)
        _NS_raz._draw_legs(surface, cx, cy + 18, facing, phase, action, attack_progress)

        # Waist / red sash
        _NS_raz._draw_waist(surface, cx, cy + 6, facing, phase)

        # Torso (bare muscular chest with flame tattoos)
        _NS_raz._draw_torso(surface, cx, cy - 8, facing, phase, action)

        # Back arm with flame fist
        _NS_raz._draw_arm_back(surface, cx, cy - 6, facing, phase, action, attack_progress)

        # Head with topknot
        _NS_raz._draw_head(surface, cx, cy - 22, facing, phase, action)

        # Front arm with flame fist (punching)
        _NS_raz._draw_arm_front(surface, cx, cy - 6, facing, phase, action, attack_progress)

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Baggy monk pants legs."""
        if action in ("idle", "float", "surge"):
            sway = math.sin(phase * 0.6) * 1
            bx = cx - 5 + int(sway)
            by = cy - 1
            _NS_raz._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 5 - int(sway)
            fy = cy
            _NS_raz._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
        elif action == "attack" and attack_progress < 0.4:
            # Combat stance - one leg forward
            bx = cx - 6
            by = cy
            _NS_raz._draw_leg(surface, bx, by, facing, back=True)
            fx = cx + 6
            fy = cy
            _NS_raz._draw_leg(surface, fx, fy, facing, back=False)
        else:
            bx = cx - 5
            by = cy - 1
            _NS_raz._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 5
            fy = cy - 1
            _NS_raz._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)

    def _draw_leg_float(surface, cx, cy, facing, back=False, phase=0):
        """Floating leg with fire wisp underneath (baggy pants)."""
        # Thigh (baggy pants - wider)
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 4, cy - 8, 9, 10))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 8, 8, 9))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (cx - 3, cy - 8, 6, 8))
        if not back:
            pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_mid"],
                             (cx - 2, cy - 7, 3, 6))
            pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_light"],
                             (cx - 1, cy - 6, 1, 4))

        # Rope tie mid-thigh (monk style)
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 4, 8, 1))

        # Lower leg (still baggy but tighter)
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 3, cy + 2, 7, 6))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 3, cy + 2, 6, 5))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (cx - 2, cy + 2, 4, 4))

        # Ankle wrap (dark cloth)
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 3, cy + 6, 7, 2))

        # Bare foot (monks go barefoot!)
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 3, cy + 8, 7, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_darkest"],
                         (cx - 3, cy + 8, 6, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_dark"],
                         (cx - 2, cy + 8, 4, 2))
        if not back:
            pygame.draw.rect(surface, _NS_raz.PALETTE["skin_mid"],
                             (cx - 2, cy + 8, 3, 1))

        # FIRE WISP under foot
        wisp_t = (phase * 0.8 + cx * 0.1) % 1.0
        wy = cy + 12 + int(wisp_t * 8)
        alpha = _NS_raz._alpha(200 * (1 - wisp_t))
        if alpha > 0 and not back:
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                (cx, wy), 3)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                (cx, wy), 2)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (cx, wy), 1)
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_white"], alpha),
                (cx, wy, 1, 1))

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Planted leg (combat)."""
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 4, cy - 8, 9, 10))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 8, 8, 9))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (cx - 3, cy - 8, 6, 8))
        if not back:
            pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_mid"],
                             (cx - 2, cy - 7, 3, 6))

        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 4, 8, 1))

        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 3, cy + 2, 7, 5))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 3, cy + 2, 6, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (cx - 2, cy + 2, 4, 3))

        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 3, cy + 5, 7, 2))

        # Foot
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 4, cy + 7, 9, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_darkest"],
                         (cx - 4, cy + 7, 8, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_dark"],
                         (cx - 3, cy + 7, 6, 2))
        if not back:
            pygame.draw.rect(surface, _NS_raz.PALETTE["skin_mid"],
                             (cx - 3, cy + 7, 5, 1))

    def _draw_waist(surface, cx, cy, facing, phase):
        """Belt/sash with red hanging cloth."""
        # Dark belt
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 11, cy - 2, 23, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (cx - 11, cy - 2, 22, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (cx - 11, cy - 2, 22, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_mid"],
                         (cx - 10, cy - 1, 20, 2))

        # Metal buckle (dark iron)
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 3, cy - 2, 7, 5))
        pygame.draw.rect(surface, _NS_raz.PALETTE["armor_darkest"],
                         (cx - 3, cy - 2, 6, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["armor_dark"],
                         (cx - 2, cy - 2, 5, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["armor_mid"],
                         (cx - 2, cy - 2, 4, 2))

        # Fire crystal in buckle
        pygame.draw.rect(surface, _NS_raz.PALETTE["fire_dark"],
                         (cx - 1, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["fire_mid"],
                         (cx, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_raz.PALETTE["fire_hot"],
                         (cx, cy - 1, 1, 1))

        # RED SASH hanging down (dramatic side piece)
        sway = math.sin(phase * 0.8) * 2
        sash_pts = [
            (cx - 8, cy + 1),
            (cx - 4, cy + 1),
            (cx - 3 + int(sway * 0.5), cy + 10),
            (cx - 5 + int(sway), cy + 16),
            (cx - 7 + int(sway * 1.2), cy + 14),
            (cx - 9, cy + 8),
        ]
        _NS_raz._poly(surface, _NS_raz.PALETTE["shadow_deep"],
                       [(px + 1, py + 1) for px, py in sash_pts])
        _NS_raz._poly(surface, _NS_raz.PALETTE["red_darkest"], sash_pts)
        _NS_raz._poly(surface, _NS_raz.PALETTE["red_dark"], [
            (cx - 7, cy + 2),
            (cx - 4, cy + 2),
            (cx - 4 + int(sway * 0.5), cy + 9),
            (cx - 5 + int(sway), cy + 15),
            (cx - 6 + int(sway * 1.2), cy + 13),
            (cx - 8, cy + 7),
        ])
        _NS_raz._poly(surface, _NS_raz.PALETTE["red_mid"], [
            (cx - 6, cy + 3),
            (cx - 5, cy + 3),
            (cx - 5 + int(sway * 0.5), cy + 12),
            (cx - 7, cy + 6),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_raz.PALETTE["red_light"],
                         (cx - 6, cy + 3),
                         (cx - 6 + int(sway * 0.5), cy + 11), 1)

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Bare muscular chest with flame tattoo marks."""
        breath = math.sin(phase * 0.6) * 1

        # Muscular torso
        torso_pts = [
            (cx - 9, cy - 3),
            (cx - 10, cy + 3),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 10, cy + 3),
            (cx + 9, cy - 3),
            (cx + 6, cy - 7),
            (cx - 6, cy - 7),
        ]
        _NS_raz._poly(surface, _NS_raz.PALETTE["shadow_deep"],
                       [(px + 1, py + 1) for px, py in torso_pts])
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_darkest"], torso_pts)

        # Mid skin
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_dark"], [
            (cx - 8, cy - 2 + int(breath)),
            (cx - 9, cy + 3),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 9, cy + 3),
            (cx + 8, cy - 2 + int(breath)),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ])

        # Highlight
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_mid"], [
            (cx - 5, cy - 1 + int(breath)),
            (cx - 7, cy + 3),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 3),
            (cx + 5, cy - 1 + int(breath)),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])

        # Pectoral definition (bright)
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_light"], [
            (cx - 4, cy + int(breath)),
            (cx - 1, cy + int(breath)),
            (cx - 2, cy + 4),
            (cx - 4, cy + 3),
        ])
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_light"], [
            (cx + 1, cy + int(breath)),
            (cx + 4, cy + int(breath)),
            (cx + 4, cy + 3),
            (cx + 2, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_shine"],
                         (cx - 3, cy + 1 + int(breath), 2, 1))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_shine"],
                         (cx + 2, cy + 1 + int(breath), 2, 1))

        # Central chest divide
        pygame.draw.line(surface, _NS_raz.PALETTE["skin_darkest"],
                         (cx, cy - 4 + int(breath)), (cx, cy + 8), 1)

        # Ab muscles
        for y_off in (5, 8):
            pygame.draw.line(surface, _NS_raz.PALETTE["skin_darkest"],
                             (cx - 3, cy + y_off), (cx + 3, cy + y_off), 1)

        # FLAME TATTOO MARKS on chest (glowing orange marks)
        tattoo_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Curved flame tattoo lines
        tattoo_alpha = _NS_raz._alpha(220 * tattoo_pulse)
        # Left side tattoo (curved lines going up)
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], tattoo_alpha),
            (cx - 6, cy + 3), (cx - 5, cy - 3 + int(breath)), 2)
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], tattoo_alpha),
            (cx - 6, cy + 3), (cx - 5, cy - 3 + int(breath)), 1)
        pygame.draw.rect(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], tattoo_alpha),
            (cx - 5, cy - 3 + int(breath), 1, 1))

        # Right side tattoo
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], tattoo_alpha),
            (cx + 6, cy + 3), (cx + 5, cy - 3 + int(breath)), 2)
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], tattoo_alpha),
            (cx + 6, cy + 3), (cx + 5, cy - 3 + int(breath)), 1)
        pygame.draw.rect(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], tattoo_alpha),
            (cx + 5, cy - 3 + int(breath), 1, 1))

        # Small central flame tattoo
        pygame.draw.rect(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], tattoo_alpha),
            (cx, cy + 2, 1, 3))
        pygame.draw.rect(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], tattoo_alpha),
            (cx, cy + 2, 1, 1))

        # Shoulder tattoo dots (glowing embers on shoulders)
        for side_sign in (-1, 1):
            sx = cx + side_sign * 7
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], tattoo_alpha),
                (sx, cy - 5), 2)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], tattoo_alpha),
                (sx, cy - 5), 1)

    def _draw_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm with flame fist."""
        base_x = cx - facing * 8
        base_y = cy

        if action == "attack":
            if attack_progress < 0.15:
                arm_angle = -0.4
            elif attack_progress < 0.35:
                t = (attack_progress - 0.15) / 0.20
                arm_angle = -0.4 + t * 0.6
            else:
                arm_angle = 0.1
        elif action == "surge":
            # Both fists together at chest
            arm_angle = -0.6 + math.sin(phase * 2) * 0.1
        else:
            arm_angle = -0.1 + math.sin(phase * 0.6) * 0.08

        elbow_x = base_x - facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)
        hand_x = elbow_x + facing * int(2 + math.cos(arm_angle + 0.4) * 3)
        hand_y = elbow_y + int(5 + math.sin(arm_angle + 0.4) * 3)

        # Upper arm (bare skin muscular)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["shadow_deep"],
                         (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_darkest"],
                         (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_dark"],
                         (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_mid"],
                         (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)

        # Bicep bulge
        mid_arm_x = int((base_x + elbow_x) / 2)
        mid_arm_y = int((base_y + elbow_y) / 2)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_dark"],
                           (mid_arm_x, mid_arm_y - 1), 3)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_mid"],
                           (mid_arm_x, mid_arm_y - 2), 2)

        # Flame tattoo on arm (glowing line)
        tattoo_alpha = _NS_raz._alpha(200)
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], tattoo_alpha),
            (base_x, base_y + 1), (elbow_x, elbow_y + 1), 1)

        # Forearm
        _NS_raz._aaline(surface, _NS_raz.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 5)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_mid"],
                         (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Wrist wrap (dark cloth)
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (mid_x - 2, mid_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (mid_x - 1, mid_y - 1, 3, 2))

        # FLAME FIST
        _NS_raz._draw_flame_fist(surface, hand_x, hand_y, facing, phase,
                                   is_back=True, action=action,
                                   attack_progress=attack_progress)

    def _draw_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with punching flame fist."""
        base_x = cx + facing * 8
        base_y = cy

        if action == "attack":
            if attack_progress < 0.15:
                # Draw back
                t = attack_progress / 0.15
                arm_angle = -0.3 - t * 0.6
            elif attack_progress < 0.35:
                # PUNCH forward extension
                t = (attack_progress - 0.15) / 0.20
                t_ease = 1 - (1 - t) ** 2
                # Arm extends forward horizontally
                arm_angle = -0.9 + t_ease * 1.4  # ends at ~0.5 (forward)
            else:
                # Recovery
                t = (attack_progress - 0.35) / 0.65
                arm_angle = 0.5 - t * 0.2
        elif action == "surge":
            arm_angle = -0.5 + math.sin(phase * 2) * 0.1
        else:
            arm_angle = 0.3 + math.sin(phase * 0.6 + 0.5) * 0.08

        # For punch, extend arm more horizontally
        if action == "attack" and 0.15 <= attack_progress < 0.5:
            elbow_x = base_x + facing * int(5 + math.cos(arm_angle) * 5)
            elbow_y = base_y + int(math.sin(arm_angle) * 2)
            hand_x = elbow_x + facing * int(8 + math.cos(arm_angle) * 6)
            hand_y = elbow_y + int(math.sin(arm_angle) * 2)
        else:
            elbow_x = base_x + facing * int(4 + math.cos(arm_angle) * 3)
            elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)
            hand_x = elbow_x + facing * int(5 + math.cos(arm_angle + 0.3) * 4)
            hand_y = elbow_y + int(4 + math.sin(arm_angle + 0.3) * 5)

        # Upper arm
        _NS_raz._aaline(surface, _NS_raz.PALETTE["shadow_deep"],
                         (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_darkest"],
                         (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_dark"],
                         (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_mid"],
                         (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_light"],
                         (base_x, base_y - 2), (elbow_x, elbow_y - 2), 1)

        # Bicep bulge (bigger during attack)
        mid_arm_x = int((base_x + elbow_x) / 2)
        mid_arm_y = int((base_y + elbow_y) / 2)
        bicep_flex = 1
        if action == "attack" and 0.1 <= attack_progress <= 0.4:
            bicep_flex = 2
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_dark"],
                           (mid_arm_x + facing, mid_arm_y - 2), 3 + bicep_flex)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_mid"],
                           (mid_arm_x + facing, mid_arm_y - 3), 2 + bicep_flex)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_light"],
                           (mid_arm_x + facing, mid_arm_y - 3), 1)

        # Flame tattoo on arm
        tattoo_alpha = _NS_raz._alpha(220)
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], tattoo_alpha),
            (base_x, base_y + 1), (elbow_x, elbow_y + 1), 1)
        pygame.draw.line(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], tattoo_alpha),
            (elbow_x, elbow_y), (hand_x, hand_y), 1)

        # Forearm
        _NS_raz._aaline(surface, _NS_raz.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 5)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_mid"],
                         (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        _NS_raz._aaline(surface, _NS_raz.PALETTE["skin_light"],
                         (elbow_x, elbow_y - 2), (hand_x, hand_y - 2), 1)

        # Wrist wrap
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_darkest"],
                         (mid_x - 2, mid_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_dark"],
                         (mid_x - 1, mid_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["cloth_mid"],
                         (mid_x, mid_y, 1, 1))

        # FLAME FIST
        _NS_raz._draw_flame_fist(surface, hand_x, hand_y, facing, phase,
                                   is_back=False, action=action,
                                   attack_progress=attack_progress)

    def _draw_flame_fist(surface, cx, cy, facing, phase, is_back=False,
                          action="idle", attack_progress=0):
        """Fist wreathed in flames."""
        # Alpha modifier
        alpha_mult = 0.85 if is_back else 1.0

        # Base fist (skin)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["shadow_deep"],
                           (cx + 1, cy + 1), 4)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_darkest"],
                           (cx, cy), 4)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_dark"],
                           (cx, cy), 3)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_mid"],
                           (cx - facing, cy - 1), 2)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["skin_light"],
                           (cx - facing, cy - 1), 1)

        # FLAMES around fist
        flame_intensity = 1.0
        if action == "attack" and 0.1 <= attack_progress <= 0.4:
            flame_intensity = 1.5
        elif action == "surge":
            flame_intensity = 1.4

        # Large flame aura
        for r in range(10, 0, -1):
            alpha = _NS_raz._alpha(120 * (10 - r) / 10 * alpha_mult * flame_intensity)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                (cx, cy), r)

        # Flame licks around fist (dancing)
        num_flames = int(6 * alpha_mult)
        for i in range(num_flames):
            angle = phase * 2 + i * math.pi * 2 / num_flames
            flame_dist = 5 + int(math.sin(phase * 3 + i) * 2)
            fx = cx + int(math.cos(angle) * flame_dist)
            fy = cy + int(math.sin(angle) * flame_dist)

            # Flame shape (tear drop)
            flame_h = 6 + int(math.sin(phase * 2 + i) * 2)
            # Direction outward from fist center
            f_angle = math.atan2(fy - cy, fx - cx)
            tip_x = fx + int(math.cos(f_angle) * flame_h)
            tip_y = fy + int(math.sin(f_angle) * flame_h)

            _NS_raz._poly(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"],
                               _NS_raz._alpha(200 * alpha_mult)),
                [(fx - 2, fy), (tip_x, tip_y), (fx + 2, fy)])
            _NS_raz._poly(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"],
                               _NS_raz._alpha(230 * alpha_mult)),
                [(fx - 1, fy), (tip_x, tip_y), (fx + 1, fy)])
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"],
                               _NS_raz._alpha(255 * alpha_mult)),
                (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_white"],
                               _NS_raz._alpha(255 * alpha_mult)),
                (tip_x, tip_y, 1, 1))

        # Central bright core (visible knuckles glow)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_hot"],
                           (cx, cy), 3)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"],
                           (cx, cy), 2)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_white"],
                           (cx, cy), 1)
        pygame.draw.rect(surface, _NS_raz.PALETTE["white"], (cx, cy, 1, 1))

        # Ember sparks flying out
        for i in range(4):
            spark_t = (phase * 3 + i * 0.25) % 1.0
            spark_angle = phase * 2 + i * math.pi / 2
            spark_r = 8 + int(spark_t * 4)
            sx = cx + int(math.cos(spark_angle) * spark_r)
            sy = cy + int(math.sin(spark_angle) * spark_r)
            alpha = _NS_raz._alpha(220 * (1 - spark_t) * alpha_mult)
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], alpha),
                (sx, sy, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with topknot + red bandana + fierce eyes."""
        # Neck
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6, 5, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_darkest"],
                         (cx - 2, cy + 6, 4, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_dark"],
                         (cx - 1, cy + 6, 3, 3))

        # Head shape
        head_pts = [
            (cx - 6, cy - 2),
            (cx - 7, cy + 2),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 7, cy + 2),
            (cx + 6, cy - 2),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ]
        _NS_raz._poly(surface, _NS_raz.PALETTE["shadow_deep"],
                       [(px + 1, py + 1) for px, py in head_pts])
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_darkest"], head_pts)

        # Face mid tone
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Face highlight
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 4, cy + 4),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])

        # Cheek highlight
        _NS_raz._poly(surface, _NS_raz.PALETTE["skin_light"], [
            (cx + facing * 1, cy - 1),
            (cx + facing * 4, cy),
            (cx + facing * 3, cy + 3),
            (cx + facing * 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_shine"],
                         (cx + facing * 3, cy, 1, 1))

        # BEARD/GOATEE (small chin patch)
        pygame.draw.rect(surface, _NS_raz.PALETTE["hair_darkest"],
                         (cx - 2, cy + 4, 5, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["hair_dark"],
                         (cx - 1, cy + 4, 3, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["hair_mid"],
                         (cx, cy + 5, 1, 1))

        # RED BANDANA across forehead
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 6, cy - 2 + 1, 13, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_darkest"],
                         (cx - 6, cy - 2, 12, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_dark"],
                         (cx - 6, cy - 2, 12, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_mid"],
                         (cx - 5, cy - 2, 10, 1))
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_light"],
                         (cx - 4, cy - 2, 4, 1))

        # Bandana knot at back
        back_dir = -facing
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_darkest"],
                         (cx + back_dir * 6 - 1, cy - 3, 3, 4))
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_dark"],
                         (cx + back_dir * 6 - 1, cy - 3, 2, 3))
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_mid"],
                         (cx + back_dir * 6, cy - 3, 1, 2))

        # Bandana tails (flowing)
        sway = math.sin(phase * 0.8) * 2
        tail1_x = cx + back_dir * 8
        tail1_y = cy
        tail2_x = tail1_x + back_dir * 3 + int(sway * 0.3)
        tail2_y = tail1_y + 4 + int(sway * 0.5)
        pygame.draw.line(surface, _NS_raz.PALETTE["red_darkest"],
                         (tail1_x, tail1_y), (tail2_x, tail2_y), 3)
        pygame.draw.line(surface, _NS_raz.PALETTE["red_mid"],
                         (tail1_x, tail1_y), (tail2_x, tail2_y), 2)
        pygame.draw.rect(surface, _NS_raz.PALETTE["red_light"],
                         (tail2_x, tail2_y, 1, 1))

        # GLOWING ORANGE EYES (fierce)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            # Halo
            for r in range(3, 0, -1):
                alpha = _NS_raz._alpha(180 * (3 - r) / 3 * eye_pulse)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["eye_mid"], alpha),
                    (ex, ey), r)
            pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_raz.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_raz.PALETTE["eye_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_raz.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_raz.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

        # Third eye tattoo/mark on forehead (small fire mark above bandana)
        mark_pulse = math.sin(phase * 3) * 0.4 + 0.6
        mark_alpha = _NS_raz._alpha(220 * mark_pulse)
        pygame.draw.rect(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], mark_alpha),
            (cx, cy - 4, 1, 2))
        pygame.draw.rect(surface,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], mark_alpha),
            (cx, cy - 4, 1, 1))

        # Nose
        pygame.draw.rect(surface, _NS_raz.PALETTE["skin_darkest"],
                         (cx, cy + 2, 1, 2))

        # TOPKNOT (hair bun tied up on top)
        _NS_raz._draw_topknot(surface, cx, cy - 6, facing, phase)

    def _draw_topknot(surface, cx, cy, facing, phase):
        """Hair tied in top bun with strands."""
        # Base hair on top of head
        pygame.draw.rect(surface, _NS_raz.PALETTE["shadow_deep"],
                         (cx - 3, cy + 1, 7, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["hair_darkest"],
                         (cx - 3, cy + 1, 6, 2))
        pygame.draw.rect(surface, _NS_raz.PALETTE["hair_dark"],
                         (cx - 2, cy + 1, 4, 1))

        # Topknot bun (rounded)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["shadow_deep"], (cx + 1, cy - 1), 4)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["hair_darkest"], (cx, cy - 2), 4)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["hair_dark"], (cx, cy - 2), 3)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["hair_mid"], (cx, cy - 3), 2)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["hair_light"], (cx - 1, cy - 4), 1)

        # Hair strand escaping from topknot (dramatic loose piece)
        sway = math.sin(phase * 0.8) * 2
        strand_end_x = cx - facing * 2 + int(sway)
        strand_end_y = cy - 8 + int(math.sin(phase) * 1)
        pygame.draw.line(surface, _NS_raz.PALETTE["hair_darkest"],
                         (cx, cy - 4), (strand_end_x, strand_end_y), 2)
        pygame.draw.line(surface, _NS_raz.PALETTE["hair_dark"],
                         (cx, cy - 4), (strand_end_x, strand_end_y), 1)
        pygame.draw.rect(surface, _NS_raz.PALETTE["hair_mid"],
                         (strand_end_x, strand_end_y, 1, 1))

    # ============================================================
    # PUNCH IMPACT FX
    # ============================================================
    def _draw_punch_impact(surface, boss, cx, cy, progress):
        """Fire punch impact - explosion at fist forward reach."""
        if progress < 0.2 or progress > 0.5:
            return

        facing = boss.direction
        if progress < 0.35:
            t = (progress - 0.2) / 0.15
        else:
            t = 1.0
        fade = 1.0 if progress <= 0.35 else max(0.0, 1 - (progress - 0.35) / 0.15)

        # Impact point (forward of fist)
        impact_x = cx + facing * 30
        impact_y = cy - 6

        # Radial fire burst
        for i in range(10):
            angle = i * math.pi / 5
            burst_len = int(20 * t)
            ex = impact_x + int(math.cos(angle) * burst_len)
            ey = impact_y + int(math.sin(angle) * burst_len * 0.7)
            alpha = _NS_raz._alpha(240 * fade)

            # Fire streak from center outward
            for streak_t_i in range(3):
                streak_t = streak_t_i / 3
                sx = int(impact_x + (ex - impact_x) * streak_t)
                sy = int(impact_y + (ey - impact_y) * streak_t)
                size = max(1, 4 - streak_t_i)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (sx, sy), size)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (sx, sy), max(1, size - 1))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (sx, sy), max(1, size - 2))

        # Central bright flash
        flash_r = int(10 + t * 8)
        for r in range(flash_r, 0, -1):
            alpha = _NS_raz._alpha(240 * fade * (flash_r - r + 1) / flash_r)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (impact_x, impact_y), r)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"], (impact_x, impact_y), 5)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_white"], (impact_x, impact_y), 3)
        _NS_raz._aacircle(surface, _NS_raz.PALETTE["white"], (impact_x, impact_y), 1)

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow_float(surface, x, y, phase, intensity=1.0):
        float_offset = math.sin(phase * 0.5) * 6
        scale = 1.0 - (float_offset + 6) / 24
        scale = max(0.55, min(1.0, scale))

        w = int(110 * scale * intensity)
        h = int(26 * scale)
        shadow = pygame.Surface((w + 20, h + 8), pygame.SRCALPHA)
        for radius in range(int(13 * scale), 0, -1):
            alpha = max(0, int((13 * scale - radius) * 16 * intensity))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, (h + 8) // 2 - radius,
                                 w + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow,
            _NS_raz._rgba((10, 5, 3), int(190 * intensity)),
            (5, (h + 8) // 2 - h // 2, w + 10, h))
        # Fire tint
        pygame.draw.ellipse(shadow,
            _NS_raz._rgba(_NS_raz.PALETTE["ember_dark"], int(100 * intensity)),
            (15, (h + 8) // 2 - h // 3, w, h // 2))
        surface.blit(shadow, (x - (w + 20) // 2, y - (h + 8) // 2))

    def _draw_fire_wisps(surface, cx, cy, phase, intensity=1.0, trail=False, facing=1):
        """Fire embers rising and swirling."""
        for i in range(int(12 * intensity)):
            t = (phase * 0.6 + i * 0.13) % 1.0
            offset_x = int(math.sin(phase * 0.8 + i) * 14)
            sx = cx + offset_x + (i - 6) * 3
            sy = cy - int(t * 45)
            alpha = _NS_raz._alpha(230 * (1 - t) * intensity)
            if alpha <= 0:
                continue
            # Fire ember colors (from dark to bright)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                (sx, sy), 3)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                (sx, sy - 1), 2)
            _NS_raz._aacircle(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                (sx, sy - 1), 1)
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_white"], alpha),
                (sx, sy - 2, 1, 1))

        # Swirling flame licks around
        for i in range(int(5 * intensity)):
            angle = phase * 1.5 + i * math.pi / 2.5
            radius = 24 + int(math.sin(phase + i) * 6)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy - 8 + int(math.sin(angle) * radius * 0.4)
            alpha = _NS_raz._alpha(240 * intensity)
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                (sx, sy, 3, 3))
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], alpha),
                (sx, sy, 1, 1))

        # Trail behind
        if trail:
            for i in range(7):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + 4 + int(math.sin(phase + i) * 2)
                alpha = _NS_raz._alpha(220 - i * 26)
                if alpha <= 0:
                    continue
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (sx, sy), max(1, 6 - i))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (sx, sy), max(1, 5 - i))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (sx, sy - 1, 2, 2))

    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -4):
            alpha = _NS_raz._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_raz._aacircle(aura,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (100, 90), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_raz._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_raz._aacircle(aura,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))

        # Floating embers
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            r = 36 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_raz.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_raz.PALETTE["fire_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], 200),
            (5, 15, 140, 24), 3)
        pygame.draw.ellipse(ring,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], 220),
            (14, 18, 122, 20), 2)
        pygame.draw.ellipse(ring,
            _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], 180),
            (30, 22, 90, 12), 1)

        # Rune spokes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 46)
            y1 = 27 + int(math.sin(angle) * 9)
            x2 = 75 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 13)
            pygame.draw.line(ring,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_light"], 220),
                (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"],
                               _NS_raz._alpha(160 * pulse)),
                (14, 11, 122, 32), 1)
        surface.blit(ring, (x - 75, y - 24))

    # ============================================================
    # SKILL Q: OVERDRIVE (fire projectile punch)
    # ============================================================
    def _draw_overdrive_fg(surface, boss, x, y, timer, phase):
        """Fire ball projectile from fist."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_raz._target_position(boss, x, y)

        if progress < 0.15:
            # Charge on fist
            t = progress / 0.15
            charge_x = x + facing * 22
            charge_y = y - 6
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_raz._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (charge_x, charge_y), r)
            for r in range(cr, 0, -1):
                alpha = _NS_raz._alpha(240 * (cr - r + 1) / cr)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (charge_x, charge_y), r)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_hot"],
                                (charge_x, charge_y), max(1, cr - 2))
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"],
                                (charge_x, charge_y), max(1, cr - 4))
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["white"],
                                (charge_x, charge_y), max(1, cr - 6))
        else:
            # Fire ball projectile
            t = (progress - 0.15) / 0.85
            start_x = x + facing * 25
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_raz._alpha(240 - i * 24)
                size = max(1, 9 - i)

                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (px, py), size)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (px, py), max(1, size - 1))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (px, py), max(1, size - 2))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (px, py), max(1, size - 3))

                # Sparks
                if i < 5:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                            _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], alpha),
                            (spark_x, spark_y, 1, 1))

            # Bright fire ball head
            for r in range(14, 3, -2):
                alpha = _NS_raz._alpha(120 * (14 - r) / 14)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (bx, by), r)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_darkest"], (bx, by), 10)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_dark"], (bx, by), 8)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_mid"], (bx, by), 6)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_light"], (bx, by), 4)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_hot"], (bx, by), 3)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"], (bx, by), 2)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["white"], (bx, by), 1)

            # Fire tail wisps around ball
            for i in range(6):
                tail_angle = phase * 4 + i * math.pi / 3
                tail_r = 10
                tx_off = int(math.cos(tail_angle) * tail_r)
                ty_off = int(math.sin(tail_angle) * tail_r)
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], 240),
                    (bx + tx_off, by + ty_off, 2, 2))
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], 240),
                    (bx + tx_off, by + ty_off, 1, 1))

            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(15 + st * 25)
                alpha = _NS_raz._alpha(240 * (1 - st))
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (tx, ty), radius + 4, 3)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (tx, ty), radius, 3)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (tx, ty), max(1, radius - 6), 2)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (tx, ty), max(1, radius - 12), 1)
                _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"],
                                    (tx, ty), max(1, radius // 4))
                _NS_raz._aacircle(surface, _NS_raz.PALETTE["white"],
                                    (tx, ty), 2)

                # Radial burst
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                        (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], alpha),
                        (ex, ey, 1, 1))

    # ============================================================
    # SKILL W: SEARING FIST (dash + punch)
    # ============================================================
    def _draw_searing_ground(surface, boss, x, y, timer, pulse):
        """Trail along dash path."""
        tx, ty = _NS_raz._target_position(boss, x, y)
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.75:
            # Landing burst at target
            t = (progress - 0.75) / 0.25
            end_x = int(x + (tx - x) * 0.9)
            end_y = int(y + (ty - y) * 0.9)
            r = int(35 * t)
            alpha = _NS_raz._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                (end_x - r, end_y + 42 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (end_x - r + 4, end_y + 42 - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6), 1)

    def _draw_searing_fg(surface, boss, x, y, timer, pulse):
        """Fire streak trail dari origin ke target."""
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_raz._target_position(boss, x, y)
        facing = boss.direction

        if progress < 0.75:
            t = progress / 0.75
            t_ease = 1 - (1 - t) ** 3

            end_x = int(x + (tx - x) * t_ease * 0.9)
            end_y = int(y + (ty - y) * t_ease * 0.9)

            # Fire streak line
            for thick, color, a_mult in [
                (14, _NS_raz.PALETTE["fire_darkest"], 0.4),
                (10, _NS_raz.PALETTE["fire_dark"], 0.6),
                (7, _NS_raz.PALETTE["fire_mid"], 0.8),
                (5, _NS_raz.PALETTE["fire_light"], 1.0),
                (3, _NS_raz.PALETTE["fire_hot"], 1.0),
                (2, _NS_raz.PALETTE["fire_shine"], 1.0),
                (1, _NS_raz.PALETTE["fire_white"], 1.0),
            ]:
                alpha = _NS_raz._alpha(240 * a_mult * (1 - t * 0.3))
                pygame.draw.line(surface,
                    _NS_raz._rgba(color, alpha),
                    (x + facing * 15, y - 6),
                    (end_x, end_y), thick)

            # Bright fireball at leading edge
            for r in range(12, 0, -1):
                alpha = _NS_raz._alpha(220 * (12 - r) / 12)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (end_x, end_y), r)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"],
                                (end_x, end_y), 5)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["white"],
                                (end_x, end_y), 2)

            # Sparks along trail
            for i in range(8):
                spark_t = (pulse * 3 + i * 0.15) % 1.0
                sp_x = int(x + (end_x - x) * spark_t)
                sp_y = int(y + (end_y - y) * spark_t)
                perp_off = math.sin(pulse * 5 + i) * 8
                dx = end_x - x
                dy = end_y - y
                dl = max(1, math.hypot(dx, dy))
                sp_x += int(-dy / dl * perp_off)
                sp_y += int(dx / dl * perp_off)
                pygame.draw.rect(surface, _NS_raz.PALETTE["fire_hot"], (sp_x, sp_y, 2, 2))
                pygame.draw.rect(surface, _NS_raz.PALETTE["fire_shine"], (sp_x, sp_y, 1, 1))

    # ============================================================
    # SKILL E: ENERGY SURGE (AoE around)
    # ============================================================
    def _draw_surge_ground(surface, boss, x, y, timer, pulse):
        """Ground rings expanding."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            r = int(30 + t * 60)
            alpha = _NS_raz._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                (x - r, y + 44 - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                (x - r + 4, y + 44 - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6), 3)
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                (x - r + 10, y + 44 - r // 3 + 6,
                 r * 2 - 20, r * 2 // 3 - 12), 2)
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (x - r + 18, y + 44 - r // 3 + 10,
                 r * 2 - 36, r * 2 // 3 - 20), 1)

    def _draw_surge_fg(surface, boss, x, y, timer, pulse):
        """Fire explosion outward + rising flames."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge - fire building around boss
            t = progress / 0.3
            # Bright glow at boss center growing
            for r in range(int(25 * t), 0, -2):
                alpha = _NS_raz._alpha(200 * (25 * t - r) / max(1, 25 * t) * t)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha),
                    (x, y - 4), r)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_hot"], (x, y - 4), int(8 * t))
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"], (x, y - 4), int(4 * t))

            # Fire tendrils forming around
            for i in range(8):
                angle = i * math.pi / 4 + pulse * 0.5
                tend_r = int(20 * t)
                tx = x + int(math.cos(angle) * tend_r)
                ty = y + int(math.sin(angle) * tend_r * 0.7) - 4
                alpha = _NS_raz._alpha(220 * t)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha), (tx, ty), 4)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], alpha), (tx, ty), 3)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha), (tx, ty), 1)
        else:
            # BURST - radial flames outward
            t = (progress - 0.3) / 0.7
            burst_r = int(t * 90)

            # Rising flame columns around
            num_columns = 12
            for i in range(num_columns):
                col_angle = i * math.pi * 2 / num_columns
                col_dist = int(burst_r * 0.7)
                col_x = x + int(math.cos(col_angle) * col_dist)
                col_y_base = y + int(math.sin(col_angle) * col_dist * 0.5)

                # Rising flame at each column
                for layer in range(5):
                    layer_t = (pulse * 0.7 + i * 0.15 + layer * 0.15) % 1.0
                    layer_y = col_y_base - int(layer_t * 30)
                    layer_alpha = _NS_raz._alpha(240 * (1 - layer_t) * (1 - t * 0.3))
                    layer_w = int(5 + layer_t * 3)
                    layer_h = int(4 + layer_t * 2)

                    pygame.draw.ellipse(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], layer_alpha),
                        (col_x - layer_w, layer_y - layer_h,
                         layer_w * 2, layer_h * 2))
                    pygame.draw.ellipse(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], layer_alpha),
                        (col_x - layer_w + 1, layer_y - layer_h + 1,
                         max(1, layer_w * 2 - 2), max(1, layer_h * 2 - 2)))
                    pygame.draw.ellipse(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_mid"], layer_alpha),
                        (col_x - layer_w + 2, layer_y - layer_h + 2,
                         max(1, layer_w * 2 - 4), max(1, layer_h * 2 - 4)))
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], layer_alpha),
                        (col_x, layer_y - 1, 1, 1))
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], layer_alpha),
                        (col_x, layer_y - 2, 1, 1))

            # Radial shockwave lines
            for i in range(14):
                angle = i * math.pi / 7
                inner_r = int(burst_r * 0.7)
                outer_r = burst_r
                p1 = (x + int(math.cos(angle) * inner_r),
                      y - 6 + int(math.sin(angle) * inner_r * 0.7))
                p2 = (x + int(math.cos(angle) * outer_r),
                      y - 6 + int(math.sin(angle) * outer_r * 0.7))
                alpha = _NS_raz._alpha(220 * (1 - t))
                pygame.draw.line(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_light"], alpha), p1, p2, 3)
                pygame.draw.line(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha), p1, p2, 1)

    # ============================================================
    # SKILL R: DEATH GLOOM (leap + meteor crash)
    # ============================================================
    def _draw_gloom_ground(surface, boss, x, y, timer, pulse):
        """Impact zone marker + shockwave rings."""
        tx, ty = _NS_raz._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.55 and progress < 0.75:
            # Warning marker before landing
            t = (progress - 0.55) / 0.20
            r = int(50 * (1 - t))
            alpha = _NS_raz._alpha(200 + int(math.sin(pulse * 8) * 40))
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                (tx - r, ty + 42 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], alpha),
                (tx - r + 3, ty + 42 - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4), 2)
        elif progress >= 0.75:
            # Massive shockwave rings
            t = (progress - 0.75) / 0.25
            for ring_i in range(3):
                ring_delay = ring_i * 0.1
                if t < ring_delay:
                    continue
                ring_t = (t - ring_delay) / (1 - ring_delay) if (1 - ring_delay) > 0 else 0
                r = int(30 + ring_t * 90)
                alpha = _NS_raz._alpha(240 * (1 - ring_t))
                pygame.draw.ellipse(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_darkest"], alpha),
                    (tx - r, ty + 42 - r // 3, r * 2, r * 2 // 3), 4)
                pygame.draw.ellipse(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_dark"], alpha),
                    (tx - r + 4, ty + 42 - r // 3 + 3,
                     r * 2 - 8, r * 2 // 3 - 6), 3)
                pygame.draw.ellipse(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (tx - r + 10, ty + 42 - r // 3 + 6,
                     r * 2 - 20, r * 2 // 3 - 12), 1)

    def _draw_gloom_fg(surface, boss, x, y, timer, pulse):
        """Meteor crash explosion + debris."""
        tx, ty = _NS_raz._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress >= 0.75:
            # EXPLOSION at landing point
            t = (progress - 0.75) / 0.25
            intensity = math.sin(t * math.pi)

            # Massive central flash
            flash_r = int(35 + t * 30)
            for r in range(flash_r, 0, -3):
                alpha = _NS_raz._alpha(240 * intensity * (flash_r - r + 3) / flash_r)
                _NS_raz._aacircle(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (tx, ty), r)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_shine"], (tx, ty), 12)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["fire_white"], (tx, ty), 6)
            _NS_raz._aacircle(surface, _NS_raz.PALETTE["white"], (tx, ty), 3)

            # Radial fire pillars shooting outward
            num_pillars = 16
            for i in range(num_pillars):
                angle = i * math.pi * 2 / num_pillars
                pillar_len = int(60 + t * 30)
                end_x = tx + int(math.cos(angle) * pillar_len)
                end_y = ty + int(math.sin(angle) * pillar_len * 0.7)
                alpha = _NS_raz._alpha(240 * intensity)
                for thick, color, a_mult in [
                    (8, _NS_raz.PALETTE["fire_darkest"], 0.5),
                    (6, _NS_raz.PALETTE["fire_dark"], 0.7),
                    (4, _NS_raz.PALETTE["fire_mid"], 0.9),
                    (3, _NS_raz.PALETTE["fire_hot"], 1.0),
                    (2, _NS_raz.PALETTE["fire_shine"], 1.0),
                    (1, _NS_raz.PALETTE["white"], 1.0),
                ]:
                    line_a = _NS_raz._alpha(alpha * a_mult)
                    pygame.draw.line(surface,
                        _NS_raz._rgba(color, line_a),
                        (tx, ty), (end_x, end_y), thick)
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                    (end_x, end_y, 3, 3))
                pygame.draw.rect(surface,
                    _NS_raz._rgba(_NS_raz.PALETTE["fire_shine"], alpha),
                    (end_x, end_y, 1, 1))

            # Debris/rocks flying up
            for i in range(20):
                deb_t = (pulse * 0.6 + i * 0.08) % 1.0
                deb_angle = i * math.pi * 2 / 20
                deb_r = int(20 + deb_t * 50)
                deb_x = tx + int(math.cos(deb_angle) * deb_r)
                deb_y = ty + int(math.sin(deb_angle) * deb_r * 0.5) - int(deb_t * 30)
                alpha = _NS_raz._alpha(220 * (1 - deb_t) * intensity)
                if alpha > 0:
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["cloth_darkest"], alpha),
                        (deb_x - 1, deb_y - 1, 3, 3))
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["ember_mid"], alpha),
                        (deb_x, deb_y, 2, 2))
                    pygame.draw.rect(surface,
                        _NS_raz._rgba(_NS_raz.PALETTE["fire_hot"], alpha),
                        (deb_x, deb_y, 1, 1))


# ====================================================================
# vraskhan.py
# ====================================================================

# ====================================================================
# VRASKHAN - THE VOIDBLADE
# Mini-boss: Shadow assassin dengan dual curved blades
# ====================================================================


class _NS_vraskhan:
    """Namespace vraskhan - shadow assassin bertema void purple."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Dark armor (deep purple-black)
        "armor_darkest": (8, 5, 15),
        "armor_dark": (25, 18, 40),
        "armor_mid": (55, 40, 80),
        "armor_light": (100, 80, 140),
        "armor_edge": (160, 140, 200),
        "armor_shine": (220, 210, 245),

        # Purple void (main accent - blades, aura)
        "void_darkest": (20, 5, 35),
        "void_dark": (60, 20, 100),
        "void_mid": (130, 50, 200),
        "void_light": (190, 120, 245),
        "void_hot": (225, 170, 255),
        "void_shine": (250, 230, 255),

        # Cloth/cape (dark violet)
        "cloth_dark": (18, 10, 30),
        "cloth_mid": (45, 25, 70),
        "cloth_light": (85, 55, 120),

        # Blade metal (dark steel with purple sheen)
        "blade_dark": (15, 15, 30),
        "blade_mid": (75, 65, 105),
        "blade_light": (180, 170, 220),
        "blade_shine": (240, 235, 255),
        "blade_edge": (200, 100, 255),

        # Eye (bright cyan-violet)
        "eye_socket": (5, 2, 10),
        "eye_dark": (60, 20, 120),
        "eye_mid": (180, 80, 255),
        "eye_hot": (230, 180, 255),
        "eye_shine": (255, 240, 255),

        # Shadow tendrils
        "shadow_darkest": (10, 5, 20),
        "shadow_dark": (30, 15, 55),
        "shadow_mid": (70, 40, 110),

        # Blood (dark crimson for finishers)
        "blood_dark": (60, 10, 15),
        "blood_mid": (140, 25, 40),
        "blood_light": (220, 60, 80),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vraskhan._clamp(color)
        if _NS_vraskhan.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_vraskhan._clamp(color)
        if _NS_vraskhan.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vraskhan._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vraskhan(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vraskhan._detect_moving(boss)
        _NS_vraskhan._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_vrk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_vraskhan._draw_void_aura(surface, x, y, pulse)
        _NS_vraskhan._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_vraskhan._draw_thorned_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vraskhan._draw_deathslash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vraskhan._draw_omni_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if active_skill == "w":
            _NS_vraskhan._draw_shadowleap_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_vraskhan._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_vraskhan._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_vraskhan._draw_idle_pose(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_vraskhan._draw_thorned_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vraskhan._draw_shadowleap_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vraskhan._draw_deathslash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vraskhan._draw_omni_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vrk_previous_timer", 0))
        active = bool(getattr(boss, "_vrk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vrk_attack_active = True
            boss._vrk_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._vrk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._vrk_attack_frame = int(getattr(boss, "_vrk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vrk_attack_active = False
            boss._vrk_attack_frame = 0
            active = False

        boss._vrk_previous_timer = timer
        boss._vrk_attack_progress = (
            min(1.0, getattr(boss, "_vrk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_vrk_last_x"):
            boss._vrk_last_x = boss.x
            boss._vrk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vrk_last_x)
        dy = abs(boss.y - boss._vrk_last_y)
        boss._vrk_last_x = boss.x
        boss._vrk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        float_y = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_vraskhan._draw_shadow(surface, x, y + 52)
        _NS_vraskhan._draw_shadow_dust(surface, x, y + 48, boss.pulse)
        _NS_vraskhan._draw_body(surface, x, y - 6 + float_y,
                                 boss.direction, boss.pulse, "idle")

    def _draw_walk_pose(surface, boss, x, y):
        phase = boss.pulse * 2.0
        float_y = int(math.sin(phase * 0.9) * 7)
        sway = int(math.sin(phase * 0.6) * 2)
        _NS_vraskhan._draw_shadow(surface, x + sway, y + 52)
        _NS_vraskhan._draw_shadow_dust(surface, x + sway, y + 48, phase,
                                        trail=True, facing=boss.direction)
        _NS_vraskhan._draw_body(surface, x + sway, y - 6 + float_y,
                                 boss.direction, phase, "walk")

    def _draw_attack_pose(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_vrk_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_vrk_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Assassin lunge with blade swing.
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 5) * facing
            lift = int(t * 5)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-5 + t * 20)) * facing
            lift = int(5 - t * 8)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(15 * (1 - t)) * facing
            lift = int(-3 + t * 3)

        float_y = int(math.sin(boss.pulse * 0.6) * 3)

        _NS_vraskhan._draw_shadow(surface, x + lunge, y + 52)
        _NS_vraskhan._draw_shadow_dust(surface, x + lunge, y + 48, boss.pulse, intense=True)
        _NS_vraskhan._draw_body(surface, x + lunge, y - 6 - lift + float_y,
                                 facing, boss.pulse, "attack", progress)

        # Swing arc.
        _NS_vraskhan._draw_swing_arc(surface, x + lunge, y - 6 - lift + float_y,
                                      facing, progress)

    # ============================================================
    # BODY - Assassin layout
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Assassin: legs (feet floating), cape, torso, arms with blades, hooded head."""
        # Cape/cloak flowing behind.
        _NS_vraskhan._draw_cape(surface, cx, cy, facing, phase, action)

        # Back shadow tendrils.
        _NS_vraskhan._draw_shadow_tendrils(surface, cx, cy - 8, facing, phase, action)

        # Legs (floating, slightly bent).
        _NS_vraskhan._draw_legs(surface, cx, cy + 22, facing, phase, action)

        # Torso (slim, armored).
        _NS_vraskhan._draw_torso(surface, cx, cy + 4, facing, phase)

        # Arms with dual blades.
        _NS_vraskhan._draw_arms_with_blades(surface, cx, cy + 2, facing, phase,
                                             action, attack_progress)

        # Hooded head with horns.
        _NS_vraskhan._draw_hooded_head(surface, cx, cy - 16, facing, phase, action)

    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Flowing dark cape behind."""
        flutter = math.sin(phase * 1.5) * 3
        if action == "walk":
            flutter = math.sin(phase * 1.8) * 5
        elif action == "attack":
            flutter = math.sin(phase * 3) * 6

        back_dir = -facing
        base_x = cx + back_dir * 8
        base_y = cy - 8

        # Cape shape (large trailing).
        cape_shape = [
            (base_x - facing * 2, base_y - 4),
            (base_x + back_dir * 6, base_y - 2 + int(flutter * 0.3)),
            (base_x + back_dir * 12, base_y + 6 + int(flutter * 0.5)),
            (base_x + back_dir * 16, base_y + 16 + int(flutter)),
            (base_x + back_dir * 14, base_y + 26 + int(flutter * 0.7)),
            (base_x + back_dir * 8, base_y + 30),
            (base_x, base_y + 24),
            (base_x, base_y + 4),
        ]
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in cape_shape])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["cloth_dark"], cape_shape)
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["cloth_mid"], [
            (base_x - facing * 1, base_y - 3),
            (base_x + back_dir * 5, base_y - 1 + int(flutter * 0.3)),
            (base_x + back_dir * 10, base_y + 6 + int(flutter * 0.5)),
            (base_x + back_dir * 13, base_y + 15 + int(flutter)),
            (base_x + back_dir * 11, base_y + 24 + int(flutter * 0.7)),
            (base_x + back_dir * 6, base_y + 27),
            (base_x, base_y + 22),
            (base_x, base_y + 4),
        ])
        # Inner highlight.
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["cloth_light"], [
            (base_x - facing, base_y - 2),
            (base_x + back_dir * 3, base_y),
            (base_x + back_dir * 5, base_y + 10),
            (base_x + back_dir * 4, base_y + 18),
            (base_x, base_y + 20),
            (base_x, base_y + 4),
        ])

        # Cape edge tatters (jagged).
        for i, edge_off in enumerate([(6, 4), (10, 12), (12, 20), (8, 28)]):
            ex_off, ey_off = edge_off
            ex = base_x + back_dir * ex_off
            ey = base_y + ey_off + int(flutter * (0.3 + i * 0.15))
            pygame.draw.line(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                             (ex, ey), (ex + back_dir * 3, ey + 2), 1)

    def _draw_shadow_tendrils(surface, cx, cy, facing, phase, action):
        """Shadow whips/tendrils writhing from back."""
        intensity = 1.5 if action == "attack" else 1.0
        num_tendrils = 5

        for i in range(num_tendrils):
            base_angle = math.pi * 0.5 + (i - num_tendrils // 2) * 0.35
            wave = math.sin(phase * 1.5 + i * 0.7) * 0.3
            angle = base_angle + wave

            base_x = cx - facing * 4
            base_y = cy + i - num_tendrils // 2

            # Draw as curved segments.
            length = int(20 + intensity * 8 + math.sin(phase + i) * 4)
            segments = 6
            prev = (base_x, base_y)
            for seg in range(1, segments + 1):
                t = seg / segments
                # Curved path.
                seg_angle = angle + math.sin(phase * 2 + i + t * 3) * 0.4 * t
                seg_len = length * t
                nx = base_x + int(math.cos(seg_angle) * seg_len) * (-facing)
                ny = base_y - int(math.sin(seg_angle) * seg_len)

                thickness = max(1, 4 - seg // 2)
                alpha = _NS_vraskhan._alpha(220 - seg * 25)

                # Shadow tendril body.
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["shadow_darkest"],
                                      prev, (nx, ny), thickness + 1)
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["shadow_dark"],
                                      prev, (nx, ny), thickness)
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["void_dark"],
                                      prev, (nx, ny), max(1, thickness - 1))

                # Occasional void sparkle.
                if seg % 2 == 0:
                    pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_light"],
                                     (nx, ny, 1, 1))
                prev = (nx, ny)

            # Tip glow.
            for r in range(3, 0, -1):
                alpha = _NS_vraskhan._alpha(150 * (3 - r) / 3)
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                        prev, r)
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"],
                             (prev[0], prev[1], 1, 1))

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Slim armored legs (floating, slight dangle)."""
        dangle = math.sin(phase * 0.9) * 1

        for side_i, off_x in enumerate((-5, 5)):
            lx = cx + off_x
            ly = cy + int(dangle) + side_i

            # Thigh (upper leg).
            _NS_vraskhan._draw_leg_segment(surface, (lx, ly - 8), (lx + off_x // 3, ly - 2), 4)
            # Shin.
            _NS_vraskhan._draw_leg_segment(surface, (lx + off_x // 3, ly - 2),
                                            (lx + off_x // 2, ly + 6), 3)

            # Boot with sharp toe.
            boot_x = lx + off_x // 2
            boot_y = ly + 6
            boot_shape = [
                (boot_x - 3, boot_y - 1),
                (boot_x + 3, boot_y - 1),
                (boot_x + 4 + facing, boot_y + 2),
                (boot_x + 6 * facing, boot_y + 4),
                (boot_x - 2, boot_y + 4),
            ]
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in boot_shape])
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_darkest"], boot_shape)
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_dark"], [
                (boot_x - 2, boot_y - 1),
                (boot_x + 2, boot_y - 1),
                (boot_x + 3 + facing, boot_y + 2),
                (boot_x + 5 * facing, boot_y + 3),
                (boot_x - 1, boot_y + 3),
            ])
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["armor_mid"],
                             (boot_x - 1, boot_y, 3, 1))

            # Small void glow on knee.
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_dark"],
                             (lx + off_x // 3 - 1, ly - 2, 2, 2))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_mid"],
                             (lx + off_x // 3, ly - 2, 1, 1))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"],
                             (lx + off_x // 3, ly - 2, 1, 1))

    def _draw_leg_segment(surface, start, end, thickness):
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                              (start[0] + 1, start[1] + 1),
                              (end[0] + 1, end[1] + 1), thickness + 1)
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_darkest"],
                              start, end, thickness)
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_dark"],
                              start, end, max(1, thickness - 1))
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_mid"],
                              (start[0], start[1] - 1), (end[0], end[1] - 1),
                              max(1, thickness - 2))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Slim armored torso with spikes and center gem."""
        breath = math.sin(phase * 0.5) * 1

        # Main torso shape (V-shape assassin).
        torso_shape = [
            (cx - 12, cy - 12),
            (cx - 14, cy - 8),
            (cx - 13, cy - 2),
            (cx - 10, cy + 6),
            (cx - 6, cy + 14),
            (cx - 3, cy + 18),
            (cx + 3, cy + 18),
            (cx + 6, cy + 14),
            (cx + 10, cy + 6),
            (cx + 13, cy - 2),
            (cx + 14, cy - 8),
            (cx + 12, cy - 12),
            (cx + 6, cy - 14),
            (cx - 6, cy - 14),
        ]
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in torso_shape])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_darkest"], torso_shape)

        # Mid armor layer.
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_dark"], [
            (cx - 10, cy - 11), (cx - 12, cy - 7), (cx - 11, cy - 2),
            (cx - 8, cy + 5), (cx - 4, cy + 12), (cx - 2, cy + 16),
            (cx + 2, cy + 16), (cx + 4, cy + 12), (cx + 8, cy + 5),
            (cx + 11, cy - 2), (cx + 12, cy - 7), (cx + 10, cy - 11),
            (cx + 4, cy - 13), (cx - 4, cy - 13),
        ])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_mid"], [
            (cx - 8, cy - 9), (cx - 10, cy - 5), (cx - 8, cy + 2),
            (cx - 5, cy + 9), (cx - 1, cy + 14), (cx + 1, cy + 14),
            (cx + 5, cy + 9), (cx + 8, cy + 2), (cx + 10, cy - 5),
            (cx + 8, cy - 9), (cx + 3, cy - 11), (cx - 3, cy - 11),
        ])

        # Chest highlight (V-plate).
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_light"], [
            (cx - 5, cy - 6), (cx - 6, cy - 1), (cx - 3, cy + 6),
            (cx, cy + 10), (cx + 3, cy + 6), (cx + 6, cy - 1),
            (cx + 5, cy - 6),
        ])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_edge"], [
            (cx - 3, cy - 4), (cx - 4, cy - 1), (cx - 2, cy + 3),
            (cx, cy + 6), (cx + 2, cy + 3), (cx + 4, cy - 1),
            (cx + 3, cy - 4),
        ])

        # Center void gem.
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        gem_x, gem_y = cx, cy - 1

        pygame.draw.rect(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                         (gem_x - 2, gem_y - 3, 4, 6))
        pygame.draw.rect(surface, _NS_vraskhan.PALETTE["armor_darkest"],
                         (gem_x - 2, gem_y - 3, 4, 6))

        # Glow halo.
        for r in range(7, 1, -1):
            alpha = _NS_vraskhan._alpha(120 * (7 - r) / 7 * gem_pulse)
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                    (gem_x, gem_y), r)

        # Diamond gem.
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["void_darkest"], [
            (gem_x, gem_y - 4), (gem_x + 2, gem_y),
            (gem_x, gem_y + 4), (gem_x - 2, gem_y),
        ])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["void_dark"], [
            (gem_x, gem_y - 3), (gem_x + 2, gem_y),
            (gem_x, gem_y + 3), (gem_x - 2, gem_y),
        ])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["void_mid"], [
            (gem_x, gem_y - 2), (gem_x + 1, gem_y),
            (gem_x, gem_y + 2), (gem_x - 1, gem_y),
        ])
        pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"],
                         (gem_x, gem_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_shine"],
                         (gem_x, gem_y - 1, 1, 1))

        # Shoulder spikes (curved).
        for side in (-1, 1):
            sx_shoulder = cx + side * 13
            sy_shoulder = cy - 10
            # Spike shape.
            spike_shape = [
                (sx_shoulder - 3 * side, sy_shoulder + 2),
                (sx_shoulder + 2 * side, sy_shoulder - 8),
                (sx_shoulder + 5 * side, sy_shoulder - 6),
                (sx_shoulder + side, sy_shoulder + 3),
            ]
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in spike_shape])
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_darkest"], spike_shape)
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_dark"], [
                (sx_shoulder - 2 * side, sy_shoulder + 1),
                (sx_shoulder + 2 * side, sy_shoulder - 7),
                (sx_shoulder + 4 * side, sy_shoulder - 5),
                (sx_shoulder, sy_shoulder + 2),
            ])
            _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_mid"], [
                (sx_shoulder, sy_shoulder + 1),
                (sx_shoulder + 2 * side, sy_shoulder - 5),
                (sx_shoulder + 3 * side, sy_shoulder - 4),
            ])
            # Bright spike tip.
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_light"],
                             (sx_shoulder + 2 * side, sy_shoulder - 8, 1, 1))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"],
                             (sx_shoulder + 2 * side, sy_shoulder - 8, 1, 1))

        # Belt line.
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                         (cx - 8, cy + 10), (cx + 8, cy + 10), 1)
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["armor_edge"],
                         (cx - 8, cy + 11), (cx + 8, cy + 11), 1)

    def _draw_arms_with_blades(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms holding curved scythe blades."""
        idle_sway = math.sin(phase * 0.6) * 3

        for side_i, side_x in enumerate((-1, 1)):
            shoulder_x = cx + side_x * 13
            shoulder_y = cy - 4

            # Arm angle depending on action.
            if action == "attack":
                # Front blade slashes across.
                if side_x == facing:
                    if attack_progress < 0.3:
                        # Wind-up (back and up).
                        t = attack_progress / 0.3
                        arm_angle_deg = -60 - t * 30
                        blade_angle_deg = -100 - t * 40
                    elif attack_progress < 0.55:
                        # SLASH forward-down.
                        t = (attack_progress - 0.3) / 0.25
                        arm_angle_deg = -90 + t * 150
                        blade_angle_deg = -140 + t * 200
                    else:
                        # Recovery.
                        t = (attack_progress - 0.55) / 0.45
                        arm_angle_deg = 60 - t * 50
                        blade_angle_deg = 60 - t * 40
                else:
                    # Back arm holds back, ready.
                    arm_angle_deg = 30 + idle_sway
                    blade_angle_deg = 60
            elif action == "walk":
                arm_angle_deg = math.sin(phase * 1.2 + side_i * math.pi) * 10 + 20
                blade_angle_deg = arm_angle_deg + 40
            else:
                arm_angle_deg = 25 + idle_sway * side_x
                blade_angle_deg = arm_angle_deg + 30

            arm_angle = math.radians(90 + arm_angle_deg * side_x)
            blade_angle = math.radians(90 + blade_angle_deg * side_x)

            # Upper arm.
            upper_len = 10
            elbow_x = shoulder_x + int(math.cos(arm_angle) * upper_len) * side_x
            elbow_y = shoulder_y + int(math.sin(arm_angle) * upper_len)

            # Forearm.
            forearm_angle = arm_angle + math.radians(15 * side_x)
            forearm_len = 9
            hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * side_x
            hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len)

            # Draw arm segments.
            _NS_vraskhan._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                            (elbow_x, elbow_y), 4)
            _NS_vraskhan._draw_arm_segment(surface, (elbow_x, elbow_y),
                                            (hand_x, hand_y), 3)

            # Draw curved scythe blade.
            is_active = (action == "attack" and side_x == facing
                          and 0.3 <= attack_progress < 0.55)
            _NS_vraskhan._draw_curved_blade(surface, hand_x, hand_y, blade_angle,
                                             side_x, phase, is_active)

    def _draw_arm_segment(surface, start, end, thickness):
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                              (start[0] + 1, start[1] + 1),
                              (end[0] + 1, end[1] + 1), thickness + 2)
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_darkest"],
                              start, end, thickness + 1)
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_dark"],
                              start, end, thickness)
        _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_mid"],
                              (start[0], start[1] - 1), (end[0], end[1] - 1),
                              max(1, thickness - 2))

    def _draw_curved_blade(surface, hand_x, hand_y, angle, side, phase, is_active):
        """Long curved scythe-like blade."""
        blade_length = 22
        glow_mult = 1.3 if is_active else 1.0

        # Calculate blade curve points.
        # Handle grip.
        grip_end_x = hand_x + int(math.cos(angle) * 5) * side
        grip_end_y = hand_y + int(math.sin(angle) * 5)

        # Blade base.
        blade_base_x = grip_end_x
        blade_base_y = grip_end_y

        # Curved blade tip.
        # Multiple segments for smooth curve.
        num_segments = 8
        blade_points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            # Curve outward (perpendicular to angle).
            curve_angle = angle + math.radians(50 * side * t)  # curves outward
            seg_len = blade_length * t
            bx = blade_base_x + int(math.cos(curve_angle) * seg_len) * side
            by = blade_base_y + int(math.sin(curve_angle) * seg_len)
            blade_points.append((bx, by))

        # Draw handle first.
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1),
                         (grip_end_x + 1, grip_end_y + 1), 4)
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["armor_darkest"],
                         (hand_x, hand_y), (grip_end_x, grip_end_y), 3)
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["armor_dark"],
                         (hand_x, hand_y), (grip_end_x, grip_end_y), 2)
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["armor_mid"],
                         (hand_x, hand_y - 1), (grip_end_x, grip_end_y - 1), 1)

        # Blade body (curved).
        for i in range(len(blade_points) - 1):
            thickness = max(1, 5 - i // 2)
            # Shadow.
            _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                                  (blade_points[i][0] + 1, blade_points[i][1] + 1),
                                  (blade_points[i + 1][0] + 1, blade_points[i + 1][1] + 1),
                                  thickness + 1)
            # Blade dark base.
            _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["blade_dark"],
                                  blade_points[i], blade_points[i + 1], thickness)
            # Blade mid.
            _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["blade_mid"],
                                  blade_points[i], blade_points[i + 1],
                                  max(1, thickness - 1))
            # Blade highlight (bright edge).
            _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["blade_light"],
                                  (blade_points[i][0], blade_points[i][1] - 1),
                                  (blade_points[i + 1][0], blade_points[i + 1][1] - 1),
                                  1)

        # GLOWING PURPLE EDGE along blade (void-infused).
        edge_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(len(blade_points) - 1):
            edge_color = _NS_vraskhan._clamp((
                _NS_vraskhan.PALETTE["blade_edge"][0] * edge_pulse * glow_mult,
                _NS_vraskhan.PALETTE["blade_edge"][1] * edge_pulse * glow_mult,
                _NS_vraskhan.PALETTE["blade_edge"][2] * edge_pulse * glow_mult,
            ))
            # Draw glow lines offset from blade.
            offset_side = side
            _NS_vraskhan._aaline(surface, edge_color,
                                  (blade_points[i][0] + offset_side,
                                   blade_points[i][1] + 1),
                                  (blade_points[i + 1][0] + offset_side,
                                   blade_points[i + 1][1] + 1), 1)

        # Blade tip (sharp point).
        tip = blade_points[-1]
        _NS_vraskhan._aacircle(surface, _NS_vraskhan.PALETTE["blade_shine"], tip, 2)
        pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"],
                         (tip[0], tip[1], 1, 1))
        pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_shine"],
                         (tip[0], tip[1], 1, 1))

        # Halo at tip.
        for r in range(4, 0, -1):
            alpha = _NS_vraskhan._alpha(140 * (4 - r) / 4 * glow_mult)
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                    tip, r)

        # Extra void trail during active swing.
        if is_active:
            for i, tp in enumerate(blade_points):
                for r in range(3, 0, -1):
                    alpha = _NS_vraskhan._alpha(180 * (3 - r) / 3)
                    _NS_vraskhan._aacircle(surface,
                                            (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                                            tp, r)

    def _draw_hooded_head(surface, cx, cy, facing, phase, action):
        """Hooded head with two curved horns."""
        # Hood (large flowing).
        hood_shape = [
            (cx - 10, cy + 4),
            (cx - 12, cy),
            (cx - 11, cy - 6),
            (cx - 6, cy - 12),
            (cx + 6, cy - 12),
            (cx + 11, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 4),
            (cx + 6, cy + 6),
            (cx - 6, cy + 6),
        ]
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in hood_shape])
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["cloth_dark"], hood_shape)
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["cloth_mid"], [
            (cx - 9, cy + 3), (cx - 11, cy - 1), (cx - 10, cy - 5),
            (cx - 5, cy - 11), (cx + 5, cy - 11), (cx + 10, cy - 5),
            (cx + 11, cy - 1), (cx + 9, cy + 3), (cx + 5, cy + 5),
            (cx - 5, cy + 5),
        ])

        # Face shadow (dark inside hood).
        face_shape = [
            (cx - 6, cy - 4),
            (cx - 7, cy),
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 7, cy),
            (cx + 6, cy - 4),
        ]
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["shadow_deep"], face_shape)
        _NS_vraskhan._poly(surface, _NS_vraskhan.PALETTE["armor_darkest"], [
            (cx - 5, cy - 3), (cx - 6, cy), (cx - 4, cy + 3),
            (cx + 4, cy + 3), (cx + 6, cy), (cx + 5, cy - 3),
        ])

        # GLOWING EYES inside hood.
        _NS_vraskhan._draw_hood_eyes(surface, cx, cy - 1, facing, phase)

        # Mouth mask/breather (jagged).
        if action == "attack":
            # Snarl.
            pygame.draw.line(surface, _NS_vraskhan.PALETTE["void_mid"],
                             (cx - 3, cy + 3), (cx + 3, cy + 3), 2)
            pygame.draw.line(surface, _NS_vraskhan.PALETTE["void_hot"],
                             (cx - 2, cy + 3), (cx + 2, cy + 3), 1)

        # HORNS (two large curved horns).
        _NS_vraskhan._draw_horns(surface, cx, cy - 8, facing, phase)

        # Hood trim (bright edge on top).
        pygame.draw.line(surface, _NS_vraskhan.PALETTE["cloth_light"],
                         (cx - 5, cy - 11), (cx + 5, cy - 11), 1)

    def _draw_horns(surface, cx, cy, facing, phase):
        """Two large curved horns sweeping back."""
        for side in (-1, 1):
            sway = math.sin(phase * 0.4 + side) * 1

            base_x = cx + side * 4
            base_y = cy - 1

            # Horn curves back and up.
            num_segments = 5
            prev = (base_x, base_y)
            for i in range(1, num_segments + 1):
                t = i / num_segments
                # Curve outward and back.
                curve_angle = math.pi * 0.7 + t * math.pi * 0.15
                seg_len = 4 + t * 3
                dx = int(math.cos(curve_angle) * seg_len) * side
                dy = -int(math.sin(curve_angle) * seg_len)
                nx = base_x + int(sum(math.cos(math.pi * 0.7 + j / num_segments * math.pi * 0.15) * (4 + (j / num_segments) * 3) for j in range(1, i + 1))) * side
                ny = base_y - int(sum(math.sin(math.pi * 0.7 + j / num_segments * math.pi * 0.15) * (4 + (j / num_segments) * 3) for j in range(1, i + 1)))
                ny += int(sway * t)

                thickness = max(1, 5 - i)
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                                      (prev[0] + 1, prev[1] + 1),
                                      (nx + 1, ny + 1), thickness + 1)
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_darkest"],
                                      prev, (nx, ny), thickness)
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_dark"],
                                      prev, (nx, ny), max(1, thickness - 1))
                _NS_vraskhan._aaline(surface, _NS_vraskhan.PALETTE["armor_mid"],
                                      (prev[0], prev[1] - 1), (nx, ny - 1),
                                      max(1, thickness - 2))

                prev = (nx, ny)

            # Sharp tip glow.
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["armor_edge"],
                             (prev[0], prev[1], 1, 1))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_light"],
                             (prev[0], prev[1], 1, 1))
            for r in range(3, 0, -1):
                alpha = _NS_vraskhan._alpha(100 * (3 - r) / 3)
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                        prev, r)

    def _draw_hood_eyes(surface, cx, cy, facing, phase):
        """Two glowing purple eye slits inside hood."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        for eye_x_off in (-3, 3):
            ex = cx + eye_x_off
            ey = cy

            # Deep socket.
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["shadow_deep"],
                             (ex - 2, ey - 1, 4, 2))

            # Glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_vraskhan._alpha(140 * (4 - r) / 4 * pulse)
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                        (ex, ey), r)

            # Eye slit.
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["eye_dark"],
                             (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["eye_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["eye_hot"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["eye_shine"],
                             (ex, ey, 1, 1))

    def _draw_swing_arc(surface, cx, cy, facing, progress):
        """Blade slash arc trail during attack."""
        if progress < 0.3 or progress > 0.6:
            return
        t = (progress - 0.3) / 0.3

        # Arc from top-back to front-down.
        num_arc = 12
        arc_points = []
        for i in range(num_arc):
            a_t = i / (num_arc - 1)
            # Angle sweeps.
            angle = math.pi * (0.75 - a_t * 1.1)  # -pi/4 to pi
            r = 26
            ax = cx + int(math.cos(angle) * r) * facing
            ay = cy - int(math.sin(angle) * r) + 4
            arc_points.append((ax, ay))

        # Only draw part of arc based on t (progress reveals arc).
        visible_count = int(len(arc_points) * min(1.0, t * 1.5))

        for i in range(max(1, visible_count) - 1):
            fade = (i / max(1, visible_count))
            alpha = _NS_vraskhan._alpha(240 * (1 - abs(fade - 0.5) * 1.5))
            # Multi-layer glow.
            _NS_vraskhan._aaline(surface, (*_NS_vraskhan.PALETTE["void_darkest"], alpha),
                                  arc_points[i], arc_points[i + 1], 5)
            _NS_vraskhan._aaline(surface, (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                  arc_points[i], arc_points[i + 1], 3)
            _NS_vraskhan._aaline(surface, (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                  arc_points[i], arc_points[i + 1], 2)
            _NS_vraskhan._aaline(surface, (*_NS_vraskhan.PALETTE["void_light"], alpha),
                                  arc_points[i], arc_points[i + 1], 1)
            # Bright center line.
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                             (arc_points[i][0], arc_points[i][1], 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow_dust(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Shadow smoke floating below assassin."""
        strength = 1.5 if intense else 1.0

        # Base shadow cloud.
        dust = pygame.Surface((140, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_vraskhan._alpha((30 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    dust, (*_NS_vraskhan.PALETTE["shadow_dark"], alpha),
                    (70 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_vraskhan._alpha((18 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    dust, (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                    (70 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(dust, (cx - 70, cy - 10))

        # Rising violet motes.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, -32, 30)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 24)
            alpha = _NS_vraskhan._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                             (sx, sy - 1, 1, 1))

        # Trail behind while moving.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vraskhan._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["shadow_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                 (sx, sy - 1, 2, 2))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 10, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (40, 15, 60, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_void_aura(surface, x, y, phase):
        """Purple void aura around body."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_vraskhan._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vraskhan._aacircle(aura,
                                        (*_NS_vraskhan.PALETTE["shadow_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_vraskhan._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vraskhan._aacircle(aura,
                                        (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_vraskhan._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vraskhan._aacircle(aura,
                                        (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Floating void motes.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_dark"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vraskhan.PALETTE["shadow_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_vraskhan.PALETTE["void_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_vraskhan.PALETTE["void_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_vraskhan.PALETTE["shadow_darkest"], 180),
                            (40, 24, 90, 14), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vraskhan.PALETTE["void_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_vraskhan.PALETTE["void_hot"],
                                        _NS_vraskhan._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q — THORNED ASSAULT (dash forward with blade line)
    # ============================================================
    def _draw_thorned_ground(surface, boss, x, y, timer, phase):
        """Dash path marker on ground."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Dash line from boss to some distance forward.
        dash_len = 140
        start_x = x
        start_y = y + 42

        # Draw dash trail on ground.
        for i in range(int(dash_len / 8)):
            t = i * 8 / dash_len
            px = start_x + int(facing * dash_len * t * progress)
            py = start_y
            alpha = _NS_vraskhan._alpha(180 * (1 - t) * progress)
            pygame.draw.ellipse(surface, (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                (px - 6, py - 2, 12, 4))
            pygame.draw.ellipse(surface, (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                (px - 4, py - 1, 8, 3))
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                             (px, py, 1, 1))

    def _draw_thorned_foreground(surface, boss, x, y, timer, phase):
        """Blade slash arc + thorn marks."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up: charging energy on blade.
            t = progress / 0.3
            hand_x = x + facing * 20
            hand_y = y - 8
            for r in range(int(6 + t * 4), 0, -1):
                alpha = _NS_vraskhan._alpha(180 * t)
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                        (hand_x, hand_y), r)
        elif progress < 0.7:
            # DASH: large arc slash across.
            t = (progress - 0.3) / 0.4
            # Multi-arc slash trail.
            dash_dist = int(t * 100)
            slash_center_x = x + facing * (20 + dash_dist)
            slash_center_y = y - 5

            # Big curved slash arc.
            num_pts = 16
            for k in range(3):  # 3 arc layers
                layer_offset = k * 3
                arc_pts = []
                for i in range(num_pts):
                    a_t = i / (num_pts - 1)
                    angle = math.pi * (0.85 - a_t * 1.3)
                    r = 30 + layer_offset
                    ax = slash_center_x + int(math.cos(angle) * r) * facing
                    ay = slash_center_y - int(math.sin(angle) * r) + 5
                    arc_pts.append((ax, ay))

                intensity = math.sin(t * math.pi)
                for i in range(len(arc_pts) - 1):
                    alpha = _NS_vraskhan._alpha(230 * intensity * (1 - k * 0.2))
                    thickness = max(1, 4 - k)
                    color = [_NS_vraskhan.PALETTE["void_light"],
                             _NS_vraskhan.PALETTE["void_mid"],
                             _NS_vraskhan.PALETTE["void_dark"]][k]
                    _NS_vraskhan._aaline(surface, (*color, alpha),
                                          arc_pts[i], arc_pts[i + 1], thickness)
                if k == 0:
                    for pt in arc_pts:
                        pygame.draw.rect(surface,
                                         (*_NS_vraskhan.PALETTE["void_hot"], _NS_vraskhan._alpha(240 * intensity)),
                                         (pt[0], pt[1], 1, 1))

            # Thorn spikes rising from ground along dash line.
            for i in range(5):
                thorn_x = x + facing * (30 + i * 20)
                thorn_y = y + 42
                thorn_h = int(20 * intensity)
                pygame.draw.line(surface,
                                 _NS_vraskhan.PALETTE["void_darkest"],
                                 (thorn_x, thorn_y),
                                 (thorn_x, thorn_y - thorn_h), 3)
                pygame.draw.line(surface,
                                 _NS_vraskhan.PALETTE["void_dark"],
                                 (thorn_x, thorn_y),
                                 (thorn_x, thorn_y - thorn_h), 2)
                pygame.draw.line(surface,
                                 _NS_vraskhan.PALETTE["void_mid"],
                                 (thorn_x, thorn_y),
                                 (thorn_x, thorn_y - thorn_h), 1)
                pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_hot"],
                                 (thorn_x, thorn_y - thorn_h, 1, 1))

    # ============================================================
    # SKILL W — SHADOW LEAP (teleport to target)
    # ============================================================
    def _draw_shadowleap_body(surface, boss, x, y, timer, phase):
        """Body fades during leap phase."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wind-up: still visible.
        if progress < 0.25:
            _NS_vraskhan._draw_idle_pose(surface, boss, x, y)
            # Dark energy gathering around body.
            for i in range(8):
                angle = phase * 3 + i * math.pi / 4
                r = 20 + int(math.sin(phase * 2 + i) * 5)
                sx = x + int(math.cos(angle) * r)
                sy = y + int(math.sin(angle) * r * 0.5)
                alpha = _NS_vraskhan._alpha(200 * progress / 0.25)
                pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                 (sx, sy, 3, 3))
                pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                                 (sx, sy, 1, 1))
        elif progress < 0.75:
            # LEAPING (invisible/mid-teleport, just show shadow silhouette).
            t = (progress - 0.25) / 0.5
            tx, ty = _NS_vraskhan._target_position(boss, x, y)
            # Interpolate position.
            leap_x = int(x + (tx - x) * t)
            leap_y = int(y + (ty - y) * t) - int(math.sin(t * math.pi) * 40)

            # Shadowy silhouette.
            for r in range(15, 3, -2):
                alpha = _NS_vraskhan._alpha(180 * (15 - r) / 15)
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["shadow_darkest"], alpha),
                                        (leap_x, leap_y), r)
            for r in range(10, 1, -2):
                alpha = _NS_vraskhan._alpha(200 * (10 - r) / 10)
                _NS_vraskhan._aacircle(surface,
                                        (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                        (leap_x, leap_y), r)
            _NS_vraskhan._aacircle(surface, _NS_vraskhan.PALETTE["void_mid"],
                                    (leap_x, leap_y), 4)
            _NS_vraskhan._aacircle(surface, _NS_vraskhan.PALETTE["void_hot"],
                                    (leap_x, leap_y), 2)
            pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_shine"],
                             (leap_x, leap_y, 1, 1))
        else:
            # Landed: reappear at boss position.
            _NS_vraskhan._draw_idle_pose(surface, boss, x, y)

    def _draw_shadowleap_foreground(surface, boss, x, y, timer, phase):
        """Departure & arrival void impacts."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vraskhan._target_position(boss, x, y)

        if progress < 0.25:
            # Departure burst.
            t = progress / 0.25
            r = int(t * 30)
            alpha = _NS_vraskhan._alpha(220 * (1 - t))
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                    (x, y - 8), r, 3)
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                    (x, y - 8), max(1, r - 4), 2)
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_light"], alpha),
                                    (x, y - 8), max(1, r - 10), 1)
        elif progress > 0.7:
            # Arrival impact at target.
            t = (progress - 0.7) / 0.3
            r = int(15 + t * 30)
            alpha = _NS_vraskhan._alpha(240 * (1 - t))

            # Massive burst.
            for layer in range(5):
                lr = r - layer * 4
                if lr > 0:
                    colors = [_NS_vraskhan.PALETTE["void_darkest"],
                              _NS_vraskhan.PALETTE["void_dark"],
                              _NS_vraskhan.PALETTE["void_mid"],
                              _NS_vraskhan.PALETTE["void_light"],
                              _NS_vraskhan.PALETTE["void_hot"]]
                    _NS_vraskhan._aacircle(surface,
                                            (*colors[layer], alpha),
                                            (tx, ty), lr, 2)

            # Cross burst rays.
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * r)
                ey = ty + int(math.sin(angle_s) * r * 0.7)
                pygame.draw.line(surface,
                                 (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_vraskhan.PALETTE["void_shine"], alpha),
                                 (ex, ey, 2, 2))

            # Central bright.
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["white"], alpha),
                             (tx, ty, 2, 2))

    # ============================================================
    # SKILL E — DEATH SLASH (3 spinning slashes)
    # ============================================================
    def _draw_deathslash_ground(surface, boss, x, y, timer, phase):
        """AoE circle around boss."""
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 55
        alpha = _NS_vraskhan._alpha(180)
        pygame.draw.ellipse(surface, (*_NS_vraskhan.PALETTE["void_darkest"], alpha),
                            (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                            (x - r + 3, y + 42 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                            (x - r + 8, y + 42 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_deathslash_foreground(surface, boss, x, y, timer, phase):
        """3 rotating slash arcs around boss."""
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 3 slashes: at 0.2, 0.5, 0.8 progress.
        slash_windows = [(0.15, 0.4), (0.4, 0.65), (0.65, 0.9)]

        for slash_i, (w_start, w_end) in enumerate(slash_windows):
            if progress < w_start or progress > w_end:
                continue

            t = (progress - w_start) / (w_end - w_start)
            # Rotate slash around boss.
            base_angle = slash_i * math.pi * 2 / 3 + phase * 0.5
            arc_sweep = math.pi * 1.5  # 270 degrees arc

            num_pts = 20
            arc_points = []
            for i in range(num_pts):
                a_t = i / (num_pts - 1)
                angle = base_angle + a_t * arc_sweep
                r = 40 + int(math.sin(phase * 2) * 3)
                ax = x + int(math.cos(angle) * r)
                ay = y + int(math.sin(angle) * r * 0.5)
                arc_points.append((ax, ay))

            # Reveal arc based on t.
            visible = int(len(arc_points) * t)
            intensity = math.sin(t * math.pi)

            for i in range(max(1, visible) - 1):
                fade = i / max(1, visible)
                alpha = _NS_vraskhan._alpha(240 * intensity * (1 - abs(fade - 0.5)))
                _NS_vraskhan._aaline(surface,
                                      (*_NS_vraskhan.PALETTE["void_darkest"], alpha),
                                      arc_points[i], arc_points[i + 1], 5)
                _NS_vraskhan._aaline(surface,
                                      (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                                      arc_points[i], arc_points[i + 1], 3)
                _NS_vraskhan._aaline(surface,
                                      (*_NS_vraskhan.PALETTE["void_mid"], alpha),
                                      arc_points[i], arc_points[i + 1], 2)
                _NS_vraskhan._aaline(surface,
                                      (*_NS_vraskhan.PALETTE["void_light"], alpha),
                                      arc_points[i], arc_points[i + 1], 1)
                pygame.draw.rect(surface,
                                 (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                                 (arc_points[i][0], arc_points[i][1], 1, 1))

            # Bright tip.
            if visible > 0:
                tip = arc_points[min(visible, len(arc_points) - 1)]
                for r in range(5, 0, -1):
                    _NS_vraskhan._aacircle(surface,
                                            (*_NS_vraskhan.PALETTE["void_hot"],
                                             _NS_vraskhan._alpha(200 * intensity)),
                                            tip, r)
                pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_shine"],
                                 (tip[0], tip[1], 1, 1))

    # ============================================================
    # SKILL R — OMNI ARMS (ultimate form with multiple blade rings)
    # ============================================================
    def _draw_omni_ground(surface, boss, x, y, timer, phase):
        """Ultimate ground rune."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rotating pentagram/star rune.
        r = 50
        num_points = 6
        for i in range(num_points):
            angle1 = phase * 0.5 + i * 2 * math.pi / num_points
            angle2 = phase * 0.5 + ((i + 2) % num_points) * 2 * math.pi / num_points
            x1 = x + int(math.cos(angle1) * r)
            y1 = y + 42 + int(math.sin(angle1) * r * 0.4)
            x2 = x + int(math.cos(angle2) * r)
            y2 = y + 42 + int(math.sin(angle2) * r * 0.4)
            alpha = _NS_vraskhan._alpha(200)
            pygame.draw.line(surface, (*_NS_vraskhan.PALETTE["void_darkest"], alpha),
                             (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface, (*_NS_vraskhan.PALETTE["void_dark"], alpha),
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(surface, (*_NS_vraskhan.PALETTE["void_light"], alpha),
                             (x1, y1), (x2, y2), 1)

        # Outer ring.
        pygame.draw.ellipse(surface, (*_NS_vraskhan.PALETTE["void_hot"], 180),
                            (x - r - 5, y + 42 - r // 3 - 3, r * 2 + 10, r * 2 // 3 + 6), 2)

    def _draw_omni_foreground(surface, boss, x, y, timer, phase):
        """Multiple rotating blade rings around boss."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 2 counter-rotating rings of ethereal blades.
        for ring_i, (ring_r, direction, count, base_speed) in enumerate([
            (35, 1, 6, 0.8),
            (55, -1, 8, 0.5),
        ]):
            for i in range(count):
                angle = phase * base_speed * direction + i * math.pi * 2 / count
                bx = x + int(math.cos(angle) * ring_r)
                by = y - 5 + int(math.sin(angle) * ring_r * 0.55)

                # Ethereal blade shape (small curved shard).
                blade_size = 10 + int(math.sin(phase + i) * 2)

                # Draw a small floating blade.
                tip_angle = angle + math.pi / 2 * direction
                tip_x = bx + int(math.cos(tip_angle) * blade_size)
                tip_y = by + int(math.sin(tip_angle) * blade_size * 0.5)

                # Shadow behind.
                pygame.draw.line(surface,
                                 (*_NS_vraskhan.PALETTE["shadow_deep"], 200),
                                 (bx + 1, by + 1), (tip_x + 1, tip_y + 1), 4)
                # Blade layers.
                pygame.draw.line(surface, _NS_vraskhan.PALETTE["void_darkest"],
                                 (bx, by), (tip_x, tip_y), 3)
                pygame.draw.line(surface, _NS_vraskhan.PALETTE["void_dark"],
                                 (bx, by), (tip_x, tip_y), 2)
                pygame.draw.line(surface, _NS_vraskhan.PALETTE["void_mid"],
                                 (bx, by), (tip_x, tip_y), 1)
                # Glowing edge.
                pygame.draw.line(surface, _NS_vraskhan.PALETTE["void_light"],
                                 (bx, by - 1), (tip_x, tip_y - 1), 1)

                # Tip glow.
                _NS_vraskhan._aacircle(surface, _NS_vraskhan.PALETTE["void_hot"],
                                        (tip_x, tip_y), 2)
                pygame.draw.rect(surface, _NS_vraskhan.PALETTE["void_shine"],
                                 (tip_x, tip_y, 1, 1))

                # Base halo.
                for r in range(3, 0, -1):
                    _NS_vraskhan._aacircle(surface,
                                            (*_NS_vraskhan.PALETTE["void_mid"],
                                             _NS_vraskhan._alpha(120 * (3 - r) / 3)),
                                            (bx, by), r)

        # Extra energy swirls around boss.
        for i in range(20):
            swirl_t = (phase * 1.5 + i * 0.1) % 1.0
            swirl_r = int(20 + swirl_t * 50)
            swirl_angle = phase * 2 + i * math.pi / 10
            sx = x + int(math.cos(swirl_angle) * swirl_r)
            sy = y - 5 + int(math.sin(swirl_angle) * swirl_r * 0.5)
            alpha = _NS_vraskhan._alpha(240 * (1 - swirl_t))
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_vraskhan.PALETTE["void_shine"], alpha),
                             (sx, sy, 1, 1))

        # Aura around body (transformed form).
        for r in range(30, 5, -3):
            alpha = _NS_vraskhan._alpha(60 * (30 - r) / 30)
            _NS_vraskhan._aacircle(surface,
                                    (*_NS_vraskhan.PALETTE["void_hot"], alpha),
                                    (x, y - 5), r)


# ====================================================================
# aurethzar.py
# ====================================================================

# ====================================================================
# AURETHZAR - THE SUNPIERCER (TRUE BOSS)
# Radiant solar archer dengan golden bow dan wings emas
# ====================================================================


class _NS_aurethzar:
    """Namespace aurethzar - true boss solar archer bertema emas radiant."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Gold armor (main body)
        "gold_darkest": (35, 22, 5),
        "gold_dark": (95, 65, 15),
        "gold_mid": (180, 130, 35),
        "gold_light": (240, 195, 80),
        "gold_edge": (255, 225, 140),
        "gold_shine": (255, 250, 210),

        # White cloth/tabard (accent)
        "cloth_dark": (95, 85, 65),
        "cloth_mid": (185, 170, 140),
        "cloth_light": (240, 230, 210),
        "cloth_shine": (255, 250, 235),

        # Skin tone (heroic pale)
        "skin_dark": (110, 75, 55),
        "skin_mid": (200, 155, 115),
        "skin_light": (245, 210, 175),

        # Blonde hair
        "hair_dark": (90, 55, 15),
        "hair_mid": (200, 145, 45),
        "hair_light": (250, 210, 110),
        "hair_shine": (255, 245, 180),

        # Solar/radiant energy (bright yellow-white)
        "solar_darkest": (45, 25, 5),
        "solar_dark": (130, 75, 15),
        "solar_mid": (230, 165, 40),
        "solar_light": (255, 220, 100),
        "solar_hot": (255, 245, 170),
        "solar_shine": (255, 255, 230),

        # Ice (for E skill - contrast)
        "ice_dark": (25, 55, 100),
        "ice_mid": (80, 155, 220),
        "ice_light": (170, 220, 255),
        "ice_shine": (230, 250, 255),

        # Deep blue sky background accents
        "sky_dark": (10, 15, 40),
        "sky_mid": (40, 55, 110),

        # Fiery accents
        "fire_dark": (100, 30, 10),
        "fire_mid": (220, 100, 30),
        "fire_light": (255, 180, 80),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 2, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_aurethzar._clamp(color)
        if _NS_aurethzar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_aurethzar._clamp(color)
        if _NS_aurethzar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_aurethzar._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 300 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_aurethzar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_aurethzar._detect_moving(boss)
        _NS_aurethzar._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_aur_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind (BIG for TRUE BOSS).
        _NS_aurethzar._draw_solar_aura(surface, x, y, pulse)
        _NS_aurethzar._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "r":
            _NS_aurethzar._draw_thunder_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating with wings).
        if attacking:
            _NS_aurethzar._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_aurethzar._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_aurethzar._draw_idle_pose(surface, boss, x, y)

        # Foreground FX (skill projectiles).
        if attacking:
            _NS_aurethzar._draw_basic_arrow(surface, boss, x, y)
        if active_skill == "q":
            _NS_aurethzar._draw_marksman_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_aurethzar._draw_piercing_arrow(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurethzar._draw_frost_shot(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurethzar._draw_distant_thunder(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aur_previous_timer", 0))
        active = bool(getattr(boss, "_aur_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aur_attack_active = True
            boss._aur_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._aur_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._aur_attack_frame = int(getattr(boss, "_aur_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._aur_attack_active = False
            boss._aur_attack_frame = 0
            active = False

        boss._aur_previous_timer = timer
        boss._aur_attack_progress = (
            min(1.0, getattr(boss, "_aur_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_aur_last_x"):
            boss._aur_last_x = boss.x
            boss._aur_last_y = boss.y
            return False
        dx = abs(boss.x - boss._aur_last_x)
        dy = abs(boss.y - boss._aur_last_y)
        boss._aur_last_x = boss.x
        boss._aur_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        float_y = int(math.sin(boss.pulse * 0.6) * 6)
        _NS_aurethzar._draw_shadow(surface, x, y + 52)
        _NS_aurethzar._draw_solar_particles(surface, x, y + 48, boss.pulse)
        _NS_aurethzar._draw_body(surface, x, y - 8 + float_y,
                                  boss.direction, boss.pulse, "idle")

    def _draw_walk_pose(surface, boss, x, y):
        phase = boss.pulse * 2.0
        float_y = int(math.sin(phase * 0.9) * 8)
        sway = int(math.sin(phase * 0.6) * 2)
        _NS_aurethzar._draw_shadow(surface, x + sway, y + 52)
        _NS_aurethzar._draw_solar_particles(surface, x + sway, y + 48, phase,
                                             trail=True, facing=boss.direction)
        _NS_aurethzar._draw_body(surface, x + sway, y - 8 + float_y,
                                  boss.direction, phase, "walk")

    def _draw_attack_pose(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_aur_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_aur_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Archer draw-and-shoot pose.
        if progress < 0.5:
            # Draw back bow.
            t = progress / 0.5
            lunge = int(-t * 3) * facing
            lift = int(t * 3)
        elif progress < 0.65:
            # RELEASE (small forward push).
            t = (progress - 0.5) / 0.15
            lunge = int((-3 + t * 8)) * facing
            lift = int(3 - t * 5)
        else:
            # Recovery.
            t = (progress - 0.65) / 0.35
            lunge = int(5 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        float_y = int(math.sin(boss.pulse * 0.6) * 4)

        _NS_aurethzar._draw_shadow(surface, x + lunge, y + 52)
        _NS_aurethzar._draw_solar_particles(surface, x + lunge, y + 48,
                                             boss.pulse, intense=True)
        _NS_aurethzar._draw_body(surface, x + lunge, y - 8 - lift + float_y,
                                  facing, boss.pulse, "attack", progress)

    # ============================================================
    # BODY - Archer Humanoid
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Archer with golden wings, bow, and radiant armor."""
        # Wings FIRST (behind body).
        _NS_aurethzar._draw_solar_wings(surface, cx, cy - 4, facing, phase, action,
                                         attack_progress)

        # Legs (floating).
        _NS_aurethzar._draw_legs(surface, cx, cy + 22, facing, phase, action)

        # Torso.
        _NS_aurethzar._draw_torso(surface, cx, cy + 4, facing, phase)

        # Cape (small back cloth).
        _NS_aurethzar._draw_cape(surface, cx, cy + 4, facing, phase, action)

        # Head with hair and halo.
        _NS_aurethzar._draw_head(surface, cx, cy - 16, facing, phase, action)

        # Arms + bow.
        _NS_aurethzar._draw_arms_with_bow(surface, cx, cy + 2, facing, phase,
                                            action, attack_progress)

    def _draw_solar_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Large radiant golden wings (feather + solar energy)."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 1.2) * 4

        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),
            (1, 0.75, 0.7),
        ]):
            base_x = cx - facing * 3
            base_y = cy - 2

            # Wing feather spars (3 main).
            spars = [
                (math.pi * 0.55 * side_mult - math.radians(beat), 34),
                (math.pi * 0.75 * side_mult - math.radians(beat * 0.8), 40),
                (math.pi * 0.95 * side_mult - math.radians(beat * 0.5), 32),
                (math.pi * 1.15 * side_mult - math.radians(beat * 0.3), 24),
            ]

            wing_surf = pygame.Surface((170, 120), pygame.SRCALPHA)
            offset_x = base_x - 85
            offset_y = base_y - 60

            # Draw wing membrane (glowing base).
            spar_tips = []
            for angle, length in spars:
                length = int(length * size_mult)
                tx = base_x + int(math.cos(angle) * length) * (-facing) - offset_x
                ty = base_y - int(math.sin(angle) * length) - offset_y
                spar_tips.append((tx, ty))

            # Membrane fills between spar tips.
            base_local = (base_x - offset_x, base_y - offset_y)
            for i in range(len(spar_tips) - 1):
                membrane_shape = [
                    base_local,
                    spar_tips[i],
                    (int((spar_tips[i][0] + spar_tips[i + 1][0]) / 2),
                     int((spar_tips[i][1] + spar_tips[i + 1][1]) / 2) + 4),
                    spar_tips[i + 1],
                ]
                # Layered gold membrane.
                _NS_aurethzar._poly(wing_surf,
                                     (*_NS_aurethzar.PALETTE["gold_darkest"],
                                      int(220 * alpha_mult)),
                                     membrane_shape)
                _NS_aurethzar._poly(wing_surf,
                                     (*_NS_aurethzar.PALETTE["gold_dark"],
                                      int(200 * alpha_mult)),
                                     [(int(p[0] * 0.9 + base_local[0] * 0.1),
                                       int(p[1] * 0.9 + base_local[1] * 0.1))
                                      for p in membrane_shape])

            # Feathers - draw individual feather shapes on each spar.
            for spar_i, ((angle, length), tip) in enumerate(zip(spars, spar_tips)):
                length_actual = int(length * size_mult)

                # Draw multiple feathers along spar.
                num_feathers = 6
                for f in range(num_feathers):
                    ft = (f + 1) / num_feathers
                    feather_pos_x = int(base_local[0] + (tip[0] - base_local[0]) * ft)
                    feather_pos_y = int(base_local[1] + (tip[1] - base_local[1]) * ft)

                    # Feather size decreases toward tip.
                    feather_len = int(8 * (1 - ft * 0.5) * size_mult)
                    feather_angle = angle + math.radians(30 * side_mult)
                    fx_end = feather_pos_x + int(math.cos(feather_angle) * feather_len) * (-facing)
                    fy_end = feather_pos_y - int(math.sin(feather_angle) * feather_len)

                    # Feather shape (elongated).
                    pygame.draw.line(wing_surf,
                                     (*_NS_aurethzar.PALETTE["gold_darkest"],
                                      int(240 * alpha_mult)),
                                     (feather_pos_x, feather_pos_y),
                                     (fx_end, fy_end), 3)
                    pygame.draw.line(wing_surf,
                                     (*_NS_aurethzar.PALETTE["gold_dark"],
                                      int(240 * alpha_mult)),
                                     (feather_pos_x, feather_pos_y),
                                     (fx_end, fy_end), 2)
                    pygame.draw.line(wing_surf,
                                     (*_NS_aurethzar.PALETTE["gold_mid"],
                                      int(240 * alpha_mult)),
                                     (feather_pos_x, feather_pos_y),
                                     (fx_end, fy_end), 1)
                    # Feather tip glow.
                    pygame.draw.rect(wing_surf,
                                     (*_NS_aurethzar.PALETTE["gold_light"],
                                      int(240 * alpha_mult)),
                                     (fx_end, fy_end, 1, 1))
                    pygame.draw.rect(wing_surf,
                                     (*_NS_aurethzar.PALETTE["solar_hot"],
                                      int(240 * alpha_mult)),
                                     (fx_end, fy_end, 1, 1))

                # Main spar (thick).
                pygame.draw.line(wing_surf,
                                 (*_NS_aurethzar.PALETTE["gold_darkest"],
                                  int(250 * alpha_mult)),
                                 base_local, tip, 4)
                pygame.draw.line(wing_surf,
                                 (*_NS_aurethzar.PALETTE["gold_dark"],
                                  int(250 * alpha_mult)),
                                 base_local, tip, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_aurethzar.PALETTE["gold_mid"],
                                  int(250 * alpha_mult)),
                                 base_local, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_aurethzar.PALETTE["gold_light"],
                                  int(250 * alpha_mult)),
                                 base_local, tip, 1)

                # Bright spar tip.
                _NS_aurethzar._aacircle(wing_surf,
                                         (*_NS_aurethzar.PALETTE["solar_light"],
                                          int(240 * alpha_mult)),
                                         tip, 2)
                pygame.draw.rect(wing_surf,
                                 (*_NS_aurethzar.PALETTE["solar_shine"],
                                  int(240 * alpha_mult)),
                                 (tip[0], tip[1], 1, 1))

            # Solar glow along top edge of wing.
            for r in range(6, 0, -1):
                alpha_g = _NS_aurethzar._alpha(120 * (6 - r) / 6 * alpha_mult)
                if len(spar_tips) > 0:
                    _NS_aurethzar._aacircle(wing_surf,
                                             (*_NS_aurethzar.PALETTE["solar_light"], alpha_g),
                                             spar_tips[0], r)
                    _NS_aurethzar._aacircle(wing_surf,
                                             (*_NS_aurethzar.PALETTE["solar_hot"], alpha_g),
                                             spar_tips[1], r)

            # Sparkles.
            for i in range(6):
                sx = int(spar_tips[i % len(spar_tips)][0] + math.sin(phase + i) * 4)
                sy = int(spar_tips[i % len(spar_tips)][1] + math.cos(phase + i) * 4)
                pygame.draw.rect(wing_surf,
                                 (*_NS_aurethzar.PALETTE["solar_shine"],
                                  int(230 * alpha_mult)),
                                 (sx, sy, 1, 1))

            surface.blit(wing_surf, (offset_x, offset_y))

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Armored legs (floating, boots)."""
        dangle = math.sin(phase * 0.9) * 1

        for side_i, off_x in enumerate((-5, 5)):
            lx = cx + off_x
            ly = cy + int(dangle) + side_i

            # Thigh.
            _NS_aurethzar._draw_leg_segment(surface, (lx, ly - 10),
                                              (lx + off_x // 4, ly - 2), 5)
            # Shin.
            _NS_aurethzar._draw_leg_segment(surface, (lx + off_x // 4, ly - 2),
                                              (lx + off_x // 3, ly + 7), 4)

            # Boot.
            boot_x = lx + off_x // 3
            boot_y = ly + 7
            boot_shape = [
                (boot_x - 4, boot_y - 1),
                (boot_x + 3, boot_y - 1),
                (boot_x + 5, boot_y + 1),
                (boot_x + 6 * facing + (facing if facing > 0 else -1), boot_y + 3),
                (boot_x - 3, boot_y + 3),
            ]
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                                 [(p[0] + 1, p[1] + 1) for p in boot_shape])
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_darkest"], boot_shape)
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_dark"], [
                (boot_x - 3, boot_y - 1),
                (boot_x + 3, boot_y - 1),
                (boot_x + 4, boot_y + 1),
                (boot_x + 5 * facing, boot_y + 2),
                (boot_x - 2, boot_y + 2),
            ])
            # Golden boot trim.
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["gold_light"],
                             (boot_x - 3, boot_y - 1), (boot_x + 3, boot_y - 1), 1)
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_edge"],
                             (boot_x, boot_y - 1, 1, 1))

            # Knee guard (gold plate).
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                             (lx + off_x // 4 - 2, ly - 3, 4, 3))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_dark"],
                             (lx + off_x // 4 - 2, ly - 3, 4, 2))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_mid"],
                             (lx + off_x // 4 - 1, ly - 3, 3, 1))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_edge"],
                             (lx + off_x // 4, ly - 3, 1, 1))

    def _draw_leg_segment(surface, start, end, thickness):
        # Cloth/pant color base.
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                               (start[0] + 1, start[1] + 1),
                               (end[0] + 1, end[1] + 1), thickness + 1)
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["cloth_dark"],
                               start, end, thickness)
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["cloth_mid"],
                               (start[0], start[1] - 1), (end[0], end[1] - 1),
                               max(1, thickness - 2))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Heroic armored torso with tabard and gold plate."""
        # Main torso shape.
        torso_shape = [
            (cx - 13, cy - 12),
            (cx - 15, cy - 8),
            (cx - 14, cy - 2),
            (cx - 11, cy + 6),
            (cx - 8, cy + 14),
            (cx - 4, cy + 18),
            (cx + 4, cy + 18),
            (cx + 8, cy + 14),
            (cx + 11, cy + 6),
            (cx + 14, cy - 2),
            (cx + 15, cy - 8),
            (cx + 13, cy - 12),
            (cx + 6, cy - 14),
            (cx - 6, cy - 14),
        ]
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 2) for p in torso_shape])

        # White cloth undertunic base (visible parts).
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_dark"], torso_shape)
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_mid"], [
            (cx - 10, cy - 10), (cx - 12, cy - 6), (cx - 11, cy),
            (cx - 8, cy + 8), (cx - 5, cy + 14), (cx + 5, cy + 14),
            (cx + 8, cy + 8), (cx + 11, cy), (cx + 12, cy - 6),
            (cx + 10, cy - 10), (cx + 5, cy - 12), (cx - 5, cy - 12),
        ])

        # Golden chest plate (top layer).
        chest_plate = [
            (cx - 11, cy - 12),
            (cx - 13, cy - 8),
            (cx - 12, cy - 2),
            (cx - 8, cy + 4),
            (cx + 8, cy + 4),
            (cx + 12, cy - 2),
            (cx + 13, cy - 8),
            (cx + 11, cy - 12),
            (cx + 5, cy - 14),
            (cx - 5, cy - 14),
        ]
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_darkest"], chest_plate)
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_dark"], [
            (cx - 10, cy - 11), (cx - 12, cy - 7), (cx - 11, cy - 2),
            (cx - 7, cy + 3), (cx + 7, cy + 3), (cx + 11, cy - 2),
            (cx + 12, cy - 7), (cx + 10, cy - 11), (cx + 5, cy - 13),
            (cx - 5, cy - 13),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_mid"], [
            (cx - 8, cy - 9), (cx - 10, cy - 5), (cx - 9, cy - 1),
            (cx - 5, cy + 2), (cx + 5, cy + 2), (cx + 9, cy - 1),
            (cx + 10, cy - 5), (cx + 8, cy - 9), (cx + 4, cy - 11),
            (cx - 4, cy - 11),
        ])
        # Chest highlight.
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_light"], [
            (cx - 5, cy - 6), (cx - 6, cy - 2), (cx - 3, cy + 1),
            (cx + 3, cy + 1), (cx + 6, cy - 2), (cx + 5, cy - 6),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_edge"], [
            (cx - 3, cy - 4), (cx - 4, cy - 1), (cx, cy + 1),
            (cx + 3, cy - 1), (cx + 3, cy - 4),
        ])

        # Center emblem (sun/star).
        emblem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        emblem_x, emblem_y = cx, cy - 4

        # Glow behind emblem.
        for r in range(6, 1, -1):
            alpha = _NS_aurethzar._alpha(140 * (6 - r) / 6 * emblem_pulse)
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                     (emblem_x, emblem_y), r)

        # Sun emblem (4-point star).
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["solar_darkest"], [
            (emblem_x, emblem_y - 4), (emblem_x + 2, emblem_y),
            (emblem_x, emblem_y + 4), (emblem_x - 2, emblem_y),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["solar_mid"], [
            (emblem_x, emblem_y - 3), (emblem_x + 1, emblem_y),
            (emblem_x, emblem_y + 3), (emblem_x - 1, emblem_y),
        ])
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_hot"],
                         (emblem_x, emblem_y, 1, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"],
                         (emblem_x, emblem_y, 1, 1))

        # Shoulder pauldrons (large gold).
        for side in (-1, 1):
            sx_shoulder = cx + side * 14
            sy_shoulder = cy - 10
            pauldron = [
                (sx_shoulder - 4 * side, sy_shoulder + 3),
                (sx_shoulder - 2 * side, sy_shoulder - 4),
                (sx_shoulder + 4 * side, sy_shoulder - 5),
                (sx_shoulder + 6 * side, sy_shoulder - 2),
                (sx_shoulder + 5 * side, sy_shoulder + 4),
                (sx_shoulder, sy_shoulder + 5),
            ]
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                                 [(p[0] + 1, p[1] + 1) for p in pauldron])
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_darkest"], pauldron)
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_dark"], [
                (sx_shoulder - 3 * side, sy_shoulder + 2),
                (sx_shoulder - 1 * side, sy_shoulder - 3),
                (sx_shoulder + 3 * side, sy_shoulder - 4),
                (sx_shoulder + 5 * side, sy_shoulder - 2),
                (sx_shoulder + 4 * side, sy_shoulder + 3),
                (sx_shoulder, sy_shoulder + 4),
            ])
            _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["gold_mid"], [
                (sx_shoulder - 1 * side, sy_shoulder),
                (sx_shoulder + 2 * side, sy_shoulder - 3),
                (sx_shoulder + 4 * side, sy_shoulder - 1),
                (sx_shoulder + 3 * side, sy_shoulder + 2),
                (sx_shoulder, sy_shoulder + 3),
            ])
            # Small spike on top of pauldron.
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                             (sx_shoulder + 2 * side, sy_shoulder - 5),
                             (sx_shoulder + 3 * side, sy_shoulder - 10), 2)
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["gold_dark"],
                             (sx_shoulder + 2 * side, sy_shoulder - 5),
                             (sx_shoulder + 3 * side, sy_shoulder - 10), 1)
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_light"],
                             (sx_shoulder + 3 * side, sy_shoulder - 10, 1, 1))

        # Tabard/skirt below belt.
        tabard = [
            (cx - 7, cy + 6),
            (cx + 7, cy + 6),
            (cx + 9, cy + 12),
            (cx + 5, cy + 18),
            (cx - 5, cy + 18),
            (cx - 9, cy + 12),
        ]
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in tabard])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_dark"], tabard)
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_mid"], [
            (cx - 6, cy + 7), (cx + 6, cy + 7), (cx + 8, cy + 12),
            (cx + 4, cy + 17), (cx - 4, cy + 17), (cx - 8, cy + 12),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_light"], [
            (cx - 3, cy + 8), (cx + 3, cy + 8), (cx + 3, cy + 15),
            (cx - 3, cy + 15),
        ])
        # Gold trim.
        pygame.draw.line(surface, _NS_aurethzar.PALETTE["gold_mid"],
                         (cx - 5, cy + 18), (cx + 5, cy + 18), 1)
        pygame.draw.line(surface, _NS_aurethzar.PALETTE["gold_light"],
                         (cx - 4, cy + 17), (cx + 4, cy + 17), 1)

        # Belt with buckle.
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                         (cx - 8, cy + 4, 16, 3))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_dark"],
                         (cx - 8, cy + 4, 16, 2))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_mid"],
                         (cx - 7, cy + 4, 14, 1))
        # Buckle.
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_edge"],
                         (cx - 2, cy + 4, 4, 3))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_hot"],
                         (cx - 1, cy + 5, 2, 1))

    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Small back cloth flapping."""
        flutter = math.sin(phase * 1.5) * 2
        if action != "idle":
            flutter *= 1.5

        back_dir = -facing
        base_x = cx + back_dir * 6
        base_y = cy - 6

        cape_shape = [
            (base_x, base_y),
            (base_x + back_dir * 4, base_y + 4 + int(flutter)),
            (base_x + back_dir * 6, base_y + 12 + int(flutter * 0.7)),
            (base_x + back_dir * 4, base_y + 18),
            (base_x, base_y + 14),
        ]
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in cape_shape])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_dark"], cape_shape)
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["cloth_mid"], [
            (base_x, base_y + 1),
            (base_x + back_dir * 3, base_y + 4 + int(flutter)),
            (base_x + back_dir * 5, base_y + 11 + int(flutter * 0.7)),
            (base_x + back_dir * 3, base_y + 16),
            (base_x, base_y + 12),
        ])

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Heroic head with blonde flowing hair and halo."""
        # Neck.
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["skin_dark"],
                         (cx - 2, cy + 6, 4, 4))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["skin_mid"],
                         (cx - 2, cy + 6, 3, 3))

        # Head shape (oval).
        head_shape = [
            (cx - 6, cy - 3),
            (cx - 7, cy),
            (cx - 6, cy + 4),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 4),
            (cx + 7, cy),
            (cx + 6, cy - 3),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ]
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in head_shape])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["skin_dark"], head_shape)
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["skin_mid"], [
            (cx - 5, cy - 2), (cx - 6, cy), (cx - 5, cy + 3),
            (cx - 2, cy + 6), (cx + 2, cy + 6), (cx + 5, cy + 3),
            (cx + 6, cy), (cx + 5, cy - 2), (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])
        # Skin highlight.
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["skin_light"], [
            (cx - 3, cy - 1), (cx - 4, cy + 1), (cx - 2, cy + 3),
            (cx + 2, cy + 3), (cx + 4, cy + 1), (cx + 3, cy - 1),
        ])

        # BLONDE HAIR (flowing).
        _NS_aurethzar._draw_hair(surface, cx, cy - 4, facing, phase, action)

        # Eyes.
        eye_x_off = -1 if facing > 0 else 1
        # Focused/heroic eyes.
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                         (cx - 3 + eye_x_off, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                         (cx + 1 + eye_x_off, cy - 1, 2, 2))
        # Blue iris.
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["ice_mid"],
                         (cx - 3 + eye_x_off, cy, 2, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["ice_mid"],
                         (cx + 1 + eye_x_off, cy, 2, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["ice_light"],
                         (cx - 2 + eye_x_off, cy, 1, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["ice_light"],
                         (cx + 2 + eye_x_off, cy, 1, 1))

        # Mouth.
        if action == "attack":
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             (cx - 2, cy + 4), (cx + 2, cy + 4), 1)
        else:
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             (cx - 1, cy + 4, 3, 1))

        # HALO (solar crown above head).
        _NS_aurethzar._draw_halo(surface, cx, cy - 9, phase)

    def _draw_hair(surface, cx, cy, facing, phase, action):
        """Blonde flowing hair."""
        flow = math.sin(phase * 0.7) * 1
        if action != "idle":
            flow *= 2

        back_dir = -facing

        # Base hair mass on top and around head.
        hair_shape = [
            (cx - 7, cy),
            (cx - 8, cy - 2),
            (cx - 7, cy - 6),
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx + 7, cy - 6),
            (cx + 8, cy - 2),
            (cx + 7, cy),
            (cx + 6, cy + 2),
            (cx - 6, cy + 2),
        ]
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in hair_shape])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["hair_dark"], hair_shape)
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["hair_mid"], [
            (cx - 6, cy - 1), (cx - 7, cy - 3), (cx - 6, cy - 5),
            (cx - 2, cy - 7), (cx + 2, cy - 7), (cx + 6, cy - 5),
            (cx + 7, cy - 3), (cx + 6, cy - 1), (cx + 5, cy),
            (cx - 5, cy),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["hair_light"], [
            (cx - 4, cy - 3), (cx - 5, cy - 5), (cx - 2, cy - 6),
            (cx + 2, cy - 6), (cx + 5, cy - 5), (cx + 4, cy - 3),
        ])
        # Highlight streak.
        pygame.draw.line(surface, _NS_aurethzar.PALETTE["hair_shine"],
                         (cx - 2, cy - 6), (cx + 2, cy - 5), 1)

        # Long hair strand flowing back.
        strand_flow = int(flow)
        strand_points = [
            (cx + back_dir * 6, cy + 2),
            (cx + back_dir * 8, cy + 6 + strand_flow),
            (cx + back_dir * 10, cy + 12 + strand_flow),
            (cx + back_dir * 8, cy + 18 + strand_flow // 2),
        ]
        for i in range(len(strand_points) - 1):
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                                    (strand_points[i][0] + 1, strand_points[i][1] + 1),
                                    (strand_points[i + 1][0] + 1, strand_points[i + 1][1] + 1),
                                    4)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["hair_dark"],
                                    strand_points[i], strand_points[i + 1], 3)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["hair_mid"],
                                    strand_points[i], strand_points[i + 1], 2)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["hair_light"],
                                    (strand_points[i][0], strand_points[i][1] - 1),
                                    (strand_points[i + 1][0], strand_points[i + 1][1] - 1),
                                    1)

    def _draw_halo(surface, cx, cy, phase):
        """Solar halo/crown above head."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7

        # Halo ring.
        halo_r = 8
        for r in range(halo_r + 3, halo_r - 2, -1):
            alpha = _NS_aurethzar._alpha(180 * pulse * (halo_r + 3 - r) / 3)
            if r >= 0:
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (cx, cy), r, 1)

        # Inner bright ring.
        _NS_aurethzar._aacircle(surface,
                                 (*_NS_aurethzar.PALETTE["solar_light"],
                                  _NS_aurethzar._alpha(220 * pulse)),
                                 (cx, cy), halo_r, 1)
        _NS_aurethzar._aacircle(surface,
                                 (*_NS_aurethzar.PALETTE["solar_hot"],
                                  _NS_aurethzar._alpha(200 * pulse)),
                                 (cx, cy), halo_r - 1, 1)

        # Sun rays extending from halo.
        num_rays = 8
        for i in range(num_rays):
            angle = phase * 0.3 + i * math.pi * 2 / num_rays
            ray_start_r = halo_r + 1
            ray_end_r = halo_r + 4 + int(math.sin(phase * 2 + i) * 2)
            sx = cx + int(math.cos(angle) * ray_start_r)
            sy = cy + int(math.sin(angle) * ray_start_r)
            ex = cx + int(math.cos(angle) * ray_end_r)
            ey = cy + int(math.sin(angle) * ray_end_r)
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_light"],
                             (sx, sy), (ex, ey), 2)
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_hot"],
                             (sx, sy), (ex, ey), 1)
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"],
                             (ex, ey, 1, 1))

    def _draw_arms_with_bow(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms - one holds bow, one draws string."""
        idle_sway = math.sin(phase * 0.6) * 2

        # Determine bow draw state.
        if action == "attack":
            if attack_progress < 0.5:
                # Drawing back.
                draw_t = attack_progress / 0.5
            elif attack_progress < 0.65:
                # Released.
                draw_t = 1.0 - (attack_progress - 0.5) / 0.15
            else:
                draw_t = 0
        else:
            draw_t = 0.3  # slight draw at rest

        # BOW ARM (front arm - holds bow extended forward).
        bow_shoulder_x = cx + facing * 12
        bow_shoulder_y = cy - 6
        bow_arm_angle = math.radians(0)  # extended forward
        bow_elbow_x = bow_shoulder_x + facing * 8
        bow_elbow_y = bow_shoulder_y + 2 + int(idle_sway)
        bow_hand_x = bow_elbow_x + facing * 8
        bow_hand_y = bow_elbow_y + int(idle_sway * 0.5)

        # Draw bow arm.
        _NS_aurethzar._draw_arm_segment(surface, (bow_shoulder_x, bow_shoulder_y),
                                          (bow_elbow_x, bow_elbow_y), 4)
        _NS_aurethzar._draw_arm_segment(surface, (bow_elbow_x, bow_elbow_y),
                                          (bow_hand_x, bow_hand_y), 3)

        # STRING-DRAWING ARM (back arm - pulls string).
        draw_shoulder_x = cx - facing * 12
        draw_shoulder_y = cy - 6
        # Elbow position pulled back more when drawing.
        pull_offset = int(draw_t * 8)
        draw_elbow_x = draw_shoulder_x - facing * (5 + pull_offset)
        draw_elbow_y = draw_shoulder_y + 1 + int(idle_sway * 0.5)
        # Hand near ear/cheek when fully drawn.
        draw_hand_x = draw_elbow_x + facing * 2 - int(draw_t * 4) * facing
        draw_hand_y = draw_elbow_y - int(draw_t * 4)

        _NS_aurethzar._draw_arm_segment(surface, (draw_shoulder_x, draw_shoulder_y),
                                          (draw_elbow_x, draw_elbow_y), 4)
        _NS_aurethzar._draw_arm_segment(surface, (draw_elbow_x, draw_elbow_y),
                                          (draw_hand_x, draw_hand_y), 3)

        # Draw the BOW.
        _NS_aurethzar._draw_bow(surface, bow_hand_x, bow_hand_y,
                                 draw_hand_x, draw_hand_y, facing, phase, draw_t)

    def _draw_arm_segment(surface, start, end, thickness):
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                               (start[0] + 1, start[1] + 1),
                               (end[0] + 1, end[1] + 1), thickness + 2)
        # Gold sleeve/gauntlet.
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                               start, end, thickness + 1)
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_dark"],
                               start, end, thickness)
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_mid"],
                               (start[0], start[1] - 1), (end[0], end[1] - 1),
                               max(1, thickness - 2))
        _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_light"],
                               (start[0], start[1] - 2), (end[0], end[1] - 2), 1)

    def _draw_bow(surface, hand_x, hand_y, draw_hand_x, draw_hand_y, facing, phase, draw_t):
        """Large ornate golden bow."""
        bow_glow = math.sin(phase * 1.5) * 0.3 + 0.7

        # Bow center (grip).
        grip_x = hand_x
        grip_y = hand_y

        # Bow curves up and down.
        bow_half_len = 20

        # Top tip.
        top_x = grip_x + facing * 4
        top_y = grip_y - bow_half_len
        # Bottom tip.
        bot_x = grip_x + facing * 4
        bot_y = grip_y + bow_half_len

        # Upper limb (curved).
        upper_curve_pts = []
        for i in range(6):
            t = i / 5
            # Bezier-like curve.
            cx = grip_x + facing * int(4 + math.sin(t * math.pi * 0.5) * 6)
            cy = int(grip_y - bow_half_len * t)
            upper_curve_pts.append((cx, cy))

        lower_curve_pts = []
        for i in range(6):
            t = i / 5
            cx = grip_x + facing * int(4 + math.sin(t * math.pi * 0.5) * 6)
            cy = int(grip_y + bow_half_len * t)
            lower_curve_pts.append((cx, cy))

        # Draw upper limb.
        for i in range(len(upper_curve_pts) - 1):
            thickness = max(2, 4 - i // 2)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                                   (upper_curve_pts[i][0] + 1, upper_curve_pts[i][1] + 1),
                                   (upper_curve_pts[i + 1][0] + 1, upper_curve_pts[i + 1][1] + 1),
                                   thickness + 1)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                                   upper_curve_pts[i], upper_curve_pts[i + 1], thickness)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_dark"],
                                   upper_curve_pts[i], upper_curve_pts[i + 1],
                                   max(1, thickness - 1))
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_mid"],
                                   (upper_curve_pts[i][0] - 1, upper_curve_pts[i][1]),
                                   (upper_curve_pts[i + 1][0] - 1, upper_curve_pts[i + 1][1]),
                                   max(1, thickness - 2))
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_light"],
                                   (upper_curve_pts[i][0] - 2, upper_curve_pts[i][1]),
                                   (upper_curve_pts[i + 1][0] - 2, upper_curve_pts[i + 1][1]),
                                   1)

        # Draw lower limb.
        for i in range(len(lower_curve_pts) - 1):
            thickness = max(2, 4 - i // 2)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                                   (lower_curve_pts[i][0] + 1, lower_curve_pts[i][1] + 1),
                                   (lower_curve_pts[i + 1][0] + 1, lower_curve_pts[i + 1][1] + 1),
                                   thickness + 1)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                                   lower_curve_pts[i], lower_curve_pts[i + 1], thickness)
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_dark"],
                                   lower_curve_pts[i], lower_curve_pts[i + 1],
                                   max(1, thickness - 1))
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_mid"],
                                   (lower_curve_pts[i][0] - 1, lower_curve_pts[i][1]),
                                   (lower_curve_pts[i + 1][0] - 1, lower_curve_pts[i + 1][1]),
                                   max(1, thickness - 2))
            _NS_aurethzar._aaline(surface, _NS_aurethzar.PALETTE["gold_light"],
                                   (lower_curve_pts[i][0] - 2, lower_curve_pts[i][1]),
                                   (lower_curve_pts[i + 1][0] - 2, lower_curve_pts[i + 1][1]),
                                   1)

        # Bow tips (pointed).
        top_tip = upper_curve_pts[-1]
        bot_tip = lower_curve_pts[-1]
        _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["gold_edge"], top_tip, 2)
        _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["gold_edge"], bot_tip, 2)
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_hot"],
                         (top_tip[0], top_tip[1], 1, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_hot"],
                         (bot_tip[0], bot_tip[1], 1, 1))

        # Glow along bow.
        for r in range(4, 0, -1):
            alpha = _NS_aurethzar._alpha(120 * (4 - r) / 4 * bow_glow)
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                     top_tip, r)
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                     bot_tip, r)

        # Bow center gem/crystal.
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["shadow_deep"],
                         (grip_x - 1, grip_y - 3, 3, 6))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["gold_darkest"],
                         (grip_x - 1, grip_y - 3, 3, 6))
        for r in range(4, 0, -1):
            alpha = _NS_aurethzar._alpha(150 * (4 - r) / 4 * bow_glow)
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                                     (grip_x, grip_y), r)
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"],
                         (grip_x, grip_y, 1, 1))

        # BOW STRING.
        # When drawn back, string goes from tips to draw hand (nocking point).
        if draw_t > 0.1:
            # String pulled back toward draw hand.
            nock_x = int(grip_x + (draw_hand_x - grip_x) * draw_t)
            nock_y = int(grip_y + (draw_hand_y - grip_y) * draw_t)

            # Top string.
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["cloth_light"],
                             top_tip, (nock_x, nock_y), 1)
            # Bottom string.
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["cloth_light"],
                             bot_tip, (nock_x, nock_y), 1)

            # Nocking point (arrow ready).
            if draw_t > 0.7:
                # Glowing arrow being nocked.
                arrow_len = 18
                arrow_end_x = nock_x + facing * arrow_len
                arrow_end_y = nock_y

                # Arrow shaft glow.
                for r in range(3, 0, -1):
                    alpha = _NS_aurethzar._alpha(180 * draw_t)
                    _NS_aurethzar._aaline(surface,
                                            (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                                            (nock_x, nock_y),
                                            (arrow_end_x, arrow_end_y), r)
                # Solid arrow shaft.
                pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_light"],
                                 (nock_x, nock_y),
                                 (arrow_end_x, arrow_end_y), 2)
                pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_shine"],
                                 (nock_x, nock_y),
                                 (arrow_end_x, arrow_end_y), 1)
                # Arrow tip.
                _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["solar_hot"],
                                         (arrow_end_x, arrow_end_y), 2)
                pygame.draw.rect(surface, _NS_aurethzar.PALETTE["white"],
                                 (arrow_end_x, arrow_end_y, 1, 1))
        else:
            # Relaxed string.
            pygame.draw.line(surface, _NS_aurethzar.PALETTE["cloth_light"],
                             top_tip, bot_tip, 1)

    # ============================================================
    # BASIC ATTACK ARROW
    # ============================================================
    def _draw_basic_arrow(surface, boss, x, y):
        """Golden arrow projectile after release."""
        progress = getattr(boss, "_aur_attack_progress", 0)
        if progress < 0.65:
            return
        facing = boss.direction
        tx, ty = _NS_aurethzar._target_position(boss, x, y)

        t = (progress - 0.65) / 0.35
        t = min(1.0, t)
        start_x = x + facing * 32
        start_y = y - 12
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Arrow trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_aurethzar._alpha(230 - i * 25)
            size = max(1, 5 - i)
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_darkest"], alpha),
                                     (px, py), size)
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                     (px, py), max(1, size - 2))

        # Arrow head.
        _NS_aurethzar._draw_arrow_shape(surface, bx, by, facing, size=6)

    def _draw_arrow_shape(surface, cx, cy, facing, size=6, color_hot=None):
        """Elongated arrow shape (like referensi)."""
        if color_hot is None:
            color_hot = _NS_aurethzar.PALETTE["solar_hot"]

        # Elongated shape (tip forward, tail feathers back).
        tip_x = cx + facing * size
        tail_x = cx - facing * size

        # Main body.
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["solar_darkest"], [
            (tip_x, cy),
            (cx, cy - size // 2),
            (tail_x, cy),
            (cx, cy + size // 2),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["solar_dark"], [
            (tip_x - facing, cy),
            (cx, cy - size // 3),
            (tail_x + facing, cy),
            (cx, cy + size // 3),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["solar_mid"], [
            (tip_x - facing * 2, cy),
            (cx, cy - size // 4),
            (tail_x + facing * 2, cy),
            (cx, cy + size // 4),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["solar_light"], [
            (tip_x - facing * 3, cy),
            (cx, cy),
            (tail_x + facing * 3, cy),
        ])
        # Bright tip.
        pygame.draw.rect(surface, color_hot, (tip_x - facing, cy, 1, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"],
                         (tip_x, cy, 1, 1))
        # Halo around arrow.
        for r in range(size + 2, 0, -1):
            alpha = _NS_aurethzar._alpha(100 * (size + 2 - r) / (size + 2))
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                     (cx, cy), r)

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_solar_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Golden particles floating around."""
        strength = 1.5 if intense else 1.0

        # Base glow cloud.
        cloud = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(35, 3, -3):
            alpha = _NS_aurethzar._alpha((35 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    cloud, (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_aurethzar._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    cloud, (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(cloud, (cx - 75, cy - 10))

        # Rising gold sparkles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, -32, 30)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 24)
            alpha = _NS_aurethzar._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_shine"], alpha),
                             (sx, sy - 1, 1, 1))

        # Feather-like particles falling.
        for i in range(6):
            fp_t = (phase * 0.4 + i * 0.17) % 1.0
            fx = cx - 20 + i * 8 + int(math.sin(phase * 1.5 + i) * 4)
            fy = cy - 5 + int(fp_t * 30)
            alpha = _NS_aurethzar._alpha(200 * (1 - fp_t) * strength)
            if alpha > 0:
                pygame.draw.line(surface, (*_NS_aurethzar.PALETTE["gold_light"], alpha),
                                 (fx, fy), (fx + 1, fy - 2), 1)
                pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["gold_edge"], alpha),
                                 (fx, fy, 1, 1))

        # Trail behind while moving.
        if trail:
            for i in range(7):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_aurethzar._alpha(170 - i * 22)
                if alpha <= 0:
                    continue
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                                         (sx, sy), max(2, 7 - i))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                                 (sx, sy - 1, 2, 2))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius, 140 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 4, 2, 180), (5, 8, 150, 16))
        pygame.draw.ellipse(shadow, (60, 40, 15, 120), (14, 10, 132, 12))
        surface.blit(shadow, (x - 80, y - 15))

    def _draw_solar_aura(surface, x, y, phase):
        """LARGE solar aura for TRUE BOSS."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        # Outer glow.
        for radius in range(115, 5, -5):
            alpha = _NS_aurethzar._alpha((115 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_aurethzar._aacircle(aura,
                                         (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                                         (130, 110), radius)
        for radius in range(75, 5, -4):
            alpha = _NS_aurethzar._alpha((75 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_aurethzar._aacircle(aura,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (130, 110), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_aurethzar._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_aurethzar._aacircle(aura,
                                         (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                         (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))

        # Rotating solar rays (godlike aura).
        num_rays = 12
        for i in range(num_rays):
            angle = phase * 0.2 + i * math.pi * 2 / num_rays
            ray_r_start = 55
            ray_r_end = 75 + int(math.sin(phase * 1.5 + i) * 8)
            sx = x + int(math.cos(angle) * ray_r_start)
            sy = y + int(math.sin(angle) * ray_r_start * 0.5)
            ex = x + int(math.cos(angle) * ray_r_end)
            ey = y + int(math.sin(angle) * ray_r_end * 0.5)
            alpha_ray = _NS_aurethzar._alpha(140 * pulse)
            pygame.draw.line(surface, (*_NS_aurethzar.PALETTE["solar_light"], alpha_ray),
                             (sx, sy), (ex, ey), 2)
            pygame.draw.line(surface, (*_NS_aurethzar.PALETTE["solar_hot"], alpha_ray),
                             (sx, sy), (ex, ey), 1)

        # Floating gold particles.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 48 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_aurethzar.PALETTE["solar_dark"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_aurethzar.PALETTE["solar_darkest"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_aurethzar.PALETTE["gold_dark"], 230),
                            (25, 24, 140, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_aurethzar.PALETTE["gold_mid"], 180),
                            (45, 26, 100, 18), 1)

        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 35 + int(math.sin(angle) * 10)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_aurethzar.PALETTE["solar_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_aurethzar.PALETTE["solar_hot"],
                                        _NS_aurethzar._alpha(180 * pulse)),
                                (15, 14, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))

    # ============================================================
    # SKILL Q — MARKSMAN (enhanced arrow, longer range)
    # ============================================================
    def _draw_marksman_skill(surface, boss, x, y, timer, phase):
        """Multiple arrows fired with enhanced range."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_aurethzar._target_position(boss, x, y)

        if progress < 0.3:
            # Charge bow with glowing energy.
            t = progress / 0.3
            hand_x = x + facing * 24
            hand_y = y - 12
            cr = int(6 + t * 10)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_aurethzar._alpha(200 * (cr + 8 - r) / (cr + 8))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                                         (hand_x, hand_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_aurethzar._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (hand_x, hand_y), r)
            _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["solar_light"],
                                     (hand_x, hand_y), cr - 2)
            _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["solar_shine"],
                                     (hand_x, hand_y), max(1, cr - 4))
        else:
            # Fire 3 arrows in slight spread.
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 32
            start_y = y - 12

            for arrow_i, spread in enumerate((-0.1, 0, 0.1)):
                bx = int(start_x + (tx - start_x) * t)
                by = int(start_y + (ty - start_y) * t + spread * 50 * t)

                # Long comet trail.
                for i in range(10):
                    trail_t = max(0.0, t - i * 0.04)
                    px = int(start_x + (tx - start_x) * trail_t)
                    py = int(start_y + (ty - start_y) * trail_t + spread * 50 * trail_t)
                    alpha = _NS_aurethzar._alpha(230 - i * 22)
                    size = max(1, 6 - i)
                    _NS_aurethzar._aacircle(surface,
                                             (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                                             (px, py), size)
                    _NS_aurethzar._aacircle(surface,
                                             (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                             (px, py), max(1, size - 1))
                    _NS_aurethzar._aacircle(surface,
                                             (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                             (px, py), max(1, size - 2))

                _NS_aurethzar._draw_arrow_shape(surface, bx, by, facing, size=7)

            # Impact burst.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(15 + st * 25)
                alpha = _NS_aurethzar._alpha(240 * (1 - st))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_darkest"], alpha),
                                         (tx, ty), radius + 3, 3)
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (tx, ty), radius, 2)
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                                     (ex, ey, 3, 3))

    # ============================================================
    # SKILL W — PIERCING ARROW (long straight line)
    # ============================================================
    def _draw_piercing_arrow(surface, boss, x, y, timer, phase):
        """Massive piercing beam-arrow through line."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        start_x = x + facing * 32
        start_y = y - 12
        # Very long range.
        end_x = start_x + facing * 500
        end_y = start_y

        if progress < 0.3:
            # Wind-up: bow charges.
            t = progress / 0.3
            for r in range(int(10 + t * 8), 0, -1):
                alpha = _NS_aurethzar._alpha(200 * t)
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (start_x, start_y), r)
            _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["solar_shine"],
                                     (start_x, start_y), int(4 + t * 4))
        elif progress < 0.7:
            # BEAM SHOT.
            t = (progress - 0.3) / 0.4
            intensity = math.sin(t * math.pi)

            # Beam extends.
            beam_end_x = int(start_x + (end_x - start_x) * min(1.0, t * 2))
            beam_end_y = start_y

            # Multi-layer beam.
            for layer_i, (width, alpha_val) in enumerate([
                (16, 100), (12, 140), (8, 180), (4, 220), (2, 255),
            ]):
                actual_alpha = _NS_aurethzar._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_aurethzar.PALETTE["solar_darkest"],
                    _NS_aurethzar.PALETTE["solar_dark"],
                    _NS_aurethzar.PALETTE["solar_mid"],
                    _NS_aurethzar.PALETTE["solar_light"],
                    _NS_aurethzar.PALETTE["solar_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y),
                                 (beam_end_x, beam_end_y), width)

            # Arrow tip.
            _NS_aurethzar._draw_arrow_shape(surface, beam_end_x, beam_end_y,
                                              facing, size=10)

            # Sparks along beam.
            for i in range(20):
                spark_t = (phase * 3 + i * 0.05) % 1.0
                spark_x = int(start_x + (beam_end_x - start_x) * spark_t)
                spark_y = start_y + int(math.sin(phase * 5 + i) * 4)
                alpha = _NS_aurethzar._alpha(240 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_aurethzar.PALETTE["solar_shine"], alpha),
                                 (spark_x, spark_y, 1, 1))
        else:
            # Aftermath: lingering light.
            t = (progress - 0.7) / 0.3
            alpha = _NS_aurethzar._alpha(150 * (1 - t))
            pygame.draw.line(surface, (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                             (start_x, start_y), (end_x, end_y), 2)
            pygame.draw.line(surface, (*_NS_aurethzar.PALETTE["solar_shine"], alpha),
                             (start_x, start_y), (end_x, end_y), 1)

    # ============================================================
    # SKILL E — FROST SHOT (ice arrow)
    # ============================================================
    def _draw_frost_shot(surface, boss, x, y, timer, phase):
        """Ice-blue arrow with frost effect."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_aurethzar._target_position(boss, x, y)

        if progress < 0.25:
            # Charge frost energy.
            t = progress / 0.25
            hand_x = x + facing * 24
            hand_y = y - 12
            cr = int(5 + t * 8)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_aurethzar._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_dark"], alpha),
                                         (hand_x, hand_y), r)
            _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["ice_mid"],
                                     (hand_x, hand_y), cr - 2)
            _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["ice_light"],
                                     (hand_x, hand_y), max(1, cr - 4))
            # Ice crystals forming.
            for i in range(6):
                angle = phase * 3 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_aurethzar.PALETTE["ice_shine"],
                                 (sx, sy, 1, 1))
        else:
            # Fire ice arrow.
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 32
            start_y = y - 12
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Ice trail (blue).
            for i in range(10):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_aurethzar._alpha(230 - i * 22)
                size = max(1, 7 - i)
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_dark"], alpha),
                                         (px, py), size)
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_mid"], alpha),
                                         (px, py), max(1, size - 1))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_light"], alpha),
                                         (px, py), max(1, size - 2))

                # Ice crystals sparkle around trail.
                if i < 4:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_aurethzar.PALETTE["ice_shine"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Frost arrow head.
            _NS_aurethzar._draw_frost_arrow(surface, bx, by, facing)

            # Impact freeze burst.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(20 + st * 30)
                alpha = _NS_aurethzar._alpha(240 * (1 - st))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_dark"], alpha),
                                         (tx, ty), radius + 3, 3)
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_mid"], alpha),
                                         (tx, ty), radius, 2)
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["ice_light"], alpha),
                                         (tx, ty), max(1, radius - 5), 1)

                # Radiating ice spikes.
                for i in range(12):
                    angle_s = i * math.pi / 6
                    spike_len = int(radius * 0.8)
                    ex = tx + int(math.cos(angle_s) * spike_len)
                    ey = ty + int(math.sin(angle_s) * spike_len * 0.8)
                    pygame.draw.line(surface,
                                     (*_NS_aurethzar.PALETTE["ice_mid"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.line(surface,
                                     (*_NS_aurethzar.PALETTE["ice_shine"], alpha),
                                     (tx, ty), (ex, ey), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_aurethzar.PALETTE["ice_shine"], alpha),
                                     (ex, ey, 2, 2))

    def _draw_frost_arrow(surface, cx, cy, facing):
        """Ice arrow shape."""
        size = 7
        tip_x = cx + facing * size
        tail_x = cx - facing * size

        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["ice_dark"], [
            (tip_x, cy),
            (cx, cy - size // 2),
            (tail_x, cy),
            (cx, cy + size // 2),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["ice_mid"], [
            (tip_x - facing, cy),
            (cx, cy - size // 3),
            (tail_x + facing, cy),
            (cx, cy + size // 3),
        ])
        _NS_aurethzar._poly(surface, _NS_aurethzar.PALETTE["ice_light"], [
            (tip_x - facing * 2, cy),
            (cx, cy - size // 4),
            (tail_x + facing * 2, cy),
            (cx, cy + size // 4),
        ])
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["ice_shine"],
                         (tip_x, cy, 1, 1))
        pygame.draw.rect(surface, _NS_aurethzar.PALETTE["white"],
                         (tip_x - facing, cy, 1, 1))

        # Halo.
        for r in range(size + 3, 0, -1):
            alpha = _NS_aurethzar._alpha(100 * (size + 3 - r) / (size + 3))
            _NS_aurethzar._aacircle(surface,
                                     (*_NS_aurethzar.PALETTE["ice_mid"], alpha),
                                     (cx, cy), r)

    # ============================================================
    # SKILL R — DISTANT THUNDER (arrow rain from sky)
    # ============================================================
    def _draw_thunder_ground(surface, boss, x, y, timer, phase):
        """Target circle marker."""
        tx, ty = _NS_aurethzar._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Growing target circle.
        r = 50
        alpha = _NS_aurethzar._alpha(200)
        pygame.draw.ellipse(surface, (*_NS_aurethzar.PALETTE["solar_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                            (tx - r + 8, ty - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 1)

        # Rotating rune runes on ground.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_light"],
                             (sx, sy, 3, 3))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"],
                             (sx, sy, 1, 1))

    def _draw_distant_thunder(surface, boss, x, y, timer, phase):
        """Multiple arrows falling from sky."""
        tx, ty = _NS_aurethzar._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            # Wind-up: aim to sky, charge energy.
            t = progress / 0.25
            # Bright energy building at boss.
            for r in range(int(15 + t * 10), 0, -2):
                alpha = _NS_aurethzar._alpha(180 * t * (15 + t * 10 - r) / (15 + t * 10))
                _NS_aurethzar._aacircle(surface,
                                         (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                         (x, y - 20), r)
        elif progress < 0.85:
            # Arrow rain phase.
            t = (progress - 0.25) / 0.6

            # 6-8 arrows falling in sequence.
            num_arrows = 8
            for i in range(num_arrows):
                # Each arrow has offset launch time.
                arrow_t = (t * num_arrows - i)
                if arrow_t < 0 or arrow_t > 1.5:
                    continue

                # Slight positional offset.
                offset_x = int(math.sin(i * 1.7) * 40)
                offset_y = int(math.cos(i * 1.3) * 15)
                target_x = tx + offset_x
                target_y = ty + offset_y

                # Falling arrow (from top of screen).
                fall_t = min(1.0, arrow_t / 0.5)
                sky_y = target_y - 250
                arrow_x = target_x
                arrow_y = int(sky_y + (target_y - sky_y) * fall_t)

                if fall_t < 1.0:
                    # Draw falling arrow with vertical trail.
                    for trail_i in range(12):
                        trail_offset = trail_i * 15
                        ty_trail = arrow_y - trail_offset
                        if ty_trail < sky_y:
                            continue
                        alpha = _NS_aurethzar._alpha(230 - trail_i * 18)
                        size = max(1, 5 - trail_i // 2)
                        _NS_aurethzar._aacircle(surface,
                                                 (*_NS_aurethzar.PALETTE["solar_dark"], alpha),
                                                 (arrow_x, ty_trail), size)
                        _NS_aurethzar._aacircle(surface,
                                                 (*_NS_aurethzar.PALETTE["solar_mid"], alpha),
                                                 (arrow_x, ty_trail), max(1, size - 1))
                        _NS_aurethzar._aacircle(surface,
                                                 (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                                 (arrow_x, ty_trail), max(1, size - 2))

                    # Arrow head (vertical/downward).
                    pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_darkest"],
                                     (arrow_x, arrow_y - 10), (arrow_x, arrow_y + 4), 4)
                    pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_mid"],
                                     (arrow_x, arrow_y - 10), (arrow_x, arrow_y + 4), 3)
                    pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_light"],
                                     (arrow_x, arrow_y - 10), (arrow_x, arrow_y + 4), 2)
                    pygame.draw.line(surface, _NS_aurethzar.PALETTE["solar_shine"],
                                     (arrow_x, arrow_y - 10), (arrow_x, arrow_y + 4), 1)
                    # Bright tip.
                    _NS_aurethzar._aacircle(surface, _NS_aurethzar.PALETTE["solar_hot"],
                                             (arrow_x, arrow_y + 4), 2)
                    pygame.draw.rect(surface, _NS_aurethzar.PALETTE["white"],
                                     (arrow_x, arrow_y + 4, 1, 1))
                else:
                    # Impact burst (arrow landed).
                    impact_t = min(1.0, (arrow_t - 0.5) / 0.5)
                    if impact_t < 1.0:
                        # Big impact for last arrow (arrow index high).
                        is_last = (i == num_arrows - 1)
                        impact_r = int(15 + impact_t * (35 if is_last else 20))
                        alpha_i = _NS_aurethzar._alpha(240 * (1 - impact_t))
                        color_center = _NS_aurethzar.PALETTE["solar_hot"] if is_last \
                            else _NS_aurethzar.PALETTE["solar_light"]
                        _NS_aurethzar._aacircle(surface,
                                                 (*_NS_aurethzar.PALETTE["solar_darkest"], alpha_i),
                                                 (target_x, target_y), impact_r + 3, 3)
                        _NS_aurethzar._aacircle(surface,
                                                 (*_NS_aurethzar.PALETTE["solar_dark"], alpha_i),
                                                 (target_x, target_y), impact_r, 3)
                        _NS_aurethzar._aacircle(surface,
                                                 (*_NS_aurethzar.PALETTE["solar_mid"], alpha_i),
                                                 (target_x, target_y), max(1, impact_r - 5), 2)
                        _NS_aurethzar._aacircle(surface,
                                                 (*color_center, alpha_i),
                                                 (target_x, target_y), max(1, impact_r - 10), 1)

                        # Impact rays.
                        num_rays = 12 if is_last else 8
                        for r_i in range(num_rays):
                            angle_s = r_i * math.pi * 2 / num_rays
                            ex = target_x + int(math.cos(angle_s) * impact_r)
                            ey = target_y + int(math.sin(angle_s) * impact_r * 0.7)
                            pygame.draw.line(surface, (*color_center, alpha_i),
                                             (target_x, target_y), (ex, ey), 2)
                            pygame.draw.rect(surface, _NS_aurethzar.PALETTE["solar_shine"],
                                             (ex, ey, 2, 2))
        else:
            # Aftermath: golden dust rising.
            t = (progress - 0.85) / 0.15
            for i in range(20):
                rise_t = (phase * 0.8 + i * 0.05) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - int(rise_t * 40)
                alpha = _NS_aurethzar._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_light"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_aurethzar.PALETTE["solar_hot"], alpha),
                                     (rx, ry, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_krognarr(surface, boss, x, y):
    """Entry point krognarr."""
    return _NS_krognarr.draw_krognarr(surface, boss, x, y)


def draw_raz(surface, boss, x, y):
    """Entry point raz."""
    return _NS_raz.draw_raz(surface, boss, x, y)


def draw_vraskhan(surface, boss, x, y):
    """Entry point vraskhan."""
    return _NS_vraskhan.draw_vraskhan(surface, boss, x, y)


def draw_aurethzar(surface, boss, x, y):
    """Entry point aurethzar."""
    return _NS_aurethzar.draw_aurethzar(surface, boss, x, y)
