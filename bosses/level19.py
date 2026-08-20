"""
bosses/level19.py - Semua boss Level 19

Berisi:
  - akahime      (mini boss - RANGED scarlet blossom kunoichi)
  - nyxthrael    (mini boss - MELEE cursed executioner)
  - sylvantheros (mini boss - RANGED verdant farseer)
  - vaelindra    (TRUE BOSS - Violet Sovereign, RANGED)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _aka_ (akahime)      di-rename -> _akm_ (bentrok dengan level7)
  - _nyx_ (nyxthrael)    di-rename -> _nxt_ (bentrok dengan level7/11)
  - _vae_ (vaelindra)    di-rename -> _vai_ (bentrok dengan level8)
  - _syl_ (sylvantheros) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# akahime.py
# ====================================================================

# ====================================================================
# AKAHIME - The Scarlet Blossom (Mini Boss - Kunoichi Marksman)
# ====================================================================


class _NS_akahime:
    """Namespace akahime - Ninja marksman mini boss with scarlet flower theme."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (light warm)
        "skin_dark": (140, 90, 80),
        "skin_mid": (220, 175, 155),
        "skin_light": (250, 215, 195),
        "skin_shine": (255, 235, 220),

        # Hair (jet black with dark purple highlight)
        "hair_darkest": (10, 8, 15),
        "hair_dark": (25, 20, 35),
        "hair_mid": (55, 40, 65),
        "hair_light": (95, 70, 110),
        "hair_shine": (155, 115, 165),

        # Outfit black leather (main body)
        "outfit_darkest": (10, 8, 12),
        "outfit_dark": (30, 22, 32),
        "outfit_mid": (65, 50, 70),
        "outfit_light": (110, 90, 115),
        "outfit_shine": (170, 145, 175),

        # Scarlet red (bows, ribbons, accents)
        "scarlet_darkest": (40, 5, 15),
        "scarlet_dark": (110, 15, 40),
        "scarlet_mid": (200, 35, 75),
        "scarlet_light": (250, 90, 130),
        "scarlet_hot": (255, 160, 195),
        "scarlet_shine": (255, 220, 235),

        # Pink petals / magic (flower petals, shuriken glow)
        "petal_darkest": (60, 10, 40),
        "petal_dark": (140, 25, 90),
        "petal_mid": (230, 60, 145),
        "petal_light": (255, 130, 200),
        "petal_hot": (255, 190, 230),
        "petal_shine": (255, 230, 245),

        # Shuriken metal
        "metal_darkest": (15, 12, 20),
        "metal_dark": (45, 40, 55),
        "metal_mid": (100, 90, 115),
        "metal_light": (180, 170, 200),
        "metal_shine": (240, 230, 250),

        # Eyes (violet-purple)
        "eye_dark": (40, 15, 60),
        "eye_mid": (140, 60, 180),
        "eye_light": (220, 180, 240),
        "eye_glow": (250, 220, 255),

        # Shadow ninjutsu (deep purple - E skill)
        "shadow_darkest": (15, 5, 25),
        "shadow_dark": (45, 20, 75),
        "shadow_mid": (100, 50, 150),
        "shadow_light": (170, 110, 210),

        # Mist
        "mist_dark": (35, 10, 40),
        "mist_mid": (100, 30, 90),
        "mist_light": (200, 100, 180),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_akahime._clamp(color)
        if _NS_akahime.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_akahime._clamp(color)
        if _NS_akahime.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_akahime._clamp(color), points)

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
    def draw_akahime(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_akahime._detect_moving(boss)
        _NS_akahime._update_aka_attack_anim(boss)
        attacking = (
            getattr(boss, "_akm_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_akahime._draw_petal_aura(surface, x, y, pulse)
        _NS_akahime._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "r":
            _NS_akahime._draw_higanbana_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_akahime._draw_shadow_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_akahime._draw_aka_attack(surface, boss, x, y)
        elif moving:
            _NS_akahime._draw_aka_float_move(surface, boss, x, y)
        else:
            _NS_akahime._draw_aka_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_akahime._draw_petal_barrage(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_akahime._draw_soul_scroll(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_akahime._draw_shadow_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akahime._draw_higanbana_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_aka_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_akm_previous_timer", 0))
        active = bool(getattr(boss, "_akm_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._akm_attack_active = True
            boss._akm_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._akm_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._akm_attack_frame = int(
                getattr(boss, "_akm_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._akm_attack_active = False
            boss._akm_attack_frame = 0
            active = False

        boss._akm_previous_timer = timer
        boss._akm_attack_progress = (
            min(1.0, getattr(boss, "_akm_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_akm_last_x"):
            boss._akm_last_x = boss.x
            boss._akm_last_y = boss.y
            return False
        dx = abs(boss.x - boss._akm_last_x)
        dy = abs(boss.y - boss._akm_last_y)
        boss._akm_last_x = boss.x
        boss._akm_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING)
    # ============================================================
    def _draw_aka_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.6) * 4)
        _NS_akahime._draw_shadow(surface, x, y + 52)
        _NS_akahime._draw_petal_particles(surface, x, y + 40, boss.pulse)
        _NS_akahime._draw_aka_body(surface, x, y - 4 + float_bob,
                                   boss.direction, boss.pulse, "idle", 0)

    def _draw_aka_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_akahime._draw_shadow(surface, x + sway, y + 52)
        _NS_akahime._draw_petal_particles(surface, x + sway, y + 40, phase,
                                          trail=True, facing=boss.direction)
        _NS_akahime._draw_aka_body(surface, x + sway, y - 6 + float_bob,
                                   boss.direction, phase, "move", 0)

    def _draw_aka_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_akm_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_akm_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Ranged: draw back → throw → recovery
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 3) * facing
            lift = int(t * 2)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-3 + t * 8)) * facing
            lift = int(2 - t * 3)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(5 * (1 - t)) * facing
            lift = int(-1 + t * 1)

        float_bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_akahime._draw_shadow(surface, x + lunge, y + 52)
        _NS_akahime._draw_petal_particles(surface, x + lunge, y + 40, boss.pulse,
                                          intense=True)
        _NS_akahime._draw_aka_body(surface, x + lunge, y - 4 - lift + float_bob,
                                   facing, boss.pulse, "attack", progress)
        _NS_akahime._draw_shuriken_projectile(surface, boss, x + lunge,
                                              y - 4 - lift + float_bob, progress)

    # ============================================================
    # BODY (Kunoichi with long ponytail, throwing shuriken)
    # ============================================================
    def _draw_aka_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw kunoichi body."""
        # Cape/sash behind (flowing scarlet).
        _NS_akahime._draw_scarlet_sash(surface, cx, cy, facing, phase)

        # Long hair (flowing behind).
        _NS_akahime._draw_ponytail(surface, cx, cy - 14, facing, phase)

        # Trailing skirt/cloth below (no legs).
        _NS_akahime._draw_lower_cloth(surface, cx, cy + 8, facing, phase)

        # Torso.
        _NS_akahime._draw_aka_torso(surface, cx, cy, facing, phase)

        # Back arm (hidden or holding scroll).
        _NS_akahime._draw_aka_arm_back(surface, cx, cy + 2, facing, phase, action,
                                       attack_progress)

        # Head + face.
        _NS_akahime._draw_aka_head(surface, cx, cy - 14, facing, phase)

        # Front arm (throwing shuriken).
        _NS_akahime._draw_aka_arm_front(surface, cx, cy + 2, facing, phase, action,
                                        attack_progress)

    def _draw_scarlet_sash(surface, cx, cy, facing, phase):
        """Flowing scarlet cape/sash behind."""
        sway = math.sin(phase * 0.5) * 3
        back_dir = -facing

        # Main sash silhouette (long flowing).
        sash_points = [
            (cx + back_dir * 4, cy - 6),
            (cx + back_dir * 8, cy - 2),
            (cx + back_dir * 12, cy + 4),
            (cx + back_dir * 14 + int(sway), cy + 10),
            (cx + back_dir * 12 + int(sway * 1.5), cy + 16),
            (cx + back_dir * 8 + int(sway), cy + 20),
            (cx + back_dir * 4, cy + 18),
            (cx + back_dir * 2, cy + 12),
            (cx, cy + 4),
        ]
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in sash_points])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_darkest"], sash_points)

        # Layered scarlet.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_dark"], [
            (cx + back_dir * 4, cy - 5),
            (cx + back_dir * 7, cy - 1),
            (cx + back_dir * 11, cy + 4),
            (cx + back_dir * 12 + int(sway), cy + 9),
            (cx + back_dir * 10 + int(sway), cy + 15),
            (cx + back_dir * 6, cy + 18),
            (cx + back_dir * 3, cy + 15),
            (cx + back_dir * 1, cy + 8),
            (cx, cy + 3),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
            (cx + back_dir * 5, cy - 3),
            (cx + back_dir * 8, cy + 2),
            (cx + back_dir * 10, cy + 8),
            (cx + back_dir * 8 + int(sway), cy + 14),
            (cx + back_dir * 5, cy + 15),
            (cx + back_dir * 3, cy + 10),
            (cx + back_dir * 1, cy + 4),
        ])

        # Bright highlight edge.
        pygame.draw.line(surface, _NS_akahime.PALETTE["scarlet_light"],
                        (cx + back_dir * 4, cy - 4),
                        (cx + back_dir * 8, cy + 1), 1)

        # Torn tatter edges at bottom.
        for i, (tx_off, ty_off) in enumerate([(-8, 20), (-4, 22), (0, 21)]):
            tx = cx + back_dir * tx_off
            ty = cy + ty_off + int(sway)
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_dark"], [
                (tx, ty - 2),
                (tx + 2, ty),
                (tx, ty + 3),
                (tx - 2, ty),
            ])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
                (tx, ty - 1),
                (tx + 1, ty),
                (tx, ty + 2),
                (tx - 1, ty),
            ])
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_light"], (tx, ty, 1, 1))

    def _draw_ponytail(surface, cx, cy, facing, phase):
        """Long flowing black ponytail behind head."""
        sway = math.sin(phase * 0.7) * 3
        back_dir = -facing

        # Ponytail base at back of head.
        base_x = cx + back_dir * 2
        base_y = cy - 2

        # Segmented ponytail.
        prev_x, prev_y = base_x, base_y
        segments = 8
        for i in range(1, segments + 1):
            t = i / segments
            # Curves back and down.
            wave = math.sin(phase * 0.8 + t * math.pi) * (3 + t * 2)
            seg_x = base_x + back_dir * int(t * 8 + wave * 0.3)
            seg_y = base_y + int(t * 18 + wave)
            thickness = max(2, 8 - i)

            # Shadow.
            _NS_akahime._aaline(surface, _NS_akahime.PALETTE["shadow_deep"],
                               (prev_x + 1, prev_y + 1), (seg_x + 1, seg_y + 1),
                               thickness + 1)
            # Hair layers.
            _NS_akahime._aaline(surface, _NS_akahime.PALETTE["hair_darkest"],
                               (prev_x, prev_y), (seg_x, seg_y), thickness)
            _NS_akahime._aaline(surface, _NS_akahime.PALETTE["hair_dark"],
                               (prev_x, prev_y), (seg_x, seg_y), max(1, thickness - 2))
            _NS_akahime._aaline(surface, _NS_akahime.PALETTE["hair_mid"],
                               (prev_x, prev_y - 1), (seg_x, seg_y - 1),
                               max(1, thickness - 4))
            # Purple highlight.
            if i < 5:
                _NS_akahime._aaline(surface, _NS_akahime.PALETTE["hair_light"],
                                   (prev_x, prev_y - 2), (seg_x, seg_y - 2),
                                   max(1, thickness - 6))
            prev_x, prev_y = seg_x, seg_y

        # Hair strand tips.
        for i in range(3):
            tip_sway = math.sin(phase * 1.2 + i) * 2
            tip_x = prev_x + int(tip_sway)
            tip_y = prev_y + i
            pygame.draw.rect(surface, _NS_akahime.PALETTE["hair_dark"], (tip_x, tip_y, 1, 2))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["hair_light"], (tip_x, tip_y, 1, 1))

        # Red ribbon bow at base of ponytail.
        rx = cx + back_dir * 3
        ry = cy - 3
        # Bow loops.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_darkest"], [
            (rx - 2, ry - 1),
            (rx - 4, ry - 3),
            (rx - 4, ry + 1),
            (rx - 1, ry),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_darkest"], [
            (rx + 2, ry - 1),
            (rx + 4, ry - 3),
            (rx + 4, ry + 1),
            (rx + 1, ry),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
            (rx - 2, ry - 1),
            (rx - 3, ry - 2),
            (rx - 3, ry + 1),
            (rx - 1, ry),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
            (rx + 2, ry - 1),
            (rx + 3, ry - 2),
            (rx + 3, ry + 1),
            (rx + 1, ry),
        ])
        # Center knot.
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_darkest"], (rx - 1, ry - 1, 3, 3))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_mid"], (rx, ry - 1, 2, 2))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_light"], (rx, ry, 1, 1))

    def _draw_lower_cloth(surface, cx, cy, facing, phase):
        """Skirt/cloth flowing below (no legs shown - floating)."""
        sway = math.sin(phase * 0.5) * 2

        # Main skirt shape.
        skirt_shape = [
            (cx - 10, cy - 6),
            (cx - 12, cy - 2),
            (cx - 11, cy + 4),
            (cx - 8, cy + 12 + int(sway)),
            (cx - 3, cy + 16),
            (cx + 3, cy + 16 - int(sway)),
            (cx + 8, cy + 12),
            (cx + 11, cy + 4),
            (cx + 12, cy - 2),
            (cx + 10, cy - 6),
        ]
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in skirt_shape])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["outfit_darkest"], skirt_shape)

        # Layered outfit.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["outfit_dark"], [
            (cx - 9, cy - 5),
            (cx - 11, cy - 1),
            (cx - 9, cy + 5),
            (cx - 5, cy + 12),
            (cx + 5, cy + 11),
            (cx + 9, cy + 5),
            (cx + 11, cy - 1),
            (cx + 9, cy - 5),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["outfit_mid"], [
            (cx - 7, cy - 3),
            (cx - 9, cy + 1),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 9, cy + 1),
            (cx + 7, cy - 3),
        ])

        # Scarlet belt/obi (waist wrap).
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                        (cx - 11, cy - 7, 22, 4))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_dark"],
                        (cx - 11, cy - 6, 22, 3))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_mid"],
                        (cx - 11, cy - 5, 22, 1))
        # Belt highlight.
        pygame.draw.line(surface, _NS_akahime.PALETTE["scarlet_light"],
                        (cx - 8, cy - 5), (cx + 8, cy - 5), 1)

        # Big front bow (obi bow).
        bow_x = cx
        bow_y = cy - 5
        # Bow loops.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_darkest"], [
            (bow_x - 2, bow_y),
            (bow_x - 6, bow_y - 3),
            (bow_x - 6, bow_y + 3),
            (bow_x - 1, bow_y),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_darkest"], [
            (bow_x + 2, bow_y),
            (bow_x + 6, bow_y - 3),
            (bow_x + 6, bow_y + 3),
            (bow_x + 1, bow_y),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_dark"], [
            (bow_x - 2, bow_y),
            (bow_x - 5, bow_y - 2),
            (bow_x - 5, bow_y + 2),
            (bow_x - 1, bow_y),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_dark"], [
            (bow_x + 2, bow_y),
            (bow_x + 5, bow_y - 2),
            (bow_x + 5, bow_y + 2),
            (bow_x + 1, bow_y),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
            (bow_x - 2, bow_y),
            (bow_x - 4, bow_y - 1),
            (bow_x - 4, bow_y + 1),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
            (bow_x + 2, bow_y),
            (bow_x + 4, bow_y - 1),
            (bow_x + 4, bow_y + 1),
        ])
        # Center knot.
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                        (bow_x - 2, bow_y - 2, 4, 4))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_mid"],
                        (bow_x - 1, bow_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_light"],
                        (bow_x, bow_y - 1, 1, 1))

        # Trailing ribbon tails from bow.
        for side_off in [-1, 1]:
            tail_sway = math.sin(phase * 0.7 + side_off) * 2
            pygame.draw.line(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                            (bow_x + side_off, bow_y + 2),
                            (bow_x + side_off * 2 + int(tail_sway), bow_y + 10), 2)
            pygame.draw.line(surface, _NS_akahime.PALETTE["scarlet_mid"],
                            (bow_x + side_off, bow_y + 2),
                            (bow_x + side_off * 2 + int(tail_sway), bow_y + 10), 1)
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_light"],
                            (bow_x + side_off * 2 + int(tail_sway), bow_y + 9, 1, 1))

        # Small flower petals falling from skirt.
        for i in range(4):
            pt = (phase * 0.5 + i * 0.25) % 1.0
            px = cx - 6 + i * 4 + int(math.sin(phase + i) * 2)
            py = cy + 4 + int(pt * 10)
            alpha = _NS_akahime._alpha(200 * (1 - pt))
            if alpha > 0:
                _NS_akahime._poly(surface, (*_NS_akahime.PALETTE["petal_dark"], alpha), [
                    (px, py - 1),
                    (px + 1, py),
                    (px, py + 1),
                    (px - 1, py),
                ])
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                (px, py, 1, 1))

    def _draw_aka_torso(surface, cx, cy, facing, phase):
        """Slim ninja torso."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape (feminine, narrow waist).
        torso_shape = [
            (cx - 8, cy - 6),
            (cx - 10, cy - 3),
            (cx - 9, cy + 3),
            (cx - 7, cy + 7),
            (cx + 7, cy + 7),
            (cx + 9, cy + 3),
            (cx + 10, cy - 3),
            (cx + 8, cy - 6),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in torso_shape])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["outfit_darkest"], torso_shape)

        # Leather outfit layers.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["outfit_dark"], [
            (cx - 7, cy - 5),
            (cx - 9, cy - 2),
            (cx - 8, cy + 2),
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 8, cy + 2),
            (cx + 9, cy - 2),
            (cx + 7, cy - 5),
            (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["outfit_mid"], [
            (cx - 5, cy - 4),
            (cx - 7, cy - 1),
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 7, cy - 1),
            (cx + 5, cy - 4),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])

        # Scarlet collar/neckline (V shape).
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_dark"], [
            (cx - 4, cy - 7),
            (cx, cy - 3),
            (cx + 4, cy - 7),
            (cx + 3, cy - 8),
            (cx - 3, cy - 8),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["scarlet_mid"], [
            (cx - 3, cy - 7),
            (cx, cy - 4),
            (cx + 3, cy - 7),
        ])
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_light"], (cx, cy - 5, 1, 1))

        # Chest/neck exposed skin.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["skin_dark"], [
            (cx - 2, cy - 6),
            (cx - 3, cy - 4),
            (cx, cy - 2),
            (cx + 3, cy - 4),
            (cx + 2, cy - 6),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["skin_mid"], [
            (cx - 1, cy - 5),
            (cx - 2, cy - 4),
            (cx, cy - 3),
            (cx + 2, cy - 4),
            (cx + 1, cy - 5),
        ])

        # Petal decoration on shoulder.
        pt_x = cx - 6 * facing
        pt_y = cy - 5
        _NS_akahime._draw_flower_petal(surface, pt_x, pt_y, 3, phase)

    def _draw_flower_petal(surface, cx, cy, size, phase):
        """Small scarlet flower ornament."""
        # 5-petal flower.
        for i in range(5):
            angle = i * math.pi * 2 / 5 - math.pi / 2
            px = cx + int(math.cos(angle) * size)
            py = cy + int(math.sin(angle) * size)
            _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                                 (px, py), 2)
            _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["scarlet_dark"],
                                 (px, py), 1)
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_mid"], (px, py, 1, 1))
        # Center.
        pygame.draw.rect(surface, _NS_akahime.PALETTE["petal_hot"], (cx, cy, 1, 1))

    def _draw_aka_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (with wrist wrap)."""
        sway = math.sin(phase * 0.4) * 1
        back_dir = -facing
        shoulder_x = cx + back_dir * 8
        shoulder_y = cy - 3
        elbow_x = shoulder_x + back_dir * 3
        elbow_y = shoulder_y + 4 + int(sway)
        hand_x = elbow_x + back_dir * 2
        hand_y = elbow_y + 4 + int(sway)

        # Shadow.
        pygame.draw.line(surface, _NS_akahime.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_akahime.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)

        # Upper arm (leather sleeve).
        pygame.draw.line(surface, _NS_akahime.PALETTE["outfit_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_akahime.PALETTE["outfit_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_akahime.PALETTE["outfit_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm (exposed skin or wrap).
        pygame.draw.line(surface, _NS_akahime.PALETTE["skin_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_akahime.PALETTE["skin_mid"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_akahime.PALETTE["skin_light"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Wrist wrap (white/scarlet bandage).
        wrap_x = (elbow_x + hand_x) // 2
        wrap_y = (elbow_y + hand_y) // 2
        pygame.draw.rect(surface, _NS_akahime.PALETTE["outfit_light"],
                        (wrap_x - 1, wrap_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_dark"],
                        (wrap_x, wrap_y - 1, 2, 1))

        # Hand.
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["skin_mid"], (hand_x, hand_y), 1)

    def _draw_aka_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm (throwing shuriken)."""
        sway = math.sin(phase * 0.4) * 1

        # Determine arm pose based on action.
        if action == "attack":
            if attack_progress < 0.3:
                # Wind-up (arm pulled back).
                t = attack_progress / 0.3
                shoulder_angle = -0.3 - t * 0.5
                elbow_bend = 0.6
            elif attack_progress < 0.55:
                # THROW (arm swings forward).
                t = (attack_progress - 0.3) / 0.25
                shoulder_angle = (-0.8) + t * 1.5
                elbow_bend = 0.6 - t * 0.4
            else:
                # Recovery.
                t = (attack_progress - 0.55) / 0.45
                shoulder_angle = 0.7 - t * 0.7
                elbow_bend = 0.2 + t * 0.2
        else:
            shoulder_angle = -0.1 + math.sin(phase * 0.5) * 0.1
            elbow_bend = 0.4

        shoulder_x = cx + facing * 8
        shoulder_y = cy - 3
        # Upper arm direction.
        upper_len = 6
        elbow_x = shoulder_x + int(math.cos(shoulder_angle) * upper_len) * facing
        elbow_y = shoulder_y + int(math.sin(shoulder_angle) * upper_len) + 2

        # Forearm direction (bent by elbow_bend).
        forearm_angle = shoulder_angle + elbow_bend
        forearm_len = 7
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len) + 3

        # Shadow.
        pygame.draw.line(surface, _NS_akahime.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_akahime.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)

        # Upper arm (leather sleeve, dark).
        pygame.draw.line(surface, _NS_akahime.PALETTE["outfit_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_akahime.PALETTE["outfit_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_akahime.PALETTE["outfit_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm (exposed skin).
        pygame.draw.line(surface, _NS_akahime.PALETTE["skin_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_akahime.PALETTE["skin_mid"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_akahime.PALETTE["skin_light"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Wrist wrap.
        wrap_x = (elbow_x + hand_x) // 2
        wrap_y = (elbow_y + hand_y) // 2
        pygame.draw.rect(surface, _NS_akahime.PALETTE["outfit_light"],
                        (wrap_x - 1, wrap_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_dark"],
                        (wrap_x, wrap_y - 1, 2, 1))

        # Hand.
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["skin_mid"], (hand_x, hand_y), 1)
        pygame.draw.rect(surface, _NS_akahime.PALETTE["skin_light"], (hand_x, hand_y, 1, 1))

        # SHURIKEN in hand (before throw).
        if action != "attack" or attack_progress < 0.5:
            _NS_akahime._draw_shuriken_small(surface, hand_x + facing * 3,
                                             hand_y - 2, phase, size=3)

    def _draw_shuriken_small(surface, cx, cy, phase, size=3):
        """Small shuriken (in hand or on body)."""
        rotation = phase * 3
        for i in range(4):
            angle = rotation + i * math.pi / 2
            tip_x = cx + int(math.cos(angle) * size)
            tip_y = cy + int(math.sin(angle) * size)
            perp = angle + math.pi / 2
            base_a = (cx + int(math.cos(perp) * 1),
                      cy + int(math.sin(perp) * 1))
            base_b = (cx - int(math.cos(perp) * 1),
                      cy - int(math.sin(perp) * 1))
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["metal_darkest"],
                             [(tip_x, tip_y), base_a, base_b])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["metal_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_a[0]) / 2), int((tip_y + base_a[1]) / 2)),
                (cx, cy),
            ])
        # Center hub.
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["scarlet_mid"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_akahime.PALETTE["petal_hot"], (cx, cy, 1, 1))

    def _draw_aka_head(surface, cx, cy, facing, phase):
        """Face with side bangs, violet eyes."""
        # Head shape (feminine oval).
        head_shape = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in head_shape])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["skin_dark"], head_shape)

        # Skin base.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx - 4, cy + 6),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 4, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Light highlight.
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["skin_light"], [
            (cx - 3, cy + 1),
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 3, cy + 1),
            (cx + 1, cy - 1),
            (cx - 1, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_akahime.PALETTE["skin_shine"], (cx, cy + 2, 1, 1))

        # HAIR TOP + side bangs.
        _NS_akahime._draw_hair_bangs(surface, cx, cy, facing, phase)

        # Eyes (violet).
        _NS_akahime._draw_violet_eyes(surface, cx, cy + 2, facing, phase)

        # Small nose.
        pygame.draw.rect(surface, _NS_akahime.PALETTE["skin_dark"], (cx, cy + 4, 1, 1))

        # Lips (scarlet).
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_mid"], (cx - 1, cy + 6, 2, 1))
        pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_light"], (cx, cy + 6, 1, 1))

    def _draw_hair_bangs(surface, cx, cy, facing, phase):
        """Hair on top of head with side bangs."""
        # Top hair (covers forehead).
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["hair_darkest"], [
            (cx - 6, cy - 2),
            (cx - 7, cy + 1),
            (cx - 6, cy + 3),
            (cx - 4, cy + 1),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 4, cy),
            (cx + 6, cy + 3),
            (cx + 7, cy + 1),
            (cx + 6, cy - 2),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])
        _NS_akahime._poly(surface, _NS_akahime.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 1),
            (cx - 4, cy),
            (cx - 1, cy - 2),
            (cx + 1, cy - 2),
            (cx + 4, cy),
            (cx + 6, cy + 1),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Side bangs (going down to cheeks).
        for side in [-1, 1]:
            bang_sway = math.sin(phase * 0.6 + side) * 1
            bang_x = cx + side * 5
            bang_top_y = cy - 2
            bang_bot_y = cy + 6 + int(bang_sway)
            pygame.draw.line(surface, _NS_akahime.PALETTE["hair_darkest"],
                            (bang_x, bang_top_y), (bang_x, bang_bot_y), 3)
            pygame.draw.line(surface, _NS_akahime.PALETTE["hair_dark"],
                            (bang_x, bang_top_y), (bang_x, bang_bot_y), 2)
            pygame.draw.line(surface, _NS_akahime.PALETTE["hair_mid"],
                            (bang_x - side, bang_top_y), (bang_x - side, bang_bot_y), 1)

        # Center forehead bangs (peek).
        for i in range(3):
            fx = cx - 2 + i * 2
            fy = cy - 2
            pygame.draw.line(surface, _NS_akahime.PALETTE["hair_darkest"],
                            (fx, fy), (fx + 1, fy + 3), 1)
            pygame.draw.line(surface, _NS_akahime.PALETTE["hair_dark"],
                            (fx, fy), (fx + 1, fy + 2), 1)

        # Purple hair highlight.
        pygame.draw.line(surface, _NS_akahime.PALETTE["hair_light"],
                        (cx - 3, cy - 4), (cx + 3, cy - 4), 1)
        pygame.draw.line(surface, _NS_akahime.PALETTE["hair_shine"],
                        (cx - 1, cy - 5), (cx + 1, cy - 5), 1)

    def _draw_violet_eyes(surface, cx, cy, facing, phase):
        """Fierce violet eyes."""
        pulse = math.sin(phase * 2.5) * 0.2 + 0.8

        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy

            # Eye white (small).
            pygame.draw.rect(surface, _NS_akahime.PALETTE["white"], (ex - 1, ey, 2, 1))

            # Iris (violet).
            pygame.draw.rect(surface, _NS_akahime.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["eye_mid"], (ex, ey, 1, 1))

            # Glow.
            for r in range(3, 0, -1):
                alpha = _NS_akahime._alpha(90 * (3 - r) / 3 * pulse)
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["eye_mid"], alpha),
                                     (ex, ey), r)

            # Bright shine dot.
            pygame.draw.rect(surface, _NS_akahime.PALETTE["eye_glow"], (ex, ey, 1, 1))

            # Eyeliner (winged tip).
            pygame.draw.line(surface, _NS_akahime.PALETTE["hair_darkest"],
                            (ex - 1, ey - 1), (ex + 1, ey - 1), 1)

    # ============================================================
    # SHURIKEN PROJECTILE (basic attack)
    # ============================================================
    def _draw_shuriken_projectile(surface, boss, x, y, progress):
        """Spinning shuriken projectile with scarlet trail."""
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_akahime._target_position(boss, x, y)

        start_x = x + facing * 16
        start_y = y - 6

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_akahime._alpha(220 - i * 25)
            size = max(1, 5 - i)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_dark"], alpha),
                                 (px, py), size)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                 (px, py), max(1, size - 1))
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                 (px, py), max(1, size - 2))
            # Petal sparks.
            if i < 4:
                spark_angle = t * 8 + i
                spx = px + int(math.cos(spark_angle) * (size + 1))
                spy = py + int(math.sin(spark_angle) * (size + 1))
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                (spx, spy, 1, 1))

        # Spinning shuriken (rotation based on progress).
        rotation = t * 20 + progress * 10
        size = 6
        for i in range(4):
            angle = rotation + i * math.pi / 2
            tip_x = bx + int(math.cos(angle) * size)
            tip_y = by + int(math.sin(angle) * size)
            perp = angle + math.pi / 2
            base_a = (bx + int(math.cos(perp) * 2),
                      by + int(math.sin(perp) * 2))
            base_b = (bx - int(math.cos(perp) * 2),
                      by - int(math.sin(perp) * 2))
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["shadow_deep"],
                             [(tip_x + 1, tip_y + 1),
                              (base_a[0] + 1, base_a[1] + 1),
                              (base_b[0] + 1, base_b[1] + 1)])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["metal_darkest"],
                             [(tip_x, tip_y), base_a, base_b])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["metal_dark"],
                             [(tip_x, tip_y),
                              (int((tip_x + base_a[0]) / 2), int((tip_y + base_a[1]) / 2)),
                              (bx, by)])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["metal_mid"],
                             [(tip_x, tip_y),
                              (int((tip_x + bx) / 2), int((tip_y + by) / 2)),
                              (bx, by)])
            # Sharp edge.
            pygame.draw.line(surface, _NS_akahime.PALETTE["metal_shine"],
                            (bx, by), (tip_x, tip_y), 1)

        # Center hub (scarlet flower).
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["scarlet_darkest"], (bx, by), 3)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["scarlet_dark"], (bx, by), 2)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["scarlet_mid"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_akahime.PALETTE["petal_hot"], (bx, by, 1, 1))

        # Glow around.
        for r in range(8, 3, -1):
            alpha = _NS_akahime._alpha(60 * (8 - r) / 8)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                 (bx, by), r)

        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(6 + st * 20)
            alpha = _NS_akahime._alpha(230 * (1 - st))
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_dark"], alpha),
                                 (tx, ty), radius + 2, 2)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                 (tx, ty), radius, 2)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                 (tx, ty), max(1, radius - 6), 1)
            # Petal burst.
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                _NS_akahime._poly(surface, (*_NS_akahime.PALETTE["petal_hot"], alpha), [
                    (ex, ey - 1),
                    (ex + 1, ey),
                    (ex, ey + 1),
                    (ex - 1, ey),
                ])

    # ============================================================
    # FLOATING PETAL PARTICLES
    # ============================================================
    def _draw_petal_particles(surface, cx, cy, phase, trail=False, facing=1,
                              intense=False):
        """Floating scarlet petals below (levitation FX)."""
        strength = 1.5 if intense else 1.0

        # Ground glow ellipse.
        glow = pygame.Surface((110, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(25, 3, -2):
            alpha = _NS_akahime._alpha((25 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_akahime.PALETTE["mist_dark"], alpha),
                                    (55 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)))
        for r in range(16, 3, -2):
            alpha = _NS_akahime._alpha((16 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_akahime.PALETTE["mist_mid"], alpha),
                                    (55 - r, 15 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 55, cy - 8))

        # Rising falling petals (spinning).
        for i, offset in enumerate([-22, -14, -6, 2, 10, 18]):
            t = (phase * 0.5 + i * 0.15) % 1.0
            px = cx + offset + int(math.sin(phase * 2 + i) * 3)
            py = cy + 4 - int(t * 22)
            alpha = _NS_akahime._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            spin = int((phase * 4 + i) % 3)
            # Petal shape.
            if spin == 0:
                _NS_akahime._poly(surface, (*_NS_akahime.PALETTE["petal_dark"], alpha), [
                    (px, py - 2),
                    (px + 2, py),
                    (px, py + 2),
                    (px - 2, py),
                ])
                _NS_akahime._poly(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha), [
                    (px, py - 1),
                    (px + 1, py),
                    (px, py + 1),
                    (px - 1, py),
                ])
            elif spin == 1:
                pygame.draw.line(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                (px - 2, py), (px + 2, py), 1)
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                (px, py, 1, 1))
            else:
                pygame.draw.line(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                (px, py - 2), (px, py + 2), 1)
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                (px, py, 1, 1))

        # Pink sparkles.
        for i in range(8):
            spark_t = (phase * 0.7 + i * 0.12) % 1.0
            sx = cx - 20 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 2 - int(spark_t * 20)
            alpha = _NS_akahime._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_akahime._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["mist_dark"], alpha),
                                     (sx, sy), max(2, 6 - i))
                _NS_akahime._poly(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha), [
                    (sx, sy - 2),
                    (sx + 2, sy),
                    (sx, sy + 2),
                    (sx - 2, sy),
                ])
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 24), pygame.SRCALPHA)
        for r in range(11, 0, -1):
            alpha = max(0, (11 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 12 - r, 90 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (5, 2, 5, 160), (5, 6, 100, 12))
        pygame.draw.ellipse(shadow, (40, 10, 40, 100), (12, 8, 86, 8))
        surface.blit(shadow, (x - 55, y - 12))

    def _draw_petal_aura(surface, x, y, phase):
        """Pink/scarlet aura with floating petals around."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for r in range(80, 5, -5):
            alpha = _NS_akahime._alpha((80 - r) * 1.1 * pulse)
            if alpha > 0:
                _NS_akahime._aacircle(aura, (*_NS_akahime.PALETTE["mist_dark"], alpha),
                                     (90, 80), r)
        for r in range(50, 5, -4):
            alpha = _NS_akahime._alpha((50 - r) * 1.3 * pulse)
            if alpha > 0:
                _NS_akahime._aacircle(aura, (*_NS_akahime.PALETTE["mist_mid"], alpha),
                                     (90, 80), r)
        for r in range(30, 5, -3):
            alpha = _NS_akahime._alpha((30 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_akahime._aacircle(aura, (*_NS_akahime.PALETTE["petal_darkest"], alpha),
                                     (90, 80), r)
        surface.blit(aura, (x - 90, y - 80))

        # Floating petals swirling.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 34 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["petal_dark"], [
                (sx, sy - 1),
                (sx + 1, sy),
                (sx, sy + 1),
                (sx - 1, sy),
            ])
            pygame.draw.rect(surface, _NS_akahime.PALETTE["petal_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with sakura runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_akahime.PALETTE["mist_dark"], 200),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_akahime.PALETTE["petal_darkest"], 220),
                            (12, 17, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_akahime.PALETTE["petal_dark"], 230),
                            (22, 19, 116, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_akahime.PALETTE["scarlet_darkest"], 180),
                            (35, 21, 90, 12), 1)

        # Runes (flower shapes).
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            # Small petal.
            _NS_akahime._poly(ring, (*_NS_akahime.PALETTE["petal_light"], 220), [
                (x1, y1 - 1),
                (x1 + 1, y1),
                (x1, y1 + 1),
                (x1 - 1, y1),
            ])

        if skill:
            pygame.draw.ellipse(ring, (*_NS_akahime.PALETTE["petal_hot"],
                                       _NS_akahime._alpha(150 * pulse)),
                                (14, 10, 132, 34), 1)
        surface.blit(ring, (x - 80, y - 24))

    # ============================================================
    # SKILL: Q - PETAL BARRAGE (multi-shuriken forward)
    # ============================================================
    def _draw_petal_barrage(surface, boss, x, y, timer, phase):
        """Volley of petal-shaped shuriken flying forward."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akahime._target_position(boss, x, y)

        start_x = x + facing * 16
        start_y = y - 6

        # 5 shuriken staggered.
        for i in range(5):
            offset = i * 0.12
            local_t = max(0.0, min(1.0, (progress - offset) * 1.3))
            if local_t <= 0:
                continue

            # Vertical spread.
            spread_y = (i - 2) * 4
            end_y = ty + spread_y

            bx = int(start_x + (tx - start_x) * local_t)
            by = int(start_y + (end_y - start_y) * local_t)

            # Trail per shuriken.
            for j in range(6):
                trail_t = max(0.0, local_t - j * 0.05)
                if trail_t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (end_y - start_y) * trail_t)
                alpha = _NS_akahime._alpha(220 - j * 30)
                size = max(1, 5 - j)
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_dark"], alpha),
                                     (px, py), size)
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                     (px, py), max(1, size - 1))
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                     (px, py), max(1, size - 2))

            # Elongated petal-shaped shuriken.
            angle = math.atan2(end_y - start_y, tx - start_x)
            length = 8
            tip = (bx + int(math.cos(angle) * length),
                   by + int(math.sin(angle) * length))
            tail = (bx - int(math.cos(angle) * length),
                    by - int(math.sin(angle) * length))
            perp = angle + math.pi / 2
            mid_a = (bx + int(math.cos(perp) * 3),
                     by + int(math.sin(perp) * 3))
            mid_b = (bx - int(math.cos(perp) * 3),
                     by - int(math.sin(perp) * 3))

            _NS_akahime._poly(surface, _NS_akahime.PALETTE["petal_darkest"],
                             [tip, mid_a, tail, mid_b])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["petal_dark"], [
                tip,
                (int((tip[0] + mid_a[0]) / 2), int((tip[1] + mid_a[1]) / 2)),
                tail,
                (int((tip[0] + mid_b[0]) / 2), int((tip[1] + mid_b[1]) / 2)),
            ])
            _NS_akahime._poly(surface, _NS_akahime.PALETTE["petal_mid"], [
                tip,
                (bx, by),
                tail,
            ])
            pygame.draw.line(surface, _NS_akahime.PALETTE["petal_light"],
                            tail, tip, 1)
            pygame.draw.rect(surface, _NS_akahime.PALETTE["petal_shine"],
                            (bx, by, 1, 1))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["white"], (tip[0], tip[1], 1, 1))

            # Impact.
            if local_t > 0.9:
                st = (local_t - 0.9) / 0.1
                r = int(4 + st * 12)
                alpha = _NS_akahime._alpha(220 * (1 - st))
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                     (tx, end_y), r, 2)
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                     (tx, end_y), max(1, r - 4), 1)

    # ============================================================
    # SKILL: W - SOUL SCROLL (bouncing scroll between enemies)
    # ============================================================
    def _draw_soul_scroll(surface, boss, x, y, timer, phase):
        """Scroll bouncing in wave pattern between multiple targets."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akahime._target_position(boss, x, y)

        start_x = x + facing * 16
        start_y = y - 6

        # 3 bounce targets.
        bounce_positions = [
            (start_x + int((tx - start_x) * 0.33),
             ty + 15),
            (start_x + int((tx - start_x) * 0.66),
             ty - 15),
            (tx, ty),
        ]

        # Full path with bounces.
        path_points = [(start_x, start_y)] + bounce_positions
        total_segments = len(path_points) - 1
        current_progress = progress * total_segments
        current_segment = min(int(current_progress), total_segments - 1)
        segment_t = current_progress - current_segment

        # Draw wave trail (past segments visible).
        for seg_i in range(current_segment + 1):
            p1 = path_points[seg_i]
            p2 = path_points[seg_i + 1]
            local_t = 1.0 if seg_i < current_segment else segment_t

            # Draw curved wave path.
            segments = 20
            for j in range(int(segments * local_t)):
                t1 = j / segments
                t2 = (j + 1) / segments
                # Arc offset (sine wave).
                arc_h = 20 if seg_i % 2 == 0 else -20
                x1 = int(p1[0] + (p2[0] - p1[0]) * t1)
                y1 = int(p1[1] + (p2[1] - p1[1]) * t1 - math.sin(t1 * math.pi) * arc_h)
                x2 = int(p1[0] + (p2[0] - p1[0]) * t2)
                y2 = int(p1[1] + (p2[1] - p1[1]) * t2 - math.sin(t2 * math.pi) * arc_h)

                # Layered wave line.
                for w, color_key in [
                    (5, "petal_darkest"),
                    (3, "petal_dark"),
                    (2, "petal_mid"),
                    (1, "petal_light"),
                ]:
                    pygame.draw.line(surface, _NS_akahime.PALETTE[color_key],
                                    (x1, y1), (x2, y2), w)

        # Current scroll position.
        if current_segment < total_segments:
            p1 = path_points[current_segment]
            p2 = path_points[current_segment + 1]
            arc_h = 20 if current_segment % 2 == 0 else -20
            scroll_x = int(p1[0] + (p2[0] - p1[0]) * segment_t)
            scroll_y = int(p1[1] + (p2[1] - p1[1]) * segment_t
                           - math.sin(segment_t * math.pi) * arc_h)

            # SCROLL SHAPE (like W icon - curled paper).
            # Body.
            pygame.draw.rect(surface, _NS_akahime.PALETTE["shadow_deep"],
                            (scroll_x - 3, scroll_y - 5, 6, 10))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                            (scroll_x - 3, scroll_y - 5, 6, 10))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_dark"],
                            (scroll_x - 2, scroll_y - 4, 4, 8))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_mid"],
                            (scroll_x - 1, scroll_y - 3, 3, 6))
            # Rolls at top/bottom.
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                            (scroll_x - 3, scroll_y - 6, 6, 2))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["scarlet_darkest"],
                            (scroll_x - 3, scroll_y + 4, 6, 2))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["metal_mid"],
                            (scroll_x - 3, scroll_y - 6, 6, 1))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["metal_light"],
                            (scroll_x - 2, scroll_y - 6, 4, 1))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["metal_mid"],
                            (scroll_x - 3, scroll_y + 5, 6, 1))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["metal_light"],
                            (scroll_x - 2, scroll_y + 5, 4, 1))

            # Glow around scroll.
            for r in range(8, 0, -1):
                alpha = _NS_akahime._alpha(100 * (8 - r) / 8)
                _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                     (scroll_x, scroll_y), r)

        # Impact at each bounce point.
        for i, (bp_x, bp_y) in enumerate(bounce_positions):
            bounce_reached_progress = (i + 1) / total_segments
            if progress >= bounce_reached_progress:
                # Impact fade.
                impact_t = min(1.0, (progress - bounce_reached_progress) * 5)
                if impact_t < 1:
                    r = int(6 + impact_t * 14)
                    alpha = _NS_akahime._alpha(230 * (1 - impact_t))
                    _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_dark"], alpha),
                                         (bp_x, bp_y), r + 2, 2)
                    _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                         (bp_x, bp_y), r, 2)
                    _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_light"], alpha),
                                         (bp_x, bp_y), max(1, r - 4), 1)
                    # Petal burst.
                    for j in range(6):
                        angle_s = j * math.pi / 3 + phase
                        ex = bp_x + int(math.cos(angle_s) * r)
                        ey = bp_y + int(math.sin(angle_s) * r * 0.7)
                        pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                        (ex, ey, 2, 2))

    # ============================================================
    # SKILL: E - SHADOW NINJUTSU (transform into purple shadow)
    # ============================================================
    def _draw_shadow_ground(surface, boss, x, y, timer, phase):
        """Purple shadow pool below."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(28 + i * 5 + math.sin(phase * 2) * 2)
            alpha = _NS_akahime._alpha(200 - i * 55)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["shadow_dark"], alpha),
                                 (x, y + 40), r, 2)
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["shadow_mid"], alpha),
                                 (x, y + 40), r, 1)

    def _draw_shadow_foreground(surface, boss, x, y, timer, phase):
        """Purple shadow silhouette overlay + trail behind."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Shadow afterimages trailing behind boss.
        for i in range(6):
            trail_offset = (i + 1) * 8 * facing
            alpha = _NS_akahime._alpha(200 - i * 30)
            if alpha <= 0:
                continue

            # Ghost silhouette.
            tx = x - trail_offset
            ty = y - 4 + int(math.sin(phase + i) * 2)

            # Body silhouette.
            silhouette = [
                (tx - 8, ty - 6),
                (tx - 10, ty),
                (tx - 8, ty + 8),
                (tx - 4, ty + 14),
                (tx + 4, ty + 14),
                (tx + 8, ty + 8),
                (tx + 10, ty),
                (tx + 8, ty - 6),
                (tx + 4, ty - 14),
                (tx - 4, ty - 14),
            ]
            _NS_akahime._poly(surface,
                             (*_NS_akahime.PALETTE["shadow_darkest"], alpha),
                             silhouette)
            # Inner glow.
            _NS_akahime._poly(surface,
                             (*_NS_akahime.PALETTE["shadow_dark"], alpha // 2), [
                                 (tx - 6, ty - 4),
                                 (tx - 8, ty),
                                 (tx - 6, ty + 6),
                                 (tx - 2, ty + 12),
                                 (tx + 2, ty + 12),
                                 (tx + 6, ty + 6),
                                 (tx + 8, ty),
                                 (tx + 6, ty - 4),
                                 (tx + 3, ty - 12),
                                 (tx - 3, ty - 12),
                             ])
            # Purple wisp on top.
            _NS_akahime._aacircle(surface,
                                 (*_NS_akahime.PALETTE["shadow_mid"], alpha),
                                 (tx, ty - 12), 3)
            _NS_akahime._aacircle(surface,
                                 (*_NS_akahime.PALETTE["shadow_light"], alpha),
                                 (tx, ty - 12), 1)

            # Trailing wisp particles.
            for j in range(3):
                wisp_x = tx + int(math.sin(phase * 2 + j + i) * 5)
                wisp_y = ty + 4 + int(math.cos(phase * 2 + j) * 3)
                pygame.draw.rect(surface,
                                (*_NS_akahime.PALETTE["shadow_light"], alpha),
                                (wisp_x, wisp_y, 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                (wisp_x, wisp_y, 1, 1))

        # Speed lines around boss.
        for i in range(5):
            line_y = y - 8 + i * 4
            line_x_start = x - 40 * facing
            line_x_end = x - 10 * facing
            alpha = _NS_akahime._alpha(180 - i * 20)
            pygame.draw.line(surface,
                            (*_NS_akahime.PALETTE["shadow_light"], alpha),
                            (line_x_start, line_y), (line_x_end, line_y), 1)

    # ============================================================
    # SKILL: R - FORBIDDEN JUTSU: HIGANBANA (giant flower on target)
    # ============================================================
    def _draw_higanbana_ground(surface, boss, x, y, timer, phase):
        """Ground rune circle at target."""
        tx, ty = _NS_akahime._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2))

        if r > 5:
            # Base dark ellipse.
            pygame.draw.ellipse(surface, (*_NS_akahime.PALETTE["petal_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_akahime.PALETTE["petal_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_akahime.PALETTE["scarlet_darkest"], 160),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

            # Runic edge.
            pygame.draw.ellipse(surface, (*_NS_akahime.PALETTE["petal_light"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_akahime.PALETTE["petal_hot"], 240),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)

    def _draw_higanbana_foreground(surface, boss, x, y, timer, phase):
        """Giant scarlet flower with 6 petals blooming."""
        tx, ty = _NS_akahime._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bloom = min(1.0, progress * 2)

        if bloom < 0.1:
            return

        # Rotate over time.
        rotation = phase * 0.4
        petal_length = int(45 * bloom)
        petal_width = int(15 * bloom)

        # Draw 6 large flower petals.
        for i in range(6):
            angle = rotation + i * math.pi / 3

            # Petal shape (elongated diamond).
            tip_x = tx + int(math.cos(angle) * petal_length)
            tip_y = ty + int(math.sin(angle) * petal_length * 0.7)
            mid1_angle = angle + 0.15
            mid2_angle = angle - 0.15
            mid_dist = petal_length * 0.5
            mid1_x = tx + int(math.cos(mid1_angle) * mid_dist)
            mid1_y = ty + int(math.sin(mid1_angle) * mid_dist * 0.7)
            mid2_x = tx + int(math.cos(mid2_angle) * mid_dist)
            mid2_y = ty + int(math.sin(mid2_angle) * mid_dist * 0.7)

            # Layered petal.
            petal_poly = [
                (tx, ty),
                (mid1_x, mid1_y),
                (tip_x, tip_y),
                (mid2_x, mid2_y),
            ]

            # Draw with alpha layers.
            petal_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
            offset_x = tx - 100
            offset_y = ty - 100
            local_poly = [(p[0] - offset_x, p[1] - offset_y) for p in petal_poly]

            _NS_akahime._poly(petal_surf,
                             (*_NS_akahime.PALETTE["petal_darkest"], 220), local_poly)

            # Inner brighter shape.
            inner_poly = []
            cx_p = sum(p[0] for p in local_poly) / 4
            cy_p = sum(p[1] for p in local_poly) / 4
            for p in local_poly:
                inner_poly.append((int(p[0] * 0.7 + cx_p * 0.3),
                                   int(p[1] * 0.7 + cy_p * 0.3)))
            _NS_akahime._poly(petal_surf,
                             (*_NS_akahime.PALETTE["petal_dark"], 200), inner_poly)

            # Even inner (bright).
            inner2_poly = []
            for p in inner_poly:
                inner2_poly.append((int(p[0] * 0.6 + cx_p * 0.4),
                                    int(p[1] * 0.6 + cy_p * 0.4)))
            _NS_akahime._poly(petal_surf,
                             (*_NS_akahime.PALETTE["petal_mid"], 180), inner2_poly)

            # Bright vein through center of petal.
            local_tip = (tip_x - offset_x, tip_y - offset_y)
            local_center = (tx - offset_x, ty - offset_y)
            pygame.draw.line(petal_surf,
                            (*_NS_akahime.PALETTE["petal_light"], 240),
                            local_center, local_tip, 2)
            pygame.draw.line(petal_surf,
                            (*_NS_akahime.PALETTE["petal_hot"], 250),
                            local_center, local_tip, 1)

            # Tip glow.
            for r_glow in range(4, 0, -1):
                alpha = _NS_akahime._alpha(120 * (4 - r_glow) / 4)
                _NS_akahime._aacircle(petal_surf,
                                     (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                     local_tip, r_glow)
            pygame.draw.rect(petal_surf, _NS_akahime.PALETTE["petal_shine"],
                            (local_tip[0], local_tip[1], 1, 1))

            surface.blit(petal_surf, (offset_x, offset_y))

        # Center glowing core.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_r = int(10 * bloom * pulse)
        for r_c in range(core_r + 4, 0, -1):
            alpha = _NS_akahime._alpha(200 * (core_r + 4 - r_c) / (core_r + 4))
            _NS_akahime._aacircle(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha),
                                 (tx, ty), r_c)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["petal_darkest"], (tx, ty), 6)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["petal_dark"], (tx, ty), 4)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["petal_light"], (tx, ty), 3)
        _NS_akahime._aacircle(surface, _NS_akahime.PALETTE["petal_hot"], (tx, ty), 2)
        pygame.draw.rect(surface, _NS_akahime.PALETTE["white"], (tx, ty, 1, 1))

        # Stamens (small dots around core).
        for i in range(8):
            angle = rotation * 2 + i * math.pi / 4
            sx = tx + int(math.cos(angle) * 8)
            sy = ty + int(math.sin(angle) * 8)
            pygame.draw.rect(surface, _NS_akahime.PALETTE["petal_shine"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_akahime.PALETTE["white"], (sx, sy, 1, 1))

        # Falling petals around area.
        for i in range(12):
            pt = (phase * 0.4 + i * 0.09) % 1.0
            pang = i * math.pi / 6
            pr = 40 + int(math.sin(phase + i) * 10)
            px = tx + int(math.cos(pang) * pr)
            py = ty + int(math.sin(pang) * pr * 0.7) - int(pt * 15)
            alpha = _NS_akahime._alpha(180 * (1 - pt))
            if alpha > 0:
                _NS_akahime._poly(surface, (*_NS_akahime.PALETTE["petal_mid"], alpha), [
                    (px, py - 2),
                    (px + 2, py),
                    (px, py + 2),
                    (px - 2, py),
                ])
                pygame.draw.rect(surface, (*_NS_akahime.PALETTE["petal_hot"], alpha),
                                (px, py, 1, 1))


# ====================================================================
# nyxthrael.py
# ====================================================================

# ====================================================================
# NYXTHRAEL - The Cursed Executioner (Mini Boss)
# ====================================================================


class _NS_nyxthrael:
    """Namespace nyxthrael - Shadow assassin mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Shadow cloak (main body, hood)
        "cloak_darkest": (5, 3, 10),
        "cloak_dark": (18, 10, 28),
        "cloak_mid": (40, 25, 60),
        "cloak_light": (75, 50, 105),
        "cloak_edge": (120, 85, 155),
        "cloak_shine": (170, 130, 200),

        # Dark armor plates (spikes, pauldrons)
        "armor_darkest": (8, 6, 12),
        "armor_dark": (25, 20, 32),
        "armor_mid": (55, 45, 70),
        "armor_light": (100, 85, 125),
        "armor_shine": (160, 145, 190),

        # Blade metal (scythe)
        "blade_darkest": (10, 8, 15),
        "blade_dark": (35, 30, 45),
        "blade_mid": (85, 75, 105),
        "blade_light": (155, 140, 180),
        "blade_shine": (220, 210, 240),

        # Red eyes/glow (menyala terang)
        "eye_socket": (5, 2, 5),
        "eye_darkest": (35, 5, 15),
        "eye_dark": (90, 10, 30),
        "eye_mid": (200, 30, 60),
        "eye_light": (255, 80, 100),
        "eye_glow": (255, 180, 180),

        # Magenta/pink shadow (Q dash, R crash)
        "magenta_darkest": (30, 5, 25),
        "magenta_dark": (90, 15, 75),
        "magenta_mid": (180, 40, 140),
        "magenta_light": (245, 100, 200),
        "magenta_hot": (255, 170, 230),
        "magenta_shine": (255, 220, 245),

        # Purple void (W night fall)
        "void_darkest": (10, 5, 30),
        "void_dark": (40, 15, 80),
        "void_mid": (95, 40, 165),
        "void_light": (170, 100, 230),
        "void_hot": (220, 170, 255),
        "void_shine": (245, 220, 255),

        # Crimson (R shadow bringer)
        "crimson_darkest": (25, 5, 10),
        "crimson_dark": (85, 10, 25),
        "crimson_mid": (200, 30, 55),
        "crimson_light": (255, 80, 100),
        "crimson_hot": (255, 160, 180),
        "crimson_shine": (255, 220, 230),

        # Bone/skull details
        "bone_dark": (60, 55, 45),
        "bone_mid": (150, 140, 120),
        "bone_light": (230, 220, 200),

        # Mist
        "mist_dark": (15, 8, 30),
        "mist_mid": (60, 30, 100),
        "mist_light": (140, 80, 180),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxthrael._clamp(color)
        if _NS_nyxthrael.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxthrael._clamp(color)
        if _NS_nyxthrael.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxthrael._clamp(color), points)

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
    def draw_nyxthrael(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxthrael._detect_moving(boss)
        _NS_nyxthrael._update_nyx_attack_anim(boss)
        attacking = (
            getattr(boss, "_nxt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_nyxthrael._draw_shadow_aura(surface, x, y, pulse)
        _NS_nyxthrael._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_nyxthrael._draw_ambush_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxthrael._draw_nightfall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxthrael._draw_darknightfall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxthrael._draw_shadowbringer_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_nyxthrael._draw_nyx_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxthrael._draw_nyx_float_move(surface, boss, x, y)
        else:
            _NS_nyxthrael._draw_nyx_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_nyxthrael._draw_ambush_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxthrael._draw_nightfall_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxthrael._draw_darknightfall_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxthrael._draw_shadowbringer_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_nyx_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nxt_previous_timer", 0))
        active = bool(getattr(boss, "_nxt_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nxt_attack_active = True
            boss._nxt_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._nxt_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._nxt_attack_frame = int(
                getattr(boss, "_nxt_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._nxt_attack_active = False
            boss._nxt_attack_frame = 0
            active = False

        boss._nxt_previous_timer = timer
        boss._nxt_attack_progress = (
            min(1.0, getattr(boss, "_nxt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_nxt_last_x"):
            boss._nxt_last_x = boss.x
            boss._nxt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nxt_last_x)
        dy = abs(boss.y - boss._nxt_last_y)
        boss._nxt_last_x = boss.x
        boss._nxt_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING)
    # ============================================================
    def _draw_nyx_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_nyxthrael._draw_shadow(surface, x, y + 52)
        _NS_nyxthrael._draw_shadow_wisps(surface, x, y + 40, boss.pulse)
        _NS_nyxthrael._draw_nyx_body(surface, x, y - 4 + float_bob,
                                     boss.direction, boss.pulse, "idle", 0)

    def _draw_nyx_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_nyxthrael._draw_shadow(surface, x + sway, y + 52)
        _NS_nyxthrael._draw_shadow_wisps(surface, x + sway, y + 40, phase,
                                         trail=True, facing=boss.direction)
        _NS_nyxthrael._draw_nyx_body(surface, x + sway, y - 6 + float_bob,
                                     boss.direction, phase, "move", 0)

    def _draw_nyx_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_nxt_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_nxt_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Melee scythe swing: wind-up → swing → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * facing  # pull back
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 16)) * facing  # swing forward
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        float_bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_nyxthrael._draw_shadow(surface, x + lunge, y + 52)
        _NS_nyxthrael._draw_shadow_wisps(surface, x + lunge, y + 40, boss.pulse,
                                         intense=True)
        _NS_nyxthrael._draw_nyx_body(surface, x + lunge, y - 4 - lift + float_bob,
                                     facing, boss.pulse, "attack", progress)

    # ============================================================
    # BODY (Hooded assassin with scythe, floating)
    # ============================================================
    def _draw_nyx_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw hooded assassin: cloak, torso, arms, hood, scythe."""
        # Trailing cloak tatters below (no legs).
        _NS_nyxthrael._draw_cloak_tatters(surface, cx, cy + 8, facing, phase)

        # Back arm (holding scythe idle) or hidden.
        # Torso with armor.
        _NS_nyxthrael._draw_nyx_torso(surface, cx, cy, facing, phase)

        # Pauldrons (spiky shoulders).
        _NS_nyxthrael._draw_pauldrons(surface, cx, cy - 4, facing, phase)

        # Hood + head.
        _NS_nyxthrael._draw_hood_head(surface, cx, cy - 14, facing, phase)

        # Scythe (behind if idle, swinging if attack).
        _NS_nyxthrael._draw_scythe(surface, cx, cy, facing, phase, action,
                                   attack_progress)

    def _draw_cloak_tatters(surface, cx, cy, facing, phase):
        """Ragged tattered cloak trailing below (no legs)."""
        sway = math.sin(phase * 0.5) * 2

        # Main cloak silhouette.
        cloak_shape = [
            (cx - 13, cy - 8),
            (cx - 16, cy - 2),
            (cx - 15, cy + 6),
            (cx - 12, cy + 14 + int(sway)),
            (cx - 8, cy + 20),
            (cx - 3, cy + 22 - int(sway)),
            (cx + 3, cy + 21),
            (cx + 8, cy + 18 + int(sway)),
            (cx + 12, cy + 12),
            (cx + 15, cy + 4),
            (cx + 16, cy - 2),
            (cx + 13, cy - 6),
        ]
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in cloak_shape])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_darkest"], cloak_shape)

        # Layered folds.
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_dark"], [
            (cx - 12, cy - 6),
            (cx - 14, cy),
            (cx - 13, cy + 8),
            (cx - 8, cy + 15),
            (cx - 2, cy + 18),
            (cx + 4, cy + 17),
            (cx + 10, cy + 12),
            (cx + 13, cy + 4),
            (cx + 14, cy),
            (cx + 12, cy - 5),
        ])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_mid"], [
            (cx - 9, cy - 4),
            (cx - 11, cy + 2),
            (cx - 7, cy + 10),
            (cx + 5, cy + 10),
            (cx + 10, cy + 4),
            (cx + 11, cy - 2),
            (cx + 9, cy - 3),
        ])

        # Ragged tatters at bottom (jagged fringe).
        tatter_positions = [
            (cx - 12, cy + 14, -1),
            (cx - 8, cy + 19, -1),
            (cx - 4, cy + 21, 0),
            (cx, cy + 22, 0),
            (cx + 4, cy + 21, 0),
            (cx + 8, cy + 18, 1),
            (cx + 12, cy + 14, 1),
        ]
        for tx, ty, tilt in tatter_positions:
            t_sway = math.sin(phase * 0.8 + tx * 0.1) * 1
            ty_actual = ty + int(t_sway)
            # Jagged spike tatter.
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_darkest"], [
                (tx, ty_actual - 3),
                (tx + 2 + tilt, ty_actual),
                (tx, ty_actual + 4),
                (tx - 2 + tilt, ty_actual),
            ])
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_dark"], [
                (tx, ty_actual - 2),
                (tx + 1 + tilt, ty_actual),
                (tx, ty_actual + 3),
                (tx - 1 + tilt, ty_actual),
            ])
            # Purple edge glow on some.
            if tx % 4 == 0:
                pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["cloak_edge"],
                                (tx + tilt, ty_actual, 1, 1))

        # Magenta wisp escaping the cloak.
        for i in range(3):
            wisp_t = (phase * 0.6 + i * 0.3) % 1.0
            wx = cx - 8 + i * 8 + int(math.sin(phase + i) * 3)
            wy = cy + 18 - int(wisp_t * 8)
            alpha = _NS_nyxthrael._alpha(180 * (1 - wisp_t))
            if alpha > 0:
                _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["magenta_dark"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_light"], alpha),
                                (wx, wy, 1, 1))

    def _draw_nyx_torso(surface, cx, cy, facing, phase):
        """Dark armored torso under cloak."""
        breath = math.sin(phase * 0.7) * 1

        # Torso silhouette.
        torso_shape = [
            (cx - 10, cy - 6),
            (cx - 12, cy - 2),
            (cx - 11, cy + 6),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 11, cy + 6),
            (cx + 12, cy - 2),
            (cx + 10, cy - 6),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_shape])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_darkest"], torso_shape)

        # Armor plate (chest).
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_darkest"], [
            (cx - 8, cy - 4),
            (cx - 9, cy),
            (cx - 7, cy + 6),
            (cx + 7, cy + 6),
            (cx + 9, cy),
            (cx + 8, cy - 4),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy),
            (cx - 6, cy + 5),
            (cx + 6, cy + 5),
            (cx + 8, cy),
            (cx + 7, cy - 3),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_mid"], [
            (cx - 5, cy - 2),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 2),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Vertical plate seam.
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["armor_darkest"],
                        (cx, cy - 4), (cx, cy + 5), 1)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["armor_light"],
                        (cx + 1, cy - 3), (cx + 1, cy + 4), 1)

        # Red glowing gem/rune on chest (curse mark).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gx, gy = cx, cy + 2
        for r in range(4, 0, -1):
            alpha = _NS_nyxthrael._alpha(180 * (4 - r) / 4 * pulse)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["eye_mid"], alpha),
                                   (gx, gy), r)
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["eye_darkest"], (gx, gy), 2)
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["eye_mid"], (gx, gy), 1)
        pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_light"], (gx, gy, 1, 1))

        # Armor edge highlights.
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["armor_shine"],
                        (cx - 4, cy - 4), (cx + 4, cy - 4), 1)

    def _draw_pauldrons(surface, cx, cy, facing, phase):
        """Spiky armored shoulders."""
        for side in [-1, 1]:
            px = cx + side * 10
            py = cy

            # Pauldron main plate.
            pauldron = [
                (px - side * 2, py - 3),
                (px + side * 5, py - 4),
                (px + side * 7, py + 1),
                (px + side * 5, py + 5),
                (px - side * 2, py + 4),
            ]
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"],
                               [(x + 1, y + 1) for x, y in pauldron])
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_darkest"], pauldron)
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_dark"], [
                (px - side, py - 2),
                (px + side * 4, py - 3),
                (px + side * 6, py + 1),
                (px + side * 4, py + 4),
                (px - side, py + 3),
            ])
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_mid"], [
                (px, py - 1),
                (px + side * 3, py - 2),
                (px + side * 4, py + 1),
                (px + side * 3, py + 3),
                (px, py + 2),
            ])
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["armor_shine"],
                            (px + side * 2, py - 1, 1, 1))

            # Spike on pauldron (upward + outward).
            for spike_off, spike_len in [(-2, 5), (1, 6), (4, 4)]:
                sp_base_x = px + side * spike_off
                sp_base_y = py - 3
                sp_tip_x = sp_base_x + side * 1
                sp_tip_y = sp_base_y - spike_len

                _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"], [
                    (sp_tip_x + 1, sp_tip_y + 1),
                    (sp_base_x - 1, sp_base_y + 1),
                    (sp_base_x + 2, sp_base_y + 1),
                ])
                _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_darkest"], [
                    (sp_tip_x, sp_tip_y),
                    (sp_base_x - 1, sp_base_y),
                    (sp_base_x + 2, sp_base_y),
                ])
                _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_mid"], [
                    (sp_tip_x, sp_tip_y),
                    (sp_base_x, sp_base_y),
                    (sp_base_x + 1, sp_base_y),
                ])
                pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["armor_shine"],
                                (sp_tip_x, sp_tip_y, 1, 1))

    def _draw_hood_head(surface, cx, cy, facing, phase):
        """Dark hood shadowing face, only red eyes visible."""
        # Hood main shape (larger, covering head).
        hood_shape = [
            (cx - 9, cy + 2),
            (cx - 11, cy - 2),
            (cx - 9, cy - 8),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 9, cy - 8),
            (cx + 11, cy - 2),
            (cx + 9, cy + 2),
            (cx + 7, cy + 6),
            (cx - 7, cy + 6),
        ]
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in hood_shape])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_darkest"], hood_shape)

        # Hood outer.
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_dark"], [
            (cx - 8, cy + 1),
            (cx - 10, cy - 2),
            (cx - 8, cy - 7),
            (cx - 3, cy - 11),
            (cx + 3, cy - 11),
            (cx + 8, cy - 7),
            (cx + 10, cy - 2),
            (cx + 8, cy + 1),
        ])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["cloak_mid"], [
            (cx - 6, cy - 1),
            (cx - 8, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 8, cy - 4),
            (cx + 6, cy - 1),
        ])

        # Hood edge highlight.
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["cloak_edge"],
                        (cx - 5, cy - 10), (cx + 5, cy - 10), 1)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["cloak_shine"],
                        (cx - 2, cy - 11), (cx + 2, cy - 11), 1)

        # Deep shadow inside hood (face area).
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow"], [
            (cx - 5, cy - 2),
            (cx - 6, cy - 6),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 6, cy - 6),
            (cx + 5, cy - 2),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])

        # BURNING RED EYES.
        _NS_nyxthrael._draw_red_eyes(surface, cx, cy - 4, facing, phase)

        # Small horn/spike on top of hood.
        for offset in [-3, 0, 3]:
            spike_x = cx + offset
            spike_top_y = cy - 14
            spike_base_y = cy - 11
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top_y + 1),
                (spike_x - 1, spike_base_y + 1),
                (spike_x + 2, spike_base_y + 1),
            ])
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_darkest"], [
                (spike_x, spike_top_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["armor_dark"], [
                (spike_x, spike_top_y),
                (spike_x, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["armor_shine"],
                            (spike_x, spike_top_y, 1, 1))

    def _draw_red_eyes(surface, cx, cy, facing, phase):
        """Two burning red eyes glowing from hood shadow."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy

            # Deep glow.
            for r in range(5, 0, -1):
                alpha = _NS_nyxthrael._alpha(160 * (5 - r) / 5 * pulse)
                _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)

            # Bright eye core.
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_darkest"],
                            (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_dark"],
                            (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_mid"],
                            (ex, ey - 1, 1, 1))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_light"],
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_glow"],
                            (ex, ey, 1, 1))

            # Red tear/glow trail below eye.
            for i in range(3):
                tear_alpha = _NS_nyxthrael._alpha(120 * (3 - i) / 3 * pulse)
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["eye_dark"], tear_alpha),
                                (ex, ey + 1 + i, 1, 1))

    def _draw_scythe(surface, cx, cy, facing, phase, action, attack_progress):
        """Curved scythe with red glowing blade."""
        # Determine scythe angle based on action.
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up (raised behind).
                t = attack_progress / 0.35
                angle = -math.pi * 0.4 - t * 0.8
            elif attack_progress < 0.6:
                # SWING (fast forward arc).
                t = (attack_progress - 0.35) / 0.25
                angle = (-math.pi * 1.2) + t * (math.pi * 1.4)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                angle = 0.2 - t * 0.5
        else:
            # Idle: resting on shoulder.
            angle = -math.pi * 0.3 + math.sin(phase * 0.5) * 0.05

        # Apply facing.
        actual_angle = angle * facing

        # Scythe handle base at hand.
        hand_x = cx + facing * 8
        hand_y = cy + 2

        handle_len = 30
        end_x = hand_x + int(math.cos(actual_angle) * handle_len)
        end_y = hand_y + int(math.sin(actual_angle) * handle_len)

        # Handle shaft (dark wood/metal).
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["shadow_deep"],
                        (hand_x + 1, hand_y + 1), (end_x + 1, end_y + 1), 4)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["armor_darkest"],
                        (hand_x, hand_y), (end_x, end_y), 3)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["armor_dark"],
                        (hand_x, hand_y), (end_x, end_y), 2)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["armor_mid"],
                        (hand_x, hand_y), (end_x, end_y), 1)

        # Grip wraps.
        for wrap_t in [0.15, 0.3]:
            wx = int(hand_x + (end_x - hand_x) * wrap_t)
            wy = int(hand_y + (end_y - hand_y) * wrap_t)
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["cloak_darkest"],
                            (wx - 1, wy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["cloak_dark"],
                            (wx, wy - 1, 2, 2))

        # BLADE at top - curved crescent.
        blade_angle = actual_angle + math.pi / 2  # perpendicular to handle
        blade_base = (end_x, end_y)

        # Blade extends in curved arc from end.
        blade_length = 18
        blade_curl = 12

        # Blade back point (opposite of curve).
        back_x = end_x + int(math.cos(actual_angle - 0.3) * 6)
        back_y = end_y + int(math.sin(actual_angle - 0.3) * 6)

        # Blade tip (curved outward).
        tip_x = end_x + int(math.cos(actual_angle + math.pi * 0.3) * blade_length)
        tip_y = end_y + int(math.sin(actual_angle + math.pi * 0.3) * blade_length)

        # Middle curve point.
        mid_x = end_x + int(math.cos(actual_angle + math.pi * 0.55) * blade_curl)
        mid_y = end_y + int(math.sin(actual_angle + math.pi * 0.55) * blade_curl)

        # Blade base attachment (perpendicular).
        base_a_x = end_x + int(math.cos(blade_angle) * 3)
        base_a_y = end_y + int(math.sin(blade_angle) * 3)
        base_b_x = end_x - int(math.cos(blade_angle) * 3)
        base_b_y = end_y - int(math.sin(blade_angle) * 3)

        # Draw blade as curved polygon.
        blade_poly = [
            (base_a_x, base_a_y),
            (mid_x, mid_y),
            (tip_x, tip_y),
            (back_x, back_y),
            (base_b_x, base_b_y),
        ]
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["shadow_deep"],
                           [(x + 1, y + 1) for x, y in blade_poly])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["blade_darkest"], blade_poly)
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["blade_dark"], [
            (base_a_x, base_a_y),
            (int((mid_x + tip_x) / 2), int((mid_y + tip_y) / 2)),
            (tip_x, tip_y),
            (int((tip_x + back_x) / 2), int((tip_y + back_y) / 2)),
            (base_b_x, base_b_y),
        ])
        _NS_nyxthrael._poly(surface, _NS_nyxthrael.PALETTE["blade_mid"], [
            (int((base_a_x + mid_x) / 2), int((base_a_y + mid_y) / 2)),
            (int((mid_x + tip_x) / 2), int((mid_y + tip_y) / 2)),
            (tip_x, tip_y),
            (int((base_a_x + tip_x) / 2), int((base_a_y + tip_y) / 2)),
        ])

        # Sharp edge highlight (curved shine line).
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["blade_light"],
                        (base_a_x, base_a_y), (mid_x, mid_y), 1)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["blade_shine"],
                        (mid_x, mid_y), (tip_x, tip_y), 1)

        # Red glow along blade edge.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        glow_alpha = _NS_nyxthrael._alpha(180 * pulse)
        pygame.draw.line(surface, (*_NS_nyxthrael.PALETTE["eye_mid"], glow_alpha),
                        (base_a_x, base_a_y), (mid_x, mid_y), 2)
        pygame.draw.line(surface, (*_NS_nyxthrael.PALETTE["eye_light"], glow_alpha),
                        (mid_x, mid_y), (tip_x, tip_y), 1)

        # Bright tip (like referring image).
        for r in range(4, 0, -1):
            alpha = _NS_nyxthrael._alpha(150 * (4 - r) / 4 * pulse)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["magenta_light"], alpha),
                                   (tip_x, tip_y), r)
        pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["magenta_shine"], (tip_x, tip_y, 1, 1))

        # Handle end cap (skull or ornament).
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["armor_darkest"],
                               (hand_x - int(math.cos(actual_angle) * 3),
                                hand_y - int(math.sin(actual_angle) * 3)), 3)
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["armor_mid"],
                               (hand_x - int(math.cos(actual_angle) * 3),
                                hand_y - int(math.sin(actual_angle) * 3)), 2)
        pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["eye_mid"],
                        (hand_x - int(math.cos(actual_angle) * 3),
                         hand_y - int(math.sin(actual_angle) * 3), 1, 1))

        # SWING TRAIL (during attack).
        if action == "attack" and 0.35 < attack_progress < 0.7:
            swing_t = (attack_progress - 0.35) / 0.35
            trail_intensity = math.sin(swing_t * math.pi)
            _NS_nyxthrael._draw_swing_trail(surface, hand_x, hand_y, facing, actual_angle,
                                           attack_progress, trail_intensity)

    def _draw_swing_trail(surface, hand_x, hand_y, facing, current_angle,
                          progress, intensity):
        """Magenta/red trail arc from scythe swing."""
        # Trail arc spans from wind-up angle to current angle.
        start_angle = (-math.pi * 1.2) * facing
        arc_span = math.pi * 1.4 * facing

        segments = 12
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            arc_t1 = min(1.0, (progress - 0.35) / 0.25)
            if t1 > arc_t1:
                continue
            a1 = start_angle + arc_span * t1
            a2 = start_angle + arc_span * t2

            radius = 30
            p1 = (hand_x + int(math.cos(a1) * radius),
                  hand_y + int(math.sin(a1) * radius))
            p2 = (hand_x + int(math.cos(a2) * radius),
                  hand_y + int(math.sin(a2) * radius))

            alpha = _NS_nyxthrael._alpha(220 * intensity * (t1))

            # Layered trail (thick outer to thin inner).
            for layer, (width, color_key) in enumerate([
                (5, "magenta_dark"),
                (3, "magenta_mid"),
                (1, "magenta_light"),
            ]):
                pygame.draw.line(surface,
                                (*_NS_nyxthrael.PALETTE[color_key], alpha),
                                p1, p2, width)

            # Bright edge sparks.
            if i % 2 == 0:
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_hot"], alpha),
                                (p2[0], p2[1], 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_shine"], alpha),
                                (p2[0], p2[1], 1, 1))

    # ============================================================
    # SHADOW WISPS (floating below body)
    # ============================================================
    def _draw_shadow_wisps(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Dark purple wisps floating below (levitation FX)."""
        strength = 1.5 if intense else 1.0

        # Ground shadow ellipse.
        glow = pygame.Surface((110, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(26, 3, -2):
            alpha = _NS_nyxthrael._alpha((26 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_nyxthrael.PALETTE["mist_dark"], alpha),
                                    (55 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)))
        for r in range(18, 3, -2):
            alpha = _NS_nyxthrael._alpha((18 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_nyxthrael.PALETTE["mist_mid"], alpha),
                                    (55 - r, 15 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 55, cy - 8))

        # Rising dark wisps.
        for i, offset in enumerate([-18, -10, -2, 6, 14, 22]):
            t = (phase * 0.6 + i * 0.15) % 1.0
            wx = cx + offset + int(math.sin(phase * 2 + i) * 3)
            wy = cy + 4 - int(t * 22)
            alpha = _NS_nyxthrael._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["mist_dark"], alpha),
                                   (wx, wy), 3)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["mist_mid"], alpha),
                                   (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["mist_light"], alpha),
                            (wx, wy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["cloak_shine"], alpha),
                            (wx, wy - 2, 1, 1))

        # Red ember sparkles.
        for i in range(8):
            spark_t = (phase * 0.7 + i * 0.12) % 1.0
            sx = cx - 22 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 2 - int(spark_t * 20)
            alpha = _NS_nyxthrael._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["eye_dark"], alpha),
                                (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["eye_light"], alpha),
                                (sx, sy, 1, 1))

        # Magenta wisps (assassination magic).
        for i in range(5):
            m_t = (phase * 0.5 + i * 0.2) % 1.0
            mx = cx - 15 + i * 8 + int(math.sin(phase * 1.5 + i) * 4)
            my = cy + 6 - int(m_t * 18)
            alpha = _NS_nyxthrael._alpha(180 * (1 - m_t) * strength)
            if alpha > 0:
                _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["magenta_dark"], alpha),
                                       (mx, my), 2)
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_light"], alpha),
                                (mx, my, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxthrael._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["mist_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["mist_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_light"], alpha),
                                (sx, sy - 1, 2, 2))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            alpha = max(0, (12 - r) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 13 - r, 100 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 7, 110, 12))
        pygame.draw.ellipse(shadow, (20, 10, 40, 110), (12, 9, 96, 8))
        surface.blit(shadow, (x - 60, y - 13))

    def _draw_shadow_aura(surface, x, y, phase):
        """Dark purple/red aura around assassin."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for r in range(85, 5, -5):
            alpha = _NS_nyxthrael._alpha((85 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxthrael._aacircle(aura, (*_NS_nyxthrael.PALETTE["mist_dark"], alpha),
                                       (100, 85), r)
        for r in range(55, 5, -4):
            alpha = _NS_nyxthrael._alpha((55 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_nyxthrael._aacircle(aura, (*_NS_nyxthrael.PALETTE["void_dark"], alpha),
                                       (100, 85), r)
        # Red inner tint.
        for r in range(32, 5, -3):
            alpha = _NS_nyxthrael._alpha((32 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_nyxthrael._aacircle(aura, (*_NS_nyxthrael.PALETTE["eye_darkest"], alpha),
                                       (100, 85), r)
        surface.blit(aura, (x - 100, y - 85))

        # Floating red embers.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 34 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_nyxthrael.PALETTE["eye_mid"] if i % 2 == 0 \
                else _NS_nyxthrael.PALETTE["magenta_mid"]
            hot = _NS_nyxthrael.PALETTE["eye_light"] if i % 2 == 0 \
                else _NS_nyxthrael.PALETTE["magenta_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Dark ring with red runes under boss."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxthrael.PALETTE["mist_dark"], 200),
                            (5, 16, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxthrael.PALETTE["void_darkest"], 220),
                            (12, 18, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxthrael.PALETTE["void_dark"], 230),
                            (22, 20, 116, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_nyxthrael.PALETTE["eye_darkest"], 180),
                            (35, 22, 90, 12), 1)

        # Red runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 62)
            y2 = 28 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_nyxthrael.PALETTE["eye_light"], 220),
                            (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxthrael.PALETTE["magenta_hot"],
                                       _NS_nyxthrael._alpha(150 * pulse)),
                                (14, 10, 132, 36), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL: Q - DEADLY AMBUSH (dash with magenta trail)
    # ============================================================
    def _draw_ambush_ground(surface, boss, x, y, timer, phase):
        """Dash trail line on ground."""
        tx, ty = _NS_nyxthrael._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Line from boss to target (dash path).
        alpha = _NS_nyxthrael._alpha(200 * (1 - progress * 0.5))

        # Base ground line.
        for w in [7, 5, 3, 1]:
            color_map = {
                7: _NS_nyxthrael.PALETTE["magenta_darkest"],
                5: _NS_nyxthrael.PALETTE["magenta_dark"],
                3: _NS_nyxthrael.PALETTE["magenta_mid"],
                1: _NS_nyxthrael.PALETTE["magenta_light"],
            }
            pygame.draw.line(surface, (*color_map[w], alpha),
                            (x, y + 40), (tx, ty), w)

    def _draw_ambush_foreground(surface, boss, x, y, timer, phase):
        """Dash streak effect and afterimages."""
        facing = boss.direction
        tx, ty = _NS_nyxthrael._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Streak from boss forward.
        start_x = x + facing * 20
        start_y = y - 4

        t = progress
        current_x = int(start_x + (tx - start_x) * t)
        current_y = int(start_y + (ty - start_y) * t)

        # Long streaking trail (like Q icon).
        for i in range(15):
            trail_t = max(0.0, t - i * 0.05)
            if trail_t <= 0:
                continue
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxthrael._alpha(240 - i * 15)

            # Streak line (from center perpendicular).
            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            perp_x = math.cos(perp_angle)
            perp_y = math.sin(perp_angle)

            size = max(1, 8 - i // 2)

            # Layered thick line.
            for layer_w, color_key in [
                (size + 2, "magenta_darkest"),
                (size, "magenta_dark"),
                (max(1, size - 2), "magenta_mid"),
                (1, "magenta_light"),
            ]:
                p1 = (px + int(perp_x * layer_w // 2),
                      py + int(perp_y * layer_w // 2))
                p2 = (px - int(perp_x * layer_w // 2),
                      py - int(perp_y * layer_w // 2))
                pygame.draw.line(surface,
                                (*_NS_nyxthrael.PALETTE[color_key], alpha),
                                p1, p2, 2)

        # Arrow-shape head at current position.
        head_angle = math.atan2(ty - start_y, tx - start_x)
        arrow_len = 20
        arrow_wid = 8

        # Arrow tip.
        tip = (current_x + int(math.cos(head_angle) * arrow_len),
               current_y + int(math.sin(head_angle) * arrow_len))
        # Arrow base.
        perp = head_angle + math.pi / 2
        base_a = (current_x + int(math.cos(perp) * arrow_wid),
                  current_y + int(math.sin(perp) * arrow_wid))
        base_b = (current_x - int(math.cos(perp) * arrow_wid),
                  current_y - int(math.sin(perp) * arrow_wid))

        alpha = _NS_nyxthrael._alpha(240)
        _NS_nyxthrael._poly(surface, (*_NS_nyxthrael.PALETTE["magenta_dark"], alpha),
                           [tip, base_a, base_b])
        _NS_nyxthrael._poly(surface, (*_NS_nyxthrael.PALETTE["magenta_mid"], alpha), [
            tip,
            (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
            (current_x, current_y),
        ])
        # Bright core.
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["magenta_light"],
                        (current_x, current_y), tip, 2)
        pygame.draw.line(surface, _NS_nyxthrael.PALETTE["magenta_shine"],
                        (current_x, current_y), tip, 1)

        # Sparkles along trail.
        for i in range(8):
            sp_t = (phase * 2 + i * 0.1) % 1.0
            sp_p = min(t, sp_t)
            spx = int(start_x + (tx - start_x) * sp_p)
            spy = int(start_y + (ty - start_y) * sp_p) + int(math.sin(phase * 4 + i) * 3)
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["magenta_hot"], (spx, spy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["magenta_shine"], (spx, spy, 1, 1))

    # ============================================================
    # SKILL: W - NIGHT FALL (dark vision-reducing area)
    # ============================================================
    def _draw_nightfall_ground(surface, boss, x, y, timer, phase):
        """Dark void circle on ground."""
        tx, ty = _NS_nyxthrael._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 3))

        if r > 5:
            # Very dark ellipse.
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["shadow"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["void_darkest"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["void_dark"], 160),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Edge glow.
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["void_mid"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["void_light"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 1)

    def _draw_nightfall_foreground(surface, boss, x, y, timer, phase):
        """Rising darkness and 'eye' warning markers."""
        tx, ty = _NS_nyxthrael._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 3))

        if r < 5:
            return

        # Central swirling darkness (like W icon - closed eye).
        center_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for layer_r in range(12, 0, -2):
            alpha = _NS_nyxthrael._alpha(220 * (12 - layer_r) / 12 * center_pulse)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["void_dark"], alpha),
                                   (tx, ty), layer_r)
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["shadow"], (tx, ty), 8)
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["void_darkest"], (tx, ty), 6)
        # Small purple iris.
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["void_mid"], (tx, ty), 3)
        _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["void_light"], (tx, ty), 2)
        pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["void_shine"], (tx, ty, 1, 1))

        # Swirling wisps around area.
        for i in range(14):
            wisp_angle = phase * 0.8 + i * math.pi / 7
            wisp_r = int(r * 0.6 + math.sin(phase * 2 + i) * 8)
            wx = tx + int(math.cos(wisp_angle) * wisp_r)
            wy = ty + int(math.sin(wisp_angle) * wisp_r * 0.5)
            alpha = _NS_nyxthrael._alpha(200)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["void_dark"], alpha),
                                   (wx, wy), 3)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["void_mid"], alpha),
                                   (wx, wy), 2)
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["void_light"], (wx, wy, 1, 1))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["void_hot"], (wx, wy, 1, 1))

        # Rising dark columns.
        num_columns = 5
        for i in range(num_columns):
            col_angle = i * math.pi * 2 / num_columns + phase * 0.15
            col_dist = int(r * 0.4)
            col_x = tx + int(math.cos(col_angle) * col_dist)
            col_y_base = ty + int(math.sin(col_angle) * col_dist * 0.4)

            for layer in range(5):
                layer_t = (phase * 0.6 + i * 0.3 + layer * 0.18) % 1.0
                layer_y = col_y_base - int(layer_t * 20)
                layer_alpha = _NS_nyxthrael._alpha(180 * (1 - layer_t))
                layer_w = int(5 + layer_t * 3)

                pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["void_dark"], layer_alpha),
                                    (col_x - layer_w, layer_y - 2, layer_w * 2, 4))
                pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["void_mid"], layer_alpha),
                                    (col_x - layer_w + 1, layer_y - 1,
                                     layer_w * 2 - 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["void_hot"], layer_alpha),
                                (col_x, layer_y, 1, 1))

    # ============================================================
    # SKILL: E - DARK NIGHT FALL (scythe sweep arc)
    # ============================================================
    def _draw_darknightfall_ground(surface, boss, x, y, timer, phase):
        """Ground shadow of sweep."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Arc shadow on ground.
        if progress > 0.2:
            for i in range(3):
                r = int(40 + i * 3)
                alpha = _NS_nyxthrael._alpha(180 - i * 40)
                # Only draw arc on facing side.
                arc_rect = (x - r, y + 40 - r // 3, r * 2, r * 2 // 3)
                pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["magenta_dark"], alpha),
                                    arc_rect, 2)

    def _draw_darknightfall_foreground(surface, boss, x, y, timer, phase):
        """Large magenta scythe arc sweep."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Sweep arc (matches E icon - curved slash).
        if progress < 0.15:
            # Wind-up.
            return

        t = (progress - 0.15) / 0.85
        # Arc sweeps forward.
        arc_progress = min(1.0, t * 1.5)

        cx_arc = x + facing * 20
        cy_arc = y
        arc_radius = 45

        # Full arc angle span.
        start_angle = -math.pi * 0.6 * facing
        end_angle = math.pi * 0.4 * facing
        current_end_angle = start_angle + (end_angle - start_angle) * arc_progress

        segments = 20
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            if t1 > arc_progress:
                break
            a1 = start_angle + (end_angle - start_angle) * t1
            a2 = start_angle + (end_angle - start_angle) * t2

            p1 = (cx_arc + int(math.cos(a1) * arc_radius),
                  cy_arc + int(math.sin(a1) * arc_radius))
            p2 = (cx_arc + int(math.cos(a2) * arc_radius),
                  cy_arc + int(math.sin(a2) * arc_radius))

            fade = 1.0 - (arc_progress - t1) * 0.6
            alpha = _NS_nyxthrael._alpha(240 * fade * (1 - t))

            # Layered thick sweep.
            for w, color_key in [
                (8, "magenta_darkest"),
                (6, "magenta_dark"),
                (4, "magenta_mid"),
                (2, "magenta_light"),
                (1, "magenta_shine"),
            ]:
                pygame.draw.line(surface,
                                (*_NS_nyxthrael.PALETTE[color_key], alpha),
                                p1, p2, w)

            # Ember sparks along arc.
            if i % 3 == 0:
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_hot"], alpha),
                                (p2[0], p2[1], 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_shine"], alpha),
                                (p2[0], p2[1], 1, 1))

        # Bright leading edge.
        lead_x = cx_arc + int(math.cos(current_end_angle) * arc_radius)
        lead_y = cy_arc + int(math.sin(current_end_angle) * arc_radius)
        for r in range(7, 0, -1):
            alpha = _NS_nyxthrael._alpha(200 * (7 - r) / 7 * (1 - t))
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["magenta_light"], alpha),
                                   (lead_x, lead_y), r)
        pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["magenta_shine"], (lead_x, lead_y, 1, 1))
        pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["white"], (lead_x, lead_y, 1, 1))

        # Radial particles from sweep.
        for i in range(12):
            p_angle = start_angle + (end_angle - start_angle) * (i / 12)
            p_t = (phase * 2 + i * 0.1) % 1.0
            p_r = arc_radius + int(p_t * 15)
            px_p = cx_arc + int(math.cos(p_angle) * p_r)
            py_p = cy_arc + int(math.sin(p_angle) * p_r)
            alpha = _NS_nyxthrael._alpha(180 * (1 - p_t) * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["magenta_hot"], alpha),
                                (px_p, py_p, 1, 1))

    # ============================================================
    # SKILL: R - SHADOW BRINGER (leap + crash with red beam)
    # ============================================================
    def _draw_shadowbringer_ground(surface, boss, x, y, timer, phase):
        """Impact circle at target."""
        tx, ty = _NS_nyxthrael._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Wind-up warning circle.
            t = progress / 0.4
            r = int(35 * t)
            alpha = _NS_nyxthrael._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["crimson_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["crimson_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Rotating runes.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["crimson_light"], (sx, sy, 2, 2))
        else:
            # Post-impact crimson pool.
            t = (progress - 0.4) / 0.6
            r = int(35 + t * 25)
            alpha = _NS_nyxthrael._alpha(230 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["crimson_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["crimson_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_nyxthrael.PALETTE["crimson_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Central bright spot.
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_light"], alpha),
                                   (tx, ty), max(1, r // 5))

    def _draw_shadowbringer_foreground(surface, boss, x, y, timer, phase):
        """Vertical red crashing beam from sky."""
        tx, ty = _NS_nyxthrael._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Wind-up: gathering energy above.
            t = progress / 0.4
            gather_y = ty - int((1 - t) * 80)
            gather_r = int(5 + t * 5)
            for r in range(gather_r + 4, 0, -1):
                alpha = _NS_nyxthrael._alpha(200 * (gather_r + 4 - r) / (gather_r + 4))
                _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_dark"], alpha),
                                       (tx, gather_y), r)
            _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["crimson_mid"], (tx, gather_y),
                                   gather_r - 2)
            _NS_nyxthrael._aacircle(surface, _NS_nyxthrael.PALETTE["crimson_light"], (tx, gather_y),
                                   max(1, gather_r - 4))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["crimson_shine"], (tx, gather_y, 1, 1))
        elif progress < 0.7:
            # CRASH PHASE: red beam from sky.
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)

            beam_top_y = max(0, ty - 240)

            for layer_i, (width, alpha_val) in enumerate([
                (16, 90), (12, 130), (8, 170), (4, 210), (2, 250),
            ]):
                actual_alpha = _NS_nyxthrael._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_nyxthrael.PALETTE["crimson_darkest"],
                    _NS_nyxthrael.PALETTE["crimson_dark"],
                    _NS_nyxthrael.PALETTE["crimson_mid"],
                    _NS_nyxthrael.PALETTE["crimson_light"],
                    _NS_nyxthrael.PALETTE["crimson_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                (tx - width // 2, beam_top_y,
                                 width, ty - beam_top_y))

            # Rising sparkles along beam.
            for i in range(18):
                spark_t = (phase * 2.5 + i * 0.12) % 1.0
                spark_y = ty - int(spark_t * (ty - beam_top_y))
                spark_x = tx + int(math.sin(phase * 5 + i) * 8)
                alpha = _NS_nyxthrael._alpha(240 * intensity * (1 - spark_t * 0.5))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["crimson_hot"], alpha),
                                (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["crimson_shine"], alpha),
                                (spark_x, spark_y, 1, 1))

            # Impact explosion.
            impact_r = int(18 + t * 30)
            impact_alpha = _NS_nyxthrael._alpha(240 * intensity)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_darkest"], impact_alpha),
                                   (tx, ty), impact_r + 3, 3)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_dark"], impact_alpha),
                                   (tx, ty), impact_r, 3)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_mid"], impact_alpha),
                                   (tx, ty), max(1, impact_r - 6), 2)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_light"], impact_alpha),
                                   (tx, ty), max(1, impact_r - 12), 1)
            _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_shine"], impact_alpha),
                                   (tx, ty), max(1, impact_r // 4))
            pygame.draw.rect(surface, _NS_nyxthrael.PALETTE["white"], (tx, ty, 1, 1))

            # Radial spike burst (like R icon - upward spikes).
            for i in range(8):
                angle_s = i * math.pi / 4 - math.pi / 2
                ray_len = int(impact_r * 1.5)
                ex = tx + int(math.cos(angle_s) * ray_len)
                ey = ty + int(math.sin(angle_s) * ray_len * 0.8)
                # Spike shape.
                perp_a = angle_s + math.pi / 2
                base_a = (tx + int(math.cos(perp_a) * 3),
                          ty + int(math.sin(perp_a) * 3))
                base_b = (tx - int(math.cos(perp_a) * 3),
                          ty - int(math.sin(perp_a) * 3))
                _NS_nyxthrael._poly(surface,
                                   (*_NS_nyxthrael.PALETTE["crimson_dark"], impact_alpha),
                                   [(ex, ey), base_a, base_b])
                pygame.draw.line(surface,
                                (*_NS_nyxthrael.PALETTE["crimson_light"], impact_alpha),
                                (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                (*_NS_nyxthrael.PALETTE["crimson_hot"], impact_alpha),
                                (ex, ey, 2, 2))
        else:
            # Aftermath: lingering red smoke.
            t = (progress - 0.7) / 0.3
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 22)
                ry = ty - int(rise_t * 32)
                alpha = _NS_nyxthrael._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_dark"], alpha),
                                           (rx, ry), 3)
                    _NS_nyxthrael._aacircle(surface, (*_NS_nyxthrael.PALETTE["crimson_mid"], alpha),
                                           (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_nyxthrael.PALETTE["crimson_light"], alpha),
                                    (rx, ry, 1, 1))


