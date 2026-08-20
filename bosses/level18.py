"""
bosses/level18.py - Semua boss Level 18

Berisi:
  - cryssalia   (mini boss - RANGED glacial empress ice mage)
  - kaelthar    (mini boss - MELEE storm fist martial artist)
  - morkhaera   (mini boss - RANGED blood-feather witch)
  - aurelion    (TRUE BOSS - Golden Sovereign, MELEE royal king)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kt_ (kaelthar) di-rename -> _kth_ (bentrok dengan Kaelthorn L17)
  - _cs_ (cryssalia), _mk_ (morkhaera), _au_ (aurelion) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# cryssalia.py
# ====================================================================

"""
CRYSSALIA - The Glacial Empress
Mini boss ice queen mage dengan power of frost.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_cryssalia:
    """Namespace cryssalia - ice queen mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale royal)
        "skin_darkest": (140, 130, 145),
        "skin_dark": (195, 180, 195),
        "skin_mid": (230, 215, 225),
        "skin_light": (250, 240, 245),
        "skin_shine": (255, 250, 252),

        # Blue hair (long wavy)
        "hair_darkest": (30, 45, 90),
        "hair_dark": (65, 90, 155),
        "hair_mid": (115, 150, 215),
        "hair_light": (175, 205, 245),
        "hair_shine": (225, 240, 255),

        # White dress (main gown)
        "dress_darkest": (140, 155, 190),
        "dress_dark": (185, 200, 225),
        "dress_mid": (220, 230, 245),
        "dress_light": (245, 250, 255),
        "dress_shine": (255, 255, 255),

        # Blue robe (outer, trailing)
        "robe_darkest": (25, 40, 90),
        "robe_dark": (55, 85, 155),
        "robe_mid": (100, 140, 210),
        "robe_light": (160, 195, 240),
        "robe_shine": (215, 235, 255),

        # Fur collar (white/cream)
        "fur_dark": (170, 175, 185),
        "fur_mid": (215, 220, 230),
        "fur_light": (245, 248, 252),
        "fur_shine": (255, 255, 255),

        # Gold trim (accents)
        "gold_dark": (110, 85, 25),
        "gold_mid": (195, 155, 50),
        "gold_light": (245, 215, 105),
        "gold_shine": (255, 245, 190),

        # Ice crystal (main theme - cool blue)
        "ice_darkest": (15, 40, 90),
        "ice_dark": (40, 100, 180),
        "ice_mid": (90, 170, 240),
        "ice_light": (170, 220, 255),
        "ice_hot": (215, 240, 255),
        "ice_shine": (240, 250, 255),
        "ice_white": (250, 253, 255),

        # Deep frost
        "frost_darkest": (10, 25, 60),
        "frost_dark": (25, 60, 130),
        "frost_mid": (60, 130, 210),

        # Eye (icy blue)
        "eye_dark": (15, 25, 45),
        "eye_white": (240, 250, 255),
        "eye_ice": (120, 200, 255),

        # Ground
        "rune_dark": (15, 35, 80),
        "rune_mid": (60, 130, 220),
        "rune_light": (170, 220, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 4, 10),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_cryssalia._clamp(color)
        if _NS_cryssalia.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_cryssalia._clamp(color)
        if _NS_cryssalia.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue
        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_cryssalia._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_cryssalia._clamp(color), valid_points)

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
        return int(x + 240 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_cryssalia(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_cryssalia._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_cs_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # Ambient behind.
        _NS_cryssalia._draw_frost_aura(surface, x, y, pulse)
        _NS_cryssalia._draw_ground_ring(surface, x, y + 55, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_cryssalia._draw_frostbites_ground(surface, boss, x, y,
                                                    skill_timer, pulse)
        elif active_skill == "r":
            _NS_cryssalia._draw_colddest_ground(surface, boss, x, y,
                                                  skill_timer, pulse)
        elif active_skill == "w":
            _NS_cryssalia._draw_bitterfrost_ground(surface, boss, x, y,
                                                     skill_timer, pulse)

        # Body.
        if attacking:
            _NS_cryssalia._draw_body_attack(surface, boss, x, y)
        elif active_skill:
            _NS_cryssalia._draw_body_cast(surface, boss, x, y, pulse, active_skill)
        else:
            _NS_cryssalia._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "q":
            _NS_cryssalia._draw_frostshock_fg(surface, boss, x, y,
                                                skill_timer, pulse)
        elif active_skill == "w":
            _NS_cryssalia._draw_bitterfrost_fg(surface, boss, x, y,
                                                 skill_timer, pulse)
        elif active_skill == "e":
            _NS_cryssalia._draw_frostbites_fg(surface, boss, x, y,
                                                skill_timer, pulse)
        elif active_skill == "r":
            _NS_cryssalia._draw_colddest_fg(surface, boss, x, y,
                                              skill_timer, pulse)

        # Basic attack projectile (ice shard).
        if attacking:
            _NS_cryssalia._draw_ice_shard(surface, boss, x, y)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_cs_previous_timer", 0))
        active = bool(getattr(boss, "_cs_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._cs_attack_active = True
            boss._cs_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._cs_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._cs_attack_frame = int(getattr(boss, "_cs_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._cs_attack_active = False
            boss._cs_attack_frame = 0
            active = False

        boss._cs_previous_timer = timer
        boss._cs_attack_progress = (
            min(1.0, getattr(boss, "_cs_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_cryssalia._draw_shadow(surface, x, y + 55)
        _NS_cryssalia._draw_float_snowflakes(surface, x, y + 30, boss.pulse)
        _NS_cryssalia._draw_queen_body(surface, x, y + bob, boss.direction,
                                        boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_cs_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_cs_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_cryssalia._draw_shadow(surface, x, y + 55)
        _NS_cryssalia._draw_float_snowflakes(surface, x, y + 30, boss.pulse,
                                              intense=True)
        _NS_cryssalia._draw_queen_body(surface, x, y + bob, facing,
                                        boss.pulse, "attack",
                                        getattr(boss, "_cs_attack_progress", 0))

    def _draw_body_cast(surface, boss, x, y, pulse, skill):
        bob = int(math.sin(pulse * 0.5) * 4)
        # Slight rise when casting.
        lift = int(math.sin(pulse * 1.5) * 2) + 3
        _NS_cryssalia._draw_shadow(surface, x, y + 55)
        _NS_cryssalia._draw_float_snowflakes(surface, x, y + 30, pulse,
                                              intense=True)
        _NS_cryssalia._draw_queen_body(surface, x, y + bob - lift,
                                        boss.direction, pulse, "cast",
                                        skill=skill)

    # ============================================================
    # QUEEN BODY (floating royal ice mage - no legs, dress trail)
    # ============================================================
    def _draw_queen_body(surface, cx, cy, facing, phase, action,
                          progress=0, skill=None):
        """Full ice queen body: dress trail, torso, fur collar, arms, staff, crown."""
        # Order: dress trail, back arm (gesture), torso, fur collar, head+crown,
        # front arm+staff
        _NS_cryssalia._draw_dress_trail(surface, cx, cy, facing, phase)
        _NS_cryssalia._draw_back_arm(surface, cx, cy, facing, phase, action,
                                       progress)
        _NS_cryssalia._draw_queen_torso(surface, cx, cy, facing, phase, action)
        _NS_cryssalia._draw_fur_collar(surface, cx, cy, facing, phase)
        _NS_cryssalia._draw_crown_head(surface, cx, cy - 20, facing, phase, action)
        _NS_cryssalia._draw_staff_arm(surface, cx, cy, facing, phase, action,
                                        progress)

    def _draw_dress_trail(surface, cx, cy, facing, phase):
        """Long flowing white/blue dress trailing below."""
        sway = math.sin(phase * 0.4) * 3
        sway2 = math.sin(phase * 0.6 + 1) * 2

        # OUTER blue robe.
        robe_shape = [
            (cx - 14, cy + 8),
            (cx - 22, cy + 18),
            (cx - 30 + int(sway), cy + 32),
            (cx - 32 + int(sway), cy + 46),
            (cx - 26 + int(sway2), cy + 56),
            (cx - 12 + int(sway2), cy + 62),
            (cx, cy + 64),
            (cx + 12 + int(sway2), cy + 62),
            (cx + 26 + int(sway2), cy + 56),
            (cx + 32 + int(sway), cy + 46),
            (cx + 30 + int(sway), cy + 32),
            (cx + 22, cy + 18),
            (cx + 14, cy + 8),
        ]
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                             [(px + 3, py + 3) for px, py in robe_shape])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["robe_darkest"],
                             robe_shape)
        # Inner shading.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["robe_dark"], [
            (cx - 12, cy + 10),
            (cx - 20, cy + 20),
            (cx - 27 + int(sway), cy + 34),
            (cx - 28 + int(sway), cy + 44),
            (cx - 24 + int(sway2), cy + 54),
            (cx - 10 + int(sway2), cy + 59),
            (cx, cy + 60),
            (cx + 10 + int(sway2), cy + 59),
            (cx + 24 + int(sway2), cy + 54),
            (cx + 28 + int(sway), cy + 44),
            (cx + 27 + int(sway), cy + 34),
            (cx + 20, cy + 20),
            (cx + 12, cy + 10),
        ])

        # INNER WHITE DRESS (front, more visible).
        dress_shape = [
            (cx - 10, cy + 10),
            (cx - 14, cy + 22),
            (cx - 18 + int(sway2), cy + 38),
            (cx - 16 + int(sway2), cy + 52),
            (cx - 8 + int(sway2), cy + 58),
            (cx + 8 + int(sway2), cy + 58),
            (cx + 16 + int(sway2), cy + 52),
            (cx + 18 + int(sway2), cy + 38),
            (cx + 14, cy + 22),
            (cx + 10, cy + 10),
        ]
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_darkest"],
                             dress_shape)
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_dark"], [
            (cx - 9, cy + 12),
            (cx - 13, cy + 22),
            (cx - 16 + int(sway2), cy + 38),
            (cx - 14 + int(sway2), cy + 50),
            (cx + 14 + int(sway2), cy + 50),
            (cx + 16 + int(sway2), cy + 38),
            (cx + 13, cy + 22),
            (cx + 9, cy + 12),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_mid"], [
            (cx - 8, cy + 14),
            (cx - 11, cy + 22),
            (cx - 13 + int(sway2), cy + 38),
            (cx - 10 + int(sway2), cy + 48),
            (cx + 10 + int(sway2), cy + 48),
            (cx + 13 + int(sway2), cy + 38),
            (cx + 11, cy + 22),
            (cx + 8, cy + 14),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_light"], [
            (cx - 6, cy + 16),
            (cx - 9, cy + 22),
            (cx - 8 + int(sway2), cy + 40),
            (cx - 4 + int(sway2), cy + 46),
            (cx + 4 + int(sway2), cy + 46),
            (cx + 8 + int(sway2), cy + 40),
            (cx + 9, cy + 22),
            (cx + 6, cy + 16),
        ])
        # Bright fabric folds.
        for i, x_ratio in enumerate((-0.5, 0.0, 0.5)):
            fold_top = cx + int(x_ratio * 8)
            fold_bot = cx + int(x_ratio * 12) + int(sway2)
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["dress_shine"],
                                    (fold_top, cy + 18), (fold_bot, cy + 46), 1)

        # GOLD TRIM ORNAMENTS on dress front (like referensi).
        # Central gold line down front.
        for gy in range(20, 46, 3):
            gx = cx + int(sway2 * 0.5)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_dark"],
                             (gx - 1, cy + gy, 2, 2))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_mid"],
                             (gx, cy + gy, 1, 1))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_shine"],
                             (gx, cy + gy, 1, 1))

        # Ice crystals at hem (dress base).
        for i in range(5):
            cx_i = cx - 16 + i * 8
            cy_i = cy + 55 + int(sway2 * 0.5)
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
                (cx_i, cy_i - 2), (cx_i + 2, cy_i),
                (cx_i, cy_i + 2), (cx_i - 2, cy_i),
            ])
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_light"],
                             (cx_i, cy_i, 1, 1))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (cx_i, cy_i - 1, 1, 1))

        # Snowflake particles falling below.
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            wx = cx - 25 + i * 7 + int(math.sin(phase + i) * 3)
            wy = cy + 58 + int(t * 8)
            alpha = _NS_cryssalia._alpha(200 * (1 - t))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                             (wx, wy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (wx, wy, 1, 1))

    def _draw_queen_torso(surface, cx, cy, facing, phase, action):
        """Elegant torso with tight bodice + gold decorations."""
        breath = math.sin(phase * 0.7) * 1

        # Bodice shape (fitted, feminine).
        torso_shape = [
            (cx - 9, cy - 6),
            (cx - 10, cy - 1),
            (cx - 9, cy + 5),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 9, cy + 5),
            (cx + 10, cy - 1),
            (cx + 9, cy - 6),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ]
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_shape])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_darkest"],
                             torso_shape)
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_dark"], [
            (cx - 8, cy - 5), (cx - 9, cy - 1),
            (cx - 8, cy + 4), (cx - 5, cy + 8),
            (cx + 5, cy + 8), (cx + 8, cy + 4),
            (cx + 9, cy - 1), (cx + 8, cy - 5),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_mid"], [
            (cx - 7, cy - 4), (cx - 8, cy),
            (cx - 5, cy + 6), (cx + 5, cy + 6),
            (cx + 8, cy), (cx + 7, cy - 4),
            (cx + 3, cy - 8), (cx - 3, cy - 8),
        ])
        # Central chest line highlight.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["dress_light"], [
            (cx - 2, cy - 5), (cx + 2, cy - 5),
            (cx + 2, cy + 5), (cx - 2, cy + 5),
        ])
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["dress_shine"],
                         (cx, cy - 3, 1, 3))

        # GOLD CORSET TRIM (V-shape down front like referensi).
        # Diagonal gold lines.
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_dark"],
                         (cx - 6, cy - 5), (cx, cy + 7), 1)
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_dark"],
                         (cx + 6, cy - 5), (cx, cy + 7), 1)
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_mid"],
                         (cx - 5, cy - 4), (cx, cy + 6), 1)
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_mid"],
                         (cx + 5, cy - 4), (cx, cy + 6), 1)
        # Gold buttons/gems along corset.
        for i, gy_off in enumerate((-3, 0, 3)):
            gx = cx
            gy = cy + gy_off
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_dark"],
                             (gx - 1, gy, 3, 2))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_mid"],
                             (gx, gy, 2, 1))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_shine"],
                             (gx, gy, 1, 1))

        # Blue ice gem center.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_cryssalia._alpha(200 * (4 - r) / 4 * pulse)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                                     (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_dark"],
                         (cx - 1, cy, 3, 3))
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_mid"],
                         (cx, cy, 2, 2))
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                         (cx, cy + 1, 1, 1))

    def _draw_fur_collar(surface, cx, cy, facing, phase):
        """White fur collar around neck/shoulders."""
        sway = math.sin(phase * 0.5) * 1

        # Fur is fluffy - draw multiple overlapping circles.
        for angle_step in range(8):
            angle = -math.pi + angle_step * math.pi / 4
            fx = cx + int(math.cos(angle) * 10)
            fy = cy - 8 + int(math.sin(angle) * 4) + int(sway)
            # Dark shadow inside.
            _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                                     (fx + 1, fy + 1), 4)
            _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_dark"],
                                     (fx, fy), 4)
            _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_mid"],
                                     (fx, fy), 3)
            _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_light"],
                                     (fx, fy - 1), 2)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["fur_shine"],
                             (fx, fy - 2, 1, 1))

        # Central fur puff (bigger, at front).
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_dark"],
                                 (cx, cy - 6), 6)
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_mid"],
                                 (cx, cy - 6), 5)
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_light"],
                                 (cx, cy - 7), 3)
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["fur_shine"],
                                 (cx, cy - 8), 2)
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                         (cx, cy - 9, 1, 1))

    def _draw_crown_head(surface, cx, cy, facing, phase, action):
        """Beautiful face with ice crown and flowing blue hair."""
        head_cx = cx
        head_cy = cy

        # LONG FLOWING BLUE HAIR (behind face, drawn first).
        _NS_cryssalia._draw_flowing_hair(surface, head_cx, head_cy, facing, phase)

        # Face (pale, delicate).
        face_shape = [
            (head_cx - 5, head_cy - 3), (head_cx - 6, head_cy + 1),
            (head_cx - 4, head_cy + 5), (head_cx - 1, head_cy + 7),
            (head_cx + 3, head_cy + 7), (head_cx + 5, head_cy + 5),
            (head_cx + 6, head_cy + 1), (head_cx + 5, head_cy - 3),
            (head_cx + 2, head_cy - 6), (head_cx - 2, head_cy - 6),
        ]
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in face_shape])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["skin_darkest"],
                             face_shape)
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["skin_dark"], [
            (head_cx - 4, head_cy - 2), (head_cx - 5, head_cy + 1),
            (head_cx - 3, head_cy + 4), (head_cx + 3, head_cy + 4),
            (head_cx + 5, head_cy + 1), (head_cx + 4, head_cy - 2),
            (head_cx + 2, head_cy - 5), (head_cx - 2, head_cy - 5),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["skin_mid"], [
            (head_cx - 3, head_cy - 1), (head_cx - 4, head_cy + 1),
            (head_cx - 2, head_cy + 3), (head_cx + 2, head_cy + 3),
            (head_cx + 4, head_cy + 1), (head_cx + 3, head_cy - 1),
            (head_cx + 1, head_cy - 4), (head_cx - 1, head_cy - 4),
        ])
        # Cheek/nose highlight.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["skin_light"], [
            (head_cx - 1, head_cy), (head_cx + 2, head_cy),
            (head_cx + 2, head_cy + 3), (head_cx - 1, head_cy + 3),
        ])
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["skin_shine"],
                         (head_cx, head_cy + 1, 1, 1))

        # ICY BLUE EYES.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for ey_side in [-1, 1]:
            eye_x = head_cx + ey_side * 2
            eye_y = head_cy
            # Eye white.
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["eye_white"],
                             (eye_x - 1, eye_y, 3, 2))
            # Iris (bright ice blue).
            for r in range(2, 0, -1):
                alpha = _NS_cryssalia._alpha(180 * (2 - r) / 2 * pulse)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (eye_x, eye_y), r)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["eye_ice"],
                             (eye_x, eye_y, 1, 1))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (eye_x, eye_y, 1, 1))

        # Delicate eyebrows.
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["hair_dark"],
                         (head_cx - 4, head_cy - 2), (head_cx - 1, head_cy - 2), 1)
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["hair_dark"],
                         (head_cx + 1, head_cy - 2), (head_cx + 4, head_cy - 2), 1)

        # Small elegant mouth (with slight pink).
        pygame.draw.line(surface, (190, 130, 150),
                         (head_cx - 1, head_cy + 5), (head_cx + 1, head_cy + 5), 1)

        # ICE CROWN (spikes crystal).
        _NS_cryssalia._draw_ice_crown(surface, head_cx, head_cy, facing, phase)

    def _draw_flowing_hair(surface, cx, cy, facing, phase):
        """Long wavy blue hair flowing behind."""
        sway = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7 + 1) * 2

        # Multiple hair strands cascading down both sides.
        for side in [-1, 1]:
            for i, (offset_x, offset_y_start, length, curve) in enumerate([
                (0, -2, 32, 4), (1, 2, 36, 5), (2, 6, 30, 3),
                (3, 10, 26, 4),
            ]):
                base_x = cx + side * (5 + offset_x)
                base_y = cy + offset_y_start

                wave = math.sin(phase * 0.6 + i + side) * 2
                mid_x = base_x + side * int(curve + wave)
                mid_y = base_y + length // 2
                end_x = base_x + side * int(sway + wave)
                end_y = base_y + length

                # Shadow.
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                                        (base_x + 1, base_y + 1),
                                        (mid_x + 1, mid_y + 1), 3)
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                                        (mid_x + 1, mid_y + 1),
                                        (end_x + 1, end_y + 1), 3)
                # Hair layers.
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["hair_darkest"],
                                        (base_x, base_y), (mid_x, mid_y), 3)
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["hair_darkest"],
                                        (mid_x, mid_y), (end_x, end_y), 2)
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["hair_dark"],
                                        (base_x, base_y), (mid_x, mid_y), 2)
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["hair_dark"],
                                        (mid_x, mid_y), (end_x, end_y), 1)
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["hair_mid"],
                                        (base_x, base_y - 1),
                                        (mid_x, mid_y - 1), 1)
                # Highlight strand.
                if i == 1:
                    _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["hair_light"],
                                            (base_x, base_y), (end_x, end_y), 1)
                    pygame.draw.rect(surface, _NS_cryssalia.PALETTE["hair_shine"],
                                     (mid_x, mid_y - 1, 1, 1))

        # Top of head bangs.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["hair_darkest"], [
            (cx - 5, cy - 6), (cx + 5, cy - 6),
            (cx + 6, cy - 4), (cx - 6, cy - 4),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["hair_dark"], [
            (cx - 4, cy - 6), (cx + 4, cy - 6),
            (cx + 5, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["hair_mid"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 3, cy - 5), (cx - 3, cy - 5),
        ])
        # Side bangs framing face.
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["hair_dark"],
                         (cx - 5, cy - 5), (cx - 5, cy + 1), 1)
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["hair_dark"],
                         (cx + 5, cy - 5), (cx + 5, cy + 1), 1)

    def _draw_ice_crown(surface, cx, cy, facing, phase):
        """Ice crown with 5 crystal spikes on top."""
        # Crown base band.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 5, cy - 4), (cx - 5, cy - 4),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["gold_dark"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 5, cy - 4), (cx - 5, cy - 4),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["gold_mid"], [
            (cx - 4, cy - 5), (cx + 4, cy - 5),
            (cx + 4, cy - 4), (cx - 4, cy - 4),
        ])
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_light"],
                         (cx - 3, cy - 5), (cx + 3, cy - 5), 1)

        # 5 ice crystal spikes on top (varied heights, khas frost crown).
        for i, (off_x, height) in enumerate([
            (-5, 4), (-3, 7), (0, 10), (3, 7), (5, 4),
        ]):
            pulse = math.sin(phase * 1.5 + i * 0.4) * 0.5 + 0.5
            spike_x = cx + off_x
            spike_base_y = cy - 5
            spike_tip_y = spike_base_y - height

            # Shadow.
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 1 + 1, spike_base_y + 1),
                (spike_x + 1 + 1, spike_base_y + 1),
            ])
            # Ice spike.
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"], [
                (spike_x, spike_tip_y),
                (spike_x, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            # Bright edge highlight.
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_light"],
                                    (spike_x, spike_tip_y),
                                    (spike_x - 1, spike_base_y), 1)
            # Glow tip.
            for gr in range(2, 0, -1):
                alpha = _NS_cryssalia._alpha(180 * pulse * (2 - gr) / 2)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (spike_x, spike_tip_y), gr)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))

        # Central big gem in crown band.
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_dark"],
                         (cx - 1, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_light"],
                         (cx, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                         (cx, cy - 5, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        """Back arm - gesturing/casting."""
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 4

        if action == "cast":
            elbow_x = shoulder_x - facing * 6
            elbow_y = shoulder_y - 2
            hand_x = shoulder_x - facing * 12
            hand_y = shoulder_y - 8
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x - facing * 5
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x - facing * 8
            hand_y = shoulder_y + 10

        # Shadow.
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                                (shoulder_x + 2, shoulder_y + 2),
                                (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm (dress sleeve, blue).
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["robe_darkest"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["robe_dark"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["robe_mid"],
                                (shoulder_x, shoulder_y - 1),
                                (elbow_x, elbow_y - 1), 1)
        # Forearm - flowing wide sleeve.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["robe_darkest"], [
            (elbow_x - 2, elbow_y - 1), (elbow_x + 2, elbow_y + 1),
            (hand_x + 4, hand_y + 3), (hand_x - 4, hand_y - 3),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["robe_dark"], [
            (elbow_x - 1, elbow_y), (elbow_x + 1, elbow_y),
            (hand_x + 3, hand_y + 2), (hand_x - 3, hand_y - 2),
        ])
        # Gold cuff.
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_dark"],
                         (hand_x - 4, hand_y - 3), (hand_x + 4, hand_y + 3), 2)
        pygame.draw.line(surface, _NS_cryssalia.PALETTE["gold_mid"],
                         (hand_x - 3, hand_y - 2), (hand_x + 3, hand_y + 2), 1)
        # Hand (pale skin).
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 3)
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["skin_mid"],
                                 (hand_x, hand_y - 1), 2)

        # Ice sparkles at fingertips.
        if action == "cast":
            for finger_i in range(3):
                fx = hand_x - facing * 2 + finger_i - 1
                fy = hand_y - 3
                pulse = math.sin(phase * 3 + finger_i) * 0.3 + 0.7
                alpha = _NS_cryssalia._alpha(220 * pulse)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (fx, fy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                                 (fx, fy, 1, 1))

    def _draw_staff_arm(surface, cx, cy, facing, phase, action, progress):
        """Front arm holding ice staff."""
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 4

        if action == "attack":
            # Reach forward casting.
            elbow_x = shoulder_x + facing * 5
            elbow_y = shoulder_y + 2
            hand_x = shoulder_x + facing * 12
            hand_y = shoulder_y - 4
            staff_angle = -math.pi / 4 if facing > 0 else math.pi + math.pi / 4
        elif action == "cast":
            # Staff raised high.
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y - 6
            hand_x = shoulder_x + facing * 8
            hand_y = shoulder_y - 14
            staff_angle = -math.pi / 2 + 0.15
        else:
            # Idle: staff held vertical.
            sway = math.sin(phase * 0.6) * 1
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x + facing * 8
            hand_y = shoulder_y + 2 + int(sway)
            staff_angle = -math.pi / 2 + 0.1

        # Shadow.
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                                (shoulder_x + 2, shoulder_y + 2),
                                (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm.
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["dress_darkest"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["dress_dark"],
                                (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["dress_mid"],
                                (shoulder_x, shoulder_y - 1),
                                (elbow_x, elbow_y - 1), 1)
        # Forearm.
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["dress_darkest"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["dress_dark"],
                                (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Gold bracer.
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["gold_dark"],
                                 (hand_x, hand_y), 3)
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["gold_mid"],
                                 (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["gold_shine"],
                         (hand_x, hand_y - 1, 1, 1))
        # Hand.
        _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 2)

        # Draw ice staff.
        _NS_cryssalia._draw_ice_staff(surface, hand_x, hand_y, staff_angle,
                                        facing, phase)

    def _draw_ice_staff(surface, hx, hy, angle, facing, phase):
        """Long staff with big ice crystal cluster on top."""
        length = 40
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        top_x = hx + int(dx * length)
        top_y = hy + int(dy * length)
        bot_x = hx - int(dx * 10)
        bot_y = hy - int(dy * 10)

        # Shadow.
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["shadow_deep"],
                                (bot_x + 2, bot_y + 2), (top_x + 2, top_y + 2), 4)
        # Staff shaft (silver/white with blue).
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["frost_darkest"],
                                (bot_x, bot_y), (top_x, top_y), 4)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["frost_dark"],
                                (bot_x, bot_y), (top_x, top_y), 3)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_dark"],
                                (bot_x, bot_y), (top_x, top_y), 1)
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_light"],
                                (bot_x, bot_y - 1), (top_x, top_y - 1), 1)

        # Decorative rings.
        for t_ring in (0.3, 0.6):
            rx = int(bot_x + (top_x - bot_x) * t_ring)
            ry = int(bot_y + (top_y - bot_y) * t_ring)
            perp = angle + math.pi / 2
            r_a = (rx + int(math.cos(perp) * 3), ry + int(math.sin(perp) * 3))
            r_b = (rx - int(math.cos(perp) * 3), ry - int(math.sin(perp) * 3))
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["gold_dark"],
                                    r_a, r_b, 2)
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["gold_light"],
                                    r_a, r_b, 1)

        # ICE CRYSTAL CLUSTER at top (large + shards).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Central big shard.
        perp = angle + math.pi / 2
        central_tip = (top_x + int(dx * 12), top_y + int(dy * 12))
        central_a = (top_x + int(math.cos(perp) * 4),
                     top_y + int(math.sin(perp) * 4))
        central_b = (top_x - int(math.cos(perp) * 4),
                     top_y - int(math.sin(perp) * 4))
        central_bot = (top_x + int(dx * 2), top_y + int(dy * 2))

        # Shadow.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
            (central_tip[0] + 2, central_tip[1] + 2),
            (central_a[0] + 2, central_a[1] + 2),
            (central_bot[0] + 2, central_bot[1] + 2),
            (central_b[0] + 2, central_b[1] + 2),
        ])
        # Crystal body layers.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_darkest"],
                             [central_tip, central_a, central_bot, central_b])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
            central_tip,
            (int((central_tip[0] + central_a[0]) / 2),
             int((central_tip[1] + central_a[1]) / 2)),
            central_bot,
            (int((central_tip[0] + central_b[0]) / 2),
             int((central_tip[1] + central_b[1]) / 2)),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"],
                             [central_tip, (top_x, top_y), central_bot])
        # Bright center.
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_light"],
                                central_tip, central_bot, 1)
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                         (central_tip[0], central_tip[1], 1, 1))
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                         (central_tip[0], central_tip[1], 1, 1))

        # Side smaller shards (2 on each side).
        for shard_i, (side_mult, offset_len) in enumerate([
            (-1, 6), (1, 6), (-1, 3), (1, 3),
        ]):
            side_perp_x = int(math.cos(perp) * side_mult * 3)
            side_perp_y = int(math.sin(perp) * side_mult * 3)
            base_pt = (top_x + side_perp_x, top_y + side_perp_y)
            tip_pt = (top_x + int(dx * offset_len) + side_perp_x * 2,
                      top_y + int(dy * offset_len) + side_perp_y * 2)
            perp2 = angle + math.pi / 2
            w_a = (base_pt[0] + int(math.cos(perp2) * 2),
                   base_pt[1] + int(math.sin(perp2) * 2))
            w_b = (base_pt[0] - int(math.cos(perp2) * 2),
                   base_pt[1] - int(math.sin(perp2) * 2))
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"],
                                 [tip_pt, w_a, w_b])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"], [
                tip_pt,
                (int((tip_pt[0] + w_a[0]) / 2), int((tip_pt[1] + w_a[1]) / 2)),
                base_pt,
            ])
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (tip_pt[0], tip_pt[1], 1, 1))

        # Big glow aura around crystal.
        for r in range(10, 1, -1):
            alpha = _NS_cryssalia._alpha(100 * (10 - r) / 10 * pulse)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                                     (top_x, top_y), r)

    # ============================================================
    # BASIC ATTACK ICE SHARD PROJECTILE
    # ============================================================
    def _draw_ice_shard(surface, boss, x, y):
        """Ice shard projectile as basic attack."""
        progress = getattr(boss, "_cs_attack_progress", 0)
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_cryssalia._target_position(boss, x, y)

        # Launch from staff top.
        start_x = x + facing * 20
        start_y = y - 20

        t = (progress - 0.5) / 0.5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (frost particles).
        for i in range(10):
            trail_t = max(0.0, t - i * 0.04)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_cryssalia._alpha(220 - i * 22)
            size = max(1, 5 - i)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_dark"], alpha),
                                     (px, py), size + 1)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_mid"], alpha),
                                     (px, py), size)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                                     (px, py), max(1, size - 2))

            # Snowflake sparkles.
            if i < 4:
                spark_x = px + int(math.sin(t * 6 + i) * 3)
                spark_y = py + int(math.cos(t * 6 + i) * 3)
                pygame.draw.rect(surface,
                                 (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                                 (spark_x, spark_y, 1, 1))

        # Ice shard head (diamond).
        angle = math.atan2(ty - start_y, tx - start_x)
        perp = angle + math.pi / 2
        tip_x = bx + int(math.cos(angle) * 8)
        tip_y = by + int(math.sin(angle) * 8)
        back_x = bx - int(math.cos(angle) * 6)
        back_y = by - int(math.sin(angle) * 6)
        wing_a = (bx + int(math.cos(perp) * 4), by + int(math.sin(perp) * 4))
        wing_b = (bx - int(math.cos(perp) * 4), by - int(math.sin(perp) * 4))

        # Shadow.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1), (wing_a[0] + 1, wing_a[1] + 1),
            (back_x + 1, back_y + 1), (wing_b[0] + 1, wing_b[1] + 1),
        ])
        # Shard.
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_darkest"], [
            (tip_x, tip_y), wing_a, (back_x, back_y), wing_b,
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
            (tip_x, tip_y),
            (int((tip_x + wing_a[0]) / 2), int((tip_y + wing_a[1]) / 2)),
            (back_x, back_y),
            (int((tip_x + wing_b[0]) / 2), int((tip_y + wing_b[1]) / 2)),
        ])
        _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"], [
            (tip_x, tip_y), (bx, by), (back_x, back_y),
        ])
        _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_shine"],
                                (tip_x, tip_y), (back_x, back_y), 1)
        pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

        # Glow around shard.
        for r in range(6, 1, -1):
            alpha = _NS_cryssalia._alpha(100 * (6 - r) / 6)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                                     (bx, by), r)

        # Impact.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            r = int(6 + st * 12)
            alpha = _NS_cryssalia._alpha(230 * (1 - st))
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_dark"], alpha),
                                     (tx, ty), r + 1, 2)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                                     (tx, ty), r, 1)
            # Small ice shards flying out.
            for i in range(6):
                a = i * math.pi / 3
                ex = tx + int(math.cos(a) * r)
                ey = ty + int(math.sin(a) * r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_cryssalia.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # FLOAT SNOWFLAKES
    # ============================================================
    def _draw_float_snowflakes(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        # Ice pool below.
        pool = pygame.Surface((110, 28), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for r in range(22, 2, -2):
            alpha = _NS_cryssalia._alpha((22 - r) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_cryssalia.PALETTE["ice_darkest"],
                                     alpha),
                                    (55 - r, 14 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(13, 1, -1):
            alpha = _NS_cryssalia._alpha((13 - r) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_cryssalia.PALETTE["ice_mid"], alpha),
                                    (55 - r, 14 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 55, cy - 5))

        # Falling/floating snowflakes.
        for i in range(12):
            t = (phase * 0.4 + i * 0.09) % 1.0
            sx = cx - 30 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 15 - int(t * 30)
            alpha = _NS_cryssalia._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Draw snowflake (small cross).
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (sx - 1, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (sx + 1, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (sx, sy + 1, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 32), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            alpha = max(0, (14 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 15 - r,
                                 120 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (10, 20, 40, 170), (5, 10, 130, 14))
        pygame.draw.ellipse(shadow, (60, 130, 200, 100), (12, 12, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_frost_aura(surface, x, y, phase):
        """Blue frost aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 220), pygame.SRCALPHA)
        for r in range(105, 5, -5):
            alpha = _NS_cryssalia._alpha((105 - r) * 1.1 * pulse)
            if alpha > 0:
                _NS_cryssalia._aacircle(aura,
                                         (*_NS_cryssalia.PALETTE["frost_darkest"],
                                          alpha), (120, 110), r)
        for r in range(65, 5, -4):
            alpha = _NS_cryssalia._alpha((65 - r) * 1.3 * pulse)
            if alpha > 0:
                _NS_cryssalia._aacircle(aura,
                                         (*_NS_cryssalia.PALETTE["frost_dark"],
                                          alpha), (120, 110), r)
        for r in range(40, 5, -3):
            alpha = _NS_cryssalia._alpha((40 - r) * 1.5 * pulse)
            if alpha > 0:
                _NS_cryssalia._aacircle(aura,
                                         (*_NS_cryssalia.PALETTE["ice_dark"],
                                          alpha // 2), (120, 110), r)
        surface.blit(aura, (x - 120, y - 110))

        # Snowflake sparkles orbiting.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 50 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_cryssalia.PALETTE["rune_dark"], 200),
                            (5, 16, 160, 26), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_cryssalia.PALETTE["ice_darkest"], 220),
                            (14, 18, 142, 22), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_cryssalia.PALETTE["ice_dark"], 230),
                            (25, 20, 120, 18), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 45)
            y1 = 29 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 29 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_cryssalia.PALETTE["ice_light"], 220),
                             (x1, y1), (x2, y2), 1)

        # Small snowflakes on ring.
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sx = 85 + int(math.cos(angle) * 60)
            sy = 29 + int(math.sin(angle) * 10)
            pygame.draw.rect(ring, (*_NS_cryssalia.PALETTE["ice_shine"], 220),
                             (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_cryssalia.PALETTE["ice_hot"],
                                 _NS_cryssalia._alpha(150 * pulse)),
                                (15, 12, 140, 34), 1)
        surface.blit(ring, (x - 85, y - 25))

    # ============================================================
    # SKILL Q: FROST SHOCK - long ice shard projectile
    # ============================================================
    def _draw_frostshock_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_cryssalia._target_position(boss, x, y)

        if progress < 0.3:
            # Charge at staff.
            t = progress / 0.3
            hx = x + facing * 20
            hy = y - 20
            cr = int(3 + t * 7)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_cryssalia._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_mid"],
                                          alpha), (hx, hy), r)
            _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["ice_light"],
                                     (hx, hy), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (hx, hy, 1, 1))
        else:
            # BIG ice shard projectile.
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 20
            start_y = y - 20
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long trail.
            for i in range(14):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_cryssalia._alpha(240 - i * 17)
                size = max(1, 8 - i)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_darkest"],
                                          alpha), (px, py), size + 1)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_dark"],
                                          alpha), (px, py), size)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_mid"],
                                          alpha), (px, py), max(1, size - 2))
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (px, py), max(1, size - 4))
                # Snowflake trail sparkles.
                if i < 6:
                    spark_x = px + int(math.sin(t * 8 + i) * 4)
                    spark_y = py + int(math.cos(t * 8 + i) * 4)
                    pygame.draw.rect(surface,
                                     (*_NS_cryssalia.PALETTE["ice_shine"],
                                      alpha), (spark_x, spark_y, 1, 1))

            # BIG ice shard head (elongated diamond).
            angle = math.atan2(ty - start_y, tx - start_x)
            perp = angle + math.pi / 2
            tip_x = bx + int(math.cos(angle) * 14)
            tip_y = by + int(math.sin(angle) * 14)
            back_x = bx - int(math.cos(angle) * 10)
            back_y = by - int(math.sin(angle) * 10)
            wing_a = (bx + int(math.cos(perp) * 6),
                      by + int(math.sin(perp) * 6))
            wing_b = (bx - int(math.cos(perp) * 6),
                      by - int(math.sin(perp) * 6))

            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
                (tip_x + 2, tip_y + 2), (wing_a[0] + 2, wing_a[1] + 2),
                (back_x + 2, back_y + 2), (wing_b[0] + 2, wing_b[1] + 2),
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_darkest"], [
                (tip_x, tip_y), wing_a, (back_x, back_y), wing_b,
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
                (tip_x, tip_y),
                (int((tip_x + wing_a[0]) / 2), int((tip_y + wing_a[1]) / 2)),
                (back_x, back_y),
                (int((tip_x + wing_b[0]) / 2), int((tip_y + wing_b[1]) / 2)),
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"], [
                (tip_x, tip_y), (bx, by), (back_x, back_y),
            ])
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_light"],
                                    (tip_x, tip_y), (back_x, back_y), 1)
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_shine"],
                                    (tip_x, tip_y),
                                    (int((tip_x + back_x) / 2),
                                     int((tip_y + back_y) / 2)), 1)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))

            # Large glow.
            for r in range(12, 2, -2):
                alpha = _NS_cryssalia._alpha(80 * (12 - r) / 12)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (bx, by), r)

            # Impact big.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                r = int(15 + st * 25)
                alpha = _NS_cryssalia._alpha(240 * (1 - st))
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_darkest"],
                                          alpha), (tx, ty), r + 3, 3)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_dark"],
                                          alpha), (tx, ty), r, 2)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (tx, ty), max(1, r - 6), 1)
                # Ice shards flying.
                for i in range(10):
                    a = i * math.pi / 5
                    ex = tx + int(math.cos(a) * r)
                    ey = ty + int(math.sin(a) * r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_cryssalia.PALETTE["ice_shine"],
                                      alpha), (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_cryssalia.PALETTE["white"], alpha),
                                     (ex, ey, 1, 1))

    # ============================================================
    # SKILL W: BITTER FROST - curved wave of frost
    # ============================================================
    def _draw_bitterfrost_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            return

        # Ground frost as wave expands.
        t = (progress - 0.3) / 0.7
        # Wave along curved arc.
        radius = int(20 + t * 90)
        alpha = _NS_cryssalia._alpha(160 * (1 - t * 0.5))
        # Arc of ground frost.
        for angle_i in range(-3, 4):
            a = angle_i * 0.3 * facing
            gx = x + int(math.cos(a) * radius) * facing
            gy = y + 45 + int(math.sin(a) * radius * 0.4)
            gr = 10
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_dark"], alpha),
                                (gx - gr, gy - gr // 3,
                                 gr * 2, gr * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_mid"], alpha),
                                (gx - gr + 2, gy - gr // 3 + 1,
                                 gr * 2 - 4, gr * 2 // 3 - 2))

    def _draw_bitterfrost_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charging on hand.
            t = progress / 0.3
            hx = x + facing * 20
            hy = y - 4
            cr = int(3 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_cryssalia._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_mid"],
                                          alpha), (hx, hy), r)
            _NS_cryssalia._aacircle(surface, _NS_cryssalia.PALETTE["ice_light"],
                                     (hx, hy), max(1, cr - 2))
            return

        # BIG CURVED FROST WAVE.
        t = (progress - 0.3) / 0.7
        intensity = math.sin(t * math.pi) * 0.5 + 0.5

        # Multiple wave arcs.
        for wave_i in range(3):
            wave_offset = wave_i * 0.15
            actual_t = max(0.0, t - wave_offset)
            if actual_t > 1.0:
                continue

            # Wave sweeps in an arc.
            radius = int(20 + actual_t * 100)
            for a_step in range(-15, 16):
                a = a_step * 0.06 * facing
                wx = x + int(math.cos(a) * radius) * facing
                wy = y - 8 + int(math.sin(a) * radius * 0.5)

                alpha = _NS_cryssalia._alpha(230 * intensity
                                              * (1 - abs(a_step) / 15 * 0.5)
                                              * (1 - wave_i * 0.25))
                if alpha <= 0:
                    continue
                size = max(1, 5 - wave_i)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_dark"],
                                          alpha), (wx, wy), size + 1)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_mid"],
                                          alpha), (wx, wy), size)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (wx, wy), max(1, size - 2))
                pygame.draw.rect(surface,
                                 (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                                 (wx, wy, 1, 1))

        # Snowflake sparkles scattered.
        for i in range(20):
            angle = i * math.pi * 2 / 20 + phase * 0.5
            dist = int(30 + t * 80 + (i % 3) * 8)
            sx = x + int(math.cos(angle) * dist) * (1 if angle < math.pi else -1) * facing
            # Actually simpler: just spread in a wave shape.
            sx = x + int(math.cos(angle * 0.5) * dist) * facing
            sy = y - 8 + int(math.sin(angle) * dist * 0.4)
            alpha = _NS_cryssalia._alpha(200 * intensity)
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["white"], alpha),
                             (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: FROST BITES - ice spikes at target area
    # ============================================================
    def _draw_frostbites_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cryssalia._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            # Warning circle grows.
            t = progress / 0.25
            r = int(45 * t)
            alpha = _NS_cryssalia._alpha(180 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_dark"], alpha),
                                (tx - r, ty - r // 3,
                                 r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning runes.
            for i in range(8):
                a = i * math.pi / 4 + phase
                sx = tx + int(math.cos(a) * r)
                sy = ty + int(math.sin(a) * r * 0.4)
                pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_light"],
                                 (sx, sy, 2, 2))
        else:
            # Frozen ground.
            r = 50
            alpha = _NS_cryssalia._alpha(200 * (1 - (progress - 0.25) / 0.75 * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_darkest"], alpha),
                                (tx - r, ty - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_cryssalia.PALETTE["ice_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_frostbites_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cryssalia._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            return

        # BIG ICE SPIKES erupt from ground (signature!).
        t = (progress - 0.25) / 0.75

        num_spikes = 12
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + t * 0.3
            spread_dist = 10 + (i % 4) * 12
            spike_x = tx + int(math.cos(angle) * spread_dist)
            spike_base_y = ty + int(math.sin(angle) * spread_dist * 0.4)

            # Staggered rise.
            spike_progress = min(1.0, max(0.0, t * 2.5 - i * 0.06))
            if spike_progress < 0.05:
                continue

            # Big ice spike.
            max_h = 35 + (i % 3) * 10
            spike_h = int(spike_progress * max_h)
            if spike_progress > 0.7:
                fade = 1 - (spike_progress - 0.7) / 0.3
                spike_h = int(spike_h * (0.6 + fade * 0.4))

            if spike_h < 3:
                continue

            spike_tip_y = spike_base_y - spike_h
            spike_width = 3 + (i % 2)

            # Shadow.
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - spike_width + 1, spike_base_y + 1),
                (spike_x + spike_width + 1, spike_base_y + 1),
            ])
            # Layered ice spike.
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - spike_width, spike_base_y),
                (spike_x + spike_width, spike_base_y),
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - spike_width + 1, spike_base_y),
                (spike_x + spike_width - 1, spike_base_y),
            ])
            _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            # Bright center vein.
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_light"],
                                    (spike_x, spike_tip_y),
                                    (spike_x, spike_base_y), 1)
            _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_shine"],
                                    (spike_x, spike_tip_y + 1),
                                    (spike_x, spike_base_y - 2), 1)

            # Bright glow tip.
            for gr in range(3, 0, -1):
                alpha = _NS_cryssalia._alpha(120 * (3 - gr) / 3)
                _NS_cryssalia._aacircle(surface,
                                         (*_NS_cryssalia.PALETTE["ice_light"],
                                          alpha), (spike_x, spike_tip_y), gr)
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))

        # Rising snowflakes.
        for i in range(15):
            p_t = (phase * 1.2 + i * 0.09) % 1.0
            angle = i * math.pi * 2 / 15
            px = tx + int(math.cos(angle) * 40)
            py = ty + 20 - int(p_t * 60)
            alpha = _NS_cryssalia._alpha(230 * (1 - p_t))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (px, py, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["white"], alpha),
                             (px, py, 1, 1))

    # ============================================================
    # SKILL R: COLD DESTRUCTION - blizzard with falling shards + rising crystals
    # ============================================================
    def _draw_colddest_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cryssalia._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Big ground freeze zone.
        r = int(70 * min(1.0, progress * 2))
        if r < 5:
            return

        alpha = _NS_cryssalia._alpha(200 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface,
                            (*_NS_cryssalia.PALETTE["ice_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_cryssalia.PALETTE["ice_dark"], alpha),
                            (tx - r + 4, ty - r // 3 + 2,
                             r * 2 - 8, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface,
                            (*_NS_cryssalia.PALETTE["ice_mid"], alpha // 2),
                            (tx - r + 10, ty - r // 3 + 4,
                             r * 2 - 20, r * 2 // 3 - 8))

    def _draw_colddest_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cryssalia._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Falling ice shards from sky.
        num_falls = 15
        for i in range(num_falls):
            fall_t = (phase * 0.8 + i * 0.11) % 1.0
            if fall_t > progress * 1.5:
                continue
            fall_x = tx + int(math.sin(i * 1.3) * 60)
            fall_y_start = max(0, ty - 200)
            fall_y = int(fall_y_start + fall_t * (ty - fall_y_start))
            alpha = _NS_cryssalia._alpha(240 * (1 - fall_t * 0.3))

            # Small ice shard falling.
            _NS_cryssalia._poly(surface, (*_NS_cryssalia.PALETTE["ice_dark"], alpha), [
                (fall_x, fall_y - 4), (fall_x + 2, fall_y),
                (fall_x, fall_y + 2), (fall_x - 2, fall_y),
            ])
            _NS_cryssalia._poly(surface, (*_NS_cryssalia.PALETTE["ice_mid"], alpha), [
                (fall_x, fall_y - 3), (fall_x + 1, fall_y),
                (fall_x, fall_y + 1), (fall_x - 1, fall_y),
            ])
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_light"], alpha),
                             (fall_x, fall_y - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (fall_x, fall_y - 2, 1, 1))
            # Trail.
            pygame.draw.line(surface,
                             (*_NS_cryssalia.PALETTE["ice_light"], alpha // 2),
                             (fall_x, fall_y), (fall_x, fall_y - 6), 1)

        # Rising crystals at ground (staggered like blizzard).
        if progress > 0.2:
            t_rise = min(1.0, (progress - 0.2) / 0.8)
            num_crystals = 10
            for i in range(num_crystals):
                angle = i * math.pi * 2 / num_crystals + t_rise * 0.5
                dist = 20 + (i % 3) * 15
                cx_i = tx + int(math.cos(angle) * dist)
                cy_base = ty + int(math.sin(angle) * dist * 0.4)

                crystal_progress = min(1.0, max(0.0, t_rise * 2 - i * 0.05))
                if crystal_progress < 0.1:
                    continue

                # Tall crystal spike.
                crystal_h = int(crystal_progress * 45)
                if crystal_h < 5:
                    continue

                crystal_tip_y = cy_base - crystal_h
                crystal_width = 3

                _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["shadow_deep"], [
                    (cx_i + 1, crystal_tip_y + 1),
                    (cx_i - crystal_width + 1, cy_base + 1),
                    (cx_i + crystal_width + 1, cy_base + 1),
                ])
                _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_darkest"], [
                    (cx_i, crystal_tip_y),
                    (cx_i - crystal_width, cy_base),
                    (cx_i + crystal_width, cy_base),
                ])
                _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_dark"], [
                    (cx_i, crystal_tip_y),
                    (cx_i - crystal_width + 1, cy_base),
                    (cx_i + crystal_width - 1, cy_base),
                ])
                _NS_cryssalia._poly(surface, _NS_cryssalia.PALETTE["ice_mid"], [
                    (cx_i, crystal_tip_y),
                    (cx_i, cy_base),
                    (cx_i + 1, cy_base),
                ])
                _NS_cryssalia._aaline(surface, _NS_cryssalia.PALETTE["ice_light"],
                                        (cx_i, crystal_tip_y),
                                        (cx_i, cy_base), 1)
                # Bright tip.
                pygame.draw.rect(surface, _NS_cryssalia.PALETTE["ice_shine"],
                                 (cx_i, crystal_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_cryssalia.PALETTE["white"],
                                 (cx_i, crystal_tip_y, 1, 1))
                for gr in range(2, 0, -1):
                    alpha = _NS_cryssalia._alpha(150 * (2 - gr) / 2)
                    _NS_cryssalia._aacircle(surface,
                                             (*_NS_cryssalia.PALETTE["ice_light"],
                                              alpha),
                                             (cx_i, crystal_tip_y), gr)

        # Blizzard sparkles everywhere.
        for i in range(30):
            spark_t = (phase * 1.5 + i * 0.07) % 1.0
            sx = tx + int(math.sin(phase * 2 + i * 0.5) * 70)
            sy = ty - 50 + int(spark_t * 100)
            alpha = _NS_cryssalia._alpha(200 * (1 - spark_t))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["ice_shine"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_cryssalia.PALETTE["white"], alpha),
                             (sx, sy, 1, 1))

        # Big central impact when starting.
        if progress < 0.3:
            t = progress / 0.3
            r_impact = int(30 * t)
            alpha = _NS_cryssalia._alpha(240 * t)
            _NS_cryssalia._aacircle(surface,
                                     (*_NS_cryssalia.PALETTE["ice_light"],
                                      alpha), (tx, ty), r_impact, 2)


# ====================================================================
# kaelthar.py
# ====================================================================

"""
KAELTHAR - The Storm Fist
Mini boss martial artist fighter dengan lightning fist power.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_kaelthar:
    """Namespace kaelthar - storm fist mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin tones (tan warrior)
        "skin_darkest": (55, 30, 20),
        "skin_dark": (110, 65, 45),
        "skin_mid": (165, 110, 75),
        "skin_light": (210, 155, 110),
        "skin_shine": (240, 200, 160),

        # Muscle shadow
        "muscle_shadow": (75, 40, 25),
        "muscle_deep": (40, 20, 12),

        # Black hair
        "hair_darkest": (10, 10, 20),
        "hair_dark": (30, 30, 45),
        "hair_mid": (60, 60, 80),
        "hair_light": (100, 100, 130),

        # Blue bandana
        "bandana_darkest": (10, 20, 55),
        "bandana_dark": (25, 55, 115),
        "bandana_mid": (55, 110, 200),
        "bandana_light": (120, 175, 250),

        # Brown pants
        "pants_darkest": (25, 15, 8),
        "pants_dark": (60, 40, 20),
        "pants_mid": (100, 70, 35),
        "pants_light": (155, 115, 65),

        # Blue sash
        "sash_darkest": (10, 25, 65),
        "sash_dark": (30, 60, 130),
        "sash_mid": (65, 115, 210),
        "sash_light": (130, 180, 250),

        # Gold accents (belt buckle, jewelry)
        "gold_dark": (95, 65, 15),
        "gold_mid": (180, 140, 45),
        "gold_light": (245, 210, 95),
        "gold_shine": (255, 245, 180),

        # Bandage wraps (arms/wrists - dark brown/black)
        "wrap_darkest": (15, 8, 5),
        "wrap_dark": (40, 25, 15),
        "wrap_mid": (75, 55, 35),

        # ELECTRIC BLUE LIGHTNING (main theme)
        "storm_darkest": (5, 20, 60),
        "storm_dark": (20, 70, 160),
        "storm_mid": (60, 140, 240),
        "storm_light": (130, 210, 255),
        "storm_hot": (200, 240, 255),
        "storm_shine": (240, 250, 255),
        "storm_white": (250, 253, 255),

        # Deep electric blue
        "elec_darkest": (5, 15, 45),
        "elec_dark": (15, 45, 110),
        "elec_mid": (40, 100, 200),

        # Tribal tattoo
        "tattoo_dark": (15, 35, 90),
        "tattoo_mid": (40, 90, 175),
        "tattoo_glow": (100, 180, 255),

        # Eye (fierce)
        "eye_dark": (10, 8, 15),
        "eye_white": (230, 225, 220),
        "eye_blue": (80, 160, 240),

        # Ground/rune
        "rune_dark": (10, 25, 60),
        "rune_mid": (50, 120, 220),
        "rune_light": (150, 220, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 6),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaelthar._clamp(color)
        if _NS_kaelthar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaelthar._clamp(color)
        if _NS_kaelthar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue
        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_kaelthar._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_kaelthar._clamp(color), valid_points)

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
    def draw_kaelthar(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_kaelthar._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kth_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_kaelthar._draw_storm_aura(surface, x, y, pulse)
        _NS_kaelthar._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_kaelthar._draw_quake_ground(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelthar._draw_fistbreak_ground(surface, boss, x, y,
                                                  skill_timer, pulse)

        # Body pose.
        if active_skill == "r":
            _NS_kaelthar._draw_body_leap(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelthar._draw_body_slam(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_kaelthar._draw_body_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelthar._draw_body_dash(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_kaelthar._draw_body_attack(surface, boss, x, y)
        else:
            _NS_kaelthar._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "q":
            _NS_kaelthar._draw_charging_fist_fg(surface, boss, x, y,
                                                  skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelthar._draw_quake_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelthar._draw_fistcrack_fg(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelthar._draw_fistbreak_fg(surface, boss, x, y,
                                              skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kth_previous_timer", 0))
        active = bool(getattr(boss, "_kth_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._kth_attack_active = True
            boss._kth_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._kth_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._kth_attack_frame = int(getattr(boss, "_kth_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kth_attack_active = False
            boss._kth_attack_frame = 0
            active = False

        boss._kth_previous_timer = timer
        boss._kth_attack_progress = (
            min(1.0, getattr(boss, "_kth_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 4)
        _NS_kaelthar._draw_shadow(surface, x, y + 50)
        _NS_kaelthar._draw_lightning_particles(surface, x, y + 40, boss.pulse)
        _NS_kaelthar._draw_fighter_body(surface, x, y + bob, boss.direction,
                                          boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_kth_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_kth_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        # Quick punch lunge.
        if progress < 0.4:
            lunge = int(progress / 0.4 * 6) * facing
        else:
            lunge = int((1 - (progress - 0.4) / 0.6) * 6) * facing

        _NS_kaelthar._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaelthar._draw_lightning_particles(surface, x + lunge, y + 40, boss.pulse)
        _NS_kaelthar._draw_fighter_body(surface, x + lunge, y + bob,
                                          facing, boss.pulse,
                                          "attack", progress)
        _NS_kaelthar._draw_punch_swing(surface, x + lunge, y + bob,
                                         facing, progress)

    def _draw_body_charge(surface, boss, x, y, timer, pulse):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.7) * 2)
        # Charge forward.
        if progress < 0.5:
            lunge = int(progress / 0.5 * 35) * boss.direction
        else:
            lunge = int(35) * boss.direction

        _NS_kaelthar._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaelthar._draw_lightning_particles(surface, x + lunge, y + 40, pulse,
                                                 intense=True)
        _NS_kaelthar._draw_fighter_body(surface, x + lunge, y + bob,
                                          boss.direction, pulse, "charge",
                                          progress)

    def _draw_body_dash(surface, boss, x, y, timer, pulse):
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.7) * 2)
        # Fast dash forward.
        if progress < 0.6:
            lunge = int(progress / 0.6 * 40) * boss.direction
        else:
            lunge = int(40) * boss.direction

        _NS_kaelthar._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaelthar._draw_lightning_particles(surface, x + lunge, y + 40, pulse,
                                                 intense=True)
        _NS_kaelthar._draw_fighter_body(surface, x + lunge, y + bob,
                                          boss.direction, pulse, "dash",
                                          progress)

    def _draw_body_slam(surface, boss, x, y, timer, pulse):
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Rear up then slam.
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 15)
        elif progress < 0.55:
            lift = 15
        else:
            t = (progress - 0.55) / 0.45
            lift = int(15 * (1 - t))

        _NS_kaelthar._draw_shadow(surface, x, y + 50)
        _NS_kaelthar._draw_lightning_particles(surface, x, y + 40, pulse,
                                                 intense=True)
        _NS_kaelthar._draw_fighter_body(surface, x, y - lift, boss.direction,
                                          pulse, "slam", progress)

    def _draw_body_leap(surface, boss, x, y, timer, pulse):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big leap up then slam.
        if progress < 0.4:
            t = progress / 0.4
            lift = int(t * 80)
        elif progress < 0.7:
            lift = 80
        else:
            t = (progress - 0.7) / 0.3
            lift = int(80 * (1 - t) - t * 5)

        _NS_kaelthar._draw_shadow(surface, x, y + 50)
        _NS_kaelthar._draw_lightning_particles(surface, x, y + 40, pulse)
        _NS_kaelthar._draw_fighter_body(surface, x, y - lift, boss.direction,
                                          pulse, "leap", progress)

    # ============================================================
    # FIGHTER BODY (muscular martial artist)
    # ============================================================
    def _draw_fighter_body(surface, cx, cy, facing, phase, action,
                            progress=0):
        """Full fighter body: legs, torso muscular topless, arms, head with bandana."""
        _NS_kaelthar._draw_back_leg(surface, cx, cy, facing, phase, action)
        _NS_kaelthar._draw_front_leg(surface, cx, cy, facing, phase, action)
        _NS_kaelthar._draw_pants_sash(surface, cx, cy, facing, phase)
        _NS_kaelthar._draw_muscular_torso(surface, cx, cy, facing, phase, action)
        _NS_kaelthar._draw_back_arm(surface, cx, cy, facing, phase, action,
                                      progress)
        _NS_kaelthar._draw_head_bandana(surface, cx, cy - 22, facing, phase, action)
        _NS_kaelthar._draw_front_arm(surface, cx, cy, facing, phase, action,
                                       progress)

    def _draw_back_leg(surface, cx, cy, facing, phase, action):
        base_x = cx - facing * 4
        knee_x = cx - facing * 6
        knee_y = cy + 18
        foot_x = cx - facing * 6
        foot_y = cy + 32

        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                              (base_x + 2, cy + 8), (knee_x + 2, knee_y + 1), 7)
        # Thigh (brown pants).
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_darkest"], [
            (base_x - 4, cy + 8), (base_x + 3, cy + 8),
            (knee_x + 3, knee_y), (knee_x - 3, knee_y),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_dark"], [
            (base_x - 3, cy + 9), (base_x + 2, cy + 9),
            (knee_x + 2, knee_y - 1), (knee_x - 2, knee_y - 1),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_mid"], [
            (base_x - 1, cy + 10), (base_x + 1, cy + 10),
            (knee_x + 1, knee_y - 2), (knee_x, knee_y - 2),
        ])
        # Shin (still pants).
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_darkest"], [
            (knee_x - 3, knee_y), (knee_x + 3, knee_y),
            (foot_x + 2, foot_y), (foot_x - 2, foot_y),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_dark"], [
            (knee_x - 2, knee_y + 1), (knee_x + 2, knee_y + 1),
            (foot_x + 1, foot_y - 1), (foot_x - 1, foot_y - 1),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 1, knee_y + 2),
            (foot_x, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        # Foot (bare/sandal - dark).
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["wrap_darkest"], [
            (foot_x - 5, foot_y - 1), (foot_x + 4, foot_y - 1),
            (foot_x + 4, foot_y + 2), (foot_x - 5, foot_y + 2),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["wrap_dark"], [
            (foot_x - 4, foot_y), (foot_x + 3, foot_y),
            (foot_x + 3, foot_y + 1), (foot_x - 4, foot_y + 1),
        ])

    def _draw_front_leg(surface, cx, cy, facing, phase, action):
        base_x = cx + facing * 4
        knee_x = cx + facing * 6
        knee_y = cy + 18
        foot_x = cx + facing * 8
        foot_y = cy + 32

        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                              (base_x + 2, cy + 8), (knee_x + 2, knee_y + 1), 8)
        # Thigh.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_darkest"], [
            (base_x - 4, cy + 8), (base_x + 4, cy + 8),
            (knee_x + 4, knee_y), (knee_x - 4, knee_y),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_dark"], [
            (base_x - 3, cy + 9), (base_x + 3, cy + 9),
            (knee_x + 3, knee_y - 1), (knee_x - 3, knee_y - 1),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_mid"], [
            (base_x - 1, cy + 10), (base_x + 2, cy + 10),
            (knee_x + 2, knee_y - 2), (knee_x, knee_y - 2),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_light"], [
            (base_x, cy + 11), (base_x + 1, cy + 11),
            (knee_x + 1, knee_y - 3), (knee_x, knee_y - 3),
        ])
        # Shin.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_darkest"], [
            (knee_x - 4, knee_y), (knee_x + 4, knee_y),
            (foot_x + 3, foot_y), (foot_x - 3, foot_y),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_dark"], [
            (knee_x - 3, knee_y + 1), (knee_x + 3, knee_y + 1),
            (foot_x + 2, foot_y - 1), (foot_x - 2, foot_y - 1),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 2, knee_y + 2),
            (foot_x + 1, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["pants_light"], [
            (knee_x, knee_y + 3), (knee_x + 1, knee_y + 3),
            (foot_x, foot_y - 3), (foot_x, foot_y - 3),
        ])
        # Foot.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["wrap_darkest"], [
            (foot_x - 5, foot_y - 1), (foot_x + 5, foot_y - 1),
            (foot_x + 5, foot_y + 3), (foot_x - 5, foot_y + 3),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["wrap_dark"], [
            (foot_x - 4, foot_y), (foot_x + 4, foot_y),
            (foot_x + 4, foot_y + 2), (foot_x - 4, foot_y + 2),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["wrap_mid"], [
            (foot_x - 3, foot_y + 1), (foot_x + 3, foot_y + 1),
        ])

    def _draw_pants_sash(surface, cx, cy, facing, phase):
        """Blue sash + gold buckle over pants."""
        sway = math.sin(phase * 0.5) * 1

        # Sash across waist (blue, wrapped).
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["sash_darkest"], [
            (cx - 10, cy + 7), (cx + 10, cy + 7),
            (cx + 11, cy + 12), (cx - 11, cy + 12),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["sash_dark"], [
            (cx - 9, cy + 8), (cx + 9, cy + 8),
            (cx + 10, cy + 11), (cx - 10, cy + 11),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["sash_mid"], [
            (cx - 7, cy + 9), (cx + 7, cy + 9),
            (cx + 8, cy + 10), (cx - 8, cy + 10),
        ])
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["sash_light"],
                         (cx - 5, cy + 9), (cx + 5, cy + 9), 1)

        # Gold buckle with blue gem in center.
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["gold_dark"],
                         (cx - 4, cy + 7, 8, 5))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["gold_mid"],
                         (cx - 3, cy + 8, 6, 3))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["gold_light"],
                         (cx - 2, cy + 8, 4, 1))
        # Blue gem in center.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_kaelthar._alpha(200 * (3 - r) / 3 * pulse)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_light"], alpha),
                                    (cx, cy + 9), r)
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["elec_dark"],
                         (cx - 1, cy + 8, 3, 3))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_mid"],
                         (cx, cy + 9, 2, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                         (cx, cy + 9, 1, 1))

        # Sash flaps hanging down (blue fabric).
        for i, side in enumerate([-1, 0, 1]):
            flap_x = cx + side * 6 + int(sway)
            flap_y_start = cy + 12
            flap_y_end = cy + 22
            flap_w = 3

            _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["sash_darkest"], [
                (flap_x - flap_w, flap_y_start),
                (flap_x + flap_w, flap_y_start),
                (flap_x + flap_w - 1, flap_y_end),
                (flap_x - flap_w + 1, flap_y_end),
            ])
            _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["sash_dark"], [
                (flap_x - flap_w + 1, flap_y_start + 1),
                (flap_x + flap_w - 1, flap_y_start + 1),
                (flap_x + flap_w - 2, flap_y_end - 1),
                (flap_x - flap_w + 2, flap_y_end - 1),
            ])
            _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["sash_mid"], [
                (flap_x, flap_y_start + 2),
                (flap_x, flap_y_end - 2),
            ])
            pygame.draw.rect(surface, _NS_kaelthar.PALETTE["sash_light"],
                             (flap_x, flap_y_start + 3, 1, 3))

    def _draw_muscular_torso(surface, cx, cy, facing, phase, action):
        """Bare muscular torso with tribal tattoo."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape (V-shape, wide shoulders).
        torso_shape = [
            (cx - 11, cy - 10),
            (cx - 13, cy - 5),
            (cx - 11, cy + 3),
            (cx - 8, cy + 8),
            (cx + 8, cy + 8),
            (cx + 11, cy + 3),
            (cx + 13, cy - 5),
            (cx + 11, cy - 10),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_shape])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_darkest"],
                            torso_shape)
        # Muscle base.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_dark"], [
            (cx - 10, cy - 8), (cx - 12, cy),
            (cx - 8, cy + 6), (cx + 8, cy + 6),
            (cx + 12, cy), (cx + 10, cy - 8),
            (cx + 6, cy - 11), (cx - 6, cy - 11),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_mid"], [
            (cx - 8, cy - 6), (cx - 10, cy),
            (cx - 6, cy + 4), (cx + 6, cy + 4),
            (cx + 10, cy), (cx + 8, cy - 6),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        # Chest highlight (pectorals).
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_light"], [
            (cx - 7, cy - 5), (cx - 2, cy - 6),
            (cx - 2, cy - 1), (cx - 6, cy),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_light"], [
            (cx + 2, cy - 6), (cx + 7, cy - 5),
            (cx + 6, cy), (cx + 2, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["skin_shine"],
                         (cx - 4, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["skin_shine"],
                         (cx + 3, cy - 4, 1, 1))

        # Ab muscles.
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["muscle_shadow"],
                         (cx, cy - 4), (cx, cy + 6), 1)
        for dy in (0, 3):
            pygame.draw.line(surface, _NS_kaelthar.PALETTE["muscle_shadow"],
                             (cx - 4, cy + dy), (cx + 4, cy + dy), 1)

        # TRIBAL TATTOO on shoulder/chest (blue).
        # Left shoulder tribal pattern.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_glow = _NS_kaelthar._alpha(180 * pulse)
        # Curved tribal lines.
        for i in range(3):
            arc_y = cy - 6 + i * 2
            pygame.draw.line(surface, _NS_kaelthar.PALETTE["tattoo_dark"],
                             (cx - 9, arc_y), (cx - 5, arc_y + 1), 1)
        # Small tribal dots/symbols.
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["tattoo_mid"],
                         (cx - 8, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["tattoo_mid"],
                         (cx - 7, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["tattoo_glow"],
                         (cx - 8, cy - 8, 1, 1))

        # Right shoulder tribal.
        for i in range(3):
            arc_y = cy - 6 + i * 2
            pygame.draw.line(surface, _NS_kaelthar.PALETTE["tattoo_dark"],
                             (cx + 5, arc_y + 1), (cx + 9, arc_y), 1)
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["tattoo_mid"],
                         (cx + 6, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["tattoo_glow"],
                         (cx + 7, cy - 8, 1, 1))

        # Chest tattoo center (small tribal cross).
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["tattoo_dark"],
                         (cx - 2, cy - 4), (cx + 2, cy - 4), 1)
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["tattoo_dark"],
                         (cx, cy - 5), (cx, cy - 3), 1)

        # Arm bandage wraps on both biceps.
        for side in [-1, 1]:
            bicep_x = cx + side * 11
            for wrap_i in range(2):
                wrap_y = cy - 8 + wrap_i * 3
                pygame.draw.line(surface, _NS_kaelthar.PALETTE["wrap_darkest"],
                                 (bicep_x - 3, wrap_y),
                                 (bicep_x + 3, wrap_y), 2)
                pygame.draw.line(surface, _NS_kaelthar.PALETTE["wrap_dark"],
                                 (bicep_x - 3, wrap_y),
                                 (bicep_x + 3, wrap_y), 1)

    def _draw_head_bandana(surface, cx, cy, facing, phase, action):
        """Face with black hair + blue bandana + gem."""
        # Long black hair FIRST (behind face).
        _NS_kaelthar._draw_long_black_hair(surface, cx, cy, facing, phase)

        # Face.
        face_shape = [
            (cx - 6, cy - 4), (cx - 7, cy),
            (cx - 5, cy + 5), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 5),
            (cx + 7, cy), (cx + 6, cy - 4),
            (cx + 3, cy - 7), (cx - 3, cy - 7),
        ]
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in face_shape])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_darkest"], face_shape)
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_dark"], [
            (cx - 5, cy - 3), (cx - 6, cy),
            (cx - 4, cy + 4), (cx + 4, cy + 4),
            (cx + 6, cy), (cx + 5, cy - 3),
            (cx + 2, cy - 6), (cx - 2, cy - 6),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_mid"], [
            (cx - 4, cy - 2), (cx - 5, cy),
            (cx - 3, cy + 3), (cx + 3, cy + 3),
            (cx + 5, cy), (cx + 4, cy - 2),
            (cx + 2, cy - 5), (cx - 2, cy - 5),
        ])
        # Cheek highlight.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["skin_light"], [
            (cx - 2, cy - 1), (cx + 2, cy - 1),
            (cx + 2, cy + 2), (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["skin_shine"],
                         (cx, cy, 1, 1))

        # BLUE BANDANA.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["bandana_darkest"], [
            (cx - 7, cy - 6), (cx + 7, cy - 6),
            (cx + 8, cy - 3), (cx - 8, cy - 3),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["bandana_dark"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5),
            (cx + 7, cy - 4), (cx - 7, cy - 4),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["bandana_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 6, cy - 4), (cx - 6, cy - 4),
        ])
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["bandana_light"],
                         (cx - 4, cy - 5), (cx + 4, cy - 5), 1)
        # DIAMOND GEM in center of bandana (khas Badang).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_kaelthar._alpha(200 * (3 - r) / 3 * pulse)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_light"], alpha),
                                    (cx, cy - 4), r)
        # Diamond shape.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["elec_dark"], [
            (cx, cy - 6), (cx + 2, cy - 4),
            (cx, cy - 2), (cx - 2, cy - 4),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_dark"], [
            (cx, cy - 5), (cx + 1, cy - 4),
            (cx, cy - 3), (cx - 1, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                         (cx, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["white"],
                         (cx, cy - 4, 1, 1))

        # Bandana tail behind.
        tail_sway = math.sin(phase * 0.7) * 2
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["bandana_darkest"], [
            (cx - 7 * facing, cy - 3),
            (cx - 12 * facing + int(tail_sway), cy - 1),
            (cx - 13 * facing + int(tail_sway), cy + 3),
            (cx - 8 * facing, cy - 1),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["bandana_dark"], [
            (cx - 8 * facing, cy - 2),
            (cx - 11 * facing + int(tail_sway), cy),
            (cx - 12 * facing + int(tail_sway), cy + 2),
        ])
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["bandana_light"],
                         (cx - 8 * facing, cy - 2),
                         (cx - 10 * facing + int(tail_sway), cy + 1), 1)

        # Fierce eye.
        ex = cx + 2 * facing
        ey = cy
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["eye_dark"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["eye_white"],
                         (ex, ey, 2, 1))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["eye_blue"],
                         (ex + 1, ey, 1, 1))
        # Second eye partial.
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["eye_dark"],
                         (cx - 3 * facing, ey, 2, 2))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["eye_white"],
                         (cx - 3 * facing + 1, ey, 1, 1))

        # Angry eyebrows.
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["hair_darkest"],
                         (cx - 4, cy - 2), (cx + 5, cy - 2), 1)

        # Grim mouth.
        pygame.draw.line(surface, _NS_kaelthar.PALETTE["muscle_deep"],
                         (cx - 2, cy + 4), (cx + 2, cy + 4), 1)

    def _draw_long_black_hair(surface, cx, cy, facing, phase):
        """Long black flowing hair behind head."""
        sway = math.sin(phase * 0.5) * 3

        # Long hair strands trailing back.
        for i, (offset_y, length, curve) in enumerate([
            (-2, 24, 4), (2, 28, 5), (6, 24, 4), (10, 18, 3),
        ]):
            base_x = cx - facing * 5
            base_y = cy + offset_y

            wave = math.sin(phase * 0.7 + i) * 2
            mid_x = base_x - facing * int(curve + wave)
            mid_y = base_y + length // 2
            end_x = base_x - facing * (length + int(sway))
            end_y = base_y + length

            # Shadow.
            _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                                  (base_x + 1, base_y + 1),
                                  (mid_x + 1, mid_y + 1), 3)
            # Main strand.
            _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["hair_darkest"],
                                  (base_x, base_y), (mid_x, mid_y), 3)
            _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["hair_darkest"],
                                  (mid_x, mid_y), (end_x, end_y), 2)
            _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["hair_dark"],
                                  (base_x, base_y), (mid_x, mid_y), 2)
            _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["hair_dark"],
                                  (mid_x, mid_y), (end_x, end_y), 1)
            _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["hair_mid"],
                                  (base_x, base_y - 1),
                                  (mid_x, mid_y - 1), 1)
            if i == 1:
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["hair_light"],
                                      (base_x, base_y), (end_x, end_y), 1)

        # Top of head bangs (black).
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["hair_darkest"], [
            (cx - 6, cy - 7), (cx + 6, cy - 7),
            (cx + 6, cy - 5), (cx - 6, cy - 5),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["hair_dark"], [
            (cx - 5, cy - 7), (cx + 5, cy - 7),
            (cx + 5, cy - 6), (cx - 5, cy - 6),
        ])

    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        """Back arm with lightning fist gauntlet."""
        shoulder_x = cx - facing * 10
        shoulder_y = cy - 8

        # Arm angle based on action.
        if action == "attack":
            # Rear arm cocked back.
            arm_swing = math.sin(progress * math.pi) * -8
            elbow_x = shoulder_x - facing * 6
            elbow_y = shoulder_y + 4 + int(arm_swing * 0.3)
            hand_x = shoulder_x - facing * 8
            hand_y = shoulder_y + 10 + int(arm_swing * 0.4)
        elif action == "slam":
            # Both arms raised.
            if progress < 0.55:
                elbow_x = shoulder_x - facing * 4
                elbow_y = shoulder_y - 6
                hand_x = shoulder_x - facing * 6
                hand_y = shoulder_y - 14
            else:
                # Slam down.
                elbow_x = shoulder_x - facing * 2
                elbow_y = shoulder_y + 8
                hand_x = shoulder_x + facing * 2
                hand_y = shoulder_y + 18
        elif action == "leap":
            # Both fists up.
            elbow_x = shoulder_x - facing * 3
            elbow_y = shoulder_y - 8
            hand_x = shoulder_x - facing * 5
            hand_y = shoulder_y - 18
        elif action == "charge":
            # Charging fist forward (back arm behind).
            elbow_x = shoulder_x - facing * 5
            elbow_y = shoulder_y - 2
            hand_x = shoulder_x - facing * 9
            hand_y = shoulder_y - 4
        else:
            sway = math.sin(phase * 0.6) * 1
            elbow_x = shoulder_x - facing * 5
            elbow_y = shoulder_y + 6 + int(sway)
            hand_x = shoulder_x - facing * 8
            hand_y = shoulder_y + 12

        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 6)
        # Upper arm (bicep - skin).
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_light"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Forearm.
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Wrist wrap (dark bandage).
        for i in range(2):
            wrap_x = int(elbow_x + (hand_x - elbow_x) * (0.6 + i * 0.15))
            wrap_y = int(elbow_y + (hand_y - elbow_y) * (0.6 + i * 0.15))
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["wrap_darkest"],
                                    (wrap_x, wrap_y), 3)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["wrap_dark"],
                                    (wrap_x, wrap_y), 2)

        # LIGHTNING FIST GAUNTLET at hand.
        _NS_kaelthar._draw_lightning_fist(surface, hand_x, hand_y, facing, phase)

    def _draw_front_arm(surface, cx, cy, facing, phase, action, progress):
        """Front arm - primary attack arm."""
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 8

        if action == "attack":
            # Punch forward.
            angle = progress * math.pi * 0.8 - math.pi / 4
            elbow_x = shoulder_x + facing * int(math.cos(angle) * 6)
            elbow_y = shoulder_y + int(math.sin(angle) * 6) + 2
            hand_x = shoulder_x + facing * int(math.cos(angle) * 14)
            hand_y = shoulder_y + int(math.sin(angle) * 14) + 3
        elif action == "charge":
            # Big fist extending forward with charge effect.
            elbow_x = shoulder_x + facing * 8
            elbow_y = shoulder_y - 2
            hand_x = shoulder_x + facing * 18
            hand_y = shoulder_y - 4
        elif action == "dash":
            # Straight forward arm.
            elbow_x = shoulder_x + facing * 8
            elbow_y = shoulder_y
            hand_x = shoulder_x + facing * 18
            hand_y = shoulder_y
        elif action == "slam":
            if progress < 0.55:
                # Raise fist high.
                elbow_x = shoulder_x + facing * 3
                elbow_y = shoulder_y - 6
                hand_x = shoulder_x + facing * 5
                hand_y = shoulder_y - 16
            else:
                # Slam down.
                elbow_x = shoulder_x + facing * 4
                elbow_y = shoulder_y + 8
                hand_x = shoulder_x + facing * 6
                hand_y = shoulder_y + 20
        elif action == "leap":
            # Both fists up.
            elbow_x = shoulder_x + facing * 3
            elbow_y = shoulder_y - 8
            hand_x = shoulder_x + facing * 5
            hand_y = shoulder_y - 18
        else:
            # Idle - fist ready at side.
            sway = math.sin(phase * 0.6) * 1
            elbow_x = shoulder_x + facing * 6
            elbow_y = shoulder_y + 6 + int(sway)
            hand_x = shoulder_x + facing * 10
            hand_y = shoulder_y + 12 + int(sway)

        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 7)
        # Upper arm (bigger bicep).
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 3)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_light"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Forearm.
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Wrist wraps.
        for i in range(2):
            wrap_x = int(elbow_x + (hand_x - elbow_x) * (0.55 + i * 0.15))
            wrap_y = int(elbow_y + (hand_y - elbow_y) * (0.55 + i * 0.15))
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["wrap_darkest"],
                                    (wrap_x, wrap_y), 4)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["wrap_dark"],
                                    (wrap_x, wrap_y), 3)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["wrap_mid"],
                                    (wrap_x, wrap_y - 1), 1)

        # BIG LIGHTNING FIST (main).
        _NS_kaelthar._draw_lightning_fist(surface, hand_x, hand_y, facing, phase,
                                            size=1.15)

    def _draw_lightning_fist(surface, hx, hy, facing, phase, size=1.0):
        """Blue lightning fist gauntlet - SIGNATURE feature!"""
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        r_base = int(6 * size)

        # Big glow aura.
        for r in range(r_base + 8, 1, -1):
            alpha = _NS_kaelthar._alpha(140 * (r_base + 8 - r) / (r_base + 8) * pulse)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_dark"], alpha),
                                    (hx, hy), r)
        for r in range(r_base + 4, 1, -1):
            alpha = _NS_kaelthar._alpha(200 * (r_base + 4 - r) / (r_base + 4) * pulse)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                    (hx, hy), r)

        # Fist shape (fist gauntlet - cluster of knuckles).
        # Shadow.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["shadow_deep"], [
            (hx + 1 - r_base, hy + 1 - r_base + 1),
            (hx + 1 + r_base, hy + 1 - r_base + 1),
            (hx + 1 + r_base + 1, hy + 1 + r_base - 1),
            (hx + 1 - r_base - 1, hy + 1 + r_base - 1),
        ])
        # Deep base.
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["elec_darkest"], [
            (hx - r_base, hy - r_base + 1),
            (hx + r_base, hy - r_base + 1),
            (hx + r_base + 1, hy + r_base - 1),
            (hx - r_base - 1, hy + r_base - 1),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["elec_dark"], [
            (hx - r_base + 1, hy - r_base + 2),
            (hx + r_base - 1, hy - r_base + 2),
            (hx + r_base, hy + r_base - 2),
            (hx - r_base, hy + r_base - 2),
        ])
        _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_dark"], [
            (hx - r_base + 2, hy - r_base + 3),
            (hx + r_base - 2, hy - r_base + 3),
            (hx + r_base - 1, hy + r_base - 3),
            (hx - r_base + 1, hy + r_base - 3),
        ])

        # Knuckles (4 small bumps on top).
        for k_i in range(4):
            k_x = hx + int((k_i - 1.5) * (r_base / 2))
            k_y = hy - r_base + 2
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_mid"],
                                    (k_x, k_y), max(1, int(r_base / 3)))
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_light"],
                                    (k_x, k_y - 1), max(1, int(r_base / 4)))
            pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                             (k_x, k_y - 1, 1, 1))

        # Central bright core.
        _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_light"],
                                (hx, hy), max(1, int(r_base / 2)))
        _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                (hx, hy), max(1, int(r_base / 3)))
        pygame.draw.rect(surface, _NS_kaelthar.PALETTE["white"],
                         (hx, hy, 1, 1))

        # Lightning arcs randomly popping out.
        for i in range(4):
            arc_angle = phase * 2 + i * math.pi / 2
            arc_len = int(r_base * 1.5)
            arc_x = hx + int(math.cos(arc_angle) * arc_len)
            arc_y = hy + int(math.sin(arc_angle) * arc_len)
            # Jagged lightning line.
            mid_x = (hx + arc_x) // 2 + int(math.sin(phase * 4 + i) * 2)
            mid_y = (hy + arc_y) // 2 + int(math.cos(phase * 4 + i) * 2)
            alpha = _NS_kaelthar._alpha(220 * pulse)
            _NS_kaelthar._aaline(surface,
                                  (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                                  (hx, hy), (mid_x, mid_y), 1)
            _NS_kaelthar._aaline(surface,
                                  (*_NS_kaelthar.PALETTE["storm_shine"], alpha),
                                  (mid_x, mid_y), (arc_x, arc_y), 1)
            pygame.draw.rect(surface,
                             (*_NS_kaelthar.PALETTE["storm_white"], alpha),
                             (arc_x, arc_y, 1, 1))

    def _draw_punch_swing(surface, cx, cy, facing, progress):
        """Lightning fist trail from punch."""
        if progress < 0.3 or progress > 0.8:
            return
        t = (progress - 0.3) / 0.5

        # Trail from side to forward.
        for i in range(6):
            trail_t = t - i * 0.06
            if trail_t < 0:
                continue
            # Fist position moves from cocked back to forward.
            fist_x = cx + facing * int(-4 + trail_t * 24)
            fist_y = cy - 5 + int(math.sin(trail_t * math.pi) * -3)
            alpha = _NS_kaelthar._alpha(240 - i * 35)

            for r in range(6, 1, -1):
                a = _NS_kaelthar._alpha(alpha * (6 - r) / 6)
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_dark"], a),
                                        (fist_x, fist_y), r)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                    (fist_x, fist_y), 3)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_light"], alpha),
                                    (fist_x, fist_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                             (fist_x, fist_y, 1, 1))

    # ============================================================
    # LIGHTNING PARTICLES (float underneath)
    # ============================================================
    def _draw_lightning_particles(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        # Blue lightning pool below.
        pool = pygame.Surface((100, 26), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(20, 2, -2):
            alpha = _NS_kaelthar._alpha((20 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_kaelthar.PALETTE["storm_darkest"], alpha),
                                    (50 - r, 13 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(11, 1, -1):
            alpha = _NS_kaelthar._alpha((11 - r) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                    (50 - r, 13 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 50, cy - 5))

        # Rising lightning sparks.
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 20 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 8 - int(t * 24)
            alpha = _NS_kaelthar._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_kaelthar.PALETTE["storm_shine"], alpha),
                             (sx, sy - 2, 1, 1))

        # Small lightning bolts around.
        for i in range(3):
            bolt_angle = phase * 1.2 + i * math.pi * 2 / 3
            bolt_len = 8
            bx1 = cx + int(math.cos(bolt_angle) * 18)
            by1 = cy + 5 + int(math.sin(bolt_angle) * 6)
            bx2 = bx1 + int(math.cos(bolt_angle) * bolt_len)
            by2 = by1 + int(math.sin(bolt_angle) * bolt_len)
            mid_x = (bx1 + bx2) // 2 + int(math.sin(phase * 3 + i) * 2)
            mid_y = (by1 + by2) // 2
            alpha = _NS_kaelthar._alpha(180 * pulse * strength)
            _NS_kaelthar._aaline(surface,
                                  (*_NS_kaelthar.PALETTE["storm_light"], alpha),
                                  (bx1, by1), (mid_x, mid_y), 1)
            _NS_kaelthar._aaline(surface,
                                  (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                                  (mid_x, mid_y), (bx2, by2), 1)

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 28), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            alpha = max(0, (14 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 14 - r,
                                 100 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (5, 15, 40, 170), (5, 8, 110, 12))
        pygame.draw.ellipse(shadow, (30, 90, 200, 100), (12, 10, 96, 8))
        surface.blit(shadow, (x - 60, y - 14))

    def _draw_storm_aura(surface, x, y, phase):
        """Blue electric storm aura."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for r in range(95, 5, -5):
            alpha = _NS_kaelthar._alpha((95 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_kaelthar._aacircle(aura,
                                        (*_NS_kaelthar.PALETTE["storm_darkest"],
                                         alpha), (110, 100), r)
        for r in range(60, 5, -4):
            alpha = _NS_kaelthar._alpha((60 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_kaelthar._aacircle(aura,
                                        (*_NS_kaelthar.PALETTE["storm_dark"],
                                         alpha), (110, 100), r)
        surface.blit(aura, (x - 110, y - 100))

        # Lightning sparks orbiting.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 50 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_kaelthar.PALETTE["rune_dark"], 200),
                            (5, 16, 150, 26), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_kaelthar.PALETTE["storm_darkest"], 220),
                            (14, 18, 132, 22), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_kaelthar.PALETTE["storm_dark"], 230),
                            (25, 20, 110, 18), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 43)
            y1 = 29 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 29 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_kaelthar.PALETTE["storm_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kaelthar.PALETTE["storm_hot"],
                                 _NS_kaelthar._alpha(150 * pulse)),
                                (15, 12, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q: CHARGING FIST - dash with fist glow
    # ============================================================
    def _draw_charging_fist_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge trail behind.
            for i in range(6):
                tx = x - facing * (i * 10)
                ty = y - 5 + int(math.sin(phase + i) * 3)
                alpha = _NS_kaelthar._alpha(230 - i * 35)
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                        (tx, ty), 5)
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_light"], alpha),
                                        (tx, ty), 3)
        else:
            # BIG glowing fist projectile in front of boss.
            t = (progress - 0.3) / 0.7
            fist_x = x + facing * (25 + int(t * 15))
            fist_y = y - 5

            # Massive fist energy.
            for r in range(18, 3, -2):
                alpha = _NS_kaelthar._alpha(80 * (18 - r) / 18)
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_dark"], alpha),
                                        (fist_x, fist_y), r)
            for r in range(12, 2, -1):
                alpha = _NS_kaelthar._alpha(200 * (12 - r) / 12)
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                        (fist_x, fist_y), r)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_light"],
                                    (fist_x, fist_y), 8)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_hot"],
                                    (fist_x, fist_y), 5)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                    (fist_x, fist_y), 3)
            pygame.draw.rect(surface, _NS_kaelthar.PALETTE["white"],
                             (fist_x, fist_y, 1, 1))

            # Lightning bolts around fist.
            for i in range(6):
                bolt_angle = phase * 4 + i * math.pi / 3
                bolt_len = 12
                b1_x = fist_x + int(math.cos(bolt_angle) * 8)
                b1_y = fist_y + int(math.sin(bolt_angle) * 8)
                b2_x = fist_x + int(math.cos(bolt_angle) * (8 + bolt_len))
                b2_y = fist_y + int(math.sin(bolt_angle) * (8 + bolt_len))
                mid_x = (b1_x + b2_x) // 2 + int(math.sin(phase * 5 + i) * 3)
                mid_y = (b1_y + b2_y) // 2 + int(math.cos(phase * 5 + i) * 3)
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["storm_hot"],
                                      (b1_x, b1_y), (mid_x, mid_y), 2)
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                      (mid_x, mid_y), (b2_x, b2_y), 1)
                pygame.draw.rect(surface, _NS_kaelthar.PALETTE["white"],
                                 (b2_x, b2_y, 1, 1))

    # ============================================================
    # SKILL W: QUAKE PUNCH - ground shockwave crystals
    # ============================================================
    def _draw_quake_ground(surface, boss, x, y, timer, phase):
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.55:
            return  # Wait for punch animation.

        t = (progress - 0.55) / 0.45
        r = int(60 * t)
        alpha = _NS_kaelthar._alpha(230 * (1 - t * 0.5))

        pygame.draw.ellipse(surface,
                            (*_NS_kaelthar.PALETTE["storm_darkest"], alpha),
                            (x - r, y + 45 - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_kaelthar.PALETTE["storm_dark"], alpha),
                            (x - r + 3, y + 45 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface,
                            (*_NS_kaelthar.PALETTE["storm_mid"], alpha // 2),
                            (x - r + 8, y + 45 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8))

    def _draw_quake_fg(surface, boss, x, y, timer, phase):
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.55:
            # Charging fist raised up.
            t = progress / 0.55
            fist_y = y - 25 + int(t * 5)
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kaelthar._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                        (x, fist_y), r)
            _NS_kaelthar._aacircle(surface, _NS_kaelthar.PALETTE["storm_light"],
                                    (x, fist_y), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                             (x, fist_y, 1, 1))
        else:
            # PUNCH HIT GROUND - crystal spikes erupt.
            t = (progress - 0.55) / 0.45

            # Central impact burst.
            burst_r = int(15 + t * 25)
            burst_alpha = _NS_kaelthar._alpha(255 * (1 - t))
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_shine"],
                                     burst_alpha), (x, y + 40), burst_r // 3)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_hot"],
                                     burst_alpha), (x, y + 40), burst_r // 2)

            # Crystal spike columns around impact.
            num_spikes = 10
            for i in range(num_spikes):
                spike_angle = i * math.pi * 2 / num_spikes
                spread = 20 + (i % 3) * 15
                spike_x = x + int(math.cos(spike_angle) * spread)
                spike_base_y = y + 45 + int(math.sin(spike_angle) * spread * 0.4)

                spike_progress = min(1.0, max(0.0, t * 2.5 - i * 0.05))
                if spike_progress < 0.05:
                    continue

                max_h = 30 + (i % 3) * 8
                spike_h = int(spike_progress * max_h)
                if spike_progress > 0.7:
                    fade = 1 - (spike_progress - 0.7) / 0.3
                    spike_h = int(spike_h * (0.6 + fade * 0.4))

                if spike_h < 3:
                    continue

                spike_tip_y = spike_base_y - spike_h
                spike_width = 3

                # Shadow.
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["shadow_deep"], [
                    (spike_x + 1, spike_tip_y + 1),
                    (spike_x - spike_width + 1, spike_base_y + 1),
                    (spike_x + spike_width + 1, spike_base_y + 1),
                ])
                # Spike body.
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_darkest"], [
                    (spike_x, spike_tip_y),
                    (spike_x - spike_width, spike_base_y),
                    (spike_x + spike_width, spike_base_y),
                ])
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_dark"], [
                    (spike_x, spike_tip_y),
                    (spike_x - spike_width + 1, spike_base_y),
                    (spike_x + spike_width - 1, spike_base_y),
                ])
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_mid"], [
                    (spike_x, spike_tip_y),
                    (spike_x - 1, spike_base_y),
                    (spike_x + 1, spike_base_y),
                ])
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["storm_light"],
                                      (spike_x, spike_tip_y),
                                      (spike_x, spike_base_y), 1)
                pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                 (spike_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kaelthar.PALETTE["white"],
                                 (spike_x, spike_tip_y, 1, 1))
                for gr in range(2, 0, -1):
                    alpha = _NS_kaelthar._alpha(120 * (2 - gr) / 2)
                    _NS_kaelthar._aacircle(surface,
                                            (*_NS_kaelthar.PALETTE["storm_light"],
                                             alpha),
                                            (spike_x, spike_tip_y), gr)

    # ============================================================
    # SKILL E: FIST CRACK - forward dash straight
    # ============================================================
    def _draw_fistcrack_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Straight forward energy line.
        if progress < 0.3:
            # Prep.
            hx = x + facing * 20
            hy = y - 5
            t = progress / 0.3
            cr = int(3 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_kaelthar._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                        (hx, hy), r)
        else:
            # Beam of energy in front (straight line thrust).
            t = (progress - 0.3) / 0.7
            beam_length = int(80 * t)
            start_x = x + facing * 20
            start_y = y - 5

            # Multi-layer beam.
            intensity = math.sin(t * math.pi) * 0.5 + 0.5
            for layer_i, (width, color) in enumerate([
                (10, _NS_kaelthar.PALETTE["storm_darkest"]),
                (7, _NS_kaelthar.PALETTE["storm_dark"]),
                (5, _NS_kaelthar.PALETTE["storm_mid"]),
                (3, _NS_kaelthar.PALETTE["storm_light"]),
                (1, _NS_kaelthar.PALETTE["storm_shine"]),
            ]):
                alpha = _NS_kaelthar._alpha(230 * intensity)
                beam_left = min(start_x, start_x + facing * beam_length)
                pygame.draw.rect(surface, (*color, alpha),
                                 (beam_left, start_y - width // 2,
                                  beam_length, width))

            # Zigzag lightning inside beam.
            for i in range(6):
                seg_start_x = start_x + facing * int(i * beam_length / 6)
                seg_end_x = start_x + facing * int((i + 1) * beam_length / 6)
                mid_x = (seg_start_x + seg_end_x) // 2
                mid_y = start_y + int(math.sin(phase * 5 + i) * 4)
                alpha = _NS_kaelthar._alpha(255 * intensity)
                _NS_kaelthar._aaline(surface,
                                      (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                                      (seg_start_x, start_y), (mid_x, mid_y), 2)
                _NS_kaelthar._aaline(surface,
                                      (*_NS_kaelthar.PALETTE["storm_shine"], alpha),
                                      (mid_x, mid_y), (seg_end_x, start_y), 1)

            # End impact.
            end_x = start_x + facing * beam_length
            end_r = int(8 + t * 8)
            end_alpha = _NS_kaelthar._alpha(240 * intensity)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_dark"],
                                     end_alpha), (end_x, start_y), end_r + 2, 2)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_mid"],
                                     end_alpha), (end_x, start_y), end_r, 2)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_light"],
                                     end_alpha), (end_x, start_y),
                                    max(1, end_r - 3))
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_shine"],
                                     end_alpha), (end_x, start_y),
                                    max(1, end_r // 2))
            # Radial burst at end.
            for i in range(8):
                a = i * math.pi / 4
                ex = end_x + int(math.cos(a) * end_r)
                ey = start_y + int(math.sin(a) * end_r)
                _NS_kaelthar._aaline(surface,
                                      (*_NS_kaelthar.PALETTE["storm_light"],
                                       end_alpha),
                                      (end_x, start_y), (ex, ey), 1)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthar.PALETTE["storm_shine"],
                                  end_alpha), (ex, ey, 1, 1))

    # ============================================================
    # SKILL R: FIST BREAK - leap and slam
    # ============================================================
    def _draw_fistbreak_ground(surface, boss, x, y, timer, pulse):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.7:
            t = (progress - 0.7) / 0.3
            r = int(30 + t * 50)
            alpha = _NS_kaelthar._alpha(240 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_kaelthar.PALETTE["storm_darkest"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_kaelthar.PALETTE["storm_dark"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))

    def _draw_fistbreak_fg(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Rising energy under boss during leap.
            for i in range(10):
                t = (phase * 1.5 + i * 0.1) % 1.0
                sx = x - 25 + i * 5 + int(math.sin(phase + i) * 3)
                sy = y + 40 - int(t * 40)
                alpha = _NS_kaelthar._alpha(230 * (1 - t))
                _NS_kaelthar._aacircle(surface,
                                        (*_NS_kaelthar.PALETTE["storm_mid"], alpha),
                                        (sx, sy), 3)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                                 (sx, sy, 1, 1))
        elif progress < 0.7:
            # Hanging in air (glowing fists).
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                sx = x + int(math.cos(angle) * 22)
                sy = y - 60 + int(math.sin(angle) * 10)
                _NS_kaelthar._aacircle(surface,
                                        _NS_kaelthar.PALETTE["storm_mid"],
                                        (sx, sy), 3)
                pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                 (sx, sy, 1, 1))
            # Lightning between fists.
            fist_y = y - 60
            for bolt_i in range(3):
                b_start_x = x - 10
                b_end_x = x + 10
                mid_x = x + int(math.sin(phase * 5 + bolt_i) * 3)
                mid_y = fist_y + int(math.cos(phase * 5 + bolt_i) * 3)
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["storm_hot"],
                                      (b_start_x, fist_y), (mid_x, mid_y), 2)
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                      (mid_x, mid_y), (b_end_x, fist_y), 1)
        else:
            # SLAM - huge crystal spikes erupt from ground.
            t = (progress - 0.7) / 0.3

            # Central impact burst.
            burst_r = int(20 + t * 30)
            burst_alpha = _NS_kaelthar._alpha(255 * (1 - t))
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_shine"],
                                     burst_alpha), (x, y + 30), burst_r // 3)
            _NS_kaelthar._aacircle(surface,
                                    (*_NS_kaelthar.PALETTE["storm_hot"],
                                     burst_alpha), (x, y + 30), burst_r // 2)

            # HUGE crystal spike columns.
            num_spikes = 14
            for i in range(num_spikes):
                spread_dist = 20 + (i % 4) * 15
                angle = i * math.pi * 2 / num_spikes
                spike_x = x + int(math.cos(angle) * spread_dist)
                spike_base_y = y + 40 + int(math.sin(angle) * spread_dist * 0.4)

                spike_h = int((1 - abs(t - 0.5) * 2) * 40)
                if spike_h < 3:
                    continue

                spike_tip_y = spike_base_y - spike_h
                spike_width = 4

                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["shadow_deep"], [
                    (spike_x + 1, spike_tip_y + 1),
                    (spike_x - spike_width + 1, spike_base_y + 1),
                    (spike_x + spike_width + 1, spike_base_y + 1),
                ])
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_darkest"], [
                    (spike_x, spike_tip_y),
                    (spike_x - spike_width, spike_base_y),
                    (spike_x + spike_width, spike_base_y),
                ])
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_dark"], [
                    (spike_x, spike_tip_y),
                    (spike_x - spike_width + 1, spike_base_y),
                    (spike_x + spike_width - 1, spike_base_y),
                ])
                _NS_kaelthar._poly(surface, _NS_kaelthar.PALETTE["storm_mid"], [
                    (spike_x, spike_tip_y),
                    (spike_x - 1, spike_base_y),
                    (spike_x + 1, spike_base_y),
                ])
                _NS_kaelthar._aaline(surface, _NS_kaelthar.PALETTE["storm_light"],
                                      (spike_x, spike_tip_y),
                                      (spike_x - spike_width, spike_base_y), 1)
                pygame.draw.rect(surface, _NS_kaelthar.PALETTE["storm_shine"],
                                 (spike_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kaelthar.PALETTE["white"],
                                 (spike_x, spike_tip_y, 1, 1))

            # Lightning bolts radiating out.
            for i in range(8):
                bolt_angle = i * math.pi / 4
                bolt_len = int(50 * t)
                b1_x = x
                b1_y = y + 30
                b2_x = x + int(math.cos(bolt_angle) * bolt_len)
                b2_y = y + 30 + int(math.sin(bolt_angle) * bolt_len * 0.7)
                mid_x = (b1_x + b2_x) // 2 + int(math.sin(phase * 3 + i) * 3)
                mid_y = (b1_y + b2_y) // 2 + int(math.cos(phase * 3 + i) * 3)
                alpha = _NS_kaelthar._alpha(240 * (1 - t))
                _NS_kaelthar._aaline(surface,
                                      (*_NS_kaelthar.PALETTE["storm_hot"], alpha),
                                      (b1_x, b1_y), (mid_x, mid_y), 2)
                _NS_kaelthar._aaline(surface,
                                      (*_NS_kaelthar.PALETTE["storm_shine"], alpha),
                                      (mid_x, mid_y), (b2_x, b2_y), 1)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthar.PALETTE["white"], alpha),
                                 (b2_x, b2_y, 1, 1))

            # Debris rocks flying.
            for i in range(12):
                debris_t = (phase * 1.5 + i * 0.15) % 1.0
                if debris_t > t:
                    continue
                angle = i * math.pi / 6
                dist = int(debris_t * 40)
                dx = x + int(math.cos(angle) * dist)
                dy = y + 30 - int(debris_t * 20) + int(debris_t ** 2 * 15)
                pygame.draw.rect(surface,
                                 _NS_kaelthar.PALETTE["wrap_dark"],
                                 (dx, dy, 2, 2))
                pygame.draw.rect(surface,
                                 _NS_kaelthar.PALETTE["wrap_mid"],
                                 (dx, dy, 1, 1))


