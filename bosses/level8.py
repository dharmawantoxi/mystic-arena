"""
bosses/level8.py - Semua boss Level 8

Gabungan dari 4 file terpisah:
  - xirthalis            (mini boss)
  - vhyssarion           (mini boss)
  - vaerith              (mini boss)
  - vhorethzir           (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True



# ====================================================================
# XIRTHALIS
# ====================================================================
class _NS_xirthalis:
    """Namespace xirthalis - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Teal/cyan carapace (main body)
        "teal_darkest": (5, 20, 25),
        "teal_dark": (15, 55, 65),
        "teal_mid": (30, 115, 125),
        "teal_light": (70, 200, 210),
        "teal_hot": (140, 255, 245),
        "teal_shine": (220, 255, 250),

        # Crimson accents (claws, stripes)
        "crimson_darkest": (30, 5, 10),
        "crimson_dark": (95, 15, 25),
        "crimson_mid": (185, 35, 45),
        "crimson_light": (245, 80, 75),
        "crimson_shine": (255, 180, 160),

        # Purple/magenta undertone (belly, joints)
        "purple_darkest": (18, 8, 30),
        "purple_dark": (50, 25, 75),
        "purple_mid": (100, 50, 140),
        "purple_light": (170, 100, 220),
        "purple_hot": (220, 150, 255),

        # Crystal wings (translucent blue)
        "wing_darkest": (10, 25, 55),
        "wing_dark": (30, 70, 130),
        "wing_mid": (70, 140, 220),
        "wing_light": (140, 210, 255),
        "wing_shine": (220, 245, 255),

        # Cyan magic (skills)
        "arcane_darkest": (5, 30, 50),
        "arcane_dark": (20, 90, 130),
        "arcane_mid": (60, 180, 230),
        "arcane_light": (150, 240, 255),
        "arcane_hot": (220, 255, 255),

        # Time magic (R skill - deep blue-violet)
        "time_darkest": (8, 10, 40),
        "time_dark": (30, 40, 110),
        "time_mid": (70, 100, 200),
        "time_light": (150, 200, 255),

        # Web/swarm (purple mesh)
        "web_dark": (60, 40, 90),
        "web_mid": (140, 110, 180),
        "web_light": (230, 210, 250),

        # Small spider swarm
        "spider_dark": (30, 15, 40),
        "spider_body": (85, 40, 100),
        "spider_eye": (240, 80, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xirthalis._clamp(color)
        if _NS_xirthalis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_xirthalis._clamp(color)
        if _NS_xirthalis.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xirthalis._clamp(color), points)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xirthalis(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xirthalis._detect_moving(boss)
        _NS_xirthalis._update_xir_attack_anim(boss)
        attacking = (
            getattr(boss, "_xir_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_xirthalis._draw_arcane_aura(surface, x, y, pulse)
        _NS_xirthalis._draw_ground_ring(surface, x, y + 34, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_xirthalis._draw_swarm_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xirthalis._draw_timelapse_ground(surface, boss, x, y, skill_timer, pulse)

        # Q Shukuchi affects body render (afterimages / invis).
        shukuchi = active_skill == "q"

        # Body.
        if shukuchi:
            _NS_xirthalis._draw_shukuchi_afterimages(surface, boss, x, y, skill_timer)
        if attacking:
            _NS_xirthalis._draw_xir_attack(surface, boss, x, y, invis=shukuchi)
        elif moving:
            _NS_xirthalis._draw_xir_walk(surface, boss, x, y, invis=shukuchi)
        else:
            _NS_xirthalis._draw_xir_idle(surface, boss, x, y, invis=shukuchi)

        # Foreground FX.
        if active_skill == "q":
            _NS_xirthalis._draw_shukuchi_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xirthalis._draw_swarm_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xirthalis._draw_geminate_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xirthalis._draw_timelapse_foreground(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_xir_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 36)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xir_previous_timer", 0))
        active = bool(getattr(boss, "_xir_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._xir_attack_active = True
            boss._xir_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xir_attack_frame = int(
                getattr(boss, "_xir_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._xir_attack_active = False
            boss._xir_attack_frame = 0
            active = False

        boss._xir_previous_timer = timer
        boss._xir_attack_progress = (
            min(1.0, getattr(boss, "_xir_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_xir_last_x"):
            boss._xir_last_x = boss.x
            boss._xir_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xir_last_x)
        dy = abs(boss.y - boss._xir_last_y)
        boss._xir_last_x = boss.x
        boss._xir_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_xir_idle(surface, boss, x, y, invis=False):
        # Hover with faster oscillation (insectoid hovering).
        bob = int(math.sin(boss.pulse * 1.2) * 3)
        _NS_xirthalis._draw_shadow(surface, x, y + 44, invis=invis)
        _NS_xirthalis._draw_hover_dust(surface, x, y + 30, boss.pulse)
        _NS_xirthalis._draw_xir_body(surface, x, y + bob,
                        boss.direction, boss.pulse * 1.5, "idle",
                        invis=invis)


    def _draw_xir_walk(surface, boss, x, y, invis=False):
        phase = boss.pulse * 2.5
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_xirthalis._draw_shadow(surface, x + sway, y + 44, invis=invis)
        _NS_xirthalis._draw_hover_dust(surface, x + sway, y + 30, phase, trail=True,
                          facing=boss.direction)
        _NS_xirthalis._draw_xir_body(surface, x + sway, y + bob,
                        boss.direction, phase, "walk", invis=invis)


    def _draw_xir_attack(surface, boss, x, y, invis=False):
        progress = getattr(boss, "_xir_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Quick lunge (fast, snappy).
        lunge = int(math.sin(progress * math.pi) * 7) * boss.direction
        lift = int(math.sin(progress * math.pi) * 2)
        _NS_xirthalis._draw_shadow(surface, x + lunge, y + 44, invis=invis)
        _NS_xirthalis._draw_hover_dust(surface, x + lunge, y + 30, boss.pulse * 1.5,
                          intense=True)
        _NS_xirthalis._draw_xir_body(surface, x + lunge, y - lift,
                        boss.direction, boss.pulse * 2, "attack",
                        progress, invis=invis)
        _NS_xirthalis._draw_melee_slash_fx(surface, boss, x + lunge, y - lift, progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_xir_body(surface, cx, cy, facing, phase, action,
                        attack_progress=0, invis=False):
        """Draw insectoid body: wings behind, abdomen, thorax, head, 6 legs, claws."""
        # If invisible during Shukuchi, apply transparency effect (drawn to surface).
        if invis:
            # Draw very faint outline only.
            _NS_xirthalis._draw_invis_silhouette(surface, cx, cy, facing, phase)
            return

        # Wings FIRST (behind body).
        _NS_xirthalis._draw_crystal_wings(surface, cx, cy - 8, facing, phase, action,
                             attack_progress)

        # Back legs.
        _NS_xirthalis._draw_insect_legs(surface, cx, cy, facing, phase, action,
                           attack_progress, back_layer=True)

        # Abdomen (tapered rear).
        _NS_xirthalis._draw_xir_abdomen(surface, cx - facing * 10, cy + 4, facing, phase)

        # Thorax.
        _NS_xirthalis._draw_xir_thorax(surface, cx, cy, facing, phase)

        # Head with mandible/eye.
        head_lunge = 0
        if action == "attack":
            head_lunge = int(math.sin(attack_progress * math.pi) * 3) * facing
        _NS_xirthalis._draw_xir_head(surface, cx + facing * 9 + head_lunge, cy + 1,
                        facing, phase, action, attack_progress)

        # Front claws (SIGNATURE - crimson pincers).
        _NS_xirthalis._draw_front_claws(surface, cx + facing * 6, cy + 2, facing, phase,
                           action, attack_progress)

        # Front legs (over body).
        _NS_xirthalis._draw_insect_legs(surface, cx, cy, facing, phase, action,
                           attack_progress, back_layer=False)


    def _draw_crystal_wings(surface, cx, cy, facing, phase, action,
                             attack_progress):
        """Iridescent crystal wings (dragonfly-like, translucent blue)."""
        # Wing beat: fast when attacking/moving, slow idle.
        if action == "attack":
            beat = math.sin(phase * 3 + attack_progress * 6) * 3
        else:
            beat = math.sin(phase * 2) * 2

        # Draw 2 wings per side (upper + lower), 4 total wings.
        for side in (-1, 1):
            for wing_i, (angle_off, size_mult) in enumerate([
                (0.0, 1.0),   # upper
                (0.35, 0.85),  # lower (slightly angled down)
            ]):
                # Wing base attaches at thorax top.
                base_x = cx + side * 3
                base_y = cy + wing_i * 3

                # Wing points: elongated teardrop shape.
                wing_angle = math.pi * (0.85 + angle_off) * side + math.radians(beat)
                length = int(22 * size_mult)
                width = int(9 * size_mult)

                tip_x = base_x + int(math.cos(wing_angle) * length)
                tip_y = base_y - int(math.sin(math.pi * 0.5 - abs(wing_angle - math.pi * 0.5)) * length * 0.3)
                if side < 0:
                    tip_x = base_x - int(abs(math.cos(wing_angle)) * length)
                else:
                    tip_x = base_x + int(abs(math.cos(wing_angle)) * length)
                tip_y = base_y - int(length * 0.35) + int(beat)

                # Wing shape (elongated leaf/blade).
                wing_shape = [
                    (base_x, base_y),
                    (base_x + side * 3, base_y - 3),
                    (base_x + side * int(length * 0.4),
                     base_y - int(length * 0.35) + int(beat)),
                    (tip_x, tip_y),
                    (base_x + side * int(length * 0.6),
                     base_y - int(length * 0.15) + int(beat * 0.7)),
                    (base_x + side * int(length * 0.3), base_y + 1),
                ]

                # Translucent wing (draw to alpha surface).
                wing_surf = pygame.Surface((80, 60), pygame.SRCALPHA)
                local_shape = [(p[0] - (base_x - 40), p[1] - (base_y - 30))
                               for p in wing_shape]

                # Layered translucent fill.
                _NS_xirthalis._poly(wing_surf, (*_NS_xirthalis.PALETTE["wing_darkest"], 110), local_shape)
                inner_shape = []
                for i, p in enumerate(local_shape):
                    # Pull each point toward wing center.
                    center_x = sum(pp[0] for pp in local_shape) / len(local_shape)
                    center_y = sum(pp[1] for pp in local_shape) / len(local_shape)
                    inner_shape.append(
                        (int(p[0] * 0.75 + center_x * 0.25),
                         int(p[1] * 0.75 + center_y * 0.25))
                    )
                _NS_xirthalis._poly(wing_surf, (*_NS_xirthalis.PALETTE["wing_dark"], 130), inner_shape)

                # Crystal veins (radial from base).
                vein_start = local_shape[0]
                for target_i in (2, 3, 4):
                    vein_end = local_shape[target_i]
                    pygame.draw.line(wing_surf,
                                     (*_NS_xirthalis.PALETTE["wing_mid"], 200),
                                     vein_start, vein_end, 1)

                # Wing edge highlight (bright cyan).
                for i in range(len(local_shape)):
                    p1 = local_shape[i]
                    p2 = local_shape[(i + 1) % len(local_shape)]
                    pygame.draw.line(wing_surf,
                                     (*_NS_xirthalis.PALETTE["wing_light"], 180), p1, p2, 1)

                # Sparkle points at wing tip.
                pygame.draw.rect(wing_surf, (*_NS_xirthalis.PALETTE["wing_shine"], 240),
                                 (local_shape[3][0], local_shape[3][1], 1, 1))

                surface.blit(wing_surf, (base_x - 40, base_y - 30))


    def _draw_xir_abdomen(surface, cx, cy, facing, phase):
        """Tapered rear body — smaller than Broodmother, more insect-like."""
        breath = math.sin(phase * 0.8) * 1

        # Abdomen shape (oval, tapering to back).
        abdomen = [
            (cx - 12, cy),
            (cx - 14, cy - 4),
            (cx - 10, cy - 8),
            (cx - 4, cy - 9),
            (cx + 2, cy - 8),
            (cx + 6, cy - 5),
            (cx + 7, cy),
            (cx + 6, cy + 5),
            (cx + 2, cy + 7),
            (cx - 4, cy + 8),
            (cx - 10, cy + 6),
            (cx - 13, cy + 3),
        ]
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in abdomen])
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["teal_darkest"], abdomen)

        # Purple underside (bottom half).
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["purple_dark"], [
            (cx - 12, cy),
            (cx - 10, cy + 6),
            (cx - 4, cy + 8),
            (cx + 2, cy + 7),
            (cx + 6, cy + 5),
            (cx + 7, cy),
        ])
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["purple_mid"], [
            (cx - 10, cy + 1),
            (cx - 8, cy + 5),
            (cx - 4, cy + 7),
            (cx + 2, cy + 6),
            (cx + 5, cy + 4),
            (cx + 6, cy + 1),
        ])

        # Teal carapace top (segmented plates).
        for plate in [
            # Main top plate
            [(cx - 10, cy - 6), (cx - 4, cy - 8), (cx + 2, cy - 7),
             (cx + 5, cy - 4), (cx + 3, cy - 2), (cx - 8, cy - 2)],
            # Side plate
            [(cx - 12, cy - 3), (cx - 10, cy - 5), (cx - 8, cy - 2),
             (cx - 11, cy + 1)],
        ]:
            _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["teal_dark"], plate)

        # Bright teal highlight.
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["teal_mid"], [
            (cx - 8, cy - 6),
            (cx - 3, cy - 7),
            (cx + 1, cy - 6),
            (cx + 2, cy - 4),
            (cx - 6, cy - 4),
        ])

        # Crimson stripe accent (running along back).
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_dark"],
                         (cx - 8, cy - 5), (cx + 2, cy - 6), 2)
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_mid"],
                         (cx - 7, cy - 5), (cx + 1, cy - 6), 1)
        # Small crimson dots.
        for dx in (-5, -1, 3):
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_light"],
                             (cx + dx, cy - 5, 1, 1))

        # Segment ridges (dark lines).
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["teal_darkest"],
                         (cx - 6, cy - 8), (cx - 7, cy + 6), 1)
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["teal_darkest"],
                         (cx - 2, cy - 9), (cx - 3, cy + 7), 1)

        # Rim highlight.
        for hx, hy in [(cx - 6, cy - 7), (cx - 1, cy - 8), (cx + 3, cy - 6)]:
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["teal_hot"], (hx, hy, 1, 1))


    def _draw_xir_thorax(surface, cx, cy, facing, phase):
        """Middle body — connects abdomen and head."""
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["shadow_deep"], (cx + 1, cy + 1), 7)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["teal_darkest"], (cx, cy), 7)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["teal_dark"], (cx - 1, cy - 1), 6)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["teal_mid"], (cx, cy - 1), 4)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["teal_light"], (cx + facing, cy - 2), 2)
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["teal_shine"],
                         (cx + facing, cy - 2, 1, 1))

        # Crimson accent stripe on top.
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_dark"],
                         (cx - 3, cy - 4), (cx + 3, cy - 4), 2)
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_mid"],
                         (cx - 2, cy - 4), (cx + 2, cy - 4), 1)


    def _draw_xir_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Head with single glowing cyan eye and mandibles."""
        # Head shape (compact insect head).
        head_shape = [
            (cx - 4, cy - 4),
            (cx - 2, cy - 6),
            (cx + 3 * facing, cy - 6),
            (cx + 6 * facing, cy - 3),
            (cx + 7 * facing, cy),
            (cx + 5 * facing, cy + 4),
            (cx + 1 * facing, cy + 5),
            (cx - 3, cy + 4),
            (cx - 5, cy),
        ]
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in head_shape])
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["teal_darkest"], head_shape)
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["teal_dark"], [
            (cx - 3, cy - 3),
            (cx + 4 * facing, cy - 5),
            (cx + 6 * facing, cy - 1),
            (cx + 4 * facing, cy + 3),
            (cx - 1, cy + 3),
            (cx - 4, cy),
        ])
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["teal_mid"], [
            (cx - 1, cy - 2),
            (cx + 3 * facing, cy - 4),
            (cx + 5 * facing, cy - 1),
            (cx + 3 * facing, cy + 2),
            (cx, cy + 2),
        ])

        # SINGLE LARGE CYAN EYE (signature Weaver look).
        _NS_xirthalis._draw_cyan_eye(surface, cx + 3 * facing, cy - 1, facing, phase)

        # Mandibles (small pincer mouth).
        mandible_open = 0
        if action == "attack":
            mandible_open = math.sin(attack_progress * math.pi) * 2

        for side in (-1, 1):
            base_x = cx + 3 * facing
            base_y = cy + 3
            tip_x = cx + int((5 + mandible_open * 0.5) * facing) + int(side * (1 + mandible_open))
            tip_y = cy + 6
            pygame.draw.line(surface, _NS_xirthalis.PALETTE["shadow_deep"],
                             (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 2)
            pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_dark"],
                             (base_x, base_y), (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_mid"],
                             (base_x, base_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_light"], (tip_x, tip_y, 1, 1))


    def _draw_cyan_eye(surface, cx, cy, facing, phase):
        """Single glowing cyan eye — signature Weaver."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Eye socket (dark).
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["shadow_deep"],
                         (cx - 2, cy - 2, 5, 4))
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_darkest"],
                         (cx - 1, cy - 2, 4, 4))

        # Glow halo.
        for radius in range(5, 0, -1):
            alpha = _NS_xirthalis._alpha(80 * (5 - radius) / 5 * pulse)
            _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["arcane_mid"], alpha), (cx + 1, cy), radius)

        # Iris (bright cyan).
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_dark"], (cx - 1, cy - 1, 4, 3))
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_mid"], (cx, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_light"], (cx + 1, cy - 1, 2, 2))
        # Bright core.
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_hot"], (cx + 1, cy, 1, 1))
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["white"], (cx + 2, cy - 1, 1, 1))


    def _draw_front_claws(surface, cx, cy, facing, phase, action, attack_progress):
        """Two large crimson claws/pincers at front — main weapons."""
        # Position claws based on attack animation.
        if action == "attack":
            p = max(0.0, min(1.0, attack_progress))
            # Wind-up → forward strike → recovery.
            if p < 0.3:
                t = p / 0.3
                claw_forward = -4 + int(t * 4)
                claw_open = 6 - int(t * 4)
                claw_rot = math.pi * 0.3 * (1 - t)
            elif p < 0.6:
                t = (p - 0.3) / 0.3
                claw_forward = int(t * 14)
                claw_open = 2 + int(t * 3)
                claw_rot = -math.pi * 0.2 * t
            else:
                t = (p - 0.6) / 0.4
                claw_forward = 14 - int(t * 14)
                claw_open = 5 - int(t * 3)
                claw_rot = -math.pi * 0.2 + math.pi * 0.5 * t
        else:
            # Idle sway.
            wave = math.sin(phase * 0.6) * 1
            claw_forward = 0 + int(wave)
            claw_open = 3
            claw_rot = math.pi * 0.2

        # Draw two claws (upper and lower).
        for side, y_off in ((-1, -3), (1, 3)):
            # Claw arm base attaches at head/thorax.
            arm_base_x = cx
            arm_base_y = cy + y_off // 2

            # Elbow joint.
            elbow_angle = math.pi * 0.15 * side + claw_rot
            elbow_dist = 6
            elbow_x = arm_base_x + int(math.cos(elbow_angle) * elbow_dist) * facing
            elbow_y = arm_base_y + int(math.sin(elbow_angle) * elbow_dist)

            # Claw tip.
            claw_tip_x = elbow_x + int((6 + claw_forward) * facing)
            claw_tip_y = elbow_y + int(y_off * 0.3)

            # Draw arm segment (thin teal).
            _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["shadow_deep"],
                    (arm_base_x + 1, arm_base_y + 1),
                    (elbow_x + 1, elbow_y + 1), 4)
            _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_darkest"],
                    (arm_base_x, arm_base_y), (elbow_x, elbow_y), 3)
            _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_dark"],
                    (arm_base_x, arm_base_y), (elbow_x, elbow_y), 2)
            _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_mid"],
                    (arm_base_x, arm_base_y - 1), (elbow_x, elbow_y - 1), 1)

            # Elbow joint (small red bump).
            _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["crimson_dark"], (elbow_x, elbow_y), 2)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_light"],
                             (elbow_x, elbow_y, 1, 1))

            # CLAW (crimson pincer).
            _NS_xirthalis._draw_pincer_claw(surface, elbow_x, elbow_y, claw_tip_x, claw_tip_y,
                              facing, side, claw_open, phase)


    def _draw_pincer_claw(surface, base_x, base_y, tip_x, tip_y, facing,
                           side, open_amt, phase):
        """Crimson pincer claw (like crab/mantis claw)."""
        # Claw base (thick red bulb).
        base_r = 4
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["shadow_deep"],
                  (base_x + facing * 2 + 1, base_y + 1), base_r)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["crimson_darkest"],
                  (base_x + facing * 2, base_y), base_r)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["crimson_dark"],
                  (base_x + facing * 2, base_y - 1), base_r - 1)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["crimson_mid"],
                  (base_x + facing * 2, base_y - 1), base_r - 2)

        # Two pincer blades opening.
        # Upper blade.
        upper_tip = (tip_x, tip_y - open_amt)
        upper_shape = [
            (base_x + facing * 3, base_y - 2),
            (base_x + facing * 5, base_y - 3),
            upper_tip,
            (base_x + facing * 4, base_y - 1),
        ]
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in upper_shape])
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["crimson_darkest"], upper_shape)
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["crimson_dark"], [
            (base_x + facing * 4, base_y - 2),
            (base_x + facing * 5, base_y - 3),
            upper_tip,
        ])
        # Sharp tip highlight.
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_shine"],
                         (upper_tip[0], upper_tip[1], 1, 1))

        # Lower blade.
        lower_tip = (tip_x, tip_y + open_amt)
        lower_shape = [
            (base_x + facing * 3, base_y + 2),
            (base_x + facing * 5, base_y + 3),
            lower_tip,
            (base_x + facing * 4, base_y + 1),
        ]
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in lower_shape])
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["crimson_darkest"], lower_shape)
        _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["crimson_dark"], [
            (base_x + facing * 4, base_y + 2),
            (base_x + facing * 5, base_y + 3),
            lower_tip,
        ])
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_shine"],
                         (lower_tip[0], lower_tip[1], 1, 1))

        # Central seam/glow between blades (when open).
        if open_amt > 3:
            pygame.draw.line(surface, _NS_xirthalis.PALETTE["crimson_light"],
                             (base_x + facing * 4, base_y),
                             ((upper_tip[0] + lower_tip[0]) // 2,
                              (upper_tip[1] + lower_tip[1]) // 2), 1)
            # Small crimson glow.
            mid_x = (upper_tip[0] + lower_tip[0]) // 2
            mid_y = (upper_tip[1] + lower_tip[1]) // 2
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_shine"],
                             (mid_x, mid_y, 1, 1))


    def _draw_insect_legs(surface, cx, cy, facing, phase, action,
                           attack_progress, back_layer=True):
        """6 insect legs (3 per side). Split back/front for layering."""
        if back_layer:
            # 3 back legs (behind body).
            leg_configs = [
                (-8, 1, math.pi * 0.9, 16, 0.0),   # back-left back
                (-10, 3, math.pi * 1.0, 18, 0.4),  # middle-left back
                (-8, 1, math.pi * 0.1, 16, 0.2),   # back-right back
                (-10, 3, math.pi * 0.0, 18, 0.6),  # middle-right back
            ]
        else:
            # 2 front legs (in front, more visible).
            leg_configs = [
                (-2, 2, math.pi * 0.75, 18, 0.15),  # front-left
                (-2, 2, math.pi * 0.25, 18, 0.35),  # front-right
            ]

        for i, (bx_off, by_off, base_angle, length, ph_off) in enumerate(leg_configs):
            base_x = cx + bx_off * facing
            base_y = cy + by_off

            # Determine side from angle.
            side = -1 if base_angle > math.pi / 2 else 1

            # Animation.
            if action == "walk":
                step = math.sin(phase * 1.8 + ph_off * math.pi * 2) * 4
                lift = max(0, math.sin(phase * 1.8 + ph_off * math.pi * 2)) * 3
            elif action == "attack":
                step = 0
                lift = 0
            else:
                step = math.sin(phase * 0.5 + ph_off * math.pi * 2) * 1.2
                lift = 0

            # Knee joint.
            joint_x = base_x + int(math.cos(base_angle) * length * 0.5) * (
                1 if base_angle < math.pi / 2 else -1
            )
            # Correct calculation: use side.
            joint_x = base_x + int(math.cos(base_angle) * length * 0.5)
            joint_y = base_y - int(math.sin(base_angle) * length * 0.5) - int(lift)

            # Foot.
            tip_x = base_x + int(math.cos(base_angle) * length) + int(step)
            tip_y = base_y + int(math.sin(base_angle) * length * 0.3) + 6

            _NS_xirthalis._draw_insect_leg_segment(surface, base_x, base_y, joint_x, joint_y,
                                      tip_x, tip_y, phase, front=not back_layer)


    def _draw_insect_leg_segment(surface, x1, y1, x2, y2, x3, y3, phase,
                                  front=False):
        """3-point articulated insect leg (thin, sharp)."""
        # Segment 1 (thigh).
        t1 = 3 if front else 2
        _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), t1 + 1)
        _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_darkest"], (x1, y1), (x2, y2), t1)
        _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_dark"], (x1, y1), (x2, y2),
                max(1, t1 - 1))
        if front:
            _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_mid"], (x1, y1 - 1), (x2, y2 - 1), 1)

        # Knee joint (small purple).
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["shadow_deep"], (x2 + 1, y2 + 1), 2)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["purple_dark"], (x2, y2), 2)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["purple_mid"], (x2, y2 - 1), 1)
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["purple_hot"], (x2, y2, 1, 1))

        # Segment 2 (shin, tapers to point).
        t2 = 2 if front else 1
        _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["shadow_deep"],
                (x2 + 1, y2 + 1), (x3 + 1, y3 + 1), t2 + 1)
        _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_darkest"], (x2, y2), (x3, y3), t2)
        if front:
            _NS_xirthalis._aaline(surface, _NS_xirthalis.PALETTE["teal_dark"], (x2, y2), (x3, y3), 1)

        # Sharp claw tip (crimson tip).
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_dark"], (x3, y3, 1, 1))
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_light"], (x3, y3 - 1, 1, 1))


    # ============================================================
    # INVISIBILITY (Shukuchi)
    # ============================================================
    def _draw_invis_silhouette(surface, cx, cy, facing, phase):
        """Ghostly outline only during Shukuchi invis."""
        # Very faint cyan outline of body silhouette.
        alpha = _NS_xirthalis._alpha(50 + math.sin(phase * 2) * 20)

        # Simple outline shape.
        outline = [
            (cx - 15, cy),
            (cx - 12, cy - 6),
            (cx - 4, cy - 8),
            (cx + 5, cy - 7),
            (cx + 12 * facing, cy - 4),
            (cx + 14 * facing, cy),
            (cx + 12 * facing, cy + 4),
            (cx + 5, cy + 6),
            (cx - 4, cy + 6),
            (cx - 12, cy + 4),
        ]
        _NS_xirthalis._poly(surface, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha), outline)
        _NS_xirthalis._poly(surface, (*_NS_xirthalis.PALETTE["arcane_mid"], alpha // 2), [
            (cx - 12, cy),
            (cx - 8, cy - 4),
            (cx + 4, cy - 5),
            (cx + 10 * facing, cy - 2),
            (cx + 10 * facing, cy + 3),
            (cx + 4, cy + 4),
            (cx - 8, cy + 3),
        ])

        # Eye still faintly visible.
        pygame.draw.rect(surface, (*_NS_xirthalis.PALETTE["arcane_light"], _NS_xirthalis._alpha(120)),
                         (cx + 3 * facing, cy - 1, 2, 2))


    def _draw_shukuchi_afterimages(surface, boss, x, y, timer):
        """Fading afterimages trailing behind."""
        facing = boss.direction
        for i in range(4):
            offset = -(i + 1) * 14 * facing
            alpha = _NS_xirthalis._alpha(120 - i * 25)
            ghost_x = x + offset
            ghost_y = y + int(math.sin(boss.pulse + i) * 2)

            # Simple silhouette copies.
            outline = [
                (ghost_x - 12, ghost_y),
                (ghost_x - 10, ghost_y - 5),
                (ghost_x - 2, ghost_y - 7),
                (ghost_x + 6, ghost_y - 6),
                (ghost_x + 11 * facing, ghost_y - 3),
                (ghost_x + 12 * facing, ghost_y),
                (ghost_x + 10 * facing, ghost_y + 3),
                (ghost_x + 4, ghost_y + 5),
                (ghost_x - 4, ghost_y + 5),
                (ghost_x - 10, ghost_y + 3),
            ]
            _NS_xirthalis._poly(surface, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha), outline)
            _NS_xirthalis._poly(surface, (*_NS_xirthalis.PALETTE["arcane_mid"], alpha // 2), [
                (ghost_x - 10, ghost_y),
                (ghost_x - 4, ghost_y - 4),
                (ghost_x + 4, ghost_y - 4),
                (ghost_x + 9 * facing, ghost_y - 1),
                (ghost_x + 8 * facing, ghost_y + 3),
                (ghost_x - 4, ghost_y + 4),
            ])
            # Sparkle streaks.
            for j in range(3):
                spark_y = ghost_y + (j - 1) * 3
                pygame.draw.rect(surface, (*_NS_xirthalis.PALETTE["arcane_light"], alpha),
                                 (ghost_x + j - 4, spark_y, 2, 1))


    # ============================================================
    # MELEE SLASH FX (double swipe)
    # ============================================================
    def _draw_melee_slash_fx(surface, boss, x, y, progress):
        """FX for melee swipe — cyan claw arcs + red impact spark."""
        if progress < 0.3:
            return

        facing = boss.direction
        tx, ty = _NS_xirthalis._target_position(boss, x, y)

        # Range check.
        dist = math.hypot(tx - x, ty - y)
        if dist > 170:
            return

        if progress > 0.35 and progress < 0.75:
            t = (progress - 0.35) / 0.40

            # Double slash arcs (upper and lower claw sweeps).
            for i, y_off in enumerate((-6, 6)):
                arc_x = x + facing * (18 + int(t * 6))
                arc_y = y + y_off
                radius = int(8 + t * 12)
                alpha = _NS_xirthalis._alpha(230 * (1 - t))

                # Slash arc.
                for a in range(4):
                    angle_start = math.pi * (0.15 + a * 0.08)
                    angle_end = math.pi * (0.85 - a * 0.08)
                    points = []
                    for s in range(7):
                        ang = angle_start + (angle_end - angle_start) * s / 6
                        if facing < 0:
                            ang = math.pi - ang
                        px = arc_x + int(math.cos(ang) * radius)
                        py = arc_y + int(math.sin(ang) * radius * 0.5)
                        points.append((px, py))
                    if len(points) > 1:
                        for j in range(len(points) - 1):
                            pygame.draw.line(surface,
                                             (*_NS_xirthalis.PALETTE["arcane_light"], alpha),
                                             points[j], points[j + 1], 2)
                            pygame.draw.line(surface,
                                             (*_NS_xirthalis.PALETTE["arcane_hot"], alpha),
                                             points[j], points[j + 1], 1)

            # Impact burst on target (crimson spark).
            if progress > 0.5:
                burst_t = (progress - 0.5) / 0.25
                burst_r = int(6 + burst_t * 12)
                burst_alpha = _NS_xirthalis._alpha(240 * (1 - burst_t))
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["crimson_dark"], burst_alpha),
                          (tx, ty), burst_r + 2, 2)
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["crimson_mid"], burst_alpha),
                          (tx, ty), burst_r, 2)
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["crimson_light"], burst_alpha),
                          (tx, ty), max(1, burst_r - 3), 1)
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["crimson_shine"], burst_alpha),
                          (tx, ty), max(1, burst_r - 6))

                # Radial sparks (crimson + cyan mixed).
                for i in range(10):
                    angle = i * math.pi / 5 + progress * 3
                    sx = tx + int(math.cos(angle) * burst_r)
                    sy = ty + int(math.sin(angle) * burst_r * 0.7)
                    color = _NS_xirthalis.PALETTE["crimson_light"] if i % 2 == 0 \
                        else _NS_xirthalis.PALETTE["arcane_light"]
                    pygame.draw.line(surface, (*color, burst_alpha),
                                     (tx, ty), (sx, sy), 1)
                    pygame.draw.rect(surface, (*_NS_xirthalis.PALETTE["white"], burst_alpha),
                                     (sx, sy, 1, 1))


    # ============================================================
    # HOVER DUST (below body - insectoid floating)
    # ============================================================
    def _draw_hover_dust(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Dust particles kicked up by hovering wings."""
        strength = 1.5 if intense else 1.0

        # Wing-beat downdraft (cyan mist below).
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 3) * 0.3 + 0.7  # faster pulse (wing beats)
        for radius in range(24, 3, -3):
            alpha = _NS_xirthalis._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xirthalis.PALETTE["arcane_darkest"], alpha),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(15, 3, -2):
            alpha = _NS_xirthalis._alpha((15 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha),
                    (60 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 60, cy - 8))

        # Sparkle particles (cyan).
        for i in range(8):
            sp_t = (phase * 0.8 + i * 0.15) % 1.0
            ex = cx - 26 + i * 7 + int(math.sin(phase * 2 + i) * 4)
            ey = cy + 6 - int(sp_t * 22)
            alpha = _NS_xirthalis._alpha(220 * (1 - sp_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_xirthalis.PALETTE["arcane_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_xirthalis.PALETTE["arcane_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Small light streaks (fast movement lines).
        for i in range(4):
            streak_t = (phase * 1.2 + i * 0.25) % 1.0
            sx = cx - 20 + i * 12
            sy = cy + int(math.sin(phase + i) * 4)
            alpha = _NS_xirthalis._alpha(180 * (1 - streak_t) * strength)
            if alpha > 0:
                pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["arcane_light"], alpha),
                                 (sx - 3, sy), (sx + 3, sy), 1)

        # Trail behind.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_xirthalis._alpha(160 - i * 28)
                if alpha <= 0:
                    continue
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha),
                          (sx, sy), max(2, 5 - i))
                pygame.draw.rect(surface, (*_NS_xirthalis.PALETTE["arcane_light"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y, invis=False):
        alpha_mult = 0.35 if invis else 1.0
        shadow = pygame.Surface((100, 22), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = int(max(0, (10 - radius) * 17) * alpha_mult)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 11 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 4, 6, int(160 * alpha_mult)),
                            (5, 5, 90, 12))
        # Cyan tint.
        pygame.draw.ellipse(shadow, (10, 40, 55, int(100 * alpha_mult)),
                            (12, 7, 76, 8))
        surface.blit(shadow, (x - 50, y - 11))


    def _draw_arcane_aura(surface, x, y, phase):
        """Cyan arcane aura."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((160, 130), pygame.SRCALPHA)
        for radius in range(65, 5, -5):
            alpha = _NS_xirthalis._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xirthalis._aacircle(aura, (*_NS_xirthalis.PALETTE["arcane_darkest"], alpha),
                          (80, 65), radius)
        for radius in range(40, 5, -4):
            alpha = _NS_xirthalis._alpha((40 - radius) * 1.7 * pulse)
            if alpha > 0:
                _NS_xirthalis._aacircle(aura, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha),
                          (80, 65), radius)
        surface.blit(aura, (x - 80, y - 65))

        # Floating sparkles.
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_hot"], (sx, sy, 1, 1))


    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground circle with arcane runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((120, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xirthalis.PALETTE["arcane_darkest"], 190),
                            (5, 12, 110, 20), 3)
        pygame.draw.ellipse(ring, (*_NS_xirthalis.PALETTE["arcane_dark"], 200),
                            (12, 14, 96, 16), 2)
        pygame.draw.ellipse(ring, (*_NS_xirthalis.PALETTE["arcane_mid"], 210),
                            (22, 16, 76, 12), 1)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 60 + int(math.cos(angle) * 32)
            y1 = 21 + int(math.sin(angle) * 6)
            x2 = 60 + int(math.cos(angle) * 50)
            y2 = 21 + int(math.sin(angle) * 9)
            pygame.draw.line(ring, (*_NS_xirthalis.PALETTE["arcane_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_xirthalis.PALETTE["arcane_hot"], _NS_xirthalis._alpha(120 * pulse)),
                                (15, 8, 90, 30), 1)
        surface.blit(ring, (x - 60, y - 21))


    # ============================================================
    # SKILL: Q - SHUKUCHI (invis dash with sparkle trail)
    # ============================================================
    def _draw_shukuchi_foreground(surface, boss, x, y, timer, phase):
        """Sparkle trail behind + speed lines during Shukuchi."""
        facing = boss.direction

        # Speed streaks radiating outward.
        for i in range(8):
            angle = phase * 5 + i * math.pi / 4
            radius_inner = 12
            radius_outer = 28 + int(math.sin(phase * 3 + i) * 4)
            x1 = x + int(math.cos(angle) * radius_inner)
            y1 = y + int(math.sin(angle) * radius_inner * 0.6)
            x2 = x + int(math.cos(angle) * radius_outer)
            y2 = y + int(math.sin(angle) * radius_outer * 0.6)
            alpha = _NS_xirthalis._alpha(200)
            pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha),
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["arcane_light"], alpha),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_hot"], (x2, y2, 2, 2))

        # Radial sparkle burst (constant during skill).
        for i in range(16):
            angle = i * math.pi / 8
            distance = 20 + int(math.sin(phase * 4 + i) * 8)
            sx = x + int(math.cos(angle) * distance)
            sy = y + int(math.sin(angle) * distance * 0.6)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_hot"], (sx, sy, 1, 1))

        # Small motion blur behind.
        for i in range(6):
            blur_x = x - (i + 1) * 8 * facing
            blur_y = y + int(math.sin(phase * 2 + i) * 3)
            alpha = _NS_xirthalis._alpha(180 - i * 25)
            _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["arcane_mid"], alpha), (blur_x, blur_y), 3)
            _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["arcane_hot"], alpha), (blur_x, blur_y), 1)


    # ============================================================
    # SKILL: W - THE SWARM (spider swarm + web on target)
    # ============================================================
    def _draw_swarm_ground(surface, boss, x, y, timer, phase):
        """Web area on ground at target."""
        tx, ty = _NS_xirthalis._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_xirthalis.PALETTE["web_dark"], 130),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))


    def _draw_swarm_foreground(surface, boss, x, y, timer, phase):
        """Purple web + swarm of small spiders."""
        tx, ty = _NS_xirthalis._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))

        if r < 5:
            return

        alpha_base = _NS_xirthalis._alpha(220 * min(1.0, progress * 3))

        # Web center.
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["web_light"], (tx, ty), 2)

        # Radial spokes.
        for i in range(10):
            angle = i * math.pi / 5 + phase * 0.05
            end_x = tx + int(math.cos(angle) * r)
            end_y = ty + int(math.sin(angle) * r * 0.5)
            pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["web_dark"], alpha_base),
                             (tx, ty), (end_x, end_y), 1)
            pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["web_mid"], alpha_base),
                             (tx, ty), (end_x, end_y), 1)

        # Concentric web rings.
        for ring_i, ring_r in enumerate((12, 24, 36, 45)):
            if ring_r > r:
                continue
            alpha = _NS_xirthalis._alpha(alpha_base * (1 - ring_i * 0.15))
            prev = None
            for i in range(11):
                angle = i * math.pi / 5 + phase * 0.05
                px = tx + int(math.cos(angle) * ring_r)
                py = ty + int(math.sin(angle) * ring_r * 0.5)
                if prev is not None:
                    pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["web_mid"], alpha),
                                     prev, (px, py), 1)
                prev = (px, py)

        # SWARM: small spiders scattering around web.
        num_spiders = 8
        for i in range(num_spiders):
            appear_t = max(0.0, min(1.0, (progress - i * 0.04) * 4))
            if appear_t <= 0:
                continue

            # Spiders spawn at boss and move to web area.
            travel_t = min(1.0, appear_t)
            start_x, start_y = x, y + 20
            end_angle = i * math.pi * 2 / num_spiders + phase * 0.2
            end_dist = int(r * 0.7 + math.sin(phase + i) * 4)
            end_x = tx + int(math.cos(end_angle) * end_dist)
            end_y = ty + int(math.sin(end_angle) * end_dist * 0.5)

            sx = int(start_x + (end_x - start_x) * travel_t)
            sy = int(start_y + (end_y - start_y) * travel_t)

            # Wiggle.
            sy += int(math.sin(phase * 4 + i) * 1)

            _NS_xirthalis._draw_swarm_spider(surface, sx, sy, phase + i)


    def _draw_swarm_spider(surface, cx, cy, phase):
        """Small purple swarm spider."""
        # Legs.
        for i in range(4):
            angle = math.pi * (0.15 + i * 0.2)
            wave = math.sin(phase * 4 + i) * 1
            for side in (-1, 1):
                lx = cx + int(math.cos(angle) * 3) * side
                ly = cy + int(math.sin(angle) * 2) + int(wave)
                pygame.draw.line(surface, _NS_xirthalis.PALETTE["spider_dark"],
                                 (cx, cy), (lx, ly), 1)

        # Body.
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["spider_dark"], (cx, cy), 2)
        _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["spider_body"], (cx, cy - 1), 1)
        # Red eye.
        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["spider_eye"], (cx, cy - 1, 1, 1))


    # ============================================================
    # SKILL: E - GEMINATE ATTACK (rapid double claw strike projectile)
    # ============================================================
    def _draw_geminate_foreground(surface, boss, x, y, timer, phase):
        """Double slash projectile toward target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xirthalis._target_position(boss, x, y)

        # Two projectiles fired quickly (second one slightly delayed).
        for shot_i, delay in enumerate((0.0, 0.15)):
            shot_progress = progress - delay
            if shot_progress < 0:
                continue

            if shot_progress < 0.15:
                # Charge at claw.
                t = shot_progress / 0.15
                hand_x = x + facing * 22
                hand_y = y - 2 + shot_i * 4
                cr = int(2 + t * 5)
                for r in range(cr + 3, 0, -1):
                    alpha = _NS_xirthalis._alpha(180 * (cr + 3 - r) / (cr + 3))
                    _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha),
                              (hand_x, hand_y), r)
                _NS_xirthalis._aacircle(surface, _NS_xirthalis.PALETTE["arcane_light"], (hand_x, hand_y), 2)
                pygame.draw.rect(surface, _NS_xirthalis.PALETTE["arcane_hot"],
                                 (hand_x, hand_y, 1, 1))
            else:
                # Projectile flies.
                t = (shot_progress - 0.15) / 0.55
                t = min(1.0, t)
                start_x = x + facing * 24
                start_y = y - 2 + shot_i * 4
                bx = int(start_x + (tx - start_x) * t)
                by = int(start_y + (ty - start_y) * t)

                # Blade-like projectile (elongated).
                trail_length = 12
                trail_x = bx - int(facing * trail_length)
                trail_y = by

                # Trail (fast motion streak).
                for i in range(4):
                    fade_t = i / 4
                    sx = int(bx - facing * trail_length * fade_t)
                    sy = by + (i - 2)
                    alpha = _NS_xirthalis._alpha(220 * (1 - fade_t))
                    pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["arcane_dark"], alpha),
                                     (sx, sy), (sx + facing * 3, sy), 2)
                    pygame.draw.line(surface, (*_NS_xirthalis.PALETTE["arcane_light"], alpha),
                                     (sx, sy), (sx + facing * 3, sy), 1)

                # Blade head.
                blade_shape = [
                    (bx - facing * 4, by - 2),
                    (bx + facing * 4, by),
                    (bx - facing * 4, by + 2),
                    (bx - facing * 2, by),
                ]
                _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["arcane_dark"], blade_shape)
                _NS_xirthalis._poly(surface, _NS_xirthalis.PALETTE["arcane_mid"], [
                    (bx - facing * 3, by - 1),
                    (bx + facing * 3, by),
                    (bx - facing * 3, by + 1),
                ])
                # Bright edge.
                pygame.draw.line(surface, _NS_xirthalis.PALETTE["arcane_light"],
                                 (bx - facing * 4, by - 2),
                                 (bx + facing * 4, by), 1)
                pygame.draw.line(surface, _NS_xirthalis.PALETTE["arcane_hot"],
                                 (bx - facing * 4, by + 2),
                                 (bx + facing * 4, by), 1)
                pygame.draw.rect(surface, _NS_xirthalis.PALETTE["white"], (bx, by, 1, 1))

                # Impact.
                if t > 0.9:
                    st = (t - 0.9) / 0.1
                    radius = int(5 + st * 12)
                    alpha = _NS_xirthalis._alpha(230 * (1 - st))
                    _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["crimson_mid"], alpha),
                              (tx, ty + shot_i * 3), radius, 2)
                    _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["crimson_light"], alpha),
                              (tx, ty + shot_i * 3), max(1, radius - 4), 1)
                    for j in range(6):
                        angle = j * math.pi / 3
                        ex = tx + int(math.cos(angle) * radius)
                        ey = ty + shot_i * 3 + int(math.sin(angle) * radius * 0.6)
                        pygame.draw.rect(surface, _NS_xirthalis.PALETTE["crimson_shine"],
                                         (ex, ey, 1, 1))


    # ============================================================
    # SKILL: R - TIME LAPSE (blue time vortex + rewind)
    # ============================================================
    def _draw_timelapse_ground(surface, boss, x, y, timer, phase):
        """Blue vortex ring on ground under boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Vortex ring.
        for i in range(3):
            r = int(20 + i * 15 + progress * 30)
            alpha = _NS_xirthalis._alpha(200 - i * 40)
            _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_dark"], alpha),
                      (x, y + 34), r, 2)
            _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_mid"], alpha),
                      (x, y + 34), r, 1)


    def _draw_timelapse_foreground(surface, boss, x, y, timer, phase):
        """Time vortex swirling around boss + clock hands + rewind afterimages."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Central time vortex core.
        core_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(30, 3, -3):
            alpha = _NS_xirthalis._alpha((30 - r) * 4 * core_pulse * min(1.0, progress * 2))
            if alpha > 0:
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_darkest"], alpha), (x, y), r)
        for r in range(20, 3, -2):
            alpha = _NS_xirthalis._alpha((20 - r) * 5 * core_pulse * min(1.0, progress * 2))
            if alpha > 0:
                _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_dark"], alpha), (x, y), r)

        # Swirling time particles (spiral inward).
        for i in range(20):
            angle = phase * 3 + i * math.pi / 10
            # Spiral inward.
            spiral_t = (phase * 0.5 + i * 0.1) % 1.0
            radius = int(35 * (1 - spiral_t) + 5)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.7)
            alpha = _NS_xirthalis._alpha(230 * spiral_t)
            _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_mid"], alpha), (sx, sy), 2)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["time_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["white"], (sx, sy, 1, 1))

        # Clock hands rotating BACKWARDS (time reversal).
        hand_angle = -phase * 4  # negative = counterclockwise
        # Hour hand.
        hx = x + int(math.cos(hand_angle) * 12)
        hy = y + int(math.sin(hand_angle) * 12)
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["time_light"], (x, y), (hx, hy), 2)
        # Minute hand.
        mx = x + int(math.cos(hand_angle * 1.5) * 20)
        my = y + int(math.sin(hand_angle * 1.5) * 20)
        pygame.draw.line(surface, _NS_xirthalis.PALETTE["time_mid"], (x, y), (mx, my), 1)

        # Clock face marks.
        for i in range(12):
            angle = i * math.pi / 6
            mark_x = x + int(math.cos(angle) * 25)
            mark_y = y + int(math.sin(angle) * 25 * 0.7)
            pygame.draw.rect(surface, _NS_xirthalis.PALETTE["time_light"], (mark_x, mark_y, 1, 1))

        # Outer ring pulse.
        ring_r = int(30 + math.sin(phase * 4) * 4)
        alpha = _NS_xirthalis._alpha(200 * core_pulse)
        _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_mid"], alpha), (x, y), ring_r, 2)
        _NS_xirthalis._aacircle(surface, (*_NS_xirthalis.PALETTE["time_light"], alpha), (x, y),
                  max(1, ring_r - 3), 1)

        # Rewind afterimages fading forward (like rewinding to previous positions).
        facing = boss.direction
        for i in range(4):
            offset_x = -(i + 1) * 8 * facing
            offset_y = int(math.sin(phase + i) * 2)
            alpha = _NS_xirthalis._alpha(150 - i * 30)
            # Ghost silhouette.
            ghost_x = x + offset_x
            ghost_y = y + offset_y
            outline = [
                (ghost_x - 12, ghost_y),
                (ghost_x - 8, ghost_y - 5),
                (ghost_x + 3, ghost_y - 6),
                (ghost_x + 10 * facing, ghost_y - 2),
                (ghost_x + 10 * facing, ghost_y + 3),
                (ghost_x + 3, ghost_y + 5),
                (ghost_x - 8, ghost_y + 4),
            ]
            _NS_xirthalis._poly(surface, (*_NS_xirthalis.PALETTE["time_mid"], alpha), outline)
            _NS_xirthalis._poly(surface, (*_NS_xirthalis.PALETTE["time_light"], alpha // 2), [
                (ghost_x - 8, ghost_y),
                (ghost_x - 4, ghost_y - 3),
                (ghost_x + 6 * facing, ghost_y - 1),
                (ghost_x + 5 * facing, ghost_y + 3),
                (ghost_x - 4, ghost_y + 3),
            ])



# ====================================================================
# VHYSSARION
# ====================================================================
class _NS_vhyssarion:
    """Namespace vhyssarion - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Toxic yellow-green (frills, glow)
        "toxic_darkest": (20, 30, 5),
        "toxic_dark": (60, 90, 15),
        "toxic_mid": (140, 190, 35),
        "toxic_light": (200, 245, 80),
        "toxic_hot": (240, 255, 150),
        "toxic_shine": (255, 255, 220),

        # Dark green scales (body)
        "scale_darkest": (10, 20, 8),
        "scale_dark": (30, 55, 18),
        "scale_mid": (65, 100, 35),
        "scale_light": (110, 155, 60),
        "scale_edge": (160, 200, 100),

        # Purple accents (belly, underscales, tongue)
        "purple_darkest": (18, 5, 25),
        "purple_dark": (55, 20, 70),
        "purple_mid": (110, 45, 130),
        "purple_light": (170, 90, 200),
        "purple_hot": (220, 150, 250),

        # Head/frill highlights (yellowish-tan)
        "frill_darkest": (35, 25, 5),
        "frill_dark": (95, 70, 20),
        "frill_mid": (170, 135, 45),
        "frill_light": (230, 200, 90),
        "frill_shine": (255, 240, 160),

        # Eye colors (orange menyala)
        "eye_socket": (5, 3, 2),
        "eye_dark": (85, 30, 5),
        "eye_mid": (220, 120, 20),
        "eye_light": (255, 200, 80),
        "eye_glow": (255, 240, 180),

        # Fang (bone yellowish)
        "fang_dark": (60, 45, 25),
        "fang_mid": (150, 125, 80),
        "fang_light": (230, 210, 160),
        "fang_shine": (255, 245, 210),

        # Blood/tongue purple
        "tongue_dark": (60, 15, 35),
        "tongue_mid": (145, 40, 90),
        "tongue_light": (210, 90, 150),

        # Poison mist/wind
        "mist_dark": (20, 40, 10),
        "mist_mid": (80, 130, 30),
        "mist_light": (170, 220, 80),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vhyssarion._clamp(color)
        if _NS_vhyssarion.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vhyssarion._clamp(color)
        if _NS_vhyssarion.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vhyssarion._clamp(color), points)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vhyssarion(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vhyssarion._detect_moving(boss)
        _NS_vhyssarion._update_vhys_attack_anim(boss)
        attacking = (
            getattr(boss, "_vhys_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_vhyssarion._draw_poison_aura(surface, x, y, pulse)
        _NS_vhyssarion._draw_ground_ring(surface, x, y + 38, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_vhyssarion._draw_plague_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vhyssarion._draw_gale_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhyssarion._draw_nova_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_vhyssarion._draw_vhys_attack(surface, boss, x, y)
        elif moving:
            _NS_vhyssarion._draw_vhys_walk(surface, boss, x, y)
        else:
            _NS_vhyssarion._draw_vhys_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_vhyssarion._draw_plague_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vhyssarion._draw_poison_sting_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vhyssarion._draw_gale_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhyssarion._draw_nova_foreground(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vhys_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vhys_previous_timer", 0))
        active = bool(getattr(boss, "_vhys_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vhys_attack_active = True
            boss._vhys_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vhys_attack_frame = int(
                getattr(boss, "_vhys_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._vhys_attack_active = False
            boss._vhys_attack_frame = 0
            active = False

        boss._vhys_previous_timer = timer
        boss._vhys_attack_progress = (
            min(1.0, getattr(boss, "_vhys_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_vhys_last_x"):
            boss._vhys_last_x = boss.x
            boss._vhys_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vhys_last_x)
        dy = abs(boss.y - boss._vhys_last_y)
        boss._vhys_last_x = boss.x
        boss._vhys_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vhys_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_vhyssarion._draw_shadow(surface, x, y + 44)
        _NS_vhyssarion._draw_poison_mist(surface, x, y + 30, boss.pulse)
        _NS_vhyssarion._draw_vhys_body(surface, x, y + bob,
                         boss.direction, boss.pulse, "idle")


    def _draw_vhys_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 3)  # more sway (snake-like)
        _NS_vhyssarion._draw_shadow(surface, x + sway, y + 44)
        _NS_vhyssarion._draw_poison_mist(surface, x + sway, y + 30, phase, trail=True,
                          facing=boss.direction)
        _NS_vhyssarion._draw_vhys_body(surface, x + sway, y + bob,
                         boss.direction, phase, "walk")


    def _draw_vhys_attack(surface, boss, x, y):
        progress = getattr(boss, "_vhys_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back then strike forward.
        if progress < 0.4:
            # Rear back.
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            # Strike forward.
            t = (progress - 0.4) / 0.25
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(4 - t * 6)
        else:
            # Recovery.
            t = (progress - 0.65) / 0.35
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_vhyssarion._draw_shadow(surface, x + lunge, y + 44)
        _NS_vhyssarion._draw_poison_mist(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_vhyssarion._draw_vhys_body(surface, x + lunge, y - lift,
                         boss.direction, boss.pulse, "attack", progress)
        _NS_vhyssarion._draw_poison_stinger_projectile(surface, boss, x + lunge, y - lift,
                                         progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_vhys_body(surface, cx, cy, facing, phase, action,
                         attack_progress=0):
        """Serpent body: coiling tail, torso rising, neck curving, head with frills."""
        # Draw coiling tail/body first (behind).
        _NS_vhyssarion._draw_serpent_coils(surface, cx, cy + 12, facing, phase)

        # Main torso (rising up).
        _NS_vhyssarion._draw_serpent_torso(surface, cx, cy, facing, phase)

        # Neck (curving forward).
        neck_lunge = 0
        if action == "attack":
            # Neck moves during attack.
            if attack_progress < 0.4:
                neck_lunge = -int(attack_progress / 0.4 * 3) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                neck_lunge = int((-3 + t * 14)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                neck_lunge = int(11 * (1 - t)) * facing
        _NS_vhyssarion._draw_serpent_neck(surface, cx, cy - 8, facing, phase, neck_lunge)

        # Head with frills.
        _NS_vhyssarion._draw_serpent_head(surface, cx + facing * 12 + neck_lunge, cy - 20,
                            facing, phase, action, attack_progress)


    def _draw_serpent_coils(surface, cx, cy, facing, phase):
        """Coiling tail sections floating below."""
        # Multiple coil segments, curving in S-shape.
        breath = math.sin(phase * 0.5) * 2

        # Bottom coil (widest).
        coil1_shape = [
            (cx - 22, cy + 8),
            (cx - 26, cy + 4),
            (cx - 25, cy - 2),
            (cx - 20, cy - 6),
            (cx - 10, cy - 8),
            (cx + 5, cy - 6),
            (cx + 18, cy - 2),
            (cx + 26, cy + 4),
            (cx + 24, cy + 10),
            (cx + 15, cy + 14),
            (cx + 3, cy + 15),
            (cx - 10, cy + 14),
            (cx - 18, cy + 12),
        ]
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in coil1_shape])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_darkest"], coil1_shape)

        # Purple underbelly.
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["purple_darkest"], [
            (cx - 20, cy + 6),
            (cx - 22, cy + 2),
            (cx - 20, cy - 4),
            (cx + 20, cy - 4),
            (cx + 22, cy + 2),
            (cx + 20, cy + 10),
            (cx + 3, cy + 13),
            (cx - 15, cy + 12),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["purple_dark"], [
            (cx - 18, cy + 4),
            (cx - 19, cy + 1),
            (cx - 17, cy - 2),
            (cx + 17, cy - 2),
            (cx + 19, cy + 1),
            (cx + 17, cy + 8),
            (cx + 3, cy + 11),
            (cx - 12, cy + 10),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["purple_mid"], [
            (cx - 14, cy + 3),
            (cx - 15, cy),
            (cx - 12, cy - 1),
            (cx + 12, cy - 1),
            (cx + 15, cy),
            (cx + 13, cy + 6),
            (cx + 3, cy + 9),
            (cx - 8, cy + 8),
        ])

        # Green scale top (visible portion).
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_dark"], [
            (cx - 22, cy),
            (cx - 20, cy - 6),
            (cx - 10, cy - 8),
            (cx + 5, cy - 6),
            (cx + 18, cy - 2),
            (cx + 20, cy - 4),
            (cx + 15, cy - 6),
            (cx, cy - 8),
            (cx - 15, cy - 6),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_mid"], [
            (cx - 18, cy - 2),
            (cx - 15, cy - 6),
            (cx - 5, cy - 7),
            (cx + 8, cy - 5),
            (cx + 16, cy - 2),
        ])

        # Scale detail (small chevrons).
        for i, dx in enumerate((-18, -12, -6, 0, 6, 12, 18)):
            y_off = int(math.sin(phase * 0.6 + i * 0.5) * 1)
            pygame.draw.line(surface, _NS_vhyssarion.PALETTE["scale_darkest"],
                             (cx + dx - 2, cy - 3 + y_off),
                             (cx + dx, cy - 5 + y_off), 1)
            pygame.draw.line(surface, _NS_vhyssarion.PALETTE["scale_darkest"],
                             (cx + dx, cy - 5 + y_off),
                             (cx + dx + 2, cy - 3 + y_off), 1)
            pygame.draw.line(surface, _NS_vhyssarion.PALETTE["scale_edge"],
                             (cx + dx - 1, cy - 4 + y_off),
                             (cx + dx + 1, cy - 4 + y_off), 1)

        # Belly segment lines (horizontal stripes on purple).
        for i in range(4):
            y_pos = cy + 2 + i * 3
            pygame.draw.line(surface, _NS_vhyssarion.PALETTE["purple_darkest"],
                             (cx - 14, y_pos), (cx + 14, y_pos), 1)

        # Small tail tip peeking out.
        tail_wave = math.sin(phase * 0.8) * 3
        tail_tip_x = cx - 26 + int(tail_wave)
        tail_tip_y = cy + 2
        pygame.draw.line(surface, _NS_vhyssarion.PALETTE["scale_darkest"],
                         (cx - 22, cy + 2), (tail_tip_x, tail_tip_y), 4)
        pygame.draw.line(surface, _NS_vhyssarion.PALETTE["scale_dark"],
                         (cx - 22, cy + 2), (tail_tip_x, tail_tip_y), 2)
        pygame.draw.line(surface, _NS_vhyssarion.PALETTE["scale_mid"],
                         (cx - 22, cy + 2), (tail_tip_x, tail_tip_y), 1)
        # Tail spike tip.
        _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_dark"], (tail_tip_x, tail_tip_y), 2)
        _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_light"], (tail_tip_x, tail_tip_y), 1)


    def _draw_serpent_torso(surface, cx, cy, facing, phase):
        """Rising torso section connecting coils to neck."""
        breath = math.sin(phase * 0.7) * 1

        # Torso oval (vertical).
        torso_shape = [
            (cx - 10, cy + 8),
            (cx - 12, cy),
            (cx - 10, cy - 8),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 10, cy - 8),
            (cx + 12, cy),
            (cx + 10, cy + 8),
            (cx + 4, cy + 12),
            (cx - 4, cy + 12),
        ]
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in torso_shape])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_darkest"], torso_shape)

        # Purple front (belly).
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["purple_dark"], [
            (cx - 6, cy + 8),
            (cx - 8, cy),
            (cx - 6, cy - 8),
            (cx + 6, cy - 8),
            (cx + 8, cy),
            (cx + 6, cy + 8),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["purple_mid"], [
            (cx - 4, cy + 6),
            (cx - 6, cy),
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy),
            (cx + 4, cy + 6),
        ])

        # Green scale back (behind, taller side).
        back_side = -facing
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_dark"], [
            (cx + back_side * 6, cy + 8),
            (cx + back_side * 12, cy),
            (cx + back_side * 10, cy - 10),
            (cx, cy - 12),
            (cx + back_side * 4, cy - 8),
            (cx + back_side * 8, cy),
            (cx + back_side * 6, cy + 6),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_mid"], [
            (cx + back_side * 8, cy),
            (cx + back_side * 8, cy - 6),
            (cx, cy - 10),
            (cx + back_side * 4, cy - 6),
            (cx + back_side * 6, cy),
        ])

        # Belly segments.
        for i in range(4):
            y_pos = cy - 6 + i * 4
            pygame.draw.line(surface, _NS_vhyssarion.PALETTE["purple_darkest"],
                             (cx - 5, y_pos), (cx + 5, y_pos), 1)
            # Small highlight.
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["purple_hot"],
                             (cx, y_pos - 1, 1, 1))

        # Back spikes (dorsal ridge).
        for i, y_off in enumerate((-10, -6, -2, 2, 6)):
            spike_wave = math.sin(phase * 0.4 + i * 0.3) * 1
            spike_x = cx + back_side * (10 + int(spike_wave))
            spike_y = cy + y_off
            # Small triangle spike.
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_darkest"], [
                (spike_x, spike_y),
                (spike_x + back_side * 3, spike_y - 1),
                (spike_x + back_side * 1, spike_y + 2),
            ])
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["toxic_dark"], [
                (spike_x + back_side, spike_y),
                (spike_x + back_side * 3, spike_y - 1),
                (spike_x + back_side * 2, spike_y + 1),
            ])
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_light"],
                             (spike_x + back_side * 2, spike_y - 1, 1, 1))


    def _draw_serpent_neck(surface, cx, cy, facing, phase, lunge_offset=0):
        """Curving neck from torso to head."""
        # Curved neck path.
        base_x = cx
        base_y = cy + 4
        tip_x = cx + facing * 12 + lunge_offset
        tip_y = cy - 10

        # 4 curve segments.
        prev = (base_x, base_y)
        for step in range(1, 5):
            t = step / 4
            mid_x = base_x + int((tip_x - base_x) * 0.55) - facing * 2
            mid_y = base_y - int((base_y - tip_y) * 0.55) - 2
            bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            width = 10 - step

            _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
                    (prev[0] + 2, prev[1] + 2), (bx + 2, by + 2), width + 1)
            _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["scale_darkest"], prev, (bx, by), width)
            _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["scale_dark"], prev, (bx, by), max(1, width - 2))
            _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["scale_mid"], (prev[0], prev[1] - 1),
                    (bx, by - 1), max(1, width - 4))

            # Belly (front side).
            _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["purple_dark"],
                    (prev[0] + facing, prev[1] + 1),
                    (bx + facing, by + 1), max(1, width - 3))

            # Small back spike per segment.
            if step % 1 == 0:
                spike_x = bx - facing * (width // 2)
                spike_y = by - width // 2
                _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["toxic_dark"], [
                    (spike_x, spike_y),
                    (spike_x - facing * 2, spike_y - 2),
                    (spike_x - facing, spike_y),
                ])
                pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_light"],
                                 (spike_x - facing * 2, spike_y - 2, 1, 1))

            prev = (bx, by)


    def _draw_serpent_head(surface, cx, cy, facing, phase, action,
                            attack_progress):
        """Head with mahkota frills, eyes, fangs, tongue."""
        # Head base shape.
        head_shape = [
            (cx - 8 * facing, cy + 5),   # back bottom
            (cx - 10 * facing, cy),      # back top
            (cx - 6 * facing, cy - 5),   # top back
            (cx, cy - 7),                # top mid
            (cx + 6 * facing, cy - 5),   # top front
            (cx + 10 * facing, cy - 2),  # snout top
            (cx + 12 * facing, cy + 1),  # snout tip
            (cx + 10 * facing, cy + 4),  # snout bottom
            (cx + 5 * facing, cy + 6),   # jaw
            (cx - 3 * facing, cy + 7),   # jaw back
        ]
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in head_shape])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_darkest"], head_shape)

        # Green scale top (main head color).
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_dark"], [
            (cx - 8 * facing, cy + 3),
            (cx - 9 * facing, cy - 1),
            (cx - 5 * facing, cy - 4),
            (cx + 1, cy - 6),
            (cx + 6 * facing, cy - 4),
            (cx + 10 * facing, cy - 1),
            (cx + 11 * facing, cy + 1),
            (cx + 8 * facing, cy + 2),
            (cx, cy + 3),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["scale_mid"], [
            (cx - 6 * facing, cy),
            (cx - 4 * facing, cy - 3),
            (cx + 2, cy - 5),
            (cx + 5 * facing, cy - 3),
            (cx + 9 * facing, cy),
            (cx + 7 * facing, cy + 1),
            (cx, cy + 2),
        ])

        # Snout highlight (yellowish-tan).
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["frill_dark"], [
            (cx + 6 * facing, cy - 3),
            (cx + 10 * facing, cy - 1),
            (cx + 11 * facing, cy + 1),
            (cx + 9 * facing, cy + 3),
            (cx + 5 * facing, cy),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["frill_mid"], [
            (cx + 7 * facing, cy - 2),
            (cx + 10 * facing, cy),
            (cx + 8 * facing, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["frill_light"],
                         (cx + 9 * facing, cy - 1, 1, 1))

        # Jaw (purple underside).
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["purple_dark"], [
            (cx - 3 * facing, cy + 6),
            (cx + 5 * facing, cy + 5),
            (cx + 10 * facing, cy + 3),
            (cx + 8 * facing, cy + 6),
            (cx + 2 * facing, cy + 7),
        ])

        # FRILLS (mahkota berduri di kepala) - signature Venomancer.
        _NS_vhyssarion._draw_head_frills(surface, cx, cy, facing, phase)

        # EYES (orange glowing).
        _NS_vhyssarion._draw_serpent_eyes(surface, cx, cy, facing, phase)

        # FANGS + MOUTH (open when attacking).
        mouth_open = 0
        tongue_out = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 4)
            if attack_progress > 0.4 and attack_progress < 0.7:
                tongue_out = math.sin((attack_progress - 0.4) / 0.3 * math.pi) * 8

        _NS_vhyssarion._draw_serpent_mouth(surface, cx, cy, facing, phase, mouth_open, tongue_out)

        # Nostril.
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
                         (cx + 9 * facing, cy - 1, 1, 1))


    def _draw_head_frills(surface, cx, cy, facing, phase):
        """Yellow-green spike frills on top and sides of head."""
        # Central crown spikes (5 spikes fanning up).
        for i, (base_off_x, base_off_y, angle_off, length) in enumerate([
            (-4, -6, math.pi * 0.55, 12),   # back
            (-1, -7, math.pi * 0.60, 14),   # back-mid
            (2, -7, math.pi * 0.65, 15),    # top-tallest
            (5, -6, math.pi * 0.72, 13),    # front-mid
            (8, -4, math.pi * 0.80, 10),    # front
        ]):
            sway = math.sin(phase * 0.5 + i * 0.4) * 1.5
            base_x = cx + int(base_off_x * facing)
            base_y = cy + base_off_y
            tip_x = cx + int((base_off_x + math.cos(angle_off) * length) * facing)
            tip_y = base_y - int(math.sin(angle_off) * length) + int(sway)

            # Spike shape.
            perp_len = 2
            angle_perp = angle_off + math.pi / 2
            pa_x = base_x + int(math.cos(angle_perp) * perp_len)
            pa_y = base_y + int(math.sin(angle_perp) * perp_len)
            pb_x = base_x - int(math.cos(angle_perp) * perp_len)
            pb_y = base_y - int(math.sin(angle_perp) * perp_len)

            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["frill_darkest"],
                  [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["frill_dark"], [
                (tip_x, tip_y),
                ((tip_x + pa_x) // 2, (tip_y + pa_y) // 2),
                (base_x, base_y),
            ])
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["frill_mid"], [
                (tip_x, tip_y),
                ((tip_x + base_x) // 2, (tip_y + base_y) // 2),
                (base_x, base_y),
            ])

            # Yellow glowing tip.
            _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_light"], (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_hot"], (tip_x, tip_y, 1, 1))

        # Side frills (smaller, sweeping backward).
        for side_flag in (1,):  # only visible side
            for i, (base_off_x, base_off_y, angle_off, length) in enumerate([
                (-8, -2, math.pi * 0.95, 8),
                (-7, 1, math.pi * 1.05, 9),
                (-5, 4, math.pi * 1.15, 7),
            ]):
                sway = math.sin(phase * 0.4 + i * 0.5) * 1
                base_x = cx + int(base_off_x * facing)
                base_y = cy + base_off_y
                tip_x = cx + int((base_off_x + math.cos(angle_off) * length) * facing)
                tip_y = base_y - int(math.sin(angle_off) * length) + int(sway)

                _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
                        (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 3)
                _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["frill_darkest"],
                        (base_x, base_y), (tip_x, tip_y), 3)
                _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["frill_dark"],
                        (base_x, base_y), (tip_x, tip_y), 2)
                _NS_vhyssarion._aaline(surface, _NS_vhyssarion.PALETTE["frill_mid"],
                        (base_x, base_y), (tip_x, tip_y), 1)
                pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_light"],
                                 (tip_x, tip_y, 1, 1))


    def _draw_serpent_eyes(surface, cx, cy, facing, phase):
        """Orange glowing eye (one visible from side view)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        ex = cx + 4 * facing
        ey = cy - 1

        # Socket.
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))

        # Glow halo.
        for radius in range(5, 0, -1):
            alpha = _NS_vhyssarion._alpha(90 * (5 - radius) / 5 * pulse)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["eye_mid"], alpha), (ex + 1, ey), radius)

        # Iris.
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["eye_dark"], (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["eye_mid"], (ex, ey - 1, 3, 2))
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["eye_light"], (ex + 1, ey - 1, 2, 2))
        # Bright center.
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["eye_glow"], (ex + 1, ey, 1, 1))
        # Vertical pupil (reptile).
        pygame.draw.line(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
                         (ex + 1, ey - 1), (ex + 1, ey + 1), 1)


    def _draw_serpent_mouth(surface, cx, cy, facing, phase, mouth_open, tongue_out):
        """Mouth with fangs; opens during attack, tongue flicks out."""
        mouth_y = cy + 3
        mouth_x_start = cx + 3 * facing
        mouth_x_end = cx + 11 * facing

        if mouth_open > 0:
            # Open mouth (dark cavity).
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y - 1),
                (mouth_x_end, mouth_y + int(mouth_open)),
                (mouth_x_start, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["tongue_dark"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y),
                (mouth_x_end - facing, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing, mouth_y + int(mouth_open * 0.7) - 1),
            ])

            # UPPER FANGS.
            for i, x_off in enumerate((4, 8)):
                fang_x = cx + int(x_off * facing)
                fang_tip_y = mouth_y + int(mouth_open * 0.9)
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["fang_dark"],
                                 (fang_x, mouth_y),
                                 (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["fang_mid"],
                                 (fang_x, mouth_y),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
                # Venom drip.
                if mouth_open > 2:
                    drip_y = fang_tip_y + int(mouth_open * 0.5)
                    pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_mid"],
                                     (fang_x, drip_y, 1, 2))
                    pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_light"],
                                     (fang_x, drip_y, 1, 1))

            # LOWER FANGS.
            for i, x_off in enumerate((5, 9)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 2
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["fang_mid"],
                                 (fang_x, fang_tip_y, 1, 1))

            # TONGUE FLICKING OUT.
            if tongue_out > 0:
                tongue_base_x = cx + 8 * facing
                tongue_base_y = mouth_y + int(mouth_open * 0.5)
                tongue_tip_x = tongue_base_x + int(tongue_out * facing)
                tongue_tip_y = tongue_base_y + int(math.sin(phase * 8) * 2)

                # Main tongue line.
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["tongue_dark"],
                                 (tongue_base_x, tongue_base_y),
                                 (tongue_tip_x, tongue_tip_y), 2)
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["tongue_mid"],
                                 (tongue_base_x, tongue_base_y),
                                 (tongue_tip_x, tongue_tip_y), 1)

                # Fork tips (bercabang).
                fork_len = 3
                fork1_x = tongue_tip_x + int(facing * fork_len)
                fork1_y = tongue_tip_y - 2
                fork2_x = tongue_tip_x + int(facing * fork_len)
                fork2_y = tongue_tip_y + 2
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["tongue_dark"],
                                 (tongue_tip_x, tongue_tip_y),
                                 (fork1_x, fork1_y), 1)
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["tongue_dark"],
                                 (tongue_tip_x, tongue_tip_y),
                                 (fork2_x, fork2_y), 1)
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["tongue_light"],
                                 (tongue_tip_x, tongue_tip_y),
                                 (fork1_x, fork1_y), 1)
                pygame.draw.line(surface, _NS_vhyssarion.PALETTE["tongue_light"],
                                 (tongue_tip_x, tongue_tip_y),
                                 (fork2_x, fork2_y), 1)
        else:
            # Closed mouth (thin line).
            pygame.draw.line(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y), 1)
            # Small fang peek.
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["fang_mid"],
                             (cx + 6 * facing, mouth_y + 1, 1, 2))
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["fang_light"],
                             (cx + 6 * facing, mouth_y + 2, 1, 1))


    # ============================================================
    # RANGED ATTACK — POISON STINGER PROJECTILE
    # ============================================================
    def _draw_poison_stinger_projectile(surface, boss, x, y, progress):
        """Yellow-green poison stinger fired from mouth toward target."""
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_vhyssarion._target_position(boss, x, y)

        # Launch point at mouth.
        start_x = x + facing * 26
        start_y = y - 18

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Poison trail.
        for i in range(7):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vhyssarion._alpha(220 - i * 28)
            # Green smoke trail.
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_darkest"], alpha), (px, py), 6 - i)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], alpha), (px, py), 4 - i // 2)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha), (px, py),
                      max(1, 3 - i // 2))
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha), (px, py),
                      max(1, 2 - i // 2))
            # Small droplets.
            if i % 2 == 0:
                drip_x = px + int(math.sin(t * 8 + i) * 3)
                drip_y = py + int(math.cos(t * 8 + i) * 2)
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                                 (drip_x, drip_y, 1, 1))

        # Stinger head (spike shape, not circle).
        # Elongated projectile pointing forward.
        angle = math.atan2(ty - start_y, tx - start_x)
        dx_ = math.cos(angle)
        dy_ = math.sin(angle)
        perp_x = -dy_
        perp_y = dx_

        stinger_len = 8
        stinger_wid = 3

        tip = (bx + int(dx_ * stinger_len), by + int(dy_ * stinger_len))
        back_left = (bx - int(dx_ * 2) + int(perp_x * stinger_wid),
                     by - int(dy_ * 2) + int(perp_y * stinger_wid))
        back_right = (bx - int(dx_ * 2) - int(perp_x * stinger_wid),
                      by - int(dy_ * 2) - int(perp_y * stinger_wid))
        back_center = (bx - int(dx_ * 4), by - int(dy_ * 4))

        # Draw stinger (diamond/spike shape).
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in [tip, back_left, back_center,
                                                back_right]])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["toxic_darkest"],
              [tip, back_left, back_center, back_right])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["toxic_dark"], [
            tip,
            (int((tip[0] + back_left[0]) / 2), int((tip[1] + back_left[1]) / 2)),
            back_center,
            (int((tip[0] + back_right[0]) / 2), int((tip[1] + back_right[1]) / 2)),
        ])
        _NS_vhyssarion._poly(surface, _NS_vhyssarion.PALETTE["toxic_mid"], [
            tip,
            (int(bx + perp_x * 1), int(by + perp_y * 1)),
            back_center,
            (int(bx - perp_x * 1), int(by - perp_y * 1)),
        ])
        _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_light"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_shine"], (tip[0], tip[1], 1, 1))
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(6 + st * 20)
            alpha = _NS_vhyssarion._alpha(240 * (1 - st))
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_darkest"], alpha), (tx, ty),
                      radius + 2, 3)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha), (tx, ty),
                      radius, 2)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha), (tx, ty),
                      max(1, radius - 5), 1)
            # Splash droplets.
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                                 (ex, ey, 1, 1))


    # ============================================================
    # FLOATING POISON MIST (below body)
    # ============================================================
    def _draw_poison_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Toxic green mist floating below body."""
        strength = 1.5 if intense else 1.0

        # Mist cloud.
        mist = pygame.Surface((130, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_vhyssarion._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhyssarion.PALETTE["mist_dark"], alpha),
                    (65 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_vhyssarion._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhyssarion.PALETTE["mist_mid"], alpha),
                    (65 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 65, cy - 10))

        # Rising green bubbles.
        for i, offset in enumerate((-22, -14, -6, 4, 12, 20, -2)):
            t = (phase * 0.4 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_vhyssarion._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["mist_dark"], alpha), (sx, sy), 3)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["mist_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Yellow embers.
        for i in range(6):
            ember_t = (phase * 0.6 + i * 0.2) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 22)
            alpha = _NS_vhyssarion._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Trail behind.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vhyssarion._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["mist_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["mist_mid"], alpha),
                          (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 24), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 90 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 6, 100, 12))
        # Green inner shadow.
        pygame.draw.ellipse(shadow, (30, 60, 15, 100), (12, 8, 86, 8))
        surface.blit(shadow, (x - 55, y - 12))


    def _draw_poison_aura(surface, x, y, phase):
        """Yellow-green toxic aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((170, 140), pygame.SRCALPHA)
        for radius in range(72, 5, -5):
            alpha = _NS_vhyssarion._alpha((72 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vhyssarion._aacircle(aura, (*_NS_vhyssarion.PALETTE["mist_dark"], alpha), (85, 70), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_vhyssarion._alpha((45 - radius) * 1.7 * pulse)
            if alpha > 0:
                _NS_vhyssarion._aacircle(aura, (*_NS_vhyssarion.PALETTE["mist_mid"], alpha), (85, 70), radius)
        surface.blit(aura, (x - 85, y - 70))

        # Floating yellow embers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 30 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_hot"], (sx, sy, 1, 1))


    def _draw_ground_ring(surface, x, y, phase, skill):
        """Green ground ring with toxic runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((130, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vhyssarion.PALETTE["mist_dark"], 200),
                            (5, 14, 120, 20), 3)
        pygame.draw.ellipse(ring, (*_NS_vhyssarion.PALETTE["toxic_darkest"], 220),
                            (12, 16, 106, 16), 2)
        pygame.draw.ellipse(ring, (*_NS_vhyssarion.PALETTE["toxic_dark"], 230),
                            (22, 18, 86, 12), 1)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 34)
            y1 = 23 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 23 + int(math.sin(angle) * 9)
            pygame.draw.line(ring, (*_NS_vhyssarion.PALETTE["toxic_light"], 210),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vhyssarion.PALETTE["toxic_hot"], _NS_vhyssarion._alpha(140 * pulse)),
                                (15, 10, 100, 30), 1)
        surface.blit(ring, (x - 65, y - 23))


    # ============================================================
    # SKILL: Q - NOXIOUS PLAGUE (AoE DoT ground field)
    # ============================================================
    def _draw_plague_ground(surface, boss, x, y, timer, phase):
        """Poison field pool on ground at target."""
        tx, ty = _NS_vhyssarion._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))

        if r > 3:
            # Ground pool (dark green).
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], 130),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))


    def _draw_plague_foreground(surface, boss, x, y, timer, phase):
        """Plague bubbles rising + toxic mist swirl."""
        tx, ty = _NS_vhyssarion._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))

        if r < 5:
            return

        # Rising toxic bubbles from pool.
        num_bubbles = 14
        for i in range(num_bubbles):
            bubble_t = (phase * 0.5 + i * 0.11) % 1.0
            # Random position within pool.
            angle = i * math.pi * 2 / num_bubbles + phase * 0.3
            bubble_r = int(r * 0.75 * (0.3 + (i % 3) * 0.25))
            bx = tx + int(math.cos(angle) * bubble_r)
            by = ty + int(math.sin(angle) * bubble_r * 0.4)
            rise_y = by - int(bubble_t * 20)

            alpha = _NS_vhyssarion._alpha(230 * (1 - bubble_t))
            size = 3 - int(bubble_t * 2)
            if size < 1:
                size = 1
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], alpha), (bx, rise_y),
                      size + 1)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha), (bx, rise_y), size)
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha),
                             (bx, rise_y - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                             (bx, rise_y - 1, 1, 1))

        # Central bright core.
        core_pulse = math.sin(phase * 3) * 0.3 + 0.7
        _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], _NS_vhyssarion._alpha(180 * core_pulse)),
                  (tx, ty), 4, 1)
        pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_shine"], (tx, ty, 1, 1))


    # ============================================================
    # SKILL: W - POISON STING (single target enhanced sting)
    # ============================================================
    def _draw_poison_sting_skill(surface, boss, x, y, timer, phase):
        """Bigger, faster poison stinger with beam."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vhyssarion._target_position(boss, x, y)

        if progress < 0.25:
            # Charge in mouth.
            t = progress / 0.25
            mouth_x = x + facing * 22
            mouth_y = y - 18
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_vhyssarion._alpha(180 * (cr + 4 - r) / (cr + 4))
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], alpha),
                          (mouth_x, mouth_y), r)
            _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_mid"], (mouth_x, mouth_y), cr - 2)
            _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_light"], (mouth_x, mouth_y),
                      max(1, cr - 4))
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_shine"],
                             (mouth_x, mouth_y, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 26
            start_y = y - 18

            # Fast beam-like projectile.
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Beam line from start to current position.
            alpha_beam = _NS_vhyssarion._alpha(180 * min(1.0, t * 2))
            pygame.draw.line(surface, (*_NS_vhyssarion.PALETTE["toxic_darkest"], alpha_beam),
                             (start_x, start_y), (bx, by), 4)
            pygame.draw.line(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], alpha_beam),
                             (start_x, start_y), (bx, by), 3)
            pygame.draw.line(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha_beam),
                             (start_x, start_y), (bx, by), 2)
            pygame.draw.line(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha_beam),
                             (start_x, start_y), (bx, by), 1)

            # Bright bolt head.
            angle = math.atan2(ty - start_y, tx - start_x)
            for size in (7, 5, 3, 2):
                _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_darkest"] if size == 7
                          else _NS_vhyssarion.PALETTE["toxic_dark"] if size == 5
                          else _NS_vhyssarion.PALETTE["toxic_mid"] if size == 3
                          else _NS_vhyssarion.PALETTE["toxic_shine"],
                          (bx, by), size)

            # Sparks trailing.
            for i in range(5):
                spark_t = max(0, t - i * 0.05)
                sx = int(start_x + (tx - start_x) * spark_t)
                sy = int(start_y + (ty - start_y) * spark_t)
                sx += int(math.sin(phase * 5 + i) * 3)
                sy += int(math.cos(phase * 5 + i) * 3)
                alpha = _NS_vhyssarion._alpha(220 - i * 35)
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_shine"], alpha),
                                 (sx, sy, 1, 1))

            # Impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(8 + st * 22)
                alpha = _NS_vhyssarion._alpha(240 * (1 - st))
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha), (tx, ty),
                          radius, 3)
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha), (tx, ty),
                          max(1, radius - 6), 2)
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_shine"], alpha), (tx, ty),
                          max(1, radius - 12))
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                                     (ex, ey, 2, 2))


    # ============================================================
    # SKILL: E - GALE (poisonous tornado)
    # ============================================================
    def _draw_gale_ground(surface, boss, x, y, timer, phase):
        """Ring at tornado base."""
        tx, ty = _NS_vhyssarion._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(22 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)


    def _draw_gale_foreground(surface, boss, x, y, timer, phase):
        """Spinning toxic tornado at target location."""
        tx, ty = _NS_vhyssarion._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.05:
            return

        # Tornado height and width.
        height = int(45 * min(1.0, progress * 3))
        max_width = 22

        # Draw stacked ellipses forming tornado (wider at top, narrow at bottom).
        num_layers = 12
        for layer in range(num_layers):
            layer_t = layer / (num_layers - 1)
            # Width tapers.
            width = int(max_width * (0.3 + layer_t * 0.7))
            layer_y = ty - int(layer_t * height)

            # Spin phase per layer.
            spin = phase * 4 - layer * 0.4

            # Draw spinning wisps as multiple offset ellipses.
            for wisp_i in range(3):
                wisp_angle = spin + wisp_i * math.pi * 2 / 3
                wisp_ox = int(math.cos(wisp_angle) * width * 0.3)
                wisp_alpha = _NS_vhyssarion._alpha(180 * (1 - layer_t * 0.4))

                # Dark backing.
                pygame.draw.ellipse(surface,
                                    (*_NS_vhyssarion.PALETTE["toxic_darkest"], wisp_alpha),
                                    (tx - width + wisp_ox, layer_y - 2,
                                     width * 2, 4), 1)
                pygame.draw.ellipse(surface,
                                    (*_NS_vhyssarion.PALETTE["toxic_dark"], wisp_alpha),
                                    (tx - width + wisp_ox + 1, layer_y - 1,
                                     width * 2 - 2, 3), 1)
                pygame.draw.ellipse(surface,
                                    (*_NS_vhyssarion.PALETTE["toxic_mid"], wisp_alpha),
                                    (tx - width + wisp_ox + 2, layer_y,
                                     width * 2 - 4, 2), 1)

            # Bright cyan streaks around edge (spinning).
            for edge_i in range(2):
                edge_angle = spin * 1.5 + edge_i * math.pi
                ex = tx + int(math.cos(edge_angle) * width)
                ey = layer_y
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], 220),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], 220),
                                 (ex, ey, 1, 1))

        # Rising particles inside tornado.
        for i in range(10):
            rise_t = (phase * 0.8 + i * 0.1) % 1.0
            angle = phase * 3 + i * math.pi / 5
            radius = int(max_width * (0.3 + rise_t * 0.7))
            px = tx + int(math.cos(angle) * radius * 0.6)
            py = ty - int(rise_t * height)
            alpha = _NS_vhyssarion._alpha(230 * (1 - rise_t))
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_shine"], alpha),
                             (px, py, 1, 1))

        # Top swirl.
        top_r = int(max_width * 0.7)
        top_y = ty - height
        for i in range(6):
            angle = phase * 5 + i * math.pi / 3
            sx = tx + int(math.cos(angle) * top_r)
            sy = top_y + int(math.sin(angle) * top_r * 0.3)
            alpha = _NS_vhyssarion._alpha(200)
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha),
                             (sx, sy, 1, 1))


    # ============================================================
    # SKILL: R - POISON NOVA (radial expanding ring)
    # ============================================================
    def _draw_nova_ground(surface, boss, x, y, timer, phase):
        """Ring at boss center."""
        for i in range(3):
            r = int(25 + i * 10 + math.sin(phase * 2) * 3)
            alpha = _NS_vhyssarion._alpha(180 - i * 40)
            _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], alpha),
                      (x, y + 34), r, 2)


    def _draw_nova_foreground(surface, boss, x, y, timer, phase):
        """Expanding radial rings of poison outward from boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple expanding rings, each staggered.
        num_rings = 4
        for ring_i in range(num_rings):
            ring_start = ring_i * 0.15
            ring_progress = (progress - ring_start) / (1 - ring_start)
            if ring_progress < 0:
                continue

            max_radius = 130
            current_r = int(ring_progress * max_radius)

            if current_r < 5:
                continue

            # Fade as it expands.
            fade = max(0, 1 - ring_progress * 0.7)
            alpha_ring = _NS_vhyssarion._alpha(240 * fade)

            # Ring elipse (on ground).
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_darkest"], alpha_ring),
                                (x - current_r, y + 34 - current_r // 3,
                                 current_r * 2, current_r * 2 // 3), 4)
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_dark"], alpha_ring),
                                (x - current_r + 2, y + 34 - current_r // 3 + 1,
                                 current_r * 2 - 4, current_r * 2 // 3 - 2), 3)
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha_ring),
                                (x - current_r + 4, y + 34 - current_r // 3 + 2,
                                 current_r * 2 - 8, current_r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_vhyssarion.PALETTE["toxic_light"], alpha_ring),
                                (x - current_r + 6, y + 34 - current_r // 3 + 3,
                                 current_r * 2 - 12, current_r * 2 // 3 - 6), 1)

            # Sparkle particles on ring.
            num_sparks = 16
            for i in range(num_sparks):
                angle = i * math.pi * 2 / num_sparks + phase * 0.5 + ring_i
                sx = x + int(math.cos(angle) * current_r)
                sy = y + 34 + int(math.sin(angle) * current_r * 0.35)
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_hot"], alpha_ring),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhyssarion.PALETTE["toxic_shine"], alpha_ring),
                                 (sx, sy, 1, 1))

        # Central pulse.
        core_pulse = math.sin(phase * 4) * 0.3 + 0.7
        core_r = int(15 * core_pulse * (1 - progress * 0.5))
        if core_r > 1:
            for r in range(core_r, 0, -2):
                alpha = _NS_vhyssarion._alpha(200 * (core_r - r) / core_r)
                _NS_vhyssarion._aacircle(surface, (*_NS_vhyssarion.PALETTE["toxic_mid"], alpha), (x, y), r)
            _NS_vhyssarion._aacircle(surface, _NS_vhyssarion.PALETTE["toxic_light"], (x, y), max(1, core_r // 3))
            pygame.draw.rect(surface, _NS_vhyssarion.PALETTE["toxic_shine"], (x, y, 1, 1))



# ====================================================================
# VAERITH
# ====================================================================
class _NS_vaerith:
    """Namespace vaerith - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Carapace merah crimson (bagian atas tubuh)
        "carapace_darkest": (25, 5, 8),
        "carapace_dark": (75, 12, 18),
        "carapace_mid": (140, 25, 30),
        "carapace_light": (200, 45, 50),
        "carapace_hot": (255, 90, 85),
        "carapace_shine": (255, 180, 165),

        # Chitin ungu-hitam (kaki, perut bawah)
        "chitin_darkest": (8, 4, 12),
        "chitin_dark": (25, 15, 32),
        "chitin_mid": (55, 35, 65),
        "chitin_light": (95, 65, 105),
        "chitin_edge": (140, 100, 150),

        # Eyes merah menyala (cluster)
        "eye_socket": (5, 2, 4),
        "eye_dark": (80, 5, 10),
        "eye_mid": (200, 30, 25),
        "eye_light": (255, 90, 70),
        "eye_glow": (255, 180, 140),
        "eye_white": (255, 240, 220),

        # Fang/taring (bone yellowish)
        "fang_dark": (60, 40, 30),
        "fang_mid": (140, 110, 85),
        "fang_light": (220, 195, 165),
        "fang_shine": (255, 240, 215),

        # Web (silk putih-biru)
        "web_dark": (60, 65, 80),
        "web_mid": (140, 150, 170),
        "web_light": (220, 230, 245),
        "web_glow": (255, 255, 255),

        # Poison green (untuk Insatiable Hunger)
        "poison_darkest": (10, 25, 5),
        "poison_dark": (30, 80, 15),
        "poison_mid": (80, 180, 40),
        "poison_light": (150, 245, 80),
        "poison_hot": (200, 255, 150),

        # Egg colors (untuk R skill)
        "egg_dark": (55, 15, 20),
        "egg_mid": (120, 30, 35),
        "egg_light": (200, 60, 60),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vaerith._clamp(color)
        if _NS_vaerith.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vaerith._clamp(color)
        if _NS_vaerith.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vaerith._clamp(color), points)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vaerith(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vaerith._detect_moving(boss)
        _NS_vaerith._update_vaerith_attack_anim(boss)
        attacking = (
            getattr(boss, "_vae_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_vaerith._draw_web_aura(surface, x, y, pulse)
        _NS_vaerith._draw_web_ground(surface, x, y + 40, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_vaerith._draw_spinweb_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaerith._draw_spawn_eggs_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_vaerith._draw_vaerith_attack(surface, boss, x, y)
        elif moving:
            _NS_vaerith._draw_vaerith_walk(surface, boss, x, y)
        else:
            _NS_vaerith._draw_vaerith_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_vaerith._draw_spiderling_summon(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vaerith._draw_spinweb_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vaerith._draw_insatiable_hunger(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaerith._draw_spawn_spiderlings(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vaerith_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vae_previous_timer", 0))
        active = bool(getattr(boss, "_vae_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vae_attack_active = True
            boss._vae_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vae_attack_frame = int(
                getattr(boss, "_vae_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._vae_attack_active = False
            boss._vae_attack_frame = 0
            active = False

        boss._vae_previous_timer = timer
        boss._vae_attack_progress = (
            min(1.0, getattr(boss, "_vae_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_vae_last_x"):
            boss._vae_last_x = boss.x
            boss._vae_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vae_last_x)
        dy = abs(boss.y - boss._vae_last_y)
        boss._vae_last_x = boss.x
        boss._vae_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vaerith_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_vaerith._draw_shadow(surface, x, y + 44)
        _NS_vaerith._draw_web_strands_below(surface, x, y + 30, boss.pulse)
        _NS_vaerith._draw_vaerith_body(surface, x, y + bob,
                            boss.direction, boss.pulse, "idle")


    def _draw_vaerith_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_vaerith._draw_shadow(surface, x + sway, y + 44)
        _NS_vaerith._draw_web_strands_below(surface, x + sway, y + 30, phase, trail=True,
                                 facing=boss.direction)
        _NS_vaerith._draw_vaerith_body(surface, x + sway, y + bob,
                            boss.direction, phase, "walk")


    def _draw_vaerith_attack(surface, boss, x, y):
        progress = getattr(boss, "_vae_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Lunge forward attack.
        lunge = int(math.sin(progress * math.pi) * 8) * boss.direction
        lift = int(math.sin(progress * math.pi) * 3)
        _NS_vaerith._draw_shadow(surface, x + lunge, y + 44)
        _NS_vaerith._draw_web_strands_below(surface, x + lunge, y + 30, boss.pulse,
                                 intense=True)
        _NS_vaerith._draw_vaerith_body(surface, x + lunge, y - lift,
                            boss.direction, boss.pulse, "attack", progress)
        _NS_vaerith._draw_melee_bite_fx(surface, boss, x + lunge, y - lift, progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_vaerith_body(surface, cx, cy, facing, phase, action,
                            attack_progress=0):
        """Draw spider body: abdomen (back), thorax, head, 8 legs, fangs."""
        # Draw back legs FIRST (so front legs overlap).
        _NS_vaerith._draw_spider_legs(surface, cx, cy, facing, phase, action,
                           attack_progress, back_layer=True)

        # Abdomen (large rear body).
        _NS_vaerith._draw_spider_abdomen(surface, cx - facing * 8, cy + 4, facing, phase)

        # Thorax (middle body).
        _NS_vaerith._draw_spider_thorax(surface, cx, cy, facing, phase)

        # Head with eyes and fangs.
        head_lunge = 0
        if action == "attack":
            head_lunge = int(math.sin(attack_progress * math.pi) * 4) * facing
        _NS_vaerith._draw_spider_head(surface, cx + facing * 10 + head_lunge, cy + 2,
                           facing, phase, action, attack_progress)

        # Draw front legs LAST (overlap abdomen).
        _NS_vaerith._draw_spider_legs(surface, cx, cy, facing, phase, action,
                           attack_progress, back_layer=False)


    def _draw_spider_abdomen(surface, cx, cy, facing, phase):
        """Large bulbous rear body dengan carapace segments."""
        breath = math.sin(phase * 0.8) * 1

        # Main abdomen shape (oval, bulbous).
        abdomen = [
            (cx - 18, cy),
            (cx - 20, cy - 8),
            (cx - 16, cy - 14),
            (cx - 8, cy - 17),
            (cx + 4, cy - 16),
            (cx + 10, cy - 12),
            (cx + 12, cy - 4),
            (cx + 10, cy + 6),
            (cx + 4, cy + 12),
            (cx - 6, cy + 13),
            (cx - 14, cy + 10),
            (cx - 19, cy + 4),
        ]
        # Shadow.
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in abdomen])
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["chitin_darkest"], abdomen)

        # Darker underside (ungu-hitam).
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["chitin_dark"], [
            (cx - 17, cy),
            (cx - 15, cy + 8),
            (cx - 6, cy + 12),
            (cx + 4, cy + 11),
            (cx + 10, cy + 4),
            (cx + 11, cy - 2),
            (cx + 9, cy - 10),
            (cx - 2, cy - 14),
            (cx - 14, cy - 12),
            (cx - 18, cy - 4),
        ])

        # Crimson carapace top plates (segmented).
        for i, plate in enumerate([
            # Top main plate
            [(cx - 15, cy - 8), (cx - 8, cy - 15), (cx + 2, cy - 14),
             (cx + 8, cy - 8), (cx + 4, cy - 4), (cx - 8, cy - 4)],
            # Left side plate
            [(cx - 15, cy - 4), (cx - 8, cy - 4), (cx - 10, cy + 4),
             (cx - 16, cy + 2)],
            # Right side plate
            [(cx + 4, cy - 4), (cx + 9, cy - 4), (cx + 8, cy + 4),
             (cx + 2, cy + 6)],
            # Center bottom plate
            [(cx - 8, cy - 2), (cx + 4, cy - 2), (cx + 2, cy + 8),
             (cx - 6, cy + 8)],
        ]):
            _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_darkest"],
                  [(p[0] + 1, p[1] + 1) for p in plate])
            _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_dark"], plate)
            # Highlight inner plate.
            inner = [(int((p[0] + plate[(idx + 1) % len(plate)][0]) / 2 * 0.3
                           + p[0] * 0.7),
                      int((p[1] + plate[(idx + 1) % len(plate)][1]) / 2 * 0.3
                           + p[1] * 0.7))
                     for idx, p in enumerate(plate)]
            _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_mid"], inner)

        # Glowing red highlights on carapace top.
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for hx, hy in [(cx - 6, cy - 10), (cx + 2, cy - 11),
                        (cx - 10, cy - 4), (cx + 5, cy - 4)]:
            r = 2
            for radius in range(r + 2, 0, -1):
                alpha = _NS_vaerith._alpha(120 * (r + 2 - radius) / (r + 2) * pulse)
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["carapace_hot"], alpha),
                          (hx, hy), radius)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_light"], (hx, hy, 1, 1))

        # Central spider marking (angular red pattern on back).
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_hot"], [
            (cx - 4, cy - 12),
            (cx, cy - 14),
            (cx + 4, cy - 12),
            (cx + 2, cy - 8),
            (cx, cy - 6),
            (cx - 2, cy - 8),
        ])
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_shine"], [
            (cx - 2, cy - 12),
            (cx, cy - 13),
            (cx + 2, cy - 12),
            (cx, cy - 9),
        ])

        # Chitin ridges (dark lines separating plates).
        pygame.draw.line(surface, _NS_vaerith.PALETTE["chitin_darkest"],
                         (cx - 10, cy - 4), (cx - 12, cy + 8), 1)
        pygame.draw.line(surface, _NS_vaerith.PALETTE["chitin_darkest"],
                         (cx + 5, cy - 4), (cx + 7, cy + 8), 1)
        pygame.draw.line(surface, _NS_vaerith.PALETTE["chitin_darkest"],
                         (cx - 8, cy - 2), (cx + 4, cy - 2), 1)

        # Rim highlight (top edge sheen).
        for hx, hy in [(cx - 10, cy - 13), (cx - 4, cy - 15),
                        (cx + 3, cy - 14), (cx + 8, cy - 10)]:
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_shine"], (hx, hy, 1, 1))


    def _draw_spider_thorax(surface, cx, cy, facing, phase):
        """Middle body segment connecting abdomen and head."""
        # Shadow.
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["shadow_deep"], (cx + 1, cy + 1), 9)

        # Main thorax.
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_darkest"], (cx, cy), 9)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_dark"], (cx - 1, cy - 1), 8)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_darkest"], (cx, cy - 1), 7)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_dark"], (cx + facing, cy - 2), 6)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_mid"], (cx + facing, cy - 2), 4)

        # Highlight.
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_light"], (cx + facing * 2, cy - 3), 2)
        pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_shine"],
                         (cx + facing * 2, cy - 3, 1, 1))

        # Segment ridge (line between abdomen and thorax).
        pygame.draw.arc(surface, _NS_vaerith.PALETTE["chitin_darkest"],
                        (cx - 10, cy - 10, 20, 20),
                        math.pi * 0.3, math.pi * 0.7, 1)


    def _draw_spider_head(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Head/cephalothorax dengan cluster mata dan fangs."""
        # Head shape (rounded, slightly smaller than thorax).
        head_shape = [
            (cx - 6, cy - 5),
            (cx - 2, cy - 8),
            (cx + 4 * facing, cy - 8),
            (cx + 8 * facing, cy - 4),
            (cx + 9 * facing, cy),
            (cx + 7 * facing, cy + 5),
            (cx + 2 * facing, cy + 7),
            (cx - 4, cy + 6),
            (cx - 7, cy + 2),
        ]
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in head_shape])
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["chitin_darkest"], head_shape)
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_darkest"], [
            (cx - 4, cy - 4),
            (cx + 6 * facing, cy - 6),
            (cx + 7 * facing, cy - 2),
            (cx + 5 * facing, cy + 4),
            (cx - 2, cy + 5),
            (cx - 5, cy + 1),
        ])
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_dark"], [
            (cx - 2, cy - 3),
            (cx + 5 * facing, cy - 5),
            (cx + 6 * facing, cy),
            (cx + 3 * facing, cy + 3),
            (cx - 1, cy + 3),
        ])
        _NS_vaerith._poly(surface, _NS_vaerith.PALETTE["carapace_mid"], [
            (cx, cy - 3),
            (cx + 4 * facing, cy - 4),
            (cx + 5 * facing, cy),
            (cx + 2 * facing, cy + 2),
        ])

        # CLUSTER MATA (8 mata seperti spider) - arranged in 2 rows.
        _NS_vaerith._draw_spider_eyes(surface, cx, cy, facing, phase)

        # FANGS (chelicerae) - dua taring besar di depan.
        _NS_vaerith._draw_spider_fangs(surface, cx + 6 * facing, cy + 4, facing, phase,
                           action, attack_progress)


    def _draw_spider_eyes(surface, cx, cy, facing, phase):
        """8 glowing red eyes arranged in cluster."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Eye positions (2 rows of 4, mirrored for facing).
        # Row 1 (top, bigger main eyes)
        main_eyes = [
            (cx + 2 * facing, cy - 4, 2),   # main center-left
            (cx + 5 * facing, cy - 4, 2),   # main center-right (largest)
        ]
        # Row 2 (smaller secondary eyes)
        small_eyes = [
            (cx - 1 * facing, cy - 3, 1),
            (cx + 1 * facing, cy - 2, 1),
            (cx + 4 * facing, cy - 1, 1),
            (cx + 7 * facing, cy - 2, 1),
            (cx + 3 * facing, cy - 6, 1),
            (cx + 6 * facing, cy - 6, 1),
        ]

        # Draw small eyes first.
        for ex, ey, r in small_eyes:
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["eye_socket"],
                             (ex - r, ey - r, r * 2 + 1, r * 2 + 1))
            alpha = _NS_vaerith._alpha(230 * pulse)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["eye_mid"], alpha), (ex, ey), r)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["eye_light"], (ex, ey, 1, 1))

        # Draw main eyes with glow.
        for ex, ey, r in main_eyes:
            # Deep socket.
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["eye_socket"],
                             (ex - r - 1, ey - r, r * 2 + 2, r * 2 + 1))
            # Glow halo.
            for radius in range(r + 3, 0, -1):
                alpha = _NS_vaerith._alpha(120 * (r + 3 - radius) / (r + 3) * pulse)
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["eye_mid"], alpha), (ex, ey), radius)
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["eye_dark"], (ex, ey), r)
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["eye_mid"], (ex, ey), r)
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["eye_light"], (ex - 1, ey - 1), 1)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["eye_white"], (ex - 1, ey - 1, 1, 1))


    def _draw_spider_fangs(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Chelicerae/fangs - two curved fangs at front."""
        # Base (mouth part).
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_darkest"], (cx, cy), 3)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_dark"], (cx, cy - 1), 2)

        # Fangs open wider during attack.
        if action == "attack":
            open_amt = math.sin(attack_progress * math.pi) * 4
        else:
            open_amt = math.sin(phase * 0.4) * 1

        for side in (-1, 1):
            # Fang base.
            base_x = cx
            base_y = cy + 1
            # Fang tip curves down and outward.
            tip_x = cx + int((3 + open_amt * 0.5) * facing) + int(side * open_amt)
            tip_y = cy + 8

            # Multi-segment curved fang.
            prev = (base_x, base_y)
            for step in range(1, 5):
                t = step / 4
                # Bezier curve.
                mid_x = base_x + int((tip_x - base_x) * 0.6) + int(side * 2)
                mid_y = base_y + int((tip_y - base_y) * 0.4)
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * tip_y)
                width = max(1, 4 - step)

                _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), width + 1)
                _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["fang_dark"], prev, (bx, by), width)
                if step < 3:
                    _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["fang_mid"], prev, (bx, by),
                            max(1, width - 1))
                else:
                    _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["fang_light"], prev, (bx, by),
                            max(1, width - 1))
                prev = (bx, by)

            # Sharp fang tip.
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["fang_light"], prev, 1)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["fang_shine"],
                             (prev[0], prev[1] - 1, 1, 1))

            # Venom drip during attack.
            if action == "attack" and attack_progress > 0.5:
                drip_t = (attack_progress - 0.5) * 2
                drip_y = prev[1] + int(drip_t * 8)
                drip_alpha = _NS_vaerith._alpha(220 * (1 - drip_t * 0.5))
                pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["poison_dark"], drip_alpha),
                                 (prev[0], drip_y, 1, 2))
                pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["poison_mid"], drip_alpha),
                                 (prev[0], drip_y, 1, 1))


    def _draw_spider_legs(surface, cx, cy, facing, phase, action,
                           attack_progress, back_layer=True):
        """8 legs, articulated with joints. Split between back layer and front."""
        # Leg configs: (base_offset_x, base_offset_y, angle_out, length, phase_offset)
        # Legs arranged: 4 on each side (2 front, 2 back per side)

        if back_layer:
            # Back 4 legs (behind body).
            leg_configs = [
                # Left side back
                (-14, -2, math.pi * 0.85, 22, 0.0),
                (-16, 2, math.pi * 0.95, 24, 0.5),
                # Right side back
                (-14, -2, math.pi * 0.15, 22, 0.25),
                (-16, 2, math.pi * 0.05, 24, 0.75),
            ]
        else:
            # Front 4 legs (in front of body, more prominent).
            leg_configs = [
                # Left side front
                (4, -2, math.pi * 0.65, 26, 0.1),
                (8, 2, math.pi * 0.75, 24, 0.6),
                # Right side front
                (4, -2, math.pi * 0.35, 26, 0.35),
                (8, 2, math.pi * 0.25, 24, 0.85),
            ]

        for i, (bx_off, by_off, base_angle, length, ph_off) in enumerate(leg_configs):
            # Determine side.
            if base_angle > math.pi / 2:
                side = -1  # left
            else:
                side = 1  # right

            # Base attaches to thorax.
            base_x = cx + bx_off * facing
            base_y = cy + by_off

            # Animation: legs step during walk, wave during idle.
            if action == "walk":
                step = math.sin(phase * 1.5 + ph_off * math.pi * 2) * 4
                lift = max(0, math.sin(phase * 1.5 + ph_off * math.pi * 2)) * 3
            elif action == "attack":
                # Front legs raise during attack.
                if not back_layer and i < 2:
                    step = -math.sin(attack_progress * math.pi) * 4
                    lift = math.sin(attack_progress * math.pi) * 6
                else:
                    step = 0
                    lift = 0
            else:
                # Idle: gentle wave.
                step = math.sin(phase * 0.5 + ph_off * math.pi * 2) * 1.5
                lift = 0

            # Joint 1 (knee) - up and out.
            joint_x = base_x + int(math.cos(base_angle) * length * 0.45 * facing)
            joint_y = base_y - int(math.sin(base_angle) * length * 0.5) - int(lift)

            # Joint 2 (foot) - down to ground.
            tip_x = base_x + int(math.cos(base_angle) * length * facing) + int(step)
            tip_y = base_y + int(math.sin(base_angle) * length * 0.3) + 8

            _NS_vaerith._draw_spider_leg_segment(surface, base_x, base_y, joint_x, joint_y,
                                      tip_x, tip_y, phase, front=not back_layer)


    def _draw_spider_leg_segment(surface, x1, y1, x2, y2, x3, y3, phase,
                                  front=False):
        """Draw articulated 3-point leg (base -> knee -> foot)."""
        # Segment 1 (base to knee): thicker
        thickness1 = 4 if front else 3
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), thickness1 + 1)
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_darkest"], (x1, y1), (x2, y2), thickness1)
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_dark"], (x1, y1), (x2, y2),
                max(1, thickness1 - 1))
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_mid"], (x1, y1), (x2, y2),
                max(1, thickness1 - 2))
        if front:
            _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_edge"], (x1, y1 - 1), (x2, y2 - 1), 1)

        # Knee joint (dark ball).
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["shadow_deep"], (x2 + 1, y2 + 1), 3)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_darkest"], (x2, y2), 3)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_darkest"], (x2, y2 - 1), 2)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_dark"], (x2, y2 - 1), 1)
        # Small red glow at knee.
        pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_hot"], (x2, y2 - 1, 1, 1))

        # Segment 2 (knee to foot): thinner, tapering.
        thickness2 = 3 if front else 2
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["shadow_deep"],
                (x2 + 1, y2 + 1), (x3 + 1, y3 + 1), thickness2 + 1)
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_darkest"], (x2, y2), (x3, y3), thickness2)
        _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_dark"], (x2, y2), (x3, y3),
                max(1, thickness2 - 1))
        if front:
            _NS_vaerith._aaline(surface, _NS_vaerith.PALETTE["chitin_mid"], (x2, y2), (x3, y3), 1)

        # Sharp foot tip.
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_darkest"], (x3, y3), 2)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_dark"], (x3, y3), 1)
        pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_dark"], (x3, y3, 1, 1))


    # ============================================================
    # MELEE ATTACK FX
    # ============================================================
    def _draw_melee_bite_fx(surface, boss, x, y, progress):
        """FX for melee bite: slash arcs + impact when fangs connect."""
        if progress < 0.4:
            return

        facing = boss.direction
        tx, ty = _NS_vaerith._target_position(boss, x, y)

        # Distance-based: only show impact if target is close (melee range).
        dist = math.hypot(tx - x, ty - y)
        if dist > 160:
            return

        if progress > 0.5 and progress < 0.85:
            t = (progress - 0.5) / 0.35

            # Slash arcs (curved cuts).
            for i in range(2):
                arc_offset = i * 8 - 4
                arc_x = x + facing * (22 + int(t * 8))
                arc_y = y + arc_offset
                radius = int(6 + t * 10)
                alpha = _NS_vaerith._alpha(220 * (1 - t))
                # Arc slash lines.
                for a in range(3):
                    angle_start = math.pi * (0.2 + a * 0.1)
                    angle_end = math.pi * (0.8 - a * 0.1)
                    points = []
                    for s in range(6):
                        ang = angle_start + (angle_end - angle_start) * s / 5
                        if facing < 0:
                            ang = math.pi - ang
                        px = arc_x + int(math.cos(ang) * radius)
                        py = arc_y + int(math.sin(ang) * radius * 0.6)
                        points.append((px, py))
                    if len(points) > 1:
                        for j in range(len(points) - 1):
                            pygame.draw.line(surface,
                                             (*_NS_vaerith.PALETTE["carapace_hot"], alpha),
                                             points[j], points[j + 1], 2)
                            pygame.draw.line(surface,
                                             (*_NS_vaerith.PALETTE["carapace_shine"], alpha),
                                             points[j], points[j + 1], 1)

            # Impact burst on target.
            if progress > 0.65:
                burst_t = (progress - 0.65) / 0.20
                burst_r = int(8 + burst_t * 14)
                burst_alpha = _NS_vaerith._alpha(230 * (1 - burst_t))
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["carapace_hot"], burst_alpha),
                          (tx, ty), burst_r, 2)
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["carapace_shine"], burst_alpha),
                          (tx, ty), max(1, burst_r - 4), 1)
                # Radial spikes.
                for i in range(8):
                    angle = i * math.pi / 4
                    ex = tx + int(math.cos(angle) * burst_r)
                    ey = ty + int(math.sin(angle) * burst_r * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_vaerith.PALETTE["carapace_light"], burst_alpha),
                                     (tx, ty), (ex, ey), 1)
                # Venom splash particles.
                for i in range(5):
                    sx = tx + int(math.cos(i * 1.3 + progress * 8) * burst_r)
                    sy = ty + int(math.sin(i * 1.3 + progress * 8) * burst_r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_vaerith.PALETTE["poison_mid"], burst_alpha),
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_vaerith.PALETTE["poison_hot"], burst_alpha),
                                     (sx, sy, 1, 1))


    # ============================================================
    # FLOATING WEB STRANDS (below body - "float" style)
    # ============================================================
    def _draw_web_strands_below(surface, cx, cy, phase, trail=False,
                                  facing=1, intense=False):
        """Silk web strands hanging/floating like Malzareth's void wisps."""
        strength = 1.5 if intense else 1.0

        # Dark mist below.
        mist = pygame.Surface((120, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(28, 3, -3):
            alpha = _NS_vaerith._alpha((28 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vaerith.PALETTE["chitin_darkest"], alpha),
                    (60 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Web strands hanging down (silk threads).
        for i, offset in enumerate((-20, -10, 0, 10, 20, -15, 15)):
            strand_len = 18 + int(math.sin(phase * 0.5 + i) * 4)
            sway = math.sin(phase * 0.8 + i * 0.4) * 3
            sx = cx + offset
            sy_start = cy + 4
            sy_end = cy + 4 + strand_len

            # Curved strand.
            points = []
            for step in range(6):
                t = step / 5
                px = sx + int(sway * t)
                py = sy_start + int(strand_len * t)
                points.append((px, py))

            # Dark backing.
            for j in range(len(points) - 1):
                pygame.draw.line(surface, _NS_vaerith.PALETTE["web_dark"],
                                 points[j], points[j + 1], 1)
            # Highlight (bright silk).
            alpha = _NS_vaerith._alpha(180 * strength)
            for j in range(len(points) - 1):
                pygame.draw.line(surface, (*_NS_vaerith.PALETTE["web_mid"], alpha),
                                 points[j], points[j + 1], 1)

            # Small silk droplet at end.
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["web_mid"], points[-1], 1)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["web_light"],
                             (points[-1][0], points[-1][1], 1, 1))

        # Floating silk particles.
        for i in range(6):
            sp_t = (phase * 0.6 + i * 0.2) % 1.0
            ex = cx - 24 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 8 - int(sp_t * 20)
            alpha = _NS_vaerith._alpha(200 * (1 - sp_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["web_light"], alpha),
                                 (ex, ey, 1, 1))

        # Small spiderlings crawling in mist (tiny detail).
        for i in range(3):
            crawl_t = (phase * 0.4 + i * 0.33) % 1.0
            cx_ = cx - 30 + int(crawl_t * 60)
            cy_ = cy + 10 + int(math.sin(phase + i) * 2)
            alpha = _NS_vaerith._alpha(180 * strength)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["carapace_dark"], alpha), (cx_, cy_), 2)
            pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["eye_light"], alpha), (cx_, cy_, 1, 1))
            # Tiny legs.
            for lx in (-2, -1, 1, 2):
                pygame.draw.line(surface, (*_NS_vaerith.PALETTE["chitin_dark"], alpha),
                                 (cx_, cy_), (cx_ + lx, cy_ + 1), 1)

        # Trail behind if moving.
        if trail:
            for i in range(4):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vaerith._alpha(140 - i * 30)
                if alpha <= 0:
                    continue
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["chitin_dark"], alpha),
                          (sx, sy), max(2, 5 - i))
                pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["web_mid"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 24), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 90 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 6, 100, 12))
        # Red inner shadow.
        pygame.draw.ellipse(shadow, (60, 15, 20, 100), (12, 8, 86, 8))
        surface.blit(shadow, (x - 55, y - 12))


    def _draw_web_aura(surface, x, y, phase):
        """Web-tinged aura with crimson glow."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((180, 130), pygame.SRCALPHA)
        for radius in range(75, 5, -5):
            alpha = _NS_vaerith._alpha((75 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_vaerith._aacircle(aura, (*_NS_vaerith.PALETTE["chitin_darkest"], alpha),
                          (90, 65), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_vaerith._alpha((45 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_vaerith._aacircle(aura, (*_NS_vaerith.PALETTE["carapace_darkest"], alpha),
                          (90, 65), radius)
        surface.blit(aura, (x - 90, y - 65))

        # Floating crimson embers.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            radius = 30 + int(math.sin(phase + i) * 8)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_hot"], (sx, sy, 1, 1))


    def _draw_web_ground(surface, x, y, phase, skill):
        """Web pattern ground ring with crimson runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)

        # Outer web ring.
        pygame.draw.ellipse(ring, (*_NS_vaerith.PALETTE["web_dark"], 200),
                            (5, 14, 130, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_vaerith.PALETTE["web_mid"], 180),
                            (12, 16, 116, 16), 1)

        # Radial web spokes.
        for i in range(8):
            angle = i * math.pi / 4
            x1 = 70 + int(math.cos(angle) * 20)
            y1 = 23 + int(math.sin(angle) * 6)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 23 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vaerith.PALETTE["web_mid"], 160), (x1, y1), (x2, y2), 1)

        # Concentric web arcs.
        for r in (30, 45, 58):
            pygame.draw.ellipse(ring, (*_NS_vaerith.PALETTE["web_dark"], 140),
                                (70 - r, 23 - r // 4, r * 2, r // 2), 1)

        # Crimson runes.
        for i in range(4):
            angle = phase * 0.3 + i * math.pi / 2
            x1 = 70 + int(math.cos(angle) * 40)
            y1 = 23 + int(math.sin(angle) * 8)
            pygame.draw.rect(ring, (*_NS_vaerith.PALETTE["carapace_hot"], _NS_vaerith._alpha(200 * pulse)),
                             (x1, y1, 2, 2))

        if skill:
            pygame.draw.ellipse(ring, (*_NS_vaerith.PALETTE["carapace_hot"],
                                        _NS_vaerith._alpha(140 * pulse)),
                                (15, 10, 110, 30), 1)
        surface.blit(ring, (x - 70, y - 23))


    # ============================================================
    # SKILL: Q - SPIDERLING (spawn small spider that runs to target)
    # ============================================================
    def _draw_spiderling_summon(surface, boss, x, y, timer, phase):
        """Spawn spiderling from under boss, runs to target."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vaerith._target_position(boss, x, y)

        if progress < 0.15:
            # Spawn burst under boss.
            t = progress / 0.15
            burst_r = int(3 + t * 10)
            for r in range(burst_r, 0, -1):
                alpha = _NS_vaerith._alpha(200 * (burst_r - r) / burst_r * (1 - t * 0.5))
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["carapace_dark"], alpha),
                          (x, y + 30), r)
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_hot"], (x, y + 30),
                      max(1, burst_r // 3))
        else:
            # Spiderling travels.
            t = (progress - 0.15) / 0.85
            sx = int(x + (tx - x) * t)
            sy = int((y + 30) + (ty - (y + 30)) * t)

            # Web trail.
            for i in range(5):
                trail_t = max(0.0, t - i * 0.08)
                px = int(x + (tx - x) * trail_t)
                py = int((y + 30) + (ty - (y + 30)) * trail_t)
                alpha = _NS_vaerith._alpha(160 - i * 30)
                pygame.draw.line(surface, (*_NS_vaerith.PALETTE["web_mid"], alpha),
                                 (px, py), (px + 2, py + 1), 1)

            # Draw spiderling (small spider).
            _NS_vaerith._draw_small_spiderling(surface, sx, sy, phase, size_mult=1.0)

            # Impact.
            if t > 0.9:
                impact_t = (t - 0.9) / 0.1
                r = int(6 + impact_t * 12)
                alpha = _NS_vaerith._alpha(200 * (1 - impact_t))
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["carapace_hot"], alpha),
                          (tx, ty), r, 2)


    def _draw_small_spiderling(surface, cx, cy, phase, size_mult=1.0):
        """Tiny spider baby - Q skill projectile."""
        s = size_mult
        # Legs (8 tiny).
        for i in range(4):
            angle = math.pi * (0.15 + i * 0.2)
            leg_wave = math.sin(phase * 3 + i) * 1
            for side in (-1, 1):
                lx = cx + int(math.cos(angle) * 4 * s) * side
                ly = cy + int(math.sin(angle) * 3 * s) + int(leg_wave)
                pygame.draw.line(surface, _NS_vaerith.PALETTE["chitin_darkest"],
                                 (cx, cy), (lx, ly), 1)
                pygame.draw.line(surface, _NS_vaerith.PALETTE["chitin_mid"],
                                 (cx, cy), (lx, ly), 1)

        # Body (small oval).
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["shadow_deep"], (cx + 1, cy + 1), int(3 * s))
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["chitin_dark"], (cx, cy), int(3 * s))
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_darkest"], (cx, cy - 1), int(2 * s))
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["carapace_dark"], (cx, cy - 1), max(1, int(2 * s) - 1))
        pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_mid"], (cx, cy - 1, 1, 1))

        # Red eyes.
        pygame.draw.rect(surface, _NS_vaerith.PALETTE["eye_light"], (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_vaerith.PALETTE["eye_light"], (cx + 1, cy - 1, 1, 1))


    # ============================================================
    # SKILL: W - SPIN WEB (sticky web area)
    # ============================================================
    def _draw_spinweb_ground(surface, boss, x, y, timer, phase):
        """Web area on ground at target location."""
        tx, ty = _NS_vaerith._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Web area radius grows then persists.
        if progress < 0.25:
            r = int(40 * progress * 4)
        else:
            r = 40

        if r > 3:
            # Ground shadow of web.
            pygame.draw.ellipse(surface, (*_NS_vaerith.PALETTE["chitin_darkest"], 130),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))


    def _draw_spinweb_foreground(surface, boss, x, y, timer, phase):
        """Draw actual web mesh with radial + concentric strands."""
        tx, ty = _NS_vaerith._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            r = int(40 * progress * 4)
        else:
            r = 40

        if r < 5:
            return

        # Web center anchor.
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["web_dark"], (tx, ty), 2)
        _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["web_light"], (tx, ty), 1)

        alpha_base = _NS_vaerith._alpha(220 * min(1.0, progress * 3))

        # Radial spokes.
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.05
            end_x = tx + int(math.cos(angle) * r)
            end_y = ty + int(math.sin(angle) * r * 0.5)
            pygame.draw.line(surface, (*_NS_vaerith.PALETTE["web_dark"], alpha_base),
                             (tx, ty), (end_x, end_y), 1)
            pygame.draw.line(surface, (*_NS_vaerith.PALETTE["web_mid"], alpha_base),
                             (tx, ty), (end_x, end_y), 1)

        # Concentric spiral rings (web mesh).
        for ring_i, ring_r in enumerate((10, 20, 30, 40)):
            if ring_r > r:
                continue
            alpha = _NS_vaerith._alpha(alpha_base * (1 - ring_i * 0.15))
            # Draw as small line segments between spokes.
            prev = None
            for i in range(13):
                angle = i * math.pi / 6 + phase * 0.05
                px = tx + int(math.cos(angle) * ring_r)
                py = ty + int(math.sin(angle) * ring_r * 0.5)
                if prev is not None:
                    pygame.draw.line(surface, (*_NS_vaerith.PALETTE["web_mid"], alpha),
                                     prev, (px, py), 1)
                prev = (px, py)

        # Sticky droplets.
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.3
            drop_r = 15 + int(math.sin(phase + i) * 8)
            if drop_r > r:
                continue
            dx = tx + int(math.cos(angle) * drop_r)
            dy = ty + int(math.sin(angle) * drop_r * 0.5)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["web_mid"], alpha_base), (dx, dy), 1)
            pygame.draw.rect(surface, _NS_vaerith.PALETTE["web_light"], (dx, dy, 1, 1))


    # ============================================================
    # SKILL: E - INSATIABLE HUNGER (green poison bite, life steal)
    # ============================================================
    def _draw_insatiable_hunger(surface, boss, x, y, timer, phase):
        """Green poison bite - target sends life force back to boss."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        tx, ty = _NS_vaerith._target_position(boss, x, y)

        # Green aura on boss (empowered fangs).
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(20, 3, -3):
            alpha = _NS_vaerith._alpha((20 - r) * 4 * pulse * (1 - progress * 0.3))
            if alpha > 0:
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_dark"], alpha),
                          (x + facing * 8, y + 2), r)

        if progress > 0.15:
            # Life drain stream from target back to boss.
            t = (progress - 0.15) / 0.85

            # Draw curved beam from target to boss.
            num_segments = 12
            for i in range(num_segments):
                seg_t = i / num_segments
                # Curved path (arc).
                mid_x = (x + tx) / 2
                mid_y = min(y, ty) - 20 - int(math.sin(phase * 2) * 5)

                # Bezier curve.
                bx = int((1 - seg_t) ** 2 * tx + 2 * (1 - seg_t) * seg_t * mid_x
                         + seg_t ** 2 * x)
                by = int((1 - seg_t) ** 2 * ty + 2 * (1 - seg_t) * seg_t * mid_y
                         + seg_t ** 2 * y)

                # Flow animation.
                flow_phase = (phase * 4 - seg_t * 5) % 1.0
                alpha = _NS_vaerith._alpha(230 * flow_phase * (1 - progress * 0.5))

                r_bit = int(3 + math.sin(seg_t * math.pi) * 2)
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_darkest"], alpha),
                          (bx, by), r_bit + 1)
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_dark"], alpha),
                          (bx, by), r_bit)
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_mid"], alpha),
                          (bx, by), max(1, r_bit - 1))
                _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_light"], alpha),
                          (bx, by), max(1, r_bit - 2))
                if flow_phase > 0.5:
                    pygame.draw.rect(surface, _NS_vaerith.PALETTE["poison_hot"], (bx, by, 1, 1))

            # Green burst on target.
            burst_r = int(8 + math.sin(phase * 3) * 4)
            burst_alpha = _NS_vaerith._alpha(200 * pulse)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_mid"], burst_alpha),
                      (tx, ty), burst_r, 2)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_light"], burst_alpha),
                      (tx, ty), max(1, burst_r - 3), 1)

            # Health flowing into boss (heal glow).
            heal_alpha = _NS_vaerith._alpha(180 * pulse)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_light"], heal_alpha),
                      (x, y), 12, 2)
            _NS_vaerith._aacircle(surface, (*_NS_vaerith.PALETTE["poison_hot"], heal_alpha), (x, y), 6, 1)

            # Rising green particles from boss (healed).
            for i in range(5):
                p_t = (phase * 0.8 + i * 0.2) % 1.0
                px = x + int(math.sin(phase + i * 2) * 8)
                py = y - int(p_t * 20)
                alpha = _NS_vaerith._alpha(220 * (1 - p_t))
                pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["poison_mid"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_vaerith.PALETTE["poison_hot"], alpha),
                                 (px, py, 1, 1))


    # ============================================================
    # SKILL: R - SPAWN SPIDERLINGS (multiple babies from eggs)
    # ============================================================
    def _draw_spawn_eggs_ground(surface, boss, x, y, timer, phase):
        """Egg sacs on ground before spawn."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Egg sacs pulse.
            pulse = math.sin(phase * 4) * 0.3 + 0.7
            for i, (ox, oy) in enumerate([(-20, 15), (20, 15), (0, 20),
                                            (-30, 5), (30, 5)]):
                appear_t = max(0.0, min(1.0, (progress - i * 0.05) * 5))
                if appear_t <= 0:
                    continue
                egg_r = int(6 * appear_t)
                _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["shadow_deep"],
                          (x + ox + 1, y + oy + 1), egg_r + 1)
                _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["egg_dark"], (x + ox, y + oy), egg_r)
                _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["egg_mid"],
                          (x + ox - 1, y + oy - 1), max(1, egg_r - 1))
                _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["egg_light"],
                          (x + ox - 1, y + oy - 2), max(1, egg_r - 3))
                # Pulsing veins.
                if pulse > 0.7:
                    pygame.draw.rect(surface, _NS_vaerith.PALETTE["carapace_hot"],
                                     (x + ox, y + oy, 1, 1))


    def _draw_spawn_spiderlings(surface, boss, x, y, timer, phase):
        """After eggs hatch, spiderlings scatter."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            return

        # Hatched: spiderlings scatter outward.
        t = (progress - 0.4) / 0.6
        egg_positions = [(-20, 15), (20, 15), (0, 20), (-30, 5), (30, 5)]

        for i, (ox, oy) in enumerate(egg_positions):
            # Cracked egg remains.
            _NS_vaerith._aacircle(surface, _NS_vaerith.PALETTE["egg_dark"],
                      (x + ox, y + oy), 5)
            pygame.draw.line(surface, _NS_vaerith.PALETTE["shadow_deep"],
                             (x + ox - 3, y + oy), (x + ox + 3, y + oy), 1)
            pygame.draw.line(surface, _NS_vaerith.PALETTE["shadow_deep"],
                             (x + ox, y + oy - 3), (x + ox, y + oy + 3), 1)

            # Spiderlings scatter (3 per egg).
            for j in range(3):
                scatter_angle = (i * 0.7 + j * 2.1) % (math.pi * 2)
                scatter_dist = int(t * 40 + j * 3)
                sx = x + ox + int(math.cos(scatter_angle) * scatter_dist)
                sy = y + oy + int(math.sin(scatter_angle) * scatter_dist * 0.5)
                # Little wiggle.
                sx += int(math.sin(phase * 3 + i + j) * 2)

                _NS_vaerith._draw_small_spiderling(surface, sx, sy, phase, size_mult=0.7)


    # ============================================================
    # BROODMOTHER ICON HELPER (for future UI if needed)
    # ============================================================