# ====================================================================
# sylvantheros.py
# ====================================================================

# ====================================================================
# SYLVANTHEROS - The Verdant Farseer (Mini Boss)
# ====================================================================


class _NS_sylvantheros:
    """Namespace sylvantheros - Nature druid mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Foliage cloak (leaf robe, main body)
        "leaf_darkest": (8, 22, 10),
        "leaf_dark": (25, 60, 28),
        "leaf_mid": (55, 110, 50),
        "leaf_light": (110, 175, 85),
        "leaf_edge": (170, 220, 120),
        "leaf_shine": (220, 245, 170),

        # Bark/wood skin (face, hands)
        "bark_darkest": (25, 15, 8),
        "bark_dark": (65, 42, 22),
        "bark_mid": (120, 85, 50),
        "bark_light": (175, 135, 85),
        "bark_shine": (220, 185, 130),

        # Antlers (bone-like brown)
        "antler_dark": (55, 40, 20),
        "antler_mid": (130, 100, 60),
        "antler_light": (200, 170, 115),
        "antler_shine": (240, 220, 170),

        # Beard/hair (blue-white mystical)
        "beard_dark": (60, 80, 110),
        "beard_mid": (140, 165, 195),
        "beard_light": (210, 225, 245),
        "beard_shine": (245, 250, 255),

        # Staff orb (glowing blue)
        "orb_darkest": (5, 15, 40),
        "orb_dark": (20, 60, 130),
        "orb_mid": (60, 130, 220),
        "orb_light": (140, 200, 255),
        "orb_shine": (220, 240, 255),

        # Nature magic (bright yellow-green - Wrath of Nature)
        "magic_darkest": (20, 40, 5),
        "magic_dark": (70, 130, 15),
        "magic_mid": (150, 210, 40),
        "magic_light": (210, 250, 90),
        "magic_hot": (245, 255, 160),
        "magic_shine": (255, 255, 230),

        # Eyes (glowing blue)
        "eye_socket": (5, 8, 15),
        "eye_dark": (15, 45, 90),
        "eye_mid": (80, 160, 230),
        "eye_light": (180, 230, 255),
        "eye_glow": (240, 250, 255),

        # Ground/roots
        "root_dark": (30, 20, 10),
        "root_mid": (70, 50, 25),

        # Mist
        "mist_dark": (20, 50, 15),
        "mist_mid": (70, 130, 45),
        "mist_light": (150, 210, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sylvantheros._clamp(color)
        if _NS_sylvantheros.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_sylvantheros._clamp(color)
        if _NS_sylvantheros.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_sylvantheros._clamp(color), points)

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
    def draw_sylvantheros(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sylvantheros._detect_moving(boss)
        _NS_sylvantheros._update_syl_attack_anim(boss)
        attacking = (
            getattr(boss, "_syl_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_sylvantheros._draw_nature_aura(surface, x, y, pulse)
        _NS_sylvantheros._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_sylvantheros._draw_sprout_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sylvantheros._draw_teleport_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sylvantheros._draw_treants_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sylvantheros._draw_wrath_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_sylvantheros._draw_syl_attack(surface, boss, x, y)
        elif moving:
            _NS_sylvantheros._draw_syl_float_move(surface, boss, x, y)
        else:
            _NS_sylvantheros._draw_syl_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_sylvantheros._draw_sprout_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sylvantheros._draw_teleport_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sylvantheros._draw_treants_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sylvantheros._draw_wrath_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_syl_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_syl_previous_timer", 0))
        active = bool(getattr(boss, "_syl_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._syl_attack_active = True
            boss._syl_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._syl_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._syl_attack_frame = int(
                getattr(boss, "_syl_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._syl_attack_active = False
            boss._syl_attack_frame = 0
            active = False

        boss._syl_previous_timer = timer
        boss._syl_attack_progress = (
            min(1.0, getattr(boss, "_syl_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_syl_last_x"):
            boss._syl_last_x = boss.x
            boss._syl_last_y = boss.y
            return False
        dx = abs(boss.x - boss._syl_last_x)
        dy = abs(boss.y - boss._syl_last_y)
        boss._syl_last_x = boss.x
        boss._syl_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING)
    # ============================================================
    def _draw_syl_idle(surface, boss, x, y):
        # Slow floating bob.
        float_bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_sylvantheros._draw_shadow(surface, x, y + 52)
        _NS_sylvantheros._draw_float_particles(surface, x, y + 40, boss.pulse)
        _NS_sylvantheros._draw_syl_body(surface, x, y - 6 + float_bob,
                                        boss.direction, boss.pulse, "idle")

    def _draw_syl_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        float_bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_sylvantheros._draw_shadow(surface, x + sway, y + 52)
        _NS_sylvantheros._draw_float_particles(surface, x + sway, y + 40, phase,
                                               trail=True, facing=boss.direction)
        _NS_sylvantheros._draw_syl_body(surface, x + sway, y - 8 + float_bob,
                                        boss.direction, phase, "move")

    def _draw_syl_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_syl_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_syl_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Range attack: staff raise → cast → recovery
        if progress < 0.3:
            t = progress / 0.3
            lift = int(t * 4)
            lunge = 0
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lift = int(4 - t * 2)
            lunge = int(t * 4) * facing
        else:
            t = (progress - 0.55) / 0.45
            lift = int(2 * (1 - t))
            lunge = int(4 * (1 - t)) * facing

        float_bob = int(math.sin(boss.pulse * 0.6) * 4)
        _NS_sylvantheros._draw_shadow(surface, x + lunge, y + 52)
        _NS_sylvantheros._draw_float_particles(surface, x + lunge, y + 40, boss.pulse,
                                               intense=True)
        _NS_sylvantheros._draw_syl_body(surface, x + lunge, y - 6 - lift + float_bob,
                                        facing, boss.pulse, "attack", progress)
        _NS_sylvantheros._draw_nature_bolt(surface, boss, x + lunge,
                                           y - 6 - lift + float_bob, progress)

    # ============================================================
    # BODY (Standing druid with leaf robe, antlers, staff)
    # ============================================================
    def _draw_syl_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw druid body: robe, arms, head with antlers, staff."""
        # Robe (bottom - trailing leaves) FIRST.
        _NS_sylvantheros._draw_leaf_robe(surface, cx, cy + 8, facing, phase)

        # Torso (foliage-covered).
        _NS_sylvantheros._draw_druid_torso(surface, cx, cy, facing, phase)

        # Off-hand arm (back).
        _NS_sylvantheros._draw_druid_arm(surface, cx - facing * 6, cy + 2, facing,
                                        phase, "back")

        # Head with antlers.
        _NS_sylvantheros._draw_druid_head(surface, cx, cy - 14, facing, phase)

        # Staff arm (front) and staff.
        staff_angle_offset = 0
        if action == "attack":
            if attack_progress < 0.3:
                staff_angle_offset = -attack_progress / 0.3 * 0.3
            elif attack_progress < 0.55:
                t = (attack_progress - 0.3) / 0.25
                staff_angle_offset = -0.3 + t * 0.5
            else:
                t = (attack_progress - 0.55) / 0.45
                staff_angle_offset = 0.2 * (1 - t)

        _NS_sylvantheros._draw_druid_arm(surface, cx + facing * 6, cy + 2, facing,
                                        phase, "front")
        _NS_sylvantheros._draw_druid_staff(surface, cx + facing * 10, cy - 2,
                                          facing, phase, staff_angle_offset, action,
                                          attack_progress)

    def _draw_leaf_robe(surface, cx, cy, facing, phase):
        """Trailing leaves at bottom (no legs, floating)."""
        sway = math.sin(phase * 0.5) * 2

        # Main robe silhouette (tapered, ends in leaves).
        robe_shape = [
            (cx - 12, cy - 8),
            (cx - 15, cy - 2),
            (cx - 14, cy + 6),
            (cx - 10, cy + 14 + int(sway)),
            (cx - 4, cy + 18),
            (cx + 4, cy + 17 - int(sway)),
            (cx + 10, cy + 15),
            (cx + 14, cy + 8),
            (cx + 15, cy + 2),
            (cx + 12, cy - 6),
        ]
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in robe_shape])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_darkest"], robe_shape)

        # Darker layer.
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
            (cx - 11, cy - 6),
            (cx - 13, cy),
            (cx - 12, cy + 8),
            (cx - 6, cy + 14),
            (cx + 4, cy + 13),
            (cx + 10, cy + 12),
            (cx + 13, cy + 6),
            (cx + 12, cy),
            (cx + 10, cy - 5),
        ])

        # Mid green.
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
            (cx - 9, cy - 4),
            (cx - 10, cy + 2),
            (cx - 6, cy + 10),
            (cx + 4, cy + 9),
            (cx + 8, cy + 8),
            (cx + 10, cy + 2),
            (cx + 8, cy - 3),
        ])

        # Individual leaf tips (fringe at bottom).
        leaf_positions = [
            (cx - 10, cy + 14, -1),
            (cx - 6, cy + 17, -1),
            (cx - 2, cy + 18, 0),
            (cx + 2, cy + 17, 0),
            (cx + 6, cy + 16, 1),
            (cx + 10, cy + 13, 1),
        ]
        for lx, ly, tilt in leaf_positions:
            leaf_sway = math.sin(phase * 0.8 + lx * 0.1) * 1
            ly_actual = ly + int(leaf_sway)
            # Leaf shape.
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
                (lx, ly_actual - 2),
                (lx + 2 + tilt, ly_actual),
                (lx, ly_actual + 3),
                (lx - 2 + tilt, ly_actual),
            ])
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
                (lx, ly_actual - 1),
                (lx + 1 + tilt, ly_actual),
                (lx, ly_actual + 2),
                (lx - 1 + tilt, ly_actual),
            ])
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["leaf_edge"],
                            (lx + tilt, ly_actual, 1, 1))

        # Belt (rope/vine).
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_dark"],
                        (cx - 11, cy - 7), (cx + 11, cy - 7), 2)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_mid"],
                        (cx - 11, cy - 7), (cx + 11, cy - 7), 1)
        # Belt buckle.
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["antler_mid"],
                        (cx - 2, cy - 8, 4, 3))
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["antler_light"],
                        (cx - 1, cy - 7, 2, 1))

    def _draw_druid_torso(surface, cx, cy, facing, phase):
        """Foliage-covered torso."""
        breath = math.sin(phase * 0.7) * 1

        # Torso base shape.
        torso_shape = [
            (cx - 10, cy - 6),
            (cx - 12, cy - 2),
            (cx - 11, cy + 6),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 11, cy + 6),
            (cx + 12, cy - 2),
            (cx + 10, cy - 6),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in torso_shape])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_darkest"], torso_shape)

        # Layered leaves on chest.
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
            (cx - 9, cy - 5),
            (cx - 10, cy - 1),
            (cx - 9, cy + 5),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 9, cy + 5),
            (cx + 10, cy - 1),
            (cx + 8, cy - 6),
            (cx - 5, cy - 7),
        ])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
            (cx - 7, cy - 4),
            (cx - 8, cy),
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 8, cy),
            (cx + 7, cy - 5),
            (cx - 3, cy - 6),
        ])

        # Center leaf highlight (V-shape at chest).
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_light"], [
            (cx - 4, cy - 3),
            (cx, cy + 4),
            (cx + 4, cy - 3),
            (cx + 2, cy - 4),
            (cx, cy - 1),
            (cx - 2, cy - 4),
        ])

        # Individual leaf spikes on shoulders.
        for side in [-1, 1]:
            sx = cx + side * 10
            sy = cy - 4
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
                (sx, sy),
                (sx + side * 3, sy - 2),
                (sx + side * 4, sy + 1),
                (sx + side * 2, sy + 3),
            ])
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
                (sx + side, sy),
                (sx + side * 2, sy - 1),
                (sx + side * 3, sy + 1),
                (sx + side, sy + 2),
            ])
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["leaf_edge"],
                            (sx + side * 2, sy, 1, 1))

        # Small glowing orb on chest (life essence).
        chest_pulse = math.sin(phase * 2) * 0.3 + 0.7
        cox, coy = cx, cy + 2
        for r in range(4, 0, -1):
            alpha = _NS_sylvantheros._alpha(180 * (4 - r) / 4 * chest_pulse)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_mid"], alpha),
                                       (cox, coy), r)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_light"], (cox, coy), 2)
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["orb_shine"], (cox, coy, 1, 1))

    def _draw_druid_arm(surface, cx, cy, facing, phase, side):
        """Arm (draped in leaves)."""
        sway = math.sin(phase * 0.4) * 1
        # Simple bark hand at end.
        if side == "back":
            hand_x = cx - facing * 4
            hand_y = cy + 8 + int(sway)
        else:
            hand_x = cx + facing * 4
            hand_y = cy + 6 + int(sway)

        # Arm shape (draped foliage).
        arm_shape = [
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (hand_x + 2, hand_y - 2),
            (hand_x + 2, hand_y + 2),
            (hand_x - 2, hand_y + 2),
            (cx - 3, cy + 2),
        ]
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_darkest"], arm_shape)
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
            (cx - 1, cy - 1),
            (cx + 2, cy - 1),
            (hand_x + 1, hand_y - 1),
            (hand_x + 1, hand_y + 1),
            (hand_x - 1, hand_y + 1),
            (cx - 2, cy + 1),
        ])

        # Bark hand.
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["bark_darkest"],
                                   (hand_x, hand_y), 3)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["bark_dark"],
                                   (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["bark_mid"],
                        (hand_x, hand_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["bark_light"],
                        (hand_x + 1, hand_y - 1, 1, 1))

    def _draw_druid_head(surface, cx, cy, facing, phase):
        """Wise druid head with antlers, beard, glowing eyes."""
        # Head shape (bark-like).
        head_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy + 2),
            (cx - 6, cy + 7),
            (cx - 2, cy + 9),
            (cx + 2, cy + 9),
            (cx + 6, cy + 7),
            (cx + 8, cy + 2),
            (cx + 7, cy - 2),
            (cx + 5, cy - 5),
            (cx - 5, cy - 5),
        ]
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in head_shape])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["bark_darkest"], head_shape)

        # Bark skin.
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["bark_dark"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["bark_mid"], [
            (cx - 5, cy),
            (cx - 5, cy + 3),
            (cx + 5, cy + 3),
            (cx + 5, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])

        # Bark texture (grain lines).
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_darkest"],
                        (cx - 4, cy + 1), (cx - 3, cy + 4), 1)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_darkest"],
                        (cx + 4, cy + 1), (cx + 3, cy + 4), 1)

        # Leaves on top of head (crown).
        for i, (lx_off, ly_off) in enumerate([(-4, -4), (-1, -6), (2, -6), (5, -4)]):
            sway = math.sin(phase * 0.6 + i) * 1
            lx = cx + lx_off
            ly = cy + ly_off + int(sway)
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
                (lx, ly),
                (lx - 2, ly + 2),
                (lx, ly + 3),
                (lx + 2, ly + 2),
            ])
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
                (lx, ly + 1),
                (lx - 1, ly + 2),
                (lx, ly + 2),
                (lx + 1, ly + 2),
            ])

        # ANTLERS (large branching, glowing tips).
        _NS_sylvantheros._draw_antlers(surface, cx, cy - 4, phase)

        # Glowing blue eyes.
        _NS_sylvantheros._draw_druid_eyes(surface, cx, cy + 1, facing, phase)

        # Beard (blue-white, flowing).
        _NS_sylvantheros._draw_druid_beard(surface, cx, cy + 5, facing, phase)

    def _draw_antlers(surface, cx, cy, phase):
        """Large branching antlers with glowing tips."""
        sway = math.sin(phase * 0.4) * 1

        for side in [-1, 1]:
            # Main antler stem.
            base_x = cx + side * 4
            base_y = cy
            stem_tip_x = base_x + side * 4
            stem_tip_y = base_y - 8 + int(sway)

            # Main branch shadow.
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (stem_tip_x + 1, stem_tip_y + 1), 3)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_dark"],
                            (base_x, base_y), (stem_tip_x, stem_tip_y), 3)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_mid"],
                            (base_x, base_y), (stem_tip_x, stem_tip_y), 2)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_light"],
                            (base_x, base_y - 1), (stem_tip_x, stem_tip_y - 1), 1)

            # Branch 1 (lower outward).
            b1_start = (base_x + side * 2, base_y - 3)
            b1_end = (base_x + side * 7, base_y - 5)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_dark"],
                            b1_start, b1_end, 2)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_mid"],
                            b1_start, b1_end, 1)

            # Branch 2 (upper inward).
            b2_start = (base_x + side * 3, base_y - 6)
            b2_end = (base_x + side * 6, base_y - 10)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_dark"],
                            b2_start, b2_end, 2)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_mid"],
                            b2_start, b2_end, 1)

            # Branch 3 (top).
            b3_start = stem_tip_x, stem_tip_y
            b3_end = (stem_tip_x + side * 3, stem_tip_y - 3)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_dark"],
                            b3_start, b3_end, 2)
            pygame.draw.line(surface, _NS_sylvantheros.PALETTE["antler_mid"],
                            b3_start, b3_end, 1)

            # Glowing tips.
            for tip in [stem_tip_x, stem_tip_y], [b1_end[0], b1_end[1]], \
                       [b2_end[0], b2_end[1]], [b3_end[0], b3_end[1]]:
                glow_pulse = math.sin(phase * 2 + side) * 0.3 + 0.7
                for r in range(3, 0, -1):
                    alpha = _NS_sylvantheros._alpha(150 * (3 - r) / 3 * glow_pulse)
                    _NS_sylvantheros._aacircle(surface,
                                              (*_NS_sylvantheros.PALETTE["magic_light"], alpha),
                                              tip, r)
                pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["antler_shine"],
                                (tip[0], tip[1], 1, 1))
                pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_hot"],
                                (tip[0], tip[1], 1, 1))

    def _draw_druid_eyes(surface, cx, cy, facing, phase):
        """Glowing blue eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy

            # Eye socket.
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["eye_socket"],
                            (ex - 1, ey - 1, 2, 2))

            # Glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_sylvantheros._alpha(120 * (4 - r) / 4 * pulse)
                _NS_sylvantheros._aacircle(surface,
                                          (*_NS_sylvantheros.PALETTE["eye_mid"], alpha),
                                          (ex, ey), r)

            # Bright core.
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["eye_light"],
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["eye_glow"],
                            (ex, ey, 1, 1))

    def _draw_druid_beard(surface, cx, cy, facing, phase):
        """Long flowing blue-white beard."""
        sway = math.sin(phase * 0.5) * 1

        # Beard base shape.
        beard_shape = [
            (cx - 4, cy - 1),
            (cx - 5, cy + 2),
            (cx - 4, cy + 6),
            (cx - 2, cy + 9 + int(sway)),
            (cx, cy + 10),
            (cx + 2, cy + 9 + int(sway)),
            (cx + 4, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
        ]
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["shadow_deep"],
                              [(px + 1, py + 1) for px, py in beard_shape])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["beard_dark"], beard_shape)
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["beard_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 3),
            (cx - 2, cy + 7),
            (cx, cy + 8),
            (cx + 2, cy + 7),
            (cx + 4, cy + 3),
            (cx + 3, cy),
        ])
        _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["beard_light"], [
            (cx - 2, cy + 1),
            (cx - 2, cy + 5),
            (cx, cy + 7),
            (cx + 2, cy + 5),
            (cx + 2, cy + 1),
        ])
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["beard_shine"],
                        (cx, cy + 4, 1, 1))

        # Strand tips.
        for i, dx in enumerate([-2, 0, 2]):
            strand_sway = math.sin(phase * 0.7 + i) * 1
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["beard_light"],
                            (cx + dx, cy + 9 + int(strand_sway), 1, 2))

    def _draw_druid_staff(surface, cx, cy, facing, phase, angle_offset, action,
                         attack_progress):
        """Staff with glowing blue orb on top."""
        # Base angle: pointing up and slightly outward.
        base_angle = -math.pi / 2 - 0.1 * facing + angle_offset * facing

        staff_length = 32
        base_x = cx + facing * 2
        base_y = cy + 6
        tip_x = base_x + int(math.cos(base_angle) * staff_length)
        tip_y = base_y + int(math.sin(base_angle) * staff_length)

        # Staff shaft shadow.
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["shadow_deep"],
                        (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 3)
        # Staff shaft (bark).
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_darkest"],
                        (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_dark"],
                        (base_x, base_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_mid"],
                        (base_x, base_y), (tip_x, tip_y), 1)

        # Bark texture (segments).
        for t_seg in [0.25, 0.5, 0.75]:
            seg_x = int(base_x + (tip_x - base_x) * t_seg)
            seg_y = int(base_y + (tip_y - base_y) * t_seg)
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["bark_darkest"],
                            (seg_x - 1, seg_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["bark_light"],
                            (seg_x, seg_y, 1, 1))

        # Orb holder (curved bracket at tip).
        perp_angle = base_angle + math.pi / 2
        bracket_a = (tip_x + int(math.cos(perp_angle) * 3),
                     tip_y + int(math.sin(perp_angle) * 3))
        bracket_b = (tip_x - int(math.cos(perp_angle) * 3),
                     tip_y - int(math.sin(perp_angle) * 3))
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_dark"],
                        bracket_a, bracket_b, 2)

        # ORB at tip (glowing blue).
        orb_x = tip_x + int(math.cos(base_angle) * 4)
        orb_y = tip_y + int(math.sin(base_angle) * 4)

        # Boost glow during attack.
        boost = 1.0
        if action == "attack" and 0.3 < attack_progress < 0.7:
            boost = 1.5

        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Big glow aura.
        for r in range(9, 0, -1):
            alpha = _NS_sylvantheros._alpha(140 * (9 - r) / 9 * pulse * boost)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_mid"], alpha),
                                       (orb_x, orb_y), r)

        # Orb layers.
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_darkest"],
                                   (orb_x, orb_y), 5)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_dark"],
                                   (orb_x, orb_y), 4)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_mid"],
                                   (orb_x, orb_y), 3)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_light"],
                                   (orb_x, orb_y), 2)
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["orb_shine"],
                        (orb_x, orb_y, 1, 1))
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["white"],
                        (orb_x, orb_y, 1, 1))

        # Orbit sparkles.
        for i in range(4):
            sp_angle = phase * 2 + i * math.pi / 2
            spx = orb_x + int(math.cos(sp_angle) * 6)
            spy = orb_y + int(math.sin(sp_angle) * 6)
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["orb_shine"], (spx, spy, 1, 1))

    # ============================================================
    # ATTACK: Nature bolt (blue-green magic projectile)
    # ============================================================
    def _draw_nature_bolt(surface, boss, x, y, progress):
        """Blue-green orb projectile from staff."""
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_sylvantheros._target_position(boss, x, y)

        # Launch point at staff tip.
        start_x = x + facing * 22
        start_y = y - 26

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Comet trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_sylvantheros._alpha(220 - i * 24)
            size = max(1, 6 - i)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_darkest"], alpha),
                                       (px, py), size)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_dark"], alpha),
                                       (px, py), max(1, size - 1))
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_mid"], alpha),
                                       (px, py), max(1, size - 2))
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_light"], alpha),
                                       (px, py), max(1, size - 3))

            if i < 3:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_hot"], alpha),
                                    (spark_x, spark_y, 1, 1))

        # Bolt head.
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_darkest"], (bx, by), 7)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_dark"], (bx, by), 5)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_mid"], (bx, by), 3)
        _NS_sylvantheros._aacircle(surface, _NS_sylvantheros.PALETTE["orb_light"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["orb_shine"], (bx, by, 1, 1))
        pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(6 + st * 20)
            alpha = _NS_sylvantheros._alpha(230 * (1 - st))
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_dark"], alpha),
                                       (tx, ty), radius + 2, 2)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_mid"], alpha),
                                       (tx, ty), radius, 2)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["orb_light"], alpha),
                                       (tx, ty), max(1, radius - 6), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_hot"], alpha),
                                (ex, ey, 2, 2))

    # ============================================================
    # FLOATING PARTICLES (leaves, sparkles below feet)
    # ============================================================
    def _draw_float_particles(surface, cx, cy, phase, trail=False, facing=1,
                              intense=False):
        """Floating leaves and green sparkles below (levitation FX)."""
        strength = 1.5 if intense else 1.0

        # Ground glow ellipse.
        glow = pygame.Surface((100, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(24, 3, -2):
            alpha = _NS_sylvantheros._alpha((24 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_sylvantheros.PALETTE["mist_dark"], alpha),
                                    (50 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)))
        for r in range(16, 3, -2):
            alpha = _NS_sylvantheros._alpha((16 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_sylvantheros.PALETTE["mist_mid"], alpha),
                                    (50 - r, 15 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 50, cy - 8))

        # Rising leaves (spinning).
        for i, offset in enumerate([-20, -12, -4, 4, 12, 20]):
            t = (phase * 0.5 + i * 0.15) % 1.0
            lx = cx + offset + int(math.sin(phase * 2 + i) * 3)
            ly = cy + 4 - int(t * 22)
            spin = int((phase * 3 + i) % 4)
            alpha = _NS_sylvantheros._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue

            # Small spinning leaf.
            if spin < 2:
                _NS_sylvantheros._poly(surface, (*_NS_sylvantheros.PALETTE["leaf_dark"], alpha), [
                    (lx, ly - 2),
                    (lx + 2, ly),
                    (lx, ly + 2),
                    (lx - 2, ly),
                ])
                _NS_sylvantheros._poly(surface, (*_NS_sylvantheros.PALETTE["leaf_mid"], alpha), [
                    (lx, ly - 1),
                    (lx + 1, ly),
                    (lx, ly + 1),
                    (lx - 1, ly),
                ])
            else:
                # Edge-on view.
                pygame.draw.line(surface, (*_NS_sylvantheros.PALETTE["leaf_mid"], alpha),
                                (lx - 2, ly), (lx + 2, ly), 1)
            pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["leaf_edge"], alpha), (lx, ly, 1, 1))

        # Green sparkles.
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.1) % 1.0
            sx = cx - 24 + i * 5 + int(math.sin(phase + i) * 4)
            sy = cy + 2 - int(spark_t * 20)
            alpha = _NS_sylvantheros._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_mid"], alpha),
                                (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_hot"], alpha),
                                (sx, sy, 1, 1))

        # Trail behind (when moving).
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_sylvantheros._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["mist_dark"], alpha),
                                           (sx, sy), max(2, 6 - i))
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["mist_mid"], alpha),
                                           (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_light"], alpha),
                                (sx, sy - 1, 2, 2))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 25), pygame.SRCALPHA)
        for r in range(11, 0, -1):
            alpha = max(0, (11 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 12 - r, 90 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 160), (5, 6, 100, 12))
        pygame.draw.ellipse(shadow, (25, 55, 15, 100), (12, 8, 86, 8))
        surface.blit(shadow, (x - 55, y - 12))

    def _draw_nature_aura(surface, x, y, phase):
        """Green nature aura around druid."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for r in range(80, 5, -5):
            alpha = _NS_sylvantheros._alpha((80 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_sylvantheros._aacircle(aura, (*_NS_sylvantheros.PALETTE["mist_dark"], alpha),
                                           (90, 80), r)
        for r in range(50, 5, -4):
            alpha = _NS_sylvantheros._alpha((50 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_sylvantheros._aacircle(aura, (*_NS_sylvantheros.PALETTE["mist_mid"], alpha),
                                           (90, 80), r)
        for r in range(30, 5, -3):
            alpha = _NS_sylvantheros._alpha((30 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_sylvantheros._aacircle(aura, (*_NS_sylvantheros.PALETTE["orb_dark"], alpha),
                                           (90, 80), r)
        surface.blit(aura, (x - 90, y - 80))

        # Floating leaves.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
                (sx, sy - 1), (sx + 1, sy), (sx, sy + 1), (sx - 1, sy),
            ])
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["leaf_edge"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring under druid."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_sylvantheros.PALETTE["mist_dark"], 200),
                            (5, 14, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_sylvantheros.PALETTE["magic_darkest"], 220),
                            (12, 16, 126, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_sylvantheros.PALETTE["magic_dark"], 230),
                            (22, 18, 106, 14), 1)
        pygame.draw.ellipse(ring, (*_NS_sylvantheros.PALETTE["orb_dark"], 180),
                            (35, 20, 80, 10), 1)

        # Runes.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 42)
            y1 = 25 + int(math.sin(angle) * 7)
            x2 = 75 + int(math.cos(angle) * 60)
            y2 = 25 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_sylvantheros.PALETTE["magic_light"], 220),
                            (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_sylvantheros.PALETTE["magic_hot"],
                                       _NS_sylvantheros._alpha(150 * pulse)),
                                (14, 10, 122, 32), 1)
        surface.blit(ring, (x - 75, y - 23))

    # ============================================================
    # SKILL: Q - SPROUT (roots/vines trapping target)
    # ============================================================
    def _draw_sprout_ground(surface, boss, x, y, timer, phase):
        """Growing tree/vines at target."""
        tx, ty = _NS_sylvantheros._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(20 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_dark"], 180),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2))

    def _draw_sprout_foreground(surface, boss, x, y, timer, phase):
        """Vines/tree grown around target."""
        tx, ty = _NS_sylvantheros._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        growth = min(1.0, progress * 2.5)

        # Central trunk.
        trunk_h = int(28 * growth)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_darkest"],
                        (tx + 1, ty + 1), (tx + 1, ty - trunk_h + 1), 4)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_dark"],
                        (tx, ty), (tx, ty - trunk_h), 3)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_mid"],
                        (tx, ty), (tx, ty - trunk_h), 2)
        pygame.draw.line(surface, _NS_sylvantheros.PALETTE["bark_light"],
                        (tx - 1, ty - 5), (tx - 1, ty - trunk_h + 5), 1)

        # Curved vines around.
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            vine_len = int(20 * growth)
            prev = (tx, ty)
            for step in range(1, 6):
                t = step / 5
                curve_x = int(math.sin(t * math.pi + angle) * 12)
                curve_y = int(-t * vine_len)
                new_pt = (tx + curve_x, ty + curve_y)
                pygame.draw.line(surface, _NS_sylvantheros.PALETTE["leaf_dark"],
                                prev, new_pt, 2)
                pygame.draw.line(surface, _NS_sylvantheros.PALETTE["leaf_mid"],
                                prev, new_pt, 1)
                prev = new_pt

            # Leaf at tip.
            tip = prev
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_dark"], [
                (tip[0], tip[1] - 2),
                (tip[0] + 3, tip[1]),
                (tip[0], tip[1] + 3),
                (tip[0] - 3, tip[1]),
            ])
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["leaf_mid"], [
                (tip[0], tip[1] - 1),
                (tip[0] + 2, tip[1]),
                (tip[0], tip[1] + 2),
                (tip[0] - 2, tip[1]),
            ])
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["leaf_edge"],
                            (tip[0], tip[1], 1, 1))

        # Sparkling magic on vines.
        for i in range(6):
            spark_angle = phase * 2 + i * math.pi / 3
            sx = tx + int(math.cos(spark_angle) * 12)
            sy = ty - trunk_h // 2 + int(math.sin(spark_angle) * 8)
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_hot"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL: W - TELEPORTATION (channeling beam of light)
    # ============================================================
    def _draw_teleport_ground(surface, boss, x, y, timer, phase):
        """Bright circle under boss (channeling)."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        for i in range(3):
            r = int(28 + i * 6 + math.sin(phase * 2) * 2)
            alpha = _NS_sylvantheros._alpha(200 - i * 50)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_mid"], alpha),
                                       (x, y + 40), r, 2)
            _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_light"], alpha),
                                       (x, y + 40), r, 1)

        # Inner ring runes.
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            rx = x + int(math.cos(angle) * 22)
            ry = y + 40 + int(math.sin(angle) * 8)
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_hot"], (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_shine"], (rx, ry, 1, 1))

    def _draw_teleport_foreground(surface, boss, x, y, timer, phase):
        """Vertical beam of light rising from boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi) if progress < 1 else 0

        # Beam from ground upward.
        beam_top_y = max(0, y - 150)

        for layer_i, (width, alpha_val) in enumerate([
            (10, 80), (6, 120), (3, 180), (1, 240),
        ]):
            actual_alpha = _NS_sylvantheros._alpha(alpha_val * intensity)
            if actual_alpha <= 0:
                continue
            colors = [
                _NS_sylvantheros.PALETTE["magic_dark"],
                _NS_sylvantheros.PALETTE["magic_mid"],
                _NS_sylvantheros.PALETTE["magic_light"],
                _NS_sylvantheros.PALETTE["magic_shine"],
            ]
            color = colors[min(layer_i, 3)]
            pygame.draw.rect(surface, (*color, actual_alpha),
                            (x - width // 2, beam_top_y, width, y + 40 - beam_top_y))

        # Rising sparkles.
        for i in range(12):
            spark_t = (phase * 2 + i * 0.15) % 1.0
            spark_y = y + 40 - int(spark_t * (y + 40 - beam_top_y))
            spark_x = x + int(math.sin(phase * 4 + i) * 6)
            alpha = _NS_sylvantheros._alpha(230 * intensity * (1 - spark_t * 0.5))
            pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_hot"], alpha),
                            (spark_x, spark_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_shine"], alpha),
                            (spark_x, spark_y, 1, 1))

    # ============================================================
    # SKILL: E - NATURE'S CALL (summoning treants)
    # ============================================================
    def _draw_treants_ground(surface, boss, x, y, timer, phase):
        """Ground marks where treants spawn."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        facing = boss.direction
        # 3 spawn positions.
        positions = [
            (x + facing * 60, y + 40),
            (x + facing * 90, y + 45),
            (x + facing * 40, y + 42),
        ]
        for i, (px, py) in enumerate(positions):
            local_progress = max(0, min(1, (progress - i * 0.15) * 2))
            if local_progress <= 0:
                continue
            r = int(12 * local_progress)
            pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_darkest"], 200),
                                (px - r, py - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_dark"], 180),
                                (px - r + 2, py - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2))

    def _draw_treants_foreground(surface, boss, x, y, timer, phase):
        """Treants rising from ground."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        facing = boss.direction
        positions = [
            (x + facing * 60, y + 40, 0),
            (x + facing * 90, y + 45, 1),
            (x + facing * 40, y + 42, 2),
        ]

        for px, py, idx in positions:
            local_progress = max(0, min(1, (progress - idx * 0.15) * 2))
            if local_progress <= 0:
                continue

            growth = local_progress
            trunk_h = int(24 * growth)
            trunk_w = 6

            # Trunk shadow.
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["shadow_deep"], [
                (px - trunk_w // 2 + 2, py + 2),
                (px + trunk_w // 2 + 2, py + 2),
                (px + trunk_w // 2 + 2, py - trunk_h + 2),
                (px - trunk_w // 2 + 2, py - trunk_h + 2),
            ])

            # Trunk.
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["bark_darkest"], [
                (px - trunk_w // 2, py),
                (px + trunk_w // 2, py),
                (px + trunk_w // 2 + 1, py - trunk_h),
                (px - trunk_w // 2 - 1, py - trunk_h),
            ])
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["bark_dark"], [
                (px - trunk_w // 2 + 1, py),
                (px + trunk_w // 2 - 1, py),
                (px + trunk_w // 2, py - trunk_h),
                (px - trunk_w // 2, py - trunk_h),
            ])
            _NS_sylvantheros._poly(surface, _NS_sylvantheros.PALETTE["bark_mid"], [
                (px - 1, py),
                (px + 1, py),
                (px + 2, py - trunk_h),
                (px - 2, py - trunk_h),
            ])

            # Foliage crown.
            if growth > 0.5:
                foliage_size = int(10 * (growth - 0.5) * 2)
                if foliage_size > 2:
                    for r in range(foliage_size, 0, -1):
                        color_i = (foliage_size - r) / foliage_size
                        if color_i < 0.3:
                            color = _NS_sylvantheros.PALETTE["leaf_darkest"]
                        elif color_i < 0.6:
                            color = _NS_sylvantheros.PALETTE["leaf_dark"]
                        else:
                            color = _NS_sylvantheros.PALETTE["leaf_mid"]
                        _NS_sylvantheros._aacircle(surface, color, (px, py - trunk_h), r)
                    pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["leaf_edge"],
                                    (px, py - trunk_h, 1, 1))

                    # Angry eyes on treant.
                    pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["eye_socket"],
                                    (px - 2, py - trunk_h + 2, 1, 1))
                    pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["eye_socket"],
                                    (px + 1, py - trunk_h + 2, 1, 1))
                    pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_light"],
                                    (px - 2, py - trunk_h + 2, 1, 1))
                    pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_light"],
                                    (px + 1, py - trunk_h + 2, 1, 1))

            # Small magic sparkles.
            if growth < 1:
                for i in range(3):
                    sp_angle = phase * 2 + i * math.pi * 2 / 3 + idx
                    spx = px + int(math.cos(sp_angle) * 8)
                    spy = py - trunk_h // 2 + int(math.sin(sp_angle) * 8)
                    pygame.draw.rect(surface, _NS_sylvantheros.PALETTE["magic_hot"], (spx, spy, 1, 1))

    # ============================================================
    # SKILL: R - WRATH OF NATURE (lightning bolts from sky)
    # ============================================================
    def _draw_wrath_ground(surface, boss, x, y, timer, phase):
        """Multiple impact circles on ground."""
        tx, ty = _NS_sylvantheros._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple strike positions.
        strikes = [
            (tx, ty, 0.0),
            (tx - 40, ty + 5, 0.15),
            (tx + 40, ty - 3, 0.25),
            (tx - 20, ty + 20, 0.35),
            (tx + 25, ty + 15, 0.4),
        ]

        for sx, sy, delay in strikes:
            local_progress = max(0, min(1, (progress - delay) * 2))
            if local_progress <= 0:
                continue

            if local_progress < 0.3:
                # Warning circle.
                t = local_progress / 0.3
                r = int(20 * t)
                alpha = _NS_sylvantheros._alpha(180 * t)
                pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_darkest"], alpha),
                                    (sx - r, sy - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_mid"], alpha),
                                    (sx - r + 2, sy - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)
            else:
                # Impact pool.
                t = (local_progress - 0.3) / 0.7
                r = int(20 + t * 15)
                alpha = _NS_sylvantheros._alpha(220 * (1 - t * 0.5))
                pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_darkest"], alpha),
                                    (sx - r, sy - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_dark"], alpha),
                                    (sx - r + 2, sy - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2))
                pygame.draw.ellipse(surface, (*_NS_sylvantheros.PALETTE["magic_mid"], alpha),
                                    (sx - r + 6, sy - r // 3 + 3,
                                     r * 2 - 12, r * 2 // 3 - 6))

    def _draw_wrath_foreground(surface, boss, x, y, timer, phase):
        """Yellow-green lightning bolts crashing down from sky."""
        tx, ty = _NS_sylvantheros._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        strikes = [
            (tx, ty, 0.0),
            (tx - 40, ty + 5, 0.15),
            (tx + 40, ty - 3, 0.25),
            (tx - 20, ty + 20, 0.35),
            (tx + 25, ty + 15, 0.4),
        ]

        for sx, sy, delay in strikes:
            local_progress = max(0, min(1, (progress - delay) * 2))
            if local_progress <= 0 or local_progress > 0.9:
                continue

            if 0.3 <= local_progress < 0.6:
                # LIGHTNING BOLT.
                t = (local_progress - 0.3) / 0.3
                intensity = math.sin(t * math.pi)
                beam_top_y = max(0, sy - 220)

                # Jagged lightning path.
                segments = 12
                prev_x = sx
                prev_y = beam_top_y
                bolt_points = [(prev_x, prev_y)]
                for seg in range(1, segments + 1):
                    seg_t = seg / segments
                    seg_y = int(beam_top_y + (sy - beam_top_y) * seg_t)
                    seg_x = sx + int(math.sin(seg * 2.5 + phase * 10) * 6 * (1 - seg_t))
                    bolt_points.append((seg_x, seg_y))

                # Draw bolt layers.
                for layer_i, (width, alpha_val) in enumerate([
                    (7, 80), (5, 130), (3, 180), (1, 255),
                ]):
                    actual_alpha = _NS_sylvantheros._alpha(alpha_val * intensity)
                    if actual_alpha <= 0:
                        continue
                    colors = [
                        _NS_sylvantheros.PALETTE["magic_dark"],
                        _NS_sylvantheros.PALETTE["magic_mid"],
                        _NS_sylvantheros.PALETTE["magic_light"],
                        _NS_sylvantheros.PALETTE["magic_shine"],
                    ]
                    color = colors[min(layer_i, 3)]
                    for i in range(len(bolt_points) - 1):
                        pygame.draw.line(surface, (*color, actual_alpha),
                                        bolt_points[i], bolt_points[i + 1], width)

                # Impact burst.
                impact_r = int(12 + t * 20)
                impact_alpha = _NS_sylvantheros._alpha(240 * intensity)
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_darkest"], impact_alpha),
                                           (sx, sy), impact_r + 2, 2)
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_dark"], impact_alpha),
                                           (sx, sy), impact_r, 2)
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_mid"], impact_alpha),
                                           (sx, sy), max(1, impact_r - 5), 1)
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_light"], impact_alpha),
                                           (sx, sy), max(1, impact_r - 10))
                _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_shine"], impact_alpha),
                                           (sx, sy), max(1, impact_r // 4))

                # Radial sparks.
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = sx + int(math.cos(angle_s) * impact_r)
                    ey = sy + int(math.sin(angle_s) * impact_r * 0.7)
                    pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_hot"], impact_alpha),
                                    (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_shine"], impact_alpha),
                                    (ex, ey, 1, 1))
            elif local_progress >= 0.6:
                # Aftermath sparkles.
                t = (local_progress - 0.6) / 0.3
                for i in range(6):
                    rise_t = (phase * 0.8 + i * 0.15) % 1.0
                    rx = sx + int(math.sin(phase + i) * 15)
                    ry = sy - int(rise_t * 24)
                    alpha = _NS_sylvantheros._alpha(200 * (1 - t) * (1 - rise_t))
                    if alpha > 0:
                        _NS_sylvantheros._aacircle(surface, (*_NS_sylvantheros.PALETTE["magic_dark"], alpha),
                                                   (rx, ry), 2)
                        pygame.draw.rect(surface, (*_NS_sylvantheros.PALETTE["magic_light"], alpha),
                                        (rx, ry, 1, 1))


# ====================================================================
# vaelindra.py
# ====================================================================

# ====================================================================
# VAELINDRA - The Violet Sovereign (TRUE BOSS)
# ====================================================================


class _NS_vaelindra:
    """Namespace vaelindra - Noble mage-fighter TRUE BOSS."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (elegant pale)
        "skin_darkest": (130, 90, 85),
        "skin_dark": (200, 160, 145),
        "skin_mid": (240, 210, 195),
        "skin_light": (255, 235, 225),
        "skin_shine": (255, 250, 245),

        # Golden hair (long, flowing)
        "hair_darkest": (55, 30, 10),
        "hair_dark": (120, 75, 25),
        "hair_mid": (200, 145, 55),
        "hair_light": (245, 205, 115),
        "hair_shine": (255, 240, 180),

        # Violet gown (main dress body)
        "gown_darkest": (15, 5, 35),
        "gown_dark": (40, 15, 80),
        "gown_mid": (85, 40, 155),
        "gown_light": (155, 100, 220),
        "gown_edge": (200, 160, 245),
        "gown_shine": (240, 220, 255),

        # White inner dress (chemise)
        "inner_dark": (140, 130, 165),
        "inner_mid": (210, 200, 230),
        "inner_light": (245, 240, 255),

        # Bright violet magic (main power color)
        "magic_darkest": (30, 5, 55),
        "magic_dark": (85, 20, 145),
        "magic_mid": (170, 55, 230),
        "magic_light": (220, 130, 255),
        "magic_hot": (245, 190, 255),
        "magic_shine": (255, 235, 255),

        # Gold accents (ornaments, belt, headband)
        "gold_darkest": (60, 40, 10),
        "gold_dark": (135, 95, 25),
        "gold_mid": (210, 165, 55),
        "gold_light": (250, 220, 130),
        "gold_shine": (255, 245, 200),

        # Eyes (bright violet-blue)
        "eye_socket": (5, 5, 15),
        "eye_dark": (25, 40, 90),
        "eye_mid": (100, 130, 220),
        "eye_light": (200, 220, 255),
        "eye_glow": (250, 245, 255),

        # Butterfly wing (psionic)
        "wing_darkest": (20, 5, 45),
        "wing_dark": (60, 20, 120),
        "wing_mid": (140, 70, 210),
        "wing_light": (210, 150, 250),
        "wing_shine": (250, 220, 255),

        # Deep magic aura (R)
        "aura_darkest": (10, 3, 25),
        "aura_dark": (35, 10, 70),
        "aura_mid": (95, 40, 175),

        # Mist
        "mist_dark": (25, 10, 55),
        "mist_mid": (85, 40, 145),
        "mist_light": (180, 120, 230),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vaelindra._clamp(color)
        if _NS_vaelindra.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_vaelindra._clamp(color)
        if _NS_vaelindra.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vaelindra._clamp(color), points)

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
    def draw_vaelindra(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vaelindra._detect_moving(boss)
        _NS_vaelindra._update_vae_attack_anim(boss)
        attacking = (
            getattr(boss, "_vai_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind (BIG for true boss).
        _NS_vaelindra._draw_royal_aura(surface, x, y, pulse)
        _NS_vaelindra._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_vaelindra._draw_spacering_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaelindra._draw_realm_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating - elegant hover).
        if attacking:
            _NS_vaelindra._draw_vae_attack(surface, boss, x, y)
        elif moving:
            _NS_vaelindra._draw_vae_float_move(surface, boss, x, y)
        else:
            _NS_vaelindra._draw_vae_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_vaelindra._draw_energywave(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vaelindra._draw_spacering_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vaelindra._draw_violet_requiem(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaelindra._draw_realm_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vae_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vai_previous_timer", 0))
        active = bool(getattr(boss, "_vai_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vai_attack_active = True
            boss._vai_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._vai_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._vai_attack_frame = int(
                getattr(boss, "_vai_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._vai_attack_active = False
            boss._vai_attack_frame = 0
            active = False

        boss._vai_previous_timer = timer
        boss._vai_attack_progress = (
            min(1.0, getattr(boss, "_vai_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_vai_last_x"):
            boss._vai_last_x = boss.x
            boss._vai_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vai_last_x)
        dy = abs(boss.y - boss._vai_last_y)
        boss._vai_last_x = boss.x
        boss._vai_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING - elegant)
    # ============================================================
    def _draw_vae_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_vaelindra._draw_shadow(surface, x, y + 55)
        _NS_vaelindra._draw_magic_wisps(surface, x, y + 42, boss.pulse)
        _NS_vaelindra._draw_vae_body(surface, x, y - 5 + float_bob,
                                     boss.direction, boss.pulse, "idle", 0)

    def _draw_vae_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.4
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_vaelindra._draw_shadow(surface, x + sway, y + 55)
        _NS_vaelindra._draw_magic_wisps(surface, x + sway, y + 42, phase,
                                        trail=True, facing=boss.direction)
        _NS_vaelindra._draw_vae_body(surface, x + sway, y - 7 + float_bob,
                                     boss.direction, phase, "move", 0)

    def _draw_vae_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_vai_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_vai_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Elegant casting motion (raise hand → release → recovery)
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 4)
            lunge = 0
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lift = int(4 - t * 3)
            lunge = int(t * 4) * facing
        else:
            t = (progress - 0.6) / 0.4
            lift = int(1 * (1 - t))
            lunge = int(4 * (1 - t)) * facing

        float_bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_vaelindra._draw_shadow(surface, x + lunge, y + 55)
        _NS_vaelindra._draw_magic_wisps(surface, x + lunge, y + 42, boss.pulse,
                                        intense=True)
        _NS_vaelindra._draw_vae_body(surface, x + lunge, y - 5 - lift + float_bob,
                                     facing, boss.pulse, "attack", progress)
        _NS_vaelindra._draw_magic_bolt_basic(surface, boss, x + lunge,
                                             y - 5 - lift + float_bob, progress)

    # ============================================================
    # BODY (Noble mage with gown, butterfly wings, staff-free hands)
    # ============================================================
    def _draw_vae_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw noble Guinevere-style body."""
        # PSIONIC BUTTERFLY WINGS FIRST (behind body).
        _NS_vaelindra._draw_butterfly_wings(surface, cx, cy - 4, facing, phase)

        # Golden hair BEHIND torso (flowing).
        _NS_vaelindra._draw_flowing_hair_back(surface, cx, cy - 14, facing, phase)

        # Long gown (bottom - trailing).
        _NS_vaelindra._draw_royal_gown(surface, cx, cy + 8, facing, phase)

        # Torso (corset).
        _NS_vaelindra._draw_vae_torso(surface, cx, cy, facing, phase)

        # Back arm.
        _NS_vaelindra._draw_vae_arm_back(surface, cx, cy + 2, facing, phase,
                                         action, attack_progress)

        # Head + face + hair top.
        _NS_vaelindra._draw_vae_head(surface, cx, cy - 14, facing, phase)

        # Front arm (casting hand).
        _NS_vaelindra._draw_vae_arm_front(surface, cx, cy + 2, facing, phase,
                                          action, attack_progress)

    def _draw_butterfly_wings(surface, cx, cy, facing, phase):
        """Large glowing psionic butterfly wings."""
        # Wing beat.
        beat = math.sin(phase * 1.2) * 3

        # Two wings on each side (upper + lower).
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 0.9),   # far wing (larger, more visible)
            (1, 0.75, 0.7),   # near wing (partial visible)
        ]):
            back_dir = -facing * side_mult
            # No, we draw both wings extending from back.
            # Wing base at shoulder blade.
            base_x = cx - facing * 2
            base_y = cy - 2

            # UPPER WING (larger, extends up-back).
            _NS_vaelindra._draw_single_butterfly_wing(
                surface, base_x, base_y, facing, side_mult,
                phase, beat, size_mult, alpha_mult, upper=True
            )

            # LOWER WING (smaller, extends down-back).
            _NS_vaelindra._draw_single_butterfly_wing(
                surface, base_x, base_y + 4, facing, side_mult,
                phase, beat, size_mult * 0.75, alpha_mult, upper=False
            )

    def _draw_single_butterfly_wing(surface, base_x, base_y, facing, side_mult,
                                     phase, beat, size_mult, alpha_mult, upper):
        """Single butterfly wing."""
        # Wing direction (back and up/down).
        wing_dir = -facing * side_mult

        wing_size = int(28 * size_mult)
        wing_height = int(20 * size_mult)

        if upper:
            wing_up = -1  # extends upward
        else:
            wing_up = 1   # extends downward

        # Wing tips.
        outer_tip_x = base_x + int(wing_dir * wing_size)
        outer_tip_y = base_y - int(wing_height) * (-wing_up if upper else 1) + int(beat)

        # Wing shape (rounded butterfly wing).
        wing_shape = [
            (base_x, base_y),
            (base_x + int(wing_dir * wing_size * 0.4),
             base_y - int(wing_height * 0.7) * (1 if upper else -1) + int(beat * 0.5)),
            (outer_tip_x, outer_tip_y),
            (base_x + int(wing_dir * wing_size * 0.9),
             base_y - int(wing_height * 0.3) * (1 if upper else -1) + int(beat * 0.3)),
            (base_x + int(wing_dir * wing_size * 0.6),
             base_y + int(wing_height * 0.1) * (1 if upper else -1)),
        ]

        # Draw on alpha surface.
        pad = 80
        wing_surf = pygame.Surface((wing_size * 2 + pad, wing_height * 2 + pad),
                                    pygame.SRCALPHA)
        offset_x = base_x - wing_size - pad // 2
        offset_y = base_y - wing_height - pad // 2
        local_shape = [(p[0] - offset_x, p[1] - offset_y) for p in wing_shape]

        # Outer glow layer.
        _NS_vaelindra._poly(wing_surf,
                           (*_NS_vaelindra.PALETTE["wing_dark"], int(180 * alpha_mult)),
                           local_shape)

        # Mid layer.
        inner_shape = []
        cx_l = sum(p[0] for p in local_shape) / len(local_shape)
        cy_l = sum(p[1] for p in local_shape) / len(local_shape)
        for p in local_shape:
            inner_shape.append((int(p[0] * 0.85 + cx_l * 0.15),
                                int(p[1] * 0.85 + cy_l * 0.15)))
        _NS_vaelindra._poly(wing_surf,
                           (*_NS_vaelindra.PALETTE["wing_mid"], int(200 * alpha_mult)),
                           inner_shape)

        # Bright center.
        inner2 = []
        for p in inner_shape:
            inner2.append((int(p[0] * 0.7 + cx_l * 0.3),
                           int(p[1] * 0.7 + cy_l * 0.3)))
        _NS_vaelindra._poly(wing_surf,
                           (*_NS_vaelindra.PALETTE["wing_light"], int(160 * alpha_mult)),
                           inner2)

        # Wing spot pattern (like real butterfly eyes).
        spot_x = (local_shape[2][0] + cx_l) // 2
        spot_y = (local_shape[2][1] + cy_l) // 2
        _NS_vaelindra._aacircle(wing_surf,
                               (*_NS_vaelindra.PALETTE["wing_darkest"], int(240 * alpha_mult)),
                               (spot_x, spot_y), 6)
        _NS_vaelindra._aacircle(wing_surf,
                               (*_NS_vaelindra.PALETTE["magic_hot"], int(220 * alpha_mult)),
                               (spot_x, spot_y), 4)
        _NS_vaelindra._aacircle(wing_surf,
                               (*_NS_vaelindra.PALETTE["magic_shine"], int(240 * alpha_mult)),
                               (spot_x, spot_y), 2)
        pygame.draw.rect(wing_surf, _NS_vaelindra.PALETTE["white"], (spot_x, spot_y, 1, 1))

        # Vein lines from base to tips.
        base_local = (base_x - offset_x, base_y - offset_y)
        for tip_i in [1, 2, 3]:
            tip_local = (local_shape[tip_i][0], local_shape[tip_i][1])
            pygame.draw.line(wing_surf,
                            (*_NS_vaelindra.PALETTE["wing_darkest"],
                             int(220 * alpha_mult)),
                            base_local, tip_local, 2)
            pygame.draw.line(wing_surf,
                            (*_NS_vaelindra.PALETTE["magic_light"],
                             int(200 * alpha_mult)),
                            base_local, tip_local, 1)

        # Bright wing edge highlight.
        for i in range(len(local_shape) - 1):
            pygame.draw.line(wing_surf,
                            (*_NS_vaelindra.PALETTE["wing_shine"],
                             int(200 * alpha_mult)),
                            local_shape[i], local_shape[i + 1], 1)

        # Sparkles on wing.
        for spark_i in range(5):
            sp_ang = phase * 2 + spark_i * math.pi / 2.5
            sp_r = 15 + int(math.sin(phase * 2 + spark_i) * 5)
            sp_x = int(cx_l + math.cos(sp_ang) * sp_r)
            sp_y = int(cy_l + math.sin(sp_ang) * sp_r)
            pygame.draw.rect(wing_surf,
                            (*_NS_vaelindra.PALETTE["magic_hot"], int(240 * alpha_mult)),
                            (sp_x, sp_y, 2, 2))
            pygame.draw.rect(wing_surf,
                            (*_NS_vaelindra.PALETTE["magic_shine"], int(240 * alpha_mult)),
                            (sp_x, sp_y, 1, 1))

        surface.blit(wing_surf, (offset_x, offset_y))

    def _draw_flowing_hair_back(surface, cx, cy, facing, phase):
        """Long golden hair flowing behind body."""
        sway = math.sin(phase * 0.5) * 3
        back_dir = -facing

        # Multiple hair strands.
        for strand_i in range(4):
            base_x = cx + (strand_i - 1.5) * 3
            base_y = cy + 2

            # Curving down and back.
            prev = (base_x, base_y)
            segments = 10
            for i in range(1, segments + 1):
                t = i / segments
                wave = math.sin(phase * 0.6 + strand_i + t * math.pi) * (2 + t * 3)
                seg_x = base_x + int(back_dir * t * 5 + wave * 0.5)
                seg_y = base_y + int(t * 28)
                thickness = max(2, 6 - i // 2)

                _NS_vaelindra._aaline(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                                     (prev[0] + 1, prev[1] + 1),
                                     (seg_x + 1, seg_y + 1), thickness + 1)
                _NS_vaelindra._aaline(surface, _NS_vaelindra.PALETTE["hair_darkest"],
                                     prev, (seg_x, seg_y), thickness)
                _NS_vaelindra._aaline(surface, _NS_vaelindra.PALETTE["hair_dark"],
                                     prev, (seg_x, seg_y), max(1, thickness - 1))
                _NS_vaelindra._aaline(surface, _NS_vaelindra.PALETTE["hair_mid"],
                                     (prev[0], prev[1] - 1),
                                     (seg_x, seg_y - 1), max(1, thickness - 2))
                if i < 6:
                    _NS_vaelindra._aaline(surface, _NS_vaelindra.PALETTE["hair_light"],
                                         (prev[0], prev[1] - 2),
                                         (seg_x, seg_y - 2), max(1, thickness - 3))
                prev = (seg_x, seg_y)

    def _draw_royal_gown(surface, cx, cy, facing, phase):
        """Long trailing violet royal gown."""
        sway = math.sin(phase * 0.4) * 3

        # Main gown silhouette (wide flowing bottom).
        gown_shape = [
            (cx - 14, cy - 8),
            (cx - 18, cy - 2),
            (cx - 22, cy + 6),
            (cx - 24, cy + 14 + int(sway)),
            (cx - 18, cy + 22),
            (cx - 8, cy + 26),
            (cx + 8, cy + 26 - int(sway)),
            (cx + 18, cy + 22),
            (cx + 24, cy + 14 - int(sway)),
            (cx + 22, cy + 6),
            (cx + 18, cy - 2),
            (cx + 14, cy - 8),
        ]
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                           [(px + 3, py + 3) for px, py in gown_shape])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gown_darkest"], gown_shape)

        # Layered gown.
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gown_dark"], [
            (cx - 13, cy - 7),
            (cx - 17, cy - 1),
            (cx - 21, cy + 6),
            (cx - 22, cy + 14),
            (cx - 16, cy + 21),
            (cx + 16, cy + 21),
            (cx + 22, cy + 14),
            (cx + 21, cy + 6),
            (cx + 17, cy - 1),
            (cx + 13, cy - 7),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gown_mid"], [
            (cx - 11, cy - 5),
            (cx - 15, cy + 1),
            (cx - 18, cy + 8),
            (cx - 18, cy + 15),
            (cx - 12, cy + 20),
            (cx + 12, cy + 20),
            (cx + 18, cy + 15),
            (cx + 18, cy + 8),
            (cx + 15, cy + 1),
            (cx + 11, cy - 5),
        ])

        # WHITE INNER PETTICOAT (visible at front bottom, layered look).
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["shadow_deep"], [
            (cx - 8, cy + 12),
            (cx - 10, cy + 18),
            (cx - 6, cy + 24),
            (cx + 6, cy + 24),
            (cx + 10, cy + 18),
            (cx + 8, cy + 12),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["inner_dark"], [
            (cx - 7, cy + 12),
            (cx - 9, cy + 17),
            (cx - 5, cy + 23),
            (cx + 5, cy + 23),
            (cx + 9, cy + 17),
            (cx + 7, cy + 12),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["inner_mid"], [
            (cx - 5, cy + 13),
            (cx - 7, cy + 17),
            (cx - 4, cy + 22),
            (cx + 4, cy + 22),
            (cx + 7, cy + 17),
            (cx + 5, cy + 13),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["inner_light"], [
            (cx - 3, cy + 15),
            (cx - 4, cy + 19),
            (cx + 4, cy + 19),
            (cx + 3, cy + 15),
        ])

        # Gown highlight on outer edge.
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (cx - 14, cy - 7), (cx - 21, cy + 6), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (cx + 14, cy - 7), (cx + 21, cy + 6), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_shine"],
                        (cx - 12, cy - 5), (cx - 16, cy - 1), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_shine"],
                        (cx + 12, cy - 5), (cx + 16, cy - 1), 1)

        # GOLDEN BELT/CORSET DETAIL at waist.
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                        (cx - 15, cy - 8, 30, 5))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gold_darkest"],
                        (cx - 14, cy - 8, 28, 4))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gold_dark"],
                        (cx - 14, cy - 7, 28, 3))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gold_mid"],
                        (cx - 14, cy - 6, 28, 2))
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_light"],
                        (cx - 13, cy - 6), (cx + 13, cy - 6), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_shine"],
                        (cx - 10, cy - 7), (cx + 10, cy - 7), 1)

        # Central belt ornament (star/crest).
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gold_darkest"], [
            (cx, cy - 10),
            (cx - 3, cy - 6),
            (cx - 5, cy - 4),
            (cx - 3, cy - 2),
            (cx, cy),
            (cx + 3, cy - 2),
            (cx + 5, cy - 4),
            (cx + 3, cy - 6),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gold_mid"], [
            (cx, cy - 9),
            (cx - 2, cy - 6),
            (cx - 4, cy - 4),
            (cx - 2, cy - 2),
            (cx, cy - 1),
            (cx + 2, cy - 2),
            (cx + 4, cy - 4),
            (cx + 2, cy - 6),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gold_light"], [
            (cx, cy - 7),
            (cx - 1, cy - 5),
            (cx - 2, cy - 4),
            (cx, cy - 3),
            (cx + 2, cy - 4),
            (cx + 1, cy - 5),
        ])
        # Center gem (violet).
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_dark"], (cx - 1, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_light"], (cx, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (cx, cy - 4, 1, 1))

        # Skirt vertical folds/pleats (darker lines).
        for x_off in [-14, -8, 0, 8, 14]:
            fold_x = cx + x_off
            pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                            (fold_x, cy - 3), (fold_x - x_off // 4, cy + 20), 1)

    def _draw_vae_torso(surface, cx, cy, facing, phase):
        """Corset torso."""
        breath = math.sin(phase * 0.7) * 1

        # Torso silhouette (feminine hourglass).
        torso_shape = [
            (cx - 8, cy - 6),
            (cx - 11, cy - 3),
            (cx - 10, cy + 2),
            (cx - 7, cy + 6),
            (cx + 7, cy + 6),
            (cx + 10, cy + 2),
            (cx + 11, cy - 3),
            (cx + 8, cy - 6),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_shape])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gown_darkest"], torso_shape)

        # Corset layers (violet).
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gown_dark"], [
            (cx - 7, cy - 5),
            (cx - 10, cy - 2),
            (cx - 9, cy + 2),
            (cx - 6, cy + 5),
            (cx + 6, cy + 5),
            (cx + 9, cy + 2),
            (cx + 10, cy - 2),
            (cx + 7, cy - 5),
            (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["gown_mid"], [
            (cx - 5, cy - 4),
            (cx - 8, cy - 1),
            (cx - 7, cy + 2),
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 7, cy + 2),
            (cx + 8, cy - 1),
            (cx + 5, cy - 4),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])

        # White chemise (visible at chest & sleeves).
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["inner_dark"], [
            (cx - 3, cy - 6),
            (cx - 4, cy - 4),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 4, cy - 4),
            (cx + 3, cy - 6),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["inner_mid"], [
            (cx - 2, cy - 5),
            (cx - 3, cy - 3),
            (cx - 1, cy - 2),
            (cx + 1, cy - 2),
            (cx + 3, cy - 3),
            (cx + 2, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["inner_light"], (cx, cy - 4, 1, 1))

        # Chest/neckline skin (small V).
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["skin_dark"], [
            (cx - 3, cy - 7),
            (cx - 1, cy - 5),
            (cx + 1, cy - 5),
            (cx + 3, cy - 7),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["skin_mid"], [
            (cx - 2, cy - 7),
            (cx, cy - 5),
            (cx + 2, cy - 7),
        ])

        # Corset lacing (X pattern down front).
        for i, y_off in enumerate([-3, -1, 1, 3]):
            line_y = cy + y_off
            if i % 2 == 0:
                pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_dark"],
                                (cx - 3, line_y), (cx + 3, line_y + 1), 1)
            else:
                pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_dark"],
                                (cx - 3, line_y + 1), (cx + 3, line_y), 1)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gold_light"],
                            (cx, line_y, 1, 1))

        # Vertical center stripe.
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                        (cx, cy - 4), (cx, cy + 5), 1)

        # Corset highlight (curve).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (cx - 4, cy - 4), (cx - 5, cy + 3), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (cx + 4, cy - 4), (cx + 5, cy + 3), 1)

    def _draw_vae_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm."""
        sway = math.sin(phase * 0.4) * 1
        back_dir = -facing
        shoulder_x = cx + back_dir * 8
        shoulder_y = cy - 3
        elbow_x = shoulder_x + back_dir * 2
        elbow_y = shoulder_y + 5 + int(sway)
        hand_x = elbow_x - back_dir * 1
        hand_y = elbow_y + 5 + int(sway)

        # Puff sleeve at shoulder.
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1), 4)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                               (shoulder_x, shoulder_y), 4)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_dark"],
                               (shoulder_x, shoulder_y), 3)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_mid"],
                               (shoulder_x - 1, shoulder_y - 1), 2)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (shoulder_x - 1, shoulder_y - 1, 1, 1))

        # Upper arm (skin).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["skin_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["skin_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["skin_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Long glove (elbow to hand - violet).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_mid"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Ribbon bow at elbow.
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (elbow_x - 2, elbow_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_shine"],
                        (elbow_x - 1, elbow_y - 1, 2, 1))

        # Hand (gloved).
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                               (hand_x, hand_y), 2)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_dark"],
                               (hand_x, hand_y), 1)

    def _draw_vae_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm (casting hand with magic)."""
        sway = math.sin(phase * 0.4) * 1

        # Arm pose based on action.
        if action == "attack":
            if attack_progress < 0.35:
                # Raise hand up.
                t = attack_progress / 0.35
                shoulder_angle = -0.2 - t * 0.5
                elbow_bend = 0.6 - t * 0.2
            elif attack_progress < 0.6:
                # Cast forward.
                t = (attack_progress - 0.35) / 0.25
                shoulder_angle = (-0.7) + t * 0.9
                elbow_bend = 0.4 + t * 0.2
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                shoulder_angle = 0.2 - t * 0.3
                elbow_bend = 0.6 - t * 0.2
        else:
            shoulder_angle = -0.1 + math.sin(phase * 0.5) * 0.1
            elbow_bend = 0.5

        shoulder_x = cx + facing * 8
        shoulder_y = cy - 3
        upper_len = 6
        elbow_x = shoulder_x + int(math.cos(shoulder_angle) * upper_len) * facing
        elbow_y = shoulder_y + int(math.sin(shoulder_angle) * upper_len) + 2

        forearm_angle = shoulder_angle + elbow_bend
        forearm_len = 8
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len) + 3

        # Puff sleeve.
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1), 4)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                               (shoulder_x, shoulder_y), 4)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_dark"],
                               (shoulder_x, shoulder_y), 3)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_mid"],
                               (shoulder_x - facing, shoulder_y - 1), 2)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (shoulder_x - facing, shoulder_y - 1, 1, 1))

        # Upper arm (skin).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["skin_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["skin_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["skin_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Long violet glove (elbow to hand).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gown_mid"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Ribbon bow at elbow.
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_edge"],
                        (elbow_x - 2, elbow_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_shine"],
                        (elbow_x - 1, elbow_y - 1, 2, 1))

        # Hand (gloved).
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_darkest"],
                               (hand_x, hand_y), 2)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["gown_dark"],
                               (hand_x, hand_y), 1)

        # Magic butterfly in hand (idle) or charging orb (attack).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        if action == "attack" and 0.15 < attack_progress < 0.6:
            # Charging orb.
            charge_t = min(1.0, (attack_progress - 0.15) / 0.4)
            orb_r = int(3 + charge_t * 5)
            for r in range(orb_r + 5, 0, -1):
                alpha = _NS_vaelindra._alpha(180 * (orb_r + 5 - r) / (orb_r + 5))
                _NS_vaelindra._aacircle(surface,
                                       (*_NS_vaelindra.PALETTE["magic_mid"], alpha),
                                       (hand_x + facing * 3, hand_y - 2), r)
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_darkest"],
                                   (hand_x + facing * 3, hand_y - 2), orb_r)
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_light"],
                                   (hand_x + facing * 3, hand_y - 2), max(1, orb_r - 2))
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_shine"],
                                   (hand_x + facing * 3, hand_y - 2), max(1, orb_r - 3))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"],
                            (hand_x + facing * 3, hand_y - 2, 1, 1))
        else:
            # Small magic butterfly floating near hand.
            bf_x = hand_x + facing * 4
            bf_y = hand_y - 3 + int(math.sin(phase * 3) * 2)
            _NS_vaelindra._draw_mini_butterfly(surface, bf_x, bf_y, phase, size=3)

    def _draw_mini_butterfly(surface, cx, cy, phase, size=3):
        """Small floating magic butterfly."""
        beat = math.sin(phase * 4) * 1
        # Upper wings.
        for side in [-1, 1]:
            wing_tip_x = cx + side * (size + int(beat))
            wing_tip_y = cy - size
            _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["wing_dark"], [
                (cx, cy),
                (cx + side, cy - 1),
                (wing_tip_x, wing_tip_y),
                (cx + side * (size - 1), cy),
            ])
            _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["wing_mid"], [
                (cx, cy),
                (cx + side, cy - 1),
                (cx + side * max(1, size - 1), wing_tip_y + 1),
            ])
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["wing_light"],
                            (wing_tip_x - side, wing_tip_y, 1, 1))
        # Lower wings.
        for side in [-1, 1]:
            wing_tip_x = cx + side * max(1, size - 1 + int(beat))
            wing_tip_y = cy + size - 1
            _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["wing_dark"], [
                (cx, cy),
                (cx + side, cy + 1),
                (wing_tip_x, wing_tip_y),
            ])
            # FIX: pastikan 3 titik minimum untuk polygon
            _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["wing_mid"], [
                (cx, cy),
                (cx + side, cy + 1),
                (cx + side * max(1, size - 2), wing_tip_y),
            ])
        # Body (glowing core).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["magic_darkest"],
                        (cx, cy - size + 1), (cx, cy + size - 1), 1)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (cx, cy, 1, 1))

    def _draw_vae_head(surface, cx, cy, facing, phase):
        """Elegant female head with tiara/headband, side bangs."""
        # Head shape.
        head_shape = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in head_shape])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["skin_darkest"], head_shape)

        # Skin base.
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx - 4, cy + 6),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 4, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["skin_mid"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 3),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 4, cy + 3),
            (cx + 3, cy + 1),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["skin_light"], [
            (cx - 2, cy + 2),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
            (cx + 2, cy + 2),
            (cx + 1, cy),
            (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["skin_shine"], (cx, cy + 3, 1, 1))

        # Hair top (golden).
        _NS_vaelindra._draw_hair_top(surface, cx, cy, facing, phase)

        # TIARA/HEADBAND (gold + violet gem).
        _NS_vaelindra._draw_tiara(surface, cx, cy - 3, phase)

        # Violet eyes.
        _NS_vaelindra._draw_royal_eyes(surface, cx, cy + 2, facing, phase)

        # Small nose.
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["skin_darkest"], (cx, cy + 4, 1, 1))

        # Lips (subtle pink-violet).
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gown_dark"], (cx - 1, cy + 6, 2, 1))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_light"], (cx, cy + 6, 1, 1))

    def _draw_hair_top(surface, cx, cy, facing, phase):
        """Golden hair top with center part."""
        # Top hair.
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["shadow_deep"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 6, cy + 4),
            (cx - 4, cy + 1),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 4, cy + 1),
            (cx + 6, cy + 4),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["hair_darkest"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 1),
            (cx - 5, cy + 1),
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 5, cy + 1),
            (cx + 7, cy + 1),
            (cx + 6, cy - 1),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy),
            (cx - 4, cy),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 4, cy),
            (cx + 6, cy),
            (cx + 5, cy - 1),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["hair_mid"], [
            (cx - 3, cy - 1),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 3, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Center part.
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["hair_darkest"],
                        (cx, cy - 3), (cx, cy - 1), 1)
        # Highlight strand.
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["hair_light"], (cx - 1, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["hair_shine"], (cx + 1, cy - 3, 1, 1))

        # Side bangs.
        for side in [-1, 1]:
            bang_sway = math.sin(phase * 0.5 + side) * 1
            bang_x = cx + side * 5
            pygame.draw.line(surface, _NS_vaelindra.PALETTE["hair_darkest"],
                            (bang_x, cy - 1), (bang_x, cy + 5 + int(bang_sway)), 2)
            pygame.draw.line(surface, _NS_vaelindra.PALETTE["hair_dark"],
                            (bang_x, cy - 1), (bang_x, cy + 5 + int(bang_sway)), 1)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["hair_mid"],
                            (bang_x - side, cy, 1, 1))

        # Center forehead bangs (peek).
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["hair_darkest"],
                        (cx - 1, cy - 1), (cx, cy + 1), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["hair_darkest"],
                        (cx + 1, cy - 1), (cx, cy + 1), 1)

    def _draw_tiara(surface, cx, cy, phase):
        """Gold headband tiara with violet gem."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Gold band.
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_darkest"],
                        (cx - 5, cy), (cx + 5, cy), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_dark"],
                        (cx - 4, cy - 1), (cx + 4, cy - 1), 1)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["gold_mid"],
                        (cx - 3, cy - 1), (cx + 3, cy - 1), 1)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["gold_shine"], (cx - 1, cy - 1, 2, 1))

        # Center violet gem (crown centerpiece).
        for r in range(4, 0, -1):
            alpha = _NS_vaelindra._alpha(150 * (4 - r) / 4 * pulse)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                   (cx, cy - 1), r)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_darkest"],
                        (cx - 1, cy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_dark"], (cx - 1, cy - 2, 2, 2))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_light"], (cx, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (cx, cy - 2, 1, 1))

        # Small side gems.
        for side_off in [-3, 3]:
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_dark"],
                            (cx + side_off, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_hot"],
                            (cx + side_off, cy - 1, 1, 1))

    def _draw_royal_eyes(surface, cx, cy, facing, phase):
        """Beautiful violet-blue eyes."""
        pulse = math.sin(phase * 2.5) * 0.2 + 0.8

        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy

            # Eye white.
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["inner_light"],
                            (ex - 1, ey, 2, 1))

            # Iris.
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["eye_mid"], (ex, ey, 1, 1))

            # Glow around eyes.
            for r in range(3, 0, -1):
                alpha = _NS_vaelindra._alpha(90 * (3 - r) / 3 * pulse)
                _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)

            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["eye_glow"], (ex, ey, 1, 1))

            # Eyelash/eyeliner.
            pygame.draw.line(surface, _NS_vaelindra.PALETTE["hair_darkest"],
                            (ex - 1, ey - 1), (ex + 1, ey - 1), 1)

    # ============================================================
    # BASIC ATTACK — Magic bolt with violet trail
    # ============================================================
    def _draw_magic_bolt_basic(surface, boss, x, y, progress):
        """Basic violet magic bolt projectile."""
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_vaelindra._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 8

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vaelindra._alpha(220 - i * 25)
            size = max(1, 6 - i)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_darkest"], alpha),
                                   (px, py), size)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_dark"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_mid"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                   (px, py), max(1, size - 3))
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                    (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                                    (spark_x, spark_y, 1, 1))

        # Bolt head.
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_darkest"], (bx, by), 8)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_dark"], (bx, by), 6)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_mid"], (bx, by), 4)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_light"], (bx, by), 3)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_hot"], (bx, by), 2)
        _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (bx, by, 1, 1))

        # Halo.
        for r in range(12, 3, -2):
            alpha = _NS_vaelindra._alpha(80 * (12 - r) / 12)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                   (bx, by), r)

        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_vaelindra._alpha(240 * (1 - st))
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_mid"], alpha),
                                   (tx, ty), max(1, radius - 4), 2)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                   (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                                (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_shine"], alpha),
                                (ex, ey, 1, 1))

    # ============================================================
    # FLOATING MAGIC WISPS
    # ============================================================
    def _draw_magic_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Violet magic wisps and butterflies floating below."""
        strength = 1.5 if intense else 1.0

        # Ground glow.
        glow = pygame.Surface((130, 34), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(28, 3, -2):
            alpha = _NS_vaelindra._alpha((28 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_vaelindra.PALETTE["mist_dark"], alpha),
                                    (65 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)))
        for r in range(20, 3, -2):
            alpha = _NS_vaelindra._alpha((20 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_vaelindra.PALETTE["mist_mid"], alpha),
                                    (65 - r, 17 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 65, cy - 10))

        # Rising violet wisps.
        for i, offset in enumerate([-24, -16, -8, 0, 8, 16, 24]):
            t = (phase * 0.5 + i * 0.14) % 1.0
            wx = cx + offset + int(math.sin(phase * 2 + i) * 4)
            wy = cy + 4 - int(t * 24)
            alpha = _NS_vaelindra._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["mist_dark"], alpha),
                                   (wx, wy), 3)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["mist_mid"], alpha),
                                   (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                            (wx, wy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                            (wx, wy - 2, 1, 1))

        # Floating mini butterflies.
        for i in range(4):
            bf_t = (phase * 0.3 + i * 0.25) % 1.0
            bf_x = cx - 20 + i * 12 + int(math.sin(phase * 2 + i) * 4)
            bf_y = cy + 8 - int(bf_t * 30)
            alpha = _NS_vaelindra._alpha(230 * (1 - bf_t) * strength)
            if alpha > 0 and 2 < bf_y < 40:
                # Small butterfly.
                bf_size = 2
                for side in [-1, 1]:
                    _NS_vaelindra._poly(surface,
                                       (*_NS_vaelindra.PALETTE["wing_mid"], alpha), [
                                           (bf_x, bf_y),
                                           (bf_x + side * 2, bf_y - 1),
                                           (bf_x + side * 3, bf_y - 2),
                                           (bf_x + side, bf_y),
                                       ])
                    _NS_vaelindra._poly(surface,
                                       (*_NS_vaelindra.PALETTE["wing_light"], alpha), [
                                           (bf_x, bf_y),
                                           (bf_x + side * 2, bf_y + 1),
                                       ])
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                                (bf_x, bf_y, 1, 1))

        # Sparkle stars.
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.1) % 1.0
            sx = cx - 22 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 2 - int(spark_t * 22)
            alpha = _NS_vaelindra._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_mid"], alpha),
                                (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                                (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["white"], alpha),
                                (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vaelindra._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["mist_dark"], alpha),
                                       (sx, sy), max(2, 7 - i))
                _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["mist_mid"], alpha),
                                       (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                                (sx, sy - 1, 1, 1))

    # ============================================================
    # AMBIENT / GROUND (BIG for true boss)
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for r in range(15, 0, -1):
            alpha = max(0, (15 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - r, 16 - r, 126 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (5, 2, 8, 170), (5, 8, 140, 16))
        pygame.draw.ellipse(shadow, (40, 15, 70, 110), (14, 11, 122, 10))
        surface.blit(shadow, (x - 75, y - 16))

    def _draw_royal_aura(surface, x, y, phase):
        """LARGE royal violet aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for r in range(105, 5, -5):
            alpha = _NS_vaelindra._alpha((105 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_vaelindra._aacircle(aura, (*_NS_vaelindra.PALETTE["mist_dark"], alpha),
                                       (120, 100), r)
        for r in range(70, 5, -4):
            alpha = _NS_vaelindra._alpha((70 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_vaelindra._aacircle(aura, (*_NS_vaelindra.PALETTE["mist_mid"], alpha),
                                       (120, 100), r)
        for r in range(40, 5, -3):
            alpha = _NS_vaelindra._alpha((40 - r) * 1.5 * pulse)
            if alpha > 0:
                _NS_vaelindra._aacircle(aura, (*_NS_vaelindra.PALETTE["magic_dark"], alpha),
                                       (120, 100), r)
        surface.blit(aura, (x - 120, y - 100))

        # Floating butterflies orbiting boss (grand entrance).
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 45 + int(math.sin(phase + i) * 12)
            bfx = x + int(math.cos(angle) * radius)
            bfy = y - 5 + int(math.sin(angle) * radius * 0.5)
            _NS_vaelindra._draw_mini_butterfly(surface, bfx, bfy, phase + i, size=3)

        # Sparkle stars.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 38 + int(math.sin(phase + i * 2) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """LARGE ground ring with runes (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vaelindra.PALETTE["mist_dark"], 200),
                            (5, 20, 180, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_vaelindra.PALETTE["magic_darkest"], 220),
                            (14, 22, 162, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_vaelindra.PALETTE["magic_dark"], 230),
                            (26, 24, 138, 20), 1)
        pygame.draw.ellipse(ring, (*_NS_vaelindra.PALETTE["aura_dark"], 180),
                            (42, 26, 106, 16), 1)

        # Runes (magic symbols).
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 52)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 78)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_vaelindra.PALETTE["magic_light"], 220),
                            (x1, y1), (x2, y2), 1)

        # Star runes.
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3 + math.pi / 6
            sx = 95 + int(math.cos(angle) * 65)
            sy = 34 + int(math.sin(angle) * 11)
            for side in range(2):
                pygame.draw.line(ring, (*_NS_vaelindra.PALETTE["magic_hot"], 240),
                                (sx - 2, sy), (sx + 2, sy), 1)
                pygame.draw.line(ring, (*_NS_vaelindra.PALETTE["magic_hot"], 240),
                                (sx, sy - 2), (sx, sy + 2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_vaelindra.PALETTE["magic_hot"],
                                       _NS_vaelindra._alpha(150 * pulse)),
                                (16, 12, 158, 42), 1)
        surface.blit(ring, (x - 95, y - 29))

    # ============================================================
    # SKILL: Q - ENERGY WAVE (violet arrow/wave forward)
    # ============================================================
    def _draw_energywave(surface, boss, x, y, timer, phase):
        """Elongated violet arrow-shaped wave."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vaelindra._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 8

        # Move over time.
        t = progress
        current_x = int(start_x + (tx - start_x) * t)
        current_y = int(start_y + (ty - start_y) * t)

        # Trail (elongated).
        for i in range(12):
            trail_t = max(0.0, t - i * 0.05)
            if trail_t <= 0:
                continue
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vaelindra._alpha(240 - i * 20)

            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            perp_x = math.cos(perp_angle)
            perp_y = math.sin(perp_angle)
            size = max(1, 8 - i // 2)

            for w, color_key in [
                (size + 2, "magic_darkest"),
                (size, "magic_dark"),
                (max(1, size - 2), "magic_mid"),
                (1, "magic_light"),
            ]:
                p1 = (px + int(perp_x * w // 2), py + int(perp_y * w // 2))
                p2 = (px - int(perp_x * w // 2), py - int(perp_y * w // 2))
                pygame.draw.line(surface,
                                (*_NS_vaelindra.PALETTE[color_key], alpha),
                                p1, p2, 2)

        # Arrow head.
        head_angle = math.atan2(ty - start_y, tx - start_x)
        arrow_len = 22
        arrow_wid = 10

        tip = (current_x + int(math.cos(head_angle) * arrow_len),
               current_y + int(math.sin(head_angle) * arrow_len))
        perp = head_angle + math.pi / 2
        base_a = (current_x + int(math.cos(perp) * arrow_wid),
                  current_y + int(math.sin(perp) * arrow_wid))
        base_b = (current_x - int(math.cos(perp) * arrow_wid),
                  current_y - int(math.sin(perp) * arrow_wid))

        alpha = _NS_vaelindra._alpha(240)
        _NS_vaelindra._poly(surface, (*_NS_vaelindra.PALETTE["magic_darkest"], alpha),
                           [tip, base_a, base_b])
        _NS_vaelindra._poly(surface, (*_NS_vaelindra.PALETTE["magic_dark"], alpha), [
            tip,
            (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
            (current_x, current_y),
            (int((tip[0] + base_b[0]) / 2), int((tip[1] + base_b[1]) / 2)),
        ])
        _NS_vaelindra._poly(surface, (*_NS_vaelindra.PALETTE["magic_mid"], alpha), [
            tip, (current_x, current_y),
            (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
        ])
        # Bright core line.
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["magic_light"],
                        (current_x, current_y), tip, 2)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["magic_shine"],
                        (current_x, current_y), tip, 1)

        # Bright tip point.
        for r in range(6, 0, -1):
            a = _NS_vaelindra._alpha(140 * (6 - r) / 6)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_hot"], a), tip, r)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (tip[0], tip[1], 1, 1))

        # Sparkles along trail.
        for i in range(10):
            sp_t = (phase * 2 + i * 0.1) % 1.0
            sp_p = min(t, sp_t)
            spx = int(start_x + (tx - start_x) * sp_p)
            spy = int(start_y + (ty - start_y) * sp_p) + int(math.sin(phase * 4 + i) * 4)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_hot"], (spx, spy, 2, 2))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (spx, spy, 1, 1))

    # ============================================================
    # SKILL: W - SPACE RING (ring around boss, pulls enemies)
    # ============================================================
    def _draw_spacering_ground(surface, boss, x, y, timer, phase):
        """Rune circles under boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        for i in range(3):
            r = int(50 + i * 6 + math.sin(phase * 2) * 3)
            alpha = _NS_vaelindra._alpha(220 - i * 60)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_dark"], alpha),
                                   (x, y + 42), r, 2)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_mid"], alpha),
                                   (x, y + 42), r, 1)

        # Rune symbols.
        for i in range(12):
            angle = phase * 0.5 + i * math.pi / 6
            rx = x + int(math.cos(angle) * 45)
            ry = y + 42 + int(math.sin(angle) * 12)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_hot"], (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (rx, ry, 1, 1))

    def _draw_spacering_foreground(surface, boss, x, y, timer, phase):
        """3D-looking violet ring surrounding boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ring pulsing.
        pulse = math.sin(phase * 2) * 3
        ring_r_x = 60 + int(pulse)
        ring_r_y = 22 + int(pulse * 0.4)

        # Draw ring as tilted ellipse (like Saturn ring).
        # Multiple layered rings for 3D effect.
        for layer, (offset_y, width, color_key, alpha_val) in enumerate([
            (0, 3, "magic_darkest", 220),
            (0, 2, "magic_dark", 240),
            (0, 1, "magic_mid", 255),
            (-2, 1, "magic_light", 200),  # top edge highlight
        ]):
            pygame.draw.ellipse(surface,
                               (*_NS_vaelindra.PALETTE[color_key], alpha_val),
                               (x - ring_r_x, y + offset_y - ring_r_y,
                                ring_r_x * 2, ring_r_y * 2), width)

        # Bright energy along ring (rotating).
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            rx = x + int(math.cos(angle) * ring_r_x)
            ry = y + int(math.sin(angle) * ring_r_y)
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_hot"], (rx, ry), 2)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (rx, ry, 1, 1))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (rx, ry, 1, 1))

        # Purple particle inward pull.
        for i in range(15):
            pt = (phase * 1.2 + i * 0.08) % 1.0
            angle = i * math.pi / 7.5
            outer_x = x + int(math.cos(angle) * (ring_r_x + 20))
            outer_y = y + int(math.sin(angle) * (ring_r_y + 5))
            # Interpolate inward.
            px = int(outer_x + (x - outer_x) * pt)
            py = int(outer_y + (y - outer_y) * pt)
            alpha = _NS_vaelindra._alpha(220 * (1 - pt))
            if alpha > 0:
                _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                       (px, py), 2)
                pygame.draw.rect(surface, (*_NS_vaelindra.PALETTE["magic_shine"], alpha),
                                (px, py, 1, 1))

        # Vertical energy pillars around ring edge.
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            pil_x = x + int(math.cos(angle) * ring_r_x)
            pil_y = y + int(math.sin(angle) * ring_r_y)
            pil_h = int(20 + math.sin(phase * 3 + i) * 4)

            alpha = _NS_vaelindra._alpha(200)
            for w, color_key in [
                (3, "magic_dark"),
                (2, "magic_mid"),
                (1, "magic_light"),
            ]:
                pygame.draw.line(surface,
                                (*_NS_vaelindra.PALETTE[color_key], alpha),
                                (pil_x, pil_y), (pil_x, pil_y - pil_h), w)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"],
                            (pil_x, pil_y - pil_h, 1, 1))

    # ============================================================
    # SKILL: E - VIOLET REQUIEM (forward dash + wave)
    # ============================================================
    def _draw_violet_requiem(surface, boss, x, y, timer, phase):
        """Fast forward dash with arrow-like violet slash."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vaelindra._target_position(boss, x, y)

        start_x = x + facing * 16
        start_y = y - 6

        t = progress

        # Elongated slash beam (thin & long, like E icon).
        beam_start_x = start_x
        beam_start_y = start_y
        beam_end_x = int(start_x + (tx - start_x) * min(1.0, t * 1.5))
        beam_end_y = int(start_y + (ty - start_y) * min(1.0, t * 1.5))

        # Draw as arrow shape.
        angle = math.atan2(beam_end_y - beam_start_y, beam_end_x - beam_start_x)
        perp = angle + math.pi / 2

        # Multiple layer beam.
        for layer_w, color_key in [
            (10, "magic_darkest"),
            (7, "magic_dark"),
            (5, "magic_mid"),
            (3, "magic_light"),
            (1, "magic_hot"),
        ]:
            alpha = _NS_vaelindra._alpha(230 * (1 - t * 0.3))
            # Center line.
            pygame.draw.line(surface,
                            (*_NS_vaelindra.PALETTE[color_key], alpha),
                            (beam_start_x, beam_start_y),
                            (beam_end_x, beam_end_y), layer_w)

        # Sharp arrow head.
        head_len = 18
        head_wid = 8
        head_tip_x = beam_end_x + int(math.cos(angle) * head_len)
        head_tip_y = beam_end_y + int(math.sin(angle) * head_len)
        head_base_a = (beam_end_x + int(math.cos(perp) * head_wid),
                       beam_end_y + int(math.sin(perp) * head_wid))
        head_base_b = (beam_end_x - int(math.cos(perp) * head_wid),
                       beam_end_y - int(math.sin(perp) * head_wid))

        alpha = _NS_vaelindra._alpha(240)
        _NS_vaelindra._poly(surface, (*_NS_vaelindra.PALETTE["magic_darkest"], alpha),
                           [(head_tip_x, head_tip_y), head_base_a, head_base_b])
        _NS_vaelindra._poly(surface, (*_NS_vaelindra.PALETTE["magic_dark"], alpha), [
            (head_tip_x, head_tip_y),
            (int((head_tip_x + head_base_a[0]) / 2),
             int((head_tip_y + head_base_a[1]) / 2)),
            (beam_end_x, beam_end_y),
            (int((head_tip_x + head_base_b[0]) / 2),
             int((head_tip_y + head_base_b[1]) / 2)),
        ])
        _NS_vaelindra._poly(surface, (*_NS_vaelindra.PALETTE["magic_mid"], alpha), [
            (head_tip_x, head_tip_y),
            (beam_end_x, beam_end_y),
            (int((head_tip_x + head_base_a[0]) / 2),
             int((head_tip_y + head_base_a[1]) / 2)),
        ])
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["magic_light"],
                        (beam_end_x, beam_end_y), (head_tip_x, head_tip_y), 2)
        pygame.draw.line(surface, _NS_vaelindra.PALETTE["magic_shine"],
                        (beam_end_x, beam_end_y), (head_tip_x, head_tip_y), 1)

        # Bright tip glow.
        for r in range(8, 0, -1):
            a = _NS_vaelindra._alpha(160 * (8 - r) / 8)
            _NS_vaelindra._aacircle(surface, (*_NS_vaelindra.PALETTE["magic_hot"], a),
                                   (head_tip_x, head_tip_y), r)
        pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"],
                        (head_tip_x, head_tip_y, 1, 1))

        # Feather-like violet streaks along the beam (like E icon).
        for i in range(6):
            streak_t = i / 6
            streak_x = int(beam_start_x + (beam_end_x - beam_start_x) * streak_t)
            streak_y = int(beam_start_y + (beam_end_y - beam_start_y) * streak_t)
            streak_len = 8

            for side in [-1, 1]:
                sk_end_x = streak_x + int(math.cos(perp) * streak_len * side)
                sk_end_y = streak_y + int(math.sin(perp) * streak_len * side)
                alpha = _NS_vaelindra._alpha(180 * (1 - streak_t))
                pygame.draw.line(surface,
                                (*_NS_vaelindra.PALETTE["magic_mid"], alpha),
                                (streak_x, streak_y), (sk_end_x, sk_end_y), 2)
                pygame.draw.line(surface,
                                (*_NS_vaelindra.PALETTE["magic_light"], alpha),
                                (streak_x, streak_y), (sk_end_x, sk_end_y), 1)
                pygame.draw.rect(surface,
                                (*_NS_vaelindra.PALETTE["magic_hot"], alpha),
                                (sk_end_x, sk_end_y, 1, 1))

        # Trail sparkles.
        for i in range(12):
            sp_t = (phase * 3 + i * 0.08) % 1.0
            sp_p = min(1.0, t * 1.5) * sp_t
            spx = int(beam_start_x + (tx - beam_start_x) * sp_p)
            spy = int(beam_start_y + (ty - beam_start_y) * sp_p) + \
                int(math.sin(phase * 5 + i) * 3)
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"], (spx, spy, 2, 2))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (spx, spy, 1, 1))

    # ============================================================
    # SKILL: R - REALM OF MYTH (giant butterfly/spirit realm dome)
    # ============================================================
    def _draw_realm_ground(surface, boss, x, y, timer, phase):
        """Large domed ground area with runes."""
        tx, ty = _NS_vaelindra._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 2))

        if r > 5:
            # Base dark ellipse.
            pygame.draw.ellipse(surface, (*_NS_vaelindra.PALETTE["aura_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vaelindra.PALETTE["aura_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vaelindra.PALETTE["magic_darkest"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

            # Bright edge ring.
            pygame.draw.ellipse(surface, (*_NS_vaelindra.PALETTE["magic_light"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_vaelindra.PALETTE["magic_hot"], 240),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)

    def _draw_realm_foreground(surface, boss, x, y, timer, phase):
        """Giant violet realm dome with butterflies and pillars."""
        tx, ty = _NS_vaelindra._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        expand = min(1.0, progress * 2)

        if expand < 0.05:
            return

        realm_r = int(90 * expand)

        # DOME (upper half circle).
        dome_surf = pygame.Surface((realm_r * 2 + 20, realm_r + 20), pygame.SRCALPHA)
        dome_center = (realm_r + 10, realm_r + 10)

        # Layered dome.
        for layer_i, (r_off, alpha_val, color_key) in enumerate([
            (0, 90, "aura_dark"),
            (-4, 120, "magic_dark"),
            (-8, 60, "magic_mid"),
        ]):
            pygame.draw.arc(dome_surf,
                           (*_NS_vaelindra.PALETTE[color_key], alpha_val),
                           (r_off, r_off, (realm_r - r_off) * 2, (realm_r - r_off) * 2),
                           0, math.pi, 3)

        # Bright edge dome outline.
        pygame.draw.arc(dome_surf,
                       (*_NS_vaelindra.PALETTE["magic_light"], 220),
                       (0, 0, realm_r * 2, realm_r * 2),
                       0, math.pi, 2)
        pygame.draw.arc(dome_surf,
                       (*_NS_vaelindra.PALETTE["magic_hot"], 240),
                       (2, 2, realm_r * 2 - 4, realm_r * 2 - 4),
                       0, math.pi, 1)

        # Vertical column shafts around perimeter.
        for i in range(10):
            angle = math.pi + (i / 10) * math.pi  # bottom half only conceptually
            # Actually spread across dome.
            angle = (i / 9) * math.pi  # 0 to pi across dome top
            px = dome_center[0] - realm_r + int(math.cos(angle - math.pi) * realm_r)
            # Compute position on dome edge.
            edge_x = dome_center[0] + int(math.cos(angle) * realm_r)
            edge_y = dome_center[1] - int(math.sin(angle) * realm_r)

            # Draw vertical energy shaft.
            shaft_h = 12
            shaft_top = (edge_x, edge_y - shaft_h)
            for w, color_key in [
                (3, "magic_dark"),
                (2, "magic_mid"),
                (1, "magic_light"),
            ]:
                alpha = _NS_vaelindra._alpha(200 * expand)
                pygame.draw.line(dome_surf,
                                (*_NS_vaelindra.PALETTE[color_key], alpha),
                                (edge_x, edge_y), shaft_top, w)

        surface.blit(dome_surf, (tx - realm_r - 10, ty - realm_r - 10))

        # GIANT BUTTERFLY at center (like R icon - spirit).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        bf_size = int(15 * expand * pulse)

        if bf_size > 3:
            # Upper wings.
            for side in [-1, 1]:
                wing_tip_x = tx + side * bf_size
                wing_tip_y = ty - bf_size

                wing_shape = [
                    (tx, ty),
                    (tx + side * 3, ty - 3),
                    (wing_tip_x, wing_tip_y),
                    (wing_tip_x + side * 3, wing_tip_y + 3),
                    (tx + side * (bf_size - 2), ty - 1),
                ]
                for layer, color_key in [
                    (0, "wing_dark"),
                    (1, "wing_mid"),
                    (2, "wing_light"),
                ]:
                    offset_pts = []
                    if layer > 0:
                        cx_p = sum(p[0] for p in wing_shape) / len(wing_shape)
                        cy_p = sum(p[1] for p in wing_shape) / len(wing_shape)
                        for p in wing_shape:
                            factor = 1 - layer * 0.15
                            offset_pts.append((int(p[0] * factor + cx_p * (1 - factor)),
                                              int(p[1] * factor + cy_p * (1 - factor))))
                    else:
                        offset_pts = wing_shape
                    _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE[color_key],
                                       offset_pts)

                # Wing tip glow.
                for r in range(4, 0, -1):
                    a = _NS_vaelindra._alpha(150 * (4 - r) / 4)
                    _NS_vaelindra._aacircle(surface,
                                           (*_NS_vaelindra.PALETTE["magic_hot"], a),
                                           (wing_tip_x, wing_tip_y), r)
                pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_shine"],
                                (wing_tip_x, wing_tip_y, 1, 1))

            # Lower wings.
            for side in [-1, 1]:
                wing_tip_x = tx + side * (bf_size - 3)
                wing_tip_y = ty + bf_size - 2

                wing_shape = [
                    (tx, ty),
                    (tx + side * 2, ty + 2),
                    (wing_tip_x, wing_tip_y),
                    (tx + side * 2, ty + bf_size // 2),
                ]
                _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["wing_dark"], wing_shape)
                _NS_vaelindra._poly(surface, _NS_vaelindra.PALETTE["wing_mid"], [
                    (tx, ty),
                    (tx + side * 2, ty + 2),
                    (wing_tip_x - side, wing_tip_y - 1),
                ])
                pygame.draw.rect(surface, _NS_vaelindra.PALETTE["magic_hot"],
                                (wing_tip_x, wing_tip_y, 1, 1))

            # Central body (glowing spirit).
            for r in range(bf_size, 0, -1):
                alpha = _NS_vaelindra._alpha(150 * (bf_size - r) / bf_size * pulse)
                if r > bf_size // 2:
                    _NS_vaelindra._aacircle(surface,
                                           (*_NS_vaelindra.PALETTE["magic_dark"], alpha),
                                           (tx, ty), r)
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_darkest"],
                                   (tx, ty), max(1, bf_size // 3))
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_mid"],
                                   (tx, ty), max(1, bf_size // 4))
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_light"],
                                   (tx, ty), max(1, bf_size // 5))
            _NS_vaelindra._aacircle(surface, _NS_vaelindra.PALETTE["magic_shine"],
                                   (tx, ty), max(1, bf_size // 8))
            pygame.draw.rect(surface, _NS_vaelindra.PALETTE["white"], (tx, ty, 1, 1))

        # Damage numbers - swirling small butterflies inside realm.
        for i in range(8):
            angle = phase * 0.7 + i * math.pi / 4
            orbit_r = int(realm_r * 0.6 + math.sin(phase * 2 + i) * 8)
            bfx = tx + int(math.cos(angle) * orbit_r)
            bfy = ty + int(math.sin(angle) * orbit_r * 0.5) - 5
            _NS_vaelindra._draw_mini_butterfly(surface, bfx, bfy, phase + i, size=3)

        # Rising violet columns (lock-in effect).
        num_pillars = 8
        for i in range(num_pillars):
            col_angle = i * math.pi * 2 / num_pillars + phase * 0.2
            col_dist = int(realm_r * 0.75)
            col_x = tx + int(math.cos(col_angle) * col_dist)
            col_y_base = ty + int(math.sin(col_angle) * col_dist * 0.5)

            # Vertical column of energy.
            for layer in range(6):
                layer_t = (phase * 0.8 + i * 0.2 + layer * 0.15) % 1.0
                layer_y = col_y_base - int(layer_t * 30)
                layer_alpha = _NS_vaelindra._alpha(200 * (1 - layer_t))
                layer_w = int(4 + layer_t * 3)

                pygame.draw.ellipse(surface,
                                    (*_NS_vaelindra.PALETTE["magic_dark"], layer_alpha),
                                    (col_x - layer_w, layer_y - 2, layer_w * 2, 4))
                pygame.draw.ellipse(surface,
                                    (*_NS_vaelindra.PALETTE["magic_mid"], layer_alpha),
                                    (col_x - layer_w + 1, layer_y - 1,
                                     layer_w * 2 - 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_vaelindra.PALETTE["magic_hot"], layer_alpha),
                                (col_x, layer_y, 1, 1))
                pygame.draw.rect(surface,
                                (*_NS_vaelindra.PALETTE["magic_shine"], layer_alpha),
                                (col_x, layer_y - 1, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_akahime(surface, boss, x, y):
    """Entry point akahime."""
    return _NS_akahime.draw_akahime(surface, boss, x, y)


def draw_nyxthrael(surface, boss, x, y):
    """Entry point nyxthrael."""
    return _NS_nyxthrael.draw_nyxthrael(surface, boss, x, y)


def draw_sylvantheros(surface, boss, x, y):
    """Entry point sylvantheros."""
    return _NS_sylvantheros.draw_sylvantheros(surface, boss, x, y)


def draw_vaelindra(surface, boss, x, y):
    """Entry point vaelindra."""
    return _NS_vaelindra.draw_vaelindra(surface, boss, x, y)
