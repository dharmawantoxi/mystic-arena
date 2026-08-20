"""
bosses/level7.py - Semua boss Level 7

Gabungan dari 4 file terpisah:
  - malzareth            (mini boss)
  - akashari             (mini boss)
  - vorenmarr            (mini boss)
  - nyxarath             (TRUE BOSS)

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
# MALZARETH
# ====================================================================
class _NS_malzareth:
    """Namespace malzareth - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Shadow demon body (very dark with cool tone)
        "shadow_pit": (2, 2, 4),
        "shadow_black": (10, 6, 12),
        "shadow_darkest": (22, 14, 22),
        "shadow_dark": (42, 24, 36),
        "shadow_mid": (72, 40, 55),
        "shadow_edge": (110, 60, 75),

        # Magenta/crimson magic (khas Shadow Demon)
        "void_darkest": (35, 5, 20),
        "void_dark": (95, 15, 45),
        "void_mid": (190, 30, 75),
        "void_light": (250, 65, 130),
        "void_hot": (255, 130, 190),
        "void_white": (255, 220, 235),

        # Deeper red accent (chest core, eyes)
        "crimson_dark": (85, 10, 15),
        "crimson_mid": (200, 30, 25),
        "crimson_light": (255, 90, 70),

        # Chain metal (dark iron with dark red tint)
        "chain_darkest": (12, 8, 10),
        "chain_dark": (32, 24, 28),
        "chain_mid": (75, 55, 60),
        "chain_light": (140, 110, 115),
        "chain_shine": (200, 175, 180),

        # Bone/horn (dark bone)
        "bone_darkest": (25, 18, 20),
        "bone_dark": (60, 45, 45),
        "bone_mid": (120, 95, 92),
        "bone_light": (190, 165, 160),

        # Cloak/robe (dark red-black)
        "cloak_darkest": (10, 4, 8),
        "cloak_dark": (25, 10, 18),
        "cloak_mid": (55, 20, 32),
        "cloak_edge": (95, 40, 55),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_malzareth._clamp(color)
        if _NS_malzareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_malzareth._clamp(color)
        if _NS_malzareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_malzareth._clamp(color), points)


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
    def draw_malzareth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_malzareth._detect_moving(boss)
        _NS_malzareth._update_malzareth_attack_anim(boss)
        attacking = (
            getattr(boss, "_mal_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient (behind).
        _NS_malzareth._draw_void_aura(surface, x, y, pulse)
        _NS_malzareth._draw_dark_ground_ring(surface, x, y + 34, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "q":
            _NS_malzareth._draw_disruption_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_malzareth._draw_purge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_malzareth._draw_disillusion_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_malzareth._draw_malzareth_attack(surface, boss, x, y)
        elif moving:
            _NS_malzareth._draw_malzareth_walk(surface, boss, x, y)
        else:
            _NS_malzareth._draw_malzareth_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_malzareth._draw_disruption_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_malzareth._draw_soul_catcher(surface, boss, x, y, skill_timer)
        elif active_skill == "e":
            _NS_malzareth._draw_shadow_poison(surface, boss, x, y, skill_timer)
        elif active_skill == "d":
            _NS_malzareth._draw_purge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_malzareth._draw_disillusion_foreground(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_malzareth_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mal_previous_timer", 0))
        active = bool(getattr(boss, "_mal_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mal_attack_active = True
            boss._mal_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mal_attack_frame = int(
                getattr(boss, "_mal_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._mal_attack_active = False
            boss._mal_attack_frame = 0
            active = False

        boss._mal_previous_timer = timer
        boss._mal_attack_progress = (
            min(1.0, getattr(boss, "_mal_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_mal_last_x"):
            boss._mal_last_x = boss.x
            boss._mal_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mal_last_x)
        dy = abs(boss.y - boss._mal_last_y)
        boss._mal_last_x = boss.x
        boss._mal_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_malzareth_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_malzareth._draw_shadow(surface, x, y + 44)
        _NS_malzareth._draw_void_wisps(surface, x, y + 30, boss.pulse)
        _NS_malzareth._draw_malzareth_body(surface, x, y + bob,
                              boss.direction, boss.pulse, "idle")


    def _draw_malzareth_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_malzareth._draw_shadow(surface, x + sway, y + 44)
        _NS_malzareth._draw_void_wisps(surface, x + sway, y + 30, phase,
                          trail=True, facing=boss.direction)
        _NS_malzareth._draw_malzareth_body(surface, x + sway, y + bob,
                              boss.direction, phase, "walk")


    def _draw_malzareth_attack(surface, boss, x, y):
        progress = getattr(boss, "_mal_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction
        lift = int(math.sin(progress * math.pi) * 2)
        _NS_malzareth._draw_shadow(surface, x + lunge, y + 44)
        _NS_malzareth._draw_void_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_malzareth._draw_malzareth_body(surface, x + lunge, y - lift,
                              boss.direction, boss.pulse, "attack", progress)
        _NS_malzareth._draw_basic_void_projectile(surface, boss, x + lunge, y - lift, progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_malzareth_body(surface, cx, cy, facing, phase, action,
                              attack_progress=0):
        sway = int(math.sin(phase * 0.7) * (2 if action != "idle" else 1))
        if action == "attack":
            sway += int(math.sin(attack_progress * math.pi) * 3) * facing

        # Back shoulder-spikes silhouette.
        _NS_malzareth._draw_shoulder_spikes(surface, cx, cy - 18, facing, phase)

        # Cloak/robe lower body (floating menggantung).
        _NS_malzareth._draw_cloak_lower(surface, cx, cy + 6, facing, phase, action)

        # Torso: hooded with chest core.
        _NS_malzareth._draw_malzareth_torso(surface, cx, cy - 10, sway, facing, phase)

        # Arms + chain-sickles.
        _NS_malzareth._draw_malzareth_arms(surface, cx, cy - 6, facing, phase, action,
                              attack_progress)

        # Head: horned hood.
        _NS_malzareth._draw_malzareth_head(surface, cx, cy - 30, facing, phase)


    def _draw_cloak_lower(surface, cx, cy, facing, phase, action):
        """Cloak menjuntai, dark with void red glow inside."""
        flow1 = math.sin(phase * 0.5) * 3
        flow2 = math.cos(phase * 0.4) * 2
        flow3 = math.sin(phase * 0.7 + 1) * 2

        # Main cloak shape (wider at bottom, flowing).
        main = [
            (cx - 15, cy - 8),
            (cx + 15, cy - 8),
            (cx + 19 + int(flow1), cy + 4),
            (cx + 22, cy + 16),
            (cx + 17, cy + 26),
            (cx + 9 + int(flow3), cy + 30),
            (cx + 2, cy + 32),
            (cx - 2, cy + 32),
            (cx - 9 + int(flow3), cy + 30),
            (cx - 17, cy + 26),
            (cx - 22, cy + 16),
            (cx - 19 - int(flow1), cy + 4),
        ]
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in main])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_darkest"], main)
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_dark"], [
            (cx - 13, cy - 6),
            (cx + 13, cy - 6),
            (cx + 16 + int(flow1), cy + 4),
            (cx + 18, cy + 14),
            (cx + 14, cy + 22),
            (cx + 4, cy + 28),
            (cx - 4, cy + 28),
            (cx - 14, cy + 22),
            (cx - 18, cy + 14),
            (cx - 16 - int(flow1), cy + 4),
        ])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_mid"], [
            (cx - 10, cy - 3),
            (cx + 10, cy - 3),
            (cx + 12, cy + 4),
            (cx + 13, cy + 14),
            (cx + 8, cy + 22),
            (cx - 8, cy + 22),
            (cx - 13, cy + 14),
            (cx - 12, cy + 4),
        ])

        # Central opening reveals magenta-red core (glowing "chest cavity" behind cloak).
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["void_darkest"], [
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 6, cy + 14),
            (cx + 3, cy + 22),
            (cx - 3, cy + 22),
            (cx - 6, cy + 14),
        ])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["void_dark"], [
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 4, cy + 14),
            (cx + 2, cy + 20),
            (cx - 2, cy + 20),
            (cx - 4, cy + 14),
        ])

        # Bright core inside.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_alpha = _NS_malzareth._alpha(200 * pulse)
        _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_light"], core_alpha),
                  (cx, cy + 12), 3)
        _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_hot"], core_alpha),
                  (cx, cy + 12), 2)
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_white"], (cx, cy + 12, 1, 1))

        # Magenta glowing runes/cracks along cloak.
        for i, (x1, y1, x2, y2) in enumerate([
            (-9, 4, -6, 14), (8, 6, 5, 16),
            (-13, 10, -10, 22), (12, 12, 9, 22),
            (-6, 16, -3, 24), (5, 18, 2, 26),
        ]):
            rune_pulse = math.sin(phase * 1.8 + i * 0.5) * 0.3 + 0.7
            rune_alpha = _NS_malzareth._alpha(210 * rune_pulse)
            pygame.draw.line(surface, (*_NS_malzareth.PALETTE["void_dark"], rune_alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 2)
            pygame.draw.line(surface, (*_NS_malzareth.PALETTE["void_light"], rune_alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 1)

        # Tattered cloak bottom hem.
        for i, ox in enumerate((-12, -6, 0, 6, 12)):
            hem_phase = math.sin(phase * 0.8 + i * 0.4) * 2
            hem_y = cy + 28 + int(hem_phase)
            pygame.draw.line(surface, _NS_malzareth.PALETTE["cloak_darkest"],
                             (cx + ox, cy + 24), (cx + ox, hem_y + 2), 3)
            pygame.draw.line(surface, _NS_malzareth.PALETTE["cloak_mid"],
                             (cx + ox, cy + 24), (cx + ox, hem_y), 1)
            # Small void glow at hem tip.
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_dark"], (cx + ox, hem_y, 1, 1))
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (cx + ox, hem_y, 1, 1))


    def _draw_malzareth_torso(surface, cx, cy, sway, facing, phase):
        # Hooded torso silhouette.
        body = [
            (cx - 13, cy - 6),
            (cx + 13, cy - 6),
            (cx + 14 + sway, cy + 6),
            (cx + 10, cy + 16),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 10, cy + 16),
            (cx - 14 - sway, cy + 6),
        ]
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in body])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_darkest"], body)
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_dark"], [
            (cx - 11, cy - 4),
            (cx + 11, cy - 4),
            (cx + 12 + sway, cy + 6),
            (cx + 8, cy + 14),
            (cx - 8, cy + 14),
            (cx - 12 - sway, cy + 6),
        ])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_mid"], [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 9, cy + 6),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 9, cy + 6),
        ])

        # Chest core cavity - big glowing magenta wound.
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_black"], [
            (cx - 5, cy - 1),
            (cx + 5, cy - 1),
            (cx + 4, cy + 10),
            (cx - 4, cy + 10),
        ])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["void_darkest"], [
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 3, cy + 9),
            (cx - 3, cy + 9),
        ])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["void_dark"], [
            (cx - 3, cy + 1),
            (cx + 3, cy + 1),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ])

        # Bright chest core orb (heart).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_r = int(2 * pulse) + 2
        for r in range(core_r * 2, 0, -1):
            alpha = _NS_malzareth._alpha(90 * (core_r * 2 - r) / (core_r * 2))
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_mid"], alpha), (cx, cy + 4), r)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_dark"], (cx, cy + 4), core_r)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_light"], (cx, cy + 4), max(1, core_r - 1))
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_hot"], (cx, cy + 4), max(1, core_r - 2))
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_white"], (cx, cy + 4, 1, 1))

        # Twisted rib-like bone lines (dark) framing the core.
        for side in (-1, 1):
            for ry_off in (0, 3, 6):
                ry = cy + 1 + ry_off
                pygame.draw.line(surface, _NS_malzareth.PALETTE["bone_dark"],
                                 (cx + side * 5, ry), (cx + side * 2, ry + 1), 2)
                pygame.draw.line(surface, _NS_malzareth.PALETTE["bone_mid"],
                                 (cx + side * 4, ry), (cx + side * 2, ry + 1), 1)

        # Shoulders - dark bulbs with jagged tops.
        for side in (-1, 1):
            sx = cx + side * 11
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_deep"], (sx + 1, cy + 1), 8)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["cloak_darkest"], (sx, cy - 1), 7)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["cloak_dark"], (sx - side, cy - 2), 5)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["cloak_mid"], (sx - side * 2, cy - 3), 3)
            # Shoulder rune glow.
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_light"],
                             (sx - side * 2, cy - 3, 1, 1))


    def _draw_shoulder_spikes(surface, cx, cy, facing, phase):
        """Massive curved spikes flanking the shoulders (khas Shadow Demon)."""
        # Big curved shoulder spikes on both sides.
        for side in (-1, 1):
            # Multiple layered spikes.
            for i, (base_off, tip_ox, tip_oy, size) in enumerate([
                (side * 11, side * 14, -14, 6),   # main big spike
                (side * 14, side * 20, -8, 5),    # outer
                (side * 8, side * 8, -18, 4),     # inner tall
            ]):
                wave = math.sin(phase * 0.4 + i + side) * 1
                bx = cx + base_off
                by = cy + 6
                tx = cx + tip_ox + int(wave)
                ty = cy + tip_oy
                perp_x = (ty - by) / max(1, math.hypot(tx - bx, ty - by))
                perp_y = -(tx - bx) / max(1, math.hypot(tx - bx, ty - by))

                base_a = (bx + int(perp_x * size / 2),
                          by + int(perp_y * size / 2))
                base_b = (bx - int(perp_x * size / 2),
                          by - int(perp_y * size / 2))

                # Dark spike layered.
                _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_deep"], [
                    (tx + 1, ty + 1),
                    (base_a[0] + 1, base_a[1] + 1),
                    (base_b[0] + 1, base_b[1] + 1),
                ])
                _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_darkest"],
                      [(tx, ty), base_a, base_b])
                _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_dark"], [
                    (tx, ty),
                    ((base_a[0] + base_b[0]) // 2, (base_a[1] + base_b[1]) // 2),
                    (base_b[0], base_b[1]),
                ])
                # Red-magenta tip.
                _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_dark"], (tx, ty), 1)
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (tx, ty, 1, 1))


    def _draw_malzareth_head(surface, cx, cy, facing, phase):
        """Head with hood + massive curved horns."""
        # Hood shape (covering head).
        hood = [
            (cx - 10, cy - 2),
            (cx - 9, cy - 8),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 9, cy - 8),
            (cx + 10, cy - 2),
            (cx + 8, cy + 4),
            (cx + 4, cy + 8),
            (cx - 4, cy + 8),
            (cx - 8, cy + 4),
        ]
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in hood])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_darkest"], hood)
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["cloak_dark"], [
            (cx - 8, cy - 1),
            (cx - 7, cy - 7),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 7, cy - 7),
            (cx + 8, cy - 1),
            (cx + 6, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 6, cy + 3),
        ])

        # Inner shadow face (deep black under hood).
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_pit"], [
            (cx - 5, cy - 5),
            (cx + 5, cy - 5),
            (cx + 4, cy + 4),
            (cx - 4, cy + 4),
        ])

        # HORN CROWN (curving back-up spikes).
        _NS_malzareth._draw_demon_horns(surface, cx, cy - 8, phase)

        # GLOWING RED EYES (bright, angry).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 2):
            # Deep socket.
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["shadow_pit"],
                             (eye_x - 1, cy - 3, 4, 3))
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["crimson_dark"],
                             (eye_x, cy - 3, 3, 2))
            eye_alpha = _NS_malzareth._alpha(240 * pulse)
            pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["crimson_mid"], eye_alpha),
                             (eye_x, cy - 3, 3, 2))
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["crimson_light"], (eye_x + 1, cy - 2, 1, 1))
            # Bright center.
            pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_white"], eye_alpha),
                             (eye_x + 1, cy - 2, 1, 1))

        # Fanged smile (small sharp teeth).
        mouth_y = cy + 3
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["shadow_pit"],
                         (cx - 5, mouth_y, 11, 3))
        for tx in range(-4, 5, 2):
            pygame.draw.line(surface, _NS_malzareth.PALETTE["bone_light"],
                             (cx + tx, mouth_y),
                             (cx + tx, mouth_y + 2), 1)
        # Inner red glow.
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["crimson_dark"], (cx - 2, mouth_y + 1, 4, 1))

        # Hood side flaps.
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_malzareth.PALETTE["cloak_darkest"],
                             (cx + side * 9, cy - 2), (cx + side * 11, cy + 6), 2)
            pygame.draw.line(surface, _NS_malzareth.PALETTE["cloak_dark"],
                             (cx + side * 8, cy - 1), (cx + side * 10, cy + 5), 1)


    def _draw_demon_horns(surface, cx, cy, phase):
        """Curving demonic horns coming out of hood."""
        # Central pair (biggest, curving up-back).
        for side in (-1, 1):
            base_x = cx + side * 4
            base_y = cy + 2
            mid_x = cx + side * 10
            mid_y = cy - 4
            tip_x = cx + side * 14
            tip_y = cy - 13

            prev = (base_x, base_y)
            for step in range(1, 7):
                t = step / 6
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * tip_y)
                width = max(1, 6 - step)
                _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), width + 1)
                _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["shadow_black"], prev, (bx, by), width)
                _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_darkest"], prev, (bx, by),
                        max(1, width - 2))
                if step > 3:
                    _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_dark"], prev, (bx, by), 1)
                prev = (bx, by)
            # Horn tip sharp.
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["bone_dark"], prev, 1)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["bone_light"], prev, 1)
            # Red glow at tip.
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (prev[0], prev[1] - 1, 1, 1))

        # Inner smaller horns.
        for side in (-1, 1):
            base_x = cx + side * 2
            base_y = cy - 1
            tip_x = cx + side * 4
            tip_y = cy - 8
            _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["shadow_black"],
                    (base_x, base_y), (tip_x, tip_y), 3)
            _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_darkest"],
                    (base_x, base_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_light"], (tip_x, tip_y, 1, 1))


    def _draw_malzareth_arms(surface, cx, cy, facing, phase, action,
                              attack_progress):
        # Off-hand (with chain-sickle hanging).
        off_dir = -facing
        off_sway = math.sin(phase * 0.7) * 2
        off_x = cx + off_dir * 15
        off_y = cy + 8 + int(off_sway)
        _NS_malzareth._draw_arm(surface, cx + off_dir * 10, cy - 2,
                  off_x, off_y, phase)
        _NS_malzareth._draw_claw_hand(surface, off_x, off_y + 3, off_dir, phase)
        # Chain-sickle hanging (idle sway).
        _NS_malzareth._draw_chain_sickle(surface, off_x, off_y + 5, off_dir,
                           phase, action="idle", swing_progress=0)

        # Main hand (weapon side).
        weapon_x = cx + facing * 10
        weapon_y = cy - 2

        if action == "attack":
            p = max(0.0, min(1.0, attack_progress))
            # 3-phase: wind-up (raise chain) → sling forward → recovery.
            if p < 0.28:
                # Wind-up: arm back.
                t = p / 0.28
                t = t * t * (3 - 2 * t)
                angle = math.pi * 0.9 - t * 0.2
                distance = 14 + int(t * 6)
            elif p < 0.55:
                # Sling forward.
                t = (p - 0.28) / 0.27
                t = 1 - (1 - t) ** 3
                angle = math.pi * 0.7 - t * math.pi * 1.10
                distance = 20 + int(t * 12)
            else:
                # Recovery.
                t = (p - 0.55) / 0.45
                t = t * t * (3 - 2 * t)
                angle = -math.pi * 0.40 + t * math.pi * 0.85
                distance = 32 - int(t * 14)

            hand_x = weapon_x + int(math.cos(angle) * distance) * facing
            hand_y = weapon_y + int(math.sin(angle) * distance)
            elbow_x = (weapon_x + hand_x) // 2 + 2 * facing
            elbow_y = (weapon_y + hand_y) // 2 - 3

            _NS_malzareth._draw_arm(surface, weapon_x, weapon_y, elbow_x, elbow_y, phase)
            _NS_malzareth._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, phase)
            _NS_malzareth._draw_claw_hand(surface, hand_x, hand_y + 2, facing, phase,
                            charged=True, charge_amount=min(1.0, p * 2))
            # Chain-sickle swings.
            _NS_malzareth._draw_chain_sickle(surface, hand_x, hand_y + 4, facing, phase,
                              action="swing", swing_progress=p)
        else:
            idle_sway = math.sin(phase * 0.5) * 0.08
            hand_x = weapon_x + facing * 12
            hand_y = weapon_y + 8 + int(idle_sway * 8)
            _NS_malzareth._draw_arm(surface, weapon_x, weapon_y, hand_x, hand_y, phase)
            _NS_malzareth._draw_claw_hand(surface, hand_x, hand_y + 2, facing, phase)
            _NS_malzareth._draw_chain_sickle(surface, hand_x, hand_y + 4, facing, phase,
                              action="idle", swing_progress=0)


    def _draw_arm(surface, x1, y1, x2, y2, phase):
        """Dark demon arm (thin, sinister)."""
        _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_darkest"], (x1, y1), (x2, y2), 6)
        _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_dark"], (x1, y1), (x2, y2), 4)
        _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_mid"], (x1 - 1, y1), (x2 - 1, y2), 2)
        _NS_malzareth._aaline(surface, _NS_malzareth.PALETTE["cloak_edge"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_claw_hand(surface, x, y, direction, phase, charged=False,
                         charge_amount=0):
        """Claw hand — bone claws."""
        # Palm.
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_deep"], (x, y), 4)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_black"], (x, y - 1), 3)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["cloak_darkest"], (x - 1, y - 1), 2)

        # 4 sharp claws.
        for i, ang in enumerate((0.2, 0.5, 0.85, 1.2)):
            length = 4 + (i % 2)
            cx_tip = x + int(math.cos(ang) * length) * direction
            cy_tip = y + int(math.sin(ang) * length)
            pygame.draw.line(surface, _NS_malzareth.PALETTE["bone_darkest"], (x, y),
                             (cx_tip, cy_tip), 2)
            pygame.draw.line(surface, _NS_malzareth.PALETTE["bone_mid"], (x, y),
                             (cx_tip, cy_tip), 1)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["bone_light"], (cx_tip, cy_tip), 1)

        if charged:
            # Void charge orb in palm.
            charge_r = int(3 + charge_amount * 7)
            for r in range(charge_r + 3, 0, -1):
                alpha = _NS_malzareth._alpha(90 * (charge_r + 3 - r) / (charge_r + 3))
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_dark"], alpha), (x, y), r)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_darkest"], (x, y), charge_r)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_dark"], (x, y), max(1, charge_r - 1))
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_mid"], (x, y), max(1, charge_r - 3))
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_light"], (x, y), max(1, charge_r - 5))
            if charge_r > 5:
                _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_hot"], (x, y), 1)
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_white"], (x, y, 1, 1))

            # Spark particles.
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                sx = x + int(math.cos(angle) * (charge_r + 3))
                sy = y + int(math.sin(angle) * (charge_r + 3))
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (sx, sy, 1, 1))


    def _draw_chain_sickle(surface, hx, hy, direction, phase,
                            action="idle", swing_progress=0):
        """Chain with sickle-blade at end (signature Shadow Demon weapon)."""
        if action == "idle":
            # Chain hangs down with slight sway.
            sway = math.sin(phase * 0.5) * 3
            length = 18
            end_x = hx + int(sway)
            end_y = hy + length
            # Small orbit motion.
            end_x += int(math.sin(phase * 0.7) * 2)

            # Draw chain links.
            _NS_malzareth._draw_chain_segment(surface, hx, hy, end_x, end_y, phase, 5)
            # Sickle blade at end.
            _NS_malzareth._draw_sickle_blade(surface, end_x, end_y, direction, phase, 0.5)
        else:
            # Swing: chain whips forward and back based on progress.
            p = swing_progress
            if p < 0.28:
                # Chain trailing behind.
                trail_angle = math.pi * 0.75
                length = 20
            elif p < 0.55:
                # Whip forward (chain extended).
                t = (p - 0.28) / 0.27
                trail_angle = math.pi * 0.75 - t * math.pi * 1.1
                length = 22 + int(t * 8)
            else:
                # Recovery, chain trails behind.
                t = (p - 0.55) / 0.45
                trail_angle = -math.pi * 0.35 + t * math.pi * 0.7
                length = 30 - int(t * 12)

            end_x = hx + int(math.cos(trail_angle) * length) * direction
            end_y = hy + int(math.sin(trail_angle) * length)

            _NS_malzareth._draw_chain_segment(surface, hx, hy, end_x, end_y, phase, 6)
            _NS_malzareth._draw_sickle_blade(surface, end_x, end_y, direction, phase, p)


    def _draw_chain_segment(surface, x1, y1, x2, y2, phase, num_links):
        """Draw metal chain from (x1,y1) to (x2,y2) with links."""
        dx = x2 - x1
        dy = y2 - y1
        dist = max(1, math.hypot(dx, dy))
        ux = dx / dist
        uy = dy / dist

        for i in range(num_links):
            t = (i + 0.5) / num_links
            lx = int(x1 + dx * t)
            ly = int(y1 + dy * t)
            # Alternate link orientation.
            if i % 2 == 0:
                # Vertical link.
                _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["chain_darkest"], (lx, ly), 2)
                _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["chain_dark"], (lx, ly - 1), 2)
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["chain_light"], (lx - 1, ly - 1, 2, 1))
            else:
                # Horizontal link.
                _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["chain_darkest"], (lx, ly), 2)
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["chain_mid"], (lx - 2, ly, 4, 2))
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["chain_light"], (lx - 1, ly, 2, 1))

        # Connecting line (thin dark).
        pygame.draw.line(surface, _NS_malzareth.PALETTE["chain_darkest"], (x1, y1), (x2, y2), 1)


    def _draw_sickle_blade(surface, cx, cy, direction, phase, activity):
        """Curved sickle blade with glowing edge."""
        # Handle base (metal cap).
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["chain_darkest"], (cx, cy), 3)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["chain_mid"], (cx - 1, cy - 1), 2)

        # Curved blade — arc shape.
        # 5 points forming a sickle.
        blade_points = []
        for i in range(6):
            t = i / 5
            angle = math.pi * 0.2 + t * math.pi * 0.9
            r = 8
            bx = cx + int(math.cos(angle) * r) * direction
            by = cy + int(math.sin(angle) * r)
            blade_points.append((bx, by))

        # Build sickle poly (blade widens then narrows).
        outer_points = []
        inner_points = []
        for i, (bx, by) in enumerate(blade_points):
            t = i / 5
            thickness = 3 * math.sin(t * math.pi) + 1
            # Perpendicular offset outward.
            if i < len(blade_points) - 1:
                nbx, nby = blade_points[i + 1]
                dx_ = nbx - bx
                dy_ = nby - by
                dist = max(1, math.hypot(dx_, dy_))
                perp_x = -dy_ / dist
                perp_y = dx_ / dist
            else:
                perp_x, perp_y = 0, 1
            outer = (bx + int(perp_x * thickness), by + int(perp_y * thickness))
            inner = (bx - int(perp_x * thickness * 0.3),
                     by - int(perp_y * thickness * 0.3))
            outer_points.append(outer)
            inner_points.append(inner)

        # Full blade shape.
        poly_points = outer_points + list(reversed(inner_points))
        # Shadow.
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in poly_points])
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["chain_darkest"], poly_points)
        _NS_malzareth._poly(surface, _NS_malzareth.PALETTE["chain_dark"],
              [(p[0], p[1]) for p in outer_points[1:-1] +
               list(reversed([(x + int(direction * 0.5),
                               y) for x, y in inner_points[1:-1]]))]
              if len(outer_points) > 3 else poly_points)

        # Cutting edge highlight (bright).
        for i in range(len(outer_points) - 1):
            pygame.draw.line(surface, _NS_malzareth.PALETTE["chain_light"],
                             outer_points[i], outer_points[i + 1], 1)

        # Glowing magenta rune along blade (if activity > 0.3).
        if activity > 0.3:
            alpha = _NS_malzareth._alpha(220 * min(1.0, (activity - 0.3) * 3))
            for i in range(len(outer_points) - 1):
                mid_x = (outer_points[i][0] + inner_points[i][0]) // 2
                mid_y = (outer_points[i][1] + inner_points[i][1]) // 2
                next_mid_x = (outer_points[i + 1][0] + inner_points[i + 1][0]) // 2
                next_mid_y = (outer_points[i + 1][1] + inner_points[i + 1][1]) // 2
                pygame.draw.line(surface, (*_NS_malzareth.PALETTE["void_light"], alpha),
                                 (mid_x, mid_y), (next_mid_x, next_mid_y), 1)

        # Sharp tip.
        tip = blade_points[-1]
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["chain_shine"], tip, 1)


    # ============================================================
    # BASIC ATTACK — VOID PROJECTILE (ranged with swing)
    # ============================================================
    def _draw_basic_void_projectile(surface, boss, x, y, progress):
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_malzareth._target_position(boss, x, y)

        t = (progress - 0.55) / 0.45
        start_x = x + facing * 34
        start_y = y - 2
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (shadow + magenta).
        for i in range(6):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_malzareth._alpha(220 - i * 35)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["shadow_black"], alpha), (px, py), 6 - i)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_darkest"], alpha), (px, py), 4 - i // 2)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_dark"], alpha), (px, py), 3 - i // 2)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_light"], alpha), (px, py),
                      max(1, 2 - i // 2))

        # Bolt head.
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_black"], (bx, by), 5)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_dark"], (bx, by), 4)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_mid"], (bx, by), 3)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_light"], (bx, by), 2)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.85:
            splash_t = (t - 0.85) / 0.15
            radius = int(5 + splash_t * 16)
            alpha = _NS_malzareth._alpha(230 * (1 - splash_t))
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_light"], alpha), (tx, ty), radius, 2)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_hot"], alpha), (tx, ty),
                      max(1, radius - 6), 1)
            for i in range(6):
                angle = i * math.pi / 3
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.6)
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (ex, ey, 2, 2))


    # ============================================================
    # FLOATING VOID WISPS (below body)
    # ============================================================
    def _draw_void_wisps(surface, cx, cy, phase, trail=False,
                          facing=1, intense=False):
        strength = 1.5 if intense else 1.0

        # Dark mist with magenta inner glow.
        mist = pygame.Surface((120, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = _NS_malzareth._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_malzareth.PALETTE["shadow_black"], alpha),
                    (60 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        # Magenta inner glow.
        for radius in range(20, 3, -3):
            alpha = _NS_malzareth._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_malzareth.PALETTE["void_dark"], alpha),
                    (60 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Shadow tendrils rising.
        for i, offset in enumerate((-20, -8, 6, 18, -14, 14, -2)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_malzareth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["shadow_black"], alpha), (sx, sy), 5)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["shadow_darkest"], alpha), (sx, sy - 1), 3)
            pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_dark"], alpha),
                             (sx, sy - 2, 2, 2))
            pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_hot"], alpha),
                             (sx, sy - 3, 1, 1))

        # Magenta embers floating up.
        for i in range(6):
            ember_t = (phase * 0.7 + i * 0.2) % 1.0
            ex = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(ember_t * 22)
            alpha = _NS_malzareth._alpha(240 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_dark"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Swirling dark motes with magenta cores.
        for i in range(8):
            angle = phase * 0.7 + i * math.pi * 2 / 8
            radius = 26 + int(math.sin(phase + i * 0.6) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * 9)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_darkest"], (sx, sy), 2)
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_mid"], (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_malzareth._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["shadow_black"], alpha),
                          (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_dark"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 4, 90, 10))
        # Magenta inner shadow.
        pygame.draw.ellipse(shadow, (60, 15, 40, 110), (12, 6, 76, 6))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_void_aura(surface, x, y, phase):
        """Dark aura with magenta inner glow."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((160, 130), pygame.SRCALPHA)
        for radius in range(70, 5, -5):
            alpha = _NS_malzareth._alpha((70 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_malzareth._aacircle(aura, (*_NS_malzareth.PALETTE["shadow_black"], alpha), (80, 65), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_malzareth._alpha((45 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_malzareth._aacircle(aura, (*_NS_malzareth.PALETTE["void_dark"], alpha), (80, 65), radius)
        surface.blit(aura, (x - 80, y - 65))

        # Floating magenta embers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 28 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (sx, sy, 1, 1))


    def _draw_dark_ground_ring(surface, x, y, phase, skill):
        """Dark ring with magenta rune lines."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((120, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_malzareth.PALETTE["shadow_black"], 190),
                            (5, 12, 110, 20), 3)
        pygame.draw.ellipse(ring, (*_NS_malzareth.PALETTE["void_darkest"], 200),
                            (12, 14, 96, 16), 2)
        pygame.draw.ellipse(ring, (*_NS_malzareth.PALETTE["void_dark"], 220),
                            (22, 16, 76, 12), 1)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 60 + int(math.cos(angle) * 32)
            y1 = 21 + int(math.sin(angle) * 6)
            x2 = 60 + int(math.cos(angle) * 50)
            y2 = 21 + int(math.sin(angle) * 9)
            pygame.draw.line(ring, (*_NS_malzareth.PALETTE["void_light"], 210),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_malzareth.PALETTE["void_hot"], _NS_malzareth._alpha(120 * pulse)),
                                (15, 8, 90, 30), 1)
        surface.blit(ring, (x - 60, y - 21))


    # ============================================================
    # SKILL: Q - DISRUPTION (void portal that removes target)
    # ============================================================
    def _draw_disruption_ground(surface, boss, x, y, timer, pulse):
        """Portal opens on ground at target."""
        tx, ty = _NS_malzareth._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_r = 30

        # Growing then shrinking portal ring.
        if progress < 0.5:
            r = int(max_r * progress * 2)
        else:
            r = int(max_r * (1 - (progress - 0.5) * 2) * 0.8 + max_r * 0.4)

        if r > 2:
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["shadow_black"], 220), (tx, ty), r + 3, 3)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_darkest"], 240), (tx, ty), r, 3)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_dark"], 220), (tx, ty), r - 3, 2)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_mid"], 210), (tx, ty), r - 6, 1)


    def _draw_disruption_foreground(surface, boss, x, y, timer, phase):
        """Portal fill + swirling particles + target consumed."""
        tx, ty = _NS_malzareth._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_r = 30

        if progress < 0.5:
            r = int(max_r * progress * 2)
        else:
            r = int(max_r * (1 - (progress - 0.5) * 2) * 0.8 + max_r * 0.4)

        if r > 2:
            # Portal interior (dark abyss).
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_pit"], (tx, ty), max(1, r - 8))

            # Swirling void particles inside portal.
            for i in range(10):
                spin_angle = phase * 3 + i * math.pi / 5
                spin_r = int(r * 0.3 + math.sin(phase * 2 + i) * 4)
                sx = tx + int(math.cos(spin_angle) * spin_r)
                sy = ty + int(math.sin(spin_angle) * spin_r)
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_light"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_malzareth.PALETTE["void_hot"], (sx, sy, 1, 1))

            # Vertical light beams from portal.
            for i in range(4):
                beam_angle = i * math.pi / 2 + phase * 0.5
                bx1 = tx + int(math.cos(beam_angle) * (r - 5))
                by1 = ty + int(math.sin(beam_angle) * (r - 5))
                bx2 = tx + int(math.cos(beam_angle) * (r + 4))
                by2 = ty + int(math.sin(beam_angle) * (r + 4))
                pygame.draw.line(surface, _NS_malzareth.PALETTE["void_hot"], (bx1, by1),
                                 (bx2, by2), 2)


    # ============================================================
    # SKILL: W - SOUL CATCHER (red skull projectile)
    # ============================================================
    def _draw_soul_catcher(surface, boss, x, y, timer):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_malzareth._target_position(boss, x, y)

        if progress < 0.25:
            # Charging skull at hand.
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 4
            skull_size = int(3 + t * 5)
            for r in range(skull_size + 3, 0, -1):
                alpha = _NS_malzareth._alpha(180 * (skull_size + 3 - r) / (skull_size + 3))
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_dark"], alpha),
                          (hand_x, hand_y), r)
            _NS_malzareth._draw_soul_skull_projectile(surface, hand_x, hand_y, skull_size, t * 5)
        else:
            # Skull travels to target.
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 24
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Trail (dark red ectoplasm).
            for i in range(6):
                trail_t = max(0.0, t - i * 0.07)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_malzareth._alpha(220 - i * 35)
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["shadow_black"], alpha),
                          (px, py), 6 - i)
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_dark"], alpha),
                          (px, py), 4 - i // 2)
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_mid"], alpha),
                          (px, py), 3 - i // 2)

            # Skull projectile.
            _NS_malzareth._draw_soul_skull_projectile(surface, bx, by, 6, t * 8)

            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(6 + st * 20)
                alpha = _NS_malzareth._alpha(230 * (1 - st))
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_mid"], alpha), (tx, ty),
                          radius, 3)
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_light"], alpha), (tx, ty),
                          max(1, radius - 5), 2)


    def _draw_soul_skull_projectile(surface, cx, cy, size, rotation):
        """Red glowing skull with eye sockets."""
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["shadow_black"], (cx, cy), size)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["crimson_dark"], (cx, cy - 1), size - 1)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["crimson_mid"], (cx - 1, cy - 1), size - 2)
        _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["crimson_light"], (cx - 1, cy - 2), max(1, size - 3))
        # Eye sockets.
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["shadow_pit"], (cx - 2, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["shadow_pit"], (cx + 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["crimson_light"], (cx - 2, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_malzareth.PALETTE["crimson_light"], (cx + 2, cy - 1, 1, 1))
        # Jaw.
        pygame.draw.line(surface, _NS_malzareth.PALETTE["shadow_pit"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)


    # ============================================================
    # SKILL: E - SHADOW POISON (purple projectile)
    # ============================================================
    def _draw_shadow_poison(surface, boss, x, y, timer):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_malzareth._target_position(boss, x, y)

        # Similar to basic but PURPLE toxic effect.
        if progress < 0.20:
            # Charge.
            t = progress / 0.20
            hand_x = x + facing * 22
            hand_y = y - 4
            cr = int(3 + t * 7)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_malzareth._alpha(180 * (cr + 3 - r) / (cr + 3))
                # Use a purple mix.
                _NS_malzareth._aacircle(surface, (140, 40, 200, alpha), (hand_x, hand_y), r)
            _NS_malzareth._aacircle(surface, (200, 100, 240), (hand_x, hand_y), 3)
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["void_white"], (hand_x, hand_y), 1)
        else:
            t = (progress - 0.20) / 0.80
            start_x = x + facing * 24
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Purple trail.
            for i in range(7):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_malzareth._alpha(220 - i * 30)
                _NS_malzareth._aacircle(surface, (60, 15, 90, alpha), (px, py), 6 - i)
                _NS_malzareth._aacircle(surface, (110, 30, 160, alpha), (px, py), 4 - i // 2)
                _NS_malzareth._aacircle(surface, (180, 90, 230, alpha), (px, py),
                          max(1, 3 - i // 2))
                # Purple sparks around trail.
                if i < 3:
                    spark_x = px + int(math.sin(t * 8 + i) * 4)
                    spark_y = py + int(math.cos(t * 8 + i) * 4)
                    pygame.draw.rect(surface, (220, 140, 255, alpha),
                                     (spark_x, spark_y, 1, 1))

            # Projectile head.
            _NS_malzareth._aacircle(surface, (30, 5, 55), (bx, by), 5)
            _NS_malzareth._aacircle(surface, (100, 20, 150), (bx, by), 4)
            _NS_malzareth._aacircle(surface, (180, 80, 230), (bx, by), 2)
            _NS_malzareth._aacircle(surface, (240, 180, 255), (bx, by), 1)

            # Impact splash.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(6 + st * 18)
                alpha = _NS_malzareth._alpha(230 * (1 - st))
                _NS_malzareth._aacircle(surface, (180, 80, 230, alpha), (tx, ty), radius, 3)
                _NS_malzareth._aacircle(surface, (240, 180, 255, alpha), (tx, ty),
                          max(1, radius - 5), 2)
                for i in range(6):
                    angle = i * math.pi / 3
                    ex = tx + int(math.cos(angle) * radius)
                    ey = ty + int(math.sin(angle) * radius * 0.6)
                    pygame.draw.rect(surface, (220, 140, 255, alpha), (ex, ey, 2, 2))


    # ============================================================
    # SKILL: D - DEMONIC PURGE (red skull chain barrage)
    # ============================================================
    def _draw_purge_ground(surface, boss, x, y, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_malzareth._target_position(boss, x, y)
        # Ring under target.
        for i in range(3):
            r = int(15 + i * 8 + progress * 10)
            alpha = _NS_malzareth._alpha(180 - i * 40)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_dark"], alpha), (tx, ty), r, 2)


    def _draw_purge_foreground(surface, boss, x, y, timer, phase):
        """Multiple red skulls chase target with orbit trails."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_malzareth._target_position(boss, x, y)

        # 5 skulls orbiting target at increasing rotation.
        for i in range(5):
            skull_t = max(0.0, min(1.0, (progress - i * 0.08) * 2))
            if skull_t <= 0:
                continue
            angle = phase * 3 + i * math.pi * 2 / 5
            orbit_r = int(30 * (1 - skull_t * 0.6))  # spiraling inward
            sx = tx + int(math.cos(angle) * orbit_r)
            sy = ty + int(math.sin(angle) * orbit_r * 0.6)

            # Orbit trail lines.
            for j in range(4):
                trail_angle = angle - j * 0.2
                tx_ = tx + int(math.cos(trail_angle) * orbit_r)
                ty_ = ty + int(math.sin(trail_angle) * orbit_r * 0.6)
                alpha = _NS_malzareth._alpha(180 - j * 40)
                pygame.draw.line(surface, (*_NS_malzareth.PALETTE["crimson_mid"], alpha),
                                 (tx_, ty_), (sx, sy), 1)

            # Small skull.
            _NS_malzareth._draw_soul_skull_projectile(surface, sx, sy, 4, phase + i)


    # ============================================================
    # SKILL: R - DISILLUSION (bright red pulse + illusion silhouettes)
    # ============================================================
    def _draw_disillusion_ground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big expanding ring.
        for i in range(3):
            r = int(20 + i * 20 + progress * 40)
            alpha = _NS_malzareth._alpha(180 - i * 50)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_dark"], alpha),
                      (x, y + 34), r, 3)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_mid"], alpha),
                      (x, y + 34), r, 1)


    def _draw_disillusion_foreground(surface, boss, x, y, timer, phase):
        """Bright red pulse + demon illusion silhouettes surrounding."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Central pulse core.
        if progress < 0.4:
            core_r = int(15 + progress * 40)
            core_alpha = _NS_malzareth._alpha(220 * (1 - progress * 1.8))
            for r in range(core_r, 0, -2):
                a = _NS_malzareth._alpha(core_alpha * (core_r - r) / core_r)
                _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_dark"], a), (x, y), r)
            _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["crimson_mid"], core_alpha), (x, y),
                      max(1, core_r // 3))
            _NS_malzareth._aacircle(surface, _NS_malzareth.PALETTE["crimson_light"], (x, y),
                      max(1, core_r // 5))

        # Illusion silhouettes materialize in a ring.
        num_illusions = 6
        for i in range(num_illusions):
            angle = i * math.pi * 2 / num_illusions + phase * 0.2
            radius = 50 + int(math.sin(phase + i) * 4)
            ix = x + int(math.cos(angle) * radius)
            iy = y + int(math.sin(angle) * radius * 0.5)
            appear_t = max(0.0, min(1.0, (progress - 0.2 - i * 0.06) * 2))
            if appear_t <= 0:
                continue
            _NS_malzareth._draw_demon_illusion(surface, ix, iy, appear_t, phase + i)


    def _draw_demon_illusion(surface, cx, cy, appear_t, phase):
        """Silhouette copy of Malzareth."""
        alpha = _NS_malzareth._alpha(220 * appear_t)
        # Cloaked demon shape.
        shape = [
            (cx - 6, cy - 24),
            (cx - 4, cy - 30),
            (cx + 4, cy - 30),
            (cx + 6, cy - 24),
            (cx + 8, cy - 12),
            (cx + 10, cy),
            (cx + 8, cy + 14),
            (cx + 4, cy + 22),
            (cx - 4, cy + 22),
            (cx - 8, cy + 14),
            (cx - 10, cy),
            (cx - 8, cy - 12),
        ]
        _NS_malzareth._poly(surface, (*_NS_malzareth.PALETTE["shadow_black"], alpha), shape)
        _NS_malzareth._poly(surface, (*_NS_malzareth.PALETTE["cloak_darkest"], _NS_malzareth._alpha(alpha * 0.85)), [
            (cx - 5, cy - 22),
            (cx - 3, cy - 28),
            (cx + 3, cy - 28),
            (cx + 5, cy - 22),
            (cx + 7, cy - 10),
            (cx + 8, cy + 12),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 8, cy + 12),
            (cx - 7, cy - 10),
        ])

        # Horns.
        for side in (-1, 1):
            pygame.draw.line(surface, (*_NS_malzareth.PALETTE["shadow_black"], alpha),
                             (cx + side * 4, cy - 28),
                             (cx + side * 8, cy - 34), 2)

        # Red eyes.
        pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["crimson_light"], alpha),
                         (cx - 2, cy - 22, 1, 1))
        pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["crimson_light"], alpha),
                         (cx + 1, cy - 22, 1, 1))

        # Chest core.
        _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_light"], alpha), (cx, cy - 5), 2)
        _NS_malzareth._aacircle(surface, (*_NS_malzareth.PALETTE["void_hot"], alpha), (cx, cy - 5), 1)

        # Sparkles around illusion.
        for i in range(3):
            s_angle = phase * 2 + i * math.pi * 2 / 3
            sx = cx + int(math.cos(s_angle) * 10)
            sy = cy + int(math.sin(s_angle) * 15)
            pygame.draw.rect(surface, (*_NS_malzareth.PALETTE["void_hot"], alpha), (sx, sy, 2, 2))


# ====================================================================
# AKASHARI
# ====================================================================
class _NS_akashari:
    """Namespace akashari - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Skin (blue-purple demon skin)
        "skin_darkest": (28, 22, 45),
        "skin_dark": (55, 45, 78),
        "skin_mid": (95, 82, 115),
        "skin_light": (145, 128, 155),
        "skin_high": (185, 168, 185),

        # Wings (dark red-black membrane)
        "wing_darkest": (12, 4, 8),
        "wing_dark": (35, 10, 18),
        "wing_mid": (75, 20, 30),
        "wing_edge": (135, 35, 45),
        "wing_bone": (30, 15, 20),

        # Hair (dark red-purple)
        "hair_darkest": (20, 8, 15),
        "hair_dark": (50, 18, 30),
        "hair_mid": (90, 35, 50),
        "hair_edge": (140, 60, 75),

        # Horns (dark curved)
        "horn_darkest": (18, 10, 15),
        "horn_dark": (45, 25, 30),
        "horn_mid": (85, 55, 55),
        "horn_light": (150, 115, 110),

        # Armor (dark leather + gold)
        "armor_darkest": (8, 4, 10),
        "armor_dark": (25, 12, 22),
        "armor_mid": (55, 28, 42),
        "armor_edge": (95, 50, 65),

        # Gold accents
        "gold_dark": (95, 62, 18),
        "gold_mid": (185, 135, 40),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 170),

        # Pain magic (khas Queen of Pain — pink-red-crimson)
        "pain_darkest": (35, 5, 20),
        "pain_dark": (100, 12, 40),
        "pain_mid": (215, 30, 85),
        "pain_light": (255, 85, 145),
        "pain_hot": (255, 165, 200),
        "pain_white": (255, 230, 240),

        # Eyes (bright glowing red)
        "eye_glow": (255, 80, 90),
        "eye_hot": (255, 200, 200),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_akashari._clamp(color)
        if _NS_akashari.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_akashari._clamp(color)
        if _NS_akashari.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_akashari._clamp(color), points)


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
    def draw_akashari(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_akashari._detect_moving(boss)
        _NS_akashari._update_akashari_attack_anim(boss)
        attacking = (
            getattr(boss, "_aka_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_akashari._draw_pain_aura(surface, x, y, pulse)
        _NS_akashari._draw_pain_ground_ring(surface, x, y + 34, pulse, active_skill)

        if active_skill == "e":
            _NS_akashari._draw_scream_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akashari._draw_sonic_wave_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_akashari._draw_akashari_attack(surface, boss, x, y)
        elif moving:
            _NS_akashari._draw_akashari_walk(surface, boss, x, y)
        else:
            _NS_akashari._draw_akashari_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_akashari._draw_shadow_strike(surface, boss, x, y, skill_timer)
        elif active_skill == "w":
            _NS_akashari._draw_bloink(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_akashari._draw_scream_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akashari._draw_sonic_wave_foreground(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_akashari_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aka_previous_timer", 0))
        active = bool(getattr(boss, "_aka_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aka_attack_active = True
            boss._aka_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._aka_attack_frame = int(
                getattr(boss, "_aka_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._aka_attack_active = False
            boss._aka_attack_frame = 0
            active = False

        boss._aka_previous_timer = timer
        boss._aka_attack_progress = (
            min(1.0, getattr(boss, "_aka_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_aka_last_x"):
            boss._aka_last_x = boss.x
            boss._aka_last_y = boss.y
            return False
        dx = abs(boss.x - boss._aka_last_x)
        dy = abs(boss.y - boss._aka_last_y)
        boss._aka_last_x = boss.x
        boss._aka_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_akashari_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        _NS_akashari._draw_shadow(surface, x, y + 44)
        _NS_akashari._draw_pain_wisps(surface, x, y + 30, boss.pulse)
        _NS_akashari._draw_akashari_body(surface, x, y + bob,
                            boss.direction, boss.pulse, "idle")


    def _draw_akashari_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_akashari._draw_shadow(surface, x + sway, y + 44)
        _NS_akashari._draw_pain_wisps(surface, x + sway, y + 30, phase,
                         trail=True, facing=boss.direction)
        _NS_akashari._draw_akashari_body(surface, x + sway, y + bob,
                            boss.direction, phase, "walk")


    def _draw_akashari_attack(surface, boss, x, y):
        progress = getattr(boss, "_aka_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction
        lift = int(math.sin(progress * math.pi) * 3)
        _NS_akashari._draw_shadow(surface, x + lunge, y + 44)
        _NS_akashari._draw_pain_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_akashari._draw_akashari_body(surface, x + lunge, y - lift,
                            boss.direction, boss.pulse, "attack", progress)
        _NS_akashari._draw_basic_pain_bolt(surface, boss, x + lunge, y - lift, progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_akashari_body(surface, cx, cy, facing, phase, action,
                             attack_progress=0):
        sway = int(math.sin(phase * 0.7) * (2 if action != "idle" else 1))
        if action == "attack":
            sway += int(math.sin(attack_progress * math.pi) * 3) * facing

        # Wings behind (biggest silhouette).
        wing_flap = math.sin(phase * 0.9) * 0.15
        if action == "walk":
            wing_flap = math.sin(phase * 1.4) * 0.25
        elif action == "attack":
            wing_flap += math.sin(attack_progress * math.pi) * 0.2
        _NS_akashari._draw_bat_wings(surface, cx, cy - 18, wing_flap, phase)

        # Long-flowing hair behind body.
        _NS_akashari._draw_flowing_hair(surface, cx, cy - 22, facing, phase)

        # Lower body (hips + tail, no legs — floating).
        _NS_akashari._draw_lower_body(surface, cx, cy + 6, facing, phase, action)

        # Torso: slim feminine with corset armor.
        _NS_akashari._draw_akashari_torso(surface, cx, cy - 10, sway, facing, phase)

        # Arms with claw hands.
        _NS_akashari._draw_akashari_arms(surface, cx, cy - 8, facing, phase, action,
                           attack_progress)

        # Head with horns.
        _NS_akashari._draw_akashari_head(surface, cx, cy - 30, facing, phase)


    def _draw_bat_wings(surface, cx, cy, flap, phase):
        """Twin bat-like membrane wings dengan 3 finger struts each."""
        for side in (-1, 1):
            # Wing extends outward with flap animation.
            spread = 1.0 - abs(flap) * 0.5

            # Root of wing (attached to back).
            root_x = cx + side * 6
            root_y = cy + 4

            # Finger tips (3 struts extending outward-up).
            finger1_x = cx + side * int(28 * spread)
            finger1_y = cy - int(18 - flap * 6)
            finger2_x = cx + side * int(32 * spread)
            finger2_y = cy - int(6 + flap * 3)
            finger3_x = cx + side * int(28 * spread)
            finger3_y = cy + int(8 - flap * 4)

            # Membrane polygon (wing shape).
            wing_poly = [
                (root_x, root_y - 4),      # top attach
                (finger1_x, finger1_y),    # top finger tip
                (finger2_x, finger2_y),    # middle tip
                (finger3_x, finger3_y),    # bottom tip
                (root_x + side * 2, root_y + 8),  # bottom attach
            ]
            # Shadow layer.
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["shadow_deep"],
                  [(px + 2, py + 2) for px, py in wing_poly])
            # Membrane layers.
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["wing_darkest"], wing_poly)
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["wing_dark"], [
                (root_x + side, root_y - 3),
                (finger1_x - side, finger1_y + 1),
                (finger2_x - side, finger2_y),
                (finger3_x - side, finger3_y - 1),
                (root_x + side * 2, root_y + 6),
            ])
            # Inner membrane (mid tone).
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["wing_mid"], [
                (root_x + side * 2, root_y - 2),
                (finger1_x - side * 3, finger1_y + 3),
                (finger2_x - side * 3, finger2_y),
                (finger3_x - side * 3, finger3_y - 2),
                (root_x + side * 3, root_y + 4),
            ])

            # Finger bones (dark lines from root to each tip).
            for fx, fy in [(finger1_x, finger1_y), (finger2_x, finger2_y),
                            (finger3_x, finger3_y)]:
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["wing_bone"], (root_x, root_y),
                        (fx, fy), 2)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["horn_dark"], (root_x, root_y),
                        (fx, fy), 1)
                # Claw at tip.
                _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["horn_dark"], (fx, fy), 2)
                pygame.draw.rect(surface, _NS_akashari.PALETTE["horn_light"], (fx, fy, 1, 1))

            # Wing edge highlight (red glow along top).
            pygame.draw.line(surface, _NS_akashari.PALETTE["wing_edge"],
                             (root_x, root_y - 3), (finger1_x, finger1_y), 1)


    def _draw_flowing_hair(surface, cx, cy, facing, phase):
        """Long wavy hair flowing behind head."""
        flow = math.sin(phase * 0.5) * 3
        flow2 = math.cos(phase * 0.4) * 2

        # Hair strands cascading.
        for i, (base_x, cascade_x, tip_y) in enumerate([
            (-6, -12 + int(flow), 8),
            (-3, -8 + int(flow2), 12),
            (0, 0 + int(flow), 14),
            (3, 8 + int(flow2), 12),
            (6, 12 + int(flow), 8),
        ]):
            # Draw as curved bezier.
            prev = (cx + base_x, cy)
            for step in range(1, 5):
                t = step / 4
                bx = int((1 - t) ** 2 * (cx + base_x)
                         + 2 * (1 - t) * t * (cx + cascade_x)
                         + t ** 2 * (cx + cascade_x - 2 + int(flow * 0.5)))
                by = int((1 - t) ** 2 * cy + 2 * (1 - t) * t * (cy + tip_y / 2)
                         + t ** 2 * (cy + tip_y))
                width = max(1, 4 - step)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), width + 1)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["hair_darkest"], prev, (bx, by), width)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["hair_dark"], prev, (bx, by),
                        max(1, width - 1))
                if step > 1:
                    _NS_akashari._aaline(surface, _NS_akashari.PALETTE["hair_mid"], prev, (bx, by), 1)
                prev = (bx, by)


    def _draw_lower_body(surface, cx, cy, facing, phase, action):
        """Slim feminine hips with flowing tail-like drape."""
        flow1 = math.sin(phase * 0.6) * 3
        flow2 = math.cos(phase * 0.5) * 2
        flow3 = math.sin(phase * 0.7 + 1) * 2

        # Slim hip/thigh shape (armored).
        hip = [
            (cx - 10, cy - 8),
            (cx + 10, cy - 8),
            (cx + 12 + int(flow1), cy + 2),
            (cx + 10, cy + 12),
            (cx + 6, cy + 20),
            (cx - 6, cy + 20),
            (cx - 10, cy + 12),
            (cx - 12 - int(flow1), cy + 2),
        ]
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in hip])
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_darkest"], hip)
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_dark"], [
            (cx - 8, cy - 6),
            (cx + 8, cy - 6),
            (cx + 10 + int(flow1), cy + 2),
            (cx + 8, cy + 12),
            (cx + 4, cy + 18),
            (cx - 4, cy + 18),
            (cx - 8, cy + 12),
            (cx - 10 - int(flow1), cy + 2),
        ])
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_mid"], [
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
            (cx + 6, cy + 2),
            (cx + 4, cy + 10),
            (cx - 4, cy + 10),
            (cx - 6, cy + 2),
        ])

        # Gold belt band at top of hips.
        pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_dark"], (cx - 11, cy - 8, 22, 3))
        pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_mid"], (cx - 10, cy - 8, 20, 2))
        # Central gold buckle with red gem.
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["gold_dark"], (cx, cy - 6), 3)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["gold_mid"], (cx, cy - 7), 2)
        pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (cx, cy - 6, 1, 1))

        # Skin exposed at inner thighs (blue-purple).
        for side in (-1, 1):
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_dark"], (cx + side * 3, cy + 8), 2)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_mid"], (cx + side * 3, cy + 7), 1)

        # Tail-like drape flowing behind (armored strips).
        for i, (drape_x, drape_y) in enumerate([
            (-3, 22), (0, 24), (3, 22),
        ]):
            drape_flow = int(math.sin(phase * 0.7 + i * 0.3) * 2)
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_darkest"], [
                (cx + drape_x - 2, cy + drape_y),
                (cx + drape_x + 2, cy + drape_y),
                (cx + drape_x + 1 + drape_flow, cy + drape_y + 8),
                (cx + drape_x - 1 + drape_flow, cy + drape_y + 8),
            ])
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_dark"], [
                (cx + drape_x - 1, cy + drape_y + 1),
                (cx + drape_x + 1, cy + drape_y + 1),
                (cx + drape_x + drape_flow, cy + drape_y + 7),
                (cx + drape_x + drape_flow, cy + drape_y + 7),
            ])
            # Gold tip.
            pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_dark"],
                             (cx + drape_x + drape_flow, cy + drape_y + 6, 2, 2))
            pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_light"],
                             (cx + drape_x + drape_flow, cy + drape_y + 7, 1, 1))


    def _draw_akashari_torso(surface, cx, cy, sway, facing, phase):
        """Slim feminine torso with corset."""
        # Torso silhouette.
        body = [
            (cx - 8, cy - 6),
            (cx + 8, cy - 6),
            (cx + 9 + sway, cy + 4),
            (cx + 8, cy + 12),
            (cx + 4, cy + 18),
            (cx - 4, cy + 18),
            (cx - 8, cy + 12),
            (cx - 9 - sway, cy + 4),
        ]
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in body])
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_darkest"], body)
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_dark"], [
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 7 + sway, cy + 4),
            (cx + 6, cy + 10),
            (cx + 3, cy + 16),
            (cx - 3, cy + 16),
            (cx - 6, cy + 10),
            (cx - 7 - sway, cy + 4),
        ])

        # Cleavage / decolletage skin exposed (upper chest).
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["skin_dark"], [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["skin_mid"], [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])
        # Skin V neckline.
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["skin_light"], [
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx, cy + 1),
        ])

        # Corset lacing (crisscross lines down center).
        for i in range(4):
            ly = cy + 4 + i * 3
            pygame.draw.line(surface, _NS_akashari.PALETTE["gold_mid"],
                             (cx - 3, ly), (cx + 3, ly + 1), 1)
            pygame.draw.line(surface, _NS_akashari.PALETTE["gold_mid"],
                             (cx + 3, ly), (cx - 3, ly + 1), 1)

        # Central chest gem (red — signature Queen of Pain).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_akashari._alpha(230 * pulse)
        gem_x, gem_y = cx, cy + 2
        # Setting.
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["gold_dark"], [
            (gem_x - 3, gem_y - 2),
            (gem_x, gem_y - 4),
            (gem_x + 3, gem_y - 2),
            (gem_x, gem_y + 2),
        ])
        _NS_akashari._poly(surface, _NS_akashari.PALETTE["gold_mid"], [
            (gem_x - 2, gem_y - 2),
            (gem_x, gem_y - 3),
            (gem_x + 2, gem_y - 2),
            (gem_x, gem_y + 1),
        ])
        # Red gem.
        _NS_akashari._poly(surface, (*_NS_akashari.PALETTE["pain_dark"], gem_alpha), [
            (gem_x - 1, gem_y - 2),
            (gem_x, gem_y - 3),
            (gem_x + 1, gem_y - 2),
            (gem_x, gem_y),
        ])
        pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (gem_x, gem_y - 2, 1, 1))

        # Shoulders — small pauldrons with spikes.
        for side in (-1, 1):
            sx = cx + side * 8
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["shadow_deep"], (sx + 1, cy - 3), 5)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["armor_darkest"], (sx, cy - 4), 4)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["armor_dark"], (sx - side, cy - 5), 3)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["armor_mid"], (sx - side * 2, cy - 5), 2)
            # Pauldron spike (curved outward-up).
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_darkest"], [
                (sx + side * 3, cy - 5),
                (sx + side * 7, cy - 12),
                (sx + side * 5, cy - 3),
            ])
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["armor_dark"], [
                (sx + side * 3, cy - 5),
                (sx + side * 6, cy - 11),
                (sx + side * 4, cy - 3),
            ])
            # Gold tip.
            pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_light"], (sx + side * 6, cy - 11, 1, 1))


    def _draw_akashari_arms(surface, cx, cy, facing, phase, action,
                             attack_progress):
        # Off-hand (elegant, exposed with gauntlet).
        off_dir = -facing
        off_sway = math.sin(phase * 0.7) * 2
        if action == "attack":
            # Raise off-hand for dramatic pose.
            p = attack_progress
            off_lift = int(math.sin(p * math.pi) * 8)
            off_x = cx + off_dir * 12
            off_y = cy - 2 - off_lift + int(off_sway)
        else:
            off_x = cx + off_dir * 14
            off_y = cy + 6 + int(off_sway)
        _NS_akashari._draw_arm(surface, cx + off_dir * 8, cy - 2,
                  off_x, off_y, phase)
        _NS_akashari._draw_claw_hand(surface, off_x, off_y + 2, off_dir, phase)

        # Main hand (casting hand).
        weapon_x = cx + facing * 8
        weapon_y = cy - 2

        if action == "attack":
            p = max(0.0, min(1.0, attack_progress))
            # 3-phase: gather pain → sling forward with graceful arc → recovery.
            if p < 0.28:
                # Gather back.
                t = p / 0.28
                t = t * t * (3 - 2 * t)
                angle = math.pi * 0.85 - t * 0.15
                distance = 14 + int(t * 6)
            elif p < 0.55:
                # Sling forward with elegant sweep.
                t = (p - 0.28) / 0.27
                t = 1 - (1 - t) ** 3
                angle = math.pi * 0.70 - t * math.pi * 1.05
                distance = 20 + int(t * 10)
            else:
                # Recovery.
                t = (p - 0.55) / 0.45
                t = t * t * (3 - 2 * t)
                angle = -math.pi * 0.35 + t * math.pi * 0.75
                distance = 30 - int(t * 12)

            hand_x = weapon_x + int(math.cos(angle) * distance) * facing
            hand_y = weapon_y + int(math.sin(angle) * distance)
            elbow_x = (weapon_x + hand_x) // 2 + 2 * facing
            elbow_y = (weapon_y + hand_y) // 2 - 3

            _NS_akashari._draw_arm(surface, weapon_x, weapon_y, elbow_x, elbow_y, phase)
            _NS_akashari._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, phase)
            _NS_akashari._draw_claw_hand(surface, hand_x, hand_y + 2, facing, phase,
                            charged=True, charge_amount=min(1.0, p * 2))
        else:
            # Idle: hand relaxed at side.
            idle_sway = math.sin(phase * 0.5) * 0.08
            hand_x = weapon_x + facing * 10
            hand_y = weapon_y + 8 + int(idle_sway * 8)
            _NS_akashari._draw_arm(surface, weapon_x, weapon_y, hand_x, hand_y, phase)
            _NS_akashari._draw_claw_hand(surface, hand_x, hand_y + 2, facing, phase)


    def _draw_arm(surface, x1, y1, x2, y2, phase):
        """Slim demon arm — blue-purple skin exposed."""
        # Shadow.
        _NS_akashari._aaline(surface, _NS_akashari.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 6)
        # Skin (mostly bare with elbow spikes).
        _NS_akashari._aaline(surface, _NS_akashari.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 5)
        _NS_akashari._aaline(surface, _NS_akashari.PALETTE["skin_dark"], (x1, y1), (x2, y2), 3)
        _NS_akashari._aaline(surface, _NS_akashari.PALETTE["skin_mid"], (x1 - 1, y1), (x2 - 1, y2), 2)
        _NS_akashari._aaline(surface, _NS_akashari.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Gold bracelet at wrist.
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["gold_dark"], (x2, y2), 3)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["gold_mid"], (x2 - 1, y2 - 1), 2)
        pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_light"], (x2 - 1, y2 - 2, 1, 1))


    def _draw_claw_hand(surface, x, y, direction, phase, charged=False,
                         charge_amount=0):
        """Elegant claw hand."""
        # Palm.
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["shadow_deep"], (x, y), 3)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_darkest"], (x, y - 1), 3)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_mid"], (x - 1, y - 1), 2)

        # 4 slender claws.
        for i, ang in enumerate((0.2, 0.5, 0.85, 1.15)):
            length = 4 + (i % 2)
            cx_tip = x + int(math.cos(ang) * length) * direction
            cy_tip = y + int(math.sin(ang) * length)
            pygame.draw.line(surface, _NS_akashari.PALETTE["horn_dark"], (x, y),
                             (cx_tip, cy_tip), 2)
            pygame.draw.line(surface, _NS_akashari.PALETTE["horn_mid"], (x, y),
                             (cx_tip, cy_tip), 1)
            # Sharp glossy tip.
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["horn_light"], (cx_tip, cy_tip), 1)

        if charged:
            # Pain magic gathering in palm.
            charge_r = int(3 + charge_amount * 8)
            for r in range(charge_r + 3, 0, -1):
                alpha = _NS_akashari._alpha(90 * (charge_r + 3 - r) / (charge_r + 3))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (x, y), r)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_darkest"], (x, y), charge_r)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_dark"], (x, y), max(1, charge_r - 1))
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_mid"], (x, y), max(1, charge_r - 3))
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_light"], (x, y), max(1, charge_r - 5))
            if charge_r > 5:
                _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_hot"], (x, y), 1)
                pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_white"], (x, y, 1, 1))

            # Spark particles.
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                sx = x + int(math.cos(angle) * (charge_r + 3))
                sy = y + int(math.sin(angle) * (charge_r + 3))
                pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (sx, sy, 1, 1))


    def _draw_akashari_head(surface, cx, cy, facing, phase):
        """Feminine demon head dengan horn crown & long hair."""
        # Neck.
        pygame.draw.rect(surface, _NS_akashari.PALETTE["skin_dark"], (cx - 2, cy + 8, 5, 5))
        pygame.draw.rect(surface, _NS_akashari.PALETTE["skin_mid"], (cx - 2, cy + 8, 3, 4))

        # Long hair BEHIND face (base blob).
        for r in range(11, 6, -1):
            color = [_NS_akashari.PALETTE["hair_darkest"], _NS_akashari.PALETTE["hair_dark"],
                     _NS_akashari.PALETTE["hair_mid"]][max(0, (11 - r) // 2)]
            _NS_akashari._aacircle(surface, color, (cx, cy - 1), r)

        # Face (oval, slim feminine).
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["shadow_deep"], (cx + 1, cy + 1), 8)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_darkest"], (cx, cy), 7)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_dark"], (cx - 1, cy - 1), 6)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_mid"], (cx - 1, cy - 2), 4)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["skin_light"], (cx - 2, cy - 3), 2)

        # HORN CROWN (curving big horns like Queen of Pain).
        _NS_akashari._draw_akashari_horns(surface, cx, cy - 6, phase)

        # Small horn tiara/crown band on forehead.
        pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_dark"], (cx - 5, cy - 6, 11, 2))
        pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_mid"], (cx - 4, cy - 6, 9, 1))
        # Center gem.
        pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (cx, cy - 5, 1, 1))

        # GLOWING RED EYES (bright, seductive).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 2):
            pygame.draw.rect(surface, _NS_akashari.PALETTE["shadow_deep"],
                             (eye_x - 1, cy - 2, 3, 2))
            pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_darkest"],
                             (eye_x, cy - 2, 2, 1))
            eye_alpha = _NS_akashari._alpha(255 * pulse)
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["eye_glow"], eye_alpha),
                             (eye_x, cy - 2, 2, 1))
            pygame.draw.rect(surface, _NS_akashari.PALETTE["eye_hot"], (eye_x, cy - 2, 1, 1))

        # Elegant nose.
        pygame.draw.line(surface, _NS_akashari.PALETTE["skin_darkest"],
                         (cx, cy), (cx, cy + 2), 1)

        # Full lips (red).
        pygame.draw.line(surface, _NS_akashari.PALETTE["pain_dark"],
                         (cx - 2, cy + 4), (cx + 2, cy + 4), 2)
        pygame.draw.line(surface, _NS_akashari.PALETTE["pain_mid"],
                         (cx - 1, cy + 4), (cx + 1, cy + 4), 1)

        # Cheek shadow.
        pygame.draw.line(surface, _NS_akashari.PALETTE["skin_darkest"],
                         (cx - 5, cy + 1), (cx - 4, cy + 4), 1)
        pygame.draw.line(surface, _NS_akashari.PALETTE["skin_darkest"],
                         (cx + 5, cy + 1), (cx + 4, cy + 4), 1)

        # Front hair strands framing face.
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_akashari.PALETTE["hair_dark"],
                             (cx + side * 6, cy - 4),
                             (cx + side * 8, cy + 4), 2)
            pygame.draw.line(surface, _NS_akashari.PALETTE["hair_mid"],
                             (cx + side * 6, cy - 4),
                             (cx + side * 7, cy + 3), 1)


    def _draw_akashari_horns(surface, cx, cy, phase):
        """Massive curved horns coming from forehead (khas Queen of Pain)."""
        # Pair of main horns (curving up and back).
        for side in (-1, 1):
            # Base at forehead.
            base_x = cx + side * 3
            base_y = cy + 2
            # Curl up then out.
            mid_x = cx + side * 7
            mid_y = cy - 6
            tip_x = cx + side * 12
            tip_y = cy - 14

            prev = (base_x, base_y)
            for step in range(1, 7):
                t = step / 6
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * tip_y)
                width = max(1, 5 - step)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), width + 1)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["horn_darkest"], prev, (bx, by), width)
                _NS_akashari._aaline(surface, _NS_akashari.PALETTE["horn_dark"], prev, (bx, by),
                        max(1, width - 1))
                if step > 2:
                    _NS_akashari._aaline(surface, _NS_akashari.PALETTE["horn_mid"], prev, (bx, by), 1)
                prev = (bx, by)
            # Sharp tip.
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["horn_darkest"], prev, 2)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["horn_light"], prev, 1)
            # Gold cap at tip.
            pygame.draw.rect(surface, _NS_akashari.PALETTE["gold_light"],
                             (prev[0], prev[1] - 1, 1, 1))


    # ============================================================
    # BASIC ATTACK — PAIN BOLT (ranged with claw swing)
    # ============================================================
    def _draw_basic_pain_bolt(surface, boss, x, y, progress):
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_akashari._target_position(boss, x, y)

        t = (progress - 0.55) / 0.45
        start_x = x + facing * 34
        start_y = y - 2
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (pink-red pain magic).
        for i in range(6):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_akashari._alpha(220 - i * 35)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_darkest"], alpha), (px, py), 6 - i)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (px, py), 4 - i // 2)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha), (px, py), 3 - i // 2)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_light"], alpha), (px, py),
                      max(1, 2 - i // 2))

        # Bolt head (bright pain orb).
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["shadow_deep"], (bx, by), 5)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_dark"], (bx, by), 4)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_mid"], (bx, by), 3)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_light"], (bx, by), 2)
        _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.85:
            splash_t = (t - 0.85) / 0.15
            radius = int(5 + splash_t * 16)
            alpha = _NS_akashari._alpha(230 * (1 - splash_t))
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_light"], alpha), (tx, ty), radius, 2)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha), (tx, ty),
                      max(1, radius - 6), 1)
            for i in range(6):
                angle = i * math.pi / 3
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.6)
                pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (ex, ey, 2, 2))


    # ============================================================
    # FLOATING PAIN WISPS (below body)
    # ============================================================
    def _draw_pain_wisps(surface, cx, cy, phase, trail=False,
                          facing=1, intense=False):
        strength = 1.5 if intense else 1.0

        # Dark mist with pink-red inner glow.
        mist = pygame.Surface((120, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = _NS_akashari._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_akashari.PALETTE["armor_darkest"], alpha),
                    (60 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -3):
            alpha = _NS_akashari._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                    (60 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Pink pain tendrils rising.
        for i, offset in enumerate((-20, -8, 6, 18, -14, 14, -2)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_akashari._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_darkest"], alpha), (sx, sy), 5)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (sx, sy - 1), 3)
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha),
                             (sx, sy - 2, 2, 2))
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha),
                             (sx, sy - 3, 1, 1))

        # Pink hearts/embers floating up (subtle Queen of Pain motif).
        for i in range(6):
            ember_t = (phase * 0.7 + i * 0.2) % 1.0
            ex = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(ember_t * 22)
            alpha = _NS_akashari._alpha(240 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Swirling dark motes with pink cores.
        for i in range(8):
            angle = phase * 0.7 + i * math.pi * 2 / 8
            radius = 26 + int(math.sin(phase + i * 0.6) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * 9)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["armor_darkest"], (sx, sy), 2)
            pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_mid"], (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_akashari._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["armor_darkest"], alpha),
                          (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 4, 90, 10))
        pygame.draw.ellipse(shadow, (95, 20, 45, 110), (12, 6, 76, 6))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_pain_aura(surface, x, y, phase):
        """Dark aura with pink-red inner glow."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((160, 130), pygame.SRCALPHA)
        for radius in range(70, 5, -5):
            alpha = _NS_akashari._alpha((70 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_akashari._aacircle(aura, (*_NS_akashari.PALETTE["armor_darkest"], alpha), (80, 65), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_akashari._alpha((45 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_akashari._aacircle(aura, (*_NS_akashari.PALETTE["pain_dark"], alpha), (80, 65), radius)
        surface.blit(aura, (x - 80, y - 65))

        # Floating pink embers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 28 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (sx, sy, 1, 1))


    def _draw_pain_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((120, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_akashari.PALETTE["armor_darkest"], 190),
                            (5, 12, 110, 20), 3)
        pygame.draw.ellipse(ring, (*_NS_akashari.PALETTE["pain_darkest"], 200),
                            (12, 14, 96, 16), 2)
        pygame.draw.ellipse(ring, (*_NS_akashari.PALETTE["pain_dark"], 220),
                            (22, 16, 76, 12), 1)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 60 + int(math.cos(angle) * 32)
            y1 = 21 + int(math.sin(angle) * 6)
            x2 = 60 + int(math.cos(angle) * 50)
            y2 = 21 + int(math.sin(angle) * 9)
            pygame.draw.line(ring, (*_NS_akashari.PALETTE["pain_light"], 210),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_akashari.PALETTE["pain_hot"], _NS_akashari._alpha(120 * pulse)),
                                (15, 8, 90, 30), 1)
        surface.blit(ring, (x - 60, y - 21))


    # ============================================================
    # SKILL: Q - SHADOW STRIKE (piercing projectile with dark trail)
    # ============================================================
    def _draw_shadow_strike(surface, boss, x, y, timer):
        """Pink-red piercing bolt dengan trailing dark shadow."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akashari._target_position(boss, x, y)

        if progress < 0.20:
            # Charge glow at hand.
            t = progress / 0.20
            hand_x = x + facing * 24
            hand_y = y - 4
            cr = int(3 + t * 8)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_akashari._alpha(180 * (cr + 3 - r) / (cr + 3))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha),
                          (hand_x, hand_y), r)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_hot"], (hand_x, hand_y), 3)
            pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_white"], (hand_x, hand_y, 1, 1))
        else:
            # Elongated shadow-strike projectile with dark trail behind.
            t = (progress - 0.20) / 0.80
            start_x = x + facing * 26
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Elongated dark shadow trail (behind projectile).
            dx = tx - start_x
            dy = ty - start_y
            dist = max(1, math.hypot(dx, dy))
            ux = dx / dist
            uy = dy / dist

            # Long streak trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + dx * trail_t)
                py = int(start_y + dy * trail_t)
                alpha = _NS_akashari._alpha(200 - i * 15)
                if alpha <= 0:
                    continue
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["armor_darkest"], alpha),
                          (px, py), max(1, 7 - i // 2))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_darkest"], alpha),
                          (px, py), max(1, 5 - i // 2))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                          (px, py), max(1, 3 - i // 3))
                if i < 6:
                    _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_light"], alpha),
                              (px, py), max(1, 2 - i // 3))

            # Bright bolt head (elongated shape).
            # Draw head as elongated ellipse in direction of motion.
            perp_x = -uy
            perp_y = ux
            head_len = 8
            head_tip_x = bx + int(ux * head_len)
            head_tip_y = by + int(uy * head_len)
            head_back_x = bx - int(ux * 3)
            head_back_y = by - int(uy * 3)

            # Diamond bolt head.
            left = (bx + int(perp_x * 3), by + int(perp_y * 3))
            right = (bx - int(perp_x * 3), by - int(perp_y * 3))
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["shadow_deep"], [
                (head_tip_x + 1, head_tip_y + 1),
                (left[0] + 1, left[1] + 1),
                (head_back_x + 1, head_back_y + 1),
                (right[0] + 1, right[1] + 1),
            ])
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["pain_darkest"], [
                (head_tip_x, head_tip_y), left, (head_back_x, head_back_y), right,
            ])
            _NS_akashari._poly(surface, _NS_akashari.PALETTE["pain_mid"], [
                (head_tip_x, head_tip_y),
                (bx + int(perp_x * 2), by + int(perp_y * 2)),
                (head_back_x, head_back_y),
                (bx - int(perp_x * 2), by - int(perp_y * 2)),
            ])
            # Bright center streak.
            _NS_akashari._aaline(surface, _NS_akashari.PALETTE["pain_hot"], (head_back_x, head_back_y),
                    (head_tip_x, head_tip_y), 2)
            _NS_akashari._aaline(surface, _NS_akashari.PALETTE["pain_white"], (head_back_x, head_back_y),
                    (head_tip_x, head_tip_y), 1)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_white"], (head_tip_x, head_tip_y), 1)

            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(6 + st * 18)
                alpha = _NS_akashari._alpha(230 * (1 - st))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_light"], alpha), (tx, ty),
                          radius, 3)
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha), (tx, ty),
                          max(1, radius - 5), 2)
                for i in range(8):
                    angle = i * math.pi / 4
                    ex = tx + int(math.cos(angle) * radius)
                    ey = ty + int(math.sin(angle) * radius * 0.6)
                    pygame.draw.rect(surface, _NS_akashari.PALETTE["pain_hot"], (ex, ey, 2, 2))


    # ============================================================
    # SKILL: W - BLOINK (heart projectile — teleport marker)
    # ============================================================
    def _draw_bloink(surface, boss, x, y, timer, phase):
        """Heart-shaped projectile with sparkle trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akashari._target_position(boss, x, y)

        if progress < 0.20:
            t = progress / 0.20
            hand_x = x + facing * 24
            hand_y = y - 4
            cr = int(3 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_akashari._alpha(180 * (cr + 3 - r) / (cr + 3))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_light"], alpha),
                          (hand_x, hand_y), r)
            # Small heart.
            _NS_akashari._draw_heart(surface, hand_x, hand_y, int(2 + t * 3), 255)
        else:
            t = (progress - 0.20) / 0.80
            start_x = x + facing * 26
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Sparkle trail (pink).
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                if trail_t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_akashari._alpha(230 - i * 25)
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (px, py), 3 - i // 3)
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha), (px, py), 2 - i // 3)
                # Random sparkles.
                sp_x = px + int(math.sin(t * 8 + i) * 4)
                sp_y = py + int(math.cos(t * 8 + i) * 4)
                pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_white"], alpha),
                                 (sp_x, sp_y, 1, 1))

            # Heart projectile with pulse.
            pulse = math.sin(phase * 5) * 0.25 + 1.0
            heart_size = int(6 * pulse)
            # Outer glow.
            for r in range(heart_size + 4, 0, -1):
                alpha = _NS_akashari._alpha(120 * (heart_size + 4 - r) / (heart_size + 4))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (bx, by), r)
            _NS_akashari._draw_heart(surface, bx, by, heart_size, 255)

            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(6 + st * 18)
                alpha = _NS_akashari._alpha(240 * (1 - st))
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha), (tx, ty),
                          radius, 3)
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_white"], alpha), (tx, ty),
                          max(1, radius - 5), 2)
                # Heart burst.
                _NS_akashari._draw_heart(surface, tx, ty, 5, alpha)


    def _draw_heart(surface, cx, cy, size, alpha):
        """Draw pink-red heart shape."""
        if size < 2:
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha),
                             (cx, cy, 1, 1))
            return
        # Heart = 2 top circles + bottom triangle.
        # Two lobes.
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["shadow_deep"], alpha),
                  (cx - size // 2 + 1, cy + 1), size // 2 + 1)
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["shadow_deep"], alpha),
                  (cx + size // 2 + 1, cy + 1), size // 2 + 1)
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                  (cx - size // 2, cy), size // 2)
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                  (cx + size // 2, cy), size // 2)
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha),
                  (cx - size // 2, cy - 1), max(1, size // 2 - 1))
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha),
                  (cx + size // 2, cy - 1), max(1, size // 2 - 1))
        # Bottom point.
        _NS_akashari._poly(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), [
            (cx - size, cy),
            (cx + size, cy),
            (cx, cy + size + 1),
        ])
        _NS_akashari._poly(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha), [
            (cx - size + 1, cy),
            (cx + size - 1, cy),
            (cx, cy + size),
        ])
        # Bright highlight on left lobe.
        if size >= 4:
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha),
                             (cx - size // 2, cy - 2, 1, 1))
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_white"], alpha),
                             (cx - size // 2 + 1, cy - 2, 1, 1))


    # ============================================================
    # SKILL: E - SCREAM OF PAIN (radial burst — spikes outward)
    # ============================================================
    def _draw_scream_ground(surface, boss, x, y, timer, phase):
        """Ring on ground indicating AoE."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_r = 55
        for i in range(3):
            r = int((max_r - i * 12) * min(1.0, progress * 1.5))
            alpha = _NS_akashari._alpha(190 - i * 40)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (x, y + 34), r, 2)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha), (x, y + 34), r, 1)


    def _draw_scream_foreground(surface, boss, x, y, timer, phase):
        """Radial spikes bursting outward from Akashari — Scream of Pain."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Central glow (source of scream).
        core_r = int(8 + progress * 12)
        core_alpha = _NS_akashari._alpha(200 * (1 - progress * 0.8))
        for r in range(core_r, 0, -2):
            a = _NS_akashari._alpha(core_alpha * (core_r - r) / core_r)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], a), (x, y), r)
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], core_alpha), (x, y),
                  max(1, core_r // 3))
        _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_white"], core_alpha), (x, y),
                  max(1, core_r // 5))

        # Radial spikes outward (bright red lines like sunburst).
        num_spikes = 16
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes
            # Spike propagates outward with time.
            spike_t = min(1.0, progress * 2)
            max_length = 55
            length = int(max_length * spike_t)
            # Beam shortens & fades near end.
            alpha = _NS_akashari._alpha(240 * (1 - abs(progress - 0.5) * 1.4))
            if alpha <= 0:
                continue

            # Direction vector.
            ex = x + int(math.cos(angle) * length)
            ey = y + int(math.sin(angle) * length * 0.6)  # flattened isometric

            # Layered spike beam.
            pygame.draw.line(surface, (*_NS_akashari.PALETTE["pain_darkest"], alpha),
                             (x, y + 1), (ex, ey + 1), 4)
            pygame.draw.line(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha),
                             (x, y), (ex, ey), 3)
            pygame.draw.line(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha),
                             (x, y), (ex, ey), 2)
            pygame.draw.line(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha),
                             (x, y), (ex, ey), 1)

            # Bright tip.
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha), (ex, ey), 2)
            pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_white"], alpha),
                             (ex, ey, 1, 1))

        # Concentric shockwave rings.
        for i in range(3):
            ring_t = (progress * 2 + i * 0.3) % 1.0
            r = int(15 + ring_t * 45)
            alpha = _NS_akashari._alpha(180 * (1 - ring_t))
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_light"], alpha), (x, y), r, 2)


    # ============================================================
    # SKILL: R - SONIC WAVE (large expanding sound rings)
    # ============================================================
    def _draw_sonic_wave_ground(surface, boss, x, y, timer, pulse):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_r = 90
        r = int(max_r * progress)
        for i in range(4):
            ring_r = max(0, r - i * 10)
            alpha = _NS_akashari._alpha(200 - i * 40)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (x, y + 34),
                      ring_r, 3)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha), (x, y + 34),
                      ring_r, 1)


    def _draw_sonic_wave_foreground(surface, boss, x, y, timer, phase):
        """Big expanding concentric sonic rings + directional cone forward."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Multiple expanding rings (concentric sonic waves).
        for i in range(5):
            wave_t = (progress * 2 + i * 0.2) % 1.0
            if wave_t > 1.0:
                continue
            r = int(15 + wave_t * 90)
            alpha = _NS_akashari._alpha(250 * (1 - wave_t))
            if alpha <= 0:
                continue

            # Layered ring.
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_darkest"], alpha), (x, y), r, 4)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_dark"], alpha), (x, y), r, 3)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_mid"], alpha), (x, y), r, 2)
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], alpha), (x, y), r, 1)
            # Inner bright rim.
            _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_white"], alpha),
                      (x, y), max(1, r - 1), 1)

        # Directional cone forward (Sonic Wave is directional in Dota).
        cone_length = int(120 * min(1.0, progress * 1.3))
        if cone_length > 5:
            for i in range(6):
                t = i / 5
                arc_length = int(cone_length * t)
                arc_alpha = _NS_akashari._alpha(220 * (1 - t))
                # Arc line at each depth.
                for a_off in (-0.4, -0.2, 0, 0.2, 0.4):
                    arc_x = x + int(math.cos(a_off) * arc_length) * facing
                    arc_y = y + int(math.sin(a_off) * arc_length * 0.5)
                    pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_hot"], arc_alpha),
                                     (arc_x, arc_y, 2, 2))
                    pygame.draw.rect(surface, (*_NS_akashari.PALETTE["pain_white"], arc_alpha),
                                     (arc_x, arc_y, 1, 1))

        # Central bright pulse.
        if progress < 0.6:
            core_r = int(10 + progress * 20)
            core_alpha = _NS_akashari._alpha(240 * (1 - progress * 1.5))
            for r in range(core_r, 0, -1):
                a = _NS_akashari._alpha(core_alpha * (core_r - r) / core_r)
                _NS_akashari._aacircle(surface, (*_NS_akashari.PALETTE["pain_hot"], a), (x, y), r)
            _NS_akashari._aacircle(surface, _NS_akashari.PALETTE["pain_white"], (x, y),
                      max(1, core_r // 3))


# ====================================================================
# VORENMARR
# ====================================================================
class _NS_vorenmarr:
    """Namespace vorenmarr - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Robe (deep blood red)
        "robe_darkest": (18, 5, 8),
        "robe_dark": (55, 12, 18),
        "robe_mid": (95, 25, 30),
        "robe_edge": (155, 45, 45),
        "robe_high": (200, 75, 65),

        # Cloak/hood (darker)
        "hood_darkest": (8, 3, 5),
        "hood_dark": (28, 10, 12),
        "hood_mid": (58, 20, 22),

        # Gold trim / armor accents
        "gold_darkest": (55, 32, 8),
        "gold_dark": (110, 72, 22),
        "gold_mid": (195, 145, 50),
        "gold_light": (245, 205, 95),
        "gold_shine": (255, 240, 170),

        # Skin (weathered pale)
        "skin_dark": (75, 45, 38),
        "skin_mid": (130, 90, 72),
        "skin_light": (185, 140, 110),

        # Hair/beard (dark grey)
        "hair_dark": (25, 20, 22),
        "hair_mid": (55, 45, 42),
        "hair_light": (95, 82, 78),

        # Staff (dark wood + iron)
        "wood_darkest": (18, 10, 8),
        "wood_dark": (42, 22, 15),
        "wood_mid": (75, 42, 25),
        "iron_dark": (28, 22, 25),
        "iron_mid": (65, 55, 58),
        "iron_light": (130, 118, 120),

        # Hellfire magic (bright red-orange, khas Warlock)
        "fire_darkest": (35, 5, 5),
        "fire_dark": (110, 15, 12),
        "fire_mid": (200, 40, 25),
        "fire_light": (255, 90, 50),
        "fire_hot": (255, 165, 90),
        "fire_white": (255, 230, 190),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vorenmarr._clamp(color)
        if _NS_vorenmarr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vorenmarr._clamp(color)
        if _NS_vorenmarr.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vorenmarr._clamp(color), points)


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
    def draw_vorenmarr(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vorenmarr._detect_moving(boss)
        _NS_vorenmarr._update_vorenmarr_attack_anim(boss)
        attacking = (
            getattr(boss, "_vor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_vorenmarr._draw_hell_aura(surface, x, y, pulse)
        _NS_vorenmarr._draw_dark_ground_ring(surface, x, y + 34, pulse, active_skill)

        if active_skill == "e":
            _NS_vorenmarr._draw_upheaval_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorenmarr._draw_golem_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_vorenmarr._draw_vorenmarr_attack(surface, boss, x, y)
        elif moving:
            _NS_vorenmarr._draw_vorenmarr_walk(surface, boss, x, y)
        else:
            _NS_vorenmarr._draw_vorenmarr_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_vorenmarr._draw_fatal_bonds(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vorenmarr._draw_power_coggle(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vorenmarr._draw_upheaval_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vorenmarr._draw_chaos_golem(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_vorenmarr_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vor_previous_timer", 0))
        active = bool(getattr(boss, "_vor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vor_attack_active = True
            boss._vor_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vor_attack_frame = int(
                getattr(boss, "_vor_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._vor_attack_active = False
            boss._vor_attack_frame = 0
            active = False

        boss._vor_previous_timer = timer
        boss._vor_attack_progress = (
            min(1.0, getattr(boss, "_vor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_vor_last_x"):
            boss._vor_last_x = boss.x
            boss._vor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vor_last_x)
        dy = abs(boss.y - boss._vor_last_y)
        boss._vor_last_x = boss.x
        boss._vor_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vorenmarr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_vorenmarr._draw_shadow(surface, x, y + 44)
        _NS_vorenmarr._draw_hell_wisps(surface, x, y + 30, boss.pulse)
        _NS_vorenmarr._draw_vorenmarr_body(surface, x, y + bob,
                              boss.direction, boss.pulse, "idle")


    def _draw_vorenmarr_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_vorenmarr._draw_shadow(surface, x + sway, y + 44)
        _NS_vorenmarr._draw_hell_wisps(surface, x + sway, y + 30, phase,
                          trail=True, facing=boss.direction)
        _NS_vorenmarr._draw_vorenmarr_body(surface, x + sway, y + bob,
                              boss.direction, phase, "walk")


    def _draw_vorenmarr_attack(surface, boss, x, y):
        progress = getattr(boss, "_vor_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 4) * boss.direction
        lift = int(math.sin(progress * math.pi) * 2)
        _NS_vorenmarr._draw_shadow(surface, x + lunge, y + 44)
        _NS_vorenmarr._draw_hell_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_vorenmarr._draw_vorenmarr_body(surface, x + lunge, y - lift,
                              boss.direction, boss.pulse, "attack", progress)
        _NS_vorenmarr._draw_basic_fire_bolt(surface, boss, x + lunge, y - lift, progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_vorenmarr_body(surface, cx, cy, facing, phase, action,
                              attack_progress=0):
        sway = int(math.sin(phase * 0.7) * (2 if action != "idle" else 1))
        if action == "attack":
            sway += int(math.sin(attack_progress * math.pi) * 2) * facing

        # Robe lower (floating drape, no legs).
        _NS_vorenmarr._draw_robe_lower(surface, cx, cy + 6, facing, phase, action)

        # Torso: dark red robe with gold trim.
        _NS_vorenmarr._draw_vorenmarr_torso(surface, cx, cy - 10, sway, facing, phase)

        # Arms (off-hand + main staff hand).
        _NS_vorenmarr._draw_vorenmarr_arms(surface, cx, cy - 6, facing, phase, action,
                              attack_progress)

        # Head: hooded with beard.
        _NS_vorenmarr._draw_vorenmarr_head(surface, cx, cy - 30, facing, phase)


    def _draw_robe_lower(surface, cx, cy, facing, phase, action):
        """Deep red robe menjuntai (floating drape)."""
        flow1 = math.sin(phase * 0.5) * 3
        flow2 = math.cos(phase * 0.4) * 2
        flow3 = math.sin(phase * 0.7 + 1) * 2

        # Main robe shape (bell/tapered wider bottom).
        main = [
            (cx - 15, cy - 8),
            (cx + 15, cy - 8),
            (cx + 19 + int(flow1), cy + 4),
            (cx + 22, cy + 16),
            (cx + 16, cy + 27),
            (cx + 8 + int(flow3), cy + 31),
            (cx + 2, cy + 33),
            (cx - 2, cy + 33),
            (cx - 8 + int(flow3), cy + 31),
            (cx - 16, cy + 27),
            (cx - 22, cy + 16),
            (cx - 19 - int(flow1), cy + 4),
        ]
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in main])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["robe_darkest"], main)
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["robe_dark"], [
            (cx - 13, cy - 6),
            (cx + 13, cy - 6),
            (cx + 16 + int(flow1), cy + 4),
            (cx + 18, cy + 14),
            (cx + 13, cy + 24),
            (cx + 4, cy + 29),
            (cx - 4, cy + 29),
            (cx - 13, cy + 24),
            (cx - 18, cy + 14),
            (cx - 16 - int(flow1), cy + 4),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["robe_mid"], [
            (cx - 10, cy - 3),
            (cx + 10, cy - 3),
            (cx + 12, cy + 4),
            (cx + 13, cy + 14),
            (cx + 8, cy + 22),
            (cx - 8, cy + 22),
            (cx - 13, cy + 14),
            (cx - 12, cy + 4),
        ])

        # Gold trim vertical strip at center front (khas Warlock robe).
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["gold_dark"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 3, cy + 12),
            (cx + 2, cy + 26),
            (cx - 2, cy + 26),
            (cx - 3, cy + 12),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["gold_mid"], [
            (cx - 1, cy - 3),
            (cx + 1, cy - 3),
            (cx + 2, cy + 12),
            (cx + 1, cy + 24),
            (cx - 1, cy + 24),
            (cx - 2, cy + 12),
        ])
        pygame.draw.line(surface, _NS_vorenmarr.PALETTE["gold_light"],
                         (cx, cy - 2), (cx, cy + 22), 1)

        # Gold trim horizontal at hem.
        pygame.draw.line(surface, _NS_vorenmarr.PALETTE["gold_dark"],
                         (cx - 16, cy + 24), (cx + 16, cy + 24), 2)
        pygame.draw.line(surface, _NS_vorenmarr.PALETTE["gold_mid"],
                         (cx - 15, cy + 24), (cx + 15, cy + 24), 1)

        # Chest core cavity below torso (glowing red inside robe).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_alpha = _NS_vorenmarr._alpha(180 * pulse)
        for r in range(6, 0, -1):
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], _NS_vorenmarr._alpha(core_alpha * (6 - r) / 6)),
                      (cx, cy + 8), r)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], core_alpha), (cx, cy + 8), 2)
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (cx, cy + 8, 1, 1))

        # Small red runic marks on robe (cracked glow like hellfire embers).
        for i, (x1, y1) in enumerate([(-9, 6), (7, 8), (-11, 14), (10, 15),
                                        (-6, 20), (6, 20)]):
            rune_pulse = math.sin(phase * 1.5 + i * 0.5) * 0.3 + 0.7
            rune_alpha = _NS_vorenmarr._alpha(200 * rune_pulse)
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], rune_alpha),
                             (cx + x1, cy + y1, 2, 2))
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], rune_alpha),
                             (cx + x1, cy + y1, 1, 1))

        # Tattered hem detail (bottom edge).
        for i, ox in enumerate((-12, -6, 0, 6, 12)):
            hem_phase = math.sin(phase * 0.8 + i * 0.4) * 2
            hem_y = cy + 29 + int(hem_phase)
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["robe_darkest"],
                             (cx + ox, cy + 25), (cx + ox, hem_y + 2), 3)
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["robe_dark"],
                             (cx + ox, cy + 25), (cx + ox, hem_y), 1)
            # Gold edge dot.
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["gold_dark"], (cx + ox, hem_y, 2, 1))


    def _draw_vorenmarr_torso(surface, cx, cy, sway, facing, phase):
        # Robe torso with tighter shape.
        body = [
            (cx - 13, cy - 6),
            (cx + 13, cy - 6),
            (cx + 14 + sway, cy + 6),
            (cx + 10, cy + 16),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 10, cy + 16),
            (cx - 14 - sway, cy + 6),
        ]
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in body])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["robe_darkest"], body)
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["robe_dark"], [
            (cx - 11, cy - 4),
            (cx + 11, cy - 4),
            (cx + 12 + sway, cy + 6),
            (cx + 8, cy + 14),
            (cx - 8, cy + 14),
            (cx - 12 - sway, cy + 6),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["robe_mid"], [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 9, cy + 6),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 9, cy + 6),
        ])

        # Gold V-neck opening at chest (fold trim).
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["gold_dark"], [
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["gold_mid"], [
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
            (cx + 1, cy + 3),
            (cx - 1, cy + 3),
        ])

        # Amulet (chest medallion — signature Warlock).
        _NS_vorenmarr._draw_chest_amulet(surface, cx, cy + 6, phase)

        # Gold shoulder pauldrons (spiky).
        for side in (-1, 1):
            sx = cx + side * 11
            # Base pauldron.
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["shadow_deep"], (sx + 1, cy - 3), 6)
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_darkest"], (sx, cy - 4), 5)
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_dark"], (sx - side, cy - 5), 4)
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_mid"], (sx - side * 2, cy - 6), 2)
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_light"], (sx - side * 2, cy - 7), 1)

            # Pauldron spike (jagged upward).
            _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["gold_darkest"], [
                (sx + side * 3, cy - 7),
                (sx + side * 6, cy - 14),
                (sx + side * 5, cy - 4),
            ])
            _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["gold_dark"], [
                (sx + side * 3, cy - 7),
                (sx + side * 5, cy - 13),
                (sx + side * 4, cy - 4),
            ])
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["gold_light"],
                             (sx + side * 4, cy - 8), (sx + side * 5, cy - 12), 1)


    def _draw_chest_amulet(surface, cx, cy, phase):
        """Ornate amulet with glowing red gem."""
        # Chain (curving across chest).
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["gold_dark"],
                             (cx + side * 5, cy - 7),
                             (cx + side * 2, cy - 3), 1)

        # Medallion base.
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["shadow_deep"], (cx, cy + 1), 4)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_darkest"], (cx, cy), 4)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_dark"], (cx - 1, cy - 1), 3)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_mid"], (cx - 1, cy - 1), 2)
        # Central gem (glowing red).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_vorenmarr._alpha(230 * pulse)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_darkest"], (cx, cy), 2)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], gem_alpha), (cx, cy), 2)
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_hot"], (cx, cy, 1, 1))


    def _draw_vorenmarr_arms(surface, cx, cy, facing, phase, action,
                              attack_progress):
        # Off-hand (open, gesturing).
        off_dir = -facing
        off_sway = math.sin(phase * 0.7) * 2
        off_x = cx + off_dir * 15
        off_y = cy + 8 + int(off_sway)
        _NS_vorenmarr._draw_arm(surface, cx + off_dir * 10, cy - 2,
                  off_x, off_y, phase)
        _NS_vorenmarr._draw_hand(surface, off_x, off_y + 3, off_dir, phase)

        # Main hand (holding staff).
        weapon_x = cx + facing * 10
        weapon_y = cy - 2

        if action == "attack":
            p = max(0.0, min(1.0, attack_progress))
            # 3-phase: raise staff → thrust forward casting → recovery.
            if p < 0.30:
                # Raise staff dramatically.
                t = p / 0.30
                t = t * t * (3 - 2 * t)
                angle = math.pi * 0.5 - t * math.pi * 0.85  # up to overhead
                distance = 18
            elif p < 0.55:
                # Cast: staff thrusts forward, orb glows brightest.
                t = (p - 0.30) / 0.25
                t = 1 - (1 - t) ** 3
                angle = -math.pi * 0.35 + t * math.pi * 0.60  # sweep down-forward
                distance = 22 + int(t * 8)
            else:
                # Recovery.
                t = (p - 0.55) / 0.45
                t = t * t * (3 - 2 * t)
                angle = math.pi * 0.25 + t * math.pi * 0.20
                distance = 30 - int(t * 12)

            hand_x = weapon_x + int(math.cos(angle) * distance) * facing
            hand_y = weapon_y + int(math.sin(angle) * distance)
            elbow_x = (weapon_x + hand_x) // 2 + 2 * facing
            elbow_y = (weapon_y + hand_y) // 2 - 3

            _NS_vorenmarr._draw_arm(surface, weapon_x, weapon_y, elbow_x, elbow_y, phase)
            _NS_vorenmarr._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, phase)
            _NS_vorenmarr._draw_hand(surface, hand_x, hand_y + 2, facing, phase)
            # Staff follows hand angle.
            staff_angle = angle + math.pi * 0.45 * facing  # staff pointing up-forward
            _NS_vorenmarr._draw_staff(surface, hand_x, hand_y, staff_angle, facing,
                        phase, casting=True, cast_progress=p)
        else:
            # Idle: staff held upright beside body.
            idle_sway = math.sin(phase * 0.5) * 0.04
            hand_x = weapon_x + facing * 6
            hand_y = weapon_y + 4 + int(idle_sway * 8)
            _NS_vorenmarr._draw_arm(surface, weapon_x, weapon_y, hand_x, hand_y, phase)
            _NS_vorenmarr._draw_hand(surface, hand_x, hand_y + 2, facing, phase)
            # Staff pointing up.
            staff_angle = -math.pi * 0.5 + idle_sway * 2
            _NS_vorenmarr._draw_staff(surface, hand_x, hand_y, staff_angle, facing,
                        phase, casting=False)


    def _draw_arm(surface, x1, y1, x2, y2, phase):
        """Dark red robed arm."""
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 7)
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["robe_dark"], (x1, y1), (x2, y2), 5)
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["robe_mid"], (x1 - 1, y1), (x2 - 1, y2), 2)
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["robe_edge"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Gold cuff at end (wrist).
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_dark"], (x2, y2), 3)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["gold_mid"], (x2 - 1, y2 - 1), 2)
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["gold_light"], (x2 - 1, y2 - 1, 1, 1))


    def _draw_hand(surface, x, y, direction, phase):
        """Weathered pale hand."""
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["shadow_deep"], (x, y), 3)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["skin_dark"], (x, y - 1), 3)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["skin_light"], (x - 1, y - 2, 1, 1))


    def _draw_staff(surface, hx, hy, angle, facing, phase, casting=False,
                     cast_progress=0):
        """Ornate warlock staff with lantern orb at top."""
        # Staff shaft (wooden with dark iron cap).
        shaft_len = 44
        # Butt end.
        butt_x = hx - int(math.cos(angle) * 10)
        butt_y = hy - int(math.sin(angle) * 10)
        # Head end (where orb sits).
        head_x = hx + int(math.cos(angle) * shaft_len)
        head_y = hy + int(math.sin(angle) * shaft_len)

        # Shadow.
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["shadow_deep"],
                (butt_x + 2, butt_y + 2), (head_x + 2, head_y + 2), 5)

        # Shaft.
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["wood_darkest"], (butt_x, butt_y),
                (head_x, head_y), 5)
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["wood_dark"], (butt_x, butt_y),
                (head_x, head_y), 3)
        _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["wood_mid"], (butt_x, butt_y),
                (head_x, head_y), 1)

        # Iron bands wrapping shaft.
        for t in (0.25, 0.55, 0.80):
            bx = butt_x + int(math.cos(angle) * (shaft_len + 10) * t)
            by = butt_y + int(math.sin(angle) * (shaft_len + 10) * t)
            perp_x = -math.sin(angle)
            perp_y = math.cos(angle)
            b1 = (bx + int(perp_x * 3), by + int(perp_y * 3))
            b2 = (bx - int(perp_x * 3), by - int(perp_y * 3))
            _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["iron_dark"], b1, b2, 3)
            _NS_vorenmarr._aaline(surface, _NS_vorenmarr.PALETTE["iron_light"], b1, b2, 1)

        # Butt cap (small metal ball).
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["iron_dark"], (butt_x, butt_y), 2)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["iron_light"], (butt_x - 1, butt_y - 1), 1)

        # Ornate iron holder at top (claws holding orb).
        holder_x = head_x - int(math.cos(angle) * 5)
        holder_y = head_y - int(math.sin(angle) * 5)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["iron_dark"], (holder_x, holder_y), 4)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["iron_mid"], (holder_x - 1, holder_y - 1), 3)

        # Claws/hooks around orb (3 curled prongs).
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)
        for prong_off in (-1, 0, 1):
            prong_x = holder_x + int(perp_x * prong_off * 3)
            prong_y = holder_y + int(perp_y * prong_off * 3)
            # Curl up around orb.
            curl_x = head_x + int(perp_x * prong_off * 4)
            curl_y = head_y + int(perp_y * prong_off * 4) - 2
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["iron_dark"],
                             (prong_x, prong_y), (curl_x, curl_y), 2)
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["iron_light"],
                             (prong_x, prong_y), (curl_x, curl_y), 1)

        # LANTERN ORB at top (glowing hellfire).
        orb_x = head_x
        orb_y = head_y
        _NS_vorenmarr._draw_lantern_orb(surface, orb_x, orb_y, phase, casting, cast_progress)


    def _draw_lantern_orb(surface, x, y, phase, casting=False, cast_progress=0):
        """Glowing red-orange orb (like a lantern with hellfire inside)."""
        intensity = 1.0 + (cast_progress if casting else 0) * 0.6
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        glow_r = int(8 * intensity * pulse)

        # Outer glow.
        for r in range(glow_r, 0, -1):
            alpha = _NS_vorenmarr._alpha(80 * (glow_r - r) / max(1, glow_r) * pulse)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (x, y), r)

        # Orb body.
        orb_size = 4
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["shadow_deep"], (x + 1, y + 1), orb_size + 1)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["iron_dark"], (x, y), orb_size + 1)

        # Bright hellfire inside orb.
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_darkest"], (x, y), orb_size)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_dark"], (x, y), orb_size - 1)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_mid"], (x, y - 1), max(1, orb_size - 2))
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_hot"], (x - 1, y - 1), max(1, orb_size - 3))
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (x - 1, y - 1, 1, 1))

        # Flame flickers on top (small tongues of fire).
        if casting or math.sin(phase * 3) > 0:
            flame_h = 3 + int(math.sin(phase * 4) * 2)
            for i, ox in enumerate((-1, 0, 1)):
                fh = flame_h - abs(ox)
                if fh > 0:
                    pygame.draw.line(surface, _NS_vorenmarr.PALETTE["fire_light"],
                                     (x + ox, y - orb_size),
                                     (x + ox, y - orb_size - fh), 1)
                    if fh > 1:
                        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_hot"],
                                         (x + ox, y - orb_size - fh, 1, 1))

        # Sparks flying off (if casting).
        if casting and cast_progress > 0.3:
            alpha = _NS_vorenmarr._alpha(240 * (1 - abs(cast_progress - 0.5) * 1.5))
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                sx = x + int(math.cos(angle) * (glow_r + 3))
                sy = y + int(math.sin(angle) * (glow_r + 3))
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha), (sx, sy, 2, 2))


    def _draw_vorenmarr_head(surface, cx, cy, facing, phase):
        """Hooded head with beard visible."""
        # Neck.
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["skin_dark"], (cx - 2, cy + 8, 5, 5))
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["skin_mid"], (cx - 2, cy + 8, 3, 4))

        # Hood shape (drape over head from behind).
        hood_back = [
            (cx - 12, cy - 5),
            (cx - 10, cy - 12),
            (cx - 4, cy - 15),
            (cx + 4, cy - 15),
            (cx + 10, cy - 12),
            (cx + 12, cy - 5),
            (cx + 13, cy + 6),
            (cx + 8, cy + 12),
            (cx - 8, cy + 12),
            (cx - 13, cy + 6),
        ]
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in hood_back])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["hood_darkest"], hood_back)
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["hood_dark"], [
            (cx - 10, cy - 4),
            (cx - 8, cy - 11),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 8, cy - 11),
            (cx + 10, cy - 4),
            (cx + 11, cy + 5),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 11, cy + 5),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["hood_mid"], [
            (cx - 8, cy - 3),
            (cx - 6, cy - 9),
            (cx + 6, cy - 9),
            (cx + 8, cy - 3),
            (cx + 8, cy + 3),
            (cx - 8, cy + 3),
        ])

        # Face partially visible inside hood (dark shadow with skin).
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["shadow_deep"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 5, cy + 4),
            (cx - 5, cy + 4),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["skin_dark"], [
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["skin_mid"], [
            (cx - 4, cy - 2),
            (cx + 4, cy - 2),
            (cx + 3, cy + 1),
            (cx - 3, cy + 1),
        ])

        # Glowing red eyes (angry warlock).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 2):
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["shadow_deep"],
                             (eye_x - 1, cy - 2, 3, 2))
            eye_alpha = _NS_vorenmarr._alpha(240 * pulse)
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], eye_alpha),
                             (eye_x, cy - 2, 2, 1))
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_hot"], (eye_x, cy - 2, 1, 1))
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (eye_x, cy - 2, 1, 1))

        # Nose shadow.
        pygame.draw.line(surface, _NS_vorenmarr.PALETTE["skin_dark"],
                         (cx - 1, cy), (cx - 1, cy + 1), 1)

        # BEARD (dark grey, prominent — khas Warlock).
        beard = [
            (cx - 5, cy + 2),
            (cx + 5, cy + 2),
            (cx + 5, cy + 6),
            (cx + 3, cy + 10),
            (cx - 3, cy + 10),
            (cx - 5, cy + 6),
        ]
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["hair_dark"], beard)
        _NS_vorenmarr._poly(surface, _NS_vorenmarr.PALETTE["hair_mid"], [
            (cx - 4, cy + 3),
            (cx + 4, cy + 3),
            (cx + 4, cy + 6),
            (cx + 2, cy + 9),
            (cx - 2, cy + 9),
            (cx - 4, cy + 6),
        ])
        # Mustache line.
        pygame.draw.line(surface, _NS_vorenmarr.PALETTE["hair_dark"],
                         (cx - 4, cy + 2), (cx + 4, cy + 2), 2)

        # Hood shoulder-cape flap (side).
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["hood_darkest"],
                             (cx + side * 10, cy + 6), (cx + side * 13, cy + 12), 3)
            pygame.draw.line(surface, _NS_vorenmarr.PALETTE["hood_dark"],
                             (cx + side * 10, cy + 6), (cx + side * 12, cy + 11), 1)

        # Hood peak/point at top with small gold rim (subtle).
        pygame.draw.line(surface, _NS_vorenmarr.PALETTE["gold_dark"],
                         (cx - 4, cy - 13), (cx + 4, cy - 13), 1)


    # ============================================================
    # BASIC ATTACK — FIRE BOLT (ranged with staff swing)
    # ============================================================
    def _draw_basic_fire_bolt(surface, boss, x, y, progress):
        """Fire bolt projectile dilempar setelah staff cast swing."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_vorenmarr._target_position(boss, x, y)

        t = (progress - 0.55) / 0.45
        # Start from orb position (approximately at swing peak).
        start_x = x + facing * 36
        start_y = y - 12
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (fire).
        for i in range(6):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vorenmarr._alpha(220 - i * 35)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_darkest"], alpha), (px, py), 6 - i)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (px, py), 4 - i // 2)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], alpha), (px, py), 3 - i // 2)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha), (px, py),
                      max(1, 2 - i // 2))

        # Bolt head (bright fire orb).
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_darkest"], (bx, by), 5)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_dark"], (bx, by), 4)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_mid"], (bx, by), 3)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_light"], (bx, by), 2)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.85:
            splash_t = (t - 0.85) / 0.15
            radius = int(5 + splash_t * 16)
            alpha = _NS_vorenmarr._alpha(230 * (1 - splash_t))
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_light"], alpha), (tx, ty), radius, 2)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha), (tx, ty),
                      max(1, radius - 6), 1)
            for i in range(6):
                angle = i * math.pi / 3
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.6)
                pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_hot"], (ex, ey, 2, 2))


    # ============================================================
    # FLOATING HELLFIRE WISPS (below body)
    # ============================================================
    def _draw_hell_wisps(surface, cx, cy, phase, trail=False,
                          facing=1, intense=False):
        strength = 1.5 if intense else 1.0

        # Dark mist with red inner glow.
        mist = pygame.Surface((120, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = _NS_vorenmarr._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha),
                    (60 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -3):
            alpha = _NS_vorenmarr._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                    (60 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Hellfire tendrils rising.
        for i, offset in enumerate((-20, -8, 6, 18, -14, 14, -2)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_vorenmarr._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), (sx, sy), 5)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_darkest"], alpha), (sx, sy - 1), 3)
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                             (sx, sy - 2, 2, 2))
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                             (sx, sy - 3, 1, 1))

        # Fire embers floating up.
        for i in range(6):
            ember_t = (phase * 0.7 + i * 0.2) % 1.0
            ex = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(ember_t * 22)
            alpha = _NS_vorenmarr._alpha(240 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Swirling dark motes with red cores.
        for i in range(8):
            angle = phase * 0.7 + i * math.pi * 2 / 8
            radius = 26 + int(math.sin(phase + i * 0.6) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * 9)
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["hood_darkest"], (sx, sy), 2)
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_mid"], (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vorenmarr._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha),
                          (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 4, 90, 10))
        pygame.draw.ellipse(shadow, (85, 20, 20, 110), (12, 6, 76, 6))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_hell_aura(surface, x, y, phase):
        """Dark red aura around body."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((160, 130), pygame.SRCALPHA)
        for radius in range(70, 5, -5):
            alpha = _NS_vorenmarr._alpha((70 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_vorenmarr._aacircle(aura, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), (80, 65), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_vorenmarr._alpha((45 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_vorenmarr._aacircle(aura, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (80, 65), radius)
        surface.blit(aura, (x - 80, y - 65))

        # Fire embers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 28 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_hot"], (sx, sy, 1, 1))


    def _draw_dark_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((120, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vorenmarr.PALETTE["hood_darkest"], 190),
                            (5, 12, 110, 20), 3)
        pygame.draw.ellipse(ring, (*_NS_vorenmarr.PALETTE["fire_darkest"], 200),
                            (12, 14, 96, 16), 2)
        pygame.draw.ellipse(ring, (*_NS_vorenmarr.PALETTE["fire_dark"], 220),
                            (22, 16, 76, 12), 1)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 60 + int(math.cos(angle) * 32)
            y1 = 21 + int(math.sin(angle) * 6)
            x2 = 60 + int(math.cos(angle) * 50)
            y2 = 21 + int(math.sin(angle) * 9)
            pygame.draw.line(ring, (*_NS_vorenmarr.PALETTE["fire_light"], 210),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vorenmarr.PALETTE["fire_hot"], _NS_vorenmarr._alpha(120 * pulse)),
                                (15, 8, 90, 30), 1)
        surface.blit(ring, (x - 60, y - 21))


    # ============================================================
    # SKILL: Q - FATAL BONDS (red chain link between enemies)
    # ============================================================
    def _draw_fatal_bonds(surface, boss, x, y, timer, phase):
        """Red glowing chain-line dari boss ke target, terlihat mengikat."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vorenmarr._target_position(boss, x, y)
        facing = boss.direction

        start_x = x + facing * 30
        start_y = y - 10

        # Casting glow at hand initially.
        if progress < 0.25:
            t = progress / 0.25
            cr = int(3 + t * 8)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_vorenmarr._alpha(180 * (cr + 3 - r) / (cr + 3))
                _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                          (start_x, start_y), r)
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_hot"], (start_x, start_y), 3)
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (start_x, start_y, 1, 1))
        else:
            # Extending chain to target.
            t = (progress - 0.25) / 0.75
            current_x = int(start_x + (tx - start_x) * min(1.0, t * 2))
            current_y = int(start_y + (ty - start_y) * min(1.0, t * 2))

            # Draw glowing bond line (dashed style with bright segments).
            dx = current_x - start_x
            dy = current_y - start_y
            dist = max(1, math.hypot(dx, dy))
            num_segs = max(6, int(dist / 12))

            for i in range(num_segs):
                seg_t = i / num_segs
                seg_t2 = (i + 0.6) / num_segs
                sx = int(start_x + dx * seg_t)
                sy = int(start_y + dy * seg_t)
                ex = int(start_x + dx * seg_t2)
                ey = int(start_y + dy * seg_t2)
                # Pulsating.
                pulse_alpha = _NS_vorenmarr._alpha(220 + math.sin(phase * 4 + i) * 30)
                # Layered bond line.
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_darkest"], pulse_alpha),
                                 (sx, sy + 1), (ex, ey + 1), 4)
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], pulse_alpha),
                                 (sx, sy), (ex, ey), 3)
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], pulse_alpha),
                                 (sx, sy), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], pulse_alpha),
                                 (sx, sy), (ex, ey), 1)

            # End nodes (glowing orbs at both ends).
            for orb_x, orb_y in [(start_x, start_y), (current_x, current_y)]:
                _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_dark"], (orb_x, orb_y), 4)
                _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_mid"], (orb_x, orb_y), 3)
                _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_hot"], (orb_x, orb_y), 2)
                pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (orb_x, orb_y, 1, 1))

            # Ring around target (bound).
            if t > 0.4:
                ring_r = int(12 + math.sin(phase * 2) * 2)
                pygame.draw.circle(surface, _NS_vorenmarr.PALETTE["fire_mid"],
                                   (tx, ty), ring_r, 2)


    # ============================================================
    # SKILL: W - POWER COGGLE (buff aura + upward arrows)
    # ============================================================
    def _draw_power_coggle(surface, boss, x, y, timer, phase):
        """Red ring on ground + upward arrows around ally (target)."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vorenmarr._target_position(boss, x, y)

        # Ground ring.
        for i in range(3):
            r = int(20 + i * 8)
            alpha = _NS_vorenmarr._alpha(200 - i * 40)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (tx, ty), r, 2)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], alpha), (tx, ty), r, 1)

        # Rune inside ring.
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_hot"], (tx, ty), 4)
        _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_white"], (tx, ty), 2)

        # Upward-flowing arrows/embers (empowerment).
        for i in range(6):
            arrow_t = (phase * 1.2 + i * 0.16) % 1.0
            arrow_angle = i * math.pi * 2 / 6
            ax = tx + int(math.cos(arrow_angle) * 14)
            ay = ty - int(arrow_t * 30) + int(math.sin(arrow_angle) * 4)
            alpha = _NS_vorenmarr._alpha(240 * (1 - arrow_t))
            if alpha <= 0:
                continue
            # Small upward arrow shape (line + arrowhead).
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                             (ax, ay), (ax, ay - 5), 2)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                             (ax, ay), (ax, ay - 5), 1)
            # Arrowhead.
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                             (ax - 2, ay - 3), (ax, ay - 5), 1)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                             (ax + 2, ay - 3), (ax, ay - 5), 1)


    # ============================================================
    # SKILL: E - UPHEAVAL (crystals bursting from ground)
    # ============================================================
    def _draw_upheaval_ground(surface, boss, x, y, timer, pulse):
        """Ring on ground indicating AoE."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vorenmarr._target_position(boss, x, y)
        max_r = 55

        for i in range(3):
            r = int((max_r - i * 10) * min(1.0, progress * 1.5))
            alpha = _NS_vorenmarr._alpha(180 - i * 40)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (tx, ty), r, 2)


    def _draw_upheaval_foreground(surface, boss, x, y, timer, phase):
        """Fire crystals erupting from ground in ring."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vorenmarr._target_position(boss, x, y)

        # 6 crystals bursting in a circle.
        num_crystals = 6
        for i in range(num_crystals):
            angle = i * math.pi * 2 / num_crystals + phase * 0.2
            distance = 32
            cx = tx + int(math.cos(angle) * distance)
            cy = ty + int(math.sin(angle) * distance * 0.55)

            crystal_t = max(0.0, min(1.0, (progress - i * 0.06) * 1.8))
            if crystal_t <= 0:
                continue
            _NS_vorenmarr._draw_fire_crystal(surface, cx, cy, crystal_t, phase + i)

        # Central big crystal.
        center_t = max(0.0, min(1.0, progress * 1.5))
        if center_t > 0:
            _NS_vorenmarr._draw_fire_crystal(surface, tx, ty, center_t, phase, big=True)


    def _draw_fire_crystal(surface, cx, cy, appear_t, phase, big=False):
        """Sharp crystal spike glowing with hellfire."""
        height = int((16 if big else 12) * appear_t)
        width = 4 if big else 3
        if height < 2:
            return
        alpha = _NS_vorenmarr._alpha(240 * appear_t)

        # Base of crystal (dark rock/shadow).
        base_shape = [
            (cx - width - 1, cy + 2),
            (cx + width + 1, cy + 2),
            (cx + width, cy + 4),
            (cx - width, cy + 4),
        ]
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha), base_shape)

        # Main crystal body (elongated diamond).
        crystal = [
            (cx, cy - height),                      # top tip
            (cx + width, cy - height // 2),         # upper right
            (cx + width - 1, cy + 2),               # bottom right
            (cx - width + 1, cy + 2),               # bottom left
            (cx - width, cy - height // 2),         # upper left
        ]
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
              [(px + 1, py + 1) for px, py in crystal])
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["fire_darkest"], alpha), crystal)
        # Inner glow (narrower).
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), [
            (cx, cy - height + 1),
            (cx + width - 1, cy - height // 2),
            (cx + width - 2, cy + 1),
            (cx - width + 2, cy + 1),
            (cx - width + 1, cy - height // 2),
        ])
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], alpha), [
            (cx, cy - height + 2),
            (cx + width - 2, cy - height // 2),
            (cx + width - 3, cy),
            (cx - width + 3, cy),
            (cx - width + 2, cy - height // 2),
        ])

        # Bright center vertical line (crystal core).
        _NS_vorenmarr._aaline(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                (cx, cy - height + 1), (cx, cy + 1), 1)
        _NS_vorenmarr._aaline(surface, (*_NS_vorenmarr.PALETTE["fire_white"], alpha),
                (cx, cy - height + 2), (cx, cy - 1), 1)

        # Facet edge highlights.
        pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_light"], alpha),
                         (cx, cy - height), (cx + width, cy - height // 2), 1)
        pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_light"], alpha),
                         (cx, cy - height), (cx - width, cy - height // 2), 1)

        # Sparks around big crystal.
        if big:
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                sx = cx + int(math.cos(angle) * (width + 4))
                sy = cy - height // 2 + int(math.sin(angle) * 6)
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 2, 2))


    # ============================================================
    # SKILL: R - CHAOS GOLEM (summon big golem beside boss)
    # ============================================================
    def _draw_golem_ground(surface, boss, x, y, timer, pulse):
        """Summoning circle on ground."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        gx = x + facing * 55
        gy = y + 34

        # Big glowing summoning ring.
        for i in range(3):
            r = int(30 + i * 8)
            alpha = _NS_vorenmarr._alpha(220 - i * 40)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_darkest"], alpha), (gx, gy), r, 3)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (gx, gy), r, 1)

        # Runic marks around circle.
        for i in range(8):
            angle = pulse * 0.4 + i * math.pi / 4
            px = gx + int(math.cos(angle) * 28)
            py = gy + int(math.sin(angle) * 14)
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_hot"], (px, py, 2, 2))
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["fire_white"], (px, py, 1, 1))


    def _draw_chaos_golem(surface, boss, x, y, timer, phase):
        """Massive chaos golem rises beside warlock."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Position golem beside boss.
        gx = x + facing * 55
        gy = y + 4

        # Rising from ground: use appear_t.
        rise_t = min(1.0, progress * 1.5)
        if rise_t <= 0.02:
            return

        # Rising offset (starts below ground).
        rise = int((1 - rise_t) * 40)
        body_y = gy + rise

        # Base fire glow at feet.
        fire_r = int(20 * rise_t)
        for r in range(fire_r, 0, -2):
            alpha = _NS_vorenmarr._alpha(180 * (fire_r - r) / max(1, fire_r))
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (gx, gy + 34), r)

        if rise_t < 0.2:
            # Early rise: mostly fire, hint of body.
            _NS_vorenmarr._aacircle(surface, _NS_vorenmarr.PALETTE["fire_hot"], (gx, gy + 34), int(rise_t * 20))
            return

        # Draw golem body (appears as it rises).
        _NS_vorenmarr._draw_golem_body(surface, gx, body_y, phase, rise_t, facing)


    def _draw_golem_body(surface, cx, cy, phase, appear_t, facing):
        """Massive lava/chaos golem body — angular, molten cracks glowing."""
        alpha = _NS_vorenmarr._alpha(255 * appear_t)
        sway = int(math.sin(phase * 0.5) * 1)

        # Massive lower body.
        lower = [
            (cx - 18, cy + 6),
            (cx + 18, cy + 6),
            (cx + 22 + sway, cy + 20),
            (cx + 15, cy + 32),
            (cx - 15, cy + 32),
            (cx - 22 - sway, cy + 20),
        ]
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
              [(px + 2, py + 2) for px, py in lower])
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), lower)
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha), [
            (cx - 16, cy + 8),
            (cx + 16, cy + 8),
            (cx + 19 + sway, cy + 20),
            (cx + 12, cy + 30),
            (cx - 12, cy + 30),
            (cx - 19 - sway, cy + 20),
        ])

        # Massive torso (barrel-chested).
        torso = [
            (cx - 20, cy - 8),
            (cx + 20, cy - 8),
            (cx + 22, cy + 8),
            (cx - 22, cy + 8),
        ]
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
              [(px + 2, py + 2) for px, py in torso])
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), torso)
        _NS_vorenmarr._poly(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha), [
            (cx - 18, cy - 6),
            (cx + 18, cy - 6),
            (cx + 20, cy + 6),
            (cx - 20, cy + 6),
        ])

        # Molten cracks glowing red across body.
        cracks = [
            ((-14, -3), (-8, 5)),
            ((6, -4), (12, 4)),
            ((-16, 12), (-8, 20)),
            ((7, 14), (16, 22)),
            ((-4, 0), (3, 8)),
            ((-2, 22), (5, 28)),
        ]
        for (x1, y1), (x2, y2) in cracks:
            pulse_alpha = _NS_vorenmarr._alpha(alpha * 0.9 * (0.7 + math.sin(phase * 2 + x1) * 0.3))
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], pulse_alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 3)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], pulse_alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 1)

        # Central chest core (glowing fire heart).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_r = int(4 * pulse) + 2
        for r in range(core_r * 2, 0, -1):
            a = _NS_vorenmarr._alpha(alpha * 0.6 * (core_r * 2 - r) / (core_r * 2))
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], a), (cx, cy), r)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha), (cx, cy), core_r)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_white"], alpha), (cx, cy), max(1, core_r - 2))

        # Arms (massive).
        for side in (-1, 1):
            # Shoulder.
            sx = cx + side * 22
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha), (sx + 1, cy - 4), 9)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), (sx, cy - 5), 8)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha), (sx - side, cy - 6), 5)
            # Arm.
            hand_x = sx + side * 4
            hand_y = cy + 12 + int(math.sin(phase * 0.5) * 1)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
                             (sx + 1, cy - 3), (hand_x + 1, hand_y + 1), 10)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha),
                             (sx, cy - 4), (hand_x, hand_y), 9)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha),
                             (sx, cy - 4), (hand_x, hand_y), 6)
            pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                             (sx, cy - 4), (hand_x, hand_y), 1)
            # Fist (big claw hand).
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha), (hand_x, hand_y + 1), 6)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), (hand_x, hand_y), 5)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha), (hand_x, hand_y), 2)
            _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha), (hand_x, hand_y), 1)
            # Claws.
            for i, ang in enumerate((0.3, 0.6, 0.9)):
                claw_x = hand_x + int(math.cos(ang) * 6) * side
                claw_y = hand_y + int(math.sin(ang) * 6)
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha),
                                 (hand_x, hand_y), (claw_x, claw_y), 2)
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha),
                                 (claw_x, claw_y, 1, 1))

        # Head (with horns).
        hx = cx
        hy = cy - 18
        # Head base.
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha), (hx + 1, hy + 1), 9)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha), (hx, hy), 8)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha), (hx - 1, hy - 1), 6)
        _NS_vorenmarr._aacircle(surface, (*_NS_vorenmarr.PALETTE["hood_mid"], alpha), (hx - 1, hy - 2), 3)

        # Horns (large, curving).
        for side in (-1, 1):
            for i, (base_off, tip_ox, tip_oy) in enumerate([
                (side * 5, side * 10, -8),
                (side * 3, side * 6, -12),
            ]):
                bx = hx + base_off
                by = hy - 4
                tx = hx + tip_ox
                ty = hy + tip_oy
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
                                 (bx + 1, by + 1), (tx + 1, ty + 1), 4)
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["hood_darkest"], alpha),
                                 (bx, by), (tx, ty), 3)
                pygame.draw.line(surface, (*_NS_vorenmarr.PALETTE["hood_dark"], alpha),
                                 (bx, by), (tx, ty), 1)
                pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_hot"], alpha), (tx, ty, 1, 1))

        # Glowing red eyes.
        for eye_x in (hx - 3, hx + 2):
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
                             (eye_x - 1, hy - 2, 4, 3))
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_mid"], alpha),
                             (eye_x, hy - 2, 3, 2))
            pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_white"], alpha),
                             (eye_x + 1, hy - 1, 1, 1))

        # Mouth (fanged).
        pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["shadow_deep"], alpha),
                         (hx - 4, hy + 3, 9, 3))
        pygame.draw.rect(surface, (*_NS_vorenmarr.PALETTE["fire_dark"], alpha),
                         (hx - 3, hy + 4, 7, 1))
        for tx in range(-3, 4, 2):
            pygame.draw.rect(surface, _NS_vorenmarr.PALETTE["hood_mid"], (hx + tx, hy + 3, 1, 2))


