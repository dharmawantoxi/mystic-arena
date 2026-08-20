"""
bosses/level11.py - Semua boss Level 11

Berisi:
  - aeralith    (mini boss - RANGED wind)
  - aurex       (mini boss - omega knight)
  - nyxareva    (mini boss - fallen queen)
  - thalakryon  (TRUE BOSS - Mermidon Abyssal)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# aeralith.py
# ====================================================================



class _NS_aeralith:
    """
    Mini-boss: Aeralith, The West Gale
    Style: layered HD-ish polygon + glow + mist + ground runes (mirip gaya VHORETHZIR)
    Basic attack: RANGED (wind crescent projectile)
    Skills (visual only): Q Tailwind, W Wind Blade, E Vacuum, R Sky Rider
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        "shadow": (0, 0, 0),
        "shadow_deep": (6, 8, 12),
        "ink": (7, 10, 14),

        # Wind teal/mint
        "wind_darkest": (6, 20, 26),
        "wind_dark": (14, 52, 62),
        "wind_mid": (48, 132, 150),
        "wind_light": (130, 230, 220),
        "wind_hot": (205, 255, 245),
        "wind_shine": (245, 255, 255),

        # Acid green flecks like ref
        "leaf_mid": (85, 190, 75),
        "leaf_light": (170, 245, 120),

        # Armor gold/bronze
        "gold_darkest": (30, 22, 10),
        "gold_dark": (78, 52, 18),
        "gold_mid": (155, 110, 35),
        "gold_light": (230, 190, 90),
        "gold_shine": (255, 245, 205),

        # Steel/obsidian
        "steel_dark": (22, 26, 34),
        "steel_mid": (60, 72, 92),
        "steel_light": (145, 165, 200),

        "white": (255, 255, 255),
    }

    # -------------------------
    # helpers
    # -------------------------
    @staticmethod
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    @staticmethod
    def _alpha(v):
        return max(0, min(255, int(v)))

    @staticmethod
    def _aacircle(surf, color, center, radius, width=0):
        color = _NS_aeralith._clamp(color)
        if _NS_aeralith.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surf, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surf, color, center, radius, width)

    @staticmethod
    def _aaline(surf, color, a, b, width=1):
        color = _NS_aeralith._clamp(color)
        if _NS_aeralith.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surf, color, a, b)
                return
            except Exception:
                pass
        pygame.draw.line(surf, color, a, b, width)

    @staticmethod
    def _poly(surf, color, pts):
        pygame.draw.polygon(surf, _NS_aeralith._clamp(color), pts)

    @staticmethod
    def _target_position(boss, x, y):
        t = getattr(boss, "target", None)
        if t is not None and getattr(t, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (t.x - getattr(boss, "x", x)) / scale
            ty = y + (t.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # -------------------------
    # state
    # -------------------------
    @staticmethod
    def _detect_moving(boss):
        if not hasattr(boss, "_aer_last_x"):
            boss._aer_last_x = boss.x
            boss._aer_last_y = boss.y
            return False
        dx = abs(boss.x - boss._aer_last_x)
        dy = abs(boss.y - boss._aer_last_y)
        boss._aer_last_x = boss.x
        boss._aer_last_y = boss.y
        return dx + dy > 0.35

    @staticmethod
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aer_previous_timer", 0))
        active = bool(getattr(boss, "_aer_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aer_attack_active = True
            boss._aer_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._aer_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._aer_attack_frame = int(getattr(boss, "_aer_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._aer_attack_active = False
            boss._aer_attack_frame = 0
            active = False

        boss._aer_previous_timer = timer
        boss._aer_attack_progress = (
            min(1.0, getattr(boss, "_aer_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # -------------------------
    # ENTRY
    # -------------------------
    @staticmethod
    def draw_aeralith(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        facing = int(getattr(boss, "direction", 1))
        moving = _NS_aeralith._detect_moving(boss)
        _NS_aeralith._update_attack_anim(boss)

        active_skill = getattr(boss, "active_skill", None)  # 'q','w','e','r'
        skill_timer = int(getattr(boss, "active_skill_timer", 0))

        attacking = bool(getattr(boss, "_aer_attack_active", False)) or (
            getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 48) - 15
        )

        # Background
        _NS_aeralith._draw_aura(surface, x, y - 12, pulse)
        _NS_aeralith._draw_ground_runes(surface, x, y + 48, pulse, active_skill)

        # Skill ground (behind)
        if active_skill == "e":
            _NS_aeralith._draw_vacuum_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_aeralith._draw_tailwind_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aeralith._draw_sky_rider_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_aeralith._draw_attack_ranged(surface, boss, x, y)
        elif moving:
            _NS_aeralith._draw_walk(surface, boss, x, y)
        else:
            _NS_aeralith._draw_idle(surface, boss, x, y)

        # Skill foreground
        if active_skill == "w":
            _NS_aeralith._draw_wind_blade_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aeralith._draw_vacuum_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_aeralith._draw_tailwind_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aeralith._draw_sky_rider_foreground(surface, boss, x, y, skill_timer, pulse)

        # front particles
        _NS_aeralith._draw_leaf_sparks(surface, x, y + 10, pulse, facing)

    # -------------------------
    # poses
    # -------------------------
    @staticmethod
    def _draw_idle(surface, boss, x, y):
        phase = boss.pulse
        bob = int(math.sin(phase * 1.1) * 5)
        _NS_aeralith._draw_shadow(surface, x, y + 52)
        _NS_aeralith._draw_platform_swirl(surface, x, y + 48, phase, 0.9)
        _NS_aeralith._draw_wind_mist(surface, x, y + 38, phase, intensity=0.9)
        _NS_aeralith._draw_body(surface, x, y + bob, boss.direction, phase, action="idle")

    @staticmethod
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 5)
        _NS_aeralith._draw_shadow(surface, x + sway, y + 52)
        _NS_aeralith._draw_platform_swirl(surface, x + sway, y + 48, phase, 1.15)
        _NS_aeralith._draw_wind_mist(surface, x + sway, y + 38, phase, intensity=1.05, trail=True, facing=boss.direction)
        _NS_aeralith._draw_body(surface, x + sway, y + bob, boss.direction, phase, action="walk")

    @staticmethod
    def _draw_attack_ranged(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_aer_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_aer_attack_dir", None)
        if facing is None:
            facing = boss.direction


        lean = int(math.sin(progress * math.pi) * 5)
        lift = int(math.sin(progress * math.pi) * 3)

        _NS_aeralith._draw_shadow(surface, x, y + 52)
        _NS_aeralith._draw_platform_swirl(surface, x, y + 48, boss.pulse, 1.25)
        _NS_aeralith._draw_wind_mist(surface, x, y + 38, boss.pulse, intensity=1.2)

        _NS_aeralith._draw_body(
            surface, x + facing * lean, y - lift, facing, boss.pulse,
            action="attack_ranged", cast=progress
        )

        # Basic projectile (smaller than W)
        _NS_aeralith._draw_wind_projectile(surface, boss, x, y, progress, power=1.0)

    # -------------------------
    # body (more “ref-like”: wind wings + armored knight + spear)
    # -------------------------
    @staticmethod
    def _draw_body(surface, cx, cy, facing, phase, action="idle", cast=0.0):
        # Wind wings behind (large sweeping swirls)
        _NS_aeralith._draw_wind_wings(surface, cx - facing * 6, cy - 10, facing, phase, action, cast)

        # Lower body: wind funnel tail
        _NS_aeralith._draw_wind_tail(surface, cx - facing * 2, cy + 20, facing, phase, action)

        # Torso silhouette + outline (HD feel)
        torso = [
            (cx - 12, cy - 6),
            (cx - 14, cy - 20),
            (cx - 7, cy - 32),
            (cx + 7, cy - 32),
            (cx + 14, cy - 20),
            (cx + 12, cy - 6),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
        ]
        # outline/back ink
        _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["ink"], [(x + 1, y + 1) for x, y in torso])
        _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["steel_dark"], torso)

        # gold plate overlay (chest)
        plate = [
            (cx - 10, cy - 8),
            (cx - 11, cy - 19),
            (cx - 5, cy - 29),
            (cx + 5, cy - 29),
            (cx + 11, cy - 19),
            (cx + 10, cy - 8),
            (cx + 6, cy + 8),
            (cx - 6, cy + 8),
        ]
        _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["gold_dark"], plate)
        _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["gold_mid"], [
            (cx - 8, cy - 10),
            (cx - 9, cy - 18),
            (cx - 4, cy - 27),
            (cx + 4, cy - 27),
            (cx + 9, cy - 18),
            (cx + 8, cy - 10),
            (cx + 5, cy + 6),
            (cx - 5, cy + 6),
        ])
        pygame.draw.line(surface, _NS_aeralith.PALETTE["gold_shine"], (cx - 4, cy - 16), (cx + 4, cy - 16), 1)

        # Shoulder pauldrons
        for sx in (-12, 12):
            px = cx + sx
            py = cy - 22
            _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["ink"], [
                (px - 7, py + 7), (px - 10, py), (px, py - 7), (px + 10, py), (px + 7, py + 7), (px, py + 10)
            ])
            _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["gold_darkest"], [
                (px - 7, py + 7), (px - 10, py), (px, py - 7), (px + 10, py), (px + 7, py + 7), (px, py + 10)
            ])
            _NS_aeralith._poly(surface, _NS_aeralith.PALETTE["gold_mid"], [
                (px - 6, py + 6), (px - 8, py), (px, py - 5), (px + 8, py), (px + 6, py + 6), (px, py + 8)
            ])
            pygame.draw.rect(surface, _NS_aeralith.PALETTE["gold_shine"], (px, py - 2, 1, 1))

        # Chest gem (wind core)
        gem_x = cx + facing * 2
        gem_y = cy - 16
        _NS_aeralith._draw_core_gem(surface, gem_x, gem_y, phase)

        # Helm/head
        head_x = cx + facing * 1
        head_y = cy - 38 + int(math.sin(phase * 1.1) * 2)
        _NS_aeralith._draw_helm(surface, head_x, head_y, facing, phase)

        # Weapon: spear + wind blade
        if action == "attack_ranged":
            weapon_angle = (-0.20 * facing) + (0.22 * math.sin(cast * math.pi)) * facing
        else:
            weapon_angle = (-0.35 * facing) + (0.10 * math.sin(phase * 0.9)) * facing

        _NS_aeralith._draw_spear(surface, cx + facing * 12, cy - 14, facing, phase, weapon_angle, action, cast)

    @staticmethod
    def _draw_core_gem(surface, cx, cy, phase):
        pulse = math.sin(phase * 2.0) * 0.25 + 0.75
        for r in range(14, 0, -2):
            a = _NS_aeralith._alpha((14 - r) * 12 * pulse)
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_mid"], a), (cx, cy), r)
        _NS_aeralith._aacircle(surface, _NS_aeralith.PALETTE["wind_light"], (cx, cy), 4)
        _NS_aeralith._aacircle(surface, _NS_aeralith.PALETTE["wind_shine"], (cx, cy), 1)

    @staticmethod
    def _draw_helm(surface, cx, cy, facing, phase):
        # base + outline
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["ink"], (cx - 9, cy - 9, 18, 16))
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["steel_dark"], (cx - 8, cy - 9, 16, 16))
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["gold_dark"], (cx - 8, cy - 9, 16, 3))

        # visor glow
        slit_y = cy - 2
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["shadow_deep"], (cx - 6, slit_y, 12, 3))
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["wind_dark"], (cx - 5, slit_y, 10, 3))
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["wind_light"], (cx - 2, slit_y + 1, 5, 1))
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["wind_shine"], (cx + 2, slit_y + 1, 1, 1))

        # plume
        plume = pygame.Surface((50, 30), pygame.SRCALPHA)
        ox, oy = cx - 25, cy - 18
        for i in range(9):
            t = i / 8
            px = 25 + int((6 + 16 * t) * facing)
            py = 18 - int(14 * t) + int(math.sin(phase * 1.6 + i * 0.6) * 2)
            a = _NS_aeralith._alpha(135 - i * 10)
            _NS_aeralith._aaline(plume, (*_NS_aeralith.PALETTE["wind_light"], a), (25, 22), (px, py), 4)
            _NS_aeralith._aaline(plume, (*_NS_aeralith.PALETTE["wind_mid"], a), (25, 22), (px, py), 2)
            _NS_aeralith._aaline(plume, (*_NS_aeralith.PALETTE["wind_dark"], a), (25, 22), (px, py), 1)
        surface.blit(plume, (ox, oy))

    @staticmethod
    def _draw_spear(surface, ax, ay, facing, phase, angle, action, cast):
        # Convert "angle factor" to a usable vector
        ang = angle
        shaft_len = 26
        blade_len = 30

        sx = int(math.cos(ang) * shaft_len) * facing
        sy = int(math.sin(ang) * shaft_len)
        bx = int(math.cos(ang) * (shaft_len + blade_len)) * facing
        by = int(math.sin(ang) * (shaft_len + blade_len))

        base = (ax - sx, ay - sy)
        mid = (ax, ay)
        tip = (ax + bx, ay + by)

        # arm + grip
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["shadow_deep"], (ax - facing * 8 + 2, ay + 2), (ax + 2, ay + 2), 6)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["gold_dark"], (ax - facing * 8, ay), (ax, ay), 6)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["gold_mid"], (ax - facing * 8, ay - 1), (ax, ay - 1), 4)

        # shaft
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["gold_darkest"], base, mid, 5)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["gold_mid"], base, mid, 3)
        pygame.draw.rect(surface, _NS_aeralith.PALETTE["gold_shine"], (ax, ay, 1, 1))

        # wind blade (tapered)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_darkest"], mid, tip, 8)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_dark"], mid, tip, 6)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_mid"], mid, tip, 3)
        _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_light"], mid, tip, 1)

        # edge sparks
        _NS_aeralith._aacircle(surface, _NS_aeralith.PALETTE["wind_light"], tip, 4)
        _NS_aeralith._aacircle(surface, _NS_aeralith.PALETTE["wind_shine"], tip, 1)

        # cast charge at tip
        if action == "attack_ranged":
            strength = max(0.0, math.sin(cast * math.pi))
            if strength > 0.05:
                for r in range(18, 0, -2):
                    a = _NS_aeralith._alpha(strength * (18 - r) * 10)
                    _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_light"], a), tip, r)
                pygame.draw.rect(surface, _NS_aeralith.PALETTE["wind_shine"], (tip[0], tip[1], 1, 1))

    # -------------------------
    # wind wings / tail / platform
    # -------------------------
    @staticmethod
    def _draw_wind_wings(surface, cx, cy, facing, phase, action, cast):
        w, h = 220, 150
        wing = pygame.Surface((w, h), pygame.SRCALPHA)
        pulse = math.sin(phase * 0.9) * 0.25 + 0.75
        intensity = 1.0 + (0.25 if action.startswith("attack") else 0.0)

        # Two big ribbons like “wings”
        origin = (110, 85)
        for side in (-1, 1):
            for i in range(9):
                t = i / 8
                a = _NS_aeralith._alpha((150 - i * 14) * intensity * pulse)
                # curve endpoints
                ex = origin[0] + int((60 + 55 * t) * (-facing) + (18 * side) * (1 - t))
                ey = origin[1] - int((40 + 35 * t) * (0.6 + 0.4 * side * 0.25)) + int(math.sin(phase * 1.4 + i) * 4)
                mx = origin[0] + int((30 + 25 * t) * (-facing) + 22 * side)
                my = origin[1] - int(22 + 10 * t) + int(math.cos(phase * 1.2 + i * 0.7) * 4)

                # draw as segmented quadratic bezier-ish
                prev = origin
                steps = 10
                for s in range(1, steps + 1):
                    u = s / steps
                    bx = int((1-u)*(1-u)*origin[0] + 2*(1-u)*u*mx + u*u*ex)
                    by = int((1-u)*(1-u)*origin[1] + 2*(1-u)*u*my + u*u*ey)
                    thick = max(1, 10 - i)  # outer thicker
                    _NS_aeralith._aaline(wing, (*_NS_aeralith.PALETTE["wind_mid"], a), prev, (bx, by), thick)
                    _NS_aeralith._aaline(wing, (*_NS_aeralith.PALETTE["wind_light"], a), prev, (bx, by), max(1, thick - 4))
                    prev = (bx, by)

        # soft fog sheet behind wings
        for r in range(70, 10, -5):
            a = _NS_aeralith._alpha((70 - r) * 2.0 * pulse * intensity)
            if a > 0:
                pygame.draw.ellipse(wing, (*_NS_aeralith.PALETTE["wind_dark"], a), (110 - r*1.4, 85 - r*0.4, int(r*2.8), int(r*0.9)))

        surface.blit(wing, (cx - w//2, cy - h//2))

    @staticmethod
    def _draw_wind_tail(surface, cx, cy, facing, phase, action):
        # funnel-like tail
        segments = 9
        points = [(cx, cy)]
        amp = 10 if action == "walk" else 8
        for i in range(1, segments + 1):
            t = i / segments
            x = cx - facing * int(6 + 26 * t)
            y = cy + int(4 + 26 * t)
            y += int(math.sin(phase * 1.7 + t * 4.2) * (amp * (1 - 0.35 * t)))
            points.append((x, y))

        for i in range(len(points) - 1):
            thick = max(2, 12 - i)
            _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["shadow_deep"],
                                 (points[i][0] + 2, points[i][1] + 2),
                                 (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                 thick + 1)
            _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_darkest"], points[i], points[i + 1], thick)
            _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_dark"], points[i], points[i + 1], max(1, thick - 2))
            _NS_aeralith._aaline(surface, _NS_aeralith.PALETTE["wind_mid"],
                                 (points[i][0], points[i][1] - 1),
                                 (points[i + 1][0], points[i + 1][1] - 1),
                                 max(1, thick - 5))

        end = points[-1]
        _NS_aeralith._aacircle(surface, _NS_aeralith.PALETTE["wind_light"], end, 4)
        _NS_aeralith._aacircle(surface, _NS_aeralith.PALETTE["wind_shine"], end, 1)

    @staticmethod
    def _draw_platform_swirl(surface, cx, cy, phase, strength=1.0):
        # rotating swirl disc under boss
        disc = pygame.Surface((210, 90), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(78, 10, -4):
            a = _NS_aeralith._alpha((78 - r) * 1.6 * pulse * strength)
            pygame.draw.ellipse(disc, (*_NS_aeralith.PALETTE["wind_darkest"], a), (105 - r, 45 - r//3, r*2, (r*2)//3))
        # arc strokes
        for i in range(12):
            ang = phase * 0.7 + i * math.pi / 6
            x1 = 105 + int(math.cos(ang) * 70)
            y1 = 45 + int(math.sin(ang) * 18)
            x2 = 105 + int(math.cos(ang + 0.8) * 40)
            y2 = 45 + int(math.sin(ang + 0.8) * 10)
            a = _NS_aeralith._alpha(110 * pulse * strength)
            _NS_aeralith._aaline(disc, (*_NS_aeralith.PALETTE["wind_mid"], a), (x2, y2), (x1, y1), 3)
            _NS_aeralith._aaline(disc, (*_NS_aeralith.PALETTE["wind_light"], a), (x2, y2), (x1, y1), 1)
        surface.blit(disc, (cx - 105, cy - 45))

    # -------------------------
    # ambient aura / ground / mist
    # -------------------------
    @staticmethod
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(16, 0, -1):
            alpha = max(0, (16 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - radius, 16 - radius, 126 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (4, 6, 8, 175), (6, 10, 138, 14))
        surface.blit(shadow, (x - 75, y - 16))

    @staticmethod
    def _draw_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.55) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)

        for radius in range(105, 5, -6):
            alpha = _NS_aeralith._alpha((105 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_aeralith._aacircle(aura, (*_NS_aeralith.PALETTE["wind_darkest"], alpha), (130, 110), radius)
        for radius in range(75, 5, -5):
            alpha = _NS_aeralith._alpha((75 - radius) * 1.25 * pulse)
            if alpha > 0:
                _NS_aeralith._aacircle(aura, (*_NS_aeralith.PALETTE["wind_dark"], alpha), (130, 110), radius)
        for radius in range(46, 5, -3):
            alpha = _NS_aeralith._alpha((46 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_aeralith._aacircle(aura, (*_NS_aeralith.PALETTE["wind_mid"], alpha), (130, 110), radius)

        surface.blit(aura, (x - 130, y - 110))

        # orbit motes
        for i in range(14):
            ang = phase * 0.35 + i * math.pi / 7
            rr = 44 + int(math.sin(phase + i) * 12)
            px = x + int(math.cos(ang) * rr)
            py = y + int(math.sin(ang) * rr * 0.55)
            c1 = _NS_aeralith.PALETTE["leaf_mid"] if i % 3 == 0 else _NS_aeralith.PALETTE["wind_light"]
            pygame.draw.rect(surface, c1, (px, py, 2, 2))
            pygame.draw.rect(surface, _NS_aeralith.PALETTE["wind_shine"], (px, py, 1, 1))

    @staticmethod
    def _draw_ground_runes(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 62), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_aeralith.PALETTE["wind_darkest"], 220), (6, 22, 178, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_aeralith.PALETTE["wind_dark"], 210), (16, 24, 158, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_aeralith.PALETTE["wind_mid"], 175), (32, 26, 126, 22), 1)

        # rotating rune ticks
        for i in range(14):
            ang = phase * 0.45 + i * math.pi / 7
            x1 = 95 + int(math.cos(ang) * 58)
            y1 = 34 + int(math.sin(ang) * 10)
            x2 = 95 + int(math.cos(ang) * 80)
            y2 = 34 + int(math.sin(ang) * 14)
            pygame.draw.line(ring, (*_NS_aeralith.PALETTE["wind_light"], 230), (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(
                ring,
                (*_NS_aeralith.PALETTE["wind_hot"], _NS_aeralith._alpha(160 * pulse)),
                (14, 14, 162, 46),
                1,
            )

        surface.blit(ring, (x - 95, y - 31))

    @staticmethod
    def _draw_wind_mist(surface, cx, cy, phase, intensity=1.0, trail=False, facing=1):
        mist = pygame.Surface((190, 66), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.25) * 0.25 + 0.75

        for radius in range(48, 6, -3):
            alpha = _NS_aeralith._alpha((48 - radius) * 2.2 * pulse * intensity)
            pygame.draw.ellipse(mist, (*_NS_aeralith.PALETTE["wind_darkest"], alpha),
                                (95 - radius * 2, 32 - radius // 3, radius * 4, max(3, radius // 2)))
        for radius in range(30, 6, -2):
            alpha = _NS_aeralith._alpha((30 - radius) * 3.0 * pulse * intensity)
            pygame.draw.ellipse(mist, (*_NS_aeralith.PALETTE["wind_dark"], alpha),
                                (95 - radius, 32 - radius // 4, radius * 2, max(2, radius // 3)))

        surface.blit(mist, (cx - 95, cy - 16))

        # float motes
        for i, off in enumerate((-44, -34, -24, -14, -4, 6, 16, 26, 36, 46)):
            t = (phase * 0.45 + i * 0.13) % 1.0
            sx = cx + off + int(math.sin(phase + i) * 3)
            sy = cy + 12 - int(t * 34)
            alpha = _NS_aeralith._alpha(210 * (1 - t) * intensity)
            if alpha > 0:
                _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_dark"], alpha), (sx, sy), 3)
                _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_light"], alpha), (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["wind_shine"], alpha), (sx, sy, 1, 1))

        if trail:
            for i in range(7):
                tx = cx - (i + 1) * 18 * facing
                ty = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_aeralith._alpha(160 - i * 22)
                if alpha <= 0:
                    continue
                _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_darkest"], alpha), (tx, ty), max(2, 8 - i))
                _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_mid"], alpha), (tx, ty), max(1, 6 - i))
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["leaf_light"], alpha), (tx, ty - 1, 2, 2))

    @staticmethod
    def _draw_leaf_sparks(surface, cx, cy, phase, facing):
        for i in range(10):
            t = (phase * 0.55 + i * 0.17) % 1.0
            px = cx + int(math.sin(phase * 1.7 + i) * 54) - int(22 * facing * (1 - t))
            py = cy - int(t * 30)
            a = _NS_aeralith._alpha(170 * (1 - t))
            if a > 0:
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["leaf_mid"], a), (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["leaf_light"], a), (px, py, 1, 1))

    # -------------------------
    # projectile (HD ribbon trail + crescent head)
    # -------------------------
    @staticmethod
    def _draw_wind_projectile(surface, boss, x, y, progress, power=1.0):
        if progress < 0.50:
            # charge sparkle at spear tip
            facing = boss.direction
            tip = (x + facing * 58, y - 22)
            pulse = max(0.0, math.sin(progress * math.pi))
            for r in range(14, 0, -2):
                a = _NS_aeralith._alpha(pulse * (14 - r) * 10)
                _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_light"], a), tip, r)
            return

        facing = boss.direction
        tx, ty = _NS_aeralith._target_position(boss, x, y)
        start = (x + facing * 58, y - 22)

        t = (progress - 0.50) / 0.50
        t = max(0.0, min(1.0, t))

        bx = int(start[0] + (tx - start[0]) * t)
        by = int(start[1] + (ty - start[1]) * t)

        # ribbon trail: draw stretched ellipses along path
        steps = 14 + int(6 * power)
        for i in range(steps):
            tt = max(0.0, t - i * (0.045 - 0.01 * min(1.0, power)))
            px = int(start[0] + (tx - start[0]) * tt)
            py = int(start[1] + (ty - start[1]) * tt)

            a = _NS_aeralith._alpha(230 - i * 14)
            w = max(3, int((22 + 8 * power) - i * 1.1))
            h = max(2, int(w * 0.45))
            # slight wobble like gust
            py += int(math.sin(boss.pulse * 2.2 + i) * 2)

            s = pygame.Surface((w * 2 + 2, h * 2 + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*_NS_aeralith.PALETTE["wind_darkest"], a), (1, 1, w * 2, h * 2))
            pygame.draw.ellipse(s, (*_NS_aeralith.PALETTE["wind_mid"], max(0, a - 45)), (2, 2, w * 2 - 2, h * 2 - 2))
            pygame.draw.ellipse(s, (*_NS_aeralith.PALETTE["wind_light"], max(0, a - 90)), (w // 2, h // 2, w + 2, h + 2))
            surface.blit(s, (px - (w + 1), py - (h + 1)))

            if i < 6:
                sx = px + int(math.sin(tt * 10 + i) * (w * 0.45))
                sy = py + int(math.cos(tt * 9 + i) * (h * 0.6))
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["leaf_light"], a), (sx, sy, 2, 2))

        # crescent head
        _NS_aeralith._draw_crescent_head(surface, (bx, by), facing, boss.pulse, scale=1.0 + 0.35 * power)

        # impact
        if t > 0.86:
            st = (t - 0.86) / 0.14
            st = max(0.0, min(1.0, st))
            rad = int(14 + st * (28 + 10 * power))
            a = _NS_aeralith._alpha(240 * (1 - st * 0.5))
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_mid"], a), (tx, ty), rad, 3)
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_light"], a), (tx, ty), max(6, rad - 10), 2)
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_shine"], a), (tx, ty), max(2, rad - 18), 1)
            for k in range(10):
                ang = k * math.pi / 5 + boss.pulse * 0.5
                ex = tx + int(math.cos(ang) * rad)
                ey = ty + int(math.sin(ang) * rad * 0.7)
                pygame.draw.line(surface, (*_NS_aeralith.PALETTE["wind_light"], a), (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["wind_shine"], a), (ex, ey, 1, 1))

    @staticmethod
    def _draw_crescent_head(surface, center, facing, phase, scale=1.0):
        cx, cy = center
        arc = pygame.Surface((96, 72), pygame.SRCALPHA)
        ox, oy = cx - 48, cy - 36

        radius = int(22 * scale)
        thick = int(8 * scale)
        rot = phase * 0.7

        pts_out, pts_in = [], []
        start_a = -1.2 + rot * 0.2
        end_a = 1.2 + rot * 0.2
        steps = 22

        for i in range(steps + 1):
            t = i / steps
            a = start_a + (end_a - start_a) * t
            x = 48 + int(math.cos(a) * radius) * facing
            y = 36 + int(math.sin(a) * radius * 0.72)
            pts_out.append((x, y))
            x2 = 48 + int(math.cos(a) * (radius - thick)) * facing
            y2 = 36 + int(math.sin(a) * (radius - thick) * 0.72)
            pts_in.append((x2, y2))

        poly = pts_out + list(reversed(pts_in))
        _NS_aeralith._poly(arc, (*_NS_aeralith.PALETTE["wind_darkest"], 220), poly)

        # inner glow fill
        for i in range(3):
            alpha = 170 - i * 45
            shrink = i * 2
            pts = []
            for (x, y) in pts_out:
                pts.append((int((x - 48) * 0.92 + 48) + shrink * (-facing), int((y - 36) * 0.92 + 36)))
            _NS_aeralith._poly(arc, (*_NS_aeralith.PALETTE["wind_mid"], alpha), pts + [(48, 36)])

        # edge highlight
        for i in range(len(pts_out) - 1):
            _NS_aeralith._aaline(arc, (*_NS_aeralith.PALETTE["wind_light"], 235), pts_out[i], pts_out[i + 1], 3)
            _NS_aeralith._aaline(arc, (*_NS_aeralith.PALETTE["wind_shine"], 210), pts_out[i], pts_out[i + 1], 1)

        pygame.draw.rect(arc, _NS_aeralith.PALETTE["wind_shine"], (48, 36, 1, 1))
        surface.blit(arc, (ox, oy))

    # -------------------------
    # Skills (visual)
    # -------------------------
    @staticmethod
    def _draw_tailwind_ground(surface, boss, x, y, timer, phase):
        duration = 40
        p = max(0.0, min(1.0, 1 - timer / duration))
        r = int(20 + 52 * p)
        a = _NS_aeralith._alpha(190 * (1 - p * 0.12))
        pygame.draw.ellipse(surface, (*_NS_aeralith.PALETTE["wind_mid"], a),
                            (x - r, y + 48 - r // 3, r * 2, r * 2 // 3), 2)

    @staticmethod
    def _draw_tailwind_foreground(surface, boss, x, y, timer, phase):
        duration = 40
        p = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # stronger streaks + afterimage feel
        for i in range(12):
            t = max(0.0, p - i * 0.05)
            sx = x + int((22 + 140 * t) * facing)
            sy = y + 12 - int(math.sin(phase * 2.2 + i) * 12 * (1 - t))
            a = _NS_aeralith._alpha(235 * (1 - i / 12) * (0.35 + 0.65 * p))
            _NS_aeralith._aaline(surface, (*_NS_aeralith.PALETTE["wind_light"], a),
                                 (sx - facing * 56, sy + 14), (sx, sy), 7)
            _NS_aeralith._aaline(surface, (*_NS_aeralith.PALETTE["wind_shine"], a),
                                 (sx - facing * 28, sy + 9), (sx, sy), 2)

    @staticmethod
    def _draw_wind_blade_skill(surface, boss, x, y, timer, phase):
        """
        W: Wind Blade -> bigger, flatter slicing gust (projectile + sheet)
        """
        duration = 60
        p = max(0.0, min(1.0, 1 - timer / duration))
        fake_progress = 0.25 + 0.75 * p

        # main projectile
        _NS_aeralith._draw_wind_projectile(surface, boss, x, y, fake_progress, power=1.85)

        # extra slicing sheet along path (gives "blade" look)
        facing = boss.direction
        tx, ty = _NS_aeralith._target_position(boss, x, y)
        start = (x + facing * 58, y - 22)
        t = max(0.0, min(1.0, (fake_progress - 0.50) / 0.50))

        for i in range(8):
            tt = max(0.0, t - i * 0.06)
            px = int(start[0] + (tx - start[0]) * tt)
            py = int(start[1] + (ty - start[1]) * tt)
            a = _NS_aeralith._alpha(180 - i * 18)
            w = max(10, 60 - i * 6)
            h = max(3, 12 - i)
            sheet = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(sheet, (*_NS_aeralith.PALETTE["wind_mid"], a), (0, 0, w, h))
            pygame.draw.ellipse(sheet, (*_NS_aeralith.PALETTE["wind_light"], max(0, a - 60)), (2, 2, w - 4, h - 4))
            surface.blit(sheet, (px - w // 2, py - h // 2))

    @staticmethod
    def _draw_vacuum_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aeralith._target_position(boss, x, y)
        duration = 90
        p = max(0.0, min(1.0, 1 - timer / duration))
        r = int(20 + 62 * min(1.0, p * 1.4))
        a = _NS_aeralith._alpha(220 * (0.35 + 0.65 * p))
        pygame.draw.ellipse(surface, (*_NS_aeralith.PALETTE["wind_darkest"], a),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_aeralith.PALETTE["wind_mid"], max(0, a - 45)),
                            (tx - r + 6, ty - r // 3 + 4, r * 2 - 12, r * 2 // 3 - 8), 2)

    @staticmethod
    def _draw_vacuum_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aeralith._target_position(boss, x, y)
        duration = 90
        p = max(0.0, min(1.0, 1 - timer / duration))
        if p <= 0:
            return

        height = 140
        # tornado column
        for layer in range(12):
            lt = (phase * 0.55 + layer * 0.12) % 1.0
            yy = ty - int(lt * height)
            w = int(12 + 28 * (1 - lt) * (0.65 + 0.35 * math.sin(phase + layer)))
            a = _NS_aeralith._alpha(170 * (1 - lt) * (0.55 + 0.45 * p))
            pygame.draw.ellipse(surface, (*_NS_aeralith.PALETTE["wind_dark"], a), (tx - w, yy - 7, w * 2, 14))
            pygame.draw.ellipse(surface, (*_NS_aeralith.PALETTE["wind_light"], max(0, a - 55)), (tx - w + 2, yy - 5, w * 2 - 4, 10))
            pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["wind_shine"], a), (tx, yy, 1, 1))

        # inward spiral motes
        for i in range(22):
            ang = phase * 1.6 + i * math.pi / 11
            rr = int(84 * (1 - p * 0.18))
            sx = tx + int(math.cos(ang) * rr)
            sy = ty + int(math.sin(ang) * rr * 0.45)
            pygame.draw.rect(surface, _NS_aeralith.PALETTE["leaf_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aeralith.PALETTE["wind_shine"], (sx, sy, 1, 1))

    @staticmethod
    def _draw_sky_rider_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aeralith._target_position(boss, x, y)
        duration = 100
        p = max(0.0, min(1.0, 1 - timer / duration))
        a = _NS_aeralith._alpha(130 + 110 * math.sin(p * math.pi))
        pygame.draw.line(surface, (*_NS_aeralith.PALETTE["wind_mid"], a), (x, y + 48), (tx, ty), 5)
        pygame.draw.line(surface, (*_NS_aeralith.PALETTE["wind_light"], a), (x, y + 48), (tx, ty), 2)

    @staticmethod
    def _draw_sky_rider_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_aeralith._target_position(boss, x, y)
        duration = 100
        p = max(0.0, min(1.0, 1 - timer / duration))

        # burst at target
        if p > 0.52:
            t = (p - 0.52) / 0.48
            r = int(18 + 52 * t)
            a = _NS_aeralith._alpha(245 * (1 - t * 0.18))

            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_darkest"], a), (tx, ty), r + 10, 5)
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_mid"], a), (tx, ty), r, 3)
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_light"], a), (tx, ty), max(6, r - 12), 2)
            _NS_aeralith._aacircle(surface, (*_NS_aeralith.PALETTE["wind_shine"], a), (tx, ty), max(2, r - 22), 1)

            for i in range(16):
                ang = i * math.pi / 8 + phase * 0.55
                ex = tx + int(math.cos(ang) * r)
                ey = ty + int(math.sin(ang) * r * 0.7)
                pygame.draw.line(surface, (*_NS_aeralith.PALETTE["wind_light"], a), (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_aeralith.PALETTE["wind_shine"], a), (ex, ey, 1, 1))


# ====================================================================
# aurex.py
# ====================================================================



# ====================================================================
# AUREX-OMEGA — THE AEGIS DEVASTATOR
# Original HD-style mini boss renderer.
# Required external imports: pygame, math
# ====================================================================
class _NS_aurex_omega:

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Deep outline / shadows
        "void": (5, 8, 15),
        "shadow": (0, 0, 0),
        "outline": (12, 18, 28),

        # Ancient gold armor
        "gold_darkest": (42, 25, 8),
        "gold_dark": (91, 55, 16),
        "gold_mid": (163, 105, 31),
        "gold_light": (222, 161, 59),
        "gold_hot": (255, 211, 108),
        "gold_shine": (255, 242, 185),

        # Blue steel
        "steel_darkest": (8, 22, 38),
        "steel_dark": (18, 49, 78),
        "steel_mid": (38, 93, 130),
        "steel_light": (76, 144, 187),
        "steel_shine": (145, 210, 239),

        # Arcane cyan core
        "core_dark": (5, 42, 66),
        "core_mid": (8, 121, 181),
        "core_light": (35, 197, 255),
        "core_hot": (128, 235, 255),
        "core_white": (225, 255, 255),

        # Electric effects
        "volt_dark": (20, 69, 140),
        "volt_mid": (40, 142, 255),
        "volt_light": (95, 211, 255),
        "volt_hot": (205, 250, 255),

        # Rune floor
        "rune_dark": (12, 37, 55),
        "rune_mid": (22, 105, 145),
        "rune_light": (74, 204, 245),

        "white": (255, 255, 255),
    }

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_aurex_omega._clamp(color), points)

    def _line(surface, color, start, end, width=1):
        pygame.draw.line(
            surface,
            _NS_aurex_omega._clamp(color),
            start,
            end,
            max(1, int(width)),
        )

    def _circle(surface, color, center, radius, width=0):
        color = _NS_aurex_omega._clamp(color)
        radius = max(1, int(radius))
        try:
            if _NS_aurex_omega.HAS_AACIRCLE and radius > 1:
                pygame.draw.aacircle(surface, color, center, radius, width)
            else:
                pygame.draw.circle(surface, color, center, radius, width)
        except Exception:
            pygame.draw.circle(surface, color, center, radius, width)

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
        return (
            int(x + 180 / scale * getattr(boss, "direction", 1)),
            int(y),
        )

    # ------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------
    def draw_aurex_omega(surface, boss, x, y):
        """
        Entry point.

        Gunakan di Boss.draw():
            _NS_aurex_omega.draw_aurex_omega(surface, self, self.x, self.y)

        Skill:
        Q = Shield Crash / melee swing
        W = Volt Blast / projectile
        E = Aegis Barrier / shield aura
        R = Destructive Spin / vortex
        """
        pulse = float(getattr(boss, "pulse", 0.0))
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))

        _NS_aurex_omega._update_attack_animation(boss)
        moving = _NS_aurex_omega._detect_moving(boss)

        attacking = (
            getattr(boss, "_omega_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 48) - 14
        )

        # Background effects
        _NS_aurex_omega._draw_aura(surface, x, y, pulse)
        _NS_aurex_omega._draw_ground_runes(surface, x, y + 42, pulse, skill)

        if skill == "r":
            _NS_aurex_omega._draw_spin_vortex_back(surface, boss, x, y, timer, pulse)

        if skill == "e":
            _NS_aurex_omega._draw_barrier_back(surface, boss, x, y, timer, pulse)

        # Main pose
        if attacking:
            _NS_aurex_omega._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_aurex_omega._draw_float_pose(surface, boss, x, y, walking=True)
        else:
            _NS_aurex_omega._draw_float_pose(surface, boss, x, y, walking=False)

        # Foreground abilities
        if skill == "q":
            _NS_aurex_omega._draw_shield_crash_fx(surface, boss, x, y, timer, pulse)
        elif skill == "w":
            _NS_aurex_omega._draw_volt_projectile(surface, boss, x, y, timer, pulse)
        elif skill == "e":
            _NS_aurex_omega._draw_barrier_front(surface, boss, x, y, timer, pulse)
        elif skill == "r":
            _NS_aurex_omega._draw_spin_vortex_front(surface, boss, x, y, timer, pulse)

    # ------------------------------------------------------------
    # State / animation
    # ------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_omega_last_x"):
            boss._omega_last_x = boss.x
            boss._omega_last_y = boss.y
            return False

        dx = abs(boss.x - boss._omega_last_x)
        dy = abs(boss.y - boss._omega_last_y)

        boss._omega_last_x = boss.x
        boss._omega_last_y = boss.y
        return dx + dy > 0.25

    def _update_attack_animation(boss):
        cooldown = max(4, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_omega_previous_timer", 0))
        active = bool(getattr(boss, "_omega_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._omega_attack_active = True
            boss._omega_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._omega_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._omega_attack_frame = getattr(boss, "_omega_attack_frame", 0) + 1
        elif timer <= 0:
            boss._omega_attack_active = False
            boss._omega_attack_frame = 0
            active = False

        boss._omega_previous_timer = timer
        boss._omega_attack_progress = (
            min(
                1.0,
                getattr(boss, "_omega_attack_frame", 0) / max(1, cooldown - 1),
            )
            if active
            else 0.0
        )

    # ------------------------------------------------------------
    # Pose router
    # ------------------------------------------------------------
    def _draw_float_pose(surface, boss, x, y, walking=False):
        phase = boss.pulse * (2.0 if walking else 1.0)
        bob = int(math.sin(phase * 1.35) * (4 if walking else 3))
        drift = int(math.sin(phase * 0.65) * (3 if walking else 1))

        _NS_aurex_omega._draw_shadow(surface, x + drift, y + 44)
        _NS_aurex_omega._draw_hover_particles(
            surface, x + drift, y + 26, phase, boss.direction, walking
        )
        _NS_aurex_omega._draw_body(
            surface,
            x + drift,
            y + bob,
            boss.direction,
            phase,
            hammer_angle=-12 if walking else 4,
            shield_shift=0,
        )

    def _draw_attack_pose(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_omega_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_omega_attack_dir", None)
        if facing is None:
            facing = boss.direction


        # Wind-up -> powerful forward swing -> recovery.
        if progress < 0.35:
            t = progress / 0.35
            hammer_angle = -20 - t * 80
            lunge = -int(t * 7) * facing
            lift = int(t * 3)
        elif progress < 0.62:
            t = (progress - 0.35) / 0.27
            hammer_angle = -100 + t * 155
            lunge = int((-7 + t * 20)) * facing
            lift = int(3 - t * 6)
        else:
            t = (progress - 0.62) / 0.38
            hammer_angle = 55 * (1 - t) + 4
            lunge = int(13 * (1 - t)) * facing
            lift = int(-3 + t * 3)

        _NS_aurex_omega._draw_shadow(surface, x + lunge, y + 44)
        _NS_aurex_omega._draw_hover_particles(
            surface, x + lunge, y + 26, boss.pulse, facing, False, intense=True
        )
        _NS_aurex_omega._draw_body(
            surface,
            x + lunge,
            y - lift,
            facing,
            boss.pulse,
            hammer_angle=hammer_angle,
            shield_shift=int(lunge * 0.25),
        )

        _NS_aurex_omega._draw_melee_swing_fx(
            surface, boss, x + lunge, y - lift, progress
        )

    # ------------------------------------------------------------
    # Main body
    # ------------------------------------------------------------
    def _draw_body(surface, cx, cy, facing, phase, hammer_angle=0, shield_shift=0):
        # Rear thruster, rear arm, legs, torso, shield, hammer, head.
        _NS_aurex_omega._draw_thruster(surface, cx, cy, facing, phase)
        _NS_aurex_omega._draw_back_arm(surface, cx, cy, facing)
        _NS_aurex_omega._draw_hover_legs(surface, cx, cy, facing, phase)
        _NS_aurex_omega._draw_torso(surface, cx, cy, facing, phase)
        _NS_aurex_omega._draw_shield(surface, cx, cy, facing, phase, shield_shift)
        _NS_aurex_omega._draw_hammer(surface, cx, cy, facing, phase, hammer_angle)
        _NS_aurex_omega._draw_head(surface, cx, cy, facing, phase)

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 30), pygame.SRCALPHA)

        for r in range(18, 1, -2):
            alpha = max(0, (18 - r) * 13)
            pygame.draw.ellipse(
                shadow,
                (0, 0, 0, alpha),
                (65 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)),
            )

        pygame.draw.ellipse(shadow, (2, 7, 12, 180), (8, 11, 114, 12))
        pygame.draw.ellipse(shadow, (13, 66, 92, 80), (20, 13, 90, 8))
        surface.blit(shadow, (x - 65, y - 14))

    def _draw_hover_legs(surface, cx, cy, facing, phase):
        float_y = int(math.sin(phase * 1.4) * 2)

        for side in (-1, 1):
            lx = cx + side * 11
            ly = cy + 20 + float_y

            # Mechanical lower limb
            _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["outline"], [
                (lx - 6, ly - 6), (lx + 6, ly - 6),
                (lx + 8, ly + 8), (lx - 8, ly + 8),
            ])
            _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_dark"], [
                (lx - 5, ly - 5), (lx + 5, ly - 5),
                (lx + 6, ly + 6), (lx - 6, ly + 6),
            ])
            _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_mid"], [
                (lx - 3, ly - 4), (lx + 3, ly - 4),
                (lx + 4, ly + 3), (lx - 4, ly + 3),
            ])

            # Blue hover engine
            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE["steel_darkest"], (lx, ly + 7), 6
            )
            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE["core_dark"], (lx, ly + 7), 4
            )
            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE["core_mid"], (lx, ly + 7), 3
            )
            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE["core_hot"], (lx, ly + 7), 1
            )

    def _draw_torso(surface, cx, cy, facing, phase):
        # Large ancient armored torso.
        outer = [
            (cx - 19, cy - 5), (cx - 16, cy - 16),
            (cx - 8, cy - 22), (cx + 8, cy - 22),
            (cx + 17, cy - 15), (cx + 20, cy - 3),
            (cx + 16, cy + 15), (cx + 8, cy + 21),
            (cx - 10, cy + 21), (cx - 18, cy + 13),
        ]
        _NS_aurex_omega._poly(
            surface, _NS_aurex_omega.PALETTE["outline"],
            [(px + 2, py + 3) for px, py in outer]
        )
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_darkest"], outer)

        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_dark"], [
            (cx - 16, cy - 4), (cx - 13, cy - 14),
            (cx - 6, cy - 19), (cx + 7, cy - 19),
            (cx + 14, cy - 12), (cx + 16, cy + 5),
            (cx + 10, cy + 16), (cx - 9, cy + 17),
            (cx - 15, cy + 10),
        ])

        # Armor highlights
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_mid"], [
            (cx - 10, cy - 13), (cx - 3, cy - 17),
            (cx + 7, cy - 16), (cx + 12, cy - 9),
            (cx + 10, cy - 4), (cx - 8, cy - 4),
        ])
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_light"], [
            (cx - 7, cy - 13), (cx, cy - 16),
            (cx + 6, cy - 13), (cx + 8, cy - 9),
            (cx - 4, cy - 9),
        ])

        # Chest plate
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["steel_darkest"], [
            (cx - 11, cy - 3), (cx + 11, cy - 3),
            (cx + 12, cy + 12), (cx + 5, cy + 17),
            (cx - 6, cy + 17), (cx - 12, cy + 10),
        ])
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["steel_mid"], [
            (cx - 8, cy - 1), (cx + 8, cy - 1),
            (cx + 9, cy + 10), (cx + 4, cy + 14),
            (cx - 5, cy + 14), (cx - 9, cy + 9),
        ])

        # Center energy core
        core_y = cy + 6
        pulse = int(math.sin(phase * 2.2) * 1)

        for r, col in [
            (10 + pulse, "core_dark"),
            (8 + pulse, "core_mid"),
            (6, "core_light"),
            (3, "core_hot"),
        ]:
            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE[col], (cx, core_y), r
            )

        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_white"], (cx - 1, core_y - 1), 1
        )

        # Chest rune lines
        for off in (-8, 8):
            _NS_aurex_omega._line(
                surface, _NS_aurex_omega.PALETTE["gold_hot"],
                (cx + off, cy + 1), (cx + off // 2, cy + 12), 1
            )

    def _draw_head(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 26

        # Neck
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["steel_darkest"], [
            (hx - 7, hy + 8), (hx + 7, hy + 8),
            (hx + 8, hy + 17), (hx - 8, hy + 17),
        ])
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["steel_mid"], [
            (hx - 5, hy + 9), (hx + 5, hy + 9),
            (hx + 5, hy + 15), (hx - 5, hy + 15),
        ])

        # Helmet
        helmet = [
            (hx - 12, hy + 2), (hx - 9, hy - 8),
            (hx - 3, hy - 13), (hx + 7, hy - 11),
            (hx + 12, hy - 4), (hx + 11, hy + 7),
            (hx + 5, hy + 11), (hx - 8, hy + 9),
        ]
        _NS_aurex_omega._poly(
            surface, _NS_aurex_omega.PALETTE["outline"],
            [(px + 1, py + 2) for px, py in helmet]
        )
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_darkest"], helmet)
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_mid"], [
            (hx - 9, hy + 1), (hx - 7, hy - 6),
            (hx - 2, hy - 10), (hx + 6, hy - 8),
            (hx + 9, hy - 3), (hx + 7, hy + 2),
            (hx - 6, hy + 3),
        ])

        # Blue visor
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["steel_darkest"], [
            (hx - 8, hy - 2), (hx + 8, hy - 3),
            (hx + 7, hy + 3), (hx - 7, hy + 4),
        ])
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["core_mid"], [
            (hx - 6, hy - 1), (hx + 6, hy - 2),
            (hx + 5, hy + 1), (hx - 5, hy + 2),
        ])
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["core_hot"],
            (hx - 4, hy), (hx + 4, hy - 1), 1
        )

        # Crown antenna
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_darkest"],
            (hx, hy - 11), (hx + facing * 2, hy - 20), 3
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_light"],
            (hx, hy - 11), (hx + facing * 2, hy - 20), 1
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_light"],
            (hx + facing * 2, hy - 21), 2
        )

    def _draw_back_arm(surface, cx, cy, facing):
        ax = cx - facing * 17
        ay = cy - 4

        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["outline"], (ax, ay), 10
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["gold_dark"], (ax, ay), 8
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["gold_mid"], (ax, ay), 5
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["steel_dark"], (ax, ay), 3
        )

    # ------------------------------------------------------------
    # Weapon / shield
    # ------------------------------------------------------------
    def _draw_shield(surface, cx, cy, facing, phase, shift=0):
        sx = cx + facing * 25 + shift
        sy = cy + 5

        shield = [
            (sx, sy - 20), (sx + facing * 10, sy - 15),
            (sx + facing * 13, sy - 4), (sx + facing * 9, sy + 15),
            (sx, sy + 23), (sx - facing * 7, sy + 15),
            (sx - facing * 9, sy - 5), (sx - facing * 6, sy - 16),
        ]

        _NS_aurex_omega._poly(
            surface, _NS_aurex_omega.PALETTE["outline"],
            [(px + 2, py + 2) for px, py in shield]
        )
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_darkest"], shield)

        inner = [
            (sx, sy - 16), (sx + facing * 7, sy - 12),
            (sx + facing * 9, sy - 4), (sx + facing * 6, sy + 11),
            (sx, sy + 17), (sx - facing * 4, sy + 10),
            (sx - facing * 5, sy - 4), (sx - facing * 3, sy - 12),
        ]
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["gold_light"], inner)

        # Shield energy panel
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["steel_darkest"], [
            (sx, sy - 11), (sx + facing * 5, sy - 8),
            (sx + facing * 6, sy + 4), (sx, sy + 11),
            (sx - facing * 3, sy + 5), (sx - facing * 3, sy - 7),
        ])
        _NS_aurex_omega._poly(surface, _NS_aurex_omega.PALETTE["core_mid"], [
            (sx, sy - 8), (sx + facing * 3, sy - 6),
            (sx + facing * 4, sy + 2), (sx, sy + 7),
            (sx - facing * 1, sy + 3), (sx - facing * 1, sy - 5),
        ])
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_hot"], (sx, sy), 3
        )

    def _draw_hammer(surface, cx, cy, facing, phase, angle_deg):
        # Pivot at left side, opposite the shield.
        px = cx - facing * 20
        py = cy - 4

        angle = math.radians(angle_deg)
        length = 25

        ex = px + int(math.cos(angle) * (-facing) * length)
        ey = py + int(math.sin(angle) * length)

        # Handle shadow and handle
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["outline"],
            (px + 2, py + 2), (ex + 2, ey + 2), 6
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_darkest"],
            (px, py), (ex, ey), 5
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_mid"],
            (px, py), (ex, ey), 3
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_hot"],
            (px, py), (ex, ey), 1
        )

        # Hammer head perpendicular to handle.
        perp = angle + math.pi / 2
        hx1 = ex + int(math.cos(perp) * 9)
        hy1 = ey + int(math.sin(perp) * 9)
        hx2 = ex - int(math.cos(perp) * 9)
        hy2 = ey - int(math.sin(perp) * 9)

        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["outline"],
            (hx1 + 2, hy1 + 2), (hx2 + 2, hy2 + 2), 12
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["steel_darkest"],
            (hx1, hy1), (hx2, hy2), 10
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_dark"],
            (hx1, hy1), (hx2, hy2), 8
        )
        _NS_aurex_omega._line(
            surface, _NS_aurex_omega.PALETTE["gold_light"],
            (hx1, hy1), (hx2, hy2), 4
        )

        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_mid"], (ex, ey), 4
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_hot"], (ex, ey), 2
        )

    # ------------------------------------------------------------
    # Ambient
    # ------------------------------------------------------------
    def _draw_thruster(surface, cx, cy, facing, phase):
        tx = cx - facing * 22
        ty = cy + 12
        pulse = math.sin(phase * 3.0) * 0.5 + 0.5

        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["steel_darkest"], (tx, ty), 8
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["steel_mid"], (tx, ty), 6
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_mid"], (tx, ty), 4
        )
        _NS_aurex_omega._circle(
            surface, _NS_aurex_omega.PALETTE["core_hot"], (tx, ty), 2
        )

        for i in range(4):
            sx = tx - facing * (7 + i * 4)
            sy = ty + int(math.sin(phase * 3 + i) * 3)
            alpha = int(180 - i * 35 + pulse * 30)
            _NS_aurex_omega._circle(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_light"], alpha),
                (sx, sy),
                max(1, 4 - i),
            )

    def _draw_hover_particles(surface, cx, cy, phase, facing, moving, intense=False):
        count = 12 if intense else 8
        spread = 35 if moving else 25

        for i in range(count):
            t = (phase * (1.2 if moving else 0.65) + i * 0.16) % 1.0
            px = cx + int(math.sin(i * 2.4 + phase) * spread)
            py = cy + 20 - int(t * (24 if moving else 16))
            size = 2 if i % 3 else 3
            alpha = int(220 * (1 - t))

            _NS_aurex_omega._circle(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_dark"], alpha),
                (px, py),
                size,
            )
            pygame.draw.rect(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_hot"], alpha),
                (px, py, 1, 1),
            )

    def _draw_aura(surface, x, y, phase):
        aura = pygame.Surface((160, 140), pygame.SRCALPHA)
        pulse = math.sin(phase * 0.7) * 0.25 + 0.75

        for r in range(62, 6, -5):
            alpha = int((62 - r) * 1.3 * pulse)
            _NS_aurex_omega._circle(
                aura,
                (*_NS_aurex_omega.PALETTE["volt_dark"], alpha),
                (80, 70),
                r,
            )

        for i in range(10):
            a = phase * 0.5 + i * math.pi / 5
            px = 80 + int(math.cos(a) * 44)
            py = 70 + int(math.sin(a) * 25)
            pygame.draw.rect(
                aura, _NS_aurex_omega.PALETTE["volt_light"], (px, py, 2, 2)
            )

        surface.blit(aura, (x - 80, y - 70))

    def _draw_ground_runes(surface, x, y, phase, skill):
        ring = pygame.Surface((150, 48), pygame.SRCALPHA)

        pygame.draw.ellipse(
            ring, (*_NS_aurex_omega.PALETTE["rune_dark"], 180),
            (8, 14, 134, 25), 2
        )
        pygame.draw.ellipse(
            ring, (*_NS_aurex_omega.PALETTE["rune_mid"], 180),
            (21, 18, 108, 17), 1
        )

        for i in range(10):
            angle = phase * 0.5 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 42)
            y1 = 26 + int(math.sin(angle) * 7)
            x2 = 75 + int(math.cos(angle) * 60)
            y2 = 26 + int(math.sin(angle) * 10)

            _NS_aurex_omega._line(
                ring,
                _NS_aurex_omega.PALETTE["rune_light"],
                (x1, y1), (x2, y2), 1
            )

        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_aurex_omega.PALETTE["core_hot"], 190),
                (15, 10, 120, 31), 1
            )

        surface.blit(ring, (x - 75, y - 24))

    # ------------------------------------------------------------
    # Basic melee attack effect
    # ------------------------------------------------------------
    def _draw_melee_swing_fx(surface, boss, x, y, progress):
        if progress < 0.35 or progress > 0.78:
            return

        facing = getattr(boss, "direction", 1)
        t = (progress - 0.35) / 0.43
        alpha = int(math.sin(t * math.pi) * 220)

        cx = x - facing * 43
        cy = y - 5

        for i in range(4):
            radius = 18 + i * 5
            rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)

            start = math.radians(210 if facing == 1 else 330)
            end = start + math.radians(85)

            pygame.draw.arc(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_light"], max(0, alpha - i * 35)),
                rect,
                start,
                end,
                max(1, 4 - i),
            )

        if progress > 0.58:
            impact_x = x - facing * 49
            impact_y = y + 10
            _NS_aurex_omega._circle(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_hot"], alpha),
                (impact_x, impact_y),
                9,
                2,
            )

    # ------------------------------------------------------------
    # Q — Shield Crash
    # ------------------------------------------------------------
    def _draw_shield_crash_fx(surface, boss, x, y, timer, phase):
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1)

        if progress < 0.45:
            return

        t = (progress - 0.45) / 0.55
        ix = x + facing * int(32 + t * 40)
        iy = y + 25
        radius = int(10 + t * 30)
        alpha = int(240 * (1 - t * 0.55))

        for r, col, width in [
            (radius + 8, "volt_dark", 3),
            (radius + 4, "volt_mid", 2),
            (radius, "volt_light", 1),
        ]:
            _NS_aurex_omega._circle(
                surface,
                (*_NS_aurex_omega.PALETTE[col], alpha),
                (ix, iy),
                r,
                width,
            )

        for i in range(10):
            angle = i * math.pi / 5 + phase
            ex = ix + int(math.cos(angle) * radius)
            ey = iy + int(math.sin(angle) * radius * 0.55)

            _NS_aurex_omega._line(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_hot"], alpha),
                (ix, iy), (ex, ey), 2
            )

    # ------------------------------------------------------------
    # W — Volt Blast projectile
    # ------------------------------------------------------------
    def _draw_volt_projectile(surface, boss, x, y, timer, phase):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1)
        tx, ty = _NS_aurex_omega._target_position(boss, x, y)

        start_x = x + facing * 27
        start_y = y - 10

        # Charge phase
        if progress < 0.22:
            t = progress / 0.22
            radius = int(4 + t * 9)

            for r in range(radius + 5, 1, -2):
                alpha = int(150 * (radius + 5 - r) / (radius + 5))
                _NS_aurex_omega._circle(
                    surface,
                    (*_NS_aurex_omega.PALETTE["volt_mid"], alpha),
                    (start_x, start_y),
                    r,
                )

            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE["volt_hot"],
                (start_x, start_y), max(1, radius - 3)
            )
            return

        t = (progress - 0.22) / 0.78
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Lightning trail
        last = (bx, by)
        for i in range(9):
            trail_t = max(0.0, t - (i + 1) * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            py += int(math.sin(phase * 8 + i) * 4)

            _NS_aurex_omega._line(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_mid"], 220 - i * 20),
                last, (px, py),
                max(1, 4 - i // 3),
            )
            last = (px, py)

        for r, col in [
            (10, "volt_dark"),
            (8, "volt_mid"),
            (5, "volt_light"),
            (2, "volt_hot"),
        ]:
            _NS_aurex_omega._circle(
                surface, _NS_aurex_omega.PALETTE[col], (bx, by), r
            )

        # Projectile impact
        if t > 0.86:
            hit_t = (t - 0.86) / 0.14
            radius = int(10 + hit_t * 24)
            alpha = int(255 * (1 - hit_t))

            for i in range(12):
                angle = i * math.pi / 6
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.7)

                _NS_aurex_omega._line(
                    surface,
                    (*_NS_aurex_omega.PALETTE["volt_hot"], alpha),
                    (tx, ty), (ex, ey), 2
                )

    # ------------------------------------------------------------
    # E — Aegis Barrier
    # ------------------------------------------------------------
    def _draw_barrier_back(surface, boss, x, y, timer, phase):
        breath = int(math.sin(phase * 2) * 3)
        radius = 53 + breath

        shield = pygame.Surface((140, 140), pygame.SRCALPHA)
        center = (70, 70)

        for r, alpha, width in [
            (radius + 5, 50, 2),
            (radius, 100, 2),
            (radius - 4, 160, 1),
        ]:
            _NS_aurex_omega._circle(
                shield,
                (*_NS_aurex_omega.PALETTE["volt_mid"], alpha),
                center,
                r,
                width,
            )

        surface.blit(shield, (x - 70, y - 70))

    def _draw_barrier_front(surface, boss, x, y, timer, phase):
        radius = 53 + int(math.sin(phase * 2) * 3)

        for i in range(18):
            angle = phase * 1.2 + i * math.pi / 9
            px = x + int(math.cos(angle) * radius)
            py = y + int(math.sin(angle) * radius)
            pygame.draw.rect(
                surface, _NS_aurex_omega.PALETTE["volt_hot"], (px, py, 2, 2)
            )

        for i in range(6):
            angle = phase * 0.6 + i * math.pi / 3
            x1 = x + int(math.cos(angle) * radius)
            y1 = y + int(math.sin(angle) * radius)
            x2 = x + int(math.cos(angle + 0.18) * (radius + 8))
            y2 = y + int(math.sin(angle + 0.18) * (radius + 8))

            _NS_aurex_omega._line(
                surface, _NS_aurex_omega.PALETTE["volt_light"],
                (x1, y1), (x2, y2), 1
            )

    # ------------------------------------------------------------
    # R — Destructive Spin
    # ------------------------------------------------------------
    def _draw_spin_vortex_back(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_radius = int(28 + min(1.0, progress * 2.5) * 56)

        for i in range(6):
            radius = max_radius - i * 8
            if radius < 8:
                continue

            alpha = max(40, 180 - i * 22)
            rect = pygame.Rect(
                x - radius,
                y + 22 - radius // 3,
                radius * 2,
                max(8, radius * 2 // 3),
            )

            pygame.draw.ellipse(
                surface,
                (*_NS_aurex_omega.PALETTE["volt_dark"], alpha),
                rect,
                max(1, 4 - i // 2),
            )

    def _draw_spin_vortex_front(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_radius = int(28 + min(1.0, progress * 2.5) * 56)

        # Multiple rotating electric tornado rings.
        for ring in range(5):
            radius = max_radius - ring * 9
            if radius < 8:
                continue

            y_off = 26 - ring * 10
            alpha = max(50, 230 - ring * 32)

            for seg in range(4):
                start = phase * 3 + seg * math.pi / 2 + ring * 0.55
                end = start + 0.9

                rect = pygame.Rect(
                    x - radius,
                    y + y_off - radius // 4,
                    radius * 2,
                    max(10, radius // 2),
                )

                pygame.draw.arc(
                    surface,
                    (*_NS_aurex_omega.PALETTE["volt_light"], alpha),
                    rect,
                    start,
                    end,
                    max(1, 4 - ring // 2),
                )

        # Central lightning sparks.
        for i in range(18):
            t = (phase * 2.5 + i * 0.11) % 1.0
            angle = i * 2.399 + phase * 4
            radius = int((1 - t) * max_radius)
            px = x + int(math.cos(angle) * radius)
            py = y + 20 - int(t * 58)

            pygame.draw.rect(
                surface,
                _NS_aurex_omega.PALETTE["volt_hot"],
                (px, py, 2, 2),
            )


# ====================================================================
# nyxareva.py
# ====================================================================

# ====================================================================
# NYXAREVA - The Fallen Queen (Mini Boss)
# Melee Strength - Dark energy blade dancer with lifesteal spins
# ====================================================================


class _NS_nyxareva:
    """Namespace nyxareva - The Fallen Queen mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Dark purple void (main theme)
        "void_darkest": (10, 5, 20),
        "void_dark": (30, 15, 55),
        "void_mid": (75, 35, 120),
        "void_light": (150, 80, 210),
        "void_hot": (200, 130, 255),
        "void_shine": (240, 200, 255),

        # Armor (dark obsidian with purple gleam)
        "armor_darkest": (12, 8, 22),
        "armor_dark": (38, 28, 55),
        "armor_mid": (75, 55, 100),
        "armor_light": (135, 110, 165),
        "armor_shine": (200, 180, 230),

        # Skin (pale death)
        "skin_dark": (100, 90, 115),
        "skin_mid": (160, 145, 175),
        "skin_light": (210, 195, 220),
        "skin_shine": (245, 230, 245),

        # Hair/veil (dark purple flowing)
        "hair_darkest": (20, 10, 35),
        "hair_dark": (50, 25, 75),
        "hair_mid": (100, 55, 140),
        "hair_light": (160, 110, 200),

        # Cape/dress (dark flowing with purple glow)
        "cape_darkest": (15, 8, 28),
        "cape_dark": (35, 20, 60),
        "cape_mid": (70, 40, 105),
        "cape_light": (120, 75, 165),

        # Blade (dark obsidian with purple edge)
        "blade_darkest": (18, 10, 30),
        "blade_dark": (45, 25, 65),
        "blade_mid": (95, 60, 130),
        "blade_light": (160, 115, 200),
        "blade_shine": (230, 200, 255),

        # Eye (glowing purple/pink)
        "eye_socket": (5, 2, 10),
        "eye_dark": (60, 20, 80),
        "eye_mid": (180, 80, 220),
        "eye_light": (240, 160, 255),
        "eye_glow": (255, 220, 255),

        # Crown/horns
        "crown_dark": (20, 15, 30),
        "crown_mid": (60, 45, 85),
        "crown_light": (130, 105, 165),

        # Shadow flames
        "flame_dark": (25, 12, 50),
        "flame_mid": (85, 40, 145),
        "flame_light": (180, 100, 240),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxareva._clamp(color)
        if _NS_nyxareva.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxareva._clamp(color)
        if _NS_nyxareva.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyxareva._clamp(color), points)

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
    def draw_nyxareva(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxareva._detect_moving(boss)
        _NS_nyxareva._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nyx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_nyxareva._draw_void_aura(surface, x, y, pulse)
        _NS_nyxareva._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_nyxareva._draw_mortal_wound_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxareva._draw_whirling_sacrifice_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxareva._draw_avatar_ground(surface, boss, x, y, skill_timer, pulse)

        # Shadow flame tendrils under body (always present as Queen aura).
        _NS_nyxareva._draw_shadow_flames(surface, x, y + 30, pulse,
                                          intense=(active_skill == "r"))

        # Body.
        if active_skill == "r":
            _NS_nyxareva._draw_nyx_avatar_form(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxareva._draw_nyx_whirling(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_nyxareva._draw_nyx_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxareva._draw_nyx_float(surface, boss, x, y)
        else:
            _NS_nyxareva._draw_nyx_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_nyxareva._draw_dark_slash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxareva._draw_mortal_wound_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxareva._draw_whirling_sacrifice_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxareva._draw_avatar_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyx_previous_timer", 0))
        active = bool(getattr(boss, "_nyx_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nyx_attack_active = True
            boss._nyx_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._nyx_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._nyx_attack_frame = int(getattr(boss, "_nyx_attack_frame", 0)) + 1
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
    def _draw_nyx_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 6)
        _NS_nyxareva._draw_shadow(surface, x, y + 50)
        _NS_nyxareva._draw_nyx_body(surface, x, y + bob - 6,
                                     boss.direction, boss.pulse, "idle")

    def _draw_nyx_float(surface, boss, x, y):
        phase = boss.pulse * 1.4
        bob = int(math.sin(phase * 0.9) * 7)
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_nyxareva._draw_shadow(surface, x + sway, y + 50)
        _NS_nyxareva._draw_nyx_body(surface, x + sway, y + bob - 8,
                                     boss.direction, phase, "float")

    def _draw_nyx_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_nyx_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_nyx_attack_dir", None)
        if facing is None:
            facing = boss.direction

        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * facing
            bob = -2 + int(math.sin(boss.pulse * 0.6) * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 14)) * facing
            bob = int(math.sin(boss.pulse * 0.6) * 3) - 4
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * facing
            bob = int(-4 + t * 4) + int(math.sin(boss.pulse * 0.6) * 2)

        _NS_nyxareva._draw_shadow(surface, x + lunge, y + 50)
        _NS_nyxareva._draw_nyx_body(surface, x + lunge, y + bob - 6,
                                     facing, boss.pulse, "attack", progress)
        _NS_nyxareva._draw_blade_slash_trail(surface, boss, x + lunge, y + bob - 6, progress)

    def _draw_nyx_whirling(surface, boss, x, y, timer, phase):
        spin_phase = phase * 5
        bob = int(math.sin(phase * 0.8) * 4) - 6
        _NS_nyxareva._draw_shadow(surface, x, y + 50)
        # Body with motion blur.
        for i in range(4):
            blur_alpha = 60 + i * 40
            blur_angle = spin_phase - i * 0.3
            offset_x = int(math.cos(blur_angle) * 4)
            _NS_nyxareva._draw_nyx_body_silhouette(surface, x + offset_x, y + bob,
                                                    boss.direction, phase, blur_alpha)
        _NS_nyxareva._draw_nyx_body(surface, x, y + bob,
                                     boss.direction, spin_phase, "whirling")

    def _draw_nyx_avatar_form(surface, boss, x, y, timer, phase):
        """Ultimate form - larger, more menacing."""
        bob = int(math.sin(phase * 0.7) * 5) - 4
        # Extra dark aura pulses.
        for i in range(3):
            r_offset = i * 8
            pulse_a = _NS_nyxareva._alpha(80 - i * 20)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], pulse_a),
                                    (x, y - 5 + bob), 55 + r_offset)

        _NS_nyxareva._draw_shadow(surface, x, y + 50)
        _NS_nyxareva._draw_nyx_body(surface, x, y + bob - 8,
                                     boss.direction, phase, "avatar")

    # ============================================================
    # BODY (Fallen Queen - regal, floating, dark)
    # ============================================================
    def _draw_nyx_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw the fallen queen floating body."""
        scale = 1.15 if action == "avatar" else 1.0

        # Draw flowing dress/tail below (like phantom mist).
        _NS_nyxareva._draw_dress_flowing(surface, cx, cy, facing, phase, action, scale)

        # Cape wings (dark spread behind).
        _NS_nyxareva._draw_cape_wings(surface, cx, cy - 4, facing, phase, action,
                                       attack_progress, scale)

        # Torso.
        _NS_nyxareva._draw_torso(surface, cx, cy, facing, phase, action, scale)

        # Off-hand blade arm (back).
        _NS_nyxareva._draw_arm_back_blade(surface, cx, cy, facing, phase, action,
                                           attack_progress, scale)

        # Head + crown.
        _NS_nyxareva._draw_head_crown(surface, cx, cy - int(20 * scale), facing,
                                       phase, action, scale)

        # Main blade arm (front).
        _NS_nyxareva._draw_arm_front_blade(surface, cx, cy, facing, phase, action,
                                            attack_progress, scale)

    def _draw_nyx_body_silhouette(surface, cx, cy, facing, phase, alpha_val):
        """Silhouette for motion blur."""
        surf = pygame.Surface((70, 90), pygame.SRCALPHA)
        # Rough torso
        pygame.draw.ellipse(surf, (*_NS_nyxareva.PALETTE["void_hot"], alpha_val),
                            (26, 30, 18, 24))
        # Head
        pygame.draw.ellipse(surf, (*_NS_nyxareva.PALETTE["void_light"], alpha_val),
                            (28, 12, 14, 16))
        # Dress
        pygame.draw.polygon(surf, (*_NS_nyxareva.PALETTE["void_light"], alpha_val), [
            (26, 50), (44, 50), (48, 78), (22, 78),
        ])
        surface.blit(surf, (cx - 35, cy - 22))

    def _draw_dress_flowing(surface, cx, cy, facing, phase, action, scale):
        """Dress flowing down like phantom mist (no legs visible)."""
        wave = math.sin(phase * 1.2) * 2

        # Main dress silhouette.
        w1 = int(9 * scale)
        w2 = int(16 * scale)
        h = int(28 * scale)

        dress_points = [
            (cx - w1, cy + 5),
            (cx - w1 - 1, cy + 12),
            (cx - w2 - int(wave), cy + h),
            (cx - w2 + 3 - int(wave), cy + h + 3),
            (cx - 4, cy + h + 5),
            (cx + 4, cy + h + 5),
            (cx + w2 - 3 + int(wave), cy + h + 3),
            (cx + w2 + int(wave), cy + h),
            (cx + w1 + 1, cy + 12),
            (cx + w1, cy + 5),
        ]
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in dress_points])
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["cape_darkest"], dress_points)

        # Inner dress darker layers.
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["cape_dark"], [
            (cx - w1 + 1, cy + 5),
            (cx - w1, cy + 12),
            (cx - w2 + 2 - int(wave), cy + h),
            (cx - 3, cy + h + 3),
            (cx + 3, cy + h + 3),
            (cx + w2 - 2 + int(wave), cy + h),
            (cx + w1, cy + 12),
            (cx + w1 - 1, cy + 5),
        ])

        # Mid tone (folds).
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["cape_mid"], [
            (cx - w1 + 2, cy + 6),
            (cx - w1 + 1, cy + 14),
            (cx - 8 - int(wave * 0.5), cy + h - 4),
            (cx - 2, cy + h),
            (cx + 2, cy + h),
            (cx + 8 + int(wave * 0.5), cy + h - 4),
            (cx + w1 - 1, cy + 14),
            (cx + w1 - 2, cy + 6),
        ])

        # Vertical fold lines.
        for i, x_off in enumerate((-6, -2, 2, 6)):
            fold_x = cx + int(x_off * scale) + int(wave * 0.3 * (i % 2 * 2 - 1))
            pygame.draw.line(surface, _NS_nyxareva.PALETTE["cape_darkest"],
                             (fold_x, cy + 8),
                             (fold_x + int(wave * 0.2), cy + h + 2), 1)
            pygame.draw.line(surface, _NS_nyxareva.PALETTE["cape_dark"],
                             (fold_x - 1, cy + 10),
                             (fold_x - 1 + int(wave * 0.2), cy + h), 1)

        # Purple glow at bottom hem.
        for i in range(3):
            hem_y = cy + h + i
            hem_alpha = _NS_nyxareva._alpha(180 - i * 50)
            pygame.draw.line(surface,
                             (*_NS_nyxareva.PALETTE["void_hot"], hem_alpha),
                             (cx - w2 + i - int(wave), hem_y),
                             (cx + w2 - i + int(wave), hem_y), 1)

        # Purple glow embers rising from dress.
        for i in range(6):
            ember_t = (phase * 0.6 + i * 0.16) % 1.0
            ex = cx + int(math.sin(phase + i) * 10) + int(wave)
            ey = cy + h - int(ember_t * 15)
            alpha = _NS_nyxareva._alpha(220 * (1 - ember_t))
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                 (ex, ey, 1, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                                 (ex, ey, 1, 1))

    def _draw_cape_wings(surface, cx, cy, facing, phase, action, attack_progress, scale):
        """Dark spread cape/wings behind the queen."""
        wave = math.sin(phase * 1.0) * 3

        # Beat during action.
        if action in ("attack", "avatar", "whirling"):
            wave *= 2

        # Two wings on both sides.
        for side_mult in [-1, 1]:
            base_x = cx + int(side_mult * 6 * scale)
            base_y = cy - 4

            # Wing extends outward and slightly up.
            span = int(24 * scale)
            drop = int(16 * scale)

            wing_points = [
                (base_x, base_y),
                (base_x + int(side_mult * span * 0.5), base_y - int(8 * scale) - int(wave * 0.5)),
                (base_x + int(side_mult * span), base_y - int(4 * scale) + int(wave)),
                (base_x + int(side_mult * (span + 2)), base_y + int(6 * scale) + int(wave)),
                (base_x + int(side_mult * span * 0.85), base_y + int(drop * 0.7)),
                (base_x + int(side_mult * span * 0.5), base_y + int(drop)),
                (base_x + int(side_mult * 3), base_y + int(drop * 0.6)),
                (base_x, base_y + int(6 * scale)),
            ]

            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                                [(px + 2, py + 2) for px, py in wing_points])
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["cape_darkest"], wing_points)

            # Inner darker.
            inner_points = [
                (base_x + int(side_mult * 2), base_y + 1),
                (base_x + int(side_mult * span * 0.4), base_y - int(6 * scale)),
                (base_x + int(side_mult * (span - 2)), base_y - int(2 * scale)),
                (base_x + int(side_mult * span), base_y + int(5 * scale)),
                (base_x + int(side_mult * span * 0.7), base_y + int(drop * 0.5)),
                (base_x + int(side_mult * span * 0.35), base_y + int(drop * 0.7)),
                (base_x + int(side_mult * 2), base_y + 4),
            ]
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["cape_dark"], inner_points)

            # Wing membrane lines (like ribs).
            for i, t in enumerate((0.3, 0.55, 0.8)):
                end_x = base_x + int(side_mult * span * t)
                end_y = base_y - int(6 * scale) + int(t * drop * 1.5)
                pygame.draw.line(surface, _NS_nyxareva.PALETTE["cape_darkest"],
                                 (base_x, base_y + 2),
                                 (end_x, end_y), 1)
                pygame.draw.line(surface, _NS_nyxareva.PALETTE["cape_mid"],
                                 (base_x + int(side_mult), base_y + 2),
                                 (end_x, end_y), 1)

            # Purple glow rim on top edge.
            pygame.draw.line(surface, _NS_nyxareva.PALETTE["void_light"],
                             wing_points[0], wing_points[1], 1)
            pygame.draw.line(surface, _NS_nyxareva.PALETTE["void_hot"],
                             wing_points[1], wing_points[2], 1)

            # Sharp tip glow.
            tip_x = wing_points[2][0]
            tip_y = wing_points[2][1]
            _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["void_hot"],
                                    (tip_x, tip_y), 2)
            _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["void_shine"],
                                    (tip_x, tip_y), 1)

    def _draw_torso(surface, cx, cy, facing, phase, action, scale):
        """Regal armored torso with purple gem."""
        w1 = int(8 * scale)
        w2 = int(9 * scale)
        h_top = int(10 * scale)

        torso_points = [
            (cx - w1, cy - h_top + 2),
            (cx - w2, cy - 3),
            (cx - w1, cy + 5),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + w1, cy + 5),
            (cx + w2, cy - 3),
            (cx + w1, cy - h_top + 2),
            (cx + 4, cy - h_top),
            (cx - 4, cy - h_top),
        ]
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_points])
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["armor_darkest"], torso_points)

        # Main plate.
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["armor_dark"], [
            (cx - w1 + 1, cy - h_top + 2),
            (cx - w2 + 1, cy - 3),
            (cx - w1 + 1, cy + 4),
            (cx + w1 - 1, cy + 4),
            (cx + w2 - 1, cy - 3),
            (cx + w1 - 1, cy - h_top + 2),
            (cx + 3, cy - h_top + 1),
            (cx - 3, cy - h_top + 1),
        ])

        # Highlight upper.
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["armor_mid"], [
            (cx - 5, cy - h_top + 3),
            (cx - 6, cy - 3),
            (cx - 4, cy + 2),
            (cx + 4, cy + 2),
            (cx + 6, cy - 3),
            (cx + 5, cy - h_top + 3),
            (cx + 2, cy - h_top + 2),
            (cx - 2, cy - h_top + 2),
        ])

        # Chest gem (large purple).
        gem_size = int(3 * scale)
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_darkest"],
                         (cx - gem_size + 1, cy - 2, gem_size * 2, gem_size + 1))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_dark"],
                         (cx - gem_size + 1, cy - 2, gem_size * 2 - 1, gem_size))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_mid"],
                         (cx - gem_size + 2, cy - 1, gem_size * 2 - 3, gem_size - 1))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                         (cx - 1, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_shine"],
                         (cx, cy - 1, 1, 1))

        # Gem glow halo.
        pulse = math.sin(phase * 2) * 0.4 + 0.6
        for r in range(6, 0, -1):
            alpha = _NS_nyxareva._alpha(70 * (6 - r) / 6 * pulse)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    (cx, cy), r)

        # V-shape purple trim.
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["void_dark"],
                         (cx - 6, cy - h_top + 3), (cx, cy - 3), 2)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["void_dark"],
                         (cx + 6, cy - h_top + 3), (cx, cy - 3), 2)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["void_light"],
                         (cx - 6, cy - h_top + 3), (cx, cy - 3), 1)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["void_light"],
                         (cx + 6, cy - h_top + 3), (cx, cy - 3), 1)

        # Shoulder pauldrons (spikes on top).
        for side in [-1, 1]:
            sp_x = cx + side * (w1 - 1)
            sp_y = cy - h_top + 2
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["armor_darkest"], [
                (sp_x, sp_y),
                (sp_x + side * 2, sp_y - 3),
                (sp_x + side * 3, sp_y + 1),
            ])
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["armor_mid"], [
                (sp_x + side, sp_y),
                (sp_x + side * 2, sp_y - 2),
                (sp_x + side * 3, sp_y + 1),
            ])
            pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                             (sp_x + side * 2, sp_y - 2, 1, 1))

    def _draw_head_crown(surface, cx, cy, facing, phase, action, scale):
        """Head with tall spiky crown."""
        # Veil/hair flowing behind.
        _NS_nyxareva._draw_hair_veil(surface, cx, cy, facing, phase, scale)

        # Face shape.
        fw = int(5 * scale)
        fh = int(6 * scale)
        face_points = [
            (cx - fw, cy - 2),
            (cx - fw - 1, cy + 1),
            (cx - fw + 1, cy + 4),
            (cx, cy + fh),
            (cx + fw - 1, cy + 4),
            (cx + fw + 1, cy + 1),
            (cx + fw, cy - 2),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ]
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in face_points])
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["skin_dark"], face_points)

        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["skin_mid"], [
            (cx - fw + 1, cy - 1),
            (cx - fw, cy + 1),
            (cx - fw + 1, cy + 3),
            (cx, cy + fh - 1),
            (cx + fw - 1, cy + 3),
            (cx + fw, cy + 1),
            (cx + fw - 1, cy - 1),
            (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["skin_light"], [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx + 3, cy + 3),
            (cx, cy + fh - 1),
            (cx - 3, cy + 3),
        ])

        # Eyes (glowing purple).
        # Back eye.
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["eye_socket"],
                         (cx - 3, cy, 2, 2))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["eye_mid"],
                         (cx - 3, cy, 2, 1))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["eye_glow"],
                         (cx - 3, cy, 1, 1))

        # Front eye (brighter).
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["eye_socket"],
                         (cx + 1, cy, 2, 2))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["eye_light"],
                         (cx + 1, cy, 2, 1))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["eye_glow"],
                         (cx + 2, cy, 1, 1))

        # Eye glow halo.
        pulse = math.sin(phase * 2.5) * 0.4 + 0.6
        for r in range(5, 0, -1):
            alpha = _NS_nyxareva._alpha(60 * (5 - r) / 5 * pulse)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    (cx + 2, cy + 1), r)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    (cx - 2, cy + 1), r)

        # Mouth (grim line).
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                         (cx - 1, cy + 4), (cx + 1, cy + 4), 1)

        # CROWN with spikes (tall dramatic crown).
        _NS_nyxareva._draw_crown(surface, cx, cy - int(4 * scale), facing, phase, scale)

    def _draw_crown(surface, cx, cy, facing, phase, scale):
        """Tall dark crown with sharp spikes."""
        # Crown base band.
        band_w = int(7 * scale)
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["crown_dark"],
                         (cx - band_w, cy - 2, band_w * 2, 3))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["crown_mid"],
                         (cx - band_w + 1, cy - 1, band_w * 2 - 2, 1))

        # 5 spikes (center tallest).
        spike_configs = [
            (-6, 5, -1),   # far left short
            (-3, 8, 0),    # left tall
            (0, 10, 1),    # center tallest
            (3, 8, 0),     # right tall
            (6, 5, -1),    # far right short
        ]
        for x_off, height, tilt in spike_configs:
            spike_x = cx + int(x_off * scale)
            spike_tip_y = cy - 2 - int(height * scale)
            spike_tip_x = spike_x + tilt

            spike_points = [
                (spike_x - 1, cy - 1),
                (spike_tip_x, spike_tip_y),
                (spike_x + 1, cy - 1),
            ]
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in spike_points])
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["crown_dark"], spike_points)
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["crown_mid"], [
                (spike_x, cy - 1),
                (spike_tip_x, spike_tip_y),
                (spike_x + 1, cy - 1),
            ])
            # Purple glow tip.
            pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                             (spike_tip_x, spike_tip_y, 1, 1))
            _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["void_shine"],
                                    (spike_tip_x, spike_tip_y), 1)

        # Center jewel on crown band.
        jewel_pulse = math.sin(phase * 1.5) * 0.4 + 0.6
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_darkest"],
                         (cx - 1, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                         (cx, cy - 1, 1, 1))
        _NS_nyxareva._aacircle(surface,
                                (*_NS_nyxareva.PALETTE["void_hot"],
                                 _NS_nyxareva._alpha(180 * jewel_pulse)),
                                (cx, cy), 3)

    def _draw_hair_veil(surface, cx, cy, facing, phase, scale):
        """Dark purple hair veil flowing behind head."""
        wave = math.sin(phase * 1.4) * 3

        # Both sides flow down.
        for side in [-1, 1]:
            veil_points = [
                (cx + side * 3, cy - 4),
                (cx + side * 5, cy - 2),
                (cx + side * 7 + int(wave * side * 0.3), cy + 3),
                (cx + side * 6 + int(wave * side * 0.5), cy + 8),
                (cx + side * 4, cy + 10),
                (cx + side * 2, cy + 5),
            ]
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in veil_points])
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["hair_darkest"], veil_points)
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["hair_dark"], [
                (cx + side * 3, cy - 3),
                (cx + side * 4, cy - 1),
                (cx + side * 6 + int(wave * side * 0.3), cy + 3),
                (cx + side * 5, cy + 8),
                (cx + side * 3, cy + 4),
            ])
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["hair_mid"], [
                (cx + side * 3, cy - 2),
                (cx + side * 5 + int(wave * side * 0.2), cy + 2),
                (cx + side * 4, cy + 6),
                (cx + side * 3, cy + 3),
            ])
            # Purple highlight strand.
            pygame.draw.line(surface, _NS_nyxareva.PALETTE["hair_light"],
                             (cx + side * 3, cy - 1),
                             (cx + side * 4, cy + 4), 1)

    def _draw_arm_back_blade(surface, cx, cy, facing, phase, action, attack_progress, scale):
        """Off-hand curved blade arm (behind body)."""
        shoulder_x = cx - facing * int(6 * scale)
        shoulder_y = cy - int(6 * scale)

        # Determine pose.
        if action == "whirling":
            # Blade extended for spin.
            angle = phase * 0.5 + math.pi
            arm_ext = int(14 * scale)
        elif action == "attack":
            # Slight back position while front blade attacks.
            angle = math.pi * 1.2
            arm_ext = int(10 * scale)
        else:
            # Idle - blade held low back.
            idle_sway = math.sin(phase * 0.5) * 0.05
            angle = math.pi * 1.15 + idle_sway
            arm_ext = int(11 * scale)

        # Elbow.
        elbow_x = shoulder_x + int(math.cos(angle * 0.5) * 5 * scale) * facing
        elbow_y = shoulder_y + int(math.sin(angle * 0.5) * 5 * scale)

        # Hand.
        hand_x = shoulder_x + int(math.cos(angle) * arm_ext) * facing
        hand_y = shoulder_y + int(math.sin(angle) * arm_ext)

        # Arm.
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 4)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_mid"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)

        # Curved blade (crescent scythe-like).
        _NS_nyxareva._draw_curved_blade(surface, hand_x, hand_y, angle, -facing, scale, back=True)

    def _draw_arm_front_blade(surface, cx, cy, facing, phase, action, attack_progress, scale):
        """Main hand curved blade."""
        shoulder_x = cx + facing * int(6 * scale)
        shoulder_y = cy - int(6 * scale)

        if action == "attack":
            if attack_progress < 0.35:
                # Wind up back and up.
                t = attack_progress / 0.35
                angle = math.pi * 1.35 + t * 0.2
                arm_ext = int(11 * scale)
            elif attack_progress < 0.6:
                # Slash forward downward.
                t = (attack_progress - 0.35) / 0.25
                angle = math.pi * 1.55 - t * math.pi * 1.5
                arm_ext = int(13 * scale) + int(t * 3)
            else:
                t = (attack_progress - 0.6) / 0.4
                angle = 0.15 + t * 0.3
                arm_ext = int(15 * scale) - int(t * 3)
        elif action == "whirling":
            angle = phase * 0.5
            arm_ext = int(14 * scale)
        elif action == "avatar":
            # Both blades held out menacingly.
            angle = -0.3
            arm_ext = int(14 * scale)
        else:
            # Idle - blade held out to side gracefully.
            idle_sway = math.sin(phase * 0.5) * 0.06
            angle = 0.2 + idle_sway
            arm_ext = int(12 * scale)

        elbow_x = shoulder_x + int(math.cos(angle * 0.5) * 5 * scale) * facing
        elbow_y = shoulder_y + int(math.sin(angle * 0.5) * 5 * scale)
        hand_x = shoulder_x + int(math.cos(angle) * arm_ext) * facing
        hand_y = shoulder_y + int(math.sin(angle) * arm_ext)

        # Arm.
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 4)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_mid"],
                         (shoulder_x, shoulder_y - 1),
                         (elbow_x, elbow_y - 1), 1)

        # Shoulder pauldron (dark with spike).
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["armor_darkest"],
                                (shoulder_x, shoulder_y), 3)
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["armor_mid"],
                                (shoulder_x, shoulder_y), 2)
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                         (shoulder_x, shoulder_y - 1, 1, 1))

        # Forearm.
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["armor_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_nyxareva.PALETTE["skin_mid"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)

        # Curved blade (crescent).
        _NS_nyxareva._draw_curved_blade(surface, hand_x, hand_y, angle, facing, scale)

    def _draw_curved_blade(surface, hand_x, hand_y, angle, facing, scale, back=False):
        """Crescent curved dark blade (like referensi Taara)."""
        blade_len = int(24 * scale)

        # Blade curves. Create an arc of points.
        num_pts = 8
        outer_pts = []
        inner_pts = []

        # Perp direction.
        perp = angle + math.pi / 2

        # Curve amount.
        curve_amount = int(10 * scale)

        for i in range(num_pts + 1):
            t = i / num_pts
            # Along blade axis.
            axis_x = hand_x + int(math.cos(angle) * (t * blade_len)) * facing
            axis_y = hand_y + int(math.sin(angle) * (t * blade_len))
            # Curve outward (sin curve).
            curve = math.sin(t * math.pi) * curve_amount

            outer_x = axis_x + int(math.cos(perp) * (2 + curve))
            outer_y = axis_y + int(math.sin(perp) * (2 + curve))
            inner_x = axis_x + int(math.cos(perp) * (curve * 0.6))
            inner_y = axis_y + int(math.sin(perp) * (curve * 0.6))

            outer_pts.append((outer_x, outer_y))
            inner_pts.append((inner_x, inner_y))

        # Full blade shape.
        blade_shape = outer_pts + inner_pts[::-1]

        # Shadow.
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in blade_shape])
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["blade_darkest"], blade_shape)

        # Dark inner.
        dark_shape = []
        for i in range(len(outer_pts)):
            t = i / (len(outer_pts) - 1)
            ox, oy = outer_pts[i]
            ix, iy = inner_pts[i]
            dark_shape.append((int(ox * 0.85 + ix * 0.15),
                               int(oy * 0.85 + iy * 0.15)))
        for i in range(len(inner_pts) - 1, -1, -1):
            ox, oy = outer_pts[i]
            ix, iy = inner_pts[i]
            dark_shape.append((int(ox * 0.15 + ix * 0.85),
                               int(oy * 0.15 + iy * 0.85)))
        _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["blade_dark"], dark_shape)

        # Mid highlight along curve.
        mid_shape = []
        for i in range(len(outer_pts)):
            ox, oy = outer_pts[i]
            ix, iy = inner_pts[i]
            mid_shape.append((int(ox * 0.6 + ix * 0.4),
                              int(oy * 0.6 + iy * 0.4)))
        for i in range(len(inner_pts) - 1, -1, -1):
            ox, oy = outer_pts[i]
            ix, iy = inner_pts[i]
            mid_shape.append((int(ox * 0.4 + ix * 0.6),
                              int(oy * 0.4 + iy * 0.6)))
        if len(mid_shape) > 2:
            _NS_nyxareva._poly(surface, _NS_nyxareva.PALETTE["blade_mid"], mid_shape)

        # Bright edge on the OUTER curve.
        for i in range(len(outer_pts) - 1):
            pygame.draw.line(surface, _NS_nyxareva.PALETTE["blade_light"],
                             outer_pts[i], outer_pts[i + 1], 1)

        # Tip glow.
        tip = outer_pts[-1]
        for r in range(5, 0, -1):
            alpha = _NS_nyxareva._alpha(120 * (5 - r) / 5)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    tip, r)
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["blade_shine"], tip, 1)
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["white"], (tip[0], tip[1], 1, 1))

        # Base of blade (attaches to hand) - dark chunk with purple gem.
        base = outer_pts[0]
        base_inner = inner_pts[0]
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["armor_darkest"],
                                (hand_x, hand_y), 3)
        _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["void_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                         (hand_x, hand_y, 1, 1))

    def _draw_blade_slash_trail(surface, boss, cx, cy, progress):
        """Curved slash trail during attack."""
        if progress < 0.35 or progress > 0.85:
            return

        facing = boss.direction
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 6

        if progress < 0.6:
            t = (progress - 0.35) / 0.25
        else:
            t = 1.0 - (progress - 0.6) / 0.25 * 0.3

        arc_start = math.pi * 1.55
        arc_end = math.pi * 0.15

        # Trail arc points.
        for i in range(14):
            trail_t = t - i * 0.04
            if trail_t < 0 or trail_t > 1:
                continue
            angle = arc_start + (arc_end - arc_start) * trail_t
            radius = 24
            arc_x = shoulder_x + int(math.cos(angle) * radius) * facing
            arc_y = shoulder_y + int(math.sin(angle) * radius)

            alpha = _NS_nyxareva._alpha(220 * (1 - i / 14))
            size = max(1, 6 - i // 2)

            for r in range(size, 0, -1):
                inner_alpha = _NS_nyxareva._alpha(alpha * (size - r + 1) / size)
                _NS_nyxareva._aacircle(surface,
                                        (*_NS_nyxareva.PALETTE["void_hot"], inner_alpha),
                                        (arc_x, arc_y), r)

            pygame.draw.rect(surface,
                             (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                             (arc_x, arc_y, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow_flames(surface, cx, cy, phase, intense=False):
        """Shadow flame tendrils at feet."""
        strength = 1.5 if intense else 1.0

        # Rising dark flame silhouettes.
        for i in range(8):
            flame_x_off = (i - 4) * 4
            flame_t = (phase * 0.4 + i * 0.13) % 1.0
            fx = cx + flame_x_off + int(math.sin(phase + i) * 3)
            fy = cy + 12 - int(flame_t * 22)
            alpha = _NS_nyxareva._alpha(200 * (1 - flame_t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["flame_dark"], alpha),
                                    (fx, fy), 4)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["flame_mid"], alpha),
                                    (fx, fy - 1), 3)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["flame_light"], alpha),
                                    (fx, fy - 1), 1)
            pygame.draw.rect(surface,
                             (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                             (fx, fy - 2, 1, 1))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 14)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 12 - radius,
                                 104 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 2, 6, 160), (5, 6, 110, 12))
        pygame.draw.ellipse(shadow, (25, 12, 45, 110), (12, 8, 96, 8))
        surface.blit(shadow, (x - 60, y - 12))

    def _draw_void_aura(surface, x, y, phase):
        """Dark purple aura."""
        pulse = math.sin(phase * 0.5) * 0.3 + 0.7

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_nyxareva._alpha((85 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nyxareva._aacircle(aura,
                                        (*_NS_nyxareva.PALETTE["void_dark"], alpha),
                                        (100, 85), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_nyxareva._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyxareva._aacircle(aura,
                                        (*_NS_nyxareva.PALETTE["void_mid"], alpha),
                                        (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))

        # Floating purple embers.
        for i in range(14):
            angle = phase * 0.35 + i * math.pi / 7
            radius = 36 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_shine"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Purple ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 52), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_nyxareva.PALETTE["void_dark"], 200),
                            (5, 16, 150, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxareva.PALETTE["void_darkest"], 220),
                            (14, 18, 132, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_nyxareva.PALETTE["void_mid"], 230),
                            (25, 20, 110, 18), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 29 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 29 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_nyxareva.PALETTE["void_hot"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxareva.PALETTE["void_hot"],
                                       _NS_nyxareva._alpha(150 * pulse)),
                                (15, 10, 130, 38), 1)
        surface.blit(ring, (x - 80, y - 26))

    # ============================================================
    # SKILL Q - DARK SLASH (crescent projectile in front)
    # ============================================================
    def _draw_dark_slash_foreground(surface, boss, x, y, timer, phase):
        """Wide crescent slash projectile in front."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up.
            t = progress / 0.3
            charge_x = x + facing * 18
            charge_y = y - 6
            cr = int(4 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_nyxareva._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_nyxareva._aacircle(surface,
                                        (*_NS_nyxareva.PALETTE["void_dark"], alpha),
                                        (charge_x, charge_y), r)
            _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["void_mid"],
                                    (charge_x, charge_y), max(1, cr - 2))
            _NS_nyxareva._aacircle(surface, _NS_nyxareva.PALETTE["void_hot"],
                                    (charge_x, charge_y), max(1, cr - 4))
        else:
            # Crescent slash expanding outward.
            t = (progress - 0.3) / 0.7
            distance = int(t * 100)
            slash_x = x + facing * distance
            slash_y = y - 6

            # Draw crescent arc.
            arc_radius = int(30 + t * 20)
            alpha = _NS_nyxareva._alpha(255 * (1 - t * 0.7))

            # Multi-layer crescent.
            num_arc_pts = 20
            for arc_i in range(3):  # 3 layers thickness
                thickness_r = arc_radius + arc_i * 2
                for i in range(num_arc_pts):
                    arc_t = i / num_arc_pts
                    arc_angle = -math.pi / 2 + arc_t * math.pi  # top to bottom
                    px = slash_x + int(math.cos(arc_angle) * thickness_r * 0.5) * facing
                    py = slash_y + int(math.sin(arc_angle) * thickness_r * 0.9)

                    fade_alpha = _NS_nyxareva._alpha(alpha * (1 - abs(arc_t - 0.5) * 1.2))

                    if arc_i == 0:
                        color = _NS_nyxareva.PALETTE["void_darkest"]
                        size = 4
                    elif arc_i == 1:
                        color = _NS_nyxareva.PALETTE["void_mid"]
                        size = 3
                    else:
                        color = _NS_nyxareva.PALETTE["void_hot"]
                        size = 2

                    for r in range(size, 0, -1):
                        inner_alpha = _NS_nyxareva._alpha(fade_alpha * (size - r + 1) / size)
                        _NS_nyxareva._aacircle(surface,
                                                (*color, inner_alpha),
                                                (px, py), r)

                    # Bright core dots.
                    pygame.draw.rect(surface,
                                     (*_NS_nyxareva.PALETTE["void_shine"], fade_alpha),
                                     (px, py, 1, 1))

            # Particle sparks trailing behind.
            for i in range(10):
                trail_dist = distance - i * 8
                if trail_dist < 0:
                    continue
                trail_x = x + facing * trail_dist
                trail_y = y - 6 + int(math.sin(phase * 3 + i) * 8)
                trail_alpha = _NS_nyxareva._alpha(200 * (1 - i / 10) * (1 - t))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["void_hot"], trail_alpha),
                                 (trail_x, trail_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["void_shine"], trail_alpha),
                                 (trail_x, trail_y, 1, 1))

    # ============================================================
    # SKILL W - MORTAL WOUND (ground strike + rising spikes)
    # ============================================================
    def _draw_mortal_wound_ground(surface, boss, x, y, timer, phase):
        """Marked ground rings at target."""
        tx, ty = _NS_nyxareva._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(35 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_nyxareva.PALETTE["void_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_nyxareva.PALETTE["void_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_nyxareva.PALETTE["void_mid"], 130),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_mortal_wound_foreground(surface, boss, x, y, timer, phase):
        """Rising dark spikes at target area."""
        tx, ty = _NS_nyxareva._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind up glow at boss.
            t = progress / 0.3
            charge_y = y + 20
            for r in range(int(8 + t * 6), 0, -1):
                alpha = _NS_nyxareva._alpha(180 * t)
                _NS_nyxareva._aacircle(surface,
                                        (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                        (x, charge_y), r)
        elif progress < 0.8:
            # Rising spikes.
            t = (progress - 0.3) / 0.5

            # Multiple spikes in cluster.
            spike_positions = [
                (tx, ty, 32),
                (tx - 18, ty - 4, 22),
                (tx + 18, ty - 2, 24),
                (tx - 8, ty + 6, 18),
                (tx + 10, ty + 8, 20),
            ]

            for sx, sy, max_h in spike_positions:
                # Spike animation - rises then holds then falls.
                if t < 0.3:
                    spike_h = int(max_h * (t / 0.3))
                elif t < 0.7:
                    spike_h = max_h + int(math.sin((t - 0.3) * 10) * 2)
                else:
                    spike_h = int(max_h * (1 - (t - 0.7) / 0.3))

                spike_tip_y = sy - spike_h

                # Layered vertical beam.
                for width, color in [
                    (8, _NS_nyxareva.PALETTE["void_darkest"]),
                    (5, _NS_nyxareva.PALETTE["void_dark"]),
                    (3, _NS_nyxareva.PALETTE["void_mid"]),
                    (2, _NS_nyxareva.PALETTE["void_hot"]),
                    (1, _NS_nyxareva.PALETTE["void_shine"]),
                ]:
                    alpha_v = _NS_nyxareva._alpha(220)
                    pygame.draw.rect(surface, (*color, alpha_v),
                                     (sx - width // 2, spike_tip_y,
                                      width, spike_h))

                # Spike top glow.
                for r in range(5, 0, -1):
                    alpha_r = _NS_nyxareva._alpha(180 * (5 - r) / 5)
                    _NS_nyxareva._aacircle(surface,
                                            (*_NS_nyxareva.PALETTE["void_hot"], alpha_r),
                                            (sx, spike_tip_y), r)
                pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_shine"],
                                 (sx, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_nyxareva.PALETTE["white"],
                                 (sx, spike_tip_y, 1, 1))

                # Base impact splash.
                for r_base in range(6, 0, -1):
                    alpha_b = _NS_nyxareva._alpha(150 * (6 - r_base) / 6)
                    _NS_nyxareva._aacircle(surface,
                                            (*_NS_nyxareva.PALETTE["void_mid"], alpha_b),
                                            (sx, sy), r_base)

                # Rising sparkles.
                for i in range(4):
                    sp_t = (phase * 2 + i * 0.25) % 1.0
                    sp_x = sx + int(math.sin(phase * 3 + i) * 5)
                    sp_y = sy - int(sp_t * spike_h)
                    sp_a = _NS_nyxareva._alpha(240 * (1 - sp_t))
                    pygame.draw.rect(surface,
                                     (*_NS_nyxareva.PALETTE["void_shine"], sp_a),
                                     (sp_x, sp_y, 1, 1))

    # ============================================================
    # SKILL E - WHIRLING SACRIFICE (spinning blade AoE)
    # ============================================================
    def _draw_whirling_sacrifice_ground(surface, boss, x, y, timer, phase):
        """Purple ring on ground during spin."""
        for i in range(3):
            r = int(30 + i * 8 + math.sin(phase * 2 + i) * 2)
            alpha = _NS_nyxareva._alpha(180 - i * 45)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    (x, y + 42), r, 2)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_light"], alpha),
                                    (x, y + 42), r, 1)

    def _draw_whirling_sacrifice_foreground(surface, boss, x, y, timer, phase):
        """Spinning purple vortex swirls around boss."""
        duration = 80

        # Vortex swirl arcs (multiple spirals).
        for spiral in range(3):
            offset = spiral * math.pi * 2 / 3
            spin_speed = 5
            spin_angle = phase * spin_speed + offset

            # Draw spiral arc.
            num_pts = 24
            for i in range(num_pts):
                t = i / num_pts
                angle = spin_angle + t * math.pi * 1.8
                radius = 15 + int(t * 30)  # spiral outward
                px = x + int(math.cos(angle) * radius)
                py = y - 5 + int(math.sin(angle) * radius * 0.5)

                alpha = _NS_nyxareva._alpha(220 * (1 - t * 0.6))
                size = max(1, 4 - i // 6)

                for r in range(size, 0, -1):
                    inner_alpha = _NS_nyxareva._alpha(alpha * (size - r + 1) / size)
                    _NS_nyxareva._aacircle(surface,
                                            (*_NS_nyxareva.PALETTE["void_hot"], inner_alpha),
                                            (px, py), r)
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                                 (px, py, 1, 1))

        # Sparks flying outward.
        for i in range(20):
            spark_angle = phase * 2 + i * math.pi / 10
            spark_dist = 32 + int((phase * 4 + i * 5) % 20)
            sx = x + int(math.cos(spark_angle) * spark_dist)
            sy = y - 5 + int(math.sin(spark_angle) * spark_dist * 0.5)
            pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyxareva.PALETTE["void_shine"], (sx, sy, 1, 1))

        # Central purple energy core (lifesteal indicator).
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for r in range(10, 0, -1):
            alpha = _NS_nyxareva._alpha(150 * (10 - r) / 10 * core_pulse)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_light"], alpha),
                                    (x, y), r)

    # ============================================================
    # SKILL R - AVATAR OF NYXAREVA (ultimate - pulls + AoE)
    # ============================================================
    def _draw_avatar_ground(surface, boss, x, y, timer, phase):
        """Ground pulse rings during ultimate."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(4):
            r = int(35 + i * 10 + math.sin(phase * 2 + i) * 3)
            alpha = _NS_nyxareva._alpha(200 - i * 45)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    (x, y + 42), r, 2)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                                    (x, y + 42), r, 1)

        # Radial dark energy tendrils on ground pulling in.
        for i in range(12):
            angle = i * math.pi / 6
            end_x = x + int(math.cos(angle) * 60)
            end_y = y + 42 + int(math.sin(angle) * 20)
            start_x = x + int(math.cos(angle) * 20)
            start_y = y + 42 + int(math.sin(angle) * 6)

            pull_t = (phase * 2 + i * 0.2) % 1.0
            px = int(end_x + (start_x - end_x) * pull_t)
            py = int(end_y + (start_y - end_y) * pull_t)
            alpha = _NS_nyxareva._alpha(220 * (1 - pull_t))
            pygame.draw.rect(surface,
                             (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                             (px, py, 1, 1))

    def _draw_avatar_foreground(surface, boss, x, y, timer, phase):
        """Massive purple flames rising around avatar form."""
        duration = 110

        # Huge flame pillars around avatar.
        num_flames = 12
        for i in range(num_flames):
            angle = i * math.pi * 2 / num_flames + phase * 0.2
            flame_r = 45 + int(math.sin(phase * 2 + i) * 5)
            fx = x + int(math.cos(angle) * flame_r)
            fy = y + int(math.sin(angle) * flame_r * 0.4)

            # Flame column rising.
            for layer in range(8):
                layer_t = (phase * 1.2 + i * 0.15 + layer * 0.12) % 1.0
                layer_y = fy - int(layer_t * 40)
                layer_w = int(5 + layer_t * 3)
                layer_h = int(6 + layer_t * 4)
                alpha = _NS_nyxareva._alpha(200 * (1 - layer_t))

                pygame.draw.ellipse(surface,
                                    (*_NS_nyxareva.PALETTE["flame_dark"], alpha),
                                    (fx - layer_w, layer_y - layer_h,
                                     layer_w * 2, layer_h * 2))
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxareva.PALETTE["flame_mid"], alpha),
                                    (fx - layer_w + 1, layer_y - layer_h + 1,
                                     max(1, layer_w * 2 - 2),
                                     max(1, layer_h * 2 - 2)))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["flame_light"], alpha),
                                 (fx, layer_y, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                                 (fx, layer_y - 1, 1, 1))

        # Central column of energy (very bright).
        for r in range(20, 0, -1):
            alpha = _NS_nyxareva._alpha(180 * (20 - r) / 20)
            _NS_nyxareva._aacircle(surface,
                                    (*_NS_nyxareva.PALETTE["void_hot"], alpha),
                                    (x, y - 5), r)

        # Vertical light beam going up.
        for width, color, alpha_v in [
            (12, _NS_nyxareva.PALETTE["void_dark"], 60),
            (8, _NS_nyxareva.PALETTE["void_mid"], 100),
            (5, _NS_nyxareva.PALETTE["void_hot"], 140),
            (2, _NS_nyxareva.PALETTE["void_shine"], 200),
        ]:
            pygame.draw.rect(surface, (*color, alpha_v),
                             (x - width // 2, 0, width, y - 5))

        # Extra bright particles rising along beam.
        for i in range(20):
            p_t = (phase * 2 + i * 0.08) % 1.0
            py = int((y - 5) - p_t * (y + 20))
            px = x + int(math.sin(phase * 3 + i) * 6)
            alpha = _NS_nyxareva._alpha(240 * (1 - p_t))
            pygame.draw.rect(surface,
                             (*_NS_nyxareva.PALETTE["void_shine"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_nyxareva.PALETTE["white"], alpha),
                             (px, py, 1, 1))


# ====================================================================
# thalakryon.py
# ====================================================================

# ====================================================================
# THALAKRYON - THE ABYSSAL SOVEREIGN
# ====================================================================


class _NS_thalakryon:
    """Namespace thalakryon - True Boss Mermidon Abyssal."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Deep abyssal blue skin (main body)
        "skin_darkest": (5, 15, 30),
        "skin_dark": (15, 40, 70),
        "skin_mid": (35, 85, 130),
        "skin_light": (70, 140, 190),
        "skin_edge": (130, 200, 240),
        "skin_shine": (200, 240, 255),

        # Green-teal scales (armor plates on chest, shoulders, arms)
        "scale_darkest": (5, 25, 25),
        "scale_dark": (20, 60, 55),
        "scale_mid": (45, 115, 100),
        "scale_light": (95, 180, 155),
        "scale_edge": (160, 230, 200),
        "scale_shine": (220, 255, 235),

        # Belly / underside (pale cyan)
        "belly_darkest": (30, 55, 65),
        "belly_dark": (70, 110, 130),
        "belly_mid": (130, 180, 200),
        "belly_light": (200, 230, 240),
        "belly_shine": (240, 255, 255),

        # Fins (translucent teal-blue)
        "fin_dark": (10, 45, 65),
        "fin_mid": (40, 110, 145),
        "fin_light": (110, 190, 220),
        "fin_glow": (180, 240, 255),

        # Trident (dark bronze + azure blade)
        "metal_darkest": (25, 20, 15),
        "metal_dark": (75, 55, 30),
        "metal_mid": (150, 120, 65),
        "metal_light": (220, 190, 120),
        "metal_shine": (255, 240, 190),

        # Blade energy (azure/cyan glow)
        "azure_darkest": (5, 20, 40),
        "azure_dark": (20, 70, 130),
        "azure_mid": (60, 150, 220),
        "azure_light": (150, 220, 255),
        "azure_hot": (220, 250, 255),
        "azure_shine": (255, 255, 255),

        # Eye (menyala cyan-white)
        "eye_socket": (2, 5, 10),
        "eye_darkest": (10, 30, 60),
        "eye_dark": (30, 80, 140),
        "eye_mid": (80, 170, 230),
        "eye_light": (180, 240, 255),
        "eye_glow": (240, 255, 255),

        # Water/tidal
        "water_darkest": (5, 20, 45),
        "water_dark": (20, 60, 110),
        "water_mid": (50, 130, 190),
        "water_light": (140, 210, 240),
        "water_foam": (230, 250, 255),

        # Abyssal purple/dark (true boss accent)
        "abyss_darkest": (10, 5, 25),
        "abyss_dark": (35, 20, 65),
        "abyss_mid": (75, 50, 130),
        "abyss_light": (140, 100, 200),

        # Kraken tentacle accents
        "tentacle_dark": (60, 25, 55),
        "tentacle_mid": (120, 55, 105),
        "tentacle_light": (190, 120, 175),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thalakryon._clamp(color)
        if _NS_thalakryon.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_thalakryon._clamp(color)
        if _NS_thalakryon.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_thalakryon._clamp(color), points)

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
    def draw_thalakryon(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thalakryon._detect_moving(boss)
        _NS_thalakryon._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_thk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind (floating aura).
        _NS_thalakryon._draw_abyssal_aura(surface, x, y, pulse)
        _NS_thalakryon._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_thalakryon._draw_aquashield_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thalakryon._draw_metamorph_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thalakryon._draw_tidalrage_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating animation).
        if attacking:
            _NS_thalakryon._draw_thk_attack(surface, boss, x, y)
        elif moving:
            _NS_thalakryon._draw_thk_float(surface, boss, x, y)
        else:
            _NS_thalakryon._draw_thk_idle(surface, boss, x, y)

        # Aquashield bubble over body.
        if active_skill == "w":
            _NS_thalakryon._draw_aquashield_bubble(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_thalakryon._draw_typhoon_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thalakryon._draw_metamorph_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thalakryon._draw_tidalrage_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_thk_previous_timer", 0))
        active = bool(getattr(boss, "_thk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._thk_attack_active = True
            boss._thk_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._thk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._thk_attack_frame = int(getattr(boss, "_thk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._thk_attack_active = False
            boss._thk_attack_frame = 0
            active = False

        boss._thk_previous_timer = timer
        boss._thk_attack_progress = (
            min(1.0, getattr(boss, "_thk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_thk_last_x"):
            boss._thk_last_x = boss.x
            boss._thk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._thk_last_x)
        dy = abs(boss.y - boss._thk_last_y)
        boss._thk_last_x = boss.x
        boss._thk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (Floating base animation)
    # ============================================================
    def _draw_thk_idle(surface, boss, x, y):
        # Floating hover - gentle up/down + slight sway.
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_thalakryon._draw_shadow(surface, x, y + 55)
        _NS_thalakryon._draw_water_wisps(surface, x, y + 40, boss.pulse)
        _NS_thalakryon._draw_thk_body(surface, x + sway, y + bob,
                                       boss.direction, boss.pulse, "idle")

    def _draw_thk_float(surface, boss, x, y):
        # Floating forward - more pronounced bob + trail.
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_thalakryon._draw_shadow(surface, x + sway, y + 55)
        _NS_thalakryon._draw_water_wisps(surface, x + sway, y + 40, phase,
                                          trail=True, facing=boss.direction)
        _NS_thalakryon._draw_thk_body(surface, x + sway, y + bob,
                                       boss.direction, phase, "float")

    def _draw_thk_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_thk_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_thk_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Swing animation: wind-up back → forward swing → recovery.
        if progress < 0.35:
            # Wind-up: pull back trident.
            t = progress / 0.35
            lunge = -int(t * 6) * facing
            lift = int(t * 4)
        elif progress < 0.6:
            # Swing forward!
            t = (progress - 0.35) / 0.25
            lunge = int((-6 + t * 18)) * facing
            lift = int(4 - t * 8)
        else:
            # Recovery.
            t = (progress - 0.6) / 0.4
            lunge = int(12 * (1 - t)) * facing
            lift = int(-4 + t * 4)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_thalakryon._draw_shadow(surface, x + lunge, y + 55)
        _NS_thalakryon._draw_water_wisps(surface, x + lunge, y + 40, boss.pulse,
                                          intense=True)
        _NS_thalakryon._draw_thk_body(surface, x + lunge, y - lift + bob,
                                       facing, boss.pulse, "attack",
                                       progress)

    # ============================================================
    # BODY (Humanoid: legs/tail, torso, arms, head, trident)
    # ============================================================
    def _draw_thk_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Humanoid mermidon body with trident."""
        # Back fins first (behind body).
        _NS_thalakryon._draw_back_fins(surface, cx, cy, facing, phase)

        # Lower body (fish tail-like or armored legs).
        _NS_thalakryon._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso (armored chest with scale plates).
        _NS_thalakryon._draw_torso(surface, cx, cy, facing, phase)

        # Compute trident swing angle for attack.
        trident_angle = 0
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: raise back.
                t = attack_progress / 0.35
                trident_angle = -math.pi * 0.35 * t
            elif attack_progress < 0.6:
                # Swing down/forward.
                t = (attack_progress - 0.35) / 0.25
                trident_angle = -math.pi * 0.35 + math.pi * 0.7 * t
            else:
                # Return.
                t = (attack_progress - 0.6) / 0.4
                trident_angle = math.pi * 0.35 * (1 - t)

        # Back arm (behind body).
        _NS_thalakryon._draw_back_arm(surface, cx, cy - 4, facing, phase, action)

        # Head with helmet fins.
        _NS_thalakryon._draw_head(surface, cx + facing * 2, cy - 22, facing,
                                   phase, action, attack_progress)

        # Front arm holding trident.
        _NS_thalakryon._draw_trident_arm(surface, cx, cy - 4, facing, phase,
                                          action, trident_angle,
                                          attack_progress)

    def _draw_back_fins(surface, cx, cy, facing, phase):
        """Fins on back/spine."""
        wave = math.sin(phase * 0.8) * 2

        # Main dorsal fin behind head.
        fin_points = [
            (cx - facing * 8, cy - 18),
            (cx - facing * 14, cy - 28 + int(wave)),
            (cx - facing * 10, cy - 24 + int(wave)),
            (cx - facing * 6, cy - 12),
        ]
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in fin_points])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_dark"], fin_points)
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_mid"], [
            (cx - facing * 8, cy - 18),
            (cx - facing * 12, cy - 26 + int(wave)),
            (cx - facing * 7, cy - 14),
        ])
        # Fin rays.
        for i in range(3):
            t = i / 2
            rx = int(cx - facing * (8 + t * 6))
            ry = cy - 18 - int(t * 10) + int(wave * t)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["fin_light"],
                                    (cx - facing * 7, cy - 14),
                                    (rx, ry), 1)

        # Shoulder fins.
        for side in (-1, 1):
            sh_wave = math.sin(phase * 0.6 + side) * 1
            fx = cx + facing * side * 10
            fy = cy - 12
            shoulder_fin = [
                (fx, fy),
                (fx - facing * 4, fy - 8 + int(sh_wave)),
                (fx + facing * 2, fy - 4),
            ]
            _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_dark"], shoulder_fin)
            _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_mid"], [
                (fx, fy),
                (fx - facing * 3, fy - 6 + int(sh_wave)),
                (fx + facing * 1, fy - 3),
            ])

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Fish-tail lower body (floating, curled)."""
        wave = math.sin(phase * 0.9) * 3
        # Main hip/waist section.
        hip = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy),
            (cx + 8, cy + 6),
            (cx - 8, cy + 6),
            (cx - 12, cy),
        ]
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in hip])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_darkest"], hip)
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_dark"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5), (cx + 11, cy),
            (cx + 7, cy + 5), (cx - 7, cy + 5), (cx - 11, cy),
        ])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_mid"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3), (cx + 9, cy),
            (cx + 5, cy + 3), (cx - 5, cy + 3), (cx - 9, cy),
        ])

        # Scale plates on hip.
        for i, dx in enumerate((-6, -2, 2, 6)):
            pygame.draw.line(surface, _NS_thalakryon.PALETTE["scale_dark"],
                             (cx + dx, cy - 4), (cx + dx + 1, cy - 5), 1)
            pygame.draw.rect(surface, _NS_thalakryon.PALETTE["scale_light"],
                             (cx + dx, cy - 5, 1, 1))

        # Fish tail (curled, floating).
        tail_segments = 6
        prev = (cx, cy + 4)
        for i in range(1, tail_segments + 1):
            t = i / tail_segments
            tx = cx + int(math.sin(phase * 0.7 + t * 2) * 6 * t) - facing * int(t * 2)
            ty = cy + 4 + int(t * 14) + int(wave * t)
            thickness = max(2, 9 - i)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                    (prev[0] + 2, prev[1] + 2),
                                    (tx + 2, ty + 2), thickness + 1)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                    prev, (tx, ty), thickness)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                    prev, (tx, ty), max(1, thickness - 2))
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_mid"],
                                    (prev[0], prev[1] - 1),
                                    (tx, ty - 1), max(1, thickness - 4))
            # Scale texture.
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_thalakryon.PALETTE["scale_mid"],
                                 (tx, ty, 1, 1))
            prev = (tx, ty)

        # Tail fin (large fan at end).
        end = prev
        fin_wave = math.sin(phase * 1.2) * 3
        tail_fin = [
            (end[0], end[1]),
            (end[0] - 10, end[1] + 6 + int(fin_wave)),
            (end[0] - 4, end[1] + 8),
            (end[0], end[1] + 10),
            (end[0] + 4, end[1] + 8),
            (end[0] + 10, end[1] + 6 - int(fin_wave)),
        ]
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_dark"], tail_fin)
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_mid"], [
            (end[0], end[1] + 1),
            (end[0] - 7, end[1] + 5 + int(fin_wave)),
            (end[0], end[1] + 8),
            (end[0] + 7, end[1] + 5 - int(fin_wave)),
        ])
        # Fin rays.
        for i, dx in enumerate((-10, -5, 0, 5, 10)):
            wave_offset = math.sin(phase * 1.2 + i * 0.5) * 1
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["fin_light"],
                                    (end[0], end[1] + 1),
                                    (end[0] + dx, end[1] + 6 + int(wave_offset)),
                                    1)
        # Glowing edges.
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["fin_glow"],
                         (end[0] - 10, end[1] + 6, 1, 1))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["fin_glow"],
                         (end[0] + 10, end[1] + 6, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular armored torso."""
        breath = math.sin(phase * 0.7) * 1

        # Main torso shape.
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
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_darkest"], torso)

        # Blue skin base.
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_dark"], [
            (cx - 11, cy - 13), (cx - 13, cy - 7), (cx - 12, cy),
            (cx - 10, cy + 7), (cx - 8, cy + 13),
            (cx + 8, cy + 13), (cx + 10, cy + 7), (cx + 12, cy),
            (cx + 13, cy - 7), (cx + 11, cy - 13),
        ])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_mid"], [
            (cx - 9, cy - 11), (cx - 11, cy - 5), (cx - 10, cy),
            (cx - 8, cy + 6), (cx - 6, cy + 11),
            (cx + 6, cy + 11), (cx + 8, cy + 6), (cx + 10, cy),
            (cx + 11, cy - 5), (cx + 9, cy - 11),
        ])
        # Muscle highlights.
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_light"], [
            (cx - 5, cy - 8), (cx - 7, cy - 3), (cx - 5, cy + 2),
            (cx - 3, cy + int(breath)),
        ])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_light"], [
            (cx + 5, cy - 8), (cx + 7, cy - 3), (cx + 5, cy + 2),
            (cx + 3, cy + int(breath)),
        ])

        # Green scale chest armor (upper plate).
        chest_plate = [
            (cx - 10, cy - 12),
            (cx + 10, cy - 12),
            (cx + 12, cy - 6),
            (cx + 8, cy - 2),
            (cx, cy - 4),
            (cx - 8, cy - 2),
            (cx - 12, cy - 6),
        ]
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["scale_darkest"], chest_plate)
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["scale_dark"], [
            (cx - 9, cy - 11), (cx + 9, cy - 11), (cx + 11, cy - 6),
            (cx + 7, cy - 3), (cx, cy - 5), (cx - 7, cy - 3),
            (cx - 11, cy - 6),
        ])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["scale_mid"], [
            (cx - 7, cy - 10), (cx + 7, cy - 10), (cx + 9, cy - 6),
            (cx, cy - 6), (cx - 9, cy - 6),
        ])
        # Chest scale detail (chevrons).
        for i, (dx, dy) in enumerate([(-5, -9), (0, -8), (5, -9),
                                       (-4, -6), (4, -6)]):
            pygame.draw.line(surface, _NS_thalakryon.PALETTE["scale_darkest"],
                             (cx + dx - 1, cy + dy),
                             (cx + dx, cy + dy - 1), 1)
            pygame.draw.line(surface, _NS_thalakryon.PALETTE["scale_darkest"],
                             (cx + dx, cy + dy - 1),
                             (cx + dx + 1, cy + dy), 1)
            pygame.draw.rect(surface, _NS_thalakryon.PALETTE["scale_edge"],
                             (cx + dx, cy + dy - 1, 1, 1))
        # Central azure gem on chest.
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["azure_dark"],
                         (cx - 1, cy - 8, 3, 3))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["azure_mid"],
                         (cx - 1, cy - 8, 2, 2))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["azure_light"],
                         (cx - 1, cy - 8, 1, 1))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["azure_shine"],
                         (cx, cy - 8, 1, 1))

        # Abs.
        for i in range(3):
            y_ab = cy + 2 + i * 3
            pygame.draw.line(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                             (cx - 5, y_ab), (cx + 5, y_ab), 1)
            pygame.draw.line(surface, _NS_thalakryon.PALETTE["belly_dark"],
                             (cx - 5, y_ab + 1), (cx + 5, y_ab + 1), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm (partially visible behind torso)."""
        sway = math.sin(phase * 0.5) * 2
        sh_x = cx - facing * 10
        sh_y = cy
        elb_x = cx - facing * 14
        elb_y = cy + 8 + int(sway)
        hand_x = cx - facing * 12
        hand_y = cy + 16

        # Upper arm.
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                (sh_x + 2, sh_y + 2),
                                (elb_x + 2, elb_y + 2), 6)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                (sh_x, sh_y), (elb_x, elb_y), 4)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_mid"],
                                (sh_x - facing, sh_y - 1),
                                (elb_x - facing, elb_y - 1), 2)

        # Forearm.
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                (elb_x + 2, elb_y + 2),
                                (hand_x + 2, hand_y + 2), 5)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                (elb_x, elb_y), (hand_x, hand_y), 4)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                (elb_x, elb_y), (hand_x, hand_y), 3)

        # Hand (claw).
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                  (hand_x, hand_y), 3)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                  (hand_x, hand_y), 2)
        # Claws.
        for i in range(3):
            angle = i * 0.5 - 0.5
            claw_x = hand_x + int(math.cos(angle) * 4) * (-facing)
            claw_y = hand_y + int(math.sin(angle) * 4) + 3
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_darkest"],
                                    (hand_x, hand_y + 1), (claw_x, claw_y), 1)
            pygame.draw.rect(surface, _NS_thalakryon.PALETTE["metal_light"],
                             (claw_x, claw_y, 1, 1))

    def _draw_trident_arm(surface, cx, cy, facing, phase, action,
                           trident_angle, attack_progress):
        """Front arm holding the trident."""
        sh_x = cx + facing * 10
        sh_y = cy

        # Elbow position (varies with trident angle).
        elb_offset = trident_angle
        elb_x = sh_x + int(math.cos(-math.pi * 0.3 + elb_offset) * 10) * facing
        elb_y = sh_y + int(math.sin(-math.pi * 0.3 + elb_offset) * 10) + 4

        # Hand position (grips trident shaft).
        hand_x = elb_x + int(math.cos(elb_offset - math.pi * 0.15) * 10) * facing
        hand_y = elb_y + int(math.sin(elb_offset - math.pi * 0.15) * 10)

        # Upper arm.
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                (sh_x + 2, sh_y + 2),
                                (elb_x + 2, elb_y + 2), 7)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_mid"],
                                (sh_x + facing, sh_y - 1),
                                (elb_x + facing, elb_y - 1), 3)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_light"],
                                (sh_x + facing, sh_y - 2),
                                (elb_x + facing, elb_y - 2), 1)

        # Shoulder pauldron (green scale).
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                  (sh_x + 1, sh_y + 1), 5)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["scale_darkest"],
                                  (sh_x, sh_y), 5)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["scale_dark"],
                                  (sh_x, sh_y), 4)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["scale_mid"],
                                  (sh_x + facing, sh_y - 1), 3)
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["scale_light"],
                         (sh_x + facing, sh_y - 2, 1, 1))

        # Forearm.
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                (elb_x + 2, elb_y + 2),
                                (hand_x + 2, hand_y + 2), 6)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                (elb_x, elb_y), (hand_x, hand_y), 4)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["skin_mid"],
                                (elb_x + facing, elb_y - 1),
                                (hand_x + facing, hand_y - 1), 2)

        # Hand.
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["skin_darkest"],
                                  (hand_x, hand_y), 4)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["skin_dark"],
                                  (hand_x, hand_y), 3)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["skin_mid"],
                                  (hand_x, hand_y - 1), 2)

        # Draw trident.
        _NS_thalakryon._draw_trident(surface, hand_x, hand_y, facing, phase,
                                      trident_angle, action, attack_progress)

    def _draw_trident(surface, hx, hy, facing, phase, angle, action,
                       attack_progress):
        """Ornate trident with azure blade glow."""
        # Trident direction (angle from hand).
        base_angle = -math.pi * 0.5 + angle  # default pointing up

        # Shaft length.
        shaft_len = 32
        head_len = 14

        # Compute shaft.
        shaft_dx = math.cos(base_angle) * facing
        shaft_dy = math.sin(base_angle)

        # Butt end (below hand).
        butt_x = hx - int(shaft_dx * 8)
        butt_y = hy - int(shaft_dy * 8)

        # Head base (top of shaft).
        head_base_x = hx + int(shaft_dx * shaft_len)
        head_base_y = hy + int(shaft_dy * shaft_len)

        # Head tip.
        head_tip_x = head_base_x + int(shaft_dx * head_len)
        head_tip_y = head_base_y + int(shaft_dy * head_len)

        # Shadow shaft.
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                (butt_x + 2, butt_y + 2),
                                (head_base_x + 2, head_base_y + 2), 4)
        # Shaft (dark bronze).
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_darkest"],
                                (butt_x, butt_y),
                                (head_base_x, head_base_y), 3)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_dark"],
                                (butt_x, butt_y),
                                (head_base_x, head_base_y), 2)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_mid"],
                                (butt_x, butt_y),
                                (head_base_x, head_base_y), 1)

        # Shaft grip wraps.
        for i in range(1, 5):
            t = i / 5
            wx = int(butt_x + (head_base_x - butt_x) * t)
            wy = int(butt_y + (head_base_y - butt_y) * t)
            perp_x = -shaft_dy
            perp_y = shaft_dx * facing
            pygame.draw.line(surface, _NS_thalakryon.PALETTE["metal_darkest"],
                             (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                             (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)

        # Trident head crossbar.
        perp_x = -shaft_dy
        perp_y = shaft_dx * facing
        cross_a = (head_base_x + int(perp_x * 6),
                   head_base_y + int(perp_y * 6))
        cross_b = (head_base_x - int(perp_x * 6),
                   head_base_y - int(perp_y * 6))
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_dark"],
                                cross_a, cross_b, 3)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_mid"],
                                cross_a, cross_b, 2)
        _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_light"],
                                cross_a, cross_b, 1)

        # Three prongs.
        for prong_offset in (-6, 0, 6):
            prong_start = (head_base_x + int(perp_x * prong_offset),
                            head_base_y + int(perp_y * prong_offset))
            prong_end = (prong_start[0] + int(shaft_dx * head_len),
                         prong_start[1] + int(shaft_dy * head_len))

            # Prong metal.
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                                    (prong_start[0] + 1, prong_start[1] + 1),
                                    (prong_end[0] + 1, prong_end[1] + 1), 3)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_darkest"],
                                    prong_start, prong_end, 3)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_dark"],
                                    prong_start, prong_end, 2)
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["metal_light"],
                                    prong_start, prong_end, 1)

            # Prong tip glow.
            _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["azure_dark"],
                                      prong_end, 3)
            _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["azure_mid"],
                                      prong_end, 2)
            _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["azure_light"],
                                      prong_end, 1)
            pygame.draw.rect(surface, _NS_thalakryon.PALETTE["azure_shine"],
                             (prong_end[0], prong_end[1], 1, 1))

        # Central azure glow between prongs.
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gx = head_base_x + int(shaft_dx * head_len * 0.5)
        gy = head_base_y + int(shaft_dy * head_len * 0.5)
        for r in range(6, 0, -1):
            alpha = _NS_thalakryon._alpha(120 * glow_pulse * (6 - r) / 6)
            _NS_thalakryon._aacircle(surface, (*_NS_thalakryon.PALETTE["azure_mid"], alpha),
                                      (gx, gy), r)
        _NS_thalakryon._aacircle(surface, _NS_thalakryon.PALETTE["azure_light"],
                                  (gx, gy), 2)
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["azure_shine"],
                         (gx, gy, 1, 1))

        # Swing streak during attack.
        if action == "attack" and 0.35 < attack_progress < 0.65:
            streak_alpha = _NS_thalakryon._alpha(200 *
                math.sin((attack_progress - 0.35) / 0.3 * math.pi))
            for i in range(1, 6):
                t = i * 0.15
                # Backward trail along swing arc.
                trail_angle = base_angle + t * 0.5 * facing
                trail_x = hx + int(math.cos(trail_angle) * (shaft_len + head_len) * facing)
                trail_y = hy + int(math.sin(trail_angle) * (shaft_len + head_len))
                _NS_thalakryon._aacircle(surface,
                                          (*_NS_thalakryon.PALETTE["azure_light"],
                                           streak_alpha // (i + 1)),
                                          (trail_x, trail_y), max(1, 4 - i))

    def _draw_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Head with fin crest, glowing eye."""
        # Head shape.
        head_shape = [
            (cx - 8, cy + 5),
            (cx - 10, cy),
            (cx - 9, cy - 6),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 9, cy - 6),
            (cx + 10, cy),
            (cx + 8, cy + 5),
            (cx + 4, cy + 8),
            (cx - 4, cy + 8),
        ]
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_darkest"], head_shape)

        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_dark"], [
            (cx - 7, cy + 4), (cx - 9, cy), (cx - 8, cy - 5),
            (cx - 3, cy - 9), (cx + 3, cy - 9), (cx + 8, cy - 5),
            (cx + 9, cy), (cx + 7, cy + 4),
            (cx + 3, cy + 7), (cx - 3, cy + 7),
        ])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_mid"], [
            (cx - 5, cy - 2), (cx - 7, cy - 4), (cx - 6, cy - 7),
            (cx - 2, cy - 8), (cx + 2, cy - 8), (cx + 6, cy - 7),
            (cx + 7, cy - 4), (cx + 5, cy - 2),
        ])
        # Face highlight.
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["skin_light"], [
            (cx + facing * 3, cy - 6),
            (cx + facing * 5, cy - 4),
            (cx + facing * 4, cy - 1),
            (cx + facing * 2, cy - 3),
        ])

        # Belly/chin (pale).
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["belly_dark"], [
            (cx - 4, cy + 3), (cx + 4, cy + 3),
            (cx + 3, cy + 7), (cx - 3, cy + 7),
        ])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["belly_mid"], [
            (cx - 3, cy + 4), (cx + 3, cy + 4),
            (cx + 2, cy + 6), (cx - 2, cy + 6),
        ])

        # Head fins/crest (top).
        _NS_thalakryon._draw_head_crest(surface, cx, cy, facing, phase)

        # Cheek fins (side).
        for side in (-1, 1):
            fin_wave = math.sin(phase * 0.6 + side) * 1
            fin_pts = [
                (cx + side * 8, cy),
                (cx + side * 14, cy - 2 + int(fin_wave)),
                (cx + side * 13, cy + 2),
                (cx + side * 8, cy + 3),
            ]
            _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_dark"], fin_pts)
            _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_mid"], [
                (cx + side * 8, cy + 1),
                (cx + side * 12, cy - 1 + int(fin_wave)),
                (cx + side * 11, cy + 2),
            ])
            pygame.draw.rect(surface, _NS_thalakryon.PALETTE["fin_glow"],
                             (cx + side * 13, cy - 1, 1, 1))

        # GLOWING EYE.
        _NS_thalakryon._draw_glowing_eye(surface, cx + facing * 3, cy - 4,
                                          facing, phase)

        # Mouth (fierce, small fangs).
        mouth_y = cy + 5
        pygame.draw.line(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                         (cx - 3, mouth_y), (cx + 3, mouth_y), 1)
        # Small fangs during attack.
        if action == "attack" and attack_progress > 0.3:
            for x_off in (-2, 0, 2):
                pygame.draw.rect(surface, _NS_thalakryon.PALETTE["metal_light"],
                                 (cx + x_off, mouth_y + 1, 1, 1))

    def _draw_head_crest(surface, cx, cy, facing, phase):
        """Top head fin crest (like a shark/fish crown)."""
        wave = math.sin(phase * 0.8) * 1

        # Main crest fin (rises up from top of head).
        crest = [
            (cx - 6, cy - 9),
            (cx - 8, cy - 16 + int(wave)),
            (cx - 3, cy - 14 + int(wave)),
            (cx, cy - 18 + int(wave)),
            (cx + 3, cy - 14 - int(wave)),
            (cx + 8, cy - 16 - int(wave)),
            (cx + 6, cy - 9),
        ]
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in crest])
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_dark"], crest)
        _NS_thalakryon._poly(surface, _NS_thalakryon.PALETTE["fin_mid"], [
            (cx - 5, cy - 10),
            (cx - 6, cy - 14 + int(wave)),
            (cx, cy - 16 + int(wave)),
            (cx + 6, cy - 14 - int(wave)),
            (cx + 5, cy - 10),
        ])
        # Fin rays.
        for dx in (-6, -2, 2, 6):
            _NS_thalakryon._aaline(surface, _NS_thalakryon.PALETTE["fin_light"],
                                    (cx + dx // 2, cy - 10),
                                    (cx + dx, cy - 15 + int(wave * 0.5)), 1)
        # Glowing tips.
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["fin_glow"],
                         (cx, cy - 18, 1, 1))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["fin_glow"],
                         (cx - 8, cy - 16, 1, 1))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["fin_glow"],
                         (cx + 8, cy - 16, 1, 1))

    def _draw_glowing_eye(surface, cx, cy, facing, phase):
        """Bright cyan glowing eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        ex = cx
        ey = cy

        # Deep socket.
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))

        # Glow halo.
        for radius in range(6, 0, -1):
            alpha = _NS_thalakryon._alpha(90 * (6 - radius) / 6 * pulse)
            _NS_thalakryon._aacircle(surface,
                                      (*_NS_thalakryon.PALETTE["eye_mid"], alpha),
                                      (ex + 1, ey), radius)

        # Iris.
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["eye_darkest"],
                         (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["eye_dark"],
                         (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["eye_mid"],
                         (ex + 1, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["eye_light"],
                         (ex + 1, ey, 1, 1))
        # Bright core.
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["eye_glow"],
                         (ex + 2, ey, 1, 1))
        pygame.draw.rect(surface, _NS_thalakryon.PALETTE["white"],
                         (ex + 2, ey - 1, 1, 1))

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
        pygame.draw.ellipse(shadow, (2, 3, 5, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (15, 40, 70, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_abyssal_aura(surface, x, y, phase):
        """Large intimidating blue + abyss purple aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_thalakryon._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_thalakryon._aacircle(aura,
                                          (*_NS_thalakryon.PALETTE["water_dark"], alpha),
                                          (110, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_thalakryon._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thalakryon._aacircle(aura,
                                          (*_NS_thalakryon.PALETTE["water_mid"], alpha),
                                          (110, 100), radius)
        # Abyss purple accent.
        for radius in range(35, 5, -3):
            alpha = _NS_thalakryon._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thalakryon._aacircle(aura,
                                          (*_NS_thalakryon.PALETTE["abyss_dark"], alpha),
                                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Floating bubbles/particles.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = (_NS_thalakryon.PALETTE["water_light"] if i % 3 != 0
                     else _NS_thalakryon.PALETTE["abyss_light"])
            hot_color = (_NS_thalakryon.PALETTE["water_foam"] if i % 3 != 0
                         else _NS_thalakryon.PALETTE["abyss_light"])
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thalakryon.PALETTE["water_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_thalakryon.PALETTE["azure_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_thalakryon.PALETTE["azure_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_thalakryon.PALETTE["abyss_dark"], 180),
                            (40, 24, 90, 14), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_thalakryon.PALETTE["azure_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_thalakryon.PALETTE["azure_hot"],
                 _NS_thalakryon._alpha(150 * pulse)),
                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    def _draw_water_wisps(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Water/mist wisps floating below."""
        strength = 1.5 if intense else 1.0

        # Base mist cloud.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_thalakryon._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_thalakryon.PALETTE["water_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(24, 3, -2):
            alpha = _NS_thalakryon._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_thalakryon.PALETTE["water_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising bubbles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_thalakryon._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_thalakryon._aacircle(surface,
                (*_NS_thalakryon.PALETTE["water_dark"], alpha), (sx, sy), 3)
            _NS_thalakryon._aacircle(surface,
                (*_NS_thalakryon.PALETTE["water_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                (*_NS_thalakryon.PALETTE["water_light"], alpha),
                (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_thalakryon.PALETTE["water_foam"], alpha),
                (sx, sy - 2, 1, 1))

        # Cyan sparkles.
        for i in range(8):
            ember_t = (phase * 0.6 + i * 0.15) % 1.0
            ex = cx - 26 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 24)
            alpha = _NS_thalakryon._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                    (*_NS_thalakryon.PALETTE["azure_mid"], alpha),
                    (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_thalakryon.PALETTE["azure_hot"], alpha),
                    (ex, ey, 1, 1))

        # Abyss purple wisps.
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 20 + i * 10 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 20)
            alpha = _NS_thalakryon._alpha(180 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["abyss_dark"], alpha), (wx, wy), 2)
                pygame.draw.rect(surface,
                    _NS_thalakryon.PALETTE["abyss_light"], (wx, wy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_thalakryon._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["water_dark"], alpha),
                    (sx, sy), max(2, 7 - i))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["water_mid"], alpha),
                    (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                    (*_NS_thalakryon.PALETTE["azure_light"], alpha),
                    (sx, sy - 1, 2, 2))

    # ============================================================
    # SKILL: Q - TYPHOON (charge forward + water vortex projectile)
    # ============================================================
    def _draw_typhoon_skill(surface, boss, x, y, timer, phase):
        """Water vortex projectile launched from trident."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_thalakryon._target_position(boss, x, y)

        if progress < 0.2:
            # Charge at trident tip.
            t = progress / 0.2
            tip_x = x + facing * 36
            tip_y = y - 30
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_thalakryon._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_darkest"], alpha),
                    (tip_x, tip_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_thalakryon._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_dark"], alpha),
                    (tip_x, tip_y), r)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_mid"], (tip_x, tip_y), cr - 2)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_light"], (tip_x, tip_y),
                max(1, cr - 4))
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_shine"], (tip_x, tip_y),
                max(1, cr - 6))

            # Swirl sparks.
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = tip_x + int(math.cos(angle) * (cr + 3))
                sy = tip_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface,
                    _NS_thalakryon.PALETTE["azure_hot"], (sx, sy, 1, 1))
        else:
            # Projectile flight.
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 36
            start_y = y - 30
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Swirling vortex trail.
            for i in range(11):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_thalakryon._alpha(240 - i * 22)

                size = max(1, 9 - i)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_darkest"], alpha),
                    (px, py), size)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_dark"], alpha),
                    (px, py), max(1, size - 1))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_mid"], alpha),
                    (px, py), max(1, size - 2))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_light"], alpha),
                    (px, py), max(1, size - 3))

                # Swirl water rings.
                if i < 5:
                    for s in range(3):
                        angle_s = t * 8 + i + s * 2
                        spark_x = px + int(math.sin(angle_s) * (size + 2))
                        spark_y = py + int(math.cos(angle_s) * (size + 2))
                        pygame.draw.rect(surface,
                            (*_NS_thalakryon.PALETTE["water_foam"], alpha),
                            (spark_x, spark_y, 1, 1))

            # Big bright head.
            for r in range(15, 3, -2):
                alpha = _NS_thalakryon._alpha(100 * (15 - r) / 15)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_light"], alpha),
                    (bx, by), r)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_darkest"], (bx, by), 10)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_dark"], (bx, by), 8)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_mid"], (bx, by), 5)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_light"], (bx, by), 3)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_shine"], (bx, by), 1)
            pygame.draw.rect(surface,
                _NS_thalakryon.PALETTE["white"], (bx, by, 1, 1))

            # Impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 30)
                alpha = _NS_thalakryon._alpha(240 * (1 - st))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_darkest"], alpha),
                    (tx, ty), radius + 4, 3)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_dark"], alpha),
                    (tx, ty), radius, 3)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_mid"], alpha),
                    (tx, ty), max(1, radius - 5), 2)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_light"], alpha),
                    (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                        (*_NS_thalakryon.PALETTE["water_foam"], alpha),
                        (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - AQUATIC SHIELD (bubble/shell shield around boss)
    # ============================================================
    def _draw_aquashield_ground(surface, boss, x, y, timer, phase):
        """Water rings under boss during shield."""
        for i in range(2):
            r = int(30 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_thalakryon._alpha(200 - i * 60)
            _NS_thalakryon._aacircle(surface,
                (*_NS_thalakryon.PALETTE["azure_mid"], alpha),
                (x, y + 40), r, 2)
            _NS_thalakryon._aacircle(surface,
                (*_NS_thalakryon.PALETTE["azure_light"], alpha),
                (x, y + 40), r, 1)

    def _draw_aquashield_bubble(surface, boss, x, y, timer, phase):
        """Bubble/shell shield around boss."""
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multiple ring layers (bubble effect).
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            _NS_thalakryon._aacircle(bubble,
                (*_NS_thalakryon.PALETTE["water_dark"], alpha_val),
                center, r - i, thickness)
            _NS_thalakryon._aacircle(bubble,
                (*_NS_thalakryon.PALETTE["water_mid"], alpha_val),
                center, r - i - 1, 1)

        # Bubble surface highlights (shine).
        for i in range(3):
            highlight_angle = -math.pi / 4 + i * 0.3
            hx = center[0] + int(math.cos(highlight_angle) * (r - 5))
            hy = center[1] + int(math.sin(highlight_angle) * (r - 5))
            _NS_thalakryon._aacircle(bubble,
                _NS_thalakryon.PALETTE["water_foam"], (hx, hy), 3 - i)

        # Rotating sparkles.
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble,
                _NS_thalakryon.PALETTE["azure_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble,
                _NS_thalakryon.PALETTE["azure_hot"], (sx, sy, 1, 1))

        # Shell segments (bottom half like clam).
        for i in range(-2, 3):
            angle = math.pi * 0.5 + i * 0.25  # bottom arc
            seg_x1 = center[0] + int(math.cos(angle) * r)
            seg_y1 = center[1] + int(math.sin(angle) * r)
            seg_x2 = center[0] + int(math.cos(angle) * (r - 8))
            seg_y2 = center[1] + int(math.sin(angle) * (r - 8))
            pygame.draw.line(bubble,
                (*_NS_thalakryon.PALETTE["scale_mid"], 200),
                (seg_x1, seg_y1), (seg_x2, seg_y2), 2)
            pygame.draw.line(bubble,
                (*_NS_thalakryon.PALETTE["scale_light"], 200),
                (seg_x1, seg_y1), (seg_x2, seg_y2), 1)

        surface.blit(bubble, (x - r - 10, y - r - 10))

        # Water droplets floating around.
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            dx = x + int(math.cos(angle) * (r + 10))
            dy = y + int(math.sin(angle) * (r + 10))
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["water_light"], (dx, dy), 2)
            pygame.draw.rect(surface,
                _NS_thalakryon.PALETTE["water_foam"], (dx, dy, 1, 1))

    # ============================================================
    # SKILL: E - TIDAL RAGE (rage buff + water column)
    # ============================================================
    def _draw_tidalrage_ground(surface, boss, x, y, timer, phase):
        """Rage aura circle."""
        for i in range(3):
            r = int(35 + i * 5 + math.sin(phase * 3 + i) * 2)
            alpha = _NS_thalakryon._alpha(180 - i * 40)
            _NS_thalakryon._aacircle(surface,
                (*_NS_thalakryon.PALETTE["azure_dark"], alpha),
                (x, y + 40), r, 2)

    def _draw_tidalrage_foreground(surface, boss, x, y, timer, phase):
        """Rising water columns around boss (rage state)."""
        # Water spouts rising around boss (columns).
        num_spouts = 6
        for i in range(num_spouts):
            angle = i * math.pi * 2 / num_spouts + phase * 0.2
            sx = x + int(math.cos(angle) * 45)
            sy_base = y + 40 + int(math.sin(angle) * 15)

            # Rising column.
            for layer in range(8):
                layer_t = (phase * 0.6 + i * 0.2 + layer * 0.12) % 1.0
                layer_y = sy_base - int(layer_t * 40)
                layer_alpha = _NS_thalakryon._alpha(200 * (1 - layer_t))
                layer_w = int(4 + layer_t * 3)
                layer_h = int(3 + layer_t * 2)

                pygame.draw.ellipse(surface,
                    (*_NS_thalakryon.PALETTE["water_dark"], layer_alpha),
                    (sx - layer_w, layer_y - layer_h,
                     layer_w * 2, layer_h * 2))
                pygame.draw.ellipse(surface,
                    (*_NS_thalakryon.PALETTE["water_mid"], layer_alpha),
                    (sx - layer_w + 1, layer_y - layer_h + 1,
                     layer_w * 2 - 2, layer_h * 2 - 2))
                pygame.draw.rect(surface,
                    (*_NS_thalakryon.PALETTE["water_light"], layer_alpha),
                    (sx, layer_y, 1, 1))
                pygame.draw.rect(surface,
                    (*_NS_thalakryon.PALETTE["water_foam"], layer_alpha),
                    (sx, layer_y - 1, 1, 1))

        # Aura sparks around boss.
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.5
            sr = 40 + int(math.sin(phase * 2 + i) * 5)
            sx = x + int(math.cos(angle) * sr)
            sy = y + int(math.sin(angle) * sr * 0.6)
            pygame.draw.rect(surface,
                _NS_thalakryon.PALETTE["azure_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                _NS_thalakryon.PALETTE["azure_hot"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL: R - METAMORPHOSIS (tidal wave + kraken tentacles)
    # ============================================================
    def _draw_metamorph_ground(surface, boss, x, y, timer, phase):
        """Massive tidal wave forming at target."""
        tx, ty = _NS_thalakryon._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up warning ring.
            t = progress / 0.3
            r = int(40 * t)
            alpha = _NS_thalakryon._alpha(180 * t)
            pygame.draw.ellipse(surface,
                (*_NS_thalakryon.PALETTE["azure_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface,
                    _NS_thalakryon.PALETTE["azure_light"], (sx, sy, 2, 2))
        else:
            # Post-strike pool.
            t = (progress - 0.3) / 0.7
            r = int(40 + t * 30)
            alpha = _NS_thalakryon._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                (*_NS_thalakryon.PALETTE["water_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                (*_NS_thalakryon.PALETTE["water_dark"], alpha),
                (tx - r + 3, ty - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                (*_NS_thalakryon.PALETTE["water_mid"], alpha),
                (tx - r + 8, ty - r // 3 + 4,
                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_metamorph_foreground(surface, boss, x, y, timer, phase):
        """Kraken tentacles rising + tidal wave crashing."""
        tx, ty = _NS_thalakryon._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge energy above target.
            t = progress / 0.3
            gather_y = ty - int((1 - t) * 60)
            gather_r = int(4 + t * 4)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_thalakryon._alpha(180 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["azure_dark"], alpha),
                    (tx, gather_y), r)
            _NS_thalakryon._aacircle(surface,
                _NS_thalakryon.PALETTE["azure_light"],
                (tx, gather_y), gather_r - 2)
            pygame.draw.rect(surface,
                _NS_thalakryon.PALETTE["azure_shine"],
                (tx, gather_y, 1, 1))
        elif progress < 0.65:
            # TIDAL WAVE + kraken tentacles.
            t = (progress - 0.3) / 0.35
            intensity = math.sin(t * math.pi)

            # Tidal wave (large curved shape rising).
            wave_h = int(60 * t)
            wave_alpha = _NS_thalakryon._alpha(220 * intensity)

            # Wave body.
            wave_pts = []
            for i in range(20):
                wx = tx - 60 + i * 6
                wy = ty - int(math.sin(i / 20 * math.pi) * wave_h)
                wave_pts.append((wx, wy))
            wave_pts.append((tx + 60, ty + 20))
            wave_pts.append((tx - 60, ty + 20))

            wave_surf = pygame.Surface((160, 100), pygame.SRCALPHA)
            offset_x = tx - 80
            offset_y = ty - 80
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in wave_pts]

            _NS_thalakryon._poly(wave_surf,
                (*_NS_thalakryon.PALETTE["water_darkest"], wave_alpha),
                local_pts)
            # Lighter inner.
            inner_pts = []
            cx_l = sum(p[0] for p in local_pts) / len(local_pts)
            cy_l = sum(p[1] for p in local_pts) / len(local_pts)
            for p in local_pts:
                inner_pts.append(
                    (int(p[0] * 0.85 + cx_l * 0.15),
                     int(p[1] * 0.85 + cy_l * 0.15))
                )
            _NS_thalakryon._poly(wave_surf,
                (*_NS_thalakryon.PALETTE["water_dark"], wave_alpha),
                inner_pts)
            inner2 = []
            for p in local_pts:
                inner2.append(
                    (int(p[0] * 0.7 + cx_l * 0.3),
                     int(p[1] * 0.7 + cy_l * 0.3))
                )
            _NS_thalakryon._poly(wave_surf,
                (*_NS_thalakryon.PALETTE["water_mid"], wave_alpha),
                inner2)

            # Wave crest (foam).
            for i in range(0, 20, 2):
                wx = tx - 60 + i * 6 - offset_x
                wy = ty - int(math.sin(i / 20 * math.pi) * wave_h) - offset_y
                pygame.draw.rect(wave_surf,
                    (*_NS_thalakryon.PALETTE["water_foam"], wave_alpha),
                    (wx, wy, 2, 2))
                pygame.draw.rect(wave_surf,
                    (*_NS_thalakryon.PALETTE["azure_light"], wave_alpha),
                    (wx, wy - 1, 1, 1))

            surface.blit(wave_surf, (offset_x, offset_y))

            # Kraken tentacles rising around boss.
            for tent_i in range(5):
                base_angle = tent_i * math.pi * 2 / 5 + phase * 0.15
                base_x = x + int(math.cos(base_angle) * 30)
                base_y = y + 30

                # Tentacle segments.
                prev = (base_x, base_y)
                seg_count = 8
                for seg in range(1, seg_count + 1):
                    seg_t = seg / seg_count
                    curve = math.sin(phase * 2 + tent_i + seg_t * 3) * 8
                    seg_x = base_x + int(math.cos(base_angle) * seg_t * 20 + curve)
                    seg_y = base_y - int(seg_t * 50 * intensity)
                    thickness = max(2, 8 - seg)

                    tent_alpha = _NS_thalakryon._alpha(220 * intensity)
                    _NS_thalakryon._aaline(surface,
                        (*_NS_thalakryon.PALETTE["shadow_deep"], tent_alpha),
                        (prev[0] + 1, prev[1] + 1),
                        (seg_x + 1, seg_y + 1), thickness + 1)
                    _NS_thalakryon._aaline(surface,
                        (*_NS_thalakryon.PALETTE["tentacle_dark"], tent_alpha),
                        prev, (seg_x, seg_y), thickness)
                    _NS_thalakryon._aaline(surface,
                        (*_NS_thalakryon.PALETTE["tentacle_mid"], tent_alpha),
                        prev, (seg_x, seg_y), max(1, thickness - 2))
                    # Sucker highlights.
                    if seg % 2 == 0:
                        pygame.draw.rect(surface,
                            (*_NS_thalakryon.PALETTE["tentacle_light"], tent_alpha),
                            (seg_x, seg_y, 1, 1))
                    prev = (seg_x, seg_y)

                # Tentacle tip curl.
                tip_glow_alpha = _NS_thalakryon._alpha(200 * intensity)
                _NS_thalakryon._aacircle(surface,
                    (*_NS_thalakryon.PALETTE["tentacle_light"], tip_glow_alpha),
                    prev, 2)
        else:
            # Aftermath: settling water + mist.
            t = (progress - 0.65) / 0.35
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 35)
                alpha = _NS_thalakryon._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_thalakryon._aacircle(surface,
                        (*_NS_thalakryon.PALETTE["water_mid"], alpha),
                        (rx, ry), 3)
                    _NS_thalakryon._aacircle(surface,
                        (*_NS_thalakryon.PALETTE["water_light"], alpha),
                        (rx, ry), 2)
                    pygame.draw.rect(surface,
                        (*_NS_thalakryon.PALETTE["water_foam"], alpha),
                        (rx, ry, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_aeralith(surface, boss, x, y):
    """Entry point aeralith."""
    return _NS_aeralith.draw_aeralith(surface, boss, x, y)


def draw_aurex(surface, boss, x, y):
    """Entry point aurex."""
    return _NS_aurex_omega.draw_aurex_omega(surface, boss, x, y)


def draw_nyxareva(surface, boss, x, y):
    """Entry point nyxareva."""
    return _NS_nyxareva.draw_nyxareva(surface, boss, x, y)


def draw_thalakryon(surface, boss, x, y):
    """Entry point thalakryon."""
    return _NS_thalakryon.draw_thalakryon(surface, boss, x, y)
