"""
heroes/_bundle.py - semua renderer hero

Gabungan dari 6 file:
  - grimjaw.py               namespace _NS_grimjaw
  - sylara.py                namespace _NS_sylara
  - kaizen.py                namespace _NS_kaizen
  - thorne.py                namespace _NS_thorne
  - vex.py                   namespace _NS_vex
  - zephyr.py                namespace _NS_zephyr

Modul dibungkus kelas `_NS_<nama>` supaya simbol bernama
sama tidak saling menimpa.
PALETTE, draw_boss, _draw_torso, _poly dan 24 simbol
lain ada di keenam file dengan isi BERBEDA.

File asli dihapus; nama submodul didaftarkan ke
sys.modules oleh __init__.py, jadi semua baris
`from heroes.<modul> import ...` tetap jalan.
"""
import math
import random
import pygame


# ====================================================================
# grimjaw.py
# ====================================================================
class _NS_grimjaw:
    """Namespace grimjaw - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")


    # ---------------------------------------------------------------------------
    # HD Color Palette - Juggernaut inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin (light tanned)
        "skin_darkest":   (100, 65, 45),
        "skin_dark":      (150, 100, 70),
        "skin_mid":       (200, 150, 110),
        "skin_light":     (230, 185, 145),
        "skin_high":      (250, 210, 175),

        # Hair (bright orange messy - signature)
        "hair_darkest":   (95, 45, 15),
        "hair_dark":      (155, 80, 25),
        "hair_mid":       (210, 125, 40),
        "hair_light":     (240, 170, 65),
        "hair_high":      (255, 205, 100),

        # MASK (WHITE with dark shadow)
        "mask_shadow":    (130, 125, 115),
        "mask_dark":      (185, 180, 170),
        "mask_mid":       (225, 220, 205),
        "mask_light":     (245, 243, 230),
        "mask_shine":     (255, 255, 250),

        # BLOOD STRIPES (bright red)
        "blood_darkest":  (95, 12, 12),
        "blood_dark":     (150, 22, 22),
        "blood_mid":      (205, 38, 38),
        "blood_light":    (245, 68, 68),
        "blood_bright":   (255, 110, 110),

        # Armor (dark brown leather)
        "armor_darkest":  (35, 20, 12),
        "armor_dark":     (70, 40, 22),
        "armor_mid":      (115, 68, 38),
        "armor_light":    (165, 105, 60),
        "armor_high":     (210, 150, 90),

        # Red cloth (loincloth / center panel)
        "red_darkest":    (65, 15, 18),
        "red_dark":       (110, 22, 28),
        "red_mid":        (165, 38, 42),
        "red_light":      (210, 62, 68),
        "red_bright":     (245, 100, 105),

        # Gold trim
        "gold_darkest":   (75, 45, 12),
        "gold_dark":      (135, 90, 22),
        "gold_mid":       (200, 150, 45),
        "gold_light":     (240, 200, 90),
        "gold_shine":     (255, 235, 150),

        # Metal (dark bronze / steel)
        "metal_darkest":  (25, 20, 25),
        "metal_dark":     (55, 50, 55),
        "metal_mid":      (105, 95, 100),
        "metal_light":    (165, 155, 160),
        "metal_shine":    (220, 215, 220),

        # FIRE SWORD (glowing orange - signature)
        "fire_darkest":   (85, 18, 5),
        "fire_dark":      (165, 42, 12),
        "fire_mid":       (235, 105, 22),
        "fire_light":     (250, 175, 55),
        "fire_hot":       (255, 230, 125),
        "fire_core":      (255, 250, 235),

        # Healing (green - Healing Ward)
        "heal_darkest":   (20, 60, 25),
        "heal_dark":      (50, 135, 60),
        "heal_mid":       (105, 215, 115),
        "heal_light":     (165, 250, 175),
        "heal_core":      (235, 255, 235),

        # Misc
        "shadow":         (0, 0, 0),
        "shadow_deep":    (5, 3, 8),
        "white":          (255, 255, 255),
        "eye_glow":       (255, 45, 45),
        "dark_eye":       (25, 5, 10),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grimjaw._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_grimjaw.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_grimjaw._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_grimjaw._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_grimjaw._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(hero, x, y):
        target = getattr(hero, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_grimjaw._world_to_local(hero, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(hero, "_render_scale", None)
        dist = 60 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(hero, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # State detection helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(hero):
        if not hasattr(hero, "_gj_last_x"):
            hero._gj_last_x = hero.x
            hero._gj_last_y = hero.y
            return False
        dx = abs(hero.x - hero._gj_last_x)
        dy = abs(hero.y - hero._gj_last_y)
        hero._gj_last_x = hero.x
        hero._gj_last_y = hero.y
        moving = dx + dy > 0.3
        hero._moving_cached = moving
        return moving


    def _update_attack_anim(hero):
        """Track melee attack animation timeline."""
        cooldown = max(2, int(getattr(hero, "attack_cooldown", 40)))
        timer = int(getattr(hero, "timer", 0))
        previous = int(getattr(hero, "_gj_prev_timer", -1))
        active = bool(getattr(hero, "_gj_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            hero._gj_attack_active = True
            hero._gj_crit_active = random.random() < 0.25
            active = True

        if active and timer <= 0:
            hero._gj_attack_active = False
            hero._gj_crit_active = False
            active = False

        hero._gj_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        hero._gj_attack_frame = max(0, cooldown - timer) if active else 0
        hero._gj_attack_progress = (
            min(1.0, hero._gj_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_grimjaw(surface, hero, x, y):
        """Entry point for Hero.draw()."""
        pulse = float(getattr(hero, "pulse", 0.0))
        active_skill = getattr(hero, "active_skill", None)
        skill_timer = int(getattr(hero, "active_skill_timer", 0))
        moving = _NS_grimjaw._detect_moving(hero)
        _NS_grimjaw._update_attack_anim(hero)

        attacking = (
            getattr(hero, "_gj_attack_active", False)
            or getattr(hero, "timer", 0) > getattr(hero, "attack_cooldown", 40) - 15
        )

        # Q = Blade Fury, W = Healing Ward, E = Critical Strike, R = Omnislash
        # (sesuai hero_skills/grimjaw_skills.py)
        is_blade_fury = active_skill == "q"
        is_healing_ward = active_skill == "w"
        is_omnislash = active_skill == "r"

        # ---------- Background layers ----------
        _NS_grimjaw._draw_fire_aura(surface, x, y, pulse)
        _NS_grimjaw._draw_fire_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Healing Ward effect (background) ----------
        if is_healing_ward:
            _NS_grimjaw._draw_healing_ward_ground(surface, hero, x, y, skill_timer, pulse)

        # ---------- Omnislash effect (background sparks) ----------
        if is_omnislash:
            _NS_grimjaw._draw_omnislash_ground(surface, hero, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if is_blade_fury:
            _NS_grimjaw._draw_grimjaw_blade_fury(surface, hero, x, y, skill_timer, pulse)
        elif is_omnislash:
            _NS_grimjaw._draw_grimjaw_omnislash(surface, hero, x, y, skill_timer, pulse)
        elif attacking:
            _NS_grimjaw._draw_grimjaw_attack(surface, hero, x, y)
        elif moving:
            _NS_grimjaw._draw_grimjaw_walk(surface, hero, x, y)
        else:
            _NS_grimjaw._draw_grimjaw_idle(surface, hero, x, y)

        # ---------- Skill foreground effects ----------
        if is_blade_fury:
            _NS_grimjaw._draw_blade_fury_rings(surface, x, y + 20, pulse)
            _NS_grimjaw._draw_fire_particles_orbit(surface, x, y, pulse)

        if is_healing_ward:
            _NS_grimjaw._draw_healing_ward_totem(surface, hero, x, y, skill_timer, pulse)
            _NS_grimjaw._draw_heal_aura(surface, x, y, pulse)

        if is_omnislash:
            _NS_grimjaw._draw_omnislash_slashes(surface, hero, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_grimjaw_idle(surface, hero, x, y):
        bob = int(math.sin(hero.pulse * 0.7) * 2)
        _NS_grimjaw._draw_shadow(surface, x, y + 48)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 35, hero.pulse)
        _NS_grimjaw._draw_grimjaw_body(surface, x, y + bob, hero.direction, hero.pulse, "idle")


    def _draw_grimjaw_walk(surface, hero, x, y):
        phase = hero.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_grimjaw._draw_shadow(surface, x + sway, y + 48)
        _NS_grimjaw._draw_fire_mist(surface, x + sway, y + 35, phase, trail=True,
                        facing=hero.direction)
        _NS_grimjaw._draw_grimjaw_body(surface, x + sway, y - bob, hero.direction, phase, "walk")


    def _draw_grimjaw_attack(surface, hero, x, y):
        progress = getattr(hero, "_gj_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        crit = getattr(hero, "_gj_crit_active", False)

        # Body lunge forward
        lunge = int(math.sin(progress * math.pi) * 4) * hero.direction

        _NS_grimjaw._draw_shadow(surface, x + lunge, y + 48)
        _NS_grimjaw._draw_fire_mist(surface, x + lunge, y + 35, hero.pulse, intense=True)
        _NS_grimjaw._draw_grimjaw_body(surface, x + lunge, y, hero.direction, hero.pulse,
                           "attack", progress)

        # Fire slash arc
        _NS_grimjaw._draw_fire_slash_arc(surface, x + lunge, y, hero.direction, progress, crit)

        # Critical strike burst
        if crit and 0.5 < progress < 0.7:
            _NS_grimjaw._draw_critical_strike_burst(surface, x + lunge, y, hero.direction,
                                        progress)


    def _draw_grimjaw_blade_fury(surface, hero, x, y, timer, phase):
        """Blade Fury - spinning with fire rings."""
        spin_phase = phase * 6
        bob = int(math.sin(spin_phase) * -1)
        # Direction flips rapidly to simulate spinning
        facing = 1 if int(spin_phase * 2) % 2 == 0 else -1

        _NS_grimjaw._draw_shadow(surface, x, y + 48)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 35, phase * 2, intense=True)
        _NS_grimjaw._draw_grimjaw_body(surface, x, y + bob, facing, phase, "spin",
                           spin_phase=spin_phase)


    def _draw_grimjaw_omnislash(surface, hero, x, y, timer, phase):
        """Omnislash - hero teleports rapidly with dramatic pose."""
        # Body flickers between poses
        flicker_phase = phase * 8
        offset_x = int(math.sin(flicker_phase) * 3)
        offset_y = int(math.cos(flicker_phase * 1.3) * 2)

        _NS_grimjaw._draw_shadow(surface, x, y + 48)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 35, phase, intense=True)

        # Draw ghost trails behind current position
        for i in range(3):
            ghost_alpha = 60 + i * 30
            gx = x - int(math.sin(flicker_phase - i * 0.5) * 15)
            gy = y + int(math.cos(flicker_phase - i * 0.5) * 5)
            _NS_grimjaw._draw_grimjaw_ghost(surface, gx, gy, hero.direction, phase,
                                ghost_alpha)

        # Main body (with attack pose)
        _NS_grimjaw._draw_grimjaw_body(surface, x + offset_x, y + offset_y, hero.direction,
                           phase, "attack", 0.6)


    def _draw_grimjaw_ghost(surface, cx, cy, facing, phase, alpha):
        """Draw a ghosted version of Grimjaw for omnislash trail."""
        # Simple ghost silhouette (just torso + head + sword)
        ghost = pygame.Surface((60, 100), pygame.SRCALPHA)

        # Torso silhouette
        _NS_grimjaw._rect(ghost, (*_NS_grimjaw.PALETTE["fire_dark"], alpha),
              (20, 40, 20, 25), border_radius=4)
        # Head silhouette
        _NS_grimjaw._rect(ghost, (*_NS_grimjaw.PALETTE["fire_mid"], alpha),
              (23, 20, 14, 18), border_radius=4)
        # Sword silhouette (extended)
        _NS_grimjaw._aaline(ghost, (*_NS_grimjaw.PALETTE["fire_light"], alpha),
                (30 + facing * 15, 50), (30 + facing * 30, 40), 3)

        surface.blit(ghost, (cx - 30, cy - 50))


    # ===================================================================
    # BODY RENDERING - HD detailed Juggernaut
    # ===================================================================
    def _draw_grimjaw_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0, spin_phase=0):
        """Full warrior body render."""
        # Body sway
        if action == "walk":
            body_sway = int(math.sin(phase * 2) * 1)
            head_bob = int(math.sin(phase * 2 + math.pi / 4) * 1)
        elif action in ("attack", "spin"):
            body_sway = 0
            head_bob = 0
        else:
            body_sway = int(math.sin(phase * 0.5) * 1)
            head_bob = int(math.sin(phase * 0.6) * 1)

        bx = cx + body_sway

        # Draw order: back to front
        # 1. Back hair
        _NS_grimjaw._draw_hair_back(surface, bx, cy - 22 + head_bob, facing, phase, action)
        # 2. Lower body (flowing red loincloth - no legs, floating style)
        _NS_grimjaw._draw_lower_body_flowing(surface, bx, cy + 14, facing, phase, action)
        # 3. Torso with armor
        _NS_grimjaw._draw_torso(surface, bx, cy - 3, facing, phase)
        # 4. Pauldrons
        _NS_grimjaw._draw_pauldrons(surface, bx, cy - 8 + head_bob, facing)
        # 5. Head with mask
        _NS_grimjaw._draw_head_mask(surface, bx, cy - 22 + head_bob, facing,
                        is_attacking=(action in ("attack", "spin")))
        # 6. Front hair
        _NS_grimjaw._draw_hair_front(surface, bx, cy - 22 + head_bob, facing, phase, action)
        # 7. Left arm (empty)
        _NS_grimjaw._draw_left_arm(surface, bx, cy + head_bob, facing, phase, action)
        # 8. Right arm + sword (front)
        _NS_grimjaw._draw_sword_arm(surface, bx, cy + head_bob, facing, phase, action,
                        attack_progress, spin_phase)


    # ═══════════════════════════════════════════════════════
    # LOWER BODY (Red loincloth flowing - floating style)
    # ═══════════════════════════════════════════════════════

    def _draw_lower_body_flowing(surface, cx, cy, facing, phase, action):
        """Red flowing loincloth with V-panel armor."""
        sway1 = int(math.sin(phase * 0.7) * 2)
        sway2 = int(math.sin(phase * 0.9 + 1) * 2)

        # Skirt shape
        lower_pts = [
            (cx - 11, cy - 2),
            (cx + 11, cy - 2),
            (cx + 13, cy + 5),
            (cx + 12 + sway1, cy + 12),
            (cx + 8 + sway2, cy + 17),
            (cx + 4 + sway1, cy + 19),
            (cx + 2 + sway2, cy + 18),
            (cx - 2 + sway1, cy + 18),
            (cx - 4 + sway2, cy + 19),
            (cx - 8 + sway1, cy + 17),
            (cx - 12 + sway2, cy + 12),
            (cx - 13, cy + 5),
        ]

        # Shadow
        shadow_pts = [(p[0] + 2, p[1] + 2) for p in lower_pts]
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["shadow_deep"], shadow_pts)

        # Red loincloth layers
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["red_darkest"], lower_pts)
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["red_dark"], [
            (cx - 10, cy - 1),
            (cx + 10, cy - 1),
            (cx + 12, cy + 5),
            (cx + 11 + sway1, cy + 12),
            (cx + 7 + sway2, cy + 16),
            (cx - 7 + sway1, cy + 16),
            (cx - 11 + sway2, cy + 12),
            (cx - 12, cy + 5),
        ])
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["red_mid"], [
            (cx - 9, cy),
            (cx + 9, cy),
            (cx + 11, cy + 5),
            (cx + 9, cy + 12),
            (cx + 4, cy + 15),
            (cx - 4, cy + 15),
            (cx - 9, cy + 12),
            (cx - 11, cy + 5),
        ])

        # Center V-panel armor (brown leather)
        v_panel_pts = [
            (cx - 4, cy - 1),
            (cx + 4, cy - 1),
            (cx + 3, cy + 12),
            (cx, cy + 15),
            (cx - 3, cy + 12),
        ]
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_darkest"], v_panel_pts)
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_dark"], [
            (cx - 3, cy),
            (cx + 3, cy),
            (cx + 2, cy + 11),
            (cx, cy + 14),
            (cx - 2, cy + 11),
        ])
        _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_mid"], [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx + 1, cy + 10),
            (cx, cy + 12),
            (cx - 1, cy + 10),
        ])

        # Gold trim on V-panel edges
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_dark"],
                (cx - 4, cy - 1), (cx, cy + 15), 1)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_dark"],
                (cx + 4, cy - 1), (cx, cy + 15), 1)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_mid"],
                (cx - 3, cy), (cx, cy + 13), 1)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_mid"],
                (cx + 3, cy), (cx, cy + 13), 1)

        # Fabric folds
        for fold_x_off in [-8, -3, 3, 8]:
            fold_x = cx + fold_x_off
            wave_offset = sway1 if fold_x_off < 0 else sway2
            _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["red_darkest"],
                    (fold_x, cy),
                    (fold_x + wave_offset // 2, cy + 14), 1)

        # Gold accents at bottom (tatter positions)
        for tx_off, tw in [(-9, sway1), (-5, sway2), (0, sway1),
                            (5, sway2), (9, sway1)]:
            tty = cy + 16
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_dark"], (cx + tx_off + tw, tty, 2, 2))
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_mid"], (cx + tx_off + tw, tty, 1, 1))


    # ═══════════════════════════════════════════════════════
    # TORSO
    # ═══════════════════════════════════════════════════════

    def _draw_torso(surface, cx, cy, facing, phase):
        """Armored torso with red center panel."""
        body_w = 22
        body_h = 24

        # Shadow
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["shadow_deep"],
              (cx - body_w // 2 + 2, cy + 2, body_w, body_h),
              border_radius=3)

        # Armor base (dark brown layers)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_darkest"],
              (cx - body_w // 2, cy, body_w, body_h), border_radius=3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_dark"],
              (cx - body_w // 2, cy, body_w - 1, body_h - 2), border_radius=3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_mid"],
              (cx - body_w // 2, cy, body_w - 2, body_h - 4), border_radius=3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_light"],
              (cx - body_w // 2, cy, body_w // 2, body_h // 3), border_radius=3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_high"],
              (cx - body_w // 2, cy, 5, 4), border_radius=2)

        # Center RED panel (vertical stripe)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["red_darkest"],
              (cx - 3, cy + 2, 7, body_h - 6))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["red_dark"],
              (cx - 3, cy + 2, 6, body_h - 7))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["red_mid"],
              (cx - 3, cy + 2, 5, body_h - 8))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["red_light"],
              (cx - 3, cy + 2, 3, body_h - 10))

        # Gold trim border on red panel
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_dark"],
                (cx - 3, cy + 2), (cx - 3, cy + body_h - 5), 1)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_dark"],
                (cx + 4, cy + 2), (cx + 4, cy + body_h - 5), 1)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_mid"],
                (cx - 3, cy + 2), (cx + 4, cy + 2), 1)

        # Shoulder straps (diagonal armor pieces)
        for side in (-1, 1):
            strap_pts = [
                (cx + side * (body_w // 2 - 1), cy + 2),
                (cx + side * (body_w // 2 - 1), cy + 9),
                (cx + side * 3, cy + 11),
                (cx + side * 3, cy + 4),
            ]
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_darkest"], strap_pts)
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_dark"], [
                (cx + side * (body_w // 2 - 2), cy + 3),
                (cx + side * (body_w // 2 - 2), cy + 8),
                (cx + side * 3, cy + 10),
                (cx + side * 3, cy + 5),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_mid"], [
                (cx + side * (body_w // 2 - 3), cy + 4),
                (cx + side * (body_w // 2 - 3), cy + 7),
                (cx + side * 3, cy + 9),
                (cx + side * 3, cy + 6),
            ])
            # Gold buckle on strap
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["gold_dark"],
                      (cx + side * 6, cy + 6), 2)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["gold_mid"],
                      (cx + side * 6, cy + 6), 1)

        # Belt (thick leather at bottom)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_darkest"],
              (cx - body_w // 2, cy + body_h - 5, body_w, 5))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_dark"],
              (cx - body_w // 2, cy + body_h - 5, body_w - 1, 4))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_mid"],
              (cx - body_w // 2, cy + body_h - 5, body_w - 2, 2))

        # Big gold belt buckle
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_darkest"],
              (cx - 4, cy + body_h - 6, 8, 7), border_radius=1)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_dark"],
              (cx - 4, cy + body_h - 6, 7, 6))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_mid"],
              (cx - 4, cy + body_h - 6, 7, 4))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_light"],
              (cx - 4, cy + body_h - 6, 4, 3))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_shine"],
              (cx - 4, cy + body_h - 6, 1, 1))

        # Center emblem on buckle
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_dark"], (cx, cy + body_h - 4, 1, 3))


    # ═══════════════════════════════════════════════════════
    # PAULDRONS (Spiked shoulder armor)
    # ═══════════════════════════════════════════════════════

    def _draw_pauldrons(surface, cx, cy, facing):
        """Shoulder pauldrons with metal spikes."""
        for side in (-1, 1):
            sx = cx + side * 12
            sy = cy + 2

            pauldron_pts = [
                (sx - 4, sy),
                (sx + 4, sy),
                (sx + 4, sy + 7),
                (sx, sy + 9),
                (sx - 4, sy + 7),
            ]
            # Shadow
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["shadow_deep"],
                  [(p[0] + 1, p[1] + 1) for p in pauldron_pts])
            # Armor layers
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_darkest"], pauldron_pts)
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_dark"], [
                (sx - 3, sy + 1),
                (sx + 3, sy + 1),
                (sx + 3, sy + 6),
                (sx, sy + 8),
                (sx - 3, sy + 6),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["armor_mid"], [
                (sx - 3, sy + 1),
                (sx + 1, sy + 1),
                (sx, sy + 6),
                (sx - 3, sy + 5),
            ])
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_high"],
                  (sx - 3, sy + 1, 2, 1))

            # Gold trim bottom
            _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_mid"],
                    (sx - 4, sy + 7), (sx + 4, sy + 7), 1)
            _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_light"],
                    (sx - 4, sy + 7), (sx, sy + 7), 1)

            # Metal spike on top
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["shadow_deep"], [
                (sx - 2, sy + 1),
                (sx, sy - 6),
                (sx + 2, sy + 1),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["metal_darkest"], [
                (sx - 2, sy),
                (sx, sy - 6),
                (sx + 2, sy),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["metal_dark"], [
                (sx - 1, sy),
                (sx, sy - 5),
                (sx + 1, sy),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["metal_mid"], [
                (sx - 1, sy),
                (sx, sy - 4),
                (sx, sy),
            ])
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["metal_shine"], (sx, sy - 4, 1, 2))
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["white"], (sx, sy - 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # HEAD + WHITE MASK with 3 blood stripes
    # ═══════════════════════════════════════════════════════

    def _draw_head_mask(surface, cx, cy, facing, is_attacking=False):
        """White Juggernaut mask with 3 blood stripes."""
        # Neck
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["skin_darkest"], (cx - 2, cy + 16, 4, 4))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["skin_dark"], (cx - 2, cy + 16, 3, 3))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["skin_mid"], (cx - 2, cy + 16, 2, 2))

        # MASK BASE (rounded rectangle - white)
        mask_x = cx - 7
        mask_y = cy
        mask_w = 14
        mask_h = 18

        # Shadow
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_shadow"],
              (mask_x + 1, mask_y + 1, mask_w, mask_h), border_radius=4)

        # Multi-layer white mask
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_shadow"],
              (mask_x, mask_y, mask_w, mask_h), border_radius=4)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_dark"],
              (mask_x, mask_y, mask_w - 1, mask_h - 1), border_radius=4)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_mid"],
              (mask_x, mask_y, mask_w - 2, mask_h - 3), border_radius=3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_light"],
              (mask_x + 1, mask_y, mask_w - 4, mask_h - 8), border_radius=3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_shine"],
              (mask_x + 1, mask_y, 5, 6), border_radius=2)

        # ═══ 3 BLOOD STRIPES (LEFT + CENTER + RIGHT) ═══
        # LEFT stripe (thin)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_darkest"], (cx - 5, cy + 1, 2, 14))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_dark"], (cx - 5, cy + 1, 2, 12))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_mid"], (cx - 5, cy + 1, 1, 10))

        # CENTER stripe (thickest, main feature)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_darkest"], (cx - 1, cy + 1, 3, 15))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_dark"], (cx - 1, cy + 1, 3, 13))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_mid"], (cx - 1, cy + 1, 2, 11))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_light"], (cx - 1, cy + 1, 1, 8))

        # RIGHT stripe (medium)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_darkest"], (cx + 3, cy + 1, 2, 14))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_dark"], (cx + 3, cy + 1, 2, 12))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_mid"], (cx + 3, cy + 1, 1, 10))

        # Blood drips at bottom
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_dark"], (cx, cy + 15, 1, 2))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["blood_mid"], (cx + 3, cy + 14, 1, 1))

        # ═══ EYE HOLES (dark cutouts) ═══
        for eye_x_off in (-5, 3):
            eye_x = cx + eye_x_off
            eye_y = cy + 6
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["dark_eye"], (eye_x, eye_y, 3, 3))

        # ═══ GLOWING RED EYES ═══
        if is_attacking:
            for eye_x_off in (-5, 3):
                eye_x = cx + eye_x_off
                eye_y = cy + 6
                _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["eye_glow"], (eye_x, eye_y, 3, 3))
                _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["white"], (eye_x, eye_y, 2, 2))
                _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["fire_core"], (eye_x, eye_y, 1, 1))

            # Glow aura behind eyes
            glow_surf = pygame.Surface((26, 12), pygame.SRCALPHA)
            for r in range(6, 0, -1):
                alpha = min(255, max(0, 180 - r * 25))
                _NS_grimjaw._aacircle(glow_surf, (255, 30, 30, alpha), (6, 6), r)
                _NS_grimjaw._aacircle(glow_surf, (255, 30, 30, alpha), (20, 6), r)
            surface.blit(glow_surf, (cx - 13, cy + 4))
        else:
            for eye_x_off in (-4, 4):
                eye_x = cx + eye_x_off
                eye_y = cy + 7
                _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["eye_glow"], (eye_x, eye_y, 1, 1))
                _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["white"], (eye_x, eye_y, 1, 1))

        # ═══ NOSE (small) ═══
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_shadow"], (cx, cy + 9, 1, 2))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["dark_eye"], (cx, cy + 11, 1, 1))

        # ═══ MOUTH (teeth grille) ═══
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["shadow"], (cx - 3, cy + 12, 6, 3))
        for tooth_x in (-3, -1, 1, 3):
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_light"],
                  (cx + tooth_x, cy + 12, 1, 2))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["mask_shadow"], (cx - 3, cy + 14, 6, 1))


    # ═══════════════════════════════════════════════════════
    # HAIR (Orange messy - back + front)
    # ═══════════════════════════════════════════════════════

    def _draw_hair_back(surface, cx, cy, facing, phase, action):
        """Wild hair strands going back."""
        wave_int = 3 if action in ("walk", "attack", "spin") else 1

        strand_configs = [
            (-7, 2, 12, -0.4),
            (-5, 4, 14, -0.2),
            (-2, 6, 16, 0),   # center longest
            (0, 7, 15, 0.1),
            (2, 6, 14, 0.2),
            (5, 4, 12, 0.3),
            (7, 2, 10, 0.4),
        ]

        for x_off, y_off, length, angle_off in strand_configs:
            wave = int(math.sin(phase * 0.8 + x_off * 0.3) * wave_int)

            strand_x = cx + x_off
            strand_y = cy + y_off

            tip_x = strand_x + int(math.sin(angle_off) * length) - facing * 2
            tip_y = strand_y + length + wave

            # Shadow
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["shadow_deep"], [
                (strand_x - 2, strand_y + 1),
                (tip_x, tip_y + 1),
                (strand_x + 2, strand_y + 1),
            ])
            # Hair layers
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_darkest"], [
                (strand_x - 2, strand_y),
                (tip_x, tip_y),
                (strand_x + 2, strand_y),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_dark"], [
                (strand_x - 1, strand_y),
                (tip_x, tip_y),
                (strand_x + 1, strand_y),
            ])
            # Highlight
            if length >= 12:
                _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["hair_mid"],
                        (strand_x, strand_y), (tip_x, tip_y), 1)


    def _draw_hair_front(surface, cx, cy, facing, phase, action):
        """Front hair spikes/tufts around mask."""
        wave_int = 2 if action in ("walk", "attack", "spin") else 1
        wave = int(math.sin(phase * 0.6) * wave_int)

        # Top tufts (above mask)
        tuft_configs = [
            (-6, -2, 5),
            (-3, -5, 6),
            (1, -5, 6),
            (5, -2, 5),
        ]

        for x_off, y_off, height in tuft_configs:
            tx = cx + x_off + wave
            ty = cy + y_off

            # Shadow
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["shadow_deep"], [
                (tx - 2, cy),
                (tx, ty - height),
                (tx + 2, cy),
            ])

            # Hair layers
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_darkest"], [
                (tx - 2, cy - 1),
                (tx, ty - height),
                (tx + 2, cy - 1),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_dark"], [
                (tx - 1, cy - 1),
                (tx, ty - height),
                (tx + 1, cy - 1),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_mid"], [
                (tx, cy - 1),
                (tx, ty - height + 1),
                (tx + 1, cy - 1),
            ])

            # Bright tip
            if height >= 5:
                _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["hair_light"],
                      (tx, ty - height + 1, 1, 2))

        # Side tufts around mask
        for side in (-1, 1):
            tuft_x = cx + side * 8
            tuft_y = cy + 5

            tuft_pts = [
                (tuft_x, tuft_y),
                (tuft_x - side * 2, tuft_y + 6),
                (tuft_x + side * 2, tuft_y + 3),
            ]
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_darkest"], tuft_pts)
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_dark"], [
                (tuft_x, tuft_y),
                (tuft_x - side, tuft_y + 5),
                (tuft_x + side * 2, tuft_y + 3),
            ])
            _NS_grimjaw._poly(surface, _NS_grimjaw.PALETTE["hair_mid"], [
                (tuft_x + side, tuft_y),
                (tuft_x, tuft_y + 4),
                (tuft_x + side * 2, tuft_y + 2),
            ])


    # ═══════════════════════════════════════════════════════
    # ARMS + FIRE SWORD
    # ═══════════════════════════════════════════════════════

    def _draw_sword_arm(surface, cx, cy, facing, phase, action,
                        attack_progress=0, spin_phase=0):
        """Right arm holding fire sword with full swing animation."""

        if action == "attack":
            # Windup → swing → recovery
            if attack_progress < 0.25:
                t = attack_progress / 0.25
                t = 1 - (1 - t) ** 2
                swing = math.pi / 8 - t * math.pi * 0.7
            elif attack_progress < 0.7:
                t = (attack_progress - 0.25) / 0.45
                t = t ** 1.5
                swing = math.pi / 8 - math.pi * 0.7 + t * math.pi * 1.2
            else:
                swing = math.pi / 8 - math.pi * 0.7 + math.pi * 1.2

        elif action == "spin":
            swing = spin_phase * 0.5

        elif action == "walk":
            swing = math.pi / 6 + math.sin(phase * 2) * 0.15
        else:
            # Idle - sword held down at side
            swing = math.pi / 4 + math.sin(phase * 0.5) * 0.05

        # Shoulder position
        shoulder_x = cx + 10 * facing
        shoulder_y = cy - 3

        arm_length = 12
        hand_x = shoulder_x + int(math.cos(swing) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing) * arm_length) + 3

        # Elbow
        elbow_x = (shoulder_x + hand_x) // 2 + int(math.cos(swing + 0.3) * 2) * facing
        elbow_y = (shoulder_y + hand_y) // 2

        # Upper arm (skin)
        _NS_grimjaw._draw_muscular_arm(surface, shoulder_x, shoulder_y, elbow_x, elbow_y)
        _NS_grimjaw._draw_muscular_arm(surface, elbow_x, elbow_y, hand_x, hand_y)

        # Bracer
        bracer_x = int(shoulder_x + (hand_x - shoulder_x) * 0.75)
        bracer_y = int(shoulder_y + (hand_y - shoulder_y) * 0.75)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_darkest"], (bracer_x, bracer_y), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_dark"], (bracer_x, bracer_y), 3)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_mid"], (bracer_x - 1, bracer_y - 1), 2)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["gold_mid"], (bracer_x, bracer_y), 1)

        # Fist
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["shadow"], (hand_x + 1, hand_y + 1), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["skin_darkest"], (hand_x, hand_y), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["skin_dark"], (hand_x, hand_y), 3)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["skin_mid"], (hand_x - 1, hand_y - 1), 2)

        # Fire sword
        _NS_grimjaw._draw_fire_sword(surface, hand_x, hand_y, swing, facing, phase, action)


    def _draw_left_arm(surface, cx, cy, facing, phase, action):
        """Left arm - empty fist."""
        if action == "walk":
            swing = math.pi / 2 + math.sin(phase * 2 + math.pi) * 0.15
        elif action == "attack":
            swing = math.pi / 2 - 0.2  # forward for balance
        else:
            swing = math.pi / 2 + math.sin(phase * 0.5) * 0.03

        shoulder_x = cx - 10 * facing
        shoulder_y = cy - 3

        arm_length = 12
        hand_x = shoulder_x + int(math.cos(swing) * arm_length) * -facing
        hand_y = shoulder_y + int(math.sin(swing) * arm_length) + 3

        elbow_x = (shoulder_x + hand_x) // 2
        elbow_y = (shoulder_y + hand_y) // 2

        _NS_grimjaw._draw_muscular_arm(surface, shoulder_x, shoulder_y, elbow_x, elbow_y)
        _NS_grimjaw._draw_muscular_arm(surface, elbow_x, elbow_y, hand_x, hand_y)

        # Bracer
        bracer_x = int(shoulder_x + (hand_x - shoulder_x) * 0.75)
        bracer_y = int(shoulder_y + (hand_y - shoulder_y) * 0.75)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_darkest"], (bracer_x, bracer_y), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_dark"], (bracer_x, bracer_y), 3)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_mid"], (bracer_x - 1, bracer_y - 1), 2)

        # Fist
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["shadow"], (hand_x + 1, hand_y + 1), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["skin_darkest"], (hand_x, hand_y), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["skin_dark"], (hand_x, hand_y), 3)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["skin_mid"], (hand_x - 1, hand_y - 1), 2)


    def _draw_muscular_arm(surface, x1, y1, x2, y2):
        """Skin-toned muscular arm segment."""
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["shadow"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 5)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["skin_dark"], (x1, y1), (x2, y2), 4)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["skin_mid"], (x1, y1), (x2, y2), 2)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["skin_light"], (x1, y1), (x2, y2), 1)


    # ═══════════════════════════════════════════════════════
    # FIRE SWORD
    # ═══════════════════════════════════════════════════════

    def _draw_fire_sword(surface, hand_x, hand_y, angle, facing, phase, action):
        """Fire sword with glowing orange blade."""
        # Handle
        grip_len = 5
        grip_end_x = hand_x + int(math.cos(angle) * grip_len) * facing
        grip_end_y = hand_y + int(math.sin(angle) * grip_len)

        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["shadow"],
                (hand_x, hand_y), (grip_end_x, grip_end_y), 5)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["armor_darkest"],
                (hand_x, hand_y), (grip_end_x, grip_end_y), 4)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["armor_dark"],
                (hand_x, hand_y), (grip_end_x, grip_end_y), 2)

        # Grip wraps
        for wrap_i in range(2):
            wt = 0.3 + wrap_i * 0.4
            wx = int(hand_x + (grip_end_x - hand_x) * wt)
            wy = int(hand_y + (grip_end_y - hand_y) * wt)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["armor_darkest"], (wx, wy), 2)

        # Guard (cross-guard)
        perp_angle = angle + math.pi / 2
        guard_len = 4
        gx1 = grip_end_x + int(math.cos(perp_angle) * guard_len)
        gy1 = grip_end_y + int(math.sin(perp_angle) * guard_len)
        gx2 = grip_end_x - int(math.cos(perp_angle) * guard_len)
        gy2 = grip_end_y - int(math.sin(perp_angle) * guard_len)

        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_darkest"], (gx1, gy1), (gx2, gy2), 4)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_dark"], (gx1, gy1), (gx2, gy2), 3)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_mid"], (gx1, gy1), (gx2, gy2), 2)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["gold_light"], (gx1, gy1), (gx2, gy2), 1)

        # ═══ FIRE BLADE ═══
        blade_len = 22 if action != "attack" else 28

        tip_x = grip_end_x + int(math.cos(angle) * blade_len) * facing
        tip_y = grip_end_y + int(math.sin(angle) * blade_len)

        pulse = math.sin(phase * 1.5) * 0.3 + 0.7

        # Big glow behind blade
        glow_size = 44
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        gcx, gcy = glow_size // 2, glow_size // 2

        blade_dx = tip_x - grip_end_x
        blade_dy = tip_y - grip_end_y

        gx_start = gcx - blade_dx // 2
        gy_start = gcy - blade_dy // 2
        gx_end = gcx + blade_dx // 2
        gy_end = gcy + blade_dy // 2

        glow_layers = [
            (7, 60, _NS_grimjaw.PALETTE["fire_darkest"]),
            (5, 100, _NS_grimjaw.PALETTE["fire_dark"]),
            (4, 150, _NS_grimjaw.PALETTE["fire_mid"]),
            (2, 200, _NS_grimjaw.PALETTE["fire_light"]),
        ]
        for width, alpha, color in glow_layers:
            pygame.draw.line(glow_surf, (*color, int(alpha * pulse)),
                             (gx_start, gy_start), (gx_end, gy_end), width)

        surface.blit(glow_surf,
                     (int((grip_end_x + tip_x) / 2) - glow_size // 2,
                      int((grip_end_y + tip_y) / 2) - glow_size // 2))

        # Core blade
        pygame.draw.line(surface, _NS_grimjaw.PALETTE["fire_dark"],
                         (grip_end_x, grip_end_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_grimjaw.PALETTE["fire_mid"],
                         (grip_end_x, grip_end_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_grimjaw.PALETTE["fire_light"],
                         (grip_end_x, grip_end_y), (tip_x, tip_y), 1)
        _NS_grimjaw._aaline(surface, _NS_grimjaw.PALETTE["fire_hot"],
                (grip_end_x, grip_end_y), (tip_x, tip_y), 1)

        # Hot tip
        tip_glow = pygame.Surface((18, 18), pygame.SRCALPHA)
        for r in range(8, 0, -1):
            alpha = min(255, max(0, int((8 - r) * 35 * pulse)))
            if alpha > 0:
                _NS_grimjaw._aacircle(tip_glow, (*_NS_grimjaw.PALETTE["fire_hot"], alpha), (9, 9), r)
        surface.blit(tip_glow, (tip_x - 9, tip_y - 9))
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_core"], (tip_x, tip_y), 2)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["white"], (tip_x, tip_y, 1, 1))

        # Fire particles rising from blade
        for i in range(3):
            particle_phase = (phase * 2 + i * 0.5) % 1.0
            pt = particle_phase
            px = tip_x + int(math.sin(particle_phase * 6) * 3)
            py = tip_y - int(pt * 10)
            alpha = min(255, max(0, int(220 * (1 - pt))))
            if alpha > 0:
                _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_light"], alpha), (px, py), 2)
                _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_hot"], alpha), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_fire_mist(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Orange fire mist beneath floating Grimjaw."""
        strength = 1.5 if intense else 1.0

        # Base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_grimjaw.PALETTE["fire_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising fire wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_darkest"], alpha), (sx, sy), 5)
            _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_dark"], alpha), (sx, sy - 1), 4)
            _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_mid"], alpha), (sx, sy - 2), 3)
            _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_light"], min(255, alpha)),
                      (sx, sy - 3), 2)
            _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_hot"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting fire embers
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_dark"], (sx, sy), 3)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_light"], (sx, sy), 2)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_grimjaw.PALETTE["fire_dark"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_fire_aura(surface, x, y, phase):
        """Large background fire aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_grimjaw._aacircle(aura, (*_NS_grimjaw.PALETTE["fire_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_fire_platform(surface, x, y, phase, skill):
        """Fire circle pattern on the ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_grimjaw.PALETTE["fire_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_grimjaw.PALETTE["fire_mid"], 180),
                            (20, 14, 90, 16), 2)

        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_grimjaw.PALETTE["fire_light"], 170),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_grimjaw.PALETTE["fire_hot"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    # ===================================================================
    # BASIC ATTACK - FIRE SLASH ARC
    # ===================================================================
    def _draw_fire_slash_arc(surface, x, y, facing, progress, crit=False):
        """Fire slash crescent during basic attack."""
        if progress < 0.3 or progress > 0.9:
            return

        alpha_factor = 1.0
        if progress < 0.4:
            alpha_factor = (progress - 0.3) / 0.1
        elif progress > 0.8:
            alpha_factor = 1 - (progress - 0.8) / 0.1

        arc_surf = pygame.Surface((130, 100), pygame.SRCALPHA)

        # Bigger arc for crit
        arc_scale = 1.3 if crit else 1.0

        for i in range(16):
            arc_progress = i / 16
            arc_angle = -math.pi / 2 + arc_progress * math.pi * 1.1

            arc_x = 65 + int(math.cos(arc_angle) * 42 * arc_scale) * facing
            arc_y = 50 + int(math.sin(arc_angle) * 38 * arc_scale)

            alpha = min(255, max(0, int((240 - i * 14) * alpha_factor)))
            if alpha <= 0:
                continue

            # Multi-layer fire slash
            _NS_grimjaw._aacircle(arc_surf, (*_NS_grimjaw.PALETTE["fire_darkest"], alpha // 2),
                      (arc_x, arc_y), 9 if crit else 8)
            _NS_grimjaw._aacircle(arc_surf, (*_NS_grimjaw.PALETTE["fire_dark"], alpha),
                      (arc_x, arc_y), 7 if crit else 6)
            _NS_grimjaw._aacircle(arc_surf, (*_NS_grimjaw.PALETTE["fire_mid"], alpha),
                      (arc_x, arc_y), 5 if crit else 4)
            _NS_grimjaw._aacircle(arc_surf, (*_NS_grimjaw.PALETTE["fire_light"], alpha),
                      (arc_x, arc_y), 3 if crit else 2)
            _NS_grimjaw._aacircle(arc_surf, (*_NS_grimjaw.PALETTE["fire_hot"], alpha),
                      (arc_x, arc_y), 2 if crit else 1)

        surface.blit(arc_surf, (x - 65, y - 50))


    def _draw_critical_strike_burst(surface, x, y, facing, progress):
        """Critical strike burst effect - extra sparkle."""
        burst_x = x + 30 * facing
        burst_y = y - 5

        t = (progress - 0.5) / 0.2
        t = max(0.0, min(1.0, t))

        # 4-pointed star burst
        star_r = int(6 + t * 14)
        alpha = int(255 * (1 - t))

        for angle_deg in (0, 45, 90, 135):
            angle = math.radians(angle_deg)
            ox1 = burst_x + int(math.cos(angle) * star_r)
            oy1 = burst_y + int(math.sin(angle) * star_r)
            ox2 = burst_x - int(math.cos(angle) * star_r)
            oy2 = burst_y - int(math.sin(angle) * star_r)

            _NS_grimjaw._aaline(surface, (*_NS_grimjaw.PALETTE["fire_dark"], alpha),
                    (ox1, oy1), (ox2, oy2), 4)
            _NS_grimjaw._aaline(surface, (*_NS_grimjaw.PALETTE["fire_light"], alpha),
                    (ox1, oy1), (ox2, oy2), 2)
            _NS_grimjaw._aaline(surface, (*_NS_grimjaw.PALETTE["fire_hot"], alpha),
                    (ox1, oy1), (ox2, oy2), 1)

        # Central bright core
        core_alpha = int(255 * (1 - t))
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_light"], core_alpha),
                  (burst_x, burst_y), 4)
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_hot"], core_alpha),
                  (burst_x, burst_y), 2)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_core"], (burst_x, burst_y),
                  max(1, int(1 + (1 - t))))

        # "CRIT!" text glow (small sparkles)
        for i in range(6):
            angle = i * math.pi / 3 + progress * 5
            dist = 20 + int(math.sin(progress * 8 + i) * 4)
            px = burst_x + int(math.cos(angle) * dist)
            py = burst_y + int(math.sin(angle) * dist)
            _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_hot"], alpha), (px, py), 2)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["white"], (px, py), 1)


    # ===================================================================
    # SKILL Q: BLADE FURY (Spinning + fire rings)
    # ===================================================================
    def _draw_blade_fury_rings(surface, x, y, phase):
        """Fire rings spinning around character during Blade Fury."""
        for ring_i in range(3):
            ring_phase = phase * 3 + ring_i * 1.5
            ring_radius = 28 + ring_i * 6

            # Ring is horizontal ellipse (ground-level)
            for i in range(24):
                angle = ring_phase + i * math.pi / 12
                px = x + int(math.cos(angle) * ring_radius)
                py = y + int(math.sin(angle) * ring_radius * 0.4)

                _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_darkest"], (px, py), 4)
                _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_dark"], (px, py), 3)
                _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_mid"], (px, py), 2)
                _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_light"], (px, py), 1)


    def _draw_fire_particles_orbit(surface, x, y, phase):
        """Fire particles orbiting during spinning."""
        for i in range(14):
            p_phase = phase * 4 + i * 0.5
            p_angle = p_phase
            p_dist = 28 + int(math.sin(p_phase * 2) * 10)

            px = x + int(math.cos(p_angle) * p_dist)
            py = y + int(math.sin(p_angle) * p_dist * 0.5)

            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_dark"], (px, py), 3)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_hot"], (px, py), 2)
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_core"], (px, py), 1)


    # ===================================================================
    # SKILL W: HEALING WARD
    # ===================================================================
    def _draw_healing_ward_ground(surface, hero, x, y, timer, phase):
        """Ground layer of healing ward - green healing circle."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 25)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        aura = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Ring
        pygame.draw.ellipse(aura, (*_NS_grimjaw.PALETTE["heal_mid"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(aura, (*_NS_grimjaw.PALETTE["heal_light"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runic marks around aura
        for i in range(8):
            a = phase * 0.3 + i * math.pi / 4
            px = cx + int(math.cos(a) * (radius - 5))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            pygame.draw.circle(aura, (*_NS_grimjaw.PALETTE["heal_core"], int(220 * pulse)),
                               (px, py), 3)
            pygame.draw.circle(aura, _NS_grimjaw.PALETTE["white"], (px, py), 1)

        surface.blit(aura, (x - cx, y + 30 - cy))


    def _draw_healing_ward_totem(surface, hero, x, y, timer, phase):
        """Green healing totem next to Grimjaw."""
        facing = getattr(hero, "direction", 1)
        wx = x + 40 * facing
        wy = y + 20

        # Base (stone/wood)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["shadow"], (wx - 6, wy + 6, 12, 5))
        _NS_grimjaw._rect(surface, (70, 45, 35), (wx - 6, wy + 5, 12, 5), border_radius=1)
        _NS_grimjaw._rect(surface, (110, 75, 55), (wx - 6, wy + 5, 11, 4), border_radius=1)
        _NS_grimjaw._rect(surface, (150, 105, 80), (wx - 5, wy + 5, 8, 2))

        # Pole (dark wood)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_darkest"], (wx - 2, wy - 6, 4, 12))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_dark"], (wx - 2, wy - 6, 3, 12))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["armor_mid"], (wx - 2, wy - 6, 2, 10))

        # Wood bindings
        for band_y in (wy - 3, wy + 2):
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_dark"], (wx - 3, band_y, 6, 1))
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["gold_mid"], (wx - 3, band_y, 4, 1))

        # Glowing orb on top
        pulse = math.sin(phase) * 0.3 + 0.7

        # Big glow
        glow_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            alpha = min(255, max(0, int(150 * pulse - r * 12)))
            if alpha > 0:
                _NS_grimjaw._aacircle(glow_surf, (*_NS_grimjaw.PALETTE["heal_mid"], alpha),
                          (16, 16), r)
        surface.blit(glow_surf, (wx - 16, wy - 8 - 16))

        # Orb layers
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["heal_darkest"], (wx, wy - 8), 6)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["heal_dark"], (wx, wy - 8), 5)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["heal_mid"], (wx - 1, wy - 9), 4)
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["heal_light"], (wx - 1, wy - 9), 3)
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["heal_core"], (wx - 1, wy - 9, 1, 1))
        _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["white"], (wx - 1, wy - 9, 1, 1))

        # Floating + heal symbols
        for i in range(4):
            sym_phase = phase * 2 + i * 1.5
            sym_y_offset = int((sym_phase * 3) % 14)
            sym_alpha = min(255, max(0, 220 - sym_y_offset * 15))

            if sym_alpha > 0:
                sym_x = wx + int(math.sin(sym_phase) * 5)
                sym_y = wy - 12 - sym_y_offset

                # Plus symbol
                sym_surf = pygame.Surface((7, 7), pygame.SRCALPHA)
                pygame.draw.rect(sym_surf,
                                 (*_NS_grimjaw.PALETTE["heal_light"], sym_alpha),
                                 (3, 0, 1, 7))
                pygame.draw.rect(sym_surf,
                                 (*_NS_grimjaw.PALETTE["heal_light"], sym_alpha),
                                 (0, 3, 7, 1))
                surface.blit(sym_surf, (sym_x - 3, sym_y - 3))


    def _draw_heal_aura(surface, x, y, phase):
        """Heal aura around Grimjaw when Healing Ward active."""
        pulse = math.sin(phase) * 0.3 + 0.7

        aura_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
        for r in range(40, 15, -3):
            alpha = min(255, max(0, int((40 - r) * 6 * pulse)))
            if alpha > 0:
                _NS_grimjaw._aacircle(aura_surf, (*_NS_grimjaw.PALETTE["heal_mid"], alpha),
                          (45, 45), r)
        surface.blit(aura_surf, (x - 45, y - 45))

        # Ground ring particles
        for i in range(14):
            angle = i * math.pi / 7 + phase
            rx = x + int(math.cos(angle) * 32)
            ry = y + int(math.sin(angle) * 12) + 18
            _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["heal_light"], (rx, ry), 2)
            _NS_grimjaw._rect(surface, _NS_grimjaw.PALETTE["heal_core"], (rx, ry, 1, 1))

        # Rising + symbols around body
        for i in range(6):
            phase_i = (phase * 1.5 + i * 0.3) % 1.0
            angle = i * math.pi / 3
            px = x + int(math.cos(angle) * 25)
            py = y + 20 - int(phase_i * 40)
            alpha = int(220 * (1 - phase_i))

            if alpha > 0:
                plus_surf = pygame.Surface((7, 7), pygame.SRCALPHA)
                pygame.draw.rect(plus_surf,
                                 (*_NS_grimjaw.PALETTE["heal_light"], alpha),
                                 (3, 0, 1, 7))
                pygame.draw.rect(plus_surf,
                                 (*_NS_grimjaw.PALETTE["heal_light"], alpha),
                                 (0, 3, 7, 1))
                surface.blit(plus_surf, (px - 3, py - 3))


    # ===================================================================
    # SKILL E: OMNISLASH (Multiple radial fire slashes)
    # ===================================================================
    def _draw_omnislash_ground(surface, hero, x, y, timer, phase):
        """Ground pulse effect during omnislash."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        ring_r = int(50 * pulse)
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_darkest"], 100),
                  (x, y + 30), ring_r + 4)
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_dark"], 150),
                  (x, y + 30), ring_r, 2)


    def _draw_omnislash_slashes(surface, hero, x, y, timer, phase):
        """Multiple fire slashes emanating from Grimjaw."""
        slash_count = 8
        for i in range(slash_count):
            slash_phase = phase * 4 + i * 0.6
            pt = (slash_phase % 2) / 2

            if pt > 0.7:
                continue

            angle = i * math.pi * 2 / slash_count + phase * 0.3
            dist = 35 + int(pt * 25)

            slash_x = x + int(math.cos(angle) * dist)
            slash_y = y + int(math.sin(angle) * dist)

            alpha = min(255, max(0, int(255 * (1 - pt))))
            slash_len = 24

            slash_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            end_x = 30 + int(math.cos(angle) * slash_len)
            end_y = 30 + int(math.sin(angle) * slash_len)

            pygame.draw.line(slash_surf,
                             (*_NS_grimjaw.PALETTE["fire_darkest"], alpha),
                             (30, 30), (end_x, end_y), 7)
            pygame.draw.line(slash_surf,
                             (*_NS_grimjaw.PALETTE["fire_dark"], alpha),
                             (30, 30), (end_x, end_y), 5)
            pygame.draw.line(slash_surf,
                             (*_NS_grimjaw.PALETTE["fire_mid"], alpha),
                             (30, 30), (end_x, end_y), 3)
            pygame.draw.line(slash_surf,
                             (*_NS_grimjaw.PALETTE["fire_hot"], alpha),
                             (30, 30), (end_x, end_y), 2)
            _NS_grimjaw._aaline(slash_surf,
                    (*_NS_grimjaw.PALETTE["fire_core"], alpha),
                    (30, 30), (end_x, end_y), 1)

            # Tip sparkle
            _NS_grimjaw._aacircle(slash_surf, (*_NS_grimjaw.PALETTE["white"], alpha),
                      (end_x, end_y), 2)

            surface.blit(slash_surf, (slash_x - 30, slash_y - 30))

        # Central bright flash
        core_pulse = math.sin(phase * 6) * 0.3 + 0.7
        _NS_grimjaw._aacircle(surface, (*_NS_grimjaw.PALETTE["fire_hot"], int(180 * core_pulse)),
                  (x, y), int(8 * core_pulse))
        _NS_grimjaw._aacircle(surface, _NS_grimjaw.PALETTE["fire_core"], (x, y), int(4 * core_pulse))


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_hero(surface, hero, x, y):
        _NS_grimjaw.draw_grimjaw(surface, hero, x, y)

# ====================================================================
# sylara.py
# ====================================================================
class _NS_sylara:
    """Namespace sylara - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Wind Ranger inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - fair
        "skin_darkest":   (155, 105,  85),
        "skin_dark":      (210, 160, 130),
        "skin_mid":       (240, 200, 170),
        "skin_light":     (250, 220, 195),
        "skin_high":      (255, 240, 220),

        # Hair (red/orange)
        "hair_darkest":   ( 85,  25,  15),
        "hair_dark":      (145,  50,  25),
        "hair_mid":       (200,  85,  35),
        "hair_light":     (240, 130,  55),
        "hair_shine":     (255, 180,  95),

        # Green outfit - forest green
        "cloth_darkest":  ( 15,  35,  20),
        "cloth_dark":     ( 35,  65,  35),
        "cloth_mid":      ( 60, 105,  55),
        "cloth_light":    ( 95, 150,  80),
        "cloth_high":     (140, 195, 115),

        # Cloak - darker green
        "cloak_darkest":  ( 20,  40,  25),
        "cloak_dark":     ( 40,  75,  40),
        "cloak_mid":      ( 65, 110,  55),
        "cloak_light":    (100, 155,  80),

        # Hood - similar to cloak
        "hood_darkest":   ( 18,  36,  20),
        "hood_dark":      ( 30,  55,  30),
        "hood_mid":       ( 55,  95,  50),
        "hood_light":     ( 85, 135,  70),

        # Leather (belt, boots, quiver)
        "leather_darkest":( 35,  20,  10),
        "leather_dark":   ( 70,  45,  25),
        "leather_mid":    (110,  75,  45),
        "leather_light":  (155, 110,  70),

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),

        # Bow - wood
        "wood_darkest":   ( 45,  25,  15),
        "wood_dark":      ( 85,  55,  30),
        "wood_mid":       (130,  90,  50),
        "wood_light":     (170, 125,  75),
        "wood_shine":     (205, 165, 105),

        # Bowstring
        "string":         (220, 210, 180),
        "string_shine":   (250, 245, 220),

        # Wind - green energy
        "wind_darkest":   ( 20,  60,  25),
        "wind_dark":      ( 50, 120,  50),
        "wind_mid":       (110, 195,  90),
        "wind_light":     (170, 235, 135),
        "wind_bright":    (210, 255, 175),
        "wind_white":     (240, 255, 220),

        # Arrow
        "arrow_shaft":    (200, 175, 130),
        "arrow_shaft_d":  (140, 110,  70),
        "arrow_head":     (180, 195, 210),
        "arrow_head_d":   (100, 115, 135),
        "arrow_feather":  (140, 200,  95),
        "arrow_feather_d":( 70, 120,  55),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       ( 90, 145,  80),
        "eye_iris_light": (150, 210, 130),
        "eye_pupil":      ( 15,  25,  15),

        # Lips
        "lips_dark":      (155,  70,  75),
        "lips_mid":       (205, 110, 115),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sylara._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_sylara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_sylara._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_sylara._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_sylara._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_sylara._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_sylara._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 250 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Wind visual helpers
    # ---------------------------------------------------------------------------
    def _draw_wind_arc(surface, cx, cy, radius, start_angle, end_angle,
                       color, width=2, segments=12):
        """Curved wind arc."""
        points = []
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius
            points.append((px, py))
        for i in range(len(points) - 1):
            _NS_sylara._aaline(surface, color, points[i], points[i + 1], width)


    def _draw_leaf(surface, cx, cy, size, angle, color_dark, color_mid, color_light):
        """Small floating leaf."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        back_x = cx - ca * size
        back_y = cy - sa * size
        side1_x = cx + math.cos(angle + math.pi / 2) * size * 0.35
        side1_y = cy + math.sin(angle + math.pi / 2) * size * 0.35
        side2_x = cx + math.cos(angle - math.pi / 2) * size * 0.35
        side2_y = cy + math.sin(angle - math.pi / 2) * size * 0.35

        _NS_sylara._poly(surface, color_dark, [
            (tip_x, tip_y), (side1_x, side1_y),
            (back_x, back_y), (side2_x, side2_y),
        ])
        _NS_sylara._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((side1_x + cx) / 2, (side1_y + cy) / 2),
            (back_x, back_y),
            ((side2_x + cx) / 2, (side2_y + cy) / 2),
        ])
        _NS_sylara._aaline(surface, color_light, (back_x, back_y), (tip_x, tip_y), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Wind Arrow
    # ---------------------------------------------------------------------------
    class WindArrowProjectile:
        """Basic wind arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=9.0, powered=False,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.powered = powered  # Powershot variant
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            # Homing: target/damage/team (visual-only; damage otoritatif
            # ada di hero_skills). Kalau target hidup, kejar tiap frame.
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target yang bergerak (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_sylara._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            max_trail = 18 if self.powered else 8
            if len(self.trail) > max_trail:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            # Trail - wind wisps
            trail_intensity = 2 if self.powered else 1
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12) * trail_intensity
                alpha = min(255, alpha)
                r = max(1, (7 if self.powered else 5) - (len(self.trail) - i))
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha), (tx, ty), r + 2)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_light"], min(255, alpha // 2)),
                          (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                if self.powered:
                    # Powershot - large glowing green arrow
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], 150), (px, py), 18)
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], 200), (px, py), 12)

                    # Large arrow shaft
                    length = 22
                    tip_x = px + ca * length
                    tip_y = py + sa * length
                    tail_x = px - ca * length
                    tail_y = py - sa * length

                    # Glow shaft
                    _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_bright"], 220),
                            (tail_x, tail_y), (tip_x, tip_y), 5)
                    _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_white"], 240),
                            (tail_x, tail_y), (tip_x, tip_y), 3)
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["white"],
                            (tail_x, tail_y), (tip_x, tip_y), 1)

                    # Arrowhead
                    perp_x = -sa * 6
                    perp_y = ca * 6
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_bright"], [
                        (tip_x + ca * 8, tip_y + sa * 8),
                        (tip_x + perp_x, tip_y + perp_y),
                        (tip_x - perp_x, tip_y - perp_y),
                    ])
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_white"], [
                        (tip_x + ca * 7, tip_y + sa * 7),
                        (tip_x + perp_x * 0.6, tip_y + perp_y * 0.6),
                        (tip_x - perp_x * 0.6, tip_y - perp_y * 0.6),
                    ])
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["white"],
                              (int(tip_x + ca * 7), int(tip_y + sa * 7)), 2)

                    # Wind spiral around powershot
                    for i in range(5):
                        a = phase * 3 + i * math.pi * 2 / 5
                        r = 12
                        sx = px + math.cos(a) * r
                        sy = py + math.sin(a) * r
                        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], 180),
                                  (int(sx), int(sy)), 2)
                else:
                    # Normal arrow
                    length = 14
                    tip_x = px + ca * length
                    tip_y = py + sa * length
                    tail_x = px - ca * length
                    tail_y = py - sa * length

                    # Glow
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], 100), (px, py), 8)
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], 130), (px, py), 5)

                    # Arrow shaft
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["arrow_shaft_d"],
                            (tail_x, tail_y), (tip_x, tip_y), 3)
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["arrow_shaft"],
                            (tail_x, tail_y), (tip_x, tip_y), 2)
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wood_shine"],
                            (tail_x, tail_y), (tip_x, tip_y), 1)

                    # Arrowhead
                    perp_x = -sa * 3
                    perp_y = ca * 3
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_head_d"], [
                        (tip_x + ca * 5, tip_y + sa * 5),
                        (tip_x + perp_x, tip_y + perp_y),
                        (tip_x - perp_x, tip_y - perp_y),
                    ])
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_head"], [
                        (tip_x + ca * 4, tip_y + sa * 4),
                        (tip_x + perp_x * 0.6, tip_y + perp_y * 0.6),
                        (tip_x - perp_x * 0.6, tip_y - perp_y * 0.6),
                    ])
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["white"],
                              (int(tip_x + ca * 4), int(tip_y + sa * 4)), 1)

                    # Fletching (feathers)
                    for f_off in (2, -2):
                        fp_x = -sa * f_off
                        fp_y = ca * f_off
                        _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_feather_d"], [
                            (tail_x, tail_y),
                            (tail_x + ca * 4, tail_y + sa * 4),
                            (tail_x + ca * 3 + fp_x, tail_y + sa * 3 + fp_y),
                        ])
                        _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_feather"], [
                            (tail_x + ca * 1, tail_y + sa * 1),
                            (tail_x + ca * 4, tail_y + sa * 4),
                            (tail_x + ca * 3 + fp_x * 0.7,
                             tail_y + sa * 3 + fp_y * 0.7),
                        ])


    class ShackleProjectile:
        """Shackle shot - arrow that binds enemies with vines/wind."""
        def __init__(self, sx, sy, tx, ty, speed=8.0,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_sylara._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Swirling trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 14)
                # Spiral around trail
                spiral_off = math.sin(phase * 3 + i * 0.5) * 3
                perp = self.angle + math.pi / 2
                sx = tx + math.cos(perp) * spiral_off
                sy = ty + math.sin(perp) * spiral_off
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_light"], alpha),
                          (int(sx), int(sy)), 3)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                          (int(sx), int(sy)), 1)

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                # Glow
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], 130), (px, py), 10)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], 170), (px, py), 7)

                # Arrow with binding energy
                length = 14
                tip_x = px + ca * length
                tip_y = py + sa * length
                tail_x = px - ca * length
                tail_y = py - sa * length

                _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wood_dark"],
                        (tail_x, tail_y), (tip_x, tip_y), 3)
                _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wind_bright"],
                        (tail_x, tail_y), (tip_x, tip_y), 2)
                _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wind_white"],
                        (tail_x, tail_y), (tip_x, tip_y), 1)

                # Vine wraps spiraling around
                for i in range(4):
                    t = i / 4.0
                    spiral_a = phase * 6 + i * math.pi / 2
                    spiral_r = 4
                    cx = px + ca * (t - 0.5) * length
                    cy = py + sa * (t - 0.5) * length
                    perp = self.angle + math.pi / 2
                    sx = cx + math.cos(perp) * math.cos(spiral_a) * spiral_r
                    sy = cy + math.sin(perp) * math.cos(spiral_a) * spiral_r
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["wind_bright"],
                              (int(sx), int(sy)), 2)
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["wind_white"],
                              (int(sx), int(sy)), 1)

                # Arrowhead
                perp_x = -sa * 4
                perp_y = ca * 4
                _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_dark"], [
                    (tip_x + ca * 6, tip_y + sa * 6),
                    (tip_x + perp_x, tip_y + perp_y),
                    (tip_x - perp_x, tip_y - perp_y),
                ])
                _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_bright"], [
                    (tip_x + ca * 5, tip_y + sa * 5),
                    (tip_x + perp_x * 0.6, tip_y + perp_y * 0.6),
                    (tip_x - perp_x * 0.6, tip_y - perp_y * 0.6),
                ])


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_sy_last_x"):
            boss._sy_last_x = boss.x
            boss._sy_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sy_last_x)
        dy = abs(boss.y - boss._sy_last_y)
        boss._sy_last_x = boss.x
        boss._sy_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track bow attack animation timeline (draw + release)."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sy_prev_timer", -1))
        active = bool(getattr(boss, "_sy_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._sy_attack_active = True
            active = True

        if active and timer <= 0:
            boss._sy_attack_active = False
            active = False

        boss._sy_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._sy_attack_frame = max(0, cooldown - timer) if active else 0
        boss._sy_attack_progress = (
            min(1.0, boss._sy_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        for proj in boss._sy_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._sy_projectiles = [p for p in boss._sy_projectiles if p.alive or p.dead_frames < 8]


    def _spawn_arrow(boss, x, y, powered=False):
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        tx, ty = _NS_sylara._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Arrow spawns from bow position
        sx = x + 22 * facing
        sy = y - 8
        speed = 10.0 if powered else 8.5
        tgt = getattr(boss, "target", None)
        proj = _NS_sylara.WindArrowProjectile(
            sx, sy, tx, ty, speed=speed, powered=powered,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._sy_projectiles.append(proj)


    def _spawn_shackle(boss, x, y):
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        tx, ty = _NS_sylara._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 22 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)
        proj = _NS_sylara.ShackleProjectile(
            sx, sy, tx, ty, speed=8.0,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._sy_projectiles.append(proj)


    def _spawn_focus_fire_volley(boss, x, y):
        """Focus Fire - many arrows homing ke target (fan sangat rapat)."""
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        tx, ty = _NS_sylara._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 22 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)

        # Base angle to target
        base_angle = math.atan2(ty - sy, tx - sx)

        # Fan of 5 arrows - spread DIPERSEMPIT 0.18 -> 0.06 supaya
        # terarah, & SEMUA homing ke target yang sama.
        for i in range(5):
            spread = (i - 2) * 0.06  # angle spread (dulu 0.18)
            angle = base_angle + spread
            ex = sx + math.cos(angle) * 400
            ey = sy + math.sin(angle) * 400
            proj = _NS_sylara.WindArrowProjectile(
                sx, sy, ex, ey, speed=11.0, powered=False,
                target=tgt, damage=0, team=getattr(boss, "team", None))
            # BUGFIX (orb random pada hero): lihat _spawn_arrow.
            proj.source, proj.cx, proj.cy = boss, x, y
            boss._sy_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_sylara(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sylara._detect_moving(boss)
        _NS_sylara._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_sy_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # ---------- Background layers ----------
        # Rim-light hijau lembut memisahkan cape dan rambut merah dari
        # terrain gelap, seperti presentation sprite pada referensi.
        # Portrait LOD sengaja melewati aura/platform seukuran arena agar
        # auto-crop mengisi portrait dengan wajah & material Sylara, bukan
        # lingkaran efek 180 px.
        if not portrait_hd:
            _NS_sylara._draw_ranger_silhouette_glow(surface, x, y - 10, pulse)
            _NS_sylara._draw_wind_aura(surface, x, y, pulse)
            _NS_sylara._draw_wind_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        # Q = Focus Fire, W = Windrun, E = Shackle Shot, R = Powershot
        # (sesuai hero_skills/sylara_skills.py)
        if active_skill == "e":
            _NS_sylara._draw_shackle_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_sylara._draw_focus_fire_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sylara._draw_windrun_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if active_skill == "w":
            # Windrun - fast dash pose
            _NS_sylara._draw_sylara_windrun(surface, boss, x, y, skill_timer)
        elif attacking:
            _NS_sylara._draw_sylara_attack(surface, boss, x, y)
        elif moving:
            _NS_sylara._draw_sylara_walk(surface, boss, x, y)
        else:
            _NS_sylara._draw_sylara_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        if not portrait_hd:
            _NS_sylara._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "r":
            _NS_sylara._draw_powershot_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_sylara._draw_focus_fire_effect(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_sylara_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x, y + 48)
            _NS_sylara._draw_floating_wind(surface, x, y + 35, boss.pulse)
        _NS_sylara._draw_sylara_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_sylara_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x + sway, y + 48)
            _NS_sylara._draw_floating_wind(surface, x + sway, y + 35, phase,
                                           trail=True, facing=boss.direction)
        _NS_sylara._draw_sylara_body(
            surface, x + sway, y - bob, boss.direction, phase, "walk",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_sylara_attack(surface, boss, x, y):
        progress = getattr(boss, "_sy_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Check if we should power-shot (during Q)
        powered = getattr(boss, "active_skill", None) == "q"

        # Spawn arrow at release (mid-late in animation)
        release_start = 0.55 if powered else 0.5
        release_end = 0.65 if powered else 0.6

        # Basic attack TIDAK spawn renderer projectile - pakai sistem
        # generic (_entity.py) yang homing & terarah saja supaya tidak
        # ada efek ganda. Renderer arrow hanya saat skill aktif.
        active_skill = getattr(boss, "active_skill", None)
        if (active_skill is not None
                and release_start < progress < release_end
                and not getattr(boss, "_sy_arrow_spawned", False)):
            _NS_sylara._spawn_arrow(boss, x, y, powered=powered)
            boss._sy_arrow_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._sy_arrow_spawned = False

        # Slight recoil back on release
        recoil = 0
        if progress > release_start:
            t = (progress - release_start) / (1 - release_start)
            recoil = int(math.sin(t * math.pi) * 2) * -boss.direction

        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_sylara._draw_shadow(surface, x + recoil, y + 48)
            _NS_sylara._draw_floating_wind(surface, x + recoil, y + 35,
                                           boss.pulse, intense=True)
        _NS_sylara._draw_sylara_body(surface, x + recoil, y, boss.direction,
                                     boss.pulse, "attack", progress,
                                     powered=powered, detail=portrait_hd)
        if not portrait_hd:
            _NS_sylara._draw_bow_release_flash(surface, x + recoil, y,
                                               boss.direction, progress)


    def _draw_sylara_windrun(surface, boss, x, y, timer):
        """Fast dash pose during windrun."""
        phase = boss.pulse * 3.0
        bob = int(abs(math.sin(phase * 2)) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x, y + 48)
            _NS_sylara._draw_windrun_trail(surface, x, y, boss.direction, phase)
        _NS_sylara._draw_sylara_body(
            surface, x, y - bob, boss.direction, phase, "windrun",
            detail=getattr(boss, "_portrait_hd", False))


    # ===================================================================
    # BODY RENDERING - HD Wind Ranger
    # ===================================================================
    def _draw_sylara_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, powered=False, detail=False):
        """Renderer tubuh Sylara kualitas maksimum, 100% procedural.

        Dibangun sebagai bone rig 2D berlapis seperti Kaizen/Thorne
        Masterwork: cape hijau per-panel yang beranimasi, quiver berisi
        anak panah, korset kulit ber-strap, hood runcing dengan rambut
        merah menyembul, dan busur recurve yang posenya dihitung dari
        sendi (grip, nock, tarikan tali). Tidak ada PNG, sprite sheet,
        ataupun image.load.
        """
        _NS_sylara._draw_sylara_elite(
            surface, cx, cy, facing, phase, action, attack_progress,
            powered=powered, detail=detail)


    # ===================================================================
    # MASTERWORK RIG - bone rig 2D berlapis (setara Kaizen Masterwork)
    # ===================================================================
    def _bow_frame(tilt):
        """Basis lokal busur: (up, forward) untuk kemiringan `tilt`."""
        return ((math.sin(tilt), -math.cos(tilt)),
                (math.cos(tilt), math.sin(tilt)))


    def _bow_point(grip, tilt, u, v):
        """Titik pada bidang busur: u = sepanjang limb, v = ke depan."""
        (ux, uy), (fx, fy) = _NS_sylara._bow_frame(tilt)
        return (grip[0] + ux * u + fx * v, grip[1] + uy * u + fy * v)


    def _bow_nock(grip, tilt, draw_amt):
        """Posisi nock (tangan penarik) dalam koordinat lokal tubuh."""
        return _NS_sylara._bow_point(grip, tilt, 0.0, -2.0 - draw_amt * 12.0)


    def _draw_elite_bow(surface, pt, f, grip, tilt, draw_amt, phase,
                        powered=False, detail=False):
        """Busur recurve kayu pose-driven: limb melengkung, tali menegang
        mengikuti tarikan, anak panah ternock saat draw_amt > 0."""
        p = _NS_sylara.PALETTE
        bp = _NS_sylara._bow_point
        flex = draw_amt * 0.55

        def limb_points(sign):
            pts = []
            for i in range(7):
                s = i / 6.0
                u = sign * 24.0 * s
                # perut busur maju, ujung recurve menekuk balik
                v = 8.0 * s * s - 14.0 * (s ** 4) - flex * 6.0 * s * s
                pts.append(bp(grip, tilt, u, v))
            return pts

        tips = []
        for sign in (1, -1):
            pts = limb_points(sign)
            tips.append(pts[-1])
            for i in range(len(pts) - 1):
                w = 5 - int(i * 0.6)
                a, b = pts[i], pts[i + 1]
                _NS_sylara._aaline(surface, p["shadow_deep"],
                                   pt(a[0] + 1, a[1] + 1),
                                   pt(b[0] + 1, b[1] + 1), w + 2)
                _NS_sylara._aaline(surface, p["wood_darkest"],
                                   pt(*a), pt(*b), w)
                _NS_sylara._aaline(surface, p["wood_mid"],
                                   pt(*a), pt(*b), max(1, w - 2))
                _NS_sylara._aaline(surface, p["wood_light"],
                                   pt(a[0], a[1] - 1), pt(b[0], b[1] - 1), 1)
                if detail and i % 2 == 0:
                    _NS_sylara._aacircle(surface, p["wood_shine"],
                                         pt(a[0], a[1] - 1), 1)
            # ujung limb dibungkus kulit + ring emas
            tip = pts[-1]
            _NS_sylara._aacircle(surface, p["leather_dark"], pt(*tip), 2)
            _NS_sylara._aacircle(surface, p["gold_mid"], pt(*tip), 1)
            _NS_sylara._aacircle(surface, p["gold_light"],
                                 pt(tip[0], tip[1] - 1), 1)

        # grip kulit + lilitan
        g_a = bp(grip, tilt, 6, 1)
        g_b = bp(grip, tilt, -6, 1)
        _NS_sylara._aaline(surface, p["leather_darkest"], pt(*g_a), pt(*g_b), 6)
        _NS_sylara._aaline(surface, p["leather_mid"], pt(*g_a), pt(*g_b), 4)
        for i in range(4):
            s = -4 + i * 2.8
            w_a = bp(grip, tilt, s, -1)
            w_b = bp(grip, tilt, s + 1.4, 3)
            _NS_sylara._aaline(surface, p["leather_light"],
                               pt(*w_a), pt(*w_b), 1)

        # tali: dua ruas menuju nock
        nock = _NS_sylara._bow_nock(grip, tilt, draw_amt)
        for col, w in ((p["shadow_deep"], 3), (p["string"], 2),
                       (p["string_shine"], 1)):
            _NS_sylara._aaline(surface, col, pt(*tips[0]), pt(*nock), w)
            _NS_sylara._aaline(surface, col, pt(*tips[1]), pt(*nock), w)

        if draw_amt > 0.05:
            _NS_sylara._draw_elite_arrow(surface, pt, nock, tilt, draw_amt,
                                         phase, powered, detail)
        return nock


    def _draw_elite_arrow(surface, pt, nock, tilt, draw_amt, phase,
                          powered=False, detail=False):
        """Anak panah ternock: shaft kayu, mata baja, bulu hijau."""
        p = _NS_sylara.PALETTE
        (_, _), (fx, fy) = _NS_sylara._bow_frame(tilt)
        length = 32
        tip = (nock[0] + fx * length, nock[1] + fy * length)
        _NS_sylara._aaline(surface, p["shadow_deep"],
                           pt(nock[0], nock[1] + 1), pt(tip[0], tip[1] + 1), 4)
        _NS_sylara._aaline(surface, p["arrow_shaft_d"], pt(*nock), pt(*tip), 3)
        _NS_sylara._aaline(surface, p["arrow_shaft"],
                           pt(nock[0], nock[1] - 1), pt(tip[0], tip[1] - 1), 1)
        # mata panah
        head_b = (tip[0] - fx * 8, tip[1] - fy * 8)
        _NS_sylara._poly(surface, p["arrow_head_d"], [
            pt(*tip), pt(head_b[0], head_b[1] - 3), pt(head_b[0], head_b[1] + 3)])
        _NS_sylara._poly(surface, p["arrow_head"], [
            pt(tip[0] - fx, tip[1] - fy),
            pt(head_b[0] + 1, head_b[1] - 2), pt(head_b[0] + 1, head_b[1] + 2)])
        if detail:
            _NS_sylara._aaline(surface, p["white"],
                               pt(tip[0] - fx * 2, tip[1] - fy * 2 - 1),
                               pt(head_b[0] + 2, head_b[1] - 1), 1)
        # fletching
        for side in (-3, 3):
            _NS_sylara._poly(surface, p["arrow_feather_d"], [
                pt(nock[0] + fx * 2, nock[1] + fy * 2),
                pt(nock[0] + fx * 9, nock[1] + fy * 9 + side),
                pt(nock[0] + fx * 9, nock[1] + fy * 9)])
            _NS_sylara._poly(surface, p["arrow_feather"], [
                pt(nock[0] + fx * 3, nock[1] + fy * 3),
                pt(nock[0] + fx * 8, nock[1] + fy * 8 + side * .7),
                pt(nock[0] + fx * 8, nock[1] + fy * 8)])
        if powered or draw_amt > 0.75:
            glow = p["wind_white"] if powered else p["wind_bright"]
            alpha = int(200 * min(1.0, draw_amt))
            for i in range(4):
                gx = tip[0] + fx * (4 + i * 5)
                gy = tip[1] + fy * (4 + i * 5)
                _NS_sylara._aacircle(surface, (*glow, max(30, alpha - i * 45)),
                                     pt(gx, gy), max(1, 3 - i))


    def _draw_sylara_masterwork_details(surface, pt, f):
        """Micro-detail khusus portrait LOD. Di skala arena tanda-tanda ini
        runtuh jadi noise, jadi LOD mengeluarkannya dari cache gameplay."""
        p = _NS_sylara.PALETTE
        # helai rambut halus di pipi & tengkuk
        for i in range(5):
            _NS_sylara._aaline(surface, p["hair_shine"],
                               pt(2 + i * 2, -37 + i),
                               pt(-1 + i * 2, -32 + i), 1)
        for i in range(4):
            _NS_sylara._aaline(surface, p["hair_light"],
                               pt(-8 - i * 3, -28 + i * 2),
                               pt(-13 - i * 3, -22 + i * 2), 1)
        # bulu mata, alis & kilau bibir
        _NS_sylara._aaline(surface, p["hair_darkest"], pt(6, -33), pt(11, -33), 1)
        _NS_sylara._aacircle(surface, p["lips_mid"], pt(10, -26), 1)
        _NS_sylara._aacircle(surface, p["skin_high"], pt(7, -29), 1)
        # jahitan tepi hood
        for i in range(5):
            _NS_sylara._aacircle(surface, p["cloth_high"],
                                 pt(-6 + i * 4, -40 + abs(i - 2)), 1)
        # anyaman korset & rivet sabuk
        for yy in (-14, -10, -6):
            _NS_sylara._aaline(surface, p["cloth_high"],
                               pt(-4, yy), pt(4, yy + 2), 1)
        for xx in (-6, 0, 6):
            _NS_sylara._aacircle(surface, p["gold_light"], pt(xx, 2), 1)
        # serat bulu fletching di quiver + kilau gesper bahu
        for i in range(3):
            _NS_sylara._aaline(surface, p["arrow_feather"],
                               pt(-15 - i * 3, -31 - i * 2),
                               pt(-18 - i * 3, -27 - i * 2), 1)
        _NS_sylara._aacircle(surface, p["gold_light"], pt(-9, -18), 1)
        # tali sepatu & lipatan sarung tangan
        for yy in (26, 31, 36):
            _NS_sylara._aaline(surface, p["leather_light"],
                               pt(7, yy), pt(12, yy), 1)


    # Buffer rig: cukup besar untuk cape, busur terentang, dan speed-line.
    RIG_W, RIG_H = 156, 136
    RIG_OX, RIG_OY = 66, 62


    def _draw_sylara_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, powered=False, detail=False):
        """Komposisi akhir: rig digambar ke buffer lalu diberi outline gelap
        1 px seperti sprite sheet referensi, baru di-blit ke arena."""
        buf = pygame.Surface((_NS_sylara.RIG_W, _NS_sylara.RIG_H),
                             pygame.SRCALPHA)
        _NS_sylara._draw_sylara_rig(buf, _NS_sylara.RIG_OX, _NS_sylara.RIG_OY,
                                    facing, phase, action, attack_progress,
                                    powered=powered, detail=detail)
        silhouette = buf.copy()
        silhouette.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        ox = int(cx) - _NS_sylara.RIG_OX
        oy = int(cy) - _NS_sylara.RIG_OY
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(silhouette, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))


    def _draw_sylara_rig(surface, cx, cy, facing, phase, action,
                         attack_progress=0.0, powered=False, detail=False):
        """Rig hand-authored meniru sprite sheet referensi Wind Ranger:
        hood hijau runcing, rambut merah berkibar, cape robek, korset
        kulit-hijau, quiver anak panah, dan busur recurve pose-driven."""
        p = _NS_sylara.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        windrun = action == "windrun"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.7)

        lean = (3 if walk else 0) * f
        if windrun:
            lean = 7 * f
        root_y = int(math.sin(phase * .72) * .7)
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if windrun:
            root_y += 2 - int(abs(math.sin(phase * 2.0)) * 2)
        if attack:
            lean = int(math.sin(ap * math.pi) * 3) * f
            root_y += int(math.sin(ap * math.pi) * 1.5)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                _NS_sylara._poly(surface, p["shadow_deep"],
                                 [(x + f, y + 1) for x, y in pts])
            _NS_sylara._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_sylara._aaline(surface, p["shadow_deep"], aa, bb, width + 3)
            _NS_sylara._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_sylara._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        wave = math.sin(phase * 1.15)
        wave2 = math.sin(phase * 1.45 + .8)
        # angin: cape & rambut terhempas lebih jauh saat bergerak/menembak
        gust = 0
        if walk:
            gust = 6
        elif windrun:
            gust = 16
        elif attack:
            gust = int(4 + 5 * math.sin(ap * math.pi))

        # ═══ CAPE: panel gelap sempit di punggung + tepi robek ═══
        cw = int(wave * 3)
        cw2 = int(wave2 * 2)
        poly(p["cloak_darkest"], [
            (-3, -34), (-8, -35),
            (-15 - gust, -24 + cw), (-20 - gust, -8 + cw),
            (-17 - int(gust * .8), 6 + cw2), (-11, 18 + cw2),
            (-4, 14), (-2, 0)])
        poly(p["cloak_dark"], [
            (-4, -32), (-8, -33),
            (-13 - gust, -22 + cw), (-17 - gust, -7 + cw),
            (-14 - int(gust * .8), 5 + cw2), (-9, 15 + cw2),
            (-4, 12), (-2, 0)], False)
        poly(p["cloak_mid"], [
            (-6, -29), (-8, -29),
            (-10 - int(gust * .6), -20 + cw), (-11 - gust, -8 + cw),
            (-9, 2 + cw2), (-6, 9 + cw2), (-5, 4)], False)
        # lipatan kain: garis vertikal supaya cape tidak jadi blok datar
        for i, (tx0, ty0, tx1, ty1) in enumerate((
                (-6, -28, -11 - gust, 2 + cw2),
                (-9, -26, -14 - gust, -1 + cw),
                (-12, -20, -16 - gust, 6 + cw2))):
            _NS_sylara._aaline(surface, p["cloak_darkest"],
                               pt(tx0, ty0), pt(tx1, ty1), 1)
        # tepi robek (segitiga bawah) - siluet khas referensi
        for i, (bx, by) in enumerate(((-16, 2), (-12, 8), (-7, 12))):
            tear = int(wave2 * (1 + i))
            poly(p["cloak_darkest"], [
                (bx - int(gust * .5), by + cw2),
                (bx + 5 - int(gust * .5), by + 2 + cw2),
                (bx + 1 - int(gust * .5), by + 11 + tear + cw2)], False)
        _NS_sylara._aaline(surface, p["cloak_light"],
                           pt(-6, -31), pt(-14 - gust, -6 + cw), 1)
        _NS_sylara._aaline(surface, p["cloak_light"],
                           pt(-14 - gust, -6 + cw), pt(-9, 12 + cw2), 1)

        # ═══ QUIVER di punggung + anak panah berbulu ═══
        poly(p["leather_darkest"], [(-6, -24), (-13, -30), (-19, -18),
                                    (-12, -8), (-6, -13)])
        poly(p["leather_dark"], [(-7, -24), (-12, -28), (-17, -18),
                                 (-11, -10), (-7, -14)], False)
        poly(p["leather_mid"], [(-9, -24), (-12, -27), (-15, -19),
                                (-11, -13)], False)
        _NS_sylara._aaline(surface, p["leather_light"],
                           pt(-13, -27), pt(-16, -19), 1)
        _NS_sylara._aaline(surface, p["gold_mid"], pt(-8, -22), pt(-16, -21), 2)
        for i, (ax, ay) in enumerate(((-13, -31), (-16, -29), (-10, -32))):
            sway = int(wave * (1 + i % 2))
            _NS_sylara._aaline(surface, p["arrow_shaft_d"],
                               pt(ax, ay), pt(ax - 4, ay - 9 + sway), 2)
            _NS_sylara._poly(surface, p["arrow_feather_d"], [
                pt(ax - 4, ay - 9 + sway), pt(ax - 8, ay - 6 + sway),
                pt(ax - 5, ay - 4 + sway)])
            _NS_sylara._poly(surface, p["arrow_feather"], [
                pt(ax - 4, ay - 9 + sway), pt(ax - 7, ay - 7 + sway),
                pt(ax - 5, ay - 5 + sway)])

        # ═══ RAMBUT BELAKANG: massa merah + helai berkibar ═══
        hw = int(wave * 2) + gust // 3
        poly(p["hair_darkest"], [(1, -42), (-5, -40), (-11 - hw, -33),
                                 (-14 - hw, -23), (-8, -18), (-3, -26),
                                 (-1, -34)])
        poly(p["hair_dark"], [(0, -40), (-4, -38), (-9 - hw, -32),
                              (-11 - hw, -24), (-6, -20), (-2, -27)], False)
        for i, (mx, my, ex, ey) in enumerate(((-5, -37, -14, -33),
                                              (-5, -32, -15, -25),
                                              (-4, -27, -12, -18))):
            sway = int(wave * (1 + i)) + gust // 3
            poly(p["hair_mid"], [(-1, -39), (mx - sway, my - 1),
                                 (ex - sway, ey), (ex - sway + 3, ey + 3),
                                 (mx - sway, my + 5)], False)
            _NS_sylara._aaline(surface, p["hair_light"],
                               pt(mx - sway, my + 1), pt(ex - sway, ey + 1), 1)
        _NS_sylara._aaline(surface, p["hair_shine"],
                           pt(-3, -38), pt(-10 - hw, -30), 1)

        # ═══ KAKI: paha ramping + boot kulit tinggi ═══
        leg_phase = stride if (walk or windrun) else 0.0
        if windrun:
            rear_foot = (-13 - int(leg_phase * 7), 38)
            front_foot = (14 + int(leg_phase * 8), 38)
        else:
            rear_foot = (-7 - int(leg_phase * 5), 40 - int(abs(leg_phase) * 2))
            front_foot = (9 + int(leg_phase * 6), 40)
        for hip, knee, foot, shade in (
                ((-6, 11), (-9, 26), rear_foot, p["cloth_darkest"]),
                ((6, 11), (9, 25), front_foot, p["cloth_dark"])):
            poly(shade, [hip, (hip[0] + 6, hip[1]),
                         (knee[0] + 4, knee[1]), (foot[0] + 4, foot[1] - 6),
                         (foot[0] - 4, foot[1] - 6), (knee[0] - 4, knee[1])])
            limb(knee, (foot[0], foot[1] - 6), 6,
                 p["leather_dark"], p["leather_mid"])
            # boot: sol + lipatan atas + tali
            poly(p["leather_darkest"], [(foot[0] - 5, foot[1] - 7),
                                        (foot[0] + 5, foot[1] - 7),
                                        (foot[0] + 6, foot[1] - 2),
                                        (foot[0] - 5, foot[1] - 2)])
            poly(p["leather_mid"], [(foot[0] - 4, foot[1] - 6),
                                    (foot[0] + 4, foot[1] - 6),
                                    (foot[0] + 5, foot[1] - 3),
                                    (foot[0] - 4, foot[1] - 3)], False)
            poly(p["leather_darkest"], [(foot[0] - 5, foot[1] - 2),
                                        (foot[0] + 7, foot[1] - 2),
                                        (foot[0] + 8, foot[1] + 1),
                                        (foot[0] - 5, foot[1] + 1)])
            _NS_sylara._aaline(surface, p["leather_light"],
                               pt(foot[0] - 3, foot[1] - 5),
                               pt(foot[0] + 4, foot[1] - 5), 1)
            _NS_sylara._aaline(surface, p["gold_mid"],
                               pt(knee[0] - 3, knee[1] + 1),
                               pt(knee[0] + 3, knee[1] + 1), 1)

        # ═══ ROK/TASSET hijau pendek berlapis ═══
        skirt = int(wave * 2) + gust // 3
        poly(p["cloth_darkest"], [(-8, 4), (8, 4), (10, 13),
                                  (4, 16), (-4, 16), (-9 - skirt, 12)])
        poly(p["cloth_dark"], [(-7, 5), (7, 5), (8, 12),
                               (3, 15), (-3, 15), (-7 - skirt, 11)], False)
        poly(p["cloth_mid"], [(-5, 6), (5, 6), (6, 11), (2, 13),
                              (-3, 13), (-5, 11)], False)
        for i, sx in enumerate((-6, -1, 4)):
            _NS_sylara._aaline(surface, p["cloth_light"],
                               pt(sx, 7), pt(sx - 1 - i, 14), 1)

        # ═══ TORSO: korset hijau + strap kulit + sabuk emas ═══
        poly(p["cloth_darkest"], [(-8, -19), (8, -21), (11, -9),
                                  (8, 5), (-7, 5), (-10, -8)])
        poly(p["cloth_dark"], [(-6, -18), (7, -19), (9, -9),
                               (7, 5), (-6, 5), (-8, -8)], False)
        poly(p["cloth_mid"], [(-4, -16), (6, -17), (8, -9),
                              (6, 3), (-4, 3), (-6, -8)], False)
        poly(p["cloth_light"], [(0, -15), (5, -15), (7, -9),
                                (4, -2), (0, -4)], False)
        poly(p["cloth_high"], [(2, -13), (5, -13), (5, -8), (2, -7)], False)
        # dada & garis leher V (ref)
        poly(p["skin_dark"], [(0, -19), (7, -20), (6, -14), (1, -13)], False)
        poly(p["skin_mid"], [(1, -18), (6, -19), (5, -15), (2, -14)], False)
        _NS_sylara._aaline(surface, p["cloth_darkest"], pt(0, -20), pt(4, -13), 2)
        # strap kulit menyilang
        _NS_sylara._aaline(surface, p["leather_darkest"], pt(-9, -17), pt(9, -2), 4)
        _NS_sylara._aaline(surface, p["leather_mid"], pt(-9, -17), pt(9, -2), 2)
        _NS_sylara._aaline(surface, p["leather_light"], pt(-8, -17), pt(8, -3), 1)
        # sabuk + gesper emas
        _NS_sylara._aaline(surface, p["leather_darkest"], pt(-10, 3), pt(10, 3), 6)
        _NS_sylara._aaline(surface, p["leather_dark"], pt(-10, 2), pt(10, 2), 4)
        _NS_sylara._rect(surface, p["gold_dark"], (pt(-3, 0)[0], pt(-3, 0)[1], 7, 6), 1)
        _NS_sylara._rect(surface, p["gold_mid"], (pt(-2, 1)[0], pt(-2, 1)[1], 5, 4), 1)
        _NS_sylara._rect(surface, p["gold_light"], (pt(-1, 2)[0], pt(-1, 2)[1], 2, 2))
        # pauldron kulit bahu belakang
        poly(p["leather_dark"], [(-7, -20), (-13, -18), (-14, -12),
                                 (-8, -11)], True)
        poly(p["leather_mid"], [(-8, -19), (-12, -17), (-12, -13),
                                (-9, -12)], False)
        _NS_sylara._aacircle(surface, p["gold_mid"], pt(-11, -15), 2)

        # bayangan leher supaya kepala tidak menyatu dengan torso
        _NS_sylara._aaline(surface, p["cloth_darkest"], pt(1, -22), pt(8, -23), 3)
        _NS_sylara._aaline(surface, p["skin_darkest"], pt(3, -24), pt(8, -25), 2)

        # ═══ POSE BUSUR & LENGAN ═══
        if attack:
            if ap < .45:
                t = ap / .45
                draw_amt = t * t * (3 - 2 * t)
                grip = (19 - int(t * 2), -14)
                tilt = .30 - t * .26
            elif ap < .58:
                t = (ap - .45) / .13
                draw_amt = max(0.0, 1.0 - t * 1.4)
                grip = (17 + int(t * 2), -14)
                tilt = .04
            else:
                t = (ap - .58) / .42
                draw_amt = 0.0
                grip = (19 - int(t * 3), -14 + int(t * 4))
                tilt = .04 + t * .40
        elif windrun:
            draw_amt = 0.0
            grip = (13, -2)
            tilt = 1.25
        else:
            draw_amt = 0.0
            grip = (17, -5 + int(wave))
            tilt = .26 + wave * .05

        # lengan belakang (penarik tali) digambar sebelum busur
        nock = _NS_sylara._bow_nock(grip, tilt, draw_amt)
        if attack and draw_amt > 0.05:
            rear_hand = (nock[0], nock[1])
            elbow = (rear_hand[0] - 7, rear_hand[1] + 7)
        elif windrun:
            rear_hand = (-9, 2)
            elbow = (-11, -6)
        else:
            rear_hand = (-8, 4 + int(wave))
            elbow = (-11, -5)
        limb((-6, -15), elbow, 6, p["cloth_dark"], p["cloth_mid"])
        limb(elbow, rear_hand, 5, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_sylara._aacircle(surface, p["leather_darkest"], (rhx, rhy), 3)
        _NS_sylara._aacircle(surface, p["leather_mid"], (rhx, rhy), 2)
        _NS_sylara._aacircle(surface, p["leather_light"], (rhx - f, rhy - 1), 1)

        # ═══ KEPALA: hood runcing, wajah, poni merah ═══
        # dome hood (belakang kepala) sedikit lebih besar dari tengkorak
        poly(p["hood_dark"], [(-1, -44), (5, -48), (13, -46), (16, -39),
                              (14, -32), (8, -28), (-1, -30), (-5, -37)])
        poly(p["hood_mid"], [(0, -43), (5, -46), (12, -44), (14, -38),
                             (12, -33), (7, -30), (0, -31), (-3, -37)], False)
        # puncak hood menjuntai ke belakang (ekor kain)
        peak = int(wave * 2) + gust // 4
        poly(p["hood_darkest"], [(0, -47), (4, -50), (-6, -50 + peak),
                                 (-16 - peak, -43 + peak), (-9, -40)])
        poly(p["hood_mid"], [(0, -46), (3, -48), (-6, -48 + peak),
                             (-13 - peak, -43 + peak), (-7, -40)], False)
        _NS_sylara._aaline(surface, p["hood_light"], pt(-1, -47),
                           pt(-12 - peak, -43 + peak), 1)
        # wajah
        poly(p["skin_dark"], [(2, -41), (12, -42), (15, -35),
                              (14, -28), (5, -26), (1, -33)])
        poly(p["skin_mid"], [(3, -40), (11, -41), (14, -35),
                             (12, -29), (6, -27), (2, -33)], False)
        poly(p["skin_light"], [(5, -39), (10, -39), (12, -34),
                               (9, -31), (5, -32)], False)
        # mata besar bergaya sprite
        ex, ey = pt(9, -34)
        _NS_sylara._rect(surface, p["eye_white"], (ex - 2, ey - 2, 6, 5))
        _NS_sylara._rect(surface, p["eye_iris"], (ex + 1, ey - 2, 3, 5))
        _NS_sylara._rect(surface, p["eye_iris_light"], (ex + 1, ey - 1, 2, 2))
        _NS_sylara._rect(surface, p["eye_pupil"], (ex + 2, ey - 1, 1, 3))
        _NS_sylara._rect(surface, p["white"], (ex + 3, ey - 2, 1, 1))
        _NS_sylara._aaline(surface, p["hair_darkest"], pt(7, -37), pt(13, -37), 1)
        # hidung + bibir
        _NS_sylara._aacircle(surface, p["skin_darkest"], pt(14, -32), 1)
        _NS_sylara._aaline(surface, p["lips_dark"], pt(11, -28), pt(13, -28), 1)
        # poni merah menyembul dari hood
        poly(p["hair_dark"], [(0, -43), (10, -44), (15, -39), (10, -38),
                              (4, -36), (-1, -38)], False)
        poly(p["hair_mid"], [(1, -42), (9, -43), (13, -39), (7, -38),
                             (2, -37)], False)
        _NS_sylara._aaline(surface, p["hair_shine"], pt(3, -42), pt(11, -41), 1)
        # brim hood: pita gelap lalu kilau kain, membingkai wajah
        _NS_sylara._aaline(surface, p["hood_darkest"], pt(-2, -43), pt(14, -45), 4)
        _NS_sylara._aaline(surface, p["hood_light"], pt(-1, -45), pt(14, -46), 2)
        _NS_sylara._aaline(surface, p["cloth_high"], pt(0, -45), pt(12, -46), 1)
        _NS_sylara._aacircle(surface, p["gold_mid"], pt(14, -43), 1)
        # helai rambut samping menutupi leher
        side_sway = int(wave * 2)
        poly(p["hair_dark"], [(1, -36), (-4, -35), (-9 - side_sway, -25),
                              (-4, -20), (0, -29)], False)
        _NS_sylara._aaline(surface, p["hair_light"],
                           pt(-1, -34), pt(-7 - side_sway, -24), 1)

        # ═══ LENGAN DEPAN + BUSUR ═══
        if attack:
            bow_hand = (grip[0] - 1, grip[1] + 1)
        elif windrun:
            bow_hand = (grip[0] - 1, grip[1] - 2)
        else:
            bow_hand = (grip[0] - 2, grip[1] + 1)
        f_elbow = ((bow_hand[0] + 6) // 2 + 2, (bow_hand[1] - 14) // 2 + 2)
        limb((6, -15), f_elbow, 6, p["cloth_mid"], p["cloth_light"])
        limb(f_elbow, bow_hand, 5, p["skin_mid"], p["skin_light"])
        # vambrace kulit lengan busur
        _NS_sylara._aaline(surface, p["leather_dark"],
                           pt(f_elbow[0], f_elbow[1]),
                           pt((f_elbow[0] + bow_hand[0]) // 2,
                              (f_elbow[1] + bow_hand[1]) // 2), 4)
        _NS_sylara._aaline(surface, p["leather_light"],
                           pt(f_elbow[0], f_elbow[1] - 1),
                           pt((f_elbow[0] + bow_hand[0]) // 2,
                              (f_elbow[1] + bow_hand[1]) // 2 - 1), 1)
        _NS_sylara._draw_elite_bow(surface, pt, f, grip, tilt, draw_amt,
                                   phase, powered=powered, detail=detail)
        bhx, bhy = pt(*bow_hand)
        _NS_sylara._aacircle(surface, p["leather_darkest"], (bhx, bhy), 3)
        _NS_sylara._aacircle(surface, p["leather_mid"], (bhx, bhy), 2)
        _NS_sylara._aacircle(surface, p["leather_light"], (bhx + f, bhy - 1), 1)

        # ═══ secondary motion: angin, jejak langkah, kilau tarikan ═══
        if walk or windrun:
            speed = 3 if windrun else 2
            for i in range(speed):
                sy = cy - 12 + i * 11 + root_y
                _NS_sylara._aaline(surface, (*p["wind_light"], 120 - i * 30),
                                   (cx - f * (26 + i * 8), sy),
                                   (cx - f * (12 + i * 5), sy - 1), 1)
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx2, fy2 = pt(planted[0], planted[1])
                for i in range(3):
                    _NS_sylara._aacircle(
                        surface, (*p["wind_mid"], max(20, int(140 * contact) - i * 40)),
                        (fx2 - f * (3 + i * 4), fy2 - i % 2), max(1, 3 - i))
        elif attack and draw_amt > .35:
            # energi angin terkumpul di tali saat tarikan penuh
            nx, ny = pt(*nock)
            for i in range(5):
                a = phase * 1.4 + i * math.pi * .4
                r = 4 + int(draw_amt * 7)
                _NS_sylara._aacircle(
                    surface, (*p["wind_bright"], int(190 * draw_amt)),
                    (nx + int(math.cos(a) * r), ny + int(math.sin(a) * r * .8)), 1)
        else:
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx = cx + int(math.sin(phase + i * 2.1) * (16 + i * 4))
                my = cy + 26 - int(t * 54)
                _NS_sylara._aacircle(surface,
                                     (*p["wind_light"], int(110 * (1 - t))),
                                     (mx, my), 1)

        if windrun and not detail:
            for i in range(6):
                a2 = phase * .7 + i * math.pi / 3
                r = 28 + int(math.sin(phase + i) * 6)
                _NS_sylara._aacircle(surface, (*p["wind_bright"], 150),
                                     (cx + int(math.cos(a2) * r),
                                      cy + int(math.sin(a2) * r * .45)), 1)

        if detail:
            _NS_sylara._draw_sylara_masterwork_details(surface, pt, f)



    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Wind mist beneath floating Sylara."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sylara.PALETTE["wind_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising wind wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha), (sx, sy), 5)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha), (sx, sy - 2), 3)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting leaves
        for i in range(3):
            angle = phase * 1.0 + i * math.pi * 2 / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_sylara._draw_leaf(surface, sx, sy, 3, angle,
                       _NS_sylara.PALETTE["cloth_dark"], _NS_sylara.PALETTE["cloth_mid"],
                       _NS_sylara.PALETTE["cloth_light"])

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_sylara.PALETTE["wind_darkest"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_ranger_silhouette_glow(surface, x, y, phase):
        """Subtle green rim light behind Sylara's hood, cape, and bow."""
        pulse = 0.72 + math.sin(phase * 1.25) * 0.15
        halo = pygame.Surface((104, 104), pygame.SRCALPHA)
        center = (52, 52)
        for radius, alpha in ((42, 9), (33, 14), (24, 21)):
            _NS_sylara._aacircle(halo,
                (*_NS_sylara.PALETTE["wind_dark"], int(alpha * pulse)),
                center, radius)
        # Echo the cape and bow line without softening the pixel silhouette.
        _NS_sylara._aaline(halo,
            (*_NS_sylara.PALETTE["wind_mid"], int(34 * pulse)),
            (28, 64), (14, 52), 2)
        _NS_sylara._aaline(halo,
            (*_NS_sylara.PALETTE["wind_mid"], int(30 * pulse)),
            (68, 51), (85, 38), 1)
        surface.blit(halo, (x - 52, y - 52))


    def _draw_wind_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sylara._aacircle(aura, (*_NS_sylara.PALETTE["wind_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_wind_platform(surface, x, y, phase, skill):
        """Wind circle platform with leaf pattern."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_mid"], 180),
                            (20, 14, 90, 16), 2)

        # Swirling wind streaks
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_sylara.PALETTE["wind_light"], 170),
                             (x1, y1), (x2, y2), 1)

        # Small leaves around ring
        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_sylara.PALETTE["wind_bright"], 200), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_bow_release_flash(surface, x, y, facing, progress):
        """Flash when releasing arrow."""
        # Flash occurs at release moment
        if progress < 0.55 or progress > 0.75:
            return
        t = (progress - 0.55) / 0.2
        intensity = math.sin(t * math.pi)

        flash_x = x + 22 * facing
        flash_y = y - 8

        alpha = int(200 * intensity)
        radius = int(4 + intensity * 12)

        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 4)
        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                  (flash_x, flash_y), radius)
        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], alpha),
                  (flash_x, flash_y), radius // 2)

        # Small streaks
        for i in range(4):
            angle = progress * 5 + i * math.pi / 2
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                    (flash_x, flash_y), (ex, ey), 1)


    # ===================================================================
    # SKILL Q: POWERSHOT (charging)
    # ===================================================================
    def _draw_powershot_charge(surface, boss, x, y, timer, phase):
        """Charging aura around boss."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        facing = boss.direction

        # Line indicator to target
        tx, ty = _NS_sylara._target_position(boss, x, y)
        for i in range(0, 100, 5):
            alpha = int(80 + math.sin(phase * 3 + i * 0.2) * 60)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                      (x + int((tx - x) * i / 100),
                       y + int((ty - y) * i / 100) - 8), 1)

        # Charging particles converging
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 30 - int(progress * 20)  # converge
            px = x + 22 * facing + int(math.cos(angle) * r)
            py = y - 8 + int(math.sin(angle) * r)
            alpha = int(200 * progress)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha), (px, py), 2)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], alpha), (px, py), 1)


    # ===================================================================
    # SKILL W: WINDRUN
    # ===================================================================
    def _draw_windrun_ground(surface, boss, x, y, timer, phase):
        """Ground effect during windrun."""
        facing = boss.direction
        # Speed lines on ground
        for i in range(6):
            off = (i - 3) * 6
            sx = x - facing * 20
            sy = y + 30 + off
            ex = sx - facing * 40
            alpha = 200 - i * 20
            _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                    (sx, sy), (ex, sy), 1)


    def _draw_windrun_trail(surface, x, y, facing, phase):
        """After-image trail behind Sylara during windrun."""
        for i in range(5):
            offset = (i + 1) * 8 * facing
            alpha = 180 - i * 30
            # Ghost silhouette
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha // 2),
                      (x - offset, y - 10), 14)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha),
                      (x - offset, y - 5), 10)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_light"], alpha),
                      (x - offset, y - 8), 6)

        # Wind swirls around Sylara
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 25
            px = x + int(math.cos(angle) * r)
            py = y - 5 + int(math.sin(angle) * r * 0.5)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], 200), (px, py), 3)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], 220), (px, py), 1)

        # Horizontal speed streaks
        for i in range(6):
            sy = y + (i - 3) * 6
            sx = x - facing * 20
            ex = sx - facing * 30
            alpha = 200 - i * 15
            _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_light"], alpha),
                    (sx, sy), (ex, sy), 1)


    # ===================================================================
    # SKILL E: SHACKLE SHOT
    # ===================================================================
    def _draw_shackle_ground(surface, boss, x, y, timer, pulse):
        """Line indicator to target for shackle shot."""
        tx, ty = _NS_sylara._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 150))

        # Dashed line indicator
        steps = 20
        for i in range(steps):
            if i % 2 == 0:
                t1 = i / steps
                t2 = (i + 1) / steps
                x1 = x + (tx - x) * t1
                y1 = y + (ty - y) * t1 - 5
                x2 = x + (tx - x) * t2
                y2 = y + (ty - y) * t2 - 5
                _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_bright"], 150),
                        (x1, y1), (x2, y2), 2)

        # Spawn shackle projectile at start
        if not getattr(boss, "_sy_shackle_spawned", False):
            _NS_sylara._spawn_shackle(boss, x, y)
            boss._sy_shackle_spawned = True
        if timer < 5:
            boss._sy_shackle_spawned = False


    # ===================================================================
    # SKILL R: FOCUS FIRE (ultimate)
    # ===================================================================
    def _draw_focus_fire_ground(surface, boss, x, y, timer, phase):
        """Ground rune for focus fire."""
        progress = max(0.0, min(1.0, 1 - timer / 180))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(40 + progress * 15)

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_mid"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_bright"], int(200 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runic marks
        for i in range(6):
            a = phase * 0.5 + i * math.pi / 3
            px = cx + int(math.cos(a) * (radius - 3))
            py = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.circle(ring, (*_NS_sylara.PALETTE["wind_white"], 240), (px, py), 3)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_focus_fire_effect(surface, boss, x, y, timer, phase):
        """Rapid arrow volley animation."""
        progress = max(0.0, min(1.0, 1 - timer / 180))

        # Fire arrows in bursts
        fire_interval = 8  # every 8 frames
        if not hasattr(boss, "_sy_focus_last_shot"):
            boss._sy_focus_last_shot = -100

        if progress > 0.2 and progress < 0.9:
            if timer % fire_interval == 0 and boss._sy_focus_last_shot != timer:
                _NS_sylara._spawn_focus_fire_volley(boss, x, y)
                boss._sy_focus_last_shot = timer

        if progress < 0.2:
            boss._sy_focus_last_shot = -100

        # Energy aura around boss (channeling)
        for i in range(10):
            angle = phase * 3 + i * math.pi / 5
            r = 25 + int(math.sin(phase * 2 + i) * 5)
            px = x + int(math.cos(angle) * r)
            py = y - 10 + int(math.sin(angle) * r * 0.6)
            alpha = int(200 + math.sin(phase * 2 + i) * 55)
            alpha = max(0, min(255, alpha))
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha), (px, py), 3)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], alpha), (px, py), 1)

        # Wind spirals
        for i in range(3):
            angle_start = phase * 2 + i * math.pi * 2 / 3
            _NS_sylara._draw_wind_arc(surface, x, y - 10, 30, angle_start,
                           angle_start + math.pi * 1.4,
                           (*_NS_sylara.PALETTE["wind_bright"], 200), width=2, segments=10)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_sylara.draw_sylara(surface, boss, x, y)

# ====================================================================
# kaizen.py
# ====================================================================
class _NS_kaizen:
    """Namespace kaizen - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Yasuo inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin
        "skin_darkest":   (135,  85,  60),
        "skin_dark":      (185, 130,  95),
        "skin_mid":       (220, 170, 135),
        "skin_light":     (240, 200, 165),
        "skin_high":      (250, 220, 190),

        # Hair (dark brown)
        "hair_darkest":   ( 30,  20,  15),
        "hair_dark":      ( 55,  35,  25),
        "hair_mid":       ( 85,  55,  35),
        "hair_light":     (120,  80,  55),
        "hair_shine":     (155, 110,  75),

        # Outfit - blue/dark
        "cloth_darkest":  ( 15,  20,  40),
        "cloth_dark":     ( 30,  45,  85),
        "cloth_mid":      ( 55,  80, 145),
        "cloth_light":    ( 90, 130, 200),
        "cloth_high":     (140, 180, 235),

        # Scarf/sash - brighter blue
        "scarf_dark":     ( 40,  70, 140),
        "scarf_mid":      ( 75, 120, 200),
        "scarf_light":    (130, 175, 240),
        "scarf_high":     (185, 215, 255),

        # Pants - darker
        "pants_dark":     ( 20,  30,  60),
        "pants_mid":      ( 40,  55, 105),
        "pants_light":    ( 70,  95, 155),

        # Leather belt/straps
        "leather_dark":   ( 55,  35,  20),
        "leather_mid":    ( 95,  65,  40),
        "leather_light":  (140, 100,  65),

        # Sword - katana
        "steel_darkest":  ( 40,  50,  65),
        "steel_dark":     ( 90, 105, 125),
        "steel_mid":      (155, 170, 190),
        "steel_light":    (210, 220, 235),
        "steel_shine":    (245, 250, 255),

        # Handle wrap
        "wrap_dark":      ( 55,  20,  25),
        "wrap_mid":       (110,  40,  50),
        "wrap_light":     (165,  70,  85),

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),

        # Wind - light cyan/white
        "wind_darkest":   ( 30,  60, 110),
        "wind_dark":      ( 55, 110, 175),
        "wind_mid":       (110, 175, 230),
        "wind_light":     (175, 220, 250),
        "wind_bright":    (215, 240, 255),
        "wind_white":     (245, 252, 255),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       (200, 150,  50),
        "eye_iris_light": (240, 200, 100),
        "eye_pupil":      ( 15,  15,  20),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaizen._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_kaizen.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaizen._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_kaizen._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_kaizen._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_kaizen._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_kaizen._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 150 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Wind visual helpers
    # ---------------------------------------------------------------------------
    def _draw_wind_arc(surface, cx, cy, radius, start_angle, end_angle,
                       color, width=2, segments=12):
        """Curved wind arc."""
        points = []
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius
            points.append((px, py))
        for i in range(len(points) - 1):
            _NS_kaizen._aaline(surface, color, points[i], points[i + 1], width)


    def _draw_wind_swirl(surface, cx, cy, size, phase, color=None, alpha=200):
        """Small wind swirl."""
        if color is None:
            color = _NS_kaizen.PALETTE["wind_bright"]
        col = (*color, alpha) if len(color) == 3 else color
        for i in range(3):
            angle_start = phase * 0.8 + i * math.pi * 2 / 3
            angle_end = angle_start + math.pi * 1.2
            _NS_kaizen._draw_wind_arc(surface, cx, cy, size, angle_start, angle_end,
                           col, width=1, segments=8)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Steel Wind Slash (Q ranged projectile)
    # ---------------------------------------------------------------------------
    class WindSlashProjectile:
        """Crescent wind slash projectile (Steel Wind)."""
        def __init__(self, sx, sy, tx, ty, speed=8.0,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_kaizen._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha), (tx, ty), r + 2)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Glow behind slash
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], 100), (px, py), 16)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], 150), (px, py), 11)

                # Crescent slash shape - perpendicular to travel direction
                perp = self.angle + math.pi / 2
                arc_radius = 14
                # Draw crescent as thick arc
                for offset in range(-2, 3):
                    width = 3 - abs(offset)
                    if width <= 0:
                        continue
                    if offset == 0:
                        color = _NS_kaizen.PALETTE["wind_white"]
                    elif abs(offset) == 1:
                        color = _NS_kaizen.PALETTE["wind_bright"]
                    else:
                        color = _NS_kaizen.PALETTE["wind_light"]
                    _NS_kaizen._draw_wind_arc(surface, px, py, arc_radius + offset,
                                   perp - 1.1, perp + 1.1,
                                   color, width=width, segments=10)

                # Tips of crescent - sharp points
                tip1_x = px + math.cos(perp - 1.1) * arc_radius
                tip1_y = py + math.sin(perp - 1.1) * arc_radius
                tip2_x = px + math.cos(perp + 1.1) * arc_radius
                tip2_y = py + math.sin(perp + 1.1) * arc_radius
                _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["wind_white"],
                          (int(tip1_x), int(tip1_y)), 2)
                _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["wind_white"],
                          (int(tip2_x), int(tip2_y)), 2)

                # Speed lines
                for i in range(3):
                    offset = (i - 1) * 5
                    sx1 = px - math.cos(self.angle) * (8 + i * 2) + math.cos(perp) * offset
                    sy1 = py - math.sin(self.angle) * (8 + i * 2) + math.sin(perp) * offset
                    sx2 = sx1 - math.cos(self.angle) * 6
                    sy2 = sy1 - math.sin(self.angle) * 6
                    _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], 180),
                            (sx1, sy1), (sx2, sy2), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_kz_last_x"):
            boss._kz_last_x = boss.x
            boss._kz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kz_last_x)
        dy = abs(boss.y - boss._kz_last_y)
        boss._kz_last_x = boss.x
        boss._kz_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kz_prev_timer", -1))
        active = bool(getattr(boss, "_kz_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._kz_attack_active = True
            active = True

        if active and timer <= 0:
            boss._kz_attack_active = False
            active = False

        boss._kz_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._kz_attack_frame = max(0, cooldown - timer) if active else 0
        boss._kz_attack_progress = (
            min(1.0, boss._kz_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_kz_projectiles"):
            boss._kz_projectiles = []
        for proj in boss._kz_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._kz_projectiles = [p for p in boss._kz_projectiles if p.alive or p.dead_frames < 8]


    def _spawn_wind_slash(boss, x, y):
        if not hasattr(boss, "_kz_projectiles"):
            boss._kz_projectiles = []
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 24 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)
        proj = _NS_kaizen.WindSlashProjectile(
            sx, sy, tx, ty, speed=8.0,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._kz_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_kaizen(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaizen._detect_moving(boss)
        _NS_kaizen._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_kz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # ---------- Background layers ----------
        # Portrait LOD intentionally omits arena-sized aura/platform. This
        # lets auto-crop fill the portrait with Kaizen's face and materials
        # instead of shrinking him to include a 180 px effect circle.
        if not portrait_hd:
            _NS_kaizen._draw_swordsman_rim_light(surface, x, y - 10, pulse)
            _NS_kaizen._draw_wind_aura(surface, x, y, pulse)
            _NS_kaizen._draw_wind_platform(
                surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_kaizen._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizen._draw_sweep_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizen._draw_tornado_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_kaizen._draw_kaizen_attack(surface, boss, x, y)
        elif moving:
            _NS_kaizen._draw_kaizen_walk(surface, boss, x, y)
        else:
            _NS_kaizen._draw_kaizen_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        if not portrait_hd:
            _NS_kaizen._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_kaizen._draw_dash_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaizen._draw_wind_wall(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizen._draw_sweep_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizen._draw_tornado(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_kaizen_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x, y + 48)
            _NS_kaizen._draw_floating_wind(surface, x, y + 35, boss.pulse)
        _NS_kaizen._draw_kaizen_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_kaizen_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x + sway, y + 48)
            _NS_kaizen._draw_floating_wind(
                surface, x + sway, y + 35, phase, trail=True,
                facing=boss.direction)
        _NS_kaizen._draw_kaizen_body(
            surface, x + sway, y - bob, boss.direction, phase, "walk",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_kaizen_attack(surface, boss, x, y):
        progress = getattr(boss, "_kz_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn wind slash projectile at mid-swing (ranged variant)
        range_val = getattr(boss, "range", 150)
        is_ranged = range_val > 80

        if is_ranged:
            if 0.45 < progress < 0.55 and not getattr(boss, "_kz_proj_spawned", False):
                _NS_kaizen._spawn_wind_slash(boss, x, y)
                boss._kz_proj_spawned = True
            if progress < 0.15 or progress > 0.9:
                boss._kz_proj_spawned = False

        # Slight step forward during swing
        step = int(math.sin(progress * math.pi) * 3) * boss.direction
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x + step, y + 48)
            _NS_kaizen._draw_floating_wind(
                surface, x + step, y + 35, boss.pulse, intense=True)
        _NS_kaizen._draw_kaizen_body(
            surface, x + step, y, boss.direction, boss.pulse,
            "attack", progress, getattr(boss, "_portrait_hd", False))


    # ===================================================================
    # BODY RENDERING - HD samurai
    # ===================================================================
    def _draw_kaizen_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, detail=False):
        """Renderer tubuh Kaizen kualitas maksimum, 100% procedural.

        Dibangun sebagai bone rig 2D berlapis: setiap pose mengubah lean,
        langkah, sendi tangan, arah katana, rambut, dan scarf. Tidak ada PNG,
        sprite sheet, ataupun image.load. Efek skill lama tetap kompatibel.
        """
        _NS_kaizen._draw_kaizen_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail)


    def _draw_kaizen_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False):
        """Hand-authored pixel-art rig memakai primitive pygame saja."""
        p = _NS_kaizen.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        stride = math.sin(phase * 1.7)
        lean = (3 if walk else 0) * f
        # Whole-body root motion: breathing, planted walk bounce, then a
        # compressed wind-up / explosive attack lunge. Because every layer
        # uses pt(), hair, face, armor and limbs remain attached to the rig.
        root_y = int(math.sin(phase * .72) * .7)
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if attack:
            ap = max(0.0, min(1.0, attack_progress))
            lean = int(math.sin(ap * math.pi) * 7) * f
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                _NS_kaizen._poly(surface, p["shadow_deep"],
                                  [(x + f, y + 1) for x, y in pts])
            _NS_kaizen._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_kaizen._aaline(surface, p["shadow_deep"], aa, bb, width + 3)
            _NS_kaizen._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_kaizen._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        # ── back hair: seven independently animated, tapered locks ──
        hair_wave = math.sin(phase * 1.25)
        tail_root = (-7, -34)
        # Broad ponytail mass first, then separate pointed locks. This avoids
        # the "thin broom" silhouette common in primitive-only renderers.
        hw = int(hair_wave * 2)
        poly(p["hair_darkest"], [(-5, -35), (-12, -48), (-24, -57 + hw),
             (-21, -48 + hw), (-38, -51 + hw), (-29, -40 + hw),
             (-45, -37 + hw), (-29, -31 + hw), (-41, -22 + hw),
             (-21, -25 + hw), (-11, -30)])
        poly(p["hair_dark"], [(-8, -36), (-14, -46), (-23, -53 + hw),
             (-21, -44 + hw), (-34, -47 + hw), (-27, -38 + hw),
             (-39, -36 + hw), (-25, -32 + hw), (-34, -26 + hw),
             (-18, -28 + hw)], False)
        poly(p["hair_mid"], [(-14, -43), (-22, -49 + hw),
             (-20, -42 + hw), (-31, -43 + hw), (-24, -37 + hw)], False)
        locks = [(-16, -47, -34, -42), (-17, -43, -39, -35),
                 (-16, -39, -38, -27), (-13, -36, -33, -20),
                 (-10, -34, -25, -16), (-15, -46, -29, -51),
                 (-11, -49, -20, -57)]
        for i, (mx, my, ex, ey) in enumerate(locks):
            wave = int(hair_wave * (2 + i % 3))
            shape = [tail_root, (mx, my + wave), (ex, ey + wave),
                     (mx - 2, my + 5 + wave), (-8, -30)]
            poly(p["hair_darkest"], shape)
            inner = [(-8, -34), (mx, my + 1 + wave),
                     (ex + 3, ey + 1 + wave), (mx + 1, my + 4 + wave)]
            poly(p["hair_dark"], inner, False)
            a, b = pt(mx + 1, my + 1 + wave), pt(ex + 4, ey + 1 + wave)
            _NS_kaizen._aaline(surface, p["hair_mid"], a, b, 1)

        # ── scarf tails behind torso ──
        scarf_wave = int(math.sin(phase * 1.45) * 3)
        scarf_boost = 7 if walk or attack else 0
        poly(p["scarf_dark"], [(-5, -25), (-12, -22),
             (-26 - scarf_boost, -17 + scarf_wave),
             (-39 - scarf_boost, -7 + scarf_wave),
             (-28, -5), (-14, -13)])
        poly(p["scarf_mid"], [(-7, -23), (-15, -20),
             (-29 - scarf_boost, -11 + scarf_wave),
             (-35 - scarf_boost, -8 + scarf_wave), (-24, -7), (-12, -16)],
             False)
        _NS_kaizen._aaline(surface, p["scarf_light"], pt(-12, -20),
                           pt(-31 - scarf_boost, -9 + scarf_wave), 2)

        # ── lacquered saya behind hip ──
        limb((-7, 7), (-31, 29), 7, (104, 27, 39), (190, 62, 70))
        _NS_kaizen._aacircle(surface, p["gold_mid"], pt(-31, 29), 3)

        # ── legs: true split stance, not one floating robe mass ──
        leg_phase = stride if walk else 0.0
        rear_foot = (-8 - int(leg_phase * 5), 40 - int(abs(leg_phase) * 2))
        front_foot = (11 + int(leg_phase * 6), 40)
        for hip, knee, foot, shade in (
                ((-5, 12), (-9, 27), rear_foot, p["pants_dark"]),
                ((6, 12), (9, 26), front_foot, p["pants_mid"])):
            poly(shade, [hip, (hip[0] + 7, hip[1]),
                         (knee[0] + 5, knee[1]), (foot[0] + 4, foot[1] - 5),
                         (foot[0] - 4, foot[1] - 5),
                         (knee[0] - 4, knee[1])])
            # shin wrap / tabi
            poly((204, 211, 216), [(foot[0] - 4, foot[1] - 10),
                 (foot[0] + 4, foot[1] - 10), (foot[0] + 4, foot[1] - 4),
                 (foot[0] - 4, foot[1] - 4)], False)
            poly(p["leather_dark"], [(foot[0] - 5, foot[1] - 4),
                 (foot[0] + 7, foot[1] - 4), (foot[0] + 8, foot[1]),
                 (foot[0] - 5, foot[1])])
            _NS_kaizen._aaline(surface, p["leather_light"],
                               pt(foot[0] - 3, foot[1] - 3),
                               pt(foot[0] + 5, foot[1] - 3), 1)

        # Wide hakama panels keep volume while the feet remain readable.
        poly(p["pants_dark"], [(-12, 5), (0, 7), (-2, 29),
                               (-13, 30), (-17, 22)])
        poly(p["pants_mid"], [(0, 7), (12, 5), (17, 22),
                              (4, 29), (1, 18)])
        poly(p["pants_light"], [(3, 9), (10, 8), (13, 21),
                                (6, 25)], False)
        for dx in (-8, 5, 12):
            _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(dx, 10),
                               pt(dx + (1 if dx > 0 else -1), 25), 1)

        # ── torso: asymmetric open jacket + leather harness ──
        poly(p["cloth_darkest"], [(-13, -17), (7, -20), (15, -10),
             (12, 9), (2, 14), (-12, 8), (-16, -6)])
        poly(p["cloth_mid"], [(-11, -15), (-2, -18), (-1, 10),
                              (-10, 7), (-13, -5)], False)
        poly(p["skin_dark"], [(-2, -18), (7, -18), (10, -9),
                              (5, 8), (-1, 9)], False)
        poly(p["skin_mid"], [(0, -16), (6, -16), (8, -8),
                             (4, 5), (0, 7)], False)
        _NS_kaizen._aaline(surface, p["leather_dark"], pt(-10, -14),
                           pt(10, 5), 5)
        _NS_kaizen._aaline(surface, p["leather_light"], pt(-10, -14),
                           pt(10, 5), 1)
        # braided obi
        _NS_kaizen._aaline(surface, p["gold_dark"], pt(-13, 7), pt(13, 7), 5)
        for dx in range(-10, 11, 4):
            _NS_kaizen._aaline(surface, p["gold_light"], pt(dx - 1, 5),
                               pt(dx + 1, 9), 1)

        # Layered steel-and-lacquer pauldron on the sword shoulder. Separate
        # lames, rivets and a cold rim turn the upper body into a readable
        # armored silhouette rather than a single blue polygon.
        pauldron = [(7, -18), (13, -20), (19, -15), (18, -8),
                    (13, -5), (8, -9)]
        poly(p["steel_darkest"], pauldron)
        poly(p["cloth_mid"], [(9, -17), (13, -18), (17, -14),
                              (16, -10), (12, -8), (9, -10)], False)
        for i in range(3):
            yy = -15 + i * 3
            _NS_kaizen._aaline(surface, p["cloth_light"],
                               pt(10, yy), pt(17 - i, yy + 1), 1)
        _NS_kaizen._aacircle(surface, p["gold_mid"], pt(12, -15), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"], pt(12, -16), 1)

        # Jacket piping, stitches, and small wind crest.
        _NS_kaizen._aaline(surface, p["cloth_high"], pt(-11, -13),
                           pt(-10, 4), 1)
        for yy in (-9, -4, 1):
            _NS_kaizen._aaline(surface, p["scarf_light"],
                               pt(-12, yy), pt(-9, yy + 1), 1)
        _NS_kaizen._draw_wind_arc(surface, *pt(-5, -5), 4, .3, 4.4,
                                   p["wind_mid"], 1, 7)

        # ── rear arm / bracer ──
        if attack:
            prog = max(0.0, min(1.0, attack_progress))
            rear_hand = (-2 + int(prog * 8), -3)
        else:
            rear_hand = (-14, 5)
        limb((-10, -12), (-16, -2), 7, p["cloth_dark"], p["cloth_light"])
        limb((-16, -2), rear_hand, 6, p["skin_dark"], p["skin_light"])
        rhx, rhy = pt(*rear_hand)
        _NS_kaizen._rect(surface, p["wrap_dark"],
                         (rhx - 4, rhy - 4, 8, 8), 2)
        _NS_kaizen._aaline(surface, p["wrap_light"],
                           (rhx - 3, rhy - 2), (rhx + 3, rhy + 1), 1)
        _NS_kaizen._aaline(surface, p["gold_mid"],
                           (rhx - 3, rhy + 2), (rhx + 3, rhy + 2), 1)

        # ── neck and three-quarter head ──
        poly(p["skin_dark"], [(-3, -23), (5, -23), (5, -16), (-3, -16)])
        face = [(-8, -42), (4, -44), (10, -38), (11, -31),
                (7, -23), (1, -20), (-6, -24), (-10, -33)]
        poly(p["skin_dark"], face)
        poly(p["skin_mid"], [(-6, -40), (3, -42), (8, -37),
             (9, -32), (6, -25), (1, -22), (-4, -25), (-7, -33)], False)
        poly(p["skin_light"], [(1, -40), (6, -37), (7, -33),
                               (3, -29), (-1, -31)], False)
        # nose, eye, brow, scar, mouth
        poly(p["skin_light"], [(8, -35), (13, -33), (8, -31)], False)
        _NS_kaizen._aaline(surface, p["hair_darkest"], pt(2, -36), pt(8, -35), 2)
        _NS_kaizen._rect(surface, p["eye_iris_light"],
                         (pt(6, -34)[0], pt(6, -34)[1], 2, 2))
        _NS_kaizen._aaline(surface, (120, 48, 47), pt(-1, -33), pt(7, -27), 1)
        _NS_kaizen._aaline(surface, p["skin_darkest"], pt(4, -25), pt(8, -26), 1)
        _NS_kaizen._aacircle(surface, p["gold_light"], pt(-8, -27), 2)

        # ── hair cap and crown spikes ──
        poly(p["hair_darkest"], [(-10, -42), (-8, -50), (-3, -47),
             (0, -54), (4, -48), (10, -49), (8, -43), (12, -40),
             (6, -38), (1, -41), (-4, -38), (-9, -34)])
        poly(p["hair_dark"], [(-7, -43), (-6, -48), (-2, -45),
             (0, -51), (3, -46), (7, -47), (6, -42), (9, -40),
             (4, -40), (1, -43), (-4, -40)], False)
        _NS_kaizen._aaline(surface, p["hair_light"], pt(-3, -46), pt(0, -50), 1)
        # Narrow hachimaki under the fringe, with an embossed wind bead.
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(-8, -40),
                           pt(8, -39), 4)
        _NS_kaizen._aaline(surface, p["scarf_mid"], pt(-7, -41),
                           pt(8, -40), 2)
        _NS_kaizen._aacircle(surface, p["wind_dark"], pt(5, -40), 2)
        _NS_kaizen._aacircle(surface, p["wind_light"], pt(5, -41), 1)

        # Scarf collar sits above neck and anchors the long tail.
        poly(p["scarf_dark"], [(-10, -24), (-7, -29), (7, -25),
             (10, -20), (5, -16), (-7, -17)])
        poly(p["scarf_mid"], [(-8, -24), (-5, -27), (6, -24),
             (8, -21), (4, -19), (-6, -19)], False)
        _NS_kaizen._aaline(surface, p["scarf_high"], pt(-5, -25), pt(6, -22), 1)

        # ── sword arm and katana, pose-driven ──
        if attack:
            prog = max(0.0, min(1.0, attack_progress))
            if prog < .28:       # wind-up behind head
                t = prog / .28
                hand = (10, -7 - int(t * 8))
                angle = -2.15 + t * .45
            elif prog < .62:     # fast horizontal cut
                t = (prog - .28) / .34
                hand = (12 + int(t * 8), -13 + int(t * 12))
                angle = -1.70 + t * 1.85
            else:                # low recovery
                t = (prog - .62) / .38
                hand = (20 - int(t * 7), -1 + int(t * 10))
                angle = .15 + t * .65
        else:
            hand = (15, 1)
            angle = .72
        elbow = ((hand[0] + 10) // 2, (hand[1] - 10) // 2)
        limb((10, -12), elbow, 8, p["cloth_mid"], p["cloth_high"])
        limb(elbow, hand, 7, p["skin_dark"], p["skin_light"])
        _NS_kaizen._draw_elite_katana(surface, cx + lean, cy, f,
                                      hand, angle, phase, attack)

        # Small wind crest and armor rivets remain legible at 50 px.
        _NS_kaizen._draw_wind_arc(surface, *pt(2, 17), 5, .2, 4.6,
                                   p["wind_light"], 1, 8)
        for dx, dy in ((-10, -9), (-8, -4), (10, -7)):
            _NS_kaizen._aacircle(surface, p["gold_mid"], pt(dx, dy), 1)

        # ── secondary motion / contact feedback ──
        if walk:
            # Dust appears only near footfall (|stride| close to one), while
            # speed lines trail opposite the facing direction.
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx, fy = pt(planted[0], planted[1])
                alpha = int(150 * contact)
                for i in range(4):
                    _NS_kaizen._aacircle(
                        surface, (*p["wind_mid"], max(15, alpha - i * 24)),
                        (fx - f * (3 + i * 3), fy - i % 2), max(1, 3 - i // 2))
            for i in range(3):
                sy = cy - 7 + i * 9 + root_y
                _NS_kaizen._aaline(surface, (*p["wind_light"], 95 - i * 18),
                                   (cx - f * (25 + i * 7), sy),
                                   (cx - f * (12 + i * 5), sy - 1), 1)
        elif attack:
            ap = max(0.0, min(1.0, attack_progress))
            impact = max(0.0, 1.0 - abs(ap - .52) / .18)
            if impact > 0:
                ix, iy = pt(47, -3)
                for i in range(6):
                    ang = -1.2 + i * .48
                    length = 5 + int(impact * (8 + i % 2 * 4))
                    _NS_kaizen._aaline(surface,
                                       (*p["wind_white"], int(220 * impact)),
                                       (ix, iy),
                                       (ix + math.cos(ang) * length * f,
                                        iy + math.sin(ang) * length),
                                       1 if i % 2 else 2)
        else:
            # Quiet idle motes make breathing visible without obscuring face.
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx = cx + int(math.sin(phase + i * 2.1) * (18 + i * 3))
                my = cy + 28 - int(t * 58)
                _NS_kaizen._aacircle(surface,
                                     (*p["wind_bright"], int(110 * (1 - t))),
                                     (mx, my), 1)

        if detail:
            # Portrait-only micro-detail. At arena scale these marks would
            # collapse into noise, so LOD keeps them out of gameplay cache.
            # Hair fibre groups
            for i in range(5):
                _NS_kaizen._aaline(
                    surface, p["hair_light"],
                    pt(-13 - i * 3, -43 + i * 3),
                    pt(-24 - i * 3, -45 + i * 5), 1)
            # Face planes, lower eyelid and lip highlight
            _NS_kaizen._aaline(surface, p["skin_high"],
                               pt(2, -39), pt(6, -37), 1)
            _NS_kaizen._aaline(surface, p["skin_darkest"],
                               pt(3, -32), pt(8, -31), 1)
            _NS_kaizen._aaline(surface, p["skin_light"],
                               pt(5, -24), pt(8, -25), 1)
            # Fine textile weave and hakama hem stitching
            for yy in (-11, -6, -1):
                _NS_kaizen._aaline(surface, p["cloth_light"],
                                   pt(-9, yy), pt(-5, yy + 2), 1)
            for xx in (-10, -5, 5, 10):
                _NS_kaizen._aacircle(surface, p["scarf_light"],
                                      pt(xx, 24), 1)
            # Engraved pauldron fan and tiny reflected rivet glints
            for a in (-.7, -.2, .3):
                _NS_kaizen._aaline(surface, p["steel_mid"], pt(12, -13),
                                   pt(12 + math.cos(a) * 5,
                                      -13 + math.sin(a) * 5), 1)
            _NS_kaizen._aacircle(surface, p["wind_white"], pt(13, -16), 1)


    def _draw_elite_katana(surface, cx, cy, facing, hand, angle, phase,
                           attacking=False):
        """Procedural katana with curved silhouette, hamon, and slash arc."""
        p = _NS_kaizen.PALETTE
        f = 1 if facing >= 0 else -1
        hx, hy = cx + hand[0] * f, cy + hand[1]
        length = 42
        ux, uy = math.cos(angle) * f, math.sin(angle)
        tx, ty = hx + ux * length, hy + uy * length
        px, py = -uy, ux
        # wrapped grip behind guard
        ex, ey = hx - ux * 12, hy - uy * 12
        _NS_kaizen._aaline(surface, p["shadow_deep"], (hx, hy), (ex, ey), 7)
        _NS_kaizen._aaline(surface, p["wrap_mid"], (hx, hy), (ex, ey), 4)
        for t in (.25, .55, .85):
            wx, wy = hx - ux * 12 * t, hy - uy * 12 * t
            _NS_kaizen._aaline(surface, p["wrap_light"],
                               (wx - px * 2, wy - py * 2),
                               (wx + px * 2, wy + py * 2), 1)
        _NS_kaizen._aaline(surface, p["gold_dark"],
                           (hx - px * 6, hy - py * 6),
                           (hx + px * 6, hy + py * 6), 4)
        _NS_kaizen._aaline(surface, p["gold_light"],
                           (hx - px * 5, hy - py * 5),
                           (hx + px * 5, hy + py * 5), 1)
        # subtly curved blade polygon
        mx, my = hx + ux * 23 + px * 2, hy + uy * 23 + py * 2
        blade = [(hx + px * 3, hy + py * 3),
                 (mx + px * 2, my + py * 2), (tx, ty),
                 (mx - px, my - py), (hx - px * 2, hy - py * 2)]
        _NS_kaizen._poly(surface, p["shadow_deep"],
                          [(x + f, y + 1) for x, y in blade])
        _NS_kaizen._poly(surface, p["steel_dark"], blade)
        _NS_kaizen._aaline(surface, p["steel_shine"],
                           (hx + px * 2, hy + py * 2), (tx, ty), 2)
        # wavy temper line
        hamon = []
        for i in range(1, 8):
            t = i / 8.0
            wave = math.sin(i * math.pi * .72 + phase * .2) * .8
            hamon.append((hx + ux * length * t + px * wave,
                          hy + uy * length * t + py * wave))
        if len(hamon) > 1:
            pygame.draw.aalines(surface, p["wind_mid"], False, hamon)
        _NS_kaizen._aacircle(surface, p["steel_shine"], (int(tx), int(ty)), 2)

        if attacking:
            # layered crescent centered on the sword hand
            start = angle - 1.25
            for radius, color, width in ((48, (*p["wind_dark"], 90), 5),
                                         (46, (*p["wind_light"], 170), 3),
                                         (44, (*p["wind_white"], 235), 1)):
                _NS_kaizen._draw_wind_arc(surface, hx, hy, radius,
                                           start, angle + .25,
                                           color, width, 18)


    def _draw_saya_back(surface, cx, cy, facing, phase):
        """Lacquered katana sheath worn diagonally behind the waist."""
        sway = math.sin(phase * .55) * .6
        # Sheath points away from the sword hand and has a curved end cap.
        sx, sy = cx - facing * 7, cy + 3
        ex, ey = cx - facing * 29, cy + 25 + sway
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["shadow_deep"],
                           (sx + 2, sy + 2), (ex + 2, ey + 2), 8)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["wrap_dark"],
                           (sx, sy), (ex, ey), 6)
        _NS_kaizen._aaline(surface, (105, 28, 40), (sx, sy), (ex, ey), 4)
        _NS_kaizen._aaline(surface, (190, 62, 70),
                           (sx - facing, sy), (ex - facing, ey), 1)
        # Koiguchi, suspension cord, and metal kojiri.
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["gold_dark"],
                           (sx - 3, sy - 2), (sx + 3, sy + 3), 3)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["gold_mid"],
                             (int(ex), int(ey)), 3)
        cord_x = cx - facing * 10
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["scarf_light"],
                           (cord_x, cy + 2),
                           (cord_x - facing * 3, cy + 12), 2)


    def _draw_masterwork_details(surface, cx, cy, facing, phase, action):
        """High-frequency material detail that survives final downscaling."""
        p = _NS_kaizen.PALETTE
        shoulder = -facing

        # Cohesive three-lame pauldron on the free shoulder.  The broad base
        # is drawn once; curved separator highlights suggest overlapping
        # lacquer plates without turning into disconnected lines at 4x zoom.
        pauldron = [
            (cx + shoulder * 4, cy - 15),
            (cx + shoulder * 11, cy - 17),
            (cx + shoulder * 17, cy - 12),
            (cx + shoulder * 16, cy - 3),
            (cx + shoulder * 10, cy + 1),
            (cx + shoulder * 6, cy - 5),
        ]
        _NS_kaizen._poly(surface, p["shadow_deep"],
                          [(x + 1, y + 1) for x, y in pauldron])
        _NS_kaizen._poly(surface, p["cloth_darkest"], pauldron)
        inner_plate = [
            (cx + shoulder * 6, cy - 14),
            (cx + shoulder * 11, cy - 15),
            (cx + shoulder * 15, cy - 11),
            (cx + shoulder * 14, cy - 5),
            (cx + shoulder * 10, cy - 2),
            (cx + shoulder * 7, cy - 6),
        ]
        _NS_kaizen._poly(surface, p["cloth_mid"], inner_plate)
        for i in range(3):
            yy = cy - 11 + i * 4
            _NS_kaizen._aaline(surface, p["cloth_light"],
                               (cx + shoulder * 7, yy),
                               (cx + shoulder * (15 - i), yy + 2), 1)
        _NS_kaizen._aacircle(surface, p["gold_mid"],
                              (cx + shoulder * 8, cy - 11), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"],
                              (cx + shoulder * 8, cy - 12), 1)

        # Braided waist rope and large asymmetric knot.
        rope_y = cy + 7
        _NS_kaizen._aaline(surface, p["gold_dark"],
                           (cx - 12, rope_y), (cx + 12, rope_y), 3)
        for rx in range(cx - 10, cx + 11, 4):
            _NS_kaizen._aaline(surface, p["gold_light"],
                               (rx - 1, rope_y - 1), (rx + 1, rope_y + 1), 1)
        knot_x = cx + facing * 11
        _NS_kaizen._aacircle(surface, p["gold_dark"], (knot_x, rope_y), 3)
        _NS_kaizen._aacircle(surface, p["gold_mid"], (knot_x, rope_y), 2)
        _NS_kaizen._poly(surface, p["gold_light"], [
            (knot_x - 1, rope_y), (knot_x, rope_y - 2),
            (knot_x + 1, rope_y), (knot_x, rope_y + 1)])

        # Wind crest embroidered on the visible hakama panel.
        crest_y = cy + 19
        glow = int(180 + math.sin(phase * 1.4) * 45)
        _NS_kaizen._draw_wind_arc(surface, cx, crest_y, 5,
                                   .15, math.pi * 1.35,
                                   (*p["wind_light"], glow), 1, 8)
        _NS_kaizen._aaline(surface, (*p["wind_bright"], glow),
                           (cx - 1, crest_y), (cx + 4, crest_y - 2), 1)

        # Jacket seam/rivets and a small chest scar add readable texture.
        for side in (-1, 1):
            _NS_kaizen._aaline(surface, p["cloth_high"],
                               (cx + side * 8, cy - 11),
                               (cx + side * 7, cy + 2), 1)
            for yy in (-7, -2):
                _NS_kaizen._aacircle(surface, p["gold_mid"],
                                      (cx + side * 8, cy + yy), 1)
        _NS_kaizen._aaline(surface, (126, 62, 56),
                           (cx - 4, cy - 7), (cx + 2, cy - 2), 1)


    def _draw_scarf_back(surface, cx, cy, facing, phase, action):
        """Flowing scarf trailing behind."""
        wave = math.sin(phase * 1.2) * 3
        wave2 = math.sin(phase * 1.5 + 0.5) * 2
        trail = -facing  # trails opposite to facing

        # Main scarf trail
        scarf = [
            (cx + trail * 8, cy - 12),
            (cx + trail * 14, cy - 8 + int(wave)),
            (cx + trail * 22, cy - 4 + int(wave2)),
            (cx + trail * 28, cy + 4 + int(wave)),
            (cx + trail * 30, cy + 12 + int(wave2)),
            (cx + trail * 26, cy + 16),
            (cx + trail * 18, cy + 12),
            (cx + trail * 12, cy + 4),
            (cx + trail * 6, cy - 6),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in scarf])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_dark"], scarf)

        scarf_inner = [
            (cx + trail * 8, cy - 10),
            (cx + trail * 13, cy - 6 + int(wave)),
            (cx + trail * 20, cy - 2 + int(wave2)),
            (cx + trail * 25, cy + 5 + int(wave)),
            (cx + trail * 22, cy + 12),
            (cx + trail * 15, cy + 8),
            (cx + trail * 8, cy - 2),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_mid"], scarf_inner)

        # Highlight streak
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["scarf_light"],
                (cx + trail * 10, cy - 6),
                (cx + trail * 22, cy + 3 + int(wave)), 1)


    def _draw_hakama(surface, cx, cy, phase, facing):
        """Floating lower body - hakama-style pants that trail."""
        sway = int(math.sin(phase * 0.6) * 2)
        wave = int(math.sin(phase * 0.9) * 2)

        # Legs are rendered first so the robe overlaps them naturally.
        # The old single dark mass made Kaizen appear to float; split shins,
        # blue greaves, white tabi and sandals now give him a firm stance.
        stride = int(math.sin(phase * 1.7) * 2)
        for side in (-1, 1):
            lx = cx + side * 7 + (stride * side)
            _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["shadow_deep"], [
                (lx - 5, cy + 17), (lx + 4, cy + 17),
                (lx + 4, cy + 35), (lx - 5, cy + 35)])
            _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_dark"], [
                (lx - 4, cy + 18), (lx + 3, cy + 18),
                (lx + 3, cy + 32), (lx - 4, cy + 32)])
            _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["cloth_mid"],
                              (lx - 3, cy + 21, 6, 9), 2)
            _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_high"],
                               (lx - 2, cy + 22), (lx - 2, cy + 29), 1)
            # Tabi sock and wooden sandal with a strong ground-contact line.
            _NS_kaizen._rect(surface, (205, 214, 220),
                              (lx - 4, cy + 31, 8, 5), 2)
            toe = 2 * facing
            _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["leather_dark"],
                              (lx - 5 + toe, cy + 35, 10, 3), 1)
            _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["leather_light"],
                               (lx - 3 + toe, cy + 35),
                               (lx + 3 + toe, cy + 35), 1)

        # Base hakama shape - wider at bottom, grounded
        hakama = [
            (cx - 12, cy),
            (cx + 12, cy),
            (cx + 16 + sway, cy + 12),
            (cx + 14, cy + 22),
            (cx + 8, cy + 28),
            (cx + 3, cy + 32),
            (cx - 3, cy + 32),
            (cx - 8, cy + 28),
            (cx - 14, cy + 22),
            (cx - 16 - sway, cy + 12),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in hakama])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["pants_dark"], hakama)

        hakama_mid = [
            (cx - 10, cy + 2),
            (cx + 10, cy + 2),
            (cx + 13 + sway, cy + 12),
            (cx + 10, cy + 20),
            (cx + 5, cy + 26),
            (cx - 5, cy + 26),
            (cx - 10, cy + 20),
            (cx - 13 - sway, cy + 12),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["pants_mid"], hakama_mid)

        hakama_inner = [
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 9 + sway, cy + 12),
            (cx + 5, cy + 20),
            (cx - 5, cy + 20),
            (cx - 9 - sway, cy + 12),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["pants_light"], hakama_inner)

        # Vertical fabric fold lines
        for i in range(3):
            lx = cx - 6 + i * 6
            _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_darkest"],
                    (lx, cy + 3), (lx + int(sway * 0.3), cy + 24), 1)

        # Tattered bottom
        for i in range(6):
            tx = cx - 12 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 2)
            _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["pants_dark"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 4), (tx - 1, ty + 4),
            ])

        # Leather belt with buckle
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["leather_dark"], (cx - 14, cy - 1, 28, 5))
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["leather_mid"], (cx - 13, cy, 26, 3))
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["leather_light"],
                (cx - 12, cy + 1), (cx + 12, cy + 1), 1)

        # Belt buckle
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["gold_dark"], (cx - 3, cy - 1, 6, 5))
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["gold_mid"], (cx - 2, cy, 4, 3))
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["gold_light"], (cx - 1, cy + 1, 2, 1))

        # Sash tail hanging (on opposite side of sword)
        tail_side = -facing
        tx = cx + tail_side * 8
        ty = cy + 3
        tail_wave = int(math.sin(phase * 0.8) * 2)
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_dark"], [
            (tx - 3, ty),
            (tx + 3, ty),
            (tx + 4 + tail_wave, ty + 12),
            (tx + 2 + tail_wave, ty + 18),
            (tx - 2 + tail_wave, ty + 18),
            (tx - 4 + tail_wave, ty + 12),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_mid"], [
            (tx - 2, ty + 1),
            (tx + 2, ty + 1),
            (tx + 2 + tail_wave, ty + 16),
            (tx - 2 + tail_wave, ty + 16),
        ])


    def _draw_torso(surface, cx, cy, facing, phase):
        """Bare chest with open jacket."""
        # Shadow
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["shadow_deep"], [
            (cx - 11 + 2, cy - 8 + 2), (cx + 11 + 2, cy - 8 + 2),
            (cx + 10 + 2, cy + 14 + 2), (cx + 4 + 2, cy + 18 + 2),
            (cx - 4 + 2, cy + 18 + 2), (cx - 10 + 2, cy + 14 + 2),
        ])

        # Skin torso base (chest exposed)
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["skin_darkest"], [
            (cx - 9, cy - 8), (cx + 9, cy - 8),
            (cx + 8, cy + 14), (cx + 3, cy + 18),
            (cx - 3, cy + 18), (cx - 8, cy + 14),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["skin_dark"], [
            (cx - 8, cy - 7), (cx + 8, cy - 7),
            (cx + 7, cy + 12), (cx + 3, cy + 16),
            (cx - 3, cy + 16), (cx - 7, cy + 12),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["skin_mid"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5),
            (cx + 5, cy + 10), (cx + 2, cy + 13),
            (cx - 2, cy + 13), (cx - 5, cy + 10),
        ])

        # Muscle definition
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_darkest"],
                (cx, cy - 5), (cx, cy + 8), 1)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_light"], (cx - 3, cy - 2), 2)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_light"], (cx + 3, cy - 2), 2)
        # Abs suggestion
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_darkest"],
                (cx - 4, cy + 3), (cx + 4, cy + 3), 1)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_darkest"],
                (cx - 3, cy + 8), (cx + 3, cy + 8), 1)

        # Jacket sides (open in middle)
        # Left side
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_darkest"], [
            (cx - 11, cy - 8), (cx - 5, cy - 8),
            (cx - 3, cy + 18), (cx - 10, cy + 14),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_dark"], [
            (cx - 10, cy - 7), (cx - 5, cy - 7),
            (cx - 3, cy + 16), (cx - 9, cy + 12),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_mid"], [
            (cx - 9, cy - 6), (cx - 6, cy - 6),
            (cx - 4, cy + 12), (cx - 8, cy + 10),
        ])
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_light"],
                (cx - 9, cy - 4), (cx - 8, cy + 10), 1)

        # Right side
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_darkest"], [
            (cx + 5, cy - 8), (cx + 11, cy - 8),
            (cx + 10, cy + 14), (cx + 3, cy + 18),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_dark"], [
            (cx + 5, cy - 7), (cx + 10, cy - 7),
            (cx + 9, cy + 12), (cx + 3, cy + 16),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["cloth_mid"], [
            (cx + 6, cy - 6), (cx + 9, cy - 6),
            (cx + 8, cy + 10), (cx + 4, cy + 12),
        ])
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_light"],
                (cx + 9, cy - 4), (cx + 8, cy + 10), 1)

        # Leather chest strap (across body)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["leather_dark"],
                (cx - 8, cy - 4), (cx + 8, cy + 2), 4)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["leather_mid"],
                (cx - 8, cy - 4), (cx + 8, cy + 2), 3)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["leather_light"],
                (cx - 8, cy - 4), (cx + 8, cy + 2), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Idle - one arm holds katana down, other rests."""
        sway = int(math.sin(phase * 0.7) * 1)

        # SWORD arm (facing side - holds katana pointed down and back)
        sword_side = facing
        ss_x = cx + sword_side * 10
        ss_y = cy + 2
        se_x = ss_x + sword_side * 5
        se_y = cy + 10 + sway
        sh_x = se_x + sword_side * 3
        sh_y = se_y + 8
        _NS_kaizen._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_kaizen._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_kaizen._draw_hand(surface, sh_x, sh_y)

        # Katana - held pointing down and slightly back
        _NS_kaizen._draw_katana_idle(surface, sh_x, sh_y, facing, phase)

        # OTHER arm (opposite side - relaxed)
        other_side = -facing
        os_x = cx + other_side * 10
        os_y = cy + 2
        oe_x = os_x + other_side * 4
        oe_y = cy + 10 + sway
        oh_x = oe_x + other_side * 2
        oh_y = oe_y + 8
        _NS_kaizen._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_kaizen._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_kaizen._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack - katana swing animation (arc)."""
        sway = int(math.sin(phase * 0.7) * 1)

        # Swing animation:
        # 0.0-0.25: windup (sword back)
        # 0.25-0.6: swing forward (arc)
        # 0.6-1.0: recovery
        if progress < 0.25:
            t = progress / 0.25
            # Windup angle: from neutral to back
            swing_angle = -0.8 + t * -0.6  # more negative = more back
        elif progress < 0.6:
            t = (progress - 0.25) / 0.35
            # Swing arc: from back to forward
            swing_angle = -1.4 + t * 2.8  # sweep from -1.4 to 1.4
        else:
            t = (progress - 0.6) / 0.4
            # Recovery: hold forward then relax
            swing_angle = 1.4 - t * 2.2

        # SWORD arm - both hands on katana during attack
        sword_side = facing
        ss_x = cx + sword_side * 10
        ss_y = cy + 2

        # Arm extends outward at swing angle
        arm_length = 14
        se_x = ss_x + int(math.cos(swing_angle) * arm_length * 0.5) * sword_side
        se_y = ss_y + int(math.sin(swing_angle) * arm_length * 0.5) - 2
        sh_x = ss_x + int(math.cos(swing_angle) * arm_length) * sword_side
        sh_y = ss_y + int(math.sin(swing_angle) * arm_length) - 2

        _NS_kaizen._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_kaizen._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_kaizen._draw_hand(surface, sh_x, sh_y)

        # Second hand grips lower on katana (two-handed grip during swing)
        other_side = -facing
        os_x = cx + other_side * 8
        os_y = cy + 3
        # Second hand meets near the first
        oh_x = int(sh_x - math.cos(swing_angle) * 4 * sword_side)
        oh_y = int(sh_y - math.sin(swing_angle) * 4)
        oe_x = (os_x + oh_x) // 2 + other_side * 2
        oe_y = (os_y + oh_y) // 2 + 2

        _NS_kaizen._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_kaizen._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_kaizen._draw_hand(surface, oh_x, oh_y)

        # KATANA - drawn along swing_angle direction
        _NS_kaizen._draw_katana_swing(surface, sh_x, sh_y, facing, swing_angle, progress)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a clothed arm segment."""
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_darkest"], (x1, y1), (x2, y2), 6)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_dark"], (x1, y1), (x2, y2), 4)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_mid"], (x1, y1), (x2, y2), 2)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["cloth_light"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Small skin-colored hand."""
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_darkest"], (x, y), 3)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_mid"], (x, y), 2)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_light"], (x - 1, y - 1), 1)


    def _draw_katana_idle(surface, hx, hy, facing, phase):
        """Katana held pointing down/backward at rest."""
        # Katana pointing down-back at ~30 degrees
        angle = math.pi * 0.35  # down and slightly forward
        length = 32

        tip_x = hx + math.cos(angle) * length * facing
        tip_y = hy + math.sin(angle) * length

        # Handle (behind hand)
        handle_len = 8
        handle_x = hx - math.cos(angle) * handle_len * facing
        handle_y = hy - math.sin(angle) * handle_len

        _NS_kaizen._draw_katana_blade(surface, hx, hy, tip_x, tip_y, angle, facing, phase)
        _NS_kaizen._draw_katana_handle(surface, hx, hy, handle_x, handle_y)


    def _draw_katana_swing(surface, hx, hy, facing, swing_angle, progress):
        """Katana during swing with motion blur/trail."""
        length = 34

        # Blade extends in swing direction
        tip_x = hx + math.cos(swing_angle) * length * facing
        tip_y = hy + math.sin(swing_angle) * length

        # Handle behind hand
        handle_len = 6
        handle_x = hx - math.cos(swing_angle) * handle_len * facing
        handle_y = hy - math.sin(swing_angle) * handle_len

        # Motion trail during active swing (0.25 - 0.7)
        if 0.25 < progress < 0.7:
            t = (progress - 0.25) / 0.45
            # Draw crescent slash arc trail
            _NS_kaizen._draw_swing_trail(surface, hx, hy, facing, swing_angle, t, length)

        _NS_kaizen._draw_katana_blade(surface, hx, hy, tip_x, tip_y, swing_angle, facing, 0)
        _NS_kaizen._draw_katana_handle(surface, hx, hy, handle_x, handle_y)


    def _draw_swing_trail(surface, cx, cy, facing, current_angle, t, length):
        """Big crescent slash trail effect."""
        # Trail spans from -0.6 rad behind current to current
        trail_span = 0.8 * (1 - t * 0.5)
        start_angle = current_angle - trail_span * facing

        # Draw crescent shape
        inner_r = length * 0.4
        outer_r = length * 1.05

        segments = 14
        outer_points = []
        inner_points = []

        for i in range(segments + 1):
            ti = i / segments
            # Angle interpolated
            if facing >= 0:
                angle = start_angle + trail_span * ti
            else:
                angle = start_angle - trail_span * ti
            ox = cx + math.cos(angle) * outer_r * facing
            oy = cy + math.sin(angle) * outer_r
            ix = cx + math.cos(angle) * inner_r * facing
            iy = cy + math.sin(angle) * inner_r
            outer_points.append((ox, oy))
            inner_points.append((ix, iy))

        # Build crescent polygon
        crescent = outer_points + list(reversed(inner_points))
        fade = int(180 * (1 - t))

        if fade > 20:
            _NS_kaizen._poly(surface, (*_NS_kaizen.PALETTE["wind_dark"], fade // 2), crescent)
            # Inner brighter layer
            inner_crescent = []
            for i in range(segments + 1):
                ti = i / segments
                if facing >= 0:
                    angle = start_angle + trail_span * ti
                else:
                    angle = start_angle - trail_span * ti
                ox = cx + math.cos(angle) * (outer_r * 0.95) * facing
                oy = cy + math.sin(angle) * (outer_r * 0.95)
                ix = cx + math.cos(angle) * (inner_r * 1.15) * facing
                iy = cy + math.sin(angle) * (inner_r * 1.15)
                inner_crescent.append((ox, oy))
            for i in range(segments + 1):
                ti = 1 - i / segments
                if facing >= 0:
                    angle = start_angle + trail_span * ti
                else:
                    angle = start_angle - trail_span * ti
                ix = cx + math.cos(angle) * (inner_r * 1.15) * facing
                iy = cy + math.sin(angle) * (inner_r * 1.15)
                inner_crescent.append((ix, iy))

            # Bright core arc
            _NS_kaizen._draw_wind_arc(surface, cx, cy, outer_r * 0.85,
                           start_angle if facing >= 0 else start_angle - trail_span,
                           (start_angle + trail_span) if facing >= 0 else start_angle,
                           (*_NS_kaizen.PALETTE["wind_bright"], fade), width=2, segments=12)
            _NS_kaizen._draw_wind_arc(surface, cx, cy, outer_r * 0.72,
                           start_angle if facing >= 0 else start_angle - trail_span,
                           (start_angle + trail_span) if facing >= 0 else start_angle,
                           (*_NS_kaizen.PALETTE["wind_white"], fade), width=1, segments=12)


    def _draw_katana_blade(surface, hx, hy, tip_x, tip_y, angle, facing, phase):
        """Draw the katana blade."""
        # Guard (tsuba)
        perp = angle + math.pi / 2
        guard_size = 4
        g1 = (hx + math.cos(perp) * guard_size, hy + math.sin(perp) * guard_size)
        g2 = (hx - math.cos(perp) * guard_size, hy - math.sin(perp) * guard_size)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["gold_dark"], g1, g2, 3)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["gold_mid"], g1, g2, 2)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["gold_light"], g1, g2, 1)

        # Blade - curved katana shape
        # Compute a slight curve for the blade
        blade_length = math.sqrt((tip_x - hx) ** 2 + (tip_y - hy) ** 2)
        # Blade width
        bw = 3

        # Perpendicular for blade thickness
        px = -math.sin(angle) * facing
        py = math.cos(angle) * facing

        # Slight curve: mid point offset
        mid_x = (hx + tip_x) / 2 + px * 2
        mid_y = (hy + tip_y) / 2 + py * 2

        # Blade polygon (curved with 4 points using mid control)
        blade_points = [
            (hx + px * bw, hy + py * bw),
            (mid_x + px * bw * 0.7, mid_y + py * bw * 0.7),
            (tip_x, tip_y),
            (mid_x - px * bw * 0.2, mid_y - py * bw * 0.2),
            (hx - px * bw, hy - py * bw),
        ]
        # Shadow
        shadow_pts = [(p[0] + 1, p[1] + 1) for p in blade_points]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["shadow_deep"], shadow_pts)

        # Base dark
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["steel_darkest"], blade_points)
        # Mid layer
        blade_mid = [
            (hx + px * bw * 0.7, hy + py * bw * 0.7),
            (mid_x + px * bw * 0.5, mid_y + py * bw * 0.5),
            (tip_x, tip_y),
            (mid_x - px * bw * 0.1, mid_y - py * bw * 0.1),
            (hx - px * bw * 0.5, hy - py * bw * 0.5),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["steel_dark"], blade_mid)

        # Light layer
        blade_light = [
            (hx + px * bw * 0.3, hy + py * bw * 0.3),
            (mid_x + px * bw * 0.2, mid_y + py * bw * 0.2),
            (tip_x, tip_y),
            (mid_x - px * bw * 0.05, mid_y - py * bw * 0.05),
            (hx - px * bw * 0.2, hy - py * bw * 0.2),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["steel_mid"], blade_light)

        # Bright edge (top of blade)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["steel_light"],
                (hx + px * bw * 0.8, hy + py * bw * 0.8),
                (tip_x, tip_y), 1)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["steel_shine"],
                (hx + px * bw * 0.5, hy + py * bw * 0.5),
                ((tip_x + mid_x) / 2, (tip_y + mid_y) / 2), 1)

        # Hamon temper line: a tiny wave inside the cutting edge.  It is
        # deliberately high contrast so it survives the final HD downscale.
        if blade_length >= 10:
            ux = (tip_x - hx) / blade_length
            uy = (tip_y - hy) / blade_length
            hamon = []
            for i in range(1, 7):
                t = i / 7.0
                ripple = math.sin(t * math.pi * 6 + phase * .25) * .65
                hamon.append((hx + ux * blade_length * t + px * ripple,
                              hy + uy * blade_length * t + py * ripple))
            if len(hamon) > 1:
                pygame.draw.aalines(surface, _NS_kaizen.PALETTE["wind_bright"],
                                    False, hamon)

        # Tip highlight
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["steel_shine"], (int(tip_x), int(tip_y)), 1)


    def _draw_katana_handle(surface, hx, hy, end_x, end_y):
        """Wrapped handle (tsuka)."""
        # Base handle
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["wrap_dark"], (hx, hy), (end_x, end_y), 5)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["wrap_mid"], (hx, hy), (end_x, end_y), 3)

        # Wrap pattern (diamond)
        length = math.sqrt((end_x - hx) ** 2 + (end_y - hy) ** 2)
        if length < 1:
            return
        dx = (end_x - hx) / length
        dy = (end_y - hy) / length
        for i in range(3):
            t = 0.2 + i * 0.3
            wx = int(hx + dx * length * t)
            wy = int(hy + dy * length * t)
            _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["wrap_dark"], (wx, wy), 2)
            _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["wrap_light"], (wx, wy), 1)

        # Pommel (end cap)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["gold_dark"], (int(end_x), int(end_y)), 3)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["gold_mid"], (int(end_x), int(end_y)), 2)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["gold_light"], (int(end_x - 1), int(end_y - 1)), 1)


    def _draw_scarf_front(surface, cx, cy, facing, phase):
        """Blue scarf around neck flowing over shoulder."""
        wave = int(math.sin(phase * 1.0) * 2)

        # Scarf collar around neck
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_dark"], [
            (cx - 8, cy - 10),
            (cx + 8, cy - 10),
            (cx + 9, cy - 4),
            (cx + 5, cy - 2),
            (cx - 5, cy - 2),
            (cx - 9, cy - 4),
        ])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_mid"], [
            (cx - 7, cy - 9),
            (cx + 7, cy - 9),
            (cx + 7, cy - 5),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
            (cx - 7, cy - 5),
        ])

        # Scarf drape over one shoulder (facing side)
        dp = facing
        drape = [
            (cx + dp * 4, cy - 8),
            (cx + dp * 9, cy - 6),
            (cx + dp * 11, cy - 2 + wave),
            (cx + dp * 12, cy + 6 + wave),
            (cx + dp * 9, cy + 10),
            (cx + dp * 5, cy + 6),
            (cx + dp * 3, cy - 2),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_dark"], drape)
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["scarf_mid"], [
            (cx + dp * 4, cy - 7),
            (cx + dp * 8, cy - 5),
            (cx + dp * 10, cy - 1 + wave),
            (cx + dp * 10, cy + 5 + wave),
            (cx + dp * 7, cy + 8),
            (cx + dp * 4, cy + 4),
        ])
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["scarf_light"],
                (cx + dp * 5, cy - 5), (cx + dp * 9, cy + 4), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Yasuo head - face, topknot, hair."""
        # Ponytail (behind head, flowing)
        _NS_kaizen._draw_ponytail(surface, cx, cy, facing, phase)

        # Head shape (face)
        face_points = [
            (cx - 7, cy - 6),
            (cx - 8, cy - 2),
            (cx - 7, cy + 3),
            (cx - 5, cy + 8),
            (cx - 2, cy + 11),
            (cx + 2, cy + 11),
            (cx + 5, cy + 8),
            (cx + 7, cy + 3),
            (cx + 8, cy - 2),
            (cx + 7, cy - 6),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["skin_darkest"],
              [(p[0] + 1, p[1] + 1) for p in face_points])
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["skin_dark"], face_points)
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["skin_mid"], [
            (cx - 6, cy - 5),
            (cx - 7, cy - 2),
            (cx - 6, cy + 3),
            (cx - 4, cy + 7),
            (cx - 2, cy + 10),
            (cx + 2, cy + 10),
            (cx + 4, cy + 7),
            (cx + 6, cy + 3),
            (cx + 7, cy - 2),
            (cx + 6, cy - 5),
        ])
        # Cheek highlights
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_light"], (cx - 4, cy + 4), 2)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_light"], (cx + 4, cy + 4), 2)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_high"], (cx - 4, cy + 4), 1)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_high"], (cx + 4, cy + 4), 1)

        # Hair top / bangs
        hair_top = [
            (cx - 8, cy - 5),
            (cx - 9, cy - 2),
            (cx - 6, cy - 4),
            (cx - 4, cy - 7),
            (cx - 1, cy - 5),
            (cx + 1, cy - 8),
            (cx + 4, cy - 6),
            (cx + 6, cy - 4),
            (cx + 9, cy - 2),
            (cx + 8, cy - 5),
            (cx + 6, cy - 10),
            (cx - 6, cy - 10),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["hair_darkest"], hair_top)
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["hair_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy - 3),
            (cx - 5, cy - 4),
            (cx - 3, cy - 6),
            (cx, cy - 5),
            (cx + 3, cy - 6),
            (cx + 5, cy - 4),
            (cx + 8, cy - 3),
            (cx + 7, cy - 5),
            (cx + 5, cy - 9),
            (cx - 5, cy - 9),
        ])
        # Highlight strand
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_mid"],
                (cx - 3, cy - 8), (cx - 1, cy - 5), 1)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_light"],
                (cx + 2, cy - 7), (cx + 4, cy - 5), 1)

        # Eyes - stern samurai gaze
        for eye_x in (-3, 3):
            # Eye white
            _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["eye_white"], (cx + eye_x - 1, cy + 1, 2, 2))
            # Yellow/gold iris
            _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["eye_iris"], (cx + eye_x - 1, cy + 1, 2, 2))
            # Highlight
            _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["eye_iris_light"], (cx + eye_x, cy + 1, 1, 1))

        # Brows (angry/stern)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_darkest"],
                (cx - 5, cy), (cx - 1, cy - 1), 2)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_darkest"],
                (cx + 1, cy - 1), (cx + 5, cy), 2)

        # Nose
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_darkest"], (cx, cy + 5), 1)

        # Nose bridge, jaw occlusion and iconic diagonal duelist scar.
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_light"],
                           (cx, cy + 2), (cx - facing, cy + 5), 1)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_darkest"],
                           (cx - 4, cy + 8), (cx, cy + 10), 1)
        _NS_kaizen._aaline(surface, (112, 48, 46),
                           (cx - facing * 6, cy + 2),
                           (cx + facing * 3, cy + 7), 1)
        _NS_kaizen._aacircle(surface, (226, 135, 125),
                             (cx - facing * 3, cy + 4), 1)

        # Ear and gold wind earring on the trailing side.
        ear_x = cx - facing * 8
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["skin_dark"],
                             (ear_x, cy + 3), 2)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["gold_light"],
                             (ear_x, cy + 7), 1)

        # Mouth (small serious line) plus lower-lip light.
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_darkest"],
                           (cx - 2, cy + 8), (cx + 2, cy + 8), 1)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["skin_light"],
                           (cx, cy + 9), (cx + facing * 2, cy + 9), 1)


    def _draw_ponytail(surface, cx, cy, facing, phase):
        """Flowing samurai ponytail/topknot behind head."""
        wave = math.sin(phase * 1.1) * 3
        wave2 = math.sin(phase * 1.4 + 0.7) * 2
        tail_side = -facing * 0.3  # slight backward lean

        # Topknot base (bun on top of head)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["hair_darkest"], (cx, cy - 12), 5)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["hair_dark"], (cx, cy - 12), 4)
        _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["hair_mid"], (cx - 1, cy - 13), 2)
        # Small tie
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["wrap_dark"], (cx - 3, cy - 10, 6, 2))
        _NS_kaizen._rect(surface, _NS_kaizen.PALETTE["wrap_mid"], (cx - 2, cy - 10, 4, 1))

        # Ponytail hair flowing upward and back
        ponytail_pts = [
            (cx - 3, cy - 14),
            (cx - 4 + int(wave), cy - 20),
            (cx - 5 + int(wave2), cy - 26),
            (cx - 3 + int(wave), cy - 32),
            (cx + int(wave2), cy - 36),
            (cx + 3 + int(wave), cy - 34),
            (cx + 5 + int(wave2), cy - 28),
            (cx + 4 + int(wave), cy - 22),
            (cx + 3, cy - 14),
        ]
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["hair_darkest"], ponytail_pts)
        _NS_kaizen._poly(surface, _NS_kaizen.PALETTE["hair_dark"], [
            (cx - 2, cy - 14),
            (cx - 3 + int(wave), cy - 20),
            (cx - 4 + int(wave2), cy - 26),
            (cx - 2 + int(wave), cy - 31),
            (cx + int(wave2), cy - 34),
            (cx + 2 + int(wave), cy - 31),
            (cx + 4 + int(wave2), cy - 27),
            (cx + 3 + int(wave), cy - 21),
            (cx + 2, cy - 14),
        ])
        # Highlights
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_mid"],
                (cx - 1 + int(wave), cy - 18),
                (cx - 1 + int(wave2), cy - 30), 1)
        _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_light"],
                (cx + 1 + int(wave), cy - 22),
                (cx + 1 + int(wave2), cy - 30), 1)

        # Wispy strands
        for i in range(3):
            sx = cx - 6 + i * 6
            sy = cy - 14 - i * 2
            ex = sx + int(math.sin(phase + i) * 4)
            ey = sy - 8
            _NS_kaizen._aaline(surface, _NS_kaizen.PALETTE["hair_dark"], (sx, sy), (ex, ey), 1)


    def _draw_body_particles(surface, cx, cy, phase):
        """Wind particles around body."""
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            radius = 30 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha), (px, py), 2)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha), (px, py), 1)

        # Passing leaves/wind streaks
        for i in range(4):
            t = (phase * 0.4 + i * 0.25) % 1.0
            fx = cx - 40 + int(t * 80)
            fy = cy - 20 + int(math.sin(phase + i) * 6) + i * 5
            alpha = int(180 * math.sin(t * math.pi))
            if alpha > 0:
                _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha),
                        (fx, fy), (fx + 8, fy - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Wind mist beneath floating Kaizen."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaizen.PALETTE["wind_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising wind wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha), (sx, sy), 5)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha), (sx, sy - 2), 3)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Small circling wind swirls
        for i in range(3):
            angle = phase * 1.2 + i * math.pi * 2 / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_kaizen._draw_wind_swirl(surface, sx, sy, 4, phase + i,
                             _NS_kaizen.PALETTE["wind_bright"], alpha=200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_kaizen.PALETTE["wind_darkest"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_swordsman_rim_light(surface, x, y, phase):
        """Small code-drawn blue rim light around scarf, katana, and hair."""
        pulse = .72 + math.sin(phase * 1.3) * .16
        halo = pygame.Surface((88, 98), pygame.SRCALPHA)
        for radius, alpha in ((38, 9), (29, 14), (20, 20)):
            _NS_kaizen._aacircle(halo, (*_NS_kaizen.PALETTE["wind_dark"],
                                         int(alpha * pulse)), (44, 49), radius)
        _NS_kaizen._aaline(halo, (*_NS_kaizen.PALETTE["wind_mid"], int(38 * pulse)),
                            (28, 57), (12, 64), 2)
        _NS_kaizen._aaline(halo, (*_NS_kaizen.PALETTE["wind_light"], int(34 * pulse)),
                            (55, 56), (78, 45), 1)
        surface.blit(halo, (x - 44, y - 49))


    def _draw_wind_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_kaizen._aacircle(aura, (*_NS_kaizen.PALETTE["wind_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_wind_platform(surface, x, y, phase, skill):
        """Wind circle platform."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_mid"], 180),
                            (20, 14, 90, 16), 2)

        # Swirling wind streaks
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_kaizen.PALETTE["wind_light"], 170),
                             (x1, y1), (x2, y2), 1)

        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_kaizen.PALETTE["wind_bright"], 200), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    # ===================================================================
    # SKILL Q: DASH / STEEL WIND (already handled with projectile)
    # ===================================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Ground effect during dash."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        # Line indicator from boss to target
        _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_mid"], 100), (x, y + 30), (tx, ty + 20), 3)
        _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], 150), (x, y + 30), (tx, ty + 20), 1)


    def _draw_dash_effect(surface, boss, x, y, timer, phase):
        """Dash trail / speed lines."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Multiple after-images along dash path
        for i in range(6):
            t = i / 5.0
            ix = int(x + (tx - x) * t)
            iy = int(y + (ty - y) * t)
            alpha = int(180 * (1 - progress) * (1 - t * 0.5))

            # Small ghost silhouette
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha // 2), (ix, iy), 12)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha), (ix, iy - 5), 8)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha), (ix, iy - 3), 4)

        # Speed streaks
        dx = tx - x
        dy = ty - y
        dist = math.sqrt(dx * dx + dy * dy) or 1
        dx /= dist
        dy /= dist
        px = -dy
        py = dx

        for i in range(8):
            off = (i - 4) * 4
            sx = x + px * off
            sy = y + py * off
            ex = sx + dx * 40
            ey = sy + dy * 40
            alpha = int(220 * (1 - progress))
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha),
                    (sx, sy), (ex, ey), 1)


    # ===================================================================
    # SKILL W: WIND WALL
    # ===================================================================
    def _draw_wind_wall(surface, boss, x, y, timer, phase):
        """Vertical wind wall in front of Kaizen."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        facing = boss.direction

        wall_x = x + 40 * facing
        wall_top = y - 45
        wall_bot = y + 35
        wall_height = wall_bot - wall_top

        # Growing wall
        if progress < 0.2:
            t = progress / 0.2
            h = int(wall_height * t)
            wall_top = y + 35 - h
        else:
            pass

        wall_width = 6

        # Base wall shadow
        _NS_kaizen._rect(surface, (*_NS_kaizen.PALETTE["wind_darkest"], 100),
              (wall_x - wall_width, wall_top, wall_width * 2, wall_bot - wall_top))

        # Wind swirls making up the wall
        for i in range(8):
            swirl_y = wall_top + i * (wall_bot - wall_top) / 8
            offset_x = int(math.sin(phase * 2 + i * 0.7) * 3)
            _NS_kaizen._draw_wind_swirl(surface, wall_x + offset_x, int(swirl_y), 5,
                             phase + i, _NS_kaizen.PALETTE["wind_bright"], alpha=200)

        # Vertical wind streaks
        for i in range(5):
            sx = wall_x + (i - 2) * 3
            streak_start = wall_top + int((phase * 20 + i * 15) % 30)
            streak_end = min(wall_bot, streak_start + 20)
            alpha = 180
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha),
                    (sx, streak_start), (sx, streak_end), 1)
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha),
                    (sx + 1, streak_start + 3), (sx + 1, streak_end - 3), 1)

        # Top and bottom energy caps
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], 200),
                  (wall_x, wall_top), 6)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                  (wall_x, wall_top), 3)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], 200),
                  (wall_x, wall_bot), 6)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                  (wall_x, wall_bot), 3)


    # ===================================================================
    # SKILL E: SWEEP (circular AoE at feet)
    # ===================================================================
    def _draw_sweep_ground(surface, boss, x, y, timer, phase):
        """Ground indicator."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        radius = int(35 + progress * 30)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_mid"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_bright"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_sweep_effect(surface, boss, x, y, timer, phase):
        """Upward sweep - wind uplift."""
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Wind pillars rising in ring
        for i in range(10):
            angle = i * math.pi / 5 + phase * 0.2
            r = 40
            px = x + int(math.cos(angle) * r)
            py = y + 25 + int(math.sin(angle) * r * 0.3)

            # Rising wind pillar
            h = int(30 * math.sin(progress * math.pi))
            if h <= 0:
                continue

            # Wind streak going up
            for seg in range(3):
                sy = py - seg * (h // 3)
                ey = py - (seg + 1) * (h // 3)
                alpha = 200 - seg * 40
                _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha),
                        (px, sy), (px, ey), 2)
                _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha),
                        (px + 1, sy), (px + 1, ey), 1)

            # Top cap
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 220), (px, py - h), 2)

        # Central burst
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], int(120 * (1 - progress))),
                  (x, y + 20), int(20 + progress * 15), 2)


    # ===================================================================
    # SKILL R: TORNADO (ultimate)
    # ===================================================================
    def _draw_tornado_ground(surface, boss, x, y, timer, phase):
        """Ground swirl indicator."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Warning circle at target
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], int(150 * pulse)),
                  (tx, ty + 20), 30, 2)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], int(180 * pulse)),
                  (tx, ty + 20), 24, 1)


    def _draw_tornado(surface, boss, x, y, timer, phase):
        """Large tornado at target position."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Tornado grows then holds
        if progress < 0.3:
            grow = progress / 0.3
        else:
            grow = 1.0

        base_y = ty + 25
        top_y = ty - 60
        height = base_y - top_y
        height = int(height * grow)
        top_y = base_y - height

        if height < 5:
            return

        # Tornado shape - narrow at bottom, wide at top
        layers = 12
        for i in range(layers):
            t = i / layers
            layer_y = int(base_y - t * height)
            # Radius grows with height
            radius = int(4 + t * 22)

            # Swirl offset
            swirl_offset = int(math.sin(phase * 3 + t * 6) * 3)
            cx = tx + swirl_offset

            # Draw layer as ellipse (rotating swirl)
            alpha_base = int(180 - t * 40)

            # Outer swirl
            for a_off in range(3):
                angle = phase * 4 + t * 8 + a_off * math.pi * 2 / 3
                wx = cx + int(math.cos(angle) * radius)
                wy = layer_y + int(math.sin(angle) * radius * 0.3)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha_base),
                          (wx, wy), 3)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha_base),
                          (wx, wy), 2)

            # Ellipse ring outline
            _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha_base),
                     (cx - radius, layer_y - int(radius * 0.3),
                      radius * 2, int(radius * 0.6)), 1)

            # Bright inner
            if i % 2 == 0:
                _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha_base),
                         (cx - radius + 2, layer_y - int(radius * 0.3) + 1,
                          radius * 2 - 4, int(radius * 0.6) - 2), 1)

        # Central vertical core
        core_x = tx + int(math.sin(phase * 2) * 2)
        _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                (core_x, top_y + 5), (core_x, base_y - 5), 2)
        _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], 150),
                (core_x + 1, top_y + 5), (core_x + 1, base_y - 5), 1)

        # Debris/particles swirling
        for i in range(8):
            t = ((phase * 0.3 + i * 0.12) % 1.0)
            py = int(base_y - t * height)
            radius = 5 + t * 22
            angle = phase * 3 + i * math.pi / 4
            px = tx + int(math.cos(angle) * radius)
            alpha = int(220 * (1 - t * 0.5))
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha), (px, py), 2)

        # Top opening flare
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], 150),
                  (tx, top_y), 22, 2)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                  (tx, top_y), 18, 1)

        # Base impact dust
        _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_dark"], 180),
                 (tx - 20, base_y - 4, 40, 10))
        _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_mid"], 200),
                 (tx - 15, base_y - 3, 30, 8))


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_kaizen.draw_kaizen(surface, boss, x, y)

# ====================================================================
# thorne.py
# ====================================================================
class _NS_thorne:
    """Namespace thorne - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Bristleback inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Fur / skin - brown
        "fur_darkest":    ( 35,  20,  10),
        "fur_dark":       ( 70,  40,  20),
        "fur_mid":        (115,  75,  40),
        "fur_light":      (160, 110,  65),
        "fur_high":       (200, 150,  95),

        # Belly / lighter skin
        "belly_dark":     (130,  90,  55),
        "belly_mid":      (175, 130,  85),
        "belly_light":    (210, 165, 115),

        # Snout - pinkish
        "snout_dark":     (135,  75,  55),
        "snout_mid":      (185, 115,  90),
        "snout_light":    (225, 160, 135),

        # Quills - yellow/orange gradient
        "quill_darkest":  ( 75,  40,  10),
        "quill_dark":     (140,  85,  20),
        "quill_mid":      (210, 155,  40),
        "quill_light":    (245, 205,  75),
        "quill_shine":    (255, 235, 130),
        "quill_tip":      (255, 250, 200),
        "quill_root":     (170,  70,  25),

        # Tusks
        "tusk_dark":      (175, 150, 110),
        "tusk_mid":       (220, 205, 165),
        "tusk_light":     (245, 235, 210),

        # Armor - metal shoulder
        "armor_darkest":  ( 25,  30,  40),
        "armor_dark":     ( 55,  65,  80),
        "armor_mid":      (100, 115, 135),
        "armor_light":    (155, 170, 190),
        "armor_shine":    (210, 220, 235),

        # Leather - straps, belt
        "leather_darkest":( 30,  18,  10),
        "leather_dark":   ( 65,  40,  20),
        "leather_mid":    (100,  65,  35),
        "leather_light":  (140,  95,  55),

        # Cloth - green vest
        "cloth_dark":     ( 30,  55,  25),
        "cloth_mid":      ( 60,  95,  45),
        "cloth_light":    ( 95, 140,  70),

        # Club - wood with metal
        "wood_dark":      ( 55,  35,  20),
        "wood_mid":       ( 95,  65,  35),
        "wood_light":     (140, 100,  60),

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),

        # Green - snot/goo (viscous nose)
        "goo_darkest":    ( 30,  55,  15),
        "goo_dark":       ( 65, 110,  30),
        "goo_mid":        (115, 175,  55),
        "goo_light":      (170, 220,  95),
        "goo_bright":     (215, 245, 145),

        # Rage - red aura (warpath)
        "rage_dark":      ( 90,  20,  15),
        "rage_mid":       (170,  45,  30),
        "rage_light":     (230,  85,  55),
        "rage_bright":    (255, 145,  90),

        # Eyes - orange/yellow
        "eye_white":      (250, 240, 200),
        "eye_iris":       (200, 100,  30),
        "eye_iris_light": (240, 165,  60),
        "eye_pupil":      ( 15,  10,   5),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thorne._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_thorne.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_thorne._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_thorne._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_thorne._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_thorne._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_thorne._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 150 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Quill helpers
    # ---------------------------------------------------------------------------
    def _draw_quill(surface, base_x, base_y, length, angle, thickness=2,
                    dark=None, mid=None, light=None, tip=None):
        """Draw a single quill (spike)."""
        if dark is None:
            dark = _NS_thorne.PALETTE["quill_darkest"]
        if mid is None:
            mid = _NS_thorne.PALETTE["quill_dark"]
        if light is None:
            light = _NS_thorne.PALETTE["quill_light"]
        if tip is None:
            tip = _NS_thorne.PALETTE["quill_tip"]

        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = base_x + ca * length
        tip_y = base_y + sa * length
        # Perpendicular for thickness
        px = -sa * thickness
        py = ca * thickness

        # Dark base triangle
        _NS_thorne._poly(surface, dark, [
            (base_x + px, base_y + py),
            (base_x - px, base_y - py),
            (tip_x, tip_y),
        ])
        # Mid layer (narrower)
        _NS_thorne._poly(surface, mid, [
            (base_x + px * 0.6, base_y + py * 0.6),
            (base_x - px * 0.6, base_y - py * 0.6),
            (tip_x - ca * 1, tip_y - sa * 1),
        ])
        # Light streak
        _NS_thorne._aaline(surface, light,
                (base_x + px * 0.2, base_y + py * 0.2),
                (tip_x - ca * 1, tip_y - sa * 1), 1)
        # Tip highlight
        _NS_thorne._aacircle(surface, tip, (int(tip_x), int(tip_y)), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------------------
    class QuillProjectile:
        """Sharp quill flying through the air."""
        def __init__(self, sx, sy, tx, ty, speed=9.0, spread_angle=0):
            self.x = float(sx)
            self.y = float(sy)
            dx = tx - sx
            dy = ty - sy
            base_angle = math.atan2(dy, dx)
            self.angle = base_angle + spread_angle
            dist = math.sqrt(dx * dx + dy * dy) or 1
            # Travel in own direction (fan spread)
            self.tx = sx + math.cos(self.angle) * 500
            self.ty = sy + math.sin(self.angle) * 500
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.max_life = 60

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            if self.age > self.max_life:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 15)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_dark"], alpha), (tx, ty), 2)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_light"], alpha // 2),
                          (tx, ty), 1)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # The quill itself
                _NS_thorne._draw_quill(surface, px, py, 12, self.angle, thickness=2)


    class GooProjectile:
        """Green viscous goo blob (Viscous Nose)."""
        def __init__(self, sx, sy, tx, ty, speed=5.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)
            self.impact_frame = -1

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            if self.impact_frame >= 0:
                if self.age - self.impact_frame > 20:
                    self.alive = False
                return

            # Homing tiap frame ke target selama masih terbang (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_thorne._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 6:
                self.impact_frame = self.age
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 15:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Impact splatter
            if self.impact_frame >= 0:
                t = (self.age - self.impact_frame) / 20.0
                radius = int(6 + t * 18)
                alpha = int(220 * (1 - t))
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_dark"], alpha),
                          (int(self.tx), int(self.ty)), radius + 2)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], alpha),
                          (int(self.tx), int(self.ty)), radius)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_light"], alpha),
                          (int(self.tx), int(self.ty)), radius // 2)
                # Splatter drops
                for i in range(6):
                    a = i * math.pi / 3 + phase
                    sr = radius * 1.3
                    sx = int(self.tx + math.cos(a) * sr)
                    sy = int(self.ty + math.sin(a) * sr)
                    _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], alpha), (sx, sy), 3)
                    _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_bright"], alpha), (sx, sy), 1)
                return

            # Trail - dripping goo
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_dark"], alpha), (tx, ty), r + 1)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], alpha), (tx, ty), r)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_light"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive and self.impact_frame < 0:
                px, py = int(self.x), int(self.y)
                # Main goo blob - irregular shape
                wobble = math.sin(self.age * 0.5) * 1

                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_darkest"], (px, py), 8)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_dark"], (px, py), 7)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"], (px - 1, py - 1), 5)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_light"], (px - 2, py - 2), 3)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_bright"], (px - 2, py - 2), 1)

                # Drip below
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_dark"],
                          (px + int(wobble), py + 6), 3)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"],
                          (px + int(wobble), py + 6), 2)

                # Front splatter chunks
                for i in range(3):
                    a = self.angle + (i - 1) * 0.4
                    dr = 10 + i
                    sx = px + int(math.cos(a) * dr)
                    sy = py + int(math.sin(a) * dr)
                    _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"], (sx, sy), 2)
                    _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_bright"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_th_last_x"):
            boss._th_last_x = boss.x
            boss._th_last_y = boss.y
            return False
        dx = abs(boss.x - boss._th_last_x)
        dy = abs(boss.y - boss._th_last_y)
        boss._th_last_x = boss.x
        boss._th_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_th_prev_timer", -1))
        active = bool(getattr(boss, "_th_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._th_attack_active = True
            active = True

        if active and timer <= 0:
            boss._th_attack_active = False
            active = False

        boss._th_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._th_attack_frame = max(0, cooldown - timer) if active else 0
        boss._th_attack_progress = (
            min(1.0, boss._th_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        for proj in boss._th_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._th_projectiles = [p for p in boss._th_projectiles if p.alive or p.dead_frames < 8]


    def _spawn_goo(boss, x, y):
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        tx, ty = _NS_thorne._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Goo from snout
        sx = x + 20 * facing
        sy = y - 20
        tgt = getattr(boss, "target", None)
        proj = _NS_thorne.GooProjectile(
            sx, sy, tx, ty, speed=5.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._th_projectiles.append(proj)


    def _spawn_quill_spray(boss, x, y):
        """Fire a burst of quills from back."""
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        tx, ty = _NS_thorne._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # From back (opposite of facing)
        sx = x - 10 * facing
        sy = y - 20

        # Fan of 7 quills
        for i in range(7):
            spread = (i - 3) * 0.15
            boss._th_projectiles.append(
                _NS_thorne.QuillProjectile(sx, sy, tx, ty, speed=9.0, spread_angle=spread))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_thorne(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thorne._detect_moving(boss)
        _NS_thorne._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_th_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        warpath_active = active_skill == "r"
        bristleback_active = active_skill == "w"

        # ---------- Background layers ----------
        # Portrait LOD sengaja menghilangkan aura/platform seukuran arena agar
        # auto-crop mengisi portrait dengan wajah & material Thorne, bukan
        # lingkaran efek 180 px.
        if not portrait_hd:
            if warpath_active:
                _NS_thorne._draw_rage_aura(surface, x, y, pulse)
            else:
                _NS_thorne._draw_dust_aura(surface, x, y, pulse)
            _NS_thorne._draw_ground_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_thorne._draw_viscous_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorne._draw_quill_spray_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_thorne._draw_thorne_attack(surface, boss, x, y, warpath_active)
        elif moving:
            _NS_thorne._draw_thorne_walk(surface, boss, x, y, warpath_active)
        else:
            _NS_thorne._draw_thorne_idle(surface, boss, x, y, warpath_active)

        # ---------- Projectiles ----------
        if not portrait_hd:
            _NS_thorne._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_thorne._draw_viscous_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thorne._draw_bristleback_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorne._handle_quill_spray_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorne._draw_warpath_effect(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_thorne_idle(surface, boss, x, y, warpath=False):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_thorne._draw_shadow(surface, x, y + 48)
            _NS_thorne._draw_floating_dust(surface, x, y + 35, boss.pulse, warpath=warpath)
        _NS_thorne._draw_thorne_body(surface, x, y + bob, boss.direction, boss.pulse,
                          "idle", warpath=warpath,
                          detail=getattr(boss, "_portrait_hd", False))


    def _draw_thorne_walk(surface, boss, x, y, warpath=False):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_thorne._draw_shadow(surface, x + sway, y + 48)
            _NS_thorne._draw_floating_dust(surface, x + sway, y + 35, phase, trail=True,
                               facing=boss.direction, warpath=warpath)
        _NS_thorne._draw_thorne_body(surface, x + sway, y - bob, boss.direction, phase,
                          "walk", warpath=warpath,
                          detail=getattr(boss, "_portrait_hd", False))


    def _draw_thorne_attack(surface, boss, x, y, warpath=False):
        progress = getattr(boss, "_th_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Slight step forward during swing
        step = int(math.sin(progress * math.pi) * 3) * boss.direction
        if not getattr(boss, "_portrait_hd", False):
            _NS_thorne._draw_shadow(surface, x + step, y + 48)
            _NS_thorne._draw_floating_dust(surface, x + step, y + 35, boss.pulse, intense=True,
                               warpath=warpath)
        _NS_thorne._draw_thorne_body(surface, x + step, y, boss.direction, boss.pulse,
                          "attack", progress, warpath=warpath,
                          detail=getattr(boss, "_portrait_hd", False))


    # ===================================================================
    # BODY RENDERING - HD porcupine-boar warrior
    # ===================================================================
    def _draw_thorne_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, warpath=False, detail=False):
        """Renderer tubuh Thorne kualitas maksimum, 100% procedural.

        Dibangun sebagai bone rig 2D berlapis seperti Kaizen Masterwork:
        surai quill berumbai yang beranimasi per-quill, stance berkaki
        terpisah dengan cakar, perut berat ber-sabuk, vest perang sobek,
        pauldron baja berlapis, kepala babi hutan ber-taring, serta gada
        berduri yang posenya dihitung dari sendi/parameter animasi. Tidak
        ada PNG, sprite sheet, ataupun image.load.
        """
        _NS_thorne._draw_thorne_elite(
            surface, cx, cy, facing, phase, action, attack_progress,
            detail=detail, warpath=warpath)


    # ===================================================================
    # MASTERWORK RIG - bone rig 2D berlapis (setara Kaizen Masterwork)
    # ===================================================================
    def _draw_elite_quill(surface, bx, by, angle, length, width,
                          root, mid, light, tip, wave=0.0, outline=True):
        """Quill ber-pita seperti referensi: pangkal merah, tengah oranye,
        ujung kuning terang. Tiga segmen tapered menumpuk."""
        a = angle + wave
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa * width, ca * width
        p1 = (bx + ca * length * .45, by + sa * length * .45)
        p2 = (bx + ca * length * .78, by + sa * length * .78)
        p3 = (bx + ca * length, by + sa * length)
        if outline:
            _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"], [
                (bx + px + 1, by + py + 1), (bx - px + 1, by - py + 1),
                (p3[0] + 1, p3[1] + 1)])
        _NS_thorne._poly(surface, root, [
            (bx + px, by + py), (bx - px, by - py),
            (p1[0] - px * .6, p1[1] - py * .6), (p1[0] + px * .6, p1[1] + py * .6)])
        _NS_thorne._poly(surface, mid, [
            (p1[0] + px * .6, p1[1] + py * .6), (p1[0] - px * .6, p1[1] - py * .6),
            (p2[0] - px * .3, p2[1] - py * .3), (p2[0] + px * .3, p2[1] + py * .3)])
        _NS_thorne._poly(surface, light, [
            (p2[0] + px * .3, p2[1] + py * .3), (p2[0] - px * .3, p2[1] - py * .3),
            p3])
        _NS_thorne._aacircle(surface, tip, (int(p3[0]), int(p3[1])), 1)


    def _draw_elite_club(surface, cx, cy, facing, hand, angle, phase,
                         attacking=False):
        """Gada besi berduri prosedural: gagang kayu, cincin pommel,
        kepala flanged berlapis band, dan duri ber-rim dingin."""
        p = _NS_thorne.PALETTE
        f = 1 if facing >= 0 else -1
        A = angle if f > 0 else math.pi - angle
        ca, sa = math.cos(A), math.sin(A)
        hx, hy = cx + hand[0] * f, cy + hand[1]
        gx, gy = hx - ca * 6, hy - sa * 6
        head_x, head_y = hx + ca * 26, hy + sa * 26

        _NS_thorne._aaline(surface, p["shadow_deep"], (int(gx) + f, int(gy) + 1),
                           (int(head_x) + f, int(head_y) + 1), 6)
        _NS_thorne._aaline(surface, p["wood_dark"], (gx, gy), (head_x, head_y), 5)
        _NS_thorne._aaline(surface, p["wood_mid"], (gx, gy), (head_x, head_y), 3)
        _NS_thorne._aaline(surface, p["wood_light"], (gx, gy - 1),
                           (head_x, head_y - 1), 1)
        # leather grip wraps + pommel ring
        for i in range(3):
            _NS_thorne._aacircle(surface, p["leather_darkest"],
                                 (int(hx - ca * i * 2.4), int(hy - sa * i * 2.4)), 3)
        _NS_thorne._aacircle(surface, p["gold_dark"], (int(gx), int(gy)), 3)
        _NS_thorne._aacircle(surface, p["gold_mid"], (int(gx), int(gy)), 2)

        # flanged iron head: tiga band berlapis + rim dingin
        perp = (-sa, ca)
        for i, wdt in enumerate((8, 9, 7)):
            off = (i - 1) * 5
            mx, my = hx + ca * (30 + off), hy + sa * (30 + off)
            cols = (p["armor_darkest"], p["armor_dark"], p["armor_mid"])[i]
            _NS_thorne._poly(surface, cols, [
                (mx - perp[0] * wdt, my - perp[1] * wdt),
                (mx + perp[0] * wdt, my + perp[1] * wdt),
                (mx + ca * 4 + perp[0] * wdt, my + sa * 4 + perp[1] * wdt),
                (mx + ca * 4 - perp[0] * wdt, my + sa * 4 - perp[1] * wdt)])
        bx, by = hx + ca * 30, hy + sa * 30
        _NS_thorne._aaline(surface, p["armor_light"],
                           (bx - perp[0] * 6, by - perp[1] * 6),
                           (bx + perp[0] * 6, by + perp[1] * 6), 1)
        # duri sekeliling kepala gada
        for da, ln in ((0, 12), (-1.2, 9), (1.2, 9), (2.4, 8), (-2.4, 8)):
            _NS_thorne._draw_elite_quill(surface, bx, by, A + da, ln, 2,
                                         p["armor_darkest"], p["armor_dark"],
                                         p["armor_light"], p["armor_shine"])
        # ujung duri depan menyala kuning-hijau (ref)
        tipx, tipy = bx + math.cos(A) * 12, by + math.sin(A) * 12
        _NS_thorne._aacircle(surface, (*p["quill_shine"], 200), (int(tipx), int(tipy)), 2)
        _NS_thorne._aacircle(surface, (*p["goo_bright"], 160), (int(tipx), int(tipy)), 1)
        if attacking:
            _NS_thorne._aacircle(surface, (*p["quill_shine"], 150),
                                 (int(bx), int(by)), 5)


    def _draw_thorne_masterwork_details(surface, pt, f):
        """Micro-detail khusus portrait LOD. Di skala arena tanda-tanda ini
        runtuh menjadi noise, jadi LOD mengeluarkannya dari cache gameplay."""
        p = _NS_thorne.PALETTE
        # barb ticks pada crest quill
        for i in range(6):
            _NS_thorne._aaline(surface, p["quill_light"],
                               pt(-6 - i * 2, -40 - i),
                               pt(-10 - i * 2, -43 - i), 1)
        # serat bulu dada
        for i in range(5):
            _NS_thorne._aaline(surface, p["fur_high"],
                               pt(-6 + i * 3, -12 + i % 2),
                               pt(-5 + i * 3, -6 + i % 2), 1)
        # kerut moncong & alur taring
        _NS_thorne._aaline(surface, p["snout_light"], pt(17, -27), pt(21, -26), 1)
        _NS_thorne._aaline(surface, p["tusk_dark"], pt(14, -21), pt(16, -27), 1)
        # anyaman strap & jahitan sabuk
        for yy in (-12, -7, -2):
            _NS_thorne._aaline(surface, p["cloth_light"],
                               pt(-9, yy), pt(-6, yy + 2), 1)
        for xx in (-10, -6, 5, 9):
            _NS_thorne._aacircle(surface, p["leather_light"], pt(xx, 7), 1)
        # goresan pauldron + kilau rivet (bahu belakang)
        for a in (-.7, -.2, .3):
            _NS_thorne._aaline(surface, p["armor_mid"], pt(-12, -16),
                               pt(-12 - math.cos(a) * 5, -16 + math.sin(a) * 5), 1)
        _NS_thorne._aacircle(surface, p["armor_shine"], pt(-15, -15), 1)
        # highlight cakar kaki depan
        _NS_thorne._aaline(surface, p["tusk_light"], pt(10, 39), pt(14, 39), 1)


    def _draw_thorne_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False, warpath=False):
        """Rewrite penuh meniru sprite sheet referensi Bristleback:
        boar-porcupine kekar, crest quill kipas ber-pita, taring besar,
        strap hijau, pauldron+vambrace baja, gada berduri horizontal."""
        p = _NS_thorne.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.7)

        lean = (3 if walk else 0) * f
        root_y = int(math.sin(phase * .72) * .7)
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if attack:
            lean = int(math.sin(ap * math.pi) * 7) * f
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                _NS_thorne._poly(surface, p["shadow_deep"],
                                 [(x + f, y + 1) for x, y in pts])
            _NS_thorne._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_thorne._aaline(surface, p["shadow_deep"], aa, bb, width + 3)
            _NS_thorne._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_thorne._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        def qa(angle):
            return angle if f > 0 else math.pi - angle

        wave = math.sin(phase * 1.25)
        flare = 1.18 if attack and .15 < ap < .7 else 1.0

        # ═══ CREST QUILLS (di belakang semua) ═══
        if warpath:
            c_root, c_mid, c_light = p["rage_dark"], p["rage_mid"], p["rage_bright"]
            b_root, b_mid, b_light = p["rage_dark"], p["rage_dark"], p["rage_mid"]
            f_root, f_mid, f_light = p["rage_mid"], p["rage_bright"], p["quill_tip"]
        else:
            c_root, c_mid, c_light = p["quill_root"], p["quill_mid"], p["quill_light"]
            b_root, b_mid, b_light = p["quill_darkest"], p["quill_dark"], p["quill_mid"]
            f_root, f_mid, f_light = p["quill_mid"], p["quill_light"], p["quill_tip"]
        c_tip = p["quill_tip"]

        # lapisan belakang: lebih gelap & panjang, mengisi siluet kipas
        back = ((3, -34, -1.30, 26, 4), (-1, -36, -1.60, 32, 5),
                (-5, -35, -1.85, 35, 5), (-9, -33, -2.10, 35, 5),
                (-12, -29, -2.35, 33, 5), (-14, -24, -2.55, 30, 4),
                (-16, -18, -2.75, 27, 4), (-17, -12, -2.90, 23, 4),
                (-18, -6, -3.00, 20, 3))
        for i, (rx, ry, ang, ln, wd) in enumerate(back):
            w = wave * .03 * (1 + i % 3)
            _NS_thorne._draw_elite_quill(surface, *pt(rx - 2, ry + 2),
                                         qa(ang - .12), (ln + 4) * flare, wd,
                                         b_root, b_mid, b_light, b_light, wave=w)
        # lapisan utama ber-pita merah->oranye->kuning
        crest = ((5, -34, -1.15, 22, 4), (1, -36, -1.45, 28, 5),
                 (-3, -36, -1.70, 31, 5), (-7, -34, -1.95, 32, 5),
                 (-10, -30, -2.20, 30, 5), (-12, -25, -2.45, 28, 4),
                 (-14, -19, -2.65, 25, 4), (-15, -13, -2.80, 22, 4),
                 (-16, -7, -2.95, 19, 3))
        for i, (rx, ry, ang, ln, wd) in enumerate(crest):
            w = wave * .04 * (1 + i % 3)
            _NS_thorne._draw_elite_quill(surface, *pt(rx, ry), qa(ang),
                                         ln * flare, wd,
                                         c_root, c_mid, c_light, c_tip, wave=w)
        # lapisan depan pendek & terang di mahkota
        front = ((6, -32, -1.30, 15, 3), (2, -33, -1.60, 17, 3),
                 (-2, -32, -1.85, 18, 3), (-6, -30, -2.10, 17, 3))
        for i, (rx, ry, ang, ln, wd) in enumerate(front):
            _NS_thorne._draw_elite_quill(surface, *pt(rx, ry), qa(ang), ln, wd,
                                         f_root, f_mid, f_light, c_tip,
                                         wave=wave * .02)

        # ═══ KAKI: pendek & tebal, stance lebar (ref gempal) ═══
        leg_phase = stride if walk else 0.0
        rear_foot = (-11 - int(leg_phase * 5), 38 - int(abs(leg_phase) * 2))
        front_foot = (13 + int(leg_phase * 6), 38)
        for hip, knee, foot, shade in (
                ((-7, 13), (-11, 26), rear_foot, p["fur_darkest"]),
                ((8, 13), (11, 25), front_foot, p["fur_dark"])):
            poly(shade, [hip, (hip[0] + 10, hip[1]), (knee[0] + 7, knee[1]),
                         (foot[0] + 6, foot[1] - 5), (foot[0] - 6, foot[1] - 5),
                         (knee[0] - 5, knee[1])])
            limb(knee, (foot[0], foot[1] - 5), 9, p["fur_mid"], p["fur_light"])
            # kaki besar dengan 3 cakar putih
            poly(p["fur_darkest"], [(foot[0] - 8, foot[1] - 5), (foot[0] + 8, foot[1] - 5),
                                    (foot[0] + 9, foot[1] + 1), (foot[0] - 8, foot[1] + 1)])
            poly(p["fur_dark"], [(foot[0] - 7, foot[1] - 4), (foot[0] + 7, foot[1] - 4),
                                 (foot[0] + 8, foot[1]), (foot[0] - 7, foot[1])], False)
            for claw in (-5, 0, 5):
                poly(p["tusk_mid"], [(foot[0] + claw, foot[1]),
                                     (foot[0] + claw + 3, foot[1]),
                                     (foot[0] + claw + 2, foot[1] + 3)], False)
                _NS_thorne._aaline(surface, p["tusk_light"],
                                   pt(foot[0] + claw + 1, foot[1] + 1),
                                   pt(foot[0] + claw + 2, foot[1] + 2), 1)

        # ═══ TORSO: gempal & lebar seperti referensi ═══
        poly(p["fur_darkest"], [(-16, -18), (12, -20), (18, -8), (16, 10), (0, 14),
                                (-14, 10), (-19, -6)])
        poly(p["fur_dark"], [(-14, -16), (10, -18), (16, -8), (14, 9), (0, 12),
                             (-12, 9), (-17, -6)], False)
        poly(p["fur_mid"], [(-10, -14), (8, -16), (12, -8), (11, 6), (0, 10),
                            (-9, 6), (-13, -6)], False)
        # bidang dada terang + perut lebar terang bawah-depan (ref)
        poly(p["fur_light"], [(0, -14), (7, -14), (10, -8), (7, -2), (1, -3)], False)
        poly(p["belly_dark"], [(0, 6), (13, 6), (16, 14), (10, 21), (0, 21), (-3, 13)], False)
        poly(p["belly_mid"], [(3, 8), (11, 8), (13, 14), (9, 18), (3, 17), (1, 12)], False)
        _NS_thorne._aaline(surface, p["belly_light"], pt(4, 12), pt(10, 12), 1)
        # serat bulu dada
        for i in range(4):
            dx = -5 + i * 4
            _NS_thorne._aaline(surface, p["fur_light"], pt(dx, -10), pt(dx + 1, -4), 1)
        # strap kain hijau menyilang X di dada (ref)
        _NS_thorne._aaline(surface, p["cloth_dark"], pt(-13, -15), pt(14, 4), 5)
        _NS_thorne._aaline(surface, p["cloth_mid"], pt(-13, -15), pt(14, 4), 3)
        _NS_thorne._aaline(surface, p["cloth_dark"], pt(14, -15), pt(-13, 4), 5)
        _NS_thorne._aaline(surface, p["cloth_mid"], pt(14, -15), pt(-13, 4), 3)
        _NS_thorne._aaline(surface, p["cloth_light"], pt(-13, -15), pt(14, 4), 1)
        # sabuk kulit + gesper baja + sash hijau (ref)
        _NS_thorne._aaline(surface, p["leather_darkest"], pt(-16, 6), pt(16, 6), 6)
        _NS_thorne._aaline(surface, p["leather_dark"], pt(-16, 5), pt(16, 5), 4)
        _NS_thorne._aaline(surface, p["leather_light"], pt(-15, 4), pt(15, 4), 1)
        poly(p["cloth_dark"], [(3, 8), (10, 8), (11, 17), (6, 20), (2, 16)], False)
        _NS_thorne._aaline(surface, p["cloth_light"], pt(4, 9), pt(8, 16), 1)
        _NS_thorne._rect(surface, p["armor_darkest"], (pt(-3, 4)[0], pt(-3, 4)[1], 6, 6), 1)
        _NS_thorne._rect(surface, p["armor_mid"], (pt(-2, 5)[0], pt(-2, 5)[1], 4, 4), 1)
        _NS_thorne._rect(surface, p["armor_light"], (pt(-1, 6)[0], pt(-1, 6)[1], 2, 2))

        # ═══ LENGAN BELAKANG: tebal, forearm+vambrace+kepalan di depan torso ═══
        if attack:
            rear_hand = (-7 + int(ap * 6), -2 + int(ap * 4))
        else:
            rear_hand = (-16, 5)
        limb((-10, -12), (-15, -3), 10, p["fur_dark"], p["fur_light"])
        limb((-15, -3), rear_hand, 9, p["fur_mid"], p["fur_high"])
        rhx, rhy = pt(*rear_hand)
        _NS_thorne._aacircle(surface, p["fur_darkest"], (rhx, rhy), 6)
        _NS_thorne._aacircle(surface, p["fur_dark"], (rhx, rhy), 5)
        for c in (-3, 1, 5):
            _NS_thorne._poly(surface, p["tusk_mid"], [(rhx + c - 1, rhy + 4),
                             (rhx + c + 2, rhy + 4), (rhx + c + 1, rhy + 7)])
        # vambrace baja berlapis + duri siku (ref)
        _NS_thorne._aaline(surface, p["shadow_deep"], pt(-18, -6), pt(-14, 1), 9)
        _NS_thorne._aaline(surface, p["armor_darkest"], pt(-18, -6), pt(-14, 1), 7)
        _NS_thorne._aaline(surface, p["armor_dark"], pt(-18, -6), pt(-14, 1), 5)
        _NS_thorne._aaline(surface, p["armor_mid"], pt(-18, -5), pt(-15, -1), 2)
        _NS_thorne._aaline(surface, p["armor_light"], pt(-18, -7), pt(-15, -7), 1)
        _NS_thorne._draw_elite_quill(surface, *pt(-18, -4), qa(math.pi - .5), 8, 2,
                                     p["armor_darkest"], p["armor_dark"],
                                     p["armor_light"], p["armor_shine"])
        # pauldron kubah besar berlapis di bahu belakang (ref)
        poly(p["armor_darkest"], [(-6, -21), (-14, -23), (-21, -17), (-20, -9),
                                  (-13, -6), (-7, -11)])
        poly(p["armor_dark"], [(-8, -20), (-14, -21), (-18, -16), (-17, -10),
                               (-12, -8), (-8, -12)], False)
        poly(p["armor_mid"], [(-9, -19), (-14, -20), (-16, -15), (-14, -11),
                              (-10, -13)], False)
        for i in range(3):
            yy = -18 + i * 3
            _NS_thorne._aaline(surface, p["armor_light"], pt(-9, yy),
                               pt(-17 + i, yy + 1), 1)
        _NS_thorne._aacircle(surface, p["gold_mid"], pt(-13, -18), 2)
        _NS_thorne._aacircle(surface, p["gold_light"], pt(-13, -19), 1)

        # ═══ KEPALA: boar BESAR & lebar, moncong, taring (ref) ═══
        poly(p["fur_darkest"], [(-5, -34), (5, -38), (14, -34), (17, -26),
                                (14, -17), (4, -14), (-4, -18), (-8, -26)])
        poly(p["fur_dark"], [(-4, -33), (5, -36), (13, -32), (15, -26),
                             (12, -18), (4, -16), (-3, -19), (-6, -26)], False)
        poly(p["fur_mid"], [(-2, -31), (5, -34), (11, -30), (12, -24),
                            (10, -18), (3, -17), (-2, -21), (-4, -26)], False)
        poly(p["fur_light"], [(2, -32), (8, -31), (10, -25), (6, -21), (2, -25)], False)
        # moncong besar
        poly(p["snout_dark"], [(13, -29), (20, -28), (24, -24), (23, -18),
                               (15, -17), (12, -21)])
        poly(p["snout_mid"], [(14, -28), (19, -27), (22, -24), (21, -19),
                              (16, -18), (13, -22)], False)
        _NS_thorne._aacircle(surface, p["fur_darkest"], pt(21, -24), 2)
        _NS_thorne._aacircle(surface, p["fur_darkest"], pt(20, -20), 1)
        _NS_thorne._aacircle(surface, p["snout_light"], pt(17, -27), 1)
        # taring putih besar melengkung (ref)
        for off, ln, wdt in ((14, 13, 5), (18, 10, 4)):
            bx2, by2 = pt(off, -16)
            tx2, ty2 = pt(off + 4, -16 - ln)
            _NS_thorne._aaline(surface, p["shadow_deep"], (bx2 + f, by2 + 1),
                               (tx2 + f, ty2 + 1), wdt + 2)
            _NS_thorne._aaline(surface, p["tusk_dark"], (bx2, by2), (tx2, ty2), wdt)
            _NS_thorne._aaline(surface, p["tusk_mid"], (bx2, by2), (tx2, ty2), wdt - 1)
            _NS_thorne._aaline(surface, p["tusk_light"], (bx2, by2 - 1), (tx2, ty2), 1)
        # mata + alis marah
        ex, ey = pt(7, -30)
        if warpath:
            _NS_thorne._rect(surface, p["rage_bright"], (ex - 2, ey - 1, 5, 3))
            _NS_thorne._rect(surface, p["rage_light"], (ex - 1, ey, 3, 1))
        else:
            _NS_thorne._rect(surface, p["eye_iris"], (ex - 2, ey - 1, 5, 3))
            _NS_thorne._rect(surface, p["eye_iris_light"], (ex - 1, ey - 1, 2, 2))
        _NS_thorne._rect(surface, p["eye_pupil"], (ex, ey, 1, 1))
        _NS_thorne._rect(surface, p["white"], (ex + 1, ey - 1, 1, 1))
        _NS_thorne._aaline(surface, p["fur_darkest"], pt(4, -33), pt(11, -32), 2)
        # telinga kecil
        poly(p["fur_darkest"], [(-2, -36), (-7, -42), (1, -39)], False)
        poly(p["snout_dark"], [(-2, -37), (-5, -40), (0, -38)], False)

        # ═══ LENGAN GADA + GADA ═══
        if attack:
            if ap < .3:
                t = ap / .3
                hand = (12 - int(t * 3), -6 - int(t * 6))
                angle = .15 - t * 2.6
            elif ap < .62:
                t = (ap - .3) / .32
                hand = (9 + int(t * 8), -12 + int(t * 13))
                angle = -2.45 + t * 2.75
            else:
                t = (ap - .62) / .38
                hand = (17 - int(t * 4), 1)
                angle = .30 - t * .15
        else:
            hand = (14, 0)
            angle = .10
        elbow = ((hand[0] + 10) // 2, (hand[1] - 13) // 2)
        limb((11, -15), elbow, 11, p["fur_dark"], p["fur_high"])
        limb(elbow, hand, 10, p["fur_mid"], p["fur_light"])
        hx, hy = pt(*hand)
        _NS_thorne._aacircle(surface, p["fur_darkest"], (hx, hy), 6)
        _NS_thorne._aacircle(surface, p["fur_mid"], (hx - 1, hy - 1), 4)
        _NS_thorne._aaline(surface, p["cloth_mid"], (hx - 3, hy - 1), (hx + 3, hy - 1), 3)
        _NS_thorne._aaline(surface, p["cloth_light"], (hx - 3, hy - 2), (hx + 3, hy - 2), 1)
        _NS_thorne._draw_elite_club(surface, cx + lean, cy + root_y, f,
                                    hand, angle, phase, attack)
        if attack and .26 < ap < .78:
            t = max(0.0, min(1.0, (ap - .26) / .5))
            _NS_thorne._draw_club_swing_trail(surface, *pt(11, -15), f, angle, t * .8)

        # ═══ secondary motion ═══
        if walk:
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx, fy = pt(planted[0], planted[1])
                alpha = int(150 * contact)
                for i in range(4):
                    _NS_thorne._aacircle(
                        surface, (*p["fur_mid"], max(15, alpha - i * 24)),
                        (fx - f * (3 + i * 3), fy - i % 2), max(1, 3 - i // 2))
            for i in range(3):
                sy = cy - 7 + i * 9 + root_y
                _NS_thorne._aaline(surface, (*p["fur_light"], 95 - i * 18),
                                   (cx - f * (25 + i * 7), sy),
                                   (cx - f * (12 + i * 5), sy - 1), 1)
        elif attack:
            impact = max(0.0, 1.0 - abs(ap - .52) / .18)
            if impact > 0:
                A = angle if f > 0 else math.pi - angle
                bxw = cx + lean + f * hand[0] + math.cos(A) * 32
                byw = cy + root_y + hand[1] + math.sin(A) * 32
                for i in range(6):
                    ang = -1.2 + i * .48
                    length = 5 + int(impact * (8 + i % 2 * 4))
                    _NS_thorne._aaline(surface,
                                       (*p["quill_shine"], int(220 * impact)),
                                       (int(bxw), int(byw)),
                                       (int(bxw + math.cos(ang) * length * f),
                                        int(byw + math.sin(ang) * length)),
                                       1 if i % 2 else 2)
        else:
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx = cx + int(math.sin(phase + i * 2.1) * (18 + i * 3))
                my = cy + 28 - int(t * 58)
                _NS_thorne._aacircle(surface,
                                     (*p["fur_high"], int(110 * (1 - t))),
                                     (mx, my), 1)

        if warpath and not detail:
            for i in range(6):
                a2 = phase * .6 + i * math.pi / 3
                r = 30 + int(math.sin(phase + i) * 5)
                _NS_thorne._aacircle(surface, (*p["rage_bright"], 140),
                                     (cx + int(math.cos(a2) * r),
                                      cy + int(math.sin(a2) * r * .45)), 1)
            for i in range(3):
                sy = cy - 12 + i * 9 + root_y
                _NS_thorne._aaline(surface, (*p["rage_mid"], 150 - i * 35),
                                   (cx - f * (34 + i * 9), sy),
                                   (cx - f * (14 + i * 5), sy), 2)

        if detail:
            _NS_thorne._draw_thorne_masterwork_details(surface, pt, f)
    def _draw_quill_mane(surface, cx, cy, facing, phase, warpath=False):
        """The huge yellow-orange quill mane."""
        # Choose colors based on warpath (rage)
        if warpath:
            c_darkest = _NS_thorne.PALETTE["rage_dark"]
            c_dark = _NS_thorne.PALETTE["quill_dark"]
            c_mid = _NS_thorne.PALETTE["quill_mid"]
            c_light = _NS_thorne.PALETTE["rage_bright"]
            c_tip = _NS_thorne.PALETTE["quill_tip"]
        else:
            c_darkest = _NS_thorne.PALETTE["quill_darkest"]
            c_dark = _NS_thorne.PALETTE["quill_dark"]
            c_mid = _NS_thorne.PALETTE["quill_mid"]
            c_light = _NS_thorne.PALETTE["quill_light"]
            c_tip = _NS_thorne.PALETTE["quill_tip"]

        wave = math.sin(phase * 1.2) * 1.5

        # Big quills going up and back
        # Multiple layers of quills at different depths
        # Layer 1 (back layer - largest)
        back_quills = [
            # (base_x_offset, base_y_offset, length, angle_rad)
            (-8,  4, 26, -math.pi / 2 - 0.9),
            (-4,  0, 32, -math.pi / 2 - 0.5),
            ( 0, -2, 36, -math.pi / 2 - 0.2),
            ( 4,  0, 34, -math.pi / 2 + 0.1),
            ( 8,  2, 30, -math.pi / 2 + 0.4),
            (10,  5, 26, -math.pi / 2 + 0.6),
        ]
        for bx, by, length, angle in back_quills:
            _NS_thorne._draw_quill(surface, cx + bx, cy + by,
                        length + int(wave * 0.5),
                        angle + wave * 0.03,
                        thickness=3,
                        dark=c_darkest, mid=c_dark, light=c_mid, tip=c_light)

        # Layer 2 (middle)
        mid_quills = [
            (-10, 6, 20, -math.pi / 2 - 1.1),
            (-6,  3, 24, -math.pi / 2 - 0.7),
            (-2,  0, 28, -math.pi / 2 - 0.3),
            ( 2,  0, 30, -math.pi / 2 + 0.0),
            ( 6,  2, 26, -math.pi / 2 + 0.3),
            (10,  5, 22, -math.pi / 2 + 0.7),
        ]
        for bx, by, length, angle in mid_quills:
            _NS_thorne._draw_quill(surface, cx + bx, cy + by,
                        length + int(wave * 0.3),
                        angle + wave * 0.02,
                        thickness=2,
                        dark=c_dark, mid=c_mid, light=c_light, tip=c_tip)

        # Layer 3 (front - shorter)
        front_quills = [
            (-9, 8, 14, -math.pi / 2 - 1.0),
            (-5, 5, 18, -math.pi / 2 - 0.5),
            ( 0, 3, 22, -math.pi / 2 - 0.1),
            ( 4, 4, 20, -math.pi / 2 + 0.2),
            ( 8, 7, 16, -math.pi / 2 + 0.6),
        ]
        for bx, by, length, angle in front_quills:
            _NS_thorne._draw_quill(surface, cx + bx, cy + by,
                        length + int(wave * 0.2),
                        angle + wave * 0.02,
                        thickness=2,
                        dark=c_mid, mid=c_light, light=c_tip, tip=c_tip)

        # Small quills on back (going backward)
        back_side = -facing
        for i in range(4):
            by_off = 8 + i * 4
            bx = cx + back_side * (8 + i)
            angle = math.pi if facing > 0 else 0
            angle -= 0.3 + i * 0.1  # tilt up a bit
            _NS_thorne._draw_quill(surface, bx, cy + by_off, 14 - i * 2,
                        angle, thickness=2,
                        dark=c_dark, mid=c_mid, light=c_light, tip=c_tip)


    def _draw_belly(surface, cx, cy, phase, facing):
        """Floating rounded belly - bottom of body."""
        sway = int(math.sin(phase * 0.6) * 2)

        # Big round belly
        belly_pts = [
            (cx - 14, cy - 2),
            (cx + 14, cy - 2),
            (cx + 18 + sway, cy + 8),
            (cx + 16, cy + 18),
            (cx + 10, cy + 24),
            (cx + 4, cy + 26),
            (cx - 4, cy + 26),
            (cx - 10, cy + 24),
            (cx - 16, cy + 18),
            (cx - 18 - sway, cy + 8),
        ]
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in belly_pts])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_darkest"], belly_pts)
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_dark"], [
            (cx - 13, cy - 1),
            (cx + 13, cy - 1),
            (cx + 15 + sway, cy + 8),
            (cx + 13, cy + 17),
            (cx + 5, cy + 23),
            (cx - 5, cy + 23),
            (cx - 13, cy + 17),
            (cx - 15 - sway, cy + 8),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_mid"], [
            (cx - 10, cy),
            (cx + 10, cy),
            (cx + 12 + sway, cy + 8),
            (cx + 9, cy + 16),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 9, cy + 16),
            (cx - 12 - sway, cy + 8),
        ])

        # Lighter belly patch (center)
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["belly_dark"], [
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 8, cy + 12),
            (cx + 5, cy + 18),
            (cx - 5, cy + 18),
            (cx - 8, cy + 12),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["belly_mid"], [
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 6, cy + 12),
            (cx + 3, cy + 16),
            (cx - 3, cy + 16),
            (cx - 6, cy + 12),
        ])
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["belly_light"],
                (cx - 3, cy + 8), (cx + 3, cy + 8), 1)

        # Belly button
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["fur_darkest"], (cx, cy + 13), 2)
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["belly_dark"], (cx, cy + 13), 1)

        # Belt across
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["leather_darkest"], (cx - 15, cy, 30, 5))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["leather_dark"], (cx - 14, cy + 1, 28, 3))
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["leather_light"],
                (cx - 13, cy + 2), (cx + 13, cy + 2), 1)

        # Belt pouches
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["leather_darkest"], (cx - 10, cy + 2, 4, 6))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["leather_dark"], (cx - 9, cy + 3, 2, 4))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["leather_darkest"], (cx + 6, cy + 2, 4, 6))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["leather_dark"], (cx + 7, cy + 3, 2, 4))

        # Gold buckle center
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["gold_dark"], (cx - 3, cy, 6, 5))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["gold_mid"], (cx - 2, cy + 1, 4, 3))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["gold_light"], (cx - 1, cy + 2, 2, 1))

        # Heavy clawed feet: Thorne is a ground bruiser, so the sprite
        # needs a broad, weighty stance instead of a floating fur fade.
        for side in (-1, 1):
            fx = cx + side * 8
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["fur_darkest"],
                              (fx - 5, cy + 22, 10, 8), border_radius=2)
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["fur_dark"],
                              (fx - 4, cy + 23, 9, 6), border_radius=2)
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["fur_mid"],
                              (fx - 3, cy + 23, 4, 3), border_radius=1)
            for claw in (-2, 1, 4):
                _NS_thorne._poly(surface, _NS_thorne.PALETTE["quill_tip"], [
                    (fx + claw, cy + 29), (fx + claw + 2, cy + 29),
                    (fx + claw + 1, cy + 32),
                ])


    def _draw_torso(surface, cx, cy, facing, phase, warpath=False):
        """Muscular torso with green vest and armor."""
        # Shadow
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 6 + 2), (cx + 12 + 2, cy - 6 + 2),
            (cx + 11 + 2, cy + 12 + 2), (cx - 11 + 2, cy + 12 + 2),
        ])

        # Fur base torso
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_darkest"], [
            (cx - 12, cy - 6), (cx + 12, cy - 6),
            (cx + 11, cy + 12), (cx - 11, cy + 12),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_dark"], [
            (cx - 11, cy - 5), (cx + 11, cy - 5),
            (cx + 10, cy + 11), (cx - 10, cy + 11),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_mid"], [
            (cx - 9, cy - 4), (cx + 9, cy - 4),
            (cx + 8, cy + 10), (cx - 8, cy + 10),
        ])

        # Green vest (torn/open) - shows through
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["cloth_dark"], [
            (cx - 10, cy - 4),
            (cx - 4, cy - 5),
            (cx - 3, cy + 12),
            (cx - 9, cy + 12),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["cloth_mid"], [
            (cx - 9, cy - 3),
            (cx - 4, cy - 4),
            (cx - 3, cy + 11),
            (cx - 8, cy + 11),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["cloth_dark"], [
            (cx + 4, cy - 5),
            (cx + 10, cy - 4),
            (cx + 9, cy + 12),
            (cx + 3, cy + 12),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["cloth_mid"], [
            (cx + 4, cy - 4),
            (cx + 9, cy - 3),
            (cx + 8, cy + 11),
            (cx + 3, cy + 11),
        ])
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["cloth_light"],
                (cx - 8, cy - 2), (cx - 7, cy + 10), 1)

        # Chest fur tuft in the middle
        for i in range(4):
            fx = cx - 3 + i * 2
            fy = cy - 3 + int(math.sin(i) * 1)
            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_dark"],
                    (fx, fy), (fx + 1, fy + 6), 1)
            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_light"],
                    (fx, fy + 1), (fx + 1, fy + 5), 1)

        # Leather straps crossing chest
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["leather_darkest"],
                (cx - 10, cy - 4), (cx + 8, cy + 6), 4)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["leather_dark"],
                (cx - 10, cy - 4), (cx + 8, cy + 6), 3)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["leather_mid"],
                (cx - 10, cy - 4), (cx + 8, cy + 6), 1)

        # Metal shoulder armor (facing side)
        armor_side = -facing  # opposite side gets big pauldron in art
        ax = cx + armor_side * 11
        ay = cy - 5

        # Pauldron - dome shape
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_darkest"], [
            (ax - 5, ay - 2),
            (ax + 5, ay - 2),
            (ax + 6, ay + 3),
            (ax + 4, ay + 8),
            (ax - 4, ay + 8),
            (ax - 6, ay + 3),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_dark"], [
            (ax - 4, ay - 1),
            (ax + 4, ay - 1),
            (ax + 5, ay + 3),
            (ax + 3, ay + 7),
            (ax - 3, ay + 7),
            (ax - 5, ay + 3),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_mid"], [
            (ax - 3, ay),
            (ax + 3, ay),
            (ax + 4, ay + 3),
            (ax + 2, ay + 6),
            (ax - 2, ay + 6),
            (ax - 4, ay + 3),
        ])
        # Highlight
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["armor_light"], (ax - 1, ay + 2), 2)
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["armor_shine"], (ax - 1, ay + 2), 1)
        # Rivets
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["armor_dark"], (ax - 3, ay + 5), 1)
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["armor_dark"], (ax + 3, ay + 5), 1)
        # Small spike on top of pauldron
        _NS_thorne._draw_quill(surface, ax, ay - 3, 5, -math.pi / 2, thickness=2,
                    dark=_NS_thorne.PALETTE["armor_darkest"], mid=_NS_thorne.PALETTE["armor_dark"],
                    light=_NS_thorne.PALETTE["armor_light"], tip=_NS_thorne.PALETTE["armor_shine"])

        # Rage cracks in torso when warpath
        if warpath:
            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["rage_light"],
                    (cx - 5, cy - 2), (cx - 3, cy + 4), 1)
            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["rage_bright"],
                    (cx + 3, cy - 1), (cx + 5, cy + 5), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Idle - one hand holds club forward, other hangs."""
        sway = int(math.sin(phase * 0.7) * 1)

        # CLUB arm (facing side - hold club forward)
        club_side = facing
        cs_x = cx + club_side * 11
        cs_y = cy + 3
        ce_x = cs_x + club_side * 7
        ce_y = cy + 5 + sway
        ch_x = ce_x + club_side * 6
        ch_y = ce_y + 2
        _NS_thorne._draw_arm_segment(surface, cs_x, cs_y, ce_x, ce_y)
        _NS_thorne._draw_arm_segment(surface, ce_x, ce_y, ch_x, ch_y)
        _NS_thorne._draw_hand(surface, ch_x, ch_y)

        # Club held horizontal
        _NS_thorne._draw_club(surface, ch_x, ch_y, facing, phase, angle=0.1)

        # OTHER arm (opposite - hanging)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 3
        oe_x = os_x + other_side * 5
        oe_y = cy + 12 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 8
        _NS_thorne._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_thorne._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_thorne._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack - club swing arc animation."""
        sway = int(math.sin(phase * 0.7) * 1)

        # Swing timing:
        # 0.0-0.25: windup (club back)
        # 0.25-0.6: swing forward (arc)
        # 0.6-1.0: recovery
        if progress < 0.25:
            t = progress / 0.25
            swing_angle = -0.5 + t * -1.0  # back
        elif progress < 0.6:
            t = (progress - 0.25) / 0.35
            swing_angle = -1.5 + t * 2.8  # sweep forward
        else:
            t = (progress - 0.6) / 0.4
            swing_angle = 1.3 - t * 1.8

        # Arm follows club
        cs_x = cx + facing * 10
        cs_y = cy + 3

        arm_length = 14
        ce_x = cs_x + int(math.cos(swing_angle) * arm_length * 0.5) * facing
        ce_y = cs_y + int(math.sin(swing_angle) * arm_length * 0.5) - 1
        ch_x = cs_x + int(math.cos(swing_angle) * arm_length) * facing
        ch_y = cs_y + int(math.sin(swing_angle) * arm_length) - 1

        _NS_thorne._draw_arm_segment(surface, cs_x, cs_y, ce_x, ce_y)
        _NS_thorne._draw_arm_segment(surface, ce_x, ce_y, ch_x, ch_y)
        _NS_thorne._draw_hand(surface, ch_x, ch_y)

        # Motion trail during active swing
        if 0.25 < progress < 0.7:
            t = (progress - 0.25) / 0.45
            _NS_thorne._draw_club_swing_trail(surface, cs_x, cs_y, facing, swing_angle, t)

        # CLUB
        _NS_thorne._draw_club(surface, ch_x, ch_y, facing, phase, angle=swing_angle,
                   attack=True)

        # OTHER arm - held up for balance
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 3
        oe_x = os_x + other_side * 6
        oe_y = cy + 4 + sway
        oh_x = oe_x + other_side * 4
        oh_y = oe_y + 6
        _NS_thorne._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_thorne._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_thorne._draw_hand(surface, oh_x, oh_y)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a furry muscular arm segment."""
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_darkest"], (x1, y1), (x2, y2), 7)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_dark"], (x1, y1), (x2, y2), 5)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_mid"], (x1, y1), (x2, y2), 3)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_light"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Furry paw/hand."""
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["fur_darkest"], (x, y), 4)
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["fur_dark"], (x, y), 3)
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["fur_mid"], (x - 1, y - 1), 2)
        # Claws
        for i in (-1, 0, 1):
            _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["tusk_dark"],
                      (x + i * 2, y + 2), 1)


    def _draw_club(surface, hx, hy, facing, phase, angle=0, attack=False):
        """Big spiked wooden club/mace."""
        # Handle extends from hand along angle
        ca, sa = math.cos(angle), math.sin(angle)
        # Handle length
        handle_len = 16
        head_offset = 22

        # Handle end (near hand - grip goes back a bit)
        grip_x = hx - ca * 4 * facing
        grip_y = hy - sa * 4

        # Head end (spike ball tip)
        head_x = hx + ca * head_offset * facing
        head_y = hy + sa * head_offset

        # Draw wooden handle
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["shadow_deep"],
                (grip_x + 2, grip_y + 2), (head_x + 2, head_y + 2), 6)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["wood_dark"], (grip_x, grip_y), (head_x, head_y), 5)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["wood_mid"], (grip_x, grip_y), (head_x, head_y), 3)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["wood_light"], (grip_x, grip_y), (head_x, head_y), 1)

        # Leather wrap on grip
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["leather_dark"],
                (grip_x, grip_y),
                (grip_x + ca * 6 * facing, grip_y + sa * 6), 5)
        for i in range(3):
            t = i * 0.15
            wx = grip_x + ca * t * 6 * facing
            wy = grip_y + sa * t * 6
            _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["leather_darkest"], (int(wx), int(wy)), 2)

        # Metal club head - cylindrical, spiky
        # Compute perpendicular for head width
        px = -sa * 6 * facing
        py = ca * 6

        # Head cylinder body
        head_pts = [
            (head_x - ca * 8 * facing + px, head_y - sa * 8 + py),
            (head_x + ca * 4 * facing + px, head_y + sa * 4 + py),
            (head_x + ca * 4 * facing - px, head_y + sa * 4 - py),
            (head_x - ca * 8 * facing - px, head_y - sa * 8 - py),
        ]
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_darkest"], head_pts)
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_dark"], [
            (head_x - ca * 7 * facing + px * 0.85, head_y - sa * 7 + py * 0.85),
            (head_x + ca * 3 * facing + px * 0.85, head_y + sa * 3 + py * 0.85),
            (head_x + ca * 3 * facing - px * 0.85, head_y + sa * 3 - py * 0.85),
            (head_x - ca * 7 * facing - px * 0.85, head_y - sa * 7 - py * 0.85),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_mid"], [
            (head_x - ca * 6 * facing + px * 0.55, head_y - sa * 6 + py * 0.55),
            (head_x + ca * 2 * facing + px * 0.55, head_y + sa * 2 + py * 0.55),
            (head_x + ca * 2 * facing - px * 0.55, head_y + sa * 2 - py * 0.55),
            (head_x - ca * 6 * facing - px * 0.55, head_y - sa * 6 - py * 0.55),
        ])
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["armor_light"],
                (head_x - ca * 5 * facing + px * 0.3, head_y - sa * 5 + py * 0.3),
                (head_x + ca * 1 * facing + px * 0.3, head_y + sa * 1 + py * 0.3), 1)

        # Spikes on club head
        spike_angles = [
            angle,  # forward tip
            angle - math.pi / 2 * facing,  # top
            angle + math.pi / 2 * facing,  # bottom
            angle - 0.7 * facing,
            angle + 0.7 * facing,
        ]
        spike_offsets_along = [4, -2, -2, 1, 1]  # position along the club head

        for a, along in zip(spike_angles, spike_offsets_along):
            sbx = head_x + ca * along * facing
            sby = head_y + sa * along
            spike_length = 8 if abs(along - 4) < 0.5 else 6
            _NS_thorne._draw_quill(surface, int(sbx), int(sby), spike_length, a,
                        thickness=2,
                        dark=_NS_thorne.PALETTE["armor_darkest"],
                        mid=_NS_thorne.PALETTE["armor_dark"],
                        light=_NS_thorne.PALETTE["armor_mid"],
                        tip=_NS_thorne.PALETTE["armor_shine"])

        # Rage glow when attack
        if attack:
            glow = int(math.sin(phase * 2) * 2 + 3)
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_shine"], 150),
                      (int(head_x), int(head_y)), 4 + glow)


    def _draw_club_swing_trail(surface, cx, cy, facing, current_angle, t):
        """Yellow crescent trail for club swing."""
        trail_span = 0.9 * (1 - t * 0.5)
        if facing >= 0:
            start_angle = current_angle - trail_span
        else:
            start_angle = current_angle - trail_span

        inner_r = 12
        outer_r = 34

        fade = int(180 * (1 - t))
        if fade < 20:
            return

        # Draw crescent as arcs
        if facing >= 0:
            a_start, a_end = start_angle, current_angle
        else:
            a_start, a_end = start_angle, current_angle

        _NS_thorne._draw_arc_pair(surface, cx, cy, inner_r, outer_r, a_start, a_end,
                       facing, fade)


    def _draw_arc_pair(surface, cx, cy, inner_r, outer_r, a_start, a_end,
                       facing, fade):
        """Crescent terisi untuk trail ayunan gada (ref: ATTACK CLUB)."""
        p = _NS_thorne.PALETTE
        segments = 12

        def ring(r0, r1, color):
            pts = []
            for i in range(segments + 1):
                ang = a_start + (a_end - a_start) * i / segments
                pts.append((cx + math.cos(ang) * r1 * facing,
                            cy + math.sin(ang) * r1))
            for i in range(segments, -1, -1):
                ang = a_start + (a_end - a_start) * i / segments
                pts.append((cx + math.cos(ang) * r0 * facing,
                            cy + math.sin(ang) * r0))
            _NS_thorne._poly(surface, color, pts)

        ring(inner_r, outer_r, (*p["quill_dark"], fade))
        ring(inner_r + (outer_r - inner_r) * .25, outer_r - 2,
             (*p["quill_mid"], fade))
        ring(inner_r + (outer_r - inner_r) * .5, outer_r - 4,
             (*p["quill_light"], max(20, fade - 60)))

        # Inner bright core
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            angle1 = a_start + (a_end - a_start) * t1
            angle2 = a_start + (a_end - a_start) * t2

            r_core = (inner_r + outer_r) * 0.5
            x1 = cx + math.cos(angle1) * r_core * facing
            y1 = cy + math.sin(angle1) * r_core
            x2 = cx + math.cos(angle2) * r_core * facing
            y2 = cy + math.sin(angle2) * r_core
            _NS_thorne._aaline(surface, (*p["quill_shine"], fade),
                    (x1, y1), (x2, y2), 1)


    def _draw_head(surface, cx, cy, facing, phase, warpath=False):
        """Boar/porcupine head with tusks."""
        # Head shape (bulky, snout forward)
        head_pts = [
            (cx - 9, cy - 4),
            (cx - 10, cy),
            (cx - 9, cy + 5),
            (cx - 5, cy + 8),
            (cx + facing * 12, cy + 8),  # snout side
            (cx + facing * 14, cy + 5),
            (cx + facing * 13, cy),
            (cx + facing * 10, cy - 4),
            (cx, cy - 6),
        ]
        if facing < 0:
            # Mirror
            pass
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_darkest"], head_pts)
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_dark"], [
            (cx - 8, cy - 3),
            (cx - 9, cy),
            (cx - 8, cy + 4),
            (cx - 5, cy + 7),
            (cx + facing * 11, cy + 7),
            (cx + facing * 13, cy + 4),
            (cx + facing * 12, cy),
            (cx + facing * 9, cy - 3),
            (cx, cy - 5),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_mid"], [
            (cx - 7, cy - 2),
            (cx - 8, cy),
            (cx - 6, cy + 3),
            (cx - 4, cy + 6),
            (cx + facing * 9, cy + 6),
            (cx + facing * 11, cy + 3),
            (cx + facing * 10, cy),
            (cx + facing * 8, cy - 2),
            (cx, cy - 4),
        ])

        # Snout (pinkish nose area at front)
        snout_x = cx + facing * 10
        snout_y = cy + 4

        _NS_thorne._poly(surface, _NS_thorne.PALETTE["snout_dark"], [
            (snout_x - facing * 2, snout_y - 3),
            (snout_x + facing * 4, snout_y - 2),
            (snout_x + facing * 5, snout_y + 2),
            (snout_x + facing * 3, snout_y + 4),
            (snout_x - facing * 2, snout_y + 3),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["snout_mid"], [
            (snout_x - facing * 1, snout_y - 2),
            (snout_x + facing * 3, snout_y - 1),
            (snout_x + facing * 4, snout_y + 2),
            (snout_x + facing * 2, snout_y + 3),
            (snout_x - facing * 1, snout_y + 2),
        ])
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["snout_light"],
                  (snout_x + facing * 2, snout_y - 1), 1)

        # Nostrils
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["fur_darkest"],
                  (snout_x + facing * 3, snout_y + 1), 1)
        _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["fur_darkest"],
                  (snout_x + facing * 3, snout_y - 1), 1)

        # Tusks - two curving up from mouth
        for side_off in (1, 3):
            tsx = snout_x - facing * side_off
            tsy = snout_y + 3
            # Curve up
            ttx = tsx + facing * 2
            tty = tsy - 5
            _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"], [
                (tsx + 1, tsy),
                (tsx + 2, tsy),
                (ttx + 1, tty),
            ])
            _NS_thorne._poly(surface, _NS_thorne.PALETTE["tusk_dark"], [
                (tsx - 1, tsy),
                (tsx + 1, tsy),
                (ttx, tty),
            ])
            _NS_thorne._poly(surface, _NS_thorne.PALETTE["tusk_mid"], [
                (tsx, tsy),
                (tsx + 1, tsy),
                (ttx, tty),
            ])
            _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["tusk_light"], (int(ttx), int(tty)), 1)

        # Eye (fierce)
        ex = cx + facing * 3
        ey = cy - 1
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["eye_white"], (ex - 2, ey, 4, 3))
        if warpath:
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["rage_bright"], (ex - 2, ey, 4, 3))
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["rage_light"], (ex - 1, ey + 1, 2, 1))
        else:
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["eye_iris"], (ex - 2, ey, 4, 3))
            _NS_thorne._rect(surface, _NS_thorne.PALETTE["eye_iris_light"], (ex - 1, ey, 2, 2))
        _NS_thorne._rect(surface, _NS_thorne.PALETTE["eye_pupil"], (ex, ey + 1, 1, 1))

        # Brow (angry)
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["fur_darkest"],
                (ex - 3, ey - 2), (ex + 3, ey - 1), 2)

        # Small ear on top (peeking through quills)
        ear_x = cx - facing * 2
        ear_y = cy - 4
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_darkest"], [
            (ear_x, ear_y),
            (ear_x - facing * 2, ear_y - 3),
            (ear_x + facing * 1, ear_y - 3),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["fur_dark"], [
            (ear_x, ear_y),
            (ear_x - facing * 1, ear_y - 2),
            (ear_x + facing * 1, ear_y - 2),
        ])

        # Small metal helmet piece on top of head
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_darkest"], [
            (cx - 4, cy - 5),
            (cx + 4, cy - 5),
            (cx + 3, cy - 2),
            (cx - 3, cy - 2),
        ])
        _NS_thorne._poly(surface, _NS_thorne.PALETTE["armor_dark"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_thorne._aaline(surface, _NS_thorne.PALETTE["armor_light"],
                (cx - 2, cy - 4), (cx + 2, cy - 4), 1)


    def _draw_body_particles(surface, cx, cy, phase, warpath=False):
        """Ambient particles around body."""
        if warpath:
            # Rage embers
            for i in range(10):
                angle = phase * 0.5 + i * math.pi / 5
                radius = 32 + int(math.sin(phase * 0.7 + i) * 8)
                px = cx + int(math.cos(angle) * radius)
                py = cy - 5 + int(math.sin(angle) * radius * 0.5)
                alpha = int(180 + math.sin(phase + i * 0.7) * 60)
                alpha = max(0, min(255, alpha))
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["rage_bright"], alpha), (px, py), 2)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_shine"], alpha), (px, py), 1)
        else:
            # Dust motes
            for i in range(6):
                angle = phase * 0.4 + i * math.pi / 3
                radius = 30 + int(math.sin(phase * 0.7 + i) * 6)
                px = cx + int(math.cos(angle) * radius)
                py = cy - 5 + int(math.sin(angle) * radius * 0.4)
                alpha = int(100 + math.sin(phase + i * 0.7) * 50)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["fur_light"], alpha), (px, py), 2)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["fur_high"], alpha), (px, py), 1)

        # Loose quills falling
        for i in range(3):
            t = (phase * 0.3 + i * 0.35) % 1.0
            fx = cx - 30 + int(t * 60)
            fy = cy - 30 + int(t * 60)
            alpha = int(200 * math.sin(t * math.pi))
            if alpha > 0:
                a = math.pi / 4 + i
                _NS_thorne._draw_quill(surface, fx, fy, 4, a, thickness=1,
                            dark=(*_NS_thorne.PALETTE["quill_darkest"], alpha),
                            mid=(*_NS_thorne.PALETTE["quill_dark"], alpha),
                            light=(*_NS_thorne.PALETTE["quill_light"], alpha),
                            tip=(*_NS_thorne.PALETTE["quill_tip"], alpha))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_dust(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False, warpath=False):
        """Dust/fur mist beneath floating Thorne."""
        strength = 1.5 if intense else 1.0

        dust_color = _NS_thorne.PALETTE["rage_dark"] if warpath else _NS_thorne.PALETTE["fur_dark"]

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*dust_color, min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising dust wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 22)
            alpha = max(0, min(255, int(180 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            base = _NS_thorne.PALETTE["rage_light"] if warpath else _NS_thorne.PALETTE["fur_mid"]
            _NS_thorne._aacircle(surface, (*base, alpha), (sx, sy), 5)
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["fur_high"], alpha), (sx, sy - 2), 3)

        # Loose quills orbiting
        for i in range(3):
            angle = phase * 0.9 + i * math.pi * 2 / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_thorne._draw_quill(surface, sx, sy, 5, angle, thickness=2)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["fur_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_thorne.PALETTE["fur_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_dust_aura(surface, x, y, phase):
        """Large background aura - dusty brown."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_thorne._aacircle(aura, (*_NS_thorne.PALETTE["fur_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_rage_aura(surface, x, y, phase):
        """Rage aura when warpath - red."""
        pulse = math.sin(phase * 0.8) * 0.3 + 0.7
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = int((80 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thorne._aacircle(aura, (*_NS_thorne.PALETTE["rage_dark"], min(255, alpha)),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))


    def _draw_ground_platform(surface, x, y, phase, skill):
        """Ground platform."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_thorne.PALETTE["fur_darkest"], 180),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_thorne.PALETTE["fur_dark"], 200),
                            (20, 14, 90, 16), 2)

        # Small quills embedded around ring
        for i in range(8):
            angle = phase * 0.2 + i * math.pi / 4
            sx = 65 + int(math.cos(angle) * 55)
            sy = 22 + int(math.sin(angle) * 10)
            _NS_thorne._draw_quill(ring, sx, sy, 5,
                        angle + math.pi / 2, thickness=1)

        if skill:
            color = _NS_thorne.PALETTE["rage_light"] if skill == "r" else _NS_thorne.PALETTE["quill_light"]
            pygame.draw.ellipse(ring, (*color, int(120 * pulse)),
                                (15, 8, 100, 28), 2)

        surface.blit(ring, (x - 65, y - 22))


    # ===================================================================
    # SKILL Q: VISCOUS NOSE
    # ===================================================================
    def _draw_viscous_ground(surface, boss, x, y, timer, phase):
        """Line indicator."""
        tx, ty = _NS_thorne._target_position(boss, x, y)
        # Dashed indicator
        for i in range(0, 20, 2):
            t1 = i / 20
            t2 = (i + 1) / 20
            _NS_thorne._aaline(surface, (*_NS_thorne.PALETTE["goo_mid"], 130),
                    (x + (tx - x) * t1, y + (ty - y) * t1 - 5),
                    (x + (tx - x) * t2, y + (ty - y) * t2 - 5), 2)


    def _draw_viscous_charge(surface, boss, x, y, timer, phase):
        """Charging goo at snout, then spits."""
        progress = max(0.0, min(1.0, 1 - timer / 40))
        facing = boss.direction

        snout_x = x + 20 * facing
        snout_y = y - 20

        if progress < 0.4:
            # Charging up
            t = progress / 0.4
            radius = int(3 + t * 5)
            pulse = math.sin(phase * 4) * 0.2 + 0.8
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_dark"], int(200 * pulse)),
                      (snout_x, snout_y), radius + 2)
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], int(220 * pulse)),
                      (snout_x, snout_y), radius)
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_bright"], int(220 * pulse)),
                      (snout_x - 1, snout_y - 1), radius // 2)

            # Drip below
            _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"],
                      (snout_x, snout_y + radius + 2), 2)

        elif progress < 0.5:
            # Spit! Spawn projectile once
            if not getattr(boss, "_th_goo_spawned", False):
                _NS_thorne._spawn_goo(boss, x, y)
                boss._th_goo_spawned = True
            # Muzzle flash
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_bright"], 200),
                      (snout_x, snout_y), 6)
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_light"], 240),
                      (snout_x, snout_y), 3)
        else:
            boss._th_goo_spawned = False


    # ===================================================================
    # SKILL W: BRISTLEBACK (defensive spike aura)
    # ===================================================================
    def _draw_bristleback_effect(surface, boss, x, y, timer, phase):
        """Golden aura + quills sticking out more aggressively."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Golden aura around body
        aura = pygame.Surface((120, 120), pygame.SRCALPHA)
        for radius in range(50, 10, -3):
            alpha = int((50 - radius) * 3 * pulse)
            pygame.draw.circle(aura, (*_NS_thorne.PALETTE["quill_shine"], min(255, alpha)),
                               (60, 60), radius, 2)
        surface.blit(aura, (x - 60, y - 60))

        # Extra quills bursting outward
        for i in range(16):
            angle = i * math.pi / 8 + phase * 0.3
            base_r = 30
            tip_r = 45 + int(math.sin(phase * 3 + i) * 3)
            bx = x + math.cos(angle) * base_r
            by = y - 10 + math.sin(angle) * base_r * 0.7
            tx = x + math.cos(angle) * tip_r
            ty = y - 10 + math.sin(angle) * tip_r * 0.7

            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["quill_darkest"], (bx, by), (tx, ty), 3)
            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["quill_dark"], (bx, by), (tx, ty), 2)
            _NS_thorne._aaline(surface, _NS_thorne.PALETTE["quill_light"], (bx, by), (tx, ty), 1)
            _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["quill_shine"], (int(tx), int(ty)), 2)
            _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["quill_tip"], (int(tx), int(ty)), 1)

        # Spark bursts on activation (first frames)
        if progress < 0.3:
            t = progress / 0.3
            burst_r = int(t * 40)
            alpha = int(200 * (1 - t))
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_shine"], alpha),
                      (x, y - 10), burst_r, 3)


    # ===================================================================
    # SKILL E: QUILL SPRAY
    # ===================================================================
    def _draw_quill_spray_ground(surface, boss, x, y, timer, phase):
        """Ground marker."""
        pass


    def _handle_quill_spray_skill(surface, boss, x, y, timer, phase):
        """Fires quills in bursts."""
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Preparation - charging up (quills stand up more)
        if progress < 0.3:
            pulse = math.sin(phase * 4) * 0.3 + 0.7
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_shine"], int(150 * pulse)),
                      (x, y - 20), int(25 * pulse), 2)

        # Fire quills at intervals
        if not hasattr(boss, "_th_spray_last"):
            boss._th_spray_last = -100

        if 0.3 < progress < 0.9:
            if timer % 6 == 0 and boss._th_spray_last != timer:
                _NS_thorne._spawn_quill_spray(boss, x, y)
                boss._th_spray_last = timer

        if progress < 0.2:
            boss._th_spray_last = -100

        # Body glow while spraying
        if 0.3 < progress < 0.9:
            alpha = int(150 + math.sin(phase * 5) * 60)
            alpha = max(0, min(255, alpha))
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_light"], alpha),
                      (x, y - 15), 30, 2)


    # ===================================================================
    # SKILL R: WARPATH (self-buff with rage aura)
    # ===================================================================
    def _draw_warpath_effect(surface, boss, x, y, timer, phase):
        """Rage aura + shaking effect."""
        progress = max(0.0, min(1.0, 1 - timer / 120))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        # Rage circle
        for r in range(3):
            radius = int(30 + r * 8 + math.sin(phase * 2 + r) * 4)
            alpha = int((150 - r * 40) * pulse)
            if alpha > 0:
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["rage_light"], alpha),
                          (x, y - 5), radius, 2)

        # Rising rage flames
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.4
            r = 28
            px = x + int(math.cos(angle) * r)
            py = y - 5 + int(math.sin(angle) * r * 0.7)

            # Flame going up
            for h in range(3):
                fy = py - h * 5 - int((phase * 20 + i * 3) % 15)
                alpha = int(200 * (1 - h / 3))
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["rage_bright"], alpha),
                          (px, fy), 3 - h)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_shine"], alpha),
                          (px, fy), max(1, 2 - h))

        # Ground impact rings
        for r in range(2):
            radius = int(20 + r * 15 + (phase * 15 + r * 20) % 30)
            alpha = int(120 * (1 - (radius - 20) / 40))
            alpha = max(0, alpha)
            if alpha > 0:
                _NS_thorne._ellipse(surface, (*_NS_thorne.PALETTE["rage_mid"], alpha),
                         (x - radius, y + 25 - radius // 3,
                          radius * 2, radius * 2 // 3), 2)

        # Central pulse
        _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["rage_bright"], int(180 * pulse)),
                  (x, y - 10), int(15 * pulse))
        _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_shine"], int(220 * pulse)),
                  (x, y - 10), int(8 * pulse))


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_thorne.draw_thorne(surface, boss, x, y)

# ====================================================================
# vex.py
# ====================================================================
class _NS_vex:
    """Namespace vex - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Outworld Destroyer inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - ashen/void gray (barely visible under hood)
        "skin_darkest":   ( 25,  30,  45),
        "skin_dark":      ( 50,  60,  75),
        "skin_mid":       ( 80,  90, 110),
        "skin_light":     (110, 125, 145),

        # Robe / cloak - dark purple/black
        "robe_darkest":   ( 10,   8,  25),
        "robe_dark":      ( 25,  20,  45),
        "robe_mid":       ( 45,  35,  75),
        "robe_light":     ( 75,  60, 115),
        "robe_high":      (110,  90, 155),

        # Armor plating - blackish purple with slight sheen
        "armor_darkest":  (  8,  10,  20),
        "armor_dark":     ( 20,  25,  40),
        "armor_mid":      ( 45,  50,  75),
        "armor_light":    ( 80,  90, 120),
        "armor_shine":    (135, 150, 190),

        # Void energy - teal/cyan glow (primary)
        "void_darkest":   (  8,  40,  50),
        "void_dark":      ( 20,  85, 100),
        "void_mid":       ( 45, 165, 175),
        "void_light":     ( 95, 225, 220),
        "void_bright":    (155, 245, 235),
        "void_hot":       (200, 255, 245),
        "void_white":     (235, 255, 250),

        # Astral purple - E skill (imprisonment)
        "astral_darkest": ( 25,   8,  50),
        "astral_dark":    ( 60,  25, 110),
        "astral_mid":     (115,  55, 190),
        "astral_light":   (175, 110, 235),
        "astral_bright":  (215, 165, 250),
        "astral_hot":     (240, 220, 255),

        # Eye - glowing teal
        "eye_glow":       (155, 245, 235),
        "eye_bright":     (220, 255, 250),

        # Staff wood/metal
        "staff_dark":     ( 15,  20,  30),
        "staff_mid":      ( 40,  45,  60),
        "staff_light":    ( 75,  85, 105),

        # Gold trim / runes
        "rune_dark":      ( 30,  75,  85),
        "rune_mid":       ( 60, 155, 165),
        "rune_light":     (140, 235, 230),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vex._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_vex.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vex._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_vex._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_vex._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_vex._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_vex._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 250 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Void visual helpers
    # ---------------------------------------------------------------------------
    def _draw_void_flame(surface, cx, cy, size, angle, phase,
                         dark=None, mid=None, light=None, hot=None):
        """Draw a floating flame-like energy shape (for hair/crown)."""
        if dark is None:
            dark = _NS_vex.PALETTE["void_darkest"]
        if mid is None:
            mid = _NS_vex.PALETTE["void_dark"]
        if light is None:
            light = _NS_vex.PALETTE["void_mid"]
        if hot is None:
            hot = _NS_vex.PALETTE["void_bright"]

        ca, sa = math.cos(angle), math.sin(angle)
        flicker = math.sin(phase * 2 + cx * 0.1) * 1

        tip_x = cx + ca * (size + flicker)
        tip_y = cy + sa * (size + flicker)
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.4
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.4
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.4
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.4

        _NS_vex._poly(surface, dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        _NS_vex._poly(surface, mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_vex._aaline(surface, light, (cx, cy), (tip_x, tip_y), 1)
        _NS_vex._aacircle(surface, hot, (int(tip_x), int(tip_y)), 1)


    def _draw_glow_orb(surface, cx, cy, radius, color_dark, color_mid,
                       color_hot, color_white=None):
        """Draw a soft glowing orb with layered halo."""
        if color_white is None:
            color_white = _NS_vex.PALETTE["white"]

        # Outer halo
        _NS_vex._aacircle(surface, (*color_dark, 100), (cx, cy), radius + 6)
        _NS_vex._aacircle(surface, (*color_mid, 150), (cx, cy), radius + 3)
        # Body
        _NS_vex._aacircle(surface, color_mid, (cx, cy), radius)
        _NS_vex._aacircle(surface, color_hot, (cx, cy), max(1, radius - 2))
        _NS_vex._aacircle(surface, color_white, (cx - 1, cy - 1), max(1, radius - 4))


    def _draw_rune_ring(surface, cx, cy, radius, phase, color, alpha=200,
                        segments=8):
        """Rotating rune ring."""
        for i in range(segments):
            a = phase * 0.5 + i * math.pi * 2 / segments
            px = cx + int(math.cos(a) * radius)
            py = cy + int(math.sin(a) * radius)
            _NS_vex._aacircle(surface, (*color, alpha), (px, py), 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_hot"], alpha), (px, py), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------------------
    class ArcaneOrbProjectile:
        """Basic teal arcane orb attack."""
        def __init__(self, sx, sy, tx, ty, speed=6.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_vex._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            # Trail - fading void wisps
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(20 + i * 14)
                r = max(1, 6 - (len(self.trail) - i) // 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], alpha), (tx, ty), r + 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha // 2),
                          (tx, ty), r)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha // 2),
                          (tx, ty), max(1, r - 2))

            if self.alive:
                px, py = int(self.x), int(self.y)

                # Soft outer glow
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], 130), (px, py), 14)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], 170), (px, py), 10)

                # Rotating rune particles around orb
                for i in range(4):
                    a = phase * 3 + i * math.pi / 2
                    r = 8 + int(math.sin(phase * 4 + i) * 2)
                    sx = px + int(math.cos(a) * r)
                    sy = py + int(math.sin(a) * r)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], 220),
                              (sx, sy), 2)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_hot"], 240),
                              (sx, sy), 1)

                # Main orb body
                _NS_vex._draw_glow_orb(surface, px, py, 6,
                               _NS_vex.PALETTE["void_dark"], _NS_vex.PALETTE["void_mid"],
                               _NS_vex.PALETTE["void_hot"], _NS_vex.PALETTE["void_white"])

                # Bright core
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (px - 1, py - 1), 1)


    class AstralOrbProjectile:
        """Astral Imprisonment purple orb - travels then creates bubble prison."""
        def __init__(self, sx, sy, tx, ty, speed=7.0,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            self.impact_frame = -1
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1

            if self.impact_frame >= 0:
                # Prison bubble stays for a while
                if self.age - self.impact_frame > 60:
                    self.alive = False
                return

            # Homing tiap frame ke target selama terbang (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_vex._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.impact_frame = self.age
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Prison bubble stage
            if self.impact_frame >= 0:
                elapsed = self.age - self.impact_frame
                t = min(1.0, elapsed / 60.0)

                # Grow-in phase
                if elapsed < 8:
                    grow = elapsed / 8
                elif elapsed > 50:
                    grow = max(0.0, 1 - (elapsed - 50) / 10)
                else:
                    grow = 1.0

                radius = int(28 * grow)
                if radius < 3:
                    return

                cx, cy = int(self.tx), int(self.ty)

                # Ground rune circle
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_dark"], 150),
                          (cx, cy + 15), radius, 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], 200),
                          (cx, cy + 15), radius - 3, 1)

                # Vertical energy beam column
                for h in range(radius, 0, -2):
                    alpha = int(140 * grow * (h / radius))
                    y_off = int(-h * 1.5)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], alpha),
                              (cx, cy + y_off), 4)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], alpha),
                              (cx, cy + y_off), 2)

                # Bubble sphere
                for r in range(radius, radius - 6, -1):
                    alpha = int(80 * grow)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_bright"], alpha),
                              (cx, cy), r, 1)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], int(60 * grow)),
                          (cx, cy), radius, 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], int(90 * grow)),
                          (cx, cy), radius - 2, 1)

                # Bubble highlight
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_hot"], int(180 * grow)),
                          (cx - radius // 2, cy - radius // 2),
                          max(1, radius // 4))

                # Rune ring rotating around
                _NS_vex._draw_rune_ring(surface, cx, cy, radius - 2, phase * 2,
                                _NS_vex.PALETTE["astral_bright"], alpha=200, segments=8)

                # Rising energy particles inside
                for i in range(6):
                    pt = (phase * 0.4 + i * 0.16) % 1.0
                    py_off = int(-pt * radius * 1.6 + radius * 0.5)
                    px_off = int(math.sin(phase * 2 + i) * (radius // 3))
                    alpha = int(220 * (1 - pt) * grow)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_hot"], alpha),
                              (cx + px_off, cy + py_off), 2)
                    _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                              (cx + px_off, cy + py_off), 1)
                return

            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 15)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_dark"], alpha), (tx, ty), r + 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], alpha // 2),
                          (tx, ty), r)

            # Traveling orb - dark void/black hole style
            if self.alive:
                px, py = int(self.x), int(self.y)

                # Glow ring
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], 200), (px, py), 10)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], 220), (px, py), 7)
                # Black center (portal)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"], (px, py), 5)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["astral_darkest"], (px, py), 3)

                # Rotating rune particles
                for i in range(4):
                    a = phase * 4 + i * math.pi / 2
                    r = 9
                    sx = px + int(math.cos(a) * r)
                    sy = py + int(math.sin(a) * r)
                    _NS_vex._aacircle(surface, _NS_vex.PALETTE["astral_bright"], (sx, sy), 2)
                    _NS_vex._aacircle(surface, _NS_vex.PALETTE["astral_hot"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_vx_last_x"):
            boss._vx_last_x = boss.x
            boss._vx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vx_last_x)
        dy = abs(boss.y - boss._vx_last_y)
        boss._vx_last_x = boss.x
        boss._vx_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vx_prev_timer", -1))
        active = bool(getattr(boss, "_vx_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._vx_attack_active = True
            active = True

        if active and timer <= 0:
            boss._vx_attack_active = False
            active = False

        boss._vx_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._vx_attack_frame = max(0, cooldown - timer) if active else 0
        boss._vx_attack_progress = (
            min(1.0, boss._vx_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_vx_projectiles"):
            boss._vx_projectiles = []
        for proj in boss._vx_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._vx_projectiles = [p for p in boss._vx_projectiles
                                if p.alive or p.dead_frames < 8]


    def _spawn_arcane_orb(boss, x, y):
        if not hasattr(boss, "_vx_projectiles"):
            boss._vx_projectiles = []
        tx, ty = _NS_vex._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Orb spawns from staff tip
        sx = x + 26 * facing
        sy = y - 20
        tgt = getattr(boss, "target", None)
        proj = _NS_vex.ArcaneOrbProjectile(
            sx, sy, tx, ty, speed=6.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._vx_projectiles.append(proj)


    def _spawn_astral_orb(boss, x, y):
        if not hasattr(boss, "_vx_projectiles"):
            boss._vx_projectiles = []
        tx, ty = _NS_vex._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 26 * facing
        sy = y - 20
        tgt = getattr(boss, "target", None)
        proj = _NS_vex.AstralOrbProjectile(
            sx, sy, tx, ty, speed=7.0,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._vx_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_vex(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vex._detect_moving(boss)
        _NS_vex._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_vx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        # Cyan rim-light keeps the crown, shoulder spikes, and staff orb
        # legible against dark terrain while preserving pixel edges.
        _NS_vex._draw_void_silhouette_glow(surface, x, y - 12, pulse)
        _NS_vex._draw_void_aura(surface, x, y, pulse)
        _NS_vex._draw_void_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "w":
            _NS_vex._draw_sanity_eclipse_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vex._draw_essence_flux_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vex._draw_astral_indicator(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_vex._draw_vex_attack(surface, boss, x, y)
        elif moving:
            _NS_vex._draw_vex_walk(surface, boss, x, y)
        else:
            _NS_vex._draw_vex_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_vex._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_vex._draw_arcane_orb_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vex._handle_astral_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vex._draw_sanity_eclipse(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vex._draw_essence_flux(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_vex_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        _NS_vex._draw_shadow(surface, x, y + 48)
        _NS_vex._draw_floating_void(surface, x, y + 35, boss.pulse)
        _NS_vex._draw_vex_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_vex_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_vex._draw_shadow(surface, x + sway, y + 48)
        _NS_vex._draw_floating_void(surface, x + sway, y + 35, phase, trail=True,
                           facing=boss.direction)
        _NS_vex._draw_vex_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_vex_attack(surface, boss, x, y):
        progress = getattr(boss, "_vx_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Basic attack TIDAK spawn renderer projectile (pakai generic
        # _entity.py yang homing & terarah). Arcane orb renderer hanya
        # saat skill aktif.
        if (getattr(boss, "active_skill", None) is not None
                and 0.5 < progress < 0.6
                and not getattr(boss, "_vx_proj_spawned", False)):
            _NS_vex._spawn_arcane_orb(boss, x, y)
            boss._vx_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._vx_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_vex._draw_shadow(surface, x + recoil, y + 48)
        _NS_vex._draw_floating_void(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_vex._draw_vex_body(surface, x + recoil, y, boss.direction, boss.pulse,
                       "attack", progress)
        _NS_vex._draw_orb_release_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING - HD void mage
    # ===================================================================
    def _draw_vex_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0):
        # Cloak/robe behind (tallest)
        _NS_vex._draw_cloak(surface, cx, cy, facing, phase, action)

        # Floating lower body (tattered robe)
        _NS_vex._draw_lower_robe(surface, cx, cy + 5, phase)

        # Torso with armor plating
        _NS_vex._draw_torso(surface, cx, cy - 8, facing, phase)

        # Arms & staff
        if action == "attack":
            _NS_vex._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_vex._draw_idle_arms(surface, cx, cy - 8, facing, phase, action)

        # Head with flaming void crown
        _NS_vex._draw_head_crown(surface, cx, cy - 28, facing, phase)

        # Body void particles
        _NS_vex._draw_body_particles(surface, cx, cy, phase)


    def _draw_cloak(surface, cx, cy, facing, phase, action):
        """Flowing tattered dark cloak."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cloak - jagged tattered edges
        cloak_outer = [
            (cx - 18, cy - 12),
            (cx - 24, cy),
            (cx - 26, cy + 12),
            (cx - 28 - int(wave), cy + 26),
            (cx - 24 - int(wave2), cy + 40),
            (cx - 15, cy + 46),
            (cx - 8, cy + 44),
            (cx, cy + 46),
            (cx + 8, cy + 44),
            (cx + 15, cy + 46),
            (cx + 24 + int(wave2), cy + 40),
            (cx + 28 + int(wave), cy + 26),
            (cx + 26, cy + 12),
            (cx + 24, cy),
            (cx + 18, cy - 12),
        ]
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_darkest"], cloak_outer)

        cloak_mid = [
            (cx - 15, cy - 10),
            (cx - 20, cy),
            (cx - 22, cy + 12),
            (cx - 24 - int(wave), cy + 24),
            (cx - 20 - int(wave2), cy + 36),
            (cx - 12, cy + 42),
            (cx, cy + 42),
            (cx + 12, cy + 42),
            (cx + 20 + int(wave2), cy + 36),
            (cx + 24 + int(wave), cy + 24),
            (cx + 22, cy + 12),
            (cx + 20, cy),
            (cx + 15, cy - 10),
        ]
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_dark"], cloak_mid)

        # Inner brighter layer
        cloak_inner = [
            (cx - 12, cy - 8),
            (cx - 16, cy + 2),
            (cx - 18, cy + 14),
            (cx - 16, cy + 26),
            (cx - 10, cy + 34),
            (cx + 10, cy + 34),
            (cx + 16, cy + 26),
            (cx + 18, cy + 14),
            (cx + 16, cy + 2),
            (cx + 12, cy - 8),
        ]
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_mid"], cloak_inner)

        # Cloak collar - spiky rising up on shoulders
        for side in (-1, 1):
            # Spikes rising up
            for i in range(3):
                spike_x = cx + side * (12 + i * 3)
                spike_y = cy - 8
                spike_h = 10 + i * 2
                _NS_vex._poly(surface, _NS_vex.PALETTE["robe_darkest"], [
                    (spike_x - 2, spike_y),
                    (spike_x + 2, spike_y),
                    (spike_x + side, spike_y - spike_h),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["robe_dark"], [
                    (spike_x - 1, spike_y - 1),
                    (spike_x + 1, spike_y - 1),
                    (spike_x + side, spike_y - spike_h + 1),
                ])
                _NS_vex._aaline(surface, _NS_vex.PALETTE["robe_high"],
                        (spike_x, spike_y - 2),
                        (spike_x + side, spike_y - spike_h + 1), 1)

        # Void runes glowing on cloak edges
        for i, (rx, ry) in enumerate([
            (cx - 20, cy + 6), (cx - 22, cy + 22), (cx - 18, cy + 36),
            (cx + 20, cy + 6), (cx + 22, cy + 22), (cx + 18, cy + 36),
        ]):
            pulse = math.sin(phase * 2 + i * 0.5) * 0.3 + 0.7
            alpha = int(180 * pulse)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], alpha), (rx, ry), 3)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha), (rx, ry), 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (rx, ry), 1)


    def _draw_lower_robe(surface, cx, cy, phase):
        """Floating tattered lower robe (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        wave = math.sin(phase * 0.9) * 2

        # Base robe
        robe = [
            (cx - 14, cy),
            (cx + 14, cy),
            (cx + 18 + sway, cy + 12),
            (cx + 14, cy + 22),
            (cx + 8, cy + 28),
            (cx + 2, cy + 30),
            (cx - 2, cy + 30),
            (cx - 8, cy + 28),
            (cx - 14, cy + 22),
            (cx - 18 - sway, cy + 12),
        ]
        _NS_vex._poly(surface, _NS_vex.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in robe])
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_darkest"], robe)
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_dark"], [
            (cx - 12, cy + 1),
            (cx + 12, cy + 1),
            (cx + 15 + sway, cy + 12),
            (cx + 11, cy + 20),
            (cx + 5, cy + 26),
            (cx - 5, cy + 26),
            (cx - 11, cy + 20),
            (cx - 15 - sway, cy + 12),
        ])
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_mid"], [
            (cx - 9, cy + 3),
            (cx + 9, cy + 3),
            (cx + 11 + sway, cy + 12),
            (cx + 6, cy + 20),
            (cx - 6, cy + 20),
            (cx - 11 - sway, cy + 12),
        ])

        # Highlight streaks
        for i in range(3):
            lx = cx - 8 + i * 8
            _NS_vex._aaline(surface, _NS_vex.PALETTE["robe_light"],
                    (lx, cy + 4), (lx + int(sway * 0.3), cy + 22), 1)

        # Jagged tattered bottom
        for i in range(8):
            tx = cx - 14 + i * 4
            ty = cy + 26 + int(math.sin(phase * 1.3 + i) * 3)
            length = 6 + int(math.sin(phase + i) * 2)
            _NS_vex._poly(surface, _NS_vex.PALETTE["robe_darkest"], [
                (tx - 2, cy + 22),
                (tx + 2, cy + 22),
                (tx + 1, ty + length),
                (tx - 1, ty + length),
            ])

        # Rune glyphs on robe front
        for i, off in enumerate((-6, 0, 6)):
            gx = cx + off
            gy = cy + 10
            pulse = math.sin(phase * 2 + i * 0.7) * 0.3 + 0.7
            alpha = int(180 * pulse)
            # Small vertical rune line
            _NS_vex._aaline(surface, (*_NS_vex.PALETTE["void_mid"], alpha),
                    (gx, gy - 3), (gx, gy + 3), 1)
            _NS_vex._aaline(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                    (gx, gy - 2), (gx, gy + 2), 1)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_hot"], alpha), (gx, gy), 1)


    def _draw_torso(surface, cx, cy, facing, phase):
        """Armored torso with void gem in the center."""
        # Shadow
        _NS_vex._poly(surface, _NS_vex.PALETTE["shadow_deep"], [
            (cx - 11 + 2, cy - 8 + 2), (cx + 11 + 2, cy - 8 + 2),
            (cx + 10 + 2, cy + 14 + 2), (cx + 4 + 2, cy + 18 + 2),
            (cx - 4 + 2, cy + 18 + 2), (cx - 10 + 2, cy + 14 + 2),
        ])

        # Base armor plate
        _NS_vex._poly(surface, _NS_vex.PALETTE["armor_darkest"], [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 10, cy + 14), (cx + 4, cy + 18),
            (cx - 4, cy + 18), (cx - 10, cy + 14),
        ])
        _NS_vex._poly(surface, _NS_vex.PALETTE["armor_dark"], [
            (cx - 10, cy - 7), (cx + 10, cy - 7),
            (cx + 8, cy + 12), (cx + 3, cy + 16),
            (cx - 3, cy + 16), (cx - 8, cy + 12),
        ])

        # Side highlight plating
        _NS_vex._poly(surface, _NS_vex.PALETTE["armor_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 10), (cx + 2, cy + 12),
            (cx - 2, cy + 12), (cx - 6, cy + 10),
        ])

        # Chest plate detail - V-shape armor grooves
        _NS_vex._aaline(surface, _NS_vex.PALETTE["armor_darkest"],
                (cx - 6, cy - 6), (cx, cy + 2), 2)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["armor_darkest"],
                (cx + 6, cy - 6), (cx, cy + 2), 2)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["armor_light"],
                (cx - 6, cy - 5), (cx, cy + 3), 1)

        # Central void gem (glowing teal)
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["armor_darkest"], (cx, cy + 5), 5)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], int(220 * gem_pulse)),
                  (cx, cy + 5), 4)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], int(240 * gem_pulse)),
                  (cx, cy + 5), 3)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(240 * gem_pulse)),
                  (cx - 1, cy + 4), 2)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (cx - 1, cy + 4), 1)

        # Shoulder pauldrons - spiky protrusions
        for side in (-1, 1):
            px = cx + side * 12
            py = cy - 6
            # Pauldron dome
            _NS_vex._poly(surface, _NS_vex.PALETTE["armor_darkest"], [
                (px - 4, py - 2), (px + 4, py - 2),
                (px + 5, py + 3), (px + 3, py + 8),
                (px - 3, py + 8), (px - 5, py + 3),
            ])
            _NS_vex._poly(surface, _NS_vex.PALETTE["armor_dark"], [
                (px - 3, py - 1), (px + 3, py - 1),
                (px + 4, py + 3), (px + 2, py + 7),
                (px - 2, py + 7), (px - 4, py + 3),
            ])
            _NS_vex._poly(surface, _NS_vex.PALETTE["armor_mid"], [
                (px - 2, py), (px + 2, py),
                (px + 3, py + 3), (px + 1, py + 6),
                (px - 1, py + 6), (px - 3, py + 3),
            ])
            # Highlight
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["armor_shine"], (px - 1, py + 2), 1)
            # Rune glow on pauldron
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(180 * gem_pulse)),
                      (px, py + 4), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Idle - one hand holds staff, other rests."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm (facing side)
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2
        se_x = ss_x + staff_side * 7
        se_y = cy + 4 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y + 2
        _NS_vex._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_vex._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_vex._draw_hand(surface, sh_x, sh_y)

        # Staff
        _NS_vex._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # OTHER arm (opposite side - resting under cloak)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 5
        oe_y = cy + 10 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 8
        _NS_vex._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_vex._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_vex._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack - staff aimed forward for casting arcane orb."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm extends forward
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2

        # Motion: windup -> thrust -> recover
        if progress < 0.3:
            t = progress / 0.3
            ext = t * 0.4
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            ext = 0.4 + t * 0.6  # thrust
        else:
            t = (progress - 0.55) / 0.45
            ext = 1.0 - t * 0.6

        aim_angle = -0.15
        se_x = ss_x + int((6 + ext * 4) * math.cos(aim_angle)) * staff_side
        se_y = ss_y + int((6 + ext * 4) * math.sin(aim_angle)) - 2
        sh_x = se_x + int((6 + ext * 6) * math.cos(aim_angle)) * staff_side
        sh_y = se_y + int((6 + ext * 6) * math.sin(aim_angle)) - 4

        _NS_vex._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_vex._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_vex._draw_hand(surface, sh_x, sh_y)
        _NS_vex._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # OTHER arm (steadying)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 6
        oe_y = cy + 6 + sway
        oh_x = oe_x + other_side * 4
        oh_y = oe_y + 6
        _NS_vex._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_vex._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_vex._draw_hand(surface, oh_x, oh_y)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_vex._aaline(surface, _NS_vex.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 6)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["robe_dark"], (x1, y1), (x2, y2), 4)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["robe_mid"], (x1, y1), (x2, y2), 2)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Ashen skeletal hand."""
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["skin_darkest"], (x, y), 3)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["skin_dark"], (x, y), 2)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["skin_mid"], (x - 1, y - 1), 1)


    def _draw_staff(surface, hx, hy, phase, side, casting=False, progress=0):
        """The void staff with glowing orb."""
        # Staff pole - long
        top_x = hx + side * 4
        top_y = hy - 42
        bot_x = hx - side * 2
        bot_y = hy + 18

        # Shadow
        _NS_vex._aaline(surface, _NS_vex.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Staff body
        _NS_vex._aaline(surface, _NS_vex.PALETTE["staff_dark"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["staff_mid"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["staff_light"], (top_x, top_y), (bot_x, bot_y), 1)

        # Wraps and rings
        for t in (0.3, 0.55, 0.8):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["armor_darkest"], (rx, ry), 3)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["armor_dark"], (rx, ry), 2)
            # Rune bead
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_bright"], (rx, ry), 1)

        # Staff head - crescent claw holder
        head_x, head_y = top_x, top_y - 2

        # Two curving claws forming a crescent that holds the orb
        for claw_side in (-1, 1):
            # Bezier-like curve
            segments = 5
            prev = (head_x, head_y + 4)
            for i in range(1, segments + 1):
                t = i / segments
                # Curve outward and up
                cx = head_x + claw_side * math.sin(t * math.pi) * 7
                cy = head_y + 4 - t * 12
                _NS_vex._aaline(surface, _NS_vex.PALETTE["staff_dark"], prev, (cx, cy), 4)
                _NS_vex._aaline(surface, _NS_vex.PALETTE["staff_mid"], prev, (cx, cy), 3)
                _NS_vex._aaline(surface, _NS_vex.PALETTE["staff_light"], prev, (cx, cy), 1)
                prev = (cx, cy)
            # Tip
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["staff_mid"], (int(prev[0]), int(prev[1])), 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["armor_shine"],
                      (int(prev[0]), int(prev[1])), 1)

        # Main orb - glowing teal
        orb_glow_size = 6
        if casting:
            orb_glow_size = 6 + int(math.sin(progress * math.pi) * 8)

        orb_x, orb_y = head_x, head_y - 3

        # Big outer glow
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], 130),
                  (orb_x, orb_y), orb_glow_size + 8)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], 180),
                  (orb_x, orb_y), orb_glow_size + 4)
        # Orb body
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_dark"], (orb_x, orb_y), orb_glow_size)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_mid"], (orb_x, orb_y), orb_glow_size - 1)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_light"], (orb_x, orb_y), orb_glow_size - 2)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (orb_x - 1, orb_y - 1),
                  max(1, orb_glow_size - 3))
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (orb_x - 1, orb_y - 1),
                  max(1, orb_glow_size - 4))

        # Rune particles rotating around
        for i in range(3):
            a = phase * 2 + i * math.pi * 2 / 3
            r = orb_glow_size + 2
            px = orb_x + int(math.cos(a) * r)
            py = orb_y + int(math.sin(a) * r)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (px, py), 1)

        # Pulsing bright halo
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(120 * pulse)),
                  (orb_x, orb_y), int(orb_glow_size + 2 * pulse), 1)


    def _draw_head_crown(surface, cx, cy, facing, phase):
        """Dark hooded face with glowing eye slit and flame crown."""
        # Hood outer
        hood_outer = [
            (cx - 12, cy - 4),
            (cx - 14, cy + 4),
            (cx - 12, cy + 12),
            (cx - 6, cy + 15),
            (cx + 6, cy + 15),
            (cx + 12, cy + 12),
            (cx + 14, cy + 4),
            (cx + 12, cy - 4),
            (cx + 8, cy - 12),
            (cx - 8, cy - 12),
        ]
        _NS_vex._poly(surface, _NS_vex.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in hood_outer])
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_darkest"], hood_outer)
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_dark"], [
            (cx - 11, cy - 3),
            (cx - 13, cy + 4),
            (cx - 11, cy + 11),
            (cx - 6, cy + 14),
            (cx + 6, cy + 14),
            (cx + 11, cy + 11),
            (cx + 13, cy + 4),
            (cx + 11, cy - 3),
            (cx + 7, cy - 11),
            (cx - 7, cy - 11),
        ])

        # Deep shadow face area (inside hood)
        face_area = [
            (cx - 7, cy),
            (cx - 8, cy + 4),
            (cx - 6, cy + 8),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 6, cy + 8),
            (cx + 8, cy + 4),
            (cx + 7, cy),
        ]
        _NS_vex._poly(surface, _NS_vex.PALETTE["shadow"], face_area)
        _NS_vex._poly(surface, _NS_vex.PALETTE["skin_darkest"], [
            (cx - 6, cy + 1),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx - 2, cy + 10),
            (cx + 2, cy + 10),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 6, cy + 1),
        ])

        # Glowing eyes (teal)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (-3, 3):
            # Glow halo
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], int(180 * eye_pulse)),
                      (cx + eye_x, cy + 5), 3)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], int(220 * eye_pulse)),
                      (cx + eye_x, cy + 5), 2)
            # Bright core
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["eye_glow"],
                      (cx + eye_x, cy + 5), 1)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["eye_bright"],
                      (cx + eye_x, cy + 5), 1)

        # Subtle mouth line (dark)
        _NS_vex._aaline(surface, _NS_vex.PALETTE["shadow"],
                (cx - 2, cy + 9), (cx + 2, cy + 9), 1)

        # Hood front / cowl (inner peaked)
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_darkest"], [
            (cx - 10, cy - 2),
            (cx - 6, cy - 8),
            (cx, cy - 11),
            (cx + 6, cy - 8),
            (cx + 10, cy - 2),
            (cx + 8, cy - 12),
            (cx - 8, cy - 12),
        ])
        _NS_vex._poly(surface, _NS_vex.PALETTE["robe_dark"], [
            (cx - 8, cy - 3),
            (cx - 5, cy - 7),
            (cx, cy - 10),
            (cx + 5, cy - 7),
            (cx + 8, cy - 3),
            (cx + 6, cy - 11),
            (cx - 6, cy - 11),
        ])

        # Void flame crown on top of hood (spiky flames of energy)
        flame_positions = [
            (-10, -10, 0.9, -math.pi / 2 - 0.7),
            (-6, -13, 1.1, -math.pi / 2 - 0.4),
            (-2, -15, 1.3, -math.pi / 2 - 0.1),
            (2, -15, 1.3, -math.pi / 2 + 0.1),
            (6, -13, 1.1, -math.pi / 2 + 0.4),
            (10, -10, 0.9, -math.pi / 2 + 0.7),
        ]
        for fx, fy, scale, base_angle in flame_positions:
            size = int(10 * scale + math.sin(phase * 2 + fx) * 1.5)
            _NS_vex._draw_void_flame(surface, cx + fx, cy + fy, size,
                             base_angle, phase)

        # Backing flame layer (bigger, darker)
        for fx, fy, scale, base_angle in flame_positions[::2]:
            size = int(14 * scale)
            _NS_vex._draw_void_flame(surface, cx + fx, cy + fy - 2, size,
                             base_angle, phase,
                             dark=_NS_vex.PALETTE["robe_darkest"],
                             mid=_NS_vex.PALETTE["void_darkest"],
                             light=_NS_vex.PALETTE["void_dark"],
                             hot=_NS_vex.PALETTE["void_mid"])

        # Small side flames on hood sides (going outward)
        _NS_vex._draw_void_flame(surface, cx - 13, cy - 2, 8, math.pi + 0.3, phase)
        _NS_vex._draw_void_flame(surface, cx + 13, cy - 2, 8, -0.3, phase)


    def _draw_body_particles(surface, cx, cy, phase):
        """Void particles floating around body."""
        for i in range(10):
            angle = phase * 0.5 + i * math.pi / 5
            radius = 30 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            alpha = max(0, min(255, alpha))
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha), (px, py), 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (px, py), 1)

        # Rising energy sparks
        for i in range(4):
            t = (phase * 0.4 + i * 0.25) % 1.0
            fx = cx - 25 + i * 15 + int(math.sin(phase + i) * 4)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], alpha), (fx, fy), 3)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (fx, fy), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_void(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Void mist beneath floating Vex."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vex.PALETTE["void_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising void wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], alpha), (sx, sy), 5)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha), (sx, sy - 2), 3)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting rune fragments
        for i in range(4):
            angle = phase * 1.0 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_dark"], (sx, sy), 3)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_mid"], (sx, sy), 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_bright"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 24)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_vex.PALETTE["void_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_void_silhouette_glow(surface, x, y, phase):
        """Layered cyan rim light for Vex's tall void-mage silhouette."""
        pulse = .72 + math.sin(phase * 1.4) * .16
        halo = pygame.Surface((104, 116), pygame.SRCALPHA)
        for radius, alpha in ((44, 9), (34, 15), (25, 22)):
            _NS_vex._aacircle(halo, (*_NS_vex.PALETTE["void_dark"],
                                      int(alpha * pulse)), (52, 58), radius)
        _NS_vex._aaline(halo, (*_NS_vex.PALETTE["void_mid"], int(40 * pulse)),
                         (36, 74), (21, 36), 2)
        _NS_vex._aaline(halo, (*_NS_vex.PALETTE["void_mid"], int(34 * pulse)),
                         (68, 57), (86, 32), 1)
        surface.blit(halo, (x - 52, y - 58))


    def _draw_void_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vex._aacircle(aura, (*_NS_vex.PALETTE["void_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_void_platform(surface, x, y, phase, skill):
        """Runic void circle on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_dark"], 180),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_mid"], 200),
                            (20, 14, 90, 16), 2)

        # Runic marks
        for i in range(8):
            angle = phase * 0.2 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 22)
            y1 = 22 + int(math.sin(angle) * 5)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_vex.PALETTE["void_light"], 180),
                             (x1, y1), (x2, y2), 1)

        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_vex.PALETTE["void_hot"], 220), (sx, sy), 2)

        if skill:
            color = _NS_vex.PALETTE["astral_light"] if skill == "e" else _NS_vex.PALETTE["void_bright"]
            pygame.draw.ellipse(ring, (*color, int(100 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_orb_release_flash(surface, x, y, facing, progress):
        """Flash when arcane orb is released."""
        if progress < 0.4 or progress > 0.7:
            return
        t = (progress - 0.4) / 0.3
        intensity = math.sin(t * math.pi)

        flash_x = x + 26 * facing
        flash_y = y - 20

        alpha = int(200 * intensity)
        radius = int(6 + intensity * 16)

        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                  (flash_x, flash_y), max(1, radius // 4))

        # Small streaks
        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_vex._aaline(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                    (flash_x, flash_y), (ex, ey), 1)


    # ===================================================================
    # SKILL Q: ARCANE ORB (charging)
    # ===================================================================
    def _draw_arcane_orb_charge(surface, boss, x, y, timer, phase):
        """Charging aura around Vex before empowered arcane orb."""
        progress = max(0.0, min(1.0, 1 - timer / 40))
        facing = boss.direction

        # Particles converging to staff tip
        tip_x = x + 26 * facing
        tip_y = y - 20

        for i in range(8):
            angle = phase * 3 + i * math.pi / 4
            r = 25 - int(progress * 15)
            px = tip_x + int(math.cos(angle) * r)
            py = tip_y + int(math.sin(angle) * r)
            alpha = int(200 * progress)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (px, py), 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (px, py), 1)


    # ===================================================================
    # SKILL E: ASTRAL IMPRISONMENT
    # ===================================================================
    def _draw_astral_indicator(surface, boss, x, y, timer, pulse):
        """Target indicator for astral imprisonment."""
        tx, ty = _NS_vex._target_position(boss, x, y)
        # Dashed line
        for i in range(0, 20, 2):
            t1 = i / 20
            t2 = (i + 1) / 20
            _NS_vex._aaline(surface, (*_NS_vex.PALETTE["astral_light"], 150),
                    (x + (tx - x) * t1, y + (ty - y) * t1 - 8),
                    (x + (tx - x) * t2, y + (ty - y) * t2 - 8), 2)
        # Circle marker
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], 150), (tx, ty), 22, 2)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], 180), (tx, ty), 18, 1)


    def _handle_astral_skill(surface, boss, x, y, timer, phase):
        """Spawns the astral orb once at start."""
        if not getattr(boss, "_vx_astral_spawned", False):
            _NS_vex._spawn_astral_orb(boss, x, y)
            boss._vx_astral_spawned = True
        if timer < 5:
            boss._vx_astral_spawned = False


    # ===================================================================
    # SKILL W: SANITY'S ECLIPSE (spike field)
    # ===================================================================
    def _draw_sanity_eclipse_ground(surface, boss, x, y, timer, phase):
        """Growing dark circle indicator on ground at target."""
        tx, ty = _NS_vex._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        if progress < 0.3:
            # Warning ring growing
            t = progress / 0.3
            radius = int(20 + t * 40)
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_darkest"], int(200 * pulse)),
                      (tx, ty + 15), radius, 3)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], int(180 * pulse)),
                      (tx, ty + 15), radius - 4, 2)
            # Central portal
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"], (tx, ty + 15), 8)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_darkest"], (tx, ty + 15), 5)


    def _draw_sanity_eclipse(surface, boss, x, y, timer, phase):
        """Green spike field explosion."""
        tx, ty = _NS_vex._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        if progress < 0.3:
            # Central portal charging (already drawn on ground)
            # Rising energy inside portal
            for i in range(4):
                t = (phase * 0.6 + i * 0.25) % 1.0
                py = ty + 15 - int(t * 20)
                alpha = int(220 * (1 - t))
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                          (tx, py), 3)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (tx, py), 1)
        else:
            # Spikes erupt outward
            t = (progress - 0.3) / 0.7
            # Base black circle
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"], (tx, ty + 15), 10)

            # Spikes in ring pattern
            num_spikes = 12
            for i in range(num_spikes):
                angle = i * math.pi * 2 / num_spikes + phase * 0.1
                # Spike grows outward and up
                spike_grow = min(1.0, t * 2)
                dist = int(20 + spike_grow * 30)
                base_x = tx + int(math.cos(angle) * dist)
                base_y = ty + 15 + int(math.sin(angle) * dist * 0.4)

                # Spike shooting up
                spike_h = int(20 * spike_grow)
                if spike_h < 3:
                    continue

                _NS_vex._poly(surface, _NS_vex.PALETTE["void_darkest"], [
                    (base_x - 4, base_y + 4),
                    (base_x + 4, base_y + 4),
                    (base_x + 3, base_y - spike_h),
                    (base_x, base_y - spike_h - 3),
                    (base_x - 3, base_y - spike_h),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_dark"], [
                    (base_x - 3, base_y + 3),
                    (base_x + 3, base_y + 3),
                    (base_x + 2, base_y - spike_h + 1),
                    (base_x, base_y - spike_h - 2),
                    (base_x - 2, base_y - spike_h + 1),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_mid"], [
                    (base_x - 2, base_y + 2),
                    (base_x + 2, base_y + 2),
                    (base_x + 1, base_y - spike_h + 3),
                    (base_x, base_y - spike_h - 1),
                    (base_x - 1, base_y - spike_h + 3),
                ])
                # Bright edge
                _NS_vex._aaline(surface, _NS_vex.PALETTE["void_bright"],
                        (base_x, base_y - spike_h + 3),
                        (base_x, base_y + 2), 1)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"],
                          (base_x, base_y - spike_h), 1)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                          (base_x, base_y - spike_h), 1)

            # Inner ring of shorter spikes
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.15
                dist = 12
                base_x = tx + int(math.cos(angle) * dist)
                base_y = ty + 15 + int(math.sin(angle) * dist * 0.4)
                spike_h = int(12 * min(1.0, t * 2))
                if spike_h < 2:
                    continue
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_dark"], [
                    (base_x - 2, base_y + 2),
                    (base_x + 2, base_y + 2),
                    (base_x, base_y - spike_h),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_bright"], [
                    (base_x - 1, base_y + 1),
                    (base_x + 1, base_y + 1),
                    (base_x, base_y - spike_h + 1),
                ])

            # Ring shockwave
            ring_r = int(50 + t * 20)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(150 * (1 - t))),
                      (tx, ty + 15), ring_r, 2)


    # ===================================================================
    # SKILL R: ESSENCE FLUX (ultimate burst)
    # ===================================================================
    def _draw_essence_flux_ground(surface, boss, x, y, timer, phase):
        """Ground rune circle."""
        progress = max(0.0, min(1.0, 1 - timer / 80))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        radius = int(35 + progress * 20)

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_dark"], int(200 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_mid"], int(220 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runes
        for i in range(6):
            a = phase * 0.5 + i * math.pi / 3
            px = cx + int(math.cos(a) * (radius - 4))
            py = cy + int(math.sin(a) * (radius // 2 - 3))
            pygame.draw.circle(ring, (*_NS_vex.PALETTE["void_hot"], 240), (px, py), 3)
            pygame.draw.circle(ring, _NS_vex.PALETTE["white"], (px, py), 1)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_essence_flux(surface, boss, x, y, timer, phase):
        """Central burst of star-shaped energy."""
        progress = max(0.0, min(1.0, 1 - timer / 80))

        # Character-centered explosion
        burst_x = x
        burst_y = y - 10

        if progress < 0.35:
            # Charging - concentric rings inward
            t = progress / 0.35
            for i in range(3):
                r = int(50 - t * 30 - i * 8)
                if r > 2:
                    alpha = int(180 * t)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                              (burst_x, burst_y), r, 2)

            # Central charging orb
            core_r = int(4 + t * 10)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_dark"],
                      (burst_x, burst_y), core_r + 4)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_mid"],
                      (burst_x, burst_y), core_r + 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (burst_x, burst_y), core_r)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (burst_x, burst_y), core_r // 2)
        else:
            # Explosion phase - star burst
            t = (progress - 0.35) / 0.65

            # Central black hole void
            core_r = int(15 * (1 - t * 0.5))
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"],
                      (burst_x, burst_y), core_r)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_darkest"],
                      (burst_x, burst_y), core_r - 2)

            # Star burst rays (4 main rays + 4 diagonal)
            num_rays = 8
            for i in range(num_rays):
                angle = i * math.pi / 4 + phase * 0.05
                ray_len = int(30 + t * 50)
                if i % 2 == 0:
                    ray_len = int(ray_len * 1.4)  # cardinal rays longer

                # Ray as elongated triangle
                perp = angle + math.pi / 2
                width = 5 * (1 - t * 0.7)
                if width < 1:
                    width = 1

                tip_x = burst_x + math.cos(angle) * ray_len
                tip_y = burst_y + math.sin(angle) * ray_len
                base_l_x = burst_x + math.cos(perp) * width
                base_l_y = burst_y + math.sin(perp) * width
                base_r_x = burst_x - math.cos(perp) * width
                base_r_y = burst_y - math.sin(perp) * width

                alpha = int(220 * (1 - t))
                _NS_vex._poly(surface, (*_NS_vex.PALETTE["void_dark"], alpha), [
                    (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y),
                ])
                _NS_vex._poly(surface, (*_NS_vex.PALETTE["void_mid"], alpha), [
                    (tip_x, tip_y),
                    (burst_x + math.cos(perp) * width * 0.6,
                     burst_y + math.sin(perp) * width * 0.6),
                    (burst_x - math.cos(perp) * width * 0.6,
                     burst_y - math.sin(perp) * width * 0.6),
                ])
                _NS_vex._poly(surface, (*_NS_vex.PALETTE["void_bright"], alpha), [
                    (tip_x, tip_y),
                    (burst_x + math.cos(perp) * width * 0.3,
                     burst_y + math.sin(perp) * width * 0.3),
                    (burst_x - math.cos(perp) * width * 0.3,
                     burst_y - math.sin(perp) * width * 0.3),
                ])
                _NS_vex._aaline(surface, _NS_vex.PALETTE["white"],
                        (burst_x, burst_y), (tip_x, tip_y), 1)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                          (int(tip_x), int(tip_y)), 1)

            # Shockwave ring
            ring_r = int(20 + t * 60)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_light"], int(180 * (1 - t))),
                      (burst_x, burst_y), ring_r, 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(150 * (1 - t))),
                      (burst_x, burst_y), ring_r + 3, 1)

            # Debris sparks
            for i in range(12):
                spark_angle = i * math.pi * 2 / 12 + phase * 0.3
                spark_r = int(t * 50)
                sx = burst_x + int(math.cos(spark_angle) * spark_r)
                sy = burst_y + int(math.sin(spark_angle) * spark_r)
                alpha = int(220 * (1 - t))
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (sx, sy), 2)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_vex.draw_vex(surface, boss, x, y)

# ====================================================================
# zephyr.py
# ====================================================================
class _NS_zephyr:
    """Namespace zephyr - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Dark Willow inspired (pink/magenta fey)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - fair with warm undertone
        "skin_darkest":   (140,  85,  75),
        "skin_dark":      (195, 140, 115),
        "skin_mid":       (230, 180, 150),
        "skin_light":     (245, 210, 180),
        "skin_high":      (255, 230, 205),

        # Hair - crimson/magenta petals
        "hair_darkest":   ( 65,  15,  35),
        "hair_dark":      (130,  30,  55),
        "hair_mid":       (195,  50,  85),
        "hair_light":     (235,  90, 130),
        "hair_shine":     (255, 145, 175),
        "hair_tip":       (255, 200, 220),

        # Dress - deep magenta/purple petals
        "dress_darkest":  ( 35,  10,  40),
        "dress_dark":     ( 75,  25,  75),
        "dress_mid":      (125,  45, 115),
        "dress_light":    (175,  75, 155),
        "dress_high":     (215, 115, 190),

        # Corset - darker purple
        "corset_dark":    ( 30,  10,  35),
        "corset_mid":     ( 65,  25,  70),
        "corset_light":   (110,  50, 115),

        # Wings - translucent purple/pink
        "wing_darkest":   ( 60,  25,  85),
        "wing_dark":      (115,  55, 155),
        "wing_mid":       (175, 100, 215),
        "wing_light":     (220, 165, 240),
        "wing_shine":     (245, 215, 250),

        # Magic - hot pink/magenta glow
        "magic_darkest":  ( 55,   5,  40),
        "magic_dark":     (130,  20,  95),
        "magic_mid":      (220,  55, 155),
        "magic_light":    (255, 115, 200),
        "magic_bright":   (255, 175, 225),
        "magic_hot":      (255, 220, 240),
        "magic_white":    (255, 245, 250),

        # Bramble - dark thorny purple
        "bramble_dark":   ( 40,  10,  50),
        "bramble_mid":    ( 90,  30,  95),
        "bramble_light":  (155,  70, 155),

        # Staff wood
        "staff_dark":     ( 35,  20,  40),
        "staff_mid":      ( 75,  45,  75),
        "staff_light":    (120,  85, 120),

        # Gold - trim
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),

        # Eyes - amber/orange (mischievous)
        "eye_white":      (250, 240, 230),
        "eye_iris":       (200, 105,  40),
        "eye_iris_light": (245, 175,  80),
        "eye_pupil":      ( 15,  10,   5),

        # Lips
        "lips_dark":      (155,  40,  70),
        "lips_mid":       (215,  85, 120),

        # Butterfly
        "butterfly_dark": ( 60,  15,  55),
        "butterfly_mid":  (170,  60, 150),
        "butterfly_light":(240, 140, 220),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zephyr._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_zephyr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_zephyr._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_zephyr._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_zephyr._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_zephyr._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_zephyr._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 200 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------
    def _draw_petal(surface, cx, cy, size, angle, dark, mid, light, shine=None):
        """Draw a small pointed petal (flame-like)."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.3) * size * 0.4
        base_l_y = cy + math.sin(angle + 2.3) * size * 0.4
        base_r_x = cx + math.cos(angle - 2.3) * size * 0.4
        base_r_y = cy + math.sin(angle - 2.3) * size * 0.4

        _NS_zephyr._poly(surface, dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        _NS_zephyr._poly(surface, mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_zephyr._aaline(surface, light, (cx, cy), (tip_x, tip_y), 1)
        if shine:
            _NS_zephyr._aacircle(surface, shine, (int(tip_x), int(tip_y)), 1)


    def _draw_butterfly(surface, cx, cy, size, phase, alpha=255):
        """Small butterfly."""
        wing_flap = math.sin(phase * 4) * 0.4 + 0.6
        ws = int(size * wing_flap)
        if ws < 1:
            ws = 1

        # Wings (4 petals)
        dark_col = (*_NS_zephyr.PALETTE["butterfly_dark"], alpha) if alpha < 255 else _NS_zephyr.PALETTE["butterfly_dark"]
        mid_col = (*_NS_zephyr.PALETTE["butterfly_mid"], alpha) if alpha < 255 else _NS_zephyr.PALETTE["butterfly_mid"]
        light_col = (*_NS_zephyr.PALETTE["butterfly_light"], alpha) if alpha < 255 else _NS_zephyr.PALETTE["butterfly_light"]

        # Upper wings
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx - ws * 2, cy - ws - 1),
            (cx - ws, cy),
        ])
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx + ws * 2, cy - ws - 1),
            (cx + ws, cy),
        ])
        _NS_zephyr._poly(surface, mid_col, [
            (cx, cy),
            (cx - ws * 2 + 1, cy - ws),
            (cx - ws, cy),
        ])
        _NS_zephyr._poly(surface, mid_col, [
            (cx, cy),
            (cx + ws * 2 - 1, cy - ws),
            (cx + ws, cy),
        ])
        # Lower wings (smaller)
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx - ws, cy + ws + 1),
            (cx - ws // 2, cy),
        ])
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx + ws, cy + ws + 1),
            (cx + ws // 2, cy),
        ])
        # Wing tip highlights
        _NS_zephyr._aacircle(surface, light_col, (cx - ws + 1, cy - ws // 2), 1)
        _NS_zephyr._aacircle(surface, light_col, (cx + ws - 1, cy - ws // 2), 1)

        # Body
        _NS_zephyr._aaline(surface, dark_col, (cx, cy - 1), (cx, cy + 2), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------------------
    class MagicBoltProjectile:
        """Pink magic bolt basic attack."""
        def __init__(self, sx, sy, tx, ty, speed=7.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_zephyr._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            # Trail - streaks of pink
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(20 + i * 15)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], alpha), (tx, ty), r + 2)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha // 2),
                          (tx, ty), r)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha // 2),
                          (tx, ty), max(1, r - 2))

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                # Glow halos
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], 130), (px, py), 14)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], 180), (px, py), 10)

                # Streaking bolt shape - elongated with tapered tail
                length = 12
                for i in range(6):
                    t = i / 5.0
                    bx = px - ca * length * t
                    by = py - sa * length * t
                    r = max(1, int(5 * (1 - t)))
                    if r > 0:
                        alpha = int(240 * (1 - t * 0.6))
                        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha),
                                  (int(bx), int(by)), r + 1)
                        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_light"], alpha),
                                  (int(bx), int(by)), r)
                        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], alpha),
                                  (int(bx), int(by)), max(1, r - 1))

                # Bright core
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_white"], (px, py), 3)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"], (px, py), 1)

                # Tiny sparkle particles behind
                for i in range(3):
                    a = phase * 4 + i * math.pi * 2 / 3
                    pr = 4
                    spx = px - ca * 6 + int(math.cos(a) * pr)
                    spy = py - sa * 6 + int(math.sin(a) * pr)
                    _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (spx, spy), 1)


    class CasketProjectile:
        """Casket Curse - flying skull that traps target."""
        def __init__(self, sx, sy, tx, ty, speed=5.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            self.impact_frame = -1
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1

            if self.impact_frame >= 0:
                if self.age - self.impact_frame > 30:
                    self.alive = False
                return

            # Homing tiap frame ke target selama terbang (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_zephyr._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.impact_frame = self.age
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 16:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Impact explosion
            if self.impact_frame >= 0:
                elapsed = self.age - self.impact_frame
                t = elapsed / 30.0

                # Explosion star burst
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], int(200 * (1 - t))),
                          (int(self.tx), int(self.ty)), int(20 + t * 30))
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], int(220 * (1 - t))),
                          (int(self.tx), int(self.ty)), int(15 + t * 25))
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], int(240 * (1 - t))),
                          (int(self.tx), int(self.ty)), int(8 + t * 20))

                # Star rays
                for i in range(8):
                    a = i * math.pi / 4 + phase * 0.1
                    ray_len = int(20 + t * 30)
                    ex = int(self.tx + math.cos(a) * ray_len)
                    ey = int(self.ty + math.sin(a) * ray_len)
                    _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_light"],
                                      int(200 * (1 - t))),
                            (int(self.tx), int(self.ty)), (ex, ey), 2)
                    _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_hot"],
                                      int(220 * (1 - t))),
                            (int(self.tx), int(self.ty)), (ex, ey), 1)

                # Core white flash (early frames)
                if t < 0.4:
                    core_alpha = int(255 * (1 - t / 0.4))
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_white"], core_alpha),
                              (int(self.tx), int(self.ty)),
                              int(10 * (1 - t / 0.4)))
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["white"], core_alpha),
                              (int(self.tx), int(self.ty)),
                              max(1, int(5 * (1 - t / 0.4))))

                # Sparkle dust
                for i in range(10):
                    sa = i * math.pi * 2 / 10 + phase * 0.3
                    sr = int(t * 40)
                    sx = int(self.tx + math.cos(sa) * sr)
                    sy = int(self.ty + math.sin(sa) * sr)
                    alpha = int(200 * (1 - t))
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha),
                              (sx, sy), 2)
                    _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"], (sx, sy), 1)
                return

            # Trail - wispy magenta
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12)
                r = max(1, 4 - (len(self.trail) - i) // 2)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], alpha), (tx, ty), r + 3)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha), (tx, ty), r + 1)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha // 2),
                          (tx, ty), r)

            # Skull face projectile
            if self.alive:
                px, py = int(self.x), int(self.y)

                # Glow halo
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], 180), (px, py), 12)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], 200), (px, py), 9)

                # Skull shape (small pink/magenta)
                # Skull dome
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_dark"], (px, py), 6)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_mid"], (px, py - 1), 5)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_light"], (px - 1, py - 2), 3)

                # Eye sockets (dark)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["shadow_deep"], (px - 2, py - 1), 1)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["shadow_deep"], (px + 2, py - 1), 1)
                # Glow inside sockets
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (px - 2, py - 1), 1)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (px + 2, py - 1), 1)

                # Jaw teeth line
                _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["shadow_deep"],
                        (px - 2, py + 3), (px + 2, py + 3), 1)

                # Wispy tendrils behind
                for i in range(3):
                    a = math.pi + self.angle + (i - 1) * 0.3
                    r = 8
                    tx = px + math.cos(a) * r
                    ty = py + math.sin(a) * r
                    _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["magic_mid"],
                            (px, py), (tx, ty), 2)
                    _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["magic_bright"],
                            (px, py), (tx, ty), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_zp_last_x"):
            boss._zp_last_x = boss.x
            boss._zp_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zp_last_x)
        dy = abs(boss.y - boss._zp_last_y)
        boss._zp_last_x = boss.x
        boss._zp_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zp_prev_timer", -1))
        active = bool(getattr(boss, "_zp_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._zp_attack_active = True
            active = True

        if active and timer <= 0:
            boss._zp_attack_active = False
            active = False

        boss._zp_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._zp_attack_frame = max(0, cooldown - timer) if active else 0
        boss._zp_attack_progress = (
            min(1.0, boss._zp_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        for proj in boss._zp_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._zp_projectiles = [p for p in boss._zp_projectiles
                                if p.alive or p.dead_frames < 8]


    def _spawn_magic_bolt(boss, x, y):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # From staff orb
        sx = x + 22 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)
        proj = _NS_zephyr.MagicBoltProjectile(
            sx, sy, tx, ty, speed=7.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._zp_projectiles.append(proj)


    def _spawn_casket(boss, x, y):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 22 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)
        proj = _NS_zephyr.CasketProjectile(
            sx, sy, tx, ty, speed=5.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._zp_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_zephyr(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zephyr._detect_moving(boss)
        _NS_zephyr._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_zp_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 42) - 15
        )

        # ---------- Background layers ----------
        # Siluet cahaya lembut membuat Zephyr tetap terbaca di atas
        # terrain yang ramai, seperti sprite-sheet referensi: magenta
        # berada di belakang karakter, bukan menutupi detail wajahnya.
        _NS_zephyr._draw_fey_silhouette_glow(surface, x, y - 12, pulse)
        _NS_zephyr._draw_fey_aura(surface, x, y, pulse)
        _NS_zephyr._draw_fey_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_zephyr._draw_bramble_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zephyr._draw_shadow_realm_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zephyr._draw_bedlam_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zephyr._draw_casket_indicator(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_zephyr._draw_zephyr_attack(surface, boss, x, y)
        elif moving:
            _NS_zephyr._draw_zephyr_walk(surface, boss, x, y)
        else:
            _NS_zephyr._draw_zephyr_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_zephyr._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_zephyr._draw_bramble_maze(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zephyr._draw_shadow_realm(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zephyr._handle_casket_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zephyr._draw_bedlam(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_zephyr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        _NS_zephyr._draw_shadow(surface, x, y + 48)
        _NS_zephyr._draw_floating_sparkles(surface, x, y + 35, boss.pulse)
        _NS_zephyr._draw_zephyr_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_zephyr_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_zephyr._draw_shadow(surface, x + sway, y + 48)
        _NS_zephyr._draw_floating_sparkles(surface, x + sway, y + 35, phase, trail=True,
                                facing=boss.direction)
        _NS_zephyr._draw_zephyr_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_zephyr_attack(surface, boss, x, y):
        progress = getattr(boss, "_zp_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Basic attack TIDAK spawn renderer projectile (pakai generic
        # _entity.py yang homing & terarah). Magic bolt renderer hanya
        # saat skill aktif.
        if (getattr(boss, "active_skill", None) is not None
                and 0.5 < progress < 0.6
                and not getattr(boss, "_zp_proj_spawned", False)):
            _NS_zephyr._spawn_magic_bolt(boss, x, y)
            boss._zp_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._zp_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_zephyr._draw_shadow(surface, x + recoil, y + 48)
        _NS_zephyr._draw_floating_sparkles(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_zephyr._draw_zephyr_body(surface, x + recoil, y, boss.direction, boss.pulse,
                          "attack", progress)
        _NS_zephyr._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING - HD fairy fey
    # ===================================================================
    def _draw_zephyr_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        # Wings behind body (biggest, drawn first)
        _NS_zephyr._draw_wings(surface, cx, cy - 5, phase)

        # Petal skirt (lower body - no legs, floating)
        _NS_zephyr._draw_petal_skirt(surface, cx, cy + 5, phase)

        # Torso with corset
        _NS_zephyr._draw_torso(surface, cx, cy - 8, facing, phase)

        # Arms & staff
        if action == "attack":
            _NS_zephyr._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_zephyr._draw_idle_arms(surface, cx, cy - 8, facing, phase, action)

        # Head with fiery petal hair
        _NS_zephyr._draw_head(surface, cx, cy - 26, facing, phase)

        # Ambient particles
        _NS_zephyr._draw_body_particles(surface, cx, cy, phase)


    def _draw_wings(surface, cx, cy, phase):
        """Translucent fairy wings with 4 petal-like sections."""
        wing_flap = math.sin(phase * 3) * 0.15 + 0.85

        # Draw both wings (large, spread behind)
        for side in (-1, 1):
            # Upper wing (larger, extends up and out)
            w_scale = wing_flap
            u_tip_x = cx + side * int(22 * w_scale)
            u_tip_y = cy - int(24 * w_scale)
            u_mid_x = cx + side * int(15 * w_scale)
            u_mid_y = cy - int(10 * w_scale)

            # Upper wing outer edge (darker)
            upper_wing = [
                (cx + side * 3, cy - 5),
                (cx + side * 8, cy - 15),
                (u_tip_x, u_tip_y),
                (u_tip_x - side * 5, u_tip_y + 8),
                (u_mid_x, u_mid_y),
                (cx + side * 2, cy - 3),
            ]
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_darkest"], 130), upper_wing)
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_dark"], 150), [
                (cx + side * 3, cy - 5),
                (cx + side * 8, cy - 14),
                (u_tip_x - side * 1, u_tip_y + 1),
                (u_tip_x - side * 4, u_tip_y + 7),
                (u_mid_x - side * 1, u_mid_y + 1),
                (cx + side * 2, cy - 3),
            ])
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_mid"], 130), [
                (cx + side * 4, cy - 5),
                (cx + side * 9, cy - 13),
                (u_tip_x - side * 3, u_tip_y + 3),
                (u_tip_x - side * 5, u_tip_y + 6),
                (u_mid_x - side * 2, u_mid_y + 2),
                (cx + side * 3, cy - 3),
            ])

            # Lower wing (smaller, extends down and out)
            l_tip_x = cx + side * int(16 * w_scale)
            l_tip_y = cy + int(12 * w_scale)
            lower_wing = [
                (cx + side * 3, cy - 3),
                (cx + side * 8, cy + 2),
                (l_tip_x, l_tip_y),
                (l_tip_x - side * 4, l_tip_y - 2),
                (cx + side * 4, cy),
            ]
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_darkest"], 130), lower_wing)
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_dark"], 150), [
                (cx + side * 3, cy - 3),
                (cx + side * 7, cy + 1),
                (l_tip_x - side * 1, l_tip_y - 1),
                (l_tip_x - side * 3, l_tip_y - 3),
                (cx + side * 3, cy),
            ])

            # Vein structure: referensi punya sayap daun yang jelas,
            # bukan hanya bidang ungu datar. Garis tipis ini menambah
            # siluet pixel-art tanpa menaikkan ukuran hitbox karakter.
            root_x, root_y = cx + side * 4, cy - 4
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["wing_light"], 200),
                    (root_x, root_y), (u_tip_x, u_tip_y), 1)
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["wing_mid"], 175),
                    (root_x, root_y), (u_mid_x, u_mid_y), 1)
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["wing_light"], 145),
                    (u_mid_x, u_mid_y),
                    (u_tip_x - side * 4, u_tip_y + 8), 1)
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["wing_light"], 180),
                    (cx + side * 4, cy - 2), (l_tip_x, l_tip_y), 1)
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["wing_mid"], 145),
                    (cx + side * 4, cy - 2),
                    (l_tip_x - side * 3, l_tip_y - 2), 1)

            # Tip shine
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["wing_shine"], 220),
                      (u_tip_x, u_tip_y), 2)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["wing_shine"], 200),
                      (l_tip_x, l_tip_y), 1)

            # Sparkle on wings
            for i in range(2):
                sa = phase * 1.5 + i * 2 + side
                spx = cx + side * (10 + int(math.sin(sa) * 3))
                spy = cy - 5 + int(math.cos(sa) * 6)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], 220), (spx, spy), 1)


    def _draw_petal_skirt(surface, cx, cy, phase):
        """Layered petal skirt (dress bottom)."""
        sway = int(math.sin(phase * 0.6) * 2)

        # Base dark layer (larger, outer petals)
        outer_petals = [
            (cx - 14, cy),
            (cx + 14, cy),
            (cx + 18 + sway, cy + 10),
            (cx + 16, cy + 18),
            (cx + 12, cy + 24),
            (cx + 6, cy + 28),
            (cx + 2, cy + 30),
            (cx - 2, cy + 30),
            (cx - 6, cy + 28),
            (cx - 12, cy + 24),
            (cx - 16, cy + 18),
            (cx - 18 - sway, cy + 10),
        ]
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in outer_petals])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["dress_darkest"], outer_petals)

        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["dress_dark"], [
            (cx - 12, cy + 1),
            (cx + 12, cy + 1),
            (cx + 15 + sway, cy + 10),
            (cx + 13, cy + 17),
            (cx + 10, cy + 22),
            (cx + 4, cy + 26),
            (cx - 4, cy + 26),
            (cx - 10, cy + 22),
            (cx - 13, cy + 17),
            (cx - 15 - sway, cy + 10),
        ])

        # Middle layer (individual petal tips)
        for i, (px_off, py_off, size, ang) in enumerate([
            (-13, 8, 12, math.pi / 2 + 0.4),
            (-8, 14, 14, math.pi / 2 + 0.2),
            (-3, 18, 15, math.pi / 2 + 0.05),
            (3, 18, 15, math.pi / 2 - 0.05),
            (8, 14, 14, math.pi / 2 - 0.2),
            (13, 8, 12, math.pi / 2 - 0.4),
        ]):
            sway_off = int(math.sin(phase * 0.7 + i) * 1)
            _NS_zephyr._draw_petal(surface, cx + px_off, cy + py_off,
                        size + sway_off, ang,
                        _NS_zephyr.PALETTE["dress_darkest"], _NS_zephyr.PALETTE["dress_dark"],
                        _NS_zephyr.PALETTE["dress_mid"], _NS_zephyr.PALETTE["dress_light"])

        # Top overlay (bright inner petals)
        inner_petals = [
            (cx - 9, cy + 4),
            (cx + 9, cy + 4),
            (cx + 11 + sway, cy + 10),
            (cx + 8, cy + 16),
            (cx + 3, cy + 20),
            (cx - 3, cy + 20),
            (cx - 8, cy + 16),
            (cx - 11 - sway, cy + 10),
        ]
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["dress_mid"], inner_petals)

        # Highlight lines on inner
        for i in range(3):
            lx = cx - 6 + i * 6
            _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["dress_light"],
                    (lx, cy + 5), (lx + int(sway * 0.3), cy + 18), 1)

        # Small petals at bottom hem (extra ruffle)
        for i in range(5):
            px = cx - 10 + i * 5
            py = cy + 24 + int(math.sin(phase + i) * 1)
            _NS_zephyr._draw_petal(surface, px, py, 4, math.pi / 2,
                        _NS_zephyr.PALETTE["dress_darkest"], _NS_zephyr.PALETTE["dress_dark"],
                        _NS_zephyr.PALETTE["dress_light"])

        # Belt line
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["corset_dark"],
                (cx - 12, cy + 1), (cx + 12, cy + 1), 2)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["gold_dark"],
                (cx - 10, cy + 1), (cx + 10, cy + 1), 1)


    def _draw_torso(surface, cx, cy, facing, phase):
        """Corset over petal top."""
        # Shadow
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["shadow_deep"], [
            (cx - 10 + 2, cy - 7 + 2), (cx + 10 + 2, cy - 7 + 2),
            (cx + 9 + 2, cy + 13 + 2), (cx + 4 + 2, cy + 17 + 2),
            (cx - 4 + 2, cy + 17 + 2), (cx - 9 + 2, cy + 13 + 2),
        ])

        # Petal top layer (dress upper - purple)
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["dress_darkest"], [
            (cx - 10, cy - 7), (cx + 10, cy - 7),
            (cx + 9, cy + 13), (cx + 4, cy + 17),
            (cx - 4, cy + 17), (cx - 9, cy + 13),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["dress_dark"], [
            (cx - 9, cy - 6), (cx + 9, cy - 6),
            (cx + 7, cy + 11), (cx + 3, cy + 15),
            (cx - 3, cy + 15), (cx - 7, cy + 11),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["dress_mid"], [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 5, cy + 9), (cx + 2, cy + 11),
            (cx - 2, cy + 11), (cx - 5, cy + 9),
        ])

        # Chest/skin (upper - V neck)
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_dark"], [
            (cx - 5, cy - 7), (cx + 5, cy - 7),
            (cx + 2, cy - 2), (cx - 2, cy - 2),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_mid"], [
            (cx - 4, cy - 7), (cx + 4, cy - 7),
            (cx + 2, cy - 3), (cx - 2, cy - 3),
        ])
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["skin_light"],
                (cx - 3, cy - 6), (cx + 3, cy - 6), 1)

        # Corset over torso
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["corset_dark"], [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 7, cy + 11),
            (cx + 3, cy + 14),
            (cx - 3, cy + 14),
            (cx - 7, cy + 11),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["corset_mid"], [
            (cx - 7, cy - 1),
            (cx + 7, cy - 1),
            (cx + 6, cy + 10),
            (cx + 2, cy + 13),
            (cx - 2, cy + 13),
            (cx - 6, cy + 10),
        ])
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["corset_light"],
                (cx - 6, cy), (cx - 5, cy + 11), 1)

        # Corset lacing (X pattern)
        for i in range(3):
            y_off = cy + 1 + i * 3
            _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["gold_mid"],
                    (cx - 3, y_off), (cx + 3, y_off + 2), 1)
            _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["gold_mid"],
                    (cx + 3, y_off), (cx - 3, y_off + 2), 1)

        # Center gem
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_dark"], (cx, cy + 3), 2)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (cx, cy + 3), 1)

        # Shoulder petal detail
        for side in (-1, 1):
            sx = cx + side * 9
            sy = cy - 5
            _NS_zephyr._draw_petal(surface, sx, sy, 6, -math.pi / 2 + side * 0.5,
                        _NS_zephyr.PALETTE["dress_darkest"], _NS_zephyr.PALETTE["dress_dark"],
                        _NS_zephyr.PALETTE["dress_light"])


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Idle - one hand holds staff, other rests."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm (facing side)
        staff_side = facing
        ss_x = cx + staff_side * 9
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy + 4 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y + 2
        _NS_zephyr._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_zephyr._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_zephyr._draw_hand(surface, sh_x, sh_y)

        _NS_zephyr._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # OTHER arm (opposite - relaxed)
        other_side = -facing
        os_x = cx + other_side * 9
        os_y = cy + 2
        oe_x = os_x + other_side * 5
        oe_y = cy + 10 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 7
        _NS_zephyr._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_zephyr._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_zephyr._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack - staff forward, casting bolt."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm extends forward
        staff_side = facing
        ss_x = cx + staff_side * 9
        ss_y = cy + 2

        # Windup / thrust / recover
        if progress < 0.3:
            t = progress / 0.3
            ext = t * 0.4
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            ext = 0.4 + t * 0.6
        else:
            t = (progress - 0.55) / 0.45
            ext = 1.0 - t * 0.6

        aim_angle = -0.1
        se_x = ss_x + int((6 + ext * 3) * math.cos(aim_angle)) * staff_side
        se_y = ss_y + int((6 + ext * 3) * math.sin(aim_angle)) - 2
        sh_x = se_x + int((6 + ext * 5) * math.cos(aim_angle)) * staff_side
        sh_y = se_y + int((6 + ext * 5) * math.sin(aim_angle)) - 3

        _NS_zephyr._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_zephyr._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_zephyr._draw_hand(surface, sh_x, sh_y)
        _NS_zephyr._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # OTHER arm - lifted / gesture
        other_side = -facing
        os_x = cx + other_side * 9
        os_y = cy + 2
        oe_x = os_x + other_side * 5
        oe_y = cy + 4 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 3
        _NS_zephyr._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_zephyr._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_zephyr._draw_hand(surface, oh_x, oh_y)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Slim arm segment - fairy sized (skin visible + dress cloth)."""
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 4)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 3)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["skin_dark"], (x1, y1), (x2, y2), 2)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["skin_mid"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Tiny fairy hand."""
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["skin_darkest"], (x, y), 2)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["skin_mid"], (x, y), 1)


    def _draw_staff(surface, hx, hy, phase, side, casting=False, progress=0):
        """Twisted magical staff with pink orb."""
        # Staff pole
        top_x = hx + side * 4
        top_y = hy - 32
        bot_x = hx - side * 2
        bot_y = hy + 12

        # Shadow
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 4)
        # Wooden twisted staff
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["staff_dark"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["staff_mid"], (top_x, top_y), (bot_x, bot_y), 2)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["staff_light"], (top_x, top_y), (bot_x, bot_y), 1)

        # Small vine wraps
        for t in (0.3, 0.55, 0.8):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["dress_dark"], (rx, ry), 2)
            _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["dress_mid"], (rx, ry), 1)

        # Staff head - twisted claw holding orb
        head_x, head_y = top_x, top_y - 2

        # Curled tendrils holding the orb
        for tendril_side in (-1, 1):
            prev = (head_x, head_y + 3)
            segments = 5
            for i in range(1, segments + 1):
                t = i / segments
                tx = head_x + tendril_side * math.sin(t * math.pi) * 5
                ty = head_y + 3 - t * 8
                _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["staff_dark"], prev, (tx, ty), 2)
                _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["staff_mid"], prev, (tx, ty), 1)
                prev = (tx, ty)

        # Main pink orb
        orb_size = 5
        if casting:
            orb_size = 5 + int(math.sin(progress * math.pi) * 6)

        orb_x, orb_y = head_x, head_y - 2

        # Layered glow
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], 130),
                  (orb_x, orb_y), orb_size + 6)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], 180),
                  (orb_x, orb_y), orb_size + 3)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_mid"], (orb_x, orb_y), orb_size)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_light"], (orb_x, orb_y), orb_size - 1)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_bright"],
                  (orb_x - 1, orb_y - 1), max(1, orb_size - 2))
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"],
                  (orb_x - 1, orb_y - 1), max(1, orb_size - 3))
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"], (orb_x - 1, orb_y - 1), 1)

        # Bintang empat arah membuat orb terasa seperti fokus sihir
        # (bukan bola warna polos), mengikuti projectile di referensi.
        star_alpha = 150 if not casting else 220
        star_r = max(3, orb_size + 2)
        _NS_zephyr._aaline(surface,
                (*_NS_zephyr.PALETTE["magic_bright"], star_alpha),
                (orb_x - star_r, orb_y), (orb_x + star_r, orb_y), 1)
        _NS_zephyr._aaline(surface,
                (*_NS_zephyr.PALETTE["magic_hot"], star_alpha),
                (orb_x, orb_y - star_r), (orb_x, orb_y + star_r), 1)

        # Sparkle particles around
        for i in range(3):
            a = phase * 2 + i * math.pi * 2 / 3
            r = orb_size + 2
            px = orb_x + int(math.cos(a) * r)
            py = orb_y + int(math.sin(a) * r)
            _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (px, py), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Fairy head with fiery petal hair."""
        # Fiery hair mane BEHIND head first
        _NS_zephyr._draw_hair_mane(surface, cx, cy, phase, layer="back")

        # Small heart-shaped face
        face_points = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 3),
            (cx - 4, cy + 7),
            (cx - 1, cy + 9),
            (cx + 1, cy + 9),
            (cx + 4, cy + 7),
            (cx + 6, cy + 3),
            (cx + 5, cy - 1),
        ]
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in face_points])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_dark"], face_points)
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 5, cy + 3),
            (cx - 3, cy + 6),
            (cx - 1, cy + 8),
            (cx + 1, cy + 8),
            (cx + 3, cy + 6),
            (cx + 5, cy + 3),
            (cx + 4, cy),
        ])

        # Cheek highlights (mischievous blush)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["hair_shine"], (cx - 3, cy + 4), 1)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["hair_shine"], (cx + 3, cy + 4), 1)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["skin_light"], (cx - 3, cy + 4), 1)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["skin_light"], (cx + 3, cy + 4), 1)

        # Eyes (amber, mischievous grin)
        for eye_x in (-2, 2):
            _NS_zephyr._rect(surface, _NS_zephyr.PALETTE["eye_white"], (cx + eye_x - 1, cy + 2, 2, 2))
            _NS_zephyr._rect(surface, _NS_zephyr.PALETTE["eye_iris"], (cx + eye_x - 1, cy + 2, 2, 2))
            _NS_zephyr._rect(surface, _NS_zephyr.PALETTE["eye_iris_light"], (cx + eye_x, cy + 2, 1, 1))

        # Brows (arched mischievous)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["hair_darkest"],
                (cx - 4, cy + 1), (cx - 1, cy), 1)
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["hair_darkest"],
                (cx + 1, cy), (cx + 4, cy + 1), 1)

        # Small nose
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["skin_darkest"], (cx, cy + 5), 1)

        # Mischievous smile
        _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["lips_dark"],
                (cx - 2, cy + 7), (cx + 2, cy + 7), 1)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["lips_mid"], (cx, cy + 7), 1)

        # Small pointed ears (elf/fey)
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_dark"], [
            (cx - 6, cy + 2),
            (cx - 8, cy),
            (cx - 6, cy + 5),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_mid"], [
            (cx - 6, cy + 3),
            (cx - 7, cy + 1),
            (cx - 6, cy + 4),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_dark"], [
            (cx + 6, cy + 2),
            (cx + 8, cy),
            (cx + 6, cy + 5),
        ])
        _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["skin_mid"], [
            (cx + 6, cy + 3),
            (cx + 7, cy + 1),
            (cx + 6, cy + 4),
        ])

        # Fiery hair mane in FRONT/TOP
        _NS_zephyr._draw_hair_mane(surface, cx, cy, phase, layer="front")


    def _draw_hair_mane(surface, cx, cy, phase, layer="back"):
        """Fiery petal-like hair mane (magenta/crimson going upward like flames)."""
        if layer == "back":
            # Back layer (larger petals framing head)
            back_petals = [
                # Kelopak samping lebih lebar menciptakan mane berduri
                # khas referensi Dark Willow, sekaligus membingkai wajah.
                (-10, -1, 13, -math.pi / 2 - 1.00),
                (-7, -4, 15, -math.pi / 2 - 0.55),
                (10, -1, 13, -math.pi / 2 + 1.00),
                (7, -4, 15, -math.pi / 2 + 0.55),
                (0, -3, 11, math.pi / 2 + 3.14),
            ]
            for bx, by, sz, ang in back_petals:
                flicker = int(math.sin(phase * 2 + bx * 0.1) * 1)
                _NS_zephyr._draw_petal(surface, cx + bx, cy + by, sz + flicker, ang,
                            _NS_zephyr.PALETTE["hair_darkest"], _NS_zephyr.PALETTE["hair_dark"],
                            _NS_zephyr.PALETTE["hair_mid"], _NS_zephyr.PALETTE["hair_shine"])
        else:
            # Front top layer - flame petals rising up
            top_petals = [
                (-6, -6, 12, -math.pi / 2 - 0.7),
                (-3, -8, 15, -math.pi / 2 - 0.3),
                ( 0, -9, 17, -math.pi / 2),
                ( 3, -8, 15, -math.pi / 2 + 0.3),
                ( 6, -6, 12, -math.pi / 2 + 0.7),
            ]
            for bx, by, sz, ang in top_petals:
                flicker = int(math.sin(phase * 2 + bx * 0.2) * 1.5)
                _NS_zephyr._draw_petal(surface, cx + bx, cy + by, sz + flicker, ang,
                            _NS_zephyr.PALETTE["hair_dark"], _NS_zephyr.PALETTE["hair_mid"],
                            _NS_zephyr.PALETTE["hair_light"], _NS_zephyr.PALETTE["hair_tip"])

            # Small front bangs (over forehead)
            _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["hair_dark"], [
                (cx - 5, cy - 1),
                (cx - 3, cy - 3),
                (cx - 1, cy - 1),
                (cx + 1, cy - 1),
                (cx + 3, cy - 3),
                (cx + 5, cy - 1),
                (cx + 4, cy),
                (cx - 4, cy),
            ])
            _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["hair_mid"], [
                (cx - 4, cy - 1),
                (cx - 2, cy - 2),
                (cx + 2, cy - 2),
                (cx + 4, cy - 1),
                (cx + 3, cy - 1),
                (cx - 3, cy - 1),
            ])

            # Tiny highlight strands
            _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["hair_shine"],
                    (cx - 2, cy - 4), (cx - 1, cy - 1), 1)
            _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["hair_tip"],
                    (cx + 1, cy - 5), (cx + 2, cy - 2), 1)


    def _draw_body_particles(surface, cx, cy, phase):
        """Sparkles and butterflies around body."""
        # Sparkles
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            radius = 25 + int(math.sin(phase * 0.7 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(150 + math.sin(phase + i * 0.7) * 60)
            alpha = max(0, min(255, alpha))
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_light"], alpha), (px, py), 1)

        # Small butterflies (2 orbiting)
        for i in range(2):
            t = phase * 0.7 + i * math.pi
            bx = cx + int(math.cos(t) * 30)
            by = cy - 5 + int(math.sin(t * 1.3) * 10) - 8
            _NS_zephyr._draw_butterfly(surface, bx, by, 3, phase + i)

        # Falling petals
        for i in range(3):
            t = (phase * 0.3 + i * 0.35) % 1.0
            fx = cx - 30 + int(t * 60) + int(math.sin(phase + i) * 3)
            fy = cy - 30 + int(t * 70)
            alpha = int(220 * math.sin(t * math.pi))
            if alpha > 0:
                a = phase * 1.5 + i
                _NS_zephyr._draw_petal(surface, fx, fy, 3, a,
                            (*_NS_zephyr.PALETTE["hair_dark"], alpha),
                            (*_NS_zephyr.PALETTE["hair_mid"], alpha),
                            (*_NS_zephyr.PALETTE["hair_shine"], alpha))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_sparkles(surface, cx, cy, phase, trail=False,
                                 facing=1, intense=False):
        """Fey mist beneath floating Zephyr."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zephyr.PALETTE["magic_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising magical dust
        for i, offset in enumerate((-18, -6, 6, 18)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], alpha), (sx, sy), 4)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha), (sx, sy - 2), 3)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha), (sx, sy - 3), 1)

        # Orbiting butterflies
        for i in range(3):
            angle = phase * 1.1 + i * math.pi * 2 / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 5)
            _NS_zephyr._draw_butterfly(surface, sx, sy, 3, phase + i)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 24)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_zephyr.PALETTE["magic_dark"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_fey_silhouette_glow(surface, x, y, phase):
        """Halo magenta rendah-kontras khusus untuk Zephyr.

        Diletakkan sebelum tubuh dan aura normal agar rim light memisahkan
        rambut, sayap, serta staff dari peta, sambil tetap mempertahankan
        tepi pixel-art yang tajam. Ukuran kecil juga aman untuk Android.
        """
        pulse = 0.70 + math.sin(phase * 1.35) * 0.16
        halo = pygame.Surface((92, 104), pygame.SRCALPHA)
        center = (46, 51)
        for radius, alpha in ((41, 10), (32, 15), (24, 23)):
            _NS_zephyr._aacircle(
                halo, (*_NS_zephyr.PALETTE["magic_dark"],
                       int(alpha * pulse)), center, radius)
        # Dua kilau vertikal mengisyaratkan sayap tanpa menggambar ulang.
        _NS_zephyr._aaline(halo, (*_NS_zephyr.PALETTE["magic_mid"],
                                  int(35 * pulse)),
                            (26, 60), (17, 30), 2)
        _NS_zephyr._aaline(halo, (*_NS_zephyr.PALETTE["magic_mid"],
                                  int(35 * pulse)),
                            (66, 60), (75, 30), 2)
        surface.blit(halo, (x - 46, y - 51))


    def _draw_fey_aura(surface, x, y, phase):
        """Background aura - dark pink."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_zephyr._aacircle(aura, (*_NS_zephyr.PALETTE["magic_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_fey_platform(surface, x, y, phase, skill):
        """Fey circle platform."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_zephyr.PALETTE["magic_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_zephyr.PALETTE["magic_mid"], 180),
                            (20, 14, 90, 16), 2)

        # Swirling sparkles
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_zephyr.PALETTE["magic_bright"], 170),
                             (x1, y1), (x2, y2), 1)

        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_zephyr.PALETTE["magic_hot"], 220), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_zephyr.PALETTE["magic_bright"], int(100 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Cast flash at staff orb."""
        if progress < 0.4 or progress > 0.7:
            return
        t = (progress - 0.4) / 0.3
        intensity = math.sin(t * math.pi)

        flash_x = x + 22 * facing
        flash_y = y - 8

        alpha = int(200 * intensity)
        radius = int(5 + intensity * 14)

        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha),
                  (flash_x, flash_y), radius)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"],
                  (flash_x, flash_y), max(1, radius // 4))

        # Star rays
        for i in range(5):
            angle = progress * 5 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.5)
            ey = flash_y + int(math.sin(angle) * radius * 1.5)
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha),
                    (flash_x, flash_y), (ex, ey), 1)


    # ===================================================================
    # SKILL Q: BRAMBLE MAZE
    # ===================================================================
    def _draw_bramble_ground(surface, boss, x, y, timer, phase):
        """Ground indicator - dark spot at target."""
        origin = getattr(boss, "_bramble_origin", None)
        if origin:
            # BUGFIX (ring acak pada hero): _bramble_origin disimpan
            # dalam koordinat DUNIA; (x, y) renderer = pusat canvas.
            # Konversi dengan _world_to_local (lihat fungsi tersebut).
            tx, ty = _NS_zephyr._world_to_local(boss, x, y,
                                                origin[0], origin[1])
        else:
            tx, ty = _NS_zephyr._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 240))

        if progress < 0.2:
            # Warning shadow spot
            radius = int(20 + progress * 30)
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            _NS_zephyr._ellipse(surface, (*_NS_zephyr.PALETTE["magic_darkest"], int(150 * pulse)),
                     (tx - radius, ty + 15 - radius // 3,
                      radius * 2, radius * 2 // 3))


    def _draw_bramble_maze(surface, boss, x, y, timer, phase):
        """Thorny brambles/vines erupting from ground."""
        origin = getattr(boss, "_bramble_origin", None)
        if origin:
            # BUGFIX (ring acak pada hero): lihat _draw_bramble_ground.
            tx, ty = _NS_zephyr._world_to_local(boss, x, y,
                                                origin[0], origin[1])
        else:
            tx, ty = _NS_zephyr._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 240))

        if progress < 0.2:
            # Growing shadow (drawn on ground above)
            return

        # Brambles growing
        t = (progress - 0.2) / 0.8
        grow = min(1.0, t * 2)

        # Ring of thorny vines around target
        num_vines = 10
        for i in range(num_vines):
            angle = i * math.pi * 2 / num_vines + phase * 0.05
            base_r = 25
            bx = tx + int(math.cos(angle) * base_r)
            by = ty + 15 + int(math.sin(angle) * base_r * 0.4)

            # Vine grows up and inward like a claw
            vine_height = int(28 * grow)
            if vine_height < 3:
                continue

            # Twisted vine points
            curve = math.sin(angle) * 3
            tip_x = bx + int(math.cos(angle - 0.3) * -8) + int(curve)
            tip_y = by - vine_height

            # Vine polygon (thick to thin)
            px = -math.sin(angle - 0.3) * 3
            py = math.cos(angle - 0.3) * 3

            _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["bramble_dark"], [
                (bx + px, by + py),
                (bx - px, by - py),
                (tip_x, tip_y),
            ])
            _NS_zephyr._poly(surface, _NS_zephyr.PALETTE["bramble_mid"], [
                (bx + px * 0.7, by + py * 0.7),
                (bx - px * 0.7, by - py * 0.7),
                (tip_x, tip_y),
            ])
            _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["bramble_light"],
                    (bx, by), (tip_x, tip_y), 1)

            # Thorns along vine
            for th in (0.3, 0.55, 0.8):
                th_x = int(bx + (tip_x - bx) * th)
                th_y = int(by + (tip_y - by) * th)
                _NS_zephyr._draw_petal(surface, th_x, th_y, 4, angle + math.pi / 2,
                            _NS_zephyr.PALETTE["bramble_dark"], _NS_zephyr.PALETTE["bramble_mid"],
                            _NS_zephyr.PALETTE["bramble_light"])
                _NS_zephyr._draw_petal(surface, th_x, th_y, 3, angle - math.pi / 2,
                            _NS_zephyr.PALETTE["bramble_dark"], _NS_zephyr.PALETTE["bramble_mid"],
                            _NS_zephyr.PALETTE["bramble_light"])

            # Glow on tip
            _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_bright"], (tip_x, tip_y), 2)
            _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (tip_x, tip_y), 1)

        # Ground rune
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], 180),
                  (tx, ty + 15), int(28 * grow), 2)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_light"], 200),
                  (tx, ty + 15), int(25 * grow), 1)

        # Butterflies floating out
        for i in range(4):
            bt = (phase + i * 0.3) % 1.0
            ba = i * math.pi / 2 + phase * 0.5
            br = int(30 + bt * 20)
            bx = tx + int(math.cos(ba) * br)
            by = ty + 10 - int(bt * 25)
            alpha = int(240 * (1 - bt))
            _NS_zephyr._draw_butterfly(surface, bx, by, 3, phase + i, alpha=alpha)


    # ===================================================================
    # SKILL W: SHADOW REALM
    # ===================================================================
    def _draw_shadow_realm_ground(surface, boss, x, y, timer, phase):
        """Ground bubble indicator around Zephyr."""
        progress = max(0.0, min(1.0, 1 - timer / 180))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(30 + progress * 15)

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        pygame.draw.ellipse(ring, (*_NS_zephyr.PALETTE["magic_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_zephyr.PALETTE["magic_mid"], int(200 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Rune sparkles
        for i in range(8):
            a = phase * 0.5 + i * math.pi / 4
            px = cx + int(math.cos(a) * (radius - 3))
            py = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.circle(ring, (*_NS_zephyr.PALETTE["magic_hot"], 220), (px, py), 2)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_shadow_realm(surface, boss, x, y, timer, phase):
        """Purple bubble prison around Zephyr - invisibility/dodge effect."""
        progress = max(0.0, min(1.0, 1 - timer / 180))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Bubble radius
        if progress < 0.15:
            t = progress / 0.15
            bubble_r = int(35 * t)
        elif progress > 0.85:
            t = (1 - progress) / 0.15
            bubble_r = int(35 * t)
        else:
            bubble_r = 35

        if bubble_r < 3:
            return

        cx, cy = x, y - 10

        # Bubble outline layers
        for r_off in (0, 2, 4):
            alpha = int(140 * pulse) - r_off * 30
            if alpha > 0:
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_light"], alpha),
                          (cx, cy), bubble_r - r_off, 2)

        # Inner shading
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], int(60 * pulse)),
                  (cx, cy), bubble_r - 4, 3)

        # Bubble highlight (top-left)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], int(200 * pulse)),
                  (cx - bubble_r // 2, cy - bubble_r // 2),
                  max(1, bubble_r // 5))
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], int(220 * pulse)),
                  (cx - bubble_r // 2, cy - bubble_r // 2),
                  max(1, bubble_r // 8))

        # Swirling energy inside
        for i in range(6):
            a = phase * 3 + i * math.pi / 3
            r = int(bubble_r * 0.7)
            px = cx + int(math.cos(a) * r)
            py = cy + int(math.sin(a) * r * 0.6)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], 200), (px, py), 2)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], 220), (px, py), 1)

        # Ground swirl
        for i in range(4):
            a = phase * 2 + i * math.pi / 2
            rx = bubble_r - 5
            px = cx + int(math.cos(a) * rx)
            py = cy + 25 + int(math.sin(a) * 8)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], 200), (px, py), 3)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], 220), (px, py), 1)

        # Rune ring on ground
        _NS_zephyr._ellipse(surface, (*_NS_zephyr.PALETTE["magic_bright"], int(180 * pulse)),
                 (cx - bubble_r, cy + 20, bubble_r * 2, 14), 2)


    # ===================================================================
    # SKILL E: CASKET CURSE
    # ===================================================================
    def _draw_casket_indicator(surface, boss, x, y, timer, pulse):
        """Line to target for casket curse."""
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        for i in range(0, 20, 2):
            t1 = i / 20
            t2 = (i + 1) / 20
            _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_bright"], 150),
                    (x + (tx - x) * t1, y + (ty - y) * t1 - 8),
                    (x + (tx - x) * t2, y + (ty - y) * t2 - 8), 2)


    def _handle_casket_skill(surface, boss, x, y, timer, phase):
        """Spawn casket once at cast start."""
        if not getattr(boss, "_zp_casket_spawned", False):
            _NS_zephyr._spawn_casket(boss, x, y)
            boss._zp_casket_spawned = True
        if timer < 5:
            boss._zp_casket_spawned = False


    # ===================================================================
    # SKILL R: BEDLAM (many duplicates)
    # ===================================================================
    def _draw_bedlam_ground(surface, boss, x, y, timer, phase):
        """Ground swirl for bedlam."""
        progress = max(0.0, min(1.0, 1 - timer / 240))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(45 + progress * 15)

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Multiple rotating rings
        for r_off in range(3):
            pygame.draw.ellipse(ring,
                                (*_NS_zephyr.PALETTE["magic_mid"], int(150 * pulse) - r_off * 30),
                                (5 + r_off * 5, 5 + r_off * 2,
                                 radius * 2 + 10 - r_off * 10,
                                 radius + 10 - r_off * 4), 2)

        # Rune sparkles
        for i in range(10):
            a = phase * 0.8 + i * math.pi / 5
            px = cx + int(math.cos(a) * (radius - 2))
            py = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.circle(ring, (*_NS_zephyr.PALETTE["magic_hot"], 240), (px, py), 3)
            pygame.draw.circle(ring, _NS_zephyr.PALETTE["white"], (px, py), 1)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_bedlam(surface, boss, x, y, timer, phase):
        """Multiple mini duplicates spinning around Zephyr."""
        progress = max(0.0, min(1.0, 1 - timer / 240))

        # Spawn several mini fairy silhouettes orbiting
        num_dupes = 6
        for i in range(num_dupes):
            angle = phase * 2 + i * math.pi * 2 / num_dupes
            orbit_r = 40 + int(math.sin(phase + i) * 5)
            dx = x + int(math.cos(angle) * orbit_r)
            dy = y - 10 + int(math.sin(angle) * 12)

            # Fading mini silhouette
            alpha = int(180 + math.sin(phase * 2 + i) * 60)
            alpha = max(0, min(240, alpha))
            _NS_zephyr._draw_mini_fairy(surface, dx, dy, phase, alpha,
                             facing=1 if math.cos(angle) > 0 else -1)

            # Sparkle trail behind each dupe
            for tr in range(3):
                tra = angle - tr * 0.3
                tx = x + int(math.cos(tra) * orbit_r)
                ty = y - 10 + int(math.sin(tra) * 12)
                a2 = alpha - tr * 40
                if a2 > 0:
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], a2),
                              (tx, ty), max(1, 3 - tr))

        # Sparkles around
        for i in range(12):
            a = phase * 1.5 + i * math.pi / 6
            r = 45 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(a) * r)
            sy = y - 5 + int(math.sin(a) * r * 0.5)
            alpha = int(200 + math.sin(phase * 3 + i) * 55)
            alpha = max(0, min(255, alpha))
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], alpha), (sx, sy), 2)
            _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"], (sx, sy), 1)

        # Swirl connecting duplicates
        for i in range(3):
            a_start = phase * 1.5 + i * math.pi * 2 / 3
            a_end = a_start + math.pi * 1.2
            segs = 12
            for s in range(segs):
                t1 = s / segs
                t2 = (s + 1) / segs
                ang1 = a_start + (a_end - a_start) * t1
                ang2 = a_start + (a_end - a_start) * t2
                r_o = 42
                x1 = x + int(math.cos(ang1) * r_o)
                y1 = y - 10 + int(math.sin(ang1) * r_o * 0.35)
                x2 = x + int(math.cos(ang2) * r_o)
                y2 = y - 10 + int(math.sin(ang2) * r_o * 0.35)
                _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_bright"], 180),
                        (x1, y1), (x2, y2), 1)


    def _draw_mini_fairy(surface, cx, cy, phase, alpha, facing=1):
        """Small silhouette of Zephyr for bedlam duplicates."""
        # Wings
        wing_flap = math.sin(phase * 3) * 0.15 + 0.85
        for side in (-1, 1):
            wp = int(6 * wing_flap)
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_mid"], alpha // 2), [
                (cx, cy - 3),
                (cx + side * wp, cy - wp - 2),
                (cx + side * wp // 2, cy - 3),
            ])
            _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["wing_light"], alpha // 2), [
                (cx, cy - 3),
                (cx + side * wp, cy - wp - 1),
                (cx + side * wp // 2, cy - 2),
            ])

        # Body (small petal skirt)
        _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["dress_dark"], alpha), [
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
        ])
        _NS_zephyr._poly(surface, (*_NS_zephyr.PALETTE["dress_mid"], alpha), [
            (cx - 3, cy + 1),
            (cx + 3, cy + 1),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])

        # Corset dark
        _NS_zephyr._rect(surface, (*_NS_zephyr.PALETTE["corset_dark"], alpha), (cx - 3, cy - 3, 6, 4))
        _NS_zephyr._rect(surface, (*_NS_zephyr.PALETTE["corset_mid"], alpha), (cx - 2, cy - 2, 4, 2))

        # Head with tiny hair flame
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["skin_dark"], alpha), (cx, cy - 6), 3)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["skin_mid"], alpha), (cx, cy - 6), 2)

        # Hair flames on top
        for i in range(3):
            a = -math.pi / 2 + (i - 1) * 0.5
            tx = cx + int(math.cos(a) * 4)
            ty = cy - 6 + int(math.sin(a) * 4)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["hair_mid"], alpha), (tx, ty), 2)
            _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["hair_shine"], alpha), (tx, ty), 1)

        # Tiny eyes
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["eye_iris"], alpha), (cx - 1, cy - 6), 1)
        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["eye_iris"], alpha), (cx + 1, cy - 6), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_zephyr.draw_zephyr(surface, boss, x, y)