# ====================================================================
# NYXARATH
# ====================================================================
class _NS_nyxarath:
    """Namespace nyxarath - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    PALETTE = {
        # Shadow body (very dark with red inner glow)
        "shadow_pit": (2, 2, 3),
        "shadow_black": (8, 5, 6),
        "shadow_darkest": (16, 10, 12),
        "shadow_dark": (32, 18, 22),
        "shadow_mid": (55, 28, 32),
        "shadow_edge": (85, 42, 45),

        # Fire/soul inner glow (red-orange)
        "fire_darkest": (35, 5, 5),
        "fire_dark": (95, 15, 12),
        "fire_mid": (180, 35, 25),
        "fire_light": (240, 75, 45),
        "fire_hot": (255, 145, 80),
        "fire_white": (255, 225, 180),

        # Bone (horns, teeth, ribs)
        "bone_darkest": (30, 22, 18),
        "bone_dark": (65, 52, 42),
        "bone_mid": (130, 110, 90),
        "bone_light": (200, 180, 155),
        "bone_shine": (240, 225, 195),

        # Souls (pale green-white)
        "soul_dark": (30, 65, 55),
        "soul_mid": (110, 180, 155),
        "soul_light": (220, 250, 235),

        # Blood pool
        "blood_dark": (25, 5, 8),
        "blood_mid": (85, 15, 15),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _alpha(v):
        return max(0, min(255, int(v)))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxarath._clamp(color)
        if _NS_nyxarath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxarath._clamp(color)
        if _NS_nyxarath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)


    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxarath._clamp(color), points)


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
    def draw_nyxarath(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxarath._detect_moving(boss)
        _NS_nyxarath._update_nyxarath_attack_anim(boss)
        attacking = (
            getattr(boss, "_nyx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ground effects (behind).
        _NS_nyxarath._draw_hell_aura(surface, x, y, pulse)
        _NS_nyxarath._draw_dark_ground_ring(surface, x, y + 34, pulse, active_skill)

        if active_skill == "e":
            _NS_nyxarath._draw_presence_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxarath._draw_requiem_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_nyxarath._draw_nyxarath_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxarath._draw_nyxarath_walk(surface, boss, x, y)
        else:
            _NS_nyxarath._draw_nyxarath_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_nyxarath._draw_shadowraze(surface, boss, x, y, skill_timer)
        elif active_skill == "w":
            _NS_nyxarath._draw_necromastery(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxarath._draw_presence_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxarath._draw_requiem_foreground(surface, boss, x, y, skill_timer, pulse)


    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_nyxarath_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyx_previous_timer", 0))
        active = bool(getattr(boss, "_nyx_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nyx_attack_active = True
            boss._nyx_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nyx_attack_frame = int(
                getattr(boss, "_nyx_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._nyx_attack_active = False
            boss._nyx_attack_frame = 0
            active = False

        boss._nyx_previous_timer = timer
        boss._nyx_attack_progress = (
            min(1.0, getattr(boss, "_nyx_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _detect_moving(boss):
        if not hasattr(boss, "_nyx_last_x"):
            boss._nyx_last_x = boss.x
            boss._nyx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nyx_last_x)
        dy = abs(boss.y - boss._nyx_last_y)
        boss._nyx_last_x = boss.x
        boss._nyx_last_y = boss.y
        return dx + dy > 0.3


    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_nyxarath_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_nyxarath._draw_shadow(surface, x, y + 44)
        _NS_nyxarath._draw_shadow_wisps(surface, x, y + 30, boss.pulse)
        _NS_nyxarath._draw_nyxarath_body(surface, x, y + bob,
                            boss.direction, boss.pulse, "idle")


    def _draw_nyxarath_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_nyxarath._draw_shadow(surface, x + sway, y + 44)
        _NS_nyxarath._draw_shadow_wisps(surface, x + sway, y + 30, phase,
                            trail=True, facing=boss.direction)
        _NS_nyxarath._draw_nyxarath_body(surface, x + sway, y + bob,
                            boss.direction, phase, "walk")


    def _draw_nyxarath_attack(surface, boss, x, y):
        progress = getattr(boss, "_nyx_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction
        lift = int(math.sin(progress * math.pi) * 2)
        _NS_nyxarath._draw_shadow(surface, x + lunge, y + 44)
        _NS_nyxarath._draw_shadow_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_nyxarath._draw_nyxarath_body(surface, x + lunge, y - lift,
                            boss.direction, boss.pulse, "attack", progress)
        _NS_nyxarath._draw_basic_soul_bolt(surface, boss, x + lunge, y - lift, progress)


    # ============================================================
    # BODY
    # ============================================================
    def _draw_nyxarath_body(surface, cx, cy, facing, phase, action,
                             attack_progress=0):
        sway = int(math.sin(phase * 0.7) * (2 if action != "idle" else 1))
        if action == "attack":
            sway += int(math.sin(attack_progress * math.pi) * 3) * facing

        # Massive back spikes/tendrils behind body (silhouette).
        _NS_nyxarath._draw_back_tendrils(surface, cx, cy - 18, facing, phase)

        # Shadow lower body (flowing dark, menggantikan kaki).
        _NS_nyxarath._draw_shadow_lower(surface, cx, cy + 6, facing, phase, action)

        # Torso: skeletal ribs + inner fire.
        _NS_nyxarath._draw_nyxarath_torso(surface, cx, cy - 10, sway, facing, phase)

        # Arms with claws.
        _NS_nyxarath._draw_nyxarath_arms(surface, cx, cy - 8, facing, phase, action,
                            attack_progress)

        # Head with massive horn crown.
        _NS_nyxarath._draw_nyxarath_head(surface, cx, cy - 30, facing, phase)


    def _draw_shadow_lower(surface, cx, cy, facing, phase, action):
        """Bagian bawah — bayangan mengalir, menjuntai seperti jubah gelap."""
        flow1 = math.sin(phase * 0.5) * 3
        flow2 = math.cos(phase * 0.4) * 2
        flow3 = math.sin(phase * 0.7 + 1) * 2

        # Main shadow shape (menggantung ke bawah).
        main = [
            (cx - 16, cy - 8),
            (cx + 16, cy - 8),
            (cx + 20 + int(flow1), cy + 4),
            (cx + 22, cy + 16),
            (cx + 16, cy + 26),
            (cx + 8 + int(flow3), cy + 30),
            (cx + 2, cy + 32),
            (cx - 2, cy + 32),
            (cx - 8 + int(flow3), cy + 30),
            (cx - 16, cy + 26),
            (cx - 22, cy + 16),
            (cx - 20 - int(flow1), cy + 4),
        ]
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in main])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_black"], main)
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_darkest"], [
            (cx - 14, cy - 6),
            (cx + 14, cy - 6),
            (cx + 17 + int(flow1), cy + 4),
            (cx + 19, cy + 14),
            (cx + 14, cy + 22),
            (cx + 4, cy + 28),
            (cx - 4, cy + 28),
            (cx - 14, cy + 22),
            (cx - 19, cy + 14),
            (cx - 17 - int(flow1), cy + 4),
        ])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_dark"], [
            (cx - 10, cy - 3),
            (cx + 10, cy - 3),
            (cx + 12, cy + 4),
            (cx + 13, cy + 14),
            (cx + 8, cy + 22),
            (cx - 8, cy + 22),
            (cx - 13, cy + 14),
            (cx - 12, cy + 4),
        ])

        # Inner red glow (soul furnace inside body).
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["fire_darkest"], [
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 6, cy + 14),
            (cx + 3, cy + 22),
            (cx - 3, cy + 22),
            (cx - 6, cy + 14),
        ])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["fire_dark"], [
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 4, cy + 14),
            (cx + 2, cy + 20),
            (cx - 2, cy + 20),
            (cx - 4, cy + 14),
        ])
        # Bright inner core.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_alpha = _NS_nyxarath._alpha(200 * pulse)
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_light"], core_alpha),
                  (cx, cy + 12), 3)
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_hot"], core_alpha),
                  (cx, cy + 12), 2)
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"], (cx, cy + 12, 1, 1))

        # Cracks glowing red on shadow body.
        for i, (x1, y1, x2, y2) in enumerate([
            (-8, 2, -5, 12), (7, 4, 5, 14),
            (-11, 10, -8, 20), (10, 12, 7, 22),
        ]):
            crack_alpha = _NS_nyxarath._alpha(180 + math.sin(phase * 2 + i) * 40)
            pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["fire_dark"], crack_alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 2)
            pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["fire_light"], crack_alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 1)

        # Small shadow tendrils extending from bottom.
        for i, ox in enumerate((-12, -6, 0, 6, 12)):
            tendril_phase = (phase * 0.6 + i * 0.2) % 1.0
            tend_y = cy + 28 + int(tendril_phase * 6)
            alpha = _NS_nyxarath._alpha(240 * (1 - tendril_phase * 0.5))
            pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                             (cx + ox, cy + 22), (cx + ox + int(math.sin(phase + i) * 2),
                                                   tend_y), 3)
            pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["shadow_dark"], alpha),
                             (cx + ox, cy + 22), (cx + ox, tend_y), 1)
            # Ember at tip.
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_mid"], (cx + ox, tend_y, 1, 1))


    def _draw_nyxarath_torso(surface, cx, cy, sway, facing, phase):
        # Skeletal ribbed torso.
        body = [
            (cx - 12, cy - 6),
            (cx + 12, cy - 6),
            (cx + 13 + sway, cy + 6),
            (cx + 10, cy + 16),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 10, cy + 16),
            (cx - 13 - sway, cy + 6),
        ]
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in body])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_black"], body)
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_darkest"], [
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 11 + sway, cy + 6),
            (cx + 8, cy + 14),
            (cx - 8, cy + 14),
            (cx - 11 - sway, cy + 6),
        ])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_dark"], [
            (cx - 7, cy - 2),
            (cx + 7, cy - 2),
            (cx + 8, cy + 6),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 8, cy + 6),
        ])

        # RIB CAGE (khas Nevermore - bright red inside).
        # Central chest cavity.
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["fire_darkest"], [
            (cx - 6, cy),
            (cx + 6, cy),
            (cx + 5, cy + 12),
            (cx - 5, cy + 12),
        ])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["fire_dark"], [
            (cx - 4, cy + 1),
            (cx + 4, cy + 1),
            (cx + 4, cy + 11),
            (cx - 4, cy + 11),
        ])

        # Rib bone lines (curving down chest).
        for i, ry in enumerate((cy + 1, cy + 4, cy + 7, cy + 10)):
            rib_alpha = _NS_nyxarath._alpha(220 + math.sin(phase + i) * 20)
            # Left rib.
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["bone_dark"],
                             (cx - 6, ry), (cx - 1, ry + 1), 2)
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["bone_light"],
                             (cx - 5, ry), (cx - 1, ry + 1), 1)
            # Right rib.
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["bone_dark"],
                             (cx + 6, ry), (cx + 1, ry + 1), 2)
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["bone_light"],
                             (cx + 5, ry), (cx + 1, ry + 1), 1)

        # Central spine glowing.
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["fire_mid"], (cx, cy), (cx, cy + 12), 2)
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["fire_hot"], (cx, cy + 1), (cx, cy + 11), 1)

        # Bright chest core orb (heart of hellfire).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_r = int(3 * pulse) + 2
        # Glow halo.
        for r in range(core_r * 2, 0, -1):
            alpha = _NS_nyxarath._alpha(90 * (core_r * 2 - r) / (core_r * 2))
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_mid"], alpha), (cx, cy + 6), r)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_dark"], (cx, cy + 6), core_r)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_light"], (cx, cy + 6), max(1, core_r - 1))
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_hot"], (cx, cy + 6), max(1, core_r - 2))
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"], (cx, cy + 6, 1, 1))

        # Shoulders — spiky dark bulbs.
        for side in (-1, 1):
            sx = cx + side * 11
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_deep"], (sx + 1, cy + 1), 8)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_black"], (sx, cy - 1), 7)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_darkest"], (sx - side, cy - 2), 5)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_dark"], (sx - side * 2, cy - 3), 3)
            # Shoulder spike.
            _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_black"], [
                (sx + side * 4, cy - 6),
                (sx + side * 8, cy - 14),
                (sx + side * 6, cy - 3),
            ])
            _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_darkest"], [
                (sx + side * 4, cy - 6),
                (sx + side * 7, cy - 13),
                (sx + side * 5, cy - 3),
            ])
            # Red glow tip.
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_dark"], (sx + side * 7, cy - 13), 1)
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"],
                             (sx + side * 7, cy - 13, 1, 1))


    def _draw_back_tendrils(surface, cx, cy, facing, phase):
        """Spiky shadow tendrils behind body — silhouette background."""
        # Big central spikes fanning outward (like a demon crown/wings).
        for i, angle_base in enumerate((-2.5, -2.1, -1.7, -1.3, -0.9,
                                         -2.3, -1.9, -1.5, -1.1)):
            wave = math.sin(phase * 0.4 + i * 0.5) * 3
            angle = angle_base + math.sin(phase * 0.3 + i) * 0.15
            length = 22 + (i % 3) * 6

            tip_x = cx + int(math.cos(angle) * length + wave * 0.3)
            tip_y = cy + int(math.sin(angle) * length - 4)

            perp = angle + math.pi / 2
            base_a = (cx + int(math.cos(perp) * 3),
                      cy + int(math.sin(perp) * 3) + 4)
            base_b = (cx - int(math.cos(perp) * 3),
                      cy - int(math.sin(perp) * 3) + 4)

            # Dark spike triangle.
            _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_a[0] + 1, base_a[1] + 1),
                (base_b[0] + 1, base_b[1] + 1),
            ])
            _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_black"], [
                (tip_x, tip_y), base_a, base_b,
            ])
            _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_darkest"], [
                (tip_x, tip_y),
                ((base_a[0] + base_b[0]) // 2, (base_a[1] + base_b[1]) // 2),
                (base_b[0], base_b[1]),
            ])
            # Bright red glow on tip (khas Nevermore).
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_dark"], (tip_x, tip_y), 2)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_light"], (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (tip_x, tip_y, 1, 1))


    def _draw_nyxarath_head(surface, cx, cy, facing, phase):
        """Kepala demon dengan horn crown besar."""
        # Head base (angular, demonic).
        head_shape = [
            (cx - 9, cy - 3),
            (cx - 7, cy - 8),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 7, cy - 8),
            (cx + 9, cy - 3),
            (cx + 8, cy + 5),
            (cx + 4, cy + 10),
            (cx - 4, cy + 10),
            (cx - 8, cy + 5),
        ]
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_deep"],
              [(px + 1, py + 1) for px, py in head_shape])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_black"], head_shape)
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_darkest"], [
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 4),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
            (cx - 6, cy + 4),
        ])
        _NS_nyxarath._poly(surface, _NS_nyxarath.PALETTE["shadow_dark"], [
            (cx - 5, cy - 1),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 1),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])

        # HORN CROWN (khas Nevermore - massive curved horns).
        _NS_nyxarath._draw_horn_crown(surface, cx, cy - 8, phase)

        # GLOWING RED EYES (bright).
        for eye_x in (cx - 3, cx + 2):
            # Eye socket (dark deep).
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                             (eye_x - 1, cy - 4, 4, 3))
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_darkest"],
                             (eye_x, cy - 4, 3, 2))
            # Glow.
            pulse = math.sin(phase * 2 + eye_x) * 0.3 + 0.7
            glow_alpha = _NS_nyxarath._alpha(220 * pulse)
            pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_light"], glow_alpha),
                             (eye_x, cy - 4, 3, 2))
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (eye_x + 1, cy - 3, 1, 1))
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"], (eye_x + 1, cy - 3, 1, 1))

        # Fanged mouth (small jagged teeth).
        mouth_y = cy + 4
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                         (cx - 5, mouth_y, 11, 4))
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_darkest"],
                         (cx - 4, mouth_y + 1, 9, 2))
        # Teeth.
        for tx in range(-4, 5, 2):
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["bone_light"],
                             (cx + tx, mouth_y), (cx + tx, mouth_y + 2), 1)
        # Central mouth glow.
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_dark"], (cx - 2, mouth_y + 1, 4, 1))
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (cx, mouth_y + 1, 1, 1))

        # Face shadow lines / cheekbones.
        pygame.draw.line(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                         (cx - 6, cy - 1), (cx - 4, cy + 4), 1)
        pygame.draw.line(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                         (cx + 6, cy - 1), (cx + 4, cy + 4), 1)


    def _draw_horn_crown(surface, cx, cy, phase):
        """Massive curved horn crown - signature Nevermore feature."""
        # Central pair (biggest, curving back-up).
        for side in (-1, 1):
            # Base of horn.
            base_x = cx + side * 3
            base_y = cy + 2
            # Curl outward and up.
            mid_x = cx + side * 8
            mid_y = cy - 6
            tip_x = cx + side * 12
            tip_y = cy - 14

            # Draw curved horn as bezier.
            prev = (base_x, base_y)
            for step in range(1, 7):
                t = step / 6
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x
                         + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y
                         + t ** 2 * tip_y)
                width = max(1, 6 - step)
                _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                        (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), width + 1)
                _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_black"], prev, (bx, by), width)
                _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_darkest"], prev, (bx, by),
                        max(1, width - 2))
                if step > 3:
                    _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_dark"], prev, (bx, by), 1)
                prev = (bx, by)
            # Horn tip - sharp bone tip with red glow.
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["bone_dark"], prev, 2)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["bone_light"], prev, 1)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_hot"], (prev[0], prev[1] - 1), 1)

        # Smaller inner horns.
        for side in (-1, 1):
            base_x = cx + side * 1
            base_y = cy - 2
            tip_x = cx + side * 3
            tip_y = cy - 9
            _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                    (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 4)
            _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_black"], (base_x, base_y),
                    (tip_x, tip_y), 3)
            _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_darkest"], (base_x, base_y),
                    (tip_x, tip_y), 1)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_light"], (tip_x, tip_y), 1)

        # Outer smaller horns.
        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy + 1
            tip_x = cx + side * 9
            tip_y = cy - 3
            _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_black"],
                    (base_x, base_y), (tip_x, tip_y), 3)
            _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_darkest"],
                    (base_x, base_y), (tip_x, tip_y), 1)


    def _draw_nyxarath_arms(surface, cx, cy, facing, phase, action,
                              attack_progress):
        # Off-hand (claw hanging).
        off_dir = -facing
        off_sway = math.sin(phase * 0.7) * 2
        off_x = cx + off_dir * 15
        off_y = cy + 8 + int(off_sway)
        _NS_nyxarath._draw_arm(surface, cx + off_dir * 10, cy - 2,
                  off_x, off_y, phase)
        _NS_nyxarath._draw_claw_hand(surface, off_x, off_y + 3, off_dir, phase, charged=False)

        # Main hand (ranged cast with swing).
        weapon_x = cx + facing * 10
        weapon_y = cy - 2

        if action == "attack":
            p = max(0.0, min(1.0, attack_progress))
            # 3-phase: gather shadow → sling forward → recovery.
            if p < 0.30:
                # Gather: claw pulled back low, gathering shadow.
                t = p / 0.30
                t = t * t * (3 - 2 * t)
                angle = math.pi * 0.85 - t * 0.2
                distance = 14 + int(t * 8)
            elif p < 0.55:
                # Sling: whip forward extended.
                t = (p - 0.30) / 0.25
                t = 1 - (1 - t) ** 3
                angle = math.pi * 0.65 - t * math.pi * 1.05
                distance = 22 + int(t * 12)
            else:
                # Recovery.
                t = (p - 0.55) / 0.45
                t = t * t * (3 - 2 * t)
                angle = -math.pi * 0.40 + t * math.pi * 0.80
                distance = 34 - int(t * 14)

            hand_x = weapon_x + int(math.cos(angle) * distance) * facing
            hand_y = weapon_y + int(math.sin(angle) * distance)
            elbow_x = (weapon_x + hand_x) // 2 + 2 * facing
            elbow_y = (weapon_y + hand_y) // 2 - 3

            _NS_nyxarath._draw_arm(surface, weapon_x, weapon_y, elbow_x, elbow_y, phase)
            _NS_nyxarath._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, phase)
            _NS_nyxarath._draw_claw_hand(surface, hand_x, hand_y + 2, facing, phase,
                            charged=True, charge_amount=min(1.0, p * 2))
        else:
            idle_sway = math.sin(phase * 0.5) * 0.08
            hand_x = weapon_x + facing * 12
            hand_y = weapon_y + 8 + int(idle_sway * 8)
            _NS_nyxarath._draw_arm(surface, weapon_x, weapon_y, hand_x, hand_y, phase)
            _NS_nyxarath._draw_claw_hand(surface, hand_x, hand_y + 2, facing, phase,
                            charged=False)


    def _draw_arm(surface, x1, y1, x2, y2, phase):
        """Thin skeletal shadow arm."""
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_black"], (x1, y1), (x2, y2), 6)
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_darkest"], (x1, y1), (x2, y2), 4)
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_dark"], (x1 - 1, y1), (x2 - 1, y2), 2)
        _NS_nyxarath._aaline(surface, _NS_nyxarath.PALETTE["shadow_mid"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Red glow lines along arm (veins).
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length > 4:
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["fire_dark"],
                             (x1, y1), (x2, y2), 1)


    def _draw_claw_hand(surface, x, y, direction, phase, charged=False,
                         charge_amount=0):
        """Claw hand with 3-4 sharp fingers."""
        # Palm.
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_deep"], (x, y), 4)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_black"], (x, y - 1), 3)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_darkest"], (x - 1, y - 1), 2)

        # Claws (4 sharp fingers).
        for i, ang in enumerate((0.15, 0.45, 0.85, 1.25)):
            length = 5 + (i % 2)
            cx_tip = x + int(math.cos(ang) * length) * direction
            cy_tip = y + int(math.sin(ang) * length)
            # Dark claw with bone tip.
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["shadow_deep"], (x, y),
                             (cx_tip, cy_tip), 3)
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["shadow_black"], (x, y),
                             (cx_tip, cy_tip), 2)
            pygame.draw.line(surface, _NS_nyxarath.PALETTE["bone_dark"], (x, y),
                             (cx_tip, cy_tip), 1)
            # Sharp bone tip.
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["bone_light"], (cx_tip, cy_tip), 1)

        if charged:
            # Gathering shadow bolt in palm.
            charge_r = int(3 + charge_amount * 8)
            # Dark aura.
            for r in range(charge_r + 3, 0, -1):
                alpha = _NS_nyxarath._alpha(90 * (charge_r + 3 - r) / (charge_r + 3))
                _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), (x, y), r)
            # Red core.
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_darkest"], (x, y), charge_r)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_dark"], (x, y), max(1, charge_r - 1))
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_mid"], (x, y), max(1, charge_r - 3))
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_light"], (x, y), max(1, charge_r - 5))
            if charge_r > 5:
                _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_hot"], (x, y), 1)
                pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"], (x, y, 1, 1))

            # Spark particles around charge.
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                sx = x + int(math.cos(angle) * (charge_r + 3))
                sy = y + int(math.sin(angle) * (charge_r + 3))
                pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (sx, sy, 1, 1))


    # ============================================================
    # BASIC ATTACK — SOUL BOLT (ranged with swing)
    # ============================================================
    def _draw_basic_soul_bolt(surface, boss, x, y, progress):
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_nyxarath._target_position(boss, x, y)

        t = (progress - 0.55) / 0.45
        start_x = x + facing * 34
        start_y = y - 2
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (shadow + red flame).
        for i in range(6):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxarath._alpha(220 - i * 35)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), (px, py), 6 - i)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_darkest"], alpha), (px, py), 4 - i // 2)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha), (px, py), 3 - i // 2)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_light"], alpha), (px, py),
                      max(1, 2 - i // 2))

        # Bolt head (bright hellfire orb).
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_black"], (bx, by), 5)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_dark"], (bx, by), 4)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_mid"], (bx, by), 3)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_light"], (bx, by), 2)
        _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_hot"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.85:
            splash_t = (t - 0.85) / 0.15
            radius = int(5 + splash_t * 16)
            alpha = _NS_nyxarath._alpha(230 * (1 - splash_t))
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_light"], alpha), (tx, ty), radius, 2)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (tx, ty),
                      max(1, radius - 6), 1)
            for i in range(6):
                angle = i * math.pi / 3
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.6)
                pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (ex, ey, 2, 2))


    # ============================================================
    # FLOATING SHADOW WISPS (below body)
    # ============================================================
    def _draw_shadow_wisps(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Dark tendrils rising + red embers below floating body."""
        strength = 1.5 if intense else 1.0

        # Dark mist underglow (evil).
        mist = pygame.Surface((120, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = _NS_nyxarath._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                    (60 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        # Red inner glow on ground.
        for radius in range(20, 3, -3):
            alpha = _NS_nyxarath._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                    (60 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Shadow tendrils rising.
        for i, offset in enumerate((-20, -8, 6, 18, -14, 14, -2)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_nyxarath._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), (sx, sy), 5)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_darkest"], alpha), (sx, sy - 1), 3)
            # Red glow at tip.
            pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                             (sx, sy - 2, 2, 2))
            pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha),
                             (sx, sy - 3, 1, 1))

        # Red embers floating up.
        for i in range(6):
            ember_t = (phase * 0.7 + i * 0.2) % 1.0
            ex = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(ember_t * 22)
            alpha = _NS_nyxarath._alpha(240 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 1, 1))

        # Swirling dark motes around.
        for i in range(8):
            angle = phase * 0.7 + i * math.pi * 2 / 8
            radius = 26 + int(math.sin(phase + i * 0.6) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * 9)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["shadow_darkest"], (sx, sy), 2)
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_mid"], (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyxarath._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                          (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                                 (sx, sy - 1, 2, 2))


    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 4, 90, 10))
        # Red inner shadow.
        pygame.draw.ellipse(shadow, (60, 15, 15, 100), (12, 6, 76, 6))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_hell_aura(surface, x, y, phase):
        """Dark aura with red glow around body."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((160, 130), pygame.SRCALPHA)
        # Dark outer.
        for radius in range(70, 5, -5):
            alpha = _NS_nyxarath._alpha((70 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_nyxarath._aacircle(aura, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), (80, 65), radius)
        # Red inner glow.
        for radius in range(45, 5, -4):
            alpha = _NS_nyxarath._alpha((45 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_nyxarath._aacircle(aura, (*_NS_nyxarath.PALETTE["fire_dark"], alpha), (80, 65), radius)
        surface.blit(aura, (x - 80, y - 65))

        # Floating red embers.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 28 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (sx, sy, 1, 1))


    def _draw_dark_ground_ring(surface, x, y, phase, skill):
        """Dark ring on ground with red rune lines."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((120, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyxarath.PALETTE["shadow_black"], 190),
                            (5, 12, 110, 20), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxarath.PALETTE["fire_darkest"], 200),
                            (12, 14, 96, 16), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxarath.PALETTE["fire_dark"], 220),
                            (22, 16, 76, 12), 1)
        # Red rune dashes rotating.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 60 + int(math.cos(angle) * 32)
            y1 = 21 + int(math.sin(angle) * 6)
            x2 = 60 + int(math.cos(angle) * 50)
            y2 = 21 + int(math.sin(angle) * 9)
            pygame.draw.line(ring, (*_NS_nyxarath.PALETTE["fire_light"], 210),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxarath.PALETTE["fire_hot"], _NS_nyxarath._alpha(120 * pulse)),
                                (15, 8, 90, 30), 1)
        surface.blit(ring, (x - 60, y - 21))


    # ============================================================
    # SKILL: Q - SHADOWRAZE (fast bright line burst forward)
    # ============================================================
    def _draw_shadowraze(surface, boss, x, y, timer):
        """Bright red laser beam forward, hits distant point."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 3 phases: charge (0-0.25), beam (0.25-0.55), impact (0.55-1.0).
        tx, ty = _NS_nyxarath._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 6

        if progress < 0.25:
            # Charge glow.
            t = progress / 0.25
            cr = int(3 + t * 8)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_nyxarath._alpha(180 * (cr + 3 - r) / (cr + 3))
                _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_mid"], alpha),
                          (start_x, start_y), r)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_hot"], (start_x, start_y), 2)
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"],
                             (start_x, start_y, 1, 1))
        elif progress < 0.55:
            # Beam extending forward.
            t = (progress - 0.25) / 0.30
            beam_len = int(220 * t)
            end_x = start_x + facing * beam_len
            end_y = start_y

            # Multi-layer beam.
            alpha_mul = 1.0
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["shadow_black"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y - 1), (end_x, end_y - 1), 7)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_darkest"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y), (end_x, end_y), 6)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_dark"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y), (end_x, end_y), 4)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_mid"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y), (end_x, end_y), 3)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_light"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y), (end_x, end_y), 2)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_hot"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y), (end_x, end_y), 1)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_white"], _NS_nyxarath._alpha(240 * alpha_mul)),
                    (start_x, start_y), (end_x, end_y), 1)
            # Head of beam.
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_hot"], (end_x, end_y), 4)
            _NS_nyxarath._aacircle(surface, _NS_nyxarath.PALETTE["fire_white"], (end_x, end_y), 2)
        else:
            # Impact star burst.
            t = (progress - 0.55) / 0.45
            end_x = start_x + facing * 220
            end_y = start_y
            radius = int(8 + t * 30)
            alpha = _NS_nyxarath._alpha(240 * (1 - t))

            # Big glow.
            for r in range(radius, 0, -3):
                a = _NS_nyxarath._alpha(alpha * (radius - r) / radius)
                _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], a), (end_x, end_y), r)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (end_x, end_y),
                      max(1, radius // 3))
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_white"], alpha), (end_x, end_y),
                      max(1, radius // 5))

            # Star spikes.
            for i in range(8):
                angle = i * math.pi / 4
                ex = end_x + int(math.cos(angle) * radius)
                ey = end_y + int(math.sin(angle) * radius)
                pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha),
                                 (end_x, end_y), (ex, ey), 2)
                pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["fire_white"], alpha),
                                 (end_x, end_y), (ex, ey), 1)

            # Sparks flying out.
            for i in range(10):
                angle = phase = i * math.pi / 5 + t * 3
                sd = radius + int(math.sin(t * 5 + i) * 4)
                sx = end_x + int(math.cos(angle) * sd)
                sy = end_y + int(math.sin(angle) * sd)
                pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (sx, sy, 2, 2))


    # ============================================================
    # SKILL: W - NECROMASTERY (glowing skulls rising)
    # ============================================================
    def _draw_necromastery(surface, boss, x, y, timer, phase):
        """Red glowing skulls appear around body."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 5 skulls appearing around.
        positions = [(-38, 8), (-20, 14), (0, 18), (20, 14), (38, 8)]
        for i, (ox, oy) in enumerate(positions):
            appear_t = max(0.0, min(1.0, (progress - i * 0.10) * 2.5))
            if appear_t <= 0:
                continue
            # Skull rises from ground.
            rise = int((1 - appear_t) * 15)
            sx = x + ox
            sy = y + oy - int(appear_t * 15) + rise
            _NS_nyxarath._draw_soul_skull(surface, sx, sy, appear_t, phase + i * 0.5)

        # Central runic circle.
        for i in range(3):
            r = int(28 + i * 8 + progress * 6)
            alpha = _NS_nyxarath._alpha(180 - i * 40)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha), (x, y + 24), r, 2)


    def _draw_soul_skull(surface, cx, cy, appear_t, phase):
        """Small red-glowing skull."""
        alpha = _NS_nyxarath._alpha(240 * appear_t)
        size = 5

        # Glow behind.
        for r in range(size * 2, 0, -1):
            a = _NS_nyxarath._alpha(alpha * 0.6 * (size * 2 - r) / (size * 2))
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], a), (cx, cy), r)

        # Skull shape.
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), (cx, cy), size)
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_darkest"], alpha), (cx, cy - 1), size - 1)
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha), (cx - 1, cy - 1), size - 2)
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_mid"], alpha), (cx - 1, cy - 2), size - 3)

        # Eye sockets.
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["shadow_deep"], alpha),
                         (cx - 2, cy - 1, 2, 2))
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["shadow_deep"], alpha),
                         (cx + 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (cx - 2, cy - 1, 1, 1))
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (cx + 1, cy - 1, 1, 1))

        # Jaw line.
        pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["shadow_deep"], alpha),
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

        # Rising ember.
        ember_y = cy - int(phase * 4) % 8 - 4
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (cx, ember_y, 1, 1))


    # ============================================================
    # SKILL: E - PRESENCE OF THE DARK LORD (aura + minion silhouettes)
    # ============================================================
    def _draw_presence_ground(surface, boss, x, y, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big expanding dark ring.
        for i in range(3):
            r = int(30 + i * 15 + progress * 20)
            alpha = _NS_nyxarath._alpha(180 - i * 40)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                      (x, y + 34), r, 3)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                      (x, y + 34), r, 1)


    def _draw_presence_foreground(surface, boss, x, y, timer, phase):
        """Vertical red columns + minion silhouettes rising."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Vertical light pillars around body.
        positions = [-45, -25, -5, 15, 35]
        for i, ox in enumerate(positions):
            pillar_t = max(0.0, min(1.0, (progress - i * 0.08) * 2))
            if pillar_t <= 0:
                continue
            px = x + ox
            py = y + 34
            height = int(40 * pillar_t)
            alpha = _NS_nyxarath._alpha(200 * pillar_t)
            # Dark base.
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                    (px, py), (px, py - height), 5)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_darkest"], alpha),
                    (px, py), (px, py - height), 4)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                    (px, py), (px, py - height), 2)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_light"], alpha),
                    (px, py), (px, py - height), 1)
            # Ground splash.
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (px, py), 3)
            # Rising sparks.
            for j in range(3):
                spark_t = (phase * 2 + j * 0.4) % 1.0
                sy = py - int(spark_t * height)
                pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha),
                                 (px, sy, 1, 1))

        # Minion silhouettes rising at base of each pillar.
        for i, ox in enumerate(positions):
            appear_t = max(0.0, min(1.0, (progress - 0.3 - i * 0.05) * 2))
            if appear_t <= 0:
                continue
            _NS_nyxarath._draw_minion_silhouette(surface, x + ox, y + 30, appear_t, phase + i)


    def _draw_minion_silhouette(surface, cx, cy, appear_t, phase):
        """Small demon minion silhouette."""
        alpha = _NS_nyxarath._alpha(220 * appear_t)
        rise = int((1 - appear_t) * 15)
        cy += rise
        # Body.
        _NS_nyxarath._poly(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), [
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 5, cy - 2),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
            (cx - 5, cy - 2),
        ])
        # Head with tiny horns.
        _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha), (cx, cy - 10), 3)
        pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                         (cx - 2, cy - 12), (cx - 3, cy - 15), 1)
        pygame.draw.line(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                         (cx + 2, cy - 12), (cx + 3, cy - 15), 1)
        # Red eyes.
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (cx - 1, cy - 10, 1, 1))
        pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (cx + 1, cy - 10, 1, 1))


    # ============================================================
    # SKILL: R - REQUIEM OF SOULS (ultimate - red waves & pillars)
    # ============================================================
    def _draw_requiem_ground(surface, boss, x, y, timer, phase):
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Massive expanding dark ring.
        max_r = 110
        r = int(max_r * progress)
        for i in range(4):
            ring_r = max(0, r - i * 12)
            alpha = _NS_nyxarath._alpha(200 - i * 40)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                      (x, y + 34), ring_r, 3)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                      (x, y + 34), ring_r, 1)

        # Rotating runes.
        for i in range(16):
            angle = phase * 0.4 + i * math.pi / 8
            rune_r = max(15, r - 8)
            px = x + int(math.cos(angle) * rune_r)
            py = y + 34 + int(math.sin(angle) * rune_r * 0.55)
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_hot"], (px, py, 2, 2))
            pygame.draw.rect(surface, _NS_nyxarath.PALETTE["fire_white"], (px, py, 1, 1))


    def _draw_requiem_foreground(surface, boss, x, y, timer, phase):
        """Many vertical soul pillars erupt in ring, then explode."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Number of pillars increases with progress.
        num_pillars = 14
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars + phase * 0.1
            pillar_t = max(0.0, min(1.0, (progress - 0.15 - i * 0.03) * 1.8))
            if pillar_t <= 0:
                continue
            # Pillar spreads outward as time progresses.
            distance = 30 + int(pillar_t * 70)
            px = x + int(math.cos(angle) * distance)
            py = y + 34 + int(math.sin(angle) * distance * 0.55)

            # Vertical pillar of red hellfire.
            height = int(50 * min(1.0, pillar_t * 2))
            if height < 4:
                continue
            alpha = _NS_nyxarath._alpha(240 * (1 - abs(pillar_t - 0.5) * 1.2))

            # Layered vertical beam.
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["shadow_black"], alpha),
                    (px, py), (px, py - height), 6)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_darkest"], alpha),
                    (px, py), (px, py - height), 5)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_dark"], alpha),
                    (px, py), (px, py - height), 3)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_mid"], alpha),
                    (px, py), (px, py - height), 2)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha),
                    (px, py), (px, py - height), 1)
            _NS_nyxarath._aaline(surface, (*_NS_nyxarath.PALETTE["fire_white"], alpha),
                    (px, py - 5), (px, py - height + 2), 1)

            # Base ground splash.
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha), (px, py), 4)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_white"], alpha), (px, py), 2)

            # Peak sparks.
            peak_y = py - height
            for j in range(4):
                spark_angle = j * math.pi / 2 + phase * 2
                sx = px + int(math.cos(spark_angle) * 3)
                sy = peak_y + int(math.sin(spark_angle) * 3)
                pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_nyxarath.PALETTE["fire_white"], alpha),
                                 (sx, sy, 1, 1))

        # Central massive orb (source).
        if progress < 0.5:
            core_r = int(15 + progress * 40)
            core_alpha = _NS_nyxarath._alpha(220 * (1 - progress * 1.5))
            for r in range(core_r, 0, -2):
                a = _NS_nyxarath._alpha(core_alpha * (core_r - r) / core_r)
                _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_dark"], a), (x, y + 15), r)
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_hot"], core_alpha), (x, y + 15),
                      max(1, core_r // 3))
            _NS_nyxarath._aacircle(surface, (*_NS_nyxarath.PALETTE["fire_white"], core_alpha), (x, y + 15),
                      max(1, core_r // 5))


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_malzareth(surface, boss, x, y):
    """Entry point malzareth."""
    return _NS_malzareth.draw_malzareth(surface, boss, x, y)

def draw_akashari(surface, boss, x, y):
    """Entry point akashari."""
    return _NS_akashari.draw_akashari(surface, boss, x, y)

def draw_vorenmarr(surface, boss, x, y):
    """Entry point vorenmarr."""
    return _NS_vorenmarr.draw_vorenmarr(surface, boss, x, y)

def draw_nyxarath(surface, boss, x, y):
    """Entry point nyxarath."""
    return _NS_nyxarath.draw_nyxarath(surface, boss, x, y)