# ====================================================================
# morkhaera.py
# ====================================================================

"""
MOR'KHAERA - The Blood-Feather Witch
Mini boss dark mage dengan spirit bird companion.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_morkhaera:
    """Namespace mor'khaera - blood witch mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale gothic)
        "skin_darkest": (100, 80, 90),
        "skin_dark": (165, 140, 150),
        "skin_mid": (215, 190, 195),
        "skin_light": (240, 220, 220),
        "skin_shine": (252, 240, 240),

        # Silver hair
        "hair_darkest": (60, 55, 75),
        "hair_dark": (120, 115, 140),
        "hair_mid": (175, 175, 195),
        "hair_light": (220, 220, 235),
        "hair_shine": (245, 245, 250),

        # Dark gothic dress (purple-black)
        "dress_darkest": (10, 5, 20),
        "dress_dark": (30, 15, 50),
        "dress_mid": (60, 30, 90),
        "dress_light": (100, 55, 140),
        "dress_shine": (150, 90, 195),

        # Crimson feathers (main theme)
        "feather_darkest": (30, 5, 15),
        "feather_dark": (80, 15, 30),
        "feather_mid": (160, 30, 55),
        "feather_light": (220, 60, 90),
        "feather_hot": (255, 100, 130),
        "feather_shine": (255, 180, 200),
        "feather_bright": (255, 220, 230),

        # Blood red (skill theme - vibrant)
        "blood_darkest": (35, 0, 10),
        "blood_dark": (95, 10, 30),
        "blood_mid": (200, 25, 60),
        "blood_light": (255, 70, 110),
        "blood_hot": (255, 130, 160),
        "blood_shine": (255, 200, 215),

        # Gold trim (dress accents, headpiece)
        "gold_darkest": (55, 40, 10),
        "gold_dark": (115, 85, 25),
        "gold_mid": (200, 155, 50),
        "gold_light": (245, 215, 100),
        "gold_shine": (255, 245, 180),

        # Blindfold (dark with gold trim)
        "blindfold_dark": (15, 5, 20),
        "blindfold_mid": (40, 20, 55),

        # Eye glow (hidden but red)
        "eye_red": (255, 50, 80),
        "eye_shine": (255, 200, 210),

        # Bird spirit (dark red raven)
        "bird_darkest": (15, 3, 10),
        "bird_dark": (45, 10, 20),
        "bird_mid": (95, 15, 35),
        "bird_light": (170, 40, 60),
        "bird_glow": (240, 80, 110),

        # Ground/rune
        "rune_dark": (40, 10, 30),
        "rune_mid": (150, 30, 60),
        "rune_light": (255, 100, 130),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morkhaera._clamp(color)
        if _NS_morkhaera.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morkhaera._clamp(color)
        if _NS_morkhaera.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue
        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_morkhaera._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_morkhaera._clamp(color), valid_points)

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
        return int(x + 240 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morkhaera(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_morkhaera._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_mk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # Ambient behind.
        _NS_morkhaera._draw_blood_aura(surface, x, y, pulse)
        _NS_morkhaera._draw_ground_ring(surface, x, y + 55, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_morkhaera._draw_energy_impact_ground(surface, boss, x, y,
                                                       skill_timer, pulse)
        elif active_skill == "w":
            _NS_morkhaera._draw_air_strike_ground(surface, boss, x, y,
                                                    skill_timer, pulse)
        elif active_skill == "r":
            _NS_morkhaera._draw_ethereal_ground(surface, boss, x, y,
                                                  skill_timer, pulse)

        # Body OR bird transformation.
        if active_skill == "r":
            _NS_morkhaera._draw_bird_form(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_morkhaera._draw_body_attack(surface, boss, x, y)
        elif active_skill:
            _NS_morkhaera._draw_body_cast(surface, boss, x, y, pulse, active_skill)
        else:
            _NS_morkhaera._draw_body_idle(surface, boss, x, y)

        # Spirit bird companion (always present except when transformed).
        if active_skill != "r":
            _NS_morkhaera._draw_spirit_bird(surface, boss, x, y, pulse,
                                              active_skill == "w")

        # Foreground skill FX.
        if active_skill == "q":
            _NS_morkhaera._draw_spirit_burst_fg(surface, boss, x, y,
                                                  skill_timer, pulse)
        elif active_skill == "w":
            _NS_morkhaera._draw_air_strike_fg(surface, boss, x, y,
                                                skill_timer, pulse)
        elif active_skill == "e":
            _NS_morkhaera._draw_energy_impact_fg(surface, boss, x, y,
                                                   skill_timer, pulse)
        elif active_skill == "r":
            _NS_morkhaera._draw_ethereal_fg(surface, boss, x, y,
                                              skill_timer, pulse)

        # Basic attack projectile (crimson feather).
        if attacking:
            _NS_morkhaera._draw_feather_projectile(surface, boss, x, y)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mk_previous_timer", 0))
        active = bool(getattr(boss, "_mk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mk_attack_active = True
            boss._mk_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._mk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._mk_attack_frame = int(getattr(boss, "_mk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mk_attack_active = False
            boss._mk_attack_frame = 0
            active = False

        boss._mk_previous_timer = timer
        boss._mk_attack_progress = (
            min(1.0, getattr(boss, "_mk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_morkhaera._draw_shadow(surface, x, y + 55)
        _NS_morkhaera._draw_float_feathers(surface, x, y + 30, boss.pulse)
        _NS_morkhaera._draw_witch_body(surface, x, y + bob, boss.direction,
                                         boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mk_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_mk_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_morkhaera._draw_shadow(surface, x, y + 55)
        _NS_morkhaera._draw_float_feathers(surface, x, y + 30, boss.pulse,
                                             intense=True)
        _NS_morkhaera._draw_witch_body(surface, x, y + bob, facing,
                                         boss.pulse, "attack",
                                         getattr(boss, "_mk_attack_progress", 0))

    def _draw_body_cast(surface, boss, x, y, pulse, skill):
        bob = int(math.sin(pulse * 0.5) * 4)
        lift = int(math.sin(pulse * 1.5) * 2) + 3
        _NS_morkhaera._draw_shadow(surface, x, y + 55)
        _NS_morkhaera._draw_float_feathers(surface, x, y + 30, pulse,
                                             intense=True)
        _NS_morkhaera._draw_witch_body(surface, x, y + bob - lift,
                                         boss.direction, pulse, "cast",
                                         skill=skill)

    # ============================================================
    # WITCH BODY (floating with dark gothic dress)
    # ============================================================
    def _draw_witch_body(surface, cx, cy, facing, phase, action,
                          progress=0, skill=None):
        """Full witch: dress trail, torso, arms, blindfolded head, staff."""
        # Order: back wing feathers, dress trail, back arm,
        # torso, head+blindfold, front arm+staff
        _NS_morkhaera._draw_wing_feathers(surface, cx, cy, facing, phase)
        _NS_morkhaera._draw_dress_trail(surface, cx, cy, facing, phase)
        _NS_morkhaera._draw_back_arm(surface, cx, cy, facing, phase, action,
                                       progress)
        _NS_morkhaera._draw_witch_torso(surface, cx, cy, facing, phase, action)
        _NS_morkhaera._draw_headpiece_head(surface, cx, cy - 20, facing, phase, action)
        _NS_morkhaera._draw_staff_arm(surface, cx, cy, facing, phase, action,
                                        progress)

    def _draw_wing_feathers(surface, cx, cy, facing, phase):
        """Feather wings/cape behind body (dark crimson wings)."""
        beat = math.sin(phase * 0.6) * 2

        for side in [-1, 1]:
            # Base wing structure.
            base_x = cx + side * 8
            base_y = cy - 4

            # Multiple feather layers (3-4 large feathers per side).
            for i, (angle_offset, length, thickness) in enumerate([
                (math.pi * 0.55, 18, 3),
                (math.pi * 0.72, 22, 3),
                (math.pi * 0.9, 20, 3),
                (math.pi * 1.05, 16, 2),
            ]):
                # Wing spreads out and back.
                angle = angle_offset * side - math.radians(beat)
                tip_x = base_x + int(math.cos(angle) * length) * (-side if side > 0 else -1)
                # Simpler: wings go back and down.
                tip_x = base_x - side * int(math.cos(angle_offset - math.pi/2) * length)
                tip_y = base_y + int(math.sin(angle_offset - math.pi/2) * length) - int(beat)

                # Feather shape (elongated leaf).
                perp_x = -math.sin(math.atan2(tip_y - base_y, tip_x - base_x))
                perp_y = math.cos(math.atan2(tip_y - base_y, tip_x - base_x))
                w_a = (base_x + int(perp_x * thickness),
                       base_y + int(perp_y * thickness))
                w_b = (base_x - int(perp_x * thickness),
                       base_y - int(perp_y * thickness))

                # Shadow.
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (w_a[0] + 1, w_a[1] + 1),
                    (w_b[0] + 1, w_b[1] + 1),
                ])
                # Feather layers.
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                                     [(tip_x, tip_y), w_a, w_b])
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_darkest"], [
                    (tip_x, tip_y),
                    (int(w_a[0] * 0.8 + base_x * 0.2),
                     int(w_a[1] * 0.8 + base_y * 0.2)),
                    (int(w_b[0] * 0.8 + base_x * 0.2),
                     int(w_b[1] * 0.8 + base_y * 0.2)),
                ])
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + w_a[0]) / 2), int((tip_y + w_a[1]) / 2)),
                    (int((tip_x + w_b[0]) / 2), int((tip_y + w_b[1]) / 2)),
                ])
                # Central spine.
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["feather_mid"],
                                       (base_x, base_y), (tip_x, tip_y), 1)
                # Bright red tip.
                _NS_morkhaera._aacircle(surface,
                                         _NS_morkhaera.PALETTE["blood_dark"],
                                         (tip_x, tip_y), 2)
                pygame.draw.rect(surface,
                                 _NS_morkhaera.PALETTE["blood_light"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface,
                                 _NS_morkhaera.PALETTE["blood_hot"],
                                 (tip_x, tip_y, 1, 1))

    def _draw_dress_trail(surface, cx, cy, facing, phase):
        """Long dark gothic dress trailing below."""
        sway = math.sin(phase * 0.4) * 3
        sway2 = math.sin(phase * 0.6 + 1) * 2

        # Dress silhouette (long, flowing dark purple).
        dress_shape = [
            (cx - 13, cy + 8),
            (cx - 20, cy + 20),
            (cx - 28 + int(sway), cy + 32),
            (cx - 30 + int(sway), cy + 46),
            (cx - 24 + int(sway2), cy + 58),
            (cx - 10 + int(sway2), cy + 64),
            (cx, cy + 66),
            (cx + 10 + int(sway2), cy + 64),
            (cx + 24 + int(sway2), cy + 58),
            (cx + 30 + int(sway), cy + 46),
            (cx + 28 + int(sway), cy + 32),
            (cx + 20, cy + 20),
            (cx + 13, cy + 8),
        ]
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                             [(px + 3, py + 3) for px, py in dress_shape])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_darkest"],
                             dress_shape)
        # Inner dark shading.
        inner = [
            (cx - 11, cy + 10),
            (cx - 18, cy + 22),
            (cx - 25 + int(sway), cy + 34),
            (cx - 26 + int(sway), cy + 46),
            (cx - 22 + int(sway2), cy + 55),
            (cx - 8 + int(sway2), cy + 62),
            (cx, cy + 63),
            (cx + 8 + int(sway2), cy + 62),
            (cx + 22 + int(sway2), cy + 55),
            (cx + 26 + int(sway), cy + 46),
            (cx + 25 + int(sway), cy + 34),
            (cx + 18, cy + 22),
            (cx + 11, cy + 10),
        ]
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_dark"], inner)
        # Mid tone.
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_mid"], [
            (cx - 9, cy + 12),
            (cx - 15, cy + 24),
            (cx - 20 + int(sway), cy + 36),
            (cx - 20 + int(sway2), cy + 52),
            (cx, cy + 58),
            (cx + 20 + int(sway2), cy + 52),
            (cx + 20 + int(sway), cy + 36),
            (cx + 15, cy + 24),
            (cx + 9, cy + 12),
        ])
        # Central light streak (fabric fold showing leg opening).
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_light"], [
            (cx - 3, cy + 14),
            (cx - 5, cy + 26),
            (cx - 4 + int(sway2), cy + 42),
            (cx - 2 + int(sway2), cy + 55),
            (cx + 2 + int(sway2), cy + 55),
            (cx + 4 + int(sway2), cy + 42),
            (cx + 5, cy + 26),
            (cx + 3, cy + 14),
        ])
        # Bright fabric hint.
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_shine"],
                               (cx, cy + 14), (cx + int(sway2), cy + 50), 1)

        # Red feather details on dress edge.
        for i in range(6):
            fx = cx - 22 + i * 9
            fy = cy + 30 + i * 4 + int(sway)
            side = -1 if i < 3 else 1
            fx = fx + side * 5
            # Small feather sticking out.
            _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_dark"], [
                (fx, fy - 3), (fx + side * 2, fy),
                (fx, fy + 3),
            ])
            _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_mid"], [
                (fx, fy - 2), (fx + side * 1, fy),
                (fx, fy + 2),
            ])
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_light"],
                             (fx, fy, 1, 1))

        # Gold trim at hem.
        for i in range(5):
            hem_x = cx - 20 + i * 10
            hem_y = cy + 60 + int(sway2 * 0.5)
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["gold_dark"],
                             (hem_x, hem_y, 3, 1))
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["gold_mid"],
                             (hem_x, hem_y, 2, 1))
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["gold_shine"],
                             (hem_x + 1, hem_y, 1, 1))

        # Red feather wisps rising from dress hem.
        for i in range(6):
            t = (phase * 0.6 + i * 0.15) % 1.0
            wx = cx - 18 + i * 7 + int(math.sin(phase + i) * 2)
            wy = cy + 60 - int(t * 15)
            alpha = _NS_morkhaera._alpha(200 * (1 - t))
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["feather_dark"], alpha),
                                     (wx, wy), 2)
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                             (wx, wy - 1, 1, 1))

    def _draw_witch_torso(surface, cx, cy, facing, phase, action):
        """Fitted corset torso with gold accents + cleavage V."""
        breath = math.sin(phase * 0.7) * 1

        # Corset silhouette.
        torso_shape = [
            (cx - 9, cy - 7),
            (cx - 11, cy - 2),
            (cx - 9, cy + 5),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 9, cy + 5),
            (cx + 11, cy - 2),
            (cx + 9, cy - 7),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ]
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_shape])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_darkest"],
                             torso_shape)
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_dark"], [
            (cx - 8, cy - 6), (cx - 10, cy - 2),
            (cx - 8, cy + 4), (cx - 5, cy + 8),
            (cx + 5, cy + 8), (cx + 8, cy + 4),
            (cx + 10, cy - 2), (cx + 8, cy - 6),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_mid"], [
            (cx - 7, cy - 4), (cx - 9, cy),
            (cx - 5, cy + 6), (cx + 5, cy + 6),
            (cx + 9, cy), (cx + 7, cy - 4),
            (cx + 3, cy - 8), (cx - 3, cy - 8),
        ])

        # Cleavage V (pale skin showing).
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["skin_dark"], [
            (cx - 3, cy - 8), (cx + 3, cy - 8),
            (cx, cy - 2),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["skin_mid"], [
            (cx - 2, cy - 7), (cx + 2, cy - 7),
            (cx, cy - 3),
        ])

        # GOLD CORSET LACES (X-pattern down center).
        for lace_i in range(4):
            lace_y = cy - 5 + lace_i * 3
            pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_dark"],
                             (cx - 4, lace_y), (cx + 4, lace_y + 2), 1)
            pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_dark"],
                             (cx + 4, lace_y), (cx - 4, lace_y + 2), 1)
            pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_mid"],
                             (cx - 4, lace_y), (cx + 4, lace_y + 2), 1)

        # Gold trim on top edge (bust line).
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_dark"],
                         (cx - 7, cy - 6), (cx - 3, cy - 8), 1)
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_dark"],
                         (cx + 3, cy - 8), (cx + 7, cy - 6), 1)
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_light"],
                         (cx - 6, cy - 6), (cx - 3, cy - 7), 1)
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_light"],
                         (cx + 3, cy - 7), (cx + 6, cy - 6), 1)

        # Central red gem on chest.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_morkhaera._alpha(200 * (4 - r) / 4 * pulse)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                     (cx, cy - 3), r)
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_darkest"],
                         (cx - 1, cy - 4, 3, 3))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_mid"],
                         (cx, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                         (cx, cy - 3, 1, 1))

        # Feather shoulder pauldrons (crimson).
        for side in [-1, 1]:
            pauldron_x = cx + side * 11
            pauldron_y = cy - 8
            # Small feathers cluster at shoulder.
            for feather_i in range(3):
                fx = pauldron_x + side * feather_i
                fy = pauldron_y + feather_i
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_dark"], [
                    (fx, fy - 3), (fx + side * 2, fy),
                    (fx, fy + 3),
                ])
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_mid"], [
                    (fx, fy - 2), (fx + side * 1, fy),
                    (fx, fy + 2),
                ])
                pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_light"],
                                 (fx, fy, 1, 1))

    def _draw_headpiece_head(surface, cx, cy, facing, phase, action):
        """Head with silver hair, blindfold, gold headpiece with horns."""
        head_cx = cx
        head_cy = cy

        # Flowing silver hair (drawn first, behind).
        _NS_morkhaera._draw_silver_hair(surface, head_cx, head_cy, facing, phase)

        # Face.
        face_shape = [
            (head_cx - 5, head_cy - 3), (head_cx - 6, head_cy + 1),
            (head_cx - 4, head_cy + 5), (head_cx - 1, head_cy + 7),
            (head_cx + 3, head_cy + 7), (head_cx + 5, head_cy + 5),
            (head_cx + 6, head_cy + 1), (head_cx + 5, head_cy - 3),
            (head_cx + 2, head_cy - 6), (head_cx - 2, head_cy - 6),
        ]
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in face_shape])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["skin_darkest"],
                             face_shape)
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["skin_dark"], [
            (head_cx - 4, head_cy - 2), (head_cx - 5, head_cy + 1),
            (head_cx - 3, head_cy + 4), (head_cx + 3, head_cy + 4),
            (head_cx + 5, head_cy + 1), (head_cx + 4, head_cy - 2),
            (head_cx + 2, head_cy - 5), (head_cx - 2, head_cy - 5),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["skin_mid"], [
            (head_cx - 3, head_cy - 1), (head_cx - 4, head_cy + 1),
            (head_cx - 2, head_cy + 3), (head_cx + 2, head_cy + 3),
            (head_cx + 4, head_cy + 1), (head_cx + 3, head_cy - 1),
            (head_cx + 1, head_cy - 4), (head_cx - 1, head_cy - 4),
        ])
        # Cheek highlight.
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["skin_light"],
                         (head_cx - 1, head_cy + 2, 3, 2))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["skin_shine"],
                         (head_cx, head_cy + 2, 1, 1))

        # BLINDFOLD (khas Pharsa - covers eyes) - gold with dark center.
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"], [
            (head_cx - 6, head_cy - 2), (head_cx + 6, head_cy - 2),
            (head_cx + 6, head_cy + 2), (head_cx - 6, head_cy + 2),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["blindfold_dark"], [
            (head_cx - 5, head_cy - 2), (head_cx + 5, head_cy - 2),
            (head_cx + 5, head_cy + 1), (head_cx - 5, head_cy + 1),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["blindfold_mid"], [
            (head_cx - 4, head_cy - 1), (head_cx + 4, head_cy - 1),
            (head_cx + 4, head_cy), (head_cx - 4, head_cy),
        ])
        # Gold trim on blindfold (top + bottom).
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_dark"],
                         (head_cx - 6, head_cy - 2),
                         (head_cx + 6, head_cy - 2), 1)
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_mid"],
                         (head_cx - 5, head_cy - 2),
                         (head_cx + 5, head_cy - 2), 1)
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_dark"],
                         (head_cx - 6, head_cy + 2),
                         (head_cx + 6, head_cy + 2), 1)
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_mid"],
                         (head_cx - 5, head_cy + 1),
                         (head_cx + 5, head_cy + 1), 1)
        # Red eye glow beneath blindfold (menakutkan).
        pulse = math.sin(phase * 2.5) * 0.5 + 0.5
        for ey_side in [-1, 1]:
            eye_x = head_cx + ey_side * 2
            eye_y = head_cy
            alpha = _NS_morkhaera._alpha(200 * pulse)
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["eye_red"], alpha),
                             (eye_x, eye_y, 1, 1))
            for r in range(2, 0, -1):
                a = _NS_morkhaera._alpha(120 * (2 - r) / 2 * pulse)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_light"], a),
                                         (eye_x, eye_y), r)

        # Gold gem in center of blindfold (small red).
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["gold_dark"],
                         (head_cx - 1, head_cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_light"],
                         (head_cx, head_cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                         (head_cx, head_cy - 1, 1, 1))

        # Small elegant mouth (dark red).
        pygame.draw.line(surface, (120, 30, 50),
                         (head_cx - 1, head_cy + 5),
                         (head_cx + 1, head_cy + 5), 1)

        # GOLD HEADPIECE with curved horns (like Pharsa).
        _NS_morkhaera._draw_gold_headpiece(surface, head_cx, head_cy, facing, phase)

    def _draw_silver_hair(surface, cx, cy, facing, phase):
        """Long silver hair flowing behind."""
        sway = math.sin(phase * 0.5) * 3

        # Multiple strands both sides.
        for side in [-1, 1]:
            for i, (offset_x, offset_y_start, length, curve) in enumerate([
                (0, -2, 30, 4), (1, 2, 34, 5), (2, 6, 28, 3),
                (3, 10, 24, 3),
            ]):
                base_x = cx + side * (5 + offset_x)
                base_y = cy + offset_y_start

                wave = math.sin(phase * 0.6 + i + side) * 2
                mid_x = base_x + side * int(curve + wave)
                mid_y = base_y + length // 2
                end_x = base_x + side * int(sway + wave)
                end_y = base_y + length

                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                                       (base_x + 1, base_y + 1),
                                       (mid_x + 1, mid_y + 1), 3)
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["hair_darkest"],
                                       (base_x, base_y), (mid_x, mid_y), 3)
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["hair_darkest"],
                                       (mid_x, mid_y), (end_x, end_y), 2)
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["hair_dark"],
                                       (base_x, base_y), (mid_x, mid_y), 2)
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["hair_dark"],
                                       (mid_x, mid_y), (end_x, end_y), 1)
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["hair_mid"],
                                       (base_x, base_y - 1),
                                       (mid_x, mid_y - 1), 1)
                if i == 1:
                    _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["hair_light"],
                                           (base_x, base_y), (end_x, end_y), 1)
                    pygame.draw.rect(surface, _NS_morkhaera.PALETTE["hair_shine"],
                                     (mid_x, mid_y - 1, 1, 1))

        # Top bangs (short over blindfold).
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["hair_darkest"], [
            (cx - 5, cy - 6), (cx + 5, cy - 6),
            (cx + 6, cy - 4), (cx - 6, cy - 4),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["hair_dark"], [
            (cx - 4, cy - 6), (cx + 4, cy - 6),
            (cx + 5, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["hair_mid"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 3, cy - 5), (cx - 3, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["hair_light"],
                         (cx - 1, cy - 6, 2, 1))

    def _draw_gold_headpiece(surface, cx, cy, facing, phase):
        """Gold headpiece with curved horns/wings on head."""
        # Base band.
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["gold_dark"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5),
            (cx + 6, cy - 4), (cx - 6, cy - 4),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["gold_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 5, cy - 4), (cx - 5, cy - 4),
        ])
        pygame.draw.line(surface, _NS_morkhaera.PALETTE["gold_light"],
                         (cx - 4, cy - 5), (cx + 4, cy - 5), 1)

        # CURVED HORNS on top (2 big horns going out and back like Pharsa).
        for side in [-1, 1]:
            # Horn base near top of head.
            base_x = cx + side * 3
            base_y = cy - 5

            # Horn curves outward and back.
            # Use bezier-like curve.
            for seg in range(6):
                t = seg / 5.0
                # Curve x: goes out then back.
                curve_x = base_x + side * int(t * 8 - t * t * 2)
                curve_y = base_y - int(t * 10) + int(t * t * 3)
                if seg == 0:
                    prev = (base_x, base_y)
                else:
                    _NS_morkhaera._aaline(surface,
                                           _NS_morkhaera.PALETTE["shadow_deep"],
                                           (prev[0] + 1, prev[1] + 1),
                                           (curve_x + 1, curve_y + 1),
                                           max(1, 4 - seg))
                    _NS_morkhaera._aaline(surface,
                                           _NS_morkhaera.PALETTE["gold_darkest"],
                                           prev, (curve_x, curve_y),
                                           max(1, 4 - seg))
                    _NS_morkhaera._aaline(surface,
                                           _NS_morkhaera.PALETTE["gold_dark"],
                                           prev, (curve_x, curve_y),
                                           max(1, 3 - seg))
                    _NS_morkhaera._aaline(surface,
                                           _NS_morkhaera.PALETTE["gold_mid"],
                                           prev, (curve_x, curve_y),
                                           max(1, 2 - seg // 2))
                    _NS_morkhaera._aaline(surface,
                                           _NS_morkhaera.PALETTE["gold_light"],
                                           (prev[0], prev[1] - 1),
                                           (curve_x, curve_y - 1), 1)
                    if seg == 5:
                        # Tip glow.
                        pulse = math.sin(phase * 2) * 0.3 + 0.7
                        for gr in range(3, 0, -1):
                            alpha = _NS_morkhaera._alpha(150 * pulse
                                                          * (3 - gr) / 3)
                            _NS_morkhaera._aacircle(surface,
                                                     (*_NS_morkhaera.PALETTE["blood_light"],
                                                      alpha),
                                                     (curve_x, curve_y), gr)
                        pygame.draw.rect(surface,
                                         _NS_morkhaera.PALETTE["blood_shine"],
                                         (curve_x, curve_y, 1, 1))
                        pygame.draw.rect(surface,
                                         _NS_morkhaera.PALETTE["white"],
                                         (curve_x, curve_y, 1, 1))
                prev = (curve_x, curve_y)

        # Central gem in headpiece.
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_dark"],
                         (cx - 1, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_mid"],
                         (cx, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                         (cx, cy - 5, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        """Back arm - gesturing."""
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 4

        if action == "cast":
            elbow_x = shoulder_x - facing * 6
            elbow_y = shoulder_y - 2
            hand_x = shoulder_x - facing * 12
            hand_y = shoulder_y - 8
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x - facing * 5
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x - facing * 8
            hand_y = shoulder_y + 10

        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                               (shoulder_x + 2, shoulder_y + 2),
                               (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm (dark sleeve).
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_darkest"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_dark"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_mid"],
                               (shoulder_x, shoulder_y - 1),
                               (elbow_x, elbow_y - 1), 1)
        # Flared sleeve (with feather trim).
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_darkest"], [
            (elbow_x - 2, elbow_y - 2), (elbow_x + 2, elbow_y + 2),
            (hand_x + 4, hand_y + 3), (hand_x - 4, hand_y - 3),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["dress_dark"], [
            (elbow_x - 1, elbow_y - 1), (elbow_x + 1, elbow_y + 1),
            (hand_x + 3, hand_y + 2), (hand_x - 3, hand_y - 2),
        ])
        # Red feather trim on sleeve.
        for i in range(3):
            fx = hand_x - facing * (i - 1)
            fy = hand_y + 3 + i
            _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_dark"], [
                (fx, fy), (fx - facing * 1, fy + 2),
                (fx + facing * 2, fy + 2),
            ])
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_light"],
                             (fx, fy + 1, 1, 1))
        # Hand.
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 3)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["skin_mid"],
                                 (hand_x, hand_y - 1), 2)

        # Red magic sparks at fingertips (casting).
        if action == "cast":
            for finger_i in range(3):
                fx = hand_x - facing * 2 + finger_i - 1
                fy = hand_y - 3
                pulse = math.sin(phase * 3 + finger_i) * 0.3 + 0.7
                alpha = _NS_morkhaera._alpha(220 * pulse)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_light"],
                                          alpha), (fx, fy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                                 (fx, fy, 1, 1))

    def _draw_staff_arm(surface, cx, cy, facing, phase, action, progress):
        """Front arm holding dark staff with red crystal."""
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 4

        if action == "attack":
            elbow_x = shoulder_x + facing * 5
            elbow_y = shoulder_y + 2
            hand_x = shoulder_x + facing * 12
            hand_y = shoulder_y - 4
            staff_angle = -math.pi / 4 if facing > 0 else math.pi + math.pi / 4
        elif action == "cast":
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y - 6
            hand_x = shoulder_x + facing * 8
            hand_y = shoulder_y - 14
            staff_angle = -math.pi / 2 + 0.15
        else:
            sway = math.sin(phase * 0.6) * 1
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x + facing * 8
            hand_y = shoulder_y + 2 + int(sway)
            staff_angle = -math.pi / 2 + 0.1

        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                               (shoulder_x + 2, shoulder_y + 2),
                               (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm.
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_darkest"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_dark"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_mid"],
                               (shoulder_x, shoulder_y - 1),
                               (elbow_x, elbow_y - 1), 1)
        # Forearm.
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_darkest"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_dark"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Gold bracer.
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["gold_dark"],
                                 (hand_x, hand_y), 3)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["gold_mid"],
                                 (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["gold_shine"],
                         (hand_x, hand_y - 1, 1, 1))
        # Hand.
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 2)

        # Draw staff.
        _NS_morkhaera._draw_dark_staff(surface, hand_x, hand_y, staff_angle,
                                         facing, phase)

    def _draw_dark_staff(surface, hx, hy, angle, facing, phase):
        """Long dark staff with big crimson crystal orb on top."""
        length = 42
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        top_x = hx + int(dx * length)
        top_y = hy + int(dy * length)
        bot_x = hx - int(dx * 12)
        bot_y = hy - int(dy * 12)

        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                               (bot_x + 2, bot_y + 2), (top_x + 2, top_y + 2), 4)
        # Staff shaft (dark).
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_darkest"],
                               (bot_x, bot_y), (top_x, top_y), 4)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_dark"],
                               (bot_x, bot_y), (top_x, top_y), 3)
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["dress_mid"],
                               (bot_x, bot_y), (top_x, top_y), 1)
        # Gold accents.
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["gold_dark"],
                               (bot_x, bot_y - 1), (top_x, top_y - 1), 1)

        # Decorative rings.
        for t_ring in (0.25, 0.5, 0.75):
            rx = int(bot_x + (top_x - bot_x) * t_ring)
            ry = int(bot_y + (top_y - bot_y) * t_ring)
            perp = angle + math.pi / 2
            r_a = (rx + int(math.cos(perp) * 3), ry + int(math.sin(perp) * 3))
            r_b = (rx - int(math.cos(perp) * 3), ry - int(math.sin(perp) * 3))
            _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["gold_dark"],
                                   r_a, r_b, 2)
            _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["gold_light"],
                                   r_a, r_b, 1)

        # BIG CRIMSON CRYSTAL ORB on top.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        orb_x = top_x + int(dx * 4)
        orb_y = top_y + int(dy * 4)
        orb_r = 6

        # Gold prongs/holder around orb.
        perp = angle + math.pi / 2
        for prong_side in [-1, 1]:
            prong_base_x = top_x + int(math.cos(perp) * 4 * prong_side)
            prong_base_y = top_y + int(math.sin(perp) * 4 * prong_side)
            prong_tip_x = orb_x + int(math.cos(perp) * 5 * prong_side)
            prong_tip_y = orb_y + int(math.sin(perp) * 5 * prong_side)
            _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["gold_dark"],
                                   (prong_base_x, prong_base_y),
                                   (prong_tip_x, prong_tip_y), 2)
            _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["gold_light"],
                                   (prong_base_x, prong_base_y),
                                   (prong_tip_x, prong_tip_y), 1)

        # Orb glow.
        for r in range(orb_r + 6, 1, -1):
            alpha = _NS_morkhaera._alpha(140 * (orb_r + 6 - r)
                                          / (orb_r + 6) * pulse)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                     (orb_x, orb_y), r)
        for r in range(orb_r + 3, 1, -1):
            alpha = _NS_morkhaera._alpha(200 * (orb_r + 3 - r)
                                          / (orb_r + 3) * pulse)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                                     (orb_x, orb_y), r)

        # Orb body.
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_darkest"],
                                 (orb_x, orb_y), orb_r)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_dark"],
                                 (orb_x, orb_y), orb_r - 1)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_mid"],
                                 (orb_x, orb_y), orb_r - 3)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_light"],
                                 (orb_x, orb_y), max(1, orb_r - 5))
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_shine"],
                                 (orb_x - 1, orb_y - 1), 1)
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["white"],
                         (orb_x - 1, orb_y - 1, 1, 1))

    # ============================================================
    # SPIRIT BIRD (companion raven)
    # ============================================================
    def _draw_spirit_bird(surface, boss, x, y, phase, casting_w=False):
        """Crimson spirit raven that circles above/around boss."""
        # Bird orbits around boss's head area.
        orbit_angle = phase * 0.4
        orbit_r = 45 if not casting_w else 20

        bx = x + int(math.cos(orbit_angle) * orbit_r) * boss.direction
        by = y - 30 + int(math.sin(orbit_angle) * 15)

        # Bird faces movement direction.
        bird_facing = boss.direction
        if math.sin(orbit_angle) < 0:
            bird_facing = -boss.direction

        _NS_morkhaera._draw_raven(surface, bx, by, bird_facing, phase,
                                    size=1.0)

    def _draw_raven(surface, cx, cy, facing, phase, size=1.0):
        """Draw a crimson raven bird."""
        beat = math.sin(phase * 2) * 3

        # Body (compact oval).
        body_shape = [
            (cx - int(6 * size), cy),
            (cx - int(8 * size), cy - int(2 * size)),
            (cx - int(6 * size), cy - int(5 * size)),
            (cx + int(2 * size), cy - int(6 * size)),
            (cx + int(6 * size), cy - int(4 * size)),
            (cx + int(8 * size), cy - int(1 * size)),
            (cx + int(6 * size), cy + int(2 * size)),
            (cx, cy + int(3 * size)),
            (cx - int(5 * size), cy + int(2 * size)),
        ]
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in body_shape])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_darkest"],
                             body_shape)
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_dark"], [
            (cx - int(5 * size), cy - int(1 * size)),
            (cx - int(6 * size), cy - int(3 * size)),
            (cx - int(4 * size), cy - int(5 * size)),
            (cx + int(2 * size), cy - int(5 * size)),
            (cx + int(6 * size), cy - int(3 * size)),
            (cx + int(7 * size), cy - int(1 * size)),
            (cx + int(5 * size), cy + int(1 * size)),
            (cx - int(4 * size), cy + int(1 * size)),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_mid"], [
            (cx - int(3 * size), cy - int(2 * size)),
            (cx - int(4 * size), cy - int(4 * size)),
            (cx + int(2 * size), cy - int(5 * size)),
            (cx + int(5 * size), cy - int(2 * size)),
            (cx + int(3 * size), cy),
            (cx - int(2 * size), cy),
        ])

        # Head (front).
        head_x = cx + int(facing * 8 * size)
        head_y = cy - int(4 * size)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["bird_darkest"],
                                 (head_x, head_y), int(4 * size))
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["bird_dark"],
                                 (head_x, head_y), int(3 * size))
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["bird_mid"],
                                 (head_x, head_y - int(size)),
                                 max(1, int(2 * size)))

        # Beak.
        beak_tip_x = head_x + int(facing * 6 * size)
        beak_tip_y = head_y + int(size)
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["gold_dark"], [
            (head_x + int(facing * 3 * size), head_y - int(size)),
            (beak_tip_x, beak_tip_y),
            (head_x + int(facing * 3 * size), head_y + int(2 * size)),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["gold_mid"], [
            (head_x + int(facing * 3 * size), head_y),
            (beak_tip_x, beak_tip_y),
            (head_x + int(facing * 3 * size), head_y + int(size)),
        ])

        # RED GLOWING EYE.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        eye_x = head_x + int(facing * 2 * size)
        eye_y = head_y - int(size)
        for r in range(3, 0, -1):
            alpha = _NS_morkhaera._alpha(180 * (3 - r) / 3 * pulse)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                     (eye_x, eye_y), r)
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["eye_red"],
                         (eye_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["eye_shine"],
                         (eye_x, eye_y, 1, 1))

        # WINGS spreading out.
        for side, wing_facing in [(1, 1), (-1, -1)]:
            wing_base_x = cx + int(side * 2 * size)
            wing_base_y = cy - int(4 * size)

            # 4 primary feathers.
            for feather_i, (angle_deg, length) in enumerate([
                (110, 14), (135, 16), (160, 14), (180, 10),
            ]):
                fa = math.radians(angle_deg) * side - math.radians(beat)
                tip_x = wing_base_x + int(math.cos(fa) * length * size)
                tip_y = wing_base_y + int(math.sin(fa) * length * size)

                # Feather shape.
                perp_a = fa + math.pi / 2
                w_a = (wing_base_x + int(math.cos(perp_a) * 2),
                       wing_base_y + int(math.sin(perp_a) * 2))
                w_b = (wing_base_x - int(math.cos(perp_a) * 2),
                       wing_base_y - int(math.sin(perp_a) * 2))

                _NS_morkhaera._poly(surface,
                                     _NS_morkhaera.PALETTE["bird_darkest"],
                                     [(tip_x, tip_y), w_a, w_b])
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + w_a[0]) / 2), int((tip_y + w_a[1]) / 2)),
                    (int((tip_x + w_b[0]) / 2), int((tip_y + w_b[1]) / 2)),
                ])
                _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["bird_mid"],
                                       (wing_base_x, wing_base_y), (tip_x, tip_y), 1)
                # Bright red tip.
                pygame.draw.rect(surface,
                                 _NS_morkhaera.PALETTE["blood_light"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface,
                                 _NS_morkhaera.PALETTE["blood_shine"],
                                 (tip_x, tip_y, 1, 1))

        # Tail feathers.
        tail_x = cx - int(facing * 8 * size)
        tail_y = cy - int(1 * size)
        for i, ta in enumerate((-0.3, 0, 0.3)):
            tip_x = tail_x - int(facing * 8 * size)
            tip_y = tail_y + int(ta * 6 * size)
            _NS_morkhaera._aaline(surface,
                                   _NS_morkhaera.PALETTE["bird_dark"],
                                   (tail_x, tail_y), (tip_x, tip_y), 2)
            _NS_morkhaera._aaline(surface,
                                   _NS_morkhaera.PALETTE["bird_mid"],
                                   (tail_x, tail_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface,
                             _NS_morkhaera.PALETTE["blood_light"],
                             (tip_x, tip_y, 1, 1))

        # Aura around bird (crimson glow).
        for r in range(int(15 * size), 3, -2):
            alpha = _NS_morkhaera._alpha(60 * (15 * size - r) / (15 * size))
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                     (cx, cy - 2), r)

    # ============================================================
    # BASIC ATTACK CRIMSON FEATHER PROJECTILE
    # ============================================================
    def _draw_feather_projectile(surface, boss, x, y):
        """Crimson feather projectile as basic attack."""
        progress = getattr(boss, "_mk_attack_progress", 0)
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_morkhaera._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 20

        t = (progress - 0.5) / 0.5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (red feathers).
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_morkhaera._alpha(220 - i * 25)
            size = max(1, 5 - i)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                     (px, py), size + 1)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                                     (px, py), size)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                     (px, py), max(1, size - 2))

        # Feather shape at head.
        angle = math.atan2(ty - start_y, tx - start_x)
        perp = angle + math.pi / 2
        tip_x = bx + int(math.cos(angle) * 8)
        tip_y = by + int(math.sin(angle) * 8)
        back_x = bx - int(math.cos(angle) * 6)
        back_y = by - int(math.sin(angle) * 6)
        w_a = (bx + int(math.cos(perp) * 3), by + int(math.sin(perp) * 3))
        w_b = (bx - int(math.cos(perp) * 3), by - int(math.sin(perp) * 3))

        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1), (w_a[0] + 1, w_a[1] + 1),
            (back_x + 1, back_y + 1), (w_b[0] + 1, w_b[1] + 1),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_darkest"], [
            (tip_x, tip_y), w_a, (back_x, back_y), w_b,
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_dark"], [
            (tip_x, tip_y),
            (int((tip_x + w_a[0]) / 2), int((tip_y + w_a[1]) / 2)),
            (back_x, back_y),
            (int((tip_x + w_b[0]) / 2), int((tip_y + w_b[1]) / 2)),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_mid"], [
            (tip_x, tip_y), (bx, by), (back_x, back_y),
        ])
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["blood_light"],
                               (tip_x, tip_y), (back_x, back_y), 1)
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

        # Glow.
        for r in range(6, 1, -1):
            alpha = _NS_morkhaera._alpha(100 * (6 - r) / 6)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                     (bx, by), r)

        # Impact.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            r = int(6 + st * 12)
            alpha = _NS_morkhaera._alpha(230 * (1 - st))
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                     (tx, ty), r + 1, 2)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                     (tx, ty), r, 1)

    # ============================================================
    # FLOAT FEATHERS
    # ============================================================
    def _draw_float_feathers(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        # Red pool below.
        pool = pygame.Surface((110, 28), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for r in range(22, 2, -2):
            alpha = _NS_morkhaera._alpha((22 - r) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_morkhaera.PALETTE["blood_darkest"],
                                     alpha),
                                    (55 - r, 14 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(13, 1, -1):
            alpha = _NS_morkhaera._alpha((13 - r) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                                    (55 - r, 14 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 55, cy - 5))

        # Falling red feathers.
        for i in range(10):
            t = (phase * 0.4 + i * 0.11) % 1.0
            sx = cx - 25 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 10 - int(t * 28)
            alpha = _NS_morkhaera._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Tiny feather shape.
            _NS_morkhaera._poly(surface, (*_NS_morkhaera.PALETTE["feather_dark"], alpha), [
                (sx, sy - 2), (sx + 1, sy), (sx, sy + 1), (sx - 1, sy),
            ])
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                             (sx, sy - 2, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 32), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            alpha = max(0, (14 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 15 - r,
                                 120 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (25, 5, 15, 170), (5, 10, 130, 14))
        pygame.draw.ellipse(shadow, (100, 15, 40, 100), (12, 12, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_blood_aura(surface, x, y, phase):
        """Crimson blood aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 220), pygame.SRCALPHA)
        for r in range(105, 5, -5):
            alpha = _NS_morkhaera._alpha((105 - r) * 1.1 * pulse)
            if alpha > 0:
                _NS_morkhaera._aacircle(aura,
                                         (*_NS_morkhaera.PALETTE["blood_darkest"],
                                          alpha), (120, 110), r)
        for r in range(65, 5, -4):
            alpha = _NS_morkhaera._alpha((65 - r) * 1.3 * pulse)
            if alpha > 0:
                _NS_morkhaera._aacircle(aura,
                                         (*_NS_morkhaera.PALETTE["blood_dark"],
                                          alpha), (120, 110), r)
        for r in range(40, 5, -3):
            alpha = _NS_morkhaera._alpha((40 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_morkhaera._aacircle(aura,
                                         (*_NS_morkhaera.PALETTE["blood_mid"],
                                          alpha // 2), (120, 110), r)
        surface.blit(aura, (x - 120, y - 110))

        # Feather particles orbiting.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 50 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            # Tiny feather.
            _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["feather_dark"], [
                (sx, sy - 2), (sx + 1, sy), (sx, sy + 1), (sx - 1, sy),
            ])
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_light"],
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_morkhaera.PALETTE["rune_dark"], 200),
                            (5, 16, 160, 26), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_morkhaera.PALETTE["blood_darkest"], 220),
                            (14, 18, 142, 22), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_morkhaera.PALETTE["blood_dark"], 230),
                            (25, 20, 120, 18), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 45)
            y1 = 29 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 29 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_morkhaera.PALETTE["blood_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_morkhaera.PALETTE["blood_hot"],
                                 _NS_morkhaera._alpha(150 * pulse)),
                                (15, 12, 140, 34), 1)
        surface.blit(ring, (x - 85, y - 25))

    # ============================================================
    # SKILL Q: SPIRIT BURST - red energy orb projectile
    # ============================================================
    def _draw_spirit_burst_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morkhaera._target_position(boss, x, y)

        if progress < 0.3:
            # Charge at staff orb.
            t = progress / 0.3
            hx = x + facing * 20
            hy = y - 20
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_morkhaera._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                         (hx, hy), r)
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_mid"],
                                     (hx, hy), max(1, cr - 2))
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_light"],
                                     (hx, hy), max(1, cr - 4))
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                             (hx, hy, 1, 1))
        else:
            # BIG ENERGY ORB projectile.
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 20
            start_y = y - 20
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long trail with feathers.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_morkhaera._alpha(240 - i * 20)
                size = max(1, 8 - i)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_darkest"],
                                          alpha), (px, py), size + 1)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_dark"],
                                          alpha), (px, py), size)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_mid"],
                                          alpha), (px, py), max(1, size - 2))
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_light"],
                                          alpha), (px, py), max(1, size - 4))
                # Trailing feathers.
                if i < 5:
                    spark_x = px + int(math.sin(t * 6 + i) * 4)
                    spark_y = py + int(math.cos(t * 6 + i) * 4)
                    pygame.draw.rect(surface,
                                     (*_NS_morkhaera.PALETTE["blood_shine"],
                                      alpha), (spark_x, spark_y, 1, 1))

            # Bright head.
            for r in range(12, 2, -2):
                alpha = _NS_morkhaera._alpha(80 * (12 - r) / 12)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_light"],
                                          alpha), (bx, by), r)
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_darkest"],
                                     (bx, by), 8)
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_dark"],
                                     (bx, by), 6)
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_mid"],
                                     (bx, by), 4)
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_light"],
                                     (bx, by), 2)
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["blood_shine"],
                             (bx, by, 1, 1))
            pygame.draw.rect(surface, _NS_morkhaera.PALETTE["white"],
                             (bx, by, 1, 1))

            # EXPLOSION on impact (khas skill Q).
            if t > 0.85:
                st = (t - 0.85) / 0.15
                r = int(15 + st * 30)
                alpha = _NS_morkhaera._alpha(240 * (1 - st))
                # Explosion rings.
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_darkest"],
                                          alpha), (tx, ty), r + 3, 3)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_dark"],
                                          alpha), (tx, ty), r, 2)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_mid"],
                                          alpha), (tx, ty), max(1, r - 6), 2)
                _NS_morkhaera._aacircle(surface,
                                         (*_NS_morkhaera.PALETTE["blood_light"],
                                          alpha), (tx, ty), max(1, r - 12), 1)
                # Radial burst spikes.
                for i in range(12):
                    a = i * math.pi / 6
                    ex = tx + int(math.cos(a) * r)
                    ey = ty + int(math.sin(a) * r * 0.7)
                    _NS_morkhaera._aaline(surface,
                                           (*_NS_morkhaera.PALETTE["blood_light"],
                                            alpha), (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_morkhaera.PALETTE["blood_shine"],
                                      alpha), (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: FEATHERED AIR STRIKE - spirit bird attacks target area
    # ============================================================
    def _draw_air_strike_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morkhaera._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Target area circle.
        r = int(50 * min(1.0, progress * 2))
        if r < 5:
            return
        alpha = _NS_morkhaera._alpha(200 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface,
                            (*_NS_morkhaera.PALETTE["blood_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4))

    def _draw_air_strike_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morkhaera._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Spirit bird flies over target dive-bombing.
        # Bird position: moves from boss to above target.
        if progress < 0.3:
            # Bird flies to target.
            t = progress / 0.3
            bx = int(x + (tx - x) * t)
            by = int(y - 40 + math.sin(t * math.pi) * -20)
            _NS_morkhaera._draw_raven(surface, bx, by, 1 if tx > x else -1,
                                        phase, size=1.5)
        else:
            # Bird hovers/dives repeatedly, launching feathers.
            t = (progress - 0.3) / 0.7
            # Bird circles above target.
            hover_angle = phase * 1.5
            bx = tx + int(math.cos(hover_angle) * 30)
            by = ty - 40 + int(math.sin(hover_angle) * 10)
            _NS_morkhaera._draw_raven(surface, bx, by,
                                        1 if math.sin(hover_angle) > 0 else -1,
                                        phase, size=1.5)

            # Feathers rain down at target area (multiple simultaneous).
            num_feathers = 8
            for i in range(num_feathers):
                feather_t = (phase * 1.5 + i * 0.15) % 1.0
                if feather_t > t + 0.3:
                    continue
                # Start from bird, fall to random spot in area.
                target_offset_x = int(math.sin(i * 1.7) * 40)
                target_offset_y = int(math.cos(i * 1.3) * 20)
                fall_target_x = tx + target_offset_x
                fall_target_y = ty + target_offset_y

                fx = int(bx + (fall_target_x - bx) * feather_t)
                fy = int(by + (fall_target_y - by) * feather_t)

                alpha = _NS_morkhaera._alpha(240 * (1 - feather_t * 0.3))

                # Feather trail.
                for tr in range(3):
                    trail_t = feather_t - tr * 0.05
                    if trail_t < 0:
                        continue
                    trail_x = int(bx + (fall_target_x - bx) * trail_t)
                    trail_y = int(by + (fall_target_y - by) * trail_t)
                    talpha = _NS_morkhaera._alpha(alpha * (1 - tr * 0.3))
                    _NS_morkhaera._aacircle(surface,
                                             (*_NS_morkhaera.PALETTE["blood_mid"],
                                              talpha), (trail_x, trail_y),
                                             max(1, 3 - tr))

                # Feather shape.
                angle = math.atan2(fall_target_y - by, fall_target_x - bx)
                perp = angle + math.pi / 2
                tip_x = fx + int(math.cos(angle) * 6)
                tip_y = fy + int(math.sin(angle) * 6)
                back_x = fx - int(math.cos(angle) * 4)
                back_y = fy - int(math.sin(angle) * 4)
                w_a = (fx + int(math.cos(perp) * 2),
                       fy + int(math.sin(perp) * 2))
                w_b = (fx - int(math.cos(perp) * 2),
                       fy - int(math.sin(perp) * 2))
                _NS_morkhaera._poly(surface,
                                     (*_NS_morkhaera.PALETTE["feather_dark"], alpha),
                                     [(tip_x, tip_y), w_a,
                                      (back_x, back_y), w_b])
                _NS_morkhaera._poly(surface,
                                     (*_NS_morkhaera.PALETTE["feather_mid"], alpha), [
                    (tip_x, tip_y), (fx, fy), (back_x, back_y),
                ])
                pygame.draw.rect(surface,
                                 (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                                 (tip_x, tip_y, 1, 1))

                # Small impact when feather reaches target.
                if feather_t > 0.85:
                    imp_t = (feather_t - 0.85) / 0.15
                    imp_r = int(4 + imp_t * 8)
                    imp_alpha = _NS_morkhaera._alpha(200 * (1 - imp_t))
                    _NS_morkhaera._aacircle(surface,
                                             (*_NS_morkhaera.PALETTE["blood_light"],
                                              imp_alpha),
                                             (fall_target_x, fall_target_y),
                                             imp_r, 1)

    # ============================================================
    # SKILL E: ENERGY IMPACT - ground explosion crimson
    # ============================================================
    def _draw_energy_impact_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morkhaera._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Warning circle.
            t = progress / 0.3
            r = int(35 * t)
            alpha = _NS_morkhaera._alpha(180 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning dot in center.
            _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["blood_light"],
                                     (tx, ty), int(3 * t))
        else:
            # Blast zone.
            t = (progress - 0.3) / 0.7
            r = int(35 + t * 15)
            alpha = _NS_morkhaera._alpha(230 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_morkhaera.PALETTE["blood_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_energy_impact_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_morkhaera._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            return

        t = (progress - 0.3) / 0.7

        # BIG BURST at ground (like signature skill E).
        burst_r = int(40 * min(1.0, t * 3))
        alpha = _NS_morkhaera._alpha(255 * (1 - t * 0.6))

        # Central bright core.
        for r in range(burst_r, 0, -2):
            core_alpha = _NS_morkhaera._alpha(alpha * (burst_r - r) / burst_r)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_dark"],
                                      core_alpha), (tx, ty), r)
        _NS_morkhaera._aacircle(surface,
                                 (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                                 (tx, ty), burst_r // 3)
        _NS_morkhaera._aacircle(surface,
                                 (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                 (tx, ty), burst_r // 4)
        _NS_morkhaera._aacircle(surface,
                                 (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                                 (tx, ty), max(1, burst_r // 6))
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["white"],
                         (tx, ty, 1, 1))

        # RADIAL FEATHER SPIKES bursting outward.
        num_spikes = 16
        for i in range(num_spikes):
            spike_angle = i * math.pi * 2 / num_spikes + t * 0.5
            spike_len = int(15 + t * 30)
            tip_x = tx + int(math.cos(spike_angle) * spike_len)
            tip_y = ty + int(math.sin(spike_angle) * spike_len * 0.7)
            mid_x = tx + int(math.cos(spike_angle) * (spike_len * 0.5))
            mid_y = ty + int(math.sin(spike_angle) * (spike_len * 0.5) * 0.7)

            # Feather spike shape.
            perp = spike_angle + math.pi / 2
            w_a = (mid_x + int(math.cos(perp) * 3),
                   mid_y + int(math.sin(perp) * 3))
            w_b = (mid_x - int(math.cos(perp) * 3),
                   mid_y - int(math.sin(perp) * 3))

            _NS_morkhaera._poly(surface,
                                 (*_NS_morkhaera.PALETTE["blood_darkest"], alpha),
                                 [(tip_x, tip_y), w_a, (tx, ty), w_b])
            _NS_morkhaera._poly(surface,
                                 (*_NS_morkhaera.PALETTE["blood_dark"], alpha), [
                (tip_x, tip_y),
                (int((tip_x + w_a[0]) / 2), int((tip_y + w_a[1]) / 2)),
                (tx, ty),
                (int((tip_x + w_b[0]) / 2), int((tip_y + w_b[1]) / 2)),
            ])
            _NS_morkhaera._poly(surface,
                                 (*_NS_morkhaera.PALETTE["blood_mid"], alpha), [
                (tip_x, tip_y), (mid_x, mid_y), (tx, ty),
            ])
            _NS_morkhaera._aaline(surface,
                                   (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                   (tx, ty), (tip_x, tip_y), 1)
            _NS_morkhaera._aaline(surface,
                                   (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                                   (tx, ty),
                                   (int((tx + tip_x) / 2),
                                    int((ty + tip_y) / 2)), 1)
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["white"], alpha),
                             (tip_x, tip_y, 1, 1))

        # Rising feather particles.
        for i in range(10):
            p_t = (phase * 1.5 + i * 0.1) % 1.0
            angle = i * math.pi * 2 / 10
            px = tx + int(math.cos(angle) * 30)
            py = ty - int(p_t * 40)
            p_alpha = _NS_morkhaera._alpha(200 * (1 - p_t))
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"],
                                      p_alpha), (px, py), 2)
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_shine"], p_alpha),
                             (px, py, 1, 1))

    # ============================================================
    # SKILL R: ETHEREAL WAY - transform into bird form
    # ============================================================
    def _draw_ethereal_ground(surface, boss, x, y, timer, pulse):
        # Ground effect area follows bird form.
        r = int(50 + math.sin(pulse * 2) * 5)
        alpha = _NS_morkhaera._alpha(180)
        pygame.draw.ellipse(surface,
                            (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                            (x - r, y + 50 - r // 3,
                             r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface,
                            (*_NS_morkhaera.PALETTE["blood_mid"], alpha),
                            (x - r + 3, y + 50 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_bird_form(surface, boss, x, y, timer, phase):
        """Transform pose: LARGE crimson raven form."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Transformation phase.
        if progress < 0.2:
            # Show boss dissolving into feathers.
            t = progress / 0.2
            fade_alpha = int(255 * (1 - t))
            # Ghostly witch body fading.
            bob = int(math.sin(phase * 0.5) * 3)
            _NS_morkhaera._draw_shadow(surface, x, y + 55)
            # Draw witch semi-transparent (skip - simpler: just draw feathers exploding out).
            for i in range(20):
                angle = i * math.pi / 10
                dist = int(t * 40)
                fx = x + int(math.cos(angle) * dist)
                fy = y + int(math.sin(angle) * dist * 0.5)
                fa = _NS_morkhaera._alpha(220 * (1 - t))
                _NS_morkhaera._poly(surface,
                                     (*_NS_morkhaera.PALETTE["feather_mid"], fa), [
                    (fx, fy - 3), (fx + 2, fy),
                    (fx, fy + 3), (fx - 2, fy),
                ])
                pygame.draw.rect(surface,
                                 (*_NS_morkhaera.PALETTE["blood_light"], fa),
                                 (fx, fy, 1, 1))
        else:
            # Draw LARGE raven form.
            bird_bob = int(math.sin(phase * 1.5) * 6)
            _NS_morkhaera._draw_shadow(surface, x, y + 55)
            _NS_morkhaera._draw_large_raven(surface, x, y - 5 + bird_bob,
                                              facing, phase)

    def _draw_large_raven(surface, cx, cy, facing, phase):
        """Massive crimson raven (transformed boss)."""
        beat = math.sin(phase * 1.5) * 6
        size = 2.5  # bigger than companion bird

        # Body (larger).
        body_shape = [
            (cx - int(10 * size), cy),
            (cx - int(12 * size), cy - int(3 * size)),
            (cx - int(10 * size), cy - int(8 * size)),
            (cx + int(2 * size), cy - int(10 * size)),
            (cx + int(10 * size), cy - int(6 * size)),
            (cx + int(13 * size), cy - int(2 * size)),
            (cx + int(10 * size), cy + int(3 * size)),
            (cx, cy + int(5 * size)),
            (cx - int(8 * size), cy + int(3 * size)),
        ]
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in body_shape])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_darkest"],
                             body_shape)
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_dark"], [
            (cx - int(8 * size), cy - int(2 * size)),
            (cx - int(10 * size), cy - int(5 * size)),
            (cx - int(6 * size), cy - int(8 * size)),
            (cx + int(2 * size), cy - int(9 * size)),
            (cx + int(10 * size), cy - int(5 * size)),
            (cx + int(11 * size), cy - int(2 * size)),
            (cx + int(8 * size), cy + int(2 * size)),
            (cx - int(6 * size), cy + int(2 * size)),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["bird_mid"], [
            (cx - int(5 * size), cy - int(3 * size)),
            (cx - int(6 * size), cy - int(7 * size)),
            (cx + int(2 * size), cy - int(8 * size)),
            (cx + int(8 * size), cy - int(3 * size)),
            (cx + int(5 * size), cy),
            (cx - int(3 * size), cy),
        ])

        # Head (large).
        head_x = cx + int(facing * 12 * size)
        head_y = cy - int(6 * size)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["bird_darkest"],
                                 (head_x, head_y), int(6 * size))
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["bird_dark"],
                                 (head_x, head_y), int(5 * size))
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["bird_mid"],
                                 (head_x, head_y - int(size)),
                                 int(3 * size))

        # Big beak.
        beak_tip_x = head_x + int(facing * 10 * size)
        beak_tip_y = head_y + int(size)
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["gold_dark"], [
            (head_x + int(facing * 4 * size), head_y - int(size)),
            (beak_tip_x, beak_tip_y),
            (head_x + int(facing * 4 * size), head_y + int(3 * size)),
        ])
        _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["gold_mid"], [
            (head_x + int(facing * 4 * size), head_y),
            (beak_tip_x, beak_tip_y),
            (head_x + int(facing * 4 * size), head_y + int(2 * size)),
        ])
        _NS_morkhaera._aaline(surface, _NS_morkhaera.PALETTE["gold_light"],
                               (head_x + int(facing * 4 * size), head_y),
                               (beak_tip_x, beak_tip_y), 1)

        # BIG RED EYE.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        eye_x = head_x + int(facing * 3 * size)
        eye_y = head_y - int(size)
        for r in range(int(5 * size), 0, -1):
            alpha = _NS_morkhaera._alpha(200 * (5 * size - r)
                                          / (5 * size) * pulse)
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                                     (eye_x, eye_y), r)
        _NS_morkhaera._aacircle(surface, _NS_morkhaera.PALETTE["eye_red"],
                                 (eye_x, eye_y), 2)
        pygame.draw.rect(surface, _NS_morkhaera.PALETTE["white"],
                         (eye_x, eye_y, 1, 1))

        # HUGE WINGS spread wide.
        for side in [-1, 1]:
            wing_base_x = cx + int(side * 3 * size)
            wing_base_y = cy - int(6 * size)

            # 6 primary feathers per wing (very big).
            for feather_i, (angle_deg, length) in enumerate([
                (100, 32), (120, 38), (140, 42), (160, 38), (180, 32), (200, 24),
            ]):
                fa = math.radians(angle_deg) * side - math.radians(beat)
                tip_x = wing_base_x + int(math.cos(fa) * length * size)
                tip_y = wing_base_y + int(math.sin(fa) * length * size)

                perp_a = fa + math.pi / 2
                w_a = (wing_base_x + int(math.cos(perp_a) * 3),
                       wing_base_y + int(math.sin(perp_a) * 3))
                w_b = (wing_base_x - int(math.cos(perp_a) * 3),
                       wing_base_y - int(math.sin(perp_a) * 3))

                # Shadow.
                _NS_morkhaera._poly(surface, _NS_morkhaera.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (w_a[0] + 1, w_a[1] + 1),
                    (w_b[0] + 1, w_b[1] + 1),
                ])
                _NS_morkhaera._poly(surface,
                                     _NS_morkhaera.PALETTE["bird_darkest"],
                                     [(tip_x, tip_y), w_a, w_b])
                _NS_morkhaera._poly(surface,
                                     _NS_morkhaera.PALETTE["bird_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + w_a[0]) / 2), int((tip_y + w_a[1]) / 2)),
                    (int((tip_x + w_b[0]) / 2), int((tip_y + w_b[1]) / 2)),
                ])
                _NS_morkhaera._poly(surface,
                                     _NS_morkhaera.PALETTE["bird_mid"], [
                    (tip_x, tip_y),
                    (int(tip_x * 0.7 + wing_base_x * 0.3),
                     int(tip_y * 0.7 + wing_base_y * 0.3)),
                    (int(tip_x * 0.7 + wing_base_x * 0.3 + 1),
                     int(tip_y * 0.7 + wing_base_y * 0.3)),
                ])
                _NS_morkhaera._aaline(surface,
                                       _NS_morkhaera.PALETTE["bird_glow"],
                                       (wing_base_x, wing_base_y),
                                       (tip_x, tip_y), 1)
                # Bright red tip glow.
                for gr in range(4, 0, -1):
                    alpha = _NS_morkhaera._alpha(150 * (4 - gr) / 4)
                    _NS_morkhaera._aacircle(surface,
                                             (*_NS_morkhaera.PALETTE["blood_light"],
                                              alpha), (tip_x, tip_y), gr)
                pygame.draw.rect(surface,
                                 _NS_morkhaera.PALETTE["blood_shine"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface,
                                 _NS_morkhaera.PALETTE["white"],
                                 (tip_x, tip_y, 1, 1))

        # Tail (spread).
        tail_x = cx - int(facing * 12 * size)
        tail_y = cy - int(2 * size)
        for i, ta in enumerate((-0.4, -0.15, 0, 0.15, 0.4)):
            tip_x = tail_x - int(facing * 14 * size)
            tip_y = tail_y + int(ta * 12 * size)
            _NS_morkhaera._aaline(surface,
                                   _NS_morkhaera.PALETTE["bird_darkest"],
                                   (tail_x, tail_y), (tip_x, tip_y), 3)
            _NS_morkhaera._aaline(surface,
                                   _NS_morkhaera.PALETTE["bird_dark"],
                                   (tail_x, tail_y), (tip_x, tip_y), 2)
            _NS_morkhaera._aaline(surface,
                                   _NS_morkhaera.PALETTE["bird_mid"],
                                   (tail_x, tail_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface,
                             _NS_morkhaera.PALETTE["blood_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface,
                             _NS_morkhaera.PALETTE["blood_shine"],
                             (tip_x, tip_y, 1, 1))

        # HUGE aura around bird.
        for r in range(int(50 * size), 5, -3):
            alpha = _NS_morkhaera._alpha(50 * (50 * size - r) / (50 * size))
            _NS_morkhaera._aacircle(surface,
                                     (*_NS_morkhaera.PALETTE["blood_dark"], alpha),
                                     (cx, cy - 2), r)

    def _draw_ethereal_fg(surface, boss, x, y, timer, phase):
        """Foreground effects during ethereal way."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Feathers scattered around from bird flight.
        for i in range(20):
            angle = phase * 0.5 + i * math.pi / 10
            radius = 60 + int(math.sin(phase * 2 + i) * 20)
            fx = x + int(math.cos(angle) * radius)
            fy = y + int(math.sin(angle) * radius * 0.6)
            fade = math.sin(phase * 3 + i) * 0.5 + 0.5
            alpha = _NS_morkhaera._alpha(200 * fade)
            _NS_morkhaera._poly(surface, (*_NS_morkhaera.PALETTE["feather_mid"], alpha), [
                (fx, fy - 2), (fx + 1, fy),
                (fx, fy + 2), (fx - 1, fy),
            ])
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_light"], alpha),
                             (fx, fy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_morkhaera.PALETTE["blood_shine"], alpha),
                             (fx, fy, 1, 1))

        # Red energy shockwaves periodically.
        wave_t = (phase * 0.8) % 1.0
        wave_r = int(30 + wave_t * 60)
        wave_alpha = _NS_morkhaera._alpha(200 * (1 - wave_t))
        pygame.draw.ellipse(surface,
                            (*_NS_morkhaera.PALETTE["blood_light"], wave_alpha),
                            (x - wave_r, y - wave_r // 3,
                             wave_r * 2, wave_r * 2 // 3), 2)


# ====================================================================
# aurelion.py
# ====================================================================

"""
AURELION - The Golden Sovereign
TRUE BOSS royal king warrior dengan kingdom army power.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_aurelion:
    """Namespace aurelion - golden sovereign true boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin tones
        "skin_darkest": (70, 45, 30),
        "skin_dark": (130, 90, 65),
        "skin_mid": (185, 140, 105),
        "skin_light": (225, 185, 145),
        "skin_shine": (245, 215, 180),

        # Muscle
        "muscle_shadow": (85, 55, 35),
        "muscle_deep": (50, 30, 20),

        # Black hair/beard
        "hair_darkest": (10, 8, 10),
        "hair_dark": (35, 30, 30),
        "hair_mid": (65, 55, 50),

        # Brown leather armor (secondary)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (55, 35, 20),
        "leather_mid": (95, 65, 35),
        "leather_light": (155, 115, 65),

        # Royal red cape
        "cape_darkest": (45, 5, 15),
        "cape_dark": (95, 15, 30),
        "cape_mid": (165, 30, 45),
        "cape_light": (215, 60, 80),
        "cape_shine": (240, 130, 140),

        # Gold armor (main - royal)
        "gold_darkest": (55, 40, 5),
        "gold_dark": (115, 85, 20),
        "gold_mid": (200, 155, 40),
        "gold_light": (245, 215, 95),
        "gold_shine": (255, 245, 180),
        "gold_bright": (255, 255, 220),

        # Deep gold (armor shadow)
        "gold_deep": (80, 55, 10),

        # Silver armor accents
        "silver_dark": (75, 80, 90),
        "silver_mid": (145, 150, 165),
        "silver_light": (210, 215, 225),
        "silver_shine": (245, 248, 252),

        # Red gems (crown, shield)
        "gem_dark": (80, 10, 20),
        "gem_mid": (180, 30, 50),
        "gem_light": (255, 80, 110),
        "gem_shine": (255, 180, 200),

        # Blue gems (accents)
        "blue_dark": (10, 30, 90),
        "blue_mid": (40, 90, 190),
        "blue_light": (120, 180, 250),

        # ROYAL RADIANT GOLD (main skill theme)
        "royal_darkest": (65, 45, 5),
        "royal_dark": (140, 100, 20),
        "royal_mid": (230, 180, 50),
        "royal_light": (255, 225, 120),
        "royal_hot": (255, 245, 190),
        "royal_shine": (255, 255, 240),

        # Spear tip steel
        "steel_dark": (55, 60, 75),
        "steel_mid": (130, 140, 160),
        "steel_light": (220, 225, 235),

        # Eye
        "eye_dark": (15, 10, 8),
        "eye_white": (240, 235, 225),
        "eye_amber": (200, 155, 60),

        # Ground/rune
        "rune_dark": (55, 40, 8),
        "rune_mid": (180, 140, 40),
        "rune_light": (255, 220, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_aurelion._clamp(color)
        if _NS_aurelion.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_aurelion._clamp(color)
        if _NS_aurelion.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue
        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_aurelion._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_aurelion._clamp(color), valid_points)

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
        return int(x + 240 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_aurelion(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_aurelion._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_au_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # BIG royal aura (true boss).
        _NS_aurelion._draw_royal_aura(surface, x, y, pulse)
        _NS_aurelion._draw_ground_ring(surface, x, y + 55, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_aurelion._draw_kings_command_ground(surface, boss, x, y,
                                                     skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelion._draw_kings_summonon_ground(surface, boss, x, y,
                                                      skill_timer, pulse)
        elif active_skill == "q":
            _NS_aurelion._draw_call_courage_ground(surface, boss, x, y,
                                                    skill_timer, pulse)

        # Body pose.
        if active_skill == "q":
            _NS_aurelion._draw_body_rush(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_aurelion._draw_body_slash(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurelion._draw_body_command(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelion._draw_body_summon(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_aurelion._draw_body_attack(surface, boss, x, y)
        else:
            _NS_aurelion._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "q":
            _NS_aurelion._draw_call_courage_fg(surface, boss, x, y,
                                                skill_timer, pulse)
        elif active_skill == "w":
            _NS_aurelion._draw_guardian_assault_fg(surface, boss, x, y,
                                                    skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurelion._draw_kings_command_fg(surface, boss, x, y,
                                                 skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelion._draw_kings_summonon_fg(surface, boss, x, y,
                                                  skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_au_previous_timer", 0))
        active = bool(getattr(boss, "_au_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._au_attack_active = True
            boss._au_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._au_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._au_attack_frame = int(getattr(boss, "_au_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._au_attack_active = False
            boss._au_attack_frame = 0
            active = False

        boss._au_previous_timer = timer
        boss._au_attack_progress = (
            min(1.0, getattr(boss, "_au_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_aurelion._draw_shadow(surface, x, y + 55)
        _NS_aurelion._draw_royal_particles(surface, x, y + 40, boss.pulse)
        _NS_aurelion._draw_king_body(surface, x, y + bob, boss.direction,
                                       boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_au_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_au_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        # Small forward lunge for spear thrust.
        if progress < 0.4:
            lunge = int(progress / 0.4 * 8) * facing
        else:
            lunge = int((1 - (progress - 0.4) / 0.6) * 8) * facing

        _NS_aurelion._draw_shadow(surface, x + lunge, y + 55)
        _NS_aurelion._draw_royal_particles(surface, x + lunge, y + 40, boss.pulse)
        _NS_aurelion._draw_king_body(surface, x + lunge, y + bob,
                                       facing, boss.pulse,
                                       "attack", progress)
        _NS_aurelion._draw_spear_thrust(surface, x + lunge, y + bob,
                                          facing, progress)

    def _draw_body_rush(surface, boss, x, y, timer, pulse):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.5) * 3)
        # Charging forward with speed aura.
        if progress < 0.5:
            lunge = int(progress / 0.5 * 30) * boss.direction
        else:
            lunge = int(30) * boss.direction

        _NS_aurelion._draw_shadow(surface, x + lunge, y + 55)
        _NS_aurelion._draw_royal_particles(surface, x + lunge, y + 40, pulse,
                                             intense=True)
        _NS_aurelion._draw_king_body(surface, x + lunge, y + bob,
                                       boss.direction, pulse, "rush",
                                       progress)

    def _draw_body_slash(surface, boss, x, y, timer, pulse):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.5) * 3)
        _NS_aurelion._draw_shadow(surface, x, y + 55)
        _NS_aurelion._draw_royal_particles(surface, x, y + 40, pulse,
                                             intense=True)
        _NS_aurelion._draw_king_body(surface, x, y + bob, boss.direction,
                                       pulse, "slash", progress)

    def _draw_body_command(surface, boss, x, y, timer, pulse):
        bob = int(math.sin(pulse * 0.5) * 3)
        # Raise spear high for command.
        lift = int(math.sin(pulse * 1.5) * 2) + 4
        _NS_aurelion._draw_shadow(surface, x, y + 55)
        _NS_aurelion._draw_royal_particles(surface, x, y + 40, pulse,
                                             intense=True)
        _NS_aurelion._draw_king_body(surface, x, y + bob - lift,
                                       boss.direction, pulse, "command")

    def _draw_body_summon(surface, boss, x, y, timer, pulse):
        bob = int(math.sin(pulse * 0.5) * 3)
        # Raise spear high for summon.
        lift = int(math.sin(pulse * 1.5) * 3) + 5
        _NS_aurelion._draw_shadow(surface, x, y + 55)
        _NS_aurelion._draw_royal_particles(surface, x, y + 40, pulse,
                                             intense=True)
        _NS_aurelion._draw_king_body(surface, x, y + bob - lift,
                                       boss.direction, pulse, "summon")

    # ============================================================
    # KING BODY (heavy armored royal warrior)
    # ============================================================
    def _draw_king_body(surface, cx, cy, facing, phase, action,
                         progress=0):
        """Full king: cape (back), legs, torso armor, arms with shield + spear, crown head."""
        _NS_aurelion._draw_royal_cape(surface, cx, cy, facing, phase)
        _NS_aurelion._draw_back_leg(surface, cx, cy, facing, phase, action)
        _NS_aurelion._draw_front_leg(surface, cx, cy, facing, phase, action)
        _NS_aurelion._draw_king_torso(surface, cx, cy, facing, phase, action)
        _NS_aurelion._draw_shield_arm(surface, cx, cy, facing, phase, action)
        _NS_aurelion._draw_king_head(surface, cx, cy - 22, facing, phase, action)
        _NS_aurelion._draw_spear_arm(surface, cx, cy, facing, phase, action,
                                       progress)

    def _draw_royal_cape(surface, cx, cy, facing, phase):
        """Long red royal cape flowing behind."""
        sway = math.sin(phase * 0.4) * 3
        sway2 = math.sin(phase * 0.6 + 1) * 2

        # Cape trails behind body.
        back_x_off = -facing * 2

        cape_shape = [
            (cx - facing * 8, cy - 10),
            (cx - facing * 14, cy - 6),
            (cx - facing * 20 + back_x_off, cy + 4),
            (cx - facing * 24 + int(sway), cy + 20),
            (cx - facing * 26 + int(sway), cy + 34),
            (cx - facing * 22 + int(sway2), cy + 48),
            (cx - facing * 14 + int(sway2), cy + 58),
            (cx - facing * 4 + int(sway2), cy + 62),
            (cx + facing * 4, cy + 58),
            (cx + facing * 2, cy + 40),
            (cx - facing * 2, cy + 20),
            (cx - facing * 4, cy + 5),
            (cx - facing * 6, cy - 4),
        ]

        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"],
                            [(px + 3, py + 3) for px, py in cape_shape])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_darkest"],
                            cape_shape)
        # Inner darker fold.
        inner = [
            (cx - facing * 7, cy - 8),
            (cx - facing * 12, cy - 4),
            (cx - facing * 18 + back_x_off, cy + 6),
            (cx - facing * 22 + int(sway), cy + 22),
            (cx - facing * 22 + int(sway), cy + 32),
            (cx - facing * 18 + int(sway2), cy + 46),
            (cx - facing * 12 + int(sway2), cy + 55),
            (cx - facing * 4 + int(sway2), cy + 58),
            (cx + facing * 2, cy + 54),
            (cx, cy + 38),
            (cx - facing * 2, cy + 18),
            (cx - facing * 4, cy + 4),
        ]
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_dark"], inner)
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_mid"], [
            (cx - facing * 6, cy - 6),
            (cx - facing * 10, cy - 2),
            (cx - facing * 16 + int(sway), cy + 24),
            (cx - facing * 15 + int(sway2), cy + 42),
            (cx - facing * 8 + int(sway2), cy + 52),
            (cx, cy + 50),
            (cx - facing * 2, cy + 30),
            (cx - facing * 4, cy + 10),
        ])
        # Bright fabric fold in center.
        for i, ratio in enumerate((-0.3, 0.0, 0.3)):
            top_x = cx + int(ratio * 6) - facing * 6
            bot_x = cx + int(ratio * 12) - facing * 10 + int(sway2)
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["cape_light"],
                                  (top_x, cy - 4), (bot_x, cy + 48), 1)

        # Gold trim on edges.
        for i in range(5):
            trim_x = cx - facing * (14 + i * 3) + int(sway * 0.5)
            trim_y = cy + 50 + i * 2
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_dark"],
                             (trim_x, trim_y, 2, 1))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_mid"],
                             (trim_x, trim_y, 1, 1))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                             (trim_x, trim_y, 1, 1))

        # Gold clasp at shoulder (holding cape).
        clasp_x = cx - facing * 6
        clasp_y = cy - 8
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (clasp_x, clasp_y), 4)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (clasp_x, clasp_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_light"],
                                (clasp_x, clasp_y), 2)
        # Red gem in clasp.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_dark"],
                         (clasp_x - 1, clasp_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_mid"],
                         (clasp_x, clasp_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_shine"],
                         (clasp_x, clasp_y - 1, 1, 1))

    def _draw_back_leg(surface, cx, cy, facing, phase, action):
        base_x = cx - facing * 4
        knee_x = cx - facing * 6
        knee_y = cy + 18
        foot_x = cx - facing * 5
        foot_y = cy + 32

        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["shadow_deep"],
                              (base_x + 2, cy + 8), (knee_x + 2, knee_y + 1), 7)
        # Thigh (leather).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_darkest"], [
            (base_x - 4, cy + 8), (base_x + 3, cy + 8),
            (knee_x + 3, knee_y), (knee_x - 3, knee_y),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_dark"], [
            (base_x - 3, cy + 9), (base_x + 2, cy + 9),
            (knee_x + 2, knee_y - 1), (knee_x - 2, knee_y - 1),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_mid"], [
            (base_x - 1, cy + 10), (base_x + 1, cy + 10),
            (knee_x + 1, knee_y - 2), (knee_x, knee_y - 2),
        ])
        # Shin (gold greaves).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_darkest"], [
            (knee_x - 3, knee_y), (knee_x + 3, knee_y),
            (foot_x + 2, foot_y), (foot_x - 2, foot_y),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
            (knee_x - 2, knee_y + 1), (knee_x + 2, knee_y + 1),
            (foot_x + 1, foot_y - 1), (foot_x - 1, foot_y - 1),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 1, knee_y + 2),
            (foot_x, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                              (knee_x, knee_y + 2), (foot_x, foot_y - 2), 1)
        # Boot (dark).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_darkest"], [
            (foot_x - 4, foot_y - 1), (foot_x + 3, foot_y - 1),
            (foot_x + 3, foot_y + 2), (foot_x - 4, foot_y + 2),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_dark"], [
            (foot_x - 3, foot_y), (foot_x + 2, foot_y),
        ])
        # Gold trim.
        pygame.draw.line(surface, _NS_aurelion.PALETTE["gold_mid"],
                         (foot_x - 4, foot_y - 1), (foot_x + 3, foot_y - 1), 1)

    def _draw_front_leg(surface, cx, cy, facing, phase, action):
        base_x = cx + facing * 4
        knee_x = cx + facing * 6
        knee_y = cy + 18
        foot_x = cx + facing * 8
        foot_y = cy + 32

        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["shadow_deep"],
                              (base_x + 2, cy + 8), (knee_x + 2, knee_y + 1), 8)
        # Thigh.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_darkest"], [
            (base_x - 4, cy + 8), (base_x + 4, cy + 8),
            (knee_x + 4, knee_y), (knee_x - 4, knee_y),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_dark"], [
            (base_x - 3, cy + 9), (base_x + 3, cy + 9),
            (knee_x + 3, knee_y - 1), (knee_x - 3, knee_y - 1),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_mid"], [
            (base_x - 1, cy + 10), (base_x + 2, cy + 10),
            (knee_x + 2, knee_y - 2), (knee_x, knee_y - 2),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_light"], [
            (base_x, cy + 11), (base_x + 1, cy + 11),
            (knee_x + 1, knee_y - 3), (knee_x, knee_y - 3),
        ])
        # Knee gold cap.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (knee_x, knee_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (knee_x, knee_y), 2)
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (knee_x, knee_y - 1, 1, 1))
        # Shin (gold greaves - shining).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_darkest"], [
            (knee_x - 4, knee_y + 2), (knee_x + 4, knee_y + 2),
            (foot_x + 3, foot_y), (foot_x - 3, foot_y),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
            (knee_x - 3, knee_y + 3), (knee_x + 3, knee_y + 3),
            (foot_x + 2, foot_y - 1), (foot_x - 2, foot_y - 1),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_mid"], [
            (knee_x - 2, knee_y + 4), (knee_x + 2, knee_y + 4),
            (foot_x + 1, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_light"], [
            (knee_x - 1, knee_y + 5), (knee_x + 1, knee_y + 5),
            (foot_x, foot_y - 3), (foot_x, foot_y - 3),
        ])
        # Gold shine highlight.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (knee_x, knee_y + 8, 1, 1))
        # Boot.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_darkest"], [
            (foot_x - 4, foot_y - 1), (foot_x + 5, foot_y - 1),
            (foot_x + 5, foot_y + 3), (foot_x - 4, foot_y + 3),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_dark"], [
            (foot_x - 3, foot_y), (foot_x + 4, foot_y),
            (foot_x + 4, foot_y + 2), (foot_x - 3, foot_y + 2),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_mid"], [
            (foot_x - 2, foot_y + 1), (foot_x + 3, foot_y + 1),
        ])
        # Gold boot trim.
        pygame.draw.line(surface, _NS_aurelion.PALETTE["gold_dark"],
                         (foot_x - 4, foot_y - 1), (foot_x + 5, foot_y - 1), 1)
        pygame.draw.line(surface, _NS_aurelion.PALETTE["gold_mid"],
                         (foot_x - 3, foot_y - 1), (foot_x + 4, foot_y - 1), 1)

    def _draw_king_torso(surface, cx, cy, facing, phase, action):
        """Heavy gold + leather chest armor with lion emblem."""
        breath = math.sin(phase * 0.7) * 1

        # Chest silhouette (wide muscular).
        torso_shape = [
            (cx - 12, cy - 10),
            (cx - 14, cy - 4),
            (cx - 12, cy + 3),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 12, cy + 3),
            (cx + 14, cy - 4),
            (cx + 12, cy - 10),
            (cx + 6, cy - 13),
            (cx - 6, cy - 13),
        ]
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_shape])
        # Leather base.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_darkest"], torso_shape)
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_dark"], [
            (cx - 11, cy - 8), (cx - 13, cy - 3),
            (cx - 11, cy + 2), (cx - 7, cy + 8),
            (cx + 7, cy + 8), (cx + 11, cy + 2),
            (cx + 13, cy - 3), (cx + 11, cy - 8),
            (cx + 5, cy - 12), (cx - 5, cy - 12),
        ])
        # GOLD CHEST PLATE (armored).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_deep"], [
            (cx - 10, cy - 8), (cx + 10, cy - 8),
            (cx + 12, cy - 3), (cx + 10, cy + 4),
            (cx + 6, cy + 8), (cx - 6, cy + 8),
            (cx - 10, cy + 4), (cx - 12, cy - 3),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_darkest"], [
            (cx - 9, cy - 7), (cx + 9, cy - 7),
            (cx + 11, cy - 3), (cx + 9, cy + 3),
            (cx + 5, cy + 7), (cx - 5, cy + 7),
            (cx - 9, cy + 3), (cx - 11, cy - 3),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
            (cx - 8, cy - 6), (cx + 8, cy - 6),
            (cx + 10, cy - 3), (cx + 8, cy + 2),
            (cx + 5, cy + 6), (cx - 5, cy + 6),
            (cx - 8, cy + 2), (cx - 10, cy - 3),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 8, cy - 2), (cx + 7, cy + 4),
            (cx - 7, cy + 4), (cx - 8, cy - 2),
        ])

        # Pectorals armor curves (indicating chest).
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_darkest"],
                              (cx - 6, cy - 4), (cx - 6, cy + 3), 1)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_darkest"],
                              (cx + 6, cy - 4), (cx + 6, cy + 3), 1)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                              (cx - 5, cy - 4), (cx - 5, cy + 2), 1)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                              (cx + 5, cy - 4), (cx + 5, cy + 2), 1)

        # LION EMBLEM at chest center.
        # Lion mane circle.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (cx, cy - 1), 4)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (cx, cy - 1), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (cx, cy - 1), 2)
        # Small lion face detail (eyes as dots).
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_darkest"],
                         (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_darkest"],
                         (cx + 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (cx, cy - 2, 1, 1))
        # Mane rays.
        for angle_i in range(6):
            a = angle_i * math.pi / 3
            rx = cx + int(math.cos(a) * 4)
            ry = cy - 1 + int(math.sin(a) * 4)
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_light"],
                             (rx, ry, 1, 1))

        # Bright shine highlights.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (cx - 8, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (cx + 7, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_bright"],
                         (cx - 8, cy + 2, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_bright"],
                         (cx + 7, cy + 2, 1, 1))

        # Belt with gold buckle at waist.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_darkest"], [
            (cx - 10, cy + 8), (cx + 10, cy + 8),
            (cx + 10, cy + 12), (cx - 10, cy + 12),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["leather_dark"], [
            (cx - 9, cy + 9), (cx + 9, cy + 9),
            (cx + 9, cy + 11), (cx - 9, cy + 11),
        ])
        # Belt gold buckle with lion.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_dark"],
                         (cx - 4, cy + 8, 8, 4))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_mid"],
                         (cx - 3, cy + 9, 6, 2))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_light"],
                         (cx - 2, cy + 9, 4, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (cx, cy + 9, 1, 1))
        # Small lion in buckle.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_dark"],
                         (cx - 1, cy + 9, 2, 2))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_mid"],
                         (cx, cy + 9, 1, 1))

        # Shoulder pauldrons (large gold).
        for side in [-1, 1]:
            pauldron_x = cx + side * 13
            pauldron_y = cy - 10
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"], [
                (pauldron_x + 1, pauldron_y - 1),
                (pauldron_x + side * 5 + 1, pauldron_y + 1),
                (pauldron_x + side * 6 + 1, pauldron_y + 7),
                (pauldron_x - 1 + 1, pauldron_y + 8),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_darkest"], [
                (pauldron_x, pauldron_y - 2),
                (pauldron_x + side * 5, pauldron_y),
                (pauldron_x + side * 6, pauldron_y + 6),
                (pauldron_x - 1, pauldron_y + 7),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
                (pauldron_x + side, pauldron_y - 1),
                (pauldron_x + side * 4, pauldron_y + 1),
                (pauldron_x + side * 5, pauldron_y + 5),
                (pauldron_x, pauldron_y + 6),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_mid"], [
                (pauldron_x + side * 2, pauldron_y),
                (pauldron_x + side * 4, pauldron_y + 2),
                (pauldron_x + side * 4, pauldron_y + 4),
                (pauldron_x + side, pauldron_y + 5),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_light"], [
                (pauldron_x + side * 2, pauldron_y + 1),
                (pauldron_x + side * 3, pauldron_y + 3),
                (pauldron_x + side * 2, pauldron_y + 4),
            ])
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                             (pauldron_x + side * 2, pauldron_y + 2, 1, 1))
            # Small spike on top.
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
                (pauldron_x + side, pauldron_y - 3),
                (pauldron_x, pauldron_y),
                (pauldron_x + side * 2, pauldron_y),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_light"], [
                (pauldron_x + side, pauldron_y - 3),
                (pauldron_x + side, pauldron_y),
                (pauldron_x + side * 2, pauldron_y),
            ])

    def _draw_king_head(surface, cx, cy, facing, phase, action):
        """Face with black hair, beard, GOLD LION CROWN."""
        head_cx = cx
        head_cy = cy

        # Face base (tan, masculine).
        face_shape = [
            (head_cx - 5, head_cy - 3), (head_cx - 6, head_cy + 1),
            (head_cx - 5, head_cy + 5), (head_cx - 2, head_cy + 7),
            (head_cx + 3, head_cy + 7), (head_cx + 5, head_cy + 5),
            (head_cx + 6, head_cy + 1), (head_cx + 5, head_cy - 3),
            (head_cx + 2, head_cy - 6), (head_cx - 2, head_cy - 6),
        ]
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in face_shape])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["skin_darkest"],
                            face_shape)
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["skin_dark"], [
            (head_cx - 4, head_cy - 2), (head_cx - 5, head_cy + 1),
            (head_cx - 4, head_cy + 4), (head_cx + 4, head_cy + 4),
            (head_cx + 5, head_cy + 1), (head_cx + 4, head_cy - 2),
            (head_cx + 2, head_cy - 5), (head_cx - 2, head_cy - 5),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["skin_mid"], [
            (head_cx - 3, head_cy - 1), (head_cx - 4, head_cy + 1),
            (head_cx - 3, head_cy + 3), (head_cx + 3, head_cy + 3),
            (head_cx + 4, head_cy + 1), (head_cx + 3, head_cy - 1),
            (head_cx + 1, head_cy - 4), (head_cx - 1, head_cy - 4),
        ])
        # Cheek highlight.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["skin_light"], [
            (head_cx - 1, head_cy), (head_cx + 2, head_cy),
            (head_cx + 2, head_cy + 2), (head_cx - 1, head_cy + 2),
        ])
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["skin_shine"],
                         (head_cx, head_cy + 1, 1, 1))

        # Short black hair on top (sides).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["hair_darkest"], [
            (head_cx - 6, head_cy - 4), (head_cx - 7, head_cy),
            (head_cx - 5, head_cy - 1), (head_cx - 4, head_cy - 4),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["hair_dark"], [
            (head_cx - 5, head_cy - 3), (head_cx - 6, head_cy),
            (head_cx - 4, head_cy - 1),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["hair_darkest"], [
            (head_cx + 4, head_cy - 4), (head_cx + 5, head_cy - 1),
            (head_cx + 7, head_cy), (head_cx + 6, head_cy - 4),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["hair_dark"], [
            (head_cx + 4, head_cy - 3), (head_cx + 6, head_cy),
            (head_cx + 5, head_cy - 1),
        ])

        # BEARD (black, chin+jaw).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["hair_darkest"], [
            (head_cx - 4, head_cy + 4), (head_cx + 4, head_cy + 4),
            (head_cx + 3, head_cy + 7), (head_cx - 3, head_cy + 7),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["hair_dark"], [
            (head_cx - 3, head_cy + 5), (head_cx + 3, head_cy + 5),
            (head_cx + 2, head_cy + 6), (head_cx - 2, head_cy + 6),
        ])
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["hair_mid"],
                         (head_cx, head_cy + 5, 1, 1))
        # Mustache hint.
        pygame.draw.line(surface, _NS_aurelion.PALETTE["hair_darkest"],
                         (head_cx - 2, head_cy + 4), (head_cx + 2, head_cy + 4), 1)

        # Fierce eyes.
        for ey_side in [-1, 1]:
            eye_x = head_cx + ey_side * 2
            eye_y = head_cy
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["eye_dark"],
                             (eye_x - 1, eye_y, 3, 2))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["eye_white"],
                             (eye_x, eye_y, 2, 1))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["eye_amber"],
                             (eye_x + 1, eye_y, 1, 1))

        # Angry eyebrows.
        pygame.draw.line(surface, _NS_aurelion.PALETTE["hair_darkest"],
                         (head_cx - 4, head_cy - 2), (head_cx - 1, head_cy - 2), 1)
        pygame.draw.line(surface, _NS_aurelion.PALETTE["hair_darkest"],
                         (head_cx + 1, head_cy - 2), (head_cx + 4, head_cy - 2), 1)

        # GOLD LION CROWN (SIGNATURE).
        _NS_aurelion._draw_lion_crown(surface, head_cx, head_cy, facing, phase)

    def _draw_lion_crown(surface, cx, cy, facing, phase):
        """Ornate golden crown with lion motif and red gems."""
        # Crown base band.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 7, cy - 3), (cx - 7, cy - 3),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_darkest"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 7, cy - 4), (cx - 7, cy - 4),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5),
            (cx + 6, cy - 4), (cx - 6, cy - 4),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 5, cy - 4), (cx - 5, cy - 4),
        ])
        pygame.draw.line(surface, _NS_aurelion.PALETTE["gold_light"],
                         (cx - 4, cy - 5), (cx + 4, cy - 5), 1)

        # 5 CROWN SPIKES (like actual royal crown - varied heights).
        for i, (off_x, height) in enumerate([
            (-6, 4), (-3, 7), (0, 10), (3, 7), (6, 4),
        ]):
            pulse = math.sin(phase * 1.5 + i * 0.4) * 0.5 + 0.5
            spike_x = cx + off_x
            spike_base_y = cy - 5
            spike_tip_y = spike_base_y - height

            # Shadow.
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 1 + 1, spike_base_y + 1),
                (spike_x + 1 + 1, spike_base_y + 1),
            ])
            # Gold spike.
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["gold_mid"], [
                (spike_x, spike_tip_y),
                (spike_x, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                                  (spike_x, spike_tip_y),
                                  (spike_x - 1, spike_base_y), 1)
            # Red gem on tip (for the 3 middle spikes).
            if abs(off_x) <= 3:
                for gr in range(2, 0, -1):
                    alpha = _NS_aurelion._alpha(180 * pulse * (2 - gr) / 2)
                    _NS_aurelion._aacircle(surface,
                                            (*_NS_aurelion.PALETTE["gem_light"],
                                             alpha), (spike_x, spike_tip_y), gr)
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_dark"],
                                 (spike_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_shine"],
                                 (spike_x, spike_tip_y, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                                 (spike_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_bright"],
                                 (spike_x, spike_tip_y, 1, 1))

        # Red gems along band.
        for gem_off_x in (-4, 0, 4):
            gx = cx + gem_off_x
            gy = cy - 5
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_dark"],
                             (gx, gy, 2, 1))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_mid"],
                             (gx, gy, 1, 1))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_shine"],
                             (gx, gy, 1, 1))

    def _draw_shield_arm(surface, cx, cy, facing, phase, action):
        """Back arm holding lion shield."""
        shoulder_x = cx - facing * 12
        shoulder_y = cy - 6

        # Arm position.
        if action == "command":
            # Shield out.
            elbow_x = shoulder_x - facing * 4
            elbow_y = shoulder_y + 4
            hand_x = shoulder_x - facing * 8
            hand_y = shoulder_y + 8
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x - facing * 3
            elbow_y = shoulder_y + 6 + int(sway)
            hand_x = shoulder_x - facing * 6
            hand_y = shoulder_y + 10

        # Upper arm (gold armor).
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 6)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Elbow gold cap.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (elbow_x, elbow_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (elbow_x, elbow_y - 1, 1, 1))
        # Forearm (skin then gauntlet).
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        # Gauntlet at hand.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (hand_x, hand_y), 4)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (hand_x, hand_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_light"],
                         (hand_x, hand_y, 1, 1))

        # LION SHIELD (round with lion emblem).
        _NS_aurelion._draw_lion_shield(surface, hand_x - facing * 6, hand_y + 2,
                                         facing, phase)

    def _draw_lion_shield(surface, sx, sy, facing, phase):
        """Round gold shield with lion emblem head."""
        shield_r = 11

        # Shadow.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["shadow_deep"],
                                (sx + 2, sy + 2), shield_r)
        # Outer rim (dark gold).
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (sx, sy), shield_r)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (sx, sy), shield_r - 1)
        # Inner shield face.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (sx, sy), shield_r - 3)

        # Outer decorative ring (darker).
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (sx, sy), shield_r - 3, 1)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_light"],
                                (sx, sy), shield_r - 4, 1)

        # Small studs around rim.
        for i in range(8):
            a = i * math.pi / 4 + phase * 0.2
            stud_x = sx + int(math.cos(a) * (shield_r - 2))
            stud_y = sy + int(math.sin(a) * (shield_r - 2))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_light"],
                             (stud_x, stud_y, 1, 1))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                             (stud_x, stud_y, 1, 1))

        # LION HEAD EMBLEM in center.
        # Mane (outer circle darker).
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (sx, sy), 5)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (sx, sy), 4)
        # Mane rays around head.
        for i in range(8):
            a = i * math.pi / 4
            m_x = sx + int(math.cos(a) * 5)
            m_y = sy + int(math.sin(a) * 5)
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_light"],
                             (m_x, m_y, 1, 1))
        # Lion face center.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (sx, sy), 2)
        # Eyes (dark).
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_darkest"],
                         (sx - 1, sy, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_darkest"],
                         (sx + 1, sy, 1, 1))
        # Nose.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_darkest"],
                         (sx, sy + 1, 1, 1))
        # Bright shine.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (sx - 4, sy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_bright"],
                         (sx - 4, sy - 4, 1, 1))

        # Red gem at top of shield.
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_dark"],
                         (sx - 1, sy - shield_r + 1, 2, 2))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_mid"],
                         (sx, sy - shield_r + 1, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_shine"],
                         (sx, sy - shield_r + 1, 1, 1))

    def _draw_spear_arm(surface, cx, cy, facing, phase, action, progress):
        """Front arm holding the royal spear with lion head + banner."""
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 6

        if action == "attack":
            # Spear thrust forward.
            elbow_x = shoulder_x + facing * 6
            elbow_y = shoulder_y + 2
            hand_x = shoulder_x + facing * 14
            hand_y = shoulder_y + 4
            spear_angle = 0 if facing > 0 else math.pi
        elif action == "rush":
            # Spear forward.
            elbow_x = shoulder_x + facing * 7
            elbow_y = shoulder_y
            hand_x = shoulder_x + facing * 15
            hand_y = shoulder_y + 2
            spear_angle = 0.1 if facing > 0 else math.pi - 0.1
        elif action == "slash":
            # Spear swing angle.
            angle = -math.pi / 4 + progress * math.pi * 0.6
            elbow_x = shoulder_x + facing * int(math.cos(angle) * 6)
            elbow_y = shoulder_y + int(math.sin(angle) * 6)
            hand_x = shoulder_x + facing * int(math.cos(angle) * 14)
            hand_y = shoulder_y + int(math.sin(angle) * 14)
            spear_angle = angle
        elif action in ("command", "summon"):
            # Raise spear high.
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y - 8
            hand_x = shoulder_x + facing * 6
            hand_y = shoulder_y - 18
            spear_angle = -math.pi / 2 + 0.1
        else:
            # Idle - spear vertical.
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x + facing * 5
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x + facing * 10
            hand_y = shoulder_y + 4 + int(sway)
            spear_angle = -math.pi / 2 + 0.1

        # Shadow.
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 6)
        # Upper arm (gold).
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Elbow.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (elbow_x, elbow_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (elbow_x, elbow_y), 2)
        # Forearm (skin).
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        # Gauntlet at hand.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (hand_x, hand_y), 4)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (hand_x, hand_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (hand_x, hand_y - 1, 1, 1))

        # Draw royal spear.
        _NS_aurelion._draw_royal_spear(surface, hand_x, hand_y, spear_angle,
                                         facing, phase)

    def _draw_royal_spear(surface, hx, hy, angle, facing, phase):
        """Gold spear with lion head + banner flag."""
        length = 44
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        top_x = hx + int(dx * length)
        top_y = hy + int(dy * length)
        bot_x = hx - int(dx * 12)
        bot_y = hy - int(dy * 12)

        # Shadow.
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["shadow_deep"],
                              (bot_x + 2, bot_y + 2), (top_x + 2, top_y + 2), 4)
        # Spear shaft (gold).
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_darkest"],
                              (bot_x, bot_y), (top_x, top_y), 4)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                              (bot_x, bot_y), (top_x, top_y), 3)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_mid"],
                              (bot_x, bot_y), (top_x, top_y), 1)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                              (bot_x, bot_y - 1), (top_x, top_y - 1), 1)

        # Decorative rings.
        for t_ring in (0.3, 0.6):
            rx = int(bot_x + (top_x - bot_x) * t_ring)
            ry = int(bot_y + (top_y - bot_y) * t_ring)
            perp = angle + math.pi / 2
            r_a = (rx + int(math.cos(perp) * 3), ry + int(math.sin(perp) * 3))
            r_b = (rx - int(math.cos(perp) * 3), ry - int(math.sin(perp) * 3))
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                                  r_a, r_b, 2)
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                                  r_a, r_b, 1)

        # SPEAR TIP (elongated blade).
        perp = angle + math.pi / 2
        blade_tip = (top_x + int(dx * 14), top_y + int(dy * 14))
        blade_mid = (top_x + int(dx * 5), top_y + int(dy * 5))
        blade_a = (blade_mid[0] + int(math.cos(perp) * 3),
                   blade_mid[1] + int(math.sin(perp) * 3))
        blade_b = (blade_mid[0] - int(math.cos(perp) * 3),
                   blade_mid[1] - int(math.sin(perp) * 3))

        # Shadow.
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"], [
            (blade_tip[0] + 2, blade_tip[1] + 2),
            (blade_a[0] + 2, blade_a[1] + 2),
            (top_x + 2, top_y + 2),
            (blade_b[0] + 2, blade_b[1] + 2),
        ])
        # Blade (steel + gold trim).
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["steel_dark"], [
            blade_tip, blade_a, (top_x, top_y), blade_b,
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["steel_mid"], [
            blade_tip,
            (int((blade_tip[0] + blade_a[0]) / 2),
             int((blade_tip[1] + blade_a[1]) / 2)),
            (top_x, top_y),
            (int((blade_tip[0] + blade_b[0]) / 2),
             int((blade_tip[1] + blade_b[1]) / 2)),
        ])
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["steel_light"],
                              blade_tip, (top_x, top_y), 1)
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["white"],
                         (blade_tip[0], blade_tip[1], 1, 1))

        # LION HEAD at base of blade (khas Minsitthar).
        lion_x = top_x - int(dx * 2)
        lion_y = top_y - int(dy * 2)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                (lion_x, lion_y), 4)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (lion_x, lion_y), 3)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_mid"],
                                (lion_x, lion_y), 2)
        # Mane rays.
        for i in range(6):
            a = i * math.pi / 3
            m_x = lion_x + int(math.cos(a) * 3)
            m_y = lion_y + int(math.sin(a) * 3)
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_light"],
                             (m_x, m_y, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_bright"],
                         (lion_x, lion_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_shine"],
                         (lion_x, lion_y, 1, 1))

        # RED BANNER/FLAG hanging from spear.
        # Banner attached below lion head.
        banner_start = (top_x - int(dx * 4), top_y - int(dy * 4))
        banner_sway = math.sin(phase * 0.7) * 2

        banner_end_x = banner_start[0] - int(dx * 10) - int(banner_sway * facing)
        banner_end_y = banner_start[1] - int(dy * 10)

        banner_shape = [
            banner_start,
            (banner_start[0] - int(perp[0] if isinstance(perp, tuple) else math.cos(perp)) * 6
             if False else banner_start[0] + int(math.cos(perp) * 6),
             banner_start[1] + int(math.sin(perp) * 6)),
            (banner_end_x + int(math.cos(perp) * 6),
             banner_end_y + int(math.sin(perp) * 6)),
            (banner_end_x - int(math.cos(perp) * 2 * facing),
             banner_end_y - int(math.sin(perp) * 2)),
            banner_start,
        ]
        # Simpler banner: rectangular flag below spear.
        b_top = (top_x - int(dx * 4), top_y - int(dy * 4))
        b_top2 = (top_x - int(dx * 4) + int(math.cos(perp) * 8),
                  top_y - int(dy * 4) + int(math.sin(perp) * 8))
        b_bot2 = (b_top2[0] - int(dx * 12) + int(banner_sway),
                  b_top2[1] - int(dy * 12))
        b_bot = (b_top[0] - int(dx * 12) + int(banner_sway),
                 b_top[1] - int(dy * 12))

        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"], [
            (b_top[0] + 1, b_top[1] + 1),
            (b_top2[0] + 1, b_top2[1] + 1),
            (b_bot2[0] + 1, b_bot2[1] + 1),
            (b_bot[0] + 1, b_bot[1] + 1),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_darkest"],
                            [b_top, b_top2, b_bot2, b_bot])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_dark"], [
            (int((b_top[0] + b_top2[0]) / 2) - int(dx * 0.5),
             int((b_top[1] + b_top2[1]) / 2)),
            b_top2,
            b_bot2,
            (int((b_bot[0] + b_bot2[0]) / 2) - int(dx * 0.5),
             int((b_bot[1] + b_bot2[1]) / 2)),
        ])
        _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_mid"], [
            b_top,
            (int((b_top[0] * 2 + b_top2[0]) / 3),
             int((b_top[1] * 2 + b_top2[1]) / 3)),
            (int((b_bot[0] * 2 + b_bot2[0]) / 3),
             int((b_bot[1] * 2 + b_bot2[1]) / 3)),
            b_bot,
        ])

        # Gold trim on banner top.
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                              b_top, b_top2, 2)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_mid"],
                              b_top, b_top2, 1)
        # Gold bottom trim.
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                              b_bot, b_bot2, 2)
        _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_mid"],
                              b_bot, b_bot2, 1)

        # Lion emblem in center of banner.
        banner_mid_x = int((b_top[0] + b_bot2[0]) / 2)
        banner_mid_y = int((b_top[1] + b_bot2[1]) / 2)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (banner_mid_x, banner_mid_y), 2)
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_light"],
                                (banner_mid_x, banner_mid_y), 1)

        # Spear bottom cap.
        _NS_aurelion._aacircle(surface, _NS_aurelion.PALETTE["gold_dark"],
                                (bot_x, bot_y), 2)
        pygame.draw.rect(surface, _NS_aurelion.PALETTE["gold_mid"],
                         (bot_x, bot_y, 1, 1))

    def _draw_spear_thrust(surface, cx, cy, facing, progress):
        """Gold energy thrust from spear."""
        if progress < 0.3 or progress > 0.8:
            return
        t = (progress - 0.3) / 0.5

        # Thrust trail.
        for i in range(6):
            trail_t = t - i * 0.06
            if trail_t < 0:
                continue
            spear_x = cx + facing * int(20 + trail_t * 20)
            spear_y = cy - 5
            alpha = _NS_aurelion._alpha(240 - i * 35)

            for r in range(5, 1, -1):
                a = _NS_aurelion._alpha(alpha * (5 - r) / 5)
                _NS_aurelion._aacircle(surface,
                                        (*_NS_aurelion.PALETTE["royal_dark"], a),
                                        (spear_x, spear_y), r)
            _NS_aurelion._aacircle(surface,
                                    (*_NS_aurelion.PALETTE["royal_mid"], alpha),
                                    (spear_x, spear_y), 3)
            _NS_aurelion._aacircle(surface,
                                    (*_NS_aurelion.PALETTE["royal_light"], alpha),
                                    (spear_x, spear_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_aurelion.PALETTE["royal_hot"], alpha),
                             (spear_x, spear_y, 1, 1))

    # ============================================================
    # ROYAL PARTICLES (float underneath)
    # ============================================================
    def _draw_royal_particles(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        # Gold pool below.
        pool = pygame.Surface((110, 28), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for r in range(22, 2, -2):
            alpha = _NS_aurelion._alpha((22 - r) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_aurelion.PALETTE["royal_darkest"], alpha),
                                    (55 - r, 14 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(13, 1, -1):
            alpha = _NS_aurelion._alpha((13 - r) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_aurelion.PALETTE["royal_mid"], alpha),
                                    (55 - r, 14 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 55, cy - 5))

        # Rising gold sparks.
        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 25 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 8 - int(t * 26)
            alpha = _NS_aurelion._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_aurelion._aacircle(surface,
                                    (*_NS_aurelion.PALETTE["royal_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_aurelion.PALETTE["royal_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_aurelion.PALETTE["royal_hot"], alpha),
                             (sx, sy - 2, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 34), pygame.SRCALPHA)
        for r in range(16, 0, -1):
            alpha = max(0, (16 - r) * 14)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 17 - r,
                                 140 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (30, 20, 5, 170), (5, 10, 150, 14))
        pygame.draw.ellipse(shadow, (140, 100, 20, 110), (12, 12, 136, 10))
        surface.blit(shadow, (x - 80, y - 17))

    def _draw_royal_aura(surface, x, y, phase):
        """LARGE royal gold aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.4) * 0.3 + 0.7
        aura = pygame.Surface((280, 240), pygame.SRCALPHA)
        for r in range(120, 5, -6):
            alpha = _NS_aurelion._alpha((120 - r) * 0.9 * pulse)
            if alpha > 0:
                _NS_aurelion._aacircle(aura,
                                        (*_NS_aurelion.PALETTE["royal_darkest"],
                                         alpha), (140, 120), r)
        for r in range(80, 5, -5):
            alpha = _NS_aurelion._alpha((80 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_aurelion._aacircle(aura,
                                        (*_NS_aurelion.PALETTE["royal_dark"],
                                         alpha), (140, 120), r)
        for r in range(50, 5, -4):
            alpha = _NS_aurelion._alpha((50 - r) * 1.5 * pulse)
            if alpha > 0:
                _NS_aurelion._aacircle(aura,
                                        (*_NS_aurelion.PALETTE["royal_mid"],
                                         alpha // 2), (140, 120), r)
        surface.blit(aura, (x - 140, y - 120))

        # Floating gold sparks + red sparks.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 55 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            if i % 4 == 0:
                # Red sparks (royal).
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_light"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["gem_shine"],
                                 (sx, sy, 1, 1))
            else:
                # Gold sparks.
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["royal_mid"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["royal_hot"],
                                 (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large ground rune circle (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_aurelion.PALETTE["rune_dark"], 200),
                            (5, 20, 190, 26), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_aurelion.PALETTE["royal_darkest"], 220),
                            (14, 22, 172, 22), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_aurelion.PALETTE["royal_dark"], 230),
                            (25, 24, 150, 18), 1)

        # Rune spikes.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 52)
            y1 = 33 + int(math.sin(angle) * 8)
            x2 = 100 + int(math.cos(angle) * 82)
            y2 = 33 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_aurelion.PALETTE["royal_light"], 220),
                             (x1, y1), (x2, y2), 1)

        # Star sparkles.
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sx = 100 + int(math.cos(angle) * 70)
            sy = 33 + int(math.sin(angle) * 10)
            pygame.draw.rect(ring, (*_NS_aurelion.PALETTE["royal_shine"], 220),
                             (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_aurelion.PALETTE["royal_hot"],
                                 _NS_aurelion._alpha(150 * pulse)),
                                (15, 14, 170, 38), 1)
        surface.blit(ring, (x - 100, y - 29))

    # ============================================================
    # SKILL Q: CALL OF COURAGE - speed aura + rush trails
    # ============================================================
    def _draw_call_courage_ground(surface, boss, x, y, timer, phase):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Blue circle underneath (speed buff).
        r = int(30 + math.sin(phase * 2) * 4)
        alpha = _NS_aurelion._alpha(200 * (1 - progress * 0.4))
        # Blue rings.
        pygame.draw.ellipse(surface,
                            (*_NS_aurelion.PALETTE["blue_mid"], alpha),
                            (x - r, y + 45 - r // 3,
                             r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface,
                            (*_NS_aurelion.PALETTE["blue_light"], alpha),
                            (x - r + 3, y + 45 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 1)
        # Sparkles around.
        for i in range(8):
            a = i * math.pi / 4 + phase * 0.5
            sx = x + int(math.cos(a) * r)
            sy = y + 45 + int(math.sin(a) * r * 0.4)
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["blue_light"],
                             (sx, sy, 1, 1))

    def _draw_call_courage_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # RED SPEAR STREAKS from behind boss (like referensi).
        for i in range(8):
            streak_t = (phase * 1.5 + i * 0.1) % 1.0
            streak_x = x - facing * (int(streak_t * 40))
            streak_y = y - 10 + int(math.sin(phase + i) * 5)
            alpha = _NS_aurelion._alpha(240 * (1 - streak_t))

            # Trailing red spear line.
            _NS_aurelion._aaline(surface,
                                  (*_NS_aurelion.PALETTE["cape_darkest"], alpha),
                                  (streak_x - facing * 8, streak_y),
                                  (streak_x, streak_y), 3)
            _NS_aurelion._aaline(surface,
                                  (*_NS_aurelion.PALETTE["cape_dark"], alpha),
                                  (streak_x - facing * 8, streak_y),
                                  (streak_x, streak_y), 2)
            _NS_aurelion._aaline(surface,
                                  (*_NS_aurelion.PALETTE["cape_mid"], alpha),
                                  (streak_x - facing * 8, streak_y),
                                  (streak_x, streak_y), 1)
            _NS_aurelion._aaline(surface,
                                  (*_NS_aurelion.PALETTE["cape_light"], alpha),
                                  (streak_x - facing * 6, streak_y),
                                  (streak_x, streak_y), 1)
            # Bright spear tip.
            pygame.draw.rect(surface,
                             (*_NS_aurelion.PALETTE["cape_shine"], alpha),
                             (streak_x, streak_y, 2, 1))

    # ============================================================
    # SKILL W: GUARDIAN ASSAULT - big gold slash arc
    # ============================================================
    def _draw_guardian_assault_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Prep charge at spear.
            hx = x + facing * 20
            hy = y - 8
            t = progress / 0.3
            cr = int(3 + t * 7)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_aurelion._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_aurelion._aacircle(surface,
                                        (*_NS_aurelion.PALETTE["royal_mid"],
                                         alpha), (hx, hy), r)
        else:
            # BIG CURVED GOLDEN SLASH in front.
            t = (progress - 0.3) / 0.7
            arc_intensity = math.sin(t * math.pi)

            # Multi-layer arc.
            for layer_i in range(3):
                for i in range(16):
                    a = -math.pi / 2.3 + (i / 15) * math.pi * 1.0
                    radius = 45 - layer_i * 6
                    ax = x + int(math.cos(a) * radius) * facing
                    ay = y - 6 + int(math.sin(a) * radius)
                    alpha = _NS_aurelion._alpha(240 * arc_intensity
                                                  - layer_i * 30)
                    if alpha <= 0:
                        continue
                    size = 6 - layer_i
                    _NS_aurelion._aacircle(surface,
                                            (*_NS_aurelion.PALETTE["royal_darkest"],
                                             alpha), (ax, ay), size + 1)
                    _NS_aurelion._aacircle(surface,
                                            (*_NS_aurelion.PALETTE["royal_dark"],
                                             alpha), (ax, ay), size)
                    _NS_aurelion._aacircle(surface,
                                            (*_NS_aurelion.PALETTE["royal_mid"],
                                             alpha), (ax, ay), max(1, size - 2))
                    _NS_aurelion._aacircle(surface,
                                            (*_NS_aurelion.PALETTE["royal_light"],
                                             alpha), (ax, ay), max(1, size - 4))
                    pygame.draw.rect(surface,
                                     (*_NS_aurelion.PALETTE["royal_hot"], alpha),
                                     (ax, ay, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_aurelion.PALETTE["royal_shine"], alpha),
                                     (ax, ay, 1, 1))

            # Extra bright sparkles along arc.
            for i in range(10):
                a = -math.pi / 2.3 + (i / 9) * math.pi * 1.0
                sx = x + int(math.cos(a) * 45) * facing
                sy = y - 6 + int(math.sin(a) * 45)
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["white"],
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: KING'S COMMAND - fan-shaped taunt area
    # ============================================================
    def _draw_kings_command_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.2:
            return

        t = (progress - 0.2) / 0.8

        # FAN-SHAPED area in front of boss.
        fan_radius = int(80 * min(1.0, t * 2))
        if fan_radius < 5:
            return

        # Fan spans about 100 degrees.
        num_slices = 12
        alpha = _NS_aurelion._alpha(200 * (1 - t * 0.3))

        # Draw fan by drawing multiple triangles.
        for i in range(num_slices):
            angle_start = -math.pi / 3.5 + i * (math.pi / 3.5 * 2) / num_slices
            angle_end = -math.pi / 3.5 + (i + 1) * (math.pi / 3.5 * 2) / num_slices

            # Base gold color.
            layer_alpha = alpha - i * 3
            if layer_alpha <= 0:
                continue
            p1 = (x + facing * 5, y + 45)
            p2 = (x + int(math.cos(angle_start) * fan_radius) * facing,
                  y + 45 + int(math.sin(angle_start) * fan_radius * 0.5))
            p3 = (x + int(math.cos(angle_end) * fan_radius) * facing,
                  y + 45 + int(math.sin(angle_end) * fan_radius * 0.5))
            _NS_aurelion._poly(surface,
                                (*_NS_aurelion.PALETTE["royal_darkest"], layer_alpha),
                                [p1, p2, p3])

        # Inner brighter layer.
        for i in range(num_slices):
            angle_start = -math.pi / 3.5 + i * (math.pi / 3.5 * 2) / num_slices
            angle_end = -math.pi / 3.5 + (i + 1) * (math.pi / 3.5 * 2) / num_slices
            layer_alpha = alpha // 2
            p1 = (x + facing * 5, y + 45)
            p2 = (x + int(math.cos(angle_start) * fan_radius * 0.8) * facing,
                  y + 45 + int(math.sin(angle_start) * fan_radius * 0.8 * 0.5))
            p3 = (x + int(math.cos(angle_end) * fan_radius * 0.8) * facing,
                  y + 45 + int(math.sin(angle_end) * fan_radius * 0.8 * 0.5))
            _NS_aurelion._poly(surface,
                                (*_NS_aurelion.PALETTE["royal_dark"], layer_alpha),
                                [p1, p2, p3])

        # Fan edge line (bright).
        edge_pts = []
        for i in range(num_slices + 1):
            angle = -math.pi / 3.5 + i * (math.pi / 3.5 * 2) / num_slices
            ex = x + int(math.cos(angle) * fan_radius) * facing
            ey = y + 45 + int(math.sin(angle) * fan_radius * 0.5)
            edge_pts.append((ex, ey))
        for i in range(len(edge_pts) - 1):
            _NS_aurelion._aaline(surface,
                                  (*_NS_aurelion.PALETTE["royal_light"], 240),
                                  edge_pts[i], edge_pts[i + 1], 2)

        # Central lion emblem in fan.
        center_x = x + facing * (fan_radius // 2 + 10)
        center_y = y + 45
        _NS_aurelion._aacircle(surface,
                                (*_NS_aurelion.PALETTE["royal_hot"], 240),
                                (center_x, center_y), 8)
        _NS_aurelion._aacircle(surface,
                                (*_NS_aurelion.PALETTE["royal_shine"], 240),
                                (center_x, center_y), 5)
        # Mane rays.
        for i in range(6):
            a = i * math.pi / 3
            rx = center_x + int(math.cos(a) * 8)
            ry = center_y + int(math.sin(a) * 8)
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["white"],
                             (rx, ry, 1, 1))

    def _draw_kings_command_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Small shield emblems flying out (taunt indicator).
        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            for i in range(6):
                spawn_t = (phase * 1.5 + i * 0.15) % 1.0
                fan_angle = -math.pi / 3.5 + (i / 5) * (math.pi / 3.5 * 2)
                fly_dist = int(spawn_t * 60)
                ex = x + int(math.cos(fan_angle) * (30 + fly_dist)) * facing
                ey = y - 5 + int(math.sin(fan_angle) * (30 + fly_dist) * 0.5)
                alpha = _NS_aurelion._alpha(240 * (1 - spawn_t))

                # Small crown/shield icon.
                _NS_aurelion._aacircle(surface,
                                        (*_NS_aurelion.PALETTE["royal_dark"], alpha),
                                        (ex, ey), 4)
                _NS_aurelion._aacircle(surface,
                                        (*_NS_aurelion.PALETTE["royal_mid"], alpha),
                                        (ex, ey), 3)
                _NS_aurelion._aacircle(surface,
                                        (*_NS_aurelion.PALETTE["royal_light"], alpha),
                                        (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_aurelion.PALETTE["royal_shine"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_aurelion.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # SKILL R: KING'S SUMMONON - wall of spears surrounding area
    # ============================================================
    def _draw_kings_summonon_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aurelion._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Big circular area at target.
        r = int(90 * min(1.0, progress * 2))
        if r < 5:
            return

        alpha = _NS_aurelion._alpha(180 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface,
                            (*_NS_aurelion.PALETTE["royal_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_aurelion.PALETTE["royal_dark"], alpha),
                            (tx - r + 4, ty - r // 3 + 2,
                             r * 2 - 8, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface,
                            (*_NS_aurelion.PALETTE["royal_mid"], alpha // 2),
                            (tx - r + 10, ty - r // 3 + 4,
                             r * 2 - 20, r * 2 // 3 - 8))

        # Runic border.
        pygame.draw.ellipse(surface,
                            (*_NS_aurelion.PALETTE["royal_light"], 240),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)

    def _draw_kings_summonon_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aurelion._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(90 * min(1.0, progress * 2))
        if r < 5:
            return

        # WALL OF SPEARS around perimeter (signature ULT!).
        num_spears = 24
        for i in range(num_spears):
            angle = i * math.pi * 2 / num_spears
            spawn_delay = (i % 4) * 0.05
            spear_progress = min(1.0, max(0.0, progress * 3 - spawn_delay))

            if spear_progress < 0.05:
                continue

            spear_x = tx + int(math.cos(angle) * r)
            spear_y_base = ty + int(math.sin(angle) * r * 0.5)

            # Spear rises from ground.
            max_h = 40
            spear_h = int(spear_progress * max_h)
            if spear_progress > 0.85:
                fade = 1 - (spear_progress - 0.85) / 0.15
                spear_h = int(spear_h * (0.7 + fade * 0.3))

            if spear_h < 3:
                continue

            spear_top_y = spear_y_base - spear_h

            # Spear shaft (gold).
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["shadow_deep"],
                                  (spear_x + 1, spear_top_y + 1),
                                  (spear_x + 1, spear_y_base + 1), 3)
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_darkest"],
                                  (spear_x, spear_top_y),
                                  (spear_x, spear_y_base), 3)
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_dark"],
                                  (spear_x, spear_top_y),
                                  (spear_x, spear_y_base), 2)
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["gold_light"],
                                  (spear_x - 1, spear_top_y),
                                  (spear_x - 1, spear_y_base), 1)

            # Spear tip (steel blade).
            tip_shape = [
                (spear_x, spear_top_y - 8),
                (spear_x + 3, spear_top_y - 2),
                (spear_x, spear_top_y + 1),
                (spear_x - 3, spear_top_y - 2),
            ]
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in tip_shape])
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["steel_dark"], tip_shape)
            _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["steel_mid"], [
                (spear_x, spear_top_y - 8),
                (spear_x + 2, spear_top_y - 2),
                (spear_x, spear_top_y),
                (spear_x - 2, spear_top_y - 2),
            ])
            _NS_aurelion._aaline(surface, _NS_aurelion.PALETTE["steel_light"],
                                  (spear_x, spear_top_y - 8),
                                  (spear_x, spear_top_y), 1)
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["white"],
                             (spear_x, spear_top_y - 8, 1, 1))

            # Small red banner on some spears (every 3rd).
            if i % 3 == 0:
                sway = math.sin(phase * 0.5 + i) * 1
                banner_x = spear_x + 1
                _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_darkest"], [
                    (banner_x, spear_top_y - 3),
                    (banner_x + 4 + int(sway), spear_top_y - 2),
                    (banner_x + 4 + int(sway), spear_top_y + 4),
                    (banner_x, spear_top_y + 3),
                ])
                _NS_aurelion._poly(surface, _NS_aurelion.PALETTE["cape_dark"], [
                    (banner_x + 1, spear_top_y - 2),
                    (banner_x + 3 + int(sway), spear_top_y - 1),
                    (banner_x + 3 + int(sway), spear_top_y + 3),
                    (banner_x + 1, spear_top_y + 2),
                ])
                pygame.draw.rect(surface, _NS_aurelion.PALETTE["cape_mid"],
                                 (banner_x + 2, spear_top_y, 1, 1))

            # Glow around spear tip.
            for gr in range(3, 0, -1):
                alpha = _NS_aurelion._alpha(120 * (3 - gr) / 3)
                _NS_aurelion._aacircle(surface,
                                        (*_NS_aurelion.PALETTE["royal_light"],
                                         alpha), (spear_x, spear_top_y - 8), gr)

        # Central rising energy at ULT center.
        if progress > 0.3 and progress < 0.9:
            rise_t = (phase * 1.5) % 1.0
            center_ray_h = int(60 * math.sin(rise_t * math.pi))
            for layer_i, (width, color) in enumerate([
                (14, _NS_aurelion.PALETTE["royal_darkest"]),
                (10, _NS_aurelion.PALETTE["royal_dark"]),
                (7, _NS_aurelion.PALETTE["royal_mid"]),
                (4, _NS_aurelion.PALETTE["royal_light"]),
                (2, _NS_aurelion.PALETTE["royal_shine"]),
            ]):
                alpha = _NS_aurelion._alpha(220)
                pygame.draw.rect(surface, (*color, alpha),
                                 (tx - width // 2, ty - center_ray_h,
                                  width, center_ray_h))
            pygame.draw.rect(surface, _NS_aurelion.PALETTE["white"],
                             (tx, ty - center_ray_h, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_cryssalia(surface, boss, x, y):
    """Entry point cryssalia."""
    return _NS_cryssalia.draw_cryssalia(surface, boss, x, y)


def draw_kaelthar(surface, boss, x, y):
    """Entry point kaelthar."""
    return _NS_kaelthar.draw_kaelthar(surface, boss, x, y)


def draw_morkhaera(surface, boss, x, y):
    """Entry point morkhaera."""
    return _NS_morkhaera.draw_morkhaera(surface, boss, x, y)


def draw_aurelion(surface, boss, x, y):
    """Entry point aurelion."""
    return _NS_aurelion.draw_aurelion(surface, boss, x, y)
