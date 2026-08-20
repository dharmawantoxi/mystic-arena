"""
bosses/level12.py - Semua boss Level 12

Berisi:
  - aurelix    (mini boss - Time Sovereign)
  - aurelyssa  (mini boss - Golden Blade Dancer)
  - vargrath   (mini boss - Demonic Warlord)
  - nazulmor   (TRUE BOSS - Deepborn Herald / eldritch)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# aurelix.py
# ====================================================================

# ====================================================================
# AURELIX - THE FALLEN REGENT (Mini Boss)
# ====================================================================


class _NS_aurelix:
    """Namespace aurelix - Mini Boss Time-Sovereign."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe deep blue (main cape/cloak)
        "robe_darkest": (5, 8, 25),
        "robe_dark": (15, 25, 60),
        "robe_mid": (35, 55, 110),
        "robe_light": (75, 105, 170),
        "robe_edge": (140, 170, 220),

        # Gold armor (chestplate, greaves, crown)
        "gold_darkest": (35, 20, 5),
        "gold_dark": (95, 65, 15),
        "gold_mid": (180, 135, 40),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 170),
        "gold_white": (255, 255, 220),

        # Skin (aged pale)
        "skin_darkest": (55, 35, 30),
        "skin_dark": (110, 80, 65),
        "skin_mid": (175, 140, 115),
        "skin_light": (225, 195, 165),
        "skin_shine": (250, 230, 210),

        # White beard/hair
        "hair_dark": (90, 90, 100),
        "hair_mid": (170, 170, 180),
        "hair_light": (230, 230, 235),
        "hair_shine": (255, 255, 255),

        # Time/magic glow (bright yellow-gold)
        "magic_darkest": (40, 25, 5),
        "magic_dark": (110, 75, 15),
        "magic_mid": (210, 155, 40),
        "magic_light": (255, 210, 90),
        "magic_hot": (255, 240, 160),
        "magic_shine": (255, 255, 220),

        # Eye glow (bright gold)
        "eye_socket": (5, 4, 2),
        "eye_darkest": (40, 25, 5),
        "eye_dark": (120, 85, 20),
        "eye_mid": (220, 170, 50),
        "eye_light": (255, 230, 130),
        "eye_glow": (255, 255, 200),

        # Gem (blue sapphire on crown)
        "gem_dark": (20, 40, 90),
        "gem_mid": (60, 110, 200),
        "gem_light": (140, 200, 255),
        "gem_shine": (230, 245, 255),

        # Shadow/void (fallen regent theme)
        "void_darkest": (5, 3, 15),
        "void_dark": (20, 12, 40),
        "void_mid": (55, 30, 90),
        "void_light": (110, 70, 160),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_aurelix._clamp(color)
        if _NS_aurelix.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_aurelix._clamp(color)
        if _NS_aurelix.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_aurelix._clamp(color), points)

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
    def draw_aurelix(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_aurelix._detect_moving(boss)
        _NS_aurelix._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_aur_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_aurelix._draw_gold_aura(surface, x, y, pulse)
        _NS_aurelix._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_aurelix._draw_will_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelix._draw_transcend_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurelix._draw_shockwave_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_aurelix._draw_aur_attack(surface, boss, x, y)
        elif moving:
            _NS_aurelix._draw_aur_float(surface, boss, x, y)
        else:
            _NS_aurelix._draw_aur_idle(surface, boss, x, y)

        # W bubble over body.
        if active_skill == "w":
            _NS_aurelix._draw_will_bubble(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_aurelix._draw_timebomb_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurelix._draw_shockwave_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelix._draw_transcend_foreground(surface, boss, x, y, skill_timer, pulse)

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
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_aur_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_aurelix._draw_shadow(surface, x, y + 55)
        _NS_aurelix._draw_gold_wisps(surface, x, y + 40, boss.pulse)
        _NS_aurelix._draw_aur_body(surface, x + sway, y + bob,
                                    boss.direction, boss.pulse, "idle")

    def _draw_aur_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_aurelix._draw_shadow(surface, x + sway, y + 55)
        _NS_aurelix._draw_gold_wisps(surface, x + sway, y + 40, phase,
                                      trail=True, facing=boss.direction)
        _NS_aurelix._draw_aur_body(surface, x + sway, y + bob,
                                    boss.direction, phase, "float")

    def _draw_aur_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_aur_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_aur_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Staff cast animation: raise staff → point forward → recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * facing
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 12)) * facing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(8 * (1 - t)) * facing
            lift = int(-2 + t * 2)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_aurelix._draw_shadow(surface, x + lunge, y + 55)
        _NS_aurelix._draw_gold_wisps(surface, x + lunge, y + 40, boss.pulse,
                                      intense=True)
        _NS_aurelix._draw_aur_body(surface, x + lunge, y - lift + bob,
                                    facing, boss.pulse, "attack",
                                    progress)
        # Basic attack projectile (gold orb).
        _NS_aurelix._draw_gold_bolt(surface, boss, x + lunge, y - lift + bob,
                                     progress)

    # ============================================================
    # BODY
    # ============================================================
    def _draw_aur_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Humanoid king with robe, staff, crown."""
        # Cape behind body.
        _NS_aurelix._draw_cape(surface, cx, cy, facing, phase)

        # Robe lower (flowing).
        _NS_aurelix._draw_robe(surface, cx, cy + 18, facing, phase)

        # Torso armor.
        _NS_aurelix._draw_torso(surface, cx, cy, facing, phase)

        # Compute staff cast progress.
        staff_raise = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                staff_raise = -t * 0.4
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                staff_raise = -0.4 + t * 0.6
            else:
                t = (attack_progress - 0.6) / 0.4
                staff_raise = 0.2 * (1 - t)

        # Back arm (behind).
        _NS_aurelix._draw_back_arm(surface, cx, cy - 4, facing, phase)

        # Head + crown + beard.
        _NS_aurelix._draw_head(surface, cx + facing * 2, cy - 22, facing,
                                phase, action, attack_progress)

        # Front arm holding staff.
        _NS_aurelix._draw_staff_arm(surface, cx, cy - 4, facing, phase,
                                     action, staff_raise, attack_progress)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Long flowing cape behind body."""
        wave = math.sin(phase * 0.7) * 2

        # Cape shape (behind body, flowing down).
        cape = [
            (cx - facing * 10, cy - 14),
            (cx - facing * 18 + int(wave), cy - 8),
            (cx - facing * 22 + int(wave), cy + 6),
            (cx - facing * 20 + int(wave * 0.5), cy + 22),
            (cx - facing * 14, cy + 30 + int(wave * 0.5)),
            (cx - facing * 4, cy + 32),
            (cx + facing * 2, cy + 30),
            (cx + facing * 4, cy + 14),
            (cx - facing * 2, cy - 12),
        ]
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in cape])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_darkest"], cape)
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_dark"], [
            (cx - facing * 9, cy - 13),
            (cx - facing * 17 + int(wave), cy - 7),
            (cx - facing * 21 + int(wave), cy + 5),
            (cx - facing * 19 + int(wave * 0.5), cy + 21),
            (cx - facing * 13, cy + 28 + int(wave * 0.5)),
            (cx - facing * 4, cy + 30),
            (cx + facing * 2, cy + 28),
            (cx + facing * 3, cy + 13),
            (cx - facing * 2, cy - 11),
        ])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_mid"], [
            (cx - facing * 12, cy - 8),
            (cx - facing * 17 + int(wave * 0.7), cy),
            (cx - facing * 15 + int(wave * 0.5), cy + 18),
            (cx - facing * 6, cy + 24),
            (cx - facing * 2, cy + 12),
            (cx - facing * 6, cy - 5),
        ])

        # Gold trim along cape edge.
        trim_points = [
            (cx - facing * 18 + int(wave), cy - 8),
            (cx - facing * 22 + int(wave), cy + 6),
            (cx - facing * 20 + int(wave * 0.5), cy + 22),
            (cx - facing * 14, cy + 30 + int(wave * 0.5)),
        ]
        for i in range(len(trim_points) - 1):
            _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_dark"],
                                 trim_points[i], trim_points[i + 1], 2)
            _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_mid"],
                                 trim_points[i], trim_points[i + 1], 1)

        # Gold decorative pattern on cape.
        for i, dy in enumerate((-4, 4, 14, 22)):
            gx = cx - facing * (10 + i * 2)
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_dark"],
                             (gx - 1, cy + dy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_mid"],
                             (gx, cy + dy, 1, 1))
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                             (gx, cy + dy, 1, 1))

    def _draw_robe(surface, cx, cy, facing, phase):
        """Lower robe/skirt flowing."""
        wave = math.sin(phase * 0.9) * 2

        # Main robe skirt (wide bottom).
        robe = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 14, cy + 4),
            (cx + 16, cy + 14),
            (cx + 12, cy + 22 + int(wave * 0.5)),
            (cx + 4, cy + 26),
            (cx - 4, cy + 26),
            (cx - 12, cy + 22 - int(wave * 0.5)),
            (cx - 16, cy + 14),
            (cx - 14, cy + 4),
        ]
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in robe])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_darkest"], robe)
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_dark"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5), (cx + 13, cy + 4),
            (cx + 15, cy + 13), (cx + 11, cy + 21),
            (cx + 4, cy + 25), (cx - 4, cy + 25),
            (cx - 11, cy + 21), (cx - 15, cy + 13), (cx - 13, cy + 4),
        ])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_mid"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3), (cx + 11, cy + 4),
            (cx + 13, cy + 12), (cx + 8, cy + 20),
            (cx, cy + 22), (cx - 8, cy + 20),
            (cx - 13, cy + 12), (cx - 11, cy + 4),
        ])

        # Vertical folds (drape lines).
        for i, dx in enumerate((-8, -4, 0, 4, 8)):
            wave_off = math.sin(phase * 0.9 + i) * 1
            pygame.draw.line(surface, _NS_aurelix.PALETTE["robe_darkest"],
                             (cx + dx, cy),
                             (cx + int(dx * 1.4) + int(wave_off), cy + 22), 1)

        # Gold hem at bottom.
        hem_pts = [
            (cx - 14, cy + 20),
            (cx - 12, cy + 22 - int(wave * 0.5)),
            (cx - 4, cy + 26),
            (cx + 4, cy + 26),
            (cx + 12, cy + 22 + int(wave * 0.5)),
            (cx + 14, cy + 20),
        ]
        for i in range(len(hem_pts) - 1):
            _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_dark"],
                                 hem_pts[i], hem_pts[i + 1], 2)
            _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_mid"],
                                 hem_pts[i], hem_pts[i + 1], 1)
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                         (cx, cy + 26, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Gold-plated torso armor."""
        breath = math.sin(phase * 0.7) * 1

        # Torso base (blue robe underlayer).
        base = [
            (cx - 11, cy - 14),
            (cx - 13, cy - 8),
            (cx - 12, cy),
            (cx - 10, cy + 8),
            (cx - 8, cy + 14),
            (cx + 8, cy + 14),
            (cx + 10, cy + 8),
            (cx + 12, cy),
            (cx + 13, cy - 8),
            (cx + 11, cy - 14),
        ]
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in base])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_darkest"], base)
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["robe_dark"], [
            (cx - 10, cy - 13), (cx - 12, cy - 7), (cx - 11, cy),
            (cx - 9, cy + 7), (cx - 7, cy + 13),
            (cx + 7, cy + 13), (cx + 9, cy + 7), (cx + 11, cy),
            (cx + 12, cy - 7), (cx + 10, cy - 13),
        ])

        # Gold chest plate (large ornate armor).
        chest = [
            (cx - 10, cy - 12),
            (cx + 10, cy - 12),
            (cx + 12, cy - 4),
            (cx + 10, cy + 4),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 10, cy + 4),
            (cx - 12, cy - 4),
        ]
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_darkest"], chest)
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_dark"], [
            (cx - 9, cy - 11), (cx + 9, cy - 11), (cx + 11, cy - 4),
            (cx + 9, cy + 3), (cx + 5, cy + 9), (cx - 5, cy + 9),
            (cx - 9, cy + 3), (cx - 11, cy - 4),
        ])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_mid"], [
            (cx - 7, cy - 9), (cx + 7, cy - 9), (cx + 9, cy - 3),
            (cx + 7, cy + 2), (cx + 4, cy + 7), (cx - 4, cy + 7),
            (cx - 7, cy + 2), (cx - 9, cy - 3),
        ])

        # Chest highlight.
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_light"], [
            (cx + facing * 2, cy - 7),
            (cx + facing * 6, cy - 5),
            (cx + facing * 5, cy),
            (cx + facing * 1, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                         (cx + facing * 4, cy - 6, 1, 1))

        # Central sapphire gem on chest.
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_dark"],
                         (cx - 2, cy - 6, 5, 5))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_dark"],
                         (cx - 1, cy - 5, 3, 3))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_mid"],
                         (cx - 1, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_light"],
                         (cx - 1, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_shine"],
                         (cx, cy - 5, 1, 1))

        # Belt (gold band).
        pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_darkest"],
                         (cx - 11, cy + 9), (cx + 11, cy + 9), 3)
        pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_dark"],
                         (cx - 11, cy + 9), (cx + 11, cy + 9), 2)
        pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_mid"],
                         (cx - 11, cy + 9), (cx + 11, cy + 9), 1)
        # Belt buckle.
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_dark"],
                         (cx - 2, cy + 8, 5, 4))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_light"],
                         (cx - 1, cy + 9, 3, 2))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                         (cx, cy + 10, 1, 1))

        # Shoulder pauldrons.
        for side in (-1, 1):
            sh_x = cx + side * 11
            sh_y = cy - 11
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["shadow_deep"],
                                    (sh_x + 1, sh_y + 1), 5)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_darkest"],
                                    (sh_x, sh_y), 5)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_dark"],
                                    (sh_x, sh_y), 4)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_mid"],
                                    (sh_x + side, sh_y - 1), 3)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_light"],
                                    (sh_x + side, sh_y - 1), 2)
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                             (sh_x + side, sh_y - 2, 1, 1))
            # Small gem in pauldron.
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_mid"],
                             (sh_x, sh_y, 1, 1))
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_light"],
                             (sh_x, sh_y, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase):
        sway = math.sin(phase * 0.5) * 1
        sh_x = cx - facing * 10
        sh_y = cy
        elb_x = cx - facing * 12
        elb_y = cy + 10 + int(sway)
        hand_x = cx - facing * 8
        hand_y = cy + 18

        # Upper arm.
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["shadow_deep"],
                             (sh_x + 2, sh_y + 2),
                             (elb_x + 2, elb_y + 2), 5)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_darkest"],
                             (sh_x, sh_y), (elb_x, elb_y), 4)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_dark"],
                             (sh_x, sh_y), (elb_x, elb_y), 3)

        # Forearm.
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["shadow_deep"],
                             (elb_x + 2, elb_y + 2),
                             (hand_x + 2, hand_y + 2), 4)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_darkest"],
                             (elb_x, elb_y), (hand_x, hand_y), 3)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_dark"],
                             (elb_x, elb_y), (hand_x, hand_y), 2)

        # Hand (skin).
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["skin_darkest"],
                                (hand_x, hand_y), 3)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["skin_mid"],
                         (hand_x, hand_y - 1, 1, 1))

    def _draw_staff_arm(surface, cx, cy, facing, phase, action, raise_amt,
                         attack_progress):
        """Front arm holding the staff."""
        sh_x = cx + facing * 10
        sh_y = cy

        # Arm goes forward-up to hold staff.
        elb_x = sh_x + int(math.cos(-math.pi * 0.15 + raise_amt) * 10) * facing
        elb_y = sh_y + int(math.sin(-math.pi * 0.15 + raise_amt) * 10)

        hand_x = elb_x + int(math.cos(-math.pi * 0.3 + raise_amt) * 10) * facing
        hand_y = elb_y + int(math.sin(-math.pi * 0.3 + raise_amt) * 10)

        # Upper arm.
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["shadow_deep"],
                             (sh_x + 2, sh_y + 2),
                             (elb_x + 2, elb_y + 2), 6)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_darkest"],
                             (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_dark"],
                             (sh_x, sh_y), (elb_x, elb_y), 4)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["robe_mid"],
                             (sh_x + facing, sh_y - 1),
                             (elb_x + facing, elb_y - 1), 2)

        # Gold armor band on upper arm.
        band_mid = ((sh_x + elb_x) // 2, (sh_y + elb_y) // 2)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_dark"],
                                band_mid, 3)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_mid"],
                                band_mid, 2)
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                         (band_mid[0], band_mid[1], 1, 1))

        # Forearm (gold gauntlet).
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["shadow_deep"],
                             (elb_x + 2, elb_y + 2),
                             (hand_x + 2, hand_y + 2), 6)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_darkest"],
                             (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_dark"],
                             (elb_x, elb_y), (hand_x, hand_y), 4)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_mid"],
                             (elb_x, elb_y), (hand_x, hand_y), 2)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_light"],
                             (elb_x + facing, elb_y - 1),
                             (hand_x + facing, hand_y - 1), 1)

        # Hand.
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_darkest"],
                                (hand_x, hand_y), 4)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_dark"],
                                (hand_x, hand_y), 3)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_mid"],
                                (hand_x, hand_y - 1), 2)
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                         (hand_x, hand_y - 1, 1, 1))

        # Draw the staff.
        _NS_aurelix._draw_staff(surface, hand_x, hand_y, facing, phase,
                                 raise_amt, action, attack_progress)

    def _draw_staff(surface, hx, hy, facing, phase, raise_amt, action,
                     attack_progress):
        """Ornate staff with gold clockwork orb on top."""
        # Staff pointing upward from hand (angled based on raise_amt).
        base_angle = -math.pi * 0.5 + raise_amt

        shaft_len = 40
        # Butt end (below hand).
        butt_x = hx - int(math.cos(base_angle) * 10) * facing
        butt_y = hy - int(math.sin(base_angle) * 10)

        # Orb position (top of staff).
        orb_x = hx + int(math.cos(base_angle) * shaft_len) * facing
        orb_y = hy + int(math.sin(base_angle) * shaft_len)

        # Shadow.
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["shadow_deep"],
                             (butt_x + 2, butt_y + 2),
                             (orb_x + 2, orb_y + 2), 4)
        # Shaft (dark wood + gold).
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_darkest"],
                             (butt_x, butt_y), (orb_x, orb_y), 3)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_dark"],
                             (butt_x, butt_y), (orb_x, orb_y), 2)
        _NS_aurelix._aaline(surface, _NS_aurelix.PALETTE["gold_mid"],
                             (butt_x, butt_y), (orb_x, orb_y), 1)

        # Staff wraps/bindings.
        for i in range(1, 5):
            t = i / 5
            wx = int(butt_x + (orb_x - butt_x) * t)
            wy = int(butt_y + (orb_y - butt_y) * t)
            perp_x = -math.sin(base_angle) * facing
            perp_y = math.cos(base_angle)
            pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_light"],
                             (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                             (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)

        # ORB at top (clockwork/time theme).
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Outer glow.
        for r in range(10, 2, -1):
            alpha = _NS_aurelix._alpha(100 * pulse * (10 - r) / 10)
            _NS_aurelix._aacircle(surface,
                                    (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                                    (orb_x, orb_y), r)

        # Orb body (gold with inner glow).
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["shadow_deep"],
                                (orb_x + 1, orb_y + 1), 6)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_darkest"],
                                (orb_x, orb_y), 6)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_dark"],
                                (orb_x, orb_y), 5)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_dark"],
                                (orb_x, orb_y), 4)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_mid"],
                                (orb_x, orb_y), 3)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_light"],
                                (orb_x, orb_y), 2)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_shine"],
                                (orb_x, orb_y), 1)

        # Clock hands rotating inside orb.
        hand_angle_1 = phase * 0.5
        hand_angle_2 = phase * 1.5
        h1x = orb_x + int(math.cos(hand_angle_1) * 3)
        h1y = orb_y + int(math.sin(hand_angle_1) * 3)
        h2x = orb_x + int(math.cos(hand_angle_2) * 2)
        h2y = orb_y + int(math.sin(hand_angle_2) * 2)
        pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_darkest"],
                         (orb_x, orb_y), (h1x, h1y), 1)
        pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_darkest"],
                         (orb_x, orb_y), (h2x, h2y), 1)

        # Gold ring around orb (like clock face).
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_mid"],
                                (orb_x, orb_y), 7, 1)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_light"],
                                (orb_x, orb_y), 8, 1)

        # Hour markers (small dots around ring).
        for i in range(4):
            angle = i * math.pi / 2 + phase * 0.1
            mx = orb_x + int(math.cos(angle) * 8)
            my = orb_y + int(math.sin(angle) * 8)
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                             (mx, my, 1, 1))

        # Sparkles around orb during attack.
        if action == "attack" and attack_progress > 0.3:
            for i in range(6):
                angle_s = phase * 4 + i * math.pi / 3
                sx = orb_x + int(math.cos(angle_s) * 12)
                sy = orb_y + int(math.sin(angle_s) * 12)
                pygame.draw.rect(surface, _NS_aurelix.PALETTE["magic_hot"],
                                 (sx, sy, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Old king head: beard, crown, glowing eyes."""
        # Head shape (aged, angular).
        head_shape = [
            (cx - 7, cy + 4),
            (cx - 9, cy),
            (cx - 8, cy - 6),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 8, cy - 6),
            (cx + 9, cy),
            (cx + 7, cy + 4),
        ]
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["skin_darkest"], head_shape)
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["skin_dark"], [
            (cx - 6, cy + 3), (cx - 8, cy), (cx - 7, cy - 5),
            (cx - 2, cy - 9), (cx + 2, cy - 9), (cx + 7, cy - 5),
            (cx + 8, cy), (cx + 6, cy + 3),
        ])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["skin_mid"], [
            (cx - 5, cy - 2), (cx - 6, cy - 4), (cx - 5, cy - 7),
            (cx - 1, cy - 8), (cx + 1, cy - 8), (cx + 5, cy - 7),
            (cx + 6, cy - 4), (cx + 5, cy - 2),
        ])
        # Highlight.
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["skin_light"],
                         (cx + facing * 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["skin_shine"],
                         (cx + facing * 3, cy - 5, 1, 1))

        # Wrinkles.
        pygame.draw.line(surface, _NS_aurelix.PALETTE["skin_darkest"],
                         (cx - 3, cy - 4), (cx - 1, cy - 4), 1)
        pygame.draw.line(surface, _NS_aurelix.PALETTE["skin_darkest"],
                         (cx + 1, cy - 4), (cx + 3, cy - 4), 1)

        # WHITE BEARD (long, flowing).
        _NS_aurelix._draw_beard(surface, cx, cy, facing, phase)

        # WHITE HAIR (behind head).
        _NS_aurelix._draw_hair(surface, cx, cy, facing, phase)

        # CROWN (golden with gem).
        _NS_aurelix._draw_crown(surface, cx, cy, facing, phase)

        # GLOWING EYES.
        _NS_aurelix._draw_king_eye(surface, cx + facing * 2, cy - 4, facing, phase)

    def _draw_beard(surface, cx, cy, facing, phase):
        """Long flowing white beard."""
        wave = math.sin(phase * 0.7) * 1

        # Beard shape (below face, hanging down).
        beard = [
            (cx - 6, cy + 2),
            (cx + 6, cy + 2),
            (cx + 8, cy + 6),
            (cx + 7, cy + 14 + int(wave)),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 7, cy + 14 - int(wave)),
            (cx - 8, cy + 6),
        ]
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in beard])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_dark"], beard)
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_mid"], [
            (cx - 5, cy + 3), (cx + 5, cy + 3), (cx + 7, cy + 6),
            (cx + 6, cy + 13 + int(wave)), (cx + 2, cy + 18),
            (cx - 2, cy + 18), (cx - 6, cy + 13 - int(wave)),
            (cx - 7, cy + 6),
        ])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_light"], [
            (cx - 3, cy + 5), (cx + 3, cy + 5), (cx + 4, cy + 10),
            (cx + 2, cy + 15), (cx - 2, cy + 15), (cx - 4, cy + 10),
        ])

        # Beard strand highlights.
        for i, dx in enumerate((-4, -1, 2, 5)):
            wave_off = math.sin(phase * 0.7 + i * 0.3) * 1
            pygame.draw.line(surface, _NS_aurelix.PALETTE["hair_shine"],
                             (cx + dx, cy + 4),
                             (cx + dx + int(wave_off), cy + 15), 1)

        # Mustache.
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_mid"], [
            (cx - 5, cy - 1), (cx + 5, cy - 1),
            (cx + 6, cy + 2), (cx - 6, cy + 2),
        ])
        _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_light"], [
            (cx - 4, cy), (cx + 4, cy),
            (cx + 5, cy + 1), (cx - 5, cy + 1),
        ])

    def _draw_hair(surface, cx, cy, facing, phase):
        """White hair behind head."""
        # Hair on back/sides.
        for side in (-1, 1):
            hair_pts = [
                (cx + side * 8, cy - 6),
                (cx + side * 11, cy - 2),
                (cx + side * 12, cy + 4),
                (cx + side * 10, cy + 8),
                (cx + side * 8, cy + 4),
            ]
            _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_dark"], hair_pts)
            _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["hair_mid"], [
                (cx + side * 8, cy - 5),
                (cx + side * 10, cy - 1),
                (cx + side * 11, cy + 3),
                (cx + side * 9, cy + 6),
                (cx + side * 8, cy + 3),
            ])
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["hair_light"],
                             (cx + side * 10, cy, 1, 1))

    def _draw_crown(surface, cx, cy, facing, phase):
        """Golden crown with spikes and gem."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Base band.
        base_y = cy - 8
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["shadow_deep"],
                         (cx - 7, base_y + 1, 15, 4))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_darkest"],
                         (cx - 7, base_y, 14, 4))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_dark"],
                         (cx - 7, base_y, 14, 3))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_mid"],
                         (cx - 6, base_y, 12, 2))
        pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_light"],
                         (cx - 6, base_y), (cx + 5, base_y), 1)

        # Crown spikes (5 pointed).
        spike_positions = [(-6, 4), (-3, 6), (0, 8), (3, 6), (6, 4)]
        for dx, height in spike_positions:
            spike_top_y = base_y - height
            # Shadow.
            _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["shadow_deep"], [
                (cx + dx + 1, spike_top_y + 1),
                (cx + dx - 1, base_y + 1),
                (cx + dx + 2, base_y + 1),
            ])
            # Dark base.
            _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_darkest"], [
                (cx + dx, spike_top_y),
                (cx + dx - 1, base_y),
                (cx + dx + 2, base_y),
            ])
            # Mid layer.
            _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_dark"], [
                (cx + dx, spike_top_y),
                (cx + dx, base_y),
                (cx + dx + 1, base_y),
            ])
            # Highlight (FIX: use proper triangle instead of 2-point line).
            _NS_aurelix._poly(surface, _NS_aurelix.PALETTE["gold_mid"], [
                (cx + dx, spike_top_y),
                (cx + dx - 1, spike_top_y + 2),
                (cx + dx + 1, spike_top_y + 2),
            ])
            # Spike tip glow.
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_shine"],
                             (cx + dx, spike_top_y, 1, 1))

        # Central sapphire gem (large).
        gem_x = cx
        gem_y = cy - 4
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gold_dark"],
                         (gem_x - 2, gem_y - 1, 5, 3))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_dark"],
                         (gem_x - 1, gem_y, 3, 2))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_mid"],
                         (gem_x - 1, gem_y, 2, 1))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_light"],
                         (gem_x, gem_y, 1, 1))
        # Gem shine (pulsing).
        if pulse > 0.85:
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["gem_shine"],
                             (gem_x, gem_y, 1, 1))
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["white"],
                             (gem_x + 1, gem_y, 1, 1))

    def _draw_king_eye(surface, cx, cy, facing, phase):
        """Glowing gold eye (fallen king ominous)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        ex = cx
        ey = cy

        # Socket.
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))

        # Halo.
        for radius in range(5, 0, -1):
            alpha = _NS_aurelix._alpha(90 * (5 - radius) / 5 * pulse)
            _NS_aurelix._aacircle(surface,
                                    (*_NS_aurelix.PALETTE["eye_mid"], alpha),
                                    (ex + 1, ey), radius)

        # Iris.
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["eye_darkest"],
                         (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["eye_dark"],
                         (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["eye_mid"],
                         (ex + 1, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["eye_light"],
                         (ex + 1, ey, 1, 1))
        pygame.draw.rect(surface, _NS_aurelix.PALETTE["eye_glow"],
                         (ex + 2, ey, 1, 1))

    # ============================================================
    # AUTO ATTACK PROJECTILE (small gold bolt)
    # ============================================================
    def _draw_gold_bolt(surface, boss, x, y, progress):
        """Small gold magic orb projectile."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_aurelix._target_position(boss, x, y)
        start_x = x + facing * 30
        start_y = y - 45  # from orb position

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail.
        for i in range(7):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_aurelix._alpha(220 - i * 28)
            size = max(1, 5 - i)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_darkest"], alpha),
                (px, py), size)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                (px, py), max(1, size - 1))
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                (px, py), max(1, size - 2))
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_light"], alpha),
                (px, py), max(1, size - 3))

        # Head.
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_darkest"],
                                (bx, by), 5)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_dark"],
                                (bx, by), 4)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_mid"],
                                (bx, by), 3)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_light"],
                                (bx, by), 2)
        _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_shine"],
                                (bx, by), 1)

        # Impact.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(6 + st * 18)
            alpha = _NS_aurelix._alpha(200 * (1 - st))
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], alpha), (tx, ty), radius, 2)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                (tx, ty), max(1, radius - 4), 1)

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
        pygame.draw.ellipse(shadow, (2, 2, 4, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (35, 25, 5, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_gold_aura(surface, x, y, phase):
        """Golden aura + void purple undertone."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_aurelix._alpha((85 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_aurelix._aacircle(aura,
                    (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                    (110, 100), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_aurelix._alpha((50 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_aurelix._aacircle(aura,
                    (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                    (110, 100), radius)
        # Void purple undertone.
        for radius in range(30, 5, -3):
            alpha = _NS_aurelix._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_aurelix._aacircle(aura,
                    (*_NS_aurelix.PALETTE["void_dark"], alpha),
                    (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Floating gold particles.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = (_NS_aurelix.PALETTE["magic_light"] if i % 3 != 0
                     else _NS_aurelix.PALETTE["void_light"])
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["magic_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Gold rune ring on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_aurelix.PALETTE["magic_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_aurelix.PALETTE["magic_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_aurelix.PALETTE["gold_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_aurelix.PALETTE["void_dark"], 180),
                            (40, 24, 90, 14), 1)

        # Roman numeral marks around ring (clock face).
        for i in range(12):
            angle = phase * 0.2 + i * math.pi / 6
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_aurelix.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_aurelix.PALETTE["magic_hot"],
                 _NS_aurelix._alpha(150 * pulse)),
                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    def _draw_gold_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Gold mist wisps."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_aurelix._alpha((32 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_aurelix._alpha((20 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising sparks.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_aurelix._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_aurelix.PALETTE["magic_hot"], alpha),
                (sx, sy, 1, 1))

        # Void wisps (fallen theme).
        for i in range(4):
            wisp_t = (phase * 0.5 + i * 0.25) % 1.0
            wx = cx - 20 + i * 12 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 18)
            alpha = _NS_aurelix._alpha(160 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_aurelix._aacircle(surface,
                    (*_NS_aurelix.PALETTE["void_dark"], alpha), (wx, wy), 2)
                pygame.draw.rect(surface,
                    _NS_aurelix.PALETTE["void_light"], (wx, wy, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_aurelix._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_aurelix._aacircle(surface,
                    (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                    (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface,
                    (*_NS_aurelix.PALETTE["magic_light"], alpha),
                    (sx, sy - 1, 2, 2))

    # ============================================================
    # SKILL: Q - TIME BOMB (projectile → delayed explosion)
    # ============================================================
    def _draw_timebomb_skill(surface, boss, x, y, timer, phase):
        """Time bomb: thrown → lands → ticks → explodes."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_aurelix._target_position(boss, x, y)

        if progress < 0.15:
            # Charge at orb.
            t = progress / 0.15
            tip_x = x + facing * 30
            tip_y = y - 45
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_aurelix._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_aurelix._aacircle(surface,
                    (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                    (tip_x, tip_y), r)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_mid"],
                                    (tip_x, tip_y), cr - 2)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_light"],
                                    (tip_x, tip_y), max(1, cr - 4))
        elif progress < 0.45:
            # Throw arc.
            t = (progress - 0.15) / 0.3
            start_x = x + facing * 30
            start_y = y - 45
            # Parabolic arc.
            bx = int(start_x + (tx - start_x) * t)
            arc_h = -60 * math.sin(t * math.pi)
            by = int(start_y + (ty - start_y) * t + arc_h)

            # Clock bomb (small clock face).
            for r in range(8, 0, -1):
                alpha = _NS_aurelix._alpha(150 * (8 - r) / 8)
                _NS_aurelix._aacircle(surface,
                    (*_NS_aurelix.PALETTE["magic_mid"], alpha), (bx, by), r)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_darkest"],
                                    (bx, by), 6)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_dark"],
                                    (bx, by), 5)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_mid"],
                                    (bx, by), 4)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_light"],
                                    (bx, by), 3)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_mid"],
                                    (bx, by), 6, 1)

            # Clock hands.
            hand_angle = phase * 3
            hx = bx + int(math.cos(hand_angle) * 4)
            hy = by + int(math.sin(hand_angle) * 4)
            pygame.draw.line(surface, _NS_aurelix.PALETTE["gold_darkest"],
                             (bx, by), (hx, hy), 1)

            # Trail.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                trail_arc = -60 * math.sin(trail_t * math.pi)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t + trail_arc)
                alpha = _NS_aurelix._alpha(200 - i * 30)
                pygame.draw.rect(surface,
                    (*_NS_aurelix.PALETTE["magic_hot"], alpha),
                    (px, py, 2, 2))
        elif progress < 0.75:
            # Ticking on ground (bomb waiting).
            t = (progress - 0.45) / 0.3
            tick_pulse = math.sin(phase * 8) * 0.5 + 0.5
            # Bomb sits on ground.
            bx, by = tx, ty
            r_pulse = 6 + int(tick_pulse * 3)

            # Warning circle (grows).
            warn_r = int(30 + t * 20)
            warn_alpha = _NS_aurelix._alpha(150 + tick_pulse * 100)
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], warn_alpha),
                (bx - warn_r, by - warn_r // 3, warn_r * 2, warn_r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], warn_alpha),
                (bx - warn_r + 3, by - warn_r // 3 + 2,
                 warn_r * 2 - 6, warn_r * 2 // 3 - 4), 2)

            # Bomb.
            for r in range(r_pulse + 3, 0, -1):
                alpha = _NS_aurelix._alpha(200 * (r_pulse + 3 - r) / (r_pulse + 3))
                _NS_aurelix._aacircle(surface,
                    (*_NS_aurelix.PALETTE["magic_mid"], alpha), (bx, by), r)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_darkest"],
                                    (bx, by), 6)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["gold_dark"],
                                    (bx, by), 5)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_hot"],
                                    (bx, by), 3)
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["magic_shine"],
                             (bx, by, 1, 1))
        else:
            # EXPLOSION.
            t = (progress - 0.75) / 0.25
            radius = int(15 + t * 45)
            alpha = _NS_aurelix._alpha(240 * (1 - t))

            # Explosion ring.
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_darkest"], alpha),
                (tx, ty), radius + 4, 3)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                (tx, ty), radius, 3)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                (tx, ty), max(1, radius - 5), 2)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_light"], alpha),
                (tx, ty), max(1, radius - 12), 1)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_hot"], alpha),
                (tx, ty), max(1, radius // 4))

            # Radial burst.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.75)
                pygame.draw.line(surface,
                    (*_NS_aurelix.PALETTE["magic_light"], alpha),
                    (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                    (*_NS_aurelix.PALETTE["magic_shine"], alpha),
                    (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - UNYIELDING WILL (golden shield)
    # ============================================================
    def _draw_will_ground(surface, boss, x, y, timer, phase):
        """Gold rings under boss."""
        for i in range(2):
            r = int(30 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_aurelix._alpha(200 - i * 60)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                (x, y + 40), r, 2)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_light"], alpha),
                (x, y + 40), r, 1)

    def _draw_will_bubble(surface, boss, x, y, timer, phase):
        """Gold dome shield (like a tomb)."""
        breath = math.sin(phase * 2) * 2
        r = 55 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Dome outer ring.
        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_aurelix._aacircle(bubble,
                (*_NS_aurelix.PALETTE["gold_dark"], alpha_val),
                center, r - i, thickness)
            _NS_aurelix._aacircle(bubble,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha_val),
                center, r - i - 1, 1)

        # Fill inside.
        for radius in range(r - 3, 5, -4):
            alpha = _NS_aurelix._alpha(50)
            _NS_aurelix._aacircle(bubble,
                (*_NS_aurelix.PALETTE["magic_light"], alpha), center, radius)

        # Rune circles rotating.
        for i in range(12):
            angle = phase * 1.2 + i * math.pi / 6
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_aurelix.PALETTE["magic_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_aurelix.PALETTE["magic_shine"],
                             (sx, sy, 1, 1))

        # Highlight (top-left arc).
        for i in range(3):
            hl_angle = -math.pi / 3 + i * 0.2
            hx = center[0] + int(math.cos(hl_angle) * (r - 5))
            hy = center[1] + int(math.sin(hl_angle) * (r - 5))
            _NS_aurelix._aacircle(bubble, _NS_aurelix.PALETTE["magic_shine"],
                                    (hx, hy), 3 - i)

        # Vertical runes inside (like tomb pillars).
        for dx in (-25, 0, 25):
            pygame.draw.line(bubble,
                (*_NS_aurelix.PALETTE["magic_hot"], 150),
                (center[0] + dx, center[1] - r + 15),
                (center[0] + dx, center[1] + r - 15), 1)

        surface.blit(bubble, (x - r - 10, y - r - 10))

    # ============================================================
    # SKILL: E - MAGIC SHOCKWAVE (arc wave forward)
    # ============================================================
    def _draw_shockwave_ground(surface, boss, x, y, timer, phase):
        """Shockwave arc on ground in front of boss."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up (small radius grows).
            t = progress / 0.3
            r = int(20 * t)
            alpha = _NS_aurelix._alpha(200 * t)
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                (x - r, y + 30 - r // 3, r * 2, r * 2 // 3), 2)
        else:
            # Wave expands outward in facing direction.
            t = (progress - 0.3) / 0.7
            wave_r = int(30 + t * 100)
            alpha = _NS_aurelix._alpha(220 * (1 - t))

            # Arc in front of boss (half-ellipse).
            # Draw multiple concentric arcs for wave effect.
            for i in range(3):
                arc_r = wave_r - i * 8
                if arc_r < 5:
                    continue
                arc_alpha = _NS_aurelix._alpha(alpha * (1 - i * 0.3))

                # Draw partial ellipse (front-facing arc).
                arc_surf = pygame.Surface((arc_r * 2 + 4, arc_r + 20),
                                          pygame.SRCALPHA)
                pygame.draw.ellipse(arc_surf,
                    (*_NS_aurelix.PALETTE["magic_dark"], arc_alpha),
                    (0, 0, arc_r * 2, arc_r), 3)
                pygame.draw.ellipse(arc_surf,
                    (*_NS_aurelix.PALETTE["magic_mid"], arc_alpha),
                    (3, 3, arc_r * 2 - 6, arc_r - 6), 2)
                pygame.draw.ellipse(arc_surf,
                    (*_NS_aurelix.PALETTE["magic_light"], arc_alpha),
                    (6, 6, arc_r * 2 - 12, arc_r - 12), 1)

                # Blit only front half based on facing.
                if facing == 1:
                    src = pygame.Rect(arc_r, 0, arc_r + 4, arc_r + 20)
                    surface.blit(arc_surf, (x, y + 30 - arc_r // 2), src)
                else:
                    src = pygame.Rect(0, 0, arc_r, arc_r + 20)
                    surface.blit(arc_surf, (x - arc_r, y + 30 - arc_r // 2), src)

    def _draw_shockwave_foreground(surface, boss, x, y, timer, phase):
        """Shockwave sparks + debris flying."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            wave_r = int(30 + t * 100)
            alpha = _NS_aurelix._alpha(220 * (1 - t))

            # Sparks along wave front.
            for i in range(20):
                # Spread over 180 degrees in facing direction.
                if facing == 1:
                    angle = -math.pi / 2 + i * math.pi / 19
                else:
                    angle = math.pi / 2 + i * math.pi / 19
                sx = x + int(math.cos(angle) * wave_r)
                sy = y + 30 + int(math.sin(angle) * wave_r * 0.5)

                # Random height for arc effect.
                if i % 2 == 0:
                    pygame.draw.rect(surface,
                        (*_NS_aurelix.PALETTE["magic_hot"], alpha),
                        (sx, sy, 2, 2))
                    pygame.draw.rect(surface,
                        (*_NS_aurelix.PALETTE["magic_shine"], alpha),
                        (sx, sy, 1, 1))
                else:
                    pygame.draw.rect(surface,
                        (*_NS_aurelix.PALETTE["magic_light"], alpha),
                        (sx, sy - 1, 1, 1))
                    pygame.draw.rect(surface,
                        (*_NS_aurelix.PALETTE["gold_shine"], alpha),
                        (sx, sy - 2, 1, 1))

            # Debris particles.
            for i in range(12):
                deb_t = (phase * 0.8 + i * 0.1) % 1.0
                deb_r = int(wave_r * 0.7 * deb_t)
                if facing == 1:
                    deb_angle = -math.pi / 2 + i * math.pi / 11
                else:
                    deb_angle = math.pi / 2 + i * math.pi / 11
                dx = x + int(math.cos(deb_angle) * deb_r)
                dy = y + 30 + int(math.sin(deb_angle) * deb_r * 0.5)
                dy -= int(math.sin(deb_t * math.pi) * 12)  # arc height
                deb_alpha = _NS_aurelix._alpha(200 * (1 - deb_t) * (1 - t))
                pygame.draw.rect(surface,
                    (*_NS_aurelix.PALETTE["gold_dark"], deb_alpha),
                    (dx, dy, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_aurelix.PALETTE["gold_light"], deb_alpha),
                    (dx, dy, 1, 1))

    # ============================================================
    # SKILL: R - TRANSCENDENCE (time-freeze + light pillars)
    # ============================================================
    def _draw_transcend_ground(surface, boss, x, y, timer, phase):
        """Large clock face on ground at target."""
        tx, ty = _NS_aurelix._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Wind-up: clock face appears.
            t = progress / 0.3
            r = int(60 * t)
            alpha = _NS_aurelix._alpha(200 * t)

            # Clock face outer.
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                (tx - r + 3, ty - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4), 2)

            # Roman numerals around clock.
            for i in range(12):
                angle = i * math.pi / 6 - math.pi / 2
                nx = tx + int(math.cos(angle) * r * 0.85)
                ny = ty + int(math.sin(angle) * r * 0.85 * 0.5)
                # Simple mark.
                pygame.draw.line(surface,
                    (*_NS_aurelix.PALETTE["magic_light"], alpha),
                    (nx - 1, ny - 1), (nx + 1, ny + 1), 1)
                pygame.draw.rect(surface,
                    (*_NS_aurelix.PALETTE["magic_shine"], alpha),
                    (nx, ny, 1, 1))
        else:
            # Post-strike: clock face lingers with pool.
            t = (progress - 0.3) / 0.7
            r = int(60 + t * 20)
            alpha = _NS_aurelix._alpha(200 * (1 - t * 0.5))

            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                (tx - r + 4, ty - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6), 2)
            pygame.draw.ellipse(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], alpha),
                (tx - r + 10, ty - r // 3 + 5,
                 r * 2 - 20, r * 2 // 3 - 10), 1)

    def _draw_transcend_foreground(surface, boss, x, y, timer, phase):
        """Vertical light pillars slamming down from sky."""
        tx, ty = _NS_aurelix._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge above target.
            t = progress / 0.3
            gather_y = ty - int((1 - t) * 80)
            gather_r = int(4 + t * 6)
            for r in range(gather_r + 4, 0, -1):
                alpha = _NS_aurelix._alpha(200 * (gather_r + 4 - r) / (gather_r + 4))
                _NS_aurelix._aacircle(surface,
                    (*_NS_aurelix.PALETTE["magic_dark"], alpha),
                    (tx, gather_y), r)
            _NS_aurelix._aacircle(surface, _NS_aurelix.PALETTE["magic_light"],
                                    (tx, gather_y), gather_r - 2)
            pygame.draw.rect(surface, _NS_aurelix.PALETTE["magic_shine"],
                             (tx, gather_y, 1, 1))
        elif progress < 0.7:
            # STRIKE: multiple light pillars around target area.
            t = (progress - 0.3) / 0.4
            intensity = math.sin(t * math.pi)

            # Main center pillar.
            _NS_aurelix._draw_light_pillar(surface, tx, ty, intensity, True)

            # Surrounding pillars (radiating outward).
            pillar_positions = [(-40, -10), (40, 5), (-25, 15), (25, -12),
                                 (-55, 8), (55, -5)]
            for i, (dx, dy) in enumerate(pillar_positions):
                appearance_t = max(0.0, t - i * 0.06)
                if appearance_t <= 0:
                    continue
                px = tx + dx
                py = ty + dy
                pillar_int = min(1.0, appearance_t * 3) * intensity
                _NS_aurelix._draw_light_pillar(surface, px, py, pillar_int, False)

            # Central explosion.
            impact_r = int(15 + t * 30)
            impact_alpha = _NS_aurelix._alpha(240 * intensity)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_darkest"], impact_alpha),
                (tx, ty), impact_r + 3, 3)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_dark"], impact_alpha),
                (tx, ty), impact_r, 3)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_mid"], impact_alpha),
                (tx, ty), max(1, impact_r - 6), 2)
            _NS_aurelix._aacircle(surface,
                (*_NS_aurelix.PALETTE["magic_light"], impact_alpha),
                (tx, ty), max(1, impact_r - 12), 1)
        else:
            # Aftermath: fading pillars + gold sparks.
            t = (progress - 0.7) / 0.3
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - int(rise_t * 40)
                alpha = _NS_aurelix._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface,
                        (*_NS_aurelix.PALETTE["magic_hot"], alpha),
                        (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                        (*_NS_aurelix.PALETTE["magic_shine"], alpha),
                        (rx, ry, 1, 1))

    def _draw_light_pillar(surface, px, py, intensity, is_main):
        """Vertical light pillar from sky."""
        if intensity <= 0:
            return

        pillar_top = max(0, py - 180)
        widths_alphas = [
            (10, 80), (7, 120), (4, 170), (2, 220), (1, 255),
        ] if is_main else [
            (6, 60), (4, 100), (2, 160), (1, 220),
        ]

        for width, alpha_val in widths_alphas:
            actual_alpha = _NS_aurelix._alpha(alpha_val * intensity)
            if actual_alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_aurelix.PALETTE["magic_light"], actual_alpha),
                (px - width // 2, pillar_top, width, py - pillar_top))

        # Bright core.
        core_alpha = _NS_aurelix._alpha(255 * intensity)
        pygame.draw.rect(surface,
            (*_NS_aurelix.PALETTE["magic_shine"], core_alpha),
            (px, pillar_top, 1, py - pillar_top))

        # Ground splash.
        _NS_aurelix._aacircle(surface,
            (*_NS_aurelix.PALETTE["magic_mid"],
             _NS_aurelix._alpha(200 * intensity)),
            (px, py), 8 if is_main else 5)
        _NS_aurelix._aacircle(surface,
            (*_NS_aurelix.PALETTE["magic_light"],
             _NS_aurelix._alpha(240 * intensity)),
            (px, py), 5 if is_main else 3)
        _NS_aurelix._aacircle(surface,
            _NS_aurelix.PALETTE["magic_shine"],
            (px, py), 2 if is_main else 1)


# ====================================================================
# aurelyssa.py
# ====================================================================

# ====================================================================
# AURELYSSA - The Golden Blade Dancer (Mini Boss)
# Melee Agility - Sword dancer with butterfly phantom aura
# ====================================================================


class _NS_aurelyssa:
    """Namespace aurelyssa - Golden Sword Dancer mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Golden aura (main theme)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (110, 75, 15),
        "gold_mid": (200, 150, 40),
        "gold_light": (255, 210, 90),
        "gold_hot": (255, 235, 150),
        "gold_shine": (255, 250, 210),

        # Armor (silver-steel with gold trim)
        "armor_darkest": (25, 28, 40),
        "armor_dark": (60, 68, 85),
        "armor_mid": (120, 130, 150),
        "armor_light": (190, 200, 220),
        "armor_shine": (240, 245, 255),

        # Skin (light peach)
        "skin_dark": (140, 95, 75),
        "skin_mid": (215, 170, 140),
        "skin_light": (245, 215, 190),
        "skin_shine": (255, 240, 225),

        # Hair (blonde/gold)
        "hair_darkest": (80, 50, 15),
        "hair_dark": (160, 110, 35),
        "hair_mid": (220, 175, 70),
        "hair_light": (250, 220, 130),
        "hair_shine": (255, 245, 195),

        # Cloth/cape (dark blue-purple with gold)
        "cloth_dark": (25, 20, 55),
        "cloth_mid": (55, 45, 100),
        "cloth_light": (110, 90, 160),

        # Blade (glowing gold steel)
        "blade_darkest": (80, 60, 20),
        "blade_dark": (170, 130, 40),
        "blade_mid": (230, 195, 80),
        "blade_light": (255, 230, 140),
        "blade_shine": (255, 250, 210),

        # Eye (golden bright)
        "eye_socket": (5, 5, 10),
        "eye_dark": (90, 60, 15),
        "eye_mid": (220, 170, 50),
        "eye_light": (255, 230, 130),
        "eye_glow": (255, 250, 200),

        # Butterfly wings (translucent gold)
        "wing_dark": (100, 70, 20),
        "wing_mid": (200, 160, 50),
        "wing_light": (255, 220, 100),
        "wing_glow": (255, 245, 180),

        # Shadow purple accents
        "shadow_purple": (40, 20, 60),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_aurelyssa._clamp(color)
        if _NS_aurelyssa.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_aurelyssa._clamp(color)
        if _NS_aurelyssa.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_aurelyssa._clamp(color), points)

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
    def draw_aurelyssa(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_aurelyssa._detect_moving(boss)
        _NS_aurelyssa._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_aly_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_aurelyssa._draw_golden_aura(surface, x, y, pulse)
        _NS_aurelyssa._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "w":
            _NS_aurelyssa._draw_lightning_sweep_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurelyssa._draw_golden_wings_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelyssa._draw_phantom_assault_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (always floating).
        if attacking:
            _NS_aurelyssa._draw_aur_attack(surface, boss, x, y)
        elif active_skill == "q":
            _NS_aurelyssa._draw_aur_whirlwind(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelyssa._draw_aur_phantom(surface, boss, x, y, skill_timer, pulse)
        elif moving:
            _NS_aurelyssa._draw_aur_float(surface, boss, x, y)
        else:
            _NS_aurelyssa._draw_aur_idle(surface, boss, x, y)

        # E - Wing shield around body.
        if active_skill == "e":
            _NS_aurelyssa._draw_golden_wings_shield(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_aurelyssa._draw_whirlwind_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_aurelyssa._draw_lightning_sweep_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelyssa._draw_phantom_assault_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aly_previous_timer", 0))
        active = bool(getattr(boss, "_aly_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aly_attack_active = True
            boss._aly_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._aly_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._aly_attack_frame = int(getattr(boss, "_aly_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._aly_attack_active = False
            boss._aly_attack_frame = 0
            active = False

        boss._aly_previous_timer = timer
        boss._aly_attack_progress = (
            min(1.0, getattr(boss, "_aly_attack_frame", 0) / max(1, cooldown - 1))
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
    def _draw_aur_idle(surface, boss, x, y):
        # Floating bob (higher, slower).
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_aurelyssa._draw_shadow(surface, x, y + 50)
        _NS_aurelyssa._draw_butterfly_trail(surface, x, y + 20, boss.pulse)
        _NS_aurelyssa._draw_aur_body(surface, x, y + bob - 6,
                                     boss.direction, boss.pulse, "idle")

    def _draw_aur_float(surface, boss, x, y):
        phase = boss.pulse * 1.4
        bob = int(math.sin(phase * 1.0) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_aurelyssa._draw_shadow(surface, x + sway, y + 50)
        _NS_aurelyssa._draw_butterfly_trail(surface, x + sway, y + 20, phase,
                                            trail=True, facing=boss.direction)
        _NS_aurelyssa._draw_aur_body(surface, x + sway, y + bob - 8,
                                     boss.direction, phase, "float")

    def _draw_aur_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_aly_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_aly_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Sword swing animation:
        # 0.0-0.35: wind up (blade back, body slight back)
        # 0.35-0.6: swing forward (fast)
        # 0.6-1.0: recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * facing
            bob = -2 + int(math.sin(boss.pulse * 0.6) * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 12)) * facing
            bob = int(math.sin(boss.pulse * 0.6) * 3) - 3
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * facing
            bob = int(-3 + t * 3) + int(math.sin(boss.pulse * 0.6) * 2)

        _NS_aurelyssa._draw_shadow(surface, x + lunge, y + 50)
        _NS_aurelyssa._draw_butterfly_trail(surface, x + lunge, y + 20,
                                            boss.pulse, intense=True)
        _NS_aurelyssa._draw_aur_body(surface, x + lunge, y + bob - 6,
                                     facing, boss.pulse, "attack", progress)
        # Sword trail slash arc.
        _NS_aurelyssa._draw_sword_slash(surface, boss, x + lunge, y + bob - 6, progress)

    def _draw_aur_whirlwind(surface, boss, x, y, timer, phase):
        # Body rotates fast during whirlwind Q.
        spin_phase = phase * 6
        bob = int(math.sin(phase * 0.8) * 3) - 6
        _NS_aurelyssa._draw_shadow(surface, x, y + 50)
        _NS_aurelyssa._draw_butterfly_trail(surface, x, y + 20, phase, intense=True)
        # Simplified spinning body.
        _NS_aurelyssa._draw_aur_body(surface, x, y + bob,
                                     boss.direction, spin_phase, "whirlwind")

    def _draw_aur_phantom(surface, boss, x, y, timer, phase):
        # Phantom form - translucent + shifted.
        bob = int(math.sin(phase * 1.2) * 4) - 8
        _NS_aurelyssa._draw_shadow(surface, x, y + 50)
        _NS_aurelyssa._draw_butterfly_trail(surface, x, y + 20, phase, intense=True)
        _NS_aurelyssa._draw_aur_body(surface, x, y + bob,
                                     boss.direction, phase, "phantom")

    # ============================================================
    # BODY (Humanoid sword dancer)
    # ============================================================
    def _draw_aur_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw floating sword dancer body."""

        # For whirlwind, draw motion blur / afterimages first.
        if action == "whirlwind":
            for i in range(4):
                blur_alpha = 60 + i * 30
                blur_x = cx + int(math.cos(phase + i * math.pi / 2) * 8)
                _NS_aurelyssa._draw_body_silhouette(surface, blur_x, cy, facing,
                                                    phase, blur_alpha)

        # Phantom afterimages.
        if action == "phantom":
            for i in range(3):
                blur_alpha = 80 + i * 40
                blur_x = cx - facing * (12 + i * 8)
                _NS_aurelyssa._draw_body_silhouette(surface, blur_x, cy, facing,
                                                    phase, blur_alpha)

        # Cape/cloth behind (drawn first).
        _NS_aurelyssa._draw_cape(surface, cx, cy, facing, phase, action)

        # Legs (floating, slightly tucked).
        _NS_aurelyssa._draw_legs(surface, cx, cy, facing, phase, action)

        # Torso.
        _NS_aurelyssa._draw_torso(surface, cx, cy, facing, phase, action)

        # Off-hand arm (back).
        _NS_aurelyssa._draw_arm_back(surface, cx, cy, facing, phase, action,
                                     attack_progress)

        # Head + hair.
        _NS_aurelyssa._draw_head(surface, cx, cy - 18, facing, phase, action)

        # Sword arm (front) + blade.
        _NS_aurelyssa._draw_arm_front_with_sword(surface, cx, cy, facing, phase,
                                                 action, attack_progress)

    def _draw_body_silhouette(surface, cx, cy, facing, phase, alpha_val):
        """Simplified translucent body for motion blur."""
        surf = pygame.Surface((60, 80), pygame.SRCALPHA)
        # Torso
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_light"], alpha_val),
                            (22, 30, 16, 22))
        # Head
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha_val),
                            (24, 12, 12, 14))
        # Legs
        pygame.draw.rect(surf, (*_NS_aurelyssa.PALETTE["gold_light"], alpha_val),
                         (24, 50, 4, 14))
        pygame.draw.rect(surf, (*_NS_aurelyssa.PALETTE["gold_light"], alpha_val),
                         (32, 50, 4, 14))
        surface.blit(surf, (cx - 30, cy - 20))

    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Cape flowing behind."""
        wave = math.sin(phase * 1.2) * 3

        cape_points = [
            (cx - facing * 6, cy - 12),
            (cx - facing * 10, cy - 8),
            (cx - facing * 14 - int(wave), cy - 2),
            (cx - facing * 16 - int(wave * 1.5), cy + 6),
            (cx - facing * 14 - int(wave), cy + 14),
            (cx - facing * 10, cy + 12),
            (cx - facing * 5, cy + 8),
            (cx - facing * 2, cy - 4),
        ]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in cape_points])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["cloth_dark"], cape_points)

        inner_pts = [
            (cx - facing * 6, cy - 10),
            (cx - facing * 10, cy - 4),
            (cx - facing * 12 - int(wave), cy + 4),
            (cx - facing * 10 - int(wave), cy + 10),
            (cx - facing * 6, cy + 8),
            (cx - facing * 3, cy - 2),
        ]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["cloth_mid"], inner_pts)

        # Gold trim on edge.
        for i in range(len(cape_points) - 1):
            pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                             cape_points[i], cape_points[i + 1], 1)

        # Gold sparkles on cape.
        for i in range(3):
            sx = cx - facing * (8 + i * 3) - int(wave * 0.5)
            sy = cy + int(math.sin(phase + i) * 4)
            pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_hot"], (sx, sy, 1, 1))

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Floating legs, slightly tucked."""
        # Legs drift downward with floating motion.
        leg_sway = math.sin(phase * 1.0) * 1

        # Back leg (further)
        back_leg_x = cx - facing * 2
        back_leg_y = cy + 14
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (back_leg_x + 1, cy + 5), (back_leg_x + 1 + int(leg_sway), back_leg_y + 6), 4)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_darkest"],
                         (back_leg_x, cy + 5), (back_leg_x + int(leg_sway), back_leg_y + 5), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_dark"],
                         (back_leg_x, cy + 5), (back_leg_x + int(leg_sway), back_leg_y + 5), 2)

        # Boot back
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["armor_darkest"],
                         (back_leg_x - 2 + int(leg_sway), back_leg_y + 3, 6, 3))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (back_leg_x - 2 + int(leg_sway), back_leg_y + 3, 6, 1))

        # Front leg
        front_leg_x = cx + facing * 3
        front_leg_y = cy + 14
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (front_leg_x + 1, cy + 5),
                         (front_leg_x + 1 - int(leg_sway), front_leg_y + 6), 4)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_dark"],
                         (front_leg_x, cy + 5),
                         (front_leg_x - int(leg_sway), front_leg_y + 5), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_mid"],
                         (front_leg_x, cy + 5),
                         (front_leg_x - int(leg_sway), front_leg_y + 5), 2)

        # Boot front
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["armor_dark"],
                         (front_leg_x - 2 - int(leg_sway), front_leg_y + 3, 6, 3))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_mid"],
                         (front_leg_x - 2 - int(leg_sway), front_leg_y + 3, 6, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Armored torso with gold trim."""
        breath = math.sin(phase * 0.5) * 1

        # Main torso shape.
        torso_points = [
            (cx - 8, cy - 8),
            (cx - 9, cy - 3),
            (cx - 8, cy + 5),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 8, cy + 5),
            (cx + 9, cy - 3),
            (cx + 8, cy - 8),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_points])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["armor_darkest"], torso_points)

        # Chest plate main.
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["armor_dark"], [
            (cx - 7, cy - 8),
            (cx - 8, cy - 3),
            (cx - 6, cy + 5),
            (cx + 6, cy + 5),
            (cx + 8, cy - 3),
            (cx + 7, cy - 8),
            (cx + 3, cy - 9),
            (cx - 3, cy - 9),
        ])

        # Highlight (upper).
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["armor_mid"], [
            (cx - 5, cy - 7),
            (cx - 6, cy - 3),
            (cx - 4, cy + 2),
            (cx + 4, cy + 2),
            (cx + 6, cy - 3),
            (cx + 5, cy - 7),
            (cx + 2, cy - 8),
            (cx - 2, cy - 8),
        ])

        # Shine
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["armor_light"],
                         (cx - 3, cy - 6, 2, 3))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["armor_shine"],
                         (cx - 3, cy - 6, 1, 1))

        # Gold trim (V-shape on chest).
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (cx - 6, cy - 4), (cx, cy + 4), 2)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (cx + 6, cy - 4), (cx, cy + 4), 2)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_light"],
                         (cx - 6, cy - 4), (cx, cy + 4), 1)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_light"],
                         (cx + 6, cy - 4), (cx, cy + 4), 1)

        # Central gem.
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (cx - 1, cy, 3, 3))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_hot"],
                         (cx, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_shine"],
                         (cx, cy, 1, 1))

        # Belt (bottom).
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["cloth_dark"],
                         (cx - 8, cy + 5, 16, 3))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (cx - 8, cy + 5, 16, 1))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_mid"],
                         (cx - 1, cy + 6, 2, 2))

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with blonde hair ponytail."""
        # Hair ponytail behind (drawn first).
        _NS_aurelyssa._draw_hair_back(surface, cx, cy, facing, phase)

        # Face shape.
        face_points = [
            (cx - 5, cy - 3),
            (cx - 6, cy + 1),
            (cx - 4, cy + 5),
            (cx, cy + 7),
            (cx + 4, cy + 5),
            (cx + 6, cy + 1),
            (cx + 5, cy - 3),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in face_points])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["skin_dark"], face_points)

        # Face mid tone.
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["skin_mid"], [
            (cx - 4, cy - 2),
            (cx - 5, cy + 1),
            (cx - 3, cy + 4),
            (cx, cy + 5),
            (cx + 3, cy + 4),
            (cx + 5, cy + 1),
            (cx + 4, cy - 2),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])

        # Cheek highlight.
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["skin_light"], [
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 3, cy + 2),
            (cx, cy + 4),
            (cx - 3, cy + 2),
        ])

        # Hair front (bangs).
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["hair_darkest"], [
            (cx - 6, cy - 6),
            (cx - 5, cy - 3),
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 5, cy - 3),
            (cx + 6, cy - 6),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["hair_dark"], [
            (cx - 5, cy - 6),
            (cx - 4, cy - 3),
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 4, cy - 3),
            (cx + 5, cy - 6),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["hair_mid"], [
            (cx - 4, cy - 6),
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 4, cy - 6),
            (cx + 2, cy - 7),
            (cx - 2, cy - 7),
        ])
        # Hair highlight.
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["hair_light"],
                         (cx - 2, cy - 6, 4, 1))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["hair_shine"],
                         (cx - 1, cy - 6, 1, 1))

        # Eyes (both, golden glow).
        # Back eye
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["eye_socket"],
                         (cx - 3, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["eye_mid"],
                         (cx - 3, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["eye_glow"],
                         (cx - 3, cy - 1, 1, 1))

        # Front eye (bigger, brighter for animation).
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["eye_socket"],
                         (cx + 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["eye_light"],
                         (cx + 1, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["eye_glow"],
                         (cx + 2, cy - 1, 1, 1))

        # Eye glow.
        pulse = math.sin(phase * 2) * 0.4 + 0.6
        for r in range(4, 0, -1):
            alpha = _NS_aurelyssa._alpha(50 * (4 - r) / 4 * pulse)
            _NS_aurelyssa._aacircle(surface, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                    (cx + 2, cy), r)

        # Mouth
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (cx - 1, cy + 3, 2, 1))

    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Ponytail flowing back."""
        wave = math.sin(phase * 1.3) * 3

        ponytail = [
            (cx - facing * 2, cy - 8),
            (cx - facing * 6, cy - 6),
            (cx - facing * 10 - int(wave), cy - 2),
            (cx - facing * 12 - int(wave * 1.2), cy + 3),
            (cx - facing * 11 - int(wave), cy + 8),
            (cx - facing * 7, cy + 6),
            (cx - facing * 4, cy - 2),
        ]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in ponytail])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["hair_darkest"], ponytail)
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["hair_dark"], [
            (cx - facing * 2, cy - 7),
            (cx - facing * 5, cy - 5),
            (cx - facing * 9 - int(wave), cy - 1),
            (cx - facing * 10 - int(wave), cy + 4),
            (cx - facing * 8, cy + 5),
            (cx - facing * 5, cy - 1),
        ])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["hair_mid"], [
            (cx - facing * 3, cy - 5),
            (cx - facing * 6, cy - 3),
            (cx - facing * 8 - int(wave), cy + 1),
            (cx - facing * 7, cy + 3),
            (cx - facing * 5, cy),
        ])
        # Hair highlight strand.
        for i in range(3):
            hx = cx - facing * (4 + i * 3)
            hy = cy - 4 + i * 3 - int(wave * 0.3)
            pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["hair_light"], (hx, hy, 1, 1))

        # Ribbon tie.
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (cx - facing * 3, cy - 7, 3, 2))
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_hot"],
                         (cx - facing * 2, cy - 7, 1, 1))

    def _draw_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (usually holds secondary or is behind)."""
        # Simple back arm.
        shoulder_x = cx - facing * 5
        shoulder_y = cy - 6
        elbow_x = cx - facing * 8
        elbow_y = cy - 1
        hand_x = cx - facing * 6
        hand_y = cy + 4

        if action == "whirlwind":
            # Both arms extended for whirlwind.
            angle = phase * 0.5
            elbow_x = cx + int(math.cos(angle + math.pi) * 10)
            elbow_y = cy - 3 + int(math.sin(angle + math.pi) * 4)
            hand_x = cx + int(math.cos(angle + math.pi) * 14)
            hand_y = cy + int(math.sin(angle + math.pi) * 6)

        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 4)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)

        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["skin_mid"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)

        # If whirlwind, draw second sword in back hand.
        if action == "whirlwind":
            _NS_aurelyssa._draw_sword_short(surface, hand_x, hand_y,
                                            math.atan2(hand_y - elbow_y, hand_x - elbow_x),
                                            facing)

    def _draw_arm_front_with_sword(surface, cx, cy, facing, phase, action,
                                    attack_progress):
        """Front arm holding main sword."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 6

        # Determine sword pose from action.
        if action == "attack":
            # Slash animation.
            if attack_progress < 0.35:
                # Wind up (blade back and up).
                t = attack_progress / 0.35
                blade_angle = math.pi * 1.3 + t * 0.3  # pointing up-back
                arm_ext = 10
            elif attack_progress < 0.6:
                # Swing forward fast.
                t = (attack_progress - 0.35) / 0.25
                blade_angle = math.pi * 1.6 - t * math.pi * 1.4  # arc forward-down
                arm_ext = 14 + int(t * 4)
            else:
                # Recovery.
                t = (attack_progress - 0.6) / 0.4
                blade_angle = 0.2 + t * 0.3
                arm_ext = 16 - int(t * 4)
        elif action == "whirlwind":
            blade_angle = phase * 0.5
            arm_ext = 14
        elif action == "phantom":
            # Blade pointing forward (thrust).
            blade_angle = 0
            arm_ext = 16
        else:
            # Idle/float - blade held to side.
            idle_sway = math.sin(phase * 0.6) * 0.05
            blade_angle = 0.3 + idle_sway
            arm_ext = 12

        # Elbow position.
        elbow_x = shoulder_x + int(math.cos(blade_angle * 0.5) * 6) * facing
        elbow_y = shoulder_y + int(math.sin(blade_angle * 0.5) * 6)

        # Hand position.
        hand_x = shoulder_x + int(math.cos(blade_angle) * arm_ext) * facing
        hand_y = shoulder_y + int(math.sin(blade_angle) * arm_ext)

        # Draw arm.
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 4)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_mid"],
                         (shoulder_x, shoulder_y - 1),
                         (elbow_x, elbow_y - 1), 1)

        # Gold shoulder pauldron.
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                                (shoulder_x, shoulder_y), 3)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_mid"],
                                (shoulder_x, shoulder_y), 2)
        pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_hot"],
                         (shoulder_x, shoulder_y - 1, 1, 1))

        # Forearm
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["armor_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["skin_mid"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)

        # Draw the sword.
        _NS_aurelyssa._draw_sword_long(surface, hand_x, hand_y, blade_angle, facing,
                                        action == "phantom")

    def _draw_sword_long(surface, hand_x, hand_y, angle, facing, phantom=False):
        """Long golden sword with glow."""
        blade_len = 26
        guard_len = 6
        pommel_len = 4

        # Blade tip
        tip_x = hand_x + int(math.cos(angle) * blade_len) * facing
        tip_y = hand_y + int(math.sin(angle) * blade_len)

        # Blade base (at guard).
        base_x = hand_x + int(math.cos(angle) * 2) * facing
        base_y = hand_y + int(math.sin(angle) * 2)

        # Perpendicular direction.
        perp = angle + math.pi / 2

        # Blade width points.
        edge1_base = (base_x + int(math.cos(perp) * 2),
                      base_y + int(math.sin(perp) * 2))
        edge2_base = (base_x - int(math.cos(perp) * 2),
                      base_y - int(math.sin(perp) * 2))

        # Blade midpoint (widest).
        mid_x = hand_x + int(math.cos(angle) * (blade_len // 2)) * facing
        mid_y = hand_y + int(math.sin(angle) * (blade_len // 2))
        edge1_mid = (mid_x + int(math.cos(perp) * 3),
                     mid_y + int(math.sin(perp) * 3))
        edge2_mid = (mid_x - int(math.cos(perp) * 3),
                     mid_y - int(math.sin(perp) * 3))

        alpha_mult = 0.6 if phantom else 1.0

        # Shadow behind.
        shadow_poly = [
            (edge1_base[0] + 1, edge1_base[1] + 1),
            (edge1_mid[0] + 1, edge1_mid[1] + 1),
            (tip_x + 1, tip_y + 1),
            (edge2_mid[0] + 1, edge2_mid[1] + 1),
            (edge2_base[0] + 1, edge2_base[1] + 1),
        ]
        if phantom:
            temp_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
            offset = (hand_x - 100, hand_y - 100)
            local_pts = [(p[0] - offset[0], p[1] - offset[1]) for p in shadow_poly]
            _NS_aurelyssa._poly(temp_surf, (*_NS_aurelyssa.PALETTE["shadow_deep"], 150),
                                local_pts)
            surface.blit(temp_surf, offset)
        else:
            _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["shadow_deep"], shadow_poly)

        # Blade main.
        blade_poly = [edge1_base, edge1_mid, (tip_x, tip_y), edge2_mid, edge2_base]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["blade_darkest"], blade_poly)
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["blade_dark"], blade_poly)

        # Inner shine.
        inner_poly = [
            (int((edge1_base[0] + edge2_base[0]) / 2 + (edge1_base[0] - edge2_base[0]) * 0.2),
             int((edge1_base[1] + edge2_base[1]) / 2 + (edge1_base[1] - edge2_base[1]) * 0.2)),
            (int((edge1_mid[0] + edge2_mid[0]) / 2 + (edge1_mid[0] - edge2_mid[0]) * 0.15),
             int((edge1_mid[1] + edge2_mid[1]) / 2 + (edge1_mid[1] - edge2_mid[1]) * 0.15)),
            (tip_x, tip_y),
            (int((edge1_mid[0] + edge2_mid[0]) / 2 - (edge1_mid[0] - edge2_mid[0]) * 0.15),
             int((edge1_mid[1] + edge2_mid[1]) / 2 - (edge1_mid[1] - edge2_mid[1]) * 0.15)),
            (int((edge1_base[0] + edge2_base[0]) / 2 - (edge1_base[0] - edge2_base[0]) * 0.2),
             int((edge1_base[1] + edge2_base[1]) / 2 - (edge1_base[1] - edge2_base[1]) * 0.2)),
        ]
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["blade_mid"], inner_poly)

        # Central line shine.
        center_base = (int((edge1_base[0] + edge2_base[0]) / 2),
                       int((edge1_base[1] + edge2_base[1]) / 2))
        center_mid = (int((edge1_mid[0] + edge2_mid[0]) / 2),
                      int((edge1_mid[1] + edge2_mid[1]) / 2))
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["blade_light"],
                         center_base, (tip_x, tip_y), 1)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["blade_shine"],
                                (tip_x, tip_y), 1)

        # Glow around blade.
        for r in range(6, 1, -1):
            alpha = _NS_aurelyssa._alpha(60 * (6 - r) / 6 * alpha_mult)
            _NS_aurelyssa._aacircle(surface, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                    (tip_x, tip_y), r)
            _NS_aurelyssa._aacircle(surface, (*_NS_aurelyssa.PALETTE["gold_light"], alpha // 2),
                                    (mid_x, mid_y), r)

        # Guard (perpendicular to blade at hand).
        guard1 = (hand_x + int(math.cos(perp) * guard_len),
                  hand_y + int(math.sin(perp) * guard_len))
        guard2 = (hand_x - int(math.cos(perp) * guard_len),
                  hand_y - int(math.sin(perp) * guard_len))
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["shadow_deep"],
                         (guard1[0] + 1, guard1[1] + 1),
                         (guard2[0] + 1, guard2[1] + 1), 4)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         guard1, guard2, 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_mid"],
                         guard1, guard2, 2)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_light"],
                         guard1, guard2, 1)

        # Guard end orbs.
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_dark"], guard1, 2)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_hot"], guard1, 1)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_dark"], guard2, 2)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_hot"], guard2, 1)

        # Pommel (opposite direction of blade).
        pommel_x = hand_x - int(math.cos(angle) * pommel_len) * facing
        pommel_y = hand_y - int(math.sin(angle) * pommel_len)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                         (hand_x, hand_y), (pommel_x, pommel_y), 3)
        pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_mid"],
                         (hand_x, hand_y), (pommel_x, pommel_y), 2)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_dark"],
                                (pommel_x, pommel_y), 2)
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_hot"],
                                (pommel_x, pommel_y), 1)

    def _draw_sword_short(surface, hand_x, hand_y, angle, facing):
        """Shorter sword for off-hand."""
        blade_len = 18
        tip_x = hand_x + int(math.cos(angle) * blade_len)
        tip_y = hand_y + int(math.sin(angle) * blade_len)
        perp = angle + math.pi / 2

        base_x = hand_x + int(math.cos(angle) * 2)
        base_y = hand_y + int(math.sin(angle) * 2)

        edge1 = (base_x + int(math.cos(perp) * 2),
                 base_y + int(math.sin(perp) * 2))
        edge2 = (base_x - int(math.cos(perp) * 2),
                 base_y - int(math.sin(perp) * 2))

        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["shadow_deep"], [
            (edge1[0] + 1, edge1[1] + 1),
            (tip_x + 1, tip_y + 1),
            (edge2[0] + 1, edge2[1] + 1),
        ])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["blade_dark"],
                            [edge1, (tip_x, tip_y), edge2])
        _NS_aurelyssa._poly(surface, _NS_aurelyssa.PALETTE["blade_mid"], [
            (int((edge1[0] + base_x) / 2), int((edge1[1] + base_y) / 2)),
            (tip_x, tip_y),
            (int((edge2[0] + base_x) / 2), int((edge2[1] + base_y) / 2)),
        ])
        _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["blade_shine"],
                                (tip_x, tip_y), 1)

        # Small glow.
        for r in range(4, 0, -1):
            alpha = _NS_aurelyssa._alpha(50 * (4 - r) / 4)
            _NS_aurelyssa._aacircle(surface, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                    (tip_x, tip_y), r)

    def _draw_sword_slash(surface, boss, cx, cy, progress):
        """Slash arc trail during attack."""
        if progress < 0.35 or progress > 0.85:
            return

        facing = boss.direction
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 6

        # Arc center at shoulder.
        # Start angle → end angle (arc from up-back to down-front).
        if progress < 0.6:
            t = (progress - 0.35) / 0.25
        else:
            t = 1.0 - (progress - 0.6) / 0.25 * 0.3

        # Number of arc points to draw the trail.
        arc_start = math.pi * 1.6
        arc_end = math.pi * 0.2
        current_angle = arc_start + (arc_end - arc_start) * t

        # Draw trail as multiple arc points fading.
        for i in range(12):
            trail_t = t - i * 0.05
            if trail_t < 0 or trail_t > 1:
                continue
            angle = arc_start + (arc_end - arc_start) * trail_t
            radius = 22
            arc_x = shoulder_x + int(math.cos(angle) * radius) * facing
            arc_y = shoulder_y + int(math.sin(angle) * radius)

            alpha = _NS_aurelyssa._alpha(200 * (1 - i / 12))
            size = max(1, 6 - i // 2)

            for r in range(size, 0, -1):
                inner_alpha = _NS_aurelyssa._alpha(alpha * (size - r + 1) / size)
                _NS_aurelyssa._aacircle(surface,
                                        (*_NS_aurelyssa.PALETTE["gold_hot"], inner_alpha),
                                        (arc_x, arc_y), r)

            # Bright core.
            pygame.draw.rect(surface, (*_NS_aurelyssa.PALETTE["gold_shine"], alpha),
                             (arc_x, arc_y, 1, 1))
            pygame.draw.rect(surface, (*_NS_aurelyssa.PALETTE["white"], alpha // 2),
                             (arc_x, arc_y, 1, 1))

    # ============================================================
    # BUTTERFLY TRAIL & AURA
    # ============================================================
    def _draw_butterfly_trail(surface, cx, cy, phase, trail=False, facing=1,
                               intense=False):
        """Golden butterflies floating around."""
        strength = 1.5 if intense else 1.0
        num_bf = 5 if not trail else 8

        for i in range(num_bf):
            angle = phase * 0.5 + i * math.pi * 2 / num_bf
            offset_dist = 20 + int(math.sin(phase + i) * 8)
            bf_x = cx + int(math.cos(angle) * offset_dist)
            bf_y = cy + int(math.sin(angle) * offset_dist * 0.4) - 10

            # Wing flap.
            flap = math.sin(phase * 4 + i) * 0.5 + 0.5

            _NS_aurelyssa._draw_small_butterfly(surface, bf_x, bf_y, flap, strength)

        # Ambient gold particles.
        for i in range(12):
            t = (phase * 0.3 + i * 0.08) % 1.0
            px = cx + int(math.cos(phase + i) * (10 + t * 20))
            py = cy - int(t * 30) + int(math.sin(phase * 2 + i) * 3)
            alpha = _NS_aurelyssa._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                 (px, py, 1, 1))
                if t < 0.5:
                    pygame.draw.rect(surface, (*_NS_aurelyssa.PALETTE["gold_shine"], alpha),
                                     (px, py, 1, 1))

        # Trailing sparkles behind if moving.
        if trail:
            for i in range(5):
                sx = cx - facing * (i + 1) * 8
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = _NS_aurelyssa._alpha(180 - i * 30)
                if alpha > 0:
                    _NS_aurelyssa._aacircle(surface,
                                            (*_NS_aurelyssa.PALETTE["gold_light"], alpha),
                                            (sx, sy), max(1, 3 - i // 2))
                    pygame.draw.rect(surface, (*_NS_aurelyssa.PALETTE["gold_shine"], alpha),
                                     (sx, sy, 1, 1))

    def _draw_small_butterfly(surface, cx, cy, flap, strength=1.0):
        """Small butterfly with flapping wings."""
        wing_w = int(3 + flap * 2)
        wing_h = int(2 + flap * 2)

        alpha_val = _NS_aurelyssa._alpha(220 * strength)

        surf = pygame.Surface((16, 12), pygame.SRCALPHA)
        # Upper wings.
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_dark"], alpha_val),
                            (8 - wing_w, 4 - wing_h, wing_w, wing_h + 2))
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_dark"], alpha_val),
                            (8, 4 - wing_h, wing_w, wing_h + 2))
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_mid"], alpha_val),
                            (8 - wing_w + 1, 4 - wing_h + 1,
                             max(1, wing_w - 1), max(1, wing_h)))
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_mid"], alpha_val),
                            (8, 4 - wing_h + 1,
                             max(1, wing_w - 1), max(1, wing_h)))
        pygame.draw.rect(surf, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha_val),
                         (8 - wing_w + 1, 4 - wing_h + 1, 1, 1))
        pygame.draw.rect(surf, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha_val),
                         (8 + wing_w - 1, 4 - wing_h + 1, 1, 1))

        # Lower wings (smaller).
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_dark"], alpha_val),
                            (8 - wing_w + 1, 5, wing_w, wing_h + 1))
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_dark"], alpha_val),
                            (8, 5, wing_w, wing_h + 1))
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_light"], alpha_val),
                            (8 - wing_w + 1, 6, max(1, wing_w - 1), max(1, wing_h - 1)))
        pygame.draw.ellipse(surf, (*_NS_aurelyssa.PALETTE["gold_light"], alpha_val),
                            (8, 6, max(1, wing_w - 1), max(1, wing_h - 1)))

        # Body.
        pygame.draw.line(surf, (*_NS_aurelyssa.PALETTE["gold_darkest"], alpha_val),
                         (8, 3), (8, 7), 1)
        pygame.draw.rect(surf, (*_NS_aurelyssa.PALETTE["gold_shine"], alpha_val),
                         (8, 5, 1, 1))

        surface.blit(surf, (cx - 8, cy - 6))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 24), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 14)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (5 - radius, 12 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 3, 8, 150), (5, 6, 100, 12))
        pygame.draw.ellipse(shadow, (60, 40, 15, 100), (12, 8, 86, 8))
        surface.blit(shadow, (x - 55, y - 12))

    def _draw_golden_aura(surface, x, y, phase):
        """Golden aura around body."""
        pulse = math.sin(phase * 0.6) * 0.3 + 0.7

        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(75, 5, -5):
            alpha = _NS_aurelyssa._alpha((75 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_aurelyssa._aacircle(aura,
                                        (*_NS_aurelyssa.PALETTE["gold_dark"], alpha),
                                        (90, 80), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_aurelyssa._alpha((45 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_aurelyssa._aacircle(aura,
                                        (*_NS_aurelyssa.PALETTE["gold_mid"], alpha),
                                        (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))

        # Floating gold sparks.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_shine"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Golden ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 50), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_aurelyssa.PALETTE["gold_dark"], 200),
                            (5, 16, 140, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_aurelyssa.PALETTE["gold_darkest"], 220),
                            (14, 18, 122, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_aurelyssa.PALETTE["gold_mid"], 230),
                            (25, 20, 100, 16), 1)

        # Runes.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 40)
            y1 = 28 + int(math.sin(angle) * 6)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 28 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_aurelyssa.PALETTE["gold_hot"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_aurelyssa.PALETTE["gold_shine"],
                                       _NS_aurelyssa._alpha(150 * pulse)),
                                (15, 10, 120, 36), 1)
        surface.blit(ring, (x - 75, y - 25))

    # ============================================================
    # SKILL Q - WHIRLWIND (spinning blades AoE)
    # ============================================================
    def _draw_whirlwind_foreground(surface, boss, x, y, timer, phase):
        """Spinning gold blade arcs around body."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multi-layer whirlwind arcs.
        for layer in range(4):
            layer_offset = layer * math.pi / 4
            spin_speed = 8
            spin_angle = phase * spin_speed + layer_offset

            # Arc points.
            radius = 32 + layer * 4 + int(math.sin(phase * 2) * 2)

            # Draw arc trails (multiple points forming arc).
            num_points = 20
            arc_span = math.pi * 1.5  # arc length

            for i in range(num_points):
                t = i / num_points
                angle = spin_angle + t * arc_span
                px = x + int(math.cos(angle) * radius)
                py = y - 5 + int(math.sin(angle) * radius * 0.5)

                alpha = _NS_aurelyssa._alpha(220 * (1 - t) * (1 - progress * 0.3))
                size = max(1, 4 - i // 5)

                for r in range(size, 0, -1):
                    inner_alpha = _NS_aurelyssa._alpha(alpha * (size - r + 1) / size)
                    _NS_aurelyssa._aacircle(surface,
                                            (*_NS_aurelyssa.PALETTE["gold_hot"], inner_alpha),
                                            (px, py), r)
                pygame.draw.rect(surface,
                                 (*_NS_aurelyssa.PALETTE["gold_shine"], alpha),
                                 (px, py, 1, 1))

        # Outer damage ring pulse.
        pulse_r = 40 + int(math.sin(phase * 3) * 5)
        for r_thick in [3, 2, 1]:
            alpha = _NS_aurelyssa._alpha(150)
            _NS_aurelyssa._aacircle(surface,
                                    (*_NS_aurelyssa.PALETTE["gold_light"], alpha),
                                    (x, y - 5), pulse_r + r_thick, 1)

        # Sparks flying outward.
        for i in range(15):
            spark_angle = phase * 2 + i * math.pi / 7
            spark_dist = 35 + int((phase * 3 + i * 4) % 15)
            sx = x + int(math.cos(spark_angle) * spark_dist)
            sy = y - 5 + int(math.sin(spark_angle) * spark_dist * 0.5)
            pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["gold_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["white"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL W - LIGHTNING SWEEP (line dash strike)
    # ============================================================
    def _draw_lightning_sweep_ground(surface, boss, x, y, timer, phase):
        """Warning line on ground for sweep direction."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_aurelyssa._target_position(boss, x, y)

        if progress < 0.5:
            # Warning line drawn on ground.
            t = progress / 0.5
            end_x = int(x + (tx - x) * t)
            end_y = y + 40
            alpha = _NS_aurelyssa._alpha(200 * t)
            pygame.draw.line(surface, (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                             (x, y + 40), (end_x, end_y), 3)
            pygame.draw.line(surface, (*_NS_aurelyssa.PALETTE["gold_shine"], alpha),
                             (x, y + 40), (end_x, end_y), 1)

    def _draw_lightning_sweep_foreground(surface, boss, x, y, timer, phase):
        """Lightning slash sweep from boss to target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_aurelyssa._target_position(boss, x, y)

        if progress < 0.4:
            # Charge up.
            t = progress / 0.4
            charge_r = int(4 + t * 8)
            charge_x = x + facing * 16
            charge_y = y - 5
            for r in range(charge_r + 3, 0, -1):
                alpha = _NS_aurelyssa._alpha(200 * (charge_r + 3 - r) / (charge_r + 3))
                _NS_aurelyssa._aacircle(surface,
                                        (*_NS_aurelyssa.PALETTE["gold_dark"], alpha),
                                        (charge_x, charge_y), r)
            _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_mid"],
                                    (charge_x, charge_y), charge_r - 2)
            _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_hot"],
                                    (charge_x, charge_y), max(1, charge_r - 4))
            _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_shine"],
                                    (charge_x, charge_y), max(1, charge_r - 6))

            # Charging lines gathering.
            for i in range(6):
                angle = phase * 3 + i * math.pi / 3
                inward_dist = int(20 * (1 - t))
                gx = charge_x + int(math.cos(angle) * inward_dist)
                gy = charge_y + int(math.sin(angle) * inward_dist)
                pygame.draw.line(surface, _NS_aurelyssa.PALETTE["gold_hot"],
                                 (charge_x, charge_y), (gx, gy), 1)
        elif progress < 0.7:
            # Sweep phase - long line slash from boss to target.
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)

            start_x = x + facing * 20
            start_y = y - 5

            # Beam extension.
            beam_end_x = int(start_x + (tx - start_x) * min(1.0, t * 2))
            beam_end_y = int(start_y + (ty - start_y) * min(1.0, t * 2))

            # Multi-layer beam.
            for width, color in [
                (8, _NS_aurelyssa.PALETTE["gold_dark"]),
                (5, _NS_aurelyssa.PALETTE["gold_mid"]),
                (3, _NS_aurelyssa.PALETTE["gold_hot"]),
                (1, _NS_aurelyssa.PALETTE["gold_shine"]),
            ]:
                alpha = _NS_aurelyssa._alpha(240 * intensity)
                pygame.draw.line(surface, (*color, alpha),
                                 (start_x, start_y), (beam_end_x, beam_end_y), width)

            # Sparkles along beam.
            for i in range(10):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                sx = int(start_x + (beam_end_x - start_x) * spark_t)
                sy = int(start_y + (beam_end_y - start_y) * spark_t)
                sy_off = int(math.sin(phase * 5 + i) * 4)
                pygame.draw.rect(surface,
                                 (*_NS_aurelyssa.PALETTE["gold_shine"],
                                  _NS_aurelyssa._alpha(240 * intensity)),
                                 (sx, sy + sy_off, 2, 2))

            # Impact at end.
            impact_r = int(8 + t * 12)
            for r in range(impact_r, 0, -1):
                alpha = _NS_aurelyssa._alpha(200 * intensity * (impact_r - r + 1) / impact_r)
                _NS_aurelyssa._aacircle(surface,
                                        (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                        (beam_end_x, beam_end_y), r)

            # Radial burst at impact.
            for i in range(8):
                angle_s = i * math.pi / 4
                bx = beam_end_x + int(math.cos(angle_s) * impact_r)
                by = beam_end_y + int(math.sin(angle_s) * impact_r)
                pygame.draw.line(surface,
                                 (*_NS_aurelyssa.PALETTE["gold_shine"],
                                  _NS_aurelyssa._alpha(220 * intensity)),
                                 (beam_end_x, beam_end_y), (bx, by), 2)
        else:
            # Fade sparkles.
            t = (progress - 0.7) / 0.3
            for i in range(10):
                sx = int(x + (tx - x) * (i / 10))
                sy = int(y - 5 + (ty - (y - 5)) * (i / 10))
                sy_off = int(math.sin(phase + i) * 3)
                alpha = _NS_aurelyssa._alpha(180 * (1 - t))
                pygame.draw.rect(surface,
                                 (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                 (sx, sy + sy_off, 1, 1))

    # ============================================================
    # SKILL E - GOLDEN WINGS (shield)
    # ============================================================
    def _draw_golden_wings_ground(surface, boss, x, y, timer, phase):
        """Golden circle on ground during shield."""
        duration = 90
        for i in range(2):
            r = int(28 + i * 6 + math.sin(phase * 2) * 2)
            alpha = _NS_aurelyssa._alpha(180 - i * 60)
            _NS_aurelyssa._aacircle(surface,
                                    (*_NS_aurelyssa.PALETTE["gold_mid"], alpha),
                                    (x, y + 42), r, 2)
            _NS_aurelyssa._aacircle(surface,
                                    (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                    (x, y + 42), r, 1)

    def _draw_golden_wings_shield(surface, boss, x, y, timer, phase):
        """Butterfly wing shield around boss."""
        duration = 90

        # Ring shield.
        breath = math.sin(phase * 2) * 3
        r = 50 + int(breath)

        shield = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        for thick, alpha_val in [(3, 100), (2, 140), (1, 200)]:
            _NS_aurelyssa._aacircle(shield,
                                    (*_NS_aurelyssa.PALETTE["gold_dark"], alpha_val),
                                    center, r, thick)
            _NS_aurelyssa._aacircle(shield,
                                    (*_NS_aurelyssa.PALETTE["gold_hot"], alpha_val),
                                    center, r - 1, 1)

        # Multiple butterflies flying around the shield.
        num_butterflies = 6
        for i in range(num_butterflies):
            angle = phase * 1.2 + i * math.pi * 2 / num_butterflies
            bx = center[0] + int(math.cos(angle) * r)
            by = center[1] + int(math.sin(angle) * r)
            flap = math.sin(phase * 5 + i) * 0.5 + 0.5
            _NS_aurelyssa._draw_small_butterfly(shield, bx, by, flap, 1.3)

        # Sparkle particles around shield.
        for i in range(20):
            angle = phase * 0.8 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * (r + 2))
            sy = center[1] + int(math.sin(angle) * (r + 2))
            pygame.draw.rect(shield, _NS_aurelyssa.PALETTE["gold_shine"],
                             (sx, sy, 2, 2))

        surface.blit(shield, (x - r - 10, y - r - 10))

    # ============================================================
    # SKILL R - PHANTOM ASSAULT (multi-strike ultimate)
    # ============================================================
    def _draw_phantom_assault_ground(surface, boss, x, y, timer, phase):
        """Ground indicator for phantom strikes."""
        tx, ty = _NS_aurelyssa._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rings at target.
        if progress > 0.1:
            for i in range(3):
                r = int(15 + i * 6 + math.sin(phase * 3 + i) * 2)
                alpha = _NS_aurelyssa._alpha(180 - i * 40)
                _NS_aurelyssa._aacircle(surface,
                                        (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                        (tx, ty), r, 2)

    def _draw_phantom_assault_foreground(surface, boss, x, y, timer, phase):
        """Multiple phantom strikes."""
        facing = boss.direction
        tx, ty = _NS_aurelyssa._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple strikes in sequence.
        num_strikes = 5
        strike_duration = 1.0 / num_strikes

        for strike_i in range(num_strikes):
            strike_start = strike_i * strike_duration
            strike_end = strike_start + strike_duration

            if progress < strike_start or progress > strike_end:
                continue

            local_t = (progress - strike_start) / strike_duration
            intensity = math.sin(local_t * math.pi)

            # Phantom silhouette dashing toward target.
            phantom_offset = math.sin(strike_i) * 20
            phantom_x = int(x + (tx - x) * local_t)
            phantom_y = int(y + (ty - y) * local_t) + int(phantom_offset)

            # Draw phantom body silhouette.
            for i in range(4):
                trail_t = local_t - i * 0.08
                if trail_t < 0:
                    continue
                trail_x = int(x + (tx - x) * trail_t)
                trail_y = int(y + (ty - y) * trail_t) + int(math.sin(strike_i + trail_t * 3) * 15)
                alpha = _NS_aurelyssa._alpha(200 * (1 - i / 4) * intensity)
                _NS_aurelyssa._draw_body_silhouette(surface, trail_x, trail_y,
                                                    facing, phase, alpha)

            # Slash beam at target on impact.
            if local_t > 0.6:
                impact_t = (local_t - 0.6) / 0.4
                impact_r = int(6 + impact_t * 15)
                impact_alpha = _NS_aurelyssa._alpha(240 * (1 - impact_t))

                # Slash lines through target.
                slash_angle = strike_i * math.pi / 3
                for beam_len in [20, 15, 10]:
                    for width, color in [
                        (4, _NS_aurelyssa.PALETTE["gold_dark"]),
                        (2, _NS_aurelyssa.PALETTE["gold_hot"]),
                        (1, _NS_aurelyssa.PALETTE["gold_shine"]),
                    ]:
                        end_x1 = tx + int(math.cos(slash_angle) * beam_len)
                        end_y1 = ty + int(math.sin(slash_angle) * beam_len)
                        end_x2 = tx - int(math.cos(slash_angle) * beam_len)
                        end_y2 = ty - int(math.sin(slash_angle) * beam_len)
                        pygame.draw.line(surface, (*color, impact_alpha),
                                         (end_x1, end_y1), (end_x2, end_y2), width)

                # Impact burst.
                for r in range(impact_r, 0, -1):
                    alpha = _NS_aurelyssa._alpha(impact_alpha * (impact_r - r + 1) / impact_r)
                    _NS_aurelyssa._aacircle(surface,
                                            (*_NS_aurelyssa.PALETTE["gold_hot"], alpha),
                                            (tx, ty), r)
                _NS_aurelyssa._aacircle(surface, _NS_aurelyssa.PALETTE["gold_shine"],
                                        (tx, ty), max(1, impact_r // 3))
                pygame.draw.rect(surface, _NS_aurelyssa.PALETTE["white"],
                                 (tx, ty, 1, 1))

                # Sparks flying.
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * impact_r * 1.5)
                    ey = ty + int(math.sin(angle_s) * impact_r * 1.5)
                    pygame.draw.rect(surface,
                                     (*_NS_aurelyssa.PALETTE["gold_hot"], impact_alpha),
                                     (ex, ey, 2, 2))


# ====================================================================
# vargrath.py
# ====================================================================

# ====================================================================
# VARGRATH - THE EMBER FIEND (Mini Boss)
# ====================================================================


class _NS_vargrath:
    """Namespace vargrath - Mini Boss Demonic Warlord."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Black armor (main plates)
        "armor_darkest": (5, 3, 5),
        "armor_dark": (25, 18, 22),
        "armor_mid": (55, 40, 45),
        "armor_light": (95, 75, 78),
        "armor_edge": (150, 125, 125),
        "armor_shine": (200, 180, 175),

        # Red skin/flesh (visible under armor)
        "flesh_darkest": (30, 5, 5),
        "flesh_dark": (75, 15, 15),
        "flesh_mid": (140, 35, 30),
        "flesh_light": (200, 70, 55),

        # Lava veins (bright orange-red glow)
        "lava_darkest": (30, 5, 0),
        "lava_dark": (110, 25, 5),
        "lava_mid": (220, 65, 15),
        "lava_light": (255, 140, 40),
        "lava_hot": (255, 200, 80),
        "lava_shine": (255, 240, 180),

        # Blade (dark metal + lava cracks)
        "blade_darkest": (10, 5, 8),
        "blade_dark": (35, 25, 30),
        "blade_mid": (70, 55, 60),
        "blade_light": (130, 110, 115),
        "blade_shine": (200, 185, 185),

        # Wing membrane (dark red-black)
        "wing_darkest": (8, 2, 5),
        "wing_dark": (35, 10, 15),
        "wing_mid": (75, 25, 30),
        "wing_light": (130, 50, 50),
        "wing_glow": (200, 90, 70),

        # Horns/bone
        "horn_dark": (25, 15, 18),
        "horn_mid": (60, 45, 45),
        "horn_light": (110, 90, 88),
        "horn_shine": (180, 160, 155),

        # Eye (menyala merah/kuning)
        "eye_socket": (5, 2, 2),
        "eye_darkest": (40, 8, 5),
        "eye_dark": (110, 25, 10),
        "eye_mid": (220, 80, 20),
        "eye_light": (255, 160, 60),
        "eye_glow": (255, 220, 140),

        # Smoke/embers
        "smoke_dark": (20, 15, 20),
        "smoke_mid": (55, 40, 45),
        "smoke_light": (110, 90, 95),

        # Abyss void (accent)
        "abyss_darkest": (10, 3, 15),
        "abyss_dark": (30, 10, 40),
        "abyss_mid": (75, 30, 90),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vargrath._clamp(color)
        if _NS_vargrath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_vargrath._clamp(color)
        if _NS_vargrath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_vargrath._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_vargrath._clamp(color), points)

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
    def draw_vargrath(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vargrath._detect_moving(boss)
        _NS_vargrath._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_var_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient.
        _NS_vargrath._draw_ember_aura(surface, x, y, pulse)
        _NS_vargrath._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground.
        if active_skill == "w":
            _NS_vargrath._draw_charge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vargrath._draw_devilstrike_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vargrath._draw_souldom_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_vargrath._draw_var_attack(surface, boss, x, y)
        elif moving:
            _NS_vargrath._draw_var_float(surface, boss, x, y)
        else:
            _NS_vargrath._draw_var_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_vargrath._draw_bloodthirst_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vargrath._draw_charge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vargrath._draw_devilstrike_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vargrath._draw_souldom_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_var_previous_timer", 0))
        active = bool(getattr(boss, "_var_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._var_attack_active = True
            boss._var_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._var_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._var_attack_frame = int(getattr(boss, "_var_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._var_attack_active = False
            boss._var_attack_frame = 0
            active = False

        boss._var_previous_timer = timer
        boss._var_attack_progress = (
            min(1.0, getattr(boss, "_var_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_var_last_x"):
            boss._var_last_x = boss.x
            boss._var_last_y = boss.y
            return False
        dx = abs(boss.x - boss._var_last_x)
        dy = abs(boss.y - boss._var_last_y)
        boss._var_last_x = boss.x
        boss._var_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_var_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_vargrath._draw_shadow(surface, x, y + 55)
        _NS_vargrath._draw_ember_mist(surface, x, y + 40, boss.pulse)
        _NS_vargrath._draw_var_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_var_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_vargrath._draw_shadow(surface, x + sway, y + 55)
        _NS_vargrath._draw_ember_mist(surface, x + sway, y + 40, phase,
                                       trail=True, facing=boss.direction)
        _NS_vargrath._draw_var_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")

    def _draw_var_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_var_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_var_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Blade swing (heavy overhead → downward slash → recovery).
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
        _NS_vargrath._draw_shadow(surface, x + lunge, y + 55)
        _NS_vargrath._draw_ember_mist(surface, x + lunge, y + 40, boss.pulse,
                                       intense=True)
        _NS_vargrath._draw_var_body(surface, x + lunge, y - lift + bob,
                                     facing, boss.pulse, "attack",
                                     progress)

    # ============================================================
    # BODY (Demon: wings, body, tail, arms, horned head)
    # ============================================================
    def _draw_var_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Demonic humanoid body."""
        # Wings behind body.
        _NS_vargrath._draw_demon_wings(surface, cx, cy - 4, facing, phase, action,
                                        attack_progress)

        # Tail curving back.
        _NS_vargrath._draw_demon_tail(surface, cx, cy + 8, facing, phase)

        # Lower body (legs/hoof-like or greaves).
        _NS_vargrath._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso.
        _NS_vargrath._draw_torso(surface, cx, cy, facing, phase)

        # Swing angle for blade.
        blade_angle = 0
        if action == "attack":
            if attack_progress < 0.35:
                # Overhead raise.
                t = attack_progress / 0.35
                blade_angle = -math.pi * 0.55 * t
            elif attack_progress < 0.6:
                # Downward slash.
                t = (attack_progress - 0.35) / 0.25
                blade_angle = -math.pi * 0.55 + math.pi * 0.95 * t
            else:
                # Return.
                t = (attack_progress - 0.6) / 0.4
                blade_angle = math.pi * 0.4 * (1 - t)

        # Back arm.
        _NS_vargrath._draw_back_arm(surface, cx, cy - 4, facing, phase, action)

        # Head with horns.
        _NS_vargrath._draw_demon_head(surface, cx + facing * 2, cy - 22,
                                       facing, phase, action, attack_progress)

        # Front arm with greatsword.
        _NS_vargrath._draw_sword_arm(surface, cx, cy - 4, facing, phase,
                                      action, blade_angle, attack_progress)

    def _draw_demon_wings(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Two large demon wings (bat/dragon-like)."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 1.0) * 4

        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing
            (1, 0.72, 0.75),  # near wing
        ]):
            base_x = cx - facing * 5
            base_y = cy - 2

            spar1_len = int(30 * size_mult)
            spar1_angle = math.pi * 0.62 * side_mult - math.radians(beat)

            spar2_len = int(34 * size_mult)
            spar2_angle = math.pi * 0.82 * side_mult - math.radians(beat * 0.8)

            spar3_len = int(26 * size_mult)
            spar3_angle = math.pi * 1.02 * side_mult - math.radians(beat * 0.5)

            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)

            membrane_points = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                (int(tip1_x * 0.55 + tip2_x * 0.45),
                 int(tip1_y * 0.55 + tip2_y * 0.45) + int(4 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.55 + tip3_x * 0.45),
                 int(tip2_y * 0.55 + tip3_y * 0.45) + int(4 * size_mult)),
                (tip3_x, tip3_y),
                (base_x - facing * 3, base_y + int(6 * size_mult)),
            ]

            wing_surf = pygame.Surface((180, 120), pygame.SRCALPHA)
            offset_x = base_x - 90
            offset_y = base_y - 60
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]

            # Layered membrane (dark red/black).
            _NS_vargrath._poly(wing_surf,
                (*_NS_vargrath.PALETTE["wing_darkest"], int(220 * alpha_mult)),
                local_points)

            # Inner darker.
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_local * 0.18),
                     int(p[1] * 0.82 + cy_local * 0.18))
                )
            _NS_vargrath._poly(wing_surf,
                (*_NS_vargrath.PALETTE["wing_dark"], int(200 * alpha_mult)),
                inner_pts)

            # Mid tone.
            inner2 = []
            for p in local_points:
                inner2.append(
                    (int(p[0] * 0.7 + cx_local * 0.3),
                     int(p[1] * 0.7 + cy_local * 0.3))
                )
            _NS_vargrath._poly(wing_surf,
                (*_NS_vargrath.PALETTE["wing_mid"], int(150 * alpha_mult)),
                inner2)

            # Wing bones (fingers) - dark.
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                pygame.draw.line(wing_surf,
                    (*_NS_vargrath.PALETTE["shadow_deep"],
                     int(240 * alpha_mult)),
                    bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                    (*_NS_vargrath.PALETTE["armor_dark"],
                     int(240 * alpha_mult)),
                    bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                    (*_NS_vargrath.PALETTE["armor_mid"],
                     int(180 * alpha_mult)),
                    bone_base, tip, 1)

                # Claw at tip (curved hook).
                _NS_vargrath._aacircle(wing_surf,
                    (*_NS_vargrath.PALETTE["horn_dark"],
                     int(240 * alpha_mult)),
                    tip, 3)
                _NS_vargrath._aacircle(wing_surf,
                    (*_NS_vargrath.PALETTE["horn_mid"],
                     int(240 * alpha_mult)),
                    tip, 2)
                pygame.draw.rect(wing_surf,
                    (*_NS_vargrath.PALETTE["horn_light"],
                     int(240 * alpha_mult)),
                    (tip[0], tip[1], 1, 1))

            # Lava glow along top edge (infernal wings).
            pygame.draw.line(wing_surf,
                (*_NS_vargrath.PALETTE["lava_dark"],
                 int(200 * alpha_mult)),
                bone_base,
                (tip1_x - offset_x, tip1_y - offset_y), 2)
            pygame.draw.line(wing_surf,
                (*_NS_vargrath.PALETTE["lava_mid"],
                 int(220 * alpha_mult)),
                bone_base,
                (tip1_x - offset_x, tip1_y - offset_y), 1)

            # Ember sparkles inside wing.
            for i in range(3):
                ember_x = int(cx_local + (i - 1) * 12)
                ember_y = int(cy_local + (i - 1) * 4)
                pygame.draw.rect(wing_surf,
                    (*_NS_vargrath.PALETTE["lava_hot"],
                     int(220 * alpha_mult)),
                    (ember_x, ember_y, 1, 1))

            surface.blit(wing_surf, (offset_x, offset_y))

    def _draw_demon_tail(surface, cx, cy, facing, phase):
        """Long spiked tail curling back."""
        back_dir = -facing
        base_x = cx + back_dir * 6
        base_y = cy + 4

        segments = 6
        points = [(base_x, base_y)]

        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (8 + t * 20))
            y_off = int(2 + t * 6 - t * t * 4)
            wave = math.sin(phase * 1.2 + t * math.pi) * (3 + t * 2)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))

        for i in range(len(points) - 1):
            thickness = max(2, 7 - i)
            _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["shadow_deep"],
                (points[i][0] + 2, points[i][1] + 2),
                (points[i + 1][0] + 2, points[i + 1][1] + 2),
                thickness + 1)
            _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_darkest"],
                points[i], points[i + 1], thickness)
            _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_dark"],
                points[i], points[i + 1], max(1, thickness - 2))
            _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_mid"],
                (points[i][0], points[i][1] - 1),
                (points[i + 1][0], points[i + 1][1] - 1),
                max(1, thickness - 4))

        # Arrow spike at tail end.
        if len(points) >= 2:
            end = points[-1]
            prev = points[-2]
            spike_angle = math.atan2(end[1] - prev[1], end[0] - prev[0])
            spike_len = 9
            spike_tip = (end[0] + int(math.cos(spike_angle) * spike_len),
                         end[1] + int(math.sin(spike_angle) * spike_len))

            perp = spike_angle + math.pi / 2
            base_a = (end[0] + int(math.cos(perp) * 4),
                      end[1] + int(math.sin(perp) * 4))
            base_b = (end[0] - int(math.cos(perp) * 4),
                      end[1] - int(math.sin(perp) * 4))

            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"], [
                (spike_tip[0] + 2, spike_tip[1] + 2),
                (base_a[0] + 2, base_a[1] + 2),
                (base_b[0] + 2, base_b[1] + 2),
            ])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_dark"],
                [spike_tip, base_a, base_b])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_mid"], [
                spike_tip,
                (int((spike_tip[0] + base_a[0]) / 2),
                 int((spike_tip[1] + base_a[1]) / 2)),
                end,
            ])
            # Lava tip.
            _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["lava_mid"],
                                     spike_tip, 2)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (spike_tip[0], spike_tip[1], 1, 1))

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Armored lower body (hip + upper legs)."""
        # Hip plate.
        hip = [
            (cx - 11, cy - 6),
            (cx + 11, cy - 6),
            (cx + 13, cy),
            (cx + 10, cy + 8),
            (cx + 4, cy + 12),
            (cx - 4, cy + 12),
            (cx - 10, cy + 8),
            (cx - 13, cy),
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hip])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_darkest"], hip)
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_dark"], [
            (cx - 10, cy - 5), (cx + 10, cy - 5), (cx + 12, cy),
            (cx + 9, cy + 7), (cx + 4, cy + 11), (cx - 4, cy + 11),
            (cx - 9, cy + 7), (cx - 12, cy),
        ])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_mid"], [
            (cx - 8, cy - 3), (cx + 8, cy - 3), (cx + 10, cy),
            (cx + 7, cy + 5), (cx + 2, cy + 9), (cx - 2, cy + 9),
            (cx - 7, cy + 5), (cx - 10, cy),
        ])

        # Lava crack across hip.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vargrath._alpha(220 * pulse)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_dark"], crack_alpha),
            (cx - 8, cy + 3), (cx + 8, cy + 3), 2)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_mid"], crack_alpha),
            (cx - 6, cy + 3), (cx + 6, cy + 3), 1)
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                         (cx, cy + 3, 1, 1))

        # Upper legs (two dark columns).
        for side in (-1, 1):
            lx = cx + side * 6
            ly1 = cy + 10
            ly2 = cy + 22
            pygame.draw.line(surface, _NS_vargrath.PALETTE["shadow_deep"],
                             (lx + 2, ly1 + 2), (lx + 2, ly2 + 2), 7)
            pygame.draw.line(surface, _NS_vargrath.PALETTE["armor_darkest"],
                             (lx, ly1), (lx, ly2), 6)
            pygame.draw.line(surface, _NS_vargrath.PALETTE["armor_dark"],
                             (lx, ly1), (lx, ly2), 5)
            pygame.draw.line(surface, _NS_vargrath.PALETTE["armor_mid"],
                             (lx + side, ly1), (lx + side, ly2), 2)

            # Small lava vein on leg.
            pygame.draw.line(surface,
                (*_NS_vargrath.PALETTE["lava_dark"], crack_alpha),
                (lx, ly1 + 4), (lx, ly2 - 4), 1)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_mid"],
                             (lx, ly1 + 8, 1, 1))

            # Knee spike.
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_dark"], [
                (lx - side * 2, ly1 + 6),
                (lx - side * 6, ly1 + 4),
                (lx - side * 2, ly1 + 10),
            ])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_mid"], [
                (lx - side * 2, ly1 + 6),
                (lx - side * 5, ly1 + 5),
                (lx - side * 3, ly1 + 8),
            ])

    def _draw_torso(surface, cx, cy, facing, phase):
        """Massive muscular armored torso."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vargrath._alpha(220 * pulse)

        # Torso base.
        torso = [
            (cx - 13, cy - 14),
            (cx - 15, cy - 8),
            (cx - 14, cy),
            (cx - 12, cy + 8),
            (cx - 10, cy + 14),
            (cx + 10, cy + 14),
            (cx + 12, cy + 8),
            (cx + 14, cy),
            (cx + 15, cy - 8),
            (cx + 13, cy - 14),
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_darkest"], torso)

        # Dark armor layer.
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_dark"], [
            (cx - 12, cy - 13), (cx - 14, cy - 7), (cx - 13, cy),
            (cx - 11, cy + 7), (cx - 9, cy + 13),
            (cx + 9, cy + 13), (cx + 11, cy + 7), (cx + 13, cy),
            (cx + 14, cy - 7), (cx + 12, cy - 13),
        ])

        # Chest plate (large ornate).
        chest = [
            (cx - 11, cy - 12),
            (cx + 11, cy - 12),
            (cx + 13, cy - 4),
            (cx + 10, cy + 4),
            (cx + 5, cy + 10),
            (cx - 5, cy + 10),
            (cx - 10, cy + 4),
            (cx - 13, cy - 4),
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_darkest"], chest)
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_dark"], [
            (cx - 10, cy - 11), (cx + 10, cy - 11), (cx + 12, cy - 4),
            (cx + 9, cy + 3), (cx + 4, cy + 9), (cx - 4, cy + 9),
            (cx - 9, cy + 3), (cx - 12, cy - 4),
        ])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_mid"], [
            (cx - 8, cy - 9), (cx + 8, cy - 9), (cx + 10, cy - 3),
            (cx + 7, cy + 2), (cx + 3, cy + 7), (cx - 3, cy + 7),
            (cx - 7, cy + 2), (cx - 10, cy - 3),
        ])

        # Chest highlight.
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_light"], [
            (cx + facing * 2, cy - 8),
            (cx + facing * 6, cy - 5),
            (cx + facing * 5, cy - 1),
            (cx + facing * 1, cy - 3),
        ])

        # Central lava crack (vertical vein from top to belly).
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_darkest"], crack_alpha),
            (cx, cy - 10), (cx, cy + 8), 3)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_dark"], crack_alpha),
            (cx, cy - 10), (cx, cy + 8), 2)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_mid"], crack_alpha),
            (cx, cy - 8), (cx, cy + 6), 1)
        # Bright hot core spots.
        for dy in (-6, -2, 2, 6):
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (cx, cy + dy, 1, 1))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_shine"],
                         (cx, cy - 2, 1, 1))

        # Side lava cracks (diagonal).
        for side in (-1, 1):
            pygame.draw.line(surface,
                (*_NS_vargrath.PALETTE["lava_dark"], crack_alpha),
                (cx + side * 3, cy - 6),
                (cx + side * 8, cy + 4), 1)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_mid"],
                             (cx + side * 5, cy - 1, 1, 1))

        # Shoulder pauldrons (dark with spikes).
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 11
            _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["shadow_deep"],
                                     (sh_x + 1, sh_y + 1), 6)
            _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_darkest"],
                                     (sh_x, sh_y), 6)
            _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_dark"],
                                     (sh_x, sh_y), 5)
            _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_mid"],
                                     (sh_x + side, sh_y - 1), 3)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["armor_light"],
                             (sh_x + side, sh_y - 2, 1, 1))

            # Spikes on pauldron.
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_dark"], [
                (sh_x + side * 2, sh_y - 4),
                (sh_x + side * 6, sh_y - 8),
                (sh_x + side * 4, sh_y - 2),
            ])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_mid"], [
                (sh_x + side * 3, sh_y - 5),
                (sh_x + side * 5, sh_y - 7),
                (sh_x + side * 4, sh_y - 3),
            ])
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_light"],
                             (sh_x + side * 6, sh_y - 8, 1, 1))

            # Lava glow on shoulder.
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_mid"],
                             (sh_x, sh_y, 1, 1))
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (sh_x, sh_y, 1, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 2
        sh_x = cx - facing * 11
        sh_y = cy
        elb_x = cx - facing * 15
        elb_y = cy + 10 + int(sway)
        hand_x = cx - facing * 13
        hand_y = cy + 20

        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 7)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_mid"],
                              (sh_x - facing, sh_y - 1),
                              (elb_x - facing, elb_y - 1), 2)

        # Forearm.
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 6)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 4)

        # Clawed hand.
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_darkest"],
                                 (hand_x, hand_y), 4)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_dark"],
                                 (hand_x, hand_y), 3)
        # Claws.
        for i in range(3):
            angle = i * 0.5 - 0.5
            claw_x = hand_x + int(math.cos(angle) * 5) * (-facing)
            claw_y = hand_y + int(math.sin(angle) * 5) + 3
            _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["horn_dark"],
                                  (hand_x, hand_y + 1), (claw_x, claw_y), 2)
            _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["horn_mid"],
                                  (hand_x, hand_y + 1), (claw_x, claw_y), 1)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_light"],
                             (claw_x, claw_y, 1, 1))

    def _draw_sword_arm(surface, cx, cy, facing, phase, action, blade_angle,
                         attack_progress):
        """Front arm holding greatsword."""
        sh_x = cx + facing * 11
        sh_y = cy

        # Arm goes down-forward to grip sword hilt.
        arm_angle = -math.pi * 0.15 + blade_angle * 0.4
        elb_x = sh_x + int(math.cos(arm_angle) * 10) * facing
        elb_y = sh_y + int(math.sin(arm_angle) * 10) + 4

        grip_angle = arm_angle + blade_angle * 0.5
        hand_x = elb_x + int(math.cos(grip_angle) * 12) * facing
        hand_y = elb_y + int(math.sin(grip_angle) * 12)

        # Upper arm.
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 8)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 7)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_mid"],
                              (sh_x + facing, sh_y - 1),
                              (elb_x + facing, elb_y - 1), 3)
        # Lava crack on arm.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vargrath._alpha(200 * pulse)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_mid"], crack_alpha),
            (sh_x, sh_y), (elb_x, elb_y), 1)

        # Forearm gauntlet.
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 7)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 6)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_mid"],
                              (elb_x + facing, elb_y - 1),
                              (hand_x + facing, hand_y - 1), 2)

        # Elbow spike.
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_dark"], [
            (elb_x - facing * 3, elb_y - 3),
            (elb_x - facing * 8, elb_y - 6),
            (elb_x - facing * 3, elb_y + 1),
        ])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_mid"], [
            (elb_x - facing * 3, elb_y - 3),
            (elb_x - facing * 6, elb_y - 5),
            (elb_x - facing * 3, elb_y),
        ])

        # Hand (gauntlet).
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_darkest"],
                                 (hand_x, hand_y), 5)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_dark"],
                                 (hand_x, hand_y), 4)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_mid"],
                                 (hand_x, hand_y - 1), 3)
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["armor_light"],
                         (hand_x, hand_y - 1, 1, 1))

        # Draw greatsword.
        _NS_vargrath._draw_greatsword(surface, hand_x, hand_y, facing, phase,
                                       blade_angle, action, attack_progress)

    def _draw_greatsword(surface, hx, hy, facing, phase, angle, action,
                          attack_progress):
        """Massive greatsword with lava cracks on blade."""
        # Sword points down at rest, up when raised.
        base_angle = math.pi * 0.5 + angle  # default down

        # Blade lengths.
        guard_len = 6
        blade_len = 42

        # Direction unit vector.
        dx = math.cos(base_angle) * facing
        dy = math.sin(base_angle)

        # Pommel (below hand).
        pommel_x = hx - int(dx * 6)
        pommel_y = hy - int(dy * 6)

        # Guard center (at hand).
        guard_x = hx
        guard_y = hy

        # Blade tip.
        tip_x = guard_x + int(dx * blade_len)
        tip_y = guard_y + int(dy * blade_len)

        # Perpendicular for width.
        perp_x = -math.sin(base_angle) * facing
        perp_y = math.cos(base_angle)

        # POMMEL (round dark iron).
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["shadow_deep"],
                                 (pommel_x + 1, pommel_y + 1), 4)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_darkest"],
                                 (pommel_x, pommel_y), 4)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["armor_dark"],
                                 (pommel_x, pommel_y), 3)
        # Lava gem in pommel.
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["lava_dark"],
                                 (pommel_x, pommel_y), 2)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["lava_mid"],
                                 (pommel_x, pommel_y), 1)
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                         (pommel_x, pommel_y, 1, 1))

        # GRIP (between pommel and guard).
        pygame.draw.line(surface, _NS_vargrath.PALETTE["shadow_deep"],
                         (pommel_x + 1, pommel_y + 1),
                         (guard_x + 1, guard_y + 1), 3)
        pygame.draw.line(surface, _NS_vargrath.PALETTE["armor_darkest"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 2)
        pygame.draw.line(surface, _NS_vargrath.PALETTE["horn_dark"],
                         (pommel_x, pommel_y), (guard_x, guard_y), 1)

        # GUARD (cross-guard, wide).
        guard_a = (guard_x + int(perp_x * guard_len),
                   guard_y + int(perp_y * guard_len))
        guard_b = (guard_x - int(perp_x * guard_len),
                   guard_y - int(perp_y * guard_len))
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["shadow_deep"],
                              (guard_a[0] + 1, guard_a[1] + 1),
                              (guard_b[0] + 1, guard_b[1] + 1), 5)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_darkest"],
                              guard_a, guard_b, 4)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_dark"],
                              guard_a, guard_b, 3)
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["armor_mid"],
                              guard_a, guard_b, 1)
        # Curved horn tips at guard ends.
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["horn_dark"],
                                 guard_a, 2)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["horn_dark"],
                                 guard_b, 2)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["horn_mid"],
                                 guard_a, 1)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["horn_mid"],
                                 guard_b, 1)

        # BLADE (long, wide, tapered).
        blade_wide = 5
        # Blade side points.
        blade_base_a = (guard_x + int(perp_x * blade_wide),
                        guard_y + int(perp_y * blade_wide))
        blade_base_b = (guard_x - int(perp_x * blade_wide),
                        guard_y - int(perp_y * blade_wide))
        # Mid points.
        mid_x = guard_x + int(dx * blade_len * 0.6)
        mid_y = guard_y + int(dy * blade_len * 0.6)
        blade_mid_a = (mid_x + int(perp_x * blade_wide),
                       mid_y + int(perp_y * blade_wide))
        blade_mid_b = (mid_x - int(perp_x * blade_wide),
                       mid_y - int(perp_y * blade_wide))

        # Draw blade polygon (shadow).
        blade_pts_shadow = [
            (blade_base_a[0] + 2, blade_base_a[1] + 2),
            (blade_mid_a[0] + 2, blade_mid_a[1] + 2),
            (tip_x + 2, tip_y + 2),
            (blade_mid_b[0] + 2, blade_mid_b[1] + 2),
            (blade_base_b[0] + 2, blade_base_b[1] + 2),
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"],
                            blade_pts_shadow)

        # Blade dark.
        blade_pts = [
            blade_base_a, blade_mid_a, (tip_x, tip_y),
            blade_mid_b, blade_base_b,
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["blade_darkest"],
                            blade_pts)

        # Inner blade mid.
        inner_blade = [
            (int(blade_base_a[0] * 0.85 + guard_x * 0.15),
             int(blade_base_a[1] * 0.85 + guard_y * 0.15)),
            (int(blade_mid_a[0] * 0.85 + mid_x * 0.15),
             int(blade_mid_a[1] * 0.85 + mid_y * 0.15)),
            (int(tip_x * 0.9 + mid_x * 0.1),
             int(tip_y * 0.9 + mid_y * 0.1)),
            (int(blade_mid_b[0] * 0.85 + mid_x * 0.15),
             int(blade_mid_b[1] * 0.85 + mid_y * 0.15)),
            (int(blade_base_b[0] * 0.85 + guard_x * 0.15),
             int(blade_base_b[1] * 0.85 + guard_y * 0.15)),
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["blade_dark"],
                            inner_blade)

        # Central lava crack along blade (fuller).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        crack_alpha = _NS_vargrath._alpha(240 * pulse)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_darkest"], crack_alpha),
            (guard_x, guard_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_dark"], crack_alpha),
            (guard_x, guard_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface,
            (*_NS_vargrath.PALETTE["lava_mid"], crack_alpha),
            (guard_x, guard_y), (tip_x, tip_y), 1)

        # Bright hot spots along fuller.
        for i in range(1, 5):
            t = i / 5
            spot_x = int(guard_x + (tip_x - guard_x) * t)
            spot_y = int(guard_y + (tip_y - guard_y) * t)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (spot_x, spot_y, 1, 1))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_shine"],
                         (int((guard_x + tip_x) / 2),
                          int((guard_y + tip_y) / 2), 1, 1))

        # Blade edge highlight.
        _NS_vargrath._aaline(surface, _NS_vargrath.PALETTE["blade_light"],
                              blade_base_a, (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["blade_shine"],
                         (tip_x, tip_y, 1, 1))

        # Blade tip glow (lava).
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["lava_dark"],
                                 (tip_x, tip_y), 3)
        _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["lava_mid"],
                                 (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                         (tip_x, tip_y, 1, 1))

        # Swing streak during attack.
        if action == "attack" and 0.35 < attack_progress < 0.7:
            streak_intensity = math.sin((attack_progress - 0.35) / 0.35 * math.pi)
            streak_alpha = _NS_vargrath._alpha(230 * streak_intensity)

            # Arc trail behind blade.
            arc_start = base_angle - 0.4
            arc_end = base_angle
            for i in range(8):
                arc_t = i / 8
                trail_angle = arc_start + (arc_end - arc_start) * arc_t
                trail_dx = math.cos(trail_angle) * facing
                trail_dy = math.sin(trail_angle)
                trail_len = blade_len + 4
                trail_x = guard_x + int(trail_dx * trail_len)
                trail_y = guard_y + int(trail_dy * trail_len)

                alpha_t = _NS_vargrath._alpha(streak_alpha * (1 - arc_t) * 0.8)
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], alpha_t),
                    (trail_x, trail_y), 4)
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], alpha_t),
                    (trail_x, trail_y), 3)
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_hot"], alpha_t),
                    (trail_x, trail_y), 1)

    def _draw_demon_head(surface, cx, cy, facing, phase, action,
                          attack_progress):
        """Horned demon head."""
        # Head shape (angular, wide-jawed).
        head_shape = [
            (cx - 8, cy + 5),
            (cx - 10, cy),
            (cx - 9, cy - 6),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 9, cy - 6),
            (cx + 10, cy),
            (cx + 8, cy + 5),
            (cx + 5, cy + 8),
            (cx - 5, cy + 8),
        ]
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["armor_darkest"],
                            head_shape)
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["flesh_darkest"], [
            (cx - 7, cy + 4), (cx - 9, cy), (cx - 8, cy - 5),
            (cx - 3, cy - 9), (cx + 3, cy - 9), (cx + 8, cy - 5),
            (cx + 9, cy), (cx + 7, cy + 4),
            (cx + 4, cy + 7), (cx - 4, cy + 7),
        ])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["flesh_dark"], [
            (cx - 6, cy + 2), (cx - 8, cy - 1), (cx - 7, cy - 4),
            (cx - 2, cy - 8), (cx + 2, cy - 8), (cx + 7, cy - 4),
            (cx + 8, cy - 1), (cx + 6, cy + 2),
        ])
        _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["flesh_mid"], [
            (cx - 4, cy - 2), (cx - 5, cy - 5), (cx - 1, cy - 7),
            (cx + 1, cy - 7), (cx + 5, cy - 5), (cx + 4, cy - 2),
        ])

        # Face highlight.
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["flesh_light"],
                         (cx + facing * 3, cy - 4, 2, 2))

        # HORNS (large curved).
        _NS_vargrath._draw_demon_horns(surface, cx, cy, facing, phase)

        # GLOWING RED EYES.
        _NS_vargrath._draw_demon_eye(surface, cx + facing * 2, cy - 3, facing, phase)
        # Second eye (smaller, further).
        _NS_vargrath._draw_demon_eye_small(surface, cx - facing * 3, cy - 3,
                                             facing, phase)

        # Jaw / fangs (opens during attack).
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 4)

        _NS_vargrath._draw_demon_mouth(surface, cx, cy, facing, phase, mouth_open)

    def _draw_demon_horns(surface, cx, cy, facing, phase):
        """Large curved horns."""
        for i, (base_off_x, angle_deg, length) in enumerate([
            (-5, 60, 12),   # left horn
            (-2, 80, 14),   # left-inner
            (2, 100, 14),   # right-inner
            (5, 120, 12),   # right horn
        ]):
            sway = math.sin(phase * 0.4 + i * 0.4) * 1
            base_x = cx + base_off_x
            base_y = cy - 8

            angle_rad = math.radians(angle_deg)
            tip_x = base_x + int(math.cos(angle_rad) * length * 0.6)
            tip_y = base_y - int(math.sin(angle_rad) * length) + int(sway)

            perp_x = -math.sin(angle_rad)
            perp_y = math.cos(angle_rad)
            pa = (base_x + int(perp_x * 2), base_y + int(perp_y * 2))
            pb = (base_x - int(perp_x * 2), base_y - int(perp_y * 2))

            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa[0] + 1, pa[1] + 1),
                (pb[0] + 1, pb[1] + 1),
            ])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_dark"],
                                [(tip_x, tip_y), pa, pb])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["horn_mid"], [
                (tip_x, tip_y),
                (int((tip_x + pa[0]) / 2), int((tip_y + pa[1]) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_shine"],
                             (tip_x, tip_y, 1, 1))

    def _draw_demon_eye(surface, cx, cy, facing, phase):
        """Large glowing red eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        ex = cx
        ey = cy

        pygame.draw.rect(surface, _NS_vargrath.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))

        # Halo glow.
        for radius in range(6, 0, -1):
            alpha = _NS_vargrath._alpha(100 * (6 - radius) / 6 * pulse)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["eye_mid"], alpha),
                (ex + 1, ey), radius)

        # Iris.
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_darkest"],
                         (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_dark"],
                         (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_mid"],
                         (ex + 1, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_light"],
                         (ex + 1, ey, 1, 1))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_glow"],
                         (ex + 2, ey, 1, 1))

    def _draw_demon_eye_small(surface, cx, cy, facing, phase):
        """Smaller second eye."""
        pulse = math.sin(phase * 2 + 1) * 0.3 + 0.7
        ex = cx
        ey = cy
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["shadow_deep"],
                         (ex - 1, ey - 1, 3, 3))
        for radius in range(3, 0, -1):
            alpha = _NS_vargrath._alpha(120 * (3 - radius) / 3 * pulse)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["eye_mid"], alpha),
                (ex, ey), radius)
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_dark"],
                         (ex, ey, 2, 2))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_light"],
                         (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_vargrath.PALETTE["eye_glow"],
                         (ex, ey, 1, 1))

    def _draw_demon_mouth(surface, cx, cy, facing, phase, mouth_open):
        """Fanged mouth."""
        mouth_y = cy + 4

        if mouth_open > 0:
            # Open jaw with fangs.
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["shadow_deep"], [
                (cx - 4, mouth_y),
                (cx + 4, mouth_y),
                (cx + 3, mouth_y + int(mouth_open)),
                (cx - 3, mouth_y + int(mouth_open)),
            ])
            _NS_vargrath._poly(surface, _NS_vargrath.PALETTE["eye_darkest"], [
                (cx - 3, mouth_y + 1),
                (cx + 3, mouth_y + 1),
                (cx + 2, mouth_y + int(mouth_open) - 1),
                (cx - 2, mouth_y + int(mouth_open) - 1),
            ])

            # Lava glow inside.
            glow_r = int(2 + mouth_open * 0.3)
            for r in range(glow_r + 2, 0, -1):
                alpha = _NS_vargrath._alpha(180 * (glow_r + 2 - r) / (glow_r + 2))
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                    (cx, mouth_y + int(mouth_open * 0.5)), r)
            _NS_vargrath._aacircle(surface,
                _NS_vargrath.PALETTE["lava_mid"],
                (cx, mouth_y + int(mouth_open * 0.5)), max(1, glow_r - 1))
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (cx, mouth_y + int(mouth_open * 0.5), 1, 1))

            # Upper fangs.
            for x_off in (-3, 0, 3):
                fang_x = cx + x_off
                fang_tip_y = mouth_y + int(mouth_open * 0.7)
                pygame.draw.line(surface, _NS_vargrath.PALETTE["horn_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_vargrath.PALETTE["horn_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_light"],
                                 (fang_x, fang_tip_y, 1, 1))
        else:
            # Closed mouth.
            pygame.draw.line(surface, _NS_vargrath.PALETTE["shadow_deep"],
                             (cx - 4, mouth_y + 1),
                             (cx + 4, mouth_y + 1), 1)
            # Fang points visible.
            for x_off in (-2, 2):
                fang_x = cx + x_off
                pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_mid"],
                                 (fang_x, mouth_y + 1, 1, 2))
                pygame.draw.rect(surface, _NS_vargrath.PALETTE["horn_light"],
                                 (fang_x, mouth_y + 2, 1, 1))

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
        pygame.draw.ellipse(shadow, (40, 15, 10, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_ember_aura(surface, x, y, phase):
        """Fiery aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_vargrath._alpha((90 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vargrath._aacircle(aura,
                    (*_NS_vargrath.PALETTE["lava_darkest"], alpha),
                    (110, 100), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_vargrath._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vargrath._aacircle(aura,
                    (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                    (110, 100), radius)
        # Abyss purple accent.
        for radius in range(30, 5, -3):
            alpha = _NS_vargrath._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vargrath._aacircle(aura,
                    (*_NS_vargrath.PALETTE["abyss_dark"], alpha),
                    (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Ember particles rising.
        for i in range(15):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = (_NS_vargrath.PALETTE["lava_mid"] if i % 3 != 0
                     else _NS_vargrath.PALETTE["abyss_mid"])
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Infernal ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vargrath.PALETTE["lava_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_vargrath.PALETTE["lava_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_vargrath.PALETTE["lava_mid"], 230),
                            (25, 22, 120, 18), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vargrath.PALETTE["lava_hot"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_vargrath.PALETTE["lava_shine"],
                 _NS_vargrath._alpha(150 * pulse)),
                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    def _draw_ember_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Ember + smoke mist."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_vargrath._alpha((32 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_vargrath.PALETTE["smoke_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_vargrath._alpha((20 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising embers.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_vargrath._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            pygame.draw.rect(surface,
                (*_NS_vargrath.PALETTE["lava_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                (*_NS_vargrath.PALETTE["lava_hot"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_vargrath.PALETTE["lava_shine"], alpha),
                (sx, sy - 1, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vargrath._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["smoke_dark"], alpha),
                    (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], alpha),
                    (sx, sy - 1, 2, 2))

    # ============================================================
    # SKILL: Q - BLOOD THIRST (blade swing arc + heal)
    # ============================================================
    def _draw_bloodthirst_skill(surface, boss, x, y, timer, phase):
        """Large arc slash forward with lava wave."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge (glow on blade).
            t = progress / 0.3
            gr = int(4 + t * 8)
            # Glow at boss's blade position (roughly right/left of body).
            bx = x + facing * 30
            by = y - 10
            for r in range(gr + 3, 0, -1):
                alpha = _NS_vargrath._alpha(200 * (gr + 3 - r) / (gr + 3))
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], alpha), (bx, by), r)
            _NS_vargrath._aacircle(surface, _NS_vargrath.PALETTE["lava_mid"],
                                     (bx, by), max(1, gr - 2))
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_shine"],
                             (bx, by, 1, 1))
        else:
            # Swing arc.
            t = (progress - 0.3) / 0.7
            arc_intensity = math.sin(t * math.pi)

            # Arc path (crescent slash in front of boss).
            center_x = x
            center_y = y - 5
            radius = 45 + int(t * 15)
            arc_alpha = _NS_vargrath._alpha(240 * arc_intensity)

            # Draw many arc points forming a crescent.
            arc_points = []
            arc_start = -math.pi / 3
            arc_end = math.pi / 3
            for i in range(20):
                arc_t = i / 19
                angle = arc_start + (arc_end - arc_start) * arc_t
                ax = center_x + int(math.cos(angle) * radius) * facing
                ay = center_y + int(math.sin(angle) * radius)
                arc_points.append((ax, ay))

            # Outer arc (dark).
            for i in range(len(arc_points) - 1):
                _NS_vargrath._aaline(surface,
                    (*_NS_vargrath.PALETTE["lava_darkest"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 6)
                _NS_vargrath._aaline(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 4)
                _NS_vargrath._aaline(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 2)
                _NS_vargrath._aaline(surface,
                    (*_NS_vargrath.PALETTE["lava_hot"], arc_alpha),
                    arc_points[i], arc_points[i + 1], 1)

            # Bright sparks along arc.
            for i, pt in enumerate(arc_points):
                if i % 2 == 0:
                    pygame.draw.rect(surface,
                        (*_NS_vargrath.PALETTE["lava_shine"], arc_alpha),
                        (pt[0], pt[1], 2, 2))
                    pygame.draw.rect(surface,
                        (*_NS_vargrath.PALETTE["white"], arc_alpha),
                        (pt[0], pt[1], 1, 1))

            # Trailing embers falling from arc.
            for i in range(12):
                fall_t = (phase * 0.5 + i * 0.08) % 1.0
                ei = i % len(arc_points)
                start_pt = arc_points[ei]
                fx = start_pt[0] + int(math.sin(phase + i) * 3)
                fy = start_pt[1] + int(fall_t * 18)
                fall_alpha = _NS_vargrath._alpha(200 * arc_intensity * (1 - fall_t))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_hot"], fall_alpha),
                    (fx, fy, 1, 1))

            # Impact burst at arc center-front.
            if t > 0.5:
                impact_t = (t - 0.5) / 0.5
                impact_x = x + facing * 60
                impact_y = y
                imp_r = int(8 + impact_t * 20)
                imp_alpha = _NS_vargrath._alpha(200 * (1 - impact_t))
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], imp_alpha),
                    (impact_x, impact_y), imp_r, 2)
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], imp_alpha),
                    (impact_x, impact_y), max(1, imp_r - 4), 1)
                # Upward burst embers.
                for i in range(8):
                    burst_angle = -math.pi / 2 + (i - 4) * 0.3
                    br = imp_r + int(impact_t * 15)
                    bx = impact_x + int(math.cos(burst_angle) * br)
                    by = impact_y + int(math.sin(burst_angle) * br)
                    pygame.draw.rect(surface,
                        (*_NS_vargrath.PALETTE["lava_hot"], imp_alpha),
                        (bx, by, 2, 2))

    # ============================================================
    # SKILL: W - DEMONIC CHARGE (rush forward with trail)
    # ============================================================
    def _draw_charge_ground(surface, boss, x, y, timer, phase):
        """Fiery trail on ground behind boss."""
        facing = boss.direction
        # Trail streaks behind boss.
        for i in range(8):
            offset = -(i + 1) * 12 * facing
            trail_x = x + offset
            trail_y = y + 40 + int(math.sin(phase + i) * 2)
            alpha = _NS_vargrath._alpha(220 - i * 25)
            if alpha <= 0:
                continue
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_darkest"], alpha),
                (trail_x - 10, trail_y - 3, 20, 6))
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                (trail_x - 8, trail_y - 2, 16, 4))
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_mid"], alpha),
                (trail_x - 5, trail_y - 1, 10, 2))
            pygame.draw.rect(surface,
                (*_NS_vargrath.PALETTE["lava_hot"], alpha),
                (trail_x, trail_y, 1, 1))

    def _draw_charge_foreground(surface, boss, x, y, timer, phase):
        """Speed lines + embers flying."""
        facing = boss.direction
        # Speed lines behind boss.
        for i in range(6):
            offset = -(i + 1) * 8 * facing
            lx1 = x + offset
            lx2 = x + offset - 12 * facing
            ly = y - 10 + int(math.sin(phase * 2 + i) * 8)
            alpha = _NS_vargrath._alpha(180 - i * 25)
            pygame.draw.line(surface,
                (*_NS_vargrath.PALETTE["lava_mid"], alpha),
                (lx1, ly), (lx2, ly), 2)
            pygame.draw.line(surface,
                (*_NS_vargrath.PALETTE["lava_hot"], alpha),
                (lx1, ly), (lx2, ly), 1)

        # Ember burst around boss.
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.5
            er = 30 + int(math.sin(phase * 2 + i) * 5)
            ex = x + int(math.cos(angle) * er)
            ey = y + int(math.sin(angle) * er * 0.6)
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_mid"],
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                             (ex, ey, 1, 1))

    # ============================================================
    # SKILL: E - DEVIL'S STRIKE (ground slam)
    # ============================================================
    def _draw_devilstrike_ground(surface, boss, x, y, timer, phase):
        """Expanding shockwave ring on ground."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Warning circle.
            t = progress / 0.3
            r = int(30 * t)
            alpha = _NS_vargrath._alpha(200 * t)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                (x, y + 40), r, 3)
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = x + int(math.cos(angle) * r)
                sy = y + 40 + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface,
                    _NS_vargrath.PALETTE["lava_hot"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.3) / 0.7
            r = int(30 + t * 55)
            alpha = _NS_vargrath._alpha(230 * (1 - t))
            # Multiple concentric rings.
            for i in range(3):
                arc_r = r - i * 8
                if arc_r < 5:
                    continue
                arc_alpha = _NS_vargrath._alpha(alpha * (1 - i * 0.3))
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_darkest"], arc_alpha),
                    (x, y + 40), arc_r, 3)
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], arc_alpha),
                    (x, y + 40), arc_r, 2)
                _NS_vargrath._aacircle(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], arc_alpha),
                    (x, y + 40), arc_r, 1)

    def _draw_devilstrike_foreground(surface, boss, x, y, timer, phase):
        """Rising lava column + rocks."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charging (staff/blade raised, sparks gather).
            t = progress / 0.3
            for i in range(8):
                angle = i * math.pi / 4 + phase * 3
                r = int(20 * (1 - t))
                sx = x + int(math.cos(angle) * r)
                sy = y - 5 + int(math.sin(angle) * r)
                pygame.draw.rect(surface, _NS_vargrath.PALETTE["lava_hot"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.3) / 0.7
            intensity = math.sin(t * math.pi)

            # Central lava column erupting upward.
            col_h = int(80 * intensity)
            col_w = int(6 + intensity * 4)
            col_y_top = y + 40 - col_h

            # Column layers.
            for layer_i, (width, alpha_val) in enumerate([
                (col_w + 4, 100), (col_w + 2, 150),
                (col_w, 200), (col_w - 2, 240),
            ]):
                if width <= 0:
                    continue
                actual_alpha = _NS_vargrath._alpha(alpha_val * intensity)
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], actual_alpha),
                    (x - width // 2, col_y_top, width, col_h))

            # Bright core.
            core_alpha = _NS_vargrath._alpha(255 * intensity)
            pygame.draw.rect(surface,
                (*_NS_vargrath.PALETTE["lava_hot"], core_alpha),
                (x - 1, col_y_top, 2, col_h))
            pygame.draw.rect(surface,
                (*_NS_vargrath.PALETTE["lava_shine"], core_alpha),
                (x, col_y_top, 1, col_h))

            # Rocks flying up.
            for i in range(10):
                rock_t = (phase * 0.5 + i * 0.1) % 1.0
                rx = x + int(math.sin(phase + i) * 30)
                ry = y + 40 - int(rock_t * col_h) - 5
                rock_alpha = _NS_vargrath._alpha(220 * intensity * (1 - rock_t * 0.5))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["armor_darkest"], rock_alpha),
                    (rx, ry, 3, 3))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["armor_dark"], rock_alpha),
                    (rx, ry, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], rock_alpha),
                    (rx, ry, 1, 1))

            # Sparks radiating outward.
            for i in range(16):
                angle = i * math.pi / 8
                sr = int(intensity * 50)
                sx = x + int(math.cos(angle) * sr)
                sy = y + 40 + int(math.sin(angle) * sr * 0.5)
                spark_alpha = _NS_vargrath._alpha(200 * intensity)
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_hot"], spark_alpha),
                    (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_shine"], spark_alpha),
                    (sx, sy, 1, 1))

    # ============================================================
    # SKILL: R - SOUL DOMINATOR (leap + massive crash)
    # ============================================================
    def _draw_souldom_ground(surface, boss, x, y, timer, phase):
        """Target circle grows before impact."""
        tx, ty = _NS_vargrath._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Warning ring growing.
            t = progress / 0.5
            r = int(50 * t)
            alpha = _NS_vargrath._alpha(200 * t)
            # Multiple ring layers.
            for i in range(3):
                ring_r = r - i * 6
                if ring_r < 5:
                    continue
                ring_alpha = _NS_vargrath._alpha(alpha * (1 - i * 0.25))
                pygame.draw.ellipse(surface,
                    (*_NS_vargrath.PALETTE["lava_darkest"], ring_alpha),
                    (tx - ring_r, ty - ring_r // 3,
                     ring_r * 2, ring_r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                    (*_NS_vargrath.PALETTE["lava_dark"], ring_alpha),
                    (tx - ring_r + 3, ty - ring_r // 3 + 2,
                     ring_r * 2 - 6, ring_r * 2 // 3 - 4), 2)
            # Runes.
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface,
                    _NS_vargrath.PALETTE["lava_hot"], (sx, sy, 2, 2))
        else:
            # Post-crash: burning pool.
            t = (progress - 0.5) / 0.5
            r = int(50 + t * 25)
            alpha = _NS_vargrath._alpha(230 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                (tx - r + 4, ty - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_mid"], alpha),
                (tx - r + 10, ty - r // 3 + 5,
                 r * 2 - 20, r * 2 // 3 - 10))
            # Bright core.
            pygame.draw.ellipse(surface,
                (*_NS_vargrath.PALETTE["lava_hot"], alpha),
                (tx - 5, ty - 2, 10, 4))

    def _draw_souldom_foreground(surface, boss, x, y, timer, phase):
        """Boss leaps up → falls down → impact."""
        tx, ty = _NS_vargrath._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Charge phase: multiple lava pillars rise at target area (warning).
            t = progress / 0.5
            intensity = t

            # 3 warning pillars.
            for i, (dx, dy) in enumerate([(-20, -5), (20, 5), (0, 0)]):
                px = tx + dx
                py = ty + dy
                pillar_h = int(60 * intensity)
                col_alpha = _NS_vargrath._alpha(200 * intensity)

                # Rising pillar.
                for layer_i, (width, alpha_val) in enumerate([
                    (6, 80), (4, 130), (2, 200), (1, 240),
                ]):
                    actual_alpha = _NS_vargrath._alpha(alpha_val * intensity)
                    pygame.draw.rect(surface,
                        (*_NS_vargrath.PALETTE["lava_dark"], actual_alpha),
                        (px - width // 2, py - pillar_h, width, pillar_h))
                # Bright core.
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_hot"], col_alpha),
                    (px, py - pillar_h, 1, pillar_h))

                # Top ember.
                _NS_vargrath._aacircle(surface,
                    _NS_vargrath.PALETTE["lava_mid"],
                    (px, py - pillar_h), 3)
                _NS_vargrath._aacircle(surface,
                    _NS_vargrath.PALETTE["lava_hot"],
                    (px, py - pillar_h), 2)
                pygame.draw.rect(surface,
                    _NS_vargrath.PALETTE["lava_shine"],
                    (px, py - pillar_h, 1, 1))
        elif progress < 0.75:
            # IMPACT: massive column + shockwave.
            t = (progress - 0.5) / 0.25
            intensity = math.sin(t * math.pi)

            # Huge central column.
            col_h = int(200 * intensity)
            col_top = max(0, ty - col_h)

            for layer_i, (width, alpha_val) in enumerate([
                (14, 100), (10, 140), (6, 180), (3, 220), (1, 255),
            ]):
                actual_alpha = _NS_vargrath._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                colors = [
                    _NS_vargrath.PALETTE["lava_darkest"],
                    _NS_vargrath.PALETTE["lava_dark"],
                    _NS_vargrath.PALETTE["lava_mid"],
                    _NS_vargrath.PALETTE["lava_light"],
                    _NS_vargrath.PALETTE["lava_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, col_top, width, ty - col_top))

            # Rising sparks along column.
            for i in range(20):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                spark_y = ty - int(spark_t * (ty - col_top))
                spark_x = tx + int(math.sin(phase * 4 + i) * 6)
                alpha = _NS_vargrath._alpha(240 * intensity * (1 - spark_t * 0.5))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_hot"], alpha),
                    (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_shine"], alpha),
                    (spark_x, spark_y, 1, 1))

            # Impact ground explosion.
            impact_r = int(18 + t * 32)
            impact_alpha = _NS_vargrath._alpha(240 * intensity)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["lava_darkest"], impact_alpha),
                (tx, ty), impact_r + 4, 3)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["lava_dark"], impact_alpha),
                (tx, ty), impact_r, 3)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["lava_mid"], impact_alpha),
                (tx, ty), max(1, impact_r - 6), 2)
            _NS_vargrath._aacircle(surface,
                (*_NS_vargrath.PALETTE["lava_hot"], impact_alpha),
                (tx, ty), max(1, impact_r - 12), 1)

            # Radial burst.
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface,
                    (*_NS_vargrath.PALETTE["lava_light"], impact_alpha),
                    (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_shine"], impact_alpha),
                    (ex, ey, 2, 2))

            # Rock debris flying.
            for i in range(15):
                debris_t = (phase * 0.8 + i * 0.08) % 1.0
                debris_angle = i * math.pi / 7
                debris_r = int(debris_t * impact_r * 1.5)
                dx = tx + int(math.cos(debris_angle) * debris_r)
                dy = ty + int(math.sin(debris_angle) * debris_r * 0.6)
                dy -= int(math.sin(debris_t * math.pi) * 25)  # arc up
                debris_alpha = _NS_vargrath._alpha(220 * (1 - debris_t))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["armor_darkest"], debris_alpha),
                    (dx, dy, 3, 3))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["armor_dark"], debris_alpha),
                    (dx, dy, 2, 2))
                pygame.draw.rect(surface,
                    (*_NS_vargrath.PALETTE["lava_mid"], debris_alpha),
                    (dx, dy, 1, 1))
        else:
            # Aftermath: smoke + embers.
            t = (progress - 0.75) / 0.25
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - int(rise_t * 45)
                alpha = _NS_vargrath._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_vargrath._aacircle(surface,
                        (*_NS_vargrath.PALETTE["smoke_dark"], alpha),
                        (rx, ry), 3)
                    _NS_vargrath._aacircle(surface,
                        (*_NS_vargrath.PALETTE["lava_dark"], alpha),
                        (rx, ry), 2)
                    pygame.draw.rect(surface,
                        (*_NS_vargrath.PALETTE["lava_hot"], alpha),
                        (rx, ry, 1, 1))