# ====================================================================
# VHORETHZIR
# ====================================================================
class _NS_vhorethzir:
    """Namespace vhorethzir - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Dark green scales (main body, wings)
        "scale_darkest": (5, 20, 10),
        "scale_dark": (20, 55, 30),
        "scale_mid": (45, 100, 55),
        "scale_light": (85, 155, 90),
        "scale_edge": (140, 200, 130),
        "scale_shine": (200, 240, 190),

        # Belly tan/gold (undersides, snout tip)
        "belly_darkest": (35, 25, 8),
        "belly_dark": (85, 65, 25),
        "belly_mid": (155, 125, 55),
        "belly_light": (215, 185, 105),
        "belly_shine": (250, 230, 160),

        # Toxic yellow-green glow (venom, eyes)
        "toxic_darkest": (20, 30, 5),
        "toxic_dark": (60, 90, 15),
        "toxic_mid": (140, 190, 35),
        "toxic_light": (200, 245, 80),
        "toxic_hot": (240, 255, 150),
        "toxic_shine": (255, 255, 220),

        # Red eye (menyala terang)
        "eye_socket": (5, 2, 2),
        "eye_darkest": (40, 5, 8),
        "eye_dark": (95, 15, 20),
        "eye_mid": (200, 35, 40),
        "eye_light": (255, 90, 80),
        "eye_glow": (255, 200, 160),

        # Fang/bone (aged bone)
        "fang_dark": (60, 45, 25),
        "fang_mid": (150, 125, 80),
        "fang_light": (230, 210, 160),
        "fang_shine": (255, 245, 210),

        # Wing membrane (translucent green)
        "membrane_dark": (15, 40, 20),
        "membrane_mid": (40, 90, 45),
        "membrane_light": (100, 170, 100),
        "membrane_glow": (160, 220, 140),

        # Nether/corruption purple (accents for TRUE BOSS)
        "nether_darkest": (10, 5, 20),
        "nether_dark": (30, 15, 55),
        "nether_mid": (80, 40, 120),
        "nether_light": (150, 100, 200),

        # Poison mist
        "mist_dark": (20, 40, 10),
        "mist_mid": (80, 130, 30),
        "mist_light": (170, 220, 80),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vhorethzir._clamp(color)
        if _NS_vhorethzir.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vhorethzir._clamp(color)
        if _NS_vhorethzir.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vhorethzir._clamp(color), points)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vhorethzir(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vhorethzir._detect_moving(boss)
        _NS_vhorethzir._update_vhz_attack_anim(boss)
        attacking = (
            getattr(boss, "_vhz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind (bigger for TRUE BOSS).
        _NS_vhorethzir._draw_nether_aura(surface, x, y, pulse)
        _NS_vhorethzir._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_vhorethzir._draw_nethertoxin_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhorethzir._draw_viperstrike_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            # Corrosive skin activates on boss location.
            _NS_vhorethzir._draw_corrosive_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_vhorethzir._draw_vhz_attack(surface, boss, x, y)
        elif moving:
            _NS_vhorethzir._draw_vhz_walk(surface, boss, x, y)
        else:
            _NS_vhorethzir._draw_vhz_idle(surface, boss, x, y)

        # Corrosive skin bubble (over body).
        if active_skill == "e":
            _NS_vhorethzir._draw_corrosive_bubble(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_vhorethzir._draw_poison_attack_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vhorethzir._draw_nethertoxin_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhorethzir._draw_viperstrike_foreground(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vhz_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vhz_previous_timer", 0))
        active = bool(getattr(boss, "_vhz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vhz_attack_active = True
            boss._vhz_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vhz_attack_frame = int(
                getattr(boss, "_vhz_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._vhz_attack_active = False
            boss._vhz_attack_frame = 0
            active = False

        boss._vhz_previous_timer = timer
        boss._vhz_attack_progress = (
            min(1.0, getattr(boss, "_vhz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_vhz_last_x"):
            boss._vhz_last_x = boss.x
            boss._vhz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vhz_last_x)
        dy = abs(boss.y - boss._vhz_last_y)
        boss._vhz_last_x = boss.x
        boss._vhz_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vhz_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_vhorethzir._draw_shadow(surface, x, y + 50)
        _NS_vhorethzir._draw_poison_mist(surface, x, y + 34, boss.pulse)
        _NS_vhorethzir._draw_vhz_body(surface, x, y + bob,
                        boss.direction, boss.pulse, "idle")


    def _draw_vhz_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_vhorethzir._draw_shadow(surface, x + sway, y + 50)
        _NS_vhorethzir._draw_poison_mist(surface, x + sway, y + 34, phase, trail=True,
                          facing=boss.direction)
        _NS_vhorethzir._draw_vhz_body(surface, x + sway, y + bob,
                        boss.direction, phase, "walk")


    def _draw_vhz_attack(surface, boss, x, y):
        progress = getattr(boss, "_vhz_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Rear back charge → forward lunge → recovery.
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 5)
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-4 + t * 14)) * boss.direction
            lift = int(5 - t * 7)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(10 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_vhorethzir._draw_shadow(surface, x + lunge, y + 50)
        _NS_vhorethzir._draw_poison_mist(surface, x + lunge, y + 34, boss.pulse, intense=True)
        _NS_vhorethzir._draw_vhz_body(surface, x + lunge, y - lift,
                        boss.direction, boss.pulse, "attack", progress)
        _NS_vhorethzir._draw_poison_venom_projectile(surface, boss, x + lunge, y - lift,
                                       progress)


    # ============================================================
    # BODY (Dragon/Wyrm layout: wings, body horizontal, neck, head, tail)
    # ============================================================
    def _draw_vhz_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw wyrm body: wings back, tail behind, body horizontal, neck, head."""
        # Wings FIRST (behind body).
        _NS_vhorethzir._draw_dragon_wings(surface, cx, cy - 4, facing, phase, action,
                            attack_progress)

        # Tail (curving back-down).
        _NS_vhorethzir._draw_wyrm_tail(surface, cx, cy + 4, facing, phase, action)

        # Main body (horizontal, muscular).
        _NS_vhorethzir._draw_wyrm_body(surface, cx, cy, facing, phase)

        # Neck (curving forward-up).
        neck_lunge = 0
        if action == "attack":
            if attack_progress < 0.4:
                neck_lunge = -int(attack_progress / 0.4 * 4) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                neck_lunge = int((-4 + t * 16)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                neck_lunge = int(12 * (1 - t)) * facing
        _NS_vhorethzir._draw_wyrm_neck(surface, cx + facing * 8, cy - 4, facing, phase,
                         neck_lunge)

        # Head with fangs.
        _NS_vhorethzir._draw_wyrm_head(surface, cx + facing * 22 + neck_lunge, cy - 14,
                         facing, phase, action, attack_progress)


    def _draw_dragon_wings(surface, cx, cy, facing, phase, action,
                            attack_progress):
        """Two large membrane wings behind body (dragon wings)."""
        # Wing beat.
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 4
        else:
            beat = math.sin(phase * 1.2) * 3

        # Draw wings on both sides (both visible in profile-view boss).
        # In HD side-view, we draw a large wing on the FAR side (mostly visible)
        # and a partial wing peeking on the near side.

        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing (bigger, fully visible)
            (1, 0.7, 0.75),   # near wing (smaller, partial)
        ]):
            # Wing base at shoulder.
            base_x = cx - facing * 4
            base_y = cy - 2

            # Wing spans up and BACK.
            # Main spar (top edge).
            spar1_len = int(28 * size_mult)
            spar1_angle = math.pi * 0.65 * side_mult - math.radians(beat)

            # Middle finger.
            spar2_len = int(32 * size_mult)
            spar2_angle = math.pi * 0.85 * side_mult - math.radians(beat * 0.8)

            # Bottom edge.
            spar3_len = int(24 * size_mult)
            spar3_angle = math.pi * 1.05 * side_mult - math.radians(beat * 0.5)

            # Calculate wing tip positions.
            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)

            # Membrane shape.
            membrane_points = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                (int(tip1_x * 0.6 + tip2_x * 0.4),
                 int(tip1_y * 0.6 + tip2_y * 0.4) + int(3 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.6 + tip3_x * 0.4),
                 int(tip2_y * 0.6 + tip3_y * 0.4) + int(3 * size_mult)),
                (tip3_x, tip3_y),
                (base_x - facing * 3, base_y + int(5 * size_mult)),
            ]

            # Draw to alpha surface for translucency.
            wing_surf = pygame.Surface((160, 100), pygame.SRCALPHA)
            offset_x = base_x - 80
            offset_y = base_y - 50
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]

            # Layered membrane.
            _NS_vhorethzir._poly(wing_surf, (*_NS_vhorethzir.PALETTE["membrane_dark"], int(200 * alpha_mult)),
                  local_points)

            # Inner darker fill (concave).
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.8 + cx_local * 0.2),
                     int(p[1] * 0.8 + cy_local * 0.2))
                )
            _NS_vhorethzir._poly(wing_surf, (*_NS_vhorethzir.PALETTE["scale_darkest"], int(180 * alpha_mult)),
                  inner_pts)

            # Membrane texture (mid green with alpha).
            _NS_vhorethzir._poly(wing_surf, (*_NS_vhorethzir.PALETTE["membrane_mid"], int(140 * alpha_mult)),
                  inner_pts)

            # Wing bones/fingers (spar lines) - darker.
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                pygame.draw.line(wing_surf,
                                 (*_NS_vhorethzir.PALETTE["scale_darkest"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_vhorethzir.PALETTE["scale_dark"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_vhorethzir.PALETTE["scale_mid"],
                                  int(180 * alpha_mult)),
                                 bone_base, tip, 1)

                # Claw at end of each finger.
                _NS_vhorethzir._aacircle(wing_surf,
                          (*_NS_vhorethzir.PALETTE["scale_darkest"], int(240 * alpha_mult)),
                          tip, 2)
                _NS_vhorethzir._aacircle(wing_surf,
                          (*_NS_vhorethzir.PALETTE["fang_dark"], int(240 * alpha_mult)),
                          tip, 1)

            # Bright green glow along top edge (magic infusion).
            pygame.draw.line(wing_surf,
                             (*_NS_vhorethzir.PALETTE["membrane_glow"],
                              int(200 * alpha_mult)),
                             bone_base,
                             (tip1_x - offset_x, tip1_y - offset_y), 1)

            # Small sparkle at wing tip.
            pygame.draw.rect(wing_surf,
                             (*_NS_vhorethzir.PALETTE["toxic_light"], int(240 * alpha_mult)),
                             (tip1_x - offset_x, tip1_y - offset_y, 1, 1))

            surface.blit(wing_surf, (offset_x, offset_y))


    def _draw_wyrm_tail(surface, cx, cy, facing, phase, action):
        """Long curving tail behind body ending in spike."""
        # Tail base at rear of body.
        back_dir = -facing
        base_x = cx + back_dir * 14
        base_y = cy + 2

        # Tail wave animation.
        tail_wave = math.sin(phase * 1.2) * 4
        if action == "walk":
            tail_wave = math.sin(phase * 1.5) * 6

        # Multiple curve segments forming long tail (S-curve).
        segments = 8
        points = [(base_x, base_y)]

        for i in range(1, segments + 1):
            t = i / segments
            # Base trajectory: goes back and down, then curls up.
            x_off = int(back_dir * (12 + t * 24))
            y_off = int(3 + t * 8 - t * t * 6)
            # Wave motion.
            wave = math.sin(phase * 1.2 + t * math.pi) * (4 + t * 3)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))

        # Draw tail as tapered segments.
        for i in range(len(points) - 1):
            thickness = max(2, 10 - i)
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
                    (points[i][0] + 2, points[i][1] + 2),
                    (points[i + 1][0] + 2, points[i + 1][1] + 2),
                    thickness + 1)
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["scale_darkest"],
                    points[i], points[i + 1], thickness)
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["scale_dark"],
                    points[i], points[i + 1], max(1, thickness - 2))
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["scale_mid"],
                    (points[i][0], points[i][1] - 1),
                    (points[i + 1][0], points[i + 1][1] - 1),
                    max(1, thickness - 4))

            # Belly (bottom, tan).
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["belly_dark"],
                    (points[i][0], points[i][1] + 1),
                    (points[i + 1][0], points[i + 1][1] + 1),
                    max(1, thickness - 4))
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["belly_mid"],
                    (points[i][0], points[i][1] + 2),
                    (points[i + 1][0], points[i + 1][1] + 2),
                    max(1, thickness - 6))

        # Tail spikes (small dorsal spikes along tail).
        for i in range(1, len(points) - 1, 2):
            spike_size = max(1, 4 - i // 2)
            spike_x = points[i][0]
            spike_y = points[i][1] - max(1, 5 - i)
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_darkest"], [
                (points[i][0] - 2, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 2, points[i][1] - 1),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["toxic_dark"], [
                (points[i][0] - 1, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 1, points[i][1] - 1),
            ])
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"],
                             (spike_x, spike_y, 1, 1))

        # BIG TAIL SPIKE at end (for Viper Strike).
        if len(points) >= 2:
            end = points[-1]
            prev = points[-2]
            spike_angle = math.atan2(end[1] - prev[1], end[0] - prev[0])
            spike_len = 10
            spike_tip = (end[0] + int(math.cos(spike_angle) * spike_len),
                         end[1] + int(math.sin(spike_angle) * spike_len))

            # Perpendicular for spike base.
            perp = spike_angle + math.pi / 2
            base_a = (end[0] + int(math.cos(perp) * 4),
                      end[1] + int(math.sin(perp) * 4))
            base_b = (end[0] - int(math.cos(perp) * 4),
                      end[1] - int(math.sin(perp) * 4))

            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["shadow_deep"], [
                (spike_tip[0] + 2, spike_tip[1] + 2),
                (base_a[0] + 2, base_a[1] + 2),
                (base_b[0] + 2, base_b[1] + 2),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_darkest"],
                  [spike_tip, base_a, base_b])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_dark"], [
                spike_tip,
                (int((spike_tip[0] + base_a[0]) / 2),
                 int((spike_tip[1] + base_a[1]) / 2)),
                end,
            ])
            # Glowing green tip.
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_dark"], spike_tip, 2)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_light"], spike_tip, 1)
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_shine"],
                             (spike_tip[0], spike_tip[1], 1, 1))


    def _draw_wyrm_body(surface, cx, cy, facing, phase):
        """Main body (horizontal muscular oval, wyrm chest)."""
        breath = math.sin(phase * 0.7) * 1

        # Body shape (elongated oval, wider at chest).
        body_shape = [
            (cx - 16, cy),
            (cx - 18, cy - 4),
            (cx - 15, cy - 9),
            (cx - 8, cy - 12),
            (cx + 4, cy - 12),
            (cx + 14, cy - 9),
            (cx + 18, cy - 4),
            (cx + 20, cy),
            (cx + 18, cy + 5),
            (cx + 12, cy + 10),
            (cx + 4, cy + 12),
            (cx - 6, cy + 12),
            (cx - 14, cy + 10),
            (cx - 18, cy + 5),
        ]
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in body_shape])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_darkest"], body_shape)

        # Green scale top (upper 60%).
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_dark"], [
            (cx - 16, cy - 2),
            (cx - 14, cy - 8),
            (cx - 6, cy - 11),
            (cx + 4, cy - 11),
            (cx + 12, cy - 8),
            (cx + 17, cy - 3),
            (cx + 18, cy),
            (cx + 14, cy + 3),
            (cx - 12, cy + 3),
            (cx - 16, cy),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_mid"], [
            (cx - 12, cy - 3),
            (cx - 10, cy - 7),
            (cx - 2, cy - 9),
            (cx + 6, cy - 9),
            (cx + 10, cy - 7),
            (cx + 14, cy - 3),
            (cx + 12, cy),
            (cx - 8, cy),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_light"], [
            (cx - 4, cy - 6),
            (cx + 2, cy - 7),
            (cx + 8, cy - 5),
            (cx + 6, cy - 2),
            (cx - 2, cy - 2),
        ])

        # Belly tan (lower part).
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["belly_dark"], [
            (cx - 14, cy + 3),
            (cx + 14, cy + 3),
            (cx + 18, cy + 5),
            (cx + 12, cy + 10),
            (cx + 4, cy + 12),
            (cx - 6, cy + 12),
            (cx - 14, cy + 10),
            (cx - 18, cy + 5),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["belly_mid"], [
            (cx - 12, cy + 5),
            (cx + 12, cy + 5),
            (cx + 15, cy + 7),
            (cx + 10, cy + 10),
            (cx - 8, cy + 10),
            (cx - 14, cy + 7),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["belly_light"], [
            (cx - 8, cy + 7),
            (cx + 8, cy + 7),
            (cx + 12, cy + 8),
            (cx + 6, cy + 9),
            (cx - 6, cy + 9),
            (cx - 10, cy + 8),
        ])

        # Belly segment stripes (chitinous plates).
        for i, y_off in enumerate((4, 7, 10)):
            alpha_seg = 200 - i * 30
            pygame.draw.line(surface, _NS_vhorethzir.PALETTE["belly_darkest"],
                             (cx - 12 + i * 2, cy + y_off),
                             (cx + 12 - i * 2, cy + y_off), 1)

        # Scale texture (small chevrons on back).
        for row in range(2):
            y_row = cy - 6 + row * 3
            for i, dx in enumerate((-10, -5, 0, 5, 10)):
                offset_x = (row % 2) * 2 - 1
                pygame.draw.line(surface, _NS_vhorethzir.PALETTE["scale_darkest"],
                                 (cx + dx + offset_x - 1, y_row),
                                 (cx + dx + offset_x, y_row - 1), 1)
                pygame.draw.line(surface, _NS_vhorethzir.PALETTE["scale_darkest"],
                                 (cx + dx + offset_x, y_row - 1),
                                 (cx + dx + offset_x + 1, y_row), 1)
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["scale_edge"],
                                 (cx + dx + offset_x, y_row - 1, 1, 1))

        # SPINE SPIKES along back (dorsal ridge).
        for i, x_off in enumerate((-14, -10, -6, -2, 2, 6, 10, 14)):
            spike_wave = math.sin(phase * 0.5 + i * 0.4) * 1
            spike_size = 3 + int((1 - abs(x_off) / 14) * 3)  # taller in middle
            spike_x = cx + x_off
            spike_base_y = cy - 10
            spike_tip_y = spike_base_y - spike_size - int(spike_wave)

            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 2, spike_base_y + 1),
                (spike_x + 2, spike_base_y + 1),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["toxic_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            # Bright tip glow.
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_shine"],
                             (spike_x, spike_tip_y, 1, 1))


    def _draw_wyrm_neck(surface, cx, cy, facing, phase, lunge_offset=0):
        """Curving neck from body to head."""
        base_x = cx
        base_y = cy
        tip_x = cx + facing * 14 + lunge_offset
        tip_y = cy - 12

        prev = (base_x, base_y)
        for step in range(1, 6):
            t = step / 5
            # Curved path.
            mid_x = base_x + int((tip_x - base_x) * 0.5) + facing * 2
            mid_y = base_y - int((base_y - tip_y) * 0.4) - 3
            bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                     + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                     + t ** 2 * tip_y)
            thickness = 10 - step

            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
                    (prev[0] + 2, prev[1] + 2), (bx + 2, by + 2), thickness + 1)
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["scale_darkest"], prev, (bx, by), thickness)
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["scale_dark"], prev, (bx, by),
                    max(1, thickness - 2))
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["scale_mid"],
                    (prev[0], prev[1] - 1), (bx, by - 1),
                    max(1, thickness - 4))

            # Belly on front side.
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["belly_dark"],
                    (prev[0] + facing, prev[1] + 1),
                    (bx + facing, by + 1), max(1, thickness - 4))
            _NS_vhorethzir._aaline(surface, _NS_vhorethzir.PALETTE["belly_mid"],
                    (prev[0] + facing, prev[1] + 2),
                    (bx + facing, by + 2), max(1, thickness - 6))

            # Small dorsal spike per segment.
            spike_x = bx - facing * (thickness // 2)
            spike_y = by - thickness // 2 - 1
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["toxic_dark"], [
                (spike_x, spike_y + 1),
                (spike_x - facing * 2, spike_y - 1),
                (spike_x - facing, spike_y + 1),
            ])
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"],
                             (spike_x - facing * 2, spike_y - 1, 1, 1))

            prev = (bx, by)


    def _draw_wyrm_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Dragon head with elongated snout, horns, fangs, red eye."""
        # Head is elongated (dragon snout).
        # Main head shape.
        head_shape = [
            (cx - 8 * facing, cy + 5),   # back bottom
            (cx - 10 * facing, cy - 1),  # back top
            (cx - 6 * facing, cy - 8),   # crown back
            (cx - 1 * facing, cy - 10),  # top mid
            (cx + 5 * facing, cy - 8),   # top front
            (cx + 12 * facing, cy - 5),  # snout top
            (cx + 18 * facing, cy - 2),  # snout tip top
            (cx + 20 * facing, cy + 2),  # snout tip
            (cx + 18 * facing, cy + 5),  # snout tip bottom
            (cx + 12 * facing, cy + 6),  # snout bottom
            (cx + 4 * facing, cy + 8),   # jaw
            (cx - 4 * facing, cy + 8),   # jaw back
        ]
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in head_shape])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_darkest"], head_shape)

        # Green top head.
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_dark"], [
            (cx - 8 * facing, cy + 3),
            (cx - 9 * facing, cy),
            (cx - 5 * facing, cy - 7),
            (cx + 4 * facing, cy - 8),
            (cx + 11 * facing, cy - 5),
            (cx + 17 * facing, cy - 2),
            (cx + 19 * facing, cy),
            (cx + 15 * facing, cy),
            (cx + 5 * facing, cy - 1),
            (cx - 5 * facing, cy),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_mid"], [
            (cx - 6 * facing, cy - 1),
            (cx - 3 * facing, cy - 6),
            (cx + 5 * facing, cy - 7),
            (cx + 12 * facing, cy - 3),
            (cx + 15 * facing, cy - 1),
            (cx + 5 * facing, cy - 2),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_light"], [
            (cx - 2 * facing, cy - 4),
            (cx + 3 * facing, cy - 6),
            (cx + 8 * facing, cy - 4),
            (cx + 5 * facing, cy - 2),
        ])

        # Snout tan (front tip).
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["belly_dark"], [
            (cx + 12 * facing, cy - 3),
            (cx + 17 * facing, cy - 1),
            (cx + 19 * facing, cy + 1),
            (cx + 18 * facing, cy + 4),
            (cx + 14 * facing, cy + 5),
            (cx + 12 * facing, cy + 3),
        ])
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["belly_mid"], [
            (cx + 13 * facing, cy - 1),
            (cx + 17 * facing, cy + 1),
            (cx + 16 * facing, cy + 3),
            (cx + 13 * facing, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["belly_light"],
                         (cx + 15 * facing, cy, 1, 1))

        # Jaw (bottom, tan-brown).
        _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["belly_dark"], [
            (cx - 3 * facing, cy + 7),
            (cx + 5 * facing, cy + 7),
            (cx + 14 * facing, cy + 5),
            (cx + 12 * facing, cy + 7),
            (cx + 3 * facing, cy + 8),
        ])

        # HORNS/BACK CRESTS (dragon crown).
        _NS_vhorethzir._draw_head_horns(surface, cx, cy, facing, phase)

        # RED EYE (menyala).
        _NS_vhorethzir._draw_dragon_eye(surface, cx + 2 * facing, cy - 2, facing, phase)

        # NOSTRIL.
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
                         (cx + 16 * facing, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_dark"],
                         (cx + 17 * facing, cy - 1, 1, 1))

        # FANGS + MOUTH (opens during attack).
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 5)

        _NS_vhorethzir._draw_dragon_mouth(surface, cx, cy, facing, phase, mouth_open)


    def _draw_head_horns(surface, cx, cy, facing, phase):
        """Curved horns/crest at back of head."""
        # 2 main horns curving back.
        for i, (base_off_x, base_off_y, angle_off, length) in enumerate([
            (-3, -8, math.pi * 0.7, 10),   # top horn
            (-1, -9, math.pi * 0.62, 12),  # tallest horn
            (2, -8, math.pi * 0.55, 9),    # front horn
        ]):
            sway = math.sin(phase * 0.4 + i * 0.4) * 1
            base_x = cx + int(base_off_x * facing)
            base_y = cy + base_off_y
            tip_x = cx + int((base_off_x + math.cos(angle_off) * length
                              * (-1)) * facing)
            tip_y = base_y - int(math.sin(angle_off) * length) + int(sway)

            # Horn shape.
            perp_x = -math.sin(angle_off)
            perp_y = math.cos(angle_off)
            pa_x = base_x + int(perp_x * 2)
            pa_y = base_y + int(perp_y * 2)
            pb_x = base_x - int(perp_x * 2)
            pb_y = base_y - int(perp_y * 2)

            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["scale_darkest"],
                  [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["fang_dark"], [
                (tip_x, tip_y),
                (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                (base_x, base_y),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["fang_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["fang_light"],
                             (tip_x, tip_y, 1, 1))


    def _draw_dragon_eye(surface, cx, cy, facing, phase):
        """Bright red dragon eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        ex = cx + 2 * facing
        ey = cy

        # Deep socket.
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))

        # Glow halo.
        for radius in range(6, 0, -1):
            alpha = _NS_vhorethzir._alpha(90 * (6 - radius) / 6 * pulse)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["eye_mid"], alpha), (ex + 1, ey), radius)

        # Iris.
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["eye_darkest"], (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["eye_dark"], (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["eye_mid"], (ex + 1, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["eye_light"], (ex + 1, ey, 1, 1))
        # Bright core.
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["eye_glow"], (ex + 2, ey, 1, 1))
        # Vertical pupil.
        pygame.draw.line(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
                         (ex + 1, ey - 1), (ex + 1, ey + 1), 1)


    def _draw_dragon_mouth(surface, cx, cy, facing, phase, mouth_open):
        """Mouth with sharp fangs; opens during attack."""
        mouth_y = cy + 4
        mouth_x_start = cx + 4 * facing
        mouth_x_end = cx + 18 * facing

        if mouth_open > 0:
            # Open mouth cavity.
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end, mouth_y + int(mouth_open)),
                (mouth_x_start, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_vhorethzir._poly(surface, _NS_vhorethzir.PALETTE["eye_darkest"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing, mouth_y + int(mouth_open * 0.7) - 1),
            ])

            # Green glow inside (venom brewing).
            glow_r = int(2 + mouth_open * 0.3)
            for r in range(glow_r + 2, 0, -1):
                alpha = _NS_vhorethzir._alpha(180 * (glow_r + 2 - r) / (glow_r + 2))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                          (cx + 12 * facing, mouth_y + int(mouth_open * 0.5)), r)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_mid"],
                      (cx + 12 * facing, mouth_y + int(mouth_open * 0.5)),
                      max(1, glow_r - 1))
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"],
                             (cx + 12 * facing, mouth_y + int(mouth_open * 0.5),
                              1, 1))

            # UPPER FANGS (multiple sharp teeth).
            for i, x_off in enumerate((6, 10, 14)):
                fang_x = cx + int(x_off * facing)
                fang_tip_y = mouth_y + int(mouth_open * 0.85)
                pygame.draw.line(surface, _NS_vhorethzir.PALETTE["fang_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_vhorethzir.PALETTE["fang_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
                # Venom drip.
                if mouth_open > 3:
                    drip_y = fang_tip_y + 2
                    pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_mid"],
                                     (fang_x, drip_y, 1, 2))
                    pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"],
                                     (fang_x, drip_y, 1, 1))

            # LOWER FANGS.
            for i, x_off in enumerate((7, 11, 15)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 2
                pygame.draw.line(surface, _NS_vhorethzir.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y),
                                 (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["fang_mid"],
                                 (fang_x, fang_tip_y, 1, 1))
        else:
            # Closed mouth line with visible fang tips.
            pygame.draw.line(surface, _NS_vhorethzir.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            # Small fang points visible.
            for x_off in (7, 11, 14):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["fang_mid"],
                                 (fang_x, mouth_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["fang_light"],
                                 (fang_x, mouth_y + 2, 1, 1))


    # ============================================================
    # RANGED ATTACK — POISON VENOM PROJECTILE (comet-like)
    # ============================================================
    def _draw_poison_venom_projectile(surface, boss, x, y, progress):
        """Green venom projectile with comet trail."""
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_vhorethzir._target_position(boss, x, y)

        # Launch point at mouth.
        start_x = x + facing * 32
        start_y = y - 12

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Long comet trail.
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vhorethzir._alpha(230 - i * 25)

            size = max(1, 7 - i)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha), (px, py), size)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha), (px, py),
                      max(1, size - 1))
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha), (px, py),
                      max(1, size - 2))
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha), (px, py),
                      max(1, size - 3))

            # Sparks around trail.
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))

        # Bright bolt head.
        _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_darkest"], (bx, by), 8)
        _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_dark"], (bx, by), 6)
        _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_mid"], (bx, by), 4)
        _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_light"], (bx, by), 3)
        _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_hot"], (bx, by), 2)
        _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["white"], (bx, by, 1, 1))

        # Radial glow around head.
        for r in range(12, 3, -2):
            alpha = _NS_vhorethzir._alpha(80 * (12 - r) / 12)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha), (bx, by), r)

        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 24)
            alpha = _NS_vhorethzir._alpha(240 * (1 - st))
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha), (tx, ty),
                      radius + 3, 3)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha), (tx, ty),
                      radius, 3)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha), (tx, ty),
                      max(1, radius - 4), 2)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha), (tx, ty),
                      max(1, radius - 10), 1)

            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_shine"], alpha),
                                 (ex, ey, 1, 1))


    # ============================================================
    # FLOATING POISON MIST
    # ============================================================
    def _draw_poison_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Toxic green mist floating below wyrm."""
        strength = 1.5 if intense else 1.0

        # Mist cloud.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_vhorethzir._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhorethzir.PALETTE["mist_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_vhorethzir._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhorethzir.PALETTE["mist_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising green bubbles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_vhorethzir._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["mist_dark"], alpha), (sx, sy), 3)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["mist_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Yellow embers.
        for i in range(8):
            ember_t = (phase * 0.6 + i * 0.15) % 1.0
            ex = cx - 26 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 24)
            alpha = _NS_vhorethzir._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Nether purple wisps (TRUE BOSS accent).
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 20 + i * 10 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 20)
            alpha = _NS_vhorethzir._alpha(180 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["nether_dark"], alpha), (wx, wy), 2)
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["nether_light"], (wx, wy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vhorethzir._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["mist_dark"], alpha),
                          (sx, sy), max(2, 7 - i))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["mist_mid"], alpha),
                          (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND (TRUE BOSS bigger scale)
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 60, 15, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))


    def _draw_nether_aura(surface, x, y, phase):
        """Large intimidating green + nether purple aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        # Outer aura.
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_vhorethzir._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vhorethzir._aacircle(aura, (*_NS_vhorethzir.PALETTE["mist_dark"], alpha), (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_vhorethzir._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vhorethzir._aacircle(aura, (*_NS_vhorethzir.PALETTE["mist_mid"], alpha), (110, 90), radius)
        # Nether purple inner tint.
        for radius in range(35, 5, -3):
            alpha = _NS_vhorethzir._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vhorethzir._aacircle(aura, (*_NS_vhorethzir.PALETTE["nether_dark"], alpha), (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Floating embers (green + purple mix).
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_vhorethzir.PALETTE["toxic_mid"] if i % 3 != 0 else _NS_vhorethzir.PALETTE["nether_mid"]
            hot_color = _NS_vhorethzir.PALETTE["toxic_hot"] if i % 3 != 0 \
                else _NS_vhorethzir.PALETTE["nether_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))


    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large ground ring with runes (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vhorethzir.PALETTE["mist_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_vhorethzir.PALETTE["toxic_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_vhorethzir.PALETTE["toxic_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_vhorethzir.PALETTE["nether_dark"], 180),
                            (40, 24, 90, 14), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vhorethzir.PALETTE["toxic_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_vhorethzir.PALETTE["toxic_hot"], _NS_vhorethzir._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))


    # ============================================================
    # SKILL: Q - POISON ATTACK (comet-like venom orb)
    # ============================================================
    def _draw_poison_attack_skill(surface, boss, x, y, timer, phase):
        """Enhanced venom orb with brighter, bigger comet trail."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vhorethzir._target_position(boss, x, y)

        if progress < 0.2:
            # Charge in mouth.
            t = progress / 0.2
            mouth_x = x + facing * 28
            mouth_y = y - 12
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_vhorethzir._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha),
                          (mouth_x, mouth_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_vhorethzir._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                          (mouth_x, mouth_y), r)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_mid"], (mouth_x, mouth_y), cr - 2)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_light"], (mouth_x, mouth_y),
                      max(1, cr - 4))
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_shine"], (mouth_x, mouth_y),
                      max(1, cr - 6))

            # Sparks.
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = mouth_x + int(math.cos(angle) * (cr + 3))
                sy = mouth_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 32
            start_y = y - 12
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Extra bright comet trail.
            for i in range(11):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_vhorethzir._alpha(240 - i * 22)

                size = max(1, 9 - i)
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha),
                          (px, py), size)
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                          (px, py), max(1, size - 1))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                          (px, py), max(1, size - 2))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                          (px, py), max(1, size - 3))

                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Huge bright head.
            for r in range(15, 3, -2):
                alpha = _NS_vhorethzir._alpha(100 * (15 - r) / 15)
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha), (bx, by), r)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_darkest"], (bx, by), 10)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_dark"], (bx, by), 8)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_mid"], (bx, by), 5)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_light"], (bx, by), 3)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["white"], (bx, by, 1, 1))

            # Big impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 30)
                alpha = _NS_vhorethzir._alpha(240 * (1 - st))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha),
                          (tx, ty), radius + 4, 3)
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                          (tx, ty), radius, 3)
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                          (tx, ty), max(1, radius - 5), 2)
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                          (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                                     (ex, ey, 2, 2))


    # ============================================================
    # SKILL: W - NETHERTOXIN (corrosive ground fume area)
    # ============================================================
    def _draw_nethertoxin_ground(surface, boss, x, y, timer, phase):
        """Toxic fume pool on ground at target."""
        tx, ty = _NS_vhorethzir._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], 130),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))


    def _draw_nethertoxin_foreground(surface, boss, x, y, timer, phase):
        """Rising toxic fumes."""
        tx, ty = _NS_vhorethzir._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))

        if r < 5:
            return

        # Rising fume columns (thicker than plague bubbles).
        num_columns = 6
        for i in range(num_columns):
            col_angle = i * math.pi * 2 / num_columns + phase * 0.1
            col_dist = int(r * 0.5)
            col_x = tx + int(math.cos(col_angle) * col_dist)
            col_y_base = ty + int(math.sin(col_angle) * col_dist * 0.4)

            # Vertical fume column with layered ellipses rising.
            for layer in range(6):
                layer_t = (phase * 0.6 + i * 0.3 + layer * 0.15) % 1.0
                layer_y = col_y_base - int(layer_t * 22)
                layer_alpha = _NS_vhorethzir._alpha(180 * (1 - layer_t))
                layer_w = int(6 + layer_t * 4)
                layer_h = int(3 + layer_t * 2)

                pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], layer_alpha),
                                    (col_x - layer_w, layer_y - layer_h,
                                     layer_w * 2, layer_h * 2))
                pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], layer_alpha),
                                    (col_x - layer_w + 1, layer_y - layer_h + 1,
                                     layer_w * 2 - 2, layer_h * 2 - 2))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], layer_alpha),
                                 (col_x, layer_y, 1, 1))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], layer_alpha),
                                 (col_x, layer_y - 1, 1, 1))

        # Ground sparkles.
        for i in range(20):
            angle = i * math.pi * 2 / 20 + phase * 0.4
            sp_r = int(r * (0.4 + (i % 3) * 0.2))
            sx = tx + int(math.cos(angle) * sp_r)
            sy = ty + int(math.sin(angle) * sp_r * 0.4)
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_hot"], (sx, sy, 1, 1))


    # ============================================================
    # SKILL: E - CORROSIVE SKIN (aura shield around boss)
    # ============================================================
    def _draw_corrosive_ground(surface, boss, x, y, timer, phase):
        """Rings under boss during corrosive skin."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(30 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_vhorethzir._alpha(200 - i * 60)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                      (x, y + 40), r, 2)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                      (x, y + 40), r, 1)


    def _draw_corrosive_bubble(surface, boss, x, y, timer, phase):
        """Bubble of toxic aura around boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Bubble radius (breathing).
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)

        # Draw bubble as ring (translucent).
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multiple ring layers.
        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_vhorethzir._aacircle(bubble, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha_val),
                      center, r - i, thickness)
            _NS_vhorethzir._aacircle(bubble, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha_val),
                      center, r - i - 1, 1)

        # Rotating sparkles along bubble edge.
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_vhorethzir.PALETTE["toxic_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_vhorethzir.PALETTE["toxic_hot"], (sx, sy, 1, 1))

        # Small toxic bubbles inside (near edge).
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            inner_r = r - 8
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            alpha = _NS_vhorethzir._alpha(180)
            _NS_vhorethzir._aacircle(bubble, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha), (bx, by), 3)
            _NS_vhorethzir._aacircle(bubble, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha), (bx, by), 2)
            pygame.draw.rect(bubble, _NS_vhorethzir.PALETTE["toxic_light"], (bx, by, 1, 1))

        surface.blit(bubble, (x - r - 10, y - r - 10))

        # Extra energy tendrils outward.
        for i in range(6):
            angle = phase * 0.8 + i * math.pi / 3
            end_x = x + int(math.cos(angle) * (r + 8))
            end_y = y + int(math.sin(angle) * (r + 8))
            alpha = _NS_vhorethzir._alpha(150 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                             (x + int(math.cos(angle) * r),
                              y + int(math.sin(angle) * r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_hot"], (end_x, end_y, 1, 1))


    # ============================================================
    # SKILL: R - VIPER STRIKE (massive tail slam beam)
    # ============================================================
    def _draw_viperstrike_ground(surface, boss, x, y, timer, phase):
        """Massive impact circle at target ground."""
        tx, ty = _NS_vhorethzir._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Two-phase: wind-up (small circle grows) → impact (huge burst).
        if progress < 0.4:
            # Wind-up: growing warning circle.
            t = progress / 0.4
            r = int(30 * t)
            alpha = _NS_vhorethzir._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Warning rune circle.
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_light"], (sx, sy, 2, 2))
        else:
            # Post-impact: expanding poison pool.
            t = (progress - 0.4) / 0.6
            r = int(30 + t * 25)
            alpha = _NS_vhorethzir._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))


    def _draw_viperstrike_foreground(surface, boss, x, y, timer, phase):
        """Vertical energy beam slamming down from sky."""
        tx, ty = _NS_vhorethzir._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Wind-up: gathering energy above target (light falling from sky).
            t = progress / 0.4
            # Small energy gathering above target.
            gather_y = ty - int((1 - t) * 60)
            gather_r = int(4 + t * 4)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_vhorethzir._alpha(180 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                          (tx, gather_y), r)
            _NS_vhorethzir._aacircle(surface, _NS_vhorethzir.PALETTE["toxic_light"], (tx, gather_y), gather_r - 2)
            pygame.draw.rect(surface, _NS_vhorethzir.PALETTE["toxic_shine"], (tx, gather_y, 1, 1))

            # Warning glow at ground target.
            alpha_warn = _NS_vhorethzir._alpha(150 * t)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha_warn), (tx, ty), 5, 1)
        elif progress < 0.7:
            # STRIKE PHASE: massive beam from sky to ground.
            t = (progress - 0.4) / 0.3
            # Beam intensity peaks then fades.
            intensity = math.sin(t * math.pi)

            # Beam from top of screen to target.
            beam_top_y = max(0, ty - 200)

            # Multi-layer beam (getting brighter toward center).
            for layer_i, (width, alpha_val) in enumerate([
                (14, 100), (10, 140), (6, 180), (3, 220), (1, 255),
            ]):
                actual_alpha = _NS_vhorethzir._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                color_idx = layer_i
                colors = [
                    _NS_vhorethzir.PALETTE["toxic_darkest"],
                    _NS_vhorethzir.PALETTE["toxic_dark"],
                    _NS_vhorethzir.PALETTE["toxic_mid"],
                    _NS_vhorethzir.PALETTE["toxic_light"],
                    _NS_vhorethzir.PALETTE["toxic_shine"],
                ]
                color = colors[min(color_idx, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, beam_top_y,
                                  width, ty - beam_top_y))

            # Sparkles rising along beam.
            for i in range(15):
                spark_t = (phase * 2 + i * 0.15) % 1.0
                spark_y = ty - int(spark_t * (ty - beam_top_y))
                spark_x = tx + int(math.sin(phase * 5 + i) * 6)
                alpha = _NS_vhorethzir._alpha(240 * intensity * (1 - spark_t * 0.5))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_shine"], alpha),
                                 (spark_x, spark_y, 1, 1))

            # Impact explosion at ground.
            impact_r = int(15 + t * 25)
            impact_alpha = _NS_vhorethzir._alpha(240 * intensity)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_darkest"], impact_alpha),
                      (tx, ty), impact_r + 3, 3)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], impact_alpha),
                      (tx, ty), impact_r, 3)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], impact_alpha),
                      (tx, ty), max(1, impact_r - 6), 2)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], impact_alpha),
                      (tx, ty), max(1, impact_r - 12), 1)
            _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_shine"], impact_alpha),
                      (tx, ty), max(1, impact_r // 4))

            # Radial ground burst.
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_hot"], impact_alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath: lingering poison mist rising.
            t = (progress - 0.7) / 0.3
            for i in range(10):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 20)
                ry = ty - int(rise_t * 30)
                alpha = _NS_vhorethzir._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_dark"], alpha),
                              (rx, ry), 3)
                    _NS_vhorethzir._aacircle(surface, (*_NS_vhorethzir.PALETTE["toxic_mid"], alpha),
                              (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_vhorethzir.PALETTE["toxic_light"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_xirthalis(surface, boss, x, y):
    """Entry point xirthalis."""
    return _NS_xirthalis.draw_xirthalis(surface, boss, x, y)

def draw_vhyssarion(surface, boss, x, y):
    """Entry point vhyssarion."""
    return _NS_vhyssarion.draw_vhyssarion(surface, boss, x, y)

def draw_vaerith(surface, boss, x, y):
    """Entry point vaerith."""
    return _NS_vaerith.draw_vaerith(surface, boss, x, y)

def draw_vhorethzir(surface, boss, x, y):
    """Entry point vhorethzir."""
    return _NS_vhorethzir.draw_vhorethzir(surface, boss, x, y)
