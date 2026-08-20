"""
bosses/level49.py - Semua boss Level 49

Berisi:
  - kairenji   (mini boss - MELEE voidblade, shadow ninja prodigy)
  - karzhul    (mini boss - MELEE fangreaver, werewolf beast-hunter)
  - xerakkuth  (mini boss - RANGED dunehorror, giant desert scorpion)
  - yomigetsu  (TRUE BOSS - RANGED moonreaper, moon demon swordsman)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================================================
# KAIRENJI - MINI BOSS
# ====================================================================================================

class _NS_kairenji:
    """Namespace kairenji - shadow ninja prodigy boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale ninja)
        "skin_darkest": (55, 40, 35),
        "skin_dark": (120, 90, 75),
        "skin_mid": (185, 150, 130),
        "skin_light": (225, 195, 175),
        "skin_shine": (250, 225, 210),

        # Hair (spiky dark black-blue)
        "hair_darkest": (5, 5, 12),
        "hair_dark": (15, 15, 28),
        "hair_mid": (35, 35, 55),
        "hair_light": (65, 65, 90),
        "hair_shine": (110, 110, 140),

        # Ninja outfit (black gi/shirt)
        "cloth_darkest": (4, 4, 8),
        "cloth_dark": (16, 16, 24),
        "cloth_mid": (35, 35, 48),
        "cloth_light": (65, 65, 85),
        "cloth_edge": (100, 100, 125),

        # Chakra purple (Susano'o/void energy)
        "void_darkest": (15, 5, 30),
        "void_dark": (55, 20, 95),
        "void_mid": (130, 55, 200),
        "void_light": (195, 130, 245),
        "void_hot": (230, 190, 255),
        "void_shine": (250, 230, 255),

        # Sharingan red (eyes + reflection)
        "eye_socket": (10, 3, 3),
        "eye_darkest": (55, 5, 8),
        "eye_dark": (135, 15, 20),
        "eye_mid": (220, 40, 50),
        "eye_light": (255, 100, 105),
        "eye_glow": (255, 200, 195),

        # Katana blade (steel)
        "blade_darkest": (12, 12, 18),
        "blade_dark": (55, 55, 68),
        "blade_mid": (145, 145, 165),
        "blade_light": (215, 215, 230),
        "blade_shine": (250, 250, 255),
        "blade_edge": (200, 180, 255),  # tinted purple from chakra

        # Handle/tsuka (dark blue wrap)
        "handle_dark": (10, 12, 30),
        "handle_mid": (35, 45, 85),
        "handle_light": (75, 90, 140),

        # Bronze/gold accents (headband, tsuba)
        "gold_dark": (85, 60, 15),
        "gold_mid": (175, 130, 40),
        "gold_light": (235, 195, 85),
        "gold_shine": (255, 235, 155),

        # Metal (iron plates, small studs)
        "metal_dark": (25, 25, 30),
        "metal_mid": (75, 75, 85),
        "metal_light": (150, 150, 165),
        "metal_shine": (215, 215, 230),

        # Water splash (blue clone effect)
        "water_dark": (5, 40, 85),
        "water_mid": (35, 130, 220),
        "water_light": (130, 210, 255),
        "water_shine": (220, 245, 255),

        # Shadow / bindings
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kairenji._clamp(color)
        if _NS_kairenji.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kairenji._clamp(color)
        if _NS_kairenji.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_kairenji._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 250 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kairenji(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kairenji._detect_moving(boss)
        _NS_kairenji._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_krj_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_kairenji._draw_void_aura(surface, x, y, pulse)
        _NS_kairenji._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_kairenji._draw_shadowclone_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_kairenji._draw_sharingan_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "q":
            _NS_kairenji._draw_susanoo_ground(
                surface, boss, x, y, skill_timer, pulse
            )

        # Body
        if active_skill == "q":
            _NS_kairenji._draw_susanoo_pose(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_kairenji._draw_shadowclone_pose(
                surface, boss, x, y, skill_timer, pulse
            )
        elif attacking:
            _NS_kairenji._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_kairenji._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_kairenji._draw_idle_pose(surface, boss, x, y)

        # Overlays
        if active_skill == "r":
            _NS_kairenji._draw_sharingan_shield(
                surface, boss, x, y, skill_timer, pulse
            )

        # Foreground FX
        if active_skill == "w":
            _NS_kairenji._draw_kotoamatsukami(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "q":
            _NS_kairenji._draw_susanoo_slash(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_kairenji._draw_sharingan_projectiles(
                surface, boss, x, y, skill_timer, pulse
            )

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_krj_prev_timer", 0))
        active = bool(getattr(boss, "_krj_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._krj_attack_active = True
            boss._krj_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._krj_attack_frame = int(
                getattr(boss, "_krj_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._krj_attack_active = False
            boss._krj_attack_frame = 0
            active = False
        boss._krj_prev_timer = timer
        boss._krj_attack_progress = (
            min(1.0, getattr(boss, "_krj_attack_frame", 0) / max(1, cd - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_krj_last_x"):
            boss._krj_last_x = boss.x
            boss._krj_last_y = boss.y
            return False
        dx = abs(boss.x - boss._krj_last_x)
        dy = abs(boss.y - boss._krj_last_y)
        boss._krj_last_x = boss.x
        boss._krj_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (floating movement — ninja hovers)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_kairenji._draw_shadow(surface, x, y + 50)
        _NS_kairenji._draw_float_wisps(surface, x, y + 44, boss.pulse)
        _NS_kairenji._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )

    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.5
        bob = int(math.sin(ph * 1.1) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_kairenji._draw_shadow(surface, x + sway, y + 50)
        _NS_kairenji._draw_float_wisps(
            surface, x + sway, y + 44, ph, trail=True, facing=boss.direction
        )
        _NS_kairenji._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_krj_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Katana slash: draw back → cut forward → recover
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_kairenji._draw_shadow(surface, x + lunge, y + 50)
        _NS_kairenji._draw_float_wisps(
            surface, x + lunge, y + 44, boss.pulse, intense=True
        )
        # Slash trail before body
        _NS_kairenji._draw_slash_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
        _NS_kairenji._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )
        # Hit impact
        _NS_kairenji._draw_slash_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

    def _draw_susanoo_pose(surface, boss, x, y, timer, pulse):
        """Teleport dash pose."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kairenji._target_position(boss, x, y)
        if progress < 0.2:
            # Wind-up: gather chakra
            t = progress / 0.2
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 4)
            bob = int(math.sin(pulse * 0.6) * 2)
            _NS_kairenji._draw_shadow(surface, x + lunge, y + 50)
            _NS_kairenji._draw_float_wisps(
                surface, x + lunge, y + 44, pulse, intense=True
            )
            _NS_kairenji._draw_body(
                surface, x + lunge, y - lift + bob, boss.direction, pulse,
                "attack", 0.2,
            )
        elif progress < 0.55:
            # Teleport dash — draw multiple afterimages between origin and target
            t = (progress - 0.2) / 0.35
            for i in range(5):
                ax = int(x + (tx - x) * (i / 5) * (1 + t * 0.2))
                ay = int(y + (ty - y) * (i / 5))
                aimg = pygame.Surface((120, 120), pygame.SRCALPHA)
                a = _NS_kairenji._alpha(180 - i * 30)
                # Chakra silhouette
                _NS_kairenji._aacircle(
                    aimg, (*_NS_kairenji.PALETTE["void_mid"], a),
                    (60, 60), 22,
                )
                _NS_kairenji._aacircle(
                    aimg, (*_NS_kairenji.PALETTE["void_dark"], a),
                    (60, 60), 16,
                )
                surface.blit(aimg, (ax - 60, ay - 60))
            # Main body at target position
            bx = tx
            by = ty
            _NS_kairenji._draw_shadow(surface, bx, by + 50)
            _NS_kairenji._draw_body(
                surface, bx, by, boss.direction, pulse, "attack", 0.5,
            )
        else:
            # Recovery at target
            t = (progress - 0.55) / 0.45
            bx = tx
            by = ty
            lift = int(3 * (1 - t))
            _NS_kairenji._draw_shadow(surface, bx, by + 50)
            _NS_kairenji._draw_float_wisps(
                surface, bx, by + 44, pulse, intense=True
            )
            _NS_kairenji._draw_body(
                surface, bx, by - lift, boss.direction, pulse, "attack", 0.7,
            )

    def _draw_shadowclone_pose(surface, boss, x, y, timer, pulse):
        """Show multiple clones running alongside the main body."""
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.7) * 4)
        _NS_kairenji._draw_shadow(surface, x, y + 50)
        _NS_kairenji._draw_float_wisps(surface, x, y + 44, pulse, intense=True)
        # 4 shadow clones offset around main
        clone_offsets = [
            (-40, -8, 0.3), (-25, 6, 0.5),
            (25, 6, 0.7), (40, -8, 0.9),
        ]
        for (dx_off, dy_off, ph_off) in clone_offsets:
            fade = math.sin(progress * math.pi + ph_off) * 0.4 + 0.6
            fade = max(0.3, min(1.0, fade))
            alpha_val = _NS_kairenji._alpha(200 * fade)
            clone_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            _NS_kairenji._draw_body(
                clone_surf, 50, 50, boss.direction,
                pulse + ph_off * 2, "idle", alpha=alpha_val,
            )
            surface.blit(clone_surf, (x + dx_off - 50, y + dy_off + bob - 50))
        # Main
        _NS_kairenji._draw_body(
            surface, x, y + bob, boss.direction, pulse, "idle"
        )

    # ============================================================
    # BODY COMPOSITION
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0,
                   alpha=255):
        if alpha < 255:
            temp = pygame.Surface((160, 140), pygame.SRCALPHA)
            _NS_kairenji._draw_body_parts(
                temp, 80, 80, facing, phase, action, progress
            )
            temp.set_alpha(alpha)
            surface.blit(temp, (cx - 80, cy - 80))
        else:
            _NS_kairenji._draw_body_parts(
                surface, cx, cy, facing, phase, action, progress
            )

    def _draw_body_parts(surface, cx, cy, facing, phase, action, progress):
        # Order: cape/scarf back -> hair back -> back arm -> legs ->
        # torso -> katana sheath -> head -> hair front -> front arm+katana
        _NS_kairenji._draw_cape(surface, cx, cy, facing, phase, action)
        _NS_kairenji._draw_hair_back(surface, cx, cy, facing, phase)
        _NS_kairenji._draw_back_arm(surface, cx, cy, facing, phase, action, progress)
        _NS_kairenji._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_kairenji._draw_torso(surface, cx, cy, facing, phase)
        _NS_kairenji._draw_head(surface, cx, cy, facing, phase)
        _NS_kairenji._draw_hair_front(surface, cx, cy, facing, phase)
        _NS_kairenji._draw_headband(surface, cx, cy, facing, phase)
        _NS_kairenji._draw_front_arm_katana(
            surface, cx, cy, facing, phase, action, progress
        )

    # ── LEGS (dangling, floating) ────────────────────────────
    def _draw_legs(surface, cx, cy, facing, phase, action):
        sway = (
            math.sin(phase * 1.4) * 3
            if action == "walk"
            else math.sin(phase * 0.5) * 1.5
        )
        for side in (-1, 1):
            lx = cx + side * 5
            ly = cy + 14
            sw = int(sway * (1 if side > 0 else -1))
            # Thigh
            thigh = [
                (lx - 3, ly - 1), (lx + 3, ly - 1),
                (lx + 4 + sw, ly + 6), (lx - 4 + sw, ly + 6),
            ]
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in thigh])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_darkest"], thigh)
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_dark"], [
                (lx - 2, ly), (lx + 2, ly),
                (lx + 3 + sw, ly + 5), (lx - 3 + sw, ly + 5),
            ])
            # Shin (wrapping cloth)
            shin = [
                (lx - 3 + sw, ly + 6), (lx + 3 + sw, ly + 6),
                (lx + 3 + sw, ly + 14), (lx - 3 + sw, ly + 14),
            ]
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_darkest"], shin)
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_dark"], [
                (lx - 2 + sw, ly + 7), (lx + 2 + sw, ly + 7),
                (lx + 2 + sw, ly + 13), (lx - 2 + sw, ly + 13),
            ])
            # Wrap bands
            for wy in (ly + 8, ly + 11):
                pygame.draw.line(surface, _NS_kairenji.PALETTE["cloth_edge"],
                                 (lx - 3 + sw, wy),
                                 (lx + 3 + sw, wy), 1)
            # Ninja sandals (open-toe boots)
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_darkest"], [
                (lx - 3 + sw, ly + 13), (lx + 3 + sw, ly + 13),
                (lx + 4 + sw + facing, ly + 16),
                (lx - 2 + sw + facing, ly + 16),
            ])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_dark"], [
                (lx - 2 + sw, ly + 14), (lx + 2 + sw, ly + 14),
                (lx + 3 + sw + facing, ly + 15),
            ])
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_edge"],
                             (lx + sw, ly + 14, 1, 1))

    # ── TORSO ────────────────────────────────────────────────
    def _draw_torso(surface, cx, cy, facing, phase):
        # Slim ninja torso
        body = [
            (cx - 9, cy - 8), (cx - 5, cy - 12),
            (cx + 5, cy - 12), (cx + 9, cy - 8),
            (cx + 10, cy), (cx + 9, cy + 8),
            (cx + 5, cy + 14), (cx - 5, cy + 14),
            (cx - 9, cy + 8), (cx - 10, cy),
        ]
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in body])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_darkest"], body)
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_dark"], [
            (cx - 8, cy - 7), (cx - 4, cy - 11), (cx + 4, cy - 11),
            (cx + 8, cy - 7), (cx + 9, cy), (cx + 8, cy + 7),
            (cx + 4, cy + 12), (cx - 4, cy + 12),
            (cx - 8, cy + 7), (cx - 9, cy),
        ])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_mid"], [
            (cx - 6, cy - 5), (cx - 2, cy - 9), (cx + 2, cy - 9),
            (cx + 6, cy - 5), (cx + 7, cy), (cx + 6, cy + 5),
            (cx + 2, cy + 9), (cx - 2, cy + 9),
            (cx - 6, cy + 5), (cx - 7, cy),
        ])
        # V-collar (skin exposed)
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["skin_darkest"], [
            (cx - 3, cy - 11), (cx, cy - 7), (cx + 3, cy - 11),
        ])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["skin_dark"], [
            (cx - 2, cy - 10), (cx, cy - 8), (cx + 2, cy - 10),
        ])
        # Uchiha-style shoulder emblem (red circle on shoulder)
        for side in (-1, 1):
            sx = cx + side * 7
            sy = cy - 4
            _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["eye_darkest"],
                                   (sx, sy), 2)
            _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["eye_dark"],
                                   (sx, sy), 1)
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_mid"],
                             (sx, sy, 1, 1))
        # Sash/belt around waist
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_darkest"],
                         (cx - 10, cy + 8, 20, 4))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["handle_dark"],
                         (cx - 9, cy + 9, 18, 2))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["handle_mid"],
                         (cx - 9, cy + 9, 18, 1))
        # Belt knot
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["handle_dark"],
                         (cx - 3, cy + 8, 6, 5))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["handle_mid"],
                         (cx - 2, cy + 9, 4, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["handle_light"],
                         (cx - 2, cy + 9, 4, 1))
        # Highlight
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_edge"], [
            (cx - 2, cy - 6), (cx + 2, cy - 6),
            (cx + 3, cy - 3), (cx - 3, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_light"],
                         (cx - 1, cy - 5, 2, 1))

    # ── BACK ARM ─────────────────────────────────────────────
    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        back = -facing
        sx = cx + back * 9
        sy = cy - 8
        sway = math.sin(phase * 0.7) * 2
        ex = sx + back * 5
        ey = sy + 10 + int(sway)
        hx = ex + back * 2
        hy = ey + 8
        # Upper arm
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["shadow_deep"],
                             (sx + 1, sy + 2), (ex + 1, ey + 2), 7)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_darkest"],
                             (sx, sy), (ex, ey), 6)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_dark"],
                             (sx, sy), (ex, ey), 4)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_mid"],
                             (sx, sy - 1), (ex, ey - 1), 2)
        # Forearm (skin exposed)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["shadow_deep"],
                             (ex + 1, ey + 2), (hx + 1, hy + 2), 5)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_darkest"],
                             (ex, ey), (hx, hy), 4)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_dark"],
                             (ex, ey), (hx, hy), 3)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_mid"],
                             (ex, ey - 1), (hx, hy - 1), 1)
        # Fist
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               (hx + 1, hy + 1), 3)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["skin_darkest"],
                               (hx, hy), 3)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["skin_dark"],
                               (hx, hy), 2)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))
        # Handseal position (two fingers up during w skill? For now normal fist)

    # ── FRONT ARM + KATANA ───────────────────────────────────
    def _draw_front_arm_katana(surface, cx, cy, facing, phase, action, progress):
        base_angle = -math.pi / 5
        if action == "attack":
            if progress < 0.3:
                t = progress / 0.3
                base_angle = -math.pi / 5 - t * math.pi / 2.3
            elif progress < 0.55:
                t = (progress - 0.3) / 0.25
                base_angle = -math.pi / 5 - math.pi / 2.3 + t * (math.pi * 1.1)
            else:
                t = (progress - 0.55) / 0.45
                base_angle = -math.pi / 5 + (math.pi * 0.65 * (1 - t))
        else:
            base_angle += math.sin(phase * 0.6) * 0.1

        sx = cx + facing * 9
        sy = cy - 8
        arm_len = 16
        hx = sx + int(math.cos(base_angle) * arm_len) * facing
        hy = sy + int(math.sin(base_angle) * arm_len)
        ex = sx + int(math.cos(base_angle) * arm_len * 0.5) * facing
        ey = sy + int(math.sin(base_angle) * arm_len * 0.5) + 2

        # Upper arm
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["shadow_deep"],
                             (sx + 1, sy + 2), (ex + 1, ey + 2), 8)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_darkest"],
                             (sx, sy), (ex, ey), 7)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_dark"],
                             (sx, sy), (ex, ey), 5)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_mid"],
                             (sx, sy - 1), (ex, ey - 1), 3)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_light"],
                             (sx, sy - 2), (ex, ey - 2), 1)
        # Forearm (skin exposed, muscular)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["shadow_deep"],
                             (ex + 1, ey + 2), (hx + 1, hy + 2), 6)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_darkest"],
                             (ex, ey), (hx, hy), 5)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_dark"],
                             (ex, ey), (hx, hy), 4)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_mid"],
                             (ex, ey - 1), (hx, hy - 1), 2)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["skin_light"],
                             (ex, ey - 2), (hx, hy - 2), 1)
        # Wrist wrap
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_darkest"],
                         (hx - 2, hy - 2, 4, 4))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_dark"],
                         (hx - 2, hy - 1, 4, 2))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_mid"],
                         (hx - 2, hy - 1, 4, 1))

        # HAND
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               (hx + 1, hy + 1), 4)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["skin_darkest"],
                               (hx, hy), 4)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["skin_dark"],
                               (hx, hy), 3)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["skin_mid"],
                               (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))

        # KATANA
        _NS_kairenji._draw_katana(surface, hx, hy, facing, phase, base_angle,
                                   action)

    def _draw_katana(surface, hx, hy, facing, phase, arm_angle, action):
        """Long katana blade with tsuba guard and wrapped handle."""
        # Handle direction (opposite of blade)
        # Tsuka (handle) - goes back from hand
        tsuka_len = 6
        tsuka_end_x = hx - int(math.cos(arm_angle) * tsuka_len) * facing
        tsuka_end_y = hy - int(math.sin(arm_angle) * tsuka_len)
        # Handle wraps
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["shadow_deep"],
                             (hx + 1, hy + 1),
                             (tsuka_end_x + 1, tsuka_end_y + 1), 4)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["handle_dark"],
                             (hx, hy), (tsuka_end_x, tsuka_end_y), 3)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["handle_mid"],
                             (hx, hy), (tsuka_end_x, tsuka_end_y), 2)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["handle_light"],
                             (hx, hy - 1), (tsuka_end_x, tsuka_end_y - 1), 1)
        # Handle wrap crosshatch pattern
        for i in range(1, tsuka_len - 1):
            t = i / tsuka_len
            wx = int(hx + (tsuka_end_x - hx) * t)
            wy = int(hy + (tsuka_end_y - hy) * t)
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["handle_dark"],
                             (wx, wy, 1, 2))
        # Pommel (small round at end)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["gold_dark"],
                               (tsuka_end_x, tsuka_end_y), 2)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["gold_mid"],
                               (tsuka_end_x, tsuka_end_y), 1)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["gold_shine"],
                         (tsuka_end_x, tsuka_end_y, 1, 1))

        # Tsuba (guard) - circular disk at hand
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               (hx + 1, hy + 1), 4)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["gold_dark"],
                               (hx, hy), 4)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["gold_mid"],
                               (hx, hy), 3)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["gold_light"],
                               (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["gold_shine"],
                         (hx - 1, hy - 1, 1, 1))

        # BLADE (long, extends from tsuba forward)
        blade_len = 28
        blade_tip_x = hx + int(math.cos(arm_angle) * blade_len) * facing
        blade_tip_y = hy + int(math.sin(arm_angle) * blade_len)
        # Blade base (next to tsuba)
        blade_base_x = hx + int(math.cos(arm_angle) * 4) * facing
        blade_base_y = hy + int(math.sin(arm_angle) * 4)
        # Perpendicular for blade width
        perp = arm_angle + math.pi / 2
        bw = 2
        bp1_x = blade_base_x + int(math.cos(perp) * bw)
        bp1_y = blade_base_y + int(math.sin(perp) * bw)
        bp2_x = blade_base_x - int(math.cos(perp) * bw)
        bp2_y = blade_base_y - int(math.sin(perp) * bw)
        # Blade poly
        blade_pts = [
            (blade_tip_x, blade_tip_y),
            (bp1_x, bp1_y),
            (bp2_x, bp2_y),
        ]
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in blade_pts])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["blade_darkest"], blade_pts)
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["blade_dark"], [
            (blade_tip_x, blade_tip_y),
            (int((bp1_x + blade_base_x) / 2),
             int((bp1_y + blade_base_y) / 2)),
            (blade_base_x, blade_base_y),
        ])
        # Bright edge (top of blade)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["blade_mid"],
                             (blade_base_x, blade_base_y),
                             (blade_tip_x, blade_tip_y), 2)
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["blade_light"],
                             (blade_base_x, blade_base_y),
                             (blade_tip_x, blade_tip_y), 1)
        # Purple chakra tint on edge
        _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["blade_edge"],
                             (int((blade_base_x + blade_tip_x) / 2),
                              int((blade_base_y + blade_tip_y) / 2)),
                             (blade_tip_x, blade_tip_y), 1)
        # Tip shine
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["blade_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        # Chakra glow at blade tip
        for r in range(4, 0, -1):
            a = _NS_kairenji._alpha(120 * (4 - r) / 4)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_mid"], a),
                                   (blade_tip_x, blade_tip_y), r)

    # ── HEAD ─────────────────────────────────────────────────
    def _draw_head(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 18
        # Face shape
        head_pts = [
            (hx - 6, hy + 4), (hx - 7, hy - 1), (hx - 5, hy - 6),
            (hx - 1, hy - 8), (hx + 3, hy - 8), (hx + 6, hy - 5),
            (hx + 7, hy), (hx + 6, hy + 4), (hx + 3, hy + 6),
            (hx - 1, hy + 6), (hx - 4, hy + 5),
        ]
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["skin_darkest"], head_pts)
        # Skin main
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["skin_dark"], [
            (hx - 5, hy + 3), (hx - 6, hy), (hx - 4, hy - 5),
            (hx, hy - 7), (hx + 2, hy - 7), (hx + 5, hy - 4),
            (hx + 6, hy), (hx + 5, hy + 3), (hx + 2, hy + 5),
            (hx, hy + 5), (hx - 3, hy + 4),
        ])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["skin_mid"], [
            (hx - 4, hy - 3), (hx - 2, hy - 5),
            (hx + 2, hy - 5), (hx + 4, hy - 3),
            (hx + 5, hy), (hx + 3, hy + 3),
            (hx - 1, hy + 3), (hx - 4, hy),
        ])
        _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["skin_light"], [
            (hx - 1, hy - 4), (hx + 2, hy - 4),
            (hx + 3, hy - 2), (hx - 2, hy - 2),
        ])
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_shine"],
                         (hx, hy - 4, 2, 1))
        # Nose small line
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy, 1, 2))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_dark"],
                         (hx + facing * 2, hy + 1, 1, 1))
        # Mouth (small serious line)
        pygame.draw.line(surface, _NS_kairenji.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy + 4),
                         (hx + facing * 3, hy + 4), 1)
        # Ear
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_darkest"],
                         (hx - facing * 6, hy, 2, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["skin_dark"],
                         (hx - facing * 6, hy + 1, 1, 2))

        # SHARINGAN EYES (red with tomoe pattern)
        _NS_kairenji._draw_sharingan_eye(surface, hx + facing * 3, hy - 2,
                                          facing, phase)
        _NS_kairenji._draw_sharingan_eye(surface, hx - facing * 2, hy - 1,
                                          facing, phase, small=True)

    def _draw_sharingan_eye(surface, ex, ey, facing, phase, small=False):
        """Red glowing Sharingan with tomoe pattern."""
        pulse = math.sin(phase * 2.5) * 0.25 + 0.75
        # Deep socket
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["shadow_deep"],
                         (ex - 2, ey - 1, 5, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_socket"],
                         (ex - 1, ey - 1, 4, 3))
        # Glow halo (red)
        for r in range(5 if not small else 3, 0, -1):
            a = _NS_kairenji._alpha(120 * (5 - r) / 5 * pulse)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["eye_mid"], a),
                                   (ex + 1, ey), r)
        # Iris (red)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_darkest"],
                         (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_dark"],
                         (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_mid"],
                         (ex + 1, ey - 1, 2, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_light"],
                         (ex + 1, ey, 1, 1))
        # Tomoe pattern (3 dots around center) - only for main eye
        if not small:
            # Central pupil
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["shadow_deep"],
                             (ex + 1, ey, 1, 1))
            # 3 tomoe positions (small dots offset from center)
            for tm_i in range(3):
                tm_ang = phase * 0.5 + tm_i * math.pi * 2 / 3
                tmx = ex + 1 + int(math.cos(tm_ang) * 1.5)
                tmy = ey + int(math.sin(tm_ang) * 1)
                pygame.draw.rect(surface, _NS_kairenji.PALETTE["shadow_deep"],
                                 (tmx, tmy, 1, 1))
        # Bright hot spot
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_glow"],
                         (ex + 2, ey, 1, 1))

    # ── HAIR (spiky style) ───────────────────────────────────
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Spiky hair behind head."""
        hx = cx + facing * 2
        hy = cy - 18
        # Multiple spiky strands
        spikes = [
            (-6, -6, 10, 0.0),
            (-3, -8, 12, 0.2),
            (0, -9, 13, 0.4),
            (3, -8, 11, 0.6),
            (6, -6, 9, 0.8),
            (-7, -3, 7, 1.0),
            (7, -3, 6, 1.2),
        ]
        for (dx, dy, length, ph_off) in spikes:
            sway = math.sin(phase * 0.6 + ph_off) * 1
            base_x = hx + dx
            base_y = hy + dy
            # Direction of spike (outward-back)
            ang = math.atan2(dy, dx) - 0.2
            tip_x = base_x + int(math.cos(ang) * length + sway)
            tip_y = base_y + int(math.sin(ang) * length)
            # Perpendicular for base width
            perp = ang + math.pi / 2
            pa_x = base_x + int(math.cos(perp) * 2)
            pa_y = base_y + int(math.sin(perp) * 2)
            pb_x = base_x - int(math.cos(perp) * 2)
            pb_y = base_y - int(math.sin(perp) * 2)
            # Shadow
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["hair_darkest"],
                               [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["hair_dark"], [
                (tip_x, tip_y),
                (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                (base_x, base_y),
            ])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["hair_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            # Highlight tip
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))

    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Bangs over forehead."""
        hx = cx + facing * 2
        hy = cy - 18
        bangs = [
            (facing * 1, -7, 5, 0.0),
            (facing * 3, -6, 7, 0.3),
            (facing * 5, -5, 5, 0.6),
            (-facing * 2, -7, 5, 0.9),
        ]
        for (dx, dy, length, ph_off) in bangs:
            sway = math.sin(phase * 0.7 + ph_off) * 0.8
            bx = hx + dx
            by = hy + dy
            tip_x = bx + int(facing * 1 + sway)
            tip_y = by + length
            _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["hair_darkest"],
                                 (bx, by), (tip_x, tip_y), 3)
            _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["hair_dark"],
                                 (bx, by), (tip_x, tip_y), 2)
            _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["hair_mid"],
                                 (bx, by - 1), (tip_x, tip_y - 1), 1)
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))

    # ── HEADBAND (ninja forehead protector) ──────────────────
    def _draw_headband(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 18
        # Cloth wrap around head
        band_y = hy - 4
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_darkest"],
                         (hx - 6, band_y, 13, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["cloth_dark"],
                         (hx - 6, band_y + 1, 13, 1))
        # Metal plate (center)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["metal_dark"],
                         (hx - 3, band_y, 6, 3))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["metal_mid"],
                         (hx - 3, band_y, 6, 2))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["metal_light"],
                         (hx - 3, band_y, 6, 1))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["metal_shine"],
                         (hx - 2, band_y, 3, 1))
        # Uchiha fan symbol (red curve on metal)
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_darkest"],
                         (hx - 1, band_y + 1, 3, 1))
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_mid"],
                         (hx, band_y + 1, 2, 1))
        # Headband ties trailing back
        back = -facing
        for tie_i in range(2):
            tie_y_off = tie_i * 2
            tie_start_x = hx + back * 6
            tie_start_y = band_y + 1 + tie_y_off
            tie_end_x = tie_start_x + back * (6 + tie_i * 2)
            tie_end_y = tie_start_y + 4 + tie_i * 2 \
                        + int(math.sin(phase * 0.8 + tie_i) * 2)
            _NS_kairenji._aaline(surface,
                                 _NS_kairenji.PALETTE["cloth_darkest"],
                                 (tie_start_x, tie_start_y),
                                 (tie_end_x, tie_end_y), 2)
            _NS_kairenji._aaline(surface, _NS_kairenji.PALETTE["cloth_dark"],
                                 (tie_start_x, tie_start_y),
                                 (tie_end_x, tie_end_y), 1)

    # ── CAPE / SCARF ─────────────────────────────────────────
    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Small cape/scarf trailing behind."""
        back = -facing
        base_x = cx + back * 4
        base_y = cy - 6
        seg = 6
        pts_t = []
        pts_b = []
        for i in range(seg + 1):
            t = i / seg
            sx = base_x - int(facing * t * 22)
            sy = base_y + int(t * 12)
            wave = math.sin(phase * 1.5 + t * math.pi * 1.5) * (2 + t * 4)
            sy += int(wave)
            w = int(3 * (1 - t * 0.4))
            pts_t.append((sx, sy - w))
            pts_b.append((sx, sy + w))
        full = pts_t + list(reversed(pts_b))
        if len(full) >= 3:
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in full])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_darkest"], full)
            inner = pts_t[:-1] + list(reversed(pts_b[:-1]))
            if len(inner) >= 3:
                _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["cloth_dark"], inner)
        # Purple chakra edge
        for i in range(len(pts_t) - 1):
            a = _NS_kairenji._alpha(200 * (1 - i / len(pts_t)))
            pygame.draw.line(surface,
                             (*_NS_kairenji.PALETTE["void_dark"], a),
                             pts_t[i], pts_t[i + 1], 1)
        # Tip particle
        if pts_t:
            tip = pts_t[-1]
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["void_mid"],
                             (tip[0], tip[1], 2, 2))
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["void_light"],
                             (tip[0], tip[1], 1, 1))

    # ============================================================
    # BASIC ATTACK SLASH TRAIL + IMPACT
    # ============================================================
    def _get_katana_tip(cx, cy, facing, progress):
        if progress < 0.3:
            t = progress / 0.3
            angle = -math.pi / 5 - t * math.pi / 2.3
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            angle = -math.pi / 5 - math.pi / 2.3 + t * (math.pi * 1.1)
        else:
            t = (progress - 0.55) / 0.45
            angle = -math.pi / 5 + (math.pi * 0.65 * (1 - t))
        sx = cx + facing * 9
        sy = cy - 8
        arm_len = 16
        hx = sx + int(math.cos(angle) * arm_len) * facing
        hy = sy + int(math.sin(angle) * arm_len)
        blade_len = 28
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        return tip_x, tip_y, angle

    def _draw_slash_trail(surface, boss, cx, cy, facing, progress):
        if progress < 0.28 or progress > 0.7:
            return
        if progress < 0.32:
            intensity = (progress - 0.28) / 0.04
        elif progress < 0.55:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.55) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        num = 14
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.22
            if sp < 0.28:
                continue
            tx, ty, ang = _NS_kairenji._get_katana_tip(cx, cy, facing, sp)
            trail.append((tx, ty, ang, i))
        if len(trail) < 2:
            return
        trail.reverse()
        ts = pygame.Surface((320, 320), pygame.SRCALPHA)
        ox = cx - 160
        oy = cy - 160
        layers = [
            (_NS_kairenji.PALETTE["void_darkest"], 14, 100),
            (_NS_kairenji.PALETTE["void_dark"], 10, 150),
            (_NS_kairenji.PALETTE["void_mid"], 6, 200),
            (_NS_kairenji.PALETTE["void_light"], 3, 240),
            (_NS_kairenji.PALETTE["void_shine"], 1, 255),
        ]
        for color, max_w, max_a in layers:
            for i in range(len(trail) - 1):
                p1, p2 = trail[i], trail[i + 1]
                fade = 1.0 - (p1[3] / num)
                a = _NS_kairenji._alpha(max_a * fade * intensity)
                w = max(1, int(max_w * fade))
                if a > 0:
                    pygame.draw.line(
                        ts, (*color, a),
                        (p1[0] - ox, p1[1] - oy),
                        (p2[0] - ox, p2[1] - oy), w,
                    )
        # Sparkles
        for i, (tx, ty, ang, idx) in enumerate(trail):
            fade = 1.0 - (idx / num)
            a = _NS_kairenji._alpha(230 * fade * intensity)
            if a <= 0 or i % 2 == 0:
                continue
            perp = ang + math.pi / 2
            for s in range(2):
                d = 4 + s * 3
                sign = 1 if s == 0 else -1
                spx = tx - ox + int(math.cos(perp) * d * sign)
                spy = ty - oy + int(math.sin(perp) * d * sign)
                pygame.draw.rect(ts, (*_NS_kairenji.PALETTE["void_hot"], a),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(ts, (*_NS_kairenji.PALETTE["white"], a),
                                 (spx, spy, 1, 1))
        surface.blit(ts, (ox, oy))
        # Leading edge
        if trail:
            lead = trail[0]
            for r in range(10, 2, -2):
                a = _NS_kairenji._alpha(160 * (10 - r) / 10 * intensity)
                _NS_kairenji._aacircle(
                    surface, (*_NS_kairenji.PALETTE["void_mid"], a),
                    (lead[0], lead[1]), r,
                )
            _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["void_hot"],
                                   (lead[0], lead[1]), 3)
            _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["white"],
                                   (lead[0], lead[1]), 1)

    def _draw_slash_impact(surface, boss, cx, cy, facing, progress):
        if progress < 0.5 or progress > 0.7:
            return
        t = (progress - 0.5) / 0.2
        inten = math.sin(t * math.pi)
        tx, ty, ang = _NS_kairenji._get_katana_tip(cx, cy, facing, progress)
        ix = tx + facing * 4
        iy = ty
        r = int(5 + t * 14)
        a = _NS_kairenji._alpha(255 * inten)
        # Burst
        for rr in range(r + 4, 0, -2):
            ra = _NS_kairenji._alpha(a * (r + 4 - rr) / (r + 4))
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_darkest"], ra),
                                   (ix, iy), rr)
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["void_dark"], a),
                               (ix, iy), max(2, r - 3))
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["void_mid"], a),
                               (ix, iy), max(1, r - 6))
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["void_light"], a),
                               (ix, iy), max(1, r - 9))
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["void_hot"], a),
                               (ix, iy), max(1, r - 12))
        pygame.draw.rect(surface, (*_NS_kairenji.PALETTE["white"], a),
                         (ix, iy, 1, 1))
        # Radial slash lines
        slash_perp = ang + math.pi / 2
        for i in range(6):
            slash_off = (i - 2.5) * 4
            sx1 = ix + int(math.cos(slash_perp) * slash_off) - int(math.cos(ang) * r) * facing
            sy1 = iy + int(math.sin(slash_perp) * slash_off) - int(math.sin(ang) * r)
            sx2 = ix + int(math.cos(slash_perp) * slash_off) + int(math.cos(ang) * r) * facing
            sy2 = iy + int(math.sin(slash_perp) * slash_off) + int(math.sin(ang) * r)
            for w, color, wa in [
                (3, _NS_kairenji.PALETTE["void_dark"], 200),
                (2, _NS_kairenji.PALETTE["void_mid"], 240),
                (1, _NS_kairenji.PALETTE["white"], 255),
            ]:
                la = _NS_kairenji._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la), (sx1, sy1), (sx2, sy2), w)
        # Sparks
        for i in range(10):
            sa = i * math.pi / 5 + progress * 4
            dist = int(r * 1.2)
            ex = ix + int(math.cos(sa) * dist)
            ey = iy + int(math.sin(sa) * dist)
            pygame.draw.rect(surface,
                             (*_NS_kairenji.PALETTE["void_hot"], a),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_kairenji.PALETTE["white"], a),
                             (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / FLOATING FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((120, 24), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            a = max(0, (12 - r) * 18)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 12 - r, 100 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (5, 2, 8, 160), (8, 6, 104, 12))
        surface.blit(sh, (x - 60, y - 12))

    def _draw_void_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for r in range(80, 5, -5):
            a = _NS_kairenji._alpha((80 - r) * 1.0 * pulse)
            if a > 0:
                _NS_kairenji._aacircle(aura,
                                       (*_NS_kairenji.PALETTE["void_darkest"], a),
                                       (100, 85), r)
        for r in range(45, 5, -3):
            a = _NS_kairenji._alpha((45 - r) * 1.3 * pulse)
            if a > 0:
                _NS_kairenji._aacircle(aura,
                                       (*_NS_kairenji.PALETTE["void_dark"], a),
                                       (100, 85), r)
        surface.blit(aura, (x - 100, y - 85))
        # Floating chakra motes
        for i in range(10):
            ang = phase * 0.35 + i * math.pi / 5
            rd = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.45)
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["void_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["void_hot"],
                             (sx, sy, 1, 1))

    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((140, 34), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(22, 3, -2):
            a = _NS_kairenji._alpha((22 - r) * 3.2 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kairenji.PALETTE["void_darkest"], a),
                    (70 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(14, 3, -2):
            a = _NS_kairenji._alpha((14 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kairenji.PALETTE["void_dark"], a),
                    (70 - r, 17 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising chakra motes
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 18)
            a = _NS_kairenji._alpha(200 * (1 - t) * strength)
            if a > 0:
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["void_dark"], a),
                                       (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kairenji.PALETTE["void_mid"], a),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_kairenji.PALETTE["void_hot"], a),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_kairenji._alpha(140 - i * 25)
                if a > 0:
                    _NS_kairenji._aacircle(
                        surface, (*_NS_kairenji.PALETTE["void_dark"], a),
                        (sx, sy), max(2, 5 - i),
                    )

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kairenji.PALETTE["void_darkest"], 180),
                            (5, 14, 150, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_kairenji.PALETTE["void_dark"], 210),
                            (15, 16, 130, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_kairenji.PALETTE["void_mid"], 190),
                            (25, 18, 110, 14), 1)
        for i in range(8):
            ang = phase * 0.4 + i * math.pi / 4
            x1 = 80 + int(math.cos(ang) * 43)
            y1 = 24 + int(math.sin(ang) * 7)
            x2 = 80 + int(math.cos(ang) * 68)
            y2 = 24 + int(math.sin(ang) * 10)
            pygame.draw.line(ring, (*_NS_kairenji.PALETTE["void_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_kairenji.PALETTE["void_hot"],
                       _NS_kairenji._alpha(150 * pulse)),
                (10, 8, 140, 32), 1,
            )
        surface.blit(ring, (x - 80, y - 22))

    # ============================================================
    # SKILL Q — SUSANO'O BURST (teleport dash slash)
    # ============================================================
    def _draw_susanoo_ground(surface, boss, x, y, timer, phase):
        """Chakra portal at origin and destination."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kairenji._target_position(boss, x, y)
        if progress < 0.2:
            # Origin portal
            t = progress / 0.2
            r = int(20 * t + 5)
            for rr in range(r, 0, -2):
                a = _NS_kairenji._alpha(180 * (r - rr) / r * t)
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["void_dark"], a),
                                       (x, y + 45), rr, 1)
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["void_mid"], a),
                                       (x, y + 45), max(1, rr - 2), 1)
        elif progress > 0.55:
            # Destination portal
            t = (progress - 0.55) / 0.3
            r = int(25 - t * 15)
            if r > 0:
                for rr in range(r, 0, -2):
                    a = _NS_kairenji._alpha(200 * (1 - t))
                    _NS_kairenji._aacircle(surface,
                                           (*_NS_kairenji.PALETTE["void_dark"], a),
                                           (tx, ty + 45), rr, 1)
                    _NS_kairenji._aacircle(surface,
                                           (*_NS_kairenji.PALETTE["void_mid"], a),
                                           (tx, ty + 45), max(1, rr - 2), 1)

    def _draw_susanoo_slash(surface, boss, x, y, timer, phase):
        """Big slash impact at target."""
        tx, ty = _NS_kairenji._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.55:
            return
        t = (progress - 0.55) / 0.35
        inten = math.sin(t * math.pi)
        a = _NS_kairenji._alpha(255 * inten)
        # Massive vertical slash line
        slash_len = int(40 + t * 15)
        slash_ang = -math.pi / 4
        for line_i, off in enumerate((-10, -3, 3, 10)):
            perp = slash_ang + math.pi / 2
            off_x = int(math.cos(perp) * off)
            off_y = int(math.sin(perp) * off)
            x1 = tx - int(math.cos(slash_ang) * slash_len) + off_x
            y1 = ty - int(math.sin(slash_ang) * slash_len) + off_y
            x2 = tx + int(math.cos(slash_ang) * slash_len) + off_x
            y2 = ty + int(math.sin(slash_ang) * slash_len) + off_y
            for w, color, wa in [
                (10, _NS_kairenji.PALETTE["void_darkest"], 80),
                (6, _NS_kairenji.PALETTE["void_dark"], 140),
                (4, _NS_kairenji.PALETTE["void_mid"], 200),
                (2, _NS_kairenji.PALETTE["void_light"], 240),
                (1, _NS_kairenji.PALETTE["white"], 255),
            ]:
                la = _NS_kairenji._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la),
                                 (x1, y1), (x2, y2), w)
        # Central chakra explosion
        br = int(12 + t * 20)
        for r in range(br + 5, 0, -3):
            ra = _NS_kairenji._alpha(a * (br + 5 - r) / (br + 5))
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_dark"], ra),
                                   (tx, ty), r)
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["void_mid"], a),
                               (tx, ty), max(2, br - 5))
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["void_hot"], a),
                               (tx, ty), max(1, br - 12))
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["white"], a),
                               (tx, ty), max(1, br - 16))
        # Sparks
        for i in range(14):
            sa = i * math.pi / 7 + phase
            dist = int(br * 1.5)
            ex = tx + int(math.cos(sa) * dist)
            ey = ty + int(math.sin(sa) * dist)
            pygame.draw.rect(surface,
                             (*_NS_kairenji.PALETTE["void_hot"], a),
                             (ex, ey, 3, 3))
            pygame.draw.rect(surface,
                             (*_NS_kairenji.PALETTE["white"], a),
                             (ex, ey, 1, 1))

    # ============================================================
    # SKILL W — KOTOAMATSUKAMI (eye projectile)
    # ============================================================
    def _draw_kotoamatsukami(surface, boss, x, y, timer, phase):
        """Big eye/mangekyō projectile flying to target."""
        facing = boss.direction
        duration = 55
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_kairenji._target_position(boss, x, y)
        if progress < 0.15:
            # Charge — big eye materializes near hand
            t = progress / 0.15
            cx_eye = x + facing * 22
            cy_eye = y - 6
            r = int(4 + t * 8)
            for rr in range(r + 4, 0, -1):
                a = _NS_kairenji._alpha(200 * (r + 4 - rr) / (r + 4))
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["void_dark"], a),
                                       (cx_eye, cy_eye), rr)
            _NS_kairenji._draw_mangekyo(surface, cx_eye, cy_eye, r, phase)
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        start_x = x + facing * 22
        start_y = y - 6
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            a = _NS_kairenji._alpha(200 - i * 20)
            size = max(2, 10 - i)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_darkest"], a),
                                   (px, py), size + 1)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_dark"], a),
                                   (px, py), size)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_mid"], a),
                                   (px, py), max(1, size - 2))
        # Main eye projectile
        _NS_kairenji._draw_mangekyo(surface, bx, by, 10, phase)
        # Glow around eye
        for r in range(15, 5, -2):
            a = _NS_kairenji._alpha(120 * (15 - r) / 15)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_mid"], a),
                                   (bx, by), r)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            r = int(15 + st * 20)
            a = _NS_kairenji._alpha(255 * (1 - st))
            for rr in range(r + 3, 0, -2):
                ra = _NS_kairenji._alpha(a * (r + 3 - rr) / (r + 3))
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["void_dark"], ra),
                                       (tx, ty), rr)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_mid"], a),
                                   (tx, ty), max(1, r - 5))
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_hot"], a),
                                   (tx, ty), max(1, r - 10))
            # Concentric hypnosis rings
            for ring_i in range(3):
                ring_r = int(r * (1.2 + ring_i * 0.3))
                ra = _NS_kairenji._alpha(180 * (1 - st))
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["void_light"], ra),
                                       (tx, ty), ring_r, 1)

    def _draw_mangekyo(surface, cx, cy, size, phase):
        """Draw a mangekyō sharingan pattern (pinwheel/eye)."""
        # Outer black rim
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               (cx, cy), size + 1)
        # Red iris body
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["eye_darkest"],
                               (cx, cy), size)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["eye_dark"],
                               (cx, cy), size - 1)
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["eye_mid"],
                               (cx, cy), size - 2)
        # Purple void tinted
        for r in range(size - 1, 0, -1):
            a = _NS_kairenji._alpha(80 * r / size)
            _NS_kairenji._aacircle(surface,
                                   (*_NS_kairenji.PALETTE["void_mid"], a),
                                   (cx, cy), r)
        # Rotating pinwheel pattern
        rot = phase * 3
        for i in range(3):
            ang = rot + i * math.pi * 2 / 3
            # Curved blade of pinwheel
            for step in range(size - 1, 0, -1):
                bx = cx + int(math.cos(ang) * step)
                by = cy + int(math.sin(ang) * step)
                pygame.draw.rect(surface, _NS_kairenji.PALETTE["shadow_deep"],
                                 (bx, by, 1, 1))
                # Curve
                curve_ang = ang + step * 0.15
                bcx = cx + int(math.cos(curve_ang) * step)
                bcy = cy + int(math.sin(curve_ang) * step)
                pygame.draw.rect(surface, _NS_kairenji.PALETTE["shadow_deep"],
                                 (bcx, bcy, 1, 1))
        # Central pupil
        _NS_kairenji._aacircle(surface, _NS_kairenji.PALETTE["shadow_deep"],
                               (cx, cy), 1)
        # Bright highlight
        pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_glow"],
                         (cx + 1, cy - 1, 1, 1))

    # ============================================================
    # SKILL E — SHADOW CLONE JUTSU (multiple clones)
    # ============================================================
    def _draw_shadowclone_ground(surface, boss, x, y, timer, phase):
        """Water splash rings under each clone."""
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Under each clone position
        clone_positions = [
            (x - 40, y + 42), (x - 25, y + 48), (x + 25, y + 48),
            (x + 40, y + 42),
        ]
        for cpx, cpy in clone_positions:
            r = int(12 + math.sin(phase * 2) * 2)
            for rr in range(r, 0, -2):
                a = _NS_kairenji._alpha(180 * (r - rr) / r)
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["water_dark"], a),
                                       (cpx, cpy), rr, 1)
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["water_mid"], a),
                                       (cpx, cpy), max(1, rr - 2), 1)
            # Splash bubbles
            for i in range(4):
                bang = phase * 2 + i * math.pi / 2
                bx = cpx + int(math.cos(bang) * (r - 2))
                by = cpy + int(math.sin(bang) * (r - 2) * 0.5)
                pygame.draw.rect(surface, _NS_kairenji.PALETTE["water_light"],
                                 (bx, by, 1, 1))
                pygame.draw.rect(surface, _NS_kairenji.PALETTE["water_shine"],
                                 (bx, by, 1, 1))

    # ============================================================
    # SKILL R — SHARINGAN REFLECTION (shield + reflected projectiles)
    # ============================================================
    def _draw_sharingan_ground(surface, boss, x, y, timer, phase):
        """Red magical ring on ground."""
        pulse = math.sin(phase * 2) * 3
        r = int(40 + pulse)
        a = _NS_kairenji._alpha(200)
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["eye_darkest"], a),
                               (x, y + 45), r, 3)
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["eye_dark"], a),
                               (x, y + 45), r - 3, 2)
        _NS_kairenji._aacircle(surface,
                               (*_NS_kairenji.PALETTE["eye_mid"], a),
                               (x, y + 45), r - 5, 1)

    def _draw_sharingan_shield(surface, boss, x, y, timer, phase):
        """Big red shield bubble around boss with sharingan pattern."""
        pulse = math.sin(phase * 2) * 3
        r = 50 + int(pulse)
        # Shield bubble surface
        shield = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Concentric shield rings
        for i, (thick, av) in enumerate([(3, 100), (2, 150), (1, 200)]):
            _NS_kairenji._aacircle(shield,
                                   (*_NS_kairenji.PALETTE["eye_dark"], av),
                                   center, r - i, thick)
            _NS_kairenji._aacircle(shield,
                                   (*_NS_kairenji.PALETTE["eye_mid"], av),
                                   center, r - i - 1, 1)
        # Central mangekyō pattern
        _NS_kairenji._draw_mangekyo(shield, center[0], center[1], 12, phase)
        # Sparks on edge
        for i in range(20):
            ang = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(ang) * r)
            sy = center[1] + int(math.sin(ang) * r)
            pygame.draw.rect(shield, _NS_kairenji.PALETTE["eye_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(shield, _NS_kairenji.PALETTE["eye_glow"],
                             (sx, sy, 1, 1))
        surface.blit(shield, (x - r - 10, y - r - 10))

    def _draw_sharingan_projectiles(surface, boss, x, y, timer, phase):
        """Reflected projectiles shooting outward from shield."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Every 15 frames spawn a projectile that flies outward
        # Simplified: continuously animate 6 projectiles flying outward in different dirs
        num_proj = 8
        for p_i in range(num_proj):
            p_phase = (phase * 0.5 + p_i * 0.2) % 1.0
            if p_phase < 0.1:
                continue
            p_ang = p_i * math.pi * 2 / num_proj + phase * 0.3
            p_dist = int(p_phase * 150)
            px = x + int(math.cos(p_ang) * p_dist)
            py = y + int(math.sin(p_ang) * p_dist)
            # Trail
            for ti in range(5):
                tt = max(0.0, p_phase - ti * 0.05)
                tpx = x + int(math.cos(p_ang) * tt * 150)
                tpy = y + int(math.sin(p_ang) * tt * 150)
                a = _NS_kairenji._alpha(220 - ti * 40)
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["eye_dark"], a),
                                       (tpx, tpy), max(1, 4 - ti))
                _NS_kairenji._aacircle(surface,
                                       (*_NS_kairenji.PALETTE["eye_mid"], a),
                                       (tpx, tpy), max(1, 3 - ti))
                pygame.draw.rect(surface,
                                 (*_NS_kairenji.PALETTE["eye_light"], a),
                                 (tpx, tpy, 1, 1))
            # Projectile head (dart-like)
            a = _NS_kairenji._alpha(240)
            perp = p_ang + math.pi / 2
            # Small dart
            dart_tip_x = px + int(math.cos(p_ang) * 4)
            dart_tip_y = py + int(math.sin(p_ang) * 4)
            dart_back_x = px - int(math.cos(p_ang) * 3)
            dart_back_y = py - int(math.sin(p_ang) * 3)
            side_a_x = px + int(math.cos(perp) * 2)
            side_a_y = py + int(math.sin(perp) * 2)
            side_b_x = px - int(math.cos(perp) * 2)
            side_b_y = py - int(math.sin(perp) * 2)
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["eye_darkest"], [
                (dart_tip_x, dart_tip_y),
                (side_a_x, side_a_y),
                (dart_back_x, dart_back_y),
                (side_b_x, side_b_y),
            ])
            _NS_kairenji._poly(surface, _NS_kairenji.PALETTE["eye_mid"], [
                (dart_tip_x, dart_tip_y),
                (px + int(math.cos(perp) * 1), py + int(math.sin(perp) * 1)),
                (dart_back_x, dart_back_y),
                (px - int(math.cos(perp) * 1), py - int(math.sin(perp) * 1)),
            ])
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["eye_light"],
                             (dart_tip_x, dart_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kairenji.PALETTE["white"],
                             (dart_tip_x, dart_tip_y, 1, 1))