# ====================================================================
# nazulmor.py
# ====================================================================

# ====================================================================
# NAZULMOR - THE DEEPBORN HERALD (True Boss)
# ====================================================================


class _NS_nazulmor:
    """Namespace nazulmor - True Boss Eldritch Cthulhu Herald."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Teal-green skin (main body)
        "skin_darkest": (5, 20, 25),
        "skin_dark": (20, 55, 60),
        "skin_mid": (45, 110, 105),
        "skin_light": (95, 175, 155),
        "skin_edge": (160, 220, 190),
        "skin_shine": (220, 250, 230),

        # Green-blue scale armor
        "scale_darkest": (5, 25, 30),
        "scale_dark": (25, 65, 75),
        "scale_mid": (55, 130, 125),
        "scale_light": (110, 195, 170),
        "scale_edge": (170, 230, 200),

        # Belly (pale sickly cyan)
        "belly_darkest": (25, 50, 55),
        "belly_dark": (65, 100, 105),
        "belly_mid": (125, 170, 165),
        "belly_light": (195, 225, 215),

        # Purple bat wing membrane (eldritch)
        "wing_darkest": (15, 5, 30),
        "wing_dark": (45, 20, 70),
        "wing_mid": (95, 45, 135),
        "wing_light": (170, 100, 200),
        "wing_glow": (220, 160, 240),

        # Tentacle (face + hair, pinkish purple)
        "tent_darkest": (25, 8, 35),
        "tent_dark": (70, 25, 80),
        "tent_mid": (140, 55, 145),
        "tent_light": (200, 110, 195),
        "tent_shine": (240, 180, 230),

        # Trident metal (dark iron)
        "metal_darkest": (10, 8, 12),
        "metal_dark": (35, 30, 40),
        "metal_mid": (85, 75, 90),
        "metal_light": (155, 145, 160),
        "metal_shine": (220, 210, 220),

        # Void/eldritch energy (bright teal-cyan glow)
        "void_darkest": (5, 20, 30),
        "void_dark": (15, 60, 90),
        "void_mid": (40, 140, 180),
        "void_light": (120, 220, 240),
        "void_hot": (200, 250, 255),
        "void_shine": (255, 255, 255),

        # Eyes (white glow, no iris)
        "eye_socket": (2, 5, 8),
        "eye_dark": (30, 60, 80),
        "eye_mid": (140, 180, 200),
        "eye_light": (220, 240, 250),
        "eye_glow": (255, 255, 255),

        # Water/mist
        "water_dark": (10, 40, 65),
        "water_mid": (35, 100, 145),
        "water_light": (120, 190, 230),
        "water_foam": (220, 245, 255),

        # Abyssal purple (accent)
        "abyss_darkest": (8, 3, 20),
        "abyss_dark": (30, 12, 55),
        "abyss_mid": (70, 35, 110),
        "abyss_light": (140, 90, 190),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nazulmor._clamp(color)
        if _NS_nazulmor.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_nazulmor._clamp(color)
        if _NS_nazulmor.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_nazulmor._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_nazulmor._clamp(color), points)

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
    def draw_nazulmor(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nazulmor._detect_moving(boss)
        _NS_nazulmor._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_naz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_nazulmor._draw_eldritch_aura(surface, x, y, pulse)
        _NS_nazulmor._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "w":
            _NS_nazulmor._draw_aquashield_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nazulmor._draw_chaotic_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nazulmor._draw_tidalrage_ground(surface, boss, x, y, skill_timer, pulse)

        # Body.
        if attacking:
            _NS_nazulmor._draw_naz_attack(surface, boss, x, y)
        elif moving:
            _NS_nazulmor._draw_naz_float(surface, boss, x, y)
        else:
            _NS_nazulmor._draw_naz_idle(surface, boss, x, y)

        # W shield bubble over body.
        if active_skill == "w":
            _NS_nazulmor._draw_aquashield_bubble(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX.
        if active_skill == "q":
            _NS_nazulmor._draw_typhoon_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nazulmor._draw_tidalrage_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nazulmor._draw_chaotic_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_naz_previous_timer", 0))
        active = bool(getattr(boss, "_naz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._naz_attack_active = True
            boss._naz_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._naz_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._naz_attack_frame = int(getattr(boss, "_naz_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._naz_attack_active = False
            boss._naz_attack_frame = 0
            active = False

        boss._naz_previous_timer = timer
        boss._naz_attack_progress = (
            min(1.0, getattr(boss, "_naz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_naz_last_x"):
            boss._naz_last_x = boss.x
            boss._naz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._naz_last_x)
        dy = abs(boss.y - boss._naz_last_y)
        boss._naz_last_x = boss.x
        boss._naz_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_naz_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_nazulmor._draw_shadow(surface, x, y + 55)
        _NS_nazulmor._draw_water_wisps(surface, x, y + 40, boss.pulse)
        _NS_nazulmor._draw_naz_body(surface, x + sway, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_naz_float(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 7)
        sway = int(math.sin(phase * 0.6) * 4)
        _NS_nazulmor._draw_shadow(surface, x + sway, y + 55)
        _NS_nazulmor._draw_water_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_nazulmor._draw_naz_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")

    def _draw_naz_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_naz_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_naz_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Trident swing.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * facing
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 16)) * facing
            lift = int(4 - t * 8)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(11 * (1 - t)) * facing
            lift = int(-4 + t * 4)

        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_nazulmor._draw_shadow(surface, x + lunge, y + 55)
        _NS_nazulmor._draw_water_wisps(surface, x + lunge, y + 40, boss.pulse,
                                        intense=True)
        _NS_nazulmor._draw_naz_body(surface, x + lunge, y - lift + bob,
                                     facing, boss.pulse, "attack",
                                     progress)

    # ============================================================
    # BODY
    # ============================================================
    def _draw_naz_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        """Eldritch humanoid body with cthulhu head + bat wings + trident."""
        # Bat wings behind.
        _NS_nazulmor._draw_bat_wings(surface, cx, cy - 6, facing, phase, action,
                                      attack_progress)

        # Lower body (fish tail-ish or armored legs).
        _NS_nazulmor._draw_lower_body(surface, cx, cy + 18, facing, phase)

        # Torso armor.
        _NS_nazulmor._draw_torso(surface, cx, cy, facing, phase)

        # Trident angle for attack.
        trident_angle = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                trident_angle = -math.pi * 0.35 * t
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                trident_angle = -math.pi * 0.35 + math.pi * 0.7 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                trident_angle = math.pi * 0.35 * (1 - t)

        # Back arm.
        _NS_nazulmor._draw_back_arm(surface, cx, cy - 4, facing, phase, action)

        # CTHULHU HEAD (with face tentacles!).
        _NS_nazulmor._draw_cthulhu_head(surface, cx + facing * 2, cy - 24,
                                         facing, phase, action, attack_progress)

        # Front arm holding trident.
        _NS_nazulmor._draw_trident_arm(surface, cx, cy - 4, facing, phase,
                                        action, trident_angle, attack_progress)

    def _draw_bat_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Purple bat/demon wings."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 1.1) * 4

        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),
            (1, 0.75, 0.75),
        ]):
            base_x = cx - facing * 5
            base_y = cy - 2

            spar1_len = int(32 * size_mult)
            spar1_angle = math.pi * 0.62 * side_mult - math.radians(beat)

            spar2_len = int(36 * size_mult)
            spar2_angle = math.pi * 0.85 * side_mult - math.radians(beat * 0.8)

            spar3_len = int(28 * size_mult)
            spar3_angle = math.pi * 1.05 * side_mult - math.radians(beat * 0.5)

            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)

            # Bat wing has scalloped edges (curved between fingers).
            membrane_points = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                # scallop curve between tip1-tip2
                (int(tip1_x * 0.55 + tip2_x * 0.45),
                 int(tip1_y * 0.55 + tip2_y * 0.45) + int(5 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.55 + tip3_x * 0.45),
                 int(tip2_y * 0.55 + tip3_y * 0.45) + int(5 * size_mult)),
                (tip3_x, tip3_y),
                (base_x - facing * 3, base_y + int(7 * size_mult)),
            ]

            wing_surf = pygame.Surface((180, 130), pygame.SRCALPHA)
            offset_x = base_x - 90
            offset_y = base_y - 65
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]

            # Dark purple membrane.
            _NS_nazulmor._poly(wing_surf,
                (*_NS_nazulmor.PALETTE["wing_darkest"], int(220 * alpha_mult)),
                local_points)

            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_local * 0.18),
                     int(p[1] * 0.82 + cy_local * 0.18))
                )
            _NS_nazulmor._poly(wing_surf,
                (*_NS_nazulmor.PALETTE["wing_dark"], int(200 * alpha_mult)),
                inner_pts)

            inner2 = []
            for p in local_points:
                inner2.append(
                    (int(p[0] * 0.7 + cx_local * 0.3),
                     int(p[1] * 0.7 + cy_local * 0.3))
                )
            _NS_nazulmor._poly(wing_surf,
                (*_NS_nazulmor.PALETTE["wing_mid"], int(140 * alpha_mult)),
                inner2)

            # Wing bones (fingers).
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                pygame.draw.line(wing_surf,
                    (*_NS_nazulmor.PALETTE["shadow_deep"],
                     int(240 * alpha_mult)),
                    bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                    (*_NS_nazulmor.PALETTE["skin_darkest"],
                     int(240 * alpha_mult)),
                    bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                    (*_NS_nazulmor.PALETTE["skin_dark"],
                     int(200 * alpha_mult)),
                    bone_base, tip, 1)

                # Claw at tip.
                _NS_nazulmor._aacircle(wing_surf,
                    (*_NS_nazulmor.PALETTE["shadow_deep"],
                     int(240 * alpha_mult)),
                    tip, 2)
                _NS_nazulmor._aacircle(wing_surf,
                    (*_NS_nazulmor.PALETTE["metal_dark"],
                     int(240 * alpha_mult)),
                    tip, 1)

            # Eldritch teal glow along top edge.
            pygame.draw.line(wing_surf,
                (*_NS_nazulmor.PALETTE["wing_glow"],
                 int(180 * alpha_mult)),
                bone_base,
                (tip1_x - offset_x, tip1_y - offset_y), 1)

            # Teal magic spots along membrane.
            for i in range(3):
                spot_x = int(cx_local + (i - 1) * 12)
                spot_y = int(cy_local + (i - 1) * 4)
                pygame.draw.rect(wing_surf,
                    (*_NS_nazulmor.PALETTE["void_light"],
                     int(200 * alpha_mult)),
                    (spot_x, spot_y, 1, 1))

            surface.blit(wing_surf, (offset_x, offset_y))

    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Armored lower body with skirt-like scale plates."""
        wave = math.sin(phase * 0.9) * 2

        # Main hip.
        hip = [
            (cx - 11, cy - 6),
            (cx + 11, cy - 6),
            (cx + 13, cy),
            (cx + 12, cy + 8),
            (cx + 6, cy + 14),
            (cx - 6, cy + 14),
            (cx - 12, cy + 8),
            (cx - 13, cy),
        ]
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hip])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_darkest"], hip)
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_dark"], [
            (cx - 10, cy - 5), (cx + 10, cy - 5), (cx + 12, cy),
            (cx + 11, cy + 7), (cx + 5, cy + 13), (cx - 5, cy + 13),
            (cx - 11, cy + 7), (cx - 12, cy),
        ])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_mid"], [
            (cx - 8, cy - 3), (cx + 8, cy - 3), (cx + 10, cy),
            (cx + 9, cy + 5), (cx + 3, cy + 10), (cx - 3, cy + 10),
            (cx - 9, cy + 5), (cx - 10, cy),
        ])

        # Scale skirt (hanging plates).
        for i, dx in enumerate((-8, -3, 3, 8)):
            plate_h = 8 + int(math.sin(phase * 0.5 + i) * 1)
            plate_pts = [
                (cx + dx - 2, cy + 8),
                (cx + dx + 2, cy + 8),
                (cx + dx + 2, cy + 8 + plate_h),
                (cx + dx, cy + 10 + plate_h),
                (cx + dx - 2, cy + 8 + plate_h),
            ]
            _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 1) for p in plate_pts])
            _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_darkest"],
                                plate_pts)
            _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_dark"], [
                (cx + dx - 1, cy + 9),
                (cx + dx + 1, cy + 9),
                (cx + dx + 1, cy + 8 + plate_h - 1),
                (cx + dx, cy + 9 + plate_h),
                (cx + dx - 1, cy + 8 + plate_h - 1),
            ])
            _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_mid"], [
                (cx + dx, cy + 10),
                (cx + dx + 1, cy + 12),
                (cx + dx, cy + 8 + plate_h - 2),
                (cx + dx - 1, cy + 12),
            ])
            # Gold trim at top.
            pygame.draw.line(surface, _NS_nazulmor.PALETTE["scale_edge"],
                             (cx + dx - 2, cy + 8),
                             (cx + dx + 2, cy + 8), 1)

        # Central hanging cloth (dark rag).
        rag = [
            (cx - 4, cy + 8),
            (cx + 4, cy + 8),
            (cx + 3, cy + 18 + int(wave)),
            (cx - 3, cy + 18 - int(wave)),
        ]
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["wing_darkest"], rag)
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["wing_dark"], [
            (cx - 3, cy + 9), (cx + 3, cy + 9),
            (cx + 2, cy + 17 + int(wave)), (cx - 2, cy + 17 - int(wave)),
        ])

    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular torso with scale armor."""
        breath = math.sin(phase * 0.7) * 1

        # Torso base (teal skin).
        torso = [
            (cx - 13, cy - 14),
            (cx - 15, cy - 8),
            (cx - 14, cy),
            (cx - 12, cy + 8),
            (cx - 10, cy + 14),
            (cx + 10, cy + 14),
            (cx + 12, cy + 8),
            (cx + 14, cy),
            (cx + 15, cy - 8),
            (cx + 13, cy - 14),
        ]
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_darkest"], torso)

        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_dark"], [
            (cx - 12, cy - 13), (cx - 14, cy - 7), (cx - 13, cy),
            (cx - 11, cy + 7), (cx - 9, cy + 13),
            (cx + 9, cy + 13), (cx + 11, cy + 7), (cx + 13, cy),
            (cx + 14, cy - 7), (cx + 12, cy - 13),
        ])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_mid"], [
            (cx - 10, cy - 11), (cx - 12, cy - 5), (cx - 11, cy),
            (cx - 9, cy + 6), (cx - 7, cy + 11),
            (cx + 7, cy + 11), (cx + 9, cy + 6), (cx + 11, cy),
            (cx + 12, cy - 5), (cx + 10, cy - 11),
        ])
        # Muscle highlights.
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_light"], [
            (cx - 5, cy - 8), (cx - 7, cy - 3), (cx - 5, cy + 2),
            (cx - 3, cy + int(breath)),
        ])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_light"], [
            (cx + 5, cy - 8), (cx + 7, cy - 3), (cx + 5, cy + 2),
            (cx + 3, cy + int(breath)),
        ])

        # Scale chest plate.
        chest = [
            (cx - 11, cy - 12),
            (cx + 11, cy - 12),
            (cx + 13, cy - 5),
            (cx + 9, cy - 1),
            (cx, cy - 3),
            (cx - 9, cy - 1),
            (cx - 13, cy - 5),
        ]
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_darkest"], chest)
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_dark"], [
            (cx - 10, cy - 11), (cx + 10, cy - 11), (cx + 12, cy - 5),
            (cx + 8, cy - 2), (cx, cy - 4), (cx - 8, cy - 2),
            (cx - 12, cy - 5),
        ])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_mid"], [
            (cx - 8, cy - 10), (cx + 8, cy - 10), (cx + 10, cy - 5),
            (cx, cy - 5), (cx - 10, cy - 5),
        ])
        # Chest scale details.
        for i, (dx, dy) in enumerate([(-5, -9), (0, -8), (5, -9),
                                       (-4, -6), (4, -6)]):
            pygame.draw.line(surface, _NS_nazulmor.PALETTE["scale_darkest"],
                             (cx + dx - 1, cy + dy),
                             (cx + dx, cy + dy - 1), 1)
            pygame.draw.line(surface, _NS_nazulmor.PALETTE["scale_darkest"],
                             (cx + dx, cy + dy - 1),
                             (cx + dx + 1, cy + dy), 1)
            pygame.draw.rect(surface, _NS_nazulmor.PALETTE["scale_edge"],
                             (cx + dx, cy + dy - 1, 1, 1))

        # Central void gem (glowing teal, eldritch).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_nazulmor._alpha(240 * pulse)
        for r in range(5, 0, -1):
            alpha = _NS_nazulmor._alpha(150 * pulse * (5 - r) / 5)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["void_mid"], alpha),
                (cx, cy - 7), r)
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_darkest"],
                         (cx - 1, cy - 8, 3, 3))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_mid"],
                         (cx - 1, cy - 8, 2, 2))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_light"],
                         (cx - 1, cy - 8, 1, 1))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_shine"],
                         (cx, cy - 8, 1, 1))

        # Abs.
        for i in range(3):
            y_ab = cy + 2 + i * 3
            pygame.draw.line(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                             (cx - 5, y_ab), (cx + 5, y_ab), 1)

        # Belly (pale) at bottom.
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["belly_dark"], [
            (cx - 5, cy + 6), (cx + 5, cy + 6),
            (cx + 4, cy + 12), (cx - 4, cy + 12),
        ])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["belly_mid"], [
            (cx - 4, cy + 8), (cx + 4, cy + 8),
            (cx + 3, cy + 11), (cx - 3, cy + 11),
        ])

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.5) * 2
        sh_x = cx - facing * 11
        sh_y = cy
        elb_x = cx - facing * 15
        elb_y = cy + 9 + int(sway)
        hand_x = cx - facing * 12
        hand_y = cy + 18

        # Upper arm.
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 7)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 5)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_mid"],
                              (sh_x - facing, sh_y - 1),
                              (elb_x - facing, elb_y - 1), 2)

        # Forearm.
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 6)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 4)

        # Clawed hand.
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                                 (hand_x, hand_y), 4)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 3)
        # Claws.
        for i in range(3):
            angle = i * 0.5 - 0.5
            claw_x = hand_x + int(math.cos(angle) * 4) * (-facing)
            claw_y = hand_y + int(math.sin(angle) * 4) + 3
            _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                                  (hand_x, hand_y + 1), (claw_x, claw_y), 1)
            pygame.draw.rect(surface, _NS_nazulmor.PALETTE["metal_light"],
                             (claw_x, claw_y, 1, 1))

    def _draw_trident_arm(surface, cx, cy, facing, phase, action,
                           trident_angle, attack_progress):
        """Front arm holding trident."""
        sh_x = cx + facing * 11
        sh_y = cy

        elb_offset = trident_angle
        elb_x = sh_x + int(math.cos(-math.pi * 0.3 + elb_offset) * 10) * facing
        elb_y = sh_y + int(math.sin(-math.pi * 0.3 + elb_offset) * 10) + 4

        hand_x = elb_x + int(math.cos(elb_offset - math.pi * 0.15) * 10) * facing
        hand_y = elb_y + int(math.sin(elb_offset - math.pi * 0.15) * 10)

        # Upper arm.
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                              (sh_x + 2, sh_y + 2),
                              (elb_x + 2, elb_y + 2), 8)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                              (sh_x, sh_y), (elb_x, elb_y), 7)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_dark"],
                              (sh_x, sh_y), (elb_x, elb_y), 6)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_mid"],
                              (sh_x + facing, sh_y - 1),
                              (elb_x + facing, elb_y - 1), 3)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_light"],
                              (sh_x + facing, sh_y - 2),
                              (elb_x + facing, elb_y - 2), 1)

        # Shoulder pauldron (dark scale).
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                                 (sh_x + 1, sh_y + 1), 6)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["scale_darkest"],
                                 (sh_x, sh_y), 6)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["scale_dark"],
                                 (sh_x, sh_y), 5)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["scale_mid"],
                                 (sh_x + facing, sh_y - 1), 3)
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["scale_edge"],
                         (sh_x + facing, sh_y - 2, 1, 1))
        # Small void spot on pauldron.
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_mid"],
                         (sh_x, sh_y, 1, 1))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_light"],
                         (sh_x, sh_y, 1, 1))

        # Forearm.
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                              (elb_x + 2, elb_y + 2),
                              (hand_x + 2, hand_y + 2), 7)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                              (elb_x, elb_y), (hand_x, hand_y), 6)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_dark"],
                              (elb_x, elb_y), (hand_x, hand_y), 5)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["skin_mid"],
                              (elb_x + facing, elb_y - 1),
                              (hand_x + facing, hand_y - 1), 2)

        # Hand gripping shaft.
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                                 (hand_x, hand_y), 4)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 3)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["skin_mid"],
                                 (hand_x, hand_y - 1), 2)

        # Draw trident.
        _NS_nazulmor._draw_trident(surface, hand_x, hand_y, facing, phase,
                                    trident_angle, action, attack_progress)

    def _draw_trident(surface, hx, hy, facing, phase, angle, action,
                       attack_progress):
        """Iron trident with 3 prongs."""
        base_angle = -math.pi * 0.5 + angle

        shaft_len = 34
        head_len = 12

        shaft_dx = math.cos(base_angle) * facing
        shaft_dy = math.sin(base_angle)

        butt_x = hx - int(shaft_dx * 8)
        butt_y = hy - int(shaft_dy * 8)

        head_base_x = hx + int(shaft_dx * shaft_len)
        head_base_y = hy + int(shaft_dy * shaft_len)

        # Shadow shaft.
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                              (butt_x + 2, butt_y + 2),
                              (head_base_x + 2, head_base_y + 2), 4)
        # Shaft (dark iron).
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_darkest"],
                              (butt_x, butt_y),
                              (head_base_x, head_base_y), 3)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_dark"],
                              (butt_x, butt_y),
                              (head_base_x, head_base_y), 2)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_mid"],
                              (butt_x, butt_y),
                              (head_base_x, head_base_y), 1)

        # Grip wraps (rope).
        for i in range(1, 5):
            t = i / 5
            wx = int(butt_x + (head_base_x - butt_x) * t)
            wy = int(butt_y + (head_base_y - butt_y) * t)
            perp_x = -shaft_dy
            perp_y = shaft_dx * facing
            pygame.draw.line(surface, _NS_nazulmor.PALETTE["metal_darkest"],
                             (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                             (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)

        # Crossbar at head.
        perp_x = -shaft_dy
        perp_y = shaft_dx * facing
        cross_a = (head_base_x + int(perp_x * 6),
                   head_base_y + int(perp_y * 6))
        cross_b = (head_base_x - int(perp_x * 6),
                   head_base_y - int(perp_y * 6))
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_dark"],
                              cross_a, cross_b, 3)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_mid"],
                              cross_a, cross_b, 2)
        _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_light"],
                              cross_a, cross_b, 1)

        # Three prongs.
        for prong_offset in (-6, 0, 6):
            prong_start = (head_base_x + int(perp_x * prong_offset),
                           head_base_y + int(perp_y * prong_offset))
            prong_end = (prong_start[0] + int(shaft_dx * head_len),
                         prong_start[1] + int(shaft_dy * head_len))

            _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                                  (prong_start[0] + 1, prong_start[1] + 1),
                                  (prong_end[0] + 1, prong_end[1] + 1), 3)
            _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_darkest"],
                                  prong_start, prong_end, 3)
            _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_dark"],
                                  prong_start, prong_end, 2)
            _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["metal_light"],
                                  prong_start, prong_end, 1)

            # Tip glow (teal void).
            _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["void_dark"],
                                     prong_end, 2)
            _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["void_mid"],
                                     prong_end, 1)
            pygame.draw.rect(surface, _NS_nazulmor.PALETTE["void_light"],
                             (prong_end[0], prong_end[1], 1, 1))

        # Central void glow between prongs.
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gx = head_base_x + int(shaft_dx * head_len * 0.5)
        gy = head_base_y + int(shaft_dy * head_len * 0.5)
        for r in range(5, 0, -1):
            alpha = _NS_nazulmor._alpha(120 * glow_pulse * (5 - r) / 5)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["void_mid"], alpha),
                (gx, gy), r)
        _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["void_light"],
                                 (gx, gy), 1)

        # Swing streak during attack.
        if action == "attack" and 0.35 < attack_progress < 0.65:
            streak_alpha = _NS_nazulmor._alpha(200 *
                math.sin((attack_progress - 0.35) / 0.3 * math.pi))
            for i in range(1, 6):
                t = i * 0.15
                trail_angle = base_angle + t * 0.5 * facing
                trail_x = hx + int(math.cos(trail_angle) * (shaft_len + head_len) * facing)
                trail_y = hy + int(math.sin(trail_angle) * (shaft_len + head_len))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_light"],
                     streak_alpha // (i + 1)),
                    (trail_x, trail_y), max(1, 4 - i))

    # ============================================================
    # CTHULHU HEAD (with face tentacles!)
    # ============================================================
    def _draw_cthulhu_head(surface, cx, cy, facing, phase, action,
                            attack_progress):
        """Iconic cthulhu head with face tentacles."""
        # Head base (rounded octopus-like).
        head_shape = [
            (cx - 9, cy + 4),
            (cx - 11, cy - 2),
            (cx - 10, cy - 8),
            (cx - 5, cy - 12),
            (cx + 5, cy - 12),
            (cx + 10, cy - 8),
            (cx + 11, cy - 2),
            (cx + 9, cy + 4),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
        ]
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_darkest"],
                            head_shape)

        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_dark"], [
            (cx - 8, cy + 3), (cx - 10, cy - 2), (cx - 9, cy - 7),
            (cx - 4, cy - 11), (cx + 4, cy - 11), (cx + 9, cy - 7),
            (cx + 10, cy - 2), (cx + 8, cy + 3),
            (cx + 4, cy + 6), (cx - 4, cy + 6),
        ])
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_mid"], [
            (cx - 6, cy - 4), (cx - 8, cy - 6), (cx - 7, cy - 9),
            (cx - 3, cy - 10), (cx + 3, cy - 10), (cx + 7, cy - 9),
            (cx + 8, cy - 6), (cx + 6, cy - 4),
        ])
        # Highlight.
        _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["skin_light"], [
            (cx + facing * 3, cy - 8),
            (cx + facing * 6, cy - 5),
            (cx + facing * 5, cy - 2),
            (cx + facing * 2, cy - 4),
        ])

        # Head crown/scales (small dorsal bumps on top of head).
        for i, dx in enumerate((-5, -1, 3)):
            bump_y = cy - 10 - int(math.sin(phase * 0.5 + i) * 1)
            _NS_nazulmor._poly(surface, _NS_nazulmor.PALETTE["scale_dark"], [
                (cx + dx - 1, cy - 8),
                (cx + dx, bump_y),
                (cx + dx + 1, cy - 8),
            ])
            pygame.draw.rect(surface, _NS_nazulmor.PALETTE["scale_light"],
                             (cx + dx, bump_y, 1, 1))

        # WHITE GLOWING EYES (2 eyes side by side, no iris).
        _NS_nazulmor._draw_cthulhu_eye(surface, cx - facing * 3, cy - 4,
                                        facing, phase, mirror=True)
        _NS_nazulmor._draw_cthulhu_eye(surface, cx + facing * 3, cy - 4,
                                        facing, phase, mirror=False)

        # FACE TENTACLES (the signature cthulhu feature!).
        _NS_nazulmor._draw_face_tentacles(surface, cx, cy, facing, phase,
                                           action, attack_progress)

    def _draw_cthulhu_eye(surface, cx, cy, facing, phase, mirror=False):
        """Bright white glowing eye (no iris)."""
        pulse = math.sin(phase * 2 + (0.5 if mirror else 0)) * 0.3 + 0.7

        ex = cx
        ey = cy

        # Deep socket.
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 4, 3))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["eye_socket"],
                         (ex - 1, ey - 1, 3, 3))

        # Halo glow.
        for radius in range(5, 0, -1):
            alpha = _NS_nazulmor._alpha(120 * (5 - radius) / 5 * pulse)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["eye_mid"], alpha),
                (ex, ey), radius)

        # White glow (no iris/pupil).
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["eye_dark"],
                         (ex - 1, ey - 1, 3, 2))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["eye_mid"],
                         (ex - 1, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["eye_light"],
                         (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_nazulmor.PALETTE["eye_glow"],
                         (ex, ey, 1, 1))
        # Bright spot.
        if pulse > 0.85:
            pygame.draw.rect(surface, _NS_nazulmor.PALETTE["white"],
                             (ex, ey - 1, 1, 1))

    def _draw_face_tentacles(surface, cx, cy, facing, phase, action,
                              attack_progress):
        """The signature face tentacles hanging from mouth area."""
        # 6 tentacles hanging down from center of face.
        # More agitated during attack.
        wiggle_intensity = 2.5 if action == "attack" else 1.0

        tentacle_configs = [
            # (base_offset_x, length, phase_offset, thickness_start)
            (-5, 12, 0.0, 3),
            (-3, 15, 0.3, 3),
            (-1, 18, 0.6, 4),
            (1, 18, 0.9, 4),
            (3, 15, 1.2, 3),
            (5, 12, 1.5, 3),
        ]

        for base_off, length, phase_off, thickness_start in tentacle_configs:
            base_x = cx + base_off
            base_y = cy + 3

            # Curl segments.
            segments = 6
            points = [(base_x, base_y)]
            for seg in range(1, segments + 1):
                t = seg / segments
                # Base direction: down, with curl influenced by wiggle.
                curl = math.sin(phase * 1.5 + phase_off + t * 2) * (3 * t * wiggle_intensity)
                x_off = int(base_off * 0.3 + curl)
                y_off = int(t * length)
                points.append((base_x + x_off, base_y + y_off))

            # Draw segments (tapered).
            for i in range(len(points) - 1):
                thickness = max(1, thickness_start - i // 2)
                _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["shadow_deep"],
                                      (points[i][0] + 1, points[i][1] + 1),
                                      (points[i + 1][0] + 1, points[i + 1][1] + 1),
                                      thickness + 1)
                _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["tent_darkest"],
                                      points[i], points[i + 1], thickness)
                _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["tent_dark"],
                                      points[i], points[i + 1], max(1, thickness - 1))
                if thickness >= 2:
                    _NS_nazulmor._aaline(surface, _NS_nazulmor.PALETTE["tent_mid"],
                                          (points[i][0] - 1, points[i][1]),
                                          (points[i + 1][0] - 1, points[i + 1][1]),
                                          max(1, thickness - 2))

                # Suckers (small dots).
                if i % 2 == 1 and thickness >= 2:
                    pygame.draw.rect(surface, _NS_nazulmor.PALETTE["tent_light"],
                                     (points[i][0], points[i][1], 1, 1))

            # Tentacle tip highlight.
            if points:
                pygame.draw.rect(surface, _NS_nazulmor.PALETTE["tent_light"],
                                 (points[-1][0], points[-1][1], 1, 1))

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
        pygame.draw.ellipse(shadow, (2, 4, 6, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (20, 50, 60, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_eldritch_aura(surface, x, y, phase):
        """Eldritch teal + purple aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((240, 220), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_nazulmor._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nazulmor._aacircle(aura,
                    (*_NS_nazulmor.PALETTE["water_dark"], alpha),
                    (120, 110), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_nazulmor._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nazulmor._aacircle(aura,
                    (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                    (120, 110), radius)
        # Purple inner tint.
        for radius in range(40, 5, -3):
            alpha = _NS_nazulmor._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nazulmor._aacircle(aura,
                    (*_NS_nazulmor.PALETTE["abyss_dark"], alpha),
                    (120, 110), radius)
        surface.blit(aura, (x - 120, y - 110))

        # Floating particles.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            if i % 3 == 0:
                color = _NS_nazulmor.PALETTE["abyss_light"]
                hot = _NS_nazulmor.PALETTE["tent_light"]
            else:
                color = _NS_nazulmor.PALETTE["void_light"]
                hot = _NS_nazulmor.PALETTE["void_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Eldritch ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nazulmor.PALETTE["water_dark"], 200),
                            (5, 20, 170, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_nazulmor.PALETTE["void_darkest"], 220),
                            (14, 22, 152, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_nazulmor.PALETTE["void_dark"], 230),
                            (25, 24, 130, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_nazulmor.PALETTE["abyss_dark"], 180),
                            (40, 26, 100, 18), 1)

        # Eldritch runes (cross patterns).
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 35 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 35 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_nazulmor.PALETTE["void_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                (*_NS_nazulmor.PALETTE["void_hot"],
                 _NS_nazulmor._alpha(150 * pulse)),
                (15, 14, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))

    def _draw_water_wisps(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Water + eldritch mist."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((160, 55), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_nazulmor._alpha((38 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_nazulmor.PALETTE["water_dark"], alpha),
                    (80 - radius * 2, 27 - radius // 3,
                     radius * 4, max(3, radius // 2)))
        for radius in range(24, 3, -2):
            alpha = _NS_nazulmor._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist,
                    (*_NS_nazulmor.PALETTE["void_mid"], alpha),
                    (80 - radius, 27 - radius // 4,
                     radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 80, cy - 12))

        # Rising bubbles.
        for i, offset in enumerate((-28, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_nazulmor._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["water_dark"], alpha), (sx, sy), 3)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["void_mid"], alpha),
                (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                (*_NS_nazulmor.PALETTE["void_light"], alpha), (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                (*_NS_nazulmor.PALETTE["void_hot"], alpha), (sx, sy - 2, 1, 1))

        # Purple abyss wisps.
        for i in range(6):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 22 + i * 10 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 22)
            alpha = _NS_nazulmor._alpha(180 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["abyss_dark"], alpha), (wx, wy), 2)
                pygame.draw.rect(surface,
                    _NS_nazulmor.PALETTE["tent_light"], (wx, wy, 1, 1))

        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nazulmor._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["water_dark"], alpha),
                    (sx, sy), max(2, 7 - i))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_mid"], alpha),
                    (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                    (*_NS_nazulmor.PALETTE["void_light"], alpha),
                    (sx, sy - 1, 2, 2))

    # ============================================================
    # SKILL: Q - TYPHOON (swirling water vortex projectile)
    # ============================================================
    def _draw_typhoon_skill(surface, boss, x, y, timer, phase):
        """Swirling water tornado forward + eldritch tint."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nazulmor._target_position(boss, x, y)

        if progress < 0.2:
            # Charge at trident tip.
            t = progress / 0.2
            tip_x = x + facing * 34
            tip_y = y - 30
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_nazulmor._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_darkest"], alpha),
                    (tip_x, tip_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_nazulmor._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                    (tip_x, tip_y), r)
            _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["void_mid"],
                                     (tip_x, tip_y), cr - 2)
            _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["void_light"],
                                     (tip_x, tip_y), max(1, cr - 4))
            _NS_nazulmor._aacircle(surface, _NS_nazulmor.PALETTE["void_shine"],
                                     (tip_x, tip_y), max(1, cr - 6))

            # Swirl sparks.
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = tip_x + int(math.cos(angle) * (cr + 3))
                sy = tip_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface,
                    _NS_nazulmor.PALETTE["void_hot"], (sx, sy, 1, 1))
        else:
            # Vortex projectile flight.
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 34
            start_y = y - 30
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Vortex trail with SWIRLING water rings.
            for i in range(11):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_nazulmor._alpha(240 - i * 22)

                size = max(1, 9 - i)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_darkest"], alpha),
                    (px, py), size)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                    (px, py), max(1, size - 1))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["water_mid"], alpha),
                    (px, py), max(1, size - 2))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["water_light"], alpha),
                    (px, py), max(1, size - 3))

                # Swirling water spirals.
                if i < 5:
                    for s in range(4):
                        angle_s = t * 10 + i + s * math.pi / 2
                        spark_x = px + int(math.sin(angle_s) * (size + 2))
                        spark_y = py + int(math.cos(angle_s) * (size + 2))
                        pygame.draw.rect(surface,
                            (*_NS_nazulmor.PALETTE["water_foam"], alpha),
                            (spark_x, spark_y, 1, 1))

            # Big vortex head.
            for r in range(15, 3, -2):
                alpha = _NS_nazulmor._alpha(100 * (15 - r) / 15)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_light"], alpha),
                    (bx, by), r)
            _NS_nazulmor._aacircle(surface,
                _NS_nazulmor.PALETTE["void_darkest"], (bx, by), 10)
            _NS_nazulmor._aacircle(surface,
                _NS_nazulmor.PALETTE["void_dark"], (bx, by), 8)
            _NS_nazulmor._aacircle(surface,
                _NS_nazulmor.PALETTE["water_mid"], (bx, by), 5)
            _NS_nazulmor._aacircle(surface,
                _NS_nazulmor.PALETTE["water_light"], (bx, by), 3)
            _NS_nazulmor._aacircle(surface,
                _NS_nazulmor.PALETTE["void_shine"], (bx, by), 1)
            pygame.draw.rect(surface,
                _NS_nazulmor.PALETTE["white"], (bx, by, 1, 1))

            # Swirl bands around head.
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                sr = 12 + int(math.sin(phase * 3 + i) * 2)
                spx = bx + int(math.cos(angle) * sr)
                spy = by + int(math.sin(angle) * sr)
                pygame.draw.rect(surface,
                    _NS_nazulmor.PALETTE["water_foam"], (spx, spy, 1, 1))

            # Impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 32)
                alpha = _NS_nazulmor._alpha(240 * (1 - st))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_darkest"], alpha),
                    (tx, ty), radius + 4, 3)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                    (tx, ty), radius, 3)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["water_mid"], alpha),
                    (tx, ty), max(1, radius - 5), 2)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["water_light"], alpha),
                    (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                        (*_NS_nazulmor.PALETTE["water_foam"], alpha),
                        (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - AQUATIC SHIELD (dome around boss)
    # ============================================================
    def _draw_aquashield_ground(surface, boss, x, y, timer, phase):
        for i in range(2):
            r = int(30 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_nazulmor._alpha(200 - i * 60)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["void_mid"], alpha),
                (x, y + 40), r, 2)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["void_light"], alpha),
                (x, y + 40), r, 1)

    def _draw_aquashield_bubble(surface, boss, x, y, timer, phase):
        """Bubble shield around boss."""
        breath = math.sin(phase * 2) * 3
        r = 60 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multiple ring layers.
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            _NS_nazulmor._aacircle(bubble,
                (*_NS_nazulmor.PALETTE["water_dark"], alpha_val),
                center, r - i, thickness)
            _NS_nazulmor._aacircle(bubble,
                (*_NS_nazulmor.PALETTE["void_mid"], alpha_val),
                center, r - i - 1, 1)

        # Bubble highlights.
        for i in range(3):
            highlight_angle = -math.pi / 4 + i * 0.3
            hx = center[0] + int(math.cos(highlight_angle) * (r - 5))
            hy = center[1] + int(math.sin(highlight_angle) * (r - 5))
            _NS_nazulmor._aacircle(bubble,
                _NS_nazulmor.PALETTE["water_foam"], (hx, hy), 3 - i)

        # Rotating sparkles.
        for i in range(22):
            angle = phase * 1.5 + i * math.pi / 11
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble,
                _NS_nazulmor.PALETTE["void_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble,
                _NS_nazulmor.PALETTE["void_hot"], (sx, sy, 1, 1))

        # Shell segments (like giant clam).
        for i in range(-2, 3):
            angle = math.pi * 0.5 + i * 0.25
            seg_x1 = center[0] + int(math.cos(angle) * r)
            seg_y1 = center[1] + int(math.sin(angle) * r)
            seg_x2 = center[0] + int(math.cos(angle) * (r - 8))
            seg_y2 = center[1] + int(math.sin(angle) * (r - 8))
            pygame.draw.line(bubble,
                (*_NS_nazulmor.PALETTE["scale_mid"], 200),
                (seg_x1, seg_y1), (seg_x2, seg_y2), 2)
            pygame.draw.line(bubble,
                (*_NS_nazulmor.PALETTE["scale_light"], 200),
                (seg_x1, seg_y1), (seg_x2, seg_y2), 1)

        surface.blit(bubble, (x - r - 10, y - r - 10))

    # ============================================================
    # SKILL: E - TIDAL RAGE (rage aura + water columns)
    # ============================================================
    def _draw_tidalrage_ground(surface, boss, x, y, timer, phase):
        for i in range(3):
            r = int(35 + i * 5 + math.sin(phase * 3 + i) * 2)
            alpha = _NS_nazulmor._alpha(180 - i * 40)
            _NS_nazulmor._aacircle(surface,
                (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                (x, y + 40), r, 2)

    def _draw_tidalrage_foreground(surface, boss, x, y, timer, phase):
        """Rising water spouts around boss."""
        num_spouts = 6
        for i in range(num_spouts):
            angle = i * math.pi * 2 / num_spouts + phase * 0.2
            sx = x + int(math.cos(angle) * 45)
            sy_base = y + 40 + int(math.sin(angle) * 15)

            for layer in range(8):
                layer_t = (phase * 0.6 + i * 0.2 + layer * 0.12) % 1.0
                layer_y = sy_base - int(layer_t * 45)
                layer_alpha = _NS_nazulmor._alpha(200 * (1 - layer_t))
                layer_w = int(4 + layer_t * 3)
                layer_h = int(3 + layer_t * 2)

                pygame.draw.ellipse(surface,
                    (*_NS_nazulmor.PALETTE["water_dark"], layer_alpha),
                    (sx - layer_w, layer_y - layer_h,
                     layer_w * 2, layer_h * 2))
                pygame.draw.ellipse(surface,
                    (*_NS_nazulmor.PALETTE["water_mid"], layer_alpha),
                    (sx - layer_w + 1, layer_y - layer_h + 1,
                     layer_w * 2 - 2, layer_h * 2 - 2))
                pygame.draw.rect(surface,
                    (*_NS_nazulmor.PALETTE["water_light"], layer_alpha),
                    (sx, layer_y, 1, 1))
                pygame.draw.rect(surface,
                    (*_NS_nazulmor.PALETTE["water_foam"], layer_alpha),
                    (sx, layer_y - 1, 1, 1))

        # Aura sparks.
        for i in range(14):
            angle = i * math.pi / 7 + phase * 0.5
            sr = 42 + int(math.sin(phase * 2 + i) * 5)
            sx = x + int(math.cos(angle) * sr)
            sy = y + int(math.sin(angle) * sr * 0.6)
            pygame.draw.rect(surface,
                _NS_nazulmor.PALETTE["void_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                _NS_nazulmor.PALETTE["void_hot"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL: R - CHAOTIC RAGE (tidal wave + kraken tentacles)
    # ============================================================
    def _draw_chaotic_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nazulmor._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            t = progress / 0.3
            r = int(45 * t)
            alpha = _NS_nazulmor._alpha(180 * t)
            pygame.draw.ellipse(surface,
                (*_NS_nazulmor.PALETTE["void_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface,
                    _NS_nazulmor.PALETTE["void_light"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.3) / 0.7
            r = int(45 + t * 35)
            alpha = _NS_nazulmor._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                (*_NS_nazulmor.PALETTE["water_dark"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                (tx - r + 3, ty - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                (*_NS_nazulmor.PALETTE["water_mid"], alpha),
                (tx - r + 8, ty - r // 3 + 4,
                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_chaotic_foreground(surface, boss, x, y, timer, phase):
        """Tidal wave + KRAKEN TENTACLES rising (eldritch signature)."""
        tx, ty = _NS_nazulmor._target_position(boss, x, y)
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charge above target.
            t = progress / 0.3
            gather_y = ty - int((1 - t) * 70)
            gather_r = int(4 + t * 5)
            for r in range(gather_r + 3, 0, -1):
                alpha = _NS_nazulmor._alpha(180 * (gather_r + 3 - r) / (gather_r + 3))
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                    (tx, gather_y), r)
            _NS_nazulmor._aacircle(surface,
                _NS_nazulmor.PALETTE["void_light"],
                (tx, gather_y), gather_r - 2)
            pygame.draw.rect(surface,
                _NS_nazulmor.PALETTE["void_shine"],
                (tx, gather_y, 1, 1))
        elif progress < 0.7:
            # TIDAL WAVE + KRAKEN TENTACLES.
            t = (progress - 0.3) / 0.4
            intensity = math.sin(t * math.pi)

            # Tidal wave.
            wave_h = int(65 * t)
            wave_alpha = _NS_nazulmor._alpha(220 * intensity)

            wave_pts = []
            for i in range(20):
                wx = tx - 65 + i * 6
                wy = ty - int(math.sin(i / 20 * math.pi) * wave_h)
                wave_pts.append((wx, wy))
            wave_pts.append((tx + 65, ty + 20))
            wave_pts.append((tx - 65, ty + 20))

            wave_surf = pygame.Surface((170, 110), pygame.SRCALPHA)
            offset_x = tx - 85
            offset_y = ty - 85
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in wave_pts]

            _NS_nazulmor._poly(wave_surf,
                (*_NS_nazulmor.PALETTE["void_darkest"], wave_alpha),
                local_pts)
            inner_pts = []
            cx_l = sum(p[0] for p in local_pts) / len(local_pts)
            cy_l = sum(p[1] for p in local_pts) / len(local_pts)
            for p in local_pts:
                inner_pts.append(
                    (int(p[0] * 0.85 + cx_l * 0.15),
                     int(p[1] * 0.85 + cy_l * 0.15))
                )
            _NS_nazulmor._poly(wave_surf,
                (*_NS_nazulmor.PALETTE["water_dark"], wave_alpha),
                inner_pts)
            inner2 = []
            for p in local_pts:
                inner2.append(
                    (int(p[0] * 0.7 + cx_l * 0.3),
                     int(p[1] * 0.7 + cy_l * 0.3))
                )
            _NS_nazulmor._poly(wave_surf,
                (*_NS_nazulmor.PALETTE["water_mid"], wave_alpha),
                inner2)

            # Wave crest (foam).
            for i in range(0, 20, 2):
                wx = tx - 65 + i * 6 - offset_x
                wy = ty - int(math.sin(i / 20 * math.pi) * wave_h) - offset_y
                pygame.draw.rect(wave_surf,
                    (*_NS_nazulmor.PALETTE["water_foam"], wave_alpha),
                    (wx, wy, 2, 2))
                pygame.draw.rect(wave_surf,
                    (*_NS_nazulmor.PALETTE["void_light"], wave_alpha),
                    (wx, wy - 1, 1, 1))

            surface.blit(wave_surf, (offset_x, offset_y))

            # KRAKEN TENTACLES rising around boss (more + bigger for eldritch).
            for tent_i in range(7):
                base_angle = tent_i * math.pi * 2 / 7 + phase * 0.15
                base_x = x + int(math.cos(base_angle) * 35)
                base_y = y + 35

                prev = (base_x, base_y)
                seg_count = 10
                for seg in range(1, seg_count + 1):
                    seg_t = seg / seg_count
                    curve = math.sin(phase * 2 + tent_i + seg_t * 3) * 10
                    seg_x = base_x + int(math.cos(base_angle) * seg_t * 25 + curve)
                    seg_y = base_y - int(seg_t * 60 * intensity)
                    thickness = max(2, 10 - seg)

                    tent_alpha = _NS_nazulmor._alpha(230 * intensity)
                    _NS_nazulmor._aaline(surface,
                        (*_NS_nazulmor.PALETTE["shadow_deep"], tent_alpha),
                        (prev[0] + 1, prev[1] + 1),
                        (seg_x + 1, seg_y + 1), thickness + 1)
                    _NS_nazulmor._aaline(surface,
                        (*_NS_nazulmor.PALETTE["tent_darkest"], tent_alpha),
                        prev, (seg_x, seg_y), thickness)
                    _NS_nazulmor._aaline(surface,
                        (*_NS_nazulmor.PALETTE["tent_dark"], tent_alpha),
                        prev, (seg_x, seg_y), max(1, thickness - 1))
                    _NS_nazulmor._aaline(surface,
                        (*_NS_nazulmor.PALETTE["tent_mid"], tent_alpha),
                        prev, (seg_x, seg_y), max(1, thickness - 3))
                    # Suckers.
                    if seg % 2 == 0:
                        pygame.draw.rect(surface,
                            (*_NS_nazulmor.PALETTE["tent_light"], tent_alpha),
                            (seg_x - 1, seg_y, 1, 1))
                        pygame.draw.rect(surface,
                            (*_NS_nazulmor.PALETTE["tent_shine"], tent_alpha),
                            (seg_x - 1, seg_y, 1, 1))
                    prev = (seg_x, seg_y)

                # Tentacle tip.
                tip_alpha = _NS_nazulmor._alpha(220 * intensity)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["tent_mid"], tip_alpha),
                    prev, 3)
                _NS_nazulmor._aacircle(surface,
                    (*_NS_nazulmor.PALETTE["tent_light"], tip_alpha),
                    prev, 2)
                pygame.draw.rect(surface,
                    (*_NS_nazulmor.PALETTE["tent_shine"], tip_alpha),
                    (prev[0], prev[1], 1, 1))
        else:
            # Aftermath: settling mist + tentacles retreating.
            t = (progress - 0.7) / 0.3
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 35)
                ry = ty - int(rise_t * 40)
                alpha = _NS_nazulmor._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_nazulmor._aacircle(surface,
                        (*_NS_nazulmor.PALETTE["void_dark"], alpha),
                        (rx, ry), 3)
                    _NS_nazulmor._aacircle(surface,
                        (*_NS_nazulmor.PALETTE["water_mid"], alpha),
                        (rx, ry), 2)
                    pygame.draw.rect(surface,
                        (*_NS_nazulmor.PALETTE["void_light"], alpha),
                        (rx, ry, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_aurelix(surface, boss, x, y):
    """Entry point aurelix."""
    return _NS_aurelix.draw_aurelix(surface, boss, x, y)


def draw_aurelyssa(surface, boss, x, y):
    """Entry point aurelyssa."""
    return _NS_aurelyssa.draw_aurelyssa(surface, boss, x, y)


def draw_vargrath(surface, boss, x, y):
    """Entry point vargrath."""
    return _NS_vargrath.draw_vargrath(surface, boss, x, y)


def draw_nazulmor(surface, boss, x, y):
    """Entry point nazulmor."""
    return _NS_nazulmor.draw_nazulmor(surface, boss, x, y)