# ====================================================================================================
# KARZHUL - MINI BOSS
# ====================================================================================================

class _NS_karzhul:
    """Namespace karzhul - werewolf beast-hunter boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Fur (silver-grey with dark patches)
        "fur_darkest": (18, 18, 22),
        "fur_dark": (55, 55, 65),
        "fur_mid": (115, 115, 128),
        "fur_light": (180, 180, 195),
        "fur_shine": (225, 225, 235),
        "fur_edge": (245, 245, 250),

        # Skin (grey wolf-face, hands)
        "skin_darkest": (25, 22, 28),
        "skin_dark": (60, 55, 65),
        "skin_mid": (105, 100, 115),
        "skin_light": (155, 148, 165),

        # Armor iron/steel (dark rusted)
        "iron_darkest": (10, 10, 14),
        "iron_dark": (35, 32, 38),
        "iron_mid": (75, 72, 80),
        "iron_light": (135, 130, 140),
        "iron_shine": (195, 190, 200),

        # Bronze/brass accents (buckles, rivets)
        "bronze_dark": (65, 40, 15),
        "bronze_mid": (135, 90, 35),
        "bronze_light": (200, 150, 70),
        "bronze_shine": (245, 210, 130),

        # Leather straps
        "leather_darkest": (15, 10, 5),
        "leather_dark": (45, 30, 15),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 105, 60),

        # Bone/tusks/teeth (aged bone)
        "bone_dark": (95, 85, 65),
        "bone_mid": (180, 165, 130),
        "bone_light": (230, 220, 190),
        "bone_shine": (255, 250, 225),

        # Claws (curved steel talons)
        "claw_darkest": (8, 8, 12),
        "claw_dark": (30, 30, 38),
        "claw_mid": (90, 90, 100),
        "claw_light": (170, 170, 185),
        "claw_shine": (230, 230, 240),
        "claw_edge": (255, 245, 210),

        # Eyes (fiery amber/orange - predator)
        "eye_socket": (8, 3, 2),
        "eye_darkest": (45, 15, 5),
        "eye_dark": (140, 55, 15),
        "eye_mid": (230, 120, 30),
        "eye_light": (255, 190, 80),
        "eye_glow": (255, 235, 160),

        # Blood/attack accent (deep crimson)
        "blood_dark": (60, 8, 12),
        "blood_mid": (140, 20, 25),
        "blood_light": (220, 50, 45),
        "blood_hot": (255, 100, 90),

        # Battle roar aura (electric blue-white)
        "roar_darkest": (10, 25, 55),
        "roar_dark": (35, 80, 145),
        "roar_mid": (95, 170, 235),
        "roar_light": (170, 220, 255),
        "roar_hot": (220, 245, 255),
        "roar_shine": (250, 253, 255),

        # Bola rope (leather cord)
        "rope_dark": (55, 40, 20),
        "rope_mid": (120, 90, 50),
        "rope_light": (180, 145, 90),

        # Hunt trail (yellow-white for thrill of hunt)
        "hunt_dark": (100, 80, 20),
        "hunt_mid": (210, 180, 60),
        "hunt_light": (250, 230, 130),
        "hunt_shine": (255, 250, 210),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_karzhul._clamp(color)
        if _NS_karzhul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_karzhul._clamp(color)
        if _NS_karzhul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_karzhul._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_karzhul(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_karzhul._detect_moving(boss)
        _NS_karzhul._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_krz_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_karzhul._draw_beast_aura(surface, x, y, pulse)
        _NS_karzhul._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_karzhul._draw_battleroar_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_karzhul._draw_hunt_ground(
                surface, boss, x, y, skill_timer, pulse
            )

        # Body
        if active_skill == "r":
            _NS_karzhul._draw_hunt_pose(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_karzhul._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_karzhul._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_karzhul._draw_idle_pose(surface, boss, x, y)

        # Overlay skills on body
        if active_skill == "w":
            _NS_karzhul._draw_battleroar_overlay(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "q":
            _NS_karzhul._draw_savageroar_glow(
                surface, boss, x, y, skill_timer, pulse
            )

        # Foreground FX
        if active_skill == "q":
            _NS_karzhul._draw_savageroar_slash(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_karzhul._draw_bolastrike(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_karzhul._draw_hunt_leap(
                surface, boss, x, y, skill_timer, pulse
            )

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_krz_prev_timer", 0))
        active = bool(getattr(boss, "_krz_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._krz_attack_active = True
            boss._krz_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._krz_attack_frame = int(
                getattr(boss, "_krz_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._krz_attack_active = False
            boss._krz_attack_frame = 0
            active = False
        boss._krz_prev_timer = timer
        boss._krz_attack_progress = (
            min(1.0, getattr(boss, "_krz_attack_frame", 0) / max(1, cd - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_krz_last_x"):
            boss._krz_last_x = boss.x
            boss._krz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._krz_last_x)
        dy = abs(boss.y - boss._krz_last_y)
        boss._krz_last_x = boss.x
        boss._krz_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS  (floating movement — beast hovers menacingly)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 4)
        _NS_karzhul._draw_shadow(surface, x, y + 52)
        _NS_karzhul._draw_float_wisps(surface, x, y + 46, boss.pulse)
        _NS_karzhul._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )

    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.4
        bob = int(math.sin(ph * 1.0) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_karzhul._draw_shadow(surface, x + sway, y + 52)
        _NS_karzhul._draw_float_wisps(
            surface, x + sway, y + 46, ph, trail=True, facing=boss.direction
        )
        _NS_karzhul._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_krz_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-5 + t * 20)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(15 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_karzhul._draw_shadow(surface, x + lunge, y + 52)
        _NS_karzhul._draw_float_wisps(
            surface, x + lunge, y + 46, boss.pulse, intense=True
        )
        _NS_karzhul._draw_claw_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
        _NS_karzhul._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )
        _NS_karzhul._draw_claw_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

    def _draw_hunt_pose(surface, boss, x, y, timer, pulse):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_karzhul._target_position(boss, x, y)
        # Wind-up (crouch) → dash leap → recovery
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 6) * boss.direction
            lift = -int(t * 3)  # crouch down
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            # Leap toward target
            lunge = int(-6 + t * (tx - x + 6 * boss.direction)) * boss.direction // max(1, abs(boss.direction))
            lunge = int((tx - x) * t)
            lift = int(math.sin(t * math.pi) * 25)  # jump arc
        else:
            t = (progress - 0.7) / 0.3
            lunge = int((tx - x) * (1 - t * 0.05))
            lift = int(5 * (1 - t))
        bob = int(math.sin(pulse * 0.5) * 2)
        _NS_karzhul._draw_shadow(surface, x + lunge, y + 52)
        _NS_karzhul._draw_float_wisps(
            surface, x + lunge, y + 46, pulse, intense=True
        )
        # Motion afterimages during leap
        if 0.3 < progress < 0.75:
            for i in range(4):
                ax = int(x + lunge * (1 - (i + 1) * 0.18))
                ay = int(y - lift + bob + int(math.sin(
                    max(0.0, (progress - 0.3 - i * 0.05) / 0.4) * math.pi
                ) * 25))
                aimg = pygame.Surface((80, 80), pygame.SRCALPHA)
                a = _NS_karzhul._alpha(140 - i * 30)
                _NS_karzhul._aacircle(
                    aimg, (*_NS_karzhul.PALETTE["hunt_dark"], a), (40, 40), 28
                )
                _NS_karzhul._aacircle(
                    aimg, (*_NS_karzhul.PALETTE["hunt_mid"], a // 2),
                    (40, 40), 18,
                )
                surface.blit(aimg, (ax - 40, ay - 40))
        _NS_karzhul._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction, pulse,
            "attack", 0.5,
        )

    # ============================================================
    # BODY COMPOSITION
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0):
        # Order: mane back -> back arm -> torso+shoulders ->
        # legs -> tail -> head -> mane front -> front arm+claws
        _NS_karzhul._draw_mane_back(surface, cx, cy, facing, phase)
        _NS_karzhul._draw_tail(surface, cx, cy, facing, phase, action)
        _NS_karzhul._draw_back_arm(surface, cx, cy, facing, phase, action, progress)
        _NS_karzhul._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_karzhul._draw_torso(surface, cx, cy, facing, phase)
        _NS_karzhul._draw_shoulder_armor(surface, cx, cy, facing, phase)
        _NS_karzhul._draw_head(surface, cx, cy, facing, phase, action)
        _NS_karzhul._draw_mane_front(surface, cx, cy, facing, phase)
        _NS_karzhul._draw_front_arm(surface, cx, cy, facing, phase, action, progress)

    # ── LEGS (dangling clawed feet) ──────────────────────────
    def _draw_legs(surface, cx, cy, facing, phase, action):
        sway = (
            math.sin(phase * 1.2) * 3
            if action == "walk"
            else math.sin(phase * 0.5) * 1.5
        )
        for side in (-1, 1):
            lx = cx + side * 7
            ly = cy + 16
            sw = int(sway * (1 if side > 0 else -1))
            # Thigh (fur)
            thigh = [
                (lx - 4, ly - 2), (lx + 4, ly - 2),
                (lx + 5 + sw, ly + 6), (lx - 5 + sw, ly + 6),
            ]
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 2) for p in thigh])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_darkest"], thigh)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_dark"], [
                (lx - 3, ly - 1), (lx + 3, ly - 1),
                (lx + 4 + sw, ly + 5), (lx - 4 + sw, ly + 5),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_mid"], [
                (lx - 2, ly), (lx + 2, ly),
                (lx + 2 + sw, ly + 4), (lx - 2 + sw, ly + 4),
            ])
            # Iron greave (armored shin)
            greave = [
                (lx - 4 + sw, ly + 6), (lx + 4 + sw, ly + 6),
                (lx + 4 + sw, ly + 12), (lx - 4 + sw, ly + 12),
            ]
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_darkest"], greave)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_dark"], [
                (lx - 3 + sw, ly + 7), (lx + 3 + sw, ly + 7),
                (lx + 3 + sw, ly + 11), (lx - 3 + sw, ly + 11),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_mid"], [
                (lx - 2 + sw, ly + 8), (lx + 2 + sw, ly + 8),
                (lx + 2 + sw, ly + 10), (lx - 2 + sw, ly + 10),
            ])
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_light"],
                             (lx - 1 + sw, ly + 8, 2, 1))
            # Bronze rivets
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                             (lx - 3 + sw, ly + 8, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                             (lx + 2 + sw, ly + 8, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_shine"],
                             (lx + 2 + sw, ly + 8, 1, 1))
            # BEAST CLAW FEET (3 sharp claws)
            foot_y = ly + 13
            for c_i, cx_off in enumerate((-3, 0, 3)):
                cx_pos = lx + cx_off + sw
                # Claw
                _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], [
                    (cx_pos + 1, foot_y),
                    (cx_pos + 1 + facing, foot_y + 4),
                    (cx_pos - 1 + facing, foot_y + 4),
                ])
                _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_darkest"], [
                    (cx_pos, foot_y),
                    (cx_pos + facing, foot_y + 4),
                    (cx_pos - 1, foot_y + 3),
                ])
                _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_mid"], [
                    (cx_pos, foot_y + 1),
                    (cx_pos + facing // 2, foot_y + 3),
                    (cx_pos, foot_y + 2),
                ])
                pygame.draw.rect(surface, _NS_karzhul.PALETTE["claw_shine"],
                                 (cx_pos, foot_y + 1, 1, 1))

    # ── TORSO (muscular chest with armor) ────────────────────
    def _draw_torso(surface, cx, cy, facing, phase):
        breath = math.sin(phase * 0.6) * 1
        # Big broad torso
        torso = [
            (cx - 15, cy - 8), (cx - 12, cy - 12),
            (cx + 8, cy - 12), (cx + 15, cy - 8),
            (cx + 17, cy), (cx + 15, cy + 8),
            (cx + 10, cy + 14), (cx - 8, cy + 14),
            (cx - 15, cy + 8), (cx - 17, cy),
        ]
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_darkest"], torso)
        # Fur main
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_dark"], [
            (cx - 14, cy - 7), (cx - 11, cy - 11),
            (cx + 7, cy - 11), (cx + 14, cy - 7),
            (cx + 16, cy), (cx + 14, cy + 7),
            (cx + 9, cy + 13), (cx - 7, cy + 13),
            (cx - 14, cy + 7), (cx - 16, cy),
        ])
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_mid"], [
            (cx - 10, cy - 5), (cx - 8, cy - 9),
            (cx + 4, cy - 9), (cx + 10, cy - 5),
            (cx + 12, cy), (cx + 10, cy + 6),
            (cx + 4, cy + 10), (cx - 4, cy + 10),
            (cx - 10, cy + 6), (cx - 12, cy),
        ])
        # Chest fur highlight (silver stripe)
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_light"], [
            (cx - 4, cy - 6), (cx, cy - 8), (cx + 4, cy - 6),
            (cx + 5, cy), (cx + 3, cy + 6), (cx - 3, cy + 6),
            (cx - 5, cy),
        ])
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_shine"], [
            (cx - 2, cy - 4), (cx + 2, cy - 4),
            (cx + 3, cy), (cx - 3, cy),
        ])
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_edge"],
                         (cx - 1, cy - 3, 2, 1))
        # Chest plate (iron)
        chest = [
            (cx - 8, cy - 4), (cx + 8, cy - 4),
            (cx + 10, cy + 4), (cx + 6, cy + 10),
            (cx - 6, cy + 10), (cx - 10, cy + 4),
        ]
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_darkest"], chest)
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_dark"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3),
            (cx + 9, cy + 4), (cx + 5, cy + 9),
            (cx - 5, cy + 9), (cx - 9, cy + 4),
        ])
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_mid"], [
            (cx - 5, cy - 2), (cx + 5, cy - 2),
            (cx + 7, cy + 3), (cx + 3, cy + 7),
            (cx - 3, cy + 7), (cx - 7, cy + 3),
        ])
        # Central emblem (skull / X)
        pygame.draw.line(surface, _NS_karzhul.PALETTE["bronze_dark"],
                         (cx - 3, cy + 1), (cx + 3, cy + 5), 2)
        pygame.draw.line(surface, _NS_karzhul.PALETTE["bronze_dark"],
                         (cx + 3, cy + 1), (cx - 3, cy + 5), 2)
        pygame.draw.line(surface, _NS_karzhul.PALETTE["bronze_mid"],
                         (cx - 3, cy + 1), (cx + 3, cy + 5), 1)
        pygame.draw.line(surface, _NS_karzhul.PALETTE["bronze_mid"],
                         (cx + 3, cy + 1), (cx - 3, cy + 5), 1)
        # Bronze rivets on chest edges
        for rv in ((-6, -2), (6, -2), (-8, 3), (8, 3), (-4, 8), (4, 8)):
            rvx = cx + rv[0]
            rvy = cy + rv[1]
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_dark"],
                             (rvx - 1, rvy - 1, 2, 2))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                             (rvx - 1, rvy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_shine"],
                             (rvx - 1, rvy - 1, 1, 1))
        # Chest plate highlight
        pygame.draw.line(surface, _NS_karzhul.PALETTE["iron_shine"],
                         (cx - 4, cy - 3), (cx + 4, cy - 3), 1)
        # Leather straps crossing torso
        pygame.draw.line(surface, _NS_karzhul.PALETTE["leather_darkest"],
                         (cx - 14, cy - 6), (cx + 12, cy + 6), 2)
        pygame.draw.line(surface, _NS_karzhul.PALETTE["leather_dark"],
                         (cx - 14, cy - 6), (cx + 12, cy + 6), 1)
        # Belt at waist with bronze buckle
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["leather_darkest"],
                         (cx - 14, cy + 9, 28, 4))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["leather_dark"],
                         (cx - 13, cy + 10, 26, 2))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["leather_mid"],
                         (cx - 13, cy + 10, 26, 1))
        # Belt buckle
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_dark"],
                         (cx - 3, cy + 9, 6, 5))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                         (cx - 2, cy + 10, 4, 3))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_light"],
                         (cx - 2, cy + 10, 4, 1))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_shine"],
                         (cx - 1, cy + 10, 2, 1))

    def _draw_shoulder_armor(surface, cx, cy, facing, phase):
        """Big spiked pauldrons on shoulders."""
        for side in (-1, 1):
            sx = cx + side * 13
            sy = cy - 9
            # Pauldron dome
            pd_pts = [
                (sx - 5, sy + 4),
                (sx - 6, sy), (sx - 3, sy - 5),
                (sx + 3, sy - 5), (sx + 6, sy),
                (sx + 5, sy + 4),
            ]
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 2) for p in pd_pts])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_darkest"], pd_pts)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_dark"], [
                (sx - 4, sy + 3),
                (sx - 5, sy), (sx - 2, sy - 4),
                (sx + 2, sy - 4), (sx + 5, sy),
                (sx + 4, sy + 3),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_mid"], [
                (sx - 3, sy + 2),
                (sx - 3, sy), (sx - 1, sy - 3),
                (sx + 1, sy - 3), (sx + 3, sy),
                (sx + 3, sy + 2),
            ])
            # Highlight
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_light"],
                             (sx - 1, sy - 2, 2, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_shine"],
                             (sx - 1, sy - 2, 1, 1))
            # 3 spikes on top
            for spk_i, sx_off in enumerate((-3, 0, 3)):
                spk_x = sx + sx_off
                spk_top = sy - 5 - (2 if spk_i == 1 else 1)
                _NS_karzhul._poly(surface,
                                  _NS_karzhul.PALETTE["shadow_deep"], [
                    (spk_x + 1, spk_top + 1),
                    (spk_x + 2, sy - 4),
                    (spk_x, sy - 4),
                ])
                _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_darkest"], [
                    (spk_x, spk_top),
                    (spk_x + 1, sy - 4),
                    (spk_x - 1, sy - 4),
                ])
                _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_mid"], [
                    (spk_x, spk_top),
                    (spk_x, sy - 4),
                    (spk_x - 1, sy - 4),
                ])
                pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_shine"],
                                 (spk_x, spk_top, 1, 1))
            # Rivets around edge
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                             (sx - 4, sy + 2, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                             (sx + 3, sy + 2, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_shine"],
                             (sx + 3, sy + 2, 1, 1))

    # ── BACK ARM ─────────────────────────────────────────────
    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        back = -facing
        sx = cx + back * 12
        sy = cy - 5
        sway = math.sin(phase * 0.7) * 2
        ex = sx + back * 6
        ey = sy + 12 + int(sway)
        hx = ex + back * 3
        hy = ey + 10
        # Upper arm (fur)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["shadow_deep"],
                            (sx + 1, sy + 2), (ex + 1, ey + 2), 9)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_darkest"],
                            (sx, sy), (ex, ey), 8)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_dark"],
                            (sx, sy), (ex, ey), 6)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_mid"],
                            (sx, sy - 1), (ex, ey - 1), 3)
        # Forearm (skin + iron bracer)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["shadow_deep"],
                            (ex + 1, ey + 2), (hx + 1, hy + 2), 7)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_darkest"],
                            (ex, ey), (hx, hy), 6)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_dark"],
                            (ex, ey), (hx, hy), 4)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_mid"],
                            (ex, ey - 1), (hx, hy - 1), 2)
        # Iron bracer
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_darkest"],
                         (ex - 3, ey + 4, 6, 4))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_dark"],
                         (ex - 3, ey + 5, 6, 2))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_mid"],
                         (ex - 3, ey + 5, 6, 1))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                         (ex - 2, ey + 5, 1, 1))
        # Small back claws (3 claws)
        for c_i, off in enumerate((-3, 0, 3)):
            cx_c = hx + off + back * 2
            cy_c = hy + 3
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_darkest"], [
                (cx_c, hy),
                (cx_c + back * 2, cy_c + 2),
                (cx_c - back, cy_c),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_dark"], [
                (cx_c, hy),
                (cx_c + back, cy_c + 1),
                (cx_c, cy_c),
            ])
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["claw_shine"],
                             (cx_c + back * 2, cy_c + 2, 1, 1))

    # ── FRONT ARM + BIG CLAWS ────────────────────────────────
    def _draw_front_arm(surface, cx, cy, facing, phase, action, progress):
        base_angle = -math.pi / 6
        if action == "attack":
            if progress < 0.3:
                t = progress / 0.3
                base_angle = -math.pi / 6 - t * math.pi / 2.5
            elif progress < 0.55:
                t = (progress - 0.3) / 0.25
                base_angle = -math.pi / 6 - math.pi / 2.5 + t * (math.pi * 1.15)
            else:
                t = (progress - 0.55) / 0.45
                base_angle = -math.pi / 6 + (math.pi * 0.75 * (1 - t))
        else:
            base_angle += math.sin(phase * 0.6) * 0.1

        sx = cx + facing * 12
        sy = cy - 5
        arm_len = 20
        hx = sx + int(math.cos(base_angle) * arm_len) * facing
        hy = sy + int(math.sin(base_angle) * arm_len)
        ex = sx + int(math.cos(base_angle) * arm_len * 0.5) * facing
        ey = sy + int(math.sin(base_angle) * arm_len * 0.5) + 2

        # Upper arm (fur, big & muscular)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["shadow_deep"],
                            (sx + 1, sy + 2), (ex + 1, ey + 2), 10)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_darkest"],
                            (sx, sy), (ex, ey), 9)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_dark"],
                            (sx, sy), (ex, ey), 7)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_mid"],
                            (sx, sy - 1), (ex, ey - 1), 4)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_light"],
                            (sx, sy - 2), (ex, ey - 2), 1)
        # Forearm (grey skin exposed)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["shadow_deep"],
                            (ex + 1, ey + 2), (hx + 1, hy + 2), 8)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_darkest"],
                            (ex, ey), (hx, hy), 7)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_dark"],
                            (ex, ey), (hx, hy), 5)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_mid"],
                            (ex, ey - 1), (hx, hy - 1), 3)
        _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["skin_light"],
                            (ex, ey - 2), (hx, hy - 2), 1)
        # Iron bracer with spike
        br_perp_x = int(math.cos(base_angle + math.pi / 2) * 3) * facing
        br_perp_y = int(math.sin(base_angle + math.pi / 2) * 3)
        br_center_x = int(ex + (hx - ex) * 0.5)
        br_center_y = int(ey + (hy - ey) * 0.5)
        # Bracer band
        br_pts = [
            (br_center_x + br_perp_x, br_center_y + br_perp_y),
            (br_center_x + br_perp_x + int(math.cos(base_angle) * 5) * facing,
             br_center_y + br_perp_y + int(math.sin(base_angle) * 5)),
            (br_center_x - br_perp_x + int(math.cos(base_angle) * 5) * facing,
             br_center_y - br_perp_y + int(math.sin(base_angle) * 5)),
            (br_center_x - br_perp_x, br_center_y - br_perp_y),
        ]
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_darkest"], br_pts)
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["iron_dark"], [
            (br_pts[0][0], br_pts[0][1]),
            (br_pts[1][0], br_pts[1][1]),
            (br_pts[2][0], br_pts[2][1]),
            (br_pts[3][0], br_pts[3][1]),
        ])
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_light"],
                         (br_center_x, br_center_y - 1, 2, 1))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_shine"],
                         (br_center_x + 1, br_center_y - 1, 1, 1))
        # HAND (fist palm)
        _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1), 5)
        _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["skin_darkest"],
                              (hx, hy), 5)
        _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["skin_dark"],
                              (hx, hy), 4)
        _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["skin_mid"],
                              (hx - 1, hy - 1), 3)
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 2, 1))
        # BIG CURVED CLAWS (main weapon — 4 talons)
        _NS_karzhul._draw_big_claws(surface, hx, hy, facing, base_angle, phase)

    def _draw_big_claws(surface, hx, hy, facing, arm_angle, phase):
        """4 huge curved talons extending from hand."""
        # Base position offset from palm
        offset_dist = 6
        base_x = hx + int(math.cos(arm_angle) * offset_dist) * facing
        base_y = hy + int(math.sin(arm_angle) * offset_dist)

        # 4 claws with slightly different angles
        claw_configs = [
            (-0.35, 12),  # top claw
            (-0.1, 14),   # 2nd
            (0.15, 13),   # 3rd
            (0.4, 11),    # bottom
        ]
        for c_i, (ang_off, length) in enumerate(claw_configs):
            claw_angle = arm_angle + ang_off
            # Curved path (base -> mid -> tip)
            mid_x = base_x + int(math.cos(claw_angle) * length * 0.5) * facing
            mid_y = base_y + int(math.sin(claw_angle) * length * 0.5)
            # Tip curves slightly inward
            tip_angle = claw_angle + 0.4
            tip_x = mid_x + int(math.cos(tip_angle) * length * 0.55) * facing
            tip_y = mid_y + int(math.sin(tip_angle) * length * 0.55)

            # Perpendicular for claw width
            perp = claw_angle + math.pi / 2
            base_w = 3
            base_a_x = base_x + int(math.cos(perp) * base_w)
            base_a_y = base_y + int(math.sin(perp) * base_w)
            base_b_x = base_x - int(math.cos(perp) * base_w)
            base_b_y = base_y - int(math.sin(perp) * base_w)

            # Shadow
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_a_x + 1, base_a_y + 1),
                (base_b_x + 1, base_b_y + 1),
            ])
            # Base claw shape (triangle-ish curved)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_darkest"], [
                (tip_x, tip_y),
                (mid_x + int(math.cos(perp) * 2), mid_y + int(math.sin(perp) * 2)),
                (base_a_x, base_a_y),
                (base_b_x, base_b_y),
                (mid_x - int(math.cos(perp) * 1), mid_y - int(math.sin(perp) * 1)),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_dark"], [
                (tip_x, tip_y),
                (mid_x + int(math.cos(perp) * 1), mid_y + int(math.sin(perp) * 1)),
                (base_a_x, base_a_y - 1 if perp > 0 else base_a_y + 1),
                (base_b_x, base_b_y),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["claw_mid"], [
                (tip_x, tip_y),
                (mid_x, mid_y),
                (base_x, base_y),
            ])
            # Bright edge (blade shine)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["claw_light"],
                                (base_x, base_y), (tip_x, tip_y), 1)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["claw_shine"],
                                (mid_x, mid_y), (tip_x, tip_y), 1)
            # Tip glow
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["claw_edge"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))
            # Rings/joints on base of claw
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_dark"],
                             (base_x - 1, base_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_mid"],
                             (base_x - 1, base_y - 1, 1, 1))

    # ── TAIL (fluffy wolf tail curling back) ─────────────────
    def _draw_tail(surface, cx, cy, facing, phase, action):
        back = -facing
        base_x = cx + back * 14
        base_y = cy + 4
        wave = math.sin(phase * 1.0) * 4
        if action == "walk":
            wave = math.sin(phase * 1.4) * 6
        segments = 6
        pts = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back * (10 + t * 22))
            y_off = int(3 + t * 4 - t * t * 3)
            wave_off = math.sin(phase * 1.0 + t * math.pi * 1.2) * (3 + t * 3)
            y_off += int(wave_off)
            pts.append((base_x + x_off, base_y + y_off))
        # Draw as fluffy segments (thick fur)
        for i in range(len(pts) - 1):
            thickness = max(3, 10 - i)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["shadow_deep"],
                                (pts[i][0] + 2, pts[i][1] + 2),
                                (pts[i + 1][0] + 2, pts[i + 1][1] + 2),
                                thickness + 1)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_darkest"],
                                pts[i], pts[i + 1], thickness)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_dark"],
                                pts[i], pts[i + 1], max(1, thickness - 2))
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_mid"],
                                (pts[i][0], pts[i][1] - 1),
                                (pts[i + 1][0], pts[i + 1][1] - 1),
                                max(1, thickness - 4))
            if thickness > 5:
                _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_light"],
                                    (pts[i][0], pts[i][1] - 2),
                                    (pts[i + 1][0], pts[i + 1][1] - 2),
                                    max(1, thickness - 7))
        # Fluffy tail tip (white)
        if len(pts) >= 2:
            end = pts[-1]
            _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["shadow_deep"],
                                  (end[0] + 1, end[1] + 1), 4)
            _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["fur_dark"],
                                  end, 4)
            _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["fur_mid"],
                                  end, 3)
            _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["fur_light"],
                                  (end[0] - 1, end[1] - 1), 2)
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_shine"],
                             (end[0] - 1, end[1] - 1, 2, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_edge"],
                             (end[0] - 1, end[1] - 1, 1, 1))

    # ── HEAD (wolf/beast head with feral face) ───────────────
    def _draw_head(surface, cx, cy, facing, phase, action):
        hx = cx + facing * 4
        hy = cy - 22
        # Head shape (elongated wolf snout)
        head = [
            (hx - 9, hy + 5),   # back bottom
            (hx - 10, hy - 1),  # back top
            (hx - 7, hy - 8),   # crown back
            (hx - 2, hy - 10),  # top
            (hx + 4, hy - 9),   # top front
            (hx + 10, hy - 6),  # snout top back
            (hx + 15, hy - 3),  # snout top
            (hx + 17, hy),      # nose tip
            (hx + 15, hy + 3),  # snout bottom
            (hx + 10, hy + 5),  # snout back
            (hx + 3, hy + 8),   # jaw
            (hx - 5, hy + 7),   # jaw back
        ]
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head])
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_darkest"], head)
        # Fur main
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_dark"], [
            (hx - 8, hy + 4), (hx - 9, hy - 1),
            (hx - 6, hy - 7), (hx - 1, hy - 9),
            (hx + 3, hy - 8), (hx + 9, hy - 5),
            (hx + 14, hy - 2), (hx + 15, hy + 2),
            (hx + 9, hy + 4), (hx - 3, hy + 6),
        ])
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_mid"], [
            (hx - 6, hy), (hx - 4, hy - 6),
            (hx, hy - 8), (hx + 3, hy - 7),
            (hx + 7, hy - 4), (hx + 12, hy - 2),
            (hx + 13, hy), (hx + 8, hy + 2),
            (hx - 1, hy + 4),
        ])
        # Silver forehead patch
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_light"], [
            (hx - 3, hy - 4), (hx + 1, hy - 7),
            (hx + 5, hy - 5), (hx + 4, hy - 2),
            (hx - 1, hy - 2),
        ])
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_shine"],
                         (hx, hy - 5, 2, 1))

        # NOSE (black leather)
        nose_pts = [
            (hx + 13, hy - 1), (hx + 17, hy),
            (hx + 15, hy + 2), (hx + 13, hy + 1),
        ]
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], nose_pts)
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["skin_darkest"], [
            (hx + 13, hy), (hx + 16, hy + 1),
            (hx + 14, hy + 2),
        ])
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["skin_dark"],
                         (hx + 14, hy, 1, 1))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["skin_light"],
                         (hx + 15, hy, 1, 1))

        # SNOUT muzzle (lighter shade under nose)
        _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_light"], [
            (hx + 9, hy + 2), (hx + 14, hy + 2),
            (hx + 13, hy + 4), (hx + 8, hy + 4),
        ])
        pygame.draw.line(surface, _NS_karzhul.PALETTE["fur_shine"],
                         (hx + 10, hy + 3), (hx + 12, hy + 3), 1)

        # EYES (fiery amber)
        _NS_karzhul._draw_beast_eye(surface, hx + facing * 3, hy - 3,
                                    facing, phase)
        # Second smaller eye (side)
        _NS_karzhul._draw_beast_eye(surface, hx - facing * 3, hy - 2,
                                    facing, phase, small=True)

        # EARS (pointed wolf ears)
        _NS_karzhul._draw_wolf_ears(surface, hx, hy, facing, phase)

        # BONE CROWN / HORNS at top
        _NS_karzhul._draw_bone_crown(surface, hx, hy, facing, phase)

        # MOUTH + FANGS
        mouth_open = 0
        if action == "attack":
            progress = getattr(pygame, "_dummy", 0)
            # Use passed action to open jaw
            mouth_open = 4

        _NS_karzhul._draw_beast_mouth(surface, hx, hy, facing, phase, mouth_open)

    def _draw_beast_eye(surface, ex, ey, facing, phase, small=False):
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        size = 1 if small else 2
        # Socket
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["shadow_deep"],
                         (ex - size, ey - 1, size * 2 + 1, size + 1))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["eye_socket"],
                         (ex - size + 1, ey - 1, size * 2, size + 1))
        # Glow halo
        for r in range(5 if not small else 3, 0, -1):
            a = _NS_karzhul._alpha(90 * (5 - r) / 5 * pulse)
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["eye_mid"], a),
                                  (ex, ey), r)
        # Iris
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["eye_darkest"],
                         (ex - size + 1, ey, size * 2, size))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["eye_dark"],
                         (ex - size + 1, ey, size * 2 - 1, size))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["eye_mid"],
                         (ex, ey, size, size))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["eye_light"],
                         (ex, ey, 1, 1))
        # Hot spot
        if not small:
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
        # Vertical slit pupil
        pygame.draw.line(surface, _NS_karzhul.PALETTE["shadow_deep"],
                         (ex, ey - 1), (ex, ey + 1), 1)

    def _draw_wolf_ears(surface, hx, hy, facing, phase):
        """Pointed wolf ears on top of head."""
        twitch = math.sin(phase * 1.5) * 1
        for side in (-1, 1):
            base_x = hx + side * 4 + (2 if side > 0 else -3)
            base_y = hy - 6
            tip_x = base_x + side * 1
            tip_y = base_y - 6 + int(twitch * (1 if side > 0 else -1))
            # Outer fur
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], [
                (base_x + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
                (base_x + 3 * side, base_y + 1),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_darkest"], [
                (base_x, base_y),
                (tip_x, tip_y),
                (base_x + 3 * side, base_y),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_dark"], [
                (base_x + side, base_y),
                (tip_x, tip_y),
                (base_x + 2 * side, base_y),
            ])
            # Inner ear (pink-skin)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["skin_dark"], [
                (base_x + side, base_y),
                (int((tip_x + base_x + side) / 2), int((tip_y + base_y) / 2)),
                (base_x + 2 * side, base_y),
            ])
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["skin_mid"],
                             (base_x + side, base_y - 1, 1, 1))

    def _draw_bone_crown(surface, hx, hy, facing, phase):
        """Bone spikes / small horns at top of head."""
        # 3 spikes across crown
        for i, x_off in enumerate((-4, 0, 4)):
            sway = math.sin(phase * 0.4 + i * 0.5) * 0.5
            sp_x = hx + x_off
            sp_base_y = hy - 8
            sp_tip_y = sp_base_y - (5 if i == 1 else 3) - int(sway)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], [
                (sp_x + 1, sp_tip_y + 1),
                (sp_x + 2, sp_base_y),
                (sp_x, sp_base_y),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["bone_dark"], [
                (sp_x, sp_tip_y),
                (sp_x + 2, sp_base_y),
                (sp_x - 1, sp_base_y),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["bone_mid"], [
                (sp_x, sp_tip_y),
                (sp_x + 1, sp_base_y),
                (sp_x, sp_base_y),
            ])
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bone_light"],
                             (sp_x, sp_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bone_shine"],
                             (sp_x, sp_tip_y, 1, 1))

    def _draw_beast_mouth(surface, hx, hy, facing, phase, mouth_open):
        mouth_y = hy + 3
        mx_start = hx + facing * 5
        mx_end = hx + facing * 14
        if mouth_open > 0:
            # Open jaw
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], [
                (mx_start, mouth_y),
                (mx_end, mouth_y),
                (mx_end - facing * 1, mouth_y + mouth_open),
                (mx_start + facing * 1, mouth_y + mouth_open - 1),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["eye_darkest"], [
                (mx_start + facing, mouth_y + 1),
                (mx_end - facing, mouth_y + 1),
                (mx_end - facing * 2, mouth_y + mouth_open - 1),
                (mx_start + facing * 2, mouth_y + mouth_open - 2),
            ])
            # Blood-red glow inside
            for r in range(4, 0, -1):
                a = _NS_karzhul._alpha(120 * (4 - r) / 4)
                _NS_karzhul._aacircle(
                    surface, (*_NS_karzhul.PALETTE["blood_mid"], a),
                    (hx + facing * 10, mouth_y + mouth_open // 2), r,
                )
            # Upper fangs
            for i, x_off in enumerate((6, 9, 12)):
                fx = hx + int(x_off * facing)
                pygame.draw.line(surface, _NS_karzhul.PALETTE["bone_dark"],
                                 (fx, mouth_y), (fx, mouth_y + mouth_open - 1), 2)
                pygame.draw.line(surface, _NS_karzhul.PALETTE["bone_mid"],
                                 (fx, mouth_y), (fx, mouth_y + mouth_open - 1), 1)
                pygame.draw.rect(surface, _NS_karzhul.PALETTE["bone_light"],
                                 (fx, mouth_y + mouth_open - 1, 1, 1))
            # Lower fangs
            for i, x_off in enumerate((7, 10)):
                fx = hx + int(x_off * facing)
                pygame.draw.line(surface, _NS_karzhul.PALETTE["bone_dark"],
                                 (fx, mouth_y + mouth_open),
                                 (fx, mouth_y + mouth_open - 2), 1)
                pygame.draw.rect(surface, _NS_karzhul.PALETTE["bone_mid"],
                                 (fx, mouth_y + mouth_open - 2, 1, 1))
        else:
            # Closed with visible fang tips
            pygame.draw.line(surface, _NS_karzhul.PALETTE["shadow_deep"],
                             (mx_start, mouth_y + 1), (mx_end, mouth_y + 1), 1)
            # Small fang tips
            for x_off in (7, 10, 12):
                fx = hx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_karzhul.PALETTE["bone_mid"],
                                 (fx, mouth_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_karzhul.PALETTE["bone_light"],
                                 (fx, mouth_y + 2, 1, 1))

    # ── MANE (shaggy fur around neck/shoulders) ──────────────
    def _draw_mane_back(surface, cx, cy, facing, phase):
        """Big shaggy mane behind head."""
        mx = cx + facing * 2
        my = cy - 14
        sway = math.sin(phase * 0.4) * 1
        # Mane spikes (radiating outward)
        spikes = [
            (-10, -6, 8),
            (-11, -2, 9),
            (-10, 2, 8),
            (-9, 6, 7),
            (10, -6, 6),
            (11, -2, 7),
            (10, 2, 6),
            (9, 6, 5),
            (-4, -10, 6),
            (4, -10, 5),
        ]
        for (dx, dy, length) in spikes:
            base_x = mx + dx
            base_y = my + dy
            spike_ang = math.atan2(dy, dx)
            tip_x = base_x + int(math.cos(spike_ang) * length)
            tip_y = base_y + int(math.sin(spike_ang) * length) + int(sway)
            perp = spike_ang + math.pi / 2
            pa_x = base_x + int(math.cos(perp) * 2)
            pa_y = base_y + int(math.sin(perp) * 2)
            pb_x = base_x - int(math.cos(perp) * 2)
            pb_y = base_y - int(math.sin(perp) * 2)
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_darkest"],
                              [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_dark"], [
                (tip_x, tip_y),
                (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                (base_x, base_y),
            ])
            _NS_karzhul._poly(surface, _NS_karzhul.PALETTE["fur_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_light"],
                             (tip_x, tip_y, 1, 1))

    def _draw_mane_front(surface, cx, cy, facing, phase):
        """Front mane strands over chest."""
        mx = cx + facing * 2
        my = cy - 8
        for i, (dx, dy, length) in enumerate([
            (-6, 0, 6), (-3, 2, 5), (3, 2, 5), (6, 0, 6),
        ]):
            base_x = mx + dx
            base_y = my + dy
            sway = math.sin(phase * 0.5 + i * 0.4) * 1
            tip_x = base_x + int(dx * 0.3) + int(sway)
            tip_y = base_y + length
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_darkest"],
                                (base_x, base_y), (tip_x, tip_y), 3)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_dark"],
                                (base_x, base_y), (tip_x, tip_y), 2)
            _NS_karzhul._aaline(surface, _NS_karzhul.PALETTE["fur_mid"],
                                (base_x, base_y - 1), (tip_x, tip_y - 1), 1)
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_light"],
                             (tip_x, tip_y, 1, 1))

    # ============================================================
    # CLAW SWING TRAIL + IMPACT (melee attack)
    # ============================================================
    def _get_claw_tip(cx, cy, facing, progress):
        if progress < 0.3:
            t = progress / 0.3
            angle = -math.pi / 6 - t * math.pi / 2.5
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            angle = -math.pi / 6 - math.pi / 2.5 + t * (math.pi * 1.15)
        else:
            t = (progress - 0.55) / 0.45
            angle = -math.pi / 6 + (math.pi * 0.75 * (1 - t))
        sx = cx + facing * 12
        sy = cy - 5
        arm_len = 20
        hx = sx + int(math.cos(angle) * arm_len) * facing
        hy = sy + int(math.sin(angle) * arm_len)
        # Claw tip is further out
        claw_len = 18
        tip_x = hx + int(math.cos(angle) * claw_len) * facing
        tip_y = hy + int(math.sin(angle) * claw_len)
        return tip_x, tip_y, angle

    def _draw_claw_trail(surface, boss, cx, cy, facing, progress):
        """3-line parallel claw slash trail."""
        if progress < 0.28 or progress > 0.7:
            return
        if progress < 0.32:
            intensity = (progress - 0.28) / 0.04
        elif progress < 0.55:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.55) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        num = 12
        # Sample trails
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.2
            if sp < 0.28:
                continue
            tx, ty, ang = _NS_karzhul._get_claw_tip(cx, cy, facing, sp)
            trail.append((tx, ty, ang, i))
        if len(trail) < 2:
            return
        trail.reverse()
        ts = pygame.Surface((280, 280), pygame.SRCALPHA)
        ox = cx - 140
        oy = cy - 140
        # Draw 3 parallel slash lines (offset perpendicular)
        for line_offset in (-6, 0, 6):
            layers = [
                (_NS_karzhul.PALETTE["blood_dark"], 12, 100),
                (_NS_karzhul.PALETTE["blood_mid"], 8, 150),
                (_NS_karzhul.PALETTE["claw_light"], 4, 200),
                (_NS_karzhul.PALETTE["claw_edge"], 2, 240),
                (_NS_karzhul.PALETTE["white"], 1, 255),
            ]
            for color, max_w, max_a in layers:
                for i in range(len(trail) - 1):
                    p1, p2 = trail[i], trail[i + 1]
                    perp1 = p1[2] + math.pi / 2
                    perp2 = p2[2] + math.pi / 2
                    off1_x = int(math.cos(perp1) * line_offset)
                    off1_y = int(math.sin(perp1) * line_offset)
                    off2_x = int(math.cos(perp2) * line_offset)
                    off2_y = int(math.sin(perp2) * line_offset)
                    fade = 1.0 - (p1[3] / num)
                    a = _NS_karzhul._alpha(max_a * fade * intensity)
                    w = max(1, int(max_w * fade * 0.7))
                    if a > 0:
                        pygame.draw.line(
                            ts, (*color, a),
                            (p1[0] - ox + off1_x, p1[1] - oy + off1_y),
                            (p2[0] - ox + off2_x, p2[1] - oy + off2_y),
                            w,
                        )
        # Sparkles
        for i, (tx, ty, ang, idx) in enumerate(trail):
            fade = 1.0 - (idx / num)
            a = _NS_karzhul._alpha(240 * fade * intensity)
            if a <= 0 or i % 2 == 0:
                continue
            perp = ang + math.pi / 2
            for line_offset in (-6, 0, 6):
                spx = tx - ox + int(math.cos(perp) * line_offset)
                spy = ty - oy + int(math.sin(perp) * line_offset)
                pygame.draw.rect(ts, (*_NS_karzhul.PALETTE["white"], a),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(ts, (*_NS_karzhul.PALETTE["claw_edge"], a),
                                 (spx, spy, 1, 1))
        surface.blit(ts, (ox, oy))

    def _draw_claw_impact(surface, boss, cx, cy, facing, progress):
        if progress < 0.5 or progress > 0.65:
            return
        t = (progress - 0.5) / 0.15
        inten = math.sin(t * math.pi)
        tx, ty, _ = _NS_karzhul._get_claw_tip(cx, cy, facing, progress)
        ix = tx + facing * 4
        iy = ty
        r = int(4 + t * 12)
        a = _NS_karzhul._alpha(240 * inten)
        # Blood splash burst
        for rr in range(r + 3, 0, -2):
            ra = _NS_karzhul._alpha(a * (r + 3 - rr) / (r + 3))
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["blood_dark"], ra),
                                  (ix, iy), rr)
        _NS_karzhul._aacircle(surface, (*_NS_karzhul.PALETTE["blood_mid"], a),
                              (ix, iy), max(2, r - 4))
        _NS_karzhul._aacircle(surface, (*_NS_karzhul.PALETTE["blood_light"], a),
                              (ix, iy), max(1, r - 7))
        _NS_karzhul._aacircle(surface, (*_NS_karzhul.PALETTE["blood_hot"], a),
                              (ix, iy), max(1, r - 10))
        # Claw scratch marks radial
        for i in range(3):
            slash_ang = -math.pi / 4 + i * math.pi / 6
            ex1 = ix + int(math.cos(slash_ang) * r * 0.8) * facing
            ey1 = iy + int(math.sin(slash_ang) * r * 0.8)
            ex2 = ix + int(math.cos(slash_ang) * r * 1.3) * facing
            ey2 = iy + int(math.sin(slash_ang) * r * 1.3)
            pygame.draw.line(surface,
                             (*_NS_karzhul.PALETTE["claw_edge"], a),
                             (ex1, ey1), (ex2, ey2), 2)
            pygame.draw.line(surface,
                             (*_NS_karzhul.PALETTE["white"], a),
                             (ex1, ey1), (ex2, ey2), 1)
        # Blood droplets flying
        for i in range(6):
            ang = i * math.pi / 3 + progress * 5
            dist = int(r * 1.4)
            dx = ix + int(math.cos(ang) * dist)
            dy = iy + int(math.sin(ang) * dist)
            pygame.draw.rect(surface, (*_NS_karzhul.PALETTE["blood_mid"], a),
                             (dx, dy, 2, 2))
            pygame.draw.rect(surface, (*_NS_karzhul.PALETTE["blood_light"], a),
                             (dx, dy, 1, 1))

    # ============================================================
    # AMBIENT / FLOATING FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((140, 28), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            a = max(0, (14 - r) * 16)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 14 - r, 120 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (5, 3, 4, 170), (8, 8, 124, 12))
        surface.blit(sh, (x - 70, y - 14))

    def _draw_beast_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for r in range(85, 5, -5):
            a = _NS_karzhul._alpha((85 - r) * 1.0 * pulse)
            if a > 0:
                _NS_karzhul._aacircle(aura,
                                      (*_NS_karzhul.PALETTE["fur_darkest"], a),
                                      (110, 90), r)
        for r in range(50, 5, -3):
            a = _NS_karzhul._alpha((50 - r) * 1.2 * pulse)
            if a > 0:
                _NS_karzhul._aacircle(aura,
                                      (*_NS_karzhul.PALETTE["eye_darkest"], a),
                                      (110, 90), r)
        surface.blit(aura, (x - 110, y - 90))
        # Floating fur particles
        for i in range(10):
            ang = phase * 0.3 + i * math.pi / 5
            rd = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.45)
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["fur_edge"],
                             (sx, sy, 1, 1))

    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((140, 34), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(22, 3, -2):
            a = _NS_karzhul._alpha((22 - r) * 3 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_karzhul.PALETTE["fur_darkest"], a),
                    (70 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(14, 3, -2):
            a = _NS_karzhul._alpha((14 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_karzhul.PALETTE["fur_dark"], a),
                    (70 - r, 17 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising motes
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 18)
            a = _NS_karzhul._alpha(200 * (1 - t) * strength)
            if a > 0:
                _NS_karzhul._aacircle(surface,
                                      (*_NS_karzhul.PALETTE["fur_mid"], a),
                                      (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_karzhul.PALETTE["fur_light"], a),
                                 (sx, sy, 1, 1))
        # Ember eye-glow motes
        for i in range(3):
            t = (phase * 0.4 + i * 0.33) % 1.0
            ex = cx + int(math.sin(phase * 2 + i) * 20)
            ey = cy - int(t * 22)
            a = _NS_karzhul._alpha(180 * (1 - t) * strength)
            if a > 0:
                pygame.draw.rect(surface,
                                 (*_NS_karzhul.PALETTE["eye_mid"], a),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_karzhul.PALETTE["eye_light"], a),
                                 (ex, ey, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_karzhul._alpha(140 - i * 25)
                if a > 0:
                    _NS_karzhul._aacircle(
                        surface, (*_NS_karzhul.PALETTE["fur_dark"], a),
                        (sx, sy), max(2, 6 - i),
                    )

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_karzhul.PALETTE["fur_darkest"], 180),
                            (5, 14, 160, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_karzhul.PALETTE["eye_darkest"], 200),
                            (14, 16, 142, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_karzhul.PALETTE["eye_dark"], 180),
                            (25, 18, 120, 16), 1)
        # Runes/markings
        for i in range(8):
            ang = phase * 0.3 + i * math.pi / 4
            x1 = 85 + int(math.cos(ang) * 45)
            y1 = 25 + int(math.sin(ang) * 8)
            x2 = 85 + int(math.cos(ang) * 70)
            y2 = 25 + int(math.sin(ang) * 12)
            pygame.draw.line(ring, (*_NS_karzhul.PALETTE["eye_mid"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_karzhul.PALETTE["eye_light"],
                       _NS_karzhul._alpha(150 * pulse)),
                (10, 8, 150, 32), 1,
            )
        surface.blit(ring, (x - 85, y - 23))

    # ============================================================
    # SKILL Q — SAVAGE ROAR (empowered slash)
    # ============================================================
    def _draw_savageroar_glow(surface, boss, x, y, timer, phase):
        """Bright glow on hand/claws indicating empowered attack."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Glow on front hand
        hx = x + facing * 30
        hy = y - 8
        for r in range(10, 0, -1):
            a = _NS_karzhul._alpha(180 * (10 - r) / 10
                                    * (0.5 + 0.5 * math.sin(phase * 4)))
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["blood_mid"], a),
                                  (hx, hy), r)
        _NS_karzhul._aacircle(surface, _NS_karzhul.PALETTE["blood_hot"],
                              (hx, hy), 3)
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["white"],
                         (hx, hy, 1, 1))

    def _draw_savageroar_slash(surface, boss, x, y, timer, phase):
        """3-line X slash appearing on target."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_karzhul._target_position(boss, x, y)
        if progress < 0.3:
            return
        t = (progress - 0.3) / 0.7
        inten = math.sin(t * math.pi)
        a = _NS_karzhul._alpha(255 * inten)
        # 3 parallel slash lines
        slash_len = int(25 + t * 15)
        slash_ang = -math.pi / 6
        for line_i, off in enumerate((-8, 0, 8)):
            perp = slash_ang + math.pi / 2
            off_x = int(math.cos(perp) * off)
            off_y = int(math.sin(perp) * off)
            x1 = tx - int(math.cos(slash_ang) * slash_len) + off_x
            y1 = ty - int(math.sin(slash_ang) * slash_len) + off_y
            x2 = tx + int(math.cos(slash_ang) * slash_len) + off_x
            y2 = ty + int(math.sin(slash_ang) * slash_len) + off_y
            for w, color, wa in [
                (8, _NS_karzhul.PALETTE["blood_dark"], 100),
                (5, _NS_karzhul.PALETTE["blood_mid"], 150),
                (3, _NS_karzhul.PALETTE["blood_light"], 200),
                (2, _NS_karzhul.PALETTE["blood_hot"], 240),
                (1, _NS_karzhul.PALETTE["white"], 255),
            ]:
                la = _NS_karzhul._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la),
                                 (x1, y1), (x2, y2), w)
        # Center burst
        br = int(6 + t * 10)
        for r in range(br + 3, 0, -2):
            ra = _NS_karzhul._alpha(a * (br + 3 - r) / (br + 3))
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["blood_mid"], ra),
                                  (tx, ty), r)
        _NS_karzhul._aacircle(surface,
                              (*_NS_karzhul.PALETTE["blood_hot"], a),
                              (tx, ty), max(1, br // 2))
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["white"],
                         (tx, ty, 1, 1))
        # Sparks
        for i in range(6):
            sa = i * math.pi / 3 + phase * 0.5
            dist = int(slash_len * 0.6)
            ex = tx + int(math.cos(sa) * dist)
            ey = ty + int(math.sin(sa) * dist)
            pygame.draw.rect(surface,
                             (*_NS_karzhul.PALETTE["blood_hot"], a),
                             (ex, ey, 2, 2))

    # ============================================================
    # SKILL W — BATTLE ROAR (defensive aura shield)
    # ============================================================
    def _draw_battleroar_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            a = _NS_karzhul._alpha(200 - i * 60)
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["roar_dark"], a),
                                  (x, y + 45), r, 2)
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["roar_mid"], a),
                                  (x, y + 45), r, 1)

    def _draw_battleroar_overlay(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Ring layers
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 150), (1, 200),
        ]):
            _NS_karzhul._aacircle(bubble,
                                  (*_NS_karzhul.PALETTE["roar_dark"], alpha_val),
                                  center, r - i, thickness)
            _NS_karzhul._aacircle(bubble,
                                  (*_NS_karzhul.PALETTE["roar_mid"], alpha_val),
                                  center, r - i - 1, 1)
        # Sparkles on edge
        for i in range(20):
            ang = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(ang) * r)
            sy = center[1] + int(math.sin(ang) * r)
            pygame.draw.rect(bubble, _NS_karzhul.PALETTE["roar_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_karzhul.PALETTE["roar_hot"],
                             (sx, sy, 1, 1))
        # Inner shockwave rings
        for ring_i in range(3):
            ring_r = int(r * (0.4 + ring_i * 0.2)
                         + math.sin(phase * 3 + ring_i) * 3)
            ra = _NS_karzhul._alpha(120 + math.sin(phase * 4 + ring_i) * 40)
            _NS_karzhul._aacircle(bubble,
                                  (*_NS_karzhul.PALETTE["roar_light"], ra),
                                  center, ring_r, 1)
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Energy tendrils
        for i in range(8):
            ang = phase * 0.8 + i * math.pi / 4
            end_x = x + int(math.cos(ang) * (r + 10))
            end_y = y + int(math.sin(ang) * (r + 10))
            a = _NS_karzhul._alpha(180 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface,
                             (*_NS_karzhul.PALETTE["roar_light"], a),
                             (x + int(math.cos(ang) * r),
                              y + int(math.sin(ang) * r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["roar_hot"],
                             (end_x, end_y, 1, 1))

    # ============================================================
    # SKILL E — BOLA STRIKE (projectile with rope)
    # ============================================================
    def _draw_bolastrike(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_karzhul._target_position(boss, x, y)
        if progress < 0.15:
            return
        t = (progress - 0.15) / 0.85
        t = max(0.0, min(1.0, t))
        start_x = x + facing * 22
        start_y = y - 4
        # Bola arcs slightly (gravity)
        bx = int(start_x + (tx - start_x) * t)
        arc = -math.sin(t * math.pi) * 20
        by = int(start_y + (ty - start_y) * t + arc)

        # Rope trail from source to bola (fading tether)
        segments = 6
        for seg_i in range(segments):
            seg_t = seg_i / segments
            sx = int(start_x + (bx - start_x) * seg_t)
            sy_arc = -math.sin(seg_t * math.pi) * arc * (1 - seg_t)
            sy = int(start_y + (by - start_y) * seg_t + sy_arc)
            sx2_t = (seg_i + 1) / segments
            sx2 = int(start_x + (bx - start_x) * sx2_t)
            sy2_arc = -math.sin(sx2_t * math.pi) * arc * (1 - sx2_t)
            sy2 = int(start_y + (by - start_y) * sx2_t + sy2_arc)
            a = _NS_karzhul._alpha(200 * (1 - abs(seg_t - 0.5) * 0.5))
            pygame.draw.line(surface, (*_NS_karzhul.PALETTE["rope_dark"], a),
                             (sx, sy), (sx2, sy2), 2)
            pygame.draw.line(surface, (*_NS_karzhul.PALETTE["rope_mid"], a),
                             (sx, sy), (sx2, sy2), 1)

        # BOLA (3 weighted balls connected by ropes)
        rot = phase * 4 + t * math.pi * 6
        for ball_i in range(3):
            ball_ang = rot + ball_i * math.pi * 2 / 3
            ball_r = 5
            ball_x = bx + int(math.cos(ball_ang) * ball_r)
            ball_y = by + int(math.sin(ball_ang) * ball_r * 0.7)
            # Ropes connecting to center
            pygame.draw.line(surface, _NS_karzhul.PALETTE["rope_dark"],
                             (bx, by), (ball_x, ball_y), 2)
            pygame.draw.line(surface, _NS_karzhul.PALETTE["rope_mid"],
                             (bx, by), (ball_x, ball_y), 1)
            # Weight ball (bronze/iron)
            _NS_karzhul._aacircle(surface,
                                  _NS_karzhul.PALETTE["shadow_deep"],
                                  (ball_x + 1, ball_y + 1), 3)
            _NS_karzhul._aacircle(surface,
                                  _NS_karzhul.PALETTE["iron_darkest"],
                                  (ball_x, ball_y), 3)
            _NS_karzhul._aacircle(surface,
                                  _NS_karzhul.PALETTE["iron_dark"],
                                  (ball_x, ball_y), 2)
            _NS_karzhul._aacircle(surface,
                                  _NS_karzhul.PALETTE["bronze_mid"],
                                  (ball_x - 1, ball_y - 1), 1)
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["bronze_shine"],
                             (ball_x - 1, ball_y - 1, 1, 1))
        # Center hub
        _NS_karzhul._aacircle(surface,
                              _NS_karzhul.PALETTE["shadow_deep"],
                              (bx + 1, by + 1), 2)
        _NS_karzhul._aacircle(surface,
                              _NS_karzhul.PALETTE["iron_dark"],
                              (bx, by), 2)
        pygame.draw.rect(surface, _NS_karzhul.PALETTE["iron_light"],
                         (bx, by, 1, 1))

        # Impact - root effect on target
        if t > 0.9:
            st = (t - 0.9) / 0.1
            r = int(10 + st * 15)
            a = _NS_karzhul._alpha(240 * (1 - st))
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["rope_dark"], a),
                                  (tx, ty), r, 3)
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["rope_mid"], a),
                                  (tx, ty), max(1, r - 3), 2)
            # Root chains around target
            for i in range(6):
                ang = i * math.pi / 3 + phase
                ex = tx + int(math.cos(ang) * r)
                ey = ty + int(math.sin(ang) * r)
                pygame.draw.line(surface,
                                 (*_NS_karzhul.PALETTE["rope_mid"], a),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface,
                                 (*_NS_karzhul.PALETTE["bronze_light"], a),
                                 (ex, ey, 2, 2))

    # ============================================================
    # SKILL R — THRILL OF THE HUNT (leap dash)
    # ============================================================
    def _draw_hunt_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_karzhul._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Trail path on ground
        if 0.3 < progress < 0.75:
            t = (progress - 0.3) / 0.45
            # Trail from origin to current position
            for i in range(8):
                seg_t = t * (i / 8)
                sx = int(x + (tx - x) * seg_t)
                a = _NS_karzhul._alpha(200 - i * 20)
                _NS_karzhul._aacircle(surface,
                                      (*_NS_karzhul.PALETTE["hunt_dark"], a),
                                      (sx, y + 45), max(2, 6 - i))
                pygame.draw.rect(surface,
                                 (*_NS_karzhul.PALETTE["hunt_light"], a),
                                 (sx, y + 45, 1, 1))
        # Landing ground scorch
        if progress > 0.7:
            t = (progress - 0.7) / 0.3
            r = int(20 + t * 15)
            a = _NS_karzhul._alpha(200 * (1 - t))
            pygame.draw.ellipse(surface,
                                (*_NS_karzhul.PALETTE["hunt_dark"], a),
                                (tx - r, ty + 40 - r // 3,
                                 r * 2, r * 2 // 3))

    def _draw_hunt_leap(surface, boss, x, y, timer, phase):
        tx, ty = _NS_karzhul._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind-up: glowing at boss position (crouching)
            t = progress / 0.3
            for r in range(15, 3, -2):
                a = _NS_karzhul._alpha(150 * (15 - r) / 15 * t)
                _NS_karzhul._aacircle(surface,
                                      (*_NS_karzhul.PALETTE["hunt_mid"], a),
                                      (x, y), r)
            # Target indicator
            ta = _NS_karzhul._alpha(200 * t)
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["hunt_light"], ta),
                                  (tx, ty), 12, 2)
            # Crosshair X
            pygame.draw.line(surface,
                             (*_NS_karzhul.PALETTE["hunt_light"], ta),
                             (tx - 8, ty - 8), (tx + 8, ty + 8), 1)
            pygame.draw.line(surface,
                             (*_NS_karzhul.PALETTE["hunt_light"], ta),
                             (tx + 8, ty - 8), (tx - 8, ty + 8), 1)
        elif progress < 0.75:
            # Leap in progress - motion streaks (handled in pose)
            pass
        else:
            # Impact at target
            t = (progress - 0.75) / 0.25
            inten = math.sin(t * math.pi)
            r = int(15 + t * 25)
            a = _NS_karzhul._alpha(255 * inten)
            for rr in range(r + 4, 0, -3):
                ra = _NS_karzhul._alpha(a * (r + 4 - rr) / (r + 4))
                _NS_karzhul._aacircle(surface,
                                      (*_NS_karzhul.PALETTE["hunt_dark"], ra),
                                      (tx, ty), rr)
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["hunt_mid"], a),
                                  (tx, ty), max(2, r - 5))
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["hunt_light"], a),
                                  (tx, ty), max(1, r - 10))
            _NS_karzhul._aacircle(surface,
                                  (*_NS_karzhul.PALETTE["hunt_shine"], a),
                                  (tx, ty), max(1, r - 15))
            pygame.draw.rect(surface, _NS_karzhul.PALETTE["white"],
                             (tx, ty, 1, 1))
            # Radial claw slashes
            for i in range(4):
                slash_ang = i * math.pi / 4 + t * 2
                sx1 = tx + int(math.cos(slash_ang) * r * 0.5)
                sy1 = ty + int(math.sin(slash_ang) * r * 0.5)
                sx2 = tx + int(math.cos(slash_ang) * r * 1.2)
                sy2 = ty + int(math.sin(slash_ang) * r * 1.2)
                pygame.draw.line(surface,
                                 (*_NS_karzhul.PALETTE["blood_light"], a),
                                 (sx1, sy1), (sx2, sy2), 3)
                pygame.draw.line(surface,
                                 (*_NS_karzhul.PALETTE["white"], a),
                                 (sx1, sy1), (sx2, sy2), 1)
            # Blood splash
            for i in range(8):
                ang = i * math.pi / 4 + phase
                dist = int(r * 0.8)
                bx = tx + int(math.cos(ang) * dist)
                by = ty + int(math.sin(ang) * dist)
                pygame.draw.rect(surface,
                                 (*_NS_karzhul.PALETTE["blood_hot"], a),
                                 (bx, by, 2, 2))


# ====================================================================================================
# XERAKKUTH - MINI BOSS
# ====================================================================================================

class _NS_xerakkuth:
    """Namespace xerakkuth - giant desert scorpion boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Chitin (dark bronze/gold armor plating)
        "chitin_darkest": (25, 15, 5),
        "chitin_dark": (75, 45, 15),
        "chitin_mid": (150, 100, 35),
        "chitin_light": (215, 160, 65),
        "chitin_shine": (250, 215, 130),
        "chitin_edge": (255, 240, 190),

        # Under-plating (softer belly, joints)
        "under_darkest": (18, 12, 8),
        "under_dark": (55, 40, 25),
        "under_mid": (110, 80, 45),
        "under_light": (170, 130, 75),

        # Bronze accents (metal-like reinforced plates)
        "bronze_dark": (85, 55, 15),
        "bronze_mid": (170, 120, 40),
        "bronze_light": (230, 180, 80),
        "bronze_shine": (255, 235, 150),

        # Sand (golden desert sand)
        "sand_darkest": (55, 35, 10),
        "sand_dark": (130, 90, 30),
        "sand_mid": (215, 165, 55),
        "sand_light": (250, 215, 120),
        "sand_hot": (255, 240, 175),
        "sand_shine": (255, 250, 220),

        # Green eyes (predator emerald)
        "eye_socket": (5, 8, 4),
        "eye_dark": (10, 60, 25),
        "eye_mid": (40, 175, 75),
        "eye_light": (130, 240, 155),
        "eye_glow": (200, 255, 220),

        # Caustic venom (toxic yellow-green)
        "venom_darkest": (20, 35, 8),
        "venom_dark": (70, 110, 20),
        "venom_mid": (155, 210, 45),
        "venom_light": (215, 250, 95),
        "venom_hot": (245, 255, 160),

        # Stinger/spike tips (glowing hot)
        "stinger_dark": (60, 30, 5),
        "stinger_mid": (170, 100, 25),
        "stinger_light": (240, 180, 70),
        "stinger_hot": (255, 230, 140),

        # Ground crack (glowing amber)
        "crack_dark": (90, 40, 5),
        "crack_mid": (200, 110, 25),
        "crack_light": (255, 190, 80),

        # Shadow
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xerakkuth._clamp(color)
        if _NS_xerakkuth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_xerakkuth._clamp(color)
        if _NS_xerakkuth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_xerakkuth._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 250 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xerakkuth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xerakkuth._detect_moving(boss)
        _NS_xerakkuth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xer_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_xerakkuth._draw_sand_aura(surface, x, y, pulse)
        _NS_xerakkuth._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX behind body
        if active_skill == "w":
            _NS_xerakkuth._draw_sandstorm_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_xerakkuth._draw_epicenter_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "q":
            _NS_xerakkuth._draw_burrowstrike_ground(
                surface, boss, x, y, skill_timer, pulse
            )

        # Body
        if active_skill == "q":
            _NS_xerakkuth._draw_burrowstrike_pose(
                surface, boss, x, y, skill_timer, pulse
            )
        elif attacking:
            _NS_xerakkuth._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_xerakkuth._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_xerakkuth._draw_idle_pose(surface, boss, x, y)

        # Foreground FX
        if active_skill == "w":
            _NS_xerakkuth._draw_sandstorm_foreground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_xerakkuth._draw_caustic_finale(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_xerakkuth._draw_epicenter_foreground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "q":
            _NS_xerakkuth._draw_burrowstrike_emerge(
                surface, boss, x, y, skill_timer, pulse
            )

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_xer_prev_timer", 0))
        active = bool(getattr(boss, "_xer_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._xer_attack_active = True
            boss._xer_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xer_attack_frame = int(
                getattr(boss, "_xer_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._xer_attack_active = False
            boss._xer_attack_frame = 0
            active = False
        boss._xer_prev_timer = timer
        boss._xer_attack_progress = (
            min(1.0, getattr(boss, "_xer_attack_frame", 0) / max(1, cd - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_xer_last_x"):
            boss._xer_last_x = boss.x
            boss._xer_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xer_last_x)
        dy = abs(boss.y - boss._xer_last_y)
        boss._xer_last_x = boss.x
        boss._xer_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (floating movement)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        _NS_xerakkuth._draw_shadow(surface, x, y + 52)
        _NS_xerakkuth._draw_sand_wisps(surface, x, y + 48, boss.pulse)
        _NS_xerakkuth._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )

    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.4
        bob = int(math.sin(ph * 1.1) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_xerakkuth._draw_shadow(surface, x + sway, y + 52)
        _NS_xerakkuth._draw_sand_wisps(
            surface, x + sway, y + 48, ph, trail=True, facing=boss.direction
        )
        _NS_xerakkuth._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_xer_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 5)
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lift = int(5 - t * 8)
            lunge = int((-3 + t * 12)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lift = int(-3 + t * 3)
            lunge = int(9 * (1 - t)) * boss.direction
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_xerakkuth._draw_shadow(surface, x + lunge, y + 52)
        _NS_xerakkuth._draw_sand_wisps(
            surface, x + lunge, y + 48, boss.pulse, intense=True
        )

        # Stinger swing trail (behind body render)
        _NS_xerakkuth._draw_stinger_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

        _NS_xerakkuth._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )

        # Hit impact (over body, at target)
        _NS_xerakkuth._draw_attack_hit_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

        # Pincer snap sparks
        _NS_xerakkuth._draw_pincer_snap_fx(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

    def _draw_burrowstrike_pose(surface, boss, x, y, timer, pulse):
        """Burrow underground → tunnel → emerge at target."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xerakkuth._target_position(boss, x, y)
        if progress < 0.25:
            # Sinking underground
            t = progress / 0.25
            lift = -int(t * 30)  # sink down
            alpha_body = _NS_xerakkuth._alpha(255 * (1 - t * 0.9))
            _NS_xerakkuth._draw_shadow(surface, x, y + 52)
            # Body sinking with fade
            body_surf = pygame.Surface((180, 140), pygame.SRCALPHA)
            _NS_xerakkuth._draw_body(
                body_surf, 90, 70, boss.direction, pulse, "idle",
                alpha=alpha_body,
            )
            surface.blit(body_surf, (x - 90, y - lift - 70))
            # Sand splash
            _NS_xerakkuth._draw_burrow_sand_burst(surface, x, y + 40, t)
        elif progress < 0.7:
            # Underground — nothing to draw except tunnel effect at ground
            # (handled in ground FX)
            pass
        else:
            # Emerging at target
            t = (progress - 0.7) / 0.3
            lift = int((1 - t) * -15)  # rise up
            alpha_body = _NS_xerakkuth._alpha(255 * t)
            body_surf = pygame.Surface((180, 140), pygame.SRCALPHA)
            _NS_xerakkuth._draw_body(
                body_surf, 90, 70, boss.direction, pulse, "attack", 0.5,
                alpha=alpha_body,
            )
            surface.blit(body_surf, (tx - 90, ty - lift - 70))
            # Update boss visible position for later frames
            _NS_xerakkuth._draw_burrow_sand_burst(surface, tx, ty + 40,
                                                   1.0 - t)

    # ============================================================
    # BODY (Scorpion — horizontal segmented body, claws, tail)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0,
                   alpha=255):
        """Composite scorpion body with all parts."""
        # Order: back legs -> tail (curled up behind) -> body/thorax ->
        # front legs -> claws -> head
        # If alpha provided, draw to intermediate surface for fade
        if alpha < 255:
            temp = pygame.Surface((200, 160), pygame.SRCALPHA)
            _NS_xerakkuth._draw_body_parts(
                temp, 100, 80, facing, phase, action, progress
            )
            temp.set_alpha(alpha)
            surface.blit(temp, (cx - 100, cy - 80))
        else:
            _NS_xerakkuth._draw_body_parts(
                surface, cx, cy, facing, phase, action, progress
            )

    def _draw_body_parts(surface, cx, cy, facing, phase, action, progress):
        # Back legs (behind body)
        _NS_xerakkuth._draw_scorpion_legs(surface, cx, cy, facing, phase,
                                          action, back=True)
        # Tail curled up-forward (over back)
        _NS_xerakkuth._draw_scorpion_tail(surface, cx, cy, facing, phase,
                                          action, progress)
        # Main thorax/body (segmented)
        _NS_xerakkuth._draw_scorpion_body(surface, cx, cy, facing, phase)
        # Front legs
        _NS_xerakkuth._draw_scorpion_legs(surface, cx, cy, facing, phase,
                                          action, back=False)
        # Claws (large pincers front)
        _NS_xerakkuth._draw_scorpion_claws(surface, cx, cy, facing, phase,
                                            action, progress)
        # Head with eyes
        _NS_xerakkuth._draw_scorpion_head(surface, cx, cy, facing, phase)

    # ── SCORPION BODY (segmented thorax + abdomen) ───────────
    def _draw_scorpion_body(surface, cx, cy, facing, phase):
        breath = math.sin(phase * 0.6) * 1
        # Main body: horizontal oval, wider at chest
        body = [
            (cx - 22, cy - 2),      # rear top
            (cx - 24, cy + 2),      # rear
            (cx - 22, cy + 8),      # rear bottom
            (cx - 12, cy + 12),     # abdomen bottom
            (cx + 4, cy + 12),      # thorax bottom
            (cx + 16, cy + 10),     # front bottom
            (cx + 22, cy + 6),      # head base
            (cx + 24, cy),          # head top
            (cx + 22, cy - 4),      # front top
            (cx + 12, cy - 8),      # thorax top
            (cx - 4, cy - 10),      # abdomen top
            (cx - 18, cy - 6),      # rear top back
        ]
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in body])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_darkest"], body)
        # Chitin mid-tone
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_dark"], [
            (cx - 20, cy - 1), (cx - 22, cy + 2), (cx - 20, cy + 7),
            (cx - 10, cy + 11), (cx + 3, cy + 11), (cx + 14, cy + 9),
            (cx + 20, cy + 5), (cx + 22, cy), (cx + 20, cy - 3),
            (cx + 10, cy - 7), (cx - 3, cy - 9), (cx - 16, cy - 5),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_mid"], [
            (cx - 16, cy), (cx - 17, cy + 3), (cx - 15, cy + 6),
            (cx - 6, cy + 9), (cx + 2, cy + 9), (cx + 10, cy + 7),
            (cx + 16, cy + 3), (cx + 17, cy), (cx + 15, cy - 3),
            (cx + 8, cy - 5), (cx - 2, cy - 6), (cx - 13, cy - 3),
        ])

        # SEGMENTED PLATES on back (abdomen segments)
        segment_boundaries = [-16, -10, -3, 4, 11, 17]
        for i, sx in enumerate(segment_boundaries[:-1]):
            seg_x_start = cx + segment_boundaries[i]
            seg_x_end = cx + segment_boundaries[i + 1]
            # Draw segmented plate with darker line between
            pygame.draw.line(surface,
                             _NS_xerakkuth.PALETTE["chitin_darkest"],
                             (seg_x_end - 1, cy - 6),
                             (seg_x_end, cy + 4), 1)
            # Highlight top edge of segment
            pygame.draw.line(surface,
                             _NS_xerakkuth.PALETTE["chitin_light"],
                             (seg_x_start + 1, cy - 5),
                             (seg_x_end - 2, cy - 5), 1)
        # Chitin shine along top
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_light"], [
            (cx - 14, cy - 3), (cx - 8, cy - 6), (cx + 4, cy - 6),
            (cx + 12, cy - 4), (cx + 15, cy - 2), (cx + 10, cy - 2),
            (cx - 4, cy - 3), (cx - 12, cy - 1),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_shine"], [
            (cx - 6, cy - 5), (cx + 2, cy - 5),
            (cx + 4, cy - 3), (cx - 4, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_edge"],
                         (cx - 2, cy - 5, 4, 1))

        # BRONZE SPIKES on top (row of dorsal spikes)
        for i, spk_x in enumerate((-18, -12, -6, 0, 6, 12, 18)):
            spk_wave = math.sin(phase * 0.5 + i * 0.4) * 0.5
            spike_h = 4 + int((1 - abs(spk_x) / 18) * 3)
            sx = cx + spk_x
            sy_base = cy - 7
            sy_tip = sy_base - spike_h - int(spk_wave)
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["shadow_deep"], [
                (sx + 1, sy_tip + 1), (sx - 2, sy_base + 1),
                (sx + 2, sy_base + 1),
            ])
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["stinger_dark"], [
                (sx, sy_tip), (sx - 2, sy_base), (sx + 2, sy_base),
            ])
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["stinger_mid"], [
                (sx, sy_tip), (sx - 1, sy_base), (sx + 1, sy_base),
            ])
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["stinger_light"],
                             (sx, sy_tip, 1, 1))
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["stinger_hot"],
                             (sx, sy_tip, 1, 1))

        # UNDER-BELLY (softer chitin)
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["under_darkest"], [
            (cx - 14, cy + 8), (cx + 14, cy + 8),
            (cx + 12, cy + 12), (cx - 12, cy + 12),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["under_dark"], [
            (cx - 12, cy + 9), (cx + 12, cy + 9),
            (cx + 10, cy + 11), (cx - 10, cy + 11),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["under_mid"], [
            (cx - 8, cy + 10), (cx + 8, cy + 10),
            (cx + 6, cy + 11), (cx - 6, cy + 11),
        ])
        # Belly segment stripes
        for stripe_x in (-8, -4, 0, 4, 8):
            pygame.draw.line(surface,
                             _NS_xerakkuth.PALETTE["under_darkest"],
                             (cx + stripe_x, cy + 9),
                             (cx + stripe_x, cy + 11), 1)

        # Small chitin texture dots
        for i in range(8):
            dx = -14 + i * 4
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_darkest"],
                             (cx + dx, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_shine"],
                             (cx + dx + 1, cy - 2, 1, 1))

    # ── SCORPION TAIL (curled up over back with stinger) ────
    def _draw_scorpion_tail(surface, cx, cy, facing, phase, action, progress):
        """Segmented tail curling up-forward, ending in stinger."""
        # Tail base at rear of body
        back = -facing
        base_x = cx + back * 20
        base_y = cy - 4

        # Attack: tail slams down forward
        slam_extra = 0
        if action == "attack":
            if progress < 0.35:
                slam_extra = int(progress / 0.35 * -8)  # rear up
            elif progress < 0.6:
                t = (progress - 0.35) / 0.25
                slam_extra = int(-8 + t * 20)  # slam forward
            else:
                t = (progress - 0.6) / 0.4
                slam_extra = int(12 * (1 - t))

        # Compute tail curve (upward arc then forward)
        segments = 8
        pts = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            # First half: curves up
            # Second half: curves forward-down
            if t < 0.5:
                st = t / 0.5
                x_off = int(back * (2 + st * 4))
                y_off = -int(st * 22)  # rises up
            else:
                st = (t - 0.5) / 0.5
                x_off = int(back * (6 - st * 6) + facing * st * 12)
                y_off = -int(22 - st * (10 - slam_extra))
            wave = math.sin(phase * 1.0 + t * math.pi * 1.2) * 1
            pts.append((base_x + x_off, base_y + y_off + int(wave)))

        # Draw segmented tail
        for i in range(len(pts) - 1):
            thickness = max(3, 12 - i)
            # Shadow
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["shadow_deep"],
                                  (pts[i][0] + 2, pts[i][1] + 2),
                                  (pts[i + 1][0] + 2, pts[i + 1][1] + 2),
                                  thickness + 1)
            # Dark chitin
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_darkest"],
                                  pts[i], pts[i + 1], thickness)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_dark"],
                                  pts[i], pts[i + 1], max(1, thickness - 2))
            # Mid
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_mid"],
                                  (pts[i][0], pts[i][1] - 1),
                                  (pts[i + 1][0], pts[i + 1][1] - 1),
                                  max(1, thickness - 4))
            # Highlight top
            if thickness > 4:
                _NS_xerakkuth._aaline(surface,
                                      _NS_xerakkuth.PALETTE["chitin_light"],
                                      (pts[i][0], pts[i][1] - 2),
                                      (pts[i + 1][0], pts[i + 1][1] - 2),
                                      max(1, thickness - 7))
            # Segment ring joint every 2 segments
            if i > 0 and i % 2 == 0:
                pygame.draw.line(surface,
                                 _NS_xerakkuth.PALETTE["chitin_darkest"],
                                 (pts[i][0] - 3, pts[i][1] - thickness // 2),
                                 (pts[i][0] + 3, pts[i][1] + thickness // 2),
                                 1)

        # Small spikes along tail (dorsal)
        for i in range(1, len(pts) - 1, 2):
            spike_size = max(2, 4 - i // 2)
            spike_x = pts[i][0]
            spike_y = pts[i][1] - 3
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["stinger_dark"], [
                (spike_x - 1, spike_y),
                (spike_x, spike_y - spike_size),
                (spike_x + 1, spike_y),
            ])
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["stinger_mid"], [
                (spike_x, spike_y),
                (spike_x, spike_y - spike_size + 1),
                (spike_x + 1, spike_y),
            ])
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["stinger_hot"],
                             (spike_x, spike_y - spike_size, 1, 1))

        # BIG STINGER at tail tip
        if len(pts) >= 2:
            tip = pts[-1]
            prev = pts[-2]
            # Compute stinger direction from last segment
            dx = tip[0] - prev[0]
            dy = tip[1] - prev[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx = dx / length
                ny = dy / length
            else:
                nx = facing
                ny = 1
            stinger_len = 12
            st_tip_x = tip[0] + int(nx * stinger_len)
            st_tip_y = tip[1] + int(ny * stinger_len)
            # Perpendicular for base width
            perp_x = -ny
            perp_y = nx
            base_w = 4
            base_a_x = tip[0] + int(perp_x * base_w)
            base_a_y = tip[1] + int(perp_y * base_w)
            base_b_x = tip[0] - int(perp_x * base_w)
            base_b_y = tip[1] - int(perp_y * base_w)
            # Shadow
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["shadow_deep"], [
                (st_tip_x + 1, st_tip_y + 1),
                (base_a_x + 1, base_a_y + 1),
                (base_b_x + 1, base_b_y + 1),
            ])
            # Main stinger
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["chitin_darkest"], [
                (st_tip_x, st_tip_y), (base_a_x, base_a_y),
                (base_b_x, base_b_y),
            ])
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["chitin_dark"], [
                (st_tip_x, st_tip_y),
                (int((st_tip_x + base_a_x) / 2),
                 int((st_tip_y + base_a_y) / 2)),
                (tip[0], tip[1]),
            ])
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["chitin_mid"], [
                (st_tip_x, st_tip_y),
                (int((st_tip_x + tip[0]) / 2),
                 int((st_tip_y + tip[1]) / 2)),
                (tip[0], tip[1]),
            ])
            # Tip glow (venomous)
            for r in range(4, 0, -1):
                a = _NS_xerakkuth._alpha(150 * (4 - r) / 4)
                _NS_xerakkuth._aacircle(surface,
                                        (*_NS_xerakkuth.PALETTE["venom_mid"], a),
                                        (st_tip_x, st_tip_y), r)
            _NS_xerakkuth._aacircle(surface,
                                    _NS_xerakkuth.PALETTE["stinger_hot"],
                                    (st_tip_x, st_tip_y), 2)
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["venom_hot"],
                             (st_tip_x, st_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["white"],
                             (st_tip_x, st_tip_y, 1, 1))
            # Venom drip during attack
            if action == "attack" and progress > 0.3 and progress < 0.7:
                for i in range(2):
                    dr_t = (progress + i * 0.1) % 1.0
                    dr_x = st_tip_x + int(nx * 3) + i
                    dr_y = st_tip_y + int(ny * 4) + int(dr_t * 6)
                    pygame.draw.rect(surface,
                                     _NS_xerakkuth.PALETTE["venom_mid"],
                                     (dr_x, dr_y, 1, 2))
                    pygame.draw.rect(surface,
                                     _NS_xerakkuth.PALETTE["venom_light"],
                                     (dr_x, dr_y, 1, 1))

    # ── SCORPION LEGS (8 legs, 4 pairs) ──────────────────────
    def _draw_scorpion_legs(surface, cx, cy, facing, phase, action, back=False):
        """4 pairs of legs. back=True draws farther legs, False draws near."""
        leg_wave_speed = 1.5 if action == "walk" else 0.6
        # Leg attachment points along body
        if back:
            attach_xs = (-14, -6, 4, 12)
            side_mult = -1  # legs go away/back-side
            base_alpha = 200
        else:
            attach_xs = (-12, -4, 6, 14)
            side_mult = 1
            base_alpha = 255

        for leg_i, ax in enumerate(attach_xs):
            base_x = cx + ax
            base_y = cy + 6 + (0 if back else 1)
            # Individual leg phase for walking animation
            leg_phase = phase * leg_wave_speed + leg_i * math.pi / 3 \
                        + (0 if back else math.pi)
            step = math.sin(leg_phase) * (5 if action == "walk" else 2)
            lift_amt = max(0, math.sin(leg_phase)) * (4 if action == "walk"
                                                       else 1)

            # Leg goes down-outward with joint (like an "L" bent)
            # Knee point
            knee_x = base_x + int(ax * 0.3 + side_mult * 6)
            knee_y = base_y + 6 - int(lift_amt)
            # Foot
            foot_x = knee_x + int(step) + (2 if ax > 0 else -2)
            foot_y = knee_y + 8 - int(lift_amt * 0.5)

            # Thigh (base -> knee)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["shadow_deep"],
                                  (base_x + 1, base_y + 1),
                                  (knee_x + 1, knee_y + 1), 4)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_darkest"],
                                  (base_x, base_y), (knee_x, knee_y), 3)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_dark"],
                                  (base_x, base_y), (knee_x, knee_y), 2)
            # Highlight
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_mid"],
                                  (base_x, base_y - 1),
                                  (knee_x, knee_y - 1), 1)

            # Shin (knee -> foot)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["shadow_deep"],
                                  (knee_x + 1, knee_y + 1),
                                  (foot_x + 1, foot_y + 1), 3)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_darkest"],
                                  (knee_x, knee_y), (foot_x, foot_y), 2)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_dark"],
                                  (knee_x, knee_y), (foot_x, foot_y), 1)

            # Knee joint (small circle)
            _NS_xerakkuth._aacircle(surface,
                                    _NS_xerakkuth.PALETTE["chitin_mid"],
                                    (knee_x, knee_y), 2)
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_shine"],
                             (knee_x, knee_y, 1, 1))

            # Sharp foot tip
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["shadow_deep"], [
                (foot_x + 1, foot_y + 1),
                (foot_x + 1 + side_mult, foot_y + 4),
                (foot_x - 1 + side_mult, foot_y + 3),
            ])
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["chitin_darkest"], [
                (foot_x, foot_y),
                (foot_x + side_mult, foot_y + 3),
                (foot_x - 1, foot_y + 2),
            ])

    # ── SCORPION CLAWS (huge pincers front) ──────────────────
    def _draw_scorpion_claws(surface, cx, cy, facing, phase, action, progress):
        """Two big pincer arms extending forward."""
        # Attack: claws open/close
        pincer_open = 0
        arm_extend = 0
        if action == "attack":
            if progress < 0.35:
                t = progress / 0.35
                pincer_open = int(t * 5)  # open wide
                arm_extend = int(t * -3)
            elif progress < 0.6:
                t = (progress - 0.35) / 0.25
                pincer_open = int(5 - t * 6)  # snap closed
                arm_extend = int(-3 + t * 8)
            else:
                t = (progress - 0.6) / 0.4
                pincer_open = int(-1 + t * 1)
                arm_extend = int(5 * (1 - t))
        else:
            pincer_open = 1 + int(math.sin(phase * 0.6) * 1)

        # Draw two claws (upper and lower)
        for side in (-1, 1):
            _NS_xerakkuth._draw_single_claw(
                surface, cx, cy, facing, phase, side, pincer_open,
                arm_extend, action,
            )

    def _draw_single_claw(surface, cx, cy, facing, phase, side, pincer_open,
                           arm_extend, action):
        """Single scorpion claw (arm + pincer)."""
        # Arm base at front of body
        base_x = cx + facing * 20
        base_y = cy - 2 + side * 4
        # Elbow (joint)
        elbow_ang = 0.2 * side
        elbow_dist = 10
        elbow_x = base_x + int(math.cos(elbow_ang) * elbow_dist) * facing
        elbow_y = base_y + int(math.sin(elbow_ang) * elbow_dist)
        # Wrist (where pincer attaches)
        wrist_ang = -0.15 * side + 0.1 * facing
        wrist_dist = 12 + arm_extend
        wrist_x = elbow_x + int(math.cos(wrist_ang) * wrist_dist) * facing
        wrist_y = elbow_y + int(math.sin(wrist_ang) * wrist_dist) + side * 2

        # Upper arm (base -> elbow)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["shadow_deep"],
                              (base_x + 1, base_y + 2),
                              (elbow_x + 1, elbow_y + 2), 8)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_darkest"],
                              (base_x, base_y), (elbow_x, elbow_y), 7)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_dark"],
                              (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_mid"],
                              (base_x, base_y - 1), (elbow_x, elbow_y - 1), 3)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_light"],
                              (base_x, base_y - 2), (elbow_x, elbow_y - 2), 1)

        # Elbow joint (big bulge)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["shadow_deep"],
                                (elbow_x + 1, elbow_y + 1), 5)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_darkest"],
                                (elbow_x, elbow_y), 5)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_dark"],
                                (elbow_x, elbow_y), 4)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_mid"],
                                (elbow_x - 1, elbow_y - 1), 3)
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_light"],
                         (elbow_x - 1, elbow_y - 1, 2, 1))
        # Small spike on elbow
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["stinger_dark"], [
            (elbow_x, elbow_y - 5),
            (elbow_x + 1, elbow_y - 3),
            (elbow_x - 1, elbow_y - 3),
        ])
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["stinger_hot"],
                         (elbow_x, elbow_y - 5, 1, 1))

        # Forearm (elbow -> wrist)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 2),
                              (wrist_x + 1, wrist_y + 2), 7)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_darkest"],
                              (elbow_x, elbow_y), (wrist_x, wrist_y), 6)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_dark"],
                              (elbow_x, elbow_y), (wrist_x, wrist_y), 4)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_mid"],
                              (elbow_x, elbow_y - 1), (wrist_x, wrist_y - 1), 2)

        # PINCER (2 curved claws that open/close)
        _NS_xerakkuth._draw_pincer(surface, wrist_x, wrist_y, facing, side,
                                    pincer_open, phase)

    def _draw_pincer(surface, wx, wy, facing, side, open_amount, phase):
        """Big pincer with 2 curved parts."""
        # Base bulb of pincer (where it attaches to arm)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["shadow_deep"],
                                (wx + 1, wy + 1), 6)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_darkest"],
                                (wx, wy), 6)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_dark"],
                                (wx, wy), 5)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_mid"],
                                (wx - 1, wy - 1), 4)
        _NS_xerakkuth._aacircle(surface,
                                _NS_xerakkuth.PALETTE["chitin_light"],
                                (wx - 2, wy - 2), 2)
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_shine"],
                         (wx - 2, wy - 2, 2, 1))

        # Upper pincer half (curves out and back)
        up_open = open_amount * 0.5
        # Upper claw tip
        u_mid_x = wx + facing * 8
        u_mid_y = wy - 5 - int(up_open)
        u_tip_x = wx + facing * 14
        u_tip_y = wy - 2 - int(up_open * 0.5)
        # Upper claw poly
        up_pts = [
            (wx, wy - 3),
            (u_mid_x, u_mid_y - 2),
            (u_tip_x, u_tip_y),
            (u_mid_x, u_mid_y + 2),
            (wx + facing * 3, wy - 1),
        ]
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in up_pts])
        _NS_xerakkuth._poly(surface,
                            _NS_xerakkuth.PALETTE["chitin_darkest"], up_pts)
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_dark"], [
            (wx + facing * 1, wy - 3),
            (u_mid_x, u_mid_y - 1),
            (u_tip_x, u_tip_y),
            (u_mid_x, u_mid_y + 1),
            (wx + facing * 3, wy - 1),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_mid"], [
            (wx + facing * 2, wy - 2),
            (u_mid_x, u_mid_y),
            (u_tip_x - facing * 1, u_tip_y),
        ])
        # Upper claw edge (bright)
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_light"],
                              (wx + facing * 2, wy - 2),
                              (u_tip_x, u_tip_y), 1)
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_edge"],
                         (u_tip_x, u_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["white"],
                         (u_tip_x, u_tip_y, 1, 1))

        # Lower pincer half (mirror, curves down)
        low_open = open_amount * 0.5
        l_mid_x = wx + facing * 8
        l_mid_y = wy + 5 + int(low_open)
        l_tip_x = wx + facing * 14
        l_tip_y = wy + 2 + int(low_open * 0.5)
        low_pts = [
            (wx, wy + 3),
            (l_mid_x, l_mid_y + 2),
            (l_tip_x, l_tip_y),
            (l_mid_x, l_mid_y - 2),
            (wx + facing * 3, wy + 1),
        ]
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in low_pts])
        _NS_xerakkuth._poly(surface,
                            _NS_xerakkuth.PALETTE["chitin_darkest"], low_pts)
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_dark"], [
            (wx + facing * 1, wy + 3),
            (l_mid_x, l_mid_y + 1),
            (l_tip_x, l_tip_y),
            (l_mid_x, l_mid_y - 1),
            (wx + facing * 3, wy + 1),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_mid"], [
            (wx + facing * 2, wy + 2),
            (l_mid_x, l_mid_y),
            (l_tip_x - facing * 1, l_tip_y),
        ])
        _NS_xerakkuth._aaline(surface,
                              _NS_xerakkuth.PALETTE["chitin_light"],
                              (wx + facing * 2, wy + 2),
                              (l_tip_x, l_tip_y), 1)
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_edge"],
                         (l_tip_x, l_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["white"],
                         (l_tip_x, l_tip_y, 1, 1))

        # Serrated teeth inside pincer (small triangles)
        for i, tx_off in enumerate((4, 7, 10)):
            teeth_x = wx + facing * tx_off
            # Upper teeth pointing down
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["chitin_darkest"], [
                (teeth_x - 1, u_mid_y + 1),
                (teeth_x, u_mid_y + 3 - int(up_open * 0.3)),
                (teeth_x + 1, u_mid_y + 1),
            ])
            # Lower teeth pointing up
            _NS_xerakkuth._poly(surface,
                                _NS_xerakkuth.PALETTE["chitin_darkest"], [
                (teeth_x - 1, l_mid_y - 1),
                (teeth_x, l_mid_y - 3 + int(low_open * 0.3)),
                (teeth_x + 1, l_mid_y - 1),
            ])

    # ── SCORPION HEAD ────────────────────────────────────────
    def _draw_scorpion_head(surface, cx, cy, facing, phase):
        """Front head (small, embedded in front of thorax)."""
        hx = cx + facing * 22
        hy = cy
        # Head shape (small triangular)
        head_pts = [
            (hx - facing * 2, hy - 4),
            (hx + facing * 5, hy - 3),
            (hx + facing * 7, hy),
            (hx + facing * 5, hy + 3),
            (hx - facing * 2, hy + 4),
        ]
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_xerakkuth._poly(surface,
                            _NS_xerakkuth.PALETTE["chitin_darkest"], head_pts)
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_dark"], [
            (hx - facing * 1, hy - 3),
            (hx + facing * 4, hy - 2),
            (hx + facing * 6, hy),
            (hx + facing * 4, hy + 2),
            (hx - facing * 1, hy + 3),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["chitin_mid"], [
            (hx, hy - 2), (hx + facing * 3, hy - 1),
            (hx + facing * 4, hy), (hx + facing * 3, hy + 1),
            (hx, hy + 2),
        ])
        # Head shine
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_light"],
                         (hx + facing * 1, hy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_shine"],
                         (hx + facing * 2, hy - 1, 1, 1))
        # Mandibles (small pincers at front)
        for m_side in (-1, 1):
            m_x = hx + facing * 6
            m_y = hy + m_side * 2
            m_tip_x = m_x + facing * 2
            m_tip_y = m_y + m_side * 1
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_darkest"],
                                  (m_x, m_y), (m_tip_x, m_tip_y), 2)
            _NS_xerakkuth._aaline(surface,
                                  _NS_xerakkuth.PALETTE["chitin_mid"],
                                  (m_x, m_y), (m_tip_x, m_tip_y), 1)
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["chitin_light"],
                             (m_tip_x, m_tip_y, 1, 1))
        # EYES (2 emerald eyes on top of head)
        for e_side in (-1, 1):
            _NS_xerakkuth._draw_scorpion_eye(
                surface, hx + facing * 1, hy + e_side * 2, facing, phase,
            )

    # ============================================================
    # BASIC ATTACK HIT FX (stinger swing + pincer snap + impact)
    # ============================================================
    def _get_stinger_tip_pos(cx, cy, facing, progress):
        """Calculate stinger tip position at given attack progress."""
        # Tail base
        back = -facing
        base_x = cx + back * 20
        base_y = cy - 4

        # Match tail slam animation
        if progress < 0.35:
            slam_extra = int(progress / 0.35 * -8)  # rear up
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            slam_extra = int(-8 + t * 20)  # slam forward
        else:
            t = (progress - 0.6) / 0.4
            slam_extra = int(12 * (1 - t))

        # Sample end segment position (approximation)
        segments = 8
        t = 1.0  # last segment
        # First half: curves up, Second half: forward-down
        if t < 0.5:
            st = t / 0.5
            x_off = int(back * (2 + st * 4))
            y_off = -int(st * 22)
        else:
            st = (t - 0.5) / 0.5
            x_off = int(back * (6 - st * 6) + facing * st * 12)
            y_off = -int(22 - st * (10 - slam_extra))
        seg_end_x = base_x + x_off
        seg_end_y = base_y + y_off

        # Stinger extends beyond segment end
        # Direction based on previous seg (approx: down-forward)
        stinger_dx = facing * 0.7
        stinger_dy = 0.7
        stinger_len = 12
        tip_x = seg_end_x + int(stinger_dx * stinger_len)
        tip_y = seg_end_y + int(stinger_dy * stinger_len)
        return tip_x, tip_y

    def _draw_stinger_trail(surface, boss, cx, cy, facing, progress):
        """Arc trail of stinger slamming down."""
        # Show trail only during slam (0.35 - 0.7)
        if progress < 0.35 or progress > 0.7:
            return
        if progress < 0.4:
            intensity = (progress - 0.35) / 0.05
        elif progress < 0.6:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.6) / 0.1)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return

        # Sample past positions of stinger tip
        num = 14
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.22
            if sp < 0.3:
                continue
            tx, ty = _NS_xerakkuth._get_stinger_tip_pos(cx, cy, facing, sp)
            trail.append((tx, ty, i))
        if len(trail) < 2:
            return
        trail.reverse()

        ts = pygame.Surface((280, 280), pygame.SRCALPHA)
        ox = cx - 140
        oy = cy - 140

        # Layered trail
        layers = [
            (_NS_xerakkuth.PALETTE["venom_darkest"], 14, 100),
            (_NS_xerakkuth.PALETTE["venom_dark"], 10, 150),
            (_NS_xerakkuth.PALETTE["venom_mid"], 6, 200),
            (_NS_xerakkuth.PALETTE["venom_light"], 3, 240),
            (_NS_xerakkuth.PALETTE["venom_hot"], 1, 255),
        ]
        for color, max_w, max_a in layers:
            for i in range(len(trail) - 1):
                p1, p2 = trail[i], trail[i + 1]
                fade = 1.0 - (p1[2] / num)
                a = _NS_xerakkuth._alpha(max_a * fade * intensity)
                w = max(1, int(max_w * fade))
                if a > 0:
                    pygame.draw.line(
                        ts, (*color, a),
                        (p1[0] - ox, p1[1] - oy),
                        (p2[0] - ox, p2[1] - oy), w,
                    )

        # Venom droplets scattered along trail
        for i, (tx, ty, idx) in enumerate(trail):
            fade = 1.0 - (idx / num)
            a = _NS_xerakkuth._alpha(230 * fade * intensity)
            if a <= 0 or i % 2 == 0:
                continue
            for spark_i in range(2):
                offset = (spark_i - 0.5) * 6
                spx = tx - ox + int(offset)
                spy = ty - oy + int(offset * 0.5)
                pygame.draw.rect(ts,
                                 (*_NS_xerakkuth.PALETTE["venom_hot"], a),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(ts,
                                 (*_NS_xerakkuth.PALETTE["white"], a),
                                 (spx, spy, 1, 1))
        surface.blit(ts, (ox, oy))

        # Leading edge glow (at current tip)
        if trail:
            lead = trail[0]
            for r in range(10, 2, -2):
                a = _NS_xerakkuth._alpha(160 * (10 - r) / 10 * intensity)
                _NS_xerakkuth._aacircle(
                    surface,
                    (*_NS_xerakkuth.PALETTE["venom_mid"], a),
                    (lead[0], lead[1]), r,
                )
            _NS_xerakkuth._aacircle(
                surface, _NS_xerakkuth.PALETTE["venom_hot"],
                (lead[0], lead[1]), 3,
            )
            _NS_xerakkuth._aacircle(
                surface, _NS_xerakkuth.PALETTE["white"],
                (lead[0], lead[1]), 1,
            )

    def _draw_attack_hit_impact(surface, boss, cx, cy, facing, progress):
        """Impact burst when stinger connects with target."""
        # Impact happens at peak of swing (progress 0.55 - 0.72)
        if progress < 0.55 or progress > 0.75:
            return
        t = (progress - 0.55) / 0.2
        inten = math.sin(t * math.pi)

        # Impact position (front of boss where stinger lands)
        tip_x, tip_y = _NS_xerakkuth._get_stinger_tip_pos(
            cx, cy, facing, progress
        )
        # Impact slightly forward of tip
        ix = tip_x + facing * 3
        iy = tip_y

        # === MAIN BURST (venom-yellow explosion) ===
        r = int(6 + t * 16)
        a = _NS_xerakkuth._alpha(255 * inten)

        # Outer dark burst
        for rr in range(r + 5, 0, -2):
            ra = _NS_xerakkuth._alpha(a * (r + 5 - rr) / (r + 5))
            _NS_xerakkuth._aacircle(
                surface,
                (*_NS_xerakkuth.PALETTE["venom_darkest"], ra),
                (ix, iy), rr,
            )
        for rr in range(int(r * 0.8), 0, -2):
            ra = _NS_xerakkuth._alpha(a * (r * 0.8 - rr) / (r * 0.8))
            _NS_xerakkuth._aacircle(
                surface,
                (*_NS_xerakkuth.PALETTE["venom_dark"], ra),
                (ix, iy), rr,
            )
        _NS_xerakkuth._aacircle(
            surface, (*_NS_xerakkuth.PALETTE["venom_mid"], a),
            (ix, iy), max(2, r - 4),
        )
        _NS_xerakkuth._aacircle(
            surface, (*_NS_xerakkuth.PALETTE["venom_light"], a),
            (ix, iy), max(1, r - 7),
        )
        _NS_xerakkuth._aacircle(
            surface, (*_NS_xerakkuth.PALETTE["venom_hot"], a),
            (ix, iy), max(1, r - 10),
        )
        _NS_xerakkuth._aacircle(
            surface, (*_NS_xerakkuth.PALETTE["sand_shine"], a),
            (ix, iy), max(1, r - 13),
        )
        pygame.draw.rect(surface, (*_NS_xerakkuth.PALETTE["white"], a),
                         (ix, iy, 1, 1))

        # === RADIAL BURST LINES (star pattern) ===
        for i in range(8):
            ang = i * math.pi / 4 + progress * 3
            spike_len = int(r * 1.4)
            ex = ix + int(math.cos(ang) * spike_len)
            ey = iy + int(math.sin(ang) * spike_len)
            # Layered star spike
            for w, color, wa in [
                (3, _NS_xerakkuth.PALETTE["venom_dark"], 200),
                (2, _NS_xerakkuth.PALETTE["venom_mid"], 240),
                (1, _NS_xerakkuth.PALETTE["venom_hot"], 255),
            ]:
                la = _NS_xerakkuth._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la),
                                 (ix, iy), (ex, ey), w)
            # Tip particle
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["venom_hot"], a),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["white"], a),
                             (ex, ey, 1, 1))

        # === SHOCKWAVE RING (expanding) ===
        wave_r = int(r * (1.3 + t * 0.5))
        wave_a = _NS_xerakkuth._alpha(200 * (1 - t))
        _NS_xerakkuth._aacircle(surface,
                                (*_NS_xerakkuth.PALETTE["venom_light"], wave_a),
                                (ix, iy), wave_r, 2)
        _NS_xerakkuth._aacircle(surface,
                                (*_NS_xerakkuth.PALETTE["venom_hot"], wave_a),
                                (ix, iy), max(1, wave_r - 1), 1)

        # === VENOM DROPLETS FLYING OUTWARD ===
        for i in range(12):
            drop_ang = i * math.pi / 6 + t * 4
            drop_dist = int(r * (0.8 + (i % 3) * 0.2 + t * 0.5))
            dx = ix + int(math.cos(drop_ang) * drop_dist)
            dy = iy + int(math.sin(drop_ang) * drop_dist)
            drop_a = _NS_xerakkuth._alpha(240 * (1 - t * 0.6))
            # Drop with trail
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["venom_dark"], drop_a),
                                    (dx, dy), 3)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["venom_mid"], drop_a),
                                    (dx, dy), 2)
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["venom_light"], drop_a),
                             (dx, dy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["venom_hot"], drop_a),
                             (dx, dy, 1, 1))
            # Trail behind droplet
            trail_dx = ix + int(math.cos(drop_ang) * drop_dist * 0.7)
            trail_dy = iy + int(math.sin(drop_ang) * drop_dist * 0.7)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["venom_mid"],
                              drop_a // 2),
                             (trail_dx, trail_dy), (dx, dy), 1)

        # === SAND KICKUP (dusty impact clouds) ===
        for i in range(6):
            dust_ang = i * math.pi / 3 + progress
            dust_dist = int(r * 1.1)
            dux = ix + int(math.cos(dust_ang) * dust_dist)
            duy = iy + int(math.sin(dust_ang) * dust_dist * 0.7) + 2
            dust_a = _NS_xerakkuth._alpha(180 * inten)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_dark"], dust_a),
                                    (dux, duy), 4)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_mid"], dust_a),
                                    (dux, duy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_hot"], dust_a),
                             (dux, duy - 1, 1, 1))

        # === HIT CROSS X-MARK (for the "critical" feel) ===
        if inten > 0.5:
            xmark_len = int(r * 0.8)
            xa = _NS_xerakkuth._alpha(255 * inten)
            # Diagonal 1
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["white"], xa),
                             (ix - xmark_len, iy - xmark_len),
                             (ix + xmark_len, iy + xmark_len), 2)
            # Diagonal 2
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["venom_hot"], xa),
                             (ix + xmark_len, iy - xmark_len),
                             (ix - xmark_len, iy + xmark_len), 2)

    def _draw_pincer_snap_fx(surface, boss, cx, cy, facing, progress):
        """Small snap-spark effect when pincers close (during attack)."""
        # Pincers snap closed around progress 0.5 - 0.65
        if progress < 0.5 or progress > 0.7:
            return
        t = (progress - 0.5) / 0.2
        inten = math.sin(t * math.pi)
        if inten <= 0:
            return

        # Two pincer positions (upper + lower claw tips)
        for side in (-1, 1):
            # Approximate pincer tip position based on side
            px = cx + facing * 34
            py = cy - 2 + side * 4

            # Small snap spark
            sr = int(3 + t * 5)
            sa = _NS_xerakkuth._alpha(230 * inten)

            for r in range(sr + 2, 0, -1):
                ra = _NS_xerakkuth._alpha(sa * (sr + 2 - r) / (sr + 2))
                _NS_xerakkuth._aacircle(surface,
                                        (*_NS_xerakkuth.PALETTE["sand_hot"], ra),
                                        (px, py), r)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_shine"], sa),
                                    (px, py), max(1, sr - 2))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["white"], sa),
                             (px, py, 1, 1))

            # Radial mini-sparks
            for i in range(4):
                spark_ang = i * math.pi / 2 + progress * 5
                spx = px + int(math.cos(spark_ang) * sr)
                spy = py + int(math.sin(spark_ang) * sr)
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_hot"], sa),
                                 (spx, spy, 1, 1))

    def _draw_scorpion_eye(surface, ex, ey, facing, phase):
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Socket
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["eye_socket"],
                         (ex - 1, ey - 1, 3, 2))
        # Glow halo
        for r in range(4, 0, -1):
            a = _NS_xerakkuth._alpha(90 * (4 - r) / 4 * pulse)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["eye_mid"], a),
                                    (ex, ey), r)
        # Iris
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["eye_dark"],
                         (ex - 1, ey, 3, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["eye_mid"],
                         (ex, ey, 2, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["eye_light"],
                         (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["eye_glow"],
                         (ex + 1, ey, 1, 1))

    # ============================================================
    # AMBIENT / FLOATING FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((180, 32), pygame.SRCALPHA)
        for r in range(16, 0, -1):
            a = max(0, (16 - r) * 14)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 16 - r, 160 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (10, 5, 2, 170), (8, 10, 164, 12))
        pygame.draw.ellipse(sh, (60, 40, 15, 100), (14, 12, 152, 8))
        surface.blit(sh, (x - 90, y - 16))

    def _draw_sand_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for r in range(95, 5, -5):
            a = _NS_xerakkuth._alpha((95 - r) * 1.0 * pulse)
            if a > 0:
                _NS_xerakkuth._aacircle(aura,
                                        (*_NS_xerakkuth.PALETTE["sand_darkest"], a),
                                        (120, 100), r)
        for r in range(55, 5, -3):
            a = _NS_xerakkuth._alpha((55 - r) * 1.3 * pulse)
            if a > 0:
                _NS_xerakkuth._aacircle(aura,
                                        (*_NS_xerakkuth.PALETTE["sand_dark"], a),
                                        (120, 100), r)
        surface.blit(aura, (x - 120, y - 100))
        # Floating sand particles
        for i in range(12):
            ang = phase * 0.4 + i * math.pi / 6
            rd = 50 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.45)
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["sand_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["sand_light"],
                             (sx, sy, 1, 1))

    def _draw_sand_wisps(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((160, 40), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(26, 3, -2):
            a = _NS_xerakkuth._alpha((26 - r) * 3 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xerakkuth.PALETTE["sand_dark"], a),
                    (80 - r * 2, 20 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(16, 3, -2):
            a = _NS_xerakkuth._alpha((16 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xerakkuth.PALETTE["sand_mid"], a),
                    (80 - r, 20 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising sand grains
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 22 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 20)
            a = _NS_xerakkuth._alpha(220 * (1 - t) * strength)
            if a > 0:
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_mid"], a),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_light"], a),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_xerakkuth._alpha(160 - i * 28)
                if a > 0:
                    _NS_xerakkuth._aacircle(
                        surface, (*_NS_xerakkuth.PALETTE["sand_dark"], a),
                        (sx, sy), max(2, 6 - i),
                    )
                    _NS_xerakkuth._aacircle(
                        surface, (*_NS_xerakkuth.PALETTE["sand_mid"], a),
                        (sx, sy), max(1, 4 - i),
                    )

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xerakkuth.PALETTE["sand_darkest"], 180),
                            (5, 16, 180, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_xerakkuth.PALETTE["chitin_darkest"], 210),
                            (14, 18, 162, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_xerakkuth.PALETTE["sand_dark"], 190),
                            (25, 20, 140, 18), 1)
        # Runes / cracks radiating
        for i in range(10):
            ang = phase * 0.3 + i * math.pi / 5
            x1 = 95 + int(math.cos(ang) * 52)
            y1 = 29 + int(math.sin(ang) * 8)
            x2 = 95 + int(math.cos(ang) * 78)
            y2 = 29 + int(math.sin(ang) * 12)
            pygame.draw.line(ring, (*_NS_xerakkuth.PALETTE["crack_mid"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_xerakkuth.PALETTE["crack_light"],
                       _NS_xerakkuth._alpha(150 * pulse)),
                (10, 10, 170, 34), 1,
            )
        surface.blit(ring, (x - 95, y - 25))

    # ============================================================
    # SKILL Q — BURROWSTRIKE (burrow + tunnel + emerge)
    # ============================================================
    def _draw_burrowstrike_ground(surface, boss, x, y, timer, phase):
        """Tunnel dust trail on ground from origin to target."""
        tx, ty = _NS_xerakkuth._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25 or progress > 0.75:
            return
        # Tunnel progress across ground
        tunnel_t = (progress - 0.25) / 0.5
        # Draw sand splash following underground path
        num_splash = 12
        for i in range(num_splash):
            splash_t = tunnel_t - i * 0.05
            if splash_t <= 0 or splash_t > 1:
                continue
            sx = int(x + (tx - x) * splash_t)
            sy = y + 45
            a = _NS_xerakkuth._alpha(220 - i * 15)
            r = max(2, 8 - i // 2)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_dark"], a),
                                    (sx, sy), r)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_mid"], a),
                                    (sx, sy - 1), max(1, r - 2))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_light"], a),
                             (sx, sy - 2, 2, 2))
            # Sand kicks up
            for sk_i in range(2):
                kick_y = sy - int(splash_t * 12 * (1 - i * 0.08))
                kick_x = sx + (sk_i - 0.5) * 4
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                                 (int(kick_x), kick_y, 1, 1))
        # Warning crosshair at target during burrow phase
        if progress < 0.65:
            warn_t = min(1.0, (progress - 0.25) / 0.3)
            wa = _NS_xerakkuth._alpha(200 * warn_t)
            wr = int(15 + math.sin(phase * 3) * 3)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["crack_mid"], wa),
                                    (tx, ty + 40), wr, 2)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["crack_light"], wa),
                             (tx - wr, ty + 40), (tx + wr, ty + 40), 1)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["crack_light"], wa),
                             (tx, ty + 40 - 7), (tx, ty + 40 + 7), 1)

    def _draw_burrow_sand_burst(surface, x, y, intensity):
        """Big sand burst at burrow/emerge point."""
        if intensity <= 0:
            return
        r = int(20 + intensity * 15)
        for rr in range(r + 5, 0, -3):
            a = _NS_xerakkuth._alpha(220 * (r + 5 - rr) / (r + 5)
                                      * intensity)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_darkest"], a),
                                    (x, y), rr)
        _NS_xerakkuth._aacircle(surface,
                                (*_NS_xerakkuth.PALETTE["sand_dark"],
                                 _NS_xerakkuth._alpha(220 * intensity)),
                                (x, y), max(2, r - 4))
        _NS_xerakkuth._aacircle(surface,
                                (*_NS_xerakkuth.PALETTE["sand_mid"],
                                 _NS_xerakkuth._alpha(220 * intensity)),
                                (x, y), max(1, r - 8))
        # Sand chunks flying outward
        for i in range(10):
            ang = i * math.pi / 5
            dist = int(r * (0.9 + (i % 3) * 0.15))
            fx = x + int(math.cos(ang) * dist)
            fy = y + int(math.sin(ang) * dist * 0.6)
            a = _NS_xerakkuth._alpha(240 * intensity)
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_mid"], a),
                             (fx, fy, 3, 3))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_light"], a),
                             (fx, fy, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                             (fx, fy, 1, 1))

    def _draw_burrowstrike_emerge(surface, boss, x, y, timer, phase):
        """Additional emerge effects."""
        tx, ty = _NS_xerakkuth._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.7:
            return
        t = (progress - 0.7) / 0.3
        inten = math.sin(t * math.pi)
        # Impact stinger slash mark at target
        a = _NS_xerakkuth._alpha(240 * inten)
        # Vertical slash of energy
        for w, color, wa in [
            (8, _NS_xerakkuth.PALETTE["crack_dark"], 100),
            (5, _NS_xerakkuth.PALETTE["sand_mid"], 150),
            (3, _NS_xerakkuth.PALETTE["sand_hot"], 220),
            (1, _NS_xerakkuth.PALETTE["white"], 255),
        ]:
            la = _NS_xerakkuth._alpha(wa * inten)
            pygame.draw.line(surface, (*color, la),
                             (tx, ty - 25), (tx, ty + 15), w)
        # Central burst
        r = int(8 + t * 15)
        for rr in range(r + 3, 0, -2):
            ra = _NS_xerakkuth._alpha(a * (r + 3 - rr) / (r + 3))
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["sand_mid"], ra),
                                    (tx, ty), rr)
        _NS_xerakkuth._aacircle(surface,
                                (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                                (tx, ty), max(2, r - 5))

    # ============================================================
    # SKILL W — SAND STORM (swirling storm around boss)
    # ============================================================
    def _draw_sandstorm_ground(surface, boss, x, y, timer, phase):
        """Sand storm base at boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2.5))
        if r < 5:
            return
        # Storm base
        for layer_r in range(r, 5, -6):
            a = _NS_xerakkuth._alpha((r - layer_r + 5) * 3)
            pygame.draw.ellipse(
                surface, (*_NS_xerakkuth.PALETTE["sand_darkest"], a),
                (x - layer_r, y + 40 - layer_r // 3,
                 layer_r * 2, layer_r * 2 // 3),
            )
        pygame.draw.ellipse(
            surface, (*_NS_xerakkuth.PALETTE["sand_dark"], 160),
            (x - r + 6, y + 40 - r // 3 + 3,
             r * 2 - 12, r * 2 // 3 - 6),
        )

    def _draw_sandstorm_foreground(surface, boss, x, y, timer, phase):
        """Swirling storm particles around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2.5))
        if r < 10:
            return
        # Swirl of sand particles orbiting boss
        num_particles = 40
        for i in range(num_particles):
            # Particle orbit
            orbit_ang = phase * 2 + i * (math.pi * 2 / num_particles) \
                        + (i % 3) * 0.3
            orbit_r = r * (0.4 + (i % 5) * 0.15)
            orbit_h = int(math.sin(orbit_ang * 2 + i) * 15) - 5
            px = x + int(math.cos(orbit_ang) * orbit_r)
            py = y + orbit_h
            a = _NS_xerakkuth._alpha(180 + math.sin(phase * 3 + i) * 60)
            size = 2 + (i % 3)
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_mid"], a),
                             (px, py, size, size))
            pygame.draw.rect(surface,
                             (*_NS_xerakkuth.PALETTE["sand_light"], a),
                             (px, py, max(1, size - 1), max(1, size - 1)))
            if i % 4 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                                 (px, py, 1, 1))
        # Swirling ring wisps
        for ring_i in range(3):
            ring_r = r * (0.5 + ring_i * 0.2)
            ring_pts = []
            for i in range(24):
                ang = phase * 1.5 + i * math.pi / 12 + ring_i * 0.5
                rx = x + int(math.cos(ang) * ring_r)
                ry = y + int(math.sin(ang) * ring_r * 0.4) \
                      + int(math.sin(ang * 2) * 4)
                ring_pts.append((rx, ry))
            for i in range(len(ring_pts) - 1):
                a = _NS_xerakkuth._alpha(140 + math.sin(phase * 2 + i) * 40)
                pygame.draw.line(surface,
                                 (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                                 ring_pts[i], ring_pts[i + 1], 1)
        # Occasional bright sand streaks
        for i in range(6):
            streak_ang = phase * 3 + i * math.pi / 3
            streak_r1 = r * 0.6
            streak_r2 = r * 1.0
            s1x = x + int(math.cos(streak_ang) * streak_r1)
            s1y = y + int(math.sin(streak_ang) * streak_r1 * 0.5)
            s2x = x + int(math.cos(streak_ang) * streak_r2)
            s2y = y + int(math.sin(streak_ang) * streak_r2 * 0.5)
            a = _NS_xerakkuth._alpha(200)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["sand_light"], a),
                             (s1x, s1y), (s2x, s2y), 2)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["sand_hot"], a),
                             (s1x, s1y), (s2x, s2y), 1)

    # ============================================================
    # SKILL E — CAUSTIC FINALE (venom spit cone)
    # ============================================================
    def _draw_caustic_finale(surface, boss, x, y, timer, phase):
        """Toxic venom cone spit forward."""
        facing = boss.direction
        duration = 60
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_xerakkuth._target_position(boss, x, y)
        if progress < 0.15:
            return
        t = (progress - 0.15) / 0.85
        t = max(0.0, min(1.0, t))
        # Spit origin (mouth/stinger)
        origin_x = x + facing * 22
        origin_y = y - 4
        # Cone extends toward target
        cone_len = min(t * 1.5, 1.0) * math.hypot(tx - origin_x, ty - origin_y)
        cone_ang = math.atan2(ty - origin_y, tx - origin_x)
        # Draw cone as swirling venom
        num_venom = 45
        for i in range(num_venom):
            v_seed = (i * 0.211) % 1.0
            v_start_t = v_seed * 0.4
            if t < v_start_t:
                continue
            v_t = max(0.0, min(1.0, (t - v_start_t) / max(0.01, 0.7)))
            # Distance along cone
            v_dist = v_t * cone_len * (0.7 + v_seed * 0.4)
            # Spread perpendicular
            spread_off = (v_seed - 0.5) * v_dist * 0.35
            perp = cone_ang + math.pi / 2
            vx = origin_x + int(math.cos(cone_ang) * v_dist) \
                 + int(math.cos(perp) * spread_off)
            vy = origin_y + int(math.sin(cone_ang) * v_dist) \
                 + int(math.sin(perp) * spread_off)
            a = _NS_xerakkuth._alpha(220 * (1 - v_t * 0.4))
            size = 3 + (i % 3)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["venom_darkest"], a),
                                    (vx, vy), size + 1)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["venom_dark"], a),
                                    (vx, vy), size)
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["venom_mid"], a),
                                    (vx, vy), max(1, size - 1))
            _NS_xerakkuth._aacircle(surface,
                                    (*_NS_xerakkuth.PALETTE["venom_light"], a),
                                    (vx, vy), max(1, size - 2))
            if v_t < 0.5:
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["venom_hot"], a),
                                 (vx, vy, 1, 1))
        # Central spit stream
        stream_pts = []
        for i in range(10):
            s_t = (i / 10) * min(t * 1.5, 1.0)
            wave = math.sin(s_t * math.pi * 3 + phase) * 4
            sx = origin_x + int(math.cos(cone_ang) * s_t * cone_len) \
                 + int(math.cos(perp := cone_ang + math.pi / 2) * wave)
            sy = origin_y + int(math.sin(cone_ang) * s_t * cone_len) \
                 + int(math.sin(perp) * wave)
            stream_pts.append((sx, sy))
        for i in range(len(stream_pts) - 1):
            a = _NS_xerakkuth._alpha(240 - i * 15)
            w = max(2, 5 - i // 2)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["venom_dark"], a),
                             stream_pts[i], stream_pts[i + 1], w + 1)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["venom_mid"], a),
                             stream_pts[i], stream_pts[i + 1], w)
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["venom_light"], a),
                             stream_pts[i], stream_pts[i + 1], max(1, w - 2))
            pygame.draw.line(surface,
                             (*_NS_xerakkuth.PALETTE["venom_hot"], a),
                             stream_pts[i], stream_pts[i + 1], 1)
        # Impact pool at target
        if t > 0.4:
            pool_r = int(15 + (t - 0.4) * 25)
            pool_a = _NS_xerakkuth._alpha(200)
            pygame.draw.ellipse(surface,
                                (*_NS_xerakkuth.PALETTE["venom_darkest"], pool_a),
                                (tx - pool_r, ty - pool_r // 3,
                                 pool_r * 2, pool_r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_xerakkuth.PALETTE["venom_dark"], pool_a),
                                (tx - pool_r + 4, ty - pool_r // 3 + 2,
                                 pool_r * 2 - 8, pool_r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_xerakkuth.PALETTE["venom_mid"], pool_a),
                                (tx - pool_r + 10, ty - pool_r // 3 + 5,
                                 pool_r * 2 - 20, pool_r * 2 // 3 - 10))
            # Bubbles
            for i in range(6):
                bub_t = (phase * 0.8 + i * 0.16) % 1.0
                bx = tx + int(math.sin(phase + i) * pool_r * 0.6)
                by = ty - int(bub_t * 15)
                ba = _NS_xerakkuth._alpha(220 * (1 - bub_t))
                _NS_xerakkuth._aacircle(surface,
                                        (*_NS_xerakkuth.PALETTE["venom_mid"], ba),
                                        (bx, by), 2)
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["venom_light"], ba),
                                 (bx, by, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_xerakkuth.PALETTE["venom_hot"], ba),
                                 (bx, by - 1, 1, 1))

    # ============================================================
    # SKILL R — EPICENTER (tremor spikes rising)
    # ============================================================
    def _draw_epicenter_ground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growing circular tremor
        if progress < 0.4:
            t = progress / 0.4
            r = int(30 + t * 40)
            a = _NS_xerakkuth._alpha(180 * t)
            # Warning ring
            for ring_i in range(3):
                pygame.draw.ellipse(
                    surface,
                    (*_NS_xerakkuth.PALETTE["crack_mid"], a),
                    (x - r + ring_i * 8, y + 42 - r // 3 + ring_i * 2,
                     r * 2 - ring_i * 16, r * 2 // 3 - ring_i * 4),
                    2,
                )
            # Cracks radiating
            for i in range(12):
                ang = i * math.pi / 6
                x1 = x + int(math.cos(ang) * 10)
                y1 = y + 42 + int(math.sin(ang) * 4)
                x2 = x + int(math.cos(ang) * r)
                y2 = y + 42 + int(math.sin(ang) * r * 0.4)
                pygame.draw.line(surface,
                                 (*_NS_xerakkuth.PALETTE["crack_dark"], a),
                                 (x1, y1), (x2, y2), 2)
                pygame.draw.line(surface,
                                 (*_NS_xerakkuth.PALETTE["crack_light"], a),
                                 (x1, y1), (x2, y2), 1)
        else:
            t = (progress - 0.4) / 0.6
            r = int(70 + t * 20)
            a = _NS_xerakkuth._alpha(200 * (1 - t * 0.3))
            # Scorched crater
            pygame.draw.ellipse(surface,
                                (*_NS_xerakkuth.PALETTE["sand_darkest"], a),
                                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_xerakkuth.PALETTE["sand_dark"], a),
                                (x - r + 5, y + 42 - r // 3 + 2,
                                 r * 2 - 10, r * 2 // 3 - 4))

    def _draw_epicenter_foreground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            return
        # Sand spikes rising from ground in rings
        t = (progress - 0.4) / 0.6
        # 3 concentric rings of spikes
        for ring_i in range(3):
            ring_r = 25 + ring_i * 22
            ring_delay = ring_i * 0.15
            if t < ring_delay:
                continue
            ring_t = min(1.0, (t - ring_delay) / 0.35)
            num_spikes = 8 + ring_i * 4
            for s_i in range(num_spikes):
                ang = s_i * math.pi * 2 / num_spikes + ring_i * 0.3
                sx = x + int(math.cos(ang) * ring_r)
                sy = y + 42 + int(math.sin(ang) * ring_r * 0.5)
                # Spike height
                spike_h = int(20 * ring_t * (1 - (t - ring_delay - 0.35) * 0.5))
                if spike_h < 2:
                    continue
                _NS_xerakkuth._draw_sand_spike(surface, sx, sy, spike_h, phase)
        # Central big spike (main)
        if t > 0.1:
            main_h = int(35 * min(1.0, t * 2))
            _NS_xerakkuth._draw_sand_spike(surface, x, y + 42, main_h, phase,
                                            big=True)

    def _draw_sand_spike(surface, sx, sy, height, phase, big=False):
        """Sand/rock spike rising from ground."""
        if height < 2:
            return
        base_w = 4 if big else 3
        tip_y = sy - height
        # Shadow
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["shadow_deep"], [
            (sx + 1, tip_y + 1),
            (sx + base_w + 1, sy + 1),
            (sx - base_w + 1, sy + 1),
        ])
        # Main body
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["sand_darkest"], [
            (sx, tip_y),
            (sx + base_w, sy),
            (sx - base_w, sy),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["sand_dark"], [
            (sx, tip_y),
            (sx + base_w - 1, sy),
            (sx - base_w + 1, sy),
        ])
        _NS_xerakkuth._poly(surface, _NS_xerakkuth.PALETTE["sand_mid"], [
            (sx, tip_y),
            (sx + base_w - 2, sy),
            (sx - base_w + 2, sy),
        ])
        # Bright edge (catches light)
        _NS_xerakkuth._aaline(surface, _NS_xerakkuth.PALETTE["sand_light"],
                              (sx, tip_y), (sx - base_w + 1, sy), 1)
        _NS_xerakkuth._aaline(surface, _NS_xerakkuth.PALETTE["sand_hot"],
                              (sx, tip_y),
                              (int(sx - base_w * 0.4), int(sy - height * 0.3)),
                              1)
        # Tip glow
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["sand_shine"],
                         (sx, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["white"],
                         (sx, tip_y, 1, 1))
        # Segment lines (chitin-like)
        for seg in range(1, 3):
            seg_y = sy - int(height * seg / 3)
            seg_w = int(base_w * (1 - seg / 3))
            pygame.draw.line(surface,
                             _NS_xerakkuth.PALETTE["sand_darkest"],
                             (sx - seg_w, seg_y),
                             (sx + seg_w, seg_y), 1)
        # Sparkles at tip
        for i in range(2):
            spark_ang = phase * 2 + i * math.pi
            spx = sx + int(math.cos(spark_ang) * 3)
            spy = tip_y - int(math.sin(spark_ang) * 2) - 1
            pygame.draw.rect(surface, _NS_xerakkuth.PALETTE["sand_hot"],
                             (spx, spy, 1, 1))


# ====================================================================================================
# YOMIGETSU - TRUE BOSS
# ====================================================================================================

class _NS_yomigetsu:
    """Namespace yomigetsu - moon demon swordsman boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Pale demon skin (bluish-white)
        "skin_darkest": (45, 40, 55),
        "skin_dark": (105, 95, 115),
        "skin_mid": (170, 155, 180),
        "skin_light": (215, 200, 225),
        "skin_shine": (240, 230, 245),

        # Hair (dark black-purple, very long flowing)
        "hair_darkest": (8, 5, 15),
        "hair_dark": (22, 15, 35),
        "hair_mid": (45, 30, 65),
        "hair_light": (85, 55, 110),
        "hair_shine": (135, 95, 165),
        "hair_edge": (185, 145, 210),

        # Purple kimono/haori (deep purple with pattern)
        "kimono_darkest": (15, 8, 25),
        "kimono_dark": (35, 20, 55),
        "kimono_mid": (75, 45, 105),
        "kimono_light": (130, 90, 165),
        "kimono_edge": (185, 145, 210),
        "kimono_shine": (215, 180, 235),

        # Under-cloth (darker gi under haori)
        "under_darkest": (5, 3, 10),
        "under_dark": (18, 12, 25),
        "under_mid": (40, 30, 55),
        "under_light": (75, 60, 95),

        # Moon breath ENERGY (bright violet-purple crescent slashes)
        "moon_darkest": (15, 5, 40),
        "moon_dark": (55, 20, 110),
        "moon_mid": (140, 70, 220),
        "moon_light": (200, 140, 255),
        "moon_hot": (235, 195, 255),
        "moon_shine": (250, 235, 255),

        # Nichirin blade (black-purple mystic steel)
        "blade_darkest": (10, 8, 18),
        "blade_dark": (30, 22, 50),
        "blade_mid": (80, 65, 120),
        "blade_light": (150, 130, 200),
        "blade_shine": (215, 200, 245),
        "blade_edge": (240, 220, 255),

        # Handle (dark red-brown wrap)
        "handle_dark": (25, 12, 8),
        "handle_mid": (85, 40, 25),
        "handle_light": (155, 90, 55),
        "handle_edge": (210, 145, 90),

        # Gold accents (tsuba, headband)
        "gold_dark": (75, 55, 15),
        "gold_mid": (170, 130, 40),
        "gold_light": (235, 200, 90),
        "gold_shine": (255, 240, 160),

        # 6 EYES (yellow-gold demon eyes)
        "eye_socket": (8, 5, 3),
        "eye_dark": (95, 65, 15),
        "eye_mid": (210, 165, 40),
        "eye_light": (250, 220, 100),
        "eye_glow": (255, 245, 180),
        "eye_pupil": (2, 2, 4),

        # Blood (demon marks on face)
        "blood_dark": (65, 8, 15),
        "blood_mid": (155, 20, 30),
        "blood_light": (220, 55, 60),

        # Moon glow (background aura white-purple)
        "moon_bg": (95, 75, 145),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_yomigetsu._clamp(color)
        if _NS_yomigetsu.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_yomigetsu._clamp(color)
        if _NS_yomigetsu.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_yomigetsu._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)

    def _draw_crescent(surface, cx, cy, radius, thickness, color, alpha,
                       angle=0.0, arc_span=math.pi):
        """Draw a crescent (moon) arc as thick line."""
        if radius < 3:
            return
        seg = max(8, int(radius * 0.6))
        pts = []
        for i in range(seg + 1):
            t = i / seg
            a = angle - arc_span / 2 + t * arc_span
            pts.append((cx + int(math.cos(a) * radius),
                        cy + int(math.sin(a) * radius)))
        for i in range(len(pts) - 1):
            pygame.draw.line(surface,
                             (*color, _NS_yomigetsu._alpha(alpha)),
                             pts[i], pts[i + 1], thickness)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_yomigetsu(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_yomigetsu._detect_moving(boss)
        _NS_yomigetsu._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_ymg_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_yomigetsu._draw_moon_aura(surface, x, y, pulse)
        _NS_yomigetsu._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX
        if active_skill == "r":
            _NS_yomigetsu._draw_perpetualnight_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "d":
            _NS_yomigetsu._draw_translucent_ground(
                surface, boss, x, y, skill_timer, pulse
            )

        # Body
        if attacking:
            _NS_yomigetsu._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_yomigetsu._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_yomigetsu._draw_idle_pose(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_yomigetsu._draw_darkmoon_slash(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "w":
            _NS_yomigetsu._draw_moonbow(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_yomigetsu._draw_moonspirit(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_yomigetsu._draw_perpetualnight_foreground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "d":
            _NS_yomigetsu._draw_translucent_foreground(
                surface, boss, x, y, skill_timer, pulse
            )

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_ymg_prev_timer", 0))
        active = bool(getattr(boss, "_ymg_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._ymg_attack_active = True
            boss._ymg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._ymg_attack_frame = int(
                getattr(boss, "_ymg_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._ymg_attack_active = False
            boss._ymg_attack_frame = 0
            active = False
        boss._ymg_prev_timer = timer
        boss._ymg_attack_progress = (
            min(1.0, getattr(boss, "_ymg_attack_frame", 0) / max(1, cd - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_ymg_last_x"):
            boss._ymg_last_x = boss.x
            boss._ymg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ymg_last_x)
        dy = abs(boss.y - boss._ymg_last_y)
        boss._ymg_last_x = boss.x
        boss._ymg_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_yomigetsu._draw_shadow(surface, x, y + 52)
        _NS_yomigetsu._draw_float_wisps(surface, x, y + 46, boss.pulse)
        _NS_yomigetsu._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )

    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.3
        bob = int(math.sin(ph * 1.0) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_yomigetsu._draw_shadow(surface, x + sway, y + 52)
        _NS_yomigetsu._draw_float_wisps(
            surface, x + sway, y + 46, ph, trail=True, facing=boss.direction
        )
        _NS_yomigetsu._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_ymg_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 4)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_yomigetsu._draw_shadow(surface, x + lunge, y + 52)
        _NS_yomigetsu._draw_float_wisps(
            surface, x + lunge, y + 46, boss.pulse, intense=True
        )
        _NS_yomigetsu._draw_slash_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
        _NS_yomigetsu._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )
        _NS_yomigetsu._draw_slash_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

    # ============================================================
    # BODY COMPOSITION
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0,
                   alpha=255):
        if alpha < 255:
            temp = pygame.Surface((200, 180), pygame.SRCALPHA)
            _NS_yomigetsu._draw_body_parts(
                temp, 100, 100, facing, phase, action, progress
            )
            temp.set_alpha(alpha)
            surface.blit(temp, (cx - 100, cy - 100))
        else:
            _NS_yomigetsu._draw_body_parts(
                surface, cx, cy, facing, phase, action, progress
            )

    def _draw_body_parts(surface, cx, cy, facing, phase, action, progress):
        # Order: long hair back -> haori sleeves back -> back arm -> legs ->
        # kimono body -> haori (over kimono) -> head -> hair front ->
        # front arm+katana
        _NS_yomigetsu._draw_hair_back(surface, cx, cy, facing, phase)
        _NS_yomigetsu._draw_haori_back_flow(surface, cx, cy, facing, phase, action)
        _NS_yomigetsu._draw_back_arm(surface, cx, cy, facing, phase, action)
        _NS_yomigetsu._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_yomigetsu._draw_kimono_body(surface, cx, cy, facing, phase)
        _NS_yomigetsu._draw_haori_front(surface, cx, cy, facing, phase)
        _NS_yomigetsu._draw_head(surface, cx, cy, facing, phase)
        _NS_yomigetsu._draw_hair_front(surface, cx, cy, facing, phase)
        _NS_yomigetsu._draw_front_arm_katana(
            surface, cx, cy, facing, phase, action, progress
        )

    # ── LEGS (kimono hakama pants dangling) ──────────────────
    def _draw_legs(surface, cx, cy, facing, phase, action):
        sway = (
            math.sin(phase * 1.3) * 3
            if action == "walk"
            else math.sin(phase * 0.5) * 1.5
        )
        # Kimono legs are wider (hakama pleats)
        for side in (-1, 1):
            lx = cx + side * 6
            ly = cy + 14
            sw = int(sway * (1 if side > 0 else -1))
            # Wide hakama shape (loose flowing)
            hak = [
                (lx - 5, ly - 1), (lx + 5, ly - 1),
                (lx + 7 + sw, ly + 8),
                (lx + 8 + sw, ly + 14),
                (lx - 8 + sw, ly + 14),
                (lx - 7 + sw, ly + 8),
            ]
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in hak])
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_darkest"], hak)
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_dark"], [
                (lx - 4, ly), (lx + 4, ly),
                (lx + 6 + sw, ly + 8), (lx + 7 + sw, ly + 13),
                (lx - 7 + sw, ly + 13), (lx - 6 + sw, ly + 8),
            ])
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_mid"], [
                (lx - 3, ly + 1), (lx + 3, ly + 1),
                (lx + 4 + sw, ly + 7), (lx + 5 + sw, ly + 12),
                (lx - 5 + sw, ly + 12), (lx - 4 + sw, ly + 7),
            ])
            # Pleat lines (hakama)
            for pleat_x in (-3, 0, 3):
                pygame.draw.line(surface,
                                 _NS_yomigetsu.PALETTE["kimono_darkest"],
                                 (lx + pleat_x, ly + 1),
                                 (lx + pleat_x + sw, ly + 13), 1)
            # Bottom hem (light edge)
            pygame.draw.line(surface, _NS_yomigetsu.PALETTE["kimono_edge"],
                             (lx - 7 + sw, ly + 13),
                             (lx + 7 + sw, ly + 13), 1)
            # Small tabi socks / geta hint at bottom
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["under_dark"], [
                (lx - 4 + sw, ly + 14), (lx + 4 + sw, ly + 14),
                (lx + 5 + sw + facing, ly + 17),
                (lx - 3 + sw + facing, ly + 17),
            ])
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["under_mid"], [
                (lx - 3 + sw, ly + 15), (lx + 3 + sw, ly + 15),
                (lx + 4 + sw + facing, ly + 16),
            ])
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["under_light"],
                             (lx + sw, ly + 15, 1, 1))

    # ── KIMONO BODY (dark under-cloth) ───────────────────────
    def _draw_kimono_body(surface, cx, cy, facing, phase):
        # Body/torso — inner black kimono
        body = [
            (cx - 10, cy - 10), (cx - 6, cy - 13),
            (cx + 6, cy - 13), (cx + 10, cy - 10),
            (cx + 11, cy), (cx + 10, cy + 10),
            (cx + 6, cy + 14), (cx - 6, cy + 14),
            (cx - 10, cy + 10), (cx - 11, cy),
        ]
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in body])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["under_darkest"], body)
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["under_dark"], [
            (cx - 9, cy - 9), (cx - 5, cy - 12),
            (cx + 5, cy - 12), (cx + 9, cy - 9),
            (cx + 10, cy), (cx + 9, cy + 9),
            (cx + 5, cy + 13), (cx - 5, cy + 13),
            (cx - 9, cy + 9), (cx - 10, cy),
        ])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["under_mid"], [
            (cx - 7, cy - 6), (cx - 4, cy - 10),
            (cx + 4, cy - 10), (cx + 7, cy - 6),
            (cx + 8, cy), (cx + 7, cy + 6),
            (cx + 4, cy + 10), (cx - 4, cy + 10),
            (cx - 7, cy + 6), (cx - 8, cy),
        ])
        # Kimono V-collar (crossed opening)
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["under_darkest"], [
            (cx - 4, cy - 12), (cx, cy - 6),
            (cx + 4, cy - 12), (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"], [
            (cx - 3, cy - 11), (cx, cy - 6),
            (cx + 3, cy - 11), (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Sash/obi
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_darkest"],
                         (cx - 11, cy + 8, 22, 6))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_dark"],
                         (cx - 10, cy + 9, 20, 4))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_mid"],
                         (cx - 10, cy + 9, 20, 2))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_light"],
                         (cx - 8, cy + 9, 16, 1))
        # Sash knot
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_darkest"],
                         (cx - 3, cy + 7, 6, 8))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_dark"],
                         (cx - 2, cy + 8, 4, 6))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_mid"],
                         (cx - 2, cy + 8, 4, 3))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_edge"],
                         (cx - 1, cy + 8, 2, 1))

    # ── HAORI (purple outer robe front) ──────────────────────
    def _draw_haori_front(surface, cx, cy, facing, phase):
        """Front open haori (purple outer robe)."""
        # Left side of haori (open at chest)
        for side in (-1, 1):
            haori_pts = [
                (cx + side * 5, cy - 12),
                (cx + side * 11, cy - 10),
                (cx + side * 13, cy - 3),
                (cx + side * 12, cy + 6),
                (cx + side * 10, cy + 12),
                (cx + side * 6, cy + 14),
                (cx + side * 3, cy + 10),
                (cx + side * 2, cy - 5),
                (cx + side * 3, cy - 11),
            ]
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in haori_pts])
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_darkest"], haori_pts)
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_dark"], [
                (cx + side * 5, cy - 11),
                (cx + side * 10, cy - 9),
                (cx + side * 12, cy - 3),
                (cx + side * 11, cy + 5),
                (cx + side * 9, cy + 11),
                (cx + side * 5, cy + 13),
                (cx + side * 3, cy + 9),
                (cx + side * 3, cy - 10),
            ])
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_mid"], [
                (cx + side * 6, cy - 9),
                (cx + side * 9, cy - 7),
                (cx + side * 10, cy - 2),
                (cx + side * 9, cy + 4),
                (cx + side * 7, cy + 10),
                (cx + side * 4, cy + 8),
                (cx + side * 4, cy - 8),
            ])
            # Purple edge (bright trim)
            pygame.draw.line(surface, _NS_yomigetsu.PALETTE["kimono_edge"],
                             (cx + side * 3, cy - 11),
                             (cx + side * 3, cy + 10), 1)
            # Scale pattern (small hexagon-ish dots)
            for pattern_i in range(4):
                for row_i in range(3):
                    px = cx + side * (5 + pattern_i * 2)
                    py = cy - 6 + row_i * 5
                    if pattern_i % 2 == row_i % 2:
                        pygame.draw.rect(surface,
                                         _NS_yomigetsu.PALETTE["kimono_light"],
                                         (px, py, 1, 1))
                    else:
                        pygame.draw.rect(surface,
                                         _NS_yomigetsu.PALETTE["kimono_edge"],
                                         (px, py, 1, 1))
        # Highlight (top shoulders)
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_shine"],
                         (cx - 8, cy - 10, 3, 1))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["kimono_shine"],
                         (cx + 5, cy - 10, 3, 1))

    def _draw_haori_back_flow(surface, cx, cy, facing, phase, action):
        """Long haori tail flowing behind."""
        back = -facing
        base_x = cx + back * 6
        base_y = cy - 6
        seg = 8
        pts_t = []
        pts_b = []
        for i in range(seg + 1):
            t = i / seg
            sx = base_x - int(facing * t * 30)
            sy = base_y + int(t * 28) - int(t * t * 6)
            wave = math.sin(phase * 1.2 + t * math.pi * 1.4) * (3 + t * 5)
            sy += int(wave)
            w = int(5 * (1 - t * 0.4))
            pts_t.append((sx, sy - w))
            pts_b.append((sx, sy + w))
        full = pts_t + list(reversed(pts_b))
        if len(full) >= 3:
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in full])
            _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_darkest"], full)
            inner = pts_t[:-1] + list(reversed(pts_b[:-1]))
            if len(inner) >= 3:
                _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_dark"], inner)
            inner2 = pts_t[:-2] + list(reversed(pts_b[:-2]))
            if len(inner2) >= 3:
                _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_mid"], inner2)
        # Purple edge highlight
        for i in range(len(pts_t) - 1):
            a = _NS_yomigetsu._alpha(220 * (1 - i / len(pts_t)))
            pygame.draw.line(surface,
                             (*_NS_yomigetsu.PALETTE["kimono_edge"], a),
                             pts_t[i], pts_t[i + 1], 1)
        # Moon glow at tip
        if pts_t:
            tip = pts_t[-1]
            for r in range(4, 0, -1):
                a = _NS_yomigetsu._alpha(150 * (4 - r) / 4)
                _NS_yomigetsu._aacircle(surface,
                                        (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                        (tip[0], tip[1]), r)
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["moon_light"],
                             (tip[0], tip[1], 1, 1))

    # ── BACK ARM ─────────────────────────────────────────────
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        back = -facing
        sx = cx + back * 10
        sy = cy - 8
        sway = math.sin(phase * 0.7) * 2
        ex = sx + back * 6
        ey = sy + 10 + int(sway)
        hx = ex + back * 2
        hy = ey + 8
        # Upper arm (kimono sleeve — wide)
        # Draw as loose sleeve poly
        sleeve_pts = [
            (sx - 3, sy), (sx + 3, sy),
            (ex + 4, ey), (ex + 5, ey + 5),
            (ex - 5, ey + 5), (ex - 4, ey),
        ]
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in sleeve_pts])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_darkest"], sleeve_pts)
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_dark"], [
            (sx - 2, sy + 1), (sx + 2, sy + 1),
            (ex + 3, ey), (ex + 4, ey + 4),
            (ex - 4, ey + 4), (ex - 3, ey),
        ])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_mid"], [
            (sx - 1, sy + 2), (sx + 1, sy + 2),
            (ex + 2, ey), (ex + 2, ey + 3),
            (ex - 2, ey + 3), (ex - 2, ey),
        ])
        # Sleeve edge
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["kimono_edge"],
                         (ex - 5, ey + 5), (ex + 5, ey + 5), 1)
        # Forearm (skin exposed, pale)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                              (ex + 1, ey + 6), (hx + 1, hy + 2), 5)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                              (ex, ey + 5), (hx, hy), 4)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_dark"],
                              (ex, ey + 5), (hx, hy), 3)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_mid"],
                              (ex, ey + 4), (hx, hy - 1), 1)
        # Fist
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                                (hx + 1, hy + 1), 3)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                                (hx, hy), 3)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["skin_dark"],
                                (hx, hy), 2)
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))

    # ── FRONT ARM + KATANA (Nichirin blade) ──────────────────
    def _draw_front_arm_katana(surface, cx, cy, facing, phase, action, progress):
        base_angle = -math.pi / 6
        if action == "attack":
            if progress < 0.3:
                t = progress / 0.3
                base_angle = -math.pi / 6 - t * math.pi / 2.2
            elif progress < 0.55:
                t = (progress - 0.3) / 0.25
                base_angle = -math.pi / 6 - math.pi / 2.2 + t * (math.pi * 1.15)
            else:
                t = (progress - 0.55) / 0.45
                base_angle = -math.pi / 6 + (math.pi * 0.7 * (1 - t))
        else:
            base_angle += math.sin(phase * 0.5) * 0.08

        sx = cx + facing * 10
        sy = cy - 8
        arm_len = 18
        hx = sx + int(math.cos(base_angle) * arm_len) * facing
        hy = sy + int(math.sin(base_angle) * arm_len)
        ex = sx + int(math.cos(base_angle) * arm_len * 0.5) * facing
        ey = sy + int(math.sin(base_angle) * arm_len * 0.5) + 2

        # Sleeve (upper arm) — wider kimono style
        sleeve_end_perp = base_angle + math.pi / 2
        sleeve_a_x = ex + int(math.cos(sleeve_end_perp) * 4)
        sleeve_a_y = ey + int(math.sin(sleeve_end_perp) * 4)
        sleeve_b_x = ex - int(math.cos(sleeve_end_perp) * 4)
        sleeve_b_y = ey - int(math.sin(sleeve_end_perp) * 4)
        sleeve_pts = [
            (sx - 3, sy), (sx + 3, sy),
            (sleeve_a_x, sleeve_a_y),
            (sleeve_b_x, sleeve_b_y),
        ]
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in sleeve_pts])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_darkest"], sleeve_pts)
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_dark"], [
            (sx - 2, sy + 1), (sx + 2, sy + 1),
            (int((sleeve_a_x + ex) / 2), int((sleeve_a_y + ey) / 2)),
            (int((sleeve_b_x + ex) / 2), int((sleeve_b_y + ey) / 2)),
        ])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["kimono_mid"], [
            (sx - 1, sy + 2), (sx + 1, sy + 2),
            (ex, ey - 1), (ex, ey + 1),
        ])
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["kimono_edge"],
                         (sleeve_a_x, sleeve_a_y),
                         (sleeve_b_x, sleeve_b_y), 1)

        # Forearm (skin)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                              (ex + 1, ey + 2), (hx + 1, hy + 2), 6)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                              (ex, ey), (hx, hy), 5)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_dark"],
                              (ex, ey), (hx, hy), 4)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_mid"],
                              (ex, ey - 1), (hx, hy - 1), 2)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["skin_light"],
                              (ex, ey - 2), (hx, hy - 2), 1)

        # HAND
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                                (hx + 1, hy + 1), 4)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                                (hx, hy), 4)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["skin_dark"],
                                (hx, hy), 3)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["skin_mid"],
                                (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))

        # NICHIRIN KATANA
        _NS_yomigetsu._draw_nichirin(surface, hx, hy, facing, phase, base_angle,
                                      action)

    def _draw_nichirin(surface, hx, hy, facing, phase, arm_angle, action):
        """Long dark Nichirin katana with purple mystic glow."""
        # Handle (goes back from hand)
        tsuka_len = 7
        tsuka_end_x = hx - int(math.cos(arm_angle) * tsuka_len) * facing
        tsuka_end_y = hy - int(math.sin(arm_angle) * tsuka_len)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1),
                              (tsuka_end_x + 1, tsuka_end_y + 1), 4)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["handle_dark"],
                              (hx, hy), (tsuka_end_x, tsuka_end_y), 3)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["handle_mid"],
                              (hx, hy), (tsuka_end_x, tsuka_end_y), 2)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["handle_edge"],
                              (hx, hy - 1), (tsuka_end_x, tsuka_end_y - 1), 1)
        # Handle wrap crosshatch
        for i in range(1, tsuka_len):
            t = i / tsuka_len
            wx = int(hx + (tsuka_end_x - hx) * t)
            wy = int(hy + (tsuka_end_y - hy) * t)
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["handle_dark"],
                             (wx, wy, 1, 2))
        # Pommel (gold end cap)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["gold_dark"],
                                (tsuka_end_x, tsuka_end_y), 2)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["gold_mid"],
                                (tsuka_end_x, tsuka_end_y), 1)
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["gold_shine"],
                         (tsuka_end_x, tsuka_end_y, 1, 1))

        # Tsuba (guard — square-ish gold)
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                         (hx - 3, hy - 3, 7, 7))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["gold_dark"],
                         (hx - 3, hy - 3, 7, 6))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["gold_mid"],
                         (hx - 2, hy - 3, 5, 5))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["gold_light"],
                         (hx - 2, hy - 3, 5, 2))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["gold_shine"],
                         (hx - 1, hy - 3, 3, 1))
        # Central hole
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                         (hx, hy - 1, 1, 2))

        # BLADE (long dark Nichirin)
        blade_len = 34  # very long katana
        blade_tip_x = hx + int(math.cos(arm_angle) * blade_len) * facing
        blade_tip_y = hy + int(math.sin(arm_angle) * blade_len)
        blade_base_x = hx + int(math.cos(arm_angle) * 4) * facing
        blade_base_y = hy + int(math.sin(arm_angle) * 4)
        perp = arm_angle + math.pi / 2
        bw = 2
        bp1_x = blade_base_x + int(math.cos(perp) * bw)
        bp1_y = blade_base_y + int(math.sin(perp) * bw)
        bp2_x = blade_base_x - int(math.cos(perp) * bw)
        bp2_y = blade_base_y - int(math.sin(perp) * bw)
        blade_pts = [
            (blade_tip_x, blade_tip_y),
            (bp1_x, bp1_y),
            (bp2_x, bp2_y),
        ]
        # Shadow
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in blade_pts])
        # Dark mystic core
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["blade_darkest"], blade_pts)
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["blade_dark"], [
            (blade_tip_x, blade_tip_y),
            (int((bp1_x + blade_base_x) / 2),
             int((bp1_y + blade_base_y) / 2)),
            (blade_base_x, blade_base_y),
        ])
        # Blade sharp edge (top)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["blade_mid"],
                              (blade_base_x, blade_base_y),
                              (blade_tip_x, blade_tip_y), 2)
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["blade_light"],
                              (blade_base_x, blade_base_y),
                              (blade_tip_x, blade_tip_y), 1)
        # Purple mystic aura along edge
        _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["blade_edge"],
                              (int((blade_base_x + blade_tip_x) / 2),
                               int((blade_base_y + blade_tip_y) / 2)),
                              (blade_tip_x, blade_tip_y), 1)
        # Tip shine
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["blade_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        # Moon chakra glow at tip
        for r in range(5, 0, -1):
            a = _NS_yomigetsu._alpha(140 * (5 - r) / 5)
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                                    (blade_tip_x, blade_tip_y), r)
        # Small floating moon crescents around blade (idle)
        if action == "idle":
            for i in range(3):
                cr_phase = phase * 0.5 + i * 0.66
                cr_t = (cr_phase % 1.0)
                cr_x = int(blade_base_x + (blade_tip_x - blade_base_x) * cr_t)
                cr_y = int(blade_base_y + (blade_tip_y - blade_base_y) * cr_t)
                cr_x += int(math.sin(cr_phase * 5) * 4)
                cr_y += int(math.cos(cr_phase * 5) * 4)
                a = _NS_yomigetsu._alpha(150 * (1 - cr_t))
                _NS_yomigetsu._draw_crescent(
                    surface, cr_x, cr_y, 3, 1,
                    _NS_yomigetsu.PALETTE["moon_light"], a,
                    angle=math.pi * cr_t,
                )

    # ── HEAD (with 6 demon eyes) ─────────────────────────────
    def _draw_head(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        # Face
        head_pts = [
            (hx - 7, hy + 5), (hx - 8, hy - 1), (hx - 6, hy - 7),
            (hx - 1, hy - 9), (hx + 4, hy - 9), (hx + 7, hy - 6),
            (hx + 8, hy), (hx + 7, hy + 5), (hx + 4, hy + 7),
            (hx - 1, hy + 7), (hx - 5, hy + 6),
        ]
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["skin_darkest"], head_pts)
        # Pale skin main
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["skin_dark"], [
            (hx - 6, hy + 4), (hx - 7, hy), (hx - 5, hy - 6),
            (hx, hy - 8), (hx + 3, hy - 8), (hx + 6, hy - 5),
            (hx + 7, hy), (hx + 6, hy + 4), (hx + 3, hy + 6),
            (hx, hy + 6), (hx - 4, hy + 5),
        ])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["skin_mid"], [
            (hx - 5, hy - 3), (hx - 3, hy - 6),
            (hx + 2, hy - 6), (hx + 5, hy - 3),
            (hx + 6, hy), (hx + 4, hy + 3),
            (hx - 1, hy + 3), (hx - 5, hy),
        ])
        _NS_yomigetsu._poly(surface, _NS_yomigetsu.PALETTE["skin_light"], [
            (hx - 2, hy - 5), (hx + 2, hy - 5),
            (hx + 3, hy - 3), (hx - 3, hy - 3),
        ])
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["skin_shine"],
                         (hx, hy - 5, 2, 1))
        # Blood marks (demon veins on face - red streaks)
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["blood_dark"],
                         (hx - 5, hy - 4), (hx - 3, hy), 1)
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["blood_mid"],
                         (hx - 5, hy - 4), (hx - 3, hy - 1), 1)
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["blood_dark"],
                         (hx + 5, hy - 4), (hx + 3, hy), 1)
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["blood_mid"],
                         (hx + 5, hy - 4), (hx + 3, hy - 1), 1)
        # Nose
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy - 1, 1, 3))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["skin_dark"],
                         (hx + facing * 2, hy + 1, 1, 1))
        # Mouth (thin serious line)
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy + 4),
                         (hx + facing * 4, hy + 4), 1)
        # Ear
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["skin_darkest"],
                         (hx - facing * 7, hy, 2, 3))

        # SIX DEMON EYES — 3 rows of 2 eyes each (KOKUSHIBO signature!)
        _NS_yomigetsu._draw_six_eyes(surface, hx, hy, facing, phase)

    def _draw_six_eyes(surface, hx, hy, facing, phase):
        """Six golden demon eyes arranged in 3 rows."""
        # Row 1 (top): main eyes at normal position
        # Row 2 (mid): secondary eyes slightly outside
        # Row 3 (bottom): smallest eyes at cheeks
        eye_positions = [
            # (x_off, y_off, size)
            (2, -3, "big"),      # row 1 right main
            (-3, -2, "big"),     # row 1 left main
            (4, 0, "mid"),       # row 2 right
            (-5, 0, "mid"),      # row 2 left
            (3, 3, "small"),     # row 3 right
            (-4, 3, "small"),    # row 3 left
        ]
        for ex_off, ey_off, size_class in eye_positions:
            ex = hx + ex_off
            ey = hy + ey_off
            _NS_yomigetsu._draw_demon_eye(surface, ex, ey, facing, phase,
                                           size_class)

    def _draw_demon_eye(surface, ex, ey, facing, phase, size_class="big"):
        """Yellow/gold demon eye with vertical pupil."""
        pulse = math.sin(phase * 2.5) * 0.25 + 0.75

        if size_class == "big":
            w, h = 4, 3
        elif size_class == "mid":
            w, h = 3, 2
        else:  # small
            w, h = 2, 2

        # Socket
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["eye_socket"],
                         (ex - w // 2, ey - h // 2, w, h))
        # Glow halo (only for big/mid)
        if size_class != "small":
            for r in range(3, 0, -1):
                a = _NS_yomigetsu._alpha(70 * (3 - r) / 3 * pulse)
                _NS_yomigetsu._aacircle(surface,
                                        (*_NS_yomigetsu.PALETTE["eye_mid"], a),
                                        (ex, ey), r)
        # Iris
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["eye_dark"],
                         (ex - w // 2, ey - h // 2, w, h))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["eye_mid"],
                         (ex - w // 2 + 1, ey - h // 2, w - 1, h))
        pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["eye_light"],
                         (ex, ey - h // 2, w - 2, 1))
        # Vertical slit pupil
        pygame.draw.line(surface, _NS_yomigetsu.PALETTE["eye_pupil"],
                         (ex, ey - h // 2), (ex, ey + h // 2 - 1), 1)
        # Hot spot
        if size_class == "big":
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["eye_glow"],
                             (ex + 1, ey - 1, 1, 1))

    # ── HAIR (long flowing dark purple) ──────────────────────
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Very long flowing hair behind body."""
        hx = cx + facing * 2
        hy = cy - 20
        # Multiple long flowing strands
        strands = [
            (-5, -6, 0.0, 40, 6),
            (-3, -8, 0.3, 44, 7),
            (-1, -9, 0.6, 46, 7),
            (1, -9, 0.9, 45, 7),
            (3, -8, 1.2, 42, 6),
            (5, -6, 1.5, 38, 5),
            (-6, -3, 0.4, 34, 5),
            (6, -3, 1.6, 32, 4),
            (-4, -1, 0.8, 38, 5),
            (4, -1, 1.8, 36, 4),
        ]
        for (ox, oy, ph_off, length, base_w) in strands:
            pts = []
            seg = 9
            for j in range(seg + 1):
                t = j / seg
                # Base direction: back + down
                sx = hx + ox - int(facing * t * length * 0.4)
                sy = hy + oy + int(t * length * 0.85)
                # Wave
                wave = math.sin(phase * 1.0 + ph_off + t * math.pi * 1.6)
                sx += int(wave * (2 + t * 6)) * (-facing)
                sy += int(math.sin(phase * 0.7 + ph_off + t) * 2)
                pts.append((sx, sy))
            for j in range(len(pts) - 1):
                thick = max(1, base_w - j // 2)
                _NS_yomigetsu._aaline(surface,
                                      _NS_yomigetsu.PALETTE["shadow_deep"],
                                      (pts[j][0] + 1, pts[j][1] + 1),
                                      (pts[j + 1][0] + 1, pts[j + 1][1] + 1),
                                      thick + 1)
                _NS_yomigetsu._aaline(surface,
                                      _NS_yomigetsu.PALETTE["hair_darkest"],
                                      pts[j], pts[j + 1], thick)
                _NS_yomigetsu._aaline(surface,
                                      _NS_yomigetsu.PALETTE["hair_dark"],
                                      pts[j], pts[j + 1], max(1, thick - 1))
                if thick > 2:
                    _NS_yomigetsu._aaline(surface,
                                          _NS_yomigetsu.PALETTE["hair_mid"],
                                          (pts[j][0], pts[j][1] - 1),
                                          (pts[j + 1][0], pts[j + 1][1] - 1),
                                          max(1, thick - 3))
                if thick > 4:
                    _NS_yomigetsu._aaline(surface,
                                          _NS_yomigetsu.PALETTE["hair_light"],
                                          (pts[j][0], pts[j][1] - 2),
                                          (pts[j + 1][0], pts[j + 1][1] - 2),
                                          1)
            # Purple wisp on some strands
            if base_w >= 6 and len(pts) > 4:
                for j in range(3, len(pts) - 1, 2):
                    a = _NS_yomigetsu._alpha(
                        140 * (1 - j / len(pts))
                        * (0.5 + 0.5 * math.sin(phase * 2 + ph_off))
                    )
                    pygame.draw.rect(surface,
                                     (*_NS_yomigetsu.PALETTE["hair_edge"], a),
                                     (pts[j][0], pts[j][1], 1, 1))

    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front bangs partially covering forehead — thin strands over face."""
        hx = cx + facing * 2
        hy = cy - 20
        bangs = [
            (-4, -7, 0.0, 8),
            (-1, -8, 0.3, 10),
            (2, -8, 0.6, 10),
            (5, -6, 0.9, 8),
            (-6, -5, 1.2, 6),
            (7, -4, 1.5, 5),
        ]
        for (ox, oy, ph_off, length) in bangs:
            bx = hx + ox
            by = hy + oy
            sway = math.sin(phase * 0.7 + ph_off) * 1
            tip_x = bx + int((facing * 1) + sway)
            tip_y = by + length
            _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["hair_darkest"],
                                  (bx, by), (tip_x, tip_y), 3)
            _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["hair_dark"],
                                  (bx, by), (tip_x, tip_y), 2)
            _NS_yomigetsu._aaline(surface, _NS_yomigetsu.PALETTE["hair_mid"],
                                  (bx, by - 1), (tip_x, tip_y - 1), 1)
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))

    # ============================================================
    # BASIC ATTACK — CRESCENT MOON SLASH TRAIL + IMPACT
    # ============================================================
    def _get_katana_tip(cx, cy, facing, progress):
        if progress < 0.3:
            t = progress / 0.3
            angle = -math.pi / 6 - t * math.pi / 2.2
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            angle = -math.pi / 6 - math.pi / 2.2 + t * (math.pi * 1.15)
        else:
            t = (progress - 0.55) / 0.45
            angle = -math.pi / 6 + (math.pi * 0.7 * (1 - t))
        sx = cx + facing * 10
        sy = cy - 8
        arm_len = 18
        hx = sx + int(math.cos(angle) * arm_len) * facing
        hy = sy + int(math.sin(angle) * arm_len)
        blade_len = 34
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        return tip_x, tip_y, angle

    def _draw_slash_trail(surface, boss, cx, cy, facing, progress):
        """Crescent moon shaped trail during basic slash."""
        if progress < 0.28 or progress > 0.7:
            return
        if progress < 0.32:
            intensity = (progress - 0.28) / 0.04
        elif progress < 0.55:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.55) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        num = 16
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.24
            if sp < 0.28:
                continue
            tx, ty, ang = _NS_yomigetsu._get_katana_tip(cx, cy, facing, sp)
            trail.append((tx, ty, ang, i))
        if len(trail) < 2:
            return
        trail.reverse()
        ts = pygame.Surface((340, 340), pygame.SRCALPHA)
        ox = cx - 170
        oy = cy - 170
        # Layered arc trail
        layers = [
            (_NS_yomigetsu.PALETTE["moon_darkest"], 16, 100),
            (_NS_yomigetsu.PALETTE["moon_dark"], 12, 150),
            (_NS_yomigetsu.PALETTE["moon_mid"], 7, 200),
            (_NS_yomigetsu.PALETTE["moon_light"], 3, 240),
            (_NS_yomigetsu.PALETTE["moon_shine"], 1, 255),
        ]
        for color, max_w, max_a in layers:
            for i in range(len(trail) - 1):
                p1, p2 = trail[i], trail[i + 1]
                fade = 1.0 - (p1[3] / num)
                a = _NS_yomigetsu._alpha(max_a * fade * intensity)
                w = max(1, int(max_w * fade))
                if a > 0:
                    pygame.draw.line(
                        ts, (*color, a),
                        (p1[0] - ox, p1[1] - oy),
                        (p2[0] - ox, p2[1] - oy), w,
                    )
        # Small crescents scattered along trail (moon breathing signature)
        for i, (tx, ty, ang, idx) in enumerate(trail):
            fade = 1.0 - (idx / num)
            a = _NS_yomigetsu._alpha(220 * fade * intensity)
            if a <= 0 or i % 3 != 0:
                continue
            # Small crescent
            cr_r = 3 + (i % 2)
            _NS_yomigetsu._draw_crescent(
                ts, tx - ox, ty - oy, cr_r, 1,
                _NS_yomigetsu.PALETTE["moon_hot"], a,
                angle=ang + math.pi / 4,
            )
            pygame.draw.rect(ts, (*_NS_yomigetsu.PALETTE["moon_shine"], a),
                             (tx - ox, ty - oy, 1, 1))
        surface.blit(ts, (ox, oy))
        # Leading edge
        if trail:
            lead = trail[0]
            for r in range(12, 2, -2):
                a = _NS_yomigetsu._alpha(180 * (12 - r) / 12 * intensity)
                _NS_yomigetsu._aacircle(
                    surface, (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                    (lead[0], lead[1]), r,
                )
            _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["moon_hot"],
                                    (lead[0], lead[1]), 3)
            _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["white"],
                                    (lead[0], lead[1]), 1)

    def _draw_slash_impact(surface, boss, cx, cy, facing, progress):
        if progress < 0.5 or progress > 0.7:
            return
        t = (progress - 0.5) / 0.2
        inten = math.sin(t * math.pi)
        tx, ty, ang = _NS_yomigetsu._get_katana_tip(cx, cy, facing, progress)
        ix = tx + facing * 4
        iy = ty
        r = int(6 + t * 16)
        a = _NS_yomigetsu._alpha(255 * inten)
        # Central burst
        for rr in range(r + 4, 0, -2):
            ra = _NS_yomigetsu._alpha(a * (r + 4 - rr) / (r + 4))
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_darkest"], ra),
                                    (ix, iy), rr)
        _NS_yomigetsu._aacircle(surface,
                                (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                (ix, iy), max(2, r - 3))
        _NS_yomigetsu._aacircle(surface,
                                (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                                (ix, iy), max(1, r - 7))
        _NS_yomigetsu._aacircle(surface,
                                (*_NS_yomigetsu.PALETTE["moon_light"], a),
                                (ix, iy), max(1, r - 10))
        _NS_yomigetsu._aacircle(surface,
                                (*_NS_yomigetsu.PALETTE["moon_hot"], a),
                                (ix, iy), max(1, r - 13))
        pygame.draw.rect(surface, (*_NS_yomigetsu.PALETTE["white"], a),
                         (ix, iy, 1, 1))
        # BIG CRESCENT MOON slash at impact point (signature)
        big_cr_r = int(r * 1.8)
        for cr_layer, (w, color, wa) in enumerate([
            (5, _NS_yomigetsu.PALETTE["moon_darkest"], 100),
            (3, _NS_yomigetsu.PALETTE["moon_mid"], 200),
            (2, _NS_yomigetsu.PALETTE["moon_hot"], 240),
            (1, _NS_yomigetsu.PALETTE["white"], 255),
        ]):
            la = _NS_yomigetsu._alpha(wa * inten)
            _NS_yomigetsu._draw_crescent(
                surface, ix, iy, big_cr_r, w,
                color, la,
                angle=ang + math.pi / 2 * facing,
                arc_span=math.pi * 1.2,
            )
        # Sparks
        for i in range(10):
            sa = i * math.pi / 5 + progress * 4
            dist = int(r * 1.4)
            ex = ix + int(math.cos(sa) * dist)
            ey = iy + int(math.sin(sa) * dist)
            pygame.draw.rect(surface,
                             (*_NS_yomigetsu.PALETTE["moon_hot"], a),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_yomigetsu.PALETTE["white"], a),
                             (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / FLOATING FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((140, 28), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            a = max(0, (14 - r) * 16)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 14 - r, 120 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (10, 5, 15, 170), (8, 8, 124, 12))
        surface.blit(sh, (x - 70, y - 14))

    def _draw_moon_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for r in range(95, 5, -5):
            a = _NS_yomigetsu._alpha((95 - r) * 1.1 * pulse)
            if a > 0:
                _NS_yomigetsu._aacircle(aura,
                                        (*_NS_yomigetsu.PALETTE["moon_darkest"], a),
                                        (120, 100), r)
        for r in range(55, 5, -3):
            a = _NS_yomigetsu._alpha((55 - r) * 1.3 * pulse)
            if a > 0:
                _NS_yomigetsu._aacircle(aura,
                                        (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                        (120, 100), r)
        surface.blit(aura, (x - 120, y - 100))
        # Floating crescents (small moons)
        for i in range(6):
            ang = phase * 0.3 + i * math.pi / 3
            rd = 50 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.45)
            a = _NS_yomigetsu._alpha(180)
            _NS_yomigetsu._draw_crescent(
                surface, sx, sy, 3, 1,
                _NS_yomigetsu.PALETTE["moon_light"], a,
                angle=phase + i,
            )
        # Sparkles
        for i in range(10):
            ang = phase * 0.5 + i * math.pi / 5 + 1.0
            rd = 40 + int(math.sin(phase * 1.5 + i) * 10)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.4)
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["moon_hot"],
                             (sx, sy, 1, 1))

    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((140, 34), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(22, 3, -2):
            a = _NS_yomigetsu._alpha((22 - r) * 3 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_yomigetsu.PALETTE["moon_darkest"], a),
                    (70 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(14, 3, -2):
            a = _NS_yomigetsu._alpha((14 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                    (70 - r, 17 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising motes (purple)
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 18)
            a = _NS_yomigetsu._alpha(200 * (1 - t) * strength)
            if a > 0:
                _NS_yomigetsu._aacircle(surface,
                                        (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                        (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_yomigetsu.PALETTE["moon_hot"], a),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_yomigetsu._alpha(140 - i * 25)
                if a > 0:
                    _NS_yomigetsu._aacircle(
                        surface, (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                        (sx, sy), max(2, 5 - i),
                    )

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_yomigetsu.PALETTE["moon_darkest"], 180),
                            (5, 14, 160, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_yomigetsu.PALETTE["moon_dark"], 210),
                            (15, 16, 140, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_yomigetsu.PALETTE["moon_mid"], 190),
                            (25, 18, 120, 16), 1)
        for i in range(10):
            ang = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(ang) * 45)
            y1 = 25 + int(math.sin(ang) * 8)
            x2 = 85 + int(math.cos(ang) * 72)
            y2 = 25 + int(math.sin(ang) * 12)
            pygame.draw.line(ring, (*_NS_yomigetsu.PALETTE["moon_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_yomigetsu.PALETTE["moon_hot"],
                       _NS_yomigetsu._alpha(150 * pulse)),
                (10, 8, 150, 32), 1,
            )
        surface.blit(ring, (x - 85, y - 23))

    # ============================================================
    # SKILL Q — DARK MOON: EVENING PALACE (horizontal crescent slash)
    # ============================================================
    def _draw_darkmoon_slash(surface, boss, x, y, timer, phase):
        """Single big horizontal crescent slash flying forward."""
        facing = boss.direction
        duration = 45
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_yomigetsu._target_position(boss, x, y)
        if progress < 0.15:
            # Charge
            t = progress / 0.15
            ox = x + facing * 25
            oy = y - 5
            for r in range(int(8 * t) + 3, 0, -1):
                a = _NS_yomigetsu._alpha(200 * (8 * t + 3 - r) / (8 * t + 3))
                _NS_yomigetsu._aacircle(surface,
                                        (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                        (ox, oy), r)
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        start_x = x + facing * 30
        start_y = y - 5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            a = _NS_yomigetsu._alpha(200 - i * 22)
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_darkest"], a),
                                    (px, py), max(2, 8 - i))
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                    (px, py), max(1, 6 - i))
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                                    (px, py), max(1, 4 - i))
        # Big crescent projectile
        cr_r = 14
        for cr_layer, (w, color, wa) in enumerate([
            (5, _NS_yomigetsu.PALETTE["moon_darkest"], 120),
            (3, _NS_yomigetsu.PALETTE["moon_dark"], 180),
            (2, _NS_yomigetsu.PALETTE["moon_mid"], 220),
            (1, _NS_yomigetsu.PALETTE["moon_hot"], 255),
        ]):
            _NS_yomigetsu._draw_crescent(
                surface, bx, by, cr_r, w, color, wa,
                angle=0 if facing > 0 else math.pi,
                arc_span=math.pi * 1.1,
            )
        # Center bright
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["moon_hot"],
                                (bx, by), 3)
        _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["white"],
                                (bx, by), 1)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            _NS_yomigetsu._draw_crescent_impact(surface, tx, ty, st, phase)

    def _draw_crescent_impact(surface, tx, ty, t, phase, big=False):
        """Small crescent impact burst."""
        base_r = 25 if big else 15
        r = int(base_r + t * (25 if big else 15))
        a = _NS_yomigetsu._alpha(255 * (1 - t))
        for rr in range(r + 3, 0, -2):
            ra = _NS_yomigetsu._alpha(a * (r + 3 - rr) / (r + 3))
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_dark"], ra),
                                    (tx, ty), rr)
        _NS_yomigetsu._aacircle(surface,
                                (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                                (tx, ty), max(1, r - 4))
        _NS_yomigetsu._aacircle(surface,
                                (*_NS_yomigetsu.PALETTE["moon_hot"], a),
                                (tx, ty), max(1, r - 8))
        # Small crescents flying outward
        for i in range(6):
            ang = i * math.pi / 3 + t * 3
            dist = int(r * 1.2)
            cx = tx + int(math.cos(ang) * dist)
            cy = ty + int(math.sin(ang) * dist)
            _NS_yomigetsu._draw_crescent(
                surface, cx, cy, 4, 1,
                _NS_yomigetsu.PALETTE["moon_hot"], a,
                angle=ang,
            )

    # ============================================================
    # SKILL W — MOONBOW HALF MOON (multiple crescents fan)
    # ============================================================
    def _draw_moonbow(surface, boss, x, y, timer, phase):
        """Multiple crescents in a bow-shape fan."""
        facing = boss.direction
        duration = 55
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_yomigetsu._target_position(boss, x, y)
        if progress < 0.15:
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        num = 5
        start_x = x + facing * 25
        start_y = y - 5
        base_dist = math.hypot(tx - start_x, ty - start_y)
        base_ang = math.atan2(ty - start_y, tx - start_x)
        spread = math.pi / 4
        for c_i in range(num):
            ang_off = (c_i - (num - 1) / 2) * (spread / num)
            r_ang = base_ang + ang_off
            r_start = c_i * 0.06
            r_t = max(0.0, min(1.0, (t - r_start) / max(0.01, 1 - r_start)))
            if r_t <= 0:
                continue
            travel = base_dist * 1.1
            cx = int(start_x + math.cos(r_ang) * travel * r_t)
            cy = int(start_y + math.sin(r_ang) * travel * r_t)
            # Trail
            for ti in range(5):
                tt = max(0.0, r_t - ti * 0.06)
                px = int(start_x + math.cos(r_ang) * travel * tt)
                py = int(start_y + math.sin(r_ang) * travel * tt)
                a = _NS_yomigetsu._alpha(180 - ti * 30)
                _NS_yomigetsu._aacircle(surface,
                                        (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                        (px, py), max(1, 4 - ti))
            # Crescent projectile
            cr_r = 10
            for cr_layer, (w, color, wa) in enumerate([
                (3, _NS_yomigetsu.PALETTE["moon_darkest"], 130),
                (2, _NS_yomigetsu.PALETTE["moon_mid"], 200),
                (1, _NS_yomigetsu.PALETTE["moon_hot"], 240),
            ]):
                _NS_yomigetsu._draw_crescent(
                    surface, cx, cy, cr_r, w, color, wa,
                    angle=r_ang + math.pi / 2,
                    arc_span=math.pi,
                )
            _NS_yomigetsu._aacircle(surface, _NS_yomigetsu.PALETTE["moon_hot"],
                                    (cx, cy), 2)
            pygame.draw.rect(surface, _NS_yomigetsu.PALETTE["white"],
                             (cx, cy, 1, 1))
            # Impact
            if r_t > 0.9:
                impact_x = tx + int((c_i - 2) * 10)
                impact_y = ty + int((c_i % 2) * 8)
                _NS_yomigetsu._draw_crescent_impact(
                    surface, impact_x, impact_y, (r_t - 0.9) / 0.1, phase,
                )

    # ============================================================
    # SKILL E — MOON SPIRIT CALAMITY (countless moon blades)
    # ============================================================
    def _draw_moonspirit(surface, boss, x, y, timer, phase):
        """Vertical crescent pattern with many small blades."""
        facing = boss.direction
        duration = 65
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_yomigetsu._target_position(boss, x, y)
        if progress < 0.15:
            return
        t = (progress - 0.15) / 0.85
        # Spawn many crescents in area around target
        num_crescents = 20
        for c_i in range(num_crescents):
            c_seed = (c_i * 0.211) % 1.0
            c_start = c_seed * 0.5
            if t < c_start:
                continue
            c_t = min(1.0, (t - c_start) / max(0.01, 0.6))
            # Position in cone toward target
            cone_off_x = (c_seed - 0.5) * 90
            cone_off_y = ((c_i * 0.377) % 1.0 - 0.5) * 60
            cx = tx + int(cone_off_x)
            cy = ty + int(cone_off_y)
            # Fade in then out
            fade = math.sin(c_t * math.pi)
            a = _NS_yomigetsu._alpha(240 * fade)
            if a <= 0:
                continue
            # Random crescent
            cr_r = 5 + (c_i % 4) * 2
            cr_ang = c_seed * math.pi * 2 + phase * 0.5
            for cr_layer, (w, color, wa) in enumerate([
                (3, _NS_yomigetsu.PALETTE["moon_darkest"], 130),
                (2, _NS_yomigetsu.PALETTE["moon_mid"], 200),
                (1, _NS_yomigetsu.PALETTE["moon_hot"], 240),
            ]):
                _NS_yomigetsu._draw_crescent(
                    surface, cx, cy, cr_r, w, color,
                    _NS_yomigetsu._alpha(wa * fade),
                    angle=cr_ang,
                    arc_span=math.pi * 1.1,
                )
            pygame.draw.rect(surface, (*_NS_yomigetsu.PALETTE["white"], a),
                             (cx, cy, 1, 1))
        # Central big glow
        if t > 0.3:
            gr = int(15 + t * 15)
            ga = _NS_yomigetsu._alpha(180 * (1 - t * 0.3))
            for rr in range(gr, 0, -3):
                ra = _NS_yomigetsu._alpha(ga * (gr - rr) / gr)
                _NS_yomigetsu._aacircle(surface,
                                        (*_NS_yomigetsu.PALETTE["moon_dark"], ra),
                                        (tx, ty), rr)

    # ============================================================
    # SKILL R — PERPETUAL NIGHT (dark realm around boss)
    # ============================================================
    def _draw_perpetualnight_ground(surface, boss, x, y, timer, phase):
        """Dark sphere/void engulfing area."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2))
        if r < 5:
            return
        # Dark realm shadow
        for layer_r in range(r, 5, -6):
            a = _NS_yomigetsu._alpha((r - layer_r + 5) * 3)
            pygame.draw.ellipse(
                surface, (*_NS_yomigetsu.PALETTE["shadow_deep"], a),
                (x - layer_r, y + 40 - layer_r // 3,
                 layer_r * 2, layer_r * 2 // 3),
            )
        pygame.draw.ellipse(
            surface, (*_NS_yomigetsu.PALETTE["moon_darkest"], 200),
            (x - r + 6, y + 40 - r // 3 + 3,
             r * 2 - 12, r * 2 // 3 - 6),
        )

    def _draw_perpetualnight_foreground(surface, boss, x, y, timer, phase):
        """Big dark sphere with moon in center + slicing crescents."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2))
        if r < 10:
            return
        # BLACK MOON sphere around boss
        sphere = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        for rr in range(r, 5, -3):
            a = _NS_yomigetsu._alpha(220 * (r - rr) / r)
            _NS_yomigetsu._aacircle(sphere,
                                    (*_NS_yomigetsu.PALETTE["shadow_deep"], a),
                                    center, rr)
        _NS_yomigetsu._aacircle(sphere,
                                _NS_yomigetsu.PALETTE["shadow"],
                                center, r - 8)
        # Purple corona ring
        for ring_i in range(3):
            ring_r = r - ring_i * 3
            _NS_yomigetsu._aacircle(sphere,
                                    (*_NS_yomigetsu.PALETTE["moon_dark"], 200),
                                    center, ring_r, 2)
            _NS_yomigetsu._aacircle(sphere,
                                    (*_NS_yomigetsu.PALETTE["moon_mid"], 220),
                                    center, ring_r - 1, 1)
        # Orbiting crescents around ring
        for i in range(8):
            orb_ang = phase * 1.5 + i * math.pi / 4
            orb_r = r + 5
            ox = center[0] + int(math.cos(orb_ang) * orb_r)
            oy = center[1] + int(math.sin(orb_ang) * orb_r)
            _NS_yomigetsu._draw_crescent(
                sphere, ox, oy, 5, 2,
                _NS_yomigetsu.PALETTE["moon_hot"], 240,
                angle=orb_ang + math.pi / 2,
            )
        surface.blit(sphere, (x - r - 10, y - r - 10))
        # Slicing crescents inside
        for i in range(6):
            sl_phase = (phase * 0.8 + i * 0.16) % 1.0
            sl_r = int(sl_phase * r)
            sl_ang = i * math.pi / 3 + phase
            sx = x + int(math.cos(sl_ang) * sl_r)
            sy = y + int(math.sin(sl_ang) * sl_r * 0.4)
            a = _NS_yomigetsu._alpha(240 * (1 - sl_phase))
            _NS_yomigetsu._draw_crescent(
                surface, sx, sy, 8, 2,
                _NS_yomigetsu.PALETTE["moon_light"], a,
                angle=sl_ang + math.pi / 2,
            )

    # ============================================================
    # SKILL D — TRANSLUCENT WORLD (ultimate — clones from all directions)
    # ============================================================
    def _draw_translucent_ground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Concentric rings
        for i in range(4):
            r = int(50 + i * 10 + math.sin(phase * 2 + i) * 3)
            a = _NS_yomigetsu._alpha(200 - i * 40)
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                    (x, y + 45), r, 2)
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_mid"], a),
                                    (x, y + 45), r - 2, 1)

    def _draw_translucent_foreground(surface, boss, x, y, timer, phase):
        """Multiple translucent clones striking from all sides."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # 8 translucent afterimages around boss
        num_clones = 8
        for c_i in range(num_clones):
            c_ang = phase * 0.6 + c_i * math.pi / 4
            c_dist = 60 + int(math.sin(phase * 2 + c_i) * 8)
            cx = x + int(math.cos(c_ang) * c_dist)
            cy = y + int(math.sin(c_ang) * c_dist * 0.7)
            # Translucent clone silhouette
            a = _NS_yomigetsu._alpha(160 + math.sin(phase * 3 + c_i) * 50)
            clone_surf = pygame.Surface((60, 90), pygame.SRCALPHA)
            # Simple silhouette body
            _NS_yomigetsu._aacircle(clone_surf,
                                    (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                                    (30, 30), 8)
            pygame.draw.rect(clone_surf,
                             (*_NS_yomigetsu.PALETTE["moon_dark"], a),
                             (22, 35, 16, 25))
            pygame.draw.rect(clone_surf,
                             (*_NS_yomigetsu.PALETTE["moon_darkest"], a),
                             (24, 60, 12, 20))
            # Slashing crescent from clone toward center
            slash_ang = c_ang + math.pi
            slash_x = cx + int(math.cos(slash_ang) * 20)
            slash_y = cy + int(math.sin(slash_ang) * 20)
            surface.blit(clone_surf, (cx - 30, cy - 40))
            # Crescent slash toward center
            _NS_yomigetsu._draw_crescent(
                surface, slash_x, slash_y, 8, 2,
                _NS_yomigetsu.PALETTE["moon_hot"], 240,
                angle=slash_ang,
            )
        # Center convergence flash
        cf_a = _NS_yomigetsu._alpha(150 + math.sin(phase * 5) * 100)
        for r in range(20, 0, -3):
            a = _NS_yomigetsu._alpha(cf_a * (20 - r) / 20)
            _NS_yomigetsu._aacircle(surface,
                                    (*_NS_yomigetsu.PALETTE["moon_hot"], a),
                                    (x, y), r)


# ====================================================================================================
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ====================================================================================================
def draw_kairenji(surface, boss, x, y):
    """Entry point kairenji."""
    return _NS_kairenji.draw_kairenji(surface, boss, x, y)

def draw_karzhul(surface, boss, x, y):
    """Entry point karzhul."""
    return _NS_karzhul.draw_karzhul(surface, boss, x, y)

def draw_xerakkuth(surface, boss, x, y):
    """Entry point xerakkuth."""
    return _NS_xerakkuth.draw_xerakkuth(surface, boss, x, y)

def draw_yomigetsu(surface, boss, x, y):
    """Entry point yomigetsu."""
    return _NS_yomigetsu.draw_yomigetsu(surface, boss, x, y)
